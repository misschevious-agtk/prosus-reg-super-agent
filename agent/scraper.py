"""
scraper.py
Fetches regulatory news from 30+ sources, categorises articles,
runs Prosus-lens analysis via OpenAI, and writes content/index.json.
"""

import os
import json
import re
import hashlib
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone
from pathlib import Path
from agent.config import (
    SOURCES, CATEGORY_KEYWORDS, WATCHLISTS,
    ALL_ENTITIES, PORTFOLIO, AGENT_CONFIG, CATEGORIES,
)

CONTENT_DIR = Path(__file__).parent.parent / "content"
INDEX_FILE  = CONTENT_DIR / "index.json"
SYNC_FILE   = CONTENT_DIR / "sync.json"
PAGES_DIR   = CONTENT_DIR / "pages"

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")

# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

def uid(article: dict) -> str:
    """Stable ID from title + date."""
    raw = (article.get("title", "") + article.get("date", "")).lower()
    return hashlib.md5(raw.encode()).hexdigest()[:10]


def fetch_html(url: str) -> str:
    try:
        headers = {"User-Agent": AGENT_CONFIG["user_agent"]}
        r = requests.get(url, headers=headers, timeout=AGENT_CONFIG["timeout"])
        r.raise_for_status()
        return r.text
    except Exception as e:
        print(f"  [WARN] Could not fetch {url}: {e}")
        return ""


def extract_articles_from_html(html: str, source_label: str) -> list[dict]:
    """Generic extraction: grab all <a> tags with meaningful text near a date."""
    soup = BeautifulSoup(html, "html.parser")
    results = []
    seen = set()

    for a in soup.find_all("a", href=True):
        title = a.get_text(strip=True)
        if len(title) < 30 or len(title) > 300:
            continue
        if title in seen:
            continue
        seen.add(title)

        # Look for a nearby date string
        parent_text = ""
        for parent in a.parents:
            parent_text = parent.get_text(" ", strip=True)
            if len(parent_text) > 50:
                break

        date = extract_date(parent_text) or datetime.now(timezone.utc).strftime("%Y-%m-%d")
        href = a["href"]
        if not href.startswith("http"):
            href = ""

        # Build a snippet from surrounding text
        body = parent_text[:600] if parent_text else title

        results.append({
            "id": uid({"title": title, "date": date}),
            "title": title,
            "body": body,
            "date": date,
            "published_at": date + "T00:00:00Z",
            "source": source_label,
            "url": href,
            "tags": [],
            "entity_match": [],
            "watchlist_hits": [],
            "prosus_lens": "",
            "category": "",
            "scope_path": "",
        })

    return results[:40]  # cap per source


def extract_date(text: str) -> str | None:
    patterns = [
        r"\b(\d{1,2})\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+(\d{4})\b",
        r"\b(\d{4})-(\d{2})-(\d{2})\b",
        r"\b(\d{1,2})/(\d{1,2})/(\d{4})\b",
    ]
    months = {"jan":1,"feb":2,"mar":3,"apr":4,"may":5,"jun":6,
              "jul":7,"aug":8,"sep":9,"oct":10,"nov":11,"dec":12}
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            try:
                g = m.groups()
                if len(g) == 3:
                    if g[1].lower()[:3] in months:
                        d = datetime(int(g[2]), months[g[1].lower()[:3]], int(g[0]))
                    elif len(g[0]) == 4:
                        d = datetime(int(g[0]), int(g[1]), int(g[2]))
                    else:
                        d = datetime(int(g[2]), int(g[1]), int(g[0]))
                    return d.strftime("%Y-%m-%d")
            except Exception:
                continue
    return None


# ─────────────────────────────────────────────
# CLASSIFICATION
# ─────────────────────────────────────────────

def categorise(article: dict) -> str:
    text = (article["title"] + " " + article["body"]).lower()
    scores = {cat: 0 for cat in CATEGORIES}
    for cat, keywords in CATEGORY_KEYWORDS.items():
        for kw in keywords:
            if kw.lower() in text:
                scores[cat] += 1
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "regulatory"


