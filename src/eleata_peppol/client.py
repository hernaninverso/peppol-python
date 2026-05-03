"""HTTP client (sync + async)."""

from __future__ import annotations

import base64
import time
from dataclasses import dataclass
from typing import Any, Iterable, Literal

import httpx

DEFAULT_BASE_URL = "https://api.eleata.io"
DEFAULT_TIMEOUT = 15.0
DEFAULT_RETRIES = 3
DEFAULT_MAX_PAYLOAD = 5_000_000

Format = Literal["peppol-bis-3", "xrechnung-2.x", "factur-x", "ubl"]


class EleataError(Exception):
    def __init__(self, message: str, status: int | None = None, body: Any = None) -> None:
        super().__init__(message)
        self.status = status
        self.body = body


@dataclass
class ValidationResult:
    valid: bool
    format: str
    errors: list[dict]
    warnings: list[dict]
    public_id: str
    report_url: str
    duration_ms: int

    @classmethod
    def from_dict(cls, d: dict) -> "ValidationResult":
        return cls(
            valid=d["valid"],
            format=d["format"],
            errors=d.get("errors", []),
            warnings=d.get("warnings", []),
            public_id=d.get("public_id", ""),
            report_url=d.get("report_url", ""),
            duration_ms=d.get("duration_ms", 0),
        )


@dataclass
class BatchJob:
    job_id: str
    status: str
    total_files: int

    @classmethod
    def from_dict(cls, d: dict) -> "BatchJob":
        return cls(job_id=d["job_id"], status=d["status"], total_files=d.get("total_files", 0))


class _BaseClient:
    def __init__(
        self,
        api_key: str,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_RETRIES,
        max_payload: int = DEFAULT_MAX_PAYLOAD,
    ) -> None:
        if not api_key:
            raise EleataError("api_key required")
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self.max_payload = max_payload

    def _headers(self, content_type: str = "application/json") -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": content_type,
            "User-Agent": "eleata-python/0.1.0",
        }

    def _backoff_seconds(self, attempt: int) -> float:
        return 0.2 * (4 ** attempt)


class Client(_BaseClient):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._http = httpx.Client(timeout=self.timeout)

    def __enter__(self) -> "Client":
        return self

    def __exit__(self, *args: Any) -> None:
        self._http.close()

    def validate(self, format: Format, xml: bytes | str) -> ValidationResult:
        body = xml.encode() if isinstance(xml, str) else xml
        if len(body) > self.max_payload:
            raise EleataError(f"payload exceeds {self.max_payload} bytes")
        last_err: Exception | None = None
        for attempt in range(self.max_retries + 1):
            try:
                r = self._http.post(
                    f"{self.base_url}/v1/validate",
                    params={"format": format},
                    content=body,
                    headers=self._headers("application/xml"),
                )
                if r.status_code >= 500 and attempt < self.max_retries:
                    raise EleataError(f"server error {r.status_code}", r.status_code)
                if r.status_code >= 400:
                    raise EleataError(f"HTTP {r.status_code}: {r.text}", r.status_code, r.text)
                return ValidationResult.from_dict(r.json())
            except (EleataError, httpx.HTTPError) as e:
                last_err = e
                if attempt < self.max_retries:
                    time.sleep(self._backoff_seconds(attempt))
                    continue
                raise
        raise last_err  # type: ignore[misc]

    def validate_batch(
        self, format: Format, files: Iterable[tuple[str, bytes]], webhook_url: str | None = None
    ) -> BatchJob:
        payload = {
            "format": format,
            "files": [{"id": fid, "xml": base64.b64encode(b).decode()} for fid, b in files],
            "webhook_url": webhook_url,
        }
        r = self._http.post(
            f"{self.base_url}/v1/validate/batch",
            json=payload,
            headers=self._headers(),
        )
        if r.status_code >= 400:
            raise EleataError(f"HTTP {r.status_code}: {r.text}", r.status_code, r.text)
        return BatchJob.from_dict(r.json())

    def get_job(self, job_id: str) -> BatchJob:
        r = self._http.get(
            f"{self.base_url}/v1/jobs/{job_id}",
            headers=self._headers(),
        )
        if r.status_code >= 400:
            raise EleataError(f"HTTP {r.status_code}: {r.text}", r.status_code, r.text)
        return BatchJob.from_dict(r.json())


class AsyncClient(_BaseClient):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._http = httpx.AsyncClient(timeout=self.timeout)

    async def __aenter__(self) -> "AsyncClient":
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self._http.aclose()

    async def validate(self, format: Format, xml: bytes | str) -> ValidationResult:
        body = xml.encode() if isinstance(xml, str) else xml
        if len(body) > self.max_payload:
            raise EleataError(f"payload exceeds {self.max_payload} bytes")
        r = await self._http.post(
            f"{self.base_url}/v1/validate",
            params={"format": format},
            content=body,
            headers=self._headers("application/xml"),
        )
        if r.status_code >= 400:
            raise EleataError(f"HTTP {r.status_code}: {r.text}", r.status_code, r.text)
        return ValidationResult.from_dict(r.json())
