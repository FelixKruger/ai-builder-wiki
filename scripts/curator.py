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
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests

import maintenance

ROOT = Path(__file__).resolve().parent.parent
ENTRIES = ROOT / "data" / "entries.json"
LOG = ROOT / "data" / "curator-log.json"
ARCHIVE = ROOT / "archive" / "removed.json"
HEALTH = ROOT / "HEALTH.md"
MSG_FILE = ROOT / ".curator-message"

# Max entries per category (CLAUDE.md rule 3). Keeps the page scannable.
CATEGORY_CAP = 12

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


def parse_candidates_from_text(text: str) -> list[dict]:
    """
    Extract candidate JSON from a free-text response.
    Tries: (1) direct JSON parse, (2) strip code fences, (3) regex for the
    {"candidates": [...]} block. Returns up to 2 candidates.
    """
    # Strip common markdown code fences
    cleaned = re.sub(r"^\s*```(?:json)?\s*\n?", "", text.strip())
    cleaned = re.sub(r"\n?\s*```\s*$", "", cleaned)

    # Try direct JSON parse
    for candidate_text in (cleaned, text):
        try:
            obj = json.loads(candidate_text)
            if isinstance(obj, dict) and "candidates" in obj:
                cs = obj["candidates"]
                if isinstance(cs, list):
                    return cs[:2]
            if isinstance(obj, list):
                return obj[:2]
        except json.JSONDecodeError:
            pass

    # Regex fallback — find the candidates array body
    match = re.search(
        r'"candidates"\s*:\s*(\[.*?\])',
        cleaned,
        re.DOTALL,
    )
    if match:
        try:
            arr = json.loads(match.group(1))
            if isinstance(arr, list):
                return arr[:2]
        except json.JSONDecodeError:
            pass

    return []


def ask_gemini(data: dict, api_key: str) -> tuple[list[dict], list[str]]:
    """
    Ask Gemini for 1-2 new tool candidates, grounded in live Google Search.
    Returns (candidates, search_sources_consulted).
    """
    try:
        from google import genai
        from google.genai import types
    except ImportError:
        print("google-genai not installed. Run: pip install google-genai", file=sys.stderr)
        return [], []

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
Use Google Search to find 1 to 2 NEW high-quality AI tools, models, agents,
frameworks, benchmarks, or infrastructure that working AI builders are
actually talking about RIGHT NOW — and that are NOT already in the wiki.

SEARCH STRATEGY (pick one or combine):
- Search Hacker News and Lobsters for AI builder launches in the past 30 days.
- Search GitHub Trending for AI/agent repos this week.
- Search Product Hunt for AI tools launched this month.
- Search recent posts on @theAIsearch, Matt Wolfe, AI Explained YouTube channels.
- Search for "{{vendor}} announces" or "{{tool}} launched" from Anthropic, OpenAI,
  Google, Mistral, DeepSeek, Alibaba, Tencent in the past 30 days.
- For each finding, follow citations to a canonical homepage or GitHub repo URL.

STRICT RULES:
1. Must have a canonical homepage URL that exists today (verify via the
   search results — do not invent URLs).
2. Must NOT be in the existing list above (check by name and by URL).
3. Must fit one of the existing category IDs — do not invent new categories.
4. Summary: ONE sentence, ~25 words max, factual, no marketing copy.
5. Why-it-matters: 1-2 sentences. Compare to the obvious alternative
   already in the wiki when useful.
6. BANNED WORDS in summary and why_it_matters: revolutionary,
   game-changing, AI-powered, cutting-edge, next-generation,
   paradigm-shifting, supercharged, unleash, groundbreaking.
7. Prefer broad-impact tools many builders actually use, not niche experiments.
8. Diversity: avoid 3+ entries from the same vendor in any category.
9. Prefer tools first surfaced in the past 6 months — the wiki should
   stay current. Only add older tools if they're notably absent and
   widely used.

If you cannot find 1-2 high-quality candidates that pass ALL rules,
return an empty candidates list. Better to add nothing than to add noise.

