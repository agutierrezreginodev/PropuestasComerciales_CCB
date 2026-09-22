# Re-auditoría de buenas prácticas — Pipeline CCB (11 workflows activos + catch-all)

**Fecha de corte:** 22 de septiembre de 2026
**Alcance:** los 11 workflows activos del pipeline definitivo de Información Georreferenciada, más el Error Workflow catch-all como componente transversal. **W2B queda fuera de alcance**: sigue retirado (`active: false`), confirmado con el usuario el 17/09 y sin novedad desde entonces (ver [`AUDITORIA_BUENAS_PRACTICAS_2026-09-16.md`](AUDITORIA_BUENAS_PRACTICAS_2026-09-16.md), sección 5, ficha W2B).
**Marco de referencia:** el mismo que el 16/09 — *Arquitectura e Ingeniería de Automatización en n8n: Guía de Buenas Prácticas, Resiliencia y Matriz de Evaluación*, rúbrica ponderada de 6 dimensiones sobre 100 puntos y lista de comprobación de 11 requisitos obligatorios para despliegue en producción. No se modificó el framework ni sus pesos entre una ronda y otra.
**Método:** re-lectura del estado vivo de la instancia, comparación nodo por nodo contra los hallazgos del 16/09, y verificación de cada corrección con ejecuciones reales (no solo validación estructural) allí donde el plan de trabajo la reclamaba. Los identificadores de ejecución citados en cada ficha son los mismos ya registrados en [`PLAN_TRABAJO_FRAMEWORK.md`](PLAN_TRABAJO_FRAMEWORK.md) al cerrar cada tarea; esta re-auditoría no repite esas pruebas, las toma como evidencia ya verificada y evalúa el estado resultante.

> **Resultado en una línea:** el pipeline sube de **54,3** a **67,3/100** en promedio. Ningún flujo cruza aún el umbral de despliegue de 75, salvo **W2C (77)**, que pasa a *Bueno / aprobado con observaciones*. Los otros dos flujos que estaban en clasificación *Crítico* (W4C y W4D) salen de esa categoría. Las mejoras son mayoritariamente el resultado de las Fases 0, 1 y 2 del plan de trabajo (seguridad, documentación y validación de entrada); las deudas de Arquitectura, Resiliencia y Seguridad (valores incrustados) apenas se movieron, y en Arquitectura hay regresiones puntuales por el propio costo de agregar validación sin extraer primero el subflujo de error compartido.

> **Nota metodológica sobre la cifra base de comparación:** el informe del 16/09 reportó un promedio de **53,6/100** sobre los 12 flujos de esa fecha, incluyendo W2B (46/100). Como W2B está fuera de alcance desde el 17/09, la comparación de este informe usa como línea base el promedio de esos mismos **11 flujos activos** el 16/09, que es **54,3/100** — no 53,6. Los puntajes individuales de cada flujo el 16/09 son exactamente los publicados en ese informe; solo cambia el denominador del promedio.

---

## 1. El framework aplicado

Sin cambios respecto al 16/09 — se reproduce aquí para que este informe se lea de forma autocontenida.

### 1.1 Rúbrica de calificación (0–100)

| # | Dimensión evaluada | Peso | Criterios técnicos |
|---|---|---|---|
| 1 | Arquitectura y Modularidad | 20 | Responsabilidad única, ausencia de lienzos sobrecargados (>20 nodos), uso correcto de `Execute Workflow`, optimización de memoria en lotes |
| 2 | Manejo de Errores y Resiliencia | 20 | `Retry On Fail` con espera exponencial, captura condicional de excepciones, diseño idempotente, `Error Workflow` centralizado |
| 3 | Documentación y Claridad Visual | 15 | Sticky Notes que justifican decisiones, descripción general del flujo completa, nomenclatura profesional en todos los nodos |
| 4 | Seguridad y Gobernanza | 15 | Cero credenciales incrustadas, uso exclusivo del gestor de credenciales, autenticación en webhooks, enmascaramiento de PII |
| 5 | Testing y Control de Calidad | 15 | Validación de esquema a la entrada, aislamiento de pruebas, guardarraíles en flujos con IA |
| 6 | Observabilidad y Rendimiento | 15 | Retención de logs, optimización de llamadas HTTP, timeouts adecuados |

### 1.2 Escala de aprobación

| Rango | Clasificación | Decisión de despliegue |
|---|---|---|
| 90–100 | Excelente / Nivel Enterprise | Despliegue en producción crítica sin restricciones |
| 75–89 | Bueno / Aprobado con observaciones | Pasa a producción condicionado a corregir en el siguiente ciclo |
| 50–74 | Inadecuado / Requiere refactorización | **Se rechaza el despliegue** hasta refactorizar |
| 0–49 | Crítico / Rechazado | **Se prohíbe** su ejecución en entornos conectados a sistemas reales |

### 1.3 Lista de comprobación obligatoria (11 requisitos)

Arquitectura · Nomenclatura · Documentación · Validación de entrada · Resiliencia · Manejo global de errores · Seguridad · Protección de webhooks · Limpieza de Pin Data · Idempotencia · Control de versiones.

---

## 2. Cómo se evaluó esta ronda

A diferencia del 16/09, esta no es una auditoría desde cero: es una **re-verificación dirigida por el plan de trabajo**. El procedimiento fue:

