import pytest
import httpx

from app.services.proxy_service import ProxyService
from app.core.exceptions import BackendUnavailableException


@pytest.fixture
def proxy_service():
    return ProxyService(backend_url="http://mock-backend")


@pytest.mark.asyncio
async def test_forward_request_success(proxy_service, httpx_mock):
    """Testa se uma requisição é repassada com sucesso ao backend e resposta lida corretamente."""
    httpx_mock.add_response(
        url="http://mock-backend/api/users",
        method="GET",
        status_code=200,
        json={"data": "success"},
    )

    response = await proxy_service.forward_request(
        method="GET",
        path="/api/users",
        headers={"host": "localhost", "x-custom": "123"},
    )

    assert response.status_code == 200
    assert response.body == {"data": "success"}
    # O header Host do backend não deve vazar na resposta ao cliente
    assert "host" not in response.headers


@pytest.mark.asyncio
async def test_forward_request_backend_unavailable(proxy_service, httpx_mock):
    """Testa se problemas de rede disparam uma exceção de backend."""
    httpx_mock.add_exception(
        httpx.ConnectError("Connection refused"), url="http://mock-backend/api/users"
    )

    with pytest.raises(BackendUnavailableException):
        await proxy_service.forward_request(
            method="GET", path="/api/users", headers={"host": "localhost"}
        )
