# Flujo de trabajo de testing — Pipeline CCB

**Para qué sirve este documento.** El pipeline se opera sobre una instancia viva de n8n que mueve propuestas comerciales
reales: no hay entorno de staging y no se puede "probar en producción" a ciegas. Este documento define **cómo se prueba
cada cambio**, con qué herramientas, en qué orden, qué evidencia se guarda y qué reglas de seguridad se respetan.

**Regla de oro del proyecto:** un cambio **no está terminado** hasta que se ejecutó al menos una vez y se vio el
resultado. La validación estructural no alcanza: esta misma sesión encontró **tres defectos** (una conexión a un nodo
renombrado, un IF sin su salida de error y un payload que se perdía al cruzar un subflujo) que solo aparecieron al
ejecutar.

**Dimensión del framework:** *Testing /15*. Tras el cierre del 23/09 el pipeline está en **12,9/15**; la distancia al umbral de 90 del
framework está concentrada acá (ver [re-auditoría de cierre del 23/09](AUDITORIA_BUENAS_PRACTICAS_2026-09-23_CIERRE.md), sección 1).

---

## 1. Los cinco niveles de prueba

Se aplican de menor a mayor costo. **No se saltea un nivel** para llegar antes al siguiente: la mayoría de los defectos
se atrapa en los niveles 0 y 1, que cuestan segundos.

| Nivel | Qué prueba | Herramienta | Cuándo | Costo |
|---|---|---|---|---|
| **0. Estructural** | Que el workflow sea válido: nodos existentes, conexiones, expresiones, nodos inalcanzables | `n8n_validate_workflow` (n8n-mcp) | **En cada cambio**, antes de guardar la unidad | segundos |
| **1. Lógica aislada** | El código de un nodo `Code` (máscaras, motivos, cálculos, formateos) | Extraer el `jsCode` y correrlo con `node` contra casos y stubs | En cada cambio que toque lógica de un `Code` | minutos |
| **2. Subflujo en aislamiento** | Un subflujo completo, con una entrada armada a mano | Flujo descartable con `Webhook` → `Execute Workflow` → respuesta, o `n8n_test_workflow` (`pinned`/`direct`) | Al crear o modificar un subflujo | minutos |
| **3. Integración con datos descartables** | El flujo completo contra las Data Tables reales, sin tocar datos de negocio | Filas `SOL-PRUEBA-*` + correos al buzón de prueba + `curl` al webhook real | Al cerrar una fase que toca varios flujos | 15–30 min |
| **4. Tráfico real de negocio** | El camino completo con una propuesta real | Ejecución real observada (cron, webhook del front, clic humano) | Antes de dar una fase por cerrada y en el cierre | variable |

---

## 2. Nivel 0 — Validación estructural

```bash
# por cada workflow tocado
n8n-mcp: n8n_validate_workflow  { "id": "<workflowId>" }
```

Devuelve `valid`, `errorCount`, `warningCount` y el detalle por nodo. **Qué mira y qué atrapa de verdad:**

- `Connection to non-existent node: "X" from "Y"` → típico después de **renombrar un nodo**: el nodo cambia de nombre
  pero la clave/destino en `connections` conserva el viejo. **Renombrar por API no actualiza `connections`.**
- `Node is not reachable from any trigger` → una rama quedó huérfana (se movió o quitó un nodo intermedio y nadie
  reconectó).
- `Output index N on node "X" exceeds...` → una salida conectada que el nodo no tiene.
- `Expression format error ... Mixed literal text and expression requires = prefix` → ojo: en las plantillas HTML de
  100–212 KB es un **falso positivo preexistente** (el runtime acepta el formato y genera PDFs reales). Se documenta, no
  se "arregla" reescribiendo las plantillas.
- `Node has onError: 'continueErrorOutput' but the error output (main[1]) is not connected` → la rama de error quedó sin
  destino.

**Complemento obligatorio (no lo cubre el validador):** un chequeo propio de dos cosas:
1. **Conectividad**: todo nodo (salvo notas) alcanzable desde un trigger, y cada rama termina en un `respondToWebhook`
   cuando el flujo responde a un webhook.
2. **Referencias entre nodos**: cada `$('Nodo')` debe existir **y ser ancestro** de quien lo usa. n8n **no** resuelve
   referencias a ramas hermanas (`Node 'X' hasn't been executed`).

---

## 3. Nivel 1 — Lógica aislada (nodos `Code`)

La lógica de negocio vive en nodos `Code`. Se prueba **sin ejecutar n8n**:

