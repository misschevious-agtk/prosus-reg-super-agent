import sys, json, os
_here = os.path.dirname(os.path.abspath(__file__))
_d = json.load(open(os.path.join(_here, "patch_data.json")))
with open("agent/scraper.py") as f:
    content = f.read()

already_cap      = "PER_SOURCE_CAP" in content
already_law360   = "law360" in content.lower()
already_cma_blog = "competitionandmarkets.blog" in content
already_dgcomp   = "presscorner/api/rss?keywords=competition" in content
already_edri     = "edri.org" in content
already_jota     = "jota.info" in content

if all([already_cap, already_law360, already_cma_blog, already_dgcomp, already_edri, already_jota]):
    print("patch_scraper: fully patched, nothing to do")
    sys.exit(0)

changes = 0

# FIX 1: Remove duplicate GCR HTML entry
if _d["old_gcr"] in content:
    content = content.replace(_d["old_gcr"], "    # GCR /news removed", 1)
    changes += 1
    print("Fix 1: removed GCR duplicate")

# FIX 2: Per-source diversity cap
if not already_cap and _d["old_cap"] in content:
    content = content.replace(_d["old_cap"], _d["new_cap"], 1)
    changes += 1
    print("Fix 2: diversity cap added")

# FIX 3: Add Law360/ProMarket/CPI to RSS_SOURCES
if not already_law360 and _d["old_c"] in content:
    content = content.replace(_d["old_c"], _d["old_c"] + _d["add_c"], 1)
    changes += 1
    print("Fix 3: added Law360/ProMarket/CPI")

# FIX 4: Update TRUSTED_SOURCES
if not already_law360 and _d["old_t"] in content:
    content = content.replace(_d["old_t"], _d["new_t"], 1)
    changes += 1
    print("Fix 4: updated TRUSTED_SOURCES")

# FIX 5: Fix broken DG COMP RSS URL
if not already_dgcomp and _d["old_dgcomp"] in content:
    content = content.replace(_d["old_dgcomp"], _d["new_dgcomp"], 1)
    changes += 1
    print("Fix 5: fixed DG COMP RSS URL")

# FIX 6: Add CMA Blog + Politico EU Tech (old slot)
if not already_cma_blog and _d["old_cma_entry"] in content:
    content = content.replace(_d["old_cma_entry"], _d["old_cma_entry"] + _d["add_cma"], 1)
    changes += 1
    print("Fix 6: added CMA Blog + Politico EU Tech")

# FIX 7: Add competition authorities + EU policy sources after ProMarket
if not already_edri and _d["old_promarket"] in content:
    content = content.replace(_d["old_promarket"], _d["old_promarket"] + _d["add_competition"], 1)
    changes += 1
    print("Fix 7: added competition authorities + EU policy sources")

# FIX 8: Add WeeTracker/TI Brazil/IP Finance/PatentDocs after Techpoint Africa
already_weetracker = "weetracker.com" in content
if not already_weetracker and _d["old_techpoint"] in content:
    content = content.replace(_d["old_techpoint"], _d["old_techpoint"] + _d["add_after_techpoint"], 1)
    changes += 1
    print("Fix 8: added WeeTracker/TI Brazil/IP Finance/PatentDocs")

with open("agent/scraper.py", "w") as f:
    f.write(content)
print("Done: %d changes applied, scraper size=%d" % (changes, len(content)))
