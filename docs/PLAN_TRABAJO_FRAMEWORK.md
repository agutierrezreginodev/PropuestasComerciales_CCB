# Plan de trabajo — Cumplimiento del framework en los 12 workflows

**Objetivo:** llevar los 12 workflows del pipeline CCB de **53,6/100** a **≥90/100** según la rúbrica del framework *Arquitectura e Ingeniería de Automatización en n8n*.

Este documento es el **tablero de ejecución**: tareas atómicas, con el nodo exacto sobre el que se actúa y cómo se verifica cada una. La estrategia y la proyección de puntaje están en [`PLAN_REMEDIACION.md`](PLAN_REMEDIACION.md); la evidencia que sustenta cada tarea, en [`AUDITORIA_BUENAS_PRACTICAS_2026-09-16.md`](AUDITORIA_BUENAS_PRACTICAS_2026-09-16.md).

---

## Cómo se usa

- Cada tarea tiene un **identificador estable** (`F0-01`, `F1-03`, …). Al ejecutarla se marca la casilla y se anota la fecha.
- Una tarea **no se da por hecha sin su verificación**. La columna *Cómo se verifica* dice exactamente qué comprobar; no alcanza con "lo cambié".
- Al cerrar cada fase se repite el procedimiento de evaluación del informe de auditoría, se re-exporta con `scripts/export_workflows.py` y se anota el puntaje nuevo en la tabla de seguimiento.
- **Regla de oro:** ningún cambio se da por bueno sin ejecutar el flujo afectado al menos una vez de punta a punta.

**Leyenda de esfuerzo:** ▪ ≤30 min · ▪▪ 1–3 h · ▪▪▪ más de medio día.

---

## Fase 0 — Bloqueantes de seguridad

> **Empezar por acá.** No son mejoras: son defectos que hoy están expuestos en producción. `F0-05` es el más costoso en términos de negocio, porque significa que las aprobaciones no le están llegando a quien debe aprobarlas.

| ID | Tarea | Flujo · nodo | Esf. | Cómo se verifica | Hecho |
|---|---|---|---|---|---|
| F0-01 | Autenticar el webhook de decisión con Header Auth y validar el token desde la página de revisión | W4D · `Webhook - Decisión Propuesta` | ▪▪ | Un POST sin cabecera devuelve 401; el flujo completo sigue funcionando desde la página de revisión | ☑ 17/09 |
| F0-02 | Autenticar la API de consulta | W4C · `Webhook - Consultar Propuesta` | ▪▪ | Un GET sin cabecera devuelve 401; la página de revisión sigue cargando la propuesta | ☑ 17/09 |
| F0-03 | Autenticar el webhook del formulario externo, con la cabecera compartida con el front | W2C · `Webhook - Solicitud Georreferenciada` | ▪▪ | Un POST sin cabecera devuelve 401; el formulario publicado sigue enviando bien | ☑ 17/09 |
| F0-04 | ~~Proteger el formulario público contra abuso~~ — **No aplica.** Confirmado con el usuario (17/09): W2B está retirado, `active: false`, una sola ejecución de prueba en toda su historia. No recibe tráfico real; no hay nada que proteger hoy | W2B · `Página 1 - Datos de la empresa` | — | — | 🚫 N/A |
| F0-05 | Restaurar el destinatario real de Teams en los dos flujos que siguen apuntando al chat de notas | W4B y W4D · `Enviar mensaje Teams` | ▪ | El aprobador recibe el mensaje en su chat; el `chatId` ya no es el de notas personales | ⏸ diferido — decisión explícita del usuario, queda en modo prueba por ahora |
| F0-06 | Restaurar el destinatario real de la notificación interna de envío | W5B · `Notificar a Asesor CCB - Envío` | ▪ | El asesor recibe la confirmación; la nota de "modo prueba" del nodo se elimina | ⏸ diferido — misma decisión que F0-05 |
| F0-07 | Quitar el `pinData` de prueba del trigger | W3 · `When Executed by Another Workflow` | ▪ | `pinData` vacío en el flujo activo; una ejecución real sigue calculando bien | ☑ 17/09 |
| F0-08 | Restringir CORS al origen conocido en los dos webhooks consumidos desde el front | W4C y W2C | ▪ | Una petición desde otro origen es rechazada por el navegador; el front propio sigue operando | ☑ 17/09 |
| F0-09 | Corregir la sticky note que dice "Creado INACTIVO" en un flujo activo | W6 · `Nota - W6` | ▪ | El texto de la nota coincide con el estado real del flujo | ☑ 17/09 |

