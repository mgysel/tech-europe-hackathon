"""Configuration settings for the AI Food-Ordering Assistant."""

import os
from dotenv import load_dotenv

# Load environment variables (only if .env file exists)
load_dotenv()

# OpenAI settings
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
LLM_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1")  # Agent uses GPT-4.1 for conversation
SEARCH_MODEL = os.getenv("SEARCH_MODEL", "o3")  # Search tool uses o3
TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", "0.3"))

# Agent settings
SYSTEM_TEMPLATE = (
    "You are an expert ordering assistant. Your job is to help the user with "
    "any ordering task - whether it's food, services, products, or other business needs. "
    "Start by asking any follow‑up questions needed to fully specify the requirements "
    "(quantity, budget, location, delivery/availability time, special needs, etc.). "
    "When you have enough info, call `search_options` with a short query containing "
    "the type of business/service needed, requirements, and location. After the tool returns, "
    "reply **only** with the options list in pretty JSON."
)

# Firebase settings
FIREBASE_ADMIN_KEY = os.getenv("FIREBASE_ADMIN_KEY")
print(f"Config Firebase admin key: {FIREBASE_ADMIN_KEY}")

# FastAPI settings
APP_TITLE = "AI Ordering Assistant"
APP_VERSION = "1.0.0" 