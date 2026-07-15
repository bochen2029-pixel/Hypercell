# CONTRACT: nucleus — per-cell persistence, identity & resume

**Status:** v0.1 DRAFT. The nucleus is a cell's private, persistent self (its PVC). A cell is a **durable
identity, not a process** (constitution A3). Kill the body, the cell persists; re-instantiate, it resumes.
RFC-2119.

## Two-level identity (the resume keystone)
- **instance-id** — one ephemeral process/pod. Changes every instantiation.
- **stable claim-id** — `run/role/index` (e.g. `r7/refiner/3`). The volume binds to THIS, not the process
  (the StatefulSet pattern: `web-0 → pvc-web-0`). `hc resume` re-binds each claim-id to a fresh instance.

## Storage (tiered; a throwaway worker never pays a resident's cost)
- **Ledger (truth):** append-only JSONL at `<HYPERCELL_HOME>/<claim-id>/ledger.jsonl`. Every percept,
  decision, produced artifact, and checkpoint is appended. Never rewritten. The system of record.
- **Index (state):** SQLite at `<claim-id>/index.db` — cursors, checkpoints, working state, task status. A
  **disposable render** of the ledger (rebuildable via `rebuild()`).
- **REEL rings (deep tiers, d2/d3 — P4):** Ring 0 identity · Ring 2 working · Ring 3 consolidated · Ring 4
  retrieval index, budgeted by ratio, compressed by the cell. Identity survives a provider swap because the
  self is the journaled ledger, not the model.

## Operations (MUST)
- `checkpoint(state)` — append a `checkpoint` record to the ledger, then update the index atomically.
- `resume()` — reconstruct working state from the last checkpoint + ledger tail. **Resume is context
  reconstruction, not deterministic replay** (LLM cognition is not replayable).
- **Idempotency:** every side-effecting act records an `idem` key; on resume, an act whose `idem` is already
  in the ledger is **skipped** (exactly-once effects).
- `rebuild()` — regenerate the index from the ledger alone (no model in the loop).
- `snapshot()` / `fork(new_claim_id)` — **COW copy** of the nucleus. This is the mechanism for **MCTS over
  agent state**: branch the search tree by forking a nucleus, not by re-prompting (P3).

## Ledger record shape
`{seq, ts, kind: percept|decision|action|outcome|checkpoint|handoff|system, idem?, body, refs[]}` — append
order is truth; `refs` point to prior `seq`. Secrets MUST NOT be written to the ledger.
