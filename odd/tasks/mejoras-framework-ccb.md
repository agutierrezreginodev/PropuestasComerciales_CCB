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
| 4 | Observabilidad: `timeout` explícito en llamadas HTTP | F6-01 | ☐ | Llamada colgada corta en el tiempo definido | — |
| 5 | Observabilidad: límite/paginación en lecturas sin tope | F6-02 | ☐ | Volumen leído por ejecución acotado | — |
| 6 | Observabilidad: enmascarar PII antes de logs y alertas | F6-03 | ☐ | La alerta identifica la solicitud sin exponer PII | — |
| 7 | Arquitectura: subflujo `[SUB] - CCB - Leer Contexto Propuesta` | F4-02 | ☐ | W4B/W4C/W4D leen el contexto por el mismo subflujo | — |
| 8 | Arquitectura: dictamen sobre separar PDF de cálculo de precio | F4-05 | ☐ | Decisión documentada | — |
| 9 | Arquitectura: partir W4D en subflujos por rama | F4-03 | ☐ | Ningún lienzo supera 20 nodos; las 3 ramas funcionan | — |
| 10 | Guardarraíles de IA: `confianza: baja` → revisión humana | F7-01 | ☐ | Corrección dudosa queda detenida | — |
| 11 | Guardarraíles de IA: kill switch de la corrección asistida | F7-02 | ☐ | Interruptor apagado → revisión manual, resto normal | — |
| 12 | Guardarraíles de IA: aprobación humana antes del recálculo | F7-03 | ☐ | Ninguna ronda se consume sin autorización | — |
| 13 | Catch-all con diseño propio | F4-01 (pendiente) | ☐ | Contrato adaptado, sin perder fidelidad de diagnóstico | — |
| 14 | Cierre documental: re-auditoría, tablero y estado actualizados | — | ☐ | Puntaje nuevo anotado y docs sincronizados | — |

## Bloqueadas por terceros (no ejecutables desde acá)

| ID | Motivo |
|---|---|
| F5-05 | Migrar a Variables nativas requiere que Tecnología habilite el acceso. La Fase 5 no lo espera: usa la Data Table. |
| F6-04 | Retención de ejecuciones a nivel de instancia — requiere Tecnología. |
| F6-05 | Monitoreo de las 4 métricas del framework — requiere un punto de consulta a nivel de instancia; se documenta el diseño. |

## Evidencia por unidad

### Unidad 1-3 — Configuración centralizada (F5) — 23/09

- Data Table `Configuracion_CCB` = `8ChPkhKrjag6Jkcs` (8 claves: `alertas_email`, `asesor_nombre`, `asesor_email`, `asesor_telefono`, `microservicio_pdf_url`, `teams_chat_aprobacion`, `notificacion_envio_email`, `teams_chat_aprobacion_produccion`).
- Subflujo nuevo `[SUB] - CCB - Leer Configuración` = `Hgy02eqPhnsdJvkq` (trigger `passthrough` → Data Table → fusiona `_config` en el item del llamador).
- Consumidores: subflujo compartido de error, catch-all, W4D, W4B, W5B, W3 (cada uno con un único nodo nuevo `Ejecutar Leer Configuración` al inicio de la cadena).
- **Verificación con tráfico real (workflow descartable, ya eliminado):** el subflujo devolvió las 8 claves al llamador (`asesor_email`, `microservicio_pdf_url`, `alertas_email`) con el payload preservado; ejecución `success`.
- **Hallazgo de motor verificado:** n8n **no** resuelve `$('nodo')` hacia una rama hermana (`Node 'X' hasn't been executed`). Es la razón de que el patrón sea un subflujo ancestro y no un nodo colgante. Queda documentado en el plan.
- Limpieza asociada: notas de nodo de W4B/W4D/W5B reescritas sin valores reales; el chatId real de producción quedó guardado en la tabla (no en el repo) y el nodo `Notificar a Fausto - Envío` pasó a `Notificar a asesor - Envío`.
- Pendiente de verificación real por flujo: la corrida de punta a punta de cada consumidor (regla de oro). El subflujo en sí ya está verificado.

## Cierre de tareas sin trabajo de código

| ID | Resolución |
|---|---|
| F3-02 | Diferido definitivamente (decisión del usuario, 23/09). Máximo nativo 5×5000 ya aplicado. |
| F4-04 | N/A — W2B retirado. |
| F4-01 (catch-all) | Se aborda como unidad 13, con diseño propio. |
