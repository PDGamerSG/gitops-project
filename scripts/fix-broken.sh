#!/usr/bin/env bash
# Revert the broken commit in the source repo so main builds again.
source "$(dirname "$0")/lib.sh"

REPO="$WORKSPACE/$SOURCE_REPO"
sync_repo "$REPO"
if ! git -C "$REPO" log -1 --format=%s | grep -q "^Broken release"; then
  die "latest source commit is not a broken release, nothing to fix"
fi
git -C "$REPO" revert --no-edit HEAD >/dev/null
git -C "$REPO" push -q origin main
ok "reverted broken commit, pushed $(git -C "$REPO" rev-parse --short HEAD)"
printf 'CI will rebuild the previous good code with a new tag.\n'
