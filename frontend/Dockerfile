# Imagen del frontend: build de Vite servido por nginx, que ademas hace de proxy
# de /api hacia la API (mismo origen para la cookie del refresh token).
# Se construye desde la carpeta frontend/:
#   docker build -t eventos-web .

# --- Etapa 1: build de produccion (frontend/dist) ---
FROM node:22-alpine AS build

WORKDIR /app

# Primero solo los manifiestos, asi la capa de dependencias se cachea mientras
# no cambien.
COPY package.json package-lock.json ./
RUN npm ci

COPY . .
# Sin VITE_API_URL: el cliente usa el default '/api', que resuelve nginx.
RUN npm run build

# --- Etapa 2: servidor estatico + proxy ---
FROM nginx:1.27-alpine

COPY --from=build /app/dist /usr/share/nginx/html

# La imagen oficial de nginx procesa /etc/nginx/templates/*.template con
# envsubst al arrancar y deja el resultado en /etc/nginx/conf.d/. Solo
# reemplaza variables de entorno definidas, asi que las de nginx ($uri,
# $host, ...) quedan intactas.
COPY nginx/default.conf.template /etc/nginx/templates/default.conf.template

# Valores por defecto. En el PaaS, PORT lo inyecta el proveedor (Render,
# Railway) y API_UPSTREAM se define con la URL de la API, sin barra final.
ENV PORT=8080
ENV API_UPSTREAM=http://api:8000

EXPOSE 8080
