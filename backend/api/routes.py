"""FastAPI routes for the AI Ordering Assistant."""

from fastapi import APIRouter, HTTPException

from schemas.schemas import (
    OrderRequest,
    OrderResponse,
    SynthflowCallRequest,
    TaskRequest,
)
from services.agent import agent_service
from services.phone_agent import make_synthflow_call, get_synthflow_call
from services.phone_call_executor import phone_call_executor
from services.firestore_service import firestore_service

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


@router.get("/firestore-test", tags=["health"])
async def test_firestore() -> dict:
    """
    Test Firestore connection and basic operations.
    """
    try:
        print("[FIRESTORE TEST] Testing Firestore connection...")

        # Test basic connection by trying to list collections
        collections = firestore_service._db.collections()
        collection_list = [col.id for col in collections]

        print(f"[FIRESTORE TEST] Available collections: {collection_list}")

        return {
            "status": "ok",
            "message": "Firestore connection successful",
            "collections": collection_list,
        }
    except Exception as e:
        print(f"[FIRESTORE TEST] Error: {e}")
        return {"status": "error", "message": str(e)}


@router.post("/task-last-message", tags=["tasks"])
async def get_last_message(req: TaskRequest) -> dict:
    """
    Get selected options from the last message in a Firestore task.

    This endpoint uses the phone_call_executor service to:
    1. Fetch all messages for the given task_id from Firestore
    2. Get the most recent message
    3. Extract and return only the selected options

    Args:
        req: TaskRequest containing the task_id

    Returns:
        Dictionary with the selected options
    """
    try:
        options, conversation_text = phone_call_executor.fetch_selected_options(
            req.task_id
        )
        return {"options": options, "conversation_text": conversation_text}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/execute-phone-calls", tags=["tasks"])
async def execute_phone_calls(req: TaskRequest) -> dict:
    """
    Execute phone calls for all selected options from a Firestore task.

    This endpoint:
    1. Fetches selected options and conversation text from the task
    2. Makes Synthflow calls to each selected restaurant
    3. Returns selected options with their call_ids

    Args:
        req: TaskRequest containing the task_id

    Returns:
        Dictionary with selected options and their call_ids
    """
    try:
        call_results = phone_call_executor.execute_phone_calls_for_selected_options(
            req.task_id
        )

        # Extract selected options with call_ids and status
        selected_options_with_calls = []
        for result in call_results:
            if result.get("status") == "success":
                call_id = (
                    result.get("call_result", {}).get("response", {}).get("call_id")
                )
                selected_options_with_calls.append(
                    {
                        "name": result.get("restaurant_name"),
                        "phone": result.get("phone"),
                        "call_id": call_id,
                        "status": "loading",  # Initial status when call is initiated
                    }
                )
            else:
                # Include failed calls with error status
                selected_options_with_calls.append(
                    {
                        "name": result.get("restaurant_name"),
                        "phone": result.get("phone"),
                        "call_id": None,
                        "status": "failed",
                        "error": result.get("error", "Unknown error"),
                    }
                )

        return {"selected_options": selected_options_with_calls}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/get-selected-options-status", tags=["tasks"])
async def get_selected_options_status(req: TaskRequest) -> dict:
    """
    Get the current status of selected options from a Firestore task.

    This endpoint returns the current status of all selected options including:
    - loading: Phone call is in progress
    - completed: Phone call completed with results
    - failed: Phone call failed

    Args:
        req: TaskRequest containing the task_id

    Returns:
        Dictionary with selected options and their current status
    """
    try:
        # Get the last message (which contains the restaurant options with status)
        messages = firestore_service.get_task_messages(req.task_id)
        if not messages:
            raise HTTPException(
                status_code=404, detail=f"No messages found for task_id: {req.task_id}"
            )

        last_message = messages[0]  # Most recent message

        # Extract selected options with their current status
        selected_options_with_status = []
        if "text" in last_message and isinstance(last_message["text"], list):
            for restaurant in last_message["text"]:
                if isinstance(restaurant, dict) and "name" in restaurant:
                    # Only include selected options
                    if restaurant.get("selected") == True:
                        option_data = {
                            "name": restaurant["name"],
                            "phone": restaurant.get("phone", "No phone"),
                            "status": restaurant.get("status", "unknown"),
                        }

                        # Include additional data if available
                        if "call_id" in restaurant:
                            option_data["call_id"] = restaurant["call_id"]
                        if "recording_url" in restaurant:
                            option_data["recording_url"] = restaurant["recording_url"]
                        if "transcript" in restaurant:
                            option_data["transcript"] = restaurant["transcript"]

                        selected_options_with_status.append(option_data)

        return {"selected_options": selected_options_with_status}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
