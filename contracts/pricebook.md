# contracts/pricebook.md — the economics plane's data + protocol contract

```
contract: pricebook
version: 5.1.0            # semver; MAJOR = field removal/semantics change, MINOR = optional field added,
                          # PATCH = wording. Pairs with: the Conductor's econ organ (PRICE→DECIDE→ENFORCE).
                          # rev 2026-07-25 (P3 resolution).
status: normative
pairing: the economics plane (verb-plane; _TEMPLATE-HEADER H2 row 9 — this contract governs the
                          # signed `pricebook.yaml` artifact)
emit_read: strict-emit / liberal-read     # §6: readers ignore unknown SKU fields, never invent absent capabilities
operator_boundary: strict-both            # operator-authored book; a row failing REQUIRED fields does not parse (§6)
schema_mirror: contracts/schemas/pricebook.schema.json
migrates_from: v1 `_PRICE` dict + `Governor.spent` (§7 migration table carries the file:line anchors)
falsifiers: [ECON-PB-1, ECON-2, ECON-LEASE-1, RESUME-$1, ECON-CACHE-1, SEC-PRICE]
owners: econ-plane (seat 07); security annex co-owned with identity-firewall.md (seat 10)
supersedes: v1 governor._PRICE dict (repealed), v3 wave-paper §2/§3/§5 drafts
```

## 0 · Scope and the one law

One plane — **PRICE → DECIDE → ENFORCE** — over one spend ledger. This contract defines: (1) the
`pricebook.yaml` artifact (PRICE); (2) the `quote()` interface the route/run planes consume (DECIDE);
(3) the escrow protocol — reservation as the only path to spend (ENFORCE); (4) the spend-record and
`cost{}` field-group shapes. The DECIDE algorithms themselves (dollar-UCB, prune, stagger, hedging) are
constitution §7 material and are not duplicated here.

Conformance verbs are RFC-2119. **A row without a date does not parse. An unpriced lane does not run.
An unreservable call does not dispatch.**

## 1 · `pricebook.yaml` — the artifact

The pricebook prices **SKUs**, not lanes. Key = `<weights>@<host>/<service_tier>`: a service tier
changes the *unit price* of the same weights on the same host (July-2026 tier zoo: Anthropic fast 2×,
OpenAI priority 4× / flex 0.5×, Gemini priority 1.8× / flex 0.5×, Fireworks fast ≈2× / priority ≈1.5×),
so the tier MUST live in the key. A **lane** = `{sku, effort, cache_mode, batch}` — lane dimensions
modify token *counts and multipliers* over one SKU's unit prices; they never change the unit prices.

### 1.1 Header + defaults (normative)

```yaml
pricebook:
  version: null            # COMPUTED: sha256 of canonical content. Every spend record cites it; costs
                           # are recomputable forever against the book they were priced under.
  signature: null          # REQUIRED at Stage-1b+: operator signature over `version`
                           # (custody + verification: contracts/identity-firewall.md §pricebook-annex).
                           # [SECURITY-SEAM: a poisoned book redirects fleet routing (cheapest-lane
                           # attack) or starves it (inflated prices). Reader behavior below §6.]
  currency: USD_per_1M_tokens
  defaults:
    max_age_days: 30       # per-SKU override allowed
    stale_mult: 1.25       # estimation-only pessimism multiplier; applied UPWARD only, never downward
    refuse_after: 2.0      # lane REFUSED at age > refuse_after × max_age_days (flag-overridable)
```

### 1.2 SKU row — full field space (normative; optional fields default to "capability absent")

