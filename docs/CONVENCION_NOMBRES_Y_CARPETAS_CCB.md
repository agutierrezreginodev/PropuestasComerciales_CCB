# Convención de nombres y carpetas — Pipeline CCB

**Para qué sirve.** Define **una sola línea** para nombrar los flujos y para organizarlos en carpetas dentro de n8n, de
modo que la lista del proyecto se lea igual que la documentación: los flujos del negocio primero, los subflujos agrupados
por dominio y los operativos al final.

**Estado actual.** 29 flujos activos + 1 retirado. Los nombres de hoy son inconsistentes: conviven `[SUB] CCB - …` y
`[SUB] - CCB - …`, `Regresion` sin tilde junto a `Regresión`, y cuatro flujos del pipeline (W2A, W3, W4B, W5B) llevan el
prefijo `[SUB]` aunque en el modelo de negocio son etapas del pipeline, no piezas internas.

---

## 1. El patrón

```
[PREFIJO] CCB · CLAVE — Título en español, con tildes
```

| Parte | Valores | Cuándo |
|---|---|---|
| **PREFIJO** | *(vacío)* · `[SUB]` · `[OPS]` · `[RETIRADO]` | Vacío para las etapas del pipeline (lo que el negocio reconoce). `[SUB]` para lo que solo se invoca desde otro flujo. `[OPS]` para lo que opera la plataforma. `[RETIRADO]` para lo que ya no corre. |
| **`CCB`** | siempre | Marca la instancia/proyecto. |
| **Separador** | `·` (punto medio) | Separa la marca de la clave. |
| **CLAVE** | `W1`…`W6` · `Catch-all` · `Error` · `Config` · `Contexto` · `PDF` · `Motor` · `Envío` · `W4D` · `Regresión` | La clave agrupa: todo lo de `Envío` aparece junto, todo lo de `W4D` también. |
| **Separador** | `—` (raya) | Separa la clave del título. |
| **Título** | español, con tildes, sin punto final | Solo minúsculas después de la primera palabra (salvo nombres propios como *Teams*). |

**Reglas de estilo:** tildes siempre (`Regresión`, `Configuración`); `W4D` en mayúsculas; nada de `Workflow N` en el nombre
(el número ya es la clave); sin punto final; sin fechas ni versiones en el nombre.

**Por qué así.** La lista de n8n ordena alfabéticamente: con el prefijo delante, los subflujos quedan juntos y agrupados
por clave (`[SUB] CCB · Envío — …`, `[SUB] CCB · W4D — …`), y las etapas del pipeline quedan arriba, en el orden W1 → W6.

---

## 2. La tabla de renombrado (los 30 flujos)

### Etapas del pipeline (12) — sin prefijo

| ID | Nombre actual | Nombre propuesto |
|---|---|---|
| `w6h0qSblUESIpSVc` | CCB - Workflow 1 - Extracción información del cliente | **CCB · W1 — Extracción de información del cliente** |
| `VChcasvisGKekezR` | [SUB] CCB - Workflow 2A - Guardar Criterios y Cotizar Servicio | **CCB · W2A — Guardar criterios y cotizar** |
| `u6KCMnLwFOp6Ja0N` | CCB - Workflow 2C - Recepción Formulario Externo (Georreferenciada) | **CCB · W2C — Recepción del formulario externo** |
| `cHOIOEFB5nbltN82` | [SUB] CCB - Workflow 3 - Motor Criterios y Precio | **CCB · W3 — Motor de criterios y precio** |
| `7gmpPMBJtEb0W3J5` | CCB - Workflow 4A - Router de Aprobación | **CCB · W4A — Router de aprobación** |
| `5RJdnHDQ8NuWZJG7` | [SUB] CCB - Workflow 4B - Aprobación de Propuesta (Teams) | **CCB · W4B — Aprobación por Teams** |
| `KuLSIzBZgaRIjuSu` | CCB - Workflow 4C - Consultar Propuesta para Revisión | **CCB · W4C — Consultar la propuesta para revisión** |
| `W0TDH4b0tHCNOzFQ` | CCB - Workflow 4D - Procesar Decisión de Propuesta | **CCB · W4D — Procesar la decisión** |
| `gvIn6mbAn2Y1bMRR` | CCB - Workflow 5A - Router de Envío | **CCB · W5A — Router de envío** |
| `XWBHgbmtBubA4gqx` | [SUB] CCB - Workflow 5B - Envío al Cliente | **CCB · W5B — Envío al cliente** |
| `mPwl4qUb0zQkmDHN` | CCB - Workflow 6 - Finalizador de Cotizaciones | **CCB · W6 — Finalizador de cotizaciones** |
| `Dh2lAQTzyoZBpXie` | CCB - Error Workflow (catch-all) | **CCB · Catch-all — Errores no capturados** |

