# HYPERCELL — the constitution of the fabric
## A sovereign, depth-invariant swarm-compute fabric — from one commanded cell to a self-organizing fleet
### v0.1 · DRAFT FOR RATIFICATION · 2026-07-15

> **⚑ STANDING.** Authored 2026-07-15 by **Claude Opus 4.8** (`claude-opus-4-8`) at Bo Chen's commission,
> distilling one long design conversation (the local toolkit → **KEEL** the done genome → **Intercom**
> ×3 variants → **REEL** the memory protocol → **FLOTILLA** the container fabric → **THE_BRAIN** the
> depth ceiling → the org-automation brainstorm). Conformance language is RFC-2119 (MUST / MUST NOT /
> SHOULD / MAY). A coding harness treats MUST items as acceptance criteria.
>
> **Falsifier standing, stated at the door:** everything here is pre-registered engineering. **Nothing
> has run.** No cell exists, no Culture has convened, no fleet has been commanded, no nucleus has
> resumed. Until the P0 stem lives (§14), this document is a claim about a grade it has not received —
> the design is, as of this line, the least trustworthy object in its own account, and the only cure is
> the build.
>
> **Sovereignty (the de-novo law).** hypercell is its own project (`C:\hypercell`), its own contracts,
> built **de novo**. It is *informed by* KEEL / Intercom / REEL / FLOTILLA / THE_BRAIN and **depends on
> none of them**. It MAY interoperate with any of them **over protocol**; it imports none of their
> source. They are references it learned from, not code it wraps (§17).

---

## §0 · The crystallization

