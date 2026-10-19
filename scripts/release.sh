#!/usr/bin/env bash
# Acts as the developer: change the app, commit, push to the source repo.
#   release.sh            bump patch version and switch the theme colour
#   release.sh broken     push a commit whose tests fail (CI must block it)
source "$(dirname "$0")/lib.sh"

REPO="$WORKSPACE/$SOURCE_REPO"
[ -d "$REPO/.git" ] || die "source repo not found. Run setup first."
sync_repo "$REPO"

current=$(node -p "require(process.argv[1]).version" "$REPO/version.json" 2>/dev/null \
  || grep -oE '"version": *"[^"]+"' "$REPO/version.json" | grep -oE '[0-9]+\.[0-9]+\.[0-9]+')

if [ "${1:-}" = "broken" ]; then
  next="not-a-version"
  theme="#dc2626"
  message="This release has a bug and should never reach the cluster"
  commit_msg="Broken release (tests will fail)"
else
  IFS=. read -r major minor patch <<<"$current"
  next="$major.$minor.$((patch + 1))"
  themes=("#2563eb" "#059669" "#7c3aed" "#db2777" "#ea580c" "#0891b2")
  theme=${themes[$(( (patch + 1) % ${#themes[@]} ))]}
  message="Release $next shipped at $(date +%H:%M:%S) through Git only"
  commit_msg="Release v$next"
fi

step "Developer: editing version.json ($current -> $next)"
cat > "$REPO/version.json" <<EOF
{
  "version": "$next",
  "theme": "$theme",
  "message": "$message"
}
EOF
git -C "$REPO" config user.name "Developer"
git -C "$REPO" config user.email "developer@local.test"
git -C "$REPO" commit -q -am "$commit_msg"
git -C "$REPO" push -q origin main
ok "pushed $(git -C "$REPO" rev-parse --short HEAD) \"$commit_msg\" to $SOURCE_REPO"

heartbeat="$WORKSPACE/.ci/watch.heartbeat"
if [ -f "$heartbeat" ] && (( $(date +%s) - $(cat "$heartbeat") < 30 )); then
  ok "CI watcher is running and will pick this up"
else
  warn "CI watcher is not running, so running the pipeline here"
  bash "$ROOT/scripts/ci-pipeline.sh" || die "pipeline failed, the cluster keeps running the previous version"
fi

if [ "${1:-}" = "broken" ]; then
  live=$(curl -s "$APP_URL/api/info" | grep -oE '"version":"[^"]+"' | cut -d'"' -f4)
  printf '\nWatch CI fail the tests. The app at %s stays on v%s.\n' "$APP_URL" "${live:-$current}"
  printf 'Undo with: gitops fix-broken\n'
else
  printf '\nOpen %s and watch it roll to v%s. ArgoCD view: %s/applications/argocd/todo-app\n' "$APP_URL" "$next" "$ARGOCD_URL"
fi
