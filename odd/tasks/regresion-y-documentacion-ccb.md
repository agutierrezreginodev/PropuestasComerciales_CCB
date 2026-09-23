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
| **R5** | Documentar el flujo completo | `docs/FLUJO_COMPLETO_PIPELINE_CCB.md`: el recorrido de negocio de punta a punta (quién interviene, qué ve, qué pasa en cada rama) + el mapa técnico de los 26 flujos y las 6 tablas; un lector nuevo puede seguirlo sin abrir n8n | ☐ pendiente |
| **R6** | Limpiar la fila basura de `Cotizaciones_CCB` (`id 21`) | Borrada con `dryRun` previo y confirmación del usuario; la tabla queda sin filas nulas | ☐ pendiente (requiere confirmación) |
| **R7** | Re-auditoría final | Puntaje nuevo publicado con la evidencia de R1–R5 | ☐ pendiente |
| **R8** | Sincronizar entrega | Snapshot, README, tablero, estado y memoria al día; un commit por unidad de trabajo | ☐ pendiente |

**Orden de ejecución:** R1 (rápido) → R2 → R3 → R5 → R4 y R6 (cuando el usuario pueda) → R7 → R8.

## Notas de ejecución

- Se aplica el [flujo de trabajo de testing](../../docs/TESTING_PIPELINE_CCB.md): validación estructural, lógica aislada,
  subflujo aislado, integración con filas `SOL-PRUEBA-*` y, cuando se puede, tráfico real.
- **Nada se da por bueno sin ejecución real.**
- Los valores reales de anonimización viven en `scripts/anonymization.local.json` (git-ignored), nunca en los workflows.
- Las filas de prueba se borran con `n8n_manage_datatable` (`deleteRows`, con `dryRun` primero): el API público no
  permite borrar filas.

## Evidencia

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
