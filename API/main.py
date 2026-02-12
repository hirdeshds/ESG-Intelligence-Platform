from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import joblib
import os



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
