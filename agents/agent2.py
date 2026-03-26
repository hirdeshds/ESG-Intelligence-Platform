from pathlib import Path

import pandas as pd
from agents.output_paths import get_agent_output_path, get_company_name


def run_agent2(input_path=None, output_path=None, company_id=None):
    company_name = get_company_name(company_id)
    source = Path(input_path) if input_path else get_agent_output_path(
        "agent1_operational_output",
        company_name=company_name,
    )
    target = Path(output_path) if output_path else get_agent_output_path(
        "agent2_financial_output",
        company_name=company_name,
        input_path=source,
    )

    if not source.exists():
        return {
            "error": f"Input file not found: {source}. Run Agent 1 first.",
        }

    try:
        df = pd.read_csv(source)
        score_columns = ["E_Score", "S_Score", "G_Score"]
        df["ESG_Score"] = df[score_columns].apply(pd.to_numeric, errors="coerce").mean(axis=1).round(2)
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
