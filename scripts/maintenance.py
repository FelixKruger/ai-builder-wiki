#!/usr/bin/env python3
"""
Quality-maintenance actions for the daily curator.

The curator used to only know how to ADD entries. That bloats the wiki
(148 entries, five categories over the 12-entry cap in CLAUDE.md) and means
some days it has nothing useful to do.

This module gives it a repertoire of genuinely useful maintenance work so
every run improves the wiki, whether or not a new tool is worth adding:

  enforce_caps()  — archive the weakest entry in any over-cap category
  find_duplicates() — same-domain / near-name collisions
  find_hype()     — entries whose copy drifted into marketing language
  find_stale()    — entries whose "why it matters" predates newer comparables

All actions are deterministic and need no API key, so a run still does real
work when the LLM is unavailable.
"""
from __future__ import annotations

import re
from collections import defaultdict
from urllib.parse import urlparse

# Superset of the curator's banned list — these all crept into live copy.
HYPE_WORDS = [
    "revolutionary",
    "game-changing",
    "game changing",
    "ai-powered",
    "cutting-edge",
    "cutting edge",
    "next-generation",
    "next generation",
    "paradigm",
    "supercharged",
    "unleash",
    "groundbreaking",
    "seamless",
    "seamlessly",
    "effortless",
    "effortlessly",
    "powerful",
    "robust",
    "best-in-class",
    "state-of-the-art",
    "blazing",
    "turbocharged",
]

# Entries from these sources were deliberate human choices — never auto-prune.
PROTECTED_SOURCES = ("seed", "human:")


# An entry this widely adopted is never pruned on model judgement alone.
# The chooser once justified cutting openai/codex (100k+ stars) as "an
# abandoned project superseded by newer tools" — confidently, and wrongly.
# Stars are a crude signal but an objective one, and this is a floor, not a
# ranking: below it the model still decides.
POPULARITY_FLOOR = 20_000
_STAR_CACHE: dict[str, int | None] = {}


def domain_of(url: str) -> str:
    return urlparse(url).netloc.replace("www.", "").lower()


def github_repo(url: str) -> str | None:
    """owner/name for a github.com URL, else None."""
    if domain_of(url) != "github.com":
        return None
    parts = [p for p in urlparse(url).path.split("/") if p]
    return f"{parts[0]}/{parts[1]}" if len(parts) >= 2 else None


