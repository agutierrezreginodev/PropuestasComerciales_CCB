# Plan de trabajo — pendientes para el 2026-09-24

**Punto de partida:** pipeline en **89,5/100** ([re-auditoría de cierre](../../docs/AUDITORIA_BUENAS_PRACTICAS_2026-09-23_CIERRE.md)),
Fases 0–7 del plan de remediación cerradas, **32 commits locales pendientes de publicar** (divergencia por reescritura de historia — ver A5), 29 flujos activos.
**Objetivo del día:** cruzar el **umbral de 90** y dejar el proyecto ordenado para la entrega (nombres, carpetas y push).

---

## Bloque A — Decisiones y UI (tú) · ~35 minutos en total

| # | Tarea | Cuánto | Cierra | Impacto |
|---|---|---|---|---|
| A1 | ✅ **Credencial del monitor** — **hecho 24/09**. **No hubo que crear nada en la UI:** la credencial *Header Auth* (`X-N8N-API-KEY`) ya existía y estaba asignada a los dos nodos HTTP (`HTTP - Leer ejecuciones`, `HTTP - Leer workflows`); lo que faltaba era que el nodo la usara — `authentication: "genericCredentialType"` + `genericAuthType: "httpHeaderAuth"` en ambos. En el camino apareció un segundo bug: un `ReferenceError` por zona muerta temporal en el nodo de métricas que tumbaba el cálculo desde el 23/09, también arreglado | — | La métrica exacta por flujo queda con datos (ejecución `428791`: las 6 métricas publicadas, con `tasa_error_por_flujo` real) | **+0,2 Seguridad** |
| A2 | ✅ **Flujos movidos a las carpetas** — **cerrado el 28/09 en la UI**. Conteo real verificado: `01` 12 · `02` 15 · `03` 2 · `99` **28** (23 del proyecto + los 5 ajenos, que se decidió conservar ahí). El 24/09 quedaron 8 históricos sin mover **porque estaban archivados**; el 28/09 13:41 se movieron esos 8 y los 5 ajenos | — | Las carpetas quedan ordenadas y no quedó nada suelto: 12 + 15 + 2 + 28 = **57** = inventario completo de la instancia | Organización |
| A3 | ✅ **Rechazo de la tarjeta de aprobación en Teams** — **hecho 24/09**: la tarjeta se rechazó y la propuesta quedó en `REVISION_MANUAL` con motivo `aprobacion_rechazada` **sin consumir ronda** | — | La última rama sin verificar de la corrección con IA (ejecuciones `429585` y `429598`) | **+0,1 Testing** |
| A4 | ✅ **Fila basura borrada y VERIFICADA** — **hecho 24/09** por el usuario; **verificado el 25/09** leyendo la tabla viva: `Cotizaciones_CCB` quedó con **2 filas**, **0 sin `id_solicitud`** y **0 casi vacías** (la fila `id 21` ya no está). En la misma lectura aparecieron **6 filas de prueba sin limpiar**, borradas el 25/09 (ver abajo) | — | R6 cerrada de verdad | Higiene de datos |
| A5 | ✅ **Historia reescrita publicada** — **ejecutado por el usuario el 25/09 y verificado contra el servidor**. `origin/main` pasó de `59086a2` a **`1aa8a20`**; higiene local ejecutada (`refs/original` borrada, reflog expirado, `gc --prune=now`: 983 objetos sueltos → 0, `.git` 16 MB → 2,7 MB) | 1 comando | Entrega | — |
| A6 | *(Opcional)* **Registrar la instancia** (Settings → Usage and plan) — **ya no es prerrequisito de A2** (A2 se cerró a mano en la UI el 28/09). Solo habilita gestionar carpetas por API (ver `scripts/mover_flujos_a_carpetas.py`) y **es la instancia del cliente**, así que se consulta con Tecnología. **Verificado el 25/09**: el API de carpetas responde `Forbidden — folders unlock on the registered free Community tier (Settings → Usage and plan → register)` | 5 min | Automatización futura de carpetas | — |

