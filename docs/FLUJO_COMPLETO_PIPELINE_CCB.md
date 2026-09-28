# El pipeline CCB de punta a punta

**Para qué sirve este documento.** Explica **todo** el recorrido de una propuesta comercial: quién interviene, qué ve
cada persona, qué hace el sistema en cada paso, qué pasa cuando algo falla y cómo se opera el conjunto. Un lector nuevo
puede entender el pipeline sin abrir n8n.

**Qué es el pipeline.** Automatiza la venta de los servicios de información de la Cámara de Comercio de Barranquilla: desde
que un lead pide información hasta que la propuesta se envía, se aprueba, se cierra o se cancela — con el cálculo de
precios, la generación del PDF, la aprobación interna y el envío al cliente.

**Los números.** 29 flujos activos en n8n (12 principales + 15 subflujos + 2 operativos), 6 tablas de datos, 3 webhooks
públicos autenticados y 2 páginas web. Puntaje de la última auditoría de buenas prácticas: **89,8/100** (remedido el 24/09)
([re-auditoría de cierre del 23/09](AUDITORIA_BUENAS_PRACTICAS_2026-09-23_CIERRE.md)).

---

## 1. El recorrido en una página

```
  LEAD (correo de mercadeo / contacto directo)
        │
        ▼
  W1 · Extracción de información del cliente ──► envía el link del formulario
        │
        ▼
  📄 Formulario  informaciongeorreferenciada-ccb.vercel.app      ← lo completa el CLIENTE
        │  POST /webhook/solicitud-georreferenciada  (con cabecera X-CCB-Auth)
        ▼
  W2C · Recepción del formulario externo  (valida campos obligatorios → 400 si faltan)
        │
        ▼
  W2A · Guardar criterios y cotizar  ──►  [SUB] Motor — Invocar el motor y guardar ──► W3
        │                                                                              │
        │                                                          W3 · Motor de criterios y precio
        │                                                              + [SUB] PDF — Generar el PDF
        │                                                                              │
        ▼                                                                              ▼
  Cotizaciones_CCB  (estado PROPUESTA_GENERADA)  ◄────────────────────────  pdf_url del PDF
        │
        ▼
  W4A · Router de aprobación ──► W4B · Aprobación por Teams ──► aviso al APROBADOR con el enlace
        │
        ▼
  📄 Página de revisión  revision-propuesta-ccb.vercel.app       ← decide el ASESOR
        │  GET  /webhook/consultar-propuesta   (W4C · muestra el contexto y el PDF)
        │  POST /webhook/decidir-propuesta     (W4D · registra la decisión)
        ▼
  W4D · Procesar la decisión  ── tres ramas ──┐
        │                                  ├── APROBAR   → estado APROBADA
        │                                  ├── CANCELAR  → estado CANCELADA
        │                                  └── CORREGIR  → rama de IA con 3 guardarraíles
        ▼
  W5A · Router de envío ──► W5B · Envío al cliente ──► [SUB] Envío — Enviar al cliente
        │                                                     (correo + PDF al CLIENTE)
        │                                              ──► [SUB] Envío — Cerrar el envío
        │                                                     (estado ENVIADA + aviso interno)
        ▼
  W6 · Finalizador de cotizaciones  (cierre automático a los 30+ días)

  ── Red de respaldo transversal ──
  [SUB] Error — Registrar y alertar  (lo llaman los flujos que fallan: fila + correo)
  catch-all  (errorWorkflow de los 11 flujos principales: fallos no capturados)
  [OPS] Monitoreo — Métricas del pipeline  (cada hora: 4 métricas + aviso por umbral)
  [OPS] Regresión — Prueba de regresión  (los lunes 6:00: prueba los 6 caminos críticos)
```

---

## 2. Los actores

| Actor | Qué hace | Qué ve |
|---|---|---|
| **Cliente / lead** | Pide información y completa el formulario | El correo con el link y, al final, la propuesta en PDF |
| **Asesor comercial** (Fausto) | Revisa la propuesta y decide: aprobar, cancelar o pedir correcciones | El aviso de Teams y la página de revisión (con el PDF) |
| **Aprobador** | Autoriza (o rechaza) que la IA ajuste los criterios antes de recalcular | El mensaje de Teams con el ajuste propuesto y el enlace a la página |
| **Equipo técnico** | Recibe las alertas de error y el resumen de la regresión | Los correos de alerta, `Errores_CCB` y `Metricas_CCB` |
| **Sistema (n8n)** | Ejecuta, calcula, genera el PDF, notifica y registra | — |

