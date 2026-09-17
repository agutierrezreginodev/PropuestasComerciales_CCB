# Plan de remediación — de 53,6 a ≥90/100

**Punto de partida:** [Auditoría de buenas prácticas del 2026-09-16](AUDITORIA_BUENAS_PRACTICAS_2026-09-16.md) — promedio del pipeline **53,6/100**, ningún flujo aprobado, 3 en clasificación *Crítico*.
**Meta:** ≥90/100 en los 12 flujos (clasificación *Excelente / Nivel Enterprise*, despliegue en producción crítica sin restricciones).

---

## 1. Cómo se cierra la brecha

La brecha total es de **36,4 puntos promedio**. No se reparte pareja entre los flujos: se concentra en cuatro dimensiones donde casi ningún flujo puntúa, y **todas se corrigen con trabajo transversal**, no flujo por flujo.

| Dimensión | Hoy | Meta | Brecha | Por qué es alcanzable |
|---|---|---|---|---|
| Documentación y Claridad Visual | 6,0 /15 | **14** | +8,0 | Trabajo mecánico: 12 descripciones, renombrado por convención, notas en los 2 flujos que no tienen |
| Seguridad y Gobernanza | 6,2 /15 | **14** | +7,8 | 4 endpoints por autenticar, 3 desvíos de prueba por revertir, configuración por centralizar |
| Testing y Control de Calidad | 5,7 /15 | **13** | +7,3 | Un nodo de validación por flujo, con rama de rechazo |
| Manejo de Errores y Resiliencia | 11,9 /20 | **18** | +6,1 | Retry al máximo nativo, `onError` faltantes, guardas de idempotencia |
| Observabilidad y Rendimiento | 9,6 /15 | **13,5** | +3,9 | Timeouts, paginación, enmascaramiento de PII, retención de ejecuciones |
| Arquitectura y Modularidad | 14,3 /20 | **18** | +3,7 | Dos subflujos compartidos y partir W4D |
| **Total** | **53,6** | **90,5** | **+36,9** | |

---

## 2. Fases

Las fases están ordenadas por **riesgo primero, y luego por relación ganancia/esfuerzo**. La Fase 0 no es negociable: son defectos que hoy están expuestos en producción.

### Fase 0 — Bloqueantes de seguridad · ganancia ≈ +6 promedio · esfuerzo bajo

Nada de esto es refactorización: son correcciones puntuales sobre flujos activos.

| # | Acción | Flujos | Detalle |
|---|---|---|---|
| 0.1 | Autenticar el webhook de decisión | W4D | `Webhook - Decisión Propuesta` ejecuta aprobaciones y cancelaciones sin ningún control. Header Auth con credencial + validación del token en la página de revisión. **El más urgente de todo el plan.** |
| 0.2 | Autenticar la API de consulta | W4C | `Webhook - Consultar Propuesta` expone datos de cliente y valor, enumerable por `id_solicitud`. Header Auth o token de un solo uso ligado a la solicitud. |
| 0.3 | Autenticar el webhook del formulario externo | W2C | `Webhook - Solicitud Georreferenciada` recibe PII sin filtro. Header Auth compartido con el front en Vercel. |
| 0.4 | Proteger el formulario público contra abuso | W2B | Es público por decisión de negocio: no se cierra, se protege (CAPTCHA, honeypot o límite de tasa en el proxy). |
| 0.5 | Revertir los 3 desvíos de "modo prueba" | W4B, W4D, W5B | Destinatario de Teams al aprobador real (W4B y W4D) y notificación interna al asesor real (W5B). Hoy las aprobaciones no llegan a quien debe aprobarlas. |
| 0.6 | Quitar el `pinData` de prueba | W3 | Payload fijado en el trigger de un flujo activo. |
| 0.7 | Restringir CORS al origen conocido | W4C, W2C | Ambos se consumen desde un front conocido; hoy aceptan cualquier origen. |
| 0.8 | Corregir la sticky note engañosa | W6 | Dice "Creado INACTIVO — pendiente de revisión antes de activar" y el flujo está activo. |

### Fase 1 — Documentación · ganancia ≈ +8 promedio · esfuerzo bajo

La fase de mejor relación ganancia/esfuerzo del plan: 15 puntos de peso, casi todo alcanzable con trabajo mecánico y cero riesgo funcional.

| # | Acción | Flujos |
|---|---|---|
| 1.1 | Completar el campo `description` con propósito, sistemas integrados, área propietaria y canal de escalado | los 12 |
| 1.2 | Renombrar los nodos según la convención del framework: `[Servicio] - [Acción/Recurso]`, `[Lógica] - [Condición]`, y `[SUB] - [Dominio] - [Función]` en los subflujos | los 12 |
| 1.3 | Eliminar los sufijos de copia-pega (`...1`, `...2`) | W1, W2B |
| 1.4 | Agregar sticky notes que justifiquen las decisiones de diseño | W4C, W4D (hoy sin ninguna) |
| 1.5 | Renombrar los workflows que son subflujos con el prefijo `[SUB]` | W2A, W3, W4B, W5B |

