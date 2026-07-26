# CONTRACT TEMPLATE HEADER — the versioning law every hypercell contract inlines
**Artifact:** `contracts/_TEMPLATE-HEADER.md` · **Version:** 5.1.0 · **Status:** RATIFIED-WITH-V5 · RFC-2119 · rev 2026-07-25 (P3 resolution: R23 facts-not-shape; H2 row 9 names `pricebook.md`)
**Pairing:** none — this is the law OF contracts, not a contract of the fabric (it versions with the
constitution, as §15's falsifier index does).

---

## H1 · The header block (MUST open every contract file, verbatim fields)

```yaml
contract: <name>                 # one of the nine (H2); anything else is a smuggled contract — refuse
version: <MAJOR>.<MINOR>.<PATCH> # semver 2.0.0; the census carries this 9-tuple
status: DRAFT | RATIFIED | DEPRECATED(superseded_by: <name>/<semver>)
pairing: <noun or verb-plane>    # exactly one: the noun or verb-plane this contract constitutes (H2)
emit_read: strict-emit / liberal-read        # H4; the only legal combination for fabric-to-fabric types
operator_boundary: strict-both | n/a         # R5: manifests + CommandEnvelope params validate STRICT
schema_mirror: contracts/schemas/<name>.schema.json   # generated, versioned in lockstep, same commit
migrates_from: <live v1 shape, one line>     # H7; "none — new in v5" is legal and explicit
falsifiers: [<MIG/contract-specific drill ids>]
```

**[R23] The law is the nine FACTS, not the YAML shape.** A contract file MUST state all nine header
facts above — `contract`, `version`, `status`, `pairing`, `emit_read`, `operator_boundary`,
`schema_mirror`, `migrates_from`, `falsifiers` — either as the fenced YAML block shown here **or as
labeled prose** carrying the same nine labels. CI gate CONTRACT-HDR-1 checks **presence of the facts**,
not conformance to one serialization: a contract whose header is readable prose is a conforming
contract, and a gate that failed it would be enforcing typography, not constitution. A file missing
any of the nine facts does not parse. The JSON-Schema mirror is generated from the fenced schemas in
the same commit as any version bump — a bump without its mirror is the lived G3/empty-`schemas/`
defect and MUST fail CI.

## H2 · The pairing law (the closed inventory; who may version)

Exactly **nine** separately-versioned contract artifacts exist. Each is the constitution of exactly one
noun or one verb-plane. **Nothing else in the fabric carries a version of its own** — a versioned
anything-else is a smuggled contract; refuse it at review.

| # | contract | pairs with | plane it governs |
|---|---|---|---|
| 1 | `wire.md` | **Medium** (noun) | converse (+ the carried forms of all verbs); the type registry; the chain |
| 2 | `nucleus.md` | **Nucleus** (noun) | persist |
| 3 | `role.md` | **Cell** (noun) | spawn |
| 4 | `run.md` | **Culture** (noun) | converge / route / schedule policy |
| 5 | `command.md` | **Conductor** (noun) | command (the operator boundary; CommandEnvelope + cmd_receipt semantics) |
| 6 | `identity-firewall.md` | **Membrane** (noun) | the boundary of every verb: ingress trust-tagging, the type-ACL's authority, the staged ladder, redaction, export |
| 7 | `oracle.md` | the bar (verb-plane) | converge's grading half; generations; the Crucible's shape |
| 8 | `act.md` | the world aperture (verb-plane) | act; receipts; effect scopes; harm classes |
| 9 | `pricebook.md` | the economics plane (verb-plane) | route's DECIDE/ENFORCE; SKUs; lanes (`pricebook.yaml` is the DATA artifact this contract governs, never the contract itself) |

**Fleet and Substrate have no contract file, deliberately:** the Fleet's truth (registry, census, queue)
is a fold; the Substrate's truth (preflight) is a point-in-time probe — both are render-class artifacts
by the render test (rebuildable; delete = lose speed, never truth). Giving either a frozen contract
would version a *derived* thing — the split-brain N5 forbids.

**The census** is the 9-tuple of versions. It appears in: every culture genesis
(`presence{phase:genesis}`), every nucleus genesis, substrate image labels, every detached artifact
(H5), and the CommandEnvelope's `contracts:{...}` expectation block (MIG-SUR).

## H3 · What bumps what (generic law; each contract ADDS its specific rows, never subtracts)

- **MAJOR (breaking):** remove/rename/re-type a field; change the semantics of an existing field or
  record; narrow a value domain; change any default in a way that alters behavior (the silent-default
  hazard — Entry-30's manifest twin); demote a durability/retention class; **add or widen any
  instruction-bearing wire type** (a new directive widens the firewall surface — always MAJOR, however
  "additive" it looks); change the hash algorithm or chain construction (the chain carries its own
  construction constant inside wire.md, decoupled from the semver — a MINOR/PATCH never re-anchors).
- **MINOR (additive):** new optional field with an inert default; new non-directive payload type; new
  enum value **with a named R3 fallback landed in the same bump**; new `kind` on an existing type with
  defined refusal on old readers; retention up-class.
- **PATCH:** docs, examples, clarifications that change no behavior.
- **The reinterpretation clause:** an addition that changes the *meaning* of existing fields is MAJOR
  even though additive — unless it ships with a total default preserving every old record's meaning
  (the `oracle_gen`/`g0` pattern is canonical: field + the reader clause "absent reads as g0, forever"
  land in the SAME bump, or the bump is silently MAJOR).

## H4 · Reader-liberality rules R1–R6 (normative, cited by every contract)

- **R1 — unknown payload types:** ignore, never error; preserve when relaying.
- **R2 — unknown fields (fabric-to-fabric):** accept and preserve byte-faithfully on store and re-emit;
  never drop. Code form: `_FrozenEmit(extra="forbid")` for what we mint; `_LiberalRead(extra="allow",
  preserved)` for what we accept. (The G2/G4 fix: the transport consumes the full envelope type;
  strict-emit keeps our own records honest.)
- **R3 — wire enums are open for readers; every enum names its unknown-fallback in a table in its
  contract:** unknown `outcome` → `invalid` (excluded — never zero, never gate); unknown act outcome →
  `unknown` (reconcile); unknown message type → R1; unknown harm class → **refuse the act** (fail closed
  at the world); unknown depth → refuse spawn (fail closed at instantiation). A new enum without its
  fallback row does not parse.
- **R4 — defaults are frozen per MAJOR.** Readers apply the defaults of the record's declared epoch
  (census fold tells them which); changing a default within a MAJOR is forbidden — it silently rewrites
  history's meaning. (Prior art: Protobuf Editions pins behavior-defaults per edition; changing one is
  an edition event, never a point release.)
- **R5 — strict at the operator boundary.** Role/run manifests and CommandEnvelope params validate
  STRICT: an unknown field is an error, never an ignored extra (`budgett: 5.00` must fail loudly).
  Liberality is for peers; strictness protects the human from silent typos.
- **R6 — old tapes always play.** Readers retain fold adapters for every prior MAJOR of log-record
  shapes; in-place log rewriting is forbidden, forever. A migration never touches written bytes.

## H5 · Version identification (version-by-epoch-record; no per-row version columns)

1. Every constitutional log opens with a genesis record carrying the census (Medium: culture genesis =
   `presence{phase:genesis}`, conductor-posted, D-gold, R-forever, the chain anchor; nucleus: the
   genesis record — both carry the 9-tuple + role_digest + lineage_root).
2. A writer upgrade appends `command{kind: contract_bump}` **inside the hash chain** (outside the chain
   a version claim can be retro-forged; inside it, "which contract wrote this span" is tamper-evident
   and foldable). Records between bumps read at the last declared version. One record per upgrade —
   never one column per row. (Contrast, dated July 2026: A2A v1.0 versions per-request via an
   `A2A-Version` header — right for stateless RPC between strangers, wrong for an append-only log whose
   records outlive their writers. The two compose: epoch records inside; the CommandEnvelope's
   `contracts:{}` expectation at the surface boundary is exactly the header pattern, adopted where it
   belongs.)
3. **Detached artifacts** (manifests, exported certificates/receipts, pricebook files, backups) carry an
   explicit `contract: <name>/<semver>` stamp — they travel without their log.
4. The census fold: `fleet_versions()` folds genesis/announce(`presence`)/bump records →
   `{principal → census}`; `hc fleet versions` renders it; substrate carries the census as image labels;
   preflight refuses mixed-MAJOR.
5. **HONEST-EPOCH (adoption):** logs predating the spine get a synthetic genesis at adoption; the chain
   starts there; prior records read under frozen pre-spine defaults, forever (one pattern, three uses:
   synthetic-genesis-at-adoption · gen-reads-as-g0 · chain-starts-at-adoption). v5's own adoption is
   the one legal "big-bang" wire MAJOR (v0.1 → 5.0.0): the presence merge and the registry land WITH
   the spine that makes every later change lawful.

## H6 · Mixed-version legality + migration procedures (cited, not restated)

Within one MAJOR, any MINOR/PATCH skew is legal fleet-wide — **that is the operational definition of
MINOR**, and MIG-1 tests it. Across MAJORs: never live-mixed; the epoch record is the barrier.
Procedures M-MINOR (rolling, 4 steps) and M-MAJOR (epoch, 10 steps, rollback point at the snapshot,
roll-forward-only after the first new-MAJOR D-gold write) are constitution text (§18 of the v5
architecture); contracts cite them. Falsifiers: MIG-1 (MINOR skew completes a live run, replay equality
both readers), MIG-2 (MAJOR epoch: park → upgrade → resume; budget = cap − folded pre-epoch spend),
MIG-3 (census gate refuses unknown MAJOR at spawn), MIG-4 (rollback point restores clean),
MIG-5 (round-trip: three unknown fields survive store-and-relay byte-identical, 10/10),
MIG-SUR (old `hc` vs new `hcd`: typed refusal naming both versions, zero silent misexecutions —
prior art: A2A `VersionNotSupportedError`).

## H7 · The migration note (MUST; one per contract; from the LIVE repo, not from v2's prose)

Every contract closes with `## Migration from live v1` naming: (a) the live file(s)/tables it
supersedes with `file:line` anchors; (b) which live fields survive, which rename (R2 alias at read,
new shape at emit — renames stay out of MAJOR this one time via the adoption epoch), which die;
(c) the HONEST-EPOCH statement for existing logs; (d) the first slice (PART D of the owning seat's
paper) that makes the contract live.
