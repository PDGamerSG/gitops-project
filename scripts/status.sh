#!/usr/bin/env bash
# One screen summary of the whole system.
source "$(dirname "$0")/lib.sh"
set +e

step "Services"
check() { if curl -sf --max-time 3 "$2" >/dev/null; then ok "$1  $3"; else warn "$1 DOWN  $3"; fi; }
check "Gitea    " "$GITEA_URL/api/healthz" "$GITEA_URL"
check "Registry " "http://$REGISTRY/v2/" "http://$REGISTRY/v2/_catalog"
check "ArgoCD   " "$ARGOCD_URL/healthz" "$ARGOCD_URL"
check "Todo app " "$APP_URL/healthz" "$APP_URL"

step "ArgoCD application"
kc -n argocd get application todo-app \
  -o custom-columns='NAME:.metadata.name,SYNC:.status.sync.status,HEALTH:.status.health.status,REVISION:.status.sync.revision'

step "Pods"
kc get pods -l app=todo-app -o wide

step "Image running now"
kc get deploy todo-app -o jsonpath='{.spec.template.spec.containers[0].image}{"\n"}'
curl -sf "$APP_URL/api/info" && echo

step "Last commits in $CONFIG_REPO"
git ls-remote "$GITEA_URL/$GITEA_USER/$CONFIG_REPO.git" >/dev/null 2>&1 && \
  [ -d "$WORKSPACE/$CONFIG_REPO/.git" ] && \
  sync_repo "$WORKSPACE/$CONFIG_REPO" && \
  git -C "$WORKSPACE/$CONFIG_REPO" log --format='  %h %<(10,trunc)%an %s' -5

[ -f "$WORKSPACE/credentials.txt" ] && { step "Logins"; cat "$WORKSPACE/credentials.txt"; }
