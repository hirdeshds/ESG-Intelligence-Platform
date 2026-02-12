# import pandas as pd
# import joblib

# def run_agent7(input_path, output_path):
#     df = pd.read_csv(input_path)

#     model = joblib.load("models/risk_model.pkl")

#     feature_importance = model.feature_importances_

#     explanation = f"""
#     Risk influenced mainly by:
#     ESG_Score Importance: {round(feature_importance[0]*100,2)}%
#     """

#     df["explanation"] = explanation

#     df.to_csv(output_path, index=False)

#     return df
import shap
import numpy as np
import pandas as pd
import joblib
model=joblib.load("models/risk_model.pkl")
df=pd.read_csv(r"C:\\Users\\Mahek Bhatia\\Desktop\\ESG-Monitoring-System\\outputs\\agent4_final_output.csv")
def generate_explanation(df, model):

    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(df[model.feature_names_in_])[1]

    contributions = shap_values[0]
    feature_names = model.feature_names_in_

    sorted_idx = np.argsort(np.abs(contributions))[::-1]

    top_factors = []

    for idx in sorted_idx[:3]:
        feature = feature_names[idx]
        impact = contributions[idx]

        if impact > 0:
            text = f"High {feature} increased ESG risk."
        else:
            text = f"{feature} helped reduce ESG risk."

        top_factors.append(text)

    return {
        "top_risk_factors": top_factors,
        "summary": "Risk score influenced mainly by the above ESG factors."
    }

