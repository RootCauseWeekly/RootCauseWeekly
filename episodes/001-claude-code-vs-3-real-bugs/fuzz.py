"""Differential test: each Claude fix vs the real upstream fix, on inputs the hidden tests never tried.

usage: fuzz.py <task-id>          -> compares every runs/<task>/r*/work against upstream-fixed code
Each implementation runs in its own subprocess (with a timeout, since t3 is a hang bug) and prints its
outputs as JSON; any input where they disagree is reported.
"""
import json, os, shutil, subprocess, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
import grade  # noqa: E402

PROBES = {
    "t1-naturalsize": r'''
import json, itertools
from humanize import naturalsize
out = {}
vals = set()
for base in (1000, 1024):
    for e in range(1, 12):
        p = base ** e
        for d in (-1, -2, -5, -50, -500, -5000, 0, 1, 49, 50, 51, 499, 500, 501):
            for m in (1, 999, 1000, 1023, 1024):
                v = m * p // (1000 if m >= 999 else 1) + d
                if v > 0: vals |= {v, -v}
for v in sorted(vals):
    for binary, gnu, fmt in itertools.product((False, True), (False, True), ("%.1f", "%.0f", "%.3f", "%d")):
        try: r = naturalsize(v, binary=binary, gnu=gnu, format=fmt)
        except Exception as ex: r = "EXC " + type(ex).__name__
        out[f"{v}|{binary}|{gnu}|{fmt}"] = r
print(json.dumps(out))
''',
    "t2-intword": r'''
import json, random
from humanize import intword
out = {}; rnd = random.Random(7); vals = set()
for k in range(3, 101):
    for d in (-1, -2, -10, -10**(k//2), -5 * 10**(k-5) if k > 5 else -1, 0, 1, 10**(k//2)):
        v = 10**k + d
        if v > 0: vals |= {v, -v}
for _ in range(5000):
    k = rnd.randint(3, 100); vals.add(rnd.randint(10**k - 10**(k-3), 10**k + 10**(k-3)))
for v in sorted(vals):
    for fmt in ("%.1f", "%.0f", "%.2f", "%.3f"):
        try: r = intword(v, fmt)
        except Exception as ex: r = "EXC " + type(ex).__name__
        out[f"{v}|{fmt}"] = r
print(json.dumps(out))
''',
    "t3-tabulate-hang": r'''
import json, random
import tabulate
out = {}; rnd = random.Random(11)
alpha = ["a", "b", " ", "-", "한", "글", "中", "文", "\U0001F600", "\x1b[31m", "\x1b[0m", "é", "é"]
cases = ["한글", "a한", "한 a", "\U0001F600\U0001F600", "\x1b[31m한글\x1b[0m"]
for _ in range(1500): cases.append("".join(rnd.choice(alpha) for _ in range(rnd.randint(1, 14))))
for s in cases:
    for w in (1, 2, 3, 4, 7):
        try: r = tabulate._CustomTextWrap(width=w).wrap(s)
        except Exception as ex: r = "EXC " + type(ex).__name__
        out[f"{s!r}|{w}"] = r
print(json.dumps(out))
''',
}


def outputs(task, workdir):
    cfg = grade.TASKS[task]
    env = dict(os.environ, PYTHONPATH=str(Path(workdir) / cfg["pythonpath"]))
    py = ROOT / "venvs" / cfg["venv"] / "bin" / "python"
    try:
        p = subprocess.run([str(py), "-c", PROBES[task]], cwd=tempfile.gettempdir(), env=env,
                           capture_output=True, text=True, timeout=900)
        return json.loads(p.stdout) if p.returncode == 0 else {"__error__": p.stderr[-500:]}
    except subprocess.TimeoutExpired:
        return {"__error__": "HANG (timeout 120s)"}


def upstream_fixed(task, tmp):
    cfg = grade.TASKS[task]
    dst = Path(tmp) / "upstream"
    shutil.copytree(ROOT / "tasks" / task / "base", dst)
    fix = (ROOT / "grader" / task / "FIX_COMMIT").read_text().strip()
    diff = subprocess.run(["git", "-C", str(ROOT / "upstream" / cfg["repo"]), "show", fix],
                          capture_output=True, text=True, check=True).stdout
    subprocess.run(["git", "apply", "-"], input=diff, text=True, cwd=dst, check=True)
    return dst


if __name__ == "__main__":
    task = sys.argv[1]
    with tempfile.TemporaryDirectory() as tmp:
        ref = outputs(task, upstream_fixed(task, tmp))
        base = outputs(task, ROOT / "tasks" / task / "base")
    assert "__error__" not in ref, ref
    report = {"task": task, "inputs": len(ref),
              "original_bug_differs": "__error__" in base and base["__error__"] or sum(base.get(k) != v for k, v in ref.items())}
    for w in sorted(ROOT.glob(f"runs/{task}/r*/work")):
        got = outputs(task, w)
        if "__error__" in got:
            report[w.parent.name] = got["__error__"]; continue
        diffs = [(k, ref[k], got.get(k)) for k in ref if got.get(k) != ref[k]]
        report[w.parent.name] = {"mismatches": len(diffs), "examples": diffs[:5]}
    print(json.dumps(report, indent=1, ensure_ascii=False))
