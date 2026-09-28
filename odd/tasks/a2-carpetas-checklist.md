# A2 — Checklist para mover los flujos a carpetas (UI de n8n)

> ## ✅ CERRADO — 28/09/2026
> Todos los flujos están en sus carpetas. **Conteo real verificado en la UI: `01` 12 · `02` 15 · `03` 2 · `99` 28**
> (el 25/09 `99` mostraba 15: faltaban 8 históricos y los 5 ajenos).
>
> - **El 24/09** se movieron 44 flujos (30 del proyecto + 14 históricos). Los **8 que faltaban estaban archivados** y por
>   eso no aparecían al arrastrar: revisar la vista *Archived* antes de dar un arrastre por completo.
> - **El 28/09 13:41** se movieron los 13 que quedaban: los 8 históricos más los 5 ajenos.
> - **Decisión del 28/09:** los 5 flujos de otra área se conservan **dentro de `99 · Retirados`**, así que esa carpeta
>   queda en **28** (23 del proyecto + 5 ajenos) y no en 23. Consecuencia asumida: el inventario completo de la
>   instancia (12 + 15 + 2 + 28 = **57**) queda bajo la carpeta del proyecto.
> - Las casillas de abajo quedan **sin tildar a propósito**: esta lista es el mapa flujo → carpeta, no un registro de
>   ejecución.

**Para qué sirve.** Lista exacta, leída de la instancia viva el 24/09, de qué flujo va en qué carpeta. La estructura y
el porqué están en [CONVENCION_NOMBRES_Y_CARPETAS_CCB.md](../../docs/CONVENCION_NOMBRES_Y_CARPETAS_CCB.md) §3; esto es
la versión operativa para arrastrar.

**Por qué a mano.** Mover flujos a carpetas exige una API key con scopes `folder:*`; la actual responde `403 Forbidden`
en `/api/v1/projects/<proyecto>/folders`. La operación `moveToFolder` existe (n8n 2.32+), así que **si algún día se crea
una clave con esos scopes, esto se puede automatizar** — hoy no.

**Verificación:** el API de n8n **no puede informar en qué carpeta está un flujo** (solo cuenta contenidos). La
comprobación es visual: cada carpeta debe mostrar **12 · 15 · 2 · 28** (con los 5 ajenos dentro de `99 · Retirados`).
La lista de abajo sirve para ir tachando.

---

## Paso 1 — Crear las carpetas

Dentro de la carpeta del proyecto `Servicios_Información_Cotizaciones_v2.0` (ya existe), crea cuatro:

- [ ] `01 · Pipeline CCB`
- [ ] `02 · Subflujos CCB`
- [ ] `03 · Operativos CCB`
- [ ] `99 · Retirados`

> La numeración es lo que las ordena alfabéticamente en el orden en que se usan. Si prefieres menos carpetas, con dos
> (`01 · Pipeline CCB` y `02 · Interno CCB`) ya queda ordenado, porque los prefijos `[SUB]` y `[OPS]` agrupan dentro.

## Paso 2 — Arrastrar los 52 flujos

### `01 · Pipeline CCB` — 12

- [ ] CCB · W1 — Extracción de información del cliente
- [ ] CCB · W2A — Guardar criterios y cotizar
- [ ] CCB · W2C — Recepción del formulario externo
- [ ] CCB · W3 — Motor de criterios y precio
- [ ] CCB · W4A — Router de aprobación
- [ ] CCB · W4B — Aprobación por Teams
- [ ] CCB · W4C — Consultar la propuesta para revisión
- [ ] CCB · W4D — Procesar la decisión
- [ ] CCB · W5A — Router de envío
- [ ] CCB · W5B — Envío al cliente
- [ ] CCB · W6 — Finalizador de cotizaciones
- [ ] CCB · Catch-all — Errores no capturados

### `02 · Subflujos CCB` — 15

