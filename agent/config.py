"""
config.py
Master configuration for the Prosus Regulatory Super-Agent.
Updated to reflect Prosus's full portfolio and AI-first strategy.
"""

# Auto-apply scraper patches at import time (diversity caps + URL fixes)
import os as _os, sys as _sys
_patch = _os.path.join(_os.path.dirname(_os.path.dirname(__file__)), "patch_scraper.py")
if _os.path.exists(_patch):
    import importlib.util as _ilu
    _spec = _ilu.spec_from_file_location("patch_scraper", _patch)
    _mod = _ilu.module_from_spec(_spec)
    try:
        _spec.loader.exec_module(_mod)
    except SystemExit:
        pass  # patch_scraper calls sys.exit(0) when already patched - that is fine

# ─────────────────────────────────────────────
# PROSUS PORTFOLIO — Entity Watchlist
# ─────────────────────────────────────────────
# Source: prosus.com/portfolio + prosus.com/ecosystems
PORTFOLIO = {

    # ── FOOD DELIVERY / QUICK COMMERCE ───────
    "food_delivery": [
        "iFood", "iFood Pago", "Swiggy", "Instamart",
        "Just Eat", "Just Eat Takeaway", "Delivery Hero",
        "Mr D Food", "Rapido", "Despegar", "Sympla",
        "99minutos",
    ],

    # ── CLASSIFIEDS / ECOMMERCE ───────────────
    "classifieds_ecommerce": [
        "OLX", "OLX Brasil", "OLX Group",
        "Takealot", "Property24", "AutoTrader", "Autotrader South Africa",
        "Autovit", "eMAG", "Agito", "Fashion Days",
        "Meesho", "La Centrale", "Avant Arte",
        "Dubizzle", "Letgo",
    ],

    # ── PAYMENTS / FINTECH ────────────────────
    "fintech_payments": [
        "PayU", "iyzico", "LazyPay", "PaySense",
        "Remitly", "Creditas", "BUX", "Bibit",
        "Bilt Rewards", "Endowus", "Constantinople",
        "Azos",
    ],

    # ── AI AGENTS / ENTERPRISE AI ─────────────
    # This is Prosus's #1 strategic focus area
    "ai_enterprise": [
        "Ema", "Ema Universal AI Employee",
        "Brainfish", "Ambient AI",
        "Advolve.AI",
        "Clarity", "Corti",
        "CuspAI",
        "Arivihan",
        "BeConfident",
        "CodeKarma",
        "Detect Technologies",
    ],

    # ── EDTECH ───────────────────────────────
    "edtech": [
        "Brainly", "GoStudent", "Eruditus",
        "Stack Overflow", "EduMe",
        "ElasticRun",
    ],

    # ── HEALTHTECH ───────────────────────────
    "healthtech": [
        "PharmEasy", "GoodRx", "Corti",
    ],

    # ── MOBILITY / LOGISTICS ─────────────────
    "mobility_logistics": [
        "Rapido", "Dott", "Bykea",
        "99minutos", "ElasticRun",
    ],

    # ── SOCIAL / CREATOR ─────────────────────
    "social_creator": [
        "BandLab", "Avant Arte", "Airmeet",
        "Stack Overflow",
    ],

    # ── INDIA ECOSYSTEM ──────────────────────
    "india_ecosystem": [
        "Swiggy", "Meesho", "PayU", "Urban Company",
        "Rapido", "PharmEasy", "DeHaat",
        "Captain Fresh", "Aruna",
        "Detect Technologies", "ElasticRun",
    ],

    # ── LATAM ECOSYSTEM ──────────────────────
    "latam_ecosystem": [
        "iFood", "OLX Brasil", "Creditas",
        "Despegar", "Sympla", "99minutos", "Azos",
    ],

    # ── EUROPE ECOSYSTEM ─────────────────────
    "europe_ecosystem": [
        "Just Eat", "eMAG", "iyzico", "OLX",
        "Dott", "BUX", "La Centrale", "Autovit",
    ],

    # ── PARENT / STRATEGIC ───────────────────
    "parent": [
        "Prosus", "Naspers", "Tencent", "Prosus Ventures",
        "Media24",
    ],
}

# Flat list for keyword matching
ALL_ENTITIES = [e for group in PORTFOLIO.values() for e in group]
# Deduplicate
ALL_ENTITIES = list(dict.fromkeys(ALL_ENTITIES))

