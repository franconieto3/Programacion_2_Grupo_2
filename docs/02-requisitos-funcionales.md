# Requisitos Funcionales

## Plataforma de descubrimiento de eventos por geolocalización

Clasificación según el método **MoSCoW**:

- **Must have (M):** imprescindible. Sin esto, el producto no cumple su objetivo mínimo. Forma
  parte del MVP entregado como Trabajo Práctico.
- **Should have (S):** importante, pero no bloqueante para el MVP. Primera prioridad de fase 2.
- **Could have (C):** deseable, aporta valor pero es prescindible en el corto/mediano plazo.

---

## RF-01 · Gestión de cuentas y autenticación

| # | Requisito | Prioridad |
|---|---|---|
| RF-01.1 | El sistema debe permitir registrar un usuario con nombre, apellido, email y contraseña | **M** |
| RF-01.2 | Todo usuario registrado puede descubrir eventos | **M** |
| RF-01.3 | El sistema debe permitir iniciar y cerrar sesión mediante email y contraseña | **M** |
| RF-01.4 | El sistema debe permitir editar los datos básicos del perfil propio | **M** |
| RF-01.5 | El sistema debe permitir autenticación mediante proveedores externos (login social) | **C** |
| RF-01.6 | El sistema debe permitir a un usuario registrado solicitar convertirse en organizador (nombre público y descripción). La solicitud queda `PENDIENTE` hasta que un administrador la aprueba o rechaza | **M** |
| RF-01.7 | El sistema debe permitir crear y editar eventos solo a usuarios con perfil de organizador `APROBADO` | **M** |
| RF-01.8 | El sistema debe permitir verificaciones adicionales del organizador (identidad, documentación, con fecha de vencimiento) y mostrar una insignia de verificado | **S** |

## RF-02 · Gestión de eventos (Organizador)

| # | Requisito | Prioridad |
|---|---|---|
| RF-02.1 | El sistema debe permitir a un organizador dar de alta un evento con título, descripción, fecha/hora de inicio, fecha/hora de fin (opcional) y precio (opcional) | **M** |
| RF-02.2 | El sistema debe permitir ubicar el evento marcando un punto sobre el mapa (coordenadas como dato autoritativo) | **M** |
| RF-02.3 | El sistema debe permitir asociar el evento a una o varias categorías de un catálogo cerrado | **M** |
| RF-02.4 | El sistema debe permitir editar y dar de baja (cancelar) un evento propio | **M** |
| RF-02.5 | El sistema debe mostrar al organizador un listado de "mis eventos" con su estado actual | **M** |
| RF-02.6 | El sistema debe permitir adjuntar una imagen de portada opcional al evento | **S** |
| RF-02.7 | El sistema debe permitir definir eventos recurrentes (agenda periódica) sin recargarlos manualmente cada vez | **S** |
| RF-02.8 | El sistema debe permitir reutilizar un lugar ya cargado en eventos anteriores del mismo organizador | **S** |
| RF-02.9 | El sistema debe permitir destacar un evento (posicionamiento pago) por un período determinado | **C** |
| RF-02.10 | El sistema debe ofrecer al organizador un panel de analítica de su evento (vistas, clics, alcance) | **C** |

## RF-03 · Descubrimiento y búsqueda de eventos (cualquier usuario)

| # | Requisito | Prioridad |
|---|---|---|
| RF-03.1 | El sistema debe mostrar los eventos disponibles en una vista de mapa, centrada por defecto en la geolocalización del usuario | **M** |
| RF-03.2 | El sistema debe mostrar los eventos disponibles en una vista de lista, con los mismos resultados que la vista mapa | **M** |
| RF-03.3 | El sistema debe permitir desplazar y hacer zoom sobre el mapa, re-ejecutando la búsqueda según el área visible (viewport) | **M** |
| RF-03.4 | El sistema debe permitir filtrar eventos por rango de fechas | **M** |
| RF-03.5 | El sistema debe permitir filtrar eventos por rango horario | **M** |
| RF-03.6 | El sistema debe permitir filtrar eventos por una o varias categorías (filtro opcional, multi-selección) | **M** |
| RF-03.7 | El sistema debe permitir buscar y establecer una ubicación de referencia distinta a la ubicación física actual del usuario (por ejemplo, un destino de viaje) | **M** |
| RF-03.8 | El sistema debe funcionar de forma plenamente usable si el usuario rechaza el permiso de geolocalización, ofreciendo una ubicación por defecto y un buscador de lugar | **M** |
| RF-03.9 | El sistema debe mostrar, ante una búsqueda sin resultados, un mensaje explícito sobre qué filtro los está excluyendo y una acción correctiva sugerida | **M** |
| RF-03.10 | El sistema debe mostrar una ficha de detalle del evento con los datos del organizador que lo publica | **M** |
| RF-03.11 | El sistema debe permitir marcar eventos como favoritos | **S** |
| RF-03.12 | El sistema debe permitir guardar ubicaciones de interés para reutilizarlas en futuras búsquedas | **S** |
| RF-03.13 | El sistema debe permitir calificar o reseñar eventos y organizadores | **C** |
| RF-03.14 | El sistema debe enviar notificaciones (push o email) sobre nuevos eventos relevantes para el usuario | **C** |

## RF-04 · Categorías

| # | Requisito | Prioridad |
|---|---|---|
| RF-04.1 | El sistema debe mantener un catálogo cerrado de categorías de eventos (bar, recital, teatro, cine, deportivo, museo, gastronomía, feria, taller, aire libre, otro) | **M** |
| RF-04.2 | El sistema debe permitir asociar múltiples categorías a un mismo evento | **M** |
| RF-04.3 | El sistema debe permitir a un administrador ampliar o modificar el catálogo de categorías | **C** |

## RF-05 · Moderación y administración de contenido

| # | Requisito | Prioridad |
|---|---|---|
| RF-05.1 | El sistema debe permitir a un administrador ocultar (dar de baja lógica) cualquier evento publicado | **M** |
| RF-05.2 | El sistema debe permitir al equipo cargar eventos de origen propio (seed) diferenciados del contenido publicado por organizadores reales | **M** |
| RF-05.3 | El sistema debe permitir a los usuarios reportar un evento sospechoso o falso | **S** |
| RF-05.4 | El sistema debe incorporar mecanismos automáticos de detección de spam o duplicados | **C** |
| RF-05.5 | El sistema debe permitir a un administrador aprobar, rechazar y suspender perfiles de organizador | **M** |

## RF-06 · Ingesta de contenido externo

| # | Requisito | Prioridad |
|---|---|---|
| RF-06.1 | El sistema debe poder incorporar eventos desde fuentes externas de forma automatizada (ETL), con normalización, geocodificación y deduplicación | **S** |

## RF-07 · Monetización

| # | Requisito | Prioridad |
|---|---|---|
| RF-07.1 | El sistema debe permitir a un organizador pagar para destacar su evento en los resultados de búsqueda | **C** |
| RF-07.2 | El sistema debe integrarse con una pasarela de pago para procesar el cobro de publicidad | **C** |

---

## Resumen por prioridad

| Prioridad | Cantidad de requisitos |
|---|---|
| **Must (M)** | 26 |
| **Should (S)** | 8 |
| **Could (C)** | 9 |

Los requisitos **Must** constituyen el MVP / Trabajo Práctico. Los requisitos **Should** son la
primera prioridad de una eventual fase 2 del producto. Los requisitos **Could** aportan valor pero
no son necesarios para validar la propuesta de valor central del producto.
