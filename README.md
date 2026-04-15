## Instalação

**1. Clone o repositório**
```bash
git clone https://github.com/ramonbss/api-proxy-com-rate-limiting-e-cache
cd api-proxy-com-rate-limiting-e-cache
```

**2. Crie e ative o ambiente virtual**
```bash
python -m venv .venv

# Linux/macOS
source .venv/bin/activate

# Windows
.venv\Scripts\activate
```

**3. Instale as dependências**
```bash
pip install -r requirements.txt
```

**4. Execução**
```bash
fastapi dev app/main.py
```

**5. Exemplo de execução**

```bash
curl -X GET "http://localhost:8000/posts/1" -H "X-Client-ID: client1"
```

**6. Testes**

```bash
pytest tests/services/
```