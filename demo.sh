#!/usr/bin/env bash
# Run with: bash demo.sh
# Recording helper: prints each command, then runs it. Use PAUSE=0 for an instant run.
set -e
PAUSE=${PAUSE:-1.5}
run() { echo; echo "\$ $*"; sleep "$PAUSE"; "$@"; sleep "$PAUSE"; }
run python -m lifecycle --as-of 2026-09-30 --out out
run python -c "import json; m=[x for x in json.load(open('out/campaign_plan.json'))['messages'] if x['segment']=='at_risk']; print(json.dumps(m[:2], indent=2))"
