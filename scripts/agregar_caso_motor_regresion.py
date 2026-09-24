#!/usr/bin/env python3
"""Añade el sexto caso (el del motor) a la regresión del pipeline CCB.

Dos cambios acotados, verificados contra la instancia viva el 24/09:

1. `[OPS] CCB · Regresión — Prueba de regresión` (`GVE3iNQ80y5Q9FEw`): se
   intercalan dos nodos entre `Ejecutar Cerrar envio` y `Ejecutar Verificar y
   limpiar`:

       Ejecutar Cerrar envio -> Preparar caso motor -> Ejecutar Motor -> Ejecutar Verificar y limpiar

   `Preparar caso motor` (`code`, `executeOnce`) emite un item con el contrato
   del motor, copiado de una propuesta real que funcionó
   (`SOL-20260916134302`), e `id_solicitud = 'SOL-PRUEBA-REGRESION-MOTOR'`.
   `Ejecutar Motor` (`executeWorkflow`) invoca
   `[SUB] CCB · Motor — Invocar el motor y guardar` (`MHWlUApSFT6gpBHs`), el
   mismo patrón que su llamador real en W2A. El flujo pasa de 16 a 18 nodos
   (límite 20). `Ejecutar Verificar y limpiar` se desplaza a `[2600, 0]` porque
   `[2160, 0]` es la posición del nodo nuevo; no se mueve nada más.

2. `[SUB] CCB · Regresión — Verificar y limpiar` (`OuE4SS9Jujz1dVif`):
   * `Comparar resultados` recibe una sexta entrada en el arreglo `casos` y una
     rama `motor` que comprueba el ESTADO REAL en las tablas
     (`estado = 'PROPUESTA_GENERADA'`, `total_registros > 0`, `valor_total > 0`,
     `fecha_calculo`, `pdf_url` y ausencia de fila en `Errores_CCB`). El `X/Y`
     del semáforo se deriva de `filas.length`, así que el `6/6` sale solo.
   * `Data Table - Limpiar cotizaciones` y `Data Table - Limpiar errores` pasan
     a `matchType: 'anyCondition'` con una segunda condición: el motor escribe
     `Cotizaciones_CCB.servicio` con el valor canónico (con tilde, necesario
     para el `Switch` del PDF) y, si falla, registra en `Errores_CCB` con
     `id_solicitud = 'SOL-PRUEBA-REGRESION-MOTOR'`; el filtro viejo no borraba
     ninguno de los dos.
   El subflujo queda en 11 nodos (no se añade ninguno).

Uso:
    # Simulación (por defecto): describe los cambios y no escribe nada.
    python3 scripts/agregar_caso_motor_regresion.py
    python3 scripts/agregar_caso_motor_regresion.py --dry-run

    # Aplicación real: respalda, hace PUT y verifica contra el respaldo.
    python3 scripts/agregar_caso_motor_regresion.py --apply

Las credenciales se leen solo del entorno (`N8N_API_URL`, `N8N_API_KEY`) y nunca
se imprimen ni se escriben en disco.

Red de seguridad:
  * Antes de cualquier `PUT` se descarga cada flujo a
    `/tmp/n8n-backup/caso-motor-2026-09-24/<id>.json` y se re-verifica leyéndolo
    (16 nodos el principal, 11 el subflujo). Si el respaldo ya existe, se
    conserva: nunca se sobreescribe con el estado posterior.
  * Tras cada `PUT` se relee el flujo y se compara contra el resultado esperado
    derivado del respaldo. Se ignoran los metadatos volátiles que cambian solos
    (`updatedAt`, `versionCounter`, `versionId`, `activeVersion*` y
    `staticData`). Cualquier otra diferencia es FALLO y no se esconde.
  * Idempotencia: una segunda corrida de `--apply` no emite ningún `PUT`.

Solo se modifica el `nodes` y el `connections` de nivel superior.
`activeVersion.nodes` es historial interno de n8n y no se toca.

No se tocan los otros 5 casos de la regresión, ni
`[SUB] CCB · Regresión — Preparar filas` (`DgUfcoudk228kOw8`, el caso del motor
no se siembra), ni W3, ni el subflujo del motor, ni el subflujo de PDF, ni el
`Schedule - Regresion semanal`, ni la activación de los flujos.
"""
from __future__ import annotations

import argparse
import copy
import json
import os
import sys
import urllib.error
import uuid

