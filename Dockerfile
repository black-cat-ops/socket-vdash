FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

RUN pip install poetry==1.8.2

COPY pyproject.toml ./

RUN poetry config virtualenvs.create false \
    && poetry install --only main --no-root

COPY collector/ ./collector/

CMD ["python", "-m", "collector.main"]