```bash
# 1) extraer el código del nodo
python3 -c "import json;print(json.load(open('workflows/<flujo>.json'))['nodes'][i]['parameters']['jsCode'])" > /tmp/nodo.js
# 2) correrlo con stubs de $json / $('nodo') y varios casos
node /tmp/nodo.js
```

Sirve para: enmascarado de PII (`limpiar()`), elección de motivos (`tope` / `ia_desactivada` / `confianza_baja` /
`aprobacion_rechazada`), formateos, validaciones de valores contra listas cerradas.
**Casos mínimos por nodo:** el camino feliz, un campo faltante, un valor fuera de lista y el caso "dato vacío/null".

---

## 4. Nivel 2 — Subflujo en aislamiento

**Patrón A (recomendado): flujo descartable.** Se crea un workflow temporal con `Webhook` (POST, `responseMode: lastNode`)
→ `Code` que desenvuelve el body (`return [{ json: $json.body }]`) → `Execute Workflow` apuntando al subflujo. Se activa,
se dispara con `curl` y se borra. **La respuesta del webhook es el resultado del subflujo**, así que la verificación es
inmediata. Después se lee la ejecución con `GET /api/v1/executions/{id}?includeData=true` para ver el `runData` nodo por
nodo.

**Patrón B: `n8n_test_workflow`** con `method: pinned` o `direct` (datos fijados). **Limitación:** los métodos oficiales
(`direct`/`pinned`) requieren el MCP de instancia habilitado; si no está, solo sirven para flujos con trigger
`webhook`/`form`/`chat`. Para un `Schedule Trigger` no hay disparo por API: se agrega **un trigger de webhook temporal**
al flujo, se ejecuta, y se quita (procedimiento usado y verificado con el monitor).

**Qué se verifica:** el item de salida, que las ramas de error devuelvan el item de fallo, y que el subflujo no dependa
de datos del llamador que no viajan en el item.

---

## 5. Nivel 3 — Integración con datos descartables

Es el nivel que más valor aporta y el que más cuidado exige. **Nunca se mutan filas reales.**

### Protocolo de datos de prueba

1. **Copiar una fila real** de cada tabla implicada y cambiarle la clave:
   `id_solicitud = "SOL-PRUEBA-<flujo>"` (prefijo `SOL-PRUEBA-` para reconocerlas y borrarlas).
2. **Redirigir todo destinatario al buzón de prueba** (`buzon-de-prueba@example.com` o el que esté configurado como
   destinatario de prueba): así el correo "al cliente" llega a una casilla interna y no a un cliente real.
3. **Usar artefactos reales** cuando el camino los necesita (por ejemplo, un `pdf_url` que exista de verdad en el
   microservicio), así se prueba la descarga de verdad.
4. **Forzar los estados coherentes** de la fila (`APROBADA`, `ENVIADA`, `ronda_correccion: 0/3`) para entrar por la rama
   que se quiere probar.
5. **Disparar por el camino real**: `curl` al webhook de producción con la cabecera de autenticación, o el ciclo
   programado.
6. **Verificar**: la respuesta, la ejecución (`status`, `lastNodeExecuted`, `runData`), el estado final de las filas
   (`estado`, `enviado_a`, `ronda_correccion`) y los registros en `Errores_CCB`.
7. **Borrar las filas de prueba** (ver más abajo) y confirmar que las tablas quedaron como estaban.

### Borrado de las filas de prueba

El API público de n8n **no permite** borrar ni actualizar filas (`DELETE`/`PATCH /rows` → 404/405). Se usa n8n-mcp:

```
n8n_manage_datatable { "action": "deleteRows", "tableId": "<tabla>",
                       "filter": { "type":"and", "filters":[ {"columnName":"id_solicitud","condition":"eq","value":"SOL-PRUEBA-<flujo>"} ] } }
```

Primero con `"dryRun": true` (muestra qué se borraría), después sin `dryRun`. Al cerrar: verificar 0 coincidencias.

### Casos que se prueban en este nivel

| Caso | Cómo se fuerza | Qué se espera |
|---|---|---|
| Camino feliz | Fila con datos completos y estado válido | Respuesta `ok:true`, filas marcadas, correos al buzón de prueba |
| Dato faltante | Fila sin el campo que el flujo necesita | Rama de error + registro en `Errores_CCB` + alerta, sin cortar el pipeline |
| Identificador inválido | Id que no existe en la tabla | Rechazo temprano (400) o error registrado, nunca un 500 mudo |
| Dependencia externa caída | Apuntar a una URL que no responde | Fallo controlado + error registrado (probado con el túnel ngrok caído) |
| Reenvío del mismo pedido | Repetir el mismo POST | No consume una ronda nueva (idempotencia) |
| Aprobación humana | Aprobar/rechazar en Teams | Recálculo + ronda consumida, o revisión manual sin consumir ronda |
| Tope alcanzado | Fila con `ronda_correccion = 3` | Revisión manual, sin consumir ronda |

