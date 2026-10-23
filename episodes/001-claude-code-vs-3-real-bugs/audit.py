"""Audit run transcripts: grader access, network use, personal-info leakage. usage: audit.py [runs/...]"""
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BAD_PATH = re.compile(r"grader|upstream/|\.\./\.\./|001-claude-code-test/(?!runs)")
NETWORK = re.compile(r"\b(curl|wget|pip install|uv pip|git (fetch|pull|clone|remote)|requests\.get|urllib|WebFetch|WebSearch)\b")
LEAK = re.compile(r"<private-terms>|slack|work-log|claude\.md|serena|rtk\b|mcp__", re.I)

dirs = [Path(a) for a in sys.argv[1:]] or sorted(ROOT.glob("runs/*/r*"))
bad = False
for d in dirs:
    calls, leaks = [], set()
    for line in open(d / "transcript.jsonl"):
        e = json.loads(line)
        if e.get("type") == "assistant":
            for c in e["message"].get("content", []):
                if c.get("type") == "tool_use":
                    s = json.dumps(c["input"])
                    calls.append((c["name"], s))
                if c.get("type") in ("text", "tool_use"):
                    leaks |= set(m.lower() for m in LEAK.findall(json.dumps(c).replace("~", "~")))
    grader = [s[:120] for _, s in calls if BAD_PATH.search(s)]
    net = [s[:120] for _, s in calls if NETWORK.search(s)]
    ok = not grader and not net
    bad |= not ok
    print(f"{d.relative_to(ROOT)}: {len(calls)} tool calls, grader-access={len(grader)}, network={len(net)}, "
          f"visible-leaks={sorted(leaks) or 'none'} -> {'CLEAN' if ok else 'FLAG'}")
    for s in grader + net:
        print("   ", s)
sys.exit(1 if bad else 0)
