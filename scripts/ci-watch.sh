#!/usr/bin/env bash
# Plays the role of the CI server trigger: "on push to main, run the pipeline".
# Polls the source repo on Gitea every 5 seconds and runs ci-pipeline.sh for
# every new commit. Leave it running in its own terminal during the demo.
source "$(dirname "$0")/lib.sh"
set +e

last=""
mkdir -p "$WORKSPACE/.ci"
HEARTBEAT="$WORKSPACE/.ci/watch.heartbeat"
trap 'rm -f "$HEARTBEAT"' EXIT
printf 'Watching %s/%s/%s (main). Ctrl+C to stop.\n' "$GITEA_URL" "$GITEA_USER" "$SOURCE_REPO"
while true; do
  date +%s > "$HEARTBEAT"
  head=$(git ls-remote "$GITEA_URL/$GITEA_USER/$SOURCE_REPO.git" refs/heads/main 2>/dev/null | cut -f1)
  if [ -n "$head" ] && [ "$head" != "$last" ]; then
    if [ -z "$last" ]; then
      printf 'Current main is %s. Waiting for new pushes...\n' "${head:0:7}"
    else
      printf '\n%s[%s] push detected on main: %s%s\n' "$c_yellow" "$(date +%H:%M:%S)" "${head:0:7}" "$c_off"
      if bash "$ROOT/scripts/ci-pipeline.sh"; then
        printf '%s[%s] pipeline succeeded%s\n' "$c_green" "$(date +%H:%M:%S)" "$c_off"
      else
        printf '%s[%s] pipeline FAILED, nothing was deployed%s\n' "$c_red" "$(date +%H:%M:%S)" "$c_off"
      fi
    fi
    last=$head
  fi
  sleep 5
done
