# models.py
from pydantic import BaseModel, Field
from typing import List, Optional


# ─── INPUT MODEL ───
# This is what the API expects from the frontend

class IdeaInput(BaseModel):
    title: str = Field(
        ...,
        description="The name or short title of the startup idea",
        examples=["StudySync - AI Study Planner", "EcoHabit - Daily Sustainability Tracker"]
    )
    description: str = Field(
        ...,
        description="Detailed explanation of the problem, solution, and unique value",
        examples=["An AI-powered app that creates personalized study schedules for college students..."]
    )
    industry: Optional[str] = Field(
        None,
        description="Main industry or category (e.g. EdTech, Health, Fintech)",
        examples=["EdTech", "Sustainability", "Productivity", "Fintech"]
    )
    target_audience: Optional[str] = Field(
        None,
        description="Who the product is primarily for",
        examples=["College students aged 18-24", "Busy working professionals", "Eco-conscious Gen Z"]
    )

    class Config:
        # Allow population by field name or alias (future-proof)
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "title": "StudySync - AI Study Planner",
                "description": "Personalized study schedules and flashcards using AI for university students.",
                "industry": "EdTech",
                "target_audience": "University students"
            }
        }


# ─── COMPONENT MODELS ───

class SWOT(BaseModel):
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    opportunities: List[str] = Field(default_factory=list)
    threats: List[str] = Field(default_factory=list)


class Competitor(BaseModel):
    name: str = Field(..., description="Name or title of the competitor/product")
    url: Optional[str] = Field(None, description="Website or app link")
    snippet: Optional[str] = Field(None, description="Short description or meta description")


class MarketAnalysis(BaseModel):
    audience_profile: str = Field(
        default="Not enough data to generate profile",
        description="Summary description of the typical target user"
    )
    potential_keywords: List[str] = Field(
        default_factory=list,
        description="SEO / search keywords that indicate market interest"
    )


# ─── FINAL RESPONSE MODEL ───

class ValidationReport(BaseModel):
    report_id: str = Field(..., description="Unique UUID of this validation report")
    idea_name: str = Field(..., description="The title of the validated idea")
    overall_score: float = Field(
        ...,
        ge=1.0,
        le=10.0,
        description="Overall viability score (1.0 = very poor, 10.0 = extremely promising)"
    )
    executive_summary: str = Field(
        ...,
        description="Concise summary of potential, strengths, risks and verdict"
    )
    swot_analysis: SWOT
    market_analysis: MarketAnalysis
    competitor_analysis: List[Competitor] = Field(
        default_factory=list,
        description="List of similar or competing products/companies"
    )
    recommended_next_steps: List[str] = Field(
        default_factory=list,
        description="3 practical next actions for the founder"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "report_id": "550e8400-e29b-41d4-a716-446655440000",
                "idea_name": "StudySync - AI Study Planner",
                "overall_score": 7.8,
                "executive_summary": "Strong niche idea in EdTech with growing demand, but faces competition from general productivity tools.",
                "swot_analysis": {
                    "strengths": ["AI personalization", "Low development cost"],
                    "weaknesses": ["Dependency on model quality", "User retention challenge"],
                    "opportunities": ["Remote learning boom", "University partnerships"],
                    "threats": ["Existing apps (Notion, Quizlet, Forest)"]
                },
                "market_analysis": {
                    "audience_profile": "University students 18–25 years old, heavy smartphone users, struggling with time management.",
                    "potential_keywords": [
                        "ai study planner",
                        "student productivity app",
                        "smart study schedule",
                        "college study tool"
                    ]
                },
                "competitor_analysis": [
                    {"name": "Notion", "url": "https://notion.so", "snippet": "All-in-one workspace..."},
                    {"name": "Quizlet", "url": "https://quizlet.com", "snippet": "Flashcards and study tools..."}
                ],
                "recommended_next_steps": [
                    "Build MVP focusing on core AI scheduling feature",
                    "Interview 15–25 students for validation",
                    "Compare freemium vs one-time purchase models"
                ]
            }
        }