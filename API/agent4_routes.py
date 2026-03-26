# API/agent4_routes.py
from fastapi import APIRouter, HTTPException
from agents.agent4 import run_agent4

router = APIRouter(prefix="/agent4", tags=["Final Risk Assessment"])

@router.get("/get-final-summary")
def get_final_risk_report():
    """
    Triggers Agent 4 to calculate Final Risk Scores and Alert Levels 
    based on Agent 3's compliance data.
    """
    try:
        # This calls your agent4 logic and returns the filtered DataFrame as a dict
        result = run_agent4()
        
        # If the agent returns an error (like file not found)
        if isinstance(result, dict) and "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
            
        return {
            "status": "Final Risk Analysis Completed",
            "report_summary": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
