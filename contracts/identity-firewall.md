```
CONTRACT: identity-firewall — the staged identity ladder, the injection firewall, the trifecta gate,
          secret redaction, message signing, and the tamper-evident export.
semver:   5.1.0 · rev 2026-07-25 (P3 resolution)
status:   RATIFIED-CANDIDATE (v5 wave 1). Frozen once ratified: a change is a semver bump + the JSON
          Schema + the code, in one commit (the pairing law, _TEMPLATE-HEADER.md H2).
pairing:  Membrane (noun) — the boundary of every verb (_TEMPLATE-HEADER.md H2 row 6)
emit_read: strict-emit / liberal-read (B.0.1)
operator_boundary: strict-both (R5)
schema_mirror: contracts/schemas/identity-firewall.schema.json (same-commit, H1)
migrates_from: live v1 — membrane.py:13 origin-trust; 0-byte firewall.py/secrets.py; no-auth api.py (B.0.2)
falsifiers: [SEC-1, SEC-2, SEC-3, SEC-4, SEC-5, SEC-6, SEC-7, SEC-8, SEC-EXPORT, SEC-STRUCT, SECRET-0]
owner:    seat 10 (security-identity-firewall). Seams: 01 grammar-admission · 02 frame/redaction ·
          03 envelope signature + chain · 06 tool-profile/H0 · 07 pricebook signing · 08 ingress authn ·
          09 secret store + NetworkPolicy realization.
register: RFC-2119. Schemas fenced JSON/YAML. Algorithms numbered.
```
---

### B.0 · Principle