1. Tomar cada tarea marcada como hecha en [`PLAN_TRABAJO_FRAMEWORK.md`](PLAN_TRABAJO_FRAMEWORK.md) (Fases 0, 1 y 2) y confirmar en la instancia viva que el cambio sigue presente y cableado como se documentó al cerrarla.
2. Releer nodo por nodo cada flujo contra la ficha del 16/09, marcando explícitamente qué mejoró, qué sigue igual y qué empeoró — sin asumir que "hecho en el plan" es lo mismo que "verificado hoy en el estado vivo".
3. Para los hallazgos "Crítico" y "Confirmado sin resolver" del 16/09, releer el código real del nodo en cuestión antes de repetir la afirmación, en vez de darla por buena. Esto llevó a corregir una afirmación del 16/09 sobre W4C (ver ficha W4C).
4. Recontar nodos por flujo desde la instancia viva para detectar regresiones de Arquitectura no reportadas por el plan de trabajo (aparecieron en W1, W2A, W3 y W5B).
5. Reconfirmar con el usuario, con fecha 22/09, las dos decisiones de negocio diferidas el 17/09 (F0-05 y F0-06 — ver sección 5).

No se recalculó ni se reinterpretó ningún puntaje de la rúbrica: los totales y los desgloses por dimensión de este informe son los datos de la re-auditoría, no una proyección.

---

## 3. Resultado consolidado

### 3.1 Comparación 16/09 → 22/09

| Flujo | 16/09 | 22/09 | Δ | Clasificación (22/09) |
|---|---|---|---|---|
| W1 — Extracción información del cliente | 50 | **58** | +8 | Requiere refactorización |
| W2A — Guardar Criterios y Cotizar | 66 | **73** | +7 | Requiere refactorización |
| W2C — Recepción Formulario Externo | 54 | **77** | +23 | **Bueno / aprobado con observaciones** |
| W3 — Motor Criterios y Precio | 58 | **70** | +12 | Requiere refactorización |
| W4A — Router de Aprobación | 63 | **72** | +9 | Requiere refactorización |
| W4B — Aprobación de Propuesta (Teams) | 60 | **66** | +6 | Requiere refactorización |
| W4C — Consultar Propuesta para Revisión | 42 (Crítico) | **66** | +24 | Requiere refactorización — sale de Crítico |
| W4D — Procesar Decisión de Propuesta | 34 (Crítico) | **54** | +20 | Requiere refactorización — sale de Crítico |
| W5A — Router de Envío | 60 | **72** | +12 | Requiere refactorización |
| W5B — Envío al Cliente | 52 | **59** | +7 | Requiere refactorización |
| W6 — Finalizador de Cotizaciones | 58 | **73** | +15 | Requiere refactorización |
| **Promedio (11 flujos activos)** | **54,3** | **67,3** | **+13,0** | **Requiere refactorización** |

Ningún flujo bajó de puntaje. El mayor salto es W2C (+23, el único que cruza el umbral de 75); el menor es W4B (+6, arrastrado por el hallazgo F0-05 confirmado sin resolver).

### 3.2 Desglose por dimensión

| Flujo | Arq /20 | Err /20 | Doc /15 | Seg /15 | Test /15 | Obs /15 | Total |
|---|---|---|---|---|---|---|---|
| W1 | 11 | 13 | 10 | 8 | 9 | 7 | 58 |
| W2A | 14 | 15 | 12 | 9 | 13 | 10 | 73 |
| W2C | 18 | 14 | 7 | 13 | 13 | 12 | 77 |
| W3 | 13 | 17 | 12 | 6 | 11 | 11 | 70 |
| W4A | 18 | 11 | 11 | 11 | 11 | 10 | 72 |
| W4B | 15 | 15 | 11 | 6 | 10 | 9 | 66 |
| W4C | 16 | 12 | 10 | 11 | 7 | 10 | 66 |
| W4D | 7 | 11 | 9 | 9 | 9 | 9 | 54 |
| W5A | 18 | 11 | 12 | 9 | 11 | 11 | 72 |
| W5B | 12 | 12 | 11 | 4 | 10 | 10 | 59 |
| W6 | 18 | 13 | 13 | 7 | 10 | 12 | 73 |
| **Promedio 22/09** | **14,5** | **13,1** | **10,7** | **8,5** | **10,4** | **10,1** | **67,3** |
| **Promedio 16/09** (mismos 11) | **14,3** | **11,9** | **6,2*** | **6,2** | **5,7** | **9,6** | **54,3** |
| **Δ** | **+0,2** | **+1,2** | **+4,5** | **+2,3** | **+4,7** | **+0,5** | **+13,0** |

\* Recalculado sobre los 11 flujos activos (excluye W2B); el 16/09 publicado incluía W2B y daba 6,0/15 sobre 12 flujos.

Las dimensiones que más se movieron son **Testing** (+4,7, por el cierre de la Fase 2 de validación de entrada) y **Documentación** (+4,5, por el cierre de la Fase 1). **Arquitectura** es la más plana (+0,2 en promedio): el salto de W2C (5→18) casi compensa las regresiones de W1, W2A, W3 y W5B por crecimiento de nodos. **Seguridad** mejora principalmente por los tres webhooks ahora autenticados (F0-01/02/03), no por los correos hardcodeados, que no se tocaron.

### 3.3 Cumplimiento de la lista obligatoria (11 requisitos)

