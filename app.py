from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
import httpx

app = FastAPI()

@app.api_route("/{full_path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy(full_path: str, request: Request):
    # Determine target service based on path
    if full_path.startswith("prefect"):
        target_url = f"http://localhost:4200/{full_path[8:]}"
    else:
        target_url = f"http://localhost:8000/{full_path}"

    # Make proxied request
    async with httpx.AsyncClient() as client:
        response = await client.request(
            method=request.method,
            url=target_url,
            headers=request.headers.raw,
            content=await request.body()
        )
        return StreamingResponse(response.aiter_raw(), status_code=response.status_code, headers=dict(response.headers))