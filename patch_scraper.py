import sys

with open("agent/scraper.py") as f:
    content = f.read()

if "PER_SOURCE_CAP" in content:
    print("patch_scraper: already patched")
    sys.exit(0)

changes = 0

# FIX 1: Remove duplicate GCR /news HTML entry
old_gcr = '    ("Global Competition Review",        "https://globalcompetitionreview.com/news"),'
if old_gcr in content:
    content = content.replace(old_gcr, "    # GCR /news removed (RSS at line 180 is canonical)", 1)
    changes += 1
    print("Fix 1: removed duplicate GCR /news entry")
else:
    print("Fix 1: GCR /news not found (ok)")

# FIX 2: Per-source diversity cap
old_cap = "    for cat in categorised:\n        cap = CAT_CAPS.get(cat, TARGET_PER_CATEGORY)\n        categorised[cat] = sorted(\n            categorised[cat], key=score, reverse=True\n        )[:cap]\n"
new_cap = """    # Per-source diversity cap (added by patch_scraper)
    PER_SOURCE_CAP = {
        "competition": 8, "ai_tech": 6, "privacy_data": 6,
        "ip_brand": 6, "fintech": 6, "platform_gig": 6,
    }
    from collections import defaultdict
    for _cat in list(categorised.keys()):
        _cap = PER_SOURCE_CAP.get(_cat, 5)
        _counts = defaultdict(int)
        _filtered = []
        for _a in sorted(categorised[_cat], key=score, reverse=True):
            _src = _a.get("source", "unknown")
            if _counts[_src] < _cap:
                _filtered.append(_a)
                _counts[_src] += 1
        categorised[_cat] = _filtered

    for cat in categorised:
        cap = CAT_CAPS.get(cat, TARGET_PER_CATEGORY)
        categorised[cat] = sorted(
            categorised[cat], key=score, reverse=True
        )[:cap]
"""

if old_cap in content:
    content = content.replace(old_cap, new_cap, 1)
    changes += 1
    print("Fix 2: per-source diversity cap added (max 8 GCR in competition)")
else:
    print("Fix 2 SKIPPED - target not found")

with open("agent/scraper.py", "w") as f:
    f.write(content)

print(f"Done: {changes} changes applied, scraper size={len(content)}")
