# OpenCodeZenProxy

A lightweight, memory-efficient FastAPI proxy that forwards all requests from `/v1/*` to `https://opencode.ai/zen/v1/*` verbatim — headers, query params, body, and method — and streams the response back.

## Features

- **Zero-copy streaming** — request body read via `request.stream()`, response forwarded via `resp.aiter_raw()`; no full buffering at any point
- **Transparent** — preserves `content-encoding`, passes through every header except hop-by-hop ones (`host`, `transfer-encoding`, `connection`, etc.)
- **Connection pooling** — shared `httpx.AsyncClient` with configurable pool limits
- **Railway-ready** — `railway.json` with health check, `$PORT` binding, and nixpacks build

## Usage

```bash
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 1253
```

Then point your client at `http://localhost:1253/v1/...` instead of `https://opencode.ai/zen/v1/...`.

## Deploy to Railway

Click the button or use the CLI:

```bash
railway up
```

The `railway.json` handles build and start command automatically.

## Endpoints

| Path | Description |
|------|-------------|
| `/v1/{path}` | Proxies to `https://opencode.ai/zen/v1/{path}` |
| `/health` | Health check (used by Railway) |

## License

MIT
