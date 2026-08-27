# CodeLens AI — Task & Goal Breakdown

A phased roadmap: AST parsing → code graph → RAG → agent → MCP server. Each phase has a clear goal, concrete tasks, and a "done when" checkpoint so scope doesn't creep.

---

## Phase 0 — Setup (Day 1)

**Goal:** Empty repo, working environment, one test repo to analyze.

- [ ] Create project repo (`codelens-ai`)
- [ ] Set up Python env (`uv` or `venv`), `requirements.txt`
- [ ] Pick a small test target repo (a simple Flask/FastAPI app, 5-10 files) to develop against
- [ ] Decide on output format for intermediate data: JSON files on disk (keep it simple, no DB yet)

**Done when:** You can run `python main.py --repo ./test_repo` and it does nothing but print "analyzing...".

---

## Phase 1 — AST Parsing (Week 1)

**Goal:** Turn Python source files into structured JSON: classes, functions, imports, calls.

**Tasks:**
- [ ] Walk repo directory, collect all `.py` files (skip venv/node_modules/.git)
- [ ] For each file, `ast.parse()` the source
- [ ] Extract via `ast.NodeVisitor` or `ast.walk()`:
  - Function defs (name, args, line number, docstring)
  - Class defs (name, base classes, methods)
  - Import statements (module, alias)
  - Function call expressions inside each function body
- [ ] Handle edge cases: nested functions, decorators, `self.method()` calls, imported-module calls
- [ ] Serialize everything to a single JSON: `{file: {classes: [...], functions: [...], imports: [...]}}`

**Done when:** Running the tool on your test repo produces a JSON file that correctly lists every function/class/import, verified by manually checking 2-3 files.

**Milestone deliverable:** `analyzer.py` + sample `output.json`

---

## Phase 2 — Code Graph (Week 2)

**Goal:** Convert the flat JSON into a queryable graph of relationships.

**Tasks:**
- [ ] Install NetworkX
- [ ] Create nodes for: File, Class, Function
- [ ] Create edges for: `CONTAINS` (file→function), `CALLS` (function→function), `IMPORTS` (file→file), `INHERITS` (class→class)
- [ ] Resolve call names to actual function nodes (this is the hard part — matching `verify_password()` call text to the actual function definition, including across files)
- [ ] Write basic graph queries:
  - "What does function X call?"
  - "What calls function X?" (reverse edges)
  - "What's the full call chain from X?" (graph traversal / BFS)
- [ ] Export/visualize graph (e.g., `networkx.draw` or export to Graphviz) just to sanity-check it looks right

**Done when:** You can ask "what calls `login()`?" and "what does `login()` call?" and get correct answers from the graph, not just the JSON.

**Milestone deliverable:** `graph_builder.py`, a working `CodeGraph` class with query methods

---

## Phase 3 — Change Impact Analysis (early, since it's your best demo)

**Goal:** Given a function/class, find everything downstream that could break.

**Tasks:**
- [ ] Reverse-traverse the `CALLS` graph from a target node
- [ ] Collect all transitively-dependent functions/files
- [ ] Rank by "distance" (direct callers = high impact, indirect = lower)
- [ ] Match affected files to likely test files (naive: `foo.py` → `test_foo.py`)
- [ ] Pretty-print output: `HIGH IMPACT / 12 functions depend on X / Affected files: ... / Tests to run: ...`

**Done when:** You can point it at `User` class in your test repo and get a correct, readable impact report.

**Why do this before RAG:** it's pure graph logic, no LLM needed, and it's your strongest demo — get it working early so you always have something impressive to show, even if later phases stall.

---

## Phase 4 — Embeddings & Vector Search (Week 3)

**Goal:** Add semantic search on top of the structural graph.

**Tasks:**
- [ ] Chunk code by function/method (use the AST boundaries from Phase 1, not naive line-splitting)
- [ ] Generate embeddings (OpenAI/Anthropic/local model — pick one, don't overthink it)
- [ ] Store in a simple vector store (start with `chromadb` or even a numpy array + cosine similarity — no need for Pinecone/Weaviate yet)
- [ ] Write a `semantic_search(query)` function returning top-k relevant code chunks
- [ ] Combine with graph: for each semantic hit, also pull its graph neighbors (this is your "Graph RAG")

**Done when:** Asking "where is password verification done?" returns the right function even if the query words don't literally match the code.

---

## Phase 5 — The Agent (Week 4)

**Goal:** Wire graph + vector search + reasoning into a tool-using agent.

**Tasks:**
- [ ] Define tools as plain functions: `search_code(query)`, `get_callers(fn)`, `get_callees(fn)`, `impact_analysis(target)`
- [ ] Use Claude/OpenAI tool-calling (function calling) — agent decides which tool(s) to call based on the question
- [ ] Build the loop: question → tool call(s) → tool result → reasoning → answer (multi-step if needed)
- [ ] Test against real questions: "How does authentication work?", "Trace the checkout flow", "What breaks if I change User?"

**Done when:** The agent correctly answers multi-step questions by chaining 2+ tool calls, not just one lookup.

**Note:** No MCP needed here — plain function-calling is simpler and sufficient for internal tool orchestration.

---

## Phase 6 — MCP Server (Week 5) — *your differentiator*

**Goal:** Expose CodeLens as an MCP server so it plugs into Claude Code, Claude Desktop, Cursor, etc. directly — no custom UI required.

**Tasks:**
- [ ] Wrap your 4 core tools (`search_code`, `get_callers`, `get_callees`, `impact_analysis`) as MCP tool definitions with proper JSON schemas
- [ ] Stand up an MCP server (stdio or SSE transport)
- [ ] Test locally by connecting Claude Desktop/Claude Code to it, pointed at your test repo
- [ ] Write a clean README showing: "connect this to Claude Code, ask it about your repo"

**Done when:** You can open Claude Code, have your MCP server connected, and ask it real questions about a repo it's never seen raw — answers come from your graph, not just raw file reads.

**This is your strongest resume/portfolio pitch:** *"An MCP server giving any AI coding assistant graph-grounded understanding of a codebase — not just semantic search over text."*

---

## Phase 7 (Stretch) — Web App

**Goal:** Only build this if Phases 1-6 are solid and you want a visual demo beyond CLI/MCP.

- [ ] FastAPI backend wrapping the same agent/tools
- [ ] React frontend: repo connect (GitHub OAuth), dashboard, chat interface, graph visualization
- [ ] Skip unless you specifically need a polished visual demo for non-technical viewers (e.g., a hiring manager who won't set up Claude Code)

---

## Phase 8 (Stretch) — Code Modification / PR Creation

- [ ] Agent proposes a diff
- [ ] GitHub API (or GitHub MCP server) to create a branch + PR
- [ ] Only attempt after everything else is reliable — this is the highest-risk, most demo-fragile feature

---

## Suggested Priority Order for a Resume Deadline

If you have limited time, ship in this order and stop wherever you run out of runway — each stopping point is still a complete, demoable project:

1. **Phases 1–3** (AST → graph → impact analysis) — fully deterministic, no LLM cost, always demoable
2. **Phase 6** (MCP server) — even with just the Phase 1-3 tools exposed, this alone is a strong, novel pitch
3. **Phase 4–5** (RAG + agent) — adds the "AI" story on top
4. Phases 7–8 only if time remains

## What to avoid

- Don't install Neo4j, Redis, LangGraph, or a vector DB cluster on day 1 — NetworkX + JSON + numpy gets you to Phase 4 fine
- Don't build the React UI before the backend logic is solid
- Don't wrap your *own* agent's internal tools in MCP — only wrap them for *external* consumption (Phase 6)