def infer_tags(article: dict) -> list[str]:
    text = (article["title"] + " " + article["body"]).lower()
    tags = []
    tag_map = {
        "GDPR": ["gdpr", "data protection regulation"],
        "AI Act": ["ai act", "ai regulation"],
        "DSA": ["digital services act", "dsa"],
        "DMA": ["digital markets act", "dma"],
        "Fine": ["fine", "penalty", "sanction", "€", "$", "£"],
        "Court": ["court", "judgment", "ruling", "appeal", "cjeu", "tribunal"],
        "Consultation": ["consultation", "public comment", "draft regulation"],
        "Enforcement": ["enforcement", "investigation", "proceeding", "dawn raid"],
        "India": ["india", "cci", "meity", "trai"],
        "Brazil": ["brazil", "cade", "anpd", "lgpd"],
        "UK": ["uk", "ico", "cma", "ofcom"],
        "EU": ["eu", "european", "edpb", "ec ", "commission"],
        "US": ["ftc", "doj", "united states", "federal"],
        "South Africa": ["south africa", "cgso", "popia", "compcom"],
        "Singapore": ["singapore", "pdpc", "imda"],
        "IP": ["copyright", "trademark", "patent", "intellectual property"],
        "AI Landscape": ["artificial intelligence", "llm", "generative ai", "deepfake", "agentic"],
        "Fintech": ["fintech", "payments", "psd", "bnpl", "crypto"],
        "Competition": ["antitrust", "cartel", "merger", "dominance", "collusion"],
    }
    for tag, kws in tag_map.items():
        if any(kw in text for kw in kws):
            tags.append(tag)
    return tags[:6]


def match_entities(article: dict) -> list[str]:
    text = (article["title"] + " " + article["body"]).lower()
    return [e for e in ALL_ENTITIES if e.lower() in text]


def hit_watchlists(article: dict) -> list[str]:
    text = (article["title"] + " " + article["body"]).lower()
    hits = []
    for wl_name, keywords in WATCHLISTS.items():
        if any(kw.lower() in text for kw in keywords):
            hits.append(wl_name)
    return hits


def scope_path(article: dict) -> str:
    """A = direct entity hit, B = jurisdiction hit, C = general relevance."""
    if article["entity_match"]:
        return "A"
    text = (article["title"] + " " + article["body"]).lower()
    jurisdiction_terms = ["eu", "uk", "india", "brazil", "south africa",
                          "netherlands", "singapore", "nigeria", "kenya"]
    if any(j in text for j in jurisdiction_terms):
        return "B"
    return "C"


# ─────────────────────────────────────────────
# PROSUS LENS — AI Analysis
# ─────────────────────────────────────────────

def prosus_lens(article: dict) -> str:
    """Call OpenAI to generate a Prosus-specific read-across paragraph."""
    if not OPENAI_API_KEY:
        return ""
    try:
        entity_context = ", ".join(article["entity_match"]) if article["entity_match"] else "the broader Prosus portfolio"
        prompt = f"""You are the Group IP Lead, Digital & Regulatory at Prosus — a global consumer internet group.
Prosus portfolio includes: iFood, Swiggy (food delivery), OLX, Takealot, eMAG (classifieds/ecommerce),
PayU, Remitly (fintech), Brainly, GoStudent, Eruditus (edtech), PharmEasy (healthtech),
Ema, Brainfish, Advolve.AI (AI enterprise), and Naspers/Tencent (parent).

Regulatory development:
Title: {article['title']}
Summary: {article['body'][:500]}
Date: {article['date']}
Category: {article['category']}
Direct entity matches: {entity_context}

Write 2–3 sentences: What does this mean specifically for Prosus and its portfolio? 
Focus on concrete operational, compliance, or strategic implications. Be specific — name the affected entities.
Do not start with "This development" or "This article"."""

        r = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": AGENT_CONFIG["openai_model"],
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 180,
                "temperature": 0.3,
            },
            timeout=30,
        )
        return r.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"  [WARN] OpenAI call failed: {e}")
        return ""


# ─────────────────────────────────────────────
# DEDUPLICATION
# ─────────────────────────────────────────────

def deduplicate(articles: list[dict]) -> list[dict]:
    seen_ids = set()
    seen_titles = set()
    out = []
    for a in articles:
        norm_title = re.sub(r"\s+", " ", a["title"].lower().strip())
        if a["id"] in seen_ids or norm_title in seen_titles:
            continue
        seen_ids.add(a["id"])
        seen_titles.add(norm_title)
        out.append(a)
    return out


# ─────────────────────────────────────────────
# TRENDING SCORER
# ─────────────────────────────────────────────

def score_trending(article: dict) -> float:
    score = 0.0
    if article["scope_path"] == "A":
        score += 10
    elif article["scope_path"] == "B":
        score += 5
    score += len(article["watchlist_hits"]) * 4
    score += len(article["entity_match"]) * 3
    score += len(article["tags"]) * 0.5
    if article.get("prosus_lens"):
        score += 2
    # Recency bonus
    try:
        days_old = (datetime.now() - datetime.fromisoformat(article["date"])).days
        score += max(0, 10 - days_old)
    except Exception:
        pass
    return score


def select_trending(categorised: dict, n: int = 8) -> list[dict]:
    all_articles = [a for arts in categorised.values() for a in arts]
    scored = sorted(all_articles, key=score_trending, reverse=True)
    return scored[:n]


