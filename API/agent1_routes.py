from fastapi import APIRouter, HTTPException

from agents.agent1 import list_available_companies, sync_and_clean_pipeline

router = APIRouter(prefix="/agent1", tags=["Data Synchronization"])


@router.post("/sync")
def trigger_data_sync():
    """
    Triggers Agent 1 to fetch raw data from storage,
    clean it, and generate the operational CSV.
    """
    result = sync_and_clean_pipeline()

    if result.get("status") == "error":
        raise HTTPException(status_code=500, detail=result["message"])

    return result


@router.get("/companies")
def get_available_companies():
    result = list_available_companies()
    if isinstance(result, dict) and "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    return {"status": "success", "companies": result}
