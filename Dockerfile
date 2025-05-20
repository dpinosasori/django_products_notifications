FROM python:3.12-slim

WORKDIR /app

# Instala dependencias del sistema para psycopg2 y otras librerías
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libpq-dev \
    gcc \
    python3-dev && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080
CMD ["gunicorn", "core.wsgi:application", "--bind", "8080:8080"]