> **A3 cerrada (24/09).** La rama de rechazo se verificó **sin clic manual**: fila descartable `SOL-PRUEBA-A3` y decisión
> disparada por HTTP contra `decidir-propuesta`. Ejecución `429585` → la cruda de Teams `{"data": {"approved": false}}` →
> rama falsa del IF; ejecución `429598` → `motivo = 'aprobacion_rechazada'` y `Mark REVISION_MANUAL`; **`Re-invocar motor`
> no corrió** → `ronda_correccion` quedó en `0` (rechazar no consume ronda).
> *Matiz:* la fila terminó en `CANCELADA`, no en `REVISION_MANUAL`, porque el usuario mandó además un `Cancelar` desde la
> página unos segundos después (ejecución `429600`). Son dos decisiones independientes sobre la misma fila y ganó la última:
> no es un defecto del flujo, pero **la evidencia del rechazo hay que buscarla en las ejecuciones, no en la fila**.

> **A4 verificada (25/09) — y de paso, la tabla tenía 6 filas de prueba sin limpiar.** Lectura directa de la instancia viva
> por MCP (no contra el reporte): `Cotizaciones_CCB` tiene **2 filas**, ambas con `id_solicitud`; **0 filas sin
> `id_solicitud`** y **0 filas casi vacías**. La fila `id 21` (19 de 23 campos nulos) **ya no está** → A4 cerrada de verdad.
> *Precisión de criterio:* la frase *"la tabla queda sin filas nulas"* estaba **mal formulada** — hay 7 columnas
> (`plan_seleccionado`, `inversion_inicial`, `pago_mensual`, `num_zonas`, `num_niveles`, `error`, `comentario_fausto`)
> que son `null` en **ambas** filas porque ese servicio no las usa. El criterio correcto es *ninguna fila sin
> `id_solicitud` y ninguna fila casi vacía*.
>
> **Hallazgo y limpieza (25/09):** la lectura destapó **6 filas de prueba** contra la regla del proyecto de borrar las
> `SOL-PRUEBA-*` al cerrar cada verificación: `SOL-PRUEBA-A3` en `Cotizaciones_CCB` (id 90, `CANCELADA`),
> `Criterios_Cotizacion` (id 77) y `Solicitudes_CCB` (id 76, `EN_REVISION`) — restos de la verificación de A3 —, más
> `SOL-PRUEBA-F403` (124), `SOL-PRUEBA-W5B` (126) y `SOL-PRUEBA-W2A` (127) en `Errores_CCB`. Se respaldaron en
> `/home/adrian/ccb-backup/filas-prueba-borradas-2026-09-25.json`, se previsualizaron con `dryRun` (6/6 confirmadas, 1 por
> filtro) y se borraron. **Verificación posterior con filtro server-side `id_solicitud like 'SOL-PRUEBA%'` → 0 filas en
> las cuatro tablas**, y los datos reales intactos (`Cotizaciones_CCB` 1 fila real `id 17` `ENVIADA`;
> `Criterios_Cotizacion` 3; `Solicitudes_CCB` 2; `Errores_CCB` 104).
>
> *Nota de método:* el `count` del API topeó en **100** para `Errores_CCB` (el real era 104), así que la verificación se
> hizo con **filtro server-side**, no con `search` sobre una página.
>
> **Pendiente, no tocado:** en `Errores_CCB` quedan otros marcadores viejos de prueba (`SOL-TEST-0001/0002`,
> `TEST-F4-01`) y decenas de filas con `id_solicitud` vacío. No se tocaron — decisión aparte.

---

### A5 — la divergencia con `origin/main` NO era un push pendiente  ·  ✅ cerrada el 25/09

Auditado el 24/09 (solo lectura). `main` local (32 commits) y `origin/main` (31) **no son ancestro uno del otro**: el
merge-base es `be2939e`. La causa no es trabajo remoto nuevo, sino un **`git filter-branch` local de las 14:30** que purgó
un correo real (`59086a2` → `59a69ac`) y quedó **sin publicar**; encima se agregó `1aa8a20`.

