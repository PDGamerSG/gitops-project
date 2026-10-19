#!/usr/bin/env bash
# Open the demo pages in the default browser.
source "$(dirname "$0")/lib.sh"

for url in "$APP_URL" \
  "$ARGOCD_URL/applications/argocd/todo-app?view=tree" \
  "$GITEA_URL/$GITEA_USER/$CONFIG_REPO/commits/branch/main"; do
  cmd /c start "" "$url"
done
printf 'ArgoCD login: admin / %s\nGitea login:  %s / %s\n' "$ARGOCD_PASS" "$GITEA_USER" "$GITEA_PASS"
printf 'In the ArgoCD tree, if pods are cut off, collapse the sidebar (arrow, top left) and click zoom out twice.\n'
