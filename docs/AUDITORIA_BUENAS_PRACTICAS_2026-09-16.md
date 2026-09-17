# Auditoría de buenas prácticas — Pipeline CCB (12 workflows)

**Fecha de corte:** 16 de septiembre de 2026
**Alcance:** los 12 workflows del pipeline definitivo de Información Georreferenciada, más el Error Workflow catch-all como componente transversal.
**Marco de referencia:** *Arquitectura e Ingeniería de Automatización en n8n: Guía de Buenas Prácticas, Resiliencia y Matriz de Evaluación* — rúbrica ponderada de 6 dimensiones sobre 100 puntos y lista de comprobación de 11 requisitos obligatorios para despliegue en producción.
**Método:** lectura nodo por nodo del estado vivo de la instancia (no de los snapshots en disco), validación estructural, auditoría de seguridad automatizada y verificación manual de cada hallazgo.

> **Resultado en una línea:** ningún flujo alcanza el umbral de 90/100. Promedio del pipeline **53,6/100**. Tres flujos caen en clasificación *Crítico* y nueve en *Requiere refactorización*. Los hallazgos son mayoritariamente transversales y sistemáticos, no defectos aislados — lo que significa que se corrigen por lote, no flujo por flujo.

---

## 1. El framework aplicado

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

## 2. Cómo se evaluó — procedimiento reproducible

El procedimiento es determinista: cualquiera puede repetirlo y obtener los mismos hallazgos.

### Paso 1 — Inventario del alcance

Se listaron los 42 workflows de la instancia y se filtraron los 12 que componen el pipeline definitivo (más el catch-all). Se descartaron los archivados, las versiones históricas (`Fase 1`, `Fase 2`, `Propuestas v3`) y los experimentos.

### Paso 2 — Lectura del estado vivo

Para cada flujo se leyó la definición completa desde la instancia. En los flujos grandes se leyó primero la topología y luego el detalle de los nodos pesados, para no truncar la respuesta. **La fuente de verdad es la instancia, nunca el JSON en disco** — ya se comprobó antes que los snapshots se desactualizan.

### Paso 3 — Inspección dirigida por requisito

En cada flujo se inspeccionaron explícitamente:

- `settings.errorWorkflow` y `settings.executionOrder`
- campo `description` del workflow
- presencia y calidad de nodos `stickyNote`
- `pinData`
- `retryOnFail` / `maxTries` / `waitBetweenTries` en todo nodo que llama a un servicio externo
- `onError` **y si la salida de error está realmente cableada** en `connections` — un `onError` sin cable es un error silencioso, y la validación estructural no lo detecta
- operación de los nodos Data Table (`insert` vs `upsert`) y su clave de match
- autenticación en triggers públicos
- existencia de validación de entrada inmediatamente después del trigger
- nomenclatura de nodos contra la convención del framework
- valores hardcodeados: correos, URLs de infraestructura, identificadores

### Paso 4 — Validación estructural

Se ejecutó la validación con perfil `runtime` sobre cada flujo, separando errores reales de falsos positivos. Dos casos documentados de falso positivo:

- **W1** — tres nodos `Preparar error - *` marcados por no tener salida de error propia. Son nodos de flujo normal dentro de una rama ya activada por el `onError` de un nodo anterior.
- **W3** — cuatro avisos de *"Mixed literal text and expression requires = prefix"* en los nodos `HTML - *`. Es intencional: el prefijo `=` haría que n8n intente evaluar ~200 KB de HTML como expresión JavaScript y reviente. Por eso existe el nodo `Interpolar plantilla HTML`.

### Paso 5 — Auditoría de seguridad automatizada

Se ejecutó el escaneo de seguridad sobre la instancia completa (42 flujos, 186 hallazgos). Cada hallazgo dentro del alcance se verificó a mano antes de darlo por válido.

### Paso 6 — Verificación del hallazgo "Crítico" de W3

