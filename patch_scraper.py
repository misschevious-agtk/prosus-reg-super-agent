import sys, json, os
_d = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "patch_data.json")))
with open("agent/scraper.py") as f:
    content = f.read()
already_has_cap = "PER_SOURCE_CAP" in content
already_has_law360 = "law360" in content.lower()
if already_has_cap and already_has_law360:
    print("patch_scraper: fully patched")
    sys.exit(0)
changes = 0
if _d["old_gcr"] in content:
    content = content.replace(_d["old_gcr"], "    # GCR /news removed", 1)
    changes += 1
    print("Fix 1: removed GCR duplicate")
if not already_has_cap and _d["old_cap"] in content:
    content = content.replace(_d["old_cap"], _d["new_cap"], 1)
    changes += 1
    print("Fix 2: diversity cap added")
elif not already_has_cap:
    print("Fix 2 SKIPPED")
if not already_has_law360 and _d["old_c"] in content:
    content = content.replace(_d["old_c"], _d["old_c"] + _d["add_c"], 1)
    changes += 1
    print("Fix 3: added Law360/ProMarket/CPI")
if not already_has_law360 and _d["old_t"] in content:
    content = content.replace(_d["old_t"], _d["new_t"], 1)
    changes += 1
    print("Fix 4: updated TRUSTED_SOURCES")
with open("agent/scraper.py", "w") as f:
    f.write(content)
print("Done: %d changes, size=%d" % (changes, len(content)))
