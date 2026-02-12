from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import joblib
import os
import io
import numpy as np
from pydantic import BaseModel
from typing import Optional



app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_PATH = "outputs/agent4_final_output.csv"
MODEL_PATH = "models/risk_model.pkl"


model = None
if os.path.exists(MODEL_PATH):
    model = joblib.load(MODEL_PATH)



@app.get("/")
def home():
    return {"message": "ESG Multi-Agent Monitoring API Running Successfully"}



@app.get("/esg-data")
def get_all_data():
    df = pd.read_csv(DATA_PATH)
    return df.to_dict(orient="records")



@app.get("/firm/{firm_id}")
def get_firm_data(firm_id: str):
    df = pd.read_csv(DATA_PATH)
    data = df[df["Firm_ID"] == firm_id]

    if data.empty:
        return {"error": "Firm not found"}

    return data.to_dict(orient="records")


@app.get("/risk-summary")
def risk_summary():
    df = pd.read_csv(DATA_PATH)

    return {
        "critical": int(df[df["alert_level"] == "Critical"].shape[0]),
        "warning": int(df[df["alert_level"] == "Warning"].shape[0]),
        "low": int(df[df["alert_level"] == "Low"].shape[0]),
    }



@app.get("/compliance-distribution")
def compliance_distribution():
    df = pd.read_csv(DATA_PATH)
    return df["Overall_Compliance"].value_counts().to_dict()


@app.get("/predict/{risk_score}")
def predict_risk(risk_score: float):

    if model is None:
        return {"error": "Model not found. Train model first."}

    prediction = model.predict([[risk_score]])

    return {
        "input_risk_score": risk_score,
        "predicted_risk_label": int(prediction[0])
    }


# ======================== BASIC PLAN ENDPOINTS ========================

def calculate_environmental_score(row):
    """
    Calculate environmental composite score using available metrics.
    Supports both detailed environmental data and E_Score fallback.
    """
    if all(col in row.index for col in ['carbon_emissions', 'energy_consumption', 
                                          'renewable_energy_percent', 'water_usage', 'waste_generated']):
        carbon_norm = min(100, max(0, 100 - (row['carbon_emissions'] / 1000 * 100)))
        energy_norm = min(100, max(0, 100 - (row['energy_consumption'] / 1000 * 100)))
        renewable_norm = min(100, max(0, row['renewable_energy_percent']))
        water_norm = min(100, max(0, 100 - (row['water_usage'] / 1000 * 100)))
        waste_norm = min(100, max(0, 100 - (row['waste_generated'] / 1000 * 100)))
        
        env_score = (carbon_norm + energy_norm + renewable_norm + water_norm + waste_norm) / 5
    elif 'E_Score' in row.index:
        env_score = row['E_Score']
    else:
        env_score = 70.0  
    
    return round(env_score, 2)


def calculate_emission_trend(df, firm_id):
    """
    Calculate Year-over-Year emission trend.
    """
    if 'Firm_ID' in df.columns and 'Year' in df.columns:
        firm_data = df[df['Firm_ID'] == firm_id].sort_values('Year')
        if len(firm_data) >= 2 and 'carbon_emissions' in df.columns:
            recent = firm_data.iloc[-1]['carbon_emissions']
            previous = firm_data.iloc[-2]['carbon_emissions']
            trend = ((recent - previous) / previous * 100) if previous != 0 else 0
            if trend < -5:
                return "Reducing"
            elif trend > 5:
                return "Increasing"
            else:
                return "Stable"
    if 'E_Score' in df.columns:
        avg_score = df['E_Score'].mean()
        firm_score = df[df['Firm_ID'] == firm_id]['E_Score'].mean() if 'Firm_ID' in df.columns else 70
        if firm_score > avg_score:
            return "Reducing"
        else:
            return "Increasing"
    return "Stable"