- **Contenido: no se pierde nada.** `--cherry-mark` confirma **31/31** pares equivalentes; el único par no equivalente es
  el propio commit de privacidad (el rewrite cambió su contenido). El diff remoto→local son **3 líneas** en
  `docs/PLAN_TRABAJO_FRAMEWORK.md` (`9772483` → `1d8ade3`) y `odd/tasks/regresion-y-documentacion-ccb.md` (`089af00` →
  `5262486`), que son el arreglo de referencias a los hashes reescritos.
- **La purga está a medias:** el correo sigue en **3 commits de `origin/main`** (0 en la rama local), en
  `refs/original/refs/heads/main` y en **983 objetos sueltos** de `.git` (sin packs). **Sin el force-push, el
  `filter-branch` no sirvió para nada.**
- **Respaldo:** bundle fuera del repositorio. El original (`/tmp/ccb-backup/…`, 231 KB) **se perdió al vaciarse `/tmp`
  entre sesiones**; se regeneró el 25/09 en una ruta **persistente**:
  `/home/adrian/ccb-backup/pre-privacidad-2026-09-24.bundle` (2,5 MB). Ahora es **autocontenido** —
  `git bundle create --all` arrastra también `refs/original/refs/heads/main`, y `git bundle verify` informa
  *"records a complete history"* — así que ya **no requiere la base `f7cfa56`** para restaurar. Verificado de verdad
  (no solo con `bundle verify`): clon `--mirror` en `/tmp`, ambos tips presentes, `git fsck` limpio. Restaurar:
  `git fetch <bundle> 'refs/original/refs/heads/main:refs/heads/main-vieja'`. **No** se creó rama de respaldo a
  propósito: una ref que apunte a la historia vieja mantendría el correo alcanzable y anularía la limpieza local.
  **Lección: un respaldo que sostiene una operación destructiva no va a `/tmp`.**
- **Rollback:** `59086a26b766cedc2b0fb7452b06100428a15ec1`.
- **Comando entregado al usuario** (lease explícito al SHA auditado, aborta si el remoto se movió):
  `git push --force-with-lease=refs/heads/main:59086a26b766cedc2b0fb7452b06100428a15ec1 origin main`
- **Higiene local (ejecutada el 25/09):** `git update-ref -d refs/original/refs/heads/main` →
  `git reflog expire --expire=now --all` → `git gc --prune=now`. Resultado: **0 entradas `filter-branch`** en el reflog,
  **983 objetos sueltos → 0** (1 pack, 833 objetos), `.git` **16 MB → 2,7 MB**, y el objeto `59086a2` **ya no existe
  localmente**.
- **Límite honesto:** GitHub retiene los commits abandonados hasta su propia recolección y siguen accesibles **por SHA
  directo**. Un force-push saca el correo de la *rama*, no del *servidor*; si esa dirección se considera comprometida, la
  mitigación real es cambiarla, no purgar git. Además, cualquier otro clon del repo queda divergente y hay que resetearlo.

> **A5 cerrada (25/09).** El usuario ejecutó el push. Verificado **contra el servidor**, no contra el reporte:
> `git ls-remote` → `origin/main` = **`1aa8a20`**; `git status -sb` quedó sin divergencia (`main...origin/main`);
> `59086a2` **ya no es ancestro** de `origin/main` y sí lo es `59a69ac` (la versión purgada); 97 commits en la rama;
> merge-base = el propio `1aa8a20`.
> **Barrido de la dirección purgada sobre TODA la historia publicada** (no solo el tip): **0 ocurrencias**. El barrido
> completo de direcciones da **15 distintas en la historia vieja vs. 14 en la publicada**, y la única que desaparece es
> `i****@camarabaq.org.co` — exactamente la que el commit de privacidad reemplazó.
> **Equivalencia de contenido re-confirmada post-push contra el bundle** (clon `--mirror` temporal, sin tocar el repo
> local): `--cherry-mark --no-merges` → **56 pares equivalentes**, 4 commits solo del lado publicado y 3 solo del lado
> viejo; divergencia cruda **32 / 31**; merge-base `be2939e`; el diff entre ambos tips sigue siendo las **3 líneas** de
> referencias a hashes. Es decir: nada se perdió y lo único distinto es lo que debía ser distinto.
> **Pendiente:** borrar el bundle cuando la entrega se dé por cerrada.

