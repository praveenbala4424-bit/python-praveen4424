# models.py
from pydantic import BaseModel, Field
from typing import List, Optional

# --- INPUT MODEL ---
# This is the data your API will receive

class IdeaInput(BaseModel):
    idea_name: str
    problem_statement: str = Field(..., max_length=1000)
    solution_description: str = Field(..., max_length=2000)
    target_audience: str = Field(..., max_length=1000)
    
# --- OUTPUT MODELS ---
# These are the nested components of your final report

class SWOT(BaseModel):
    strengths: List[str]
    weaknesses: List[str]
    opportunities: List[str]
    threats: List[str]

class Competitor(BaseModel):
    name: str
    url: str
    snippet: str

class MarketAnalysis(BaseModel):
    audience_profile: str
    potential_keywords: List[str]

# --- FINAL REPORT MODEL ---
# This is the full JSON object your API will send back

class ValidationReport(BaseModel):
    report_id: str
    idea_name: str
    overall_score: float = Field(..., ge=1.0, le=10.0)
    executive_summary: str
    swot_analysis: SWOT
    market_analysis: MarketAnalysis
    competitor_analysis: List[Competitor]
    recommended_next_steps: List[str]