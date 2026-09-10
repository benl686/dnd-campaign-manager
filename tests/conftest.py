# Make root-level modules (treasure_tables, character_lib, …) importable when
# pytest is run from the project root. tests/ has no __init__.py, so pytest
# adds tests/ (not the root) to sys.path — this shim adds the parent.
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
