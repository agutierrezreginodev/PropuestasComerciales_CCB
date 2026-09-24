# Plan de trabajo — pendientes para el 2026-09-24

**Punto de partida:** pipeline en **89,5/100** ([re-auditoría de cierre](../../docs/AUDITORIA_BUENAS_PRACTICAS_2026-09-23_CIERRE.md)),
Fases 0–7 del plan de remediación cerradas, 54 commits locales sin push, 29 flujos activos.
**Objetivo del día:** cruzar el **umbral de 90** y dejar el proyecto ordenado para la entrega (nombres, carpetas y push).

---

## Bloque A — Decisiones y UI (tú) · ~35 minutos en total

| # | Tarea | Cuánto | Cierra | Impacto |
|---|---|---|---|---|
| A1 | ✅ **Credencial del monitor** — **hecho 24/09**. **No hubo que crear nada en la UI:** la credencial *Header Auth* (`X-N8N-API-KEY`) ya existía y estaba asignada a los dos nodos HTTP (`HTTP - Leer ejecuciones`, `HTTP - Leer workflows`); lo que faltaba era que el nodo la usara — `authentication: "genericCredentialType"` + `genericAuthType: "httpHeaderAuth"` en ambos. En el camino apareció un segundo bug: un `ReferenceError` por zona muerta temporal en el nodo de métricas que tumbaba el cálculo desde el 23/09, también arreglado | — | La métrica exacta por flujo queda con datos (ejecución `428791`: las 6 métricas publicadas, con `tasa_error_por_flujo` real) | **+0,2 Seguridad** |
| A2 | **Mover los flujos a las carpetas** en la UI (arrastrar; la estructura está en [CONVENCION_NOMBRES_Y_CARPETAS_CCB.md](../../docs/CONVENCION_NOMBRES_Y_CARPETAS_CCB.md) §3) | 5 min | La carpeta del proyecto queda ordenada en 12 · 15 · 2 · 1 | Organización |
| A3 | **Rechazar una tarjeta de aprobación en Teams** (o dejar vencer una) para probar la rama `aprobacion_rechazada` de F7-03 | 5 min | La última rama sin verificar de la corrección con IA | **+0,1 Testing** |
| A4 | **Confirmar el borrado de la fila basura** de `Cotizaciones_CCB` (`id 21`, campos nulos) | 1 min | R6 cerrada | Higiene de datos |
| A5 | **Push de los commits** (decisión: subir o dejar local) | 2 min | Entrega | — |
| A6 | *(Opcional)* **Registrar la instancia** (Settings → Usage and plan) si se quiere administrar carpetas por API | 5 min | Automatización futura de carpetas | — |

> **A3 es la única prueba que no puedo hacer yo:** la aprobación positiva ya se verificó con un clic real; la de rechazo
> usa la misma rama y el mismo procedimiento, y el resultado esperado es `REVISION_MANUAL` con motivo `aprobacion_rechazada`
> **sin consumir ronda**.

> **Legado de la instancia — analizado y resuelto el 24/09.** Había **31 flujos inactivos**. Se verificó que **ningún flujo
> activo invocaba a uno inactivo** y que **no había referencias rotas**, así que ninguno estaba vivo de forma invisible.
> Se clasificaron en: **22** versiones anteriores del pipeline (se conservan), **5** ajenos al proyecto (no se tocaron: la
> instancia es organizacional y parecen de otra área) y **4** de prueba. Se borraron **3** por ser basura clara
> (`My workflow 20`, con 0 nodos; `My workflow 17`, un `errorTrigger` suelto; `TEST_STATE_2TPL`), con respaldo previo.
> El respaldo completo de los 31 está en `/tmp/n8n-backup/legado-2026-09-24/` (1,4 MB) — **no viven en el snapshot del
> repo**, que solo exporta los 30 del proyecto. Estado tras limpiar: **57 flujos** (29 activos + 28 inactivos).
> Para A2, la estructura queda en `12 · 15 · 2 · 1` más una carpeta `99 · Retirados` para lo que se conserva.

