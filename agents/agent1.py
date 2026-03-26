import json
import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from pymongo import MongoClient

from agents.output_paths import get_agent_output_path, get_company_name

load_dotenv()

BASE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = BASE_DIR / "outputs"
CONFIG_DIR = BASE_DIR / "config"
REQUIRED_COLUMNS = [
    "Year",
    "Industry_Type",
    "E_Score",
    "S_Score",
    "G_Score",
    "ROA",
    "ROE",
    "Net Profit Margin",
]


def _get_client():
    uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    return MongoClient(uri)


def _candidate_db_names(company_id):
    names = []
    for value in [os.getenv("MONGO_DB_NAME"), company_id, "company_database"]:
        if value and value not in names:
            names.append(value)
    return names


def list_available_companies():
    try:
        client = _get_client()
        db_name = os.getenv("MONGO_DB_NAME", "company_database")
        records = list(
            client[db_name]["company_info"].find(
                {},
                {
                    "_id": 0,
                    "firm_id": 1,
                    "sector": 1,
                    "Industry_Type": 1,
                    "firm_size_employees": 1,
                },
            )
        )
        return sorted(records, key=lambda item: item.get("firm_id", ""))
    except Exception as exc:
        return {"error": f"Could not fetch companies from MongoDB: {exc}"}


def _build_standard_frame(records):
    df = pd.DataFrame(records)

    for column in REQUIRED_COLUMNS:
        if column not in df.columns:
            df[column] = None

    df = df[REQUIRED_COLUMNS].copy()
    df = df.dropna(how="all", subset=["E_Score", "S_Score", "G_Score", "ROA", "ROE", "Net Profit Margin"])
    df = df.sort_values(by=["Year", "Industry_Type"], na_position="last").reset_index(drop=True)
    return df


def _load_from_mapped_collection(db, company_id):
    mapping_file = CONFIG_DIR / f"{company_id}_mapping.json"
    if not mapping_file.exists():
        return None, f"Mapping file missing for {company_id}."

    with open(mapping_file, "r", encoding="utf-8") as file_obj:
        client_mapping = json.load(file_obj)

    collection_name = os.getenv("MONGO_COLLECTION", "raw_firm_data")
    collection = db[collection_name]

    columns_to_fetch = {"_id": 0}
    for client_col_name in client_mapping.values():
        columns_to_fetch[client_col_name] = 1

    query = {}
    if company_id and company_id.upper() == company_id:
        query = {"Firm_ID": company_id}

    raw_data = list(collection.find(query, columns_to_fetch))
    if not raw_data:
        return None, f"No data found in collection '{collection_name}'."

    df = pd.DataFrame(raw_data)
    rename_dict = {client_col: standard_col for standard_col, client_col in client_mapping.items()}
    df = df.rename(columns=rename_dict)

    for column in REQUIRED_COLUMNS:
        if column not in df.columns:
            df[column] = None

    return df[REQUIRED_COLUMNS].copy(), None


