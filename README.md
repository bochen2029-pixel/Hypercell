# hypercell

It started with a small, specific annoyance. I was running several sessions of a coding assistant at once, each working a different corner of the same problem, and none of them could talk to the others. When one session worked something out that another needed, I was the wire between them. I copied a message out of one window and pasted it into the next, then carried the reply back, a human relay ferrying notes between machines that were perfectly able to read them on their own. The work was real. The bottleneck was me.

hypercell is what that annoyance became once I followed it all the way down. At its simplest it is a way to spawn a fleet of AI agents, let them coordinate among themselves, and command the whole thing from one seat. Each agent is a cell. A cell can be as shallow as a single call to a language model or as deep as a system that keeps its own memory and reasons in a loop over time. Cells remember what they were doing, so when the machine reboots they wake where they left off instead of starting over. They arrive at answers by being measured against something outside themselves, rather than by agreeing with one another. And the model behind them is swappable, so I can point a cell at DeepSeek when cost matters, at Cerebras when speed matters, or at anything else I choose. The whole system runs in containers, which means it runs the same on my own computer, on a rented server, or in a cloud cluster, and I can reach it from a laptop or a phone.

The name is not decoration. A hypercell begins undifferentiated, the way a stem cell does, and becomes what the work asks it to be. Point it inward and it deepens, growing memory, judgment, and a loop it runs on itself until a single cell is a small reasoning system in its own right. Point it outward and it broadens, specializing into a researcher, a reviewer, a coordinator, or a shared plane that a hundred other cells route their work through. Nothing about a cell is fixed at birth. The same seed scales down to a one-line wrapper around a model and up to something I have been building separately and calling the brain, and the fabric holds every stage in between without changing shape. This is the property I care about most, because it means I never outgrow the design. I only differentiate it further.

The first thing it buys is sovereignty. hypercell belongs to me in a way that a subscription to someone else's assistant never can. It leans on no single vendor, no single model, and no proprietary tool to function. If a provider changes its price or its terms, I change a line of configuration. If I want to move the entire fleet from the desk in front of me to a data center on the other side of the world, I move it. The intelligence is rented and interchangeable. The structure that gives it memory, continuity, and coordination is owned.

That ownership is the point, because everyone else is climbing in the other direction. The companies that sell the models are working hard to be more than sellers of tokens, wrapping assistants, design tools, and hosted surfaces around their own inference so the value accrues to them. Around them a whole supply of agent infrastructure has grown up almost overnight: services that hand an agent a set of pre-wired connectors and absorb the messy authentication, services that give it a cloud browser to see the web, a sandboxed computer to work on, even an email address of its own so it can sign up for things and receive the replies. hypercell is my climb up that same ladder, except the top of it belongs to me. It is not a wall against that world either. When a piece of it is genuinely a commodity, a cell can rent it the way it rents a model, borrowing a connector layer or a browser or a machine and keeping the loop, the memory, and the coordination for itself. The picture I keep coming back to is a phone in my hand talking to a model running on my own hardware that still reaches out through a turnkey layer to do the boring plumbing. It was never going to be all mine or all theirs. The whole design is about choosing that line myself, part by part, and moving it whenever I want to.

Take the same fabric into an organization and it stops being a personal tool and becomes a claim about how work actually gets done. Strip any company to its core and you find a single thread of irreducible steps running from input to output. At each important point on that thread sits a person doing the one thing software historically could not: taking everything the tools already computed and compressed, holding it in mind, and doing the cognitive work of making sense of it. That connective judgment is the real substance of the business, and most other roles exist to support those points, and then to support the support. If a swarm of cells can stand in for that judgment, one node at a time, the compression does not stop at a single job. It cascades outward through everything that was built to hold that job up. This is the difference between using AI to help everyone write faster email and using it to reconsider what the organization needs to be in the first place.

