# GitOps continuous deployment with ArgoCD

This repository is a complete, runnable GitOps example. The fastest way to run
the app by itself is `docker compose up --build`, then open
http://localhost:3000. The full demo uses the setup below to create a local
Kubernetes cluster, registry, Gitea server, and ArgoCD controller.

Live project showcase: https://gitops-project.vercel.app

The public showcase includes a live control-plane console with three linked
views: the Todo workload, Gitea desired state, and the ArgoCD application tree.
Changes made in the App tab are projected into a new desired-state commit,
manifest image tag, ArgoCD sync phase, and three-pod resource tree. The state
is kept in the browser and shared across open tabs, so the control-plane views
can be shown side by side during a presentation.

The root repository is the source of truth for the demo. The `app` directory is
the deployable Node.js service; `config-repo` contains the desired Kubernetes
state; and `infra` plus `scripts` provision and exercise the delivery flow.

This project builds the pull-based GitOps pipeline described in the review 1 document. Everything runs on one Windows machine. After the first setup it needs no internet and no GitHub, Docker Hub, or cloud account.

| Piece in the review document | What this project runs locally |
|---|---|
| Source Git repo | `todo-app` repo on a Gitea server, http://localhost:3300 |
| CI server (GitHub Actions) | `scripts/ci-pipeline.sh`, triggered by `gitops ci-watch` |
| Container registry (Docker Hub) | `registry:2` container, `localhost:5001` |
| Config Git repo (`argo-deployment`) | `argo-deployment` repo on the same Gitea server |
| Kubernetes cluster (DigitalOcean) | kind cluster `gitops`, 1 control plane and 2 workers |
| GitOps controller | ArgoCD v3.5.3, UI at http://localhost:8080 |
| PAT token for the ops repo | Gitea user `gitops`, credentials in the push URL |

`app/.github/workflows/prod.yml` has the GitHub Actions version of the same pipeline, for running it against GitHub and Docker Hub later.

## How the flow works

```
 Developer                CI (push phase)                         CD (pull phase, inside the cluster)
 ---------                ---------------                         -----------------------------------
 git push  ---> todo-app repo
                    |
                    v
              ci-watch sees new commit
                    |
                    v
              docker build (runs unit tests)
              docker push localhost:5001/todo-app:<sha>
              clone argo-deployment, sed image tag, commit, push
                                                  |
                                                  v
                                        argo-deployment repo  <--- ArgoCD polls every 10 s
                                                                         |
                                                                         v
                                                               kubectl apply inside cluster
                                                               rolling update of 3 pods
```

The CI side never gets cluster credentials. It only writes to Git. ArgoCD runs inside the cluster, reads Git, and applies the change. The ArgoCD application has `automated`, `prune` and `selfHeal` turned on, so a manual `kubectl` change gets reverted within seconds.

## Requirements

Already installed on this machine:

- Docker Desktop (running)
- kind, kubectl
- Git for Windows (the scripts run in its bash)

Setup uses about 3 GB of Docker disk space and 4 GB of RAM. Keep at least 10 GB free on C:. Docker Desktop crashed once during testing when the disk was full.

## Commands

Run these from PowerShell or cmd inside the `gitops-project` folder.

| Command | What it does |
|---|---|
| `.\gitops setup` | Creates the cluster, registry, Gitea, ArgoCD, both repos, the first image and the ArgoCD application. Takes about 5 minutes the first time. Safe to run again. |
| `.\gitops ci-watch` | The CI server. Polls the `todo-app` repo every 5 seconds and runs the pipeline for each new commit. Keep it open in its own terminal. |
| `.\gitops release` | Plays the developer. Bumps the version in `version.json`, changes the theme colour, commits and pushes. |
| `.\gitops release broken` | Pushes a commit whose unit tests fail. CI stops at the build and the cluster keeps the old version. |
| `.\gitops fix-broken` | Reverts the broken commit so CI builds again. |
| `.\gitops drift-demo` | Scales the deployment to 8 replicas and deletes its service with kubectl, then prints how many seconds ArgoCD takes to restore both. |
| `.\gitops rollback` | Runs `git revert` on the last commit in `argo-deployment`. ArgoCD rolls the pods back to the previous image. |
| `.\gitops open` | Opens the todo app, the ArgoCD tree view and the Gitea commit list in your browser. |
| `.\gitops showcase` | Serves the public showcase locally at http://localhost:4173 so the live Workload, Gitea, and ArgoCD views can be presented offline. Set `SHOWCASE_PORT` to change the port. |
| `.\gitops status` | Shows service health, ArgoCD sync state, pods, the running image and the config repo history. |
| `.\gitops teardown` | Deletes the cluster, registry, Gitea and the `workspace` folder. |

Logins are printed at the end of setup and saved to `workspace\credentials.txt`.

