# CCB Propuestas — Snapshot de Workflows n8n

Este repositorio contiene un **snapshot versionado** de los workflows de producción del proyecto **CCB Propuestas** (Cámara de Comercio de Barranquilla — Información Geográfica), exportados directamente desde la instancia de n8n mediante la API/MCP de solo lectura.

El propósito es cumplir con el requisito de buenas prácticas (REQ-6.2 de auditoría): tener respaldo versionado en git de la definición completa de cada flujo, para poder auditar cambios, recuperar versiones anteriores y revisar la lógica sin depender exclusivamente del editor de n8n.

Cada archivo es el JSON completo del workflow (nodos, conexiones, configuración de errores, notas, etc.) tal como lo devuelve la API de n8n, con formato *pretty-printed* (2 espacios de indentación).

## Workflows incluidos

| ID en n8n | Nombre en n8n | Archivo |
|---|---|---|
| `w6h0qSblUESIpSVc` | CCB - Workflow 1 - Extracción información del cliente | [`workflows/w1-extraccion-informacion-cliente.json`](workflows/w1-extraccion-informacion-cliente.json) |
| `u6KCMnLwFOp6Ja0N` | CCB - Workflow 2C - Recepción Formulario Externo (Georreferenciada) | [`workflows/w2c-recepcion-formulario-externo.json`](workflows/w2c-recepcion-formulario-externo.json) |
| `VChcasvisGKekezR` | CCB - Workflow 2A - Guardar Criterios y Cotizar Servicio | [`workflows/w2a-guardar-criterios-cotizar-servicio.json`](workflows/w2a-guardar-criterios-cotizar-servicio.json) |
| `lIcdT6nGd0w1G2i0` | CCB - Workflow 2B - Formulario de Solicitud *(**retirado, `active: false`** — no recibe tráfico real. Confirmado por historial: una sola ejecución en toda su vida, de prueba manual el 14/09, sin terminar. Se conserva en el snapshot como referencia histórica del formulario multi-página original)* | [`workflows/w2-formulario-solicitud.json`](workflows/w2-formulario-solicitud.json) |
| `cHOIOEFB5nbltN82` | CCB - Workflow 3 - Motor Criterios y Precio | [`workflows/w3-motor-criterios-precio.json`](workflows/w3-motor-criterios-precio.json) |
| `7gmpPMBJtEb0W3J5` | CCB - Workflow 4A - Router de Aprobación | [`workflows/w4a-router-aprobacion.json`](workflows/w4a-router-aprobacion.json) |
| `5RJdnHDQ8NuWZJG7` | CCB - Workflow 4B - Aprobación de Propuesta (Teams) | [`workflows/w4b-aprobacion-propuesta-teams.json`](workflows/w4b-aprobacion-propuesta-teams.json) |
| `KuLSIzBZgaRIjuSu` | CCB - Workflow 4C - Consultar Propuesta para Revisión | [`workflows/w4c-consultar-propuesta-revision.json`](workflows/w4c-consultar-propuesta-revision.json) |
| `W0TDH4b0tHCNOzFQ` | CCB - Workflow 4D - Procesar Decisión de Propuesta | [`workflows/w4d-procesar-decision-propuesta.json`](workflows/w4d-procesar-decision-propuesta.json) |
| `gvIn6mbAn2Y1bMRR` | CCB - Workflow 5A - Router de Envío | [`workflows/w5a-router-envio.json`](workflows/w5a-router-envio.json) |
| `XWBHgbmtBubA4gqx` | CCB - Workflow 5B - Envío al Cliente | [`workflows/w5b-envio-al-cliente.json`](workflows/w5b-envio-al-cliente.json) |
| `mPwl4qUb0zQkmDHN` | CCB - Workflow 6 - Finalizador de Cotizaciones | [`workflows/w6-finalizador-cotizaciones.json`](workflows/w6-finalizador-cotizaciones.json) |
| `Dh2lAQTzyoZBpXie` | CCB - Error Workflow (catch-all) | [`workflows/error-workflow-catchall.json`](workflows/error-workflow-catchall.json) |

El snapshot está **completo**: los 12 workflows del pipeline definitivo más el Error Workflow catch-all. Se exportan con [`scripts/export_workflows.py`](scripts/export_workflows.py) (ver *Mantenimiento*).

## Pipeline completo — Información Georreferenciada

Recorrido de punta a punta, verificado en vivo con datos reales (16/09/2026), sin ningún paso simulado:

1. **W1** recibe un correo (de mercadeo o contacto directo del cliente) filtrado por una regla nativa de Outlook, extrae nombre/teléfono/email con IA y envía al cliente el link del formulario público.
2. El cliente completa el **formulario público** (página estática) y lo envía.
3. **W2C** recibe el formulario → **W2A** guarda los criterios y ejecuta el motor → **W3** filtra la base de empresas, calcula el precio y genera el PDF de la propuesta.
4. Un router (W4-A) dispara la notificación al asesor comercial por Microsoft Teams (W4-B) con un link a una página de revisión.
5. El asesor revisa el PDF y elige una de tres acciones: **Aprobar**, **Solicitar correcciones** o **Cancelar** (W4-D).
   - *Solicitar correcciones* dispara un ajuste asistido por IA sobre los criterios guardados, validado contra listas fijas de valores permitidos (para que un valor fuera de lista se descarte en vez de corromper el dato en silencio), y vuelve a invocar el motor. Tope de 3 rondas antes de pasar a revisión manual.
   - *Cancelar* termina el flujo sin llegar nunca a entrega.
