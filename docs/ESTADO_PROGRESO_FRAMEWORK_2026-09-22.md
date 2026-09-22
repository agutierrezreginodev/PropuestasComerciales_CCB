# Estado de progreso — Cumplimiento del framework de evaluación

**Fecha:** 22 de septiembre de 2026
**Proyecto:** Pipeline CCB (Cámara de Comercio de Barranquilla — Servicios de Información)
**Framework:** *Arquitectura e Ingeniería de Automatización en n8n: Guía de Buenas Prácticas, Resiliencia y Matriz de Evaluación* — rúbrica ponderada de 6 dimensiones sobre 100 puntos + checklist de 11 requisitos obligatorios.
**Repo:** `ccb-workflows-git` (público, `agutierrezreginodev/PropuestasComerciales_CCB`)
**Objetivo del plan:** llevar el pipeline de **54,3 → ≥90/100**.

---

## 1. Resultado de la re-auditoría (16/09 → 22/09)

### 1.1 Puntajes por flujo

| Flujo | 16/09 | 22/09 | Δ | Clasificación (22/09) |
|---|---|---|---|---|
| W1 — Extracción información del cliente | 50 | **58** | +8 | Requiere refactorización |
| W2A — Guardar Criterios y Cotizar | 66 | **73** | +7 | Requiere refactorización |
| W2C — Recepción Formulario Externo | 54 | **77** | +23 | **Bueno / aprobado con observaciones** |
| W3 — Motor Criterios y Precio | 58 | **70** | +12 | Requiere refactorización |
| W4A — Router de Aprobación | 63 | **72** | +9 | Requiere refactorización |
| W4B — Aprobación de Propuesta (Teams) | 60 | **66** | +6 | Requiere refactorización |
| W4C — Consultar Propuesta para Revisión | 42 (Crítico) | **66** | +24 | Sale de Crítico |
| W4D — Procesar Decisión de Propuesta | 34 (Crítico) | **54** | +20 | Sale de Crítico |
| W5A — Router de Envío | 60 | **72** | +12 | Requiere refactorización |
| W5B — Envío al Cliente | 52 | **59** | +7 | Requiere refactorización |
| W6 — Finalizador de Cotizaciones | 58 | **73** | +15 | Requiere refactorización |
| **Promedio (11 flujos activos)** | **54,3** | **67,3** | **+13,0** | Requiere refactorización |

> **Nota metodológica:** la comparación usa los 11 flujos activos (W2B retirado, fuera de alcance desde 17/09). El 16/09 publicado reportó 53,6 sobre 12 flujos incluyendo W2B.

### 1.2 Desglose por dimensión (promedio)

| Dimensión | 16/09 | 22/09 | Δ |
|---|---|---|---|
| Arquitectura /20 | 14,3 | 14,5 | +0,2 |
| Manejo de Errores /20 | 11,9 | 13,1 | +1,2 |
| Documentación /15 | 6,2* | 10,7 | +4,5 |
| Seguridad /15 | 6,2 | 8,5 | +2,3 |
| Testing /15 | 5,7 | 10,4 | +4,7 |
| Observabilidad /15 | 9,6 | 10,1 | +0,5 |
| **Total** | **54,3** | **67,3** | **+13,0** |

### 1.3 Checklist obligatoria (11 requisitos) — estado 22/09

| Requisito | Estado |
|---|---|
| Manejo global (`errorWorkflow`) | ✅ 11/11 |
| Limpieza (sin Pin Data) | ✅ 11/11 |
| Protección de webhooks públicos | ✅ 3/3 |
| Documentación (`description`) | ✅ 11/11 |
| Validación de entrada | ✅ 11/11 |
| Nomenclatura formal | ✅ 11/11 (deuda menor: IF inconsistentes) |
| Arquitectura (≤20 nodos) | ⚠️ 6/11 (W1, W2A, W3, W4D, W5B fallan) |
| Idempotencia | ⚠️ 6/11 |
| Seguridad (sin valores incrustados) | ⚠️ 2/11 (correo hardcodeado en 9) |
| Resiliencia (retry) | ⚠️ en mejora (F3-01 aplicado, ver §3) |
| Control de versiones | ✅ 13/13 |

