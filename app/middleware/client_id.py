from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware


class ClientIdentificationMiddleware(BaseHTTPMiddleware):
    """
    Identifica o cliente a partir do header X-Client-ID.
    Não havendo o X-Client-ID, utiliza o IP de origem.
    """

    async def dispatch(self, request: Request, call_next):
        client_id = request.headers.get("X-Client-ID")
        if not client_id:
            client_id = request.client.host if request.client else "unknown"

        request.state.client_id = client_id
        return await call_next(request)
