# AI Builder's Field Guide

> A daily-curated wiki of the tools, models, and patterns that AI power-users and builders actually reach for.

**[Browse the live site →](https://felixkruger.github.io/ai-builder-wiki/)** &middot; [RSS](https://felixkruger.github.io/ai-builder-wiki/feed.xml) &middot; [Suggest a tool](https://github.com/felixkruger/ai-builder-wiki/issues/new?title=Suggest:+&labels=suggestion)

---

## What this is

A short, opinionated list of the AI tools, models, and frameworks that working builders actually use in practice — refreshed every day by an AI curator.

No marketing copy. No "revolutionary" adjectives. No five entries from the same vendor. Every link is verified live before it lands.

If you ship products on top of LLMs and want a fast scan of what's in use right now, this is for you.

## What makes it different

- **Curated by an AI agent, daily.** A scheduled Claude session picks up the oldest entries, re-verifies their URLs, scans high-signal news sources, and proposes at most **two additions per day**. Quality over volume.
- **Diff-able and forkable.** The whole wiki is one JSON file (`data/entries.json`). Want to fork it for your own niche (audio AI? agents for sales? robotics?) — clone, edit one file, deploy.
- **Per-card permalinks + OG images.** Every entry has a stable URL fragment and an auto-generated social card. Sharing a single tool to your team is one click.
- **Plain static site.** No JS framework, no tracking, no build server beyond the daily render. Loads in under a second.

## Recently added

<!-- RECENTLY_ADDED:START -->

- **[Claude Code](https://felixkruger.github.io/ai-builder-wiki/#claude-code)** — Anthropic's official terminal-native coding agent — reads your repo, edits files, runs commands, talks to MCP servers. _(added 2026-04-27)_

- **[Cursor](https://felixkruger.github.io/ai-builder-wiki/#cursor)** — AI-first VS Code fork with Composer, Tab autocomplete, and a strong agent loop. _(added 2026-04-27)_

- **[Windsurf](https://felixkruger.github.io/ai-builder-wiki/#windsurf)** — Codeium's agentic IDE with Cascade — strong long-running task execution, now part of OpenAI. _(added 2026-04-27)_

- **[Aider](https://felixkruger.github.io/ai-builder-wiki/#aider)** — Open-source CLI pair-programmer — git-native, model-agnostic, and the benchmark for many leaderboards. _(added 2026-04-27)_

- **[Cline](https://felixkruger.github.io/ai-builder-wiki/#cline)** — Open-source autonomous coding agent for VS Code — plan/act modes, MCP support, BYO model. _(added 2026-04-27)_

- **[Claude API (Anthropic)](https://felixkruger.github.io/ai-builder-wiki/#claude-api)** — Anthropic's API — Claude Opus 4.7, Sonnet 4.6, Haiku 4.5. Native tool use, prompt caching, extended thinking, files, citations. _(added 2026-04-27)_

- **[OpenAI API](https://felixkruger.github.io/ai-builder-wiki/#openai-api)** — GPT-5 family, Realtime API, structured outputs, Responses API. _(added 2026-04-27)_

- **[Gemini API (Google)](https://felixkruger.github.io/ai-builder-wiki/#gemini-api)** — Gemini 2.5 Pro / Flash with 2M-token context, native multimodal, and grounding-with-Search. _(added 2026-04-27)_

<!-- RECENTLY_ADDED:END -->

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

[Open an issue](https://github.com/felixkruger/ai-builder-wiki/issues/new?title=Suggest:+&labels=suggestion) with the URL and one sentence on why it belongs. The curator picks up suggestions on the next daily run.

For faster turnaround, [open a PR](https://github.com/felixkruger/ai-builder-wiki/compare) editing `data/entries.json` directly. See [`CLAUDE.md`](CLAUDE.md) for the entry schema.

## Fork it

The whole site is a static-site generator over one JSON file. To run your own:

```bash
git clone https://github.com/felixkruger/ai-builder-wiki.git my-wiki
cd my-wiki
pip install -r requirements.txt
# Edit data/entries.json — keep the schema in CLAUDE.md
python scripts/render.py
# Enable GitHub Pages: Settings → Pages → Source: GitHub Actions
# Push to main — the deploy workflow ships it
```

For the daily curator, see [`docs/cowork-setup.md`](docs/cowork-setup.md).

## How it's built

| Piece                          | What it does                                                                           |
| ------------------------------ | -------------------------------------------------------------------------------------- |
| `data/entries.json`            | Source of truth — every tool entry lives here                                          |
| `scripts/render.py`            | Renders `index.html`, `feed.xml`, OG cards, and this README's "Recently added" section |
| `templates/`                   | Jinja2 templates for the site, RSS, OG cards, README                                   |
| `skills/wiki-curator/SKILL.md` | The daily curator's playbook                                                           |
| `docs/cowork-setup.md`         | How to schedule the curator as a Claude cowork agent                                   |
| `.github/workflows/deploy.yml` | Builds & ships to GitHub Pages on every push to `main`                                 |

## License

Content under [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/). Code under MIT.
