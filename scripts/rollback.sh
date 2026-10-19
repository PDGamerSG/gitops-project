#!/usr/bin/env bash
# Rollback the GitOps way: revert the last commit in the config repo.
# No pipeline re-run, no kubectl. ArgoCD sees Git change and follows it.
source "$(dirname "$0")/lib.sh"

REPO="$WORKSPACE/$CONFIG_REPO"
[ -d "$REPO/.git" ] || die "config repo not found. Run setup first."
sync_repo "$REPO"

step "Config repo history (newest first)"
git -C "$REPO" log --oneline -5

commits=$(git -C "$REPO" rev-list --count HEAD)
(( commits > 1 )) || die "only one commit in the config repo, nothing to roll back to"

before=$(grep -m1 -oE 'image: .*' "$REPO/manifest.yml")
git -C "$REPO" config user.name "Developer"
git -C "$REPO" config user.email "developer@local.test"
git -C "$REPO" revert --no-edit HEAD >/dev/null
after=$(grep -m1 -oE 'image: .*' "$REPO/manifest.yml")
git -C "$REPO" push -q origin main

step "Reverted $(git -C "$REPO" rev-parse --short HEAD~1)"
printf '  from  %s\n  to    %s\n' "$before" "$after"
ok "pushed. ArgoCD will roll the pods back within about 10 seconds."
