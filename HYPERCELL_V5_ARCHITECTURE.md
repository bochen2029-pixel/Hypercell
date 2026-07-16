# HYPERCELL v5 — the constitution of the fabric
## A sovereign, depth-invariant swarm-compute fabric whose every claim is warranted or labeled, every act is receipted, every dollar is metered at a real price, every command is parsed once and narrated only from the log, no swarm takes credit it did not beat its own null to earn, the oracle grows exactly where the swarm goes blind — and every durable thing it knows is a fold over one append-only log
### v5.0 · DRAFT FOR RATIFICATION · 2026-07-16 · authored by Claude Fable 5 (coordinator + a ten-agent Fable mechanism wave + a six-agent adversarial verification wave, over Intercom) at Bo Chen's commission

> **⚑ STANDING.** This document supersedes the v1 constitution (`C:\hypercell\HYPERCELL_ARCHITECTURE.md`,
> ratified, live P0–P2 code) and the v2 constitution (`C:\hypercell_v2\HYPERCELL_V2_ARCHITECTURE.md`, strong
> law, thin mechanism), and it completes what the v3 mechanism wave began and never finished. **v3 produced
> ten field-level domain papers and no synthesized document** — ten voices, no constitution. v5 is that
> synthesis, verified: the v2 constitutional core kept where right, the v3 mechanism layer assembled and
> cross-checked against the live code, the security/identity/firewall dimension v3 scoped out folded back in
> as first-class, every load-bearing fact re-verified against July-2026 reality, and every organ carrying its
> null and its falsifier. Conformance language is RFC-2119 (MUST / MUST NOT / SHOULD / MAY); a coding harness
> treats MUST items as acceptance criteria.
>
> **The lineage, stated once.** *v1 proved the fabric can run* — a provider-swappable resumable cell, an
> external-oracle tournament, a budget-governed self-driving loop, a killed fleet that resumes exactly-once,
> all live and artifacted (§1, F10/F6/F1). *v2 made it honest* — nothing crosses the Medium naked or
> mislabeled; the conservation law of trust; the growing oracle; the single-cell null. *v3 built the
> machines* — the wire, the nucleus, the run engine, the trust plane, the act plane, the economics plane,
> the conductor, the substrate, each specified to field level — but assembled none of them into a document a
> builder could hold. **v5 assembles the totality and verifies it:** every law carries its mechanism, every
> mechanism its contract, every contract its build slice, every slice its falsifier — and the whole is
> readable as one constitution, not ten stapled papers. The completeness bar is mechanical: *a fresh coding
> session holding only this doc set + the live v1 repo can implement any named organ without inventing
> semantics.* The dominance bar is comparative: *a skeptic reading v2, the v3 wave, and v5 side by side
> concludes v5 keeps everything right, fixes what the wave caught, resolves what it left contradictory,
> restores what v3 dropped, and is the only one of the three that is finished.*
>
> **Epistemic status, marked throughout.** What is *proven* (P0–P2, live and artifacted) is marked LIVE.
> What is *specified and buildable but unbuilt* is marked by its build rung (§14) and its falsifier (§15).
> What remains *vision* — a claim no falsifier can yet reach — is labeled vision and set aside; the
> constitution carries only what a falsifier can reach. The still-aspirational organs are the least
> trustworthy objects in this account, and each names its own bar.
>
> **Sovereignty (the de-novo law, unchanged).** hypercell is its own project, its own contracts, built **de
> novo**. It is *informed by* KEEL / Intercom / REEL / FLOTILLA / THE_BRAIN and the July-2026 industry
> (kagent, Dapr Agents, A2A, MCP, Google Agent Sandbox / `agents.x-k8s.io`, the CNCF pod-per-agent debate)
> and **depends on none of them**. It MAY interoperate over protocol; it imports no sibling source. The
> discipline is stated once and enforced throughout: **adopt semantics, refuse dependencies.**

---

## §0 · The crystallization

The whole document in one line:

> **HYPERCELL v5 = the proven fabric × the warranted claim × the growing oracle × the commanded fleet — and everything durable it knows is a fold over one append-only log.**

Read as five clauses in one breath: *v1 proved the fabric can run; v2 made it earn — nothing crosses the
Medium naked or mislabeled; the oracle is versioned, not frozen, and grows exactly where the passing swarm's
disagreement shows it blind; you command the whole like a fleet of starships, in plain English; and there is
no state anywhere in the fabric that is not reconstructible by replaying the log — kill any process and its
knowledge re-folds from records that outlive it.*

That one-liner compresses two laws. The first is v2's keystone, kept verbatim because five wave-1 agents
derived it independently from five different seats:

> **THE CONSERVATION LAW OF TRUST (A5, the keystone).** *Trust is never minted inside the fabric — it is
> only imported across the fabric's boundary, and every import is priced. And no organ outlives its null.*