# ─────────────────────────────────────────────
# JURISDICTIONS — where Prosus operates
# ─────────────────────────────────────────────
JURISDICTIONS = [
    "EU", "European Union", "Netherlands", "Germany", "France",
    "Romania", "Poland", "UK", "United Kingdom",
    "India", "Brazil", "South Africa",
    "Singapore", "Indonesia", "Pakistan",
    "United States", "Mexico", "Colombia", "Chile", "Peru",
    "Nigeria", "Kenya",
]

# ─────────────────────────────────────────────
# WATCHLISTS — Prosus-specific priority topics
# ─────────────────────────────────────────────
WATCHLISTS = {

    # ── TOP PRIORITY: AI Agents & Agentic AI ─
    "AI Agents & Agentic AI": [
        "AI agent", "agentic AI", "autonomous agent",
        "multi-agent", "AI workforce", "digital worker",
        "AI employee", "enterprise AI agent", "AI assistant",
        "life assistant", "personal AI", "AI ecosystem",
        "agentic systems", "AI orchestration",
        "Universal AI Employee",
        # Prosus-relevant named agents
        "Ema", "Brainfish", "Ambient AI",
    ],

    # ── TOP PRIORITY: Agentic Fraud & Trust ──
    "Agentic Fraud & Digital Trust": [
        "agentic fraud", "AI fraud", "automated deception",
        "impersonation", "synthetic identity", "deepfake",
        "AI scam", "voice cloning", "brand impersonation",
        "digital trust", "AI-enabled fraud",
        "agentic impersonation", "automated phishing",
    ],

    # ── AI Act & GPAI ─────────────────────────
    "EU AI Act": [
        "AI Act", "EU AI Act", "GPAI", "general purpose AI",
        "Article 53", "Article 55", "high-risk AI",
        "AI Office", "AI governance", "foundation model",
        "AI liability", "AI safety", "AI risk classification",
        "prohibited AI", "AI conformity",
    ],

    # ── Algorithmic Systems & Recommenders ───
    "Algorithmic Regulation": [
        "algorithmic collusion", "algorithmic pricing",
        "dynamic pricing", "recommender system",
        "algorithmic accountability", "algorithmic transparency",
        "AI recommender", "automated decision-making",
        "Article 22 GDPR", "profiling",
        "algorithmic discrimination", "pricing algorithm",
    ],

    # ── Data & Privacy ────────────────────────
    "Data & Privacy": [
        "GDPR", "data protection", "personal data", "data breach",
        "adequacy decision", "data transfer", "SCCs",
        "DPDP", "Digital Personal Data Protection",
        "data localisation", "consent management",
        "LGPD", "POPIA", "PDPA",
        "right to erasure", "data minimisation",
        "cross-border data",
    ],

    # ── Platform & DSA ────────────────────────
    "Platform Regulation (DSA/DMA)": [
        "DSA", "Digital Services Act", "DMA", "Digital Markets Act",
        "platform liability", "gatekeeper", "very large platform",
        "VLOP", "content moderation", "systemic risk",
        "interoperability", "self-preferencing",
        "dark pattern", "platform regulation",
    ],

    # ── Competition & Market Power ────────────
    "Competition & Antitrust": [
        "antitrust", "competition", "abuse of dominance",
        "merger control", "market investigation",
        "gig economy", "worker classification",
        "food delivery competition", "platform monopoly",
        "algorithmic collusion", "cartel",
        "CADE", "CCI", "CMA antitrust", "DG COMP",
    ],

    # ── Fintech & Payments ────────────────────
    "Fintech & Payments Regulation": [
        "PSD3", "PSR", "open banking", "BNPL",
        "buy now pay later", "digital payments",
        "e-money", "payment service provider",
        "DORA", "crypto regulation", "stablecoin",
        "digital wallet", "embedded finance",
        "PayU", "iyzico", "Remitly",
    ],

    # ── IP & AI Training Data ─────────────────
    "IP & AI Training Data": [
        "AI training data", "copyright infringement",
        "AI-generated content", "authorship AI",
        "training data scraping", "web scraping copyright",
        "WIPO AI", "fair use AI", "text and data mining",
        "database rights", "AI copyright",
        "Llama", "OpenAI copyright", "generative AI IP",
    ],

    # ── Consumer Protection & EdTech ──────────
    "Consumer Protection & EdTech": [
        "consumer protection AI", "EdTech regulation",
        "children online", "COPPA", "age verification",
        "student data", "online tutoring regulation",
        "Brainly", "GoStudent", "Eruditus",
        "digital literacy", "online education law",
    ],

    # ── Gig Economy & Labour ──────────────────
    "Gig Economy & Labour": [
        "gig worker", "platform worker", "worker classification",
        "independent contractor", "delivery worker",
        "EU Platform Work Directive", "gig economy",
        "Swiggy worker", "iFood worker", "food delivery worker",
        "algorithmic management", "worker rights platform",
    ],

    # ── Quick Commerce & Food Delivery ────────
    "Food Delivery & Quick Commerce": [
        "food delivery regulation", "quick commerce",
        "dark kitchen", "ghost kitchen", "delivery platform",
        "iFood", "Swiggy", "Just Eat",
        "food safety regulation", "delivery worker rights",
        "restaurant aggregator", "online food",
    ],
}

