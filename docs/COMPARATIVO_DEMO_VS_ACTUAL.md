# Comparativo: el pipeline del demo vs. el pipeline actual

**Fecha:** 2026-09-23
**Para qué sirve.** El demo que se grabó y se envió describe el pipeline como *12 workflows + 2 páginas*. Este documento
responde una pregunta concreta de negocio y de entrega: **¿sigue funcionando de la misma manera?** La respuesta corta es
**sí, el recorrido de negocio es idéntico y está vivo**, con **una sola diferencia visible** (la aprobación en Teams antes
del recálculo con IA) y un interior mucho más robusto.

**Cómo se verificó.** Todo lo que afirma este documento se comprobó contra la **instancia viva** el 2026-09-23:
inventario de workflows por API, descarga real de un PDF desde el microservicio, y respuesta HTTP de las dos páginas.
No hay afirmaciones tomadas de memoria.

---

## 1. El recorrido del demo, paso a paso, hoy

| # | Paso del demo | Estado | Qué cambió |
|---|---|---|---|
| 1 | **W1** `CCB · W1 — Extracción de información del cliente` (`w6h0qSblUESIpSVc`) — correo de mercadeo o contacto directo → link del form | ✅ Activo, mismo ID | Por dentro: el registro y la alerta de error se extrajeron a un subflujo compartido |
| 2 | **📄** `informaciongeorreferenciada-ccb.vercel.app` — el cliente completa el formulario | ✅ **HTTP 200** | Sin cambios (página externa) |
| 3 | **W2C** `CCB · W2C — Recepción del formulario externo` (`u6KCMnLwFOp6Ja0N`) | ✅ Activo, mismo ID | Sin cambios funcionales |
| 4 | **W2A** hoy `CCB · W2A — Guardar criterios y cotizar` (`VChcasvisGKekezR`) | ✅ Activo, **mismo ID** | **Renombrado** (perdió el `[SUB]`: es una etapa del pipeline). 25 → **19 nodos**; el motor y el guardado salieron a un subflujo |
| 5 | **W3** hoy `CCB · W3 — Motor de criterios y precio` (`cHOIOEFB5nbltN82`) | ✅ Activo, **mismo ID** | **Renombrado**. 25 → **16 nodos**; la generación del PDF salió a un subflujo. Mismo PDF, misma URL |
| 6 | **W4A** `CCB · W4A — Router de aprobación` (`7gmpPMBJtEb0W3J5`) | ✅ Activo, mismo ID | Sin cambios funcionales (8 nodos) |
| 7 | **W4B** hoy `CCB · W4B — Aprobación por Teams` (`5RJdnHDQ8NuWZJG7`) | ✅ Activo, **mismo ID** | **Renombrado**. 14 → **11 nodos**; la lectura de contexto salió a un subflujo |
| 8 | **📄** `revision-propuesta-ccb.vercel.app` — se revisa el PDF y se decide | ✅ **HTTP 200** | Sin cambios (página externa) |
| 9 | **W4C** `CCB · W4C — Consultar la propuesta para revisión` (`KuLSIzBZgaRIjuSu`) | ✅ Activo, mismo ID | 12 → **9 nodos** (contexto a subflujo) |
| 10 | **W4D** `CCB · W4D — Procesar la decisión` (`W0TDH4b0tHCNOzFQ`) | ✅ Activo, mismo ID | **54 → 19 nodos** + 5 subflujos de rama. **La rama de IA tiene 3 guardarraíles nuevos** (ver §3) |
| 11 | **W5A** `CCB · W5A — Router de envío` (`gvIn6mbAn2Y1bMRR`) | ✅ Activo, mismo ID | Sin cambios funcionales (11 nodos) |
| 12 | **W5B** hoy `CCB · W5B — Envío al cliente` (`XWBHgbmtBubA4gqx`) | ✅ Activo, **mismo ID** | **Renombrado**. 25 → **19 nodos** + 3 subflujos (enviar, cerrar envío, cerrar error) |
| 13 | **W6** `CCB · W6 — Finalizador de cotizaciones` (`mPwl4qUb0zQkmDHN`) | ✅ Activo, mismo ID | 12 → **10 nodos** (contexto a subflujo) |
| 14 | **Catch-all — Errores no capturados** `Dh2lAQTzyoZBpXie` | ✅ Activo, mismo ID | Se conserva con su diseño propio (no se migró al subflujo compartido, para no pisar el historial de incidentes) |