---

## 6. Nivel 4 — Tráfico real de negocio

Es la regla de oro. Se observa una ejecución real (del cron, del formulario o de la página de revisión) y se registra la
evidencia: id de ejecución, estado, nodos clave, filas afectadas, correo recibido. Si algo no se puede provocar con
tráfico real, **se declara como no verificado** y queda en la lista de pendientes (nunca se da por bueno).

---

## 7. Evidencia y registro

Cada verificación deja cuatro datos, en este orden:

1. **Qué se ejecutó** (id de ejecución y modo: `trigger`, `webhook`, `integrated`, `manual`).
2. **Qué se vio** (respuesta, `status`, `lastNodeExecuted`, salida de los nodos clave).
3. **Qué quedó en los datos** (filas y sus campos, registros de error).
4. **Dónde se registra**: la columna *Cómo se verifica* del [tablero](PLAN_TRABAJO_FRAMEWORK.md), la sección
   correspondiente del [estado](ESTADO_PROGRESO_FRAMEWORK_2026-09-23.md) o la re-auditoría, y la ficha del flujo en
   [FLUJOS_PIPELINE_CCB.md](FLUJOS_PIPELINE_CCB.md) si el contrato cambió.

---

## 8. Seguridad del testing

- **No mutar datos reales.** Todo pasa por filas `SOL-PRUEBA-*`.
- **Nada de secretos en workflows ni en el repo.** La API key vive en el entorno o en una credencial de n8n; los valores
  reales de anonimización en `scripts/anonymization.local.json` (git-ignored).
- **Los correos de prueba van al buzón interno**, nunca a un cliente.
- **Borrar todo lo que se creó** (filas, workflows descartables, triggers temporales) y confirmarlo.
- **Revisar antes de borrar por patrón de nombre**: una limpieza por prefijo puede llevarse workflows que no son de la
  sesión (pasó con un workflow de smoke test preexistente).
- **No tocar producción sin autorización** cuando la prueba implique escrituras en tablas compartidas.

---

## 9. Regresión automatizada (lo que falta para cruzar el umbral de 90)

Hoy el testing es **manual y documentado**. La brecha con la rúbrica se cierra con un flujo de regresión:

**Diseño propuesto — `[OPS] CCB · Regresión — Prueba de regresión`** (trigger manual/semanal):

1. Crea sus propias filas `SOL-PRUEBA-REGRESION` en las tablas implicadas (copias de filas reales).
2. Ejecuta en secuencia los caminos críticos con datos fijados:
   `[SUB] W4D — Aprobar` → `[SUB] W4D — Cancelar` → `[SUB] W4D — Revisión manual (tope)` → `[SUB] Error — Registrar y alertar` →
   `[SUB] Motor — Invocar el motor y guardar` → `[SUB] Envío — Enviar al cliente` → `[SUB] Envío — Cerrar el envío`.
3. Compara los resultados contra lo esperado (respuesta, estado de las filas, registros de error) y publica un
   **semáforo** por camino (una fila por caso en una Data Table `Regresion_CCB` o en el correo de resumen).
4. Borra sus propias filas al terminar y reporta el resultado en un correo al destinatario de alertas.

Con eso, cada cambio de un flujo se valida contra los caminos críticos en un clic, y la dimensión *Testing* sube a la par
de *Observabilidad*.

---

## 10. Checklist por cambio (resumen operativo)

```
[ ] 1. n8n_validate_workflow del/los workflow(s) tocados  → 0 errores
[ ] 2. Chequeo propio: conectividad + referencias $('nodo') que sean ancestro
[ ] 3. Si toqué lógica de un Code: probarla con node y sus 4 casos mínimos
[ ] 4. Si creé/modifiqué un subflujo: probarlo aislado (webhook descartable)
[ ] 5. Si toca datos: filas SOL-PRUEBA-*, correos al buzón de prueba, y borrar al final
[ ] 6. Ejecutar el camino de error, no solo el feliz
[ ] 7. Registrar la evidencia (id de ejecución + resultado) en el tablero y en la ficha del flujo
[ ] 8. Re-exportar el snapshot del repo (scripts/export_workflows.py) y commitear
```