# El script hermano tiene las utilidades de red y los settings de solo lectura.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from renombrar_workflows import (  # noqa: E402
    SETTINGS_SOLO_LECTURA,
    enviar_put,
    fetch,
)

# Respaldo crudo previo a este script (red de seguridad).
RESPALDO_DIR = "/tmp/n8n-backup/caso-motor-2026-09-24"

# Flujo principal y subflujo de verificación y limpieza.
FLUJO_PRINCIPAL = {
    "id": "GVE3iNQ80y5Q9FEw",
    "nombre": "[OPS] CCB · Regresión — Prueba de regresión",
    "nodos_respaldo": 16,
    "nodos_final": 18,
}
SUBFLUJO = {
    "id": "OuE4SS9Jujz1dVif",
    "nombre": "[SUB] CCB · Regresión — Verificar y limpiar",
    "nodos_respaldo": 11,
    "nodos_final": 11,
}
FLUJOS = [FLUJO_PRINCIPAL, SUBFLUJO]

# Metadatos volátiles que cambian solos y no se comparan.
CLAVES_VOLATILES = (
    "updatedAt",
    "versionCounter",
    "versionId",
    "activeVersion",
    "activeVersionId",
    "staticData",
)

# ---------------------------------------------------------------- flujo principal

NOMBRE_CERRAR = "Ejecutar Cerrar envio"
NOMBRE_PREPARAR = "Preparar caso motor"
NOMBRE_EJECUTAR = "Ejecutar Motor"
NOMBRE_VERIFICAR = "Ejecutar Verificar y limpiar"

# Posiciones (el lienzo avanza de 220 en 220 en esta zona).
POS_PREPARAR = [2160, 0]
POS_EJECUTAR = [2380, 0]
# `Ejecutar Verificar y limpiar` estaba en [2160, 0]; se desplaza a la siguiente.
POS_VERIFICAR = [2600, 0]

# Subflujo del motor que se invoca (mismo valor que usa W2A, su llamador real).
MOTOR_ID = "MHWlUApSFT6gpBHs"
MOTOR_NOMBRE = "[SUB] CCB · Motor — Invocar el motor y guardar"

# Contrato del motor, copiado de una propuesta real que funcionó
# (`SOL-20260916134302`). Sin `total_registros`: usarlo saltaría el filtrado
# contra la planilla Excel y haría el test más débil. `servicio` lleva tilde
# porque el `Switch` del subflujo de PDF compara exacto y sensible a tildes.
JSCODE_PREPARAR = """return [{ json: {
  id_solicitud: 'SOL-PRUEBA-REGRESION-MOTOR',
  servicio: 'Información Georreferenciada',
  tipo_servicio: 'Georreferenciada',
  tipo_organizacion: 'Personas Jurídicas; Personas Naturales; Establecimientos; Entidades sin ánimo de lucro',
  municipios: 'Todo el Departamento del Atlántico',
  sectores: 'Comercio al por mayor y al por menor',
  tamano_empresa: 'Microempresas; Pequeñas empresas; Medianas empresas; Grandes empresas',
  indiferente_ventas: true,
  nombre_solicitante: 'Solicitante de prueba',
  razon_social: 'Empresa de prueba',
  email_solicitante: 'pruebas@ejemplo.test',
  telefono_solicitante: '3000000000',
  ciudad: 'Barranquilla',
} }];"""


def id_nodo(workflow_id: str, nombre: str) -> str:
    """Id determinista para un nodo nuevo (mismo nombre -> mismo id)."""
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"ccb-regresion-caso-motor/{workflow_id}/{nombre}"))


def construir_nodo_preparar() -> dict:
    return {
        "parameters": {"jsCode": JSCODE_PREPARAR},
        "type": "n8n-nodes-base.code",
        "typeVersion": 2,
        "name": NOMBRE_PREPARAR,
        "position": list(POS_PREPARAR),
        "executeOnce": True,
        "id": id_nodo(FLUJO_PRINCIPAL["id"], NOMBRE_PREPARAR),
    }


def construir_nodo_ejecutar() -> dict:
    return {
        "parameters": {
            "workflowId": {
                "__rl": True,
                "value": MOTOR_ID,
                "mode": "id",
                "cachedResultName": MOTOR_NOMBRE,
            },
            "options": {"waitForSubWorkflow": True},
        },
        "type": "n8n-nodes-base.executeWorkflow",
        "typeVersion": 1.2,
        "name": NOMBRE_EJECUTAR,
        "position": list(POS_EJECUTAR),
        "id": id_nodo(FLUJO_PRINCIPAL["id"], NOMBRE_EJECUTAR),
    }


