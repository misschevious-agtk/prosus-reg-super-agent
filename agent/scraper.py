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
- Targets 30 articles per category
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
TARGET_PER_CATEGORY = 30

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
    # ── IP & Brand Protection specialists ─────────────────────────────────
    ("World Trademark Review",             "https://www.worldtrademarkreview.com/rss"),
    ("IP Kat",                             "https://ipkitten.blogspot.com/feeds/posts/default"),
    # ── Privacy specialists ────────────────────────────────────────────────
    ("Future of Privacy Forum",            "https://fpf.org/feed/"),
    ("EFF Deeplinks",                      "https://www.eff.org/rss/updates.xml"),
    ("CNIL Press Releases",                "https://www.cnil.fr/en/rss.xml"),
    ("EDPB",                               "https://edpb.europa.eu/rss.xml"),
    ("Guardian Privacy",                   "https://www.theguardian.com/world/privacy/rss"),
    ("Krebs on Security",                  "https://krebsonsecurity.com/feed/"),
    ("Infosecurity Magazine",              "https://www.infosecurity-magazine.com/rss/news/"),
    ("Dark Reading",                       "https://www.darkreading.com/rss.xml"),
    ("BleepingComputer",                   "https://www.bleepingcomputer.com/feed/"),
    ("DataBreaches.net",                   "https://www.databreaches.net/feed/"),
    ("CyberScoop",                         "https://cyberscoop.com/feed/"),
    ("The Record (cybersecurity)",         "https://therecord.media/feed"),
    ("Hunton Privacy Blog",                "https://www.huntonprivacyblog.com/feed/"),
    ("Inside Privacy (Covington)",         "https://www.insideprivacy.com/feed/"),
    ("TechGDPR",                           "https://techgdpr.com/blog/feed/"),
    ("Mozilla Privacy Blog",               "https://blog.mozilla.org/privacy/feed/"),
    ("SecurityWeek",                       "https://feeds.feedburner.com/securityweek"),
    ("Rest of World",                      "https://restofworld.org/feed/"),
    # ── Platform / Gig / Society ──────────────────────────────────────────
    ("Oxford Internet Institute",          "https://www.oii.ox.ac.uk/feed/"),
    ("AI Now Institute",                   "https://ainowinstitute.org/feed"),
    ("Fairwork Project",                   "https://fair.work/en/fw/feed/"),
    ("Guardian Workers Rights",            "https://www.theguardian.com/money/work-and-careers/rss"),
    ("Reuters Tech (platform)",            "https://feeds.reuters.com/reuters/technologyNews"),
    # ── Emerging Markets: Africa ──────────────────────────────────────────
    ("TechCabal (Africa)",                 "https://techcabal.com/feed/"),
    ("Techloy (Africa)",                   "https://techloy.com/feed/"),
    # ── Emerging Markets: India ───────────────────────────────────────────
    ("Inc42 (India)",                      "https://inc42.com/feed/"),
    # ── Emerging Markets: Brazil ──────────────────────────────────────────
    ("Startups.com.br (Brazil)",           "https://startups.com.br/feed/"),
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
    "promo code", "discount code", "coupon code", "% off ",
    "best deals", "buying guide", "review:", "vs review",
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
    # Prosus entities (direct)
    "ifood", "swiggy", "olx", "takealot", "payu", "brainly", "meesho",
    "pharmeasy", "rapido", "prosus", "naspers", "tencent", "just eat",
    "emag", "creditas", "iyzico", "gostudent", "eruditus", "urban company",
    "dott", "bykea", "media24", "ema ai", "brainfish", "zapia",
    # Big tech / AI (regulatory angle)
    "apple", "google", "meta", "amazon", "microsoft", "openai",
    "uber", "deliveroo", "doordash", "zomato", "paytm",
    # Regulators
    "ftc", "cma", "cade", "cci", "acm", "edpb", "ico", "cfpb",
    "anatel", "anpd", "bacen", "compcom", "cnil", "meity", "rbi",
    # Thought-leadership topics — let India/Africa/EM stories through
    "startup", "unicorn", "funding", "venture", "invest",
    "digital bank", "neobank", "insurtech", "lending",
    "e-commerce", "marketplace", "gig", "delivery",
    "edtech", "healthtech", "proptech", "agritech",
    "india", "brazil", "africa", "nigeria", "kenya",
    "indonesia", "pakistan", "turkey", "south africa",
    "trademark", "copyright", "ip ", "intellectual",
    "data", "privacy", "surveillance", "biometric",
]

