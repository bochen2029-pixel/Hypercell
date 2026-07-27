# CONTRACT: wire — the Medium envelope, payload registry, chain, retention, transports

**Version:** `wire/5.1.0` (semver; this file is the source of truth; the JSON-Schema mirror at
`contracts/schemas/wire.schema.json` is generated from it, never hand-edited).
**Status:** v5.0 CONSTITUTIONAL DRAFT · frozen at ratification · rev 2026-07-25 (P3 resolution); a
change is a semver bump + the schema + the code in one commit, announced by
`command{kind:contract_bump}` on `_ops` (§6.3).
**Pairing:** Medium (noun) — converse (+ the carried forms of all verbs); the type registry; the
chain (the pairing law: `contracts/_TEMPLATE-HEADER.md` H2).
**Emit/read:** strict-emit / liberal-read (H4; the Reader-liberality block below is its normative
statement here). **Operator boundary:** n/a — wire carries no operator-input surface; R5
strictness lives with run.md's manifests and command.md's CommandEnvelope.
**Schema mirror:** `contracts/schemas/wire.schema.json` (generated, same-commit lockstep).
**Falsifiers:** C1–C12 (§12, the transport conformance battery — one test file, both transports);
the ARCH §15 wire-group rows; MIG-1/MIG-5 exercise the reader laws (H6).
**Supersedes:** wire v0.1 (live at `C:\hypercell\contracts\wire.md`) and the v2 §4/§9 wire text.
**Reader liberality (MUST, both directions):** receivers MUST ignore unknown *types* and MUST
preserve — round-trip, never drop — unknown *fields*; emitters mint only registry types and schema
fields (`x-*` excepted). Reader models are liberal (`accept + preserve`); emit models are frozen
(strict). A reader that errors on an unknown type or strips an unknown field fails C7. MINOR bumps
are additive with defined defaults for absent fields (e.g. `receipt.oracle_gen` absent reads `"g0"`,
forever). A new **instruction-bearing** type is always MAJOR.
**Migration:** §15 (from the live v1 shape — 9 columns, global seq, no chain: E4).
**Versioning anchor:** every culture's first record is `presence{phase:genesis}` carrying the
contract census `{"wire":"5.1.0", …}` and the chain-construction id (§5). The wire version is never
inferred from file mtimes or code — it is read out of the log it governs.

RFC-2119 register throughout.

---

## §1 · Principles and framing laws

The Medium is **one append-only, hash-chained, firewalled log per culture, plus native wake**. Its
five duties — audit trail, resume source, provenance record, viewer feed, stigmergy substrate — are
all **named folds over that one log** (the Fold Law, A13). Three framing laws:

- **L-FOLD-CLOSURE (MUST).** Every constitutional fold (certificate, resume, null ledger, claim
  validity, spend, `hc top`, viewer queries) declares its input filter, and that filter MUST be
  **compaction-closed**: a subset of the types whose retention class survives the fold's horizon
  (R-forever ∪ R-run for run-scoped folds; R-forever alone for fleet-history folds). A fold that
  reads R-decay types is a bug at review time, not a surprise at TTL time. Corollary (the
  decision-record pattern): where a decision consumes R-decay evidence (e.g. a preflight `status`),
  the durable decision record MUST embed that evidence's digest and verdict inline — folds read the
  decision record, never the decaying row.
- **L-ORDER (MUST).** The **culture is the ordering domain**: `seq` is strictly monotonic and dense
  at post *within a culture*; cross-culture ordering is undefined. `priority` is an attention hint
  for surfaces and MUST NOT reorder delivery: poll/replay order is `seq`, full stop.
- **L-CLOCK (MUST).** `seq`, `ts`, and (where present at post time) `hash` are **Medium-assigned**.
  Cells MUST NOT supply them. `ts` is informative; `seq` is normative.

---

## §2 · The envelope — 16 fixed columns

v1's thirteen live columns + exactly three (`corr`, `mentions`, `hash`). Two column names are
additionally **reserved** with pinned semantics (`sig` — excluded from the leaf, signs it; and
`redactions` — inside the leaf; both §2.1, per R1 "the count must be true"). Anything beyond this
set is a wire MAJOR bump.

| # | field | type | assigned by | semantics |
|---|---|---|---|---|
| 1 | `seq` | int | Medium | per-culture total order; dense at post; gaps only via `compact` |
| 2 | `ts` | str | Medium | UTC ISO-8601 ms; informative (L-CLOCK) |
| 3 | `culture` | str | sender | the room / run id; `commons`, `_ops`, and `_fleet` are reserved (R22) |
| 4 | `sender` | str | sender¹ | claim-id, or `operator` / `conductor` / `bridge:<peer>` / a registered surface principal |
| 5 | `recipient` | str? | sender | null = whole culture; claim-id = directed (still visible); `operator` = human inbox |
| 6 | `type` | str | sender | registry (§3) or `x-*` |
| 7 | `reply_to` | int? | sender | the `seq` answered (threading) |
| 8 | `round` | int? | sender | round (tournament) / stage (pipeline) |
| 9 | `priority` | int | sender | 0 normal; higher = surface first; never reorders (L-ORDER) |
| 10 | `origin` | str? | sender/bridge | `command`: the authority acted for; bridged messages: `external` |
| 11 | `idem` | str? | sender | idempotency key; `(culture, sender, idem)` unique — the exactly-once post key (§7.1) |
| 12 | `corr` | str? | sender | ULID of the logical operation (run, act, command); survives bridging & re-sequencing |
| 13 | `mentions` | json? | sender | array of claim-ids; the wake-on-mention filter |
| 14 | `body` | json/str? | sender | payload; soft cap 4 KB (warn), hard cap 32 KB (refuse → artifact) |
| 15 | `artifact` | json? | sender | pointer block (§4); REQUIRED when the payload exceeds the body cap |
| 16 | `hash` | str? | Medium | per-culture chain head at this seq (§5); T0: at post; T1: at seal |

¹ Sender identity is a declared principal binding. Authenticating it is seat 10's identity ladder;
the §6 ACL is enforced as a *correctness* mechanism at every stage regardless
(`[SECURITY-SEAM: sender-authn]`, §16.1).

**L-ASSIGNED-BY-IS-TRUST-INPUT (MUST).** The assigned-by column above is **normative for trust
derivation**: firewall trust tags (identity-firewall.md) MUST derive only from *Medium-assigned*
fields (`seq`, `ts`, `hash`), the §6 ACL fold's verdict, and the reader's own ingress channel
class — never from sender-declared fields. `origin` and `sender` are declarations until the ladder
authenticates them; deriving trust from them is the `membrane.py:13` bug rebuilt one level up.

### 2.1 Reserved columns: `sig` and `redactions` (declared now; absent in 5.x rows until a MINOR lands them)

Counts stay true (the E1 lesson): the v5 envelope is 16 columns; these two are **reserved** —
name, semantics, and leaf treatment pinned now so each lands later as a MINOR bump with **no chain
break and no MAJOR**.

- **`sig`** = ed25519 signature (hex) by the *sender principal's registered key* over `leaf_n`
  (§5.1). `sig`, like `hash`, is **excluded from the leaf** — a signature cannot sign itself;
  verification is `ed25519.verify(pubkey(sender), leaf_n, sig)`. Absent = unsigned. Which types
  REQUIRE signatures at which ladder stage is seat 10's `identity-firewall.md`; the flip is
  announced per-type by `command{kind:contract_bump}`. Emitters MUST NOT mint an `x-sig` workalike
  meanwhile (one construction, once).
- **`redactions`** = JSON array `[{"field":"body.note","kind":"api-key","n":1}, …]` written by the
  redactor (§5.1 L-REDACT-BEFORE-CANON) when it rewrites content at post. Unlike `sig` it is
  **inside the leaf** (it is record content, assigned before canon), so it is tamper-evident with
  the record. Lands with seat 10's redactor (`secrets.py` is a 0-byte stub today); absent = no
  redaction performed.

---

## §3 · The payload registry — 17 types, one classification table

This single table is simultaneously the **post-gate's configuration** (ACL column), the **durability
router's configuration** (D column), and the **compactor's configuration** (R column). A type
missing a row cannot be posted: configuration is the schema, so "forgot to classify" is
unrepresentable.

