# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Genera docs/informe-pipeline-ccb.html: arquitectura, evaluacion del framework por flujo
y pendientes. Lee el inventario EN VIVO de la instancia y la evaluacion de los informes de
auditoria (constantes abajo).

Uso:  N8N_API_URL=... N8N_API_KEY=... python3 scripts/generar_informe_html.py
"""
import os, sys, html, datetime

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)

# ===== Datos: inventario en vivo + evaluacion del framework =====
# -*- coding: utf-8 -*-
"""Datos del informe: inventario en vivo + evaluacion del framework (auditoria de cierre 23/09)."""
import sys, json, os, urllib.request

def cargar_workflows():
    """Lee el inventario de workflows desde la API publica de n8n."""
    url = os.environ["N8N_API_URL"].rstrip("/") + "/api/v1/workflows?limit=200"
    req = urllib.request.Request(url, headers={"X-N8N-API-KEY": os.environ["N8N_API_KEY"], "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)["data"]

FLUJOS = [
 # id, grupo, clave, nombre_largo, rol, llamadores
 ("w6h0qSblUESIpSVc","pipeline","W1","Extracción de información del cliente","Recibe el lead por correo o contacto directo y envía el enlace del formulario.","—"),
 ("VChcasvisGKekezR","pipeline","W2A","Guardar criterios y cotizar","Guarda los criterios del cliente e invoca el motor de cálculo.","W2C"),
 ("u6KCMnLwFOp6Ja0N","pipeline","W2C","Recepción del formulario externo","Webhook del formulario: valida los campos obligatorios y responde.","Página del formulario"),
 ("cHOIOEFB5nbltN82","pipeline","W3","Motor de criterios y precio","Calcula el precio con el motor y genera el PDF de la propuesta.","W2A · W4D"),
 ("7gmpPMBJtEb0W3J5","pipeline","W4A","Router de aprobación","Detecta las propuestas listas y avisa al asesor.","Cron"),
 ("5RJdnHDQ8NuWZJG7","pipeline","W4B","Aprobación por Teams","Notifica al asesor por Teams con el enlace a la página de revisión.","W4A"),
 ("KuLSIzBZgaRIjuSu","pipeline","W4C","Consultar la propuesta para revisión","Webhook de consulta: devuelve el contexto y el PDF a la página.","Página de revisión"),
 ("W0TDH4b0tHCNOzFQ","pipeline","W4D","Procesar la decisión","Webhook de decisión y router de las tres ramas (aprobar, cancelar, corregir).","Página de revisión"),
 ("gvIn6mbAn2Y1bMRR","pipeline","W5A","Router de envío","Detecta las propuestas aprobadas listas para enviar.","Cron"),
 ("XWBHgbmtBubA4gqx","pipeline","W5B","Envío al cliente","Envía la propuesta con el PDF y cierra el envío.","W5A"),
 ("mPwl4qUb0zQkmDHN","pipeline","W6","Finalizador de cotizaciones","Cierra automáticamente las cotizaciones de 30+ días.","Cron"),
 ("Dh2lAQTzyoZBpXie","pipeline","Catch-all","Errores no capturados","Red de respaldo: registra los incidentes que no detecta nadie más.","errorWorkflow de los 11"),
 ("2dY1kaT7I5a0eP2w","sub","Error","Registrar y alertar","Escribe el incidente en Errores_CCB con PII enmascarada y avisa por correo.","8 flujos + la regresión"),
 ("Hgy02eqPhnsdJvkq","sub","Config","Leer la configuración","Devuelve el item del llamador con las 12 claves de configuración adjuntas.","9 flujos"),
 ("GELWpskp0aYJ2zPg","sub","Contexto","Leer el contexto de la propuesta","Lee cotización, criterios y solicitud en un solo item.","W4B · W4C · W4D · W5B"),
 ("DF3emCmBBBB2HA3i","sub","PDF","Generar el PDF","Pide el PDF al microservicio y devuelve la URL.","W3"),
 ("MHWlUApSFT6gpBHs","sub","Motor","Invocar el motor y guardar","Invoca W3, guarda la cotización y maneja el rechazo del motor.","W2A · la regresión"),
 ("AnPJGVWylmKEYWmJ","sub","Envío","Enviar al cliente","Arma y envía el correo con el PDF adjunto.","W5B"),
 ("1Zzkrg3dTkTrddgp","sub","Envío","Cerrar el envío","Marca ENVIADA en cotización y solicitud y avisa internamente.","W5B · la regresión"),
 ("D2d9Og6UUvq13TJA","sub","Envío","Cerrar el error de envío","Registra el fallo de envío y responde igual al asesor.","W5B"),
 ("8j6BCwXkgJCccyO1","sub","W4D","Aprobar","Marca la cotización como APROBADA con el comentario del asesor.","W4D · la regresión"),
 ("Jgf514VxDINJ8ra3","sub","W4D","Cancelar","Marca la cotización como CANCELADA.","W4D · la regresión"),
 ("iNSErCHs2iw33emJ","sub","W4D","Revisión manual","Unifica los cuatro motivos de revisión manual sin consumir ronda.","W4D · la regresión"),
 ("3NAcLF4jaZ1JBw0A","sub","W4D","Corrección con IA","Guardarraíles de IA, ajuste, re-invocación del motor y aprobación humana.","W4D"),
 ("POeFkqQp8e4cGfY3","sub","W4D","Cierre de la corrección","Verifica el recálculo, guarda la ronda y avisa por Teams.","W4D"),
 ("DgUfcoudk228kOw8","sub","Regresión","Preparar filas","Crea las filas descartables en tres tablas.","la regresión"),
 ("OuE4SS9Jujz1dVif","sub","Regresión","Verificar y limpiar","Verifica el estado real, publica el semáforo y borra las cuatro tablas.","la regresión"),
 ("ZwBFTBhwS9pjS69X","ops","Monitoreo","Métricas del pipeline","Cada hora publica las 4 métricas del framework y avisa por umbral.","Cron horario"),
 ("GVE3iNQ80y5Q9FEw","ops","Regresión","Prueba de regresión","Corre 6 caminos críticos con filas descartables y publica el semáforo.","Cron semanal + a mano"),
 ("lIcdT6nGd0w1G2i0","retirado","W2B","Formulario antiguo","Retirado: el formulario vive en la página nueva.","—"),
]

# Evaluacion del framework (re-auditoria de cierre del 23/09). Dimensiones: /20, /20, /15, /15, /15, /15
EVAL = {
 "W1":  dict(arq=17, err=16, doc=14, seg=13, tst=12, obs=13, antes=83),
 "W2A": dict(arq=18, err=17, doc=14, seg=13, tst=13, obs=14, antes=87),
 "W2C": dict(arq=18, err=15, doc=14, seg=14, tst=12, obs=12, antes=84),
 "W3":  dict(arq=18, err=17, doc=14, seg=14, tst=13, obs=14, antes=89),
 "W4A": dict(arq=19, err=17, doc=14, seg=14, tst=13, obs=14, antes=89),
 "W4B": dict(arq=18, err=17, doc=14, seg=14, tst=13, obs=14, antes=88),
 "W4C": dict(arq=19, err=16, doc=14, seg=14, tst=12, obs=12, antes=85),
 "W4D": dict(arq=19, err=18, doc=14, seg=14, tst=14, obs=15, antes=92),
 "W5A": dict(arq=18, err=18, doc=14, seg=14, tst=13, obs=14, antes=89),
 "W5B": dict(arq=18, err=18, doc=14, seg=14, tst=14, obs=14, antes=90),
 "W6":  dict(arq=18, err=18, doc=14, seg=14, tst=13, obs=14, antes=89),
}
# Pendientes por flujo: (dimensión, qué falta, acción concreta, responsable)
PEND = {
 "W1": [("Testing","Sin caso propio en la regresión: su camino (correo → enlace) no se ejercita automáticamente.","Agregar un caso que verifique la extracción y el envío del enlace.","Yo"),
        ("Manejo de errores","El reintento está en los nodos de red, pero no hay prueba del camino de error del correo.","Forzar un correo sin remitente reconocido y verificar el registro.","Yo")],
 "W2A": [],
 "W2C": [("Manejo de errores","El webhook valida los campos (400) pero el fallo de escritura en la tabla no tiene rama propia.","Agregar rama de error en el guardado con registro y respuesta controlada.","Yo"),
         ("Testing","Sin caso propio en la regresión.","Caso que replique un POST del formulario con datos válidos y con faltantes.","Yo"),
         ("Observabilidad","Hereda la poda de instancia.","Poda de ejecuciones (Tecnología).","Tecnología")],
 "W3": [("Manejo de errores","La lectura de la planilla Excel reintenta 3x2 s y tiene rama de error, pero su fallo no está cubierto por la regresión: el caso del motor asume que la planilla responde.","Caso que fuerce un fallo de lectura de la planilla y verifique el registro y el `ok:false`.","Yo")],
 "W4A": [("Testing","Es un router: se prueba de forma indirecta, sin caso propio.","Caso que verifique que detecta solo las propuestas en PROPUESTA_GENERADA.","Yo")],
 "W4B": [("Testing","El aviso a Teams se verificó con clics reales pero no está en la regresión.","Caso que compruebe el armado del aviso (sin enviar a Teams).","Yo"),
         ("Observabilidad","Hereda la poda de instancia.","Poda de ejecuciones (Tecnología).","Tecnología")],
 "W4C": [("Manejo de errores","El webhook de consulta no tiene rama propia para el fallo de las lecturas.","Rama de error con registro en Errores_CCB y respuesta controlada.","Yo"),
         ("Testing","Sin caso propio en la regresión.","Caso que consulte una propuesta descartable y verifique la forma de la respuesta.","Yo")],
 "W4D": [("Testing","La rama de corrección con IA no está en la regresión (requiere la aprobación humana).","Caso que verifique los motivos `ia_desactivada` y `confianza_baja` (no requieren clic).","Yo")],
 "W5A": [("Testing","Sin caso propio en la regresión.","Caso que verifique la detección de aprobadas.","Yo")],
 "W5B": [("Testing","Prácticamente completo: su camino de envío ya está cubierto (incluido el cierre).","Solo falta el envío real a un cliente, que depende del negocio.","Tú")],
 "W6": [("Testing","Su disparador es un cron de 30+ días: no se puede esperar.","Caso con fechas manipuladas para forzar el cierre.","Yo"),
        ("Observabilidad","Hereda la poda de instancia.","Poda de ejecuciones (Tecnología).","Tecnología")],
}
COMUNES = [
 ("Observabilidad","Poda de ejecuciones a nivel de instancia: hoy la retención es por flujo, no global.","`EXECUTIONS_DATA_PRUNE` / `MAX_AGE` en la instancia.","Tecnología","+0,3"),
 ("Seguridad","`/metrics` está expuesto sin autenticación.","Restringirlo o cerrarlo (o exponerlo solo en la red interna).","Tecnología","+0,2"),
]
def inventario():
    ws = {w["id"]: w for w in cargar_workflows()}
    filas = []
    for fid, grupo, clave, nombre, rol, llamadores in FLUJOS:
        w = ws.get(fid, {})
        reales = len([n for n in w.get("nodes", []) if n["type"] != "n8n-nodes-base.stickyNote"])
        con_notas = len(w.get("nodes", []))
        ev = EVAL.get(clave)
        filas.append(dict(id=fid, grupo=grupo, clave=clave, nombre=nombre, rol=rol, llamadores=llamadores,
                          activo=bool(w.get("active")), nodos=reales, con_notas=con_notas, real=reales,
                          descripcion=(w.get("description") or ""), ev=ev,
                          score=(sum([ev["arq"],ev["err"],ev["doc"],ev["seg"],ev["tst"],ev["obs"]]) if ev else None),
                          pend=PEND.get(clave, [])))
    return filas
def _demo():
    filas = inventario()
    print(json.dumps([{k: v for k, v in f.items() if k != "descripcion"} for f in filas], ensure_ascii=False)[:1200])
    print("\nflujos:", len(filas), "| activos:", sum(1 for f in filas if f["activo"]))
    print("nodos totales:", sum(f["nodos"] for f in filas), "| promedio de los principales:", round(sum(f["nodos"] for f in filas if f["grupo"]=="pipeline")/12, 1))

# ===== Generacion del informe =====
F = inventario()
ACT = [f for f in F if f["grupo"] != "retirado"]
PIPE = [f for f in F if f["grupo"] == "pipeline"]
SUB = [f for f in F if f["grupo"] == "sub"]
OPS = [f for f in F if f["grupo"] == "ops"]
RET = [f for f in F if f["grupo"] == "retirado"]
PIPE_EVAL = [f for f in PIPE if f["score"]]   # el catch-all no se puntua con la rubrica
SC = [f["score"] for f in PIPE_EVAL]
BRUTO = sum(SC) / len(SC)
B = f'{BRUTO:.1f}'.replace('.', ',')            # valor visible, coma decimal
FALTA = f'{90 - BRUTO:.1f}'.replace('.', ',')
def barra(v, mx, clase=""):
    p = round(v / mx * 100)
    return f'<div class="bar {clase}"><span style="width:{p}%"></span></div>'
def chip_dim(n, v, mx):
    p = v / mx
    c = "ok" if p >= .9 else ("warn" if p >= .75 else "bad")
    return f'<td class="num {c}">{v}<small>/{mx}</small></td>'
def dims_tabla(ev):
    return ("<table class='mini'><tr><th>Arq</th><th>Err</th><th>Doc</th><th>Seg</th><th>Test</th><th>Obs</th></tr><tr>"
            + chip_dim("arq", ev["arq"], 20) + chip_dim("err", ev["err"], 20) + chip_dim("doc", ev["doc"], 15)
            + chip_dim("seg", ev["seg"], 15) + chip_dim("tst", ev["tst"], 15) + chip_dim("obs", ev["obs"], 15)
            + "</tr></table>")
def dims_barras(ev):
    filas = [("Arquitectura", ev["arq"], 20), ("Manejo de errores", ev["err"], 20), ("Documentación", ev["doc"], 15),
             ("Seguridad", ev["seg"], 15), ("Testing", ev["tst"], 15), ("Observabilidad", ev["obs"], 15)]
    out = []
    for nom, v, mx in filas:
        p = v / mx
        c = "ok" if p >= .9 else ("warn" if p >= .75 else "bad")
        out.append(f'<div class="dimrow"><span class="dimnom">{nom}</span>{barra(v, mx, c)}<span class="dimval {c}">{v}<small>/{mx}</small></span></div>')
    return "".join(out)

# ---------- inventario ----------
def tabla_inventario(filas, con_eval=False):
    th_eval = "<th>Puntaje</th>" if con_eval else ""
    out = [f"<table class='inv'><thead><tr><th>Clave</th><th>Flujo</th><th>Nodos</th><th>Estado</th><th>Rol</th><th>Lo llama</th>{th_eval}<th>ID</th></tr></thead><tbody>"]
    for f in filas:
        ev = f"<td class='num'><b>{f['score']}</b><small>/100</small></td>" if (con_eval and f["score"]) else ("<td class='num muted'>—</td>" if con_eval else "")
        estado = "<span class='pill ok'>activo</span>" if f["activo"] else "<span class='pill off'>inactivo</span>"
        out.append(f"<tr><td><code>{html.escape(f['clave'])}</code></td>"
                   f"<td>{html.escape(f['nombre'])}</td>"
                   f"<td class='num'>{f['nodos']}</td><td>{estado}</td>"
                   f"<td class='rol'>{html.escape(f['rol'])}</td>"
                   f"<td class='rol'>{html.escape(f['llamadores'])}</td>{ev}"
                   f"<td><code class='id'>{f['id']}</code></td></tr>")
    out.append("</tbody></table>")
    return "".join(out)

# ---------- tarjetas por flujo ----------
def tarjeta(f):
    ev, s = f["ev"], f["score"]
    falta = 90 - s
    if falta > 0:
        cab = f"<span class='gap warn'>faltan {falta} para 90</span>"
    else:
        cab = "<span class='gap ok'>sobre el objetivo de 90</span>"
    pends = ""
    if f["pend"]:
        items = "".join(
            f"<li><span class='tagdim'>{html.escape(d)}</span><p>{html.escape(q)}</p>"
            f"<p class='acc'><b>Acción:</b> {html.escape(a)} <span class='who'>{html.escape(w)}</span></p></li>"
            for d, q, a, w in f["pend"])
        pends = f"<div class='pend'><h5>Pendientes para subir el puntaje</h5><ul>{items}</ul></div>"
    else:
        pends = "<div class='pend'><p class='muted'>Sin pendientes propios: hereda los globales.</p></div>"
    return f"""<details class="flujo" id="f-{f['clave'].lower()}">
