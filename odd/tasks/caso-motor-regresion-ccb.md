# Feature: caso del motor en la regresión del pipeline

**Creada:** 2026-09-24 · **Origen:** tarea **B4** del [plan del 24/09](plan-pendientes-2026-09-24.md): *"Caso del motor en
la regresión (`[SUB] Invocar Motor y Guardar Cotización` → W3, que lee la planilla Excel y necesita los criterios
completos). La regresión pasa a `6/6`"*.

## Objetivo

Añadir un **sexto caso** a `[OPS] CCB · Regresión — Prueba de regresión` (`GVE3iNQ80y5Q9FEw`) que ejercite el **camino
del motor**: preparar los criterios → invocar `[SUB] CCB · Motor — Invocar el motor y guardar` (`MHWlUApSFT6gpBHs`) →
W3 (`cHOIOEFB5nbltN82`) → `[SUB] CCB · PDF — Generar el PDF` (`DF3emCmBBBB2HA3i`), y **verificar el estado real** en las
tablas. El semáforo debe pasar de `5/5` a **`6/6`**.

Es el único camino crítico del pipeline que la regresión no cubre, y de paso pasa por el subflujo de PDF, cuyo
renombrado (24/09) no quedó ejercitado por tráfico real.

## Alcance

- **Dentro:** el flujo de regresión, su subflujo `[SUB] CCB · Regresión — Verificar y limpiar`
  (`OuE4SS9Jujz1dVif`) y el snapshot del repo; la documentación del testing y la ficha del flujo.
- **Fuera:** W3, el subflujo del motor y el subflujo de PDF (**no requieren cambios**); los otros 5 casos de la
  regresión (deben seguir pasando sin tocarlos); el microservicio de PDF y la planilla Excel (dependencias externas que
  solo se verifican).

> **Enmienda de alcance (24/09, tras la primera corrida real).** El supuesto *"W3 y el subflujo de PDF no requieren
> cambios"* resultó **falso**: el caso del motor encontró un bug de producción que vive en esos dos flujos. Se incorporan
> al alcance en la sección **Hallazgo** de abajo.

## Criterio de cierre

1. El caso del motor corre de punta a punta y **verifica el estado real** en `Cotizaciones_CCB`, no el retorno del
   subflujo.
2. **Verificación observable:** fila con `id_solicitud = 'SOL-PRUEBA-REGRESION-MOTOR'` y
   `estado = 'PROPUESTA_GENERADA'`, `valor_total > 0`, `fecha_calculo` presente, `pdf_url` presente, y **ninguna** fila en
   `Errores_CCB` para ese `id_solicitud`.
3. **Semáforo `6/6`** publicado en `Metricas_CCB`, con los 6 casos en el detalle.
4. **Sin filas sucias** al terminar, en las 4 tablas, **tanto si el caso pasa como si falla**.
5. **Ningún flujo supera los 20 nodos.**
6. **Ejecución real** con `6/6` (evidencia: id de ejecución).
7. Los 5 casos anteriores siguen en verde.
8. Un commit.

---

## Diseño (verificado contra la instancia viva el 24/09)

### Punto de inserción

Cadena viva del flujo principal: `Ejecutar Cerrar envio` → `Ejecutar Verificar y limpiar` → `Outlook - Enviar resumen de
regresion`. El caso nuevo se **intercala** entre el cierre de envío y la verificación.

### Nodos a añadir — +2 en el flujo principal (16 → 18, límite 20 ✓)

| Nodo | Tipo | Qué hace |
|---|---|---|
| `Preparar caso motor` | `code` con `executeOnce: true` | Emite **un** item con el contrato del motor y `id_solicitud = 'SOL-PRUEBA-REGRESION-MOTOR'` |
| `Ejecutar Motor` | `executeWorkflow` → `MHWlUApSFT6gpBHs` | Invoca el subflujo del motor (entrada passthrough: el item tal cual) |

### El contrato del motor (replicado de W2A, su llamador real)

