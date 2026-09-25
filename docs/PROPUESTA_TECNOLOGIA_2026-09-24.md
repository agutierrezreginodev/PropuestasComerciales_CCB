# Propuesta a Tecnología — endurecimiento de la instancia n8n del pipeline CCB

**Para:** Tecnología (Infraestructura y Plataforma)
**De:** equipo del proyecto CCB — Servicios de Información (Cámara de Comercio de Barranquilla)
**Fecha:** 24 de septiembre de 2026
**Instancia:** `automatizacion.camarabaq.org.co` (n8n autohospedado)

---

## 1. Qué pedimos, en una línea

**Cuatro cambios acotados sobre la instancia**, dos de ellos de pocos minutos y de configuración pura, con un
objetivo doble: cerrar los últimos tres hallazgos de la auditoría de buenas prácticas del proyecto, y quitar el punto
más frágil de la operación actual.

Ninguno requiere tocar la lógica de los flujos, las credenciales ni los webhooks.

---

## 2. Contexto

- El pipeline CCB (29 flujos activos dentro de nuestro alcance) automatiza la venta de servicios de información: desde
  el lead hasta la propuesta enviada, aprobada o cerrada.
- Lo evaluamos contra la rúbrica *Arquitectura e Ingeniería de Automatización en n8n*: hoy está en **89,8/100**. El
  umbral de producción crítica es **90**, y **todo lo que depende de los flujos ya está hecho**: los puntos que
  faltan son de instancia.
- **La instancia es compartida.** Su propio contador reporta **84 flujos activos**, mientras nuestro proyecto ve 29.
  Eso significa que dos de los pedidos (P1 y P2) **benefician a toda la instancia**, no solo a este proyecto.

---

## 3. Los pedidos

### P1 — Poda de ejecuciones · ~5 minutos · el que más aporta

**Qué pedimos:** revisar y dejar **explícita** la poda de ejecuciones de la instancia.

| Variable | Valor que pedimos |
|---|---|
| `EXECUTIONS_DATA_PRUNE` | `true` |
| `EXECUTIONS_DATA_MAX_AGE` | `336` (14 días, el valor por defecto de n8n) — o `720` (30 días) si prefieren más historial |
| `EXECUTIONS_DATA_PRUNE_MAX_COUNT` | `10000` (por defecto), o `0` sin límite si prefieren que mande solo la edad |

**Por qué.** n8n documenta que la poda *"borra las ejecuciones terminadas junto con sus datos de ejecución y datos
binarios en un ciclo regular"*, y que por rendimiento primero **marca** los objetivos y después los elimina. Cada
ejecución guarda el detalle nodo por nodo: sin poda, eso crece sin techo.

**Dato medido hoy:** el registro de ejecuciones llega hasta el **26 de junio — 89 días de antigüedad**. Con el valor
por defecto (336 horas = 14 días) no debería quedar nada de más de dos semanas, así que **la poda no está aplicando el
valor por defecto** en esta instancia.

**Cómo lo verificamos nosotros:** consultamos por API la ejecución más antigua; debería pasar a ~14 (o 30) días.

---

### P2 — Restringir `/metrics` · ~15 minutos

**Qué pedimos:** dejar de servir `/metrics` en internet abierto. Exponerlo **solo a la red interna** (regla en el proxy
inverso o en el firewall, o escuchando en una interfaz interna).

**Por qué.** Hoy ese endpoint responde **200 sin autenticación** desde internet y devuelve 25,9 KB con **42–43 familias de
métricas** del proceso: rol de la instancia, handles activos, lag del event loop, contadores de ejecuciones, cantidad
de flujos activos. No hay datos de clientes, pero es información operativa de la instancia completa.

*Remedido el **25/09** — el pedido sigue vigente:* `GET /metrics` desde internet responde **200**, **25.902 bytes** y
**42 familias**, sin credencial alguna. En la misma fecha, `GET /healthz` → **200**: la instancia está viva y alcanzable,
así que no se trata de un servicio caído.

Las instrucciones oficiales de n8n son explícitas:

> **No exponga públicamente el endpoint de métricas.** Exponga `/metrics` únicamente a servicios internos que consumen
> los datos de Prometheus. No lo haga accesible desde internet público, ya que puede revelar datos operativos
> sensibles de su instancia.
> — *Enable Prometheus metrics*, documentación de n8n

