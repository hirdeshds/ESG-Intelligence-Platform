import os
import json
from pathlib import Path
import pandas as pd
from pymongo import MongoClient
from dotenv import load_dotenv
from agents.output_paths import get_agent_output_path, get_company_name

load_dotenv()

BASE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = BASE_DIR / "outputs"
CONFIG_DIR = BASE_DIR / "config"

def run_explicit_agent1(company_id="company3", output_dir=None):
    target_dir = Path(output_dir) if output_dir else DEFAULT_OUTPUT_DIR
    target_dir.mkdir(parents=True, exist_ok=True)

    print(f"Agent 1: Running explicit extraction for {company_id}...")

    # 1. Load the exact mapping the client provided from the UI
    mapping_file = CONFIG_DIR / f"{company_id}_mapping.json"
    
    if not mapping_file.exists():
        return {"status": "error", "message": f"Mapping file missing for {company_id}. Client must complete UI setup first."}

    with open(mapping_file, "r") as f:
        client_mapping = json.load(f)

    # 2. Connect to MongoDB
    uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    db_name = os.getenv("MONGO_DB_NAME", company_id)
    collection_name = os.getenv("MONGO_COLLECTION", "raw_firm_data")
    
    try:
        client = MongoClient(uri)
        collection = client[db_name][collection_name]

        # 3. Fetch ONLY the columns the client mapped
        # client_mapping.values() contains their weird column names (like "environme")
        columns_to_fetch = {"_id": 0}
        for client_col_name in client_mapping.values():
            columns_to_fetch[client_col_name] = 1

        raw_data = list(collection.find({}, columns_to_fetch))
        
        if not raw_data:
            return {"status": "error", "message": "No data found in the database."}

        df = pd.DataFrame(raw_data)

        # 4. Translate columns to our Standard Format
        # Pandas requires {OldName: NewName}, so we reverse the dictionary
        rename_dict = {client_col: standard_col for standard_col, client_col in client_mapping.items()}
        df = df.rename(columns=rename_dict)

        # 5. Clean and Save
        df = df.dropna(how='all', subset=["E_Score", "ROA"]).reset_index(drop=True)
        
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

    if target_path.exists():
        try:
            existing_df = pd.read_csv(target_path)
            return {
                "status": "success",
                "file_path": str(target_path),
                "rows": len(existing_df),
                "message": "Existing operational output found and reused.",
            }
        except Exception:
            pass

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
