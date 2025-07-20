"""Search tools for the AI Ordering Assistant."""

import json
import logging
from typing import List, Dict, Any

from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage
from langchain.tools import tool

from config import SEARCH_MODEL, OPENAI_API_KEY

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Search TOOL (OpenAI function‑call)
# ---------------------------------------------------------------------------
@tool(
    "search_options",
    args_schema=None,
    return_direct=True,
)
def search_options_tool(query: str) -> List[Dict[str, Any]]:
    """Search for businesses/services and return the 5 best options for the query.

    Args:
        query: A natural‑language query describing what you need, including type of business/service, 
               requirements, budget, location, quantity, etc.

    Returns:
        A list with exactly five dicts in this shape::
            {
                "rank": int,  # 1-based ranking (1..5)
                "name": str,
                "description": str,  # Brief description of the business/service and why it fits
                "url": str,  # Business website or relevant URL
                "image_url": str,  # URL to business/service image
                "estimated_price": int,  # Price estimate in dollars (e.g., 15, 25, 45, 80)
                "phone": str,  # Business phone number
                "notes": str  # Additional notes about ordering, capacity, availability, etc.
            }

    The function uses OpenAI to find and structure real business/service information.
    """
    
    # Use the dedicated search model (o3 by default, but fallback to other models if needed)
    try:
        # For o3 model, explicitly set temperature to 1 (the only supported value)
        if SEARCH_MODEL == "o3":
            llm = ChatOpenAI(
                model_name=SEARCH_MODEL, 
                temperature=1,  # o3 only supports temperature=1
                api_key=OPENAI_API_KEY
            )
        # For other models that don't support custom temperature, don't set it
        elif SEARCH_MODEL in ["gpt-4o-mini", "gpt-3.5-turbo", "o1-mini", "o1-preview", "o4-mini"]:
            llm = ChatOpenAI(
                model_name=SEARCH_MODEL, 
                api_key=OPENAI_API_KEY
            )
        else:
            llm = ChatOpenAI(
                model_name=SEARCH_MODEL, 
                temperature=0.1,
                api_key=OPENAI_API_KEY
            )
    except Exception as e:
        logger.warning(f"Failed to create LLM with {SEARCH_MODEL}, falling back to gpt-4o: {e}")
        llm = ChatOpenAI(
            model_name="gpt-4o", 
            api_key=OPENAI_API_KEY
        )
    
    logger.info(f"Searching for options with query: {query} using model: {llm.model_name}")

    system_prompt = """You are an expert concierge with extensive knowledge of businesses and services worldwide. 
    
    Your task is to recommend exactly 5 real businesses/services that best match the user's requirements. 
    This could include restaurants, catering services, event planners, retail stores, service providers, 
    or any other type of business that can fulfill ordering or procurement needs.
    
    For each business/service, provide:
    - Real business names (not generic or made-up names)
    - Brief descriptions explaining why each business fits the request
    - Business website URLs or relevant links
    - REAL image URLs for business photos (verify these are actual working URLs, not placeholder or example URLs)
    - Estimated price in dollars (e.g., 15, 25, 45, 80)
    - Business phone numbers in proper format
    - Additional notes about ordering, capacity, delivery, availability, etc.
    
    IMPORTANT: For image_url field, only provide actual working URLs to real business images. Do not use:
    - Example URLs (like "https://example.com/...")
    - Placeholder URLs
    - Generic stock photo URLs
    - Made-up URLs
    If you cannot find a real image URL for a business, use null instead.
    
    Focus on businesses/services that can actually handle the specified requirements.
    
    Return ONLY a valid JSON array with exactly 5 businesses/services, each having these fields:
    - rank: integer from 1 to 5
    - name: string (real business name)
    - description: string (brief description of business and why it fits)
    - url: string (business website or relevant URL)
    - image_url: string or null (REAL URL to business image, or null if unavailable)
    - estimated_price: integer (price estimate in dollars)
    - phone: string (business phone number)
    - notes: string (additional notes about ordering, capacity, availability, etc.)
    
    Example format:
    [
        {
            "rank": 1,
            "name": "Mario's Italian Bistro",
            "description": "Family-owned Italian restaurant specializing in authentic wood-fired pizzas and pasta. Perfect for large groups with their spacious dining area and catering services.",
            "url": "https://mariositalianbistro.com",
            "image_url": null,
            "estimated_price": 25,
            "phone": "+1 (555) 123-4567",
            "notes": "Offers group discounts for 20+ people. Requires 24-hour advance notice for large orders. Free delivery within 5 miles."
        }
    ]"""

    human_prompt = f"""Find 5 real businesses/services that best match this request: {query}

    Consider factors like:
    - Type of business/service requested
    - Quantity/group size requirements
    - Location/delivery area
    - Budget constraints
    - Special requirements or restrictions
    - Timing requirements

    Provide practical, actionable recommendations with real contact information.
    
    Remember: Only use REAL image URLs that actually work, or use null if you cannot verify a real image URL."""

    try:
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_prompt)
        ]
        
        response = llm.invoke(messages)
        logger.info(f"Raw LLM response: {response.content[:200]}...")
        
        # Parse the JSON response
        options = json.loads(response.content)
        
        # Validate the response structure
        if not isinstance(options, list):
            raise ValueError("Response is not a list")
        
        if len(options) != 5:
            logger.warning(f"Expected 5 options, got {len(options)}")
        
        # Ensure each option has required fields
        required_fields = ["rank", "name", "description", "url", "image_url", "estimated_price", "phone", "notes"]
        validated_options = []
        
        for i, option in enumerate(options[:5]):  # Take only first 5
            if not isinstance(option, dict):
                logger.error(f"Option {i} is not a dict: {option}")
                continue
                
            # Ensure all required fields are present
            validated_option = {}
            for field in required_fields:
                if field in option:
                    validated_option[field] = option[field]
                else:
                    logger.warning(f"Missing field '{field}' in option {i}")
                    validated_option[field] = None
            
            # Ensure rank is an integer
            try:
                validated_option["rank"] = int(validated_option["rank"])
            except (ValueError, TypeError):
                validated_option["rank"] = i + 1
            
            # Ensure estimated_price is an integer
            try:
                validated_option["estimated_price"] = float(validated_option["estimated_price"])
            except (ValueError, TypeError):
                validated_option["estimated_price"] = None
                
            validated_options.append(validated_option)
        
        # Ensure we have exactly 5 options
        while len(validated_options) < 5:
            validated_options.append({
                "rank": len(validated_options) + 1,
                "name": None,
                "description": None,
                "url": None,
                "image_url": None,
                "estimated_price": None,
                "phone": None,
                "notes": None
            })
        
        logger.info(f"Successfully found {len(validated_options)} options using {llm.model_name}")
        # Return as JSON string since the agent expects string output
        return json.dumps(validated_options[:5], indent=2)
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing error: {e}")
        logger.error(f"Raw response: {response.content}")
        
        # Fallback: try to extract business names from the response
        lines = response.content.strip().split('\n')
        fallback_options = []
        
        for i, line in enumerate(lines[:5]):
            if line.strip():
                fallback_options.append({
                    "rank": i + 1,
                    "name": line.strip(),
                    "description": None,
                    "url": None,
                    "image_url": None,
                    "estimated_price": None,
                    "phone": None,
                    "notes": None
                })
        
        # Fill remaining slots if needed
        while len(fallback_options) < 5:
            fallback_options.append({
                "rank": len(fallback_options) + 1,
                "name": None,
                "description": None,
                "url": None,
                "image_url": None,
                "estimated_price": None,
                "phone": None,
                "notes": None
            })
            
        return json.dumps(fallback_options[:5], indent=2)
        
    except Exception as e:
        logger.error(f"Unexpected error in search: {e}")
        
        # Ultimate fallback
        fallback_result = [
            {
                "rank": i + 1,
                "name": None,
                "description": None,
                "url": None,
                "image_url": None,
                "estimated_price": None,
                "phone": None,
                "notes": None
            }
            for i in range(5)
        ]
        return json.dumps(fallback_result, indent=2) 