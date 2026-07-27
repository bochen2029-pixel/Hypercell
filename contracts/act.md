# CONTRACT: act — the act plane (acts · receipts · effects · evidence · grounding · tools)

**Version:** 5.1.0 · **Status:** RATIFIED WITH v5 · RFC-2119 throughout. · **Date:** 2026-07-16 · rev 2026-07-25 (P3 resolution)
**Pairing (kernel §3):** verb-plane contract for the verb `act` — the only world-touching verb. Owner: Membrane
(gate + executor) with Conductor-side folds (effect registry, settlement, stains).
**Emit/read (H4):** strict-emit / liberal-read (the G4 note below) · **Operator boundary (R5):** n/a — no
operator-authored artifact validates here (grants/cancels ride command.md's CommandEnvelope) ·
**Schema mirror:** `contracts/schemas/act.schema.json` (lockstep, same commit — Change law below) ·
**Falsifiers:** [ACT-GATE-1, ACT-SETTLE-1, ACT-H2-1, ACT-SCRUB-1, ACT-TRIFECTA-1, DELIVER-1, GROUND-1/2]
**Change law:** any field add = MINOR; field remove/retype or semantic change = MAJOR; this file, the JSON-Schema
mirror (`schemas/act.schema.json`), and the code change in one commit (kernel versioning law; version census in
the nucleus genesis record).
**Reader liberality (G4 fix, kernel R2/R5):** emitters emit exactly this shape; readers MUST ignore unknown
fields and MUST preserve them on re-emit (never `extra=forbid` on read paths). A reader that cannot parse a
REQUIRED field treats the record as `invalid`, never as absent.
**Migration from live v1:** §13. The live repo has **no act code**: `cell/membrane.py` is 18 lines (firewall
predicate + string wrap only); `MessageType` (`common/types.py:32-44`) has neither `act` nor `act_receipt`;
`Role.tools` and `Role.harm_ceiling` already exist (`types.py:99,102`) and are consumed here unchanged.

## §1 · Principles (the laws this contract mechanizes)

1. **One verb, one executor.** Every world-touching call — a web fetch, a sandbox run, a delivery — is an `act`
   through ONE pipeline (§6.0). No second code path may reach the world (fixes the F17 defect class
   structurally: `runtime.py:83-101`'s unguarded `produce()` is the lived counterexample).
2. **Conservation of trust (A5) on this plane:** no act reports itself — the executor/resolver mints the
   receipt, reality grades the wager; no answer asserts itself — evidence or an honest label (§9); refusals are
   receipts too.
3. **fsync-before-effect:** the act record is fsynced in the actor's nucleus BEFORE the effect executes
   (`cell/nucleus.py:67-70` already conforms; the nucleus contract's `append()` property, reaffirmed seam #350).
4. **Fold Law (A13):** every durable act-plane structure is a deterministic fold over D-gold records (§11).
5. **Degeneracy:** Conductor round-trips per act = **0 at H0** (in-process gate; leased metering §10.4), **1 at
   H1+** (effect reservation), **2 for held acts** (reserve + grant consumption). `hc ask` touches none of this.

## §2 · The `act` payload (cell → Membrane → executor; Medium type `act`)

Envelope columns (`seq/ts/culture/sender/corr/…`) are wire.md's; `envelope.corr MUST equal act_id`.

```jsonc
{
  "act_id": "01JZX9GJB2M8Q4R7T5V6W8Y0A1",  // ULID, actor-minted; the corr for every phase receipt & grant.
  "claim": "r42/researcher/0",             // actor claim-id: binds act -> durable identity -> lineage.
  "capability_ref": "web.fetch",           // MUST resolve in Annex A (§10) AND ∈ role.tools.
  "tool_version": 1,                       // profile MAJOR pinned at gate time; receipts echo it.
  "harm_declared": "H0",                   // cell's claim. harm_effective = max(declared, derived) at gate;
                                           // declared < derived => REFUSE, never silent promotion (§6.1).
  "idem": "01JZX9GJB2M8Q4R7T5V6W8Y0A1",    // REQUIRED H1+; attempt-level key for nucleus resume dedup
                                           // (v1 outcome_for(idem), nucleus.py:98-104). Defaults to act_id.
  "attempt": 1,                            // increments ONLY after exec outcome=invalid (apparatus failure).
  "effect_scope": "lineage",               // instance | lineage | slot. REQUIRED H1+; H0 fixed at instance.
  "effect_id": "sha256:9f2c…",             // sha256(capability_ref ‖ tool_version ‖ JCS(sig_args));
                                           // JCS = RFC 8785 over effect-significant args ONLY (§7.1).
  "expectation": { /* §4 */ },             // REQUIRED H1+ and MUST pass the losability battery (§4.1).
                                           // MAY at H0 but SHOULD NOT (a read that cannot mutate needs no
                                           // wager; a scheduled re-observation is just a new H0 act).
  "args": { "url": "https://…", "max_bytes": 2097152 },
  "args_ref": null,                        // artifact pointer when args > 4KB (wire body cap).
  "cost_est": { "usd_worst": 0.0005, "basis": "pricebook:tool.web.fetch@<as_of>" }
}
```

Field laws: `args` MUST validate against the profile's `args_schema` (gate step b). `args` MUST NOT contain
credentials in any position (gate step f refuses on the profile's `credential_carrier` pattern set; adapter
credentials are fabric-held and injected at the executor — §10.2). `cost_est.usd_worst` MUST be computable
from the pricebook lane, else the act is **unreservable, hence refused** (econ T1 extended to tools).

## §3 · The `act_receipt` payload (executor/Conductor → Medium; NEVER the acting cell)

**Type status (ruled, #687/#692, coordinator-countersigned — R1):** `act_receipt` is a first-class Medium
type. (The registry is now **17** total — seat 01 ruled `cmd_receipt` first-class alongside `act_receipt`,
giving the fabric's three boundaries three non-mintable receipt types: `act_receipt` = world below,
`cmd_receipt` = operator above, `receipt` = the bar. My plane owns only `act`/`act_receipt`.)
The **type is the ACL key**: `act_receipt` is mintable by **executor principals** (runner-N, the Conductor's
resolver/settlement daemons) and by NO acting cell's cognition principal (A5: no act reports itself; at T0
class-0 the executor is in-process and this is convention red-teamed by HC-7-v2 attempt 8; from Stage 1a it is
a mechanical post-ACL row — [SECURITY-SEAM §12.4]).
**Duty split (V-RECEIPT, kernel):** `act_receipt` = the WORLD side (what happened: hold/exec/settle);
`receipt{subject:act}` = the ORACLE side (what it was worth, trust-plane, seat-05 contract). `graded_by` on an
act_receipt is an executor or resolver id, never a judge.

Three phases = **three separate envelopes sharing `corr = act_id`**, never a mutable row:

```jsonc
{
  "act_id": "01JZX9GJB2…",
  "phase": "exec",                         // hold | exec | settle
  "outcome": "ok",                         //   exec:   ok | refused | invalid | unknown
                                           //   settle: ok | miss | expired
                                           //   hold:   (no outcome; carries "hold" + "summary")
  "reason": null,                          // refused: harm_derived | harm_ceiling | egress | budget |
                                           //   duplicate_effect | not_losable | trifecta | canceled |
                                           //   grant_lapsed | dead_man    (closed enum; MINOR to extend)
  "harm_effective": "H0",
  "tool_version": 1,
  "evidence": {                            // exec phase; §5 for how refs point AT this
    "output_hash": "sha256:ab41…",         // over RAW output bytes, pre-transform (re-checkable)
    "artifact": { "path": "sha256/ab/ab41….html", "bytes": 18734,
                  "mime": "text/html", "sha256": "ab41…" },       // content-addressed store
    "provenance": { "url": "https://…", "method": "GET", "status": 200,
                    "etag": "W/\"1a2b\"", "content_type": "text/html",
                    "scrubbed": false },   // TRUE iff credential components were removed (§10.2);
                                           // scrubbed provenance is the ONLY provenance that may cross
                                           // into evidence bundles, reports, or certificates (seat 05).
    "retrieved_at": "2026-07-16T04:41:00.212Z",
    "truncated": false                     // max_bytes hit => true => evidence graded partial (§5.4)
  },
  "isolation": { "required": "class-0", "actual": "class-0", "degraded": false },
  "cost": { "usd_effective": 0.0003, "usd_reserved": 0.0005, "sku": "tool.web.fetch",
            "purpose": "tool", "resv_id": "lease:tool.web.fetch/r42-researcher-0",
            "pricebook_version": "2026-07" }, // the canonical six (R16); seat-07 cost{} field-group (#694):
                                           // escrow truth-home is the Conductor's own ledger; this group
                                           // rides records already crossing — NO type=spend on the Medium.
  "wall_ms": 412,                          // SIBLING measurement field, never a cost{} member (R16);
                                           // `tokens`, where present, rides the same way.
  "graded_by": "executor:runner-1",        // exec: executor id · settle: "resolver:<check.kind>" ·
                                           // hold: "conductor" · reconcile-minted: "resolver:reconcile"
  "attempt": 1,
  "summary": null,                         // phase=hold ONLY (join-free queue rendering, seat 08):
                                           // { "claim": "r42/researcher/0", "capability_ref": "email.send",
                                           //   "harm_effective": "H2",
                                           //   "expectation": { "kind": "http_status", "resolve_by": ts }|null,
                                           //   "until": ts|null, "grant_ttl_s": 86400 }
  "hold": null,                            // phase=hold ONLY:
                                           // { "until": ts|null, "notified_seq": int|null,
                                           //   "escalated": "H3"|null, "grant_ref": cmd_id|null }
  "duplicate_of": null                     // refused/duplicate_effect: the WINNER's act_id — the losing
                                           // sibling awaits that corr and SHARES its evidence (§7.3).
}
```

### §3.1 Outcome semantics, phase-partitioned (normative)

| phase | outcome | meaning | retry law |
|---|---|---|---|
| exec | `ok` | channel completed; the result — whatever it shows; a 403 page is a completed observation — is in `evidence` | n/a |
| exec | `refused` | did not execute, by decision (gate predicate, budget, duplicate, trifecta, cancel, **grant expiry**) | fix and re-submit (a NEW act) |
| exec | `invalid` | apparatus failure BEFORE the world was reached (executor bug; sandbox failed to start) | retry legal: same `idem`, `attempt+1` |
| exec | `unknown` | dispatched, no definitive response (timeout mid-flight; crash between journal and outcome) | **NEVER blind-retry** → reconciliation §8 |
| settle | `ok` | the wager held: expectation observed true by `resolve_by` | n/a |
| settle | `miss` | the wager lost: check ran, observed false | `on_miss` policy (§4) |
| settle | `expired` | undecidable by deadline (resolver down; late check on a non-monotone observable) | escalates like miss, tagged apparatus |

**Phase law:** a `settle` receipt REQUIRES a prior `exec ok` on the same corr. Grant expiry on a held (never
executed) act is therefore `exec/refused/grant_lapsed` — *ruled here*, repairing the v3 §2.2-vs-§3.4
contradiction: a hold that lapses produces a terminal refusal, not a settlement.

### §3.2 Retention & durability (cite-pinned; adjudication #10, kept)

**H1+ acts and their receipts: R-forever + D-gold unconditionally** (world effects are the provenance
skeleton). **H0 acts/receipts default R-run + D-chatter** (loss = a re-fetch). At verdict time the Conductor
**retention-promotes exactly the act receipts in the delivered verdict's evidence closure** — a fold over
`verdict.evidence[]` closures (seat 03 T6), never a row mutation. Uncited H0 fetches decay with the run.

## §4 · `expectation` — the losable wager

```jsonc
{
  "check": { "kind": "http_status",                     // ∈ resolver registry (§4.2)
             "args": { "url": "https://…", "method": "HEAD", "expect": [200] } },
  "resolve_by": "2026-07-16T05:41:00Z",                 // > journal-ts + effect latency;
                                                        // ≤ role.max_wager_horizon (default 7d)
  "on_miss": "flag",                                    // flag | compensate:<profile-template ref>
                                                        // compensation = a NEW act, full pipeline, its own
                                                        // wager; never an implicit rollback
  "resolver": "conductor"                               // conductor | operator (manual; H2/H3 only)
}
```

### §4.1 Losability battery (gate step g; all four MUST hold)
1. `check.kind ∈` registry ∧ `check.args` schema-valid for the kind (every kind total & decidable with a
   reachable FAILS branch).
2. **Non-tautology:** the expected-set MUST NOT cover the kind's codomain (`http_status expect:[200..599]`
   rejects at parse). A wager that cannot lose is not a wager.
3. **Independence:** the check consults only world/Medium/artifact-store observables; no registry kind can
   read the actor's own assertion text (A5).
4. **Window:** journal-ts + expected effect latency < `resolve_by` ≤ `role.max_wager_horizon`.

### §4.2 Resolver registry (initial kinds; each returns HOLDS | FAILS | UNDECIDABLE)
`http_status` · `content_digest` (re-fetch, compare sha256) · `dns_resolves` · `file_exists` (artifact-store
stat + **digest** — a same-name spoof file never satisfies it; seat 09 seals `/out/manifest.json` before any
probe can read it) · `medium_query` (filter + count comparator) · `oracle_cmd` (registered checker) · `manual`
(operator task; legal only where an operator is already in the loop, H2/H3). Each kind declares
`late_check: valid | expired` — a post-deadline check counts only if its observable is **monotone** (an email
delivered stays delivered); default `expired` — honesty over generosity.

### §4.3 Settlement
The settlement daemon is Conductor-side, cognition-free registry logic. Fold-conformant: on start it
re-derives `unsettled := { acts | exec ok ∧ expectation ∧ resolve_by ≤ now ∧ no settle receipt }` from the log
and runs the checks; `graded_by: resolver:<kind>`. A cell never settles its own wager.
**Wager ledger:** a fold over settle receipts, per `(claim, capability_ref)` → `{wagers, won, lost, expired}`.
Consumed as observability, never auto-kill (v2 §13): `hc top` flags miss-rates over pre-registered bounds;
SHOULD-dial: H2 hold delay scales `delay × (1 + k·miss_rate)`.

## §5 · Evidence — one locator scheme; resolution, sampling, staleness

### §5.1 `evidence[]` entry (on `submission` and `verdict`)

```jsonc
{ "kind": "act",                           // act | medium | nucleus | url | file (= scheme, kept
                                           // explicit [R30: `url`, never `web` — wire.md §3.1 owns shape]
                                           // so folds filter without parsing URIs)
  "ref": "act://01JZX9GJB2M8Q4R7T5V6W8Y0A1",
  "sha256": "ab41…",                       // content digest at witness time
  "retrieved_at": "2026-07-16T04:41:00Z",
  "quote": "Qdrant sustained 2,100 QPS at 1M vectors…",   // ≤ grounding.quote_max (default 500 chars)
  "role": "supports" }                     // supports | contradicts | context
```

`quote` = the entailing span (without it, entailment checks re-read whole artifacts and GX-2 dies);
`role: contradicts` is first-class — it is the payload shape of the `oracle_gap` hint (a cell surfacing
receipt-contradicting evidence); `context` is un-graded background.

### §5.2 Schemes & resolution (numbered; hop limit 3, no cycles, every hop's digest MUST verify)
1. Unknown scheme → **structural fail** (invalid ref, not merely unverified).
2. `medium://<culture>/<seq>` → envelope+body at seq; integrity = the per-culture hash chain. Constitutional
   folds MUST cite compaction-closed types (cite receipts, not chat).
3. `act://<corr>` → the query `(type ∈ {act, act_receipt}, corr)`; evidence content := the exec receipt's
   artifact. MUST resolve to `phase:exec, outcome:ok` to serve as `supports`; a refused/miss receipt is
   citable only as `context` (the honest paywall attempt). **Resolution horizon:** resolvable forever iff
   cited by a retained verdict's evidence closure or H1+; uncited H0 refs resolve for the run's retention
   span only — the walkable set is defined, not discovered.
4. `nucleus://<claim-id>/<seq>` → a private ledger record; resolves ONLY through the audit channel
   (Conductor-side, strictest auth; peers/judges never read foreign nuclei — judges get the quoted span
   inline). The record MUST be `register: factual`; factual records' refs terminate in
   percepts/**act-execution receipts**/commands within ≤3 hops (nucleus xref allowlist includes
   `act_receipt` — cross-ruled with seat 02).
5. `https://<url>#sha256=<digest>` → resolves via the **witnessing act's stored artifact** (digest = join key
   into the content-addressed store); the live web is re-fetched only to re-witness staleness. **An https ref
   with no witnessing act in the poster's own receipt set is a naked claim.** You cite what you fetched, not
   what you remember.
6. `file://<path>#sha256=<digest>` → artifact-store/workspace volumes only; digest mandatory; out-of-volume
   paths structural-fail (the oracle dir is never mounted — HC-7).

### §5.3 Verification sampling (two-tier; who pays what)

| check | when | rate |
|---|---|---|
| structural (URI parses; scheme known; fields present; quote ≤ cap) | membrane post-gate | 100% |
| **act-ref provenance** — every `act://` ref ∈ the poster's OWN receipt history (`exists()`) | membrane post-gate | **100% — forged refs die structurally** |
| digest re-verification (stored bytes hash equal) | grounding validator (§9.3) | ρ=0.2 per submission (min 1, stratified); **100% at champion promotion; 100% for stained roles** until 3 clean runs |
| quote-presence (containment in artifact) | grounding validator | same sample |
| quote-**entailment** (does the span support the claim?) | judge panel (seat 05) | k=2 refs per submission, coordinator-sampled (never judge-picked); `citation_precision p@k` on the StackReceipt |

### §5.4 Staleness & partiality
`retrieved_at` older than the run's `grounding.max_age` → ref demotes to `context` unless re-witnessed (a
`content_digest` re-check refreshes `retrieved_at`; a changed digest is a NEW witness, not an erratum).
Staleness never improves a grade. `truncated:true` artifacts support only claims about the retrieved prefix;
judges see the flag.

