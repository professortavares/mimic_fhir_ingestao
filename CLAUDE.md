# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**mimic_fhir_ingestao** is a Python system that imports FHIR-formatted healthcare data from the MIMIC (Medical Information Mart for Intensive Care) database into PostgreSQL. Currently handles:
- **Organization** records: `id`, `name`
- **Location** records: `id`, `name`, FK to Organization

The entire system runs in Docker with automatic ingestion on container startup.

## Architecture

### Project Structure

```
src/                      # Application modules
├── leitor.py              # File reading and FHIR field extraction
├── banco.py               # PostgreSQL operations
└── ingestao.py            # Main orchestrator

conftest.py               # pytest configuration (adds src/ to path)
entry_point.sh            # Docker container entry point
tests/                    # Test suite (unchanged imports due to conftest.py)
```

### Core Modules (in `src/`)

- **leitor.py** — Reads NDJSON.gz files and extracts FHIR records
  - `extrair_campos(registro)` — Validates and extracts `id`, `name` from Organization
  - `ler_registros(caminho_arquivo)` — Streams Organization file, skips invalid records with warnings
  - `extrair_campos_location(registro)` — Validates and extracts `id`, `name`, `organizacao_id` (FK) from Location
  - `ler_localizacoes(caminho_arquivo)` — Streams Location file, skips invalid records with warnings
  - Robust: handles malformed JSON, missing fields, invalid FK references

- **banco.py** — Handles PostgreSQL connections and operations
  - `conectar(configuracao)` — Creates psycopg2 connection from env config dict
  - `criar_tabela(conexao)` — Creates `organizacoes` table (idempotent)
  - `inserir_organizacoes(conexao, registros)` — Bulk inserts with `ON CONFLICT ... DO NOTHING`
  - `criar_tabela_localizacoes(conexao)` — Creates `localizacoes` table with FK constraint to `organizacoes`
  - `inserir_localizacoes(conexao, registros)` — Bulk inserts with FK validation and `ON CONFLICT ... DO NOTHING`
  - All operations logged at INFO level

- **ingestao.py** — Main entry point and orchestrator
  - Reads env vars (`POSTGRES_*`, `LOG_LEVEL`, `CAMINHO_ARQUIVO`, `CAMINHO_ARQUIVO_LOCATION`)
  - Orchestrates: connect → create tables (organization first, then location) → insert both types
  - Configures Python logging with timestamp + module + level format
  - Exits with code 0 on success, 1 on error

### Data Flow

```
MimicOrganization.ndjson.gz → leitor.ler_registros() → dict[id, nome]
                                                         ↓
                                    banco.criar_tabela()
                                    banco.inserir_organizacoes()
                                         ↓
                                     PostgreSQL organizacoes

MimicLocation.ndjson.gz → leitor.ler_localizacoes() → dict[id, nome, organizacao_id]
                                                       ↓
                                      banco.criar_tabela_localizacoes()
                                      banco.inserir_localizacoes()
                                           ↓
                                     PostgreSQL localizacoes (FK → organizacoes)
```

### Containerization

- **Dockerfile** — Python 3.11-slim, copies `src/`, `tests/`, `conftest.py`, `entry_point.sh`
  - Sets `PYTHONPATH=/app/src` so modules can be imported directly
  - Runs `entry_point.sh` as CMD (bash script that loads `.env` and calls `python src/ingestao.py`)
  - Does NOT copy `data/` (files are mounted at runtime)

- **docker-compose.yml** — Simplified to just the app service
  - No postgres service (uses external PostgreSQL configured via `.env`)
  - Mounts `./data:/app/data` for input files
  - Uses `env_file: .env` to load configuration

- **entry_point.sh** — Bash script entry point
  - Loads `.env` if present (useful for local execution outside Docker)
  - Calls `python src/ingestao.py`

## Common Development Tasks

### Run Ingestion (Local)
```bash
source venv/bin/activate
./entry_point.sh
```
Requires PostgreSQL running with credentials from `.env` and data files in `./data/`

