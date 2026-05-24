[C — Contextualizado]
Evolua o projeto existente para também ingerir o arquivo ./data/MimicLocation.ndjson.gz, mantendo a arquitetura já criada para ingestão do MIMIC FHIR em PostgreSQL.

[L — Limitado]
Cite e implemente apenas os novos pontos desta evolução. Mantenha o padrão atual de Docker, logs, testes, código em português, simplicidade, docstrings e comentários relevantes.

[A — Acionável]
Adicione a ingestão de Location, criando/atualizando a tabela necessária e a lógica de importação para o novo arquivo.

[R — Referenciado]
Analise ./data/MimicLocation.ndjson.gz e ingira apenas os campos id, name e a FK para Organization. Como arquivos .gz foram adicionados ao repositório na etapa anterior, remova-os do repo e adicione uma regra no .gitignore para impedir novos commits de arquivos .gz.

[O — Objetivo]
Ao executar via Docker, o projeto deve importar Organization e Location, relacionando Location com Organization por FK, sem versionar arquivos .gz, e com o README.md atualizado com a nova ingestão e forma de acionamento.