# API/agent5_routes.py
from fastapi import APIRouter, HTTPException
from agents.agent5 import run_agent5

router = APIRouter(prefix="/agent5", tags=["AI Explainability"])

@router.get("/explain")
def get_risk_explanation():
    """
    Triggers Agent 5 to provide SHAP-based explanations 
    for the ESG risk levels calculated in Agent 4.
    """
    result = run_agent5()
    
    if isinstance(result, dict) and "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
        
    return result
