from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = BASE_DIR / "outputs"
DEFAULT_INPUT_FILE = DEFAULT_OUTPUT_DIR / "agent1_operational_output.csv"
DEFAULT_OUTPUT_FILE = DEFAULT_OUTPUT_DIR / "agent2_financial_output.csv"


def run_agent2(input_path=None, output_path=None):
    source = Path(input_path) if input_path else DEFAULT_INPUT_FILE
    target = Path(output_path) if output_path else DEFAULT_OUTPUT_FILE

    if not source.exists():
        return {
            "error": f"Input file not found: {source}. Run Agent 1 first.",
        }

    try:
        df = pd.read_csv(source)
        df["financial_risk_score"] = (
            (df["E_Score"] < 60).astype(int)
            + (df["S_Score"] < 60).astype(int)
            + (df["G_Score"] < 60).astype(int)
        ) * 33

        target.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(target, index=False)
        return df.to_dict(orient="records")
    except Exception as exc:
        return {"error": f"Agent 2 failed: {exc}"}
