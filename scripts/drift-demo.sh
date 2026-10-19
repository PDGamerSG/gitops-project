#!/usr/bin/env bash
# Configuration drift demo. Changes the live cluster by hand, the way an admin
# with kubectl would, then times how long ArgoCD self-heal takes to undo it.
source "$(dirname "$0")/lib.sh"

desired=$(grep -m1 -oE 'replicas: *[0-9]+' "$ROOT/config-repo/manifest.yml" | grep -oE '[0-9]+')
[ -f "$WORKSPACE/$CONFIG_REPO/manifest.yml" ] && \
  desired=$(grep -m1 -oE 'replicas: *[0-9]+' "$WORKSPACE/$CONFIG_REPO/manifest.yml" | grep -oE '[0-9]+')

state() {
  local replicas svc
  replicas=$(kc get deploy todo-app -o jsonpath='{.spec.replicas}' 2>/dev/null || echo "?")
  svc=$(kc get svc todo-app -o name 2>/dev/null || echo "missing")
  printf 'replicas=%s  service=%s  argocd=%s' "$replicas" "${svc#service/}" \
    "$(kc -n argocd get application todo-app -o jsonpath='{.status.sync.status}/{.status.health.status}')"
}

step "Git says: replicas=$desired, service todo-app exists"
printf '  live now: %s\n' "$(state)"

step "Manual change 1: kubectl scale deployment todo-app --replicas=8"
kc scale deployment todo-app --replicas=8
step "Manual change 2: kubectl delete service todo-app"
kc delete service todo-app --wait=false
printf '  live now: %s\n' "$(state)"

step "Waiting for ArgoCD to put the cluster back to what Git says"
start=$SECONDS
while true; do
  r=$(kc get deploy todo-app -o jsonpath='{.spec.replicas}' 2>/dev/null || echo 0)
  if [ "$r" = "$desired" ] && kc get svc todo-app >/dev/null 2>&1; then break; fi
  printf '  %2ss  %s\n' $((SECONDS - start)) "$(state)"
  (( SECONDS - start > 180 )) && die "self-heal did not finish in 180s"
  sleep 1
done
ok "drift reverted in $((SECONDS - start))s: $(state)"
printf '\nArgoCD history: %s/applications/argocd/todo-app\n' "$ARGOCD_URL"
