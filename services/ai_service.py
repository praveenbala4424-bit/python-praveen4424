# services/ai_service.py
import os
import json
import re
from typing import Dict, Any, Optional

from dotenv import load_dotenv
import google.generativeai as genai

from models import IdeaInput, SWOT, MarketAnalysis

# ─── Load environment variables ───
load_dotenv()

API_KEY = os.getenv("GOOGLE_API_KEY")
if not API_KEY:
    raise ValueError(
        "GOOGLE_API_KEY not found in .env file. "
        "Please set it: GOOGLE_API_KEY=your-key-here"
    )

genai.configure(api_key=API_KEY)

# Ordered list of models to try (best first)
MODEL_CANDIDATES = [
    "gemini-2.5-flash",               # your preferred / latest
    "gemini-2.5-pro",                 # strong fallback
    "gemini-2.0-flash",               # good balance
    "gemini-2.0-flash-001",
    "gemini-1.5-flash",               # very reliable in many regions
    "gemini-1.5-flash-001",
    "gemini-1.5-pro",
    "gemini-flash-latest",
]

# Global model cache – we initialize lazily and switch on failure
_current_model = None
_current_model_name = None


def get_model():
    """Get or initialize a working Gemini model with automatic fallback"""
    global _current_model, _current_model_name

    if _current_model is not None:
        return _current_model

    for model_name in MODEL_CANDIDATES:
        try:
            print(f"Trying to initialize model: {model_name}")
            model = genai.GenerativeModel(
                model_name=model_name,
                generation_config={
                    "temperature": 0.3,
                    "top_p": 0.95,
                    "top_k": 40,
                    "max_output_tokens": 2048,
                },
                safety_settings={
                    "HARM_CATEGORY_HARASSMENT": "BLOCK_NONE",
                    "HARM_CATEGORY_HATE_SPEECH": "BLOCK_NONE",
                    "HARM_CATEGORY_SEXUALLY_EXPLICIT": "BLOCK_NONE",
                    "HARM_CATEGORY_DANGEROUS_CONTENT": "BLOCK_NONE",
                }
            )
            # Quick test call to verify the model is usable
            test_response = model.generate_content("Say hello")
            if test_response.text:
                print(f"Successfully initialized model: {model_name}")
                _current_model = model
                _current_model_name = model_name
                return model

        except Exception as e:
            err_str = str(e).lower()
            print(f"Model {model_name} failed: {err_str[:120]}...")
            if any(x in err_str for x in ["429", "quota", "rate limit", "resourceexhausted", "503", "unavailable"]):
                print(f"→ Rate limit / quota hit on {model_name}. Trying next model...")
                continue
            elif "not found" in err_str or "unsupported" in err_str:
                print(f"→ Model {model_name} not available in this project/region. Skipping.")
                continue
            else:
                print(f"→ Unexpected error with {model_name}. Skipping.")

    raise RuntimeError(
        "No usable Gemini model could be initialized. "
        "Check your API key, quota, and region restrictions."
    )


def safe_json_parse(text: str) -> Optional[Dict[str, Any]]:
    """
    Extract and parse JSON from model's response.
    Handles code blocks, markdown, extra whitespace, etc.
    """
    if not text or not isinstance(text, str):
        print("safe_json_parse: received empty or invalid input")
        return None

    # Remove common markdown/code fences
    cleaned = re.sub(
        r'^(?:\s*```(?:json)?\s*|\s*```)\s*|\s*(?:```(?:json)?\s*|\s*```)\s*$',
        '',
        text.strip(),
        flags=re.MULTILINE | re.IGNORECASE
    )

    # Extract the first JSON object-like structure
    match = re.search(r'\{.*\}', cleaned, re.DOTALL)
    if match:
        cleaned = match.group(0)

    try:
        parsed = json.loads(cleaned)
        if isinstance(parsed, dict):
            return parsed
        else:
            print(f"Parsed result is not a dict: {type(parsed)}")
            return None
    except json.JSONDecodeError as e:
        print(f"JSON decode failed:\nFirst 300 chars: {text[:300]}...\nError: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error in safe_json_parse: {e}")
        return None


def get_swot_analysis(idea: IdeaInput) -> SWOT:
    """Generate SWOT analysis using Gemini with fallback"""
    prompt = f"""\
You are an experienced startup advisor.
Analyze this startup idea:

Title: {idea.title}
Description: {idea.description}
Industry: {idea.industry or "Not specified"}
Target audience: {idea.target_audience or "Not specified"}

Create a realistic SWOT analysis.
Return **only** valid JSON with these exact keys:
{{
  "strengths": list of strings,
  "weaknesses": list of strings,
  "opportunities": list of strings,
  "threats": list of strings
}}
No explanations, no markdown, no extra text.
"""

    try:
        model = get_model()
        response = model.generate_content(prompt)
        data = safe_json_parse(response.text)

        if data and isinstance(data, dict):
            return SWOT(**data)

        print("SWOT: Invalid or empty JSON from model")
        return SWOT(
            strengths=["Could not generate SWOT analysis"],
            weaknesses=["AI response was malformed"],
            opportunities=[],
            threats=[]
        )

    except Exception as e:
        print(f"SWOT analysis failed: {str(e)[:200]}...")
        return SWOT(
            strengths=["Service temporarily unavailable"],
            weaknesses=[str(e)],
            opportunities=[],
            threats=[]
        )


def get_market_analysis(idea: IdeaInput) -> MarketAnalysis:
    """Generate target audience profile and search keywords"""
    prompt = f"""\
You are a market research expert.
For this startup idea:

Title: {idea.title}
Description: {idea.description}
Industry: {idea.industry or "Not specified"}
Target audience: {idea.target_audience or "Not specified"}

1. Write a concise "audience_profile" (2–4 sentences) describing the typical user.
2. Provide 6–12 realistic "potential_keywords" people might search on Google.

Return **only** valid JSON:
{{
  "audience_profile": string,
  "potential_keywords": list of strings
}}
Nothing else.
"""

    try:
        model = get_model()
        response = model.generate_content(
            prompt,
            generation_config={"temperature": 0.1}
        )
        
        data = safe_json_parse(response.text)

        if data and isinstance(data, dict):
            return MarketAnalysis(**data)

        print("Market analysis: Invalid JSON received")
        return MarketAnalysis(
            audience_profile="Could not generate profile due to formatting issue",
            potential_keywords=[]
        )

    except Exception as e:
        print(f"Market analysis failed: {str(e)[:200]}...")
        return MarketAnalysis(
            audience_profile=f"Service error: {str(e)}",
            potential_keywords=[]
        )