# ─────────────────────────────────────────────
# CATEGORIES — tuned for Prosus portfolio
# ─────────────────────────────────────────────
CATEGORIES = [
    "ai_agents",         # NEW: AI agents, agentic AI, enterprise AI — #1 Prosus priority
    "competition",
    "privacy",
    "ip",
    "regulatory",
    "fintech",
    "consumer_protection",
    "platform_liability",
    "gig_economy",       # NEW: gig/platform workers — food delivery, ride-hailing
]

CATEGORY_KEYWORDS = {
    "ai_agents": [
        "AI agent", "agentic", "autonomous agent", "AI workforce",
        "enterprise AI", "AI assistant", "life assistant", "AI employee",
        "multi-agent", "AI orchestration", "agentic AI", "agentic fraud",
        "deepfake", "synthetic media", "AI ecosystem",
        "foundation model", "large language model", "LLM",
        "generative AI", "AI Act", "GPAI", "AI governance",
        "AI regulation", "AI Office", "AI liability", "AI safety",
        "AI transparency", "AI bias", "AI accountability",
        "AI audit", "AI compliance", "ISO 42001", "artificial intelligence",
    ],
    "competition": [
        "antitrust", "competition", "cartel", "merger",
        "abuse of dominance", "market power", "price-fixing",
        "collusion", "CADE", "CCI", "CMA antitrust",
        "DOJ antitrust", "DG COMP", "market investigation",
        "algorithmic collusion", "gatekeeper", "DMA",
    ],
    "privacy": [
        "GDPR", "data protection", "personal data", "data breach",
        "privacy", "ICO", "CNIL", "EDPB", "ANPD", "PDPC", "POPIA",
        "DPDP", "LGPD", "data transfer", "SCCs", "adequacy",
        "right to erasure", "consent", "data subject",
        "cookie", "tracking", "surveillance", "cross-border data",
    ],
    "ip": [
        "intellectual property", "copyright", "patent", "trademark",
        "AI training data", "training data scraping",
        "AI-generated content", "authorship", "WIPO",
        "text and data mining", "database right",
        "fair use", "infringement", "CJEU copyright",
    ],
    "regulatory": [
        "DSA", "DMA", "NIS2", "DORA",
        "digital services act", "digital markets act",
        "regulation enters into force", "compliance deadline",
        "enforcement begins", "regulatory framework",
        "consultation", "legislative proposal", "delegated act",
        "implementing act", "MeitY", "TRAI", "Ofcom",
        "platform regulation", "ecommerce regulation",
    ],
    "fintech": [
        "fintech", "payments", "PSD3", "PSR", "open banking",
        "BNPL", "buy now pay later", "digital payments",
        "e-money", "crypto", "stablecoin", "DORA",
        "payment service", "digital wallet", "embedded finance",
        "PayU", "iyzico", "Remitly", "Creditas",
    ],
    "consumer_protection": [
        "consumer law", "consumer protection", "dark pattern",
        "drip pricing", "fake reviews", "subscription trap",
        "consumer rights", "unfair commercial practices",
        "CMA consumer", "FTC consumer", "age verification",
        "children online", "COPPA", "student data",
    ],
    "platform_liability": [
        "platform liability", "intermediary liability",
        "content moderation", "notice and takedown",
        "algorithmic recommender", "DSA liability",
        "hosting provider", "user-generated content",
        "VLOP", "very large online platform",
    ],
    "gig_economy": [
        "gig worker", "platform worker", "worker classification",
        "independent contractor", "delivery worker",
        "EU Platform Work Directive", "gig economy",
        "food delivery worker", "algorithmic management",
        "minimum wage platform", "worker rights",
        "freelance regulation", "on-demand worker",
    ],
}

