# Feature: renombrado de los 30 flujos y consistencia del repositorio

**Creada:** 2026-09-24 · **Origen:** [plan de pendientes del 24/09](plan-pendientes-2026-09-24.md)
(bloque B, tareas B1–B3) y la revisión previa del informe de cierre, que detectó seis desfases documentales.

## Objetivo

Aplicar en la instancia viva la [convención de nombres](../../docs/CONVENCION_NOMBRES_Y_CARPETAS_CCB.md) a los **30
flujos** (29 activos + 1 retirado), refrescar los `cachedResultName` de los nodos `Execute Workflow`, y dejar el
repositorio **consistente** con la instancia: snapshot re-exportado, documentación alineada y los desfases numéricos
corregidos.

## Alcance

- **Dentro:** los 30 flujos del proyecto en la instancia viva (solo el campo `name` y los `cachedResultName`); el repo
  `ccb-workflows-git` (script de renombrado, snapshot, README, docs y la ficha ODD); la verificación con la regresión.
- **Fuera:** los **31 flujos inactivos de legado** que viven en la instancia y no son del proyecto (decisión aparte); el
  movimiento de flujos a carpetas (es en la UI, tarea A2); la creación de la credencial *Header Auth* (A1); cualquier
  cambio de lógica, credencial, webhook o conexión.

## Criterio de cierre

1. Los 30 flujos llevan el nombre nuevo en la instancia y **ningún** `cachedResultName` queda con el nombre viejo.
2. Respaldo crudo previo al renombrado, guardado y referenciado en esta ficha.
3. El snapshot del repo re-exportado muestra los nombres nuevos; `grep` no encuentra nombres viejos en `README.md` ni en
   `docs/` (salvo en documentos históricos con nota de errata).
4. Los seis desfases detectados en la revisión quedan corregidos o explícitamente anotados.
5. Prueba de humo: validación estructural de los 30 flujos con **0 errores** y regresión del pipeline en **5/5**.
6. Un commit por unidad de trabajo.

---

## Tareas

| # | Tarea | Criterio de aceptación | Estado |
|---|---|---|---|
| **B1a** | Respaldar los 30 flujos crudos antes de tocar nada | JSON crudo de los 30 en el respaldo, con la fecha del día | ☑ 24/09 — 30 flujos, 1,9 MB, `MANIFEST.json` con sha256 |
| **B1b** | Escribir `scripts/renombrar_workflows.py` con `--dry-run` y `--apply` | El dry-run lista los 30 cambios de nombre y los `cachedResultName` afectados, sin escribir | ☑ 24/09 — 30 PLAN, 47 cachés, 0 PUT |
| **B1c** | Aplicar el renombrado en la instancia | Los 30 con el nombre nuevo; los llamadores con el `cachedResultName` nuevo; 0 cambios en IDs, webhooks y conexiones | ☑ 24/09 — 28 PUT, verificación independiente 0 problemas |
| **B2a** | Re-exportar el snapshot | `workflows/*.json` con los nombres nuevos | ☑ 24/09 — 30 archivos re-exportados |
| **B2b** | Alinear la documentación con los nombres nuevos | README, `FLUJOS_PIPELINE_CCB.md`, `FLUJO_COMPLETO_PIPELINE_CCB.md`, `COMPARATIVO_DEMO_VS_ACTUAL.md` | ☑ 24/09 — 0 nombres viejos en los 7 documentos vivos |
| **B2c** | Corregir los desfases detectados en la revisión | Ver la tabla "Desfases" abajo | ☑ 24/09 — 8 desfases + 2 huecos extra |
| **B3a** | Validar los 30 flujos con `n8n_validate_workflow` | 0 errores, salvo los 4 falsos positivos documentados en B4 | ☑ 24/09 — 29/30 `valid` con 0 errores |
| **B3b** | Regresión del pipeline `5/5` | Ejecución real con semáforo 5/5 | ☑ 24/09 — ejecución `427975`, `5/5` |
| **B4** | Dictamen sobre los 4 errores de validación del subflujo de PDF | Decisión tomada con evidencia, no por defecto | ☑ 24/09 — **falsos positivos por diseño**, no se tocan |
| **B5** | Actualizar las 9 notas fijas que citan el nombre viejo | Las 9 notas con el nombre nuevo; nada más cambia | ☑ 24/09 — 12 sustituciones, 9 flujos, 0 problemas |
| **B6** | Quitar el `pinData` de `[SUB] CCB · Error` | `pinData` vacío y el requisito de limpieza vuelve a cumplirse | ☑ 24/09 — `pinData: {}` confirmado |

