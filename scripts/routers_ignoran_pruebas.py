#!/usr/bin/env python3
"""Guardián que descarta las filas de prueba en los 3 routers de producción.

Bug preexistente que la corrida de verificación del arreglo del PDF destapó por
coincidencia de reloj (24/09). El diagnóstico completo está en la ficha
`odd/tasks/caso-motor-regresion-ccb.md`, sección **Hallazgo 2**.

W4A, W5A y W6 leen `Cotizaciones_CCB` (`YAvQTqzsgJWjacVZ`) filtrando por `estado`
y **no excluyen** las filas descartables de la regresión (`SOL-PRUEBA-*`). El
nodo `Data Table` no soporta operadores en los filtros (solo igualdad +
`matchType`), así que la exclusión no se puede expresar como filtro. Esta
migración inserta un único nodo `Code` por flujo entre la lectura y el `IF`:

    <nodo de lectura> -> Descartar filas de prueba -> Validar id_solicitud presente

El guardián devuelve la lista vacía cuando no queda ninguna fila, de modo que la
cadena se detiene sin registrar ningún error. **No se reutiliza el `IF`
existente a propósito**: su rama falsa va a
`Preparar error - id_solicitud faltante` -> `Ejecutar Registrar-y-Alertar`, así
que excluir una fila de prueba por ahí ensuciaría `Errores_CCB`, que es justo lo
que se quiere evitar.

Los tres flujos:

| Flujo | id                  | lectura                                            | antes -> después |
|-------|---------------------|----------------------------------------------------|------------------|
| W4A   | `7gmpPMBJtEb0W3J5`  | `Data Table - Leer cotizaciones PROPUESTA_GENERADA`| 9 -> 10          |
| W5A   | `gvIn6mbAn2Y1bMRR`  | `Data Table - Leer cotizaciones APROBADA`          | 12 -> 13         |
| W6    | `mPwl4qUb0zQkmDHN`  | `Data Table - Leer cotizaciones ENVIADA`           | 11 -> 12         |

**No se toca nada más.** En particular:

* El `IF` `Validar id_solicitud presente` queda intacto (ni condición ni nodos).
* Ninguna otra conexión cambia (solo la de la lectura y la del guardián).
* El nodo de lectura se mantiene en su posición `[240, 0]`. El guardián entra en
  `[360, 0]` (a la derecha de la lectura, sin solapar el `IF` en `[480, 0]`), así
  que **no hace falta desplazar ningún nodo**.
* No se activan ni desactivan flujos.

Uso:
    # Simulación (por defecto): describe el nodo y las reconexiones y no escribe.
    python3 scripts/routers_ignoran_pruebas.py
    python3 scripts/routers_ignoran_pruebas.py --dry-run

    # Aplicación real: respalda, hace PUT y verifica contra el respaldo.
    python3 scripts/routers_ignoran_pruebas.py --apply

Las credenciales se leen solo del entorno (`N8N_API_URL`, `N8N_API_KEY`) y nunca
se imprimen ni se escriben en disco.

Red de seguridad:
  * Antes de cualquier `PUT` se descarga cada flujo a
    `/tmp/n8n-backup/routers-pruebas-2026-09-24/<id>.json` y se re-verifica
    leyéndolo (9 nodos en W4A, 12 en W5A, 11 en W6). Si el respaldo ya existe se
    conserva: nunca se sobreescribe con el estado posterior.
  * Tras cada `PUT` se relee el flujo y se comprueba (a) que el guardián existe,
    que la cadena quedó `<lectura> -> Descartar filas de prueba ->
    Validar id_solicitud presente` y que el nombre es correcto, y (b) que **nada
    más** cambió respecto al respaldo, ignorando los metadatos volátiles
    (`updatedAt`, `versionCounter`, `versionId`, `activeVersion*` y `staticData`)
    y el `id` del nodo nuevo. Cualquier otra diferencia es FALLO y no se esconde.
  * Idempotencia: una segunda corrida de `--apply` no emite ningún `PUT`.

Solo se modifica `nodes` y `connections`. `activeVersion.nodes` es historial
interno de n8n y no se toca.
"""
from __future__ import annotations

import argparse
import copy
import json
import os
import sys
import urllib.error
import uuid

# El script hermano tiene las utilidades de red y el filtrado de `settings`.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from renombrar_workflows import (  # noqa: E402
    SETTINGS_SOLO_LECTURA,
    enviar_put,
    fetch,
)

