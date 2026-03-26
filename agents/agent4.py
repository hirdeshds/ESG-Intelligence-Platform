from pathlib import Path

import pandas as pd
from agents.output_paths import get_agent_output_path, get_company_name


def run_agent4(input_path=None, output_path=None, company_id=None):
    company_name = get_company_name(company_id)
    source = Path(input_path) if input_path else get_agent_output_path(
        "agent3_compliance_output",
        company_name=company_name,
    )
    target = Path(output_path) if output_path else get_agent_output_path(
        "agent4_final_output",
        company_name=company_name,
        input_path=source,
    )

    if not source.exists():
        return {
            "error": f"Input file not found: {source}. Run Agent 3 first.",
        }

    try:
        df = pd.read_csv(source)

        # Normalize firm identifier across datasets.
        if "Firm_ID" not in df.columns:
            if "firm_id" in df.columns:
                df = df.rename(columns={"firm_id": "Firm_ID"})
            else:
                df["Firm_ID"] = company_name

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
        report_columns = ["Firm_ID", "Year", "Overall_Compliance", "final_esg_risk_score", "alert_level"]
        for column in report_columns:
            if column not in df.columns:
                df[column] = pd.NA
        report = df[report_columns]
        report.to_csv(target, index=False)
        return report.to_dict(orient="records")
    except Exception as exc:
        return {"error": f"Agent 4 failed: {exc}"}
