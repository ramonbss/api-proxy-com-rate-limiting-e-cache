# API Proxy com Rate Limiting e Cache — Planejamento Detalhado por Commits

## Nome do arquivo
`output/api-proxy-project-planning.md`

## Documentos complementares
Este planejamento deve ser usado em conjunto com:
- `output/api-proxy-project-structure.md` _(a ser criado na implementação)_
- `README.md` _(gerado no Commit 005)_
- `ARCHITECTURE.md` _(gerado no Commit 037)_
- `RUNNING.md` _(gerado no Commit 038)_

## Visão do projeto
Construir uma API em **FastAPI** que funcione como proxy reverso para um backend fictício, com rate limiting por cliente (Sliding Window), cache de respostas in-memory (TTL + LRU), tratamento de erros estruturado, observabilidade via logs e documentação completa de execução.

## Por que FastAPI e não Flask?
FastAPI foi escolhido em vez do Flask pelos seguintes motivos:
- **Async nativo**: suporte a `async/await` sem extensões externas, essencial para um proxy que faz I/O (chamadas HTTP ao backend) de forma eficiente.
- **Pydantic integrado**: validação e serialização de schemas sem boilerplate adicional.
- **OpenAPI automático**: documentação Swagger UI gerada automaticamente a partir de type hints e docstrings.
- **Middleware nativo**: pipeline de middleware de primeira classe, sem depender de extensões como `Flask-Middleware`.

## Filosofia de planejamento
Cada item abaixo tem granularidade de **um commit focado**. Um commit neste contexto representa:
- Um arquivo criado com seus testes correspondentes.
- Uma camada de serviço com injeção de dependência e testes.
- Um middleware ou rota com schemas e testes.
- Um adaptador de infraestrutura com testes.
- Um artefato de documentação completo e revisado.

Cada commit explicita **o motivo da escolha técnica** para preservar o raciocínio arquitetural para mantenedores futuros.

---

## Macro Milestones

1. Fundação do repositório
2. Abstrações centrais (interfaces e exceções)
3. Configuração e settings
4. Mock backend (backend fictício)
5. Cache Service
6. Rate Limiter Service
7. Proxy Service (Facade)
8. Middleware e rotas
9. Tratamento de erros e observabilidade
10. Testes de integração
11. Documentação e execução

---

## Plano por commits

---

### Milestone 1 — Fundação do repositório

- [ ] **Commit 001**: Inicializar `pyproject.toml` com dependências do projeto (`fastapi`, `uvicorn`, `httpx`, `cachetools`, `pydantic-settings`, `pytest`, `pytest-asyncio`, `ruff`).
  > **Motivo**: `pyproject.toml` é o padrão moderno PEP 517/518/621, centralizando metadados, dependências e configuração de ferramentas num único arquivo. Substitui o padrão legado `setup.py` + `requirements.txt` separados, reduzindo duplicação e fragmentação de configuração.

