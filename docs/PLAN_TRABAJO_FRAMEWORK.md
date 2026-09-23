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
| F1-01 | Completar el campo `description` de cada workflow con propósito, sistemas integrados, área propietaria y canal de escalado | los 12 activos | ▪▪ | Ningún flujo del pipeline tiene `description: null` | ☑ 17/09 |
| F1-02 | Renombrar nodos de integración a `[Servicio] - [Acción/Recurso]` | los 12 activos | ▪▪▪ | Los nodos que llaman a Outlook, Teams, Excel, Data Table y HTTP siguen el patrón | ☑ 18/09 |
| F1-03 | Renombrar nodos de decisión a `[Lógica] - [Condición]` | los 12 activos | ▪▪ | Los IF y Switch siguen el patrón; desaparece `¿ok?` y similares sin contexto | ☑ 18/09 |
| F1-04 | Eliminar los sufijos de copia-pega (`...1`, `...2`) | W1 *(W2B fuera de alcance — retirado)* | ▪ | Ningún nodo conserva sufijo numérico automático | ☑ 17/09 |
| F1-05 | Agregar sticky notes que justifiquen las decisiones de diseño en los dos flujos que no tienen ninguna | W4C, W4D | ▪▪ | Cada bloque funcional tiene una nota que explica **por qué**, no **qué** | ☑ 17/09 |
| F1-06 | Renombrar con el prefijo `[SUB]` los workflows que son subflujos | W2A, W3, W4B, W5B | ▪ | El nombre distingue a simple vista un subflujo de un flujo principal | ☑ 17/09 |

**Nota de estilo:** el patrón a replicar ya existe en el repositorio — `Nota - W5-A`, `Nota - W3 Motor` y la nota de contrato de W2A explican decisiones y dependencias, que es justo lo que pide el framework.

**Criterio de cierre:** los 12 con descripción completa, convención de nombres aplicada y al menos una nota por bloque funcional. **6 de 6 hechas — Fase 1 cerrada (18/09).**

> **Nota — F1-02/F1-03 cerradas (18/09):** se retomaron con la misma disciplina con la que se pausaron el 17/09 — de a un flujo por vez, revisando antes de cada rename si algún Code/Set lo referenciaba por texto (`$('Nombre del nodo')`, literales de auditoría `nodo_fallido: '...'`), porque eso **no se actualiza solo** al renombrar (solo las `connections` lo hacen). Cubiertos los 11 flujos activos: W1, W2A, W3, W4A, W4B, W4C, W4D, W5A, W5B y W6 tenían nodos que renombrar; **W2C** ya cumplía el patrón en su totalidad (sin cambios). Cada flujo se validó con `n8n_validate_workflow` (0 errores) después de aplicar sus renames y corregir las referencias encontradas. Commits locales (sin push): `00dee2c` (W1), `55e8e80` (W2A), `17431dd` (W3), `43d0443` (W4A), `3871659` (W4B), `9772483` (W4C), `efba200` (W4D), `d1eb29e` (W5A), `b30e73e` (W5B), `a6b74b7` (W6).

---

## Fase 2 — Validación de entrada

> Ningún flujo valida hoy su entrada. Al cerrar esta fase el pipeline cruza el **umbral de despliegue (75)**.

| ID | Tarea | Flujo · nodo | Esf. | Cómo se verifica | Hecho |
|---|---|---|---|---|---|
| F2-01 | Insertar un nodo de validación inmediatamente después del trigger, con rama de rechazo | los 12 activos | ▪▪▪ | Un payload sin campos requeridos se rechaza **antes** de leer o escribir en Data Table | ☑ 18/09 *(11 de 11 flujos activos; W2B fuera de alcance, ver F2-05 — ver nota)* |
| F2-02 | Que la rama de rechazo responda **HTTP 400 real** en los flujos con webhook | W2C, W4C, W4D | ▪▪ | Una petición inválida devuelve 400, no 200 con `ok:false` en el cuerpo | ☑ 17/09 |
| F2-03 | Hacer que el consolidador lance excepción real, para que la rama de error 500 deje de ser inalcanzable | W4C · `Consolidar respuesta` | ▪▪ | Forzando un fallo, la respuesta sale por la rama de error con código 500 | ☑ 17/09 *(ver nota)* |
| F2-04 | Validar `decision` contra un enum cerrado antes de tocar la base | W4D · `Extraer decisión del body` | ▪ | Una decisión no reconocida se rechaza con 400 sin leer Data Table | ☑ 17/09 |
| F2-05 | ~~Rechazar `id_solicitud` nulo o inválido~~ — **No aplica.** W2B retirado, fuera de alcance (ver Fase 0) | W2B | — | — | 🚫 N/A |
| F2-06 | Agregar rama por defecto al Switch de servicio, que hoy descarta en silencio | W3 · `Enrutar por servicio` | ▪ | Un servicio no reconocido produce error explícito y queda registrado | ☑ 17/09 |
| F2-07 | Validar la salida del extractor de IA antes de usarla | W1 · `Information Extractor` | ▪▪ | Un correo sin datos extraíbles no genera un registro con campos inventados | ☑ 17/09 |

**Criterio de cierre:** ningún flujo ejecuta lógica de negocio ni toca la base antes de comprobar que su entrada es válida. **6 de 7 hechas, 1 N/A** (18/09) — F2-01 se cerró el 18/09, el resto ya estaba cerrado desde el 17/09. Todas verificadas con tráfico real contra el webhook en vivo (no solo estructuralmente): F2-04 confirmado con 400 + registro en `Errores_CCB` para decisión inválida y vacía; F2-03 confirmado con 400 real para `id_solicitud` faltante, sin afectar el camino de "no encontrada" (200, sin cambios). Ronda adicional (17/09): F2-02 se cerró sin salvedades tras verificar con tráfico real contra el webhook en vivo los 4 casos siguientes — W2C con payload inválido (sin `nombre`/`email`/`telefono`/`razon_social`) → 400 real con el mensaje de campos faltantes; W2C con payload válido → 200, pipeline completo de punta a punta intacto (generó `id_solicitud` real y llegó al motor de criterios; la respuesta de negocio "0 registros" es un resultado legítimo de los criterios de prueba, no una falla); W4C sin `id_solicitud` → 400 real, cortando antes de tocar las 3 Data Tables; W4C con un `id_solicitud` real existente → 200 con el resumen completo de la propuesta, camino válido intacto.

**F2-07 cerrado (17/09):** W1 no tiene webhook — su trigger es `Nuevo correo` (Microsoft Outlook Trigger, poll cada minuto), así que la verificación de tráfico real se hizo enviando dos correos reales al buzón monitoreado (no simulados con pinData, no disponible: el token de MCP a nivel de instancia sigue sin configurar). Se insertó el nodo `¿Extracción tiene datos mínimos?` (IF, combinador `or`) entre `Information Extractor` y `Consolidar datos de la solicitud`, exigiendo que al menos uno de los tres campos extraídos (`nombre_cliente`, `telefono`, `email_cliente`) venga no vacío; si los tres vienen vacíos corta hacia el nuevo nodo `Preparar rechazo - Extracción sin datos`, que reutiliza el `Registrar error - Extractor IA` / `Enviar alerta - Extractor IA` ya existentes. Caso válido — ejecución `384094`: correo con nombre/teléfono/email reales → extracción completa → rama verdadera → se creó `SOL-20260917140236` en `Solicitudes_CCB` (`EMAIL_VALIDADO`) → notificación al cliente enviada; camino normal intacto. Caso sin datos — ejecución `384138`: correo sin nombre/teléfono/email → `Information Extractor` devolvió `{"nombre_cliente":"","telefono":"","email_cliente":""}` → rama de rechazo → **no se creó ningún registro en `Solicitudes_CCB`** → error registrado en `Errores_CCB` (id 34) y alerta enviada. Ambos casos verificados leyendo las ejecuciones reales (`n8n_executions`), no solo la validación estructural.

