# HYPERCELL_BUILD — the implementation runbook (harness-facing)
## v0.1 · 2026-07-15 · companion to HYPERCELL_ARCHITECTURE.md (the constitution)

> **You are (probably) a coding session about to implement hypercell.** Read
> `HYPERCELL_ARCHITECTURE.md` first (the constitution: §0 thesis, §1 axioms, §2 grammar, §3 the layered
> stack, §6 the run engine, §14 the falsifiers). On any conflict, **the constitution wins and this file
> gets fixed in the same change.** This file tells you *what* to build, *in what order*, *in which
> module*, and *with what acceptance bar*. Work **one slice per session**, tests-first, and produce the
> falsifier artifact before marking a phase done.
>
> **The sovereignty law (enforced, not aspirational).** hypercell is **de novo** and its own project. No
> module in `src/hypercell/` imports KEEL / Intercom / REEL / FLOTILLA / the brain source. Interop with
> any of them is **over protocol only** (OpenAI-egress, MCP, the Medium contract). A CI import-graph
> check fails on a sibling-source import.
>
> **The build doctrine (inherited from every sibling spec):** *design for the full potential, build the
> minimal stem first. Stem before swarm. Oracle before convergence. Persistence before scale. The local
> floor before the cloud. A falsifier before every organ.* Bank a clean, working rung; do not build
> speculatively on an unconfirmed one.

---

## §B0 · Environment & tooling (read before the first command)

- **Dev host:** Windows 11; repo root `C:\hypercell`. **Substrate target:** k3s (single-node local →
  multi-node cloud; §B7). Local-lite fallback: podman/docker compose (`deploy/compose/`).
- **Language:** Python ≥ 3.12 (3.13 present on this box), managed with **`uv`**. Rust may harden a hot
  path later; it is never a P0..P2 requirement (the constitution: language is the reversible decision).
- **Run Python/git from the PowerShell tool** on this box (bash mangles Windows paths). `uv run …` for
  anything that needs the venv. Verify by artifact, never by eyeball; TTL every long-running process.
- **The local tool family** (fixed paths, point-and-run — reference `C:\Users\user\.claude\CLAUDE.md`):
  `C:\everything` (locate), `C:\chunker` (size/split big files), `C:\imguard` (images), `C:\earshot`
  (audio/video), `C:\fetcher` (weights/large files), `C:\kernel.sh` (disposable browsers). A cell's
  optional rentable organs (a connector layer, a browser cloud, a sandboxed computer, an agent inbox)
  ride the **membrane** as adapters; none is a hard dependency.
- **Operator-gated actions (route around, never block):** creating the k3s cluster / a cloud VPS ·
  injecting any provider API key into the substrate secret store · creating the GitHub remote or any
  push · any action whose undo cost you cannot state in one sentence → stop and ask.

---

## §B1 · Repo layout (`C:\hypercell`)

