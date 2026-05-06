"""
scraper.py — Prosus Regulatory Super-Agent v3
- RSS-first: clean, structured, date-stamped feeds only
- Hard 7-day recency filter: NO old content ever
- Title keyword gate: article title must contain a regulatory keyword
- ai_agents mirrored to ai_landscape for dashboard compatibility
"""

import os, json, re, hashlib, requests
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from pathlib import Path
from agent.config import (
    SOURCES, CATEGORY_KEYWORDS, WATCHLISTS,
    ALL_ENTITIES, AGENT_CONFIG, CATEGORIES,
)

CONTENT_DIR = Path(__file__).parent.parent / "content"
INDEX_FILE  = CONTENT_DIR / "index.json"
SYNC_FILE   = CONTENT_DIR / "sync.json"
PAGES_DIR   = CONTENT_DIR / "pages"
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
MAX_AGE_DAYS = 7

RSS_SOURCES = [
    {"label": "European Commission",  "url": "https://ec.europa.eu/commission/presscorner/api/rss"},
    {"label": "EDPB",                 "url": "https://www.edpb.europa.eu/rss_en"},
    {"label": "ICO (UK)",             "url": "https://ico.org.uk/about-the-ico/media-centre/news-and-blogs/feed/"},
    {"label": "CMA (UK)",             "url": "https://www.gov.uk/search/all.atom?organisations%5B%5D=competition-and-markets-authority&order=updated-newest"},
    {"label": "Ofcom (UK)",           "url": "https://www.ofcom.org.uk/rss/news"},
    {"label": "FTC (US)",             "url": "https://www.ftc.gov/feeds/press-releases.xml"},
    {"label": "DOJ Antitrust (US)",   "url": "https://www.justice.gov/feeds/atr/news.xml"},
    {"label": "MAS (Singapore)",      "url": "https://www.mas.gov.sg/news/rss"},
    {"label": "PDPC (Singapore)",     "url": "https://www.pdpc.gov.sg/rss/media-releases"},
    {"label": "IAPP",                 "url": "https://iapp.org/feed/"},
    {"label": "TechCrunch Policy",    "url": "https://techcrunch.com/category/policy/feed/"},
    {"label": "The Verge Policy",     "url": "https://www.theverge.com/rss/policy/index.xml"},
    {"label": "MIT Tech Review AI",   "url": "https://www.technologyreview.com/feed/"},
    {"label": "GCR Competition",      "url": "https://globalcompetitionreview.com/rss"},
    {"label": "WIPO",                 "url": "https://www.wipo.int/pressroom/en/rss/news.xml"},
    {"label": "Digital Watch",        "url": "https://dig.watch/feed"},
    {"label": "Economic Times Tech",  "url": "https://economictimes.indiatimes.com/tech/rssfeeds/13357270.cms"},
    {"label": "Mint Tech",            "url": "https://www.livemint.com/rss/technology"},
    {"label": "CADE Brazil",          "url": "https://www.gov.br/cade/pt-br/assuntos/noticias/RSS"},
    {"label": "CompCom SA",           "url": "https://www.compcom.co.za/feed/"},
    {"label": "VentureBeat AI",       "url": "https://venturebeat.com/category/ai/feed/"},
    {"label": "AI Now Institute",     "url": "https://ainowinstitute.org/feed"},
    {"label": "Politico Tech EU",     "url": "https://www.politico.eu/feed/?category=tech"},
]

NOISE_PATTERNS = [
    r'\bstock\b', r'\bearnings\b', r'shares? (rise|fall|rally|drop)',
    r'\bipo\b', r'\bquarterly results\b', r'\bcricket\b', r'\bfootball\b',
    r'\bweather\b', r'\brecipe\b', r'who is\b', r'what is\b.*disease',
    r'power purchase agreement', r'dispute resolution.*middle east',
    r'engaging healthcare', r'\bbnpparibas\b', r'\bwalt disney\b',
    r'\bbcci\b', r'\bmanufacturing\b.*\bplant\b',
]

