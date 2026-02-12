import pandas as pd
import joblib

def run_agent6(input_path, output_path):
    df = pd.read_csv(input_path)

    model = joblib.load("models/risk_model.pkl")

    df["predicted_risk"] = model.predict(df[["ESG_Score"]])

    df.to_csv(output_path, index=False)

    return df