def github_stars(url: str, token: str | None = None) -> int | None:
    """Star count for a GitHub entry, or None if not GitHub / lookup failed."""
    repo = github_repo(url)
    if not repo:
        return None
    if repo in _STAR_CACHE:
        return _STAR_CACHE[repo]

    stars = None
    try:
        import requests

        headers = {"Accept": "application/vnd.github+json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        r = requests.get(f"https://api.github.com/repos/{repo}", headers=headers, timeout=15)
        if r.status_code == 200:
            stars = r.json().get("stargazers_count")
    except Exception:
        stars = None

    _STAR_CACHE[repo] = stars
    return stars


def is_load_bearing(entry: dict, token: str | None = None) -> bool:
    """True when an entry is too widely adopted to prune automatically."""
    stars = github_stars(entry.get("url", ""), token)
    return stars is not None and stars >= POPULARITY_FLOOR


def is_protected(entry: dict) -> bool:
    src = entry.get("source", "")
    return any(src.startswith(p) for p in PROTECTED_SOURCES)


def weakness_score(entry: dict) -> tuple:
    """
    Lower sorts first = weaker = pruned first.

    Deterministic fallback only — used when no popularity signal is available.
    Ranking: unprotected before protected, then least-recently-verified,
    then most-recently-added (newest auto-adds are the least proven).
    """
    return (
        1 if is_protected(entry) else 0,
        entry.get("last_verified", ""),
        # invert "added" so newer additions prune before older established ones
        tuple(-int(p) for p in re.findall(r"\d+", entry.get("added", "0-0-0"))[:3]),
    )


def over_cap_categories(
    entries: list[dict], categories: list[dict], cap: int = 12
) -> list[tuple[dict, list[dict], int]]:
    """Return (category, its entries, overflow_count) for every category over cap."""
    by_cat: dict[str, list[dict]] = defaultdict(list)
    for e in entries:
        by_cat[e["category"]].append(e)

    out = []
    for c in categories:
        items = by_cat.get(c["id"], [])
        overflow = len(items) - cap
        if overflow > 0:
            out.append((c, items, overflow))
    # biggest offender first
    out.sort(key=lambda t: -t[2])
    return out


def enforce_caps(
    entries: list[dict],
    categories: list[dict],
    cap: int = 12,
    max_prunes: int = 2,
    chooser=None,
    github_token: str | None = None,
) -> list[dict]:
    """
    Archive the weakest entries in over-cap categories — at most `max_prunes`
    per run so a backlog is worked off gradually and stays reviewable, rather
    than deleting a third of the wiki in one commit.

    `chooser(category, items, n)` may return a list of entry ids to drop
    (LLM-assisted judgement). Anything it returns that is protected or unknown
    is ignored, and the deterministic weakness score fills any shortfall.

    Returns archive records; mutates `entries` in place.
    """
    removed: list[dict] = []
    budget = max_prunes

    for cat, items, overflow in over_cap_categories(entries, categories, cap):
        if budget <= 0:
            break
        want = min(overflow, budget)
        prunable = []
        for e in items:
            if is_protected(e):
                continue
            if is_load_bearing(e, github_token):
                print(f"    keeping {e['id']}: too widely adopted to auto-prune")
                continue
            prunable.append(e)
        if not prunable:
            continue

        by_id = {e["id"]: e for e in prunable}
        picks: list[dict] = []

        if chooser is not None:
            try:
                for eid in chooser(cat, prunable, want) or []:
                    if eid in by_id and by_id[eid] not in picks:
                        picks.append(by_id[eid])
                    if len(picks) >= want:
                        break
            except Exception:
                picks = []

        # fill any shortfall deterministically
        if len(picks) < want:
            for e in sorted(prunable, key=weakness_score):
                if e not in picks:
                    picks.append(e)
                if len(picks) >= want:
                    break

        for e in picks[:want]:
            removed.append(
                {
                    "id": e["id"],
                    "name": e["name"],
                    "url": e["url"],
                    "removed_at": e.get("last_verified", ""),
                    "reason": (
                        f"category cap: {cat['name']} had {len(items)} entries "
                        f"(cap {cap}); pruned as lowest-signal for this category"
                    ),
                }
            )
            budget -= 1

    if removed:
        drop = {r["id"] for r in removed}
        entries[:] = [e for e in entries if e["id"] not in drop]

    return removed


def find_duplicates(entries: list[dict]) -> list[tuple[dict, dict, str]]:
    """
    Detect probable duplicates. Returns (keep, drop, reason) triples.

    Two signals:
      1. Identical canonical URL (after stripping trailing slash) — certain dupe.
      2. Same repo path on github.com — certain dupe.
    Name similarity alone is too noisy to auto-act on, so it is reported by
    the health check but never auto-pruned here.
    """
    pairs: list[tuple[dict, dict, str]] = []

    by_url: dict[str, list[dict]] = defaultdict(list)
    for e in entries:
        key = e["url"].rstrip("/").lower()
        by_url[key].append(e)

    for key, group in by_url.items():
        if len(group) < 2:
            continue
        ranked = sorted(group, key=weakness_score, reverse=True)
        keeper = ranked[0]
        for loser in ranked[1:]:
            pairs.append((keeper, loser, f"duplicate URL of {keeper['id']}"))

    # same github repo reached via different URL forms
    by_repo: dict[str, list[dict]] = defaultdict(list)
    for e in entries:
        u = urlparse(e["url"])
        if domain_of(e["url"]) == "github.com":
            parts = [p for p in u.path.split("/") if p]
            if len(parts) >= 2:
                by_repo[f"{parts[0].lower()}/{parts[1].lower()}"].append(e)

    already = {p[1]["id"] for p in pairs}
    for repo, group in by_repo.items():
        if len(group) < 2:
            continue
        ranked = sorted(group, key=weakness_score, reverse=True)
        keeper = ranked[0]
        for loser in ranked[1:]:
            if loser["id"] in already or loser["id"] == keeper["id"]:
                continue
            pairs.append((keeper, loser, f"same GitHub repo ({repo}) as {keeper['id']}"))

    return pairs


def find_hype(entries: list[dict]) -> list[tuple[dict, list[str]]]:
    """Entries whose summary/why_it_matters contain marketing language."""
    out = []
    for e in entries:
        text = f"{e.get('summary','')} {e.get('why_it_matters','')}".lower()
        hits = [w for w in HYPE_WORDS if re.search(rf"\b{re.escape(w)}\b", text)]
        if hits:
            out.append((e, sorted(set(hits))))
    return out


def find_similar_names(entries: list[dict], threshold: float = 0.6) -> list[tuple[str, str]]:
    """Report-only: near-identical display names worth a human look."""
    out = []
    names = [(e["id"], re.sub(r"[^a-z0-9 ]", "", e["name"].lower())) for e in entries]
    for i, (id1, n1) in enumerate(names):
        for id2, n2 in names[i + 1 :]:
            a, b = set(n1.split()), set(n2.split())
            if not a or not b:
                continue
            overlap = len(a & b) / max(len(a), len(b))
            if overlap >= threshold:
                out.append((id1, id2))
    return out


def health_report(entries: list[dict], categories: list[dict], cap: int = 12) -> dict:
    """Structured snapshot of wiki health — drives HEALTH.md and the run log."""
    by_cat: dict[str, int] = defaultdict(int)
    for e in entries:
        by_cat[e["category"]] += 1

    over_cap = {
        c["name"]: by_cat.get(c["id"], 0)
        for c in categories
        if by_cat.get(c["id"], 0) > cap
    }

    verified = sorted(e.get("last_verified", "") for e in entries if e.get("last_verified"))
    sources: dict[str, int] = defaultdict(int)
    for e in entries:
        sources[e.get("source", "unknown").split(":")[0]] += 1

    return {
        "total_entries": len(entries),
        "categories": len(categories),
        "per_category": {c["name"]: by_cat.get(c["id"], 0) for c in categories},
        "over_cap": over_cap,
        "oldest_verified": verified[0] if verified else None,
        "newest_verified": verified[-1] if verified else None,
        "hype_count": len(find_hype(entries)),
        "duplicate_count": len(find_duplicates(entries)),
        "similar_name_pairs": len(find_similar_names(entries)),
        "by_source": dict(sources),
    }
