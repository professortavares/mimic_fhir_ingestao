# MIMIC FHIR Ingestão

Projeto Python para importar dados do MIMIC versão FHIR a partir de arquivos NDJSON comprimidos com gzip para um banco de dados PostgreSQL.

## Propósito

Este projeto realiza a ingestão de registros FHIR do MIMIC (Medical Information Mart for Intensive Care) em um banco PostgreSQL. Atualmente, importa dados de organizações (`MimicOrganization.ndjson.gz`), extraindo os campos `id` e `name` para uma tabela de organizações.

## Pré-requisitos

- Docker e Docker Compose instalados

## Como Usar

### 1. Preparar o ambiente

Clone ou navegue até o diretório do projeto:

```bash
cd mimic_fhir_ingestao
```

### 2. Configurar variáveis de ambiente (opcional)

Copie o arquivo `.env.example` para `.env` e ajuste as configurações conforme necessário:

```bash
cp .env.example .env
```

O arquivo `.env.example` contém:

```env
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=mimic_fhir
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
LOG_LEVEL=INFO
CAMINHO_ARQUIVO=./data/MimicOrganization.ndjson.gz
```

### 3. Executar a ingestão

Inicie os serviços com Docker Compose:

```bash
docker compose up --build
```

O comando acima:
- Inicia o serviço PostgreSQL
- Aguarda o PostgreSQL estar pronto (healthcheck)
- Constrói e executa o container da aplicação
- Realiza a ingestão automaticamente

Você verá logs como:

```
mimic_fhir_app | 2026-05-23 10:30:45,123 - ingestao - INFO - Iniciando ingestão de dados MIMIC FHIR
mimic_fhir_app | 2026-05-23 10:30:45,456 - leitor - INFO - Registro 1 lido com sucesso: id=ee172322-118b-5716-abbc-18e4c5437e15
mimic_fhir_app | 2026-05-23 10:30:45,789 - banco - INFO - Registro inserido: id=ee172322-118b-5716-abbc-18e4c5437e15, nome=Beth Israel Deaconess Medical Center
mimic_fhir_app | 2026-05-23 10:30:46,012 - ingestao - INFO - Ingestão concluída com sucesso
```

### 4. Verificar dados importados

Em outro terminal, execute:

```bash
docker compose exec postgres psql -U postgres -d mimic_fhir -c "SELECT * FROM organizacoes;"
```

Resultado esperado:

```
                  id                  |                    nome
--------------------------------------+---------------------------------------------
 ee172322-118b-5716-abbc-18e4c5437e15 | Beth Israel Deaconess Medical Center
(1 row)
```

### 5. Executar testes

Para rodar os testes unitários:

```bash
docker compose run --rm app python -m pytest tests/ -v
```

Saída esperada:

```
tests/test_leitor.py::TestExtrairCampos::test_extrair_campos_sucesso PASSED
tests/test_leitor.py::TestExtrairCampos::test_extrair_campos_sem_id PASSED
tests/test_leitor.py::TestExtrairCampos::test_extrair_campos_sem_nome PASSED
tests/test_leitor.py::TestLerRegistros::test_ler_registros_sucesso PASSED
tests/test_leitor.py::TestLerRegistros::test_ler_registros_arquivo_nao_encontrado PASSED
tests/test_leitor.py::TestLerRegistros::test_ler_registros_json_invalido PASSED
tests/test_banco.py::TestConectar::test_conectar_sucesso PASSED
tests/test_banco.py::TestConectar::test_conectar_falha PASSED
tests/test_banco.py::TestCriarTabela::test_criar_tabela_sucesso PASSED
tests/test_banco.py::TestInserirOrganizacoes::test_inserir_organizacoes_sucesso PASSED
tests/test_banco.py::TestInserirOrganizacoes::test_inserir_organizacoes_vazio PASSED
```

## Parar os serviços

Para parar e remover os containers:

```bash
docker compose down
```

Para remover também os volumes (dados do PostgreSQL):

```bash
docker compose down -v
```

## Estrutura do Projeto

```
mimic_fhir_ingestao/
├── leitor.py              # Módulo para leitura de NDJSON.gz
├── banco.py               # Módulo para operações com PostgreSQL
├── ingestao.py            # Script principal de ingestão
├── requirements.txt       # Dependências Python
├── Dockerfile             # Definição de imagem Docker
├── docker-compose.yml     # Orquestração de containers
├── .env.example           # Exemplo de variáveis de ambiente
├── README.md              # Este arquivo
└── tests/
    ├── test_leitor.py     # Testes do módulo leitor
    └── test_banco.py      # Testes do módulo banco
```

## Módulos

### `leitor.py`

**Funções:**
- `extrair_campos(registro)`: Extrai `id` e `name` de um registro JSON FHIR.
- `ler_registros(caminho_arquivo)`: Lê arquivo NDJSON.gz e retorna lista de registros.

### `banco.py`

**Funções:**
- `conectar(configuracao)`: Cria conexão com PostgreSQL.
- `criar_tabela(conexao)`: Cria tabela `organizacoes` se não existir.
- `inserir_organizacoes(conexao, registros)`: Insere registros (ignora duplicatas).

### `ingestao.py`

**Funções:**
- `configurar_logging(nivel)`: Configura sistema de logs.
- `obter_configuracao_banco()`: Obtém config do banco de env vars.
- `main()`: Orquestra o fluxo de leitura → ingestão.

## Logs

Os logs são enviados para stdout com o formato:

```
TIMESTAMP - MODULO - LEVEL - MENSAGEM
```

Exemplos:
- `INFO`: Registros processados, tabelas criadas, inserts bem-sucedidos
- `ERROR`: Falhas de leitura, erros de conexão, erros de parse JSON
- `WARNING`: Avisos sobre dados ausentes

O nível de log pode ser controlado pela variável de ambiente `LOG_LEVEL` (padrão: `INFO`).

## Idempotência

A ingestão é idempotente. Se você executar `docker compose up` novamente:
- A tabela já existirá (não será recriada)
- Registros duplicados serão ignorados (`ON CONFLICT ... DO NOTHING`)
- Nenhum erro será gerado

## Dados

O arquivo de entrada está em `./data/MimicOrganization.ndjson.gz`. Cada linha é um registro FHIR Organization em JSON.

Estrutura esperada:

```json
{
  "id": "ee172322-118b-5716-abbc-18e4c5437e15",
  "name": "Beth Israel Deaconess Medical Center",
  "resourceType": "Organization",
  ...
}
```

Apenas `id` e `name` são extraídos e armazenados.

## Troubleshooting

### O app trava esperando o PostgreSQL

Isso é normal. O `healthcheck` aguarda até 50 segundos (5 tentativas × 10s). Se continuar, verifique:

```bash
docker compose logs postgres
```

### Erro "arquivo não encontrado"

Certifique-se de que `MimicOrganization.ndjson.gz` existe em `./data/`:

```bash
ls -la data/
```

### Erro de conexão com PostgreSQL

Verifique as variáveis de ambiente em `.env` e confirme que os valores correspondem aos definidos em `docker-compose.yml`.

## Desenvolvedor

Desenvolvido como projeto de ingestão de dados MIMIC FHIR.