## §6 · The harm dial, mechanized

### §6.0 ACT-PIPELINE (normative; the only path to the world)

```
composed → 1 GATE → 2 ESCROW → 3 EFFECT-RESERVE → 4 JOURNAL(fsync) → 5 EXECUTE → 6 RECEIPT → 7 SETTLE
                │
                ├─ REFUSE (any gate predicate) → act_receipt{exec, refused, reason} — refusals are receipts
                └─ H3, or H2-unattended: … → 4 JOURNAL(fsync) → HOLD (receipt phase:hold) →
                   grant/deadline → re-GATE (statics only, authoritative) → 2 ESCROW → 3 EFFECT-RESERVE →
                   5 EXECUTE → 6 RECEIPT → 7 SETTLE          (no re-journal; §6.4)
```

### §6.1 GATE (step 1; static, in-process, order normative)
a. `capability_ref` resolves in Annex A ∧ ∈ `role.tools`.
b. `args` validate against `args_schema`; **credential-pattern refuse** (no cell-supplied credentials, §10.2).
c. `harm_derived := profile.harm_floor ⊔ shape(args)` — shape raises harm on non-GET/HEAD method, body,
   cell-scoped credential, or state addressing (generic transports only; adapters are admission-certified §6.2).
d. `harm_effective := max(harm_declared, harm_derived)`; **declared < derived ⇒ REFUSE
   (`reason: harm_derived`)** — never silent promotion (the wager must be cell-authored; adjudication #4).
e. `harm_effective ≤ role.harm_ceiling`, else REFUSE.
f. Egress target ⊆ role egress allowlist, else REFUSE (enforcement internals [SECURITY-SEAM §12.2]).
g. H1+: `idem` present ∧ `effect_scope` named ∧ expectation passes §4.1, else REFUSE (`not_losable`).
h. **Trifecta step (NEW):** `T := profile.trifecta ⊔ cell.acquired_trifecta ⊔ role.standing_access`; if T
   completes {private_data, untrusted_content, external_comms} → REFUSE (`reason: trifecta`) unless the
   operator waiver policy applies (scoped-act → shed-egress → quarantine; seat 10 owns policy semantics).
   `cell.acquired_trifecta` is a FOLD over the cell's exec-ok receipts since spawn (untrusted_content is
   ACQUIRED on the first world-content fetch) — ingress re-evaluation as a log query, zero monitors.