# Respaldo crudo previo a este script (red de seguridad).
RESPALDO_DIR = "/tmp/n8n-backup/routers-pruebas-2026-09-24"

# Metadatos volátiles que cambian solos y no se comparan.
CLAVES_VOLATILES = (
    "updatedAt",
    "versionCounter",
    "versionId",
    "activeVersion",
    "activeVersionId",
    "staticData",
)

# Nodo guardián (idéntico en los tres flujos).
NOMBRE_GUARDIAN = "Descartar filas de prueba"
TIPO_GUARDIAN = "n8n-nodes-base.code"
TYPE_VERSION_GUARDIAN = 2
# A la derecha de la lectura ([240, 0]); el `IF` está en [480, 0], sin solape.
POS_GUARDIAN = [360, 0]

# `jsCode` exacto del guardián, idéntico en los tres flujos.
JSCODE_GUARDIAN = """// Los flujos de produccion no deben actuar sobre las filas descartables de la regresion
// (SOL-PRUEBA-*). Sin este filtro, un tick del cron que caiga a mitad de una corrida procesa
// una fila de prueba: cambia su estado, intenta enviar correos y ensucia Errores_CCB.
// El filtro del nodo Data Table solo soporta igualdad, asi que la exclusion se hace aca.
// Si no queda ninguna fila, la lista vacia detiene la cadena sin registrar ningun error.
return $input.all()
  .filter((item) => !String((item.json || {}).id_solicitud || '').startsWith('SOL-PRUEBA'))
  .map((item) => ({ json: item.json }));"""

# Los 3 routers de producción que leen `Cotizaciones_CCB` filtrando por `estado`.
FLUJOS = [
    {
        "id": "7gmpPMBJtEb0W3J5",
        "nombre": "CCB · W4A — Router de aprobación",
        "lectura": "Data Table - Leer cotizaciones PROPUESTA_GENERADA",
        "if": "Validar id_solicitud presente",
        "nodos_respaldo": 9,
        "nodos_final": 10,
    },
    {
        "id": "gvIn6mbAn2Y1bMRR",
        "nombre": "CCB · W5A — Router de envío",
        "lectura": "Data Table - Leer cotizaciones APROBADA",
        "if": "Validar id_solicitud presente",
        "nodos_respaldo": 12,
        "nodos_final": 13,
    },
    {
        "id": "mPwl4qUb0zQkmDHN",
        "nombre": "CCB · W6 — Finalizador de cotizaciones",
        "lectura": "Data Table - Leer cotizaciones ENVIADA",
        "if": "Validar id_solicitud presente",
        "nodos_respaldo": 11,
        "nodos_final": 12,
    },
]


# ----------------------------------------------------------------------- comunes


def buscar_nodo(workflow: dict, nombre: str) -> dict | None:
    for nodo in workflow.get("nodes", []):
        if nodo.get("name") == nombre:
            return nodo
    return None


def sin_id(nodo: dict) -> dict:
    copia = copy.deepcopy(nodo)
    copia.pop("id", None)
    return copia


def id_nodo(workflow_id: str, nombre: str) -> str:
    """Id determinista para el guardián (mismo nombre -> mismo id)."""
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"ccb-routers-guardian/{workflow_id}/{nombre}"))


def construir_guardian(workflow_id: str) -> dict:
    return {
        "parameters": {"jsCode": JSCODE_GUARDIAN},
        "type": TIPO_GUARDIAN,
        "typeVersion": TYPE_VERSION_GUARDIAN,
        "name": NOMBRE_GUARDIAN,
        "position": list(POS_GUARDIAN),
        "id": id_nodo(workflow_id, NOMBRE_GUARDIAN),
    }