RELEVANT_TITLE_KEYWORDS = [
    'regulat','law','legislat','bill',' act ','policy','rule','directive',
    'enforcement','fine','penalt','sanction','compliance','court','ruling',
    'judgment','antitrust','competition','merger','acquisition','takeover',
    'gdpr','data protect','privacy','data breach','personal data','dpdp',
    'lgpd','popia','pdpa','data transfer',
    'artificial intelligence',' ai ','ai act','machine learning','llm',
    'generative','deepfake','agentic','foundation model',
    'platform','dsa','dma','digital market','digital service','algorithm',
    'fintech','payment','crypto','stablecoin','bnpl','open banking',
    'cartel','dominan','monopol','collusion','gatekeeper',
    'copyright','trademark','patent','intellectual property',
    'ifood','swiggy','olx','takealot','payu','brainly','gostudent',
    'meesho','pharmeasy','rapido','just eat','emag','despegar',
    'prosus','naspers','tencent',
]

def uid(a): return hashlib.md5((a.get("title","") + a.get("date","")).lower().encode()).hexdigest()[:10]

def fetch(url):
    try:
        r = requests.get(url, headers={"User-Agent": AGENT_CONFIG["user_agent"]}, timeout=AGENT_CONFIG["timeout"])
        r.raise_for_status(); return r.text
    except Exception as e:
        print(f"    [WARN] {url[:60]}: {e}"); return ""

def parse_rss_date(s):
    if not s: return ""
    for fmt in ["%a, %d %b %Y %H:%M:%S %z","%a, %d %b %Y %H:%M:%S GMT",
                "%Y-%m-%dT%H:%M:%SZ","%Y-%m-%dT%H:%M:%S%z","%Y-%m-%d"]:
        try: return datetime.strptime(s.strip(), fmt).strftime("%Y-%m-%d")
        except: pass
    return s[:10] if len(s) >= 10 else ""

def is_recent(date_str):
    if not date_str: return False
    try:
        d = datetime.fromisoformat(date_str + "T00:00:00+00:00")
        return (datetime.now(timezone.utc) - d).days <= MAX_AGE_DAYS
    except: return False

def parse_rss(xml_text, label):
    if not xml_text: return []
    try:
        clean = re.sub(r' xmlns[^"]*"[^"]*"','', xml_text)
        clean = re.sub(r'<([a-zA-Z]+):([a-zA-Z]+)',r'<\1_\2', clean)
        clean = re.sub(r'</([a-zA-Z]+):([a-zA-Z]+)',r'</\1_\2', clean)
        root = ET.fromstring(clean)
    except Exception as e:
        print(f"    [WARN] XML {label}: {e}"); return []
    items = root.findall('.//item') or root.findall('.//entry')
    out = []
    for item in items:
        def g(tag, alt=None):
            el = item.find(tag) or (item.find(alt) if alt else None)
            return el.text.strip() if el is not None and el.text else ""
        title = g('title'); 
        if not title or len(title) < 20: continue
        body = re.sub(r'<[^>]+',' ', g('description','summary') or g('content') or "").strip()
        body = re.sub(r'\s+',' ', body)[:800]
        raw_date = g('pubDate') or g('published') or g('updated') or g('dc_date') or ""
        date = parse_rss_date(raw_date)
        url = g('link') or ""
        if not url:
            le = item.find('link')
            if le is not None: url = le.get('href','') or le.text or ""
        out.append({"id":uid({"title":title,"date":date}),"title":title,"body":body or title,
                    "date":date,"published_at":date+"T00:00:00Z","source":label,"url":url.strip(),
                    "tags":[],"entity_match":[],"watchlist_hits":[],"prosus_lens":"","category":"","scope_path":""})
    return out

def title_is_relevant(title):
    t = title.lower()
    if any(re.search(p, t) for p in NOISE_PATTERNS): return False
    return any(kw in t for kw in RELEVANT_TITLE_KEYWORDS)

