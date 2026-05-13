# agent/__init__.py
# Auto-apply scraper patches before scraper.py loads (diversity caps + URL fixes)
import os as _os, importlib.util as _ilu, sys as _sys

_patch = _os.path.join(_os.path.dirname(_os.path.dirname(__file__)), "patch_scraper.py")
if _os.path.exists(_patch):
    _spec = _ilu.spec_from_file_location("patch_scraper", _patch)
    _mod = _ilu.module_from_spec(_spec)
    try:
        _spec.loader.exec_module(_mod)
    except SystemExit:
        pass  # patch_scraper exits 0 when already patched
