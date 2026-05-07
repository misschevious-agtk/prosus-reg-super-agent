"""
scraper.py — Prosus Regulatory Super-Agent v4.1
- 46 verified RSS feeds across EU, UK, US, India, Brazil, SA, Global
- Regulators: CMA, CFPB, CompCom SA, EU AI Office, CNIL, GCR
- IP specialists: IPKat, IP Watchdog, IP Finance
- Privacy: EFF, CDT, FPF, Access Now, Privacy International, CNIL, Netzpolitik
- Competition: Chillin Competition, GCR, EU Law Live
- AI/Chatbot: AI Now, Algorithm Watch, AI Policy Exchange, Future of Life
- Regional: ET Tech, Inc42, MediaNama (India); Jota, Telesintese (Brazil);
            TechCentral, Ventureburn, Techpoint (SA/Africa); The Hindu
- Law/Above The Law for litigation news
- Hard 7-day recency cutoff — no stale content ever
- Title-priority categorisation with body scoring fallback
- Targets 20 articles per category
"""

import os, json, re, hashlib, requests
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
from pathlib import Path
from agent.config import (
    CATEGORY_KEYWORDS, WATCHLISTS, ALL_ENTITIES, AGENT_CONFIG, CATEGORIES,
)

CONTENT_DIR = Path(__file__).parent.parent / "content"
INDEX_FILE  = CONTENT_DIR / "index.json"
SYNC_FILE   = CONTENT_DIR / "sync.json"
PAGES_DIR   = CONTENT_DIR / "pages"
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
MAX_AGE_DAYS = 7
TARGET_PER_CATEGORY = 20

# ── 50 VERIFIED RSS FEEDS ─────────────────────────────────────────────────
RSS_SOURCES = [
    # ── EU / EUROPEAN AUTHORITIES ──────────────────────────────────────────
    ("EU Digital Strategy / AI Office", "https://digital-strategy.ec.europa.eu/en/rss.xml"),
    ("CMA (UK)",                         "https://www.gov.uk/search/all.atom?organisations%5B%5D=competition-and-markets-authority&order=updated-newest"),
    ("WIPO",                             "https://www.wipo.int/pressroom/en/rss.xml"),
    ("CNIL (France)",                    "https://www.cnil.fr/fr/rss.xml"),
    ("EU Law Live",                      "https://eulawlive.com/feed/"),
    # ── US AUTHORITIES ─────────────────────────────────────────────────────
    ("CFPB",                             "https://www.cfpb.gov/feed/"),
    ("CFPB Blog",                        "https://www.cfpb.gov/about-us/blog/feed/"),
    # ── SA / AFRICA ────────────────────────────────────────────────────────
    ("CompCom South Africa",             "https://www.compcom.co.za/feed/"),
    ("TechCentral (SA)",                 "https://techcentral.co.za/feed/"),
    ("Ventureburn (Africa)",             "https://ventureburn.com/feed/"),
    ("Techpoint Africa",                 "https://techpoint.africa/feed/"),
    # ── INDIA ──────────────────────────────────────────────────────────────
    ("Economic Times Tech",              "https://economictimes.indiatimes.com/tech/rssfeeds/13357270.cms"),
    ("Inc42",                            "https://inc42.com/feed/"),
    ("MediaNama",                        "https://www.medianama.com/feed/"),
    ("The Hindu Tech",                   "https://www.thehindu.com/sci-tech/technology/feeder/default.rss"),
    # ── BRAZIL ─────────────────────────────────────────────────────────────
    ("Jota (Brazil)",                    "https://www.jota.info/feed"),
    ("Telesintese (Brazil)",             "https://www.telesintese.com.br/feed/"),
    ("The Decoder (AI)",                 "https://the-decoder.com/feed/"),
    ("Rest of World",                    "https://restofworld.org/feed/"),
    ("404 Media",                        "https://www.404media.co/feed"),
    ("Platformer",                       "https://www.platformer.news/feed"),
    ("Convergencia Digital (Brazil)",      "https://www.convergenciadigital.com.br/feed/"),
    ("Teletime (Brazil)",                  "https://www.teletime.com.br/feed/"),
    # ── IP SPECIALISTS ─────────────────────────────────────────────────────
    ("IPKat",                            "https://ipkitten.blogspot.com/feeds/posts/default?alt=rss"),
    ("IP Watchdog",                      "https://ipwatchdog.com/feed/"),
    ("IP Finance",                       "https://ipfinance.blogspot.com/feeds/posts/default"),
    # ── PRIVACY / DATA PROTECTION ─────────────────────────────────────────
    ("EFF",                              "https://www.eff.org/rss/updates.xml"),
    ("Future of Privacy Forum",          "https://fpf.org/feed/"),
    ("Privacy International",            "https://privacyinternational.org/rss.xml"),
    ("Access Now",                       "https://www.accessnow.org/feed/"),
    ("CDT",                              "https://cdt.org/feed/"),
    ("Netzpolitik (EU digital rights)",  "https://netzpolitik.org/feed/"),
    # ── AI / CHATBOT REGULATION ───────────────────────────────────────────
    ("AI Now Institute",                 "https://ainowinstitute.org/feed/"),
    ("Future of Life Institute",         "https://futureoflife.org/feed/"),
    ("Algorithm Watch",                  "https://algorithmwatch.org/en/feed/"),
    ("Responsible AI",                   "https://www.responsible.ai/feed/"),
    ("AI Policy Exchange",               "https://aipolicyexchange.org/feed/"),
    # ── COMPETITION LAW ───────────────────────────────────────────────────
    ("Chillin Competition",              "https://chillingcompetition.com/feed"),
    ("Global Competition Review",        "https://globalcompetitionreview.com/rss"),
    # ── LEGAL / LITIGATION NEWS ───────────────────────────────────────────
    ("Above The Law",                    "https://abovethelaw.com/feed/"),
    # ── BROAD TECH / POLICY ───────────────────────────────────────────────
    ("TechCrunch",                       "https://techcrunch.com/feed/"),
    ("MIT Technology Review",            "https://www.technologyreview.com/feed/"),
    ("VentureBeat AI",                   "https://venturebeat.com/feed/"),
    ("Ars Technica",                     "https://feeds.arstechnica.com/arstechnica/technology-lab"),
    ("Wired",                            "https://www.wired.com/feed/rss"),
    ("The Register",                     "https://www.theregister.com/headlines.atom"),
    ("BBC Technology",                   "https://feeds.bbci.co.uk/news/technology/rss.xml"),
    ("The Guardian Tech",                "https://www.theguardian.com/technology/rss"),
    ("Bloomberg Technology",             "https://feeds.bloomberg.com/technology/news.rss"),
    ("ZDNet Government",                 "https://www.zdnet.com/topic/government/rss.xml"),
    ("Financial Times Tech",             "https://www.ft.com/technology?format=rss"),
    ("Digital Watch",                    "https://dig.watch/feed"),
]

