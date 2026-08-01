"""PRAXIS Ingestion Link Verifier — I5.

Performs async HTTP HEAD requests to verify URL liveness before serving.
"""

import httpx
import logging

logger = logging.getLogger("praxis.verify")


async def verify_url(url: str, timeout: float = 5.0) -> bool:
    """Verify if a URL is active by executing a HEAD request, falling back to GET.

    Returns True if response code is less than 400, False otherwise.
    """
    if not url or not (url.startswith("http://") or url.startswith("https://")):
        return False

    async with httpx.AsyncClient(follow_redirects=True, verify=False) as client:
        try:
            # 1. Attempt HEAD request (fast and low bandwidth)
            res = await client.head(url, timeout=timeout)
            if res.status_code < 400:
                return True
        except Exception as e:
            logger.debug(f"HEAD request failed for {url}: {e}")

        try:
            # 2. Fallback to GET request with short response read limit
            res = await client.get(url, timeout=timeout, headers={"Range": "bytes=0-100"})
            if res.status_code < 400:
                return True
        except Exception as e:
            logger.warning(f"Liveness check failed for {url}: {e}")

    return False
