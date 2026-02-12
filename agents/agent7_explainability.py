import pandas as pd
import joblib

def run_agent7(input_path, output_path):
    df = pd.read_csv(input_path)

    model = joblib.load("models/risk_model.pkl")

    feature_importance = model.feature_importances_

    explanation = f"""
    Risk influenced mainly by:
    ESG_Score Importance: {round(feature_importance[0]*100,2)}%
    """

    df["explanation"] = explanation

    df.to_csv(output_path, index=False)

    return df