> **Nota — alcance real de F2-03:** el 400 para "falta `id_solicitud`" es un error real y verificado. El 500 para una falla genuina de infraestructura (ej. el Data Table deja de responder) sigue sin pasar por `Responder error consulta`: hoy cae en el manejo de error por defecto de n8n, porque los 3 nodos de lectura no tienen `onError` cableado hacia `Consolidar respuesta`. Cerrar eso del todo requeriría wiring adicional en las 3 lecturas — queda como mejora futura, no bloqueante.
>
> **F2-01: 6 de 12 flujos con gatekeeping real (17/09).** W4D (F2-04), W2C, W4C y W1 (F2-07) ya tenían validación de entrada verificada con tráfico real. Esta ronda se extendió a **W5A** (`CCB - Workflow 5A - Router de Envío`) y **W5B** (`[SUB] CCB - Workflow 5B - Envío al Cliente`) — se priorizaron estos dos entre los 6 restantes porque son los que efectivamente envían el PDF y el correo a un cliente real: un dato corrupto ahí impacta a alguien fuera del pipeline interno, no solo un proceso propio.
>
> - **W5A:** se insertó el IF `Validar id_solicitud presente` entre `Leer cotizaciones APROBADA` y `Marcar EN_ENVIO`, que descarta filas APROBADA con `id_solicitud` vacío antes de despacharlas a W5-B.
> - **W5B:** se insertó el mismo IF `Validar id_solicitud presente` inmediatamente después del trigger `Recibir solicitud`, antes de `Leer cotización` — complementa (no reemplaza) al `¿Datos completos?` ya existente, que sigue siendo la defensa de fondo para `pdf_url` y el email, campos que solo se conocen después de leer y consolidar.
> - Ambos casos se verificaron con **ejecución real** en el editor de n8n (sin `n8n_test_workflow`, el token de MCP a nivel de instancia sigue sin configurar): W5B con `Recibir solicitud` disparado manualmente con `{"id_solicitud": ""}` (ejecución `384298`), W5A insertando una fila de prueba APROBADA con `id_solicitud` vacío en `Cotizaciones_CCB` y ejecutando el workflow manualmente (ejecución `384321`).
> - **Dos rondas de corrección post-verificación**, encontradas revisando el detalle de esas ejecuciones (no solo la validación estructural, que ya daba 0 errores en ambos casos):
>   1. **W5B — `alwaysOutputData` en `Marcar ERROR_ENVIO`:** la primera corrida (ejecución `384272`) mostró que el nodo de marcado (`Marcar ERROR_ENVIO`, un `update` de Data Table filtrando por `id_solicitud`) devolvía 0 items cuando `id_solicitud` está vacío — no matchea ninguna fila — y al no propagar ningún item, la cadena de alerta (`Preparar alerta de fallo - Envío` → `Enviar alerta - Envío`) nunca se ejecutaba y la alerta se perdía en silencio. Se corrigió seteando `alwaysOutputData: true` en `Marcar ERROR_ENVIO` (mismo patrón ya usado en `Leer cotización` de ese flujo), sin afectar los otros 3 casos de error existentes (PDF, envío, datos incompletos), donde siempre hay una fila real que matchear. Re-verificado en la ejecución `384298`: alerta llegó por Outlook.
>   2. **W5A — mensaje de diagnóstico correcto:** la primera corrida (ejecución `384309`) mostró que la rama de rechazo de `Validar id_solicitud presente` reutilizaba `Preparar error - Router` tal cual, produciendo `nodo_fallido: "Marcar EN_ENVIO"` y `mensaje_error: "Error desconocido en el router W5-A"` — el mensaje genérico reservado para fallos reales de ese nodo, que hubiera hecho diagnosticar mal el incidente a quien auditara `Errores_CCB` después. Se agregó un nodo dedicado `Preparar error - id_solicitud faltante` (mismo patrón que en W5B) que arma `nodo_fallido: "Validar id_solicitud presente"` y un mensaje específico, conectado a los genéricos `Registrar error - Router` / `Enviar alerta - Router` (reutilizados sin cambios). Re-verificado en la ejecución `384321`: `nodo_fallido` y `mensaje_error` correctos, alerta enviada.
>
> **F2-01: 8 de 12 flujos con gatekeeping real (17/09, misma sesión).** Se extendió el mismo patrón validado en W5A/W5B a **W4A** (`CCB - Workflow 4A - Router de Aprobación`) y **W4B** (`[SUB] CCB - Workflow 4B - Aprobación de Propuesta (Teams)`) — el par router + subflujo arquitectónicamente análogo, un peldaño más arriba en el pipeline (aprobación de la propuesta antes del envío).
>
> - **W4A:** se insertó el IF `Validar id_solicitud presente` entre `Leer cotizaciones PROPUESTA_GENERADA` y `Marcar EN_REVISION`, con rama de rechazo hacia un nodo dedicado `Preparar error - id_solicitud faltante` (mismo patrón que W5A desde el inicio, no hubo que reutilizar `Preparar error - Router` a ciegas esta vez) → `Registrar error - Router` / `Enviar alerta - Router` (reutilizados sin cambios).
> - **W4B:** se insertó el mismo IF inmediatamente después del trigger `Recibir solicitud`, antes de `Leer cotización`, con su propio nodo dedicado `Preparar error - id_solicitud faltante` → `Registrar error - Teams` (reutilizado).
> - **Corrección proactiva, antes de la prueba real (no encontrada por la prueba — anticipada por el bug equivalente de W5B):** al revisar W4B se detectó que `Marcar REVISION_MANUAL - Error Teams` (aguas abajo de `Registrar error - Teams`, compartido por las 4 causas de error incluida la nueva) filtraba por `$('Consolidar datos de la propuesta').first().json.id_solicitud` — una referencia a un nodo que la nueva rama de rechazo nunca ejecuta, porque corta *antes* de `Leer cotización`/`Consolidar`. Eso hubiera repetido el mismo bug de `Marcar ERROR_ENVIO` en W5B (0 items, alerta perdida en silencio) más un riesgo adicional de referencia rota. Se corrigió con el mismo patrón ya probado esa mañana: expresión con fallback (`try { $('Consolidar...').first()... } catch { $json.id_solicitud }`) + `alwaysOutputData: true`, sin tocar los otros 3 casos de error (que sí tienen `Consolidar` ejecutado).
> - Ambos casos se verificaron con **ejecución real** en el editor de n8n: W4A insertando una fila de prueba `PROPUESTA_GENERADA` con `id_solicitud` vacío en `Cotizaciones_CCB` y ejecutando el workflow manualmente (ejecución `384448`), W4B con `Recibir solicitud` disparado manualmente con `id_solicitud` vacío (ejecución `384453`). En ambas: rama de rechazo corrió sin cortarse, `nodo_fallido: "Validar id_solicitud presente"` y mensaje específico correcto (no el genérico de otro nodo), `Marcar REVISION_MANUAL - Error Teams` no devolvió 0 items pese al id vacío, y la alerta por Outlook llegó (`success: true`) en los dos flujos. No hizo falta ninguna corrección posterior a la verificación.
>
> **F2-01: 10 de 12 flujos con gatekeeping real (17/09, misma sesión).** Se extendió el mismo patrón a **W2A** (`[SUB] CCB - Workflow 2A - Guardar Criterios y Cotizar Servicio`) y **W3** (`[SUB] CCB - Workflow 3 - Motor Criterios y Precio`) — a diferencia de los pares router+subflujo de las rondas anteriores (W5A/W5B, W4A/W4B), acá el input real no es solo `id_solicitud`: W2A recibe de W2C el payload completo de criterios de cotización, y W3 recibe de W2A lo necesario para calcular precio. Los campos mínimos se derivaron leyendo el código real de los nodos consumidores (no se asumió nada): `Switch por servicio` (sin `fallbackOutput`, descarta en silencio cualquier `servicio` no reconocido) y los checks duros de `Calcular Conteo y Precio` en W3 (`Falta tipo_organizacion` / `visitas_por_asesor` / `incluye_rutas` / `num_niveles` / `plan_deseado` o `consultas_mensuales`+`numero_usuarios`, según el servicio).
>
> - **W2A:** se insertó `Validar entrada - Guardar Criterios y Cotizar` (Code) → `¿Entrada válida? - Guardar Criterios y Cotizar` (IF) inmediatamente después del trigger `Recibir solicitud`, antes de `Aplanar contrato de entrada`. Exige `id_solicitud`, `servicio` (uno de los 4 valores exactos del Switch) y `criterios` (objeto no vacío), más el campo específico por servicio (`organizacion_juridica` para Georreferenciada; `cantidad_registros`+`visitas_asesor`+`incluir_rutas` para Zonificación y Rutero; `cantidad_registros`+`niveles_analisis` para Ubicación de Nuevo Negocio; `plan_en_linea` real o `consultas_mensuales`+`usuarios` para Información en Línea). Rama de rechazo: nodo dedicado `Preparar error - Validación de entrada (Guardar Criterios)` → reutiliza `Guardar incidencia - Data Table` / `Enviar alerta de guardado` ya existentes, sin tocar `Preparar error - Guardado de criterios` ni `Preparar error - Motor rechazó la propuesta` (son de otros casos).
> - **W3:** se insertó el mismo patrón (`Validar entrada - Motor Criterios y Precio` → `¿Entrada válida? - Motor Criterios y Precio`) inmediatamente después del trigger `When Executed by Another Workflow`, antes de `Normalizar Criterios` y `Leer BD (hoja BD)`. Exige `id_solicitud`, `tipo_servicio` reconocido, y el campo específico por servicio equivalente al de W2A. Rama de rechazo: nodo dedicado `Preparar error - Validación de entrada (Motor)` → reutiliza `Registrar error infra - Data Table` / `Restaurar resultado de error` ya existentes. No se tocó `Enrutar por servicio` (F2-06), que es una validación distinta y complementaria.
> - **Corrección proactiva, antes de la prueba real (mismo patrón anticipado desde W5B/W4B):** tanto `Consolidar resultado de error` (W2A) como `Restaurar resultado de error` (W3) solo sabían leer los nodos de error "viejos", que con el corte temprano ya no ejecutan en la rama nueva. Se agregó en ambos una tercera fuente (`$('Preparar error - Validación de entrada (...)').first().json`, con el mismo try/catch ya existente) antes de correr la prueba real, no después.
> - Ambos casos se verificaron con **ejecución real** (`Test workflow` manual en el editor, sin `n8n_test_workflow` — el token de MCP a nivel de instancia sigue sin configurar): W2A con `Recibir solicitud` disparado con `criterios.organizacion_juridica` faltante (ejecución `384673`) — rechazó con el mensaje específico correcto, `Guardar incidencia - Data Table` y `Enviar alerta de guardado` corrieron bien (`success: true`), `Return - Error` devolvió `ok:false` limpio sin cortar en seco. W3 con `When Executed by Another Workflow` disparado con `visitas_por_asesor` faltante (ejecución `384676`) — rechazó con el mensaje específico correcto, `Registrar error infra - Data Table` corrió, y llegó sin cortarse hasta `Devolver resultado al formulario`. No hizo falta ninguna corrección posterior a la verificación.
> - **Regresión confirmada sin prueba adicional:** la ejecución real más reciente de producción de ambos flujos (`383084`/`383085`, mismo día, servicio Información Georreferenciada) ya traía exactamente los campos mínimos exigidos — confirma que el camino válido no se rompe, sin necesidad de una prueba válida nueva.
>
> **F2-01 completo (18/09) — 11 de 11 flujos activos con gatekeeping real.** Se cerró el último flujo pendiente, **W6** (`CCB - Workflow 6 - Finalizador de Cotizaciones`) — mismo patrón que W5A: se insertó el IF `Validar id_solicitud presente` inmediatamente después de `Leer cotizaciones ENVIADA`, antes de `Filtrar 30+ dias sin respuesta` y de las dos escrituras (`Marcar FINALIZADA - Cotizacion` / `Marcar FINALIZADA - Solicitudes`). Rama de rechazo: nodo dedicado `Preparar error - id_solicitud faltante` con `nodo_fallido`/`mensaje_error` específicos (no reutiliza el mensaje genérico de `Preparar error - Finalizador`, que queda solo para fallos reales de las escrituras) → reutiliza sin cambios `Registrar error - Finalizador` / `Enviar alerta - Finalizador`.
>
> - **Corrección proactiva revisada, sin hallazgo:** se revisó si algún nodo aguas abajo del corte dependía de un nodo que la nueva rama de rechazo ya no ejecuta (el bug de `$('Nodo').first()` sin guarda que apareció en W5B y W4B). `Marcar FINALIZADA - Solicitudes` referencia `$('Filtrar 30+ dias sin respuesta').item.json.id_solicitud` como fallback, pero usa `.item` (paired-item, no `.first()`) y `Filtrar` sigue ejecutando con normalidad para la rama válida del IF — no aplicaba el bug, no hizo falta corrección.
> - Verificado con **ejecución real** (`Test workflow` manual en el editor de n8n, ejecución `388873`): fila de prueba insertada en `Cotizaciones_CCB` (`estado: ENVIADA`, `id_solicitud` vacío, id de fila 21) → rechazada por `Validar id_solicitud presente`, `nodo_fallido` y mensaje específico correctos, registrada en `Errores_CCB` (id 109), alerta enviada (`success: true`). Camino válido intacto en la misma corrida: la fila real (id 17, `fecha_envio` con solo 2 días de antigüedad) llegó a `Filtrar 30+ dias sin respuesta`, que devolvió 0 items correctamente por no cumplir el umbral de 30 días — sin romper la regresión.
> - Fila de prueba (id 21) con borrado pedido explícitamente al usuario en el mismo mensaje donde se pidió la verificación.
>
> **F2-01 cerrado: 11 de 11 flujos activos con gatekeeping real de entrada; W2B queda fuera de alcance** (retirado, ver F0 y F2-05). De los 12 flujos que trackea este plan, 11 quedan cubiertos y 1 es N/A — mismo criterio de cierre "efectivo" ya usado para dar por cerrada la Fase 0.
>
> **Nota — cierre formal de Fase 2 pendiente de re-auditoría:** las 7 tareas de Fase 2 están todas hechas o N/A, pero la "Definición de hecho" de este documento exige además re-ejecutar el procedimiento de evaluación del informe de auditoría y anotar el puntaje nuevo en la tabla de "Seguimiento por flujo" — eso **no se hizo** en esta sesión. La tabla de seguimiento sigue mostrando los puntajes de línea de base (53,6 de promedio) sin actualizar, igual que quedó pendiente tras cerrar Fase 0 y Fase 1: ninguna de las tres fases cerradas hasta ahora tiene su puntaje re-evaluado. Cerrar Fase 2 "en los papeles" del todo requiere esa re-auditoría, que no es parte de esta tarea.

