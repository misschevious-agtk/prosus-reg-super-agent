import sys, json, os, re

_here = os.path.dirname(os.path.abspath(__file__))
_d = json.load(open(os.path.join(_here, "patch_data.json")))

with open("agent/scraper.py") as f:
    content = f.read()

already_cap      = "PER_SOURCE_CAP" in content
already_law360   = "law360" in content.lower()
already_cma_blog = "competitionandmarkets.blog" in content
already_dgcomp   = "presscorner/api/rss?keywords=competition" in content
already_edri     = "edri.org" in content
already_weetracker = "weetracker.com" in content
already_no_mlex  = "mlex.com" not in content

if all([already_cap, already_law360, already_cma_blog, already_dgcomp,
        already_edri, already_weetracker, already_no_mlex]):
    print("patch_scraper: fully patched, nothing to do")
    sys.exit(0)

changes = 0
lines = content.split("\n")
new_lines = []
i = 0

while i < len(lines):
    l = lines[i]

    # MLEX REMOVAL

    # Skip MLex RSS section header comments
    if re.search(r"#\s*MLEX", l) or re.search(r"#\s*Requires MLEX_USERNAME", l):
        i += 1
        continue

    # Skip MLex RSS source tuples
    if '"MLex ' in l and "mlex.com" in l:
        i += 1
        continue

    # Skip MLex label in TRUSTED_SOURCES comment + value
    if l.strip() == "# MLex premium feeds":
        i += 1
        continue
    if l.strip() in ('"mlex",', '"mlex"'):
        i += 1
        continue

    # Skip "mlex" in scoring/categorise inline lists
    if re.match(r'\s+"mlex",\s*$', l):
        i += 1
        continue

    # Skip MLex auth session block (from _mlex_session = None through end of _get_mlex_session)
    if re.match(r"^_mlex_session\s*=\s*None", l.strip()):
        while i < len(lines):
            if lines[i].strip() == "" and i + 1 < len(lines) and lines[i+1].strip().startswith("def fetch"):
                break
            i += 1
        i += 1  # consume the blank line
        continue

    # Skip MLex comments inside fetch()
    if "# Try authenticated session for MLex" in l:
        i += 1
        continue
    if "# (MLex RSS feeds are publicly accessible" in l:
        i += 1
        continue

    # Replace mlex.com branch in fetch() with simple requests.get
    if '"mlex.com" in url:' in l:
        indent = len(l) - len(l.lstrip())
        while i < len(lines):
            if "requests.get(url, headers=headers, timeout=14)" in lines[i]:
                new_lines.append(" " * indent + "r = requests.get(url, headers=headers, timeout=14)")
                i += 1
                break
            i += 1
        continue

    new_lines.append(l)
    i += 1

content = "\n".join(new_lines)

if "mlex.com" not in content:
    changes += 1
    print("Fix MLex: all MLex references removed")
else:
    remaining = [l for l in content.split("\n") if "mlex" in l.lower()]
    print("WARNING: %d MLex refs remain:" % len(remaining))
    for l in remaining[:5]:
        print(" ", l.strip()[:80])

# REMAINING PATCHES (source additions, caps, etc.)

if not already_cap and _d["old_cap"] in content:
    content = content.replace(_d["old_cap"], _d["new_cap"], 1)
    changes += 1
    print("Fix: diversity cap added")

if not already_law360 and _d["old_c"] in content:
    content = content.replace(_d["old_c"], _d["old_c"] + _d["add_c"], 1)
    changes += 1
    print("Fix: added Law360/ProMarket/CPI")

if not already_law360 and _d["old_t"] in content:
    content = content.replace(_d["old_t"], _d["new_t"], 1)
    changes += 1
    print("Fix: updated TRUSTED_SOURCES")

if not already_dgcomp and _d["old_dgcomp"] in content:
    content = content.replace(_d["old_dgcomp"], _d["new_dgcomp"], 1)
    changes += 1
    print("Fix: DG COMP RSS URL corrected")

if not already_cma_blog and _d["old_cma_entry"] in content:
    content = content.replace(_d["old_cma_entry"], _d["old_cma_entry"] + _d["add_cma"], 1)
    changes += 1
    print("Fix: added CMA Blog + Politico EU Tech")

if not already_edri and _d["old_promarket"] in content:
    content = content.replace(_d["old_promarket"], _d["old_promarket"] + _d["add_competition"], 1)
    changes += 1
    print("Fix: added EDRi/Access Now/Netzpolitik/BEUC/CDT/EFF/Reg Review + competition authorities")

if not already_weetracker and _d["old_techpoint"] in content:
    content = content.replace(_d["old_techpoint"], _d["old_techpoint"] + _d["add_after_techpoint"], 1)
    changes += 1
    print("Fix: added WeeTracker/TI Brazil/IP Finance/PatentDocs")

with open("agent/scraper.py", "w") as f:
    f.write(content)

print("Done: %d changes, scraper size=%d" % (changes, len(content)))