# --------------------------------------------------------------------- subflujo

NOMBRE_COMPARAR = "Comparar resultados"

# Las dos ediciones literales de `parameters.jsCode`. Cada una trae un
# `marcador` (presente solo cuando la edición ya se aplicó) y un ancla exacta
# (`antes`) que debe aparecer una única vez en el estado original.
EDICIONES_JSCODE = [
    {
        "descripcion": "sexta entrada del arreglo `casos`",
        "marcador": "  { caso: 'motor',    id: 'SOL-PRUEBA-REGRESION-MOTOR',    "
        "esperado: 'PROPUESTA_GENERADA con total_registros>0, valor_total>0 y pdf_url' },\n",
        "antes": "  esperado: 'ENVIADA en cotizacion y solicitud' },\n];",
        "despues": "  esperado: 'ENVIADA en cotizacion y solicitud' },\n"
        "  { caso: 'motor',    id: 'SOL-PRUEBA-REGRESION-MOTOR',    "
        "esperado: 'PROPUESTA_GENERADA con total_registros>0, valor_total>0 y pdf_url' },\n"
        "];",
    },
    {
        "descripcion": "rama `motor` dentro del `map` de `filas`",
        "marcador": "  if (c.caso === 'motor') {\n",
        "antes": "  }\n"
        "  return { caso: c.caso, esperado: c.esperado, obtenido: r.estado || '(sin fila)', "
        "ok: r.estado === c.esperado };",
        "despues": "  }\n"
        "  if (c.caso === 'motor') {\n"
        "    const r = cot.find((x) => x.id_solicitud === c.id) || {};\n"
        "    const conError = err.some((e) => e.id_solicitud === c.id);\n"
        "    const total = Number(r.total_registros);\n"
        "    const valor = Number(r.valor_total);\n"
        "    const ok = r.estado === 'PROPUESTA_GENERADA' && total > 0 && valor > 0 && "
        "!!r.fecha_calculo && !!r.pdf_url && !conError;\n"
        "    const partes = [\n"
        "      'cotizacion ' + (r.estado || '(sin fila)'),\n"
        "      'total ' + (Number.isFinite(total) ? total : '(sin dato)'),\n"
        "      'valor_total ' + (Number.isFinite(valor) ? valor : '(sin dato)'),\n"
        "      'pdf ' + (r.pdf_url ? 'si' : 'no'),\n"
        "    ];\n"
        "    if (conError) partes.push('ERROR registrado en Errores_CCB');\n"
        "    return { caso: c.caso, esperado: c.esperado, obtenido: partes.join(' / '), ok };\n"
        "  }\n"
        "  return { caso: c.caso, esperado: c.esperado, obtenido: r.estado || '(sin fila)', "
        "ok: r.estado === c.esperado };",
    },
]

# Estado original y objetivo de los dos `deleteRows` que cambian de filtro.
# Solo se tocan `matchType` y `filters`; el resto de la configuración
# (`operation`, `dataTableId`, posición, etc.) queda intacto.
LIMPIEZA = {
    "Data Table - Limpiar cotizaciones": {
        "antes": {
            "matchType": "allConditions",
            "filters": {"conditions": [{"keyName": "servicio", "keyValue": "SOL-PRUEBA-REGRESION"}]},
        },
        "despues": {
            "matchType": "anyCondition",
            "filters": {
                "conditions": [
                    {"keyName": "servicio", "keyValue": "SOL-PRUEBA-REGRESION"},
                    {"keyName": "id_solicitud", "keyValue": "SOL-PRUEBA-REGRESION-MOTOR"},
                ]
            },
        },
    },
    "Data Table - Limpiar errores": {
        "antes": {
            "matchType": "allConditions",
            "filters": {
                "conditions": [
                    {"keyName": "id_solicitud", "keyValue": "SOL-PRUEBA-REGRESION-ERROR"}
                ]
            },
        },
        "despues": {
            "matchType": "anyCondition",
            "filters": {
                "conditions": [
                    {"keyName": "id_solicitud", "keyValue": "SOL-PRUEBA-REGRESION-ERROR"},
                    {"keyName": "id_solicitud", "keyValue": "SOL-PRUEBA-REGRESION-MOTOR"},
                ]
            },
        },
    },
}

