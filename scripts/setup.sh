#!/usr/bin/env bash
# One-shot bring-up of the whole GitOps environment on this machine.
# Safe to re-run: every step skips work that is already done.
source "$(dirname "$0")/lib.sh"

step "Checking tools"
for tool in docker kind kubectl git; do
  command -v "$tool" >/dev/null || die "$tool is not installed"
done
docker info >/dev/null 2>&1 || die "Docker is not running. Start Docker Desktop first."
ok "docker, kind, kubectl, git"

# 1. Kubernetes cluster ------------------------------------------------------
step "1/7 Kubernetes cluster '$CLUSTER'"
if kind get clusters 2>/dev/null | grep -qx "$CLUSTER" && \
   kubectl --context "$KCTX" get nodes >/dev/null 2>&1; then
  ok "cluster already exists and is reachable"
else
  if kind get clusters 2>/dev/null | grep -qx "$CLUSTER"; then
    warn "cluster exists but its API is unreachable; recreating it"
    kind delete cluster --name "$CLUSTER"
  fi
  kind create cluster --config "$ROOT/infra/kind-cluster.yaml" --wait 120s
fi
kubectl config use-context "$KCTX" >/dev/null
ok "kubectl context set to $KCTX"

# 2. Container registry ------------------------------------------------------
step "2/7 Local container registry at $REGISTRY"
if [ "$(docker inspect -f '{{.State.Running}}' "$REGISTRY_NAME" 2>/dev/null)" != "true" ]; then
  docker rm -f "$REGISTRY_NAME" >/dev/null 2>&1 || true
  docker run -d --restart=always --name "$REGISTRY_NAME" \
    -p "127.0.0.1:$REGISTRY_PORT:5000" registry:2 >/dev/null
fi
docker network connect kind "$REGISTRY_NAME" 2>/dev/null || true
# Tell containerd on every node that localhost:5001 means the registry container.
for node in $(kind get nodes --name "$CLUSTER"); do
  dir="/etc/containerd/certs.d/localhost:$REGISTRY_PORT"
  docker exec "$node" mkdir -p "$dir"
  printf '[host."http://%s:5000"]\n' "$REGISTRY_NAME" | docker exec -i "$node" cp /dev/stdin "$dir/hosts.toml"
done
wait_for 60 "registry answering" curl -sf "http://$REGISTRY/v2/"
if ! curl -sf "http://$REGISTRY/v2/node/manifests/22-alpine" -H "Accept: application/vnd.oci.image.index.v1+json, application/vnd.docker.distribution.manifest.list.v2+json, application/vnd.docker.distribution.manifest.v2+json, application/vnd.oci.image.manifest.v1+json" >/dev/null; then
  docker image inspect node:22-alpine >/dev/null 2>&1 || docker pull node:22-alpine
  docker tag node:22-alpine "$BASE_IMAGE"
  docker push -q "$BASE_IMAGE" >/dev/null
fi
ok "registry running, base image mirrored, wired into cluster nodes"

# 3. Git server --------------------------------------------------------------
step "3/7 Local Git server (Gitea) at $GITEA_URL"
if [ "$(docker inspect -f '{{.State.Running}}' "$GITEA_NAME" 2>/dev/null)" != "true" ]; then
  docker rm -f "$GITEA_NAME" >/dev/null 2>&1 || true
  docker run -d --restart=always --name "$GITEA_NAME" --network kind \
    -p "$GITEA_PORT:3000" \
    -e GITEA__database__DB_TYPE=sqlite3 \
    -e GITEA__security__INSTALL_LOCK=true \
    -e GITEA__server__ROOT_URL="$GITEA_URL/" \
    -e GITEA__server__OFFLINE_MODE=true \
    -e GITEA__service__DISABLE_REGISTRATION=true \
    -e GITEA__repository__ENABLE_PUSH_CREATE_USER=true \
    -e GITEA__repository__DEFAULT_PUSH_CREATE_PRIVATE=false \
    "$GITEA_IMAGE" >/dev/null
fi
wait_for 120 "Gitea is answering" curl -sf "$GITEA_URL/api/healthz"
if ! curl -sf -u "$GITEA_USER:$GITEA_PASS" "$GITEA_URL/api/v1/user" >/dev/null; then
  docker exec -u git "$GITEA_NAME" gitea admin user create \
    --username "$GITEA_USER" --password "$GITEA_PASS" \
    --email "$GITEA_USER@local.test" --admin --must-change-password=false >/dev/null
fi
ok "Gitea user $GITEA_USER ready"