i. H3 (and H2 in an unattended run): → JOURNAL then HOLD (§6.4–6.5).

### §6.2 H0 — observation as a structurally read-only channel (two legs, one predicate table)
- **Generic transports** (`web.fetch`, `fs.read`): the CELL composes the request → structural law verbatim:
  methods ∈ {GET, HEAD}, no body, no cell-scoped credentials, no session state. (v2 §6's Membrane-injected
  read-scoped credentials on allowlisted GET/HEAD endpoints remain legal — the injection is fabric-side.)
- **Profiled adapters** (`web.search` via a search API): the FABRIC composes the request → H0 is certified at
  **profile admission**, once, under the predicate: (a) cell args are query CONTENT only, cannot address
  state; (b) credentials adapter-held, read-scoped, executor-injected, invisible to cell/frames/ledgers;
  (c) endpoint pinned ∧ ⊆ egress allowlist. The adapter's private wire mechanics (a POST to the search
  endpoint) are irrelevant: **harm grades the cell's causal surface, not the adapter's plumbing.**
- **H0-by-declaration stays dead:** no cell declares H0 — `harm_floor` is fabric data; derived-harm still
  refuses args that smuggle method/body/credential/state.
- **H0 ≠ exfil-safe (NEW; the EchoLeak lesson).** H0 grades MUTATION risk only. A cell-composed GET URL is an
  egress channel (`?leak=<secret>` — the EchoLeak class exfiltrated via GET image URLs). Exfiltration risk is
  the trifecta plane's: profiles declare `exfil_channel` (§10.3); the derivation rule (seat 10, #699,
  verbatim): **`external_comms := egress-allowlist-breadth OR cell-composed-destination, NEVER method`** — a
  read-only GET can exfiltrate, so method never clears the boolean.
