#!/bin/bash
# python scripts/live.py is run from the repo root; MSYS_NO_PATHCONV stops Git Bash turning /command into a Windows path
export MSYS_NO_PATHCONV=1
L=/c/bench/project-zomboid-rl-based-players/.pzclient/Logs
for c in "$@"; do
  python scripts/live.py bot smokechat "$c" >/dev/null; sleep ${WAIT:-8}; python scripts/live.py bot smokeweather free >/dev/null; sleep 3
  echo "$c -> $(grep -a 'WEATHER raining' $L/$(ls -t $L | grep DebugLog.txt | head -1) | tail -1 | sed 's/.*WEATHER/WEATHER/')"
done
