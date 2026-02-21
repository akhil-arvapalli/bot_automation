import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") # If they provide it, otherwise fallback to CLI
PORT = int(os.getenv("PORT", 3000))