- Caps: `max_bytes` + `timeout_s` (oversize ⇒ `truncated:true`); `web.*` resolves public ranges only —
  fabric-internal state has its own locators (`medium://`, `file://`), so an internal fetch can never
  masquerade as world evidence.

### §6.3 H1 — execute → receipt
The full pipeline, one Conductor round-trip (the effect reservation). H1 is the DEFAULT world-write tier and
MUST stay this cheap.

### §6.4 H2 — the hold is a cancelable message; the dead-man clause
1. Gate passes statics → **JOURNAL (fsync) precedes the hold** — the hold must be durable. (This repairs the
   v3 state-diagram/§3.3 contradiction: held acts journal BEFORE holding; after grant they re-gate, escrow,
   effect-reserve, execute — **no second journal**; the effect-registry hold→exec transition consumes the grant.)
2. Conductor posts `act_receipt{phase:hold, summary{…}, hold:{until: now+delay, notified_seq:null}}` to the
   run culture AND `_ops` — one record = the countdown AND the visible, cancelable message.
3. **Proof-of-notification** = an INTERACTIVE-class surface principal's read-cursor advancing past the hold
   record's seq (or explicit surface ACK). Surfaces declare `cursor_class: interactive | headless` at
   registration; headless MCP clients and cron ticks can never satisfy the dead-man; the read-only viewer is
   constitutionally mute. Recorded as `hold.notified_seq` (adjudication #8).
4. Notified ∧ not canceled by `until` → **re-run gate statics (the second gate is authoritative** — role,
   allowlist, pricebook, trifecta state may have changed) → EXECUTE → exec receipt.
5. **Dead-man:** no proof by `until − grace` (grace = max(10% of delay, 60s)) → post
   `act_receipt{phase:hold, hold:{escalated:"H3"}}` — the act parks. A cancelable delay nobody fetched is H1
   wearing H2's badge — now a log query.
6. `command{kind:cancel, corr:act_id}` (legal only in phase=hold) → `exec/refused/canceled`. Unattended runs:
   H2 enters HOLDING directly (v2 §10 kept).

### §6.5 H3 — park until command
JOURNAL → `act_receipt{phase:hold, summary{…}, hold:{until:null}}` → wait. Execution requires
`command{kind:grant, corr:act_id}`. **Grant validity:** (a) references a journaled act — a grant can never
pre-authorize a not-yet-journaled effect (`effect_id` is already fixed; kills grant-then-mutate-args);
(b) unexpired (`ttl` default 24h; expiry ⇒ `exec/refused/grant_lapsed` — §3.1 phase law); (c) **single-use**
(consumed by exactly one effect-registry hold→exec transition, recorded with the grant's `cmd_id`). Statics
re-run at consumption. Queue surfaces (`hc queue`, grant text rendered from hold-receipt `summary{}` alone)
are seat 08's; consumption semantics are this contract's. Grant co-sign cryptography: Stage-1b ed25519,
operator key off-box — unattended H3 impossible by construction [SECURITY-SEAM §12.3].

## §7 · Scoped exactly-once (F10 extended through the fork dimension)

### §7.1 Key shapes

| `effect_scope` | key | fires again on fork? | canonical uses |
|---|---|---|---|
| `instance` | `(claim_id, step_id)` | yes, per branch — by design | checkpoints, self-posts, per-branch compute |
| `lineage` | `(lineage_root, effect_id)` | **no — set-once across the fork tree** | H1+ world acts: sends, payments, deliveries |
| `slot` | `(routine_id, scheduled_slot)` | n/a — one fire per scheduled slot | unattended routines; missed slot is NOT pending (`catchup: skip | once`) |

`lineage_root` comes from the nucleus **genesis record** (seat 02); a fork child's genesis carries
`forked_from{claim, seq, head_hash}`. `effect_id = sha256(capability_ref ‖ tool_version ‖ JCS(sig_args))`,
JCS = RFC 8785, over **effect-significant args only** (marked per-field in the profile): volatile args can
neither break dedup (spurious uniqueness) nor evade it (cosmetic-difference duplicates). Concurrent fork
siblings compute the same key.

### §7.2 Effect registry & lineage index — two Conductor folds
- `lineage(claim_id → root_id, parent_id, forked_at_seq)`: folded from fork/genesis records posted D-gold.
- `effects(scope_key → {act_id, state: reserved|held|executed|settled, receipt_seq, lease, grant_cmd_id})`:
  folded from act/act_receipt/grant records; the live table is a serving copy, rebuilt from the log on start.

### §7.3 Reservation (step 3): atomic insert-if-absent
`conductor.effects.reserve(key, act_id)` — reserve-then-execute, never consult-then-act (FIX-2; TOCTOU
closed). Loser → `exec/refused/duplicate_effect` + `duplicate_of: <winner act_id>`; escrow released; the
losing sibling awaits the winner's corr and **shares its evidence** — dedup-and-share, not dedup-and-fail.
Reservations carry a lease TTL; orphans are swept.

### §7.4 Crash-window analysis (resume behavior per window)

| window | on disk at crash | resume behavior |
|---|---|---|
| W0 pre-escrow | nothing | re-attempt; same `effect_id` recomputed |
| W1 escrow→reserve | reservation only | escrow reconcile releases; registry untouched |
| W2 reserve→journal | registry `reserved`, no act record | lease TTL expires the orphan, OR the resumed actor re-attempts: same semantic act ⇒ same `effect_id` ⇒ same key ⇒ re-binds (new act_id, same key) |
| W3 journal→execute | fsync'd `action`, no outcome | `pending()` fires → reconciliation §8 → probe absent ⇒ `invalid` ⇒ retry same idem |
| **W3h journal→hold-receipt** | fsync'd `action`, no hold receipt | reconciliation step 0: intended-hold (H2/H3 statics) with no hold receipt ⇒ re-post hold receipt idempotently; countdown timestamps come from the Medium, never the crashed process |
| W4 execute→receipt | effect happened, no receipt | reconciliation → probe finds effect → receipt `ok` minted by `resolver:reconcile`. **Irreducible** (you cannot fsync a receipt before the world answers) — exactly why probes are mandatory at H1+ |
| W5 receipt→settle | receipted, unsettled | settlement fold picks it up (§4.3) |

## §8 · The `unknown` reconciliation procedure (never blind-retry)

Trigger: resume finds `nucleus.pending()` non-empty (an `action` without `outcome` — live mechanism
`cell/nucleus.py:106-116`; **v5 nucleus contract: `pending() → list`, per-act reconciliation** — the live
single-dict return is a single-flight assumption a grounded run breaks; migration §13), or an exec receipt
lands `unknown`.

0. **Hold check (NEW).** If a live `act_receipt{phase:hold}` exists for this corr (unexpired, not escalated):
   the act is legitimately HELD — resume the countdown from the log; do NOT probe, park, or retry.
1. **Do not re-execute.** Look up the profile's **reconcile probe** — an H0 read that decides whether the
   effect landed. **Probe admission predicate (NEW, structural):** `probe.harm_floor == H0` ∧ probe egress ⊆
   the role's allowlist, both checked at PROFILE ADMISSION (a mutating probe recurses the in-doubt problem;
   read-only turtles all the way down). **A profile without an admissible probe is inadmissible at H1+.**
2. Run the probe (a full H0 act: gated, receipted, metered).
3. effect-found → `act_receipt{exec, ok, graded_by: resolver:reconcile}` with probe evidence → settlement.
   effect-provably-absent → `invalid` → retry legal, same `idem`, `attempt+1`.
   undeterminable → stays `unknown`; if profile `retry_safe: provider_idem` → safe re-send (the provider's
   idempotency key IS the probe); else **park to operator** (`_ops` task). The fabric never guesses.
4. **Money twin (econ, settled):** an in-doubt provider call is an act-shaped unknown — `escrow.reconcile()`
   commits at worst-case under `outcome=unknown`; the provider usage-API query is its probe; `res:sync` folds
   to zero on resume, `res:durable` (batch legs) folds still-held until a receipted reconciliation act lands;
   `res:lease` (§10.4) folds still-held and settles from the cell's own drawdown receipts. One law — money
   and effects.

## §9 · The grounding dial & L-NO-NAKED-CLAIMS made arithmetic

### §9.1 The dial — three registered positions (v2 §5 names; v3's arithmetic)

| mode | default binding (intake-written, task-class-keyed) | grading effect |
|---|---|---|
| `none` | executable oracle (tests/checker run the artifact) | citations add nothing; the execution receipt IS the warrant |
| `sampled` | judged + closed-world | evidence demanded on a pre-registered fraction of material claims (GX-2's affordability fallback); coverage arithmetic over the sampled set |
| `required` | judged + **acquisitive** (what v2 called "cite-or-abstain"; the enum value is `required` — the old name is NOT a legal `grounding_mode`) | every material claim carries evidence or an honest `ungrounded:true`/ABSTAIN label; an unreferenced, unlabeled material claim ⇒ **gate** |

Set at intake, never by cells: the run manifest's `grounding{mode, sample_fraction?, max_age, quote_max,
source_diversity?}` block is written by the intake classifier (seat 04) at the same task-class level as
refuse-defaults (L2 axes: verification × information); "cite sources" in the utterance forces `required`.
A role may RAISE its floor, never lower it. (v3's `optional`/`cite_or_abstain` modes dissolve into
`sampled`/`required` respectively — mode names restored to v2's three; GROUND-2 escape: if `required` loses
to an honest declared-mode baseline on judged non-factual classes, the class default demotes to `sampled` —
falsifier-decided, PART D row 8.)

### §9.2 The honesty asymmetry (pre-registered constants, per oracle generation)
`abstain_floor` = the generation's registered value — home: **oracle.md §3** (v2's pre-registered 0.3;
R20 — this file carries a pointer, never a second copy) · `C_unwarranted = 0.4`. `S` = panel content
score; `c` = grounded-material-claim coverage (claims honestly marked `ungrounded:true` count as
honestly-uncovered):

```
fabrication detected     → outcome=gate, score=0, stain minted        (below everything, always)
honest ABSTAIN(reason)   → score = the generation's registered abstain_floor (oracle.md §3)
ungrounded / partial     → score = min(S, C_unwarranted + (1 − C_unwarranted)·c)
fully grounded           → score = S
INVARIANT: 0 = score(fabricated) < abstain_floor ≤ cap(honest ungrounded) < 1 = cap(grounded)
```

Lying about evidence is ALWAYS strictly worse than admitting its absence. Fabrication = digest mismatch ∨
forged act-ref ∨ quote-not-in-source ∨ (sampled) non-entailing quote. **Stain registry** = a fold over gate
receipts: `(claim/role, kind:fabrication, act_ref, at)`; consequences: ρ→1.0 for the role until 3 clean runs;
second stain quarantines the role from `required` runs pending operator review.

### §9.3 Who grades what (settled with seat 05)
The **grounding validator** is deterministic Conductor code (ref resolution, digest sample, act-ref
provenance, quote presence, coverage, **domains-per-claim**) emitting a per-submission gate row into the
StackReceipt. Row shape **pinned by seat 05 (#695), adopted verbatim** so seat 04's certificate block reads one
shape: `{name:"grounding", kind:"grounding", outcome, gate:true, evidence:{resolved, digest_ok, witness_ok,
entailment:{sampled, passed}, coverage, citation_precision_at_k, domains_per_claim:{min, median},
trust_floor_met}}`. `witness_ok` = the act-ref-provenance check (the poster holds the receipt); `trust_floor_met`
consumes seat 02/10's terminal trust tags (a low-trust terminal never *silently* gates — absent a registered
floor the gate passes and the certificate reports the trust classes). Quote-ENTAILMENT is the judge panel's
(k=2, coordinator-sampled — the `entailment` sub-row).
The HC-V4→GROUND-1 seeded-fabrication fixtures double as panel control probes (badness verified by the
non-panel validator — admissible under seat 05's control law).

### §9.4 Fetch-to-cite + source diversity (v2 §5 restored)
A search snippet is `role:context`, NEVER `supports` — a material claim requires a fetched, digest-pinned
artifact (the F5/Entry-33 drift killer). Grounding certifies **provenance, never source truth**: a fetched
page can be adversarial, so `grounding.source_diversity: n` MAY require support from ≥n independent
registrable domains for load-bearing claims; cross-source disagreement is a probe signal (`oracle_gap`); the
certificate reports the domain count per material claim ("grounded in 1 domain" is an honest sentence).

## §10 · ANNEX A — the tool-profile registry (a SECTION of this contract, not a new artifact)

### §10.1 The seam
The membrane executor is an **MCP client**; first-class tools are builtin in-process adapters presenting the
same call shape (adopt semantics, refuse dependencies). **Pin: MCP spec 2025-11-25 (latest stable).** The
2026-07-28 revision is a live RC as of this writing (stateless core; sessions removed; extensions framework;
12-month deprecation policy) — final lands 2026-07-28; migrate at the first MAINTENANCE window after GA;
statelessness suits this executor (every call self-contained; we never used sessions/sampling/roots).
Rented adapters (connector gateways, cloud browsers, agent inboxes) mount as `exec: mcp://<server>` rows
behind the same gate, receipts, metering — zero new schema. **No provider-side tool execution** (server-side
search/code-interpreter bypasses egress, provenance, metering, receipts). Tool results enter frames as blocks
carrying seat 10's **`tool` trust tag** (the enum is `{operator, receipted, tool, external}`; control flow
derives only from `operator` — a `tool` block can be quoted and reasoned over, never obeyed) with the
`act://` ref attached — structural per-block provenance assigned at frame-assembly time, never string-wrap
(which a forged closing fence defeats). The tag is transport-assigned and non-suppliable; the executor
guarantees every tool result carries its receipt ref.

