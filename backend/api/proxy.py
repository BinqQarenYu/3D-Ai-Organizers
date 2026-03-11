from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
import httpx
import logging
from backend.api.url_validator import validate_url

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/api/proxy")
async def proxy_external_asset(url: str = Query(..., description="The external URL to proxy")):
    if not url.startswith("http://") and not url.startswith("https://"):
        raise HTTPException(status_code=400, detail="Invalid URL protocol.")

    validate_url(url)

    try:
        async def stream_generator():
            async with httpx.AsyncClient() as client:
                async with client.stream("GET", url) as r:
                    if r.status_code != 200:
                        yield b"" # Or raise, but we are already in the generator
                        return
                    async for chunk in r.aiter_bytes():
                        yield chunk

        # Make an initial HEAD request to get headers and check status
        async with httpx.AsyncClient() as client:
            head_r = await client.head(url)
            if head_r.status_code != 200:
                raise HTTPException(status_code=head_r.status_code, detail="Failed to fetch external URL.")

            headers = {}
            if "Content-Disposition" in head_r.headers:
                headers["Content-Disposition"] = head_r.headers["Content-Disposition"]

            return StreamingResponse(
                stream_generator(),
                media_type=head_r.headers.get("Content-Type", "application/octet-stream"),
                headers=headers
            )
    except Exception as e:
        logger.error(f"Error proxying {url}: {e}")
        raise HTTPException(status_code=500, detail="Error proxying external URL.")