| Requisito | 16/09 (11 activos) | 22/09 | Detalle 22/09 |
|---|---|---|---|
| Manejo global (`errorWorkflow` asignado) | 11/11 ✅ | **11/11 ✅** | Sin cambios; todos apuntan al catch-all centralizado |
| Limpieza (sin Pin Data) | 10/11 | **11/11 ✅** | W3 resuelto (F0-07, reconfirmado 22/09) |
| Protección de webhooks públicos | 0/3 aplicables | **3/3 ✅** | Resuelto: W2C, W4C y W4D autenticados con Header Auth (F0-01/02/03) |
| Documentación (`description` del workflow) | 0/11 | **11/11 ✅** | Resuelto (F1-01, 17/09); reconfirmado en todas las fichas de esta ronda |
| Validación de entrada tras el trigger | 0/11 | **11/11 ✅** | Resuelto (F2-01, cerrado 18/09); reverificado con tráfico/ejecuciones reales en esta ronda |
| Nomenclatura formal | 0/11 | **11/11**, con una deuda menor | Homologada por F1-02/F1-03 (18/09); hallazgo nuevo de inconsistencia en nodos IF de W1 (ver sección 4) |
| Arquitectura (≤20 nodos o partido en subflujos) | 7/11 | **6/11** | Empeoró: fallan W1 (23), W2A (28), W3 (24, regresión desde 20), W4D (43) y W5B (24-25, empeoró desde 23). Pasan W2C, W4A, W4B, W4C, W5A, W6 |
| Idempotencia | 6/11 | **6/11** | Sin cambio de conjunto; siguen fallando W1, W2C, W3, W4D y W5B; siguen bien W2A, W4A, W4B, W4C, W5A y W6 |
| Seguridad (sin valores incrustados) | 2/11 | **2/11** | Sin cambios; solo W2C y W4C siguen sin correo hardcodeado |
| Resiliencia (retry con backoff exponencial) | 0/11 ❌ | **0/11 ❌** | Sin cambios; limitación de plataforma ya documentada (n8n no ofrece backoff exponencial nativo), Fase 3 del plan sigue sin empezar |
| Control de versiones | 13/13 ✅ | **13/13 ✅** | Sin cambios; resuelto desde el 16/09 |

**Cinco de once requisitos pasaron a cumplimiento pleno** desde el 16/09 (Limpieza, Protección de webhooks, Documentación, Validación de entrada, Nomenclatura). Los seis restantes no se tocaron en esta ronda del plan (Fases 3, 4 y 5 siguen en `☐`), y uno de ellos (Arquitectura) empeoró como efecto colateral de agregar los nodos de validación de Fase 2 sin haber extraído antes el subflujo de error compartido (F4-01).

---

## 4. Hallazgos transversales (actualizados)

### 4.1 Bloqueantes de seguridad — estado 22/09

1. **Los tres endpoints públicos que estaban sin autenticación ahora están protegidos.** F0-01 (W4D), F0-02 (W4C) y F0-03 (W2C) están confirmados activos con Header Auth y credencial gestionada, verificados con tráfico real (401 sin cabecera, 200/400 con ella). W2B, el cuarto endpoint del 16/09, sigue retirado y fuera de alcance.
2. **Los tres desvíos de "modo prueba" siguen activos, por decisión explícita del usuario, reconfirmada el 22/09** (ver sección 5): `W4B` y `W4D · Enviar mensaje Teams` siguen apuntando al chat de notas personales en vez del aprobador real; `W5B · Notificar a Asesor CCB - Envío` sigue redirigido a una cuenta de demo. En los tres casos, la sticky note del flujo describe el destinatario real y quedó desactualizada/engañosa respecto al comportamiento efectivo — esto sí es hallazgo nuevo de esta ronda, no estaba señalado el 16/09.
3. **El correo personal de desarrollo/demo sigue siendo el único destinatario de alertas en 9 de los 11 flujos activos** (todos salvo W2C y W4C). Ningún flujo se corrigió en este punto; sigue pendiente en Fase 5 (`F5-01`/`F5-02`, configuración centralizada).
4. **Hallazgo nuevo — token compartido sin verificación de ownership en W4C:** el Header Auth impide el acceso anónimo, pero cualquiera que posea el token puede seguir enumerando `id_solicitud` sin que el flujo verifique que esa propuesta le pertenece.

### 4.2 Deudas sistemáticas — estado 22/09

5. **La validación de entrada, ausente en los 12 flujos el 16/09, ya está presente en los 11 flujos activos**, verificada con tráfico o ejecuciones reales en cada caso (F2-01 a F2-07, plan de trabajo). Es el cambio más consistente de esta ronda y explica la mayor parte del salto de puntaje.
6. **Respuestas HTTP que mienten — parcialmente corregido.** W4C ya no devuelve el error de `Consolidar respuesta` como dato con `200` fijo (sale por `onError`), aunque no hacia un `500` como se había afirmado el 16/09 (ver corrección en la ficha de W4C) sino hacia un `400` real. En W4D, la rama de enum inválido ya responde `400` real, pero todas las demás ramas de error (tope de rondas, recálculo fallido, fallo de Teams) siguen respondiendo `200` fijo — el problema persiste parcialmente.
7. **Retry sin backoff exponencial — sin cambios.** Donde hay retry, la espera sigue fija. Fase 3 del plan (resiliencia) no se ha empezado.
8. **El patrón `Preparar error → Registrar en Data Table → Enviar alerta` sigue replicado en los 11 flujos activos**, y en W1 pasó de triplicado a **cuadruplicado** (los nuevos nodos de validación de entrada se sumaron al patrón existente en vez de extraerlo primero a subflujo). Es la causa directa de que W1 haya subido de 21 a 23 nodos pese a las mejoras. `F4-01` (subflujo compartido de error) sigue sin implementarse y es ahora más urgente.
9. **Documentación mínima — resuelto.** Los 11 flujos activos tienen `description` completo (F1-01). Persisten huecos puntuales: W2C sigue con cero sticky notes (no estaba en el alcance de F1-05).
10. **Guardarraíles de IA incompletos en W4D — sin cambios, confirmado por lectura directa del código.** El campo `confianza` se sigue calculando y no se usa para enrutar; no hay kill switch; la aprobación humana sigue llegando después del recálculo y el incremento de ronda.
11. **Riesgo de idempotencia en W4D — sin cambios, confirmado por lectura directa del código.** `Guardar ronda + comentario` sigue sin guarda contra reenvíos.
12. **Hallazgo nuevo — regresión de arquitectura por costo de la Fase 2.** W1, W2A, W3 y W5B subieron de nodos (23, 28, 24 y 24-25 respectivamente) al agregar los nodos de validación de entrada sin haber extraído antes la lógica de error repetida a un subflujo compartido. El efecto neto en la dimensión Arquitectura es casi nulo pese al trabajo real hecho.
13. **Hallazgo nuevo — nomenclatura de nodos IF inconsistente entre flujos.** Pese al cierre de F1-02/F1-03, coexisten dos formatos de nombre de nodo condicional: pregunta simple (`¿ok?`) y `[Acción] - ¿Condición?`. Detectado al revisar W1; probablemente presente en más flujos, no se hizo un barrido exhaustivo en esta ronda.
14. **Hallazgo nuevo — UPDATE mal filtrado en la rama de rechazo de W4B.** `Marcar REVISION_MANUAL - Error Teams` ejecuta un `update` sobre `Cotizaciones_CCB` filtrando por `id_solicitud=''` cuando la validación de entrada rechaza la solicitud. No causa daño porque no matchea ninguna fila, pero es un no-op sucio que debería evitarse explícitamente en vez de dejarlo caer por falta de match.
15. **Hallazgo nuevo — asimetría de diseño en la rama de rechazo de W2C.** A diferencia del resto del pipeline, un payload inválido en W2C no dispara alerta por correo. Es una decisión de diseño defendible (el rechazo ya es visible para quien envía el formulario), pero no está documentada en ninguna sticky note.