> **Decisión:** W2A, W3, W4B y W5B **pierden** el `[SUB]`. Son etapas del pipeline (aparecen así en el demo y en la
> auditoría) y el prefijo confundía. Que se invoquen con *Execute Workflow* es un detalle técnico que vive en su ficha.
> Si se prefiere la señal operativa de "esto no tiene disparador propio", la alternativa es dejarlos con `[SUB]`; la
> recomendación es no hacerlo.

### Subflujos (15) — prefijo `[SUB]`

| ID | Nombre actual | Nombre propuesto |
|---|---|---|
| `2dY1kaT7I5a0eP2w` | [SUB] CCB - Registrar y Alertar Error | **[SUB] CCB · Error — Registrar y alertar** |
| `Hgy02eqPhnsdJvkq` | [SUB] CCB - Leer Configuración | **[SUB] CCB · Config — Leer la configuración** |
| `GELWpskp0aYJ2zPg` | [SUB] CCB - Leer Contexto Propuesta | **[SUB] CCB · Contexto — Leer el contexto de la propuesta** |
| `DF3emCmBBBB2HA3i` | [SUB] CCB - Generar PDF de Propuesta | **[SUB] CCB · PDF — Generar el PDF** |
| `MHWlUApSFT6gpBHs` | [SUB] CCB - Invocar Motor y Guardar Cotización | **[SUB] CCB · Motor — Invocar el motor y guardar** |
| `AnPJGVWylmKEYWmJ` | [SUB] CCB - Enviar propuesta al cliente | **[SUB] CCB · Envío — Enviar al cliente** |
| `1Zzkrg3dTkTrddgp` | [SUB] CCB - Cerrar envío | **[SUB] CCB · Envío — Cerrar el envío** |
| `D2d9Og6UUvq13TJA` | [SUB] CCB - Cerrar error de envío | **[SUB] CCB · Envío — Cerrar el error de envío** |
| `8j6BCwXkgJCccyO1` | [SUB] CCB - W4D Aprobar | **[SUB] CCB · W4D — Aprobar** |
| `Jgf514VxDINJ8ra3` | [SUB] CCB - W4D Cancelar | **[SUB] CCB · W4D — Cancelar** |
| `iNSErCHs2iw33emJ` | [SUB] CCB - W4D Revisión Manual | **[SUB] CCB · W4D — Revisión manual** |
| `3NAcLF4jaZ1JBw0A` | [SUB] CCB - W4D Corrección IA | **[SUB] CCB · W4D — Corrección con IA** |
| `POeFkqQp8e4cGfY3` | [SUB] CCB - W4D Cierre de Corrección | **[SUB] CCB · W4D — Cierre de la corrección** |
| `DgUfcoudk228kOw8` | [SUB] CCB - Regresion: Preparar filas | **[SUB] CCB · Regresión — Preparar filas** |
| `OuE4SS9Jujz1dVif` | [SUB] CCB - Regresion: Verificar y limpiar | **[SUB] CCB · Regresión — Verificar y limpiar** |

### Operativos (2) y retirado (1)

| ID | Nombre actual | Nombre propuesto |
|---|---|---|
| `ZwBFTBhwS9pjS69X` | [OPS] CCB - Monitoreo del pipeline | **[OPS] CCB · Monitoreo — Métricas del pipeline** |
| `GVE3iNQ80y5Q9FEw` | [OPS] CCB - Regresión del pipeline | **[OPS] CCB · Regresión — Prueba de regresión** |
| `lIcdT6nGd0w1G2i0` | CCB - Workflow 2B - Formulario de Solicitud | **[RETIRADO] CCB · W2B — Formulario antiguo** |