RESPONSE FORMAT — output a single JSON object. You may add brief commentary
before or after, but the JSON object MUST be parseable on its own:

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
    sources: list[str] = []

    try:
        # Google Search grounding — Gemini does the live web search for us.
        # Free on the Gemini API free tier (Flash: ~500 grounded queries/day,
        # we use 1/day).
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                tools=[types.Tool(google_search=types.GoogleSearch())],
                temperature=0.6,
            ),
        )
        text = response.text or ""
    except Exception as e:
        print(f"Gemini call failed: {e}", file=sys.stderr)
        return [], []

    # Extract grounding citations (the URLs Gemini actually consulted).
    try:
        for cand in (response.candidates or []):
            gm = getattr(cand, "grounding_metadata", None)
            if not gm:
                continue
            for chunk in (getattr(gm, "grounding_chunks", None) or []):
                web = getattr(chunk, "web", None)
                if web and getattr(web, "uri", None):
                    sources.append(web.uri)
    except Exception as e:
        print(f"  (note) could not extract grounding sources: {e}", file=sys.stderr)

    # De-duplicate sources, preserve order.
    seen: set[str] = set()
    sources = [s for s in sources if not (s in seen or seen.add(s))]
    print(f"  Gemini consulted {len(sources)} web source(s) via grounded search")

    candidates = parse_candidates_from_text(text)
    if not candidates:
        print(f"  Could not parse candidates. Raw response (first 600 chars):\n  {text[:600]}", file=sys.stderr)
    return candidates, sources


def has_banned_words(*texts: str) -> str | None:
    for t in texts:
        lower = (t or "").lower()
        for word in BANNED_WORDS:
            if word in lower:
                return word
    return None


def vet_candidate(
    c: dict,
    existing_ids: set[str],
    existing_urls: set[str],
    valid_cats: set[str],
    cat_counts: dict[str, int] | None = None,
) -> tuple[bool, str]:
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

    # CLAUDE.md rule 3: never let a category exceed the cap.
    if cat_counts is not None and cat_counts.get(c["category"], 0) >= CATEGORY_CAP:
        return False, f"category '{c['category']}' is full ({CATEGORY_CAP} cap)"

    bad = has_banned_words(c["summary"], c["why_it_matters"])
    if bad:
        return False, f"banned word: {bad}"

    status, final_url = http_check(c["url"])
    if status != 200:
        return False, f"URL returned HTTP {status}"
    if final_url and final_url != c["url"]:
        c["url"] = final_url  # capture redirect

    return True, "ok"


def make_prune_chooser(api_key: str | None):
    """
    Build a chooser(category, entries, n) -> [entry_id, ...] backed by Gemini.

    Picking which entry to cut needs world knowledge — is this tool widely used,
    or a repo that trended for a week? A deterministic score can't tell, and got
    it badly wrong in testing (it wanted to cut OpenAI Codex and keep an
    unmaintained fork). Returns None when no key is set, in which case
    maintenance falls back to the deterministic score.
    """
    if not api_key:
        return None

    def chooser(category: dict, entries: list[dict], n: int) -> list[str]:
        from google import genai
        from google.genai import types

        listing = [
            {"id": e["id"], "name": e["name"], "url": e["url"], "summary": e["summary"]}
            for e in entries
        ]
        prompt = f"""You are curating the "{category['name']}" section of a wiki for
AI builders. The section is over its {CATEGORY_CAP}-entry cap and must lose exactly {n} entr{'y' if n == 1 else 'ies'}.

Entries:
{json.dumps(listing, indent=2)}

Pick the {n} LEAST essential for a working AI builder in {today()[:4]}. Prefer to cut:
- Tools that are obscure, abandoned, or were briefly trendy but never adopted
- Near-duplicates of a stronger entry in the same list
- Anything superseded by a newer tool in the list

Never cut a widely adopted, actively maintained tool just because it is older.

Return ONLY JSON: {{"drop": ["id1"{', "id2"' if n > 1 else ''}], "reason": "one sentence"}}"""

        client = genai.Client(api_key=api_key)
        resp = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json", temperature=0.2
            ),
        )
        obj = json.loads(resp.text or "{}")
        drop = obj.get("drop", [])
        if obj.get("reason"):
            print(f"    chooser: {obj['reason']}")
        return drop if isinstance(drop, list) else []

    return chooser


