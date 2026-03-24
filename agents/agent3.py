from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = BASE_DIR / "outputs"
DEFAULT_INPUT_FILE = DEFAULT_OUTPUT_DIR / "agent2_financial_output.csv"
DEFAULT_OUTPUT_FILE = DEFAULT_OUTPUT_DIR / "agent3_compliance_output.csv"


def check_environment(row):
    return "Violation" if row["E_Score"] < 60 else "Compliant"


def check_social(row):
    return "Violation" if row["S_Score"] < 60 else "Compliant"


def check_governance(row):
    if row["G_Score"] < 60 or row["Board_Independence"] < 0.5:
        return "Violation"
    return "Compliant"


def run_agent3(input_path=None, output_path=None):
    source = Path(input_path) if input_path else DEFAULT_INPUT_FILE
    target = Path(output_path) if output_path else DEFAULT_OUTPUT_FILE

    if not source.exists():
        return {
            "error": f"Input file not found: {source}. Run Agent 2 first.",
        }

    try:
        df = pd.read_csv(source)
        df["E_Compliance"] = df.apply(check_environment, axis=1)
        df["S_Compliance"] = df.apply(check_social, axis=1)
        df["G_Compliance"] = df.apply(check_governance, axis=1)

        df["Overall_Compliance"] = df.apply(
            lambda row: "Non-Compliant"
            if "Violation" in [row["E_Compliance"], row["S_Compliance"], row["G_Compliance"]]
            else "Compliant",
            axis=1,
        )

        target.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(target, index=False)
        return df.to_dict(orient="records")
    except Exception as exc:
        return {"error": f"Agent 3 failed: {exc}"}