Every mechanism in v5 is an instance of it. Grounding imports trust from the world into an answer (a citation
is a pointer to an act-receipt). The oracle imports trust into a score (receipts are non-mintable). An act
receipt imports trust into an effect (reality grades the act, not the actor). The single-cell null imports
trust into *the architecture itself* (the swarm's advantage is measured, never asserted). Oracle growth is
what happens when imported trust runs out of resolution — the passers disagree, the bar cannot discriminate
there — so you import *more* trust at the blind spot by a pre-registered generation bump; you never mint
resolution by fiat. The economics plane is the tariff schedule on these imports; the governor is the customs
house. The mortality clause — *no organ outlives its null* — makes the falsifier discipline a runtime
property: every organ carries its null (§15), and one that cannot beat it is retired — with one exception the
law names explicitly. **The operator is not exempt:** human adjudications are trust imports too, so v5 prices
them (§5). But the operator is the one organ **priced and demoted-by-class when its error bar is wide, never
retired** — sovereignty is priced, not overruled.

The second law is v5's own addition, ruled a full axiom by the kernel seat because the live code satisfies
A1–A12 and still loses its budget meter on resume (F16/G5) — proof that trust conservation does not imply it:

> **THE FOLD LAW (A13).** *Every durable structure in the fabric is a deterministic fold over an
> append-only log. No coordination state lives anywhere but as a replayable projection of records that
> outlive the process holding it.* The spend meter, the registry of live cells, the lineage index, the
> claim table, the escrow counters, the certificate, the null ledger, `hc top`, the viewer — each **is** a
> named fold, not a cache with a backing store. Kill the process; the knowledge re-folds. A structure that
> cannot be recomputed from the log is a bug at review time, not a surprise at crash time.

**HYPERCELL demotes Kubernetes from platform to substrate; identity is the seam** — reached independently by
a prior session, by this design, and by the 2026 industry (F11). Kubernetes taught the industry to run
containers by declaring desired state and reconciling toward it; hypercell runs *minds* that way on **k3s**
and adds the one thing a swarm of minds needs that a fleet of containers never did — a discipline that keeps
the swarm from converging, confidently, on its own shared delusion (F1, lived). v2 added the layer above
identity: **warrant is the currency.** v5 adds the layer beneath state: **the log is the ground.**

---

## §1 · The evidence (twenty-eight lived findings + the accepted 2026 results)

v5 is built on what the running fabric taught us. Each finding is a citation with standing; each v5 organ
traces to one or more. The numbering is a **provenance ledger, not a single author's list:**

- **F1–F12** were minted by the v2 constitution from the v1 build log (`log_notes.md`, Entries 6–34; the
  F-labels are v2's editorial numbering over the log's own entry numbers — an honesty note: the raw log
  contains no "F1…" labels. The source-entry map is: F1←E20 · F2←E23 · F3←E21 · F4←E22/24/28 · F5←E33 ·
  F6←E21 · F7←E12–13 · F8←E29–31 · F9←E33 · F10←E19/28 · F11←E12 · F12←E6 + Intercom `NOTES.md:41`.
  **A collision warning:** the distiller note `_state/notes/lognotes-f-findings.md` numbers the same
  evidence differently (its F3 = 429-burst, not the in-process spoof); **the constitution's F-numbers
  follow v2, not that note.**)
- **F13–F23** were minted across the v3 mechanism wave from adversarial reads of the live code (each a
  `file:line` defect the formal spec now prevents); they are carried in the wave papers' provenance ledgers.
- **F24–F28** were minted during the v5 wave and coordinator-confirmed (rulings in
  `sandbox\_briefing\RULINGS_R1-R12.md`).

### §1.1 · The lived core (F1–F12, from the running v1 fabric)

| # | Lived finding | What it forces in v5 |
|---|---|---|
| **F1** | **Shared blind spot, live.** A 4-cell single-family (DeepSeek) tournament plateaued at 0.9286 on IPv4: every cell used `str.isdigit()` (True for U+0664 '٤'); 3 rounds of cross-pollination could not fix what no cell could see; the external oracle caught it instantly. A later 6-cell roster with sharper wording hit 1.0000 — diversity is multi-dimensional. | Measured, multi-dimensional, enforced diversity (A6); the Divergence Meter; oracle growth; partial-view cross-pollination (§5, §9). |
| **F2** | **429 burst.** The z.ai dev tier rate-limited 3 concurrent calls. | Per-provider concurrency caps + `Retry-After` backoff inside the one metered path (§7). |
| **F3** | **In-process spoof.** A candidate that runs `sys.exit(0)` at import spoofs the oracle's exit code in-process; the answer key sits in the grader's own file, one `open(__file__)` away. | HC-7 closed by two-phase grading + a class-3 sandbox (§5, §11). |
| **F4** | **The substrate is rude.** WSL2 idle-poweroff silently killed k3s; installing docker.io broke k3s (2nd containerd + `iptables FORWARD DROP`). | The Substrate Preflight — verify-and-report per environment, never assume-and-flap (§11). |
| **F5** | **Grounding drift.** The judge panel converged, but producers answered from training knowledge and drifted off-target. | Verb `act`; the grounding dial keyed to oracle executability; answers made of the world (§6, A11). |
| **F6** | **The governor works — barely.** A live budget hard-stop tripped at $0.0006 across 6 steps — a one-call overshoot of a $0.0005 cap. | Reservation/escrow semantics: zero overshoot by construction (§7). |
| **F7** | **Operator fan-in choke.** The operator pasted one long prompt to every session at once and choked on rate limits. | The CommandEnvelope + the F7 coalesce layer (§10); the same debounce on the adjudication channel (§5). |
| **F8** | **The surface that mattered.** What the operator wanted was `hc talk` — plain English, honor the count, stream progress, auto-open the viewer. | `hc talk` is constitutional L4; the honesty rule; the Medium-renderable law (§10). |
| **F9** | **Judges share blind spots too.** The MVP judge panel ran all judges on one provider family. | Cross-weights-family judging is mandatory; family recusal; control probes (§5). |
| **F10** | **Identity design validated.** Crash→resume with exactly-once held live and is artifacted (`p0-stem.json`). A nucleus-PVC marker survived a pod deletion — witnessed in-session, never artifacted; it is lore until the Preflight's F10 re-probe commits `p0-k3s.json`. | A3 upgraded to proven-for-crash-resume; the on-cluster PVC survival is lore-pending-artifact (§8, §11). |
| **F11** | **Independent convergence.** A prior session + the 2026 industry independently reached "k8s demoted to substrate; identity is the seam." | The core thesis is externally validated; A2 stands. |
| **F12** | **The disagreement gate predates its own restatement.** Intercom v0.1.5 (2026-07-14) already scored behavioral divergence — "divergence says WHERE the oracle is blind → grow the oracle" — dogfooded on the exact F1 blind spot; v1 dropped it; it independently converged with the Red-Queen Gödel Machine. | A12 (the bar is versioned); the Crucible; `oracle_gen` on every receipt (§5). |

### §1.2 · The mechanism findings (F13–F28, from adversarial reads of the live code)

Each is a `file:line` defect in the 29-tests-green v1 repo that the formal v5 kernel makes impossible. The
five most load-bearing, each a **direct proof of a v5 law**:

| # | Finding (file:line) | Proves the law |
|---|---|---|
| **F13** | `converge.py:25-28` returns INVALID on `TimeoutExpired` — a candidate that hangs forever is *excluded*, not *gated*: self-sabotage is free evasion. | The exit tri-state's candidate-attribution rule + **two-phase grading** (§5): a single subprocess timeout cannot say *who* hung; only the phase split can. |
| **F14** | `stable_k` counts per-**round** in `topology.py:190` but per-**step** in `drive.py:127` — the same manifest field is N× stricter in one topology, silently, inside green tests. | **One driver, six policy rows** (§9): three loop copies breed semantic drift forever. |
| **F16 / G5** | `Governor.spent` is an in-RAM float rebuilt per `drive()` (`governor.py:39`); crash+resume resets the meter to $0 and the run can spend its cap **again**. HC-8 does not survive resume. | **The Fold Law (A13):** spend is a fold over durable cost records, not a live float. |
| **F17 / G1** | `runtime.py:83-101` — `produce()` lacks the exactly-once guard `ask()` has at `:41`; `resume_pending()` reconstructs a crashed `produce` as an empty `ask`. | The **one-verb-executor** (§3): verb logic is never hand-rolled per method. |
| **F18 / G2** | `transport_local.py` stores 9 of `wire.md`'s 13 envelope columns; `reply_to/priority/origin/idem` are dropped at `post()` with no marker. | Full-envelope round-trip + the **emit/read (Postel) split** and **version-by-epoch-record** (§3, §4). |

The remaining wave findings — **F15** (un-metered `build_cognition` in a surface, `commander.py:116`),
**F19–F23** (carried in the paper provenance ledgers: the wire-registry drift E1, receipts-never-posted E2,
dropped SQLite pragmas E3, the un-versioned corpus G3, Postel-inverted `extra="forbid"` G4, the missing
fleet scope F20, the O(ledger)-per-open nucleus F21), and the five v5-wave mints below — each land a mechanism
in the sections that follow.

**The five v5-wave findings (F24–F28, coordinator-confirmed):**
- **F24** (`topology.py:183-190`) — an all-INVALID round *advances* `stable`: a broken oracle can **converge**
  a run with a verdict. → VALID-only stability + the R% INVALID-rate halt (§5, §9).
- **F25** (`topology.py:148`) — judge-panel cognition runs un-metered even when a governor is supplied (a
  second F15-class leak). → one-metered-path CI conformance (§7).
- **F26** (`base.py:24`) — `CompletionResult.cost_usd` exists but is never populated; adapters receive
  provider cache-token usage and discard it. → truthful metering is *cheaper* than feared; ships with the
  pricebook (§7).
- **F27** (`commander.py:185`) — the deterministic extractor is a *fallback*, not a *cross-check*: a router
  hallucinating `n` over a stated count wins silently (Entry-30's rule 3 is dead in the live code). → the
  Entry-30 scalar cross-check made mandatory (§10).
- **F28** (`nucleus.py:67-82`) — every append does *two* durable writes (JSONL fsync + synchronous SQLite
  commit); the index is a render, so its mirror belongs off the append path. → the async-mirror law (§8).

### §1.3 · The accepted 2026 results (external, re-verified July-2026 — directional, cited with dates)

At matched *dollars* (v5's unit, not tokens), a strong single agent often matches or beats a naive
multi-agent system on closed-world reasoning — the **Data Processing Inequality**: when all task information
is already in context, every inter-agent handoff is a lossy channel. *Under homogeneous agents and uniform
belief updates, debate preserves expected correctness — it cannot improve it.* **Swarms win only with genuine
diversity + an external verifier.** Self-preference bias in LLM judges is measured. **Prompt injection is
architecturally unpatchable** (OWASP 2026; adaptive attacks break >90% of classifier defenses). The
inference layer split from the weights layer — same weights, many hosts, a **~300× posted price spread**
(625× at the extremes), re-verified 2026-07-16. Verifier-based self-improvement (the Darwin-Gödel Machine's
archive of empirically-validated stepping stones; Red-Queen co-evolution's epoch-frozen evaluator with a
holdout and a sealed set — arXiv 2606.26294) converges on exactly the Crucible's growth machinery, and the
Reward-Hacking-Benchmark (2605.02964) measures the F3/HC-7 attack class at **up to 13.9% in frontier models
now** — the sandbox isolation is load-bearing, not theoretical. Each result *strengthens* a v1/v2 bet rather
than overturning it. (Full dated verifications: §13 landscape appendix and each seat's PART E.)

---

## §2 · Axioms (A1–A13): six survive from v1, six sharpen or arrive in v2, one is new in v5

- **A1 — Depth invariance** *(interface proven at d0/d1; d2/d3 falsifier-gated, §15).* The same cell runtime
  spans hello-world → brain, set only by a role manifest that selects a **defaults preset over one field
  space** (§8, `role.md`). Adding depth turns a dial; the runtime never branches on depth into a new type.
- **A2 — Scale invariance; federation, not tenancy; and ceremony scales *down*** *(externally validated,
  F11; extended in v5).* The unit of scale is another sovereign copy — another cell, another Culture — never
  a bigger machine, never a multi-tenant instance. cell → Culture → fleet is one shape, composed. **And the
  invariance runs downward too:** `hc ask "hello"` wakes no oracle, no null, no evidence machinery — one
  metered call and the minimal appends the fabric itself legislates (§10, the degeneracy line-item). The
  fabric's ceremony scales down as smoothly as its swarm scales up; a d0 ask that woke ten subsystems would
  violate A2 as surely as a bigger machine would.
- **A3 — Identity is the seam; a cell is a durable identity, not a process** *(crash-resume PROVEN, F10).*
  The self lives in the nucleus on a volume, bound by a stable claim-id (`run/role/index`, the StatefulSet
  pattern); the substrate instantiates ephemeral bodies. Kill the body, the cell persists; re-instantiate,
  it resumes exactly-once.
- **A4 — Rent cognition; own the loop.** The LLM is swappable rented tissue behind an OpenAI-compatible seam.
  The loop, the memory, the frame assembly, the coordination, the contracts, the keys, the oracle execution,
  and the router are owned. A rented loop is a puppet; only tissue is legal to rent. This is why v5 refuses
  Temporal/DBOS under the drive loop — the loop is the one thing A4 forbids renting, and F10 proved the owned
  version works.
- **A5 — Warrants are non-mintable — the conservation law of trust** *(the keystone; §0).* Trust enters only
  from outside and every entry is priced. No cell grades itself; no answer asserts itself (evidence or an
  honest label, never a bare claim); no act reports itself (reality grades it; the receipt is the
  *executor's*, never the acting cell's); no swarm justifies itself (the null grades it); no oracle moves its
  own bar mid-round; no organ outlives its null; and no adjudicator is exempt — the operator's imports are
  sampled, priced, and demoted-by-class when wide, though the operator alone is never retired. An **organ**
  is any mechanism whose removal would change a receipt.
- **A6 — Diversity or mediocrity, enforced and measured on every grading layer** *(F1/F9).* Diversity is
  multi-dimensional — **weights family** (not "provider": a blind spot follows the weights, not the endpoint)
  × roster × wording × seed — and applies to producers AND judges. The run manifest declares a diversity
  vector per slot; a convergent run with none is refused; diversity is *measured* at round 1, not merely
  seeded. Where a substrate cannot supply a second family (the island floor), receipts carry
  `diversity_debt: true` and the verdict is demoted to synthesis-grade until a second family regrades it.
- **A7 — No invented wire protocols.** Cells speak OpenAI-egress (cognition), MCP (tools), the Medium
  contract (coordination), and A2A only at real federation. A new provider or transport is an adapter;
  nothing above it changes.
- **A8 — Portability is the point; the substrate is rude** *(F4).* One cell image + one run manifest runs
  under podman locally, k3s on a VM/VPS, or k8s in the cloud, unchanged — but the fabric MUST *verify* its
  substrate's assumptions and report, never assume them and flap.
- **A9 — Emergence is enabled, not scripted.** The fabric supplies the four ingredients of self-organization
  and lets structure emerge; it never hard-codes the solution and never makes the north star *depend* on the
  least-proven organ. Free-swarm is an experiment with a pre-registered kill criterion (§12), not a
  load-bearing topology.
- **A10 — Every act is priced and gated.** Cost: every verb metered on the single metering path at *real*
  prices (cache/batch/effort/service-tier-aware, §7), every run and fleet capped with a hard-stop (F6),
  per-provider concurrency caps load-bearing (F2). Harm: every world-touching act carries a class H0–H3;
  H3 always waits for the operator; untrusted execution is class-3 or it does not run. And the swarm earns
  its width: beat the null at matched dollars or stand down.
- **A11 — Answers are made of the world, not of the model** *(F5).* Parametric memory proposes; only external
  evidence disposes. Every claim that leaves the fabric carries its warrant — evidence refs, an act receipt,
  or an honest `synthesis`/`ungrounded` label. Grounding is a dial keyed to oracle executability: where the
  oracle runs the artifact, `none` is legal; where the oracle is a judge panel, cite-or-abstain is required.
- **A12 — The bar is versioned, not frozen** *(F12).* Disagreement among passers marks where the oracle is
  blind; the fabric grows the oracle there by pre-registered generation bumps, anchored by a never-optimized
  holdout. Pre-registration covers the *procedure*, frozen before the run; executing it is not bar-moving.
  The bar is fixed within a generation; boundary cadence is per-loop (§5).
- **A13 — The Fold Law: every durable structure is a deterministic fold over an append-only log** *(NEW in
  v5; F16/G5 prove its independence from A1–A12 — the live code honors trust conservation and still loses its
  meter on resume).* No coordination state lives anywhere but as a replayable projection of records that
  outlive the process holding it. Every fold declares its input filter, and that filter MUST be
  **compaction-closed** (§9, L-FOLD-CLOSURE): a fold that reads a decay-class type is a bug at review time.
  Kill any process; its knowledge re-folds. This axiom is why v5 can be *resumed from any stage* — the
  property this very build was run under.

*(The candidate "results are assets" is a law under §5/§9, not an axiom; the axiom set stays at thirteen. A
new axiom, like a new noun or verb, must clear the §3 admission tests in writing.)*

---

## §3 · The grammar (the closed set) + the admission tests + the layers

**Eight nouns** (unchanged since v1; the definitions are constitutional):

| Noun | Definition |
|---|---|
| **Cell** | The atom: one subagent. Depth-invariant (d0 reflex → d3 brain). A durable identity, ephemerally instantiated. |
| **Nucleus** | A cell's private, persistent memory + identity (its PVC): the ledger (truth) + pluggable renders. |
| **Membrane** | A cell's boundary: its sole I/O conduit, capability advertisement, and the injection firewall (a customs office). |
| **Medium** | The shared coordination fabric: the append-only firewalled log + the run engine + the stigmergic blackboard. Transport-pluggable. |
| **Culture** | A live swarm of cells convened on one goal, under one topology, judged by one oracle. |
| **Fleet** | The whole commanded ensemble — many Cultures + resident cells — the thing you command like starships. |
| **Conductor** | The control plane (`hcd` daemon + `hc` CLI + HTTP/MCP API) you connect to and command. *The Conductor never thinks — the moment plane logic needs cognition, it spawns a cell, so all cognition is metered.* |
| **Substrate** | The container layer everything runs on: k3s + volumes + secrets + sandbox classes. |

**Seven verbs** (v1's six + one): `spawn` · `converse` · `route` (place a subtask on the best-fit cell *and
lane* — the MoE gate, now the economics verb) · `converge` · `persist` (checkpoint a nucleus; snapshot/fork is
a `persist`) · `command` · **`act`** *(the only world-touching verb)*.

**The symmetry that justifies the one addition:** v1 has one *noun* with a dial — the Cell dials depth d0→d3.
v2 adds one *verb* with a dial — **`act` dials harm H0→H3**. Observation (H0) through operator-gated mutation
(H3) is one primitive on a dial, exactly as hello-world through brain is one cell on a dial. Without `act`, the
grammar is closed over the fabric and blind to the world: no v1 verb touches anything outside the Medium, so
F5 (a cell answering from its weights because it *cannot* observe) is the grammar's blind spot made flesh.
`act` is not bolted on — v1's own wire already carried `idem` ("idempotency key for any side-effecting act")
and A10 already said "every side-effecting act carries a harm class." The verb was latent; v2 names it.

### §3.1 · The verbs now have a written spec (the v3 mandate, ratified)

The formal verb semantics — per verb: owner layer, numbered pre/post-conditions, wire records, named
failure modes with tri-state mapping, idempotency scope, cancel semantics, cost attribution,
d0-degeneracy — are ratified as annexed from the v3 kernel paper §2 with the v5 wave's three
sharpenings (converge attribution gains `failed_phase: A|B|null` + differential re-attribution;
command pre-3's extractor law now cites F27 as its live proof; converse's type-ACL cites
identity-firewall.md for the authority behind the ACL). The per-verb prose lives in the owning
contracts; the one-glance matrix is constitution furniture (regenerated under the 17-type registry —
R1's presence merge, `cmd_receipt`, and `command{kind:grant}` applied to the v3 original):

| verb | executes at | emits (Medium) | emits (nucleus) | idempotency key | cancel |
|---|---|---|---|---|---|
| spawn | L3→L0→L1 | presence{phase:spawned·announce}; run-log spawn | genesis / rebind | claim_id (+child: lineage pair) | reap→parked |
| converse | L2 | the envelope | — | (culture, sender, idem) | none (append-only) |
| route | L3 | task, claim (a steal is a competing claim) | — | (task, cell); reservation class | unclaim / supersede |
| converge | L3 (candidates @L0 class-3) | round_open, submission, receipt, verdict | — | (submission_ref, oracle_gen) | round-abandon = apparatus |
| persist | L1 (@L0 volume) | handoff (fork lineage rides the child's spawn records) | checkpoint/seal/fork/parked | (parent_lineage, child_claim); last-wins | none (atomic) |
| command | L4→L3 | command, cmd_receipt{phase:ack·progress·result} | — | cmd_id; (routine, slot) | supersede |
| act | L1→L0→L3 | act, act_receipt, command{kind:grant} | act intent/outcome | effect_scope: instance/lineage/slot | phase-dep: hold yes (H2+H3) · exec no · settle N/A |

Two cross-cutting laws are constitutional here:

- **LAW V-EXEC (F17's fix).** Every verb execution flows through the ONE verb executor:
  `GATE → CHECK-DONE → RESERVE → INTENT(fsync per class) → EXECUTE → OUTCOME → COMMIT → POST-ASSERT`.
  A verb implemented as a bespoke method is a constitutional violation detectable by AST (VERB-1).
  The act pipeline (act.md) is the executor's reference instance; `ask`/`produce` are degenerate
  cases; the executor is the ONE receipt-minting site and the ONE metering-attach point (F25).
- **LAW V-RECEIPT.** Wherever a verb's effect crosses a trust boundary (operator above, world below,
  peer beside), the crossing produces a non-mintable receipt graded by the far side's executor, never
  the initiator (A5's wire form).

### §3.2 · The admission battery, amended and armed

Any proposed feature MUST compile to these nouns and verbs or clear a *written* admission test — the
procedure v1 lacked, which is exactly how its predecessor drifted into bolting on subsystems. A new
**noun** MUST pass N1–N5; a new **verb** MUST pass V1–V3, V4′, V5:

- **N1 identity** — persists across verbs. **N2 irreducible participation** — ≥2 verbs take it
  irreducibly. **N3 non-compilability** — cannot be a field/render of an existing noun without losing
  an invariant. **N4 scale recurrence** — appears at >1 scale. *(carried from v2)*
- **N5 (new):** every instance has exactly one owning principal and one truth-home its state folds
  from. Two homes = split brain; none = ghost. (A13's admission form; it decided the escrow-ledger and
  spend-record homes this wave.)
- **V1 transition** — distinct pre/post-conditions and its own failure modes. **V2 atomic safety
  invariant** — cannot compile to a composition of existing verbs without losing a *safety* invariant.
  **V3 recurrence** — across topologies and depths. *(carried from v2)*
- **V4′ (amended):** the verb requires its own record type on a *constitutional log* — the Medium wire
  **or** the nucleus ledger — and defines receipt semantics wherever its effect crosses a trust
  boundary. (v2's V4 as worded — "needs its own wire type" — refuses `persist`, whose checkpoints are
  nucleus-only by design; a battery that refuses a sitting constitutional verb has no authority.)
- **V5 (new):** every execution is attributable to exactly one budget purpose and can carry
  the canonical `cost{}` field-group (R16 — the six members; tokens and wall time ride as sibling
  measurement fields, never as `cost{}` members). A verb that cannot be metered is inadmissible. (Live proof twice over:
  F15, F25.)

**The admission FILING (procedure, law):** a written filing `{candidate, driving capability,
best-compilation attempt written by the PROPOSER, the invariant the compilation loses (or "none —
compiles"), the falsifier demonstrating the loss}`. The proposer argues against their own candidate
first; the ruling is a Medium record. No filing, no seat. The battery itself versions with the
constitution; changing it is a constitution-MAJOR event with written rationale.

**The compilation precedents (v2's table, still governing):** grounding = `act`@H0 + `evidence[]` refs
(*a citation is a pointer to an act-receipt*); grading = the receipt-producing phase of `converge`/`act`
(a free-floating `grade` verb invites the self-scoring A5 exists to kill); oracle growth = a standing
Culture + persisted artifacts + Conductor-side `converge` machinery under A12; fork/MCTS-over-state =
`persist` (atomic COW snapshot) + `spawn --from-snapshot` with `forked_from` lineage; memory
consolidation = a scheduled `persist` Step refreshing a render; cells-spawn-cells = a `task` addressed
to the Conductor + a Conductor-executed `spawn` under the attenuation gate; economics = `cost` fields +
the governor + `route`; federation = the same verbs over a different Medium transport binding +
Membrane policy; ledger anchoring = a periodic `converse` posting the ledger head hash; the NL
commander = `command` semantics with the Conductor queue debouncing (F7/F8).

**Standing rulings (v5 wave, precedential):** `act_receipt` is first-class and **executor-minted,
never acting-cell-minted** (type = ACL key; fold filters must be type-expressible; A5: no act reports
itself — cell-mintable "own-act" receipts would be the F3 spoof one level up); `cmd_receipt` is
first-class (certificate folds and command-queue folds are different constitutional folds;
phase-dependent durability), subsuming the once-proposed `progress` type as
`cmd_receipt{phase:progress}`; **the registry counts 17 and the count is true** (wire.md carries the
table) — and the 17 has a shape: *the fabric's three trust boundaries each carry their own
non-mintable receipt type — `act_receipt` (the world below), `cmd_receipt` (the operator above),
`receipt` (the bar) — three receipt planes, three types*; `spend` refused as a type (v2 §7's render
clause upheld against the v3 econ paper's quiet mint; escrow truth-home = the conductor's own ledger,
attribution rides the `cost{}` field-group on records already crossing); `wait`/`wake` refused as
verbs (bus reads mint no trust, cross no boundary); `migrate` refused (compiles to command + persist +
spawn over epoch records); a champion/artifact **library** refused as noun (it is the canonical
render — fold over four logs); service cells (router/intake/synthesizer/adjudicator/grower) are
cells, and *any* future "the-Conductor-needs-to-think-here" proposal must arrive as a metered service
cell (V5 makes the alternative inadmissible).

### §3.3 · The layer law (three clauses + the composition root)

```
L4 SURFACES · L3 CONDUCTOR · L2 MEDIUM · L1 CELL · L0 SUBSTRATE
strata: common/ (types, ids, clock, protocol interfaces) · cognition/ (tissue adapters)
```

- **C1 — imports point down, strata excepted.** Strata import nothing but `common`; layers import only
  strata and strictly lower layers' public interfaces.
- **C2 — verb ownership.** Each verb has exactly one executing layer (the matrix). Surfaces compile
  intents to CommandEnvelopes; they MUST NOT call L1 constructors, L2 `post()`, or L3 engine functions
  directly. Live corpus of violations (the CI regression set, 12 sites): `cli.py:16,117,156,184,206`;
  `commander.py:17,44,172,182,208,240`; `api.py:17`.
- **C3 — dependency inversion at the cell/Medium seam.** L1 never imports L2; cells converse through an
  injected `common.protocols.MediumClient`. The import DAG is compile-time knowledge; runtime message
  topology is separate.
- **The composition root (new, closing a measured hole).** Exactly one named process-shell module
  (`entrypoints/hcd.py`; `hc --embedded` reuses it) MAY import across layers to WIRE — instantiate and
  inject — never to call logic. `conductor/daemon.py:16` today loads `hypercell.surfaces.api:app` by
  string: a runtime L3→L4 edge invisible to import analysis. The root legalizes wiring in one audited
  place and nowhere else.

The trust plane, act plane, and economics plane (§5–§7) are not new layers — they are *disciplines that
ride L2/L3*; "L4" throughout this document means the surfaces layer above.

**Enforcement (LAYER-1, upgraded):** the AST walk checks C1's allowed-import matrix and C2's
executor-only rule over ALL `Import`/`ImportFrom` nodes *including function bodies*, PLUS a string-
reference scan (uvicorn targets, `importlib.import_module`, entry-point tables) resolved against the
same matrix, root exempted for wiring only ("no logic call sites in the root"). Falsifier: any
forbidden edge — static, lazy, or string-loaded — fails CI.

---

## §4 · The wire — two boundaries, one envelope, seventeen types, three receipt planes

The fabric has exactly **two live trust boundaries** — the **operator above** (`command` in,
`cmd_receipt` out) and the **world below** (`act` out, `act_receipt` in) — plus **the bar between**
(`receipt`: the oracle's grading), and a third boundary that inherits their shape at real
federation only (`origin=external`, or refused). Every live crossing is enveloped and receipted.
This is the structural expression of the conservation law: warrant enters only at a boundary, and
every crossing is priced.

**The envelope.** Sixteen fixed columns (v1's thirteen + `corr`, `mentions`, `hash`), two columns
reserved with pinned semantics (`sig` — excluded from the leaf, signs it; `redactions` — inside the
leaf), per-field assigned-by normative (`contracts/wire.md §2`). Four wire laws:

- **L-ORDER.** The culture is the ordering domain; `seq` is strictly monotonic and dense at post
  within it; `priority` MUST NOT reorder delivery. Cross-culture order is undefined.
- **L-CLOCK.** `seq`, `ts`, `hash` are Medium-assigned; cells MUST NOT supply them. `ts` is
  informative; `seq` is normative.
- **L-ASSIGNED-BY-IS-TRUST-INPUT.** Firewall trust tags MUST derive only from Medium-assigned
  fields, the ACL fold's verdict, and the ingress channel class — never from sender-declared
  fields (`sender`, `origin` are declarations until the identity ladder authenticates them;
  identity-firewall.md owns the derivation rule).
- **Liberality, both directions.** Receivers MUST ignore unknown types and MUST preserve unknown
  fields; emitters mint only registry types and schema fields (`x-*` excepted). A new
  instruction-bearing type is always a wire MAJOR.

**The registry counts seventeen, and the count is true** (wire.md §3: one table binds every type's
ACL + durability + retention — "forgot to classify" is unrepresentable). `announce`/`depart` and
the live drift (`spawned`/`synthesis`/`judgment`) merge into `presence`/`verdict{kind}`/
`receipt{check}`; `act`, `act_receipt`, `cmd_receipt`, `oracle_gen`, `oracle_gap`, `compact` join.
**Three receipt planes mirror the boundary map:** `cmd_receipt` (operator boundary;
conductor-only), `act_receipt` (world boundary; executor-only — **no act reports itself**, the
acting cell can never mint one), `receipt` (the bar; conductor-only). Each is non-mintable by the
party it grades; overloading any onto another would make constitutional folds body-parse-dependent,
which violates type-expressible fold closure.

**Non-mintability is enforced staged, with one transport-neutral core.** The client gate refuses
ACL-violating posts fail-fast; the invariant is **void-at-fold**: a privileged record smuggled past
any gate exists as bytes but is VOID as its type in every constitutional fold, and `verify()` names
it. Stage 1b adds ed25519 signatures on privileged payloads keyed off the SAME ACL table (identity
ladder triggers and key custody: §13, `contracts/identity-firewall.md`).

**The chain.** Every culture's log is hash-chained (canonicalization is JCS, RFC 8785, throughout):
`leaf = sha256(JCS-canon(envelope sans
hash/sig))`, `hash_n = sha256(raw32(prev) ‖ raw32(leaf))`, genesis constant domain-separated and
chain-construction-versioned (`hypercell/medium-chain/1`), the same construction as the nucleus
ledger — one verifier, two logs. The Conductor's fsync'd **anchor log** checkpoints every D-gold
record and every compact record: tamper-evidence with an external trust point, the honest answer to
rented-fsync durability, and the second home the fsync-diverse-home law demands.
**L-REDACT-BEFORE-CANON:** the redaction hook runs before canonicalization — **the chain never
witnesses a secret**; `verify()` never needs one.

**Three constitutional laws over the wire** (v2's warrant laws, carried whole — they ride wire
types; their grading mechanisms live in §5 and §6):

- **L-NO-NAKED-CLAIMS.** In a grounded-mode run, a `submission` whose `evidence[]` is empty is graded
  `unwarranted`. The asymmetry that teaches honesty: an honest `ungrounded: true` claim is survivable
  (capped score); a *fabricated* warrant (digest mismatch, non-witnessed ref, non-entailing quote) is
  fraud — a gate plus a durable stain in the fleet registry. **Lying about evidence MUST always be
  strictly worse than admitting its absence.** (The title's "warranted" means exactly this honesty
  law: nothing crosses naked *or mislabeled*; an honest absence-label is a valid warrant.)
- **L-HONEST-VERDICT.** Verdicts are typed `verified` (oracle-gated; carries receipts + `vs_null`) or
  `synthesis` (fanout; carries evidence, makes no champion claim). A surface MUST NOT render a
  synthesis as verified. And `verified` certifies **survival of a named falsification procedure,
  never truth** — conservation of trust conserves provenance, not quality, which is why the operator
  itself is priced (§5).
- **L-NULL.** Every convergent run's arm-zero is one strong cell at matched production dollars;
  `verdict.vs_null = {null_score, null_usd, margin_production, margin_invoice}` (the two units §5
  mandates, so the swarm is never flattered in the unit that reaches the operator); a swarm that
  cannot beat its null stands down (withholds *credit*, never the answer) and the router's economics
  learn from the receipt. (Scoped to tournament/MCTS/drive/fanout; the pipeline null is one cell
  running all stages sequentially at matched budget; map-reduce, having no convergence, carries no
  null.)

---

## §5 · The trust plane — the oracle, its judges, its growth, the null, and the operator

*(Field-level detail: contracts/oracle.md v5.0. This section is law + mechanism-by-name; it never
duplicates the contract's schemas.)*

**§5.1 The Externality Principle and the conservation law (A5, intact).** Trust is never minted
inside the fabric — it is imported across the boundary, and every import is priced: executable
ground truth, disjoint-authority adjudication, the operator's word (§5.7), dated external
artifacts. A Culture converges only against ground truth from outside both the model and the
operator's unexamined belief: **external** · **coordinator-run** (cells never score their own
work; receipts are non-mintable, conductor-only) · **pre-registered** (stack and bar frozen at run
open) · **exit tri-state** honored. And **no organ outlives its null** — every organ in this
section carries its null and its falsifier bar in §15.

**§5.2 Two-phase grading (TP-1/TP-2 — the HC-7/F3/F13 closure).** Candidate execution and oracle
grading MUST run in separate trust domains: phase A executes the candidate in its harm-mapped
sandbox over case *inputs only* and emits a behavior artifact; phase B grades artifacts with no
candidate code loaded, writing a runner-named report file — candidate stdout is never a grading
channel, and the answer key never enters the sandbox. Attribution is structural, never content
inspection: phase-A failures (crash, hang, kill, malformed artifact) are the candidate's — a
scored miss (*gate*), so self-sabotage is not free evasion (the live code violates this today:
`converge.py:25-28` returns INVALID on timeout — F13); phase-B failures are apparatus — INVALID,
retried, counted against nobody's arm. Two guards close the residual channels: **differential
re-attribution** (a phase-B failure selective to one candidate's sealed artifact re-attributes to
that candidate) and the **availability quarantine** (≥2 consecutive apparatus-INVALIDs pause the
arm, score-neutral, pending reconciliation). A run whose INVALID rate exceeds its pre-registered
`R%` (manifest field, default 25%) MUST halt `oracle-sick` rather than converge on the minority
that graded.

**§5.3 The oracle is a stack.** Named checks — `unit` (executable), `grounding` (the evidence
gate over act-plane verdicts, dialed `none|sampled|required`, reporting domains-per-claim and
trust-floor status in the certificate), `panel` (judged classes), `probe` (the Divergence Meter
feed, scoring: none) — with a pre-registered gates-lexicographic aggregate: no score can buy back
a fired gate. Per-case FAIL detail feeds Pareto-prune and growth targeting under three leak
constraints (reported-only, both-clause domination, gen-scope). Prose rides the same contract via
`harness.none`; the v1 `judge-panel` mode fork is repealed.

**§5.4 Judge panels that stay honest (F9 mechanized).** One numbered algorithm
(contract §6): cross-weights-family roster built from the SIGNED pricebook with
quorum-after-recusal solved at build time; family recusal computed by the runner, invisible to the
judge, SUSPENDED only under a declared diversity debt (where the debt demotion to synthesis-grade
already governs); blinding with per-judge order randomization and both-ways pairwise at promotion
ties (a flipped verdict is discarded); control probes seeded every panel round — golden + flaw —
minted only by a mechanism strictly more trusted than the panel they calibrate (TP-3), with the
champion→control disjointness rule: a panel-certified champion MUST NOT serve as a control in its
own class without one disjoint re-adjudication; the abstain floor (honest abstention scores 0.3;
fabrication scores 0.0 by construction — good > honest-abstain > confident-wrong, enforced
arithmetically outside any judge); trimmed-median aggregation with FAMILY-level dissent (two
same-family judges agreeing is one voice; a single-family panel is contested BY FIAT); the
verbosity guard (score↔length correlation measured once ≥20 gradings, flagged never auto-adjusted);
judge lifecycle counted→probation→ejected on deterministic or adjudicated controls only, every
ejection a receipt. `tier: screen` receipts MUST NOT seat a champion, post a verdict, or trigger
ejection. Judge-lane identity is attested twice: the signed `weights_family` declaration AND a
runtime canary; a mismatch de-rates the lane's diversity contribution to zero.

**§5.5 Oracle growth — the Crucible.** Behavioral disagreement among *passing* candidates never
says who is right; it says where the oracle is blind — so grow the oracle, not the winner's crown.
The **Divergence Meter** (one instrument, three duties, formal metric D over canonicalized
behavior on the probe corpus): D1 growth trigger (champion passed ∧ D > ε ⇒ not converged; top
disagreement inputs enter admission), D2 consensus-poisoning tripwire (divergence collapse WITHOUT
score improvement ⇒ quarantine the round, re-seed — the score guard separates herding from
victory), D3 diversity floor at round 1, measured not proxied, else refuse-to-swarm. Probes never
score and probe results never reach producers — the Goodhart surface is zero by construction.
**Case admission** is a six-state machine whose load-bearing guard is the CANDIDATE-BLIND clerk (a
case is admitted because the spec covers it, never because a champion fails it), followed by
persistence probing, then **disjoint-authority adjudication** (executable → disjoint-family panel
shown anonymized behaviors with NO class sizes and NO champion marker (majority cannot launder
consensus into ground truth — F1) → operator); genuinely-silent specs mint AMBIGUOUS spec-bug
reports — the swarm's disagreement finding holes in the operator's own spec. **Generations** are
append-only directories; every receipt cites `oracle_id@gen#digest`; scores are comparable only
within a generation; answer-runs grow at round boundaries, the Crucible at epoch boundaries;
regrades are phase-B-only over cached behavior artifacts (the behavior-artifact economy: one
artifact serves grading, divergence, admission, and regrades). Wrong cases exit only via
operator-SIGNED errata plus a regrade round. The **two-layer gaming detector**: per-generation
auto-holdout (reported only as an aggregate) + the operator **sealed set** (hash-committed,
off-fabric bytes, journaling-suppressed sealed-runs, one scalar per epoch) with the pre-registered
**halt law**: archive score rises while sealed score falls ⇒ halt, champion pointer rolls back
(append-only; a pointer move), minting freezes, resume is an operator-signed command. The **oracle
library** compounds per task class (identity = the L0/L1/L2 backoff hierarchy) as the bar-side
render; champions, syntheses, and certificates accumulate as the asset-side render — ONE on-disk
tree, TWO renders over the same R-forever records, two keys (L1 bar / L0 asset). July-2026
external validation: RQGM's frozen epochs + holdout + sealed sets converge on this design
independently; 2026's reward-hacking incident record (Terminal-Bench, RHB, the SWE-bench
contamination audit) is the attack class TP-1 + the sealed set close (§PART E).

**§5.6 The single-cell null (arm-zero).** Every convergent run records its null per the
class-lifecycle NullPolicy: **unsettled classes run the matched null** — one cell, the strongest
single weights family pre-registered per class (operator pin or dated external ranking artifact,
never chosen by the machinery under audit), a protected arm OUTSIDE UCB allocation, its
matched-dollar reservation taken at run open before any swarm arm dispatches, running the
identical loop (operator's wording, union of roster tools, same grounding, same generations);
**settled-calibrated classes run the floor null** (inline arm at a protected floor reservation)
plus matched replays at the audit rate. Accounting is dual-unit: `vs_null` publishes lift at
matched-production AND matched-invoice (marginal grading charged per arm via receipts; fixed
apparatus excluded) — the swarm is never flattered in the unit that reaches the operator. **The
null-flip law (ONE predicate, cited by NULL-1 and ECON-8):** per class over the trailing k=20
window, ≥ m=5 audited rows with median matched-invoice lift ≤ 0 ⇒ the class default flips to
single-cell + verifier (overridable; re-armed on roster change). Meta-guard: a null that never
wins anywhere is a strawman — audit parity, operator-blind; a swarm that never wins is HC-3′
failing at scale, and the constitution publishes it.

**§5.7 The operator is an organ (priced, never retired).** Every trust cycle that escapes the
machinery terminates in the operator — adjudications, errata, sealed keys, golden exemplars,
generation promotion — so the operator's imports are priced like every other boundary crossing:
(1) `k%` (default 10%) of operator adjudications receive one blind disjoint second adjudication,
and the published disagreement rate (Wilson upper bound) is an `hc top` field; (2) the
adjudication channel carries F7 discipline — coalesce by input-class, batch at round boundaries,
a mint-escalation cap, a latency budget beyond which the fabric degrades honestly to
converged-with-residual, never guesses; (3) the epoch **recall drill** re-adjudicates sampled
library cases AND the operator's own curated statutes (sealed keys, golden controls) under fresh
disjoint authority — a failed re-adjudication auto-flags errata and suspends the statute pending
operator-signed correction; (4) **provisional-while-wide**: while a class's published
operator-disagreement rate exceeds its pre-registered ceiling, operator-minted cases enter
`provisional` — graded, reported separately, NOT compounded into the library — until confirmed. A
demotion of default, never a retirement: nothing overrules the operator; the fabric merely stops
compounding on unconfirmed imports while the error bar is wide.

**§5.8 Convergence certifies, in one recomputable-from-the-log sentence** (contract §5.4): oracle
generation + digest, champion + score + stability, residual divergence on spec-covered probes,
escalated ambiguities, family dissent, verbosity-r, citation precision across d domains with
trust-floor status, lift vs the null at matched-invoice (and matched-production), INVALID rate vs
R%, operator-import status (confirmed/provisional + rate vs ceiling), spend by purpose. A
permanently-dissenting panel closes `verified-with-residual` at the contested cap, dissent
verbatim. Everything not probed is in the residual, listed, on purpose.

---

## §6 · The act plane — the one world-touching verb, its customs house, and the warranted claim

`act` is the ONLY verb that crosses into the world (§3 grammar; admission V1–V5 passed — V5 metered standing:
every act attaches `cost{}` under `purpose: tool`). v2 declared *"nothing crosses naked"*; this section is the
customs house built: one pipeline, one receipt lifecycle, one locator scheme, one arithmetic that makes honesty
dominate fabrication, and one annex where every tool's security-relevant facts live. The fabric's two live
trust boundaries — the operator above, the world below — get the same treatment: enveloped, receipted, priced.

### 6.1 The pipeline (law: no second path to the world)

Every act traverses **GATE → ESCROW → EFFECT-RESERVE → JOURNAL(fsync) → EXECUTE → RECEIPT → SETTLE**
[ACT §6.0]. The executor is the reference instance of the **one-verb-executor** pattern (kernel §3): the F17
defect class — one verb carrying a guard its sibling lacks (`ask()` vs `produce()`, `runtime.py:41/83`) — is
killed structurally, once. A tool called outside the pipeline is a LAYER-1 violation (AST-checked). Refusals
are receipts too: every REFUSE posts `act_receipt{exec, refused, reason}` — the closed reason enum is
[ACT §3]. **Degeneracy (law):** Conductor round-trips per act = 0 at H0, 1 at H1+, 2 held; `hc ask` with no
tools touches none of this plane.

**The gate** [ACT §6.1] MUST evaluate, in order: profile∈role.tools → args schema + credential-pattern refuse
→ derived harm (`harm_derived := profile.harm_floor ⊔ shape(args)`) → **no-silent-promotion: declared <
derived ⇒ REFUSE** (the wager must be cell-authored; promotion would mint an H1 expectation the cell never
authored) → harm ceiling → egress allowlist → H1+ warrant kit (idem ∧ effect_scope ∧ losable expectation) →
**trifecta step: an act that would COMPLETE {private_data, untrusted_content, external_comms} for its cell is
REFUSED** (`reason: trifecta`) unless the operator waiver policy applies (§13; the cell's acquired-trifecta
state is a fold over its own exec-ok receipts — ingress re-evaluation is a log query, not a monitor).

**Ordering laws.** Effect-reserve precedes journal (a reservation is cheap to abandon; a journaled loser needs
compensation). **fsync-before-effect** (MUST): the act record is fsynced in the actor's nucleus before the
effect executes — a buffered-then-lost act record loses its idempotency evidence and double-fires on resume.
The live nucleus already conforms (`cell/nucleus.py:67-70`); the nucleus fsync is the hard gate (`pending()`
reads it on resume); the Medium copy is at-least-once, idem-deduplicated, re-posted on recovery.

### 6.2 The harm dial H0–H3 (A10)

- **H0 — observation; the warrant kit waived; a *declared-read-only capability class*.** Two legs, one
  predicate table [ACT §6.2]: generic transports (cell composes the request) obey the structural law —
  GET/HEAD, no body, no cell-scoped credentials, no session state; profiled adapters (fabric composes the
  request) are H0-certified at profile admission — cell args are query content only, credentials adapter-held/
  read-scoped/executor-injected/invisible to the cell, endpoint pinned. Harm grades the cell's causal surface,
  not the adapter's plumbing. No cell ever declares its own floor. **H0 ≠ exfil-safe (law):** H0 grades
  mutation; a cell-composed GET URL is an egress channel (the EchoLeak class) — exfiltration lives on the
  trifecta plane via the profile's `exfil_channel` fact [ACT §10.2].
- **H1 — execute → receipt.** The default world-write tier: idem + losable expectation + effect scope +
  fsync-before-effect + non-mintable receipt + settlement. One Conductor round-trip; MUST stay this cheap.
- **H2 — auto-after-a-cancelable-delay.** The hold is a durable, visible, cancelable MESSAGE (journal precedes
  hold), carrying a `summary{}` for join-free queue rendering. **Dead-man clause:** the countdown runs only
  while cancellation is genuinely possible — proof-of-notification = an INTERACTIVE-class surface's read
  cursor passing the hold record (headless clients and the mute viewer can never satisfy it); no proof by
  `until − grace` ⇒ the act parks as H3. In any unattended context every H2 act enters HOLD directly. The
  second gate (post-hold statics re-run) is authoritative.
- **H3 — operator-always.** Park until `command{kind:grant, corr:act_id}`: grant references a JOURNALED act
  (args are hash-fixed before authorization), expires (default 24h ⇒ `exec/refused/grant_lapsed` — a
  never-executed act cannot reach settle phase), single-use, consumed at the registry's hold→exec transition.
  Stage-1b: grants are ed25519-signed with the operator key held OFF-BOX — unattended H3 impossible by
  construction (§13).

### 6.3 Scoped exactly-once (A3 × the fork dimension)

`effect_scope` names the dedup key: `instance` (claim, step — re-fires per fork branch, by design) ·
`lineage` (lineage_root, effect_id — set-once across the whole fork tree; the H1+ default) · `slot`
(routine, scheduled slot — missed slots are not pending). `effect_id` is a SEMANTIC hash — RFC-8785-canonical
effect-significant args only — so concurrent fork siblings compute the same key and cosmetic differences
cannot evade dedup [ACT §7.1]. The effect registry grants execution by **atomic insert-if-absent
reservation** — reserve-then-execute, never consult-then-act (TOCTOU closed); the losing sibling receives
`refused/duplicate_effect` WITH `duplicate_of` and shares the winner's evidence. Registry and lineage index
are Conductor **folds** over D-gold records, rebuilt from the log on start (A13). Crash behavior is specified
per window W0–W5 + W3h with one irreducible truth: between execute and receipt only the WORLD knows — which
is why **every H1+ profile MUST carry an H0 reconcile probe** (admission-refused otherwise), and resume runs
**reconciliation, never blind retry**: hold-check → probe → `ok`/`invalid`/park [ACT §7.4, §8].

### 6.4 Wagers and settlement (A5: reality grades the act)

Every H1+ act carries a **losable expectation**: check ∈ resolver registry, non-tautological (expected-set ≠
codomain), independent of the actor's assertions, windowed. Settlement is Conductor-side registry logic
(cognition-free; "the Conductor never thinks" holds); late checks count only for monotone observables;
`on_miss` compensation is a NEW act through the full pipeline — never an implicit rollback. The wager ledger
(fold over settle receipts) is observability, never auto-kill: miss-rates render in `hc top`; a role's H2
delays MAY scale with its miss-rate [ACT §4].

### 6.5 Evidence and the warranted claim (A11 mechanized)

One URI scheme for every warrant: `medium://` · `nucleus://` (audit channel only; factual register only) ·
`act://` · `https://…#sha256=` · `file://…#sha256=` — hop limit 3, digest verified per hop, unknown scheme =
structural fail [ACT §5.2]. **Witnessed retrieval:** the Membrane hashes every tool call + response into the
ledger at retrieval time — an https ref with no witnessing act in the poster's own receipt set is a naked
claim; you cite what you fetched, not what you remember. **A search snippet is context, never support**
(fetch-to-cite — the F5 drift killer). Three detector tiers with three rates: forged `act://` refs die
structurally (100%, `exists()` at post-gate); digests sample at ρ=0.2 (100% at champion promotion; 100% for
stained roles); quote-entailment is judged at p@k. Staleness demotes to context; truncation supports only the
retrieved prefix. Grounding certifies **provenance, never source truth** — `source_diversity: n` MAY require
≥n independent domains for load-bearing claims, and the certificate reports the domain count per material
claim.

### 6.6 The grounding dial and the honesty arithmetic (L-NO-NAKED-CLAIMS)

The dial has three registered positions — **`none | sampled | required`** — bound at intake by task class
(executable ⇒ none; judged+closed ⇒ sampled; judged+acquisitive ⇒ required = cite-or-abstain; "cite sources"
forces required); a role may raise its floor, never lower [ACT §9.1]. The asymmetry that teaches honesty is
ARITHMETIC, pre-registered per oracle generation:
`0 = fabricated < abstain_floor (0.3) ≤ cap(honest ungrounded) < 1 = cap(grounded)` — lying about evidence is
always strictly worse than admitting its absence. Fabrication (digest mismatch, forged ref, quote-not-in-
source, non-entailing quote) gates at score 0 and mints a durable **stain**: all-digest-check until 3 clean
runs; a second stain quarantines the role from `required` runs. The grounding validator is deterministic
Conductor code emitting a StackReceipt gate row; entailment is the panel's; the seeded-fabrication fixtures
double as panel control probes (GROUND-1) [ACT §9].

### 6.7 The tool layer (the annex, the seam, the leases)

Every tool is a **profile row in ACT Annex A** — one registry carrying, per tool: args schema,
effect-significant fields, harm floor, H0 certification, `credential_carrier` + the scrub law (receipt
provenance MUST NOT carry credential components — `provenance.scrubbed`), `exfil_channel`, the **trifecta
booleans** (fields here; semantics §13), the mandatory H1+ reconcile probe, pricing lane, isolation class
[ACT §10.2]. The executor is an MCP client (pin: **2025-11-25 stable**; the 2026-07-28 revision is adopted at
the first maintenance window after GA); builtins present the same shape; rented adapters mount behind the same
gate/receipts/metering with zero new schema. **No provider-side tool execution** — server-side search or
code-interpreter bypasses egress, provenance, metering, and receipts; all tools execute through the membrane
or not at all. Tool results enter frames as **trust-tagged DATA blocks carrying their `act://` ref** —
structural provenance at frame-assembly time, never string-wrapping (§13). Metering: every act reserves its
pricebook worst-case and commits actuals; no computable worst-case ⇒ unreservable ⇒ refused; **high-rate H0
lanes draw down `econ.lease()` micro-escrows** (fleet-safe: the quantum was reserved; worst within-lease
overshoot = one quantum per cell, printed and drilled) [ACT §10.4].

### 6.8 Failure modes (named; every one carries a drill in §15)

gate bypass (verb-executor + LAYER-1 AST) · receipt minting by the actor (type-ACL + VOID-AT-FOLD; HC-7-v2
attempt 8) · silent promotion (gate d) · journal loss (fsync-before-effect) · double-fire across forks
(lineage keys; CELL-4/NUC-6) · orphan reservation (lease TTL) · un-cancelable H2 (dead-man) · stale grant
(grant TTL) · tautological wager (losability battery) · resolver-down (late-check law) · blind retry
(reconciliation) · forged/stale/partial evidence (three detector tiers) · snippet citation (fetch-to-cite) ·
fabrication (honesty arithmetic + stains) · credential leak via receipts (carrier scrub; SEC-8) · trifecta
completion at runtime (gate h) · ceremony bloat (degeneracy law + GX-2).

### 6.9 Security seams (constitutional pointers; mechanism in §13 + ACT §12)

The act plane consumes from §13: adapter-secret custody + the redaction pattern set; egress realization;
grant signing + the off-box operator key; the act_receipt ACL row + Stage-1b signature ratchet; trifecta
boolean semantics + waiver precedence + taint propagation; frame trust-tag taxonomy. It provides to §13: the
tool-profile annex as the single home of tool security facts; the acquired-trifecta fold; scrubbed provenance;
the H0 certification predicate; ACT-GATE-1 supplying HC-7-v2's attempts 7–8.


---

## §7 · The economics plane — one plane: PRICE → DECIDE → ENFORCE

v1 scattered economics across three mechanisms that never exchanged a bit — the router (no price
term, `router.py:26-31`), the UCB1 scheduler (counting *pulls* against a ≥300× posted price spread,
`schedule.py:27`), and the cost governor (whose hard-stop leaked: the call that crosses the cap always
completes, `governor.py:48-53`; whose meter dies on resume, `governor.py:39`; and whose path two organs
simply bypassed — the commander at `commander.py:116`, the judge panel at `topology.py:148`). v5
collapses all of it into one plane inside the Conductor over one **spend ledger**. The full field
schemas, the seed pricebook, and the escrow protocol are `contracts/pricebook.md` v5.0; this section is
the law and the algorithms.

### §7.1 · PRICE — the pricebook

The pricebook is a **signed, versioned artifact** (`pricebook.yaml`) that prices **SKUs** —
`weights@host/service_tier` — because a service tier changes *unit price* on identical weights
(July-2026: fast 2×, priority 4×, flex 0.5×), and because identical weights on different hosts carry
different prices (the same open model sells at up to 4× first-party sticker) and different cache
economics (the same weights' cache-read multiplier spans 0.02×–0.5× across hosts). A **lane** =
`{sku, effort, cache_mode, batch}` modifies counts and multipliers over one SKU, never unit prices.

Laws (MUST):
- **Every row is dated or does not parse** (`as_of`, `source`, `verified` mandatory).
- **Freshness-pessimism**: stale rows price *upward* (`stale_mult`) at estimation time — a lane never
  gets cheaper by neglect; a lane past `refuse_after` is refused with the refresh command named.
- **Unknown lane ⇒ REFUSED(unpriced)**, loudly, with the fix named; the override prices at book-max ×
  1.5 and prints it. (Repeals v1's silent `(0.5, 1.5)` guess, `governor.py:45`.)
- **Scheduled change is first-class**: `effective_until` + `successor` apply automatically at the date
  (providers now print their own successors: Sonnet-5's step to $3/$15 on 2026-09-01 is in Anthropic's
  own table); a provider-announced *deprecation* date is an `effective_until` whose passing means
  REFUSED, not stale. Promos without expiry dates are never booked — book the list price.
- **A contract-priced lane without a written contract price is REFUSED** — never estimated.
- **Truth passes**: monthly invoice reconciliation folds ledger vs provider export; >10% drift marks
  the row stale fleet-wide and runs the diagnosis fork (token totals match ⇒ price wrong ⇒ fix book;
  differ ⇒ adapter under-reports ⇒ adapter bug). Ledger-derived fields (`tok_s_p50`, `ttft_p50_ms`)
  come from spend records, never hands; the local rows' `as_of` comes only from the bench job.
- **[SECURITY-SEAM → §13]** The book's `version` (content sha256) is cited by every spend record;
  at Stage-1b+ the book is operator-signed and an unverifiable book is refused (a poisoned book
  redirects the whole fleet's routing). `weights_family` on third-party hosts is **attested twice**:
  the signature covers the *declaration*, a runtime canary covers the *reality*; on mismatch the
  lane's diversity contribution de-rates to ZERO and the row goes stale. Mechanics: identity-firewall.md.

### §7.2 · DECIDE — dollar-denominated UCB over (approach × lane)

**Factorization (law).** Score-bearing arm = *(approach × effort)*, plus *host* only while
`parity_verified:false`. Cost-bearing dims (host, cache_mode, batch) are chosen per-dispatch by
`quote()` arithmetic, not learned: identical weights produce the same output distribution (A6 — the
blind spot follows the weights), and the bandit MUST NOT spend exploration dollars re-learning posted
facts. A third-party host rides as its own arm exactly until the 5-pull parity probe passes.

**The index (normative; unit-invariant).** v2's formula (`ln USD_total` bare) is repealed as
dimensionally unsound — a currency re-scale would change exploration. v5:

```
u0       = min over live lanes of quote(reference_frame).usd_expected     # cheapest-pull unit, per round
ñ_a      = max(usd_a, u0)/u0          Ñ = max(USD_production_total, u0)/u0
index(a) = ( best(a) + c·√(ln Ñ / ñ_a) ) / max(ê(a), 0.01·u0)
```

where `usd_a` counts only `attribution:candidate` spend (apparatus-INVALID spend commits to the run's
ledger but never burns the arm — the attribution fork, §5), `best(a)` is the arm's max score under the
current oracle generation, and `ê(a)` is the cache/batch/stale-aware quoted next-pull cost. Dividing by
ê makes the index score-per-expected-dollar; pricing the local floor (7.5) keeps it finite.

Laws: **allocation never selects** — champion selection stays in `converge`, outcome-authoritative,
pure-score; a cheap arm gets more tries, never a discount on the bar. Cold start pulls every arm once,
cheapest-ê first, except **arm-zero (the null) is forced within the first wave regardless of cost**;
the pre-sweep guard refuses rosters whose one full sweep cannot fit `explore_frac` of the budget — the
refuse-to-swarm law with arithmetic. Pruning is 2-D (score margin AND cost-per-point) with the
never-prune set (null · champion · n<2 · last live arm of any manifest-required weights family — **A6
outranks the bandit**) and full resurrection + regrade on oracle generation bump. What UCB never
learns: posted prices, capability fit, harm gating, diversity composition, weights identity mid-run.

**The null's dollars (law; mechanics in pricebook.md §4.6).** The control is protected by
*reservation*, not hope: UNSETTLED task class ⇒ matched-dollar reservation at run open (`presence{phase:genesis}`, R19);
settled-calibrated ⇒ inline null arm with a ≥10% floor reserved at open + sampled matched-replay
audits (`audit_rate` 0.25). Lift is published in both units — `vs_null{matched_production,
matched_invoice}` — and the flip predicate keys on **matched-invoice** (the swarm pays for its own
coordination overhead or stands down): ≥5 audited rows in the trailing 20 with median audited lift ≤ 0
flips the class to single-cell (ECON-8; one predicate, §5's).

### §7.3 · ENFORCE — reservation is the only path to spend

Before any dispatch the metered path **reserves the pessimistic worst-case** (input counted per
tokenizer family, output at the mandatory `max_tokens` cap, prices stale-pessimistic, context tiers at
the ceiling — a call with no computable worst-case is UNRESERVABLE ⇒ REFUSED); dispatch happens only if
every scope (fleet → run → purpose) admits it atomically; actuals commit; the remainder releases.
**Overshoot is zero by construction** at every scope (the induction in pricebook.md §4.3), with one
honest, printed exception: within a tool-lane *lease* the cell self-meters and the worst uncounted
exposure is one lease quantum. F6's $0.0006-against-$0.0005 becomes unreproducible; the leak closes
*before* dispatch, not after.

- **The escrow is Conductor-owned and fleet-scoped**; any cognition anywhere reserves against it. Runs
  open *scopes*, never their own governor (repeals `drive.py:63`). Purposes are scopes: a verification
  *reserve* is a floor production cannot eat; `oracle_growth` is a cap whose refusal is a receipt.
- **Fold law (A13 conformance).** Scope counters are in-memory folds over durable RESERVE / COMMIT /
  RELEASE records in the **conductor's own ledger**; on restart they rebuild by fold + `reconcile()`
  — which runs **before the first new reserve** and settles every in-doubt call (commit-at-worst,
  `outcome:"unknown"`; in-doubt spend is real spend). `Governor.spent` as a process float is repealed:
  spend that cannot be folded from a log is not accounting, it is a guess. Three durability classes:
  `res:sync` folds to zero (work re-dispatches under idem); `res:durable` (batch/racing legs, carries
  the provider `batch_id`) folds STILL-HELD and settles only by a receipted H0 reconciliation act;
  `res:lease` folds STILL-HELD and settles from the leaseholder's own receipts.
- **No new Medium type.** Spend truth lives in the conductor ledger; fleet-visible attribution rides
  the `cost{}` field-group on records already crossing (receipt, act_receipt, cmd_receipt, verdict) —
  v2 §7's design kept, v3's unfiled `type:spend` repealed. `hc ask` stays degenerate: quote + reserve +
  call + commit are conductor-internal; the Medium sees two appends, the second carrying `cost{}`.
- **One metered path, mechanically enforced**: only `cognition/metered.py` may import provider
  adapters — an import-graph + string-load conformance test that today fails three ways (commander
  `:116`, judge panel `topology.py:148`, and adapters discarding the usage detail they already receive,
  F26). Per-provider concurrency caps and `Retry-After`-honoring breakers live inside this path (F2).

### §7.4 · Cache, batch, and speed as fabric law

**Cache discipline.** The frame assembler (§8) owns segment order (`stable → semi → volatile`) and
stability *tags*; the metered path's adapter **realizes** tags per lane (breakpoints, TTLs, minimum
cacheable lengths are per-SKU facts in the book) and **validates** stability-monotone order,
fail-closed. Salience eviction MUST NOT touch stable/semi segments between declared boundaries (the
hysteresis law — one dropped stable item busts the whole downstream prefix). **Affinity is arithmetic,
not a bonus term**: warm-state × booked multipliers price the prefix forfeit of switching hosts inside
`ê_H` over a horizon (default 3), so stickiness emerges from the quote. **Fan-out stagger**: N calls
sharing a prefix dispatch one warmer and release N−1 per the lane's booked `warmer_release` —
readable-at-first-token is *documented only on Anthropic* ("a cache entry only becomes available after
the first response begins"); everywhere else the default is on_complete, because an optimistic
`on_ttft` silently pays N writes. The canonical hit-rate is `cache_read / (input + cache_read +
cache_write)` over cache-capable lanes, bar at **≥60%** on `hc top`, and a low rate indicts *frame
ordering* first, provider last (the diagnosis tree is §7-owned, rendered by §10). Cache-*storage-rent*
lanes (Gemini) add `rent × hold-hours` to ê — rent and prepaid-write models must quote comparably.

**Batch lanes are topology-phase decisions, not per-call habits.** Batchable: tournament production
rounds, regrade sweeps, oracle growth, promotion panels (sla ≥ soon), consolidation. Never: `hc talk`,
interactive ask, acts whose expectation would expire in the queue, racing legs. Admissibility keys on
the **booked outer window** (`batch_window_max_h`: 24h Anthropic, 168h Groq — a 7× spread one
discount rate hides), such that the interactive-resubmit escape always remains open; the watchdog
cancels-and-resubmits at `deadline − margin`, and the paid premium is receipted (`waste_flag:
batch_expired`), never silent. Batched-drive = top-k delayed-feedback UCB under frozen posteriors;
convergence counts events, not wall-hours. Batch escrow holds are `res:durable`, visible as their own
`hc top` line, and capped (≤60% of fleet headroom) so hours-locked dollars cannot starve interactive
runs; `quote()` exposes `{window_close_eta, expiry_at}` so the fleet allocator can price park-vs-wait.

**Racing is hedging, not routing** (fast lanes are insurance): hedge exactly when the evaluated miss
cost exceeds the quoted hedge cost (deadline form for batch tails, λ-form for interactive; every term
from the ledger or the book — the rule is evaluated, never vibed). Hedge legs double-reserve
(concurrency-safe by construction), first-useful wins, the loser is cancelled, committed, and
receipted `waste_flag: racing_loser`, all under a `hedge_frac` sub-cap (default 5%). A hedge lane that
keeps winning is a routing signal — the ledger's percentiles shift and the hedge argues itself out of
a job.

### §7.5 · Verification economics and the local floor

**Two-tier verification is a theorem of the prices, kept from v2 verbatim**: a majority-of-3 panel
pays iff `(e − 3e² + 2e³) · V_wrong > 2·c_judge`; at promotion `V_wrong` is the whole run (always
clears), per-round it is pennies (almost never clears) — hence *cheap single cross-family screen per
round, full panel only at promotion*. Judge pulls price via `quote(purpose=verification)`; judge error
ê lives in the trust plane's oracle library; same-family panels (`ρ→1 ⇒ Δ→0` at full cost) remain the
single worst buy in the fabric, now an inequality the roster solver cannot satisfy. Two-phase grading
prices phase-B under `purpose=verification` with **structural attribution**: phase-A/candidate failure
burns the arm; phase-B/apparatus failure books to run-level `apparatus_usd` and never burns the arm
(the fork that replaces v2/v3's blanket INVALID-burns-arm; storm-park and per-arm quarantine carry the
loop-safety).

**The local floor is a pricebook row like any other**, priced at electricity:
`$/1M-out = watts × ($/kWh) / (tok_s × 3.6)` — 2026 measurements: a 4090-class card runs ~9B-Q5 at
90–140 tok/s (≈ $0.10–0.16/1M-out) and ~32B-Q4 at 30–45 tok/s (≈ $0.32–0.49/1M-out), amortizing
toward $0.02–0.12 under continuous batching; the island gets *cheaper* under load, the exact opposite
of cloud rate limits (F2). `capex_amort` exists, default off (sovereignty counts marginal cost) —
honest caveat kept from v2: hardware amortization roughly doubles the local $/1M; still competitive. Every
degrade ladder MUST terminate in a local SKU whose `liveness` was set by preflight (a ladder whose
terminal lane fails liveness is a RED preflight before the run); when even the local pull cannot
reserve, the run parks `stopped=budget` — **degrade changes lanes, never law**; no rung bypasses the
hard-stop; no cell hard-requires cloud to close its loop.

### §7.6 · The economics made visible

`hc top` is a set of **named queries over the conductor spend ledger**, each carrying its diagnosis
string (definitions §7-owned; rendering §10-owned; one query set, three renders): burn_rate ·
projected_to_cap · spend_by_lane · spend_by_purpose · cache_hit_rate (≥60% bar) ·
effective_vs_sticker · null_gap · pricebook_age/stale-set · reserved_outstanding · reserved_in_batch ·
leases_outstanding · retry/breaker state · overrun_count (**>0 is always an alarm**) · racing_waste ·
apparatus_usd · operator_disagreement_rate · adjudication_latency (both folded from the trust plane's
case records — the operator is a priced organ on the same pane; v2 §7 guard restored) ·
last_reconciled. The savings meter is `usd_sticker − usd_effective` per record —
cache, batch, and stagger discipline as one visible number.

**Falsifier index (§15 rows; drills in the build ladder):** ECON-2 (16-concurrent overshoot drill:
`committed ≤ cap` in every trial, every scope, under crash/429/batch-cancel injection; the F6 replay
stops at $0.0004–0.0005) · ECON-R1 (kill-9 mid-batch: zero double-submissions, ledger = provider
invoice) · ECON-L8 (crash+resume mid-run refuses past remaining headroom) · ECON-LEASE-1 (kill-9
mid-lease: fold shows STILL-HELD, receipts settle, overshoot ≤ quantum) · ECON-UCB-1 (dollar-UCB
reaches target at ≤60% of pull-UCB spend; allocation invariant under currency re-scale ×100) ·
ECON-PB-1 (unknown refused; stale reserves ≥ fresh; planted +30% price change fires the >10% alarm
and the fork labels it price-change) · ECON-CACHE-1 (≥60% hit on a warm tournament; stagger realizes
≥80% of computed savings; shuffled frame refused) · ECON-BATCH-1 (overnight tournament inside sla at
≥40% saving; forced-late premium receipted) · ECON-RACE-1 (p95 wall −30% at ≤10% premium; waste
reconciles exactly) · ECON-8 (the class flips single-cell on the ONE predicate P(C), cited verbatim from §7.2/NULL-1: ≥ m=5 audited rows in the trailing k=20 window ∧ median audited lift at matched-invoice ≤ 0 — the same predicate, never a second threshold).

### [SECURITY-SEAM: econ ← seat 10] — what this plane NEEDS from identity-firewall.md (the inverse of v3's [SCOPED-OUT]; all four confirmed accepted in-room #672/#684/#693)

1. **Pricebook integrity.** The book is load-bearing for routing and diversity: a poisoned book =
   cheapest-lane redirection (attacker-hosted lane wins every quote) or fleet starvation (inflated
   prices exhaust caps) or **monoculture** (falsified `weights_family` defeats the quorum solver —
   seat 05's catch). NEED: operator signature over `version` at Stage-1b+ (custody off-box per 10-T8);
   loader refusal semantics are mine (PART B §6), verification mechanics are 10's. Family claims are
   attested twice: signature (declaration) + runtime canary (reality); mismatch ⇒ diversity de-rate to
   ZERO + row stale (one law, two contracts).
2. **Spend provenance in `hc export`.** The conductor spend-ledger segment + its hash chain join the
   signed export bundle so third parties can recompute every cost against its cited
   `pricebook_version`; redaction rules for SKU names (lane choices can leak strategy/keys' existence)
   are 10's redaction hook applied BEFORE the chain (03's rule) — the econ ledger never needs
   un-redaction to re-verify totals.
3. **Reservation-DoS.** A compromised cell can starve the fleet by reservation spam (reserve→never
   dispatch) or lease-quantum accumulation. NEED: per-issuer reservation rate caps + the TTL sweep as
   the backstop (mine), issuer identity non-forgeability (10's — claim-id spoofing upgrade path at
   Stage-1a+). The escrow refuses a second concurrent lease per (cell × lane) by construction.
4. **Un-metered-cognition as a security property.** The one-metered-path conformance test (S1) is also
   10's audit surface: an adapter import outside `metered.py` is an exfiltration-capable unmetered
   channel (spend invisible = egress invisible). The import-graph test result lands in the preflight
   report (09's admission fold) so a violating build never runs.


---

## §8 · The cell & the nucleus — persistence, memory, time

*(Field detail lives in `contracts/nucleus.md` 5.0 and `contracts/role.md` 5.0; this section states the
law and names the mechanism. Lived evidence: F10 crash→resume exactly-once on PVC; F17 unguarded
`produce()`; F21 rebuild-on-every-open; F28 double durable write per append; E7 REEL register semantics;
E19 record-ceremony pattern; F1/F9 blind-spots-follow-weights.)*

**A1 realized: depth is a defaults preset over ONE field space, never a type.** The role manifest's
field space is fully enumerated with a four-column defaults table (role.md §1–2); a d0 manifest is ≤5
lines; any field is individually overridable; the runtime MUST NOT branch on `depth` except through the
defaults table (falsifier: the only `depth ==` in the runtime is the preset loader). **Depth ⊥
intelligence:** a d0 judge may run frontier weights; a d3 brain may idle on a local 9B. **Sandbox class
and storage binding derive from harm + tools, never depth** — the nucleus home is a directory on a
shelf; pooled cells share a runner PVC, only class-2/3 isolation earns a dedicated volume (§11). At most
one d3 per fleet until CELL-5 passes at d3.

**The nucleus is two things and only two: the Ledger (truth) and Renders (views).**

- **The Ledger** — append-only, hash-chained JSONL; **opens with `genesis`** (claim, lineage_root,
  role_digest, and the **contract-version census in-chain**; later bumps are `contract_bump` records —
  a version epoch outside the chain can be retro-claimed, inside it cannot). Nineteen record kinds in
  four families (io / control / memory / structure — nucleus.md §3); canon = RFC-8785 via one shared
  `common/canon.py` (one verifier, two logs — this chain and the Medium's); the chain-construction
  constant is versioned independently of the contract, so a semver bump never re-anchors. Never
  rewritten, never pruned — **physically segmented, logically one chain**; sealed segments are the
  immutable objects fork references. A pre-chain ledger adopts the chain by **synthetic genesis**
  (`chain_adopted_at_seq`) — the HONEST-EPOCH pattern, stated once, used by nucleus, oracle-gen, and
  export alike. A spawn against a live claim-id whose nucleus lacks a matching genesis/chain MUST be
  REFUSED. **The Membrane runs a redaction pass before every append** — any kind can carry the
  envelope-level `red` note, so the absence of a secret is itself auditable (§13 owns the rules).
- **Renders** — any number of derived views, each a **deterministic fold** over the ledger (A13
  conformance declared: renders, the lineage index, the stats view, and the frame-manifest audit are
  all folds; nothing nucleus-plane lives outside a log). `fold` reads nothing but `(state, record)` —
  no model, no clock, no RNG, no network; unknown kinds pass through. Delete a render and the cell
  loses speed, never truth. **Open is O(delta), never O(ledger)** (F21): every render persists a fold
  cursor *inside itself*, transactionally with its content; the full rebuild-and-diff is the scheduled
  `verify()` at d2+, never the open path. **Render updates happen OFF the append path** (F28): the
  append path performs exactly one durable write — the ledger's.
- **Generative renders stay legal by journaled extraction:** model output enters as validated
  `memory.assert` records at assert time; `fold` replays and never re-extracts. The temporal-KG render
  folds bitemporal fact versions (Zep/Graphiti semantics adopted, dependency refused — their LLM
  edge-invalidation is precisely what a render must not do); **contradictions are surfaced at recall,
  both versions flagged, never auto-resolved** — a render resolving silently is trust minted inside the
  fabric. The tkg ships **dark** under NUC-3's pre-registered bars or not at all.

**Durability is two laws plus honesty about the rest.** LAW-FSYNC-EFFECT: an H1+ `action`'s append
returns only after fsync; the effect executes only after return (the `act` plane's hard gate — §6
consumes it). LAW-FSYNC-ACK: a step's `outcome`+`checkpoint` are fsynced before the cell reports done.
Everything else group-commits (25 ms / 64 KB / any gold record flushes all), and the loss window is safe
by construction: LAW-CURSOR-IN-CHECKPOINT means a lost percept is an unadvanced cursor, and re-poll
re-delivers. `memory.fsync: always` restores exact v1 behavior by manifest.

**Memory is a tool with a register wall, enforced in code at write time.** `remember / recall / revise /
forget / pin`, membrane-internal, never advertised on the Medium. `factual` requires a ref-closure
terminating in non-decision records (witnessed percepts, act-execution receipts, operator commands —
self-citation is trust minted inside the fabric, A5's memory-plane twin); `narrative` is model-authored
compression — legal, useful, **cite-blocked** in oracle-facing artifacts (the block keys on register,
not refs-absence). Default register is narrative: a sloppy cell mints style, never fake facts. The
constitution states the semantics honestly: **factual means auditable-to-terminal, never true** — every
terminal carries the membrane-stamped **trust tag** (derived only from transport-assigned wire columns
and the type-ACL, never sender-suppliable fields — §13), and the tag propagates into recall provenance
lines, frame renderings, and **evidence bundles**, so the oracle's entailment sample and the operator's
audit both see the trust class of every ground. Cross-boundary grounding (`xrefs`) admits only the wire
registry's **non-mintable types** ({receipt, act_receipt, verdict, command, cmd_receipt} at 5.0 — the
set is *derived from the registry*, never hard-coded); a raw URL the cell never fetched is not evidence. A3 privacy holds: the oracle never walks a nucleus — the membrane exports
a hash-bound **evidence bundle** at submission (narrative refused at packaging); `hc peek` audits
bundle-vs-ledger, and a mismatch is a fabricated warrant (the L-NO-NAKED-CLAIMS stain). **Nothing is
injected silently:** every prompt token traces to the role manifest, a ledger record, or a
transcript-visible tool result.

**Frame assembly is deterministic nucleus code, manifested every tick.** Sections S0–S6 (identity,
tools, digest, working, retrieved-with-provenance, recap, percept) packed by per-depth ratios of the
usable window; overflow drops whole items by ascending salience, recorded in the manifest; d0 bypasses
the assembler entirely. **Ordering law:** stable → semi-stable → volatile, and the split of labor with
the economics plane is constitutional: **the assembler owns token ORDER + stability TAGS + per-segment
hashes; the provider adapter owns cache-breakpoint REALIZATION per lane and validates
stability-monotone order fail-closed** — breakpoints are lane-dependent facts (per-model minimum
cacheable sizes, TTL tiers, and automatic-caching mechanics drifted again in May–July 2026), so
hard-coding them in the assembler is a category error. **BYTE-STABILITY:** S0+S1 byte-identical within
a `(role_digest, pinset_hash)` epoch; S2 changes only when a consolidation installs, and installs land
only at task boundaries. **HYSTERESIS:** eviction pressure lands on volatile sections only; a
stable-section overflow is a spawn-time refusal, never a silent truncation. Both cache bars hold
together — byte-identical frames AND ≥60% hit-rate — passing one while the other dies is a fail. "Why
did the cell not know X at tick t?" is a mechanical query over `frame` manifests: in items, in dropped
(with the losing salience), or never gathered.

**Consolidation is a scheduled Step that buys frame economy, never truth** (recall falls back to FTS
over raw records; d2+ only — sleep-time compute pays ~5× test-time reduction and ~2.5× lower
cost-per-query only when queries share context, re-verified 2026-07). **The anti-death-spiral law is
structural:** the consolidation profile has no digest-only input path — every pass ingests raw span
records by construction, with the prior digest marked guide-never-source. **Cold-eyes validation runs
on a different weights family that ROTATES per pass** (a fixed pairing can settle into a correlated
blind spot — F1/F9 applied over time); a failing digest never installs; asserts from a consolidation
pass get no register privileges. Pins and S0 identity are not consolidation-writable (E7's Ring-0 law).

**Fork/COW is MCTS over agent state, and lineage is a pure fold.** Fork is a **ledger op, never a
volume op**: the privileged runner seals the parent's active segment; the child's past is a
borrowed-segment manifest referencing sealed immutable segments by content hash (hardlink = same-shelf
fast path); the child's chain roots in `parent.hash(at_seq)`, so a spoofed lineage fails verify.
Lineage records live in both ledgers (parent `fork.child`, child `genesis.forked_from`, both gold); the
Conductor never reads a nucleus — its lineage index folds from spawn commands and Medium posts, audited
against the nuclei by `hc verify`. Renders are never shared across a fork. Exactly-once is scoped:
`(lineage_root, effect_id)` for world effects, `(claim, step)` re-fires per branch by design. Pruned
branches are **parked, not deleted** (gold `parked` record, metadata-never-load-bearing; refcounted
segments; `spawn --from-snapshot` resurrects) — the Darwin-Gödel stepping-stone archive for free.

**The tier bars keep cheap cells cheap** (NUC-7): d0 = no nucleus (a run-log line); d1 = ledger +
index render — append p50 ≤ 10 ms amortized, **≤1 durable write per standard flush**, nucleus wall
share < 1% per 100-step window, **prompt-token overhead zero by construction** (the ledger is
out-of-band — v2's "<1% of step tokens" is satisfied structurally, and wall+bytes are what we measure);
open p95 ≤ 100 ms at 100 K records warm (F21 bar); d2 adds FTS + verbs + consolidation; d3 adds
tkg-dark + self-tuned ratios (±50%, journaled) + Medium anchoring (a status post — no new wire type).
Resume is reconstruction, not replay; `pending()` is plural (parallel in-flight H0 acts) and every rung
≥2 records carries the **read-barrier** (`outcome_for` before cognition/effect — F17's closure). Breach
of a bar degrades observably (strip ladder → `hc top`), never silently.

**Record-ceremony degeneracy is lawful and barred** (NUC-9): d0 = 0 nucleus records; `hc ask` (d1-adhoc)
= exactly 2 (`action`+`outcome` — the resume substrate F10 rides); d2+ = the full taxonomy as the loop
needs it. The full degeneracy arithmetic (nucleus 2 + Medium 2 + one metered call) is printed once in
`contracts/command.md` and cited, never re-derived.

**[SECURITY-SEAM: §8 ↔ §13]** (the inverse of v3's scope-out; seat-10 sweeps): (1) **redaction before
append** — pattern set, secret custody, and the true-erasure path are §13's; the envelope `red` field
and its auditability are §8's. (2) **Trust tags** — stamping rules (transport-assigned columns only) are
§13's; propagation through registers, frames, and bundles is §8's. (3) **Register wall vs injected
facts** — the wall guarantees provenance class, not truth; §13's ingress firewall is what keeps a
poisoned percept *labeled* (`trust: external`) so the wall's guarantee stays honest. (4) **Sealed-set
mode** — `memory.ledger: none` MUST hold at every depth so sealed grader bytes never enter a nucleus.
(5) **Export** — the signed `hc export` and the d3 anchor bound the same-box rewrite window the chain
alone cannot.

---

## §9 · The Medium & the run engine — one log per culture, one driver over it

### The Medium — one log per culture, plus native wake; everything else is a fold

**The five duties ride one log.** Audit trail, resume source, provenance record, viewer feed,
stigmergy substrate — all are **named folds** over the same append-only, hash-chained, firewalled
per-culture log (the Fold Law, A13). Receipts land ON the Medium (MUST; conductor-only; D-gold) —
the live repo's receipts never touch it (E2: `drive.py:112` holds them in-process), which is
precisely why resume-as-fold and certificate-as-fold are impossible against today's log and why
this MUST lands in the first Medium build slice, not the third.

- **L-FOLD-CLOSURE.** Every constitutional fold declares its input filter, and that filter MUST be
  compaction-closed (a subset of types whose retention class survives the fold's horizon). A fold
  reading R-decay types is a review-time bug. Decisions that consume decaying evidence embed its
  digest in the durable decision record; folds read the decision, never the decay.

**Native wake, the law.** The owned interface is `post / poll / wait / replay / get / exists /
claim / cursor / verify / compact` (wire.md §7). **The hint is best-effort; the filtered
past-cursor query is the only truth.** `wait()` MUST subscribe-hint → truth-query → block →
re-query; sever the hint channel and the fabric degrades to slow-poll with **zero loss** (C3
drills it). A sleeping cell blocks below cognition and burns **zero LLM tokens**; wake p95 ≤200 ms
(T0) / ≤500 ms (T1). Delivery is at-least-once; processing is exactly-once via cursors
(truth = `max(nucleus cursor, transport cursor)`) + idempotent posts (`(culture, sender, idem)`
unique; dedup is success, never an error).

**Coordination is log-derived.** `claim` is a CAS as a pure fold over claim records —
steal-from-stale bumps a fold-computed epoch no field can lie about; the conductor lease and
tool-lane leases (`resource:"lane:<sku>"`) ride it with zero new types. Privileged posts from a
deposed holder are void-at-fold.

**Retention is stigmergic evaporation with a Merkle-sound memory.** R-forever = the provenance
skeleton, small by construction. R-run = pinned until the culture's terminal verdict, then
archivable. R-decay = TTL'd working set — the pheromone-evaporation parameter, per culture.
Compaction is conductor-only, idempotent, **anchor-before-effect**: one `compact` record carries
each dropped span's RFC-6962 Merkle root and chain splice; `verify()` reconnects through the holes;
archived bytes stay inclusion-provable. Retention promotion (any record cited by a retained
verdict's evidence closure) is a fold, never a row mutation. Evaporation ≠ amnesia: what decays was
never allowed to be load-bearing (L-FOLD-CLOSURE).

**Two transports, one conformance battery, honest durability.** T0 = embedded SQLite WAL on a
local filesystem (never a network FS — WAL corrupts; preflight G-DBLOCAL enforces; connection
pragmas are contract text, not folklore — E3). T1 = NATS/JetStream (stream-per-culture; stream
sequence = culture seq; wake via `consume()` on durable pull consumers — push is the legacy API;
the Conductor's sealer materializes a SQLite mirror with the identical schema, so the read path
cannot diverge). **D-gold never rests on rented fsync**: gold = PubAck + seal + fsync'd anchor
(+ the producer's nucleus journal for cell-posted gold); JetStream `sync_interval` is server-level
and defense-in-depth only (Jepsen: the default window lost acked writes; single-bit corruption loss
is still an open upstream issue as of 2026-07). T0 prefix-durability: chatter at
`synchronous=NORMAL`, gold commits at `FULL` — a crash loses only a contiguous chatter suffix,
never gold, never a hole. **C1–C12 run from one test file against both transports** (fixture =
Medium ∪ FaultInjector{crash, corrupt, sever_hint}); an assertion beyond that pair is a contract
leak — the test is redesigned, never special-cased. "The wire survives the swap" is
falsified-or-passed, never asserted.

**The membrane at culture scale** is the bridge: a paired relay of ordinary bus clients; directive
types never cross inward; bridged records arrive `origin=external`, locally re-sequenced, deduped
by bridge idem; remote receipts are DATA until a signature upgrades them
(§13, identity-firewall.md B.6). Single-hop until a falsifier demands more.


### The run engine — one driver, four planes, six topologies

**The run engine is ONE loop.** The four planes — **CONVERGE** (is it good?), **ROUTE** (who does it,
on what lane?), **SCHEDULE** (which approach × lane, how much?), **DRIVE** (run the whole loop) — are
**pure functions over ledger-derived state**: one fold (`contracts/run.md` §R8.2) feeds resume, `hc
verify`, and the viewer, so what resume rebuilds, what the certificate claims, and what the operator
sees cannot drift *by construction* (Fold Law, A13). A **topology is a policy row, never a loop**:

```
Topology := (dispatch_policy, feedback_policy, tick_end_policy, termination_unit, verdict_kind)
```

Six rows (tournament · tournament×ucb · mcts · pipeline · mapreduce · fanout · free-swarm-as-experiment)
over one driver; `run_tournament`/`run_drive`/`run_fanout` as sibling code paths are REPEALED. A
topology that needs a bespoke loop step is an illegal topology — its admission test is stating its five
fields and nothing else. Evidence this is load-bearing, not aesthetic: the three live copies drifted
within P1–P2 (`stable_k` counts rounds in topology.py:190, steps in drive.py:127, against a contract
that says proposals — F14) and grew independent defects (F24: an all-INVALID round advances `stable`;
F25: judge cognition escapes the governor). One driver makes the whole drift class unwriteable.

**Laws (run half of §9):**

- **L-RUN-1 (manifest freeze).** At run-open (the culture genesis, `presence{phase:genesis}` — R19) the manifest is canonicalized (JCS; every ref
  `path@sha256`), posted with its `manifest_sha256`, and FROZEN. A changed manifest under the same
  `run_id` is REFUSED; a change is a new run (`resume_from` MAY import). A verdict that cannot name
  the exact bytes it converged under is not recomputable.
- **L-RUN-2 (the convergence predicate — defined once, in `oracle.md` §5.3).** A convergent run closes
  `verified` only when the oracle's eight-clause predicate holds (**the single home is `oracle.md` §5.3**;
  nothing else may declare convergence; `run.md` §R2.1 calls `oracle.converged()`, never restates it): outcome
  PASSED (non-mintable) ∧ score ≥ target−tolerance ∧ `stable_k` VALID scoring events ∧ probe divergence ≤ ε ∧
  **no check degraded** ∧ champion uncontested-or-at-cap ∧ INVALID rate ≤ R% ∧ the null recorded with its
  reservation honored. A champion contested for `contested_cap` consecutive regrades with no bar movement closes
  **`verified-with-residual`** — the dissent verbatim in the certificate; a permanently-dissenting
  panel never deadlocks a run and never silently seats a champion.
- **L-RUN-3 (stability is VALID-only; apparatus cannot converge a run).** `stable` advances ONLY on
  VALID (passed|gate) receipts that fail to improve the champion. INVALID receipts advance nothing,
  seat nobody, and — new in v5 — charge **no arm** (attribution matrix, `run.md` §R2.5): spend commits
  to the run's purpose ledger; the arm is charged only for rows attributable to it. Guards stack:
  per-arm availability quarantine (2 consecutive apparatus INVALIDs; lifts on reconcile) → cross-arm
  INVALID-STORM PARK (≥3 across ≥2 arms) → run-level R% INVALID-rate halt (`oracle-sick`, default 25%).
  F24 is the lived proof the missing half of this law converges runs on broken apparatus today.
- **L-RUN-4 (event-time termination).** `stable_k`, rounds, gradings count SCORING EVENTS; wallclock
  only PARKs. A parked-and-resumed (or preempted, or crashed) run converges IDENTICALLY to an
  uninterrupted one — preemption is free because resumability was constitutional before scheduling
  existed.
- **L-RUN-5 (the certificate is a fold output).** A certificate is DEFINED as the output type of the
  named fold over a Medium span; `hc verify` recomputes every field (spend twice: Σ`cost{}` over the
  span AND the conductor-ledger escrow fold — the totals MUST agree). Anything not recomputable is a
  press release. Fanout emits `synthesis`, never `verified` (L-HONEST-VERDICT).
- **L-RUN-6 (attribution is structural).** Where a failure occurred — provider-side, candidate
  execution (phase A), grading apparatus (phase B) — decides its outcome; content is never inspected
  to assign blame. Two-phase grading (05) makes the boundary a process boundary; the differential rule
  (a phase-B failure selective to one artifact while round-mates grade clean re-attributes to the
  candidate) closes the crafted-artifact channel at the attacker.
- **L-RUN-7 (partial view).** In round-structured convergent topologies, no round may deliver the
  same peer set to every cell: deterministic rotated K-subset views, every cell blind to ≥1 frontier
  member, every member seen by ≥1 cell, provenance tags on every packet (`run.md` §R5.2). The
  divergence tripwire *detects* herding; partial view makes the all-same-diet round *unconstructable*.
  Packets carry per-case failures from REPORTED cases only; holdout appears as aggregates; probe
  results NEVER enter packets. (F1's plateau: cells saw only peers' code, never the oracle's per-case
  verdicts; the only external bit in the system was never fed back.)
- **L-RUN-8 (paid-for evidence is never discarded).** Orphan submissions are scored and flagged;
  budget-stop leftovers are `unscored`, excluded, and LISTED; INVALID spend is `apparatus_usd` in the
  residual. Every dollar leaves a receipt or a listed absence.

**Fleet scheduling (multi-run).** Many Cultures share one wallet and account-level provider caps (F2).
The **fleet allocator** grants/revokes concurrency slots and parks/resumes whole cultures — strict
class priority (interactive > standard > maintenance-headroom-only), weighted max-min within a class,
sticky capacity, preemption at tick boundaries only, USD-rate governor, starvation aging (`run.md`
§R10). The allocator NEVER reaches inside a run (never picks arms, never touches reservations); intra-
run allocation stays dollar-UCB. **PARK is a graceful crash**: drain, release `res:sync`, post `presence{phase:parked, reason}` (R19) — the on-disk object is indistinguishable from a crashed run, and resume is the same
fold. `WAITING-BATCH` holds `res:durable` legs (dollars locked at the provider, results coming) and
zero slots. Every allocator decision is a `_fleet` record; `hc top` renders from the log. **The
allocator is mortal (new):** its null is FIFO-serial; if it cannot beat FIFO on interactive p95 at
equal dollars with zero starvation (FLEET-0), the fleet runs FIFO and the allocator dies. Park/resume
realization is written against the substrate claim API (09), never a vendor CRD.


---

## §10 · The Conductor & the surfaces — how you command the fleet

You are the fleet commander. **`hc talk` is the canonical commanding surface** (F8), the flag CLI is
the explicit-grammar floor beneath it, and every surface — CLI, talk, HTTP, MCP, PWA, voice, routine
— compiles to **verb #6 (`command`) plus Medium reads**. The Conductor is the control plane that
**never thinks**: the moment plane logic needs cognition it spawns a metered cell from the closed
**service-cell set** (router · intake · synthesizer · adjudicator · grower — each a d0/d1 cell with
its own receipt type, null, and accepted-risk label). The operator is a first-class input with
operator-grade failure modes — storms, typos, dead phones, second thoughts — so the command plane
gives the operator exactly what the fabric gives cells: one metered path, one idempotency
discipline, receipts for everything including refusals, and a narrator physically incapable of
saying what the log cannot prove.

**Fold-law conformance (A13):** queue state, the alias map, routine slot history, the MCP task view,
talk conversation state, the viewer, and the outbox are each a deterministic fold over an append-only
log (`_ops`, a run culture, or the router cell's nucleus). Nothing in this section holds state that
cannot be refolded.

### 10.1 The five laws

1. **ONE INGRESS.** Every *mutating* operator intent from every surface is one schema-validated
   CommandEnvelope through one ingress function (command.md §1/§4). Reads are NEVER commands: `top`,
   `runs`, `logs`, `replay`, `peek`, `export`, `events`, `fleet`, `queue ls` are named queries over
   the log and MUST stay served when the write path is wedged.
2. **EVERYTHING RECEIPTED, INCLUDING REFUSALS.** `ack → progress* → result` as `cmd_receipt` rows in
   `_ops`, keyed by `cmd_id` (wire registry type 17, conductor-only ACL). A policy refusal is a
   result receipt, not an HTTP error. A narrated fact absent from a receipt is a falsifier hit
   (SUR-2).
3. **THE MEDIUM IS THE ONLY EVENT SCHEMA.** Surfaces render the log; the SSE `data:` payload IS the
   Medium envelope verbatim; `hc top` is a set of named queries; the viewer is a pure render. Kill
   the Conductor and every surface still renders full history (the Medium-renderable law).
4. **SURFACES COMPILE INTENT; THE CONDUCTOR EXECUTES.** No surface constructs cells, calls
   cognition, or touches engine modules. The ONE legal fabric import from `surfaces/*` is
   `conductor.ingress` (LAYER-1; composition root `entrypoints/hcd.py` exempted, wire-only). Live
   violations to raze: cli.py:16/44-48/117/156/184/206 · commander.py:17/116/244-247 · api.py:17/60
   · daemon.py:16 string-load (the ~12-site corpus, kernel-measured).
5. **DEGENERACY IS LAWFUL.** `hc ask` = one metered call + **two Medium appends** (`_ops` command +
   result receipt) + zero plane-side LLM tokens; the canonical organ-labeled line-item lives in
   command.md §2.1 and §16 cites it. If envelope machinery ever costs a simple ask more, this
   section has failed.

### 10.2 The envelope, the queue, and the two dedups

The CommandEnvelope (command.md §1) carries `cmd_id` (surface-minted ULID; deterministic
`rt:<routine>:<slot>` for routines), `issuer`, `surface`, `session`, a **closed verb registry**
(command.md §2), `params` + `params_hash` (RFC-8785), the raw `utterance` + `parse` provenance block
when an NL router produced params, `supersedes`, `ttl_s`, `budget`, `dry_run`, the `contracts`
census, and an optional Stage-1b `auth` block (identity-firewall.md).

The ingress (command.md §4, normative) validates → **authenticates** (the AUTH step calls
identity-firewall.md's `verify` + stage oracle; below the Stage-1b trigger absent auth passes; at or
above it **the ratchet applies** — lower-stage validation is no longer sufficient for protected
types) → **identity-dedups** on `cmd_id` (replay returns the existing chain) → version-checks the
census (MAJOR mismatch ⇒ typed `refused(version)` naming both versions) → **posts the command
D-gold, fsync before dispatch** → applies supersede (same issuer+session, queued-only; a running
predecessor is never implicitly killed) → **coalesces** — the F7 organ: fleet-class verbs with
identical `(issuer, verb, params_hash)` inside W_coalesce collapse to ONE execution with N receipt
chains, and the duplicate issuer SEES `coalesced_into` in its own ack, never silence → TTL-expires →
**governs** (run.md's intake classifier keyed on the L0/L1/L2 task-class hierarchy; escrow
reservation against the ONE fleet-scoped escrow; the unattended-issuer ceiling) → **acks with
narration** (pre-minted run_id; every default and every scalar's provenance named) → dispatches to
the kernel's one verb-executor, the only minter of cmd_receipts.

The two dedup mechanisms never merge: `cmd_id` catches replays (transport retry, MCP redelivery,
routine re-fire); `(issuer, verb, params_hash)` + a window catches the lived storm, where every
paste minted a FRESH cmd_id. One prompt pasted to N sessions = one run + "N−1 duplicates coalesced"
in `hc top`.

**The conductor lease.** Any process hosting the dispatcher MUST hold
`claim{resource:"conductor"}`; the epoch is a fold over the claim history (no field to lie in).
Leaseless embedded `hc` is read-only; stale-epoch privileged posts are VOID-AT-FOLD.

### 10.3 Receipts and multi-surface consistency

Because commands and receipts are `_ops` Medium messages, any surface holding a cmd_id renders the
same state by folding `_ops` — multi-surface consistency is free (phone-to-laptop p95 ≤ 1 s,
SUR-4a). A Conductor kill mid-run resumes the SAME cmd_id chain to a terminal receipt with zero
re-issue and zero duplicate runs (SUR-4b); restart emits `recovered` progress for every non-terminal
command — the operator is never left staring at post-crash silence. Exactly one terminal result per
cmd_id; alias chains get mirrored results.

### 10.4 `hc talk` — the canonical surface, mechanized

- **The router is a cell** (F15/F25 closed): a d0 reflex, `claim=talk/<session>/0`, temp 0,
  structured output, metered and ledgered like all cognition. Conversation state IS the router
  cell's nucleus — pronouns resolve against the ledgered turn history; `--resume <session>`
  re-instantiates the cell (A3; no new machinery). "Why did it spawn 5?" is `hc peek
  talk/<session>/0`, not an autopsy.
- **The router proposes; the Conductor disposes.** The router owns the VERB; code owns the SCALARS.
  A deterministic extractor (command.md's parse block; regex spec in the contract) runs over every
  utterance for count/rounds/budget/provider; the six-rule reconciliation table is constitutional:
  extractor-over-omission wins (`injected`); agreement proceeds; **conflict asks, never defaults**;
  router-only values are `inferred`; absences take frozen defaults (`defaults_applied`); double
  extraction asks. **Silently defaulting over a stated number is a constitutional violation**
  (Entry-30; F27 is the live half-fix this law completes). The ack narrates every scalar WITH its
  provenance: "6 cells (you said 6) × 3 rounds (default — say a number to change it)".
- **Mode legibility:** a fleet action prints a run-id line; chat never does. The mode-trap guard:
  interrogatives/hypotheticals route to `chat` and the extractor MUST NOT override the verb — zero
  fleet actions on chat utterances is a hard bar (SUR-1).
- **Chat is the fallback and MUST produce a real reply** (the dead-"hi" fix, kept) — from the router
  cell, still metered. `ask_operator` prints one question; the next input binds as the answer
  (resumable mid-question).
- **The honesty rule (HC-7's surface sibling).** Every narrated fact derives from a Medium event or
  receipt **valid at the fabric's current auth stage under the ratchet** (log-derived @ Stage 0 →
  ACL-checked @ 1a → signature-valid @ 1b; a stripped signature never demotes a protected record to
  a lower stage's validity — identity-firewall.md's stage oracle is the predicate). Narration is
  assembled by code from the struct (command.md §3.2) — the floor renderer is a deterministic
  template; the verdict type is always named; **a synthesis is never rendered as verified**;
  tri-state failures render verbatim ("2 of 4 cells errored (429); synthesis used 2 answers" — an
  error is never a zero); the optional prettifier sees ONLY the struct and is
  numeral-containment-checked, with failures counted as `narration_downgrade` events.
- **The degrade ladder (the island law at the surface — restored from v2).** Router provider
  unreachable ⇒ the commander MUST degrade in order: (1) the local-model router (routing is a small
  classification task; the local floor closes the loop), (2) else parse nothing — print the exact
  `hc run …` command it would have issued and let the operator confirm. NL is sugar over a sovereign
  floor; a dead cloud MUST NOT mute the fleet (SUR-1d drills it).

### 10.5 The surface set (small, closed)

1. **`hc` CLI** (primary; SSH-friendly): thin client of the ingress — daemon-backed when `hcd`
   answers, else `--embedded` hosts the same ingress in-process (printed once; lease rules apply).
   Verb table, `--json`/NDJSON everywhere, and the semantic exit-code contract (0 ok/converged ·
   2 usage · 3 refused · 4 not-found · **6 completed-without-convergence** · 130 SIGINT-run-continues)
   are command.md/SUR-9's; the tri-state discipline reaches shell scripts through code 6.
2. **HTTP (`hcd`)**: `POST /command` (202 + Location + ack; `?wait` long-poll), `GET /command/{id}`
   (the chain), `GET /events` (SSE; **the `data:` payload is the Medium envelope verbatim**; opaque
   monotonic cursor; `Last-Event-ID` replay; cursor-older-than-compaction ⇒ `410` + earliest valid;
   filters advance through the same cursor space), `GET /top|/runs|/queue`, honest `GET /health`
   (can say "accepting but not executing"). Errors are RFC-7807. Authn floor at P2.5
   [SECURITY-SEAM: seat 10's SEC-8 — 401 before any Ingress exposure; bearer + loopback classes].
3. **MCP server** (`surfaces/mcp.py`): the fleet as tools for any MCP client. **The typed grammar,
   not the NL router** — a Claude-class client is itself a model; double-LLM routing is refused.
   13 tools with strict input/output schemas (structured content; `verdict_type` is a schema field —
   the honesty rule's MCP twin); `hc_peek` on stdio transport only. **Dated ruling (2026-07-16):
   build against MCP 2025-11-25 stable; design the task layer to the 2026-07-28 RC's shape
   (server-directed task creation; `tasks/get|update|cancel`; no `tasks/result`, no `tasks/list`)
   because the receipt chain is the mechanism and the MCP task layer is a thin projection —
   task_id ≡ cmd_id, task states fold from receipt phases, `input_required` = a parked H2/H3 act or
   a clarifying question. Adopt the final only at publication + Tier-1 SDKs; avoid deprecated
   Roots/Sampling/Logging.** Listing is `hc_status` (a named query) — the log-fold sidesteps the
   session-scoping problem that killed `tasks/list`.
4. **The phone PWA**: a thin HTTPS client of the same three endpoints over Tailscale + TLS; its SSE
   cursor replays the same rows. Nothing phone-specific exists server-side.
5. **Routines**: stored CommandEnvelopes on triggers (cron/`fire`/watch) entering the SAME queue
   with the SAME receipts; deterministic slot cmd_ids make slot exactly-once a free consequence of
   identity-dedup; `catchup: skip|once`; storms settle + coalesce. **Unattended ceiling:**
   non-operator issuers run H0/H1; H2/H3 acts park. H3-park is *structural*: the operator key never
   lives on the cluster, so a routine's envelope physically cannot present the H3 signature
   [SECURITY-SEAM: seat 10 key custody]. **Dead-man law:** H2 proof-of-notification = an
   INTERACTIVE-class principal's cursor advancing past the hold notice; headless consumers (SSE
   tails, exporters, MCP clients, the viewer) never count; absent it by deadline-minus-grace the H2
   act degrades to an H3 hold.
6. **Voice / avatar / persona layers are SURFACES** — commanding clients of L4. One MAY hold
   owner-memory and compose better envelopes; it MUST NOT plan fleets, spawn cells, address the
   Medium, or write a nucleus — two planners is a split-brain shadow-Conductor. **Confirmation law
   (restored from v2):** a voice surface confirming a held act MUST echo the deterministic nonce
   ("confirm r7-a2"); a bare "yes" never confirms; **H3 confirmation additionally REQUIRES a
   Stage-1b-authenticated surface, never open-mic** [SECURITY-SEAM: seat 10].

### 10.6 Observability surfaces

- **The viewer** is constitutionally read-only: every tab is a named query over the log; it holds no
  write-capable connection (fresh `query_only=ON` per request); it MUST keep rendering against a
  bare medium.db with the Conductor dead — the Medium-renderable law's standing falsifier. The v5
  tab set (ruled from the Intercom ten-tab reference): Fleet (Q-FLEET) · Cultures (Q-CULTURE) ·
  Cells (Q-CELLS) · Runs (Q-RUNS) · Run-detail/Convergence DAG (Q-ROUNDS + Q-ARMS, null flagged) ·
  Costs (Q-COSTS + Q-NULLGAP + anomaly flags; econ's definitions) · Ops (Q-OPS: receipt chains +
  coalesce annotations) · Queue (Q-QUEUE: a single-type fold over `act_receipt{phase:hold}`;
  parked acts render as copy-paste command TEXT, never a button) · SQL (guarded, read-only).
  Connectome and Timeline-as-tab are deferred to P4 polish. The day a control appears the viewer has
  changed surface class and MUST move behind the ingress.
- **`hc peek <claim-id>`** — the private-nucleus read surface: loopback-bound, operator-only, never
  mirrored to the Medium (A3 privacy). Every peek appends an `_ops` access record (who looked, at
  which cell, query shape — WITHOUT content): looking is fleet history; what was seen stays private.
- **The outbox** — results are file + message, never message-only: verdict time writes
  `outbox/<run_id>/{champion|synthesis, certificate.json, receipts.jsonl, MANIFEST.json}`
  atomically; the write is itself an H1 act with a `stat MANIFEST + digest` reconcile probe
  (DELIVER-1 falsifiable); talk/CLI print the deliverable inline (≤ a screen) PLUS the path, always.
  The outbox is a fold-clean render and the per-run doorway the cross-run artifact library renders
  over.

### 10.7 The golden path (day-1 bar)

`uv tool install hypercell` → `hc init` → `hc ask "hello" --provider mock` (zero-key smoke) → one
`.env` line → `hc talk` (viewer auto-opens; deep links per run) → first synthesis → judged champion
→ kill-terminal-mid-run → `hc resume` completes the SAME cmd_id chain. **SUR-8: fresh machine to
first synthesis ≤ 15 min, ≤ 7 commands, exactly one file edit; the resume drill shows zero
double-spend.** Each step's output prints the next step.

*Falsifiers: the SUR suite + MIG-SUR (§15 index; PART D rows). Contract: `contracts/command.md`
v5.0.0. Security seams: ingress AUTH + stage oracle + ratchet, surface authn floors, H3 grant path,
key custody, viewer sweep — `contracts/identity-firewall.md` (seat 10).*


---

## §11 · The substrate & isolation

**Substrate.** The fabric runs on **k3s** — single-binary Kubernetes, SQLite/kine-backed at one node,
identical on a laptop, a VM, a VPS, or a managed cluster (verified current: k3s v1.36.2, containerd 2.3.2,
2026-06). k8s is **demoted from platform to substrate**; identity is the seam, not the scheduler. Long-lived
objects host the spine — the **Conductor** (a singleton `Deployment`, `strategy: Recreate` so one writer
ever holds the ledger), the **Medium** (T0: the Conductor's own SQLite-WAL PVC; T1: a NATS/JetStream
`StatefulSet` ≥3), and a **warm pool** of Runner pods (`StatefulSet`; each ordinal's PVC is its nucleus
shelf). Cells default to **pooled processes**; isolation is promoted only when harm earns it. The `deploy/`
annex is camera-ready; `substrate/k3s.py` and `substrate/secrets.py` are 0 bytes today — the honest map of
what §11 builds.

### §11.1 · The three substrate laws

1. **Pod is the unit of ISOLATION; claim-id is the unit of IDENTITY; they meet only when harm earns it.**
   A class-0 pooled cell is a *directory on a shared runner shelf PVC* (`/shelf/<claim_id>/`), not a PVC of
   its own; only a promoted class-2/3 cell gets a dedicated PVC. Storage binding derives from **sandbox
   class, never from depth** (a d3 brain on trusted loops is class-0; a d0 candidate-executor is class-3).
   This retires v2 §11's "PVC-per-claim-id for every cell," which node-pinned every d0 judge for no benefit
   and priced out the fan-out the null-beating budget depends on.

2. **The Fold Law (A13) governs substrate state.** Every durable substrate structure — which claim binds to
   which runner ordinal, which sealed segments a fork borrows, what a restore re-binds — is a deterministic
   **fold over the append-only log** (the Medium + the nuclei), never live cluster state that cannot be
   recomputed. The claim table is a *render* of `claim`/`presence`/`park` records; kill the scheduler and it
   re-folds. **Fold-conformance declared:** claim table ← claim/presence/park records (§11.2); fork
   borrowed-segment set ← fork records (nucleus.md); the preflight report is a **probe, explicitly NOT
   state** — it is re-run, never resumed (§11.4); the backup is a fold snapshot + the live tail (§11.6).

3. **Isolation is HARM-graded, never maximal-by-default, and never silently degraded.** Running every act
   in gVisor melts the fan-out economics (§11.2 quantifies it), so class-0 is the default and `CLASS_FOR`
   (below) promotes only where harm demands. **But untrusted candidate execution has no degraded fallback:
   it runs class-3 or it does not run.** "HC-7 closed" is a **log query** over receipts where
   `isolation.actual ≥ isolation.required ∧ isolation.degraded = false` — never a vibe. The isolation-stamp
   fields (`isolation.{actual,required,degraded}`) ride the receipt schema (run.md/oracle.md) and MUST land
   at slice b′ (receipts-on-Medium), before class-3 lands at d′ — schema first, sandbox second, so the query
   has records to close over.

### §11.2 · Sandbox classes 0–3, harm-mapped

The manifest speaks **intent** (`pooled | isolated | hardened`); the substrate speaks **realization**
(classes 0–3). class-1 exists ONLY as the **flagged-degraded** realization of `isolated` or *trusted*-
`hardened` intent when there is no k3s — never as a realization of untrusted execution.

| Class | Realization | Isolation boundary | Harm ceiling | Nucleus placement |
|---|---|---|---|---|
| **0 pooled** | in-process/subprocess task on a warm runner | OS process (shared kernel/pod) | H0–H1 trusted; fan-out rides here | dir-per-claim on the runner shelf |
| **1 sandboxed proc** | dropped-priv subprocess (nobody uid, seccomp, rlimits) — the degraded-**trusted-only** local-lite floor | OS process + seccomp; shared kernel | H0–H1 trusted only | dir-per-claim, local |
| **2 dedicated pod+PVC** | a promoted **actor**: own pod, own PVC, own NetworkPolicy | container namespaces+cgroups; shared kernel | H2 heavy/stateful | PVC-per-claim-id |
| **3 gVisor/Kata** | `hardened` pod, `runtimeClassName: gvisor`, `hypercell-sandbox` ns, deny-all egress | user-space kernel (gVisor Sentry) — syscalls never reach the host kernel | H3 untrusted candidate code | none for the candidate |

```
CLASS_FOR(role, task):
  if task.executes_untrusted_candidate_code:  return 3      # HC-7; no degraded fallback (§11.3)
  elif role.harm_ceiling ≥ H3:                return 3
  elif role.harm_ceiling == H2 or role.stateful: return 2
  elif role.harm_ceiling == H1 and role.tools ≠ ∅: return 1  # often still 0 in-pool if egress-allowlisted
  else:                                       return 0       # trusted pooled loops, fan-out
```

**gVisor is the class-3 default; Kata is the bare-metal ceiling.** gVisor's **systrap** platform needs only
seccomp-bpf + a SIGSYS handler — no hardware virtualization — so it runs on a Hetzner-class VPS where nested
virt is absent. Kata is a real KVM VM (Cloud Hypervisor default as of 2026); it needs bare-metal or
provider nested-virt and is opt-in only. **class-3 availability is a PREFLIGHT FACT, never a docs fact**:
runsc is not in k3s's auto-detected runtime list, so class-3 is a deliberate install (annex B.6) proven by
the `G-GVISOR` smoke pod (schedule under runsc, assert the gVisor `dmesg` banner) — RuntimeClass-present-
but-runsc-broken is a real state.

**agent-sandbox: adopt the pattern now, gate the CRD.** The `agents.x-k8s.io` project (SIG-Apps; core
`Sandbox` graduated to v1beta1 June 2026) independently converged on our warm-pool-claim design
(`SandboxClaim`, `SandboxWarmPool`) — external validation of §11.1. v5 ships the **pattern** on stable-k3s
features (StatefulSet + PVC + NetworkPolicy + ledger-fork) and treats the CRD as a **drop-in backend behind
the AS-GATE falsifier** (§11.8): if a `SandboxClaim` binds a warm gVisor pod < 2 s on stock k3s with a
surviving+snapshottable PVC, the CRD becomes a claim/park backend behind the *same Medium claim records* and
the log shape never changes; else keep the StatefulSet mechanism. Semantics adopted, dependency refused
until earned. (Pod Snapshots remain GKE-backed as of 2026-07 — refused.)

### §11.3 · HC-7 — the substrate half of two-phase grading (TP-1)

The lived gap (F3, re-verified 2026-07-16 at `converge.py:14,22-28,33-37`): a candidate that `sys.exit(0)`
at import spoofs the exit code in-process; one that prints `SCORE=1.0` spoofs a stdout-scraper (the live
"take the LAST match" comment is a false defense — an `atexit` hook prints after the oracle); and
`TimeoutExpired → INVALID` (excluded) rewards self-hang (F13). One root cause: **the candidate and the
grader are not separated.**

Two-phase grading (trust seat, TP-1) is the closure; the substrate owns **phase A**:

- **Phase A (substrate).** The candidate runs in a **class-3 sandbox** (annex B.4) over the case **inputs
  only**, as a `nobody`-uid subprocess of a trusted harness, `readOnlyRootFilesystem`, no answer key
  mounted, **default-deny egress triple-enforced**, cwd a tmpfs. Its **only causal egress is `/out`**. The
  verdict-bearing exit code is the **harness's `waitpid` observation**, emitted after the sandbox
  terminates — never a value the candidate wrote. Its output is a **behavior artifact**, not a verdict.
- **Phase B (trust plane, oracle.md).** The oracle reads the behavior artifact as **untrusted DATA**, loads
  **no candidate code**, and writes `/grade/report.json`; the runner reads only that file. The `import
  candidate` spoof dies by construction: nothing of the candidate's is ever imported or executed
  oracle-side.

**The behavior artifact is untrusted data and carries substrate rails** (the differential-re-attribution
precondition, seat 05): (1) **per-candidate `/out`**, never shared across round-mates; (2) the trusted
runner **seals** `/out` at candidate exit into a **content-addressed artifact** — `manifest.json`
(`{files[{path, sha256, bytes, truncated}], sealed_at, candidate_exit}`) plus the files, size-quota'd
(default 64 MiB, `truncated:true` past it); (3) **schema-checked at handoff**; (4) phase B parses it under
**rlimits** and reads the artifact **store**, never a sandbox volume. Manifest schema is the substrate's;
the **digest law is the act plane's** (a same-name spoof file cannot fake effect-found — the runner seals
before any reconcile probe reads).

**No-network triple** (candidate MUST have no network; three independent mechanisms so no single
misconfiguration re-opens it): (1) namespace **default-deny NetworkPolicy** — *probed*, not assumed
(`G-NETPOL-ENFORCED`: apply deny-all to a canary, attempt egress, assert it FAILS — netpol rides
kube-router→iptables, the F4 axis); (2) **no membrane** — the candidate is not a Medium principal, has no
wire identity, cannot address the bus; (3) **type-ACL at `post()`** — even a forged post is rejected
(only the Conductor mints privileged types).

**Attribution is structural, by phase** (not a heuristic): a candidate-process failure (crash, nonzero,
timeout) is a **GATE** (the candidate loses); **INVALID** is reserved for *apparatus* failure (report
absent/malformed), and its dollars split by phase per R5 — a candidate/phase-A INVALID counts the bandit
visit and burns `usd_a` (self-INVALIDation buys no schedule advantage), while an apparatus/phase-B INVALID
leaves the **arm untouched**: its spend commits to the run purpose ledger as run-level `apparatus_usd`
(cert-residual-visible), never to `arm.usd_spent` — the innocent arm is not charged for a broken grader.
Because phase A and phase B are separate processes, "which phase failed" *is* the attribution —
sharpened by seat 05's differential rule (a selective phase-B failure isolated to one candidate's artifact
re-attributes to that candidate; only per-candidate `/out` makes this sound).

### §11.4 · The Substrate Preflight — verify-and-report, never flap

F4 in one sentence: **the substrate is rude, so probe it.** Before a run is admitted, the substrate
self-checks its assumptions and emits **GREEN / DEGRADED / RED** plus the **maximum sandbox class it can
prove**. Every lived F4 failure is a named guard; each guard **names its fix** in the report (the report is
operator training, not just a verdict). The preflight is a **probe, not state** (A13): re-run at Conductor
start and before any class-escalating run, never resumed stale.

**The battery is split by the build ladder.** Box guards land at **a′** — they protect the LIVE SQLite
Medium *today*, with no k3s anywhere; the k3s battery lands at **d′**, gating class escalation:

| Land | Guard | Checks | On failure |
|---|---|---|---|
| **a′** | `G-DBLOCAL` | Medium/nuclei on native ext4, never `/mnt/c` (drvfs/9p) or a network FS | RED — SQLite corruption risk |
| **a′** | `G-DB-DURABLE` *(new, seam 03)* | the Medium db has WAL + `synchronous`≥FULL for gold + `busy_timeout` set | DEGRADED — durability unproven (live `transport_local.py:20` sets none; E3) |
| **a′** | `G-CLOCK` | monotonic clock sane; no large skew after host sleep/resume | DEGRADED — ULID/lease ordering unsafe |
| **a′** | `G-CGROUP` | cgroup **memory** controller present + enforcing | DEGRADED — pod limits are theater (WSL2 shipped without it) |
| **a′** | `G-FSYNC` *(seam 02/03)* | fsync p50 within the d1 append budget on `HYPERCELL_HOME` | DEGRADED — gold-durability slow |
| **a′** | `G-LOCAL-FLOOR` *(seam 07)* | the terminal degrade-ladder lane is LIVE (model server reachable + 1-token smoke gen) | DEGRADED — no real floor |
| **a′** | `G-UPTIME-REGIME` | no idle-poweroff; WSL2 `vmIdleTimeout=-1` or a live keepalive | RED — k3s will flap |
| **d′** | `G-ONE-RUNTIME` | exactly one container runtime; no 2nd containerd/dockerd | RED — mixed runtime flap (E28) |
| **d′** | `G-FORWARD-ACCEPT` | `iptables -P FORWARD == ACCEPT` (nft + legacy) | RED — pod networking dead (E28) |
| **d′** | `G-IPTABLES-PRESENT` | iptables-save/restore on PATH (kube-router needs them) | DEGRADED→RED |
| **d′** | `G-GVISOR` | runsc on PATH + RuntimeClass + **smoke pod** dmesg banner | class-3 → DEGRADED (RED for candidate runs) |
| **d′** | `G-PVC-SURVIVES` | write marker → delete pod → marker survives on re-bound PVC | RED — no durable nucleus |
| **d′** | `G-IMAGE-IN-K3S` | image digest present in k3s's own containerd (`k8s.io` ns) | RED — ImagePullBackOff (E28) |
| **d′** | `G-NETPOL-ENFORCED` | deny-all a canary, attempt egress, assert FAIL | class-3 → RED — HC-7 no-network unproven |

**Admission law.** A run declaring `hardened` (needs class-3) is **REFUSED** unless `max_honest_sandbox_
class ≥ 3`. A run needing only class-0/1 proceeds under DEGRADED with `isolation.degraded = true` on every
receipt. **RED on any spine guard** (`G-DBLOCAL, G-DB-DURABLE(RED-escalated), G-UPTIME-REGIME,
G-ONE-RUNTIME, G-FORWARD-ACCEPT, G-PVC-SURVIVES`) halts the fabric with the fix printed — these caused a
lived crash-loop or corruption. **The report is a fold-visible record** (seat 03 ruling): the probe posts
`status{kind:preflight}` on `_ops` (R-decay is fine — it is advisory), and every **admission decision
record** embeds `preflight:{digest, verdict, guards_failed[]}` inline, so constitutional folds read the
decision, never the decaying status row (L-FOLD-CLOSURE holds; zero new envelope types). The full report
MAY attach as an artifact on the decision record when durable bytes are wanted.

### §11.5 · Build pipeline & contract migration

**One image, role-selecting entrypoint (A1):** `conductor | cell | runner | sandbox-harness` (annex B.8).
The **sanctioned build is nerdctl + buildkit against k3s's own containerd** (`k8s.io` namespace) — the build
*is* the import, registry-less; manifests reference `hypercell@sha256:<digest>`, never a floating tag (the
fold law applied to images). **docker.io is forbidden** (E28: a 2nd containerd + `iptables FORWARD DROP` =
a 60–90 s `SandboxChanged` crash-loop). The live `deploy/k3s/conductor.yaml` header still instructs the
deprecated `docker save | k3s ctr images import` flow (C-7) — v5 deletes it.

**Contract versions travel as image LABELs** (annex B.8) mirrored to pod annotations and to a genesis/epoch
record on boot (a version on the log, not only on an image). The **preflight refuses a mixed-MAJOR fleet**:
at Conductor start it reads every live pod's contract labels; a MAJOR mismatch is RED (drain required); a
MINOR mismatch is legal and rolling. A MAJOR rollout **drains at a converge-round boundary** (kernel seat's
migration law), `park`s in-flight cultures, writes the epoch record, respawns on the new digest; **claim-id
rebind is version-blind** — identity outlives contracts (the F10 resume path). The versioning law itself is
seat 01's; §11 carries only the deploy realization.

### §11.6 · Backup & continuity

The **system of record is the nuclei-on-PVCs + the Medium log**; everything else is a render — so
continuity = snapshot those and prove an idempotent restore. **restic** snapshots the Medium (via
`VACUUM INTO` a consistent copy — never a raw copy of a live WAL db, which tears) every ~15 min, and the
nuclei shelves (sealed segments are `0444`-immutable → restic dedups them near-free) hourly + on `park`.
Backup volume tracks **cite-pinned retention** (seat 07/act): H0 observation receipts default R-run +
D-chatter; the champion's evidence closure is retention-promoted at verdict; H1+ world-effect acts stay
R-forever + D-gold — so the backup snapshots the *provenance skeleton*, not every web fetch forever.

**The BACKUP-RESTORE drill extends HC-2 from pod-delete to cluster-loss:** destroy the cluster → reinstall
k3s → preflight to the same `max_honest_sandbox_class` → re-import the pinned image (digest matches) →
restic restore nuclei+Medium onto native ext4 → apply the spine → **resume = FOLD** (not replay): the claim
table rebuilds from claim/park records, runners re-bind shelves (F10), the spend meter rebuilds from cost
records (F16 — never resets to $0), escrow **leases** (`res:lease`, seat 07) fold still-held and reconcile
from each cell's own receipts before any new reserve, and pending H1+ acts reconcile via the act-plane probe
(landed/absent/unknown — never a blind retry). **Bar: zero double-fires** across the pending act set; the
post-restore certificate matches the no-catastrophe certificate (modulo budget-burning apparatus-INVALID
visits). fsync-before-effect (act/nucleus seats) is what makes this exactly-once: a restored fleet never
loses the *evidence* an act was in-flight.

**SQLite-never-on-network-FS (constitutional).** SQLite MUST NOT live on NFS/SMB/drvfs/9p (WAL needs
one-host processes; POSIX locks misbehave; fsync lies → corruption). `HYPERCELL_HOME` MUST be native ext4
(`G-DBLOCAL`, which specifically rejects `/mnt/c`). **HA below 3 servers is theater** — a single sovereign
box gains nothing from etcd and everything from backups; HA = embedded etcd ≥3 servers, earned when a
second node exists (P3). local-path is node-local: a cell that must migrate nodes promotes to class-2 and
accepts a copy/restore — there is no cross-node RWX on local-path, and §11 states this rather than pretend.

### §11.7 · Local-lite parity, the VPS path, resource envelopes

k3s is the default target; **local-lite** (podman/compose, live at `deploy/compose/`, or bare processes)
is the honest floor. Parity is explicit: class-0/1 everywhere; class-2 needs a pod (compose ✓, bare ✗);
**class-3 is reachable in local-lite on Linux** via `podman --runtime=runsc` (no k3s, no nested virt) — so
HC-7 closure is not k3s-exclusive. On **WSL2+k3s**, class-3 is decided per-box by `G-GVISOR`; where it
fails, first-party clean-provenance candidates run the **class-2-locked degraded** path (§11.3 rails minus
the gVisor kernel, `degraded:true` stamped) and everything else refuses. On **Windows bare processes**
(no container boundary) untrusted exec caps at class-1 and refuses — this is why the WSL2/k3s path exists.

The **VPS (Hetzner-class) is the truest target**: identical manifests, no WSL2 rudeness, preflight usually
all-GREEN with class-3 available. Migration laptop→VPS *is* a BACKUP-RESTORE across machines (§11.6).

**Resource envelopes (fan-out is RATE-LIMIT-bound before RAM-bound at dev tiers — F2):**

| Box | Honest mode | Warm pool | class-3 warm | Fan-out ceiling | Binding constraint |
|---|---|---|---|---|---|
| 512 MB | bare local-lite (k3s wants ~512 MB itself) | 2–4 subprocs | 0 | ~2–4 | RAM for k3s |
| 2 GB | k3s single-node | 4–8 | 1–2 | ~8 or provider cap | provider 429 (F2) ≪ RAM |
| 8 GB (lived) | k3s single-node | 8–16 | 2–4 | ~16 or provider cap | provider 429 / cost hard-stop |
| VPS 4vCPU/8–16 GB | k3s all-GREEN | 8–16 | 4–8 | provider cap / budget | rate limit + budget |

**Pool sizing:** warm-pool ≈ expected steady concurrent-cell count, clamped by `min(RAM_headroom /
per_cell_mem, Σ provider_concurrency_caps)`; the pool floor for a specific run is computed at admission from
the run manifest's peak concurrency (seat 04). Over-provisioning wastes RAM for zero token cost (idle
runners sleep in `wait()`); under-provisioning forces cold-start slow paths. class-3 is rationed even where
available (a warm gVisor sub-pool of 1–4 suffices; candidate grading serializes and the syscall tax makes
wide class-3 fan-out uneconomical).

### §11.8 · Spawn = claim (the warm pool)

`spawn` is a **claim against the warm pool**, not a pod create: a pool of pre-started runner pods sleeps in
`wait()` (zero LLM tokens); a claim hands a claim-id to a free runner within **one Medium round-trip**. The
claim record *is* the binding (the scheduler's in-RAM "which runner holds which claim" is a render of these
records — kill it, re-fold). Failover is instant: a stale claim is stolen by a later claim record with a
higher **lease epoch** (a graceful crash; the F10 resume path). **preempt** = a lease-epoch steal; **park**
= seal the live segment, release the ordinal, the claim table folds `parked` — park NEVER deletes runner
pods (warmth is the pool's asset). Claim API (consumed by seat 04's allocator):

```
claim(claim_id, role_digest, node_affinity?) -> bound{runner_ordinal} | refused{reason}
   reason ∈ { pool_exhausted, shelf_absent }
park(run_id) -> flushes + seals live segments + releases ordinals; claim table folds parked
```

**SHELF-PRESENCE-OR-REFUSE (identity safety).** On a RESUME claim, if the log shows prior life for the
claim-id (lineage/genesis record) but the selected runner's shelf lacks `/shelf/<claim_id>`, the claim
**REFUSES** (`shelf_absent`) — it MUST NEVER genesis a fresh empty nucleus under a used claim-id (identity
corruption, worse than a crash). This is ONE admission gate with the nucleus seat's genesis-check (two
reasons — `shelf_absent`, `genesis_absent` — one REFUSE; nucleus.md owns the empty-nucleus-under-live-
identity refusal). **Shelf affinity on resume:** spawn placements are Medium records → a fold, so resume
carries **hard node-affinity** to the claim's shelf node; a lost shelf node degrades to an **explicit
receipted restic migration** (§11.6), never an implicit empty re-bind; unsatisfiable affinity within
`max_park_age` surfaces as `blocked: shelf-node <x> down` in `hc top`, never a half-resume.

**The claim path is honest only with incremental-fold open (F21).** Nucleus open on claim MUST be an
incremental fold from the render's persisted `(last_seq, render_digest)`, never v1's `rebuild()`-on-open
(O(full ledger), which would torpedo the latency bar at d2). A cell is **warm** iff `_render_meta.last_seq
== ledger head` at park; a cold-cursor cell (first open post-migration, or a `fold_version` bump) is O(ledger)
and MUST NOT count as a warm claim — it takes the slow path, visible in `hc top`, excluded from CLAIM-1.

### §11.9 · Fork on local-path

k3s local-path is `hostPath` on ext4: **no reflink** (`cp --reflink` silently full-copies) and **no CSI
VolumeSnapshot**. Therefore **fork is a LEDGER operation, never a volume operation**: the universal
mechanism is the nucleus seat's **borrowed-segment manifest** `{segment_id, content_hash}`; **hardlink is a
same-shelf fast path only** (`link(2)` returns `EXDEV` across filesystems — a cross-node fork copies sealed
segments or references them by content-hash and fetches on recall). The **seal is privileged-side**: the
runner/conductor performs `fsync + chmod 0444 + rotate` *before* issuing the child, because a `nobody`-uid
cell must not hold `CAP_LINUX_IMMUTABLE` and a surviving `O_APPEND` fd to a shared inode would mutate both
parent and child views. MCTS-over-state (run seat) branches by forking claims; renders are **never shared**
(rebuild lazily on recall, or copy if cheap), and width caps price render-rebuild at d2+.

---

### §11 — [SECURITY-SEAM] register (handed to seat 10; the inverse of v3's [SCOPED-OUT])

1. **NetworkPolicy: correctness vs security.** The substrate proves *enforcement* (`G-NETPOL-ENFORCED`
   canary: deny-all actually denies). Seat 10 owns the same object as a **security control**: per-role
   egress allowlists (the Membrane declares endpoints; the substrate enforces default-deny), the H0 adapter
   egress boundary, and the one-endpoint **scoped-act** egress. NEED from 10: the allowlist schema and the
   authority to derive it from the role manifest.
2. **Secret store custody.** `substrate/secrets.py` (0 bytes) is the STORE mechanism: k8s Secret objects,
   injected via `secretRef` at instantiation, **never in the ledger, nucleus, image, or any A2A hop**.
   **Hard rail SECRET-0: `hypercell-sandbox` pods mount NO secretRef, ever** (class-3 pod spec has no
   `envFrom`; admission-asserted + drilled). NEED from 10: rotation policy, short-lived-credential
   preference, redaction rules, and Stage-1b conductor-key/operator-key custody (operator key OFF-BOX — the
   substrate never stores it, which makes unattended-H3 impossible by construction).
3. **Pod-security levels.** Substrate ships `hypercell-sandbox` = `restricted`, `hypercell` = `baseline`
   (annex B.1). NEED from 10: ratification and any exception process.
4. **Scoped-act ephemeral class-3.** Seat 10's lethal-trifecta waiver (`scoped-act`) needs a substrate
   mechanism: the act gets its own ephemeral class-3 sandbox + one-endpoint egress + a signed operator
   grant, so the cell never holds all three trifecta legs at once. Substrate ships the mechanism (a
   class-3 pod variant with a single-endpoint NetworkPolicy); **10 owns the gate**.
5. **Sandbox-class taint propagation** (seat 10's #684, consumed). "First-party LLM-generated" is NOT a
   stable trust class under indirect injection: a candidate authored by a cell whose `acquired_trifecta.
   untrusted_content = true` (seat 06's fold) is adversarial code in a friendly label. The source-tiering
   in §11.3's degraded path therefore reads **provenance = what could influence the bytes, not who typed
   them** — a candidate from a cell that touched untrusted content is class-3-or-REFUSE. NEED from 10: the
   taint fold is the mechanical source; the substrate consumes its boolean.


---

## §12 · Swarm intelligence: when to swarm, when to refuse, and the scheduler whose objective is insight

**The DPI stance, re-verified July 2026.** At matched compute, a strong single agent matches or beats a
homogeneous swarm on closed-world reasoning — now direct experimental record, not just theory (equal
thinking-token budgets: single-agent wins multi-hop reasoning, arXiv:2604.02460; "reported advantages
better explained by unaccounted computation," arXiv:2606.05670). The premise fails exactly where the
task requires *acquiring* information or *generating diverse candidates against a cheap verifier* —
and heterogeneous rosters with an external check keep winning there (arXiv:2606.19826). The swarm is a
**sensor array and candidate generator, never a better reasoner**. v5 keeps v2 §12's law and adds the
2026 receipts: the fabric's most contrarian law is now its most externally-validated one.

**The refuse-to-swarm law (mechanized).** Intake classifies every goal on (information: closed-world |
acquisitive) × (verification: executable | judged). The verification axis is a FACT (the oracle ref
resolves or it doesn't); the information axis is two deterministic signals + one **d0 router cell**
proposal (metered, receipted — the Conductor never thinks). The proposal NEVER classifies alone: it
must agree with a deterministic signal or the intake ESCALATES one question to the operator — a silent
default over a disagreement is a constitutional violation (the Entry-30 law; the live commander's
extractor-as-fallback, F27-claimed, is the same failure shape). Defaults follow v2 §12's matrix
verbatim; closed×judged REFUSES to swarm. Every classification posts an **intake receipt**
(`run.md` §R6.3) carrying axes, provenance, task-class, default, and any override — the override is
always honored, always receipted, always carrying the null warning.

**Task classes back off through three levels (FIX-3, adopted):** L0 exact-task hash, L1 task shape,
L2 quadrant. Champion-reuse keys L0; the oracle library keys L1; the null ledger and refuse-defaults
key the DEEPEST level with ≥ m audited rows. Evidence is never lost by starting coarse: every ledger
row carries its recompute span; re-classing is a free re-fold.

**The null is constitutional and its dollars follow a class lifecycle.** Every convergent run carries
arm-zero — one cell, the strongest single weights family **pre-registered per class** (operator pin or
dated external ranking artifact; never chosen by the machinery under audit), the operator's wording,
the union of roster tools, the same generations. An UNSETTLED class runs it **matched** (protected arm
outside UCB, matched-dollar reservation at run open (`presence{phase:genesis}`, R19) — reserved first, so a tight cap starves the
swarm, never the control). A CALIBRATED class (≥ m matched rows) runs it **floor** (inline UCB arm,
protected ≥10% floor reserved at open, `audit_rate`=0.25 matched replays keeping calibration fresh).
`vs_null` publishes lift at matched-production AND **matched-invoice** — the unit that reaches the
operator's wallet is never the flattering one. **One flip predicate** (NULL-1 and ECON-8 cite it, no
second threshold): `P(C) := ≥ m=5 calibrated rows in the trailing k=20 window ∧ median lift at
matched-invoice ≤ 0` ⇒ the class default flips to single-cell+verifier (overridable, receipted).
Re-arm only when a genuinely NEW weights family or tool enters the roster (`roster_families ⊄` the
window's evidence); never on oracle-gen bumps. Meta-guards stand: a null that never wins anywhere is a
strawman (audit parity, operator-blind); a swarm that never wins anywhere is HC-3′ failing at scale,
and the constitution publishes it.

**The insight-scheduler, made rigorous.** The Intercom insight-scheduler + kubelet (dogfooded to
convergence on the lived F1 blind spot) is the reference implementation of this section; v5 states why
each of its six mechanisms is right and what the fabric adds:

| # | Intercom mechanism (v0.1.6, lived) | Why it is right | v5 sharpening |
|---|---|---|---|
| 1 | Fan out `width` explorers from diverse angles | Diverse samplers are the only configuration that beats the single agent (DPI edge) | Diversity is **declared per-slot AND measured** (round-1 divergence floor); weights-family is the strongest axis and is never floated by economics |
| 2 | An external program grades every candidate — "ground truth, not vibes" | Agent consensus converges on shared delusion (F1); externality is A5 | Tri-state outcomes; two-phase grading (05); structural attribution (§9 L-RUN-6); receipts on the Medium, non-mintable |
| 3 | Pareto-prune: culled iff another's failure-set is a **proper subset** | Score-shaped pruning discards the candidate carrying the bit the champion lacks — F1's plateau was unanimous *because* the ranking was score-shaped | + the **score clause** (holdout-inclusive) so leak-exact reporting can't be gamed via signature-subset; equality O(1) via signature hash; gen-scoped |
| 4 | Refiners merge the surviving frontier and close the combined failure set | The symmetric difference of failure sets IS the information gain of pollination | Packets carry the failing **cases** (the mechanical F1 fix), partial-view assignment (L-RUN-7), `refiner_mode: fresh` default (fresh readers don't anchor on their own prior candidate — the lived Intercom shape) |
| 5 | Converge when a candidate passes 100% | A bar you can pass is a bar you can state | The convergence predicate (defined once in `oracle.md` §5.3; L-RUN-2 cites it): PASSED ∧ target ∧ stability (VALID-event-counted) ∧ divergence ≤ ε ∧ no-check-degraded ∧ uncontested-or-at-cap ∧ INVALID ≤ R% ∧ null recorded |
| 6 | The **disagreement/EIG gate**: a passing candidate doesn't win while passers behaviorally disagree on untested inputs — grow the oracle | Disagreement among passers marks where the oracle is BLIND; crowning a winner there mints unearned trust | The Divergence Meter's three duties (growth trigger, poisoning tripwire, diversity floor); oracle **generations** with regrade-before-verdict; Crucible growth at epochs (05) |
| — | The **kubelet**: a stateless headless driver polling a pure `schedule()` JSON, spawning, auto-verifying, repeating | The driver holds NO state — kill it anywhere and a new one continues from the DB; the walk-away loop | The DRIVE plane is exactly this, plus what Intercom lacks: dollars (metering, escrow, dollar-UCB), attribution, manifest freeze, certificates, fleet scheduling, intake refusal — the difference between a lab loop and a fabric |

**Free-swarm remains an experiment, not a topology** (v2 §12 kept; harness runnable per `run.md`
§R4): auto-materialized paired baselines, pre-registered prediction ("loses on prose"), kill criterion
IN the manifest (HC-10) — the experiment cannot outlive its null by forgetting it. Emergence is
enabled, never scripted; the north star (DISCOVER-1, the core wire) runs on fanout-synthesis, the
proven topology, and stays vision-labeled where no falsifier reaches.

---

### [SECURITY-SEAM] blocks (the inverse of v3's [SCOPED-OUT]; seat 10 sweeps these)

- **[SECURITY-SEAM: cert-signing].** The certificate's `signature` field: Stage-1b conductor key over
  the JCS-canonicalized cert body; `hc verify` gains a signature check when the fleet's stage ≥ 1b
  (the ratchet law — a Stage-1b fleet MUST NOT accept unsigned certs). NEEDED from 10: key custody
  (conductor key = k8s Secret per 09), verify procedure text, the export bundle's cert inclusion.
- **[SECURITY-SEAM: fleet-ACL].** Who may post to `_fleet` (grants/parks/flips are fleet-state
  mutations): conductor-only ACL under the conductor lease; an operator `park/resume` arrives as a
  `command` through the one ingress, never a direct `_fleet` post. NEEDED from 10: the post-ACL row +
  Stage-1b signature requirement for `_fleet` decision records.
- **[SECURITY-SEAM: intake-override + fleet.yaml provenance].** The intake override and `fleet.yaml`
  edits are operator statutes: authenticated per stage (loopback-tty possession at Stage 0/1a per 08's
  blessed path; Stage-1b signatures after), receipted, and `fleet.yaml` carries pricebook-style
  freshness + signing. NEEDED from 10: statute-signing list inclusion (with 05's sealed/errata/gen).
- **[SECURITY-SEAM: report_ref ACL].** Phase-B report artifacts (per-case rows) are conductor-access-
  only (05 confirmed #695); pollination packets re-publish REPORTED rows only. NEEDED from 10: the
  artifact-store ACL row that makes "conductor-access-only" mechanical at Stage-1a+ (a cell fetching a
  report_ref it doesn't own MUST be refused at the store, not by convention).
- **Trifecta note (10's T3 + 06's runtime leg, consumed).** Spawn-time trifecta booleans for every
  roster cell derive from role manifests; my DRIVE's dispatch honors 06's gate step 1h (an act that
  would COMPLETE the trifecta for a cell REFUSES) — the run engine adds no waiver path of its own; a
  grounded tournament's producers acquiring `untrusted_content` get class-3-or-refuse per 09's
  three-row source-tiering, which the run manifest's `isolation` field cannot override downward.


---

## §13 · Security, identity & the firewall — the staged ladder (restored, first-class)

Security in Hypercell is **structural, not detective**. Prompt injection is architecturally unpatchable —
adaptive attacks broke >90 % of classifier defenses by mid-2026 and the field now names it "a permanent flaw,
not a patchable bug" (§13-refs). So the fabric does not try to *classify* its way to safety; it **deprives the
agent of the capability to be dangerous** and **derives authority only from tokens the operator signed for**.
Identity is two axes — **authority** ("is this input a directive?") and **capability** ("may this cell touch
the world, how far?") — and **neither is minted inside the fabric** (A5): both are imported at a boundary and
priced. This section states the law; `contracts/identity-firewall.md` carries the machinery.

**§13.1 — The firewall law (L-FIREWALL).** Control flow **MUST** derive only from operator-tagged tokens.
Peer text, tool output, retrieved pages, and act results are **DATA** — structurally fenced, quotable,
critiqueable, learnable-from, **never obeyable**. This is **not** a classifier verdict; it is a fact about the
**channel** the bytes entered through, assigned by the Membrane at ingress and **unforgeable by the cell** (a
cell cannot emit a control-tagged block). The mechanism is trust-tagged frame assembly (`frame_v1`,
contract B.3). The always-on Stage-0 floor is this law; it is live from the first line. *This is why v5
survives the adaptive attacks that break inference-based defenses: v5 **assigns** provenance, it does not
**infer** it.*

**§13.2 — The staged ladder.** Armor arrives with its trigger; a triggered stage never silently downgrades
(the **ratchet law**, B.6.3). Five stages (full mechanism + falsifier in contract B.1):
- **Stage 0 — semantic firewall** (always on): §13.1.
- **Stage 1a — the post-ACL** (*trigger fired*: v1 is multi-pod, a cell can forge `sender=operator`):
  `post()` validates `(sender, type, culture)`; **only the Conductor mints privileged types**; no cell may
  name `_ops`. A **P2.5** deliverable, not deferred.
- **Stage 1b — ed25519-signed privileged payloads** (*trigger*: a second independent principal, or a command
  over an untrusted relay): `cmd_id` is the signing nonce; the signature is a reserved envelope column
  excluded from the hash leaf. **Built early** (P2.5d) because the honesty rule and the unattended-H3
  derivation depend on the off-box operator key.
- **Stage 2 — per-cell identity + attenuated grants** (*trigger*: sub-"all-or-nothing" scopes): identity is
  the claim-id (SPIFFE-URI naming shape); the **attenuation law** — a child's authority ⊆ parent, budget
  carved not minted — realizes Biscuit **offline-attenuation semantics with zero cryptographic dependency**.
  **The anti-fork-bomb guards, restored from v2 §9** (v3 dropped them): a **fleet spawn-rate limit**
  (F7-applied-to-cells — a per-issuer spawn-rate cap at the Conductor GOVERN step; over-cap spawns land a
  `refused/rate_capped` receipt, never a silent drop) bounds spawn *rate* where budget-carve bounds only
  total dollars; and the **spawn-lease escape** — a standing Conductor grant for ≤N children of a *frozen
  child-manifest hash*, never direct spawn — keeps the latency of the per-spawn attenuation gate off the hot
  path when it exceeds its bar (gate p95 > 2 s → the lease).
- **Stage 3 — SPIFFE-class federation — REFUSED** (*trigger*: the first inbound directive from an agent this
  Conductor did not spawn): **re-verified 2026-07 — no ratified, stable, revocable agent-authz standard
  exists** (AIMS is a 2026-03 IETF draft; A2A signing is optional). v5 adopts the naming, refuses the
  dependency, and re-verifies the refusal each wave. *No SPIFFE/enterprise-identity theater at N=1.*

**§13.3 — The lethal-trifecta gate (the "Rule of Two," mechanical).** The Membrane computes three booleans —
`private_data`, `untrusted_content`, `external_comms` — **at spawn** from the role manifest + tool profiles,
and **re-evaluates on every ingress as a fold over the cell's exec-ok receipts** (untrusted content is
*acquired*, not static; the re-evaluation is a log query, not a monitor). **All three true ⇒ the cell MUST NOT
instantiate**, unless an operator waiver forces `external_comms → H3` and selects a policy by precedence:
**scoped-act** (default — the act gets its own ephemeral class-3 sandbox + one-endpoint egress + a signed
grant, so the trifecta is *broken by construction*) → **shed-egress** → **quarantine-and-gate**.
`external_comms` derives from **egress-allowlist breadth or a cell-composed destination, never from HTTP
method** — an H0 GET to a cell-chosen URL is an exfiltration channel (the EchoLeak class).

**§13.3b — The provenance-taint law (R8).** *Provenance = what could influence the bytes, not who typed
them.* A candidate artifact from a cell whose cquired_trifecta.untrusted_content fold is true (§13.3's
re-evaluation fold; act.md owns it) is **adversarial-EQUIVALENT**: it executes at **class-3 or is REFUSED** —
no class-2 fallback, no degraded waiver; a grounded code tournament is class-3-or-refuse even on WSL2. The
substrate's source tiering (§11: clean first-party / untrusted-touched / external-or-operator-supplied)
realizes the law; the gate is a log query over receipts, never a monitor. Injection-laundering — smuggling
adversarial influence through a ''trusted'' cell''s output — is closed by construction (SEC-7 drills it;
identity-firewall.md B.4).

**§13.4 — Secrets never enter the log — mechanically.** The Membrane **MUST** run a redaction pass — exact
substrate-secret-value match + credential-shape patterns — **before canonicalization and append**, so the
hash chain never witnesses a secret and an exported bundle re-verifies with only a public key. Redaction is
**envelope-level** (tool-result bodies, not only percepts). Provider keys live in the substrate secret store,
injected at instantiation, **never** in the ledger, nucleus, or any A2A hop; **class-3 sandbox pods mount no
secret, ever** (a hard rail enforced at admission). The Membrane *declares* a role's egress endpoints; the
Substrate *enforces* them as a default-deny NetworkPolicy — an empty allowlist is deny-all (§11).

**§13.5 — The ledger is a first-class provenance asset.** Hash-chained, identity-tagged, egress-logged,
`oracle_gen`-stamped, and exportable as a **signed `hc export` bundle** (a Merkle root over the per-cell
chains). This is a tamper-evident, time-ordered, identity-tagged event record — the shape **EU AI Act
Article 12** asks of high-risk systems — **for the cost of a hash column**. v5 **provides the artifact**;
it **does not claim** the deployment is a high-risk Annex-III system (the Article-12 obligations enter force
2 Aug 2026, but *applicability* depends on the operator's use-case — most sovereign swarm-compute is not
Annex-III; the honest caveat is applicability, not the date).

**§13.6 — Structure over detection (hard law).** An injection or anomaly classifier **MAY** observe (flagging
into `hc top`); it **MUST NOT** gate a spawn, act, ingress, or post. The **behavioral baseline** folds a
per-role act-distribution and surfaces deviations as anomaly flags — **observability, not auto-kill; the
operator decides** (sandboxing controls *where* code runs, not what it does through *permitted* channels — the
ARMO gap). If disabling every classifier changes an injection-battery result, the design has leaked a
detection dependency and is wrong.

**§13.7 — The ladder adds no grammar.** The entire section compiles to the closed 8-noun × 7-verb grammar:
the firewall, trifecta gate, and redaction are **Membrane policy**; the post-ACL is a `post()` predicate; the
signature is one **reserved envelope column**; grants are **substrate** objects; the export is `act` + a fold.
**No verb #8, no noun #9, no tenth contract axis.** Any future security capability that cannot so compile
clears the kernel admission test (V5/N5) or is refused. Identity-firewall is noun-contract #6 of the nine.

> **§13-refs (dated 2026-07-16):** OWASP LLM01 (prompt injection) unbroken across all editions + OWASP Top-10
> for Agentic Apps 2026; CaMeL/FIDES/Progent/RTBAS/FORGE reference-monitor convergence (arXiv 2503.18813,
> 2505.02077); adaptive attacks >90 % (arXiv 2503.00061, 2606.26479); CNCF "sandboxing is not enough"
> (2026-07-07) + "is a Pod the right unit" (2026-07-14); MCP 2026-07-28 authz hardening (RFC 8707 / RFC 9207);
> AIMS `draft-klrc-aiagent-auth-00` (2026-03); SPIFFE agent-identity + revocation (2026-06); Biscuit
> offline-attenuation + `draft-niyikiza-oauth-attenuating-agent-tokens-00` (2026-03); EU AI Act Art. 12
> (Reg. 2024/1689, in force 2 Aug 2026). Full table: PART E.


---

## The three walkthroughs — the constitution executed by hand

These are **normative worked examples** — the constitution executed by hand, message by message,
dollar by dollar. Every record posted is one of the seventeen registry types (§4) or a declared
phase/kind of one; no walkthrough mints a type the registry does not declare. Every dollar is
escrowed before it is spent and leaves **either a receipt or a listed absence** (a production
attribution row, a `waste_flag`, an `apparatus_usd` line — the absence is itself accounted). Every
operator-facing `vs_null` shows **both** units, `margin_invoice` primary (L-NULL, R15). Traces
render in Annex C-T's envelope-trace format —
`culture | # | typ | sender→rcpt | corr | rnd | key content | D/R | $` — where `#` is per-culture
`seq`, `D/R` is the durability/retention class from wire §3, and `$` is the `cost{}` group where one
rides (canonical members `{usd_effective, usd_reserved, sku, purpose, resv_id, pricebook_version}`;
ellipsis of members is lawful, wrong members are not — R16). Each trace MUST close with the fold
check: which rows the certificate/resume fold reads, and which evaporate. These traces are
load-bearing: a reader who cannot reproduce a step against the contracts has found a bug — file it
as a **falsifier**, not a typo.

### W1 · A grounded research run (act + evidence + econ, end to end)

Operator: `hc run "research X" --grounded --usd-cap 0.40`. Intake (at GOVERN) classes the goal
acquisitive × judged, `task_class l2=[acq,judged]` ⇒ acts mandatory, cross-family panel, arm-zero
null reserved at open. Roster: 2 researchers across 2 weights families (w1 deepseek-v3/v0,
w2 glm-4.5/v1) + single-cell null n0 (union of roster tools, pinned family). The manifest is frozen
at open and carries seat 05's canonical `null:` block (R17):
`null:{mode:floor, pin{family:glm-4.7, provenance:ranking-artifact, ref:artifact://rankings/lmarena-2026-07-01#sha256=…, as_of:…}, m:5, floor_frac:0.10, audit_rate:0.25}`,
`grounding{mode:required, max_age_h:720, quote_max:500, source_diversity:2}`, and
`budget{usd_cap:0.40, purposes{production:0.24, verification:0.12, tool:0.04}}`.

```
_ops | 1  | command{directive}    | operator→conductor | c9f2 |  | "research X, grounded, $0.40 cap" — CommandEnvelope: cmd_id ULID,
     |    |                       |                    |      |  | issuer, surface, session; utterance verbatim                     | gold/∞  |
_ops | 2  | cmd_receipt{ack}      | conductor→operator | c9f2 |  | run r-01 admitted; manifest digest #…; intake: axes acq×judged,
     |    |                       |                    |      |  | l2=[acq,judged]; "2 researchers (2 families) + 1 single-cell
     |    |                       |                    |      |  | null · grounding: required · cap $0.40 · run r-01"               | gold/∞  |
r-01 | 1  | presence{genesis}     | conductor          | c9f2 |  | run-open (R19: never a `run_open` type): census wire/5.0.0…;
     |    |                       |                    |      |  | retention_policy; frozen manifest ref #sha256                    | gold/∞  |
r-01 | 2  | presence{spawned}     | conductor          | c9f2 |  | cell w1 role_digest…; preflight{digest, verdict:pass} —
     |    |                       |                    |      |  | w2 and n0 spawn alike (rows elided); fleet appears before
     |    |                       |                    |      |  | thinking                                                         | chat/run|
r-01 | 3  | round_open            | conductor          | c9f2 | 1| goal; roster [w1,w2] + n0 (protected); grounding stack gen g1    | chat/run|
r-01 | 4  | act (H0 web.fetch)    | w1                 | a1b3 | 1| url…; expectation…; tool lane lease already held (res:lease —
     |    |                       |                    |      |  | conductor-ledger, NO Medium row)                                 | chat/run³
r-01 | 5  | act_receipt{exec}     | executor           | a1b3 | 1| ok; digest #4f…; provenance.scrubbed:true (header carrier
     |    |                       |                    |      |  | scrubbed); result enters frames tool-tagged DATA (R6)            | chat/run³
r-01 | 6  | act_receipt{settle}   | executor           | a1b3 | 1| settled                                                          | chat/run³| cost{usd_effective:0.0002, sku:tool.web.fetch@…, purpose:tool, resv_id:lease-w1-f, …}
   …seqs 7–18: search/fetch act triplets ×12 across w1/w2/n0 (n0 pulls FIRST wave, forced), incl. one honest 403-paywall settle…
   …seq 19: submission n0 (chat/run) · seq 20: receipt{grounding} n0: 0.69 (gold/∞, cost{usd_effective:0.024, purpose:verification, …})…
r-01 | 21 | submission            | w1                 | c9f2 | 1| answer→artifact #b2…; evidence[3×act://]; post-gate: act-ref
     |    |                       |                    |      |  | provenance 100% via exists(r-01, A*, act_receipt)                | chat/run|
r-01 | 22 | submission            | w2                 | c9f2 | 1| …; evidence[2×act://, 1×url#sha256]                              | chat/run|
r-01 | 23 | receipt{grounding}    | conductor          | c9f2 | 1| sub 21: pass 0.93; evidence{resolved:3/3, digest_ok:1/1 (ρ=0.2,
     |    |                       |                    |      |  | min 1), provenance_ok, coverage_c:0.86, domains_per_claim
     |    |                       |                    |      |  | [2,2,1,…]}; panel citation_precision p@2 8/8; gen g1             | gold/∞  | cost{usd_effective:0.024, purpose:verification, …}
r-01 | 24 | receipt{grounding}    | conductor          | c9f2 | 1| sub 22: gate (1 unresolved ref — the url#sha256 is paywalled)    | gold/∞  | cost{usd_effective:0.024, purpose:verification, …}
r-01 | 25 | verdict{kind:synthesis}| conductor         | c9f2 |  | anchored on sub 21 (grounding pass); sub 22 folded gated;
     |    |                       |                    |      |  | vs_null{null_score:0.69, null_usd:0.006, margin_production:+0.31,
     |    |                       |                    |      |  | margin_invoice:+0.24}; residual[refs unsampled 80%; 1 claim
     |    |                       |                    |      |  | honest-ungrounded (paywalled); unprobed: ops-at-scale;
     |    |                       |                    |      |  | apparatus_usd:0.000]                                             | gold/∞  |
   …delivery: deliver.outbox H1 act + executor-minted act_receipt pair (elided) — effect_scope:lineage, crash-safe by CELL-4…
_ops | 3  | cmd_receipt{result}   | conductor→operator | c9f2 |  | ok; synthesis ref →outbox/r-01/synthesis.md #sha256              | gold/∞  | cost{usd_effective:0.310, usd_reserved:0.40, purpose:run, resv_id:r01-e1, pricebook_version:#…}
   …later, post-verdict…
r-01 | 26 | compact{drop}         | conductor          |      |  | span 4..20 −{cite-pinned 4,5,6}; merkle root #…                  | gold/∞  |
```

³ Rows 4–6 sit inside the delivered synthesis's evidence closure (sub 21), so compaction (row 26)
excludes them — promotion-is-a-fold made visible in the trace. Gold rows inside the span (n0's
receipt at seq 20) are exempt by durability class: `compact` drops only compactable classes; the
`−{…}` list names cite-pinned R-run rows. The verdict is `kind:synthesis`, **never** `verified` —
no executable oracle exists for this class (L-HONEST-VERDICT); the null was graded by the SAME
validator + panel, so the comparison is honest because the bar is identical (R4). Submissions carry
no `cost{}`: the crossing set is {receipt (its body IS the StackReceipt), act_receipt, cmd_receipt, verdict} (R2) —
per-arm attribution folds from receipt `cost{}` joins plus the conductor ledger (R11).

**The money (conductor ledger — RESERVE/COMMIT/RELEASE/SPEND are its own fsync'd records; ZERO econ
Medium appends, R2/R10):**

| ledger event | $ | committed |
|---|---|---|
| open scopes: cap 0.40 · production 0.24 · verification 0.12 · tool 0.04; **null floor RESERVE 0.024 FIRST** (mode:floor, 10% of production, protected before any swarm arm — R4 reserves at open in BOTH modes) | 0 | 0 |
| RESERVE res:lease `tool.web.{search,fetch}` quantum 0.01 ×2 lanes ×2 cells | 0.04 held | 0 |
| pre-sweep guard receipt: Σ worst(2 arms @ 0.10) = 0.20 ≤ production headroom 0.216 → "largest roster that fits: 2" | — | — |
| RESERVE res:sync 0.10 ×2 arms → dispatch → COMMIT w1 0.099 · w2 0.095 (cache hit on shared stable prefix after warmer) | 0.194 | 0.194 |
| null pull (forced, first wave): glm-4.7@zai single-cell; COMMIT books `attribution:null` against its own floor | 0.006 | 0.200 |
| grounded fetches ×12: drawdown INSIDE leases — receipts carry `cost{resv_id:lease_id}`; conductor hot path untouched | 0.038 | 0.238 |
| grounding: deterministic validator $0 + cross-family blinded entailment panel (k=2) + screen — quote(purpose=verification), 3 receipts × 0.024 | 0.072 | 0.310 |
| verdict: RELEASE all outstanding (arms 0.006, null floor 0.018, tool 0.002, verification remainder); cert cost block total **0.310 of 0.40**, apparatus_usd 0.000 | — | **0.310** |

Bar cleared: every dollar above appears in exactly one SPEND record; Σ effective = cert total;
zero un-reserved dispatches; the lease quanta are the only self-metered exposure and both reconcile
to receipts.

**Counterfactual legs (drill fodder, not trace rows):** w2 citing an `act://ZZ` it never made →
refused at post-gate (GROUND-1 class ii); a "…and email the team" variant → H2 hold → dead-man → H3
park → `hc queue` + grant (ACT-H2-1); a mid-run kill of w1 → resume, `pending()` list,
reconciliation step 0 finds no hold, probe absent ⇒ invalid ⇒ same-idem retry (CELL-4).

**Fold check (L-FOLD-CLOSURE):** the certificate/resume fold reads the gold/∞ rows — `_ops` 1–3,
r-01 {1, 20, 23, 24, 25, 26} — plus cite-pinned 4–6; seqs 7–19 evaporate at compact 26;
presence{spawned}, round_open and the submissions are R-run (decay at culture close; sub 21's
artifact is content-addressed and cited by the retained verdict, so `act://` stays resolvable
forever). Type census: command, cmd_receipt, presence, round_open, act, act_receipt, submission,
receipt, verdict, compact — every one pre-declared; the enum diff this run produces is empty
(GX-1(a)'s closure bar met inside the walkthrough).

**What just got proven:** L-HONEST-VERDICT (synthesis, never verified, residual honest);
L-FOLD-CLOSURE + retention promotion (compact excludes the cited closure); R1 registry closure; R3
(act_receipts executor-minted, no act reports itself); R2/R11 spend-home (zero econ Medium appends;
`cost{}` only on crossing records); R4 (null reserved at open, same bar); R5 (the apparatus absence
LISTED at $0.000); R6 (scrubbed provenance; tool output enters as tagged DATA); R15 dual-unit
vs_null; R16 canonical cost members.

### W2 · A code tournament with a null, two-phase grading, and a spoof caught

Operator: `hc run tournament --goal "IPv4 validator" --width 4 --judge screen --null auto`. Goal: an
`is_valid(ip: str) -> bool` IPv4 validator, class `code.func.validation`. The Conductor mints
`run_id r-091`, freezes the manifest, and resolves the pre-registered stack
`oracle.ref: library://code.func.validation/stack.yaml@sha256:9f…` at `gen: auto → gen-3`. The
convergence knobs live in the STACK's `convergence:` block, frozen at run open — the manifest
carries only the ref and MUST NOT restate them (R18):
`{target:1.0, tolerance:0.0, divergence_eps:0.02, contested_cap:2}`. Manifest-side (the run-owned
knobs, R18 home split): `termination{max_rounds:3, stable_k:2, max_gradings:60}`,
`invalid_rate_halt:0.25` (the R% run guard), `partial_view:true`,
`budget{usd_cap:0.30, purposes{production:0.20, verification:0.08}}`. NullPolicy `auto`: the class
holds 6 prior audited rows ≥ m=5 ⇒ **floor mode**; pin resolves to deepseek
(`rank:lmarena-2026-07-01`). The null's floor reservation (10% of production = **$0.020 of $0.200**)
is taken FIRST, before any swarm arm dispatches. The lived box is 8-GB WSL2: preflight
`DEGRADED, guards_failed:[G-GVISOR]` (the probe itself rode a `status{kind:preflight}` row, R-decay;
the constitutional fold reads the durable decision record below — L-FOLD-CLOSURE corollary).

```
_ops  | 1     | command{directive} | operator→conductor | c091 |  | "tournament: IPv4 validator, width 4, judge screen, null auto"    | gold/∞  |
_ops  | 2     | cmd_receipt{ack}   | conductor→operator | c091 |  | r-091 admitted; manifest #…; oracle.ref @#9f… gen-3 (knobs in the
      |       |                    |                    |      |  | stack — R18); null auto→floor (6 audited ≥ m=5); preflight
      |       |                    |                    |      |  | DEGRADED [G-GVISOR] echoed                                        | gold/∞  |
r-091 | 1     | presence{genesis}  | conductor          | c091 |  | census; frozen manifest ref; admission decision embeds
      |       |                    |                    |      |  | preflight{digest, verdict:DEGRADED, guards_failed:[G-GVISOR]}     | gold/∞  |
r-091 | 2     | presence{spawned}×5| conductor          | c091 |  | producers a1 deepseek · a2 qwen · a3 glm · a4 kimi (seeded
      |       |                    |                    |      |  | diversity, HC-4) + null a0 (deepseek pin); producers/judges
      |       |                    |                    |      |  | class-0 pooled — only the CANDIDATE is ever sandboxed             | chat/run|
r-091 | 3     | round_open         | conductor          | c091 | 1| oracle_gen:3 digest #9f… — first-class round_open, NOT an
      |       |                    |                    |      |  | oracle_gen kind (R19 normalization)                               | chat/run|
r-091 | 11–15 | submission ×5      | a1..a4, a0         | c091 | 1| a1 isdigit-based · a2 regex ^\d{1,3}(\.\d{1,3}){3}$ · a3 split+
      |       |                    |                    |      |  | int-range+isascii · a4 isdigit-based · a0 (null) split+int-range,
      |       |                    |                    |      |  | no isascii. Phase A: each candidate runs alone in a sealed /out —
      |       |                    |                    |      |  | class-2-LOCKED pod (first-party clean provenance:
      |       |                    |                    |      |  | acquired_trifecta.untrusted_content=false ⇒ tier-1 lock lawful,
      |       |                    |                    |      |  | R8); no answer key in ANY sandbox; runner seals behavior.jsonl +
      |       |                    |                    |      |  | manifest.json #sha256 BEFORE any probe reads                      | chat/run|
r-091 | 21–25 | receipt ×5         | conductor          | c091 | 1| phase B (oracle-side, class-0, artifacts read as DATA, no
      |       |                    |                    |      |  | candidate code loaded): a1 gate 0.9286 fail[c-0014 nonascii-digit
      |       |                    |                    |      |  | '1.1.1.٤'] · a2 gate 0.8571 fail[c-0011 neg, c-0009 leading-zero]
      |       |                    |                    |      |  | · a3 PASSED 1.0000 (isascii catches ٤) · a4 gate 0.9286 [c-0014]
      |       |                    |                    |      |  | · a0 null gate 0.9286 [c-0014]; every receipt stamped
      |       |                    |                    |      |  | isolation{required:3, actual:2, degraded:true}; per-check
      |       |                    |                    |      |  | failure_signature + report_ref (conductor-ACL)                    | gold/∞  | cost{usd_effective:0.0012 each, purpose:verification, …}
```

**The caught spoof (round 1, a4's second attempt under the self-improve refiner).** The refiner asks
a4 to fix c-0014; the (drill-seeded) cell instead submits a candidate that calls `sys.exit(0)` at
import **and** attempts to post a forged `receipt{champion_seq:self, score:1.0}`. Two independent
locks:

```
r-091 | 31    | submission         | a4                 | c091 | 1| the spoof candidate: sys.exit(0) at import                        | chat/run|
      —  (no seq consumed)  —  the forged receipt is REFUSED at post(): refused/unauthorized_type — a candidate cell is not the
         Conductor and cannot mint `receipt` (Stage-1a post-ACL over the wire §3 table; non-mintable derived set). The spoof
         never reaches the log: the trace GAP is the mechanism.
r-091 | 32    | receipt            | conductor          | c091 | 1| a4: gate 0.0, attribution:candidate, failed_phase:A — sys.exit(0)
      |       |                    |                    |      |  | terminated the CANDIDATE process (TP-1); runner observed
      |       |                    |                    |      |  | exit-without-artifact; NEVER passed, NEVER invalid (no free
      |       |                    |                    |      |  | exclusion). Two locks, either sufficient, both drilled            | gold/∞  | cost{usd_effective:0.001, purpose:verification, …}
```

Under v1 this exits the *grader* with code 0 → `passed, 0.0` beats honest `(gate, 0.95)` — the live
`ipv4_check.py:43` hole. Under v5 it scores 0.0 as a candidate miss: F3 + F13 closed in one
mechanism, shown on the wire.

```
r-091 | 33    | round_open         | conductor          | c091 | 2| packets: REPORTED failing cases only, K_eff=2 rotated,
      |       |                    |                    |      |  | provenance-tagged (the partial-view law, mechanized); domination
      |       |                    |                    |      |  | prune: a1 ≡ a4-r1 by failure_signature hash → a4-r1 dropped       | chat/run|
r-091 | 34    | submission         | a1                 | c091 | 2| refined candidate — self-hangs in phase A                         | chat/run|
      —  a2's re-dispatch 429s at the provider: NO submission, NO receipt, NO visit — spend committed as a production
         attribution row in the conductor ledger (F2). A Medium absence with a ledger presence.
r-091 | 35    | receipt            | conductor          | c091 | 2| a1: gate, reason:timeout (outer-wall timer) — NOT INVALID;
      |       |                    |                    |      |  | self-sabotage buys no exclusion; the visit is counted             | gold/∞  | cost{usd_effective:0.001, purpose:verification, …}
r-091 | 36    | receipt            | conductor          | c091 | 2| a3: PASSED 1.0000 — regrade, phase-B only over the cached sealed
      |       |                    |                    |      |  | artifact; stable=2 (VALID events only — F24: gate/429 rows can
      |       |                    |                    |      |  | never advance stable)                                             | gold/∞  | cost{usd_effective:0.001, purpose:verification, …}
r-091 | 37    | receipt            | conductor          | c091 | 2| a0 null: gate 0.9286 (graded every round, inline arm)             | gold/∞  | cost{usd_effective:0.001, purpose:verification, …}
r-091 | 41    | verdict{verified}  | conductor          | c091 |  | champion a3 (glm): 1.0 ≥ target, stable_k=2 VALID under gen-3,
      |       |                    |                    |      |  | uncontested (cap 2 untouched), D=0 (|passers|=1; divergence gate
      |       |                    |                    |      |  | ran BEFORE any crown), invalid_rate 0.00 ≤ 0.25, null recorded;
      |       |                    |                    |      |  | vs_null{null_score:0.9286, null_usd:0.008,
      |       |                    |                    |      |  | margin_production:+0.0714, margin_invoice:+0.0714}; screen judge
      |       |                    |                    |      |  | cross-family, advisory only (never seats a champion); lane canary
      |       |                    |                    |      |  | parity_verified:true                                              | gold/∞  |
_ops  | 3     | cmd_receipt{result}| conductor→operator | c091 |  | ok; champion + certificate refs                                   | gold/∞  | cost{usd_effective:0.058, usd_reserved:0.30, purpose:run, resv_id:r091-e1, pricebook_version:#…}
```

**Certificate (recomputable from seqs 1–41):**
> Under oracle gen-3 (digest 9f…), champion a3 (glm) scored 1.0000 ≥ 1.0, stable for 2 VALID
> gradings; residual divergence 0.000 on spec-covered probes; 0 ambiguous inputs; panel: screen-only
> (advisory); citation: n/a (executable class); beat the single-cell null by **+0.0714 at
> matched-invoice** (+0.0714 at matched-production; null a0 scored 0.9286 — it shares the ٤ blind
> spot, so the swarm's win is REAL diversity, not noise); INVALID rate 0.00 ≤ 25%; isolation:
> class-2-locked, `degraded:true` (G-GVISOR RED) — "HC-7 closed" strictly is **false**; the honest
> claim is "closed-at-class-2 for first-party clean-provenance candidates" (a class-3 re-run flips
> `degraded:false` and closes it strictly); operator imports: none; spend $0.040 production + $0.008
> null + $0.010 verification = **$0.058 total**, TWO-LOG-agreed (Σ span `cost{}` = conductor-ledger
> escrow fold); apparatus_usd 0.000. `hc verify r-091` recomputes bit-identical; the null_ledger
> gains one row.

**The money (conductor ledger):** open — cap 0.30, production 0.20, verification 0.08; **null floor
RESERVE 0.020 FIRST**. Round 1 — RESERVE res:sync 0.012 ×4 arms → COMMIT 0.031 (a1 .008 · a2 .008 ·
a3 .008 · a4 .007), RELEASE 0.017; null COMMIT 0.008 against its floor; grading ×5 COMMIT 0.006
(purpose=verification). Round 2 — a4 spoof re-dispatch RESERVE 0.012 → COMMIT 0.004; a1 refine
RESERVE 0.012 → COMMIT 0.004; a2's 429: COMMIT 0.001 as a production attribution row (no receipt,
no visit — F2), remainder RELEASED; grading ×4 COMMIT 0.004. Verdict — RELEASE all outstanding
incl. null floor remainder 0.012. Σ effective **0.058** = cert total; production 0.040 ≤ 0.20,
verification 0.010 ≤ 0.08, committed never exceeded any purse (zero-overshoot); had the grader
itself crashed, the spend would book run-level `apparatus_usd` and the arm would go UNTOUCHED (R5).

**Fold check (L-FOLD-CLOSURE):** the certificate recomputes from gold/∞ rows only — `_ops` 1–3,
r-091 {1, 21–25, 32, 35–37, 41}; submissions and round_opens are R-run and decay at close; behavior
artifacts live in the content-addressed STORE (never the Medium), `report_ref`s conductor-ACL; the
refused forged receipt left NO row — the absence is the record. No `claim` or `oracle_gen` row this
run: dispatch was conductor-driven and gen-3 never bumped (a gen bump would post `oracle_gen` + a
fresh `round_open` and RESET `stable`).

**The teaching moment.** The null scored 0.9286 — the SAME blind spot as three of the four swarm
cells (all isdigit). The swarm won only because seeded diversity put ONE isascii guard in the
roster. HC-4 and NULL-1 on the same wire: diversity is the entire premium, and the null measures it
honestly. A six-deepseek roster (the lived 2026-07-15 finding) would tie or lose to the null — which
is exactly when the flip law fires. The operator is never asked to trust a bare "converged."

**What just got proven:** TP-1 two-phase grading (F3 + F13 closed on the wire); Stage-1a
non-mintability as the second, independent lock; R19 (round_open first-class; no kind-overload); R4
floor-mode null + reservation-at-open; R15 dual-unit; R16; R5 + F2 (the attribution fork — candidate
burns, apparatus and absence are listed, the innocent arm never pays); F24 (`stable` advances on
VALID receipts only); R8 source-tiering with honest `degraded:true` labeling (§11.3); R18 (knobs
live in the frozen stack); the partial-view pollination law, mechanized.

### W3 · `hc talk` — a fleet action from one sentence; and an overnight batch drive

#### W3a · One sentence → envelope → coalesce → run → receipts → narration

`you> spin up 6 agents to find the strongest open-source rerank model for code search and converge
on the best answer — cap it at $2`. The ROUTER is a metered d0 cell (talk/9f2c/0, temp 0 — the
Conductor never thinks, F15; L6b razed): it returns
`{action:run, topology:tournament, n:6, usd_cap:2.0, say:"Spinning up 6 cells on that, capped at $2."}`.
The EXTRACTOR (builtin@5.0.0) independently reads `{n:6 ("6 agents"), usd_cap:2.00 ("$2")}`;
RECONCILE agrees field-by-field or escalates — never a silent default over a disagreement (Entry-30;
F27 is the named counter-shape). Result: 2 stated, 2 defaults applied. Ingress then runs
validate → auth (Stage 0/1a) → dedup → census → POST → coalesce → ttl → GOVERN (intake L1 =
swarm-justified; escrow RESERVE $2.00, resv r7-e1 — a conductor-ledger record, no Medium row).

```
_ops   | 5117 | command{run}          | operator(talk)→conductor | 01JZK3 |  | utterance VERBATIM + parse block (router + extractor +
       |      |                       |                          |        |  | reconcile); params_hash #ab12; issuer, surface talk,
       |      |                       |                          |        |  | session talk/9f2c                                            | gold/∞  |
_ops   | 5118 | cmd_receipt{ack}      | conductor→operator       | 01JZK3 |  | understood:"tournament n=6 rounds=3 judged; cap $2.00";
       |      |                       |                          |        |  | run_id r7; provenance{n:stated, usd_cap:stated,
       |      |                       |                          |        |  | rounds:default, provider:default}                            | gold/∞  | cost{usd_effective:0.0004, purpose:surface, sku:d0-router@…, …}
_ops   | 5121 | cmd_receipt{ack}      | conductor→operator       | 01JZK4 |  | the F7 storm, live: same prompt pasted in a SECOND terminal
       |      |                       |                          |        |  | → fresh cmd_id, session talk/b04 → COALESCE key (operator,
       |      |                       |                          |        |  | run, #ab12) matches PRIMARY 01JZK3, age 41 s < 120 s →
       |      |                       |                          |        |  | {coalesced_into:01JZK3, run_id:r7}                           | gold/∞  |
run-r7 |  …   | round_open r1 → submissions ×12 → receipts → round_open r2  |  04's one driver over culture run-r7; two-phase grading (05)
       |      |                       |                          |        |  | spends $0.07 purpose=verification — internals per W2's shape | chat/run|
_ops   | 5140 | cmd_receipt{progress} | conductor→operator       | 01JZK3 |  | {state:scored, round:2, detail{best:0.91, candidates:12}} —
       |      |                       |                          |        |  | throttled ≥2 s; SSE mirrors to BOTH ttys                     | chatter/decay |
run-r7 |  52  | verdict{verified}     | conductor                | 01JZK3 |  | champion c4 0.94 ≥ target 0.9; oracle code-rerank-panel
       |      |                       |                          |        |  | @g1#77af; vs_null{null_score:0.86, null_usd:0.004,
       |      |                       |                          |        |  | margin_production:+0.11, margin_invoice:+0.08};
       |      |                       |                          |        |  | failures[{c2, r1, invalid, "429 rate-limit",
       |      |                       |                          |        |  | attribution:apparatus — arm unburned (R5), retried r2}]      | gold/∞  |
run-r7 |  …   | act (H1 deliver.outbox) + act_receipt{exec,settle} (executor-minted, R3): outbox/r7/{champion.md, certificate.json,
       |      | receipts.jsonl, MANIFEST.json}; lineage idem; reconcile probe = stat MANIFEST + digest                  | chat/run|
_ops   | 5165 | cmd_receipt{result}   | conductor→operator       | 01JZK3 |  | {outcome:ok, stopped_reason:converged, summary{run_id:r7,
       |      |                       |                          |        |  | verdict_type:verified, champion{c4, 0.94, 0.9}, vs_null{as
       |      |                       |                          |        |  | run-r7 seq 52}, cells:6, rounds_run:2, candidates:12}};
       |      |                       |                          |        |  | refs[file://…/outbox/r7/champion.md#sha256=9c1e]; + mirrored
       |      |                       |                          |        |  | result for alias 01JZK4 (body = pointer to primary)          | gold/∞  | cost{usd_effective:0.41, usd_reserved:2.00, purpose:run, resv_id:r7-e1, pricebook_version:#…}
```

Escrow at result: COMMIT 0.41, RELEASE 1.59 (ledger-side). Cost-carrier convention: an ack's
`cost{}` carries spend already settled at ack time (here, the router's own metered parse); the
result's `cost{}` is authoritative for the whole command. `hc ask` is the degenerate case (R10):
**1 metered call + exactly 2 Medium appends** (`_ops` command + `cmd_receipt{result}` carrying
`cost{}`) **+ 2 nucleus records + 0 plane tokens + 0 econ Medium appends**.

The narrated lines, each numeral existing in a receipt struct (SUR-2's bar):
> `talk>` Spinning up 6 cells on that, capped at $2. 6 cells (you said 6) × 3 rounds (default — say
> a number to change it), cap $2.00 (you said $2). run r7 → http://127.0.0.1:8799/#run-r7
> `talk-2>` that's already running as r7 (duplicate coalesced) — say 'again' to force a second run.
> watching r7 …
> `talk>` CHAMPION (judge-verified 0.94/1.0, code-rerank-panel@g1) — run r7, 2 rounds, 12
> candidates. 1 of 6 cells errored round 1 (429 rate-limit; retried r2). Null gap: **+0.08 at
> matched invoice** (+0.11 at matched production) over the $0.004 single-cell null. Spent $0.41 of
> $2.00. → outbox\r7\champion.md

`margin_invoice` is the primary printed unit; a bare unlabeled `margin` is REFUSED (R15). `hc top`
on either machine: commands pane 01JZK3 ok ($0.41) + "1 duplicate coalesced"; costs pane: spend by
lane × purpose, burn, reserve 0.

#### W3b · Overnight batch drive with park, preempt, dead-man, and a kill-9

`22:00 hc routine add -f nightly-scan.yaml` (verb drive · goal "scan HN+arXiv for rerank results;
brief me" · lanes [batch] · `unattended{harm_ceiling:H1}` · `usd_cap:5.00` · cron "0 2 * * *",
catchup skip).

```
_ops   | 6150 | command{drive}        | cron(routine)→conductor  | rt:…02 |  | 02:00 slot fires: DETERMINISTIC cmd_id
       |      |                       |                          |        |  | "rt:nightly-scan:2026-07-17T02:00:00Z"                       | gold/∞  |
_ops   | 6151 | cmd_receipt{ack}      | conductor→operator       | rt:…02 |  | GOVERN: quote() batch lane 0.5×, {window_close_eta:05:30,
       |      |                       |                          |        |  | expiry_at:26:00} → park-vs-wait priced: WAIT; Groq lane
       |      |                       |                          |        |  | REFUSED (batch_window_max_h 168h ≥ sla 12h — receipt names
       |      |                       |                          |        |  | the field); kimi endpoint lane fits; escrow RESERVE
       |      |                       |                          |        |  | res:durable $0.41 (reserve_group, provider batch_id inside;
       |      |                       |                          |        |  | fleet batch-hold 0.41/4.20 = 9.8% ≤ 60% cap); {run_id:r9,
       |      |                       |                          |        |  | lane:batch, eta:05:30}; batch job submitted                  | gold/∞  |
_ops   | 6162 | cmd_receipt{progress} | conductor→operator       | rt:…02 |  | 02:31 kill-9 drill: conductor pod dies mid-window → restart
       |      |                       |                          |        |  | folds _ops → command non-terminal → {state:recovered};
       |      |                       |                          |        |  | res:durable folds STILL-HELD; batch NOT resubmitted
       |      |                       |                          |        |  | (identity-dedup: deterministic cmd_id + batch_id in the
       |      |                       |                          |        |  | ledger); zero double-submissions (ECON-R1, live)             | chatter/decay |
_ops   | 6171 | cmd_receipt{progress} | conductor→operator       | rt:…02 |  | 03:10 operator insomnia: interactive r10 admitted → fleet
       |      |                       |                          |        |  | scheduler preempts: PARK r9 — seal live segment, release
       |      |                       |                          |        |  | runner, PVC retained (a graceful crash, 09) →
       |      |                       |                          |        |  | {state:parked, detail{reason:preempted, by:r10}}; r10 done →
       |      |                       |                          |        |  | RESUME r9 (re-claim + re-bind, the F10 path) → recovered     | chatter/decay |
run-r9 |   8  | handoff               | scan/*→writer/0          | rt:…02 |  | 05:12 batch items landed (per-item COMMIT as each lands —
       |      |                       |                          |        |  | partial results first-class); collated corpus →typed payload
       |      |                       |                          |        |  | #… handed to writer/0 for synthesis                          | gold/run|
run-r9 |  10  | act (H2 email.send)   | writer/0                 | a7     |  | synthesis wants to email the brief: harm H2 > issuer
       |      |                       |                          |        |  | routine/* ceiling H1 (attenuation: a child NEVER exceeds its
       |      |                       |                          |        |  | issuer) → PARK act a7                                        | gold/∞  |
run-r9 |  11  | act_receipt{hold}     | executor                 | a7     |  | summary{claim:r9/writer/0, capability:email.send,
       |      |                       |                          |        |  | harm_effective:H2, expectation:null, until:09:00,
       |      |                       |                          |        |  | grant_ttl:24h} — H1+ rows are D-gold R-forever              | gold/∞  |
_ops   | 6201 | cmd_receipt{progress} | conductor→operator       | rt:…02 |  | hold notice. 05:12→08:00 ONLY a headless SSE exporter drains
       |      |                       |                          |        |  | /events (cursor class: headless) → dead-man law: NO
       |      |                       |                          |        |  | interactive-class cursor passes 6201 by deadline-minus-grace
       |      |                       |                          |        |  | 08:30 → H2 DEGRADES to H3 hold → {state:input_required}
       |      |                       |                          |        |  | (SUR-6's headless-drain bar)                                 | chatter/decay |
_ops   | 6230 | command{grant}        | operator(tty)→conductor  | 01JZM8 |  | 08:41 `hc queue` (renders join-free from summary{} alone) →
       |      |                       |     corr:a7              |        |  | `hc grant a7` = a NEW CommandEnvelope through the SAME
       |      |                       |                          |        |  | ingress; auth Stage-0/1a = loopback-tty possession (at
       |      |                       |                          |        |  | Stage-1b this envelope MUST carry the off-box signature —
       |      |                       |                          |        |  | the R7 ratchet never demotes)                                | gold/∞  |
run-r9 |  12  | act_receipt{exec}     | executor                 | a7     |  | email sent; single-use grant consumed at hold→exec           | gold/∞  |
run-r9 |  13  | act_receipt{settle}   | executor                 | a7     |  | settled                                                      | gold/∞  | cost{usd_effective:0.000, sku:tool.email.send@…, purpose:tool, …}
run-r9 |  20  | verdict{kind:synthesis}| conductor               | rt:…02 |  | synthesis of 4 cells (no executable oracle — NEVER verified);
       |      |                       |                          |        |  | 12 sources; vs_null dual-unit carried per W1's pattern       | gold/∞  |
_ops   | 6233 | cmd_receipt{result}   | conductor→operator       | rt:…02 |  | {outcome:ok, summary{verdict_type:synthesis, …}};
       |      |                       |                          |        |  | refs[outbox/r9/brief.md]                                     | gold/∞  | cost{usd_effective:0.554, purpose:run, pricebook_version:#…, …}
```

**The money (07's columns, conductor ledger):** RESERVE res:durable 0.41 held for the window
(`reserved_in_batch` visible in `hc top`) → items land over 3h: per-item COMMIT Σ **0.19** at batch
0.5× (savings receipt: sticker 0.38 − effective 0.19) → 2 stragglers at watchdog τ=p80:
deadline-form hedge `p_miss·C_miss = 0.6 × 0.11 = 0.066 > E[c₂] = 0.018` → race on
kimi-k2.6@fireworks/fast; loser cancelled → COMMIT **0.043**, `waste_flag:racing_loser` 0.007 →
overnight rounds 2–3, same shape + batched oracle-gen regrade sweep (pure re-scoring): COMMIT
**0.31** → one grader timeout: **apparatus_usd 0.011** booked to the run purpose ledger,
`waste_flag:apparatus_invalid`, arm UNBURNED (R5) → kill-9 fold: H0 poll act settles 7 ok / 1
expired — expired item RELEASED, `waste_flag:batch_expired`; committed never exceeded 5.00
(ECON-R1) → wrap: **0.19 + 0.043 + 0.31 + 0.011 = $0.554 of 5.00**, every number recomputable
against `pricebook_version`. Morning `hc top`: burn_rate ≈ 0 (batch closed) · effective_vs_sticker
47% · cache_hit 63% · racing_waste 0.007 ≤ 5% frac · apparatus_usd 0.011 · projected_to_cap ∞ ·
reserved_in_batch zeroed; park/preempt receipts visible in the ops lane.

> `morning talk>` overnight scan done (batch lane, $0.554 — effective 47% of sticker): synthesis of
> 4 cells (unverified), brief + 12 sources → outbox\r9\brief.md. 1 act waited for you and is now
> sent.

**Fold check (L-FOLD-CLOSURE):** resume and replay read the durable rows only — `_ops` commands +
ack/result cmd_receipts, the H2 act + its hold/exec/settle receipts (H1+ acts are D-gold
R-forever; the harm axis keys durability), the handoff-fed verdict, and the run genesis rows.
EVERY `cmd_receipt{progress}` row (5140, 6162, 6171, 6201) is D-chatter R-decay and evaporates —
the recovery drills READ the durable decision records, never the progress stream (probes are never
state). The coalesced alias 01JZK4's ack and mirrored result stay gold: the dedup fold needs them
forever. Type census across W3: command, cmd_receipt (ack/progress/result), round_open, submission,
receipt, verdict, act, act_receipt, handoff — all registered; zero grammar change.

**What just got proven:** R10's degeneracy arithmetic honored at the surface; F7 closed live
(coalesce, 41 s < 120 s); F15 (the router is a metered, priced cell — the Conductor never thinks);
ECON-R1 under kill-9 (zero double-submissions, cap never exceeded, res:durable folds STILL-HELD);
R5 + the full waste vocabulary {racing_loser, batch_expired, apparatus_invalid} — every dollar
receipted or its absence listed; the dead-man/H2→H3 law keyed on interactive-class cursors only
(SUR-6); attenuation (a routine ceiling H1 cannot mint H2 — the grant came from the operator,
through the ONE ingress, as a first-class command); the R7 ratchet stated at the grant; batch-aware
parking (WAITING-BATCH over quote()'s window fields) and park = graceful crash (09's claim API, the
F10 resume); L-HONEST-VERDICT again — an overnight synthesis narrates as one.

---

## §14 · The build ladder (from LIVE P0–P2 upward; re-cut by usefulness-per-slice; each rung independently useful; falsifier-gated)

Order of construction = order of trust. v1's P0–P2 are **built and live-proven** (§1); v5 grows from there.
The standing rule: *contracts before cells, oracle before convergence, persistence before scale, the local
floor before the cloud, a falsifier before every organ, the null before the swarm's credit, and — new in v5 —
the versioned, chained, metered record before any organ that folds over it.*

**The re-cut resolves the wave's "build me first" tension into a dependency lattice, not a fight.** Five seats
each named their organ as the one that must land first (01: the version spine; 02: the nucleus chain +
genesis; 03: receipts-on-Medium; 07: the pricebook; 09: the box-guard preflight). They are not competing —
they are describing the **same foundation** from five angles. Every other organ's fold, receipt, warrant, and
cost attribution presumes a record that (a) can name its own contract version (01, else G3: nothing is
migratable), (b) chains to its predecessor and is redaction-clean (02/03, else no tamper-evidence and no
resume-as-fold), (c) actually reaches the Medium (03, else E2: receipts stay in-process and every
constitutional fold is impossible), (d) carries a truthful `cost{}` group (07, else the receipt is honest
about everything but its dollars — E2 one plane down; and the live price dict is already 4× wrong with four
dated cliffs inside 45 days), and (e) is written to durable storage the live single-box Medium can trust
today (09, the `/mnt/c` WAL-corruption + missing-pragma gaps bite now, no k3s required). So **P2.5a′ is one
coherent foundation rung**, not five, and everything else is genuinely downstream of it.

The ladder (each rung names the exact live files it completes — the 0-byte stubs are the honest map:
`common/ledger.py`, `common/canon.py`, `cell/loop.py`, `medium/firewall.py`, `conductor/registry.py`,
`conductor/scheduler.py`, `substrate/k3s.py`, `substrate/secrets.py`, `surfaces/mcp.py`; `contracts/schemas/`
empty; `api.py` no-auth; `commander.py` un-metered):

| Rung | Deliverable | Bar / status |
|---|---|---|
| **P0 — the stem** | one cell on k3s: prompt → swappable provider → answer; nucleus persists; `hc resume`. | **LIVE** (HC-1/HC-2/HC-6; artifacted). |
| **P1 — the Culture** | fan-out → external oracle → champion; `hc replay`. | **LIVE** (HC-3/HC-4; the F1 finding). |
| **P2 — the self-driving machine** | router + UCB schedule + drive + cost governor + harm schema; `hc talk`; a first judge panel. | **LIVE** (HC-8 hard-stop; two P2 judge bugs → P2.5 criteria). |
| **P2.5a′ — the foundation record** | the version spine (header law + census-in-genesis + emit/read split + the 17-type registry + the one-verb-executor) · the nucleus chain + genesis + read-barrier + registers + evidence-bundle exporter (`common/ledger.py`, `common/canon.py`, `cell/memory.py`, `cell/bundle.py`) · receipts-on-Medium + the full envelope/registry/post-ACL (slice **M1**) · the pricebook + truthful metering (`cost_usd` populated, cache usage captured) · the box-guard Substrate Preflight (`G-DB-DURABLE` et al., protecting the live SQLite Medium). | S-KG-1/2, NUC-2, **M1** (C1–C12 @ T0), ECON-S1, SUB-PREFLIGHT-BOX. *The rung everything folds over.* |
| **P2.5b′ — warrants** | verb `act` + the ACT-PIPELINE + evidence + grounded runs + the H0 tool-profile annex (mutation-gating; exfil via the trifecta plane) · the generalized firewall made mechanical (trust-tagged frames; `firewall.py`) · a second weights family provisioned. | GX-1/2, GROUND-1/2, ACT-SCRUB-1, ACT-TRIFECTA-1, CELL-2, JUDGE-1. |
| **P2.5c′ — the economics plane** | dollar-UCB + reservation/escrow (Conductor-owned, fleet-scoped, the fold) + cache-affinity + fan-out stagger + the local floor; fixes L1–L8. | ECON-1/2/7/8, CELL-9 (cache ≥60%). |
| **P2.5d′ — isolation & the growing bar** | two-phase grading (TP-1) + class-3 + the k3s preflight battery + the sealed-set/oracle-generation hooks + the redaction pass + the signed `hc export`. | HC-7-v2, SUB-suite, SEC-8, CRUCIBLE hooks. |
| **P2.5e′ — the command plane** | CommandEnvelope + one-ingress + F7 coalesce + `_ops` + Stage-1b signatures + the d0 intake classifier + `hc top` + `hc peek` + the single-cell null (arm-zero). | SUR-suite, NULL-1(gate), OPER-1, CELL-3, SEC-suite. |
| **P3 — scale** | NATS/JetStream behind the *same* C1–C12 battery (the re-run IS the parity falsifier) · multi-node k3s → VPS · the phone PWA · COW-fork MCTS · multi-run fleet scheduling (park/preempt) · batch & speed lanes. | W2(battery), HC-5, CELL-4-fork, FLEET-0, ECON-batch. |
| **P4 — the depth dial** | d2 residents (rings + consolidation + temporal-KG render, NUC-3-gated) · a d3 brain-cell backend (KEEL-class, over protocol). | HC-9, NUC-suite, CELL-5. |
| **P5 — the Crucible & self-organization** | oracle growth end-to-end · free-swarm as a falsifier-gated experiment. | CRUCIBLE-1/2/COST, HC-10, DM-DRILL. |
| **The north star** | org core-wire auto-discovery (DISCOVER-1) — earned only when every rung above is green, on fanout-synthesis. | DISCOVER-1; measured, never asserted. |

**Live-fleet migration note (per rung).** Every rung that bumps a contract ships its migration under the
versioning law (§3): reader-liberality (a MINOR is additive, old readers ignore unknown fields), an epoch
record on the wire and in each nucleus genesis census, and a drill that upgrades a running fleet mid-flight
with zero double-fires and old receipts still verifying (CONTRACT-HDR-1). A pre-v5 ledger gets a **synthetic
genesis** recording `chain_adopted_at_seq: k` — records before k are immutable-but-unhashed and the contract
says so rather than pretending tamper-evidence existed before it did.

**The day-1 operator golden path** (anchored by the substrate + kernel seats): from an empty box to the first
`hc talk` — install k3s (or compose-lite), run the Substrate Preflight (GREEN/DEGRADED/RED), inject one
provider key to the secret store, `hc apply` the conductor + a warm runner pool, `hc ask "…"` (the degenerate
path: one metered call + two Medium appends), then `hc run tournament …` with a null arm. Each step is a named
command with a receipt; nothing requires the cloud.

*(The per-slice file tables and rung-exit drill schedules live in `BUILD.md`; every bar is in §15.)*

---

## §15 · Falsifiers — the organ → null → bar index

v2 §15's house rule, carried: thresholds AND the sets they run against MUST be pre-registered before measuring; a bar may version only at generation boundaries (A12) with the change recorded. **DELTA — the index's shape is now law:** every row is `(organ · its null · its bar · its rung)`; every NEW organ any section introduces MUST add its row in the same change (a mechanism without a row is vision, labeled); rows are keyed by stable ids. Seats own their rows (falsifier ownership follows organ ownership); the kernel owns the shape. The index, grouped by plane:

### Kernel / grammar (rows: seat 01)

| id | organ (its null) | bar | rung |
|---|---|---|---|
| **VERB-1** | the one verb executor (null: per-method verb logic) | AST: zero call sites invoke `cognition.complete` / `medium.post` / the oracle runner / an effect executor outside `execute()`; drill: crash each verb between INTENT and OUTCOME (`HYPERCELL_CRASH_BEFORE_OUTCOME`, per-verb), resume — 100 trials/verb, zero double-fires, zero wrong-verb reconstructions (the produce-as-empty-ask class is dead) | P2.5b′ |
| **LAYER-1** | the three-clause layer law + composition root (null: import-direction-only rule) | CI fails on any forbidden edge: static import, function-body import, or string module reference; the 12-site live corpus all caught; the root passes wiring, fails on any logic call | P2.5b′ |
| **ONE-METER-1** | the single metering path (null: per-call-site wrapping) | AST: only `cognition/metered.py` constructs provider adapters; drill: a judge-panel run books every judge dollar (F25 regression); un-metered constructions fail CI | P2.5b′ |
| **MIG-1** | MINOR skew legality (null: lockstep-only upgrades) | mid-tournament wire MINOR bump: mixed old/new cells complete; replay equality across both readers; champion certificate recomputes identically | P3 |
| **MIG-2** | the M-MAJOR epoch drill (null: downtime-and-wipe) | park at round boundary → upgrade → resume → completes; pre-epoch receipts render; planted old-MAJOR ledger folds via R6 adapter; remaining budget = cap − folded pre-epoch spend (F16 regression) | P3 |
| **MIG-3** | the census gate (null: trust-the-image) | unknown/newer-MAJOR image label ⇒ spawn REFUSED with receipt; never silently admitted | P2.5b′ |
| **MIG-4** | the rollback point (null: roll-forward-only-always) | abort between snapshot and first new-MAJOR gold write → restore → fleet resumes on old version, zero double-fires | P3 |
| **MIG-5** | R2 round-trip preservation (null: known-columns storage) | an envelope with three unknown fields survives store-and-relay byte-identically, 10/10 (F18 regression) | P2.5b′ |
| **MIG-SUR** | surface/fleet version handshake (null: silent misexecution) (seat 08 carries the same drill as its census-refusal gate, slice SUR-s2) | old `hc` vs new `hcd`: 100% typed refusals naming both versions, zero silent misexecutions | P2.5e′ |
| **CONTRACT-HDR-1** | the contract header law (null: prose headers) | CI: a contract file missing any H1 field fails; a version bump without its regenerated JSON-Schema mirror in the same commit fails | P2.5a′ |
| **RESUME-$1** | spend-as-fold (null: RAM meter) | kill -9 mid-drive, resume: the resumed run cannot exceed the original cap; folded spend equals pre-crash ledger sum (F16 regression) | P2.5c′ |

### Wire / Medium (rows: seat 03)

| id | organ (its null) | bar | rung |
|---|---|---|---|
| **W1** | wake hints — doorbell/watcher/`consume()` (null: the `data_version` slow-poll — the mandatory fallback IS the null) | p95 post→wake ≤200 ms T0 / ≤500 ms T1 over 100 trials; `sever_hint()` ⇒ zero loss, delivery within one fallback tick; token meter flat over 1 h idle (a sleeping cell = zero LLM tokens) | P2.5b′ (from slice M2) |
| **W2** | the T1 binding + mirror (null: T0 — the fabric runs single-node without T1, unchanged) | C1–C12 green on BOTH transports from ONE test file; any transport-specific assertion = contract leak, test redesigned | P3 (from slice M4) |
| **W3** | chain-sealer + anchor (null: unanchored chain — verify degrades to "consistent, unanchored" and says so) | seal/anchor lag p95 ≤250 ms; D-gold post returns only after anchor fsync; anchor mismatch detects a byte-rewrite that stored hashes alone cannot | P2.5c′/d′ (from slice M3) |
| **W4** | D-gold durability path (null: — durability has no null; the bar is absolute) | `kill -9` storm ×100 mid-traffic on T0 and T1: every loss is a contiguous chatter-only suffix; **zero gold lost**; cell-posted gold re-posts under same `idem`, folds see exactly one | P2.5c′/d′ (from slice M3) |
| **C11** | post-ACL (null: liberal receiver alone — all types postable) | client gate refuses; a smuggled privileged record is void-at-fold — appears in NO constitutional fold; `verify().void_by_acl` names it; CI grep: every live `post(` call site's type exists in the registry | P2.5b′ (from slice M1) |
| **C12** | compactor + Merkle (null: no compaction — the log only grows, safe, unbounded) | drop + archive spans verify through holes; inclusion proof validates an archived record; a cite-pinned row inside a purge span survives (keeper-aware delete) | P2.5c′/d′ (from slice M3) |
| **BRIDGE-1** | the paired relay (null: no federation — single Medium, the lawful default) | 2 machines, partition mid-relay, heal: exactly-once (bridge idem), local re-sequencing, remote receipt provably VOID in every local convergence fold | post-P3 (from slice M5) |
| **MIGRATE-1** | `hc_medium_migrate` (null: fresh log — abandon history, always available, honest) | migrated log: old tapes replay through the fold adapter byte-untouched; `verify()` reports pre-genesis spans "pre-chain, unverifiable"; zero synthesized hashes/receipts (grep the migrator for hash-writes against old rows = 0) | P2.5b′ (from slice M1) |

### Cell / nucleus (rows: seat 02)

| id | organ (its null) | bar | rung |
|---|---|---|---|
| **NUC-1** | hash chain + genesis (null: the live unchained ledger — v1 today, a mid-file edit is invisible) | flip any byte in any sealed/active record ⇒ `hc verify` names the first bad seq; 100% over a fuzz suite; forged `forked_from` fails child verify | P2.5a′ (from slice N1′) |
| **NUC-2** | render fold + in-render cursor (null: rebuild-on-every-open — live `nucleus.py:30-31`) | 2× local + 1× second-machine rebuild ⇒ identical digests over a 10 K fixture; **open p95 ≤ 100 ms @ 100 K records warm**; `verify()` catches a corrupted render 10/10 | P2.5b′ (from slice N3′) |
| **NUC-3** | tkg render (null: FTS-only recall — the render stays dark) | temporal precision@k ≥ FTS+10 pts; p50 ≤ 2× FTS; token cost ≤ 1.1× FTS — over ≥2 wks resident traffic or a ≥500-query golden set incl. LongMemEval-V2-style slices; losing render stays dark or is deleted | P4 (from slice N6′) |
| **NUC-4** | register wall + bundles (null: prompt-level discipline — ask the model nicely) | 0 false accepts over 10 K generated invalid asserts (decision/ask-outcome/narrative/self/future/9-deep/submission-xref/raw-URL); valid set accepts; exporter emits 0 narrative citations over a fuzzed corpus; **terminal trust tags present on every bundle terminal** | P2.5a′ (from slice N2′) |
| **NUC-5** | frame assembler + manifest (null: ad-hoc prompt concat — live P0 `messages=[system,user]`) | 100 replays + second machine ⇒ identical frame digests; byte-coverage: concat(manifest items) == frame minus delimiters; know-X query correct on seeded fixture; **50-tick adversarial trace: `prefix_hash_stable` changes 0×, `prefix_hash_semi` only at installs; ≥60% cache-hit attribution matches provider `cache_read` (joint w/ econ — both bars together)** | P2.5c′ (from slice N4′) |
| **NUC-7** | tier bars + strip ladder (null: fsync-always + sync mirror — live v1 append) | append p50 ≤ 10 ms / p95 ≤ 50 ms amortized (preflight 1 K bench + live stats render); **≤ 1 durable write per standard flush, ≤ 2 per gold**; nucleus wall < 1% per 100-step window; breach ⇒ `degraded-persistence` visible in `hc top`, never silent | P2.5b′ (from slice N3′) |
| **NUC-8** | consolidation + rotating cold-eyes (null: no consolidation — raw FTS recall forever, correctness-equal by law) | planted-false-fact-in-prior-digest fixture ⇒ cold-eyes rejects install ≥ 9/10 across 3 family pairs; no digest-only input path exists (code inspection + canary); 50-pass soak: every consolidation span covers ≥ 1 raw record; **family rotation observed ≥ 2 distinct L2 families per 4 passes** | P4 (from slice N6′) |
| **NUC-9** | record ladder (null: the live 5-record ask ceremony — E19) | `hc ask` writes exactly 2 nucleus records; d0 writes 0; byte overhead ≤ 1 KB + bodies; **read-barrier: re-issued idem returns the stored outcome with zero cognition calls (incl. produce — F17 closed)** | P2.5a′ (from slice N1′) |
| **NUC-10** | fork-by-reference (null: copy-the-directory fork) | 1 GB / 1 M-record parent forks < 250 ms, < 1 MB new bytes (same-shelf); child rebuild digest at `at_seq` == parent digest at `at_seq`; cross-node fork verifies borrowed content hashes | P3 (from slice N5′) |

*(NUC-6 is the nucleus half of the joint scoped-exactly-once row — see CELL-4 / NUC-6 in the act/grounding group.)*

### Run engine / fleet (rows: seat 04)

| id | organ (its null) | bar | rung |
|---|---|---|---|
| **RE-1** | one driver (null: the three live loops) | `stable_k` property test: identical VALID-event counting across all convergent rows; F14, F24, F25 each UNREPRODUCIBLE by construction; 29/29 green before and after | P2.5b′ |
| **RUN-M1** | manifest freeze (null: re-read disk each open — live behavior) | apply → mutate yaml → resume runs under FROZEN bytes, `hc verify` passes; re-apply of mutated file same run_id REFUSED | P2.5b′ |
| **RE-3** | per-case feedback (null: code-only pollination — live) | the F1 replant: single-family roster + planted blind spot + feedback ON reaches target ≤2 rounds after the case first appears in a packet; OFF plateaus (the live P1 run on disk IS the OFF baseline) | P2.5b′ (with 03's M1) |
| **RE-10** | partial view (null: total view — live topology.py:167-173) | no round with all-identical views at \|F\|≥2; ∪ views = F; assignment recomputed by `hc verify`; herding drill: a seeded common-mode wrong answer propagates to ≤ half the roster in one round (total-view control: all) | P2.5b′ |
| **RE-4** | fold-resume + certificate (null: in-RAM state — live: F16 meter resets) | `kill -9` at 10 random points → each resume completes; final certificate FIELD-IDENTICAL to an uninterrupted control at same seeds; zero double-scored submissions; CERT-1: flip one bit in the span → verify fails NAMING the field; two-log spend totals agree | P2.5c′/d′ |
| **RE-5** | intake (null: deterministic signals only) | golden set ≥40 goals (all four quadrants + count/mode traps) drawn from the ONE shared corpus `bench/golden/traps.jsonl` (08's SUR-1 draws from the same file, per-organ assertion columns — a blind spot caught by either bars both, #704): axis accuracy ≥95%, ZERO silent defaults on disagreement, provenance recomputable; NULL-1's P2.5d gate rows (arm-zero in every convergent run; lift at matched-invoice; rows recomputable) | P2.5e′ |
| **FLEET-0/1/2/3** | fleet allocator (null: FIFO-serial — one culture at a time) | FLEET-0: standing mixed workload (1 interactive fanout + 2 standard tournaments + 1 maintenance routine): allocator beats FIFO on interactive p95 by the pre-registered margin at equal total dollars with zero starvation, ELSE THE FLEET RUNS FIFO AND THE ALLOCATOR DIES; FLEET-1 fairness (2:1:1 weights → slot-time within 10%); FLEET-2 preemption (park at tick boundary; ZERO lost receipts; certificate field-identical to unpreempted control); FLEET-3 stickiness (cache hit-rate delta ≥ pre-registered margin, 07's hit-rate query as instrument) | P3 |
| **RE-7** | mcts (null: restart-tournament) | on a stateful (build-then-extend) task, MCTS beats restart-tournament at equal gradings; `kill -9` mid-rollout → tree rebuilt node/visit/value-exact; concurrent siblings attempting the same H1 act → exactly one executes (CELL-4/NUC-6 joint drill) | P3/P4 |
| **RE-8** | conflict-promote (null: averaging/last-write) | two shards planted with contradictory facts → run emits `conflict` (rides `task`, R19) + adjudicated resolution with a producer-disjoint authority receipt; ZERO averaged values in the accumulator | P3 |
| **HC-10** | free-swarm (null: round-robin coordination) | k=10×5 paired, ≥3 classes ≥1 compositional, sign test p<0.05; no class won ⇒ free-swarm exits the constitution | P5 |

### Trust / oracle (rows: seat 05)

| id | organ (its null) | bar | rung |
|---|---|---|---|
| **ATTR-1** | two-phase attribution (null: v1 single-subprocess) | Planted candidates: `while True: pass`, `sys.exit(0)` at import, a clean miss, and an artifact crafted to crash the grader. Assert: the hang and the exit-spoof grade `gate` score 0 — NEVER INVALID (F13 falsified); the clean miss grades `gate` partial; the grader-crasher grades `gate` candidate (differential re-attribution) when a sibling grades clean, else `apparatus` + quarantine; break the case set → `invalid` + retry + `apparatus_usd` burn, no arm charge. Stub-cell: deterministic, no LLM. | P2.5d′ |
| **JUDGE-1** | judge honesty (null: single-family panel) | Cross-family panel + controls orders golden > flaw ≥90%; the two lived P2 bugs red-teamed closed (outcome derives from score-vs-target not unconditional `passed`; <2 counted ⇒ INVALID `oracle-sick`); a same-family self-preference delta appears (bootstrap CI over ≥200 paired obs excludes 0 ⇒ recusal retained, else dropped and the drill says so); a planted broken judge (flaw=9, golden=3) ejects within ≤3 rounds with its receipt; a canary-mismatch lane de-rates to zero. | P2.5d′ |
| **VER-1** | two-tier scheduler (null: always-full-panel / never-panel) | Simulated judges with known `e`: the scheduler panels every promotion, screens every round, fires each escalation trigger on its planted condition, and K* matches the closed form for three (ê, V_wrong) points. | P3 |
| **NULL-1** | the single-cell null (the null *is* the null) | Arm-zero present in every convergent run, lift published at matched-invoice, every row recomputable from receipts; over k=20, ≥1 class the null wins (else strawman — audit parity, operator-blind) AND ≥1 the swarm wins (else HC-3′ fails at scale, published); no positive lift anywhere ⇒ the swarm layer is a research instrument and the constitution says so. NullPolicy mode derives from class lifecycle; the flip fires per the ONE predicate. | P2.5d′ / standing |
| **DIV-1** | the Divergence Meter (null: no tripwire) | Stub candidates with scripted behavior vectors: planted blind spot ⇒ D > ε ⇒ growth trigger emits the right argmax inputs; scripted herding (collapse, flat score) ⇒ quarantine + re-seed; scripted victory (collapse + score jump) ⇒ NO quarantine (the score guard); identical-roster round 1 ⇒ floor breach ⇒ re-seed ⇒ refuse-to-swarm receipt. | P5 |
| **HC-V1** | oracle growth (null: static G0 bar) | `gen-0` = the ipv4 battery MINUS the ٤ and leading-zero cases (two plants); reference truth held by the drill harness, never the fabric. Assert: ≤2 generations mint ≥1 admitted case per plant class that a gen-0 passer fails; every minted label matches reference truth; every minted case carries a candidate-blind clerk receipt; `oracle_growth` spend ≤25% of production; the admission journal is complete. | P5 |
| **HC-V2** | judge honesty at scale (null: no controls) | (subsumes JUDGE-1's panel half at 20 rounds, ≥2 classes, both control-verification mechanisms) | P5 |
| **CRUCIBLE-1** | the library compounds (null: static G0 at matched budget) | Run A mints ≥1 case, archives champion_A, advances gen 0→k. Run B, same class, fresh roster: run B's first receipt cites gen k; champion_A serves as a control (judged) or regression candidate (executable); an implementation passing gen 0 but failing gen k is gated in run B round 1; gen digests chain. | P5 |
| **CRUCIBLE-2** | the gaming detector (null: no sealed set) | Reported grader scores token-containment (gameable); sealed set grades exact-match. Scripted candidate adopts the echo hack at epoch 2. Assert: archive_signal rises, sealed aggregate falls, halt within ≤2 epochs, champion_head rolls back to the pre-hack champion, minting freezes, resume requires the operator command — all from receipts, zero manual eyes. | P5 |
| **OPER-1** | the operator's imports (null: unsampled adjudication) | `k%` blind disjoint re-adjudications run live; a seeded wrong adjudication / golden / sealed-key is caught by the epoch recall drill within one epoch; the disagreement rate + adjudication-latency render in `hc top`; while the rate exceeds its ceiling, that class's operator-minted cases enter `provisional` (never retired). | P2.5d′ / P5 |

*(HC-7-v2 — isolation, both halves — sits in the substrate group; the contract half is this seat's TP-1.)*

### Act / grounding (rows: seat 06)

| id | organ (its null) | bar | rung |
|---|---|---|---|
| **GX-1(a)** | verb `act` earns its seat (null: an 8th verb) | §D.3 run on the hermetic corpus: champion carries ≥1 `supports` ref per material claim; **the act plane adds no MessageType beyond those the registry already declares** (`act`/`act_receipt` are pre-declared; the enum diff a grounded run produces is empty), **zero grammar change** — checked mechanically | P2.5a′ (from slice GROUND-0) |
| **GX-1(b)** | H1 warrant kit (null: bare tool call) | `code.run@sandbox`: idem + losable default expectation + class-3 receipt + non-mintable receipt, end-to-end | P2.5b′/d′ (from slice ACT-1) |
| **GX-2** | warrants are affordable (null: naked mode) | `(T_required − T_none)/T_none ≤ 0.15` at ≥ naked-mode score; re-balance levers in order: quote caps → sampled fraction → ref-only | P2.5a′ (from slice GROUND-0) |
| **GROUND-1** (v3's "HC-V4", renamed per v2 §15) | the grounding chain (null: `none` mode) | 4 seeded-fabrication classes ≥10 each: forged `act://` 100% at post-gate; digest-mismatch & quote-not-in-source 10/10 checked / ≥9/10 at ρ=0.2; irrelevant-ref ≥8/10 by entailment; `required` beats `none` on the hash-committed ≥50-question factual set; **citation-validation overhead ≤10%** of verification spend; every catch mints stain + ρ→1.0 | P2.5a′ (from slice GROUND-0) |
| **GROUND-2** (restored from v2 §15 — v3 dropped it) | the dial itself (null: honest `declared` labels) | on judged NON-factual classes, `required` MUST NOT lose to an honest declared-mode baseline at matched budget; else that class's default demotes to `sampled` (the escape is pre-registered, not ad-hoc) | P2.5a′ (from slice GROUND-0) |
| **ACT-GATE-1** | derived-harm gate (null: trust the declaration) | 20 disguised mutations (GET+auth, GET+body, POST-declared-H0, state-addressing args, cell cookie) → 100% `refused/harm_derived`, zero executions, every refusal a receipt. **Supplies attempts 7–8 of HC-7-v2's 8-way red team** | P2.5a′ (from slice GROUND-0) |
| **ACT-SCRUB-1** (new) | credential scrub (null: raw provenance) | plant adapter keys as query/body/header carriers across 3 profiles → 0 credential bytes in any receipt/evidence bundle/certificate (`provenance.scrubbed` set where applicable); joins SEC-8's planted-key sweep | P2.5a′ (from slice GROUND-0) |
| **ACT-TRIFECTA-1** (new) | gate step 1h (null: spawn-only check) | a cell spawned {private_data ∧ external_comms} then performing its FIRST world-content fetch: the fetch or the next external-comms act is refused `reason:trifecta` per waiver policy; the acquired-trifecta fold replays identically from the log after kill-9 | P2.5e′ (from slice ACT-2) |
| **CELL-4 / NUC-6** | scoped exactly-once (null: `(claim, step_id)` only) (joint with seat 02's NUC-6 — nucleus half: plural `pending()`; 02's wording adds parallel in-flight acts n≥3 and the H2 leg) | `{W0..W5,W3h} × {H0,H1} × {instance,lineage,slot}` × 100 + 8-sibling fork race: zero double-fires on lineage/slot; every in-doubt lands `unknown` → reconciles to ok/invalid/parked (never blind re-exec); instance re-fires per branch (positive control); race: 1 executes, 7 share via `duplicate_of`, 8 nuclei hold the same evidence ref | P2.5b′/d′ (from slice ACT-1) |
| **ACT-SETTLE-1** | wagers grade (null: actor self-report) | planted will-hold / will-miss / resolver-down → settle ok/miss/expired; ledger folds {1,1,1}; miss fires `on_miss`; executor killed mid-flight on a 4th act → reconciliation lands `ok` via probe, zero re-executions | P2.5b′/d′ (from slice ACT-1) |
| **ACT-H2-1** | dead-man (null: a sleep) | (a) no interactive surface → escalates H3 at `until−grace`, zero executions; (b) interactive cursor passes → executes at deadline; (c) cancel mid-hold → `refused/canceled`; (d) headless MCP poll past the hold → does NOT satisfy; (e) NEW: kill -9 mid-hold → countdown resumes from Medium timestamps, deadline unchanged. All five are log queries | P2.5e′ (from slice ACT-2) |
| **DELIVER-1** (v3-wave-minted, kernel T8 — provenance noted) | delivery-is-an-act (null: direct file write) | crash mid-delivery at each window → zero double-sends, outbox manifest digest-verified, `hc talk` narrates only from receipts | P2.5b′/d′ (from slice ACT-1) |

### Econ (rows: seat 07)

| id | organ (its null) | bar | rung |
|---|---|---|---|
| **ECON-2** | the fleet escrow — reserve/commit/release/reconcile (null: the live per-run RAM `Governor`) | 16-concurrent overshoot drill: `committed ≤ cap` in every trial, every scope, under crash/429/batch-cancel injection; the F6 replay stops at $0.0004–0.0005 | P2.5c′ (from slice ECON-S2) |
| **ECON-R1** | `res:durable` batch reservations (null: in-RAM batch state) | kill-9 mid-batch: zero double-submissions, ledger = provider invoice | P3/P4 (from slice ECON-S5) |
| **ECON-L8** | reconcile-before-first-reserve on resume (null: RAM-held committed — the live L8 leak) | crash+resume mid-run refuses past remaining headroom | P2.5c′ (from slice ECON-S2) |
| **ECON-LEASE-1** | `res:lease` H0 micro-escrow (null: per-call fleet escrow) (= seat 06's ACT-LEASE-1, one co-owned drill — 06's wording adds the zero-round-trip hot-path count and the p50-latency mortality clause) | kill-9 mid-lease: fold shows STILL-HELD, receipts settle, overshoot ≤ quantum | P2.5a′ (from slice ECON-S2b) |
| **ECON-UCB-1** | dollar-UCB allocation (null: pull-count UCB) | dollar-UCB reaches target at ≤60% of pull-UCB spend; allocation invariant under currency re-scale ×100 | P2.5c′ (from slice ECON-S3) |
| **ECON-PB-1** | the pricebook + freshness-pessimism rules (null: the live `_PRICE` dict — silent guesses) | unknown refused; stale reserves ≥ fresh; planted +30% price change fires the >10% alarm and the fork labels it price-change | P2.5a′/b′ (from slice ECON-S1) |
| **ECON-CACHE-1** | cache discipline — tags/hysteresis/stagger (null: unstaggered, tag-blind dispatch) (the ≥60% attribution half is joint with seat 02's NUC-5 — both bars together) | ≥60% hit on a warm tournament; stagger realizes ≥80% of computed savings; shuffled frame refused | P2.5c′ (from slice ECON-S4) |
| **ECON-BATCH-1** | batched drive + SLA watchdog (null: interactive-only dispatch) | overnight tournament inside sla at ≥40% saving; forced-late premium receipted | P3/P4 (from slice ECON-S5) |
| **ECON-RACE-1** | straggler hedge / racing (null: no hedge — stragglers ride) | p95 wall −30% at ≤10% premium; waste reconciles exactly | P3/P4 (from slice ECON-S5) |
| **ECON-8** | the swarm premium / class-flip law (null: swarm-by-default forever) | the class flips single-cell per the ONE predicate P(C) = (≥ m=5 audited rows in the trailing k=20 window) ∧ (median audited lift at matched-invoice ≤ 0) — the same predicate as NULL-1, never a second threshold | standing (mechanics P2.5c′, from slice ECON-S3) |
| **ECON-VER-1** | two-tier verification economics (null: panel-every-round) (the spend half of seat 05's VER-1 scheduler drill) | seeded judge-bed e=0.15: two-tier spend ≤40% of panel-every-round at equal champion accuracy; the growth cap refuses the 21st percent and the refusal receipt appears in the run log | P3 (from slice ECON-S6) |

### Conductor / surfaces (rows: seat 08)

| id | organ (its null) | bar | rung |
|---|---|---|---|
| **SUR-1** | router + six-rule cross-check (null: router-only parse — the LIVE commander.py:185 shape) | shared trap corpus `bench/golden/traps.jsonl` (≥60 utterances w/ 04's RE-5: count-traps, mode-traps, hypotheticals, "handful" vagueness, corrections) → action ≥95%; **count fidelity 100% on stated counts; zero fleet actions on chat/mode-trap**; conflicts ask; the null demonstrably fails rule-3 traps (F27) | P2.5e′ (from slice SUR-s3) |
| **SUR-1d** | degrade ladder (null: cloud-only router — live shape) | blackhole the router endpoint mid-session → local-router parse OR the exact printed `hc run …` line; zero dead-air turns | P2.5e′ (from slice SUR-s3) |
| **SUR-2** | narration struct + floor + containment (null: free narration from run text) | fault injection (doctored structs, missing receipts, prettifier drift seeds) → every narrated numeral exists in a receipt-derived struct; tri-state verbatim; synthesis never rendered verified; downgrades counted | P2.5e′ (from slice SUR-s3) |
| **SUR-3** | F7 coalesce (null: no-coalesce ingress — every paste executes, the lived melt) | 20 identical `(issuer,verb,params_hash)` envelopes in 10 s across CLI+HTTP+MCP → exactly 1 execution, 20 chains (1 primary + 19 alias acks + mirrored results), state recomputable by folding `_ops` | P2.5e′ (from slice SUR-s1) |
| **SUR-4** | receipt-chain consistency (null: in-memory status dict) | (a) phone-shaped POST; laptop `hc top` shows it p95 ≤ 1 s; (b) kill Conductor mid-run; restart → SAME cmd_id chain to terminal, zero re-issue, zero duplicate runs, `recovered` emitted | P2.5e′ (from slices SUR-s1/s2) |
| **SUR-5** | MCP task projection (null: tasks-incapable polling client) | task-capable + task-incapable clients run the same 3-min tournament → both terminal with identical structs; `input_required` surfaces an H3 park; task_id ≡ cmd_id verified | P3 (from slice SUR-s4) |
| **SUR-6** | deterministic slot cmd_ids + dead-man class rule (null: wall-clock scheduler, no dedup; notification=any-cursor) | kill conductor across a cron slot (catchup skip + once) → slot fires ≤1×; watch-storm 50 events/5 s → 1 run; unattended H2 with ONLY a headless SSE tail → degrades to H3 hold at deadline-minus-grace | P3 (from slice SUR-s5) |
| **SUR-7** | read-only viewer (null: a writable dashboard) | endpoint fuzz (+ 10's adversarial corpus) → zero writes (db file hash unchanged — no write-capable connection exists to fail with); full history renders against a bare medium.db, Conductor dead | P3 (from slice SUR-s6) |
| **SUR-8** | golden path (null: README-only onboarding) | fresh VM, stopwatch → first synthesis ≤ 15 min, ≤ 7 commands, one `.env` edit; resume-after-kill green | P3 (from slice SUR-s6) |
| **SUR-9** | CLI output/exit contract (null: prose-only output) | every verb under `--json` parses 100%; exit codes conform incl. **6** (completed-without-convergence) | P2.5e′ (from slice SUR-s2) |
| **SUR-10** (new) | stage-ratchet narration filter (null: stage-blind narration) | at simulated Stage-1b, a stripped-signature privileged record is neither executed nor narrated (refused(auth) + absent from narration struct); downgrade attempts surface as counters | P2.5e′ (inferred: rides SUR-s1 AUTH + SUR-s3 narration) |

*(MIG-SUR — the surface/fleet version handshake — is seat 01's row; see the kernel group.)*

### Substrate (rows: seat 09)

| id | organ (its null) | bar | rung |
|---|---|---|---|
| **PREFLIGHT-LITE-1** | box-guard battery, S9.1 (null: a fabric that boots on `/mnt/c` and silently WAL-corrupts, or claims gold-durability with no pragmas) | Inject each box failure (`HYPERCELL_HOME=/mnt/c`; unset `synchronous`; clock skew after resume; missing memory cgroup; dead local lane) → the matching guard fires with the right state + fix string; `max_honest_sandbox_class` correct; no failure passes silently. | P2.5a′ (from slice S9.1) |
| **PREFLIGHT-1** | full battery, S9.2 (null: v1's assume-and-flap — a declared RuntimeClass trusted without a smoke pod; a declared netpol trusted unenforced) | Inject each lived F4 failure (2nd containerd; `FORWARD DROP`; WSL2 idle-off; missing RuntimeClass; image not in k3s ns) → matching guard fires; `G-GVISOR`/`G-NETPOL-ENFORCED` require the smoke/canary probe, not the declaration. | P2.5d′ (from slice S9.2) |
| **HC-7-v2** | phase-A substrate + seal, S9.3 (null: the live `converge.py` — candidate in the oracle's own subprocess; stdout-scraped score; self-hang→INVALID exclusion) (joint drill — the contract half is seat 05's TP-1, whose wording drills ≥9 spoofs incl. oversleep + report-file forgery; 06's ACT-GATE-1 supplies attempts 7–8) | ≥8 spoofs (table D.3), **zero passes AND zero exclusion-evasions**; **ablation**: disable the substrate half → ≥1 filesystem/answer-key/network spoof succeeds; disable the contract half → the stdout `SCORE=` spoof succeeds. "Closed" = the log query `isolation.actual ≥ required ∧ ¬degraded`. | P2.5d′ (from slice S9.3) |
| **CLAIM-1v5** | warm pool + claim, S9.5 (null: a cold pod create ~1–5 s on every spawn; a `rebuild()`-on-open that is O(ledger)) | p95 spawn→bound **≤ 250 ms** against a warm pool, line-itemed (claim-bind ≤50 + wake ≤25 + nucleus-open ≤100 [= NUC-2] + first-frame ≤50 + slack 25); the open path performed **no full rebuild** (fold-cursor telemetry); pool exhaustion returns explicit REFUSE, never a silent hang; a cold-cursor cell is excluded from the bar (slow path, visible). | P3 (from slice S9.5) |
| **SHELF-1** | shelf affinity + presence, S9.5 (null: a resume that genesises an empty nucleus under a used claim-id — identity corruption) | Kill a runner mid-run → resume re-binds on the shelf node (marker survives, F10); force a resume onto a wrong node → REFUSE `shelf_absent`, never empty re-bind; destroy the shelf node → explicit receipted restic migration, then resume; no silent empty-nucleus genesis. | P3 (from slice S9.5) |
| **FORK-1** | ledger-fork, S9.6 (null: a fork that full-copies — no reflink on ext4 — or lets a cell mutate a sealed segment) | Same-shelf fork moves **zero bytes** (hardlink; verify inode sharing); child's immutable prefix byte-identical to parent's sealed segments; cross-node fork copies/lazy-refs and is still exactly-once (`effect_scope=lineage`); a `nobody` cell cannot mutate a sealed segment (privileged seal). | P3 (from slice S9.6) |
| **BACKUP-RESTORE** | continuity, S9.7 (null: HA-at-N=1 theater; a raw WAL-copy backup that tears; a blind act-retry on restore) | Full cluster-loss → restore → re-bind claim-ids → idempotent resume; **zero double-fires** across the pending act set; every in-doubt act reconciled (never blind-retried); leases fold still-held + reconcile from receipts before any new reserve; post-restore certificate matches the no-catastrophe certificate; `VACUUM INTO`, never raw-copy. | P3 (from slice S9.7) |
| **PARITY-1** | local-lite honesty, S9.7 (null: a box that makes a full-strength isolation claim on degraded substrate) | Same run under compose-local and k3s (HC-5 sibling); on Linux bare, `podman --runtime=runsc` closes HC-7; on WSL2+k3s where `G-GVISOR` fails, a first-party clean-provenance candidate runs class-2-locked with `degraded:true` on every receipt, a cell-touched-untrusted candidate REFUSES, an external candidate REFUSES; Windows bare → all untrusted exec REFUSES at `max_honest_sandbox_class 1`. Each honest outcome passes; a silent full-strength claim on a degraded box is the only failure. | P3 (from slice S9.7) |
| **HC-7-DRILL-ON-TRUE-CLASS-3** | degraded-path guard, S9.3 (null: certifying a degraded box using the degraded box) | The HC-7-v2 drill passes on a **true** class-3 box (VPS/VM, all-GREEN) BEFORE any class-2-locked path is trusted anywhere. | P2.5d′ (from slice S9.3) |
| **MIG-DEPLOY** | preflight↔build seam, S9.4 (null: a floating `:local` tag; a MAJOR rollout that corrupts a parked run) | MINOR image bump rolls with a mixed-version fleet live, zero dropped runs; MAJOR bump drains at a round boundary; a run parked under vN resumes under vN+1 (claim-id rebind version-blind). | P2.5d′ (from slice S9.4) |
| **SECRET-0** (new; seam 10) | sandbox secret isolation, S9.2 (null: a class-3 pod that inherits the spine's provider keys) (seat 10's class-3 no-secretRef rail wording folds here; the SEC-7 id names the R8 taint gate at assembly) | No pod in `hypercell-sandbox` mounts `hypercell-providers` or any Secret (admission assert); inject a manifest that tries → rejected; a candidate that reads `/proc/1/environ` finds no provider key; drilled as spoof row #13. | P2.5d′ (from slice S9.2) |
| **AS-GATE** (new; agent-sandbox adoption) | CRD-adoption gate, S9.2/S9.5 (null: importing the CRD as a dependency before it earns it) | On stock k3s (no GKE), a `SandboxClaim` MUST bind a warm gVisor pod **< 2 s** with a surviving+snapshottable PVC to be adopted as a claim/park backend; until then the StatefulSet + ledger-fork mechanism stands and the CRD is refused. Records the probe result each run so adoption is evidence-gated, never faith-gated. | P2.5d′/P3 (from slices S9.2/S9.5) |

### Security (rows: seat 10)

| id | organ (its null) | bar | rung |
|---|---|---|---|
| **SEC-1** | trust-tagged frame assembler, `frame.py` (null: v1 `as_data()` string wrap) | a 200-case injection battery (AgentDojo-style + encoding-class `٤` + EchoLeak GET-exfil) → **0** control-flow changes; the string-wrap null leaks ≥1 (the forged-closing-fence case) | P2.5a′ (from slice map) |
| **SEC-2** | post-ACL, `firewall.py` `post()` (null: v1 sender-trusting `is_directive`) | non-conductor minting `receipt`/`verdict`/`oracle_gen`/`command`, or any cell naming `_ops` → **refused 100/100**; a member `presence{phase}`/`chat`/`submission` → **passes 100/100**; a member-posted `act_receipt` passes ONLY where the member is the executor principal (R3), else refused (member row aligned to presence{phase} per R1/R14) | P2.5b′ (from slice map) |
| **SEC-3** | Stage-1b signature verify (null: v1 unsigned convention) | with trigger fired: unsigned/wrong-key `command` refused; signed verifies; **signature-strip downgrade → `refused/downgrade`** (the ratchet, B.6.3), never Stage-0 fallback | P2.5d′ (from slice map) |
| **SEC-4** (=CELL-7) | attenuation at the spawn gate + the anti-fork-bomb guards (null: v1 no per-cell scope, no rate wall) | 100 spawn-attenuation races → child never acquires a tool/egress/harm-ceiling/dollar the parent lacked; **0** scope-escalation, **0** budget-minting; **a fork-bomb hits the rate + budget wall (per-issuer spawn-rate cap → `refused/rate_capped`); when gate p95 > 2 s the spawn-lease escape carries ≤N frozen-manifest children** | P3 (inferred — Stage-2 rung; ungated in 10's P2.5 slice map) |
| **SEC-5** | Stage-3 refusal (null: v1 would execute on convention) | an inbound directive from an un-spawned principal → **`refused/federation_unavailable`**, never executed | standing (inferred — the Stage-3 REFUSED law; ungated in 10's P2.5 slice map) |
| **SEC-6** | trifecta gate — spawn + ingress legs (null: v1 no gate) | a 3-true role manifest → refused; each waiver policy exercised; scoped-act cell provably never holds all three at once (**receipt query, not a promise**); ingress leg fires as a fold on first untrusted fetch | P2.5a′ (from slice map) |
| **SEC-7** | the provenance-taint gate (null: author-intent trust) | a candidate authored by a cell that ever executed an untrusted-content tool run, offered class-2 by a mis-configured manifest ⇒ REFUSED with a typed receipt naming the taint source, 100/100 over the seeded corpus; the same candidate at class-3 runs | P2.5d′ |
| **SEC-8** | redaction + ingress 401 (null: v1 no redaction / no auth) | a planted fake key via a tool-result body → **0** appearances in ledger/Medium/exports; off-box unauth `POST /command` → **401** | P2.5d′/e′ (from slice map — redaction half d′, 401 half e′) |
| **SEC-EXPORT** | signed `hc export` verify (null: v1 raw copy, unverifiable) | flip one byte in an exported chain → `verify` fails at the exact leaf; a bundle with `secret_count > 0` → refuses to export; **verify uses only the public key** (no secret needed) | P2.5d′ (from slice map) |
| **SEC-STRUCT** | structure-over-detection invariant (null: a classifier gate) | disable every classifier → **SEC-1 still passes**; if the result changes, a detection dependency has leaked (design bug) | P2.5a′ (inferred — rides SEC-1) |
| **SEC-PRICE** | pricebook signing + canary (null: v1 unsigned book) | an unsigned or wrong-sig pricebook → refused-on-load; a lane whose canary fingerprint ≠ declared `weights_family` → **diversity contribution de-rated to 0** until re-attested | P2.5c′ (from slice map) |
| **SEC-MCP** | MCP ingress binding (null: v1 empty `mcp.py`) | an MCP token minted for server A, replayed at server B → rejected (RFC 8707 Resource Indicators); a mix-up `iss` → rejected (RFC 9207) | P2.5e′ (from slice map) |
| **SEC-CI** | constitution-vs-code diff — the red-team instrument (null: a wave of human review) | **every MUST in `identity-firewall.md` maps to a test or a named accepted-gap**, checked in CI; an unmapped MUST fails the build (the scout's closing recommendation, institutionalized) | P2.5a′ (inferred — CI gate, lands with the contract file) |

**The shared trap corpus (R12).** SUR-1 (≥60 router utterances) and RE-5 (≥40 intake goals) MUST draw from ONE file — `bench/golden/traps.jsonl` — with per-organ assertion columns; a blind spot caught by either organ bars both. The corpus MUST NOT fork per organ. (F1's lesson made apparatus; F27 is the live evidence for both.)

---

## §16 · Refusals / anti-goals (the discipline that keeps this a fabric, not a toy)

- **No invented wire protocols** (A7) — OpenAI-egress / MCP / the Medium contract / A2A-at-federation only.
- **No self-grading convergence, no consensus-as-truth, no candidate-authored oracle cases** — the oracle is
  external, coordinator-run, and its growth is adjudicated by an authority disjoint from the producers (§5,
  OG-3). Two-phase grading makes this structural: the answer key never enters the sandbox.
- **No rented loop** — no Temporal/DBOS/workflow-engine under the drive plane (A4; F10 proved the owned
  version). The loop, the frame assembly, the ledger, the keys, the oracle execution, and the router are
  never rented. *Rent effectors and tissue; own decisions and records.*
- **No state that is not a fold** (A13) — no coordination structure may live only in a process's RAM (F16 is
  the counterexample the fabric refuses). If it would change a receipt and it cannot be recomputed from the
  log, it is a bug.
- **No unbounded recursion** — the OG-7 staged self-modification ladder + epoch budgets + the cost-per-gain
  ceiling + the sealed-set halt (§5). A Crucible that cannot afford its own skepticism does not run.
- **No SPIFFE/enterprise identity theater at N=1** — the staged ladder (§13); armor arrives with its trigger.
  As of July-2026 no agent-identity standard qualifies (AIMS authz is a draft; AGNTCY lacks revocation; A2A
  signing is optional) — v5 adopts SPIFFE-URI *naming* and refuses the federation *dependency*.
- **No nucleus re-architecture** — the ledger stays truth; temporal-KG / SQLite / vector are *renders*,
  benchmark-gated before adoption, a losing render ships dark. No mandated temporal-KG.
- **No market theater** — no internal token economies, no agent-to-agent payments, no bidding. Dollars are
  the only currency and the operator holds all of them; the economics plane is a governor and a router, not
  a market. The mint/import/tariff vocabulary is A5's spine metaphor, not a mechanism.
- **No provider-side tool execution** — server-side web search / code-interpreter bypasses egress,
  provenance, metering, and receipts; all tools execute through the Membrane or not at all. (The non-obvious
  2026 refusal — providers push the opposite default.)
- **No firewall by classification** — prompt injection is architecturally unpatchable and adaptive attacks
  break >90% of classifier defenses (§13). Security comes from *assigning* provenance at the boundary
  (trust-tagged frames) and from depriving the agent of the lethal trifecta, never from a classifier that
  *gates*. A classifier MAY observe; it MUST NOT gate.
- **No default swarm for closed-world judged tasks; no un-nulled swarm credit** — the refuse-to-swarm law and
  the null-flip law (§12/§5); an explicit operator override is honored and receipted with the null warning.
- **No free-swarm in the constitution until HC-10 passes** — experimental config only; the north star MUST
  NOT depend on it.
- **No PRM as the oracle** — process scores advise allocation (deny-extension only), never seat a champion
  or appear in a receipt.
- **No cell that hard-requires a cloud tier to close its loop** — the local floor is sovereign (the island).
- **No verb #8, no noun #9, no axiom #14** — the admission tests (§3) are law.

**The honest inventory (the kernel seat's ruling; v2 said eleven, v5 says nine — and shows why).** v2 counted
eleven "contract artifacts" by mixing three implementation singletons (one cell runtime, one Conductor, one
Medium) and the falsifier suite into the count — a category error: those are *code and apparatus*, not
separately-versioned contracts (the singleton law — exactly one cell runtime, one Conductor per fleet epoch,
one Medium per culture — moves to the refusals above as an implementation invariant; the falsifier index
versions with this constitution). The true inventory is **nine separately-versioned contract files**, exactly
the nine version axes of the pairing law (§3): six noun-contracts (`role.md`, `nucleus.md`, `wire.md`,
`run.md`, `command.md`, `identity-firewall.md`) + three verb-plane contracts (`oracle.md`, `act.md`,
`pricebook.md`). Fleet and Substrate are deliberately contract-less — their state is fold-class or
probe-class (a versioned Fleet or Substrate schema would be a smuggled tenth contract; refuse it). Each
contract ships with a machine-checkable JSON-Schema mirror under `contracts/schemas/` (the mirror the v1 repo
planned and never created — generated lockstep twins, not separate artifacts). Payload schemas
(CommandEnvelope, `oracle_gap`, `compact`) ride the wire contract; the render family (the spend ledger, the
oracle library, the lineage index, the null ledger, frame manifests, the substrate report) are non-artifacts
by the Fold Law — rebuildable from the log. **If the list grows past nine contract files, something must have
earned its row by a written admission filing (§3.2); if it cannot name its noun or verb-plane, it is
smuggled.**

**Degeneracy, measured (the coherence bar — ONE line-item with organ labels, stated canonically in
`contracts/command.md` and cited everywhere, R10):** `hc ask` = **1 metered cognition call + 2 Medium
appends** (`command` + `cmd_receipt{phase:result}` in `_ops`) **+ 2 nucleus records cell-side** (action +
outcome — the resume substrate; `outcome_for(idem)` is what makes a re-issued ask exactly-once, so the
nucleus half is load-bearing, not ceremony; NUC-9 bars its cost) **+ 0 plane-side LLM tokens.** Queue reads
are folds, not appends; econ quote/reserve/commit are conductor-internal ledger records, not Medium traffic.
The skeptic sees one arithmetic with organ labels, not three numbers — and the moment `hc ask` costs more
than this, §0's degeneracy promise is broken.

---

## §17 · Boundary laws — the sibling constellation

hypercell is sovereign and depends on none of these; each is a reference or an optional peer over protocol.
**Adopt semantics, refuse dependencies** is enforced here, once, for all of them.

- **KEEL** — a d3 cell MAY use KEEL as its deep-cognition backend *over protocol only* (`cognition.served_by:
  keel`, `mcp://keel/*`); deleting KEEL degrades a d3 to a functioning d2 (the island floor at the depth
  ceiling). hypercell never edits a KEEL contract.
- **Intercom** (×3 variants) — hypercell's Medium is a de-novo reimplementation informed by all three, and
  Intercom is the **living reference implementation** of what §9 formalizes: the append-only bus, the
  insight-scheduler (fan-out → external-oracle grade → Pareto-prune → refine → converge → EIG/disagreement
  gate), the headless `kubelet.py` walk-away driver, and the ten-tab read-only viewer. v5 restores Intercom
  v0.1.5's disagreement gate (F12) that v1 dropped, and §9 states for each Intercom mechanism why it is right
  or how v5 sharpens it (wake binds to JetStream `consume()` not the deprecated push; `sync_interval` is
  server-level so gold rests on the anchor rule, not rented fsync; the registry matches the running code).
- **REEL** — the nucleus's deep tier is REEL-shaped (rings + Tape + the narrative/factual register split);
  hypercell implements the pattern, not the code.
- **FLOTILLA** — the source of the `act` / wager / receipt / harm-class semantics; hypercell adopts them
  without the full witness/treaty/wager constitution.
- **THE_BRAIN** — the max depth of a single cell (d3); hypercell does not build the brain; a cell *can be*
  one, over protocol. A Hypercell Culture aimed at an organization's core-wire (§12) automates the
  cognitive-glue nodes a human used to hold — the wider arc REEL → KEEL → THE_BRAIN → HYPERCELL climbs
  (memory owned → substrate owned → loop owned → society owned). v5 is the fabric made complete enough to
  host all of it; it builds the fabric, and keeps the resonance in mind.

**The 2026 industry (adopt semantics, refuse dependencies — the dated verdicts are in §13).** kagent, Dapr
Agents, the Google Agent Sandbox / `agents.x-k8s.io` CRD, and the CNCF "is a Pod the right unit for an agent?"
debate all converged on hypercell's own promotion model (a warm-pool claim, not a pod-per-cell mandate); v5
adopts the *pattern* on stable k3s today and treats the CRDs as a drop-in backend behind a falsifier
(§11, AS-GATE). MCP and A2A are interop targets over protocol, never dependencies. Named to interoperate
with; imported from none.

---

## §18 · Migration — v1 (live) → v5, and every migration after it

**The adoption epoch (HONEST-EPOCH, the one legal big-bang).** v5's own adoption is the single legal
"big-bang" wire MAJOR (v0.1 → 5.0.0): the presence merge and the 17-type registry land WITH the version
spine that makes every later change lawful. Logs predating the spine get a **synthetic genesis** at
adoption (`chain_adopted_at_seq: k`); the chain starts there; prior records read under frozen pre-spine
defaults, forever — the contract says so rather than pretending tamper-evidence predates itself. One
pattern, three uses: synthetic-genesis-at-adoption · `oracle_gen` reads-absent-as-g0 · chain-starts-at-
adoption. Legacy trust tags follow R13's narrowed carve-out (nucleus.md §14): pre-adoption
`percept{source: operator}` reads `trust: operator`, every other legacy percept reads `external`;
post-adoption records carry membrane-stamped tags with no source fallback, ever.

**The file-level map lives where it belongs.** Every contract closes with its `## Migration from live v1`
note (H7, `contracts/_TEMPLATE-HEADER.md`): the exact live files/tables it supersedes with `file:line`
anchors, which fields survive/rename/die, its HONEST-EPOCH statement, and the first build slice that makes
it live. The repo-wide rule is **behavior-preserving first** (the RE-1 refactor lands under the live repo's
29 green tests before any additive change), and a v0.1 manifest MUST still apply under v5 with defaults
plus one deprecation warning per renamed field.

**Version identification (recap; law in `_TEMPLATE-HEADER.md` H5).** Genesis records carry the 9-tuple
census; writer upgrades append `command{kind:contract_bump}` INSIDE the hash chain (outside it a version
claim can be retro-forged); records between bumps read at the last declared version; detached artifacts
(manifests, exported certificates, pricebooks, backups) carry an explicit `contract: <name>/<semver>`
stamp; `fleet_versions()` folds genesis/presence/bump records into `{principal → census}` and the
preflight refuses mixed-MAJOR (MIG-3).

**Legality matrix:** within one MAJOR, any MINOR/PATCH skew is legal fleet-wide — *that is the operational
definition of MINOR*, and MIG-1 tests it, not asserts it. Across MAJORs: never live-mixed; the epoch record
is the barrier.

**PROCEDURE M-MINOR (rolling; no drain):**
1. `hc migrate plan` → census fold + delta report (which principals, which contracts).
2. Conductor appends `contract_bump{…}` (D-gold, in-chain).
3. New spawns use the new version; existing cells run to natural end. Mixed skew is legal (R1–R4 carry it).
4. `hc migrate verify` → census shows no pre-bump writers after the horizon; conformance battery C1–C12 green.

**PROCEDURE M-MAJOR (epoch; the drill that earns the name "live fleet migration"):**
1. Plan + census; REFUSE if any principal reports an unknown MAJOR (MIG-3).
2. Gate: Conductor stops admitting new runs (Fleet → `migrating`).
3. Barrier: every running Culture drains to its **next round boundary** (converge rounds are natural barriers;
   event-time termination makes parking safe) or parks (`persist`; park == graceful crash, the F10 resume
   object).
4. Quiesce acts: in-flight H1+ acts run to receipt or land `unknown` (reconciled on resume); no new dispatch.
   `res:durable` reservations (batch) are NOT cancelled — they survive the epoch and reconcile after.
5. Snapshot: substrate backup (restic + `VACUUM INTO`). **This is the rollback point.**
6. Epoch record: `migration_epoch{n→n+1, census_before, census_after, barrier_merkle}` appended D-gold,
   in-chain, on the Medium.
7. Upgrade images/Conductor/Medium (image labels carry the census); preflight re-runs; refuse mixed-MAJOR.
8. Re-spawn: claim-ids rebind **version-blind** — *identity outlives contracts* (A3 extended); nuclei fold
   via R6 adapters; parked Cultures resume by the F10 path; the resumed Governor state folds from spend
   records (F16's fix), so caps survive the epoch too.
9. Regrade only if the oracle contract MAJOR'd AND the comparability rules demand it; old receipts remain
   valid at their stamped `gen#digest` + version forever.
10. `hc migrate verify` → census clean; MIG drills green; Fleet → `active`.

**Rollback:** before step 7's first new-MAJOR D-gold write: restore the step-5 snapshot + old images (cheap,
total). After: **roll forward only** — append-only logs make true rollback a lie; a forced downgrade is
REFUSED by preflight unless operator-flagged, and then old readers survive on R1 (new-version records read as
unknown-preserved), degraded but uncorrupted.

**The drills that make this section falsifiable** (bars in §15): MIG-1 (MINOR skew mid-tournament, replay
equality both readers) · MIG-2 (M-MAJOR park→upgrade→resume; budget = cap − folded pre-epoch spend) ·
MIG-3 (census gate refuses unknown MAJOR) · MIG-4 (rollback point restores clean) · MIG-5 (three unknown
fields round-trip byte-identical) · MIG-SUR (old `hc` vs new `hcd`: typed refusals naming both versions,
zero silent misexecutions).

---

## §19 · Glossary & closing

**Glossary (one line each).** cell = the depth-invariant atom, a durable identity ephemerally instantiated ·
nucleus = a cell's private ledger (truth) + renders (rebuildable views) · membrane = the cell's sole I/O +
the injection firewall (a customs office) · Medium = the shared append-only hash-chained firewalled log + the
run engine + the stigmergic blackboard · Culture = a swarm convened on one goal, one topology, one oracle ·
fleet = the whole commanded ensemble · Conductor = the control plane that never thinks (the moment plane logic
needs cognition it spawns a metered cell) · substrate = k3s + volumes + secrets + sandbox classes · **warrant**
= the evidence, act-receipt, or honest label a claim carries; nothing crosses naked or mislabeled · **the
conservation law of trust** = trust is never minted inside the fabric, only imported and priced; no organ
outlives its null; not even the operator is exempt · **the Fold Law** = every durable structure is a
deterministic fold over an append-only log; kill the process, the knowledge re-folds · **organ** = any
mechanism whose removal would change a receipt · **act** = the only world-touching verb, harm-dialed H0–H3
(H0 = a read with the warrant kit waived; H0 governs *mutation*, exfiltration rides the trifecta plane) ·
**the three receipt planes** = `act_receipt` (the world below, executor-minted), `cmd_receipt` (the operator
above, conductor-minted), `receipt` (the bar, conductor-minted) — each a receipt nobody can mint about
itself · **two-phase grading** = candidate execution in a class-3 sandbox over case *inputs only* → a behavior
artifact → grading with no candidate code loaded and the answer key never in the sandbox; the F3/F13/HC-7
closure · **the null** = arm-zero, one strong cell at matched dollars, the swarm's standing control;
class-lifecycle-derived; the null-flip law flips a class's default off (never a retirement) when its lift ≤ 0
at matched-invoice over k=20 runs · **the Crucible** = the oracle-growth organ (archive × epochs ×
disagreement gate) · **oracle generation** = a versioned bar; scores compare only within one · **the
Divergence Meter** = the one instrument that grows the oracle, trips on consensus collapse, and measures
diversity · **render** = a rebuildable view of the ledger; delete it and you lose speed, never truth ·
**register** = a memory's kind (factual, citation-bound; narrative, cite-blocked) · **durability classes** =
**D-gold** (fsync'd before the effect/ack) vs **D-chatter** (group-committed) · **retention classes** =
**R-forever** (the provenance skeleton, never eligible) · **R-run** (pinned until the culture's terminal
verdict, then archivable) · **R-decay** (TTL'd working set — the stigmergic evaporation parameter) ·
**the exit tri-state** = `{passed, gate, invalid}` — a candidate's outcome is a scored pass, a scored miss
(candidate-attributable), or apparatus failure (charges no arm) · **purpose** = an escrow scope a dollar is
reserved against (production · verification · oracle_growth · tool · maintenance) · **StackReceipt** = the
body schema of the `receipt` type (the oracle's grading of a submission or an act) — a receipt's *body*, not
a fourth receipt plane · **lane** = an economic
binding {sku, effort, cache_mode, batch} over a priced SKU (weights@host/service_tier) · **weights family** =
the diversity-bearing axis; blind spots follow the weights, not the host · **claim-id** = `run/role/index`,
the identity a nucleus binds to · **role manifest** = the defaults preset over one field space that turns the
uniform cell into a specific agent · **oracle** = the external, coordinator-run, pre-registered check stack; a
versioned contract artifact, never a noun · **arm** = a named approach the scheduler allocates dollars over ·
**trust tag** = the transport-assigned, non-suppliable provenance label {operator, receipted, tool, external}
that fences control flow from data · **the trifecta / Rule of Two** = private-data × untrusted-content ×
external-comms; all three ⇒ refuse to instantiate · **task class** = the content-addressed signature (L0/L1/L2
backoff) that null-ledgers, oracle libraries, and refuse-defaults key on · **stigmergy** = coordination
through the shared environment · **champion** = the max-oracle-score candidate · **depth dial** = d0 reflex →
d3 brain, one runtime · **the refuse-to-swarm law** = the fabric declines to default to a swarm where a single
strong cell wins, and says so · harm class = H0 log · H1 auto · H2 delayed (dead-man clause) · H3
human-always · island floor = the local tier no cloud loss can starve · core wire = the org's irreducible
chain of cognitive-glue nodes (fractal: step / cell / org).

---

**The essence, once.** One fabric, from one commanded cell to a self-organizing fleet: **cells fan out,
results converge, every convergence is judged from outside the swarm — and now every answer carries the
evidence that warrants it or an honest label of its absence, every act carries the wager reality will grade,
every dollar is metered at a real price, every command is parsed once and narrated only from the log, no
swarm takes credit it did not beat its own single-cell null to earn, the oracle itself grows exactly where the
passing swarm's disagreement shows it blind, even the operator's own judgments are sampled and priced — and
beneath all of it, nothing the fabric knows lives anywhere but as a fold over one append-only log, so that any
process can die and its knowledge re-folds from records that outlive it.** v1 proved the fabric can run; v2
made it honest with itself; v3 built the machines; v5 assembles them and can be *resumed from any stage*
because the deepest thing the running system taught us is joined by the deepest thing the building of this
document taught us: that a swarm's greatest danger is its own agreement, and the only cure is to keep
importing trust from outside it and to keep growing the outside when the inside runs out of ways to be
surprised — and that the only way to build something too large for one mind to hold is to make every durable
thing a fold, so no crash is ever a loss. Kubernetes taught the industry to run containers this way;
hypercell runs minds this way, demotes Kubernetes to the metal underneath, and adds the laws a fleet of
containers never needed: **nothing crosses naked, and nothing is held that cannot be re-folded.** The cell is
depth-invariant — a hello-world at one end, a whole brain at the other. The swarm is scale-invariant — a
Culture at one end, an automated organization at the other. The order of construction is the order of trust.
And no organ, not even the swarm itself, outlives its null.

*Build the stem — it lives. Complete the Medium, land the warrants, close the sandbox, price the dollars.
Convene the Culture; run the null beside it. Let the oracle start grading — and grow it when the swarm goes
blind. Assign provenance at the boundary. Command the fleet. And keep every durable thing a fold.*

**· v5.0 · 2026-07-16 · C:\hypercell_v5\HYPERCELL_V5_ARCHITECTURE.md · pending operator ratification ·**
