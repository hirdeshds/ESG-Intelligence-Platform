from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = BASE_DIR / "outputs"
DEFAULT_INPUT_FILE = DEFAULT_OUTPUT_DIR / "agent3_compliance_output.csv"
DEFAULT_OUTPUT_FILE = DEFAULT_OUTPUT_DIR / "agent4_final_output.csv"


def run_agent4(input_path=None, output_path=None):
    source = Path(input_path) if input_path else DEFAULT_INPUT_FILE
    target = Path(output_path) if output_path else DEFAULT_OUTPUT_FILE

    if not source.exists():
        return {
            "error": f"Input file not found: {source}. Run Agent 3 first.",
        }

    try:
        df = pd.read_csv(source)

        df["final_esg_risk_score"] = (
            (df["E_Compliance"] == "Violation").astype(int)
            + (df["S_Compliance"] == "Violation").astype(int)
            + (df["G_Compliance"] == "Violation").astype(int)
        ) * 33

        def assign_alert(score):
            if score >= 66:
                return "Critical"
            if score >= 33:
                return "Warning"
            return "Low"

        df["alert_level"] = df["final_esg_risk_score"].apply(assign_alert)

        target.parent.mkdir(parents=True, exist_ok=True)
        report = df[["Firm_ID", "Year", "Overall_Compliance", "final_esg_risk_score", "alert_level"]]
        report.to_csv(target, index=False)
        return report.to_dict(orient="records")
    except Exception as exc:
        return {"error": f"Agent 4 failed: {exc}"}
