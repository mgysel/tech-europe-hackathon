import os
import requests
from dotenv import load_dotenv

load_dotenv()

SYNTHFLOW_API_URL = "https://api.synthflow.ai/v2/calls"
SYNTHFLOW_API_KEY = os.getenv("SYNTHFLOW_API_KEY")


def make_synthflow_call(
    model_id: str,
    phone: str,
    name: str,
    custom_variables: list = None,
):
    headers = {
        "Authorization": f"Bearer {SYNTHFLOW_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model_id": model_id,
        "phone": phone,
        "name": name,
    }

    if custom_variables:
        payload["custom_variables"] = custom_variables

    print(f"Sending payload to Synthflow: {payload}")
    response = requests.post(SYNTHFLOW_API_URL, headers=headers, json=payload)

    response.raise_for_status()
    return response.json()


def get_synthflow_call(call_id: str) -> dict:
    """Get call information by call_id."""
    headers = {
        "Authorization": f"Bearer {SYNTHFLOW_API_KEY}",
        "Content-Type": "application/json",
    }

    url = f"{SYNTHFLOW_API_URL}/{call_id}"
    response = requests.get(url, headers=headers)

    response.raise_for_status()
    return response.json()
