from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.services.rate_limiter import LimitsRateLimiter
from app.middleware.client_id import ClientIdentificationMiddleware
from app.middleware.rate_limit import RateLimitMiddleware
from app.core.exceptions import RateLimitExceededException
from app.routers.proxy import proxy_router

# Toda esta configuracao abaixo poderia ser movida para um Factory pattern
# para facilitar a injecao de dependencias, multiplas instancias e testes isolados com diferentes configurações.
# Como está a nível de modulo, todo codigo abaixo sera executado assim que o Python importar este modulo.

app = FastAPI(
    title="API Proxy",
    description="API Proxy com Rate Limiting e Cache",
    version="0.1.0",
)

rate_limiter_service = LimitsRateLimiter(rate_limit_string="10/minute")


# Registra middlewares na ordem inversa de execução. O middleware segue um FILO
app.add_middleware(RateLimitMiddleware, rate_limiter=rate_limiter_service)
app.add_middleware(ClientIdentificationMiddleware)


@app.exception_handler(RateLimitExceededException)
async def rate_limit_exceeded_handler(
    request: Request, exc: RateLimitExceededException
):
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={"error": "Too Many Requests", "detail": str(exc)},
        headers={"Retry-After": str(exc.retry_after)},
    )


@app.get("/health", tags=["health"])
def health() -> JSONResponse:
    return JSONResponse({"status": "ok"})


app.include_router(proxy_router)