6. Al aprobar, un router (W5-A) dispara el envío al cliente (W5-B): PDF adjunto (o solo link si supera 4MB) + confirmación interna al asesor.
7. Un cierre automático (W6) marca como finalizadas las cotizaciones enviadas que llevan 30+ días sin respuesta.
8. Un **Error Workflow catch-all** transversal captura cualquier fallo no manejado explícitamente por el flujo de origen, lo registra y envía una alerta técnica con flujo, tipo de error, nodo fallido y mensaje.

Un diagrama interactivo de este flujo (generado con [Archify](https://github.com/tt-a1i/archify)) está disponible en [`docs/diagrams/pipeline-ccb.html`](docs/diagrams/pipeline-ccb.html).

## Resumen de pruebas realizadas (16/09/2026)

Se corrió el recorrido completo en vivo contra la instancia real de n8n y datos reales de prueba (nunca simulados), cubriendo los tres caminos de decisión del asesor (aprobar, corregir con IA, cancelar) y el manejo de errores en cada etapa. Como parte de esa ronda de pruebas se encontraron y corrigieron alrededor de una decena de fallos reales, entre ellos:

- Formato de respuesta del modelo de IA que rompía el parser de extracción de datos.
- Mapeos de tipo de organización y de ubicación geográfica del formulario que no coincidían con las categorías esperadas por el motor, produciendo "0 registros" sin explicar la causa.
- Una notificación interna que se perdía en silencio cuando una solicitud entraba por el formulario nuevo sin pasar por el flujo de correo.
- Una validación insuficiente en el ajuste de criterios por IA, que permitía que un valor mal interpretado por el modelo se filtrara hacia un campo equivocado sin ser detectado hasta rondas posteriores — corregido con una whitelist de valores permitidos por campo.
- Una alerta de error de envío que no reflejaba el detalle real del fallo.

Todo el detalle de casos de prueba (matriz completa de cobertura, evidencia de cada ejecución) se mantiene en la documentación operativa interna del proyecto, fuera de este repositorio público.

## Auditoría de buenas prácticas

Los 12 workflows se evaluaron contra el marco *Arquitectura e Ingeniería de Automatización en n8n* (rúbrica ponderada de 6 dimensiones sobre 100 puntos y lista de comprobación de 11 requisitos de despliegue).

- **[Informe de auditoría (2026-09-16)](docs/AUDITORIA_BUENAS_PRACTICAS_2026-09-16.md)** — procedimiento reproducible paso a paso, resultado consolidado, desglose por dimensión y ficha por flujo con lo que cumple, lo que no y sus pendientes.
- **[Plan de remediación](docs/PLAN_REMEDIACION.md)** — la estrategia: las 8 fases para pasar de 53,6 a ≥90/100, con ganancia estimada, esfuerzo y dependencias externas.
- **[Plan de trabajo](docs/PLAN_TRABAJO_FRAMEWORK.md)** — el tablero de ejecución: 50 tareas atómicas con el nodo exacto sobre el que se actúa, cómo se verifica cada una y el seguimiento de puntaje por flujo.

Resultado: promedio **53,6/100**, ningún flujo sobre el umbral de 90. Tres flujos en clasificación *Crítico* y nueve en *Requiere refactorización*. Los hallazgos son sistemáticos (autenticación de endpoints, validación de entradas, documentación, configuración centralizada), no defectos aislados. Ningún workflow fue modificado durante la auditoría.

## Anonimización

Este repositorio es **público**. Antes de subir los JSON se reemplazaron textualmente los siguientes valores internos/sensibles por placeholders genéricos. La lógica de negocio, nombres de nodos, expresiones, fórmulas de precio y estructura de conexiones **no se modificaron**.

| Dato original | Dónde aparecía | Placeholder usado |
|---|---|---|
| Correo usado para alertas de error/desarrollo | Múltiples nodos de notificación de errores | `dev-alerts@example.com` |
| Correo interno usado como destinatario de prueba / propietario del proyecto en n8n | Nodos de notificación en modo prueba | `interno-alertas@example.com` |
| Correo de un asesor comercial de la Cámara | Código de datos fijos de la propuesta (Workflow 3) | `asesor@example.com` |
| Nombre del mismo asesor comercial | Código de datos fijos de la propuesta (Workflow 3) | `Asesor CCB` |
| URL del microservicio externo de generación de PDF (túnel ngrok) | Nodo HTTP Request que genera el PDF (Workflow 3) | `https://pdf-service.example.com` |
| ID de la carpeta de Outlook monitoreada por el trigger de correo entrante | Nodo "Nuevo correo" (Workflow 1) | `<OUTLOOK_FOLDER_ID>` |
| Identificador de archivo (workbook) de Excel/SharePoint | Nodo de lectura de la base de empresas (Workflow 3) | `<EXCEL_WORKBOOK_ID>` |
| Identificador de hoja (worksheet) de Excel/SharePoint | Nodo de lectura de la base de empresas (Workflow 3) | `<EXCEL_WORKSHEET_ID>` |
| URL de SharePoint con sitio personal, ruta interna e identificador del documento | Nodo de lectura de la base de empresas (Workflow 3) | `https://<EXCEL_SITE_ID>/<EXCEL_WORKBOOK_ID>` (y variante con `/<EXCEL_WORKSHEET_ID>`) |
| Nombre de pila del asesor comercial, suelto (sin apellidos) | Nombres de nodo y sticky notes de varios flujos | `Asesor CCB` |
| Identificador de chat de Microsoft Teams (`<n>:<hash>@unq.gbl.spaces`) | Nodos de envío a Teams (Workflows 4B y 4D) | `<TEAMS_CHAT_ID>` |
| Identificador de carpeta/mensaje de Outlook (cadena que empieza con `AAMk`) | Filtro `foldersToInclude` del trigger de correo (Workflow 1) | `<OUTLOOK_FOLDER_ID>` |

Las tres últimas filas se agregaron el 2026-09-16: el proceso anterior no las cubría porque esos identificadores solo aparecen en los flujos incorporados en esa fecha.

Además, el bloque `shared` que n8n incluye en cada export (metadata de propiedad del workflow: nombre y correo del propietario, ID de proyecto, ID de creador) se **elimina por completo** de cada archivo antes de commitear — no aporta nada para auditar la lógica del flujo y expone datos personales innecesariamente.

**Qué NO se anonimizó (a propósito):** IDs de workflow, IDs de Data Table, ID del proyecto de n8n, IDs y nombres de credenciales. Son identificadores internos de n8n, no secretos explotables por sí solos, y modificarlos habría roto el valor del snapshot como respaldo fiel de lo que corre en producción. Tampoco se tocó la columna `comentario_fausto` de una Data Table: es un nombre de campo del esquema de datos, y renombrarlo en el snapshot lo dejaría inconsistente con la base real.

**Mantenimiento:** el proceso está automatizado en [`scripts/export_workflows.py`](scripts/export_workflows.py). Exporta los 13 flujos desde la instancia, elimina el bloque `shared`, aplica exactamente la tabla de reemplazos de arriba y **termina con código de error si sobrevive algún correo fuera de los dominios de reemplazo**, para que una fuga no pueda colarse en un commit sin que nadie lo note.

```bash
N8N_API_URL="https://<instancia>" N8N_API_KEY="<clave>" python3 scripts/export_workflows.py
```

Las credenciales se leen solo del entorno: nunca se escriben en disco ni se imprimen. Conviene correrlo después de cualquier cambio relevante en n8n, y siempre al cerrar una fase del plan de remediación.

**Historial reconstruido (16/09/2026):** se detectó que el correo interno (ahora `interno-alertas@example.com`) y el nombre del propietario del proyecto quedaron expuestos en texto plano en los commits anteriores (dentro del bloque `shared`, no cubierto por la tabla de anonimización original). El historial de esta rama se reconstruyó desde cero —no comparte ningún commit con el anterior— y está verificado sin esa exposición en **ninguno** de sus commits, no solo en el estado actual.

Ese historial reemplazó a la rama publicada el 16/09/2026, y las ramas que aún alcanzaban los commits antiguos se eliminaron. Hoy **ningún commit con esa exposición es alcanzable desde ninguna rama de este repositorio**.

> ⚠️ Queda un residuo conocido: GitHub conserva los commits huérfanos y las referencias internas de los pull requests, así que los commits antiguos siguen siendo consultables por su identificador directo. Cerrar eso requiere solicitar a GitHub Support la purga de referencias y la recolección de basura del repositorio. Los datos involucrados son un correo interno y un nombre propio — no credenciales.

**Última actualización:** 2026-09-16 (tarde) — se completó el snapshot con los 7 workflows que faltaban (4A, 4B, 4C, 4D, 5A, 5B y 6), se re-exportaron los 6 existentes desde el estado vivo, se automatizó el proceso en `scripts/export_workflows.py`, se amplió la tabla de anonimización con tres identificadores nuevos, y se publicó la auditoría de buenas prácticas de los 12 flujos junto con su plan de remediación y el plan de trabajo para ejecutarlo. También se reemplazó la rama publicada por el historial sin PII.

**Actualización previa:** 2026-09-16 (mañana) — se re-exportaron Workflow 1 (fixes de extracción por IA y filtro de correo), Workflow 3 (mapeos de organización jurídica y ubicación geográfica, corrección de género en "todos"), Error Workflow catch-all (campo de tipo de error agregado), y el formulario legacy (Workflow 2); se agregaron los workflows nuevos del formulario de Información Georreferenciada (Workflow 2C y Workflow 2A); y se corrigió la exposición de datos personales descrita arriba.