# ── NOISE FILTERS ─────────────────────────────────────────────────────────
EXPLICIT_NOISE = [
    "box office", "cricket match", "football match", "recipe",
    "power purchase agreement", "engaging healthcare professionals",
]

NOISE_RE = [
    # Pure earnings/financial
    r"q[1-4]\s+(?:revenue|profit|earnings|results)",
    r"quarterly (?:results|earnings|revenue|profit)",
    r"misses estimates",
    r"tops estimates",
    r"(?:revenue|profit|sales).{0,20}(?:rises|falls|drops|jumps|surges|climbs)\s+\d+",
    r"reaches \$[\d.]+\s*trillion",
    r"soars after",
    r"shares (?:jump|soar|rally|drop|fall|rise)\s+(?:on|after)",
    r"forecasts (?:strong|higher|lower|better).{0,20}(?:revenue|profit|outlook)",
    r"infuse.{0,15}crore",
    r"workers demand.{0,20}slice",
    r"(?:ai chip|data center).{0,20}(?:surge|demand|outlook)",
    r"clean energy target",
    r"computing deal with spacex",
    r"jumps \d+% after",
    r"raises \$[\d.]+[mb]",
    r"nears \$[\d.]+[b] valuation",
    r"valued at \$[\d.]+[b]",
    r"angel round",
    r"series [abcde] round",
    r"disrupt 202\d",
    r"\$[\d]+[mb] from [\w ]+(?:fund|ventures|capital)",
    r"(?:chip|semiconductor).{0,20}(?:sales|demand|outlook|factory)",
    r"loss narrows.{0,20}%",
    r"profit (?:jumps|rises|falls).{0,20}%",
    r"(?:deeptech|fintech) bets heat up",
]

STRONG_REGULATORY = [
    "regulat", "privacy", "compliance", "fine", "court", "ruling", "ban",
    "merger", "antitrust", "gdpr", "lawsuit", "settle", "enforcement",
    "probe", "investigation", "penalty", "sanction", "copyright",
    "trademark", "patent", "chatbot", "deepfake", "legislation",
]

# ── RELEVANT TITLE KEYWORDS (must match at least one) ─────────────────────
RELEVANT_KWS = [
    # Regulation/law
    "regulat", "legislation", "policy", "directive", "enforcement",
    "fine", "penalty", "sanction", "compliance", "court", "ruling",
    "judgment", "antitrust", "competition", "merger", "acquisition",
    # Privacy/data
    "gdpr", "data protection", "privacy", "data breach", "personal data",
    "dpdp", "lgpd", "popia", "pdpa", "surveillance", "data leak",
    # AI
    "ai", "artificial intelligence", "machine learning", "llm", "chatgpt",
    "generative", "deepfake", "agentic", "foundation model", "openai",
    "anthropic", "gemini", "claude", "copilot",
    # Chatbot / AI assistants (broad — let more through to categoriser)
    "chatbot", "large language", "conversational ai",
    "deepseek", "gemini", "claude", "grok", "perplexity",
    "anthropic", "hallucination", "ai fraud", "synthetic voice",
    "openai", "voice cloning", "ai impersonat", "ai defamat",
    # Platform
    "platform", "dsa", "dma", "digital market", "algorithm",
    # Fintech
    "fintech", "payment", "crypto", "stablecoin", "bnpl",
    # Competition
    "cartel", "monopoly", "dominant", "gatekeeper", "probed",
    # IP
    "copyright", "trademark", "patent", "intellectual property",
    "training data", "text and data mining",
    # Legal actions
    "lawsuit", "sued", "settle", "ban", "block", "probe", "investigate",
    "fined", "violation", "breach", "infringement", "watchdog",
    # Prosus entities
    "ifood", "swiggy", "olx", "takealot", "payu", "brainly", "meesho",
    "pharmeasy", "rapido", "prosus", "naspers", "tencent", "just eat",
    "emag", "creditas", "iyzico", "gostudent", "eruditus", "urban company",
    "dott", "bykea", "media24", "ema ai", "brainfish",
    # Big tech (regulatory angle)
    "apple", "google", "meta", "amazon", "microsoft", "openai",
    "uber", "deliveroo", "doordash",
    # Regulators (articles about them)
    "ftc", "cma", "cade", "cci", "acm", "edpb", "ico", "cfpb", "anatel", "anpd", "bacen",
    "compcom", "anpd", "cnil",
]