### §10.2 Profile fields (normative shape)

```yaml
<capability_ref>:
  version: 1                      # profile MAJOR; pinned on acts, echoed on receipts
  harm_floor: H0                  # fabric data; cells never declare their own floor
  exec: builtin                   # builtin | mcp://<server>
  args_schema: { … }              # JSON-Schema; validated at gate step b
  effect_significant: [ … ]       # arg names hashed into effect_id (§7.1)
  h0_certification: { … }         # adapters only: the §6.2 admission predicate evidence
  credential_carrier: header      # none | header | query | body — where the ADAPTER key rides.
                                  # LAW: credentials are fabric-held, executor-injected, never in args,
                                  # never in frames/ledgers/Medium. The executor MUST scrub the credential
                                  # component from receipt provenance before post (provenance.scrubbed=true);
                                  # query/body-carrier endpoints REQUIRE scrub verification at admission.
                                  # [SECURITY-SEAM §12.1]
  exfil_channel: url              # none | url | body | headers — can cell-authored bytes reach the wire?
                                  # Feeds the trifecta booleans; url ⇒ external_comms derives from egress-
                                  # allowlist breadth (seat 10's derivation rule).
  trifecta:                       # seat-10 Rule-of-Two inputs (semantics theirs; fields live here)
    private_data: false           #   can this tool reach non-public data?
    untrusted_content: true       #   does it return world-authored content?
    external_comms: derived       #   true | false | derived (from exfil_channel × egress)
  reconcile: { kind: …, args: … } # H1+: MANDATORY H0 probe (admission predicate §8.1); H0: null
  retry_safe: null                # provider_idem | null
  expectation_default: { … }      # optional auto-suppliable losable check
  pricing: pricebook:tool.<ref>   # per-call/per-second/per-unit lane (seat 07); as_of freshness law;
                                  # no computable worst-case ⇒ unreservable ⇒ refused
  isolation_required: class-0     # class-3 for candidate code, ALWAYS (no degraded fallback)
  grading_note: …                 # free text consumed by §9 docs
```

