# CONTRACT: oracle — the trust plane (the keystone)

**Contract:** `oracle` · **Version:** 5.1.0 (semver; see §16 versioning) · **Status:** v5
CONSTITUTIONAL DRAFT · **Date:** 2026-07-16 · rev 2026-07-25 (P3 resolution) · RFC-2119.
**Pairing:** the bar (verb-plane) — converge's grading half; generations; the Crucible's shape
(_TEMPLATE-HEADER H2 row 7).
**Owns:** the Externality Principle mechanics; two-phase grading; the oracle stack; judge machinery;
control probes; the oracle library + generations (the Crucible); case admission; holdout + sealed
set; the Divergence Meter; the single-cell null; the operator-as-organ; verification scheduling.
**Reads:** run.md (manifest fields `oracle:`, `null:`, `R%`, `k%`, `wrong_answer_cost`), wire.md
(payload types `receipt`, `verdict`, `oracle_gen`), pricebook.md (`weights_family`, lane costs),
act.md (evidence-validation primitives), identity-firewall.md (signing, post-ACL).
**Emit/read:** strict-emit / liberal-read (_TEMPLATE-HEADER H4, R1–R6). **Reader liberality:**
readers MUST ignore unknown fields and MUST apply the defined default when a
versioned field is absent (each addition below states its absent-reading). Writers MUST emit every
REQUIRED field. Unknown `kind` values on `oracle_gen` records are preserved, never dropped.
**Operator boundary:** strict-both (R5) — the stack block, the `null:` grammar (§12.1), and
operator-statute commands (§15 SEC-1) validate STRICT; an unknown field there is an error.
**Schema mirror:** `contracts/schemas/oracle.schema.json` (generated, versioned in lockstep,
same commit).
**Migrates from:** live v1 `C:\hypercell\contracts\oracle.md` v0.1 + `converge.py`/`judge.py`/
`oracles/ipv4_check.py` (§M).
**Falsifiers:** JUDGE-1 · CRUCIBLE-1 · CRUCIBLE-2 · DIV-1 · NULL-1 · OPER-1 · SEC-CANARY ·
SINGLE-ARM-ATTR (index: ARCH §15).

---

## §1 · Law: the Externality Principle and the conservation of trust

1. **Trust is never minted inside the fabric; it is imported across the boundary, and every import
   is priced.** The imports are exactly: executable ground truth (the case set), disjoint-authority
   adjudication, the operator's word (priced per §13), and dated external artifacts (rankings,
   pricebooks) carried facts-with-dates.
