import httpx
from typing import Any, Dict, Optional

from app.core.exceptions import BackendUnavailableException
from app.schemas.responses import ProxyResponse


class ProxyService:
    def __init__(self, backend_url: str):
        self.backend_url = backend_url
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
        """

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

        proxy_response = ProxyResponse(
            status_code=response.status_code,
            headers=response.headers,
            body=response_body,
        )

        return proxy_response