# Campos de los nodos nuevos cuyo `id` no se compara (n8n puede reasignarlo).
NODOS_NUEVOS = (NOMBRE_PREPARAR, NOMBRE_EJECUTAR)


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


def proyeccion(workflow: dict) -> dict:
    """Vista comparable del flujo.

    Se descartan los metadatos volátiles que cambian solos y el `id` de los nodos
    nuevos (n8n puede reasignarlo al guardarlos). Todo lo demás se compara tal cual,
    de modo que cualquier otro cambio respecto al esperado es un FALLO.
    """
    resultado = {
        clave: copy.deepcopy(valor)
        for clave, valor in workflow.items()
        if clave not in CLAVES_VOLATILES
    }
    for nodo in resultado.get("nodes", []):
        if nodo.get("name") in NODOS_NUEVOS:
            nodo.pop("id", None)
    return resultado


# ------------------------------------------------------------------- mutación


def mutar_principal(workflow: dict) -> tuple[dict, list[str], list[str]]:
    """Aplica (sobre una copia) los dos nodos y la reconexión del flujo principal.

    Devuelve `(trabajo, pendientes, problemas)`: `trabajo` es el resultado objetivo
    completo (idempotente), `pendientes` describe los cambios que faltaban y
    `problemas` son conflictos inesperados (si hay alguno no se hace PUT).
    """
    trabajo = copy.deepcopy(workflow)
    pendientes: list[str] = []
    problemas: list[str] = []

    # 1. Nodos nuevos.
    for modelo, posicion in (
        (construir_nodo_preparar(), POS_PREPARAR),
        (construir_nodo_ejecutar(), POS_EJECUTAR),
    ):
        nombre = modelo["name"]
        actual = buscar_nodo(trabajo, nombre)
        if actual is None:
            trabajo["nodes"].append(copy.deepcopy(modelo))
            pendientes.append(f"añadir nodo {nombre!r} en {posicion}")
            continue
        if sin_id(actual) != sin_id(modelo):
            problemas.append(
                f"el nodo {nombre!r} ya existe pero no coincide con el esperado; "
                "no se sobreescribe a ciegas"
            )

    # 2. Cadena de conexiones:
    #    Ejecutar Cerrar envio -> Preparar caso motor -> Ejecutar Motor -> Ejecutar Verificar y limpiar
    conexiones = trabajo.setdefault("connections", {})
    salida = json.dumps(conexiones.get(NOMBRE_CERRAR), ensure_ascii=False)
    if f'"node": "{NOMBRE_PREPARAR}"' not in salida:
        pendientes.append(f"reconectar {NOMBRE_CERRAR!r} -> {NOMBRE_PREPARAR!r} (antes iba a {NOMBRE_VERIFICAR!r})")
    conexiones[NOMBRE_CERRAR] = {
        "main": [[{"node": NOMBRE_PREPARAR, "type": "main", "index": 0}]]
    }

    if json.dumps(conexiones.get(NOMBRE_PREPARAR), ensure_ascii=False) != json.dumps(
        {"main": [[{"node": NOMBRE_EJECUTAR, "type": "main", "index": 0}]]}, ensure_ascii=False
    ):
        pendientes.append(f"conectar {NOMBRE_PREPARAR!r} -> {NOMBRE_EJECUTAR!r}")
    conexiones[NOMBRE_PREPARAR] = {
        "main": [[{"node": NOMBRE_EJECUTAR, "type": "main", "index": 0}]]
    }

    if json.dumps(conexiones.get(NOMBRE_EJECUTAR), ensure_ascii=False) != json.dumps(
        {"main": [[{"node": NOMBRE_VERIFICAR, "type": "main", "index": 0}]]}, ensure_ascii=False
    ):
        pendientes.append(f"conectar {NOMBRE_EJECUTAR!r} -> {NOMBRE_VERIFICAR!r}")
    conexiones[NOMBRE_EJECUTAR] = {
        "main": [[{"node": NOMBRE_VERIFICAR, "type": "main", "index": 0}]]
    }

    # 3. Posición de `Ejecutar Verificar y limpiar`: [2160, 0] es el hueco del nodo nuevo.
    verificador = buscar_nodo(trabajo, NOMBRE_VERIFICAR)
    if verificador is None:
        problemas.append(f"no se encontró el nodo {NOMBRE_VERIFICAR!r} en el flujo principal")
    elif list(verificador.get("position") or []) != POS_VERIFICAR:
        pendientes.append(
            f"desplazar {NOMBRE_VERIFICAR!r} de {verificador.get('position')} a {POS_VERIFICAR}"
        )
        verificador["position"] = list(POS_VERIFICAR)

    return trabajo, pendientes, problemas