> Las sticky notes existentes ya cumplen el criterio del framework: explican *por qué*, no *qué*. El patrón a replicar está en `Nota - W5-A`, `Nota - W3 Motor` y la nota de contrato de W2A.

### Fase 2 — Validación de entrada · ganancia ≈ +7 promedio · esfuerzo medio

Ningún flujo valida hoy su entrada. El framework lo exige inmediatamente después del trigger, con rama de rechazo.

| # | Acción | Flujos |
|---|---|---|
| 2.1 | Nodo de validación tras el trigger que verifique campos requeridos y tipos, con rama de rechazo | los 12 |
| 2.2 | En los flujos con webhook, que la rama de rechazo responda **HTTP 400 real** | W2C, W4C, W4D |
| 2.3 | Corregir el manejo de error de `Consolidar respuesta` para que lance excepción y la rama 500 deje de ser inalcanzable | W4C |
| 2.4 | Validar `decision` contra un enum cerrado antes de tocar la base | W4D |
| 2.5 | Rechazar `id_solicitud` nulo o inválido en vez de aceptarlo como `null` | W2B |
| 2.6 | Agregar rama por defecto al Switch de servicio (hoy descarta en silencio) | W3 |
| 2.7 | Validar la salida del extractor IA antes de usarla | W1 |

### Fase 3 — Resiliencia e idempotencia · ganancia ≈ +6 promedio · esfuerzo medio

> ⚠️ **Límite de plataforma verificado.** El framework pide *"3 a 5 reintentos con intervalo de espera exponencial"*. La documentación oficial de n8n confirma que `Retry On Fail` solo admite `maxTries` de **2 a 5** y `waitBetweenTries` como **delay fijo de 0 a 5000 ms**: **no hay backoff exponencial nativo a nivel de nodo**. El criterio adoptado es usar el máximo nativo (`maxTries: 5`, `waitBetweenTries: 5000`) como estándar, y reservar el backoff exponencial real —implementado con `Loop Over Items` + `Wait`, el patrón que la propia documentación recomienda para límites de tasa— solo para la llamada al microservicio de PDF, que es la dependencia más frágil. Esta desviación queda documentada como limitación de plataforma, no como incumplimiento.

| # | Acción | Flujos |
|---|---|---|
| 3.1 | `Retry On Fail` (5 intentos / 5000 ms) en **todo** nodo que llame a un servicio externo | los 12; faltan por completo en W2C, W4A, W5A, W6 |
| 3.2 | Backoff exponencial real con `Loop Over Items` + `Wait` en la generación de PDF | W3 |
| 3.3 | `onError` con reversión de estado: si el despacho falla, la fila no debe quedar atascada en estado intermedio | W5A |
| 3.4 | `onError` en la reinvocación del motor | W4D |
| 3.5 | Manejo de error al nodo crítico que dispara guardado y cotización (hoy sin nada) | W2B |
| 3.6 | Cambiar `continueRegularOutput` por manejo real en las cadenas de alerta, para que un fallo de la propia alerta no se pierda en silencio | W4A, W6, W2A |
| 3.7 | Guarda de idempotencia antes de incrementar la ronda de corrección (hoy un doble POST consume dos rondas) | W4D |
| 3.8 | Clave de match en los registros de error que hoy hacen `insert` puro | W5B, W2B |
| 3.9 | Resolver la regeneración de `id_solicitud` por timestamp | W2C, W1 |
| 3.10 | Reconciliación cuando una de las dos actualizaciones de estado falla y la otra no | W6 |
| 3.11 | Distinguir PDF de 0 bytes (corrupto) del caso "demasiado grande" | W5B |

### Fase 4 — Arquitectura · ganancia ≈ +4 promedio · esfuerzo alto

| # | Acción | Flujos |
|---|---|---|
| 4.1 | Crear `[SUB] - CCB - Registrar y Alertar Error` y reemplazar con él el patrón replicado en los 12 flujos (triplicado dentro de W1, tres bloques casi idénticos en W5B) | los 12 |
| 4.2 | Crear `[SUB] - CCB - Leer Contexto Propuesta` para el bloque de tres lecturas duplicado idéntico | W4B, W4C, W4D |
| 4.3 | Partir W4D (43 nodos, 5 ramas complejas) en subflujos por rama de decisión: aprobar, cancelar, corregir con IA | W4D |
| 4.4 | Extraer la lógica repetida de consolidación de criterios (4 copias con ~90% de código idéntico) | W2B |
| 4.5 | Evaluar separar la generación de PDF del cálculo de precio | W3 |

> 4.1 y 4.2 por sí solas bajan a W1 de 20 a ~13 nodos funcionales, a W5B de 23 a ~19, y descargan a W4B/W4C/W4D. Es la acción con mayor efecto multiplicador del plan.

### Fase 5 — Configuración centralizada · ganancia ≈ +2 promedio · esfuerzo bajo

