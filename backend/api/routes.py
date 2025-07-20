"""FastAPI routes for the AI Ordering Assistant."""

from fastapi import APIRouter, HTTPException

from schemas.schemas import OrderRequest, OrderResponse, SynthflowCallRequest
from services.agent import agent_service
from services.phone_agent import make_synthflow_call, get_synthflow_call

# Create router for order-related endpoints
router = APIRouter()

@router.post("/synthflow-call")
async def make_call(req: SynthflowCallRequest) -> dict:
    """Make a call using Synthflow AI."""
    try:
        custom_variables = [{"key": "sourcing_request", "value": req.sourcing_request}]
        result = make_synthflow_call(
            model_id="90a9b8ba-b0bb-4948-a3fc-8000f5e18846",
            phone=req.phone,
            name=req.name,
            custom_variables=custom_variables,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/synthflow-call/{call_id}")
async def get_call(call_id: str) -> dict:
    """Get call information by call_id."""
    try:
        result = get_synthflow_call(call_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/order", response_model=OrderResponse, tags=["orders"])
async def place_order(req: OrderRequest) -> OrderResponse:
    """
    Process any order request through the AI agent using Firestore task data.
    
    This endpoint allows you to:
    - Provide a task_id to retrieve conversation history from Firestore
    - Get AI-powered business/service recommendations based on the task messages
    
    The AI agent will:
    1. Fetch all messages for the given task_id from Firestore
    2. Process the conversation history to understand the order requirements
    3. Ask follow-up questions if needed
    4. Research the best 10 businesses/services for your use case
    5. Return business/service names and phone numbers in structured format
    
    Firestore Structure:
    - tasks/{task_id}/messages/{message_id}
    - Messages should have 'user', 'ai', or 'message' fields
    """
    return await agent_service.process_order(req)


@router.get("/healthz", tags=["health"])
def health() -> dict[str, str]:
    """
    Basic liveness probe compatible with Kubernetes etc.
    
    Returns a simple status check to verify the service is running.
    """
    return {"status": "ok"} 