# ── CATEGORY RULES ────────────────────────────────────────────────────────

# Title-priority rules — exact phrase match in title wins
TITLE_CAT_RULES = [
    ("competition", [
        "antitrust", "merger inquiry", "merger control", "cartel", "competition fine",
        "competition probe", "probed over", "market dominance", "gatekeeper",
        "acquisition blocked", "merger cleared", "competition authority",
        "abuse of dominance", "market investigation", "competition law",
        "merger review", "price fixing", "competition watchdog",
    ]),
    ("privacy", [
        "gdpr", "data breach", "data protection", "privacy violation", "privacy fine",
        "privacy law", "data leak", "personal data", "surveillance", "cookie consent",
        "pdpa", "dpdp", "lgpd", "popia", "adequacy decision", "data transfer ban",
        "privacy watchdog", "data governance", "biometric", "right to erasure",
    ]),
    ("ip", [
        "copyright", "trademark", "patent", "intellectual property", "trade secret",
        "training data", "ai-generated", "fair use", "infringement", "wipo",
        "text and data mining", "neighbouring rights", "press publisher",
        "database right", "music ai", "book ai training",
    ]),
    ("chatbot_regulation", [
        # Explicit chatbot/LLM legal
        "chatbot law", "chatbot regulation", "chatbot banned", "chatbot fined",
        "llm regulation", "llm lawsuit", "chatgpt lawsuit", "openai lawsuit",
        "openai fined", "openai sued", "openai probe", "openai investigat",
        "anthropic sued", "anthropic fine", "anthropic regulat",
        "chatbot liability", "conned by a chatbot", "chatbot fraud",
        "military chatbot", "generative ai lawsuit", "generative ai sued",
        "llm liability", "chatbot harm", "chatbot compliance",
        # Broad AI assistant regulation
        "ai assistant ban", "ai assistant regulat", "ai assistant law",
        "gpt regulat", "gpt banned", "gpt sued", "gpt probe",
        "gemini sued", "gemini banned", "gemini regulat",
        "claude sued", "claude banned", "copilot sued", "copilot ban",
        "deepseek ban", "deepseek regulat", "deepseek probe",
        "chatgpt banned", "chatgpt probe", "chatgpt fine",
        "openai faces", "openai ordered", "openai blocked",
        "ai hallucination lawsuit", "ai defamation", "ai misinformation law",
        "ai impersonation", "synthetic voice law", "voice cloning law",
        "ai-generated fraud", "ai fraud law", "chatbot scam",
        "llm copyright", "llm training lawsuit", "chatgpt copyright",
        "openai copyright", "anthropic copyright", "google ai sued",
        "meta ai sued", "microsoft ai sued", "ai bias lawsuit",
        "ai discrimination", "ai in hiring", "automated hiring ban",
        "eu targets ai", "regulator targets ai", "ftc ai", "ftc openai",
        "cci ai", "cma ai", "chatbot children", "ai children safety",
    ]),
    ("ai_agents", [
        "ai act", "eu ai act", "ai regulation", "ai governance", "ai liability",
        "ai safety bill", "ai office", "high-risk ai", "gpai", "deepfake law",
        "synthetic media law", "ai compliance", "algorithmic accountability",
        "ai audit", "automated decision ban", "ai watermarking", "iso 42001",
        "foundation model regulation", "ai transparency obligation",
    ]),
    ("fintech", [
        "crypto regulation", "stablecoin", "bnpl", "payment regulation", "fintech law",
        "digital payments", "open banking", "psd3", "e-money", "dora",
        "cfpb", "bacen", "payment fine", "defi regulation", "upi regulation",
    ]),
    ("platform_liability", [
        "platform liability", "digital services act", "dsa enforcement",
        "content moderation law", "online safety act", "online harms",
        "vlop", "intermediary liability", "age verification law",
    ]),
    ("gig_economy", [
        "gig worker", "platform worker", "worker classification", "gig economy law",
        "delivery driver rights", "algorithmic management", "worker misclassification",
        "platform work directive", "minimum earnings guarantee",
    ]),
    ("consumer_protection", [
        "consumer protection", "dark pattern", "drip pricing", "fake reviews",
        "age verification", "children online", "coppa", "misleading advertising",
        "unfair commercial practices", "subscription trap",
    ]),
]

