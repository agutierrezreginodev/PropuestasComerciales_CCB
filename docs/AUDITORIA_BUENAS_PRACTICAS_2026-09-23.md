# Re-auditoría de buenas prácticas — 2026-09-23

**Proyecto:** Pipeline CCB (Cámara de Comercio de Barranquilla — Servicios de Información)
**Framework:** *Arquitectura e Ingeniería de Automatización en n8n: Guía de Buenas Prácticas, Resiliencia y Matriz de Evaluación* — rúbrica ponderada de **6 dimensiones sobre 100 puntos** + lista de comprobación de 11 requisitos.
**Alcance:** los **11 flujos activos** del pipeline (W2B sigue retirado y fuera de alcance).
**Comparabilidad:** mismo procedimiento y misma rúbrica que el informe del 16/09 y la re-auditoría del 22/09, para que la evolución sea comparable.
**Evidencia base:** [auditoría del 16/09](AUDITORIA_BUENAS_PRACTICAS_2026-09-16.md), [re-auditoría del 22/09](AUDITORIA_BUENAS_PRACTICAS_2026-09-22.md), [estado de progreso](ESTADO_PROGRESO_FRAMEWORK_2026-09-23.md) y las verificaciones con tráfico real registradas en el [tablero](PLAN_TRABAJO_FRAMEWORK.md).

> **Cómo leer los puntajes.** Cada dimensión se evalúa contra lo que exige la rúbrica. Cuando una mejora **no** fue verificada con tráfico real, el puntaje se mantiene conservador aunque el diseño esté implementado (regla de oro del proyecto: un cambio no está "bien" hasta que se ejecutó). La dimensión **Testing** queda deliberadamente baja porque el pipeline **no tiene suite automatizada**: lo que hay son verificaciones manuales documentadas y validación estructural.

---

## 1. Resultado general

| Momento | Promedio | Clasificación |
|---|---|---|
| 16/09 (auditoría original) | **53,6 / 100** | Requiere refactorización |
| 22/09 (primera re-auditoría) | **67,3 / 100** | Requiere refactorización |
| **23/09 (esta re-auditoría)** | **87,7 / 100** | **Aprobado con observaciones** |

Umbrales del framework: **≥90** para producción crítica, **≥75** aprobado con observaciones, **<75** requiere refactorización.

**Dos flujos ya superan el umbral de 90** (W4D 92 y W5B 90) y **ninguno queda por debajo de 83** (en el 22/09 el rango era 54–77).

---

## 2. Puntaje por flujo

| Flujo | Arquitectura /20 | Manejo de errores /20 | Documentación /15 | Seguridad /15 | Testing /15 | Observabilidad /15 | **Total** | 22/09 | 16/09 |
|---|---|---|---|---|---|---|---|---|---|
| W1 — Extracción | 17 | 16 | 13 | 13 | 11 | 13 | **83** | 58 | 50 |
| W2A — Criterios y cotizar | 18 | 17 | 13 | 13 | 12 | 14 | **87** | 73 | 66 |
| W2C — Formulario externo | 18 | 15 | 14 | 14 | 11 | 12 | **84** | 77 | 54 |
| W3 — Motor de cálculo | 18 | 17 | 14 | 14 | 12 | 14 | **89** | 70 | 58 |
| W4A — Router de aprobación | 19 | 17 | 13 | 14 | 12 | 14 | **89** | 72 | 63 |
| W4B — Aprobación (Teams) | 18 | 17 | 13 | 14 | 12 | 14 | **88** | 66 | 60 |
| W4C — Consulta de propuesta | 19 | 16 | 13 | 14 | 11 | 12 | **85** | 66 | 42 |
| W4D — Procesar decisión | 19 | 18 | 14 | 14 | 12 | 15 | **92** | 54 | 34 |
| W5A — Router de envío | 18 | 18 | 13 | 14 | 12 | 14 | **89** | 72 | 60 |
| W5B — Envío al cliente | 18 | 18 | 14 | 14 | 12 | 14 | **90** | 59 | 52 |
| W6 — Finalizador | 18 | 18 | 13 | 14 | 12 | 14 | **89** | 73 | 58 |
| **Promedio de los 11** | **18,2** | **17,0** | **13,4** | **13,8** | **11,7** | **13,6** | **87,7** | **67,3** | **53,6** |

### Qué sostiene cada puntaje (evidencia verificada)