**Los 12 workflows del demo siguen activos, con el mismo ID.** Eso significa que **las URLs de los webhooks, las
credenciales y la configuración de las dos páginas siguen apuntando al mismo lugar**: no hay nada que reconectar.

Eso se verificó aparte, comparando el snapshot actual contra el primer commit de cada archivo: los **tres paths de
webhook son idénticos** a los del demo —`solicitud-georreferenciada` (W2C), `consultar-propuesta` (W4C) y
`decidir-propuesta` (W4D)—, así que las páginas siguen llamando exactamente a la misma dirección. Lo único que cambió
ahí es que **ahora exigen la cabecera de autenticación** (`X-CCB-Auth`), que las páginas ya envían.

---

## 2. Lo que se agregó (17 flujos nuevos)

Ninguno de estos aparece en el recorrido del cliente: son piezas internas que los flujos originales (o la regresión)
invocan, más los dos flujos operativos.

| Flujo nuevo | ID | Qué resuelve |
|---|---|---|
| `[SUB] CCB · Error — Registrar y alertar` | `2dY1kaT7I5a0eP2w` | El registro y la alerta de error estaban duplicados en 8 flujos; ahora es uno solo |
| `[SUB] CCB · Config — Leer la configuración` | `Hgy02eqPhnsdJvkq` | Lee los 12 valores de `Configuracion_CCB`; ningún nodo tiene correos ni URLs escritos a mano |
| `[SUB] CCB · Contexto — Leer el contexto de la propuesta` | `GELWpskp0aYJ2zPg` | Las tres lecturas de contexto de W4B/W4C/W4D/W5B |
| `[SUB] CCB · PDF — Generar el PDF` | `DF3emCmBBBB2HA3i` | La etapa de PDF salió de W3 (25 → 17 nodos; 16 sin contar las notas fijas) |
| `[SUB] CCB · Motor — Invocar el motor y guardar` | `MHWlUApSFT6gpBHs` | La invocación del motor y el guardado, fuera de W2A |
| `[SUB] CCB · Envío — Enviar al cliente` | `AnPJGVWylmKEYWmJ` | El envío al cliente, fuera de W5B |
| `[SUB] CCB · Envío — Cerrar el envío` | `1Zzkrg3dTkTrddgp` | El cierre correcto del envío |
| `[SUB] CCB · Envío — Cerrar el error de envío` | `D2d9Og6UUvq13TJA` | El cierre cuando el envío falla |
| `[SUB] CCB · W4D — Aprobar` / `Cancelar` | `8j6BCwXkgJCccyO1` / `Jgf514VxDINJ8ra3` | Las dos ramas simples de W4D |
| `[SUB] CCB · W4D — Revisión manual` | `iNSErCHs2iw33emJ` | Unifica las dos cadenas casi iguales de revisión manual (tope, IA apagada, confianza baja, aprobación rechazada) |
| `[SUB] CCB · W4D — Corrección con IA` | `3NAcLF4jaZ1JBw0A` | Todo el camino de correcciones con IA, con sus guardarraíles |
| `[SUB] CCB · W4D — Cierre de la corrección` | `POeFkqQp8e4cGfY3` | Lo que pasa después del recálculo (guardar ronda, avisar, manejar fallos) |
| **`[OPS] CCB · Monitoreo — Métricas del pipeline`** | `ZwBFTBhwS9pjS69X` | **Nuevo**: cada hora publica las 4 métricas del framework y avisa si se supera un umbral |
| `[SUB] CCB · Regresión — Preparar filas` | `DgUfcoudk228kOw8` | Crea las filas descartables que usa la regresión en tres tablas |
| `[SUB] CCB · Regresión — Verificar y limpiar` | `OuE4SS9Jujz1dVif` | Verifica el estado real, publica el semáforo y limpia lo que creó |
| **`[OPS] CCB · Regresión — Prueba de regresión`** | `GVE3iNQ80y5Q9FEw` | **Nuevo**: recorre los caminos críticos cada lunes y a mano |

**Total hoy: 29 workflows activos** (los 12 del demo + 17 nuevos). En el repo hay **30 archivos** de snapshot: los 29
activos más el formulario antiguo (`W2B`), que quedó retirado pero se conserva como referencia histórica.

---

## 3. La única diferencia visible en el comportamiento

En el paso 10 del demo —*"W4-D (decisión, con rama de IA para correcciones, tope 3 rondas)"*— la rama de IA ahora tiene
**tres guardarraíles** que antes no existían:

