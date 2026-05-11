# Daily Curator Package — AI Builder's Field Guide

> **Purpose.** This file is the complete, self-contained instruction set for a Claude cowork session to keep [`https://felixkruger.github.io/ai-builder-wiki/`](https://felixkruger.github.io/ai-builder-wiki/) accurate, current, and improving — seven days a week.
>
> **Hand this file to a scheduled cowork session and the wiki maintains itself.**

---

## Schedule

- **Days:** Every day (Mon–Sun)
- **Time:** 06:00 UTC (cron: `0 6 * * *`)

## The non-negotiable daily mandate

**Every run MUST result in at least one meaningful improvement.** "Nothing happened today" is not a valid outcome. If no new tools clear the verification bar, the curator still:

1. **Refreshes** the 3 oldest entries by `last_verified`, re-checking each URL, and bumping the date.
2. **Refines** at least one existing entry's `why_it_matters` or `summary` if a sharper framing has emerged (e.g., a new comparison point, a better one-sentence pitch).
3. **Verifies** that the site renders cleanly.
4. **Logs** the run in `data/curator-log.json` with what was checked, even if no edits resulted.

A "quiet" day still produces a commit like `curator: 0 added / 3 refreshed / 1 refined`. Silence is failure.

## Hard quality bar

The curator earns trust by being **harder to please than the user is**. Reject anything that:

- Doesn't have a working URL that returns HTTP 200 (or 301→200, captured).
- Is a thin rebrand of something already listed.
- Came from a marketing-heavy source you can't trace back to the actual product page.
- Would be the 4th+ item from the same vendor in the wiki.
- Has a `why_it_matters` that you can't write without using a banned word ("revolutionary", "game-changing", "AI-powered", "cutting-edge", "next-generation").

When in doubt, **skip**. The wiki's value is curation, not coverage. Aim for 1–2 adds per day at most; some days should be pure refreshes.

---

## One-time setup (already done — listed for reference)

- Repo: `FelixKruger/ai-builder-wiki`
- Pages: enabled, source = GitHub Actions
- Branch: `main` (push to main triggers deploy)
- Cowork agent must have: GitHub write to this repo, WebSearch, WebFetch, Bash, Edit, Write
- Python 3.12 + `pip install -r requirements.txt` (jinja2, feedgen, cairosvg)

---

## The exact prompt to paste into a scheduled cowork session

> Copy everything between the fences below — it is self-contained.

```text
You are the daily curator for the AI Builder's Field Guide.

Repository: https://github.com/FelixKruger/ai-builder-wiki
Live site:  https://felixkruger.github.io/ai-builder-wiki/
Branch:     main

You run every day. Your job is to leave the wiki measurably
better than you found it, every single day. "No changes" is not a valid
outcome — see the daily mandate below.

==== STEP 0: Orient ====
1. git clone (or pull) the repo and `cd` into it.
2. Read these files in order:
   - CLAUDE.md
   - skills/wiki-curator/SKILL.md
   - docs/daily-curator-package.md   ← this file
   - data/curator-log.json           ← see what yesterday's run did
   - scripts/sources.json            ← query bank + source list
3. Generate today's run_id: `YYYY-MM-DD-HHMM` from current UTC time.

==== STEP 1: Refresh (always do this) ====
- Pick the 3 entries with the oldest `last_verified` dates in data/entries.json.
- For each: HTTP HEAD/GET the URL.
  - 200: bump `last_verified` to today. If the page has a noticeably better
    one-line pitch than your current summary, refine it (but do NOT lose the
    factual + "vs. obvious alternative" framing).
  - 301→200 to a related URL: update `url`, bump `last_verified`, note in
    commit message.
  - 4xx/5xx persistent or 301 to unrelated domain: archive the entry per
    CLAUDE.md rule 4 (append to archive/removed.json with reason).

==== STEP 2: Refine (always do this) ====
- Pick 1 random entry that isn't in the refresh batch.
- Re-read its summary and why_it_matters. Ask: "If I wrote this fresh today,
  would I write the same thing?"
- If yes: do nothing.
- If no: edit it. Common improvements:
  - Add a comparison to a tool the wiki has added since this entry was written.
  - Replace vague language with a concrete number (latency, context size,
    benchmark score) if you can verify it.
  - Trim words. Aim for shorter, sharper.

==== STEP 3: Discover (try to do this) ====
- Get the next query from scripts/sources.json::query_bank, indexed by
  data/curator-log.json::rotation_pointer (wrap around at end of list).
- WebSearch that query. Also scan the top 1–3 high_signal sources from
  scripts/sources.json (rotate which ones you hit, log which you visited).
- Build a candidate list. For each candidate:
  - Is it already in data/entries.json? (search by domain + name)
  - Is it in archive/removed.json? (skip)
  - Does it have a public URL returning 200?
  - Can you write a non-hype "why it matters" comparing it to an existing entry?
- If you get 1–2 candidates that pass: add them.
- If zero: that's fine. Log "no candidates from query: X" and move on.
- HARD CAP: at most 2 new entries per run.

==== STEP 4: Verify the build ====
- Run: python scripts/render.py
- It should print "Rendered N entries across 8 categories." with N matching
  the entry count in entries.json.
- If render fails: revert your data edits (`git checkout -- data/`) and exit 1
  with a clear error message in the log.

==== STEP 5: Log the run ====
Append a record to data/curator-log.json with this exact shape:

  {
    "run_id": "YYYY-MM-DD-HHMM",
    "started_at": "...UTC iso...",
    "ended_at":   "...UTC iso...",
    "added":      ["id1", "id2"],
    "refreshed":  ["id3", "id4", "id5"],
    "refined":    ["id6"],
    "removed":    [{"id": "id7", "reason": "domain dead"}],
    "sources_checked": ["query: X", "anthropic-blog", "github-trending"],
    "notes": "1-2 sentence summary"
  }

Then increment `rotation_pointer` (modulo length of query_bank).

==== STEP 6: Commit and push ====
- If `git status --porcelain` is empty: STOP. Do not commit. Do not push.
  Write the empty run to the log only if step 1's refresh produced no diff,
  which should be rare.
- Otherwise:
  - Commit message:
        curator: <N> added / <M> refreshed / <K> refined / <R> removed (run_id)

        - added: <ids or none>
        - refreshed: <ids or none>
        - refined: <ids or none>
        - removed: <ids or none>
        - sources: <comma list>

  - git push origin main
  - The Pages workflow handles deploy.

==== HARD RULES ====
- Never edit: index.html, feed.xml, README.md outside the
  <!-- RECENTLY_ADDED:START --> markers, templates/*, scripts/*, static/*.
- Never use hype adjectives. Banned: revolutionary, game-changing, AI-powered,
  cutting-edge, next-generation, paradigm-shifting, supercharged, unleash.
- Never add an entry you cannot verify with a 200 response.
- Never bypass archive: removed entries always go to archive/removed.json first.
- Never push if pre-commit hooks fail. Investigate, fix, re-commit.
- Never commit secrets, API keys, or tokens. Reject any source that requires
  one of yours.
```

---

## Sources to scan

The curator rotates through `scripts/sources.json::query_bank` (currently 22 queries) one entry per day. It additionally checks 1–3 of these high-signal feeds per run:

### Tier-1 (check most days)

| Source                   | URL                                      | Why                                                        |
| ------------------------ | ---------------------------------------- | ---------------------------------------------------------- |
| Anthropic news           | https://www.anthropic.com/news           | Claude releases, agent SDK, skills                         |
| OpenAI news              | https://openai.com/news/                 | API and Codex updates                                      |
| Google DeepMind blog     | https://deepmind.google/discover/blog/   | Gemini and research                                        |
| Hacker News front page   | https://news.ycombinator.com/            | Builder sentiment                                          |
| GitHub trending (weekly) | https://github.com/trending?since=weekly | Surfacing OSS releases                                     |
| Smithery MCP registry    | https://smithery.ai                      | New MCP servers                                            |
| The AI Search (YouTube)  | https://www.youtube.com/@theAIsearch     | Tool reviews / weekly digests — see "YouTube intake" below |

### Tier-2 (rotate, hit one or two per run)

- Product Hunt AI — https://www.producthunt.com/topics/artificial-intelligence
- AI Tidbits — https://www.aitidbits.ai/
- Interconnects — https://www.interconnects.ai/
- Latent Space — https://www.latent.space/
- ThursdAI — https://sub.thursdai.news/
- Hugging Face papers (daily) — https://huggingface.co/papers

---

## YouTube intake (The AI Search and similar channels)

For YouTube sources, scraping the page directly fails (JS-rendered). The curator must use one of these access patterns:

### Option A: RSS feed (preferred — works in any cowork session)

Every YouTube channel exposes an RSS feed. For **The AI Search**:

```
https://www.youtube.com/feeds/videos.xml?channel_id=UCIgnGlGkVRhd4qNFcEwLL4A
```

Fetch the feed. Extract the latest 5–10 video titles + descriptions. Look for:

- Tool names in titles (e.g., "I tested {X} and {Y}")
- Comparison videos (e.g., "{X} vs {Y}") — both halves are candidates
- "New AI tool" videos — high signal for fresh releases
- "Top N AI tools for {use case}" — extract the unique mentions

For each candidate tool name:

1. Search for its canonical URL (homepage or GitHub).
2. Verify the URL returns 200.
3. Run it through the standard quality bar.
4. If it passes and isn't already in the wiki, add it.

### Option B: NotebookLM MCP (when available)

If the cowork session has `notebooklm-mcp` available:

1. Create a notebook seeded with the channel's RSS feed and 5 recent video URLs.
2. Ask: "List every distinct AI tool, model, framework, agent, or product mentioned in these videos. For each, give the canonical URL if mentioned, and one sentence on what it does. Group by category."
3. Run candidates through verification + quality bar.

### Other channels worth scanning (rotate one per week)

- Matt Wolfe — `https://www.youtube.com/feeds/videos.xml?channel_id=UCORIeT1hk6tYBuntEXsguLg`
- Wes Roth — `https://www.youtube.com/feeds/videos.xml?channel_id=UCqcbQf6yw5KzRoDDcZ_wBSw`
- AI Explained — `https://www.youtube.com/feeds/videos.xml?channel_id=UCNJ1Ymd5yFuUPtn21xtRbbw`
- David Ondrej — `https://www.youtube.com/feeds/videos.xml?channel_id=UCcfWTRMP2LcKvDS44yITihA`

When in doubt, prefer creators who consistently link to homepages in their descriptions over those who only push affiliate links.

---

## Commit message examples (good ones)

```text
curator: 2 added / 3 refreshed / 1 refined / 0 removed (2026-05-13-0600)

- added: smithery-mcp-cli, exa-search
- refreshed: claude-code, cursor, windsurf
- refined: pgvector (sharpened "vs Pinecone" framing)
- sources: query "AI search API for agents", anthropic-blog, hn-frontpage
```

```text
curator: 0 added / 3 refreshed / 1 refined / 1 removed (2026-05-14-0600)

- refreshed: braintrust, langfuse, inspect
- refined: openai-api (added Responses API note now that it's GA)
- removed: cline-old-domain (archived; domain redirects to spam)
- sources: query "LLM eval framework", github-trending, youtube/theAIsearch
- notes: no new candidates passed quality bar today
```

## Commit message examples (bad ones to avoid)

```text
update entries        ← vague, no run_id, no counts
fix typo              ← if it's just a typo, fine, but use the curator format
add 5 new tools       ← exceeds the 2-per-run cap
```

---

## Failure modes and recovery

| Symptom                           | What happened                                      | Recovery                                                            |
| --------------------------------- | -------------------------------------------------- | ------------------------------------------------------------------- |
| `git push` rejected               | Concurrent run or wrong auth                       | Pull, re-render to confirm clean, retry                             |
| `python scripts/render.py` errors | Invalid JSON in entries.json                       | `git checkout -- data/` to revert, log the bad candidate id, exit 1 |
| WebSearch returns nothing         | Query too narrow, or API throttle                  | Log "query empty" and proceed with refresh-only                     |
| 5+ candidates from same vendor    | Source bias (e.g., one Anthropic news post)        | Pick the most interesting one, skip the rest                        |
| YouTube RSS returns empty         | Channel ID wrong or feed throttled                 | Skip YouTube for this run, log the issue                            |
| Pages deploy failed               | Usually a templating error after a malformed entry | Check the failed workflow log; revert the offending entry; retry    |

If you hit a failure you can't classify, do not push. Write the failure to the curator log with `"notes": "FAILED: <description>"` and exit non-zero. The next run will see the failed log and a human can intervene.

---

## What the curator must NEVER do

(Mirrored from `CLAUDE.md` for self-containment.)

- Don't add entries it can't verify with a 200 response.
- Don't edit `index.html`, `feed.xml`, the auto-section of `README.md`, templates, or scripts.
- Don't commit if there is genuinely no change AND step 1's refresh found nothing to bump.
- Don't bypass the archive: removed entries must be appended to `archive/removed.json` first.
- Don't add hype copy. Use comparison-to-alternative framing instead.
- Don't add more than 2 new entries per run.
- Don't run on weekends.
- Don't commit on behalf of the user without the `Co-Authored-By` line if the cowork runtime supports it.

---

## Verifying a run worked (what a human checks the next morning)

1. Open https://github.com/FelixKruger/ai-builder-wiki/commits/main — there should be a `curator: ...` commit dated today.
2. Open https://felixkruger.github.io/ai-builder-wiki/ — the `Last curated:` date in the header should be today.
3. Open `data/curator-log.json` — the latest run should reflect what the commit message said.
4. If the wiki has not been updated for 2+ days in a row, the curator is failing silently. Read the cowork run logs and check the failure modes table above.