El escaneo reportó **4 hallazgos críticos** de tipo `url_with_auth` (URL con credenciales embebidas) en los cuatro nodos `HTML - *` de W3. Se verificó por dos vías independientes:

1. Búsqueda del patrón real `esquema://usuario:clave@host` en los ~670 KB de los cuatro nodos → **0 coincidencias**.
2. Barrido regex del mismo patrón sobre el export completo de los 13 flujos → **0 coincidencias**.

**Veredicto: falso positivo.** El disparador es el enlace de Google Fonts presente en los cuatro templates:

```
https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;500;600;700;800;900&display=swap
```

El detector interpreta el `@` del eje variable `wght@300` como separador de credenciales. Cuatro nodos con el mismo enlace producen exactamente cuatro hallazgos. **No hay ninguna credencial en texto plano en el pipeline.**

Lo que sí es real en esos mismos nodos: el correo del asesor comercial hardcodeado, y la URL del microservicio de PDF (túnel temporal) escrita a mano en dos nodos.

### Paso 7 — Verificación del control de versiones

Se contrastó cada flujo vivo contra el repositorio git, comparando `versionCounter`. Al iniciar la auditoría: 6 de 13 flujos versionados, 4 de ellos desactualizados (W2B llevaba 49 versiones de desfase). Como parte de este trabajo se creó `scripts/export_workflows.py` y se sincronizaron los 13.

---

## 3. Resultado consolidado

| Flujo | Nodos | Puntaje | Clasificación | Bloqueante principal |
|---|---|---|---|---|
| W1 — Extracción información del cliente | 21 | **50** | Requiere refactorización | Patrón de error triplicado (45% del lienzo); sin validación de entrada |
| W2A — Guardar Criterios y Cotizar | 25 | **66** | Requiere refactorización | Retry ausente en 9 de 10 nodos de E/S |
| W2B — Formulario de Solicitud | 31 | **46** | **Crítico** | Formulario público sin protección que recolecta PII; nodo crítico sin manejo de error |
| W2C — Recepción Formulario Externo | 5 | **54** | Requiere refactorización | Webhook público sin autenticación; sin idempotencia |
| W3 — Motor Criterios y Precio | 20 | **58** | Requiere refactorización | `pinData` de prueba en flujo activo; Switch sin rama por defecto |
| W4A — Router de Aprobación | 8 | **63** | Requiere refactorización | Fallos de la propia cadena de alerta se pierden en silencio |
| W4B — Aprobación de Propuesta (Teams) | 12 | **60** | Requiere refactorización | Destinatario de Teams en modo prueba dentro de un flujo activo |
| W4C — Consultar Propuesta para Revisión | 8 | **42** | **Crítico** | API pública sin autenticación que expone datos de cliente y valor |
| W4D — Procesar Decisión de Propuesta | 43 | **34** | **Crítico** | Webhook de escritura sin autenticación; 43 nodos; doble incremento de ronda |
| W5A — Router de Envío | 8 | **60** | Requiere refactorización | Sin retry; fila puede quedar atascada en `EN_ENVIO` |
| W5B — Envío al Cliente | 23 | **52** | Requiere refactorización | Notificación interna redirigida a cuenta de prueba en flujo activo |
| W6 — Finalizador de Cotizaciones | 9 | **58** | Requiere refactorización | Cierre masivo automático sin retry ni kill switch |
| **Promedio del pipeline** | | **53,6** | **Requiere refactorización** | |

### 3.1 Desglose por dimensión

