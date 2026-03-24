import os
from pathlib import Path

import pandas as pd

try:
    from sqlalchemy import create_engine, inspect
except ImportError:  # Optional until the sync endpoint is used with a real DB.
    create_engine = None
    inspect = None

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = BASE_DIR / "outputs"
DEFAULT_SAMPLE_CSV = BASE_DIR / "csv files" / "basic_sample.csv"


def run_agent1(user_mapping, output_path):
    if create_engine is None or inspect is None:
        return {
            "status": "error",
            "message": "Missing dependency: sqlalchemy. Install project requirements to use database sync.",
        }

    db_url = os.getenv("COMPANY_DB_URL")
    if not db_url:
        return {
            "status": "error",
            "message": "COMPANY_DB_URL is not set.",
        }

    engine = create_engine(db_url)

    try:
        inspector = inspect(engine)
        db_columns = [col["name"] for col in inspector.get_columns(user_mapping["table"])]

        required_keys = ["year_col", "ind_col", "env_col", "soc_col", "gov_col", "board_col"]
        missing_columns = []

        for key in required_keys:
            col_name = user_mapping[key]
            if col_name not in db_columns:
                missing_columns.append(col_name)

        if missing_columns:
            return {
                "status": "error",
                "message": f"Mapping failed. The following columns do not exist in the database: {', '.join(missing_columns)}",
                "available_columns": db_columns,
            }

        query = f"""
        SELECT
            {user_mapping['year_col']} AS Year,
            {user_mapping['ind_col']} AS Industry_Type,
            {user_mapping['env_col']} AS E_Score,
            {user_mapping['soc_col']} AS S_Score,
            {user_mapping['gov_col']} AS G_Score,
            {user_mapping['board_col']} AS Board_Independence
        FROM {user_mapping['table']}
        """

        df = pd.read_sql(query, engine)
        df = df.dropna().reset_index(drop=True)

        output_dir = Path(output_path)
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / "agent1_operational_output.csv"
        df.to_csv(output_file, index=False)

        return {
            "status": "success",
            "message": "Data successfully fetched and mapped",
            "file_path": str(output_file),
        }

    except Exception as exc:
        return {
            "status": "error",
            "message": f"System Error: {exc}",
        }


def sync_and_clean_pipeline(sample_csv_path=None, output_dir=None):
    input_csv = Path(sample_csv_path) if sample_csv_path else DEFAULT_SAMPLE_CSV
    target_dir = Path(output_dir) if output_dir else DEFAULT_OUTPUT_DIR
    target_dir.mkdir(parents=True, exist_ok=True)

    if not input_csv.exists():
        return {
            "status": "error",
            "message": f"Sample input file not found: {input_csv}",
        }

    try:
        df = pd.read_csv(input_csv).dropna().reset_index(drop=True)
        output_file = target_dir / "agent1_operational_output.csv"
        df.to_csv(output_file, index=False)
        return {
            "status": "success",
            "message": "Agent 1 completed successfully",
            "file_path": str(output_file),
            "rows_processed": int(len(df)),
        }
    except Exception as exc:
        return {
            "status": "error",
            "message": f"Agent 1 failed: {exc}",
        }