`id_solicitud`, `servicio`, `tipo_organizacion`, `municipios`, `sectores`, `tamano_empresa`, `activos_min`,
`activos_max`, `activos_entre`, `activos_y`, `ventas_min`, `ventas_max`, `ventas_entre`, `ventas_y`,
`indiferente_ventas`, `tipo_servicio`, `nombre_solicitante`, `razon_social`, `email_solicitante`, `telefono_solicitante`,
`ciudad`.

Valores para el caso — **copiados de una propuesta real que funcionó** (`SOL-20260916134302`): esa fila tiene
`total_registros = 1929`, `valor_total = 1504755`, `pdf_url` presente y `servicio = 'Información Georreferenciada'`. Es
decir, la combinación de criterios está **probada en producción**, así que el caso no es un experimento:

```js
{
  id_solicitud: 'SOL-PRUEBA-REGRESION-MOTOR',
  servicio: 'Información Georreferenciada',      // con tilde: el Switch del PDF compara exacto
  tipo_servicio: 'Georreferenciada',             // el valor que valida el gate de W3
  tipo_organizacion: 'Personas Jurídicas; Personas Naturales; Establecimientos; Entidades sin ánimo de lucro',
  municipios: 'Todo el Departamento del Atlántico',
  sectores: 'Comercio al por mayor y al por menor',
  tamano_empresa: 'Microempresas; Pequeñas empresas; Medianas empresas; Grandes empresas',
  indiferente_ventas: true,
  nombre_solicitante: 'Solicitante de prueba',
  razon_social: 'Empresa de prueba',
  email_solicitante: 'pruebas@ejemplo.test',     // dominio reservado por RFC 2606
  telefono_solicitante: '3000000000',
  ciudad: 'Barranquilla',
}
```

**Sin `total_registros`.** El motor admite `total_registros` como *override* que **salta** todo el filtrado contra la
planilla Excel, pero usarlo haría un test más débil y menos honesto (parecería validar el conteo sin validarlo). Con los
criterios reales se ejercita el camino completo: normalización de criterios, lectura de la planilla, resolución del
sector canónico, filtrado y conteo, precio, PDF y guardado. Las aserciones son de **rango** (`total_registros > 0`,
`valor_total > 0`), nunca de valor exacto, para que el caso no se rompa cuando la base de empresas crezca.

### Verificación — `[SUB] CCB · Regresión — Verificar y limpiar`

En `Comparar resultados` (el `X/Y` es **derivado** de `filas.length`, así que el `6/6` sale solo):

- Añadir la sexta entrada al arreglo `casos`:
  `{ caso: 'motor', id: 'SOL-PRUEBA-REGRESION-MOTOR', esperado: 'PROPUESTA_GENERADA con valor_total, fecha_calculo y pdf_url' }`
- Añadir una rama `motor` con lógica propia (no basta `estado === esperado`): comprobar `estado`, `total_registros > 0`,
  `valor_total > 0`, `fecha_calculo`, `pdf_url` y la **ausencia** de fila de error. El texto de `obtenido` debe permitir
  diagnosticar cuál de las condiciones falló.

### Limpieza — 0 nodos nuevos, 2 ediciones

El conflicto real: el motor escribe `Cotizaciones_CCB.servicio` con el valor que recibe, y la limpieza actual filtra
`servicio = 'SOL-PRUEBA-REGRESION'`. Con el valor canónico (necesario para el PDF) esa fila **no se limpiaría**. Y si el
motor falla, registra en `Errores_CCB` con `id_solicitud = 'SOL-PRUEBA-REGRESION-MOTOR'`, que el limpiador actual
**tampoco** borra (solo borra `…-ERROR`).

Solución verificada: el nodo `Data Table` soporta `matchType: 'anyCondition'` (el nodo lo trae como valor por defecto;
los existentes usan `allConditions` explícito). Se añade una segunda condición a dos nodos y se cambia su `matchType`:

| Nodo | Filtro resultante (`anyCondition`) |
|---|---|
| `Data Table - Limpiar cotizaciones` | `servicio = 'SOL-PRUEBA-REGRESION'` **o** `id_solicitud = 'SOL-PRUEBA-REGRESION-MOTOR'` |
| `Data Table - Limpiar errores` | `id_solicitud = 'SOL-PRUEBA-REGRESION-ERROR'` **o** `id_solicitud = 'SOL-PRUEBA-REGRESION-MOTOR'` |

