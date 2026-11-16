# Modelo de datos

Esquema relacional de la base (PostgreSQL), tal como lo dejan las migraciones `0001_auth_tables`
a `0005_administradores_id_default`. Las tablas y columnas salen de los modelos SQLAlchemy de
`backend/app/**/models.py`.

## Diagrama entidad-relación

```mermaid
erDiagram
    usuario ||--o{ refresh_token : "tiene"
    usuario ||--o{ password_reset_token : "tiene"
    usuario ||--o| organizadores : "perfil de organizador"
    usuario ||--o| administradores : "rol de administrador"
    organizadores |o--o{ eventos : "publica"
    lugar ||--o{ eventos : "ocurre en"
    eventos ||--o{ evento_categoria : "se clasifica en"
    categoria_evento ||--o{ evento_categoria : "clasifica"

    usuario {
        uuid id_usuario PK
        varchar(255) nombre
        varchar(255) apellido
        varchar(255) email UK "indexado"
        varchar(255) password_hash "nullable: login social"
        timestamptz fecha_creacion
        boolean activo
    }

    refresh_token {
        uuid id PK
        uuid usuario_id FK "indexado"
        varchar(64) token_hash UK "SHA-256 del token"
        timestamptz expires_at
        timestamptz revoked_at "nullable"
        timestamptz creado_en
    }

    password_reset_token {
        uuid id PK
        uuid usuario_id FK "indexado"
        varchar(64) token_hash UK "SHA-256 del token"
        timestamptz expires_at
        timestamptz used_at "nullable"
        timestamptz creado_en
    }

    audit_log {
        uuid id PK
        varchar(64) event_type "indexado"
        varchar(255) email "nullable, indexado"
        varchar(500) detalle
        timestamptz ocurrido_en
    }

    organizadores {
        uuid id_organizador PK
        uuid id_usuario FK, UK "ON DELETE CASCADE"
        varchar(255) nombre_publico
        text descripcion
        estado_organizador estado
        timestamptz fecha_creacion
    }

    administradores {
        uuid id_admin PK "DEFAULT gen_random_uuid()"
        uuid id_usuario FK, UK "ON DELETE CASCADE"
        timestamptz fecha_alta
    }

    lugar {
        uuid id_lugar PK
        varchar(255) nombre "nullable"
        varchar(255) direccion "nullable"
        float latitud "indice (latitud, longitud)"
        float longitud
    }

    eventos {
        uuid id_evento PK
        uuid id_organizador FK "nullable: eventos de seed"
        uuid id_lugar FK "indexado"
        varchar(255) titulo
        text descripcion
        timestamptz fecha_inicio "UTC"
        timestamptz fecha_fin "nullable"
        time hora_inicio_local "derivado de fecha_inicio"
        numeric precio "(10, 2), nullable"
        estado_evento estado "indice (estado, fecha_inicio)"
        origen_evento origen
        timestamptz fecha_publicacion "nullable"
        timestamptz fecha_actualizacion
    }

    evento_categoria {
        uuid id_evento PK, FK "ON DELETE CASCADE"
        int id_categoria PK, FK
    }

    categoria_evento {
        int id_categoria PK
        varchar(50) slug UK
        varchar(100) nombre
        text descripcion "nullable"
        boolean activa
    }
```

`audit_log` no tiene claves foráneas: guarda el email como texto, así que también puede registrar
intentos de login con emails que no existen. Es infraestructura de seguridad (RNF-04), no parte
del dominio, y la escribe `AuditLogObserver`.

## Tipos enumerados

| Tipo (PostgreSQL) | Valores | Usado en |
|---|---|---|
| `estado_organizador` | `PENDIENTE`, `APROBADO`, `RECHAZADO`, `SUSPENDIDO` | `organizadores.estado` |
| `estado_evento` | `BORRADOR`, `PUBLICADO`, `CANCELADO`, `OCULTO` | `eventos.estado` |
| `origen_evento` | `CARGA_ORGANIZADOR`, `SEED_EQUIPO` | `eventos.origen` |

