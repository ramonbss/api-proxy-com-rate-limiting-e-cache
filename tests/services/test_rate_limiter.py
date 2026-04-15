import pytest

from app.services.rate_limiter import LimitsRateLimiter


@pytest.fixture
def rate_limiter():
    # Cria com limite de 3 requisicoes por minuto
    return LimitsRateLimiter("3/minute")


@pytest.mark.asyncio
async def test_allow_within_limit(rate_limiter):
    # Aceita ate 3 requisicoes
    assert await rate_limiter.is_allowed("client1") is True
    assert await rate_limiter.is_allowed("client1") is True
    assert await rate_limiter.is_allowed("client1") is True

    # Quarta requisicao deve ser bloqueada
    assert await rate_limiter.is_allowed("client1") is False


@pytest.mark.asyncio
async def test_allow_multiple_clients(rate_limiter):
    """
    Testa se clientes diferentes não interferem um no outro
    """
    # cliente1 será bloqueado
    for _ in range(3):
        assert await rate_limiter.is_allowed("client1") is True
    assert await rate_limiter.is_allowed("client1") is False

    # cliente2 deve acessar normalmente
    assert await rate_limiter.is_allowed("client2") is True
    assert await rate_limiter.is_allowed("client2") is True
