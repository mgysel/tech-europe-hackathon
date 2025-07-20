"""Phone call executor service for fetching selected options from Firestore."""

import asyncio
from typing import List, Dict, Any
from services.firestore_service import firestore_service
from services.phone_agent import make_synthflow_call, get_synthflow_call
from services.generic_llm_executor import generic_llm_executor
from firebase_admin import firestore


class PhoneCallExecutor:
    """Service for executing phone call related operations."""

    def __init__(self):
        pass

    def fetch_selected_options(self, task_id: str) -> tuple[List[Dict[str, str]], str]:
        """
        Fetch and return selected options and conversation text from a Firestore task.

        Args:
            task_id: The Firestore task ID to fetch messages from

        Returns:
            Tuple of (selected_options, conversation_text)
            - selected_options: List of dictionaries containing name and phone of selected options
            - conversation_text: String containing the full conversation history
        """
        try:
            # Get all messages for the task
            messages = firestore_service.get_task_messages(task_id)

            if not messages:
                print(f"[PHONE CALL EXECUTOR] No messages found for task_id: {task_id}")
                return [], ""

            # Build conversation text from all messages
            conversation_parts = []
            for msg in reversed(messages):  # Reverse to get chronological order
                if "text" in msg:
                    if isinstance(msg["text"], list):
                        # Handle restaurant list
                        restaurant_text = "Restaurant options:\n"
                        for i, restaurant in enumerate(msg["text"], 1):
                            restaurant_text += f"{i}. {restaurant.get('name', 'Unknown')} - {restaurant.get('phone', 'No phone')}\n"
                        conversation_parts.append(f"AI: {restaurant_text}")
                    else:
                        conversation_parts.append(f"AI: {msg['text']}")
                elif "message" in msg:
                    conversation_parts.append(f"User: {msg['message']}")
                elif "ai" in msg:
                    conversation_parts.append(f"AI: {msg['ai']}")
                elif "user" in msg:
                    conversation_parts.append(f"User: {msg['user']}")

            conversation_text = "\n".join(conversation_parts)

            # Get the last message (first in the list since they're ordered by timestamp descending)
            last_message = messages[0]

            print(f"[PHONE CALL EXECUTOR] Task ID: {task_id}")
            print(f"[PHONE CALL EXECUTOR] Last message: {last_message}")

            # Extract options from the message if they exist
            options = []
            message_text = ""

            # Check different possible fields for the message content
            if "text" in last_message:
                message_text = last_message["text"]
            elif "message" in last_message:
                message_text = last_message["message"]
            elif "ai" in last_message:
                message_text = last_message["ai"]
            elif "user" in last_message:
                message_text = last_message["user"]

            print(f"[PHONE CALL EXECUTOR] Message text type: {type(message_text)}")

            # Handle different message formats
            if isinstance(message_text, list):
                # If it's a list of restaurants, extract only selected ones
                for i, restaurant in enumerate(message_text, 1):
                    if isinstance(restaurant, dict) and "name" in restaurant:
                        # Only include if selected is True
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
                                option_data["recording_url"] = restaurant[
                                    "recording_url"
                                ]
                            if "transcript" in restaurant:
                                option_data["transcript"] = restaurant["transcript"]

                            options.append(option_data)
            elif isinstance(message_text, str):
                # If it's a string, look for numbered options or choices
                lines = message_text.split("\n")
                for line in lines:
                    line = line.strip()
                    # Look for patterns like "1.", "2.", "A.", "B.", etc.
                    if (
                        line
                        and (line[0].isdigit() and line[1] in [".", ")", " "])
                        or (line[0].isalpha() and line[1] in [".", ")", " "])
                    ):
                        options.append(line)

            print(f"[PHONE CALL EXECUTOR] Found selected options: {options}")
            print(f"[PHONE CALL EXECUTOR] Conversation text: {conversation_text}")
            return options, conversation_text

        except Exception as e:
            print(f"[PHONE CALL EXECUTOR] Error fetching selected options: {e}")
            raise

    def execute_phone_calls_for_selected_options(
        self, task_id: str
    ) -> List[Dict[str, Any]]:
        """
        Execute phone calls for all selected options from a Firestore task.

        Args:
            task_id: The Firestore task ID to fetch messages from

        Returns:
            List of dictionaries containing call results for each selected option
        """
        try:
            # First get the selected options and conversation text
            selected_options, conversation_text = self.fetch_selected_options(task_id)

            if not selected_options:
                print(
                    f"[PHONE CALL EXECUTOR] No selected options found for task_id: {task_id}"
                )
                return []

            print(
                f"[PHONE CALL EXECUTOR] Executing phone calls for {len(selected_options)} selected options"
            )

            # Set status to "loading" for all selected options
            self._update_selected_options_status(task_id, selected_options, "loading")

            call_results = []

            # Summarize conversation to sourcing requirement using LLM
            print(f"[PHONE CALL EXECUTOR] Summarizing conversation using LLM...")
            sourcing_requirement = (
                generic_llm_executor.summarize_conversation_to_sourcing_requirement(
                    conversation_text
                )
            )

            for i, option in enumerate(selected_options, 1):
                try:
                    print(
                        f"[PHONE CALL EXECUTOR] Making call {i}/{len(selected_options)} to {option['name']}"
                    )

                    # Create custom variables with the summarized sourcing requirement
                    custom_variables = [
                        {"key": "sourcing_request", "value": sourcing_requirement}
                    ]

                    # Make the Synthflow call
                    result = make_synthflow_call(
                        model_id="90a9b8ba-b0bb-4948-a3fc-8000f5e18846",
                        phone=option["phone"],
                        name=option["name"],
                        custom_variables=custom_variables,
                    )

                    call_results.append(
                        {
                            "restaurant_name": option["name"],
                            "phone": option["phone"],
                            "call_result": result,
                            "status": "success",
                        }
                    )

                    print(f"[PHONE CALL EXECUTOR] Call {i} successful: {result}")

                except Exception as e:
                    print(
                        f"[PHONE CALL EXECUTOR] Call {i} failed for {option['name']}: {e}"
                    )
                    call_results.append(
                        {
                            "restaurant_name": option["name"],
                            "phone": option["phone"],
                            "call_result": None,
                            "status": "failed",
                            "error": str(e),
                        }
                    )

            print(f"[PHONE CALL EXECUTOR] Completed {len(call_results)} calls")

            # Update the last message in Firestore with call results
            try:
                print(
                    f"[PHONE CALL EXECUTOR] Updating Firestore message with call results..."
                )
                self._update_firestore_message_with_call_results(task_id, call_results)
                print(f"[PHONE CALL EXECUTOR] Successfully updated Firestore message")
            except Exception as e:
                print(f"[PHONE CALL EXECUTOR] Error updating Firestore message: {e}")

            # Start async polling for call results
            call_ids = []
            for result in call_results:
                if result.get("status") == "success":
                    call_id = (
                        result.get("call_result", {}).get("response", {}).get("call_id")
                    )
                    if call_id:
                        call_ids.append(call_id)

            if call_ids:
                print(
                    f"[PHONE CALL EXECUTOR] Starting async polling for call_ids: {call_ids}"
                )
                # Start the async polling in the background
                asyncio.create_task(self._poll_call_results_async(call_ids, task_id))

            return call_results

        except Exception as e:
            print(f"[PHONE CALL EXECUTOR] Error executing phone calls: {e}")
            raise

    def _update_firestore_message_with_call_results(
        self, task_id: str, call_results: List[Dict[str, Any]]
    ) -> None:
        """
        Update the last message in Firestore with call results.

        Args:
            task_id: The Firestore task ID
            call_results: List of call results to add to the message
        """
        try:
            # Get the last message (which contains the restaurant options)
            messages = firestore_service.get_task_messages(task_id)
            if not messages:
                print(
                    f"[PHONE CALL EXECUTOR] No messages found to update for task_id: {task_id}"
                )
                return

            last_message = messages[0]  # Most recent message

            # Create a mapping of restaurant names to call IDs
            call_results_map = {}
            for result in call_results:
                restaurant_name = result.get("restaurant_name")
                if restaurant_name:
                    call_result = result.get("call_result", {})
                    print(
                        f"[PHONE CALL EXECUTOR] Processing result for {restaurant_name}"
                    )
                    print(f"[PHONE CALL EXECUTOR] Full call_result: {call_result}")

                    # Extract call_id from the correct path
                    response = call_result.get("response", {})
                    call_id = response.get("call_id")

                    if call_id:
                        call_results_map[restaurant_name] = call_id
                        print(
                            f"[PHONE CALL EXECUTOR] Found call_id for {restaurant_name}: {call_id}"
                        )
                    else:
                        print(
                            f"[PHONE CALL EXECUTOR] No call_id found for {restaurant_name}"
                        )
                        print(f"[PHONE CALL EXECUTOR] Response structure: {response}")

            # Update the restaurant options with call information
            if "text" in last_message and isinstance(last_message["text"], list):
                updated_restaurants = []
                for restaurant in last_message["text"]:
                    if isinstance(restaurant, dict) and "name" in restaurant:
                        restaurant_name = restaurant["name"]
                        if restaurant_name in call_results_map:
                            # Add call_id and set status to "loading" for the restaurant
                            restaurant["call_id"] = call_results_map[restaurant_name]
                            restaurant["status"] = "loading"
                            print(
                                f"[PHONE CALL EXECUTOR] Set {restaurant_name} status to loading with call_id: {call_results_map[restaurant_name]}"
                            )
                        updated_restaurants.append(restaurant)

                # Update the existing message in Firestore instead of creating a new one
                print(
                    f"[PHONE CALL EXECUTOR] Updating existing message in Firestore..."
                )
                print(
                    f"[PHONE CALL EXECUTOR] Updated restaurants: {updated_restaurants}"
                )

                # Get the message ID and update the existing document
                message_id = last_message.get("id")
                if message_id:
                    # Update the existing message
                    doc_ref = firestore_service._db.collection(
                        f"tasks/{task_id}/messages"
                    ).document(message_id)
                    doc_ref.update(
                        {
                            "text": updated_restaurants,
                            "updated_at": firestore.SERVER_TIMESTAMP,
                        }
                    )
                    print(
                        f"[PHONE CALL EXECUTOR] Updated existing message {message_id}"
                    )
                else:
                    # Fallback: create a new message if we can't find the ID
                    firestore_service.write_task_message(
                        task_id=task_id,
                        sender="system",
                        text=updated_restaurants,
                        message_type="restaurant_options_with_calls",
                    )
                    print(f"[PHONE CALL EXECUTOR] Created new message (no ID found)")

                print(
                    f"[PHONE CALL EXECUTOR] Updated {len(updated_restaurants)} restaurants with call information"
                )

        except Exception as e:
            print(f"[PHONE CALL EXECUTOR] Error updating Firestore message: {e}")
            raise

    async def _poll_call_results_async(self, call_ids: List[str], task_id: str) -> None:
        """
        Asynchronously poll call results for given call_ids.
        Stops polling for each call when recording_url is found and saves to Firestore.

        Args:
            call_ids: List of call IDs to poll
            task_id: The task ID for updating Firestore
        """
        print(f"[PHONE CALL EXECUTOR] Starting async polling for {len(call_ids)} calls")

        # Track which calls are completed (have recording_url)
        completed_calls = set()

        # Poll each call_id sequentially every 5 seconds for 100 seconds total
        max_iterations = 20  # 100 seconds / 5 seconds = 20 iterations
        poll_interval = 5  # seconds

        for iteration in range(max_iterations):
            print(
                f"[PHONE CALL EXECUTOR] Polling iteration {iteration + 1}/{max_iterations}"
            )

            for call_id in call_ids:
                # Skip if this call is already completed
                if call_id in completed_calls:
                    continue

                try:
                    print(f"[PHONE CALL EXECUTOR] Polling call_id: {call_id}")
                    result = get_synthflow_call(call_id)
                    print(f"[PHONE CALL EXECUTOR] Call {call_id} result: {result}")

                    # Check if we have recording_url and transcript
                    response = result.get("response", {})
                    calls = response.get("calls", [])

                    if calls and len(calls) > 0:
                        call_data = calls[0]  # Get the first call
                        recording_url = call_data.get("recording_url")
                        transcript = call_data.get("transcript")

                        if recording_url and transcript:
                            print(
                                f"[PHONE CALL EXECUTOR] Found recording_url and transcript for {call_id}"
                            )
                            print(
                                f"[PHONE CALL EXECUTOR] Recording URL: {recording_url}"
                            )
                            print(f"[PHONE CALL EXECUTOR] Transcript: {transcript}")

                            # Save to Firestore
                            try:
                                self._update_firestore_with_call_results(
                                    task_id, call_id, recording_url, transcript
                                )
                                print(
                                    f"[PHONE CALL EXECUTOR] Successfully saved call results to Firestore for {call_id}"
                                )
                                completed_calls.add(call_id)
                            except Exception as e:
                                print(
                                    f"[PHONE CALL EXECUTOR] Error saving to Firestore for {call_id}: {e}"
                                )

                except Exception as e:
                    print(f"[PHONE CALL EXECUTOR] Error polling call {call_id}: {e}")

            # Check if all calls are completed
            if len(completed_calls) == len(call_ids):
                print(
                    f"[PHONE CALL EXECUTOR] All calls completed! Stopping polling early."
                )
                break

            # Wait 5 seconds before next iteration
            if iteration < max_iterations - 1:  # Don't wait after the last iteration
                print(
                    f"[PHONE CALL EXECUTOR] Waiting {poll_interval} seconds before next poll..."
                )
                await asyncio.sleep(poll_interval)

        print(f"[PHONE CALL EXECUTOR] Completed async polling for all calls")

    def _update_firestore_with_call_results(
        self, task_id: str, call_id: str, recording_url: str, transcript: str
    ) -> None:
        """
        Update the restaurant option in Firestore with recording_url and transcript.

        Args:
            task_id: The Firestore task ID
            call_id: The call ID to match with restaurant
            recording_url: The recording URL from Synthflow
            transcript: The transcript from Synthflow
        """
        try:
            # Get the last message (which contains the restaurant options)
            messages = firestore_service.get_task_messages(task_id)
            if not messages:
                print(
                    f"[PHONE CALL EXECUTOR] No messages found to update for task_id: {task_id}"
                )
                return

            last_message = messages[0]  # Most recent message

            # Update the restaurant options with recording_url and transcript
            if "text" in last_message and isinstance(last_message["text"], list):
                updated_restaurants = []
                for restaurant in last_message["text"]:
                    if isinstance(restaurant, dict) and "name" in restaurant:
                        # Check if this restaurant has the matching call_id
                        if restaurant.get("call_id") == call_id:
                            # Add recording_url and transcript to this restaurant
                            restaurant["recording_url"] = recording_url
                            restaurant["transcript"] = transcript
                            # Set status to "completed" when call results are received
                            restaurant["status"] = "completed"
                            print(
                                f"[PHONE CALL EXECUTOR] Updated {restaurant['name']} with recording_url, transcript, and completed status"
                            )
                        updated_restaurants.append(restaurant)

                # Update the existing message in Firestore
                print(
                    f"[PHONE CALL EXECUTOR] Updating existing message in Firestore with call results..."
                )

                # Get the message ID and update the existing document
                message_id = last_message.get("id")
                if message_id:
                    # Update the existing message
                    doc_ref = firestore_service._db.collection(
                        f"tasks/{task_id}/messages"
                    ).document(message_id)
                    doc_ref.update(
                        {
                            "text": updated_restaurants,
                            "updated_at": firestore.SERVER_TIMESTAMP,
                        }
                    )
                    print(
                        f"[PHONE CALL EXECUTOR] Updated existing message {message_id} with call results"
                    )
                else:
                    print(
                        f"[PHONE CALL EXECUTOR] No message ID found, cannot update existing message"
                    )

        except Exception as e:
            print(
                f"[PHONE CALL EXECUTOR] Error updating Firestore with call results: {e}"
            )
            raise

    def _update_selected_options_status(
        self, task_id: str, options: List[Dict[str, Any]], status: str
    ) -> None:
        """
        Update the status of selected options in Firestore.

        Args:
            task_id: The Firestore task ID
            options: List of selected options to update
            status: The new status to set ("loading" or "completed")
        """
        try:
            # Get the last message (which contains the restaurant options)
            messages = firestore_service.get_task_messages(task_id)
            if not messages:
                print(
                    f"[PHONE CALL EXECUTOR] No messages found to update status for task_id: {task_id}"
                )
                return

            last_message = messages[0]  # Most recent message

            # Update the restaurant options with the new status
            if "text" in last_message and isinstance(last_message["text"], list):
                updated_restaurants = []
                for restaurant in last_message["text"]:
                    if isinstance(restaurant, dict) and "name" in restaurant:
                        # Find the option by name and update its status
                        for option in options:
                            if restaurant["name"] == option["name"]:
                                restaurant["status"] = status
                                print(
                                    f"[PHONE CALL EXECUTOR] Updated status for {restaurant['name']} to {status}"
                                )
                                break
                        updated_restaurants.append(restaurant)

                # Update the existing message in Firestore
                print(
                    f"[PHONE CALL EXECUTOR] Updating existing message in Firestore with status..."
                )

                # Get the message ID and update the existing document
                message_id = last_message.get("id")
                if message_id:
                    # Update the existing message
                    doc_ref = firestore_service._db.collection(
                        f"tasks/{task_id}/messages"
                    ).document(message_id)
                    doc_ref.update(
                        {
                            "text": updated_restaurants,
                            "updated_at": firestore.SERVER_TIMESTAMP,
                        }
                    )
                    print(
                        f"[PHONE CALL EXECUTOR] Updated existing message {message_id} with status"
                    )
                else:
                    print(
                        f"[PHONE CALL EXECUTOR] No message ID found, cannot update existing message"
                    )

        except Exception as e:
            print(f"[PHONE CALL EXECUTOR] Error updating Firestore with status: {e}")
            raise


# Create a singleton instance
phone_call_executor = PhoneCallExecutor()
