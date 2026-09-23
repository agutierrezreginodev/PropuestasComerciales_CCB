# Feature: cerrar la brecha al umbral de 90 y documentar el flujo completo

**Creada:** 2026-09-23 · **Origen:** [re-auditoría del 23/09](../../docs/AUDITORIA_BUENAS_PRACTICAS_2026-09-23.md) (87,7/100)
y la petición del usuario de *"seguir con los pendientes para cumplir con el puntaje de la auditoría, y documentar todo el flujo"*.

## Objetivo

Cerrar la brecha de **2,3 puntos** que separa al pipeline del umbral de **90/100** del framework, concentrada en
**Testing (11,7/15)** y en dos puntos de **Observabilidad** y **Seguridad**; y dejar el pipeline **documentado de punta a
punta**, incluyendo el recorrido de negocio completo, no solo la ficha por flujo.

## Alcance

- **Dentro:** los workflows de la instancia viva, sus datos de prueba, el repo `ccb-workflows-git` (snapshot, docs) y la
  memoria de proyecto.
- **Fuera:** la poda de ejecuciones a nivel de instancia, el cierre de `/metrics` y los tokens de los front-ends
  (dependen de Tecnología); la creación de la credencial *Header Auth* en la UI y el clic de rechazo en Teams (dependen
  del usuario); la carpeta `Servicios_Información_Cotizaciones_v2.0` (bloqueada por permisos del API).

## Criterio de cierre

1. Cada tarea con **evidencia de ejecución real** (id de ejecución, filas, correo) registrada en este archivo.
2. Re-auditoría final publicada con el puntaje nuevo (objetivo: **≥90** o la explicación exacta de lo que falta).
3. `docs/FLUJO_COMPLETO_PIPELINE_CCB.md` publicado y enlazado desde el README.
4. Un commit por unidad de trabajo y snapshot re-exportado.

---

## Tareas

| # | Tarea | Criterio de aceptación | Estado |
|---|---|---|---|
| **R1** | Restaurar el `httpMethod: GET` explícito en el webhook de W4C | El snapshot muestra el método y el path responde como webhook vivo | ☑ 23/09 — commit `089af00` |
| **R2** | Verificar con tráfico real la ruta de error compartida (`[SUB] CCB - Registrar y Alertar Error`) | Una ejecución real que falle deja fila en `Errores_CCB` con `error_timestamp` y mensaje enmascarado, envía el correo de alerta y **no corta** el flujo que la invoca | ☑ 23/09 — ejecución `422821` |
| **R3** | Construir `[OPS] CCB - Regresión del pipeline` | El flujo corre los caminos críticos con filas descartables, publica un semáforo por camino, borra sus filas y reporta por correo | ☑ 23/09 — flujo `GVE3iNQ80y5Q9FEw`, **4/4 casos ok** |
| **R4** | Probar la rama de **rechazo/expiración** de la aprobación de IA (F7-03) | Rechazo real en Teams → motivo `aprobacion_rechazada`, revisión manual y **sin consumir ronda** | ☐ pendiente (requiere un clic del usuario) |
| **R5** | Documentar el flujo completo | `docs/FLUJO_COMPLETO_PIPELINE_CCB.md`: el recorrido de negocio de punta a punta + el mapa técnico de los 27 flujos y las 6 tablas | ☑ 23/09 — publicado (10 secciones) |
| **R6** | Limpiar la fila basura de `Cotizaciones_CCB` (`id 21`) | Borrada con `dryRun` previo y confirmación del usuario; la tabla queda sin filas nulas | ☐ pendiente (requiere confirmación) |
| **R7** | Re-auditoría final | Puntaje nuevo publicado con la evidencia de R1–R5 | ☑ 23/09 — **89,5/100** (a 0,5 del umbral) |
| **R9** | v2 de la regresión: cubrir los caminos de envío y del motor | Dos casos más en el flujo de regresión | ◐ 23/09 — camino **envío** hecho (5/5 casos ok); el del **motor** queda pendiente |
| **R8** | Sincronizar entrega | Snapshot, README, tablero, estado y memoria al día; un commit por unidad de trabajo | ☑ 23/09 — 28 archivos, tablero y estado actualizados |

