# services/search_service.py
import os
import requests
from typing import List
from models import Competitor
from dotenv import load_dotenv

load_dotenv()
SEARCH_API_KEY = os.getenv("GOOGLE_SEARCH_API_KEY")
SEARCH_CX = os.getenv("GOOGLE_SEARCH_CX")
SEARCH_URL = "https://www.googleapis.com/customsearch/v1"
def get_competitor_search(keywords: List[str]) -> List[Competitor]:
    if not keywords:
        return []
        
    # Use the AI's top keyword as the search query
    query = keywords[0] 
    
    params = {
        'key': SEARCH_API_KEY,
        'cx': SEARCH_CX,
        'q': query,
        'num': 3 # Ask for top 3 results
    }
    
    try:
        response = requests.get(SEARCH_URL, params=params)
        response.raise_for_status() # Raise an error for bad responses
        data = response.json()
        
        competitors = []
        if 'items' in data:
            for item in data['items']:
                competitors.append(
                    Competitor(
                        name=item.get('title', 'N/A'),
                        url=item.get('link', 'N/A'),
                        snippet=item.get('snippet', 'N/A')
                    )
                )
        return competitors
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching search results: {e}")
        return []