def write_curator_message(
    added: list[str],
    refreshed: list[str],
    removed: list[dict],
    pruned: list[dict],
    deduped: list[dict],
    rid: str,
) -> None:
    total_removed = len(removed) + len(pruned) + len(deduped)
    lines = [
        f"curator: {len(added)} added / {len(refreshed)} refreshed / {total_removed} removed ({rid})",
        "",
    ]
    if added:
        lines.append(f"- added: {', '.join(added)}")
    if refreshed:
        lines.append(f"- refreshed: {', '.join(refreshed)}")
    if removed:
        lines.append(f"- dead links: {', '.join(r['id'] for r in removed)}")
    if pruned:
        lines.append(f"- pruned (over cap): {', '.join(r['id'] for r in pruned)}")
    if deduped:
        lines.append(f"- deduped: {', '.join(r['id'] for r in deduped)}")
    if not (added or refreshed or removed or pruned or deduped):
        lines.append("- health check only (all URLs current, no quality issues found)")
    lines.append("- via: GitHub Actions + Gemini 2.5 Flash (free tier)")
    lines.append("")
    MSG_FILE.write_text("\n".join(lines), encoding="utf-8")


def write_health_report(health: dict, rid: str) -> None:
    """Human-readable wiki health dashboard, regenerated every run."""
    lines = [
        "# Wiki health",
        "",
        f"_Generated by the daily curator, run `{rid}`._",
        "",
        f"- **Entries:** {health['total_entries']} across {health['categories']} categories",
        f"- **Oldest verification:** {health['oldest_verified']}",
        f"- **Newest verification:** {health['newest_verified']}",
        f"- **Entries over category cap:** {len(health['over_cap'])}",
        f"- **Entries with marketing language:** {health['hype_count']}",
        f"- **Probable duplicates:** {health['duplicate_count']}",
        f"- **Similar-name pairs (needs human eye):** {health['similar_name_pairs']}",
        "",
        "## Entries per category",
        "",
        "| Category | Count | Status |",
        "| --- | ---: | --- |",
    ]
    for name, n in health["per_category"].items():
        status = "over cap" if name in health["over_cap"] else "ok"
        lines.append(f"| {name} | {n} | {status} |")

    lines += [
        "",
        "## Where entries came from",
        "",
        "| Source | Count |",
        "| --- | ---: |",
    ]
    for src, n in sorted(health["by_source"].items(), key=lambda kv: -kv[1]):
        lines.append(f"| {src} | {n} |")
    lines.append("")

    HEALTH.write_text("\n".join(lines), encoding="utf-8")


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
    search_sources: list[str] = []
    if not api_key:
        print(
            "\nStep 2: SKIPPED — GEMINI_API_KEY not set. "
            "Add a free key from https://aistudio.google.com/apikey "
            "as a repo secret to enable new-tool discovery with live search.",
            file=sys.stderr,
        )
        candidates: list[dict] = []
    else:
        print(f"\nStep 2: asking Gemini ({GEMINI_MODEL}) for new candidates (with live Google Search grounding)")
        candidates, search_sources = ask_gemini(data, api_key)
        print(f"  Gemini returned {len(candidates)} candidate(s)")

    # ---- Step 3: vet + add ----
    print(f"\nStep 3: vetting candidates")
    existing_ids = {e["id"] for e in entries}
    existing_urls = {e["url"].rstrip("/") for e in entries}
    valid_cats = {c["id"] for c in categories}
    cat_counts: dict[str, int] = {}
    for e in entries:
        cat_counts[e["category"]] = cat_counts.get(e["category"], 0) + 1
    added: list[str] = []

    for c in candidates:
        ok, reason = vet_candidate(c, existing_ids, existing_urls, valid_cats, cat_counts)
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
        cat_counts[c["category"]] = cat_counts.get(c["category"], 0) + 1
        added.append(c["id"])
        print(f"  ACCEPT: {c['id']} -> {c['category']}")

    # ---- Step 3b: quality maintenance (deterministic, no API needed) ----
    # This is what keeps the wiki from bloating and guarantees the run has
    # real work to do even when no new tool is worth adding.
    print("\nStep 3b: quality maintenance")

    deduped = []
    for keeper, loser, reason in maintenance.find_duplicates(entries):
        deduped.append(
            {
                "id": loser["id"],
                "name": loser["name"],
                "url": loser["url"],
                "removed_at": today(),
                "reason": reason,
            }
        )
        print(f"  DEDUPE: {loser['id']} ({reason})")
    if deduped:
        drop = {d["id"] for d in deduped}
        entries[:] = [e for e in entries if e["id"] not in drop]

    # At most 2 prunes per run: works a backlog off gradually and keeps each
    # commit small enough for a human to review.
    pruned = maintenance.enforce_caps(
        entries,
        categories,
        cap=CATEGORY_CAP,
        max_prunes=2,
        chooser=make_prune_chooser(api_key),
    )
    for p in pruned:
        print(f"  PRUNE: {p['id']} ({p['reason']})")
    if not pruned:
        print("  all categories within cap")

    # ---- Step 4: persist data files ----
    data["entries"] = entries
    ENTRIES.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    all_removed = removed + deduped + pruned
    if all_removed:
        # archive/removed.json is a flat list of records (CLAUDE.md rule 4).
        # Tolerate the {"removed": [...]} shape in case an old run wrote it.
        existing: list = []
        if ARCHIVE.exists():
            try:
                loaded = json.loads(ARCHIVE.read_text(encoding="utf-8") or "[]")
                existing = loaded.get("removed", []) if isinstance(loaded, dict) else loaded
            except json.JSONDecodeError:
                print("  archive/removed.json unreadable; starting a fresh list", file=sys.stderr)
        existing.extend(all_removed)
        ARCHIVE.parent.mkdir(parents=True, exist_ok=True)
        ARCHIVE.write_text(json.dumps(existing, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    # ---- Step 4b: health report (always regenerated) ----
    health = maintenance.health_report(entries, categories, cap=CATEGORY_CAP)
    write_health_report(health, rid)
    print(f"\nStep 4b: health — {health['total_entries']} entries, "
          f"{len(health['over_cap'])} categories over cap, "
          f"{health['hype_count']} entries with marketing language")

    # ---- Step 5: log the run ----
    log = json.loads(LOG.read_text(encoding="utf-8")) if LOG.exists() else {"runs": [], "rotation_pointer": 0}
    sources_checked = [f"gemini:{GEMINI_MODEL}+google-search-grounding"] if api_key else ["refresh-only (no api key)"]
    sources_checked.extend(search_sources[:20])  # cap to 20 to keep log readable
    log.setdefault("runs", []).append(
        {
            "run_id": rid,
            "started_at": started,
            "ended_at": now_iso(),
            "added": added,
            "refreshed": refreshed,
            "removed": all_removed,
            "pruned_over_cap": [p["id"] for p in pruned],
            "deduped": [d["id"] for d in deduped],
            "health": health,
            "sources_checked": sources_checked,
            "notes": "Automated GitHub Actions run with Gemini + Google Search grounding."
            if api_key
            else "Automated GitHub Actions run — refresh-only (GEMINI_API_KEY not set).",
        }
    )
    LOG.write_text(json.dumps(log, indent=2) + "\n", encoding="utf-8")

    # ---- Step 6: write commit message file ----
    write_curator_message(added, refreshed, removed, pruned, deduped, rid)

    print(
        f"\nDone. {len(added)} added, {len(refreshed)} refreshed, "
        f"{len(removed)} dead, {len(pruned)} pruned, {len(deduped)} deduped."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
