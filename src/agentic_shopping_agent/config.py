from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    browser_use_api_key: str
    default_location: str = "United States"
    default_currency: str = "USD"


def load_settings() -> Settings:
    load_dotenv()

    api_key = os.getenv("BROWSER_USE_API_KEY")
    if not api_key:
        raise RuntimeError(
            "BROWSER_USE_API_KEY is missing. Create a .env file or export the variable before running the agent."
        )

    return Settings(
        browser_use_api_key=api_key,
        default_location=os.getenv("SHOPPING_AGENT_DEFAULT_LOCATION", "United States"),
        default_currency=os.getenv("SHOPPING_AGENT_DEFAULT_CURRENCY", "USD"),
    )

