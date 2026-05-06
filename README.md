# ⚖️ Prosus Digital Regulatory Super-Agent

AI-powered regulatory intelligence platform for the Prosus Digital & Regulatory team.

## What it does

- **30+ sources** across EU, UK, US, India, Brazil, South Africa, Singapore
- **AI-powered Prosus Lens** — every article analysed through the lens of Prosus portfolio companies
- **Flash Alerts** — high-priority items that hit 2+ watchlists or directly name a portfolio entity
- **8 categories** — Competition, Privacy, IP, AI Landscape, Regulatory, Fintech, Consumer Protection, Platform Liability
- **Watchlists** — AI Act, Agentic Fraud, Algorithmic Collusion, Data Transfers, Platform Liability, Fintech, IP & Copyright, Consumer Protection
- **Mobile-first dashboard** — filter, search, expand, and read-across on any device
- **Daily auto-sync** via GitHub Actions at 06:00 UTC

## Portfolio Entities Monitored

iFood · Swiggy · Rapido · OLX · Takealot · eMAG · Dubizzle · PayU · Remitly · Brainly · GoStudent · Eruditus · Stack Overflow · PharmEasy · Ema · Brainfish · Advolve.AI · Prosus · Naspers · Tencent

## Scope Path

| Badge | Meaning |
|-------|---------|
| 🔴 Red dot | **Scope A** — directly names a Prosus portfolio entity |
| 🟡 Amber dot | **Scope B** — affects a jurisdiction where Prosus operates |
| 🟢 Green dot | **Scope C** — general relevance |

## Setup

### 1. Fork this repo

### 2. Add your OpenAI API key (optional but recommended)
Go to **Settings → Secrets → Actions** and add:
```
OPENAI_API_KEY = sk-...
```
Without this, the Prosus Lens analysis will be disabled — everything else still works.

### 3. Enable GitHub Pages
Go to **Settings → Pages → Source → Deploy from branch → main → / (root)**

Your dashboard will be live at `https://<your-username>.github.io/prosus-reg-super-agent/`

### 4. Run the first sync
Go to **Actions → Daily Regulatory Sync → Run workflow**

The scraper will fetch all sources, categorise articles, generate Prosus Lens analysis, and commit the updated `content/index.json`. GitHub Pages will update within ~2 minutes.

### 5. Run locally (optional)
```bash
pip install -r requirements.txt
python -m agent.scraper
```

## Repository Structure

```
prosus-reg-super-agent/
├── agent/
│   ├── __init__.py
│   ├── config.py          # Sources, entities, watchlists, categories
│   └── scraper.py         # Core intelligence engine
├── pages/
│   └── index.html         # Mobile dashboard template
├── content/
│   ├── index.json         # Auto-generated: all articles + trending + alerts
│   ├── sync.json          # Auto-generated: last sync metadata
│   └── pages/             # Auto-generated: per-article markdown
├── .github/
│   └── workflows/
│       └── daily-sync.yml # GitHub Actions: runs daily at 06:00 UTC
├── index.html             # Auto-copied from pages/ on sync
└── requirements.txt
```

## Customising

Edit `agent/config.py` to:
- Add/remove sources (`SOURCES`)
- Add portfolio entities (`PORTFOLIO`)
- Add watchlist topics (`WATCHLISTS`)
- Adjust categories (`CATEGORIES` / `CATEGORY_KEYWORDS`)

---

Built for the Prosus Digital & Regulatory team.
