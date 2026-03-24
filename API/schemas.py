from pydantic import BaseModel, Field
from typing import List, Optional

class ESGFirmBase(BaseModel):
    """The core data structure for an ESG record."""
    Firm_ID: str = Field(..., example="FIRM_001")
    Year: int = Field(..., example=2024)
    Industry_Type: str = Field(..., example="Manufacturing")
    E_Score: float = Field(..., ge=0, le=100)
    S_Score: float = Field(..., ge=0, le=100)
    G_Score: float = Field(..., ge=0, le=100)
    Board_Independence: float = Field(..., ge=0, le=1.0)

class ESGRiskResponse(ESGFirmBase):
    """Data returned when checking risk levels."""
    final_esg_risk_score: Optional[float] = None
    alert_level: Optional[str] = Field(None, example="Critical")
    Overall_Compliance: Optional[str] = "Compliant"

class RiskSummary(BaseModel):
    """Structure for the dashboard 'Risk Summary' widget."""
    Critical: int = 0
    Warning: int = 0
    Low: int = 0

class PredictionRequest(BaseModel):
    """Input for the Machine Learning prediction agent."""
    risk_score: float