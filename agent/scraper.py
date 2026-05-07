"""
scraper.py — Prosus Regulatory Super-Agent v3
- RSS-first: verified working feeds only
- Hard 7-day recency cutoff — no old content ever
- Two-stage noise filter: explicit noise + pure funding noise
- Keyword matching with word-boundary awareness
- ai_agents mirrored to ai_landscape for dashboard compatibility
"""

import os, json, re, hashlib, requests
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
from pathlib import Path
from agent.config import (
    CATEGORY_KEYWORDS, WATCHLISTS,
    ALL_ENTITIES, AGENT_CONFIG, CATEGORIES,
)

CONTENT_DIR = Path(__file__).parent.parent / "content"
INDEX_FILE  = CONTENT_DIR / "index.json"
SYNC_FILE   = CONTENT_DIR / "sync.json"
PAGES_DIR   = CONTENT_DIR / "pages"
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
MAX_AGE_DAYS = 7

# ── VERIFIED WORKING RSS FEEDS ─────────────────────────────────────────────
RSS_SOURCES = [
    ("CMA (UK)",           "https://www.gov.uk/search/all.atom?organisations%5B%5D=competition-and-markets-authority&order=updated-newest"),
    ("TechCrunch",         "https://techcrunch.com/feed/"),
    ("MIT Tech Review",    "https://www.technologyreview.com/feed/"),
    ("VentureBeat AI",     "https://venturebeat.com/feed/"),
    ("Ars Technica",       "https://feeds.arstechnica.com/arstechnica/technology-lab"),
    ("Wired",              "https://www.wired.com/feed/rss"),
    ("Economic Times Tech","https://economictimes.indiatimes.com/tech/rssfeeds/13357270.cms"),
    ("Digital Watch",      "https://dig.watch/feed"),
    ("CompCom SA",         "https://www.compcom.co.za/feed/"),
    ("EU Digital Strategy","https://digital-strategy.ec.europa.eu/en/rss.xml"),
    ("WIPO",               "https://www.wipo.int/pressroom/en/rss.xml"),
    ("AI Now Institute",   "https://ainowinstitute.org/news/rss"),
    ("Future of Life",     "https://futureoflife.org/feed/"),
]

# ── NOISE FILTERS ──────────────────────────────────────────────────────────
EXPLICIT_NOISE = [
    "box office", "cricket match", "football match", "recipe",
    "power purchase agreement", "quarterly earnings call", "ipo price band",
    "engaging healthcare professionals", "dispute resolution in the middle east",
]

# Titles that are pure funding/biz news with no regulatory angle
FUNDING_NOISE_PATTERNS = [
    r"raises \$[\d.]+[mb]",
    r"valued at \$[\d.]+[b]",
    r"angel round",
    r"series [abcde] round",
    r"chip factory",
    r"driverless truck",
    r"lock in.*ticket",
    r"disrupt 202\d",
    r"\$[\d]+[mb] from [a-z0-9]+",
]

STRONG_REGULATORY = [
    "regulat", "privacy", "compliance", "fine", "court", "ruling",
    "ban", "merger", "antitrust", "gdpr", "lawsuit", "settle",
    "enforcement", "probe", "investigation", "penalty", "sanction",
]

# ── RELEVANT KEYWORDS (title must match at least one) ──────────────────────
RELEVANT_KWS = [
    # Regulation
    "regulat", "legislation", "policy", "directive", "enforcement",
    "fine", "penalty", "sanction", "compliance", "court", "ruling",
    "judgment", "antitrust", "competition", "merger", "acquisition", "takeover",
    # Privacy / Data
    "gdpr", "data protection", "privacy", "data breach", "personal data",
    "dpdp", "lgpd", "popia", "pdpa", "surveillance",
    # AI
    "ai", "artificial intelligence", "machine learning", "llm", "chatgpt",
    "generative", "deepfake", "agentic", "foundation model",
    # Platform
    "platform", "dsa", "dma", "digital market", "algorithm", "content moderation",
    # Fintech
    "fintech", "payment", "crypto", "stablecoin", "bnpl", "open banking",
    # Competition
    "cartel", "monopoly", "dominant", "gatekeeper",
    # IP
    "copyright", "trademark", "patent", "intellectual property",
    # Legal actions
    "lawsuit", "sue", "settle", "ban", "block", "probe", "investigate",
    # Prosus entities
    "ifood", "swiggy", "olx", "takealot", "payu", "brainly", "meesho",
    "pharmeasy", "rapido", "prosus", "naspers", "tencent",
    # Big tech (often regulatory angle)
    "apple", "google", "meta", "amazon", "microsoft", "openai", "anthropic",
    "uber", "deliveroo", "doordash",
]

