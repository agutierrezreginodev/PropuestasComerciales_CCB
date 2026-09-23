# ODD — Mejoras del framework de buenas prácticas CCB

**Objetivo:** ejecutar todas las mejoras restantes del plan de remediación del framework
(*Arquitectura e Ingeniería de Automatización en n8n*, rúbrica de 6 dimensiones / 100 puntos),
para llevar el pipeline CCB de **67,3/100** a la mayor puntuación alcanzable antes de la
verificación con tráfico real.

**Tablero canónico:** [`docs/PLAN_TRABAJO_FRAMEWORK.md`](../../docs/PLAN_TRABAJO_FRAMEWORK.md) — este documento **no** lo reemplaza.
Cada tarea de acá corresponde a un `ID` (`F4-02`, `F5-01`, …) del plan y se marca allí también.
La evidencia por fase vive en [`docs/AUDITORIA_BUENAS_PRACTICAS_2026-09-22.md`](../../docs/AUDITORIA_BUENAS_PRACTICAS_2026-09-22.md)
y el estado global en [`docs/ESTADO_PROGRESO_FRAMEWORK_2026-09-22.md`](../../docs/ESTADO_PROGRESO_FRAMEWORK_2026-09-22.md).

## Decisiones de alcance (2026-09-23)

| Decisión | Elección |
|---|---|
| Modo de aplicación | Aplicar en la instancia viva vía API REST + re-exportar el snapshot del repo |
| F3-02 (backoff exponencial real en W3) | **Diferido definitivamente.** n8n no soporta backoff nativo; reestructurar el camino crítico del motor (PDF sobre túnel ngrok) tiene relación riesgo/beneficio mala. Se cierra como desviación por límite de plataforma, con máximo nativo 5×5000 aplicado. |
| F4-04 (consolidación de criterios duplicada) | **N/A.** Apunta a W2B, retirado y fuera de alcance desde 17/09. |
| F7-03 (mover la aprobación humana antes del recálculo) | **Se implementa.** Cambia el comportamiento de negocio: ninguna ronda se consume sin autorización humana. |
| Push a GitHub | No sin pedido explícito. Todo queda en commits locales. |
| Regla de oro | Ningún cambio se da por bueno sin ejecución real. Al cerrar cada unidad se anota qué quedó verificado y qué no. |

## Unidades de trabajo

| # | Unidad | IDs del plan | Estado | Verificación | Commit |
|---|---|---|---|---|---|
| 1 | Configuración centralizada: Data Table `Configuracion_CCB` | F5-01 | ☑ | Lectura de prueba devuelve las 8 claves | `f5-config-centralizada` |
| 2 | Configuración centralizada: reemplazar correo/correos hardcodeados | F5-02 | ☑ | El correo vive en `alertas_email`; lo consumen subflujo de error, catch-all y W4D | `f5-config-centralizada` |
| 3 | Configuración centralizada: URL del microservicio y datos del asesor fuera de los nodos | F5-03, F5-04 | ☑ | Sin literales de correo/URL/chatId en los nodos de los 13 flujos | `f5-config-centralizada` |
| 4 | Observabilidad: `timeout` explícito en llamadas HTTP | F6-01 | ☑ | 60s en los dos nodos HTTP del pipeline | `be0ac78` |
| 5 | Observabilidad: límite/paginación en lecturas sin tope | F6-02 | ☑ | 100 filas por ciclo en las 3 colas | `be0ac78` |
| 6 | Observabilidad: enmascarar PII antes de logs y alertas | F6-03 | ☑ | `limpiar()` en subflujo de error, catch-all y W4D; W2C verificado | `be0ac78` |
| 6b | Observabilidad: sellar `error_timestamp` y monitorear las 4 métricas | F6-05 | ☑ | Flujo `[OPS]` horario verificado + 8 nodos de error sellados | `ops-monitoreo` |
| 7 | Arquitectura: subflujo `[SUB] - CCB - Leer Contexto Propuesta` | F4-02 | ☑ | W4B 14→12, W4C 12→10, W4D 50→48; verificado con datos reales | `f4-02` |
| 8 | Arquitectura: dictamen sobre separar PDF de cálculo de precio | F4-05 | ☑ | Dictamen: separar en sesión dedicada con PDF real; binario no consumido aguas abajo (verificado) | `f4-05` |
| 9 | Arquitectura: partir W4D en subflujos por rama | F4-03 | ☑ | W4D 54→19 nodos + 5 subflujos; 3 caminos verificados con tráfico real | `f4-03` |
| 9b | Bug: las alertas de error perdían el detalle (update de Data Table antes del subflujo) | F4-03 | ☑ | Orden invertido en W4B/W5A/W6/cierre; verificado con ejecución real | `f4-03` |
| 10 | Guardarraíles de IA: `confianza: baja` → revisión humana | F7-01 | ☑ | `IF - ¿Confianza suficiente?` → revisión manual sin consumir ronda | `f7-01-02` |
| 11 | Guardarraíles de IA: kill switch de la corrección asistida | F7-02 | ☑ | Clave `ia_correccion_habilitada` en `Configuracion_CCB` | `f7-01-02` |
| 12 | Guardarraíles de IA: aprobación humana antes del recálculo | F7-03 | 🔶 | Dos caminos (Teams `sendAndWait` vs. página de revisión): decisión del usuario pendiente | — |
| 13 | Catch-all con diseño propio | F4-01 (pendiente) | ☐ | Contrato adaptado, sin perder fidelidad de diagnóstico | — |
| 14 | Cierre documental: re-auditoría, tablero y estado actualizados | — | ☐ | Puntaje nuevo anotado y docs sincronizados | — |

