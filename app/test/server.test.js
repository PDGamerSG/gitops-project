const test = require("node:test");
const assert = require("node:assert");
const { createServer } = require("../server");

async function withServer(fn) {
  const server = createServer();
  await new Promise((resolve) => server.listen(0, resolve));
  const base = `http://127.0.0.1:${server.address().port}`;
  try {
    await fn(base);
  } finally {
    server.close();
  }
}

test("health check responds ok", () =>
  withServer(async (base) => {
    const res = await fetch(`${base}/healthz`);
    assert.strictEqual(res.status, 200);
    assert.deepStrictEqual(await res.json(), { status: "ok" });
    assert.strictEqual(res.headers.get("x-content-type-options"), "nosniff");
  }));

test("info endpoint reports version and commit", () =>
  withServer(async (base) => {
    const info = await (await fetch(`${base}/api/info`)).json();
    assert.match(info.version, /^\d+\.\d+\.\d+$/);
    assert.match(info.theme, /^#[0-9a-fA-F]{6}$/);
    assert.ok(info.commit);
  }));

test("todos can be created, toggled and deleted", () =>
  withServer(async (base) => {
    const created = await fetch(`${base}/api/todos`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title: "Write the report" }),
    });
    assert.strictEqual(created.status, 201);
    const todo = await created.json();

    const toggled = await (await fetch(`${base}/api/todos/${todo.id}`, { method: "PATCH" })).json();
    assert.strictEqual(toggled.done, true);

    const removed = await fetch(`${base}/api/todos/${todo.id}`, { method: "DELETE" });
    assert.strictEqual(removed.status, 204);
    assert.deepStrictEqual(await (await fetch(`${base}/api/todos`)).json(), []);
  }));

test("empty titles are rejected", () =>
  withServer(async (base) => {
    const res = await fetch(`${base}/api/todos`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title: "  " }),
    });
    assert.strictEqual(res.status, 400);
  }));
