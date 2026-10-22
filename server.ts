import express from "express";
import next from "next";
import { parse } from "url";

const dev = process.env.NODE_ENV !== "production";
const app = next({ dev });
const handle = app.getRequestHandler();

app.prepare().then(() => {
  const server = express();

  // Use /.*/ to replace "*" in path strings for Express 5
  server.all(/.*/, (req, res) => {
    const parsedUrl = parse(req.url!, true);
    handle(req, res, parsedUrl);
  });

  const port = process.env.PORT ? parseInt(process.env.PORT, 10) : 3000;
  const host = "0.0.0.0";
  server.listen(port, host, () => {
    console.log(`> Ready on http://${host}:${port}`);
  });
}).catch((err) => {
  console.error("Error starting server:", err);
  process.exit(1);
});
