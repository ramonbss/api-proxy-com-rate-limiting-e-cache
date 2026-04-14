import pytest
from app.services.proxy_service import ProxyService


@pytest.fixture
def non_mocked_hosts() -> list:
    return ["jsonplaceholder.typicode.com"]


@pytest.mark.asyncio
async def test_forward_request_real_api(non_mocked_hosts):
    """
    Teste de integração real.
    """

    proxy_service = ProxyService(backend_url="https://jsonplaceholder.typicode.com")

    response = await proxy_service.forward_request(
        method="GET", path="/todos/1", headers={}
    )

    assert response.status_code == 200
    assert isinstance(response.body, dict)
    assert response.body["id"] == 1
    assert "userId" in response.body
