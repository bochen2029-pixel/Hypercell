# CONTRACT: command — the CommandEnvelope, the receipt chain, the ingress

**Version:** `command/5.1.0` · **Status:** v5 RATIFIED-DRAFT · **Date:** 2026-07-16 · rev 2026-07-25 (P3 resolution)
**Pairing (_TEMPLATE-HEADER.md H2):** `command` ↔ the **Conductor** (noun 7) — the wire form of verb #6.
**Operator boundary (R5):** strict-both — CommandEnvelope `params` and routine specs validate
STRICT: an unknown field is a loud error, never an ignored extra.
**Schema mirror:** `contracts/schemas/command.schema.json` — generated lockstep twin, same commit
(kernel T2; §8).
**Emit/read (kernel R1–R6):** emitters mint **strictly** (registry verbs, schema-valid fields);
readers are **liberal on fields** (unknown fields MUST round-trip unmodified, MUST NOT be dropped)
and **closed on verbs** (unknown verb ⇒ `refused(invalid)` naming the registry). Defaults in §1.3
are **frozen for this MAJOR**: a reader of `command/5.x` MUST apply exactly these defaults to absent
fields, forever, regardless of later MINORs.
**Unknown-fallback (R3):** unknown `verb` → refuse-typed; unknown field → preserve; unknown
`refused_class`/`outcome`/`state` value read from a NEWER minor → render verbatim, treat as
non-terminal unless phase says `result`.
**Transport:** a CommandEnvelope is the `body` of a Medium message `type=command` posted to the
`_ops` culture (wire.md owns the outer envelope; wire.md's registry row for `command` cites THIS file
for the body schema — schema-by-reference, defined once). Bodies > the wire's inline cap ride the
wire's artifact pointer unchanged.
**Durability/retention (wire.md classes):** `command` and `cmd_receipt{phase:ack|result}` are
**D-gold, R-forever** (the provenance skeleton's spine); `cmd_receipt{phase:progress}` is
**D-chatter, R-decay**.
**Registry note:** `cmd_receipt` is a payload-type registry row in wire.md — **the 17th type, RULED
in-room and coordinator-countersigned** (#688 evidence → #692 kernel-seat ruling → R1, 17/17):
conductor-only ACL; the only type with phase-dependent durability; 3-phase lifecycle over
`cmd_id`; overloading `receipt{kind}` would make certificate and queue folds body-parse-dependent
(violates type-expressible fold closure) and breaks live oracle-receipt queries. The ruling also
subsumes kernel's proposed `progress{corr}` streaming type: **operator-facing streaming RIDES
`cmd_receipt{phase:progress}`**; run-internal progress stays `status` (DATA). The wire envelope's
`corr` column carries `cmd_id` on every cmd_receipt (join-free folds); the body repeats it.
**Migration from live v1:** §9. **Falsifiers:** SUR-1..10, MIG-SUR (constitution §15).

---

## §1 · The CommandEnvelope

Every **mutating** operator intent from every surface — CLI, talk, HTTP, MCP, PWA, routine — is one
schema-validated CommandEnvelope through one ingress. Reads are NEVER commands (§7).

### 1.1 Schema (normative)

```jsonc
// command/5.0.0 — the wire form of an operator intent
{
  "cmd_id": "01J9Y6ZQ8K3W...",         // REQUIRED. Globally-unique, <=64 chars, SURFACE-minted.
                                        //   Interactive surfaces SHOULD mint ULIDs (sortable).
                                        //   Routine executors MUST mint deterministically:
                                        //   "rt:<routine_id>:<slot>"   (§6.2 — slot exactly-once free).
                                        //   Roles: identity-dedup key (§4 step 3) + receipt-chain key
                                        //   + the Stage-1b signing nonce [SECURITY-SEAM below].
  "issuer": "operator",                 // REQUIRED. "operator" | "routine/<id>" | "conductor".
                                        //   Authentication of the STRING is identity-firewall.md's;
                                        //   the queue's unattended ceiling (§6.4) keys on it.
  "surface": "talk",                    // REQUIRED. "cli"|"talk"|"http"|"mcp"|"pwa"|"routine"|"test".
  "session": "talk/9f2c",               // REQUIRED. Surface-session id; scopes supersede (§5.2) and
                                        //   conversation state. Routine sessions = "routine/<id>".
  "verb": "run",                        // REQUIRED. Closed registry (§2).
  "params": { },                        // REQUIRED. Per-verb typed object (§2). Strict-mint.
  "params_hash": "sha256:...",          // REQUIRED. Over RFC-8785 (JCS) canonical form of `params`.
                                        //   The Conductor RECOMPUTES; mismatch => refused(invalid).
  "utterance": "spin up 6 agents ...",  // REQUIRED iff an NL layer produced params (talk; MCP tools
                                        //   that accept utterance): the raw operator text — provenance
                                        //   for the Entry-30 cross-check (§2.1 of ARCH §10; extractor
                                        //   spec below). Absent for typed surfaces.
  "parse": {                            // Present iff an NL router produced params (audit of parsing).
    "router_claim": "talk/9f2c/0",      //   the d0 router CELL that parsed it (F15: metered, ledgered)
    "model": "deepseek-chat",
    "extractor": "builtin@5.0.0",       //   version of the deterministic extractor that ran
    "extracted": {"n": 6},              //   scalars the extractor found in the utterance
    "injected": ["n"],                  //   scalars the extractor FORCED over router omission (rule 1)
    "inferred": ["rounds"],             //   scalars the router supplied with no utterance evidence
    "defaults_applied": ["provider"]    //   scalars filled from frozen defaults — each narrated in ack
  },
  "supersedes": null,                   // OPTIONAL. A cmd_id from the SAME (issuer, session) to
                                        //   cancel-replace while still QUEUED (§5.2).
  "ttl_s": 600,                         // Stale-refusal window; default 600; per-verb override §1.3.
  "budget": {"usd_cap": 2.0},           // OPTIONAL overrides; CLAMPED to fleet caps by the governor
                                        //   (pricebook.md); never raises a cap, only lowers.
  "dry_run": false,                     // Parse + plan + intake-class + econ quote + narrate; execute
                                        //   NOTHING; result carries the plan + quote.
  "reply": {"detail": "summary"},       // Delivery hint: "summary" | "full". Receipts land on _ops
                                        //   regardless — reply shapes rendering, never truth.
  "contracts": {"command": "5.0.0",     // The surface's census expectation (kernel G3/R-rules).
                "wire": "5.0.0"},       //   MAJOR mismatch => refused(version) naming both versions.
  "ts_surface": "2026-07-16T04:40:00Z", // Informational; the AUTHORITATIVE ts is the Medium's at post.
  "auth": null                          // OPTIONAL Stage-1b block: {"alg":"ed25519","key_id":"...",
                                        //   "sig":"base64(sign(leaf))"} — field semantics, key custody,
                                        //   and the verify() predicate are identity-firewall.md's
                                        //   (schema-by-reference). Reader rule: absent => an unsigned
                                        //   Stage-0/1a envelope (legal below the Stage-1b trigger).
}
```

**[SECURITY-SEAM: envelope authentication → seat 10].** This contract needs from
`identity-firewall.md`: (a) the `auth` block schema + `verify(env) → ok | fail` and the signing
input (the wire leaf, sig excluded, per 03's reserved-column placement); (b) the **Stage-1b trigger**
statement (second independent principal, or an untrusted relay) — below the trigger, absent `auth` is
legal and the ingress MUST NOT refuse it; at-or-above, **the RATCHET law** (10's #684, kernel-confirmed
#692) applies: lower-stage validation is no longer SUFFICIENT for the types the stage protects —
inbound `issuer=operator` envelopes without valid `auth` ⇒ `refused(auth)`, and a stripped signature
can never demote a privileged record to "Stage-0 valid" for narration or execution; (c) `cmd_id`
blessed as the signature nonce (replay = identity-dedup, §4 step 3 — a replayed signed envelope is
answered with the EXISTING chain, executing nothing); (d) surface authn floors per surface class
(http/pwa bearer; mcp stdio = process possession; cli/talk tty = box possession at Stage 0/1a);
(e) the day-1 H3 grant path below the trigger (loopback-tty possession = operator authn — requested
#688); (f) `current_stage()` = a fold over `command{kind:stage_bump}` records + `stage_of(event)` —
the stage oracle this contract's AUTH step and the constitution's honesty rule both call (#692).

### 1.2 Field invariants

1. `(cmd_id)` is globally unique forever; the ingress treats a duplicate as replay, never re-execution.
2. `params_hash` binds params at mint time; any mutation in flight is detectable (`refused(invalid)`).
3. `utterance`+`parse` make every NL-parsed scalar auditable: a stated count silently defaulted is
   grep-able in the log, not anecdotal (F27's bar).
4. `issuer` ∈ {"operator", "routine/*", "conductor"}; `issuer=conductor` is legal ONLY for
   fabric-internal maintenance envelopes the Conductor mints for itself (compaction schedules);
   it MUST NOT carry `grant`/`deny` (§6.4's ceiling applies to every non-operator issuer).
5. `ts_surface` never orders anything; ordering is the Medium's `seq` (wire.md).

### 1.3 Frozen defaults (MAJOR 5)

| field | default | field | default |
|---|---|---|---|
| `ttl_s` | 600 (`stop`,`grant`,`deny`: 3600) | `reply.detail` | "summary" |
| `dry_run` | false | `budget` | absent ⇒ fleet caps |
| `supersedes`/`auth`/`parse` | absent | W_coalesce (§5.1) | 120 s (`run`,`drive` only) |
| run params | run.md's frozen defaults table | progress min-interval | 2 s per cmd |

---

## §2 · The verb registry (CLOSED)

Commands are writes. The registry is closed: an unknown verb is `refused(invalid)` naming this table.
Verbs compile to the seven constitutional verbs; no verb here mints new grammar (kernel V1–V5).

| verb | params (typed object) | effect |
|---|---|---|
| `run` | an inline **run-manifest fragment per run.md** (`topology, goal, n?, rounds?, oracle?, judge?, target?, diversify?, lanes?, manifest_ref?`) — the field space is run.md's §manifest, cited not duplicated; the verb-executor compiles fragment→manifest under run.md's frozen defaults | convene a Culture; `hc apply -f` compiles a manifest file to this verb |
| `drive` | `{goal, oracle, arms?, max_steps?, usd_cap?, target?}` | the self-driving loop — **a policy-row preset over the ONE driver** (run.md topology unification; prior 4); no second code path exists |
| `ask` | `{prompt, provider?, model?, role?, claim?, idem?}` | one cell answers. THE degeneracy law's subject: adds exactly 2 `_ops` appends + 1 queue op over a bare cell ask (constitution §10 law 5) |
| `resume` | `{run?: id, claim?: id}` | culture-level or cell-level resume |
| `pause` | `{run}` | park — run-engine's graceful crash; resumable |
| `stop` | `{run \| cmd \| "all", force?: bool}` | terminal; converge-what-you-have; MUST NOT interrupt an act between journal and effect (act.md) |
| `fire` | `{routine, vars?: {k: v}}` | trigger a stored routine; `vars` filtered by its whitelist (§6.1) |
| `grant` / `deny` | `{act_id, why?}` | resolve a parked H2/H3 act. Consumption semantics (single-use, TTL, lapse outcome, postdating, `cancel` legality) are **act.md's — cited, never duplicated here** |
| `cancel` | `{act_id, why?}` | withdraw a still-held act; legality window is act.md's |
| `routine.set` | `{routine_id, spec?, enabled?}` | create/update/enable/disable a routine (§6) |
| `provider.set` / `config.set` | `{key, value}` | fleet configuration |
| `maintain` | `{op: compact\|verify\|backup, scope}` | operator-triggered maintenance; internals are substrate/medium seats' |

**The `command.kind` registry (THE one home — wire.md §3.1 delegates here; no copy exists).** The
wire `command` TYPE carries every kind below. The non-envelope kinds are NOT operator envelopes and
NOT in this verb registry; they share the `command` type's ACL and authority gate, never the §1
schema. **kind-addition = a `command.md` MINOR, zero wire-registry impact** (kernel ruling #692).
Operator `grant`/`deny`/`cancel` envelopes ARE the `command{kind:grant|cancel}` records the act
plane consumes — one record, two readers.

| kind | class | semantics |
|---|---|---|
| `directive` | envelope | the ingress-posted CommandEnvelope itself (§4 step 5) — the default kind of every operator intent |
| `grant` / `cancel` | envelope + act plane | one record, two readers: the operator's grant/deny/cancel envelope IS the record act.md consumes |
| `contract_bump` | governance (kernel) | census epoch record inside the chain (_TEMPLATE-HEADER.md H5) |
| `migration_epoch` | governance (kernel) | the MAJOR-epoch barrier (constitution §18) |
| `stage_bump` | governance (identity-firewall.md) | input to the `current_stage()` fold (§1.1 seam, #692) |
| `key_rotate` | governance (identity-firewall.md) | key-custody rotation |
| `adjudication` | governance (R19) | the operator's disjoint-authority decision entering the trust plane — its bar-effect lands as `oracle_gen{kind:operator_audit}`; the pending work it answers rides `task` |
| `errata` | governance | operator-signed errata record (constitution §5.5; trust-plane twin `oracle_gen{kind:errata}`) |
| `flip` / `grant` / `revoke` / `park` / `resume` | fleet decision (R22) | decision records — conductor-only, D-gold, R-forever, posted to the `_fleet` culture (wire.md §2); `class_default_flip` rides `command{kind:flip, class, level, evidence[]}` (run.md §R7.3/§R9). Culture disambiguates the reader: the act-plane `grant` above posts to `_ops`, the fleet-decision `grant` to `_fleet` |
| `oracle.seal` / `oracle.errata` / `oracle.control` / `oracle.adjudicate` / `null.pin` / `crucible.resume` | operator statute (s6-10) | the operator-statute carriers SEC-1 (oracle.md §15) cross-refs: generation sealing, trust-plane errata, control/golden registration, adjudication entry, null pins, crucible resumes. **Each carries a Stage-1b operator-signature slot** (the `auth` block; identity-firewall.md): at/above the Stage-1b trigger an unsigned statute is `refused(auth)`. They enter through the ONE ingress like every operator intent — the surface (e.g. `hc oracle control add --golden`) compiles the statute to its kind-carrying record |

### 2.1 The degeneracy arithmetic (the canonical line-item; constitution §16 cites THIS box)

Stated once, organ-labeled, so the coherence skeptic sees one arithmetic (room #687/#691/#694):

| `hc ask` costs | count | organ / bar |
|---|---|---|
| metered LLM calls | **1** | the cell's own call (econ meters it) |
| Medium appends | **2** — `_ops` `command` + `cmd_receipt{result}` (cost{} rides the result) | **THE §16 degeneracy bar counts these** (SUR/law 5) |
| ack rows | **0** (collapsed into result for the degenerate path — §3's collapse clause) | the DEGEN-1 bar's substrate |
| nucleus records | 2 — action + outcome, cell-side | NUC-9's bar; the resume substrate (F10) — the cell working, not ceremony |
| plane-side LLM tokens | **0** | law 5's hard zero |
| econ Medium appends | 0 — quote/reserve/commit are conductor-internal ledger records | econ ruling #694: print 2, not 3 |
| queue ops | 1 in-memory | a fold-read, not ceremony |

If the envelope machinery ever costs a simple ask more than these 2 Medium appends, §10 has failed.

**[SECURITY-SEAM: verb ceilings → seat 10].** `grant`/`deny` at H3 require the operator-signed path
once Stage-1b is live (the off-box operator key makes a routine-issued H3 grant *physically
impossible*, not policy-refused — 10-T8). Until the trigger: loopback-tty possession, per the §1.1
seam ask.

---

## §3 · The receipt chain — `cmd_receipt`

Payload type `cmd_receipt` (wire registry row; **conductor-only ACL** — same non-mintability class as
`receipt`/`verdict`; smuggled instances are VOID-AT-FOLD per wire.md C11). Every accepted envelope —
including every refusal — gets a chain keyed by `cmd_id`: `ack → progress* → result`.

**The degenerate collapse (the arithmetic's load-bearing clause).** For `ask` (and any verb whose
dispatch completes synchronously within the ack window) the chain collapses — the terminal
`cmd_receipt{phase:result}` doubles as the ack; no separate `cmd_receipt{phase:ack}` row is posted.
The §2.1 arithmetic counts this collapsed chain (2 Medium appends).

```jsonc
// type: cmd_receipt — Conductor -> _ops. NON-MINTABLE by cells or surfaces.
{ "cmd_id": "01J9Y...",
  "phase": "ack" | "progress" | "result",

  // phase=ack (D-gold): confirmation-by-narration, emitted BEFORE dispatch
  "ack": { "understood": "tournament n=6 rounds=3 judge-panel",   // normalized one-line summary
           "run_id": "r7",                    // pre-minted for run/drive: stop/watch work from second 0
           "defaults": ["rounds=3 (default)"],// every default named — F8's misroute-in-seconds
           "provenance": {"n": "stated", "rounds": "default",
                          "usd_cap": "stated"},                   // per-scalar, from parse block
           "coalesced_into": null,            // alias ack: the primary cmd_id (§5.1)
           "dry_run": false },

  // phase=progress (D-chatter; state-change-driven; min-interval 2s/cmd; event-time, never wallclock)
  "progress": { "state": "queued|spawned|round_open|scored|synthesizing|converging|input_required|parked|recovered",
                "round": 2, "detail": {"best": 0.86, "candidates": 12} },

  // phase=result (D-gold; terminal, EXACTLY ONCE per cmd_id; alias mirrors reference the primary)
  "result": { "outcome": "ok|failed|refused|superseded|expired",
                                       // ^ THE one outcome enum (this file is its home; wire.md §3.1
                                       //   delegates here). No `partial` — it has no producer.
              "refused_class": null,   // iff refused: invalid|version|auth|policy|budget|not_found
                                       //   |downgrade — the Stage-1b ratchet's stripped-signature
                                       //   refusal (identity-firewall.md B.6.3; SEC-3)
              "stopped_reason": null,  // iff ok: converged|target|budget|max_steps|operator
              "refs": ["medium://run-r7/412",
                       "file://outbox/r7/champion.md#sha256=9c1e..."],
              "summary": { /* the narration struct, §3.2 */ },
              "cost": {"usd_effective": 0.031} } }
                                       // ^ the canonical cost{} group (R16): members ⊆ {usd_effective,
                                       //   usd_reserved, sku, purpose, resv_id, pricebook_version};
                                       //   elision is lawful, wrong members are not. `wall_ms`/`tokens`
                                       //   are SIBLING receipt fields, never cost{} members. cmd_receipt
                                       //   is in R2's spend crossing set — the result's cost{} is
                                       //   authoritative for the whole command (W3a).
```

**States with cross-contract meaning:** `input_required` = an H2/H3 act parked (act.md) or a talk
clarifying question — maps 1:1 to the MCP task state; `parked` = fleet-scheduler park (run.md);
`recovered` is emitted at restart for every command the fold found non-terminal — the operator is
never left staring at post-crash silence (SUR-4b).

### 3.1 Chain laws

1. **Everything receipted, including refusals** — a policy refusal is a `result{outcome:refused}`,
   not an HTTP error. Only an envelope too malformed to carry a usable `cmd_id` gets a bare
   transport-level 400.
2. **Exactly one terminal result per cmd_id.** Alias chains (§5.1) get their result MIRRORED (body =
   pointer to the primary's result), one per alias.
3. **Multi-surface consistency is a fold:** any surface holding a cmd_id (or none) renders identical
   state by folding `_ops`. Bars: cross-surface visibility p95 ≤ 1 s Conductor-up (SUR-4a); a
   Conductor kill mid-run resumes the SAME chain to terminal with zero re-issue and zero duplicate
   runs (SUR-4b; the cmd_id↔run_id binding is recoverable from the ack AND from run_open).
4. The **verb-executor** (kernel G1: one place per verb for pre-gate/record/execute/post) is the ONLY
   minter of cmd_receipts — receipt shape cannot drift per call-site.

### 3.2 The narration struct (the honesty rule's substrate)

Assembled by **code** from `_ops` + run-culture reads ONLY; the ONLY source any surface narrates from.
Fields are first-class receipt/verdict/certificate fields (trust seat's StackReceipt — v3 seam #6,
carried), never prose:

```jsonc
{ "run_id": "r7", "verdict_type": "verified|synthesis|best_so_far|none",
  "oracle": "ipv4_check@g3#a1b2c3",
  "champion": {"cell": "c2", "arm": "a1", "score": 0.9286, "target": 1.0},
  "vs_null":  {"null_score": 0.85, "null_usd": 0.004,
               "margin_invoice": 0.078, "margin_production": 0.081},
               // DUAL-UNIT (R15, v2 L-NULL's restored anti-flattery guard): margin_invoice is the
               // PRIMARY operator-facing figure (the unit the operator pays); margin_production
               // rides alongside; a single unlabeled "margin" is REFUSED at schema validation.
  "cells": 6, "rounds_run": 3, "candidates": 12,
  "failures": [{"cell": "c3", "round": 2, "outcome": "invalid", "reason": "429 rate-limit"}],
  "contested": false, "residual": ["unicode digits unprobed"],
  "cost": {"usd_effective": 0.031}, "refs": ["file://.../outbox/r7/champion.md#sha256=..."] }
```

Rendering law (constitution §10): deterministic floor template per `verdict_type`; verdict prefix
code-chosen (`CHAMPION (oracle-verified, …)` / `SYNTHESIS (unverified fan-in of N cells)` /
`BEST-SO-FAR (not converged; budget-stopped)`); tri-state failures verbatim from `failures[]`; an
optional prettifier receives ONLY the struct and is numeral-containment-post-checked (the
prettifier, if enabled, is deterministic code or a metered d0 service cell — never un-metered
inline cognition; the Conductor never thinks); containment
failure ⇒ floor template + a `narration_downgrade` status appended to `_ops` (drift becomes a
counter). **A synthesis is never rendered as verified** — the lie would have to live in a schema
value (SUR-2).

---

## §4 · The ingress algorithm (normative; ONE function; every surface calls it)

```
ingress(env) -> ack_receipt:
 1. VALIDATE   schema (liberal-read); recompute params_hash over JCS(env.params);
               mismatch/malformed => refused(invalid) result receipt.
               (Only a body with no usable cmd_id gets a transport 400.)
 2. AUTH       [SECURITY-SEAM: seat 10 owns the predicate] verify(env) per identity-firewall.md:
               below the Stage-1b trigger, absent auth passes; at/above it, issuer=operator without
               valid auth => refused(auth). Surface-authn floors checked here too (bearer/tty/stdio).
 3. DEDUP      (identity): cmd_id already in _ops => return the EXISTING receipt chain (idempotent
               replay; zero extra state — the dedup index is a fold over _ops, R-forever). STOP.
 4. VERSION    census check (env.contracts vs fleet): MAJOR mismatch => post the command, then
               refused(version) naming both versions ("surface speaks command/5, fleet at command/6 —
               upgrade hc"). STOP.  (MIG-SUR.)
 5. POST       env to _ops as type=command, D-gold, fsync BEFORE any dispatch (F10: the command's
               existence survives a crash so receipts always have a referent). Refused and aliased
               envelopes are posted too — the fold-law demands the log hold every accepted envelope.
 6. SUPERSEDE  if env.supersedes names a cmd from the SAME (issuer, session) still QUEUED:
               predecessor gets result{outcome:superseded, by: cmd_id}; proceed. If predecessor is
               already RUNNING: proceed UNCHANGED; the ack carries "predecessor r7 already running —
               say 'stop r7' to abort" (an implicit kill is a harm decision; the operator says it).
 7. COALESCE   (equivalence — the F7 organ; fleet-class verbs run|drive only):
               key = (issuer, verb, params_hash). If a PRIMARY with the same key is QUEUED or RUNNING
               and age < W_coalesce (120 s default):
                 - env.cmd_id becomes an ALIAS (the alias record IS the ack receipt with
                   coalesced_into set — no second store; the alias map is a fold over acks);
                 - ack{coalesced_into: primary, run_id} — the duplicate issuer SEES the coalescing in
                   the same breath, NEVER silent;
                 - the primary's terminal result is MIRRORED to each alias cmd_id; progress is not
                   mirrored (surfaces follow the primary chain via coalesced_into).
               The lived storm (one prompt pasted to N sessions) = ONE run + N receipt chains +
               "N−1 duplicates coalesced" in hc top. STOP.
 8. TTL        now − ts_surface > ttl_s AT DISPATCH TIME => result{outcome: expired} (checked
               queue-side, not only at arrival: a command stuck behind a wedged queue can expire).
 9. GOVERN     pre-dispatch gates; each refusal a typed result receipt naming its override:
                 a. intake class — fleet-class verbs (`run`|`drive`) ONLY; every other verb skips
                    to 9b (waking the metered intake cell for an `ask` would break §2.1's 1-call
                    term). (run.md's classifier, keyed on the L0/L1/L2 task-class hierarchy):
                    refuse-to-swarm => refused(policy) + the null recommendation; --force-swarm
                    honored and receipted WITH the null warning (v2 §12 kept);
                 b. escrow reservation against the ONE fleet-scoped escrow (pricebook.md; closes
                    F16/F20): reservation failure => refused(budget) naming the gap;
                 c. unattended-issuer ceiling: issuer != operator MUST NOT carry grant/deny (§6.4);
                    its runs execute H0/H1 only — H2/H3 acts park (act.md).
10. ACK        pre-mint run_id for run/drive; emit ack{understood, run_id?, defaults[], provenance{}}
               — confirmation-by-narration (F8): misroutes surface in seconds; stop is one word.
               Collapsed chains (§3: dispatch completes synchronously within the ack window) merge
               steps 10–11: the terminal result doubles as the ack; no separate ack row is posted.
11. DISPATCH   hand to the verb-executor (kernel G1). Progress receipts: state-change-driven,
               min-interval 2 s per cmd. Terminal result exactly once (§3.1).
```

**Failure modes (named):** (a) coalesce false-positive — operator wants two identical runs: bounded
by W_coalesce + the narrated ack ("say 'again' to force a second run" ⇒ re-issue with a surface-minted
`params.nonce`, changing the hash); (b) coalesce false-negative — phrasing differences change the
hash: accepted; F7's storm is verbatim paste; (c) queue wedge — dispatcher dead ⇒ acks still emitted,
TTL expires stale commands, the read path (§7) stays served; (d) crash between steps 5 and 10 —
restart folds `_ops`, finds commands with no terminal receipt, re-enters at step 8; step-3 dedup makes
re-entry idempotent; `recovered` progress emitted (SUR-4b).

**The conductor lease (two-ingress exclusion).** Any process hosting the dispatcher MUST hold the
lease — `claim{resource:"conductor", lease_s}` on the Medium (log-derived CAS; **epoch = a fold over
the claim history** — there is no epoch field to lie in). No lease ⇒ embedded `hc` is READ-ONLY
(queries fine; commands refused naming the holder). Privileged posts carry the epoch; stale-epoch
posts are VOID-AT-FOLD.

---

## §5 · Coalesce & supersede reference

### 5.1 Two dedup mechanisms, two keys (the load-bearing split)

| mechanism | key | window | catches | answer |
|---|---|---|---|---|
| identity-dedup (§4 step 3) | `cmd_id` | forever (R-forever fold) | transport retries, MCP redelivery, routine re-fire after crash | the existing chain, replayed |
| equivalence-coalesce (§4 step 7) | `(issuer, verb, params_hash)` | W_coalesce (120 s; per-verb config) | the F7 storm: same intent, FRESH cmd_ids | one execution, N chains, alias acks |

A cmd_id-keyed dedup catches ZERO of the lived F7 storm (each paste minted a fresh cmd_id). The keys
never merge; the code paths never merge.

### 5.2 Supersede

`supersedes` is scoped to the SAME `(issuer, session)` — surface A cannot silently cancel surface
B's queued work; cross-session cancellation is an explicit `stop`. Superseding a RUNNING command
never auto-kills (§4 step 6).

---

## §6 · Routines — stored commands on triggers (NO second scheduler exists)

### 6.1 Schema

```yaml
# routine/5.0.0 — a stored CommandEnvelope + triggers
routine_id: nightly-digest
enabled: true
issuer: routine/nightly-digest        # NEVER "operator" — §6.4 ceilings key on this string
envelope:
  verb: run
  params: {topology: fanout, goal: "Digest of ${date}: ...", n: 4, lanes: [batch]}
subst_whitelist: [date, file]         # ${var} resolves ONLY from this list; anything else => refused
triggers:
  - {kind: cron,  spec: "0 6 * * *", catchup: skip}   # catchup: skip | once (default skip)
  - {kind: fire}                                       # POST /fire/<id>; bearer custody -> seat 10
  - {kind: watch, glob: "inbox/*.md", settle_s: 5, var: file}
unattended: {harm_ceiling: H1}        # H2/H3 acts PARK, never silently auto-approved
```

Routine specs are content-addressed at fire time (the fire record carries `spec_sha256`); an edit
mid-flight never mutates a running envelope.

### 6.2 Slot exactly-once, for free

A trigger firing mints `cmd_id = "rt:<routine_id>:<slot>"` — deterministic: cron slot = the
**scheduled** tick ISO-8601 (never observed time — G-CLOCK skew shifts firing, never duplicates);
watch slot = `sha256(path|mtime|size)[:16]`; fire slot = caller idem or a fresh ULID. Identity-dedup
(§4 step 3) then guarantees a crashed-and-restarted scheduler cannot double-fire a slot. `catchup:
skip` ignores missed slots; `once` fires only the single newest missed slot.

### 6.3 Same queue, same receipts

A routine's envelope is indistinguishable in flow from a typed command; watch-event storms coalesce
under §4 step 7 (`settle_s` as pre-filter); `hc top`'s commands pane shows them.

### 6.4 The unattended ceiling + the dead-man law

Issuer `routine/*` (and any non-operator issuer) runs H0/H1; an H2/H3 act inside its run PARKS in
the approval queue with a hold notice on `_ops`. **[SECURITY-SEAM: seat 10]** the structural form:
the operator private key never lives on the cluster, so a routine's envelope is only ever
conductor-signed and *physically cannot* present the signature H3 requires (10-T8, adopted).

**Dead-man proof-of-notification (H2):** notification = an **interactive-class** principal's
read-cursor advancing past the hold-notice seq. Cursor class is declared per principal at
registration: `interactive` (talk REPL on a live tty; `hc queue --watch`; PWA foreground with
visibility evidence) vs `headless` (background SSE tails, exporters, routines, bridges, **MCP
clients — commanding AND headless**; the read-only viewer — doubly excluded). A headless consumer
draining `/events` overnight does not count; absent an interactive cursor-advance by
deadline-minus-grace, the H2 act degrades to an H3 hold. A cancelable delay nobody can cancel is H1
wearing H2's badge.

---

## §7 · Queries are never commands (the read path)

`top`, `runs`, `logs`, `replay`, `peek`, `export`, `events`, `fleet`, `queue ls`, `doctor`,
`provider ls`, `version` are **named queries over the log** — never enveloped, never queued, served
even with the dispatcher wedged (law 1's availability half). The named-query registry (Q-FLEET,
Q-CULTURE, Q-CELLS, Q-RUNS, Q-ROUNDS, Q-ARMS, Q-COSTS, Q-OPS, Q-QUEUE, Q-NULLGAP) is defined in
constitution §10 (viewer table) with field definitions owned by their planes (econ owns Q-COSTS/
Q-NULLGAP + diagnosis strings; run owns Q-RUNS/Q-ROUNDS/Q-ARMS; act owns Q-QUEUE's fields). One
definition, three renderers: CLI table, `GET` JSON, viewer lane.

**Q-QUEUE is a single-type fold** (seam settled #690): `act_receipt{phase:hold}` rows carry an
executor-minted `summary{claim, capability_ref, harm_effective, expectation:{kind, resolve_by}|null,
until, grant_ttl}` block — countdowns and the exact copy-paste grant text (`hc grant a7`) render
from hold rows alone, O(1) per act, zero nucleus reads.

### 7.1 · The CLI exit-code contract (SUR-9; constitution §10.5.1 cites THIS table)

Semantic exit codes — the tri-state discipline reaching shell scripts. Every verb honors them under
`--json` and prose alike; the receipt chain stays the truth (a script needing detail parses the
result receipt, never the exit code alone).

| code | meaning |
|---|---|
| `0` | ok / converged (a `result{outcome:ok}` exists) |
| `2` | usage error — malformed invocation; no envelope was minted |
| `3` | refused — a typed `result{outcome:refused}`; the class is in the receipt |
| `4` | not-found — the named run/cmd/act/routine does not exist |
| `6` | **completed-without-convergence** — terminal, best-so-far/synthesis delivered (the tri-state's third value in shell form) |
| `130` | SIGINT — the CLIENT detaches; the run continues (stopping is an explicit `stop`, never a keystroke side-effect) |

### 7.2 · The MCP tool inventory (the "13 tools"; constitution §10.5.3 cites THIS list)

The MCP server (`surfaces/mcp.py`) exposes the typed grammar, never the NL router (a Claude-class
client is itself a model; double-LLM routing is refused). **Eleven commanding tools** — one per
operator-facing verb of §2, each minting a CommandEnvelope (`surface:"mcp"`) through the ONE
ingress, `task_id ≡ cmd_id` — **plus two read tools**:

| # | tool | maps to |
|---|---|---|
| 1–11 | `hc_run` · `hc_drive` · `hc_ask` · `hc_resume` · `hc_pause` · `hc_stop` · `hc_fire` · `hc_grant` · `hc_deny` · `hc_cancel` · `hc_routine_set` | the §2 verbs, 1:1; strict input/output schemas; `verdict_type` is a schema field (the honesty rule's MCP twin) |
| 12 | `hc_status` | the named-query listing (the log-fold that sidesteps `tasks/list`) |
| 13 | `hc_peek` | the private-nucleus read (stdio transport ONLY; constitution §10.6) |

The fleet-configuration verbs (`provider.set`, `config.set`, `maintain`) are deliberately NOT
exposed over MCP — MCP clients are headless-class principals (§6.4); fleet configuration stays on
the operator's CLI/HTTP surfaces. Grant/deny over MCP remain subject to the same H3 structural
ceiling as every surface (§2's SECURITY-SEAM).

---

## §8 · Reader-liberality & versioning

- Envelope fields: liberal-read, round-trip-preserve (R2/R5). Verb set: CLOSED (§2).
- `contracts` census: MAJOR mismatch = typed refusal BOTH ways (old hc/new hcd and new hc/old hcd);
  MINOR skew = proceed (unknown fields preserved; unknown enum values rendered verbatim).
- This file versions as `command/5.x`; the JSON-Schema mirror (`contracts/schemas/command.schema.json`)
  is a generated lockstep twin, not a second artifact (kernel T2).

## §9 · Migration from the live v1 shape

The live repo has **no envelope, no queue, no receipts, no `_ops`**: `cli.py` builds cells and calls
engine functions in-process (cli.py:16,44-48,117,128-134,156-172,206-215); `commander.py` routes NL
with un-metered cognition (F15, :116) and dispatches directly (:159-258); `api.py` builds a cell
inside the request handler and blocks the connection for the whole run (:17,57-62); `daemon.py` is a
533-byte uvicorn wrapper; `surfaces/mcp.py` is 0 bytes. The only idempotency anywhere is cell-level
`idem` on ask. Migration:

1. **M-CMD-1 (with SUR-s1):** introduce `_ops` + the `command`/`cmd_receipt` registry rows (rides
   wire.md's spine-adoption epoch — one wire MAJOR, 03/01 own it); re-route `cli.py` verbs through
   the embedded ingress. **Operator-visible CLI flags do not change** — the surface compiles the same
   flags to envelopes; `hc run/ask/drive` outputs gain an ack line + receipt pointers.
2. **M-CMD-2 (with SUR-s2):** `api.py`'s `POST /ask`,`/resume` become compat shims that mint
   envelopes (deprecated at command/6); new endpoints per constitution §10 land beside them.
   `daemon.py`'s entry moves to the composition root — `entrypoints/hcd.py` (kernel LAYER-1 v5
   ruling #692: ONE named root, wire-only — constructors + inject + serve, no logic call sites;
   `hc --embedded` reuses it).
3. **M-CMD-3 (with SUR-s3):** `commander.py`'s router becomes a d0 cell; `talk` mints envelopes;
   the direct-dispatch block (:165-258) is deleted; `med._db` reach-in (:244-247) is replaced by a
   named query.
4. Old ledgers/mediums predating `_ops` fold cleanly: the commands pane renders empty; nothing
   retro-mints (03-T9's no-retro-minting law).

**Rollback:** each M-CMD is a pure addition + re-route; the engine functions remain callable by the
verb-executor; reverting re-exposes them to the old call sites without data migration.