> **Legado de la instancia — analizado y resuelto el 24/09.** Había **31 flujos inactivos**. Se verificó que **ningún flujo
> activo invocaba a uno inactivo** y que **no había referencias rotas**, así que ninguno estaba vivo de forma invisible.
> Se clasificaron en: **22** versiones anteriores del pipeline (se conservan), **5** ajenos al proyecto (no se tocaron: la
> instancia es organizacional y parecen de otra área) y **4** de prueba. Se borraron **3** por ser basura clara
> (`My workflow 20`, con 0 nodos; `My workflow 17`, un `errorTrigger` suelto; `TEST_STATE_2TPL`), con respaldo previo.
> Esos 31 **no viven en el snapshot del repo** (que solo exporta los 30 del proyecto) y su respaldo en
> `/tmp/n8n-backup/legado-2026-09-24/` **se perdió con la limpieza de `/tmp`** — verificado el 28/09: esa ruta ya no
> existe, así que entre el 24 y el 28/09 n8n fue su única copia. **Resuelto el 28/09**: los **27** flujos que no son del
> proyecto (22 históricos + 5 ajenos; los 3 de prueba se habían borrado el 24/09) quedaron respaldados en
> `/home/adrian/ccb-backup/legado-2026-09-28/` (1,3 MB, `MANIFEST.md` + `manifest.json` con sha256) vía
> `scripts/export_legado.py`. Estado tras limpiar la instancia: **57 flujos** (29 activos + 28 inactivos).
> Para A2, la estructura **quedó** (28/09) en `12 · 15 · 2 · 28`: 23 del proyecto en `99 · Retirados` (el retirado más
> las 22 versiones históricas) y además los 5 ajenos que se decidió conservar ahí — detalle y conteo verificado en la
> [checklist de A2](a2-carpetas-checklist.md).

---

## Bloque B — Técnico (yo) · ~3 horas

| # | Tarea | Criterio de aceptación | Impacto |
|---|---|---|---|
| B1 | **Renombrar los 30 flujos** por script, según la tabla de la convención, y **refrescar los `cachedResultName`** de los ~19 nodos que llaman a otro flujo | Los 30 con el nombre nuevo; los llamadores apuntan al nombre nuevo; 0 errores de validación | Consistencia |
| B2 | **Actualizar el repositorio** con los nombres nuevos: README, `FLUJOS_PIPELINE_CCB.md`, `FLUJO_COMPLETO_PIPELINE_CCB.md`, `COMPARATIVO_DEMO_VS_ACTUAL.md` y el snapshot | `grep` no encuentra nombres viejos en los docs; snapshot re-exportado | Consistencia |
| B3 | **Prueba de humo del renombrado:** validar los 30 flujos y correr la regresión | Validación 0 errores y regresión `5/5` | Verificación |
| B4 | ✅ **Caso del motor en la regresión** (`[SUB] CCB · Motor — Invocar el motor y guardar` → W3, que lee la planilla Excel y necesita los criterios completos) — **hecho 24/09** | La regresión pasa a `6/6` ✅ (ejecución `428586`) | **+0,1 Testing** |
| B5 | ✅ **Cerrar el hueco del correo de alerta silencioso** — **hecho 24/09** con una rama de error en el subflujo compartido que registra el meta-incidente con claves propias | El fallo de envío queda registrado y visible (regresión `428867`, sub-ejecución `428877`) | Observabilidad |
| B6 | ✅ **Cerrar la sesión** con la evidencia en la ficha de la feature y la memoria del proyecto — **hecho 24/09**, completado el 25/09 con el cierre de A5 (push verificado + higiene local) | Ficha y memoria actualizadas | Trazabilidad |