---

## Bloque B — Técnico (yo) · ~3 horas

| # | Tarea | Criterio de aceptación | Impacto |
|---|---|---|---|
| B1 | **Renombrar los 30 flujos** por script, según la tabla de la convención, y **refrescar los `cachedResultName`** de los ~19 nodos que llaman a otro flujo | Los 30 con el nombre nuevo; los llamadores apuntan al nombre nuevo; 0 errores de validación | Consistencia |
| B2 | **Actualizar el repositorio** con los nombres nuevos: README, `FLUJOS_PIPELINE_CCB.md`, `FLUJO_COMPLETO_PIPELINE_CCB.md`, `COMPARATIVO_DEMO_VS_ACTUAL.md` y el snapshot | `grep` no encuentra nombres viejos en los docs; snapshot re-exportado | Consistencia |
| B3 | **Prueba de humo del renombrado:** validar los 30 flujos y correr la regresión | Validación 0 errores y regresión `5/5` | Verificación |
| B4 | ✅ **Caso del motor en la regresión** (`[SUB] CCB · Motor — Invocar el motor y guardar` → W3, que lee la planilla Excel y necesita los criterios completos) — **hecho 24/09** | La regresión pasa a `6/6` ✅ (ejecución `428586`) | **+0,1 Testing** |
| B5 | *(Opcional)* **Cerrar el hueco del correo de alerta silencioso**: si el envío de la alerta falla, hoy la ejecución queda en `success` y nadie se entera | El fallo de envío queda registrado y visible | Observabilidad |
| B6 | **Cerrar la sesión** con la evidencia en la ficha de la feature y la memoria del proyecto | Ficha y memoria actualizadas | Trazabilidad |

> **B4 cerrada (24/09).** El caso del motor corre de punta a punta y verifica el **estado real** (no el retorno del
> subflujo): la regresión quedó en **`6/6`** con la ejecución **`428586`** (0 nodos con error, 0 filas sucias). El camino
> destapó **dos hallazgos que no estaban en el plan**: (1) un **bug de producción** en la etapa de PDF — `Normalizar
> Criterios` (W3) descartaba `id_solicitud`, así que el microservicio no persistía el archivo y `pdf_url` quedaba vacío;
> ahora el PDF se persiste y se sirve en `/pdfs/{id_solicitud}.pdf`; y (2) los **routers de cron (W4A/W5A/W6) procesaban
> las filas de prueba** `SOL-PRUEBA-*` cuando un tick caía a mitad de una corrida — se añadió el guardián `Descartar
> filas de prueba`. Detalle completo en [`caso-motor-regresion-ccb.md`](caso-motor-regresion-ccb.md).

---

## Bloque C — Tecnología · depende de su agenda

| # | Tarea | Por qué | Impacto |
|---|---|---|---|
| C1 | **Poda de ejecuciones a nivel de instancia** (`EXECUTIONS_DATA_PRUNE` / `MAX_AGE`) | La retención **por flujo** ya está aplicada (W4A, W5A, W6 y el monitor no guardan las ejecuciones exitosas), pero la poda global es de instancia | **+0,3 Observabilidad** |
| C2 | **Cerrar o restringir `/metrics`** | Hoy está expuesto sin autenticación | **+0,2 Seguridad** |
| C3 | *(Opcional)* **API key con scopes `folder:*`** | Solo si se quiere crear carpetas por script (mover flujos por API no es posible) | — |

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

**Conclusión (actualizada el 24/09):** el trabajo técnico del día y **A1 ya están hechos**, así que el punto de partida
real es **89,8** y el umbral depende de **una sola cosa: C1**, la poda de ejecuciones a nivel de instancia, que es de
Tecnología. Con C1 se cruza (90,1) y C2 lo consolida (90,3). El resto del día es consistencia (carpetas, A2) y las
decisiones que quedan (A3, A4, A5).

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
