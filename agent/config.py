"""
config.py — Prosus Regulatory Super-Agent v4
Full entity watchlist, expanded keywords, all Prosus ecosystem regulators.
"""

# ─────────────────────────────────────────────────────────────────────────────
# PROSUS PORTFOLIO — Complete Entity Watchlist
# Source: prosus.com/portfolio (May 2026)
# ─────────────────────────────────────────────────────────────────────────────
PORTFOLIO = {

    # ── FOOD DELIVERY / QUICK COMMERCE ───────────────────────────────────────
    "food_delivery": [
        "iFood", "iFood Pago",
        "Swiggy", "Instamart", "Swiggy Genie",
        "Just Eat", "Just Eat Takeaway", "JET",
        "Delivery Hero",
        "Mr D Food", "MrD",
        "Rapido",
        "Despegar",
        "Sympla",
        "99minutos",
    ],

    # ── CLASSIFIEDS / ECOMMERCE ───────────────────────────────────────────────
    "classifieds_ecommerce": [
        "OLX", "OLX Brasil", "OLX Group", "OLX Europe",
        "Takealot", "Takealot Group",
        "Property24",
        "AutoTrader", "AutoTrader South Africa",
        "Autovit",
        "eMAG", "emag.ro",
        "Agito",
        "Fashion Days",
        "Meesho",
        "La Centrale",
        "Avant Arte",
        "Dubizzle",
        "Letgo",
        "Aruna",
        "Captain Fresh",
        "DeHaat",
    ],

    # ── PAYMENTS / FINTECH ────────────────────────────────────────────────────
    "fintech_payments": [
        "PayU", "PayU Global",
        "iyzico",
        "LazyPay",
        "PaySense",
        "Remitly",
        "Creditas",
        "BUX",
        "Bibit",
        "Bilt Rewards",
        "Endowus",
        "Azos",
    ],

    # ── AI AGENTS / ENTERPRISE AI ─────────────────────────────────────────────
    "ai_enterprise": [
        "Ema", "Ema Universal AI",
        "Brainfish",
        "Ambient AI",
        "Advolve", "Advolve.AI",
        "Corti",
        "CuspAI",
        "Arivihan",
        "BeConfident",
        "Clarity AI",
    ],

    # ── EDTECH ───────────────────────────────────────────────────────────────
    "edtech": [
        "Brainly",
        "GoStudent",
        "Eruditus",
        "Stack Overflow",
        "Codecademy",
        "Airmeet",
    ],

    # ── HEALTH ───────────────────────────────────────────────────────────────
    "health": [
        "PharmEasy",
        "GoodRx",
    ],

    # ── MOBILITY / GIG ────────────────────────────────────────────────────────
    "mobility": [
        "Dott",
        "Bykea",
        "Urban Company",
    ],

    # ── MEDIA / OTHER ─────────────────────────────────────────────────────────
    "media_other": [
        "Media24",
        "Naspers",
        "Naspers Foundry",
    ],

    # ── PARENT / INVESTEE ─────────────────────────────────────────────────────
    "parent_investee": [
        "Prosus",
        "Tencent",
        "WeChat",
    ],
}

# Flat list for entity matching
ALL_ENTITIES = [e for group in PORTFOLIO.values() for e in group]