def _load_from_split_collections(db, firm_id=None):
    base_query = {"firm_id": firm_id} if firm_id else {}

    company_info = list(
        db["company_info"].find(base_query, {"_id": 0, "firm_id": 1, "sector": 1, "Industry_Type": 1})
    )
    sustainability_logs = list(
        db["sustainability_logs"].find(
            base_query,
            {
                "_id": 0,
                "firm_id": 1,
                "fiscal_year": 1,
                "Year": 1,
                "e_score_raw": 1,
                "s_score_raw": 1,
                "g_score_raw": 1,
                "E_Score": 1,
                "S_Score": 1,
                "G_Score": 1,
            },
        )
    )
    finance_data = list(
        db["finance_data"].find(
            base_query,
            {
                "_id": 0,
                "firm_id": 1,
                "fiscal_year": 1,
                "Year": 1,
                "roa_pct": 1,
                "roe_pct": 1,
                "net_margin": 1,
                "ROA": 1,
                "ROE": 1,
                "Net Profit Margin": 1,
            },
        )
    )

    if not sustainability_logs and not finance_data:
        return None, "No data found in split MongoDB collections."

    info_df = pd.DataFrame(company_info)
    if info_df.empty:
        info_df = pd.DataFrame(columns=["firm_id", "sector", "Industry_Type"])
    info_df["Industry_Type"] = info_df.get("Industry_Type", info_df.get("sector"))
    info_df = info_df[["firm_id", "Industry_Type"]].drop_duplicates()

    esg_df = pd.DataFrame(sustainability_logs)
    if not esg_df.empty:
        esg_df["Year"] = esg_df.get("Year", esg_df.get("fiscal_year"))
        esg_df["E_Score"] = esg_df.get("E_Score", esg_df.get("e_score_raw"))
        esg_df["S_Score"] = esg_df.get("S_Score", esg_df.get("s_score_raw"))
        esg_df["G_Score"] = esg_df.get("G_Score", esg_df.get("g_score_raw"))
        esg_df = esg_df[["firm_id", "Year", "E_Score", "S_Score", "G_Score"]]
    else:
        esg_df = pd.DataFrame(columns=["firm_id", "Year", "E_Score", "S_Score", "G_Score"])

    finance_df = pd.DataFrame(finance_data)
    if not finance_df.empty:
        finance_df["Year"] = finance_df.get("Year", finance_df.get("fiscal_year"))
        finance_df["ROA"] = finance_df.get("ROA", finance_df.get("roa_pct"))
        finance_df["ROE"] = finance_df.get("ROE", finance_df.get("roe_pct"))
        finance_df["Net Profit Margin"] = finance_df.get("Net Profit Margin", finance_df.get("net_margin"))
        finance_df = finance_df[["firm_id", "Year", "ROA", "ROE", "Net Profit Margin"]]
    else:
        finance_df = pd.DataFrame(columns=["firm_id", "Year", "ROA", "ROE", "Net Profit Margin"])

    merged_df = pd.merge(esg_df, finance_df, on=["firm_id", "Year"], how="outer")
    merged_df = pd.merge(merged_df, info_df, on="firm_id", how="left")
    merged_df = merged_df.drop(columns=["firm_id"], errors="ignore")
    return merged_df, None


def run_explicit_agent1(company_id="company3", output_dir=None):
    target_dir = Path(output_dir) if output_dir else DEFAULT_OUTPUT_DIR
    target_dir.mkdir(parents=True, exist_ok=True)

    print(f"Agent 1: Running explicit extraction for {company_id}...")

    try:
        client = _get_client()
        df = None
        errors = []

        for db_name in _candidate_db_names(company_id):
            db = client[db_name]

            mapped_df, mapped_error = _load_from_mapped_collection(db, company_id)
            if mapped_df is not None:
                df = mapped_df
                break

            split_df, split_error = _load_from_split_collections(db, firm_id=company_id)
            if split_df is not None:
                df = split_df
                break

            errors.append(f"{db_name}: {mapped_error} {split_error}")

        if df is None:
            return {
                "status": "error",
                "message": "Agent 1 could not load data from MongoDB. " + " | ".join(errors),
            }

        df = _build_standard_frame(df.to_dict(orient="records"))

        if df.empty:
            return {"status": "error", "message": "No usable data found for the required Agent 1 columns."}

        output_file = target_dir / f"{company_id}_master.csv"
        df.to_csv(output_file, index=False)

        print(f"Success! Standardized CSV created at {output_file}")
        return {"status": "success", "file_path": str(output_file), "rows": len(df)}
    except Exception as exc:
        return {"status": "error", "message": f"Agent 1 failed: {exc}"}


def sync_and_clean_pipeline(company_id=None, output_dir=None):
    company_name = get_company_name(company_id)
    target_path = get_agent_output_path(
        "agent1_operational_output",
        company_name=company_name,
    )

    explicit_result = run_explicit_agent1(company_id=company_name, output_dir=output_dir)
    if explicit_result.get("status") != "success":
        return explicit_result

    source_path = Path(explicit_result["file_path"])
    target_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        df = pd.read_csv(source_path)
        df.to_csv(target_path, index=False)
        return {
            "status": "success",
            "file_path": str(target_path),
            "rows": len(df),
            "message": "Operational output generated successfully.",
        }
    except Exception as exc:
        return {"status": "error", "message": f"Agent 1 failed while writing operational output: {exc}"}


if __name__ == "__main__":
    run_explicit_agent1()
