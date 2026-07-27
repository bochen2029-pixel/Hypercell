"""hypercell wire & contract types (the frozen sovereign layer, in code).

Mirrors `contracts/*.md`. Frozen pydantic v2 models. A change here is a semver bump in lockstep with the
contract doc and the JSON Schema. Nothing in this module imports a sibling project (KEEL/Intercom/REEL/
FLOTILLA/the brain) — hypercell is de novo.
"""
from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import AliasChoices, BaseModel, ConfigDict, Field


class Depth(StrEnum):
    """The cell depth dial (constitution A1, contracts/role.md)."""

    d0 = "d0"  # reflex: a bare provider call, no memory
    d1 = "d1"  # worker: one perceive -> act -> checkpoint loop
    d2 = "d2"  # resident: a long-lived specialist (REEL rings)
    d3 = "d3"  # brain: a self-closing loop (KEEL-class, over protocol)


class Topology(StrEnum):
    tournament = "tournament"
    mcts = "mcts"
    pipeline = "pipeline"
    mapreduce = "mapreduce"
    free_swarm = "free-swarm"


class MessageType(StrEnum):
    announce = "announce"
    depart = "depart"
    chat = "chat"
    status = "status"
    task = "task"
    claim = "claim"
    submission = "submission"
    receipt = "receipt"
    round_open = "round_open"
    verdict = "verdict"
    handoff = "handoff"
    command = "command"


class OracleMode(StrEnum):
    golden = "golden"
    target = "target"
    gate = "gate"
    judge_panel = "judge-panel"


class Outcome(StrEnum):
    """The oracle exit tri-state (contracts/oracle.md). INVALID is excluded, never a zero score."""

    passed = "passed"  # exit 0
    gate = "gate"  # exit 1, a real negative result
    invalid = "invalid"  # exit 2, error/timeout -> excluded


class HarmClass(StrEnum):
    H0 = "H0"  # log-only
    H1 = "H1"  # fenced-auto
    H2 = "H2"  # auto-after-a-cancelable-delay
    H3 = "H3"  # human-always


