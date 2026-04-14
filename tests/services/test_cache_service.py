import time

import pytest

from app.services.cache_key import build_cache_key
from app.services.cache_service import TTLCacheService


# ---------------------------------------------------------------------------
# Testes: build_cache_key
# ---------------------------------------------------------------------------


class TestBuildCacheKey:
    def test_same_input_same_key(self):
        chave1 = build_cache_key("/products", {"page": "1", "limit": "10"})
        chave2 = build_cache_key("/products", {"page": "1", "limit": "10"})
        assert chave1 == chave2

    def test_query_params_order_doesnt_matter(self):
        """?a=1&b=2 deve gerar a mesma chave que ?b=2&a=1."""
        chave1 = build_cache_key("/products", {"a": "1", "b": "2"})
        chave2 = build_cache_key("/products", {"b": "2", "a": "1"})
        assert chave1 == chave2

    def test_different_paths_different_keys(self):
        chave1 = build_cache_key("/products")
        chave2 = build_cache_key("/users")
        assert chave1 != chave2

    def test_different_query_params_different_keys(self):
        chave1 = build_cache_key("/products", {"page": "1"})
        chave2 = build_cache_key("/products", {"page": "2"})
        assert chave1 != chave2

    def test_empty_query_params_doesnt_throw_exceptions(self):
        chave = build_cache_key("/products")
        assert isinstance(chave, str)
        assert len(chave) == 32

    def test_fixed_size_independent_of_url_length(self):
        """Hash truncado deve ter sempre 32 caracteres."""
        chave_curta = build_cache_key("/a")
        chave_longa = build_cache_key("/" + "x" * 500, {"k": "v" * 100})
        assert len(chave_curta) == 32
        assert len(chave_longa) == 32


# ---------------------------------------------------------------------------
# Testes: TTLCacheService
# ---------------------------------------------------------------------------
@pytest.fixture
def cache() -> TTLCacheService:
    return TTLCacheService()


@pytest.mark.asyncio
class TestTTLCacheService:
    async def test_cache_miss_returns_none(self, cache: TTLCacheService):
        resultado = await cache.get("chave-inexistente")
        assert resultado is None

    async def test_cache_hit_returns_correct_value(self, cache: TTLCacheService):
        await cache.set("chave", {"status_code": 200, "body": "ok"})
        resultado = await cache.get("chave")
        assert resultado == {"status_code": 200, "body": "ok"}

    async def test_expiration_by_ttl(self):
        """Após o TTL, o item deve ser removido automaticamente."""
        cache = TTLCacheService(default_ttl=1)
        await cache.set("chave", "valor")
        assert await cache.get("chave") == "valor"

        time.sleep(1.1)  # Aguarda expiração

        assert await cache.get("chave") is None

    async def test_lru_eviction_when_max_size_is_reached(self):
        """Ao atingir max_size, o item menos recentemente usado é descartado."""
        cache = TTLCacheService(max_size=2, default_ttl=60)
        await cache.set("a", 1)
        await cache.set("b", 2)
        await cache.get("a")  # "a" vira o mais recente
        await cache.set("c", 3)  # "b" é o LRU → deve ser removido

        assert await cache.get("a") == 1
        assert await cache.get("c") == 3
        assert await cache.get("b") is None  # removido por LRU

    async def test_invalidate_remove_item(self, cache: TTLCacheService):
        await cache.set("chave", "valor")
        await cache.invalidate("chave")
        assert await cache.get("chave") is None

    async def test_invalidate_non_existent_key_doesnt_throw_exception(
        self, cache: TTLCacheService
    ):
        await cache.invalidate("nao-existe")  # Não deve lançar

    async def test_clear_remove_all_items(self, cache: TTLCacheService):
        await cache.set("a", 1)
        await cache.set("b", 2)
        await cache.clear()
        assert await cache.get("a") is None
        assert await cache.get("b") is None

    async def test_multiple_clients_isolated(self, cache: TTLCacheService):
        """Chaves diferentes armazenam valores independentes."""
        await cache.set("cliente_a", {"data": "resposta_a"})
        await cache.set("cliente_b", {"data": "resposta_b"})
        assert (await cache.get("cliente_a"))["data"] == "resposta_a"
        assert (await cache.get("cliente_b"))["data"] == "resposta_b"

    async def test_set_overwrites_existing_value(self, cache: TTLCacheService):
        await cache.set("chave", "valor_antigo")
        await cache.set("chave", "valor_novo")
        assert await cache.get("chave") == "valor_novo"
