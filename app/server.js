// Todo app used as the workload for the GitOps pipeline.
// No npm dependencies, so the image builds offline from node:22-alpine alone.
const http = require("node:http");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");

const release = require("./version.json");

function createServer() {
  const todos = [];
  let nextId = 1;
  const indexHtml = fs.readFileSync(path.join(__dirname, "public", "index.html"));

  function sendJson(res, status, body) {
    res.writeHead(status, {
      "Content-Type": "application/json; charset=utf-8",
      "Cache-Control": "no-store",
    });
    res.end(JSON.stringify(body));
  }

  function readBody(req) {
    return new Promise((resolve, reject) => {
      let data = "";
      req.on("data", (chunk) => {
        data += chunk;
        if (data.length > 1e5) reject(new Error("body too large"));
      });
      req.on("end", () => {
        try {
          resolve(data ? JSON.parse(data) : {});
        } catch (err) {
          reject(err);
        }
      });
    });
  }

  return http.createServer(async (req, res) => {
    const url = new URL(req.url, "http://localhost");

    res.setHeader("X-Content-Type-Options", "nosniff");
    res.setHeader("X-Frame-Options", "DENY");
    res.setHeader("Referrer-Policy", "no-referrer");

    try {
      if (req.method === "GET" && url.pathname === "/") {
        res.writeHead(200, {
          "Content-Type": "text/html; charset=utf-8",
          "Cache-Control": "no-store",
        });
        return res.end(indexHtml);
      }

      if (req.method === "GET" && url.pathname === "/healthz") {
        return sendJson(res, 200, { status: "ok" });
      }

      if (req.method === "GET" && url.pathname === "/api/info") {
        return sendJson(res, 200, {
          version: release.version,
          theme: release.theme,
          message: release.message,
          commit: process.env.GIT_SHA || "dev",
          pod: process.env.POD_NAME || os.hostname(),
          node: process.env.NODE_NAME || "local",
          startedAt: startedAt,
        });
      }

      if (url.pathname === "/api/todos" && req.method === "GET") {
        return sendJson(res, 200, todos);
      }

      if (url.pathname === "/api/todos" && req.method === "POST") {
        const body = await readBody(req);
        const title = typeof body.title === "string" ? body.title.trim() : "";
        if (!title) return sendJson(res, 400, { error: "title is required" });
        const todo = { id: nextId++, title, done: false };
        todos.push(todo);
        return sendJson(res, 201, todo);
      }

      const match = url.pathname.match(/^\/api\/todos\/(\d+)$/);
      if (match) {
        const index = todos.findIndex((t) => t.id === Number(match[1]));
        if (index === -1) return sendJson(res, 404, { error: "not found" });

        if (req.method === "PATCH") {
          todos[index].done = !todos[index].done;
          return sendJson(res, 200, todos[index]);
        }
        if (req.method === "DELETE") {
          todos.splice(index, 1);
          res.writeHead(204);
          return res.end();
        }
      }

      sendJson(res, 404, { error: "not found" });
    } catch (err) {
      sendJson(res, 400, { error: err.message });
    }
  });
}

const startedAt = new Date().toISOString();

if (require.main === module) {
  const port = Number(process.env.PORT) || 3000;
  const server = createServer();
  server.listen(port, () => console.log(`todo-app ${release.version} listening on ${port}`));
  process.on("SIGTERM", () => server.close(() => process.exit(0)));
}

module.exports = { createServer };