---

## 5. Decisión del usuario sobre F0-05 y F0-06 (reconfirmada 22/09)

El 17/09 el usuario decidió explícitamente mantener diferidos los destinatarios de prueba de `F0-05` (Teams en W4B y W4D) y `F0-06` (notificación de envío en W5B) — ver [`PLAN_TRABAJO_FRAMEWORK.md`](PLAN_TRABAJO_FRAMEWORK.md), Fase 0. Consultado de nuevo en esta ronda, el 22/09, el usuario **reconfirmó la misma decisión**: los tres nodos siguen apuntando a destinatarios de prueba a propósito, no por descuido. Esta re-auditoría documenta el estado técnico tal cual —incluyendo que las sticky notes de esos tres flujos describen incorrectamente el destinatario real, lo que sí es un hallazgo nuevo (ver 4.1, punto 2)— sin tratarlo como un hallazgo abierto a resolver de oficio.

---

## 6. Fichas por flujo

Mismo formato que el informe del 16/09: puntaje por dimensión, qué cumple, qué no cumple, hallazgos nuevos de esta ronda y pendientes priorizados. El detalle operativo completo (matriz de casos de prueba y evidencia de ejecuciones) se mantiene en la documentación interna del proyecto, fuera de este repositorio.

### W1 — Extracción información del cliente · 23 nodos · activo · **58/100**

**Puntaje por dimensión:** Arq 11/20 · Err 13/20 · Doc 10/15 · Seg 8/15 · Test 9/15 · Obs 7/15
**Comparación:** 50 → 58 (+8) · Requiere refactorización (sin cambio de clasificación)

**Cumple:** `errorWorkflow` centralizado · `pinData` limpio · retry (3 intentos) en extractor IA, modelo y los cuatro nodos Outlook · `onError` cableado de verdad en extractor y creación de solicitud · `upsert` por `id_solicitud` en los Data Table de entidad · credenciales por gestor · `description` completo (nuevo) · sticky note actualizada, coherente con el estado real del flujo (nuevo) · validación de datos mínimos tras la extracción IA, real y verificada con ejecuciones reales (`384094`/`384138`): un correo sin nombre/teléfono/email no genera un registro con campos inventados (nuevo, F2-07) · validación estructural limpia: los dos falsos positivos documentados el 16/09 ya no se reproducen (0 errores/0 advertencias).

**No cumple:** 23 nodos (antes 21), por encima del umbral de 20 · el patrón `Preparar error → Registrar → Alertar` ahora **cuadruplicado** (antes triplicado), sin extraerse a subflujo compartido · sin retry en los cinco Data Table, backoff fijo en el resto · correo personal de desarrollo hardcodeado en tres nodos de alerta · `id_solicitud` generado por timestamp, sin deduplicar por identificador del mensaje de origen.

**Hallazgos nuevos (22/09):** nomenclatura de nodos IF inconsistente entre flujos del pipeline (formato de pregunta simple vs. `[Acción] - ¿Condición?`) — deuda de consistencia transversal, no solo de W1.

**Pendientes:** *Alta* — extraer el manejo de error a subflujo compartido (F4-01, más urgente ahora que el patrón se cuadruplicó); sacar el correo hardcodeado. *Media* — retry con backoff en los cinco Data Table; homologar la nomenclatura de nodos IF. *Baja* — deduplicar por identificador del mensaje de origen.

### W2A — Guardar Criterios y Cotizar Servicio · 28 nodos · activo · **73/100**

**Puntaje por dimensión:** Arq 14/20 · Err 15/20 · Doc 12/15 · Seg 9/15 · Test 13/15 · Obs 10/15
**Comparación:** 66 → 73 (+7) · Requiere refactorización (sin cambio de clasificación)

