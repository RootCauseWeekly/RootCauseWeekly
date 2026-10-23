<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/banner-dark.png">
  <img alt="Root Cause: Why software fails. Tested, not hyped." src="assets/banner-light.png">
</picture>

<p align="center">
  <a href="https://www.youtube.com/@RootCauseWeekly"><img alt="YouTube @RootCauseWeekly" src="https://img.shields.io/badge/YouTube-@RootCauseWeekly-c4302b?style=for-the-badge&logo=youtube&logoColor=white"></a>
  <img alt="New episode weekly" src="https://img.shields.io/badge/new%20episode-weekly-007979?style=for-the-badge">
  <img alt="Every claim has receipts" src="https://img.shields.io/badge/every%20claim-has%20receipts-1c844e?style=for-the-badge">
</p>

---

**Root Cause** is a YouTube channel about why software breaks.

Every episode takes one failure (a famous outage, a nasty bug, or an AI tool under real pressure), finds the actual root cause, and explains it in plain words. No hype and no guessing. If a number shows up on screen, it has a source. If something is tested on screen, the logs are in this repo.

## Two series

| | Series | What happens |
|---|---|---|
| 🔍 | **Disaster breakdowns** | One real software failure, explained from the first symptom to the line that caused it. Knight Capital, CrowdStrike, Therac-25, and more. |
| 🧪 | **AI, put to the test** | Real tasks, isolated runs, hidden graders, and every result shown, including the failures. Currently testing Claude Code. |

## Episodes

| # | Episode | Format | Receipts |
|---|---|---|---|
| 001 | **[Claude Code Fixed 9/9 Real Bugs. Then I Checked Harder.](https://youtu.be/OWmdR0hGPY0)** | Long-form · 9 min | [logs, grader, results](episodes/001-claude-code-vs-3-real-bugs) · found [tabulate #478](https://github.com/astanin/python-tabulate/issues/478) |
| S01 | **A decade-old bug in 70% of the web. AI found it.** (PHP2Shell) | Short | sources in the video description |

More breakdowns are on the way. [Subscribe on YouTube](https://www.youtube.com/@RootCauseWeekly) to catch them.

## How tests on this channel work

When something gets tested, these rules apply. Episode 001 is the first one run this way.

1. **Real problems only.** Bugs come from real open-source projects, rolled back to the commit before the real fix. Nothing is made up for the camera.
2. **The grader isn't mine.** Each project's own regression tests decide pass or fail. They're kept outside the AI's folder and hashed before and after every run.
3. **Isolated runs.** No personal settings, no memory, no internet, and every log is audited afterwards.
4. **Repeat it.** Each task is run several times, and every run is reported.
5. **Go past the tests.** Differential testing compares the new code against the old code on thousands of inputs, because passing tests isn't the same as being right.
6. **Say what it doesn't prove.** Every episode ends with its limits.

## What's in this repo

```
episodes/
  001-claude-code-vs-3-real-bugs/   run.py · grade.py · audit.py · fuzz.py · results.json
                                    grader/ (hashed) · runs/ (prompts, diffs, transcripts)
```

Clone it, read the transcripts, and rerun the graders: each episode folder has a `setup.sh` and step-by-step instructions. Found a mistake? [File a correction](../../issues/new?template=correction.yml).

## Suggest an episode

What should break next? [Suggest an episode](../../issues/new?template=episode-idea.yml), or leave a comment under any video.

## License

Code (scripts and harnesses) is [MIT](LICENSE). Write-ups, data and transcripts are [CC BY 4.0](LICENSE-CC-BY-4.0.txt): reuse them freely with credit to Root Cause. Third-party code that the scripts fetch keeps its own license.

<p align="center"><sub>Root Cause · faceless, weekly, and every claim comes with receipts.</sub></p>
