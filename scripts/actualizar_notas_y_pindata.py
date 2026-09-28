#!/usr/bin/env python3
"""Actualiza dos detalles acotados de la instancia viva tras el renombrado del 24/09:

1. **Nueve notas fijas** (sticky notes) cuyo texto todavia cita el nombre **viejo**
   de algun flujo del pipeline CCB. Se sustituye, solo dentro de `parameters.content`,
   cada aparicion literal de un nombre viejo por su nombre nuevo. El mapa viejo->nuevo
   se arma con `RENOMBRES` (de `scripts/renombrar_workflows.py`) y con el respaldo
   `~/ccb-backup/renombrado-2026-09-24/<id>.json` (campo `name`), que es el estado
   **anterior** al renombrado.

2. **Un item fijado** (`pinData`) en el flujo `2dY1kaT7I5a0eP2w`
   (`[SUB] CCB · Error — Registrar y alertar`). Se quita enviando `pinData: {}` en el
   `PUT`, para cumplir el requisito "sin datos de prueba fijados".

Uso:
    # Simulacion (por defecto): no escribe nada.
    python3 scripts/actualizar_notas_y_pindata.py
    python3 scripts/actualizar_notas_y_pindata.py --dry-run
    python3 scripts/actualizar_notas_y_pindata.py --only Dh2lAQTzyoZBpXie

    # Aplicacion real: respalda, hace PUT y verifica contra el respaldo.
    python3 scripts/actualizar_notas_y_pindata.py --apply

Las credenciales se leen solo del entorno (`N8N_API_URL`, `N8N_API_KEY`) y nunca se
imprimen ni se escriben en disco.

Red de seguridad:
  * Antes de cualquier `PUT`, se descarga cada flujo a cambiar a
    `~/ccb-backup/notas-pindata-2026-09-24/<id>.json` (estado posterior al renombrado).
  * Tras cada `PUT`, se relee el flujo y se comprueba (a) que el cambio esperado esta y
    (b) que el resto del flujo no cambio respecto al respaldo. Se ignoran los metadatos
    volatiles que cambian solos (`updatedAt`, `versionCounter`, `versionId`,
    `activeVersion*` y `staticData`, que guarda el cursor del trigger de sondeo).
  * La verificacion de las notas normaliza `parameters.content` de las sticky notes y la
    del `pinData` normaliza `pinData`; el resto se compara tal cual.
  * Idempotencia: una segunda corrida de `--apply` no debe emitir ningun `PUT`.

Solo se modifica el `nodes` de nivel superior. `activeVersion.nodes` es historial interno
de n8n y no se toca. En `DF3emCmBBBB2HA3i` no se tocan los nodos `set` `HTML - *`: sus
plantillas contienen `{{ }}` a proposito y romperian el flujo si se convirtieran en
expresiones.
"""
from __future__ import annotations

import argparse
import copy
import json
import os
import sys
import urllib.error

# El script hermano tiene las utilidades de red y la tabla de renombrado.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from renombrar_workflows import (  # noqa: E402
    RENOMBRES,
    SETTINGS_SOLO_LECTURA,
    enviar_put,
    fetch,
)

# Tipo de nodo de nota fija.
TIPO_STICKY = "n8n-nodes-base.stickyNote"

# Base de los respaldos: persistente (nunca /tmp) y sobreescribible por entorno.
RESPALDO_BASE = os.environ.get("CCB_BACKUP_DIR", os.path.join(os.path.expanduser("~"), "ccb-backup"))

# Respaldo crudo previo al renombrado (estado viejo, para armar el mapa).
RESPALDO_RENOMBRADO_DIR = os.path.join(RESPALDO_BASE, "renombrado-2026-09-24")

# Respaldo crudo posterior al renombrado (red de seguridad de este script).
RESPALDO_DIR = os.path.join(RESPALDO_BASE, "notas-pindata-2026-09-24")

