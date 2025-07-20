"""Generic LLM executor service for OpenAI operations."""

import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


class GenericLLMExecutor:
    """Service for executing generic LLM operations using OpenAI."""

    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def summarize_conversation_to_sourcing_requirement(
        self, conversation_text: str
    ) -> str:
        """
        Summarize conversation text into a concise sourcing requirement.

        Args:
            conversation_text: The full conversation text to summarize

        Returns:
            A concise sourcing requirement based on the conversation
        """
        try:
            print(
                f"[GENERIC LLM EXECUTOR] Summarizing conversation to sourcing requirement"
            )
            print(
                f"[GENERIC LLM EXECUTOR] Conversation length: {len(conversation_text)} characters"
            )

            prompt = f"""
You are a sourcing specialist. Based on the following conversation, create a concise sourcing requirement that captures the key details needed for procurement.

Conversation:
{conversation_text}

Please create a sourcing requirement that includes:
1. What is being sourced (product/service)
2. Quantity needed
3. Location/delivery requirements
4. Budget constraints
5. Timeline requirements
6. Any special requirements or preferences

Format the response as a clear, professional sourcing requirement that can be used to contact suppliers.

Sourcing Requirement:
"""

            response = self.client.chat.completions.create(
                model="gpt-4o-mini",  # Using a cost-effective model
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional sourcing specialist who creates clear, concise sourcing requirements.",
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=500,
                temperature=0.3,
            )

            sourcing_requirement = response.choices[0].message.content.strip()

            print(
                f"[GENERIC LLM EXECUTOR] Generated sourcing requirement: {sourcing_requirement}"
            )
            return sourcing_requirement

        except Exception as e:
            print(f"[GENERIC LLM EXECUTOR] Error summarizing conversation: {e}")
            # Fallback: return a basic summary if LLM fails
            return f"Sourcing requirement based on conversation: {conversation_text[:200]}..."


# Create a singleton instance
generic_llm_executor = GenericLLMExecutor()
