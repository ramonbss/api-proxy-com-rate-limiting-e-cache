import time
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.interfaces import IRateLimiter
from app.core.exceptions import RateLimitExceededException


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware que aplica rate limiting baseado no client_id.
    O rate limit é passado por injeção de dependência.
    """

    def __init__(self, app, rate_limiter: IRateLimiter):
        super().__init__(app)
        self.rate_limiter = rate_limiter

    async def dispatch(self, request: Request, call_next) -> Response:
        client_id = getattr(request.state, "client_id")

        is_allowed = await self.rate_limiter.is_allowed(client_id)
        if not is_allowed:
            reset_time = await self.rate_limiter.get_reset_time(client_id)
            retry_after = max(int(reset_time - time.time()), 1)
            raise RateLimitExceededException(
                client_id=client_id, retry_after=retry_after
            )

        response = await call_next(request)

        # Adicionar headers relacionados ao Rate limit
        remaining = await self.rate_limiter.get_remaining(client_id)
        reset_time = await self.rate_limiter.get_reset_time(client_id)

        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(reset_time)
        return response