**Criterio de cierre:** los cuatro endpoints rechazan peticiones no autenticadas, ningún flujo activo apunta a un destinatario de prueba, y ningún flujo activo tiene datos fijados. **6 de 9 hechas, 1 no aplica, 2 diferidas por decisión del usuario (17/09) — Fase 0 efectivamente cerrada** salvo que se reactive W2B o el usuario reconsidere F0-05/F0-06.

> **Nota — W2B fuera del pipeline activo (17/09):** confirmado con el usuario que W2B está retirado. Se reemplazó por el formulario estático nuevo (`formulario-solicitud-ccb` → W2C) **solo para Información Georreferenciada**. Los otros tres servicios que W2B atendía (Zonificación y Rutero, Ubicación de Nuevo Negocio, Información en Línea) **no tienen hoy ningún punto de entrada activo** — es una decisión de alcance del usuario, no un descubrimiento nuevo: se implementarán más adelante. Mientras tanto, W2B se mantiene en el repositorio como referencia histórica, pero queda fuera de las fases de este plan hasta que se reactive o se reemplace.

> **Nota — desvío detectado en F0-08 (17/09):** el esquema de nodos de n8n-mcp no lista la opción "Allowed Origins (CORS)" del nodo Webhook, aunque sí existe en la documentación oficial de n8n y en el nodo real de esta instancia (v2.1). Se verificó contra la instancia viva con `validateOnly` y con tráfico real (`curl` variando el header `Origin`) antes de confiar en cualquiera de las dos fuentes: el campo es `parameters.options.allowedOrigins` y el servidor sí lo hace cumplir — refleja el origen configurado en `Access-Control-Allow-Origin` sin importar qué origen mande el cliente. Dicho esto, CORS solo lo hace cumplir el navegador: no es una barrera contra scripts/bots que ignoran esa cabecera, que es la amenaza que ya cubre el Header Auth de F0-01/F0-02/F0-03.

---

## Fase 1 — Documentación

> La fase de mejor relación ganancia/esfuerzo: 15 puntos de rúbrica, trabajo mecánico y **riesgo funcional nulo**. Si hay poco tiempo, es la que más mueve la aguja por hora invertida.

| ID | Tarea | Alcance | Esf. | Cómo se verifica | Hecho |
|---|---|---|---|---|---|
| F1-01 | Completar el campo `description` de cada workflow con propósito, sistemas integrados, área propietaria y canal de escalado | los 12 | ▪▪ | Ningún flujo del pipeline tiene `description: null` | ☐ |
| F1-02 | Renombrar nodos de integración a `[Servicio] - [Acción/Recurso]` | los 12 | ▪▪▪ | Los nodos que llaman a Outlook, Teams, Excel, Data Table y HTTP siguen el patrón | ☐ |
| F1-03 | Renombrar nodos de decisión a `[Lógica] - [Condición]` | los 12 | ▪▪ | Los IF y Switch siguen el patrón; desaparece `¿ok?` y similares sin contexto | ☐ |
| F1-04 | Eliminar los sufijos de copia-pega (`...1`, `...2`) | W1, W2B | ▪ | Ningún nodo conserva sufijo numérico automático | ☐ |
| F1-05 | Agregar sticky notes que justifiquen las decisiones de diseño en los dos flujos que no tienen ninguna | W4C, W4D | ▪▪ | Cada bloque funcional tiene una nota que explica **por qué**, no **qué** | ☐ |
| F1-06 | Renombrar con el prefijo `[SUB]` los workflows que son subflujos | W2A, W3, W4B, W5B | ▪ | El nombre distingue a simple vista un subflujo de un flujo principal | ☐ |

**Nota de estilo:** el patrón a replicar ya existe en el repositorio — `Nota - W5-A`, `Nota - W3 Motor` y la nota de contrato de W2A explican decisiones y dependencias, que es justo lo que pide el framework.

**Criterio de cierre:** los 12 con descripción completa, convención de nombres aplicada y al menos una nota por bloque funcional.

---

## Fase 2 — Validación de entrada

> Ningún flujo valida hoy su entrada. Al cerrar esta fase el pipeline cruza el **umbral de despliegue (75)**.