# ── HELPERS ────────────────────────────────────────────────────────────────

def uid(title, date):
    return hashlib.md5((title + date).lower().encode()).hexdigest()[:10]


def fetch(url):
    try:
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=12)
        r.raise_for_status()
        return r.text
    except Exception as e:
        print(f"    [WARN] {url[:55]}: {e}")
        return ""


def parse_date(s):
    if not s:
        return ""
    # RFC 2822 (standard RSS)
    try:
        return parsedate_to_datetime(s).strftime("%Y-%m-%d")
    except Exception:
        pass
    # ISO 8601 (Atom)
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00")).strftime("%Y-%m-%d")
    except Exception:
        pass
    return s[:10] if len(s) >= 10 else ""


def is_recent(date_str):
    if not date_str:
        return False
    try:
        d = datetime.fromisoformat(date_str + "T00:00:00+00:00")
        return (datetime.now(timezone.utc) - d).days <= MAX_AGE_DAYS
    except Exception:
        return False


def has_kw(text, kws):
    t = text.lower()
    for kw in kws:
        kw = kw.lower().strip()
        if len(kw) <= 3:
            if re.search(r"\b" + re.escape(kw) + r"\b", t):
                return True
        else:
            if kw in t:
                return True
    return False


def is_noise(title):
    t = title.lower()
    if has_kw(title, EXPLICIT_NOISE):
        return True
    for pat in FUNDING_NOISE_PATTERNS:
        if re.search(pat, t):
            if not any(s in t for s in STRONG_REGULATORY):
                return True
    return False


def parse_feed(xml_text, label):
    if not xml_text:
        return []
    try:
        # Strip XML namespaces for simple element access
        xml = re.sub(r"<(\w+):", r"<\1_", xml_text)
        xml = re.sub(r"</(\w+):", r"</\1_", xml)
        xml = re.sub(r'\s+xmlns(?::\w+)?="[^"]*"', "", xml)
        root = ET.fromstring(xml)
    except Exception as e:
        print(f"    [WARN] XML parse {label}: {e}")
        return []

    items = root.findall(".//item") or root.findall(".//entry")
    out = []
    for item in items:
        def g(*tags):
            for tag in tags:
                el = item.find(tag)
                if el is not None and el.text:
                    return el.text.strip()
            return ""

        title = g("title")
        if len(title) < 15:
            continue

        date = parse_date(g("pubDate", "published", "updated", "dc_date"))
        if not is_recent(date):
            continue

        if is_noise(title):
            continue

        if not has_kw(title, RELEVANT_KWS):
            continue

        body = re.sub(r"<[^>]+>", " ", g("description", "summary", "content")).strip()
        body = re.sub(r"\s+", " ", body)[:600]

        link_el = item.find("link")
        url = ""
        if link_el is not None:
            url = link_el.get("href", "") or (link_el.text or "").strip()

        out.append({
            "id":           uid(title, date),
            "title":        title,
            "date":         date,
            "published_at": date + "T00:00:00Z",
            "source":       label,
            "url":          url,
            "body":         body or title,
            "tags":         [],
            "entity_match": [],
            "watchlist_hits": [],
            "prosus_lens":  "",
            "category":     "",
            "scope_path":   "",
        })
    return out


# ── CLASSIFICATION ─────────────────────────────────────────────────────────

def categorise(a):
    text = (a["title"] + " " + a["body"]).lower()
    rules = [
        ("competition",        ["antitrust", "competition", "merger", "cartel", "dominant", "gatekeeper", "cma", "m&a"]),
        ("privacy",            ["gdpr", "privacy", "data protection", "data breach", "personal data", "dpdp", "lgpd", "popia", "surveillance"]),
        ("ai_agents",          ["artificial intelligence", "ai act", "machine learning", "llm", "deepfake", "agentic", "generative", "foundation model", "chatgpt"]),
        ("ip",                 ["copyright", "trademark", "patent", "intellectual property"]),
        ("fintech",            ["fintech", "payment", "crypto", "stablecoin", "bnpl", "open banking"]),
        ("platform_liability", ["platform", "dsa", "dma", "digital market", "content moderation"]),
        ("gig_economy",        ["gig", "worker", "labour", "labor", "gig economy", "rapido", "swiggy", "deliveroo"]),
        ("consumer_protection",["consumer", "misleading", "unfair", "deceptive", "scam", "fraud"]),
    ]
    for cat, kws in rules:
        if any(kw in text for kw in kws):
            return cat
    return "regulatory"


