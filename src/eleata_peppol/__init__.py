"""eleata-peppol — Python SDK for eleata Peppol API.

Defaults: timeout 15s, 3 retries with exponential backoff, max payload 5MB.
"""

from .client import AsyncClient, Client, EleataError, ValidationResult, BatchJob

__all__ = ["Client", "AsyncClient", "EleataError", "ValidationResult", "BatchJob"]
__version__ = "0.1.0"
