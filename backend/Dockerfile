# Imagen de la API (FastAPI). Se construye desde la carpeta backend/:
#   docker build -t eventos-api .

# --- Etapa 1: dependencias fijadas a partir de poetry.lock ---
# Se exportan a un requirements.txt con versiones exactas y hashes, asi la
# imagen tiene las mismas versiones que se testean en CI. Poetry solo vive en
# esta etapa: la imagen final no lo necesita.
FROM python:3.13-slim AS requisitos

# Misma version de Poetry que genero poetry.lock (ver su primera linea).
RUN pip install --no-cache-dir poetry==2.5.1 poetry-plugin-export==1.9.0

WORKDIR /src
COPY pyproject.toml poetry.lock ./
# Solo las dependencias de ejecucion (sin el grupo dev). Falla si
# poetry.lock quedo desactualizado respecto de pyproject.toml.
RUN poetry export --only main --format requirements.txt --output requirements.txt

# --- Etapa 2: imagen de ejecucion ---
FROM python:3.13-slim

WORKDIR /app

# Primero las dependencias (capa que se cachea mientras no cambie el lock) y
# despues el codigo. Con hashes, pip rechaza cualquier paquete que no
# coincida con el lock.
COPY --from=requisitos /src/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia el codigo de backend/ (lo que no esta excluido en .dockerignore). La
# app corre desde /app, no hace falta instalarla como paquete.
COPY . .

EXPOSE 8000

# Al iniciar: aplica las migraciones pendientes y despues levanta la API.
# --host 0.0.0.0 para que acepte conexiones desde fuera del contenedor.
# El puerto sale de PORT si el proveedor (Render, Railway) lo inyecta; si no, 8000.
# --proxy-headers: detras del proxy del PaaS y de nginx, toma la IP y el
# esquema reales de los headers X-Forwarded-*.
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --proxy-headers --forwarded-allow-ips='*'"]