| ID | Tarea | Flujo · nodo | Esf. | Cómo se verifica | Hecho |
|---|---|---|---|---|---|
| F2-01 | Insertar un nodo de validación inmediatamente después del trigger, con rama de rechazo | los 12 | ▪▪▪ | Un payload sin campos requeridos se rechaza **antes** de leer o escribir en Data Table | ☐ |
| F2-02 | Que la rama de rechazo responda **HTTP 400 real** en los flujos con webhook | W2C, W4C, W4D | ▪▪ | Una petición inválida devuelve 400, no 200 con `ok:false` en el cuerpo | ☐ |
| F2-03 | Hacer que el consolidador lance excepción real, para que la rama de error 500 deje de ser inalcanzable | W4C · `Consolidar respuesta` | ▪▪ | Forzando un fallo, la respuesta sale por la rama de error con código 500 | ☐ |
| F2-04 | Validar `decision` contra un enum cerrado antes de tocar la base | W4D · `Extraer decisión del body` | ▪ | Una decisión no reconocida se rechaza con 400 sin leer Data Table | ☐ |
| F2-05 | Rechazar `id_solicitud` nulo o inválido en vez de aceptarlo como `null` | W2B · `Capturar ID de solicitud` | ▪ | Un envío sin identificador no llega a persistir nada | ☐ |
| F2-06 | Agregar rama por defecto al Switch de servicio, que hoy descarta en silencio | W3 · `Enrutar por servicio` | ▪ | Un servicio no reconocido produce error explícito y queda registrado | ☐ |
| F2-07 | Validar la salida del extractor de IA antes de usarla | W1 · `Information Extractor` | ▪▪ | Un correo sin datos extraíbles no genera un registro con campos inventados | ☐ |

**Criterio de cierre:** ningún flujo ejecuta lógica de negocio ni toca la base antes de comprobar que su entrada es válida.

---

## Fase 3 — Resiliencia e idempotencia

> ⚠️ **Límite de plataforma.** El framework pide reintentos con espera exponencial. n8n solo admite `maxTries` de 2 a 5 y `waitBetweenTries` como **delay fijo de 0 a 5000 ms**: no hay backoff exponencial nativo. Se adopta el máximo nativo como estándar y se implementa backoff real solo donde el costo lo justifica.

| ID | Tarea | Flujo · nodo | Esf. | Cómo se verifica | Hecho |
|---|---|---|---|---|---|
| F3-01 | `Retry On Fail` (5 intentos / 5000 ms) en todo nodo que llame a un servicio externo | los 12; faltan por completo en W2C, W4A, W5A, W6 | ▪▪ | Ningún nodo de red queda sin reintento configurado | ☐ |
| F3-02 | Backoff exponencial real con `Loop Over Items` + `Wait` en la generación de PDF | W3 · `Generar PDF (microservicio)` | ▪▪ | Ante fallos sucesivos, los intentos se espacian progresivamente | ☐ |
| F3-03 | `onError` con reversión de estado, para que una fila no quede atascada en estado intermedio | W5A · `Despachar a W5-B`, `Leer cotizaciones APROBADA` | ▪▪ | Forzando un fallo del despacho, la fila vuelve a un estado recuperable | ☐ |
| F3-04 | `onError` explícito en la reinvocación del motor | W4D · `Re-invocar motor` | ▪ | Una excepción del subflujo no tumba la ejecución completa | ☐ |
| F3-05 | Manejo de error en el nodo crítico que dispara guardado y cotización, hoy sin nada | W2B · `Ejecutar Guardar-y-Cotizar` | ▪▪ | Un fallo muestra al usuario el aviso amigable en vez de cortar en seco | ☐ |
| F3-06 | Reemplazar `continueRegularOutput` en las cadenas de alerta, para que un fallo de la propia alerta no se pierda | W4A, W6, W2A | ▪▪ | Un fallo al enviar la alerta queda registrado en algún lado | ☐ |
| F3-07 | Guarda de idempotencia antes de incrementar la ronda de corrección | W4D · `Guardar ronda + comentario` | ▪▪ | Enviar dos veces la misma decisión consume **una** ronda, no dos | ☐ |
| F3-08 | Clave de match en los registros de error que hoy insertan sin deduplicar | W5B · `Registrar error - Envío`; W2B · registros de error | ▪ | Reintentar no duplica filas en la tabla de errores | ☐ |
| F3-09 | Resolver la regeneración de `id_solicitud` por timestamp | W2C, W1 | ▪▪ | Reprocesar la misma solicitud de origen no crea un registro nuevo | ☐ |
| F3-10 | Reconciliación cuando una de las dos actualizaciones de estado falla y la otra no | W6 | ▪▪ | Un fallo parcial queda detectado y reportado, no silencioso | ☐ |
| F3-11 | Distinguir un PDF de 0 bytes de uno demasiado grande | W5B · `Evaluar adjunto` | ▪ | Un PDF corrupto genera alerta, no se envía como "solo enlace" | ☐ |