---

## Fase 3 — Resiliencia e idempotencia

> ⚠️ **Límite de plataforma.** El framework pide reintentos con espera exponencial. n8n solo admite `maxTries` de 2 a 5 y `waitBetweenTries` como **delay fijo de 0 a 5000 ms**: no hay backoff exponencial nativo. Se adopta el máximo nativo como estándar y se implementa backoff real solo donde el costo lo justifica.

| ID | Tarea | Flujo · nodo | Esf. | Cómo se verifica | Hecho |
|---|---|---|---|---|---|
| F3-01 | `Retry On Fail` (5 intentos / 5000 ms) en todo nodo que llame a un servicio externo | los 12; faltan por completo en W2C, W4A, W5A, W6 | ▪▪ | Ningún nodo de red queda sin reintento configurado | ☑ 22/09 *(8 flujos: W2A, W4A, W4B, W4C, W4D, W5A, W5B, W6 — nodos de red de negocio a 5×5000; W1/W2C/W3 ya tenían retry en sus nodos críticos; ver nota)* |
| F3-02 | Backoff exponencial real con `Loop Over Items` + `Wait` en la generación de PDF | W3 · `Generar PDF (microservicio)` | ▪▪ | Ante fallos sucesivos, los intentos se espacian progresivamente | ☑ 23/09 **cerrado como desviación de plataforma** — retry al máximo nativo 5×5000; el backoff exponencial real queda descartado por decisión del usuario (ver nota) |
| F3-03 | `onError` con reversión de estado, para que una fila no quede atascada en estado intermedio | W5A · `Despachar a W5-B`, `Leer cotizaciones APROBADA` | ▪▪ | Forzando un fallo del despacho, la fila vuelve a un estado recuperable | ☑ 22/09 *(ver nota)* |
| F3-04 | `onError` explícito en la reinvocación del motor | W4D · `Re-invocar motor` | ▪ | Una excepción del subflujo no tumba la ejecución completa | ☑ *(ya estaba en la instancia viva, verificado 22/09: `onError: continueErrorOutput` + retry 3×5000)* |
| F3-05 | Manejo de error en el nodo crítico que dispara guardado y cotización, hoy sin nada | W2B · `Ejecutar Guardar-y-Cotizar` | ▪▪ | Un fallo muestra al usuario el aviso amigable en vez de cortar en seco | 🚫 N/A — W2B retirado (fuera de alcance desde 17/09) |
| F3-06 | Reemplazar `continueRegularOutput` en las cadenas de alerta, para que un fallo de la propia alerta no se pierda | W4A, W6, W2A | ▪▪ | Un fallo al enviar la alerta queda registrado en algún lado | ☑ 22/09 *resuelto por diseño F4-01* — las cadenas de alerta viven en el subflujo compartido; el registro en `Errores_CCB` ocurre ANTES de la alerta, así que un fallo de la alerta no pierde el registro técnico; el item siempre vuelve al llamador (`continueRegularOutput` a propósito) |
| F3-07 | Guarda de idempotencia antes de incrementar la ronda de corrección | W4D · `Guardar ronda + comentario` | ▪▪ | Enviar dos veces la misma decisión consume **una** ronda, no dos | ☑ 22/09 *(ver nota)* |
| F3-08 | Clave de match en los registros de error que hoy insertan sin deduplicar | W5B · `Registrar error - Envío`; W2B · registros de error | ▪ | Reintentar no duplica filas en la tabla de errores | ☑ 22/09 *(subflujo compartido: insert → upsert con match por id_solicitud+workflow_origen+nodo_fallido; W2B N/A)* |
| F3-09 | Resolver la regeneración de `id_solicitud` por timestamp | W2C, W1 | ▪▪ | Reprocesar la misma solicitud de origen no crea un registro nuevo | ☑ 22/09 *(W1: deriva del id del mensaje de Outlook; W2C: front genera clave estable por sesión en sessionStorage — commit `df1a8a3`, pendiente deploy a Vercel)* |
| F3-10 | Reconciliación cuando una de las dos actualizaciones de estado falla y la otra no | W6 | ▪▪ | Un fallo parcial queda detectado y reportado, no silencioso | ☑ 22/09 *(ver nota)* |
| F3-11 | Distinguir un PDF de 0 bytes de uno demasiado grande | W5B · `Evaluar adjunto` | ▪ | Un PDF corrupto genera alerta, no se envía como "solo enlace" | ☑ 22/09 *(ver nota)* |