# ─────────────────────────────────────────────────────────────────────────────
# WATCHLISTS — Thematic keyword clusters for Flash Alert triggering
# ─────────────────────────────────────────────────────────────────────────────
WATCHLISTS = {

    # --- COMPETITION / ANTITRUST ---
    "Competition": [
        "antitrust", "competition fine", "competition probe",
        "merger blocked", "merger inquiry", "market investigation",
        "cartel", "abuse of dominance", "market dominance",
        "gatekeeper designation", "DMA enforcement", "CMA case",
        "CADE investigation", "CADE aprovação", "CADE condena", "CADE multa", "ACM investigation", "DG COMP",
        "FTC investigation", "DOJ antitrust", "price fixing",
        "bid rigging", "market sharing",
    ],

    # --- PRIVACY / DATA PROTECTION ---
    "Privacy": [
        "GDPR fine", "GDPR violation", "data protection authority",
        "data breach notification", "personal data leak",
        "DPDP", "LGPD fine", "POPIA enforcement",
        "PDPA penalty", "ICO enforcement", "EDPB decision",
        "AP enforcement", "data transfer ban", "adequacy decision",
        "consent enforcement", "biometric data ban",
        "cross-border data flow", "data localisation order",
        "KVKK", "surveillance order",
    ],

    # --- AI REGULATION ---
    "AI_Regulation": [
        "EU AI Act", "AI Act enforcement", "GPAI model",
        "foundation model audit", "AI Office",
        "high-risk AI system", "AI liability",
        "deepfake legislation", "synthetic media law",
        "AI transparency obligation", "AI governance",
        "algorithmic accountability", "automated decision ban",
        "ISO 42001", "NIST AI RMF", "AI watermarking",
    ],

    # --- CHATBOT / LLM LITIGATION ---
    "Chatbot_Litigation": [
        "ChatGPT lawsuit", "OpenAI sued", "OpenAI fined",
        "Anthropic sued", "Gemini lawsuit", "chatbot fraud",
        "LLM liability", "chatbot harm", "AI hallucination lawsuit",
        "generative AI sued", "AI defamation",
        "chatbot regulation", "LLM regulation",
        "conversational AI law", "military chatbot",
    ],

    # --- IP / COPYRIGHT ---
    "IP_Copyright": [
        "AI training data", "training data copyright",
        "generative AI copyright", "text and data mining",
        "Article 17", "press publisher rights",
        "neighbouring rights", "sui generis database",
        "AI-generated content ownership",
        "fair use AI", "trade secret AI",
        "patent eligibility AI", "music AI training",
        "book AI training", "news publisher rights",
    ],

    # --- GIG ECONOMY ---
    "Gig_Economy": [
        "gig worker classification", "platform worker directive",
        "worker misclassification", "independent contractor status",
        "delivery worker rights", "algorithmic management",
        "collective bargaining platform", "minimum earnings",
        "gig economy law", "on-demand labour",
        "Swiggy workers", "iFood workers", "Rapido workers",
        "Uber workers", "Deliveroo workers",
    ],

    # --- FINTECH ---
    "Fintech_Regulation": [
        "BNPL regulation", "Buy Now Pay Later law",
        "open banking regulation", "PSD3",
        "crypto regulation", "stablecoin law",
        "DORA compliance", "digital wallet regulation",
        "payment service directive", "e-money licence",
        "BACEN Open Finance", "UPI regulation", "PIX regulation",
        "NPCI", "digital rupee", "CFPB enforcement",
    ],

    # --- PLATFORM / DSA ---
    "Platform_DSA": [
        "DSA enforcement", "Digital Services Act fine",
        "VLOP designation", "platform liability",
        "content moderation law", "notice and takedown",
        "online safety act", "online harms",
        "intermediary liability", "algorithmic transparency",
    ],

    # --- PROSUS ENTITIES DIRECT ---
    "Prosus_Direct": [
        "Prosus", "Naspers", "iFood", "Swiggy", "OLX",
        "Takealot", "PayU", "Just Eat", "eMAG", "Meesho",
        "PharmEasy", "Rapido", "iyzico", "Creditas", "Brainly",
        "GoStudent", "Ema AI", "Brainfish", "Media24",
    ],
}


# ─────────────────────────────────────────────────────────────────────────────
# CATEGORY KEYWORDS — for classification
# ─────────────────────────────────────────────────────────────────────────────
CATEGORIES = [
    "competition",
    "privacy",
    "ip",
    "ai_agents",
    "chatbot_regulation",
    "fintech",
    "platform_liability",
    "gig_economy",
    "consumer_protection",
    "regulatory",
]

