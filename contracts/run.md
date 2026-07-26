# CONTRACT: run — the run manifest, the planes, the topologies, intake, certificates, and the fleet

**Contract:** run · **Version: 5.1.0** (semver; see `contracts/_TEMPLATE-HEADER.md`) · **Status: CONSTITUTIONAL.**
**Date:** 2026-07-16 · rev 2026-07-25 (P3 resolution). RFC-2119.
**Pairing (H2):** run.md ↔ the **Culture** (noun 4) — the converge / route / schedule policy plane.
**Emit/read (H4):** strict-emit / liberal-read — reader law §R12. **Operator boundary (R5):**
strict-both — the run manifest and its overrides validate STRICT at `hc apply` (unknown field =
error, never an ignored extra).
**Schema mirror:** `contracts/schemas/run.schema.json` (generated in lockstep, same commit).
**Migrates from:** v0.1 (live repo) — migration note §R12.
**Falsifiers:** RUN-M1, RE-4, RE-10, CERT-1, FLEET-0..3, NULL-1, SINGLE-ARM-ATTR (constitution §15).

A **run** is the declarative unit of swarm work: a manifest the operator (or a surface acting for them)
applies, a Culture the Conductor reconciles toward it, and a **verdict with a recomputable certificate**
coming back. One driver executes every topology; the topology is a **policy row, never a loop**.

```
Topology := (dispatch_policy, feedback_policy, tick_end_policy, termination_unit, verdict_kind)
```

The four planes — CONVERGE, ROUTE, SCHEDULE, DRIVE — are pure functions over **ledger-derived state**
(the FOLD, §R8). Nothing durable lives outside the log (Fold Law, A13). `run_tournament` / `run_drive`
/ `run_fanout` as sibling code paths are **REPEALED**; `hc drive` survives as CLI sugar for
`tournament × {dispatch: ucb}`.

## R1 · The manifest (`hc apply -f run.yaml`)