- ArgoCD: user `admin`, password `admin123`. Setup replaces the random initial password with this one.
- Gitea: user `gitops`, password `gitops123`.

## Presentation script

Run `.\gitops open`, or open these by hand. On a laptop screen the ArgoCD tree cuts off the pods on the right. Click the arrow at the top left of ArgoCD to collapse the sidebar, then click zoom out twice. The whole tree then fits.

Have four windows ready before you start: the todo app (http://localhost:8081), the ArgoCD app page (http://localhost:8080/applications/argocd/todo-app), the Gitea config repo commits (http://localhost:3300/gitops/argo-deployment/commits/branch/main), and a terminal running `.\gitops ci-watch`.

1. **Show the running system.** Run `.\gitops status`. Point out 3 pods, the image tag, which equals a Git commit SHA, and the ArgoCD state `Synced/Healthy`.
2. **Deploy through Git only.** Run `.\gitops release` in a second terminal. The CI terminal runs the tests, builds, pushes the image and commits the new tag. Within about a minute the ArgoCD tree shows a new ReplicaSet, and the app header switches colour and version. The Gitea commit list shows the commit from `CI Bot`. Nobody ran kubectl.
3. **Configuration drift and self-heal.** Run `.\gitops drift-demo`. It scales to 8 replicas and deletes the service by hand. ArgoCD marks the app `OutOfSync` and restores 3 replicas and the service, usually in under 10 seconds.
4. **Rollback is a Git revert.** Run `.\gitops rollback`. It shows the before and after image tags. The app returns to the previous version in about 20 seconds.
5. **Bad code never ships.** Run `.\gitops release broken`. The CI terminal prints `not ok` for a test and `pipeline FAILED`. The app stays on its current version. Run `.\gitops fix-broken` to recover.

Measured on this machine: commit to fully rolled out in 35 to 60 seconds, rollback in 19 seconds, drift reverted in 6 seconds.

## After a reboot

1. Start Docker Desktop and wait until it says running.
2. The cluster, registry and Gitea containers restart on their own. Wait about a minute.
3. Run `.\gitops status`. If a service shows `DOWN`, run `.\gitops setup`. It skips the finished steps and repairs the rest.

## Project layout

```
gitops-project/
  gitops.cmd                    Windows entry point, runs scripts\<command>.sh with Git Bash
  app/                          template for the todo-app source repo
    server.js                   Node.js todo API and page, no npm dependencies
    version.json                version, theme colour, message shown in the header
    test/server.test.js         unit tests, run inside docker build
    Dockerfile                  stage 1 runs tests, stage 2 is the runtime image
    .github/workflows/prod.yml  GitHub Actions version of the pipeline
  config-repo/manifest.yml      template for the argo-deployment repo (Deployment + NodePort Service)
  infra/
    kind-cluster.yaml           3 node cluster, host ports 8080 and 8081
    argocd-install.yaml         ArgoCD manifest saved locally for offline installs
    argocd-application.yaml    ArgoCD Application with auto sync, prune, self heal
  scripts/                      setup, ci-pipeline, ci-watch, release, drift-demo, rollback, status, teardown
  workspace/                    created by setup: developer clones of both repos, CI scratch, credentials
```

## Settings changed from ArgoCD defaults

- `timeout.reconciliation: 10s` in `argocd-cm`. ArgoCD polls Git every 10 seconds instead of every 3 minutes.
- `server.insecure: "true"` in `argocd-cmd-params-cm`. The UI serves plain HTTP, so the browser shows no certificate warning.
- `argocd-server` service type `NodePort` 30808, which kind maps to localhost:8080. This replaces `kubectl port-forward svc/argocd-server -n argocd 8080:443`, and the UI stays up without a terminal open.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `Docker is not running` | Start Docker Desktop, then run the command again. |
| Setup stops with connection refused errors | Docker Desktop crashed, usually from low disk space. Free space on C:, restart Docker Desktop, run `.\gitops setup` again. |
| ArgoCD tree cuts off the pods on the right | Collapse the sidebar with the arrow at the top left, then click zoom out twice in the tree toolbar. |
| ArgoCD login fails | Use `admin` / `admin123`. If it still fails, run `.\gitops setup` again, which resets the password. |
| App still shows the old version | Check `.\gitops status`. If the ArgoCD state is `OutOfSync`, click Refresh in the ArgoCD UI. |
| `release` says the watcher is not running | It runs the pipeline in the same terminal instead, so the release still ships. |
| Port 8080, 8081, 3300 or 5001 busy | Stop the program using it, or change the port in `scripts/lib.sh` and `infra/kind-cluster.yaml`, then run teardown and setup. |
| Start from zero | `.\gitops teardown` then `.\gitops setup`. |