**Cumple:** subflujo extraído por responsabilidad única, con su contrato de entrada/salida documentado en sticky note · retención de ejecuciones configurada · idempotencia real (`upsert` con clave `id_solicitud` recibida del llamador, no regenerada) · manejo de error consolidado (no duplicado) para las cuatro ramas de servicio · guardarraíl de negocio (`Validar motor`) antes de persistir · validación estructural sin errores ni advertencias · `description` completo (nuevo) · validación de entrada real y específica por servicio, derivada del código real de W3 (no de supuestos), verificada con ejecución real `384673` (nuevo, F2-01).

**No cumple:** retry en solo 1-2 de ~10 nodos de E/S · 3 nodos con `onError: continueRegularOutput` en alertas/logs (un fallo del propio log se pierde) · correo hardcodeado en dos nodos · `workflowInputs.schema` vacío en la invocación a W3 · sin timeout · 28 nodos (antes 25), por encima del umbral y en aumento.

**Hallazgos nuevos (22/09):** ninguno adicional a lo ya reflejado en el crecimiento de nodos.

**Pendientes:** *Alta* — retry en los nodos de guardado y en la invocación al motor; sacar el correo. *Media* — completar el esquema de entrada al motor; homologar `onError` en los tres nodos de alerta/log. *Baja* — timeout explícito.

### W2C — Recepción Formulario Externo · 5 nodos · activo · **77/100 — Bueno / aprobado con observaciones**

**Puntaje por dimensión:** Arq 18/20 · Err 14/20 · Doc 7/15 · Seg 13/15 · Test 13/15 · Obs 12/15
**Comparación:** 54 → 77 (+23) · **primer y único flujo que cruza el umbral de despliegue de 75**

**Cumple:** arquitectura mínima y bien delegada al subflujo de guardado · `errorWorkflow` centralizado · salidas de error cableadas y verificadas · `pinData` limpio · retención de logs activa · Header Auth con credencial gestionada, confirmado activo (nuevo, F0-03) · CORS restringido al origen real `formulario-solicitud-ccb.vercel.app`, confirmado (nuevo, F0-08) · validación de entrada con rechazo `400` real, verificada de punta a punta con tráfico real (payload inválido → 400, válido → 200) (nuevo, F2-01/F2-02) · `description` completo (F1-01, 17/09).

**No cumple:** cero sticky notes (no estaba en el alcance de F1-05) · sin retry en ningún nodo · no idempotente: sigue regenerando `id_solicitud` por timestamp si no llega en el cuerpo · PII sin enmascarar en el registro de `Errores_CCB`.

**Hallazgos nuevos (22/09):** la rama de rechazo no dispara alerta por correo — asimetría de diseño respecto al resto del pipeline (defendible, pero no documentada en ninguna sticky note).

**Pendientes:** *Alta* — resolver la idempotencia real de `id_solicitud`. *Media* — retry en la invocación al subflujo; enmascarar PII en `Errores_CCB`; documentar (o corregir) la asimetría de la rama de rechazo. *Baja* — agregar al menos una sticky note.

### W3 — Motor Criterios y Precio · 24 nodos · activo · **70/100**

**Puntaje por dimensión:** Arq 13/20 · Err 17/20 · Doc 12/15 · Seg 6/15 · Test 11/15 · Obs 11/15
**Comparación:** 58 → 70 (+12) · Requiere refactorización (sin cambio de clasificación)

**Cumple:** `errorWorkflow` centralizado y `callerPolicy` restringido a workflows del mismo propietario · retry (3 intentos) en los dos nodos de red · cadena de recuperación de errores completa y verificada en `connections`, terminando en un único nodo de retorno determinista · credencial de Excel por gestor · comentarios de código que explican decisiones no obvias · retención completa más log propio · sticky note que señala la deuda del túnel temporal · `description` completo (nuevo) · Switch de servicio con rama por defecto real, cableada a error — F2-06 confirmado corregido (nuevo) · `pinData` limpio, se quitó el payload de prueba (nuevo, F0-07) · validación de entrada real que corta antes de tocar la base (nuevo, F2-01).

**No cumple:** correo y nombre del asesor comercial hardcodeados (cinco apariciones) · URL del microservicio ngrok duplicada en dos nodos · retry con espera fija, sin backoff exponencial · sin timeout explícito en la llamada HTTP al PDF, sobre un túnel temporal · 24 nodos (antes 20), por encima del umbral — **regresión de arquitectura** por los nodos de validación agregados sin el subflujo compartido de error (F4-01) que la habría compensado.

**Hallazgos nuevos (22/09):** ninguno adicional; la regresión de nodos es la novedad principal de esta ficha.

**Pendientes:** *Alta* — centralizar la URL del microservicio; extraer el manejo de error a subflujo compartido (F4-01, más urgente por la regresión de nodos). *Media* — parametrizar los datos del asesor; backoff exponencial; timeout explícito. *Baja* — evaluar separar la generación de PDF.

### W4A — Router de Aprobación · 8 nodos · activo · **72/100**

**Puntaje por dimensión:** Arq 18/20 · Err 11/20 · Doc 11/15 · Seg 11/15 · Test 11/15 · Obs 10/15
**Comparación:** 63 → 72 (+9) · Requiere refactorización (sin cambio de clasificación)

**Cumple:** responsabilidad única · `Execute Workflow` en modo *fire-and-forget* justificado en sticky note · `errorWorkflow` centralizado · `pinData` limpio · idempotencia por marcado previo de estado, con el riesgo residual documentado · salida de error cableada · credencial por gestor · `description` completo (nuevo) · validación de entrada real, confirmada en `connections`: corta antes de marcar `EN_REVISION` o de despachar a W4-B si falta `id_solicitud` (nuevo, F2-01).

