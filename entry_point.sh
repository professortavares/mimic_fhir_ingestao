#!/bin/bash
set -e

# Carrega .env local se existir (útil para execução fora do Docker)
if [ -f .env ]; then
    set -a
    source .env
    set +a
fi

exec python src/ingestao.py