| Flujo | Arq /20 | Err /20 | Doc /15 | Seg /15 | Test /15 | Obs /15 | Total |
|---|---|---|---|---|---|---|---|
| W1 | 12 | 13 | 5 | 8 | 5 | 7 | 50 |
| W2A | 15 | 15 | 9 | 9 | 8 | 10 | 66 |
| W2B | 10 | 10 | 6 | 5 | 8 | 7 | 46 |
| W2C | 18 | 12 | 3 | 6 | 3 | 12 | 54 |
| W3 | 15 | 16 | 8 | 6 | 3 | 10 | 58 |
| W4A | 18 | 11 | 8 | 11 | 5 | 10 | 63 |
| W4B | 15 | 15 | 9 | 6 | 6 | 9 | 60 |
| W4C | 15 | 8 | 4 | 2 | 4 | 9 | 42 |
| W4D | 6 | 9 | 2 | 1 | 8 | 8 | 34 |
| W5A | 18 | 10 | 6 | 9 | 6 | 11 | 60 |
| W5B | 12 | 13 | 6 | 4 | 7 | 10 | 52 |
| W6 | 17 | 11 | 6 | 7 | 5 | 12 | 58 |
| **Promedio** | **14,3** | **11,9** | **6,0** | **6,2** | **5,7** | **9,6** | **53,6** |

La dimensión más débil en términos relativos es **Documentación (40% del peso disponible)**, seguida de **Testing (38%)** y **Seguridad (41%)**. La más fuerte es **Observabilidad (64%)**.

### 3.2 Cumplimiento de la lista obligatoria

| Requisito | Cumplen | Detalle |
|---|---|---|
| Manejo global (`errorWorkflow` asignado) | **12/12** ✅ | Todos apuntan al catch-all centralizado |
| Limpieza (sin Pin Data) | 11/12 | Falla W3 (payload de prueba en flujo activo) |
| Arquitectura (≤20 nodos o partido en subflujos) | 8/12 | Fallan W1, W2A, W2B, W4D, W5B |
| Idempotencia | 6/12 | Fallan W2B, W2C, W3, W4D, W5B |
| Protección de webhooks públicos | 0/4 aplicables | **Fallan los 4**: W2B, W2C, W4C, W4D |
| Seguridad (sin valores incrustados) | 2/12 | 10 flujos con correo hardcodeado |
| Resiliencia (retry con backoff exponencial) | **0/12** ❌ | Ninguno usa espera exponencial; 5 no tienen retry en absoluto |
| Validación de entrada tras el trigger | **0/12** ❌ | Ningún flujo valida el payload antes de usarlo |
| Nomenclatura formal | **0/12** ❌ | Ningún nodo sigue la convención del framework |
| Documentación (`description` del workflow) | **0/12** ❌ | Los 12 tienen `description: null` |
| Control de versiones | 13/13 ✅ | Resuelto en esta sesión (antes: 6/13, 4 desactualizados) |

---

## 4. Hallazgos transversales

### 4.1 Bloqueantes de seguridad

1. **Cuatro endpoints públicos sin autenticación**, tres de ellos activos:
   - `W4D · Webhook - Decisión Propuesta` (POST) — **el más grave**: ejecuta aprobaciones, cancelaciones y recálculos con IA. Cualquiera que conozca la URL puede aprobar una propuesta.
   - `W4C · Webhook - Consultar Propuesta` (GET) — expone nombre de cliente, razón social, servicio, valor total y enlace al PDF; enumerable por `id_solicitud`.
   - `W2C · Webhook - Solicitud Georreferenciada` (POST) — recibe PII del formulario externo sin filtro.
   - `W2B · Página 1 - Datos de la empresa` (Form Trigger) — formulario público que recolecta PII sin CAPTCHA ni límite de tasa. *Nota: este es público por decisión de negocio; lo que falta no es cerrarlo sino protegerlo contra abuso.*

2. **Tres desvíos de "modo prueba" activos en producción.** Los tres están documentados en notas del propio nodo como temporales para la grabación de la demo, y siguen vigentes:
   - `W4B · Enviar mensaje Teams` → chat de notas personales en lugar del aprobador real.
   - `W4D · Enviar mensaje Teams` → mismo desvío, en el flujo que procesa decisiones reales.
   - `W5B · Notificar a Asesor CCB - Envío` → notificación interna redirigida a una cuenta distinta del asesor.

