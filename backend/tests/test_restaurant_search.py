#!/usr/bin/env python3
"""Test script for restaurant search functionality."""

import os
import sys
from dotenv import load_dotenv

# Add the backend directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tools.restaurant_tools import search_restaurants_tool

def main():
    """Test the restaurant search tool."""
    load_dotenv()
    
    # Check if API key is available
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY not found in environment variables")
        print("Please set your OpenAI API key in the .env file")
        return
    
    print("🔍 Testing restaurant search tool...")
    print("=" * 50)
    
    # Test query
    test_query = "Italian restaurants for 20 people in New York, budget $25 per person, delivery needed tomorrow at 7pm"
    
    try:
        print(f"Query: {test_query}")
        print("\n🤖 Searching for restaurants...")
        
        results = search_restaurants_tool(test_query)
        
        print(f"\n✅ Found {len(results)} restaurants:")
        print("=" * 50)
        
        for restaurant in results:
            print(f"\n{restaurant['rank']}. {restaurant['name']}")
            print(f"   Description: {restaurant['description']}")
            print(f"   Phone: {restaurant['phone']}")
            print(f"   Notes: {restaurant['notes']}")
            
        print("\n" + "=" * 50)
        print("✅ Restaurant search test completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error during restaurant search: {e}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 