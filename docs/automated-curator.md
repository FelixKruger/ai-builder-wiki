# Automated Daily Curator — Setup

> **Goal:** the wiki updates itself every weekday at 06:00 UTC, with zero machines of yours running.
>
> **Total setup time: ~1 minute.**

This replaces the cowork agent and the Beelink cron script with a free GitHub Actions cron job that calls **Gemini 2.5 Flash** (Google's free-tier model) once per weekday. GitHub runs the job on their hardware; you don't need anything turned on.

---

## Setup (do this once)

### Step 1 — Get a free Gemini API key

1. Open https://aistudio.google.com/apikey
2. Sign in with any Google account.
3. Click **"Create API key"** → pick or create a project → copy the key.

Free tier: ~1500 requests/day for Gemini 2.5 Flash. The curator uses **1 request per weekday**, so you are roughly 300× under the limit. No credit card required.

### Step 2 — Add the key as a repo secret

1. Open https://github.com/FelixKruger/ai-builder-wiki/settings/secrets/actions
2. Click **"New repository secret"**
3. Name: `GEMINI_API_KEY`
4. Value: paste the key from step 1
5. Click **"Add secret"**

### Step 3 — Verify it works (optional but recommended)

1. Open https://github.com/FelixKruger/ai-builder-wiki/actions/workflows/curator.yml
2. Click **"Run workflow"** → **"Run workflow"** (uses the `main` branch).
3. Wait ~1 minute. The run should complete green.
4. Check https://github.com/FelixKruger/ai-builder-wiki/commits/main — if the curator found 1-2 candidates or refreshed any URLs, you'll see a `curator: ...` commit.

Done. From tomorrow morning the curator will run automatically at 06:00 UTC, Monday through Friday.

---

## What the workflow does each run

1. **Refreshes the 3 oldest entries** by `last_verified` — HTTP-checks each URL, captures redirects, archives any that 404.
2. **Asks Gemini** for 1–2 new high-quality candidates similar in spirit to what's already in the wiki.
3. **Verifies every candidate URL** returns HTTP 200 (rejects hallucinated URLs Gemini might invent).
4. **Filters by quality rules** — banned hype words, dedup against existing entries, must fit an existing category.
5. **Re-renders** `index.html`, `feed.xml`, OG cards, and the README's "Recently added" section.
6. **Commits and pushes** as `github-actions[bot]`.
7. **Triggers the Pages deploy** so the live site updates within 30–60 seconds.

If nothing passes the quality bar on a given day, the run still refreshes existing entries — so the live site always has a fresh `Last curated:` date.

---

## Cost

- **GitHub Actions:** free for public repos (this is one). Unlimited minutes.
- **Gemini 2.5 Flash:** free tier, ~5 requests/week. Free indefinitely.
- **Total: $0/month.**

---

## Customizing

### Change the schedule

Edit `.github/workflows/curator.yml`, line `cron: "0 6 * * 1-5"`.

Format is UTC. Examples:

- `0 14 * * 1-5` — 14:00 UTC (10:00 EDT, 16:00 CEST) Mon–Fri
- `0 6 * * *` — every day including weekends
- `0 6 * * 1,3,5` — Mon, Wed, Fri only

### Use a different LLM

The curator only depends on Gemini for one thing: suggesting candidate tools. Swap providers by editing `scripts/curator.py::ask_gemini()`. Alternatives:

| Provider                                                                                        | Free?                                  | Setup                |
| ----------------------------------------------------------------------------------------------- | -------------------------------------- | -------------------- |
| **Gemini 2.5 Flash** (current)                                                                  | Yes, ~1500/day                         | `GEMINI_API_KEY`     |
| **OpenRouter** with `:free` models (e.g., `deepseek/deepseek-r1:free`, `qwen/qwen3-coder:free`) | Yes, lower rate limit but no daily cap | `OPENROUTER_API_KEY` |
| **Anthropic Claude API**                                                                        | Paid (~$0.01/run)                      | `ANTHROPIC_API_KEY`  |
| **Hugging Face Inference**                                                                      | Yes, rate-limited                      | `HF_TOKEN`           |

The script structure is identical for any of these — just swap the SDK call.

### Change what the curator looks for

Edit the `prompt` string in `scripts/curator.py::ask_gemini()`. You can bias toward:

- A specific category (`Focus today on retrieval & search tools…`)
- A specific source bias (`Look for tools recently mentioned by working AI builders on Hacker News…`)
- A specific tone (`Prefer tools used by Y Combinator AI startups…`)

### Disable temporarily

Comment out the `schedule` block in `.github/workflows/curator.yml`. The manual "Run workflow" button still works.

### Stop forever

Delete `.github/workflows/curator.yml`.

---

## Troubleshooting

**The scheduled run didn't fire.**
GitHub Actions cron is best-effort and can lag by up to ~1 hour during peak load. If it hasn't fired by 07:30 UTC, click "Run workflow" manually once — the next scheduled run usually catches up.

**Run failed with `GEMINI_API_KEY env var not set`.**
The secret name in repo settings must be exactly `GEMINI_API_KEY` (uppercase, underscore). Check at https://github.com/FelixKruger/ai-builder-wiki/settings/secrets/actions.

**Run succeeded but the live site didn't update.**
The curator triggers a Pages deploy as the last step. If the trigger silently failed, manually run the "Deploy to GitHub Pages" workflow from the Actions tab. Worst case: edit any file in `data/` and push — that retriggers a deploy.

**Gemini returned hallucinated URLs.**
The script rejects any candidate whose URL doesn't return HTTP 200. Hallucinations are filtered out before reaching `entries.json`. Check the workflow run log for `REJECT:` lines.

**Quality is dropping (too many marginal entries).**
Lower the temperature in `scripts/curator.py` (currently `0.7`), or tighten the banned-words list, or add explicit "avoid: …" rules to the prompt.