2. The oracle is **external** · **coordinator-run** (cells never score their own work; receipts are
   non-mintable — conductor-only per the wire type-ACL) · **pre-registered** (the stack and bar are
   frozen at run open; only the case-set *generation* moves, and only by §9's procedure) ·
   **exit tri-state** honored (§2.4).
3. **No organ outlives its null** (the mortality clause). This contract's own organs each carry a
   null and a bar: the panel (single-family panel → JUDGE-1), growth (static G0 → CRUCIBLE-1), the
   sealed set (no sealed set → CRUCIBLE-2), the meter (no tripwire → DIV-1), the swarm itself (the
   single-cell null → NULL-1), the operator's imports (unsampled adjudication → OPER-1).
4. **Honest degradation.** Every mechanism that cannot run (no second family, no corpus, no canon,
   no controls) MUST degrade to a named, certificate-visible weaker state (contested / residual /
   advisory / provisional), never to silence and never to a fabricated verdict.

## §2 · Two-phase grading (TP-1) and the report-file protocol (TP-2)

**LAW TP-1.** Candidate **execution** and oracle **grading** MUST be separate phases in separate
trust domains. Phase A executes the candidate in its required sandbox class over case **inputs
only** (expected values MUST NOT enter the sandbox) and produces a behavior artifact (§4.1).
Phase B grades behavior artifacts oracle-side with **no candidate code loaded**. The v1
single-subprocess protocol (`<oracle_cmd> <candidate_path>`, `SCORE=` scraped from stdout) is
repealed as a grading path (it survives only as the §2.5 shim).

**LAW TP-2.** The grading channel is a **file the runner names** (`--report <path>`); the grader
writes one JSON report there (§4.2); the runner reads only that file. Candidate stdout is NEVER a
grading channel. Grader stdout/stderr are captured as human-facing artifacts only. A missing,
empty, or malformed report file is phase-B INVALID (never a silent zero) — the runner pre-creates
the file 0-length and treats non-JSON content as apparatus failure.

### 2.1 Sandbox requirements (the substrate half; seat 09 owns mechanics)
- Untrusted/external/adversarial candidate code: **class-3, no exceptions** — refuse to run below.
- LLM-generated candidates (our own cells' output) MAY run locked class-2 (no-net triple +
  runner-observed exit + no answer-key mount) where class-3's preflight probe fails (the blessed
  source-tier, v3 adjudication #9) — **only while the authoring cell is clean first-party under R8
  (`acquired_trifecta.untrusted_content = false`); an untrusted-touched cell's output is
  adversarial-EQUIVALENT: class-3-or-REFUSE, no class-2 fallback, even on WSL2** (the taint law,
  identity-firewall.md B.4); `isolation_actual` is stamped on EVERY receipt and any
  degradation is a visible certificate flag claiming no HC-7 closure.
- The sandbox is per-candidate; limits are per-case (`limits`) and per-phase (`limits_total`).
  Sandbox availability is a PREFLIGHT FACT (smoke probe), never a docs fact.

### 2.2 Attribution (structural, never content inspection)

| failure | receipt | who pays | who learns | bandit visit |
|---|---|---|---|---|
| phase-A candidate failure (crash / hang / resource-kill / malformed artifact) | `gate`, `attribution: candidate`, `failed_phase: A` | production line | arm quality (a scored miss) | arm keeps the visit |
| candidate-mimicking-apparatus (inducing grader failure from inside the sandbox) | `gate` — phase-A structural attribution; the grader never shares the candidate's fate | production line | arm quality | arm keeps the visit |
| lane failure at dispatch (429 / outage — F2) | no oracle receipt — never reaches the trust plane | retry per econ backoff | lane health only | REFUNDED to the approach |
| apparatus (phase-B grader crash, bad case set, sandbox infra, panel quorum failure) | `invalid`, `attribution: apparatus`, `failed_phase: A\|B` | `maintenance` purpose (judge spend rides `verification`) | apparatus alarms | counts nobody's visit |

`failed_phase` distinguishes exec-infrastructure apparatus (A: sandbox failed to start — Substrate
Preflight alarm) from grading apparatus (B: grader/case-set/panel — roster or library repair).
Absent-reading: `failed_phase` absent = `null` (pre-v5 receipt).

**Spend-side pin (joint row with seats 04 + 07, #683/#679/#695):** apparatus-INVALID spend
COMMITS to the run's purpose ledger (the money was spent; the cap is real) but is NEVER charged to
`arm.usd_spent` for the dollar-UCB index — it folds to a run-level `apparatus_usd`, surfaced in
the certificate residual with `waste_flag: apparatus_invalid`.

### 2.3 Differential re-attribution (NEW in v5 — closes the last evasion channel)
Phase B never loads candidate code, but it parses candidate-*authored* content (the behavior
artifact). A well-formed-but-adversarial artifact that crashes the grader would be misattributed
apparatus — a free evasion. Therefore:
1. On phase-B failure grading candidate `c`'s artifact, the runner retries per `grade.retries`.
2. If retries exhaust AND ≥1 other candidate's artifact graded clean under the same
   `(oracle, gen, check)` in the same round, attribution flips to `candidate`: receipt `gate`,
   score 0, `attribution: candidate`, `failed_phase: B`, reason `grader-failure-selective`.
3. If no clean sibling exists because the grader fails on ALL artifacts in a multi-candidate
   round, attribution stays `apparatus` and §2.4's quarantine may fire.
4. **Single-arm topologies (s6-14).** For topologies dispatching one candidate per round
   (tournament×ucb, mcts, pipeline — run.md §R3) the clean-sibling premise structurally cannot
   hold, so the runner MUST synthesize the differential in the same round: re-grade the
   grader-crashing artifact against a SECOND independent grader instance, OR run the same grader
   against a golden known-good artifact (§7) as the sibling. A selective crash that survives the
   second grader (the golden grades clean; only this artifact crashes) is candidate-attributed:
   receipt `gate`, score 0, `attribution: candidate`, `failed_phase: B`, reason
   `grader-failure-selective`. Where neither instrument is available, attribution stays
   `apparatus` AND the certificate MUST carry the flag
   `differential re-attribution unavailable (single-arm topology)` — a named §1.4 residual, so
   the open evasion channel is visible, never silent. Falsifier: SINGLE-ARM-ATTR.

**Substrate precondition (seat 09, #686 — MUST):** differential re-attribution is sound only over
**per-candidate sealed artifacts**: each candidate writes to its own `/out` (never shared), the
trusted runner seals it at candidate exit into a content-addressed artifact (manifest + sha256 per
file, size-quota, schema-check at handoff), and phase B reads the STORE — never a sandbox volume.
Without per-candidate isolation an adversarial artifact can contaminate round-mates and
re-attribution degrades to a heuristic.

### 2.4 Exit tri-state + anti-evasion economics
- Tri-state per check: `passed | gate | invalid`. Gates dominate scores (`gates-lexicographic`,
  §3): no score can buy back a fired gate.
- A required check INVALID after retries ⇒ the whole StackReceipt is `invalid`.
- Apparatus INVALID counts nobody's bandit visit and is paid by `maintenance` (v3 adjudication #10
  kept). **Availability quarantine (restored, narrowed):** ≥2 consecutive apparatus-INVALIDs on one
  arm pause that arm (no score effect, no visit effect) pending reconciliation + a §2.3 check; the
  pause lifts when a grading completes clean. The quarantine's own firing rate is an apparatus
  health metric (`hc top`). Under TP-1 it SHOULD fire ~never; if it fires often, the apparatus is
  sick, not the arm.
- **Run-level INVALID-rate halt (restored from v2):** a run whose INVALID rate (invalid receipts /
  all receipts, folded by the run engine) exceeds its pre-registered `R%` (run-manifest field,
  default 25%) halts `oracle-sick` rather than converge on the minority that graded.

### 2.5 The `score-stdout-v1` shim (deprecated)
v1-style oracles run under the shim runner: candidate execution still splits per TP-1 (the shim
wraps the candidate in phase A), the legacy grader keeps the last-match `SCORE=` rule and exit-code
mapping. Where the oracle cannot be split, receipts are marked `attribution: coarse` and the run
cannot claim HC-7 closure. New oracles MUST use `report-file-v5`.

## §3 · The oracle STACK (`library://<task_class>/stack.yaml`; the manifest carries `oracle.ref` ONLY — ref-only, R18)

"The oracle" is never one command: it is a stack of **named checks** with a pre-registered
aggregate, a null policy per check, and per-case FAIL detail. Frozen at run open.

```yaml
oracle:
  id: ipv4_check                      # stable name within task_class
  task_class: code.func.validation    # L1 library key (§8.3)
  protocol: report-file-v5            # report-file-v5 | score-stdout-v1 (deprecated shim)
  gen: auto                           # auto = library head at run open; or pinned int.
                                      # digest is NEVER authored: runner resolves gen->digest from
                                      # the registry; hand-pinned digest mismatch = apparatus INVALID.
  checks:
    - name: unit                      # ── KIND unit: executable ground truth ──
      kind: unit
      required: true                  # required: INVALID after retries invalidates the receipt
      weight: 1.0
      exec:                           # PHASE A (TP-1)
        driver: harness.func          # harness.func | harness.cli | harness.none
                                      #   harness.none: prose/artifact tasks — the declared
                                      #   artifact IS the behavior; no execution
        entry: "is_valid"
        sandbox: class-3              # §2.1; isolation_actual stamped on every receipt
        limits: { wall_ms: 2000, cpu_ms: 1000, mem_mb: 256 }   # per case
        limits_total: { wall_ms: 60000 }                        # whole phase A
      grade:                          # PHASE B (TP-2)
        cmd: "python oracles/ipv4_grade.py"
        timeout_ms: 30000
        retries: 2                    # then §2.3 differential re-attribution, then INVALID
      cases: "library://code.func.validation/ipv4_check@gen"
      on_null: invalid                # no resolvable case set = apparatus

    - name: grounding                 # ── KIND grounding: the evidence gate (A11) ──
      kind: grounding
      required: true                  # present iff run grounding mode != none
      gate: true                      # gates contribute pass|gate, never a score
      config:
        mode: sampled                 # none | sampled | required (v2 dial; 'grounded mode' below
                                      #   means sampled or required). none: check absent.
        input: evidence-bundle        # membrane-packaged at submission: cited memories + terminal
                                      #   ref-closure content-hashes; packager refuses
                                      #   register=narrative (cite-block is cell-side, pre-oracle)
        digest_check: all             # every evidence ref sha256 re-verified (act-plane primitive)
        witness_check: all            # every act:// ref must exist in poster's receipt history
        entailment_sample: 0.2        # fraction of (claim, ref) pairs sampled
        entailment_by: cross-family-judge   # single entailment miss gates only when digest/witness
                                            #   corroborates; else flagged for panel
        source_diversity: 1           # >=n independent domains per load-bearing claim; the
                                      #   CERTIFICATE reports domains-per-material-claim either way
        trust_floor: null             # optional: minimum ingress trust tag (seat-10 taxonomy) for
                                      #   a terminal to count toward source_diversity; terminals
                                      #   below floor are REPORTED, never silently gating
      on_null: gate                   # grounded mode + empty evidence[] = unwarranted
                                      # honest `ungrounded: true` => score cap, not gate (v2 §4)

    - name: panel                     # ── KIND panel: cross-family judges (§6) ──
      kind: panel
      required: true                  # judged classes; absent for pure-executable classes
      weight: 1.0
      tier: { screen: 1, promotion: auto }    # §14: auto = break-even K*
      roster:
        families_min: 3               # distinct weights families (hard floor 2)
        quorum: 3                     # counted judges surviving recusal, PER producer family
        judge_depth: d0
        source: pricebook             # weights_family column — a TRUST input (§15 SEC-2)
        k_max: 7
      blinding: { strip_metadata: true, order: per-judge-random, pairwise: both-ways }
      controls: { golden: 1, flaw: 1, source: "library://<task_class>/controls" }
      abstain_floor: 0.3              # §6 step 7; fabrication := 0.0 < floor by construction.
                                      #   THE pre-registered constant's ONE home (R20; v2's
                                      #   value) — act.md §9 cites it, never restates
      aggregate: trimmed-median
      dissent_bound: 0.25             # FAMILY-level dissent above this => contested
      verbosity_guard:                # RESTORED from v2 §5 (one of the five 2026 judge biases)
        min_gradings: 20              # correlation computed once >= this many counted gradings
        r_flag: 0.4                   # |spearman(score, candidate_tokens)| above this flags
                                      #   panel-health; flag NEVER auto-adjusts scores (an
                                      #   auto-length-penalty is a new Goodhart surface)
      on_null: invalid                # judged class with no constructible panel = apparatus
                                      #   (see §6 step 3 for the diversity-debt exception)

    - name: probe                     # ── KIND probe: the Divergence Meter feed (§11) ──
      kind: probe
      scoring: none                   # NEVER contributes to score/outcome; results NEVER reach
                                      #   producers (zero Goodhart surface, adjudication #382)
      corpus: "library://<task_class>/probes"
      budget: { max_inputs: 128, max_pairs: 32 }
      on_null: skip                   # advisory; missing corpus degrades honestly (residual)

  aggregate:
    score: weighted-mean              # over scoring checks, post-gate
    outcome: gates-lexicographic      # ANY fired gate => gate, regardless of score
    invalid: required-after-retries
    fabrication_score: 0.0

  convergence:                        # trust-side predicate the run engine consumes (§5.3).
                                      # KNOB HOMES (R18): the stack owns exactly these five —
                                      #   {target, tolerance, divergence_eps, contested_cap,
                                      #   contested_blocks_champion} — and ONLY those. `stable_k`
                                      #   is a MANIFEST knob (run.md termination{}): counted by
                                      #   the run engine as consecutive GRADING EVENTS with no
                                      #   champion improvement UNDER ONE oracle gen; gen bump
                                      #   resets (stability is a (champion, bar) property).
    target: 1.0
    tolerance: 0.0
    divergence_eps: 0.02
    contested_blocks_champion: true
    contested_cap: 2                  # regrade attempts before verified-with-residual close (§5.3)
                                      # [R25] `null_arm` is NOT a stack knob and does not appear here.
                                      #   The null policy — including whether an arm is REQUIRED — lives
                                      #   entirely in the manifest's `null:` block (grammar §12.1 below,
                                      #   which run.md copies verbatim). The stack owns exactly five
                                      #   knobs: target, tolerance, divergence_eps,
                                      #   contested_blocks_champion, contested_cap. One knob, one home —
                                      #   the same R18 discipline that collapsed abstain_floor.

  growth:                             # A12 pre-registration, frozen at run open
    enabled: true
    granularity: round                # round (answer runs) | epoch (Crucible P5) — v2 §5 law
    budget_frac_max: 0.20
    max_cases_per_gen: 16
    p_holdout: 0.20
    admission: candidate-blind        # §9 G1 — constitutionally load-bearing
    adjudication_quorum: 3
```

Field semantics: `required`, `on_null ∈ {skip, gate, invalid}` (exactly three; a check missing
`on_null` is a schema error), `gates-lexicographic` (encodes live `topology.py:184`'s
outcome-authoritative rule at check level), `harness.none` (prose rides the same contract —
repeals v1's `oracle.mode: judge-panel` fork; §M).

## §4 · Phase artifacts (normative)

### 4.1 The behavior artifact — `_sandbox/<run>/r<round>/<cell>/behavior.jsonl`
```jsonc
{ "case": "c-01942",                  // case_id or probe_id
  "input_digest": "sha256:…",
  "output": "true",                   // canonicalized (task-class canon(), §11.2)
  "raw_ref": "artifact://…",          // bounded pointer to raw output
  "status": "ok | error | timeout | killed",   // per-case, candidate-attributable
  "wall_ms": 12 }
// trailer:
{ "trailer": true, "cases_run": 142, "cases_killed": 2,
  "sandbox": { "class": 3, "degraded": false },     // isolation_actual (HC-7 log query)
  "candidate_digest": "sha256:…" }
```
The sandbox receives inputs only. `status != ok` = candidate miss on that case; a killed run marks
all un-run cases missed. Artifacts are cached keyed `(candidate_digest, input_digest)` — one
artifact serves grading, divergence (§11), admission probing (§9), and regrades (§9.4): **the
behavior-artifact economy**, the claim that makes growth affordable at fan-out scale.

### 4.2 The report file — written by phase B at `--report <path>` (the ONLY grading channel)
```jsonc
{ "oracle": "ipv4_check", "gen": 3, "digest": "sha256:…",
  "check": "unit",
  "outcome": "passed | gate | invalid",
  "score": 0.9286,
  "cases": [                          // PER-CASE FAIL DETAIL — reported cases ONLY
    { "case": "c-00007", "ok": false, "class": "nonascii-digit",
      "expected_digest": "sha256:…", "got_digest": "sha256:…",
      "msg": "is_valid('1.1.1.٤') -> True, want False" } ],   // msg <= 200 chars
  "holdout": { "n": 3, "passed": 2 },                 // AGGREGATE ONLY, never per-case
  "provisional": [ { "case": "c-019", "ok": true } ], // §8.2 operator-provisional cases: graded,
                                                      //   listed separately, EXCLUDED from score
                                                      //   and failure_signature until confirmed
  "failure_signature": "sha256(sorted reported failed case ids)",
  "error": null }
```
This field list is FROZEN for the substrate channel table (seat 09, #695): nothing else crosses
the report seam.

**The three leak constraints on failure-set consumers (prune, cross-pollination, growth targeting;
settled adjudication #382):** (a) domination is computed over *reported* cases only — recomputing
from raw rows is a contract violation; (b) because `score` is holdout-inclusive while signatures
are reported-only, domination REQUIRES both clauses:
`failures_reported(c2) ⊊ failures_reported(c1) ∧ score(c2) ≥ score(c1)`;
(c) failure sets are gen-scoped — cross-gen superset tests are category errors; a gen bump
un-prunes all; recomputation under the new gen is phase-B-only over cached artifacts.

**Report-artifact ACL (explicit, seat 04's ask #683):** `report_ref` artifacts are
**conductor-access-only**. Cross-pollination packets built by the run engine may carry REPORTED
per-case rows only; holdout rows do not exist in reports; probe-corpus results NEVER leave the
meter (§11.1). A packet builder reading raw behavior artifacts or probe results is a contract
violation.

## §5 · StackReceipt · verdict · certificate (the oracle↔run seam)

**Posting law:** every StackReceipt MUST be posted to the Medium (conductor-only per type-ACL,
D-gold). The live engine keeps receipts in-process (zero receipt rows in today's log — E2);
certificate-as-fold is fiction until this lands (build slice TP-1). **Reader clause:** a receipt
without `oracle.gen` reads as `g0`, forever; a receipt without `failed_phase` reads `null`; a
receipt without `vs_null` predates the null contract (§12) and is excluded from null-ledger folds.

### 5.1 StackReceipt (conductor-posted `receipt` payload; non-mintable — §15 SEC-3)
```jsonc
{ "submission_seq": 481,
  "oracle": { "id": "ipv4_check", "gen": 3, "digest": "sha256:…" },
  "outcome": "passed | gate | invalid",
  "attribution": "candidate | apparatus | null",     // null on passed
  "failed_phase": "A | B | null",                    // §2.2; null on passed
  "contested": false,                                // OR over checks
  "score": 0.9286,
  "checks": [
    { "name": "unit", "kind": "unit", "outcome": "gate", "score": 0.9286,
      "failure_signature": "sha256:…", "report_ref": "artifact://…" },
    { "name": "grounding", "kind": "grounding", "outcome": "passed", "gate": true,
      "evidence": { "resolved": 14, "digest_ok": 14, "witness_ok": 14,
                    "entailment": { "sampled": 3, "passed": 3 },
                    "coverage": 0.93, "citation_precision_at_k": 0.95,
                    "domains_per_claim": { "min": 1, "median": 2 },
                    "trust_floor_met": true } },
      // ^ row shape PINNED with seat 06 (#695): act-plane primitives fill evidence{},
      //   this contract owns gate semantics over it; 04's certificate reads one shape
    { "name": "panel", "kind": "panel", "outcome": "passed", "score": 0.83,
      "tier": "screen | promotion",
      "scores": [8.5, 8.0, 9.0, 4.5, 8.0],           // raw, counted judges, post-blind order
      "families": ["qwen", "glm", "kimi", "qwen", "deepseek"],
      "recused":  [ { "lane": "deepseek@ds", "raw": 9.5 } ],
      "abstained": [], "probation": [],
      "controls": { "golden": 8.7, "flaw": 3.1, "per_judge_pass": [true,true,true,false,true] },
      "dissent": 0.11,                               // FAMILY-level (§6 step 8)
      "verbosity_r": 0.08,                           // §6 step 9; null until min_gradings
      "contested": false, "degraded": false },
    { "name": "probe", "kind": "probe", "outcome": "passed", "scoring": "none",
      "divergence_contrib_ref": "artifact://…" } ],
  "graded_by": "conductor",
  "cost": { "usd_effective": 0.0041, "usd_reserved": 0.0050, "sku": "deepseek-chat@ds/std",
            "purpose": "verification", "resv_id": "rsv_01H…", "pricebook_version": "pb-2026-07-16" },
            // `verification` — judge/grader spend rides the verification purse (§2.2). "grading" is
            // NOT a legal purpose; the closed set is {production, verification, oracle_growth,
            // tool, maintenance} and pricebook.md owns it.
            // the canonical crossing-record field-group (R2/R16; pricebook.md owns member
            // semantics); per-arm attribution source for vs_null matched-invoice folds (R11)
  "wall_ms": 2210,                                    // measurement — a SIBLING of cost{}, not a
                                                      // member (R16: cost{} carries dollar
                                                      // attribution only)
  "evidence_ref": "artifact://…" }
```
Per-case detail NEVER rides the Medium receipt — it lives in the report artifact behind
`checks[].report_ref`, under §4.2's leak constraints (confirmed with seat 04, #678).

### 5.2 Verdict additions (run engine assembles; trust plane defines the fields)
```jsonc
{ "kind": "verified | verified-with-residual | synthesis",
                                                      // wire.md §3.1 owns the wire discriminator
                                                      //   `kind` (R21); same enum, same spelling
  "oracle_gen": { "id": "ipv4_check", "gen": 3, "digest": "sha256:…" },
  "champion": { "arm": "a3 | null-arm", "score": 0.97, "receipt_seq": 512 },
  "vs_null": {                                        // §12.3 dual-unit accounting; canonical
                                                      //   members (R15) = {null_score, null_usd,
                                                      //   margin_production, margin_invoice}
    "null_score": 0.86,
    "null_usd": 0.029,                                // ONE member — a production/invoice split
                                                      //   of the null's spend is render-side
                                                      //   detail, never the wire join key
    "margin_production": +0.11,
    "margin_invoice": +0.06,                          // the operator's unit; the flip keys here
    "null_mode": "inline | sampled | audited-estimate",
    "null_pin": { "family": "deepseek", "provenance": "operator-pin | ranking-artifact",
                  "ref": "artifact://rankings/…#sha256=…",   // §12.1 is the grammar HOME [R17];
                                                            // `medium://` is NOT a legal null ref
                  "as_of": "2026-07-01" } },
  "residual": {
    "divergence": 0.017,
    "contested_cases": [],
    "unprobed": ["ipv6-mapped", "whitespace"],
    "panel_dissent_by_family": { "qwen-glm": 0.11 },
    "grounding": { "domains_per_material_claim_min": 1, "trust_floor_met": true },
    "degraded": [] },                                 // named degradations (§1.4)
  "regrades": [ { "gen": 3, "survivors": 5, "usd": 0.006 } ],
  "invalid_rate": 0.04 }                              // folded by run engine; §2.4 halt input
```

### 5.3 The trust-side convergence predicate — the ONE home (nothing else may declare convergence)

**EIGHT clauses** — the honest count (never "five"; every clause is load-bearing). This section is
the predicate's ONLY definition: no other contract, walkthrough, or fold may declare convergence.
The predicate is exposed to the run engine as **`oracle.converged(R, run)`**; run.md §R2.1 binds
`converged() := oracle.converged(R, run)` and owns only the fold plumbing that feeds it; ARCH
L-RUN-2 and §12 cite this section.

```
oracle.converged(R, run) :=     # R = the champion's StackReceipt (non-mintable, conductor-posted)
  (i)    R.outcome == passed                          # on the NON-MINTABLE receipt —
                                                      #   outcome-authoritative (live rule kept)
  (ii)   R.score >= target - tolerance
  (iii)  stable_for(stable_k)                         # run-engine counter over the MANIFEST's
                                                      #   termination.stable_k (run.md; R18);
                                                      #   VALID scoring events only (F24 fix);
                                                      #   gen bump resets
  (iv)   D(passers, probe_corpus) <= divergence_eps   # §11 D1; growth may fire instead
  (v)    not any(check.degraded for check in R.checks)  # OR degradation named in residual + type
                                                         #   demoted per the degradation's law
  (vi)   not R.contested                              # champion uncontested-or-at-cap: OR
                                                      #   contested_cap regrades exhausted =>
                                                      #   close verified-with-residual, dissent
                                                      #   verbatim in the certificate (v2 law)
  (vii)  run.invalid_rate <= R%                       # else halt oracle-sick, never converge
  (viii) null_recorded(run)                           # §12; per the run's registered null mode,
                                                      #   its reservation honored — an unrun
                                                      #   required null can never close as a
                                                      #   deliverable champion (run.md §R7.1)
```

### 5.4 Certificate trust fields (the one recomputable-from-the-log sentence)
*"Under oracle generation Gₙ (digest, lineage), champion c (arm a) scored s ≥ t, stable for k
gradings; residual behavioral divergence ≤ ε on spec-covered probes; m ambiguous inputs escalated
(listed); panel dissent σ across families {…}; verbosity-r v; citation precision p@k across d
domains (trust floor: met/not-required); beat / lost-to the matched-dollar single-cell null by δ at
matched-invoice (δ′ at matched-production); INVALID rate i ≤ R%; operator imports in this class:
confirmed / provisional (rate r vs ceiling c); spend $x production + $y verification + $z growth."*
Every clause folds from Medium records; the certificate is a render, never a source.

### 5.5 The `oracle_gen.kind` registry — the ONE registry (wire.md §3.1 delegates here)

This contract owns the `oracle_gen` kind registry. wire.md §3.1's `oracle_gen` block carries
`kind: see contracts/oracle.md §5.5` — a delegation, never a copy. All kinds are conductor-minted
(SEC-3), D-gold, R-forever. Unknown kinds are preserved, never dropped (header liberality); an
emit-strict emitter MUST mint only from this table.

| kind | minted at | carries |
|---|---|---|
| `gen_open` | §9.4 generation open | `{gen, digest, minted[], errata[]}` |
| `sealed_report` | §10 epoch sealed-run close | `{epoch, aggregate, n, commitment_ok}` |
| `spec_bug` | §9 AMBIGUOUS adjudication | the spec hole, verbatim dissent |
| `judge_ejected` | §6 step 6 lifecycle | `{lane, family, control_record}` |
| `crucible_halt` | §10 halt rule fires | halt evidence; champion_head pointer move |
| `diversity_alarm` | §11.3 D2 tripwire | quarantined round, D trend |
| `errata` | §8.2 signed correction applied | `{case, action, reason}` + Stage-1b signature |
| `operator_audit` | §13.1 blind second adjudication | the audit row (§13.1 shape) |

## §6 · THE JUDGE ALGORITHM (one numbered algorithm; each step names its law)

Inputs: blind packet set (candidates + §7 controls), producer families F_p, pricebook P, tier
(screen|promotion), task-class controls/history. Output: per-candidate panel-check verdicts.

```
JUDGE-PIPELINE(candidates C, F_p, P, tier, class):
 1. ROSTER (quorum-after-recusal solved at BUILD time):
    eligible := judge-capable lanes in P grouped by weights_family
    fams := distinct families in eligible
    if |fams| < max(2, families_min):
       if run.diversity_debt declared: build what exists; panel degraded:=true (≡ contested;
          may rank, never seat a verified champion; recusal SUSPENDS — step 4 — because the
          cross-family guarantee is already forfeited and stamped; the debt demotion to
          synthesis-grade governs)                     [v2 §5 restored]
       else: panel INVALID (apparatus: honest cross-family panel unconstructible)
    order fams: ∉F_p first, then ascending cost (PoLL default: small models, many families);
    round-robin seats until K filled (screen: K=1 rotating family ≠ candidate family;
    promotion: K = K* families per §14); REPAIR: for each f in F_p, while
    |{j : family(j)≠f}| < quorum and K < k_max: add cheapest judge ∉ f.
    INVARIANT (the roster theorem): for every producer family, ≥ quorum counted judges
    survive recusal. Judges are d0 reflex cells, temp 0, distinct seeds, no nucleus
    carry-over between panel rounds; rubric angles from the registered set (v1's five carried).
 2. CONTROLS: seed 1 golden + 1 flaw from library://class/controls (§7), rotated without
    replacement within the run; young class with no controls: mark controls:absent —
    un-controlled panels cannot eject judges nor certify promotion where controls exist
    elsewhere in the class.
 3. BLIND: packet = {goal, spec_excerpt, candidate_text, evidence_digest_list}; strip cell
    names, providers, rounds, scores; randomize candidate order per judge.
 4. SCORE: each judge emits exactly `SCORE: <0-10>` or `ABSTAIN: <reason>` (one line, strict
    parse; no-parse = abstain-by-failure). RECUSAL: the runner (never the judge — disclosure
    would break blinding) marks same-family scores recused: logged advisory, excluded from
    counted. Under declared diversity_debt recusal is SUSPENDED (step 1).
 5. PAIRWISE (promotion ties only, |Δscore| < tie_eps): each pair judged BOTH WAYS by every
    counted judge; a judge whose verdict flips with order is position-sensitive on that pair —
    its pair verdict discarded (0.5/0.5). Flip rate > 0.3 flags the rubric, not the candidates.
 6. LIFECYCLE (per-lane control record; deterministic/adjudicated controls only — never
    contradiction.inject):
    counted --(1 control failure: score(flaw) ≥ score(golden) − δ, δ=1.0)--> probation
      (still graded on every packet — it must not be able to tell; excluded from aggregates)
    probation --(2 consecutive control passes)--> counted
    probation --(2nd failure within W=5 panel rounds)--> ejected for the run;
      roster refills maintaining step-1 invariant; post oracle_gen{kind: judge_ejected,
      lane, family, control_record} (R-forever). EJECTION IS PROVISIONAL (a suspension:
      excluded from aggregates, still graded) while ANY golden used in the run is
      unaudited (§7 mint-audit, s6-11); a §13.3 recall-drill reversal of the golden
      RESTORES wrongly-suspended judges.
 7. ABSTAIN FLOOR: candidate-declared `abstain{reason}` short-circuits: outcome gate, score =
    abstain_floor exactly (default 0.3), panel skipped. A fabrication gate (digest mismatch /
    non-witnessed ref / non-entailing quote) forces score = 0.0 < floor BY CONSTRUCTION:
    good > honest-abstain > confident-wrong, enforced arithmetically outside any judge.
    JUDGE abstention: not counted, not a control failure; >50% of a panel abstaining on one
    candidate ⇒ panel INVALID for that candidate (apparatus), re-rostered once, then INVALID.
 8. AGGREGATE (trimmed median + FAMILY dissent):
    counted := scores − recused − abstained − probation − ejected
    if |counted| < quorum: expand (≤2 repairs) else check INVALID `oracle-sick`
      (the <2-counted INVALID floor binds only non-debt runs — step 1)   [v2 §5 restored]
    n ≥ 5: drop one min + one max, median of rest; 3 ≤ n ≤ 4: plain median; score := median/10
    fam_score(f) := median of counted scores from family f
    dissent := max over family pairs |fam_score(f1) − fam_score(f2)| / 10
    contested := dissent > dissent_bound; |families among counted| == 1 ⇒ contested BY FIAT
    (two same-family judges agreeing is ONE voice — F1/F9; judge-level IQR stays in the
    receipt as evidence, the flag keys on the family gap).
 9. VERBOSITY GUARD (restored; MUST measure, SHOULD act, MUST NOT auto-adjust):
    once ≥ min_gradings counted gradings in the run: verbosity_r := spearman(counted score,
    candidate token count); |r| > r_flag ⇒ post panel-health flag to hc top + certificate;
    action is rubric review / operator attention — never a score adjustment (an automatic
    length penalty is a new Goodhart surface pointed at the guard itself).
10. HALTS: check INVALID per steps 7-8 feeds §2.4's run-level R% halt; ejections feed §14's
    ê estimator (Wilson upper bound on control-failure rate).
```

Failure modes: all-families-overlap-producers (solo-operator worst case) → degraded ≡ contested,
run completes as ranked synthesis, never a verified champion; probe starvation in a young class →
controls:absent path; rubric-angle collapse → pairwise flip rate + dissent trend in `hc top`.
**Falsifier: JUDGE-1** (incl. the two lived P2 bugs: the always-pass aggregate `judge.py:72` —
outcome derives from score-vs-target, never unconditional; the thin-quorum leak `judge.py:63-70` —
<2 counted ⇒ INVALID `oracle-sick`).

## §7 · Control probes (TP-3) — minting by the next-more-trusted tier

**LAW TP-3.** A control probe is admissible ONLY if its label (golden, or flaw-with-known-defect)
is verified by a mechanism strictly more trusted than the panel it will calibrate: an executable
battery, a deterministic evidence check, or a disjoint-authority adjudication. Controls labeled by
unverified belief are theater and are forbidden.

**Golden admissibility (the champion→control disjointness rule — v2 restored, closing v3's
circularity):**

| golden source | admissible when | authority |
|---|---|---|
| executable-verified champion | promotion receipt shows the unit battery passed at its gen | the battery (deterministic) |
| operator exemplar | registered via `hc oracle control add --golden` **AND audited at MINT: admissible only after one disjoint re-adjudication** (§13.1's blind-second-authority machinery, applied at rate 1.0 to golden registration) | the re-adjudication (operator priced, §13; the §13.3 recall drill still re-samples goldens each epoch) |
| **panel-certified champion** | **ONLY after one disjoint re-adjudication** (§9 G3 machinery: families ∉ the certifying panel's families, or executable, or operator) | the re-adjudication |

A panel-certified champion admitted as a golden without re-adjudication calibrates the panel
against the panel's own past judgment — forbidden. **Operator exemplars obey the same law
(s6-11):** a golden is the least-audited operator import with the highest blast radius (a poisoned
golden ejects honest judges run-wide — F9-by-operator), so golden REGISTRATION comes under the
§13.1 mint-time blind-second-authority audit, and while ANY golden used in a run is unaudited,
judge EJECTION on its controls is PROVISIONAL — a suspension, not an ejection (§6 step 6): a
§13.3 recall-drill reversal restores wrongly-suspended judges.

**Flaw = golden × registered mutation** (injector cells are standing maintenance roles, NEVER
rostered as producers in any run whose panels use their probes — OG-4):

| flaw class | verifying mechanism (non-panel) | strength |
|---|---|---|
| mutation.code (boundary flip, off-by-one, negation, deleted guard) | unit battery: flaw fails ≥1 case the golden passes | deterministic |
| citation.corrupt (perturb cited number/entity, keep the citation) | grounding primitives: entailment/digest fires on the corrupted claim | deterministic-ish |
| requirement.drop (delete one enumerated sub-goal's answer) | coverage check vs the goal's requirement list | deterministic |
| contradiction.inject (assert X early, ¬X late) | NLI/consistency (model-assisted) | weak — screen-tier only, NEVER ejection-grade |
| oracle-caught.real (archived candidate the unit oracle gated) | the gate receipt itself | deterministic; free; accumulates from run one |
| adjudicated.real (candidate the Crucible's disjoint authority REJECTED) | the adjudication receipt | strongest for panel-class flaws; accumulates |

Pipeline: mint → verify discriminativeness (the TP-3 gate, table above) → **style screen** (a d0
classifier shown the probe among 3 real archived candidates must not spot it above chance+margin;
injectors generate under the producers' own base_prompt register) → register to
`controls/probes.jsonl` with provenance + verification receipt + usage counters (overexposed probes
retire per class). Budget: 2 probes per panel round = 2 extra gradings.

**The honest residual, named:** deterministic controls verify judges on the *verifiable subset* of
flaw space; quality on panel-only flaws is extrapolated — and the residual shrinks structurally:
every Crucible adjudication mints an `adjudicated.real` control, which IS a panel-class flaw with a
disjoint-authority label. The calibration layer obeys the conservation law itself.

## §8 · The oracle library — the compounding asset (and the two renders)

### 8.1 On-disk layout (per task class)
```
<home>/oracle_library/<task_class>/
  registry.json          # RENDER (§8.4): current gen, lineage, commitments, champion_head
  stack.yaml             # default stack for the class
  gen-0000/ …            # generations are DIRECTORIES, append-only
    manifest.json        #  {gen, opened_at, opened_by_run, digest, case_count,
    cases.jsonl          #   minted:[case_ids], errata_applied:[…]}  + Stage-1b signature (§15)
    errata.jsonl         #  operator-SIGNED corrections {case, action: retire|relabel, reason, ts}
  holdout/assignments.jsonl     # {case_id, gen_assigned, coin_receipt}
  sealed/commitment.json        # {sha256, n, committed_at, sig}  — BYTES LIVE OFF-FABRIC (§10)
  sealed/reports.jsonl          # {epoch, aggregate, n, commitment_ok, ts} — one scalar/epoch
  champions/<run_id>.json       # {artifact_ref#sha256, receipt_ref, gen, score, dissent,
                                #  certification: executable|panel|operator}  ← asset render root
  controls/probes.jsonl         # §7
  probes/corpus.jsonl           # §11.1 — divergence inputs (unscored)
  admission/<obs_id>.jsonl      # case-admission journal, one row per transition (§9)
```

### 8.2 The case row (with the v5 status vocabulary)
```jsonc
{ "case": "c-014", "input": "1.1.1.٤", "input_digest": "sha256:…",
  "expected": "false", "class": "nonascii-digit",
  "authority": { "kind": "executable | panel-disjoint | operator",
                 "ref": "medium://…", "families": ["qwen","glm"] },
  "minted_from": { "run": "r19", "obs": "obs-01J…", "producers": ["deepseek"] },
  "status": "active | provisional | holdout | errata-retired",
  //         provisional (NEW): operator-minted while the class's published operator-
  //         disagreement rate exceeds its ceiling (§13.4) — graded and reported but
  //         EXCLUDED from score, failure_signature, and prune until confirmed; the
  //         report file lists provisional case results separately.
  "added_gen": 3 }
```
Generations are append-only; a wrong case exits only via signed errata + a regrade round. The gen
digest = sha256 over sorted active-case digests; every receipt cites `oracle_id@gen#digest` — a
mismatch against the registry is tamper-evidence.

### 8.3 Task-class identity — the backoff hierarchy (FIX-3, finalized with seat 04)
- **L0 — exact signature** `(oracle-template digest, toolset, topology family, goal schema-sig)`:
  **champion/artifact reuse keys here only** (an artifact is trusted only where its exact bar applies).
- **L1 — template family** (template id + toolset + topology; digests dropped): **the oracle
  library keys here** — generations, controls, probes, admission all accumulate at L1.
- **L2 — (verification-axis × information-axis)** global prior: **the null ledger and
  refuse-to-swarm defaults read the deepest level holding ≥ m audited samples**, backing off
  L0→L1→L2 (m per §12.4's flip predicate).
Task classes are minted at first use (intake names or a d0 classifier *proposes*; ambiguity is a
one-line operator ask — Entry-30; never silent merge). Classes are append-only; re-classing is
operator errata; receipts keep their original class stamp.

**Template registration + match (b3-01):** oracle templates are an **operator-registered
pinned-artifact set** — the registration home; `registry.json` carries the render. Each
registration carries a match predicate `template.match: {class_hints_any: [...], goal_regex: ...}`,
evaluated DETERMINISTICALLY at intake; on multi-match, **first-by-registration-order wins** (no
scoring, no tie-break heuristics); the run's provenance quotes the matched template id. run.md
§R6.1's "a registered oracle-template matches" consumes exactly this predicate.

### 8.4 THE RULING — one tree, two renders, two keys (resolves v3 coordinator thesis 6)
The **oracle library** (bar side: gens, cases, controls, probes, admission — keyed L1) and the
**artifact library** (asset side: champions, syntheses, certificates — keyed L0 for reuse) are TWO
RENDERS over the SAME R-forever Medium records (`oracle_gen` kinds + receipts + verdicts), sharing
ONE on-disk tree. They are not two stores (no second source of truth) and not one render (they fold
different record subsets under different keys for different consumers: the bar render feeds
grading; the asset render feeds seeding/controls/context reuse). `registry.json` and
`champions/*.json` are both renders: delete them and you lose open-time speed, never truth —
`current_gen` folds over gen manifests; `champion_head` folds over champion + halt records
(rollback is an appended halt record that changes the fold's output, never an edit). Fold-law
conformance: DECLARED for both renders; compaction-closed input filters per L-FOLD-CLOSURE (seat 03).

### 8.5 Trust-plane service cells (authority bounds structural, not prompted)

| service cell | depth | authority | structural bound |
|---|---|---|---|
| admission clerk | d0 | advance/refuse OBSERVED→PROBED | sees spec + input ONLY; cannot mint, label, or see candidates |
| adjudicator panel | d0 | mints case labels | only via quorum + family disjointness; packet hides bodies, counts, champion |
| flaw injector | d0/d1 | proposes control flaws | unusable until verified one tier up (TP-3); never rostered as producer |
| prober | d0 | hint-only | probes score nothing; an un-adjudicated probe can trigger observation, never a score |
| claim extractor (prose) | d0 | advisory-only | feeds D-proxies; can never feed D1 minting |

## §9 · Case admission — the state machine (six states, guarded transitions)

```
OBSERVED ──G1──> PROBED ──G2──> CONTESTED ──G3──> ADJUDICATED ──┬──> MINTED
   │               │                                            ├──> AMBIGUOUS (spec_bug)
   └─(dedupe/      └─(flaky ⇒ REJECTED-flaky;                   └──> REJECTED (reason)
      out-of-spec)     input retained as probe)
```
- **OBSERVED:** input `x` splits oracle-*passing* candidates (source: §11 D1 argmax, or a cell's
  `oracle_gap` hint — DATA, never an admission shortcut). Journal `{x_digest, partition, d(x)}`.
- **G1 — spec-derivability, CANDIDATE-BLIND (constitutionally load-bearing):** a d0 clerk (family
  ∉ producer families) sees ONLY spec text + `x`: "is `x` inside the input domain the spec
  defines?" Never candidates, behaviors, or who-fails-what. A case admitted because the spec
  covers it is growth; a case admitted because champion X fails it is an attack. Plus dedupe.
- **PROBED / G2 — persistence:** re-run `x` across passers + null + prior champions, twice, seeds
  varied (phase-A only, cached). Both probes show ≥2 behavior classes, else REJECTED-flaky.
  Deterministic classes: a candidate itself flaky on `x` is gated (nondeterminism is a miss).
- **CONTESTED:** adjudication scheduled iff `oracle_growth` funds remain and `max_cases_per_gen`
  not exhausted (A12 caps).
- **G3 — ADJUDICATED (disjoint authority, strict order):** (1) executable authority if one exists;
  (2) disjoint panel — families ∉ ALL producer families, shown `{spec, x, anonymized behavior
  classes}`, NEVER bodies, NEVER class sizes, NEVER the champion's class (the no-majority-signal
  law: F1 proved the majority shares blind spots, so the majority signal must not exist in the
  packet); `ENTAILS: <class>` or `AMBIGUOUS: <reason>`; label iff ≥ adjudication_quorum agree
  (≥2 families, ≤1 dissent); (3) the operator (an H3-style parked question; priced per §13).
- **MINTED:** appended to gen n+1 staging with authority receipt; the holdout coin (registered
  p_holdout) assigns reported/holdout AT MINT; if operator-minted under an exceeded ceiling:
  `status: provisional` (§8.2).
- **AMBIGUOUS:** `oracle_gen{kind: spec_bug}` (R-forever) — the swarm's disagreement found a hole
  in the operator's own spec (attacks MAST's specification-failure class at the root); operator
  spec-errata re-enters at CONTESTED.
- **REJECTED:** reason journaled; the input STAYS in the probe corpus (rejection kills the case,
  not the probe).
Every transition appends `{obs_id, from, to, guard, receipt_ref, ts}`; HC-V1 asserts journal
completeness. **Adjudication reserve (v2):** a convergent judged run MUST declare one weights
family held out of the producer roster, or declare operator-only adjudication at open and cap
mints accordingly.

### 9.4 Regrade rounds (granularity law; near-free by construction)
Answer runs grow at ROUND boundaries; the Crucible (P5) at EPOCH boundaries. On gen open:
(1) conductor posts `oracle_gen{kind: gen_open, gen: n+1, digest, minted, errata}` then
`round_open{round, oracle_gen: n+1}`; (2) survivors (Pareto set + champion) regraded
**phase-B-only** over cached
behavior artifacts — no sandbox, no LLM, no production spend; (3) scores partition by gen (frozen
history); champion recomputed under n+1; `verdict.regrades[]` records each pass.

**Gen-bump authority (s6-15; resolves the run.md §R2.1/§R8.2 conflict):** the ONE record whose
`oracle_gen` drives the fold's gen bump is the conductor **`oracle_gen{kind: gen_open}`** record —
never a `round_open` body. `round_open.oracle_gen` is a REFERENCE: a `round_open` whose
`oracle_gen` references no conductor `oracle_gen` record at-or-before its own seq is
**VOID-AT-FOLD**. The rule keys on record EXISTENCE — a fold input — never on a body parse, so the
post-ACL model (privilege per mint-principal, identity-firewall.md B.9/R14) holds. A self-clocked
`round_open` (wire.md §3 ACL) therefore can never force a gen bump, a champion/stability reset, or
a regrade round. Self-clock round FREQUENCY is bounded in the run manifest (a rounds-per-wallclock
/ rounds-per-grading cap; run.md owns the field), so round-churn cannot exhaust `max_rounds` into
a premature `verdict{exhausted}`.

## §10 · Holdout + the operator sealed set + halt/rollback

**Layer 1 — auto-holdout (cheap, continuous):** the registered coin sends ~p_holdout of new cases
+ a frozen gen-0 slice to holdout; graded every phase-B pass, contributes to `score`, reported
ONLY as `{n, passed}` — never per-case, never in failure_signature. Audits optimization against
reported FAIL detail; not independent of minting — hence layer 2.

**Layer 2 — the operator sealed set (independent by construction).** The law is about *records*,
not wires: sealed bytes are never PERSISTED on-fabric — no Medium post, no nucleus record, no
artifact write, ever. Sealed cases MUST carry operator-fixed expected verdicts (executable checks
or answer keys); a sealed case needing the current generation's panel to grade is inadmissible.
- **Storage:** operator curates OFF-fabric; `hc oracle seal --task-class X --file sealed.jsonl`
  writes ONLY `sealed/commitment.json {sha256, n, committed_at, sig}` (§15 SEC-1).
- **Execution (epoch boundaries), `sealed-run` mode:** verify sha256 vs commitment (mismatch ⇒
  refuse + alarm); phase A on fresh d0/d1 cells, no nucleus carry-over, `journaling: suppressed`
  (a role manifest requesting suppression outside sealed-run is REFUSED at spawn — anywhere else
  it is an audit hole); ephemeral class-3 on tmpfs; phase B in-memory; per-case results DISCARDED.
- **Reporting:** append `{epoch, aggregate, n, commitment_ok}` + post `oracle_gen{kind:
  sealed_report}` (R-forever). One scalar per epoch: the leak budget is ≤ log2(n+1) bits/epoch
  toward anything optimizing against it — bounded and slow by construction.

**Halt + champion rollback (pre-registered at G0 in `growth_policy.halt`; changing it mid-class is
forbidden — fork the class):**
```
AT EPOCH e CLOSE:
 1. archive_signal := score_g(e)(champion_e) − score_g(e)(champion_{e−1})
      # ONE gen, TWO champions — comparable by construction (cross-gen deltas are forbidden)
 2. sealed_delta := sealed_agg(e) − sealed_agg(e−1)   # sealed set frozen ⇒ comparable
 3. if archive_signal ≥ +A and sealed_delta ≤ −S:
      (small-sample rule: sealed n < 30 ⇒ require a second consecutive epoch)
      HALT: post oracle_gen{kind: crucible_halt} (R-forever);
      champion_head ← last champion whose epoch had sealed_delta ≥ 0 (a POINTER MOVE;
      nothing deleted); admission freezes at CONTESTED; oracle_growth budget freezes;
      operator surfaces show the halt.
 4. RESUME only by operator command (itself an R-forever record, signed).
```

## §11 · The Divergence Meter — one instrument, three duties

### 11.1 Probe corpus (per class; deterministic sources budget FIRST)
1. **Mutation of admitted cases** (registered input-mutation operators incl. encoding-class:
   digit→unicode-digit swap, casing, padding, truncation) — deterministic, free.
2. **Contested history** — every REJECTED/AMBIGUOUS admission input stays a probe: known to split
   behavior, the highest-yield instruments.
3. **Spec-derived boundary enumeration** — a d0 prober generates candidate inputs from spec text
   alone (the residual explorer: F1's ٤ lives outside the case set's neighborhood; kill the prober
   and that blind-spot class re-opens). Hint-only standing: a model-authored corpus mints nothing.
Corpus: default 128 active, refreshed at gen boundaries. **Probes never score** (`scoring: none`)
and **probe results never enter cross-pollination packets** (adjudication #382): pollination feeds
producers *reported per-case failures* only. Together the two rules zero the Goodhart surface.

### 11.2 The metric
`b_c[x] = canon(phaseA_output(c, x))`, `canon()` registered per class (versioned; a canon change
is a gen-boundary event). **D(S, X) = mean over unordered pairs {c₁,c₂}⊆S, x∈X of
1[b_c₁[x] ≠ b_c₂[x]]** — the probability two random passers disagree on a random probe. All pairs
if |S| ≤ 8 else max_pairs sampled. Per-input `d(x) = 1 − max_class_frequency(x)` ranks growth
targets. Cost: |S|·|X| sandbox executions, zero LLM tokens (cached artifacts; `verification` line).

### 11.3 The three duties (pre-registered inequalities)
```
D1 GROWTH    champion passed AND D(passers,X) > divergence_eps ⇒ NOT converged; emit top-k
             argmax d(x) → OBSERVED (§9). Growth disabled/exhausted ⇒ converge anyway, the
             certificate residual carries the divergence + unminted inputs (honesty over machinery).
D2 TRIPWIRE  after pollination round r: D_r ≤ κ·D_{r−1} AND champion_score_r ≤ score_{r−1} + m_min
             ⇒ quarantine round r (its submissions leave the next peer corpus), re-seed diversity,
             post oracle_gen{kind: diversity_alarm}. κ=0.25 default. The SCORE GUARD separates
             herding from victory: collapse WITH improvement is convergence on the answer;
             collapse WITHOUT it is the swarm converging on itself. ≤1 quarantine/run w/o operator ack.
D3 FLOOR     at round 1: D_1 ≥ floor_class (default 0.05) else re-seed (≤2), else REFUSE-TO-SWARM
             fallback: single-cell + verifier, receipted (diversity measured, not proxied:
             family count is the seed; D_1 is the check).
```

### 11.4 Prose degradation (honest)
No canon() for paragraphs ⇒ D-proxies, certificate-stated: (a) family-level panel dissent (free);
(b) claim-set Jaccard via d0 extractor (journaled; advisory). D2/D3 MAY run on proxies; **D1
minting REQUIRES executable or adjudicable inputs** — no case minted from fuzzy claim distance;
prose growth only through G3 routes 2/3.

## §12 · The single-cell null (arm-zero) — the swarm's own mortality clause

### 12.1 NullPolicy (run-manifest `null:` block; run engine enforces, this contract defines)

The null's mode is **derived from the class lifecycle**, never authored per-run (the synthesis of
v2 §5's rigor and the settled-class economics — seat 04's #683(c), accepted #695).

**This block is THE canonical `null:` grammar (R17) — the ONE home:** run.md §R1 regenerates its
`null:` block by COPY from here (never by hand); ARCH W1 cites it. `provenance` is a CLOSED enum
`{operator-pin, ranking-artifact}`; the `ref` grammar is `artifact://rankings/…#sha256=…`.

```yaml
null:
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
```
### 12.2 Parity laws (what "matched" means)
- The null is ONE cell of the pinned strongest family, running the IDENTICAL oracle loop: the
  operator's own wording (wording exploration is paid inside each arm's budget — F1's wording
  nuance cannot contaminate the control), the UNION of roster tools, the same grounding mode, the
  same generations, the same bar.
- The null is a **protected arm outside UCB allocation** (a control cannot be a bandit arm the
  optimizer starves).
### 12.3 Accounting (dual-unit; the certificate carries both)
- Matched **production** dollars: the null's production spend = the swarm's per-arm production cap.
- **Fixed** verification apparatus (oracle build, probe authorship) is arm-independent — excluded.
  **Marginal per-candidate grading** is arm-caused — charged to each arm including the null, via
  StackReceipt.cost joined by the econ fold (receipts are the attribution source; escrow stays one
  `verification` purse — seat 07 seam, #678).
- `vs_null` publishes margin at BOTH units — `margin_production` and **`margin_invoice`**
  (production + attributed verification — the unit that reaches the operator); the canonical
  members are R15's {null_score, null_usd, margin_production, margin_invoice} (§5.2); the swarm
  is never flattered in the operator's unit.
### 12.4 The null-flip law (ONE predicate; NULL-1 and ECON-8 cite it; seat 04's T3 adopted)
Per task class, over the trailing k=20 window at the deepest L-level with evidence:
`FLIP(class) := (≥ m=5 audited rows in window) ∧ (median audited margin_invoice ≤ 0)`
⇒ the class's default flips to single-cell + verifier (cheaper; overridable; re-armed when the
roster changes). **Audited rows** = matched-mode nulls and floor-mode matched replays ONLY;
floor-mode non-audit rows are sanity instruments, never flip evidence (their dollars are not
matched, so their lift is not comparable). **Meta-guard:** if the null never wins anywhere, it is
a strawman — audit parity, operator-blind. If the swarm never wins, that is HC-3′ failing at
scale, and the constitution publishes it (the honest kill of the fabric's own pitch).

## §13 · The operator as a priced organ (OPER-1 mechanized)

The conservation law's naive reading exempts the one node every trust cycle routes through: G3
fallbacks, AMBIGUOUS spec-bugs, errata, sealed keys, golden exemplars, generation promotion all
terminate in the operator — whose imports the fabric's own evidence says fail (F7 fan-in choke;
F1 wording; MAST's 41.77% specification failures). So the operator's imports are priced like every
other boundary crossing — a demotion of *default*, never a retirement of sovereignty.

### 13.1 Every operator adjudication is a receipt with a sampled null
`k%` (run-manifest field, default 10%) of operator adjudications — and, at rate 1.0, EVERY
operator golden registration at MINT time (§7, s6-11: a golden is admissible only after its one
disjoint re-adjudication) — receive one BLIND second
adjudication — executable where possible, else a fresh-family panel (families disjoint from any
that saw the case). Posted as `oracle_gen{kind: operator_audit}`:
```jsonc
{ "kind": "operator_audit", "case_ref": "…", "operator_label": "B",
  "second_authority": { "kind": "executable | panel-disjoint", "families": ["glm","kimi"] },
  "second_label": "B", "agree": true, "class": "code.func.validation", "ts": "…" }
```
In a declared operator-only run (no disjoint authority exists), the sample DEFERS to the epoch
recall drill (a later-provisioned family may exist by then); the unsampled fraction is published
beside the rate.
### 13.2 F7 discipline on the adjudication channel
AMBIGUOUS / spec-bug asks coalesce by input-class and batch at round boundaries; a per-run
mint-escalation cap; an adjudication-latency budget rendered in `hc top` — beyond it the fabric
degrades honestly to converged-with-residual (parked CONTESTED backlog, oldest-first), never guesses.
### 13.3 The wrong-case recall drill (each epoch)
Re-adjudicate a random sample of admitted library cases — AND of the operator's own curated
statutes: sealed-set answer keys and golden controls — per class under a fresh disjoint authority.
A failed re-adjudication auto-flags errata and SUSPENDS the contested statute (case →
`errata-retired` pending; golden → pulled from rotation; sealed key → flagged, the sealed report
annotated) pending operator-signed correction. A golden reversal additionally RESTORES judges
suspended on that golden's controls (§6 step 6, s6-11). The sealed set detects score *gaming*; this drill
detects case *wrongness* — both compounding liabilities closed.
### 13.4 Provisional-while-wide (the law that consumes the meter)
Per class, pre-register an operator-disagreement ceiling (default 20%). The published rate =
fold over `operator_audit` records (Wilson upper bound at small n, pessimistic like §14's ê).
**While rate > ceiling: operator-minted cases and adjudications in that class enter
`status: provisional`** — graded and reported separately, excluded from score/signature/prune,
NOT compounded into the library head — until the recall drill or a disjoint authority confirms
them (confirmation promotes provisional → active; a regrade round follows). Nothing overrules the
operator; the fabric merely stops compounding on unconfirmed imports while the error bar is wide.
`hc top` renders: rate, ceiling, unsampled fraction, provisional backlog, adjudication latency.

## §14 · Two-tier verification scheduling (the break-even, operational)

Cheap screen per round; full cross-family panel at promotion — as arithmetic, not vibes:
- Majority error `P_K(e) = Σ_{i=⌈(K+1)/2⌉..K} C(K,i)·e^i·(1−e)^(K−i)`; **K counts FAMILIES, not
  judges** (same-family judges are correlated voters — F9 as a theorem about money).
- **ê from the control record** (the §7 double duty), consumed PESSIMISTICALLY: the Wilson 95%
  upper bound on control_failures/control_trials (controls minted from past failures are
  distributionally stale ⇒ the raw rate lower-bounds error on novel candidates). No history ⇒
  registered prior ê₀ = 0.15. Wide interval ⇒ more panels — the correct failure direction.
- `V_wrong` per decision point (manifest `wrong_answer_cost`): promotion default = run `usd_cap`;
  per-round default = the round's production spend at risk.
- `K*(ê, V, c) := smallest odd K in [3, k_max] with (P_K(ê) − P_{K+2}(ê))·V < 2·c_judge`.
- SCHEDULE: per-round 1 screen judge (cheapest lane, family ≠ candidate's, rotating round-robin so
  the screen's blind spot is not constant; `tier: screen` receipts MUST NOT seat a champion, post
  a verdict, or trigger ejection). Promotion: full panel K = K* families, controls seeded,
  both-ways ties — ALWAYS (the constitutional floor: the arithmetic sizes K, it never zeroes the
  panel). ESCALATE screen→panel when ANY: (a) screen ≥ target − ε_esc; (b) unit and screen
  disagree in direction; (c) champion would change with margin < m_esc; (d) round == max_rounds.
- Worked (ê=.15, c=$0.002): promotion V=$2 ⇒ ΔP(1→3)·V=$0.178 vs $0.004 — 45× over break-even;
  per-round V=$0.05 ⇒ $0.0045 vs $0.004 — marginal ⇒ screen + triggers. "Essentially always at
  promotion and never per-round" — derived.

## §15 · [SECURITY-SEAM] blocks (what the trust plane NEEDS from seat 10)

- **[SECURITY-SEAM: SEC-1 operator-statute signing].** `sealed/commitment.json`, `errata.jsonl`
  rows, gen `manifest.json`, crucible resume commands, and null-pin operator overrides are
  **operator statutes**: each MUST carry a Stage-1b operator signature (ed25519 per
  identity-firewall.md); an unsigned statute is refused and alarmed. Key custody (off-box) is seat
  10's; the *verification points* (library open, sealed-run start, halt resume, errata apply) are
  defined here and MUST verify before acting.
- **[SECURITY-SEAM: SEC-2 judge-roster identity].** The pricebook's `weights_family` column is a
  TRUST input: recusal, quorum-after-recusal, family-counted K, and dissent all read it. A
  poisoned family column silently converts a cross-family panel into a monoculture (F9 by attack).
  NEED — both halves, per seat 10 #684 (accepted #695): (1) the SIGNED declaration — the pricebook
  signature explicitly covers `weights_family` (what the operator believes a lane runs); (2) the
  RUNTIME canary — MECHANIZED (s6-13): a per-round probe of (a) a TOKENIZER FINGERPRINT — the
  registered per-family tokenization of a fixed probe-string set (token counts + boundary
  positions are family-discriminative) — and (b) a per-family KNOWN-ANSWER corpus, pinned like
  controls (§7 registry shape: provenance + verification receipt + usage counters; overexposed
  items rotate). **FAIL-CLOSED: a claimed family with NO registered fingerprint/corpus contributes
  ZERO diversity** — never counted, not counted-until-proven-bad. On mismatch: that lane's scores
  are INVALID for the round AND its diversity contribution DE-RATES TO ZERO (family-unknown for
  quorum and K counting) until re-attested. **TWO FLAGS, TWO OWNERS:** `family_verified` (this
  canary; trust-owned; the ONLY flag that diversity-counting, quorum, and family-counted K may
  key on) is distinct from `parity_verified` (econ COST parity; pricebook-owned, seat 07 #679).
  Diversity-counting keys on `family_verified`, NEVER the econ score-parity probe — two families
  scoring within its ε on an easy oracle are not thereby one family, and one backend under two
  names is not thereby two. The roster solver reads `weights_family` only from signed books AND
  counts only `family_verified` lanes; aggregator hosts carry `parity_verified: false` until the
  econ parity probe passes. Falsifier: SEC-CANARY — a lane declaring family X while running
  family Y at matched score contributes ZERO diversity; the run degrades/refuses per §6 step 1.
- **[SECURITY-SEAM: SEC-3 receipt non-mintability].** StackReceipt/verdict/`oracle_gen` posts are
  conductor-only: the Medium post-ACL (seat 03 registry × seat 10 enforcement) is the mechanism;
  this contract's law is that a receipt arriving from any other identity is REJECTED at the
  Medium, not merely distrusted downstream.
- **[SECURITY-SEAM: SEC-4 sealed-run redaction].** Sealed-run mode suppresses journaling on grader
  cells; seat 10's redaction pass MUST additionally cover the *runner's* logs for the sealed-run
  window (sealed inputs transit prompts — the records-not-wires law holds only if runner-side
  debug logging is redaction-swept).
- **[SECURITY-SEAM: SEC-5 evidence-bundle provenance].** The grounding check consumes evidence
  bundles whose terminal refs carry seat-10 ingress trust tags (seat 02's T6); scrubbed provenance
  (seat 06's credential_carrier scrub) is REQUIRED before any citation line reaches a report file,
  certificate, or blind packet.

## §16 · Versioning + migration

**Semver:** field additions with defined absent-readings = MINOR; any change to attribution,
tri-state, aggregate semantics, or leak constraints = MAJOR. Every StackReceipt implicitly carries
its contract version via the run manifest's contract census (seat 02 genesis).

**§M Migration from the live v1 shape (`C:\hypercell\contracts\oracle.md` v0.1 + live code):**
1. `run_oracle(cmd, path)` (converge.py) → `grade(candidate_ref, stack, gen)`; the v1 protocol
   survives as `score-stdout-v1` (§2.5) with candidate execution split out (attribution for free
   where splittable; `attribution: coarse` where not).
2. `oracle.mode: golden|target|gate|judge-panel` (v0.1) → check composition: `judge-panel` becomes
   a `panel` check (`harness.none`); `golden/target/gate` become `unit` check configs. Old
   manifests read: mode maps to the equivalent single-check stack, `gen: 0`.
3. Live `Receipt{submission_seq, outcome, score, graded_by, evidence}` (types.py) → StackReceipt:
   old receipts read as single-check stacks, `oracle.gen = g0` forever, `failed_phase = null`,
   no `vs_null` (excluded from null folds).
4. `judge_score()` (judge.py) → §6 JUDGE-PIPELINE; the two lived P2 bugs (always-pass at :72,
   thin-quorum at :63-70) are closed by steps 7-8 + the §5.3 predicate; same-family default
   (one `cog`) is closed by step 1.
5. `oracles/ipv4_check.py` splits: `ipv4_driver.py` (in-sandbox, inputs-only) +
   `ipv4_grade.py` (phase B, owns CASES + expected values) — the reference oracle of TP-1.
6. The ٤ battery seeds `library://code.func.validation/ipv4_check@gen-0`; `CASES` leaves the
   grader file for `gen-0000/cases.jsonl` (the answer key exits candidate reach permanently).
