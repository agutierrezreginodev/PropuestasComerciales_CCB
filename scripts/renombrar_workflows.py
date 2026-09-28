#!/usr/bin/env python3
"""Renombra los flujos del pipeline CCB en n8n y refresca los `cachedResultName`
de los nodos `Execute Workflow` que apuntan a ellos.

Es una migracion de una sola vez: la tabla de renombrado es fija y vive
incrustada en este archivo (constante `RENOMBRES`), no se parsea de ningun
markdown.

Uso:
    # Simulacion (por defecto): no escribe nada.
    python3 scripts/renombrar_workflows.py
    python3 scripts/renombrar_workflows.py --dry-run
    python3 scripts/renombrar_workflows.py --only w6h0qSblUESIpSVc

    # Aplicacion real: hace PUT y verifica contra el respaldo.
    python3 scripts/renombrar_workflows.py --apply

Las credenciales se leen solo del entorno (`N8N_API_URL`, `N8N_API_KEY`) y nunca
se imprimen ni se escriben en disco.

Reglas de la migracion:
  * Solo se modifican `name` y `parameters.workflowId.cachedResultName`.
  * Los nodos que apuntan a alguno de los 30 flujos pero que NO traen
    `cachedResultName` se dejan intactos: no se agrega el campo.
  * En `--apply`, tras el PUT se vuelve a leer el flujo y se compara contra el
    respaldo en ~/ccb-backup/renombrado-2026-09-24/<id>.json para comprobar
    que ningun otro campo cambio.
"""
from __future__ import annotations

import argparse
import copy
import json
import os
import sys
import urllib.error
import urllib.request

# Tabla fija de renombrado (30 flujos). Es una migracion de una sola vez: los
# nombres se copian caracter por caracter, incluidos "·" (U+00B7) y "—" (U+2014).
RENOMBRES = {
    "w6h0qSblUESIpSVc": "CCB · W1 — Extracción de información del cliente",
    "VChcasvisGKekezR": "CCB · W2A — Guardar criterios y cotizar",
    "u6KCMnLwFOp6Ja0N": "CCB · W2C — Recepción del formulario externo",
    "cHOIOEFB5nbltN82": "CCB · W3 — Motor de criterios y precio",
    "7gmpPMBJtEb0W3J5": "CCB · W4A — Router de aprobación",
    "5RJdnHDQ8NuWZJG7": "CCB · W4B — Aprobación por Teams",
    "KuLSIzBZgaRIjuSu": "CCB · W4C — Consultar la propuesta para revisión",
    "W0TDH4b0tHCNOzFQ": "CCB · W4D — Procesar la decisión",
    "gvIn6mbAn2Y1bMRR": "CCB · W5A — Router de envío",
    "XWBHgbmtBubA4gqx": "CCB · W5B — Envío al cliente",
    "mPwl4qUb0zQkmDHN": "CCB · W6 — Finalizador de cotizaciones",
    "Dh2lAQTzyoZBpXie": "CCB · Catch-all — Errores no capturados",
    "2dY1kaT7I5a0eP2w": "[SUB] CCB · Error — Registrar y alertar",
    "Hgy02eqPhnsdJvkq": "[SUB] CCB · Config — Leer la configuración",
    "GELWpskp0aYJ2zPg": "[SUB] CCB · Contexto — Leer el contexto de la propuesta",
    "DF3emCmBBBB2HA3i": "[SUB] CCB · PDF — Generar el PDF",
    "MHWlUApSFT6gpBHs": "[SUB] CCB · Motor — Invocar el motor y guardar",
    "AnPJGVWylmKEYWmJ": "[SUB] CCB · Envío — Enviar al cliente",
    "1Zzkrg3dTkTrddgp": "[SUB] CCB · Envío — Cerrar el envío",
    "D2d9Og6UUvq13TJA": "[SUB] CCB · Envío — Cerrar el error de envío",
    "8j6BCwXkgJCccyO1": "[SUB] CCB · W4D — Aprobar",
    "Jgf514VxDINJ8ra3": "[SUB] CCB · W4D — Cancelar",
    "iNSErCHs2iw33emJ": "[SUB] CCB · W4D — Revisión manual",
    "3NAcLF4jaZ1JBw0A": "[SUB] CCB · W4D — Corrección con IA",
    "POeFkqQp8e4cGfY3": "[SUB] CCB · W4D — Cierre de la corrección",
    "DgUfcoudk228kOw8": "[SUB] CCB · Regresión — Preparar filas",
    "OuE4SS9Jujz1dVif": "[SUB] CCB · Regresión — Verificar y limpiar",
    "ZwBFTBhwS9pjS69X": "[OPS] CCB · Monitoreo — Métricas del pipeline",
    "GVE3iNQ80y5Q9FEw": "[OPS] CCB · Regresión — Prueba de regresión",
    "lIcdT6nGd0w1G2i0": "[RETIRADO] CCB · W2B — Formulario antiguo",
}

