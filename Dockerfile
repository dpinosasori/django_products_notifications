# Stage 1: Build
FROM python:3.12-slim as builder

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libpq-dev gcc python3-dev libjpeg-dev zlib1g-dev && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --user -r requirements.txt

# Stage 2: Runtime
FROM python:3.12-slim

WORKDIR /app

# Copia solo lo necesario desde el builder
COPY --from=builder /root/.local /root/.local
COPY . .

# Asegura que los scripts estén en PATH
ENV PATH=/root/.local/bin:$PATH

# Pre-compila bytecode de Python para optimizar inicio
RUN python -m compileall .

# Usa un usuario no-root para seguridad
RUN useradd -m appuser && chown -R appuser /app
USER appuser

EXPOSE 8080

CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "4", "--threads", "2", "core.wsgi"]