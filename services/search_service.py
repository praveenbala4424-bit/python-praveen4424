# services/search_service.py
import os
import requests
from typing import List, Optional
from dotenv import load_dotenv

from models import Competitor

# ─── Load environment variables ───
load_dotenv()

SEARCH_API_KEY = os.getenv("GOOGLE_SEARCH_API_KEY")
SEARCH_CX = os.getenv("GOOGLE_SEARCH_CX")
SEARCH_URL = "https://www.googleapis.com/customsearch/v1"

# Basic validation at module level (runs once on import)
if not SEARCH_API_KEY or not SEARCH_CX:
    print("WARNING: Google Custom Search API credentials missing!")
    print("  → Set GOOGLE_SEARCH_API_KEY and GOOGLE_SEARCH_CX in .env file")
    print("  → Get them at: https://developers.google.com/custom-search/v1/overview")


def get_competitor_search(keywords: List[str], max_results: int = 6) -> List[Competitor]:
    """
    Search for potential competitors using Google Custom Search JSON API.
    
    Args:
        keywords: List of potential search keywords from market analysis
        max_results: Max number of results to return (default 6)
    
    Returns:
        List of Competitor objects (name, url, snippet)
    """
    if not keywords or not SEARCH_API_KEY or not SEARCH_CX:
        print("Skipping competitor search: no keywords or missing API credentials")
        return []

    # Use top 3–5 keywords → better relevance than just first one
    top_keywords = keywords[:5]
    query = " OR ".join(f'"{k}"' for k in top_keywords if k.strip())

    if not query.strip():
        print("No valid keywords for competitor search")
        return []

    params = {
        "key": SEARCH_API_KEY,
        "cx": SEARCH_CX,
        "q": query,
        "num": min(max_results, 10),  # Google API max is 10 per request
    }

    headers = {
        "User-Agent": "TrendSpark/1.0 (College Project; +https://github.com/your-repo)"
    }

    try:
        response = requests.get(
            SEARCH_URL,
            params=params,
            headers=headers,
            timeout=12,              # prevent hanging forever
        )
        response.raise_for_status()

        data = response.json()

        competitors: List[Competitor] = []

        items = data.get("items", [])
        for item in items[:max_results]:
            snippet = item.get("snippet", "No description available")
            # Clean up snippet (remove extra spaces/newlines)
            snippet = " ".join(snippet.split())

            competitors.append(
                Competitor(
                    name=item.get("title", "Untitled Result"),
                    url=item.get("link", "#"),
                    snippet=snippet,
                )
            )

        print(f"Found {len(competitors)} potential competitors for query: {query[:80]}...")
        return competitors

    except requests.exceptions.HTTPError as e:
        status = e.response.status_code if e.response else "unknown"
        print(f"Google Search API HTTP error {status}: {e}")
        if status == 429:
            print("→ Rate limit exceeded. Consider waiting or upgrading quota.")
        elif status == 403:
            print("→ API key or CX invalid / quota exceeded.")
        return []

    except requests.exceptions.RequestException as e:
        print(f"Network/search error during competitor lookup: {e}")
        return []

    except ValueError as e:
        print(f"JSON decode error from Google API: {e}")
        return []

    except Exception as e:
        print(f"Unexpected error in get_competitor_search: {e}")
        return []