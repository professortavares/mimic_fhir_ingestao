# MIMIC FHIR Ingestão

Projeto Python para importar dados do MIMIC versão FHIR a partir de arquivos NDJSON comprimidos com gzip para um banco de dados PostgreSQL.

## Propósito

Este projeto realiza a ingestão de registros FHIR do MIMIC (Medical Information Mart for Intensive Care) em um banco PostgreSQL. Atualmente, importa:
- **Organizações** (`MimicOrganization.ndjson.gz`): extraindo `id` e `name` para a tabela `organizacoes`
- **Localizações** (`MimicLocation.ndjson.gz`): extraindo `id`, `name` e FK para `organizacoes` na tabela `localizacoes`
- **Pacientes** (`MimicPatient.ndjson.gz`): extraindo `id`, `name (family)`, `gender`, `birthDate`, `race`, `identifier`, `language`, `maritalStatus` e FK para `organizacoes` na tabela `pacientes`
- **Encontros** (`MimicEncounter.ndjson.gz`): extraindo `id`, `type (display)`, `class (code)`, `period (start/end)`, `status`, `hospitalization (code)`, `dischargeDisposition (code)`, FK para `pacientes` e relacionamento com múltiplas `localizacoes` (com periods) na tabela `encontros` e `encontros_localizacoes`

## Pré-requisitos

- Docker e Docker Compose instalados

## Como Usar

### 1. Preparar o ambiente

Clone ou navegue até o diretório do projeto:

```bash
cd mimic_fhir_ingestao
```

### 2. Configurar variáveis de ambiente

Copie o arquivo `.env.example` para `.env` e configure com os valores do seu PostgreSQL externo:

```bash
cp .env.example .env
```

Edite `.env` com suas credenciais do banco:

```env
POSTGRES_HOST=seu_host
POSTGRES_PORT=5432
POSTGRES_DB=seu_banco
POSTGRES_USER=seu_usuario
POSTGRES_PASSWORD=sua_senha
LOG_LEVEL=INFO
CAMINHO_ARQUIVO=./data/MimicOrganization.ndjson.gz
CAMINHO_ARQUIVO_LOCATION=./data/MimicLocation.ndjson.gz
CAMINHO_ARQUIVO_PATIENT=./data/MimicPatient.ndjson.gz
CAMINHO_ARQUIVO_ENCOUNTER=./data/MimicEncounter.ndjson.gz
```

### 3. Executar a ingestão

Inicie a aplicação com Docker Compose:

```bash
docker compose up --build
```

O comando acima:
- Lê as configurações do arquivo `.env`
- Constrói a imagem Docker
- Executa o container da aplicação
- Realiza a ingestão no PostgreSQL externo configurado

Você verá logs como:

```
mimic_fhir_app | 2026-05-23 10:30:45,123 - ingestao - INFO - Iniciando ingestão de dados MIMIC FHIR
mimic_fhir_app | 2026-05-23 10:30:45,234 - ingestao - INFO - Lendo arquivo de organizações: ./data/MimicOrganization.ndjson.gz
mimic_fhir_app | 2026-05-23 10:30:45,456 - leitor - INFO - Registro 1 lido com sucesso: id=ee172322-118b-5716-abbc-18e4c5437e15
mimic_fhir_app | 2026-05-23 10:30:45,567 - banco - INFO - Registro inserido: id=ee172322-118b-5716-abbc-18e4c5437e15, nome=Beth Israel Deaconess Medical Center
mimic_fhir_app | 2026-05-23 10:30:45,678 - ingestao - INFO - Lendo arquivo de localizações: ./data/MimicLocation.ndjson.gz
mimic_fhir_app | 2026-05-23 10:30:45,789 - leitor - INFO - Localização 1 lida com sucesso: id=ecbf468a-22ec-5320-8e11-6ebcc918dad5
mimic_fhir_app | 2026-05-23 10:30:45,890 - ingestao - INFO - Lendo arquivo de pacientes: ./data/MimicPatient.ndjson.gz
mimic_fhir_app | 2026-05-23 10:30:46,001 - leitor - INFO - Paciente 1 lido com sucesso: id=pat-12345
mimic_fhir_app | 2026-05-23 10:30:46,012 - ingestao - INFO - Ingestão de dados MIMIC FHIR concluída com sucesso
```

### 4. Executar testes

Para rodar os testes unitários (localmente):

```bash
source venv/bin/activate
python -m pytest tests/ -v
```