`Cotizaciones_CCB` **sí tiene** columna `id_solicitud`, así que la condición es de clave exacta (no hace falta prefijo).
El subflujo de limpieza queda en **11 nodos**.

### Sin sembrar filas

No se añade `MOTOR` a los arreglos `casos` de `[SUB] CCB · Regresión — Preparar filas`: el camino del motor **no lee**
`Solicitudes_CCB` ni `Criterios_Cotizacion`, y su propio `Data Table - Guardar Cotización` hace *upsert* (inserta si la
fila no existe). Menos piezas en movimiento; la limpieza por `id_solicitud` cubre la fila creada.

## Riesgos

- **El caso acopla la regresión a dos dependencias externas**: el microservicio de PDF y la planilla Excel de W3. Si
  cualquiera falla, el caso falla y el semáforo se pone rojo por una causa ajena al código. Verificado el 24/09: el
  microservicio responde (`/health` 200, `/html-pdf` devuelve un PDF real de 7 KB) y el nodo Excel de W3 está
  configurado con IDs reales en la instancia (`readRows`, hoja `BD` del libro `BD_Empresas CCB`, `alwaysOutputData`,
  `onError: continueErrorOutput`).
- **Si el motor falla**, deja fila en `Errores_CCB`, que además contamina la métrica de errores del monitor. Por eso la
  limpieza por `id_solicitud` se aplica **antes** de dar el caso por cerrado.
- **El flujo de regresión es producción**: corre solo los lunes a las 6:00. El cambio entra en la corrida semanal.
- **Tildes**: cualquier valor de servicio sin tilde cae en "servicio no reconocido" en el `Switch` del PDF. Es un fallo
  silencioso; el caso lo detecta porque exige `pdf_url` presente.

## Hallazgo — bug de producción que encontró el caso del motor (24/09)

**La primera corrida real dio `5/6`, y ese es el valor del caso:** los 5 anteriores siguen verdes y el nuevo falló en una
sola condición, `pdf_url`, delatando un bug real que ningún otro control cubría.

```
FALLO motor: esperado PROPUESTA_GENERADA con total_registros>0, valor_total>0 y pdf_url
      obtenido: cotizacion PROPUESTA_GENERADA / total 1929 / valor_total 1504755 / pdf no
```

**Evidencia (ejecución `428251` y sub-ejecuciones `428267`, `428268`, `428271`):** el PDF se generó (el nodo HTTP corrió
sin error) pero `Adjuntar PDF_URL` devolvió **`PDF_URL = null`**.

**Causa raíz.** En W3, `Normalizar Criterios` empieza con `const row = $json` y devuelve un **objeto construido con 40
campos en el que `id_solicitud` no está**. A partir de ahí el identificador desaparece de toda la cadena posterior:

- la llamada HTTP manda `id_solicitud` vacío, y el microservicio **solo persiste el PDF si lo recibe**
  (`if (options.id_solicitud) fs.writeFileSync(...)`), así que el archivo no se guarda;
- `Adjuntar PDF_URL` construye `BASE_URL + '/pdfs/' + null + '.pdf'` → `null`;
- el motor guarda `pdf_url` vacío en `Cotizaciones_CCB`;
- la pista está en el propio código: `nombre_archivo = (criterios.id_solicitud || numeroPropuesta) + …` — ese respaldo
  existe precisamente porque el campo nunca llega.

**Por qué era silencioso.** `IF - ¿PDF generado?` solo comprueba `$json.ok === true`, y ese `ok` viene **heredado del
cálculo**. Un `PDF_URL` nulo pasaba como éxito. La última propuesta **real** es del **16/09**, anterior a la extracción
F4-05 (23/09): no se había generado ninguna desde entonces.

**El arreglo (dos cambios):**

