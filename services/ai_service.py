# services/ai_service.py
import os
import json
import google.generativeai as genai
from dotenv import load_dotenv
from models import IdeaInput, SWOT, MarketAnalysis # Import your models

# Load API key from .env file
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Set up the generative model
# model = genai.GenerativeModel('gemini-1.5-flash-latest')
try:
    model = genai.GenerativeModel("gemini-2.5-flash")
except Exception as e:
    print("Model initialization failed:", e)

# Helper function to safely parse JSON from AI
def safe_json_parse(text_response):
    # The AI might wrap the JSON in ```json ... ```
    if "```json" in text_response:
        text_response = text_response.split("```json", 1)[1].rsplit("```", 1)[0]
    try:
        return json.loads(text_response)
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from AI response: {text_response}")
        return None

def get_swot_analysis(idea: IdeaInput) -> SWOT:
    prompt = f"""
    You are a startup mentor. Analyze the following startup idea:
    Problem: {idea.problem_statement}
    Solution: {idea.solution_description}
    Audience: {idea.target_audience}
    
    Generate a detailed SWOT analysis.
    Return your response as a valid JSON object ONLY, with keys "strengths", "weaknesses", "opportunities", and "threats". Each key should have a list of strings.
    """
    
    response = model.generate_content(prompt)
    json_data = safe_json_parse(response.text)
    
    if json_data:
        return SWOT(**json_data) # Validate data using the Pydantic model
    return SWOT(strengths=["Error generating data"], weaknesses=[], opportunities=[], threats=[])


def get_market_analysis(idea: IdeaInput) -> MarketAnalysis:
    prompt = f"""
    You are a market analyst. For the following startup idea:
    Problem: {idea.problem_statement}
    Solution: {idea.solution_description}
    Audience: {idea.target_audience}
    
    Generate a brief "audience_profile" describing the target user.
    Also, generate a list of 5-10 "potential_keywords" they would use on Google.
    Return a valid JSON object ONLY with keys "audience_profile" (a string) and "potential_keywords" (a list of strings).
    """
    
    response = model.generate_content(prompt,generation_config={'temperature':0.0})
    json_data = safe_json_parse(response.text)
    
    if json_data:
        return MarketAnalysis(**json_data)
    return MarketAnalysis(audience_profile="Error generating data", potential_keywords=[])

# Add more functions here for next_steps, summary, etc.
# ...