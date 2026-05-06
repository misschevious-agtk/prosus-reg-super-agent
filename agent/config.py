"""
config.py
Master configuration for the Prosus Regulatory Super-Agent.
"""

# ─────────────────────────────────────────────
# PROSUS PORTFOLIO — Entity Watchlist
# ─────────────────────────────────────────────
PORTFOLIO = {
    "food_delivery": [
        "iFood", "Swiggy", "Delivery Hero", "Rapido",
    ],
    "classifieds_ecommerce": [
        "OLX", "Takealot", "Property24", "Letgo", "Dubizzle",
        "eMAG", "Avito",
    ],
    "fintech_payments": [
        "PayU", "Remitly", "LazyPay", "PaySense",
    ],
    "edtech": [
        "Brainly", "GoStudent", "Eruditus", "Stack Overflow",
    ],
    "healthtech": [
        "PharmEasy", "GoodRx",
    ],
    "ai_enterprise": [
        "Ema", "Brainfish", "Advolve.AI",
    ],
    "parent": [
        "Prosus", "Naspers", "Tencent",
    ],
}

# Flat list for keyword matching
ALL_ENTITIES = [e for group in PORTFOLIO.values() for e in group]

# ─────────────────────────────────────────────
# JURISDICTIONS
# ─────────────────────────────────────────────
JURISDICTIONS = [
    "EU", "European Union", "UK", "United Kingdom",
    "India", "Brazil", "South Africa", "Netherlands",
    "Singapore", "United States", "Germany", "France",
    "Poland", "Romania", "Nigeria", "Kenya",
]

# ─────────────────────────────────────────────
# REGULATORY SOURCES — 30+ across all jurisdictions
# ─────────────────────────────────────────────
SOURCES = [
    # ── EU / Europe ──────────────────────────
    {"label": "European Commission",        "url": "https://ec.europa.eu/commission/presscorner/api/documents?service=press-corner&typeDocument=IP&pageSize=10&page=1"},
    {"label": "EU AI Office",               "url": "https://digital-strategy.ec.europa.eu/en/news-redirect/newsroom"},
    {"label": "EDPB",                       "url": "https://www.edpb.europa.eu/news/news_en"},
    {"label": "CNIL (France)",              "url": "https://www.cnil.fr/en/news"},
    {"label": "ICO (UK)",                   "url": "https://ico.org.uk/about-the-ico/media-centre/news-and-blogs/"},
    {"label": "CMA (UK)",                   "url": "https://www.gov.uk/cma-cases"},
    {"label": "Ofcom (UK)",                 "url": "https://www.ofcom.org.uk/news-centre"},
    {"label": "BfDI (Germany)",             "url": "https://www.bfdi.bund.de/EN/Home/home_node.html"},
    {"label": "Digital Watch",              "url": "https://dig.watch/updates"},

    # ── USA ──────────────────────────────────
    {"label": "FTC",                        "url": "https://www.ftc.gov/news-events/news/press-releases"},
    {"label": "DOJ Antitrust",              "url": "https://www.justice.gov/atr/news"},
    {"label": "FCC",                        "url": "https://www.fcc.gov/news-events/blog"},

    # ── India ────────────────────────────────
    {"label": "CCI (India)",                "url": "https://www.cci.gov.in/media-gallery/press-release"},
    {"label": "MeitY (India)",              "url": "https://www.meity.gov.in/whats-new"},
    {"label": "TRAI (India)",               "url": "https://www.trai.gov.in/whats-new"},
    {"label": "Business Standard Tech",     "url": "https://www.business-standard.com/technology"},
    {"label": "Mint Tech & Startup",        "url": "https://www.livemint.com/technology"},

    # ── Brazil ───────────────────────────────
    {"label": "CADE (Brazil)",              "url": "https://www.gov.br/cade/en/latest-news"},
    {"label": "ANPD (Brazil)",              "url": "https://www.gov.br/anpd/pt-br/assuntos/noticias"},

    # ── South Africa ─────────────────────────
    {"label": "CGSO / POPIA (SA)",          "url": "https://www.justice.gov.za/inforeg/newsroom.html"},
    {"label": "CompCom (SA)",               "url": "https://www.compcom.co.za/category/media-releases/"},

    # ── Singapore ────────────────────────────
    {"label": "PDPC (Singapore)",           "url": "https://www.pdpc.gov.sg/news-and-events/media-releases"},
    {"label": "IMDA (Singapore)",           "url": "https://www.imda.gov.sg/resources/press-releases-factsheets-and-speeches"},

    # ── Global / Aggregators ─────────────────
    {"label": "IAPP",                       "url": "https://iapp.org/news/a/"},
    {"label": "TechCrunch Policy",          "url": "https://techcrunch.com/category/policy/"},
    {"label": "Wired Policy",               "url": "https://www.wired.com/tag/policy/"},
    {"label": "Politico Tech",              "url": "https://www.politico.eu/newsletter/digital-bridge/"},
    {"label": "GCR (Competition)",          "url": "https://globalcompetitionreview.com/news"},
    {"label": "WIPO",                       "url": "https://www.wipo.int/pressroom/en/"},
    {"label": "Future of Life Institute",   "url": "https://futureoflife.org/news/"},
    {"label": "AI Now Institute",           "url": "https://ainowinstitute.org/news"},
    {"label": "DLA Piper DP",               "url": "https://www.dlapiperdataprotection.com"},
]

