FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY tests/ ./tests/
COPY conftest.py entry_point.sh ./
RUN chmod +x entry_point.sh

ENV PYTHONPATH=/app/src

CMD ["./entry_point.sh"]
