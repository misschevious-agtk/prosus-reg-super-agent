import sys

with open("agent/scraper.py") as f:
    content = f.read()

if "apply_diversity_cap" in content:
    print("Already fully patched")
    sys.exit(0)

changes = 0

# FIX 1: add source var + SOURCE_CAT_MAP to categorise()
old_source = '    title = a["title"].lower()\n    # Title match wins'
new_source = '    title = a["title"].lower()\n    source = a.get("source", "").lower()\n    # Title match wins'
content = content.replace(old_source, new_source, 1)

old_cat = '    best_cat, best_score = "regulatory", 0'
new_cat = (
    '    best_cat, best_score = "competition", 0\n'
    '\n'
    '    SOURCE_CAT_MAP = [\n'
    '        ("competition", ["mlex antitrust", "mlex state aid", "mlex trade",\n'
    '                         "mlex mergers", "global competition review",\n'
    '                         "chillin competition", "kluwer competition",\n'
    '                         "antitrust law blog", "lexxion", "competition policy intl",\n'
    '                         "cpi antitrust", "promarket", "stigler",\n'
    '                         "covington competition", "clifford chance antitrust",\n'
    '                         "bird & bird competition", "linklaters", "de brauw",\n'
    '                         "freshfields", "compcom south africa", "cma blog",\n'
    '                         "cma ", "eu law live", "dg comp"]),\n'
    '        ("ai_tech",    ["mlex technology", "clifford chance ai",\n'
    '                         "bird & bird insights", "freshfields technology",\n'
    '                         "freshfields digital", "ai now institute", "eff deeplinks",\n'
    '                         "algorithmwatch", "netzpolitik", "tech policy press",\n'
    '                         "digital watch", "access now"]),\n'
    '        ("ip_brand",   ["mlex ip", "ipkat", "ip kat", "ipwatchdog", "ip watchdog",\n'
    '                         "patently-o", "torrentfreak", "managing ip",\n'
    '                         "world trademark", "kluwer trademark", "selvam",\n'
    '                         "spicyip", "anand & anand", "rna law", "c&c ip",\n'
    '                         "epo ", "uk ipo", "wipo", "euipo", "uspto",\n'
    '                         "bird & bird patent", "inta", "ipo uk"]),\n'
    '        ("privacy_data", ["mlex data privacy", "edpb", "cnil", "datatilsynet",\n'
    '                           "hunton privacy", "techgdpr", "noyb",\n'
    '                           "future of privacy", "ico (uk", "ico "]),\n'
    '        ("fintech",    ["mlex financial", "mlex financial services",\n'
    '                         "mlex financial crime"]),\n'
    '    ]\n'
    '    for cat, src_keys in SOURCE_CAT_MAP:\n'
    '        if any(k in source for k in src_keys):\n'
    '            return cat'
)

if old_cat in content:
    content = content.replace(old_cat, new_cat, 1)
    changes += 1
    print("Fix 1: SOURCE_CAT_MAP added")
else:
    print("Fix 1 SKIPPED - old block not found")

# FIX 2: diversity cap
old_cap = (
    "    for cat in categorised:\n"
    "        cap = CAT_CAPS.get(cat, TARGET_PER_CATEGORY)\n"
    "        categorised[cat] = sorted(\n"
    "            categorised[cat], key=score, reverse=True\n"
    "        )[:cap]"
)

new_cap = (
    '    SOURCE_CAP_DEFAULT  = 5\n'
    '    SOURCE_CAP_TRUSTED  = 12\n'
    '    SOURCE_CAP_REGIONAL = 3\n'
    '    REGIONAL_SOURCES = {\n'
    '        "economic times", "livemint", "inc42", "techcabal", "techloy",\n'
    '        "techpoint africa", "techcentral", "moneyweb", "ventureburn",\n'
    '        "jota", "telesintese", "startups.com.br",\n'
    '    }\n'
    '\n'
    '    def apply_diversity_cap(articles, cat_cap):\n'
    '        sorted_arts = sorted(articles, key=score, reverse=True)\n'
    '        source_counts = {}\n'
    '        out = []\n'
    '        for a in sorted_arts:\n'
    '            src = a.get("source", "").lower()\n'
    '            trusted = is_trusted(a.get("source", ""))\n'
    '            regional = any(r in src for r in REGIONAL_SOURCES)\n'
    '            if trusted:\n'
    '                cap = SOURCE_CAP_TRUSTED\n'
    '            elif regional:\n'
    '                cap = SOURCE_CAP_REGIONAL\n'
    '            else:\n'
    '                cap = SOURCE_CAP_DEFAULT\n'
    '            current = source_counts.get(src, 0)\n'
    '            if current < cap:\n'
    '                out.append(a)\n'
    '                source_counts[src] = current + 1\n'
    '            if len(out) >= cat_cap:\n'
    '                break\n'
    '        return out\n'
    '\n'
    '    for cat in categorised:\n'
    '        cap = CAT_CAPS.get(cat, TARGET_PER_CATEGORY)\n'
    '        categorised[cat] = apply_diversity_cap(categorised[cat], cap)'
)

if old_cap in content:
    content = content.replace(old_cap, new_cap, 1)
    changes += 1
    print("Fix 2: diversity cap added")
else:
    print("Fix 2 SKIPPED")

# FIX 3: broken URLs
url_fixes = [
    ('("DG COMP (Competition)",           "https://competition-policy.ec.europa.eu/rss.xml"),',
     '("DG COMP (Competition)",           "https://competition-policy.ec.europa.eu/news_en"),\n    ("CMA Blog",                        "https://competitionandmarkets.blog.gov.uk/feed/"),\n    ("ProMarket / Stigler Center",      "https://promarket.org/feed/"),'),
    ('("Kluwer Competition Law Blog",      "https://competitionlawblog.kluwerarbitration.com/feed/"),',
     '("Kluwer Competition Law Blog",      "https://www.kluwercompetitionlaw.com/blog/feed/"),'),
    ('("Reed Smith Antitrust Report",      "https://www.antitrustandcompetitionreport.com/feed/"),',
     '("CPI Antitrust Chronicle",          "https://www.competitionpolicyinternational.com/feed/"),'),
    ('("Hogan Lovells Insights",           "https://www.hoganlovells.com/en/insights"),',
     '("ICO (UK Privacy Regulator)",       "https://www.gov.uk/search/news-and-communications.atom?organisations%5B%5D=information-commissioner-s-office"),'),
    ('("CPI / PYMNTS Latest",              "https://www.pymnts.com/cpi/latest-news-for-cpi/"),',
     '("IPO UK (Patent & TM Office)",      "https://www.gov.uk/search/news-and-communications.atom?organisations%5B%5D=intellectual-property-office"),'),
]
url_changes = 0
for old_url, new_url in url_fixes:
    if old_url in content:
        content = content.replace(old_url, new_url, 1)
        url_changes += 1

changes += url_changes
print(f"Fix 3: {url_changes} URL fixes applied")

with open("agent/scraper.py", "w") as f:
    f.write(content)

print(f"Done: {changes} total changes, size={len(content)}")