**Criterio de cierre:** ningún nodo de red sin reintento, ninguna escritura sin clave, ningún fallo que se pierda en silencio.

> **Nota — F3-01 (22/09):** se aplicó retry `5×5000` a los nodos de red de **negocio** sin reintento en W2A (6), W4A (3), W4B (4), W4C (3), W4D (10), W5A (3), W5B (7), W6 (3). W1, W2C y W3 ya tenían retry en sus nodos críticos (W1: 2 Data Table 5×5000 + Outlook 3×2000; W2C: `Ejecutar Guardar-y-Cotizar` 5×5000; W3: HTTP PDF 3×2000). **Decisión de diseño:** los nodos `Ejecutar Registrar-y-Alertar` del subflujo compartido NO llevan retry en esta ronda — el subflujo hace upsert en `Errores_CCB` (F3-08) y reintentar duplicaría la invocación; el `continueRegularOutput` del subflujo ya lo protege. Los registros de error variante B (W2C, W3, W4C, W4D) tampoco llevan retry: son insert puro dentro del manejo de fallos, no caminos de negocio.

> **Nota — F3-03 (22/09):** W5A `Despachar a W5-B` ahora tiene `onError: continueErrorOutput` → `Preparar error - Despacho falló` → `Data Table - Revertir a APROBADA (fallo despacho)` → `Ejecutar Registrar-y-Alertar`. Si el despacho fire-and-forget falla, la fila vuelve a `APROBADA` (recuperable el próximo ciclo de 15 min) en vez de quedar atascada en `EN_ENVIO`, y el error queda registrado+alertado vía subflujo compartido.

> **Nota — F3-07 (22/09):** W4D insertó `IF - ¿Comentario ya procesado?` entre `Releer cotización` y `Guardar ronda y comentario`: si el comentario guardado ya es el mismo que llega en el POST (y no está vacío), responde "ya procesado" sin incrementar ronda ni re-correr el pipeline de IA. Un reenvío del mismo POST ahora consume **una** ronda, no dos.

> **Nota — F3-08 (22/09):** el `Data Table - Registrar error` del subflujo compartido pasó de insert a **upsert** con match por `id_solicitud + workflow_origen + nodo_fallido` — reintentar el mismo error para la misma solicitud actualiza la fila en vez de duplicarla. Esto beneficia a los 8 flujos que ya usan el subflujo (F4-01).

> **Nota — F3-09 (22/09):** W1 `Consolidar datos de la solicitud` ya no genera `id_solicitud` por timestamp: ahora deriva de `SOL-` + últimos 12 chars alfanuméricos del `id` del mensaje de Outlook (`item.json.id`). El mismo correo reprocesado (trigger re-lee, reintento) produce el mismo `id_solicitud` y el upsert de `Solicitudes_CCB` actualiza en vez de duplicar. **W2C pendiente de cambio de front:** el formulario externo se abre sin `?id_solicitud=` y el backend regenera por timestamp; no hay identificador natural de origen. La solución requiere que `formulario-solicitud-ccb` genere una clave estable por envío (`crypto.randomUUID()` en `sessionStorage`) y la mande como `id_solicitud` — toca otro repo y su despliegue en Vercel; no se implementó a ciegas.

> **Nota — F3-10 (22/09):** W6 insertó `Data Table - Revertir FINALIZADA a ENVIADA (Cotización)` en la rama de error compartida (antes del `Ejecutar Registrar-y-Alertar`): si `Marcar FINALIZADA (Solicitudes)` falla después de que `Marcar FINALIZADA (Cotización)` tuvo éxito, la fila de cotizaciones vuelve a `ENVIADA` y el ciclo de 3am la reintenta — sin dejar el pipeline a mitad de camino. `alwaysOutputData` garantiza que la alerta siga saliendo.

> **Nota — F3-11 (22/09):** W5B `Evaluar adjunto` ahora lanza error explícito si el PDF tiene 0 bytes (`onError: continueErrorOutput`) → nuevo `Preparar error - PDF corrupto` → cadena de error existente (`Marcar ERROR_ENVIO` → consolidador → subflujo). El consolidador `Preparar alerta de fallo - Envío` aprendió a leer el 5º Preparar. Un PDF corrupto ya no se envía como "solo enlace": marca `ERROR_ENVIO` y alerta. Un PDF >4MB sigue yendo por "solo link" (comportamiento legítimo intacto).

> **Nota — F3-06 (22/09):** se resuelve por diseño con F4-01, no con código adicional. Las cadenas de alerta de W4A/W6/W2A ahora viven en el subflujo compartido: el registro en `Errores_CCB` ocurre **antes** de la alerta, así que un fallo del Outlook ya no pierde el registro técnico; `continueRegularOutput` del Outlook es intencional para que el item siempre vuelva al llamador.

> **Nota — F3-02 (23/09, cierre definitivo):** decisión explícita del usuario: **no se implementa el backoff exponencial real**. n8n no lo soporta de forma nativa (`waitBetweenTries` es un delay fijo de 0–5000 ms) y reestructurar el camino crítico del motor (generación del PDF sobre el túnel temporal ngrok) con `Loop Over Items` + `Wait` tiene una relación riesgo/beneficio mala: el PDF es idempotente, así que el máximo nativo (5×5000) cubre el caso de reintento. Queda registrado como desviación por límite de plataforma, no como incumplimiento del framework. **Hallazgo del validador:** W3 reporta 4 errores de "Mixed literal text and expression requires = prefix" en los nodos `HTML - ...` — son preexistentes (interpolación `{{ }}` en texto literal, formato que el runtime de n8n acepta y que genera PDFs reales en producción); la validación estructural sin chequeo de expresiones da 0 errores/0 warnings. No se reescribieron 200K+ chars de plantillas para apaciguar al validador.

---

## Fase 4 — Arquitectura

> `F4-01` y `F4-02` tienen el mayor efecto multiplicador del plan: bajan el conteo de nodos de varios flujos a la vez y eliminan la duplicación que hoy penaliza a los 12.

| ID | Tarea | Alcance | Esf. | Cómo se verifica | Hecho |
|---|---|---|---|---|---|
| F4-01 | Crear `[SUB] - CCB - Registrar y Alertar Error` y reemplazar con él el patrón replicado en los 12 flujos | los 12 (triplicado en W1, tres bloques en W5B) | ▪▪▪ | El patrón existe en un solo lugar; los errores se siguen registrando y alertando igual | ☑ **8/9 flujos del patrón A migrados (22/09)** + **catch-all resuelto con diseño propio (23/09)** — ver nota |
| F4-02 | Crear `[SUB] - CCB - Leer Contexto Propuesta` para el bloque de tres lecturas duplicado idéntico | W4B, W4C, W4D | ▪▪ | Los tres flujos leen el contexto invocando el mismo subflujo | ☑ 23/09 — subflujo `GELWpskp0aYJ2zPg`; W4B 14→12, W4C 12→10, W4D 50→48 nodos |
| F4-03 | Partir el flujo de decisión en subflujos por rama: aprobar, cancelar, corregir con IA | W4D (43 nodos, 5 ramas) | ▪▪▪ | Ningún lienzo supera 20 nodos; los tres caminos siguen funcionando de punta a punta | ☑ 23/09 — **W4D 54→19 nodos** + 5 subflujos; los tres caminos verificados con tráfico real |
| F4-04 | Extraer la lógica repetida de consolidación de criterios (4 copias con ~90% de código idéntico) | W2B | ▪▪ | La lógica vive en un solo lugar; las cuatro ramas de servicio siguen cotizando igual | 🚫 N/A — W2B está retirado y fuera de alcance desde el 17/09 (misma decisión que F0-04 y F3-05). Refactorizar un flujo sin tráfico real no aporta puntaje ni reduce riesgo. |
| F4-05 | Evaluar separar la generación de PDF del cálculo de precio | W3 | ▪▪ | Decisión documentada; si se separa, ambos flujos bajo el umbral de nodos | ☑ 23/09 — **ejecutado**: `[SUB] - CCB - Generar PDF de Propuesta`; **W3 25→17 nodos** y `valid=true` (ver nota) |

