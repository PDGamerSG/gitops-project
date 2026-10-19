# Presentation plan: GitOps continuous deployment with ArgoCD

This file has two parts.

- Part 1 is for you. It covers how to run the talk, the timing, the live demo and likely questions.
- Part 2 is for Claude. Copy everything from "Part 2" to the end into a new Claude chat and it will build the PowerPoint.

---

# Part 1: how to present

## The one idea to get across

A deployment is a Git commit. Nobody runs kubectl against the cluster. CI only writes to Git, and ArgoCD, running inside the cluster, pulls from Git and makes the cluster match it. If someone changes the cluster by hand, ArgoCD puts it back.

Every slide and every demo step should support that sentence.

## Talk structure (about 15 minutes)

| Part | Slides | Time | Goal |
|---|---|---|---|
| Problem | 1 to 3 | 2 min | Show why push-based CI/CD is risky |
| Solution | 4 to 6 | 3 min | Explain GitOps and the pull model |
| Architecture and build | 7 to 10 | 3 min | Show what you built and how the pieces connect |
| Live demo | 11 | 5 min | Prove it works |
| Results and wrap-up | 12 to 15 | 2 min | Numbers, learnings, questions |

If you have only 10 minutes, skip slides 9 and 13 and cut the demo to steps 2, 3 and 4.

## Before you walk in

1. Start Docker Desktop at least 5 minutes early. Wait until it says running.
2. In PowerShell, inside `gitops-project`, run `.\gitops status`. All four services must say `ok`. If one says DOWN, run `.\gitops setup`.
3. Run `.\gitops open`. Log in to ArgoCD with `admin` / `admin123`. Collapse the sidebar and zoom out twice so all 3 pods are visible.
4. Open terminal 1 and run `.\gitops ci-watch`. Leave it running.
5. Open terminal 2 in the same folder for the demo commands.
6. Increase the terminal font size so the back row can read it.
7. Arrange windows so you can switch fast: slides, browser (app, ArgoCD, Gitea tabs), terminal 1, terminal 2.

## Live demo script (5 minutes)

Say the line in quotes, then run the command.

**Step 1. Show the running system (30 s)**
"This is the app running on a 3 node Kubernetes cluster. The image tag is a Git commit SHA. ArgoCD says Synced and Healthy."
Show the todo app page, then the ArgoCD tree.

**Step 2. Deploy through Git only (90 s)**
"I'm the developer. I change the code and push. I won't touch the cluster."
Run `.\gitops release` in terminal 2.
Point at terminal 1: tests run, the image builds, CI pushes a commit to the config repo.
Switch to Gitea: "Here is the commit from the CI bot. It changed one line, the image tag."
Switch to ArgoCD: new ReplicaSet appears, pods roll over.
Switch to the app: the header colour and version change.
"From git push to live took under a minute, and nobody ran kubectl."

**Step 3. Drift and self-heal (45 s)**
"Now I'm an admin making a manual change in production, which is exactly what causes drift."
Run `.\gitops drift-demo`.
"I scaled to 8 pods and deleted the service. ArgoCD saw that the cluster no longer matches Git and reverted it in a few seconds."

**Step 4. Rollback is a Git revert (45 s)**
"The release is bad. How do we roll back?"
Run `.\gitops rollback`.
"That was a git revert on the config repo. No pipeline re-run. ArgoCD follows Git back to the previous image."
Show the app returning to the old version.

**Step 5. Bad code never ships (60 s)**
"What if a developer pushes code with a bug?"
Run `.\gitops release broken`.
Point at terminal 1: `not ok` and `pipeline FAILED`.
"Tests run inside the Docker build. The image never gets built, Git never changes, so the cluster is untouched."
Run `.\gitops fix-broken` to clean up.

**If the demo breaks:** stay calm and say "let me show you the recorded result". Move to slide 12, which has the measured numbers. Run `.\gitops status` afterwards to recover.

## Likely questions and short answers

**Why two repositories?**
The app repo changes on every code commit. The config repo holds only the desired cluster state. Keeping them apart gives a clean deployment history, lets different people own each one, and stops CI build commits from triggering each other in a loop.

**What is the difference between push and pull deployment?**
In push, the CI server holds cluster admin credentials and runs kubectl or helm against the cluster. In pull, a controller inside the cluster reads Git and applies changes. The cluster credentials never leave the cluster.

**How does ArgoCD know something changed?**
It polls the config repo. The default is every 3 minutes. We set it to 10 seconds. It also watches live cluster objects, which is why drift gets fixed within seconds. Webhooks from Git can trigger an instant sync in production setups.

**What does self-heal do, and what does prune do?**
Self-heal re-applies Git state when the live cluster differs. Prune deletes cluster resources that were removed from Git.

**ArgoCD or Flux?**
Both are CNCF GitOps controllers that pull from Git. ArgoCD has a web UI with a live resource tree, which suits a demo. Flux is more CLI and CRD driven. The GitOps model is the same.