**Orden:** B1a → B1b → B1c → B2a → B4 → B5 → B6 → B3a → B2b/B2c → B3b (la corre el usuario).

## Desfases detectados en la revisión previa (2026-09-24)

Verificados contra la instancia viva por API de solo lectura.

| # | Desfase | Valor real | Dónde |
|---|---|---|---|
| 1 | El texto dice "cinco flujos en 90 o más" y cita W5B en 91 | **Siete** (W3 90, W4A 91, W4B 90, W4D 94, W5A 91, W5B **92**, W6 91) | `docs/AUDITORIA_BUENAS_PRACTICAS_2026-09-23_CIERRE.md` §2 |
| 2 | Claves de `Configuracion_CCB`: 10 y 7 según el doc | **12** (confirmado en la tabla `8ChPkhKrjag6Jkcs`) | `docs/ESTADO_PROGRESO_FRAMEWORK_2026-09-23.md:43`, `docs/PLAN_TRABAJO_FRAMEWORK.md:232` |
| 3 | Commits locales sin push: 25 y 48 | **50** | `docs/ESTADO_PROGRESO_FRAMEWORK_2026-09-23.md:89`, `odd/tasks/plan-pendientes-2026-09-24.md:4` |
| 4 | "Testing (11,7 → 12,8)" contra la tabla, que dice 12,9 | **12,9** | `docs/AUDITORIA_BUENAS_PRACTICAS_2026-09-23_CIERRE.md` §1 |
| 5 | "El flujo más grande tiene 19 nodos" sin declarar que excluye sticky notes | 19 sin sticky; **20** con sticky en W1, W2A, W4D y W5B (siguen cumpliendo ≤20) | Informe HTML y re-auditoría de cierre |
| 6 | El informe se presenta como "generado desde la instancia viva" | El **inventario** es vivo; los **nombres** son la convención objetivo y la **evaluación está hardcodeada** en `scripts/generar_informe_html.py` | `docs/informe-pipeline-ccb.html`, `scripts/generar_informe_html.py` |
| 7 | La lista de comprobación marca "Limpieza (sin Pin Data): cumple — Sin pin data en ningún flujo" | **1 flujo activo sí tiene `pinData`**: `[SUB] CCB · Error — Registrar y alertar`, con un item fijado (`TEST-F4-01`, resto del R2 del 23/09) | `docs/AUDITORIA_BUENAS_PRACTICAS_2026-09-23_CIERRE.md` §4, informe HTML §5 |

**Decisión de estilo:** los documentos de auditoría **fechados** son evidencia histórica: no se reescriben en silencio,
se les añade una **nota de errata** de una línea. Los documentos **vivos** (README, tablero, estado, plan del día) se
corrigen directamente.

## Hallazgo B4 — los 4 "errores" del subflujo de PDF son falsos positivos (24/09)

`n8n_validate_workflow` marca **4 errores** en `[SUB] CCB · PDF — Generar el PDF` (`DF3emCmBBBB2HA3i`), uno por cada
nodo `HTML - *` (Información Georreferenciada, Zonificación y Rutero, Ubicación de Nuevo Negocio, Información en Línea):

```
Expression format error in node 'HTML - <servicio>':
Field 'assignments.assignments[0].value' Mixed literal text and expression requires = prefix
```