# ── CATEGORY RULES ────────────────────────────────────────────────────────

# Title-priority rules — exact phrase match in title wins
TITLE_CAT_RULES = [
    # ── 1. AI & EMERGING TECH ─────────────────────────────────────────────
    ("ai_tech", [
        "ai act", "eu ai", "ai regulation", "ai law", "ai governance",
        "ai liability", "ai safety", "ai policy", "ai rules", "ai standard",
        "ai compliance", "ai audit", "ai office", "high-risk ai", "gpai",
        "algorithmic accountability", "automated decision", "ai watermark",
        "ai transparency", "foundation model", "ai oversight", "ai ban",
        "ai legislation", "ai bill", "ai framework", "ai strategy",
        "ai lawsuit", "ai sued", "ai fined", "ai court", "ai probe",
        "ai investigation", "ai penalty", "ai damages", "ai settlement",
        "openai lawsuit", "openai sued", "openai fined", "openai probe",
        "openai trial", "openai court", "openai ordered", "openai blocked",
        "anthropic sued", "anthropic fine", "anthropic probe",
        "chatgpt lawsuit", "chatgpt sued", "chatgpt fine", "chatgpt banned",
        "deepseek ban", "deepseek probe", "gemini sued", "gemini banned",
        "claude banned", "claude sued", "copilot ban", "copilot sued",
        "meta ai sued", "google ai sued", "microsoft ai sued",
        "ai hallucination", "ai defamation", "ai impersonation",
        "ai fraud", "deepfake law", "synthetic media", "voice cloning",
        "ai-generated", "ai harm", "ai bias", "ai discrimination",
        "ai misinformation", "ai copyright", "ai training data",
        "llm copyright", "llm lawsuit", "llm regulation",
        "openai", "anthropic", "deepseek", "chatgpt", "gemini", "claude",
        "grok", "perplexity", "mistral", "llama", "gpt-", " llm ",
        "large language model", "generative ai", "agentic ai", "ai agent",
        "chatbot", "multimodal", "ai model", "ai chip", "ai compute",
        "ai race", "ai sovereignty", "us china ai", "ai export",
    ]),
    # ── 2. COMPETITION & MARKETS ──────────────────────────────────────────
    ("competition", [
        "antitrust", "merger inquiry", "merger control", "merger probe",
        "merger blocked", "merger cleared", "merger fine", "merger review",
        "cartel", "price fixing", "market sharing", "bid rigging",
        "competition fine", "competition probe", "competition authority",
        "competition watchdog", "competition law", "competition ruling",
        "market dominance", "abuse of dominance", "dominant position",
        "monopoly", "oligopoly", "gatekeeper", "market power",
        "acquisition blocked", "takeover blocked", "deal cleared",
        "dma enforcement", "dma designation", "dma fine",
        "market investigation", "market study",
        "ftc sues", "ftc probe", "ftc fine", "doj antitrust",
        "cma probe", "cma fine", "cma ruling", "cma investigation",
        "cci probe", "cci fine", "cci order", "cci ruling",
        "cade probe", "cade fine", "cade ruling",
        "probed over", "fined for competition",
    ]),
    # ── 3. FINTECH & PAYMENTS ─────────────────────────────────────────────
    ("fintech", [
        "fintech regulation", "fintech law", "fintech fine", "fintech probe",
        "payment regulation", "payment fine", "payment ban", "payment law",
        "digital payments", "mobile payment", "instant payment",
        "open banking", "psd3", "psd2", "payment services",
        "bnpl regulation", "bnpl law", "bnpl fine", "buy now pay later",
        "digital lending", "online lending", "lending regulation",
        "neobank regulation", "neobank license", "digital bank regulation",
        "crypto regulation", "crypto law", "crypto fine", "crypto ban",
        "stablecoin", "cbdc", "defi regulation", "digital asset",
        "remittance regulation", "cross-border payment",
        "payment aggregator", "payment gateway regulation",
        "insurtech", "embedded finance", "open finance",
        "dora", "cfpb", "rbi payment", "rbi fintech",
        "bacen payment", "upi regulation", "npci",
        "paypal", "stripe", "revolut", "klarna", "wise transfer",
        "monzo", "nubank", "mercadopago", "razorpay", "phonepe",
        "paytm regulation", "paytm fine", "paytm ban",
        "payment fraud", "financial fraud", "money laundering fintech",
    ]),
    # ── 4. PLATFORM & GIG ECONOMY ─────────────────────────────────────────
    ("platform_gig", [
        "food delivery", "delivery app", "food platform", "meal delivery",
        "restaurant platform", "delivery marketplace",
        "uber eats", "doordash", "zomato", "talabat", "bolt food",
        "grubhub", "just eat", "delivery hero",
        "ride-hail", "ridesharing", "ride sharing",
        "mobility platform", "uber regulation", "uber fine", "uber sued",
        "grab regulation", "gojek", "ola regulation", "bolt taxi",
        "e-scooter regulation", "micro-mobility",
        "gig worker", "platform worker", "worker classification",
        "gig economy", "independent contractor", "self-employed platform",
        "algorithmic management", "algorithmic work",
        "platform work directive", "gig rights",
        "delivery rider", "courier rights", "driver rights",
        "worker misclassification", "employee status platform",
        "collective bargaining gig", "gig union",
        "digital services act", "dsa enforcement", "dsa fine",
        "online marketplace regulation", "marketplace liability",
        "platform liability", "intermediary liability", "vlop",
        "online safety", "online harms", "content moderation law",
        "seller liability", "product liability marketplace",
    ]),
    # ── 5. IP & BRAND PROTECTION ──────────────────────────────────────────
    ("ip_brand", [
        "trademark", "trade mark", "trademark infringement", "trademark fine",
        "trademark lawsuit", "trademark ruling", "trademark registration",
        "passing off", "brand impersonation", "brand infringement",
        "trade dress", "service mark",
        "copyright", "copyright infringement", "copyright lawsuit",
        "copyright fine", "copyright ruling", "fair use",
        "text and data mining", "neighbouring rights", "press publisher",
        "music copyright", "ai training data", "llm copyright",
        "book copyright", "image copyright", "database right",
        "patent", "patent infringement", "patent lawsuit", "patent ruling",
        "standard essential patent", "frand", "patent troll",
        "brand protection", "counterfeiting", "fake goods", "counterfeit",
        "product piracy", "anti-counterfeiting",
        "domain name", "cybersquatting", "typosquatting",
        "wipo", "inta", "euipo", "uspto",
        "trade secret", "misappropriation",
    ]),
    # ── 6. PRIVACY & DATA ─────────────────────────────────────────────────
    ("privacy_data", [
        "gdpr", "data protection", "privacy regulation", "privacy law",
        "privacy fine", "privacy violation", "privacy lawsuit",
        "data privacy", "dpdp act", "lgpd", "popia", "pdpa", "ccpa",
        "privacy shield", "adequacy decision", "data transfer",
        "data localisation", "data sovereignty", "data governance",
        "privacy watchdog", "data protection authority", "dpa fine",
        "ico fine", "cnil fine", "edpb ruling",
        "privacy enforcement", "data protection fine",
        "data breach", "data leak", "data hack", "data stolen",
        "personal data exposed", "user data sold",
        "surveillance", "facial recognition", "biometric data",
        "location tracking", "cookie consent", "cookie ban",
        "tracking ban", "ad tracking", "targeted advertising ban",
        "right to erasure", "right to be forgotten",
        "ai privacy", "ai surveillance", "training data privacy",
    ]),
    # ── 7. EMERGING MARKETS ───────────────────────────────────────────────
    ("emerging_markets", [
        "india tech", "india digital", "india startup", "india unicorn",
        "india regulation", "india antitrust", "india competition",
        "india fintech", "india payment", "india e-commerce",
        "india data", "india privacy", "india ai", "india gig",
        "india food delivery", "india internet", "india platform",
        "digital india", "cci ruling", "cci investigation",
        "rbi circular", "rbi guideline", "meity notification",
        "dpdp", "india data protection",
        "brazil tech", "brazil digital", "brazil startup",
        "brazil fintech", "brazil e-commerce", "brazil food delivery",
        "brazil antitrust", "brazil competition", "brazil data",
        "brazil ai", "brazil platform",
        "cade ruling", "cade investigation", "anpd ruling",
        "lgpd enforcement", "bacen digital", "pix payment",
        "south africa tech", "south africa fintech", "south africa digital",
        "south africa startup", "south africa competition",
        "turkey tech", "turkey fintech", "turkey digital",
        "turkey competition", "rekabet kurumu",
        "indonesia tech", "indonesia digital", "indonesia fintech",
        "ojk regulation", "indonesia competition",
        "pakistan tech", "pakistan fintech", "pakistan digital",
        "latin america tech", "latam fintech", "latam startup",
        "africa tech", "africa fintech", "africa startup",
        "nigeria tech", "kenya tech", "southeast asia tech",
    ]),
    # ── 8. POLICY & SOCIETY ───────────────────────────────────────────────
    ("policy_society", [
        "internet regulation", "digital regulation", "tech regulation",
        "digital economy", "platform economy", "app economy",
        "digital single market", "digital trade", "data economy",
        "tech policy", "digital policy", "internet policy",
        "tech law", "digital law", "internet law",
        "consumer protection", "dark pattern", "drip pricing",
        "fake reviews", "subscription trap", "misleading advertising",
        "age verification", "children online", "online safety children",
        "digital literacy", "digital inclusion", "digital divide",
        "algorithmic transparency", "explainable ai",
        "tech investment", "innovation policy", "regulatory sandbox",
        "digital infrastructure", "broadband regulation",
        "future of work", "automation jobs", "ai jobs",
        "digital tax", "tech tax", "digital services tax",
        "ai energy", "tech sustainability", "digital carbon",
    ]),
]


