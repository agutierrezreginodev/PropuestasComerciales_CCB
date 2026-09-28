#!/usr/bin/env python3
"""Mueve los 30 flujos del pipeline CCB a las carpetas del proyecto en n8n.

Es una migracion de una sola vez: la asignacion flujo -> carpeta vive incrustada
en este archivo (constante `CARPETAS`), en el mismo orden que la seccion 3 de
`docs/CONVENCION_NOMBRES_Y_CARPETAS_CCB.md`. No se parsea ningun markdown: los
ids y los nombres se copian caracter por caracter, incluidos "·" (U+00B7) y
"—" (U+2014).

Uso:
    # Plan offline: no toca la red. Sirve para revisar la tabla.
    python3 scripts/mover_flujos_a_carpetas.py --solo-plan

    # Sonda de acceso (solo lectura): informa que endpoints responden hoy.
    python3 scripts/mover_flujos_a_carpetas.py

    # Simulacion (por defecto): lee los flujos reales y valida el plan. No escribe.
    python3 scripts/mover_flujos_a_carpetas.py --dry-run

    # Aplicacion real: crea las carpetas que falten y mueve los flujos.
    python3 scripts/mover_flujos_a_carpetas.py --project-id <PROJECT_ID> --apply

    # Opcional: crear tambien las subcarpetas dentro de "02 · Subflujos CCB".
    python3 scripts/mover_flujos_a_carpetas.py --project-id <ID> --apply --subcarpetas

ESTADO (25/09/2026): **el camino de escritura no esta probado.** La instancia no
esta registrada, y por eso:
  * `GET /api/v1/projects/{id}/folders` -> 403 Forbidden
  * `GET /api/v1/projects`             -> 403 "Your license does not allow for
    feat:projectRole:admin"
  * `n8n_manage_folders` (MCP)         -> Forbidden, "folders unlock on the
    registered free Community tier (Settings -> Usage and plan -> register)"
El camino de lectura si esta probado: `GET /api/v1/workflows` -> 200.
Con A6 (registrar la instancia) hecho, correr este script sin argumentos para
ver la sonda de acceso antes de intentar `--apply`.

NOTA (28/09/2026): **A2 ya se cerro a mano en la UI**, asi que este script **no
hace falta para el estado actual**. Quedo como herramienta para una instancia
futura o para reorganizar carpetas cuando la instancia este registrada (A6).

LIMITE CONOCIDO: n8n trata la carpeta de un flujo como **write-only** — la acepta
al escribir y **no la devuelve al leer**. Por eso `--apply` no puede verificar el
resultado por API: al final informa los conteos por carpeta y recuerda que la
comprobacion real es visual en la UI (12 · 15 · 2 · 28: 23 del proyecto mas los
5 ajenos que se decidio dejar en `99 · Retirados`). Tampoco se puede revertir
un movimiento de carpeta por API.

Las credenciales se leen solo del entorno (`N8N_API_URL`, `N8N_API_KEY`) y nunca
se imprimen ni se escriben en disco. El id del proyecto se toma de
`--project-id` o de `N8N_PROJECT_ID`; no se adivina, porque hoy `GET /projects`
esta bloqueado y no hay forma de descubrirlo.
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import sys
import urllib.error
import urllib.request

# Carpeta -> [(id, nombre esperado)] en el orden de la convencion §3.
CARPETAS: list[tuple[str, list[tuple[str, str]]]] = [
    (
        "01 · Pipeline CCB",
        [
            ("w6h0qSblUESIpSVc", "CCB · W1 — Extracción de información del cliente"),
            ("VChcasvisGKekezR", "CCB · W2A — Guardar criterios y cotizar"),
            ("u6KCMnLwFOp6Ja0N", "CCB · W2C — Recepción del formulario externo"),
            ("cHOIOEFB5nbltN82", "CCB · W3 — Motor de criterios y precio"),
            ("7gmpPMBJtEb0W3J5", "CCB · W4A — Router de aprobación"),
            ("5RJdnHDQ8NuWZJG7", "CCB · W4B — Aprobación por Teams"),
            ("KuLSIzBZgaRIjuSu", "CCB · W4C — Consultar la propuesta para revisión"),
            ("W0TDH4b0tHCNOzFQ", "CCB · W4D — Procesar la decisión"),
            ("gvIn6mbAn2Y1bMRR", "CCB · W5A — Router de envío"),
            ("XWBHgbmtBubA4gqx", "CCB · W5B — Envío al cliente"),
            ("mPwl4qUb0zQkmDHN", "CCB · W6 — Finalizador de cotizaciones"),
            ("Dh2lAQTzyoZBpXie", "CCB · Catch-all — Errores no capturados"),
        ],
    ),
    (
        "02 · Subflujos CCB",
        [
            ("2dY1kaT7I5a0eP2w", "[SUB] CCB · Error — Registrar y alertar"),
            ("Hgy02eqPhnsdJvkq", "[SUB] CCB · Config — Leer la configuración"),
            ("GELWpskp0aYJ2zPg", "[SUB] CCB · Contexto — Leer el contexto de la propuesta"),
            ("DF3emCmBBBB2HA3i", "[SUB] CCB · PDF — Generar el PDF"),
            ("MHWlUApSFT6gpBHs", "[SUB] CCB · Motor — Invocar el motor y guardar"),
            ("AnPJGVWylmKEYWmJ", "[SUB] CCB · Envío — Enviar al cliente"),
            ("1Zzkrg3dTkTrddgp", "[SUB] CCB · Envío — Cerrar el envío"),
            ("D2d9Og6UUvq13TJA", "[SUB] CCB · Envío — Cerrar el error de envío"),
            ("8j6BCwXkgJCccyO1", "[SUB] CCB · W4D — Aprobar"),
            ("Jgf514VxDINJ8ra3", "[SUB] CCB · W4D — Cancelar"),
            ("iNSErCHs2iw33emJ", "[SUB] CCB · W4D — Revisión manual"),
            ("3NAcLF4jaZ1JBw0A", "[SUB] CCB · W4D — Corrección con IA"),
            ("POeFkqQp8e4cGfY3", "[SUB] CCB · W4D — Cierre de la corrección"),
            ("DgUfcoudk228kOw8", "[SUB] CCB · Regresión — Preparar filas"),
            ("OuE4SS9Jujz1dVif", "[SUB] CCB · Regresión — Verificar y limpiar"),
        ],
    ),
    (
        "03 · Operativos CCB",
        [
            ("ZwBFTBhwS9pjS69X", "[OPS] CCB · Monitoreo — Métricas del pipeline"),
            ("GVE3iNQ80y5Q9FEw", "[OPS] CCB · Regresión — Prueba de regresión"),
        ],
    ),
    (
        "99 · Retirados",
        [
            ("lIcdT6nGd0w1G2i0", "[RETIRADO] CCB · W2B — Formulario antiguo"),
        ],
    ),
]

# Subcarpetas opcionales dentro de "02 · Subflujos CCB" (--subcarpetas).
SUBCARPETAS: dict[str, list[str]] = {
    "Compartidos": ["2dY1kaT7I5a0eP2w", "Hgy02eqPhnsdJvkq", "GELWpskp0aYJ2zPg", "DF3emCmBBBB2HA3i", "MHWlUApSFT6gpBHs"],
    "Envío": ["AnPJGVWylmKEYWmJ", "1Zzkrg3dTkTrddgp", "D2d9Og6UUvq13TJA"],
    "W4D": ["8j6BCwXkgJCccyO1", "Jgf514VxDINJ8ra3", "iNSErCHs2iw33emJ", "3NAcLF4jaZ1JBw0A", "POeFkqQp8e4cGfY3"],
    "Regresión": ["DgUfcoudk228kOw8", "OuE4SS9Jujz1dVif"],
}

CARPETA_PADRE_SUBCARPETAS = "02 · Subflujos CCB"

# Campos de `settings` que la API devuelve pero no acepta en el PUT (solo lectura).
SETTINGS_SOLO_LECTURA = ("binaryMode", "timeSavedMode")

# Respaldo crudo por flujo antes de cada PUT (mismo criterio que el renombrado).
RESPALDO_DIR = f"/tmp/n8n-backup/carpetas-{datetime.date.today().isoformat()}"


def validar_tabla() -> list[str]:
    """Comprueba la consistencia interna de la tabla. Se corre siempre."""
    problemas: list[str] = []
    ids = [wid for _, flujos in CARPETAS for wid, _ in flujos]
    repetidos = sorted({w for w in ids if ids.count(w) > 1})
    if repetidos:
        problemas.append(f"ids repetidos en CARPETAS: {repetidos}")
    if len(ids) != 30:
        problemas.append(f"CARPETAS tiene {len(ids)} flujos, se esperaban 30")

    ids_sub = [wid for lista in SUBCARPETAS.values() for wid in lista]
    repetidos_sub = sorted({w for w in ids_sub if ids_sub.count(w) > 1})
    if repetidos_sub:
        problemas.append(f"ids repetidos en SUBCARPETAS: {repetidos_sub}")
    fuera_de_carpetas = sorted(set(ids_sub) - set(ids))
    if fuera_de_carpetas:
        problemas.append(f"SUBCARPETAS menciona ids que no estan en CARPETAS: {fuera_de_carpetas}")
    esperados_sub = dict(CARPETAS)[CARPETA_PADRE_SUBCARPETAS]
    if set(ids_sub) != {wid for wid, _ in esperados_sub}:
        problemas.append(
            "SUBCARPETAS debe cubrir exactamente los flujos de "
            f"{CARPETA_PADRE_SUBCARPETAS!r}"
        )
    return problemas


def peticion(base: str, key: str, metodo: str, ruta: str, payload: dict | None = None) -> tuple[int, object]:
    """Hace una peticion a la API publica y devuelve (status, cuerpo parseado)."""
    cuerpo = None if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
    cabeceras = {"X-N8N-API-KEY": key, "accept": "application/json"}
    if cuerpo is not None:
        cabeceras["content-type"] = "application/json"
    request = urllib.request.Request(f"{base}{ruta}", data=cuerpo, method=metodo, headers=cabeceras)
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            texto = response.read().decode("utf-8", "replace")
            try:
                return response.status, json.loads(texto)
            except json.JSONDecodeError:
                return response.status, texto
    except urllib.error.HTTPError as exc:
        texto = exc.read().decode("utf-8", "replace")
        try:
            return exc.code, json.loads(texto)
        except json.JSONDecodeError:
            return exc.code, texto


def listar_flujos(base: str, key: str) -> tuple[dict[str, str], list[dict], str | None]:
    """Devuelve (id -> nombre) de TODOS los flujos visibles para la clave."""
    mapa: dict[str, str] = {}
    crudos: list[dict] = []
    cursor: str | None = None
    for _ in range(20):
        ruta = "/api/v1/workflows?limit=250" + (f"&cursor={cursor}" if cursor else "")
        status, data = peticion(base, key, "GET", ruta)
        if status != 200 or not isinstance(data, dict):
            return mapa, crudos, f"GET /workflows -> HTTP {status}"
        for flujo in data.get("data") or []:
            if isinstance(flujo, dict) and flujo.get("id"):
                mapa[str(flujo["id"])] = str(flujo.get("name", ""))
                crudos.append({"id": str(flujo["id"]), "name": flujo.get("name"), "active": flujo.get("active")})
        cursor = data.get("nextCursor")
        if not cursor:
            break
    return mapa, crudos, None


def construir_payload(workflow: dict, folder_id: str) -> dict:
    """Arma el PUT con solo los campos aceptados, mas `parentFolderId`."""
    settings = dict(workflow.get("settings") or {})
    for campo in SETTINGS_SOLO_LECTURA:
        settings.pop(campo, None)

    payload = {
        "name": workflow["name"],
        "nodes": workflow.get("nodes", []),
        "connections": workflow.get("connections", {}),
        "settings": settings,
        "parentFolderId": folder_id,
    }

    # `description` no puede ser nulo: se omite si no es una cadena no vacia.
    descripcion = workflow.get("description")
    if isinstance(descripcion, str) and descripcion:
        payload["description"] = descripcion

    return payload


def guardar_respaldo(workflow: dict) -> str:
    os.makedirs(RESPALDO_DIR, exist_ok=True)
    ruta = os.path.join(RESPALDO_DIR, f"{workflow['id']}.json")
    with open(ruta, "w", encoding="utf-8") as handle:
        json.dump(workflow, handle, ensure_ascii=False, indent=2)
    return ruta


def plan_offline() -> int:
    print(f"{'carpeta':<22}{'flujos':>7}")
    print("-" * 60)
    for carpeta, flujos in CARPETAS:
        print(f"{carpeta:<22}{len(flujos):>7}")
    total = sum(len(flujos) for _, flujos in CARPETAS)
    print("-" * 60)
    print(f"{'TOTAL':<22}{total:>7}")
    print()
    for subcarpeta, ids in SUBCARPETAS.items():
        print(f"  subcarpeta de {CARPETA_PADRE_SUBCARPETAS}: {subcarpeta} -> {len(ids)} flujos")
    return 0


def sonda_acceso(base: str, key: str, project_id: str | None) -> int:
    """Solo lectura: informa que endpoints responden hoy y cierra sin escribir."""
    print("Sonda de acceso (solo lectura)")
    print("-" * 60)
    status, _ = peticion(base, key, "GET", "/api/v1/workflows?limit=1")
    print(f"  GET /api/v1/workflows                 -> HTTP {status}   {'OK' if status == 200 else 'BLOQUEADO'}")
    status_proj, cuerpo_proj = peticion(base, key, "GET", "/api/v1/projects?limit=5")
    detalle = ""
    if isinstance(cuerpo_proj, dict) and cuerpo_proj.get("message"):
        detalle = f"   {str(cuerpo_proj['message'])[:80]}"
    print(f"  GET /api/v1/projects                  -> HTTP {status_proj}{detalle}")
    if project_id:
        status_carp, cuerpo_carp = peticion(base, key, "GET", f"/api/v1/projects/{project_id}/folders")
        print(f"  GET /projects/{project_id}/folders -> HTTP {status_carp}")
        if isinstance(cuerpo_carp, dict) and cuerpo_carp.get("message"):
            print(f"      {cuerpo_carp['message']}")
    else:
        print("  (sin --project-id: no se pudo sondear el endpoint de carpetas)")
    print("-" * 60)
    if status_proj == 200:
        print("Acceso a carpetas disponible. Se puede planificar el --apply.")
        return 0
    print("Acceso a carpetas BLOQUEADO. Falta registrar la instancia")
    print("(Settings -> Usage and plan -> register) y una API key con scopes folder:*.")
    return 1


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Mueve los 30 flujos CCB a las carpetas del proyecto en n8n.",
    )
    modo = parser.add_mutually_exclusive_group()
    modo.add_argument("--dry-run", action="store_true", help="simula sin escribir (por defecto)")
    modo.add_argument("--apply", action="store_true", help="crea carpetas y mueve los flujos")
    parser.add_argument("--solo-plan", action="store_true", help="imprime la tabla y no toca la red")
    parser.add_argument("--probar-acceso", action="store_true", help="solo sonda de lectura")
    parser.add_argument("--subcarpetas", action="store_true", help="crea tambien las subcarpetas de 02")
    parser.add_argument("--project-id", default=os.environ.get("N8N_PROJECT_ID", ""), help="id del proyecto (o N8N_PROJECT_ID)")
    args = parser.parse_args()

    problemas_tabla = validar_tabla()
    if problemas_tabla:
        print("TABLA INVALIDA:", file=sys.stderr)
        for problema in problemas_tabla:
            print(f"  - {problema}", file=sys.stderr)
        return 2

    if args.solo_plan:
        return plan_offline()

    base = os.environ.get("N8N_API_URL", "").rstrip("/")
    key = os.environ.get("N8N_API_KEY", "")
    if not base or not key:
        print("N8N_API_URL y N8N_API_KEY deben estar definidas en el entorno.", file=sys.stderr)
        return 2

    if args.probar_acceso:
        return sonda_acceso(base, key, args.project_id or None)

    aplicar = args.apply
    if aplicar and not args.project_id:
        print(
            "En --apply hace falta --project-id (o N8N_PROJECT_ID): no se puede descubrir solo,\n"
            "porque hoy GET /api/v1/projects responde 403.",
            file=sys.stderr,
        )
        return 2

    # --- Validacion del plan contra la instancia (lectura, nunca escritura) ---
    mapa, crudos, error = listar_flujos(base, key)
    if error:
        print(f"No se pudo leer la lista de flujos: {error}", file=sys.stderr)
        return 1

    plan = {wid: nombre for _, flujos in CARPETAS for wid, nombre in flujos}
    faltantes = [wid for wid in plan if wid not in mapa]
    renombrados = [wid for wid in plan if wid in mapa and mapa[wid] != plan[wid]]
    ajenos = [f for f in crudos if str(f["id"]) not in plan]

    print(f"Flujos visibles para la clave: {len(crudos)}")
    print(f"Flujos en el plan: {len(plan)}")
    print(f"Plan ausentes en la instancia: {len(faltantes)}")
    print(f"Plan con nombre distinto al esperado: {len(renombrados)}")
    print(f"Flujos visibles que NO estan en el plan (no se tocan): {len(ajenos)}")
    if renombrados:
        for wid in renombrados:
            print(f"  nombre inesperado {wid}: {mapa[wid]!r} (esperado {plan[wid]!r})", file=sys.stderr)
    propios_fuera = [f for f in ajenos if "CCB" in str(f["name"] or "")]
    if propios_fuera:
        print(f"  de esos, con 'CCB' en el nombre (legado y versiones viejas, no se tocan): {len(propios_fuera)}")
        for f in propios_fuera[:5]:
            print(f"    {f['id']}  {f['name']}")
        if len(propios_fuera) > 5:
            print(f"    ... y {len(propios_fuera) - 5} mas")
    print()

    if faltantes or renombrados:
        print("El plan no coincide con la instancia: no se hace nada.", file=sys.stderr)
        return 1

    if not aplicar:
        print("Modo simulacion (--dry-run): no se creo ninguna carpeta ni se movio ningun flujo.")
        print()
        for carpeta, flujos in CARPETAS:
            print(f"{carpeta}: {len(flujos)} flujo{'s' if len(flujos) != 1 else ''}")
        return 0

    # --- Aplicacion ---
    status, carpetas_data = peticion(base, key, "GET", f"/api/v1/projects/{args.project_id}/folders?take=100")
    if status != 200:
        print(f"FALLO: GET folders -> HTTP {status}", file=sys.stderr)
        print(f"  {str(carpetas_data)[:300]}", file=sys.stderr)
        print("  (¿instancia sin registrar? correr --probar-acceso)", file=sys.stderr)
        return 1
    existentes = {}
    if isinstance(carpetas_data, list):
        lista_carpetas = carpetas_data
    elif isinstance(carpetas_data, dict):
        lista_carpetas = carpetas_data.get("data") or []
    else:
        lista_carpetas = []
    for carpeta in lista_carpetas:
        if isinstance(carpeta, dict) and carpeta.get("name"):
            existentes[str(carpeta["name"])] = str(carpeta.get("id"))

    creadas = 0
    ids_carpetas: dict[str, str] = {}
    for carpeta, _ in CARPETAS:
        if carpeta in existentes:
            ids_carpetas[carpeta] = existentes[carpeta]
            print(f"carpeta ya existe: {carpeta} ({existentes[carpeta]})")
            continue
        status, data = peticion(base, key, "POST", f"/api/v1/projects/{args.project_id}/folders", {"name": carpeta})
        if status not in (200, 201) or not isinstance(data, dict) or not data.get("id"):
            print(f"FALLO: crear carpeta {carpeta!r} -> HTTP {status}: {str(data)[:200]}", file=sys.stderr)
            return 1
        ids_carpetas[carpeta] = str(data["id"])
        creadas += 1
        print(f"carpeta creada: {carpeta} ({data['id']})")

    if args.subcarpetas:
        padre = ids_carpetas[CARPETA_PADRE_SUBCARPETAS]
        for subcarpeta in SUBCARPETAS:
            status, data = peticion(
                base, key, "POST", f"/api/v1/projects/{args.project_id}/folders",
                {"name": subcarpeta, "parentFolderId": padre},
            )
            if status not in (200, 201) or not isinstance(data, dict) or not data.get("id"):
                print(f"FALLO: crear subcarpeta {subcarpeta!r} -> HTTP {status}: {str(data)[:200]}", file=sys.stderr)
                return 1
            ids_carpetas[f"{CARPETA_PADRE_SUBCARPETAS}/{subcarpeta}"] = str(data["id"])
            print(f"subcarpeta creada: {subcarpeta} ({data['id']})")

    # Destino por flujo (la subcarpeta gana si se pidio).
    destino: dict[str, str] = {}
    for carpeta, flujos in CARPETAS:
        for wid, _ in flujos:
            destino[wid] = ids_carpetas[carpeta]
    if args.subcarpetas:
        for subcarpeta, ids in SUBCARPETAS.items():
            clave = f"{CARPETA_PADRE_SUBCARPETAS}/{subcarpeta}"
            for wid in ids:
                destino[wid] = ids_carpetas[clave]

    movidos = 0
    fallos = 0
    for carpeta, flujos in CARPETAS:
        for wid, nombre in flujos:
            status, workflow = peticion(base, key, "GET", f"/api/v1/workflows/{wid}")
            if status != 200 or not isinstance(workflow, dict):
                print(f"FALLO GET {wid} ({nombre}): HTTP {status}", file=sys.stderr)
                fallos += 1
                continue
            ruta = guardar_respaldo(workflow)
            payload = construir_payload(workflow, destino[wid])
            status, respuesta = peticion(base, key, "PUT", f"/api/v1/workflows/{wid}", payload)
            if status not in (200, 201):
                print(f"FALLO PUT {wid} ({nombre}): HTTP {status}: {str(respuesta)[:200]}", file=sys.stderr)
                print(f"  respaldo intacto en {ruta}", file=sys.stderr)
                fallos += 1
                continue
            movidos += 1
            print(f"movido: {nombre} -> {carpeta}")

    print()
    print(f"Carpetas creadas: {creadas}")
    print(f"Flujos movidos: {movidos}")
    if fallos:
        print(f"FALLOS: {fallos}", file=sys.stderr)
        return 1

    # Verificacion. OJO: la carpeta de un flujo es write-only en la API de n8n
    # (se escribe, no se lee de vuelta), asi que NO se puede comprobar releyendo
    # el flujo. Lo unico comprobable por API es la lista de carpetas y su conteo.
    print()
    print("Verificacion (la API no puede leer de vuelta la carpeta de un flujo):")
    status, carpetas_data = peticion(base, key, "GET", f"/api/v1/projects/{args.project_id}/folders?take=100")
    if status == 200:
        if isinstance(carpetas_data, list):
            lista_final = carpetas_data
        elif isinstance(carpetas_data, dict):
            lista_final = carpetas_data.get("data") or []
        else:
            lista_final = []
        campos_conteo = ("count", "workflowCount", "workflowsCount", "totalWorkflows")
        for carpeta in lista_final:
            if not isinstance(carpeta, dict):
                continue
            conteo = next((carpeta[c] for c in campos_conteo if c in carpeta), None)
            extra = f"  -> {conteo} flujos" if conteo is not None else ""
            print(f"  {carpeta.get('name')}{extra}")
    else:
        print(f"  AVISO: no se pudo releer la lista de carpetas (HTTP {status}).")
    print()
    print("Los movimientos se enviaron; n8n no permite comprobarlos por API.")
    print("Confirmar en la UI que cada carpeta tenga: 12 · 15 · 2 · 1 (los 30 del proyecto)")
    if args.subcarpetas:
        print("  (y, con --subcarpetas, 5 · 3 · 5 · 2 dentro de 02 · Subflujos CCB)")

    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