**Criterio de cierre:** ningún nodo de red sin reintento, ninguna escritura sin clave, ningún fallo que se pierda en silencio.

---

## Fase 4 — Arquitectura

> `F4-01` y `F4-02` tienen el mayor efecto multiplicador del plan: bajan el conteo de nodos de varios flujos a la vez y eliminan la duplicación que hoy penaliza a los 12.

| ID | Tarea | Alcance | Esf. | Cómo se verifica | Hecho |
|---|---|---|---|---|---|
| F4-01 | Crear `[SUB] - CCB - Registrar y Alertar Error` y reemplazar con él el patrón replicado en los 12 flujos | los 12 (triplicado en W1, tres bloques en W5B) | ▪▪▪ | El patrón existe en un solo lugar; los errores se siguen registrando y alertando igual | ☐ |
| F4-02 | Crear `[SUB] - CCB - Leer Contexto Propuesta` para el bloque de tres lecturas duplicado idéntico | W4B, W4C, W4D | ▪▪ | Los tres flujos leen el contexto invocando el mismo subflujo | ☐ |
| F4-03 | Partir el flujo de decisión en subflujos por rama: aprobar, cancelar, corregir con IA | W4D (43 nodos, 5 ramas) | ▪▪▪ | Ningún lienzo supera 20 nodos; los tres caminos siguen funcionando de punta a punta | ☐ |
| F4-04 | Extraer la lógica repetida de consolidación de criterios (4 copias con ~90% de código idéntico) | W2B | ▪▪ | La lógica vive en un solo lugar; las cuatro ramas de servicio siguen cotizando igual | ☐ |
| F4-05 | Evaluar separar la generación de PDF del cálculo de precio | W3 | ▪▪ | Decisión documentada; si se separa, ambos flujos bajo el umbral de nodos | ☐ |

**Criterio de cierre:** ningún flujo por encima de 20 nodos y ningún bloque lógico duplicado entre flujos.

---

## Fase 5 — Configuración centralizada

> El acceso a Variables de n8n sigue bloqueado por permisos. **Esta fase no lo espera:** usa una Data Table como fuente única de verdad, y migra a Variables si algún día se habilitan.

| ID | Tarea | Alcance | Esf. | Cómo se verifica | Hecho |
|---|---|---|---|---|---|
| F5-01 | Crear la Data Table `Configuracion_CCB` (clave/valor) con correo de alertas, datos del asesor, URL del microservicio y chat de aprobación | instancia | ▪ | La tabla existe y responde a una lectura de prueba | ☐ |
| F5-02 | Reemplazar el correo de alertas hardcodeado | los 10 flujos que lo tienen | ▪▪ | Cambiar el destinatario en un solo lugar se refleja en todos los flujos | ☐ |
| F5-03 | Sacar del código y de los parámetros la URL del microservicio, hoy duplicada en dos nodos | W3 | ▪ | Cambiar la URL en un solo lugar no requiere editar ningún flujo | ☐ |
| F5-04 | Parametrizar nombre y correo del asesor, hoy repetidos en cinco nodos | W3 | ▪▪ | Un cambio de asesor no exige tocar los templates | ☐ |
| F5-05 | Migrar a Variables nativas si Tecnología las habilita | los 12 | ▪▪ | Las lecturas de configuración apuntan a Variables sin cambiar la lógica | ☐ |

**Criterio de cierre:** ningún correo, URL ni identificador de destino escrito a mano dentro de un nodo.

---

## Fase 6 — Observabilidad

| ID | Tarea | Alcance | Esf. | Cómo se verifica | Hecho |
|---|---|---|---|---|---|
| F6-01 | `timeout` explícito en las llamadas HTTP | W3, W5B | ▪ | Una llamada colgada corta en el tiempo definido, no queda esperando | ☐ |
| F6-02 | Paginación o límite en las lecturas que hoy traen todo sin tope | W4A, W5A, W6 | ▪ | El volumen leído por ejecución está acotado | ☐ |
| F6-03 | Enmascarar PII antes de logs y alertas externas | W4B, W4D, W5B, W2C | ▪▪ | Las alertas identifican la solicitud sin exponer datos personales completos | ☐ |
| F6-04 | Revisar las variables de retención de ejecuciones a nivel de instancia | instancia — requiere Tecnología | ▪ | La retención está acotada y el disco deja de crecer sin control | ☐ |
| F6-05 | Monitorear las cuatro métricas del framework: tasa de ejecución, tasa de error por flujo (umbral 2%), latencia p95 y profundidad de cola | instancia | ▪▪ | Existe un punto donde consultar las cuatro y un umbral que dispara aviso | ☐ |