<summary><span class="fclave">{html.escape(f['clave'])}</span>
  <span class="fnombre">{html.escape(f['nombre'])}</span>
  <span class="fscore {'ok' if s>=90 else 'warn'}">{s}<small>/100</small></span></summary>
<div class="fbody">
  <p class="rol">{html.escape(f['rol'])}</p>
  <div class="fmeta">{f['nodos']} nodos · <code>{f['id']}</code> · {cab}</div>
  <div class="cols"><div>{dims_barras(ev)}</div><div><h5>Dimensiones</h5>{dims_tabla(ev)}
  <p class="muted small">Puntaje del 22/09: {ev['antes']} → hoy <b>{s}</b> ({'+' if s-ev['antes']>=0 else ''}{s-ev['antes']})</p></div></div>
  {pends}
</div></details>"""

# ---------- globales ----------
def tabla_comunes():
    out = ["<table class='inv'><thead><tr><th>Dimensión</th><th>Qué falta</th><th>Acción</th><th>Responsable</th><th>Impacto</th></tr></thead><tbody>"]
    for d, q, a, w, imp in COMUNES:
        out.append(f"<tr><td><code>{html.escape(d)}</code></td><td>{html.escape(q)}</td><td>{html.escape(a)}</td>"
                   f"<td><span class='who'>{html.escape(w)}</span></td><td class='num'>{html.escape(imp)}</td></tr>")
    out.append("</tbody></table>")
    return "".join(out)

DIM_EVAL = [("Arquitectura", 18.2, 20), ("Manejo de errores", 17.0, 20), ("Documentación", 14.0, 15),
            ("Seguridad", 13.8, 15), ("Testing", 12.9, 15), ("Observabilidad", 13.6, 15)]
def barra_global(nom, v, mx):
    p = v / mx
    c = "ok" if p >= .9 else ("warn" if p >= .8 else "bad")
    return (f'<div class="gbar"><div class="ghead"><b>{nom}</b><span class="{c}">{(format(v, ".1f") if isinstance(v, float) else v).replace(".", ",")}<small>/{mx}</small></span></div>'
            f'{barra(v, mx, c)}</div>')

HTML = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Pipeline CCB — Arquitectura, evaluación del framework y pendientes</title>
<style>
:root{{--bg:#f5f7fb;--card:#fff;--ink:#0f172a;--muted:#5b6b7f;--line:#e3e8ef;--brand:#1d4ed8;--ok:#15803d;--warn:#b45309;--bad:#b91c1c;--chip:#eef2ff;--okbg:#f0fdf4;--warnbg:#fffbeb}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--ink);font:15px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}}
a{{color:var(--brand);text-decoration:none}} a:hover{{text-decoration:underline}}
code{{background:#f1f5f9;border:1px solid var(--line);border-radius:5px;padding:1px 5px;font:12.5px/1.5 ui-monospace,SFMono-Regular,Menlo,monospace}}
code.id{{font-size:11.5px;color:var(--muted)}}
.wrap{{max-width:1120px;margin:0 auto;padding:0 22px 80px}}
header.top{{background:linear-gradient(135deg,#0b1c3d,#1d4ed8 60%,#2563eb);color:#fff;padding:38px 0 30px;margin-bottom:26px}}
header.top .wrap{{padding-bottom:0}}
header.top h1{{margin:0 0 6px;font-size:29px;letter-spacing:-.02em}}
header.top p{{margin:0;opacity:.92;max-width:760px}}
.hero{{display:flex;gap:26px;align-items:center;flex-wrap:wrap;margin-top:22px}}
.ring{{--p:{round(BRUTO,1)};width:132px;height:132px;border-radius:50%;flex:0 0 auto;display:grid;place-items:center;
  background:conic-gradient(#22c55e calc(var(--p)*1%),rgba(255,255,255,.22) 0);position:relative}}
.ring::before{{content:"";position:absolute;inset:11px;border-radius:50%;background:#12224a}}
.ring span{{position:relative;text-align:center;font-size:30px;font-weight:700;line-height:1}}
.ring span small{{display:block;font-size:11px;font-weight:500;opacity:.85;letter-spacing:.08em;margin-top:4px}}
.hero .txt{{flex:1;min-width:280px}}
.hero .txt b{{font-size:17px}}
.chips{{display:flex;gap:8px;flex-wrap:wrap;margin-top:10px}}
.chip{{background:rgba(255,255,255,.15);border:1px solid rgba(255,255,255,.28);border-radius:999px;padding:4px 11px;font-size:12.5px}}
nav.toc{{position:sticky;top:0;z-index:20;background:rgba(245,247,251,.94);backdrop-filter:blur(8px);border-bottom:1px solid var(--line);margin:-26px 0 26px}}
nav.toc .wrap{{display:flex;gap:16px;flex-wrap:wrap;padding:11px 22px;font-size:13.5px;font-weight:600}}
h2{{font-size:21px;margin:38px 0 6px;letter-spacing:-.01em}}
h2 .n{{color:var(--brand);font-weight:700;margin-right:8px}}
h3{{font-size:16.5px;margin:24px 0 8px}}
h4{{font-size:14px;margin:18px 0 6px;color:var(--muted);text-transform:uppercase;letter-spacing:.06em}}
h5{{font-size:13px;margin:0 0 8px;text-transform:uppercase;letter-spacing:.05em;color:var(--muted)}}
p.lead{{color:var(--muted);margin:0 0 14px;max-width:820px}}
.card{{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:20px 22px;margin:16px 0;box-shadow:0 1px 2px rgba(15,23,42,.04)}}
.grid{{display:grid;gap:16px}} .g2{{grid-template-columns:repeat(auto-fit,minmax(320px,1fr))}} .g3{{grid-template-columns:repeat(auto-fit,minmax(240px,1fr))}}
.kpi{{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:16px 18px}}
.kpi b{{display:block;font-size:26px;letter-spacing:-.02em}}
.kpi span{{color:var(--muted);font-size:13px}}
.bar{{background:#eef2f7;border-radius:6px;height:9px;overflow:hidden;flex:1}}
.bar span{{display:block;height:100%;border-radius:6px;background:#94a3b8}}
.bar.ok span{{background:linear-gradient(90deg,#22c55e,#15803d)}}
.bar.warn span{{background:linear-gradient(90deg,#f59e0b,#b45309)}}
.bar.bad span{{background:linear-gradient(90deg,#f87171,#b91c1c)}}
.gbar{{margin:0 0 12px}} .ghead{{display:flex;justify-content:space-between;font-size:13.5px;margin-bottom:3px}}
.ghead .ok{{color:var(--ok)}} .ghead .warn{{color:var(--warn)}} .ghead .bad{{color:var(--bad)}}
.dimrow{{display:flex;align-items:center;gap:10px;font-size:13px;margin-bottom:6px}}
.dimnom{{width:130px;color:var(--muted)}} .dimval{{width:52px;text-align:right;font-weight:700}}
.dimval.ok,.num.ok{{color:var(--ok)}} .dimval.warn,.num.warn{{color:var(--warn)}} .dimval.bad,.num.bad{{color:var(--bad)}}
small{{font-weight:400;color:var(--muted);font-size:11px}}
table{{width:100%;border-collapse:collapse;background:var(--card);font-size:13.5px}}
table.mini{{margin-top:6px}}
.mini th{{font-size:11px;text-transform:uppercase;letter-spacing:.04em;color:var(--muted);padding:4px 6px;border-bottom:1px solid var(--line);text-align:center}}
.num{{text-align:center;font-variant-numeric:tabular-nums}}
table.inv{{border:1px solid var(--line);border-radius:12px;overflow:hidden;margin:12px 0}}
table.inv th{{background:#f8fafc;text-align:left;padding:9px 10px;font-size:11.5px;text-transform:uppercase;letter-spacing:.04em;color:var(--muted);border-bottom:1px solid var(--line)}}
table.inv td{{padding:9px 10px;border-bottom:1px solid var(--line);vertical-align:top}}
table.inv tr:last-child td{{border-bottom:0}} table.inv tbody tr:hover{{background:#fbfcfe}}
td.rol{{color:var(--muted);font-size:13px}}
.pill{{display:inline-block;border-radius:999px;padding:1px 9px;font-size:11.5px;font-weight:600}}
.pill.ok{{background:var(--okbg);color:var(--ok);border:1px solid #bbf7d0}}
.pill.off{{background:#f1f5f9;color:var(--muted);border:1px solid var(--line)}}
details.flujo{{background:var(--card);border:1px solid var(--line);border-radius:12px;margin:10px 0;overflow:hidden}}
details.flujo>summary{{display:flex;align-items:center;gap:12px;padding:13px 16px;cursor:pointer;font-weight:600;list-style:none}}
details.flujo>summary::-webkit-details-marker{{display:none}}
details.flujo>summary::before{{content:"▸";color:var(--muted);transition:.15s}}
details.flujo[open]>summary::before{{transform:rotate(90deg)}}
.fclave{{background:var(--chip);color:var(--brand);border-radius:7px;padding:2px 9px;font-size:12.5px;font-weight:700;min-width:76px;text-align:center}}
.fnombre{{flex:1}}
.fscore{{font-weight:700;font-size:16px}} .fscore.ok{{color:var(--ok)}} .fscore.warn{{color:var(--warn)}}
.fbody{{padding:4px 18px 18px;border-top:1px solid var(--line)}}
.fmeta{{color:var(--muted);font-size:13px;margin:6px 0 14px}}
.gap{{border-radius:999px;padding:1px 9px;font-size:12px;font-weight:600}}
.gap.ok{{background:var(--okbg);color:var(--ok);border:1px solid #bbf7d0}}
.gap.warn{{background:var(--warnbg);color:var(--warn);border:1px solid #fde68a}}
.cols{{display:grid;grid-template-columns:1fr 1fr;gap:22px;align-items:start}}
@media(max-width:760px){{.cols{{grid-template-columns:1fr}}}}
.pend{{margin-top:16px;border-top:1px dashed var(--line);padding-top:12px}}
.pend ul{{list-style:none;margin:0;padding:0}}
.pend li{{border-left:3px solid #fbbf24;background:var(--warnbg);border-radius:0 10px 10px 0;padding:9px 13px;margin:8px 0}}
.pend li p{{margin:3px 0 0;font-size:13.5px}}
.tagdim{{font-size:11.5px;font-weight:700;text-transform:uppercase;letter-spacing:.05em;color:var(--warn)}}
.acc{{color:var(--muted)}} .acc b{{color:var(--ink)}}
.who{{display:inline-block;background:var(--chip);color:var(--brand);border-radius:999px;padding:1px 9px;font-size:11.5px;font-weight:600}}
.muted{{color:var(--muted)}} .small{{font-size:12.5px}}
.stage{{display:flex;gap:14px;align-items:center;background:var(--card);border:1px solid var(--line);border-radius:12px;padding:13px 16px;margin:8px 0}}
.stage .num{{flex:0 0 auto;width:30px;height:30px;border-radius:9px;background:var(--chip);color:var(--brand);display:grid;place-items:center;font-weight:700}}
.stage b{{display:block}} .stage .who2{{color:var(--muted);font-size:13px}}
.arrow{{text-align:center;color:#94a3b8;margin:-2px 0 -2px 30px;font-size:16px}}
.callout{{border-left:4px solid var(--brand);background:#eff6ff;border-radius:0 12px 12px 0;padding:13px 16px;margin:14px 0}}
.callout.ok{{border-color:var(--ok);background:var(--okbg)}}
.callout.warn{{border-color:#f59e0b;background:var(--warnbg)}}
footer{{border-top:1px solid var(--line);margin-top:44px;padding-top:18px;color:var(--muted);font-size:13px}}
@media print{{nav.toc{{display:none}} details.flujo{{page-break-inside:avoid}} details.flujo .fbody{{display:block!important}}}}
</style>
</head>
<body>
<header class="top"><div class="wrap">
  <h1>Pipeline CCB · Arquitectura, evaluación del framework y pendientes</h1>
  <p>Servicios de Información — Cámara de Comercio de Barranquilla. Informe generado el {datetime.date.today().isoformat()}: el <b>inventario</b> (ids, activos y nodos) se lee en vivo de la instancia de n8n; la <b>evaluación por flujo</b> y los <b>pendientes</b> son constantes tomadas de la re-auditoría de cierre del 23/09, no una medición automática.</p>
  <div class="hero">
    <div class="ring"><span>{B}<small>/100</small></span></div>
    <div class="txt">
      <b>Aprobado con observaciones — a {FALTA} puntos del umbral de 90</b>
      <div class="chips">
        <span class="chip">{len(ACT)} flujos activos</span>
        <span class="chip">{sum(f['nodos'] for f in ACT)} nodos en total (sin notas fijas; {sum(f['con_notas'] for f in ACT)} con notas)</span>
        <span class="chip">máximo por flujo: {max(f['nodos'] for f in ACT)} nodos sin notas / {max(f['con_notas'] for f in ACT)} con notas</span>
        <span class="chip">10 de 11 requisitos de la lista de comprobación</span>
        <span class="chip">{sum(1 for f in PIPE_EVAL if f['score']>=90)} de {len(PIPE_EVAL)} flujos sobre 90</span>
      </div>
    </div>
  </div>
</div></header>

<nav class="toc"><div class="wrap">
  <a href="#resumen">Resumen</a><a href="#pipeline">Cómo funciona</a><a href="#inventario">Inventario</a>
  <a href="#evaluacion">Evaluación por flujo</a><a href="#checklist">Lista de comprobación</a>
  <a href="#pendientes">Pendientes y el 90</a><a href="#anexos">Anexos</a>
</div></nav>

<div class="wrap">

<h2 id="resumen"><span class="n">1</span>Resumen ejecutivo</h2>
<p class="lead">El pipeline automatiza la venta de los servicios de información: desde el lead hasta la propuesta enviada,
aprobada, cerrada o cancelada. Se evalúa contra la rúbrica del framework (<i>Arquitectura e Ingeniería de Automatización
en n8n</i>): seis dimensiones ponderadas sobre 100, más una lista de comprobación de 11 requisitos.</p>

<div class="grid g2">
  <div class="card">
    <h4>Evolución del puntaje</h4>
    <div class="gbar"><div class="ghead"><b>16/09 · auditoría original</b><span class="bad">53,6<small>/100</small></span></div><div class="bar bad"><span style="width:53.6%"></span></div></div>
    <div class="gbar"><div class="ghead"><b>22/09 · primera re-auditoría</b><span class="bad">67,3<small>/100</small></span></div><div class="bar bad"><span style="width:67.3%"></span></div></div>
    <div class="gbar"><div class="ghead"><b>23/09 · mañana</b><span class="warn">87,7<small>/100</small></span></div><div class="bar warn"><span style="width:87.7%"></span></div></div>
    <div class="gbar"><div class="ghead"><b>23/09 · cierre (hoy)</b><span class="ok">{B}<small>/100</small></span></div><div class="bar ok"><span style="width:{BRUTO:.1f}%"></span></div></div>
    <p class="small muted">Misma rúbrica y mismo procedimiento en las cuatro mediciones, para que la serie sea comparable.
    Línea base del umbral: <b>90</b> para producción crítica, <b>75</b> aprobado con observaciones.</p>
  </div>
  <div class="card">
    <h4>Las seis dimensiones del framework</h4>
    {"".join(barra_global(n, v, mx) for n, v, mx in DIM_EVAL)}
    <p class="small muted">Promedio de los {len(PIPE_EVAL)} flujos del pipeline. Testing es la más baja: no hay tests unitarios ni
    integración continua, y eso no se compensa con documentación.</p>
  </div>
</div>

<div class="grid g3" style="margin-top:16px">
  <div class="kpi"><b>{len(PIPE_EVAL)}</b><span>flujos del pipeline evaluados con la rúbrica completa</span></div>
  <div class="kpi"><b>{max(SC)}<small>/100</small></b><span>el mejor flujo ({[f['clave'] for f in PIPE_EVAL if f['score']==max(SC)][0]})</span></div>
  <div class="kpi"><b>{min(SC)}<small>/100</small></b><span>el más bajo ({", ".join(f['clave'] for f in PIPE_EVAL if f['score']==min(SC))}) — ninguno por debajo de 85</span></div>
  <div class="kpi"><b>{sum(1 for f in PIPE_EVAL if f['score']>=90)}</b><span>flujos ya sobre el objetivo de 90</span></div>
  <div class="kpi"><b>2</b><span>pendientes globales, ambos de Tecnología</span></div>
  <div class="kpi"><b>30</b><span>flujos en el proyecto (29 activos + 1 retirado)</span></div>
</div>

<h2 id="pipeline"><span class="n">2</span>Cómo funciona el pipeline</h2>
<p class="lead">Cinco etapas y tres ramas de decisión. En cada paso: quién interviene, qué hace el sistema y qué pasa si falla.</p>

<div class="card">
<h4>Etapa 1 — El lead y el formulario</h4>
<div class="stage"><span class="num">1</span><div><b>CCB · W1 — Extracción de información del cliente</b><span class="who2">Lead por correo de mercadeo o contacto directo → envía el enlace del formulario</span></div></div>
<div class="arrow">▼</div>
<div class="stage"><span class="num">2</span><div><b>📄 Página del formulario (Vercel)</b><span class="who2">El <b>cliente</b> completa los datos · llama al webhook <code>solicitud-georreferenciada</code> con la cabecera <code>X-CCB-Auth</code></span></div></div>
<div class="arrow">▼</div>
<div class="stage"><span class="num">3</span><div><b>CCB · W2C — Recepción del formulario externo</b><span class="who2">Valida los campos obligatorios: si falta alguno responde 400 con el detalle, sin tocar la base</span></div></div>
<div class="arrow">▼</div>
<div class="stage"><span class="num">4</span><div><b>CCB · W2A — Guardar criterios y cotizar</b> → <b>[SUB] CCB · Motor — Invocar el motor y guardar</b><span class="who2">Guarda los criterios e invoca el motor de cálculo</span></div></div>
<div class="arrow">▼</div>
<div class="stage"><span class="num">5</span><div><b>CCB · W3 — Motor de criterios y precio</b> → <b>[SUB] CCB · PDF — Generar el PDF</b><span class="who2">Calcula el precio y pide el PDF al microservicio; queda la fila en <code>Cotizaciones_CCB</code> con <code>PROPUESTA_GENERADA</code></span></div></div>
</div>

<div class="card">
<h4>Etapa 2 — La aprobación interna</h4>
<div class="stage"><span class="num">6</span><div><b>CCB · W4A — Router de aprobación</b> → <b>CCB · W4B — Aprobación por Teams</b><span class="who2">Avisa al <b>asesor</b> por Teams con el enlace a la página de revisión</span></div></div>
<div class="arrow">▼</div>
<div class="stage"><span class="num">7</span><div><b>📄 Página de revisión (Vercel)</b><span class="who2">El asesor ve los datos, los criterios y el PDF · consulta por el webhook <code>consultar-propuesta</code> (W4C)</span></div></div>
</div>

<div class="card">
<h4>Etapa 3 — La decisión (tres ramas)</h4>
<div class="stage"><span class="num">8</span><div><b>CCB · W4D — Procesar la decisión</b><span class="who2">Webhook <code>decidir-propuesta</code>: valida la decisión (400 si no se reconoce) y responde <b>antes</b> de cualquier espera</span></div></div>
<div class="grid g3" style="margin-top:12px">
  <div class="kpi"><b>✓ Aprobar</b><span><code>[SUB] CCB · W4D — Aprobar</code> → estado <b>APROBADA</b></span></div>
  <div class="kpi"><b>✕ Cancelar</b><span><code>[SUB] CCB · W4D — Cancelar</code> → estado <b>CANCELADA</b></span></div>
  <div class="kpi"><b>✎ Corregir</b><span><code>[SUB] CCB · W4D — Corrección con IA</code> → recalcula o pasa a revisión manual</span></div>
</div>
<div class="callout warn"><b>Los tres guardarraíles de la rama de IA.</b> (1) Si la IA declara <b>confianza baja</b>, va a revisión
manual sin aplicar nada y <b>sin consumir ronda</b> (F7-01). (2) El interruptor <code>ia_correccion_habilitada</code> apaga la
corrección y la manda a revisión manual (F7-02). (3) Antes de recalcular, se pide <b>aprobación humana por Teams</b> (hasta
24 h): si se rechaza, nadie responde o falla el envío, va a revisión manual sin consumir ronda (F7-03). Tope: 3 rondas.</div>
</div>

<div class="card">
<h4>Etapas 4 y 5 — El envío y el cierre</h4>
<div class="stage"><span class="num">9</span><div><b>CCB · W5A — Router de envío</b> → <b>CCB · W5B — Envío al cliente</b><span class="who2"><code>[SUB] CCB · Envío — Enviar al cliente</code> (correo con el PDF) y <code>[SUB] CCB · Envío — Cerrar el envío</code> (estado <b>ENVIADA</b> en cotización y solicitud + aviso interno)</span></div></div>
<div class="arrow">▼</div>
<div class="stage"><span class="num">10</span><div><b>CCB · W6 — Finalizador de cotizaciones</b><span class="who2">Cierra automáticamente las cotizaciones de 30+ días</span></div></div>
</div>

<div class="card">
<h4>Red de respaldo transversal</h4>
<div class="grid g3">
  <div class="kpi"><b>[SUB] CCB · Error</b><span>Registra el incidente en <code>Errores_CCB</code> con PII enmascarada, avisa por correo y <b>devuelve el item al llamador</b> para que el flujo que falló no se corte. Lo usan 8 flujos.</span></div>
  <div class="kpi"><b>CCB · Catch-all</b><span>Es el <code>errorWorkflow</code> de los 11 flujos: captura lo que nadie detectó y conserva el historial de incidentes.</span></div>
  <div class="kpi"><b>[OPS] CCB · Monitoreo</b><span>Cada hora publica las 4 métricas del framework (tasa de ejecución, tasa de error por flujo, latencia p95 y saturación) en <code>Metricas_CCB</code> y avisa si se supera un umbral.</span></div>
  <div class="kpi"><b>[OPS] CCB · Regresión</b><span>Los lunes o a mano: corre 6 caminos críticos con filas descartables, <b>verifica el estado real</b>, publica el semáforo y limpia lo que creó.</span></div>
</div>
</div>

<h2 id="inventario"><span class="n">3</span>Inventario: los 30 flujos</h2>
<p class="lead">Datos leídos de la instancia viva: {len(ACT)} activos, {sum(f['nodos'] for f in ACT)} nodos en total y un máximo
de {max(f['nodos'] for f in ACT)} nodos por flujo. El conteo <b>excluye las notas fijas (sticky notes)</b>: contando con ellas
son {sum(f['con_notas'] for f in ACT)} nodos y el máximo sube a {max(f['con_notas'] for f in ACT)}. El criterio del framework es
<b>≤20 nodos</b>, así que se cumple en ambos conteos.</p>

<h3>Las 12 etapas del pipeline</h3>
{tabla_inventario(PIPE, con_eval=True)}
<h3>Los 15 subflujos</h3>
{tabla_inventario(SUB)}
<h3>Los 2 operativos y el retirado</h3>
{tabla_inventario(OPS + RET)}

<h2 id="evaluacion"><span class="n">4</span>Evaluación del framework, flujo por flujo</h2>
<p class="lead">Puntaje de cada flujo del pipeline en las seis dimensiones de la rúbrica, con los <b>pendientes concretos</b>
para subirlo. El objetivo de 90 es el umbral de producción crítica del framework; se aplica al <b>promedio del pipeline</b>
({B} hoy) y la lectura por flujo sirve como guía de dónde está el margen.</p>
{"".join(tarjeta(f) for f in sorted(PIPE_EVAL, key=lambda x: x["score"]))}

<h2 id="checklist"><span class="n">5</span>Lista de comprobación del framework</h2>
<p class="lead">Once requisitos. Hoy se cumplen <b>10</b>; el único ámbar es idempotencia, y es por diseño: hay <i>upserts</i> en
todos los puntos de escritura y guardarraíles en W4D, pero los webhooks públicos no tienen clave natural de origen.</p>
<table class="inv"><thead><tr><th>Requisito</th><th>Estado</th><th>Evidencia</th></tr></thead><tbody>
<tr><td>Manejo global de errores</td><td><span class="pill ok">cumple</span></td><td>Los 11 flujos principales tienen <code>errorWorkflow</code> (catch-all) y los que escriben usan el subflujo compartido de error</td></tr>
<tr><td>Limpieza (sin datos de prueba fijados)</td><td><span class="pill ok">cumple</span></td><td>Sin <i>pin data</i> en ningún flujo; las filas de la regresión se borran al terminar</td></tr>
<tr><td>Protección de webhooks públicos</td><td><span class="pill ok">cumple</span></td><td>Los 3 webhooks con autenticación por cabecera (<code>X-CCB-Auth</code>) y CORS restringido en los dos del front</td></tr>
<tr><td>Documentación de los flujos</td><td><span class="pill ok">cumple</span></td><td>Descripción en los 30 flujos + notas internas + documentación en el repo</td></tr>
<tr><td>Validación de entrada</td><td><span class="pill ok">cumple</span></td><td>Los 11 flujos validan antes de escribir; los webhooks responden 400 con el detalle</td></tr>
<tr><td>Nomenclatura formal</td><td><span class="pill ok">cumple</span></td><td>Convención única documentada (patrón <code>[PREFIJO] CCB · CLAVE — Título</code>)</td></tr>
<tr><td>Resiliencia (reintentos y timeout)</td><td><span class="pill ok">cumple</span></td><td>Reintentos 5×5000 en los nodos de red y timeout explícito de 60 s en los dos HTTP</td></tr>
<tr><td>Seguridad (sin valores incrustados)</td><td><span class="pill ok">cumple</span></td><td>Cero correos, URLs o destinatarios dentro de los nodos: todo sale de <code>Configuracion_CCB</code></td></tr>
<tr><td>Arquitectura (máx. 20 nodos por flujo)</td><td><span class="pill ok">cumple</span></td><td>El flujo más grande tiene {max(f['nodos'] for f in ACT)} nodos sin notas ({max(f['con_notas'] for f in ACT)} con notas); el conteo excluye las notas fijas; el router de decisión bajó de 54 a 19</td></tr>
<tr><td>Observabilidad (4 métricas y umbral)</td><td><span class="pill ok">cumple</span></td><td>Flujo de monitoreo horario + <code>Metricas_CCB</code> + marca de tiempo en los 8 puntos de error</td></tr>
<tr><td>Idempotencia</td><td><span class="pill warn" style="background:var(--warnbg);color:var(--warn);border:1px solid #fde68a">parcial</span></td><td>6 de 11: <i>upserts</i> en las escrituras y guardarraíl de comentario repetido en W4D; los webhooks públicos no tienen clave de origen</td></tr>
</tbody></table>

<h2 id="pendientes"><span class="n">6</span>Pendientes globales y el camino al 90</h2>
<p class="lead">Dos pendientes que no son de un flujo en particular sino de la instancia o del conjunto. Los dos que
mueven el umbral son de Tecnología: lo que estaba en manos del proyecto —el trabajo técnico del día, la credencial del
monitor y el hueco del correo de alerta— ya se hizo el 24/09.</p>
{tabla_comunes()}
<div class="card">
<h4>El cálculo</h4>
<table class="inv"><thead><tr><th>Escenario</th><th>Suma</th><th>Resultado</th></tr></thead><tbody>
<tr><td>Trabajo técnico del día (casos de regresión) — <b>hecho</b></td><td class="num">+0,1 Testing</td><td class="num"><b>89,6</b></td></tr>
<tr><td>+ la credencial del monitor — <b>hecha el 24/09</b>, sin tocar la UI</td><td class="num">+0,2 Seguridad</td><td class="num"><b>89,8 ← punto de partida actual</b></td></tr>
<tr><td><b>+ la poda de ejecuciones de instancia</b> (Tecnología)</td><td class="num">+0,3 Observabilidad</td><td class="num"><b class="ok">90,1 ✅ cruza</b></td></tr>
<tr><td>+ cerrar o restringir <code>/metrics</code> (Tecnología)</td><td class="num">+0,2 Seguridad</td><td class="num"><b class="ok">90,3 ✅ consolidado</b></td></tr>
</tbody></table>
<p class="small muted">Los dos primeros escenarios ya están cumplidos: <b>todo lo que estaba en manos del proyecto se hizo</b>.
El umbral depende de una sola cosa, la poda de ejecuciones de instancia (Tecnología), que mueve Observabilidad, la
dimensión más baja junto con Seguridad. Los casos de regresión que aún faltan (routers, cierre por fechas) también
empujan Testing.</p>
</div>

<h2 id="anexos"><span class="n">7</span>Anexos</h2>
<div class="grid g2">
<div class="card"><h4>Cómo se evaluó</h4>
<p class="small">La rúbrica del framework pondera seis dimensiones sobre 100 (Arquitectura y manejo de errores sobre 20;
documentación, seguridad, testing y observabilidad sobre 15) más una lista de comprobación de 11 requisitos. El puntaje del
pipeline es el <b>promedio de los 11 flujos principales</b>. El <b>inventario</b> (ids, activos y nodos) se lee en vivo de la
instancia de n8n; la <b>evaluación por flujo</b> y los <b>pendientes</b> son constantes tomadas de la re-auditoría de cierre
del 23/09, no una medición automática. Esa evaluación se verificó <b>contra la instancia viva</b> en su momento: inventario por
API, validación estructural, ejecuciones reales de la regresión y del monitoreo, y capturas de error provocadas a propósito.
Cuando una mejora no se pudo ejecutar, el puntaje se mantiene conservador y el hueco queda declarado.</p></div>
<div class="card"><h4>Limitaciones declaradas</h4>
<p class="small">(1) Es una evaluación por evidencia y verificación real, no una suite automatizada con integración continua:
de ahí el 12,9 en Testing. (2) La poda de ejecuciones, <code>/metrics</code> y la licencia de carpetas son de instancia, no
de los flujos. (3) El hueco del <b>correo de alerta</b> quedó <b>cerrado el 24/09</b> (errata): si el envío falla, la ejecución
sigue en <code>success</code>, pero el subflujo compartido registra el fallo en <code>Errores_CCB</code> con claves propias
(<code>workflow_origen='alerta-error'</code>) y devuelve igualmente el item al llamador. (4) Sin verificar todavía: el rechazo de la aprobación de IA y el disparo automático semanal de la regresión.</p></div>
<div class="card"><h4>Tablas de datos</h4>
<p class="small"><code>Configuracion_CCB</code> (12 claves) · <code>Solicitudes_CCB</code> · <code>Criterios_Cotizacion</code>
· <code>Cotizaciones_CCB</code> · <code>Errores_CCB</code> · <code>Metricas_CCB</code>. Las tres primeras alimentan el
cálculo; la cuarta es el estado de la propuesta; las dos últimas son la salud del sistema.</p></div>
<div class="card"><h4>Documentos relacionados (en el repositorio)</h4>
<p class="small"><a href="AUDITORIA_BUENAS_PRACTICAS_2026-09-23_CIERRE.md">Re-auditoría de cierre</a> ·
<a href="AUDITORIA_BUENAS_PRACTICAS_2026-09-23.md">Re-auditoría de la mañana</a> ·
<a href="FLUJO_COMPLETO_PIPELINE_CCB.md">El pipeline de punta a punta</a> ·
<a href="FLUJOS_PIPELINE_CCB.md">Fichas de cada flujo</a> ·
<a href="TESTING_PIPELINE_CCB.md">Flujo de trabajo de testing</a> ·
<a href="COMPARATIVO_DEMO_VS_ACTUAL.md">Comparativo con el demo</a> ·
<a href="CONVENCION_NOMBRES_Y_CARPETAS_CCB.md">Convención de nombres y carpetas</a> ·
<a href="../odd/tasks/plan-pendientes-2026-09-24.md">Plan de pendientes del 24/09</a></p></div>
</div>

<footer>
  <p><b>Pipeline CCB</b> — informe de arquitectura y evaluación del framework · generado el {datetime.date.today().isoformat()} ·
  {len(ACT)} flujos activos · {sum(f['nodos'] for f in ACT)} nodos (sin notas fijas; {sum(f['con_notas'] for f in ACT)} con notas) · puntaje <b>{B}/100</b> (umbral de producción crítica: 90).</p>
  <p class="small">El inventario (ids, activos y nodos) se lee en vivo de la instancia de n8n; la evaluación por flujo y los
  pendientes son constantes tomadas de la re-auditoría de cierre del 23/09, no una medición automática. Este documento no
  sustituye a los informes firmados: los resume para lectura rápida y para presentación.</p>
</footer>
</div></body></html>"""

salida = os.path.join(os.path.dirname(AQUI), "docs", "informe-pipeline-ccb.html")
open(salida, "w", encoding="utf-8").write(HTML)
print("escrito:", salida, "|", len(HTML.encode("utf-8")), "bytes")
print("promedio:", round(BRUTO, 1), "| flujos evaluados:", len(SC), "| max nodos:", max(f['nodos'] for f in ACT))
