from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from agents.output_paths import get_agent_output_path, get_company_name

try:
    import shap
except ImportError:
    shap = None

BASE_DIR = Path(__file__).resolve().parents[1]
MODEL_PATH = BASE_DIR / "models" / "risk_model.pkl"


def generate_explanation(df, model):
    explainer = shap.TreeExplainer(model)
    feature_names = list(getattr(model, "feature_names_in_", []))
    if not feature_names:
        return {
            "top_risk_factors": [],
            "summary": "Model does not expose feature names for SHAP explanations.",
        }

    shap_values = explainer.shap_values(df[feature_names])
    if isinstance(shap_values, list):
        shap_values = shap_values[1] if len(shap_values) > 1 else shap_values[0]
        contributions = shap_values[0]
    elif isinstance(shap_values, np.ndarray) and shap_values.ndim == 3:
        # Newer SHAP versions may return (samples, features, classes).
        contributions = shap_values[0, :, -1]
    else:
        contributions = shap_values[0]

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
        "summary": "Risk score influenced mainly by the above ESG factors.",
    }


def run_agent5(input_path=None, company_id=None):
    if shap is None:
        return {"error": "Missing dependency: shap."}
    if not MODEL_PATH.exists():
        return {"error": f"Model file not found: {MODEL_PATH}"}

    company_name = get_company_name(company_id)
    source = Path(input_path) if input_path else get_agent_output_path(
        "agent4_final_output",
        company_name=company_name,
    )
    if not source.exists():
        return {"error": f"Input file not found: {source}. Run Agent 4 first."}

    try:
        model = joblib.load(MODEL_PATH)
        df = pd.read_csv(source)
        feature_names = list(getattr(model, "feature_names_in_", []))
        if not feature_names:
            return {"error": "Loaded model does not expose feature_names_in_."}

        missing_features = [name for name in feature_names if name not in df.columns]
        if missing_features:
            return {
                "error": "Agent 5 failed: missing model feature columns in input data: "
                + ", ".join(missing_features)
            }

        return generate_explanation(df, model)
    except Exception as exc:
        return {"error": f"Agent 5 failed: {exc}"}
