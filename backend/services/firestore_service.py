"""Firestore service for interacting with Google Cloud Firestore via Firebase Admin SDK."""

from __future__ import annotations
import logging

import json
from typing import Any, Dict, List, Optional

import firebase_admin
from firebase_admin import credentials, firestore

from config import FIREBASE_ADMIN_KEY


logging.basicConfig(level=logging.DEBUG)


class FirestoreService:
    """Service wrapper around Firestore client."""

    def __init__(self, key_path: Optional[str] | None = None):
        """Create a FirestoreService instance, initializing Firebase if needed.

        Priority order for credentials:
        1. Environment variable ``ADMIN_KEY_JSON`` containing the **JSON string** of
           the service-account key.
        2. Environment variable ``FIREBASE_ADMIN_KEY_PATH`` pointing to a file.
        3. ``key_path`` argument (passed explicitly by caller).
        4. Default file name ``admin_key.json`` in project root.
        """

        if not firebase_admin._apps:
            # Load from FIREBASE_ADMIN_KEY environment variable (JSON string)
            firebase_admin_key = FIREBASE_ADMIN_KEY
            print(f"Firebase admin key : {firebase_admin_key}")
            if not firebase_admin_key:
                raise ValueError("FIREBASE_ADMIN_KEY environment variable is required")

            try:
                print(
                    "Loading credentials from FIREBASE_ADMIN_KEY environment variable"
                )
                cred_dict = json.loads(firebase_admin_key)
                cred = credentials.Certificate(cred_dict)
            except json.JSONDecodeError as e:
                raise ValueError(f"Failed to parse FIREBASE_ADMIN_KEY as JSON: {e}")

            firebase_admin.initialize_app(cred)

        # Store a Firestore client instance for reuse
        self._db = firestore.client()

    # ---------------------------------------------------------------------
    # Public API
    # ---------------------------------------------------------------------
    def get_task_messages(self, task_id: str) -> List[Dict[str, Any]]:
        """Return all messages for a given task as a list of dictionaries.

        Firestore structure::
            tasks/{task_id}/messages/{message_id}

        Args:
            task_id: Identifier of the task whose messages should be retrieved.

        Returns:
            List of message documents (each as a dict) including an "id" field.
        """
        # Retrieve ordered by timestamp descending

        logging.debug(f"Getting messages for task_id: {task_id}")
        messages_ref = self._db.collection(f"tasks/{task_id}/messages").order_by(
            "createdAt", direction=firestore.Query.DESCENDING
        )
        print(f"Messages reference: {messages_ref}")

        docs = messages_ref.get()
        print(f"Docs: {docs}")
        return [doc.to_dict() | {"id": doc.id} for doc in docs]

    def write_task_message(
        self, task_id: str, message: Optional[str] | None = None, **kwargs: Any
    ) -> str:
        """Write a new message document under ``tasks/{task_id}/messages``.

        If no ``timestamp`` is provided via ``kwargs``, the server timestamp will
        be used automatically.

        Args:
            task_id: Task identifier.
            message: Message body (stored under the "message" field).
            **kwargs: Additional fields to include in the document.

        Returns:
            The ID of the newly created Firestore document.
        """
        payload: Dict[str, Any] = dict(**kwargs)

        if message is not None:
            payload["message"] = message

        # Auto-add server timestamp if caller didn't provide one
        if "timestamp" not in payload:
            payload["createdAt"] = firestore.SERVER_TIMESTAMP

        doc_ref = self._db.collection(f"tasks/{task_id}/messages").document()
        doc_ref.set(payload)

        return doc_ref.id


# Create a singleton instance that can be imported elsewhere in the codebase
firestore_service = FirestoreService()