3. **Correo personal de desarrollo como único destinatario de alertas de producción** en 10 de los 12 flujos.

### 4.2 Deudas sistemáticas

4. **Ningún flujo valida su entrada.** El framework exige *input gatekeeping* inmediatamente después del trigger, con rama de rechazo. En el pipeline, los flujos leen de Data Table y ejecutan lógica de negocio antes de comprobar que los campos requeridos existan.

5. **Respuestas HTTP que mienten.** W4C y W4D responden `200 OK` incluso cuando la operación falló, devolviendo `{ok:false}` en el cuerpo. En W4C la rama de error 500 es literalmente inalcanzable, porque el nodo que debería lanzar la excepción devuelve el error como dato normal.

6. **Retry sin backoff exponencial.** Donde hay retry, la espera es fija (2000/5000 ms). El framework pide 3–5 reintentos con espera exponencial.

7. **El patrón `Preparar error → Registrar en Data Table → Enviar alerta` está replicado en los 12 flujos**, y triplicado dentro de W1 (9 de 20 nodos). Es el candidato más obvio a subflujo compartido y resolvería de una vez la dimensión de Arquitectura en varios flujos.

8. **Documentación mínima.** Los 12 tienen `description: null`. Las sticky notes existentes son de buena calidad (justifican decisiones, no describen lo obvio), pero W4C y W4D —los dos flujos más riesgosos— no tienen ninguna.

9. **Guardarraíles de IA incompletos en W4D.** Lo que sí hay es sólido: salida estructurada con JSON Schema, modelo *fixer* de respaldo y validación en código contra listas cerradas de valores permitidos por campo. Lo que falta: el campo `confianza` que devuelve el modelo **se calcula pero no se usa para enrutar** — una corrección con confianza baja se aplica igual; no hay kill switch; y la aprobación humana llega recién en la ronda siguiente, cuando el recálculo y el incremento de ronda ya ocurrieron.

10. **Riesgo de idempotencia en W4D.** `Guardar ronda + comentario` incrementa el contador sin guarda contra reenvíos: un doble POST consume dos de las tres rondas disponibles.

---

## 5. Fichas por flujo

Cada ficha detalla lo que cumple, lo que no, y los pendientes priorizados. El detalle operativo completo (matriz de casos de prueba y evidencia de ejecuciones) se mantiene en la documentación interna del proyecto, fuera de este repositorio.

### W1 — Extracción información del cliente · 21 nodos · activo · **50/100**

**Cumple:** `errorWorkflow` centralizado · `pinData` limpio · retry (3 intentos) en extractor IA, modelo y los cuatro nodos Outlook · `onError` cableado de verdad en extractor y creación de solicitud · `upsert` por `id_solicitud` en los Data Table de entidad · credenciales por gestor · sticky note que explica por qué ya no se filtra por remitente y cómo viaja el ID en el asunto.

**No cumple:** sin validación del payload de correo antes del extractor IA · nomenclatura con sufijos de copia-pega (`...1`, `...2`) · `description: null` · sin retry en los cinco Data Table y backoff fijo en el resto · correo personal hardcodeado en tres nodos de alerta · patrón de error triplicado (9 de 20 nodos) · el `id_solicitud` se genera por timestamp, sin deduplicar por identificador del mensaje de origen · la salida del extractor IA no se valida antes de usarse.

**Pendientes:** *Alta* — extraer el manejo de error a subflujo; validar el payload tras el trigger; sacar el correo hardcodeado. *Media* — renombrar nodos; retry con backoff en los Data Table; completar `description`. *Baja* — deduplicar por identificador del mensaje.

### W2A — Guardar Criterios y Cotizar Servicio · 25 nodos · activo · **66/100**

El mejor puntuado del pipeline.