def infer_tags(a):
    text = (a["title"] + " " + a["body"]).lower()
    tag_map = {
        "GDPR": ["gdpr"], "AI Act": ["ai act"], "DSA": ["digital services act", " dsa "],
        "DMA": ["digital markets act", " dma "], "Fine": ["fine", "penalty", "sanction"],
        "Court": ["court", "judgment", "ruling", "appeal"], "Merger": ["merger", "acquisition"],
        "Enforcement": ["enforcement", "investigation", "proceeding"],
        "India": ["india", " cci ", "meity", "dpdp"], "Brazil": ["brazil", "cade", "lgpd"],
        "UK": [" uk ", " cma ", "ofcom"], "EU": [" eu ", "european commission", "edpb"],
        "US": ["ftc", " doj ", "federal trade"], "South Africa": ["south africa", "popia"],
        "Singapore": ["singapore", "pdpc"], "IP": ["copyright", "trademark", "patent"],
        "AI": ["artificial intelligence", "llm", "generative", "deepfake"],
        "Fintech": ["fintech", "crypto", "bnpl"], "Competition": ["antitrust", "cartel"],
    }
    return [t for t, kws in tag_map.items() if any(kw in text for kw in kws)][:6]


def match_entities(a):
    text = (a["title"] + " " + a["body"]).lower()
    return [e for e in ALL_ENTITIES if e.lower() in text]


def hit_watchlists(a):
    text = (a["title"] + " " + a["body"]).lower()
    return [wl for wl, kws in WATCHLISTS.items() if any(kw.lower() in text for kw in kws)]


def scope_path(a):
    if a["entity_match"]:
        return "A"
    text = (a["title"] + " " + a["body"]).lower()
    if any(j in text for j in ["eu", "uk", "india", "brazil", "south africa", "netherlands", "singapore", "nigeria"]):
        return "B"
    return "C"


def score(a):
    s = {"A": 10, "B": 5, "C": 0}.get(a.get("scope_path", "C"), 0)
    s += len(a.get("watchlist_hits", [])) * 4
    s += len(a.get("entity_match", [])) * 3
    s += len(a.get("tags", [])) * 0.5
    if a.get("prosus_lens"):
        s += 2
    try:
        days = (datetime.now(timezone.utc) - datetime.fromisoformat(a["date"] + "T00:00:00+00:00")).days
        s += max(0, 7 - days) * 2  # recency bonus: today = +14, 7 days ago = 0
    except Exception:
        pass
    return s


def prosus_lens(a):
    if not OPENAI_API_KEY:
        return ""
    try:
        ctx = ", ".join(a["entity_match"]) if a["entity_match"] else "the Prosus portfolio"
        prompt = (
            f"Prosus is a global technology investor (iFood, Swiggy, OLX, PayU, Brainly, "
            f"GoStudent, Meesho, PharmEasy, Rapido, eMag, Takealot, etc) headquartered in Amsterdam.\n\n"
            f"Title: {a['title']}\nSummary: {a['body'][:400]}\n"
            f"Category: {a['category']}\nDirect entity matches: {ctx}\n\n"
            "Write 2-3 sentences on what this means specifically for Prosus and its portfolio. "
            "Name affected entities. Be concrete on compliance, strategic, or operational implications. "
            "Do not start with 'This development'."
        )
        r = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"},
            json={"model": "gpt-4o-mini", "messages": [{"role": "user", "content": prompt}],
                  "max_tokens": 180, "temperature": 0.3},
            timeout=30,
        )
        return r.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"    [WARN] OpenAI: {e}")
        return ""


def deduplicate(articles):
    seen_ids, seen_titles, out = set(), set(), []
    for a in articles:
        norm = re.sub(r"\s+", " ", a["title"].lower().strip())[:80]
        if a["id"] in seen_ids or norm in seen_titles:
            continue
        seen_ids.add(a["id"])
        seen_titles.add(norm)
        out.append(a)
    return out


