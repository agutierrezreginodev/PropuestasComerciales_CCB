#!/usr/bin/env python3
"""Corrige cuatro afirmaciones obsoletas repartidas en cuatro flujos de la instancia viva.

Cada correccion es una sustitucion **literal** acotada a un unico campo de un unico nodo.
No se reformatea ni se toca nada mas: si la cadena "antes" no aparece exactamente una vez
en su campo, la correccion se reporta como FALLO y no se aplica a medias.

Las cuatro correcciones:

  1. `DF3emCmBBBB2HA3i` (`[SUB] CCB · PDF — Generar el PDF`), nodo `Nota - Generar PDF`,
     campo `parameters.content`: recuento de nodos de W3.
  2. `Hgy02eqPhnsdJvkq` (`[SUB] CCB · Config — Leer la configuración`), nodo
     `Nota - Leer Configuración`, campo `parameters.content`: cuantos flujos invocan hoy la
     tabla de configuracion.
  3. `KuLSIzBZgaRIjuSu` (`CCB · W4C — Consultar la propuesta para revisión`), nodo
     `Nota - W4C Consultar Propuesta`, campo `parameters.content`: dos sustituciones (el
     titulo y la nota sobre `alwaysOutputData`).
  4. `XWBHgbmtBubA4gqx` (`CCB · W5B — Envío al cliente`), nodo `Consolidar datos del
     envío` (`n8n-nodes-base.code`), campo `parameters.jsCode`: solo el comentario de la
     linea 2. La linea 3 (`$('Ejecutar Leer Contexto Propuesta')`) referencia un nodo del
     flujo y no se toca.

Uso:
    # Simulacion (por defecto): no escribe nada.
    python3 scripts/corregir_notas_obsoletas.py
    python3 scripts/corregir_notas_obsoletas.py --dry-run
    python3 scripts/corregir_notas_obsoletas.py --only KuLSIzBZgaRIjuSu

    # Aplicacion real: respalda, hace PUT y verifica contra el respaldo.
    python3 scripts/corregir_notas_obsoletas.py --apply

    # Solo lectura: relee cada flujo y lo verifica contra su respaldo, sin escribir.
    python3 scripts/corregir_notas_obsoletas.py --verify-only

Las credenciales se leen solo del entorno (`N8N_API_URL`, `N8N_API_KEY`) y nunca se
imprimen ni se escriben en disco.

Red de seguridad:
  * Antes de cualquier `PUT`, se descarga cada uno de los cuatro flujos a
    `~/ccb-backup/notas-obsoletas-2026-09-24/<id>.json`. Si el respaldo ya existe, se
    conserva (nunca se sobreescribe con el estado posterior).
  * Tras cada `PUT`, se relee el flujo y se comprueba (a) que las sustituciones esperadas
    estan y (b) que el resto del flujo no cambio respecto al respaldo. Se ignoran los
    metadatos volatiles que cambian solos (`updatedAt`, `versionCounter`, `versionId`,
    `activeVersion*` y `staticData`). La unica excepcion permitida es el campo tocado, que
    se normaliza a `<CAMPO>` en ambos lados.
  * Idempotencia: una segunda corrida de `--apply` debe dar 0 `PUT`. Una correccion ya
    aplicada (`antes` ausente y `despues` presente) se informa como "ya aplicada" y no es
    un FALLO.

Solo se modifica el `nodes` de nivel superior. `activeVersion.nodes` es historial interno
de n8n y no se toca.

Un `TimeoutError` en el `PUT` no se trata como fallo ciego: n8n puede haber confirmado el
cambio y haberse perdido solo la respuesta de lectura. En ese caso se relee el flujo y se
decide por el estado observado (si la sustitucion quedo y el resto no cambio, es APLICADO;
si no, FALLO).
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
RESPALDO_BASE = os.environ.get("CCB_BACKUP_DIR", os.path.join(os.path.expanduser("~"), "ccb-backup"))
RESPALDO_DIR = os.path.join(RESPALDO_BASE, "notas-obsoletas-2026-09-24")

# Las cuatro sustituciones literales. El separador de campo de nodo es un punto
# (`parameters.content`), asi que `campo` guarda solo la ultima clave.
CORRECCIONES = [
    {
        "id": "DF3emCmBBBB2HA3i",
        "flujo": "[SUB] CCB · PDF — Generar el PDF",
        "nodo": "Nota - Generar PDF",
        "campo": "content",
        "antes": "Etapa de presentación del motor, separada del cálculo de precio "
        "(W3 pasó de 25 a 19 nodos).",
        "despues": "Etapa de presentación del motor, separada del cálculo de precio "
        "(W3 pasó de 25 a 17 nodos; 16 sin contar las notas fijas).",
    },
    {
        "id": "Hgy02eqPhnsdJvkq",
        "flujo": "[SUB] CCB · Config — Leer la configuración",
        "nodo": "Nota - Leer Configuración",
        "campo": "content",
        "antes": "Cambiar un valor en la tabla se refleja en los 13 flujos sin tocar "
        "ningún workflow.",
        "despues": "Cambiar un valor en la tabla se refleja en toda la cadena sin tocar "
        "ningún workflow: hoy 12 flujos la invocan directamente y 22 la alcanzan.",
    },
    {
        "id": "KuLSIzBZgaRIjuSu",
        "flujo": "CCB · W4C — Consultar la propuesta para revisión",
        "nodo": "Nota - W4C Consultar Propuesta",
        "campo": "content",
        "antes": "### W4C - Consultar Propuesta para Revision",
        "despues": "### CCB · W4C — Consultar la propuesta para revisión",
    },
    {
        "id": "KuLSIzBZgaRIjuSu",
        "flujo": "CCB · W4C — Consultar la propuesta para revisión",
        "nodo": "Nota - W4C Consultar Propuesta",
        "campo": "content",
        "antes": "- Los 3 nodos de lectura (Cotizacion/Criterios/Solicitud) usan "
        "alwaysOutputData=true a proposito: si el id_solicitud no existe, la ejecucion "
        "sigue con datos vacios en vez de cortar, y Consolidar respuesta arma un "
        "{ok:false, error:...} explicito.",
        "despues": "- El contexto (cotización/criterios/solicitud) lo entrega "
        "`[SUB] CCB · Contexto — Leer el contexto de la propuesta` (F4-02), que lee las "
        "tres tablas con `alwaysOutputData=true` a propósito: si el id_solicitud no "
        "existe, la ejecución sigue con datos vacíos en vez de cortar, y `Consolidar "
        "respuesta` arma un `{ok:false, error:...}` explícito.",
    },
    {
        "id": "XWBHgbmtBubA4gqx",
        "flujo": "CCB · W5B — Envío al cliente",
        "nodo": "Consolidar datos del envío",
        "campo": "jsCode",
        "antes": "// F4-02/F4-03: el contexto lo entrega "
        "[SUB] CCB - Leer Contexto Propuesta.",
        "despues": "// F4-02/F4-03: el contexto lo entrega "
        "[SUB] CCB · Contexto — Leer el contexto de la propuesta.",
    },
]

# Ids unicos, en orden de aparicion.
IDS_AFECTADOS = list(dict.fromkeys(c["id"] for c in CORRECCIONES))


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


def buscar_nodo(workflow: dict, nombre: str) -> dict | None:
    for nodo in workflow.get("nodes", []):
        if nodo.get("name") == nombre:
            return nodo
    return None


def analizar(workflow: dict, correcciones: list[dict]) -> tuple[list[dict], dict]:
    """Aplica las correcciones sobre una copia de trabajo y describe el resultado.

    Devuelve `(resultados, trabajo)`:
      * `resultados`: una entrada por correccion con `estado` en
        {"pendiente", "ya aplicada", "FALLO"}. En una correccion ya aplicada la copia de
        trabajo no se modifica; en un FALLO tampoco.
      * `trabajo`: copia del flujo con las correcciones pendientes ya aplicadas, de la que
        se leen los valores esperados y se arma el payload.

    Se trabaja sobre la copia de forma secuencial para que dos correcciones en el mismo
    campo (flujo 3, `Nota - W4C Consultar Propuesta`) se acumulen en vez de pisarse.
    """
    trabajo = copy.deepcopy(workflow)
    resultados: list[dict] = []

    for corr in correcciones:
        entrada = {
            "correccion": corr,
            "estado": None,
            "coincidencias": None,
            "motivo": None,
            "texto_encontrado": None,
        }
        nodo = buscar_nodo(trabajo, corr["nodo"])
        if nodo is None:
            entrada["estado"] = "FALLO"
            entrada["motivo"] = f"no se encontro el nodo {corr['nodo']!r} en el flujo"
            resultados.append(entrada)
            continue

        parametros = nodo.get("parameters")
        if not isinstance(parametros, dict):
            entrada["estado"] = "FALLO"
            entrada["motivo"] = f"el nodo {corr['nodo']!r} no tiene `parameters` objeto"
            resultados.append(entrada)
            continue

        valor = parametros.get(corr["campo"])
        if not isinstance(valor, str):
            entrada["estado"] = "FALLO"
            entrada["motivo"] = (
                f"el campo `parameters.{corr['campo']}` del nodo {corr['nodo']!r} no es texto"
            )
            resultados.append(entrada)
            continue

        antes_count = valor.count(corr["antes"])
        despues_count = valor.count(corr["despues"])
        entrada["coincidencias"] = antes_count

        if antes_count == 1:
            parametros[corr["campo"]] = valor.replace(corr["antes"], corr["despues"], 1)
            entrada["estado"] = "pendiente"
        elif antes_count == 0 and despues_count >= 1:
            entrada["estado"] = "ya aplicada"
        else:
            entrada["estado"] = "FALLO"
            entrada["texto_encontrado"] = valor
            if antes_count == 0:
                entrada["motivo"] = (
                    f"la cadena 'antes' no aparece y la cadena 'despues' tampoco "
                    f"({despues_count} coincidencias): no se puede aplicar"
                )
            else:
                entrada["motivo"] = (
                    f"la cadena 'antes' aparece {antes_count} veces (se esperaba 1): "
                    "no se sustituye a medias"
                )
        resultados.append(entrada)

    return resultados, trabajo


def valores_esperados(trabajo: dict, resultados: list[dict]) -> dict[tuple[str, str], str]:
    """Mapa (nombre de nodo, campo) -> texto final esperado para las pendientes."""
    esperados: dict[tuple[str, str], str] = {}
    for entrada in resultados:
        if entrada["estado"] != "pendiente":
            continue
        corr = entrada["correccion"]
        nodo = buscar_nodo(trabajo, corr["nodo"])
        esperados[(corr["nodo"], corr["campo"])] = (nodo.get("parameters") or {})[corr["campo"]]
    return esperados


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


def proyeccion(workflow: dict, campos_tocados: set[tuple[str, str]]) -> dict:
    """Campos que el PUT debe preservar, normalizando la unica excepcion esperada.

    Se comparan solo los campos relevantes del flujo, no los metadatos volatiles que
    cambian solos (`updatedAt`, `versionCounter`, `versionId`, `activeVersion*` y
    `staticData`). En los nodos, cada campo tocado se normaliza a `<CAMPO>` para que la
    unica diferencia permitida sea justamente ese campo.
    """
    nodos = copy.deepcopy(workflow.get("nodes", []))
    for nodo in nodos:
        parametros = nodo.get("parameters")
        if not isinstance(parametros, dict):
            continue
        for nombre, campo in campos_tocados:
            if nodo.get("name") == nombre and campo in parametros:
                parametros[campo] = "<CAMPO>"

    return {
        "name": workflow.get("name"),
        "nodes": nodos,
        "connections": workflow.get("connections"),
        "settings": workflow.get("settings"),
        "active": workflow.get("active"),
        "pinData": workflow.get("pinData"),
        "description": workflow.get("description"),
    }


def verificar(
    actual: dict,
    respaldo: dict,
    campos_tocados: set[tuple[str, str]],
    esperados: dict[tuple[str, str], str],
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
    antes = proyeccion(respaldo, campos_tocados)
    despues = proyeccion(actual, campos_tocados)
    for campo in antes:
        if antes[campo] != despues[campo]:
            problemas.append(f"el campo {campo!r} cambio respecto al respaldo")

    return problemas


def describir_correccion(corr: dict, truncar: int = 110) -> tuple[str, str]:
    def corto(texto: str) -> str:
        texto = " ".join(texto.split())
        return texto if len(texto) <= truncar else texto[: truncar - 1] + "…"

    return corto(corr["antes"]), corto(corr["despues"])


def cargar_respaldo(workflow_id: str) -> dict | None:
    ruta = os.path.join(RESPALDO_DIR, f"{workflow_id}.json")
    if not os.path.exists(ruta):
        return None
    with open(ruta, encoding="utf-8") as handle:
        return json.load(handle)


def verificar_respaldo(base: str, key: str, ids: list[str]) -> int:
    """Modo de solo lectura: comprueba cada flujo contra su respaldo, sin escribir nada.

    Reutiliza `verificar` para comprobar (a) que la sustitucion quedo y (b) que el resto no
    cambio respecto al respaldo, con el campo tocado normalizado en ambos lados.
    """
    fallos = 0
    print()
    print("=" * 100)
    print("VERIFICACION CONTRA RESPALDO (solo lectura)")
    print("=" * 100)
    for workflow_id in ids:
        correcciones = [c for c in CORRECCIONES if c["id"] == workflow_id]
        flujo = correcciones[0]["flujo"]
        titulo = f"{workflow_id} — {flujo}"

        respaldo = cargar_respaldo(workflow_id)
        if respaldo is None:
            print(f"\n{titulo}\n  FALLO: falta el respaldo en {RESPALDO_DIR}/{workflow_id}.json")
            fallos += 1
            continue

        try:
            actual = fetch(base, key, workflow_id)
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError) as exc:
            print(f"\n{titulo}\n  FALLO: no se pudo leer el flujo ({type(exc).__name__}: {exc})")
            fallos += 1
            continue

        # El valor esperado se deriva del respaldo aplicando las sustituciones.
        _resultados, trabajo = analizar(respaldo, correcciones)
        campos_tocados = {(c["nodo"], c["campo"]) for c in correcciones}
        esperados: dict[tuple[str, str], str] = {}
        for corr in correcciones:
            nodo = buscar_nodo(trabajo, corr["nodo"])
            esperados[(corr["nodo"], corr["campo"])] = (nodo.get("parameters") or {})[
                corr["campo"]
            ]

        problemas = verificar(actual, respaldo, campos_tocados, esperados)
        if problemas:
            print(f"\n{titulo}\n  FALLO:")
            for problema in problemas:
                print(f"    - {problema}")
            fallos += 1
        else:
            print(f"\n{titulo}")
            for corr in correcciones:
                print(f"  OK: nodo {corr['nodo']!r} · parameters.{corr['campo']}")
            print("  resto del flujo sin cambios respecto al respaldo")

    print()
    print(f"Flujos verificados: {len(ids)}")
    if fallos:
        print(f"FALLOS: {fallos}", file=sys.stderr)
        return 1
    print("OK")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Corrige cuatro afirmaciones obsoletas, una por campo y nodo concretos.",
    )
    modo = parser.add_mutually_exclusive_group()
    modo.add_argument("--dry-run", action="store_true", help="simula sin escribir (por defecto)")
    modo.add_argument("--apply", action="store_true", help="respalda, aplica los PUT y verifica")
    modo.add_argument(
        "--verify-only",
        action="store_true",
        help="solo relee cada flujo y lo verifica contra su respaldo, sin escribir",
    )
    parser.add_argument("--only", metavar="ID", help="procesa solo el flujo indicado")
    args = parser.parse_args()

    base = os.environ.get("N8N_API_URL", "").rstrip("/")
    key = os.environ.get("N8N_API_KEY", "")
    if not base or not key:
        print("N8N_API_URL y N8N_API_KEY deben estar definidas en el entorno.", file=sys.stderr)
        return 2

    ids = list(IDS_AFECTADOS)
    if args.only:
        if args.only not in IDS_AFECTADOS:
            print(
                f"El id {args.only!r} no esta entre los cuatro flujos afectados.",
                file=sys.stderr,
            )
            return 2
        ids = [args.only]

    if args.verify_only:
        return verificar_respaldo(base, key, ids)

    aplicar = args.apply
    fallos = 0

    # ------------------------------------------------------------------ Fase A
    # Leer los flujos y calcular el plan. No se escribe nada todavia.
    plan: list[dict] = []
    for workflow_id in ids:
        correcciones = [c for c in CORRECCIONES if c["id"] == workflow_id]
        flujo = correcciones[0]["flujo"]
        try:
            actual = fetch(base, key, workflow_id)
        except urllib.error.HTTPError as exc:
            cuerpo = exc.read().decode("utf-8", "replace")
            print(f"FALLO GET {workflow_id}: HTTP {exc.code}", file=sys.stderr)
            print(f"  cuerpo: {cuerpo}", file=sys.stderr)
            fallos += 1
            plan.append({"id": workflow_id, "flujo": flujo, "estado": "FALLO", "tipo": "GET"})
            continue
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            print(f"FALLO GET {workflow_id}: {type(exc).__name__}: {exc}", file=sys.stderr)
            fallos += 1
            plan.append({"id": workflow_id, "flujo": flujo, "estado": "FALLO", "tipo": "GET"})
            continue

        resultados, trabajo = analizar(actual, correcciones)
        campos_tocados = {
            (e["correccion"]["nodo"], e["correccion"]["campo"])
            for e in resultados
            if e["estado"] == "pendiente"
        }
        pendientes = [e for e in resultados if e["estado"] == "pendiente"]
        flujo_fallos = [e for e in resultados if e["estado"] == "FALLO"]
        fallos += len(flujo_fallos)

        plan.append(
            {
                "id": workflow_id,
                "flujo": flujo,
                "workflow": actual,
                "resultados": resultados,
                "trabajo": trabajo,
                "campos_tocados": campos_tocados,
                "esperados": valores_esperados(trabajo, resultados),
                "pendiente": bool(pendientes),
                "estado": "OK",
                "puts": 0,
            }
        )

    def titulo(entrada: dict) -> str:
        return f"{entrada['id']} — {entrada['flujo']}"

    # ------------------------------------------------------------------ Fase B
    # Respaldo previo: antes de cualquier PUT, asegurar una copia cruda de los cuatro.
    if aplicar:
        for entrada in plan:
            if entrada["estado"] == "FALLO":
                continue
            ruta = guardar_respaldo(entrada["id"], entrada["workflow"])
            entrada["respaldo"] = ruta

    # ------------------------------------------------------------------ Fase C
    puts = 0
    if aplicar:
        for entrada in plan:
            if entrada["estado"] == "FALLO" or not entrada["pendiente"]:
                continue

            respuesta_perdida = None
            try:
                _status, _cuerpo = enviar_put(
                    base, key, entrada["id"], construir_payload(entrada["trabajo"])
                )
            except urllib.error.HTTPError as exc:
                cuerpo = exc.read().decode("utf-8", "replace")
                print(f"FALLO PUT {entrada['id']}: HTTP {exc.code}", file=sys.stderr)
                print(f"  cuerpo: {cuerpo}", file=sys.stderr)
                entrada["estado"] = "FALLO"
                entrada["tipo"] = "PUT"
                fallos += 1
                continue
            except (urllib.error.URLError, TimeoutError, OSError) as exc:
                # Un timeout de lectura no implica que el PUT no se haya aplicado: n8n
                # puede haber confirmado el cambio y perderse solo la respuesta. Se
                # continua a la relectura y se decide por el estado observado.
                respuesta_perdida = f"{type(exc).__name__}: {exc}"
                print(
                    f"AVISO PUT {entrada['id']}: respuesta perdida ({respuesta_perdida}); "
                    "se verifica releyendo el flujo.",
                    file=sys.stderr,
                )

            puts += 1
            entrada["puts"] = 1

            try:
                verificado = fetch(base, key, entrada["id"])
            except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError) as exc:
                print(
                    f"FALLO VERIFICACION {entrada['id']}: no se pudo releer "
                    f"({type(exc).__name__}: {exc})",
                    file=sys.stderr,
                )
                entrada["estado"] = "FALLO"
                entrada["tipo"] = "VERIFICACION"
                fallos += 1
                continue

            problemas = verificar(
                verificado,
                entrada["workflow"],
                entrada["campos_tocados"],
                entrada["esperados"],
            )
            entrada["verificado"] = verificado
            if problemas:
                print(f"FALLO VERIFICACION {entrada['id']}:", file=sys.stderr)
                for problema in problemas:
                    print(f"  - {problema}", file=sys.stderr)
                entrada["estado"] = "FALLO"
                entrada["tipo"] = "VERIFICACION"
                fallos += 1
                continue

            if respuesta_perdida:
                entrada["aviso"] = "PUT con respuesta perdida; verificado releyendo el flujo"

    # ------------------------------------------------------------------ Salida
    print()
    print("=" * 100)
    print("PLAN DE SUSTITUCIONES LITERALES")
    print("=" * 100)
    for entrada in plan:
        print()
        print(f"{titulo(entrada)}")
        if entrada["estado"] == "FALLO" and "resultados" not in entrada:
            print(f"  FALLO: no se pudo leer el flujo ({entrada['tipo']})")
            continue
        for resultado in entrada["resultados"]:
            corr = resultado["correccion"]
            antes, despues = describir_correccion(corr)
            print(f"  nodo {corr['nodo']!r} · parameters.{corr['campo']}")
            print(f"    antes : {antes}")
            print(f"    despues : {despues}")
            if resultado["estado"] == "pendiente":
                print(f"    -> PENDIENTE: {resultado['coincidencias']} coincidencia exacta")
            elif resultado["estado"] == "ya aplicada":
                print("    -> YA APLICADA: la cadena 'antes' no esta y la 'despues' si (idempotente)")
            else:
                print(f"    -> FALLO: {resultado['motivo']}")
                if resultado["texto_encontrado"] is not None:
                    print(f"       texto encontrado: {resultado['texto_encontrado']!r}")

    print()
    print("=" * 100)
    print("RESUMEN")
    print("=" * 100)
    print(f"{'id':<20}{'flujo':<52}{'sust.':>7}  {'estado':<14}detalle")
    print("-" * 100)
    aplicados = 0
    for entrada in plan:
        if entrada["estado"] == "FALLO" and "resultados" not in entrada:
            print(f"{entrada['id']:<20}{entrada['flujo'][:50]:<52}{'-':>7}  {'FALLO':<14}{entrada['tipo']}")
            continue
        total = sum(1 for e in entrada["resultados"] if e["estado"] == "pendiente")
        ya = sum(1 for e in entrada["resultados"] if e["estado"] == "ya aplicada")
        fallidas = sum(1 for e in entrada["resultados"] if e["estado"] == "FALLO")
        partes = [f"pendientes={total}", f"ya aplicadas={ya}", f"fallos={fallidas}"]
        if aplicar:
            if entrada["estado"] == "FALLO":
                estado = "FALLO"
                detalle = f"{entrada['tipo']}; " + ", ".join(partes)
            elif entrada["pendiente"]:
                estado = "APLICADO"
                aplicados += 1
                detalle = "PUT + verificacion OK; resto sin cambios"
                if entrada.get("aviso"):
                    detalle += f" [{entrada['aviso']}]"
            else:
                estado = "sin cambios"
                detalle = ", ".join(partes)
        else:
            estado = "PLAN" if entrada["pendiente"] else "sin cambios"
            detalle = ", ".join(partes)
        print(f"{entrada['id']:<20}{entrada['flujo'][:50]:<52}{total:>7}  {estado:<14}{detalle}")

    print()
    print(f"Flujos procesados: {len(plan)}")
    if aplicar:
        print(f"Flujos aplicados: {aplicados}")
    else:
        print(f"Flujos con cambios planificados: {sum(1 for e in plan if e.get('pendiente'))}")
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
