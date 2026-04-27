#!/usr/bin/env bash
# Beelink cron entrypoint for the wiki curator.
# Runs the local Claude Code CLI (authenticated under the user's subscription)
# against the wiki-curator skill, then commits + pushes any changes.
#
# Install: crontab -e
#   0 6 * * * /home/<user>/projects/ai-builder-wiki/scripts/curate.sh >> /home/<user>/.ai-field-guide-curator.log 2>&1
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_DIR"

echo "=== curator run: $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="

git fetch --quiet origin main
git checkout main
git pull --ff-only origin main

if ! command -v claude >/dev/null 2>&1; then
  echo "ERROR: 'claude' CLI not found on PATH. Install Claude Code and sign in." >&2
  exit 1
fi

claude \
  --print \
  --permission-mode acceptEdits \
  "Run the wiki-curator skill at skills/wiki-curator/SKILL.md. Generate today's run_id from the current UTC time. Follow CLAUDE.md strictly. When done, do NOT commit — exit and let the shell wrapper handle git."

if [[ -z "$(git status --porcelain)" ]]; then
  echo "No changes; exiting clean."
  exit 0
fi

python3 scripts/render.py

git add -A
git diff --cached --stat

RUN_ID="$(date -u +%Y-%m-%d-%H%M)"
git commit -m "curator: daily run $RUN_ID

Automated update from skills/wiki-curator. See data/curator-log.json for details."

for attempt in 1 2 3 4; do
  if git push -u origin main; then
    echo "Pushed on attempt $attempt."
    exit 0
  fi
  sleep $((2 ** attempt))
done

echo "ERROR: push failed after 4 attempts." >&2
exit 1