---

## 2. Plan de remediación — estado de fases

| Fase | Contenido | Estado |
|---|---|---|
| **Fase 0** | Bloqueantes de seguridad | ☑ **Cerrada** — 6/9, 1 N/A (W2B), 2 diferidas por decisión del usuario (F0-05/F0-06, reconfirmadas 22/09) |
| **Fase 1** | Documentación | ☑ **Cerrada** (18/09) — 6/6 |
| **Fase 2** | Validación de entrada | ☑ **Cerrada** (18/09) — 6/7 + 1 N/A; 11/11 flujos con gatekeeping real |
| **Fase 3** | Resiliencia e idempotencia | 🔄 **7/11** (ver §3) — F3-01, 03, 04, 06, 07, 08, 09-W1, 10, 11 hechos; F3-02 parcial; F3-05 N/A |
| **Fase 4** | Arquitectura | 🔄 **F4-01 hecho (8/9)** — F4-02, 03, 04, 05 pendientes |
| **Fase 5** | Configuración centralizada | ☐ Sin empezar |
| **Fase 6** | Observabilidad | ☐ Sin empezar |
| **Fase 7** | Guardarraíles de IA | ☐ Sin empezar |

---

## 3. Trabajo realizado el 22/09 (sesión actual)

### 3.1 F4-01 — Subflujo compartido de error (`[SUB] - CCB - Registrar y Alertar Error`)

**Qué es:** subflujo que centraliza el patrón replicado `Preparar error → Registrar en Errores_CCB → Alertar por Outlook`. Contrato tolerante: `{ id_solicitud, workflow_origen, nodo_fallido, mensaje_error, emailBody, subject?, alertar? }` con defaults. ID: `2dY1kaT7I5a0eP2w` (publicado, validado 0 errores).

**Flujos migrados (8/9 del patrón A):**

| Flujo | Antes → Después | Particularidad |
|---|---|---|
| W6 | 11 → 10 | **Piloto, VERIFICADO con ejecuciones reales** (416449, 416453+416454) |
| W4A | 10 → 9 | Espejo de W6 |
| W5A | 10 → 9 | Espejo de W6 |
| W1 | 23 → 20 | Patrón paralelo; 3 invocaciones; se agregó `workflow_origen: 'intake-v2.0'` a los 4 Preparar |
| W2A | 28 → 26 | 2 invocaciones; `Consolidar resultado de error → Return` intacto |
| W4B | 14 → 13 | `Marcar REVISION_MANUAL` queda en el llamador |
| W5B | 25 → 24 | Patrón consolidado; consolidador emite `emailBody`+`workflow_origen` |
| W4D (recálculo) | 48 → 47 | Solo la rama de recálculo; `alwaysOutputData` en `Marcar ERROR_CALCULO` |

**Exclusiones intencionales:**
- Variantes B (solo registrar, responden al llamador): W2C, W3, W4C y 3 ramas de W4D — no son el patrón duplicado.
- **Catch-all:** contrato divergente (`workflowName`/`lastNode`/`errorMessage`/`alertHtml`), `id_solicitud` fijo, único punto ciego del pipeline → diferido con diseño propio.

**Bug encontrado y corregido:** el IF condicional inicial evaluaba `alertar: true` como false (salida `[[], [item]]`) y saltaba el Outlook. Se eliminó: el subflujo registra y alerta siempre (cadena lineal `Normalizar → Registrar → Alertar → Devolver`), como todos los llamadores del patrón A.

### 3.2 F3 — Resiliencia e idempotencia