# Tipo de nodo que invoca otro flujo.
TIPO_EXECUTE_WORKFLOW = "n8n-nodes-base.executeWorkflow"

# Campos de `settings` que la API devuelve pero no acepta en el PUT (solo lectura).
SETTINGS_SOLO_LECTURA = ("binaryMode", "timeSavedMode")

# Respaldo crudo de los 30 flujos, hecho por el padre antes de esta migracion.
RESPALDO_BASE = os.environ.get("CCB_BACKUP_DIR", os.path.join(os.path.expanduser("~"), "ccb-backup"))
RESPALDO_DIR = os.path.join(RESPALDO_BASE, "renombrado-2026-09-24")


def fetch(base: str, key: str, workflow_id: str) -> dict:
    """Lee un flujo completo por ID."""
    request = urllib.request.Request(
        f"{base}/api/v1/workflows/{workflow_id}",
        headers={"X-N8N-API-KEY": key, "accept": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=90) as response:
        return json.load(response)


def enviar_put(base: str, key: str, workflow_id: str, payload: dict) -> tuple[int, str]:
    """Envia el PUT del flujo y devuelve (status, cuerpo)."""
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        f"{base}/api/v1/workflows/{workflow_id}",
        data=data,
        method="PUT",
        headers={
            "X-N8N-API-KEY": key,
            "accept": "application/json",
            "content-type": "application/json",
        },
    )
    with urllib.request.urlopen(request, timeout=120) as response:
        return response.status, response.read().decode("utf-8", "replace")


def calcular_cambios(workflow: dict) -> tuple[list[tuple[dict, str]], int]:
    """Calcula los nodos cuyo `cachedResultName` hay que refrescar.

    Devuelve (cambios, sin_cache): `cambios` es la lista de (nodo, nombre nuevo)
    y `sin_cache` cuenta los nodos que apuntan a alguno de los 30 flujos pero no
    traen `cachedResultName` (esos no se tocan).
    """
    cambios: list[tuple[dict, str]] = []
    sin_cache = 0
    for nodo in workflow.get("nodes", []):
        if nodo.get("type") != TIPO_EXECUTE_WORKFLOW:
            continue
        parametros = nodo.get("parameters") or {}
        referencia = parametros.get("workflowId")
        if not isinstance(referencia, dict):
            continue
        destino = referencia.get("value")
        if destino not in RENOMBRES:
            continue
        if "cachedResultName" not in referencia:
            sin_cache += 1
            continue
        nuevo = RENOMBRES[destino]
        if referencia.get("cachedResultName") != nuevo:
            cambios.append((nodo, nuevo))
    return cambios, sin_cache


def construir_payload(workflow: dict) -> dict:
    """Arma el cuerpo del PUT con solo los campos aceptados por la API."""
    settings = dict(workflow.get("settings") or {})
    for campo in SETTINGS_SOLO_LECTURA:
        settings.pop(campo, None)

    payload = {
        "name": workflow["name"],
        "nodes": workflow.get("nodes", []),
        "connections": workflow.get("connections", {}),
        "settings": settings,
    }

    # `description` no puede ser nulo: se omite si no es una cadena no vacia.
    descripcion = workflow.get("description")
    if isinstance(descripcion, str) and descripcion:
        payload["description"] = descripcion

    return payload