```yaml
# ── run.yaml v5 ─────────────────────────────────────────────────────────────
schema: hypercell.run/5.0        # Conductor REFUSES unknown MAJOR, warns+ignores unknown MINOR fields
run_id: ipv4-r2                  # stable; claim-ids derive: <run_id>/<slot>/<index>[+fork<k>]
goal: |                          # operator's wording VERBATIM (F1: wording is a diversity axis;
  Implement is_valid(s)...       #  the null arm receives THIS wording — §R7)
class_hints: [code, python]      # optional operator hint to the intake classifier (§R6)

topology: tournament             # tournament | mcts | pipeline | mapreduce | fanout | free-swarm

roster:
  - slot: refiner                # slot name; claim-id = ipv4-r2/refiner/0..count-1
    role: roles/refiner.role.yaml     # pinned at run_open → …@sha256:…
    count: 4
    diversity:                   # PER-SLOT diversity vector (A6): declared here, MEASURED at round 1
      weights_family: [deepseek-v3, glm-4.5, qwen3]   # cell i ← family[i mod |families|]
      wording_variant: [v0, v1, v2]  # ids into the role's variant table
      seed: auto                 # auto → distinct per cell; or an explicit list (reproducibility)
      temperature: [0.2, 0.5, 0.8]
      on_missing: shrink         # missing family key at open: shrink (drop cells, WARN, record
                                 #  realized vector) | refuse. Weights are NEVER silently substituted.
    refiner_mode: fresh          # fresh (default) | persistent — round-structured topologies only.
                                 #  fresh: each round's producers are NEW cells reading the frontier
                                 #  (Intercom's dogfooded explorer→refiner shape; no anchoring on own
                                 #  prior candidate). persistent: cells carry nuclei across rounds
                                 #  (needed when the task itself is stateful). Fold-visible either way.
    lane_prefs: { effort: low, batch: allowed }   # hints; econ floats host/effort/cache/batch,
                                 #  MUST NOT float weights (diversity axis)
  # arm-zero MAY be declared; if omitted the Conductor INJECTS it for every convergent topology (§R7)

oracle:
  ref: oracles/ipv4_check@sha256:…   # the oracle STACK artifact (internals: contracts/oracle.md) —
                                 #  THE single home (R18) of every trust-side predicate knob:
                                 #  target, tolerance, divergence_eps,
                                 #  contested_blocks_champion, contested_cap
                                 #  growth{enabled, granularity}, the probe corpus pin, and the
                                 #  contested dissent bound all live in the stack's `convergence:` /
                                 #  `growth:` blocks, frozen at run open. EXCEPTION [R25]: `null_arm`
                                 #  is a NULL POLICY, not a trust predicate — it lives in THIS file's
                                 #  `null:` block below, never in the stack.
                                 #  The manifest MUST NOT
                                 #  restate them — two homes is the F14 drift class at manifest
                                 #  level (observed live: `divergence_epsilon` vs `divergence_eps`,
                                 #  contested_cap 3 vs 2). Probe results NEVER enter feedback
                                 #  packets (§R5) regardless of stack settings.
  gen: 3                         # generation PIN; scores compare only within a generation (A12)
  invalid_rate_halt: 0.25        # RESTORED v2 §5 "R%" — a RUN-side guard and manifest field (05
                                 #  §5.2 names it so): INVALID rate > R% ⇒ HALT `oracle-sick`
                                 #  (never converge on the minority that graded)

grounding: none                  # none | sampled | required (A11). Floor keyed to oracle kind:
                                 #  judged ⇒ `required` is the legal minimum; tighten only.

operator_audit:
  sample_rate: 0.10              # RESTORED v2 §5 "k%": blind second adjudication of operator-
                                 #  adjudicated cases (mechanics: contracts/oracle.md; the field is
                                 #  manifest-declared so the certificate can echo it)

budget:
  usd_cap: 0.50
  purposes:                      # v2 §7 split, ENFORCED as escrow scopes (07): sum ≤ usd_cap
    production: 0.35
    verification: 0.10           # a RESERVE: production cannot eat it (BUDGET-RAZOR §R4.3)
    oracle_growth: 0.05          # ≤ 20% of usd_cap by law
    tool: 0.0
    maintenance: 0.0
  per_provider_concurrency: { deepseek: 4, glm: 1 }   # a REQUEST against fleet-scoped caps (§R10)
  pricebook: pricebook.yaml@sha256:…   # PIN; the certificate cites it

termination:                     # EVENT-TIME, never wallclock (parking cannot corrupt convergence)
  max_rounds: 3                  # unit per topology row (§R3)
  stable_k: 2                    # consecutive VALID scoring events with no champion improvement
                                 #  under one gen (F14's one-definition fix). KNOB HOME (R18): the
                                 #  MANIFEST owns the termination{} knobs, invalid_rate_halt, null:,
                                 #  and operator_audit{}; the oracle STACK's `convergence:` block
                                 #  owns {target, tolerance, divergence_eps, contested_cap,
                                 #  contested_blocks_champion} — oracle.md §3. ONE home each.
  max_gradings: 60               # absolute oracle-call cap (outermost event bound)
  self_clock_min_events: 1       # R14 guard (s6-15): a SELF-CLOCKED round_open is legal only after
                                 #  ≥ this many new VALID scoring events since the previous
                                 #  round_open; under-frequency rows are VOID-AT-FOLD (round-churn
                                 #  cannot burn max_rounds toward a premature exhausted verdict)
  wallclock_alarm_s: 3600        # an ALARM: fires PARK + operator notice, never a verdict

null:                            # §R7; the two-mode class lifecycle (v2 §5 × ECON T4 synthesis).
                                 #  GRAMMAR IS CANONICAL PER R17: this block is oracle.md §12.1's
                                 #  NullPolicy block VERBATIM (seat 05 owns it, R4; regenerated by
                                 #  COPY, s2-21); the earlier `null_policy:{mode, family, floor,
                                 #  audit_rate}` spelling is REPEALED — one grammar, no translator.
  null_arm: required          # [R25] KNOB HOME. required | omitted. `required` (the default for every
                              #   convergent topology) means the Conductor INJECTS arm-zero if the
                              #   roster omits it, and BUDGET-RAZOR refuses to return a champion whose
                              #   null never ran (`verdict{exhausted:null-starved}`, §R7.1). This is a
                              #   NULL POLICY, not a trust predicate — it does NOT live in the oracle
                              #   stack's `convergence:` block (oracle.md §3 carries only the pointer).
  mode: auto                  # auto (derive from class lifecycle — the default and the law) |
                              #   matched (force) | floor (force; refused for unsettled classes)
  # DERIVATION (auto):
  #   UNSETTLED class (< m matched/audited rows at the deepest L-level with evidence)
  #     => mode: matched — the v2 shape exactly: ONE null cell, protected arm OUTSIDE UCB
  #        allocation, matched-dollar reservation taken AT RUN OPEN before any swarm arm
  #        dispatches (protected = reserved first; a tight cap cannot starve the control).
  #   SETTLED-CALIBRATED class (>= m matched/audited rows)
  #     => mode: floor — inline null arm at a protected floor reservation (floor_frac of the
  #        production cap, reserved at open) + audit_rate of runs replay the FULL matched-
  #        dollar null to keep calibration fresh. Only matched/audited rows are flip evidence.
  pin:                        # the null's family is PRE-REGISTERED, never chosen by the
    family: deepseek          #   machinery under audit:
    provenance: ranking-artifact   # operator-pin | ranking-artifact (dated external ranking,
    ref: "artifact://rankings/lmarena-2026-07-01#sha256=…"      #   facts-with-dates style)
    as_of: "2026-07-01"
  m: 5                        # settledness + flip-evidence threshold (§12.4)
  floor_frac: 0.10            # floor mode: protected reservation fraction
  audit_rate: 0.25            # floor mode: fraction of runs replaying the matched null —
                              #   0.25 × k=20 window = 5 = m: the flip predicate is
                              #   satisfiable at default rates BY CONSTRUCTION

task_class: auto                 # auto ⇒ intake computes the FIX-3 hierarchy (§R6); an explicit
                                 #  {l0,l1,l2} object overrides WITH a receipt

priority:                        # multi-run fleet scheduling (§R10)
  class: standard                # interactive | standard | maintenance (default by surface:
                                 #  hc talk → interactive; hc apply/run → standard; routines → maintenance)
  weight: 1.0                    # fair-share weight within the class
  preemptible: true              # interactive MAY set false

partial_view: true               # round-structured convergent topologies: MUST default true (§R5.2)
resume: auto                     # auto (`hc resume` re-enters, §R9) | manual
resume_from: null                # import artifacts+history from a prior run_id (new run, new id)
isolation: pooled                # pooled | isolated | hardened → substrate classes 0–3 (09)
```

### R1.1 · Validation laws (Conductor-side, at `hc apply`)

1. Convergent topologies (`tournament|mcts|pipeline|mapreduce`) REQUIRE `oracle` and a roster whose
   **realized** `weights_family` count ≥ 2 (A6). Fewer ⇒ REFUSED unless an operator waiver (receipted;
   certificate carries `diversity_defect`). `fanout`/`free-swarm` are oracle-exempt; `free-swarm`
   additionally materializes its experiment harness (§R5.6).
2. `budget.purposes` MUST sum ≤ `usd_cap`; `oracle_growth ≤ 0.2 × usd_cap`.
3. `grounding` ≥ the legal floor for the oracle kind (judged ⇒ `required`); tightening only.
4. Every `role`/`oracle`/`probe_corpus`/`pricebook` ref MUST resolve and is sha256-pinned at freeze.
5. Slot names unique; claim-ids derive deterministically (`run/slot/index`) — resume is a pure function
   of (manifest, log) because of this.
6. `stable_k`, `max_*` are positive integers; `invalid_rate_halt ∈ (0,1]`; `contested_cap ≥ 1`.
7. Admission ALSO posts `pool_floor{n}` — the topology's peak concurrent dispatch width (tournament:
   Σ slot counts; ucb/mcts: 1; fanout: n) — the warm-pool sizing hint (seam: 09).

### R1.2 · Canonicalize · freeze · refuse-on-mutation

At `run_open` the Conductor canonicalizes the manifest (RFC-8785 JCS over the YAML-parsed object;
every file ref resolved to `path@sha256`), posts `presence{phase:genesis, manifest, manifest_sha256}`
(run-open — R19: never a `run_open` type), and **freezes
it**. `hc apply` of a changed manifest under the same `run_id` is REFUSED — a change is a new run,
which MAY declare `resume_from: <old_run_id>`. A verdict that cannot name the exact bytes it converged
under is not recomputable. *(Falsifier RUN-M1, PART D.)*

## R2 · The four planes (pure functions over the FOLD)

### R2.1 · CONVERGE — outcome-authoritative champion + the fold plumbing for the convergence predicate

```
state: champion{arm, cand, artifact_sha, score, outcome, receipt_seq}, stable, signatures{cand→per-check},
       divergence, contested_streak, null_recorded, gen, invalid_rate

update(receipt r for candidate c of arm a):                  # one deterministic fold step
  1. gen is folded from the conductor `oracle_gen` record — THE one gen-bump driver (§R8.2; R14
     guard, s6-15); on bump: champion = ∅; stable = 0
                            # bar moved ⇒ stability evidence VOID; survivors regraded before any verdict
                            # a receipt whose r.oracle_gen ≠ the folded gen is STALE — idempotent
                            #  re-scoring keys on (submission_seq, oracle_gen); it never bumps gen itself
  2. attribute(r) per the matrix §R2.5:
       INVALID (apparatus|panel) → log; NO champion effect; NO stable effect; run invalid_rate updates
       GATE / PASSED → continue
  3. signatures[c] = { chk.name: chk.failure_signature for chk in r.checks }   # per-check (05); case
                            # rows live behind checks[].report_ref, conductor-ACL, NEVER on the receipt
  4. key(c) = (r.outcome == PASSED, r.score, -r.seq)         # outcome-authoritative; earliest-receipt tie-break
  5. if key(c) > key(champion): champion = c; stable = 0
     else: stable += 1                                       # VALID receipts ONLY reach this line —
                                                             #  F24's fix is structural, not a guard clause

converged() := oracle.converged(R, run)                      # THE convergence predicate — oracle.md
                                                             #  §5.3 (EIGHT clauses; the sole home:
                                                             #  "nothing else may declare convergence"
                                                             #  — LB2/s2-04). This engine restates
                                                             #  NOTHING; it supplies the fold inputs
                                                             #  the predicate reads — champion receipt
                                                             #  R, stable counter, probe divergence,
                                                             #  contested_streak, invalid_rate,
                                                             #  null_recorded — and calls.
```

Interim (until TP-3 lands at P4 — the s5-06 schedule fix, mirrored from L-RUN-2): the divergence
clause (oracle.md §5.3 clause (iv)) reads satisfied iff `|passers| ≤ 1`; where a probe corpus is
pinned, D is computable early from cached behavior artifacts.

Seam (unchanged from wave adjudication #1): 05 owns `grade()` / `probe_divergence()` / receipt & verdict
fields / regrade semantics; the run engine owns WHEN they are called, champion selection over receipts,
round/epoch boundaries, certificate assembly.

### R2.2 · ROUTE — capability filter → liveness → priced index → escrowed placement

```
ROUTE(need, arm) → Placement | REFUSE:
  1. feasible = [ad ∈ registry : coverage(need.caps, ad) > 0 ∧ ad.live
                 ∧ ad.harm_ceiling ≥ need.harm ∧ need.tools ⊆ ad.tools]   # capability = HARD filter
  2. feasible == ∅ → REFUSE(no-capability)
  3. quotes = econ.quote(frame_manifest, lane_space(need), purpose)       # 07's signature, verbatim
  4. order by (coverage DESC, usd_effective_expected ASC, load ASC)
  5. for q: rsv = econ.reserve(q.lane, q.usd_worst, scopes=[fleet, run, purpose], group_id?)
       rsv ≠ REFUSED → return Placement(cell, lane, rsv)
  6. all refused → REFUSE(first reason)          # drive parks the task / starves the arm

Idempotent high-frequency H0 acts MAY draw on per-cell tool-lane LEASES (06-T10) — same reserve()
interface, drawn down locally, reconciled at renewal; the run engine is lease-oblivious.

CLAIM/STEAL (mapreduce shards, pipeline stages, routed subtasks): claim = a Medium record with
wire.md §3.1's field names — {task, resource, lease_s, release} (s2-24; this file never respells
them); heartbeat re-posts before lease_s expires; once stale, any cell MAY post a fresh claim for
the same task — steal = post-after-expiry, positional (wire.md §7.3), no marker field; LOG ORDER
adjudicates (battery C4). A landed submission without a
live claim is scored but flagged `orphan` — paid-for evidence is never discarded.

