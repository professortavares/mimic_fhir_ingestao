# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**mimic_fhir_ingestao** is a Python system that imports FHIR-formatted healthcare data from the MIMIC (Medical Information Mart for Intensive Care) database into PostgreSQL. Currently handles:
- **Organization** records: `id`, `name`
- **Location** records: `id`, `name`, FK to Organization

The entire system runs in Docker with automatic ingestion on container startup.

## Architecture

### Core Modules

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

- **Dockerfile** — Python 3.11-slim, copies code + tests (not data), runs `ingestao.py` as CMD
- **docker-compose.yml** — Defines postgres + app services
  - postgres: PostgreSQL 15, healthcheck via `pg_isready`
  - app: depends_on postgres with `condition: service_healthy`, mounts `./data` volume, reads `.env` for config
  - Data files (`*.gz`) are mounted at runtime, not copied into image (allows data updates without rebuild)

## Common Development Tasks

### Run Ingestion (Local)
```bash
source venv/bin/activate
python ingestao.py
```
Requires PostgreSQL running on localhost:5432 with credentials from `.env`

### Run Ingestion (Docker)
```bash
docker compose up --build
```
Starts both PostgreSQL and app; app exits when done. Logs appear in stdout.

### Run Tests (Local)
```bash
source venv/bin/activate
python -m pytest tests/ -v
```

### Run Tests (Docker)
```bash
docker compose run --rm app python -m pytest tests/ -v
```

### Verify Data in Database
```bash
docker compose exec postgres psql -U postgres -d mimic_fhir -c "SELECT * FROM organizacoes;"
```

### Set Up Local Development
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with PostgreSQL credentials
```

### Stop & Clean Up
```bash
docker compose down          # Stop containers, keep volumes
docker compose down -v       # Stop containers, remove volumes (data)
```

## Testing Notes

- **tests/test_leitor.py** — 13 tests covering Organization and Location extraction, file reading, error handling
  - Tests missing fields, invalid JSON, empty files, FK extraction from `managingOrganization.reference`
  - Uses temporary gzip files to simulate real NDJSON.gz
  - All critical logic tested

- **tests/test_banco.py** — 8 tests using `unittest.mock.MagicMock` to simulate psycopg2
  - No real database needed
  - Verifies SQL and connection flow for both tables, including FK constraints

**Total: 24 tests pass locally and in Docker.**

## Code Conventions

- **Language**: Portuguese (variable names, docstrings, comments, log messages)
- **Logging**: Uses Python's `logging` module; set `LOG_LEVEL` env var for level
- **Errors**: Logged but don't crash; invalid records skipped with warnings
- **Idempotency**: `ON CONFLICT ... DO NOTHING` prevents duplicate inserts
- **Dependencies**: psycopg2-binary, pytest (see requirements.txt)

## Configuration via Environment Variables

See `.env.example`:
- `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`
- `LOG_LEVEL` (default: INFO)
- `CAMINHO_ARQUIVO` (default: ./data/MimicOrganization.ndjson.gz)
- `CAMINHO_ARQUIVO_LOCATION` (default: ./data/MimicLocation.ndjson.gz)

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