**Cumple:** es un subflujo extraído por responsabilidad única, con su contrato de entrada/salida documentado en sticky note · retención de ejecuciones configurada explícitamente · **idempotencia real**: `upsert` con clave `id_solicitud` recibida del llamador, no regenerada · manejo de error consolidado (no duplicado) para las cuatro ramas de servicio · guardarraíl de negocio (`Validar motor`) antes de persistir · validación estructural sin errores ni advertencias.

**No cumple:** `description: null` · retry en solo 1 de 10 nodos de E/S · `onError: continueRegularOutput` en cuatro nodos de log/alerta (un fallo del propio log se pierde) · sin validación de entrada · 24 nodos funcionales, por encima del umbral · correo hardcodeado en dos nodos · `workflowInputs.schema` vacío en la invocación al motor · sin timeout.

**Pendientes:** *Alta* — retry en los nodos de guardado y en la invocación al motor; validar entrada; sacar el correo. *Media* — completar el esquema de entrada al motor; `description` y renombrado. *Baja* — homologar retry entre los dos nodos de alerta.

### W2B — Formulario de Solicitud · 31 nodos · inactivo · **46/100 (Crítico)**

> **Actualización (17/09/2026):** confirmado con el usuario que W2B está **retirado**, no solo inactivo temporalmente. Fue reemplazado por un formulario estático nuevo (`formulario-solicitud-ccb` → W2C), pero **solo para Información Georreferenciada** — decisión de alcance, no hallazgo: los otros tres servicios que cubría W2B (Zonificación y Rutero, Ubicación de Nuevo Negocio, Información en Línea) quedan sin punto de entrada activo hasta que se implementen más adelante. La clasificación *Crítico* de abajo describe la calidad del código tal como quedó, útil para cuando se retome ese trabajo; no describe un riesgo hoy expuesto en producción.

**Cumple:** `errorWorkflow` centralizado · `pinData` limpio · **Switch con rama por defecto real** cableada a manejo de error (mejor que W2A en esto) · guardarraíl de UX que informa al usuario según el resultado real del subflujo · esquema de entrada explícito en la invocación al subflujo · dos sticky notes que explican la arquitectura de ramas.

**No cumple:** formulario público sin CAPTCHA, límite de tasa ni honeypot, recolectando razón social, identificación, dirección, correo y teléfono · `id_solicitud` se acepta como nulo sin rechazar, y aguas abajo es la clave del `upsert` — dos envíos sin ID colisionarían sobre el mismo registro · el nodo crítico que dispara todo el guardado **no tiene ni `onError` ni `retryOnFail`** · correo hardcodeado · `description: null` y solo dos notas para 31 nodos · cuatro nodos de consolidación con ~90% de código idéntico · registros de error con `insert` puro.

**Pendientes:** *Alta* — proteger el formulario contra abuso; rechazar `id_solicitud` inválido; dar manejo de error al nodo crítico; sacar el correo. *Media* — `upsert` en los registros de error; extraer la lógica repetida. *Baja* — renombrado y documentación.

### W2C — Recepción Formulario Externo · 5 nodos · activo · **54/100**

**Cumple:** arquitectura mínima y bien delegada al subflujo de guardado · `errorWorkflow` centralizado · salidas de error cableadas en los dos nodos que pueden fallar · sin secretos · `pinData` limpio · retención de logs activa.

**No cumple:** **webhook público sin autenticación** recibiendo PII · sin validación con rechazo diferenciado (todo error cae en un 500 genérico) · sin retry en ningún nodo · no idempotente: regenera `id_solicitud` por timestamp si no llega en el cuerpo · PII sin enmascarar en logs · `description: null` y cero sticky notes.

**Pendientes:** *Alta* — autenticar el webhook; validación con rechazo 400; resolver idempotencia; enmascarar PII. *Media* — retry en la invocación al subflujo; documentación. *Baja* — renombrado.