**No cumple:** sin retry en ningún nodo · `continueRegularOutput` en la cadena de alerta del router — si la propia alerta falla, no se entera nadie y ni siquiera se dispara el catch-all · correo Gmail personal hardcodeado como único destinatario de alertas · lectura sin paginar.

**Hallazgos nuevos (22/09):** ninguno.

**Pendientes:** *Alta* — retry; corregir el `onError` de la cadena de alerta; sacar el correo. *Media* — paginación en la lectura.

### W4B — Aprobación de Propuesta (Teams) · 12 nodos · activo · **66/100**

**Puntaje por dimensión:** Arq 15/20 · Err 15/20 · Doc 11/15 · Seg 6/15 · Test 10/15 · Obs 9/15
**Comparación:** 60 → 66 (+6) · Requiere refactorización (sin cambio de clasificación) — el menor salto del pipeline

**Cumple:** tamaño acotado y responsabilidad única · `errorWorkflow` centralizado · retry (3 intentos) y `onError` cableado en el envío a Teams, con cadena completa hasta marcar revisión manual · sticky note que justifica decisiones reales (aunque desactualizada en el destinatario, ver hallazgo) · credenciales por gestor · `pinData` limpio · idempotente por actualización con clave · nomenclatura homologada (F1-02/F1-03, 18/09) · `description` completo (nuevo) · validación de entrada real de `id_solicitud` (nuevo, F2-01).

**No cumple:** **el destinatario de Teams sigue en modo prueba (`chatId: "48:notes"`) — F0-05 CONFIRMADO SIN RESOLVER, el hallazgo más importante de esta ronda**: las aprobaciones reales no le llegan a Fausto Eusse Bovea, el aprobador real · la sticky note del flujo describe incorrectamente que sí llega al aprobador real — desactualizada y engañosa · sin retry en el nodo de alerta · correo hardcodeado · sin enmascaramiento de PII hacia Teams y Outlook · bloque de lectura de tres tablas duplicado idéntico con W4C y W4D (candidato a subflujo compartido, F4-02).

**Hallazgos nuevos (22/09):** en la rama de rechazo de la validación de entrada, `Marcar REVISION_MANUAL - Error Teams` ejecuta un `update` sobre `Cotizaciones_CCB` filtrando por `id_solicitud=''` — no causa daño porque no matchea ninguna fila, pero es un no-op sucio que debería evitarse.

**Pendientes:** *Alta* — restaurar el destinatario real de Teams cuando el usuario lo decida (F0-05, diferido a propósito, reconfirmado 22/09); corregir la sticky note engañosa mientras tanto. *Media* — extraer el bloque de lectura a subflujo compartido (F4-02); evitar el `update` con `id_solicitud=''`; retry en la alerta. *Baja* — enmascarar PII hacia Teams/Outlook.

### W4C — Consultar Propuesta para Revisión · 8 nodos · activo · **66/100 — sale de Crítico**

**Puntaje por dimensión:** Arq 16/20 · Err 12/20 · Doc 10/15 · Seg 11/15 · Test 7/15 · Obs 10/15
**Comparación:** 42 (Crítico) → 66 (+24)

**Cumple:** ocho nodos, solo consulta · lectura defensiva que permite continuar sin coincidencias · `errorWorkflow` centralizado · `pinData` limpio · idempotente por naturaleza · sticky notes agregadas y `description` completo (F1-05/F1-01, 17/09) · Header Auth confirmado activo con credencial real (nuevo, F0-02) · CORS restringido al origen real `revision-propuesta-ccb.vercel.app`, confirmado (nuevo, F0-08) · validación de `id_solicitud` real, cortando antes de las tres lecturas (nuevo, F2-01) · `Consolidar respuesta` ya no devuelve el error como dato con `200` fijo: ahora sale por `onError` hacia un `400` real (mejora real, F2-03).

**No cumple:** cero retry en ningún nodo · sin registro en `Errores_CCB` para el fallo de `Consolidar respuesta` — asimétrico respecto al fallo de validación, que sí registra · token de autenticación compartido sin verificación de *ownership* sobre `id_solicitud`, lo que no impide enumeración por quien posea el token.

**Corrección a un hallazgo del 16/09:** el informe anterior afirmaba que "el 500 ya es alcanzable". Esta ronda revisó el código real y **no existe ningún `responseCode: 500` en todo el workflow**, solo `200` y `400`. Lo que sí mejoró de verdad es que `Consolidar respuesta` deja de devolver el error como dato con `200` fijo y ahora sale por `onError` hacia un `400` real — una mejora real, pero distinta de la descrita el 16/09. Se documenta aquí como corrección, no como hallazgo nuevo.

**Pendientes:** *Media* — registrar en `Errores_CCB` el fallo de `Consolidar respuesta`; agregar verificación de *ownership* sobre `id_solicitud`. *Baja* — retry; documentar por qué la API es pública.

### W4D — Procesar Decisión de Propuesta · 43 nodos · activo · **54/100 — sale de Crítico**

**Puntaje por dimensión:** Arq 7/20 · Err 11/20 · Doc 9/15 · Seg 9/15 · Test 9/15 · Obs 9/15
**Comparación:** 34 (Crítico) → 54 (+20) · el más grande y riesgoso del pipeline, sigue lejos del umbral de 75

**Cumple:** uso correcto de `Execute Workflow` para reinvocar el motor · guardarraíles de IA sustantivos: salida estructurada con JSON Schema obligatorio, modelo *fixer* de respaldo, validación en código que contrasta cada clave devuelta por el modelo contra listas cerradas de valores válidos por campo · retry en los dos modelos y en el envío a Teams, con salida de error cableada · `errorWorkflow` centralizado · `pinData` limpio · credenciales por gestor · sticky notes agregadas (F1-05, 17/09) · Header Auth confirmado activo (nuevo, F0-01) · `Validar decisión reconocida` con enum cerrado y `400` real, confirmado cortando **antes** de tocar Data Table (nuevo, F2-04) · `description` honesta, que admite explícitamente el pendiente del campo `confianza` (nuevo).