El acceso a **Variables de n8n** está bloqueado por permisos desde la auditoría anterior. **No hay que seguir esperándolo:** existe una alternativa que no depende de Tecnología.

| # | Acción | Detalle |
|---|---|---|
| 5.1 | Crear una Data Table `Configuracion_CCB` (clave/valor) con el correo de alertas, el correo y nombre del asesor, la URL del microservicio y el chat de aprobación | Fuente única de verdad, editable sin tocar los flujos |
| 5.2 | Reemplazar el correo hardcodeado en los 10 flujos que lo tienen | Hoy un correo personal de desarrollo es el único destinatario de las alertas de producción |
| 5.3 | Sacar la URL del microservicio del código y los parámetros | W3, duplicada en dos nodos |
| 5.4 | Parametrizar nombre y correo del asesor | W3, hoy en cinco nodos |
| 5.5 | Migrar a Variables nativas **si y cuando** Tecnología las habilite | La Data Table es la solución operativa mientras tanto, no un parche descartable |

### Fase 6 — Observabilidad · ganancia ≈ +4 promedio · esfuerzo bajo

| # | Acción | Flujos |
|---|---|---|
| 6.1 | `timeout` explícito en las llamadas HTTP | W3, W5B |
| 6.2 | Paginación o límite en las lecturas con `returnAll: true` | W4A, W5A, W6 |
| 6.3 | Enmascarar PII antes de logs y alertas externas | W4B, W4D, W5B, W2C |
| 6.4 | Revisar las variables de retención de ejecuciones a nivel de instancia (`EXECUTIONS_DATA_PRUNE`, `_MAX_AGE`, `_PRUNE_MAX_COUNT`) | instancia — requiere Tecnología |
| 6.5 | Monitorear las cuatro métricas del framework: tasa de ejecución, tasa de error por flujo (umbral 2%), latencia p95 y profundidad de cola | instancia |

### Fase 7 — Guardarraíles de IA · ganancia ≈ +2 en W4D · esfuerzo medio

| # | Acción | Detalle |
|---|---|---|
| 7.1 | Enrutar `confianza: "baja"` a revisión humana | Hoy el modelo devuelve el nivel de confianza y **se ignora**: una corrección dudosa se aplica igual |
| 7.2 | Kill switch para desactivar la corrección asistida por IA sin desactivar el flujo entero | Exigido explícitamente por el framework para flujos con agentes |
| 7.3 | Mover la aprobación humana antes del recálculo y del incremento de ronda | Hoy llega una ronda tarde |

---

## 3. Proyección de puntaje

| Fase | Acumulado estimado | Clasificación |
|---|---|---|
| Hoy | 53,6 | Requiere refactorización |
| + Fase 0 | ~60 | Requiere refactorización — pero ya sin riesgo expuesto |
| + Fase 1 | ~68 | Requiere refactorización |
| + Fase 2 | ~75 | **Aprobado con observaciones** |
| + Fase 3 | ~81 | Aprobado con observaciones |
| + Fase 4 | ~85 | Aprobado con observaciones |
| + Fases 5, 6 y 7 | **~90,5** | **Excelente / Nivel Enterprise** |

El umbral de despliegue (75) se cruza al terminar la Fase 2. Las fases 0 a 2 son de esfuerzo bajo-medio y ninguna requiere permisos que hoy no tengamos.

---

## 4. Dependencias externas

Dos requisitos del framework siguen bloqueados por permisos de Tecnología. **Ninguno impide llegar a 90**, pero conviene tenerlos presentes:

| Bloqueo | Impacto | Alternativa mientras tanto |
|---|---|---|
| Variables de n8n no habilitadas | Configuración centralizada | Data Table `Configuracion_CCB` (Fase 5) |
| Sin token de MCP a nivel de instancia | Pruebas oficiales con datos fijados | Pruebas manuales documentadas en la matriz de casos interna |
| Sin instancia de *staging* separada | El framework pide probar fuera de producción | Límite real: la dimensión de Testing no llega a 15/15 sin esto |
| Microservicio de PDF sobre túnel temporal | Dependencia frágil en el camino crítico | Deploy con dominio propio y proxy inverso (pendiente de infraestructura) |

---

## 5. Orden de ejecución sugerido

1. **Esta semana:** Fase 0 completa. Son defectos expuestos hoy en producción — sobre todo 0.1 (webhook de decisión sin autenticación) y 0.5 (aprobaciones que no llegan al aprobador real).
2. **Siguiente:** Fase 1 y Fase 5. Bajo esfuerzo, sin riesgo funcional, y juntas suben ~10 puntos.
3. **Después:** Fase 2, que es la que cruza el umbral de despliegue.
4. **Con más calma:** Fases 3, 4, 6 y 7, verificando con una nueva pasada de auditoría al cerrar cada una.

Al terminar cada fase conviene repetir el procedimiento de la sección 2 del informe y re-exportar los flujos con `scripts/export_workflows.py`, para que el snapshot y la calificación no vuelvan a quedar desfasados.