# 4. ArgoCD ------------------------------------------------------------------
step "4/7 Installing ArgoCD"
kc create namespace argocd --dry-run=client -o yaml | kc apply -f - >/dev/null
kc apply -n argocd --server-side --force-conflicts -f "$ROOT/infra/argocd-install.yaml" >/dev/null
# Serve the UI over plain HTTP and poll Git every 10 seconds instead of 3 minutes.
kc -n argocd patch configmap argocd-cmd-params-cm --type merge -p '{"data":{"server.insecure":"true"}}' >/dev/null
kc -n argocd patch configmap argocd-cm --type merge -p '{"data":{"timeout.reconciliation":"10s","timeout.reconciliation.jitter":"0s"}}' >/dev/null
# Expose the UI on a NodePort that kind maps to localhost:8080. No port-forward needed.
kc -n argocd patch svc argocd-server --type merge \
  -p '{"spec":{"type":"NodePort","ports":[{"name":"http","port":80,"protocol":"TCP","targetPort":8080,"nodePort":30808},{"name":"https","port":443,"protocol":"TCP","targetPort":8080,"nodePort":30843}]}}' >/dev/null
kc -n argocd rollout restart deployment argocd-server argocd-repo-server >/dev/null
kc -n argocd rollout restart statefulset argocd-application-controller >/dev/null
kc -n argocd rollout status deployment argocd-server --timeout=300s
kc -n argocd rollout status deployment argocd-repo-server --timeout=300s
kc -n argocd rollout status statefulset argocd-application-controller --timeout=300s
wait_for 180 "ArgoCD UI reachable at $ARGOCD_URL" curl -sf "$ARGOCD_URL/healthz"
# Replace the random initial admin password with a fixed one for the demo.
if ! curl -sf "$ARGOCD_URL/api/v1/session" -H "Content-Type: application/json"     -d "{\"username\":\"admin\",\"password\":\"$ARGOCD_PASS\"}" >/dev/null; then
  hash=$(kc -n argocd exec deploy/argocd-server -- argocd account bcrypt --password "$ARGOCD_PASS")
  kc -n argocd patch secret argocd-secret --type merge     -p "{\"stringData\":{\"admin.password\":\"$hash\",\"admin.passwordMtime\":\"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"}}" >/dev/null
  wait_for 60 "ArgoCD admin password set to $ARGOCD_PASS" curl -sf "$ARGOCD_URL/api/v1/session"     -H "Content-Type: application/json" -d "{\"username\":\"admin\",\"password\":\"$ARGOCD_PASS\"}"
fi

# 5. Git repositories --------------------------------------------------------
step "5/7 Creating the two Git repositories"
mkdir -p "$WORKSPACE"

# push_template <template dir> <repo name> <commit message>
push_template() {
  local src=$1 name=$2 msg=$3 dest="$WORKSPACE/$2"
  if curl -sf "$GITEA_URL/api/v1/repos/$GITEA_USER/$name" >/dev/null; then
    ok "$name already on Gitea"
    [ -d "$dest/.git" ] || git clone -q "$GITEA_AUTH_URL/$GITEA_USER/$name.git" "$dest"
    return
  fi
  rm -rf "$dest"
  mkdir -p "$dest"
  cp -r "$src/." "$dest/"
  git -C "$dest" init -q -b main
  git -C "$dest" config user.name "Developer"
  git -C "$dest" config user.email "developer@local.test"
  git -C "$dest" add .
  git -C "$dest" commit -q -m "$msg"
  git -C "$dest" remote add origin "$GITEA_AUTH_URL/$GITEA_USER/$name.git"
  git -C "$dest" push -q -u origin main
  ok "$name pushed to $GITEA_URL/$GITEA_USER/$name"
}
push_template "$ROOT/config-repo" "$CONFIG_REPO" "Initial Kubernetes manifests"
push_template "$ROOT/app" "$SOURCE_REPO" "Initial todo app"

# 6. First CI run ------------------------------------------------------------
step "6/7 Running the CI pipeline once for the first image"
current_tag=$(grep -oE "image: .*" "$WORKSPACE/$CONFIG_REPO/manifest.yml" | head -1 || true)
if sync_repo "$WORKSPACE/$CONFIG_REPO" && grep -q ":initial" "$WORKSPACE/$CONFIG_REPO/manifest.yml"; then
  bash "$ROOT/scripts/ci-pipeline.sh"
else
  ok "config repo already points at a built image ($current_tag)"
fi

# 7. ArgoCD application ------------------------------------------------------
step "7/7 Registering the application with ArgoCD"
kc apply -f "$ROOT/infra/argocd-application.yaml" >/dev/null
wait_for 300 "ArgoCD reports todo-app Synced and Healthy" \
  bash -c "[ \"\$(kubectl --context $KCTX -n argocd get application todo-app -o jsonpath='{.status.sync.status}/{.status.health.status}')\" = 'Synced/Healthy' ]"
wait_for 120 "todo app reachable at $APP_URL" curl -sf "$APP_URL/healthz"

pass=$(argocd_password)
cat > "$WORKSPACE/credentials.txt" <<EOF
ArgoCD UI   $ARGOCD_URL   user: admin    password: $pass
Gitea       $GITEA_URL    user: $GITEA_USER   password: $GITEA_PASS
Todo app    $APP_URL
Registry    http://$REGISTRY/v2/_catalog
EOF

printf '\n%sEverything is up.%s\n\n' "$c_green" "$c_off"
cat "$WORKSPACE/credentials.txt"
printf '\nNext: "gitops open" opens the pages. Run "gitops ci-watch" in a second terminal, then "gitops release".\n'
