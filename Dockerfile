FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml ./
COPY poetry.lock ./

RUN apt-get update && \
    apt-get install -y gcc libpq-dev curl build-essential && \
    pip install --no-cache-dir poetry==1.8.2 && \
    poetry config virtualenvs.create false && \
    poetry install --only main --no-interaction --no-ansi && \
    rm -rf ~/.cache/pypoetry/* && \
    apt-get purge -y gcc libpq-dev build-essential && \
    apt-get autoremove -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

COPY . .

ENV PYTHONUNBUFFERED=1
EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s CMD curl -f http://localhost:80/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]