Ou via Docker:

```bash
docker compose run --rm app python -m pytest tests/ -v
```

Saída esperada (60 testes ao total):

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
tests/test_leitor.py::TestExtrairCamposPatient::test_extrair_campos_patient_sucesso PASSED
tests/test_leitor.py::TestExtrairCamposPatient::test_extrair_campos_patient_sem_id PASSED
tests/test_leitor.py::TestExtrairCamposPatient::test_extrair_campos_patient_sem_gender PASSED
tests/test_leitor.py::TestExtrairCamposPatient::test_extrair_campos_patient_sem_name PASSED
tests/test_leitor.py::TestExtrairCamposPatient::test_extrair_campos_patient_name_vazio PASSED
tests/test_leitor.py::TestExtrairCamposPatient::test_extrair_campos_patient_campos_opcionais_none PASSED
tests/test_leitor.py::TestExtrairCamposPatient::test_extrair_campos_patient_extrai_uuid_org_corretamente PASSED
tests/test_leitor.py::TestLerPacientes::test_ler_pacientes_sucesso PASSED
tests/test_leitor.py::TestLerPacientes::test_ler_pacientes_arquivo_nao_encontrado PASSED
tests/test_leitor.py::TestLerPacientes::test_ler_pacientes_campos_ausentes PASSED
tests/test_leitor.py::TestExtrairCamposEncounter::test_extrair_campos_encounter_sucesso PASSED
tests/test_leitor.py::TestExtrairCamposEncounter::test_extrair_campos_encounter_sem_id PASSED
tests/test_leitor.py::TestExtrairCamposEncounter::test_extrair_campos_encounter_sem_subject PASSED
tests/test_leitor.py::TestExtrairCamposEncounter::test_extrair_campos_encounter_subject_reference_vazia PASSED
tests/test_leitor.py::TestExtrairCamposEncounter::test_extrair_campos_encounter_campos_opcionais_none PASSED
tests/test_leitor.py::TestExtrairCamposEncounter::test_extrair_campos_encounter_extrai_uuid_paciente_corretamente PASSED
tests/test_leitor.py::TestExtrairCamposEncounter::test_extrair_campos_encounter_sem_localizacoes PASSED
tests/test_leitor.py::TestLerEncontros::test_ler_encontros_sucesso PASSED
tests/test_leitor.py::TestLerEncontros::test_ler_encontros_arquivo_nao_encontrado PASSED
tests/test_leitor.py::TestLerEncontros::test_ler_encontros_campos_ausentes PASSED
tests/test_banco.py::TestConectar::test_conectar_sucesso PASSED
tests/test_banco.py::TestConectar::test_conectar_falha PASSED
tests/test_banco.py::TestCriarTabela::test_criar_tabela_sucesso PASSED
tests/test_banco.py::TestInserirOrganizacoes::test_inserir_organizacoes_sucesso PASSED
tests/test_banco.py::TestInserirOrganizacoes::test_inserir_organizacoes_vazio PASSED
tests/test_banco.py::TestCriarTabelaLocalizacoes::test_criar_tabela_localizacoes_sucesso PASSED
tests/test_banco.py::TestInserirLocalizacoes::test_inserir_localizacoes_sucesso PASSED
tests/test_banco.py::TestInserirLocalizacoes::test_inserir_localizacoes_vazio PASSED
tests/test_banco.py::TestInserirLocalizacoes::test_inserir_localizacoes_com_fk PASSED
tests/test_banco.py::TestCriarTabelaPacientes::test_criar_tabela_pacientes_sucesso PASSED
tests/test_banco.py::TestInserirPacientes::test_inserir_pacientes_sucesso PASSED
tests/test_banco.py::TestInserirPacientes::test_inserir_pacientes_vazio PASSED
tests/test_banco.py::TestInserirPacientes::test_inserir_pacientes_com_fk PASSED
tests/test_banco.py::TestCriarTabelaEncontros::test_criar_tabela_encontros_sucesso PASSED
tests/test_banco.py::TestInserirEncontros::test_inserir_encontros_sucesso PASSED
tests/test_banco.py::TestInserirEncontros::test_inserir_encontros_vazio PASSED
tests/test_banco.py::TestInserirEncontros::test_inserir_encontros_com_fk PASSED
tests/test_banco.py::TestCriarTabelaEncontrosLocalizacoes::test_criar_tabela_encontros_localizacoes_sucesso PASSED
tests/test_banco.py::TestInserirEncontrosLocalizacoes::test_inserir_encontros_localizacoes_sucesso PASSED
tests/test_banco.py::TestInserirEncontrosLocalizacoes::test_inserir_encontros_localizacoes_vazio PASSED
tests/test_banco.py::TestInserirEncontrosLocalizacoes::test_inserir_encontros_localizacoes_sem_locations PASSED
tests/test_banco.py::TestInserirEncontrosLocalizacoes::test_inserir_encontros_localizacoes_com_fks PASSED
```

## Parar o serviço

Para parar e remover o container:

```bash
docker compose down
```

## Estrutura do Projeto

```
mimic_fhir_ingestao/
├── src/                   # Módulos Python da aplicação
│   ├── leitor.py          # Módulo para leitura de NDJSON.gz
│   ├── banco.py           # Módulo para operações com PostgreSQL
│   └── ingestao.py        # Script principal de ingestão
├── tests/                 # Testes da aplicação
│   ├── test_leitor.py     # Testes do módulo leitor
│   └── test_banco.py      # Testes do módulo banco
├── conftest.py            # Configuração de testes (adiciona src ao path)
├── entry_point.sh         # Script de entrada do container
├── requirements.txt       # Dependências Python
├── Dockerfile             # Definição de imagem Docker
├── docker-compose.yml     # Orquestração de containers
├── .env.example           # Exemplo de variáveis de ambiente
└── README.md              # Este arquivo
```

## Módulos

### `leitor.py`

**Funções:**
- `extrair_campos(registro)`: Extrai `id` e `name` de um registro FHIR Organization.
- `ler_registros(caminho_arquivo)`: Lê arquivo NDJSON.gz de organizações e retorna lista de registros.
- `extrair_campos_location(registro)`: Extrai `id`, `name` e `organizacao_id` (FK) de um registro FHIR Location.
- `ler_localizacoes(caminho_arquivo)`: Lê arquivo NDJSON.gz de localizações e retorna lista de registros.
- `extrair_campos_patient(registro)`: Extrai `id`, `nome_familia`, `genero`, `data_nascimento`, `raca`, `identificador`, `idioma`, `estado_civil` e `organizacao_id` (FK) de um registro FHIR Patient.
- `ler_pacientes(caminho_arquivo)`: Lê arquivo NDJSON.gz de pacientes e retorna lista de registros.
- `extrair_campos_encounter(registro)`: Extrai `id`, `tipo`, `classe`, `periodo_inicio`, `periodo_fim`, `status`, `hospitalizacao_code`, `alta_code`, `paciente_id` (FK) e `localizacoes` (lista com IDs e períodos) de um registro FHIR Encounter.
- `ler_encontros(caminho_arquivo)`: Lê arquivo NDJSON.gz de encontros e retorna lista de registros.

### `banco.py`

**Funções:**
- `conectar(configuracao)`: Cria conexão com PostgreSQL.
- `criar_tabela(conexao)`: Cria tabela `organizacoes` se não existir.
- `inserir_organizacoes(conexao, registros)`: Insere registros de organizações (ignora duplicatas).
- `criar_tabela_localizacoes(conexao)`: Cria tabela `localizacoes` com FK para `organizacoes`.
- `inserir_localizacoes(conexao, registros)`: Insere registros de localizações (ignora duplicatas).
- `criar_tabela_pacientes(conexao)`: Cria tabela `pacientes` com FK para `organizacoes`.
- `inserir_pacientes(conexao, registros)`: Insere registros de pacientes (ignora duplicatas).
- `criar_tabela_encontros(conexao)`: Cria tabela `encontros` com FK para `pacientes`.
- `inserir_encontros(conexao, registros)`: Insere registros de encontros (ignora duplicatas).
- `criar_tabela_encontros_localizacoes(conexao)`: Cria tabela `encontros_localizacoes` (junção com períodos) com FK para `encontros` e `localizacoes`.
- `inserir_encontros_localizacoes(conexao, encontros_com_localizacoes)`: Insere relacionamentos encontro-localização (ignora duplicatas).

### `ingestao.py`

**Funções:**
- `configurar_logging(nivel)`: Configura sistema de logs.
- `obter_configuracao_banco()`: Obtém config do banco de variáveis de ambiente.
- `main()`: Orquestra o fluxo completo:
  1. Conecta ao banco de dados
  2. Cria tabelas (organizacoes, localizacoes, pacientes, encontros e encontros_localizacoes)
  3. Lê e insere organizações
  4. Lê e insere localizações
  5. Lê e insere pacientes
  6. Lê e insere encontros
  7. Lê e insere relacionamentos encontro-localização

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

### `MimicPatient.ndjson.gz`
Cada linha é um registro FHIR Patient em JSON.

Estrutura esperada:

```json
{
  "id": "pat-12345",
  "gender": "male",
  "name": [
    {
      "family": "Silva"
    }
  ],
  "birthDate": "1980-01-01",
  "resourceType": "Patient",
  "managingOrganization": {
    "reference": "Organization/ee172322-118b-5716-abbc-18e4c5437e15"
  },
  "identifier": [
    {
      "value": "ID123"
    }
  ],
  "extension": [
    {
      "url": "http://example.com/race",
      "valueCodeableConcept": {
        "coding": [
          {
            "display": "White"
          }
        ]
      }
    }
  ],
  "communication": [
    {
      "language": {
        "coding": [
          {
            "code": "en"
          }
        ]
      }
    }
  ],
  "maritalStatus": {
    "coding": [
      {
        "code": "M"
      }
    ]
  },
  ...
}
```

Campos extraídos: `id`, `name[0].family`, `gender`, `birthDate`, `race` (de `extension[*].valueCodeableConcept.coding[0].display`), `identifier[0].value`, `language[0].language.coding[0].code`, `maritalStatus.coding[0].code`, e `organizacao_id` (extraído de `managingOrganization.reference`)

### `MimicEncounter.ndjson.gz`
Cada linha é um registro FHIR Encounter em JSON.

Estrutura esperada:

```json
{
  "id": "enc-12345",
  "subject": {
    "reference": "Patient/pat-12345"
  },
  "type": [
    {
      "coding": [
        {
          "display": "Hospitalization"
        }
      ]
    }
  ],
  "class": {
    "code": "IMP"
  },
  "period": {
    "start": "2020-01-01T10:00:00Z",
    "end": "2020-01-05T14:00:00Z"
  },
  "status": "finished",
  "hospitalization": {
    "coding": [
      {
        "code": "hosp-code"
      }
    ]
  },
  "dischargeDisposition": {
    "coding": [
      {
        "code": "discharge-code"
      }
    ]
  },
  "location": [
    {
      "location": {
        "reference": "Location/loc-1"
      },
      "period": {
        "start": "2020-01-01T10:00:00Z",
        "end": "2020-01-03T14:00:00Z"
      }
    },
    {
      "location": {
        "reference": "Location/loc-2"
      },
      "period": {
        "start": "2020-01-03T15:00:00Z",
        "end": "2020-01-05T14:00:00Z"
      }
    }
  ],
  "resourceType": "Encounter",
  ...
}
```

Campos extraídos: `id`, `paciente_id` (extraído de `subject.reference`), `tipo` (extraído de `type[0].coding[0].display`), `classe` (extraído de `class.code`), `periodo_inicio` e `periodo_fim` (extraídos de `period.start` e `period.end`), `status`, `hospitalizacao_code` (extraído de `hospitalization.coding[0].code`), `alta_code` (extraído de `dischargeDisposition.coding[0].code`), e múltiplos relacionamentos com localizações (com períodos próprios)

## Troubleshooting

### Erro "arquivo não encontrado"

Certifique-se de que os arquivos existem em `./data/`:

```bash
ls -la data/
```

Você deve ver:
- `MimicOrganization.ndjson.gz`
- `MimicLocation.ndjson.gz`
- `MimicPatient.ndjson.gz`
- `MimicEncounter.ndjson.gz`

Note: os arquivos `.gz` são ignorados pelo git (`.gitignore`) e precisam estar presentes localmente para o docker-compose montar o volume.

### Erro de conexão com PostgreSQL

Verifique o arquivo `.env` e confirme que as variáveis de conexão apontam para um PostgreSQL válido:
- `POSTGRES_HOST`: IP ou hostname do servidor PostgreSQL
- `POSTGRES_PORT`: Porta (padrão 5432)
- `POSTGRES_DB`: Nome do banco de dados
- `POSTGRES_USER`: Usuário de acesso
- `POSTGRES_PASSWORD`: Senha de acesso

### Como debugar

Para ver os logs da aplicação:

```bash
docker compose logs app
```

## Desenvolvedor

Desenvolvido como projeto de ingestão de dados MIMIC FHIR.
