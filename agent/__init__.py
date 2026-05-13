# agent/__init__.py - auto-patch scraper before load
import os as _os, importlib.util as _ilu, sys as _sys

_repo = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
_patch = _os.path.join(_repo, "patch_scraper.py")
_orig_dir = _os.getcwd()
print("[init] repo=%s patch_exists=%s" % (_repo, _os.path.exists(_patch)))
if _os.path.exists(_patch):
    _os.chdir(_repo)
    _spec = _ilu.spec_from_file_location("patch_scraper", _patch)
    _mod = _ilu.module_from_spec(_spec)
    _mod.__file__ = _patch
    try:
        _spec.loader.exec_module(_mod)
    except SystemExit:
        pass
    finally:
        _os.chdir(_orig_dir)
