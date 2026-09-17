# Casos de Uso

## Plataforma de descubrimiento de eventos por geolocalización

---

## CU-01 · Demandante descubre eventos cerca de su ubicación actual

**Actor principal:** Usuario con rol Demandante

**Precondiciones:**
- El usuario tiene una cuenta registrada e inició sesión (o navega sin sesión, si la búsqueda es pública).
- El navegador solicita permiso de geolocalización.

**Flujo principal:**
1. El usuario ingresa a la vista de Mapa.
2. El sistema solicita permiso de geolocalización al navegador.
3. El usuario acepta el permiso.
4. El sistema centra el mapa en la ubicación actual del usuario y ejecuta una búsqueda de eventos dentro del área visible (viewport), con los filtros por defecto (sin rango de fecha ni categoría aplicados, u horizonte por defecto como "próximas 24-48 h").
5. El sistema muestra los eventos encontrados como marcadores sobre el mapa.
6. El usuario ajusta el rango de fechas y horario mediante los filtros disponibles.
7. El sistema re-ejecuta la búsqueda y actualiza los marcadores.
8. El usuario selecciona un marcador.
9. El sistema muestra la ficha de detalle del evento (título, descripción, fecha/hora, ubicación, precio si corresponde, datos del oferente).

**Flujos alternativos:**
- **3a. El usuario rechaza el permiso de geolocalización:** el sistema centra el mapa en una ubicación por defecto y muestra visible el buscador de lugar, permitiendo continuar la búsqueda sin geolocalización (RF-03.8).
- **5a. No hay eventos en el área y rango seleccionados:** el sistema informa explícitamente qué filtro está excluyendo resultados (por ejemplo, "no hay eventos en este rango de fechas en la zona visible") y sugiere una acción correctiva, como ampliar el rango de fechas o alejar el mapa (RF-03.9).
- **6a. El usuario desplaza o hace zoom sobre el mapa:** el sistema re-dispara la búsqueda sobre la nueva área visible, con demora (debounce) para no disparar una consulta por cada movimiento (RF-03.3, RNF-01.3).

**Postcondición:** el usuario visualiza los eventos disponibles en la zona y el rango de fechas/horario de su interés, y puede acceder al detalle de cualquiera de ellos.

**Requisitos relacionados:** RF-03.1, RF-03.3, RF-03.4, RF-03.5, RF-03.8, RF-03.9, RF-03.10.

---

## CU-02 · Demandante explora eventos en una ubicación distinta a la actual

**Actor principal:** Usuario con rol Demandante

**Escenario:** el usuario se encuentra actualmente en una ciudad, pero viajará a otra dentro de unos días y quiere saber qué actividades va a tener disponibles.

**Precondiciones:**
- El usuario está en la vista de Mapa o Lista.

**Flujo principal:**
1. El usuario utiliza el buscador de ubicación e ingresa el nombre de la ciudad o lugar de destino (por ejemplo, "Mar del Plata").
2. El sistema consulta el servicio de geocodificación (Nominatim) y muestra sugerencias coincidentes.
3. El usuario selecciona la ubicación deseada de la lista de sugerencias.
4. El sistema desplaza el mapa (o ajusta la referencia de la vista Lista) a la ubicación seleccionada, sin modificar la ubicación física real del usuario.
5. El usuario define el rango de fechas correspondiente a su viaje (por ejemplo, "dentro de una semana, 3 días").
6. El sistema ejecuta la búsqueda de eventos en esa ubicación y rango de fechas, y muestra los resultados en la vista elegida (mapa o lista).
7. El usuario revisa los resultados y accede al detalle de los eventos que le interesan.

**Flujos alternativos:**
- **2a. No se encuentran coincidencias para el texto ingresado:** el sistema informa que no se encontró la ubicación y sugiere revisar la búsqueda.
- **6a. No hay eventos publicados para esa ubicación y rango:** el sistema muestra el estado vacío explicativo, igual que en CU-01.

**Postcondición:** el usuario obtiene un panorama de la oferta de eventos en un lugar donde no se encuentra físicamente, para un rango de fechas futuro.

**Requisitos relacionados:** RF-03.2, RF-03.4, RF-03.6, RF-03.7, RNF-01.4.

---

## CU-03 · Oferente publica un nuevo evento

**Actor principal:** Usuario con rol Oferente

**Precondiciones:**
- El usuario tiene una cuenta registrada con rol Oferente e inició sesión.

**Flujo principal:**
1. El usuario accede a la opción "Publicar evento".
2. El sistema muestra un formulario de carga con los campos: título, descripción, fecha/hora de inicio, fecha/hora de fin (opcional) y precio (opcional).
3. El usuario completa los datos generales del evento.
4. El sistema muestra un mapa interactivo para que el usuario marque, arrastrando un pin, la ubicación exacta del evento.
5. El usuario posiciona el pin en el lugar correspondiente.
6. El usuario selecciona una o varias categorías del catálogo cerrado (por ejemplo, "recital" y "aire libre").
7. El usuario confirma la publicación.
8. El sistema valida los datos ingresados, guarda el evento con estado `PUBLICADO` y lo asocia al perfil del oferente.
9. El sistema muestra el evento en el listado "Mis eventos" del oferente.

**Flujos alternativos:**
- **8a. Faltan datos obligatorios o son inválidos (por ejemplo, fecha de fin anterior a la de inicio):** el sistema rechaza el guardado e indica los campos a corregir.
- **9a. El oferente decide editar el evento luego de publicado:** desde "Mis eventos", accede a la edición, modifica los campos necesarios (incluyendo reposicionar el pin o cambiar categorías) y guarda los cambios (RF-02.4).
- **9b. El oferente decide cancelar el evento:** desde "Mis eventos", cambia el estado del evento a cancelado; el evento deja de aparecer en las búsquedas de los demandantes.

**Postcondición:** el evento queda publicado y disponible para ser descubierto por demandantes que realicen una búsqueda compatible con su ubicación, fecha/horario y categoría.

**Requisitos relacionados:** RF-02.1, RF-02.2, RF-02.3, RF-02.4, RF-02.5, RF-04.1, RF-04.2.

---

## Nota sobre priorización de estos casos de uso

Los tres casos de uso descriptos representan el **flujo central del producto** (el "corazón" del
MVP, según la planificación): la publicación de un evento por parte de un oferente y su
descubrimiento por parte de un demandante, tanto en la ubicación actual como en una ubicación de
interés futura. Cualquier funcionalidad de fase 2 (favoritos, notificaciones, publicidad,
recurrencia, etc.) se apoya sobre estos tres flujos base y no los reemplaza.