# Body scoring fallback
BODY_CAT_RULES = [
    ("competition", [
        "antitrust", "competition law", "merger control", "cartel",
        "market investigation", "gatekeeper", "price fixing", "market dominance",
        "merger inquiry", "acquisition blocked", "competition authority",
    ]),
    ("privacy", [
        "gdpr", "data protection", "personal data", "data breach", "privacy law",
        "dpdp", "lgpd", "popia", "pdpa", "surveillance", "adequacy decision",
        "data localisation", "consent enforcement", "biometric",
    ]),
    ("ip", [
        "intellectual property", "copyright infringement", "trademark",
        "patent", "ai training data", "text and data mining", "wipo",
        "trade secret", "fair use", "neighbouring rights",
    ]),
    ("chatbot_regulation", [
        # Legal / regulatory actions
        "chatbot law", "llm regulation", "chatgpt regulation",
        "openai lawsuit", "openai sued", "openai fined", "openai probe",
        "openai investigat", "openai ordered", "openai blocked", "openai ban",
        "anthropic sued", "anthropic fined", "anthropic probe", "anthropic regulat",
        "chatbot liability", "chatbot fraud", "chatbot scam", "chatbot harm",
        "generative ai sued", "generative ai fine", "generative ai ban",
        "llm liability", "llm lawsuit", "llm banned",
        "chatgpt banned", "chatgpt probe", "chatgpt fine", "chatgpt lawsuit",
        "deepseek ban", "deepseek probe", "deepseek regulat", "deepseek blocked",
        "gemini sued", "gemini banned", "gemini probe",
        "claude banned", "claude sued", "claude probe",
        "grok banned", "grok sued", "copilot ban", "copilot sued",
        "ai hallucination lawsuit", "ai defamation", "ai impersonation",
        "synthetic voice law", "voice cloning law", "ai-generated fraud",
        "conned by a chatbot", "military chatbot",
        "llm copyright", "llm training lawsuit", "chatgpt copyright",
        "openai copyright", "anthropic copyright",
        "ftc openai", "ftc anthropic", "ftc chatbot",
        "cma openai", "cma anthropic", "cci ai chatbot",
        "chatbot children", "ai children safety", "ai in hiring ban",
        # Company strategy that is regulatory-relevant
        "openai regul", "anthropic regul", "openai policy",
        "anthropic policy", "openai comply", "anthropic comply",
        # Geopolitical / government AI talks
        "us and china", "china ai talks", "ai formal talks", "ai diplomacy",
        "government chatgpt", "government openai", "government anthropic",
        "senate ai", "congress ai", "parliament ai", "minister ai",
        "white house ai", "eu openai", "eu anthropic", "eu chatgpt",
        # OpenAI / Anthropic business with regulatory angle
        "openai ad", "chatgpt ad", "openai self-serve", "chatgpt self-serve",
        "openai antitrust", "anthropic antitrust",
    ]),
    ("ai_agents", [
        "ai act", "gpai", "foundation model regulation", "ai governance",
        "ai liability", "ai safety bill", "ai office", "high-risk ai",
        "algorithmic accountability", "automated decision ban",
        "ai audit", "ai watermark", "ai standard", "ai compliance",
        "deepfake law", "synthetic media law", "ai rulebook",
    ]),
    ("fintech", [
        "fintech regulation", "payment regulation", "psd3", "open banking",
        "bnpl regulation", "crypto regulation", "stablecoin", "dora",
    ]),
    ("platform_liability", [
        "platform liability", "digital services act", "content moderation law",
        "online safety", "intermediary liability", "vlop",
    ]),
    ("gig_economy", [
        "gig worker", "platform worker", "worker classification",
        "gig economy law", "delivery worker rights",
    ]),
    ("consumer_protection", [
        "consumer protection", "dark pattern", "unfair commercial",
        "fake reviews", "age verification",
    ]),
]

# ══════════════════════════════════════════════════════════════════════════════
# PROSUS RELEVANCE GATE — article must match ≥1 of these to be included
# Source: prosus.com/portfolio + Tara's regulatory focus areas (May 2026)
# ══════════════════════════════════════════════════════════════════════════════