def calculate_renewable_status(row):
    """
    Determine renewable energy usage status.
    """
    if 'renewable_energy_percent' in row.index:
        renewable = row['renewable_energy_percent']
        if renewable >= 50:
            return "High"
        elif renewable >= 25:
            return "Moderate"
        else:
            return "Low"
    return "Moderate"  #


def calculate_csr_growth(row, df=None):
    """
    Calculate CSR growth (YoY).
    """
    if 'csr_spending' in row.index and df is not None and 'Firm_ID' in df.columns:
        firm_data = df[df['Firm_ID'] == row['Firm_ID']].sort_values('Year')
        if len(firm_data) >= 2:
            recent = firm_data.iloc[-1]['csr_spending']
            previous = firm_data.iloc[-2]['csr_spending']
            growth = ((recent - previous) / previous * 100) if previous != 0 else 0
            return f"{growth:+.0f}%"
    
    if 'Innovation_Spending' in row.index:
        innovation = row['Innovation_Spending']
        if innovation > 4.5:
            return "+15%"
        elif innovation > 3.5:
            return "+8%"
        else:
            return "+3%"
    
    return "+5%" 


def calculate_financial_alignment(row):
    """
    Determine financial ESG alignment based on financial indicators.
    """
    scores = []
    
    if 'ROA' in row.index:
        scores.append(min(row['ROA'], 15) / 15 * 100)
    if 'ROE' in row.index:
        scores.append(min(row['ROE'], 20) / 20 * 100)
    if 'Net_Profit_Margin' in row.index:
        scores.append(min(row['Net_Profit_Margin'], 12) / 12 * 100)
    
    if scores:
        avg_score = np.mean(scores)
        if avg_score >= 75:
            return "Excellent"
        elif avg_score >= 60:
            return "Good"
        elif avg_score >= 45:
            return "Fair"
        else:
            return "Poor"
    
    return "Good"  # Default


def calculate_csr_score(row):
    """
    Calculate CSR (Social) score from available data.
    Returns numeric score 0-100.
    Uses S_Score if available, otherwise estimates from financial indicators.
    """
    if 'S_Score' in row.index:
        return round(float(row['S_Score']), 2)
    
    if 'Innovation_Spending' in row.index:
        innovation = row['Innovation_Spending']
        csr_proxy = min(100, max(0, (innovation / 6.0) * 100))
        return round(csr_proxy, 2)
    
    return 65.0


def calculate_weighted_esg_score(environmental_score, csr_score):
    """
    Calculate weighted ESG composite score using formula-based approach.
    Formula: ESG_Score = (0.70 * Environmental_Score) + (0.30 * CSR_Score)
    
    Args:
        environmental_score: Environmental score (0-100)
        csr_score: CSR/Social score (0-100)
    
    Returns:
        Weighted ESG composite score (0-100)
    """
    esg_score = (0.70 * environmental_score) + (0.30 * csr_score)
    return round(esg_score, 2)


def predict_risk_category(final_esg_score):
    """
    Predict risk category and probability using loaded model.
    """
    global model
    
    if model is None:
        if final_esg_score >= 70:
            return "Low", 0.15
        elif final_esg_score >= 55:
            return "Medium", 0.55
        else:
            return "High", 0.85
    
    try:
        risk_prob = model.predict_proba([[final_esg_score]])[0]
        prediction = model.predict([[final_esg_score]])[0]
        
        risk_map = {0: "Low", 1: "Medium", 2: "High"}
        risk_category = risk_map.get(prediction, "Medium")
        
        risk_probability = round(float(risk_prob[prediction]), 2)
        
        return risk_category, risk_probability
    except Exception as e:
        # Fallback
        if final_esg_score >= 70:
            return "Low", 0.15
        elif final_esg_score >= 55:
            return "Medium", 0.55
        else:
            return "High", 0.85