def proyeccion(workflow: dict) -> dict:
    """Campos que el PUT debe preservar, normalizando la excepcion esperada.

    Se ignoran los metadatos volatiles que cambian solos tras un PUT
    (`updatedAt`, `versionCounter`, `versionId`, `activeVersion`, etc.). El
    `name` queda fuera porque es el cambio esperado, y los `cachedResultName`
    se normalizan a un marcador para comparar el resto de `nodes`.

    `staticData` tambien queda fuera: en los flujos con trigger de sondeo guarda
    el cursor del trigger (por ejemplo `node:<trigger>:lastTimeChecked`), que
    avanza solo mientras el flujo esta activo. Comprobado el 24/09 en W1: su
    cursor se movio entre el respaldo y el PUT sin que el PUT lo tocara.
    """
    nodos = copy.deepcopy(workflow.get("nodes", []))
    for nodo in nodos:
        parametros = nodo.get("parameters") or {}
        referencia = parametros.get("workflowId")
        if isinstance(referencia, dict) and "cachedResultName" in referencia:
            referencia["cachedResultName"] = "<CACHE>"

    return {
        "nodes": nodos,
        "connections": workflow.get("connections"),
        "settings": workflow.get("settings"),
        "active": workflow.get("active"),
        "pinData": workflow.get("pinData"),
        # `staticData` se omite a proposito: es estado vivo del trigger, no del
        # flujo. Ver la nota del docstring.
        "description": workflow.get("description"),
    }


def cargar_respaldo(workflow_id: str) -> dict | None:
    ruta = os.path.join(RESPALDO_DIR, f"{workflow_id}.json")
    if not os.path.exists(ruta):
        return None
    with open(ruta, encoding="utf-8") as handle:
        return json.load(handle)


