# CONTRACT: nucleus — the cell's ledger, renders, memory, frames, fork, consolidation

**Version:** 5.1.0 · **Status:** RATIFIED-DRAFT (v5 wave) · **Date:** 2026-07-16 · rev 2026-07-25 (P3 resolution)
**Contract:** `nucleus` · **Pairing:** Nucleus (noun) — governs `persist` (_TEMPLATE-HEADER.md H2 row 2)
**Emit/read:** strict-emit / liberal-read (H4) · **Operator boundary:** strict-both (R5)
**Schema mirror:** `contracts/schemas/nucleus.schema.json` (same-commit, H1)
**Migrates from:** live v1 `cell/nucleus.py` + contracts v0.1 (§14) · **Falsifiers:** NUC-1..NUC-10 (§15)
**Replaces:** v0.1 stub (live repo) + v3 draft (wave paper §N1–N6)
**Pairs with:** `contracts/role.md` 5.0 (the knobs) · `contracts/wire.md` 5.x (xref targets, artifact
pointer) · `contracts/act.md` 5.x (fsync-before-effect consumer) · `contracts/identity-firewall.md` 5.x
(trust tags, redaction rules) · JSON-Schema mirror at `contracts/schemas/nucleus.schema.json`.
**Register:** RFC-2119. **Reader liberality (G4):** emitters write exactly this shape; readers MUST
ignore unknown *fields* and unknown *kinds* (folds return state unchanged on unknown kinds), MUST NOT
error on either, and MUST preserve unknown fields when re-serializing. A field's *absence* is never a
version probe — the genesis census (§1) is.

> The nucleus is two things and only two: the **Ledger** (truth) and **Renders** (model-free,
> deterministically rebuildable views). Every token a cell ever sees or says traces to a ledger record.
> Delete any render and the cell loses speed, never truth.

## §0 · Identity & storage layout

A cell is a **durable identity, not a process**: the stable **claim-id** `run/role/index` (e.g.
`r7/refiner/3`; `common/ids.py:43-45`) names it; an ephemeral **instance-id** names one instantiation.

The nucleus home is a **directory on a shelf**, keyed by claim-id:

```
<SHELF>/<claim-id>/
  ledger.jsonl                    # the active segment (truth)
  sealed/seg-000001.jsonl         # sealed segments: immutable, chmod 0444
  sealed/seg-000001.meta.json     # {first_seq, last_seq, first_hash, last_hash, sha256_file}
  artifacts/sha256-<hex>          # spilled bodies (§2.3)
  index.db                        # render #0 (disposable)
  renders/<name>/                 # further renders (disposable)
```

**Shelf binding derives from SANDBOX CLASS, never depth** (substrate contract): a pooled cell (class
0/1) is a directory on the shared runner PVC; class-2/3 isolation gets a dedicated PVC. On any substrate
the shelf MUST be a node-local POSIX filesystem with honest fsync (ext4/xfs; never a network filesystem,
never `/mnt/c` under WSL2 — G-DBLOCAL). The v0.1 phrase "its PVC" is REPLACED by this paragraph.

## §1 · The genesis record (seq 1, exactly once, gold)

Every ledger opens with `genesis`. A spawn against a claim-id whose Medium history shows prior receipts
but whose nucleus lacks a genesis (or fails chain verify) MUST be REFUSED — the
empty-nucleus-under-live-identity corruption is a mechanical check, not a hope.

```jsonc
{ "claim":        "r7/refiner/3",
  "lineage_root": "r7/refiner/3",        // own claim if root; inherited if forked
  "role_digest":  "sha256:…",            // sha256(canon(role manifest)) at instantiation
  "contract":     {                      // THE CENSUS: which contract versions wrote this ledger's
    "wire": "5.0", "nucleus": "5.0",     // records. ALWAYS the FULL 9-TUPLE — all nine contract
    "role": "5.0", "run": "5.0",         // axes (_TEMPLATE-HEADER.md H2/H5.1) as nine short
    "command": "5.0",                    // strings, at EVERY depth that has a ledger at all
    "identity-firewall": "5.0",          // (d0 has none — §3.1). A partial census is refused at
    "oracle": "5.0", "act": "5.0",       // spawn, never defaulted. In-chain ⇒ tamper-evident ⇒
    "pricebook": "5.0"                   // foldable (kernel law).
  },
  "created_by":   "conductor",           // conductor | operator
  "run_id":       "r7",
  "forked_from":  null,                  // or {claim, seq, head_hash, parent_sealed_segment_digest}
  "prefix_ref":   null }                 // or the borrowed-segment manifest (§10)
```

- Later version transitions append `contract_bump {from, to, migration_note}` INSIDE the chain — a
  version epoch declared outside the chain can be retro-claimed; inside it, it cannot.