def guardar_respaldo(workflow_id: str, workflow: dict) -> str:
    """Copia cruda del flujo previa al PUT. Nunca sobreescribe un respaldo existente."""
    os.makedirs(RESPALDO_DIR, exist_ok=True)
    ruta = os.path.join(RESPALDO_DIR, f"{workflow_id}.json")
    if os.path.exists(ruta):
        return ruta
    with open(ruta, "w", encoding="utf-8") as handle:
        json.dump(workflow, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    return ruta


def cargar_respaldo(workflow_id: str) -> dict | None:
    ruta = os.path.join(RESPALDO_DIR, f"{workflow_id}.json")
    if not os.path.exists(ruta):
        return None
    with open(ruta, encoding="utf-8") as handle:
        return json.load(handle)


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

    # `description` no puede ser nulo: se omite si no es una cadena no vacía.
    descripcion = workflow.get("description")
    if isinstance(descripcion, str) and descripcion:
        payload["description"] = descripcion

    return payload


def destinos(workflow: dict, origen: str) -> list[str]:
    conexiones = workflow.get("connections") or {}
    return [
        conexion.get("node")
        for grupo in (conexiones.get(origen, {}).get("main") or [])
        for conexion in (grupo or [])
    ]


# --------------------------------------------------------------------- mutación


def mutar(workflow: dict, info: dict) -> tuple[dict, list[str], list[str]]:
    """Aplica (sobre una copia) el guardián y su reconexión.

    Devuelve `(trabajo, pendientes, problemas)`: `trabajo` es el resultado
    objetivo completo (idempotente), `pendientes` describe los cambios que
    faltaban y `problemas` son conflictos inesperados (si hay alguno no se hace
    PUT).
    """
    trabajo = copy.deepcopy(workflow)
    pendientes: list[str] = []
    problemas: list[str] = []

    lectura = info["lectura"]
    nombre_if = info["if"]

    # 1. El nodo guardián.
    modelo = construir_guardian(info["id"])
    actual = buscar_nodo(trabajo, NOMBRE_GUARDIAN)
    if actual is None:
        trabajo.setdefault("nodes", []).append(copy.deepcopy(modelo))
        pendientes.append(f"añadir nodo {NOMBRE_GUARDIAN!r} en {POS_GUARDIAN}")
    elif sin_id(actual) != sin_id(modelo):
        problemas.append(
            f"el nodo {NOMBRE_GUARDIAN!r} ya existe pero no coincide con el esperado; "
            "no se sobreescribe a ciegas"
        )

    # 2. La cadena: lectura -> guardián -> IF.
    conexiones = trabajo.setdefault("connections", {})

    if destinos(trabajo, lectura) != [NOMBRE_GUARDIAN]:
        pendientes.append(
            f"reconectar {lectura!r} -> {NOMBRE_GUARDIAN!r} "
            f"(antes iba a {nombre_if!r})"
        )
    conexiones[lectura] = {
        "main": [[{"node": NOMBRE_GUARDIAN, "type": "main", "index": 0}]]
    }

    if destinos(trabajo, NOMBRE_GUARDIAN) != [nombre_if]:
        pendientes.append(f"conectar {NOMBRE_GUARDIAN!r} -> {nombre_if!r}")
    conexiones[NOMBRE_GUARDIAN] = {
        "main": [[{"node": nombre_if, "type": "main", "index": 0}]]
    }

    return trabajo, pendientes, problemas


# --------------------------------------------------------------- verificación


def proyeccion(workflow: dict) -> dict:
    """Vista comparable del flujo.

    Se descartan los metadatos volátiles que cambian solos y el `id` del nodo
    nuevo (n8n puede reasignarlo al guardarlo). Todo lo demás se compara tal
    cual, de modo que cualquier otro cambio respecto al respaldo es un FALLO.
    """
    resultado = {
        clave: copy.deepcopy(valor)
        for clave, valor in workflow.items()
        if clave not in CLAVES_VOLATILES
    }
    for nodo in resultado.get("nodes", []):
        if nodo.get("name") == NOMBRE_GUARDIAN:
            nodo.pop("id", None)
    return resultado


def verificar(actual: dict, respaldo: dict, info: dict) -> list[str]:
    """Comprueba (a) el guardián y la cadena, y (b) que el resto no cambió."""
    problemas: list[str] = []

    esperado, _pendientes, _problemas = mutar(respaldo, info)

    # (a) el guardián existe y es el nodo esperado.
    guardian = buscar_nodo(actual, NOMBRE_GUARDIAN)
    if guardian is None:
        problemas.append(f"falta el nodo {NOMBRE_GUARDIAN!r} tras el PUT")
    else:
        if guardian.get("name") != NOMBRE_GUARDIAN:
            problemas.append(
                f"el nodo guardián quedó con nombre {guardian.get('name')!r} "
                f"(se esperaba {NOMBRE_GUARDIAN!r})"
            )
        if guardian.get("type") != TIPO_GUARDIAN:
            problemas.append(f"el guardián no es de tipo {TIPO_GUARDIAN!r}")
        if guardian.get("typeVersion") != TYPE_VERSION_GUARDIAN:
            problemas.append(
                f"el guardián tiene typeVersion {guardian.get('typeVersion')!r} "
                f"(se esperaba {TYPE_VERSION_GUARDIAN})"
            )
        if (guardian.get("parameters") or {}).get("jsCode") != JSCODE_GUARDIAN:
            problemas.append("el `jsCode` del guardián no quedó exactamente como se esperaba")

        # la cadena lectura -> guardián -> IF.
        cadena = destinos(actual, info["lectura"])
        if cadena != [NOMBRE_GUARDIAN]:
            problemas.append(
                f"la conexión {info['lectura']!r} -> {NOMBRE_GUARDIAN!r} no quedó: {cadena}"
            )
        salida = destinos(actual, NOMBRE_GUARDIAN)
        if salida != [info["if"]]:
            problemas.append(
                f"la conexión {NOMBRE_GUARDIAN!r} -> {info['if']!r} no quedó: {salida}"
            )

    # (b) nada más cambió respecto al respaldo.
    a = proyeccion(actual)
    e = proyeccion(esperado)
    for clave in sorted(set(a) | set(e)):
        if a.get(clave) != e.get(clave):
            problemas.append(f"el campo {clave!r} cambió respecto al respaldo")

    # (c) conteo de nodos.
    conteo = len(actual.get("nodes", []))
    if conteo != info["nodos_final"]:
        problemas.append(f"el flujo tiene {conteo} nodos (se esperaban {info['nodos_final']})")

    return problemas


# ------------------------------------------------------------------------ salida


def imprimir_plan(entrada: dict) -> None:
    info = entrada["info"]
    print()
    print("=" * 100)
    print(f"PLAN — {info['nombre']} ({info['id']})")
    print("=" * 100)
    if entrada["estado"] == "FALLO" and "pendientes" not in entrada:
        print(f"  FALLO: no se pudo leer el flujo ({entrada.get('tipo')})")
        return
    if not entrada["pendientes"]:
        print(
            "  sin cambios pendientes (ya está en el estado objetivo); "
            f"{len(entrada['workflow'].get('nodes', []))} nodos"
        )
        return
    print(
        f"  nodos: {len(entrada['workflow'].get('nodes', []))} -> "
        f"{len(entrada['trabajo'].get('nodes', []))} (límite 20)"
    )
    for pendiente in entrada["pendientes"]:
        print(f"  - {pendiente}")
    print(f"  guardián {NOMBRE_GUARDIAN!r}: {TIPO_GUARDIAN} v{TYPE_VERSION_GUARDIAN} en {POS_GUARDIAN}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Guardián que descarta las filas de prueba en los 3 routers CCB.",
    )
    modo = parser.add_mutually_exclusive_group()
    modo.add_argument("--dry-run", action="store_true", help="simula sin escribir (por defecto)")
    modo.add_argument("--apply", action="store_true", help="respalda, aplica los PUT y verifica")
    args = parser.parse_args()

    base = os.environ.get("N8N_API_URL", "").rstrip("/")
    key = os.environ.get("N8N_API_KEY", "")
    if not base or not key:
        print("N8N_API_URL y N8N_API_KEY deben estar definidas en el entorno.", file=sys.stderr)
        return 2

    aplicar = args.apply
    fallos = 0

    # ------------------------------------------------------------- Fase A: leer
    # Se leen los tres flujos y se calcula el objetivo. No se escribe nada todavía.
    plan: list[dict] = []
    for info in FLUJOS:
        entrada: dict = {"info": info, "id": info["id"]}
        try:
            actual = fetch(base, key, info["id"])
        except urllib.error.HTTPError as exc:
            cuerpo = exc.read().decode("utf-8", "replace")
            print(f"FALLO GET {info['id']}: HTTP {exc.code}", file=sys.stderr)
            print(f"  cuerpo: {cuerpo}", file=sys.stderr)
            entrada.update({"estado": "FALLO", "tipo": "GET"})
            fallos += 1
            plan.append(entrada)
            continue
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            print(f"FALLO GET {info['id']}: {type(exc).__name__}: {exc}", file=sys.stderr)
            entrada.update({"estado": "FALLO", "tipo": "GET"})
            fallos += 1
            plan.append(entrada)
            continue

        trabajo, pendientes, problemas = mutar(actual, info)
        entrada.update(
            {
                "workflow": actual,
                "trabajo": trabajo,
                "pendientes": pendientes,
                "problemas": problemas,
                "estado": "FALLO" if problemas else "OK",
                "tipo": "MUTACION" if problemas else None,
            }
        )
        if problemas:
            fallos += len(problemas)
        plan.append(entrada)

    for entrada in plan:
        imprimir_plan(entrada)
        for problema in entrada.get("problemas", []):
            print(f"  FALLO: {problema}", file=sys.stderr)

    # --------------------------------------------------------- Fase B: respaldo
    # Antes de cualquier PUT, respaldar (o re-verificar) cada flujo a tocar.
    if aplicar:
        for entrada in plan:
            if entrada["estado"] == "FALLO":
                continue
            ruta = guardar_respaldo(entrada["id"], entrada["workflow"])
            entrada["respaldo"] = ruta
            respaldo = cargar_respaldo(entrada["id"])
            entrada["respaldo_data"] = respaldo
            if respaldo is None:
                print(f"FALLO RESPALDO {entrada['id']}: no se pudo releer {ruta}", file=sys.stderr)
                entrada["estado"] = "FALLO"
                fallos += 1
                continue
            conteo = len(respaldo.get("nodes", []))
            if respaldo.get("id") != entrada["id"] or conteo != entrada["info"]["nodos_respaldo"]:
                print(
                    f"FALLO RESPALDO {entrada['id']}: {ruta} tiene id {respaldo.get('id')!r} y "
                    f"{conteo} nodos (se esperaban {entrada['info']['nodos_respaldo']})",
                    file=sys.stderr,
                )
                entrada["estado"] = "FALLO"
                fallos += 1
                continue
            print(f"\nRESPALDO {entrada['id']}: {ruta} ({conteo} nodos, reverificado)")

    # ------------------------------------------------------------ Fase C: aplicar
    puts = 0
    if aplicar:
        for entrada in plan:
            if entrada["estado"] == "FALLO":
                entrada["estado_final"] = "FALLO"
                continue
            if not entrada["pendientes"]:
                entrada["estado_final"] = "sin cambios"
                continue

            try:
                _status, _cuerpo = enviar_put(
                    base, key, entrada["id"], construir_payload(entrada["trabajo"])
                )
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

            problemas = verificar(verificado, entrada["respaldo_data"], entrada["info"])
            entrada["verificado"] = verificado
            if problemas:
                print(f"FALLO VERIFICACION {entrada['id']}:", file=sys.stderr)
                for problema in problemas:
                    print(f"  - {problema}", file=sys.stderr)
                entrada["estado_final"] = "FALLO"
                fallos += 1
                continue

            entrada["estado_final"] = "APLICADO"

    # ------------------------------------------------------------------ resumen
    print()
    print("=" * 100)
    print("RESUMEN")
    print("=" * 100)
    print(f"{'id':<20}{'flujo':<44}{'nodos':>6}  {'estado':<12}detalle")
    print("-" * 100)
    con_cambios = 0
    for entrada in plan:
        info = entrada["info"]
        conteo = len(entrada["workflow"].get("nodes", []))
        if entrada["estado"] == "FALLO" and "pendientes" not in entrada:
            print(
                f"{entrada['id']:<20}{info['nombre'][:42]:<44}{conteo:>6}  "
                f"{'FALLO':<12}{entrada.get('tipo')}"
            )
            continue
        total = len(entrada["pendientes"])
        if aplicar:
            estado = entrada.get("estado_final", "sin cambios")
            if estado == "APLICADO":
                con_cambios += 1
                detalle = "PUT + verificación OK; resto sin cambios"
            elif estado == "FALLO":
                detalle = "ver ejecución"
            else:
                detalle = "ya estaba aplicado"
        else:
            if entrada["estado"] == "FALLO":
                estado = "FALLO"
                detalle = "conflicto de mutación"
            elif total:
                estado = "PLAN"
                con_cambios += 1
                detalle = f"{len(entrada['trabajo'].get('nodes', []))} nodos finales"
            else:
                estado = "sin cambios"
                detalle = "ya estaba aplicado"
        print(f"{entrada['id']:<20}{info['nombre'][:42]:<44}{conteo:>6}  {estado:<12}{detalle}")

    print()
    print(f"Flujos procesados: {len(plan)}")
    if aplicar:
        print(f"Flujos aplicados: {con_cambios}")
    else:
        print(f"Flujos con cambios planificados: {con_cambios}")
    print(f"PUT enviados: {puts}")
    if not aplicar:
        print("Modo simulación (--dry-run): no se envió ningún PUT ni se escribió ningún respaldo.")
    elif puts == 0:
        print("Sin PUT: todo estaba ya aplicado (idempotente).")

    if fallos:
        print(f"FALLOS: {fallos}", file=sys.stderr)
        return 1

    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