```yaml
skus:
  <weights>@<host>/<service_tier>:        # service_tier ∈ standard|fast|priority|flex|dedicated
    weights_family: <string>              # REQUIRED. The diversity axis (A6). Consumed by the oracle
                                          #   seat's quorum solver + the router's diversity floor.
                                          #   For third-party hosts this is a CLAIM: it is trustworthy
                                          #   only under lane-family attestation = signed book
                                          #   (declaration) + runtime canary (reality) — the canary and
                                          #   de-rate-to-zero law live in identity-firewall.md. The
                                          #   trust DIVERSITY identity flag is `family_verified`
                                          #   (oracle.md SEC-2's canary) — a DISTINCT flag with a
                                          #   distinct owner (trust plane), never a field of this
                                          #   book; diversity-counting gates on family_verified,
                                          #   NEVER parity_verified (below).
    parity_verified: false                # the ECON COST-parity flag (pricebook-owned). Third-party
                                          #   serving of open weights ⇒ parity probe required
                                          #   (constitution §7): 5 paired pulls vs first-party, |Δscore|
                                          #   ≤ 0.05 under the run's oracle → flip true (version bump).
                                          #   Cost/routing parity ONLY — diversity-counting MUST NOT
                                          #   key on this flag. A family_verified canary mismatch also
                                          #   flips this false + row stale (the parity pulls presumed
                                          #   the declared family); the diversity-contribution-ZERO
                                          #   law is family_verified's (oracle.md SEC-2), never this flag's.
    in: <usd/1M>                          # REQUIRED (token rows). Cache-MISS sticker input price.
    out: <usd/1M>                         # REQUIRED (token rows).
    cache_read_mult: <float>              # multiplier on `in` for cache-hit tokens. ABSENT ⇒ no cache
                                          #   capability (quote() treats read=1.0, capability off).
                                          #   Per-SKU FACT, never per-weights (lived: deepseek-v4-flash
                                          #   = 0.02 first-party vs 0.2 on Fireworks, same weights).
    cache_write_mult: <float>             # multiplier on `in` for cache-write tokens (Anthropic 1.25,
                                          #   OpenAI-5.6+ 1.25, DeepSeek 1.0). ABSENT ⇒ writes free.
    cache_write_mult_1h: <float>          # long-TTL write variant (Anthropic 2.0).
    cache_storage_usd_per_1M_hr: <float>  # NEW v5: explicit-cache storage RENT (Gemini 1.00–4.50).
                                          #   ê over a hold of H hours MUST add rent × H. Anthropic's
                                          #   1h-write-at-2× is the prepaid equivalent; quote() makes
                                          #   the two models comparable via expected_hold_hours.
    cache_ttl_s: <int>                    # provider prefix retention. UNDOCUMENTED ⇒ pessimistic 300.
    cache_ttl_refresh_on_hit: <bool>      # Anthropic true (documented); default false.
    cache_min_prompt_tokens: <int>        # NEW v5: minimum cacheable prompt (Anthropic 512/1024/4096
                                          #   by model; OpenAI 1024). Below it, cache terms drop out.
    cache_granularity_tokens: <int>       # prefix-match granularity (DeepSeek 64). Informational.
    cache_scope: org|key|request          # NEW v5: OpenAI caches are org-scoped (documented) — a
                                          #   fleet-wide warm-prefix asset; default `key`.
    warmer_release: on_ttft|on_complete|none
                                          # when N−1 staggered callers may read the warmer's prefix.
                                          #   on_ttft is DOCUMENTED ONLY for Anthropic ("a cache entry
                                          #   only becomes available after the first response begins",
                                          #   platform.claude.com, 2026-07-16). Default on_complete.
                                          #   An optimistic on_ttft elsewhere silently pays N writes.
    batch_kind: endpoint|window|none      # endpoint = real async batch API (submit/poll, per-item
                                          #   results). window = off-peak clock discount (no current
                                          #   seed lane: DeepSeek's discontinued 2025-09-05; enum kept
                                          #   for schema stability). none = batch dims inadmissible.
    batch_mult: <float>                   # whole-call multiplier under batch (0.5 across the industry).
    batch_window_max_h: <int>             # NEW v5: the booked OUTER completion bound (Anthropic 24,
                                          #   Groq 168). sla admissibility keys on THIS, never on the
                                          #   marketing-typical. ABSENT with batch_kind:endpoint ⇒ 24.
    stacks_with_cache: <bool|null>        # whether batch_mult × cache_read_mult compose (Anthropic,
                                          #   OpenAI: true). null ⇒ PESSIMISTIC better-of-two at quote.
    effort_map: {low: …, medium: …, high: …}   # OPTIONAL provider effort/reasoning dial → param map.
                                          #   Effort changes COUNTS (output tokens), never unit price;
                                          #   it is a lane dim priced empirically by the ledger.
    context_max: <int>
    max_output_max: <int>
    context_tiers:                        # long-context surcharges. Straddle rule (normative, and now
      - {over_tokens: 200000, in: …, out: …}   # provider-documented at xAI: the higher tier prices the
                                          #   WHOLE call when the estimate straddles the boundary).
    effective_until: <date>               # scheduled price/existence cliff. WITH successor: applied
    successor: {in: …, out: …}            #   automatically at the date. WITHOUT successor: row goes
                                          #   stale at the date (rule 6). Deprecation dates are cliffs
                                          #   too (lived: four dated cliffs within 45 days of the seed).
    requires_contract: false              # NEW v5: true = live lane, custom-priced (Cerebras dedicated
                                          #   endpoints). quote() REFUSES unless the operator has
                                          #   written a contract_price block. Never estimated.
    geo_mult: {us_only: 1.1}              # inference-geo multiplier (Anthropic documented 1.1×).
    tokenizer: {family: <str>, chars_per_token_hint: <float>}
                                          # NEW v5: cross-SKU ê conversion. Anthropic's 2026 tokenizer
                                          #   bills ~30% more tokens for the same text (documented).
                                          #   The frame manifest's est_tokens is PER-FAMILY (seam: the
                                          #   assembler (02) counts per family; quote() picks the
                                          #   matching count). ABSENT ⇒ one universal estimate, and
                                          #   cross-family ê comparisons carry that declared error.
    concurrency_cap: <int>                # fleet-side politeness cap (lived F2: z.ai 429s at 3).
                                          #   Provider-documented where available (DeepSeek 2500/500).
    tok_s_p50: <float>                    # LEDGER-DERIVED (rolling p50, last 200 calls). Hand-seeded
    ttft_p50_ms: <float>                  #   only until 20 calls accrue (rule 7). Never hand-edited after.
    liveness: null                        # LOCAL rows only; SET BY PREFLIGHT (substrate seam), never
                                          #   by hand. A degrade ladder whose terminal lane fails
                                          #   liveness = RED preflight BEFORE the run.
    electricity: {watts: <int>, usd_per_kwh: <float>, measured_at: <date>}   # local rows
    capex_amort: null                     # OPTIONAL {gpu_usd, dep_hours}; default OFF — sovereignty
                                          #   accounting counts marginal cost; operator may opt in.
    as_of: <date>                         # REQUIRED. age = today − as_of drives rules 2–4.
    source: <string>                      # REQUIRED. Primary docs > vendor page > aggregator > bench.
    verified: true|false|mixed|bench      # REQUIRED.
    promo_until: <date|null>              # a promo price MUST NOT be booked without its expiry; book
                                          #   the LIST price and note the promo (lived: qwen3.7-max).

  # ---- NON-TOKEN (tool) lanes: acts reserve here under purpose=tool ----------
  tool.<capability>@<provider>/<tier>:
    pricing_model: flat_per_call|per_second|per_unit
    per_call: <usd> | per_second: <usd> | per_unit: {unit: <str>, usd: <float>}
    worst_case: <expr>                    # a tool act with no computable worst-case is UNRESERVABLE
                                          #   ⇒ REFUSED (act seam, constitution §6).
    leaseable: true                       # NEW v5: eligible for §5.5 leases (high-rate H0 lanes).
    as_of: …; source: …; verified: …
```

