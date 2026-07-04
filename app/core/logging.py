import logging
import time
import uuid

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("ai_content")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Attaches a unique request_id to every request and logs:
    - method, path, request_id on arrival
    - status code + duration on completion
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = str(uuid.uuid4())[:8]
        request.state.request_id = request_id

        start = time.perf_counter()
        logger.info(
            "request_start",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
            },
        )
        logger.info(f"[{request_id}] → {request.method} {request.url.path}")

        response = await call_next(request)

        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        logger.info(
            f"[{request_id}] ← {response.status_code} "
            f"({request.method} {request.url.path}) {duration_ms}ms"
        )

        response.headers["X-Request-ID"] = request_id
        return response