---

## 3. El recorrido paso a paso

### Etapa 1 — El lead y el formulario

1. Llega un lead por correo de mercadeo o contacto directo. **W1** (`Extracción de información del cliente`) lo procesa y le
   envía el enlace del formulario.
2. El cliente completa el formulario en `informaciongeorreferenciada-ccb.vercel.app`. La página llama al webhook
   `solicitud-georreferenciada` con la cabecera de autenticación.
3. **W2C** (`Recepción del formulario externo`) valida que estén los campos obligatorios: si falta alguno responde **400** con
   el detalle, sin tocar la base. Si están, sigue.
4. **W2A** (`Guardar criterios y cotizar`) guarda los criterios del cliente y llama al subflujo
   `[SUB] Motor — Invocar el motor y guardar`, que invoca a **W3** y guarda el resultado.
5. **W3** (`Motor de criterios y precio`) calcula el precio con el motor de criterios y llama a
   `[SUB] PDF — Generar el PDF`, que pide el PDF al microservicio, **lo persiste** y devuelve la `pdf_url`
   (`…/pdfs/{id_solicitud}.pdf`). Si no puede construir la URL pública (por ejemplo, si falta `id_solicitud`), el
   subflujo devuelve el fallo como **error** (`ok: false` con el motivo), no como éxito.
6. Queda una fila en **`Cotizaciones_CCB`** con `estado = PROPUESTA_GENERADA`, el valor, el IVA, el total y la
   `pdf_url` (servible en `/pdfs/{id_solicitud}.pdf`).

**Si algo falla:** el error se registra y se avisa (ver §5). El cliente no recibe nada roto: la página muestra el error.

### Etapa 2 — La aprobación interna

7. **W4A** (`Router de aprobación`) detecta las cotizaciones en `PROPUESTA_GENERADA`.
8. **W4B** (`Aprobación por Teams`) avisa al asesor por Teams con el enlace a la página de revisión. Lee el
   contexto de la propuesta con `[SUB] Contexto — Leer el contexto de la propuesta` y el chat desde la configuración.
9. El asesor abre `revision-propuesta-ccb.vercel.app`, que consulta **W4C** (`Consultar la propuesta para revisión`, webhook
   `consultar-propuesta`) y muestra los datos, los criterios y el PDF.

### Etapa 3 — La decisión (las tres ramas)

10. El asesor decide en la página. **W4D** (`Procesar la decisión`) recibe la decisión por el webhook
    `decidir-propuesta`, valida que sea reconocible (si no, **400**) y responde **antes** de cualquier espera.

| Rama | Qué hace | Estado final |
|---|---|---|
| **Aprobar** | `[SUB] W4D — Aprobar`: guarda el comentario del asesor | `APROBADA` |
| **Cancelar** | `[SUB] W4D — Cancelar`: guarda el comentario | `CANCELADA` |
| **Pedir correcciones** | `[SUB] W4D — Corrección con IA` (ver abajo) | `EN_REVISION` (ronda +1) o `REVISION_MANUAL` |

**La rama de correcciones, en orden, con sus tres guardarraíles:**

1. Si ya hay **3 rondas** → `[SUB] W4D — Revisión manual` con motivo `tope` (no consume ronda).
2. Si el interruptor `ia_correccion_habilitada` está en **falso** → Revisión Manual con motivo `ia_desactivada`
   (no llama al modelo).
3. La IA ajusta los criterios y declara su **confianza**. Cada valor se valida contra las listas cerradas y los inválidos
   se descartan.
4. Si la confianza es **baja** → Revisión Manual con motivo `confianza_baja` (no se aplica nada).
5. Se pide **aprobación humana por Teams** (`sendAndWait`, hasta 24 h) con el ajuste propuesto y el enlace.
6. Aprobada → se recalcula con **W3** y sigue `[SUB] W4D — Cierre de la corrección` (guarda la ronda, sube a `EN_REVISION` y
   avisa por Teams). Rechazada, sin respuesta o fallo de envío → Revisión Manual con motivo `aprobacion_rechazada`.

Ninguno de los caminos a Revisión Manual **consume una ronda de corrección**.

