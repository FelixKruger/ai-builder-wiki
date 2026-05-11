#!/usr/bin/env python3
"""
Daily curator — runs in GitHub Actions on cron, uses Gemini 2.5 Flash (free tier).

What it does each run:
  1. Refreshes the 3 oldest entries by last_verified — HTTP-verifies each URL,
     captures redirects, archives any that 404.
  2. Asks Gemini for 1-2 new high-quality candidates similar in spirit to
     what's already in the wiki.
  3. Verifies each candidate URL returns 200 (rejects hallucinations).
  4. Appends accepted candidates to data/entries.json.
  5. Appends a run record to data/curator-log.json.
  6. Writes a commit message to .curator-message for the workflow to use.

Requires env: GEMINI_API_KEY  (free key from https://aistudio.google.com/apikey)

Exit codes:
  0  — success (changes may or may not have been made)
  1  — fatal config / API error; workflow should not push
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
ENTRIES = ROOT / "data" / "entries.json"
LOG = ROOT / "data" / "curator-log.json"
ARCHIVE = ROOT / "archive" / "removed.json"
MSG_FILE = ROOT / ".curator-message"

GEMINI_MODEL = "gemini-2.5-flash"
HTTP_TIMEOUT = 20
USER_AGENT = "AI-Builder-Wiki-Curator/1.0 (+https://github.com/FelixKruger/ai-builder-wiki)"

BANNED_WORDS = {
    "revolutionary",
    "game-changing",
    "ai-powered",
    "cutting-edge",
    "next-generation",
    "paradigm-shifting",
    "supercharged",
    "unleash",
    "groundbreaking",
}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def run_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d-%H%M")


def http_check(url: str) -> tuple[int, str]:
    """HEAD then GET fallback. Returns (status_code, final_url)."""
    headers = {"User-Agent": USER_AGENT}
    try:
        r = requests.head(url, allow_redirects=True, timeout=HTTP_TIMEOUT, headers=headers)
        if r.status_code >= 400 or r.status_code == 405:
            r = requests.get(url, allow_redirects=True, timeout=HTTP_TIMEOUT, headers=headers, stream=True)
            r.close()
        return r.status_code, r.url
    except requests.RequestException as e:
        print(f"  http_check failed for {url}: {e}", file=sys.stderr)
        return 0, url


def refresh_oldest(entries: list[dict], k: int = 3) -> tuple[list[str], list[dict]]:
    """Refresh the k entries with the oldest last_verified date. Returns (refreshed_ids, removed_records)."""
    sorted_entries = sorted(entries, key=lambda e: e.get("last_verified", ""))
    targets = sorted_entries[:k]
    refreshed: list[str] = []
    removed: list[dict] = []

    for e in targets:
        status, final_url = http_check(e["url"])
        if status == 200:
            e["last_verified"] = today()
            if final_url and final_url != e["url"]:
                e["url"] = final_url
            refreshed.append(e["id"])
            print(f"  refreshed: {e['id']} ({status})")
        elif status in (301, 302, 307, 308):
            e["last_verified"] = today()
            e["url"] = final_url
            refreshed.append(e["id"])
            print(f"  refreshed (redirect captured): {e['id']} -> {final_url}")
        else:
            # broken — schedule for archive
            removed.append(
                {
                    "id": e["id"],
                    "name": e["name"],
                    "url": e["url"],
                    "removed_at": today(),
                    "reason": f"HTTP {status} during daily refresh",
                }
            )
            print(f"  REMOVED: {e['id']} (HTTP {status})")

    # apply removals
    removed_ids = {r["id"] for r in removed}
    if removed_ids:
        entries[:] = [e for e in entries if e["id"] not in removed_ids]

    return refreshed, removed


def ask_gemini(data: dict, api_key: str) -> list[dict]:
    """Ask Gemini for 1-2 new tool candidates. Returns list (may be empty)."""
    try:
        from google import genai
        from google.genai import types
    except ImportError:
        print("google-genai not installed. Run: pip install google-genai", file=sys.stderr)
        return []

    entries = data["entries"]
    categories = data["categories"]

    existing_compact = [
        {"id": e["id"], "name": e["name"], "category": e["category"], "url": e["url"]}
        for e in entries
    ]
    cats_compact = [
        {
            "id": c["id"],
            "name": c["name"],
            "section": c.get("section", ""),
            "intent": c.get("intent", ""),
            "blurb": c.get("blurb", ""),
        }
        for c in categories
    ]

    prompt = f"""You are the daily curator for the AI Builder's Field Guide
