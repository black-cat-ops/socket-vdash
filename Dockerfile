FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install UV
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

COPY pyproject.toml README.md ./

# Install only dependencies, not the package itself
RUN uv pip install --system requests psycopg2-binary python-dotenv schedule click

COPY collector/ ./collector/

CMD ["python", "-m", "collector.main"]