### Etapa 4 — El envío al cliente

11. **W5A** (`Router de envío`) toma las cotizaciones aprobadas.
12. **W5B** (`Envío al cliente`) llama a `[SUB] Envío — Enviar al cliente`: correo con el PDF al cliente y luego
    `[SUB] Envío — Cerrar el envío`, que marca `ENVIADA` en `Cotizaciones_CCB` (con `fecha_envio` y `enviado_a`) y en
    `Solicitudes_CCB`, y avisa internamente al asesor.
13. Si el envío falla, `[SUB] Envío — Cerrar el error de envío` registra el fallo y **el asesor igual recibe respuesta** (nadie queda
    sin contestación).

### Etapa 5 — El cierre

14. **W6** (`Finalizador de cotizaciones`) cierra automáticamente las cotizaciones que llevan **30+ días** sin moverse.

---

## 4. Los estados de una propuesta

```
PROPUESTA_GENERADA ──► (el asesor decide)
        │
        ├── APROBADA ──► ENVIADA ──► (cierre a los 30+ días)
        ├── CANCELADA
        ├── EN_REVISION  (corrección con IA aplicada; ronda +1, hasta 3)
        ├── REVISION_MANUAL  (tope, IA apagada, confianza baja o aprobación rechazada)
        └── ERROR_CALCULO  (el motor rechazó el recálculo)
```

`EN_REVISION` vuelve a la página de revisión: el asesor puede aprobar, cancelar o pedir otra corrección (hasta el tope).

---

## 5. Cuando algo falla

**Tres capas, en orden:**

1. **Reintentos.** Todos los nodos de red reintentan 5 veces cada 5 segundos; los dos nodos HTTP tienen timeout de 60 s.
2. **Subflujo compartido `[SUB] Error — Registrar y alertar`.** Lo llaman los flujos que detectan un fallo: escribe una fila
   en **`Errores_CCB`** con `id_solicitud`, `workflow_origen`, `nodo_fallido`, `mensaje_error` (con los datos personales
   enmascarados: `<correo>`, `<url>`, `<num>`) y `error_timestamp` en hora de Bogotá, y manda el correo de alerta. Devuelve
   el item al llamador, así **el flujo que falló no se corta**. Si el **envío del correo de alerta** falla, una rama de
   error del subflujo registra ese fallo en `Errores_CCB` con claves propias (`workflow_origen = 'alerta-error'`) y
   **también devuelve el item al llamador**, para no romper el mismo contrato.
3. **Catch-all.** El `errorWorkflow` de los 11 flujos principales captura lo que no se detectó arriba y registra el
   incidente (conserva el historial: no hace *upsert*, inserta).

**Cómo se diagnostica un error, en 4 pasos:**

1. Llega el correo de alerta → anota el `id_solicitud` y el nodo.
2. Busca la fila en `Errores_CCB` por ese id → ahí está el mensaje enmascarado y la hora.
3. Abre la ejecución en n8n (o consulta `GET /api/v1/executions?workflowId=...`) y mira el nodo que falló.
4. Causas habituales: el **túnel del microservicio de PDF caído** (es el punto más frágil), el **motor de cálculo
   rechazando** el caso, o **Teams/Outlook** sin credencial válida.

**Lo que no se ve solo:** si el **correo de alerta** falla, ya no queda silencioso: el subflujo compartido tiene una rama
 de error que registra el fallo de envío en `Errores_CCB` con claves propias (`workflow_origen = 'alerta-error'`) y
devuelve igualmente el item al llamador. (Cerró el hueco declarado el 24/09; verificado con tráfico real, regresión
`428867`.)

---

## 6. Las tablas de datos

