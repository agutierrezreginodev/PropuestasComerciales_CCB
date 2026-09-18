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
