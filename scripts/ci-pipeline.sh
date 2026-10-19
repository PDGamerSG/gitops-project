#!/usr/bin/env bash
# CI half of the flow (push). Same steps as app/.github/workflows/prod.yml:
#   checkout -> test + build image -> push image -> bump tag in config repo -> push
# It never touches the cluster. ArgoCD pulls the change on its own.
source "$(dirname "$0")/lib.sh"

CI_DIR="$WORKSPACE/.ci"
BUILD_DIR="$CI_DIR/build"
OPS_DIR="$CI_DIR/ops"
mkdir -p "$CI_DIR"

step "CI: checkout $SOURCE_REPO@main"
rm -rf "$BUILD_DIR"
git clone -q --depth 1 "$GITEA_AUTH_URL/$GITEA_USER/$SOURCE_REPO.git" "$BUILD_DIR"
SHA=$(git -C "$BUILD_DIR" rev-parse HEAD)
SHORT=${SHA:0:7}
AUTHOR_MSG=$(git -C "$BUILD_DIR" log -1 --format='%s (%an)')
ok "commit $SHORT: $AUTHOR_MSG"

step "CI: run tests and build image $REGISTRY/$IMAGE_NAME:$SHA"
docker build --build-arg BASE_IMAGE="$BASE_IMAGE" --build-arg GIT_SHA="$SHA" -t "$REGISTRY/$IMAGE_NAME:$SHA" "$BUILD_DIR"
ok "tests passed, image built"

step "CI: push image to registry"
docker push -q "$REGISTRY/$IMAGE_NAME:$SHA" >/dev/null
ok "pushed $REGISTRY/$IMAGE_NAME:$SHA"

step "CI: update image tag in $CONFIG_REPO"
rm -rf "$OPS_DIR"
git clone -q "$GITEA_AUTH_URL/$GITEA_USER/$CONFIG_REPO.git" "$OPS_DIR"
sed -i "s|image: .*/$IMAGE_NAME:.*|image: $REGISTRY/$IMAGE_NAME:$SHA|" "$OPS_DIR/manifest.yml"
if git -C "$OPS_DIR" diff --quiet; then
  ok "manifest already uses $SHORT, nothing to commit"
else
  git -C "$OPS_DIR" config user.name "CI Bot"
  git -C "$OPS_DIR" config user.email "ci-bot@local.test"
  git -C "$OPS_DIR" commit -q -am "Update $IMAGE_NAME image tag to $SHA"
  git -C "$OPS_DIR" push -q origin main
  ok "pushed commit $(git -C "$OPS_DIR" rev-parse --short HEAD) to $CONFIG_REPO"
fi

# Keep the developer's copy of the config repo current, if there is one.
[ -d "$WORKSPACE/$CONFIG_REPO/.git" ] && sync_repo "$WORKSPACE/$CONFIG_REPO" 2>/dev/null || true

printf '\n%sCI finished.%s ArgoCD will detect the new tag within about 10 seconds.\n' "$c_green" "$c_off"
