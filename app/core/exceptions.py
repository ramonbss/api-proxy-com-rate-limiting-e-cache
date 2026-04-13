class ProxyBaseException(Exception):
    """Exceção base para todos os erros pertencentes ao domínio do Proxy."""

    pass


class RateLimitExceededException(ProxyBaseException):
    """
    Lançada quando um cliente excede o limite estipulado de requisições.
    Retorna um HTTP 429 "Too Many Requests".
    """

    def __init__(self, client_id: str, retry_after: int):
        self.client_id = client_id
        self.retry_after = retry_after
        super().__init__(
            f"O cliente {client_id} excedeu o limite de requisições. Tente novamente em {retry_after}s."
        )


class BackendUnavailableException(ProxyBaseException):
    """
    Lançada quando há problemas de conexão ou falhas do backend.
    """

    def __init__(self, message: str = "O backend está indisponível no momento."):
        self.message = message
        super().__init__(self.message)


class CacheException(ProxyBaseException):
    """Lançada quando houver alguma falha, não recuperavel, nas operações do cache."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)