**What happens if Git is down?**
The cluster keeps running its current state. New deployments wait until Git is back. Nothing gets deleted.

**How are secrets handled?**
Not in plain Git. Common options are Sealed Secrets, SOPS, or External Secrets Operator reading from a vault. This project has no application secrets, so it is out of scope.

**Why run everything locally instead of GitHub and DigitalOcean?**
So the demo works offline and without cloud cost. Each local part maps one to one: Gitea for GitHub, a local registry for Docker Hub, a kind cluster for DigitalOcean, and a script for GitHub Actions. The repo also includes the real GitHub Actions workflow, `prod.yml`.

**Where does Helm fit?**
Helm packages Kubernetes YAML into reusable, configurable charts. ArgoCD can deploy Helm charts from the config repo the same way it deploys plain YAML.

**What is declarative deployment?**
You describe the end state you want, like "3 replicas of this image", instead of writing the steps to get there. Kubernetes and ArgoCD work out the steps. React does the same for UI.

---

# Part 2: prompt for Claude to build the slides

Copy from here to the end of the file into Claude.

---

Build a 15 slide PowerPoint presentation (.pptx) for a college Software Configuration Management (SCM) project review. The topic is "GitOps-based continuous deployment using ArgoCD". The audience is faculty evaluators who know basic DevOps but not GitOps.

## Design requirements