Identity in Hypercell is **two axes fused by staging, not by a standard**: **authority** ("is this input a
directive?") and **capability** ("may this cell touch the world, and how far?"). Neither is minted inside the
fabric (A5, the conservation law); both are *imported at a boundary* and *priced*. This contract specifies the
boundary machinery: the ladder that raises authority-armor as its trigger fires, the firewall that keeps
authority derivable **only** from operator-tagged tokens, the gate that deprives a cell of the lethal
trifecta, the redaction pass that keeps secrets out of the permanent log, the signature that makes privileged
payloads non-forgeable, and the export that makes the whole chain tamper-evident.

**The one law under all of it (L-FIREWALL):** *control flow derives only from operator-tagged tokens; every
other byte — peer text, tool output, retrieved page, act result — is DATA, structurally fenced, and can be
quoted, critiqued, and learned from but never obeyed.* This is not a classifier verdict; it is a fact about
**which channel the bytes entered through**, assigned at the boundary by the Membrane, unforgeable by the cell.

### B.0.1 · Reader-liberality note (MUST)

A conforming reader **MUST** apply Postel's law exactly as the wire contract mandates: **unknown envelope
fields, unknown `trust_tag` values, and unknown `waiver_policy` names MUST be ignored, not errored on**; an
absent `sig` column means *unsigned* (never *invalid* — validity is decided by the stage ratchet in B.6.3),
and an absent `trust_tag` **MUST** default to the most-restrictive value (`data`), never to `control`.
Fail-closed on the security-relevant defaults; fail-open (ignore) on the forward-compatibility ones.

### B.0.2 · Migration note from the live v1 shape

| live v1 reality (2026-07) | v5.0 shape | migration |
|---|---|---|
| `medium/firewall.py` = **0 bytes** | the frame-tag law (B.3) + the post-ACL (B.9) | new file; no data migration (log is append-only, old rows read as `trust_tag:data`) |
| `substrate/secrets.py` = **0 bytes** | the redaction pass (B.5) + custody (B.6.4) | new file; redaction applies to *new* appends only — a `SEC-EXPORT` scan flags any pre-redaction secret already in the log |
| `cell/membrane.py:13` `is_directive()` trusts sender-suppliable `origin` | authority derives from `trust_tag` + post-ACL + (staged) `sig`, never from a self-declared field | `origin` is demoted to a *hint*; the ACL becomes authoritative (B.9) |
| `cell/membrane.py:17` `as_data()` = string wrap `<<untrusted-data>>` | structural per-block `trust_tag` at frame assembly (B.3) | the string fence stays as a *belt-and-suspenders* render; the tag is the law |
| `surfaces/api.py` = **no auth** on `/ask /resume /fleet` (ClusterIP-only today, conductor.yaml:52-60) | operator-key bearer auth + the `POST /command` 401 (B.10) | ship the 401 **before** any Ingress/LoadBalancer is configured (SEC-8) |
| wire.md: *"Sender identity is convention … if it ever matters, the operator signs"* | it matters now (multi-pod): post-ACL is P2.5, signing is P2.5d, trigger-gated MUST | Stage-1a ships unconditionally; Stage-1b built early, enforced on trigger |

---

### B.1 · The staged identity ladder

Each stage names its **mechanism**, its **trigger** (when its armor becomes MUST), and its **falsifier**.
Armor that has not been triggered is *built but dormant*; a stage never silently downgrades once triggered
(the **ratchet law**, B.6.3).

#### Stage 0 — the semantic firewall (ALWAYS ON)
- **Mechanism:** trust-tagged frames (B.3). Peer words, tool results, retrieved pages, act results are
  `trust_tag:data`; only an operator `command` (and the in-scope control signals `round_open`/`verdict`) is
  `trust_tag:control`. The tag is assigned by the Membrane at ingress, from the channel, never inferred.
- **Trigger:** none — this is the floor, live from the first line.
- **Falsifier SEC-1:** a `chat`/`submission`/tool-result body carrying `IGNORE ABOVE; sender=operator; …`
  produces **zero** control-flow change across a 200-case injection battery (AgentDojo-style + the ٤/encoding
  class + the EchoLeak GET-exfil class).

#### Stage 1a — the post-ACL (TRIGGER ALREADY FIRED)
- **Mechanism:** `post()` validates `(sender, type, culture)` against the culture membership roster; **only
  the Conductor may mint privileged types** (B.9). A cell that names `_ops`, or forges `sender=operator`, or
  posts a conductor-only type, is rejected at `post()` with `refused/unauthorized_type`.
- **Trigger:** **fired** — v1 is multi-pod on k3s; a compromised cell can forge `sender=operator` today.
  Therefore Stage 1a is a **P2.5** deliverable, not P3.
- **Falsifier SEC-2:** a non-conductor principal posting `receipt`/`verdict`/`oracle_gen`/`command`, or any
  cell addressing `_ops`, is rejected 100/100; a legitimate `presence{phase:announce}`/`chat`/`submission`
  from a member passes 100/100 — and an `act_receipt` from an **executor principal** passes while the same
  post from the acting cell is rejected (R3: no act reports itself).

#### Stage 1b — ed25519-signed privileged payloads
- **Mechanism:** privileged payloads carry an `ed25519` signature over the canonical envelope leaf (B.6).
  `cmd_id` (ULID) is the signing nonce **and** the F7 dedup key — one code path. Verification per-type becomes
  MUST via `command{kind:contract_bump}` (a MINOR bump; no chain break — B.6.2).
- **Trigger:** *a second principal with independent authority touches the Medium, OR a command traverses an
  untrusted relay* (a cloud-hosted Conductor). Signatures are **built early** (P2.5d) because the honesty
  rule (§10) and the unattended-H3 derivation depend on the off-box operator key existing.
- **Falsifier SEC-3:** with Stage-1b triggered, an unsigned or wrong-key `command` is refused end-to-end; a
  correctly signed one verifies; a **signature-stripping downgrade** (B.6.3) is refused, not silently
  demoted to Stage-0 validity.

#### Stage 2 — per-cell identity + attenuated grants
- **Mechanism:** a cell's identity is its **claim-id** (`spiffe://<trust-domain>/<claim-path>` naming shape,
  E.14 — forward-compatible, zero SPIRE dependency). Tool/egress scopes are **short-lived substrate grants**
  bound to the claim-id. The **attenuation law** (with 04's spawn gate): a child's authority ⊆ parent's,
  budget **carved, not minted** — realized with Biscuit *offline-attenuation semantics* (E.15), **zero crypto
  dependency**: the parent derives the child grant locally, no issuer round-trip, and the child grant can only
  *narrow* the parent's scope set (set-inclusion checked at the spawn gate).
- **Trigger:** a role manifest declares tool/egress scopes finer than "all-or-nothing" (grounding lands here).
- **Falsifier SEC-4 (= CELL-7):** a child cell cannot acquire a tool, an egress endpoint, a harm-ceiling, or a
  dollar the parent lacked; 100 spawn-attenuation races, zero scope-escalation, zero budget-minting.

#### Stage 3 — capability tokens / SPIFFE-class workload identity — **REFUSED**
- **Mechanism (when earned):** federated workload identity with revocation.
- **Trigger:** the first inbound directive from an agent this Conductor **did not spawn**.
- **Refusal (re-verified 2026-07-16, E.13/E.14):** no **stable + revocable + ratified** agent-authz standard
  exists — **AIMS** is a 4-month-old IETF *draft* (`draft-klrc-aiagent-auth-00`, 2026-03); **A2A** message
  signing is *optional*; **SPIFFE** now has revocation (CRL/OCSP) + Google backing but standardizes *workload*
  identity, not *agent delegation*. **v5 adopts the SPIFFE-URI naming shape (Stage 2) and refuses the
  federation dependency** until a ratified standard clears the trigger. Re-verify each wave.
- **Falsifier SEC-5:** an inbound directive from an un-spawned principal is **refused** with
  `federation_unavailable`, never executed on convention.

---

### B.2 · The two-axis identity record (schema)

```json
// carried in the cell's nucleus instance block; folded, never self-asserted
{
  "claim_id": "spiffe://hc.local/run/ipv4/roster/2",   // Stage-2 naming shape; the durable identity
  "authority": {
    "stage": 1,                        // 0|1|2|3 — the fabric's CURRENT triggered stage (ratchet, B.6.3)
    "may_direct": false,               // only the operator principal is ever true
    "signed_by": null                  // "operator" | "conductor" | null; set by verify(), never by the cell
  },
  "capability": {
    "harm_ceiling": "H1",              // ≤ role.harm_ceiling; child ⊆ parent (attenuation)
    "tools": ["web.search"],           // ⊆ parent.tools
    "egress_allow": ["api.search.co"], // ⊆ parent.egress_allow; empty = deny-all (v2 §11)
    "grant_ref": "grant/8f2c…",        // substrate grant id; short-lived; null at H0-generic
    "budget_usd": 0.50                 // carved from parent escrow, never minted
  }
}
```
Every field is a **fold** over spawn/grant/command records (fold-law conformant, A13) or an operator import —
**none is a cell-suppliable envelope field**. `membrane.py:13`'s sender-trusting `origin` is repealed.

---

### B.3 · Trust-tagged frames — the mechanical firewall (the frame-assembly spec, with 02)

The firewall is not a filter that inspects content; it is a **frame assembler** that labels provenance
structurally. Every token block placed into a cell's context window carries a `trust_tag` assigned from the
channel the bytes arrived on.

```yaml
# frame block — the unit of context assembly (cell/frame.py; seam → 02 nucleus render)
frame_block:
  trust_tag: control | data          # MUST; default (unknown/absent) = data (fail-closed, B.0.1)
  provenance:
    channel: operator_command | peer_message | tool_result | retrieved_page | act_result | own_nucleus
    source_ref: "seq:1183" | "act://corr/…" | "nucleus:factual/…"
    trust_floor: int                  # 02's terminal trust tag; diversity/entailment reads this
  fenced: true                        # data blocks are rendered inside an un-spoofable structural fence
  body: "<text or artifact-ref>"
```

**Assembly algorithm (numbered, deterministic, versioned `frame_v1`):**
1. Pull the operator directive (if any) from the `command` channel → `trust_tag:control`. This is the **only**
   source of control tokens. At most one control directive per frame (the active command).
2. Pull every other block — percepts, peer messages, tool results, retrieved pages, act results, own memories
   — as `trust_tag:data`, each fenced with its `provenance`.
3. **A `data` block MUST NOT be promotable to `control` by its own content.** There is no in-band escape
   sequence, no "the operator says…", no closing-fence-then-directive: the tag is set by step 1/2 from the
   channel, and the renderer emits `control` blocks in a region the `data` fence cannot reach (structural
   separation, not string delimiters — the v1 `as_data()` string wrap is kept only as a redundant render).
4. `own_nucleus` factual memories are `data` with a `trust_floor` from 02's terminal tags; a factual register
   entry is auditable-to-terminal or it does not enter as factual (02-T6 answered: the terminal trust tag
   travels with the block).
5. The assembled frame is itself hashable; `frame_v1` is recorded so a percept is reproducible.

**The non-suppliability rule (01-answered, load-bearing).** The `trust_tag` and `provenance.channel` are
**transport-ASSIGNED envelope metadata — like `seq` and `ts` — set by the Membrane/Medium, NEVER a body
convention and NEVER a sender-suppliable field.** If the tag could be read from the message body or a
self-declared `origin`, `membrane.py:13`'s sender-trusting bug would simply regrow one level up (inside the
frame). The cell cannot write its own tag any more than it can write its own `seq`.