def categorise(a):
    text = (a["title"]+" "+a["body"]).lower()
    scores = {cat: sum(1 for kw in kws if kw.lower() in text) for cat, kws in CATEGORY_KEYWORDS.items()}
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "regulatory"

def infer_tags(a):
    text = (a["title"]+" "+a["body"]).lower()
    tag_map = {
        "GDPR":["gdpr"],"AI Act":["ai act"],"DSA":["digital services act"," dsa "],
        "DMA":["digital markets act"," dma "],"Fine":["fine","penalty","sanction"],
        "Court":["court","judgment","ruling","appeal"],"Merger":["merger","acquisition","clearance"],
        "Enforcement":["enforcement","investigation","proceeding"],
        "India":["india"," cci ","meity","dpdp"],"Brazil":["brazil","cade","lgpd"],
        "UK":[" uk ","ico"," cma ","ofcom"],"EU":[" eu ","european","edpb"],
        "US":["ftc"," doj ","federal trade"],"South Africa":["south africa","popia"],
        "Singapore":["singapore","pdpc"],"IP":["copyright","trademark","patent"],
        "AI Landscape":["artificial intelligence","llm","generative ai","deepfake","agentic"],
        "Fintech":["fintech","payment","crypto","bnpl"],"Competition":["antitrust","cartel","dominan"],
    }
    return [t for t,kws in tag_map.items() if any(kw in text for kw in kws)][:6]

def match_entities(a):
    text = (a["title"]+" "+a["body"]).lower()
    return [e for e in ALL_ENTITIES if e.lower() in text]

def hit_watchlists(a):
    text = (a["title"]+" "+a["body"]).lower()
    return [wl for wl,kws in WATCHLISTS.items() if any(kw.lower() in text for kw in kws)]

def scope_path(a):
    if a["entity_match"]: return "A"
    text = (a["title"]+" "+a["body"]).lower()
    if any(j in text for j in ["eu","uk","india","brazil","south africa","netherlands","singapore"]): return "B"
    return "C"

def score_trending(a):
    s = {"A":10,"B":5,"C":0}.get(a.get("scope_path","C"),0)
    s += len(a.get("watchlist_hits",[])) * 4 + len(a.get("entity_match",[])) * 3 + len(a.get("tags",[])) * 0.5
    if a.get("prosus_lens"): s += 2
    try:
        days = (datetime.now(timezone.utc) - datetime.fromisoformat(a["date"]+"T00:00:00+00:00")).days
        s += max(0, 7 - days) * 2
    except: pass
    return s

def prosus_lens(a):
    if not OPENAI_API_KEY: return ""
    try:
        entity_ctx = ", ".join(a["entity_match"]) if a["entity_match"] else "the Prosus portfolio"
        prompt = (f"{AGENT_CONFIG['prosus_context']}\n\nTitle: {a['title']}\nSummary: {a['body'][:400]}\n"
                  f"Category: {a['category']}\nEntities: {entity_ctx}\n\n"
                  "Write 2-3 sentences on Prosus implications. Name entities. Be concrete. Don't start with 'This development'.")
        r = requests.post("https://api.openai.com/v1/chat/completions",
            headers={"Authorization":f"Bearer {OPENAI_API_KEY}","Content-Type":"application/json"},
            json={"model":AGENT_CONFIG["openai_model"],"messages":[{"role":"user","content":prompt}],
                  "max_tokens":180,"temperature":0.3}, timeout=30)
        return r.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"    [WARN] OpenAI: {e}"); return ""

def deduplicate(articles):
    seen_ids, seen_titles, out = set(), set(), []
    for a in articles:
        norm = re.sub(r"\s+"," ", a["title"].lower().strip())[:80]
        if a["id"] in seen_ids or norm in seen_titles: continue
        seen_ids.add(a["id"]); seen_titles.add(norm); out.append(a)
    return out

