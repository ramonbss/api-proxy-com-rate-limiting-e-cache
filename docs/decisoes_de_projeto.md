* Decisões de Projeto

** 1. Implementar classes abstratas (interfaces) para os serviços de cache e rate limiting, além das exceptions iniciais.
- A finalidade disto é:
1. ter um "o quê" bem definido antes das implementações começarem. Assim, já se tem uma ideia de como o projeto ficará e se é necessário fazer algum ajuste na arquitetura antes de começar a implementar o "como".
1. Facilita testes, basta passar um mock que implemente a interface para testar o serviço.
1. Exceções são mais facilmente identificáveis e tratáveis.