# ─────────────────────────────────────────────
# SOURCES — 30+ across all Prosus jurisdictions
# ─────────────────────────────────────────────
SOURCES = [
    # ── EU / EUROPE ───────────────────────────
    {"label": "European Commission",     "url": "https://ec.europa.eu/commission/presscorner/api/documents?service=press-corner&typeDocument=IP&pageSize=10&page=1"},
    {"label": "EU AI Office",            "url": "https://digital-strategy.ec.europa.eu/en/news-redirect/newsroom"},
    {"label": "EDPB",                    "url": "https://www.edpb.europa.eu/rss.xml"},
    {"label": "noyb",                     "url": "https://noyb.eu/en/rss.xml"},
    {"label": "Hunton Privacy",             "url": "https://www.huntonprivacyblog.com/feed/"},
    {"label": "CNIL (France)",           "url": "https://www.cnil.fr/en/news"},
    {"label": "ICO (UK)",                "url": "https://ico.org.uk/about-the-ico/media-centre/news-and-blogs/"},
    {"label": "CMA (UK)",                "url": "https://www.gov.uk/cma-cases"},
    {"label": "Ofcom (UK)",              "url": "https://www.ofcom.org.uk/news-centre"},
    {"label": "BfDI (Germany)",          "url": "https://www.bfdi.bund.de/EN/Home/home_node.html"},
    {"label": "Digital Watch",           "url": "https://dig.watch/updates"},

    # ── USA ───────────────────────────────────
    {"label": "FTC",                     "url": "https://www.ftc.gov/news-events/news/press-releases"},
    {"label": "DOJ Antitrust",           "url": "https://www.justice.gov/atr/news"},
    {"label": "FCC",                     "url": "https://www.fcc.gov/news-events/blog"},

    # ── INDIA (critical for Swiggy, Meesho, PayU, Rapido) ─
    {"label": "CCI (India)",             "url": "https://www.cci.gov.in/media-gallery/press-release"},
    {"label": "MeitY (India)",           "url": "https://www.meity.gov.in/whats-new"},
    {"label": "TRAI (India)",            "url": "https://www.trai.gov.in/whats-new"},
    {"label": "Business Standard Tech",  "url": "https://www.business-standard.com/technology"},
    {"label": "Mint Tech",               "url": "https://www.livemint.com/technology"},
    {"label": "Economic Times Tech",     "url": "https://economictimes.indiatimes.com/tech"},

    # ── BRAZIL (critical for iFood, OLX, Creditas) ─
    {"label": "CADE (Brazil)",           "url": "https://www.gov.br/cade/en/latest-news"},
    {"label": "ANPD (Brazil)",           "url": "https://www.gov.br/anpd/pt-br/assuntos/noticias"},

    # ── SOUTH AFRICA (Naspers base: Takealot, Media24) ─
    {"label": "CompCom (SA)",            "url": "https://www.compcom.co.za/category/media-releases/"},
    {"label": "CGSO / POPIA (SA)",       "url": "https://www.justice.gov.za/inforeg/newsroom.html"},

    # ── SINGAPORE (Endowus, Prosus Ventures) ─
    {"label": "PDPC (Singapore)",        "url": "https://www.pdpc.gov.sg/news-and-events/media-releases"},
    {"label": "IMDA (Singapore)",        "url": "https://www.imda.gov.sg/resources/press-releases-factsheets-and-speeches"},
    {"label": "MAS (Singapore)",         "url": "https://www.mas.gov.sg/news"},

    # ── GLOBAL / AGGREGATORS ─────────────────
    {"label": "IAPP",                    "url": "https://iapp.org/feed/"},
    {"label": "TechCrunch Policy",       "url": "https://techcrunch.com/category/policy/"},
    {"label": "Wired Policy",            "url": "https://www.wired.com/tag/policy/"},
    {"label": "Politico Tech",           "url": "https://www.politico.eu/newsletter/digital-bridge/"},
    {"label": "GCR (Competition)",       "url": "https://globalcompetitionreview.com/rss/"},
    {"label": "Law360 Competition",        "url": "https://www.law360.com/competition/rss"},
    {"label": "DG COMP Press",            "url": "https://ec.europa.eu/commission/presscorner/api/rss?keywords=competition+antitrust&size=20"},
    {"label": "ProMarket (Stigler)",        "url": "https://promarket.org/feed/"},
    {"label": "Chillin Competition",          "url": "https://chillingcompetition.com/feed/"},
    {"label": "WIPO",                    "url": "https://www.wipo.int/pressroom/en/"},
    {"label": "AI Now Institute",        "url": "https://ainowinstitute.org/feed/"},
    {"label": "DLA Piper DP",            "url": "https://www.dlapiperdataprotection.com"},

    # ── AI-SPECIFIC SOURCES ───────────────────
    {"label": "MIT Tech Review AI",      "url": "https://www.technologyreview.com/topic/artificial-intelligence/"},
    {"label": "VentureBeat AI",          "url": "https://venturebeat.com/ai/"},
    {"label": "The Verge Tech Policy",   "url": "https://www.theverge.com/policy"},

    # ── MLEX — Premium Regulatory Intelligence (subscription required) ─
    {"label": "MLex Antitrust",          "url": "https://www.mlex.com/mlex/antitrust/rss",             "requires_auth": True},
    {"label": "MLex Data Privacy",       "url": "https://www.mlex.com/mlex/data-privacy-security/rss", "requires_auth": True},
    {"label": "MLex Energy",             "url": "https://www.mlex.com/mlex/energy/rss",                "requires_auth": True},
    {"label": "MLex Financial Crime",    "url": "https://www.mlex.com/mlex/financial-crime/rss",       "requires_auth": True},
    {"label": "MLex Financial Services", "url": "https://www.mlex.com/mlex/financial-services/rss",    "requires_auth": True},
    {"label": "MLex M&A",                "url": "https://www.mlex.com/mlex/mergers-acquisitions/rss",  "requires_auth": True},
    {"label": "MLex State Aid",          "url": "https://www.mlex.com/mlex/state-aid/rss",             "requires_auth": True},
    {"label": "MLex Technology",         "url": "https://www.mlex.com/mlex/technology/rss",            "requires_auth": True},
    {"label": "MLex Trade",              "url": "https://www.mlex.com/mlex/trade/rss",                 "requires_auth": True},

    # ── LAW FIRMS — Public Insights Feeds ────
    {"label": "Clifford Chance",         "url": "https://www.cliffordchance.com/insights/resources/blogs/antitrust-fdi-insights.html"},
    {"label": "Bird & Bird Competition", "url": "https://www.twobirds.com/en/competition-law-insights"},
    {"label": "Bird & Bird Insights",    "url": "https://www.twobirds.com/en/insights"},
    {"label": "Linklaters Insights",     "url": "https://www.linklaters.com/insights"},
    {"label": "Freshfields",             "url": "https://www.law360.com/competition/rss"},
    {"label": "DLA Piper Tech",          "url": "https://www.dlapiper.com/en/insights?topic=technology"},
    {"label": "Lexology",                "url": "https://www.lexology.com/library?q=AI+regulation+competition+privacy"},
]