PROSUS_ENTITIES = [
    # Core / large opcos
    "prosus", "naspers", "tencent",
    "delivery hero", "just eat", "just eat takeaway",
    "ifood", "swiggy", "oda food", "flink food", "sharebite", "foodics",
    "olx", "autotrader", "autovit", "imovirtual",
    "otodom", "otomoto", "standvirtual", "storia", "property24",
    "payu", "iyzico", "wibmo", "zooz", "red dot payment", "tonik",
    "paysense", "lazypay", "remitly", "bux fintech", "bibit",
    "endowus", "thndr", "klar fintech", "spendflow", "iniciador",
    "meesho", "urban company", "bykea", "rapido", "captain fresh",
    "elasticrun", "shipper", "shopup", "mensa brands", "virgio",
    "good glamm", "vegrow", "dehaat", "aruna", "creditas", "azos",
    "eruditus", "brainly", "platzi", "goodhabitz", "gostudent",
    "sololearn", "skillsoft", "edume", "arivihan",
    "pharmeasy", "corti health", "voa health",
    "stack overflow", "similarweb", "superside", "bandlab",
    "avant arte", "dott scooter", "kovi", "99minutos",
    "emag", "merxu", "flexion mobile",
    # AI investees
    "zapia", "brainlogic", "brain logic",
    "advolve", "brainfish", "luzia",
    "martian ai", "qeen.ai", "orbii", "nexad",
    "taktile", "spotdraft", "intella ai", "kismet ai",
    "fundamental research labs",
    "cusp ai", "neara", "plerion",
    "airmeet", "watchtowr", "zypl",
    "fashinza", "bilt rewards",
]

REGULATORY_BODIES = [
    # India
    "competition commission of india", "cci investigat", "cci order",
    "cci fine", "cci probe", "cci swiggy", "cci meesho", "cci zomato",
    "reserve bank of india", "rbi guideline", "rbi circular",
    "rbi fintech", "rbi payment", "rbi lending", "rbi digital",
    "meity", "ministry of electronics", "india data protection",
    "dpdp act", "india privacy bill", "trai regulation",
    "npci ", "upi regulation", "india antitrust",
    # Brazil
    "cade ", "cade aprovação", "cade condena", "cade multa", "cade probe",
    "anpd ", "lgpd", "brazil data protection", "brazil privacy",
    "bacen ", "banco central do brasil", "anatel ",
    # Netherlands / EU
    "acm investigation", "acm fine", "acm ruling", "dutch competition",
    "digital markets act", "dma enforcement", "dma designation",
    "digital services act", "dsa enforcement", "dsa fine",
    "eu ai act", "ai act", "gpai regulation",
    "edpb", "eu data protection board", "gdpr fine", "gdpr enforcement",
    # South Africa
    "competition commission south africa",
    "competition tribunal south africa",
    "south africa competition",
    # Turkey
    "turkish competition authority", "rekabet kurumu", "turkey fintech",
    # Pakistan
    "pakistan competition commission", "state bank of pakistan",
    # Indonesia
    "kppu", "indonesia competition", "ojk regulation",
    # Poland / Romania
    "uokik", "poland competition", "competition council romania",
    # UK
    "competition and markets authority", "cma ruling", "cma probe",
    "cma investigation", "cma fine", "ico fine", "ico enforcement",
    # US
    "ftc investigation", "ftc fine", "ftc sues", "ftc probe",
    "doj antitrust", "cfpb rule", "cfpb fine",
    # Global IP (Tara's domain)
    "wipo", "inta trademark", "brand protection ruling",
]

THEMATIC_HOOKS = [
    # Food delivery
    "food delivery regulation", "food delivery antitrust",
    "food delivery fine", "food delivery worker",
    "delivery platform law", "delivery app ban",
    # Classifieds / proptech
    "online classifieds regulation", "property portal law",
    "auto classifieds regulation",
    # Payments / fintech
    "bnpl regulation", "buy now pay later law",
    "digital lending regulation", "neobank regulation",
    "payment aggregator regulation", "fintech licensing",
    "cross-border payments regulation", "remittance regulation",
    "open banking regulation", "psd3", "instant payments regulation",
    # Edtech
    "edtech regulation", "online education regulation",
    # Healthtech
    "online pharmacy regulation", "digital health regulation",
    "telemedicine law",
    # Gig / workers
    "platform worker regulation", "gig worker regulation",
    "worker classification", "algorithmic management law",
    # AI / agentic
    "generative ai regulation", "ai agent regulation",
    "ai governance", "ai liability", "ai act enforcement",
    "llm regulation", "chatbot regulation", "ai fraud law",
    "deepfake regulation", "synthetic media law", "voice cloning law",
    "agentic ai regulation", "ai copyright",
    # IP / brand
    "trademark infringement", "brand protection",
    "counterfeiting online", "ip enforcement",
    "domain name regulation", "cybersquatting",
    "ai training data lawsuit", "llm copyright",
    # Platform liability
    "platform liability", "marketplace liability",
    "intermediary liability", "vlop enforcement",
    "online marketplace regulation",
    # M&A
    "food delivery merger", "classifieds merger",
    "fintech acquisition blocked", "edtech merger",
    "healthtech acquisition", "tech merger blocked",
]

ALL_RELEVANCE_KWS = [kw.lower() for kw in PROSUS_ENTITIES + REGULATORY_BODIES + THEMATIC_HOOKS]