**Orden de ejecución:** R1 (rápido) → R2 → R3 → R5 → R4 y R6 (cuando el usuario pueda) → R7 → R8.

## Notas de ejecución

- Se aplica el [flujo de trabajo de testing](../../docs/TESTING_PIPELINE_CCB.md): validación estructural, lógica aislada,
  subflujo aislado, integración con filas `SOL-PRUEBA-*` y, cuando se puede, tráfico real.
- **Nada se da por bueno sin ejecución real.**
- Los valores reales de anonimización viven en `scripts/anonymization.local.json` (git-ignored), nunca en los workflows.
- Las filas de prueba se borran con `n8n_manage_datatable` (`deleteRows`, con `dryRun` primero): el API público no
  permite borrar filas.

## Evidencia

### R9 — v2 de la regresión · 23/09

**Hecho.** El flujo de regresión pasó de 4 a **5 casos** (se agregó `Cerrar envío`) y de 20 a **16 nodos**: se extrajeron
`[SUB] CCB - Regresion: Preparar filas` (`DgUfcoudk228kOw8`, 7 nodos) y `[SUB] CCB - Regresion: Verificar y limpiar`
(`OuE4SS9Jujz1dVif`, 11 nodos), con lo que el principal quedó bajo el límite de arquitectura y ahora puede crecer.

**Verificación (ejecución `423112`, `success`, 0 nodos con error):** **5/5 casos ok** — `APROBADA`, `CANCELADA`,
`REVISION_MANUAL`, fila en `Errores_CCB` con marca de tiempo y `ENVIADA` en la cotización **y** en la solicitud con
`fecha_envio` — semáforo `5/5` publicado, correo con `{success: true}`, y **limpieza confirmada por `getRows` en las
cuatro tablas** (Cotizaciones, Solicitudes, Criterios y Errores: 0 filas cada una).

**Hallazgos:** (1) al mover nodos a un subflujo hay que revisar las expresiones del flujo que se queda: el nodo del correo
seguía apuntando a un nodo movido (`Referenced node doesn't exist`) y se corrigió a `$json`. (2) El subflujo de contexto
devuelve siempre un item bien formado aunque falte alguna lectura, así que un caso puede correr con datos parciales.
(3) `Cerrar envío` necesita fila en **Solicitudes** y en **Criterios** (las lecturas del contexto no deben quedar vacías
para que la cadena siga).

**Pendiente declarado:** el camino del **motor** (`[SUB] Invocar Motor y Guardar Cotización` → W3) no se agregó: W3 lee
una planilla de Excel con una credencial y su contrato de entrada son los criterios completos, así que exige su propia
sesión de trabajo. Es el último caso que falta para cubrir los caminos críticos.

### R7 y R8 — Re-auditoría de cierre y sincronización · 23/09

`docs/AUDITORIA_BUENAS_PRACTICAS_2026-09-23_CIERRE.md`: **89,5/100** (mañana 87,7 → +1,8). Subieron **Testing**
(11,7 → 12,8: la suite de regresión, la ruta de error y los webhooks verificados en vivo, y el procedimiento de 5
niveles) y **Documentación** (13,4 → 14,0: el pipeline de punta a punta, el comparativo y la ficha de la regresión).
Cinco flujos en 90 o más (W4D 94; W4A, W5A, W5B y W6 en 91) y ninguno por debajo de 85.

Queda **a 0,5 puntos del umbral**, con el camino calculado: la v2 de la regresión (+0,2) y la poda de ejecuciones de
instancia (+0,3) lo cruzan; el rechazo de la aprobación de IA (+0,1) y el cierre de `/metrics` con la credencial (+0,2)
lo consolidan.

Sincronización: 28 archivos de snapshot (27 activos + W2B retirado), README, tablero, estado y esta ficha al día.