### W3 — Motor Criterios y Precio · 20 nodos · activo · **58/100**

**Cumple:** `errorWorkflow` centralizado y `callerPolicy` restringido a workflows del mismo propietario · retry (3 intentos) en los dos nodos de red · cadena de recuperación de errores completa y verificada en `connections`, terminando en un único nodo de retorno determinista · credencial de Excel por gestor · comentarios de código que explican decisiones no obvias · retención completa más log propio · sticky note que señala explícitamente la deuda del túnel temporal.

**No cumple:** **`pinData` con payload de prueba en un flujo activo** · `description: null` · el Switch de servicio **no tiene rama por defecto**: un valor no reconocido se descarta en silencio · URL del microservicio hardcodeada y duplicada en dos nodos · correo y nombre del asesor hardcodeados en cinco nodos · retry con espera fija · sin timeout explícito en la llamada HTTP, sobre un túnel temporal · 20 nodos exactos, en el límite de la norma.

**Pendientes:** *Alta* — quitar el `pinData`; rama por defecto en el Switch; centralizar la URL del microservicio. *Media* — `description`; parametrizar los datos del asesor; backoff exponencial; timeout explícito. *Baja* — renombrado; evaluar separar la generación de PDF.

### W4A — Router de Aprobación · 8 nodos · activo · **63/100**

**Cumple:** responsabilidad única · `Execute Workflow` en modo *fire-and-forget* justificado en sticky note (el subflujo puede tardar hasta 24 h) · `errorWorkflow` centralizado · `pinData` limpio · idempotencia por marcado previo de estado, con el riesgo residual documentado · salida de error cableada · credencial por gestor.

**No cumple:** sin retry en ningún nodo · los nodos de registro y alerta usan `continueRegularOutput`: **si la propia alerta falla, no se entera nadie** y ni siquiera se dispara el catch-all · sin validación tras la lectura · `description: null` · se llama "Router" pero no tiene nodo de decisión de negocio · correo hardcodeado como único destinatario de alertas.

**Pendientes:** *Alta* — retry; corregir el `onError` de la cadena de alerta; sacar el correo. *Media* — validación con rechazo; `description`; renombrado. *Baja* — paginación en la lectura.

### W4B — Aprobación de Propuesta (Teams) · 12 nodos · activo · **60/100**

**Cumple:** tamaño acotado y responsabilidad única · `errorWorkflow` centralizado · retry (3 intentos) y `onError` cableado en el envío a Teams, con cadena completa hasta marcar revisión manual · sticky note que justifica decisiones reales · credenciales por gestor · `pinData` limpio · idempotente por actualización con clave.

**No cumple:** **destinatario de Teams en modo prueba dentro de un flujo activo** — las aprobaciones no llegan al aprobador real · sin retry en el nodo de alerta · sin validación de `id_solicitud` tras el trigger · `description: null` · nomenclatura no conforme · correo hardcodeado · sin enmascaramiento de PII hacia Teams y Outlook · el bloque de lectura de contexto está duplicado idéntico en W4B, W4C y W4D.

**Pendientes:** *Alta* — restaurar el destinatario real; validar `id_solicitud`. *Media* — retry en la alerta; extraer el bloque de lectura a subflujo compartido. *Baja* — `description` y renombrado.

### W4C — Consultar Propuesta para Revisión · 8 nodos · activo · **42/100 (Crítico)**

**Cumple:** ocho nodos, solo consulta · lectura defensiva que permite continuar sin coincidencias · `errorWorkflow` centralizado · sin credenciales · `pinData` limpio · idempotente por naturaleza.

**No cumple:** **API pública sin autenticación** que expone nombre de cliente, razón social, servicio, valor total y enlace al PDF, enumerable por `id_solicitud` · sin CORS restringido pese a consumirse desde un origen externo conocido · **la rama de error 500 es inalcanzable**: el nodo que la alimentaría devuelve el error como dato normal en vez de lanzar excepción, así que todo sale con `200 OK` · sin validación previa a las tres lecturas · cero sticky notes y `description: null`.