CATEGORY_KEYWORDS = {
    "competition": [
        "antitrust", "competition law", "merger control", "cartel",
        "abuse of dominance", "market investigation", "CMA", "CADE",
        "FTC", "DOJ antitrust", "DG COMP", "ACM",
        "gatekeeper", "DMA enforcement", "price fixing",
        "market dominance", "monopoly", "merger inquiry",
        "acquisition blocked", "competition fine",
    ],
    "privacy": [
        "GDPR", "data protection", "personal data", "data breach",
        "privacy law", "DPDP", "LGPD", "POPIA", "PDPA",
        "data transfer", "right to erasure", "consent",
        "surveillance", "cross-border data", "adequacy decision",
        "biometric data", "data localisation", "ICO", "EDPB",
        "data minimisation", "privacy fine", "AP enforcement",
        "KVKK", "data governance",
    ],
    "ip": [
        "copyright", "trademark", "patent", "intellectual property",
        "AI training data", "training data scraping",
        "AI-generated content", "authorship", "WIPO",
        "text and data mining", "database right",
        "fair use", "IP law", "generative AI copyright",
        "trade secret", "neighbouring rights",
        "press publisher rights", "Article 17",
        "patent eligibility", "music AI training",
    ],
    "ai_agents": [
        "AI Act", "EU AI Act", "AI regulation", "GPAI",
        "foundation model", "agentic AI", "AI governance",
        "AI liability", "AI safety", "AI Office",
        "high-risk AI", "deepfake", "synthetic media",
        "AI compliance", "ISO 42001", "AI audit",
        "AI transparency", "algorithmic accountability",
        "automated decision", "AI watermarking",
    ],
    "chatbot_regulation": [
        "chatbot law", "chatbot regulation", "chatbot banned",
        "chatbot fined", "LLM regulation", "LLM lawsuit",
        "ChatGPT lawsuit", "ChatGPT banned", "OpenAI lawsuit",
        "OpenAI fined", "Anthropic sued", "chatbot liability",
        "chatbot fraud", "AI chatbot banned", "LLM liability",
        "generative AI lawsuit", "generative AI fined",
        "chatbot harm", "military chatbot", "chatbot privacy",
    ],
    "fintech": [
        "fintech regulation", "payment regulation", "PSD3",
        "open banking", "BNPL", "digital payments law",
        "e-money directive", "crypto regulation", "stablecoin",
        "digital wallet", "embedded finance", "DORA",
        "payment fine", "crypto law", "DeFi regulation",
        "BACEN", "UPI regulation", "NPCI", "PIX regulation",
        "CFPB", "digital rupee",
    ],
    "platform_liability": [
        "platform liability", "DSA", "digital services act",
        "content moderation", "notice and takedown", "VLOP",
        "intermediary liability", "user-generated content",
        "hosting provider", "online safety", "online harms",
        "DSA enforcement", "algorithmic transparency",
    ],
    "gig_economy": [
        "gig worker", "platform worker", "worker classification",
        "independent contractor", "delivery worker",
        "platform work directive", "gig economy law",
        "algorithmic management", "freelance regulation",
        "worker misclassification", "minimum earnings",
        "collective bargaining platform",
    ],
    "consumer_protection": [
        "consumer protection", "unfair commercial practices",
        "dark pattern", "drip pricing", "fake reviews",
        "subscription trap", "age verification",
        "children online", "COPPA", "student data",
        "misleading advertising", "deceptive design",
    ],
}