- **Synthetic genesis (HONEST-EPOCH pattern, shared with trust's oracle_gen-g0):** a pre-chain ledger
  adopts the chain by appending a genesis carrying `"chain_adopted_at_seq": k`; records `< k` are
  immutable-but-unhashed and the contract says so rather than pretending tamper-evidence predates itself
  — and the migration binds an **operator-signed Merkle baseline** over that region (§14 step 1), so
  "immutable" is checkable against a signed root, never merely asserted.

## §2 · The record envelope, canon, and the hash chain

```jsonc
// Every ledger record. JSONL, one per line, UTF-8, append-only. Migration from live v1: see §14.
{ "v":    5,                              // nucleus contract major
  "seq":  42,                             // 1-based, dense, monotonic. THE order. Never order by ts.
  "ts":   "2026-07-16T04:31:07.114Z",     // UTC ISO-8601 ms (common/clock.py); informational only
  "kind": "action",                       // §3 taxonomy
  "idem": "act_01H…",                     // nullable; the exactly-once key
  "refs": [17, 23],                       // prior seqs this record depends on (strictly < seq)
  "red":  null,                           // OPTIONAL redaction note, ANY kind: [{path, rule}] — the
                                          // membrane redacted body content pre-append; absence is
                                          // auditable (identity-firewall.md owns the rule set)
  "body": { … },                          // kind-specific (§3); >8 KB or binary → artifact spill
  "prev": "sha256:…",                     // previous record's hash (hex)
  "hash": "sha256:…" }                    // chain column — construction: wire.md §5.1 (one home)
```

- **Chain construction (ONE home, MUST):** the per-record recipe — the canonical leaf (record sans
  `hash`/`sig`) and the raw-digest chain step — is defined in **wire.md §5.1** and nowhere else; this
  contract CITES it and never restates it. The nucleus ledger uses the same canon + leaf + chain
  construction as the Medium's per-culture chain: one verifier, two logs.
- **canon()** = RFC-8785 (JCS): sorted keys, no insignificant whitespace, UTF-8. ONE shared
  implementation `common/canon.py` serves this chain AND the Medium's per-culture chain — one `hc verify`,
  two logs. Hashed bodies SHOULD carry money as integer micro-USD and durations as integer ms (floats
  are cross-language canon hazards).
- **Anchors:** root cells `prev₀ = sha256("hypercell/nucleus-chain/1" ‖ 0x00 ‖ claim_id)`; forked
  children `prev₀ = parent.hash(at_seq)` — the chain crosses the fork, so a spoofed `forked_from` fails
  child-chain verify. **The chain-construction constant is versioned independently of this contract**
  (seat-03 law, adopted): a nucleus.md MAJOR bump never re-anchors existing chains; changing the hash
  algorithm bumps the chain constant (`…/nucleus-chain/2`) and is declared by a `contract_bump`. The
  chain is tamper-*evident*, not tamper-*proof*; the d3 Medium-anchor pattern and the signed `hc export`
  (identity-firewall.md) bound the same-box-rewrite window.
- **Artifact spill:** a body > 8 KB or non-text becomes
  `{"artifact": {"rel": "artifacts/sha256-…", "sha256": "…", "bytes": n, "mime": "…"}}`; the record hash
  covers the artifact's sha256, so tamper-evidence extends to spilled bytes. Model reasoning traces MAY
  spill (role-config), never inline.

## §3 · The kind taxonomy — 19 kinds, 4 families (closed; unknown kinds ignored by folds)

| family | kind | body essentials | durability | writer |
|---|---|---|---|---|
| io | `percept` | `{source: operator\|medium\|tool\|wake\|resume, trust: operator\|receipted\|tool\|external, medium?: {culture,seq}, content\|artifact, part?: {i,n}}` | standard | runtime |
| io | `decision` | `{chosen, why, options?}` — model-authored choice (d2+, OPTIONAL) | standard | runtime |
| io | `action` | `{verb, args…, harm_class?, capability_ref?, cost_est?}` | **gold if H1+** | runtime |
| io | `outcome` | `{of: verb, result\|artifact, model?, usage {prompt,completion,cache_read}, cost {usd_micro, wall_ms}, error?}` | gold iff its action was gold | runtime |
| control | `genesis` | §1 | **gold** | runtime, once |
| control | `checkpoint` | `{state: {…}, medium_cursor?: {culture: seq}}` | **gold when ack-bearing** | runtime |
| control | `nucleus.stats` | `{span:[lo,hi], appends, p50_ns, p95_ns, bytes, fsyncs, group_commits}` | standard | nucleus (§12) |
| control | `parked` | `{reason, by_run, final_score?}` — metadata, NEVER load-bearing for resume | gold | runtime on park |
| control | `repair` | `{torn_bytes, after_seq, quarantined_to}` (§8) | gold | nucleus on open |
| control | `contract_bump` | `{from, to, migration_note}` (§1) | **gold** | runtime at migration |
| memory | `memory.assert` | `{memory_id, register: factual\|narrative, content, s?,p?,o?, entities?, valid_from?, valid_to?, xrefs?: []}` — grounding refs ride envelope `refs[]` | standard | verbs (§6) |
| memory | `memory.supersede` | assert body + `{target_memory_id}` — atomic replace | standard | verbs |
| memory | `memory.retract` | `{target_memory_id, mode: ended\|error, valid_to?, reason}` | standard | verbs |
| memory | `memory.pin` | `{target_memory_id, on: bool, order?}` | standard | verbs |
| memory | `memory.forget` | `{target_memory_id, reason}` — render tombstone; ledger retains | standard | verbs |
| memory | `memory.recall` | `{query, k, filters, results: [memory_id…], render, render_head_seq}` — journaled READ; no fold consumes it | standard | verbs |
| structure | `frame` | the frame manifest (§7.5) | standard | assembler |
| structure | `fork.child` | `{child_claim, at_seq, reason, run_id}` (parent side; child side = its genesis) | **gold** | fork (§10) |
| structure | `consolidation` | `{span:[lo,hi], digest_artifact, asserts:[seq…], cold_eyes:{family,verdict,score}, installed: bool}` | gold on install | consolidation Step (§11) |

Removed v0.1 kinds: `handoff` (compiles to `checkpoint` + a Medium `handoff` post), `system` (each use
compiles to a named kind). Waking is perceiving: `percept{source: wake, body:{reason, waited_ms, filter}}`.

**Trust tags (`percept.trust`) are stamped by the membrane at ingress, before append** — operator
console ⇒ `operator`; receipted/privileged Medium types ⇒ `receipted`; the cell's own tool results ⇒
`tool`; everything else (peer chat/submissions, fetched web content) ⇒ `external`. The tag is DATA the
register wall (§6), frame provenance lines (§7), and evidence bundles (§6.2) consume; the firewall
contract owns the stamping rules. A record whose trust tag is absent reads as `external` (fail-closed).

### §3.1 Lawful degeneracy — the record ladder (NUC-9)

- **d0 = 0 records.** No nucleus exists; the call is one line in the Culture run-log on the Medium.
- **d1-adhoc (`hc ask`) = 2 records:** `action{idem}` + `outcome{idem}`. The live 5-record pattern
  (`runtime.py:45-51,63-73`) is ceremony the code itself doesn't need: `pending()` detects in-doubt work
  by action-without-outcome (`nucleus.py:106-116`), not by checkpoint.
- **d1-worker** adds percepts + checkpoints as the loop needs them; **d2+** uses the full taxonomy.
- **THE READ-BARRIER INVARIANT (MUST):** at every rung ≥ 2 records, the verb executor consults
  `outcome_for(idem)` BEFORE issuing cognition/effects and returns the stored outcome on hit. A 2-record
  verb without the barrier is F17 (live `produce()`, `runtime.py:83-101`), not degeneracy. The
  one-verb-executor (kernel contract) is the single place this lives.

## §4 · Durability — two laws, one group-commit

- **LAW-FSYNC-EFFECT (MUST):** an H1+ `action`'s `append()` does not return until fsynced; the effect
  executes only after return. (Enforcement point: the nucleus append path — act.md consumes this.)
- **LAW-FSYNC-ACK (MUST):** the `outcome` + `checkpoint` of a completed step are fsynced before the cell
  reports done on the Medium.
- **Group-commit for everything else:** appends buffer in-process; flush = write-all + one fsync,
  triggered by (a) any gold record (one fsync covers buffered standards), (b) a 25 ms window, (c) 64 KB
  buffered. Standard `append()` returns after the buffered write.
- **LAW-CURSOR-IN-CHECKPOINT (MUST):** a cell's Medium cursor advances only inside a `checkpoint`
  record. Losing a standard tail therefore loses only re-derivable records: an unadvanced cursor
  re-delivers the percepts. (Journal-before-use, made mechanical.)
- **LAW-ASYNC-MIRROR (MUST — new in 5.0, F28):** renders (including index.db) are updated OFF the
  append path — async or batched; the fold cursor (§5) guarantees catch-up on open. The append path
  performs exactly ONE durable write per flush (the ledger's). Live v1 does two synchronous durable
  writes per record (`nucleus.py:67-82`); §14 migrates.
- **Substrate reality (F4):** preflight runs a 1 K-append gold bench; a shelf that cannot deliver gold
  fsync p95 ≤ 50 ms is DEGRADED (substrate contract).
- `memory.fsync: always` (role.md) restores the v1 fsync-every-append behavior wholesale.

## §5 · Renders — fold / open / rebuild / verify (the Fold Law, cell-side)

```python
class Render(Protocol):                  # every render registers name + semver
    name: str; version: str              # fold_version = f"{name}/{version}"
    def init(self) -> S: ...
    def fold(self, s: S, rec: Record) -> S: ...   # PURE + TOTAL: unknown kinds → s unchanged
    def finalize(self, s: S) -> View: ...
    def digest(self, s: S) -> str: ...            # canonical content digest (not the ledger hash)

def rebuild(ledger, r) -> View:          # from zero; the reference path
    return r.finalize(reduce(r.fold, ledger.records(), r.init()))

def open(view_dir, ledger, r) -> View:   # THE HOT PATH — O(delta), never O(ledger)  [F21]
    # load the render's own _render_meta(name, fold_version, last_seq, state_digest);
    # fold only records > last_seq; missing meta or fold_version mismatch ⇒ rebuild from zero.
    # THE CURSOR LIVES INSIDE THE RENDER: _render_meta commits in the SAME transaction as the
    # folded content (SQLite: one txn; file renders: one atomic rename) — a sidecar can desync,
    # one transaction cannot.

def verify(live, ledger, r) -> {ok, at_seq?, diff}:
    # SCHEDULED (d2+), never the open path: rebuild a shadow, compare digests; on mismatch bisect
    # using fold-state digests snapshotted every K=4096 records.
```

**DETERMINISM LAW (MUST):** `fold` reads nothing but `(s, rec)` — no model, no clock, no RNG, no
network, no environment. Same ledger prefix ⇒ byte-identical digest on any machine. Query-time
parameters (`now`, `as_of`) are **arguments to the view**, never read inside fold. A render is
disposable by definition.

### §5.1 Registry per depth

| render | what | depth | status |
|---|---|---|---|
| `index` (#0) | SQLite mirror (`records` + idem/kind indexes + memory projection) | d1+ | LIVE — contract-completes (pragmas: WAL, `busy_timeout=5000`, `synchronous=NORMAL` — the *ledger* carries durability, the render need not, E3) |
| `fts` | FTS5 over memory content + outcomes — recall's floor, consolidation-independent | d2+ | add |
| `tkg` | temporal knowledge graph (§5.2) | d3 (d2 opt-in) | add, **dark** until NUC-3 |
| `stats` | rolling persistence-cost view over `nucleus.stats` | d1+ | add (feeds NUC-7) |

### §5.2 The temporal-KG render (bitemporal fold; semantics adopted, dependency refused)

Each fact version carries **valid time** (`valid_from`/`valid_to` — true in the world) and
**transaction time** (`tx_from` = seq of assert, `tx_to` = seq of supersede/error-retract — believed by
the cell). Zep/Graphiti's `(valid_at, invalid_at, created_at, expired_at)` ≙ ours; their license
(Apache-2.0, re-verified 2026-07) permits import — we still refuse the dependency and fold ~150 lines
over our own `memory.*` records (reference fold: v3 paper §N2.4, adopted verbatim into
`renders/tkg.py`). **THE CONTRADICTION LAW:** two live versions of a one-valued edge are returned
*both, flagged* — the render never last-write-wins and never auto-resolves (Graphiti's LLM
edge-invalidation is precisely the refused dependency; a render resolving silently mints trust).
Resolution is the cell's explicit, journaled `revise`.

**Generative renders stay legal by JOURNALED EXTRACTION:** extraction (entities/relations/validity) is
a model Step whose outputs enter the ledger as `memory.assert` records at assert time, fully validated
(§6); `fold` replays recorded assertions and never re-extracts. Embedding vectors are model output:
journaled as artifacts keyed `(model_id, content_sha256)`; a lost vector degrades that item to FTS —
speed lost, truth kept.

**NUC-3 dark launch (MUST before the tkg serves recall):** shadow-serve next to FTS for ≥2 weeks of
resident traffic or a ≥500-query golden set (operator-curated + LongMemEval-V2-style slices across its
five abilities: static-state recall, dynamic-state tracking, workflow knowledge, environment gotchas,
premise awareness). Bars, ALL required: temporal precision@k ≥ FTS+10 pts; p50 recall ≤ 2× FTS;
retrieved-token cost ≤ 1.1× FTS. A losing render stays dark or is deleted.

## §6 · Memory-as-tool — verbs, registers, write-time enforcement

Membrane-internal tools, never advertised on the Medium. Five verbs → six record kinds:

| verb | record | semantics |
|---|---|---|
| `remember(content, register=narrative, refs=[], xrefs=[], s?,p?,o?, entities?, valid_from?, valid_to?)` | `memory.assert` | file a memory; factual requires validated grounding |
| `recall(query, k?, register?, as_of?, now?)` | `memory.recall` | journaled read; returns memories WITH provenance (register, refs, terminal trust tags, validity, contradiction flags) |
| `revise(target, content?, mode?)` | `memory.supersede` \| `memory.retract` | atomic correction; the old version stays queryable as-of the past |
| `forget(target, reason)` | `memory.forget` | render tombstone; ledger retains (true erasure: identity-firewall.md) |
| `pin(target, on=true, order?)` | `memory.pin` | consolidation-immune + S0-eligible; over `pin_budget` ⇒ E_PIN_BUDGET (unpin something first) |

### §6.1 The register wall (write-time CODE, not prompt)

`factual` = refs whose closure terminates in non-decision records. `narrative` = model-authored lossy
compression — legal, useful, **cite-blocked** in oracle-facing artifacts (the block keys on
`register == narrative`, never refs-absence). Default register is `narrative`: a sloppy cell mints
style, never fake facts.

**SEMANTICS, stated honestly (MUST appear in operator docs):** factual means
**auditable-to-terminal — never true**. A factual memory citing a poisoned `percept{trust: external}`
is legitimately *witnessed*; its content is still untrusted input. What the wall guarantees is that the
provenance class of every claim is mechanical: recall provenance lines, evidence bundles, and audits all
surface each terminal's `trust` tag, so a "fact" grounded only in external content is *visibly* so —
to the cell, to the oracle's entailment sample, and to the operator. [SECURITY-SEAM: the firewall
contract owns trust-tag stamping; this contract owns their propagation.]

```
VALIDATE-FACTUAL-ASSERT(record):                       # inside remember(); atomic with append
 1. refs ∪ xrefs non-empty                              → else E_REG_NO_REFS
 2. every local ref r: 1 ≤ r < this.seq                 → else E_REG_BAD_REF (only the past is citable)
 3. closure walk (stack, visited-set, depth ≤ 8):
      terminal-OK: percept{source ∈ operator|medium|tool}         (witnessed input, trust tag rides)
                   outcome of action{verb: act}                    (receipt-backed world result)
                   percept{source: operator} carrying a command    (operator authority)
      factual memory.assert → recurse into ITS refs               (factual chains allowed)
      DECISION-CLASS → E_REG_DECISION_REF(path): decision · action{ask|produce} · outcome of
                   ask|produce (model text — self-citation is trust minted inside the fabric) ·
                   narrative assert · checkpoint · frame · consolidation
      depth > 8 → E_REG_TOO_DEEP(path)
 4. xrefs (cross-boundary URIs):
      medium://culture/seq  → admissible iff the referenced type is in the wire registry's
                              NON-MINTABLE (warrant-class) set — **wire.md §3 names it; this
                              contract cites it and never hard-codes it** (the set = the
                              mint-restricted types that CERTIFY a boundary crossing) — another
                              model's assertion (submission/chat/status) is never grounding
      act://corr            → ok (a citation IS a pointer to an act-receipt)
      https://…             → REJECTED unless resolvable to an act://corr that fetched it
 5. rejection returns the typed error + path (transcript-visible); the cell MAY re-file as narrative;
    the nucleus never silently downgrades.
```

Cycles impossible by construction (rule 2); the walk is O(8·branching) against a warm index.

### §6.2 The evidence-bundle export (privacy-preserving walkability)

A3 keeps the nucleus private; the oracle cannot walk `nucleus://` refs. At submission time the membrane
packages every cited memory + its terminal ref-closure content-hashes as ONE artifact:

```jsonc
{ "claim": "r7/refiner/3", "ledger_head": {"seq": 1201, "hash": "sha256:…"},
  "cited": [{ "memory_id": "m_01H…", "register": "factual", "content": "…", "asserted_seq": 812,
              "terminal_refs": [{"kind": "act_receipt", "locator": "act://01H…", "sha256": "…",
                                  "trust": "receipted"},
                                {"kind": "percept", "locator": "nucleus://…/git401", "sha256": "…",
                                  "trust": "tool"}]}] }
```

The exporter **refuses `register: narrative` at packaging** — a narrative citation never reaches the
wire. Terminal `trust` tags ride the bundle (5.0 addition). The oracle validates hashes + samples
entailment with zero nucleus access; `nucleus://` stays the operator-audit pointer (`hc peek` checks
bundle-vs-ledger byte equality; a mismatch at audit = fabricated warrant, the L-NO-NAKED-CLAIMS stain).

## §7 · Frame assembly — deterministic, manifested, cache-shaped

The frame is rebuilt from the nucleus each tick by deterministic nucleus code. **Nothing is injected
silently:** every prompt token traces to the role manifest, a ledger record, or a transcript-visible
tool result.

### §7.1 Sections and stability classes

| § | section | contents | stability |
|---|---|---|---|
| S0 | identity | role prompt (head, mandatory) + pinned memories (pin order) | stable |
| S1 | tools | tool schemas for `role.tools` (ride the API `tools` param; budgeted here) | stable |
| S2 | digest | all installed digests, oldest→newest (pre-chunked ≤512 tok) | semi-stable |
| S3 | working | last `checkpoint.state` + open task records | volatile (slow-churn; budget-droppable per §7.2 step 5) |
| S4 | retrieved | assembly-time recall results WITH provenance lines (`[factual · trust:tool · nucleus://…/812]` / `[narrative — not citable]`) | volatile |
| S5 | recap | last `recap_k` io records verbatim, oldest→newest | volatile |
| S6 | percept | the new input (paginated if oversize; never silently truncated) | volatile |

**Open tasks (S3)** = `pending()` items plus the percepts of Medium tasks this cell holds an
unexpired claim on (from `checkpoint.state`).

d0 bypasses the assembler: frame = `role.prompt + percept`, two strings, zero nucleus reads.
Ratio defaults per depth live in **role.md §3** (one table, not duplicated here).

### §7.2 ASSEMBLE (normative, numbered)

```
ASSEMBLE(nucleus N, role R, percept P, window W) → (frame_bytes, manifest):
 1. W_use ← W.context − W.max_output − 256
 2. B[s] ← ⌊R.frame.ratios[s] · W_use⌋ for s ∈ S0..S6; slack ← W_use − ΣB
 3. gather candidates at ledger head h (recorded in the manifest):
      S0 [R.prompt(mandatory)] ++ pins by (pin_order, mid) · S1 tool schemas in role order (mandatory)
      S2 all installed digests, oldest→newest · S3 last checkpoint.state + open tasks
      S4 RECALL_ASSEMBLY(N, DERIVE_Q(P,S3), k=R.memory.recall_k) · S5 last recap_k io records · S6 P
 4. score non-mandatory items with SALIENCE (§7.3); mandatory ⇒ +∞
 5. pack S0..S6 in order; within a section sort (salience ↓, seq ↓, id ↑); take WHOLE items while
    Σtok ≤ B[s]; record every drop {ref, tok, salience, reason}.
    HYSTERESIS: budget drops apply to VOLATILE sections (S3–S6) ONLY. S0/S1/S2 item sets are FIXED
    between declared boundaries (role change, pin op, consolidation install); S0+S1+S2 over budget is a
    ROLE-MANIFEST ERROR refused at spawn/pin/install time — never a silent runtime drop.
 6. spillover: leftover re-offered in fixed order [S6, S4, S5] — volatile only (spillover into S2 would
    break the semi-stable prefix between installs).
 7. if est(S0) + est(first page of S6) > W_use → frame_error manifest, abort tick (operator-visible).
 8. frame ← join(sections, fixed delimiters); tag each segment stable|semi|volatile. The assembler
    does NOT place cache breakpoints: breakpoints are lane-dependent facts (per-provider mechanics +
    per-model minimum cacheable sizes drift quarterly — July-2026 table in the pricebook annex); the
    provider adapter inside the metered path maps stability tags → that lane's controls and VALIDATES
    stability-monotone order fail-closed. Assembler owns ORDER + TAGS; econ owns REALIZATION.
 9. manifest ← {tick, ledger_head: h, window: {context, max_output, W_use},
                segments: [{name, class, sha256, tokens, items: [{ref, tokens, salience}], dropped}],
                prefix_hash_stable, prefix_hash_semi, est_tokens_total,
                versions: {assembler, salience, estimator}, digest: sha256(frame)}
10. append kind=frame (standard durability); return.
Overflow (estimator undershot): re-run once at W_use·0.9; both manifests recorded.
```

### §7.3 Deterministic subroutines

- **RECALL_ASSEMBLY(N, q, k):** = the §6 recall query path (FTS floor; tkg only if NUC-3-passed),
  both registers (narrative marked not-citable), as_of=now, UNJOURNALED — the frame manifest's
  `segments[S4].items` IS its durable record; ledger `memory.recall` records are minted only by the
  model-initiated verb.
- **DERIVE_Q(P, S3):** content words of P (pinned tokenizer + stopword list, versioned) ∪ entity keys of
  open tasks → an FTS5 query. The model can want more: mid-tick `recall` tool calls are the sanctioned
  path — journaled, transcript-visible, accounted next frame. Assembly itself never asks a model.
- **SALIENCE_v1:** `4.0·pinned + 2.0·(register=factual) + 1.5·jaccard(entities, working.entities) +
  1.0·exp(−(h−seq)/half_life) + 0.5·ln(1+recall_count)`; weights from `role.frame.salience`; ties →
  newer seq, then id. Versioned: a weight change bumps `salience/1.x` in every subsequent manifest.
- **Token estimator:** pinned + versioned (`bytes4/1.0` floor; bundled tokenizer when the lane is
  known); error absorbed by slack + the step-10 retry.

### §7.4 Byte-stability & hysteresis (the cache seam — settled with econ)

**BYTE-STABILITY LAW:** S0+S1 MUST be byte-identical across ticks within a `(role_digest, pinset_hash)`
epoch; S2 changes ONLY at consolidation installs; installs happen ONLY at task boundaries. S1's
canonical bytes (tool schemas in role order, JCS) enter `segments[S1].sha256` and the stable-prefix
hash but are REALIZED as the API `tools` param, never concatenated into prompt text. **Both bars
hold together:** byte-identical-frame determinism AND the ≥60% cache-hit rate — passing one while the
other dies is a fail. The manifest's `segments[].sha256` + `prefix_hash_stable/semi` +
`est_tokens_total` let the economics plane predict hits, reserve exactly, and attribute every miss
(first-differing-segment-index ⇒ assembler bug; S0 delta ⇒ pin churn; S2 delta ⇒ install timing; no
delta yet cold ⇒ provider TTL eviction). Adapter-side validation includes the lane's
`min_cacheable_tokens` (per-model, 512–4096 across July-2026 lanes): a stable prefix under the lane
minimum is reported `cache-ineligible`, never silently uncached.

### §7.5 Determinism & the audit query

Same `(ledger prefix ≤ h, role_digest, P, W, versions)` ⇒ byte-identical frame. "Why did the cell not
know X at tick t?" is one query over `frame` records: X's ref is in `segments[].items` (knew), in
`dropped` (budget, with the losing salience), or in neither (never gathered — DERIVE_Q names why).

## §8 · Torn tails, repair, what never enters

- **Secrets NEVER enter the ledger.** The membrane redaction pass runs before EVERY append (any kind);
  the envelope `red` field notes what was redacted so the absence is auditable. Pattern set + custody:
  identity-firewall.md.
- **Torn tail:** on open, a last line failing JSON parse or hash verify moves to `ledger.torn-<ts>`;
  append `repair{…}` (gold); continue. Anything above the torn line was unacknowledged (group-commit) or
  pre-effect (gold law) — truncation is safe by construction.
- **Disk-full:** gold append raises BEFORE any effect (fail-stopped; `status: degraded` to the Medium).
- **Clock skew:** `ts` is informational; `seq` is order. **fsync-lying hardware:** preflight probes;
  the d3 anchor pattern bounds the damage window.

## §9 · Segmentation & retention

Never rewritten, never pruned — but physically segmented, logically one chain. Rotation seals at
`segment_mb` (default 64) or on fork: flush+fsync, write meta sidecar, chmod 0444, rename. The chain
crosses segments (`prev` of a segment's first record = prior meta's `last_hash`). Sealed segments MAY
move to cold storage behind a redirect stub. Readers iterate sealed-then-active; `verify_chain` walks
the same way.

## §10 · Fork/COW — MCTS over agent state; lineage as a pure fold

```
FORK(parent, child_claim, at_seq = head):            # runner/conductor-driven (privileged side)
 1. take the parent's append lock (no gold append mid-fork)
 2. FORK-FORCES-SEAL (privileged): the runner — never the cell — rotates + seals the parent's active
    segment (fsync, meta, chmod 0444). A cell NEVER holds an append fd to a sealed segment. Idempotent:
    concurrent forks share one rotation.
 3. parent appends fork.child{child_claim, at_seq, reason} — GOLD
 4. child dir + BORROWED-SEGMENT MANIFEST — the universal mechanism is LOGICAL:
    prefix_ref = {segments: [{segment_id, content_hash}], partial?: {segment_id, upto_seq}}.
    Hardlink is the same-filesystem fast path only (EXDEV across filesystems); same-shelf siblings
    hardlink free; cross-node forks materialize by copy/fetch verified against content_hash. Mid-history
    at_seq copies nothing: readers stop at partial.upto_seq.
 5. child genesis{forked_from: {claim, at_seq, head_hash, parent_sealed_segment_digest},
    lineage_root: parent.lineage_root, prefix_ref} — GOLD; child chain prev₀ = H(at_seq).
 6. RENDERS ARE NEVER SHARED ACROSS FORK: the child folds its own renders over prefix-then-own.
    fork_render_policy per run manifest: {rebuild | ledger-only-until-recall} (lazy default — unexpanded
    MCTS siblings stay free; d2+ MCTS width caps price render-rebuild).
Cost: O(1) + one rename + one genesis write (same-shelf). Bars: NUC-10.
```

- Lineage lives in BOTH ledgers (parent `fork.child`, child `genesis.forked_from`, both gold). The
  Conductor never reads a nucleus (A3): its lineage index folds from spawn commands + Medium posts —
  the Medium-side fork signal (`presence{phase:spawned, forked_from}`, wire.md §3) rides **D-gold**:
  lineage provenance is never chatter-class (s2-28) — and is a *render*; `hc verify` audits
  index-vs-ledger. Lineage-scoped exactly-once keys
  `(lineage_root, effect_id)`; instance-scoped keys `(claim, step)` re-fire per branch by design.
- **Fork is a ledger op, never a volume op.** Filesystem/CSI snapshots serve backup only.
- **Parked, not deleted:** on prune the cell writes `parked{…}` (gold) and departs; the Conductor MAY
  move the nucleus to `parked/` (refcounted sealed segments are never deleted while a child references
  them). The parked record is metadata: a crash-park writes nothing and resume works identically.
  `spawn --from-snapshot` resurrects a stepping stone (the Darwin-Gödel archive for free).

## §11 · Consolidation — a scheduled Step; the death spiral structurally impossible

Buys frame economy, never truth (recall falls back to FTS over raw records). d2+ only — sleep-time
compute pays ~5× test-time reduction and ~2.5× lower cost-per-query only when queries share context
(re-verified 2026-07; PART E #4), which is what "resident" means.

```
CONSOLIDATE(cell):                                   # command-triggered Step, maintenance lane
 0. eligibility: depth ≥ d2 ∧ idle ≥ idle_s ∧ (records_since ≥ min_records ∨ tokens_since ≥
    min_tokens) ∧ governor grants a maintenance reservation (≤ budget_pct of lifetime)
 1. span ← [last_consolidated_seq + 1, head_at_start]
 2. INPUT-SET LAW (structural anti-death-spiral): the Step's frame uses a fixed maintenance profile
    [identity, PRIOR-DIGEST-AS-GUIDE (marked, never a source), RAW SPAN RECORDS, instructions] — no
    digest-only profile EXISTS; a zero-raw-record pass is impossible by construction.
 3. one cognition call (family L1, cheap/local lane) → (a) digest artifact — REEL 5-field: what
    happened / what changed / what matters / what's unresolved / retrieval anchors — pre-chunked
    ≤512 tok; (b) proposed memory.asserts, each ref'ing into the span — §6.1 validation UNCHANGED (a
    consolidation pass gets no register privileges); (c) decay proposals (unreferenced across k passes
    → salience floor drop; never deletion; pins immune).
 4. COLD-EYES: one call on family L2 ≠ L1, where **L2 ROTATES per pass over the available ≠L1 set**
    (5.0 delta: a fixed pairing can settle into a correlated blind spot; rotation applies F1/F9 over
    time). Input = digest + deterministic sample of span raw records (every j-th + all gold). Grades
    entailment + material omission → {pass|fail, score, notes}.
 5. pass → append consolidation{…, installed: true}; the digest INSTALLS at the next task boundary
    (S2 swap — the cache seam depends on it). fail → installed:false (prior digest stays live); retry
    with a different L1; 2 consecutive fails → operator flag in hc top. A failing digest NEVER installs.
```

Identity drift is impossible by construction: S0/pins are not consolidation-writable; Ring-0 loads
verbatim (E7's REEL law).

## §12 · Tier bars (NUC-7) — measured without recursion

The nucleus keeps an in-memory ring buffer (last 1024 appends: wall_ns, bytes, fsync?) and flushes ONE
`nucleus.stats` record per checkpoint or per 512 appends.

- **Latency:** append p50 ≤ 10 ms, p95 ≤ 50 ms amortized over group-commit — at preflight (scripted
  1 K-append bench) and live (stats render).
- **Wall share:** Σ(nucleus time)/step wall < 1% over any 100-step window. Prompt-token overhead is
  zero *by construction* (the ledger is out-of-band) — v2 §8's "<1% of step tokens" is satisfied
  structurally; wall and bytes are what we measure.
- **Append-path budget (5.0, F28):** ≤ 1 durable write per standard flush; ≤ 2 per gold append
  (ledger + nothing else on the path; render mirrors are async, §4).
- **Open (F21):** p95 ≤ 100 ms on a 100 K-record ledger with a warm fold cursor.
- **Strip ladder (breach → observable, never silent):** widen group window to 100 ms → gold-only fsync
  floor → mark `degraded-persistence` in the fleet registry (`hc top` surfaces) → operator decides
  d1→d0 re-manifest. Stripping is an operator action on evidence, never an automatic silent downgrade.

## §13 · Operations (the API the runtime consumes)

`append(kind, body, *, idem?, refs?, durability?)` → seq · `records(lo?, hi?)` → iterator ·
`outcome_for(idem)` → body|None (the read-barrier) · **`pending()` → list[{idem, seq, body}]** ordered
by seq — ALL actions without outcomes (5.0: plural; grounded runs hold parallel in-flight H0 acts; the
v1 single-flight caller reads `[0]`) · `checkpoint(state)` → seq · `resume()` → last checkpoint state ·
`verify_chain(lo?, hi?)` → {ok, first_bad_seq?} · `open_render(name)` / `verify_render(name)` (§5) ·
memory verbs (§6) · `assemble(role, percept, window)` (§7) · `fork(child_claim, at_seq)` (§10,
privileged) · `stats()` (§12).

## §14 · Migration from the live v1 shape (repo `C:\hypercell`, contracts v0.1)

1. **Records:** live `{seq,ts,kind,idem,body,refs}` (`nucleus.py:59-66`) gains `v`, `prev`, `hash`,
   optional `red`. Existing ledgers migrate by **synthetic genesis** (§1): append genesis with
   `chain_adopted_at_seq = head+1`; chain begins there; prior records stay immutable-but-unhashed.
   **Signed baseline over the pre-adoption region (MUST, s6-12):** the migration computes an RFC-6962
   Merkle root over the pre-adoption records (`seq < chain_adopted_at_seq`, canon bytes) and binds it
   into the **operator-signed** synthetic genesis as `pre_adoption_root` — post-migration tampering of
   the unhashed region is detectable against a signed baseline, never merely asserted; the R13 legacy
   trust-tag read (step 2) rests on it, and the signed export path (identity-firewall.md B.7) carries
   the same root.
2. **Kinds:** v0.1 `handoff`/`system` are never written by live code (verified) — removed with no
   data migration. Live `percept` records lack `trust`: for **pre-adoption records only**
   (`seq < chain_adopted_at_seq`), readers map `source: operator` → `trust: operator` and every other
   legacy percept → `external` (ruling R13: legacy `source` was assigned by the cell's own runtime —
   a nucleus accepts appends only from its own membrane, so the field was never remote-suppliable and
   the narrowed read does not regrow the membrane.py:13 bug; strict fail-closed would instead mislabel
   genuine operator history as `external` in bundles and audits). Post-adoption records MUST carry
   membrane-stamped tags — absent → `external`, no source fallback, ever.
3. **Open path:** `Nucleus.__init__` stops calling `rebuild()` (`nucleus.py:30-31`); `open()` uses the
   in-render fold cursor (§5). First open after migration pays one full fold (meta absent), then O(delta).
4. **Append path:** the synchronous index INSERT+commit (`nucleus.py:71-82`) moves to the async mirror
   (§4 LAW-ASYNC-MIRROR). `memory.fsync: always` preserves exact v1 semantics for operators who want it.
5. **pending():** returns a list (§13); `resume_pending()` iterates it and dispatches per-verb via the
   one-verb-executor (kernel contract) — closing F17 (produce-resumed-as-empty-ask) structurally.
6. **Role fields:** see role.md §5 migration (memory_policy → memory block).
7. **Files:** the chain/segment/group-commit engine lands in `common/ledger.py` (0 bytes today);
   `common/canon.py` is new; `cell/nucleus.py` becomes the cell-facing wrapper.

## §15 · Falsifier hooks (bars live in the constitution §15 index)

NUC-1 chain tamper · NUC-2 render determinism + open cost · NUC-3 tkg dark bars · NUC-4 register wall
(0 false accepts; + trust-tag propagation case) · NUC-5 frame determinism + byte-coverage + hysteresis +
cache attribution · NUC-6/CELL-4 kill-9 × harm × fork (+ parallel-pending case) · NUC-7 tier bars
(+ append-path budget) · NUC-8 anti-death-spiral + rotating cold-eyes · NUC-9 record ladder ·
NUC-10 fork cost + digest equality.
