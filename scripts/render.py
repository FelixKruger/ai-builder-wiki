#!/usr/bin/env python3
"""Render entries.json -> index.html, feed.xml, README's auto-section, and per-entry OG cards."""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from email.utils import format_datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "entries.json"
TEMPLATES = ROOT / "templates"
OUT_HTML = ROOT / "index.html"
OUT_FEED = ROOT / "feed.xml"
OUT_README = ROOT / "README.md"
OG_DIR = ROOT / "static" / "og"
RECENT_LIMIT = 8


def load_data() -> dict:
    with DATA.open(encoding="utf-8") as f:
        return json.load(f)


def build_env() -> Environment:
    return Environment(
        loader=FileSystemLoader(str(TEMPLATES)),
        autoescape=select_autoescape(["html", "xml"]),
        trim_blocks=False,
        lstrip_blocks=False,
    )


def render_site(data: dict) -> None:
    env = build_env()
    site = data["site"]
    categories = data["categories"]
    entries = data["entries"]

    by_category: dict[str, list] = {c["id"]: [] for c in categories}
    for e in entries:
        if e["category"] in by_category:
            by_category[e["category"]].append(e)

    counts = {cid: len(items) for cid, items in by_category.items()}

    recent_sorted = sorted(entries, key=lambda e: e.get("added", ""), reverse=True)
    recent = recent_sorted[:RECENT_LIMIT]
    for e in recent:
        added = e.get("added", "")
        try:
            dt = datetime.strptime(added, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            e["added_rfc"] = format_datetime(dt)
        except ValueError:
            e["added_rfc"] = format_datetime(datetime.now(timezone.utc))

    now = datetime.now(timezone.utc)
    ctx = {
        "site": site,
        "categories": categories,
        "entries": entries,
        "by_category": by_category,
        "counts": counts,
        "recent": recent,
        "generated_at": now.isoformat(),
        "generated_at_human": now.strftime("%Y-%m-%d"),
        "generated_at_rfc": format_datetime(now),
    }

    OUT_HTML.write_text(env.get_template("wiki.html.j2").render(**ctx), encoding="utf-8")
    OUT_FEED.write_text(env.get_template("feed.xml.j2").render(**ctx), encoding="utf-8")
    update_readme(env, ctx)
    render_og_cards(env, data)
    print(f"Rendered {len(entries)} entries across {len(categories)} categories.")


def update_readme(env: Environment, ctx: dict) -> None:
    """Either rewrite README.md from template or splice the auto-section into existing README."""
    rendered = env.get_template("readme.md.j2").render(**ctx)
    if not OUT_README.exists() or "<!-- RECENTLY_ADDED:START -->" not in OUT_README.read_text(encoding="utf-8"):
        OUT_README.write_text(rendered, encoding="utf-8")
        return
    existing = OUT_README.read_text(encoding="utf-8")
    new_block = re.search(
        r"<!-- RECENTLY_ADDED:START -->.*?<!-- RECENTLY_ADDED:END -->",
        rendered,
        re.DOTALL,
    ).group(0)
    spliced = re.sub(
        r"<!-- RECENTLY_ADDED:START -->.*?<!-- RECENTLY_ADDED:END -->",
        new_block,
        existing,
        flags=re.DOTALL,
    )
    OUT_README.write_text(spliced, encoding="utf-8")


def render_og_cards(env: Environment, data: dict) -> None:
    OG_DIR.mkdir(parents=True, exist_ok=True)
    cat_names = {c["id"]: c["name"] for c in data["categories"]}
    site_title = data["site"]["title"]
    base_url = data["site"]["base_url"]
    template = env.get_template("og-card.svg.j2")

    have_cairo = False
    try:
        import cairosvg  # type: ignore
        have_cairo = True
    except Exception as exc:
        print(f"  cairosvg unavailable, skipping PNGs: {exc}", file=sys.stderr)

    for e in data["entries"]:
        svg = template.render(
            site_title=site_title,
            name=e["name"],
            category_name=cat_names.get(e["category"], ""),
            summary=e["summary"],
            last_verified=e["last_verified"],
            base_url=base_url.rstrip("/").replace("https://", ""),
        )
        svg_path = OG_DIR / f"{e['id']}.svg"
        svg_path.write_text(svg, encoding="utf-8")
        if have_cairo:
            try:
                cairosvg.svg2png(bytestring=svg.encode(), write_to=str(OG_DIR / f"{e['id']}.png"), output_width=1200, output_height=630)
            except Exception as exc:
                print(f"  OG PNG failed for {e['id']}: {exc}", file=sys.stderr)

    # Index OG card
    index_svg = template.render(
        site_title=site_title,
        name=site_title,
        category_name=data["site"]["tagline"],
        summary=f"{len(data['entries'])} entries · curated daily by an AI agent",
        last_verified=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        base_url=base_url.rstrip("/").replace("https://", ""),
    )
    (OG_DIR / "index.svg").write_text(index_svg, encoding="utf-8")
    if have_cairo:
        try:
            cairosvg.svg2png(bytestring=index_svg.encode(), write_to=str(OG_DIR / "index.png"), output_width=1200, output_height=630)
        except Exception as exc:
            print(f"  OG PNG failed for index: {exc}", file=sys.stderr)


def main() -> int:
    data = load_data()
    render_site(data)
    return 0


if __name__ == "__main__":
    sys.exit(main())
