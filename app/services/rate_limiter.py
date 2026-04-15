import time
import asyncio
from typing import Optional
from limits import storage, strategies, parse

from app.core.interfaces import IRateLimiter


class LimitsRateLimiter(IRateLimiter):
    """
    Implementação de Rate Limiting utilizando algoritmo MovingWindow.
    Principais componentes:
        storage: Armazena os contadores
        strategy: Algoritmo utilizado pelo rate limiting
        item: Limite de acesso no formato aceito pela biblioteca limits
    """

    def __init__(self, rate_limit_string: str = "10/minute"):
        """
        Args:
            rate_limit_string: Limite no formato aceito pelo limits (ex: '10/minute')
        """
        self._storage = storage.MemoryStorage()
        self._strategy = strategies.MovingWindowRateLimiter(self._storage)
        self._item = parse(rate_limit_string)

    async def is_allowed(self, client_id: str) -> bool:
        """
        Verifica se a requisição do client_id
        """
        # incrementa o contador de acessos e retorna True se não excedido
        return self._strategy.hit(self._item, client_id)

    async def get_remaining(self, client_id: str) -> int:
        """
        Calcula requisições restantes.
        """
        stats = self._strategy.get_window_stats(self._item, client_id)
        return stats.remaining

    async def get_reset_time(self, client_id: str) -> int:
        """
        Retorna o timestamp de quando o registro mais antigo vai expirar.
        """
        stats = self._strategy.get_window_stats(self._item, client_id)
        return int(stats.reset_time)