**Pendientes:** *Alta* — autenticar el endpoint; corregir el manejo de error para que 400/500 sean alcanzables. *Media* — CORS restringido al origen conocido. *Baja* — documentar por qué la API es pública.

### W4D — Procesar Decisión de Propuesta · 43 nodos · activo · **34/100 (Crítico)**

El flujo más grande, más riesgoso y peor puntuado del pipeline.

**Cumple:** uso correcto de `Execute Workflow` para reinvocar el motor · **guardarraíles de IA sustantivos**: salida estructurada con JSON Schema obligatorio, modelo *fixer* de respaldo, y validación en código que contrasta cada clave devuelta por el modelo contra las claves existentes y contra listas cerradas de valores válidos por campo, rechazando lo que queda fuera de rango en lugar de aplicarlo a ciegas · retry en los dos modelos y en el envío a Teams, con salida de error cableada · `errorWorkflow` centralizado · `pinData` limpio · credenciales por gestor.

**No cumple:** **webhook de escritura sin autenticación** que ejecuta aprobaciones, cancelaciones y recálculos · 43 nodos y cinco ramas condicionales complejas en un solo lienzo (la validación estructural sugiere partirlo) · destinatario de Teams en modo prueba · correo hardcodeado en dos alertas · sin validación de `decision` contra un enum, y respuesta `200` fija para todas las ramas, incluida la de error · sin retry en las alertas y sin `onError` en la reinvocación del motor · **doble incremento de ronda** ante un reenvío del POST, consumiendo el tope de tres rondas · `confianza` del modelo calculada pero no usada para enrutar; sin kill switch; la aprobación humana llega después del recálculo · cero sticky notes y `description: null`.

**Pendientes:** *Alta* — autenticar el webhook; restaurar el destinatario real; guarda de idempotencia antes de incrementar la ronda; partir en subflujos por rama de decisión. *Media* — enrutar `confianza: baja` a revisión manual y agregar kill switch; retry en alertas y `onError` en la reinvocación; validar `decision` con respuesta 400 real. *Baja* — documentar las decisiones de diseño de IA.

### W5A — Router de Envío · 8 nodos · activo · **60/100**

**Cumple:** ocho nodos con envío delegado a subflujo · `errorWorkflow` centralizado · salida de error cableada y verificada · credencial por gestor · `pinData` limpio · sticky note que documenta el marcado anti-duplicado y la dependencia operativa · idempotencia del camino feliz por transición de estado previa al despacho · retención de ejecuciones configurada · validación estructural sin errores ni advertencias.

**No cumple:** sin retry en ningún nodo, incluida la llamada a Outlook · la lectura y el despacho no tienen `onError` propio: **si el despacho falla, la fila queda atascada en estado intermedio** sin revertir · `description: null` · nomenclatura no conforme · correo hardcodeado · sin validación de entrada · lectura sin límite ni paginación.

**Pendientes:** *Alta* — `onError` en despacho y lectura con reversión de estado; retry en la alerta; sacar el correo. *Media* — renombrado, `description`, validación. *Baja* — paginación.

### W5B — Envío al Cliente · 23 nodos · activo · **52/100**

**Cumple:** `errorWorkflow` centralizado · retry (3 intentos) en descarga de PDF y en los dos nodos de envío · salidas de error cableadas y verificadas · credencial por gestor · `pinData` limpio · retención completa · actualizaciones de estado idempotentes por clave · sticky note que documenta la prioridad de destinatario, el umbral de tamaño del adjunto y el cambio de diseño fechado · **manejo explícito del adjunto ausente**: si la descarga falla no intenta adjuntar un binario inexistente, sino que registra y alerta.

