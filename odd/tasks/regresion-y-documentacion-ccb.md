# Feature: cerrar la brecha al umbral de 90 y documentar el flujo completo

**Creada:** 2026-09-23 · **Origen:** [re-auditoría del 23/09](../../docs/AUDITORIA_BUENAS_PRACTICAS_2026-09-23.md) (87,7/100)
y la petición del usuario de *"seguir con los pendientes para cumplir con el puntaje de la auditoría, y documentar todo el flujo"*.

## Objetivo

Cerrar la brecha de **2,3 puntos** que separa al pipeline del umbral de **90/100** del framework, concentrada en
**Testing (11,7/15)** y en dos puntos de **Observabilidad** y **Seguridad**; y dejar el pipeline **documentado de punta a
punta**, incluyendo el recorrido de negocio completo, no solo la ficha por flujo.

## Alcance

- **Dentro:** los workflows de la instancia viva, sus datos de prueba, el repo `ccb-workflows-git` (snapshot, docs) y la
  memoria de proyecto.
- **Fuera:** la poda de ejecuciones a nivel de instancia, el cierre de `/metrics` y los tokens de los front-ends
  (dependen de Tecnología); la creación de la credencial *Header Auth* en la UI y el clic de rechazo en Teams (dependen
  del usuario); la carpeta `Servicios_Información_Cotizaciones_v2.0` (bloqueada por permisos del API).

## Criterio de cierre

1. Cada tarea con **evidencia de ejecución real** (id de ejecución, filas, correo) registrada en este archivo.
2. Re-auditoría final publicada con el puntaje nuevo (objetivo: **≥90** o la explicación exacta de lo que falta).
3. `docs/FLUJO_COMPLETO_PIPELINE_CCB.md` publicado y enlazado desde el README.
4. Un commit por unidad de trabajo y snapshot re-exportado.

---

## Tareas

| # | Tarea | Criterio de aceptación | Estado |
|---|---|---|---|
| **R1** | Restaurar el `httpMethod: GET` explícito en el webhook de W4C | El snapshot muestra el método y la consulta desde la página sigue respondiendo 200 | ☐ pendiente |
| **R2** | Verificar con tráfico real la ruta de error compartida (`[SUB] CCB - Registrar y Alertar Error`) | Una ejecución real que falle deja fila en `Errores_CCB` con `error_timestamp` y mensaje enmascarado, envía el correo de alerta y **no corta** el flujo que la invoca | ☐ pendiente |
| **R3** | Construir `[OPS] CCB - Regresión del pipeline` | El flujo corre los caminos críticos con filas descartables, publica un semáforo por camino, borra sus filas y reporta por correo | ☐ pendiente |
| **R4** | Probar la rama de **rechazo/expiración** de la aprobación de IA (F7-03) | Rechazo real en Teams → motivo `aprobacion_rechazada`, revisión manual y **sin consumir ronda** | ☐ pendiente (requiere un clic del usuario) |
| **R5** | Documentar el flujo completo | `docs/FLUJO_COMPLETO_PIPELINE_CCB.md`: el recorrido de negocio de punta a punta (quién interviene, qué ve, qué pasa en cada rama) + el mapa técnico de los 26 flujos y las 6 tablas; un lector nuevo puede seguirlo sin abrir n8n | ☐ pendiente |
| **R6** | Limpiar la fila basura de `Cotizaciones_CCB` (`id 21`) | Borrada con `dryRun` previo y confirmación del usuario; la tabla queda sin filas nulas | ☐ pendiente (requiere confirmación) |
| **R7** | Re-auditoría final | Puntaje nuevo publicado con la evidencia de R1–R5 | ☐ pendiente |
| **R8** | Sincronizar entrega | Snapshot, README, tablero, estado y memoria al día; un commit por unidad de trabajo | ☐ pendiente |

**Orden de ejecución:** R1 (rápido) → R2 → R3 → R5 → R4 y R6 (cuando el usuario pueda) → R7 → R8.

## Notas de ejecución

- Se aplica el [flujo de trabajo de testing](../../docs/TESTING_PIPELINE_CCB.md): validación estructural, lógica aislada,
  subflujo aislado, integración con filas `SOL-PRUEBA-*` y, cuando se puede, tráfico real.
- **Nada se da por bueno sin ejecución real.**
- Los valores reales de anonimización viven en `scripts/anonymization.local.json` (git-ignored), nunca en los workflows.
- Las filas de prueba se borran con `n8n_manage_datatable` (`deleteRows`, con `dryRun` primero): el API público no
  permite borrar filas.

## Evidencia

_(se completa al cerrar cada tarea: id de ejecución, filas afectadas, correo recibido y commit)_
