# services/pipeline_service.py
import uuid
from models import IdeaInput, ValidationReport, SWOT, MarketAnalysis, Competitor
from services.ai_service import get_swot_analysis, get_market_analysis, model, safe_json_parse
from services.search_service import get_competitor_search
from typing import List

def run_validation_pipeline(idea: IdeaInput) -> ValidationReport:
    # --- Step 1 & 2: Run core analyses in parallel (or sequentially) ---
    print(f"Starting pipeline for: {idea.idea_name}")
    swot_data = get_swot_analysis(idea)
    market_data = get_market_analysis(idea)
    
    # --- Step 3: Use market data to run search ---
    competitor_data = get_competitor_search(market_data.potential_keywords)
    
    # --- Step 4 & 5: Generate Final Summary, Score, & Next Steps ---
    # We do this last, giving the AI all context
    
    summary_prompt = f"""
    You are a senior investor. You have the following analysis for an idea:
    Idea: {idea.idea_name}
    SWOT: {swot_data.model_dump_json()}
    Market: {market_data.model_dump_json()}
    Competitors: {[c.model_dump_json() for c in competitor_data]}

    Based on ALL this data, generate:
    1. A concise "executive_summary" (string).
    2. An "overall_score" (float between 1.0 and 10.0).
    3. A "recommended_next_steps" (list of 3 string actions).
    
    Return a valid JSON object ONLY with keys "executive_summary", "overall_score", and "recommended_next_steps".
    """
    
    response = model.generate_content(summary_prompt)
    final_data = safe_json_parse(response.text)
    
    if not final_data:
        # Handle failure
        final_data = {
            "executive_summary": "Error generating final summary.",
            "overall_score": 1.0,
            "recommended_next_steps": ["Debug AI summary prompt."]
        }

    # --- Step 6: Assemble the Final Report ---
    report = ValidationReport(
        report_id=str(uuid.uuid4()), # Generate a unique ID
        idea_name=idea.idea_name,
        overall_score=final_data.get("overall_score", 1.0),
        executive_summary=final_data.get("executive_summary", "Error"),
        swot_analysis=swot_data,
        market_analysis=market_data,
        competitor_analysis=competitor_data,
        recommended_next_steps=final_data.get("recommended_next_steps", [])
    )
    
    print(f"Pipeline complete for: {idea.idea_name}")
    return report