**No cumple:** **notificación interna redirigida a cuenta de prueba en flujo activo**, enviando datos reales de cliente · 23 nodos, con tres bloques de preparación de error casi idénticos · correos hardcodeados en cuatro nodos · el registro de error no declara operación ni clave de match (duplicaría filas al reintentar) · retry con espera fija y dos nodos Outlook sin retry · la validación real ocurre después de tres lecturas · **un PDF de 0 bytes no se distingue de uno demasiado grande**: cae en la rama "enviar solo enlace" sin alerta · sin timeout en la descarga · PII sin enmascarar en notificaciones · un destinatario en copia se calcula pero nunca se usa.

**Pendientes:** *Alta* — restaurar el destinatario real; eliminar los correos hardcodeados; clave de match en el registro de error; separar el caso de PDF corrupto. *Media* — retry en los dos nodos Outlook; extraer los bloques de error a subflujo; mover la validación antes de las lecturas. *Baja* — timeout explícito; resolver el destinatario en copia sin usar.

### W6 — Finalizador de Cotizaciones · 9 nodos · activo · **58/100**

**Cumple:** `errorWorkflow` centralizado · salidas de error cableadas en las dos actualizaciones de estado · registro en la tabla de errores con origen y nodo fallido · credencial por gestor · filtro de estado y regla de negocio (30 días) aplicados antes de mutar datos · retención completa · `pinData` limpio · nueve nodos · idempotente por diseño de estado.

**No cumple:** `description: null` · **la sticky note dice "Creado INACTIVO — pendiente de revisión antes de activar" y el flujo está activo** · sin retry en el único nodo de red · si la alerta falla, el fallo se traga en silencio · sin reconciliación: si una de las dos actualizaciones tiene éxito y la otra falla, las tablas quedan desincronizadas · correo hardcodeado · sin validación de esquema · **cierre masivo automático diario sin control humano ni kill switch**.

**Pendientes:** *Alta* — retry en la alerta; sacar el correo; corregir la sticky note. *Media* — registrar el fallo de la propia alerta; reconciliación ante actualización parcial; renombrado y `description`. *Baja* — validación de campos requeridos; extraer el bloque de error a subflujo compartido.

---

## 6. Qué se corrigió durante esta auditoría

- **Control de versiones (11 de 13 flujos):** se creó `scripts/export_workflows.py`, que exporta los 13 flujos desde la instancia, elimina el bloque de propiedad, aplica la tabla de anonimización y **falla con código de error si sobrevive algún correo fuera de los dominios de reemplazo**. Los 13 JSON quedaron sincronizados con el estado vivo.
- **Anonimización ampliada:** el proceso previo no cubría los identificadores de chat de Teams ni los de carpeta de Outlook, que sí aparecían en los flujos nuevos. Ambos se agregaron a la tabla.
- **Falso positivo crítico descartado** con evidencia reproducible (sección 2, paso 6), evitando una corrección innecesaria sobre cuatro nodos de 200 KB.

Ningún workflow fue modificado en la instancia durante esta auditoría: es un trabajo de lectura, evaluación y documentación.

---

## 7. Conclusión

El pipeline es **funcionalmente sólido** —se validó de punta a punta con datos reales, cubriendo los tres caminos de decisión— pero **no está listo para producción crítica según el framework**. La brecha no está en la lógica de negocio, sino en la disciplina de ingeniería alrededor: autenticación de endpoints, validación de entradas, resiliencia con backoff, documentación y configuración centralizada.

La buena noticia es que **los hallazgos son sistemáticos**. Cuatro correcciones transversales —proteger los endpoints, extraer el manejo de error a un subflujo compartido, centralizar la configuración y agregar validación de entrada con rechazo— mueven simultáneamente a los 12 flujos. El plan de remediación con el detalle de esfuerzo y ganancia estimada por fase está en [`PLAN_REMEDIACION.md`](PLAN_REMEDIACION.md).
