# CONTRACT: role — the cell role manifest (the depth dial)

**Status:** v0.1 DRAFT. One uniform cell runtime is differentiated by a **role manifest**. Same image → a
hello-world reflex or a full brain, by manifest alone (constitution A1, §4). RFC-2119.

## Fields
```yaml
name: refiner                 # role label
depth: d1                     # d0 reflex | d1 worker | d2 resident | d3 brain
provider:                     # the swappable cognition (see contracts/oracle.md is separate)
  provider: deepseek          # deepseek|cerebras|glm|kimi|qwen|grok|openai|anthropic|gemini|<custom>
  model: deepseek-chat
  base_url: null              # null → registry default for the provider
  key_ref: DEEPSEEK_API_KEY   # env var (or substrate secret) holding the key
  params: { temperature: 0.7, max_tokens: 4096 }
prompt: |                     # the role's system prompt (positive specification; no ban-lists)
  You are a refiner. Read the other candidates and produce one that beats the field.
capabilities: [code, python, tests]   # advertised to the router (MoE placement)
tools: []                     # MCP tool refs / rentable organ adapters (connectors, browser, computer, inbox)
memory_policy: scratch        # scratch (d0/d1) | reel (d2/d3)
oracle_ref: null              # optional: a role-local oracle (usually the run supplies it)
harm_ceiling: H1              # H0 log · H1 auto · H2 delayed · H3 human-always
```

## Depth dial (MUST)
| depth | the cell is | nucleus tier |
|---|---|---|
| `d0` | a bare provider call, no memory | none/scratch |
| `d1` | one perceive→act→checkpoint loop | cursor+scratch |
| `d2` | a long-lived resident specialist | REEL rings |
| `d3` | a self-closing brain (KEEL-class, over protocol) | full brain |

Adding depth changes `depth` + `memory_policy`; it MUST NOT fork the runtime into a new cell type.

## Provider is config, not code (MUST — HC-6)
Swapping `provider.*` changes the cell's model with **no code change**. A Culture MAY be heterogeneous (a
`cerebras` coordinator directing `deepseek` workers). A small local-model pod is the island floor: no cell
may hard-require a cloud tier to close its loop.
