# Imagen de la API (FastAPI). Se construye desde la carpeta backend/:
#   docker build -t eventos-api .
FROM python:3.13-slim

WORKDIR /app

# Copia el codigo de backend/ (lo que no esta excluido en .dockerignore).
COPY . .

# Instala solo las dependencias de ejecucion (project.dependencies), sin el
# grupo dev. Dentro del contenedor no hace falta Poetry ni un entorno virtual:
# el contenedor ya es un entorno aislado.
RUN pip install --no-cache-dir .

EXPOSE 8000

# Al iniciar: aplica las migraciones pendientes y despues levanta la API.
# --host 0.0.0.0 para que acepte conexiones desde fuera del contenedor.
# El puerto sale de PORT si el proveedor (Render, Railway) lo inyecta; si no, 8000.
# --proxy-headers: detras del proxy del PaaS y de nginx, toma la IP y el
# esquema reales de los headers X-Forwarded-*.
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --proxy-headers --forwarded-allow-ips='*'"]
