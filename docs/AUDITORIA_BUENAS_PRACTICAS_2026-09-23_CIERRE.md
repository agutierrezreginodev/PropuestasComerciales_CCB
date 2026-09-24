# Re-auditoría de cierre — 2026-09-23

**Qué es.** El cierre del mismo día de la [re-auditoría del 23/09](AUDITORIA_BUENAS_PRACTICAS_2026-09-23.md), con la
evidencia de las tareas **R1–R5** de la feature `regresion-y-documentacion-ccb`. Misma rúbrica, mismo método y misma
escala que los informes del 16/09, del 22/09 y de la mañana del 23/09, para que la serie siga siendo comparable.

| Momento | Promedio | Clasificación |
|---|---|---|
| 16/09 | 53,6 / 100 | Requiere refactorización |
| 22/09 | 67,3 / 100 | Requiere refactorización |
| 23/09 (mañana) | 87,7 / 100 | Aprobado con observaciones |
| **23/09 (cierre)** | **89,5 / 100** | Aprobado con observaciones — **a 0,5 del umbral de 90** |

---

## 1. Qué se movió y por qué

| Dimensión | Mañana | Cierre | Qué la movió |
|---|---|---|---|
| Arquitectura /20 | 18,2 | **18,2** | Sin cambios: el flujo nuevo de regresión tiene 20 nodos (el límite del criterio), así que no suma |
| Manejo de errores /20 | 17,0 | **17,0** | Sin cambios |
| Documentación /15 | 13,4 | **14,0** | El [pipeline de punta a punta](FLUJO_COMPLETO_PIPELINE_CCB.md) (10 secciones), el [comparativo demo-vs-actual](COMPARATIVO_DEMO_VS_ACTUAL.md) y la ficha del flujo de regresión |
| Seguridad /15 | 13,8 | **13,8** | Sin cambios: la credencial *Header Auth* y el cierre de `/metrics` siguen pendientes |
| Testing /15 | 11,7 | **12,9** | **El salto grande:** una suite de regresión repetible, la ruta de error y los tres webhooks verificados con tráfico real, y el procedimiento de testing documentado en 5 niveles |
| Observabilidad /15 | 13,6 | **13,6** | Sin cambios: la poda a nivel de instancia sigue en Tecnología y el semáforo de la regresión es una señal de *testing*, no de operación |
| **Total** | **87,7** | **89,5** | **+1,8** |

> **Nota de errata (24/09):** el diagnóstico era incorrecto — la credencial ya existía y estaba asignada; el fallo era `authentication` sin configurar en los dos nodos HTTP, más un `ReferenceError` por zona muerta temporal en el nodo de métricas que congeló las 5 métricas ~28 h. Ambos arreglados y verificados (ejecución `428791`).

**Lo que sostiene el salto de Testing (11,7 → 12,8), con evidencia:**

> **Nota de errata (24/09):** el párrafo dice «11,7 → 12,8»; la tabla de la sección 1 muestra Testing en **12,9**. Se conserva el texto original por ser evidencia histórica.

1. **Suite de regresión repetible** (`[OPS] CCB - Regresión del pipeline`, `GVE3iNQ80y5Q9FEw`): recorre cuatro caminos
   críticos con filas descartables, **verifica el estado real en las tablas**, publica el semáforo en `Metricas_CCB`
   (`regresion_pipeline = 4/4`), limpia sus filas y avisa por correo. Corre sola los lunes y a mano cuando se quiera.
   Verificada con ejecución real (`422898`, 0 nodos con error).
2. **La ruta de error compartida, verificada con tráfico real** (R2, ejecución `422821`): el enmascarado, la marca de
   tiempo, el correo de alerta y —lo que importa— que **el flujo que falla no se corta**.
3. **Los tres webhooks públicos verificados en vivo** (R1): responden 403 sin credencial (vivos y con autenticación) y
   404 cuando el método no coincide, lo que prueba que la restricción de método funciona.
4. **Procedimiento documentado en cinco niveles** ([TESTING_PIPELINE_CCB.md](TESTING_PIPELINE_CCB.md)), con el protocolo
   de datos descartables y su borrado, los casos que hay que forzar y el checklist por cambio.

---

## 2. Puntaje por flujo (cierre)