# Body scoring fallback
BODY_CAT_RULES = [
    ("ai_tech", [
        "artificial intelligence", "machine learning", "generative ai",
        "large language model", "foundation model", "ai model",
        "openai", "anthropic", "deepseek", "chatgpt", "llm",
        "ai regulation", "ai governance", "ai liability", "ai safety",
        "ai act", "gpai", "deepfake", "synthetic media",
        "ai copyright", "ai training data", "ai lawsuit", "ai fraud",
    ]),
    ("competition", [
        "antitrust", "competition law", "merger control", "cartel",
        "market investigation", "gatekeeper", "price fixing",
        "market dominance", "merger inquiry", "competition authority",
        "digital markets act", "abuse of dominance",
    ]),
    ("fintech", [
        "fintech", "payment regulation", "digital payments",
        "open banking", "bnpl", "buy now pay later",
        "digital lending", "neobank", "crypto regulation",
        "stablecoin", "remittance", "payment fine", "psd3",
    ]),
    ("platform_gig", [
        "food delivery", "gig worker", "platform worker",
        "worker classification", "ride-hail", "delivery app",
        "digital services act", "platform liability",
        "online marketplace", "algorithmic management",
        "content moderation", "intermediary liability",
    ]),
    ("ip_brand", [
        "trademark", "copyright", "patent", "intellectual property",
        "brand protection", "counterfeiting", "trade secret",
        "wipo", "fair use", "domain name", "cybersquatting",
        "copyright infringement", "trademark infringement",
    ]),
    ("privacy_data", [
        "gdpr", "data protection", "personal data", "data breach",
        "privacy law", "data leak", "surveillance", "biometric",
        "dpdp", "lgpd", "popia", "pdpa", "cookie",
        "data localisation", "privacy fine", "facial recognition",
    ]),
    ("emerging_markets", [
        "india", "brazil", "south africa", "turkey", "indonesia",
        "pakistan", "nigeria", "kenya", "latin america",
        "cci", "cade", "anpd", "rbi", "meity",
        "digital india", "pix payment", "upi",
    ]),
    ("policy_society", [
        "digital regulation", "tech regulation", "internet regulation",
        "consumer protection", "digital economy", "platform economy",
        "tech policy", "age verification", "children online",
        "digital tax", "innovation policy", "future of work",
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
    # India ecosystem (Prosus is deeply exposed — anything in this space matters)
    "paytm", "phonepe", "razorpay", "zepto", "blinkit", "dunzo",
    "zomato", "ola ", "nykaa", "groww", "zerodha", "cred ", "slice ",
    "byju", "unacademy", "vedantu", "upgrad", "classplus",
    "1mg", "netmeds", "practo", "tata 1mg",
    "flipkart", "snapdeal", "indiamart", "shopclues",
    "ola electric", "ather", "bounce infinity",
    "oyo", "zostel", "meru",
    "paisa bazaar", "policybazaar", "acko",
    "khatabook", "vyapar", "ofbusiness",
    "innovaccer", "healthifyme", "cure.fit",
    "inmobi", "moengage", "clevertap",
    "lenskart", "mamaearth", "boat ",
    # Brazil ecosystem
    "nubank", "mercado livre", "mercadolivre", "stone ", "totvs",
    "vtex", "movile", "locaweb", "rdstation",
    "99 app", "99taxi", "loggi", "lalamove brazil",
    "quinto andar", "loft ", "zap imoveis",
    "gympass", "zenvia", "neoway",
    # Africa ecosystem
    "safaricom", "mpesa", "m-pesa", "flutterwave", "paystack",
    "jumia", "konga", "sendwave", "chipper cash",
    "fincra", "mono ", "lendsqr", "cowrywise",
    "village capital", "techstars africa",
    # Indonesia / SE Asia
    "gojek", "tokopedia", "bukalapak", "traveloka",
    "grab ", "lazada", "shopee",
    # Turkey
    "trendyol", "getir", "hepsiburada", "n11 ",
    "yemeksepeti", "sahibinden",
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
    Tier-2: Title contains a Prosus-sector, litigation, enforcement, or market signal → relevant.
    Tier-3: Regulator/court/legislation + sector combo in full text → relevant.
    Tier-4: Competitor or adjacent company in a Prosus sector → relevant (sets precedent).
    Everything else → drop.
    """
    title = a["title"].lower()
    text  = (a["title"] + " " + a.get("body", "") + " " + " ".join(a.get("tags", []))).lower()

    # ── TIER 1: Direct portfolio entity ──────────────────────────────────────
    ENTITIES_LC = [e.lower() for e in PROSUS_ENTITIES]
    if any(kw in text for kw in ENTITIES_LC):
        return True

    # ── TIER 2: Title-level sector signals (broad) ───────────────────────────
    TITLE_SECTOR_KWS = [
        # AI — all Prosus AI investees affected (Zapia, Brainfish, Luzia, Advolve…)
        "ai act", "eu ai", "ai regulation", "ai law", "ai governance",
        "ai liability", "ai agent", "agentic ai", "generative ai",
        "large language model", "llm", "chatbot", "foundation model",
        "deepfake", "synthetic media", "voice cloning",
        "openai", "anthropic", "deepseek", "chatgpt", "gemini", "claude",
        "grok", "perplexity", "mistral", "cohere",
        "ai copyright", "ai lawsuit", "ai sued", "ai fined", "ai probe",
        "ai fraud", "ai impersonat", "ai defamat", "ai hallucin",
        # Fintech / payments (PayU, iyzico, LazyPay, Creditas, Tonik…)
        "fintech", "neobank", "digital bank", "payment regulation",
        "bnpl", "buy now pay later", "digital lending", "instant loan",
        "open banking", "payment app", "payment platform", "payment fine",
        "crypto regulation", "stablecoin", "defi regulation", "remittance",
        "digital wallet", "mobile payment", "payment fraud",
        "paypal", "stripe", "revolut", "klarna", "wise", "monzo",  # precedents
        # Food delivery (Swiggy, iFood, Delivery Hero, Just Eat, Rapido…)
        "food delivery", "delivery app", "food app", "food platform",
        "restaurant platform", "delivery platform", "meal delivery",
        "uber eats", "doordash", "zomato", "talabat", "bolt food",  # precedents
        # Gig / platform workers
        "gig worker", "platform worker", "worker classification",
        "gig economy", "algorithmic management", "algorithmic work",
        "independent contractor", "self-employed platform",
        "uber driver", "delivery rider", "courier rights",
        # E-commerce / marketplace (Meesho, OLX, eMAG, Shopup…)
        "e-commerce regulation", "online marketplace", "marketplace law",
        "marketplace liability", "platform liability", "seller liability",
        "digital services act", "dsa enforcement", " dma ", "dma fine",
        "amazon antitrust", "amazon sued", "amazon fine",  # precedents
        "flipkart", "snapdeal", "shopee",  # India/SEA competitors
        # Classifieds / property tech (OLX, AutoTrader, OtoDOM, Property24…)
        "classifieds", "property portal", "real estate platform",
        "auto classifieds", "used car platform", "property listing",
        # Edtech (Eruditus, Brainly, Platzi, GoodHabitz, Sololearn…)
        "edtech", "online education", "learning platform",
        "online course regulation", "e-learning law",
        # Healthtech (PharmEasy, Corti, VOA Health…)
        "online pharmacy", "digital health", "telemedicine",
        "healthtech regulation", "e-pharmacy", "digital prescription",
        # IP / brand protection (Tara's INTA domain — core focus)
        "trademark", "brand protection", "intellectual property",
        "copyright infringement", "ip enforcement", "domain name",
        "cybersquatting", "counterfeiting", "brand impersonat",
        "wipo", "inta", "trade mark", "passing off",
        # Privacy / data — broad; plain "privacy" is enough for the discourse
        "gdpr", "data protection", "privacy regulation", "privacy fine",
        "privacy law", "privacy ruling", "privacy lawsuit", "privacy violation",
        "privacy watchdog", "privacy probe", "privacy settlement",
        "privacy groups", "privacy rights", "digital privacy",
        "privacy tech", "privacy feature", "privacy tool",
        " privacy", "privacy ",          # plain word — catches most headlines
        "data breach", "data leak", "data hack", "data stolen", "data exposed",
        "data localisation", "data sovereignty", "data governance",
        "biometric", "facial recognition", "surveillance", "tracking ban",
        "cookie consent", "cookie law", "cookie ban",
        "age verification", "age-gating", "children online",
        "right to erasure", "right to be forgotten",
        "ico fine", "ico ruling", "ico investigation",
        "cnil fine", "cnil ruling", "edpb ruling", "edpb decision",
        "personal data", "user data", "location data",
        "data subject", "consent mechanism", "data transfer",
        # Competition / antitrust (broad — any market Prosus operates in)
        "antitrust", "competition fine", "competition probe", "competition law",
        "monopoly", "market dominance", "abuse of dominance",
        "merger blocked", "merger cleared", "merger probe", "merger fine",
        "cartel", "price fixing", "market sharing",
        # Lawsuits & enforcement — sector-agnostic litigation signals
        "class action", "lawsuit filed", "court rules", "court orders",
        "injunction", "damages awarded", "settlement reached",
        "sued by", "fined by", "ordered to pay", "penalty imposed",
        "enforcement action", "consent decree", "regulatory fine",
        # India (massive Prosus exposure — Swiggy, Meesho, PayU, Urban Company…)
        "india tech", "indian startup", "india digital", "india app",
        "india competition", "india antitrust", "india fintech",
        "india data", "india privacy", "india e-commerce",
        "india food delivery", "india gig", "india payment",
        "cci order", "cci fine", "cci probe", "cci ruling",
        "rbi fintech", "rbi payment", "rbi ban", "rbi guideline",
        "meity rule", "dpdp act", "india ai",
        # Brazil (iFood, OLX, Creditas, Azos…)
        "brazil tech", "brazil fintech", "brazil digital",
        "brazil competition", "brazil data", "brazil e-commerce",
        "brazil food delivery", "brazil payment", "brazil ai",
        "cade fine", "cade probe", "cade ruling", "lgpd fine",
        # South Africa (Naspers home market, TechCentral coverage)
        "south africa tech", "south africa fintech", "south africa digital",
        "south africa competition", "sacc ruling",
        # Netherlands / EU (HQ market, OLX, PayU, Dott…)
        "dutch tech", "netherlands fintech", "acm fine", "acm probe",
        "eu fine", "eu probe", "eu ruling", "eu court",
        # Turkey (iyzico)
        "turkey fintech", "turkey tech", "turkey competition",
        # Indonesia / Pakistan / emerging markets (Shipper, Bykea…)
        "indonesia tech", "indonesia fintech", "pakistan tech",
        # Key competitors that set direct precedent for Prosus opcos
        "uber", "grab", "gojek", "ola cab", "bolt taxi",  # ride/delivery
        "lazada", "tokopedia", "bukalapak",  # SEA e-commerce
        "nubank", "mercadopago", "mercadolivre",  # Brazil fintech
        "byju", "unacademy", "vedantu",  # India edtech
        "1mg", "netmeds", "practo",  # India healthtech
    ]

    if any(kw in title for kw in TITLE_SECTOR_KWS):
        return True

    # ── TIER 1b: Source-based fast-pass ──────────────────────────────────────
    source_lc = a.get("source", "").lower()

    # Pure specialist sources: every article is relevant by definition
    PURE_SPECIALIST = [
        "eff ", "electronic frontier", "cnil", "edpb", "future of privacy",
        "fpf", "hunton privacy", "inside privacy", "techgdpr", "mozilla privacy",
        "guardian privacy", "ip kat", "world trademark", "managing ip",
        "techcabal", "techloy", "techpoint africa", "inc42",
        "startups.com.br", "distrito",
        "oxford internet", "oii", "platform law", "worker info",
        "ai now institute", "fairwork", "fair.work",
    ]
    if any(s in source_lc for s in PURE_SPECIALIST):
        return True

    # Security/breach feeds: only pass if title has a privacy/data/law/company signal
    # (avoids ransomware-as-a-service, CVE, malware that have no Prosus angle)
    SECURITY_SOURCES = [
        "infosecurity", "dark reading", "bleepingcomputer", "databreaches",
        "cyberscoop", "the record", "krebs", "securityweek",
    ]
    PRIVACY_SIGNALS = [
        "breach", "leak", "exposed", "stolen", "scraped", "hacked",
        "privacy", "personal data", "user data", "gdpr", "data protection",
        "fine", "penalty", "lawsuit", "probe", "regulation", "law",
        "surveillance", "facial recognition", "biometric", "tracking",
        "ai ", "chatgpt", "openai", "meta ", "google ", "amazon ", "apple ",
        "microsoft", "tiktok", "facebook", "instagram", "linkedin",
        "healthcare data", "medical record", "patient data",
        "financial data", "bank data", "credit card data",
        "children data", "student data", "employee data",
    ]
    if any(s in source_lc for s in SECURITY_SOURCES):
        if any(sig in title for sig in PRIVACY_SIGNALS):
            return True

    # General tech sources with strong privacy/EM signal in title
    GENERAL_TECH = ["rest of world", "wired", "the verge", "vice"]
    EM_PRIVACY_SIGNALS = [
        "privacy", "data breach", "surveillance", "gdpr", "data protection",
        "india", "brazil", "africa", "nigeria", "kenya", "indonesia",
        "fintech", "gig", "platform worker",
    ]
    if any(s in source_lc for s in GENERAL_TECH):
        if any(sig in title for sig in EM_PRIVACY_SIGNALS):
            return True

    # ── TIER 2b: Thematic hooks in full text ─────────────────────────────────
    THEMES_LC = [t.lower() for t in THEMATIC_HOOKS]
    if any(kw in text for kw in THEMES_LC):
        return True

    # ── TIER 3: Regulator/court/legislation + sector in body ─────────────────
    PROSUS_SECTORS = [
        "food delivery", "delivery app", "restaurant platform",
        "fintech", "payment", "neobank", "digital lending", "bnpl",
        "edtech", "online education", "e-learning",
        "online pharmacy", "digital health", "telemedicine",
        "platform worker", "gig worker", "gig economy",
        "e-commerce", "online marketplace", "classifieds",
        "artificial intelligence", "generative ai", "llm", "chatbot",
        "trademark", "brand protection", "intellectual property",
        "platform liability", "content moderation",
        "big tech", "digital platform", "tech company",
        "data protection", "privacy", "personal data",
        "ride-hail", "ridesharing", "mobility platform",
    ]
    REGULATOR_NAMES = [kw.lower() for kw in REGULATORY_BODIES]
    if any(reg in text for reg in REGULATOR_NAMES):
        if any(sector in text for sector in PROSUS_SECTORS):
            return True

    # ── TIER 4: Litigation / enforcement language + sector ───────────────────
    LITIGATION_KWS = [
        "lawsuit", "sued", "court", "tribunal", "judge", "ruling",
        "verdict", "injunction", "damages", "settlement", "penalty",
        "fine", "enforcement", "investigation", "probe", "raid",
        "subpoena", "indictment", "charges filed", "complaint filed",
        "regulatory action", "enforcement notice", "cease and desist",
        "appeal", "class action", "collective action",
    ]
    if any(lit in text for lit in LITIGATION_KWS):
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

    ALL_CATS = ["ai_tech", "competition", "fintech", "platform_gig", "ip_brand", "privacy_data", "emerging_markets", "policy_society"]
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
    # Tab aliases for backward-compat with HTML pills
    categorised["ai_landscape"]       = categorised.get("ai_tech", [])
    categorised["chatbot"]            = categorised.get("ai_tech", [])
    categorised["chatbot_regulation"] = categorised.get("ai_tech", [])
    categorised["ai_agents"]          = categorised.get("ai_tech", [])
    categorised["gig_economy"]        = categorised.get("platform_gig", [])
    categorised["platform_liability"] = categorised.get("platform_gig", [])
    categorised["consumer_protection"]= categorised.get("policy_society", [])
    categorised["ip"]                 = categorised.get("ip_brand", [])
    categorised["privacy"]            = categorised.get("privacy_data", [])
    categorised["regulatory"]         = []  # no longer a catch-all

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