def run():
    now = datetime.now(timezone.utc)
    print(f"[{now.isoformat()}] Prosus Reg Super-Agent v3")
    print(f"  Cutoff: last {MAX_AGE_DAYS} days only ({(now-timedelta(days=MAX_AGE_DAYS)).strftime('%Y-%m-%d')} → today)")
    raw = []
    for src in RSS_SOURCES:
        print(f"  RSS: {src['label']} ...")
        arts = parse_rss(fetch(src["url"]), src["label"])
        print(f"    → {len(arts)} raw")
        raw.extend(arts)
    print(f"\n  Total raw: {len(raw)}")
    raw = [a for a in raw if is_recent(a.get("date",""))]
    print(f"  After recency filter: {len(raw)}")
    raw = [a for a in raw if title_is_relevant(a.get("title",""))]
    print(f"  After title gate: {len(raw)}")
    raw = [a for a in raw if len(a.get("body","")) > 30]
    raw = deduplicate(raw)
    print(f"  After dedup: {len(raw)}")
    categorised = {cat: [] for cat in CATEGORIES}
    for a in raw:
        a["category"] = categorise(a); a["tags"] = infer_tags(a)
        a["entity_match"] = match_entities(a); a["watchlist_hits"] = hit_watchlists(a)
        a["scope_path"] = scope_path(a)
        if a["scope_path"] in ("A","B") and OPENAI_API_KEY:
            a["prosus_lens"] = prosus_lens(a)
        categorised[a["category"]].append(a)
    max_per = AGENT_CONFIG["max_per_category"]
    for cat in categorised:
        categorised[cat] = sorted(categorised[cat], key=score_trending, reverse=True)[:max_per]
    categorised["ai_landscape"] = categorised.get("ai_agents", [])
    all_arts = [a for k,v in categorised.items() for a in v if k != "ai_landscape"]
    trending = sorted(all_arts, key=score_trending, reverse=True)[:AGENT_CONFIG["trending_count"]]
    flash = [{"id":a["id"],"title":a["title"],"date":a["date"],"source":a["source"],"url":a["url"],
              "watchlist_hits":a["watchlist_hits"],"entity_match":a["entity_match"],"prosus_lens":a["prosus_lens"]}
             for a in all_arts if len(a.get("watchlist_hits",[])) >= 2 or (a.get("entity_match") and a.get("watchlist_hits"))][:10]
    PAGES_DIR.mkdir(parents=True, exist_ok=True)
    for arts in categorised.values():
        for a in arts:
            slug = re.sub(r"[^a-z0-9]+","-",a["title"].lower())[:60]
            (PAGES_DIR / f"{a['date']}-{slug}.md").write_text(
                f"---\ntitle: \"{a['title']}\"\ndate: {a['date']}\nsource: {a['source']}\n---\n\n{a['body']}\n\n{a.get('prosus_lens','')}\n", encoding="utf-8")
    total = sum(len(v) for k,v in categorised.items() if k != "ai_landscape")
    index = {"generated_at":now.isoformat(),"total_articles":total,"recency_days":MAX_AGE_DAYS,
             "trending":trending,"flash_alerts":flash,**categorised}
    CONTENT_DIR.mkdir(parents=True, exist_ok=True)
    INDEX_FILE.write_text(json.dumps(index, indent=2, ensure_ascii=False), encoding="utf-8")
    SYNC_FILE.write_text(json.dumps({"last_sync":now.isoformat(),"total_articles":total,
        "flash_alerts":len(flash),"by_category":{k:len(v) for k,v in categorised.items() if k!="ai_landscape"},
        "sources":len(RSS_SOURCES),"recency_days":MAX_AGE_DAYS}, indent=2), encoding="utf-8")
    print(f"\n[DONE] {total} articles | {len(flash)} alerts | {len(trending)} trending")
    for cat,arts in categorised.items():
        if cat != "ai_landscape" and arts: print(f"  {cat}: {len(arts)}")

if __name__ == "__main__":
    run()