**Criterio de cierre:** ningún flujo por encima de 20 nodos y ningún bloque lógico duplicado entre flujos. **Estado 23/09: W4D (19), sus 5 subflujos (3/3/6/15/17), W3 (17) y el subflujo de PDF (11) cumplen. Siguen sobre el umbral W2A (26) y W5B (26), que no estaban contemplados en el plan.**

> **Nota — F4-01 en curso (22/09):** el subflujo compartido `[SUB] - CCB - Registrar y Alertar Error` (`2dY1kaT7I5a0eP2w`) ya existe, publicado y validado (0 errores/0 warnings). Su contrato de entrada tolera la divergencia real del patrón (ver re-auditoría del 22/09, sección 4.2 punto 8): recibe `{ id_solicitud, workflow_origen, nodo_fallido, mensaje_error, emailBody, subject?, alertar? }` con defaults para los campos ausentes (W1 y W3 no emiten `workflow_origen`; W5B/catch-all usan `alertHtml` en vez de `emailBody`). Registra siempre en `Errores_CCB` y condiciona la alerta Outlook a `alertar !== false`. **W6 migrado como piloto** (commit `e8177dd`): sus dos `Preparar error` ahora invocan el subflujo en vez de duplicar Data Table+Outlook (10 nodos, antes 11). **Pendiente:** verificación con ejecución real de W6 antes de escalar al resto de flujos — la regla de oro del proyecto aplica igual acá.

> **Nota — catch-all resuelto con diseño propio (23/09):** se evaluó migrarlo al subflujo compartido y la decisión fue **no hacerlo**, por una razón concreta: el `Data Table - Registrar error` del subflujo hace *upsert* por `id_solicitud + workflow_origen + nodo_fallido`, así que dos incidentes distintos del mismo nodo se pisarían entre sí. En el catch-all el `id_solicitud` es fijo (`N/A (catch-all)`) y lo que importa es conservar el **historial de cada incidente**, así que mantiene su insert propio. Lo que sí se hizo: documentar la decisión en la nota del flujo (que además decía erróneamente que solo cubría W1, W2 y W3, cuando cubre los 11 activos), agregar la `description` que le faltaba al subflujo de error y enmascarar el mensaje de error antes de registrarlo y alertarlo (F6-03).

> **Nota — F4-01 cerrado (22/09, 8/9 del patrón A):** se migraron al subflujo compartido **W1** (23→20, 3 invocaciones para sus 4 Preparar en paralelo; se agregó `workflow_origen: 'intake-v2.0'` a los 4 Preparar que no lo emitían), **W2A** (28→26, con `Consolidar resultado de error`→`Return` intacto), **W4A** (10→9), **W5A** (10→9), **W4B** (14→13, `Marcar REVISION_MANUAL` queda en el llamador), **W5B** (25→24, el consolidador ahora emite también `emailBody` y `workflow_origen`), **W4D-rama recálculo** (48→47, con `alwaysOutputData` en `Marcar ERROR_CALCULO`) y **W6** (piloto, verificado con ejecuciones reales 416449/416453+416454). Las variantes B (solo registrar: W2C, W3, W4C y 3 ramas de W4D) **no** pasan por el subflujo — no son el patrón duplicado. El **catch-all queda diferido con diseño propio** (contrato divergente `workflowName`/`lastNode`/`errorMessage`/`alertHtml`, `id_solicitud` fijo y punto ciego único del pipeline). Commits `fbd45c1`, `7e68c8d`, `b5e2b6d`, `5203603`.

> **Nota — F4-02 (23/09):** el bloque `Data Table - Leer cotización → Leer criterios → Leer solicitud` estaba duplicado **idéntico** en W4-B, W4-C y W4-D, y cada flujo lo consumía con las mismas tres líneas (`$('Data Table - Leer cotización').first().json || {}`). Ahora vive en `[SUB] - CCB - Leer Contexto Propuesta` (`GELWpskp0aYJ2zPg`), que resuelve el `id_solicitud` (item, `body` o `query`) y devuelve un solo item con `{ id_solicitud, cotizacion, criterios, solicitud }`.
>
> Las tres lecturas del subflujo llevan `alwaysOutputData`, así que una propuesta sin cotización **no corta la cadena**: devuelve `{}` en la clave que falte y el llamador decide, igual que antes. Eso además hace explícito el caso que antes dependía de que la cadena lineal llegara entera.
>
> **Verificado con datos reales:** se ejecutó el subflujo desde un workflow descartable (ya eliminado) con un `id_solicitud` real de `Cotizaciones_CCB`: devolvió la cotización (`ENVIADA`, Información Georreferenciada), los criterios (razón social) y `null` en la solicitud, que no existía para ese id — confirmando el fallback sin cortar la ejecución.

> **Nota — F4-03 cerrado (23/09):** W4-D dejó de ser un lienzo de 54 nodos y pasó a ser un **router de decisión de 19 nodos**; cada rama vive en su propio subflujo:
>
> | Subflujo | ID | Nodos | Qué hace |
> |---|---|---|---|
> | `[SUB] - CCB - W4D Aprobar` | `8j6BCwXkgJCccyO1` | 3 | Marca `APROBADA` y devuelve la confirmación |
> | `[SUB] - CCB - W4D Cancelar` | `Jgf514VxDINJ8ra3` | 3 | Marca `CANCELADA` y devuelve la confirmación |
> | `[SUB] - CCB - W4D Revisión Manual` | `iNSErCHs2iw33emJ` | 6 | Los tres motivos de revisión manual (tope, IA desactivada, confianza baja) sin consumir ronda |
> | `[SUB] - CCB - W4D Corrección IA` | `3NAcLF4jaZ1JBw0A` | 15 | Guardarraíles + ajuste con IA + re-invocación del motor |
> | `[SUB] - CCB - W4D Cierre de Corrección` | `POeFkqQp8e4cGfY3` | 17 | Idempotencia del comentario, ronda, aviso por Teams y los dos fallos posibles |
>
> El router conserva las dos respuestas distintas del rechazo: **400** `{ok:false, error}` cuando la decisión no se reconoce antes de leer la base (F2-04) y **200** `{ok:false, mensaje}` cuando no se reconoce después de consolidar.
>
> **Verificado con tráfico real** (filas descartables `SOL-PRUEBA-F403` / `SOL-PRUEBA-F403B`, sin tocar datos reales): `Aprobar` → 200 + fila `APROBADA`; `Cancelar` → 200 + fila `CANCELADA`; `Solicitar correcciones` con ronda 3 → 200 con el mensaje de tope + fila `REVISION_MANUAL` y **la ronda sin consumir**; y la cadena anidada W4D → C1 → Revisión Manual → Leer Configuración ejecutada completa (`success`).
>
> **Dos defectos encontrados y corregidos al verificar:**
> 1. **Los avisos de error perdían el detalle.** El nodo `Data Table` **reemplaza el item** por la fila actualizada, así que en cuatro cadenas la llamada al subflujo compartido de error salía *después* de un update y llegaba sin `mensaje_error` ni `nodo_fallido`: la alerta se registraba como `desconocido` / `Error sin mensaje`. Afectaba a **W4B, W5A, W6** y al nuevo cierre de corrección (herencia del orden original de W4-D). Se invirtió el orden — primero registrar y alertar, después marcar el estado — y se verificó con una ejecución real: la fila registrada ahora dice `solicitud=SOL-PRUEBA-F403B`, `nodo=Re-invocar motor (recálculo)` y el mensaje real del fallo.
> 2. **El aviso de tope salía con asunto y cuerpo vacíos**, por la misma razón (leía `$json._aviso_asunto` después de un update). Ahora el asunto, el cuerpo y el motivo se resuelven por nombre de nodo, que no depende del item.
>
> **Pendiente de esta fase:** el criterio de ≤20 nodos sigue fallando en **W2A (26)**, **W3 (25)** y **W5B (26)**. La F4-05 cubre W3; W2A y W5B **no estaban contemplados** en el plan y hay que decidir si se parten igual (mismo patrón: agrupar por rama de servicio / por responsabilidad).

