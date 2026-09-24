#!/usr/bin/env python3
"""Cierra el hueco del correo de alerta silencioso en el subflujo compartido de error.

B5 del plan del 24/09. El subflujo `[SUB] CCB · Error — Registrar y alertar`
(`2dY1kaT7I5a0eP2w`, 6 nodos) registra un error en `Errores_CCB` y avisa por
Outlook. Su nodo `Outlook - Enviar alerta` tenia `onError:
"continueRegularOutput"`, asi que si el envio de la alerta fallaba la ejecucion
terminaba en `success` y nadie se enteraba de que la alerta no salio.

Esta migracion cierra ese hueco con cuatro cambios quirurgicos:

1. `Outlook - Enviar alerta`: `onError` pasa de `"continueRegularOutput"` a
   `"continueErrorOutput"`. No se toca ninguna otra propiedad del nodo.
2. Nodo nuevo `Preparar alerta fallida` (`n8n-nodes-base.code`, v2) con el
   `jsCode` que arma la fila del meta-incidente. Usa `workflow_origen` y
   `nodo_fallido` propios para que el upsert cree su propia fila y NO pise el
   incidente original, que ya quedo registrado aguas arriba.
3. Nodo nuevo `Data Table - Registrar alerta fallida` (`n8n-nodes-base.dataTable`,
   v1.1) con **exactamente** la misma configuracion que `Data Table - Registrar
   error` (misma tabla `Errores_CCB`, `operation=upsert`, `matchType=allConditions`,
   mismos 3 filtros y mismas 5 columnas), mas `onError: "continueRegularOutput"`
   y `alwaysOutputData: true` — igual que su nodo hermano, para que un fallo al
   registrar el meta-incidente no rompa la cadena.
4. Conexiones: la salida 0 (normal) del Outlook sigue yendo a `Devolver item al
   llamador`; la salida 1 (error) entra a `Preparar alerta fallida` -> `Data Table
   - Registrar alerta fallida` -> `Devolver item al llamador`. El ultimo salto es
   obligatorio y deliberado: el subflujo debe seguir devolviendo a sus 13
   llamadores el item normalizado tambien cuando la alerta falla. La rama de error
   no queda como un camino sin salida.

El subflujo pasa de 6 a 8 nodos (limite 20). No se toca ningun otro nodo ni
conexion.

Uso:
    # Simulacion (por defecto): describe el cambio de `onError`, los 2 nodos
    # nuevos y las 3 conexiones nuevas, y no escribe nada.
    python3 scripts/alerta_fallida_visible.py
    python3 scripts/alerta_fallida_visible.py --dry-run

    # Aplicacion real: respalda, hace PUT y verifica contra el respaldo.
    python3 scripts/alerta_fallida_visible.py --apply

Las credenciales se leen solo del entorno (`N8N_API_URL`, `N8N_API_KEY`) y nunca
se imprimen ni se escriben en disco.

Red de seguridad:
  * Antes de cualquier `PUT` se descarga el flujo a
    `/tmp/n8n-backup/b5-alerta-2026-09-24/2dY1kaT7I5a0eP2w.json` y se re-verifica
    leyendolo (6 nodos). Si el respaldo ya existe se conserva: nunca se
    sobreescribe con el estado posterior.
  * Tras el `PUT` se relee el flujo y se comprueba (a) que `Outlook - Enviar
    alerta` quedo con `onError="continueErrorOutput"`, (b) que los 2 nodos nuevos
    quedaron con su `jsCode` y sus columnas exactos, (c) las 4 conexiones —en
    particular que la salida 0 siga yendo a `Devolver item al llamador` y que la
    salida 1 vaya a `Preparar alerta fallida`— y (d) que **nada mas** cambio
    respecto al respaldo, ignorando los metadatos volatiles. Cualquier otra
    diferencia es FALLO y no se esconde.
  * Idempotencia: una segunda corrida de `--apply` no emite ningun `PUT`.

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

# El script hermano tiene las utilidades de red y el filtrado de `settings`.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from renombrar_workflows import (  # noqa: E402
    SETTINGS_SOLO_LECTURA,
    enviar_put,
    fetch,
)

# Respaldo crudo previo a este script (red de seguridad).
RESPALDO_DIR = "/tmp/n8n-backup/b5-alerta-2026-09-24"

# Metadatos volatiles que cambian solos y no se comparan.
CLAVES_VOLATILES = (
    "updatedAt",
    "versionCounter",
    "versionId",
    "activeVersion",
    "activeVersionId",
    "staticData",
)

INFO = {
    "id": "2dY1kaT7I5a0eP2w",
    "nombre": "[SUB] CCB · Error — Registrar y alertar",
    "nodos_respaldo": 6,
    "nodos_final": 8,
}

# Nodos existentes que se tocan / se verifican.
NODO_OUTLOOK = "Outlook - Enviar alerta"
NODO_TABLA_ERROR = "Data Table - Registrar error"
NODO_DEVOLVER = "Devolver item al llamador"

# Nodos nuevos.
NODO_PREPARAR = "Preparar alerta fallida"
NODO_REGISTRAR_ALERTA = "Data Table - Registrar alerta fallida"
NODOS_NUEVOS = (NODO_PREPARAR, NODO_REGISTRAR_ALERTA)

# Cambio de manejo de error del nodo de Outlook.
ONERROR_ANTES = "continueRegularOutput"
ONERROR_DESPUES = "continueErrorOutput"

# Tipos y versiones de los nodos nuevos.
TIPO_CODE = "n8n-nodes-base.code"
TYPE_VERSION_CODE = 2
TIPO_DATA_TABLE = "n8n-nodes-base.dataTable"
TYPE_VERSION_DATA_TABLE = 1.1

# Tabla `Errores_CCB` (solo para la comprobacion explicita de columnas/filtros).
TABLA_ERRORES_ID = "lO46Xkqj0TTedLjI"
COLUMNAS_ESPERADAS = (
    "id_solicitud",
    "workflow_origen",
    "nodo_fallido",
    "mensaje_error",
    "error_timestamp",
)
FILTROS_ESPERADOS = ("id_solicitud", "workflow_origen", "nodo_fallido")

# Posiciones nuevas, por debajo de la linea principal (y=0), sin solapar a nadie.
POS_PREPARAR = [240, 220]
POS_REGISTRAR_ALERTA = [464, 220]

# `jsCode` exacto de `Preparar alerta fallida`.
JSCODE_PREPARAR = """// B5: una alerta que NO se pudo enviar es un incidente por si misma. El nodo de Outlook tenia
// onError=continueRegularOutput, asi que un fallo de envio se perdia en silencio: el flujo que
// fallaba terminaba en 'success' y nadie se enteraba de que la alerta no salio.
// Se registra con claves propias (workflow_origen y nodo_fallido distintos) para que el upsert
// cree su propia fila y NO pise el incidente original, que ya quedo registrado aguas arriba.
const ent = (() => { try { return $('Normalizar entrada de error').first().json || {}; } catch (e) { return {}; } })();
const err = ($json && $json.error) ? $json.error : ($json || {});
const detalle = (err && (err.message || err.description)) || JSON.stringify(err || {}) || 'Error sin mensaje';
return { json: {
  id_solicitud: ent.id_solicitud || '(sin id)',
  workflow_origen: 'alerta-error',
  nodo_fallido: 'Outlook - Enviar alerta (envío fallido)',
  mensaje_error: 'La alerta de error no se pudo enviar por Outlook: ' + String(detalle).slice(0, 240),
  error_timestamp: $now.setZone('America/Bogota').toFormat('yyyy-MM-dd HH:mm:ss'),
} };"""


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


def salidas(workflow: dict, origen: str) -> list[list[str]]:
    """Destinos por salida `main` del nodo (indice = salida)."""
    grupos = (workflow.get("connections") or {}).get(origen, {}).get("main") or []
    return [[conexion.get("node") for conexion in (grupo or [])] for grupo in grupos]


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

    # `description` no puede ser nulo: se omite si no es una cadena no vacia.
    descripcion = workflow.get("description")
    if isinstance(descripcion, str) and descripcion:
        payload["description"] = descripcion

    return payload


# ------------------------------------------------------------------ nodos nuevos


def construir_preparar_alerta_fallida() -> dict:
    return {
        "parameters": {"jsCode": JSCODE_PREPARAR},
        "type": TIPO_CODE,
        "typeVersion": TYPE_VERSION_CODE,
        "name": NODO_PREPARAR,
        "position": list(POS_PREPARAR),
        "id": "sub-error-preparar-alerta-fallida",
    }


def construir_registrar_alerta_fallida(workflow: dict) -> dict | None:
    """Copia la configuracion de `Data Table - Registrar error` para su nodo hermano.

    Devuelve `None` si no existe el nodo hermano del que copiar.
    """
    hermano = buscar_nodo(workflow, NODO_TABLA_ERROR)
    if hermano is None:
        return None
    return {
        "parameters": copy.deepcopy(hermano.get("parameters") or {}),
        "type": TIPO_DATA_TABLE,
        "typeVersion": TYPE_VERSION_DATA_TABLE,
        "name": NODO_REGISTRAR_ALERTA,
        "position": list(POS_REGISTRAR_ALERTA),
        "id": "sub-error-registrar-alerta-fallida",
        "alwaysOutputData": True,
        "onError": ONERROR_ANTES,
    }


# --------------------------------------------------------------------- mutacion


def mutar(workflow: dict) -> tuple[dict, list[str], list[str]]:
    """Aplica (sobre una copia) los 4 cambios y describe el resultado.

    Devuelve `(trabajo, pendientes, problemas)`: `trabajo` es el resultado objetivo
    completo (idempotente), `pendientes` describe los cambios que faltaban y
    `problemas` son conflictos inesperados (si hay alguno no se hace PUT).
    """
    trabajo = copy.deepcopy(workflow)
    pendientes: list[str] = []
    problemas: list[str] = []

    # 1. `onError` del nodo de Outlook.
    outlook = buscar_nodo(trabajo, NODO_OUTLOOK)
    if outlook is None:
        problemas.append(f"no se encontro el nodo {NODO_OUTLOOK!r}")
    else:
        onerror = outlook.get("onError")
        if onerror == ONERROR_ANTES:
            outlook["onError"] = ONERROR_DESPUES
            pendientes.append(
                f"cambiar `onError` de {NODO_OUTLOOK!r}: {ONERROR_ANTES} -> {ONERROR_DESPUES}"
            )
        elif onerror != ONERROR_DESPUES:
            problemas.append(
                f"el nodo {NODO_OUTLOOK!r} tiene un `onError` inesperado "
                f"({onerror!r}); no se sobreescribe a ciegas"
            )

    # 2. Nodo nuevo `Preparar alerta fallida`.
    modelo_preparar = construir_preparar_alerta_fallida()
    actual_preparar = buscar_nodo(trabajo, NODO_PREPARAR)
    if actual_preparar is None:
        trabajo.setdefault("nodes", []).append(copy.deepcopy(modelo_preparar))
        pendientes.append(
            f"anadir nodo {NODO_PREPARAR!r} ({TIPO_CODE} v{TYPE_VERSION_CODE}) "
            f"en {POS_PREPARAR}"
        )
    elif sin_id(actual_preparar) != sin_id(modelo_preparar):
        problemas.append(
            f"el nodo {NODO_PREPARAR!r} ya existe pero no coincide con el esperado; "
            "no se sobreescribe a ciegas"
        )

    # 3. Nodo nuevo `Data Table - Registrar alerta fallida` (copia de su hermano).
    modelo_tabla = construir_registrar_alerta_fallida(trabajo)
    if modelo_tabla is None:
        problemas.append(
            f"no se encontro {NODO_TABLA_ERROR!r} para copiar su configuracion "
            f"al nodo {NODO_REGISTRAR_ALERTA!r}"
        )
    else:
        actual_tabla = buscar_nodo(trabajo, NODO_REGISTRAR_ALERTA)
        if actual_tabla is None:
            trabajo.setdefault("nodes", []).append(copy.deepcopy(modelo_tabla))
            pendientes.append(
                f"anadir nodo {NODO_REGISTRAR_ALERTA!r} "
                f"({TIPO_DATA_TABLE} v{TYPE_VERSION_DATA_TABLE}) en {POS_REGISTRAR_ALERTA} "
                "(misma configuracion que "
                f"{NODO_TABLA_ERROR!r})"
            )
        elif sin_id(actual_tabla) != sin_id(modelo_tabla):
            problemas.append(
                f"el nodo {NODO_REGISTRAR_ALERTA!r} ya existe pero no coincide con el "
                "esperado; no se sobreescribe a ciegas"
            )

    # 4. Conexiones. La salida 0 del Outlook no cambia; la 1 se abre a la rama nueva.
    conexiones = trabajo.setdefault("connections", {})

    salidas_outlook = salidas(trabajo, NODO_OUTLOOK)
    salida0 = salidas_outlook[0] if len(salidas_outlook) > 0 else None
    salida1 = salidas_outlook[1] if len(salidas_outlook) > 1 else None

    if salida0 != [NODO_DEVOLVER]:
        pendientes.append(
            f"restaurar conexion {NODO_OUTLOOK!r} salida 0 -> {NODO_DEVOLVER!r} "
            f"(estaba en {salida0})"
        )
    if salida1 != [NODO_PREPARAR]:
        pendientes.append(
            f"conectar {NODO_OUTLOOK!r} salida 1 (error) -> {NODO_PREPARAR!r}"
        )
    conexiones[NODO_OUTLOOK] = {
        "main": [
            [{"node": NODO_DEVOLVER, "type": "main", "index": 0}],
            [{"node": NODO_PREPARAR, "type": "main", "index": 0}],
        ]
    }

    if salidas(trabajo, NODO_PREPARAR) != [[NODO_REGISTRAR_ALERTA]]:
        pendientes.append(f"conectar {NODO_PREPARAR!r} -> {NODO_REGISTRAR_ALERTA!r}")
    conexiones[NODO_PREPARAR] = {
        "main": [[{"node": NODO_REGISTRAR_ALERTA, "type": "main", "index": 0}]]
    }

    if salidas(trabajo, NODO_REGISTRAR_ALERTA) != [[NODO_DEVOLVER]]:
        pendientes.append(
            f"conectar {NODO_REGISTRAR_ALERTA!r} -> {NODO_DEVOLVER!r} "
            "(la rama de error tambien devuelve el item al llamador)"
        )
    conexiones[NODO_REGISTRAR_ALERTA] = {
        "main": [[{"node": NODO_DEVOLVER, "type": "main", "index": 0}]]
    }

    return trabajo, pendientes, problemas


# --------------------------------------------------------------- verificacion


def proyeccion(workflow: dict) -> dict:
    """Vista comparable del flujo.

    Se descartan los metadatos volatiles que cambian solos y el `id` de los nodos
    nuevos (n8n puede reasignarlo al guardarlos). Los nodos se ordenan por nombre
    para no fallar por un reordenamiento sin significado. Todo lo demas se compara
    tal cual: cualquier otro cambio respecto al respaldo es un FALLO.
    """
    vista = {
        clave: copy.deepcopy(valor)
        for clave, valor in workflow.items()
        if clave not in CLAVES_VOLATILES
    }
    nodos = vista.get("nodes", [])
    for nodo in nodos:
        if nodo.get("name") in NODOS_NUEVOS:
            nodo.pop("id", None)
    nodos.sort(key=lambda nodo: nodo.get("name") or "")
    return vista


def verificar(actual: dict, respaldo: dict) -> list[str]:
    """Comprueba (a) `onError`, (b) nodos nuevos, (c) conexiones y (d) el resto."""
    problemas: list[str] = []

    esperado, _pendientes, _problemas = mutar(respaldo)

    # (a) `onError` del nodo de Outlook.
    outlook = buscar_nodo(actual, NODO_OUTLOOK)
    if outlook is None:
        problemas.append(f"falta el nodo {NODO_OUTLOOK!r} tras el PUT")
    elif outlook.get("onError") != ONERROR_DESPUES:
        problemas.append(
            f"{NODO_OUTLOOK!r} quedo con `onError` {outlook.get('onError')!r} "
            f"(se esperaba {ONERROR_DESPUES!r})"
        )

    # (b) los 2 nodos nuevos, exactamente como se esperaban.
    for nombre in NODOS_NUEVOS:
        actual_nodo = buscar_nodo(actual, nombre)
        esperado_nodo = buscar_nodo(esperado, nombre)
        if actual_nodo is None:
            problemas.append(f"falta el nodo {nombre!r} tras el PUT")
        elif esperado_nodo is not None and sin_id(actual_nodo) != sin_id(esperado_nodo):
            problemas.append(
                f"el nodo {nombre!r} no quedo exactamente como se esperaba "
                "(tipo, typeVersion, parametros, posicion u onError)"
            )

    preparar = buscar_nodo(actual, NODO_PREPARAR)
    if preparar is not None:
        if (preparar.get("parameters") or {}).get("jsCode") != JSCODE_PREPARAR:
            problemas.append("el `jsCode` de `Preparar alerta fallida` no quedo exacto")

    tabla = buscar_nodo(actual, NODO_REGISTRAR_ALERTA)
    if tabla is not None:
        parametros = tabla.get("parameters") or {}
        columnas = ((parametros.get("columns") or {}).get("value")) or {}
        if set(columnas) != set(COLUMNAS_ESPERADAS):
            problemas.append(
                f"las columnas de {NODO_REGISTRAR_ALERTA!r} no son las 5 esperadas: "
                f"{sorted(columnas)}"
            )
        condiciones = (parametros.get("filters") or {}).get("conditions") or []
        if [condicion.get("keyName") for condicion in condiciones] != list(FILTROS_ESPERADOS):
            problemas.append(
                f"los filtros de {NODO_REGISTRAR_ALERTA!r} no son los 3 esperados: "
                f"{[c.get('keyName') for c in condiciones]}"
            )
        if (parametros.get("dataTableId") or {}).get("value") != TABLA_ERRORES_ID:
            problemas.append(f"{NODO_REGISTRAR_ALERTA!r} no apunta a la tabla `Errores_CCB`")
        if parametros.get("operation") != "upsert":
            problemas.append(f"{NODO_REGISTRAR_ALERTA!r} no quedo con `operation=upsert`")
        if parametros.get("matchType") != "allConditions":
            problemas.append(f"{NODO_REGISTRAR_ALERTA!r} no quedo con `matchType=allConditions`")
        if tabla.get("onError") != ONERROR_ANTES:
            problemas.append(
                f"{NODO_REGISTRAR_ALERTA!r} no quedo con `onError={ONERROR_ANTES}`"
            )
        if tabla.get("alwaysOutputData") is not True:
            problemas.append(f"{NODO_REGISTRAR_ALERTA!r} no quedo con `alwaysOutputData=true`")

    # (c) las 4 conexiones.
    salidas_outlook = salidas(actual, NODO_OUTLOOK)
    if len(salidas_outlook) != 2:
        problemas.append(
            f"{NODO_OUTLOOK!r} tiene {len(salidas_outlook)} salidas (se esperaban 2)"
        )
    else:
        if salidas_outlook[0] != [NODO_DEVOLVER]:
            problemas.append(
                f"la salida 0 de {NODO_OUTLOOK!r} no va a {NODO_DEVOLVER!r}: "
                f"{salidas_outlook[0]}"
            )
        if salidas_outlook[1] != [NODO_PREPARAR]:
            problemas.append(
                f"la salida 1 (error) de {NODO_OUTLOOK!r} no va a {NODO_PREPARAR!r}: "
                f"{salidas_outlook[1]}"
            )
    if salidas(actual, NODO_PREPARAR) != [[NODO_REGISTRAR_ALERTA]]:
        problemas.append(
            f"la conexion {NODO_PREPARAR!r} -> {NODO_REGISTRAR_ALERTA!r} no quedo: "
            f"{salidas(actual, NODO_PREPARAR)}"
        )
    if salidas(actual, NODO_REGISTRAR_ALERTA) != [[NODO_DEVOLVER]]:
        problemas.append(
            f"la conexion {NODO_REGISTRAR_ALERTA!r} -> {NODO_DEVOLVER!r} no quedo: "
            f"{salidas(actual, NODO_REGISTRAR_ALERTA)}"
        )

    # (d) nada mas cambio respecto al respaldo.
    a = proyeccion(actual)
    e = proyeccion(esperado)
    for clave in sorted(set(a) | set(e)):
        if a.get(clave) != e.get(clave):
            problemas.append(f"el campo {clave!r} cambio respecto al respaldo")

    # (e) conteo de nodos.
    conteo = len(actual.get("nodes", []))
    if conteo != INFO["nodos_final"]:
        problemas.append(f"el flujo tiene {conteo} nodos (se esperaban {INFO['nodos_final']})")

    return problemas


# ------------------------------------------------------------------------ salida


def _corto(texto: str, limite: int = 150) -> str:
    plano = " ".join(texto.split())
    return plano if len(plano) <= limite else plano[: limite - 1] + "…"


def imprimir_plan(entrada: dict) -> None:
    info = entrada["info"]
    print()
    print("=" * 100)
    print(f"PLAN — {info['nombre']} ({info['id']})")
    print("=" * 100)
    if entrada["estado"] == "FALLO" and "pendientes" not in entrada:
        print(f"  FALLO: no se pudo leer el flujo ({entrada.get('tipo')})")
        return
    print(
        f"  nodos: {len(entrada['workflow'].get('nodes', []))} -> "
        f"{len(entrada['trabajo'].get('nodes', []))} (límite 20)"
    )
    if not entrada["pendientes"]:
        print("  sin cambios pendientes (ya está en el estado objetivo)")
    for pendiente in entrada["pendientes"]:
        print(f"  - {pendiente}")

    print()
    print(f"  Nodo nuevo {NODO_PREPARAR!r}: {TIPO_CODE} v{TYPE_VERSION_CODE} en {POS_PREPARAR}")
    for linea in JSCODE_PREPARAR.splitlines():
        print(f"      {linea}")
    print()
    print(
        f"  Nodo nuevo {NODO_REGISTRAR_ALERTA!r}: {TIPO_DATA_TABLE} "
        f"v{TYPE_VERSION_DATA_TABLE} en {POS_REGISTRAR_ALERTA}"
    )
    print(
        f"      operación=upsert · matchType=allConditions · tabla Errores_CCB "
        f"({TABLA_ERRORES_ID})"
    )
    print(f"      filtros: {', '.join(FILTROS_ESPERADOS)}")
    print(f"      columnas: {', '.join(COLUMNAS_ESPERADAS)}")
    print(f"      onError={ONERROR_ANTES} · alwaysOutputData=true")

    print()
    print("  Conexiones objetivo:")
    print(f"      {NODO_OUTLOOK!r} salida 0 (main) -> {NODO_DEVOLVER!r} (sin cambios)")
    print(f"      {NODO_OUTLOOK!r} salida 1 (error) -> {NODO_PREPARAR!r}")
    print(f"      {NODO_PREPARAR!r} -> {NODO_REGISTRAR_ALERTA!r}")
    print(f"      {NODO_REGISTRAR_ALERTA!r} -> {NODO_DEVOLVER!r}")

    for problema in entrada["problemas"]:
        print(f"  FALLO: {problema}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Cierra el hueco del correo de alerta silencioso (B5) en el subflujo de error.",
    )
    modo = parser.add_mutually_exclusive_group()
    modo.add_argument("--dry-run", action="store_true", help="simula sin escribir (por defecto)")
    modo.add_argument("--apply", action="store_true", help="respalda, aplica el PUT y verifica")
    args = parser.parse_args()

    base = os.environ.get("N8N_API_URL", "").rstrip("/")
    key = os.environ.get("N8N_API_KEY", "")
    if not base or not key:
        print("N8N_API_URL y N8N_API_KEY deben estar definidas en el entorno.", file=sys.stderr)
        return 2

    aplicar = args.apply
    fallos = 0

    # ------------------------------------------------------------- Fase A: leer
    # Se lee el flujo y se calcula el objetivo. No se escribe nada todavia.
    entrada: dict = {"info": INFO, "id": INFO["id"]}
    try:
        actual = fetch(base, key, INFO["id"])
    except urllib.error.HTTPError as exc:
        cuerpo = exc.read().decode("utf-8", "replace")
        print(f"FALLO GET {INFO['id']}: HTTP {exc.code}", file=sys.stderr)
        print(f"  cuerpo: {cuerpo}", file=sys.stderr)
        entrada.update({"estado": "FALLO", "tipo": "GET"})
        fallos += 1
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        print(f"FALLO GET {INFO['id']}: {type(exc).__name__}: {exc}", file=sys.stderr)
        entrada.update({"estado": "FALLO", "tipo": "GET"})
        fallos += 1
    else:
        trabajo, pendientes, problemas = mutar(actual)
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

    imprimir_plan(entrada)
    for problema in entrada.get("problemas", []):
        print(f"  FALLO: {problema}", file=sys.stderr)

    # --------------------------------------------------------- Fase B: respaldo
    # Antes de cualquier PUT, respaldar (o re-verificar) el flujo a tocar.
    respaldo_data = None
    if aplicar and entrada["estado"] != "FALLO":
        ruta = guardar_respaldo(entrada["id"], entrada["workflow"])
        entrada["respaldo"] = ruta
        respaldo_data = cargar_respaldo(entrada["id"])
        conteo = len(respaldo_data.get("nodes", [])) if respaldo_data else 0
        if respaldo_data is None or respaldo_data.get("id") != INFO["id"] or conteo != INFO["nodos_respaldo"]:
            print(
                f"FALLO RESPALDO {entrada['id']}: {ruta} tiene id "
                f"{respaldo_data.get('id') if respaldo_data else None!r} y {conteo} nodos "
                f"(se esperaban {INFO['nodos_respaldo']})",
                file=sys.stderr,
            )
            entrada["estado"] = "FALLO"
            fallos += 1
        else:
            print(f"\nRESPALDO {entrada['id']}: {ruta} ({conteo} nodos, reverificado)")

    # ------------------------------------------------------------ Fase C: aplicar
    puts = 0
    estado_final = None
    if aplicar and entrada["estado"] != "FALLO":
        if not entrada["pendientes"]:
            estado_final = "sin cambios"
        else:
            try:
                _status, _cuerpo = enviar_put(
                    base, key, entrada["id"], construir_payload(entrada["trabajo"])
                )
            except urllib.error.HTTPError as exc:
                cuerpo = exc.read().decode("utf-8", "replace")
                print(f"FALLO PUT {entrada['id']}: HTTP {exc.code}", file=sys.stderr)
                print(f"  cuerpo: {cuerpo}", file=sys.stderr)
                estado_final = "FALLO"
                fallos += 1
            except (urllib.error.URLError, TimeoutError, OSError) as exc:
                print(f"FALLO PUT {entrada['id']}: {type(exc).__name__}: {exc}", file=sys.stderr)
                estado_final = "FALLO"
                fallos += 1
            else:
                puts += 1
                try:
                    verificado = fetch(base, key, entrada["id"])
                except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError) as exc:
                    print(
                        f"FALLO VERIFICACION {entrada['id']}: no se pudo releer "
                        f"({type(exc).__name__}: {exc})",
                        file=sys.stderr,
                    )
                    estado_final = "FALLO"
                    fallos += 1
                else:
                    entrada["verificado"] = verificado
                    problemas = verificar(verificado, respaldo_data)
                    if problemas:
                        print(f"FALLO VERIFICACION {entrada['id']}:", file=sys.stderr)
                        for problema in problemas:
                            print(f"  - {problema}", file=sys.stderr)
                        estado_final = "FALLO"
                        fallos += 1
                    else:
                        estado_final = "APLICADO"
    elif aplicar:
        estado_final = "FALLO"

    # ------------------------------------------------------------------ resumen
    print()
    print("=" * 100)
    print("RESUMEN")
    print("=" * 100)
    print(f"{'id':<20}{'flujo':<44}{'nodos':>6}  {'estado':<12}detalle")
    print("-" * 100)
    if entrada["estado"] == "FALLO" and "pendientes" not in entrada:
        print(
            f"{entrada['id']:<20}{INFO['nombre'][:42]:<44}{0:>6}  {'FALLO':<12}{entrada.get('tipo')}"
        )
    else:
        conteo = len(entrada["workflow"].get("nodes", []))
        if aplicar:
            estado = estado_final or "FALLO"
            if estado == "APLICADO":
                detalle = "PUT + verificación OK; resto sin cambios"
            elif estado == "FALLO":
                detalle = "ver ejecución"
            else:
                detalle = "ya estaba aplicado"
        elif entrada["estado"] == "FALLO":
            estado = "FALLO"
            detalle = "conflicto de mutación"
        elif entrada["pendientes"]:
            estado = "PLAN"
            detalle = f"{len(entrada['trabajo'].get('nodes', []))} nodos finales"
        else:
            estado = "sin cambios"
            detalle = "ya estaba aplicado"
        print(f"{entrada['id']:<20}{INFO['nombre'][:42]:<44}{conteo:>6}  {estado:<12}{detalle}")

    print()
    print(f"Flujos procesados: 1")
    if aplicar:
        print(f"Flujos aplicados: {1 if estado_final == 'APLICADO' else 0}")
    else:
        print(f"Flujos con cambios planificados: {1 if entrada.get('pendientes') else 0}")
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
