import express from "express"
import { randomUUID } from "node:crypto"
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js"
import { SSEServerTransport } from "@modelcontextprotocol/sdk/server/sse.js"
import { z } from "zod"

const app = express()
const server = new McpServer({ name: "crawl4ai-mock", version: "1.0.0" })
const sessions = new Map()

server.tool(
  "crawl4ai_md",
  "Mock de extracao markdown do crawl4ai",
  { url: z.string().url() },
  async ({ url }) => ({
    content: [{ type: "text", text: `MOCK_CRAWL4AI_MD_OK ${url}` }],
  }),
)

server.tool(
  "crawl4ai_html",
  "Mock de extracao HTML do crawl4ai",
  { url: z.string().url() },
  async ({ url }) => ({
    content: [{ type: "text", text: `<html><body>MOCK_CRAWL4AI_HTML_OK ${url}</body></html>` }],
  }),
)

server.tool(
  "crawl4ai_execute_js",
  "Mock de execucao JS do crawl4ai",
  { url: z.string().url(), scripts: z.array(z.string()) },
  async ({ url, scripts }) => ({
    content: [{ type: "text", text: JSON.stringify({ ok: true, marker: "MOCK_CRAWL4AI_EXECUTE_JS_OK", url, scripts }) }],
  }),
)

app.get("/health", (_req, res) => {
  res.status(200).json({ ok: true })
})

app.get("/mcp/sse", async (req, res) => {
  const transport = new SSEServerTransport("/mcp/messages", res)
  const sessionId = transport.sessionId ?? randomUUID()
  sessions.set(sessionId, transport)

  res.on("close", () => {
    sessions.delete(sessionId)
  })

  await server.connect(transport)
})

app.post("/mcp/messages", express.json(), async (req, res) => {
  const sessionId = String(req.query.sessionId || "")
  const transport = sessions.get(sessionId)
  if (!transport) {
    res.status(404).json({ error: "session not found" })
    return
  }
  await transport.handlePostMessage(req, res, req.body)
})

const port = Number(process.env.MCP_MOCK_PORT || 11235)
app.listen(port, "0.0.0.0", () => {
  console.log(`mcp mock listening on http://0.0.0.0:${port}`)
})