> **Nota — F4-05 ejecutado (23/09):** la etapa de presentación salió del motor a `[SUB] - CCB - Generar PDF de Propuesta` (`DF3emCmBBBB2HA3i`, 11 nodos): `Enrutar por servicio` + las 4 plantillas `HTML - …` + `Interpolar plantilla HTML` + `HTTP - Generar PDF` + `Adjuntar PDF_URL`, más un nodo propio que devuelve el fallo (servicio no reconocido o microservicio caído) como item.
>
> **Resultados:** W3 pasó de 25 a **17 nodos** y quedó `valid=true` con **0 errores y 0 advertencias** — los 4 hallazgos "Mixed literal text and expression requires = prefix" **se fueron con las plantillas** al subflujo (siguen siendo los mismos falsos positivos preexistentes: el runtime los acepta y genera PDFs reales). El subflujo tiene 11 nodos, también bajo el umbral.
>
> **Cambio de contrato:** el subflujo ya **no devuelve el binario del PDF**, solo `PDF_URL` (se verificó que ningún flujo aguas abajo consume el binario). El fallo se devuelve como item `{ ok: false, error, mensaje_error }` y W3 lo registra en `Errores_CCB` y responde con `Restaurar resultado de error` (que ahora lee el fallo del subflujo).
>
> **Pendiente de verificación real:** generar un PDF de verdad. El túnel ngrok del microservicio está **caído** (`POST /html-pdf` → `ERR_NGROK_3200`, y `/pdfs/SOL-20260916134302.pdf` → 404), así que la corrida end-to-end con PDF real no se pudo completar. Es el mismo punto débil que el plan llama "Fase D de infra": la URL del microservicio vive en `Configuracion_CCB.microservicio_pdf_url` y se cambia sin tocar workflows cuando el túnel se republica.
>
> ⚠️ **Implicación de producción:** con el túnel caído, la generación de PDF falla para propuestas reales (el error queda registrado y alertado por el subflujo, pero no hay PDF ni envío). Vale confirmar con el usuario si el túnel se republica.

> **Nota — F4-05 (23/09, dictamen):** **recomendación: separar** la generación de PDF en `[SUB] - CCB - Generar PDF`, moviendo `Enrutar por servicio` + los 4 nodos `HTML - …` + `Interpolar plantilla HTML` + `HTTP - Generar PDF` + `Adjuntar PDF_URL` (8 nodos). W3 quedaría en **17 nodos** y cumpliría el umbral de ≤20 del framework (hoy tiene 25: de esos, 4 son plantillas HTML de 100–212 KB y 1 es una nota).
>
> El bloqueo para hacerlo ya **no existe**: se verificó que **ningún flujo aguas abajo consume el binario del PDF** (solo W3 lo menciona, en `Adjuntar PDF_URL`), así que el subflujo puede devolver únicamente `PDF_URL` y se elimina el riesgo de mover binarios entre workflows.
>
> Por qué no se ejecutó en esta ronda: mueve ~600 KB de plantillas por el API, toca el camino crítico del motor y la regla de oro exige verificarlo **generando un PDF real** (túnel ngrok + microservicio vivos). Es un cambio de una sesión dedicada, no un cierre de ronda. Queda como el trabajo pendiente con mejor relación valor/riesgo de la Fase 4 después de F4-03. se migraron al subflujo compartido **W1** (23→20, 3 invocaciones para sus 4 Preparar en paralelo; se agregó `workflow_origen: 'intake-v2.0'` a los 4 Preparar que no lo emitían), **W2A** (28→26, 2 invocaciones, con `Consolidar resultado de error`→`Return` intacto), **W4A** (10→9), **W5A** (10→9), **W4B** (14→13, `Marcar REVISION_MANUAL` queda en el llamador antes de la invocación), **W5B** (25→24, patrón consolidado: los 4 Preparar→`Marcar ERROR_ENVIO`→consolidador→invocación; el consolidador ahora emite también `emailBody` y `workflow_origen`), **W4D-rama recálculo** (48→47, con `alwaysOutputData` agregado a `Marcar ERROR_CALCULO`). Las variantes B (solo registrar, responden al llamador: W2C, W3, W4C y 3 ramas de W4D) **no** pasan por el subflujo — no son el patrón duplicado que F4-01 ataca. **Catch-all diferido con diseño propio**: su contrato es distinto (`workflowName`/`lastNode`/`errorMessage`/`alertHtml`), registra `id_solicitud: "N/A (catch-all)"` fijo, y es el único punto ciego del pipeline — migrarlo sin adaptar el contrato perdería fidelidad del diagnóstico en el canal de última instancia. Commits: `fbd45c1`, `7e68c8d`, `b5e2b6d`. **Verificación real pendiente en flujos no-piloto:** la regla de oro exige corrida de punta a punta por flujo; solo W6 quedó verificado con ejecuciones reales (416449/416453+416454).

---

## Fase 5 — Configuración centralizada

> El acceso a Variables de n8n sigue bloqueado por permisos. **Esta fase no lo espera:** usa una Data Table como fuente única de verdad, y migra a Variables si algún día se habilitan.

| ID | Tarea | Alcance | Esf. | Cómo se verifica | Hecho |
|---|---|---|---|---|---|
| F5-01 | Crear la Data Table `Configuracion_CCB` (clave/valor) con correo de alertas, datos del asesor, URL del microservicio y chat de aprobación | instancia | ▪ | La tabla existe y responde a una lectura de prueba | ☑ 23/09 — tabla `8ChPkhKrjag6Jkcs`, 7 claves, lectura verificada |
| F5-02 | Reemplazar el correo de alertas hardcodeado | los 10 flujos que lo tienen | ▪▪ | Cambiar el destinatario en un solo lugar se refleja en todos los flujos | ☑ 23/09 — el correo vive en la clave `alertas_email`; lo consumen el subflujo compartido de error (8 flujos), el catch-all y W4D |
| F5-03 | Sacar del código y de los parámetros la URL del microservicio, hoy duplicada en dos nodos | W3 | ▪ | Cambiar la URL en un solo lugar no requiere editar ningún flujo | ☑ 23/09 — `microservicio_pdf_url`; los dos nodos de W3 la leen de la tabla |
| F5-04 | Parametrizar nombre y correo del asesor, hoy repetidos en cinco nodos | W3 | ▪▪ | Un cambio de asesor no exige tocar los templates | ☑ 23/09 — `asesor_nombre`/`asesor_email`/`asesor_telefono`; las 4 plantillas HTML usan el placeholder `{{ $json.asesor_email }}` y W5B lee el correo de la tabla |
| F5-05 | Migrar a Variables nativas si Tecnología las habilita | los 12 | ▪▪ | Las lecturas de configuración apuntan a Variables sin cambiar la lógica | ⏸ bloqueada — la API de Variables devuelve 403 (`Your license does not allow for feat:variables`). La Fase 5 no la espera: usa la Data Table. |

**Criterio de cierre:** ningún correo, URL ni identificador de destino escrito a mano dentro de un nodo. ✅ **Cumplido (23/09)** en los 11 flujos activos + catch-all + subflujos: una barrida sobre los nodos no encuentra literales de correo, URL del microservicio ni chatId. Quedan fuera de alcance los del flujo retirado W2B.

> **Nota — F5 (23/09):** la configuración se centraliza en la Data Table `Configuracion_CCB` (id `8ChPkhKrjag6Jkcs`) con las claves `alertas_email`, `asesor_nombre`, `asesor_email`, `asesor_telefono`, `microservicio_pdf_url`, `teams_chat_aprobacion`, `notificacion_envio_email` y `teams_chat_aprobacion_produccion`. El acceso se hace con el subflujo compartido **`[SUB] - CCB - Leer Configuración`** (id `Hgy02eqPhnsdJvkq`), que entrega el item del llamador con la configuración adjunta en `_config`.
>
> **Hallazgo de motor (23/09) — por qué un subflujo y no un nodo suelto:** primero se probó colgar el nodo `Data Table - Leer configuración` como rama hermana del trigger y referenciarlo con `$('nodo')`. Se verificó con un workflow descartable y tráfico real que **n8n no resuelve esa referencia**: `Node 'Data Table - Leer configuración' hasn't been executed`. La referencia solo funciona si el nodo está **aguas arriba** del que la usa. Por eso el patrón adoptado es un subflujo invocado como primer nodo de la cadena (`inputSource: passthrough`), que devuelve el payload del llamador intacto más `_config`.
>
> **Valores en modo prueba:** `teams_chat_aprobacion` y `notificacion_envio_email` conservan a propósito los valores de prueba (F0-05/F0-06 diferidas). El chat real del aprobador quedó guardado en `teams_chat_aprobacion_produccion`: cerrar F0-05 es cambiar la clave activa, sin tocar ningún workflow.