- 16:9 layout, clean technical style. Dark navy title bar or accent (#0F2A44) with a teal highlight (#14B8A6) and orange for ArgoCD accents (#EF7B4D). White or very light grey slide backgrounds for readability.
- Sentence case titles. At most 5 bullets per slide and at most 12 words per bullet.
- Draw diagrams with shapes and arrows, not paragraphs of text. Keep diagrams simple enough to read from the back of a room.
- Put the speaker notes below into the notes section of each slide, not onto the slide.
- Use monospace font for commands and file names.
- No stock photos, no emoji, no decorative clip art.
- Add a slide number on every slide except the title.

## Slides

### Slide 1: Title
- Title: GitOps-based continuous deployment with ArgoCD
- Subtitle: Pull-based CD on Kubernetes with Git as the single source of truth
- Footer: Software Configuration Management project review, team member names (leave placeholders: Name 1, Name 2, Name 3, Name 4), guide name placeholder, date placeholder
- Speaker notes: Introduce the team and the one-line idea. A deployment is a Git commit, and the cluster keeps itself in line with Git.

### Slide 2: How deployments usually work (push model)
- Diagram: Developer, then Git repo, then CI server (GitHub Actions or Jenkins), then an arrow labelled "kubectl apply with admin credentials" pointing into a Kubernetes cluster box.
- Bullets:
  - CI server builds the image and pushes it into the cluster
  - CI must store cluster admin credentials
  - Deployment happens from outside the cluster
- Speaker notes: This is the traditional push model. The CI tool reaches into production. It works, but the next slide shows the problems.

### Slide 3: Problem statement
- Three cards side by side, each with a short title and one line:
  - Security risk: external CI holds production cluster credentials, a high-value target
  - Configuration drift: manual `kubectl edit` changes make the live cluster differ from the repo
  - Hard rollbacks: reverting means re-running complex pipelines instead of returning to a known good state
- Speaker notes: Explain each problem with a concrete example. Drift example: an admin scales pods by hand at 2 am, nobody records it, and the next deploy behaves differently.

### Slide 4: The solution, GitOps
- Big statement at the top: "Git is the single source of truth for the cluster"
- Four principles as icons with short labels:
  - Declarative: describe the desired state in YAML
  - Versioned: every change is a Git commit
  - Pulled automatically: a controller inside the cluster pulls changes
  - Continuously reconciled: drift is detected and reverted
- Speaker notes: These are the four OpenGitOps principles. Relate declarative to React, where you describe what the UI should look like and the framework makes it happen.

### Slide 5: Push vs pull
- Two column comparison table:

| | Push model | Pull model (GitOps) |
|---|---|---|
| Who deploys | External CI server | ArgoCD inside the cluster |
| Cluster credentials | Stored in CI | Never leave the cluster |
| Drift | Goes unnoticed | Detected and reverted |
| Rollback | Re-run pipeline | `git revert` |
| Audit trail | CI logs | Git history |

- Speaker notes: The key line is that CI never talks to the cluster. It only writes to Git.

### Slide 6: Project objectives
- Four numbered objectives:
  1. Single source of truth: all app and cluster configuration in Git
  2. Automated reconciliation: no manual deployments
  3. Zero drift: manual cluster changes get reverted automatically
  4. Better security: no cluster credentials outside the cluster
- Speaker notes: These come from our review 1 document. The demo proves each one.

### Slide 7: Architecture
- Main diagram, left to right, grouped into four labelled zones:
  - Development: Developer, then Source Git repo (`todo-app`)
  - CI build and test: CI pipeline (run tests, build image, push image, update tag)
  - Artifacts and configuration: Container registry (versioned images tagged with commit SHA) and Config Git repo (`argo-deployment`, Kubernetes YAML)
  - Kubernetes cluster: ArgoCD controller, which watches the config repo and applies to Deployment, ReplicaSet, 3 Pods, Service
- Arrows: developer commits to source repo; source repo triggers CI; CI pushes image to registry; CI commits new image tag to config repo; ArgoCD pulls from config repo (label "watch every 10 s"); ArgoCD applies to cluster resources; pods pull image from registry.
- Draw a dashed line between CI and the cluster labelled "no access".
- Speaker notes: Walk the arrows left to right. Stress the dashed line. CI and the cluster never talk directly. Git is the only bridge.

### Slide 8: Step-by-step flow
- A horizontal 5-step timeline, split into CI (push) and CD (pull):
  1. Code commit: developer pushes to the source repo
  2. CI: tests run, Docker image built and tagged with the commit SHA
  3. Manifest update: CI changes the image tag in the config repo and commits
  4. Drift detection: ArgoCD notices Git and cluster differ
  5. Sync: ArgoCD applies the change and pods roll over with zero downtime
- Speaker notes: Steps 1 to 3 are push, done by CI. Steps 4 and 5 are pull, done by ArgoCD inside the cluster.

### Slide 9: Tech stack and local setup
- Table mapping the production tools to the offline setup we built:

| Role | Production equivalent | Our implementation |
|---|---|---|
| Source and config repos | GitHub | Gitea (self-hosted Git) |
| CI | GitHub Actions | Pipeline script plus `prod.yml` workflow |
| Image registry | Docker Hub | Local Docker registry |
| Kubernetes | DigitalOcean | kind, 1 control plane and 2 workers |
| GitOps controller | ArgoCD | ArgoCD v3.5.3 |
| Application | Any service | Node.js todo app, 3 replicas |

- Footer line: Runs fully offline on one laptop, set up with one command: `gitops setup`
- Speaker notes: We mirrored every cloud component locally so the demo does not depend on internet or cloud billing. The GitHub Actions version is included too.

### Slide 10: Key configuration
- Two code snippets side by side in monospace boxes.
- Left, titled "ArgoCD Application":
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
- Right, titled "CI updates only the image tag":
```bash
docker build -t localhost:5001/todo-app:$SHA .
docker push localhost:5001/todo-app:$SHA
sed -i "s|image: .*|image: .../todo-app:$SHA|" manifest.yml
git commit -am "Update image tag to $SHA"
git push
```
- Speaker notes: `selfHeal` reverts drift. `prune` deletes resources removed from Git. The CI side ends with `git push`. It never runs kubectl.

### Slide 11: Live demo
- Title: Live demo
- Five numbered demo steps, large text:
  1. Deploy a new version with only `git push`
  2. Watch the CI bot commit to the config repo
  3. Manually break the cluster, and ArgoCD self-heals it
  4. Roll back with `git revert`
  5. Push broken code, and CI blocks it
- Speaker notes: Switch to the live system here. Follow the demo script in part 1 of the plan.

### Slide 12: Results
- Four large number tiles:
  - Under 60 s: git push to fully rolled out
  - 2 to 6 s: manual drift reverted by ArgoCD
  - 19 s: rollback through `git revert`
  - 0: kubectl commands needed to deploy
- One line under the tiles: failed tests stop the release before an image is built
- Speaker notes: These were measured on our laptop setup with a 10 second Git polling interval. Production setups use Git webhooks for instant sync.

### Slide 13: Objectives achieved
- Checklist table linking each objective to its evidence:

| Objective | Evidence from the demo |
|---|---|
| Single source of truth | Every deploy and rollback is a Git commit |
| Automated reconciliation | ArgoCD synced with no manual step |
| Zero drift | Scaled pods and deleted service restored automatically |
| Better security | CI has no cluster credentials, only Git access |

- Speaker notes: Close the loop with slide 6.

### Slide 14: Learnings and future scope
- Two columns.
- Learnings:
  - Declarative config makes the cluster state reviewable
  - Separating app and config repos keeps history clean
  - Git history doubles as the deployment audit log
- Future scope:
  - Helm charts and Kustomize for multiple environments
  - Git webhooks for instant sync
  - Sealed Secrets for secret management
  - Staging to production promotion through pull requests
- Speaker notes: Mention that Helm packages YAML into reusable charts, and ArgoCD deploys them the same way.

### Slide 15: Thank you and questions
- Title: Thank you
- Subtitle: Questions?
- Small line: Git is the single source of truth. The cluster follows.
- Speaker notes: Be ready for the questions on push vs pull, why two repos, ArgoCD vs Flux, and secrets.
