import sys, json, os
_d = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "patch_data.json")))
with open("agent/scraper.py") as f:
    content = f.read()
already_has_cap = "PER_SOURCE_CAP" in content
already_has_law360 = "law360" in content.lower()
already_has_cma_blog = "competitionandmarkets.blog" in content
already_has_dgcomp_fixed = "presscorner/api/rss?keywords=competition" in content
if already_has_cap and already_has_law360 and already_has_cma_blog and already_has_dgcomp_fixed:
    print("patch_scraper: fully patched")
    sys.exit(0)
changes = 0
# FIX 1: Remove duplicate GCR HTML entry
if _d["old_gcr"] in content:
    content = content.replace(_d["old_gcr"], "    # GCR /news removed", 1)
    changes += 1
    print("Fix 1: removed GCR duplicate")
# FIX 2: Per-source diversity cap
if not already_has_cap and _d["old_cap"] in content:
    content = content.replace(_d["old_cap"], _d["new_cap"], 1)
    changes += 1
    print("Fix 2: diversity cap added")
elif not already_has_cap:
    print("Fix 2 SKIPPED")
# FIX 3: Add Law360/ProMarket/CPI to RSS_SOURCES
if not already_has_law360 and _d["old_c"] in content:
    content = content.replace(_d["old_c"], _d["old_c"] + _d["add_c"], 1)
    changes += 1
    print("Fix 3: added Law360/ProMarket/CPI")
# FIX 4: Update TRUSTED_SOURCES
if not already_has_law360 and _d["old_t"] in content:
    content = content.replace(_d["old_t"], _d["new_t"], 1)
    changes += 1
    print("Fix 4: updated TRUSTED_SOURCES")
# FIX 5: Fix broken DG COMP RSS URL
if not already_has_dgcomp_fixed and _d["old_dgcomp"] in content:
    content = content.replace(_d["old_dgcomp"], _d["new_dgcomp"], 1)
    changes += 1
    print("Fix 5: fixed DG COMP RSS URL")
# FIX 6: Add CMA Blog + Politico EU Tech
if not already_has_cma_blog and _d["old_cma_entry"] in content:
    content = content.replace(_d["old_cma_entry"], _d["old_cma_entry"] + _d["add_cma"], 1)
    changes += 1
    print("Fix 6: added CMA Blog + Politico EU Tech")
with open("agent/scraper.py", "w") as f:
    f.write(content)
print("Done: %d changes, size=%d" % (changes, len(content)))