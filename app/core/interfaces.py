from abc import ABC, abstractmethod
from typing import Any, Optional


class IRateLimiter(ABC):
    """
    Interface para o serviço de Rate Limiting.
    """

    @abstractmethod
    async def is_allowed(self, client_id: str) -> bool:
        """
        Verifica se a requisição do client_id é permitida na janela atual.

        Args:
            client_id: Identificador do cliente (ex: IP, API Key).

        Returns:
            bool: True se for permitido, False se tiver excedido o limite.
        """
        pass

    @abstractmethod
    async def get_remaining(self, client_id: str) -> int:
        """
        Retorna o número de requisições restantes para o client_id na janela atual.
        """
        pass

    @abstractmethod
    async def get_reset_time(self, client_id: str) -> int:
        """
        Retorna o timestamp UNIX (em segundos) em que o limite do client_id será liberado.
        """
        pass


class ICacheService(ABC):
    """
    Interface abstrata para o serviço de Cache de respostas.
    """

    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """
        Obtém um valor do cache pela chave.

        Returns:
            O valor armazenado, ou None se não existir.
        """
        pass

    @abstractmethod
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Define um valor no cache com a chave fornecida.
        """
        pass

    @abstractmethod
    async def invalidate(self, key: str) -> None:
        """
        Remove um item do cache pela chave.
        """
        pass

    @abstractmethod
    async def clear(self) -> None:
        """
        Limpa todos os itens do cache.
        """
        pass