def verificar(actual: dict, workflow_id: str, nombre_nuevo: str) -> list[str]:
    """Comprueba (a) nombre, (b) cachedResultName y (c) resto del flujo."""
    problemas: list[str] = []

    # (a) nombre nuevo
    if actual.get("name") != nombre_nuevo:
        problemas.append(f"el nombre no quedo nuevo: {actual.get('name')!r}")

    # (b) cachedResultName nuevos
    for nodo in actual.get("nodes", []):
        if nodo.get("type") != TIPO_EXECUTE_WORKFLOW:
            continue
        referencia = (nodo.get("parameters") or {}).get("workflowId")
        if not isinstance(referencia, dict) or "cachedResultName" not in referencia:
            continue
        destino = referencia.get("value")
        if destino in RENOMBRES and referencia.get("cachedResultName") != RENOMBRES[destino]:
            problemas.append(
                f"cachedResultName no quedo nuevo en el nodo {nodo.get('name')!r}: "
                f"{referencia.get('cachedResultName')!r}"
            )

    # (c) el resto del flujo no cambio respecto al respaldo
    respaldo = cargar_respaldo(workflow_id)
    if respaldo is None:
        problemas.append(
            f"no hay respaldo en {RESPALDO_DIR}/{workflow_id}.json para comparar el resto del flujo"
        )
    else:
        antes = proyeccion(respaldo)
        despues = proyeccion(actual)
        for campo in antes:
            if antes[campo] != despues[campo]:
                problemas.append(f"el campo {campo!r} cambio respecto al respaldo")

    return problemas


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Renombra los flujos CCB en n8n y refresca los cachedResultName.",
    )
    modo = parser.add_mutually_exclusive_group()
    modo.add_argument("--dry-run", action="store_true", help="simula sin escribir (por defecto)")
    modo.add_argument("--apply", action="store_true", help="aplica los PUT y verifica")
    parser.add_argument("--only", metavar="ID", help="procesa solo el flujo indicado")
    args = parser.parse_args()

    base = os.environ.get("N8N_API_URL", "").rstrip("/")
    key = os.environ.get("N8N_API_KEY", "")
    if not base or not key:
        print("N8N_API_URL y N8N_API_KEY deben estar definidas en el entorno.", file=sys.stderr)
        return 2

    ids = list(RENOMBRES)
    if args.only:
        if args.only not in RENOMBRES:
            print(f"El id {args.only!r} no esta en la tabla de renombrado.", file=sys.stderr)
            return 2
        ids = [args.only]

    if not os.path.isdir(RESPALDO_DIR):
        print(
            f"AVISO: no existe el respaldo {RESPALDO_DIR}; en --apply no se podra verificar (c).",
            file=sys.stderr,
        )

    aplicar = args.apply
    filas: list[tuple[str, str, str, int, str]] = []
    fallos = 0
    puts = 0
    total_cache = 0
    con_cambios = 0
    sin_cambios = 0
    total_sin_cache = 0

    for workflow_id in ids:
        nombre_nuevo = RENOMBRES[workflow_id]
        try:
            actual = fetch(base, key, workflow_id)
        except urllib.error.HTTPError as exc:
            cuerpo = exc.read().decode("utf-8", "replace")
            print(f"FALLO GET {workflow_id}: HTTP {exc.code}", file=sys.stderr)
            print(f"  cuerpo: {cuerpo}", file=sys.stderr)
            filas.append((workflow_id, "?", nombre_nuevo, 0, "FALLO"))
            fallos += 1
            continue
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            print(f"FALLO GET {workflow_id}: {type(exc).__name__}: {exc}", file=sys.stderr)
            filas.append((workflow_id, "?", nombre_nuevo, 0, "FALLO"))
            fallos += 1
            continue

        nombre_viejo = actual.get("name", "?")
        cambios, sin_cache = calcular_cambios(actual)
        total_sin_cache += sin_cache

        # Idempotencia: ya esta todo como debe quedar -> no se toca.
        if actual.get("name") == nombre_nuevo and not cambios:
            filas.append((workflow_id, nombre_viejo, nombre_nuevo, 0, "sin cambios"))
            sin_cambios += 1
            continue

        if not aplicar:
            filas.append((workflow_id, nombre_viejo, nombre_nuevo, len(cambios), "PLAN"))
            con_cambios += 1
            total_cache += len(cambios)
            continue

        # Mutar solo lo permitido sobre la copia leida.
        for nodo, nuevo in cambios:
            nodo["parameters"]["workflowId"]["cachedResultName"] = nuevo
        actual["name"] = nombre_nuevo

        payload = construir_payload(actual)
        try:
            status, cuerpo = enviar_put(base, key, workflow_id, payload)
        except urllib.error.HTTPError as exc:
            cuerpo = exc.read().decode("utf-8", "replace")
            print(f"FALLO PUT {workflow_id}: HTTP {exc.code}", file=sys.stderr)
            print(f"  cuerpo: {cuerpo}", file=sys.stderr)
            filas.append((workflow_id, nombre_viejo, nombre_nuevo, 0, "FALLO"))
            fallos += 1
            continue
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            print(f"FALLO PUT {workflow_id}: {type(exc).__name__}: {exc}", file=sys.stderr)
            filas.append((workflow_id, nombre_viejo, nombre_nuevo, 0, "FALLO"))
            fallos += 1
            continue

        puts += 1

        # Verificacion posterior obligatoria: releer y comparar.
        try:
            verificado = fetch(base, key, workflow_id)
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError) as exc:
            print(f"FALLO VERIFICACION {workflow_id}: no se pudo releer ({type(exc).__name__}: {exc})", file=sys.stderr)
            filas.append((workflow_id, nombre_viejo, nombre_nuevo, len(cambios), "FALLO"))
            fallos += 1
            continue

        problemas = verificar(verificado, workflow_id, nombre_nuevo)
        if problemas:
            print(f"FALLO VERIFICACION {workflow_id}:", file=sys.stderr)
            for problema in problemas:
                print(f"  - {problema}", file=sys.stderr)
            filas.append((workflow_id, nombre_viejo, nombre_nuevo, len(cambios), "FALLO"))
            fallos += 1
            continue

        filas.append((workflow_id, nombre_viejo, nombre_nuevo, len(cambios), "APLICADO"))
        con_cambios += 1
        total_cache += len(cambios)

    # Resumen tabular por flujo.
    print(f"{'id':<20}{'cache':>6}  {'estado':<12}nombre antiguo -> nombre nuevo")
    print("-" * 100)
    for workflow_id, viejo, nuevo, n, estado in filas:
        print(f"{workflow_id:<20}{n:>6}  {estado:<12}{viejo} -> {nuevo}")

    print()
    print(f"Flujos procesados: {len(filas)}")
    if aplicar:
        print(f"Flujos aplicados: {con_cambios}")
    else:
        print(f"Flujos con cambios planificados: {con_cambios}")
    print(f"Flujos sin cambios: {sin_cambios}")
    print(f"cachedResultName {'refrescados' if aplicar else 'a refrescar'}: {total_cache}")
    print(f"PUT enviados: {puts}")
    print(f"Nodos executeWorkflow hacia los 30 sin cachedResultName (no se tocan): {total_sin_cache}")
    if not aplicar:
        print("Modo simulacion (--dry-run): no se envio ningun PUT.")

    if fallos:
        print(f"FALLOS: {fallos}", file=sys.stderr)
        return 1

    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
