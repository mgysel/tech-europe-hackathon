"""Configuration settings for the AI Food-Ordering Assistant."""

import os
from dotenv import load_dotenv

# Load environment variables (only if .env file exists)
load_dotenv()

# OpenAI settings
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
LLM_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1")  # Agent uses GPT-4.1 for conversation
RESTAURANT_SEARCH_MODEL = os.getenv("RESTAURANT_SEARCH_MODEL", "o3")  # Restaurant tool uses o3
TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", "0.3"))

# Agent settings
SYSTEM_TEMPLATE = (
    "You are an expert food‑order assistant. Your job is to help the user place "
    "group food orders. Start by asking any follow‑up questions needed to fully "
    "specify the order (dietary restrictions, budget, location, delivery time, "
    "etc.). When you have enough info, call `search_restaurants` with a short "
    "query containing cuisine, size, and location. After the tool returns, "
    "reply **only** with the restaurant list in pretty JSON."
)

# FastAPI settings
APP_TITLE = "AI Food‑Ordering Assistant"
APP_VERSION = "1.0.0" 