The far edge of this is the most speculative part and, to me, the most interesting. I do not want to hand-tune every connection and every handoff forever. I would rather build the ground a swarm can stand on and let it work out the rest. Give it a goal, give it an honest way to tell whether it is getting closer, seed it with enough variety that it does not collapse into one opinion, and let the coordination emerge the way it does in an ant colony, where no single ant holds the plan and yet the structure gets built. Cells that have deepened all the way into full reasoning systems, each closing its own loop and checking its own work, are the ones I would trust to run without a human standing over them. When that begins to happen, the system starts closing its own loop, using intelligence to supply the parts of intelligence it still lacks. That is the wager at the end of the road, the one the terms AGI and ASI are pointing at: use AI to solve AI, and find out how far a fabric of cooperating cells can carry itself.

So here is the arc, stated plainly. It began as a way to stop being the copy-and-paste messenger between my own sessions. It turned into a sovereign personal AI, then into a method for compressing the cognitive labor of an entire organization, and finally into a serious attempt at the self-improving, self-organizing intelligence that people have in mind when they talk about AGI. The same small idea at every scale, only larger each time. hypercell is the name I am giving the whole of it for now, and if something one day grows large enough to contain even this, it will have started here, as a single cell that could become anything.

---

## Running it

hypercell runs today on Python 3.12. The fastest way in is to talk to it:

```
git clone https://github.com/bochen2029-pixel/Hypercell
cd Hypercell
uv venv && uv pip install -e ".[dev]"
cp .env.example .env          # then add one provider key, e.g. DEEPSEEK_API_KEY

hc talk                        # then just say: "spin up 6 agents to research X"
```

`hc talk` is the natural-language commander. You describe what you want, a router model
turns it into a fleet action, runs it, and reports back. To watch the swarm coordinate
live, open the Medium viewer (a read-only dashboard over the shared coordination log):

```
python tools/medium_viewer.py       # http://127.0.0.1:8799
```

Or drive it directly, no natural language:

```
hc run tournament --provider deepseek --n 6 --goal "..." --oracle "python oracles/ipv4_check.py"
hc drive --provider deepseek --goal "..." --oracle "..." --usd-cap 0.05
hc ask   --provider deepseek "..."          # a single cell
hc resume --claim run/role/0                # wake a crashed cell from its nucleus
```

Swap the model by config, never by code: `--provider deepseek|cerebras|glm|kimi|qwen|grok|openai`,
with keys in `.env`. It is built to run the same in a container or on k3s (`images/Dockerfile`,
`deploy/`).

## What is here

- **`HYPERCELL_V5_ARCHITECTURE.md` is the current constitution** (v5.0 — draft for
  ratification): the thirteen axioms including the Fold Law, the eight-noun / seven-verb
  grammar with the world-touching `act` verb, the trust / act / economics planes, two-phase
  grading, the staged identity firewall, the build ladder from the live P0–P2 upward, and the
  full organ-by-organ falsifier index. It supersedes v1 (below) and the interim v2, folding
  the v3 mechanism wave into one verified document.
- `HYPERCELL_V1_ARCHITECTURE.md` is the **original constitution**, preserved verbatim — the
  ratified law the live P0–P2 code was built against. v5 keeps every v1 law it found right and
  cites the live code by `file:line` where each mechanism goes next.
- `HYPERCELL_BUILD.md` is the v1 build runbook (P0 through P5, each rung falsifier-gated);
  v5 §14 carries the re-cut ladder.
- `contracts/` holds the frozen v1 wire, nucleus, role, run, and oracle contracts (v5
  specifies nine — the four new plane contracts land as the ladder is built).
- `src/hypercell/` is the fabric: cells, the swappable cognition seam, the Medium, the
  conductor (tournament, drive, router, schedule, fanout), and the surfaces (CLI, HTTP
  API, MCP, and `hc talk`).
- `tools/medium_viewer.py` is a live dashboard over the Medium.

## Status

Early and honest — the **code is the live v1 stem; the design is v5**. P0 (a commandable,
provider-swappable, resumable cell), P1 (the tournament Culture that converges against an
external oracle), and P2 (the self-driving loop with a cost governor) are built and
live-tested (`bench/.hypercellstate/`); the conductor has run on-cluster on k3s
(crash-resume is artifacted; on-cluster PVC survival is witnessed and pending a committed
artifact). This is a working stem, not a finished product — v5 is the constitution it grows
into, and its §14–§15 are the rung-by-rung plan and its falsifiers. `TODO.md` lists what is
parked.

## License

MIT. See [LICENSE](LICENSE).