| Guardarraíl | Qué hace | Qué pasa si se activa |
|---|---|---|
| **Confianza baja** (F7-01) | Si el modelo declara `confianza: baja` | Va a **revisión manual**; no se aplica nada y **no se consume ronda** |
| **Interruptor de apagado** (F7-02) | La clave `ia_correccion_habilitada` en `Configuracion_CCB` | Si está en falso, va a **revisión manual** sin llamar al modelo |
| **Aprobación humana en Teams** (F7-03) | Antes del recálculo: `sendAndWait`, aprobación doble, hasta 24 h, con el enlace a la página de revisión | Aprobada → recálculo y ronda +1. **Rechazada, sin respuesta o fallo de envío → revisión manual, sin consumir ronda** |

**Lo demás del recorrido es idéntico.** Aprobar, cancelar y pedir correcciones se hacen exactamente igual desde la
página de revisión.

Detalle técnico importante para el front: **W4D responde al webhook antes de esperar la aprobación humana**, así la
página de revisión no queda colgada mientras se espera (hasta 24 h).

Dos mejoras más que no se ven pero cambian el resultado: el ajuste de la IA **valida cada valor contra las listas
cerradas** de criterios y descarta los inválidos (antes podía corromper el criterio), y el **nombre y la razón social del
cliente salen parciales** en los correos de alerta.

---

## 4. Comparativo de indicadores

| Indicador | En el demo | Hoy |
|---|---|---|
| Workflows activos | 12 | **29** (12 + 17 nuevos) |
| Flujo más grande | 54 nodos (W4D) | **19 nodos** |
| Valores incrustados en nodos (correos, URLs, destinatarios) | 20+ | **0** |
| Cadenas de error que perdían el detalle | 4 | **0** |
| Reintentos y timeout explícito | parcial | **11/11 flujos** |
| Enmascarado de datos personales en alertas | no | **sí** |
| Marca de tiempo en los errores | no | **sí** (8 puntos de registro) |
| Monitoreo de las 4 métricas | no existía | **cada hora**, con umbral y aviso |
| Retención de ejecuciones | todas | **acotada por flujo** (se conservan los errores) |
| Guardarraíles de IA | ninguno | **3** (confianza, interruptor, aprobación) |
| Puntaje de la auditoría | **53,6 / 100** | **87,7 / 100** |

---

## 5. Qué no se puede dar por verificado

| Punto | Estado |
|---|---|
| La rama de **rechazo / expiración** de la aprobación en Teams | Pendiente de ejecutar con tráfico real (la aprobación **positiva** sí se verificó con un clic real: recálculo OK y ronda 0 → 1) |
| La rama de **confianza baja** | Implementada; sin corrida real |
| **Métrica exacta de error por flujo** | ✅ **Resuelto el 24/09.** El diagnóstico anterior era incorrecto: la credencial *Header Auth* ya existía y estaba asignada; fallaba que el nodo no la usaba (`authentication` sin configurar) más un `ReferenceError` por zona muerta temporal en el nodo de métricas. Corregidos ambos, la métrica publica datos reales (ejecución `428791`, 6 métricas) |
| **Poda de ejecuciones** a nivel de instancia y cierre de `/metrics` | Depende de Tecnología |
| **Mover los 17 flujos nuevos** a la carpeta `Servicios_Información_Cotizaciones_v2.0` | El API de carpetas responde 403: requiere una key con scopes `folder:*` y/o registrar la instancia, o arrastrarlos en la UI |
| **Fila basura** en `Cotizaciones_CCB` (`id 21`, todos los campos nulos, `ENVIADA`, 2026-09-18) | Detectada; se puede borrar con `n8n_manage_datatable` |
| El nodo webhook de **W4C** perdió el parámetro explícito `httpMethod: GET` | Queda con el valor por defecto de n8n, que es GET: **el comportamiento es el mismo**, pero conviene volver a dejarlo explícito para que el contrato no dependa de un valor implícito |

---

## 6. Nota de presentación

Si el video del demo muestra la rama de correcciones con IA, **conviene rehacer ese fragmento o agregar una aclaración**:
hoy, entre "el asesor pide correcciones" y "el motor recalcula" hay un mensaje de Teams pidiendo autorizar el ajuste.
Todo lo demás del video sigue siendo exacto.

Si se vuelve a grabar, el orden visual recomendado es: el formulario → la cotización y el PDF → el aviso de Teams → la
página de revisión → aprobar (o pedir correcciones y autorizar en Teams) → el correo al cliente → el cierre. Y para la
explicación interna, el orden de los 29 flujos por familia: los 11 principales + el catch-all, los 15 subflujos y los 2 flujos
operativos.