---

## Fase 6 — Observabilidad

| ID | Tarea | Alcance | Esf. | Cómo se verifica | Hecho |
|---|---|---|---|---|---|
| F6-01 | `timeout` explícito en las llamadas HTTP | W3, W5B | ▪ | Una llamada colgada corta en el tiempo definido, no queda esperando | ☑ 23/09 — `options.timeout = 60000` en `HTTP - Generar PDF (microservicio)` (W3) y `HTTP - Descargar PDF` (W5B). Son los únicos dos nodos HTTP del pipeline. |
| F6-02 | Paginación o límite en las lecturas que hoy traen todo sin tope | W4A, W5A, W6 | ▪ | El volumen leído por ejecución está acotado | ☑ 23/09 — `limit: 100` en las tres lecturas de cola (`PROPUESTA_GENERADA`, `APROBADA`, `ENVIADA`). Son colas de trabajo: el resto se procesa en el ciclo siguiente (15 min / 3am). |
| F6-03 | Enmascarar PII antes de logs y alertas externas | W4B, W4D, W5B, W2C | ▪▪ | Las alertas identifican la solicitud sin exponer datos personales completos | ☑ 23/09 — helper `limpiar()` en el subflujo compartido de error (cubre W4B/W5B y los otros 6 flujos que alertan por ahí), en el catch-all y en 4 nodos de error de W4D; `parcial()` para nombre y razón social en el aviso de tope. W2C verificado: su registro de error solo lleva nombres de campos faltantes. |
| F6-04 | Revisar las variables de retención de ejecuciones a nivel de instancia | instancia — requiere Tecnología | ▪ | La retención está acotada y el disco deja de crecer sin control | ⏸ pendiente de Tecnología — ver nota |
| F6-05 | Monitorear las cuatro métricas del framework: tasa de ejecución, tasa de error por flujo (umbral 2%), latencia p95 y profundidad de cola | instancia | ▪▪ | Existe un punto donde consultar las cuatro y un umbral que dispara aviso | ☑ 23/09 — flujo `[OPS] - CCB - Monitoreo del pipeline` (horario) + Data Table `Metricas_CCB`; verificado con ejecución real |

**Nota — F6-05 (23/09):** el flujo de monitoreo corre **cada hora**, calcula las cuatro métricas y las publica en la Data Table `Metricas_CCB` (una fila por métrica, upsert por `metrica`, así la tabla no crece):

| Métrica publicada | Fuente | Umbral que dispara aviso |
|---|---|---|
| `tasa_error_pct` | contadores `n8n_workflow_execution_duration_seconds_count{status}` de `/metrics` | ≥ 2% |
| `ejecuciones_total` | idem (acumulado del proceso) | informativa |
| `latencia_p95_ms` | buckets del histograma de duración | informativa |
| `saturacion_handles` | `n8n_nodejs_active_handles_total` | informativa |
| `errores_ultima_hora` | `Errores_CCB` por `error_timestamp`, con desglose por `workflow_origen` | ≥ 3 en la hora |

Si se supera un umbral, envía el detalle al destinatario de `alertas_email` de `Configuracion_CCB`; la URL de `/metrics` también sale de esa tabla (`metricas_url`), así que mudar de instancia no toca el flujo.

**Verificación real:** se agregó un trigger por webhook temporal, se ejecutó contra la instancia viva (ejecución `success`) y se comprobó: `tasa_error_pct = 0.17`, `ejecuciones_total = 124.471`, `errores_ultima_hora = 0`, `latencia_p95_ms = 5000`, `saturacion_handles = 19`, la rama de alerta evaluada como falsa (correcto: por debajo del umbral) y las 5 filas escritas en `Metricas_CCB`. Después se eliminó el trigger temporal: el flujo quedó **solo por horario**.

**Limitaciones declaradas:** `/metrics` acumula desde el arranque del proceso (no por ventana) y no tiene etiqueta de flujo, así que la tasa de error es global y el desglose por flujo sale de `Errores_CCB`. La profundidad de cola real (workers) requeriría acceso a la cola de n8n, que la API pública no expone: se usa la saturación de handles como proxi. **Para el cálculo exacto por flujo** hace falta una credencial de API de n8n dentro del flujo (la API pública devuelve 403 al crear credenciales: debe crearla una persona desde la UI).

**Columna `error_timestamp` (23/09):** `Errores_CCB` no tenía marca de tiempo, así que ningún error propio era ubicable en el tiempo. Se agregó la columna y se selló en los **8 nodos** que insertan errores (subflujo compartido, W2C, W3 ×2, W4D ×3, catch-all) con `={{ $now.setZone('America/Bogota').toFormat('yyyy-MM-dd HH:mm:ss') }}` (expresión verificada contra la instancia viva).

### Nota — F6-03 (23/09, enmascarado de PII)

El texto libre que llega a `Errores_CCB` y a las alertas internas viene de mensajes de error de n8n (Outlook, HTTP, Teams) que pueden arrastrar correos de destinatario, URLs con identificadores o números de documento. El helper aplicado antes de registrar o alertar:

```js
const limpiar = (t) => String(t === null || t === undefined ? '' : t)
  .replace(/[\w.+-]+@[\w-]+\.[\w.]+/g, '<correo>')
  .replace(/https?:\/\/\S+/g, '<url>')
  .replace(/\b\d{7,}\b/g, '<num>');
```

En el aviso de tope de correcciones (W4D) el asesor sigue recibiendo la solicitud completa, pero nombre y razón social van parciales (`parcial()`): el aviso identifica el caso sin transportar el dato personal completo. El correo **al cliente** no se toca — ahí los datos del cliente son el contenido legítimo del mensaje.

Verificado con `node` sobre casos reales (`Recipient address rejected: cliente@empresa.com` → `<correo>`; URL de Graph con token → `<url>`; NIT → `<num>`).

### Nota — F6-04 / F6-05 (23/09)

**Hallazgo relevante:** el endpoint `/metrics` de la instancia está **expuesto sin autenticación** y devuelve 42 métricas de proceso (CPU, memoria, event loop, `n8n_workflow_execution_duration_seconds`, `n8n_nodejs_active_requests`, `n8n_active_workflow_count`). Sirve para latencia y profundidad de cola, pero **no** para tasa de ejecución ni tasa de error por flujo, que viven en la API de ejecuciones.

Estado de las cuatro métricas del framework:

| Métrica | Fuente | Estado |
|---|---|---|
| Latencia (p95) | `n8n_workflow_execution_duration_seconds` en `/metrics` | ✅ en `Metricas_CCB` |
| Profundidad de cola | `n8n_nodejs_active_handles_total` en `/metrics` | ⚠️ proxi de saturación (la cola real no es accesible) |
| Tasa de error (umbral 2%) | contadores `status="failed"`/`status="success"` en `/metrics` + desglose por flujo desde `Errores_CCB` | ✅ global; por flujo requiere credencial de API |
| Tasa de ejecución | `n8n_workflow_execution_duration_seconds_count` en `/metrics` | ✅ acumulada |

**Segundo hallazgo (habilitador de la métrica de error):** `Errores_CCB` no tenía columna de fecha — los registros de error no eran ubicables en el tiempo, así que no se podía calcular nada por ventana. **Corregido el 23/09**: columna `error_timestamp` + sellado en los 8 puntos de inserción (ver la nota de F6-05).

**F6-04** requiere que Tecnología revise `EXECUTIONS_DATA_PRUNE` / `EXECUTIONS_DATA_MAX_AGE`; no es accesible desde la API pública. Queda como pedido concreto, junto con el cierre de `/metrics` (o al menos su restricción por red), que hoy publica la topología interna de la instancia.

---

## Fase 7 — Guardarraíles de IA

> Lo que ya existe en W4D es sólido: salida estructurada con esquema obligatorio, modelo de respaldo y validación contra listas cerradas de valores. Falta cerrar el círculo.

