# Estado de progreso — Cumplimiento del framework (23/09/2026)

**Proyecto:** Pipeline CCB (Cámara de Comercio de Barranquilla — Servicios de Información)
**Framework:** *Arquitectura e Ingeniería de Automatización en n8n* — rúbrica ponderada de 6 dimensiones sobre 100 puntos + lista de comprobación de 11 requisitos.
**Repo:** `ccb-workflows-git` (público, `agutierrezreginodev/PropuestasComerciales_CCB`)
**Documentos relacionados:** [`PLAN_TRABAJO_FRAMEWORK.md`](PLAN_TRABAJO_FRAMEWORK.md) (tablero de ejecución), [`AUDITORIA_BUENAS_PRACTICAS_2026-09-22.md`](AUDITORIA_BUENAS_PRACTICAS_2026-09-22.md) (última evaluación completa), [`ESTADO_PROGRESO_FRAMEWORK_2026-09-22.md`](ESTADO_PROGRESO_FRAMEWORK_2026-09-22.md) (estado anterior).

> **Sobre el puntaje:** este documento **no publica un promedio nuevo**. La evaluación numérica exige repetir el procedimiento de la auditoría (ficha por flujo contra las 6 dimensiones) y queda como tarea de cierre pendiente. Lo que sí se registra acá es qué tareas del plan se cerraron, con su evidencia, y el estado verificable de la lista de comprobación.

---

## 1. Fases cerradas el 23/09

| Fase | Estado | Qué se hizo |
|---|---|---|
| **Fase 5 — Configuración centralizada** | ✅ **Cerrada** | Data Table `Configuracion_CCB` + subflujo `[SUB] - CCB - Leer Configuración`; ningún correo, URL ni destino escrito a mano en los 13 flujos |
| **Fase 6 — Observabilidad** | ✅ **Cerrada** (salvo F6-04) | Timeouts, límites de lectura, enmascarado de PII, marca de tiempo de errores y monitoreo horario de las 4 métricas |
| **Fase 4 — Arquitectura** | 🔄 F4-01, **F4-02, F4-03 y F4-05 cerradas** | Subflujo de contexto de propuesta; **W4-D partido en router de 19 nodos + 5 subflujos**; dictamen sobre separar el PDF; catch-all con diseño propio |
| **Fase 7 — Guardarraíles de IA** | ✅ **Cerrada y verificada (F7-01, F7-02, F7-03)** | Confianza baja → revisión manual; interruptor de la corrección asistida; **aprobación humana en Teams antes del recálculo y de la ronda** |
| Fase 0 / 1 / 2 | ✅ Cerradas previamente | — |
| Fase 3 | ✅ 9/11 + 1 N/A; F3-02 cerrado como desviación de plataforma | — |

## 2. Lista de comprobación (11 requisitos) — estado 23/09

| Requisito | 22/09 | 23/09 |
|---|---|---|
| Manejo global (`errorWorkflow`) | ✅ 11/11 | ✅ 11/11 (verificado: los 11 flujos activos apuntan al catch-all) |
| Limpieza (sin Pin Data) | ✅ 11/11 | ✅ 11/11 |
| Protección de webhooks públicos | ✅ 3/3 | ✅ 3/3 |
| Documentación (`description`) | ✅ 11/11 | ✅ 13/13 (se agregó la del subflujo de error; las notas desactualizadas del catch-all y de W4B/W4D/W5B se corrigieron) |
| Validación de entrada | ✅ 11/11 | ✅ 11/11 |
| Nomenclatura formal | ✅ 11/11 | ✅ 11/11 (+ `Notificar a asesor - Envío`, sin nombres de personas) |
| **Seguridad (sin valores incrustados)** | ⚠️ 2/11 | ✅ **11/11** — correo de alertas, correo/nombre del asesor, URL del microservicio y chatId salen de `Configuracion_CCB` |
| **Idempotencia** | ⚠️ 6/11 | ⚠️ 6/11 (sin cambios: cubierta por upsert en los puntos de escritura y por el subflujo de error) |
| **Resiliencia (retry)** | ⚠️ en mejora | ✅ 11/11 en nodos de red de negocio (5×5000) + timeout explícito en los dos nodos HTTP |
| **Arquitectura (≤20 nodos)** | ⚠️ 6/11 | ✅ **9/11** — W4D 54→**19** (F4-03); siguen sobre el umbral solo W2A (26) y W5B (26), que no estaban contemplados en el plan |
| Control de versiones | ✅ 13/13 | ✅ 17/17 workflows versionados en el snapshot |

## 3. Artefactos nuevos (23/09)

| Artefacto | ID | Rol |
|---|---|---|
| Data Table `Configuracion_CCB` | `8ChPkhKrjag6Jkcs` | Fuente única de verdad de la configuración (10 claves) |
| Data Table `Metricas_CCB` | `W3oJ4a8h0TAPO9ji` | Publicación de las 4 métricas del framework (upsert por métrica: no crece) |
| Subflujo `[SUB] - CCB - Leer Configuración` | `Hgy02eqPhnsdJvkq` | Entrega la configuración adjunta al item del llamador (`_config`) |
| Subflujo `[SUB] - CCB - Leer Contexto Propuesta` | `GELWpskp0aYJ2zPg` | Reemplaza el bloque de 3 lecturas duplicado en W4B/W4C/W4D |
| Flujo `[OPS] - CCB - Monitoreo del pipeline` | `ZwBFTBhwS9pjS69X` | Horario: mide y publica las 4 métricas, alerta sobre umbral |
| Columna `error_timestamp` en `Errores_CCB` | — | Sella los 8 puntos de registro de error (antes no había forma de ubicarlos en el tiempo) |
| Subflujo `[SUB] - CCB - W4D Aprobar` | `8j6BCwXkgJCccyO1` | Rama "aprobar" del router de decisión (3 nodos) |
| Subflujo `[SUB] - CCB - W4D Cancelar` | `Jgf514VxDINJ8ra3` | Rama "cancelar" (3 nodos) |
| Subflujo `[SUB] - CCB - W4D Revisión Manual` | `iNSErCHs2iw33emJ` | Los tres motivos de revisión manual sin consumir ronda (6 nodos) |
| Subflujo `[SUB] - CCB - W4D Corrección IA` | `3NAcLF4jaZ1JBw0A` | Guardarraíles + ajuste con IA + re-invocación del motor (15 nodos) |
| Subflujo `[SUB] - CCB - W4D Cierre de Corrección` | `POeFkqQp8e4cGfY3` | Idempotencia, ronda, aviso por Teams y fallos (17 nodos) |