- **Arquitectura (14,5 → 18,2).** Ningún flujo activo supera los 20 nodos (máximo 19) y ningún bloque lógico está duplicado: el patrón de error vive en un solo subflujo compartido (usado por 8 flujos), las tres lecturas de contexto en otro (W4B/W4C/W4D/W5B), la etapa de PDF en otro, el motor y el guardado de la cotización en otro, el envío y sus cierres en tres más, y W4D pasó de 54 a 19 nodos con cinco subflujos por rama. Todos los subflujos están entre 3 y 18 nodos.
- **Manejo de errores (13,1 → 17,0).** Reintentos `5×5000` en todos los nodos de red de negocio, `errorWorkflow` centralizado en los 11, timeout explícito en los dos nodos HTTP, reversión compensatoria en W5A y W6, upsert idempotente en el registro de errores, y **cuatro cadenas de error que perdían el detalle de la alerta quedaron corregidas** (el nodo `Data Table` reemplaza el item y el subflujo recibía `desconocido` / "Error sin mensaje"). El guardarraíl de idempotencia de W4D, que comparaba contra vacío, también quedó corregido.
- **Documentación (10,7 → 13,4).** Los 27 workflows tienen `description`, cada bloque funcional tiene sticky notes que explican decisiones, y se agregó [`FLUJOS_PIPELINE_CCB.md`](FLUJOS_PIPELINE_CCB.md) con la ficha de los 14 flujos nuevos (por qué se creó, cómo funciona, con qué se relaciona) más el mapa de dependencias. Queda manual, no automatizado.
- **Seguridad (8,5 → 13,8).** **Cero** correos, URLs o destinatarios escritos a mano dentro de los nodos: todo sale de la Data Table `Configuracion_CCB` por medio de un subflujo. Los 3 webhooks públicos están autenticados (Header Auth) y los 2 consumidos desde el front tienen CORS restringido. No quedan valores de PII en las notas de nodo. **No** se bonifica el `/metrics` expuesto sin autenticación ni los tokens de los front-ends (hallazgos de instancia, pendientes de Tecnología).
- **Observabilidad (10,1 → 13,6).** Las cuatro métricas del framework se publican cada hora en `Metricas_CCB` (tasa de ejecución, tasa de error —global y **por flujo con denominador real**—, latencia p95 y saturación), con umbral que dispara aviso. Se agregó `error_timestamp` a los 8 puntos de registro de error (antes los errores no eran ubicables en el tiempo), límites de lectura en las colas, enmascarado de PII en los avisos y retención por flujo en los routers de alta frecuencia.
- **Testing (10,4 → 11,7).** Sube por las verificaciones **con tráfico real** documentadas (subflujos de configuración y de contexto, flujo de monitoreo, guardarraíles de IA con aprobación humana real en Teams, F4-03 con filas descartables, F4-05 con un PDF real, W5B y W2A con filas descartables) y por la **validación estructural de los 27 workflows** (0 errores, salvo el falso positivo conocido de las plantillas). Queda en 11,7 porque **no hay suite automatizada ni regresión continua**, y porque varias ramas siguen sin corrida de punta a punta.

---

## 3. Lista de comprobación (11 requisitos)

| Requisito | 22/09 | 23/09 |
|---|---|---|
| Manejo global (`errorWorkflow`) | ✅ 11/11 | ✅ 11/11 |
| Limpieza (sin Pin Data) | ✅ 11/11 | ✅ 11/11 |
| Protección de webhooks públicos | ✅ 3/3 | ✅ 3/3 |
| Documentación (`description`) | ✅ 11/11 | ✅ **27/27 workflows** |
| Validación de entrada | ✅ 11/11 | ✅ 11/11 |
| Nomenclatura formal | ✅ 11/11 | ✅ 11/11 (familia `[SUB] CCB - …` / `[OPS] CCB - …` alineada) |
| Resiliencia (retry + timeout) | ⚠️ en mejora | ✅ 11/11 |
| Seguridad (sin valores incrustados) | ⚠️ 2/11 | ✅ **11/11** |
| Arquitectura (≤20 nodos) | ⚠️ 6/11 | ✅ **11/11** |
| Observabilidad (4 métricas + umbral) | ⚠️ no existía | ✅ flujo horario de monitoreo |
| Idempotencia | ⚠️ 6/11 | ⚠️ 6/11 (por diseño: upserts en los puntos de escritura, guardarraíl de comentario repetido en W4D y upsert del subflujo de error; sin clave natural en los webhooks públicos) |

**10 de 11 cumplidos.**

---

## 4. Lo que falta para cruzar el umbral de 90 (87,7 → ≥90)

La distancia es de **2,3 puntos**, y está concentrada en dos dimensiones:

| Camino | Dimensión | Qué haría falta | Impacto estimado |
|---|---|---|---|
| Cerrar las verificaciones pendientes con tráfico real | Testing | Corrida de punta a punta de las ramas de error de los 8 flujos que usan el subflujo compartido; rechazo/expiración de la aprobación de IA; y **una suite de regresión** (aunque sea un flujo de prueba que recorra los caminos críticos) | +2 a +3 |
| Poda de ejecuciones a nivel de instancia | Observabilidad | `EXECUTIONS_DATA_PRUNE` / `MAX_AGE` (Tecnología). La retención **por flujo** ya está aplicada | +0,5 a +1 |
| Credencial y cierre de `/metrics` | Seguridad | Credencial Header Auth creada en la UI (para la métrica por flujo exacta) y cerrar o restringir `/metrics`; tokens de los front-ends fuera del código | +0,5 a +1 |

Con el primer bloque ya se cruza el umbral; los otros dos lo consolidan.

---

## 5. Limitaciones declaradas de esta re-auditoría

1. **Es una evaluación por evidencia documentada y verificación real, no una suite automatizada.** El puntaje de Testing refleja exactamente eso.
2. **Las dimensiones de instancia** (retención de ejecuciones, exposición de `/metrics`, licencia de carpetas/Variables) no dependen de los workflows y quedan fuera del alcance de la mejora.
3. **La métrica exacta de error por flujo está implementada pero sin datos**: n8n no usa las credenciales creadas por API (devuelve 401 al no enviar el header), así que hace falta crear la credencial Header Auth en la UI. Mientras tanto el monitor publica "sin ejecuciones recientes" sin romperse.
4. **W2B sigue retirado** y no se audita; si se reactiva, arrastra sus hallazgos originales.
5. Los puntajes por dimensión son **juicio experto con evidencia**, no una fórmula automática: se mantiene el mismo criterio del 16/09 y del 22/09 para que la serie sea comparable.