# ─────────────────────────────────────────────
# AGENT SETTINGS
# ─────────────────────────────────────────────
AGENT_CONFIG = {
    "trending_count": 10,
    "max_per_category": 25,
    "flash_alert_threshold": 2,
    "timeout": 20,
    "user_agent": "ProsusRegSuperAgent/2.0 (+https://github.com/misschevious-agtk/prosus-reg-super-agent)",
    "openai_model": "gpt-4o",
    # Prosus strategic context for AI analysis
    "prosus_context": (
        "Prosus is a global consumer internet group focused on lifestyle e-commerce. "
        "Its #1 strategic priority is AI agents, agentic AI, and AI ecosystems — "
        "deployed across food delivery (iFood, Swiggy, Just Eat), classifieds (OLX, eMAG, Takealot), "
        "payments (PayU, iyzico), edtech (Brainly, GoStudent, Eruditus), and enterprise AI "
        "(Ema Universal AI Employee, Brainfish Ambient AI agents, Advolve.AI, Clarity, Corti). "
        "Prosus operates ecosystems in Europe, Latin America (Brazil focus), India, and South Africa. "
        "Key regulatory risks: EU AI Act GPAI obligations for Ema/Brainfish/Advolve.AI; "
        "DSA/DMA platform obligations for OLX/eMAG/Takealot/iFood; "
        "GDPR/DPDP data compliance for cross-border operations; "
        "competition scrutiny of food delivery platforms; "
        "gig worker classification for Swiggy/iFood/Rapido; "
        "fintech licensing for PayU/iyzico across multiple jurisdictions; "
        "IP and training data liability for AI products."
    ),
}
