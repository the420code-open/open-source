#!/bin/bash
# The run day: waits until its start (by default 00:01 Cape Town time on 16 November 2026, 22:01 UTC on the 15th; G,
# 15 November 2026, in chat: "Run at 12:01 today", so 12:01 Cape Town time, 10:01 UTC), then runs run_day.py with
# every maker's key put in its environment by makers_key.py run, one inside the other; the keys are never written
# anywhere. AG Opus, through G, 15 November 2026: "If every route passes, the run takes 16 November, from 00:01 Cape
# Town time, with its known roads' arm the same day."
FR=…/open-source/challenge/first-roads
RUN=$FR/${2:-run-2026-11-16}
V=…/venv-suite/Scripts/python.exe
KEY="…/tools/open/makers_key.py"
START=$(date -u -d "${1:-2026-11-15T22:01:00Z}" +%s)
mkdir -p "$RUN"
$V -I $FR/runner/stay_awake.py 40 &
AWAKE=$!
trap 'kill $AWAKE 2>/dev/null' EXIT
echo "$(date -u +%FT%TZ) waiting for ${1:-2026-11-15T22:01:00Z}" >> "$RUN/launch.log"
while [ "$(date -u +%s)" -lt "$START" ]; do sleep 15; done
if ! $V -I $FR/runner/run_day.py ready "$RUN" >> "$RUN/launch.log" 2>&1; then
  echo "$(date -u +%FT%TZ) not started: a route has not passed its check" >> "$RUN/launch.log"
  exit 4
fi
echo "$(date -u +%FT%TZ) starting" >> "$RUN/launch.log"
CMD=()
for m in anthropic openai google xai meta mistral deepinfra kimi; do CMD+=(python "$KEY" run $m --); done
"${CMD[@]}" $V -I $FR/runner/run_day.py run "$RUN" >> "$RUN/launch.log" 2>&1
echo "$(date -u +%FT%TZ) run_day.py exited with $?" >> "$RUN/launch.log"
