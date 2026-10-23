"""Re-grade every run from its saved diff against the hidden upstream tests. Run ./setup.sh first.

usage: python3 regrade.py      -> one line per run, then the total (expected: 9/9 PASS)
"""
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
import grade  # noqa: E402

rows = []
for work in sorted(ROOT.glob("runs/*/r*/work")):
    task, run = work.parent.parent.name, work.parent.name
    g = grade.run(task, work)
    rows.append(g["verdict"] == "PASS")
    print(f"{task:18} {run}  {g['verdict']:4}  {g['tail'][-1]}")
if not rows: sys.exit("no work dirs found: run ./setup.sh first")
print(f"\n{sum(rows)}/{len(rows)} PASS")
sys.exit(0 if all(rows) else 1)