### §10.3 The first-class five (normative rows; full YAML in the repo annex)

| ref | floor | key facts |
|---|---|---|
| `web.search` | H0 (certified) | adapter-composed; creds adapter-held read-scoped; `credential_carrier` per provider (Brave: header `X-Subscription-Token` — verified 2026-07); results are POINTERS — snippets cite as context only; `trifecta: {false, true, false}` (endpoint pinned) |
| `web.fetch` | H0 (structural) | GET/HEAD, no body, no cell credentials, `max_bytes` 2 MiB, `timeout_s` 30, static render; `exfil_channel: url` ⇒ `external_comms: derived`; JS-rendering browsers are rented adapters behind the same seam |
| `fs.read` | H0 | volumes: workspace + artifact-store ONLY; never foreign nuclei, never the oracle dir (HC-7) |
| `code.run@sandbox` | H1 | `net: "none"` is the contract, not a knob; `isolation_required: class-3` ALWAYS; effects escape only via `/out` artifacts; probe = `file_exists` **with digest** on the runner-sealed `/out/manifest.json` (seat 09 seals before any probe reads); expectation_default auto-supplied |
| `deliver.outbox` | H1 | delivery IS an act (kernel T8); `effect_scope_default: lineage`; probe = manifest digest; DELIVER-1's mechanism |

