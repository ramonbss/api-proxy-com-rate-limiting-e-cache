import httpx
from typing import Any, Dict, Optional

from app.core.exceptions import BackendUnavailableException
from app.core.interfaces import ICacheService
from app.schemas.responses import ProxyResponse
from app.services.cache_key import build_cache_key

# métodos cacheáveis
METODOS_CACHEAVEIS = {"GET"}


class ProxyService:
    def __init__(self, backend_url: str, cache_service: ICacheService):
        """
        Args:
            backend_url: URL base do backend para onde as requisições serão encaminhadas.
            cache_service: Implementação de ICacheService por injecao de dependencia.
        """
        self.backend_url = backend_url
        self.cache_service = cache_service
        self.client = httpx.AsyncClient(base_url=self.backend_url, timeout=10.0)

    async def forward_request(
        self,
        method: str,
        path: str,
        headers: Dict[str, str],
        query_params: Optional[Dict[str, str]] = None,
        body: Optional[Any] = None,
    ) -> ProxyResponse:
        """
        Encaminha a requisição diretamente para o endereçp {backend_url}
        Utiliza cache sempre que possivel
        """
        is_cacheable = (
            method.upper() in METODOS_CACHEAVEIS and self.cache_service is not None
        )

        #  Consulta no cache primeiro
        if is_cacheable:
            cache_key = build_cache_key(path, query_params)
            cached_response = await self.cache_service.get(cache_key)
            if cached_response is not None:
                cached_response["headers"]["X-Cache"] = "HIT"
                return ProxyResponse(**cached_response)

        # Limpar o header "host" original
        forward_headers = {k: v for k, v in headers.items() if k.lower() != "host"}

        try:
            response = await self.client.request(
                method=method.upper(),
                url=path,
                params=query_params,
                headers=forward_headers,
                json=body if method.upper() in ["POST", "PUT", "PATCH"] else None,
            )
        except httpx.RequestError as e:
            raise BackendUnavailableException(
                message=f"Erro de conexão com o backend: {str(e)}"
            )

        try:
            response_body = response.json()
        except Exception:
            response_body = response.text

        response_headers = dict(response.headers)
        response_headers["X-Cache"] = "MISS"

        proxy_response = ProxyResponse(
            status_code=response.status_code,
            headers=response_headers,
            body=response_body,
        )

        # Armazena no cache apenas conexões bem sucedidas
        if is_cacheable and response.is_success:
            await self.cache_service.set(cache_key, proxy_response.model_dump())

        return proxy_response
