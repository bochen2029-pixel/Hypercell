"""`web.fetch` — retrieve one document. Structurally read-only by construction, not by promise."""
from __future__ import annotations

import hashlib
from typing import Any

from . import AdapterError, corpus_dir, scrub


def execute(args: dict[str, Any]) -> tuple[str, str, dict[str, Any]]:
    url = str(args["url"])
    corpus = corpus_dir()
    if corpus is None:  # pragma: no cover - the live path needs a network and a key
        raise AdapterError(
            "no fixture corpus and live HTTP is not wired at GROUND-0. Set HYPERCELL_GROUNDED_CORPUS "
            "to run the act plane hermetically."
        )

    # A URL maps to a fixture by digest, so a corpus entry is addressed the same way an artifact is.
    name = hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]
    for candidate in (corpus / f"{name}.txt", corpus / (url.rsplit("/", 1)[-1] or "index.txt")):
        if candidate.is_file():
            content = candidate.read_text(encoding="utf-8")
            prov = scrub(
                {
                    "channel": "retrieved_page",
                    "adapter": "web.fetch",
                    "url": url,
                    "headers": args.get("headers", {}),
                }
            )
            return content, "text/html", prov
    raise AdapterError(f"not in the fixture corpus: {url}")