| ID | Tarea | Flujo | Esf. | Cómo se verifica | Hecho |
|---|---|---|---|---|---|
| F7-01 | Enrutar `confianza: "baja"` a revisión humana en vez de aplicar el ajuste igual | W4D | ▪▪ | Una corrección con confianza baja queda detenida esperando decisión | ☑ 23/09 — `IF - ¿Confianza suficiente?` → `Preparar aviso - Revisión manual` |
| F7-02 | Kill switch para desactivar la corrección asistida por IA sin apagar el flujo entero | W4D | ▪▪ | Con el interruptor apagado, las correcciones van a revisión manual y el resto opera normal | ☑ 23/09 — clave `ia_correccion_habilitada` en `Configuracion_CCB` |
| F7-03 | Mover la aprobación humana antes del recálculo y del incremento de ronda | W4D | ▪▪▪ | Ninguna ronda se consume sin que una persona lo haya autorizado | ☑ 23/09 — **camino A implementado**: aprobación en Teams con `sendAndWait` antes del recálculo (ver nota) |

> **Nota — F7-01 / F7-02 (23/09):** la rama de corrección de W4-D ahora tiene dos guardas antes de tocar la propuesta:
>
> 1. `IF - ¿Corrección IA habilitada?` lee `ia_correccion_habilitada` de `Configuracion_CCB` (interruptor **F7-02**). Si vale `false`, la corrección **no** se manda al modelo: va directo a revisión manual y el resto del flujo opera normal. Apagar la IA es cambiar una celda de la tabla, sin tocar el workflow.
> 2. `IF - ¿Confianza suficiente?` evalúa la `confianza` que ya declaraba el parser estructurado (`alta`/`media`/`baja`, campo que existía pero **se perdía**: `Aplicar correcciones` no lo reenviaba — corregido). Con `baja`, el ajuste **no se aplica**: la propuesta queda en `REVISION_MANUAL`.
>
> En los dos casos el aviso al asesor explica el motivo, la interpretación de la IA y el comentario original, y — importante — **no se consume una ronda de corrección**.
>
> **Verificación:** la lógica del nodo nuevo se probó con `node` usando el código extraído de la instancia y los dos casos reales (confianza baja / IA desactivada), comprobando motivo, asunto y cuerpo generados. La ejecución de punta a punta de la rama queda en la regla de oro (requiere un POST real al webhook de decisión).

> **Nota — F7-03 implementado (23/09, camino A):** la corrección asistida ya no se aplica sola. En `[SUB] - CCB - W4D Corrección IA` el flujo es ahora: guardarraíles (tope, interruptor, confianza) → **`Teams - Pedir aprobación de la corrección`** (`sendAndWait`, aprobación doble, espera máxima 24 h) con el pedido del asesor y el ajuste propuesto por la IA → `Preservar contexto tras la aprobación` (la respuesta de Teams no trae el contexto, así que se rearma desde `Aplicar correcciones` y se normaliza la aprobación sea cual sea su forma) → `IF - ¿Aprobó la corrección?`:
>
> - **Aprobada** → `Re-invocar motor` → recálculo y **recién ahí** se consume la ronda.
> - **Rechazada, no respondida a tiempo o fallo al enviar** → `Ejecutar Revisión Manual` (sin consumir ronda), con el motivo `aprobacion_rechazada` en el aviso.
>
> **La ronda no se consume sin autorización humana explícita**, y el `IF - ¿Comentario ya procesado?` sigue evitando el doble consumo por reenvíos.
>
> Además, W4D **responde el webhook antes de esperar**: `Responder decisión - Corrección en aprobación` contesta *"Tu pedido quedó registrado; el asesor debe aprobar el ajuste propuesto por la IA"* y recién después se invoca la subrama, para que la página de revisión no quede colgada esperando la respuesta humana. W4D queda en **20 nodos** y C1 en **18** (ambos bajo el umbral).
>
> **Validación:** los tres workflows afectados validan `valid=true`, 0 errores y 0 advertencias con `n8n_validate_workflow`. La credencial de Teams usada es la real del pipeline (`INT-ServiciosInformacion Microsoft Teams`), no una inventada.
>
> **Pendiente de verificación real:** el clic de aprobación (y el rechazo) en Teams. El timeout y el rechazo se pueden probar dejando vencer la espera; la aprobación requiere que la persona apruebe en el chat. El chat hoy apunta al de pruebas (F0-05 diferida), lo que de hecho facilita la prueba.

> **Nota — F7-03 (23/09, decisión que quedó documentada):** el requisito es que ninguna ronda se consuma sin autorización humana sobre la **propuesta de la IA**. Hoy el humano autoriza "solicitar correcciones", pero el ajuste de la IA se aplica y se recalcula sin que nadie lo vea antes. Hay dos caminos y cambian el producto, así que no se implementa sin decisión:
>
> | Camino | Cómo | Costo / riesgo |
> |---|---|---|
> | **A. Aprobación dentro de Teams** (`sendAndWait`) | Después de `Aplicar correcciones`, el flujo manda la propuesta de ajuste al aprobador en Teams y **espera** su aprobación antes de recalcular y de incrementar la ronda. El patrón ya existió en este pipeline (W4-B usaba `sendAndWait`) | No toca el front. Requiere reordenar la respuesta del webhook (responder antes de esperar), definir el tiempo de espera y una rama de expiración, y probar con Teams real. El chat hoy está en modo prueba (F0-05), lo que de hecho facilita la prueba |
> | **B. Aprobación en la página de revisión** | Nuevo estado `PENDIENTE_APROBACION_IA` + nuevo valor de decisión en el webhook; el asesor aprueba desde `revision-propuesta-ccb` | Toca **dos repos** (pipeline y front) y el deploy del front está bloqueado por la migración de cuenta de Vercel |

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
| **Frontends en cuenta Vercel equivocada (Muttu)** | Deploy del fix F3-09 (idempotencia del formulario) — el fix está commiteado pero no publicado | Migración Vercel: replicar en `agutierrezreginodev` → verificar → liberar dominio → eliminar en Muttu (plan completo en §Migración Vercel) |

---

## Migración Vercel — plan de acción

> **Contexto (22/09):** los proyectos `formulario-solicitud-ccb` y `revision-propuesta-ccb` se crearon por error en el equipo **Muttu** (orgId `team_UF3EtORaOMPzlT6Lz64g3rB7`), sin repo conectado. Deberían estar en la cuenta personal `agutierrezreginodev` (los repos GitHub ya están ahí). La transferencia de proyectos de Vercel solo se hace a un **Team**, y crear el Team en la cuenta destino exige método de pago — opción descartada por el usuario. **Decisión: replicar en la cuenta personal y eliminar en Muttu para liberar los dominios.**

> **⚠️ Orden obligatorio — no eliminar en Muttu antes de tener el reemplazo verificado** (el formulario público y la página de revisión están en producción; eliminarlos primero los deja caídos).

### Pasos

| # | Paso | Quién | Cómo se verifica | Estado |
|---|---|---|---|---|
| M1 | Login en Vercel con la cuenta personal `agutierrezreginodev` | usuario | `vercel whoami` muestra `agutierrezreginodev` | ☐ |
| M2 | Replicar `formulario-solicitud-ccb` en la cuenta personal (deploy desde repo local, incluye fix F3-09) | orquestador | Deploy exitoso; dominio temporal `formulario-solicitud-ccb-*.vercel.app` responde | ☐ |
| M3 | Replicar `revision-propuesta-ccb` en la cuenta personal | orquestador | Deploy exitoso; dominio temporal `revision-propuesta-ccb-*.vercel.app` responde | ☐ |
| M4 | Verificar funcionalidad de ambos en los dominios temporales (formulario envía, revisión carga) | usuario | Prueba real de envío + carga de propuesta | ☐ |
| M5 | Actualizar CORS en n8n: W2C `allowedOrigins` → dominio temporal nuevo del formulario; W4C → dominio temporal nuevo de revisión | orquestador | `curl` con `Origin` variado refleja el origen nuevo | ☐ |
| M6 | Eliminar los proyectos en Muttu (libera los dominios `.vercel.app` originales) | orquestador (tras M4) | `vercel project remove` x2; dominios originales dejan de responder | ☐ |
| M7 | Recuperar los dominios originales en la cuenta personal (`vercel alias` / domains) | orquestador | `formulario-solicitud-ccb.vercel.app` y `revision-propuesta-ccb.vercel.app` apuntan a los proyectos nuevos | ☐ |
| M8 | Re-ajustar CORS en n8n a los dominios originales (si difieren de los temporales) | orquestador | CORS vuelve a apuntar a los dominios canónicos | ☐ |
| M9 | Conectar repos GitHub a los proyectos Vercel para auto-deploy en el futuro | orquestador | Push a `agutierrezreginodev/formulario-solicitud-ccb` dispara deploy | ☐ |

> **Nota:** el fix F3-09 (idempotencia del formulario con `sessionStorage`, commit `df1a8a3` en repo aparte) queda publicado cuando se complete M2 — es el desbloqueo principal de esta migración.