def generate_summary(env_score, emission_trend, renewable_status, csr_growth, financial_alignment):
    """
    Generate human-readable ESG performance summary.
    """
    summary_parts = []
    
    # Environmental assessment
    if env_score >= 75:
        summary_parts.append("Company environmental practices are strong")
    elif env_score >= 55:
        summary_parts.append("Company environmental practices are moderate")
    else:
        summary_parts.append("Company environmental practices need improvement")
    
    # Trend assessment
    if emission_trend == "Reducing":
        summary_parts.append("and emissions are trending downward")
    elif emission_trend == "Increasing":
        summary_parts.append("but emissions are increasing")
    else:
        summary_parts.append("with stable emission levels")
    
    # Renewable energy assessment
    if renewable_status == "High":
        summary_parts.append(". Renewable energy adoption is commendable")
    elif renewable_status == "Low":
        summary_parts.append(". Renewable energy usage can improve significantly")
    else:
        summary_parts.append(". Renewable energy usage is at moderate levels")
    
    # Financial alignment
    if financial_alignment == "Excellent":
        summary_parts.append(", with excellent financial ESG alignment")
    elif financial_alignment == "Good":
        summary_parts.append(", with good financial ESG alignment")
    else:
        summary_parts.append(", but financial ESG alignment needs work")
    
    return ". ".join(summary_parts) + "."


@app.post("/basic/predict")
async def basic_plan_predict(file: UploadFile = File(...)):
    """
    BASIC PLAN API Endpoint for Foundational ESG Intelligence
    
    - Lightweight, fast, low-compute processing
    - Operational Agent: Environmental metrics
    - Financial Agent: CSR and financial alignment
    - Risk Prediction: RandomForest model inference
    - Returns structured ESG assessment
    
    Upload a CSV with columns like:
    - Firm_ID, Year, E_Score, S_Score, G_Score (minimal)
    - Or detailed: carbon_emissions, energy_consumption, renewable_energy_percent, water_usage, waste_generated
    - Revenue, ROA, ROE, Net_Profit_Margin for financial assessment
    """
    try:
        # Read uploaded CSV file
        contents = await file.read()
        df = pd.read_csv(io.StringIO(contents.decode('utf-8')))
        
        if df.empty:
            return {"error": "Uploaded CSV is empty"}
        
        if len(df) > 1:
            data_row = df.iloc[0] 
        else:
            data_row = df.iloc[0]
        
        environment_score = calculate_environmental_score(data_row)
        emission_trend = calculate_emission_trend(df, data_row.get('Firm_ID', 'Unknown'))
        renewable_status = calculate_renewable_status(data_row)
        
        csr_growth = calculate_csr_growth(data_row, df)
        financial_alignment = calculate_financial_alignment(data_row)
        
        csr_score = calculate_csr_score(data_row)
        
  
        esg_score = calculate_weighted_esg_score(environment_score, csr_score)

        e_score = data_row.get('E_Score', environment_score)
        s_score = data_row.get('S_Score', 65.0)
        g_score = data_row.get('G_Score', 65.0)
        final_esg_score = (e_score + s_score + g_score) / 3
        
        risk_category, risk_probability = predict_risk_category(final_esg_score)

        
        response = {
            "esg_score": float(esg_score),
            "risk_category": risk_category,
            "risk_probability": float(risk_probability),
            "environment_score": float(round(environment_score, 2)),
            "emission_trend": emission_trend,
            "renewable_usage_status": renewable_status,
            "csr_growth": csr_growth,
            "financial_esg_alignment": financial_alignment
        }
        
        return response
    
    except Exception as e:
        return {"error": f"Failed to process file: {str(e)}"}


# ------------------- PREMIUM PLAN HELPERS -------------------