def mutar_subflujo(workflow: dict) -> tuple[dict, list[str], list[str]]:
    """Aplica (sobre una copia) la sexta entrada, la rama `motor` y los dos filtros."""
    trabajo = copy.deepcopy(workflow)
    pendientes: list[str] = []
    problemas: list[str] = []

    # 2a. `Comparar resultados`: dos ediciones literales del `jsCode`.
    nodo = buscar_nodo(trabajo, NOMBRE_COMPARAR)
    if nodo is None:
        problemas.append(f"no se encontró el nodo {NOMBRE_COMPARAR!r}")
    else:
        parametros = nodo.get("parameters")
        if not isinstance(parametros, dict) or not isinstance(parametros.get("jsCode"), str):
            problemas.append(f"el nodo {NOMBRE_COMPARAR!r} no tiene `parameters.jsCode` de texto")
        else:
            codigo = parametros["jsCode"]
            nuevo = codigo
            for edicion in EDICIONES_JSCODE:
                if edicion["marcador"] in nuevo:
                    continue  # ya aplicada
                coincidencias = nuevo.count(edicion["antes"])
                if coincidencias == 1:
                    nuevo = nuevo.replace(edicion["antes"], edicion["despues"], 1)
                    pendientes.append(f"{NOMBRE_COMPARAR!r}: {edicion['descripcion']}")
                else:
                    problemas.append(
                        f"{NOMBRE_COMPARAR!r}: el ancla de {edicion['descripcion']!r} aparece "
                        f"{coincidencias} veces (se esperaba 1); no se sustituye a medias"
                    )
            if nuevo != codigo:
                nodo["parameters"]["jsCode"] = nuevo

    # 2b. Los dos `deleteRows` pasan a `anyCondition` con una condición extra.
    for nombre, espec in LIMPIEZA.items():
        nodo = buscar_nodo(trabajo, nombre)
        if nodo is None:
            problemas.append(f"no se encontró el nodo {nombre!r}")
            continue
        parametros = nodo.get("parameters")
        if not isinstance(parametros, dict):
            problemas.append(f"el nodo {nombre!r} no tiene `parameters` objeto")
            continue
        actual = {"matchType": parametros.get("matchType"), "filters": parametros.get("filters")}
        if actual == espec["despues"]:
            continue  # ya aplicado
        if actual != espec["antes"]:
            problemas.append(
                f"el filtro de {nombre!r} no está ni en el estado original ni en el objetivo; "
                "no se sobreescribe a ciegas"
            )
            continue
        parametros["matchType"] = espec["despues"]["matchType"]
        parametros["filters"] = copy.deepcopy(espec["despues"]["filters"])
        condiciones = len(espec["despues"]["filters"]["conditions"])
        pendientes.append(f"{nombre!r}: matchType=anyCondition + {condiciones} condiciones")

    return trabajo, pendientes, problemas


def mutar(workflow: dict) -> tuple[dict, list[str], list[str]]:
    if workflow.get("id") == FLUJO_PRINCIPAL["id"]:
        return mutar_principal(workflow)
    return mutar_subflujo(workflow)


# --------------------------------------------------------------- verificación