### §10.4 Metering & leases (settled with seat 07, #679/#690)
Every act reserves `cost_est.usd_worst` and commits actuals under `purpose: tool`. **High-rate H0 tool lanes
use `econ.lease(lane, ceiling, ttl) → lease_id`**: a fleet-escrow micro-reservation (durability `res:lease`,
scope cell×lane, quantum default $0.05 or 20 calls) drawn down locally — each H0 receipt IS the drawdown log;
renewal reconciles actuals and re-reserves; crash folds the lease still-held and `reconcile()` settles from
the cell's own receipts. Honest tradeoff (printed, falsifier-checked): zero-overshoot holds at fleet scope;
within-lease the cell self-meters — worst overshoot = one quantum per cell. H1+ acts stay per-call reserve
(fsync ≪ effect latency). Per-provider concurrency caps apply to tool endpoints exactly as to cognition (F2).
Wire realization of the lease was CLOSED by R11 as conductor-internal (the conductor's own escrow ledger;
no Medium traffic); this contract needs only the signature + drawdown semantics.

### §10.5 Result → ledger flow (five hops, all mechanical)
executor stores raw bytes content-addressed → `output_hash` → `act_receipt` posted (durability per §3.2) →
`nucleus.append(kind=percept, refs=[receipt])` → frame carries the trust-tagged block + `act://` ref → the
cell's submission copies refs it ACTUALLY holds (the 100% provenance check closes the loop).

