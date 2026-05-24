# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**mimic_fhir_ingestao** is a Python system that imports FHIR-formatted healthcare data from the MIMIC (Medical Information Mart for Intensive Care) database into PostgreSQL. Currently handles Organization records, extracting `id` and `name` fields from NDJSON.gz files.

The entire system runs in Docker with automatic ingestion on container startup.

## Architecture

### Core Modules

- **leitor.py** — Reads NDJSON.gz files and extracts FHIR Organization records
  - `extrair_campos(registro)` — Validates and extracts `id` and `name` from a JSON object
  - `ler_registros(caminho_arquivo)` — Streams file, yields valid records, logs invalid ones as warnings
  - Robust: skips malformed JSON and missing fields instead of crashing

- **banco.py** — Handles PostgreSQL connections and operations
  - `conectar(configuracao)` — Creates psycopg2 connection from env config dict
  - `criar_tabela(conexao)` — Creates `organizacoes` table if needed (idempotent)
  - `inserir_organizacoes(conexao, registros)` — Bulk inserts with `ON CONFLICT ... DO NOTHING`
  - All operations logged at INFO level

- **ingestao.py** — Main entry point and orchestrator
  - Reads env vars (`POSTGRES_*`, `LOG_LEVEL`, `CAMINHO_ARQUIVO`)
  - Calls leitor → banco functions in sequence
  - Configures Python logging with timestamp + module + level format
  - Exits with code 0 on success, 1 on error

### Data Flow

```
NDJSON.gz → leitor.ler_registros() → dict[id, nome]
                                      ↓
                                   banco.criar_tabela()
                                   banco.inserir_organizacoes()
                                      ↓
                                   PostgreSQL
```

### Containerization

- **Dockerfile** — Python 3.11-slim, copies code + data, runs `ingestao.py` as CMD
- **docker-compose.yml** — Defines postgres + app services
  - postgres: PostgreSQL 15, healthcheck via `pg_isready`
  - app: depends_on postgres with `condition: service_healthy`, reads `.env` for config

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

- **tests/test_leitor.py** — 9 tests covering extraction, file reading, error handling
  - Uses temporary files with gzip to simulate real NDJSON.gz
  - Tests missing fields, invalid JSON, empty files
  - All critical logic tested

- **tests/test_banco.py** — 5 tests using `unittest.mock.MagicMock` to simulate psycopg2
  - No real database needed
  - Verifies SQL and connection flow

**All 14 tests pass locally and in Docker.**

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

## Key Constraints & Patterns

1. **Idempotent Ingestion** — Safe to run multiple times; duplicates ignored by CONFLICT clause
2. **Lazy Error Handling** — Invalid records (missing id/name) logged as warnings, doesn't stop processing
3. **Logging as Observability** — No silent failures; all INFO events logged with timestamp/module
4. **Mock Testing** — DB tests use mocks to avoid needing PostgreSQL; only integration tests (if added) would use real DB
5. **Single Responsibility** — leitor handles file I/O, banco handles DB, ingestao orchestrates

## Future Extensions

When adding support for new FHIR resource types:
1. Add extraction logic to leitor (new function or conditional in `extrair_campos`)
2. Add table schema to banco (new `criar_tabela_*` function)
3. Add tests for new extraction + insertion paths
4. Update docker-compose and .env.example if new env vars needed
5. Document in README.md

Current code is minimalist and easily extended for additional Organization fields or new resource types.