> **B4 cerrada (24/09).** El caso del motor corre de punta a punta y verifica el **estado real** (no el retorno del
> subflujo): la regresión quedó en **`6/6`** con la ejecución **`428586`** (0 nodos con error, 0 filas sucias). El camino
> destapó **dos hallazgos que no estaban en el plan**: (1) un **bug de producción** en la etapa de PDF — `Normalizar
> Criterios` (W3) descartaba `id_solicitud`, así que el microservicio no persistía el archivo y `pdf_url` quedaba vacío;
> ahora el PDF se persiste y se sirve en `/pdfs/{id_solicitud}.pdf`; y (2) los **routers de cron (W4A/W5A/W6) procesaban
> las filas de prueba** `SOL-PRUEBA-*` cuando un tick caía a mitad de una corrida — se añadió el guardián `Descartar
> filas de prueba`. Detalle completo en [`caso-motor-regresion-ccb.md`](caso-motor-regresion-ccb.md).

---

## Bloque C — Tecnología · depende de su agenda

> **La propuesta formal para Tecnología está redactada:** [PROPUESTA_TECNOLOGIA_2026-09-24.md](../../docs/PROPUESTA_TECNOLOGIA_2026-09-24.md).
> Cubre este bloque completo (C1 poda, C2 `/metrics`) más el alojamiento del microservicio de PDF y, como opcional, el
> MCP de instancia. Cada pedido va de caja cerrada y con su verificación del lado del proyecto.
>
> **Estado medido el 25/09 (para no pedir a ciegas):**
> - **C2 sigue abierto:** `GET /metrics` desde internet responde **200 sin autenticación**, 25.902 bytes y **42 familias**
>   de métricas del proceso. Es la evidencia fresca del pedido; el monitor no necesita cambios (la URL es un valor de
>   `Configuracion_CCB`).
> - **La instancia está viva y accesible:** `GET /healthz` → **200** (0,9 s). Ojo con el falso negativo: la herramienta
>   `n8n_health_check` del MCP responde *"Unable to connect to n8n"* (ETIMEDOUT/ENETUNREACH) aunque el `curl` al mismo
>   host funcione. **No usar ese mensaje como prueba de caída**; verificar con `curl`.
> - **C1 (la edad del registro de ejecuciones) no se pudo remedir hoy** con las herramientas disponibles: la auditoría de
>   instancia del MCP devolvió `403 Forbidden` en el audit nativo y su escaneo propio expiró por red, y el resultado fue
>   un **`0 findings` engañoso con `0 workflows scanned`** — no es un "auditoría limpia", es una auditoría que no corrió.
>   El valor del 24/09 (registro hasta el **26 de junio**, ~89 días) sigue siendo la referencia.

| # | Tarea | Por qué | Impacto |
|---|---|---|---|
| C1 | **Poda de ejecuciones a nivel de instancia** (`EXECUTIONS_DATA_PRUNE` / `MAX_AGE`) | La retención **por flujo** ya está aplicada (W4A, W5A, W6 y el monitor no guardan las ejecuciones exitosas), pero la poda global es de instancia | **+0,3 Observabilidad** |
| C2 | **Cerrar o restringir `/metrics`** | Hoy está expuesto sin autenticación | **+0,2 Seguridad** |
| C3 | *(Opcional)* **API key con scopes `folder:*`** | Solo si se quiere gestionar carpetas por script: mover un flujo a una carpeta **sí** es posible (`parentFolderId`, n8n 2.32+), pero exige la instancia registrada (A6) | — |

---

## Orden recomendado del día