Reservation durability: res:sync (ordinary call — folds to ∅ on resume; receipted-or-lost, lost work
re-dispatches under idem) | res:durable (batch/racing legs — carries provider batch_id; folds STILL-HELD;
released only by a receipted H0 reconciliation act: ok|expired|lost). SPEND-HOME (01's C-5 ruling,
07's retraction #694): escrow truth = the CONDUCTOR'S OWN LEDGER (RESERVE/COMMIT/RELEASE/SPEND are its
fsync'd nucleus records; scope counters fold from them); fleet-visible attribution = the `cost{}`
field-group riding records ALREADY crossing the Medium (the R2 crossing set: receipt, act_receipt,
cmd_receipt, verdict — s2-22). No `spend`
Medium type exists. In-doubt spend: a conductor-ledger RESERVE without its COMMIT reconciles AT WORST
CASE (outcome: unknown) BEFORE the first new reserve; the reconciliation itself is receipted.
```

### R2.3 · SCHEDULE — dollar-UCB over (arm × lane); 2-D prune; failure-set domination

```
state per arm: visits, usd_spent, best, pruned, quarantined   # rebuilt by FOLD from receipts

SCHEDULE(arms) → arm | NONE:
  live = [a : ¬a.pruned ∧ ¬a.quarantined]      # arm-zero: in `live` in floor mode; OUTSIDE UCB in
                                               #  matched mode (its dispatch is reservation-driven, §R7)
  ∃ unvisited → first unvisited
  u = min over live lanes of usd_expected(next pull);  U = Σ_a usd_spent(a)/u
  index(a) = [a.best + c·sqrt(ln U / (usd_spent(a)/u))] / ê_cost(a)     # exploration in DOLLARS (07)
  return argmax index

prune_2D(arms, champion):                      # BOTH clauses required
  a.pruned ⟺ champion.best − a.best ≥ margin ∧ cost_per_point(champion) ≤ cost_per_point(a)

Candidate-level domination (tournament prune) — gen-scoped, two-tier read (05's receipt shape):
  EQUALITY is O(1) off the receipt: checks[].failure_signature = sha256 over sorted REPORTED failed
  case-ids — equal hashes ⇒ equal reported sets ⇒ keep one (cheapest lane), retire the twin from the
  peer set (history keeps both).
  SUBSET/domination reads the reported failed-id SETS from checks[].report_ref (conductor-access-only;
  the pruner IS the Conductor):
  c2 dominates c1 ⟺ same oracle_gen
                    ∧ ∀ check k: failed(c2,k) ⊆ failed(c1,k), with ⊊ for ≥1 k   # REPORTED ids only
                    ∧ score(c2) ≥ score(c1)                                  # holdout-inclusive guard
  Crossing or disjoint failure sets ⇒ BOTH kept (their symmetric difference is the pollination payload).
  Score-margin pruning of a non-superset loser is FORBIDDEN (F1: the plateau was score-shaped).
```

### R2.4 · DRIVE — the only loop

```
DRIVE(run):
  0. OPEN: post presence{phase:genesis, manifest, sha} if absent; state = FOLD(culture span)  # open ≡ resume (R19)
  1. loop:
     a. fleet.parked(run_id)? → PARK (drain ≤ drain_timeout; stragglers cancelled, res:sync released,
        tasks re-queued; post presence{phase:parked, reason}; stop — on-disk object ≡ a crash)
     b. batch = dispatch_policy(state)                       # row, §R3
     c. parallel over batch within granted slots (§R10):
          placement = ROUTE(need, arm);  feedback = feedback_policy(state)   # §R5 packets, partial view
          sub = dispatch(placement, goal, feedback)          # post submission{artifact@sha}
          r   = oracle.grade(sub, stack@gen)                 # 05; receipt POSTED to the Medium (E2 fix)
          econ.commit(placement.rsv, r.cost);  SCHEDULE.update(arm, r);  CONVERGE.update(r)
     d. tick_end_policy(state)                               # prune / pollinate / round++ / gen-bump
     e. STOP (first match):
          CONVERGED → certificate (§R8.1); verdict{kind: verified | verified-with-residual, vs_null, cert}
          BUDGET    → BUDGET-RAZOR below → verdict{exhausted: budget}; a required null still
                      unrun ⇒ verdict{exhausted: null-starved} — NEVER a deliverable champion (s6-06)
          EVENTS    → max_gradings | max_<unit> → verdict{exhausted: events}
          NO-ARMS   → all pruned ∨ starved ≥ starve_k → verdict{exhausted: no-arms}
          ORACLE-SICK → invalid_rate > R% → HALT verdict{exhausted: oracle-sick}    # v2 §5 restored
          OPERATOR  → stop command → verdict{stopped}
          APPARATUS → invalid_streak ≥ 3 across ≥ 2 arms → PARK + alarm             # INVALID-STORM law
  2. Non-verdict exits (PARK) leave NO verdict; resume re-enters at 0.

BUDGET-RAZOR: production cap hit mid-tick ⇒ already-produced submissions are scored from the
verification reserve (that is what the reserve protects); still unscored when verification is also
exhausted ⇒ recorded `unscored`, EXCLUDED from champion selection, LISTED in the certificate residual.
BUDGET-RAZOR × the null (s6-06): budget exhaustion while the run's required null is unrun yields
`verdict{exhausted: null-starved}`, never a champion — a champion-by-exhaustion with no null
comparison is the exact dodge the predicate's null clause (oracle.md §5.3 viii) exists to prevent.

Event-time termination: stable_k / rounds / gradings count SCORING EVENTS; wallclock only PARKs.
A parked-and-resumed run converges IDENTICALLY to an uninterrupted one (falsifier FLEET-2).
```

### R2.5 · The attribution matrix (v5 final — structural, never content-inspected)

| Row | Failure site | Outcome | Arm visit | Arm usd | Run spend | Guard |
|---|---|---|---|---|---|---|
| **production** | provider call fails pre-artifact (429/5xx/timeout) — no artifact exists | *no receipt* | NO | NO | committed | retry/backoff inside the metered path (F2); exhausted ⇒ task re-queued, lane degraded (econ lane stat) |
| **candidate** (phase-A) | candidate execution fails in sandbox: nonzero exit / hang / OOM | **GATE** | YES | YES | committed | self-sabotage is not evasion (v2 §5); timeout is a GATE here — F13's fix |
| **candidate** (differential) | phase-B fails on THIS artifact while peers grade clean in the same round | **GATE** (re-attributed) | YES | YES | committed | 05's differential re-attribution — the crafted-artifact-crashes-grader channel, closed at the attacker |
| **apparatus** | phase-B harness/oracle/dep failure, non-selective (`failed_phase: B`, exec-infra or grading-infra) | **INVALID** | NO | NO | committed → run-level `apparatus_usd` | ≥2 consecutive on one arm ⇒ availability quarantine (paused; zero score/visit effect; lifts on reconcile); ≥3 across ≥2 arms ⇒ STORM PARK; run-level R% halt |
| **panel** | judge panel unparseable / post-recusal quorum < 2 | **INVALID** (`oracle-sick`) | NO | NO | committed | as apparatus; storm + R% laws apply |

**Single-arm topologies (tournament×ucb, mcts, pipeline — s6-14):** the differential row's premise
(a clean sibling graded in the same round) structurally cannot hold when dispatch is one candidate
per round. For those rows a grader-crashing artifact is re-graded per oracle.md §2.3's single-arm
rule — a SECOND independent grader instance, or a golden known-good artifact in the same round; a
selective crash that survives the second grader is candidate-attributed by that comparison, never
left `apparatus`. Where neither backstop is available the certificate residual MUST carry the flag
`differential re-attribution unavailable (single-arm topology)` — the open channel is visible,
never silent. Mechanism home: oracle.md §2.3; this file binds only WHEN it fires.

Supersedes v3 §2.5 (apparatus visits+usd — repealed by wave adjudication #10 + differential rule) and
v2 §5's "counts as a bandit visit and burns budget" (spend commits to the RUN — the cap is real money —
but the bandit index charges only rows attributable to the arm).

## R3 · The topology table (six topologies, seven printed rows, one loop)

The count convention, stated once (s2-23): §R1's `topology` enum has SIX values. The table prints
SEVEN rows because `tournament × ucb` is a dispatch PRESET of the tournament row (`hc drive` sugar,
never a seventh topology); `free-swarm` is one of the six but is admitted only as an experiment
harness (§R5.6), never a convergent topology.

| topology | dispatch | feedback | tick_end | termination unit | verdict kind |
|---|---|---|---|---|---|
| **tournament** | all live arms per round (`refiner_mode` governs producer identity) | frontier packets, **partial-view** (§R5.2), per-check failure rows | domination prune → pollinate → round++ → gen-bump check | rounds | `verified` / `verified-with-residual` |
| **tournament × ucb** (`hc drive`) | 1 arm (dollar-UCB) | champion-so-far packet + its signature | 2-D prune; step++ | steps (gradings) | `verified` / `-with-residual` |
| **mcts** | 1 tree node (UCT select → COW expand) | ancestor-path artifacts + signatures | backprop; progressive widening; subtree park | node expansions | `verified` / `-with-residual` |
| **pipeline** | next incomplete stage | upstream artifact (+ gate receipt on retry) | stage gate → advance / retry / poison-halt | stages | `verified` (or `gate` report) |
| **mapreduce** | unclaimed/stale shards (claim/steal) | none | typed merges; **conflict-promote** | shards | `verified` + conflicts[] |
| **fanout** | all arms, once | none | synthesize (coordinator cell) | single round | **`synthesis`** (never verified) |
| **free-swarm** | cells self-dispatch by local rules; drive enforces caps/slots only | stigmergic (the log) | evaporation (compaction TTL) | gradings | experiment report (§R5.6) |

Convergent rows REQUIRE: oracle + seeded-and-measured diversity + injected arm-zero. A topology needing
a bespoke loop step is an ILLEGAL topology — the admission test is stating its five fields and nothing else.
Fanout-synthesis (and free-swarm) is null-exempt BY DESIGN and therefore makes NO dominance claim:
its output is `synthesis` — reported, never celebrated — and carries no certificate; the exemption
is explicit, never inferred (s6-07).

## R4 · Topology mechanics (delta over v3; full state machines carry from the v3 paper unchanged)

- **Tournament**: state machine, resume, packet caps, herding tripwire — v3 §4.1 verbatim, PLUS §R5.2
  partial-view and report_ref-sourced case rows.
- **MCTS**: COW-fork, write-barrier, privacy-correct tree fold (Conductor never reads a nucleus; tree
  renders from Medium fork records; nuclei are audit truth), `effect_scope: lineage` with fail-closed
  H1+ when the lineage index is unreachable, prune=park (stepping-stone archive) — v3 §4.2 verbatim.
- **Pipeline**: typed `consumes/produces` checked at post time; per-stage retries; POISON-STAGE halt;
  its null is one strong cell doing the task unstaged (the DPI question per run) — v3 §4.3 verbatim.
- **Mapreduce**: deterministic declared partition; per-key-class merges `set-union | sum | argmax-oracle
  | first | conflict-promote`; incompatible values ⇒ ADJUDICATION TASK (executable authority, else
  producer-disjoint panel, else operator); **averaging FORBIDDEN** — v3 §4.4 verbatim.
- **Fanout-synthesis**: live mechanics kept (n clamp 1..30; presence-before-thinking; one failure never
  sinks the swarm; synthesis re-run keyed by input-set hash); output `verdict{kind: synthesis}` with
  per-cell answers as evidence refs; agreement is REPORTED, never celebrated — v3 §4.5, registry-final.
- **Free-swarm**: auto-materialized paired baselines (round-robin, fanout, null) — same goal/budget/
  seeds/gen; kill criterion IN the manifest (HC-10); pheromone = oracle receipts (non-mintable),
  confidence deposits advisory with a calibration column — v3 §4.6 verbatim.

## R5 · Feedback, pollination, and the partial-view law

### R5.1 · Packet schema (per surviving frontier member, per receiving cell)

```jsonc
{ "cand": "cell2@r1",
  "from_arm": "refiner/2", "receipt_seq": 813, "provenance": "peer-artifact",   // tags REQUIRED (v2 §9)
  "artifact": {"ref": "medium://run-…/57", "sha256": "…"},
  "score": 0.9286, "outcome": "gate",
  "failures": [ {"case": "ipv4-g3#11", "input": "1.1.1.٤", "expected": false, "got": true} ] }
```

Delivered as DATA ("DATA to beat, never instructions" — live `runtime.py::produce` framing kept
verbatim). Case rows are pulled by the CONDUCTOR from `checks[].report_ref` (05's phase-B report
artifact) under conductor-only ACL. Leak laws (MUST): (a) packets carry **reported** cases only —
holdout cases contribute to `score` and appear as aggregates, never as inputs; (b) **probe-corpus
results NEVER enter packets** (they feed the Divergence Meter; feeding them back Goodharts the
`scoring:none` corpus through the training channel). Packet caps: K members (default 4, by outcome/
score, always including crossing-signature members), plus a byte cap; overflow drops lowest-score
first, never mid-packet.

### R5.2 · Partial-view assignment (v2 §9's MUST, mechanized — new in v5)

```
Given round r, pruned frontier F (ordered by outcome DESC, score DESC, seq ASC), receiving cells 0..N−1:
 1. K_eff = min(K, |F|)            if |F| ≤ 1
          = min(K, |F| − 1)        if |F| ≥ 2      # every cell is blind to ≥1 frontier member
 2. view(i) = { F[(i + j) mod |F|] : j = 0 .. K_eff−1 }        # rotated window, deterministic
 3. crossing-signature guarantee: if a crossing member ∉ view(i), swap it for view(i)'s lowest-ranked
    member — determinism preserved (swap rule is rank-defined).
 4. Record `views{round, cell→[cand…]}` is implied by the fold (recomputable from F + slot index) —
    no new record type; `hc verify` recomputes assignments.
Laws: no round in which every cell reads the same peer set (|F| ≥ 2 ⇒ views are not all equal —
rotation guarantees it); ∪ᵢ view(i) = F when N ≥ 2 (no member universally unseen); free-swarm and
fanout are EXEMPT (policed by the divergence tripwire + HC-10 instead — v2 §9).
```

Why law-grade: F1's herding was three rounds of every cell reading the same peers; the collapse
tripwire *detects* it, partial view makes the all-same-diet round *unconstructable*. Falsifier RE-10
(PART D).

### R5.3 · Refiner freshness (`refiner_mode`, new in v5)

`fresh` (default): each round's producers are newly spawned cells whose frame = goal + packets — the
Intercom insight-scheduler's dogfooded shape (explorers → refiners), zero anchoring on their own prior
candidate. `persistent`: cells carry nuclei across rounds — REQUIRED when the task is stateful
(build-then-extend). The mode is per-slot, fold-visible, and certificate-recorded. Rationale: the F1
plateau had two causes — no failure feedback (fixed by packets) and self-anchoring (fixed by `fresh`);
v1 conflated them.

## R6 · Intake — the d0 classifier, the task-class hierarchy, refuse-to-swarm

### R6.1 · Classification (manifest-first, model-assisted, operator-final)

```
classify(goal, manifest, roles) → (info, verify, task_class, provenance):
 1. VERIFY axis is a FACT: executable ⟺ oracle.ref resolves to a runnable stack ∨ a registered
    oracle-template matches; else judged. Template registration home AND match predicate live in
    oracle.md §8.3 (`template.match: {class_hints_any, goal_regex}` — deterministic,
    first-by-registration-order; b3-01) — this file binds only the run side: templates are
    operator-registered pinned artifacts, and the matched template id is quoted in provenance.
    Candidate-/model-authored oracles are FORBIDDEN (OG-4).
 2. INFO axis, three signals: s1 (deterministic): role.tools ∩ {web.search, web.fetch, connector.*} ≠ ∅;
    s2 (deterministic): grounding == required ∨ class_hints ∩ acquisitive-classes, where
    `acquisitive-classes` is a NAMED operator-registered config set — a pinned artifact registered
    beside the oracle templates (same registration home + registry render, oracle.md §8.3;
    registration/edit is an operator command, receipted). Absent registration the set is EMPTY and
    s2 degrades to `grounding == required` alone — stated in the intake receipt, never silent (b3-05).
    s3 (proposal): a d0 router cell (temp 0, structured output) → {info, confidence, quoted_spans[]};
    quoted_spans MUST be verbatim substrings of the goal text — a span ∉ goal makes the proposal
    unparseable (b3-11). s3 unavailable/unparseable after 1 retry ⇒ treated as a DISAGREEMENT
    (step 3 escalates one question; b3-07).
 3. RECONCILE (Entry-30 law): s3 agrees with (s1 ∨ s2) — precisely,
    `agree := (s3.info == acquisitive) == (s1 ∨ s2)` (b3-10) → classified. Disagreement → `hc talk` asks
    the operator ONE question and records the answer. SILENT DEFAULT OVER A DISAGREEMENT IS A
    CONSTITUTIONAL VIOLATION. s3 alone NEVER classifies (a cross-check, never a fallback — the same
    law that indicts commander.py:185's extractor-as-fallback, 08's finding).
 4. DEFAULT = matrix[info][verify] (v2 §12 verbatim):
      closed × judged        → single strong cell (REFUSE to swarm)
      closed × executable    → small tournament IFF est_gen_cost ≥ 10 × est_verify_cost, else single+verifier
                               (est_gen_cost = econ.quote() over ONE round at declared roster width,
                                at apply time; est_verify_cost = the stack's per-grading estimate ×
                                expected gradings — b3-06)
      acquisitive × executable → tournament / tournament×ucb
      acquisitive × judged   → fanout-synthesis + mandatory act-receipts + cross-family panel
 5. NULL-LEDGER LOOKUP: class flipped (§R7.3) → default = single-cell+verifier; hc talk says it in
    plain language, override always available.
 6. OPERATOR OVERRIDE: always honored, always receipted with the null warning attached (L-NULL).
```

The d0 router is a **named service cell** (`intake/<run_id>/0`): metered, ledgered, receipted — never
an inline Conductor call (the Conductor never thinks; F15's law). Its null: the deterministic signals
alone; if the proposal never changes an outcome over k runs, intake goes fully deterministic (A5).

### R6.2 · The task-class hierarchy (FIX-3, adopted — replaces v3's flat triple)

```
L0 = sha256(canon((oracle_template, toolset, topology_family, goal_schema_sig)))        # exact-task —
                                        # the 4-tuple JCS-canonicalized (RFC-8785) as ONE object:
                                        #  length/domain separation by construction (b3-09)
L1 = (oracle_template, toolset, topology_family)                                        # task shape
L2 = (information_axis, verification_axis)                                              # quadrant
```

`goal_schema_sig := sha256(canon(template slot-fill with literals stripped))` — the matched
oracle-template's slot pattern filled from the goal, with the goal's literal values stripped, then
canonicalized (RFC-8785) and hashed (b3-02). For TEMPLATE-LESS goals L0 is UNDEFINED and
champion-reuse falls back to L1.

Consumers pick their level: champion-reuse L0; oracle library (05) L1; **null ledger + refuse-defaults:
the DEEPEST level with n ≥ m audited rows** (m = 5). Every ledger row carries all three keys plus its
`recompute_span`, so re-classing under a finer scheme is a free re-fold — no evidence is lost by
starting coarse. Split confirmed with 05 (#678: their T9 = this table).

### R6.3 · The intake receipt (posted by the Conductor; the classification's provenance)

This IS a legal wire `receipt` (the b3-03 ruling): wire.md §3.1 widens the receipt `check` enum to
include `intake` and `subject` to admit `{"run": "<run_id>"}` — intake provenance rides a `receipt`,
never a `cmd_receipt`. Posting locus (b3-08): the Conductor posts it into the RUN culture
immediately after `presence{phase:genesis}` and before the first `round_open`;
`intake_receipt_seq` is a run-culture seq (the certificate's `recompute.span` re-derives it).

```jsonc
{ "type": "receipt", "check": "intake", "subject": { "run": "ipv4-r2" }, "run_id": "ipv4-r2",
  "body": {
    "goal_sha256": "…",
    "axes": { "information": "acquisitive", "verification": "executable" },
    "provenance": {
      "verify_fact": { "oracle_ref": "oracles/ipv4_check@sha256:…", "resolves": true },
      "s1": { "fired": true,  "tools": ["web.search"] },
      "s2": { "fired": false },
      "s3": { "proposal": "acquisitive", "confidence": 0.92, "quoted_spans": ["…"],
              "cell": "intake/ipv4-r2/0", "receipt_seq": 122 } },
    "reconcile": "agree",                       // agree | escalated{question_seq, answer_seq}
    "task_class": { "l0": "sha256:…", "l1": ["tmpl:pytest", "tools:none", "tournament"],
                    "l2": ["acquisitive", "executable"] },
    "default": { "topology": "tournament", "source": "matrix" },   // matrix | ledger-flip
    "override": null } }                        // or {by, cmd_seq, null_warning_ack: true}
```

Override flow: an operator override is a `command` (08's envelope) referencing this receipt; the
Conductor applies it, posts the amended intake receipt with `override` filled, and the null warning
text is IN the receipt (the certificate echoes `intake_receipt_seq`).

## R7 · The null (arm-zero): two-mode lifecycle, ledger, flip

### R7.1 · The two modes (v2 §5 × ECON T4, unified — one predicate throughout)

- **matched** (UNSETTLED class: < m matched rows at the deepest class level with data): v2 §5 exact —
  the null is a **protected arm outside UCB**; its **matched-dollar reservation is taken at
  `run_open`** before any swarm arm dispatches (protected = reserved first; a tight cap starves the
  swarm, never the control); it runs the identical oracle loop, the operator's wording, the **union**
  of roster tools, the same grounding, the same generations. Every matched row is calibration-grade.
- **floor** (CALIBRATED class): the null is an **inline UCB arm** with a spend floor ≥
  `null.floor_frac` × production, **reserved at run_open**; the null clause of the convergence
  predicate (oracle.md §5.3 viii) checks the
  floor was honored. At `audit_rate`, the run is followed by a **matched-dollar single-cell replay**
  (same wording, union tools, same gen) — audited rows keep the calibration fresh; v2's "a settled
  class runs the null sampled 1/k" IS this sampling.
- `mode: auto` selects by ledger state; explicit pins are receipted. In BOTH modes `vs_null` publishes
  margin at **matched-production AND matched-invoice** (the operator's unit — never flatter the swarm
  in the unit that reaches the wallet; members per R15: {null_score, null_usd, margin_production,
  margin_invoice}). Escrow mechanics are 07's (#694): matched-mode reservation rides a
  `purpose=verification` sub-scope (the control is calibration apparatus); floor-mode floor rides a
  `purpose=production` sub-scope (the control is a live arm). The comparison UNIT is always matched
  production dollars + matched invoice — the purse never changes the math.
- **Reservation durability (s6-06):** the null's protected reservation — matched-dollar or floor —
  is `res:durable`-class: it survives park/crash and folds STILL-HELD on resume (§R2.2), OR resume
  MUST re-take it FIRST, before any swarm re-dispatch — the same reserved-first ordering `run_open`
  establishes. Either way the invariant "a tight cap starves the swarm, never the control" holds
  ACROSS the resume boundary, and budget exhaustion with the required null unrun terminates
  `verdict{exhausted: null-starved}` (§R2.4), never a deliverable champion.

### R7.2 · The null ledger (one row per convergent run; recomputable from receipts)

```sql
CREATE TABLE null_ledger(
  run_id TEXT PRIMARY KEY,
  class_l0 TEXT, class_l1 TEXT, class_l2 TEXT,   -- FIX-3 keys (all three; deepest-with-n≥m drives)
  ts TEXT, oracle_gen TEXT,
  champion_arm TEXT,                              -- may BE 'null-arm' (run still delivers)
  swarm_best REAL, null_best REAL,
  swarm_usd_production REAL, null_usd_production REAL,
  swarm_usd_invoice REAL, null_usd_invoice REAL,  -- BOTH units (v2 §5). LOCAL LEDGER ONLY: the
                                                  -- production/invoice split is render-side (R15
                                                  -- permits it here); the WIRE join key is the
                                                  -- single `null_usd` in vs_null, never this pair.
  margin_production REAL, margin_invoice REAL,    -- R15 member names (margin_*, never lift_*)
  null_mode TEXT,                                 -- 'matched' | 'floor-inline' | 'floor-audited'
  roster_families TEXT,                           -- JSON: what this evidence is ABOUT (re-arm key)
  recompute_span TEXT                             -- medium [seq_lo, seq_hi]
);
```

### R7.3 · The flip predicate (THE one predicate; NULL-1 and ECON-8 both cite it)

```
P(C) := |{calibrated rows of class C in trailing k=20-run window}| ≥ m=5
        ∧ median(margin_invoice over those rows) ≤ 0
        where calibrated = null_mode ∈ {matched, floor-audited}   (floor-inline rows steer audit_rate
        only — consistent inline losses accelerate auditing — and never flip alone)
FLIP:  P(C) at the deepest class level with n ≥ m ⇒ post command{kind:flip, class, level, evidence[]}
       to _fleet (THE decision carrier — R22: conductor-only, D-gold, R-forever; the bare
       `class_default_flip` record name is REPEALED); intake default for C becomes
       single-cell+verifier (overridable; override receipted).
RE-ARM: iff a new run's roster_families ⊄ ∪(families across the window's calibrated rows) — a genuinely
       new weights family or tool is a new swarm; a count tweak is not. NO re-arm on oracle-gen bumps
       (both arms graded by the same generation; the bar moved for both).
META-GUARD (v2 §5, restored): if the null never wins ANY class on the standing benchmark suite, the
       null is a strawman ⇒ audit parity, operator-blind. If the swarm never wins any, that is HC-3′
       failing at scale — the constitution PUBLISHES it (NULL-1's standing fleet-health bar).
```

## R8 · FOLD, resume, and the certificate

### R8.1 · The certificate (the output type of the named fold; else it is a press release)

```jsonc
{ "cert_version": "5.1",                            // BUMPED: the P3 pass renamed this certificate's
                                                    // vs_null members `lift_*` → `margin_*` and
                                                    // collapsed `null_usd_*` → `null_usd` (R15).
                                                    // A renamed field IS a format change; a reader
                                                    // pinned to 5.0 must not silently mis-read it.
  "run_id": "ipv4-r2", "manifest_sha256": "…", "topology": "tournament",
  "verdict_kind": "verified",                       // verified | verified-with-residual
  "task_class": { "l0": "…", "l1": ["…"], "l2": ["…"] },
  "intake_receipt_seq": 128,
  "oracle":   { "id": "oracles/ipv4_check", "gen": 4, "digest": "sha256:…",
                "lineage": ["g1:…","g2:…","g3:…","g4:…"] },
  "champion": { "arm": "refiner/2", "claim_id": "ipv4-r2/refiner/2",
                "artifact": {"ref": "medium://run-ipv4-r2/812", "sha256": "…"},
                "score": 1.0, "outcome": "passed", "receipt_seq": 813 },
  "convergence": { "target": 1.0, "tolerance": 0.0, "stable_events": 3, "stable_k": 2,
                   "divergence": 0.0, "epsilon": 0.02, "probe_corpus": "probes/ipv4-g3@sha256:…",
                   "contested": false, "contested_streak": 0, "gradings": 22,
                   "invalid_rate": 0.04, "invalid_rate_halt": 0.25 },
  "grounding": { "mode": "required", "citation_precision": 0.97,
                 "domains_per_material_claim_min": 2, "witnessed": true },     // v2 §5 sentence, fielded
  "vs_null":  { "mode": "floor-audited", "family": "pin:deepseek-v3",
                "null_score": 0.9286, "null_usd": 0.024,          // R15 canonical members: {null_score,
                "margin_production": 0.0714, "margin_invoice": 0.0523,  // null_usd, margin_production,
                "swarm_usd_invoice": 0.031,                       // margin_invoice}; a production/invoice
                                                                  // usd split is render-side, never the join key
                "verdict": "swarm-justified" },     // or champion=null-arm → "swarm-not-justified"
  "residual": { "unprobed": ["unicode-digits-beyond-arabic", "ipv6"],
                "ambiguous_escalated": [], "unscored": [],
                "invalid_count": 1, "apparatus_usd": 0.004, "panel_dissent": null,
                "diversity": { "declared": ["deepseek-v3","glm-4.5"], "realized": ["deepseek-v3","glm-4.5"],
                               "round1_divergence": 0.31, "floor": 0.10, "defect": false },
                "views_law": "held" },              // partial-view law held every round (RE-10 recompute)
  "spend":    { "production": 0.19, "verification": 0.06, "oracle_growth": 0.01, "tool": 0.0,
                "total": 0.26, "pricebook": "pricebook.yaml@sha256:…", "in_doubt": 0.0 },
  "recompute":{ "culture": "run-ipv4-r2", "span": [301, 947], "chain_head": "sha256:…",
                "procedure": "hc verify ipv4-r2" },
  "signature": { /* [SECURITY-SEAM: cert-signing] — seat 10: Stage-1b conductor key over the
                    canonicalized cert body; verify procedure and key custody in identity-firewall.md */ } }
```

`hc verify(run_id)`: (1) load span, verify the per-culture hash chain to `chain_head`; (2) `state =
FOLD(span)` — the SAME fold resume uses; (3) recompute every field; diff MUST be ∅ (field-named failure
otherwise); (4) artifact sha spot-check; oracle digest + pricebook pin check; (5) recompute view
assignments (§R5.2) and the flip predicate inputs. *(Falsifier CERT-1.)* Fanout runs emit a `synthesis`
report, never a certificate (L-HONEST-VERDICT).

### R8.2 · FOLD — one derivation; resume = fold, not replay

```
FOLD(culture, span) → PlanesState:
  input filter (COMPACTION-CLOSED — R-forever ∪ R-run only; L-FOLD-CLOSURE conformance; every name
  below is a REGISTERED type or a registered type's phase/kind — the R19 carrier map, registry 17):
    presence{phase:genesis}   [run-open] · round_open · submission · receipt · task · claim ·
    presence{phase:spawned}   [fork: carries forked_from; authoritative lineage = nucleus gold] ·
    task[conflict: operator-organ adjudication work] · command{kind:adjudication} [+ its bar-effect
    oracle_gen{kind:operator_audit}] · oracle_gen [conductor — THE gen-bump driver, s6-15] ·
    presence{phase:parked} · presence{phase:resumed} · verdict
                                        (NO spend type: spend folds from the cost{} field-group
                                         on receipt-class records + the conductor's own ledger)
  for msg in replay(culture, span) in seq order:
    presence{phase:genesis} → pin manifest; init arms (+ injected arm-zero); derive claim-ids
    round_open → round++; gen-bump ONLY iff its oracle_gen references a conductor `oracle_gen`
                 record at-or-before its seq — the conductor oracle_gen record is THE one gen-bump
                 driver (R14 guard, s6-15). A round_open citing no such record is VOID-AT-FOLD
                 (keys on record EXISTENCE — a fold input — never a body parse); a self-clocked
                 round_open under the manifest's self_clock_min_events floor is likewise
                 VOID-AT-FOLD. On bump: champion/stable reset; regrade-required
    submission → arms[sender].produced++; artifacts[cand] = {ref, sha}
    receipt    → attribute (§R2.5) → SCHEDULE.update / CONVERGE.update (ORDER IS SEMANTIC: stable
                 counts non-improving VALID events); cost{} → per-purpose spend accumulators
    task/claim → claims table (log-order adjudication)
    presence{phase:spawned, forked_from} → MCTS tree (nodes/edges/write-barriers)  [R19: "fork"]
    task[adjudication] / command{kind:adjudication} → mapreduce accumulator  [R19: conflict flow]
    presence{phase:parked|resumed} → lifecycle;  verdict → terminal
  reservations: res:sync → ∅; res:durable → STILL-HELD (settled only by a receipted reconcile act)
```

Resume (`hc resume <run_id>`): (1) `presence{phase:genesis}` → frozen manifest (sha mismatch = refuse); (2) derive
ALL claim-ids → re-bind nuclei; a claim-id with prior receipts but an ABSENT nucleus is a REFUSAL,
never an empty re-bind (identity corruption > crash); shelf-node affinity applies (§R10); (3) `state =
FOLD`; (4) `econ.reconcile()` — in-doubt at worst case + poll every `res:durable` batch_id — BEFORE the
first new reserve; (5) idempotent re-scoring keyed `(submission_seq, oracle_gen)`; gen-bump pending ⇒
regrade survivors first; (6) re-enter DRIVE at 1a. Park-resume and crash-resume are THE SAME CODE PATH;
the parked record is metadata, NEVER load-bearing. *(Falsifier RE-4.)*

## R9 · Run lifecycle

`RUNNING | WAITING-BATCH | PARKED(reason) | TERMINAL(verdict)` — WAITING-BATCH holds `res:durable`
reservations and ZERO fleet slots (dollars locked at the provider, results coming); PARKED reasons:
`preempted | apparatus | budget-wait | operator | wallclock-alarm`. All transitions are `_fleet`
records; DECISION records (flip/grant/revoke/park/resume) ride
`command{kind:flip|grant|revoke|park|resume}` — conductor-only, D-gold, R-forever (R22; already
instruction-bearing, so L-FOLD-CLOSURE holds); `hc top` renders from the log, never from
Conductor memory.

## R10 · Multi-run fleet scheduling

```yaml
# fleet.yaml (Conductor-scoped, operator-owned; freshness discipline as the pricebook;
# provenance/signing: [SECURITY-SEAM: fleet-yaml])
providers: { deepseek: 8, glm: 1, cerebras: 2 }   # account-level concurrency truth (F2)
usd_rate_cap: 2.00/h
classes:
  interactive:  { priority: 0 }
  standard:     { priority: 1 }
  maintenance:  { priority: 2, headroom_only: true }
min_run_quantum: 4      # ticks before a (re)started run may be parked (anti-thrash)
max_park_age: 2h        # aging boost at 1×; operator notice at 2×
drain_timeout: 60s
```

```
ALLOCATE (on any run state change or fleet tick):
 1. strict class priority (interactive > standard > maintenance-headroom-only).
 2. within a class: weighted max-min via deficit round-robin.
 3. capacity hysteresis: the allocator owns CAPACITY (concurrent calls per run per provider), sticky
    while need persists; PLACEMENT stays the econ plane's priced index (warm-loss priced in quote()
    over a 3-call horizon) — one decision each, the two cannot fight. Hard stickiness only for
    in-flight batch groups (legs already paid).
 4. preemption: interactive arrives ∧ no headroom → victim = argmax cost_per_point over preemptible
    standard runs (tie: lowest weight, fewest prior parks); park at the NEXT TICK BOUNDARY.
 5. USD-rate governor: fleet burn > cap → stretch tick admission (lowest class first), then park by
    (4)'s ordering. Never mid-tick.
 6. starvation guard: parked_age > max_park_age ⇒ deficit boost; > 2× ⇒ operator notice in hc top.
 7. batch-aware parking: a run whose next dispatch is a res:durable leg with window_close_eta beyond
    the park horizon SHOULD transition WAITING-BATCH rather than hold slots (quote() exposes
    {window_close_eta, expiry} — seam: 07).
PARK(run) = a graceful crash: stop admitting ticks → drain in-flight sync work (≤ drain_timeout;
stragglers cancelled, res:sync released, tasks re-queued) → post presence{phase:parked, reason} (R19).
Park NEVER cancels
res:durable legs. The on-disk object is indistinguishable from a crashed run; RESUME is §R8.2.
Realization is written against 09's CLAIM API, never a CRD (adopt semantics, refuse dependencies —
09's #696 pushback adopted): class-0 pooled = drain asyncio tasks + close nuclei (the live shape,
fanout.py:80); class-2/3 = `park(run_id)` flushes + seals the live segment + releases the ordinal
(pod deleted, PVC RETAINED); resume = `claim(claim_id, role_digest, node_affinity?) →
bound{ordinal} | refused{reason: pool_exhausted | shelf_absent}` — the F10 path at culture width.
agents.x-k8s.io Sandbox MAY later serve as a claim/park BACKEND behind the same Medium claim records
iff 09's AS-GATE falsifier passes; the log shape never changes either way. Resume carries hard
node-affinity to the nucleus shelf; `shelf_absent` on a claim-id with prior receipts ⇒ receipted
restic MIGRATION, never an empty re-bind (one admission gate with 02's genesis check — two reasons,
same REFUSE).
```

**The allocator's null (new in v5 — the mortality clause applied to my own newest organ):**
**FIFO-serial** — no allocator: one culture at a time, arrival order, full provider caps. Falsifier
FLEET-0 (PART D): if the allocator cannot beat FIFO-serial on interactive p95 latency at equal total
dollars with zero starvation on the standing mixed workload, the fleet RUNS FIFO and the allocator dies.

## R11 · Records this engine posts (registry alignment — 03's final registry, 17 per 01's C-2/C-5 rulings)

`presence{phase:genesis}` (run-open) · `round_open` · `submission` · `receipt` (conductor-only ACL;
oracle grading — posted TO the Medium, the E2 fix, D-gold; carries `cost{}`) · `verdict{kind}` ·
`task` (including operator-organ adjudication work, the "conflict" carrier — R19) ·
`command{kind:adjudication}` (the operator's decision entering; bar-effect =
`oracle_gen{kind:operator_audit}`) · `claim` · `presence{phase:spawned, forked_from}` (the fork
signal; authoritative lineage = the two gold nucleus records) · `presence{phase:parked|resumed}` ·
(the live `spawned` type is repealed into `presence{phase}`) · `_fleet` records — decision records
(flip/grant/revoke/park/resume) ride `command{kind:flip|grant|revoke|park|resume}` (conductor-only,
D-gold, R-forever — R22; the wire reserves `_fleet` beside `_ops`); render chatter MAY ride `status`
(R-decay) but NO constitutional fold reads it — decisions NEVER ride status-class records
(L-FOLD-CLOSURE). Every name above is one of R1's 17 types or a declared phase/kind of one
(the R19 carrier map; presence phases parked/resumed and command kind adjudication land as MINORs in
wire.md/command.md). NO spend type (spend-home ruling: conductor ledger + `cost{}` on crossing
records); NO engine-private types — anything not in the registry does not cross the wire.

**Certificate spend recompute is a TWO-LOG consistency check:** `hc verify` sums the span's `cost{}`
groups per purpose AND folds the conductor-ledger escrow records for the run scope; the two totals MUST
agree (a divergence names the missing receipt or the unposted commit). One number, two derivations,
zero trust in either alone.

## R12 · Reader liberality + migration from v0.1 (the live shape)

**Reader law (G4's fix, 01's emit/read split):** readers MUST ignore unknown fields on MINOR bumps and
MUST refuse unknown MAJOR. Writers MUST emit every REQUIRED field. Absent-field defaults are THIS
table's, never reader-invented.

| v0.1 field (live) | v5.0 | Note |
|---|---|---|
| `run_id`, `goal`, `topology` | same | `topology` gains `fanout` (live but undeclared) — six values (§R3's count convention) |
| `roster[].{role,count,diversify}` | `roster[].{slot,role,count,diversity{…},refiner_mode,lane_prefs}` | `diversify: true` ⇒ `diversity` defaults table (temps+angles become wording_variants); slot defaults to role stem |
| `oracle.{mode,cmd,target,tolerance}` | `oracle.{ref,gen,invalid_rate_halt}` — every other knob moves INTO the stack artifact's `convergence:`/`growth:` blocks (R18: one home, frozen at run open) | `cmd` becomes the stack's single check; `mode: judge-panel` becomes a judged stack (05); target/tolerance migrate into the stack |
| `budget.{usd_cap,per_provider_concurrency}` | + `purposes{}`, `pricebook@sha` | purposes default: production 70% / verification 20% / growth 5% / tool+maint 5% |
| `termination.{max_rounds,stable_k}` | + `max_gradings`, `self_clock_min_events`, `wallclock_alarm_s` | `stable_k` SEMANTICS FIXED: valid scoring events (was: rounds in topology.py, steps in drive.py — F14) |
| `seed_diversity: true` | per-slot `diversity` vectors | measured at round 1 (divergence floor), not asserted |
| `isolate: false/true` | `isolation: pooled/isolated/hardened` | maps 0→pooled, 1→isolated; hardened new (class-3) |
| *(absent)* | `class_hints, operator_audit, null (R17 grammar), task_class, priority, partial_view, resume, resume_from` | defaults as §R1; absent ⇒ defaults, warn once |

Live-repo migration is **behavior-preserving first** (RE-1 refactor under the 29 green tests), then
additive: a v0.1 yaml MUST still apply under v5 with defaults + one deprecation warning per renamed field.