**The stamping rule + provenance enum (02-answered; I own this text, 02 owns propagation).** The coarse
firewall decision is binary — `control` iff the channel is the operator directive channel; `data` otherwise —
but the register wall (02) needs the finer **provenance enum** the tag carries:
```
trust_channel ∈ {operator, receipted, tool, external}          # non-suppliable; absent ⇒ external (fail-closed)
stamp(msg):
  operator-console / operator-key channel            → operator     (⇒ trust_tag:control)
  envelope.type ∈ ACL-privileged-set ∧ ACL-verified sender → receipted   (⇒ trust_tag:data, high floor)
  the cell's own tool result                          → tool         (⇒ trust_tag:data)
  anything else (peer text, retrieved page, unverified)→ external     (⇒ trust_tag:data, lowest floor)
```
`control` maps to `operator` only; `data` covers `{receipted, tool, external}`. 02's `percept.trust` derives
**only** from these transport-assigned columns + the type-ACL verdict + the ingress channel class — never from
a body/`origin` field. This enum is the one this contract owns; 02's `salience`/register propagation reads it.

**Why this beats CaMeL-family monitors (E.11, the sharpest defense of the design):** adaptive attacks break
provenance defenses that **infer** provenance at a monitor (>90% success via provenance-spoofing). v5 does not
infer — it **assigns** the tag at the trust boundary from the channel. A cell physically cannot emit a
`control` block; the worst an injected `data` block can do is *ask*, and asking is not obeying. Detection is
adaptive-attackable; **assignment is not**.

**Extends to all ingress (M12, v2 §6):** act results, tool outputs, and retrieved documents are `data` — the
EchoLeak / lethal-trifecta class is closed at the same seam v1 already owned, now mechanically.

---

### B.4 · The lethal-trifecta gate (Meta's "Rule of Two," mechanical) — two legs