1. **W3 · `Normalizar Criterios`** — añadir `id_solicitud: row.id_solicitud` al objeto que devuelve. Arregla de raíz la
   persistencia en el microservicio, el `pdf_url` de la fila y el `nombre_archivo`.
2. **`[SUB] CCB · PDF` · `Adjuntar PDF_URL`** — cuando no puede construir la URL, devuelve además `ok: false` con el
   motivo y `nodo_fallido`. **Decisión de implementación:** se endurece **ahí** y no en la condición del `IF`, porque el
   camino falso del IF pasa por `Data Table - Registrar error infra (PDF)` → `Restaurar resultado de error`, y ese nodo
   **copia el item del subflujo de PDF**, que en ese escenario traería `ok: true` heredado: quedaría una fila de error
   registrada y a la vez un `ok: true` devuelto. Poniendo la señal en el nodo que sí sabe que falló, el IF existente hace
   lo correcto y el `mensaje_error` es útil.

**Verificación del arreglo:** la corrida real debe volver a dar `6/6` con `pdf_url` presente, y el PDF debe quedar
persistido y servible en el microservicio (`/pdfs/{id_solicitud}.pdf`).

## Hallazgo 2 — los routers de producción pisan las filas de prueba (preexistente)

La corrida de verificación del arreglo (`428440`) dio `5/6` con un caso distinto en rojo: `aprobar → ERROR_ENVIO`. **No
tiene relación con el caso del motor ni con el arreglo del PDF**; es un defecto preexistente que la corrida destapó por
pura coincidencia de reloj.

**Qué pasó.** W4A y W5A son **routers por cron cada 15 minutos** que leen `Cotizaciones_CCB` filtrando por estado
(`PROPUESTA_GENERADA` y `APROBADA`) y **no excluyen filas de prueba**. La corrida arrancó a las 15:14:48 y dura ~110 s,
así que el tick de las 15:15 cayó en medio: W5A tomó `SOL-PRUEBA-REGRESION-APROBAR`, la marcó `EN_ENVIO`, invocó W5B
**cinco veces** y el fallo la dejó en `ERROR_ENVIO`. Evidencia literal de W5B:
`{"id_solicitud": "SOL-PRUEBA-REGRESION-APROBAR", "servicio": "SOL-PRUEBA-REGRESION", …, "estado_actual": "ERROR_ENVIO", "pdf_url": null}`.

**Las dos consecuencias:**

1. **La regresión es flaky por diseño**: ~`110/900` ≈ **12 % de probabilidad de solape** con un tick en cada corrida. Las
dos corridas anteriores pasaron por suerte de reloj.
2. **Los routers actúan de verdad sobre datos de prueba**: intentan enviar correos y registran errores. Esta corrida dejó
   una fila sucia en `Errores_CCB` con `workflow_origen='desconocido'`, que la limpieza no cubre (no es `-ERROR` ni
   `-MOTOR`).

**La clase completa (3 flujos, verificada recorriendo los 29 activos):** los únicos que leen `Cotizaciones_CCB` filtrando
por `estado` son **W4A** (`PROPUESTA_GENERADA`), **W5A** (`APROBADA`) y **W6** (`ENVIADA`, diario 3am). Los tres chocan
con la regresión: W4A con la fila del motor (`PROPUESTA_GENERADA`), W5A con la del caso `aprobar`, y W6 con la del caso
`envio` (si un tick cae dentro de una corrida manual).

**El arreglo: un guardián por flujo.** Se inserta un nodo `Code` entre la lectura y `Validar id_solicitud presente` que
descarta silenciosamente las filas cuyo `id_solicitud` empieza por `SOL-PRUEBA`. Si no queda ninguna, devuelve una lista
vacía y la cadena se detiene sin error. **No se reutiliza el `IF` existente a propósito**: su rama falsa va a
`Preparar error - id_solicitud faltante` → `Registrar-y-Alertar`, así que excluir una fila de prueba por ahí **ensuciaría
`Errores_CCB`**, que es justo lo que se quiere evitar. El nodo `Data Table` **no soporta operadores** (solo igualdad y
`anyCondition`/`allConditions`), así que la exclusión no se puede expresar como filtro.

