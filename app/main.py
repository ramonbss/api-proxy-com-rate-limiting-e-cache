from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import json

from app.services.proxy_service import ProxyService
from app.core.exceptions import BackendUnavailableException

app = FastAPI(
    title="API Proxy",
    description="API Proxy com Rate Limiting e Cache",
    version="0.1.0",
)

# jsonplaceholder é uma api publica usada para testes
proxy_service = ProxyService(backend_url="https://jsonplaceholder.typicode.com")


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
