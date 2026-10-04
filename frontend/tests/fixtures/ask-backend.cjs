// Neutral contract fixture. Never invokes religious reasoning or real sources.
const http = require("node:http");
http
  .createServer(async (req, res) => {
    if (req.method === "GET") {
      res.end("ok");
      return;
    }
    let body = "";
    for await (const part of req) body += part;
    const payload = JSON.parse(body);
    res.setHeader("Content-Type", "application/json");
    if (payload.question === "fixture-error") {
      res.writeHead(422);
      res.end(JSON.stringify({ detail: "Fixture validation error" }));
      return;
    }
    res.end(
      JSON.stringify({
        mode: payload.mode,
        language: "en",
        decision_state: "ready",
        answer: payload.question,
        source_excerpts: [],
        sources: [],
      }),
    );
  })
  .listen(3101, "127.0.0.1");