def verificar(actual: dict, esperado: dict) -> list[str]:
    """Comprueba que el flujo releído coincide exactamente con el objetivo esperado."""
    problemas: list[str] = []

    # (a) el resultado objetivo, campo por campo.
    a = proyeccion(actual)
    e = proyeccion(esperado)
    for clave in sorted(set(a) | set(e)):
        if a.get(clave) != e.get(clave):
            problemas.append(f"el campo {clave!r} no coincide con el resultado esperado")

    # (b) comprobaciones explícitas, con mensajes legibles.
    es_principal = actual.get("id") == FLUJO_PRINCIPAL["id"]
    info = FLUJO_PRINCIPAL if es_principal else SUBFLUJO
    conteo = len(actual.get("nodes", []))
    if conteo != info["nodos_final"]:
        problemas.append(f"el flujo tiene {conteo} nodos (se esperaban {info['nodos_final']})")

    if es_principal:
        for nombre in NODOS_NUEVOS:
            if buscar_nodo(actual, nombre) is None:
                problemas.append(f"falta el nodo {nombre!r} tras el PUT")
        cadena = [
            (NOMBRE_CERRAR, NOMBRE_PREPARAR),
            (NOMBRE_PREPARAR, NOMBRE_EJECUTAR),
            (NOMBRE_EJECUTAR, NOMBRE_VERIFICAR),
        ]
        for origen, destino in cadena:
            destinos = [
                c.get("node")
                for grupo in (actual.get("connections", {}).get(origen, {}).get("main") or [])
                for c in (grupo or [])
            ]
            if destinos != [destino]:
                problemas.append(f"la conexión {origen!r} -> {destino!r} no quedó: {destinos}")
        verificador = buscar_nodo(actual, NOMBRE_VERIFICAR)
        if verificador is not None and list(verificador.get("position") or []) != POS_VERIFICAR:
            problemas.append(
                f"{NOMBRE_VERIFICAR!r} quedó en {verificador.get('position')} "
                f"(se esperaba {POS_VERIFICAR})"
            )
    else:
        comparar = buscar_nodo(actual, NOMBRE_COMPARAR)
        codigo = (comparar or {}).get("parameters", {}).get("jsCode", "")
        for edicion in EDICIONES_JSCODE:
            if edicion["marcador"] not in codigo:
                problemas.append(f"falta en `Comparar resultados`: {edicion['descripcion']}")
        for nombre, espec in LIMPIEZA.items():
            nodo = buscar_nodo(actual, nombre)
            parametros = (nodo or {}).get("parameters") or {}
            actual_filtro = {
                "matchType": parametros.get("matchType"),
                "filters": parametros.get("filters"),
            }
            if actual_filtro != espec["despues"]:
                problemas.append(f"el filtro de {nombre!r} no quedó como se esperaba")

    return problemas


# ------------------------------------------------------------------------ salida


def imprimir_plan(entrada: dict) -> None:
    info = entrada["info"]
    print()
    print("=" * 100)
    print(f"PLAN — {info['nombre']} ({info['id']})")
    print("=" * 100)
    if entrada["estado"] == "FALLO":
        print(f"  FALLO: no se pudo leer el flujo ({entrada.get('tipo')})")
        return
    if not entrada["pendientes"]:
        print(f"  sin cambios pendientes (ya está en el estado objetivo); "
              f"{len(entrada['workflow'].get('nodes', []))} nodos")
        return
    print(f"  nodos: {len(entrada['workflow'].get('nodes', []))} -> "
          f"{len(entrada['trabajo'].get('nodes', []))} (límite 20)")
    for pendiente in entrada["pendientes"]:
        print(f"  - {pendiente}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Añade el sexto caso (el del motor) a la regresión CCB.",
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
    # Se leen los dos flujos y se calcula el objetivo. No se escribe nada todavía.
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
            if respaldo is None:
                print(f"FALLO RESPALDO {entrada['id']}: no se pudo releer {ruta}", file=sys.stderr)
                entrada["estado"] = "FALLO"
                fallos += 1
                continue
            conteo = len(respaldo.get("nodes", []))
            if conteo != entrada["info"]["nodos_respaldo"]:
                print(
                    f"FALLO RESPALDO {entrada['id']}: {ruta} tiene {conteo} nodos "
                    f"(se esperaban {entrada['info']['nodos_respaldo']})",
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
            if entrada["estado"] == "FALLO" or not entrada["pendientes"]:
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

            problemas = verificar(verificado, entrada["trabajo"])
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
    print(f"{'id':<20}{'flujo':<52}{'cambios':>8}  {'estado':<12}detalle")
    print("-" * 100)
    con_cambios = 0
    for entrada in plan:
        info = entrada["info"]
        if entrada["estado"] == "FALLO" and "pendientes" not in entrada:
            print(f"{entrada['id']:<20}{info['nombre'][:50]:<52}{'-':>8}  {'FALLO':<12}{entrada.get('tipo')}")
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
        print(f"{entrada['id']:<20}{info['nombre'][:50]:<52}{total:>8}  {estado:<12}{detalle}")

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