| Tabla | ID | Qué guarda | Quién escribe | Quién lee |
|---|---|---|---|---|
| **Configuracion_CCB** | `8ChPkhKrjag6Jkcs` | 12 claves: correos, URL del microservicio, chat de Teams, interruptor de IA, URL de revisión, URL de la API | Se edita a mano | Todos (por `[SUB] Config — Leer la configuración`) |
| **Solicitudes_CCB** | `u5gFYvTfuQRX71u5` | La solicitud del cliente | W2C / W2A | W4B, W4C, W5B |
| **Criterios_Cotizacion** | `ldABWugJR1GcFFyy` | Los criterios de cotización (sector, registros, plan…) | W2A / W4D | W3, W4D, W5B |
| **Cotizaciones_CCB** | `YAvQTqzsgJWjacVZ` | La propuesta: valores, `pdf_url`, estado, ronda, comentario, envío | W2A (motor), W4D, W5B, W6 | W4A, W4C, W4D, W5A, W5B, W6 |
| **Errores_CCB** | `lO46Xkqj0TTedLjI` | Un registro por incidente, con marca de tiempo | Subflujo de error + catch-all | El monitor y el diagnóstico humano |
| **Metricas_CCB** | `W3oJ4a8h0TAPO9ji` | Las 4 métricas del framework + el semáforo de la regresión | El monitor y la regresión | El equipo técnico |

**Las 12 claves de configuración:** `asesor_nombre`, `asesor_email`, `asesor_telefono`, `alertas_email`,
`notificacion_envio_email`, `microservicio_pdf_url`, `teams_chat_aprobacion`, `teams_chat_aprobacion_produccion`,
`metricas_url`, `ia_correccion_habilitada`, `revision_url`, `n8n_api_url`.

> **Dos claves están en modo prueba** (`teams_chat_aprobacion` y `notificacion_envio_email`): apuntan a un chat y a un
> buzón de prueba por decisión del proyecto. `teams_chat_aprobacion_produccion` ya tiene el chat real del aprobador,
> listo para el cambio.

---

## 7. El mapa técnico: los 29 flujos

### Los 12 principales (lo que hace el negocio)

| Flujo | ID | Rol |
|---|---|---|
| W1 · Extracción de información del cliente | `w6h0qSblUESIpSVc` | Lead → link del formulario |
| W2A · Guardar criterios y cotizar | `VChcasvisGKekezR` | Guarda criterios e invoca el motor |
| W2C · Recepción del formulario externo | `u6KCMnLwFOp6Ja0N` | Webhook del formulario (valida y responde) |
| W3 · Motor de criterios y precio | `cHOIOEFB5nbltN82` | Calcula y genera el PDF |
| W4A · Router de aprobación | `7gmpPMBJtEb0W3J5` | Detecta propuestas por aprobar |
| W4B · Aprobación por Teams | `5RJdnHDQ8NuWZJG7` | Avisa al asesor |
| W4C · Consultar la propuesta para revisión | `KuLSIzBZgaRIjuSu` | Webhook de consulta de la página |
| W4D · Procesar la decisión | `W0TDH4b0tHCNOzFQ` | Webhook de decisión + router de ramas |
| W5A · Router de envío | `gvIn6mbAn2Y1bMRR` | Detecta aprobadas por enviar |
| W5B · Envío al cliente | `XWBHgbmtBubA4gqx` | Envía y cierra el envío |
| W6 · Finalizador de cotizaciones | `mPwl4qUb0zQkmDHN` | Cierre a los 30+ días |
| Catch-all — Errores no capturados | `Dh2lAQTzyoZBpXie` | Red de respaldo de fallos no capturados |

### Los 15 subflujos (piezas reutilizables)

| Subflujo | ID | Lo llaman |
|---|---|---|
| Error — Registrar y alertar | `2dY1kaT7I5a0eP2w` | 10 flujos (13 puntos de llamada); 8 flujos del pipeline lo alcanzan |
| Config — Leer la configuración | `Hgy02eqPhnsdJvkq` | 9 flujos |
| Contexto — Leer el contexto de la propuesta | `GELWpskp0aYJ2zPg` | W4B, W4C, W4D, W5B |
| PDF — Generar el PDF | `DF3emCmBBBB2HA3i` | W3 |
| Motor — Invocar el motor y guardar | `MHWlUApSFT6gpBHs` | W2A |
| Envío — Enviar al cliente | `AnPJGVWylmKEYWmJ` | W5B |
| Envío — Cerrar el envío | `1Zzkrg3dTkTrddgp` | W5B |
| Envío — Cerrar el error de envío | `D2d9Og6UUvq13TJA` | W5B |
| W4D — Aprobar / Cancelar | `8j6BCwXkgJCccyO1` / `Jgf514VxDINJ8ra3` | W4D |
| W4D — Revisión manual | `iNSErCHs2iw33emJ` | W4D (4 motivos) |
| W4D — Corrección con IA | `3NAcLF4jaZ1JBw0A` | W4D |
| W4D — Cierre de la corrección | `POeFkqQp8e4cGfY3` | W4D |
| Regresión — Preparar filas | `DgUfcoudk228kOw8` | La regresión |
| Regresión — Verificar y limpiar | `OuE4SS9Jujz1dVif` | La regresión |

