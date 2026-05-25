[C — Contextualizado]
Refatore o projeto existente de ingestão MIMIC FHIR em Python/PostgreSQL, mantendo a arquitetura funcional já criada e a ingestão atual de Organization e Location.

[L — Limitado]
Altere apenas a organização e execução do projeto, sem mudar o comportamento da ingestão. Preserve Docker, logs, testes, código em português, docstrings, comentários relevantes e atualize o README.md.

[A — Acionável]
Ajuste o docker-compose para usar um PostgreSQL externo informado por variáveis de ambiente, sem subir uma imagem PostgreSQL dentro do projeto. Reorganize os arquivos .py soltos na raiz, como banco, ingestão e leitor, em um diretório adequado de aplicação. Altere o Dockerfile para executar um entry_point.sh em vez de chamar Python diretamente.

[R — Referenciado]
No .env.example, substitua valores reais de conexão com banco por placeholders, mantendo os nomes dos arquivos de importação. A execução real deve usar um arquivo .env com os valores verdadeiros de conexão ao PostgreSQL.

[O — Objetivo]
Ao executar via Docker, o entry_point.sh deve iniciar a ingestão usando as configurações do .env, conectando-se ao PostgreSQL externo informado, com código organizado em diretórios adequados, .env.example seguro e README.md atualizado.