"""Run the service: ``python -m pitwall_ingest``.

Reads ``HOST`` (default ``127.0.0.1``) and ``PORT`` (default ``8000``) from the environment.
"""

import os

import uvicorn

from pitwall_ingest.api.app import create_app


def main() -> None:
    """Start the HTTP server."""
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run(create_app(), host=host, port=port)


if __name__ == "__main__":
    main()
