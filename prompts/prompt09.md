[C — Contextualizado]
Evolua o projeto MIMIC FHIR para gerar automaticamente um dicionário de dados em YAML ao final da ingestão.

[L — Limitado]
Mantenha a arquitetura atual, Docker, entry_point.sh, logs, testes, código em português, docstrings e comentários relevantes. Não altere o comportamento das ingestões já existentes.

[A — Acionável]
Implemente a geração de um arquivo YAML de dicionário de dados no diretório /dic do projeto, executado automaticamente ao final da ingestão dos dados.

[R — Referenciado]
O dicionário deve conter, no mínimo, para cada tabela ingerida: nome da tabela, descrição da tabela e, para cada coluna, nome, descrição, tipo, obrigatoriedade, indicação de PK, indicação de FK com tabela referenciada quando existir, e 3 exemplos de valores obtidos dos dados importados.

[O — Objetivo]
Ao executar a ingestão via Docker, após importar os dados, o projeto deve criar/atualizar o dicionário YAML em /dic com a estrutura e exemplos reais das tabelas importadas, e atualizar o README.md explicando sua geração e localização.