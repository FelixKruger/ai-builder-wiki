# AI Builder's Field Guide

> A daily-curated wiki of the tools, models, and patterns that AI power-users and builders actually reach for.

**[Browse the live site →](https://felixkruger.github.io/ai-builder-wiki/)** &middot; [RSS](https://felixkruger.github.io/ai-builder-wiki/feed.xml) &middot; [Suggest a tool](https://github.com/felixkruger/ai-builder-wiki/issues/new?title=Suggest:+&labels=suggestion)

---

## What this is

A short, opinionated list of the AI tools, models, and frameworks that working builders actually use in practice — refreshed every weekday by an AI curator.

No marketing copy. No "revolutionary" adjectives. No five entries from the same vendor. Every link is verified live before it lands.

If you ship products on top of LLMs and want a fast scan of what's in use right now, this is for you.

## What makes it different

- **Curated by an AI agent, Mon–Fri.** A scheduled Claude session picks up the oldest entries, re-verifies their URLs, scans high-signal news sources, refines stale framing, and proposes at most **two additions per day**. Quality over volume.
- **Use-case-first taxonomy.** Categories are grouped into five sections — _Build with AI_, _Models & Infrastructure_, _Build Agents_, _Generate Media_, _Measure & Monitor_ — so you can jump straight to what you actually need.
- **Diff-able and forkable.** The whole wiki is one JSON file (`data/entries.json`). Want to fork it for your own niche — clone, edit one file, deploy.
- **Per-card permalinks + OG images.** Every entry has a stable URL fragment and an auto-generated social card. Sharing a single tool to your team is one click.
- **Plain static site.** No JS framework, no tracking, no build server beyond the daily render. Loads in under a second.

## What are you trying to do?

- **I want AI in my editor** → [AI Coding Tools](https://felixkruger.github.io/ai-builder-wiki/#ai-coding)
- **I want to run many coding agents at once** → [Multi-Agent Coding](https://felixkruger.github.io/ai-builder-wiki/#multi-agent-coding)
- **I want my AI-built UIs to stop looking generic** → [AI Design Skills](https://felixkruger.github.io/ai-builder-wiki/#ai-design-skills)
- **I want a working app from a prompt** → [App Builders](https://felixkruger.github.io/ai-builder-wiki/#app-builders)

- **I need the best-available model behind an API** → [Hosted Frontier APIs](https://felixkruger.github.io/ai-builder-wiki/#hosted-apis)
- **I want a model I can run on my own hardware** → [Open-Weight Models](https://felixkruger.github.io/ai-builder-wiki/#open-weights)
- **I need to host an open model at scale** → [Inference & Hosting](https://felixkruger.github.io/ai-builder-wiki/#inference-platforms)

- **I'm building an agent product** → [Agent Frameworks & SDKs](https://felixkruger.github.io/ai-builder-wiki/#agent-frameworks)
- **My agent needs to remember things** → [Agent Memory](https://felixkruger.github.io/ai-builder-wiki/#agent-memory)
- **My agent needs to look things up** → [Retrieval & Search](https://felixkruger.github.io/ai-builder-wiki/#retrieval-search)
- **I need to give my agent tools** → [MCP Ecosystem](https://felixkruger.github.io/ai-builder-wiki/#mcp-tools)

- **I need a voice or audio output** → [Voice & Audio](https://felixkruger.github.io/ai-builder-wiki/#voice-audio)
- **I need to generate or compose video** → [AI Video](https://felixkruger.github.io/ai-builder-wiki/#ai-video)
- **I need 3D assets — games, AR, products** → [AI 3D](https://felixkruger.github.io/ai-builder-wiki/#ai-3d)

- **I need to know if my AI works** → [Evals, Benchmarks & Observability](https://felixkruger.github.io/ai-builder-wiki/#evals)

## Recently added

<!-- RECENTLY_ADDED:START -->

- **[Helicone](https://felixkruger.github.io/ai-builder-wiki/#helicone)** — Helicone provides logging, monitoring, and debugging for large language model applications to help builders understand and optimize their AI usage. _(added 2026-05-19)_

- **[OpenSwarm](https://felixkruger.github.io/ai-builder-wiki/#openswarm)** — OpenSwarm is an open-source multi-agent system that orchestrates specialized AI agents to create diverse deliverables from a single terminal prompt. _(added 2026-05-19)_

- **[Suno v5](https://felixkruger.github.io/ai-builder-wiki/#suno-v5)** — Suno v5 is an AI music generation tool that creates full-length tracks with human-like vocals across various genres. _(added 2026-05-18)_

- **[Baton](https://felixkruger.github.io/ai-builder-wiki/#baton)** — Baton is a desktop application that provides a unified interface for developing and managing multiple AI coding agents and their associated worktrees. _(added 2026-05-18)_

- **[Statewright](https://felixkruger.github.io/ai-builder-wiki/#statewright)** — Statewright utilizes visual state machines to enhance the reliability of AI agents by formally restricting their tool access, iteration limits, and valid transitions within a workflow. _(added 2026-05-18)_

- **[MemPalace](https://felixkruger.github.io/ai-builder-wiki/#mempalace)** — Open-source local AI memory system — stores conversation history as verbatim text with semantic retrieval. _(added 2026-05-11)_

- **[OB1](https://felixkruger.github.io/ai-builder-wiki/#ob1)** — Self-hosted shared memory database — lets multiple AI tools read and write one persistent memory without vendor lock-in. _(added 2026-05-11)_

- **[You.com Search API](https://felixkruger.github.io/ai-builder-wiki/#you-com-api)** — Web search API engineered for AI agents — 300ms p99 latency, real-time indexing across 10M+ news sources. _(added 2026-05-11)_

<!-- RECENTLY_ADDED:END -->

## Sections & categories

### Build with AI

- **[AI Coding Tools](https://felixkruger.github.io/ai-builder-wiki/#ai-coding)** (6) — Agents and IDEs that read, write, and run your code. Where you reach when you want AI inside your editor.
- **[Multi-Agent Coding](https://felixkruger.github.io/ai-builder-wiki/#multi-agent-coding)** (3) — Run, orchestrate, and embed fleets of coding agents — local, cross-device, or inside your product.
- **[AI Design Skills](https://felixkruger.github.io/ai-builder-wiki/#ai-design-skills)** (2) — Reusable skills and prompts that teach coding agents about visual design.
- **[App Builders](https://felixkruger.github.io/ai-builder-wiki/#app-builders)** (3) — Generate a working full-stack app from a prompt. Prototype-to-production in minutes.

### Models & Infrastructure

- **[Hosted Frontier APIs](https://felixkruger.github.io/ai-builder-wiki/#hosted-apis)** (3) — The closed-weight frontier models you call from your stack — Claude, GPT, Gemini.
- **[Open-Weight Models](https://felixkruger.github.io/ai-builder-wiki/#open-weights)** (3) — Downloadable model families. Host yourself or run on any inference platform.
- **[Inference & Hosting](https://felixkruger.github.io/ai-builder-wiki/#inference-platforms)** (4) — Where to run open-weight models in production — managed inference, fine-tuning, custom silicon.

### Build Agents

- **[Agent Frameworks & SDKs](https://felixkruger.github.io/ai-builder-wiki/#agent-frameworks)** (3) — The glue for building autonomous, tool-using agents.
- **[Agent Memory](https://felixkruger.github.io/ai-builder-wiki/#agent-memory)** (4) — Persistent memory layers — what your agent knows across sessions, users, and turns.
- **[Retrieval & Search](https://felixkruger.github.io/ai-builder-wiki/#retrieval-search)** (3) — Vector stores, full-text search, and web search APIs. Stateless retrieval — different from memory.
- **[MCP Ecosystem](https://felixkruger.github.io/ai-builder-wiki/#mcp-tools)** (2) — Servers, clients, and registries for the Model Context Protocol — the standard for connecting agents to tools.

### Generate Media

- **[Voice & Audio](https://felixkruger.github.io/ai-builder-wiki/#voice-audio)** (2) — Speech synthesis, voice cloning, realtime agents, and music generation.
- **[AI Video](https://felixkruger.github.io/ai-builder-wiki/#ai-video)** (3) — Text-to-video models and programmatic video frameworks.
- **[AI 3D](https://felixkruger.github.io/ai-builder-wiki/#ai-3d)** (2) — Text- or image-to-3D generators and 3D asset pipelines.

### Measure & Monitor

- **[Evals, Benchmarks & Observability](https://felixkruger.github.io/ai-builder-wiki/#evals)** (4) — Measure what your agents and models actually do. Public leaderboards and production observability.

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

For the daily curator, see [`docs/daily-curator-package.md`](docs/daily-curator-package.md).

## How it's built

| Piece                           | What it does                                                                |
| ------------------------------- | --------------------------------------------------------------------------- |
| `data/entries.json`             | Source of truth — every tool entry and category lives here                  |
| `scripts/render.py`             | Renders `index.html`, `feed.xml`, OG cards, and this README's auto-sections |
| `templates/`                    | Jinja2 templates for the site, RSS, OG cards, README                        |
| `skills/wiki-curator/SKILL.md`  | The daily curator's playbook                                                |
| `docs/daily-curator-package.md` | Mon–Fri prompt for the scheduled Claude cowork session                      |
| `.github/workflows/deploy.yml`  | Builds & ships to GitHub Pages on every push to `main`                      |

## License

Content under [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/). Code under MIT.