(https://felixkruger.github.io/ai-builder-wiki/).

Today is {today()}.

The wiki already has these {len(existing_compact)} entries:
{json.dumps(existing_compact, indent=2)}

These are the {len(cats_compact)} categories (organized into sections):
{json.dumps(cats_compact, indent=2)}

YOUR JOB:
Propose 1 to 2 NEW high-quality AI tools, models, agents, frameworks,
benchmarks, or infrastructure that are similar in spirit to what's
already in the wiki but NOT already present.

STRICT RULES:
1. Must have a canonical homepage URL you are confident exists.
2. Must NOT be in the existing list above (check by name and URL).
3. Must fit one of the existing category IDs — do not invent new categories.
4. Summary: ONE sentence, ~25 words max, factual, no marketing copy.
5. Why-it-matters: 1-2 sentences. Compare to the obvious alternative
   already in the wiki when useful.
6. BANNED WORDS in summary and why_it_matters: revolutionary,
   game-changing, AI-powered, cutting-edge, next-generation,
   paradigm-shifting, supercharged, unleash, groundbreaking.
7. Prefer broad-impact tools many builders actually use, not niche
   experiments.
8. Diversity: avoid 3+ entries from the same vendor in any category.

If you cannot find 1-2 high-quality candidates that pass ALL rules,
return an empty candidates list.

RESPONSE FORMAT — return ONLY valid JSON, no markdown fences, no commentary:
{{
  "candidates": [
    {{
      "id": "kebab-case-stable-id",
      "name": "Display Name",
      "url": "https://homepage.example.com/",
      "category": "exact-category-id-from-list",
      "summary": "One factual sentence.",
      "why_it_matters": "Comparison-driven sentence or two."
    }}
  ]
}}
"""

    client = genai.Client(api_key=api_key)

    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.7,
            ),
        )
        text = response.text or ""
    except Exception as e:
        print(f"Gemini call failed: {e}", file=sys.stderr)
        return []

    try:
        result = json.loads(text)
        candidates = result.get("candidates", [])
        if not isinstance(candidates, list):
            return []
        return candidates[:2]
    except (json.JSONDecodeError, AttributeError) as e:
        print(f"Failed to parse Gemini JSON: {e}\nRaw: {text[:500]}", file=sys.stderr)
        return []


def has_banned_words(*texts: str) -> str | None:
    for t in texts:
        lower = (t or "").lower()
        for word in BANNED_WORDS:
            if word in lower:
                return word
    return None


def vet_candidate(c: dict, existing_ids: set[str], existing_urls: set[str], valid_cats: set[str]) -> tuple[bool, str]:
    """Returns (accepted, reason_if_rejected)."""
    required = ("id", "name", "url", "category", "summary", "why_it_matters")
    for k in required:
        if not c.get(k):
            return False, f"missing field {k}"

    if c["id"] in existing_ids:
        return False, "duplicate id"
    if c["url"].rstrip("/") in existing_urls:
        return False, "duplicate url"
    if c["category"] not in valid_cats:
        return False, f"invalid category {c['category']}"

    bad = has_banned_words(c["summary"], c["why_it_matters"])
    if bad:
        return False, f"banned word: {bad}"

    status, final_url = http_check(c["url"])
    if status != 200:
        return False, f"URL returned HTTP {status}"
    if final_url and final_url != c["url"]:
        c["url"] = final_url  # capture redirect

    return True, "ok"


def write_curator_message(added: list[str], refreshed: list[str], removed: list[dict], rid: str) -> None:
    lines = [
        f"curator: {len(added)} added / {len(refreshed)} refreshed / {len(removed)} removed ({rid})",
        "",
    ]
    if added:
        lines.append(f"- added: {', '.join(added)}")
    if refreshed:
        lines.append(f"- refreshed: {', '.join(refreshed)}")
    if removed:
        lines.append(f"- removed: {', '.join(r['id'] + ' (' + r['reason'] + ')' for r in removed)}")
    if not (added or refreshed or removed):
        lines.append("- no-op (URL verification only, nothing changed)")
    lines.append("- via: GitHub Actions + Gemini 2.5 Flash (free tier)")
    lines.append("")
    MSG_FILE.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    api_key = os.environ.get("GEMINI_API_KEY")
    rid = run_id()
    started = now_iso()
    print(f"Curator run {rid} started.")

    data = json.loads(ENTRIES.read_text(encoding="utf-8"))
    entries = data["entries"]
    categories = data["categories"]

    # ---- Step 1: refresh oldest (always runs, no API needed) ----
    print(f"\nStep 1: refreshing 3 oldest entries by last_verified")
    refreshed, removed = refresh_oldest(entries, k=3)

    # ---- Step 2: ask Gemini for candidates (skipped if no key) ----
    if not api_key:
        print(
            "\nStep 2: SKIPPED — GEMINI_API_KEY not set. "
            "Add a free key from https://aistudio.google.com/apikey "
            "as a repo secret to enable new-tool discovery.",
            file=sys.stderr,
        )
        candidates: list[dict] = []
    else:
        print(f"\nStep 2: asking Gemini ({GEMINI_MODEL}) for new candidates")
        candidates = ask_gemini(data, api_key)
        print(f"  Gemini returned {len(candidates)} candidate(s)")

    # ---- Step 3: vet + add ----
    print(f"\nStep 3: vetting candidates")
    existing_ids = {e["id"] for e in entries}
    existing_urls = {e["url"].rstrip("/") for e in entries}
    valid_cats = {c["id"] for c in categories}
    added: list[str] = []

    for c in candidates:
        ok, reason = vet_candidate(c, existing_ids, existing_urls, valid_cats)
        if not ok:
            print(f"  REJECT: {c.get('id', '?')} -> {reason}")
            continue
        new_entry = {
            "id": c["id"],
            "name": c["name"],
            "url": c["url"],
            "category": c["category"],
            "summary": c["summary"],
            "why_it_matters": c["why_it_matters"],
            "last_verified": today(),
            "source": f"curator:{rid}",
            "added": today(),
        }
        entries.append(new_entry)
        existing_ids.add(c["id"])
        existing_urls.add(c["url"].rstrip("/"))
        added.append(c["id"])
        print(f"  ACCEPT: {c['id']} -> {c['category']}")

    # ---- Step 4: persist data files ----
    data["entries"] = entries
    ENTRIES.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    if removed:
        if ARCHIVE.exists():
            archive_data = json.loads(ARCHIVE.read_text(encoding="utf-8"))
            if "removed" not in archive_data:
                archive_data["removed"] = []
        else:
            archive_data = {"removed": []}
        archive_data["removed"].extend(removed)
        ARCHIVE.parent.mkdir(parents=True, exist_ok=True)
        ARCHIVE.write_text(json.dumps(archive_data, indent=2) + "\n", encoding="utf-8")

    # ---- Step 5: log the run ----
    log = json.loads(LOG.read_text(encoding="utf-8")) if LOG.exists() else {"runs": [], "rotation_pointer": 0}
    log.setdefault("runs", []).append(
        {
            "run_id": rid,
            "started_at": started,
            "ended_at": now_iso(),
            "added": added,
            "refreshed": refreshed,
            "removed": removed,
            "sources_checked": [f"gemini:{GEMINI_MODEL}"],
            "notes": "Automated GitHub Actions run.",
        }
    )
    LOG.write_text(json.dumps(log, indent=2) + "\n", encoding="utf-8")

    # ---- Step 6: write commit message file ----
    write_curator_message(added, refreshed, removed, rid)

    print(f"\nDone. {len(added)} added, {len(refreshed)} refreshed, {len(removed)} removed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
