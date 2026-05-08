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
MAX_AGE_DAYS = 30
TARGET_PER_CATEGORY = 40

# ── 50 VERIFIED RSS FEEDS ─────────────────────────────────────────────────
RSS_SOURCES = [

    # ══════════════════════════════════════════════════════════════════════
    # INDIA  — Prosus exposure: Swiggy, Meesho, PayU, Urban Company,
    #          PharmEasy, Rapido, GoStudent, Brainly, Ola Electric
    # ══════════════════════════════════════════════════════════════════════
    # General India tech
    ("MediaNama (India)",               "https://medianama.com/feed/"),
    ("Inc42 (India)",                   "https://inc42.com/feed/"),
    ("Economic Times Tech (India)",     "https://economictimes.indiatimes.com/tech/rssfeeds/13357270.cms"),
    ("LiveMint Tech (India)",           "https://www.livemint.com/rss/technology"),
    # India digital rights / privacy specialists
    ("SFLC India",                      "https://sflc.in/feed/"),
    ("Bar and Bench India",             "https://www.barandbench.com/feed"),

    # ══════════════════════════════════════════════════════════════════════
    # BRAZIL — Prosus exposure: iFood, OLX, Creditas, Azos, Remessa Online
    # ══════════════════════════════════════════════════════════════════════
    # General Brazil tech/policy
    ("Jota (Brazil law/policy)",        "https://www.jota.info/feed"),
    ("Telesintese (Brazil telecom)",    "https://www.telesintese.com.br/feed/"),
    ("Teletime (Brazil)",               "https://www.teletime.com.br/feed/"),
    ("Convergencia Digital (Brazil)",   "https://www.convergenciadigital.com.br/feed/"),
    ("Tecnoblog (Brazil)",              "https://tecnoblog.net/feed/"),
    ("TecMundo (Brazil)",               "https://rss.tecmundo.com.br/feed"),
    ("Startups.com.br",                 "https://startups.com.br/feed/"),
    ("Congresso em Foco (Brazil)",      "https://congressoemfoco.uol.com.br/feed/"),
    ("Politica Por Inteiro (Brazil)",   "https://www.politicaporinteiro.org/feed/"),

    # ══════════════════════════════════════════════════════════════════════
    # SOUTH AFRICA — Prosus home market via Naspers; OLX, TakeLot, Media24
    # ══════════════════════════════════════════════════════════════════════
    ("TechCentral (SA)",                "https://techcentral.co.za/feed/"),
    ("Moneyweb (SA)",                   "https://www.moneyweb.co.za/feed/"),
    ("Daily Maverick (SA)",             "https://www.dailymaverick.co.za/dmrss/"),
    ("Mail & Guardian (SA)",            "https://mg.co.za/feed/"),
    ("De Rebus SA law",                 "https://www.derebus.org.za/feed/"),
    ("CompCom South Africa",            "https://www.compcom.co.za/feed/"),
    ("Ventureburn (Africa)",            "https://ventureburn.com/feed/"),

    # ══════════════════════════════════════════════════════════════════════
    # EUROPE — HQ jurisdiction; GDPR, AI Act, DMA, DSA directly apply
    # ══════════════════════════════════════════════════════════════════════
    # EU regulators
    ("EDPB",                            "https://edpb.europa.eu/rss.xml"),
    ("CNIL (France)",                   "https://www.cnil.fr/en/rss.xml"),
    ("CMA (UK)",                        "https://www.gov.uk/search/all.atom?organisations%5B%5D=competition-and-markets-authority&order=updated-newest"),
    ("noyb (Schrems)",                  "https://noyb.eu/en/rss.xml"),
    # EU policy/law media
    ("EU Digital Strategy",             "https://digital-strategy.ec.europa.eu/en/rss.xml"),
    ("EU Law Live",                     "https://eulawlive.com/feed/"),
    ("Netzpolitik (EU digital rights)", "https://netzpolitik.org/feed/"),
    ("Politico EU",                     "https://www.politico.eu/feed/"),
    # UK
    ("The Register (UK)",               "https://www.theregister.com/headlines.atom"),
    ("Guardian Tech (UK)",              "https://www.theguardian.com/technology/rss"),
    ("Guardian Privacy (UK)",           "https://www.theguardian.com/world/privacy/rss"),
    ("BBC Technology (UK)",             "https://feeds.bbci.co.uk/news/technology/rss.xml"),

    # ══════════════════════════════════════════════════════════════════════
    # AFRICA (rest) — TechCabal / Techpoint / Techloy for Nigeria, Kenya, Ghana
    # ══════════════════════════════════════════════════════════════════════
    ("TechCabal (Africa)",              "https://techcabal.com/feed/"),
    ("Techloy (Africa)",                "https://techloy.com/feed/"),
    ("Techpoint Africa",                "https://techpoint.africa/feed/"),

    # ══════════════════════════════════════════════════════════════════════
    # GLOBAL PRIVACY & DIGITAL RIGHTS
    # ══════════════════════════════════════════════════════════════════════
    ("EFF Deeplinks",                   "https://www.eff.org/rss/updates.xml"),
    ("Future of Privacy Forum",         "https://fpf.org/feed/"),
    ("Hunton Privacy Blog",             "https://www.huntonprivacyblog.com/feed/"),
    ("TechGDPR",                        "https://techgdpr.com/blog/feed/"),
    ("Access Now",                      "https://www.accessnow.org/feed/"),
    ("Global Voices",                   "https://globalvoices.org/feed/"),
    ("Rest of World",                   "https://restofworld.org/feed/"),
    ("Article 19",                      "https://www.article19.org/feed/"),
    ("Platformer (Casey Newton)",       "https://www.platformer.news/feed"),
    ("Tech Policy Press",               "https://techpolicy.press/feed/"),
    ("The Rideshare Guy",               "https://therideshareguy.com/feed/"),
    ("Worker Info Exchange",            "https://www.workerinfoexchange.org/feed"),
    ("Gig Economy Data Hub",            "https://www.gigeconomydata.org/feed"),

    # ══════════════════════════════════════════════════════════════════════
    # CYBERSECURITY / DATA BREACHES (qualified gate — privacy angle only)
    # ══════════════════════════════════════════════════════════════════════
    ("Infosecurity Magazine",           "https://www.infosecurity-magazine.com/rss/news/"),
    ("Dark Reading",                    "https://www.darkreading.com/rss.xml"),
    ("CyberScoop",                      "https://cyberscoop.com/feed/"),
    ("The Record (cybersecurity)",      "https://therecord.media/feed"),
    ("Krebs on Security",               "https://krebsonsecurity.com/feed/"),

    # ══════════════════════════════════════════════════════════════════════
    # AI & EMERGING TECH
    # ══════════════════════════════════════════════════════════════════════
    ("AI Now Institute",                "https://ainowinstitute.org/feed"),
    ("The Decoder",                     "https://the-decoder.com/feed/"),
    ("404 Media",                       "https://www.404media.co/feed"),
    ("MIT Technology Review",           "https://www.technologyreview.com/feed/"),
    ("VentureBeat AI",                  "https://venturebeat.com/feed/"),
    ("Future of Life Institute",        "https://futureoflife.org/feed/"),

    # ══════════════════════════════════════════════════════════════════════
    # IP & BRAND PROTECTION
    # ══════════════════════════════════════════════════════════════════════
    ("IPKat",                           "https://ipkitten.blogspot.com/feeds/posts/default?alt=rss"),
    ("IP Watchdog",                     "https://ipwatchdog.com/feed/"),
    ("World Trademark Review",          "https://www.worldtrademarkreview.com/rss"),
    ("WIPO",                            "https://www.wipo.int/pressroom/en/rss.xml"),

    # ══════════════════════════════════════════════════════════════════════
    # COMPETITION LAW
    # ══════════════════════════════════════════════════════════════════════
    ("Chillin Competition",              "https://chillingcompetition.com/feed"),
    ("Global Competition Review",        "https://globalcompetitionreview.com/rss"),
    ("Competition Policy International", "https://www.competitionpolicyinternational.com/feed/"),
    ("Digital Regulation Platform",      "https://digitalregulation.org/feed/"),

    # ══════════════════════════════════════════════════════════════════════
    # FINTECH
    # ══════════════════════════════════════════════════════════════════════

    # ══════════════════════════════════════════════════════════════════════
    # GIG / PLATFORM WORKERS
    # ══════════════════════════════════════════════════════════════════════
    ("Oxford Internet Institute",       "https://www.oii.ox.ac.uk/feed/"),

    # ══════════════════════════════════════════════════════════════════════
    # BROAD TECH / INTERNATIONAL
    # ══════════════════════════════════════════════════════════════════════
    ("TechCrunch",                      "https://techcrunch.com/feed/"),
    ("Ars Technica",                    "https://feeds.arstechnica.com/arstechnica/technology-lab"),
    ("Wired",                           "https://www.wired.com/feed/rss"),
    ("Bloomberg Technology",            "https://feeds.bloomberg.com/technology/news.rss"),
    ("ZDNet Government",                "https://www.zdnet.com/topic/government/rss.xml"),
    ("Digital Watch Observatory",       "https://dig.watch/feed"),
]