- [ ] **Commit 002**: Criar `.gitignore`, `.editorconfig` e `.env.example`.
  > **Motivo**: `.gitignore` protege artefatos de build (`__pycache__`, `.pytest_cache`, `.venv`) e segredos (`.env`) de vazar para o repositório. `.editorconfig` garante consistência de indentação e encoding entre VSCode, PyCharm e qualquer outro editor. `.env.example` documenta todas as variáveis de ambiente necessárias sem expor valores reais, seguindo a metodologia [12-factor app](https://12factor.net/config).

- [ ] **Commit 003**: Criar estrutura base de pastas (`app/`, `app/core/`, `app/services/`, `app/middleware/`, `app/routers/`, `app/schemas/`, `tests/`, `docs/`).
  > **Motivo**: Separar código de produção (`app/`), testes (`tests/`) e documentação (`docs/`) segue a convenção da comunidade Python e facilita a configuração de ferramentas como `pytest` (que aponta para `tests/`) e `ruff` (que exclui `tests/` de certas regras). A estrutura interna de `app/` reflete as camadas arquiteturais: `core/` (abstrações), `services/` (implementações), `middleware/` (pipeline HTTP), `routers/` (endpoints), `schemas/` (contratos de dados).

- [ ] **Commit 004**: Adicionar `Makefile` com alvos `run`, `test`, `lint`, `format` e `dev`.
  > **Motivo**: O `Makefile` funciona como interface unificada de comandos, reduzindo a curva de aprendizado para novos contribuidores. Em vez de memorizar `uvicorn app.main:app --reload --port 8000`, basta `make run`. Todos os ambientes (local, CI/CD) executam os mesmos alvos, garantindo consistência. É tecnologia-agnóstica: funciona em qualquer shell Unix sem instalar nada extra.

- [ ] **Commit 005**: Adicionar `README.md` com visão do projeto, diagrama de arquitetura em texto e lista de comandos rápidos.
  > **Motivo**: O README é a primeira coisa que qualquer pessoa lê ao abrir o repositório. Documentar a motivação, a arquitetura de alto nível e os comandos de execução antes de escrever código garante que o projeto tem propósito claro desde o início. Seguindo a filosofia "docs as code": documentação vive junto ao código e evolui com ele.

- [ ] **Commit 006**: Adicionar `Dockerfile` para o serviço proxy com multi-stage build.
  > **Motivo**: Multi-stage build separa o ambiente de build (com ferramentas de compilação) do ambiente de runtime (imagem enxuta), resultando em imagens menores e mais seguras. Containerização garante que o ambiente de execução é idêntico em desenvolvimento, CI e produção, eliminando o problema "funciona na minha máquina".

- [ ] **Commit 007**: Adicionar `docker-compose.yml` orquestrando o serviço proxy e o mock backend como serviços separados.
  > **Motivo**: `docker-compose` permite subir todo o ambiente com um único `docker-compose up`, sem instalar Python ou dependências manualmente. Separar proxy e mock backend em containers distintos reflete a arquitetura real de dois processos independentes, tornando o ambiente de desenvolvimento fiel à produção.

---

### Milestone 2 — Abstrações centrais

- [ ] **Commit 008**: Criar `app/core/interfaces.py` com `IRateLimiter` (ABC) declarando `is_allowed()`, `get_remaining()` e `get_reset_time()`.
  > **Motivo**: Interface via `ABC` (Abstract Base Class) implementa o princípio **D do SOLID (Dependency Inversion)**: o `ProxyService` dependerá desta abstração, não de uma implementação concreta. Isso permite trocar o algoritmo de Sliding Window por Token Bucket no futuro sem alterar o código cliente. O Python fará `TypeError` em tempo de instanciação se uma subclasse não implementar todos os métodos abstratos, funcionando como contrato verificável.

- [ ] **Commit 009**: Adicionar `ICacheService` (ABC) em `app/core/interfaces.py` com `get()`, `set()`, `invalidate()` e `clear()`.
  > **Motivo**: Mesma razão do `IRateLimiter`. A abstração do cache permite trocar de in-memory (`TTLCache`) para Redis ou Memcached no futuro sem alterar o `ProxyService`. Aplica o princípio **O (Open/Closed)**: aberto para extensão (nova implementação), fechado para modificação (código existente não muda).

- [ ] **Commit 010**: Criar `app/core/exceptions.py` com hierarquia customizada: `ProxyBaseException`, `RateLimitExceededException`, `BackendUnavailableException`, `CacheException`.
  > **Motivo**: Exceções customizadas carregam semântica de domínio. `except RateLimitExceededException` é mais legível, preciso e seguro do que `except Exception`. A hierarquia com base comum (`ProxyBaseException`) permite capturar todas as exceções do domínio com um único handler, ou handlers específicos para cada tipo. Cada exceção pode carregar dados contextuais (ex: `retry_after`, `client_id`) usados pelo handler para montar a resposta HTTP.

- [ ] **Commit 011**: Criar `app/schemas/responses.py` com modelos Pydantic: `ProxyResponse`, `ErrorResponse` e `RateLimitInfo`.
  > **Motivo**: Schemas Pydantic garantem validação e serialização type-safe. `ErrorResponse` padroniza o formato de erro em todos os endpoints (`{"error": "...", "detail": "...", "retry_after": N}`), tornando a API previsível para os clientes. `RateLimitInfo` encapsula os dados de rate limit retornados nos headers, centralizando a lógica de formatação.

---

### Milestone 3 — Configuração e settings

- [ ] **Commit 012**: Criar `app/config.py` com classe `Settings` usando `pydantic-settings`, carregando variáveis de ambiente com validação de tipos e valores padrão documentados.
  > **Motivo**: `pydantic-settings` carrega configurações do `.env` e de variáveis de ambiente com validação automática de tipos (ex: `RATE_LIMIT_MAX_REQUESTS: int = 10`). Evita strings mágicas espalhadas pelo código e centraliza toda a configuração num único lugar. Se uma variável obrigatória estiver ausente, o erro acontece na inicialização do app (fail-fast), não em tempo de execução numa requisição.

- [ ] **Commit 013**: Adicionar configuração de logging estruturado em JSON em `app/core/logging.py` com níveis diferenciados por ambiente.
  > **Motivo**: Logs estruturados em JSON são consumíveis por ferramentas de observabilidade (Datadog, ELK Stack, CloudWatch, Loki). Em desenvolvimento, um formatter legível por humanos é configurado. Em produção, JSON com campos padronizados (`timestamp`, `level`, `service`, `message`, `extra`) permite queries e alertas. O nível de log é configurável via `Settings`.

---

### Milestone 4 — Mock backend (backend fictício)

- [ ] **Commit 014**: Criar `app/mock_backend/main.py` com FastAPI standalone expondo endpoints `/products`, `/users` e `/orders` com dados fictícios.
  > **Motivo**: O mock backend simula o "backend fictício" do enunciado. Ter um servidor real (ainda que fake) rodando em porta separada (ex: 8001) permite testar o fluxo completo de proxy sem depender de APIs externas, tornando os testes determinísticos e funcionando offline. É um exemplo do padrão **Test Double** aplicado em nível de serviço.

- [ ] **Commit 015**: Adicionar latência artificial configurável e simulação de erros aleatórios no mock backend.
  > **Motivo**: Simular latência (ex: 100-300ms) permite demonstrar que o cache reduz o tempo de resposta de forma mensurável. Simular falhas ocasionais (ex: 10% dos requests retornam 500) permite validar que o tratamento de erros do proxy funciona corretamente em condições adversas, cobrindo os caminhos de falha desde o início.

---

### Milestone 5 — Cache Service

- [ ] **Commit 016**: Implementar `TTLCacheService` em `app/services/cache_service.py` usando `cachetools.TTLCache` com `threading.Lock` para thread-safety. Implementa `ICacheService`.
  > **Motivo**: `cachetools.TTLCache` oferece LRU (Least Recently Used) + TTL (Time-To-Live) em memória sem dependências externas — sem Redis, sem infraestrutura adicional. É thread-safe com `threading.Lock` porque FastAPI pode usar múltiplas threads no modo de workers síncronos e em contextos de test. TTL garante que dados envelhecidos são descartados automaticamente, evitando que o proxy sirva respostas desatualizadas indefinidamente.

- [ ] **Commit 017**: Adicionar utilitário `app/services/cache_key.py` para geração determinística de chaves de cache (método HTTP + path + query params ordenados → hash SHA-256 truncado).
  > **Motivo**: A chave de cache precisa ser determinística (mesmos inputs → mesma chave) e única (inputs diferentes → chaves diferentes). Query params ordenados (`?b=2&a=1` equivale a `?a=1&b=2`) antes do hash evita duplicações desnecessárias. SHA-256 truncado mantém as chaves com tamanho fixo independente do tamanho da URL, evitando memory overhead com URLs longas.

- [ ] **Commit 018**: Adicionar testes unitários para `TTLCacheService` cobrindo: cache hit, cache miss, expiração por TTL, evicção LRU e thread-safety básico.
  > **Motivo**: Testes unitários do cache isolam e validam comportamentos críticos antes de integrá-los ao proxy. Hit retorna dado correto, miss retorna `None`, expiração funciona após o TTL, evicção LRU descarta o item menos recentemente usado quando a capacidade máxima é atingida. São a base para refactoring seguro no futuro.

---

### Milestone 6 — Rate Limiter Service

- [ ] **Commit 019**: Implementar `SlidingWindowRateLimiter` em `app/services/rate_limiter.py` usando `collections.deque` de timestamps por `client_id`. Implementa `IRateLimiter`.
  > **Motivo**: **Sliding Window** com deque de timestamps é `O(1)` amortizado para `is_allowed()`. Cada cliente tem sua própria deque, evitando contenção entre clientes distintos. Sliding Window é mais justo que Fixed Window porque não sofre com o problema de burst na borda da janela (um cliente poderia fazer 2x o limite em 1 segundo aproveitando a virada da janela fixa). A deque com `maxlen` limita automaticamente a memória por cliente.

- [ ] **Commit 020**: Adicionar rotina de limpeza periódica em `SlidingWindowRateLimiter` para remover entradas de clientes inativos da memória.
  > **Motivo**: Sem limpeza, a estrutura de dados cresce indefinidamente à medida que novos `client_id`s aparecem (cada IP único ocupa espaço). A limpeza remove entradas cujo último timestamp é mais antigo que a janela de tempo configurada, pois esses clientes não têm requisições recentes e podem ser recriados sob demanda. Previne memory leak em produção com alto volume de clientes distintos.

- [ ] **Commit 021**: Adicionar testes unitários para `SlidingWindowRateLimiter` cobrindo: permitir dentro do limite, bloquear ao exceder, liberar após a janela deslizar, múltiplos clientes isolados e limpeza de entradas inativas.
  > **Motivo**: O rate limiter é o componente de segurança mais crítico do proxy. Testes unitários cobrem os cenários de negócio: N requisições permitidas, N+1 bloqueada, liberação correta após o tempo da janela, e isolamento entre clientes (cliente A não interfere no contador do cliente B). Testes de múltiplos clientes simultâneos validam a ausência de race conditions.

---

### Milestone 7 — Proxy Service (Facade)

- [ ] **Commit 022**: Implementar `ProxyService` em `app/services/proxy_service.py` recebendo `IRateLimiter` e `ICacheService` via injeção de dependência no construtor.
  > **Motivo**: `ProxyService` é o **Facade Pattern**: esconde a complexidade de orquestrar rate limit + cache + forward + resposta atrás de uma interface simples (`forward_request()`). Dependency Injection via construtor (não instanciação interna) permite mockar as dependências nos testes unitários do serviço, testando o `ProxyService` de forma isolada.

- [ ] **Commit 023**: Adicionar lógica de forwarding de requisições usando `httpx.AsyncClient` com timeout configurável e connection pooling.
  > **Motivo**: `httpx` é a escolha moderna para HTTP assíncrono em Python, compatível com o event loop do FastAPI (diferente de `requests`, que é síncrono). `AsyncClient` com connection pooling reutiliza conexões TCP com o backend, reduzindo overhead de handshake por requisição. Timeout configurável via `Settings` previne que requisições lentas ao backend bloqueiem workers indefinidamente.

- [ ] **Commit 024**: Adicionar lógica de caching no `ProxyService`: cachear apenas respostas GET com status 2xx, TTL vindo de `Settings`, e chave via utilitário do Commit 017.
  > **Motivo**: Apenas respostas `GET` bem-sucedidas (2xx) são cacheáveis, respeitando a semântica REST: métodos idempotentes e _safe_ (`GET`, `HEAD`) podem ser cacheados; `POST`, `PUT`, `DELETE` modificam estado e nunca devem ser cacheados. TTL centralizado em `Settings` permite ajuste sem alterar código. Erros do backend (4xx, 5xx) não são cacheados para não propagar falhas temporárias.

- [ ] **Commit 025**: Adicionar headers de diagnóstico nas respostas: `X-Cache`, `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset` e `X-Proxy-Duration`.
  > **Motivo**: Headers de diagnóstico são a base de observabilidade para o cliente. `X-Cache: HIT/MISS` permite medir a taxa de acerto do cache do lado do cliente. `X-RateLimit-*` seguem o [draft IETF RateLimit Header Fields for HTTP](https://datatracker.ietf.org/doc/draft-ietf-httpapi-ratelimit-headers/), tornando a API interoperável com clientes que implementam backoff automático. `X-Proxy-Duration` expõe a latência interna do proxy para debugging.

---

### Milestone 8 — Middleware e rotas

- [ ] **Commit 026**: Adicionar `ClientIdentificationMiddleware` em `app/middleware/client_id.py` extraindo `client_id` do header `X-Client-ID` com fallback para IP do cliente.
  > **Motivo**: Rate limiting por cliente exige identificar o cliente de forma unívoca. Header `X-Client-ID` permite identificação explícita (API keys, user IDs, tokens de sessão). Fallback para IP (`request.client.host`) permite que o proxy funcione sem autenticação prévia, cobrindo o caso básico do enunciado. O `client_id` resolvido é injetado no `request.state` para consumo downstream sem re-computação.

- [ ] **Commit 027**: Adicionar `RateLimitMiddleware` em `app/middleware/rate_limit.py` retornando HTTP 429 com header `Retry-After` quando o limite é excedido.
  > **Motivo**: Middleware intercept toda requisição antes de chegar ao route handler, garantindo que nenhuma rota "esquece" de checar o rate limit. HTTP 429 é o código padrão RFC 6585 para "Too Many Requests". `Retry-After` informa ao cliente exatamente quantos segundos aguardar antes de tentar novamente, habilitando backoff inteligente e reduzindo requisições desnecessárias após o bloqueio.

- [ ] **Commit 028**: Criar `app/routers/proxy_router.py` com rota curinga `GET /proxy/{path:path}` que delega ao `ProxyService`.
  > **Motivo**: Rota curinga `{path:path}` do FastAPI captura qualquer subpath (ex: `/proxy/products/123?filter=active`) e encaminha ao backend preservando path e query string. Isso torna o proxy **transparente**: o cliente chama `/proxy/products` e recebe exatamente o que receberia chamando `/products` diretamente no backend. A rota delega toda a lógica ao `ProxyService`, mantendo o router fino (sem lógica de negócio).

---

### Milestone 9 — Tratamento de erros e observabilidade

- [ ] **Commit 029**: Adicionar exception handler global para `RateLimitExceededException` → HTTP 429 com `ErrorResponse` padronizado.
  > **Motivo**: Handler global via `@app.exception_handler` evita código repetitivo de `try/except` nos route handlers. Mapeia exceções de domínio para respostas HTTP padronizadas usando o `ErrorResponse` schema do Commit 011, garantindo que todos os erros de rate limit têm o mesmo formato JSON, independentemente de onde a exceção foi lançada.

- [ ] **Commit 030**: Adicionar exception handler global para `BackendUnavailableException` → HTTP 502 ou 503 com `Retry-After` condicional.
  > **Motivo**: HTTP **502 Bad Gateway** é semanticamente correto quando o backend retorna uma resposta inválida (erro de aplicação). HTTP **503 Service Unavailable** é correto quando o backend está completamente inacessível (timeout, connection refused). Distinguir os dois códigos ajuda o cliente a decidir sua estratégia: 503 com `Retry-After` sugere retry automático; 502 sugere que o problema pode ser permanente.

- [ ] **Commit 031**: Adicionar `LoggingMiddleware` em `app/middleware/logging.py` registrando cada requisição com `duration_ms`, `status_code`, `cache_hit`, `client_id` e `path` em JSON estruturado.
  > **Motivo**: Logs estruturados por requisição são a base de observabilidade operacional. `duration_ms` permite detectar degradação de performance ao longo do tempo. `cache_hit` no log permite calcular a **taxa de acerto do cache** agregando os logs (ex: no Datadog). `client_id` permite identificar padrões de uso e abuso por cliente específico sem alterar o código de negócio.

- [ ] **Commit 032**: Adicionar endpoints `/health` e `/ready` em `app/routers/health.py`.
  > **Motivo**: `/health` retorna 200 se o processo está vivo (usado por load balancers e Docker healthcheck para saber se o container deve ser reiniciado). `/ready` retorna 200 apenas se o serviço está pronto para receber tráfego (dependências inicializadas, cache warm). A distinção é essencial para Kubernetes **liveness probe** vs **readiness probe**: um container pode estar vivo mas não pronto.

---

### Milestone 10 — Testes de integração

- [ ] **Commit 033**: Adicionar testes de integração para a rota proxy cobrindo cache HIT (segunda requisição idêntica) e cache MISS (primeira requisição e requisição com parâmetros diferentes).
  > **Motivo**: Testes de integração validam o fluxo completo — cliente → middleware → proxy service → mock backend → cache → resposta — sem mockar componentes internos. `TestClient` do FastAPI (baseado em `httpx`) permite testar sem subir servidor real, mas exercitando todo o middleware stack. Verificar `X-Cache: HIT` na segunda requisição confirma que o cache está funcionando end-to-end.

- [ ] **Commit 034**: Adicionar testes de integração para rate limiting: N requisições permitidas, N+1 retorna 429, header `Retry-After` presente, liberação após o tempo da janela.
  > **Motivo**: Testa o comportamento end-to-end do rate limiting: o contador incrementa corretamente, o bloqueio ocorre no momento certo, o header `Retry-After` tem valor plausível, e o sistema libera o cliente após a janela deslizar. Estes testes são a prova de que o `SlidingWindowRateLimiter`, o `RateLimitMiddleware` e o handler 429 estão integrados corretamente.

- [ ] **Commit 035**: Adicionar testes de integração para cenários de erro: backend indisponível retorna 502/503, client_id ausente usa fallback de IP, timeout no backend retorna erro adequado.
  > **Motivo**: Testa os **caminhos de falha** (unhappy paths), frequentemente negligenciados. Backend indisponível deve retornar 502/503, não 500 genérico. Fallback de IP garante que o proxy não quebra quando o header `X-Client-ID` está ausente. Timeout configura o comportamento defensivo do `httpx.AsyncClient`. Cobrir falhas desde o início previne surpresas em produção.

---

### Milestone 11 — Documentação e execução

- [ ] **Commit 036**: Adicionar metadados OpenAPI customizados em `app/main.py` (título, versão, descrição, tags) e docstrings nos endpoints e schemas.
  > **Motivo**: FastAPI gera Swagger UI automaticamente a partir de metadados e docstrings. Adicionar descrições, exemplos de request/response e tags torna a documentação interativa (`/docs`) útil para quem consome a API sem custo adicional de manutenção — a documentação vive no código e é sempre sincronizada com a implementação.

- [ ] **Commit 037**: Criar `ARCHITECTURE.md` com diagrama de sequência do fluxo completo, decisões arquiteturais registradas (ADRs) e justificativas das escolhas técnicas.
  > **Motivo**: Diagramas de sequência documentam o fluxo de dados de forma visual, facilitando o onboarding de novos contribuidores. **ADRs (Architecture Decision Records)** registram o _porquê_ das decisões (ex: "Por que FastAPI e não Flask?", "Por que in-memory e não Redis?"), preservando o contexto para mantenedores futuros que, sem esse registro, precisariam rever a decisão do zero.

- [ ] **Commit 038**: Criar `RUNNING.md` com instruções passo a passo de execução local (venv, uvicorn), execução via Docker Compose, execução dos testes e exemplos de requests com `curl`.
  > **Motivo**: Instrução clara de execução é **requisito explícito do enunciado**. Um projeto só é completo se alguém consegue rodá-lo do zero seguindo apenas o documento, sem precisar perguntar nada. Exemplos com `curl` permitem validar o comportamento do cache (`X-Cache: HIT/MISS`) e do rate limiting (HTTP 429) sem instalar nenhum cliente HTTP adicional.

---

## Resumo de escolhas tecnológicas

| Componente | Tecnologia | Motivo |
|---|---|---|
| **Framework** | FastAPI | Async nativo, Pydantic integrado, OpenAPI automático |
| **HTTP Client** | `httpx.AsyncClient` | Async, compatível com event loop FastAPI, connection pooling |
| **Cache** | `cachetools.TTLCache` | LRU + TTL em memória, sem dependências externas |
| **Rate Limit** | Implementação própria (Sliding Window) | Controle total do algoritmo, sem deps extras |
| **Config** | `pydantic-settings` | Validação de tipos, carregamento de `.env`, fail-fast |
| **Testes** | `pytest` + `pytest-asyncio` + `httpx.TestClient` | Padrão da comunidade Python, suporte a async |
| **Linter/Formatter** | `ruff` | Substitui `flake8` + `black` + `isort` num único binário, mais rápido |
| **Containerização** | Docker + `docker-compose` | Ambiente reproduzível, sem "funciona na minha máquina" |

## Relação com SOLID

| Princípio | Sigla | Aplicação no projeto |
|---|---|---|
| Single Responsibility | **S** | `RateLimiter`, `CacheService` e `ProxyService` têm uma única responsabilidade cada |
| Open/Closed | **O** | Novas implementações de cache/rate limit sem modificar código existente |
| Liskov Substitution | **L** | `TTLCacheService` substitui qualquer `ICacheService` sem quebrar contratos |
| Interface Segregation | **I** | `IRateLimiter` e `ICacheService` são interfaces pequenas e focadas |
| Dependency Inversion | **D** | `ProxyService` depende de `IRateLimiter` e `ICacheService`, não de implementações concretas |

## Design Patterns utilizados

| Pattern | Onde | Por quê |
|---|---|---|
| **Facade** | `ProxyService` | Esconde a complexidade de rate limit + cache + HTTP forward |
| **Strategy** | `IRateLimiter` + implementações | Algoritmos de rate limiting intercambiáveis sem alterar o cliente |
| **Template Method** | `ICacheService` + implementações | Contrato fixo, implementação variável |
| **Middleware Chain** | Pipeline de middlewares FastAPI | Cada middleware tem uma responsabilidade; são compostos em cadeia |
