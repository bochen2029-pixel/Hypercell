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
- [ ] **Judge-panel oracle for prose/research tasks.** The fan-out currently converges only on
      tasks with an *external verifier* (code + a checker script). To throw open-ended
      research/prose at the swarm ("conduct this research, give me the answer"), build a
      diverse-provider judge-panel oracle (the Externality Principle for NL).
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