### R5 — El pipeline de punta a punta · 23/09

`docs/FLUJO_COMPLETO_PIPELINE_CCB.md`, enlazado desde el README. Diez secciones: el recorrido en una página (diagrama),
los actores, las cinco etapas paso a paso con lo que ve cada persona, las tres ramas de la decisión (con los tres
guardarraíles de la IA), los estados de una propuesta, las tres capas de manejo de error y el diagnóstico en 4 pasos, las
6 tablas y las 12 claves de configuración, el mapa de los 27 flujos, la operación del día a día (cómo cambiar un
destinatario, apagar la IA, lanzar la regresión), las dependencias de terceros y los documentos relacionados.

Incluye el hueco conocido declarado: si el correo de alerta falla, la ejecución queda en `success` y nadie se entera.

_(se completa al cerrar cada tarea: id de ejecución, filas afectadas, correo recibido y commit)_

### R1 — `httpMethod: GET` explícito en el webhook de W4C · 23/09 · commit `089af00`

- **Antes:** `{path: consultar-propuesta, httpMethod: null, authentication: headerAuth, responseMode: responseNode}`.
- **Después:** `httpMethod: "GET"` explícito. `n8n_validate_workflow` → 9 nodos, 0 errores, 0 advertencias.
- **Verificación contra la instancia viva** (no hay token disponible: vive en la credencial `headerAuth`, que el API
  público no puede leer, y en el código de las páginas):
  - `GET /webhook/consultar-propuesta` → **403** `Authorization data is wrong!` → el path está registrado, el método
    GET llega al webhook y la autenticación se exige.
  - `POST /webhook/solicitud-georreferenciada` → **403** y `POST /webhook/decidir-propuesta` → **403** → los otros dos
    webhooks también están vivos y con auth.
  - `GET` a los dos webhooks POST-only → **404** → la restricción de método funciona (n8n responde 404 cuando el método
    no coincide).
- **Pendiente declarado:** la respuesta **200 con credencial válida** no se puede probar sin el token; queda cubierta por
  el uso real de las páginas.

### R2 — Ruta de error compartida con tráfico real · 23/09

**Montaje.** Flujo temporal descartable `TEST DESCARTABLE - R2 ruta de error (7a98c53936)` (`aE4LpvQdltT2orEK`):
webhook (path aleatorio no adivinable) → desenvolver body → `Execute Workflow` al subflujo de error
(`waitForSubWorkflow: true`, la misma configuración que usa W2A) → marcar continuación → responder. Se activó, se disparó
con `curl` y se borró al terminar.

**Carga enviada** (con PII a propósito, para probar el enmascarado):
`{id_solicitud: SOL-PRUEBA-R2, workflow_origen: "W2A (prueba R2)", nodo_fallido: "HTTP - Invocar motor", mensaje_error:
"Fallo simulado: connect ETIMEDOUT al motor http://10.0.0.9:8080/calcular para buzon-de-prueba@example.com (codigo
interno 1234567890123)", subject: "[PRUEBA R2] ..."}`

**Resultado (ejecuciones `422820` llamador y `422821` subflujo, ambas `success`):**

| Qué se verifica | Evidencia |
|---|---|
| **Enmascarado** de PII | La URL, el correo y el número largo quedaron como `<url>`, `<correo>` y `<num>`, **tanto en la fila guardada como en el cuerpo del correo** |
| **Fila registrada** en `Errores_CCB` | `id 128`, `id_solicitud: SOL-PRUEBA-R2`, `nodo_fallido: HTTP - Invocar motor`, `mensaje_error` enmascarado |
| **Marca de tiempo** | `error_timestamp: "2026-09-23 13:46:53"` (zona `America/Bogota`, con `$now.setZone`) |
| **Correo de alerta enviado** | `Outlook - Enviar alerta` → `{success: true}` (no falló en silencio: el nodo tiene `onError: continueRegularOutput`, así que había que mirar su salida) al destinatario de `alertas_email` |
| **El llamador NO se corta** | El flujo de prueba terminó en `Marcar continuacion` y respondió `{llamador_continuo: true, devuelto_por_subflujo: {...}}`: el subflujo devolvió el item y el llamador siguió |
| **Configuración por subflujo** | La salida de `Ejecutar Leer Configuración` es un *passthrough*: conserva los campos del llamador y agrega `_config` |