1. **B1 + B2 + B3** primero (una sola unidad de trabajo): renombrar, actualizar el repo y verificar con la regresión. Así
   todo lo que se haga después (A2 incluido) ya usa los nombres nuevos.
2. **A1 y A3** en paralelo cuando puedas: no dependen de nada mío.
3. **B4** después: la regresión ya estará verde con los nombres nuevos, así que un caso nuevo se prueba sobre terreno firme.
4. **C1 y C2** cuando Tecnología tenga la ventana.
5. **A5** (push) al final, con todo verificado.

---

## Lo que cruza el umbral de 90

| Escenario | Cálculo | Resultado |
|---|---|---|
| Trabajo técnico del día (B1–B4) — **hecho** | 89,5 + 0,1 (Testing) | 89,6 |
| + A1 — **hecho el 24/09** | 89,6 + 0,2 (Seguridad) | **89,8 ← punto de partida actual** |
| **+ C1 (poda de instancia)** | 89,8 + 0,3 (Observabilidad) | **90,1 ✅ cruza** |
| **+ C2 (`/metrics`)** | 90,1 + 0,2 | **90,3 ✅ consolidado** |

**Conclusión (actualizada el 25/09):** el trabajo técnico del día y **A1 ya están hechos**, así que el punto de partida
real es **89,8** y el umbral depende de **una sola cosa: C1**, la poda de ejecuciones a nivel de instancia, que es de
Tecnología. Con C1 se cruza (90,1) y C2 lo consolida (90,3).

---

## Cierre del 25/09 — qué queda

| # | Pendiente | De quién | Estado |
|---|---|---|---|
| A5 | Publicar la historia reescrita + higiene local | — | ✅ **cerrado el 25/09** (ver arriba) |
| A4 | **Verificar de verdad** el borrado de la fila `id 21` de `Cotizaciones_CCB` | yo | ✅ **cerrado el 25/09** — tabla leída, 0 filas sin `id_solicitud`; y de paso se limpiaron 6 filas de prueba (ver arriba) |
| A2 | Mover los flujos a las carpetas | tú | ✅ **cerrado el 28/09** — 12 · 15 · 2 · 28 = 57; los 8 que faltaban estaban archivados |
| A6 | *(Opcional)* Registrar la instancia — habilita gestionar carpetas por API | tú | ☐ ya no es prerrequisito de A2; se consulta con Tecnología |
| C1 | Poda de ejecuciones de instancia | Tecnología | ☐ **es lo único que cruza el 90** |
| C2 | Cerrar o restringir `/metrics` | Tecnología | ☐ consolida en 90,3 |
| — | Borrar el bundle `/home/adrian/ccb-backup/…` | yo | ☐ cuando la entrega se dé por cerrada |

**A4 quedó cerrada el 25/09** — era el único pendiente de esta lista que podía cerrar yo sin ti. C1 y C2 dependen de la
agenda de Tecnología; la propuesta formal ya está redactada en
[PROPUESTA_TECNOLOGIA_2026-09-24.md](../../docs/PROPUESTA_TECNOLOGIA_2026-09-24.md).

---

## Riesgos y notas

- **El renombrado no cambia IDs ni webhooks**: los tres paths (`solicitud-georreferenciada`, `consultar-propuesta`,
  `decidir-propuesta`) y las credenciales quedan igual, así que **las dos páginas siguen funcionando**. Lo único que se
  actualiza son los `cachedResultName` de los llamadores.
- **Los registros viejos de `Errores_CCB` conservan el nombre anterior** en `workflow_origen`: es historial, no se toca.
- **El túnel del microservicio de PDF** sigue siendo el punto más frágil de producción: si el lunes la regresión falla en
  un caso, revisar el túnel primero.
- **La regresión deja 4 correos por corrida** (error, revisión manual, cierre de envío y resumen) al correo de alertas:
  son identificables por el id `SOL-PRUEBA-REGRESION-*`.
- **No se toca nada sin ejecución real**: cada tarea de este plan cierra con evidencia (id de ejecución, filas, correo).
