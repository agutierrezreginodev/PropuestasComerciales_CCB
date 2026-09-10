# CCB Propuestas — Snapshot de Workflows n8n

Este repositorio contiene un **snapshot versionado** de los 4 workflows de producción del proyecto **CCB Propuestas** (Cámara de Comercio de Barranquilla — Información Geográfica), exportados directamente desde la instancia de n8n mediante la API/MCP de solo lectura.

El propósito es cumplir con el requisito de buenas prácticas (REQ-6.2 de auditoría): tener respaldo versionado en git de la definición completa de cada flujo, para poder auditar cambios, recuperar versiones anteriores y revisar la lógica sin depender exclusivamente del editor de n8n.

Cada archivo es el JSON completo del workflow (nodos, conexiones, configuración de errores, notas, etc.) tal como lo devuelve la API de n8n, con formato *pretty-printed* (2 espacios de indentación).

## Workflows incluidos

| ID en n8n | Nombre en n8n | Archivo |
|---|---|---|
| `w6h0qSblUESIpSVc` | CCB - Workflow 1 - Extracción información del cliente | [`workflows/w1-extraccion-informacion-cliente.json`](workflows/w1-extraccion-informacion-cliente.json) |
| `lIcdT6nGd0w1G2i0` | CCB - Workflow 2 - Formulario de Solicitud | [`workflows/w2-formulario-solicitud.json`](workflows/w2-formulario-solicitud.json) |
| `cHOIOEFB5nbltN82` | CCB - Workflow 3 - Motor Criterios y Precio | [`workflows/w3-motor-criterios-precio.json`](workflows/w3-motor-criterios-precio.json) |
| `Dh2lAQTzyoZBpXie` | CCB - Error Workflow (catch-all) | [`workflows/error-workflow-catchall.json`](workflows/error-workflow-catchall.json) |

## Anonimización

Este repositorio es **público**. Antes de subir los JSON se reemplazaron textualmente los siguientes valores internos/sensibles por placeholders genéricos. La lógica de negocio, nombres de nodos, expresiones, fórmulas de precio y estructura de conexiones **no se modificaron**.

| Dato original | Dónde aparecía | Placeholder usado |
|---|---|---|
| Correo personal usado para alertas de error/desarrollo | Múltiples nodos de notificación de errores (Workflow 1, Workflow 2, Error Workflow) y en la condición del nodo "¿Correo de mercadeo?" (Workflow 1) | `dev-alerts@example.com` |
| Correo de un asesor comercial de la Cámara | Código del nodo que arma los datos fijos de la propuesta (Workflow 3) | `asesor@example.com` |
| Nombre del mismo asesor comercial | Código del nodo que arma los datos fijos de la propuesta (Workflow 3) | `Asesor CCB` |
| URL del microservicio externo de generación de PDF (túnel ngrok) | Nodo HTTP Request que genera el PDF (Workflow 3) | `https://pdf-service.example.com` |
| ID de la carpeta de Outlook monitoreada por el trigger de correo entrante | Nodo "Nuevo correo" (Microsoft Outlook Trigger, Workflow 1), campo `filters.foldersToInclude` | `"<OUTLOOK_FOLDER_ID>"` |
| Identificador de archivo (workbook) de Excel/SharePoint | Nodo "Leer BD (hoja BD)" (Microsoft Excel, Workflow 3), campo `workbook.value` | `<EXCEL_WORKBOOK_ID>` |
| Identificador de hoja (worksheet) de Excel/SharePoint | Nodo "Leer BD (hoja BD)" (Microsoft Excel, Workflow 3), campo `worksheet.value` | `<EXCEL_WORKSHEET_ID>` |
| URL de SharePoint con el sitio personal, la ruta interna y el identificador del documento | Nodo "Leer BD (hoja BD)" (Microsoft Excel, Workflow 3), campos `workbook.cachedResultUrl` y `worksheet.cachedResultUrl` | `https://<EXCEL_SITE_ID>/<EXCEL_WORKBOOK_ID>` y `https://<EXCEL_SITE_ID>/<EXCEL_WORKBOOK_ID>/<EXCEL_WORKSHEET_ID>` respectivamente |

**Qué NO se anonimizó (a propósito):** IDs de workflow, IDs de Data Table, ID del proyecto de n8n, IDs y nombres de credenciales (p. ej. la credencial de Microsoft Outlook o de OpenRouter). Son identificadores internos de n8n, no secretos explotables por sí solos, y modificarlos habría roto el valor del snapshot como respaldo fiel de lo que corre en producción.

**Mantenimiento:** cualquier cambio relevante que se haga a estos workflows directamente en n8n debería re-exportarse (mismo procedimiento: `n8n_get_workflow` en modo `full`, aplicar los mismos reemplazos de esta tabla, y commitear el JSON actualizado acá) para que este repositorio no quede desactualizado como respaldo.

**Última actualización:** 2026-09-10 — se re-exportaron Workflow 2 (creció a 51 nodos: validación de resultado del motor por servicio) y Workflow 3 (creció a 18 nodos: interpolación de templates HTML, layout de portada, y manejo de errores de infraestructura en la lectura de la base de datos y la generación del PDF).