## Máquinas de estado

Las transiciones se validan en los métodos de las entidades (`Organizador.aprobar()`,
`Evento.ocultar()`, etc.). Una transición inválida lanza `TransicionEstadoInvalidaError` o
`TransicionEstadoEventoInvalidaError`, y la API responde `409`.

### Perfil de organizador

```mermaid
stateDiagram-v2
    [*] --> PENDIENTE : SolicitarOrganizador
    PENDIENTE --> APROBADO : aprobar() (admin)
    PENDIENTE --> RECHAZADO : rechazar() (admin)
    RECHAZADO --> PENDIENTE : reenviar_solicitud() (el usuario)
    APROBADO --> SUSPENDIDO : suspender() (admin)
```

Un usuario `SUSPENDIDO` no puede volver a solicitar el perfil. Uno `RECHAZADO` reutiliza la misma
fila, porque `id_usuario` es único (multiplicidad 0..1).

### Evento

```mermaid
stateDiagram-v2
    [*] --> PUBLICADO : CrearEvento / seed
    BORRADOR --> CANCELADO : cancelar() (organizador)
    PUBLICADO --> CANCELADO : cancelar() (organizador)
    PUBLICADO --> OCULTO : ocultar() (admin)
    CANCELADO --> OCULTO : ocultar() (admin)
```

`BORRADOR` está en el enum y en las reglas de edición y visibilidad, pero hoy ningún flujo crea
eventos en ese estado: el alta los deja `PUBLICADO`.

## Decisiones del modelo

| Decisión | Motivo |
|---|---|
| PK UUID en todas las tablas salvo `categoria_evento` | Identificadores no secuenciales (RNF-04.3): no se pueden enumerar recursos. La API identifica las categorías por `slug`, así que su PK entera no se expone |
| `usuario` sin columna de rol | Los roles son tablas aparte con relación 0..1 (`organizadores`, `administradores`). Una misma cuenta busca y publica, y el permiso de administrador se consulta en cada request |
| Administradores dados de alta a mano en la base | No hay endpoint para asignar el rol: nadie puede escalar privilegios desde la app. La migración `0005` agrega `DEFAULT gen_random_uuid()` a `id_admin` para que alcance con un `INSERT ... SELECT` |
| Tokens guardados como hash | Si se filtra la base, los refresh y reset tokens no sirven. `revoked_at` y `used_at` permiten invalidarlos sin borrarlos |
| `password_hash` nullable | Deja preparado el login social (RF-01.5), donde no hay contraseña local |
| Coordenadas obligatorias, nombre y dirección opcionales en `lugar` | El pin del mapa es el dato autoritativo (RF-02.2) |
| Fechas en UTC más `hora_inicio_local` | El filtro por rango horario (RF-03.5) compara una columna `time` sin convertir zonas dentro de la query. `Evento.programar()` la recalcula siempre junto con las fechas |
| `eventos.id_organizador` nullable con `origen` | Los eventos del seed del equipo (RF-05.2) no tienen organizador y se distinguen por `origen = SEED_EQUIPO` |
| Índices `(latitud, longitud)` y `(estado, fecha_inicio)` | Cubren la búsqueda por viewport y la regla de visibilidad (solo `PUBLICADO` que no terminaron) |
| Categorías con `activa` en lugar de borrarlas | El catálogo es cerrado (RF-04.1): una categoría se retira sin romper los eventos que la usan |

## Migraciones

| Migración | Contenido |
|---|---|
| `0001_auth_tables` | `usuario`, `refresh_token`, `password_reset_token`, `audit_log` |
| `0002_organizadores` | `organizadores` y el tipo `estado_organizador` |
| `0003_administradores` | `administradores` |
| `0004_eventos` | `lugar`, `eventos`, `categoria_evento`, `evento_categoria`, los tipos `estado_evento` y `origen_evento`, y la carga de las 11 categorías |
| `0005_administradores_id_default` | `DEFAULT gen_random_uuid()` en `administradores.id_admin` (solo en PostgreSQL) |
