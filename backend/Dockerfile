FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# 仅装 libpq（psycopg2 需要）+ curl（healthcheck）
RUN apt-get update && \
    apt-get install -y --no-install-recommends libpq5 curl && \
    rm -rf /var/lib/apt/lists/*

# 先装依赖（利用 docker 缓存）
COPY pyproject.toml ./
RUN pip install --upgrade pip && \
    pip install .

# 再拷代码
COPY app ./app

EXPOSE 8082

HEALTHCHECK --interval=10s --timeout=3s --retries=10 \
  CMD curl -fsS http://localhost:8082/api/healthz || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8082"]