def is_prosus_relevant(a):
    """
    Tier-1: Direct portfolio entity mention → always relevant.
    Tier-2: Title contains a Prosus-sector signal → relevant.
    Tier-3: Regulator + sector combo in full text → relevant.
    Everything else → drop.
    """
    title = a["title"].lower()
    text  = (a["title"] + " " + a.get("body", "") + " " + " ".join(a.get("tags", []))).lower()

    # Tier 1 — direct portfolio entity anywhere in text
    ENTITIES_LC = [e.lower() for e in PROSUS_ENTITIES]
    if any(kw in text for kw in ENTITIES_LC):
        return True

    # Sector keywords broad enough to catch relevant stories from their TITLE alone
    TITLE_SECTOR_KWS = [
        # AI / tech regulation (Zapia, all AI investees, EU AI Act impacts)
        "ai act", "eu ai", "ai regulation", "ai law", "ai governance",
        "ai liability", "ai agent", "agentic ai", "generative ai",
        "llm", "chatbot", "foundation model", "deepfake",
        "openai", "anthropic", "deepseek", "chatgpt", "gemini",
        # Fintech / payments (PayU, iyzico, LazyPay, Creditas)
        "fintech", "neobank", "digital bank", "payment regulation",
        "bnpl", "buy now pay later", "digital lending",
        "open banking", "payment app", "payment platform",
        "crypto regulation", "stablecoin", "remittance",
        "paypal", "mastercard", "visa", "stripe",  # competitors/precedents
        # Food delivery (Swiggy, iFood, Delivery Hero, Just Eat)
        "food delivery", "delivery app", "food app",
        "restaurant platform", "delivery platform",
        "uber eats", "doordash", "zomato",  # competitors/precedents
        # Gig / platform workers
        "gig worker", "platform worker", "worker classification",
        "gig economy", "algorithmic work",
        # E-commerce / marketplace (Meesho, OLX, eMAG)
        "e-commerce regulation", "online marketplace",
        "marketplace liability", "platform liability",
        "digital services act", "dsa ", " dma ",
        # Classifieds / property (OLX, AutoTrader, OtoDOM)
        "classifieds", "property portal", "real estate platform",
        # Edtech (Eruditus, Brainly, Platzi, GoodHabitz)
        "edtech", "online education regulation", "learning platform",
        # Healthtech (PharmEasy, Corti)
        "online pharmacy", "digital health regulation", "telemedicine law",
        # IP / brand (Tara's INTA focus)
        "trademark", "brand protection", "intellectual property",
        "copyright infringement", "ip enforcement", "domain name",
        "cybersquatting", "counterfeiting",
        # Privacy / data
        "gdpr", "data protection", "privacy regulation",
        "data localisation", "biometric data",
        # Competition in Prosus markets
        "antitrust", "competition fine", "competition probe",
        "monopoly", "market dominance",
        # India broadly (huge Prosus exposure)
        "india tech", "indian startup", "india digital",
        "india competition", "india antitrust", "india fintech",
        "india data", "india privacy",
        # Brazil broadly (iFood, OLX, Creditas)
        "brazil tech", "brazil fintech", "brazil digital",
        "brazil competition", "brazil data",
    ]

    # Tier 2 — title signal alone is sufficient
    if any(kw in title for kw in TITLE_SECTOR_KWS):
        return True

    # Tier 2b — thematic hook in full text
    THEMES_LC = [t.lower() for t in THEMATIC_HOOKS]
    if any(kw in text for kw in THEMES_LC):
        return True

    # Tier 3 — regulator name + sector in body (for articles where title is vague)
    PROSUS_SECTORS = [
        "food delivery", "delivery app", "restaurant app",
        "fintech", "payment", "neobank", "digital lending", "bnpl",
        "edtech", "online education", "e-learning",
        "online pharmacy", "digital health", "telemedicine",
        "platform worker", "gig worker",
        "e-commerce", "online marketplace", "classifieds",
        "artificial intelligence", "generative ai", "llm", "chatbot",
        "trademark", "brand protection", "intellectual property",
        "platform liability", "content moderation",
        "big tech", "digital platform", "tech company",
        "data protection", "privacy", "personal data",
    ]
    REGULATOR_NAMES = [kw.lower() for kw in REGULATORY_BODIES]
    if any(reg in text for reg in REGULATOR_NAMES):
        if any(sector in text for sector in PROSUS_SECTORS):
            return True

    return False


def categorise(a):
    text = (a["title"] + " " + a["body"]).lower()
    title = a["title"].lower()
    # Title match wins — first match in priority order
    for cat, kws in TITLE_CAT_RULES:
        if any(kw in title for kw in kws):
            return cat
    # Body scoring fallback
    best_cat, best_score = "regulatory", 0
    for cat, kws in BODY_CAT_RULES:
        score = sum(1 for kw in kws if kw in text)
        if score > best_score:
            best_score, best_cat = score, cat
    return best_cat


# ── HELPERS ───────────────────────────────────────────────────────────────

def uid(title, date):
    return hashlib.md5((title + date).lower().encode()).hexdigest()[:10]

def fetch(url):
    try:
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=14)
        r.raise_for_status()
        return r.text
    except Exception as e:
        print(f"    [WARN] {url[:55]}: {e}")
        return ""

def parse_date(s):
    if not s: return ""
    try: return parsedate_to_datetime(s).strftime("%Y-%m-%d")
    except: pass
    try: return datetime.fromisoformat(s.replace("Z", "+00:00")).strftime("%Y-%m-%d")
    except: pass
    return s[:10] if len(s) >= 10 else ""

