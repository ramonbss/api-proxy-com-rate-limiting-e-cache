# Decisões de Projeto

## Implementar classes abstratas (interfaces) para os serviços de cache e rate limiting, além das exceptions iniciais.
- A finalidade disto é:
1. ter um "o quê" bem definido antes das implementações começarem. Assim, já se tem uma ideia de como o projeto ficará e se é necessário fazer algum ajuste na arquitetura antes de começar a implementar o "como".
1. Facilita testes, basta passar um mock que implemente a interface para testar o serviço.
1. Exceções são mais facilmente identificáveis e tratáveis.

## Implementar Proxy Service
- Implementar proxy com async. Como se trata de operações I/O, o proxy se mantém livre para novas requisições enquanto aguarda uma resposta do backend
- Implementar testes unitários e de integração (para confirmar que o proxy está funcionando corretamente, ja que não há um backend real) para o proxy
- Receber principais verbos HTTP: GET, POST, PUT, DELETE, PATCH
- Tratar o header Host
- Tratar exceções provenientes da conexão com o backend
- [Nao se aplica]Limpar headers que não fazem sentido após o httpx já ter decodificado (gzip, brotli, etc)


## Implementar Cache
- Utilizar cachetools (TTL e LRU for free)
- Funcao de hash deterministica (funcao 'hash' python adiciona um 'salt' para randomizar o resultado)
- logica de hit/miss
