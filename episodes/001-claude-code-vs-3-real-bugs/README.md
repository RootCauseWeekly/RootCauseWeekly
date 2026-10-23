# Claude Code vs 3 real bugs: the receipts

This is the evidence behind the Root Cause video [**"Claude Code Fixed 9/9 Real Bugs. Then I Checked Harder."**](https://youtu.be/OWmdR0hGPY0)

[![Watch on YouTube](https://img.youtube.com/vi/OWmdR0hGPY0/maxresdefault.jpg)](https://youtu.be/OWmdR0hGPY0)

## Setup
- **Bugs:** three real, already-fixed bugs from MIT-licensed projects. Each task is the project's code at the parent of the real fix commit.

  | Task | Bug | Source |
  |---|---|---|
  | t1 | humanize `naturalsize()` printed "1000.0 kB" | https://github.com/python-humanize/humanize/pull/329 |
  | t2 | humanize `intword()` printed "1000.0 sextillion" | https://github.com/python-humanize/humanize/pull/346 |
  | t3 | python-tabulate `_CustomTextWrap` hung forever | https://github.com/astanin/python-tabulate/issues/399 |

- **Agent:** Claude Code 2.1.309, model `claude-opus-5-5`, running headless (`claude -p`, see `run.py`). It had no user settings, CLAUDE.md, memory or MCP servers. Its only tools were Bash, Read, Edit and Write, and its only input was the bug report (`prompt.txt`).
- **Grader:** the project's own regression test from the real fix commit, kept outside the agent's folder (`grader/`). It was hashed before the runs (`grader.sha256`) and checked after them (`grader.verify.txt`, all OK). `audit.py` checks every transcript for grader access and network use; both were 0 in every run.
- **Runs:** 3 fresh sessions per bug. Each has its `prompt.txt`, `fix.diff`, `meta.json` and `transcript.jsonl`. The stream-json transcripts have system/init events removed and local paths redacted.

## Results (`results.json`)
- **Tests:** 9/9 runs passed the hidden upstream tests, for $1.13 total and 35–54 s per run.
- **Differential testing** (`fuzz.py`, `fuzz2.py`): each fix was compared against the real fix and against the pre-fix code.
  - **t1:** 0 differences on 37,664 inputs.
  - **t2:** runs 2 and 3 had 0 differences on 25,936 inputs. Run 1 had 32, all at 10^100 − 1 and its neighbours (100 digits). That's where the real fix still prints a huge "decillion" count: known issue humanize #356.
  - **t3:** across 6,910 strings, the pre-fix code hangs on 1,291. Every fix removes all of those hangs. The real fix 032dc0d (master only, unreleased) also changes 201 outputs that previously terminated, and all 201 have a line wider than `width`. Claude runs 1 and 2 changed 0 of them. Run 3 changed 147 (107 differ only in whitespace or escape-code placement, 40 have the same text with different line breaks, such as a dropped leading blank line) and produced 0 over-width lines.
  - Reported upstream as [python-tabulate #478](https://github.com/astanin/python-tabulate/issues/478).

## Reproduce it

You need git, [uv](https://docs.astral.sh/uv/) and Python 3.
```bash
./setup.sh                                    # clones upstream, rebuilds the pre-fix snapshots, envs, and each run's code (~10 s)
python3 regrade.py                            # re-grades all 9 runs with the hidden upstream tests -> 9/9 PASS
python3 fuzz.py t2-intword                    # each fix vs the real fix (also t1-naturalsize, t3-tabulate-hang)
venvs/tabulate/bin/python fuzz2.py t3         # t3 vs the pre-fix code: the 201 over-width outputs
venvs/humanize/bin/python fuzz2.py t2         # t2 run 1: the 32 differences, all at 100 digits
```
Re-running the agent itself (`python3 run.py <task> <n>`) needs Claude Code installed and logged in, and it costs a few cents per run. Model outputs vary, so expect your diffs to differ from the ones saved here.

## Caveats
- These are small, single-function bugs, and each report included a repro.
- The t1 and t3 fixes are near or before the model's training cutoff. Only t2 (Sep 2026) is clearly after it.
- Claude Code also helped build this harness. The fuzz probes were written after the test results were in.
