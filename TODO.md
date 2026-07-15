# hypercell — TODO / backlog (someday, later, etc.)

Deprioritized items, parked here on 2026-07-15 so we can focus on **driving the swarm on
command**. Nothing here blocks local use. See `log_notes.md` for full context.

## k3s / substrate (the on-cluster ladder — parked)
- [ ] **Make the WSL keepalive permanent.** k3s in WSL2 flaps unless a `wsl … sleep infinity`
      session holds the distro open (WSL2 idle-powers-off the distro; systemd services don't
      count as "busy"). Durable fix: `C:\Users\user\.wslconfig` → `[wsl2]\nvmIdleTimeout=-1`
      then `wsl --shutdown` (k3s is `enabled`, auto-starts on boot).
- [ ] **Close HC-7** — run a cell as an isolated pod (`--isolate`) so untrusted candidate code
      executes in a container sandbox (the on-cluster boundary now exists; conductor proven).
- [ ] **On-pods distributed fan-out (P3).** Today the tournament fans out cells as in-process
      async tasks; the conductor pod hosts a cell in-process. Wire real cell-pods + a `/run`
      endpoint on the conductor API so a tournament fans out across pods on k3s.
- [ ] **Clean image rebuilds.** docker.io conflicts with k3s (2nd containerd + FORWARD DROP);
      it's stopped+disabled. Switch to `nerdctl`+buildkit on k3s's own containerd for rebuilds.

## capability
- [ ] **GLM concurrency=1 + 429 backoff → the HC-4 mixed tournament** (GLM/mixed vs DeepSeek's
      isdigit/٤ blind spot). NOTE: a 6-cell DeepSeek roster already hit 1.0000 on 2026-07-15,
      so the blind spot is roster-size + goal-wording sensitive, not purely provider-family.
- [x] **Judge-panel oracle for open tasks — DONE (2026-07-15).** `conductor/engine/judge.py`:
      N independent judges score each candidate (median -> 0..1), wired into the tournament as
      `--judge N` and into `hc talk` ("converge on the best X" -> judged champion). MVP judges
      share the base provider; **cross-family judging (different providers) is the next diversity
      upgrade** (the strongest guard against a shared blind spot).
- [ ] **Grounding: give cells tools, web search first.** The other half of "make the swarm
      trustworthy". Cells answer from training knowledge and drift (the pitch demo proved it);
      a web-search tool-use loop in the cell turns "research X" into grounded, cited answers.
      Biggest remaining usefulness unlock and the foundation for the org-automation north star.
- [ ] **NATS/JetStream transport swap** (Medium at multi-node scale) · **COW-fork = MCTS over
      agent state** · **phone `/fire` surface**.

## surfaces / driving
- [ ] **MobaXterm / SSH driving:** install hypercell natively in WSL Ubuntu + `openssh-server`
      so you SSH in and drive `hc run tournament …` on Linux (same env as the pods).
- [ ] **Lite CLI / API run-endpoint** so a thin remote client can command spawns over HTTP.

## housekeeping
- [ ] **GitHub remote + first push** (Bo's call; hypercells.org registered). `.dockerignore`,
      `tools/medium_viewer.py`, `TODO.md` are new uncommitted files.
- [ ] Correct the `everywhere` memory (it's FINISHED, not pre-implementation).