> Las dos piezas de la regresión comparten la clave `Regresión` a propósito: con los prefijos `[SUB]` y `[OPS]` quedan
> adyacentes en la lista y se leen como una familia.

---

## 3. Las carpetas en la UI de n8n

### Lo que se puede y lo que no (verificado)

| Punto | Realidad |
|---|---|
| Anidamiento | **Sí**: n8n soporta carpetas ilimitadas y anidadas |
| Requisito | Instancia **registrada** (Community registrada o plan pago). En esta instancia las carpetas ya funcionan (los 12 flujos originales están en una). **Ojo: que las carpetas funcionen no significa que la instancia esté registrada** — el 25/09 el API de carpetas respondió `Forbidden` con ese motivo exacto. Lo que funciona sin registro es *crear* carpetas y arrastrar flujos **en la UI**; lo que exige registro es hacerlo **por API**. |
| **Mover flujos por API** | **Hoy no se puede *en esta instancia*, pero sí en general.** El API público clásico (`POST`/`PUT /api/v1/workflows`) rechaza `parentFolderId`. El movimiento moderno **sí existe** por otras dos vías: la operación `moveToFolder` de `n8n_update_partial_workflow` y la acción `move` (`transferToFolderId`) de `n8n_manage_folders`. Ambas exigen **API key con scopes `folder:*`** *y* **instancia registrada**. Verificado el **25/09**: responden `Forbidden — folders unlock on the registered free Community tier (Settings → Usage and plan → register)`. **Con A6 (registrar la instancia) hecho, A2 deja de ser un arrastre manual y se puede scriptear.** |
| API de carpetas | Existe (`/projects/{id}/folders`), pero exige una API key con scopes `folder:*` **y** licencia: por eso hoy responde 403. Sirve para *crear* carpetas por script, no para mover flujos |
| Verificación por API | No se puede: `GET /workflows` no devuelve la carpeta del flujo. La verificación es visual en la UI |

### La estructura propuesta

```
📁 Servicios_Información_Cotizaciones_v2.0        ← la carpeta del proyecto (ya existe)
│
├── 📁 01 · Pipeline CCB                          ← 12 flujos: las etapas del negocio
│     CCB · W1 — …   ·  W2A  ·  W2C  ·  W3  ·  W4A  ·  W4B
│     W4C  ·  W4D  ·  W5A  ·  W5B  ·  W6  ·  Catch-all
│
├── 📁 02 · Subflujos CCB                         ← 15 flujos: piezas internas
│     (opcional, si se quiere refinar:)
│     ├── 📁 Compartidos     Error · Config · Contexto · PDF · Motor
│     ├── 📁 W4D             Aprobar · Cancelar · Revisión manual · Corrección IA · Cierre
│     ├── 📁 Envío           Enviar · Cerrar envío · Cerrar error
│     └── 📁 Regresión       Preparar filas · Verificar y limpiar
│
├── 📁 03 · Operativos CCB                        ← 2 flujos
│     Monitoreo · Regresión
│
└── 📁 99 · Retirados                             ← 1 flujo
      [RETIRADO] CCB · W2B — Formulario antiguo
```

**Por qué así:** la carpeta `01` es la que se abre en una reunión (lo que el negocio reconoce); la `02` es la caja de
herramientas; la `03` es lo que se mira cuando algo se rompe; y `99` evita que un flujo viejo confunda a quien entra
nuevo. La numeración ordena las carpetas alfabéticamente en el orden en que se usan.

**Alternativa simple:** si no se quieren cuatro carpetas, alcanza con **dos** (`01 · Pipeline CCB` y `02 · Interno CCB`),
porque los prefijos `[SUB]` y `[OPS]` ya ordenan la lista dentro de cada una.

### Cómo se hace (en la UI, ~5 minutos)

1. En el proyecto, botón de **crear carpeta** → `01 · Pipeline CCB`. Repetir para `02 · Subflujos CCB`, `03 · Operativos CCB` y `99 · Retirados`.
2. **Arrastrar** cada flujo sobre su carpeta (o usar el menú de la tarjeta del flujo, si la versión lo ofrece).
3. Verificar de un vistazo que cada carpeta tenga la cantidad esperada: **12 · 15 · 2 · 1**.
4. Si se quieren las subcarpetas de `02`, crearlas dentro y repetir el arrastre (el anidamiento está soportado).