**No son un defecto.** Son los 4 "Mixed literal" que la auditoría del 23/09 declaraba preexistentes en W3: cuando F4-05
extrajo el subflujo de PDF, se mudaron con las plantillas. La prueba de que **no** hay que "arreglarlos" está en el
propio flujo, en el comentario del nodo Code `Interpolar plantilla HTML`:

> Los templates HTML de los nodos Set contienen placeholders `{{ $json.campo }}` y `{{ .campo }}`. El nodo Set de n8n NO
> interpola estos (un valor sin `=` es texto literal; con `=` n8n intenta evaluar el HTML completo como expresión JS y
> revienta). Por eso la interpolación se hace acá.

Los 4 nodos son `set` tv3.4 con un único campo `html` (212 KB, 138 KB, 132 KB y 116 KB de HTML) y más de 31 marcadores
`{{ }}`. Añadir el prefijo `=` que pide el validador haría que n8n evaluara ~600 KB de HTML como expresión JavaScript:
es exactamente lo que el diseño evita. **Decisión del usuario (24/09): documentarlos como falsos positivos y no tocar las
plantillas.** El validador es heurístico (ve `{{ }}` en un campo de texto y asume expresión n8n); el diseño real mueve la
interpolación al Code node.

Consecuencia para B3a: el criterio "0 errores" se cumple en **29 de los 30** flujos. Los **10 warnings** del resto son
informativos (`executeOnce is enabled`) en los 3 flujos de la regresión.

## Notas de ejecución

- **Nada se da por bueno sin ejecución real** (regla de oro del proyecto): el renombrado cierra con la regresión.
- El renombrado **no cambia IDs ni webhooks**: los tres paths públicos (`solicitud-georreferenciada`,
  `consultar-propuesta`, `decidir-propuesta`) y las credenciales quedan igual.
- Las filas viejas de `Errores_CCB` conservan el nombre anterior en `workflow_origen`: es historial y no se toca.
- La API pública no devuelve la carpeta del flujo: la verificación de carpetas es visual en la UI (tarea A2).
- Valores reales de anonimización en `scripts/anonymization.local.json` (git-ignored), nunca en los workflows.
- Credenciales de la instancia por variables de entorno (`N8N_API_URL`, `N8N_API_KEY`), nunca en el repo.

## Evidencia

### B1 — renombrado de los 30 flujos · 24/09

**Hecho.** Los 30 flujos llevan el nombre de la convención y los 47 `cachedResultName` de los llamadores apuntan al nombre
nuevo. El prefijo `[SUB]` se retiró de W2A, W3, W4B y W5B, según la decisión registrada en la convención.

**Cómo se hizo, con red de seguridad:**

1. **Respaldo crudo** de los 30 flujos en `/tmp/n8n-backup/renombrado-2026-09-24/` (1,9 MB) con `MANIFEST.json`
   (id, nombre, activo, nodos y sha256 por flujo).
2. **Script `scripts/renombrar_workflows.py`** con `--dry-run` (por defecto), `--apply` y `--only <id>`. Solo modifica
   `name` y `parameters.workflowId.cachedResultName`; filtra `settings` (`binaryMode` y `timeSavedMode` son de solo
   lectura) y omite `description` cuando es nula.
3. **Tabla verificada de forma independiente**: 30/30 entradas idénticas a las de la convención, con 30 usos de `·`
   (U+00B7) y 30 de `—` (U+2014), sin guiones ASCII ni `–` (U+2013) y sin punto final.
4. **Dos canarios antes de la corrida completa**: el flujo retirado (payload aceptado) y `[SUB] CCB · Error` (flujo
   **activo** con un cambio de caché). Inspección profunda del canario activo: `active`, `description`, `pinData`,
   `settings`, `connections`, `tags`, `triggerCount`, `isArchived` y `meta` **idénticos**, y la firma estructural
   (tipo, typeVersion, nombre de nodo, credenciales y path de webhook) sin cambios.
