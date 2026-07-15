# CONTRACT: oracle — the external falsifier (the keystone)

**Status:** v0.1 DRAFT. The single most load-bearing rule in the fabric (constitution §7, A5). No Culture
converges on its own say-so. RFC-2119.

## The Externality Principle (MUST)
Ground truth for convergence originates **outside both the model and the operator**. The oracle is:
- **External** — a test suite / checker / linter / benchmark / metric-vs-pre-registered-target for code; a
  **diverse judge-panel across provider families** for prose (judges must not share a blind spot).
- **Coordinator-run** — executed by the conductor over a candidate's *declared output*. **A cell NEVER
  scores its own work.** A `receipt` is only valid from `conductor`/coordinator (wire.md). Receipts are
  non-mintable.
- **Pre-registered** — the target/tolerance/gate is fixed BEFORE the run. Moving a bar after seeing a number
  is forbidden.
- **Exit tri-state** — never conflated:
  - `0` = **pass** (full score).
  - `1` = **gate fired** = a real negative result (a scored miss).
  - `2` = **error / timeout** = **INVALID**, excluded from the ranking. NEVER a zero score (a zero silently
    poisons the champion selection).

## The falsifier contract (MUST)
```
<cmd> <candidate_path>   →   prints  SCORE=<float 0..1>   on stdout,   exits 0|1|2 per the tri-state.
```
Modes (`run.md` `oracle.mode`):
- `golden` — declared-output hash must match a frozen expected hash (reproduction/two-pass judge).
- `target` — a declared metric vs a pre-registered `target` ± `tolerance`.
- `gate` — a named gate must not fire.
- `judge-panel` — N independent judges (different provider families) score; aggregate; the aggregate is the
  receipt. For non-executable (prose/design) candidates.

## Convergence (MUST)
Champion = the max-`SCORE` candidate (the MCTS best-node). Converged when `champion_score ≥ target` AND
stable for `stable_k` non-improving proposals, OR `max_rounds` reached, OR the budget hard-stop fires.
Every receipt is logged at both ends and is auditable. `oracles/` holds example falsifiers.