def operational_agent_advanced(df: pd.DataFrame):
    # environmental score using detailed metrics or E_Score
    if not df.empty:
        row = df.iloc[0]
    else:
        return 70.0, "Stable", None

    env_score = calculate_environmental_score(row)

    # carbon intensity (if revenue available)
    carbon_intensity = None
    if 'carbon_emissions' in row.index and 'Revenue' in row.index and row['Revenue'] != 0:
        carbon_intensity = row['carbon_emissions'] / row['Revenue']

    # trend slope over years based on carbon_emissions
    trend_direction = "Stable"
    forecast_next = None
    if 'Year' in df.columns and 'carbon_emissions' in df.columns and len(df) >= 2:
        temp = df[['Year', 'carbon_emissions']].dropna()
        if len(temp) >= 2:
            years = temp['Year'].astype(float).values.reshape(-1, 1)
            emissions = temp['carbon_emissions'].astype(float).values
            # linear regression for slope
            from sklearn.linear_model import LinearRegression
            lr = LinearRegression()
            lr.fit(years, emissions)
            slope = lr.coef_[0]
            trend_direction = "Reducing" if slope < -0.01 else ("Increasing" if slope > 0.01 else "Stable")
            # forecast next year
            next_year = years.max() + 1
            forecast_next = float(lr.predict([[next_year]])[0])

    return env_score, trend_direction, forecast_next


def financial_agent_advanced(df: pd.DataFrame):
    csr_growth = None
    csr_to_revenue = None
    roi_estimate = None

    if 'csr_spending' in df.columns and 'Year' in df.columns:
        firm_data = df.sort_values('Year')
        if len(firm_data) >= 2:
            recent = firm_data.iloc[-1]['csr_spending']
            previous = firm_data.iloc[-2]['csr_spending']
            csr_growth = ((recent - previous) / previous * 100) if previous != 0 else 0

    if 'csr_spending' in df.columns and 'Revenue' in df.columns:
        total_csr = df['csr_spending'].sum()
        total_rev = df['Revenue'].sum()
        if total_rev != 0:
            csr_to_revenue = total_csr / total_rev

    # simplistic ROI: assume ROA or ROE exist
    if 'ROA' in df.columns:
        roi_estimate = df['ROA'].mean()
    elif 'ROE' in df.columns:
        roi_estimate = df['ROE'].mean()

    # financial score combine available metrics into 0-100
    scores = []
    if csr_growth is not None:
        scores.append(min(max(csr_growth, -100), 100))
    if csr_to_revenue is not None:
        scores.append(min(max(csr_to_revenue * 100, 0), 100))
    if roi_estimate is not None:
        scores.append(min(max(roi_estimate, 0), 100))

    financial_score = float(np.mean(scores)) if scores else 50.0

    return financial_score, csr_growth, roi_estimate


def regulatory_agent(df: pd.DataFrame):
    violations = []
    if 'Board_Independence' in df.columns:
        if df.iloc[0]['Board_Independence'] < 0.5:
            violations.append("Board independence below threshold")
    if 'renewable_energy_percent' in df.columns:
        if df.iloc[0]['renewable_energy_percent'] < 20:
            violations.append("Renewable energy usage below threshold")
    if 'carbon_emissions' in df.columns:
        if df.iloc[0]['carbon_emissions'] > 1000:
            violations.append("Carbon emissions above threshold")

    compliance_score = 100 - len(violations) * 33
    if compliance_score < 0:
        compliance_score = 0

    return compliance_score, violations


def risk_prediction_agent(final_score: float):
    # reuse existing predict_risk with probability
    return predict_risk(final_score)


def anomaly_detection_agent(df: pd.DataFrame):
    detected = False
    reason = None

    # IsolationForest on numeric columns
    num = df.select_dtypes(include=["number"]).fillna(0)
    if not num.empty and len(num) >= 2:
        from sklearn.ensemble import IsolationForest
        iso = IsolationForest(random_state=42, contamination=0.1)
        preds = iso.fit_predict(num)
        if preds[0] == -1:
            detected = True
            reason = "First row is an outlier in numeric metrics"

    # also check yoy carbon emissions jump
    if 'Year' in df.columns and 'carbon_emissions' in df.columns and len(df) >= 2:
        temp = df.sort_values('Year')
        recent = temp.iloc[-1]['carbon_emissions']
        previous = temp.iloc[-2]['carbon_emissions']
        if previous != 0:
            change = (recent - previous) / previous * 100
            if abs(change) > 30:
                detected = True
                reason = f"Carbon emissions changed by {change:.0f}% YoY"

    return detected, reason


