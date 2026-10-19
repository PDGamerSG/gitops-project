#!/usr/bin/env bash
# Remove everything setup.sh created: cluster, registry, Gitea, workspace.
source "$(dirname "$0")/lib.sh"
set +e

step "Deleting kind cluster $CLUSTER"
kind delete cluster --name "$CLUSTER"
step "Removing registry and Gitea containers"
docker rm -f "$REGISTRY_NAME" "$GITEA_NAME"
step "Removing workspace"
rm -rf "$WORKSPACE"
ok "clean. Run setup again to rebuild."