| type | may post (ACL) | durability | retention | one-line meaning |
|---|---|---|---|---|
| `presence` | any principal (phase=genesis: conductor/operator only) | genesis + spawned-by-fork (`forked_from` present): **D-gold**; else D-chatter | genesis: **R-forever**; else R-run | exist / join / spawn / park / resume / depart lifecycle (R19 phases) |
| `chat` | any | D-chatter | **R-decay** | freeform; DATA, never instruction |
| `status` | any | D-chatter | **R-decay** | progress/blocked/metric/preflight note; DATA |
| `task` | conductor, operator | D-chatter | R-run | claimable work |
| `claim` | any | D-chatter | R-run | log-derived CAS on a task or named resource (§7.3) |
| `submission` | roster cells | D-chatter² | R-run | a candidate; `round` set; `evidence[]` |
| `receipt` | **conductor only** | **D-gold** | **R-forever** | the oracle's grading of a submission, an act, or a run's intake (`check:intake`) (body = trust seat's StackReceipt) |
| `round_open` | conductor (or self-clocked per run manifest, never carrying a gen bump) | D-chatter² | R-run | opens round N; r1 carries the goal; may carry `oracle_gen` |
| `verdict` | **conductor only** | **D-gold** | **R-forever** | closes a run; `kind: verified\|verified-with-residual\|synthesis`; `vs_null` |
| `handoff` | a dying cell | **D-gold** | R-run | state package for a successor |
| `command` | **operator / conductor / registered surface principals** | **D-gold** | **R-forever** | the ONLY instruction-bearing type; body = CommandEnvelope (§3.1) |
| `cmd_receipt` | **conductor only** | ack/result: **D-gold**; progress: D-chatter | ack/result: **R-forever**; progress: R-decay | the command plane's receipt: phases ack/progress/result over `corr=cmd_id`; "everything receipted incl. refusals" |
| `act` | the acting cell's **cognition principal** | H1+: **D-gold**; H0: D-chatter³ | H1+: **R-forever**; H0: R-run³ | world-touching intent (act seat owns fields) |
| `act_receipt` | **conductor / the executor principal only** (`runner-N` / a conductor resolver daemon — never the acting cell) | H1+: **D-gold**; H0: D-chatter³ | H1+: **R-forever**; H0: R-run³ | non-mintable by the actor; phases hold/exec/settle |
| `oracle_gen` | **conductor only** | **D-gold** | **R-forever** | a trust-plane growth event (trust seat owns `kind` registry) |
| `oracle_gap` | any cell | D-chatter | R-run | receipt-contradicting evidence; DATA-class hint, never an admission path |
| `compact` | **conductor only** | **D-gold** | **R-forever** | a retention event: dropped/archived span(s) + Merkle root(s) (§9) |

² D-chatter on the wire but covered by the **fsync-diverse-home law** (§5.4): the producer's own
fsync'd nucleus journal holds the content (live: `nucleus.py:67-70`); a transport loss is recovered
by idempotent re-post under the same `idem`.

³ **Cite-pinned retention.** H0 observation acts/receipts default D-chatter + R-run (loss = a
re-fetch); at verdict the Conductor **retention-promotes** exactly the records inside the champion's
`evidence[]` closure. Promotion is a *fold*, not a mutation: the compactor's eligibility check
(§9.2 step 1) excludes any record reachable from a retained verdict's evidence closure — **of any
type** (a cited `chat` row pins identically). The `act://` resolution law follows: resolvable
forever iff cited by a retained verdict. H1+ stays D-gold + R-forever unconditionally.

**The count — 17, true.** v1's twelve − `announce`/`depart` (merged into `presence`) = ten, +
`presence` + `act` + `act_receipt` + `cmd_receipt` + `oracle_gen` + `oracle_gap` + `compact` =
**17**. The merge absorbs live drift E1: `spawned` → `presence{phase:spawned}`; `synthesis` →
`verdict{kind:synthesis}`; `judgment` → `receipt{check:panel}`. `cmd_receipt` restores the v3
conductor seam (#4) my predecessor negotiated but never swept into this table (caught #688; ruled
#692; accepted #698 — "the count must be true" beats "16 is sacred").

**The three receipt planes** mirror the fabric's trust boundaries (v2 §4): the fabric has exactly
two live crossings — the operator above, the world below — plus the bar between. Each gets its own
non-mintable receipt type: **`cmd_receipt`** (operator boundary; conductor-only),
**`act_receipt`** (world boundary; executor-only — never the acting cell: no act reports itself),
**`receipt`** (the oracle's grading; conductor-only). `receipt{subject:{act}}` vs `act_receipt`
duty split: the former is the **oracle grading an act's outcome** (quality), the latter the
**executor's phase record** (hold/exec/settle — reality). Different ACL, durability, retention,
and cardinality ⇒ different types (PART A.2 row 1). Overloading any receipt onto another would
make constitutional folds body-parse-dependent, violating type-expressible fold closure (§692
ruling grounds). Unknown types MUST be ignored; experiments are `x-*`.

**The NON-MINTABLE (warrant-class) xref set — HOME.** The set is {`receipt`, `act_receipt`,
`verdict`, `command`, `cmd_receipt`}: the mint-restricted types that CERTIFY a boundary crossing.
The derivation is this table's ACL column intersected with crossing-certification — `oracle_gen`
and `compact` are mint-restricted too but certify no crossing (they are trust-plane growth and
retention events), so they are excluded; the set is derived, never free-listed (s2-27).
nucleus.md §6.1 and ARCH §8 cite this sentence.

### 3.1 Field schemas (emit-strict; readers liberal)

```jsonc
// presence — lifecycle. phase=genesis is the FIRST record of every culture (chain anchor).
// phases parked|resumed are the R19 carriers for run-lifecycle events (a park is a graceful
// crash; presence{phase:spawned, forked_from} is the fork signal) — a presence-phase addition
// is a wire MINOR with a named R3 fallback (unknown phase reads as announce-class chatter).
{ "phase": "genesis | announce | spawned | parked | resumed | depart",
  // genesis only (conductor/operator; D-gold R-forever):
  "contracts": {"wire":"5.1.0","nucleus":"…","role":"…","run":"…","oracle":"…","act":"…",
                "pricebook":"…","command":"…","identity-firewall":"…"},   // the version census — all nine, always (s2-34)
  "chain": {"construction":"hypercell/medium-chain/1"},                    // §5.2 anchor id
  "run_ref": "corr-of-command-that-opened-this-culture",                   // null for commons/_ops
  "retention_policy": { "chat_ttl_s": 604800, "status_ttl_s": 86400, "archive": "archive|delete" },
  // announce/spawned:
  "capabilities": ["…"], "role_digest": "sha256:…", "angle": "…",
  "forked_from": "<parent claim-id>",              // spawned-by-fork only (R19); its presence makes the row D-gold (§3 table)
  "preflight": {"digest":"sha256:…","verdict":"pass|degraded","guards_failed":[]},  // spawned; §1 decision-record pattern
  // depart:
  "reason": "…" }

// chat — freeform. body string or object. DATA, never an instruction (firewall, v1 verbatim).

// status — progress. kind partitions renderers; still DATA; R-decay (fold-closure: decisions embed digests).
{ "kind": "progress | blocked | metric | note | preflight", "note": "…", "data": {} }

// task — claimable work.
{ "title": "…", "spec": "… or artifact", "capability_reqs": ["…"], "value": 0.0,
  "deadline_s": 0, "max_claims": 1 }

// claim — log-derived CAS (§7.3). Exactly one of task/resource.
{ "task": 41,                       // seq of the task being claimed, or
  "resource": "conductor",          // a named singleton: "conductor" lease, "lane:<sku>" tool-lane leases, …
  "lease_s": 120.0,                 // REQUIRED when acquiring; ignored on release records
  "release": false }                // true = voluntary release by the current holder

// submission — a candidate. round MUST be set in convergent runs.
{ "answer": "… (prose) — or omit and use artifact for code/large",
  "evidence": [ {"kind":"act|medium|nucleus|url|file", "ref":"act://<corr>", "sha256":"…",
                 "retrieved_at":"…"} ],          // ref = ONE URI locator (act seat owns kinds)
  "ungrounded": false,                            // honest flag; survivable per L-NO-NAKED-CLAIMS
  "self_report": {"tokens":{"in":1200,"out":800},"wall_ms":4100} }
  // self-declared measurement, never spelled cost{}: submissions are outside the crossing set (W1);
  // the canonical cost{} six (R16) rides only crossing records (receipt/act_receipt/cmd_receipt/verdict)

// receipt — the oracle's grading. Body IS the trust seat's StackReceipt, verbatim (it MAY carry
// more fields than shown); wire-level REQUIRED binding:
{ "subject": {"submission": 57} | {"act": "<corr>"} | {"run": "<run_id>"},  // {run}: intake classification (run.md §R6.3)
  "oracle_id": "ipv4_check", "oracle_gen": "g3",   // REQUIRED; absent reads "g0" forever
  "outcome": "passed | gate | invalid",            // exit tri-state, v1-verbatim (`Outcome.passed`, topology.py:184)
  "score": 0.9286,
  "check": "unit | grounding | panel | probe | intake",
  "per_case": [ {"id":"c17","pass":false,"detail_ref":"…"} ],
  "report_ref": {"…":"artifact"},                  // report-file protocol (trust seat)
  "families": ["…"], "dissent": 0.0, "contested": false,
  "cost": {} }

// round_open — opens round N; round 1 carries the goal.
{ "goal": "… (r1 only)", "roster": ["claim-ids"], "deadline_s": 0,
  "oracle_gen": "g3",                              // a gen bump opens a round; NEVER on self-clocked round_open
  "regrade": false }

// verdict — closes a run. kind is the honesty split (L-HONEST-VERDICT).
{ "kind": "verified | verified-with-residual | synthesis",   // HOME enum (R21): the wire verdict
                                                             // discriminator; oracle.md §5.2's block is certificate-side
  "champion": {"submission": 57, "arm": "arm2", "score": 1.0},               // verified / verified-with-residual
  "vs_null": {"null_score": 0.86, "null_usd": 0.004,                          // REQUIRED on verified (L-NULL)
              "margin_production": 0.14, "margin_invoice": 0.11},             // DUAL-UNIT per v2 §4, restored
              // (the v3 draft collapsed this to one `margin` — a dropped v2 guard; the flip
              //  predicate keys matched-INVOICE, ruling R4; field detail owned by run.md, seat 04)
  "residual": ["…unprobed, listed on purpose…"],
  "why": "…", "certificate_ref": {"…":"artifact"},
  "text_ref": {"…":"artifact"} }                   // synthesis payload (absorbs live `synthesis`)

// handoff — continuity package (Intercom §13 semantics kept).
{ "successor": null, "state_ref": {"…":"artifact"}, "open_threads": ["…"], "next_action": "…" }

// command — the ONLY directive. Body is the CommandEnvelope BY REFERENCE (conductor seat owns
// contracts/command.md; this contract never duplicates its fields); wire-level binding:
{ "kind": "see contracts/command.md §2 (the one kind registry)",
  "cmd_id": "ULID",                                // dedup key (F7); MUST equal envelope corr for directives
  "grant_for": "<act corr>",                       // kind=grant only
  "census": {} }                                   // kind=contract_bump: the new version census

// cmd_receipt — the command plane's receipt (conductor seat owns body fields in contracts/command.md);
// wire-level bindings owned here: corr = the command's cmd_id (REQUIRED); phase ∈ {ack, progress,
// result}; each phase a SEPARATE envelope over that corr (fold, never mutation); ack/result are
// D-gold R-forever (the operator-boundary provenance: every command — including a REFUSED one —
// gets a result); progress is D-chatter R-decay and operator-facing streaming rides it (run-internal
// progress stays `status`).
{ "phase": "ack | progress | result",
  "outcome": "see contracts/command.md §3 (the one outcome enum)",   // phase=result; refusals are receipts too
  "note": "…", "result_ref": {"…":"artifact"}, "cost": {} }

// act / act_receipt — act seat owns field schemas (contracts/act.md). Wire-level bindings owned here:
//   act.corr REQUIRED (pairs act→grant→receipts); act.idem REQUIRED at H1+;
//   act_receipt.phase ∈ {hold, exec, settle}; each phase is a SEPARATE envelope sharing the act's
//   corr (the wager lifecycle is a fold over corr — never a mutated row);
//   phase=hold IS the H2 visible countdown message (one record, two duties).

// oracle_gen — the trust plane's growth-event slot (trust seat owns the kind registry; kind-addition
// is MINOR under the kernel versioning law — not even a type addition).
{ "kind": "see contracts/oracle.md (the one kind registry; trust seat owns it)",
  "oracle_id": "ipv4_check", "gen": "g4", "digest": "sha256:…", "case_count": 41,
  "lineage": {"prev_gen": "g3", "prev_digest": "sha256:…"}, "opened_by": "<corr>", "errata_ref": null }

// oracle_gap — receipt-contradicting evidence. DATA-class hint to the probe scheduler; NEVER an
// admission path.
{ "receipt": 88, "claim": "receipt marks c17 pass but the artifact fails on '٤'",
  "evidence": [ {"…":"evidence ref"} ], "severity": "low | material" }

// compact — a retention event (§9). One record may carry several contiguous runs.
{ "kind": "drop | archive",
  "runs": [ {"from_seq": 100, "to_seq": 180, "count": 81,
             "merkle_root": "sha256:…", "algo": "rfc6962-sha256",
             "chain": {"prev": "<hash@99>", "post": "<hash@180>"}} ],
  "by_type": {"chat": 70, "status": 11},
  "archive_ref": {"…":"artifact → archived JSONL"} }   // kind=archive only
```

**Registry drift falsifier.** E1 recurring ⇒ C7 + a CI check that greps live `post(` call sites
against this registry (the check that would have caught `spawned` on day one).

---

## §4 · The artifact pointer

```jsonc
{ "path": "sandbox/<culture>/r2/arm3.py",   // culture-sandbox-relative; NEVER absolute (bridge/portability)
  "bytes": 184220, "lines": 2310, "mime": "text/x-python",
  "sha256": "…",                            // REQUIRED: a pointer to an editable path is not provenance
  "store": "sandbox | archive | objstore | quarantine",
  "manifest": null }                        // chunker manifest for pre-chunked artifacts
```

Laws: (1) `sha256` computed at post time by the *sender's* bus client; any reader MAY re-verify; a
digest mismatch is fraud-class evidence (L-NO-NAKED-CLAIMS). (2) The sandbox store SHOULD be
content-addressed (`sandbox/<culture>/objects/<sha256[:2]>/<sha256>`) so `file://…#sha256=…`
evidence refs resolve with no mapping table. (3) `bytes`/`lines` MUST be present so receivers can
budget before opening (Intercom-proven). (4) Archival (§9) moves bytes `sandbox → archive` and posts
`compact{kind:archive}`; envelopes are immutable, so a stale `store:sandbox` pointer resolves by
falling through the archive map — a fold over `compact{kind:archive}` records. (5) On T1
multi-node, `sandbox` is the culture's shared volume; an object-store realization (e.g. JetStream
Object Store) is a permitted `store` behind the same pointer schema — adapters change, the pointer
doesn't.

---

## §5 · The hash chain — one construction for tamper-evidence, sealing, and gold durability

### 5.1 Canonical form and leaf

`canon(x)` = RFC 8785 (JCS) canonical JSON, UTF-8. The **leaf** of a message is:

```
leaf_n = sha256( canon({ seq, ts, culture, sender, recipient?, type, reply_to?, round?,
                         priority, origin?, idem?, corr?, mentions?, body?, artifact? }) )
```

— every envelope field **except `hash` and (reserved) `sig`**; when the reserved `redactions`
column lands it IS in the leaf (§2.1 — it is record content); absent and null are identical (omit
from the canon object); `body` as posted (JSON canonicalized; raw strings as their UTF-8 bytes
inside the JSON string); `artifact` including its `sha256`. **The nucleus ledger uses the same
`canon` + leaf + chain construction** (cell-nucleus seam, confirmed #689: their anchor is
`sha256("hypercell/nucleus-chain/1" ‖ 0x00 ‖ claim_id)`): one verifier, two logs.

**L-REDACT-BEFORE-CANON (MUST).** The redaction hook (seat 10's redactor) runs in `post()` **before
canon** (§7.1 step 0). The leaf — and therefore the chain, the anchor, and every Merkle root — is
computed over post-redaction bytes only. **The chain never witnesses a secret**: `verify()` MUST
never require a secret to re-verify a log. (An append-only log cannot un-say a secret; the only
correct placement is before the append. `[SECURITY-SEAM: redaction]`, §16.3.)

### 5.2 The chain

```
hash_0 = sha256( b"hypercell/medium-chain/1" || 0x00 || utf8(culture) )   // genesis constant, per culture
hash_n = sha256( raw32(hash_{n-1}) || raw32(leaf_n) )                     // raw digest concat; hex in the column
```

The construction id `hypercell/medium-chain/1` is **chain-versioned, not wire-versioned** (v3 baked
`wire/3` into the constant; repealed): a wire semver bump never re-anchors existing chains, and a
future digest-algorithm change mints `medium-chain/2` for *new* cultures only. Each culture's
genesis record states its construction id (§3.1), so a verifier never guesses.

### 5.3 Who computes it, per transport

- **T0 (SQLite):** the posting transaction holds the culture's write lock, reads `hash` at `seq−1`,
  computes, inserts — race-free by construction. `post()` returns the hash.
- **T1 (JetStream):** publishers are concurrent and the broker runs no fabric code; the chain is
  computed by the **chain-sealer** — the Conductor's durable consumer that processes each culture
  stream in seq order and materializes `hash` into the read model (§11.3). `post()` on T1 returns
  `hash: null`; the guarantee is **eventual seal with bounded lag** (W3 measures it); D-gold posts
  *force* an immediate seal (§5.4).

### 5.4 The anchor — one mechanism, three duties

The Conductor maintains an **anchor log**: an append-only, fsync'd JSONL file
(`<home>/_anchor/<culture>.jsonl`) of `{seq, hash, ts}` checkpoints, written (a) every
`anchor_every` messages (default 64), (b) at every **D-gold** message, (c) at every `compact`
record.

1. **Tamper-evidence with an external trust point.** `verify()` recomputes the chain over retained
   contiguous runs, checks `compact` boundary assertions across holes (§9), and matches every
   anchor. A rewrite of log bytes + stored hashes still collides with the anchor. Custody and
   non-repudiation of the anchor file: `[SECURITY-SEAM: anchor-custody]`, §16.2.
2. **The Jepsen answer, honestly.** On T1, a D-gold `post()` returns only after (i) PubAck and
   (ii) the sealer has consumed the message and fsync'd its anchor entry. Gold never has its only
   copy inside JetStream's lax-fsync window. (Re-verified 2026-07-16: the corruption-class loss —
   49.7% of acked writes under one flipped bit — is *still an open issue*, nats-server #7549;
   PART E.)
3. **The fsync-diverse-home law.** Conductor-posted gold → the anchor. **Cell-posted** gold
   (`act` H1+, `handoff`) and all paid work (`submission`) are journaled in the producer's own
   fsync'd nucleus *before* posting (live: `nucleus.py:67-70`); recovery re-posts under the same
   `idem`; dedup makes it exactly-once. **Law: every D-gold record has a second, fsync-diverse
   home.** Corollary (T0 prefix-durability): chatter commits at `synchronous=NORMAL`, gold commits
   flip the transaction to `FULL`; a crash loses only a contiguous **chatter-only suffix** — a gold
   commit's fsync covers the whole WAL before it. (sqlite.org/wal.html, fetched 2026-07-16:
   "Writers sync the WAL on every transaction commit if PRAGMA synchronous is set to FULL but omit
   this sync … NORMAL.")

**Failure modes:** sealer crash ⇒ restarts from its durable consumer position; seal-lag bound
re-established (W3). Anchor lost ⇒ chain still self-consistent; `verify()` degrades to
"consistent, unanchored" and says so.

---

## §6 · The post-ACL as a correctness mechanism; the lease; `_ops`

### 6.1 Two enforcement layers, one transport-neutral semantic

1. **Client gate (fail-fast; both transports).** The bus client refuses an ACL-violating `post()`
   with `AclDenied` before any bytes move. On T0 the gate re-checks inside the write transaction
   (perfect); on T1 it is advisory (the broker runs no fabric code). Hardening the gate against a
   hostile client: `[SECURITY-SEAM: acl-authn]`, §16.1.
2. **Void-at-fold (the invariant).** A privileged record that reaches the log without valid ACL
   standing **exists as bytes but is VOID as its type**: every constitutional fold applies the ACL
   filter deterministically and treats it as absent; `verify()` names it (`void_by_acl[]`). C11
   tests *this* semantic — "the post was rejected" would be a T0-only assertion, i.e. a contract
   leak by §12's own rule.

### 6.2 The conductor lease (fencing with zero new types)

"Exactly one live Conductor" is a `claim` on the reserved resource `"conductor"` in `_ops`. The
**epoch** is a fold (1 + valid holder-changes over that claim history) — no field anyone can lie
in; `hc verify` recomputes it. Privileged types (`receipt`, `cmd_receipt`, `verdict`,
`oracle_gen`, `compact`, conductor-`command`) are valid only when posted by the fold-current lease
holder; a deposed conductor's late posts are void-at-fold.

### 6.3 The `_ops` culture

The reserved control room: only `operator`, `conductor`, and registered surface principals may
address it; a cell principal's `post(culture="_ops", …)` is `AclDenied` (one ACL row — privilege as
a property of a *place*). `contract_bump`, the conductor lease, fleet-scoped `command`s, and
preflight/status ops-chatter live here.

### 6.4 The `_fleet` culture (R22)

The reserved fleet-history room, reserved beside `_ops` in §2's culture column. Its ACL row:
genesis is **conductor-posted at fleet init** (`presence{phase:genesis}` — conductor-genesis);
**privileged posts to `_fleet` are conductor-only**, enforced by the same two layers as §6.1
(client gate + void-at-fold). Fleet decision records (flip / grant / revoke / park / resume) ride
`command{kind:…}` — conductor-only, D-gold, R-forever, already instruction-bearing — so
L-FOLD-CLOSURE holds for every fleet-history fold with zero new types; field detail is run.md's
(§R7.3/§R9/§R11).

### 6.5 Principal registration and classing (the ACL column's evaluation rule)

- **Registration.** A sender principal is REGISTERED when its identity record exists at ingress:
  cells at spawn (the claim-id minted by the spawn gate; identity-firewall.md B.2), surface
  principals at their authenticated `_ops` registration, `operator` and `conductor` as the two
  well-known principals. Cursor class (`interactive | headless`, §7.4) is declared at this
  registration.
- **Claim-id grammar.** A cell's sender identity is its **claim-id** in the SPIFFE-URI naming
  shape: `spiffe://<trust-domain>/<claim-path>` (e.g. `spiffe://hc.local/run/ipv4/roster/2`) —
  identity-firewall.md B.2/Stage 2 (naming shape adopted now; federation refused).
- **Classing.** `class(sender)` ∈ {operator, conductor, surface, executor, cell}. The **executor
  principal** is `runner-N` or a conductor resolver daemon — a principal DISTINCT from any acting
  cell (no act reports itself); the acting cell posts as its **cognition principal** (its
  claim-id). **Unregistered senders class as `cell`** — the least-privileged class: their
  privileged posts are `AclDenied` at the gate and void-at-fold past it. Authenticating the
  binding stays seat 10's ladder (§16.1); classing is evaluable at Stage 0 from the registration
  fold alone.

---

## §7 · The bus interface — signatures, semantics, error modes

One protocol, two bindings. All ordering is `seq`; `priority` never reorders.

```python
class Medium(Protocol):
    # ---- write ----
    def post(self, culture: str, sender: str, type: str, *,
             body: Any = None, recipient: str | None = None, reply_to: int | None = None,
             round: int | None = None, priority: int = 0, origin: str | None = None,
             idem: str | None = None, corr: str | None = None,
             mentions: list[str] | None = None, artifact: dict | None = None
             ) -> Posted        # Posted{seq:int, ts:str, hash:str|None, dedup:bool}

    # ---- read ----
    def poll(self, culture: str, me: str, *, filter: Filter | None = None,
             limit: int = 500, advance: bool = True) -> Batch
             # Batch{msgs:[Msg], cursor:int, head_seq:int}; Msg = the §2 16-column envelope, verbatim
    def wait(self, culture: str, me: str, *, filter: Filter | None = None,
             timeout_s: float, limit: int = 500) -> Batch      # blocks; zero LLM tokens (§8)
    def replay(self, culture: str, *, from_seq: int = 1, to_seq: int | None = None,
               types: list[str] | None = None, include_compacted: bool = False
               ) -> Iterator[Msg]                              # audit path; reads archives if asked
    def get(self, culture: str, seq: int) -> Msg | None
    def exists(self, culture: str, *, corr: str, type: str | None = None) -> bool
             # O(1) on the corr index; serves the membrane's structural act-ref check

    # ---- coordination ----
    def claim(self, culture: str, me: str, *, task: int | None = None,
              resource: str | None = None, lease_s: float = 120.0, release: bool = False
              ) -> ClaimResult   # {won:bool, seq:int, holder:str, valid_until:str, epoch:int}
    def cursor_of(self, culture: str, agent: str) -> Cursor    # {seq:int, klass:"interactive|headless"}
    def set_cursor(self, culture: str, me: str, seq: int) -> None   # monotonic; regress is a no-op

    # ---- integrity & lifecycle ----
    def verify(self, culture: str, *, from_seq: int = 1, to_seq: int | None = None) -> VerifyReport
             # {ok, head_seq, head_hash, sealed_to, anchored_to, breaks[], void_by_acl[], zombies[]}
             # breaks: [{seq, expected, found}] — locates the exact seq (C12); void_by_acl/zombies: [seq]
    def compact(self, culture: str, *, now: str | None = None) -> list[int]   # conductor-only; §9
             # returns the seqs of the compact record(s) posted; [] if nothing was eligible
    def close(self) -> None

Filter = {types?: [str], recipient_me?: bool, mentions_me?: bool,
          senders?: [str], rounds?: [int], corr?: str}
          # recipient_me: rows where recipient == me OR recipient is null (inbox = directed + broadcast)
```

### 7.1 `post` semantics (numbered; the order is normative)

0. **Redact** (L-REDACT-BEFORE-CANON): the registered redactor rewrites `body`/`artifact` bytes;
   everything after this step sees only redacted content.
1. Validate: type known-or-`x-*`; ACL row (client gate, §6); body ≤ 32 KB hard
   (`PayloadTooLarge`; > 4 KB soft ⇒ warn "use an artifact" — the warning is client-local,
   log-class, never a Medium record); both caps measure `len(utf8(canon(body)))` (string bodies:
   their UTF-8 bytes; T1's `max_msg_size` sees the same bytes); artifact ⇒ `sha256` present.
2. Culture existence: the first record of a new culture MUST be `presence{phase:genesis}` posted by
   conductor/operator; any other first post ⇒ `UnknownCulture`. (`commons`, `_ops` pre-exist.)
3. Idempotency: if `idem` is set and `(culture, sender, idem)` was already posted ⇒ return the
   **original** `Posted` with `dedup=true`. Never an error: dedup is success. This is the
   exactly-once re-post key for crash recovery and the bridge (§13).
4. Durability: D-gold ⇒ the §5.4 path (T0: `synchronous=FULL` commit; T1: PubAck + sealed +
   anchored) before return. D-chatter ⇒ transport default.

Errors: `AclDenied` · `PayloadTooLarge` · `UnknownCulture` · `MediumBusy` (T0: `busy_timeout`
exhausted; T1: flow-control/stream-limit after bounded retries) · `MediumClosed`.

### 7.2 `poll` / `wait` (at-least-once delivery, exactly-once processing)

- `poll` runs the filtered past-cursor query, returns ≤ `limit` messages in seq order, and (if
  `advance`) sets the cursor to the last *returned* seq. Delivery is at-least-once; processing is
  exactly-once via the cursor + the consumer's own idempotency. The guarantee holds per
  (agent, fixed filter): an agent polling one culture under multiple filters MUST use
  `advance=false` + `set_cursor`, or distinct principals (b1-07).
- `wait` MUST implement **subscribe-hint → query → block → re-query** in that order (§8); a timeout
  returns an empty Batch, not an error. **The hint is best-effort and may over-fire; the filtered
  past-cursor query is the only truth** — sever the hint channel and the system degrades to
  slow-poll with zero loss (C3).

### 7.3 `claim` — the log-derived CAS (steal-from-stale)

No mutable claim state exists in the contract; any claims table is a render. Validity is a pure
function of `(log, t)`:

```
valid_holder(culture, target, t):                       # target = task seq | resource name
  holder = None; valid_until = -inf; epoch = 0
  for c in log(culture, type='claim', target=target):   # seq order
      if c.body.release and c.sender == holder: holder = None; continue
      if (holder is None or c.ts >= valid_until) and not c.body.release:
                                                        # free, or previous lease expired; a
                                                        # release record never ACQUIRES (b1-04)
          if c.sender != holder: epoch += 1
          holder = c.sender; valid_until = c.ts + c.body.lease_s
      elif c.sender == holder:                          # renewal before expiry
          valid_until = c.ts + c.body.lease_s
      # else: a challenger inside a live lease — a no-op by the fold
  return (holder if t < valid_until else None), epoch
```

`claim()` = post the record, then evaluate the fold at the post's own `ts`: `won = (holder == me)`.
The claimant learns the outcome from its own posted seq — no read-modify-write race on either
transport. **Steal-from-stale** = post after expiry (the fold flips holders, bumps the epoch); the
zombie discovers it lost *from the log* and stands down — its later privileged posts are
void-at-fold (§6). Time in the fold is Medium time (`ts` server-stamped; `t` = the evaluating
reader's newest observed `ts`, never an agent clock). Tool-lane micro-escrow leases (econ/act seam)
ride this same type: `claim{resource:"lane:<sku>"}` — zero new machinery.

### 7.4 Cursor placement (survives crash *and* context compaction)

- Transport-side cursor state (T0 `cursors` table; T1 KV + consumer position) is **machinery**.
- A nucleus-bearing cell (d1+) also journals cursor advances in its own nucleus (piggybacked on
  existing appends, ≈ zero cost). **Truth on resume: `max(nucleus cursor, transport cursor)`** — a
  total transport-state loss still resumes exactly-once. d0 cells ride transport cursors alone;
  re-delivery is harmless to a stateless reflex.
- Cursors carry a **class** (`interactive | headless`), declared at principal registration. The
  dead-man/H2 proof-of-notification law keys on *interactive* cursors only. `cursor_of()` exposes
  the class. The read-only viewer holds no principal, so it cannot advance an interactive cursor —
  which is what keeps "the operator saw it" honest.

---

## §8 · WAKE — the hint + cursor-query law, mechanized on both transports

**Targets:** p95 post→wake ≤ **200 ms** (T0), ≤ **500 ms** (T1); a sleeping cell burns **zero LLM
tokens** (it blocks in `wait()`, in the runtime, below cognition); hint severed ⇒ zero loss.

### 8.1 T0 (SQLite, single node)

- **Hint 1 — the doorbell file.** After commit, `post()` atomically replaces
  `_medium/doorbell/<sha1(culture)>` (8-byte LE head seq; write-tmp + `os.replace`). Waiters watch
  the doorbell directory (`inotify` / `ReadDirectoryChangesW`); one file per culture keeps watch
  noise O(cultures), not O(messages).
- **Hint 2 — the WAL watch** (optional): `medium.db-wal` mtime catches *any* commit; noisier; needs
  no post-side cooperation (covers foreign writers).
- **Mandatory fallback — the `data_version` poll.** A waiter with no watcher loops:
  `PRAGMA data_version` (header read; changes only on *other-connection* commits); changed ⇒ run
  the truth query; else sleep, adaptive 25 → 250 ms backoff. The fallback alone meets the 200 ms
  p95; watchers only make it faster.

### 8.2 T1 (JetStream, multi-node)

- **Hint = `consume()` on a durable pull consumer** (the modern API; push consumers are the legacy
  API and new client features land pull-only — PART E), one consumer per waiting agent per culture,
  `filter_subject = hc.m.<culture>.<type>` when the wait filter is type-shaped (§11.1), else the
  culture wildcard. Delivery is single-digit ms; 500 ms p95 is cluster-hop headroom.
- **Hints may be imprecise.** Subject filtering gives type precision; `mentions`/`recipient`
  precision comes from the truth query — by law the hint may over-fire, so no header gymnastics are
  load-bearing.
- Fallback: subscription drops ⇒ interval-poll the read API — same law, slower, zero loss.

### 8.3 The wake loop (normative pseudocode, both transports)

```
wait(culture, me, filter, timeout_s):
  h  = hint.subscribe(culture, filter)          # 1. subscribe FIRST (missed-wakeup discipline)
  b  = poll(culture, me, filter, advance=False) # 2. truth query — maybe already satisfied
  if b.msgs: hint.unsubscribe(h); return advance_and(b)
  deadline = now + timeout_s
  while now < deadline:                         # 3. block on hint or fallback tick
      hint.await(h, min(deadline - now, fallback_interval))
      b = poll(culture, me, filter, advance=False)   # 4. truth re-query on EVERY wake or tick
      if b.msgs: hint.unsubscribe(h); return advance_and(b)
  hint.unsubscribe(h); return empty_batch()     # timeout is a result, not an error
```

**Failure modes:** watcher loses events under load ⇒ absorbed by the fallback tick; doorbell file
deleted ⇒ recreated on next post; N waiters stampede on one post ⇒ N indexed sub-ms truth queries
(bounded, measured in W1).

---

## §9 · Retention & compaction — evaporation with a Merkle-sound memory

### 9.1 The classes (precise)

- **R-forever** — the provenance skeleton: `receipt`, `act_receipt`(H1+), `verdict`, `oracle_gen`,
  `command`, `act`(H1+), `compact`, `presence{genesis}`, `cmd_receipt{ack|result}` (the
  operator-boundary provenance, per the §3 table). Small by construction. Never eligible.
- **R-run** — **pinned until the culture's terminal `verdict`/abort lands; then archivable**:
  envelopes move to the archive JSONL under a `compact{kind:archive}` record (Merkle-rooted;
  resolution falls through the archive fold); artifact *bytes* archive with them. Types:
  `submission`, `task`, `claim`, `round_open`, `handoff`, non-genesis `presence`, `oracle_gap`,
  H0 `act`/`act_receipt`. "R-run-expired" MEANS: terminal verdict landed + the culture's archive
  grace TTL elapsed. (Resolves the v3 §9.1/§9.2 tension — PART A #19.)
- **R-decay** — TTL then dropped (or archived, per policy) through a `compact` record: `chat`,
  `status`, `cmd_receipt{progress}` (operator streaming rides `phase:progress`, per the §3 table).
  TTLs from the culture's genesis `retention_policy` (defaults: chat 7 d, status 24 h).

**Stigmergic evaporation, stated once.** On an append-only blackboard, chatter decay *is* the
pheromone-evaporation parameter: without evaporation the colony locks onto early trails; with it, a
cell conditioning on the visible log gets a recency-weighted signal for free. The TTL is that
parameter, per culture, tunable per run manifest. Evaporation ≠ amnesia: the audit path survives
via `archive` policy + Merkle roots; it is the *working set* that evaporates.

**The pin rule.** R-decay and R-run records are compaction-eligible only after the culture's
terminal `verdict`/abort. Open runs pin their span; post-verdict, chat evaporates and every
certificate still refolds, because L-FOLD-CLOSURE forbade certificates from reading chat in the
first place.

### 9.2 The compaction algorithm (conductor-only; idempotent; anchor-before-effect)

```
compact(culture, now):
 1. eligible = { m : retention(m) ∈ {R-decay, R-run-expired} ∧ m.ts + ttl < now ∧ m.seq ≤ sealed_head
                 ∧ culture has no open run                        # the pin rule
                 ∧ m ∉ evidence_closure(retained verdicts) }      # the cite-pin: promotion is a FOLD
                 # over verdict evidence[] closures — any type; never a row mutation
 2. partition eligible into maximal contiguous seq runs [a₁..b₁], [a₂..b₂], …
    (a keeper inside a span splits it — the chain must reconnect per run)
 3. per run: merkle_root over leaves a..b in seq order, RFC 6962 (sha256; 0x00/0x01 domain-separated
    leaf/node prefixes — no odd-duplication ambiguity)
 4. if policy=archive: append the runs' full envelopes to archive/<culture>/<date>.jsonl (fsync)
 5. post ONE compact record {kind, runs:[{from,to,count,merkle_root,chain:{prev:hash[a-1],
    post:hash[b]}}…], by_type, archive_ref?}                      # D-gold ⇒ sealed + anchored
 6. only AFTER (5) is anchored: physically delete —
    T0: DELETE range;
    T1: per-subject purge up_to_seq ONLY where the span is keeper-free for that subject;
        otherwise per-seq DeleteMsg (a cite-pinned row of the same type inside the span MUST
        survive a subject-wide purge); then mirror deletes.
 7. verify() thereafter: recompute the chain over retained contiguous runs; across each hole trust
    the compact record's chain.post (itself chained + anchored); archived bytes stay spot-checkable
    against merkle_root via standard inclusion proofs.
```

**Failure modes:** crash between 5 and 6 ⇒ rows survive + compact posted: re-run detects the
existing record and re-executes the delete (idempotent). Crash mid-delete ⇒ `verify()` flags
`zombies[]` (rows provably inside a compacted span); housekeeping re-deletes. Compact record lost
before deletion ⇒ impossible by construction (anchor-before-effect — fsync-before-effect applied to
forgetting).

---

## §10 · T0 binding — the embedded SQLite log

**Placement law (MUST):** `<home>/_medium/medium.db` on a **local** filesystem. Never
SMB/NFS/9p/drvfs — sqlite.org is explicit: "WAL does not work over a network filesystem" (fetched
2026-07-16). Substrate preflight guard G-DBLOCAL enforces it. One medium per node; multi-node is
T1's job, never a shared file.

```sql
PRAGMA journal_mode=WAL;            -- once, persists in the file
PRAGMA auto_vacuum=INCREMENTAL;     -- at create; compaction can return pages
-- EVERY connection, no exceptions (E3 — the lesson v1 dropped; contract text, not folklore):
PRAGMA busy_timeout=5000;
PRAGMA synchronous=NORMAL;          -- chatter default; D-gold commits flip to FULL for the txn (§5.4)

CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY, value TEXT NOT NULL);
  -- {'wire_version':'5.1.0','medium_id':'<ULID>','chain_start_seq_<culture>':…}

CREATE TABLE IF NOT EXISTS messages(
  culture   TEXT    NOT NULL,
  seq       INTEGER NOT NULL,              -- per-culture, dense at post (L-ORDER)
  ts        TEXT    NOT NULL,              -- Medium clock
  sender    TEXT    NOT NULL,
  recipient TEXT,
  type      TEXT    NOT NULL,
  reply_to  INTEGER,
  round     INTEGER,
  priority  INTEGER NOT NULL DEFAULT 0,
  origin    TEXT,
  idem      TEXT,
  corr      TEXT,
  mentions  TEXT,                          -- JSON array
  body      TEXT,
  artifact  TEXT,                          -- JSON pointer block
  hash      TEXT,                          -- chain head at this seq (§5)
  PRIMARY KEY (culture, seq)
) WITHOUT ROWID;                           -- clustered by culture: per-culture range scans are the workload

CREATE INDEX IF NOT EXISTS idx_m_type ON messages(culture, type, round, seq);
CREATE INDEX IF NOT EXISTS idx_m_rcpt ON messages(culture, recipient, seq);
CREATE INDEX IF NOT EXISTS idx_m_corr ON messages(culture, corr, type) WHERE corr IS NOT NULL;
CREATE UNIQUE INDEX IF NOT EXISTS idx_m_idem ON messages(culture, sender, idem) WHERE idem IS NOT NULL;

CREATE TABLE IF NOT EXISTS mentions(      -- derived index for wake-on-mention (rebuildable render)
  culture TEXT NOT NULL, agent TEXT NOT NULL, seq INTEGER NOT NULL,
  PRIMARY KEY (culture, agent, seq)) WITHOUT ROWID;

CREATE TABLE IF NOT EXISTS cursors(       -- Intercom-proven; + class column (§7.4)
  culture TEXT NOT NULL, agent TEXT NOT NULL,
  seq INTEGER NOT NULL DEFAULT 0, klass TEXT NOT NULL DEFAULT 'headless',
  updated_at TEXT NOT NULL, PRIMARY KEY (culture, agent));
```

**Write discipline.** One write connection per process; `BEGIN IMMEDIATE` for every post (write
lock up front ⇒ `next_seq` and the §5 chain read are race-free); WAL gives single-writer-at-a-time
across processes; `busy_timeout` queues the rest (E3). Readers never block writers; the viewer
opens `PRAGMA query_only=ON` connections (the live viewer already does).

**Housekeeping** (conductor cron, idempotent): `compact()` per §9 · `PRAGMA
wal_checkpoint(TRUNCATE)` on quiet · `PRAGMA incremental_vacuum` after big deletes · stale-cursor
report (>15 min; Intercom's liveness convention).

**Throughput honesty.** `synchronous=FULL` per gold commit on NVMe sustains ≫10³ posts/s; lived
fabric rates are 10⁰–10¹/s. The T0 bottleneck that matters is the write lock under fan-out storms —
bounded by `busy_timeout` + C10's backpressure assertion, not by fsync.

---

## §11 · T1 binding — NATS JetStream

### 11.1 Layout

- **Stream per culture:** `HC_M_<sanitized-culture>`, subjects `hc.m.<culture>.<type>` (type is a
  subject token ⇒ native type-filtered consumers for wake). **Stream sequence = culture `seq`:**
  contiguous at publish, gaps only where compaction purged — the same object as T0's per-culture
  seq (why L-ORDER chose the culture as the ordering domain).
- `file` storage; `replicas: min(3, cluster_size)`; `max_msg_size` default (1 MB) dwarfs the 32 KB
  body cap; `duplicate_window: 2m` with `Nats-Msg-Id: <sender>:<idem>` on idempotent posts.
- `ts` = the broker's ingest timestamp — L-CLOCK holds: the Medium stamps time.
- **Version floor:** run nats-server ≥ 2.12.12 on the 2.12 maintenance line or ≥ 2.14.3 (both
  2026-06-29) — the post-Jepsen fix train (PART E); older 2.12.x carry known filestore defects.

### 11.2 Durability classes, honestly

`sync_interval` is **server-level** (re-verified against docs.nats.io 2026-07-16; per-stream
granularity exists only by *placing* streams on differently-configured servers — machinery a ≤3-node
deployment won't carry); the default is 2m, and Jepsen showed that window loses acked writes
wholesale; single-bit `.blk` corruption losing 49.7% of acked writes remains an **open** issue
(#7549). Therefore:

- **D-gold does not rest on JetStream fsync at all.** Gold = PubAck + sealer consumption + fsync'd
  anchor append (§5.4), plus the producer-side nucleus journal for cell-posted gold. A JetStream
  durability lapse loses at most chatter and *re-postable* records; W4 drills exactly this.
- `sync_interval: always` (server-wide) is **recommended** where the write rate permits (it
  throttles to a few hundred msg/s — far above fabric rates) and treated purely as defense-in-depth.
- Replication ≥3 where the cluster has 3 nodes; at N=1 (the lived VPS case) the anchor rule *is*
  the durability story, and this binding says so instead of pretending.

### 11.3 The mirror — one read model, zero read-path divergence

The Conductor runs one durable consumer per culture (the **sealer**, §5.3) that materializes every
message into a **SQLite mirror with the exact §10 schema**. Consequences, all load-bearing:

1. Rich reads (`poll` with compound filters, `exists`, `verify`, every viewer query) execute the
   *same SQL* on both transports — the read path cannot diverge, so C1–C12 sharing one test file is
   structural, not aspirational.
2. The sealer computes the chain and the anchor in the same consumption loop — one consumer, three
   duties (mirror, seal, anchor).
3. The mirror is a **render**: delete it and re-consume the stream from seq 1 to rebuild (Fold Law).
4. Read-your-writes: `post()` returns the PubAck seq; a subsequent `poll` on T1 blocks until
   `mirror_head ≥ that seq` (bounded by seal lag; measured in W3).
5. Simple type-shaped waits (d1 cells) bypass the mirror entirely — direct `consume()` per §8.2 —
   so the mirror serves queries, never deliveries.

**Long-horizon idem dedup = dedup-at-fold.** The broker's `duplicate_window` kills racing
duplicates; beyond the window, the mirror's unique `(culture, sender, idem)` index ignores the later
copy and **every fold applies the same first-wins rule** — a duplicate past the window exists as
stream bytes but is VOID as a record (the same shape as void-at-fold, §6). `replay()` applies it
identically.

### 11.4 Consumer/cursor mapping

Per-agent cursors live in KV bucket `HC_CUR` (key `<culture>/<agent>`, CAS monotonic-advance); wake
consumers are ephemeral-durable (`InactivityThreshold` reaps them); the authoritative resume point
remains §7.4's `max(nucleus, transport)`. A KV regression under a broker durability lapse
re-delivers — at-least-once + the cursor law absorb it by design.

### 11.5 Backpressure

Publishers: bounded in-flight PubAcks; on flow-control/stream-limit refusal, exponential backoff
with jitter, then `MediumBusy`. Consumers: `max_ack_pending` bounds redelivery storms; a slow
consumer lags (pull), never drops. C10 asserts no-loss + bounded publisher latency.

---

## §12 · The conformance battery C1–C12 — runnable specifications

**The one-file law.** All twelve run from a single spec module, parameterized by a fixture
providing exactly (a) the `Medium` protocol (§7) and (b) a three-method `FaultInjector`:

```python
class FaultInjector(Protocol):
    def crash(self) -> None                 # kill the transport process(es) hard; reopen cold
    def corrupt(self, culture, seq) -> None # flip one byte of a stored record, below the API
    def sever_hint(self) -> None            # kill watchers / subscriptions; leave the log intact
```

Fault injection is *test-harness* contract, not Medium contract. **Any assertion beyond
(Medium ∪ FaultInjector) is a contract leak: the test is redesigned, never special-cased.**
Enforced by import-lint on the test module (it may import the two protocols and stdlib, nothing
else).

| # | name | SETUP | ACTION | ASSERT |
|---|---|---|---|---|
| C1 | total order | one culture; 8 concurrent posters × 200 msgs | posts race | every consumer's poll order == seq order; seqs strictly monotonic, dense (no compaction yet); identical across consumers |
| C2 | gold durability | 50 chatter posted, then 1 gold (`receipt`, as conductor) | `crash()` the instant `post()` returns; reopen | the gold record present WITH hash; any loss is a contiguous chatter-only *suffix* (§5.4 prefix-durability) |
| C3 | wake | waiter in `wait(types=[round_open])` | (a) post match, measure ×100; (b) `sever_hint()`, post match | (a) p95 ≤ 200 ms T0 / 500 ms T1; (b) received within one fallback tick — **zero loss, slower only** |
| C4 | claim-by-log-order | one `task`; 8 claimants | all `claim()`; kill winner; wait lease; challenger claims; zombie returns | exactly one `won=true` initially; steal succeeds after expiry with epoch+1; the zombie's own `claim()` result and the fold agree it lost |
| C5 | cursor persistence | consumer polls k of 2k msgs | `crash()` consumer side; reopen; poll | resumes at k+1 exactly: no skip, no re-delivery past cursor; nucleus-journal variant: wipe the transport cursor, still k+1 |
| C6 | filter correctness | 1k-msg corpus mixing types/recipients/mentions/corr | poll with each Filter axis + pairwise combinations | result set == reference full-scan filter; order == seq |
| C7 | liberal receiver | post `x-probe` type + a registry type bearing an unknown extra field | consumers poll; re-emit the polled record | no error; unknown type delivered + ignorable; unknown field round-trips byte-identical |
| C8 | idem dedup | post `(sender, idem)`; repeat identically — including after `crash()`+reopen | compare the two `Posted` | second returns `dedup=true` with the ORIGINAL seq; the log holds exactly one record; every fold sees one |
| C9 | replay equality | scripted 500-msg history exercising all 17 types | `replay(1..head)` vs accumulated `poll` batches vs a T0/T1 cross-run | identical canonical projections (excluding `ts`/`hash` timing); same seqs, same order, same bodies |
| C10 | backpressure | tiny consumer buffer; a 10k-msg burst | post storm | zero loss; publisher latency bounded or explicit `MediumBusy`; the lagging consumer recovers the exact sequence via its cursor |
| C11 | non-mintable ACL | a cell principal | attempt `receipt`/`verdict`/`oracle_gen`/`compact`/`command` posts; harness smuggles one below the gate | gate returns `AclDenied`; the smuggled record is **void-at-fold** — appears in no constitutional fold; `verify().void_by_acl` names it |
| C12 | chain verify + compaction | 300 msgs incl. TTL-expired chat; run `compact()` | (a) `verify()` pristine; (b) `corrupt()` one retained record; (c) verify across the hole; (d) inclusion-prove one archived record | (a) ok; (b) break located at exactly that seq; (c) ok through `compact.chain` + anchors; (d) proof validates against `merkle_root` |

**Acceptance bar:** C1–C12 green on T0 **and** T1 from the one file. "The wire survives the swap"
is thereby falsified-or-passed, never asserted.

---

## §13 · The multi-machine bridge (the culture membrane) — zero new mechanics

A paired relay: one bridge daemon per machine, each an ordinary bus client of its **local** Medium.
The bridge composes only existing primitives:

1. **Policy manifest** (per pair): `{peer, cultures:[…], types_allow:[…], direction: in|out|both,
   max_artifact_bytes}`. Directive types (`command`) MUST NOT appear in `types_allow` — directive
   authority never crosses a membrane inward.
2. **Outbound** = the relay `poll()`s its cursor over the local culture (§7 cursors give it crash
   resume free) and ships matching envelopes + artifact bytes to its peer. Channel transport and
   authentication: `[SECURITY-SEAM: bridge-channel]`, §16.4.
3. **Inbound** = the peer relay `post()`s each message locally with: `origin="external"` · **local
   re-sequencing** (`seq` is transport-local; `corr` is the cross-Medium thread) ·
   `idem = "bridge:<src_medium_id>:<src_seq>"` — exactly-once across the bridge is §7.1 dedup, no
   new machinery · original sender preserved in body; envelope `sender = bridge:<peer>`.
4. **Demotion law.** A `receipt`/`verdict`/`act_receipt`/`cmd_receipt` arriving `origin=external`
   is **DATA**: it satisfies no local convergence gate, seats no champion, settles no local
   command; folds treat it as evidence-class only. Upgrading remote receipts to warrant-class
   requires signature verification — `[SECURITY-SEAM: remote-warrants]`, §16.5.
5. **Artifacts:** bytes ≤ cap copy into the local sandbox; the relay recomputes `sha256` and MUST
   match the sender's claim, else the message posts with the artifact quarantined
   (`store:"quarantine"`) — a digest mismatch is never silently forwarded.
6. **Loop prevention:** a relay never forwards `origin=external` (single-hop federation; multi-hop
   needs routing and is refused until a falsifier demands it).

JetStream cross-domain stream *sourcing* may replace step 2/3's plumbing later — it also
re-sequences — but only behind the same conformance gate (BRIDGE-1). July-2026 note: MCP's
stateless streamable-HTTP and A2A's Linux-Foundation maturation live at the **fabric membrane**
(surfaces seat) and change nothing here — an agent-delegation protocol is not a log transport
(PART E).

---

## §14 · The viewer feed — named queries, all pure folds

`tools/medium_viewer.py` (live, stdlib, read-only `query_only=ON`) already implements the first
three; all are folds with L-FOLD-CLOSURE-checked input filters; the T0 SQL is the reference
realization and runs unchanged against the T1 mirror.

| query | fold over | live? |
|---|---|---|
| V-overview | per culture: count, senders, max round, first/last ts | ✔ |
| V-tail | messages after cursor (the viewer IS a poll client with advance=false) | ✔ |
| V-types | type histogram per culture | ✔ |
| V-run | `round_open/submission/receipt/verdict` → barrier state, receipts, champion | new |
| V-genealogy | verdict → receipts → submissions → evidence refs (provenance walk) | new |
| V-claims | the §7.3 fold: holder, valid_until, epoch, stale flags | new |
| V-acts | act corr groups: hold/exec/settle, outcomes, parked H3 queue | new |
| V-chain | verify tail: sealed_to, anchored_to, seal lag, breaks/void/zombies | new |
| V-compaction | compact records: spans, bytes reclaimed, archive refs | new |
| V-spend | sum over `cost{}` groups riding crossing records (`receipt`/`act_receipt`/`cmd_receipt`/`verdict`) — the fleet-visible attribution view; escrow truth-home is the Conductor's own ledger, never a Medium type (spend-home ruling #692/#694: no `spend` type exists) | seam |

**Class law (v2 §10, kept verbatim):** the viewer is constitutionally read-only — it renders
command *text*, never buttons; it holds no principal, so it cannot advance an interactive cursor.

---

## §15 · Migration from the live v1 medium

Live shape (E4, verified at `transport_local.py:23-25`): 9 columns, global `seq` (rowid), no chain,
no ACL, no cursors, WAL-only pragma. `hc medium migrate`:

1. Create the §10 schema alongside; copy each culture's rows in old-seq order, assigning per-culture
   dense seqs; preserve `ts/sender/recipient/type/round/body/artifact`; dropped-column fields null.
2. **No retro-minting.** Historical rows get `hash = NULL`; per culture, post a fresh
   `presence{phase:genesis}` carrying `{migrated_from, original_seq_range}` at the head; the chain
   starts there (`meta.chain_start_seq_<culture>`). Synthesizing historical hashes or receipts
   would be minting provenance — refused. `verify()` reports pre-genesis spans as "pre-chain,
   unverifiable", which is the truth.
3. Legacy `spawned`/`synthesis`/`judgment` rows are *read* through a fold adapter (the E1 mapping:
   → `presence{phase:spawned}` / `verdict{kind:synthesis}` / `receipt{check:panel}`) — bytes
   untouched; old tapes still play.
4. The merge (`announce`/`depart` → `presence`) is a **wire MAJOR** (0.1 → 5.0), legal exactly once
   as the spine-adoption epoch; the genesis census (§3.1) is what makes any later bump a readable
   event instead of an archaeology project.

---

## §16 · Security seams (what this contract NEEDS from identity-firewall.md)

The inverse of v3's `[SCOPED-OUT: security]`: each block states the need, the correctness mechanism
that stands meanwhile, and the seam owner (seat 10).

- **16.1 `[SECURITY-SEAM: sender-authn + acl-authn]`** — §2 sender binding and the §6.1 client gate
  are declared, not authenticated. NEED: the identity ladder's per-stage principal authentication;
  at Stage 1b, ed25519 signatures on privileged payloads **keyed off the SAME §3 ACL table** (one
  privilege source of truth — the signature requirement column is the ACL column). Meanwhile:
  void-at-fold (§6.2) keeps every fold correct against smuggled bytes.
- **16.2 `[SECURITY-SEAM: anchor-custody]`** — §5.4's anchor is the external trust point; its
  custody is the same trust root as receipts. NEED: custody/off-box placement policy and (Stage 2+)
  countersigning or transparency-log posting for non-repudiation. Meanwhile: anchor mismatch is
  still tamper-*evidence*.
- **16.3 `[SECURITY-SEAM: redaction]`** — §5.1's L-REDACT-BEFORE-CANON fixes the hook placement
  (before canon/append; the chain never witnesses a secret). NEED: the redactor itself (patterns,
  secret classes, verify-mode) — `secrets.py` is a 0-byte stub today. Meanwhile: the hook point is
  contract text; a null redactor is identity.
- **16.4 `[SECURITY-SEAM: bridge-channel]`** — §13 step 2's paired channel. NEED: transport
  authentication + encryption between relays. Meanwhile: policy manifest + digest re-verification +
  quarantine keep correctness.
- **16.5 `[SECURITY-SEAM: remote-warrants]`** — §13 step 4. NEED: signature verification to upgrade
  `origin=external` receipts to warrant-class. Meanwhile: the demotion law (remote receipts = DATA)
  is the safe default.
- **16.6 `[SECURITY-SEAM: sig-column]`** — §2.1 reserves the envelope placement, leaf exclusion,
  and verification rule. NEED: key registration/rotation/custody per principal. Placement is mine;
  keys are theirs.

---

## §17 · Failure-mode index

missed-wakeup race (§8.3 subscribe-first) · zombie claimant (§7.3 fold + §6 void) · double-post on
resume (§7.1 idem) · gold-only-copy-in-broker (§5.4 anchor) · chatter loss window (§5.4 suffix law —
bounded, declared) · compaction-vs-certificate race (§9 pin rule + L-FOLD-CLOSURE) · crash
mid-compaction (§9 idempotent re-run; zombies flagged) · cite-pinned row inside a purge span
(§9.2 step 6 keeper-aware delete) · mirror-lag read-your-writes (§11.3 blocking read) · registry
drift (§3 CI grep + C7) · ACL smuggling (§6 void-at-fold + C11) · WAL-on-network-FS (§10 placement
law + preflight G-DBLOCAL) · secret-in-chain (§5.1 redact-before-canon) · duplicate-past-window
(§11.3 dedup-at-fold).

*— end of contracts/wire.md v5.1 —*

