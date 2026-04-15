from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import json

from app.services.proxy_service import ProxyService
from app.services.cache_service import TTLCacheService
from app.services.rate_limiter import LimitsRateLimiter
from app.middleware.client_id import ClientIdentificationMiddleware
from app.middleware.rate_limit import RateLimitMiddleware
from app.core.exceptions import BackendUnavailableException, RateLimitExceededException

app = FastAPI(
    title="API Proxy",
    description="API Proxy com Rate Limiting e Cache",
    version="0.1.0",
)

cache_service = TTLCacheService(max_size=512, default_ttl=60)
rate_limiter_service = LimitsRateLimiter(rate_limit_string="10/minute")
proxy_service = ProxyService(
    backend_url="https://jsonplaceholder.typicode.com",
    cache_service=cache_service,
)

# Registra middlewares na ordem inversa de execução. O middleware segue um FILO
app.add_middleware(RateLimitMiddleware, rate_limiter=rate_limiter_service)
app.add_middleware(ClientIdentificationMiddleware)


@app.exception_handler(RateLimitExceededException)
async def rate_limit_exceeded_handler(
    request: Request, exc: RateLimitExceededException
):
    return JSONResponse(
        status_code=429,
        content={"error": "Too Many Requests", "detail": str(exc)},
        headers={"Retry-After": str(exc.retry_after)},
    )


@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_endpoint(path: str, request: Request):
    """
    Endpoint que atua como proxy reverso
    """
    query_params = dict(request.query_params)
    headers = dict(request.headers)

    body_data = await request.body()
    body_json = None
    if body_data:
        try:
            body_json = json.loads(body_data)
        except json.JSONDecodeError:
            pass

    try:
        response = await proxy_service.forward_request(
            method=request.method,
            path=f"/{path}",
            headers=headers,
            query_params=query_params,
            body=body_json,
        )
        return JSONResponse(
            status_code=response.status_code,
            content=response.body,
            headers=response.headers,
        )
    except BackendUnavailableException as e:
        return JSONResponse(
            status_code=502, content={"error": "Bad Gateway", "detail": str(e)}
        )
    except Exception as e:
        return JSONResponse(
            status_code=500, content={"error": "Internal Error", "detail": str(e)}
        )
