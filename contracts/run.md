# CONTRACT: run — the run manifest (declare a swarm; the fabric reconciles to it)

**Status:** v0.1 DRAFT. A run is a **declarative manifest** — `hc apply -f run.yaml` — reproducible and
shareable, the same philosophy as the substrate under it. Topologies are declared, not hard-coded
(constitution §6). RFC-2119.

## Fields
```yaml
run_id: r7                    # stable; roster claim-ids derive from it (run/role/index)
goal: "Implement is_valid(ip) for IPv4 and pass the checker."
topology: tournament          # tournament | mcts | pipeline | mapreduce | free-swarm
roster:                       # the cells to spawn (each references a role manifest)
  - { role: examples/refiner.role.yaml, count: 4, diversify: true }
  - { role: examples/judge.role.yaml,   count: 1 }
oracle:                       # the EXTERNAL, coordinator-run falsifier (see contracts/oracle.md)
  mode: target                # golden | target | gate | judge-panel
  cmd: "python oracles/ipv4_check.py"
  target: 1.0
  tolerance: 0.0
budget:                       # the cost governor (hard-stop)
  usd_cap: 2.00
  per_provider_concurrency: { deepseek: 8, cerebras: 2 }
termination:
  max_rounds: 3
  stable_k: 2                 # converge when champion is stable for k non-improving proposals
seed_diversity: true          # MUST for convergent topologies (HC-4): vary provider/prompt/seed per slot
isolate: false                # false → pooled processes on Runner pods; true → pod+PVC per cell
```

## Semantics (MUST)
- **Convergent topologies (tournament/mcts/free-swarm) REQUIRE an `oracle` and `seed_diversity: true`.** A
  swarm that grades itself, or that is N identical cells, converges on confident mediocrity.
- The **budget hard-stop** is enforced on the single metering path (HC-8); a run that would breach the cap
  stops and reports, never overruns.
- `isolate: true` promotes each cell to its own pod + PVC (heavy/untrusted work); default is pooled.
- A run is resumable: `hc resume <run_id>` re-binds every roster claim-id and continues.
