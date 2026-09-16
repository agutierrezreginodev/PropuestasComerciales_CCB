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
| `lIcdT6nGd0w1G2i0` | CCB - Workflow 2 - Formulario de Solicitud *(formulario viejo, multi-página — sigue en producción para Zonificación, Ubicación e Información en Línea; Información Georreferenciada usa el formulario nuevo vía W2C)* | [`workflows/w2-formulario-solicitud.json`](workflows/w2-formulario-solicitud.json) |
| `cHOIOEFB5nbltN82` | CCB - Workflow 3 - Motor Criterios y Precio | [`workflows/w3-motor-criterios-precio.json`](workflows/w3-motor-criterios-precio.json) |
| `Dh2lAQTzyoZBpXie` | CCB - Error Workflow (catch-all) | [`workflows/error-workflow-catchall.json`](workflows/error-workflow-catchall.json) |

**Pendiente de agregar a este snapshot** (existen y están activos en producción, todavía no exportados a este repo): W4-A (Router de Aprobación), W4-B (Aprobación de Propuesta / Teams), W4-C (Consultar Propuesta), W4-D (Procesar Decisión de Propuesta), W5-A (Router de Envío), W5-B (Envío al Cliente), W6 (Finalizador de Cotizaciones).

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

Además, el bloque `shared` que n8n incluye en cada export (metadata de propiedad del workflow: nombre y correo del propietario, ID de proyecto, ID de creador) se **elimina por completo** de cada archivo antes de commitear — no aporta nada para auditar la lógica del flujo y expone datos personales innecesariamente.

**Qué NO se anonimizó (a propósito):** IDs de workflow, IDs de Data Table, ID del proyecto de n8n, IDs y nombres de credenciales. Son identificadores internos de n8n, no secretos explotables por sí solos, y modificarlos habría roto el valor del snapshot como respaldo fiel de lo que corre en producción.

**Mantenimiento:** cualquier cambio relevante que se haga a estos workflows directamente en n8n debería re-exportarse (`n8n_get_workflow` en modo `full`, quitar el bloque `shared`, aplicar los mismos reemplazos de esta tabla, y commitear el JSON actualizado acá) para que este repositorio no quede desactualizado como respaldo.

**Historial reescrito (16/09/2026):** se detectó que el correo interno (ahora `interno-alertas@example.com`) y el nombre del propietario del proyecto quedaron expuestos en texto plano en los commits anteriores (dentro del bloque `shared`, no cubierto por la tabla de anonimización original). Se reescribió el historial de este repositorio para purgar esa exposición de todos los commits, no solo del estado actual.

**Última actualización:** 2026-09-16 — se re-exportaron Workflow 1 (fixes de extracción por IA y filtro de correo), Workflow 3 (mapeos de organización jurídica y ubicación geográfica, corrección de género en "todos"), Error Workflow catch-all (campo de tipo de error agregado), y el formulario legacy (Workflow 2); se agregaron los workflows nuevos del formulario de Información Georreferenciada (Workflow 2C y Workflow 2A); y se corrigió la exposición de datos personales descrita arriba.