Three booleans, computed structurally, never by a classifier:

```yaml
trifecta:
  private_data:      bool   # role holds/reads private nucleus, operator memory, or another cell's output
  untrusted_content: bool   # role ingests peer text, tool results, or retrieved pages (acquired, not static)
  external_comms:    bool   # role can send bytes to an unpinned destination (see the exfil rule below)
```

**Leg 1 — spawn-time (the Membrane, this seat).** At instantiation the gate computes the three booleans from
the **role manifest + the tool-profile trifecta annex** (B-Annex-1, format owned by 06, semantics by 10,
pricing by 07). **All three true ⇒ REFUSE to instantiate** (`refused/trifecta`), unless an operator waiver
applies (below).

**Leg 2 — ingress-time (the act gate, with 06 — the runtime leg).** Spawn booleans go **stale the moment
content is acquired** — and not only `untrusted_content`: **all three booleans are folds, re-evaluated at
every ingress** (s6-05; a cross-pollination/handoff packet completes the trifecta as surely as a fetch):
```
untrusted_content := fold(exec_ok_receipts)            # true on first world-content fetch
private_data      := standing_access ⊔ fold(received handoff/submission/pollination
                                            from other claim_ids) ⊔ (operator-memory grant present)
external_comms    := profile ⊔ fold(egress grants acquired)
```
The act gate (06) gains **step 1h**: it REFUSES (`reason:trifecta`) whenever the **post-ingress fold shows
ALL THREE true (holds-all-three)** — regardless of which channel set the third, never only "the act that
would complete it" — unless the waiver applies. **"Re-evaluated on every ingress" is thus a log
query (a fold), not a monitor** — zero always-on detection, fold-law conformant.

**Declared `trifecta{}` is ADVISORY (MUST, s6-03).** The gate never takes the profile's declared booleans
(B-Annex-1) as authority: it RECOMPUTES them from `exfil_channel` + `egress_allow` + role holdings + the
folds above, and REFUSES admission when declared < recomputed — an under-declaring profile fails admission.