### Run Ingestion (Docker)
```bash
docker compose up --build
```
Builds image, starts container, runs ingestion, exits. App connects to PostgreSQL configured in `.env`.

### Run Tests (Local)
```bash
source venv/bin/activate
python -m pytest tests/ -v
```
Uses `conftest.py` to add `src/` to path; no manual PYTHONPATH needed.

### Run Tests (Docker)
```bash
docker compose run --rm app python -m pytest tests/ -v
```

### Set Up Local Development
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your PostgreSQL credentials
```

### Stop Container
```bash
docker compose down
```

## Testing Notes

- **tests/test_leitor.py** — 14 tests covering Organization and Location extraction
  - Uses `conftest.py` to ensure `from leitor import ...` works without manual path setup
  - Tests missing fields, invalid JSON, empty files, FK extraction from `managingOrganization.reference`
  - Uses temporary gzip files to simulate real NDJSON.gz

- **tests/test_banco.py** — 13 tests using `unittest.mock.MagicMock` to simulate psycopg2
  - Uses `conftest.py` to ensure `from banco import ...` works
  - No real database needed; verifies SQL and connection flow for both tables

**Total: 27 tests pass locally and in Docker.**

### conftest.py
- Automatically executed by pytest
- Adds `src/` to `sys.path` so test imports (`from leitor import ...`) work without modification
- Essential for development flow where modules moved to `src/` but tests stay in `tests/`

## Code Conventions

- **Language**: Portuguese (variable names, docstrings, comments, log messages)
- **Logging**: Uses Python's `logging` module; set `LOG_LEVEL` env var for level
- **Errors**: Logged but don't crash; invalid records skipped with warnings
- **Idempotency**: `ON CONFLICT ... DO NOTHING` prevents duplicate inserts
- **Dependencies**: psycopg2-binary, pytest (see requirements.txt)

## Configuration via Environment Variables

See `.env.example` (values are placeholders; replace with your PostgreSQL connection details):
- `POSTGRES_HOST` — PostgreSQL server address
- `POSTGRES_PORT` — PostgreSQL port (default 5432)
- `POSTGRES_DB` — Database name
- `POSTGRES_USER` — Database user
- `POSTGRES_PASSWORD` — Database password
- `LOG_LEVEL` — Log level (default: INFO)
- `CAMINHO_ARQUIVO` — Path to MimicOrganization file (default: ./data/MimicOrganization.ndjson.gz)
- `CAMINHO_ARQUIVO_LOCATION` — Path to MimicLocation file (default: ./data/MimicLocation.ndjson.gz)

### Docker Execution
- docker-compose uses `env_file: .env` to load variables
- entry_point.sh loads `.env` before running `python src/ingestao.py`

## Key Constraints & Patterns

1. **Idempotent Ingestion** — Safe to run multiple times; duplicates ignored by CONFLICT clause
2. **Lazy Error Handling** — Invalid records (missing id/name) logged as warnings, doesn't stop processing
3. **Logging as Observability** — No silent failures; all INFO events logged with timestamp/module
4. **Mock Testing** — DB tests use mocks to avoid needing PostgreSQL; only integration tests (if added) would use real DB
5. **Single Responsibility** — leitor handles file I/O, banco handles DB, ingestao orchestrates

## Future Extensions

When adding support for new FHIR resource types (e.g., Patient, Encounter):
1. Add extraction logic to leitor (new function: `extrair_campos_<tipo>` + `ler_<tipo>s`)
2. Add table schema to banco (new function: `criar_tabela_<tipo>s`)
3. Add insertion function to banco (new function: `inserir_<tipo>s`)
4. Add tests (TestExtrairCampos<Tipo>, TestLer<Tipo>s, TestInserir<Tipo>s)
5. Update ingestao.py `main()` to call new reader and inserter
6. Update docker-compose.yml and .env.example for new env vars
7. Document in README.md

Pattern to follow (demonstrated by Organization → Location):
- Keep functions generic and stateless
- Use `ON CONFLICT ... DO NOTHING` for idempotency
- Log every significant operation
- Separate concerns: leitor (I/O + parsing), banco (DB ops), ingestao (orchestration)
