# hypercell — ONE uniform image. The entrypoint selects conductor | cell by HYPERCELL_ROLE.
# (The same image runs the control plane and the cells: one runtime, differentiated by role — A1.)
FROM python:3.12-slim AS base
ENV PYTHONUNBUFFERED=1
WORKDIR /app

# uv for fast, reproducible installs
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

COPY pyproject.toml README.md ./
COPY src ./src
RUN uv pip install --system .

# per-cell nuclei (ledgers + indexes) mount here; a PVC binds by stable claim-id
ENV HYPERCELL_HOME=/var/lib/hypercell
VOLUME ["/var/lib/hypercell"]

ENV HYPERCELL_ROLE=conductor
# conductor -> the control-plane daemon (hcd); cell -> the cell runtime.
# (Both entrypoints are implemented in P0; this scaffold wires the dispatch.)
ENTRYPOINT ["sh", "-c", "if [ \"$HYPERCELL_ROLE\" = cell ]; then exec python -m hypercell.cell.runtime; else exec hcd; fi"]
