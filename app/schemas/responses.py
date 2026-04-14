from typing import Any, Dict
from pydantic import BaseModel


class ProxyResponse(BaseModel):
    status_code: int
    headers: Dict[str, str]
    body: Any


class ErrorResponse(BaseModel):
    error: str
    detail: str