| Flujo | Arquitectura /20 | Manejo de errores /20 | Documentación /15 | Seguridad /15 | Testing /15 | Observabilidad /15 | **Total** | Mañana |
|---|---|---|---|---|---|---|---|---|
| W1 — Extracción | 17 | 16 | 14 | 13 | 12 | 13 | **85** | 83 |
| W2A — Criterios y cotizar | 18 | 17 | 14 | 13 | 13 | 14 | **89** | 87 |
| W2C — Formulario externo | 18 | 15 | 14 | 14 | 12 | 12 | **85** | 84 |
| W3 — Motor de cálculo | 18 | 17 | 14 | 14 | 13 | 14 | **90** | 89 |
| W4A — Router de aprobación | 19 | 17 | 14 | 14 | 13 | 14 | **91** | 89 |
| W4B — Aprobación (Teams) | 18 | 17 | 14 | 14 | 13 | 14 | **90** | 88 |
| W4C — Consulta de propuesta | 19 | 16 | 14 | 14 | 12 | 12 | **87** | 85 |
| W4D — Procesar decisión | 19 | 18 | 14 | 14 | 14 | 15 | **94** | 92 |
| W5A — Router de envío | 18 | 18 | 14 | 14 | 13 | 14 | **91** | 89 |
| W5B — Envío al cliente | 18 | 18 | 14 | 14 | **14** | 14 | **92** | 90 |
| W6 — Finalizador | 18 | 18 | 14 | 14 | 13 | 14 | **91** | 89 |
| **Promedio** | **18,2** | **17,0** | **14,0** | **13,8** | **12,9** | **13,6** | **89,5** | **87,7** |

**Cinco flujos ya están en 90 o más** (W4D 94, W4A 91, W5A 91, W5B 91, W6 91) y **ninguno baja de 85**.

> **Nota de errata (24/09):** el párrafo dice «cinco» y cita W5B en 91; la tabla de arriba muestra **siete** flujos en 90 o más (W3 90, W4A 91, W4B 90, W4D 94, W5A 91, W5B **92**, W6 91) y W5B en **92**. Se conserva el texto original por ser evidencia histórica.

---

## 3. Lo que falta exactamente para cruzar 90 (0,5 puntos)

| Camino | Dimensión | Qué falta | Cuánto suma | Quién |
|---|---|---|---|---|
| **v2 de la regresión** (hecha el 23/09): el camino `Cerrar envío` ya está; **falta el del motor** | Testing | El caso de `[SUB] Invocar Motor y Guardar Cotización` (W3 lee una planilla Excel y necesita los criterios completos) | ~+0,1 | Yo (sesión aparte) |
| **Probar el rechazo/expiración** de la aprobación de IA | Testing | Un rechazo real en Teams → motivo `aprobacion_rechazada` sin consumir ronda | ~+0,1 | Tú (un clic) |
| **Poda de ejecuciones a nivel de instancia** | Observabilidad | `EXECUTIONS_DATA_PRUNE` / `MAX_AGE`. La retención **por flujo** ya está aplicada | ~+0,3 | Tecnología |
| **Cerrar `/metrics` y la credencial de la API** | Seguridad | Restringir `/metrics`; crear la credencial *Header Auth* en la UI para que la métrica por flujo tenga datos | ~+0,2 | Tecnología + tú |

> **Nota de errata (24/09):** el diagnóstico era incorrecto — la credencial ya existía y estaba asignada; el fallo era `authentication` sin configurar en los dos nodos HTTP, más un `ReferenceError` por zona muerta temporal en el nodo de métricas que congeló las 5 métricas ~28 h. Ambos arreglados y verificados (ejecución `428791`).

**La v2 de la regresión ya está aplicada** (W5B subió a 92) y el promedio se mantiene en **89,5** porque un solo flujo no mueve la media redondeada.
Para cruzar **90,0** hacen falta los ítems de instancia: la **poda de ejecuciones** (+0,3 en Observabilidad) y el **cierre de
`/metrics` con la credencial** (+0,2 en Seguridad). El caso del motor suma ~+0,1 más.

---

## 4. Lista de comprobación (11 requisitos)

Sin cambios respecto de la mañana: **10 de 11 cumplidos**. El único ámbar es **idempotencia (6/11)**, por diseño: hay
*upserts* en todos los puntos de escritura y guardarraíles en W4D, pero los webhooks públicos no tienen clave natural de
origen. La regresión nueva **no** lo mejora (y no lo empeora).

---

## 5. Limitaciones declaradas (sin cambios)

1. Es una evaluación por **evidencia documentada y verificación real**, no una suite automatizada con CI: el puntaje de
   Testing refleja exactamente eso (no hay tests unitarios ni integración continua).
2. Las dimensiones de **instancia** (retención, `/metrics`, licencia de carpetas) no dependen de los workflows.
3. **Hueco de observabilidad declarado:** si el **correo de alerta** falla, la ejecución queda en `success` y nadie se
   entera (el nodo usa `onError: continueRegularOutput` para no cortar el flujo que falla). Cerrarlo exige una rama de
   error nueva en el subflujo compartido.
4. **No verificado todavía:** el rechazo/expiración de la aprobación de IA; que el disparador semanal de la regresión se
   dispare solo (se probó con un webhook temporal); los caminos `Cerrar envío` y del motor dentro de la regresión.
5. **W2B** sigue retirado y fuera de alcance.