def explainability_agent(df_features: pd.DataFrame):
    if model is None:
        return {"top_factors": [], "summary": "Model unavailable"}
    try:
        import shap
        explainer = shap.TreeExplainer(model)
        sv = explainer.shap_values(df_features)
        # shap values may be a list or numpy array
        if isinstance(sv, list) and len(sv) > 1:
            sv = sv[1]
        # convert 3D array (n_samples,n_features,n_classes) to 2D for class 1
        if isinstance(sv, np.ndarray) and sv.ndim == 3:
            # pick last class contributions
            sv = sv[:, :, -1]
        # now sv shape should be (n_samples, n_features)
        shap_vals = sv[0]
        abs_vals = np.abs(shap_vals)
        idx = np.argsort(abs_vals)[::-1][:3]
        top = []
        for i in idx:
            # ensure scalar index
            if isinstance(i, (list, tuple, np.ndarray)):
                i = int(i[0])
            feature = df_features.columns[i]
            impact = shap_vals[i]
            # convert to scalar if array
            try:
                impact_val = float(impact)
            except Exception:
                impact_val = impact
            if impact_val > 0:
                top.append(f"High {feature} increased risk")
            else:
                top.append(f"{feature} mitigated risk")
        summary = "Risk influenced mainly by " + ", ".join([f.split()[1] for f in top]) + "."
        return {"top_factors": top, "summary": summary}
    except Exception as e:
        # capture error message for debugging
        return {"top_factors": [], "summary": f"Explainability failed: {str(e)}"}


# ------------------- PREMIUM PLAN ENDPOINT -------------------

@app.post("/premium/predict")
async def premium_plan_predict(file: UploadFile = File(...)):
    # follow execution flow described in requirements
    try:
        contents = await file.read()
        df = pd.read_csv(io.StringIO(contents.decode('utf-8')))
        if df.empty:
            return {"error": "Uploaded CSV is empty"}

        # basic validation
        required = ['Firm_ID', 'Year']
        if not all(col in df.columns for col in required):
            return {"error": "CSV missing required columns"}

        # 1. Operational agent
        env_score, trend_dir, forecast = operational_agent_advanced(df)

        # 2. Financial agent
        fin_score, csr_growth, roi_est = financial_agent_advanced(df)

        # 3. Regulatory agent
        comp_score, violations = regulatory_agent(df)

        # 4. Risk prediction
        final_esg = (env_score + fin_score + comp_score) / 3
        risk_score = final_esg
        # determine category and probability
        if model is not None:
            prob = model.predict_proba([[final_esg]])[0]
            pred = model.predict([[final_esg]])[0]
            risk_cat = {0:"Low",1:"Medium",2:"High"}.get(int(pred), "Medium")
            confidence = round(float(prob[pred]),2)
        else:
            # fallback heuristics
            if final_esg >= 70:
                risk_cat = "Low"
                confidence = 0.15
            elif final_esg >= 55:
                risk_cat = "Medium"
                confidence = 0.55
            else:
                risk_cat = "High"
                confidence = 0.85

        # 5. Anomaly detection
        anomaly, reason = anomaly_detection_agent(df)

        # 6. Explainability
        features_df = pd.DataFrame([[final_esg]], columns=["final_esg_risk_score"])
        explanation = explainability_agent(features_df)

        response = {
            "risk_analysis": {"score": float(risk_score), "category": risk_cat, "confidence": float(confidence)},
            "trend_analysis": {"direction": trend_dir, "forecast_next_year": float(forecast) if forecast is not None else None},
            "environmental_score": float(env_score),
            "financial_score": float(fin_score),
            "compliance": {"score": float(comp_score), "violations": violations},
            "anomaly_detection": {"detected": anomaly, "reason": reason},
            "explanation": explanation
        }
        return response
    except Exception as e:
        return {"error": f"Premium plan processing failed: {str(e)}"}