# ── NOISE FILTERS ─────────────────────────────────────────────────────────
EXPLICIT_NOISE = [
    # Sport
    "box office", "cricket match", "football match", "urc race",
    # Consumer/gadget
    "recipe", "promo code", "discount code", "coupon code", "% off ",
    "best deals", "buying guide", "vs review",
    "launched in india", "mah battery", "snapdragon 8",
    "zeiss camera", "dimensity", "smartphone launch", "phone launch",
    "laptop deal", "macbook deal", "iphone 18",
    "tem desconto", "novo celular", "novo smartwatch",
    # Infrastructure (not regulatory)
    "power purchase agreement", "data center investment",
    "data centre investment", "data center capacity",
    "pops que podem virar", "eldorado do sul",
    "850 mhz", "roaming permanente", "pgmc",
    "white paper sobre recursos de órbita",
    # Pure consumer health/lifestyle
    "engaging healthcare professionals",
    # Telecom spectrum auctions (not policy)
    "adjudica lotes", "leilão de 700",
    "leilão de 850", "roaming permanente",
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
    # Infrastructure / hardware noise
    r"data cent(?:er|re)s?.{0,30}(?:eldorado|infraestrutura|estratégica|borda|us\$\s*\d)",
    r"\d+\s*(?:mil|thousand)\s*(?:pop|pops)\b",
    r"breakeven para \d{4}",
    r"tem desconto .{0,10}%",
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
        # Regional AI regulation
        "south africa ai", "ai bill south africa", "sa ai bill",
        "national ai policy south africa", "dtps ai",
        "india ai regulation", "india ai policy", "india ai bill",
        "india ai governance", "india ai framework",
        "meity ai", "ministry of electronics ai",
        "supreme court ai", "court cites ai", "ai expert panel",
        "ai cyberattack", "ai-powered cyberattack",
        "south africa developer", "risks losing developers",
        "ai impact summit", "india ai summit",
        "brazil ai", "lei de ia", "pl 2338", "marco legal da ia",
        "marco legal de inteligência", "inteligência artificial brasil",
        "projeto de lei ia", "senado ia", "câmara ia",
        "india artificial intelligence", "india algorithm",
        "ai white paper india", "ai consultation india",
        "european commission ai", "ec ai consultation",
        "eu ai office", "ai regulatory sandbox",
        "have your say ai", "public consultation ai",
        "ai impact assessment", "ai risk classification",
        # Arabic/Turkish/Indonesian AI regulation
        "uae ai", "saudi ai", "turkey ai", "indonesia ai",
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
        # ── Meta / WhatsApp / messaging AI ───────────────────────────────────
        "whatsapp ai", "whatsapp terms", "whatsapp policy", "whatsapp privacy",
        "whatsapp data", "whatsapp encryption", "whatsapp ban",
        "whatsapp regulation", "whatsapp fine", "whatsapp lawsuit",
        "meta ai terms", "meta ai policy", "meta ai regulation",
        "meta ai training", "meta terms of service", "meta terms change",
        "instagram ai", "facebook ai terms", "meta data policy",
        "messenger ai", "signal regulation", "telegram regulation",
        "telegram ban", "telegram fine", "messaging app regulation",
        "end-to-end encryption law", "chat control", "e2e encryption ban",
    ]),
    # ── 2. COMPETITION & MARKETS ──────────────────────────────────────────
    ("competition", [
        # Core antitrust
        "antitrust", "merger inquiry", "merger control", "merger probe",
        "merger blocked", "merger cleared", "merger fine", "merger review",
        "cartel", "price fixing", "market sharing", "bid rigging",
        "competition fine", "competition probe", "competition authority",
        "competition watchdog", "competition law", "competition ruling",
        "market dominance", "abuse of dominance", "dominant position",
        "monopoly", "oligopoly", "market power",
        "acquisition blocked", "takeover blocked", "deal cleared",
        "market investigation", "market study", "market inquiry",
        # Key regulators
        "ftc sues", "ftc probe", "ftc fine", "doj antitrust",
        "cma probe", "cma fine", "cma ruling", "cma investigation",
        "cci probe", "cci fine", "cci order", "cci ruling",
        "cci approval", "cci seeks", "cci clears", "cci blocks",
        "cade probe", "cade fine", "cade ruling", "cade aprovação",
        "competition commission south africa", "competition tribunal south africa",
        "rekabet kurumu", "kppu", "accc",
        "probed over", "fined for competition",
        # ── DMA / Digital Markets Act ───────────────────────────────────────────
        "digital markets act", "dma enforcement", "dma gatekeeper",
        "dma compliance", "dma fine", "dma interoperability",
        "dma self-preferencing", "dma designation", "dma investigation",
        "dma non-compliance", "core platform service",
        "dma ruling", "dma obligation", "dma decision",
        # ── Global digital markets regimes ───────────────────────────────────
        "dmcc act", "digital markets competition consumers",
        "strategic market status", "sms designation",
        "pro-competition intervention", "designated activity",
        "australia digital platform", "australia cdmo",
        "korea platform monopoly", "korea pmfp",
        "japan digital platform", "japan platform regulation",
        "india digital competition", "india competition amendment",
        "india digital competition act", "india dca",
        "digital markets regime", "ex ante regulation",
        "platform regulation competition",
        # ── Ecosystem / conglomerate mergers ────────────────────────────────────
        "ecosystem competition", "conglomerate merger", "digital ecosystem",
        "platform ecosystem", "tech merger", "digital merger",
        "killer acquisition", "acqui-hire", "nascent competitor",
        "potential competition merger", "portfolio effects",
        "dynamic competition", "innovation competition",
        "gatekeeper", "self-preferencing", "tipping market",
        "winner takes all", "network effects competition",
        "data advantage competition", "data moat",
        # ── Algorithmic pricing & collusion ───────────────────────────────────
        "algorithmic pricing", "algorithmic collusion", "pricing algorithm",
        "algorithmic tacit collusion", "hub and spoke algorithm",
        "ai pricing antitrust", "dynamic pricing antitrust",
        "algorithmic cartel", "ai collusion",
        # ── App stores / interoperability ─────────────────────────────────────
        "app store competition", "app store antitrust", "app store ruling",
        "app store fine", "apple app store ruling", "apple app store fine",
        "google play antitrust", "in-app payment antitrust",
        "interoperability obligation", "app store fee",
        "sideloading", "alternative app store",
        # ── European Champions / industrial policy debate ──────────────────────
        "european champion", "industrial policy competition",
        "merger policy reform europe", "eu merger guidelines",
        "european merger reform", "competition industrial policy",
        "eu merger policy", "eu competition reform",
        "rethinking merger", "merger policy debate",
        # ── Food delivery / classifieds / Prosus sector M&A ───────────────────
        "food delivery merger", "delivery platform acquisition",
        "food delivery acquisition", "food platform merger",
        "classifieds merger", "property portal merger",
        "online marketplace acquisition", "marketplace merger",
        "fintech acquisition blocked", "edtech merger",
        "healthtech acquisition", "tech merger blocked",
        # ── Regional geo+topic combos ─────────────────────────────────────────
        "india merger", "india acquisition antitrust",
        "brazil merger", "brazil acquisition cade",
        "south africa merger", "south africa competition",
        "turkey competition", "indonesia competition",
        "africa competition", "kenya competition",
        "nigeria competition authority",
    ]),
    # ── 3. FINTECH & PAYMENTS ─────────────────────────────────────────────
    ("fintech", [
        "fintech regulation", "fintech law", "fintech fine", "fintech probe",
        "fintech licensing", "fintech compliance", "fintech enforcement",
        "payment regulation", "payment fine", "payment ban", "payment law",
        "payment compliance", "payment enforcement", "payment license",
        "digital payments", "mobile payment", "instant payment",
        "open banking", "psd3", "psd2", "payment services directive",
        "bnpl regulation", "bnpl law", "bnpl fine", "buy now pay later",
        "bnpl crackdown", "bnpl ban", "bnpl probe",
        "digital lending", "online lending", "lending regulation",
        "lending ban", "lending crackdown", "predatory lending",
        "neobank regulation", "neobank license", "digital bank regulation",
        "digital bank fine", "digital bank ban",
        "crypto regulation", "crypto law", "crypto fine", "crypto ban",
        "stablecoin", "cbdc", "defi regulation", "digital asset",
        "crypto enforcement", "crypto crackdown", "crypto compliance",
        "remittance regulation", "cross-border payment",
        "payment aggregator", "payment gateway regulation",
        "insurtech", "embedded finance", "open finance",
        "dora", "cfpb", "rbi payment", "rbi fintech", "rbi crackdown",
        "bacen payment", "upi regulation", "npci", "pix payment",
        "sebi fintech", "irdai", "irda regulation",
        # Prosus portfolio — fintech companies
        "payu", "iyzico", "wibmo", "red dot payment", "tonik bank",
        "paysense", "lazypay", "remitly", "bux fintech", "bibit",
        "endowus", "thndr", "klar fintech", "creditas", "iniciador",
        # Competitor fintech
        "paypal", "stripe", "revolut", "klarna", "wise transfer",
        "monzo", "nubank", "mercadopago", "razorpay", "phonepe",
        "paytm", "paytm regulation", "paytm fine", "paytm ban",
        "payment fraud", "financial fraud", "money laundering fintech",
        "anti-money laundering fintech", "aml fintech",
        # Africa fintech
        "m-pesa", "mpesa", "safaricom payment", "mobile money",
        "africa payment", "africa fintech", "kenya payment",
        "nigeria fintech", "ghana payment", "flutterwave", "fincra",
        "opay", "moniepoint", "wave mobile money",
        # Credit / lending platforms
        "credit marketplace", "digital credit", "digital lending india",
        "india fintech", "india payment", "india digital banking",
        "india upi", "india neobank",
    ]),
    # ── 4. PLATFORM & GIG ECONOMY ─────────────────────────────────────────
    ("platform_gig", [
        # ── Prosus food delivery portfolio — any mention is relevant ──────────
        "ifood", "just eat", "just eat takeaway", "delivery hero", "swiggy",
        "swiggy regulation", "swiggy fine", "swiggy ipo", "swiggy probe",
        "ifood regulation", "ifood fine", "ifood probe", "ifood competition",
        # ── All food delivery (sector context) ───────────────────────────────
        "food delivery", "food delivery regulation", "food delivery law",
        "food delivery fine", "food delivery probe", "food delivery ban",
        "delivery app", "food platform", "meal delivery",
        "restaurant platform", "delivery marketplace",
        "uber eats", "doordash", "zomato", "talabat", "bolt food",
        "grubhub", "rappi", "glovo", "foodpanda", "wolt",
        "chowdeck", "jumia food",
        # ── Prosus classifieds / OLX portfolio ───────────────────────────────
        "olx", "autotrader", "otomoto", "otodom", "property24",
        "imovirtual", "autovit", "standvirtual", "storia",
        # ── Ride-hailing ──────────────────────────────────────────────────────
        "ride-hail", "ridesharing", "ride sharing", "ridehailing",
        "mobility platform", "ride app",
        "uber regulation", "uber fine", "uber sued", "uber ban", "uber ruling",
        "uber ipo", "uber competition", "grab regulation", "gojek",
        "ola regulation", "ola cab", "bolt taxi", "rapido",
        "e-scooter regulation", "micro-mobility regulation", "dott scooter",
        # ── Gig & platform workers (core regulatory focus) ────────────────────
        "gig worker", "platform worker", "worker classification",
        "gig economy", "gig economy regulation", "gig economy law",
        "gig economy fine", "gig economy probe",
        "independent contractor", "self-employed platform",
        "algorithmic management", "algorithmic work", "algorithmic boss",
        "platform work directive", "eu platform work", "gig rights",
        "gig worker rights", "delivery rider rights", "courier rights",
        "driver rights", "driver misclassification",
        "worker misclassification", "employee status platform",
        "collective bargaining gig", "gig union", "platform union",
        "social protection gig", "gig benefits", "minimum wage delivery",
        "AB5", "worker reclassification", "bogus self-employment",
        "freelancer law", "freelancer regulation",
        # ── Online marketplace / DSA / platform liability ─────────────────────
        "digital services act", "dsa enforcement", "dsa fine", "dsa compliance",
        "dsa designation", "vlop", "very large online platform",
        "online marketplace regulation", "marketplace liability",
        "platform liability", "intermediary liability",
        "online safety", "online harms act", "online safety act",
        "content moderation law", "content moderation fine",
        "seller liability", "product liability marketplace",
        "e-commerce regulation", "marketplace rules", "e-commerce law",
        # ── Consumer / platform harms ─────────────────────────────────────────
        "dark pattern", "deceptive design", "addictive design",
        "platform addiction", "recommender system regulation",
        "algorithm transparency platform", "feed algorithm law",
        "consumer protection platform", "subscription trap",
        "fake reviews regulation", "fake reviews fine",
        # ── Platform impersonation / fraud ────────────────────────────────────
        "platform fraud", "restaurant impersonation", "fake restaurant",
        "ghost kitchen fraud", "brand impersonation platform",
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
        # GDPR / EU core
        "gdpr", "data protection", "privacy regulation", "privacy law",
        "privacy fine", "privacy violation", "privacy lawsuit",
        "privacy ruling", "privacy probe", "privacy settlement",
        "privacy watchdog", "data protection authority", "dpa fine",
        "ico fine", "ico ruling", "ico investigation", "ico enforcement",
        "cnil fine", "cnil ruling", "edpb ruling", "edpb decision",
        "edpb opinion", "edpb guidelines",
        "noyb", "schrems", "privacy shield", "adequacy decision",
        "data transfer", "standard contractual clause", "scc",
        # US privacy
        "state privacy law", "state privacy act", "cpra", "ccpa",
        "federal privacy", "us privacy law", "ftc privacy",
        "ftc data", "ftc fine", "ftc action",
        "maryland privacy", "texas privacy", "virginia privacy",
        "children privacy", "coppa", "kids online safety",
        # India privacy
        "dpdp", "dpdp act", "dpdp rules", "dpdp regulations",
        "digital personal data protection",
        "india data protection", "india privacy",
        "india data law", "india data rules",
        "meity data", "meity privacy",
        "data fiduciary", "data principal",
        "consent manager", "data protection board india",
        # Brazil privacy
        "lgpd", "anpd", "brazil data", "brazil privacy",
        "lei geral de proteção de dados",
        "autoridade nacional de proteção",
        "proteção de dados", "privacidade", "dados pessoais",
        "vazamento de dados", "lei de dados",
        # South Africa privacy
        "popia", "popi act", "south africa data", "sa data protection",
        "information regulator south africa",
        "popia compliance", "popia fine", "popia enforcement",
        # Other regions
        "pdpa", "appi", "pipl", "turkey data", "turkey privacy",
        "indonesia data protection", "pdp law",
        "kenya data protection", "nigeria data protection",
        "ghana data protection", "rwanda data",
        # Data breaches
        "data breach", "data leak", "data hack", "data stolen",
        "data exposed", "records exposed", "personal data exposed",
        "user data sold", "database exposed", "customer data leaked",
        "health data breach", "medical data leak", "patient data",
        "biometric data breach", "financial data breach",
        # Surveillance / tracking
        "surveillance", "facial recognition", "biometric regulation",
        "location tracking", "cookie consent", "cookie ban",
        "tracking ban", "ad tracking", "targeted advertising ban",
        "right to erasure", "right to be forgotten",
        "data localisation", "data sovereignty", "data governance",
        # AI & privacy
        "ai privacy", "ai surveillance", "training data privacy",
        "ai data protection", "llm privacy", "scraping ban",
        "synthetic data regulation", "deepfake privacy",
        # General enforcement language
        "privacy enforcement", "data protection fine",
        "privacy class action", "privacy collective action",
        "privacy settlement", "privacy penalty",
        # Key enforcers making news
        "ico ", "cnil ", "garante ", "datatilsynet",
        "dpc ireland", "data protection commission",
        "hamburger dpa", "spanish aepd", "italian garante",
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
        "food delivery", "delivery app", "delivery rider", "delivery platform",
        "gig worker", "platform worker", "worker classification",
        "gig economy", "gig rights", "courier rights", "driver rights",
        "worker misclassification", "employee status", "bogus self-employed",
        "ride-hail", "ridesharing", "ride app", "uber", "grab", "gojek", "ola",
        "just eat", "delivery hero", "ifood", "swiggy", "zomato", "talabat",
        "grubhub", "doordash", "rappi", "glovo", "wolt",
        "digital services act", "dsa enforcement", "vlop",
        "platform liability", "online marketplace", "marketplace liability",
        "intermediary liability", "content moderation",
        "algorithmic management", "dark pattern",
        "platform work directive", "ab5", "minimum wage gig",
    ]),
    ("ip_brand", [
        "trademark", "copyright", "patent", "intellectual property",
        "brand protection", "counterfeiting", "trade secret",
        "wipo", "fair use", "domain name", "cybersquatting",
        "copyright infringement", "trademark infringement",
    ]),
    ("privacy_data", [
        # English
        "gdpr", "data protection", "personal data", "data breach",
        "privacy law", "privacy fine", "privacy ruling", "privacy probe",
        "data leak", "surveillance", "biometric", "facial recognition",
        "dpdp", "lgpd", "popia", "pdpa", "cookie", "tracking",
        "data localisation", "privacy enforcement", "ico", "cnil", "edpb",
        "noyb", "schrems", "right to erasure", "data transfer",
        "privacy watchdog", "data protection authority",
        "privacy class action", "privacy collective action",
        "age verification", "children online safety", "cookie consent",
        # Portuguese (Brazil)
        "proteção de dados", "privacidade", "lgpd", "anpd",
        "dados pessoais", "vazamento de dados", "lei de dados",
        # Indian context
        "dpdp act", "digital personal data", "india data protection",
        # SA context
        "popia", "information regulator", "popi",
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
    # Brazil — competition + privacy + AI regulation
    "cade ", "cade aprovação", "cade condena", "cade multa", "cade probe",
    "anpd ", "lgpd", "brazil data protection", "brazil privacy",
    "bacen ", "banco central do brasil", "anatel ",
    "pl 2338", "marco legal da ia", "marco legal de inteligência",
    "projeto de lei de inteligência artificial",
    "senado federal ia", "câmara dos deputados ia",
    "proteção de dados brasil", "lei de ia brasil",
    # Netherlands / EU
    "acm investigation", "acm fine", "acm ruling", "dutch competition",
    "digital markets act", "dma enforcement", "dma designation",
    "digital services act", "dsa enforcement", "dsa fine",
    "eu ai act", "ai act", "gpai regulation",
    "edpb", "eu data protection board", "gdpr fine", "gdpr enforcement",
    # South Africa — competition + privacy + AI regulation
    "competition commission south africa",
    "competition tribunal south africa",
    "south africa competition",
    "information regulator south africa",
    "popia", "popi act", "south africa data protection",
    "south africa ai bill", "national ai policy south africa",
    "department of communications south africa", "dcdt south africa",
    "dtps south africa", "cybercrimes act south africa",
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
        # India-specific privacy / AI regulation
        "dpdp", "dpdp act", "dpdp rules", "dpdp regulation",
        "digital personal data protection",
        "data protection board", "data fiduciary",
        "meity data", "meity privacy", "meity ai",
        "india ai regulation", "india ai policy", "india ai bill",
        "india ai governance", "it rules india", "it amendment rules",
        # Brazil-specific privacy / AI regulation
        "lgpd", "anpd", "lei geral de proteção",
        "proteção de dados", "privacidade", "dados pessoais",
        "pl 2338", "marco legal da ia", "marco legal de inteligência",
        "projeto de lei ia", "senado ia",
        "inteligência artificial brasil",
        # South Africa-specific privacy / AI regulation
        "popia", "popi act", "information regulator",
        "south africa ai bill", "sa ai bill", "ai bill south africa",
        "national ai policy", "dtps ai", "dcdt ai",
        "cybercrimes act", "electronic communications act",
        # EU consultations and Have Your Say
        "have your say", "public consultation", "open consultation",
        "call for evidence", "impact assessment eu",
        "european commission consultation",
        "regulatory consultation", "stakeholder consultation",
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

    # ── SOURCE TRUST MODEL ────────────────────────────────────────────────────
    # All RSS_SOURCES are curated specialist/regional feeds.
    # Trust the source selection — don't second-guess it with a keyword gate.
    # The noise filter (is_noise) already strips gadget reviews, earnings, etc.
    # Only apply light additional filtering for the highest-volume general sources.

    source_lc = a.get("source", "").lower()

    # ── PURE SPECIALISTS: always pass ────────────────────────────────────────
    # These sources publish nothing but regulatory/policy/rights content
    ALWAYS_PASS = [
        "eff ", "electronic frontier", "cnil", "edpb", "datatilsynet",
        "future of privacy", "fpf", "hunton privacy", "techgdpr",
        "noyb", "access now", "guardian privacy", "article 19",
        "algorithmwatch", "global voices", "sflc", "medianama",
        "bar and bench", "live law", "jota", "de rebus",
        "daily maverick", "mail & guardian",
        "ip kat", "ipkat", "world trademark", "ip watchdog",
        "oxford internet", "ai now institute", "worker info",
        "techcabal", "techloy", "techpoint africa", "inc42",
        "startups.com.br", "ventureburn", "rest of world",
        "chillin competition", "global competition review",
        "cma ", "eu law live", "eu digital strategy",
        "digital watch", "tech policy press", "platformer",
        "euractiv", "netzpolitik", "politico eu",
        "compcom south africa",
    ]
    if any(s in source_lc for s in ALWAYS_PASS):
        return True

    # ── SECURITY FEEDS: require privacy/enforcement signal ───────────────────
    SECURITY_SOURCES = [
        "infosecurity", "dark reading", "cyberscoop",
        "the record", "krebs",
    ]
    SECURITY_SIGNALS = [
        "breach", "leak", "exposed", "stolen", "scraped", "hacked",
        "privacy", "personal data", "gdpr", "fine", "penalty",
        "lawsuit", "regulation", "surveillance", "biometric",
    ]
    if any(s in source_lc for s in SECURITY_SOURCES):
        return any(sig in title for sig in SECURITY_SIGNALS)

    # ── VOLUME SOURCES: broad tech but high noise — require topic signal ─────
    # (ET Tech, LiveMint, Bar & Bench, Bloomberg, Wired, Register etc.)
    # Anything from a topic-relevant angle passes; gadget/consumer drops to noise filter
    VOLUME_SOURCES = [
        "economic times tech", "livemint", "bloomberg technology",
        "the register", "ars technica", "techcrunch", "zdnet",
        "bbc technology", "guardian tech", "wired",
        "mit technology review", "venturebeat", "404 media",
        "telesintese", "teletime", "tecnoblog", "tecmundo",
        "convergencia digital", "techtudo",
        "techcentral", "moneyweb",
    ]
    TOPIC_SIGNALS = [
        "regulation", "regulat", "law", "legal", "court", "ruling",
        "fine", "ban", "probe", "investigat", "enforcement",
        "privacy", "data protect", "breach", "surveillance",
        "ai govern", "ai act", "ai regulation", "ai law", "ai policy",
        "ai fraud", "ai scam", "ai deepfake", "ai impersonat",
        "antitrust", "competition", "merger", "monopol",
        "intellectual property", "copyright", "trademark", "patent",
        "fintech", "payment", "crypto", "bnpl", "digital bank",
        "gig worker", "platform worker", "delivery rider",
        "platform liability", "content moderation", "online safety",
        "gdpr", "dpdp", "lgpd", "popia", "pdpa",
        "cci ", "cade ", "rbi ", "meity", "anpd",
        "musk", "x corp", "meta ", "google ", "apple ", "microsoft ",
        "openai", "anthropic", "chatgpt", "deepseek", "gemini",
        "encryption", "backdoor", "child safety online",
        "digital tax", "digital services tax",
    ]
    if any(s in source_lc for s in VOLUME_SOURCES):
        return any(sig in title for sig in TOPIC_SIGNALS)

    # ── EVERYTHING ELSE: trust the source curation, pass it ──────────────────
    return True


def categorise(a):
    text = (a["title"] + " " + a["body"]).lower()
    title = a["title"].lower()
    # Title match wins — first match in priority order
    for cat, kws in TITLE_CAT_RULES:
        if any(kw in title for kw in kws):
            return cat
    # Body scoring fallback — need ≥2 signals for privacy_data to avoid false positives
    # (e.g. "data" alone from a data-centre or telecom article)
    best_cat, best_score = "regulatory", 0
    for cat, kws in BODY_CAT_RULES:
        score = sum(1 for kw in kws if kw in text)
        min_score = 2 if cat == "privacy_data" else 1
        if score >= min_score and score > best_score:
            best_score, best_cat = score, cat
    return best_cat


# ── HELPERS ───────────────────────────────────────────────────────────────

def uid(title, date):
    return hashlib.md5((title + date).lower().encode()).hexdigest()[:10]

def fetch(url):
    try:
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"}, timeout=14)
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

COMMON_ENGLISH = {"clarity", "corti", "aruna", "azos", "agito", "letgo", "dott", "bykea"}

def match_entities(a):
    # Use original case title+body for common-word disambiguation
    raw_text = (a["title"] + " " + a["body"])
    text = raw_text.lower()
    matches = []
    # Merge config entities + scraper's own PROSUS_ENTITIES list for broader coverage
    combined = list(dict.fromkeys(ALL_ENTITIES + PROSUS_ENTITIES))
    for e in combined:
        el = e.lower()
        # Skip very common English words unless capitalised as a brand
        if el in COMMON_ENGLISH:
            if not re.search(r"\b" + re.escape(e) + r"\b", raw_text):
                continue
        # Short names (≤6 chars) need word-boundary match
        if len(el) <= 6:
            if re.search(r"\b" + re.escape(el) + r"\b", text):
                matches.append(e)
        else:
            if el in text:
                matches.append(e)
    return list(dict.fromkeys(matches))  # deduplicate

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

def prosus_relevance(a):
    """
    Generate a short rule-based Prosus relevance note for every article.
    No API call — uses category, entity matches, title signals.
    Returns a string of 1-2 sentences, max ~180 chars.
    """
    cat   = a.get("category", "")
    title = a.get("title", "").lower()
    body  = a.get("body", "").lower()
    text  = title + " " + body
    ents  = a.get("entity_match", [])
    port  = ", ".join(ents[:2]) if ents else None

    # ── Portfolio direct hit ──────────────────────────────────────────────
    if port:
        base = f"Directly affects Prosus portfolio: {port}."
        if "fine" in text or "penalty" in text:
            return base + " Potential compliance and financial exposure."
        if "merger" in text or "acquisition" in text or "takeover" in text:
            return base + " Watch for regulatory clearance implications."
        if "ban" in text or "blocked" in text or "prohibited" in text:
            return base + " Operational continuity risk."
        return base + " Monitor for strategic and compliance impact."

    # ── AI & Policy ───────────────────────────────────────────────────────
    if cat == "ai_tech":
        if any(k in text for k in ["eu ai act", "ai act", "ai liability"]):
            return ("EU AI Act obligations apply to Prosus AI products including Ema "
                    "and Brainfish. High-risk classification rules may require conformity assessments.")
        if any(k in text for k in ["deepfake", "synthetic media", "voice cloning", "impersonat"]):
            return ("AI-generated fraud and impersonation directly threaten Prosus brands — "
                    "iFood, OLX, PayU and classifieds platforms are prime targets.")
        if any(k in text for k in ["agentic", "ai agent", "autonomous ai"]):
            return ("Agentic AI regulation will shape how Ema (Prosus AI employee product) "
                    "can be deployed across markets.")
        if any(k in text for k in ["copyright", "training data", "llm scraping"]):
            return ("AI training data rules affect Prosus AI ventures including Ema, "
                    "Brainfish, and Brainly's content-based model.")
        if "openai" in text or "anthropic" in text or "google" in text or "microsoft" in text:
            return ("Big-tech AI moves set the competitive context for Prosus AI portfolio "
                    "companies including Ema, Brainfish, and GoStudent.")
        return ("AI policy shifts affect Prosus's AI-first ventures (Ema, Brainfish, Advolve.AI) "
                "and AI-integrated opcos across edtech, healthtech and food delivery.")

    # ── Competition / Antitrust ───────────────────────────────────────────
    if cat == "competition":
        if any(k in text for k in ["dma", "digital markets act", "gatekeeper"]):
            return ("DMA enforcement shapes the operating environment for iFood, Just Eat, "
                    "OLX and PayU as downstream users of gatekeeper platforms.")
        if any(k in text for k in ["merger", "acquisition", "takeover", "m&a"]):
            return ("Merger precedents inform Prosus's own M&A strategy and portfolio "
                    "exit/consolidation decisions across the portfolio.")
        if any(k in text for k in ["food delivery", "ifood", "just eat", "delivery hero", "swiggy"]):
            return ("Competition enforcement in food delivery directly affects iFood (Brazil), "
                    "Just Eat Takeaway and Swiggy valuations and market structure.")
        if any(k in text for k in ["algorithmic", "pricing algorithm", "dynamic pricing"]):
            return ("Algorithmic pricing scrutiny applies to iFood, PayU and OLX, "
                    "all of which use dynamic or algorithmic pricing.")
        if any(k in text for k in ["app store", "apple", "google play"]):
            return ("App store rulings affect distribution costs for all Prosus "
                    "mobile-first opcos — iFood, Swiggy, PayU, eMAG and classifieds apps.")
        if any(k in text for k in ["classifieds", "marketplace", "olx", "property portal"]):
            return ("Marketplace competition rules directly affect OLX Group's "
                    "classifieds and property portal network across 30+ markets.")
        return ("Competition enforcement trends shape Prosus portfolio M&A strategy "
                "and the regulatory risk profile of opcos in food delivery, classifieds and fintech.")

    # ── Privacy & Data ────────────────────────────────────────────────────
    if cat == "privacy_data":
        if any(k in text for k in ["dpdp", "india data", "india privacy"]):
            return ("India DPDP rules apply to Meesho, Swiggy, Rapido, Urban Company "
                    "and all Prosus India opcos processing personal data of Indian citizens.")
        if any(k in text for k in ["lgpd", "anpd", "brazil data", "brazil privacy"]):
            return ("Brazil LGPD enforcement directly affects iFood and Creditas, "
                    "Prosus's largest LatAm opcos handling millions of user records.")
        if any(k in text for k in ["popia", "south africa data", "information regulator"]):
            return ("POPIA compliance is mandatory for Prosus SA opcos including "
                    "Takealot, Media24 and Property24.")
        if any(k in text for k in ["gdpr", "ico", "edpb", "cnil", "dpa fine"]):
            return ("GDPR enforcement applies to all Prosus EU operations — "
                    "Just Eat Takeaway, OLX Group, Dott and Amsterdam HQ staff data.")
        if "breach" in text or "leak" in text:
            return ("Data breach incidents set enforcement precedents relevant to "
                    "Prosus's consumer-facing opcos across food, classifieds and fintech.")
        return ("Data protection rules affect every Prosus consumer opco. "
                "India (DPDP), Brazil (LGPD), South Africa (POPIA) and EU (GDPR) are primary exposure markets.")

    # ── IP & Brand ────────────────────────────────────────────────────────
    if cat == "ip_brand":
        if any(k in text for k in ["ai trademark", "ai copyright", "llm trademark", "ai brand"]):
            return ("AI-generated brand infringement is a live threat for iFood, OLX and PayU — "
                    "platforms with high brand equity and significant fake-seller exposure.")
        if any(k in text for k in ["deepfake", "impersonat", "fake brand", "brand fraud"]):
            return ("Brand impersonation via AI directly threatens Prosus consumer brands. "
                    "Relevant to Tara Harris's INTA session on GenAI and agentic fraud.")
        if any(k in text for k in ["domain", "cybersquat", "brand hijack"]):
            return ("Domain and brand hijacking affects iFood, OLX and PayU "
                    "which operate localised brand variants across 50+ markets.")
        if any(k in text for k in ["trademark filing", "trademark registration", "ip filing"]):
            return ("Trademark trends inform Prosus IP strategy for portfolio brands "
                    "expanding into new markets.")
        return ("IP and brand protection rules affect Prosus's global brand portfolio — "
                "iFood, OLX, PayU, Swiggy and 40+ localised opco brands.")

    # ── Fintech ───────────────────────────────────────────────────────────
    if cat == "fintech":
        if any(k in text for k in ["payu", "iyzico", "wibmo", "red dot"]):
            return ("Directly affects PayU group — Prosus's global payments platform "
                    "operating across India, Europe, Africa and LatAm.")
        if any(k in text for k in ["upi", "rbi", "india payment", "india fintech"]):
            return ("RBI and UPI rules directly govern PayU India and LazyPay, "
                    "Prosus's largest regulated fintech entities.")
        if any(k in text for k in ["bnpl", "buy now pay later", "digital lending"]):
            return ("BNPL regulation affects LazyPay (India) and PaySense, "
                    "Prosus's consumer credit products.")
        if any(k in text for k in ["pix", "bacen", "brazil payment"]):
            return ("Brazil payment regulation affects iFood's payment stack "
                    "and Creditas's lending operations.")
        if any(k in text for k in ["crypto", "stablecoin", "cbdc"]):
            return ("Crypto and CBDC rules reshape the competitive environment "
                    "for PayU and Prosus's digital banking investments.")
        if any(k in text for k in ["mobile money", "m-pesa", "africa payment"]):
            return ("African mobile money regulation affects Prosus's fintech "
                    "investments across Nigeria, Kenya and South Africa.")
        return ("Fintech regulation affects PayU, iyzico, LazyPay, Creditas "
                "and Prosus's broader payments and lending portfolio.")

    # ── Platform & Gig ────────────────────────────────────────────────────
    if cat == "platform_gig":
        if any(k in text for k in ["gig worker", "platform worker", "delivery rider",
                                    "worker classification", "misclassification"]):
            return ("Gig worker regulation creates compliance obligations for iFood, "
                    "Just Eat Takeaway and Swiggy on rider classification and benefits.")
        if any(k in text for k in ["food delivery", "ifood", "just eat", "swiggy", "delivery hero"]):
            return ("Platform enforcement in food delivery directly affects iFood, "
                    "Just Eat Takeaway and Swiggy — three of Prosus's largest opcos.")
        if any(k in text for k in ["dsa", "digital services act", "vlop", "content moderation"]):
            return ("DSA obligations may apply to Just Eat Takeaway and OLX Group "
                    "if designated as Very Large Online Platforms by the EU.")
        if any(k in text for k in ["olx", "classifieds", "marketplace fraud", "fake listing"]):
            return ("Marketplace liability rules directly affect OLX Group's "
                    "classifieds network and its seller/buyer trust framework.")
        return ("Platform regulation affects iFood, Just Eat Takeaway, Swiggy, "
                "OLX Group and Dott — Prosus's core consumer platform businesses.")

    # ── Fallback ──────────────────────────────────────────────────────────
    return ("Relevant to Prosus's global digital regulatory exposure across "
            "food delivery, classifieds, payments and AI.")


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

    ALL_CATS = ["ai_tech", "competition", "fintech", "platform_gig", "ip_brand", "privacy_data"]
    categorised = {cat: [] for cat in ALL_CATS}

    for a in raw:
        a["category"]       = categorise(a)
        a["tags"]           = infer_tags(a)
        a["entity_match"]   = match_entities(a)
        a["watchlist_hits"] = hit_watchlists(a)
        a["scope_path"]     = scope_path(a)
        a["prosus_lens"]    = prosus_relevance(a)   # rule-based, no API needed
        if a["scope_path"] in ("A", "B") and OPENAI_API_KEY:
            enhanced = prosus_lens(a)               # optional GPT upgrade
            if enhanced:
                a["prosus_lens"] = enhanced
        categorised.setdefault(a["category"], []).append(a)

    # Per-category caps — competition gets more room
    CAT_CAPS = {
        "competition": 60,
        "ai_tech": 40,
        "ip_brand": 40,
        "privacy_data": 40,
        "fintech": 40,
        "platform_gig": 40,
    }
    for cat in categorised:
        cap = CAT_CAPS.get(cat, TARGET_PER_CATEGORY)
        categorised[cat] = sorted(
            categorised[cat], key=score, reverse=True
        )[:cap]

    # Dashboard compatibility aliases
    # Tab aliases for backward-compat with HTML pills
    categorised["ai_landscape"]       = categorised.get("ai_tech", [])
    categorised["chatbot"]            = categorised.get("ai_tech", [])
    categorised["chatbot_regulation"] = categorised.get("ai_tech", [])
    categorised["ai_agents"]          = categorised.get("ai_tech", [])
    categorised["gig_economy"]        = categorised.get("platform_gig", [])
    categorised["platform_liability"] = categorised.get("platform_gig", [])
    categorised["consumer_protection"]= categorised.get("competition", [])
    categorised["ip"]                 = categorised.get("ip_brand", [])
    categorised["privacy"]            = categorised.get("privacy_data", [])
    categorised["regulatory"]         = []  # no longer a catch-all

    skip = {"ai_landscape", "chatbot", "ai_agents", "chatbot_regulation",
            "gig_economy", "platform_liability", "consumer_protection",
            "ip", "privacy", "regulatory"}
    all_arts = [a for k, v in categorised.items() for a in v if k not in skip]

    # Deduplicated flash alerts — only articles NOT already top of their tab
    # so nothing appears twice on the dashboard
    tab_top_ids = {
        a["id"]
        for k, v in categorised.items() if k not in skip
        for a in v[:3]  # top 3 of each tab are already "featured"
    }
    flash = [
        {"id": a["id"], "title": a["title"], "date": a["date"],
         "source": a["source"], "url": a["url"],
         "watchlist_hits": a["watchlist_hits"],
         "entity_match": a["entity_match"], "prosus_lens": a["prosus_lens"]}
        for a in all_arts
        if (len(a.get("watchlist_hits", [])) >= 2
            or (a.get("entity_match") and a.get("watchlist_hits")))
        and a["id"] not in tab_top_ids
    ][:5]  # max 5 flash alerts, all unique

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

    print(f"\n DONE: {total} articles | {len(flash)} flash alerts")
    for cat, arts in sorted(categorised.items(), key=lambda x: -len(x[1])):
        if cat not in skip and arts:
            print(f"  {cat}: {len(arts)}")


if __name__ == "__main__":
    run()