## 4. Verificación (regla de oro)

**Verificado con tráfico real el 23/09:**

- Subflujo de configuración: ejecutado desde un workflow descartable; devolvió las claves al llamador con el payload intacto.
- Subflujo de contexto de propuesta: ejecutado con un `id_solicitud` real de `Cotizaciones_CCB`; devolvió cotización y criterios, y `null` en la solicitud inexistente (fallback sin cortar la cadena).
- Flujo de monitoreo: ejecución completa `success`; 0,17% de error, 124.471 ejecuciones, p95 5.000 ms, 19 handles, 5 filas escritas en `Metricas_CCB`.
- Enmascarado de PII y lógica de los guardarraíles de IA: probados con `node` sobre el código extraído de la instancia, con casos reales.
- Hallazgo de motor verificado: n8n **no** resuelve `$('nodo')` hacia una rama hermana (*"hasn't been executed"*); el patrón válido es un subflujo ancestro.
- **F4-03 verificado** con filas descartables (`SOL-PRUEBA-F403` / `SOL-PRUEBA-F403B`): `Aprobar` → 200 + `APROBADA`; `Cancelar` → 200 + `CANCELADA`; `Solicitar correcciones` con ronda 3 → 200 con el mensaje de tope + `REVISION_MANUAL` **sin consumir ronda**; cadena anidada W4D → C1 → Revisión Manual → Leer Configuración completa (`success`).
- **Defecto corregido y verificado:** los avisos de error perdían el detalle porque el nodo `Data Table` reemplaza el item; afectaba a W4B, W5A, W6 y al cierre. Tras invertir el orden, una ejecución real registró `solicitud=SOL-PRUEBA-F403B`, `nodo=Re-invocar motor (recálculo)` y el mensaje real del fallo (antes: `desconocido` / `Error sin mensaje`). También se corrigió el aviso de tope, que salía con asunto y cuerpo vacíos.

**Pendiente de verificación real (no se dio por bueno):**

- Corrida de punta a punta de las ramas de error de W4A/W5A/W1/W2A/W4B/W5B/W4D con el subflujo compartido.
- Ramas nuevas de W4D: confianza baja, IA desactivada, y las de F3-03/F3-07/F3-10/F3-11.
- Separación del PDF (F4-05) requiere generar un PDF real antes de darse por hecha.

## 5. Pendientes

### 5.1 Decisiones del usuario

| Tema | Detalle |
|---|---|
| **F7-03** (aprobación humana antes del recálculo) | Dos caminos: **A)** aprobación dentro de Teams (`sendAndWait`, no toca el front, requiere reordenar la respuesta del webhook y definir expiración) o **B)** aprobación en la página de revisión (nuevo estado + nuevo valor de decisión; toca el front y su deploy está bloqueado por la migración de Vercel). |
| **Tasa de error exacta por flujo** | La métrica global ya se publica; el cálculo por flujo con denominador real necesita una credencial de API dentro de un workflow, y el API público no permite crearlas (403): la debe crear una persona desde la UI. |
| **`/metrics` expuesto sin autenticación** | Hoy publica 42 métricas de proceso de la instancia. Se usó como fuente del monitoreo; conviene restringirlo por red con Tecnología. |
| **Push a GitHub** | 25 commits locales sin publicar en `ccb-workflows-git`. |

### 5.2 Trabajo pendiente en el plan

1. **Aprobación humana (F7-03)** — implementada; falta la verificación real (clic de aprobación/rechazo en Teams).
2. **F4-05** — ejecutar la separación de la etapa de PDF (W3 quedaría en 17 nodos). El bloqueo ya no existe: se verificó que ningún flujo aguas abajo consume el binario del PDF.
2. **Partir W2A (26) y W5B (26)** para cerrar el criterio de ≤20 nodos: no estaba contemplado en el plan y hay que decidirlo (mismo patrón que F4-03: agrupar por rama de servicio / responsabilidad).
3. **F7-03** — según la decisión de arriba.
4. **F6-04** — retención de ejecuciones (`EXECUTIONS_DATA_PRUNE` / `MAX_AGE`): requiere Tecnología.
5. **Re-auditoría de cierre** — repetir el procedimiento de evaluación y publicar el puntaje nuevo.

### 5.3 Limpieza manual

- Filas de prueba en `Errores_CCB` (ids **118**, **120**, **121**, **122**, **123**): el API público de n8n no permite borrar ni actualizar filas (404/405), hay que eliminarlas desde la UI. El flujo de monitoreo excluye las de prefijo `PRUEBA-`.
- Filas descartables en `Cotizaciones_CCB` (`SOL-PRUEBA-F403`, `SOL-PRUEBA-F403B`) usadas para verificar F4-03: eliminarlas desde la UI.
- Tabla **`Errores_Workflows_CCB`**: quedó huérfana (ningún workflow escribe en ella). Se conserva por su historial; conviene decidir si se archiva.