# ── MAIN ───────────────────────────────────────────────────────────────────

def run():
    now = datetime.now(timezone.utc)
    cutoff = (now - timedelta(days=MAX_AGE_DAYS)).strftime("%Y-%m-%d")
    print(f"[{now.strftime('%Y-%m-%d %H:%M')} UTC] Prosus Reg Super-Agent v3")
    print(f"  Recency cutoff: {cutoff} → today only")

    raw = []
    for label, url in RSS_SOURCES:
        print(f"  Fetching: {label} ...")
        arts = parse_feed(fetch(url), label)
        print(f"    → {len(arts)} qualifying")
        raw.extend(arts)

    print(f"\n  Total before dedup: {len(raw)}")
    raw = deduplicate(raw)
    print(f"  After dedup:        {len(raw)}")

    # Enrich
    categorised = {cat: [] for cat in CATEGORIES}
    for a in raw:
        a["category"]       = categorise(a)
        a["tags"]           = infer_tags(a)
        a["entity_match"]   = match_entities(a)
        a["watchlist_hits"] = hit_watchlists(a)
        a["scope_path"]     = scope_path(a)
        if a["scope_path"] in ("A", "B") and OPENAI_API_KEY:
            a["prosus_lens"] = prosus_lens(a)
        if a["category"] in categorised:
            categorised[a["category"]].append(a)
        else:
            categorised.setdefault(a["category"], []).append(a)

    # Sort + cap per category
    max_per = AGENT_CONFIG.get("max_per_category", 20)
    for cat in categorised:
        categorised[cat] = sorted(categorised[cat], key=score, reverse=True)[:max_per]

    # Mirror ai_agents → ai_landscape for dashboard pill compatibility
    categorised["ai_landscape"] = categorised.get("ai_agents", [])

    all_arts = [a for k, v in categorised.items() for a in v if k != "ai_landscape"]
    trending = sorted(all_arts, key=score, reverse=True)[:AGENT_CONFIG.get("trending_count", 10)]
    flash = [
        {"id": a["id"], "title": a["title"], "date": a["date"], "source": a["source"],
         "url": a["url"], "watchlist_hits": a["watchlist_hits"],
         "entity_match": a["entity_match"], "prosus_lens": a["prosus_lens"]}
        for a in all_arts
        if len(a.get("watchlist_hits", [])) >= 2 or (a.get("entity_match") and a.get("watchlist_hits"))
    ][:10]

    # Save markdown pages
    PAGES_DIR.mkdir(parents=True, exist_ok=True)
    for arts in categorised.values():
        for a in arts:
            slug = re.sub(r"[^a-z0-9]+", "-", a["title"].lower())[:60]
            (PAGES_DIR / f"{a['date']}-{slug}.md").write_text(
                f"---\ntitle: \"{a['title']}\"\ndate: {a['date']}\n"
                f"source: {a['source']}\ncategory: {a['category']}\n"
                f"scope: {a['scope_path']}\ntags: {a['tags']}\nurl: {a['url']}\n---\n\n"
                f"{a['body']}\n\n{a.get('prosus_lens', '')}\n",
                encoding="utf-8",
            )

    total = sum(len(v) for k, v in categorised.items() if k != "ai_landscape")
    index = {
        "generated_at":   now.isoformat(),
        "total_articles": total,
        "recency_days":   MAX_AGE_DAYS,
        "trending":       trending,
        "flash_alerts":   flash,
        **categorised,
    }

    CONTENT_DIR.mkdir(parents=True, exist_ok=True)
    INDEX_FILE.write_text(json.dumps(index, indent=2, ensure_ascii=False), encoding="utf-8")
    SYNC_FILE.write_text(json.dumps({
        "last_sync":      now.isoformat(),
        "total_articles": total,
        "flash_alerts":   len(flash),
        "recency_days":   MAX_AGE_DAYS,
        "sources":        len(RSS_SOURCES),
        "by_category":    {k: len(v) for k, v in categorised.items() if k != "ai_landscape"},
    }, indent=2), encoding="utf-8")

    print(f"\n✓ Done: {total} articles | {len(flash)} flash alerts | {len(trending)} trending")
    for cat, arts in sorted(categorised.items(), key=lambda x: -len(x[1])):
        if cat != "ai_landscape" and arts:
            print(f"  {cat}: {len(arts)}")


if __name__ == "__main__":
    run()