class _Frozen(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class ProviderConfig(_Frozen):
    """The swappable cognition seam config (contracts/role.md). Provider is config, not code."""

    # `weights_family` is the v5 spelling (role.md §3's d0 manifest example); `provider` is the v1
    # one. The attribute stays `.provider` so the pricebook, the metered path and drive do not move
    # — the rename is accepted at the door and canonicalised, which is what a migration shim IS.
    provider: str = Field(default="deepseek", validation_alias=AliasChoices("provider", "weights_family"))
    model: str = "deepseek-chat"
    base_url: str | None = None  # None -> registry default
    key_ref: str | None = None  # env var / secret holding the key; None -> "<PROVIDER>_API_KEY"
    params: dict[str, Any] = Field(default_factory=dict)


class Artifact(_Frozen):
    path: str
    bytes: int
    lines: int | None = None
    mime: str = "text/plain"
    manifest: str | None = None


#: Depth-default frame ratios (role.md §3, the one table the runtime branches on). d0 bypasses the
#: assembler (`prompt + percept`), so it has no row. Field order: identity, tools, digest, working,
#: retrieved, recap, percept, slack.
_RATIO_DEFAULTS: dict[Depth, dict[str, float]] = {
    Depth.d1: {"identity": .10, "tools": .08, "digest": 0.0, "working": .12,
               "retrieved": 0.0, "recap": .25, "percept": .35, "slack": .10},
    Depth.d2: {"identity": .08, "tools": .08, "digest": .12, "working": .10,
               "retrieved": .14, "recap": .18, "percept": .22, "slack": .08},
    Depth.d3: {"identity": .08, "tools": .06, "digest": .18, "working": .10,
               "retrieved": .18, "recap": .12, "percept": .20, "slack": .08},
}
_RECAP_K_DEFAULTS: dict[Depth, int] = {Depth.d1: 8, Depth.d2: 12, Depth.d3: 12}
#: SALIENCE_v1 weights (nucleus.md §7.3). Same at every depth; a weight change bumps salience/1.x.
_SALIENCE_V1 = {"w_pin": 4.0, "w_factual": 2.0, "w_task": 1.5, "w_recency": 1.0, "w_ref": 0.5, "half_life": 512.0}


class FrameCfg(_Frozen):
    """The frame assembler's knobs (role.md §3). `None` means 'take the depth default' — the whole
    A1 mechanism: depth is a defaults preset over ONE field space, so a role sets a ratio only to
    OVERRIDE it, and the runtime resolves the rest from the depth table, never by branching on depth.
    """

    ratios: dict[str, float] | None = None
    salience: dict[str, float] = Field(default_factory=lambda: dict(_SALIENCE_V1))
    recap_k: int | None = None
    self_tune: dict[str, Any] = Field(default_factory=lambda: {"enabled": False, "bounds_pct": 50})


class Role(_Frozen):
    """A cell role manifest (contracts/role.md). One runtime, differentiated by this."""

    name: str
    depth: Depth = Depth.d1
    provider: ProviderConfig = Field(default_factory=ProviderConfig)
    prompt: str = ""
    capabilities: list[str] = Field(default_factory=list)
    tools: list[str] = Field(default_factory=list)
    memory_policy: str = "scratch"  # "scratch" | "reel"
    frame: FrameCfg = Field(default_factory=FrameCfg)
    oracle_ref: str | None = None
    harm_ceiling: HarmClass = HarmClass.H1

    def frame_ratios(self) -> dict[str, float]:
        """The resolved ratio vector for this role: its override, else the depth default (§3).

        d0 has no assembler and no row; asking for its ratios is a caller bug, so it raises rather
        than inventing a vector — a d0 that reached the assembler took a wrong turn upstream.
        """
        if self.frame.ratios is not None:
            return self.frame.ratios
        if self.depth == Depth.d0:
            raise ValueError("d0 bypasses the assembler (prompt + percept); it has no frame ratios")
        return dict(_RATIO_DEFAULTS[self.depth])

    def frame_salience(self) -> dict[str, float]:
        return dict(self.frame.salience)

    def recap_k(self) -> int:
        if self.frame.recap_k is not None:
            return self.frame.recap_k
        return _RECAP_K_DEFAULTS.get(self.depth, 8)


class Message(_Frozen):
    """The Medium envelope (contracts/wire.md). `seq`/`ts` are set by the Medium, not the cell."""

    seq: int | None = None
    ts: str | None = None
    culture: str = "commons"
    sender: str = "conductor"
    recipient: str | None = None
    type: MessageType = MessageType.chat
    reply_to: int | None = None
    round: int | None = None
    priority: int = 0
    origin: str | None = None
    idem: str | None = None
    body: str | None = None
    artifact: Artifact | None = None


class Receipt(_Frozen):
    """The oracle's score of a submission (contracts/oracle.md). Valid only from the coordinator."""

    submission_seq: int
    outcome: Outcome
    score: float  # 0..1; meaningful only when outcome == passed | gate
    graded_by: str  # a hash/name of the pre-registered falsifier
    evidence: str | None = None


class RosterEntry(_Frozen):
    role: str  # path to a role manifest
    count: int = 1
    diversify: bool = False


class Budget(_Frozen):
    usd_cap: float = 1.0
    per_provider_concurrency: dict[str, int] = Field(default_factory=dict)


class Termination(_Frozen):
    max_rounds: int = 3
    stable_k: int = 2


class RunManifest(_Frozen):
    """A declarative run (contracts/run.md). `hc apply -f run.yaml`."""

    run_id: str
    goal: str
    topology: Topology = Topology.tournament
    roster: list[RosterEntry] = Field(default_factory=list)
    oracle: dict[str, Any] = Field(default_factory=dict)
    budget: Budget = Field(default_factory=Budget)
    termination: Termination = Field(default_factory=Termination)
    seed_diversity: bool = True
    isolate: bool = False
