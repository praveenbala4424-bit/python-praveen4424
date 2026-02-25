# services/pipeline_service.py
import uuid
from typing import List

from models import IdeaInput, ValidationReport, SWOT, MarketAnalysis, Competitor
from services.ai_service import get_swot_analysis, get_market_analysis, safe_json_parse, get_model
from services.search_service import get_competitor_search


def run_validation_pipeline(idea: IdeaInput) -> ValidationReport:
    """
    Runs the full validation pipeline for a startup idea.
    Returns a complete ValidationReport.
    """
    # Safe title fallback
    idea_title = idea.title.strip() if idea.title else "Untitled Idea"
    idea_industry = idea.industry or "not specified"

    print(f"Starting validation pipeline for: '{idea_title}' (industry: {idea_industry})")

    # Step 1 & 2: Core analyses
    swot_data: SWOT = get_swot_analysis(idea)
    market_data: MarketAnalysis = get_market_analysis(idea)

    # Step 3: Competitor search based on market keywords
    competitor_data: List[Competitor] = get_competitor_search(
        market_data.potential_keywords
    )

    # Step 4: Final AI summary + scoring
    summary_prompt = f"""
You are an experienced startup investor and product strategist.

Analyze the following startup idea with all available data:

Idea Title: {idea_title}
Description: {idea.description or "No description provided"}
Industry/Category: {idea_industry}
Target Audience: {idea.target_audience or "Not specified"}

SWOT Analysis:
{swot_data.model_dump_json(indent=2)}

Market Analysis:
{market_data.model_dump_json(indent=2)}

Competitors Found:
{[c.model_dump_json(indent=2) for c in competitor_data]}

Based on ALL this information, produce a concise, honest evaluation in valid JSON format ONLY.
Required keys:
- "executive_summary": a short paragraph (80-150 words) summarizing viability, strengths & main risks
- "overall_score": float between 1.0 and 10.0 (10 = extremely promising)
- "recommended_next_steps": list of exactly 3 practical next actions (strings)

Return ONLY the JSON object. No extra text, no markdown, no explanations.
"""

    try:
        # ─── FIXED: Call the function to get the actual model ───
        model = get_model()
        response = model.generate_content(summary_prompt)
        final_data = safe_json_parse(response.text)

        if not isinstance(final_data, dict):
            raise ValueError("AI response was not parsed into a dictionary")

    except Exception as e:
        print(f"Error in final summary generation: {str(e)[:300]}...")
        final_data = {
            "executive_summary": "Unable to generate final summary due to an error.",
            "overall_score": 1.0,
            "recommended_next_steps": [
                "Verify the AI service configuration",
                "Check prompt formatting and model availability",
                "Test with a simpler idea first"
            ]
        }

    # Step 5: Build final report
    report = ValidationReport(
        report_id=str(uuid.uuid4()),
        idea_name=idea_title,
        overall_score=float(final_data.get("overall_score", 1.0)),
        executive_summary=final_data.get(
            "executive_summary",
            "No summary could be generated."
        ),
        swot_analysis=swot_data,
        market_analysis=market_data,
        competitor_analysis=competitor_data,
        recommended_next_steps=final_data.get("recommended_next_steps", [])
    )

    return report