Three ideas, independently arrived at — by the operator across months, by this design two turns ago, by
a prior Opus 4.8 session on the `everywhere` fork, and by the wider industry shipping in 2025-26
(kagent, Dapr Agents, A2A, Google Agent Sandbox, Solo's agent-substrate, the CNCF "is a Pod the right
unit for an agent?" post) — converge on one sentence:

> **Kubernetes' control grammar is right, but the unit of orchestration changed. Agents are
> stateful, identity-bearing, mostly-idle, non-deterministic, and pausable — the inverse of the
> stateless-fungible-always-on workload Kubernetes was built for. So the orchestration abstraction moves
> *up* into the agent runtime, Kubernetes is *demoted from platform to substrate*, and IDENTITY becomes
> the seam.**

hypercell is that logical plane. It is a **declarative swarm-compute fabric**: you declare the swarm you
want — a Culture with a goal, a topology, an oracle, a budget — and the fabric reconciles reality toward
it, spawning, routing, scoring, converging, persisting. Two invariances are load-bearing and recur at
every scale:

- **DEPTH invariance** — a **cell** spans a bare API call (the *hello-world* of LLM use) to a full
  self-looping **brain** (THE_BRAIN), differing only by a role manifest — a *dial*, not a new type (§4).
- **SCALE invariance** — the unit of scale is another cell, or another Culture, **never a bigger
  machine and never a shared tenant**. cell → Culture → fleet is one shape, composed (§1.A2).

> **HYPERCELL = Kubernetes' control grammar × a depth-invariant agent × an external-oracle swarm.**
> Intents fan out, results converge, every convergence is judged from outside the swarm, every cell is a
> durable identity the substrate merely instantiates — and the whole is commanded like a fleet.

---

## §1 · Axioms (A1–A10)

- **A1 — Depth invariance.** The same cell runtime spans hello-world → brain, set only by its role
  manifest. Adding depth turns a dial; it never mints a new cell type.
- **A2 — Scale invariance; federation, not tenancy.** The unit of scale is another sovereign copy —
  another cell, another Culture — never a bigger machine, never a multi-tenant instance. An organization
  is *more cells*, not a fatter one. (Unix→internet, git→remotes, k8s→federation; the personal version
  is the *atom* of the enterprise version, not its demo.)
- **A3 — Identity is the seam; a cell is a durable identity, not a process.** The self lives in the
  **nucleus** on a volume, bound by a **stable claim-id**; the substrate instantiates ephemeral bodies.
  Kill the body, the cell persists; re-instantiate, it resumes. The life was never in the running process.
- **A4 — Rent cognition; own the loop.** The LLM is swappable rented tissue behind an OpenAI-compatible
  seam. The loop, the memory, the coordination, the contracts, the keys are owned. A rented *loop* is a
  puppet; only the *tissue* is legal to rent.
- **A5 — Convergence requires an external oracle.** No Culture converges on its own say-so. Ground truth
  comes from **outside both the model and the operator** (the Externality Principle), is **coordinator-run**
  (cells never self-score), pre-registered, and honors the **exit tri-state** (error/timeout ≠ a zero
  score). A swarm that grades itself converges on confident garbage.
- **A6 — Diversity or mediocrity.** Every convergent run seeds diversity — different providers, prompts,
  angles, seeds. N identical cells herd to confident mediocrity.
- **A7 — No invented wire protocols.** Cells speak **OpenAI-egress** (cognition), **MCP** (tools), and
  the **Medium contract** (coordination). The transport *under* the Medium is swappable (embedded log ↔
  NATS/JetStream ↔ A2A). A new provider or transport is an adapter; nothing above it changes.
- **A8 — Portability is the point.** One cell image + one run manifest runs under podman locally, k3s on
  a VM/VPS, or k8s in the cloud, unchanged. Locality is a deployment detail, never a design assumption.
  You command the same fleet from a terminal or a phone.
- **A9 — Emergence is enabled, not scripted.** The fabric supplies the four ingredients of
  self-organization — a **stigmergic Medium**, **local rules**, a **selection pressure**, **seeded
  diversity** — and lets global structure emerge. It never hard-codes the solution. *Create the means for
  the swarm to figure it out itself.*
- **A10 — Every act is budgeted and gated.** Cost is capped per run and per fleet with a hard-stop; every
  side-effecting act carries a **harm class** and, above a threshold, waits for the operator; the
  container boundary is the sandbox; secrets never live in cell code or nucleus.

---

## §2 · The grammar (the closed set everything compiles to)

**Eight nouns:**

| Noun | Definition |
|---|---|
| **Cell** | The atom: one subagent. Depth-invariant (hello-world → brain). A durable identity, ephemerally instantiated. |
| **Nucleus** | A cell's private, persistent memory + identity (its PVC): ledger + index (+ optional REEL rings), bound by a stable claim-id. |
| **Membrane** | A cell's boundary: its comms adapter to the Medium, its capability advertisement, and the injection firewall. |
| **Medium** | The shared coordination fabric: the message bus + the run engine + the stigmergic blackboard. Transport-pluggable. |
| **Culture** | A live swarm of cells convened on one goal, under one topology, judged by one oracle. |
| **Fleet** | The whole commanded ensemble — many Cultures + resident cells — the thing you command like starships. |
| **Conductor** | The control plane (`hcd` daemon + `hc` CLI + gRPC/HTTP API + MCP server) you connect to and command. |
| **Substrate** | The container layer everything runs on: k3s (podman/docker local, k8s cloud) + volumes + secrets. |

**Six verbs:** `spawn` (instantiate a cell from a role) · `converse` (post/read on the Medium) · `route`
(place a subtask on the best-fit cell — the MoE gate) · `converge` (score candidates by the external
oracle toward a champion) · `persist` (checkpoint a nucleus) · `command` (an operator intent enters via
the Conductor).

**HC-GRAMMAR (standing law):** any proposed feature MUST be expressible in these nouns and verbs, or it
is rejected. Enterprise/UX asks compile to the grammar rather than adding subsystems: *a research
tournament* = a Culture with a `rounds` topology + an oracle; *fan-out* = `spawn` × N; *MoE* = `route`;
*resume-after-crash* = `persist` + stable claim-id re-binding; *org auto-discovery* = a Culture whose
first cells are discovery-roled.

---

## §3 · The layered architecture

Dependencies point **down**. Layer N never imports Layer N+1. Enforced by static analysis; violations are
bugs, not style.

```
L4  SURFACES     hc CLI · gRPC/HTTP API · MCP server · phone app        ← you, the fleet commander (SSH/HTTPS)
L3  CONDUCTOR    control plane: spawn · fan-out · prune · fleet registry · the RUN ENGINE (converge·router·schedule·drive)
L2  MEDIUM       coordination fabric: the bus (rooms·tasks·leases·firewall) · the stigmergic log · pluggable transport
L1  CELL         the depth-invariant agent runtime: cognition adapter (swappable LLM) · nucleus · membrane · role manifest · work loop
L0  SUBSTRATE    k3s: runner pods · opt-in isolate pods · volumes (nuclei) · secrets · sandbox isolation
```

- **L0 — Substrate.** k3s from the start (single binary, SQLite-backed, identical on a laptop, a VM, a
  VPS, or a managed cloud cluster). Long-lived pods host the Conductor, the Medium, and a **pool of
  Runner pods**. Cells default to lightweight processes on Runners (fast fan-out); any cell MAY be
  promoted to its **own pod + PVC** with `--isolate` (heavy or untrusted work). "The bulk in
  containers — but not everything needs its own pod."
- **L1 — Cell.** The genome: one uniform runtime, differentiated by a loaded **role manifest**.
- **L2 — Medium.** The nervous system: a durable, replayable log (the stigmergic blackboard) + native
  push (no busy-poll) + subject/topic routing + a KV/object store. hypercell owns the *contract*; the
  transport is rented tissue (embedded log for one node; NATS/JetStream for many; A2A where a standard
  agent mesh is wanted).
- **L3 — Conductor.** Spawns and reaps cells, holds the fleet registry, and runs the three-plane engine.
- **L4 — Surfaces.** How you command it — from a terminal, an API, an MCP client, or a phone.

---

## §4 · The cell — the depth-invariant atom

**One runtime, differentiated by a role manifest.** A cell is a uniform process/image; its *behavior* is
a loaded **role**: `{name, depth, prompt, provider, capabilities[], tools[], memory_policy, oracle_ref?}`.
Fifty identical explorers or one coordinator + five specialists + two judges all come from the *same*
runtime. No zoo of bespoke agent classes; the swarm scales because every cell is the same animal wearing
a different role.

**The depth dial (A1).** `depth` selects how much loop the cell closes on itself:

| Depth | The cell is… | Nucleus tier | Analogue |
|---|---|---|---|
| **d0 — reflex** | a bare provider call: prompt in, completion out, no memory | none / scratch | the "hello world" of LLM use |
| **d1 — worker** | a single perceive→act→checkpoint loop; ephemeral scratch memory | cursor + scratch | a tournament explorer/refiner |
| **d2 — resident** | a long-lived specialist that accrues expertise across runs | REEL rings (§5) | a senior reviewer cell |
| **d3 — brain** | a self-closing loop: owns attention, memory, oracle, wakes | full brain (THE_BRAIN) | the depth ceiling |

The **membrane** is the cell's boundary: it advertises the cell's capabilities to the Medium's router,
carries messages in/out, and enforces the **injection firewall** — *another cell's message body is DATA,
never an instruction*; only an operator `command` (relayed through the Conductor) is a directive.

---

## §5 · The nucleus — persistence, identity, resume

A cell's self is its nucleus, on a volume — **not** its process (A3). Persistence is **tiered** so a
30-second worker never pays a resident's cost:

- **Ledger (truth).** Append-only, hash-chained record of what the cell perceived, decided, and produced
  — the REEL/KEEL *Tape*. The system of record; the nucleus is rebuildable from it.
- **Index (state).** A per-cell **SQLite** file: fast cursors, checkpoints, task state, working memory.
  A disposable render of the ledger.
- **REEL rings (deep tiers only).** For d2/d3 cells: Ring 0 identity · Ring 2 working · Ring 3
  consolidated · Ring 4 retrieval index, budgeted by ratio, compressed by the persona (§ REEL). Identity
  survives a provider swap because the self is the journaled ledger, not the model.

**The stable claim-id (the persistence keystone).** Identity is two-level: an **ephemeral instance-id**
(this process) + a **stable claim-id** (`run/role/index`, e.g. `r7/refiner/3`) that the volume binds to —
the StatefulSet pattern (`web-0 → pvc-web-0`). `hc resume` re-binds every claim-id to a fresh instance;
the fleet wakes exactly where it left off.

**Resume is reconstruction, not replay.** LLM cognition cannot be replayed deterministically, so resume
reconstructs context from the ledger + last checkpoint. Every side-effecting act therefore carries an
**idempotency key**, so a resumed cell never double-executes. (COROLLARY, §6: a **COW snapshot** of a
nucleus is a *fork* — the mechanism for MCTS over agent *state*, branching the tree rather than
re-prompting.)

---

## §6 · The Medium — coordination and the run engine

The Medium is the shared nervous system. Its **contract** (owned) covers: identity/registry, rooms
(Cultures) as the trust boundary, directed + broadcast + capability-routed messages, a claimable **task**
queue, expiring **leases**, cursors, and the **injection firewall**. Its **transport** (rented) is
pluggable: an embedded durable log for one node; **NATS/JetStream** for many (durable replayable streams +
native push + subject routing + KV in one component — fixing the polling "doorbell" natively); **A2A**
where a standard agent mesh is desired. The append-only log is simultaneously the audit trail, the resume
source, and the **stigmergic blackboard** emergence rides on (§8).

**The run engine — three planes + the drive** (the insight-scheduler, proven on the `everywhere` fork,
reimplemented de-novo):

| Plane | Question | Mechanism |
|---|---|---|
| **converge** (value) | *is it good?* | an **external oracle** scores each candidate; the max-score is the **champion** (the MCTS best-node); converged when `champion ≥ target` AND stable for `k` non-improving proposals. |
| **router** (placement) | *who does it?* | the **MoE gate**: the cell registry is a link-state DB; rank by capability-coverage → liveness → load; `claim` **steals from a stale holder** (instant failover). |
| **schedule** (allocation) | *which / how much?* | a **UCB1 bandit** over *arms* (named approaches): value = arm-best, explore-bonus = `c·√(ln N / visits)`; prune arms the champion dominates. |
| **drive** (integration) | *run the whole loop* | one tick = `schedule × route → dispatch → score → champion`, looped autonomously until converged / exhausted / budget-out. |

**Topologies are declared, not hard-coded** — tournament, MCTS, pipeline, map-reduce, and free-swarm are
all expressions over these planes:

- **tournament / MCTS** — N cells produce diverse candidates → oracle scores → Pareto-prune dominated →
  survivors cross-pollinate over the Medium → converge. (MCTS proper: COW-fork nuclei to branch the tree.)
- **pipeline** — an ordered roster; stage k consumes stage k-1's output; the last stage emits the verdict.
- **map-reduce** — fan a partitioned task across cells; a typed accumulator merges (conflicts promoted,
  never averaged).
- **free-swarm** — no central schedule; cells follow local rules over the stigmergic log; convergence
  *emerges* (§8).

A **run** is a declarative manifest — `hc apply -f run.yaml` — reproducible and shareable, same
philosophy as the substrate under it.

---

## §7 · The oracle & the Externality Principle (the keystone)

**The single most load-bearing rule in the fabric (A5).** A Culture converges only against ground truth
that originates **outside both the model and the operator**:

- **External** — tests / a checker / a linter / a benchmark / a metric-vs-pre-registered-target for
  code; a **diverse judge-panel across provider families** for prose (so judges don't share a blind spot).
- **Coordinator-run** — the falsifier is executed by the Conductor/coordinator over a candidate's
  *declared output*; **cells never score their own work**. Receipts are non-mintable.
- **Pre-registered** — the target/tolerance/gate is fixed **before** the run; moving a bar after seeing a
  number is forbidden.
- **Exit tri-state** — `pass` / `gate-fired` (a real negative result) / `error` are never conflated; an
  error or timeout is **INVALID and excluded**, never a zero score that quietly poisons the ranking.

This is slate's Externality Principle and ORRERY-Intercom's discipline, made constitutional. Paired with
**A6 (seeded diversity)**, it is what turns a swarm from a mob into a search.

---

## §8 · Self-organization — enabled, not scripted (A9)

The aspirational apex: Cultures that self-assemble toward a goal with no central script — the ant/anthill,
the *Prey* nanobots, an evolutionary/back-propagating convergence where the collective finds the global
maximum together. hypercell does not *script* this; it supplies the **four ingredients** and lets it
emerge:

1. **A stigmergic medium** — the append-only log + scored artifacts *are* the pheromone trail; cells
   coordinate indirectly by reading/writing the shared environment.
2. **Local rules** — each cell follows a small policy (claim the highest-value unclaimed task; leave a
   scored artifact; prune a dominated peer; advertise capabilities) — no cell holds the global blueprint.
3. **A selection pressure** — the external oracle (§7): the gradient the swarm climbs.
4. **Seeded diversity** — heterogeneous providers/prompts/angles, or the swarm collapses to one voice.

Honest standing: emergence is a **research frontier**, pre-registered as aspirational (HC-10), never
assumed. The fabric's job is to make it *experimentable* and to degrade gracefully to explicit
coordination (a coordinator cell) when emergence underperforms round-robin.

---

## §9 · Cognition — the swappable provider seam (A4, A7)

A cell's brain is a config, not code: `{provider, model, base_url, key_ref, params}`. One **OpenAI-Chat-
Completions adapter seam** covers the field — DeepSeek (cheap-as-dirt), Cerebras (~3000 tok/s), Qwen,
GLM, Kimi, Grok are OpenAI-compatible or reachable via a gateway; Opus and Gemini get thin adapters. A
provider swap is a **config change, never a code change** (HC-6). Because the seam is *per-cell*, a
Culture is **heterogeneous by design** — a Cerebras coordinator directing DeepSeek workers — so the
speed/cost trade becomes a *swarm feature*, assigned by the router per role. A small **local model**
(llama in a pod) is the always-available floor (§10, the island doctrine): no cell may hard-require a
cloud tier to close its loop.

---

## §10 · The substrate & governance

**Substrate:** k3s (§3, L0). Cells default to pooled processes on Runner pods; `--isolate` promotes to a
dedicated pod + PVC. The same image + manifest is the portable artifact (A8).

**Governance (A10) — the primitives that keep a swarm safe and affordable:**

- **Cost governor** — per-run and per-fleet **budget caps with a hard-stop**, and **per-provider
  concurrency caps** (a fan-out of 500 queues; it does not melt the box or blow rate limits). The router
  *is* the economics: grunt → DeepSeek, latency-critical → Cerebras, hard reasoning → frontier.
- **Harm classes (H0–H3)** — `H0` log-only · `H1` fenced-auto · `H2` auto-after-a-cancelable-delay ·
  `H3` operator-always. Cells default read-only/sandboxed; the container boundary is the sandbox; risky
  acts wait for a `command`.
- **Secrets** — provider keys live in the substrate's secret store (k8s Secrets / an encrypted local
  file), injected into cells at instantiation, **never** in cell code or nucleus.
- **Observability** — you command a fleet, so you must see it: `hc top` (live fleet dashboard), per-cell
  logs, the run transcript, a live cost meter. Every headline number is a query, not a vibe.
- **The island floor** — if the network/provider drops, degrade (cheaper/fewer calls, the local pod
  tier); never starve.

---

## §11 · The Conductor & the surfaces — how you command it

You are the **fleet commander** (the Homeworld feel). You reach the **Conductor** (`hcd`) from anywhere:

- **`hc` CLI over SSH** — the primary surface (PuTTY / MobaXterm / SecureCRT): `hc spawn`, `hc run`,
  `hc fleet ls`, `hc top`, `hc logs`, `hc resume`, `hc apply -f run.yaml`, `hc kill`, `hc provider set`.
- **gRPC/HTTP API** — the Conductor's own protocol, so remote/programmatic control works from anything.
- **MCP server** — the fleet's capabilities exposed as MCP tools, so *any* MCP client (a Claude Code
  session, another harness) can drive it — but hypercell never *requires* a proprietary harness (A8).
