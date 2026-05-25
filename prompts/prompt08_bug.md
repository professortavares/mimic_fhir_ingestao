[C — Contextualizado]
Corrija um bug na ingestão do arquivo Encounter do projeto MIMIC FHIR. Atualmente, os campos hospitalizacao_code e alta_code estão sendo gravados vazios no PostgreSQL, mesmo existindo valores no arquivo de origem.

[L — Limitado]
Mantenha a arquitetura atual, Docker, entry_point.sh, organização dos diretórios, logs, testes, código em português, docstrings e comentários relevantes. Não altere o comportamento das demais ingestões já funcionais.

[A — Acionável]
Investigue a estrutura real do arquivo Encounter, identifique onde estão os valores corretos de hospitalizacao_code e alta_code e ajuste a lógica de extração/mapeamento desses campos.

[R — Referenciado]
Use o arquivo de origem de Encounter como referência e valide diretamente nele que os valores existem. Adicione logs úteis para diagnosticar registros sem esses campos e crie/atualize testes unitários cobrindo a extração de hospitalizacao_code e alta_code a partir de exemplos reais ou representativos do NDJSON.

[O — Objetivo]
Após a correção, a ingestão de Encounter deve preencher corretamente hospitalizacao_code e alta_code no PostgreSQL quando esses valores existirem no arquivo, mantendo registros sem valor como nulos/vazios de forma controlada e documentada no README.md se necessário.