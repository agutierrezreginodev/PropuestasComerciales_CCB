# Flujos del pipeline CCB — subflujos y flujos operativos

Este documento explica **cada flujo que se agregó** al pipeline de Cotizaciones CCB después de los 12 originales:
por qué se creó, cómo funciona y con qué otros flujos se relaciona.

> **Regla de mantenimiento:** todo flujo nuevo se documenta acá **en el mismo cambio** que lo crea, con las tres
> secciones (por qué / cómo funciona / relaciones). Si un flujo cambia de contrato, se actualiza su ficha.
> El catálogo técnico (id, nombre, archivo) está en el [README](../README.md); este documento es el *por qué* y el *cómo*.

---

## 1. Convenciones

**Carpeta en n8n.** Los 12 flujos originales viven en la carpeta **`Servicios_Información_Cotizaciones_v2.0`**.
Todos los flujos nuevos deben quedar en esa misma carpeta.

> ⚠️ **Pendiente operativo (23/09):** el API de n8n no permite mover workflows a una carpeta con la API key actual
> (`/api/v1/projects/{id}/folders` → `403 Forbidden`: *"Folders need an API key with folder:\* scopes AND a licensed
> instance… unlock on the registered free Community tier"*). Para moverlos por script hace falta **una API key con los
> scopes de carpeta** y/o **registrar la instancia** (Settings → Usage and plan → register). Mientras tanto los flujos
> nuevos están en el proyecto personal y se mueven a mano desde la UI (arrastrar a la carpeta): son **10 flujos**.

**Nombres.** El framework exige que un subflujo se distinga a simple vista del flujo principal (tarea F1-06 del plan):

| Prefijo | Se usa para | Ejemplos |
|---|---|---|
| `[SUB]` | Subflujo: se invoca desde otro flujo (`Execute Workflow`) | `[SUB] CCB - Registrar y Alertar Error` |
| `[OPS]` | Flujo operativo/de plataforma: no procesa propuestas, opera el pipeline | `[OPS] CCB - Monitoreo del pipeline` |
| (sin prefijo) | Flujo principal del pipeline | `CCB - Workflow 1 - Extracción información del cliente` |

Los nodos dentro de los flujos siguen la convención `[Servicio] - [Acción/Recurso]` (p. ej. `Data Table - Leer cotización`,
`Outlook - Enviar alerta`) y los de decisión `[Lógica] - [Condición]` (p. ej. `IF - ¿Rondas de corrección >= 3?`).

**Contrato de subflujo.** Todos los subflujos comparten la misma forma: el trigger es
`When Executed by Another Workflow` con `inputSource: passthrough` (recibe el item del llamador tal cual) y devuelven
un item con la misma forma o una ampliada, para que el llamador pueda seguir su cadena.

---

## 2. `[SUB] CCB - Registrar y Alertar Error`
**ID:** `2dY1kaT7I5a0eP2w` · **Nodos:** 6 · **Plan:** F4-01

**Por qué se creó.** El patrón `Preparar error → registrar en Errores_CCB → alertar por Outlook` estaba **replicado en
los 11 flujos activos** (triplicado en W1, cuatro veces en W5B). Además, el registro y la alerta no siempre ocurrían en
el mismo orden, así que un fallo del correo podía hacer perder el registro técnico del error.

**Cómo funciona.** `Normalizar entrada de error` acepta un contrato tolerante —`{ id_solicitud, workflow_origen,
nodo_fallido, mensaje_error, emailBody, subject?, alertar? }`, todo con defaults— y **enmascara PII** del texto libre
(correos, URLs y números de más de 7 dígitos) antes de usarlo. Después encadena en forma lineal:
`Data Table - Registrar error` (**upsert** por `id_solicitud + workflow_origen + nodo_fallido`, con marca de tiempo) →
`Outlook - Enviar alerta` (destinatario desde `Configuracion_CCB`) → `Devolver item al llamador` (siempre devuelve el
item, aunque el correo falle). El registro ocurre **antes** de la alerta: un fallo del correo no pierde el registro.

**Relaciones.** Lo llaman **8 flujos** en sus ramas de error: W1, W2A, W4A, W4B, W4D (rama de recálculo), W5A, W5B y W6
(nodo `Ejecutar Registrar-y-Alertar`). No lo usa el **catch-all** (mantiene su propio registro, ver más abajo) ni las
variantes B (W2C, W3, W4C y tres ramas de W4D): esas responden al llamador y no envían correo.

---

## 3. `[SUB] CCB - Leer Configuración`
**ID:** `Hgy02eqPhnsdJvkq` · **Nodos:** 4 · **Plan:** F5 (F5-01, F5-03)

**Por qué se creó.** El correo de alertas, el correo y nombre del asesor, la URL del microservicio de PDF y el chat de
aprobación estaban **escritos a mano dentro de los nodos**, en 10 flujos distintos. Cambiar un destinatario exigía editar
workflows, y las notas internas de los nodos llegaban a contener valores reales que se exportan al repositorio público.

**Cómo funciona.** Entrega el item del llamador **con la configuración adjunta** en `_config` (un objeto
`clave → valor` leído de la Data Table `Configuracion_CCB`). La lectura va en línea con el trigger, así que el resto del
flujo puede usar `{{ $json._config.<clave> }}` (o `$('Ejecutar Leer Configuración').first().json._config.<clave>` cuando
un nodo intermedio reemplaza el item por la fila de una tabla).

> **Nota de diseño:** se implementó como subflujo y no como un nodo suelto colgado del trigger porque n8n **no resuelve
> referencias `$('nodo')` hacia ramas hermanas** (`Node 'X' hasn't been executed`, verificado con tráfico real). Un nodo
> de configuración solo es utilizable si es **ancestro** de quien lo lee.

**Relaciones.** Lo llaman los flujos que necesitan configuración: el subflujo de error, el catch-all, W3, W4B, W4D, W5B,
el subflujo de PDF, el subflujo de Revisión Manual y el flujo de monitoreo. Las claves actuales: `alertas_email`,
`asesor_nombre`, `asesor_email`, `asesor_telefono`, `microservicio_pdf_url`, `teams_chat_aprobacion`,
`notificacion_envio_email`, `teams_chat_aprobacion_produccion`, `metricas_url`, `ia_correccion_habilitada`, `revision_url`,
`n8n_api_url`.

---

## 4. `[SUB] CCB - Leer Contexto Propuesta`
**ID:** `GELWpskp0aYJ2zPg` · **Nodos:** 7 · **Plan:** F4-02

**Por qué se creó.** El bloque de **tres lecturas idénticas** (`Cotizaciones_CCB` + `Criterios_Cotizacion` +
`Solicitudes_CCB` por `id_solicitud`) estaba duplicado en W4B, W4C y W4D, junto con las mismas tres líneas de
consolidación en cada flujo.

**Cómo funciona.** `Resolver id_solicitud` busca el id en el item, en `body` o en `query` y falla ruidosamente si no
viene. Después encadena las tres lecturas (todas con `alwaysOutputData`, así que **un dato faltante no corta la cadena**)
y `Devolver contexto de la propuesta` entrega un único item
`{ id_solicitud, cotizacion, criterios, solicitud }` donde cada clave es la fila de su tabla o `{}`.

**Relaciones.** Lo llaman **W4B, W4C y W4D** (nodo `Ejecutar Leer Contexto Propuesta`), que reemplazaron sus tres nodos
de lectura por una sola invocación: W4B 14→12, W4C 12→10, W4D 50→48 nodos. Al devolver `{}` en lugar de cortar la
cadena, cada llamador decide qué hacer con los datos faltantes (igual que antes, cuando usaba `get()` con fallback).

---

## 5. `[SUB] CCB - Generar PDF de Propuesta`
**ID:** `DF3emCmBBBB2HA3i` · **Nodos:** 12 · **Plan:** F4-05

**Por qué se creó.** W3 (motor de cálculo) mezclaba dos responsabilidades: **calcular el precio** y **armar la
presentación** (elegir plantilla, interpolar el HTML y llamar al microservicio de PDF). Eso lo dejaba con 25 nodos —por
encima del umbral de 20 del framework— y con cuatro hallazgos de validador en los nodos de plantilla.

**Cómo funciona.** Recibe el item **ya calculado** por W3, elige la plantilla con `Enrutar por servicio` (4 servicios +
rama por defecto), `Interpolar plantilla HTML` reemplaza los `{{ $json.campo }}` de la plantilla por los datos del
cálculo, `HTTP - Generar PDF` llama al microservicio y `Adjuntar PDF_URL` arma el enlace público
(`<url del microservicio>/pdfs/<id>.pdf`). Los dos fallos posibles los resuelve `Devolver fallo de PDF`: **servicio no
reconocido** (rama por defecto del Switch) o **microservicio caído** (salida de error del HTTP). La URL del microservicio
sale de `Configuracion_CCB` (ya no está en el código de los nodos).

**Relaciones.** Lo llama **W3** (nodo `Ejecutar Generar PDF de Propuesta`), que bajó a **17 nodos** y quedó sin errores
de validador. **No devuelve el binario del PDF**: se verificó que ningún flujo aguas abajo lo consume; el PDF se entrega
por `PDF_URL` (W5B lo descarga desde ahí para adjuntarlo o mandar el enlace).

> **Dependencia externa:** el microservicio de PDF se publica por un túnel ngrok. Si el túnel está caído
> (`ERR_NGROK_3200`), la generación falla y no hay envío al cliente; el error queda registrado y alertado.

---

## 6. Los tres subflujos del envío (W5B)
**Plan:** F4-03 (W5B pasó de 25 a **19 nodos** en el conteo del framework; reutiliza además `[SUB] CCB - Leer Contexto Propuesta`)

W5B hacía cuatro cosas en un solo lienzo: leer la propuesta, descargar el PDF, enviarlo y cerrar el estado. Se extrajeron
las dos últimas para dejarlo bajo el umbral, **sin tocar la descarga del PDF ni la composición del correo** (los pasos con
más riesgo de verificación real).

### 6.1 `[SUB] CCB - Enviar propuesta al cliente` — `AnPJGVWylmKEYWmJ` · 9 nodos
**Por qué:** el envío al cliente y el cierre del envío son una sola responsabilidad ("enviar la propuesta"), y mezclados
en W5B lo dejaban sobre el umbral de nodos. **Cómo funciona:** recibe el item preparado por W5B
(`email_destinatario`, `emailBodyConAdjunto`, `emailBodySoloLink`, `adjuntar`, el binario del PDF e `id_solicitud`), decide
con `IF - ¿Adjuntar PDF? (<4MB)` entre `Outlook - Enviar con adjunto` y `Outlook - Enviar solo link`, **reinyecta el
contexto** (`Reinyectar contexto del envío`: los nodos de Outlook devuelven `{success:true}` y pierden los datos), delega
el cierre en `[SUB] CCB - Cerrar envío` y devuelve `{ ok:true, id_solicitud, mensaje }`. Si el correo falla,
`Devolver fallo de envío` devuelve el item con `{ ok:false, error, mensaje_error }` para que W5B use su rama de error de
siempre. **Relaciones:** lo llama W5B (`Ejecutar Enviar al Cliente`); llama a `[SUB] CCB - Cerrar envío`.

### 6.2 `[SUB] CCB - Cerrar envío` — `1Zzkrg3dTkTrddgp` · 6 nodos
**Por qué:** marcar `ENVIADA` en dos tablas y avisar al asesor es el cierre de un envío exitoso, y es reutilizable por
cualquier flujo que envíe una propuesta. **Cómo funciona:** lee la configuración (destinatario del aviso) y el contexto
con `[SUB] CCB - Leer Contexto Propuesta` (razón social para el cuerpo del aviso), marca `ENVIADA` en `Cotizaciones_CCB`
(con `enviado_a` tomado del item del llamador y la fecha) y en `Solicitudes_CCB`, y notifica al asesor por correo.
**Relaciones:** lo llama `[SUB] CCB - Enviar propuesta al cliente`.

### 6.3 `[SUB] CCB - Cerrar error de envío` — `D2d9Og6UUvq13TJA` · 3 nodos
**Por qué:** el cierre de un envío fallido (marcar `ERROR_ENVIO` + registrar + alertar) estaba dentro de W5B y es el mismo
patrón que ya usa el subflujo de error compartido. **Cómo funciona:** recibe el item ya preparado por la rama de error de
W5B (`id_solicitud`, `workflow_origen`, `nodo_fallido`, `mensaje_error`, `emailBody`), marca `ERROR_ENVIO` y llama a
`[SUB] CCB - Registrar y Alertar Error`. **Relaciones:** lo llama W5B (`Ejecutar Cerrar Error de Envío`, alimentado por
`Preparar alerta de fallo - Envío`); llama al subflujo compartido de error.

---

## 7. `[SUB] CCB - Invocar Motor y Guardar Cotización`
**ID:** `MHWlUApSFT6gpBHs` · **Nodos:** 10 · **Plan:** F4-03 (W2A pasó de 25 a **19 nodos**)

**Por qué se creó.** W2-A (guardar criterios y cotizar) tenía 25 nodos: además de leer y validar el formulario, guardaba
los criterios por servicio, invocaba el motor de cálculo y guardaba la cotización. El tramo "motor + guardado" se extrajo
para dejarlo bajo el umbral del framework.

**Cómo funciona.** Recibe el item con los criterios ya preparados por W2-A (`Preparar criterios para motor - …`),
invoca el motor (`Ejecutar motor` → W3), **restaura `id_solicitud`** (W3 no lo reenvía en su salida, así que se recupera
del item del llamador) y evalúa `IF - Motor Retornó OK`:

- **El motor calculó** → `Data Table - Guardar Cotización` (upsert por `id_solicitud`) → `Return - Cotización generada`
  devuelve la respuesta lista para el formulario.
- **El motor rechazó el cálculo o lanzó una excepción** → `Preparar error - Motor rechazó la propuesta` (distingue
  excepción de rechazo) → `[SUB] CCB - Registrar y Alertar Error` → `Return - Error (motor)`.
- **Falló el guardado** → `Preparar error - Guardado de cotización` → `[SUB] CCB - Registrar y Alertar Error` →
  `Return - Error (motor)`.

Devuelve el item de respuesta en los tres casos, así que el flujo llamador no necesita enrutar el resultado.

**Relaciones.** Lo llama **W2-A** (`Ejecutar Invocar Motor y Guardar Cotización`, alimentado por los cuatro
`Preparar criterios para motor - …`); llama a **W3** (motor de cálculo) y a `[SUB] CCB - Registrar y Alertar Error`.
Las ramas de error de validación de entrada y de guardado de criterios siguen viviendo en W2-A.

---

## 8. Los cinco subflujos de rama de W4D
**Plan:** F4-03 (partir un lienzo de 54 nodos en un router + una rama por decisión)

W4D recibía la decisión del asesor (aprobar / cancelar / solicitar correcciones) en un solo lienzo de 54 nodos.
Ahora W4D es un **router de 20 nodos** y cada rama vive en su propio subflujo. Las dos respuestas del rechazo se
preservan: **400** `{ok:false, error}` cuando la decisión no se reconoce antes de leer la base, **200**
`{ok:false, mensaje}` cuando no se reconoce después.

### 8.1 `[SUB] CCB - W4D Aprobar` — `8j6BCwXkgJCccyO1` · 3 nodos
**Por qué:** la rama "aprobar" eran dos nodos dentro del lienzo gigante. **Cómo funciona:** recibe el item consolidado,
`Data Table - Marcar APROBADA` (estado + comentario del asesor) y `Confirmar aprobación` devuelve el mensaje de
confirmación que el router responde al asesor. **Relaciones:** lo llama W4D (`Ejecutar Aprobar`); el resultado vuelve por
`Responder decisión`.

### 8.2 `[SUB] CCB - W4D Cancelar` — `Jgf514VxDINJ8ra3` · 3 nodos
**Por qué / cómo / relaciones:** idéntico al anterior pero marca `CANCELADA` (`Ejecutar Cancelar`).

### 8.3 `[SUB] CCB - W4D Revisión Manual` — `iNSErCHs2iw33emJ` · 6 nodos
**Por qué:** había **dos** cadenas casi iguales de "marcar `REVISION_MANUAL` + avisar" (tope de rondas y corrección no
aplicada por confianza baja o IA desactivada). Se unificaron en un subflujo que calcula el **motivo** y arma el aviso:
`Preparar aviso - Revisión manual` → `Data Table - Marcar REVISION_MANUAL` (`alwaysOutputData`: el aviso sale aunque la
fila no exista) → `Outlook - Enviar alerta` (asunto y cuerpo por nombre de nodo, porque el update de la tabla reemplaza
el item) → `Confirmar aviso - Revisión manual`. **Motivos soportados:** `tope` (3 rondas), `ia_desactivada`,
`confianza_baja` y `aprobacion_rechazada`. **Ninguno consume una ronda de corrección.** El nombre y la razón social del
cliente salen **parciales** (F6-03) y el comentario del asesor se enmascara. **Relaciones:** lo llama C1 (tres caminos).

### 8.4 `[SUB] CCB - W4D Corrección IA` — `3NAcLF4jaZ1JBw0A` · 18 nodos
**Por qué:** concentra todo el camino "solicitar correcciones": los guardarraíles de IA, el ajuste con el modelo, la
re-invocación del motor y el traspaso al cierre. **Cómo funciona, en orden:**
1. `Ejecutar Leer Configuración` (interruptor `ia_correccion_habilitada`, chat de aprobación, URL de revisión).
2. `IF - ¿Rondas de corrección >= 3?` → si ya hay 3 rondas, va a Revisión Manual (motivo `tope`).
3. `IF - ¿Corrección IA habilitada?` → **kill switch** (F7-02): si está en `false`, va a Revisión Manual
   (motivo `ia_desactivada`) sin llamar al modelo.
4. `Preparar corrección IA` arma el prompt con las claves existentes de los criterios y las convenciones de valores;
   `IA - Ajustar criterios` (modelo OpenRouter + parser estructurado + modelo de respaldo) devuelve
   `{criterios_ajustados, resumen_cambios, confianza}`; `Aplicar correcciones` **valida cada valor contra listas
   cerradas** y descarta los inválidos en lugar de corromper el criterio.
5. `IF - ¿Confianza suficiente?` (F7-01): si la IA declaró `confianza: baja`, va a Revisión Manual
   (motivo `confianza_baja`) y **no se aplica nada**.
6. `Teams - Pedir aprobación de la corrección` (**F7-03**, operación `sendAndWait`, aprobación doble, espera máxima
   24 h): manda al aprobador el pedido del asesor, el ajuste propuesto por la IA y el **enlace a la página de revisión**.
7. `Preservar contexto tras la aprobación` rearma el contexto desde `Aplicar correcciones` (la respuesta de Teams no lo
   trae) y normaliza la aprobación; `IF - ¿Aprobó la corrección?` decide:
   - **aprobada** → `Re-invocar motor` (W3 recalcula) y sigue al cierre de corrección;
   - **rechazada, sin respuesta o fallo al enviar** → Revisión Manual (motivo `aprobacion_rechazada`).
8. `Preservar contexto de la corrección` agrega el comentario del asesor y el contexto al resultado del motor, y llama a
   `[SUB] CCB - W4D Cierre de Corrección`.

**Relaciones:** lo llama W4D (`Ejecutar Corrección IA`) **después de responderle al asesor** (ver más abajo); llama a
W3 por medio de `Re-invocar motor`, al subflujo de Revisión Manual y al subflujo de Cierre de Corrección.

### 8.5 `[SUB] CCB - W4D Cierre de Corrección` — `POeFkqQp8e4cGfY3` · 17 nodos
**Por qué:** todo lo que pasa **después** del recálculo (verificar el resultado, guardar la ronda, avisar por Teams y
manejar los dos fallos posibles) estaba mezclado con el resto del camino de correcciones.
**Cómo funciona:** `IF - ¿Recálculo exitoso (ok)?` → si fue bien: `Data Table - Releer cotización` →
`IF - ¿Comentario ya procesado?` (guarda de idempotencia: un reenvío del mismo POST **no consume otra ronda**) →
`Data Table - Guardar ronda y comentario` (ronda +1, estado `EN_REVISION`) → `Reconstruir mensaje simple` →
`Teams - Enviar mensaje (corrección)` con el enlace a la página → confirmación. Si el motor rechazó el recálculo o
lanzó una excepción: `Preparar error - Recálculo falló` → `Data Table - Marcar ERROR_CALCULO` →
`[SUB] CCB - Registrar y Alertar Error` → confirmación de error. Si falla el mensaje de Teams:
`Preparar error - Teams envío` → registra en `Errores_CCB` → confirma igual (el asesor no queda sin respuesta).
**Relaciones:** lo llama C1; llama al subflujo de error y usa la configuración para el chat de Teams y la URL de revisión.

### 8.6 W4D como router (el flujo que los orquesta)
**Por qué:** era un lienzo de 54 nodos (muy por encima del umbral). **Cómo funciona hoy (20 nodos):**
webhook autenticado (`X-CCB-Auth`) → `Extraer decisión del body` → `Validar decisión reconocida`
(rechazo temprano **400**) → `Ejecutar Leer Contexto Propuesta` → `Consolidar datos y decisión` → tres IF en cascada →
`Ejecutar Aprobar` / `Ejecutar Cancelar` / **`Responder decisión - Corrección en aprobación`** →
`Ejecutar Corrección IA` → `Responder decisión` (200). La respuesta de la rama de correcciones se emite **antes** de
esperar la aprobación humana, para que la página de revisión no quede colgada.

---

## 9. `[OPS] CCB - Monitoreo del pipeline`
**ID:** `ZwBFTBhwS9pjS69X` · **Nodos:** 10 · **Plan:** F6-05

**Por qué se creó.** El framework pide monitorear cuatro métricas (tasa de ejecución, tasa de error por flujo con umbral
2%, latencia p95 y profundidad de cola) y no existía ningún punto donde consultarlas.

**Cómo funciona.** Corre **cada hora**: lee el endpoint Prometheus `/metrics` de la instancia (URL desde
`Configuracion_CCB.metricas_url`), lee los errores registrados en la última hora desde `Errores_CCB` (columna
`error_timestamp`), calcula en un nodo de código la tasa de error acumulada, las ejecuciones totales, la latencia p95
(a partir de los buckets del histograma) y la saturación de handles, **publica cada métrica como una fila** en la Data
Table `Metricas_CCB` (upsert por `metrica`, así la tabla no crece) y, si se supera un umbral (≥2% de error o ≥3 errores
en la hora), manda el detalle al correo de `alertas_email`.

**Limitaciones declaradas.** `/metrics` acumula desde el arranque del proceso y no trae etiqueta de flujo, así que la
tasa de error es global y el desglose por flujo sale de `Errores_CCB`; la profundidad de cola real (workers) no es
accesible por API y se usa la saturación de handles como proxi.

**Relaciones.** Es el único flujo que no procesa propuestas: **lee** el estado de todo el pipeline. Depende del subflujo
de configuración, de `Errores_CCB` (que alimentan los 8 flujos que registran errores) y de `Metricas_CCB`.

---

## 9.bis `[OPS] CCB - Regresión del pipeline`
**ID:** `GVE3iNQ80y5Q9FEw` · **Nodos:** 16 · **Plan:** R3 y R9 (feature `regresion-y-documentacion-ccb`)

**Por qué se creó.** La re-auditoría dejó *Testing* como la dimensión más baja (11,7/15): todo se verificaba a mano y
cada cambio exigía repetir el procedimiento completo. Este flujo convierte esa verificación en una **prueba de regresión
repetible**: en un clic (o sola, cada lunes) recorre los caminos críticos y publica un semáforo.

**Cómo funciona.** Se dispara **a mano** (`Trigger manual`) o **sola los lunes a las 6:00** (`Schedule - Regresión
semanal`). En orden:

1. `Ejecutar Leer Configuracion` (el subflujo de configuración: de ahí sale el destinatario del resumen).
2. `Ejecutar Preparar filas` → **[SUB] CCB - Regresion: Preparar filas**: crea **cinco filas descartables** en
   `Cotizaciones_CCB`, `Solicitudes_CCB` y `Criterios_Cotizacion` con ids fijos (`SOL-PRUEBA-REGRESION-APROBAR`,
   `-CANCELAR`, `-REVISION`, `-ERROR`, `-ENVIO`). Los ids son fijos a propósito: cada corrida **reutiliza** las mismas
   filas (upsert), así las tablas no crecen. Cada tabla lleva una marca para poder borrarlas de una sola vez
   (`servicio`, `observaciones` y `comentarios` = `SOL-PRUEBA-REGRESION`).
3. Cinco casos en cadena, cada uno con su nodo de preparación y su subflujo real:
   `W4D Aprobar` (espera `APROBADA`) → `W4D Cancelar` (espera `CANCELADA`) → `W4D Revisión Manual` con motivo `tope`
   (espera `REVISION_MANUAL`) → `Registrar y Alertar Error` (espera una fila en `Errores_CCB` con `error_timestamp`) →
   `Cerrar envío` (espera `ENVIADA` en la cotización **y** en la solicitud, con `fecha_envio`).
4. `Ejecutar Verificar y limpiar` → **[SUB] CCB - Regresion: Verificar y limpiar**: lee las tres tablas y **verifica el
   estado real**, no lo que devolvieron los subflujos (así se detecta una regresión en el mapeo de un `update`); publica
   el resultado en `Metricas_CCB` como la métrica `regresion_pipeline` (`valor` = casos ok, `estado` = `ok`/`FALLO`);
   **borra sus propias filas** de las cuatro tablas (incluida `Errores_CCB`, para no ensuciar la métrica de errores del
   monitor) y devuelve el resumen.
5. `Outlook - Enviar resumen de regresion`: manda el semáforo con el detalle caso por caso.

**Detalle técnico.** La operación de borrado del nodo *Data Table* se llama **`deleteRows`** (la documentación la
etiqueta "Delete", pero el valor interno es `deleteRows`; con `delete` el nodo falla con
`Cannot read properties of undefined (reading 'execute')`). Los nodos de preparación y comparación usan `executeOnce`
para que cada caso corra **una sola vez** aunque los nodos de lectura devuelvan muchas filas.

**Relaciones.** No procesa propuestas reales: **prueba** los flujos. Llama a los subflujos de configuración, de error y a
tres ramas de W4D; escribe y borra en `Cotizaciones_CCB` y `Errores_CCB`; publica en `Metricas_CCB` y avisa al correo de
`alertas_email`. Los ids `SOL-PRUEBA-REGRESION-*` son la marca para reconocer sus filas.

---

## 9.ter Los dos subflujos de la regresión
**Plan:** R9. El flujo de regresión tenía 20 nodos (el límite del criterio de arquitectura) y necesitaba crecer: se
extrajeron la preparación y la verificación/limpieza, y quedó en **16 nodos**.

### `[SUB] CCB - Regresion: Preparar filas` — `DgUfcoudk228kOw8` · 7 nodos
**Por qué:** crear y reutilizar las filas de prueba de las tres tablas implicadas (`Cotizaciones_CCB`,
`Solicitudes_CCB` y `Criterios_Cotizacion`) sin cargar el flujo principal. **Cómo funciona:** tres pares
preparador + *upsert* (los preparadores llevan `executeOnce` para emitir su lista una sola vez). Las filas quedan
marcadas con `SOL-PRUEBA-REGRESION`. **Relaciones:** lo llama el flujo de regresión.

### `[SUB] CCB - Regresion: Verificar y limpiar` — `OuE4SS9Jujz1dVif` · 11 nodos
**Por qué:** la verificación del estado real y la limpieza de las cuatro tablas. **Cómo funciona:** tres lecturas
(cotizaciones, solicitudes y errores), `Comparar resultados` (compara contra lo esperado caso por caso), publica el
semáforo en `Metricas_CCB`, borra con `deleteRows` las filas marcadas de las cuatro tablas y devuelve el resumen para el
correo. **Relaciones:** lo llama el flujo de regresión; escribe y borra en cuatro tablas y publica en `Metricas_CCB`.

---

## 10. El catch-all (flujo original que **no** se migró)
**ID:** `Dh2lAQtzyoZBpXie` · 6 nodos

Es el `errorWorkflow` centralizado de los 11 flujos activos. Se evaluó migrarlo al subflujo compartido de error y la
decisión fue **no hacerlo**: el registro del subflujo hace *upsert* por `id_solicitud + workflow_origen + nodo_fallido`,
así que dos incidentes distintos del mismo nodo se pisarían entre sí; en el catch-all el `id_solicitud` es fijo
(`N/A (catch-all)`) y lo que importa es conservar el **historial de cada incidente**. Mantiene su insert propio, con
marca de tiempo, enmascarado del mensaje y reintentos en el envío del correo.

---

## 11. Mapa de dependencias (quién llama a quién)

```
W4D (router) ──> [SUB] CCB - W4D Aprobar / Cancelar / Revisión Manual
   │                    │                                  ▲
   │                    │                                  │
   └──> [SUB] CCB - W4D Corrección IA ──> W3 (motor) ───────┤
                 │  ▲                 └──> [SUB] CCB - Generar PDF de Propuesta
                 │  └──> [SUB] CCB - W4D Cierre de Corrección
                 └─────> [SUB] CCB - Leer Configuración ─────┐
                                                            │
W4B/W4C/W4D/W5B ──> [SUB] CCB - Leer Contexto Propuesta
W5B ──> [SUB] CCB - Enviar propuesta al cliente ──> [SUB] CCB - Cerrar envío
W5B ──> [SUB] CCB - Cerrar error de envío ──> [SUB] CCB - Registrar y Alertar Error           │
W1/W2A/W4A/W4B/W4D/W5A/W5B/W6 ──> [SUB] CCB - Registrar y Alertar Error
W2A ──> [SUB] CCB - Invocar Motor y Guardar Cotización ──> W3
[OPS] CCB - Monitoreo del pipeline ──> lee todo el pipeline ───┘
catch-all ──> recibe los fallos no capturados de los 11 flujos activos
[OPS] CCB - Regresion del pipeline ──> [SUB] Regresion: Preparar filas / Verificar y limpiar
   └──> prueba los subflujos de error, tres ramas de W4D y el cierre de envio
```
