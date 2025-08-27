FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# App code
COPY app /app/app
COPY config /app/config

ENV PYTHONUNBUFFERED=1 \
    ANTHROPIC_MODEL=claude-3-5-sonnet-latest \
    MCP_CONFIG_PATH=/app/config/mcp.json

EXPOSE 8000

CMD ["python", "-m", "app.api.main"]
