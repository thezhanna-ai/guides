"""Use the corrected live-cover canon rather than the rejected 908eb6e layout."""
from pathlib import Path
import runpy, sys
entry=Path(__file__).resolve().parents[1]/"litso-oblozhka-kanon-20261011"/"build_cover.py"
sys.path.insert(0,str(entry.parent))
runpy.run_path(str(entry),run_name="__main__")
