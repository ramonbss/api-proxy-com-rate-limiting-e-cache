import pytest
from app.services.cache_service import TTLCacheService
from app.services.proxy_service import ProxyService


@pytest.fixture
def non_mocked_hosts() -> list:
    return ["jsonplaceholder.typicode.com"]


@pytest.mark.asyncio
async def test_forward_request_real_api(non_mocked_hosts):
    """
    Teste de integração real.
    """
    cache_service = TTLCacheService(max_size=512, default_ttl=60)
    proxy_service = ProxyService("https://jsonplaceholder.typicode.com", cache_service)

    response = await proxy_service.forward_request(
        method="GET", path="/todos/1", headers={}
    )

    assert response.status_code == 200
    assert isinstance(response.body, dict)
    assert response.body["id"] == 1
    assert "userId" in response.body
