[C — Contextualizado]
Estou construindo um projeto Python para importar dados do MIMIC versão FHIR a partir do arquivo ./data/MimicOrganization.ndjson.gz para um banco PostgreSQL.

[L — Limitado]
Use Docker para executar o sistema: ao rodar o container, a ingestão deve iniciar automaticamente. Gere também .env.example. O código Python deve estar em português, com docstrings e comentários de linha relevantes, priorizando simplicidade e legibilidade. Gere logs para fluxo normal, erros e falhas. Crie testes unitários para os métodos críticos.

[A — Acionável]
Implemente o projeto completo: código Python de ingestão, conexão com PostgreSQL, leitura de ndjson.gz, extração dos campos necessários, testes, Dockerfile/docker-compose se necessário, .env.example e atualização do README.md.

[R — Referenciado]
O arquivo de entrada é ./data/MimicOrganization.ndjson.gz. Analise sua estrutura para localizar e ingerir apenas os campos id e name. O README.md deve explicar o propósito do projeto: importar arquivos do MIMIC versão FHIR.

[O — Objetivo]
Ao executar o projeto via Docker, os registros do arquivo devem ser importados para uma tabela PostgreSQL contendo id e name, com logs visíveis, testes disponíveis e documentação clara de acionamento.