# ─────────────────────────────────────────────────────────────────────────────
# SOURCES — Verified RSS feeds (will be extended once feed research complete)
# Grouped by region/type for transparency
# ─────────────────────────────────────────────────────────────────────────────
SOURCES = {

    # ── EU / EUROPEAN AUTHORITIES ─────────────────────────────────────────────
    "EU_Digital_Strategy":    "https://digital-strategy.ec.europa.eu/en/rss.xml",
    "EU_Law_Live":            "https://eulawlive.com/feed/",
    "CMA_UK":                 "https://www.gov.uk/search/all.atom?organisations%5B%5D=competition-and-markets-authority&order=updated-newest",
    "WIPO":                   "https://www.wipo.int/pressroom/en/rss.xml",

    # ── SA ────────────────────────────────────────────────────────────────────
    "CompCom_SA":             "https://www.compcom.co.za/feed/",
    "TechCentral_SA":         "https://techcentral.co.za/feed/",       # if verified
    "MyBroadband_SA":         "https://mybroadband.co.za/feed/",       # if verified

    # ── INDIA ─────────────────────────────────────────────────────────────────
    "ET_Tech":                "https://economictimes.indiatimes.com/tech/rssfeeds/13357270.cms",
    "Inc42":                  "https://inc42.com/feed/",
    "MediaNama":              "https://www.medianama.com/feed/",

    # ── BRAZIL ───────────────────────────────────────────────────────────────
    "Jota_Brazil":            "https://www.jota.info/feed",

    # ── IP SPECIALIST ─────────────────────────────────────────────────────────
    "IPKat":                  "https://ipkitten.blogspot.com/feeds/posts/default?alt=rss",
    "IP_Watchdog":            "https://ipwatchdog.com/feed/",
    "IP_Finance":             "https://ipfinance.blogspot.com/feeds/posts/default",

    # ── PRIVACY / DATA SPECIALIST ─────────────────────────────────────────────
    "EFF":                    "https://www.eff.org/rss/updates.xml",
    "FPF":                    "https://fpf.org/feed/",
    "Privacy_International":  "https://privacyinternational.org/rss.xml",
    "Access_Now":             "https://www.accessnow.org/feed/",
    "CDT":                    "https://cdt.org/feed/",
    "Netzpolitik":            "https://netzpolitik.org/feed/",

    # ── AI / CHATBOT REGULATION ───────────────────────────────────────────────
    "AI_Now_Institute":       "https://ainowinstitute.org/feed/",
    "Future_of_Life":         "https://futureoflife.org/feed/",
    "Responsible_AI":         "https://www.responsible.ai/feed/",

    # ── COMPETITION SPECIALIST ────────────────────────────────────────────────
    "Chillin_Competition":    "https://chillingcompetition.com/feed",

    # ── GENERAL TECH/POLICY ───────────────────────────────────────────────────
    "TechCrunch":             "https://techcrunch.com/feed/",
    "MIT_Tech_Review":        "https://www.technologyreview.com/feed/",
    "VentureBeat_AI":         "https://venturebeat.com/feed/",
    "Ars_Technica":           "https://feeds.arstechnica.com/arstechnica/technology-lab",
    "Wired":                  "https://www.wired.com/feed/rss",
    "The_Register":           "https://www.theregister.com/headlines.atom",
    "BBC_Technology":         "https://feeds.bbci.co.uk/news/technology/rss.xml",
    "Guardian_Tech":          "https://www.theguardian.com/technology/rss",
    "Bloomberg_Tech":         "https://feeds.bloomberg.com/technology/news.rss",
    "ZDNet_Gov":              "https://www.zdnet.com/topic/government/rss.xml",
    "FT_Technology":          "https://www.ft.com/technology?format=rss",
    "Digital_Watch":          "https://dig.watch/feed",
}


# ─────────────────────────────────────────────────────────────────────────────
# AGENT SETTINGS
# ─────────────────────────────────────────────────────────────────────────────
AGENT_CONFIG = {
    "trending_count":         12,
    "max_per_category":       20,
    "flash_alert_threshold":  2,
    "timeout":                20,
    "user_agent":             "ProsusRegSuperAgent/4.0 (+https://github.com/misschevious-agtk/prosus-reg-super-agent)",
    "openai_model":           "gpt-4o",
    "prosus_context": (
        "Prosus is a global consumer internet group (HQ: Amsterdam, listed Amsterdam/Johannesburg). "
        "Portfolio: iFood & Swiggy (food delivery, Brazil/India), Just Eat (Europe), Rapido & 99minutos (logistics), "
        "OLX & eMAG & Takealot (classifieds/ecomm, global), Meesho (India social commerce), "
        "PayU & iyzico & LazyPay & Creditas (payments/fintech, global), "
        "Brainly & GoStudent & Eruditus & Arivihan (edtech), PharmEasy & GoodRx (health), "
        "Ema & Brainfish & Advolve.AI & Corti (enterprise AI agents), "
        "Dott (e-scooters, EU), Urban Company (India home services), Bykea (Pakistan), "
        "Media24 (South Africa media). Parent: Naspers. Key investee: Tencent. "
        "Key regulatory risks: "
        "EU AI Act GPAI/high-risk obligations for Ema/Brainfish/Advolve; "
        "DSA/DMA for OLX/eMAG/Takealot/iFood/Meesho; "
        "GDPR/DPDP/LGPD/POPIA data compliance; "
        "competition scrutiny of food delivery (iFood/Swiggy market dominance); "
        "gig worker classification (Swiggy/iFood/Rapido/Dott); "
        "fintech licensing (PayU/iyzico/Creditas across 50+ jurisdictions); "
        "IP & training data liability for AI products; "
        "ACM/AP (Netherlands) as Prosus HQ regulator; "
        "BACEN/ANPD (Brazil) for iFood ecosystem; "
        "CCI/RBI/DPDP Board (India) for Swiggy/Meesho/PayU; "
        "CompCom/Information Regulator (SA) for Takealot/Media24; "
        "KVKK (Turkey) for iyzico."
    ),
}