# ─────────────────────────────────────────────
# SAVE MARKDOWN
# ─────────────────────────────────────────────

def save_markdown(article: dict) -> None:
    PAGES_DIR.mkdir(parents=True, exist_ok=True)
    slug = re.sub(r"[^a-z0-9]+", "-", article["title"].lower())[:60]
    path = PAGES_DIR / f"{article['date']}-{slug}.md"
    tags_str = ", ".join(article["tags"])
    entities_str = ", ".join(article["entity_match"]) if article["entity_match"] else "None"
    watchlists_str = ", ".join(article["watchlist_hits"]) if article["watchlist_hits"] else "None"
    path.write_text(
        f"""---
title: "{article['title']}"
date: {article['date']}
source: {article['source']}
category: {article['category']}
scope_path: {article['scope_path']}
tags: [{tags_str}]
entity_match: [{entities_str}]
watchlist_hits: [{watchlists_str}]
url: {article['url']}
---

## Summary

{article['body']}

## Prosus Read-Across

{article['prosus_lens'] or '_No AI analysis available (OPENAI_API_KEY not set)_'}
""",
        encoding="utf-8",
    )


# ─────────────────────────────────────────────
# FLASH ALERTS
# ─────────────────────────────────────────────

def build_flash_alerts(all_articles: list[dict]) -> list[dict]:
    """Articles that hit 2+ watchlists or directly name a portfolio entity."""
    alerts = []
    for a in all_articles:
        if len(a["watchlist_hits"]) >= 2 or (a["entity_match"] and a["watchlist_hits"]):
            alerts.append({
                "id": a["id"],
                "title": a["title"],
                "date": a["date"],
                "source": a["source"],
                "url": a["url"],
                "watchlist_hits": a["watchlist_hits"],
                "entity_match": a["entity_match"],
                "prosus_lens": a["prosus_lens"],
            })
    return alerts[:10]


# ─────────────────────────────────────────────
# MAIN RUN
# ─────────────────────────────────────────────

def run():
    print(f"[{datetime.now(timezone.utc).isoformat()}] Prosus Reg Super-Agent starting...")

    raw_articles = []
    for source in SOURCES:
        print(f"  Fetching: {source['label']} ...")
        html = fetch_html(source["url"])
        if not html:
            continue
        articles = extract_articles_from_html(html, source["label"])
        print(f"    → {len(articles)} raw items")
        raw_articles.extend(articles)

    print(f"\n  Total raw: {len(raw_articles)}")
    raw_articles = deduplicate(raw_articles)
    print(f"  After dedup: {len(raw_articles)}")

    # Filter out empty / noise
    raw_articles = [a for a in raw_articles if len(a.get("body", "")) > 40]

    # Classify & enrich
    categorised = {cat: [] for cat in CATEGORIES}
    for article in raw_articles:
        article["category"] = categorise(article)
        article["tags"] = infer_tags(article)
        article["entity_match"] = match_entities(article)
        article["watchlist_hits"] = hit_watchlists(article)
        article["scope_path"] = scope_path(article)
        # Only call OpenAI for Scope A/B articles to save cost
        if article["scope_path"] in ("A", "B") and OPENAI_API_KEY:
            article["prosus_lens"] = prosus_lens(article)
        categorised[article["category"]].append(article)

    # Cap per category
    max_per = AGENT_CONFIG["max_per_category"]
    for cat in categorised:
        categorised[cat] = sorted(
            categorised[cat], key=score_trending, reverse=True
        )[:max_per]

    trending = select_trending(categorised, n=AGENT_CONFIG["trending_count"])
    flash_alerts = build_flash_alerts(
        [a for arts in categorised.values() for a in arts]
    )

    # Save markdown pages
    for arts in categorised.values():
        for article in arts:
            save_markdown(article)

    # Build index
    total = sum(len(v) for v in categorised.values())
    index = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_articles": total,
        "trending": trending,
        "flash_alerts": flash_alerts,
        **categorised,
    }

    CONTENT_DIR.mkdir(parents=True, exist_ok=True)
    INDEX_FILE.write_text(json.dumps(index, indent=2, ensure_ascii=False), encoding="utf-8")

    sync_summary = {
        "last_sync": datetime.now(timezone.utc).isoformat(),
        "total_articles": total,
        "flash_alerts": len(flash_alerts),
        "by_category": {cat: len(arts) for cat, arts in categorised.items()},
        "sources_attempted": len(SOURCES),
    }
    SYNC_FILE.write_text(json.dumps(sync_summary, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"\n[DONE] {total} articles indexed across {len(SOURCES)} sources.")
    print(f"       {len(flash_alerts)} Flash Alerts generated.")
    print(f"       Trending: {len(trending)} items.")


if __name__ == "__main__":
    run()
