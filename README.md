# MIMIC FHIR Ingestão

Projeto Python para importar dados do MIMIC versão FHIR a partir de arquivos NDJSON comprimidos com gzip para um banco de dados PostgreSQL.

## Propósito

Este projeto realiza a ingestão de registros FHIR do MIMIC (Medical Information Mart for Intensive Care) em um banco PostgreSQL. Atualmente, importa:
- **Organizações** (`MimicOrganization.ndjson.gz`): extraindo `id` e `name` para a tabela `organizacoes`
- **Localizações** (`MimicLocation.ndjson.gz`): extraindo `id`, `name` e FK para `organizacoes` na tabela `localizacoes`

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
CAMINHO_ARQUIVO_LOCATION=./data/MimicLocation.ndjson.gz
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
mimic_fhir_app | 2026-05-23 10:30:45,234 - ingestao - INFO - Lendo arquivo de organizações: ./data/MimicOrganization.ndjson.gz
mimic_fhir_app | 2026-05-23 10:30:45,456 - leitor - INFO - Registro 1 lido com sucesso: id=ee172322-118b-5716-abbc-18e4c5437e15
mimic_fhir_app | 2026-05-23 10:30:45,567 - banco - INFO - Registro inserido: id=ee172322-118b-5716-abbc-18e4c5437e15, nome=Beth Israel Deaconess Medical Center
mimic_fhir_app | 2026-05-23 10:30:45,678 - ingestao - INFO - Lendo arquivo de localizações: ./data/MimicLocation.ndjson.gz
mimic_fhir_app | 2026-05-23 10:30:45,789 - leitor - INFO - Localização 1 lida com sucesso: id=ecbf468a-22ec-5320-8e11-6ebcc918dad5
mimic_fhir_app | 2026-05-23 10:30:46,012 - ingestao - INFO - Ingestão de dados MIMIC FHIR concluída com sucesso
```

### 4. Verificar dados importados

Em outro terminal, execute para verificar organizações:

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

Para verificar localizações:

```bash
docker compose exec postgres psql -U postgres -d mimic_fhir -c "SELECT COUNT(*) FROM localizacoes;"
```

Resultado esperado:

```
 count
-------
    31
(1 row)
```

Para ver a relação entre localizações e organizações:

```bash
docker compose exec postgres psql -U postgres -d mimic_fhir -c "SELECT l.nome, o.nome FROM localizacoes l JOIN organizacoes o ON l.organizacao_id = o.id LIMIT 3;"
```

Resultado esperado:

```
                        nome                        |                    nome
----------------------------------------------------+---------------------------------------------
 Cardiology Surgery Intermediate                    | Beth Israel Deaconess Medical Center
 Emergency Department                               | Beth Israel Deaconess Medical Center
 Intensive Care Unit                                | Beth Israel Deaconess Medical Center
