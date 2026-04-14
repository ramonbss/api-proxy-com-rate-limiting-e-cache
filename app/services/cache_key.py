import hashlib
from typing import Optional


def build_cache_key(path: str, query_params: Optional[dict] = None) -> str:
    """
    Gera uma chave de cache determinística a partir do método HTTP, path e query params.

    Args:
        method: Verbo HTTP (ex: "GET").
        path: Path da requisição (ex: "/products/1").
        query_params: Dicionário com os query params da requisição.

    Returns:
        String hexadecimal de 32 caracteres representando a chave de cache.
    """
    # Ordena os params para garantir determinismo independente da ordem que vierem
    params_ordenados = ""
    if query_params:
        pares_ordenados = sorted(query_params.items())
        params_ordenados = "&".join(f"{k}={v}" for k, v in pares_ordenados)

    chave_bruta = f"{path}?{params_ordenados}"
    return hashlib.sha256(chave_bruta.encode()).hexdigest()[:32]