# ─────────────────────────────────────────────
# WATCHLISTS — Priority alert topics
# ─────────────────────────────────────────────
WATCHLISTS = {
    "AI Act": [
        "AI Act", "EU AI Act", "Article 53", "Article 55",
        "high-risk AI", "GPAI", "general purpose AI", "AI Office",
        "AI liability", "AI governance", "foundation model",
    ],
    "Agentic AI & Fraud": [
        "agentic AI", "AI agent", "autonomous agent", "deepfake",
        "impersonation", "synthetic media", "AI fraud", "AI scam",
        "agentic fraud", "automated deception",
    ],
    "Algorithmic Collusion": [
        "algorithmic collusion", "algorithmic pricing", "dynamic pricing",
        "price-fixing algorithm", "hub and spoke", "AI collusion",
    ],
    "Data Transfers": [
        "SCCs", "standard contractual clauses", "adequacy decision",
        "cross-border transfer", "data localisation", "Chapter V",
        "GDPR transfer", "EEA transfer",
    ],
    "Platform Liability": [
        "DSA", "Digital Services Act", "platform liability",
        "intermediary liability", "content moderation",
        "notice and takedown", "algorithmic recommender",
    ],
    "Fintech & Payments": [
        "PSD3", "PSR", "open banking", "BNPL", "buy now pay later",
        "digital payments", "e-money", "payment service",
        "crypto regulation", "stablecoin", "DORA",
    ],
    "IP & Copyright": [
        "AI-generated", "AI training", "copyright infringement",
        "intellectual property", "trademark", "CJEU", "WIPO",
        "fair use", "authorship", "originality",
    ],
    "Consumer Protection": [
        "consumer law", "dark pattern", "drip pricing",
        "fake reviews", "subscription trap", "consumer rights",
        "CMA consumer", "FTC consumer",
    ],
}

# ─────────────────────────────────────────────
# CATEGORIES
# ─────────────────────────────────────────────
CATEGORIES = [
    "competition",
    "privacy",
    "ip",
    "ai_landscape",
    "regulatory",
    "fintech",
    "consumer_protection",
    "platform_liability",
]

CATEGORY_KEYWORDS = {
    "competition": [
        "antitrust", "competition", "cartel", "merger", "abuse of dominance",
        "market power", "price-fixing", "collusion", "CADE", "CCI", "CMA antitrust",
        "DOJ antitrust", "European Commission competition", "DG COMP",
        "market investigation", "algorithmic collusion",
    ],
    "privacy": [
        "GDPR", "data protection", "personal data", "data breach",
        "privacy", "ICO", "CNIL", "EDPB", "ANPD", "PDPC", "POPIA",
        "data transfer", "right to erasure", "consent", "data subject",
        "cookie", "tracking", "surveillance",
    ],
    "ip": [
        "intellectual property", "copyright", "patent", "trademark",
        "trade secret", "design right", "database right", "infringement",
        "AI-generated", "authorship", "originality", "CJEU copyright",
        "USPTO", "EPO", "WIPO", "licensing", "fair use", "fair dealing",
        "AI training data",
    ],
    "ai_landscape": [
        "artificial intelligence", "AI model", "machine learning",
        "large language model", "LLM", "generative AI", "foundation model",
        "AI Act", "AI governance", "AI regulation", "AI Office",
        "AI liability", "AI safety", "AI risk", "AI audit", "AI transparency",
        "AI bias", "deepfake", "autonomous system", "AI accountability",
        "AI enforcement", "AI compliance", "agentic", "AI agent",
        "AI standard", "ISO 42001", "GPAI",
    ],
    "regulatory": [
        "DSA", "DMA", "digital markets act", "digital services act",
        "regulation enters into force", "compliance deadline",
        "enforcement begins", "regulatory framework", "consultation",
        "legislative proposal", "delegated act", "implementing act",
        "NIS2", "DORA", "ecommerce regulation", "platform regulation",
        "MeitY", "TRAI", "Ofcom",
    ],
    "fintech": [
        "fintech", "payments", "PSD3", "PSR", "open banking",
        "BNPL", "buy now pay later", "digital payments", "e-money",
        "crypto", "stablecoin", "DORA", "payment service",
        "digital wallet", "PayU", "Remitly",
    ],
    "consumer_protection": [
        "consumer law", "consumer protection", "dark pattern",
        "drip pricing", "fake reviews", "subscription trap",
        "consumer rights", "unfair commercial practices",
        "CMA consumer", "FTC consumer",
    ],
    "platform_liability": [
        "platform liability", "intermediary liability",
        "content moderation", "notice and takedown",
        "algorithmic recommender", "DSA liability",
        "hosting provider", "user-generated content",
    ],
}

# ─────────────────────────────────────────────
# AGENT SETTINGS
# ─────────────────────────────────────────────
AGENT_CONFIG = {
    "trending_count": 8,
    "max_per_category": 25,
    "flash_alert_threshold": 3,   # Watchlist hits before a Flash Alert fires
    "timeout": 20,
    "user_agent": "ProsusRegSuperAgent/2.0 (+https://github.com/misschevious-agtk/prosus-reg-super-agent)",
    "openai_model": "gpt-4o",
}
