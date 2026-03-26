# API/agent3_routes.py
from fastapi import APIRouter, HTTPException
from agents.agent3 import run_agent3

router = APIRouter(prefix="/agent3", tags=["Compliance Audit"])

@router.get("/audit")
def get_compliance_results():
    result = run_agent3()
    
    # Error handling if Agent 2 hasn't run yet
    if isinstance(result, dict) and "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
        
    return {
        "status": "Compliance Audit Completed",
        "compliance_summary": result
    }
