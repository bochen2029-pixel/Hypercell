"""`web.search` — find candidate documents. Returns pointers, never the cell's conclusion."""
from __future__ import annotations

from typing import Any

from . import AdapterError, corpus_dir, scrub


def execute(args: dict[str, Any]) -> tuple[str, str, dict[str, Any]]:
    query = str(args["query"]).lower()
    k = int(args.get("k", 5))
    corpus = corpus_dir()
    if corpus is None:  # pragma: no cover - live search needs a provider key
        raise AdapterError("no fixture corpus; set HYPERCELL_GROUNDED_CORPUS to search hermetically")

    hits = []
    for path in sorted(corpus.glob("*.txt")):
        text = path.read_text(encoding="utf-8", errors="replace")
        if any(term in text.lower() for term in query.split()):
            hits.append({"title": path.stem, "path": path.name, "snippet": text[:160].replace("\n", " ")})
    if not hits:
        raise AdapterError(f"no corpus document matches {query!r}")

    lines = [f"{i + 1}. {h['title']} ({h['path']})\n   {h['snippet']}" for i, h in enumerate(hits[:k])]
    prov = scrub({"channel": "tool_result", "adapter": "web.search", "query": args["query"]})
    return "\n".join(lines), "text/plain", prov