### Unidad 6b — Observabilidad: medición y monitoreo (F6-05) — 23/09

- Columna `error_timestamp` agregada a `Errores_CCB` y sellada en los 8 nodos que registran errores (expresión verificada contra la instancia).
- Data Table `Metricas_CCB` = `W3oJ4a8h0TAPO9ji` (upsert por `metrica`: no crece).
- Flujo `[OPS] - CCB - Monitoreo del pipeline` = `ZwBFTBhwS9pjS69X`, horario, 10 nodos. Fuente: `/metrics` (expuesto sin auth) + `Errores_CCB`. URL centralizada en `Configuracion_CCB.metricas_url`.
- **Verificado con ejecución real** (trigger por webhook temporal, ya eliminado): `success`; tasa de error 0,17%, 124.471 ejecuciones, 0 errores en la hora, p95 5.000 ms, 19 handles; rama de alerta evaluada como falsa; 5 filas escritas en `Metricas_CCB`.
- Limitaciones declaradas: `/metrics` es acumulado desde el arranque y sin etiqueta de flujo; la cola real de workers no es accesible; la tasa exacta por flujo necesita una credencial de API que solo puede crear una persona desde la UI.
- **Pendiente de limpieza manual:** queda una fila de verificación en `Errores_CCB` (id 118, `id_solicitud = PRUEBA-F6-05`); la API pública no permite borrar filas, así que hay que eliminarla desde la UI. El flujo de monitoreo ya la excluye por prefijo `PRUEBA-`.

## Bloqueadas por terceros (no ejecutables desde acá)

| ID | Motivo |
|---|---|
| F5-05 | Migrar a Variables nativas requiere que Tecnología habilite el acceso (la API de Variables devuelve 403 por licencia). La Fase 5 no lo espera: usa la Data Table. |
| F6-04 | Retención de ejecuciones a nivel de instancia (`EXECUTIONS_DATA_PRUNE`/`MAX_AGE`) — requiere Tecnología. |
| F6-05 (exactitud por flujo) | La tasa de error por flujo con denominador real necesita una credencial de API de n8n dentro del flujo; la API pública no permite crear credenciales (403). Se entrega la métrica global + el desglose por flujo desde `Errores_CCB`. |
| Seguridad | `/metrics` está expuesto sin autenticación en `automatizacion.camarabaq.org.co/metrics` (42 métricas de proceso). Se usó como fuente, pero conviene restringirlo o cerrarlo: es decisión de Tecnología. |

## Evidencia por unidad

### Unidad 1-3 — Configuración centralizada (F5) — 23/09