### Los 2 operativos (no procesan propuestas)

| Flujo | ID | Rol |
|---|---|---|
| Monitoreo — Métricas del pipeline | `ZwBFTBhwS9pjS69X` | Cada hora: 4 métricas + aviso por umbral |
| Regresión — Prueba de regresión | `GVE3iNQ80y5Q9FEw` | Lunes 6:00: prueba los 6 caminos críticos y publica el semáforo (`6/6`) |

Detalle de cada flujo (por qué se creó, cómo funciona, con qué se relaciona): [FLUJOS_PIPELINE_CCB.md](FLUJOS_PIPELINE_CCB.md).

---

## 8. Cómo se opera (tareas frecuentes)

| Necesito… | Qué hago |
|---|---|
| **Cambiar un destinatario, una URL o el chat de Teams** | Editar la fila correspondiente en `Configuracion_CCB`. **No se toca ningún workflow.** |
| **Apagar la corrección con IA** | Poner `ia_correccion_habilitada` en `false`. Las correcciones pasan a revisión manual y el resto sigue igual. |
| **Ver el estado del pipeline** | `Metricas_CCB` (las 4 métricas + `regresion_pipeline`) o el correo del monitor. |
| **Probar que todo sigue funcionando** | Lanzar a mano `[OPS] CCB · Regresión — Prueba de regresión` (o esperar el lunes). Deja el semáforo en `Metricas_CCB`. |
| **Investigar un error** | El correo de alerta → `Errores_CCB` → la ejecución en n8n (§5). |
| **Ver el PDF de una propuesta** | La columna `pdf_url` de `Cotizaciones_CCB`. |
| **Saber quién consumió una ronda** | La columna `ronda_correccion` de `Cotizaciones_CCB` (máximo 3) y el comentario en `comentario_fausto`. |

**Retención:** los flujos de alta frecuencia (W4A, W5A, W6 y el monitor) **no guardan los datos de las ejecuciones
exitosas** (sí los de error), para que la base no crezca sin control.

---

## 9. Lo que depende de terceros

| Dependencia | Riesgo | Qué hacer si falla |
|---|---|---|
| **Microservicio de PDF** (túnel ngrok) | Es el punto más frágil: si el túnel cae, no se generan PDFs ni quedan servibles en `/pdfs/{id_solicitud}.pdf` | Reiniciar el túnel y actualizar `microservicio_pdf_url` |
| **Motor de cálculo (W3)** | Si rechaza un caso, la propuesta queda en `ERROR_CALCULO` | Revisar los criterios; el error queda registrado |
| **Teams / Outlook** (credenciales OAuth) | Si la credencial vence, no salen avisos ni correos | Renovar la credencial en n8n |
| **n8n (instancia)** | La retención a nivel de instancia y el `/metrics` sin autenticar dependen de Tecnología | — |

---

## 10. Documentos relacionados

| Documento | Qué contiene |
|---|---|
| [FLUJOS_PIPELINE_CCB.md](FLUJOS_PIPELINE_CCB.md) | Ficha de cada flujo nuevo: por qué, cómo y con qué se relaciona |
| [TESTING_PIPELINE_CCB.md](TESTING_PIPELINE_CCB.md) | Los 5 niveles de prueba, el protocolo de datos descartables y el checklist por cambio |
| [AUDITORIA_BUENAS_PRACTICAS_2026-09-23_CIERRE.md](AUDITORIA_BUENAS_PRACTICAS_2026-09-23_CIERRE.md) | Puntaje por flujo y por dimensión (89,5/100 el 23/09; medición posterior del 24/09: 89,8, a 0,2 del umbral) y lo que falta para cruzar 90 |
| [COMPARATIVO_DEMO_VS_ACTUAL.md](COMPARATIVO_DEMO_VS_ACTUAL.md) | Qué cambió respecto del demo que se grabó |
| [PLAN_TRABAJO_FRAMEWORK.md](PLAN_TRABAJO_FRAMEWORK.md) | El plan de remediación con su evidencia |