def is_recent(d):
    if not d: return False
    try:
        dt = datetime.fromisoformat(d + "T00:00:00+00:00")
        return (datetime.now(timezone.utc) - dt).days <= MAX_AGE_DAYS
    except: return False

def has_kw(text, kws):
    t = text.lower()
    for kw in kws:
        kw = kw.lower().strip()
        if len(kw) <= 3:
            if re.search(r"\b" + re.escape(kw) + r"\b", t): return True
        else:
            if kw in t: return True
    return False

def is_noise(title):
    t = title.lower()
    if has_kw(title, EXPLICIT_NOISE): return True
    for pat in NOISE_RE:
        if re.search(pat, t):
            if not any(s in t for s in STRONG_REGULATORY):
                return True
    return False

def parse_feed(xml_text, label):
    if not xml_text: return []
    try:
        xml = re.sub(r"<(\w+):", r"<\1_", xml_text)
        xml = re.sub(r"</(\w+):", r"</\1_", xml)
        xml = re.sub(r'\s+xmlns(?::\w+)?="[^"]*"', "", xml)
        root = ET.fromstring(xml)
    except Exception as e:
        print(f"    [WARN] XML {label}: {e}")
        return []
    items = root.findall(".//item") or root.findall(".//entry")
    out = []
    for item in items:
        def g(*tags):
            for tag in tags:
                el = item.find(tag)
                if el is not None and el.text is not None and el.text.strip():
                    return el.text.strip()
            return ""
        title = g("title")
        if len(title) < 15: continue
        date = parse_date(g("pubDate", "published", "updated", "dc_date", "date"))
        if not is_recent(date): continue
        if is_noise(title): continue
        if not has_kw(title, RELEVANT_KWS): continue
        body = re.sub(r"<[^>]+>", " ", g("description", "summary", "content")).strip()
        body = re.sub(r"\s+", " ", body)[:700]
        link_el = item.find("link")
        url = ""
        if link_el is not None:
            url = link_el.get("href", "") or (link_el.text or "").strip()
        article = {
            "id": uid(title, date), "title": title, "date": date,
            "published_at": date + "T00:00:00Z", "source": label, "url": url,
            "body": body or title, "tags": [], "entity_match": [],
            "watchlist_hits": [], "prosus_lens": "", "category": "", "scope_path": "",
        }
        # ── PROSUS RELEVANCE GATE ─────────────────────────────────────────
        # Drop articles with no connection to Prosus portfolio or markets
        if not is_prosus_relevant(article): continue
        out.append(article)
    return out

def infer_tags(a):
    text = (a["title"] + " " + a["body"]).lower()
    tag_map = {
        "GDPR": ["gdpr"], "AI Act": ["ai act"], "DSA": [" dsa "], "DMA": [" dma "],
        "Fine": ["fine", "penalty", "sanction"],
        "Court": ["court", "judgment", "ruling", "appeal"],
        "Merger": ["merger", "acquisition"],
        "Enforcement": ["enforcement", "investigation"],
        "India": ["india", "dpdp", "cci", "rbi", "sebi"],
        "Brazil": ["brazil", "cade", "lgpd", "bacen", "anpd"],
        "UK": ["united kingdom", " cma ", "ofcom", "ico"],
        "EU": ["european", "edpb", "commission", "cnil"],
        "Netherlands": ["netherlands", " acm ", "autoriteit persoonsgegevens"],
        "US": ["ftc", " doj ", "federal trade", "cfpb", "nlrb"],
        "South Africa": ["south africa", "popia", "compcom", "takealot"],
        "Turkey": ["turkey", "kvkk", "btk", "iyzico"],
        "Singapore": ["singapore", "pdpc", "mas"],
        "IP": ["copyright", "trademark", "patent"],
        "AI": ["artificial intelligence", "llm", "generative", "deepfake", "chatbot"],
        "Fintech": ["fintech", "crypto", "bnpl", "payment"],
        "Competition": ["antitrust", "cartel", "merger", "dominan"],
        "Chatbot": ["chatbot", "llm", "chatgpt", "claude", "gemini", "openai"],
        "Gig": ["gig worker", "platform worker", "worker classification"],
    }
    return [t for t, kws in tag_map.items() if any(kw in text for kw in kws)][:8]

def match_entities(a):
    text = (a["title"] + " " + a["body"]).lower()
    return [e for e in ALL_ENTITIES if e.lower() in text]

def hit_watchlists(a):
    text = (a["title"] + " " + a["body"]).lower()
    return [wl for wl, kws in WATCHLISTS.items()
            if any(kw.lower() in text for kw in kws)]

def scope_path(a):
    if a["entity_match"]: return "A"
    text = (a["title"] + " " + a["body"]).lower()
    if any(j in text for j in [
        "eu ", "uk ", "india", "brazil", "south africa",
        "netherlands", "singapore", "nigeria", "kenya",
        "turkey", "indonesia", "pakistan",
    ]): return "B"
    return "C"

def score(a):
    s = {"A": 10, "B": 5, "C": 0}.get(a.get("scope_path", "C"), 0)
    s += len(a.get("watchlist_hits", [])) * 4
    s += len(a.get("entity_match", [])) * 3
    s += len(a.get("tags", [])) * 0.5
    if a.get("prosus_lens"): s += 2
    try:
        days = (datetime.now(timezone.utc) -
                datetime.fromisoformat(a["date"] + "T00:00:00+00:00")).days
        s += max(0, 7 - days) * 2
    except: pass
    return s