5. **Corrida completa**: 28 `PUT` → 27 aplicados y 2 canarios idempotentes.
6. **Verificación independiente del script** (escrita por el padre) de los 30 flujos contra el respaldo: **0 problemas**.
   47 `cachedResultName` correctos, 5 nodos que apuntan a los 30 sin el campo (no se tocan: el campo es opcional y
   n8n resuelve por ID), 30 nombres únicos y **29 activos preservados**.
7. **Idempotencia probada**: segunda corrida de `--apply` → 30 "sin cambios", **0 `PUT`**, salida 0.

**Falso positivo corregido en el verificador.** La primera corrida marcó un FALLO en W1 por `staticData`. Se investigó:
`staticData` guarda el cursor de sondeo del trigger de Outlook y **avanza solo** (`node:Outlook - Nuevo correo recibido`:
`lastTimeChecked` pasó de `2026-09-23T15:57` a `2026-09-24T13:14` sin intervención del `PUT`). Se excluyó `staticData`
de la proyección de comparación, con la nota correspondiente en el docstring. El renombrado de W1 quedó correcto
(nombre nuevo, 3 cachés nuevos, `active: true` y el resto intacto).

**Hallazgo colateral (resuelto en B5):** 9 notas fijas (sticky notes) dentro de los flujos citaban el nombre
**viejo** en su texto, por ejemplo `## [SUB] CCB - Cerrar envío (F4-03/W5B)`. La convención (§4) no las contemplaba; el
usuario decidió actualizarlas.

### B3b — regresión del pipeline · 24/09

**Hecho.** El usuario corrió `[OPS] CCB · Regresión — Prueba de regresión` desde la UI (modo manual). Ejecución
**`427975`**: `status: success`, `finished: true`, 15 nodos ejecutados, **0 nodos con error**, último nodo el envío del
resumen. Duración: 69 s.

**Semáforo publicado:** `Metricas_CCB.regresion_pipeline = 5/5`, con `actualizado_en: 2026-09-24 08:41:19` — la marca
de esta corrida, no la anterior. Los cinco casos:

| Caso | Esperado | Obtenido | ok |
|---|---|---|---|
| aprobar | `APROBADA` | `APROBADA` | ✅ |
| cancelar | `CANCELADA` | `CANCELADA` | ✅ |
| revisión manual | `REVISION_MANUAL` | `REVISION_MANUAL` | ✅ |
| error | fila en `Errores_CCB` con `error_timestamp` | fila con `2026-09-24 08:40:56` | ✅ |
| envío | `ENVIADA` en cotización y solicitud | cotización `ENVIADA` / solicitud `ENVIADA` | ✅ |

**Qué cubre y qué no.** La regresión ejercita el router de decisión (W4D) con sus subflujos de aprobar, cancelar y
revisión manual, el subflujo compartido de error y la cadena de envío con su cierre — todo ya con los nombres nuevos, y
con filas descartables `SOL-PRUEBA-REGRESION-*` que el propio flujo limpia. **No cubre el camino del motor ni la
generación del PDF** (es el caso `motor` que queda pendiente en el plan del día): el renombrado del subflujo de PDF
no quedó ejercitado por esta corrida.

**Conclusión de B3:** el renombrado no rompió ninguna referencia. Los 30 flujos validan sin errores propios (salvo los 4
falsos positivos documentados en B4) y la regresión pasa `5/5` con tráfico real.


### B5 y B6 — notas fijas y `pinData` · 24/09

**Hecho.** 12 sustituciones literales de nombre viejo→nuevo repartidas en las 9 notas fijas, y `pinData` vaciado en
`[SUB] CCB · Error — Registrar y alertar` (el item fijado `TEST-F4-01` era resto de la verificación R2 del 23/09).

**Cómo:** `scripts/actualizar_notas_y_pindata.py` con `--dry-run` (por defecto) y `--apply`. Construye el mapa
viejo→nuevo desde `RENOMBRES` y el respaldo pre-renombrado, sustituye **solo** dentro de `parameters.content` de los
nodos `stickyNote` del `nodes` de nivel superior (ordenando de más largo a más corto) y envía `pinData: {}` únicamente
en el flujo del error. Respaldo previo del estado post-renombrado en `/tmp/n8n-backup/notas-pindata-2026-09-24/`.