**Coste:** +1 nodo en cada flujo (W4A 9→10, W5A 12→13, W6 11→12); los tres quedan muy por debajo del límite de 20.

## Evidencia

**Las tres corridas reales, en orden:**

| Corrida | Resultado | Qué aportó |
|---|---|---|
| `428251` | `5/6` | Los 5 casos anteriores verdes; el motor falló solo en `pdf_url` → **encontró el bug de producción** |
| `428440` | `5/6` | El caso del motor **pasa** y el PDF queda persistido (995.881 bytes); el rojo vino del tick del cron que pisó la fila de `aprobar` → **encontró el segundo bug** |
| `428586` | **`6/6`** | Corrida definitiva: 0 nodos con error, 0 filas sucias, PDF de 995.995 bytes servible |

**Verificaciones independientes del padre** (no las de los subagentes):

- **Caso del motor**: el payload llevaba las tildes correctas y **sin** `total_registros`; la cadena quedó
  `Ejecutar Cerrar envio → Preparar caso motor → Ejecutar Motor → Ejecutar Verificar y limpiar`; 18 nodos; el diff contra
  el respaldo solo traía los cambios previstos; y `node --check` confirmó que el `jsCode` es JavaScript válido.
- **Bug del `pdf_url`**: `id_solicitud` como primer campo de `Normalizar Criterios`; rama de fallo en
  `Adjuntar PDF_URL`; los 4 nodos `HTML - *` **byte-idénticos** al respaldo; `IF - ¿PDF generado?` sin tocar; y el PDF
  servible en `/pdfs/SOL-PRUEBA-REGRESION-MOTOR.pdf`.
- **Guardián**: presente en los 3 flujos **y también en el grafo publicado** (`activeVersion`), que es lo que usa el cron;
  cadena correcta; conteos 10/13/12; diff sin nada más. Prueba de lógica con `node`: descarta las cuatro filas de prueba
  (`-APROBAR`, `-MOTOR`, `-X`, `-F403`) y deja pasar la real.
- **Guardián bajo colisión real**: se sembró una fila `SOL-PRUEBA-GUARDIAN-*` en estado `APROBADA` y se esperó al tick de
  W5A de las 15:45:25. La fila **quedó intacta**, W5B **no** se ejecutó y **no** apareció ninguna fila nueva en
  `Errores_CCB`. Es la única prueba que demuestra el efecto, no solo la intención: la corrida `428586` no cayó sobre
  ningún tick.

**Residuo de la prueba (declarado):** el `dryRun` de `insertRows` de la herramienta MCP **no se respetó** y sembró la fila
**dos veces** (ids 70 y 71). No se pudieron borrar: todas las formas del parámetro `filter` de `deleteRows` fallan con
`Invalid input` y la API pública no tiene endpoint de borrado de filas. Quedan **inertes** (estado `APROBADA`, y el guardián
ímpide que W5A las toque) y **el limpiador de la propia regresión las borra en la próxima corrida**, porque su filtro es
`servicio = 'SOL-PRUEBA-REGRESION'` y esas filas llevan exactamente ese valor.

**Documentación:** los 6 casos en `docs/TESTING_PIPELINE_CCB.md`, el guardián en el nuevo §9.quater de
`docs/FLUJOS_PIPELINE_CCB.md`, la persistencia del `pdf_url` en `docs/FLUJO_COMPLETO_PIPELINE_CCB.md`, B4 en el plan del
día, y el informe HTML regenerado. Se corrigieron en el generador dos entradas del `PEND` que el trabajo de hoy había
dejado falsas (el caso del motor ya no falta, y el nodo Excel de W3 **sí** tiene reintentos: 3×2 s).

## Enmienda de alcance

El encargo era solo añadir un caso de prueba. Terminó arreglando **dos bugs de producción** (`pdf_url` nunca persistido y
los routers pisando datos de prueba) más un guardián en 3 flujos de producción. Todo salió de la evidencia de las
corridas, no de suposiciones, y cada paso se verificó contra la instancia con respaldo previo.