| ID | Qué se hizo |
|---|---|
| F3-01 | Retry `5×5000` en 33 nodos de red de negocio sin reintento (W2A, W4A, W4B, W4C, W4D, W5A, W5B, W6) |
| F3-02 | Parcial: retry HTTP PDF de W3 subido a 5×5000. Backoff exponencial real diferido (n8n no lo soporta nativo; reestructurar el motor = riesgo/beneficio malo) |
| F3-03 | W5A: despacho con `onError` → revierte a APROBADA + registra/alerta |
| F3-04 | ✅ Ya estaba en la instancia viva (`Re-invocar motor`, verificado) |
| F3-05 | 🚫 N/A (W2B retirado) |
| F3-06 | Resuelto por diseño F4-01 (registro ocurre antes de la alerta en el subflujo) |
| F3-07 | W4D: IF idempotencia — reenvío del mismo comentario no consume ronda |
| F3-08 | Subflujo: insert → upsert con clave `id_solicitud+workflow_origen+nodo_fallido` |
| F3-09 | W1: `id_solicitud` derivado del id del correo Outlook (no timestamp). W2C: front genera clave estable en sessionStorage (commit en repo aparte, pendiente deploy) |
| F3-10 | W6: si falla la 2ª escritura, revierte la 1ª a ENVIADA |
| F3-11 | W5B: PDF de 0 bytes → ERROR_ENVIO + alerta (consolidador aprende 5º Preparar) |

### 3.3 Hallazgos de la sesión

1. **Retries F3 preexistentes en la instancia viva** (W1, W2C, W4D-`Re-invocar motor`): cambios hechos fuera del plan/snapshot. F3-04 ya estaba resuelto. **Pendiente aclarar con el usuario si fue otra sesión suya.**
2. **Validador n8n-mcp vs. plantillas HTML de W3:** 4 errores de "Mixed literal text and expression requires = prefix" en nodos `HTML - ...` — **preexistentes**, el runtime los acepta y generan PDFs reales. Validación estructural sin expresiones: 0 errores. No se reescribieron las plantillas.
3. **Los `Ejecutar Registrar-y-Alertar` no llevan retry a propósito:** el subflujo hace upsert; reintentar duplicaría invocaciones.

---

## 4. Commits (todos locales, SIN PUSH — 16 commits pendientes)

```
e65fb83 docs(f3-02): documentar retry 5x5000 + diferimiento de backoff exponencial y hallazgo del validador
faac159 feat(f3-02): retry HTTP PDF al máximo nativo 5x5000
f1c350e docs(f3): cerrar F3-01/03/04/06/07/08/09-W1/10/11
e0be80f feat(f3): resiliencia — F3-03/07/08/09-W1/10/11
6f3f62a feat(f3-01): retry 5x5000 en 8 flujos
5203603 docs(f4-01): cerrar F4-01 — 8/9 flujos patrón A
b5e2b6d refactor(f4-01): W4B/W5B/W4D-recálculo
7e68c8d refactor(f4-01): W1 y W2A
fbd45c1 refactor(f4-01): W4A y W5A
0d98159 fix(f4-01): eliminar IF condicional — verificado 416449/416453
d645369 docs(f4-01): marcar en curso
6db7320 chore(workflows): re-exportar estado vivo — retry F3 preexistentes
e8177dd feat(f4-01): crear subflujo + migrar W6 (piloto)
dd0fd1c docs(diagrams): regenerar 4 diagramas
a01ecea docs(auditoria): re-auditoría 22/09
0cb9611 chore(workflows): re-exportar 6 flujos post-Fase 2
```

**Commit aparte (repo privado `formulario-solicitud-ccb`):** `df1a8a3` — fix F3-09 idempotencia en el front (sessionStorage). Sin push, **sin deploy a Vercel** (pendiente migración de cuenta).

---

## 5. Pendientes y próximos pasos

### 5.1 Migración de cuenta Vercel (EN CURSO — el usuario salió a retomar)

- **Problema:** los proyectos `formulario-solicitud-ccb` y `revision-propuesta-ccb` están en el equipo **Muttu** (`team_UF3EtORaOMPzlT6Lz64g3rB7`), creados con una sesión que no se quería; sin repo conectado. Deberían estar en la cuenta personal `agutierrezreginodev`.
- **Restricción Vercel:** la transferencia de proyectos solo se hace a un **Team**, no a una cuenta personal directa.
- **Decisión del usuario:** transferir. **Team a crear (en la cuenta agutierrezreginodev):** `agutierrezreginodev's projects`.
- **Pasos:** (1) crear el Team logueado como agutierrezreginodev → (2) logueado como muttuhub, transferir ambos proyectos al Team → (3) aceptar solicitudes desde agutierrezreginodev → (4) conectar los repos GitHub al Team → (5) hacer deploy del fix F3-09.
- **Los repos GitHub ya están en la cuenta correcta** (`agutierrezreginodev/formulario-solicitud-ccb`, `.../revision-propuesta-ccb`). CLI Vercel logueado como `muttuhub`; la sesión destino requiere `vercel login` del usuario.

