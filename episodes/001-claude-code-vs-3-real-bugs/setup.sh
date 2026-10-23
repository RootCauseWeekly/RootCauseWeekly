#!/usr/bin/env bash
# Rebuild everything the scripts need that isn't checked in: upstream clones, the pre-fix snapshots,
# the Python environments, and each run's work dir (snapshot + Claude's fix.diff).
# Needs: git, uv (https://docs.astral.sh/uv/). Run from this folder: ./setup.sh
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p upstream tasks venvs
clone() { [ -d "upstream/$1" ] || git clone -q --filter=blob:none "https://github.com/$2.git" "upstream/$1"; }
clone humanize python-humanize/humanize
clone python-tabulate astanin/python-tabulate

snapshot() {   # task repo
  local id=$1 repo=$2 base; base=$(cat "grader/$id/BASE_COMMIT")
  rm -rf "tasks/$id/base"; mkdir -p "tasks/$id/base"
  git -C "upstream/$repo" archive "$base" | tar -x -C "tasks/$id/base"
  if [ "$repo" = humanize ]; then   # hatch-vcs normally generates this file at install time
    printf '__version__ = version = "0.0.0"\n__version_tuple__ = version_tuple = (0, 0, 0)\n' > "tasks/$id/base/src/humanize/_version.py"
  fi
}
snapshot t1-naturalsize humanize
snapshot t2-intword humanize
snapshot t3-tabulate-hang python-tabulate

for v in humanize tabulate; do
  [ -x "venvs/$v/bin/python" ] || uv venv -q -p 3.12 "venvs/$v"
  uv pip install -q -p "venvs/$v/bin/python" -r "requirements/$v.txt"
done

for d in runs/*/r*/; do   # each run's final code = snapshot + the diff Claude Code produced
  task=$(basename "$(dirname "$d")"); rm -rf "$d/work"; cp -R "tasks/$task/base" "$d/work"
  (cd "$d/work" && git apply --whitespace=nowarn ../fix.diff)
done
echo "ready: python3 regrade.py  (re-grades all 9 runs)  ·  python3 fuzz.py <task>  ·  python3 run.py <task> <n>"
