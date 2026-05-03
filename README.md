# eleata-peppol

> Python SDK for the [eleata Peppol API](https://peppol.eleata.io). Validate
> EU invoices (Peppol BIS 3, XRechnung, Factur-X, UBL) in 5 lines.

[![PyPI](https://img.shields.io/pypi/v/eleata-peppol.svg)](https://pypi.org/project/eleata-peppol/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

## Install

```bash
pip install eleata-peppol
```

## Usage

```python
import os
from eleata_peppol import Client

client = Client(api_key=os.environ["ELEATA_KEY"])

with open("invoice.xml", "rb") as f:
    result = client.validate(
        format="peppol-bis-3",
        xml=f.read(),
    )

if not result.valid:
    raise ValueError(f"Invalid: {result.errors}")
print(f"✓ Valid in {result.duration_ms}ms — {result.report_url}")
```

## Async

```python
from eleata_peppol import AsyncClient

async with AsyncClient(api_key=os.environ["ELEATA_KEY"]) as client:
    result = await client.validate(format="xrechnung-2.x", xml=xml_bytes)
```

## Defaults

- **Timeout**: 15 seconds
- **Retries**: 3 with exponential backoff
- **Max payload**: 5 MB (client-side reject)
- **Base URL**: `https://api.eleata.io`

## Batch

```python
job = client.validate_batch(
    format="peppol-bis-3",
    files=[(invoice.id, invoice.xml) for invoice in invoices],
    webhook_url="https://yourapp.com/webhooks/eleata",
)
print(f"Job started: {job.job_id}")
```

## Type hints

Full type annotations. Works with `mypy --strict` and Pyright.

## License

MIT