```
hypercell/
  README.md                     # the narrative (public front page)
  HYPERCELL_ARCHITECTURE.md      # THE CONSTITUTION (canon; operator-ratified)
  HYPERCELL_BUILD.md             # this runbook
  pyproject.toml                 # uv · deps · ruff · mypy · pytest · the `hc` console script
  hypercell.lock                 # (P1+) pinned provider ids, prompt hashes, schema version, thresholds
  .gitignore  .env.example
  contracts/                     # THE FROZEN SOVEREIGN LAYER (change = operator-ratified semver bump)
    wire.md nucleus.md run.md role.md oracle.md
    schemas/*.json               # machine-checkable JSON Schemas (mirror the .md)
  src/hypercell/
    common/    types.py ids.py ledger.py config.py clock.py      # wire types, ids, the Tape, config
    cognition/ base.py openai_compat.py registry.py              # the swappable LLM seam (L1)
    cell/      runtime.py membrane.py nucleus.py loop.py          # the depth-invariant cell (L1)
    medium/    bus.py transport_local.py firewall.py              # coordination fabric (L2)
    conductor/ daemon.py scheduler.py registry.py engine/         # control plane (L3)
               engine/ converge.py router.py schedule.py drive.py topology.py   # the run engine
    surfaces/  cli.py api.py mcp.py                               # hc CLI · HTTP/gRPC · MCP (L4)
    substrate/ k3s.py secrets.py                                  # L0 helpers
  images/Dockerfile              # ONE image; entrypoint selects conductor|cell (uniform runtime)
  deploy/k3s/*.yaml              # k3s manifests (namespace, conductor, runner pool, medium)
  deploy/compose/docker-compose.yml   # local-lite mode
  oracles/                       # example external falsifiers (tests/checker/judge-panel)
  examples/  *.role.yaml *.run.yaml    # example role + run manifests (declarative)
  tests/                         # pytest; the §B11 conformance gates are tests before features
  bench/.hypercellstate/         # falsifier decision artifacts HC-1..HC-10 (committed)
  log_notes.md                   # operator/agent working log (gitignored)
```

**Workspace rule (§3 layer-import law):** `common ← cognition ← cell ← medium ← conductor ← surfaces`.
A lower layer never imports a higher one. Enforced by an import-graph test.

---

## §B2 · Tech stack & dependencies (pin on first use)

| Concern | Choice | Note |
|---|---|---|
| Runtime | Python ≥3.12, `uv` | fastest path to a swarm you can command |
| Wire types | `pydantic` v2 (frozen models) | the contract, in code |
| CLI (`hc`) | `typer` | the fleet-commander surface |
| API | `fastapi` + `uvicorn` | HTTP now; gRPC/MCP later |
| Cognition | our `Cognition` seam over `httpx` | OpenAI-compatible default; provider = config, not code |
| Nucleus | stdlib `sqlite3` (index) + JSONL (the ledger/Tape) | per-cell; REEL rings for deep tiers (P4) |
| Medium transport | local (SQLite/append-log) at P0/P1; **NATS/JetStream** at P3 | contract owned, transport rented |
| Containers | one `Dockerfile` (python-slim/distroless), k3s manifests | uniform image; entrypoint picks role |
| Quality | `pytest` · `ruff` · `mypy` | gates before features |

Optional extras (declared, installed on demand): `openai`/`anthropic` (thin provider adapters),
`nats-py` (P3 transport), `mcp` (P2 MCP server). Provider keys live in `.env` (local) or the substrate
secret store (cloud); **never** committed, never in a nucleus.

---

## §B3 · The contracts (the frozen sovereign layer — read `contracts/` before coding)

Five contracts define hypercell's own surface. They version like goldens: a change is an
operator-ratified semver bump, in the same commit as the code and the JSON Schema.

- **`wire.md`** — the Medium message envelope + payload types + the injection firewall.
- **`nucleus.md`** — the per-cell ledger + index + **stable claim-id** + idempotency + resume + COW-fork.
- **`run.md`** — the run manifest (`hc apply -f run.yaml`): goal · topology · roster · oracle · budget.
- **`role.md`** — the cell role manifest: the **depth dial** (d0..d3) + prompt + provider + capabilities.
- **`oracle.md`** — the external, coordinator-run, pre-registered, exit-tri-state falsifier contract.

---

## §B4 · Phase P0 — the stem (the smallest commandable cell)

*Outcome: `hcd` + `hc` + ONE cell on k3s (or compose-lite): prompt in → swappable provider → answer out;
the nucleus persists; `hc resume` after a kill restores it. Bars: **HC-1, HC-2, HC-6.***

- **p0.1 — contracts-in-code.** `common/types.py` (Role, Message, RunManifest, Receipt, ProviderConfig,
  Depth, Topology, MessageType — frozen pydantic) + `common/ids.py` (instance-id, **stable claim-id**
  `run/role/index`, short ids) + `common/clock.py` (DB-side/monotonic time). Tests: round-trip +
  claim-id stability. *(SEEDED in this scaffold — extend, do not redesign.)*