# Flujo -> nombre de la nota fija cuyo texto hay que actualizar.
NOTAS = {
    "Dh2lAQTzyoZBpXie": "Nota - Error Workflow",
    "ZwBFTBhwS9pjS69X": "Nota - Monitoreo",
    "1Zzkrg3dTkTrddgp": "Nota - Cerrar envío",
    "D2d9Og6UUvq13TJA": "Nota - Cerrar error de envío",
    "AnPJGVWylmKEYWmJ": "Nota - Enviar al cliente",
    "DF3emCmBBBB2HA3i": "Nota - Generar PDF",
    "MHWlUApSFT6gpBHs": "Nota - Motor y cotización",
    "Hgy02eqPhnsdJvkq": "Nota - Leer Configuración",
    "GELWpskp0aYJ2zPg": "Nota - Leer Contexto Propuesta",
}

# Flujo con un item fijado de prueba que hay que quitar.
FLUJO_PINDATA = "2dY1kaT7I5a0eP2w"

# Los 10 flujos afectados por este script.
IDS_AFECTADOS = list(NOTAS) + [FLUJO_PINDATA]


def cargar_respaldo(directorio: str, workflow_id: str) -> dict | None:
    ruta = os.path.join(directorio, f"{workflow_id}.json")
    if not os.path.exists(ruta):
        return None
    with open(ruta, encoding="utf-8") as handle:
        return json.load(handle)