---

## Fase 7 — Guardarraíles de IA

> Lo que ya existe en W4D es sólido: salida estructurada con esquema obligatorio, modelo de respaldo y validación contra listas cerradas de valores. Falta cerrar el círculo.

| ID | Tarea | Flujo | Esf. | Cómo se verifica | Hecho |
|---|---|---|---|---|---|
| F7-01 | Enrutar `confianza: "baja"` a revisión humana en vez de aplicar el ajuste igual | W4D | ▪▪ | Una corrección con confianza baja queda detenida esperando decisión | ☐ |
| F7-02 | Kill switch para desactivar la corrección asistida por IA sin apagar el flujo entero | W4D | ▪▪ | Con el interruptor apagado, las correcciones van a revisión manual y el resto opera normal | ☐ |
| F7-03 | Mover la aprobación humana antes del recálculo y del incremento de ronda | W4D | ▪▪▪ | Ninguna ronda se consume sin que una persona lo haya autorizado | ☐ |

---

## Seguimiento por flujo

Se actualiza al cerrar cada fase, repitiendo el procedimiento de evaluación del informe.

| Flujo | Inicial | Actual | Objetivo | Fases que lo tocan |
|---|---|---|---|---|
| W1 — Extracción información | 50 | 50 | ≥90 | 1, 2, 3, 4, 5 |
| W2A — Guardar Criterios y Cotizar | 66 | 66 | ≥90 | 1, 2, 3, 5 |
| W2B — Formulario de Solicitud | 46 | 46 | ≥90 | 0, 1, 2, 3, 4, 5 |
| W2C — Recepción Formulario Externo | 54 | 54 | ≥90 | 0, 1, 2, 3, 5, 6 |
| W3 — Motor Criterios y Precio | 58 | 58 | ≥90 | 0, 1, 2, 3, 4, 5, 6 |
| W4A — Router de Aprobación | 63 | 63 | ≥90 | 1, 2, 3, 5, 6 |
| W4B — Aprobación (Teams) | 60 | 60 | ≥90 | 0, 1, 2, 3, 4, 5, 6 |
| W4C — Consultar Propuesta | 42 | 42 | ≥90 | 0, 1, 2, 4, 5 |
| W4D — Procesar Decisión | 34 | 34 | ≥90 | 0, 1, 2, 3, 4, 5, 6, 7 |
| W5A — Router de Envío | 60 | 60 | ≥90 | 1, 2, 3, 5, 6 |
| W5B — Envío al Cliente | 52 | 52 | ≥90 | 0, 1, 2, 3, 4, 5, 6 |
| W6 — Finalizador | 58 | 58 | ≥90 | 0, 1, 2, 3, 5 |
| **Promedio** | **53,6** | **53,6** | **≥90** | |

---

## Definición de "hecho"

Una fase está cerrada cuando se cumplen las cuatro condiciones:

1. Todas sus tareas están marcadas **con su verificación ejecutada**, no solo aplicada.
2. El flujo afectado corrió de punta a punta al menos una vez sin errores nuevos.
3. Los JSON se re-exportaron con `scripts/export_workflows.py` y se commitearon.
4. El puntaje nuevo quedó anotado en la tabla de seguimiento.

---

## Dependencias externas

Ninguna impide llegar a 90, pero conviene tenerlas a la vista:

| Bloqueo | Qué frena | Cómo se avanza igual |
|---|---|---|
| Variables de n8n no habilitadas | Configuración centralizada nativa | Data Table `Configuracion_CCB` (Fase 5) |
| Sin token de MCP a nivel de instancia | Pruebas oficiales con datos fijados | Pruebas manuales con la matriz de casos interna |
| Sin instancia de *staging* | Probar fuera de producción | Límite real: Testing no llega a 15/15 sin esto |
| Microservicio de PDF sobre túnel temporal | Estabilidad del camino crítico | Deploy con dominio propio y proxy inverso |
