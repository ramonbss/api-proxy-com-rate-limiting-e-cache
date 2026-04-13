from fastapi import FastAPI

app = FastAPI(
    title="API Proxy",
    description="API Proxy com Rate Limiting e Cache",
    version="0.1.0",
)


@app.get("/ping", tags=["Health"])
async def ping():
    """
    Endpoint simples de verificação (ping-pong).
    """
    return {"ping": "pong!"}
