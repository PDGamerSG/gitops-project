#!/usr/bin/env bash
# Shared settings for every script. Sourced, not executed.
set -euo pipefail

# Git Bash on Windows rewrites arguments that look like paths. Turn that off.
export MSYS_NO_PATHCONV=1
# Never let git open a credential prompt. All URLs carry their credentials.
export GIT_TERMINAL_PROMPT=0 GCM_INTERACTIVE=never
# Keep LF line endings in the demo repos so sed edits stay clean diffs.
export GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=core.autocrlf GIT_CONFIG_VALUE_0=false

# pwd -W gives E:/path form, which both bash and Windows tools (kind, docker) accept.
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && (pwd -W 2>/dev/null || pwd))"
WORKSPACE="$ROOT/workspace"

CLUSTER=gitops
KCTX="kind-$CLUSTER"

REGISTRY_NAME=kind-registry
REGISTRY_PORT=5001
REGISTRY="localhost:$REGISTRY_PORT"

GITEA_NAME=gitea
GITEA_IMAGE=gitea/gitea:1.24
GITEA_PORT=3300
GITEA_USER=gitops
GITEA_PASS=gitops123
GITEA_URL="http://localhost:$GITEA_PORT"
GITEA_AUTH_URL="http://$GITEA_USER:$GITEA_PASS@localhost:$GITEA_PORT"

SOURCE_REPO=todo-app
CONFIG_REPO=argo-deployment
IMAGE_NAME=todo-app
# Base image mirrored into the local registry so builds never reach Docker Hub.
BASE_IMAGE="$REGISTRY/node:22-alpine"

ARGOCD_URL="http://localhost:8080"
ARGOCD_PASS=admin123
APP_URL="http://localhost:8081"

kc() { kubectl --context "$KCTX" "$@"; }

c_blue=$'\e[1;34m'; c_green=$'\e[1;32m'; c_yellow=$'\e[1;33m'; c_red=$'\e[1;31m'; c_off=$'\e[0m'
step() { printf '\n%s==> %s%s\n' "$c_blue" "$*" "$c_off"; }
ok()   { printf '%s  ok%s %s\n' "$c_green" "$c_off" "$*"; }
warn() { printf '%s  !! %s%s\n' "$c_yellow" "$*" "$c_off"; }
die()  { printf '%s  xx %s%s\n' "$c_red" "$*" "$c_off" >&2; exit 1; }

# wait_for <seconds> <description> <command...>
wait_for() {
  local timeout=$1 desc=$2; shift 2
  local start=$SECONDS
  until "$@" >/dev/null 2>&1; do
    (( SECONDS - start > timeout )) && die "timed out waiting for $desc"
    sleep 2
  done
  ok "$desc"
}

# The workspace clones mirror Gitea. Scripts own them, so hard reset to origin/main
# instead of merging, which also clears line-ending noise.
sync_repo() {
  git -C "$1" fetch -q origin main
  git -C "$1" reset -q --hard origin/main
}

argocd_password() {
  printf '%s' "$ARGOCD_PASS"
}
