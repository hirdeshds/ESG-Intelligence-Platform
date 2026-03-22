from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import joblib
import os
import io
import numpy as np

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

# ============================================================
# ROOT
# ============================================================

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



# ============================================================
# -------------------- BASIC PLAN ----------------------------
# ============================================================

def calculate_environmental_score(row):
    if all(col in row.index for col in [
        'carbon_emissions','energy_consumption',
        'renewable_energy_percent','water_usage','waste_generated'
    ]):
        carbon = max(0, 100 - row['carbon_emissions'] * 0.05)
        energy = max(0, 100 - row['energy_consumption'] * 0.01)
        renewable = row['renewable_energy_percent']
        water = max(0, 100 - row['water_usage'] * 0.05)
        waste = max(0, 100 - row['waste_generated'] * 0.05)
        return round((carbon + energy + renewable + water + waste)/5,2)

    return row.get("E_Score",70.0)

def calculate_csr_score(row):
    return row.get("S_Score",65.0)

def calculate_weighted_esg(environment, csr):
    return round((0.70*environment + 0.30*csr),2)

def predict_risk_category(score):
    if model is None:
        if score >= 70: return "Low",0.15
        elif score >= 55: return "Medium",0.55
        else: return "High",0.85

    prob = model.predict_proba([[score]])[0]
    pred = model.predict([[score]])[0]
    risk_map = {0:"Low",1:"Medium",2:"High"}
    return risk_map.get(pred,"Medium"), round(float(prob[pred]),2)

@app.post("/basic/predict")
async def basic_plan_predict(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        df = pd.read_csv(io.StringIO(contents.decode("utf-8")))

        if df.empty:
            return {"error":"CSV empty"}

        row = df.iloc[0]
        # robustly extract year as native Python int when present
        year_val = None
        if 'Year' in df.columns:
            try:
                yraw = df.iloc[0].get('Year', None)
                if pd.notna(yraw):
                    year_val = int(yraw)
            except Exception:
                try:
                    # fallback for floats stored as strings
                    year_val = int(float(df.iloc[0].get('Year')))
                except Exception:
                    year_val = None

        env_score = calculate_environmental_score(row)
        csr_score = calculate_csr_score(row)
        esg_score = calculate_weighted_esg(env_score, csr_score)

        risk_category, probability = predict_risk_category(esg_score)

        return {
            "firm_id": row.get("Firm_ID","Unknown"),
            "year": year_val,
            "esg_score": float(esg_score),
            "risk_category": risk_category,
            "risk_probability": probability,
            "environment_score": float(env_score),
            "csr_score": float(csr_score)
        }

    except Exception as e:
        return {"error":str(e)}

# ============================================================
# -------------------- PREMIUM PLAN --------------------------
# ============================================================

from sklearn.linear_model import LinearRegression
from sklearn.ensemble import IsolationForest
import shap

def operational_agent_advanced(df):
    row = df.iloc[0]
    env_score = calculate_environmental_score(row)

    trend = "Stable"
    forecast = None

    if "Year" in df.columns and "carbon_emissions" in df.columns and len(df)>=2:
        temp = df.sort_values("Year")
        X = temp["Year"].values.reshape(-1,1)
        y = temp["carbon_emissions"].values
        lr = LinearRegression()
        lr.fit(X,y)
        slope = lr.coef_[0]
        trend = "Increasing" if slope>0 else "Reducing"
        forecast = float(lr.predict([[max(X)+1]])[0])

    return env_score, trend, forecast

def regulatory_agent(df):
    violations=[]
    row=df.iloc[0]

    if "renewable_energy_percent" in row and row["renewable_energy_percent"]<20:
        violations.append("Low renewable energy")

    if "board_independence_percent" in row and row["board_independence_percent"]<50:
        violations.append("Low board independence")

    if "carbon_emissions" in row and row["carbon_emissions"]>1500:
        violations.append("High carbon emissions")

    score=max(0,100-len(violations)*30)
    return score,violations

def anomaly_detection_agent(df):
    num=df.select_dtypes(include=["number"])
    if len(num)<2:
        return False,None

    iso=IsolationForest(random_state=42)
    preds=iso.fit_predict(num)

    if preds[-1]==-1:
        return True,"Recent data appears anomalous"

    return False,None

def explainability_agent(score):
    if model is None:
        return {"top_factors":[],"summary":"Model unavailable"}

    try:
        explainer=shap.TreeExplainer(model)
        df_feat=pd.DataFrame([[score]],columns=["final_esg_risk_score"])
        sv=explainer.shap_values(df_feat)

        if isinstance(sv,list):
            sv=sv[1]

        shap_vals=sv[0]
        idx=np.argsort(np.abs(shap_vals))[::-1][:1]

        top=[]
        for i in idx:
            impact=shap_vals[i]
            if impact>0:
                top.append("Higher ESG score increased risk")
            else:
                top.append("ESG score reduced risk")

        return {
            "top_factors":top,
            "summary":"Risk influenced mainly by ESG score."
        }

    except Exception as e:
        return {"top_factors":[],"summary":str(e)}

@app.post("/premium/predict")
async def premium_plan_predict(file: UploadFile = File(...)):
    try:
        contents=await file.read()
        df=pd.read_csv(io.StringIO(contents.decode("utf-8")))

        if df.empty:
            return {"error":"CSV empty"}

        env_score,trend,forecast=operational_agent_advanced(df)
        comp_score,violations=regulatory_agent(df)

        csr_score=df.iloc[0].get("S_Score",65.0)

        final_score=(env_score+csr_score+comp_score)/3

        risk_cat,confidence=predict_risk_category(final_score)

        anomaly,reason=anomaly_detection_agent(df)

        explanation=explainability_agent(final_score)

        return {
            "risk_analysis":{
                "score":float(final_score),
                "category":risk_cat,
                "confidence":confidence
            },
            "trend_analysis":{
                "direction":trend,
                "forecast_next_year":forecast
            },
            "compliance":{
                "score":comp_score,
                "violations":violations
            },
            "anomaly_detection":{
                "detected":anomaly,
                "reason":reason
            },
            "explanation":explanation
        }

    except Exception as e:
        return {"error":str(e)}

