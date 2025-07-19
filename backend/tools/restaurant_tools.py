"""Restaurant search tools for the AI Food-Ordering Assistant."""

import json
import logging
from typing import List, Dict, Any

from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage
from langchain.tools import tool

from config import RESTAURANT_SEARCH_MODEL, OPENAI_API_KEY

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Search‑restaurants TOOL (OpenAI function‑call)
# ---------------------------------------------------------------------------
@tool(
    "search_restaurants",
    args_schema=None,
    return_direct=True,
)
def search_restaurants_tool(query: str) -> List[Dict[str, Any]]:
    """Search for restaurants and return the 10 best options for the query.

    Args:
        query: A natural‑language query describing cuisine, head‑count, budget, location, etc.

    Returns:
        A list with exactly ten dicts in this shape::
            {
                "rank": int,  # 1-based ranking (1..10)
                "name": str,
                "description": str,  # Brief description of the restaurant and why it fits
                "url": str,  # Restaurant website or menu URL
                "image_url": str,  # URL to restaurant image
                "price": int,  # Price estimate in dollars (e.g., 15, 25, 45, 80)
                "phone": str,  # Restaurant phone number
                "notes": str  # Additional notes about ordering, capacity, etc.
            }

    The function uses OpenAI's o3 model to find and structure real restaurant information.
    """
    
    # Use the dedicated restaurant search model (o3 by default, but fallback to other models if needed)
    try:
        # For o3 model, explicitly set temperature to 1 (the only supported value)
        if RESTAURANT_SEARCH_MODEL == "o3":
            llm = ChatOpenAI(
                model_name=RESTAURANT_SEARCH_MODEL, 
                temperature=1,  # o3 only supports temperature=1
                api_key=OPENAI_API_KEY
            )
        # For other models that don't support custom temperature, don't set it
        elif RESTAURANT_SEARCH_MODEL in ["gpt-4o-mini", "gpt-3.5-turbo"]:
            llm = ChatOpenAI(
                model_name=RESTAURANT_SEARCH_MODEL, 
                api_key=OPENAI_API_KEY
            )
        else:
            llm = ChatOpenAI(
                model_name=RESTAURANT_SEARCH_MODEL, 
                temperature=0.1,
                api_key=OPENAI_API_KEY
            )
    except Exception as e:
        logger.warning(f"Failed to create LLM with {RESTAURANT_SEARCH_MODEL}, falling back to gpt-4o: {e}")
        llm = ChatOpenAI(
            model_name="gpt-4o", 
            api_key=OPENAI_API_KEY
        )
    
    logger.info(f"Searching restaurants for query: {query} using model: {llm.model_name}")

    system_prompt = """You are an expert restaurant concierge with extensive knowledge of restaurants worldwide. 
    
    Your task is to recommend exactly 10 real restaurants that best match the user's requirements. 
    
    For each restaurant, provide:
    - Real restaurant names (not generic or made-up names)
    - Brief descriptions explaining why each restaurant fits the request
    - Restaurant website URLs or menu links
    - Image URLs for restaurant photos
    - Price estimates in dollars (e.g., 15, 25, 45, 80)
    - Restaurant phone numbers in proper format
    - Additional notes about ordering, capacity, delivery, etc.
    
    Focus on restaurants that can actually handle the specified group size and requirements.
    
    Return ONLY a valid JSON array with exactly 10 restaurants, each having these fields:
    - rank: integer from 1 to 10
    - name: string (real restaurant name)
    - description: string (brief description of restaurant and why it fits)
    - url: string (restaurant website or menu URL)
    - image_url: string (URL to restaurant image)
    - price: integer (price estimate in dollars)
    - phone: string (restaurant phone number)
    - notes: string (additional notes about ordering, capacity, etc.)
    
    Example format:
    [
        {
            "rank": 1,
            "name": "Mario's Italian Bistro",
            "description": "Family-owned Italian restaurant specializing in authentic wood-fired pizzas and pasta. Perfect for large groups with their spacious dining area and catering services.",
            "url": "https://mariositalianbistro.com",
            "image_url": "https://example.com/marios-bistro.jpg",
            "price": 25,
            "phone": "+1 (555) 123-4567",
            "notes": "Offers group discounts for 20+ people. Requires 24-hour advance notice for large orders. Free delivery within 5 miles."
        }
    ]"""

    human_prompt = f"""Find 10 real restaurants that best match this request: {query}

    Consider factors like:
    - Cuisine type requested
    - Group size and capacity
    - Location/delivery area
    - Budget constraints
    - Dietary restrictions
    - Timing requirements

    Provide practical, actionable restaurant recommendations with real contact information."""

    try:
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_prompt)
        ]
        
        response = llm.invoke(messages)
        logger.info(f"Raw LLM response: {response.content[:200]}...")
        
        # Parse the JSON response
        restaurants = json.loads(response.content)
        
        # Validate the response structure
        if not isinstance(restaurants, list):
            raise ValueError("Response is not a list")
        
        if len(restaurants) != 10:
            logger.warning(f"Expected 10 restaurants, got {len(restaurants)}")
        
        # Ensure each restaurant has required fields
        required_fields = ["rank", "name", "description", "url", "image_url", "price", "phone", "notes"]
        validated_restaurants = []
        
        for i, restaurant in enumerate(restaurants[:10]):  # Take only first 10
            if not isinstance(restaurant, dict):
                logger.error(f"Restaurant {i} is not a dict: {restaurant}")
                continue
                
            # Ensure all required fields are present
            validated_restaurant = {}
            for field in required_fields:
                if field in restaurant:
                    validated_restaurant[field] = restaurant[field]
                else:
                    logger.warning(f"Missing field '{field}' in restaurant {i}")
                    validated_restaurant[field] = None
            
            # Ensure rank is an integer
            try:
                validated_restaurant["rank"] = int(validated_restaurant["rank"])
            except (ValueError, TypeError):
                validated_restaurant["rank"] = i + 1
            
            # Ensure price is an integer
            try:
                validated_restaurant["price"] = float(validated_restaurant["price"])
            except (ValueError, TypeError):
                validated_restaurant["price"] = None
                
            validated_restaurants.append(validated_restaurant)
        
        # Ensure we have exactly 10 restaurants
        while len(validated_restaurants) < 10:
            validated_restaurants.append({
                "rank": len(validated_restaurants) + 1,
                "name": None,
                "description": None,
                "url": None,
                "image_url": None,
                "price": None,
                "phone": None,
                "notes": None
            })
        
        logger.info(f"Successfully found {len(validated_restaurants)} restaurants using {llm.model_name}")
        return validated_restaurants[:10]  # Ensure exactly 10
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing error: {e}")
        logger.error(f"Raw response: {response.content}")
        
        # Fallback: try to extract restaurant names from the response
        lines = response.content.strip().split('\n')
        fallback_restaurants = []
        
        for i, line in enumerate(lines[:10]):
            if line.strip():
                fallback_restaurants.append({
                    "rank": i + 1,
                    "name": line.strip(),
                    "description": None,
                    "url": None,
                    "image_url": None,
                    "price": None,
                    "phone": None,
                    "notes": None
                })
        
        # Fill remaining slots if needed
        while len(fallback_restaurants) < 10:
            fallback_restaurants.append({
                "rank": len(fallback_restaurants) + 1,
                "name": None,
                "description": None,
                "url": None,
                "image_url": None,
                "price": None,
                "phone": None,
                "notes": None
            })
            
        return fallback_restaurants[:10]
        
    except Exception as e:
        logger.error(f"Unexpected error in restaurant search: {e}")
        
        # Ultimate fallback
        return [
            {
                "rank": i + 1,
                "name": None,
                "description": None,
                "url": None,
                "image_url": None,
                "price": None,
                "phone": None,
                "notes": None
            }
            for i in range(10)
        ] 