def guardar_respaldo(workflow_id: str, workflow: dict) -> str:
    os.makedirs(RESPALDO_DIR, exist_ok=True)
    ruta = os.path.join(RESPALDO_DIR, f"{workflow_id}.json")
    with open(ruta, "w", encoding="utf-8") as handle:
        json.dump(workflow, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    return ruta


def cargar_reemplazos() -> list[tuple[str, str]]:
    """Arma la lista (viejo, nuevo) leyendo el respaldo previo y `RENOMBRES`.

    Se ordena de mas larga a mas corta para que un nombre corto no corrompa a uno
    largo que lo contenga.
    """
    reemplazos: list[tuple[str, str]] = []
    for workflow_id, nuevo in RENOMBRES.items():
        respaldo = cargar_respaldo(RESPALDO_RENOMBRADO_DIR, workflow_id)
        if respaldo is None:
            raise FileNotFoundError(
                f"falta el respaldo {RESPALDO_RENOMBRADO_DIR}/{workflow_id}.json "
                "para armar el mapa viejo->nuevo"
            )
        viejo = respaldo.get("name")
        if not isinstance(viejo, str) or not viejo:
            raise ValueError(f"el respaldo {workflow_id}.json no tiene un `name` valido")
        if viejo != nuevo:
            reemplazos.append((viejo, nuevo))
    reemplazos.sort(key=lambda par: len(par[0]), reverse=True)
    return reemplazos


def sustituir(texto: str, reemplazos: list[tuple[str, str]]) -> tuple[str, int]:
    """Reemplaza cada nombre viejo por el nuevo y devuelve (texto, total de cambios)."""
    total = 0
    for viejo, nuevo in reemplazos:
        if viejo in texto:
            total += texto.count(viejo)
            texto = texto.replace(viejo, nuevo)
    return texto, total


def calcular_nota(
    workflow: dict, reemplazos: list[tuple[str, str]]
) -> tuple[list[tuple[str, str, int]], list[str]]:
    """Calcula las sustituciones de las sticky notes de un flujo.

    Devuelve (cambios, sin_match): `cambios` es (nombre del nodo, contenido nuevo,
    numero de sustituciones) y `sin_match` son las sticky notes sin ninguna coincidencia
    (puede que citen el nombre de forma parcial; no se inventan sustituciones).
    """
    cambios: list[tuple[str, str, int]] = []
    sin_match: list[str] = []
    nuevos = {nuevo for _, nuevo in reemplazos}
    for nodo in workflow.get("nodes", []):
        if nodo.get("type") != TIPO_STICKY:
            continue
        parametros = nodo.get("parameters") or {}
        contenido = parametros.get("content")
        if not isinstance(contenido, str):
            continue
        nuevo, total = sustituir(contenido, reemplazos)
        if total:
            cambios.append((nodo.get("name"), nuevo, total))
        elif not any(nuevo in contenido for nuevo in nuevos):
            # Ni nombre viejo ni nuevo: puede citar el nombre de forma parcial.
            # (Una nota ya actualizada tiene el nombre nuevo y no es un aviso.)
            sin_match.append(nodo.get("name"))
    return cambios, sin_match


def construir_payload(workflow: dict, incluir_pindata: dict | None = None) -> dict:
    """Arma el cuerpo del PUT con solo los campos aceptados por la API.

    `incluir_pindata` es None para omitir el campo (asi n8n preserva el existente) o el
    valor a enviar (por ejemplo `{}` para vaciar el item fijado).
    """
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

    if incluir_pindata is not None:
        payload["pinData"] = incluir_pindata

    return payload


def proyeccion(workflow: dict, normalizar_nota: bool, normalizar_pindata: bool) -> dict:
    """Campos que el PUT debe preservar, con las excepciones esperadas normalizadas.

    Se comparan solo los campos relevantes del flujo (no los metadatos volatiles que
    cambian solos: `updatedAt`, `versionCounter`, `versionId`, `activeVersion*` y
    `staticData`). El contenido de las notas se normaliza a `<NOTA>` cuando el cambio
    esperado es justamente la nota, y `pinData` a `<PINDATA>` cuando el cambio esperado
    es vaciarlo. Un `pinData` vacio (`None` o `{}`) se normaliza a `<VACIO>`.
    """
    nodos = copy.deepcopy(workflow.get("nodes", []))
    if normalizar_nota:
        for nodo in nodos:
            if nodo.get("type") == TIPO_STICKY:
                parametros = nodo.get("parameters")
                if isinstance(parametros, dict) and "content" in parametros:
                    parametros["content"] = "<NOTA>"

    pin = workflow.get("pinData")
    if normalizar_pindata:
        pin = "<PINDATA>"
    elif pin in (None, {}):
        pin = "<VACIO>"

    return {
        "name": workflow.get("name"),
        "nodes": nodos,
        "connections": workflow.get("connections"),
        "settings": workflow.get("settings"),
        "active": workflow.get("active"),
        "pinData": pin,
        "description": workflow.get("description"),
    }


def verificar(
    actual: dict,
    respaldo: dict,
    cambios_nota: list[tuple[str, str, int]],
    quitar_pindata: bool,
) -> list[str]:
    """Comprueba (a) el cambio esperado y (b) que el resto no cambio respecto al respaldo."""
    problemas: list[str] = []

    # (a) cambio esperado presente.
    if quitar_pindata:
        pin = actual.get("pinData")
        if pin not in (None, {}):
            problemas.append(f"el pinData no quedo vacio: {pin!r}")

    for nombre_nodo, esperado, _ in cambios_nota:
        nodo_actual = None
        for nodo in actual.get("nodes", []):
            if nodo.get("type") == TIPO_STICKY and nodo.get("name") == nombre_nodo:
                nodo_actual = nodo
                break
        if nodo_actual is None:
            problemas.append(f"no se encontro la nota {nombre_nodo!r} tras el PUT")
            continue
        contenido = (nodo_actual.get("parameters") or {}).get("content")
        if contenido != esperado:
            problemas.append(f"la nota {nombre_nodo!r} no quedo con el texto esperado")

    # (b) el resto del flujo no cambio respecto al respaldo.
    antes = proyeccion(respaldo, bool(cambios_nota), quitar_pindata)
    despues = proyeccion(actual, bool(cambios_nota), quitar_pindata)
    for campo in antes:
        if antes[campo] != despues[campo]:
            problemas.append(f"el campo {campo!r} cambio respecto al respaldo")

    return problemas


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Actualiza las notas fijas con nombres viejos y quita un pinData de prueba.",
    )
    modo = parser.add_mutually_exclusive_group()
    modo.add_argument("--dry-run", action="store_true", help="simula sin escribir (por defecto)")
    modo.add_argument("--apply", action="store_true", help="respalda, aplica los PUT y verifica")
    parser.add_argument("--only", metavar="ID", help="procesa solo el flujo indicado")
    args = parser.parse_args()

    base = os.environ.get("N8N_API_URL", "").rstrip("/")
    key = os.environ.get("N8N_API_KEY", "")
    if not base or not key:
        print("N8N_API_URL y N8N_API_KEY deben estar definidas en el entorno.", file=sys.stderr)
        return 2

    try:
        reemplazos = cargar_reemplazos()
    except (FileNotFoundError, ValueError) as exc:
        print(f"FALLO: {exc}", file=sys.stderr)
        return 2

    ids = list(IDS_AFECTADOS)
    if args.only:
        if args.only not in IDS_AFECTADOS:
            print(f"El id {args.only!r} no es uno de los 10 flujos afectados.", file=sys.stderr)
            return 2
        ids = [args.only]

    aplicar = args.apply
    fallos = 0

    # ------------------------------------------------------------------ Fase A
    # Leer los flujos y calcular el plan. No se escribe nada todavia.
    plan: list[dict] = []
    for workflow_id in ids:
        try:
            actual = fetch(base, key, workflow_id)
        except urllib.error.HTTPError as exc:
            cuerpo = exc.read().decode("utf-8", "replace")
            print(f"FALLO GET {workflow_id}: HTTP {exc.code}", file=sys.stderr)
            print(f"  cuerpo: {cuerpo}", file=sys.stderr)
            plan.append({"id": workflow_id, "estado": "FALLO", "workflow": None})
            fallos += 1
            continue
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            print(f"FALLO GET {workflow_id}: {type(exc).__name__}: {exc}", file=sys.stderr)
            plan.append({"id": workflow_id, "estado": "FALLO", "workflow": None})
            fallos += 1
            continue

        entrada: dict = {"id": workflow_id, "workflow": actual, "sin_match": []}
        if workflow_id in NOTAS:
            cambios, sin_match = calcular_nota(actual, reemplazos)
            entrada["tipo"] = "nota"
            entrada["cambios"] = cambios
            entrada["total"] = sum(n for _, _, n in cambios)
            entrada["sin_match"] = sin_match
        else:
            pin = actual.get("pinData")
            entrada["tipo"] = "pindata"
            entrada["quitar"] = pin not in (None, {})
            entrada["pin_antes"] = pin
        plan.append(entrada)

    # Avisos de notas sin ninguna coincidencia.
    for entrada in plan:
        if entrada.get("estado") == "FALLO":
            continue
        for nombre_nota in entrada.get("sin_match", []):
            print(
                f"AVISO {entrada['id']}: la nota {nombre_nota!r} no cita ningun nombre "
                "viejo ni nuevo (puede citarlo de forma parcial).",
                file=sys.stderr,
            )

    def pendiente(entrada: dict) -> bool:
        if entrada.get("tipo") == "nota":
            return entrada.get("total", 0) > 0
        if entrada.get("tipo") == "pindata":
            return entrada.get("quitar", False)
        return False

    # ------------------------------------------------------------------ Respaldo
    # Antes de cualquier PUT, respaldar cada flujo que se va a tocar.
    if aplicar:
        for entrada in plan:
            if entrada.get("estado") == "FALLO" or not pendiente(entrada):
                continue
            ruta = guardar_respaldo(entrada["id"], entrada["workflow"])
            entrada["respaldo_ruta"] = ruta

    # ------------------------------------------------------------------ Fase B
    puts = 0
    if aplicar:
        for entrada in plan:
            if entrada.get("estado") == "FALLO":
                continue
            if not pendiente(entrada):
                entrada["estado_final"] = "sin cambios"
                continue

            antes = entrada["workflow"]
            mutado = copy.deepcopy(antes)
            if entrada["tipo"] == "nota":
                for nombre_nodo, nuevo, _ in entrada["cambios"]:
                    for nodo in mutado.get("nodes", []):
                        if nodo.get("type") == TIPO_STICKY and nodo.get("name") == nombre_nodo:
                            parametros = nodo.get("parameters")
                            if isinstance(parametros, dict):
                                parametros["content"] = nuevo
                payload = construir_payload(mutado)
            else:
                mutado["pinData"] = {}
                payload = construir_payload(mutado, incluir_pindata={})

            try:
                _status, _cuerpo = enviar_put(base, key, entrada["id"], payload)
            except urllib.error.HTTPError as exc:
                cuerpo = exc.read().decode("utf-8", "replace")
                print(f"FALLO PUT {entrada['id']}: HTTP {exc.code}", file=sys.stderr)
                print(f"  cuerpo: {cuerpo}", file=sys.stderr)
                entrada["estado_final"] = "FALLO"
                fallos += 1
                continue
            except (urllib.error.URLError, TimeoutError, OSError) as exc:
                print(f"FALLO PUT {entrada['id']}: {type(exc).__name__}: {exc}", file=sys.stderr)
                entrada["estado_final"] = "FALLO"
                fallos += 1
                continue

            puts += 1

            # Releer y verificar.
            try:
                verificado = fetch(base, key, entrada["id"])
            except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError) as exc:
                print(
                    f"FALLO VERIFICACION {entrada['id']}: no se pudo releer "
                    f"({type(exc).__name__}: {exc})",
                    file=sys.stderr,
                )
                entrada["estado_final"] = "FALLO"
                fallos += 1
                continue

            problemas = verificar(
                verificado,
                antes,
                entrada.get("cambios", []),
                entrada.get("quitar", False),
            )
            if problemas:
                print(f"FALLO VERIFICACION {entrada['id']}:", file=sys.stderr)
                for problema in problemas:
                    print(f"  - {problema}", file=sys.stderr)
                entrada["estado_final"] = "FALLO"
                fallos += 1
                continue

            entrada["estado_final"] = "APLICADO"

    # ------------------------------------------------------------------ Salida
    print()
    print(f"{'id':<20}{'cambios':>8}  {'estado':<12}detalle")
    print("-" * 96)
    con_cambios = 0
    sin_cambios = 0
    for entrada in plan:
        workflow_id = entrada["id"]
        if entrada.get("estado") == "FALLO":
            print(f"{workflow_id:<20}{'-':>8}  {'FALLO':<12}no se pudo leer el flujo")
            continue
        if entrada["tipo"] == "nota":
            total = entrada["total"]
            detalle = f"nota: {total} sustitucion(es)"
        else:
            total = 1 if entrada["quitar"] else 0
            if entrada["quitar"]:
                clave = entrada.get("pin_antes")
                claves = list(clave) if isinstance(clave, dict) else []
                detalle = f"pinData: quitar item fijado (claves={claves})"
            else:
                detalle = "pinData: ya vacio"

        if aplicar:
            estado = entrada.get("estado_final", "sin cambios")
            if estado == "APLICADO":
                con_cambios += 1
                detalle += "; resto sin cambios"
            elif estado == "sin cambios":
                sin_cambios += 1
        else:
            if pendiente(entrada):
                estado = "PLAN"
                con_cambios += 1
            else:
                estado = "sin cambios"
                sin_cambios += 1
        print(f"{workflow_id:<20}{total:>8}  {estado:<12}{detalle}")

    print()
    print(f"Flujos procesados: {len(plan)}")
    if aplicar:
        print(f"Flujos aplicados: {con_cambios}")
    else:
        print(f"Flujos con cambios planificados: {con_cambios}")
    print(f"Flujos sin cambios: {sin_cambios}")
    print(f"PUT enviados: {puts}")
    if not aplicar:
        print("Modo simulacion (--dry-run): no se envio ningun PUT ni se escribio ningun respaldo.")

    if fallos:
        print(f"FALLOS: {fallos}", file=sys.stderr)
        return 1

    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
