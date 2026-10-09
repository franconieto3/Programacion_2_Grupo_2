# Requisitos No Funcionales

## Plataforma de descubrimiento de eventos por geolocalización

---

## RNF-01 · Rendimiento

| # | Requisito |
|---|---|
| RNF-01.1 | La búsqueda de eventos por área visible del mapa (viewport) debe resolverse mediante consulta indexada, evitando recorridos completos de tabla (*full table scan*), sobre las columnas de estado, fecha de inicio y coordenadas. |
| RNF-01.2 | El filtro por rango horario debe resolverse contra un campo indexado (hora local denormalizada), sin requerir extracción de hora en tiempo de consulta sobre toda la tabla. |
| RNF-01.3 | La re-ejecución de la búsqueda al mover o hacer zoom sobre el mapa debe aplicar una técnica de demora (*debounce*) para evitar disparar una consulta por cada movimiento incremental del usuario. |
| RNF-01.4 | Las búsquedas de lugares mediante el geocodificador externo deben cachearse localmente para reducir llamadas repetidas y respetar los límites de uso del servicio. |

## RNF-02 · Escalabilidad

| # | Requisito |
|---|---|
| RNF-02.1 | El modelo de datos debe soportar múltiples ciudades y ubicaciones sin requerir una entidad "ciudad" predefinida ni cambios de código para incorporar una nueva zona geográfica. |
| RNF-02.2 | El diseño de la arquitectura (API desacoplada del frontend) debe permitir evolucionar o reemplazar el cliente (por ejemplo, incorporar una app nativa) sin modificar el backend. |
| RNF-02.3 | Los campos preparados para funcionalidades de fase 2 (recurrencia, destacado, origen del dato) deben existir desde el modelo inicial para evitar migraciones estructurales posteriores. |

## RNF-03 · Usabilidad

| # | Requisito |
|---|---|
| RNF-03.1 | La interfaz debe diseñarse con enfoque *mobile-first*, dado que el uso del mapa con geolocalización es mayoritariamente móvil. |
| RNF-03.2 | Ante una búsqueda sin resultados, el sistema debe comunicar explícitamente la causa (qué filtro los excluye) y ofrecer una acción correctiva, nunca una pantalla vacía sin explicación. |
| RNF-03.3 | El sistema debe ser plenamente utilizable aunque el usuario rechace el permiso de geolocalización del navegador. |
| RNF-03.4 | La interfaz y los mensajes al usuario deben estar en español. |

## RNF-04 · Seguridad

| # | Requisito |
|---|---|
| RNF-04.1 | Las contraseñas deben almacenarse con hashing seguro (nunca en texto plano). |
| RNF-04.2 | La autenticación debe realizarse mediante tokens (JWT), con el *access token* mantenido en memoria del cliente y nunca persistido en `localStorage`, para reducir superficie de ataque ante XSS. |
| RNF-04.3 | Los identificadores de entidades sensibles (usuarios, eventos) deben ser no secuenciales (UUID), evitando enumeración o filtrado del volumen real de registros. |
| RNF-04.4 | Las acciones de moderación (ocultar contenido, aprobar o suspender organizadores) deben quedar restringidas a administradores. El administrador no es un rol que pueda elegirse en el registro; el mecanismo con el que se lo representa está pendiente de definir. |

## RNF-05 · Compatibilidad e integraciones

| # | Requisito |
|---|---|
| RNF-05.1 | El uso del servicio de mapas y geocodificación (OpenStreetMap / Nominatim) debe respetar sus políticas de uso (límite de 1 solicitud por segundo, identificación mediante *User-Agent*, prohibición de geocodificación masiva). |
| RNF-05.2 | El entorno de desarrollo, pruebas y producción debe utilizar el mismo motor de base de datos (PostgreSQL) en desarrollo y producción, para evitar divergencias de comportamiento; SQLite se admite únicamente para la suite de tests automatizados. |
| RNF-05.3 | El backend debe exponer sus APIs mediante el framework **FastAPI** (Python), con documentación OpenAPI autogenerada y validación de esquemas mediante Pydantic. |

## RNF-06 · Mantenibilidad y calidad de código

| # | Requisito |
|---|---|
| RNF-06.1 | El proyecto debe contar con una suite de tests automatizados, con foco de cobertura en la lógica de búsqueda y filtrado (casos borde de fechas, horarios y límites geográficos). |
| RNF-06.2 | El código debe pasar controles de estilo y formato automatizados (linting) como parte del flujo de integración. |
| RNF-06.3 | Toda integración de código a la rama principal debe pasar por un pipeline de integración continua en verde y al menos una revisión por otro integrante del equipo. |
| RNF-06.4 | La rama principal del repositorio debe estar protegida contra *push* directo. |
| RNF-06.5 | El proyecto debe contar con documentación (README) que describa la arquitectura, las decisiones tomadas y la guía de puesta en marcha del entorno. |

## RNF-07 · Legales y de privacidad

| # | Requisito |
|---|---|
| RNF-07.1 | El sistema no debe persistir el historial de ubicaciones del usuario en el MVP; la ubicación se utiliza únicamente durante la sesión activa, en línea con la Ley de Protección de Datos Personales (Ley 25.326). |
| RNF-07.2 | Antes de operar con usuarios reales fuera del ámbito académico, el sistema debe contar con una política de privacidad accesible. |

## RNF-08 · Internacionalización y consistencia de datos

| # | Requisito |
|---|---|
| RNF-08.1 | Todas las marcas de tiempo deben almacenarse internamente en UTC y presentarse al usuario en hora local, para evitar ambigüedades y facilitar una futura expansión fuera de la zona horaria actual. |
| RNF-08.2 | Las coordenadas geográficas deben almacenarse con precisión suficiente para uso urbano (equivalente a aproximadamente 10 cm), sin necesidad de mayor precisión en el MVP. |

## RNF-09 · Disponibilidad

| # | Requisito |
|---|---|
| RNF-09.1 | El sistema no requiere garantías formales de disponibilidad (SLA) durante la etapa de Trabajo Práctico, dado que no opera con usuarios reales en producción crítica. |
| RNF-09.2 | En caso de despliegue, debe optar por proveedores sin infraestructura propia que gestionar (PaaS), dado que el equipo no cuenta con experiencia previa en Docker ni en operación de servidores. |
