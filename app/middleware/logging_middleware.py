import logging
import time

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.core.security import decode_access_token

logger = logging.getLogger("app.request")


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        start_time = time.time()

        response = await call_next(request)

        process_time = time.time() - start_time

        user_info: str = "anonymous"
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.removeprefix("Bearer ")
            payload = decode_access_token(token)
            if payload:
                user_id = payload.get("sub", "unknown")
                role = payload.get("role", "unknown")
                user_info = f"{user_id} ({role})"

        logger.info(
            f"{request.method} {request.url.path} "
            f"-> {response.status_code} "
            f"[{user_info}] "
            f"({process_time:.3f}s)"
        )

        return response