**Limpieza verificada:** `deleteRows` con `dryRun` coincidió en **exactamente 1 fila** (la de prueba) y luego se borró; el flujo temporal se desactivó y se eliminó (`GET` → **404**); el inventario quedó en **57 workflows**, igual que antes de la prueba.

### R3 — `[OPS] CCB - Regresión del pipeline` · 23/09

**Qué es.** Flujo nuevo `GVE3iNQ80y5Q9FEw`, **20 nodos**, activo. Se dispara a mano (`Trigger manual`) o solo los lunes a
las 6:00 (`Schedule - Regresion semanal`). Recorre cuatro caminos críticos con filas descartables, **verifica el estado
real en las tablas**, publica un semáforo y limpia lo que creó. Ficha completa en
[`docs/FLUJOS_PIPELINE_CCB.md`](../../docs/FLUJOS_PIPELINE_CCB.md) §9.bis.

**Casos y verificación (ejecución `422898`, `success`, 0 nodos con error):**

| Caso | Subflujo ejercitado | Esperado | Obtenido |
|---|---|---|---|
| `aprobar` | `[SUB] CCB - W4D Aprobar` | `APROBADA` | ✅ `APROBADA` |
| `cancelar` | `[SUB] CCB - W4D Cancelar` | `CANCELADA` | ✅ `CANCELADA` |
| `revision` | `[SUB] CCB - W4D Revisión Manual` (motivo `tope`) | `REVISION_MANUAL` | ✅ `REVISION_MANUAL` |
| `error` | `[SUB] CCB - Registrar y Alertar Error` | fila en `Errores_CCB` con `error_timestamp` | ✅ fila con marca de tiempo |

- **Semáforo:** `Metricas_CCB` → métrica `regresion_pipeline` = **`4/4`**, `estado: ok`.
- **Correo de resumen:** `Outlook - Enviar resumen de regresion` → `{success: true}`.
- **Limpieza:** `getRows` con filtro `servicio = SOL-PRUEBA-REGRESION` → **0 filas** en `Cotizaciones_CCB`; filtro
  `id_solicitud = SOL-PRUEBA-REGRESION-ERROR` → **0 filas** en `Errores_CCB`.
- **Validación estructural:** 20 nodos, 0 errores, 6 advertencias informativas (los `executeOnce` intencionales).

**Hallazgos de la construcción:**

1. **La operación de borrado del nodo *Data Table* es `deleteRows`, no `delete`.** La documentación la etiqueta "Delete",
   pero con `delete` el nodo falla con `Cannot read properties of undefined (reading 'execute')` y **no borra nada**. Se
aisló con una sonda de dos variantes: `delete` no borró la fila A, `deleteRows` sí borró la B.
2. **El caso de error deja una fila en `Errores_CCB`** en cada corrida, y el monitor la contaría como error real: se
   agregó un segundo nodo de limpieza para esa tabla (de ahí los 20 nodos).
3. Los nodos de preparación y comparación necesitan `executeOnce`, porque los nodos de lectura devuelven **una fila por
   item** y sin eso cada caso se ejecutaría N veces.
4. La primera corrida (`422861`) falló en el nodo de limpieza; se corrigió la operación y la segunda (`422884`) pasó.

**No verificado (declarado):** que el disparador semanal se dispare solo (no se esperó al lunes); el flujo se probó con
un trigger de webhook temporal que **se quitó después** (el flujo quedó con sus dos disparadores reales). Los caminos
`Cerrar envío` y del motor **no** están cubiertos todavía: son la v2 de este flujo.