**The exfil rule (06-T3 answered — `external_comms` is not about HTTP method).** A cell-composed `GET` URL is
an egress channel (EchoLeak exfiltrated via GET image URLs). Therefore:
```
external_comms(profile) := (egress_allow is broader than an operator-pinned fixed set)
                           OR (url | body | headers are cell-composed toward an unpinned destination)
```
The tool profile declares `exfil_channel: none | url | body | headers` (annex field 06's, derivation rule
10's — **confirmed**). H0-read-only ≠ exfil-safe: an H0 fetch to a cell-chosen URL still sets
`external_comms`.

**Waiver precedence (operator forces `external_comms → H3` = operator-always, then picks a policy):**
1. **scoped-act** (default): the act gets its **own ephemeral class-3 sandbox + one-endpoint egress + a signed
   operator grant**, so the cell never holds all three at once (the trifecta is *broken by construction*, not
   permitted).
2. **shed-egress**: drop the external tool from the role; the cell keeps private data + untrusted content but
   cannot exfiltrate.
3. **quarantine-and-gate**: instantiate with every act held for operator co-sign (H3).

**Falsifier SEC-6:** a role manifest with all three booleans true is refused; each waiver policy is exercised
and the resulting cell provably never holds all three simultaneously (scoped-act: the egress sandbox holds no
private data; verified by a receipt query, not a promise).

**THE PROVENANCE-TAINT LAW (R8 — this contract owns it; ruled in-wave, restated here as law).**
*Provenance = what could influence the bytes, not who typed them.* A candidate artifact from a cell whose
`acquired_trifecta.untrusted_content = true` (the fold over its exec-ok receipts — act.md owns the fold) is
**adversarial-EQUIVALENT**: it executes at **class-3 or is REFUSED**, whatever its author's intent — a
grounded code tournament is class-3-or-refuse even on WSL2. Source tiering (substrate realizes, deploy annex):
(1) clean first-party → class-3 default, MAY lock class-2 with `degraded: true` where gVisor is absent;
(2) untrusted-touched → class-3-or-refuse, no degraded fallback; (3) external/operator-supplied →
class-3-or-refuse. The gate is mechanical (a log query over receipts), never a monitor, never a heuristic —
injection-laundering through a "trusted" cell's output is closed by construction.
**Falsifier SEC-7 (taint):** a candidate authored by a cell that ever executed an untrusted-content tool run
is offered class-2 by a mis-configured manifest ⇒ REFUSED with a typed receipt naming the taint source,
100/100 over the seeded corpus; the same candidate at class-3 runs.

---

### B.5 · Secret redaction — the Membrane pass before every append (the enforcement point v1 named)

```
redact(bytes) → bytes'                       # cell/membrane.py + substrate/secrets.py (both 0 bytes today)
```
1. **Exact-match** every substrate-secret *value* (provider keys, grant secrets, the conductor signing key)
   against the outgoing bytes; replace each hit with `⟦redacted:sha8(value)⟧`.
2. **Pattern-match** the common secret shapes (`Authorization:\s*Bearer …`, `sk-…`, `AKIA…`, JWT triples,
   `?api_key=…` / `&token=…` query components — the credential-carrier classes 06 declares per profile).
3. **Order (03-answered, critical):** the redaction hook sits **BEFORE canonicalization and append** — the
   hash chain never witnesses a secret, so `verify()` **never needs a secret to re-verify** an exported
   bundle. Redaction is **envelope-level** (02-T3 / 03-T8 answered): it runs on the whole outgoing envelope
   body + artifact, not just percepts — a leaked `Authorization:` header in a *tool-result body* is caught
   because tool results are not percepts. The redactor writes its markers into a **`redactions[]` envelope
   column that IS inside the canonical leaf** (03's wire schema): the chain witnesses the *marker*, never the
   *value*, so the redaction is itself tamper-evident while the secret stays absent from history.
   `redactions[]` is redactor-assigned (non-suppliable) and lands as a wire MINOR with `secrets.py`.
4. **Provenance-URL scrub (06-T3 answered):** for a tool profile with `credential_carrier: query`, the
   executor strips the credential component from `receipt.provenance.url` **before** post; scrub-verify runs
   at **profile admission** (a profile whose test vector leaks its key fails admission).

**Falsifier SEC-8 (the headline):** a planted fake key injected via a tool-result body appears **0 times** in
the ledger, the Medium, and every `hc export` bundle; a mid-file edit that reintroduces it is caught by the
export scan (SEC-EXPORT).

---

### B.6 · Message signing (Stage 1b mechanism) — placement, chain, ratchet, custody

#### B.6.1 · Envelope placement (03-answered, adopt verbatim)
`sig` is a **RESERVED envelope column**, **EXCLUDED from the canonical leaf** exactly like `hash`:
```
leaf_n   = JCS(RFC-8785)(envelope columns 1..15, WITHOUT hash, WITHOUT sig)
hash_n   = sha256(leaf_n ‖ hash_{n-1})          # the raw32 chain (03's chain law)
sig_n    = ed25519_sign(signing_key, leaf_n)    # signs the leaf; absent ⇒ unsigned
```
A `sig` value never enters the leaf, so signing never perturbs the hash chain, and an unsigned message hashes
identically whether or not signing is later enabled.

#### B.6.2 · Turning verification MUST on (no chain break)
Stage-1b enforcement flips **per-type** via `command{kind:contract_bump}` — a **MINOR** addition (no chain
break, no wire MAJOR). Before the flip: a valid `sig` is verified-if-present, tolerated-if-absent. After the
flip for type T: an inbound T without a valid `sig` is refused.

#### B.6.3 · The ratchet law (my cross-read claim, 01/08 answered)
**Auth stage is a ratchet, not a menu.** Once a stage's trigger has fired, lower-stage validation is **no
longer SUFFICIENT** for the privileged types that stage protects. Formally: `validate(msg)` at fabric stage S
requires `msg` to satisfy the check *for stage S*, not "for some stage ≤ S". This closes the **downgrade
attack**: an attacker who strips a signature does **not** fall back to Stage-0 "log-derived" acceptance — a
stripped-signature privileged type at Stage-1b is `refused/downgrade`. The honesty rule (§10) narrates only
events valid **at the current stage**, so a downgraded event is un-narratable, not silently narrated.

#### B.6.4 · Key custody (09-answered, adopt verbatim)
- **Operator private key: OFF-BOX.** The substrate **never** stores it. This is load-bearing: a routine's
  envelopes are only ever *conductor*-signed and thus **physically cannot present the H3 signature**, making
  unattended H3 impossible **by construction**, not by policy (§10, M14).
- **Conductor signing key:** a k8s `Secret`, `hypercell` namespace only, injected by `secretRef`, **never
  image-baked**.
- **HARD RAIL:** `hypercell-sandbox` (class-3) pods mount **NO `secretRef`, ever** — the class-3 Pod spec has
  no `envFrom`/`secretRef`; enforced by an admission assert + a drill spoof row (SECRET-0, the substrate
  seam's row — §15; the SEC-7 id names the R8 provenance-taint gate, B.4). A candidate cell
  therefore *cannot* read any key, closing the H0-adapter-key exfil path at the substrate.

**Falsifier SECRET-0 (substrate seam; bar in §15):** a class-3 sandbox pod spec carrying any `secretRef` is
rejected by admission; a candidate that greps its own env/filesystem for a key finds none (drill).

#### B.6.5 · The stage oracle (08-asked, 01-confirmed) — a fold, no lie-able field
The honesty rule (§10) and the ratchet (B.6.3) both call a mechanical stage oracle:
```
current_stage()      → 0 | 1a | 1b | 2 | 3         # a FOLD over command{kind:stage_bump} records (A13-conformant)
stage_of(event)      → the minimum stage at which `event` is VALID (pure fn of the record + census + stage-fold)
narratable(event)    := stage_of(event) ≤ current_stage()   # the ratchet: current stage is a floor, not a menu
```
`stage_bump` joins `contract_bump` in the `command`-kind set — a **command.md MINOR, zero registry impact**
(01 #692). Neither `current_stage()` nor `stage_of()` reads a suppliable field: the stage is a fold over
signed operator `stage_bump` commands, so it cannot be lied into a lower value by a message.

#### B.6.6 · The Day-1 H3 grant path (08-asked) — before signatures exist
An H3 act must be usable **before** the Stage-1b trigger fires (else H3 is dead until signatures ship).
At Stage 0/1a, operator authentication for `grant`/`deny` is **loopback-tty possession or an operator-key
bearer on the loopback surface** — explicitly blessed as the Day-1 operator-authn floor. When Stage-1b
triggers, the grant path ratchets up: **H3 confirmation additionally REQUIRES a Stage-1b-authenticated
surface, never open-mic** (§10). H2 confirmation echoes a **deterministic nonce** ("confirm r7-a2"); a bare
"yes" never confirms (both lines land here and are cited by §10/command.md, not duplicated).

---

### B.7 · The tamper-evident `hc export` bundle

```yaml
# hc export <scope> --sign  →  a signed, verifiable bundle
export_bundle:
  version: "5.0.0"
  scope: {culture?, run_id?, claim_id?, from_seq, to_seq}
  merkle_root: "<RFC-6962 root over the per-cell hash chains in scope>"   # 03's spans law
  chains: [{claim_id, from_hash, to_hash, leaf_count}]
  pre_adoption_baselines: [{claim_id, chain_adopted_at_seq, pre_adoption_root}]  # R13/s6-12: the
                                # operator-signed Merkle baseline over each unhashed pre-adoption
                                # region, verbatim from that chain's synthetic genesis (nucleus.md §14)
  identity_tags: [{claim_id, spiffe_uri, first_seq}]
  oracle_gens:  [{oracle_id, gen, sealed_commitment_ref}]                 # 05's sealed/errata sigs
  redaction_manifest: {secret_count: 0, scanned_bytes: N}                 # SEC-EXPORT asserts 0
  signed_by: "operator" | "conductor"
  sig: "<ed25519 over merkle_root ‖ scope ‖ version>"
```
- **Article-12-grade, applicability *not* claimed (E.16).** The bundle is a tamper-evident, identity-tagged,
  time-ordered event record — the shape EU-AI-Act Article 12 asks of high-risk systems — *for the cost of a
  hash column*. **v5 provides the artifact; it does not claim the deployment is a high-risk Annex-III system**
  (that depends on the operator's use-case; the date is 2 Aug 2026, now in force, but applicability is the open
  question, not the deadline).
- **verify() needs no secret** (B.5.3): because redaction precedes canonicalization, an auditor re-verifies the
  Merkle root and every chain link over redacted bytes with only the public key.
- **The signed pre-adoption baseline rides the export (MUST, s6-12 — pairs with nucleus.md §14 step 1).** For
  any chain adopted by synthetic genesis, the bundle carries that genesis's `pre_adoption_root` (the
  migration-time Merkle root over the unhashed `seq < chain_adopted_at_seq` region, operator-signed at
  adoption); `verify` re-derives the region root from the exported bytes and fails on mismatch. The R13
  legacy read (`source:operator → trust:operator`) is admissible **only** against a verifying baseline —
  post-migration tampering of pre-chain history is detectable, never merely asserted.

**Falsifier SEC-EXPORT:** flip one byte in any exported chain → `verify` fails at the exact leaf; a bundle
with `redaction_manifest.secret_count > 0` refuses to export.

---

### B.8 · Structure over detection + the behavioral baseline (hard law)

- **A classifier MUST NOT gate.** An injection/anomaly classifier MAY flag into `hc top`; it MUST NOT block a
  spawn, act, ingress, or post. (Empirically forced: adaptive attacks break >90% of classifier gates, E.11/E.12.)
- **The behavioral baseline (the ARMO gap, E.4):** the fabric folds a per-role act-distribution and surfaces
  deviations as **anomaly flags** in `hc top` — *observability, not auto-kill; the operator decides*.
  Sandboxing controls *where* code runs; the baseline is the only lens on what it does through *permitted*
  channels.

**Falsifier SEC-STRUCT:** disable every classifier and the injection battery (SEC-1) still passes — security
comes from the frame tags + the trifecta gate, never from detection. If turning off the classifier changes the
SEC-1 result, the design has leaked a detection dependency.

---

### B.9 · The privileged-type ACL (the post-ACL, Stage 1a) — bound to the type registry

`post()` enforces, per envelope `type`, **who may mint it**. **The mint-principal is the ACL key** (01's
V-RECEIPT ruling #692): who may witness a thing is decided by *type*, never by a body-`subject` parse.

**Principal grammar home (one home, no second copy).** wire.md §3/§6 is the **registration/grammar home**
for principals: principal registration, the claim-id grammar, "unregistered senders class as `cell`", and
the principal wordings this table uses (**executor principal** = `runner-N` / a conductor resolver daemon;
the acting cell = its **cognition principal**) are defined there. This section states the security-side ACL
law over those definitions and never re-defines them.

| type | who may mint | ACL row |
|---|---|---|
| `command` | `operator` / `conductor` on the operator's behalf (signed) / **registered surface principals** (the operator's authenticated ingress, M13) | privileged · Stage-1b-signed on trigger |
| `receipt` (the *oracle grading* — of a submission **or** of an act) | **conductor only** | privileged |
| `verdict`, `oracle_gen`, `compact` | **conductor only** | privileged |
| `round_open` | conductor by default; **self-clocked only where the run manifest declares it, and then never carrying a generation bump** (a gen-bump `round_open` is always conductor-only) | privileged (conditional, R14) |
| `oracle_gap` | **any cell** | member · DATA-class hint, never an admission path (R14; restricting it would kill its function) |
| `cmd_receipt` (the command-plane ack/progress/result over `cmd_id`) | **conductor only** | privileged · phase-dependent durability |
| `act` (the *request* to touch the world) | the **acting cell's cognition principal** | member · cell-mintable |
| `act_receipt` (the world-side *executor* phase records: hold/exec/settle over `corr`) | the **executor principal** (`runner-N` / a conductor resolver daemon) — **never the acting cell** | member (executor) · **not** cell-mintable |
| `task` | conductor, operator | restricted (claimable work; wire.md §3) |
| `presence` (non-genesis phases: announce/spawned/depart; genesis = conductor/operator only), `chat`, `status`, `claim`, `submission`, `handoff` | any culture member | member |

**The A5 correction (06-answered, load-bearing).** `act_receipt` is **executor-minted, never
acting-cell-minted** — *no act reports itself* (A5). The acting cell mints `act` (the request); the executor
principal (a runner or a conductor resolver daemon, a *distinct* principal at Stage-1a+) mints the world-side
`act_receipt`. Letting a cell mint its own `act_receipt` would be the **F3 spoof one level up** — a compromised
cell writing its own world-witnesses. At T0 (class-0, executor in-process) this is convention, red-teamed by
HC-7-v2 attempt 8; at Stage-1a+ it is mechanical (the executor is a separate principal the ACL checks).

**The count (01 ruling #692, coordinator-countersigned — R1).** `act_receipt` (executor phases) and
`receipt` (oracle grading — of a submission or an act, discriminated by `subject`, both conductor-minted so the
ACL is one row) are **distinct types**; `cmd_receipt` (command-plane, conductor-only, phase-dependent
durability) is a further distinct type raised by 08/03. **The honest registry count is 17** (16 + `cmd_receipt`)
— prior-2's "16/16" amends to a **true 17/17** under its own "the count must be true" clause. The firewall's
always-privileged set is `{command, receipt, verdict, oracle_gen, compact, cmd_receipt}`, plus `round_open`
conditionally (privileged unless manifest-declared self-clocked, and then never gen-bump-bearing) and
`act_receipt` mint-restricted to executor principals; **`oracle_gap` is never privileged** (R14 — the wire §3
table is the ONE privilege source of truth; the Stage-1b signature-requirement column IS its ACL column).
`_ops` is a room no cell can name (only authenticated surface principals address it, §10 M13). *The security
requirement (distinct mint-principals) is what forces the count — arithmetic follows the ACL, not the reverse.*

**Falsifier SEC-2** (B.1) is this section's drill.

---

### B.10 · Ingress authentication (the surfaces, with 08)

- `POST /command`, `/ask`, `/resume`, `/fleet`, `/top`, `/events`, `/fire/{routine}` **MUST** require an
  operator-key bearer credential; an off-box unauthenticated call returns **401**. (`api.py` is no-auth today;
  ClusterIP-only, so the exposure fires the instant an Ingress is added — the 401 ships **before** that, 09.)
- The **MCP server** (`surfaces/mcp.py`, empty today), when it ships, **MUST** bind tokens to the intended
  server via **Resource Indicators (RFC 8707)** and validate `iss` via **RFC 9207** (E.6, the 2026-07-28 MCP
  authz hardening) — even against the stable 2025-11-25 base.
- **Read-only stays read-only:** the viewer is constitutionally read-only; a viewer that grows action buttons
  has changed surface class (§10). `hc peek` is loopback/operator-key only.

**Falsifier SEC-8** (B.5) includes the 401 drill.

---

### B-Annex-1 · The tool-profile trifecta annex (handshake with 06, priced by 07)

Format owned by 06 (act-grounding), boolean semantics by 10 (this contract), pricing by 07:
```yaml
tool_profile:
  id: "web.search@v1"
  harm_floor: H0
  credential_carrier: header | query | body   # drives redaction (B.5) + provenance scrub (06-T3)
  exfil_channel: none | url | body | headers   # drives external_comms (B.4)
  egress_allow: ["api.search.co"]              # pinned set; breadth drives external_comms
  trifecta: {private_data: false, untrusted_content: true, external_comms: false}
```
`untrusted_content:true` for `web.search` because it returns retrieved pages (`data`); `external_comms:false`
because egress is operator-pinned to one endpoint and the URL is not cell-composed. Change either and the
booleans recompute — that is the derivation rule (10) over the annex fields (06).

### B-Annex-2 · The pricebook-signing seam (07 + 05 answered)

- The **pricebook is an operator-signed artifact** (07-T10). A poisoned book is a **cheapest-lane routing
  attack** (redirect the fleet to an attacker's lane) or a **price-DoS** (inflate prices to stall). The
  signature (ed25519, operator key) makes the book tamper-evident; the roster solver reads `weights_family`
  **only from a signed book**.
- **`weights_family` is a TRUST-plane input, not just econ (05-answered, AMPLIFIED).** A signed book attests
  what the operator *believes* a lane runs; it cannot attest what the lane *actually* runs (providers reroute
  backends silently). So **lane-family-attestation := signed-declaration AND runtime-canary**: a per-round
  canary probe (known-answer / tokenizer-fingerprint) checks the response against the declared family; a
  mismatch **de-rates that lane's diversity contribution to ZERO** (not merely an alarm) until re-attested.
  **Two flags, two owners (s6-13):** `family_verified` (the canary, TRUST-owned — mechanized in oracle.md
  SEC-2: tokenizer-fingerprint + per-family known-answer corpus pinned like controls; FAIL-CLOSED — no
  fingerprint for a claimed family ⇒ diversity contribution ZERO) is DISTINCT from `parity_verified` (econ
  cost parity, pricebook-owned). **Diversity-counting keys on `family_verified`, never the econ
  score-parity probe.** Aggregator hosts (Together/Fireworks) book `family_verified:false` until the canary
  passes. Without both, 05's cross-family quorum theorem is trust-me theater.
- **Spend-event redaction (07-T10b):** SKU names can leak strategy; the Conductor's escrow-ledger records
  (RESERVE/COMMIT/RELEASE/SPEND — conductor-internal, **no wire type exists**, R2) and any exported `cost{}`
  field-groups redact SKU detail to a hashed lane id in operator-external exports, and carry
  `pricebook_version` for recomputability.
- **Reservation-spam is a budget-DoS (07-T10c):** a compromised cell spraying escrow reservations is throttled
  by **per-issuer reservation rate caps** at the Conductor; over-cap reservations are `refused/rate_capped`
  receipts, not silent drops.

### B-Annex-3 · The full `[SECURITY-SEAM]` resolution ledger (every seat)

| seat | seam | resolution in this contract |
|---|---|---|
| 01 | membrane trusts sender `origin`; type-ACL needs sigs; no 10th axis | B.2 repeals `origin`-trust; B.9 ACL + B.6 sigs; **ladder adds no noun/verb** (B.11) |
| 02 | percept trust-tags; envelope-level redactions; `tool_profile` in role | B.3 step-4 terminal trust tag; B.5 envelope-level; B-Annex-1 |
| 03 | 5 seams: redact-before-append; sig placement; chain constant | B.5.3 order; B.6.1 placement; B.7 Merkle spans |
| 04 | spawn gate = attenuation checkpoint | B.1-Stage2 + SEC-4; child ⊆ parent at the spawn gate |
| 05 | sealed/errata/gen sigs; `weights_family` attestation; StackReceipt non-mint | B.7 `oracle_gens`; B-Annex-2 canary; B.9 conductor-only |
| 06 | credential_carrier scrub; trifecta annex; `act_receipt` first-class; exfil channel | B.5.4; B-Annex-1; B.9; B.4 exfil rule |
| 07 | pricebook signing; spend redaction; reservation-DoS | B-Annex-2 (all three) |
| 08 | Stage-1b verify at ingress; api 401; off-box H3; honesty-rule ratchet | B.10; B.6.3 ratchet; B.6.4 off-box |
| 09 | NetworkPolicy realization; secret-store custody; pod-security; scoped-act class-3 | B.6.4 custody + hard rail; B.4 scoped-act; egress = 09's default-deny NetworkPolicy |

### B.11 · Grammar conformance (with 01) — the ladder adds NO noun and NO verb

Every mechanism in this contract compiles to the closed grammar: the firewall + trifecta gate + redaction are
**Membrane policy**; the post-ACL is a `post()` predicate; the signature is one **reserved envelope column**;
grants are **substrate** objects; the export is `act` (a world-crossing read) + a fold; `stage_bump` and
`key_rotate` join the existing `command`-kind set (command.md MINOR, zero registry impact). **No verb #8, no
noun #9, no 10th contract axis beyond the nine kernel counts** (identity-firewall is noun-contract #6, per
01-T3). This is a MUST: if any future security addition needs a new noun or verb, it clears kernel's V5/N5
admission test first or it is refused.

**No smuggled 10th contract (01 constraint #687-1, MUST).** identity-firewall.md is the **9th and last**
version axis. It carries **no separately-versioned sub-schema** — no independently-semver'd keyring, policy
grammar, or tag-enum artifact inside it (that would be a 10th contract smuggled through the side door). The
`trust_channel` enum, the tool-profile trifecta annex, and the waiver-policy set version **with this contract's
own semver**; a change to any of them is an identity-firewall.md bump, never a private sub-version.

