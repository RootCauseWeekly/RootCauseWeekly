"""Deeper checks. t2: bucket every r1-vs-upstream mismatch by digit count.
t3: per-input timeout so the pre-fix (hanging) code can be compared input by input; classify every
difference from the pre-fix output for upstream and each Claude run."""
import json, re, subprocess, sys, tempfile, os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import fuzz, grade
ROOT = Path(__file__).resolve().parent

T3_PER_INPUT = fuzz.PROBES["t3-tabulate-hang"].replace(
    "        try: r = tabulate._CustomTextWrap(width=w).wrap(s)\n        except Exception as ex: r = \"EXC \" + type(ex).__name__",
    "        signal.setitimer(signal.ITIMER_REAL, 0.3)\n        try: r = tabulate._CustomTextWrap(width=w).wrap(s)\n        except TimeoutError: r = \"HANG\"\n        except Exception as ex: r = \"EXC \" + type(ex).__name__\n        signal.setitimer(signal.ITIMER_REAL, 0)",
).replace("import json, random", "import json, random, signal\ndef _h(*a): raise TimeoutError\nsignal.signal(signal.SIGALRM, _h)")
assert "HANG" in T3_PER_INPUT

def outs(task, wd, probe=None):
    if probe: fuzz.PROBES[task] = probe
    return fuzz.outputs(task, Path(wd).resolve())

if sys.argv[1] == "t2":
    with tempfile.TemporaryDirectory() as t:
        up = outs("t2-intword", fuzz.upstream_fixed("t2-intword", t))
    r1 = outs("t2-intword", ROOT / "runs/t2-intword/r1/work")
    from collections import Counter
    print(Counter(len(k.split("|")[0].lstrip("-")) for k in up if up[k] != r1[k]))
else:
    import wcwidth
    strip = lambda s: re.sub(r"\x1b\[[0-9;]*m", "", s)
    # a line is over-width if it is wider than the requested width, except a lone character that can never
    # fit (a 2-column character in a 1-column slot); ' 文' at width 2 counts: the space did not have to be there
    over = lambda k, v: isinstance(v, list) and any(wcwidth.wcswidth(strip(l)) > int(k.rsplit("|", 1)[1]) and len(strip(l)) > 1 for l in v)
    base = outs("t3-tabulate-hang", ROOT / "tasks/t3-tabulate-hang/base", T3_PER_INPUT)
    with tempfile.TemporaryDirectory() as t:
        impls = {"upstream": outs("t3-tabulate-hang", fuzz.upstream_fixed("t3-tabulate-hang", t))}
    for r in ("r1", "r2", "r3"): impls[r] = outs("t3-tabulate-hang", ROOT / f"runs/t3-tabulate-hang/{r}/work")
    hang = [k for k, v in base.items() if v == "HANG"]
    term = [k for k in base if base[k] != "HANG"]
    print(f"inputs {len(base)}: pre-fix hangs on {len(hang)}, terminates on {len(term)}")
    for name, o in impls.items():
        changed = [k for k in term if o[k] != base[k]]
        def kind(k):
            vis = lambda lines: [strip(x) for x in lines]
            if over(k, o[k]): return "over_width"
            if [x.strip() for x in vis(o[k])] == [x.strip() for x in vis(base[k])]: return "whitespace_or_escape_placement"
            if "".join(vis(o[k])).replace(" ", "") == "".join(vis(base[k])).replace(" ", ""): return "same_text_different_line_breaks"
            return "text_changed"
        from collections import Counter
        cls = dict(Counter(kind(k) for k in changed))
        ex = [(k, base[k], o[k]) for k in changed if not over(k, o[k])][:3]
        print(name, "changes vs pre-fix on terminating inputs:", len(changed), cls,
              "| hang inputs still hanging:", sum(o[k] == "HANG" for k in hang), "| over-width total:", sum(over(k, v) for k, v in o.items()))
        for e in ex: print("    e.g.", e)