### Checklist de arrastre — los 30 flujos, uno por uno

Lista literal para no tener que decidir nada en la UI. Total: **12 · 15 · 2 · 1 = 30**.

**📁 01 · Pipeline CCB — 12**

- `CCB · Catch-all — Errores no capturados`
- `CCB · W1 — Extracción de información del cliente`
- `CCB · W2A — Guardar criterios y cotizar`
- `CCB · W2C — Recepción del formulario externo`
- `CCB · W3 — Motor de criterios y precio`
- `CCB · W4A — Router de aprobación`
- `CCB · W4B — Aprobación por Teams`
- `CCB · W4C — Consultar la propuesta para revisión`
- `CCB · W4D — Procesar la decisión`
- `CCB · W5A — Router de envío`
- `CCB · W5B — Envío al cliente`
- `CCB · W6 — Finalizador de cotizaciones`

**📁 02 · Subflujos CCB — 15** *(con el refinamiento opcional de subcarpetas entre paréntesis)*

- `[SUB] CCB · Config — Leer la configuración` *(Compartidos)*
- `[SUB] CCB · Contexto — Leer el contexto de la propuesta` *(Compartidos)*
- `[SUB] CCB · Error — Registrar y alertar` *(Compartidos)*
- `[SUB] CCB · Motor — Invocar el motor y guardar` *(Compartidos)*
- `[SUB] CCB · PDF — Generar el PDF` *(Compartidos)*
- `[SUB] CCB · Envío — Cerrar el envío` *(Envío)*
- `[SUB] CCB · Envío — Cerrar el error de envío` *(Envío)*
- `[SUB] CCB · Envío — Enviar al cliente` *(Envío)*
- `[SUB] CCB · W4D — Aprobar` *(W4D)*
- `[SUB] CCB · W4D — Cancelar` *(W4D)*
- `[SUB] CCB · W4D — Cierre de la corrección` *(W4D)*
- `[SUB] CCB · W4D — Corrección con IA` *(W4D)*
- `[SUB] CCB · W4D — Revisión manual` *(W4D)*
- `[SUB] CCB · Regresión — Preparar filas` *(Regresión)*
- `[SUB] CCB · Regresión — Verificar y limpiar` *(Regresión)*

**📁 03 · Operativos CCB — 2**

- `[OPS] CCB · Monitoreo — Métricas del pipeline`
- `[OPS] CCB · Regresión — Prueba de regresión`

**📁 99 · Retirados — 1**

- `[RETIRADO] CCB · W2B — Formulario antiguo`

> Los subflujos de `02` están ordenados **por grupo**, no por nombre, para que el refinamiento en subcarpetas sea un corte
> contiguo de la lista. Los cinco de `Compartidos` son los únicos que llaman a más de una etapa del pipeline.

---

## 4. Qué hay que actualizar después del renombrado

El nombre del flujo aparece en tres lugares además de n8n, y los tres se actualizan en el mismo trabajo:

1. **Los nodos `Execute Workflow`** guardan un `cachedResultName` con el nombre viejo. No rompe nada (n8n resuelve por
   ID), pero queda desactualizado: hay que refrescarlo en los ~19 nodos que llaman a otro flujo.
2. **El repositorio**: `README.md` (tabla de flujos y conteos), `docs/FLUJOS_PIPELINE_CCB.md` (fichas y mapa de
   dependencias), `docs/FLUJO_COMPLETO_PIPELINE_CCB.md` (mapa técnico), `docs/COMPARATIVO_DEMO_VS_ACTUAL.md` y el
   snapshot (`scripts/export_workflows.py`, que exporta por ID: los archivos no cambian de nombre, solo su contenido).
3. **Las filas de `Errores_CCB`**: el subflujo de error guarda `workflow_origen` con el nombre del flujo que falló, así que
   a partir del renombrado los registros nuevos traen el nombre nuevo (los viejos conservan el anterior: es historial).

**Verificación después del renombrado:** validar los 30 flujos (`n8n_validate_workflow`, 0 errores) y **correr la
regresión** como prueba de humo (espera `5/5`): si el renombrado rompió una referencia, ahí se ve.
