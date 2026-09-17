# Objetivo y Alcance del Proyecto

## Plataforma de descubrimiento de eventos por geolocalización

---

## 1. Problema que se aborda

La oferta de actividades de una zona (bares, recitales, teatro, cine, eventos deportivos, ferias,
talleres, museos, etc.) está fragmentada entre los canales propios de cada organizador: las redes
sociales del bar, del teatro, de la banda, de la marca. Si una persona no sigue activamente a
quien organiza, simplemente no se entera de que el evento existe.

Esto genera un problema de descubrimiento, no de escasez: la oferta suele existir, pero no es
visible para quien no conoce de antemano al organizador.

## 2. Objetivo del proyecto

Diseñar y desarrollar una plataforma web que centralice la oferta de eventos y actividades de una
zona, y la haga navegable **por ubicación, fecha y categoría** — en lugar de por organizador —
para resolver dos preguntas concretas:

- **"¿Qué puedo hacer hoy o esta semana cerca de donde estoy?"**
- **"¿Qué voy a poder hacer en el lugar al que voy a viajar?"**

## 3. Propuesta de valor

- **Para quien busca actividades (demandante):** un único lugar donde descubrir eventos por
  cercanía geográfica, fecha/horario y categoría, sin necesidad de conocer o seguir previamente
  al organizador. La búsqueda funciona tanto sobre la ubicación actual como sobre una ubicación
  alternativa (por ejemplo, un destino de viaje futuro).
- **Para quien organiza actividades (oferente):** un canal gratuito de publicación y visibilidad,
  alternativo o complementario a sus redes sociales propias, que lo pone frente a personas que no
  lo conocían de antemano.

## 4. Modelo de dos lados

El producto conecta dos roles de usuario con necesidades opuestas y complementarias:

| Rol | Qué hace |
|---|---|
| **Demandante** | Busca y descubre eventos filtrando por ubicación, fecha/horario y categoría |
| **Oferente** | Publica sus eventos (persona, local, marca o establecimiento) para ganar visibilidad |

Ambos roles se registran con cuentas separadas y excluyentes desde el alta.

## 5. Naturaleza del entregable

Este proyecto tiene una doble naturaleza, definida desde el inicio de la planificación:

1. Es el **Trabajo Práctico** de la materia Programación 2, desarrollado por un equipo de 3 a 5
   personas en un plazo de 4 a 8 semanas, con control de versiones y CI/CD como criterios de
   evaluación explícitos de la cátedra.
2. Es, al mismo tiempo, la **base funcional de un producto real**, pensado para poder crecer más
   allá del TP sin necesidad de reescribirse.

Esta doble naturaleza es la que orienta las decisiones de alcance: se prioriza lo que el equipo
puede construir y defender dentro del plazo académico, evitando decisiones que cierren puertas
arquitectónicas a futuro.

## 6. Alcance general

### Incluido (MVP)

- Registro y autenticación de usuarios, con rol excluyente (demandante u oferente).
- Alta, edición y baja de eventos por parte del oferente, con ubicación geográfica precisa
  (marcada directamente sobre el mapa) y una o varias categorías de un catálogo cerrado.
- Búsqueda y descubrimiento de eventos por parte del demandante, en dos vistas (mapa y lista),
  filtrando por rango de fechas, rango horario y categoría.
- Posibilidad de explorar eventos en una ubicación distinta a la ubicación física actual del
  usuario (por ejemplo, un destino de viaje).
- Carga inicial de contenido mediante seed manual del equipo (no se incluye integración
  automática con fuentes externas).
- Moderación básica de contenido por parte de un administrador.
- Prácticas de ingeniería de software: suite de tests automatizados, pipeline de integración
  continua y documentación del proyecto.

### Explícitamente fuera de alcance (fase 2, posterior al TP)

- Ingesta automática de eventos desde fuentes externas (ETL).
- Favoritos y ubicaciones guardadas por el usuario.
- Eventos recurrentes (agenda semanal fija de un mismo lugar).
- Verificación de identidad de oferentes y sistema de reportes de usuarios.
- Notificaciones (push/email) sobre nuevos eventos.
- Monetización mediante publicidad o posicionamiento pago.
- Dashboard de analítica para oferentes.
- Reseñas y calificaciones de eventos u oferentes.
- Aplicación nativa o PWA.

La justificación detallada de cada decisión de alcance, junto con el modelo de datos, la
arquitectura técnica y el detalle funcional, se desarrolla en los documentos de Requisitos
Funcionales, Requisitos No Funcionales y Casos de Uso que acompañan a este documento.