### 5.2 Verificación real pendiente (regla de oro del proyecto)

Solo W6 quedó verificado con ejecuciones reales. El resto está validado estructuralmente. Corridas de punta a punta necesarias:

| Caso | Cómo probar |
|---|---|
| F3-03 (W5A) | Fila APROBADA con despacho forzado a fallar → revierte a APROBADA + alerta |
| F3-07 (W4D) | Reenviar el MISMO POST de decisión 2 veces → una ronda, no dos |
| F3-10 (W6) | Forzar fallo de la 2ª escritura → la 1ª revierte a ENVIADA + alerta |
| F3-11 (W5B) | PDF de 0 bytes → ERROR_ENVIO + alerta (no link) |
| F3-09 (W2C) | Doble submit del formulario → un solo registro |
| F4-01 (W4A/W5A/W1/W2A/W4B/W5B/W4D) | Rama de error de cada flujo → registra + alerta vía subflujo |

### 5.3 Próximas fases del plan

1. **F4-02** (subflujo `Leer Contexto Propuesta` compartido W4B/W4C/W4D) y **F4-03** (partir W4D, 48 nodos) — el mayor multiplicador de Arquitectura restante.
2. **F5** (configuración centralizada — correo hardcodeado en 9 flujos).
3. **F6** (observabilidad — timeout, paginación, PII, retención, 4 métricas).
4. **F7** (guardarraíles de IA en W4D — enrutar `confianza: baja`, kill switch).
5. **Catch-all** con diseño propio (contrato divergente).
6. **Backoff exponencial real** en W3 (F3-02 completo) si se decide asumir el riesgo.
7. **Purgar PII del historial de GitHub** (commits huérfanos accesibles por SHA) — opcional.

### 5.4 Decisiones diferidas del usuario (reconfirmadas 22/09)

- F0-05/F0-06: destinatarios de prueba de Teams/Outlook se mantienen en modo prueba a propósito.
- W2B retirado: no se reactiva; los otros 3 servicios sin intake activo se implementarán más adelante.

---

## 6. Datos útiles

- **IDs de workflows activos:** W1=`w6h0qSblUESIpSVc`, W2A=`VChcasvisGKekezR`, W2C=`u6KCMnLwFOp6Ja0N`, W3=`cHOIOEFB5nbltN82`, W4A=`7gmpPMBJtEb0W3J5`, W4B=`5RJdnHDQ8NuWZJG7`, W4C=`KuLSIzBZgaRIjuSu`, W4D=`W0TDH4b0tHCNOzFQ`, W5A=`gvIn6mbAn2Y1bMRR`, W5B=`XWBHgbmtBubA4gqx`, W6=`mPwl4qUb0zQkmDHN`, catch-all=`Dh2lAQTzyoZBpXie`, subflujo error=`2dY1kaT7I5a0eP2w`. W2B=`lIcdT6nGd0w1G2i0` (retirado).
- **Data Tables:** Errores_CCB=`lO46Xkqj0TTedLjI`, Cotizaciones_CCB=`YAvQTqzsgJWjacVZ`, Solicitudes_CCB=`u5gFYvTfuQRX71u5`.
- **Regla de oro del proyecto:** ningún cambio se da por bueno sin verificación con tráfico/ejecución real (no alcanza validación estructural).
- **Regla de push:** no pushear sin pedido explícito. Push por SSH (`git@github.com:...`), `gh`/HTTPS bloqueado por firewall corporativo.
- **Credenciales:** los valores reales viven en `scripts/anonymization.local.json` (git-ignored); el repo público solo tiene placeholders.
- **Token MCP de instancia:** no configurado — la verificación de flujos no-webhook requiere "Test workflow" manual del usuario + ID de ejecución.