**A tener en cuenta (y no es un obstáculo):** el flujo `[OPS] CCB · Monitoreo` lee `/metrics` para publicar cuatro
métricas. Con la restricción debe seguir alcanzándolo **desde dentro de la red**. El flujo **no necesita ningún
cambio de código**: la URL del endpoint es un valor de configuración en una tabla de datos
(`Configuracion_CCB.metricas_url`), así que basta con que la nueva dirección interna sea alcanzable desde n8n.

**Cómo lo verificamos nosotros:** un GET desde internet debe devolver 403/404, y el monitor debe seguir publicando sus
cuatro métricas.

---

### P3 — Alojar el microservicio de PDF · el más grande, y el más valioso

**Qué es.** `microservicio-propuestas`: un servicio Node (Express + Puppeteer) que convierte el HTML de la propuesta en
PDF y lo persiste en `/pdfs/{id_solicitud}.pdf`. Hoy corre en una **máquina local detrás de un túnel ngrok**.

**Qué pedimos:** desplegarlo como **contenedor** en la infraestructura de la organización, con una **URL estable**.

- El repositorio **ya trae `Dockerfile`**; no hay que escribirlo.
- Requiere Chromium (Puppeteer), que el propio Dockerfile contempla.
- Persiste los PDFs en disco: conviene montar un volumen si quieren conservar el historial.

**Por qué.** **Hoy el servicio estuvo caído** y toda generación de propuesta falló en el paso del PDF. Nuestra propia
auditoría lo declara *"el punto más frágil de producción"*, y con razón: la continuidad del negocio depende de que una
máquina esté encendida, de que el proceso siga vivo **y** de que el túnel esté arriba. Con una URL estable y un
contenedor supervisado, esa cadena de dependencias desaparece.

**Cómo lo verificamos nosotros:** generamos un PDF real de punta a punta y comprobamos que queda servible en
`/pdfs/{id_solicitud}.pdf`.

---

### P4 — *(opcional)* Habilitar el MCP de instancia · ~2 minutos · requiere dueño o admin

**Qué pedimos:** en `Settings → Instance-level MCP`, activar el acceso MCP y generar el token de acceso.

**Por qué.** Nos permite **disparar y verificar los flujos por API**, sin depender de que una persona entre a la UI y
ejecute el flujo a mano. Hoy cada verificación de la regresión del pipeline exige ese clic manual.

**No cambia el comportamiento del producto**: es capacidad operativa del equipo, y el acceso queda acotado a lo que ya
podemos ver y hacer en la instancia.

---

## 4. Lo que NO pedimos

- **No** pedimos cambios en la lógica de ningún flujo, ni en credenciales, ni en los webhooks públicos.
- **No** pedimos servidores, licencias ni servicios nuevos. P1 y P2 son configuración sobre lo que ya existe; P3
  reutiliza el `Dockerfile` que ya está en el repositorio.
- **No** pedimos acceso a datos ni flujos de otras áreas. Todo lo que tocamos vive en nuestro proyecto.

---

## 5. Orden recomendado y esfuerzo

| | Esfuerzo | Qué cierra | Beneficia a |
|---|---|---|---|
| **P1** poda de ejecuciones | ~5 min | El último punto de **Observabilidad** (+0,3) | toda la instancia |
| **P2** restringir `/metrics` | ~15 min | El último punto de **Seguridad** (+0,2) | toda la instancia |
| **P3** alojar el microservicio | ~1–2 h | El punto más frágil de producción | el pipeline CCB |
| **P4** MCP de instancia | ~2 min | Verificación automática, sin clics | el equipo del proyecto |

**Con P1 y P2 el proyecto pasa de 89,8 a 90,3** y cumple el umbral de producción crítica del framework.

---

## 6. Verificación: toda de nuestro lado

No les pedimos que verifiquen nada. **Cada pedido es de caja cerrada** y lo comprobamos nosotros, reportando:

| Pedido | Nuestra comprobación |
|---|---|
| P1 | Antigüedad de la ejecución más antigua, por API |
| P2 | Código HTTP de `/metrics` desde internet + el monitor publicando sus 4 métricas |
| P3 | Un PDF real generado y servible en `/pdfs/{id}.pdf` |
| P4 | Una corrida de la regresión disparada por API, con su resultado |

---

## 7. Si algo no es viable

Preferimos un "no" explicado a un silencio:

- Si **P1 o P2** no se pueden aplicar, dígannos la restricción y proponemos la alternativa (por ejemplo, una regla de
  red más específica o un valor de poda distinto).
- Si **P3** no se puede alojar, evaluamos dejar el microservicio como servicio supervisado en la máquina actual —con
  arranque automático— y lo documentamos como **riesgo aceptado**, no como pendiente olvidado.