### 1.3 Freshness-pessimism rules (normative, numbered — carried from v3, r6 sharpened)

1. Every SKU carries `as_of`; `age = today − as_of`.
2. `age ≤ max_age_days` → fresh: quote() uses booked values.
3. `age > max_age_days` → **stale**: every *estimation* use (reservation worst-case, UCB ê, quote)
   multiplies price by `stale_mult`. Pessimism is upward-only: reserves inflate, refusals come earlier;
   a lane never gets cheaper by neglect. `hc top` shows the stale set.
4. `age > refuse_after × max_age_days` → lane **REFUSED** at quote() unless `--allow-stale-prices`;
   the refusal names the row and the refresh command (`hc pricebook refresh <sku>`).
5. **Unknown lane** → `REFUSED(unpriced)` naming the fix (`hc pricebook add <sku>`). Override
   `--allow-unpriced` prices at the **book-wide max in/out × 1.5**, printed in the receipt. (Repeals
   v1's silent `(0.5,1.5)` at `governor.py:45`.) Applies to every spend including `hc ask`.
6. `effective_until` passed with `successor` present → successor prices apply automatically (no silent
   under-reservation). Passed without successor → the row goes stale at the date. **A provider-announced
   deprecation date is an `effective_until`**; past it the lane is REFUSED (not merely stale) — a dead
   model name is not a stale price, it is no price.
7. `tok_s_p50 / ttft_p50_ms` are ledger-derived (rolling p50 over the last 200 calls per SKU); the
   hand-seeded value yields after 20 calls accrue.
8. Local SKU `as_of` is set only by the bench job (`hc econ bench-local`: re-measure tok/s + watts).
9. `requires_contract:true` rows and `verified:false` rows are quotable but every quote/receipt carries
   the flag; `requires_contract` without a written `contract_price` block ⇒ REFUSED.

### 1.4 Monthly invoice reconciliation (the truth pass — carried verbatim from v3 §2.5)

`hc econ reconcile --month YYYY-MM`: fold the conductor spend ledger → Σ `usd_effective` + Σ tokens by
`(host, sku, service_tier)`; ingest provider billing exports; per group `drift = (invoice − ledger) /
ledger`. `|drift| ≤ 2%` OK · `2–10%` `pricebook_drift` event, row flagged · `>10%` **alarm**: row marked
stale immediately (rule-3 pessimism fleet-wide) + the diagnosis fork: token totals match ⇒ *price* wrong
⇒ update the book; token totals differ ⇒ *adapter under-reports usage* ⇒ adapter-bug ticket. Verified
rows get fresh `as_of`; `version` bumps; costs stay recomputable per priced-under version.

## 2 · The seed book (v5.0, every row dated 2026-07-16; sources in the seat-07 paper PART E)

```yaml
# pricebook.yaml — SEED as of 2026-07-16. verified:true = primary provider docs fetched that day.
skus:
  deepseek-v4-flash@deepseek/standard:
    {weights_family: deepseek, in: 0.14, out: 0.28, cache_read_mult: 0.02,
     cache_ttl_s: 300, cache_granularity_tokens: 64, warmer_release: on_complete, batch_kind: none,
     context_max: 1000000, max_output_max: 384000, concurrency_cap: 2500, parity_verified: true,
     as_of: 2026-07-16, source: "api-docs.deepseek.com/quick_start/pricing", verified: true}
  deepseek-v4-pro@deepseek/standard:
    {weights_family: deepseek, in: 0.435, out: 0.87, cache_read_mult: 0.0083,
     cache_ttl_s: 300, warmer_release: on_complete, batch_kind: none, context_max: 1000000,
     max_output_max: 384000, concurrency_cap: 500, parity_verified: true,
     as_of: 2026-07-16, source: "api-docs.deepseek.com (v3's 1.74 booked price STALE: 4x drop)", verified: true}
  kimi-k2.6@moonshot/standard:
    {weights_family: kimi, in: 0.95, out: 4.00, cache_read_mult: 0.168, context_max: 262144,
     warmer_release: on_complete, parity_verified: true,
     as_of: 2026-07-16, source: "platform.kimi.ai/docs/pricing/chat-k26", verified: true}
  kimi-k3@moonshot/standard:
    {weights_family: kimi, in: 3.00, out: 15.00, cache_read_mult: 0.1, context_max: 1048576,
     warmer_release: on_complete, parity_verified: true,
     as_of: 2026-07-16, source: "platform.kimi.ai/docs/pricing/chat-k3", verified: true}
  kimi-k2@groq/standard:
    {weights_family: kimi, in: 1.00, out: 3.00, cache_read_mult: 0.5,
     batch_kind: endpoint, batch_mult: 0.5, batch_window_max_h: 168, stacks_with_cache: null,
     warmer_release: on_complete, parity_verified: false,
     as_of: 2026-07-16, source: "groq.com/pricing", verified: true}
  kimi-k2.6@together/standard:
    {weights_family: kimi, in: 1.20, out: 4.50, cache_read_mult: 0.167, parity_verified: false,
     as_of: 2026-07-16, source: "together.ai/pricing", verified: true}
  kimi-k2.6@fireworks/standard:
    {weights_family: kimi, in: 0.95, out: 4.00, cache_read_mult: 0.168,
     batch_kind: endpoint, batch_mult: 0.5, parity_verified: false,
     as_of: 2026-07-16, source: "docs.fireworks.ai/serverless/pricing", verified: true}
  kimi-k2.6@fireworks/fast:
    {weights_family: kimi, in: 2.00, out: 8.00, cache_read_mult: 0.15, parity_verified: false,
     as_of: 2026-07-16, source: "docs.fireworks.ai (fast tier)", verified: true}
  glm-5.2@zai/standard:
    {weights_family: glm, in: 1.40, out: 4.40, cache_read_mult: 0.186, concurrency_cap: 3,
     warmer_release: on_complete, parity_verified: true,
     as_of: 2026-07-16, source: "docs.z.ai/guides/overview/pricing (concurrency: lived F2)", verified: true}
  glm-4.7-flashx@zai/standard:
    {weights_family: glm, in: 0.07, out: 0.40, cache_read_mult: 0.143, parity_verified: true,
     as_of: 2026-07-16, source: "docs.z.ai (screen-judge candidate)", verified: true}
  glm-4.7-flash@zai/standard:
    {weights_family: glm, in: 0.0, out: 0.0, parity_verified: true,
     as_of: 2026-07-16, source: "docs.z.ai (free lane; free != unpriced)", verified: true}
  claude-fable-5@anthropic/standard:
    {weights_family: anthropic, in: 10.00, out: 50.00, cache_read_mult: 0.1, cache_write_mult: 1.25,
     cache_write_mult_1h: 2.0, cache_ttl_s: 300, cache_ttl_refresh_on_hit: true,
     cache_min_prompt_tokens: 512, max_cache_breakpoints: 4, warmer_release: on_ttft,
     batch_kind: endpoint, batch_mult: 0.5, batch_window_max_h: 24, stacks_with_cache: true,
     geo_mult: {us_only: 1.1}, context_max: 1000000, parity_verified: true,
     tokenizer: {family: anthropic-2026, chars_per_token_hint: 3.1},
     as_of: 2026-07-16, source: "platform.claude.com/docs/en/about-claude/pricing", verified: true}
  claude-opus-4.8@anthropic/standard:
    {weights_family: anthropic, in: 5.00, out: 25.00, cache_read_mult: 0.1, cache_write_mult: 1.25,
     cache_write_mult_1h: 2.0, cache_ttl_s: 300, cache_ttl_refresh_on_hit: true,
     cache_min_prompt_tokens: 1024, max_cache_breakpoints: 4, warmer_release: on_ttft,
     batch_kind: endpoint, batch_mult: 0.5, batch_window_max_h: 24, stacks_with_cache: true,
     geo_mult: {us_only: 1.1}, context_max: 1000000, parity_verified: true,
     tokenizer: {family: anthropic-2026, chars_per_token_hint: 3.1},
     as_of: 2026-07-16, source: "platform.claude.com pricing", verified: true}
  claude-opus-4.8@anthropic/fast:
    {weights_family: anthropic, in: 10.00, out: 50.00, cache_read_mult: 0.1, cache_write_mult: 1.25,
     batch_kind: none, parity_verified: true, tokenizer: {family: anthropic-2026, chars_per_token_hint: 3.1},
     as_of: 2026-07-16, source: "platform.claude.com (research preview; fast+batch incompatible)", verified: true}
  claude-sonnet-5@anthropic/standard:
    {weights_family: anthropic, in: 2.00, out: 10.00, cache_read_mult: 0.1, cache_write_mult: 1.25,
     cache_write_mult_1h: 2.0, cache_min_prompt_tokens: 1024, warmer_release: on_ttft,
     batch_kind: endpoint, batch_mult: 0.5, batch_window_max_h: 24, stacks_with_cache: true,
     effective_until: 2026-08-31, successor: {in: 3.00, out: 15.00, cache_read: 0.30},
     context_max: 1000000, parity_verified: true,
     tokenizer: {family: anthropic-2026, chars_per_token_hint: 3.1},
     as_of: 2026-07-16, source: "platform.claude.com (provider prints the successor itself)", verified: true}
  claude-haiku-4.5@anthropic/standard:
    {weights_family: anthropic, in: 1.00, out: 5.00, cache_read_mult: 0.1, cache_write_mult: 1.25,
     cache_min_prompt_tokens: 4096, warmer_release: on_ttft, batch_kind: endpoint, batch_mult: 0.5,
     batch_window_max_h: 24, stacks_with_cache: true, parity_verified: true,
     as_of: 2026-07-16, source: "platform.claude.com pricing", verified: true}
  gpt-5.6-sol@openai/standard:
    {weights_family: openai, in: 5.00, out: 30.00, cache_read_mult: 0.1, cache_write_mult: 1.25,
     cache_ttl_s: 1800, cache_min_prompt_tokens: 1024, cache_scope: org, warmer_release: on_complete,
     batch_kind: endpoint, batch_mult: 0.5, batch_window_max_h: 24, stacks_with_cache: true,
     parity_verified: true, as_of: 2026-07-16, source: "developers.openai.com/api/docs/pricing", verified: true}
  gpt-5.6-sol@openai/priority:
    {weights_family: openai, in: 20.00, out: 120.00, parity_verified: true,
     as_of: 2026-07-16, source: "developers.openai.com (4x standard)", verified: true}
  gpt-5.6-sol@openai/flex:
    {weights_family: openai, in: 2.50, out: 15.00, parity_verified: true,
     as_of: 2026-07-16, source: "developers.openai.com (0.5x, queued)", verified: true}
  gpt-5.6-luna@openai/standard:
    {weights_family: openai, in: 1.00, out: 6.00, cache_read_mult: 0.1, cache_write_mult: 1.25,
     cache_ttl_s: 1800, cache_min_prompt_tokens: 1024, cache_scope: org,
     batch_kind: endpoint, batch_mult: 0.5, parity_verified: true,
     as_of: 2026-07-16, source: "developers.openai.com", verified: true}
  gemini-3.5-flash@google/standard:
    {weights_family: gemini, in: 1.50, out: 9.00, cache_read_mult: 0.1,
     cache_storage_usd_per_1M_hr: 1.00, batch_kind: endpoint, batch_mult: 0.5,
     warmer_release: on_complete, parity_verified: true,
     as_of: 2026-07-16, source: "ai.google.dev/gemini-api/docs/pricing", verified: true}
  gemini-3.1-pro-preview@google/standard:
    {weights_family: gemini, in: 2.00, out: 12.00, cache_read_mult: 0.1,
     cache_storage_usd_per_1M_hr: 4.50, context_tiers: [{over_tokens: 200000, in: 4.00, out: 18.00}],
     batch_kind: endpoint, batch_mult: 0.5, warmer_release: on_complete, parity_verified: true,
     as_of: 2026-07-16, source: "ai.google.dev pricing", verified: true}
  gemini-3.1-flash-lite@google/standard:
    {weights_family: gemini, in: 0.25, out: 1.50, batch_kind: endpoint, batch_mult: 0.5,
     parity_verified: true, as_of: 2026-07-16, source: "ai.google.dev pricing", verified: true}
  grok-4.3@xai/standard:
    {weights_family: grok, in: 1.25, out: 2.50, cache_read_mult: 0.16,
     context_tiers: [{over_tokens: 200000, in: 2.50, out: 5.00}], context_max: 1000000,
     warmer_release: on_complete, parity_verified: true,
     as_of: 2026-07-16, source: "docs.x.ai/docs/models (whole-call tier rule provider-documented)", verified: true}
  qwen3.5-plus@alibaba/standard:
    {weights_family: qwen, in: 0.40, out: 2.40,
     context_tiers: [{over_tokens: 256000, in: 0.50, out: 3.00}],
     batch_kind: endpoint, batch_mult: 0.5, parity_verified: true,
     as_of: 2026-07-16, source: "Model Studio via aggregators — primary unfetched", verified: false}
  qwen3.7-max@alibaba/standard:
    {weights_family: qwen, in: 2.50, out: 7.50, promo_until: null,   # promo 1.25/3.75 NOT booked (no expiry)
     batch_kind: endpoint, batch_mult: 0.5, parity_verified: true,
     as_of: 2026-07-16, source: "aggregators; LIST price booked, promo noted", verified: false}
  gpt-oss-120b@groq/standard:
    {weights_family: gpt-oss, in: 0.15, out: 0.60, batch_kind: endpoint, batch_mult: 0.5,
     batch_window_max_h: 168, tok_s_p50: 500, parity_verified: false,
     as_of: 2026-07-16, source: "groq.com/pricing (vendor TPS = upper bound)", verified: true}
  gpt-oss-120b@cerebras/standard:
    {weights_family: gpt-oss, in: 0.35, out: 0.75, tok_s_p50: 1500, parity_verified: false,
     as_of: 2026-07-16, source: "cerebras rate card via aggregators; speed 1000-2100 measured-class", verified: false}
  kimi-k2.6@cerebras/dedicated:
    {weights_family: kimi, requires_contract: true, parity_verified: false,
     as_of: 2026-07-16, source: "cerebras.ai/pricing — dedicated endpoints, custom pricing; REFUSED without contract_price", verified: true}
  llama-3.3-70b@groq/standard:
    {weights_family: llama, in: 0.59, out: 0.79, batch_kind: endpoint, batch_mult: 0.5,
     batch_window_max_h: 168, tok_s_p50: 394, parity_verified: false,
     as_of: 2026-07-16, source: "groq.com/pricing", verified: true}
  deepseek-v4-pro@together/standard:      # kept as the parity-probe exhibit: 4x first-party, same weights
    {weights_family: deepseek, in: 1.74, out: 3.48, cache_read_mult: 0.115, parity_verified: false,
     as_of: 2026-07-16, source: "together.ai/pricing", verified: true}

  # ---- the local floor (island law): per-class rows, bench-owned ------------
  qwen3.5-9b-q5@local-4090/standard:
    {weights_family: qwen, in: 0.00, out: 0.133,      # 350W × $0.15/kWh ÷ (110 tok/s × 3.6)
     out_batched: 0.02, tok_s_p50: 110, cache_read_mult: 0.0, parity_verified: true,
     electricity: {watts: 350, usd_per_kwh: 0.15, measured_at: null},
     liveness: null, as_of: null, source: "electricity formula + bench job (v3's 100-tok/s
       32B seed was a 9B-class figure — corrected per 2026 benches: 9B=90-140, 32B=30-45 tok/s)",
     verified: bench}
  qwen3-32b-q4@local-4090/standard:
    {weights_family: qwen, in: 0.00, out: 0.38,       # 350W × $0.15/kWh ÷ (38 tok/s × 3.6)
     out_batched: 0.08, tok_s_p50: 38, cache_read_mult: 0.0, parity_verified: true,
     electricity: {watts: 350, usd_per_kwh: 0.15, measured_at: null},
     liveness: null, as_of: null, source: "electricity formula + bench job", verified: bench}

  # ---- non-token lanes -------------------------------------------------------
  tool.web.search@provider-x/standard:
    {pricing_model: flat_per_call, per_call: 0.01, leaseable: true,
     as_of: 2026-07-16, source: "connector price sheet (Anthropic server-side web search comparator:
       $10/1k searches = $0.01/call, platform.claude.com)", verified: mixed}
  tool.code.run@sandbox-local/standard:
    {pricing_model: per_second, per_second: 0.00002, worst_case: "timeout_s × per_second",
     leaseable: true, as_of: null, source: "bench (electricity share)", verified: bench}
```

## 3 · `quote()` — the DECIDE interface (consumed by route/run planes; seam #1, re-confirmed)

```
quote(frame_manifest, lanes[], purpose) → per lane:
  { usd_expected,            # cache/batch/stale/tier-aware estimate (warm-state × multipliers)
    usd_worst,               # the reservation number (§4.1)
    warm_frac,               # T_warm / T_total under current warmth state
    ttft_p50_ms, tok_s_p50,  # ledger-derived
    stale: bool, verified: …, requires_contract: bool,
    window_close_eta, expiry_at,   # batch lanes only (NEW v5 — seat 04's park-vs-wait pricing)
    refused: null | {reason: unpriced|stale|dead|unreservable|contract_required, fix: "<command>"} }
```

Normative quote arithmetic: cache-miss sticker unless warm-state proves otherwise; batch and cache
multipliers compose only where `stacks_with_cache:true`, else better-of-two; `context_tiers` straddle
prices the whole call at the higher tier; `effective_until`/`successor` applied at evaluation date;
stale ⇒ ×`stale_mult`; storage-rent lanes add `rent × expected_hold_hours`; est_tokens taken from the
frame manifest **per tokenizer family** where the book declares one.

## 4 · ENFORCE — the escrow protocol (reservation is the only path to spend)

One escrow object in the Conductor. **Truth-home: the conductor's own ledger** (fsync'd RESERVE /
COMMIT / RELEASE / SPEND records). Scope counters (`{cap, committed, reserved}` for fleet, per-run,
per-purpose) are **in-memory folds over those records**, rebuilt on restart by fold + `reconcile()` —
never trusted from RAM (fold law; repeals live `Governor.spent`, `governor.py:39`). Spend records DO
NOT cross the Medium; fleet-visible attribution rides the `cost{}` field-group (§5.2) on records
already crossing (receipt / act_receipt / cmd_receipt / verdict / StackReceipt). [v2 §7 kept: "no new payload type";
v3's Medium `type:spend` repealed — seat-01 ruling #687 + seat-07 retraction #694.]

### 4.1 Pessimistic worst-case (unchanged from v3, normative)

```
worst(call) = T_in_known × p_in_max + max_tokens × p_out_max + per_call_fees
  T_in_known: frame-manifest est_tokens_total (per tokenizer family), ALL input priced cache-miss
  p_*_max:    booked × stale_mult if stale × context-tier ceiling if straddling
  max_tokens: REQUIRED — a request without max_tokens is UNRESERVABLE ⇒ REFUSED
  retries:    each retry attempt is a NEW reservation (a 429 storm is gated per attempt)
```

### 4.2 Operations (atomic under one writer lock; numbered)

```
reserve(lane, worst, scopes, group_id=None, durability="res:sync") → resv_id | REFUSED(scope, headroom)
  1. for s in scopes (fixed order fleet→run→purpose): if s.committed + s.reserved + worst > s.cap:
       return REFUSED(s, headroom)
  2. for s in scopes: s.reserved += worst
  3. append+fsync RESERVE{resv_id, worst, scopes, lane, ttl, durability, provider_ref?} to conductor ledger
  4. return resv_id

reserve_group(items[N]) → admitted k ≤ N     # ONE lock acquisition; greedy in dispatch order;
                                             # partial admission is an EXPLICIT receipt, never silent
commit(resv_id, api_actuals) → spend record
  1. usd = price(actuals, pricebook@dispatch_version)
  2. usd > worst ⇒ OVERRUN alarm (indicts estimator/adapter, bounded to one call) — commit anyway, row stale
  3. scopes: committed += usd; reserved −= worst
  4. append SPEND record (§5); return
release(resv_id, reason)                     # reserved −= worst; append RELEASE{reason}

reconcile()                                  # RESUME path — runs BEFORE the first new reserve
  res:sync with no terminal record  → provider usage API answers ⇒ commit(actuals);
                                      else commit(worst, outcome="unknown")   # in-doubt spend is REAL
  res:durable with no terminal      → rebuild STILL-HELD (record carries provider batch_id); settle only
                                      by the receipted H0 reconciliation act (04's WAITING-BATCH consumes
                                      this; 06's probe-admission predicate governs the poll)
  res:lease with no terminal        → rebuild STILL-HELD; settle from the leaseholder's own receipts (§4.5)
  then rebuild all scope counters by fold over surviving rows.

sweep()  # every 60s: RESERVE past ttl with no terminal → reconcile that id (NEVER blind-release)
```

### 4.3 Zero-overshoot statement (amended honestly for leases)

Premises P1 (all spend flows through commit — import-graph-enforced: only `cognition/metered.py`
imports provider adapters), P2 (every commit references a prior reserve), P3 (reserve atomic + refusing),
P4 (`actual ≤ worst`: input counted, output provider-capped, prices pessimistic-stale, tier ceiling) ⇒
by induction over the ledger's total order, `committed_s ≤ cap_s` at every prefix, for every scope.
**With leases (§4.5): the invariant holds at fleet/run/purpose scopes by construction (the quantum was
reserved); within a lease the cell self-meters, so the worst uncounted exposure is ≤ one lease quantum
per cell×lane — and the fleet-aggregate lease-overshoot bound is max concurrent leaseholders × quantum,
itself bounded by fleet slots × quantum** — printed, capped, and drilled (ECON-LEASE-1 asserts against
that aggregate number), never hidden. The only P4 escape is a
provider billing above its own enforced ceiling — bounded to one call by the OVERRUN alarm and caught
structurally at monthly reconciliation.

### 4.4 Reservation durability classes (carried; adjudication #6a)

`res:sync` — folds to zero on resume; work re-dispatches under its idem key; in-flight settled by
reconcile(). `res:durable` — batch submissions / racing legs; carries provider `batch_id`; folds
STILL-HELD; released only by a receipted reconciliation act (`ok | expired | lost`, waste-flagged).

### 4.5 `res:lease` — tool-lane micro-escrow (NEW v5; seat-06 seam, #671 T10 + #679)

High-rate H0 tool lanes (grounded search/fetch) MUST NOT serialize through the Conductor per call.

```
1. lease(cell, lane, quantum) = reserve(lane, worst=quantum, scopes=[fleet, run, purpose:tool],
   durability="res:lease", holder=claim_id) — the quantum is REAL reserved headroom.
2. The leaseholder draws down locally: each act's receipt carries cost{resv_id: lease_id, usd_effective}
   (the cell's own receipts ARE the drawdown log; no conductor round-trip).
3. Renewal (quantum exhausted or ttl): the conductor folds the holder's receipts since grant,
   commit(actual_total), release(remainder), issue the next lease. Renewal is the reconciliation point.
4. Crash: the lease folds STILL-HELD; reconcile() settles from the holder's receipts on the Medium/its
   nucleus; unreceipted remainder commits at worst (in-doubt law).
5. Admissibility: lane.leaseable == true AND pricing_model has computable per-call worst-case AND
   harm class == H0. Everything else reserves per-call.
```

### 4.6 Purposes as scopes (carried) + the null's escrow (04#683c mechanics, mine)

`purposes: {production frac · verification reserve_frac (a FLOOR — production headroom is computed net
of the unspent reserve) · oracle_growth cap_frac (a CEILING; a refused growth reservation is a receipt,
not an error) · tool frac · maintenance cap_frac}`. Two-phase grading prices phase-B under
`purpose=verification` — grader spend is attributable and the verifier's lunch is protected by
reservation, not hope. **Null modes:** UNSETTLED class ⇒ `mode:matched`: matched-dollar reservation
taken at `run_open` (res:sync, inside purpose=verification). SETTLED-CALIBRATED ⇒ `mode:floor`: ≥10%
of production budget reserved at `run_open` for the null arm + `audit_rate` (default 0.25 — sized so
the trailing k=20 flip window can hold ≥ m=5 audited rows by construction, 05 #695) sampled matched
replays, reserved at selection. Both modes make the control's dollars **protected by reservation
first** — the allocator cannot starve the control.

## 5 · Record shapes

### 5.1 SPEND record (conductor ledger; NOT a Medium type)

```jsonc
{ "rec": "spend",
  "corr": "run-r7", "run_id": "r7", "arm_id": "arm3", "step_id": "s12",
  "issuer": "r7/arm3/0",                       // claim-id, or "conductor" for plane-side calls
  "purpose": "production|verification|oracle_growth|tool|maintenance",
  "attribution": "candidate|apparatus|null",   // NEW v5 (joint row w/ 04+05, #683b):
                                               //   apparatus ⇒ NOT charged to arm.usd_spent for the
                                               //   dollar-UCB index; folds run-level apparatus_usd
  "sku": "deepseek-v4-flash@deepseek/standard",
  "lane": {"effort": "medium", "cache_mode": "auto", "batch": false},
  "tokens": {"in": 9120, "out": 512, "cache_read": 8100, "cache_write": 1020},
  "usd_sticker": 0.001420,                     // all tokens at cache-miss — the counterfactual
  "usd_effective": 0.000391,                   // at booked multipliers — what we believe we owe
  "usd_reserved": 0.000912,                    // the escrow worst-case this call held
  "api_reported_usd": null,                    // provider-reported actual where the API returns one
  "pricebook_version": "sha256:…",             // recomputable forever
  "latency_ms": {"queue": 40, "ttft": 610, "total": 2410},
  "retries": 0, "outcome": "ok|error|429|timeout|cancelled|unknown",
  "resv_id": "01J8…", "batch_id": null, "race_group": null,
  "waste_flag": null }   // racing_loser | batch_expired | apparatus_invalid | null
```

### 5.2 `cost{}` field-group (rides Medium records that already cross: receipt / act_receipt / cmd_receipt / verdict / StackReceipt)

```jsonc
"cost": { "usd_effective": 0.000391, "usd_reserved": 0.000912, "sku": "…", "purpose": "…",
          "resv_id": "01J8…", "pricebook_version": "sha256:…" }
```

This is v2 §7's original design, kept: fleet-visible spend attribution without a new payload type.
`hc top`, the null ledger, and `vs_null{matched_production, matched_invoice}` are conductor renders
over the conductor ledger; the Medium `cost{}` groups are the cross-check join (StackReceipt joins
suffice — confirmed with seats 01/03/05, #687/#694/#695/#698). An `hc ask`'s dollars are visible as
`cmd_receipt{phase:result}.cost{}` — the degeneracy arithmetic's one Medium-side money line.

### 5.3 `CompletionResult` v5 (the M1 fields; `cognition/base.py` migration)

```python
class CompletionResult(BaseModel):
    text: str; model: str
    prompt_tokens: int = 0; completion_tokens: int = 0
    cache_read_tokens: int = 0        # NEW — adapters MUST surface provider usage detail
    cache_write_tokens: int = 0       # NEW
    api_reported_usd: float | None = None   # NEW — populate cost_usd's dormant slot (F26)
    cost_usd: float = 0.0             # EXISTS TODAY, never populated (base.py:24) — M1 fills it
    raw: dict | None = None
```

## 6 · Reader-liberality note (G4 discipline)

Readers MUST ignore unknown SKU fields (forward-compat: new pricing dimensions arrive quarterly — this
refresh alone added five). Readers MUST NOT invent absent capabilities: absent `cache_read_mult` = no
cache, absent `batch_kind` = `none`, absent `warmer_release` = `on_complete`, absent
`stacks_with_cache` = better-of-two. A row failing REQUIRED fields (`in/out` or `pricing_model`,
`as_of`, `source`, `verified`, `weights_family` for token rows) **does not parse** — the book loader
refuses the whole file with the row named (a half-parsed pricebook is worse than none). Unknown
`service_tier` strings are legal (new tiers keep arriving); unknown `pricing_model` strings are NOT
(the escrow cannot compute worst-case for a model it does not know ⇒ that row unreservable).
Signature verification (`signature` field): at Stage-1b+ a book failing verification is REFUSED
entirely; below Stage-1b the loader warns and proceeds (the ladder's honesty rule — never pretend a
check that cannot run yet passed). [SECURITY-SEAM: verification mechanics, key custody, and the
canary/de-rate law are identity-firewall.md's; this contract only carries the field and the refusal.]

## 7 · Migration note (live v1 → v5)

| live v1 (today) | v5 | how |
|---|---|---|
| `_PRICE` dict, `governor.py:14-27` | `pricebook.yaml` + loader | M1: dict deleted; loader refuses unknown lanes (repeals `:45`'s silent `(0.5,1.5)`) |
| `Governor.spent` float, `governor.py:39` | fold over conductor-ledger RESERVE/COMMIT/RELEASE | M2: `check()/record()` → `reserve()/commit()/release()`; `reconcile()` before first reserve on resume (repeals L8) |
| per-run `Governor()`, `drive.py:63` | runs open a *scope*, not an instance | M2 (repeals L6) |
| raw `build_cognition()` at `commander.py:116` and `topology.py:148` | all cognition through `cognition/metered.py` | M2 + import-graph conformance test (repeals L6b, L6c/F25) |
| `CompletionResult` 2 usage fields; `cost_usd` dormant (`base.py:17-25`) | §5.3 shape | M1 — additive, zero control-flow change (F26: fields half-exist) |
| no batch/cache/tier awareness anywhere | lane dims + SKU tiers | M3 with dollar-UCB + stagger |
| spend visible only as a run-end printout | SPEND records + `cost{}` groups + `hc top` named queries | M1 emits, 08 renders |

Readers of v1 artifacts: a v1 run log carries no `resv_id`/`pricebook_version`; the migration fold
backfills `attribution:"candidate"`, `pricebook_version:"pre-v5"` — old spend is visible, marked, and
never silently re-priced.

