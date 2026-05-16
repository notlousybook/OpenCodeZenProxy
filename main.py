import os
from typing import AsyncGenerator
import httpx
from fastapi import FastAPI, Request, Response
from fastapi.responses import StreamingResponse

app = FastAPI()

UPSTREAM_BASE = "https://opencode.ai/zen/v1"

HOP_BY_HOP = frozenset({
    "host", "content-length", "transfer-encoding", "connection",
    "keep-alive", "proxy-authenticate", "proxy-authorization",
    "te", "trailers", "upgrade",
})

client: httpx.AsyncClient | None = None


@app.on_event("startup")
async def startup():
    global client
    client = httpx.AsyncClient(
        timeout=httpx.Timeout(60.0, connect=10.0),
        limits=httpx.Limits(
            max_keepalive_connections=20,
            max_connections=100,
        ),
    )


@app.on_event("shutdown")
async def shutdown():
    if client is not None:
        await client.aclose()


@app.api_route("/v1/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS", "CONNECT", "TRACE"])
async def proxy(request: Request, path: str):
    upstream_url = f"{UPSTREAM_BASE}/{path}"

    params = dict(request.query_params)

    headers = {}
    for key, value in request.headers.items():
        if key.lower() not in HOP_BY_HOP:
            headers[key] = value

    body = request.stream()

    try:
        req = client.build_request(
            request.method,
            upstream_url,
            params=params,
            headers=headers,
            content=body,
        )
        resp = await client.send(req, stream=True)

        response_headers = {}
        for key, value in resp.headers.items():
            if key.lower() not in HOP_BY_HOP:
                response_headers[key] = value

        async def iterate() -> AsyncGenerator[bytes, None]:
            try:
                async for chunk in resp.aiter_raw():
                    yield chunk
            finally:
                await resp.aclose()

        return StreamingResponse(
            iterate(),
            status_code=resp.status_code,
            headers=response_headers,
        )
    except httpx.TimeoutException:
        return Response("Upstream timeout", status_code=504)
    except httpx.RequestError as e:
        return Response(f"Upstream error: {e}", status_code=502)


@app.get("/health")
async def health():
    return {"status": "ok"}