**Verificación:**

- `--dry-run`: 10 flujos en PLAN, 12 sustituciones + 1 item fijado, **0 `PUT`**.
- `--apply`: 10 `PUT`, 10 aplicados, verificación por flujo contra el respaldo con "resto sin cambios".
- **Idempotencia**: segunda y tercera corrida → 0 `PUT`, 10 "sin cambios".
- **Verificación independiente del padre** de los 10 flujos contra el respaldo: **0 problemas**; `pinData` de
  `2dY1kaT7I5a0eP2w` = `{}`; **0 nombres viejos** en las notas de los flujos activos; y los 4 nodos `HTML - *` del
  subflujo de PDF **byte-idénticos** (el cambio fue solo la nota).

### B2b y B2c — documentación y desfases · 24/09

**Hecho.** Nombres nuevos en `README.md` y los 6 documentos vivos (fichas, tablas, mapas de dependencias y
llamadores), con los conteos de arquitectura ajustados: **29 activos** (12 principales + 15 subflujos + 2 operativos),
30 archivos de snapshot y 17 flujos nuevos respecto del demo.

**Verificación independiente del padre:** 0 apariciones de los 30 nombres viejos en `README.md` y los 6 documentos
vivos. Los nombres viejos que quedan están donde deben: la tabla "Nombre actual → Nombre propuesto" de la convención (es
el registro de la migración), la ficha histórica de la feature anterior y los documentos de auditoría fechados.

**Los 8 desfases, corregidos:** `Configuracion_CCB` 10→**12** claves (ESTADO) y 7→**12** (PLAN); commits locales
25→**52** (ESTADO) y 48→**52** (plan del día); el conteo de nodos declara que **excluye las notas fijas** (19 sin notas /
20 con notas, criterio ≤20); la fila de *Limpieza (sin Pin Data)* queda marcada como reverificada el 24/09; y los 4
errores del validador del subflujo de PDF quedan declarados como falsos positivos documentados. En los dos documentos de
auditoría **fechados** se añadieron **notas de errata** (Testing 12,9; siete flujos ≥90 con W5B en 92) sin reescribir el
texto original.

**Huecos extra que encontró la revisión del padre y se cerraron en el mismo commit:** el `COMPARATIVO` decía "W3 25 → 16
nodos" mientras el `PLAN` decía 25→17 (diferencia de conteo con/sin notas: ahora dice "17 nodos; 16 sin contar las notas
fijas"), y `TESTING_PIPELINE_CCB.md` seguía con el Testing previo al cierre (11,7 → **12,9**, apuntando a la re-auditoría
de cierre).

**Generador del informe:** `scripts/generar_informe_html.py` ahora declara el conteo con/sin notas y aclara que el
**inventario es vivo** pero la **evaluación por flujo y los pendientes son constantes** de la re-auditoría de cierre del
23/09 (no una medición automática). `docs/informe-pipeline-ccb.html` regenerado con el script.

### Pendientes que esta unidad deja abiertos (requieren decisión)

1. **Nota del subflujo de PDF con un número falso:** la nota fija de `[SUB] CCB · PDF — Generar el PDF` dice "W3 pasó de
   25 a **19** nodos"; el valor real es 17 (16 sin la nota).
2. **Comentario desactualizado en un nodo Code:** `w5b-envio-al-cliente.json` cita `[SUB] CCB - Leer Contexto
   Propuesta` dentro del código de un nodo (no es el `name` ni un `cachedResultName`).
3. **Legado de la instancia:** hay **31 flujos inactivos** ajenos al proyecto (`CCB_Propuestas_v2*`, `CCB - Fase 1/2*`,
   duplicados `copy`, `My workflow 17/19/20`, `TEST_STATE_2TPL`, etc.). El informe cuenta solo los 30 del proyecto. Es
   lo que hay que resolver antes de ordenar carpetas (A2).
4. **Push:** 53 commits locales sin publicar.
