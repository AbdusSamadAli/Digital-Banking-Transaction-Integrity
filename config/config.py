"""Central configuration. Everything is driven by env vars / .env so the same suite runs locally, on Grid and in CI."""
import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    BASE_URL: str = os.getenv("BASE_URL", "https://parabank.parasoft.com/parabank").rstrip("/")
    API_URL: str = os.getenv("API_URL", f"{BASE_URL}/services/bank")

    BROWSER: str = os.getenv("BROWSER", "chrome").lower()
    HEADLESS: bool = os.getenv("HEADLESS", "true").lower() == "true"
    WINDOW_SIZE: str = os.getenv("WINDOW_SIZE", "1920,1080")
    GRID_URL: str = os.getenv("GRID_URL", "")  # e.g. http://localhost:4444 -> run on Selenium Grid

    EXPLICIT_WAIT: int = int(os.getenv("EXPLICIT_WAIT", "15"))
    API_TIMEOUT: int = int(os.getenv("API_TIMEOUT", "20"))

    # ParaBank moves this amount from the funding account into every newly opened account
    NEW_ACCOUNT_MIN_DEPOSIT: str = os.getenv("NEW_ACCOUNT_MIN_DEPOSIT", "100.00")