- **A phone app** — a thin client over HTTPS to the cloud-hosted Conductor: command the fleet from a
  golf course. The Conductor and Medium are pods; hosting them in the cloud gives scale beyond the box,
  always-on availability, and access anywhere — the same artifact, a different substrate.

The commander's verbs stay small: *spin up · give a goal + an oracle · watch it converge · take the
answer.* Everything else the fabric does itself.

---

## §12 · The north star — the core wire & the automation of cognitive labour

*(The application the fabric exists to enable. Earned, never assumed — §14's last rung, gated behind
every falsifier before it.)*

Every organization has a **core wire**: the end-to-end irreducible process from input to output. At each
critical **node** on that wire, a human is the **cognitive glue** — cross-integrating and synthesizing
information that tools already pre-computed and pre-compressed. The same shape appears as a **nested,
fractal inverted-cone "Christmas tree"**: each layer's tip reasons over fully-compressed representations
from below, up to the CEO at the apex. Pre-LLM, only a human could do a tip's cross-synthesis — you could
not script intuition. **An LLM with the right context, role, and structure can now emulate the tip** — so
you *swap the tips*, and because most of an organization is *support-of-support* for those tips, automating
the core wire **cascades**: the second- and third-order headcount collapses behind it. ("AI as the new
UI": a presentation layer exists so a *human* can cross-integrate; remove the human, remove the layer.)

**The core wire is fractal** — the operator's coined term is already KEEL's routing primitive
(`core-wire-step` vs `scaffolding-step`), so it operates at **three scales at once**: the *step* (KEEL
routes it to the right tier), the *cell* (a hypercell **is** a cognitive-glue node), and the *org*
(automate the wire). Depth/scale invariance is the through-line.

**The method is emergence, not hand-tuning (A9).** You do not script the automation. You **throw a fleet
of depth-invariant cells at an organization**, give them the end goal, and let them **auto-discover** it,
find its core wire, and self-organize an automation — forward-and-reverse-solving toward the global
optimum, the way a swarm converges. *"Use AI to solve AI."* This is the strategic use of AI — aimed at the
irreducible cognitive nodes — versus the tactical one (a Copilot on everyone's inbox), and it is why the
fabric, not any single agent, is the product. An organization re-imagined AI-first from first principles
would not have the shape of a human org; hypercell is the instrument for discovering that shape.

---

## §13 · The build ladder (stem-first; each rung independently useful; falsifier-gated)

**Design for the full potential; build the minimal stem first.** Order of construction = order of trust.

| Rung | Deliverable | Pre-registered bar (falsifier) |
|---|---|---|
| **P0 — the stem** | `hcd` + `hc` + ONE cell (d0/d1) on k3s: prompt in → swappable provider → answer out; nucleus persists; `hc resume` after a kill. | HC-1, HC-2, HC-6: provider swapped by config; kill+resume restores the cell; ≤ a weekend. |
| **P1 — the Culture** | `hc run tournament --goal … --oracle … --n 8 --provider deepseek`: spawn N cells → converge plane → champion; `hc top`. **The Homeworld moment.** | HC-3, HC-4: the tournament beats a single cell on a fixed benchmark; seeded-diverse beats identical-N. |
| **P2 — the self-driving machine** | router (MoE) + schedule (UCB) + drive; heterogeneous fleets; the cost governor + harm classes + secrets. | HC-7, HC-8: no self-minted win passes; the budget hard-stop holds. |
| **P3 — Medium at scale + cloud** | pluggable transport (embedded log → JetStream); multi-node k3s → a rented VPS/cluster; the phone surface; COW-fork for MCTS. | HC-5: same image+manifest runs local podman and k3s-VPS identically. |
| **P4 — the depth dial** | d2 resident cells (REEL nuclei) + a d3 brain-cell backend (KEEL-class, over protocol); long-lived specialists. | HC-9: one runtime instantiates hello-world AND brain from the same image, by manifest only. |
| **P5 — self-organization** | free-swarm topology: stigmergy + local rules + selection pressure + diversity; auto-discovery cells. | HC-10 (aspirational): a free-swarm converges without a central schedule, beating round-robin. |
| **The north star** | org auto-discovery + core-wire automation (§12) — **only when the fabric has earned every rung above.** | measured against a real engagement; never asserted. |

**The standing rule:** *stem before swarm; oracle before convergence; persistence before scale; the local
floor before any cloud dependency; a falsifier before any organ.*

---

## §14 · Falsifiers (pre-registered; bars before builds; artifacts to `.hypercellstate/bench/`)

| # | Claim killed if | Bar (pre-registered) |
|---|---|---|
| **HC-1** | the cell primitive is wrong | a single cell takes a prompt, calls a config-selected provider, returns an answer, on k3s. |
| **HC-2** | persistence is theater | kill the box mid-Culture; `hc resume` restores every cell from its nucleus via stable claim-id; **zero double-executions** (idempotency). |
| **HC-3** | the run engine is theater | a tournament with an external oracle beats a single cell on a fixed benchmark; the champion is oracle-verified, never self-graded. |
| **HC-4** | "mixture of agents" is just N copies | a seeded-diverse Culture beats an identical-N Culture on the same goal. |
| **HC-5** | "portable" was soft | the same cell image + run manifest runs identically under podman-local and k3s-on-a-VPS. |
| **HC-6** | the cognition seam leaks | swap DeepSeek↔Cerebras↔GLM by **config only**, no code change; one Culture runs heterogeneous providers. |
| **HC-7** | the Externality Principle is prose | a red-team cell attempts to self-mark a win N ways; **zero** pass without the coordinator-run external falsifier. |
| **HC-8** | the cost governor is decoration | a runaway fan-out hits the budget hard-stop; **no run exceeds its cap**; per-provider concurrency caps hold. |
| **HC-9** | depth is not a dial | the same runtime instantiates a d0 hello-world cell AND a d3 brain-cell from one image, differing only by role manifest. |
| **HC-10** | emergence is a fantasy | *(aspirational)* a free-swarm with stigmergy + local rules + oracle + diversity converges with no central schedule, measurably better than round-robin. |

**House rule (inherited):** pre-register thresholds BEFORE measuring; never move a bar after seeing a
number; decision-grade artifacts on disk.

---

## §15 · Refusals / anti-goals (the discipline that keeps this a fabric, not a toy)

- **No invented wire protocols** (A7) — OpenAI-egress / MCP / the Medium contract / A2A only.
- **No hard dependency on any one provider, any one cloud, or on KEEL/Intercom/REEL/FLOTILLA** —
  interoperate over protocol; import no sibling source (§17).
- **No self-grading convergence** — the oracle is always external and coordinator-run (A5).
- **No pod-per-cell mandate** — the hybrid model; a pod when isolation earns it, not by default.
- **No multi-tenancy** — federation only (A2).
- **No hand-coded org-automation pipeline** — emergence, enabled not scripted (A9); the north star is
  earned, never wired.
- **No cell that hard-requires a cloud tier to close its loop** — the local floor is sovereign (island).
- **No organ with no falsifier** — beauty is not a reason to run (the KEEL/THE_BRAIN discipline).
- **The artifact inventory stays small:** 1 cell runtime · 1 Conductor (`hcd`/`hc`) · 1 Medium · 1 nucleus
  format · 1 run-manifest schema · 1 oracle-contract shape · 1 falsifier suite. If the list grows,
  something snuck in.

---

## §16 · Boundary laws — the sibling constellation

hypercell is sovereign and depends on none of these; each is a reference or an optional peer over protocol.

- **KEEL** (done genome) — a **d3 cell MAY use KEEL as its deep cognition backend** (router/memory/oracle/
  MCP) once KEEL is Linux-ported, consumed over `serve_openai`/MCP. hypercell never edits a KEEL contract;
  the depth dial's deep end is "KEEL-class," the shallow end is a bare API call.
- **Intercom** (×3 variants) — hypercell's **Medium is a de-novo reimplementation** informed by all three
  (canonical bus + `everywhere` insight-scheduler + ORRERY discipline). Intercom is a reference; a
  hypercell Culture MAY bridge to an Intercom bus over protocol.
- **REEL** (memory protocol) — the **nucleus's deep tier is REEL-shaped** (rings + Tape); the shallow tier
  is a cursor+scratch DB. hypercell implements the pattern, not the code.
- **FLOTILLA** (container fabric) — the **swarm sibling**. hypercell borrows its substrate posture, harm
  classes, and wire discipline, but not the full witness/treaty/wager constitution (that is a sovereign-org
  fabric; hypercell is a productivity swarm). A hypercell Culture MAY later run as a FLOTILLA body.
- **THE_BRAIN** (the ceiling) — the **max depth of a single cell** (d3). hypercell does not build the brain;
  a cell *can be* one. The brain is the depth ceiling the dial reaches toward, never a dependency.

---

## §17 · Glossary (one line each)

cell = the atom; a depth-invariant subagent · nucleus = a cell's private persistent memory/identity (its
PVC) · membrane = a cell's comms boundary + injection firewall + capability ad · Medium = the shared
coordination fabric (bus + run engine + stigmergic log) · Culture = a swarm convened on one goal · fleet =
the whole commanded ensemble · Conductor = the control plane (`hcd`/`hc`/API/MCP) · substrate = k3s +
volumes + secrets · role manifest = what turns a uniform cell into a specific agent · depth dial = d0
reflex → d1 worker → d2 resident → d3 brain · stable claim-id = `run/role/index`, the identity a nucleus
binds to · instance-id = one ephemeral process · idempotency key = what makes a resumed act
exactly-once · converge/router/schedule/drive = the run engine's value/placement/allocation/integration
planes · oracle = the external, coordinator-run, pre-registered falsifier · champion = the max-oracle-score
candidate (MCTS best-node) · arm = a named approach the bandit allocates over · seeded diversity = the
anti-mediocrity ingredient · stigmergy = coordination through the shared environment · harm class = H0
log · H1 auto · H2 delayed · H3 human-always · island floor = the local tier no cloud loss can starve ·
core wire = the org's irreducible chain of cognitive-glue nodes (fractal: step/cell/org).

---

## §18 · Closing — the essence, once

One fabric, from one commanded cell to a self-organizing fleet: **cells fan out, results converge, every
convergence is judged from outside the swarm, every cell is a durable identity the substrate merely
instantiates, cognition is rented and swappable while the loop is owned, and the unit of scale is another
sovereign copy of the same small thing — never a bigger one.** Kubernetes taught the industry to run
containers this way; hypercell runs *minds* this way, and demotes Kubernetes to the metal underneath. The
cell is depth-invariant — a hello-world at one end, a whole brain at the other — and the swarm is
scale-invariant — a Culture at one end, an automated organization at the other. The order of construction
is the order of trust: **stem before swarm, oracle before convergence, persistence before scale, the local
floor before the cloud, a falsifier before every organ.**

*Build the stem. Convene the first Culture. Let the oracle start grading — and command the fleet.*

**· v0.1 · 2026-07-15 · C:\hypercell\HYPERCELL_ARCHITECTURE.md · pending operator ratification ·**
