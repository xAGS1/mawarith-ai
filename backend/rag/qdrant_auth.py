"""Optional authentication for the existing Qdrant REST transport."""

import os


def qdrant_auth_kwargs() -> dict:
    api_key = os.getenv("QDRANT_API_KEY")
    return {"headers": {"api-key": api_key}} if api_key else {}