- [ ] [SUB] CCB · Config — Leer la configuración
- [ ] [SUB] CCB · Contexto — Leer el contexto de la propuesta
- [ ] [SUB] CCB · Envío — Cerrar el envío
- [ ] [SUB] CCB · Envío — Cerrar el error de envío
- [ ] [SUB] CCB · Envío — Enviar al cliente
- [ ] [SUB] CCB · Error — Registrar y alertar
- [ ] [SUB] CCB · Motor — Invocar el motor y guardar
- [ ] [SUB] CCB · PDF — Generar el PDF
- [ ] [SUB] CCB · Regresión — Preparar filas
- [ ] [SUB] CCB · Regresión — Verificar y limpiar
- [ ] [SUB] CCB · W4D — Aprobar
- [ ] [SUB] CCB · W4D — Cancelar
- [ ] [SUB] CCB · W4D — Cierre de la corrección
- [ ] [SUB] CCB · W4D — Corrección con IA
- [ ] [SUB] CCB · W4D — Revisión manual

### `03 · Operativos CCB` — 2

- [ ] [OPS] CCB · Monitoreo — Métricas del pipeline
- [ ] [OPS] CCB · Regresión — Prueba de regresión

### `99 · Retirados` — 23

El retirado del proyecto y las 22 versiones anteriores del pipeline (historia; se conservan):

- [ ] [RETIRADO] CCB · W2B — Formulario antiguo
- [ ] CCB - Criterios y Precio
- [ ] CCB - Error Handler (Propuestas v3)
- [ ] CCB - Error Workflow (Catch-all Alertas Técnicas)
- [ ] CCB - Fase 1 - Trigger y Validacion Email *(copia de 27 nodos)* · id `ektDPgkxk6TzyiuN`
- [ ] CCB - Fase 1 - Trigger y Validacion Email *(copia de 19 nodos)* · id `I3CPjETbgjoIoD9c`
- [ ] CCB - Fase 2
- [ ] CCB - Fase 2 - Generacion Propuesta
- [ ] CCB - Fase 2 - Generacion Propuesta Prueba
- [ ] CCB - Sub Aprobación de Propuesta (Teams)
- [ ] CCB - Workflow #1 -  Intake
- [ ] CCB - Workflow #2 - Generación Propuesta
- [ ] CCB - Workflow #3 - Notificación y Aprobación (Router)
- [ ] CCB - Workflow 1 - Extracción información del cliente copy
- [ ] CCB Propuestas - Generación y Revisión
- [ ] CCB Propuestas v3 (PDF) - Email Intake
- [ ] CCB_PropuestasComerciales *(copia de 71 nodos)* · id `op8kdJREsljR0jNv`
- [ ] CCB_PropuestasComerciales *(copia de 70 nodos)* · id `iVNgsGVbfEG4HWla` *(esta fue la que quedó sin mover el
  24/09 y se movió el 28/09)*
- [ ] CCB_Propuestas_v2
- [ ] CCB_Propuestas_v2_Bootstrap_W1
- [ ] CCB_Propuestas_v2_Bootstrap_W2
- [ ] CCB_Propuestas_v2_Bootstrap_W3
- [ ] CCB_Propuestas_v2_StaticDataTest

## No mover — no son del proyecto (5)

La instancia es organizacional y estos parecen de otra área. Si están dentro de la carpeta del proyecto, conviene
sacarlos, pero **decidirlo contigo**, no borrarlos:

- CamaraBAQ - Emails leads sin agendar y no asistió
- Chatbot - Consultorio IA
- My workflow 16 - Envío correos HTML
- My workflow 19
- RSS IA → Google Sheets

## Paso 3 — Comprobar

- [ ] `01 · Pipeline CCB` muestra **12** flujos
- [ ] `02 · Subflujos CCB` muestra **15**
- [ ] `03 · Operativos CCB` muestra **2**
- [ ] `99 · Retirados` muestra **23**
- [ ] La lista general ya no mezcla el pipeline con la historia

## Notas

- **Mover un flujo a una carpeta no cambia su ID ni sus webhooks**, así que las dos páginas (formulario y revisión) y los
  tres endpoints públicos siguen funcionando igual.
- **Los 5 ajenos no se borran**: ya se limpió lo que era basura clara en su momento (`My workflow 20`, `My workflow 17` y
  `TEST_STATE_2TPL`, con respaldo en `/tmp/n8n-backup/legado-2026-09-24/`).
- **Los 22 de historia no tienen copia en el repo** (el snapshot solo exporta los 30 del proyecto). Su única copia es
  `/tmp/n8n-backup/legado-2026-09-24/`, que es efímera: no los borres sin archivarlos antes en un sitio durable.
