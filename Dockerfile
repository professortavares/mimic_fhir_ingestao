FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY leitor.py banco.py ingestao.py ./
COPY tests/ ./tests/

CMD ["python", "ingestao.py"]
