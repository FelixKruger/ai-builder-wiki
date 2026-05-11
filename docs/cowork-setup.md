# Daily curator via Claude cowork

This wiki updates itself every day. A scheduled Claude session opens the repo, runs the [`wiki-curator` skill](../skills/wiki-curator/SKILL.md), and commits any new entries.

Two ways to run it:

1. **Claude cowork** (recommended) — scheduled managed agent. Zero infrastructure to babysit.
2. **Beelink / local cron** — see [`scripts/curate.sh`](../scripts/curate.sh). Useful if you already have a home server running.

---

## Option 1: Claude cowork (recommended)

### One-time setup

1. Open the repo on [GitHub](https://github.com/felixkruger/ai-builder-wiki).
2. In Claude.ai, link your GitHub account (Settings → Integrations → GitHub) and grant **write** access to this repo.
3. Confirm the repo's Pages deploy works: Settings → Pages → Source: **GitHub Actions**.

### The daily prompt

Feed this as the prompt to a scheduled cowork agent. It's self-contained — no extra context needed.

```text
You are the daily curator for the AI Builder's Field Guide wiki.

Repository: https://github.com/felixkruger/ai-builder-wiki
Branch: main

Steps:
1. Clone (or pull) the repo and cd into it.
2. Read CLAUDE.md, skills/wiki-curator/SKILL.md, and data/curator-log.json.
3. Generate today's run_id from current UTC time (format: YYYY-MM-DD-HHMM).
4. Execute the wiki-curator skill exactly as written.
5. Verify every URL with HTTP HEAD/GET before adding or refreshing.
6. Add at most 2 new entries. Refresh 3 oldest entries by last_verified.
7. Run: python scripts/render.py
8. If git status shows no diff, exit 0 silently.
9. Otherwise commit using the format in CLAUDE.md and push to main.

The Pages workflow handles deploy. Do not edit index.html, feed.xml, the
auto-section of README.md, templates, or scripts.
```

### Scheduling

Using the [`schedule` skill](https://github.com/anthropics/anthropic-skills) (or `oh-my-claudecode:schedule`):

```text
/schedule add wiki-curator
cron: 0 6 * * *      # 06:00 UTC every day
prompt: [the daily prompt above]
```

If you don't have the schedule skill installed, you can also:

- Run the daily prompt manually in a fresh Claude.ai session whenever you remember (lower discipline, fine for a personal wiki)
- Use the [Anthropic Cowork managed agents](https://www.anthropic.com/news) console (when GA)

### Required capabilities for the agent

| Capability                                    | Why                                                                         |
| --------------------------------------------- | --------------------------------------------------------------------------- |
| `WebSearch`                                   | Discover candidate tools from query bank                                    |
| `WebFetch`                                    | Verify candidate URLs return 200                                            |
| `Bash` / shell                                | Run `python scripts/render.py`, git commit, git push                        |
| `Edit` / `Write`                              | Modify `data/entries.json`, `data/curator-log.json`, `archive/removed.json` |
| GitHub write to `felixkruger/ai-builder-wiki` | Push the commit                                                             |

---

## Option 2: Beelink / local cron

If you prefer a home server, [`scripts/curate.sh`](../scripts/curate.sh) is the cron entrypoint. It runs the local `claude` CLI (authenticated under your subscription) against the wiki-curator skill, then commits and pushes.

Install on a Linux machine with the Claude Code CLI signed in:

```bash
git clone https://github.com/felixkruger/ai-builder-wiki.git ~/projects/ai-builder-wiki
cd ~/projects/ai-builder-wiki
chmod +x scripts/curate.sh
pip install -r requirements.txt

# Add to crontab (crontab -e):
0 6 * * * /home/$USER/projects/ai-builder-wiki/scripts/curate.sh >> /home/$USER/.ai-field-guide-curator.log 2>&1
```

---

## Verifying a run worked

After a daily run, check:

- [`data/curator-log.json`](../data/curator-log.json) — should have a new run record
- The repo's [commit history](https://github.com/felixkruger/ai-builder-wiki/commits/main) — should show a `curator: ...` commit
- The [Pages workflow](https://github.com/felixkruger/ai-builder-wiki/actions) — should be green
- The live site — `Last curated:` date in the header should be today

If no commit appears and no log entry, the curator either found no candidates or hit a verification wall. Both are clean exits.

## Manual one-off test

To run the curator once in a regular Claude Code session inside the repo:

```text
Run the wiki-curator skill at skills/wiki-curator/SKILL.md.
Generate today's run_id from current UTC time.
Follow CLAUDE.md strictly. Verify every URL. Add at most 2 entries.
When done, run `python scripts/render.py`, commit, and push to main.
```

## Failure modes

| Failure               | What happens                                                              | Fix                                          |
| --------------------- | ------------------------------------------------------------------------- | -------------------------------------------- |
| Push 403              | Curator exits non-zero, log shows auth error                              | Re-link GitHub in Claude.ai settings         |
| URL verify fails      | Entry marked for removal on next run                                      | None — by design                             |
| WebSearch empty       | Curator writes "no candidates today" log and exits 0                      | None — by design                             |
| Render fails          | Curator reverts the data edit and exits non-zero                          | Check `data/entries.json` for malformed JSON |
| Category cap exceeded | Curator must archive an entry first; if it can't decide, it skips the add | None — by design                             |

## What the curator must NEVER do

(Mirroring [`CLAUDE.md`](../CLAUDE.md) — repeated here so the cowork prompt is self-contained.)

- Don't add entries it can't verify.
- Don't edit `index.html`, `feed.xml`, the auto-section of `README.md`, templates, or scripts.
- Don't commit if `git status` is clean — exit 0.
- Don't bypass the archive: removed entries must be appended to `archive/removed.json` first.
- Don't add hype copy. Compare to the obvious alternative when useful.
