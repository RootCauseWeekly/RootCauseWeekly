"""Run one isolated headless Claude Code attempt on a task, then grade it.

usage: run.py <task-id> <attempt-n>
Work dir: runs/<task>/r<n>/work (fresh copy of the pre-fix snapshot, single git commit, no upstream history).
The grader lives in grader/<task>, outside the work dir. Outputs: transcript.jsonl, meta.json, fix.diff.
"""
import json, os, shutil, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
import grade  # noqa: E402

REPORTS = {
    "t1-naturalsize": ("humanize", "src", """\
`naturalsize()` gives the wrong unit right below a boundary:

>>> from humanize import naturalsize
>>> naturalsize(999999)
'1000.0 kB'      # expected '1.0 MB'
>>> naturalsize(999999999)
'1000.0 MB'      # expected '1.0 GB'
>>> naturalsize(1024 ** 2 - 1, binary=True)
'1024.0 KiB'     # expected '1.0 MiB'"""),
    "t2-intword": ("humanize", "src", """\
`intword()` gives the wrong word for some very large numbers:

>>> import humanize
>>> humanize.intword(10**24 - 1)
'1000.0 sextillion'      # expected '1.0 septillion'
>>> humanize.intword(10**27 - 1)
'1000.0 septillion'      # expected '1.0 octillion'"""),
    "t3-tabulate-hang": ("tabulate", ".", """\
An infinite loop on wide characters:

>>> import tabulate
>>> data = "\\ud55c\\uae00"  # Korean text, each char is 2 display columns wide
>>> tabulate._CustomTextWrap(width=1).wrap(data)   # never returns"""),
}

PROMPT = """You are working in a checkout of the open-source Python library `{project}`. A user filed this bug report:

{report}

Find the root cause and fix it in the library code. Use `.venv/bin/python` to run code and tests \
(set PYTHONPATH={pythonpath}). Do not use the internet. When you are done, briefly explain the root cause and your fix."""

FLAGS = ["--model", "claude-opus-5-5", "--setting-sources", "project", "--strict-mcp-config",
         "--mcp-config", '{"mcpServers":{}}', "--no-session-persistence", "--output-format", "stream-json",
         "--verbose", "--tools", "Bash,Read,Edit,Write", "--allowedTools", "Bash", "Read", "Edit", "Write",
         "--permission-mode", "acceptEdits", "--max-budget-usd", "5",
         "--settings", '{"enabledPlugins":{"worklog-nudge@inline":false,"db-status@inline":false,"bucket@inline":false}}']
ENV = dict(os.environ, CLAUDE_CODE_DISABLE_CLAUDE_MDS="1", CLAUDE_CODE_DISABLE_AUTO_MEMORY="1")


def main(task, n):
    venv, pythonpath, report = REPORTS[task]
    out = ROOT / "runs" / task / f"r{n}"
    shutil.rmtree(out, ignore_errors=True)
    work = out / "work"
    shutil.copytree(ROOT / "tasks" / task / "base", work)
    (work / ".venv").symlink_to(ROOT / "venvs" / venv)
    (work / ".gitignore").open("a").write("\n.venv\n")
    git = lambda *a: subprocess.run(["git", "-C", str(work), *a], check=True, capture_output=True)
    git("init", "-q"); git("add", "-A")
    git("-c", "user.name=lab", "-c", "user.email=lab@example.invalid", "commit", "-qm", "snapshot")
    project = "tabulate" if venv == "tabulate" else "humanize"
    prompt = PROMPT.format(project=project, report=report, pythonpath=pythonpath)
    (out / "prompt.txt").write_text(prompt)
    t0 = time.time()
    with open(out / "transcript.jsonl", "w") as f:
        try:
            p = subprocess.run(["claude", "-p", prompt, *FLAGS], cwd=work, stdout=f, stderr=subprocess.PIPE,
                               stdin=subprocess.DEVNULL, text=True, timeout=1800, env=ENV)
            rc, err = p.returncode, p.stderr[-2000:]
        except subprocess.TimeoutExpired:
            rc, err = "timeout", ""
    wall = round(time.time() - t0, 1)
    diff = subprocess.run(["git", "-C", str(work), "diff"], capture_output=True, text=True).stdout
    (out / "fix.diff").write_text(diff)
    result = next((json.loads(l) for l in open(out / "transcript.jsonl") if '"type":"result"' in l), {})
    g = grade.run(task, work)
    meta = dict(task=task, attempt=n, rc=rc, wall_s=wall, verdict=g["verdict"], grade_tail=g["tail"][-3:],
                cost_usd=result.get("total_cost_usd"), duration_ms=result.get("duration_ms"),
                num_turns=result.get("num_turns"), is_error=result.get("is_error"),
                files_changed=[l[6:] for l in diff.splitlines() if l.startswith("+++ b/")], stderr=err)
    (out / "meta.json").write_text(json.dumps(meta, indent=1))
    print(json.dumps({k: meta[k] for k in ("task", "attempt", "verdict", "cost_usd", "wall_s", "num_turns", "files_changed")}))


if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]))
