#!/usr/bin/env python3
"""Arregla el `pdf_url` que nunca se guardaba: dos ediciones quirurgicas, una por flujo.

Bug de produccion encontrado por el caso del motor de la regresion (24/09). El
diagnostico completo esta en la ficha `odd/tasks/caso-motor-regresion-ccb.md`,
seccion **Hallazgo**. Mecanismo:

* En W3 (`cHOIOEFB5nbltN82`), `Normalizar Criterios` empieza con `const row = $json`
  y devuelve un objeto de 40 campos en el que `id_solicitud` no esta. Toda la
  cadena posterior pierde el identificador.
* El microservicio (`microservicio-propuestas/server.js`) **solo persiste el PDF
  si recibe `id_solicitud`**: `if (options.id_solicitud) fs.writeFileSync(...)`.
* `[SUB] CCB · PDF — Generar el PDF` (`DF3emCmBBBB2HA3i`), nodo
  `Adjuntar PDF_URL`, construye `BASE_URL + '/pdfs/' + id + '.pdf'` con `id = null`
  y devuelve `PDF_URL = null`.
* W3 lo daba por bueno porque `IF - ¿PDF generado?` solo mira `$json.ok === true`,
  y ese `ok` viene heredado del calculo.

Las dos ediciones:

1. **W3 · `Normalizar Criterios`** (`parameters.jsCode`): se antepone
   `id_solicitud: row.id_solicitud` como **primer campo** del objeto devuelto.
   `row` ya esta definido en la primera linea del nodo (`const row = $json;`), asi
   que es la entrada del flujo. Arregla de raiz la persistencia en el
   microservicio, el `pdf_url` de la fila y el `nombre_archivo`.

2. **`[SUB] CCB · PDF` · `Adjuntar PDF_URL`** (`parameters.jsCode`): cuando no
   puede construir la URL publica, ademas de `PDF_URL: null` devuelve `ok: false`
   con el motivo, `nodo_fallido` y `mensaje_error`. Se endurece **aqui** y no en la
   condicion del `IF`: el camino falso del IF pasa por
   `Data Table - Registrar error infra (PDF)` -> `Restaurar resultado de error`, y
   ese nodo copia el item del subflujo de PDF, que en ese escenario traeria
   `ok: true` heredado. Poniendo la senal en el nodo que si sabe que fallo, el IF
   existente hace lo correcto sin tocarlo.

**No se toca nada mas.** En particular:

* La condicion de `IF - ¿PDF generado?` (queda intacta).
* Los 4 nodos `HTML - *` del subflujo de PDF: sus plantillas usan `{{ }}` a
  proposito y convertirlas en expresiones de n8n romperia la generacion.
* No se anaden ni se quitan nodos en ninguno de los dos flujos.

Uso:
    # Simulacion (por defecto): describe las dos sustituciones y no escribe nada.
    python3 scripts/arreglar_pdf_url.py
    python3 scripts/arreglar_pdf_url.py --dry-run

    # Aplicacion real: respalda, hace PUT y verifica contra el respaldo.
    python3 scripts/arreglar_pdf_url.py --apply

Las credenciales se leen solo del entorno (`N8N_API_URL`, `N8N_API_KEY`) y nunca
se imprimen ni se escriben en disco.

Red de seguridad:
  * Antes de cualquier `PUT` se descarga cada flujo a
    `/tmp/n8n-backup/arreglo-pdf-url-2026-09-24/<id>.json` y se re-verifica
    leyendolo (17 nodos en W3, 12 en el subflujo de PDF). Si el respaldo ya existe
    se conserva: nunca se sobreescribe con el estado posterior.
  * Tras cada `PUT` se relee el flujo y se comprueba (a) que la sustitucion quedo
    y (b) que **nada mas** cambio respecto al respaldo, ignorando los metadatos
    volatiles (`updatedAt`, `versionCounter`, `versionId`, `activeVersion*` y
    `staticData`) y normalizando el unico campo tocado. Cualquier otra diferencia
    es FALLO y no se esconde.
  * Idempotencia: una segunda corrida de `--apply` no emite ningun `PUT`.

Solo se modifica el `parameters.jsCode` de un nodo por flujo. `activeVersion.nodes`
es historial interno de n8n y no se toca.
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
RESPALDO_DIR = "/tmp/n8n-backup/arreglo-pdf-url-2026-09-24"

# Metadatos volatiles que cambian solos y no se comparan.
CLAVES_VOLATILES = (
    "updatedAt",
    "versionCounter",
    "versionId",
    "activeVersion",
    "activeVersionId",
    "staticData",
)

# --------------------------------------------------------------------- edicion 1

# Estado original y objetivo del ancla en W3. El objeto devuelto empieza en
# `return { json: {` y su primer campo es `_tipoNorm`; `id_solicitud` se antepone.
W3_ANTES = "return {\n  json: {\n    _tipoNorm: tipoNorm,"
W3_DESPUES = "return {\n  json: {\n    id_solicitud: row.id_solicitud,\n    _tipoNorm: tipoNorm,"

# --------------------------------------------------------------------- edicion 2

# `jsCode` completo de `Adjuntar PDF_URL` antes y despues. El reemplazo es la
# totalidad del campo: se conserva el comentario original y se anade la rama de
# fallo (`if (!PDF_URL) { ... ok: false ... }`).
PDF_ANTES = """// Construye la URL publica del PDF persistido por el microservicio.
// BASE_URL: valor centralizado en la Data Table Configuracion_CCB (F5-03).
const BASE_URL = (($('Ejecutar Leer Configuración').first().json._config || {}).microservicio_pdf_url || '');
let id = $json.id_solicitud;
if (!id) { try { id = $('When Executed by Another Workflow').first().json.id_solicitud; } catch (e) {} }
if (!id) { try { id = $('Interpolar plantilla HTML').first().json.id_solicitud; } catch (e) {} }
const PDF_URL = id ? (BASE_URL + '/pdfs/' + id + '.pdf') : null;
// F4-05: el PDF viaja por URL (pdf_url); nadie aguas abajo consume el binario, asi que no se cruza entre subflujos.
return { json: { ...$json, id_solicitud: id, PDF_URL } };"""

PDF_NUEVO = """// Construye la URL publica del PDF persistido por el microservicio.
// BASE_URL: valor centralizado en la Data Table Configuracion_CCB (F5-03).
const BASE_URL = (($('Ejecutar Leer Configuración').first().json._config || {}).microservicio_pdf_url || '');
let id = $json.id_solicitud;
if (!id) { try { id = $('When Executed by Another Workflow').first().json.id_solicitud; } catch (e) {} }
if (!id) { try { id = $('Interpolar plantilla HTML').first().json.id_solicitud; } catch (e) {} }
const PDF_URL = id ? (BASE_URL + '/pdfs/' + id + '.pdf') : null;
// F4-05: el PDF viaja por URL (pdf_url); nadie aguas abajo consume el binario, asi que no se cruza entre subflujos.
if (!PDF_URL) {
  // Un PDF sin URL publica no puede pasar como exito: W3 solo mira 'ok', y el microservicio
  // solo persiste el archivo si recibe id_solicitud (si no lo recibe, el .pdf no existe en disco).
  const mensaje = 'No se pudo construir la URL publica del PDF: falta "id_solicitud" en la entrada de la etapa de PDF, '
    + 'asi que el microservicio no persistio el archivo (su persistencia depende de options.id_solicitud).';
  return { json: { ...$json, id_solicitud: id, PDF_URL: null, ok: false, error: mensaje,
                   nodo_fallido: 'Adjuntar PDF_URL', mensaje_error: mensaje } };
}
return { json: { ...$json, id_solicitud: id, PDF_URL } };"""

W3_ID = "cHOIOEFB5nbltN82"
PDF_ID = "DF3emCmBBBB2HA3i"

# Nodos que NO deben cambiar (se comprueban explicitamente tras el PUT, ademas de
# la comparacion global contra el respaldo).
NODOS_INTOCABLES = {
    W3_ID: ["IF - ¿PDF generado?"],
    PDF_ID: [
        "HTML - Información Georreferenciada",
        "HTML - Zonificación y Rutero",
        "HTML - Ubicación de Nuevo Negocio",
        "HTML - Información en Línea",
    ],
}

# Flujos y ediciones. `nodos` es el conteo esperado antes y despues (no cambia).
FLUJOS = [
    {
        "id": W3_ID,
        "nombre": "CCB · W3 — Motor de criterios y precio",
        "nodos": 17,
        "ediciones": [
            {
                "descripcion": "anteponer `id_solicitud` como primer campo del objeto devuelto",
                "nodo": "Normalizar Criterios",
                "campo": "jsCode",
                "antes": W3_ANTES,
                "despues": W3_DESPUES,
            }
        ],
    },
    {
        "id": PDF_ID,
        "nombre": "[SUB] CCB · PDF — Generar el PDF",
        "nodos": 12,
        "ediciones": [
            {
                "descripcion": "reemplazar el `jsCode` completo con la rama de fallo (ok:false)",
                "nodo": "Adjuntar PDF_URL",
                "campo": "jsCode",
                "antes": PDF_ANTES,
                "despues": PDF_NUEVO,
            }
        ],
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


# --------------------------------------------------------------------- mutacion


def analizar(workflow: dict, ediciones: list[dict]) -> tuple[dict, list[dict], list[str]]:
    """Aplica (sobre una copia) las ediciones del flujo y describe el resultado.

    Devuelve `(trabajo, resultados, problemas)`:
      * `trabajo`: copia con las ediciones pendientes ya aplicadas (idempotente).
      * `resultados`: una entrada por edicion con `estado` en
        {"pendiente", "ya aplicada"} (los conflictos van a `problemas`).
      * `problemas`: conflictos inesperados; si hay alguno no se hace PUT.
    """
    trabajo = copy.deepcopy(workflow)
    resultados: list[dict] = []
    problemas: list[str] = []

    for edicion in ediciones:
        nodo = buscar_nodo(trabajo, edicion["nodo"])
        if nodo is None:
            problemas.append(f"no se encontro el nodo {edicion['nodo']!r}")
            continue
        parametros = nodo.get("parameters")
        if not isinstance(parametros, dict):
            problemas.append(f"el nodo {edicion['nodo']!r} no tiene `parameters` objeto")
            continue
        valor = parametros.get(edicion["campo"])
        if not isinstance(valor, str):
            problemas.append(
                f"el campo `parameters.{edicion['campo']}` del nodo "
                f"{edicion['nodo']!r} no es texto"
            )
            continue

        antes_count = valor.count(edicion["antes"])
        despues_count = valor.count(edicion["despues"])

        if antes_count == 1:
            parametros[edicion["campo"]] = valor.replace(edicion["antes"], edicion["despues"], 1)
            resultados.append({"edicion": edicion, "estado": "pendiente"})
        elif antes_count == 0 and despues_count >= 1:
            resultados.append({"edicion": edicion, "estado": "ya aplicada"})
        else:
            if antes_count == 0:
                problemas.append(
                    f"{edicion['nodo']!r}: no se encontro el ancla ni el resultado "
                    f"({despues_count} coincidencias del texto final); no se sobreescribe a ciegas"
                )
            else:
                problemas.append(
                    f"{edicion['nodo']!r}: el ancla aparece {antes_count} veces "
                    "(se esperaba 1); no se sustituye a medias"
                )

    return trabajo, resultados, problemas


def campos_tocados(ediciones: list[dict]) -> set[tuple[str, str]]:
    return {(e["nodo"], e["campo"]) for e in ediciones}


def esperados_desde(trabajo: dict, ediciones: list[dict]) -> dict[tuple[str, str], str]:
    esperados: dict[tuple[str, str], str] = {}
    for edicion in ediciones:
        nodo = buscar_nodo(trabajo, edicion["nodo"])
        esperados[(edicion["nodo"], edicion["campo"])] = (nodo.get("parameters") or {})[
            edicion["campo"]
        ]
    return esperados


# --------------------------------------------------------------- verificacion


def proyeccion(workflow: dict, tocados: set[tuple[str, str]]) -> dict:
    """Vista comparable del flujo, con el unico campo tocado normalizado.

    Se descartan los metadatos volatiles que cambian solos. En los nodos, cada campo
    tocado se normaliza a `<CAMPO>` en ambos lados, de modo que la unica diferencia
    permitida sea justamente ese campo. Todo lo demas se compara tal cual: cualquier
    otro cambio respecto al respaldo es un FALLO.
    """
    vista = {
        clave: copy.deepcopy(valor)
        for clave, valor in workflow.items()
        if clave not in CLAVES_VOLATILES
    }
    for nodo in vista.get("nodes", []):
        parametros = nodo.get("parameters")
        if not isinstance(parametros, dict):
            continue
        for nombre, campo in tocados:
            if nodo.get("name") == nombre and campo in parametros:
                parametros[campo] = "<CAMPO>"
    return vista


def comparar_nodos_intactos(actual: dict, respaldo: dict, nombres: list[str]) -> list[str]:
    problemas: list[str] = []
    for nombre in nombres:
        a = buscar_nodo(actual, nombre)
        b = buscar_nodo(respaldo, nombre)
        if a is None:
            problemas.append(f"desaparecio el nodo {nombre!r} (no debia tocarse)")
        elif b is not None and sin_id(a) != sin_id(b):
            problemas.append(f"el nodo {nombre!r} cambio, pero no debia tocarse")
    return problemas


def verificar(
    actual: dict,
    respaldo: dict,
    tocados: set[tuple[str, str]],
    esperados: dict[tuple[str, str], str],
    info: dict,
) -> list[str]:
    """Comprueba (a) la sustitucion esperada y (b) que el resto no cambio."""
    problemas: list[str] = []

    # (a) cada campo tocado quedo con el texto esperado.
    for (nombre, campo), valor_esperado in esperados.items():
        nodo = buscar_nodo(actual, nombre)
        if nodo is None:
            problemas.append(f"no se encontro el nodo {nombre!r} tras el PUT")
            continue
        valor = (nodo.get("parameters") or {}).get(campo)
        if valor != valor_esperado:
            problemas.append(
                f"el campo `parameters.{campo}` del nodo {nombre!r} no quedo con el texto esperado"
            )

    # (b) el resto del flujo no cambio respecto al respaldo.
    antes = proyeccion(respaldo, tocados)
    despues = proyeccion(actual, tocados)
    for clave in sorted(set(antes) | set(despues)):
        if antes.get(clave) != despues.get(clave):
            problemas.append(f"el campo {clave!r} cambio respecto al respaldo")

    # (c) conteo de nodos sin cambios.
    conteo = len(actual.get("nodes", []))
    if conteo != info["nodos"]:
        problemas.append(f"el flujo tiene {conteo} nodos (se esperaban {info['nodos']})")

    # (d) los nodos que no debian tocarse, uno por uno (mensaje legible).
    problemas.extend(
        comparar_nodos_intactos(actual, respaldo, NODOS_INTOCABLES.get(info["id"], []))
    )

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
    if entrada["estado"] == "FALLO" and "resultados" not in entrada:
        print(f"  FALLO: no se pudo leer el flujo ({entrada.get('tipo')})")
        return

    print(f"  nodos: {len(entrada['workflow'].get('nodes', []))} (sin cambios; se esperan {info['nodos']})")
    for resultado in entrada["resultados"]:
        edicion = resultado["edicion"]
        print(f"  nodo {edicion['nodo']!r} · parameters.{edicion['campo']}")
        print(f"    ({resultado['estado']}) {edicion['descripcion']}")
        print(f"    ANTES:   {_corto(edicion['antes'])}")
        print(f"    DESPUES: {_corto(edicion['despues'])}")
    for problema in entrada["problemas"]:
        print(f"  FALLO: {problema}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Arregla el `pdf_url` que nunca se guardaba (W3 + subflujo de PDF).",
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
    # Se leen los dos flujos y se calcula el objetivo. No se escribe nada todavia.
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

        trabajo, resultados, problemas = analizar(actual, info["ediciones"])
        entrada.update(
            {
                "workflow": actual,
                "trabajo": trabajo,
                "resultados": resultados,
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
            if respaldo.get("id") != entrada["id"] or conteo != entrada["info"]["nodos"]:
                print(
                    f"FALLO RESPALDO {entrada['id']}: {ruta} tiene id {respaldo.get('id')!r} y "
                    f"{conteo} nodos (se esperaban {entrada['info']['nodos']})",
                    file=sys.stderr,
                )
                entrada["estado"] = "FALLO"
                fallos += 1
                continue
            print(
                f"\nRESPALDO {entrada['id']}: {ruta} ({conteo} nodos, reverificado)"
            )

    # ------------------------------------------------------------ Fase C: aplicar
    puts = 0
    if aplicar:
        for entrada in plan:
            if entrada["estado"] == "FALLO":
                entrada["estado_final"] = "FALLO"
                continue
            pendientes = [r for r in entrada["resultados"] if r["estado"] == "pendiente"]
            if not pendientes:
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

            tocados = campos_tocados(entrada["info"]["ediciones"])
            esperados = esperados_desde(entrada["trabajo"], entrada["info"]["ediciones"])
            problemas = verificar(verificado, entrada["respaldo_data"], tocados, esperados, entrada["info"])
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
        pendientes = [r for r in entrada.get("resultados", []) if r["estado"] == "pendiente"]
        if entrada["estado"] == "FALLO" and "resultados" not in entrada:
            print(f"{entrada['id']:<20}{info['nombre'][:42]:<44}{conteo:>6}  {'FALLO':<12}{entrada.get('tipo')}")
            continue
        if aplicar:
            estado = entrada.get("estado_final", "sin cambios")
            if estado == "APLICADO":
                con_cambios += 1
                detalle = "PUT + verificacion OK; resto sin cambios"
            elif estado == "FALLO":
                detalle = "ver ejecucion"
            else:
                detalle = "ya estaba aplicado"
        else:
            if entrada["estado"] == "FALLO":
                estado = "FALLO"
                detalle = "conflicto de mutacion"
            elif pendientes:
                estado = "PLAN"
                con_cambios += 1
                detalle = f"{len(pendientes)} sustitucion(es)"
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
        print("Modo simulacion (--dry-run): no se envio ningun PUT ni se escribio ningun respaldo.")
    elif puts == 0:
        print("Sin PUT: todo estaba ya aplicado (idempotente).")

    if fallos:
        print(f"FALLOS: {fallos}", file=sys.stderr)
        return 1

    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