**No cumple:** 43 nodos y cinco ramas condicionales complejas en un solo lienzo · destinatario de Teams en modo prueba — diferido a propósito, decisión del usuario reconfirmada 22/09 (misma situación que W4B) · correo hardcodeado en dos alertas, sin cambios · **`Guardar ronda + comentario` sigue sin ninguna guarda de idempotencia — CONFIRMADO SIN RESOLVER por lectura directa del código**: un reenvío del mismo POST de decisión vuelve a correr el pipeline de IA completo y consume una ronda de corrección extra, agotando el tope de tres más rápido de lo debido · **el campo `confianza` (alta/media/baja) que el modelo de IA calcula nunca se lee en `Aplicar correcciones` — CONFIRMADO SIN RESOLVER**: no enruta a revisión humana, no hay *kill switch*, la propia sticky note lo admite como pendiente · fuera de la rama de enum inválido, todas las demás ramas de error (tope de rondas, recálculo fallido, fallo de Teams) siguen respondiendo `200` fijo por el nodo genérico `Responder decisión` — el problema de "respuestas que mienten" persiste parcialmente · `Re-invocar motor` sigue sin `onError` ni retry.

**Hallazgos nuevos (22/09):** una rama muerta, `IF - ¿Decisión es solicitar correcciones?` → `Preparar error - No reconocida`, quedó inalcanzable tras el gate temprano de F2-04.

**Pendientes:** *Alta* — guarda de idempotencia antes de incrementar la ronda (F3-07, ahora con evidencia directa de código); enrutar `confianza: baja` a revisión humana y agregar *kill switch* (F7-01/F7-02); que todas las ramas de error respondan con el código real, no `200` fijo; eliminar la rama muerta. *Media* — partir en subflujos por rama de decisión (F4-03); `onError` y retry en la reinvocación del motor. *Baja* — restaurar el destinatario de Teams cuando el usuario lo decida (F0-05, diferido).

### W5A — Router de Envío · 8 nodos · activo · **72/100**

**Puntaje por dimensión:** Arq 18/20 · Err 11/20 · Doc 12/15 · Seg 9/15 · Test 11/15 · Obs 11/15
**Comparación:** 60 → 72 (+12) · Requiere refactorización (sin cambio de clasificación)

**Cumple:** ocho nodos con envío delegado a subflujo · `errorWorkflow` centralizado · salida de error cableada y verificada · credencial por gestor · `pinData` limpio · sticky note que documenta el marcado anti-duplicado y la dependencia operativa · idempotencia del camino feliz por transición de estado previa al despacho · retención de ejecuciones configurada · validación estructural sin errores ni advertencias · nomenclatura homologada (F1-02/F1-03, 18/09) · `description` completo (nuevo) · validación de entrada real: `Validar id_solicitud presente` corta antes de `Marcar EN_ENVIO` (nuevo, F2-01).

**No cumple:** **`Despachar a W5-B` sigue sin `onError` — CONFIRMADO SIN RESOLVER**: al ser *fire-and-forget* (`waitForSubWorkflow:false`), si el despacho falla la fila queda atascada en `EN_ENVIO` sin que el router lo detecte, porque no espera respuesta; solo se blindó el paso previo (el marcado), no el despacho en sí · cero retry en ningún nodo, incluida la llamada a Outlook · correo hardcodeado, sin cambios · lectura sin límite ni paginación.

**Hallazgos nuevos (22/09):** ninguno.

**Pendientes:** *Alta* — `onError` en el despacho con reversión de estado (F3-03), riesgo de negocio confirmado y no solo estructural. *Media* — retry; sacar el correo. *Baja* — paginación.

### W5B — Envío al Cliente · 24-25 nodos · activo · **59/100**

**Puntaje por dimensión:** Arq 12/20 · Err 12/20 · Doc 11/15 · Seg 4/15 · Test 10/15 · Obs 10/15
**Comparación:** 52 → 59 (+7) · Requiere refactorización (sin cambio de clasificación)

**Cumple:** `errorWorkflow` centralizado · retry (3 intentos) en la descarga de PDF y en los dos nodos de envío · salidas de error cableadas y verificadas · credencial por gestor · `pinData` limpio · retención completa · actualizaciones de estado idempotentes por clave · sticky note que documenta la prioridad de destinatario, el umbral de tamaño del adjunto y el cambio de diseño fechado (desactualizada en el destinatario real, ver hallazgo) · manejo explícito del adjunto ausente · `description` completo (nuevo) · `Validar id_solicitud presente` corta antes de las tres lecturas — fix parcial (nuevo, F2-01).

**No cumple:** **la notificación interna sigue redirigida a una cuenta de demo — F0-06 CONFIRMADO SIN RESOLVER, diferido a propósito por decisión del usuario, reconfirmada 22/09**; la sticky note del flujo quedó desactualizada, dice que va al asesor real · `¿Datos completos?` (valida email/PDF) sigue evaluándose **después** de las tres lecturas — la validación temprana solo cubrió el caso más barato (`id_solicitud`) · `Registrar error (Envío)` sigue sin operación de match, insert puro que duplicaría filas en un reintento · un PDF de 0 bytes y uno de más de 4MB producen exactamente el mismo resultado en `Evaluar adjunto` (`tamano > 0 && tamano <= LIMITE`), sin distinguirlos ni alertar el caso de 0 bytes · tres correos hardcodeados · `Marcar ENVIADA` sin `onError` propio · 24-25 nodos (antes 23), con tres bloques de preparación de error casi idénticos — empeoró.