## §11 · Fold-law conformance declaration (A13; input filters, compaction-closed)

| fold (owner) | input filter (types; all D-gold) |
|---|---|
| effect registry (Conductor) | `act`(H1+), `act_receipt`(H1+ all phases), `command{kind:grant\|cancel}` |
| lineage index (Conductor) | fork/genesis records: `presence{phase:genesis}` · `presence{phase:spawned, forked_from}` (carrier spelled by wire.md §3.1/R19; fork-provenance presence rows ride D-gold) |
| settlement queue (Conductor) | `act`(H1+ w/ expectation), `act_receipt{exec ok}`, `act_receipt{settle}` |
| wager ledger (Conductor) | `act_receipt{phase:settle}` |
| stain registry (Conductor) | gate receipts (grounding validator rows, StackReceipt kinds) |
| acquired-trifecta (Membrane/Conductor) | `act_receipt{exec ok}` per claim since spawn/quarantine-flush |
| retention promotion (Conductor) | `verdict.evidence[]` closures |

H0 records are D-chatter and appear in NO constitutional fold above — H0 decay can never open a fold hole
(L-FOLD-CLOSURE conformance, seat 03). All folds rebuild from the log on start; serving copies are renders.

## §12 · [SECURITY-SEAM] register — what this plane NEEDS from seat 10 (the inverse of v3's SCOPED-OUT)

1. **[SECURITY-SEAM: adapter-secret custody + scrub]** Custody of adapter keys (substrate secret store;
   never image-baked; never in frames/ledger/Medium — seat 09's no-secretRef-in-sandbox rail). I own:
   `credential_carrier` declaration, executor-side scrub of receipt provenance, `provenance.scrubbed` flag,
   admission-time scrub verification. Seat 10 owns: the pattern set (with seat 02's envelope-level
   `redactions[]`), planted-key drill SEC-8 (tool-output leg already covers my §10.5 flow).
2. **[SECURITY-SEAM: egress enforcement]** I own the gate predicate (step f) + per-profile pinned endpoints +
   allowlist-as-operator-signed-facts. Seat 10/09 own NetworkPolicy realization + the class-3 no-egress rail.
3. **[SECURITY-SEAM: H3 grant signing]** Grant/cancel co-sign: Stage-1b ed25519, operator key OFF-BOX ⇒
   unattended H3 impossible by construction (10-T8). I own consumption semantics (§6.5); 10 owns key law;
   08 needs the Stage-0/1a interim authn ruling (loopback-tty possession) — I consume whatever stage_of() says.
4. **[SECURITY-SEAM: act_receipt non-mintability]** Type-ACL row: `act_receipt` ← executor principals only;
   VOID-AT-FOLD for smuggled receipts (seat 03 C11); Stage-1b signature on `act_receipt` when the ratchet
   fires (10's ratchet law). Until Stage-1a, convention red-teamed by HC-7-v2 attempt 8.
5. **[SECURITY-SEAM: trifecta derivation]** Fields + acquired-fold are mine (§6.1h, §10.2); boolean semantics,
   waiver policy precedence, and the `external_comms` derivation from exfil_channel × egress are seat 10's.
   Taint propagation ("outputs of an untrusted_content=true cell are adversarial-equivalent") keys on my fold;
   sandbox-class consequence is seat 09's.
6. **[SECURITY-SEAM: frame trust-tags]** Tool results enter frames as DATA-tagged blocks with `act://` refs
   (§10.1); tag taxonomy + assembly law are seat 10/02's; I guarantee every tool result carries its receipt ref.

## §13 · Migration from live v1 (the honest delta)

| live shape | v5 shape | note |
|---|---|---|
| no act/act_receipt in `MessageType` (`types.py:32-44`) | two new registry types | wire MAJOR rides the spine-adoption epoch (seat 03/01) |
| `membrane.py` = `is_directive` + `as_data` (18 lines) | the §6 gate + executor | greenfield; `as_data` string-wrap REPLACED by trust-tagged frame blocks (10-T1) |
| `ask()` idem guard exists; `produce()` lacks it (`runtime.py:41-43` vs `83-101`, F17) | one-verb-executor: ALL verbs through §6.0 | the guard becomes structural, not per-method |
| `nucleus.pending()` returns first pending action (`nucleus.py:106-116`) | `pending() → list`; per-act reconciliation §8 | single-flight assumption breaks under parallel H0 fetches (C11) |
| `Role.tools`, `Role.harm_ceiling` exist (`types.py:99,102`) | consumed unchanged | `role.md` gains egress allowlist + max_wager_horizon + standing_access (seat 02) |
| `Governor` in-process reserve/commit (`governor.py`) | `econ.reserve/lease/commit/reconcile` (seat 07) | escrow home per the 01/07 ruling |
| no artifact store | content-addressed store (path derivable from sha256) | serves evidence artifacts AND seat 09's behavior artifacts |
| `HarmClass` enum exists (`types.py:62-66`) | unchanged | comments updated to v5 semantics |

**Bootstrap order:** GROUND-0 needs only {gate statics, H0 profiles, receipts, evidence validator, dial} —
PART D. Old ledgers: acts absent entirely; no back-fill; the first v5 run starts the act plane clean.

