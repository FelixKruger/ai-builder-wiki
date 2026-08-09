#!/usr/bin/env python3
"""
The part of the curator that produces something worth reading.

A list of 147 tools with one-line blurbs is a directory — search already does
that better. What a builder actually needs is the judgement a directory can't
give: *which* of these twelve coding agents fits my situation, and what will
bite me. The site is called a Field Guide; this module is what earns the name.

Two actions, one of each per run:

  write_guide()   — a "how to choose" guide for one category, rotating so every
                    category is rewritten every couple of weeks as its entries
                    change. Comparison and synthesis over tools already vetted
                    and in the wiki, never a claim invented about a new tool.
  rewrite_entry() — take one weak entry (marketing language, or vague copy that
                    could describe any tool in its category) and make it
                    concrete and comparative.

Both are deliberately conservative about facts: they reason over entries the
wiki already holds and are instructed away from volatile specifics (prices,
benchmark numbers, version strings) that rot within weeks and can't be
verified by an HTTP check.
"""
from __future__ import annotations

import json
from datetime import date, datetime, timezone

import llm
import maintenance

GUIDE_MAX_AGE_DAYS = 14
GUIDE_SYSTEM = (
    "You write for working software engineers who ship AI products. You are "
    "blunt, specific, and comparative. You never use marketing language. You "
    "would rather say 'most teams don't need this' than pad a recommendation."
)


def _days_since(iso: str | None) -> int:
    if not iso:
        return 10_000
    try:
        d = datetime.strptime(iso[:10], "%Y-%m-%d").date()
    except ValueError:
        return 10_000
    return (date.today() - d).days


def pick_guide_target(categories: list[dict], entries: list[dict]) -> dict | None:
    """
    Category whose guide is most overdue. Missing guides first, then oldest.
    Skips categories too thin to compare meaningfully.
    """
    counts: dict[str, int] = {}
    for e in entries:
        counts[e["category"]] = counts.get(e["category"], 0) + 1

    candidates = [c for c in categories if counts.get(c["id"], 0) >= 3]
    if not candidates:
        return None

    def staleness(c: dict) -> int:
        return _days_since((c.get("guide") or {}).get("updated"))

    best = max(candidates, key=staleness)
    return best if staleness(best) >= GUIDE_MAX_AGE_DAYS else None


def write_guide(category: dict, entries: list[dict]) -> tuple[dict, str] | None:
    """Write a decision guide for one category. Returns (guide, model) or None."""
    members = [e for e in entries if e["category"] == category["id"]]
    if len(members) < 3:
        return None

    listing = [
        {"name": e["name"], "summary": e["summary"], "why_it_matters": e["why_it_matters"]}
        for e in members
    ]

    prompt = f"""Write a "how to choose" guide for the **{category['name']}** section of a
field guide for AI builders.

The reader arrives at this section thinking: "{category.get('intent', category['name'])}"

These are the tools in the section — the ONLY tools you may recommend:

{json.dumps(listing, indent=2)}

Write 120-200 words of prose that helps someone pick. Requirements:

- Open with the default: which tool most people should reach for first, and why.
- Then the forks that actually matter — the two or three situations where a
  different tool is the right answer, and which one. Be concrete about the
  situation ("if your codebase is a large monorepo", "if you can't send code
  to a third party"), not vague ("depending on your needs").
- Name a real trade-off. Something a vendor page would not tell you.
- If several tools here genuinely overlap, say so plainly rather than
  inventing a distinction.

Hard rules:
- Only mention tools from the list above. Never invent one.
- No prices, version numbers, benchmark scores, or funding news — they go
  stale and cannot be verified.
- No marketing adjectives. Banned: {', '.join(maintenance.HYPE_WORDS[:12])}.
- Plain prose. No headings, no bullet lists, no bold.
- Do not open with "When it comes to" or "In the world of".

Return ONLY JSON: {{"guide": "the prose"}}"""

    obj, model = llm.complete_json(
        prompt, system=GUIDE_SYSTEM, max_tokens=1200, temperature=0.4
    )
    body = (obj.get("guide") or "").strip()
    if len(body) < 120:
        return None

    known = {e["name"].lower() for e in members}
    hype = [w for w in maintenance.HYPE_WORDS if w in body.lower()]
    if hype:
        print(f"    guide rejected: marketing language {hype}")
        return None

    return (
        {
            "body": body,
            "updated": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "model": model,
            "covers": sorted(known),
        },
        model,
    )


def pick_weak_entry(entries: list[dict], categories: list[dict]) -> dict | None:
    """
    The entry most in need of rewriting: marketing language first, then the
    vaguest copy (shortest "why it matters", which is where hedging shows up).
    """
    hyped = [e for e, _ in maintenance.find_hype(entries)]
    if hyped:
        return min(hyped, key=lambda e: len(e.get("why_it_matters", "")))

    scored = sorted(entries, key=lambda e: len(e.get("why_it_matters", "")))
    return scored[0] if scored else None


def rewrite_entry(entry: dict, entries: list[dict], categories: list[dict]) -> tuple[dict, str] | None:
    """Sharpen one entry's copy. Returns (patch, model) or None."""
    cat = next((c for c in categories if c["id"] == entry["category"]), None)
    if not cat:
        return None

    siblings = [
        {"name": e["name"], "summary": e["summary"]}
        for e in entries
        if e["category"] == entry["category"] and e["id"] != entry["id"]
    ][:12]

    prompt = f"""Sharpen one entry in a field guide for AI builders.

The entry, as it stands:
{json.dumps({k: entry[k] for k in ('name', 'url', 'summary', 'why_it_matters')}, indent=2)}

It sits in the "{cat['name']}" section alongside:
{json.dumps(siblings, indent=2)}

Rewrite `summary` and `why_it_matters`.

- summary: ONE sentence, under 25 words, purely factual — what the tool is.
- why_it_matters: one or two sentences answering "why would I pick this over
  the others in this section?". Name the specific alternative it beats and the
  specific situation where it wins. If its real edge is that it is the boring,
  well-supported default, say that.

Hard rules:
- Do not invent capabilities. If you are unsure a feature exists, leave it out.
- No prices, version numbers, or benchmark scores.
- No marketing adjectives. Banned: {', '.join(maintenance.HYPE_WORDS[:12])}.
- If the current copy is already concrete and comparative, return it unchanged.

Return ONLY JSON: {{"summary": "...", "why_it_matters": "...", "changed": true/false}}"""

    obj, model = llm.complete_json(
        prompt, system=GUIDE_SYSTEM, max_tokens=800, temperature=0.3
    )

    summary = (obj.get("summary") or "").strip()
    why = (obj.get("why_it_matters") or "").strip()
    if not summary or not why:
        return None
    if not obj.get("changed", True):
        return None
    if summary == entry["summary"] and why == entry["why_it_matters"]:
        return None

    combined = f"{summary} {why}".lower()
    hype = [w for w in maintenance.HYPE_WORDS if w in combined]
    if hype:
        print(f"    rewrite rejected: marketing language {hype}")
        return None
    if len(summary) > 220:
        print("    rewrite rejected: summary too long")
        return None

    return {"summary": summary, "why_it_matters": why}, model
