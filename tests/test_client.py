"""Smoke tests for sync + async clients."""

import pytest

from eleata_peppol import AsyncClient, Client, EleataError


def test_client_requires_api_key():
    with pytest.raises(EleataError):
        Client(api_key="")


def test_client_rejects_oversized_payload():
    client = Client(api_key="evk_test", max_payload=100)
    with pytest.raises(EleataError, match="exceeds"):
        client.validate(format="peppol-bis-3", xml=b"x" * 200)


def test_async_client_requires_api_key():
    with pytest.raises(EleataError):
        AsyncClient(api_key="")


@pytest.mark.asyncio
async def test_async_client_rejects_oversized_payload():
    async with AsyncClient(api_key="evk_test", max_payload=100) as client:
        with pytest.raises(EleataError, match="exceeds"):
            await client.validate(format="peppol-bis-3", xml=b"x" * 200)


def test_client_accepts_str_xml():
    """String input should be coerced to bytes (encoded utf-8)."""
    client = Client(api_key="evk_test", max_payload=1000)
    # Will fail at network level but not at payload check
    with pytest.raises(EleataError) as exc:
        client.validate(format="ubl", xml="<x/>")
    assert "exceeds" not in str(exc.value)
