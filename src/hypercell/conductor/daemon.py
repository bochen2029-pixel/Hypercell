"""The control-plane daemon (hcd). P0: serve the Conductor HTTP API.

Fan-out to separate cell processes/pods is P1+; for P0 the conductor hosts the cell in-process behind
the API and the CLI.
"""
from __future__ import annotations

import os


def main() -> None:
    import uvicorn

    host = os.environ.get("HYPERCELL_API_HOST", "127.0.0.1")
    port = int(os.environ.get("HYPERCELL_API_PORT", "8787"))
    uvicorn.run("hypercell.surfaces.api:app", host=host, port=port, log_level="info")


if __name__ == "__main__":
    main()
