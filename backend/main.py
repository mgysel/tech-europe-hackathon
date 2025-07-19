from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from langchain.agents import initialize_agent, AgentType
from langchain_openai import ChatOpenAI
from langchain.tools import Tool
from firebase_admin import credentials, firestore, initialize_app
import os
from dotenv import load_dotenv
from typing import Dict, Any
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="AI Hackathon Backend", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Firebase
try:
    # Check if Firebase is already initialized
    if not firestore.client():
        # Initialize Firebase Admin SDK
        # For development, you can use a service account key file
        # cred = credentials.Certificate("path/to/serviceAccountKey.json")
        # For now, we'll use the default credentials (GOOGLE_APPLICATION_CREDENTIALS env var)
        initialize_app()
    db = firestore.client()
    logger.info("Firebase initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Firebase: {e}")
    db = None

# Initialize LangChain
def create_langchain_agent():
    """Create and return a LangChain agent"""
    try:
        # Initialize the language model
        llm = ChatOpenAI(
            temperature=0,
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            model="gpt-3.5-turbo"
        )
        
        # Define tools for the agent
        tools = [
            Tool(
                name="get_order_details",
                func=get_order_details,
                description="Get order details from Firebase database"
            ),
            Tool(
                name="update_order_status",
                func=update_order_status,
                description="Update order status in Firebase database"
            ),
            Tool(
                name="process_order",
                func=process_order,
                description="Process an order and return processing details"
            )
        ]
        
        # Initialize the agent
        agent = initialize_agent(
            tools=tools,
            llm=llm,
            agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
            verbose=True,
            handle_parsing_errors=True
        )
        
        return agent
    except Exception as e:
        logger.error(f"Failed to create LangChain agent: {e}")
        return None

# Tool functions for the agent
def get_order_details(order_id: str) -> str:
    """Get order details from Firebase"""
    try:
        if not db:
            return "Firebase not initialized"
        
        doc_ref = db.collection('orders').document(order_id)
        doc = doc_ref.get()
        
        if doc.exists:
            order_data = doc.to_dict()
            return f"Order {order_id} details: {order_data}"
        else:
            return f"Order {order_id} not found"
    except Exception as e:
        logger.error(f"Error getting order details: {e}")
        return f"Error retrieving order details: {str(e)}"

def update_order_status(order_id: str, status: str) -> str:
    """Update order status in Firebase"""
    try:
        if not db:
            return "Firebase not initialized"
        
        doc_ref = db.collection('orders').document(order_id)
        doc_ref.update({
            'status': status,
            'updated_at': firestore.SERVER_TIMESTAMP
        })
        return f"Order {order_id} status updated to {status}"
    except Exception as e:
        logger.error(f"Error updating order status: {e}")
        return f"Error updating order status: {str(e)}"

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "AI Hackathon Backend API", "status": "running"}

@app.get("/order/{order_id}")
async def process_order_endpoint(order_id: str):
    """
    Process an order using LangChain agent
    
    Args:
        order_id (str): The ID of the order to process
        
    Returns:
        dict: Processing result and status
    """
    try:
        logger.info(f"Processing order: {order_id}")
        
        # Create LangChain agent
        agent = create_langchain_agent()
        
        if not agent:
            raise HTTPException(status_code=500, detail="Failed to create LangChain agent")
        
        # Prepare the prompt for the agent
        prompt = f"""
        Process order {order_id}. Here's what you need to do:
        1. Get the order details using the get_order_details tool
        2. Process the order using the process_order tool
        3. Update the order status to 'processed' using the update_order_status tool
        4. Provide a summary of what was done
        
        Please execute these steps and provide a comprehensive response.
        """
        
        # Run the agent
        result = agent.run(prompt)
        
        return {
            "order_id": order_id,
            "status": "success",
            "result": result,
            "message": f"Order {order_id} processed successfully"
        }
        
    except Exception as e:
        logger.error(f"Error processing order {order_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing order: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "firebase": "connected" if db else "disconnected",
        "langchain": "available" if os.getenv("OPENAI_API_KEY") else "missing_api_key"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 