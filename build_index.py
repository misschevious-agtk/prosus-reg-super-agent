#!/usr/bin/env python3
"""Trim index.json to keep GitHub Pages payload lean."""
import json, pathlib

ROOT = pathlib.Path(__file__).parent
IN   = ROOT / "content" / "index.json"

SKIP_KEYS = {
    "ai_landscape","chatbot","chatbot_regulation","ai_agents",
    "gig_economy","platform_liability","consumer_protection",
    "ip","privacy","regulatory","policy_society"
}
BODY_LIMIT = 60

data = json.loads(IN.read_text())
new_data = {}

for key, val in data.items():
    if key in SKIP_KEYS:
        continue
    if isinstance(val, list):
        is_flash = (key == "flash_alerts")
        trimmed = []
        for a in val:
            art = {}
            for k, v in a.items():
                if k in ("watchlist_hits", "tags", "scope_path", "uid", "published_at"):
                    continue
                elif k == "id" and not is_flash:
                    continue
                elif k == "prosus_lens":
                    if v:
                        art["lens"] = v[:130]
                elif k == "entity_match":
                    if v:
                        art["portfolio"] = v[:3]
                elif k == "body":
                    art["body"] = (v or "")[:BODY_LIMIT]
                else:
                    art[k] = v
            trimmed.append(art)
        new_data[key] = trimmed
    else:
        new_data[key] = val

out = json.dumps(new_data, ensure_ascii=False, separators=(",",":"))
IN.write_text(out)
print(f"index.json: {len(out)//1024}KB ({len(out)} chars)")