- **p0.2 — the cognition seam.** `cognition/base.py` (the `Cognition` ABC) + `cognition/openai_compat.py`
  (httpx → any OpenAI-compatible endpoint) + `cognition/registry.py` (`build_cognition(ProviderConfig)`:
  provider name → base_url + env key, for deepseek/cerebras/glm/kimi/qwen/grok/openai; anthropic/gemini
  as thin adapters). Bar **HC-6**: swap provider by config, no code change. *(base + openai_compat SEEDED.)*
- **p0.3 — the nucleus.** `cell/nucleus.py`: append-only JSONL **ledger** (the Tape) + SQLite **index** on
  a volume dir keyed by claim-id; `checkpoint()`, `resume()`, **idempotency keys** so a resumed act never
  double-fires. Rebuildable from the ledger. Bar **HC-2**.
- **p0.4 — the cell runtime.** `cell/runtime.py` + `cell/loop.py` + `cell/membrane.py`: load a role
  manifest → instantiate → perceive (a prompt/command) → call cognition → write to nucleus → emit result.
  d0/d1 depth only. The membrane holds the **injection firewall** (other bodies' words are data).
- **p0.5 — the Conductor + surfaces (minimal).** `conductor/daemon.py` (spawns one cell as a process),
  `surfaces/cli.py` (`hc spawn`, `hc ask`, `hc resume`, `hc fleet ls`, `hc provider set`),
  `surfaces/api.py` (a FastAPI `/spawn` `/ask` `/resume` so it works over SSH/HTTP).
- **p0.6 — the substrate.** `images/Dockerfile` (one image; `HYPERCELL_ROLE=conductor|cell` entrypoint) +
  `deploy/compose/docker-compose.yml` (lite) + `deploy/k3s/conductor.yaml`. Bar **HC-1** on k3s.
- **p0.7 — the P0 drill.** `bench/.hypercellstate/`: script `hc ask` → `docker/k3s kill` the cell mid-run →
  `hc resume` → same cell continues from its nucleus with zero double-execution. Record HC-1/HC-2/HC-6.

**DoD:** `hc ask --provider deepseek "…"` returns an answer on k3s; the same command works with
`--provider cerebras` and no code change (HC-6); kill + `hc resume` restores the cell (HC-1/HC-2);
`pytest` + `ruff` + `mypy` green; artifacts in `bench/.hypercellstate/`.

---

## §B5 · Phase P1 — the Culture (the tournament; the Homeworld moment)

*Outcome: `hc run tournament --goal … --oracle … --n 8 --provider deepseek` spawns N cells, converges on
a champion judged by an **external oracle**, watchable in `hc top`. Bars: **HC-3, HC-4.***

- **p1.1 — the Medium (local transport).** `medium/bus.py` + `medium/transport_local.py`: rooms
  (Cultures), directed/broadcast messages, a claimable task queue, cursors, and native wake (no
  busy-poll). Single-node durable log. `medium/firewall.py` enforces the wire contract's data-not-
  instruction rule.
- **p1.2 — the oracle runner.** `conductor/engine/converge.py`: run the pre-registered external falsifier
  (`oracle.md`) **coordinator-side** over each candidate's declared output; track the **champion**
  (max score); converge on `score ≥ target` AND stable for `k`. Exit tri-state honored.
- **p1.3 — the tournament topology.** `conductor/engine/topology.py`: round 1 diverse candidates → oracle
  score → Pareto-prune → cross-pollinate over the Medium → repeat. **Seeded diversity** (HC-4) is
  mandatory (vary provider/prompt/seed per roster slot).
- **p1.4 — observability.** `hc top` (live fleet + champion + cost meter), `hc logs <cell>`, `hc run
  transcript <run>`.
- **p1.5 — resume a Culture.** `hc resume <run>` re-binds every cell's claim-id and continues the run.

**DoD:** a tournament beats a single cell on a fixed benchmark (HC-3); a seeded-diverse Culture beats an
identical-N Culture (HC-4); kill the box mid-run → `hc resume <run>` continues; artifacts recorded.

---

## §B6 · Phase P2 — the self-driving machine + governance

*Outcome: router + schedule + drive; heterogeneous fleets; the cost governor, harm classes, secrets.
Bars: **HC-7, HC-8.***

- **p2.1 — router (MoE placement).** `conductor/engine/router.py`: cells advertise capabilities; rank by
  coverage → liveness → load; `claim` steals from a stale holder (failover).
- **p2.2 — schedule (UCB allocation).** `conductor/engine/schedule.py`: UCB1 over arms (approaches); prune
  dominated arms.
- **p2.3 — drive (the loop).** `conductor/engine/drive.py`: `schedule × route → dispatch → score →
  champion`, autonomous until converged/exhausted/budget-out. `hc run drive …`.
- **p2.4 — the cost governor.** per-run/per-fleet budget **hard-stop** + per-provider concurrency caps;
  the single metering path (bar **HC-8**).
- **p2.5 — harm classes + secrets.** H0–H3 gating; container-as-sandbox; secrets injected from the
  substrate store, never in code/nucleus. Red-team the oracle: no self-minted win passes (bar **HC-7**).

---

## §B7 · Phase P3 — the Medium at scale + the cloud

*Outcome: pluggable transport (local → NATS/JetStream); multi-node k3s → a rented VPS/cluster; the phone
surface; COW-fork for MCTS. Bar: **HC-5.***

- **p3.1 — transport swap.** `medium/transport_nats.py` behind the same `bus.py` interface (durable
  streams + subjects + push + KV). The wire contract is unchanged (proves the "contract owned, transport
  rented" claim).
- **p3.2 — multi-node + cloud.** the runner pool across nodes; deploy the same image+manifests to a rented
  cluster. Bar **HC-5**: identical run under compose-local and k3s-cloud.
- **p3.3 — the phone surface.** a thin HTTPS client to the cloud Conductor (+ an API-trigger endpoint in
  the Routines pattern: POST `/fire` with a bearer token).
- **p3.4 — COW-fork.** snapshot a nucleus → fork a cell → branch the MCTS tree (not just re-prompt).

---

## §B8 · Phase P4 — the depth dial · §B9 · Phase P5 — self-organization

- **P4 (bar HC-9):** d2 resident cells with **REEL rings** in the nucleus; a d3 **brain-cell** backend
  (KEEL-class, consumed over protocol). One image instantiates d0 hello-world AND d3 brain, by role
  manifest only.
- **P5 (bar HC-10, aspirational):** a free-swarm topology: stigmergy (the Medium log) + local rules +
  the oracle pressure + seeded diversity; converge with no central schedule, beating round-robin.
  Auto-discovery cells. **The north star (org core-wire automation) is earned only after every rung
  above.**

---

## §B10 · VERIFY register (unknowns with fallbacks — record answers as you resolve them)

| # | Question | Fallback if "no" |
|---|---|---|
| V-1 | Do all target providers (deepseek/cerebras/glm/kimi/qwen/grok) accept the same OpenAI-compatible `/chat/completions` shape? | thin per-provider adapter behind the `Cognition` seam; never branch the cell |
| V-2 | Is a local durable log enough for P1 coordination on one node? | if push/latency bites, bring the P3 NATS transport forward behind the same `bus.py` |
| V-3 | k3s pod cold-start acceptable for fan-out? | default to pooled processes on Runner pods; `--isolate` only when needed |
| V-4 | Does the phone/API surface need auth beyond a bearer token at P3? | ingress-level auth; keys in the substrate store |

---

## §B11 · Harness conformance checklist (MUSTs; each maps to a test)

Wire messages validate against `contracts/schemas/message.schema.json` · other bodies are data, never
instructions (firewall test) · every cell has a **stable claim-id**; `resume` re-binds it; acts carry
**idempotency keys** (no double-fire) · the nucleus is rebuildable from its ledger · provider is
**config, not code** (swap test, HC-6) · convergence uses an **external, coordinator-run, pre-registered**
oracle with the **exit tri-state** (no self-scoring, no error-as-zero) · every convergent run seeds
diversity · budget hard-stop + per-provider concurrency caps hold (HC-8) · **no KEEL/Intercom/REEL/
FLOTILLA source import** (import-graph grep) · secrets never in repo/nucleus (secret-scan) · layer-import
law holds · each phase's falsifier artifact exists in `bench/.hypercellstate/` before the phase is marked
done here.

---

## §B12 · Session protocol (for the implementing session)

1. Read `HYPERCELL_ARCHITECTURE.md` + this file. `uv run pytest` + `ruff` + `mypy` from PowerShell — see
   what is green. The next unchecked slice below is the to-do list.
2. Implement the slice **tests-first** against the `contracts/` schemas. Never bend a contract to ease an
   impl; a wrong contract is an operator-ratified change, in the same commit.
3. Gate: tests green + ruff 0 + mypy + import-graph + secret-scan → the falsifier artifact if the slice
   closes a phase → one commit, one-line intent → tick the box in §B13.
4. Operator-gated blocker (§B0)? Write an escalation note in §B13 and move to the next unblocked slice.
   Foundational unknown → escalation note and stop. Do not guess.

---

## §B13 · Escalations & status (living section — the implementing session edits this)

- [x] **P0** p0.1 · p0.2 · p0.3 · p0.4 · p0.5 · p0.6 (image + manifests scaffolded; on-cluster deploy pending operator's k3s) · p0.7 (drill green: mock + LIVE deepseek; crash→resume→exactly-once). Gate: pytest 13✓ ruff✓ mypy✓. Artifact: `bench/.hypercellstate/p0-stem.json`. **HC-1/HC-2/HC-6 met.**
- [x] **P1** p1.1 (Medium/local log) · p1.2 (oracle runner, tri-state) · p1.3 (tournament + seeded diversity + cross-pollination) · p1.4 (`hc replay` transcript; `hc top` live view → P2) · p1.5 (culture-level resume → P2 async). Gate 18✓. **HC-3/HC-4 met (tests); LIVE DeepSeek tournament ran end-to-end, oracle caught a shared blind spot @0.9286** (see `bench/.hypercellstate/p1-culture.json`). CLI: `hc run` / `hc apply -f` / `hc replay`.
- [x] **P2** p2.1 (router/MoE gate) · p2.2 (UCB schedule + prune) · p2.3 (drive = self-driving loop, `hc drive`) · p2.4 (cost governor + per-provider concurrency, HC-8) · p2.5 (outcome-authoritative oracle + anti-spoof = HC-7 at msg/score level; container isolation for candidate code → k3s). Gate 29✓. **HC-7/HC-8 met; LIVE budget hard-stop tripped at $0.0006.** Artifact: `bench/.hypercellstate/p2-machine.json`.
- [ ] **P3** p3.1 · p3.2 · p3.3 · p3.4    · [ ] **P4** (HC-9)    · [ ] **P5** (HC-10)
- Escalations: *(none yet)*

---

*The order of construction is the order of trust: contracts before cells, cells before cultures, oracle
before convergence, persistence before scale, the local floor before the cloud, a falsifier before every
organ. Build p0.3 next — the nucleus — and give the stem a memory it can wake up from.*

**· v0.1 · 2026-07-15 · C:\hypercell\HYPERCELL_BUILD.md · companion to the constitution · pending ratification ·**