(3 rows)
```

### 5. Executar testes

Para rodar os testes unitários:

```bash
docker compose run --rm app python -m pytest tests/ -v
```

Saída esperada (24 testes ao total):

```
tests/test_leitor.py::TestExtrairCampos::test_extrair_campos_sucesso PASSED
tests/test_leitor.py::TestExtrairCampos::test_extrair_campos_sem_id PASSED
tests/test_leitor.py::TestExtrairCampos::test_extrair_campos_sem_nome PASSED
tests/test_leitor.py::TestExtrairCampos::test_extrair_campos_campos_extras PASSED
tests/test_leitor.py::TestLerRegistros::test_ler_registros_sucesso PASSED
tests/test_leitor.py::TestLerRegistros::test_ler_registros_arquivo_nao_encontrado PASSED
tests/test_leitor.py::TestLerRegistros::test_ler_registros_json_invalido PASSED
tests/test_leitor.py::TestLerRegistros::test_ler_registros_campos_ausentes PASSED
tests/test_leitor.py::TestLerRegistros::test_ler_registros_arquivo_vazio PASSED
tests/test_leitor.py::TestExtrairCamposLocation::test_extrair_campos_location_sucesso PASSED
tests/test_leitor.py::TestExtrairCamposLocation::test_extrair_campos_location_sem_managing_org PASSED
tests/test_leitor.py::TestExtrairCamposLocation::test_extrair_campos_location_sem_id PASSED
tests/test_leitor.py::TestExtrairCamposLocation::test_extrair_campos_location_sem_nome PASSED
tests/test_leitor.py::TestExtrairCamposLocation::test_extrair_campos_location_reference_invalida PASSED
tests/test_leitor.py::TestExtrairCamposLocation::test_extrair_campos_location_extrai_uuid_corretamente PASSED
tests/test_leitor.py::TestLerLocalizacoes::test_ler_localizacoes_sucesso PASSED
tests/test_leitor.py::TestLerLocalizacoes::test_ler_localizacoes_arquivo_nao_encontrado PASSED
tests/test_leitor.py::TestLerLocalizacoes::test_ler_localizacoes_campos_ausentes PASSED
tests/test_banco.py::TestConectar::test_conectar_sucesso PASSED
tests/test_banco.py::TestConectar::test_conectar_falha PASSED
tests/test_banco.py::TestCriarTabela::test_criar_tabela_sucesso PASSED
tests/test_banco.py::TestInserirOrganizacoes::test_inserir_organizacoes_sucesso PASSED
tests/test_banco.py::TestInserirOrganizacoes::test_inserir_organizacoes_vazio PASSED
tests/test_banco.py::TestCriarTabelaLocalizacoes::test_criar_tabela_localizacoes_sucesso PASSED
tests/test_banco.py::TestInserirLocalizacoes::test_inserir_localizacoes_sucesso PASSED
tests/test_banco.py::TestInserirLocalizacoes::test_inserir_localizacoes_vazio PASSED
tests/test_banco.py::TestInserirLocalizacoes::test_inserir_localizacoes_com_fk PASSED
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
- `extrair_campos(registro)`: Extrai `id` e `name` de um registro FHIR Organization.
- `ler_registros(caminho_arquivo)`: Lê arquivo NDJSON.gz de organizações e retorna lista de registros.
- `extrair_campos_location(registro)`: Extrai `id`, `name` e `organizacao_id` (FK) de um registro FHIR Location.
- `ler_localizacoes(caminho_arquivo)`: Lê arquivo NDJSON.gz de localizações e retorna lista de registros.

### `banco.py`

**Funções:**
- `conectar(configuracao)`: Cria conexão com PostgreSQL.
- `criar_tabela(conexao)`: Cria tabela `organizacoes` se não existir.
- `inserir_organizacoes(conexao, registros)`: Insere registros de organizações (ignora duplicatas).
- `criar_tabela_localizacoes(conexao)`: Cria tabela `localizacoes` com FK para `organizacoes`.
- `inserir_localizacoes(conexao, registros)`: Insere registros de localizações (ignora duplicatas).

### `ingestao.py`

**Funções:**
- `configurar_logging(nivel)`: Configura sistema de logs.
- `obter_configuracao_banco()`: Obtém config do banco de variáveis de ambiente.
- `main()`: Orquestra o fluxo completo:
  1. Conecta ao banco de dados
  2. Cria tabelas (organizacoes e localizacoes)
  3. Lê e insere organizações
  4. Lê e insere localizações

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

Os arquivos de entrada estão em `./data/`:

### `MimicOrganization.ndjson.gz`
Cada linha é um registro FHIR Organization em JSON.

Estrutura esperada:

```json
{
  "id": "ee172322-118b-5716-abbc-18e4c5437e15",
  "name": "Beth Israel Deaconess Medical Center",
  "resourceType": "Organization",
  ...
}
```

Campos extraídos: `id`, `name`

### `MimicLocation.ndjson.gz`
Cada linha é um registro FHIR Location em JSON.

Estrutura esperada:

```json
{
  "id": "ecbf468a-22ec-5320-8e11-6ebcc918dad5",
  "name": "Cardiology Surgery Intermediate",
  "resourceType": "Location",
  "managingOrganization": {
    "reference": "Organization/ee172322-118b-5716-abbc-18e4c5437e15"
  },
  ...
}
```

Campos extraídos: `id`, `name`, e `organizacao_id` (extraído de `managingOrganization.reference`)

## Troubleshooting

### O app trava esperando o PostgreSQL

Isso é normal. O `healthcheck` aguarda até 50 segundos (5 tentativas × 10s). Se continuar, verifique:

```bash
docker compose logs postgres
```

### Erro "arquivo não encontrado"

Certifique-se de que ambos os arquivos existem em `./data/`:

```bash
ls -la data/
```

Você deve ver:
- `MimicOrganization.ndjson.gz`
- `MimicLocation.ndjson.gz`

Note: os arquivos `.gz` são ignorados pelo git (`.gitignore`) e precisam estar presentes localmente para o docker-compose montar o volume.

### Erro de conexão com PostgreSQL

Verifique as variáveis de ambiente em `.env` e confirme que os valores correspondem aos definidos em `docker-compose.yml`.

## Desenvolvedor

Desenvolvido como projeto de ingestão de dados MIMIC FHIR.