def prosus_lens(a):
    if not OPENAI_API_KEY: return ""
    try:
        ctx = ", ".join(a["entity_match"]) if a["entity_match"] else "the Prosus portfolio"
        prompt = (
            "Prosus is a global tech investor: iFood, Swiggy, OLX, PayU, Brainly, Meesho, "
            "PharmEasy, Rapido, eMAG, Takealot, GoStudent, Ema (AI agent), Brainfish, "
            "iyzico, Creditas, Urban Company, Dott, Bykea, Media24, etc. HQ: Amsterdam.\n\n"
            f"Title: {a['title']}\nSummary: {a['body'][:400]}\n"
            f"Category: {a['category']}\nDirect entities: {ctx}\n\n"
            "Write 2-3 sentences on Prosus-specific implications. Name affected entities. "
            "Be concrete on compliance, strategic, or operational impact. "
            "Do not start with 'This development'."
        )
        r = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {OPENAI_API_KEY}",
                     "Content-Type": "application/json"},
            json={"model": "gpt-4o-mini",
                  "messages": [{"role": "user", "content": prompt}],
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
        if a["id"] in seen_ids or norm in seen_titles: continue
        seen_ids.add(a["id"]); seen_titles.add(norm); out.append(a)
    return out


# ── MAIN ─────────────────────────────────────────────────────────────────

def run():
    now = datetime.now(timezone.utc)
    cutoff = (now - timedelta(days=MAX_AGE_DAYS)).strftime("%Y-%m-%d")
    print(f"[{now.strftime('%Y-%m-%d %H:%M')} UTC] Prosus Reg Super-Agent v4.1")
    print(f"  Cutoff: {cutoff} → today | Target: {TARGET_PER_CATEGORY}/cat | Sources: {len(RSS_SOURCES)}")

    raw = []
    for label, url in RSS_SOURCES:
        print(f"  {label[:40]:<40} ...", end=" ", flush=True)
        arts = parse_feed(fetch(url), label)
        print(len(arts))
        raw.extend(arts)

    print(f"\n  Raw total: {len(raw)}")
    raw = deduplicate(raw)
    print(f"  After dedup: {len(raw)}")

    ALL_CATS = [cat for cat, _ in TITLE_CAT_RULES] + ["regulatory"]
    categorised = {cat: [] for cat in ALL_CATS}

    for a in raw:
        a["category"]       = categorise(a)
        a["tags"]           = infer_tags(a)
        a["entity_match"]   = match_entities(a)
        a["watchlist_hits"] = hit_watchlists(a)
        a["scope_path"]     = scope_path(a)
        if a["scope_path"] in ("A", "B") and OPENAI_API_KEY:
            a["prosus_lens"] = prosus_lens(a)
        categorised.setdefault(a["category"], []).append(a)

    for cat in categorised:
        categorised[cat] = sorted(
            categorised[cat], key=score, reverse=True
        )[:TARGET_PER_CATEGORY]

    # Dashboard compatibility aliases
    categorised["ai_landscape"] = categorised.get("ai_agents", [])
    categorised["chatbot"]      = categorised.get("chatbot_regulation", [])

    skip = {"ai_landscape", "chatbot"}
    all_arts = [a for k, v in categorised.items() for a in v if k not in skip]
    trending = sorted(all_arts, key=score, reverse=True)[:12]
    flash = [
        {"id": a["id"], "title": a["title"], "date": a["date"],
         "source": a["source"], "url": a["url"],
         "watchlist_hits": a["watchlist_hits"],
         "entity_match": a["entity_match"], "prosus_lens": a["prosus_lens"]}
        for a in all_arts
        if len(a.get("watchlist_hits", [])) >= 2
        or (a.get("entity_match") and a.get("watchlist_hits"))
    ][:10]

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

    total = sum(len(v) for k, v in categorised.items() if k not in skip)
    index = {
        "generated_at":   now.isoformat(),
        "total_articles": total,
        "recency_days":   MAX_AGE_DAYS,
        "trending":       trending,
        "flash_alerts":   flash,
        **categorised,
    }
    CONTENT_DIR.mkdir(parents=True, exist_ok=True)
    INDEX_FILE.write_text(
        json.dumps(index, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    SYNC_FILE.write_text(json.dumps({
        "last_sync":      now.isoformat(),
        "total_articles": total,
        "flash_alerts":   len(flash),
        "recency_days":   MAX_AGE_DAYS,
        "sources":        len(RSS_SOURCES),
        "by_category":    {k: len(v) for k, v in categorised.items() if k not in skip},
    }, indent=2), encoding="utf-8")

    print(f"\n DONE: {total} articles | {len(flash)} flash alerts | {len(trending)} trending")
    for cat, arts in sorted(categorised.items(), key=lambda x: -len(x[1])):
        if cat not in skip and arts:
            print(f"  {cat}: {len(arts)}")


if __name__ == "__main__":
    run()