- Data Table `Configuracion_CCB` = `8ChPkhKrjag6Jkcs` (8 claves: `alertas_email`, `asesor_nombre`, `asesor_email`, `asesor_telefono`, `microservicio_pdf_url`, `teams_chat_aprobacion`, `notificacion_envio_email`, `teams_chat_aprobacion_produccion`).
- Subflujo nuevo `[SUB] - CCB - Leer Configuración` = `Hgy02eqPhnsdJvkq` (trigger `passthrough` → Data Table → fusiona `_config` en el item del llamador).
- Consumidores: subflujo compartido de error, catch-all, W4D, W4B, W5B, W3 (cada uno con un único nodo nuevo `Ejecutar Leer Configuración` al inicio de la cadena).
- **Verificación con tráfico real (workflow descartable, ya eliminado):** el subflujo devolvió las 8 claves al llamador (`asesor_email`, `microservicio_pdf_url`, `alertas_email`) con el payload preservado; ejecución `success`.
- **Hallazgo de motor verificado:** n8n **no** resuelve `$('nodo')` hacia una rama hermana (`Node 'X' hasn't been executed`). Es la razón de que el patrón sea un subflujo ancestro y no un nodo colgante. Queda documentado en el plan.
- Limpieza asociada: notas de nodo de W4B/W4D/W5B reescritas sin valores reales; el chatId real de producción quedó guardado en la tabla (no en el repo) y el nodo `Notificar a Fausto - Envío` pasó a `Notificar a asesor - Envío`.
- Pendiente de verificación real por flujo: la corrida de punta a punta de cada consumidor (regla de oro). El subflujo en sí ya está verificado.

### Unidad 7-8 — Arquitectura (F4-02, F4-05) — 23/09

- `[SUB] - CCB - Leer Contexto Propuesta` = `GELWpskp0aYJ2zPg`: resuelve `id_solicitud` (item/body/query) y devuelve `{ id_solicitud, cotizacion, criterios, solicitud }` en un solo item; las 3 lecturas con `alwaysOutputData` para que un dato faltante no corte la cadena.
- Migrados los 3 llamadores: W4B 14→12, W4C 12→10, W4D 50→48. Sin referencias residuales a los nodos viejos.
- **Verificado con datos reales**: subflujo ejecutado con un `id_solicitud` real (devolvió cotización + criterios y `null` en solicitud inexistente).
- F4-05 dictaminado: separar la etapa de PDF (W3 quedaría en 17 nodos); el binario del PDF no lo consume nadie aguas abajo (verificado). Se ejecuta en sesión dedicada con generación de PDF real.

### Unidad 10-11 — Guardarraíles de IA (F7-01, F7-02) — 23/09

- `IF - ¿Corrección IA habilitada?` lee `ia_correccion_habilitada` de `Configuracion_CCB`; en `false` la corrección va a revisión manual.
- `IF - ¿Confianza suficiente?` usa la `confianza` del parser, que **se perdía** en `Aplicar correcciones` (corregido); con `baja` no se aplica el ajuste y la propuesta queda en `REVISION_MANUAL`.
- Ambos caminos avisan al asesor con motivo + interpretación de la IA + comentario, y **no consumen ronda**. W4D pasó de 48 a 54 nodos (F4-03 los va a redistribuir).
- **Verificado**: lógica del nodo nuevo probada con `node` sobre el código extraído y los dos casos reales.
- F7-03 queda con dos caminos documentados y pendiente de decisión del usuario.

### Unidad 9 — Arquitectura: partir W4-D (F4-03) — 23/09

- W4-D pasó de 54 a **19 nodos** (router). Cinco subflujos nuevos: Aprobar `8j6BCwXkgJCccyO1` (3), Cancelar `Jgf514VxDINJ8ra3` (3), Revisión Manual `iNSErCHs2iw33emJ` (6), Corrección IA `3NAcLF4jaZ1JBw0A` (15), Cierre de Corrección `POeFkqQp8e4cGfY3` (17).
- Se preservaron las dos respuestas del rechazo (400 temprano, 200 tardío) y las referencias `$('nodo')` se resolvieron por nombre dentro de cada subflujo (verificación estática de ancestros: 0 rotas en los 5).
- **Verificado con tráfico real** con filas descartables: Aprobar/Cancelar/Tope de rondas, más la cadena anidada W4D → C1 → Revisión Manual → Leer Configuración.
- **Dos defectos corregidos**: (1) los avisos de error perdían el detalle porque un update de Data Table reemplaza el item — afectaba W4B, W5A, W6 y el cierre; (2) el aviso de tope salía con asunto y cuerpo vacíos, mismo motivo.
- Pendiente: ≤20 nodos sigue fallando en W2A (26), W3 (25) y W5B (26); W2A y W5B no estaban en el plan.

## Cierre de tareas sin trabajo de código

| ID | Resolución |
|---|---|
| F3-02 | Diferido definitivamente (decisión del usuario, 23/09). Máximo nativo 5×5000 ya aplicado. |
| F4-04 | N/A — W2B retirado. |
| F4-01 (catch-all) | Se aborda como unidad 13, con diseño propio. |
