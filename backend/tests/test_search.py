#!/usr/bin/env python3
"""Test script for search functionality."""

import os
import sys
from dotenv import load_dotenv

# Add the backend directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tools.search_tools import search_options_tool

def main():
    """Test the search tool."""
    load_dotenv()
    
    # Check if API key is available
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY not found in environment variables")
        print("Please set your OpenAI API key in the .env file")
        return
    
    print("🔍 Testing search tool...")
    print("=" * 50)
    
    # Test queries for different types of ordering tasks
    test_queries = [
        "Italian restaurants for 20 people in New York, budget $25 per person, delivery needed tomorrow at 7pm",
        "Event planning services for a corporate party of 100 people in Chicago, budget $5000",
        "Office supply stores that can deliver 50 laptops to San Francisco within 3 days",
        "Catering services for a wedding of 150 people in Los Angeles, vegetarian options needed"
    ]
    
    for i, test_query in enumerate(test_queries, 1):
        try:
            print(f"\n--- Test {i} ---")
            print(f"Query: {test_query}")
            print("\n🤖 Searching for options...")
            
            results = search_options_tool(test_query)
            
            print(f"\n✅ Found {len(results)} options:")
            print("=" * 30)
            
            for option in results[:3]:  # Show first 3 results
                print(f"\n{option['rank']}. {option['name']}")
                print(f"   Description: {option['description']}")
                print(f"   Phone: {option['phone']}")
                print(f"   Notes: {option['notes']}")
                
        except Exception as e:
            print(f"\n❌ Error during search: {e}")
            print(f"Error type: {type(e).__name__}")
            import traceback
            traceback.print_exc()
            continue
            
    print("\n" + "=" * 50)
    print("✅ Search tool test completed!")

if __name__ == "__main__":
    main() 