**Hallazgos nuevos (22/09):** ninguno adicional a lo ya reflejado arriba.

**Pendientes:** *Alta* — restaurar el destinatario real cuando el usuario lo decida (F0-06, diferido); clave de match en el registro de error; separar el caso de PDF corrupto (0 bytes) del de tamaño excesivo. *Media* — mover `¿Datos completos?` antes de las lecturas; retry en los dos nodos Outlook; extraer los bloques de error a subflujo compartido. *Baja* — timeout explícito en la descarga; resolver el destinatario en copia sin usar; enmascarar PII en notificaciones.

### W6 — Finalizador de Cotizaciones · 9 nodos · activo · **73/100**

**Puntaje por dimensión:** Arq 18/20 · Err 13/20 · Doc 13/15 · Seg 7/15 · Test 10/15 · Obs 12/15
**Comparación:** 58 → 73 (+15) · **mayor mejora relativa al esfuerzo invertido**

**Cumple:** `errorWorkflow` centralizado · salidas de error cableadas en las dos actualizaciones de estado · registro en la tabla de errores con origen y nodo fallido · credencial por gestor · filtro de estado y regla de negocio (30 días) aplicados antes de mutar datos · retención completa · `pinData` limpio · nueve nodos · idempotente por diseño de estado · **sticky note corregida y honesta** — ya no dice "Creado INACTIVO"; ahora documenta que el flujo está activo en producción desde el 11/09/2026 y cómo desactivarlo si hiciera falta (F0-09, confirmado corregido de verdad) · `description` completo, que cita explícitamente el pendiente del *kill switch* (nuevo) · validación de entrada real confirmada (nuevo, F2-01) · `Marcar FINALIZADA (Solicitudes)` ahora tiene `onError` cableado a la cadena de error compartida — antes se perdía en silencio (mejora nueva).

**No cumple:** sin reconciliación real entre las dos tablas si una actualización tiene éxito y la otra falla · la propia alerta del finalizador sigue con `continueRegularOutput` — si falla, nadie se entera · cero retry en el único nodo de red · correo hardcodeado · *kill switch* para el cierre masivo diario sigue sin implementar (ahora al menos documentado honestamente en la sticky note y en `description`).

**Hallazgos nuevos (22/09):** ninguno adicional.

**Pendientes:** *Alta* — *kill switch* para el cierre masivo diario. *Media* — reconciliación ante actualización parcial; registrar el fallo de la propia alerta; retry en el nodo de red. *Baja* — sacar el correo hardcodeado.

### Error Workflow catch-all (`Dh2lAQTzyoZBpXie`) — evaluación breve, sin ficha en el informe del 16/09

> Este componente no tuvo ficha propia en el informe del 16/09; se agrega aquí por primera vez. Es una evaluación cualitativa de los datos verificados en esta ronda — **no se le calculó un puntaje de rúbrica**, porque el 16/09 no dejó una línea base de dimensiones contra la cual comparar, y esta re-auditoría no recalcula ni inventa puntajes.

**Qué hace:** cuatro nodos — `Error Trigger` → arma una alerta HTML con flujo, nodo, error y link a la ejecución → registra en `Errores_CCB` → envía por Outlook, con retry (3 intentos / 2000 ms). La notificación es de buena calidad y accionable.

**Hallazgo importante:** no tiene manejo de error de segundo nivel. Si el propio registro en Data Table o el envío del correo fallan, el fallo se pierde en silencio, sin ninguna red de contención — es el único punto ciego de todo el pipeline: si el catch-all falla, nadie se entera de nada.

**Hallazgos adicionales:** el destinatario es el mismo correo Gmail personal hardcodeado que aparece en 9 de los 11 flujos activos — aquí es más grave por ser el canal de última instancia de todo el pipeline. La sticky note está desactualizada: dice "asignado a W1, W2 y W3" cuando en realidad lo usan los 11 flujos activos (y W2B, mientras estuvo en operación).

---

## 7. Conclusión

El pipeline avanzó de forma real y verificable: **+13,0 puntos de promedio**, dos flujos que salen de *Crítico* (W4C, W4D) y uno que cruza el umbral de despliegue (W2C). El patrón se repite en casi todas las fichas: las Fases 0 (seguridad), 1 (documentación) y 2 (validación de entrada) del plan de trabajo mueven la aguja de forma consistente y verificada con tráfico o ejecuciones reales, no solo con validación estructural.

La brecha que queda es la misma que se identificó el 16/09, solo que ahora más acotada: **Resiliencia** (retry sin backoff, Fase 3 sin empezar), **Seguridad de valores incrustados** (correo hardcodeado en 9 de 11 flujos, Fase 5 sin empezar) y **Arquitectura** (el patrón de error replicado sigue sin extraerse a subflujo compartido, y de hecho empeoró en cuatro flujos como efecto colateral de la propia Fase 2). Dos decisiones de negocio siguen diferidas a propósito (F0-05, F0-06), reconfirmadas por el usuario el 22/09, y dos hallazgos de W4D (guarda de idempotencia y enrutamiento por `confianza`) siguen sin resolver pese a estar confirmados por lectura directa del código.

El siguiente salto de puntaje más probable no viene de trabajo nuevo, sino de cerrar lo que ya está en el plan: `F4-01` (subflujo de error compartido) resolvería de un golpe la regresión de Arquitectura en cuatro flujos, y Fase 3 (resiliencia) es la única fase de peso pendiente que no depende de ninguna decisión de negocio diferida.
