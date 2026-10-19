(function () {
  const storageKey = "gitops-todo-showcase-live-v2";
  const legacyKey = "gitops-todo-showcase";
  const channel = "BroadcastChannel" in window ? new BroadcastChannel("gitops-todo-live") : null;
  const $ = (selector) => document.querySelector(selector);
  const $$ = (selector) => Array.from(document.querySelectorAll(selector));
  let reconcileTimer;
  let lastSignature = "";
  let state;

  function readTasks() {
    try {
      const parsed = JSON.parse(localStorage.getItem(legacyKey) || "[]");
      return Array.isArray(parsed) ? parsed : [];
    } catch (_) {
      return [];
    }
  }

  function fingerprint(tasks) {
    let hash = 2166136261;
    const value = JSON.stringify(tasks);
    for (let index = 0; index < value.length; index += 1) {
      hash ^= value.charCodeAt(index);
      hash = Math.imul(hash, 16777619);
    }
    return (hash >>> 0).toString(16).padStart(8, "0").slice(0, 7);
  }

  function relativeTime(timestamp) {
    const seconds = Math.max(0, Math.round((Date.now() - timestamp) / 1000));
    if (seconds < 5) return "just now";
    if (seconds < 60) return `${seconds}s ago`;
    return `${Math.round(seconds / 60)}m ago`;
  }

  function createInitialState() {
    const tasks = readTasks();
    return {
      tasks,
      revision: 1,
      commit: "151a8f4",
      events: [{ message: "Initial desired state published", author: "CI Bot", commit: "151a8f4", at: Date.now() - 86400000 }],
      delivery: { phase: "healthy", label: "Synced / Healthy", at: Date.now() },
    };
  }

  function loadState() {
    try {
      const saved = JSON.parse(localStorage.getItem(storageKey) || "null");
      if (saved && Array.isArray(saved.tasks)) return saved;
    } catch (_) {
      // Use a clean initial projection when local storage contains invalid data.
    }
    return createInitialState();
  }

  function saveState(next, broadcast) {
    state = { ...state, ...next };
    localStorage.setItem(storageKey, JSON.stringify(state));
    if (broadcast && channel) channel.postMessage(state);
    render();
  }

  function imageTag() {
    return `localhost:5001/todo-app:${state.commit}`;
  }

  function manifestText() {
    const active = state.tasks.filter((task) => !task.done).length;
    const completed = state.tasks.length - active;
    return `apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: todo-app\n  namespace: default\nspec:\n  replicas: 3\n  revision: ${state.commit}\n  template:\n    spec:\n      containers:\n        - name: todo-app\n          image: ${imageTag()}\n          env:\n            - name: TODO_ACTIVE\n              value: "${active}"\n            - name: TODO_COMPLETED\n              value: "${completed}"\n---\napiVersion: v1\nkind: Service\nmetadata:\n  name: todo-app\nspec:\n  type: NodePort\n  ports:\n    - port: 3000\n      nodePort: 30081`;
  }

  function startReconcile(next) {
    window.clearTimeout(reconcileTimer);
    const runId = Date.now();
    state.reconcileRun = runId;
    const phases = [
      ["commit", "Gitea desired state updated", 0],
      ["syncing", "ArgoCD detected a new desired revision", 650],
      ["syncing", "ArgoCD is applying the manifest", 1350],
      ["healthy", "Synced / Healthy · rollout complete", 2350],
    ];
    const advance = (phase, label) => {
      if (!state || state.reconcileRun !== runId) return;
      saveState({ delivery: { phase, label, at: Date.now() } }, true);
    };
    saveState({ ...next, reconcileRun: runId, delivery: { phase: "commit", label: phases[0][1], at: Date.now() } }, true);
    phases.slice(1).forEach(([phase, label, delay]) => {
      window.setTimeout(() => advance(phase, label), delay);
    });
  }

  function reconcileTasks(tasks, signature) {
    const commit = fingerprint(tasks);
    const event = { message: "Todo state committed to desired state", author: "CI Bot", commit, at: Date.now() };
    startReconcile({ tasks, revision: state.revision + 1, commit, events: [event, ...(state.events || [])].slice(0, 6) });
    lastSignature = signature;
  }

  function renderWorkload() {
    const list = $("#live-task-list");
    if (!list) return;
    list.replaceChildren();
    $("#live-task-empty").hidden = state.tasks.length > 0;
    state.tasks.forEach((task) => {
      const item = document.createElement("li");
      item.className = `live-task${task.done ? " done" : ""}`;
      const checkbox = document.createElement("input");
      checkbox.type = "checkbox";
      checkbox.checked = Boolean(task.done);
      checkbox.disabled = true;
      checkbox.setAttribute("aria-label", `Complete ${task.title}`);
      const label = document.createElement("span");
      label.textContent = task.title;
      item.append(checkbox, label);
      list.append(item);
    });
    $("#live-image").textContent = imageTag();
    $("#live-revision").textContent = state.commit;
  }

  function renderGitea() {
    const list = $("#live-commits");
    if (!list) return;
    list.replaceChildren();
    (state.events || []).slice(0, 6).forEach((event, index) => {
      const row = document.createElement("li");
      row.className = "live-commit-row";
      const badge = document.createElement("span");
      badge.className = "live-commit-badge";
      badge.textContent = index === 0 ? "CI" : "G";
      const copy = document.createElement("div");
      const message = document.createElement("strong");
      message.textContent = event.message;
      const meta = document.createElement("small");
      meta.textContent = `${event.author} · ${relativeTime(event.at)}`;
      copy.append(message, meta);
      const sha = document.createElement("span");
      sha.className = "live-sha";
      sha.textContent = event.commit;
      row.append(badge, copy, sha);
      list.append(row);
    });
    $("#live-commit-count").textContent = String((state.events || []).length);
    $("#live-commit-total").textContent = `${(state.events || []).length} commit${state.events?.length === 1 ? "" : "s"}`;
    $("#live-manifest-content").textContent = manifestText();
  }

  function renderArgo() {
    const pods = $("#live-argo-pods");
    if (!pods) return;
    pods.replaceChildren();
    for (let index = 0; index < 3; index += 1) {
      const pod = document.createElement("span");
      pod.className = "live-pod";
      pod.textContent = `pod/todo-app-${state.commit.slice(0, 5)}-${index + 1}`;
      pods.append(pod);
    }
    const active = state.tasks.filter((task) => !task.done).length;
    const completed = state.tasks.length - active;
    $("#live-argo-root-detail").textContent = `${state.tasks.length} task${state.tasks.length === 1 ? "" : "s"} projected · desired state matches live state`;
    $("#live-argo-config-detail").textContent = `image ${state.commit} · ${active} active · ${completed} complete`;
    $("#live-argocd-revision").textContent = `revision ${state.commit} · 3 resources`;
  }

  function renderEvents() {
    const list = $("#live-argo-events");
    if (!list) return;
    list.replaceChildren();
    (state.events || []).slice(0, 3).forEach((event, index) => {
      const row = document.createElement("div");
      row.className = `live-event${index === 0 ? " current" : ""}`;
      const type = document.createElement("b");
      type.textContent = index === 0 ? "SYNC" : "GIT";
      const text = document.createElement("span");
      text.textContent = `${event.message} · ${relativeTime(event.at)}`;
      row.append(type, text);
      list.append(row);
    });
  }

  function renderDelivery() {
    const delivery = state.delivery || { phase: "healthy", label: "Synced / Healthy", at: Date.now() };
    const healthy = delivery.phase === "healthy";
    const stateNode = $("#live-sync-state");
    stateNode.textContent = delivery.label;
    stateNode.dataset.phase = delivery.phase;
    $("#live-last-update").textContent = `revision ${state.commit} · ${relativeTime(delivery.at)}`;
    $("#live-workload-sync").textContent = healthy ? "Synced / Healthy" : delivery.label;
    $("#live-workload-chip").textContent = healthy ? "healthy" : delivery.phase;
    $("#live-workload-chip").className = `live-chip${healthy ? "" : " warn"}`;
    $("#live-gitea-chip").textContent = healthy ? "working tree clean" : "commit pending";
    $("#live-gitea-chip").className = `live-chip${healthy ? "" : " warn"}`;
    $("#live-argocd-sidebar-status").textContent = healthy ? "Synced · Healthy" : `OutOfSync · ${delivery.phase}`;
    ["#live-argocd-sync-chip", "#live-argocd-health-chip", "#live-argocd-sync-status", "#live-argocd-health-status"].forEach((selector) => {
      const node = $(selector);
      node.classList.toggle("syncing", !healthy);
    });
    $("#live-argocd-sync-chip").textContent = healthy ? "Synced" : "OutOfSync";
    $("#live-argocd-health-chip").textContent = healthy ? "Healthy" : "Progressing";
    $("#live-argocd-sync-status").textContent = healthy ? "Synced" : "OutOfSync";
    $("#live-argocd-health-status").textContent = healthy ? "Healthy" : "Progressing";
    $("#live-argo-root-badge").textContent = healthy ? "Healthy" : "Progressing";
    $("#live-argo-root-badge").style.color = healthy ? "var(--mint)" : "var(--yellow)";
    $("#live-argo-config-badge").textContent = healthy ? "Synced" : "Updating";
    $("#live-argo-config-badge").style.color = healthy ? "var(--mint)" : "var(--yellow)";
    $("#live-argocd-last-sync").textContent = healthy ? relativeTime(delivery.at) : "reconciling";
    $("#runtime-image").textContent = imageTag();
    $("#runtime-release").textContent = `revision ${state.commit} · live projection`;
    $("#runtime-sync").textContent = healthy ? "Synced / Healthy" : delivery.label;
    $("#hero-version").textContent = `v${state.commit}`;
    $("#hero-sync").textContent = healthy ? "ArgoCD reports Synced / Healthy" : `ArgoCD reports ${delivery.label}`;
  }

  function render() {
    renderWorkload();
    renderGitea();
    renderArgo();
    renderEvents();
    renderDelivery();
  }

  function receive(incoming) {
    if (!incoming || !Array.isArray(incoming.tasks)) return;
    state = { ...state, ...incoming };
    lastSignature = JSON.stringify(state.tasks);
    localStorage.setItem(storageKey, JSON.stringify(state));
    render();
  }

  state = loadState();
  lastSignature = JSON.stringify(state.tasks);
  $$("[data-live-screen]").forEach((tab) => tab.addEventListener("click", () => {
    const target = tab.dataset.liveScreen;
    $$("[data-live-screen]").forEach((item) => {
      const active = item === tab;
      item.classList.toggle("active", active);
      item.setAttribute("aria-selected", active ? "true" : "false");
    });
    $$(".live-screen").forEach((screen) => {
      const active = screen.id === target;
      screen.classList.toggle("active", active);
      screen.setAttribute("aria-hidden", active ? "false" : "true");
    });
  }));
  window.addEventListener("storage", (event) => {
    if (event.key === storageKey && event.newValue) {
      try { receive(JSON.parse(event.newValue)); } catch (_) { /* keep the last valid state */ }
    }
    if (event.key === legacyKey) poll();
  });
  if (channel) channel.addEventListener("message", (event) => receive(event.data));

  function poll() {
    const tasks = readTasks();
    const signature = JSON.stringify(tasks);
    if (signature === lastSignature) return;
    reconcileTasks(tasks, signature);
  }

  window.setInterval(poll, 250);
  render();
}());
