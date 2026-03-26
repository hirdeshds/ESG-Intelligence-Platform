import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[1]
BASE_OUTPUT_DIR = BASE_DIR / "outputs"
ENV_FILE = BASE_DIR / "config" / ".env"
DEFAULT_COMPANY_NAME = "company_database"
DEFAULT_FIRM_ID = "TECH001"


def reload_env():
    load_dotenv(ENV_FILE, override=True)


def get_company_name(company_name=None):
    reload_env()
    if company_name:
        return company_name
    return os.getenv("MONGO_FIRM_ID") or os.getenv("MONGO_DB_NAME", DEFAULT_COMPANY_NAME)


def get_company_output_dir(company_name=None, input_path=None):
    if input_path:
        source = Path(input_path)
        if source.parent.name and source.parent != BASE_OUTPUT_DIR:
            return source.parent
    return BASE_OUTPUT_DIR / get_company_name(company_name)


def get_agent_output_path(agent_label, company_name=None, input_path=None):
    resolved_company = get_company_name(company_name)
    output_dir = get_company_output_dir(company_name=resolved_company, input_path=input_path)
    return output_dir / f"{resolved_company}_{agent_label}.csv"
