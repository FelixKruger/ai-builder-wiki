# AI Builder's Field Guide

A daily-curated wiki of the tools, models, and patterns that AI power-users and builders actually reach for.

**Live site:** https://felixkruger.github.io/ai-builder-wiki/
**RSS:** https://felixkruger.github.io/ai-builder-wiki/feed.xml

A curated, daily-updated wiki of the tools, models, and patterns AI power-users and builders actually reach for. Every entry is verified live before it lands.

## Recently added

<!-- RECENTLY_ADDED:START -->

- **[Claude Code](https://felixkruger.github.io/ai-builder-wiki/#claude-code)** — Anthropic's official terminal-native coding agent — reads your repo, edits files, runs commands, talks to MCP servers. *(added 2026-04-27)*

- **[Cursor](https://felixkruger.github.io/ai-builder-wiki/#cursor)** — AI-first VS Code fork with Composer, Tab autocomplete, and a strong agent loop. *(added 2026-04-27)*

- **[Windsurf](https://felixkruger.github.io/ai-builder-wiki/#windsurf)** — Codeium's agentic IDE with Cascade — strong long-running task execution, now part of OpenAI. *(added 2026-04-27)*

- **[Aider](https://felixkruger.github.io/ai-builder-wiki/#aider)** — Open-source CLI pair-programmer — git-native, model-agnostic, and the benchmark for many leaderboards. *(added 2026-04-27)*

- **[Cline](https://felixkruger.github.io/ai-builder-wiki/#cline)** — Open-source autonomous coding agent for VS Code — plan/act modes, MCP support, BYO model. *(added 2026-04-27)*

- **[Claude API (Anthropic)](https://felixkruger.github.io/ai-builder-wiki/#claude-api)** — Anthropic's API — Claude Opus 4.7, Sonnet 4.6, Haiku 4.5. Native tool use, prompt caching, extended thinking, files, citations. *(added 2026-04-27)*

- **[OpenAI API](https://felixkruger.github.io/ai-builder-wiki/#openai-api)** — GPT-5 family, Realtime API, structured outputs, Responses API. *(added 2026-04-27)*

- **[Gemini API (Google)](https://felixkruger.github.io/ai-builder-wiki/#gemini-api)** — Gemini 2.5 Pro / Flash with 2M-token context, native multimodal, and grounding-with-Search. *(added 2026-04-27)*

<!-- RECENTLY_ADDED:END -->

## How it works

- `data/entries.json` is the source of truth.
- `scripts/render.py` regenerates `index.html`, `feed.xml`, and this README's "Recently added" section.
- A curator agent (see `skills/wiki-curator/SKILL.md`) runs daily on a Beelink mini-PC, finds new tools, verifies them, and commits.
- GitHub Pages auto-deploys on every push to `main`.

## Categories

- **[Coding Agents & IDEs](https://felixkruger.github.io/ai-builder-wiki/#coding-agents)** (5) — Agents that read, write, and run your code.
- **[Foundation Models & APIs](https://felixkruger.github.io/ai-builder-wiki/#foundation-models)** (4) — The frontier models you call from your stack.
- **[Agent Frameworks & SDKs](https://felixkruger.github.io/ai-builder-wiki/#agent-frameworks)** (3) — Glue for building autonomous, tool-using agents.
- **[Evals & Observability](https://felixkruger.github.io/ai-builder-wiki/#eval-observability)** (3) — Measure what your agents actually do in production.
- **[RAG, Vector Search & Memory](https://felixkruger.github.io/ai-builder-wiki/#rag-memory)** (2) — Retrieval, embeddings, and long-term context.
- **[App & UI Builders](https://felixkruger.github.io/ai-builder-wiki/#ui-builders)** (3) — Generate working apps from a prompt.
- **[Voice & Multimodal](https://felixkruger.github.io/ai-builder-wiki/#voice-multimodal)** (2) — Speech, vision, and real-time multimodal stacks.
- **[MCP Ecosystem](https://felixkruger.github.io/ai-builder-wiki/#mcp-tools)** (2) — Servers, clients, and registries for the Model Context Protocol.


## Suggest a tool

[Open an issue](https://github.com/felixkruger/ai-builder-wiki/issues/new?title=Suggest:+&labels=suggestion) with the URL and one sentence on why it belongs.

## License

Content under CC-BY-4.0. Code under MIT.
