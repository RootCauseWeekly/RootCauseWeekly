"""Grade a work dir against the hidden upstream regression tests.

usage: grade.py <task-id> <workdir> [--fixed]   (--fixed: apply the real upstream fix first, sanity check)
Copies the grader's test files over the work dir copy, runs the full test suite with a hard timeout,
prints a JSON verdict. Never writes into the agent's run dir: grades a throwaway copy.
"""
import json, os, shutil, subprocess, sys, tempfile, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TASKS = {
    "t1-naturalsize": dict(repo="humanize", venv="humanize", pythonpath="src", tests="tests"),
    "t2-intword": dict(repo="humanize", venv="humanize", pythonpath="src", tests="tests"),
    "t3-tabulate-hang": dict(repo="python-tabulate", venv="tabulate", pythonpath=".", tests="test"),
}
TIMEOUT = 120


def run(task, workdir, fixed=False):
    cfg = TASKS[task]
    g = ROOT / "grader" / task
    with tempfile.TemporaryDirectory() as tmp:
        dst = Path(tmp) / "w"
        shutil.copytree(workdir, dst, ignore=shutil.ignore_patterns(".git", ".venv", "__pycache__", ".pytest_cache"))
        if fixed:
            fix = (g / "FIX_COMMIT").read_text().strip()
            diff = subprocess.run(["git", "-C", str(ROOT / "upstream" / cfg["repo"]), "show", fix],
                                  capture_output=True, text=True, check=True).stdout
            subprocess.run(["git", "apply", "--include=*", "-"], input=diff, text=True, cwd=dst, check=True)
        for f in g.rglob("*"):
            if f.is_file() and f.name not in ("BASE_COMMIT", "FIX_COMMIT"):
                rel = f.relative_to(g)
                (dst / rel).parent.mkdir(parents=True, exist_ok=True)
                shutil.copy(f, dst / rel)
        env = dict(os.environ, PYTHONPATH=str(dst / cfg["pythonpath"]), SETUPTOOLS_SCM_PRETEND_VERSION="0.0.0")
        py = ROOT / "venvs" / cfg["venv"] / "bin" / "python"
        t0 = time.time()
        try:
            p = subprocess.run([str(py), "-m", "pytest", "-q", "--color=no", "-p", "no:cacheprovider", cfg["tests"]],
                               cwd=dst, env=env, capture_output=True, text=True, timeout=TIMEOUT)
            tail = (p.stdout + p.stderr).strip().splitlines()[-15:]
            verdict = "PASS" if p.returncode == 0 else "FAIL"
        except subprocess.TimeoutExpired:
            tail, verdict = [f"timed out after {TIMEOUT}s"], "HANG"
        return dict(task=task, verdict=verdict, secs=round(time.time() - t0, 1), tail=tail)


if __name__ == "__main__":
    print(json.dumps(run(sys.argv[1], sys.argv[2], "--fixed" in sys.argv), indent=1))
