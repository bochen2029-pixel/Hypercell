# CONTRACT: role — the cell role manifest (the depth dial over ONE field space)

**Version:** 5.1.0 · **Status:** RATIFIED-DRAFT (v5 wave) · **Date:** 2026-07-16 · rev 2026-07-25 (P3 resolution)
**Pairing (H2):** `Cell` (noun — the spawn plane) · **Emit/read (H4):** strict-emit / liberal-read ·
**Operator boundary (R5):** strict-both (the G4 note below) ·
**Falsifiers:** [ROLE-1 (depth-grep; §4 L-NO-DEPTH-BRANCH), NUC-3 (the d2 admission gate). d3 has
no falsifier and no owning slice — it is capped at one per fleet and deliberately unscheduled
(ARCH §15); this header does NOT cite a bar that does not exist.]
**Replaces:** v0.1 stub (live repo) + v3 draft (wave paper §N5)
**Pairs with:** `contracts/nucleus.md` 5.0 (every `memory.*`/`frame.*` knob's mechanism) ·
`contracts/act.md` 5.x + `contracts/identity-firewall.md` 5.x (tool profiles, trifecta booleans,
harm gate) · `contracts/run.md` 5.x (per-slot diversity binding) · `contracts/pricebook.md` 5.x
(lane realization) · JSON-Schema mirror at `contracts/schemas/role.schema.json`.
**Register:** RFC-2119. **Reader liberality (G4):** a manifest is validated STRICT at authoring/spawn
time (unknown fields refused with a typed error — a typo'd knob must not silently no-op) and read
LIBERAL by every other consumer (unknown fields preserved, never dropped, never errored) so an old
fleet can carry new-field manifests through untouched.

> **A1 realized:** depth is a **defaults preset over one field space**, never a type. Any field is
> individually overridable; the runtime never branches on `depth` except through the defaults table
> (§2). **Depth ⊥ intelligence:** a d0 judge MAY run max-effort frontier weights; a d3 brain MAY idle
> on a local 9B. **Sandbox class derives from harm + tools, never depth.**

## §1 · The field space (complete; every field below `name` has a default)

> **[R28] What §2 does and does not contain.** §2 is the table of **depth-VARYING** defaults — the
> fields whose default changes across d0/d1/d2/d3. Fields whose default is **depth-invariant** carry
> that default here in §1 and are marked as such; they are deliberately absent from §2 rather than
> padded into it with four identical columns. `comment`, `prompt`, `egress`, `oracle_ref`, `diversity`
> and `max_wager_horizon` are depth-invariant. A1 is unharmed: depth still selects a defaults column,
> and it still selects nothing else.

```yaml
name: refiner                    # REQUIRED. The only field with no default.
depth: d1                        # d0|d1|d2|d3 — selects the DEFAULTS COLUMN, nothing else
comment: ""                      # free text; never enters the frame
provider:                        # WEIGHTS = the diversity axis; the role PINS it (blind spots
  weights_family: deepseek       #   follow weights, not endpoints — F1/F9)
  model: deepseek-chat
  base_url: null                 #   null → registry default
  key_ref: null                  #   env/secret NAME (never a value); null → <FAMILY>_API_KEY
  params: {temperature: 0.7}
  effort: null                   #   provider effort dial, if the lane has one
lane_hints:                      # HINTS ONLY — the economics plane may override, logged
  latency_class: standard        #   interactive|standard|batch
  batch_ok: true
  cache_mode: auto
prompt: |                        # the role's system prompt (frame S0 head; positive specification)
  You are a refiner…
grounding_mode: none             # none | sampled | required (the A11 dial — act.md §9.1 owns the mode
                                 #   semantics; a run may RAISE, never lower)
capabilities: [code, python]     # router placement (MoE)
tools:                           # each entry: {ref, profile} — ref = MCP/adapter id; profile = the
  - ref: web.fetch               #   TOOL-PROFILE ANNEX id (act.md format; carries harm floor, egress
    profile: tp/web.fetch@1      #   allowlist, credential_carrier, trifecta booleans {private_data,
                                 #   untrusted_content, external_comms} — declared values are ADVISORY;
                                 #   identity-firewall.md B.4's Rule-of-Two gate RECOMPUTES the fold at
                                 #   spawn and at every ingress, and refuses a profile whose declaration
                                 #   is weaker than the recomputation). A bare-string
                                 #   entry is read as {ref: s, profile: null} (reader liberality);
                                 #   profile: null is REFUSED at spawn for harm ≥ H1 tools.
harm_ceiling: H1                 # H0..H3; the membrane gate enforces
egress: []                       # DECLARATION of intended hosts; enforcement = identity-firewall.md
standing_access: []              # declared private-surface access the role may read:
                                 #   operator-memory | foreign-nucleus | peer-output-ingestion
                                 #   (closed set). The trifecta `private_data` leg reads it —
                                 #   act.md §6.1h at the act gate; identity-firewall.md B.4 folds it
                                 #   with received peer output and operator-memory grants.
isolate_intent: pooled           # pooled|isolated|hardened — HARM-derived default, never depth-derived
oracle_ref: null
diversity: {slot: null, seed: null, angle: null}   # bound by the run manifest's diversity vector
budget: {step_usd: 0.10, lifetime_usd: 1.0, maintenance_pct: 0}
max_wager_horizon: 7d            # [R29] depth-INVARIANT. The furthest future a held act may be
                                 #   wagered against; act.md §4 reads it and §13 promises it.
                                 #   Relocated here in the P3 pass — act.md stated the default while
                                 #   the field had no home, which is exactly the two-homes/no-home
                                 #   drift class R18 exists to kill.
memory:
  ledger: full                   # none | full  (none at ANY depth — sealed-set grader cells use it
                                 #   so sealed bytes can never land in a nucleus record; trust seam)
  fsync: gold                    # gold (two laws + group-commit) | always (exact v1 behavior)
  segment_mb: 64
  renders: [index]               # index | fts | tkg (tkg implies dark until NUC-3)
  verbs: false                   # remember/recall/revise/forget/pin
  registers: [narrative, factual]
  pin_budget: 0
  recall_k: 0
  consolidation:
    enabled: false
    idle_s: 300
    min_records: 200
    min_tokens: 50000
    budget_pct: 5                # the maintenance line (of lifetime spend)
    cold_eyes_family: rotate     # rotate (default; ≠L1, rotates per pass) | a pinned family ≠ L1
    install: task-boundary       # never mid-task (the cache seam depends on it)
frame:
  ratios: {identity: .10, tools: .08, digest: 0, working: .12, retrieved: 0, recap: .25, percept: .35, slack: .10}
  salience: {w_pin: 4.0, w_factual: 2.0, w_task: 1.5, w_recency: 1.0, w_ref: 0.5, half_life: 512}
  recap_k: 8
  self_tune: {enabled: false, bounds_pct: 50}      # d3: journaled tuning, ±bounds, never beyond
wake:
  policy: on_task                # none | on_task | on_mention | self_clocked
  max_idle_s: null
anchor: {enabled: false, every_n_records: 512}     # d3: post ledger head hash to Medium (compiles to
                                                   # a status post — no new wire type)
```

## §2 · The defaults table — every field, four columns (`—` = n/a; the COMPLETE preset)

| field | **d0 reflex** | **d1 worker** | **d2 resident** | **d3 brain** |
|---|---|---|---|---|
| provider.* / effort | *free (operator)* | *free* | *free* | *free* — depth ⊥ intelligence |
| lane_hints.latency_class | interactive | standard | standard | batch-tolerant |
| lane_hints.batch_ok | true | true | true | false (wakes are latency-bound) |
| lane_hints.cache_mode | auto | auto | auto | auto |
| grounding_mode | none (run may raise) | none | required | required |
| capabilities / tools | per role | per role | per role | per role |
| harm_ceiling | H0 | H1 | H1 | H2 |
| standing_access | [] | [] | per role | per role |
| isolate_intent | pooled | pooled | pooled | pooled (harm promotes, depth never) |
| budget.step_usd | 0.05 | 0.10 | 0.25 | 1.00 |
| budget.lifetime_usd | — | 1 | 10 | 100 |
| budget.maintenance_pct | 0 | 0 | 5 | 5 |
| memory.ledger | **none** (Culture run-log line) | full | full | full |
| memory.fsync | — | gold | gold | gold |
| memory.segment_mb | — | 64 | 64 | 256 |
| memory.renders | [] | [index] | [index, fts] | [index, fts, tkg-dark] |
| memory.verbs | off | off | **on** | on |
| memory.registers | — | — | [narrative, factual] | [narrative, factual] |
| memory.pin_budget | 0 | 0 | 12 | 24 |
| memory.recall_k | 0 | 0 | 6 | 10 |
| consolidation.enabled | no | no | **yes** | yes |
| consolidation idle_s / min_records / min_tokens | — | — | 300 / 200 / 50 K | 600 / 500 / 150 K |
| consolidation budget_pct / cold_eyes / install | — | — | 5 / rotate / task-boundary | 5 / rotate / task-boundary |
| frame.ratios (identity/tools/digest/working/retrieved/recap/percept/slack) | *bypass* (prompt+percept) | .10/.08/0/.12/0/.25/.35/.10 | .08/.08/.12/.10/.14/.18/.22/.08 | .08/.06/.18/.10/.18/.12/.20/.08 |
| frame.salience / recap_k | — | v1 / 8 | v1 / 12 | v1 / 12 |
| frame.self_tune | no | no | no | **yes** (±50%, journaled) |
| wake.policy | none (spawned per call) | on_task | on_mention | self_clocked |
| wake.max_idle_s | — | — | — | 3600 |
| anchor | no | no | no | **yes**, every 512 records |
| nucleus records per `ask` (NUC-9) | **0** | **2** (adhoc; + read-barrier) | full taxonomy | full taxonomy |

Governance line (constitution §8, kept): **at most one d3 per fleet — and the cap stands, because no d3 admission bar exists** (§15 mints
none; d3 is gated behind NUC-3’s d2 outcome and is unscheduled).

## §3 · The ≤5-line d0 manifest (the dial, proven)

```yaml
name: probe
depth: d0
provider: {weights_family: deepseek, model: deepseek-chat}
prompt: "Extract the ticket id. Answer with the id only."
```

Four content lines; the defaults column fills the other ~30 fields. Same runtime, same image — the depth-⊥-intelligence claim's
d0 half costs a manifest this size, its d3 half costs a longer manifest, never a new type.

## §4 · Laws over the space

- **L-ROLE-DIGEST:** `role_digest = sha256(canon(manifest AFTER defaults expansion))`, recorded in
  genesis; frame determinism and cache epochs key on it. Editing a role mid-life is a NEW digest —
  a re-manifest event, never a silent drift.
- **L-STRICT-SPAWN / LIBERAL-READ (G4):** header note, normative. Spawn-time validation additionally
  REFUSES: S0+S1+S2 ratio-budget overflow at the declared window (nucleus.md §7.2 step 5),
  `Σ(frame.ratios, slack included) ≠ 1.0 ± ε`, tools whose
  profiles exceed `harm_ceiling`, `profile: null` at harm ≥ H1, pin_budget 0 with verbs on and pins
  requested.
- **L-RAISE-ONLY:** a run manifest may RAISE `grounding_mode` and LOWER `harm_ceiling`/budgets for its
  slots; never the reverse. (The strictest of role/run/operator wins where they disagree.)
- **L-SEALED-SET:** `memory.ledger: none` MUST be honored at every depth (trust seam: sealed-run
  grader cells; sealed bytes never land in a nucleus record).
- **L-NO-DEPTH-BRANCH:** runtime code branches on FIELDS (memory.verbs, wake.policy, …), never on
  `depth` itself, except the defaults-table lookup. (Falsifier: grep the runtime for `depth ==` — the
  only hit is the preset loader.)

## §5 · Migration from the live v1 shape (`common/types.py:91-102` + contracts/role.md v0.1)

| v1 field | v5 mapping |
|---|---|
| `provider.provider` (str) | `provider.weights_family` (the diversity axis was always the family; the endpoint is `base_url`) |
| `memory_policy: "scratch"` | `memory: {ledger: full, verbs: false, renders: [index]}` (d0/d1 defaults column) |
| `memory_policy: "reel"` | `memory:` d2 defaults column (verbs on, fts render, consolidation on) |
| `tools: [str]` | `tools: [{ref, profile}]`; bare strings read as `{ref, profile: null}` (liberal read), refused at spawn for H1+ |
| absent `lane_hints/budget/diversity/frame/wake/anchor/egress/isolate_intent/grounding_mode/comment` | defaults column of `depth` |
| `Role(extra="forbid")` frozen model | split: authoring validator stays strict; fleet readers move to liberal read (G4) — the pydantic model gains `extra="allow"` on the READ path only |

v1 manifests on disk remain valid v5 manifests (every v1 field has a v5 reading; nothing is dropped).
