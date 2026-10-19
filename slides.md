Make a PowerPoint presentation (.pptx) with exactly these 15 slides, in this order. Put the "On the slide" text on the slide. Draw the "Visual" as shapes, arrows or tables. Put "Speaker notes" in the notes section, not on the slide. Style: 16:9, white background, navy (#0F2A44) titles, teal (#14B8A6) highlights, orange (#EF7B4D) for ArgoCD. Sentence case titles, no emoji, no stock photos, monospace font for code.

---

## Slide 1

**Title:** GitOps-based continuous deployment with ArgoCD

**On the slide:**
- Subtitle: Pull-based deployment on Kubernetes with Git as the single source of truth
- Software Configuration Management project review
- Team: Name 1, Name 2, Name 3, Name 4
- Guide: Guide name
- Date

**Visual:** Git logo, an arrow, and the Kubernetes logo, placed small at the bottom.

**Speaker notes:** Introduce the team. Our project makes a deployment just a Git commit. The cluster keeps itself matched to Git.

---

## Slide 2

**Title:** How deployment usually works

**On the slide:**
- CI server builds the app and deploys it into the cluster
- CI server stores cluster admin credentials
- Deployment is pushed from outside the cluster

**Visual:** Flow diagram: Developer → Git repo → CI server (GitHub Actions / Jenkins) → red arrow labelled "kubectl apply with admin access" → Kubernetes cluster.

**Speaker notes:** This is the push model. The CI tool reaches into production from outside. It works, but it creates three problems.

---

## Slide 3

**Title:** Problem statement

**On the slide:** Three cards side by side.
- **Security risk:** external CI holds production cluster credentials
- **Configuration drift:** manual `kubectl edit` changes make the cluster differ from the repo
- **Hard rollbacks:** reverting means re-running complex pipelines

**Visual:** A lock icon, a warning icon and an undo icon, one on each card.

**Speaker notes:** Drift example: an admin scales pods by hand late at night, nobody records it, and the next deploy behaves differently.

---

## Slide 4

**Title:** Our solution: GitOps

**On the slide:**
- Big line at the top: Git is the single source of truth
- Declarative: desired state written in YAML
- Versioned: every change is a Git commit
- Pulled: a controller inside the cluster pulls changes
- Reconciled: drift is detected and reverted automatically

**Visual:** Four icons in a row, one per principle.

**Speaker notes:** Declarative means we describe what we want, not the steps. React works the same way for UI. ArgoCD is the controller we used.

---

## Slide 5

**Title:** Push model vs pull model

**On the slide:** Comparison table.

| | Push model | Pull model (GitOps) |
|---|---|---|
| Who deploys | External CI server | ArgoCD inside the cluster |
| Cluster credentials | Stored in CI | Never leave the cluster |
| Manual changes | Go unnoticed | Reverted automatically |
| Rollback | Re-run pipeline | `git revert` |
| Audit trail | CI logs | Git history |

**Visual:** Highlight the pull model column in teal.

**Speaker notes:** The key point is that CI never talks to the cluster. It only writes to Git.

---

## Slide 6

**Title:** Project objectives

**On the slide:**
1. Single source of truth: all configuration lives in Git
2. Automated reconciliation: no manual deployments
3. Zero drift: manual cluster changes get reverted
4. Better security: no cluster credentials outside the cluster

**Visual:** Four numbered circles with the objective next to each.

**Speaker notes:** These objectives come from our review 1 document. The live demo proves each one.

---

## Slide 7

**Title:** System architecture

**On the slide:** Diagram only, with four labelled zones from left to right.

**Visual:**
- Zone 1, Development: Developer → Source repo (`todo-app`)
- Zone 2, CI build and test: CI pipeline box listing: run tests, build image, push image, update tag
- Zone 3, Artifacts and config: Container registry (images tagged with commit SHA) and Config repo (`argo-deployment`, Kubernetes YAML)
- Zone 4, Kubernetes cluster: ArgoCD → Deployment → ReplicaSet → 3 Pods, plus Service
- Arrows: CI → registry "push image"; CI → config repo "commit new tag"; ArgoCD → config repo "watch every 10 s"; ArgoCD → cluster resources "apply"; Pods → registry "pull image"
- Dashed red line between CI and the cluster, labelled "no access"

**Speaker notes:** Walk the arrows left to right. The dashed line is the whole point: CI and the cluster never talk directly. Git is the only link between them.

---

## Slide 8

**Title:** How a change reaches production

**On the slide:** Five steps on a horizontal timeline.
1. **Commit:** developer pushes code
2. **Build:** tests run, Docker image tagged with commit SHA
3. **Update:** CI changes the image tag in the config repo
4. **Detect:** ArgoCD sees Git and cluster differ
5. **Sync:** ArgoCD rolls out new pods with zero downtime

**Visual:** Bracket over steps 1 to 3 labelled "CI (push)" and over steps 4 to 5 labelled "CD (pull)".

**Speaker notes:** CI finishes at step 3 with a git push. Everything after that happens inside the cluster.

---

## Slide 9

**Title:** Tech stack

**On the slide:** Table.

| Role | Usually | In our project |
|---|---|---|
| Git hosting | GitHub | Gitea (self-hosted) |
| CI | GitHub Actions | Pipeline script + `prod.yml` |
| Image registry | Docker Hub | Local Docker registry |
| Kubernetes | DigitalOcean | kind (3 nodes) |
| GitOps controller | ArgoCD | ArgoCD v3.5.3 |
| Application | Any service | Node.js todo app, 3 replicas |

Bottom line: Runs fully offline, set up with one command: `gitops setup`

**Visual:** Small tool logos next to each row if available.

**Speaker notes:** We ran every cloud part locally so the demo needs no internet or cloud account. The GitHub Actions workflow is also in the repo.

---

## Slide 10

**Title:** Key configuration

**On the slide:** Two code boxes side by side.

Left box, titled "ArgoCD application":
```yaml
source:
  repoURL: http://gitea:3000/gitops/argo-deployment.git
  targetRevision: main
destination:
  server: https://kubernetes.default.svc
  namespace: default
syncPolicy:
  automated:
    prune: true
    selfHeal: true
```

Right box, titled "CI only updates Git":
```bash
docker build -t localhost:5001/todo-app:$SHA .
docker push localhost:5001/todo-app:$SHA
sed -i "s|image: .*|image: .../todo-app:$SHA|" manifest.yml
git commit -am "Update image tag to $SHA"
git push
```

**Visual:** Highlight `selfHeal: true` and `git push` in teal.

**Speaker notes:** selfHeal reverts manual changes. prune deletes resources removed from Git. The CI script ends with git push and never runs kubectl.

---

## Slide 11

**Title:** Live demo

**On the slide:**
1. Deploy a new version with only `git push`
2. See the CI bot commit to the config repo
3. Break the cluster by hand, and ArgoCD fixes it
4. Roll back with `git revert`
5. Push broken code, and CI blocks it

**Visual:** Large numbered list, with a small "LIVE" tag in the corner.

**Speaker notes:** Switch to the running system now and go through the five steps.

---

## Slide 12

**Title:** Results

**On the slide:** Four big number tiles.
- **< 60 s**: git push to fully live
- **2 to 6 s**: manual change reverted by ArgoCD
- **19 s**: rollback using `git revert`
- **0**: kubectl commands needed to deploy

Line under the tiles: Failing tests stop a release before an image is built.

**Visual:** Tiles in a 2 by 2 grid, numbers in teal.

**Speaker notes:** Measured on our laptop with ArgoCD checking Git every 10 seconds. Real setups use Git webhooks to sync instantly.

---

## Slide 13

**Title:** Objectives achieved

**On the slide:** Table.

| Objective | Proof from the demo |
|---|---|
| Single source of truth | Every deploy and rollback is a Git commit |
| Automated reconciliation | ArgoCD deployed with no manual step |
| Zero drift | Scaled pods and deleted service came back |
| Better security | CI had only Git access, no cluster access |

**Visual:** Green check mark in front of each objective.

**Speaker notes:** This closes the loop with the objectives on slide 6.

---

## Slide 14

**Title:** Learnings and future scope

**On the slide:** Two columns.

Learnings:
- Declarative config makes cluster state reviewable
- Separate app and config repos keep history clean
- Git history works as the deployment audit log

Future scope:
- Helm charts for multiple environments
- Git webhooks for instant sync
- Sealed Secrets for secret management
- Staging to production through pull requests

**Visual:** Lightbulb icon over learnings, arrow icon over future scope.

**Speaker notes:** Helm packages Kubernetes YAML into reusable charts. ArgoCD deploys Helm charts the same way it deploys plain YAML.

---

## Slide 15

**Title:** Thank you

**On the slide:**
- Questions?
- Small line at the bottom: Git is the single source of truth. The cluster follows.

**Visual:** Same Git → Kubernetes logos as slide 1.

**Speaker notes:** Be ready for: push vs pull, why two repos, ArgoCD vs Flux, what happens if Git is down, how secrets are handled.
