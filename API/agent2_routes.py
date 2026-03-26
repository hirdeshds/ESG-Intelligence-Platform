# API/agent2_routes.py
from fastapi import APIRouter, HTTPException
from agents.agent2 import run_agent2

router = APIRouter(prefix="/agent2", tags=["Financial Analysis"])

@router.get("/process")
def get_agent2_results():
    result = run_agent2()
    
    # If the agent returned an error (like file not found)
    if isinstance(result, dict) and "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
        
    return {
        "status": "Agent 2 completed successfully",
        "data": result
    }
