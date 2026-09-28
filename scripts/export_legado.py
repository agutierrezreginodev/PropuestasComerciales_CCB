#!/usr/bin/env python3
"""Archiva los flujos de la instancia que NO son del proyecto (el "legado").

**Para que sirve.** El snapshot del repo exporta solo los 30 flujos del proyecto
(`scripts/export_workflows.py`), asi que las versiones historicas y los flujos
ajenos al proyecto **no tienen copia en el repo**. El respaldo anterior vivia en
`/tmp/n8n-backup/legado-2026-09-24/` y se perdio cuando `/tmp` se limpio: desde
entonces n8n era su **unica** copia. Este script crea una copia **durable, fuera
del repositorio**, con manifiesto y `sha256` por archivo.

Uso:
    # Solo lista lo que archivaria. No escribe nada.
    python3 scripts/export_legado.py --dry-run

    # Escribe en ~/ccb-backup/legado-<AAAA-MM-DD>/
    python3 scripts/export_legado.py

    # Destino explicito
    python3 scripts/export_legado.py --out /home/adrian/ccb-backup/legado-2026-09-28

    # Omite los 5 flujos de otra area (ver AJENOS)
    python3 scripts/export_legado.py --excluir-ajenos

IMPORTANTE — **este archivo no se anonimiza.** A diferencia de
`export_workflows.py`, que prepara contenido para el repositorio publico, esto es
un **respaldo**: guarda los flujos tal como estan en la instancia, con correos e
identificadores reales, para que sirva para restaurar. Por eso el destino **no
puede estar dentro del repositorio ni en `/tmp`**: el script lo verifica y aborta.
El manifiesto advierte lo mismo, y el script informa cuantos correos reales
encontro (enmascarados) para que quede claro que el archivo es sensible.

Credenciales: solo del entorno (`N8N_API_URL`, `N8N_API_KEY`); nunca se imprimen
ni se escriben en el manifiesto. La instancia se registra como `<N8N_API_URL>`.
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import sys
import urllib.error
import urllib.request

AQUI = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(AQUI)
sys.path.insert(0, AQUI)

# La lista de los 30 del proyecto es la fuente de verdad de "que es del proyecto":
# se importa en vez de duplicarla, para que no se desincronice.
from export_workflows import EMAIL_RE, WORKFLOWS, es_correo_de_prueba, mask  # noqa: E402

IDS_DEL_PROYECTO = set(WORKFLOWS.values())

# Flujos que no son del proyecto: la instancia es organizacional y estos parecen
# de otra area. Se archivan igual (hoy viven dentro de la carpeta del proyecto),
# pero `--excluir-ajenos` permite dejarlos fuera.
AJENOS = {
    "CamaraBAQ - Emails leads sin agendar y no asistió",
    "Chatbot - Consultorio IA",
    "My workflow 16 - Envío correos HTML",
    "My workflow 19",
    "RSS IA → Google Sheets",
}


def fetch(base: str, key: str, workflow_id: str) -> dict:
    request = urllib.request.Request(
        f"{base}/api/v1/workflows/{workflow_id}",
        headers={"X-N8N-API-KEY": key, "accept": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=90) as response:
        return json.load(response)


def listar_flujos(base: str, key: str) -> list[dict]:
    """Inventario completo (paginado) — solo lectura."""
    flujos, cursor = [], None
    while True:
        url = f"{base}/api/v1/workflows?limit=250" + (f"&cursor={cursor}" if cursor else "")
        request = urllib.request.Request(url, headers={"X-N8N-API-KEY": key})
        with urllib.request.urlopen(request, timeout=90) as response:
            data = json.load(response)
        flujos += data["data"]
        cursor = data.get("nextCursor")
        if not cursor:
            return flujos


def sha256_de(ruta: str) -> str:
    with open(ruta, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def destino(argumento: str | None) -> str:
    if argumento:
        return os.path.abspath(argumento)
    fecha = datetime.date.today().isoformat()
    return os.path.join(os.path.expanduser("~"), "ccb-backup", f"legado-{fecha}")


def validar_destino(ruta: str) -> str | None:
    """Devuelve el motivo del rechazo, o None si el destino es aceptable."""
    real = os.path.realpath(ruta)
    if real == os.path.realpath(REPO_ROOT) or real.startswith(os.path.realpath(REPO_ROOT) + os.sep):
        return "esta dentro del repositorio"
    if real == "/tmp" or real.startswith("/tmp/"):
        return "esta en /tmp (efimero: es exactamente lo que se perdio la vez anterior)"
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Archiva los flujos que no son del proyecto.")
    parser.add_argument("--dry-run", action="store_true", help="solo lista; no escribe nada")
    parser.add_argument("--out", default=None, help="destino (por defecto ~/ccb-backup/legado-<fecha>)")
    parser.add_argument("--excluir-ajenos", action="store_true", help="omite los 5 flujos de otra area")
    args = parser.parse_args()

    base = os.environ.get("N8N_API_URL", "").rstrip("/")
    key = os.environ.get("N8N_API_KEY", "")
    if not base or not key:
        print("N8N_API_URL y N8N_API_KEY deben estar definidas en el entorno.", file=sys.stderr)
        return 2

    # La guarda del destino va antes de tocar la red: si el destino no sirve, no
    # tiene sentido leer la instancia. Con --dry-run no se escribe, asi que no aplica.
    out = None
    if not args.dry_run:
        out = destino(args.out)
        motivo = validar_destino(out)
        if motivo:
            print(f"Destino rechazado: {out}\n  Motivo: {motivo}.", file=sys.stderr)
            print("Este respaldo contiene correos e identificadores reales: no puede vivir en el repo ni en /tmp.",
                  file=sys.stderr)
            return 2

    inventario = listar_flujos(base, key)
    legado = [w for w in inventario if w["id"] not in IDS_DEL_PROYECTO]
    if args.excluir_ajenos:
        legado = [w for w in legado if w["name"] not in AJENOS]
    legado.sort(key=lambda w: w["name"])

    print(f"Inventario: {len(inventario)} flujos | del proyecto: {len(IDS_DEL_PROYECTO)}"
          f" | a archivar: {len(legado)}")
    ajenos_incluidos = [w for w in legado if w["name"] in AJENOS]
    print(f"De esos, {len(ajenos_incluidos)} son de otra area (se archivan igual salvo --excluir-ajenos).\n")

    if args.dry_run:
        for w in legado:
            marca = "ajeno" if w["name"] in AJENOS else "historico"
            print(f"  [{marca:9}] {'archivado' if w['isArchived'] else 'activo   ' if w['active'] else 'inactivo '}"
                  f"  {w['name']}   id={w['id']}")
        print(f"\n(dry-run: no se escribio nada; {len(legado)} flujos se archivarian)")
        return 0

    os.makedirs(out, exist_ok=True)
    registros, correos, bytes_totales = [], {}, 0
    errores = 0

    for w in legado:
        try:
            flujo = fetch(base, key, w["id"])
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
            print(f"  ERROR al leer {w['name']}: {type(exc).__name__}", file=sys.stderr)
            errores += 1
            continue

        flujo.pop("shared", None)
        texto = json.dumps(flujo, indent=2, ensure_ascii=False)
        ruta = os.path.join(out, f"{w['id']}.json")
        with open(ruta, "w", encoding="utf-8") as handle:
            handle.write(texto + "\n")

        reales = sorted({a for a in EMAIL_RE.findall(texto) if not es_correo_de_prueba(a)})
        if reales:
            correos[w["name"]] = [mask(a) for a in reales]

        tamano = os.path.getsize(ruta)
        bytes_totales += tamano
        registros.append(
            {
                "id": w["id"],
                "nombre": w["name"],
                "activo": w["active"],
                "archivado": w["isArchived"],
                "nodos": len(flujo.get("nodes") or []),
                "bytes": tamano,
                "sha256": sha256_de(ruta),
                "origen": "otra area" if w["name"] in AJENOS else "version historica",
            }
        )

    manifiesto = {
        "proposito": "Respaldo durable de los flujos de la instancia que NO son del proyecto.",
        "fecha": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
        "instancia": "<N8N_API_URL>",
        "inventario_total": len(inventario),
        "del_proyecto": len(IDS_DEL_PROYECTO),
        "archivados": len(registros),
        "errores": errores,
        "bytes_totales": bytes_totales,
        "advertencia": "SIN ANONIMIZAR: contiene correos e identificadores reales. No commitear, no mover al repo.",
        "flujos": registros,
    }
    with open(os.path.join(out, "manifest.json"), "w", encoding="utf-8") as handle:
        json.dump(manifiesto, handle, indent=2, ensure_ascii=False)
        handle.write("\n")

    lineas = [
        "# Legado de la instancia — respaldo durable",
        "",
        f"- **Fecha:** {manifiesto['fecha']}",
        f"- **Origen:** instancia indicada por `N8N_API_URL` (no se registra la URL)",
        f"- **Inventario:** {len(inventario)} flujos · del proyecto {len(IDS_DEL_PROYECTO)} · "
        f"**archivados aqui {len(registros)}** (errores: {errores})",
        f"- **Tamano:** {bytes_totales / 1024:.0f} KB",
        "",
        "> **Sin anonimizar.** Este respaldo conserva los flujos tal como estan en la instancia, con correos e",
        "> identificadores reales, para que sirva para restaurar. **No commitear y no mover al repositorio.**",
        "",
        "## Como restaurar",
        "",
        "Cada archivo es la respuesta cruda de `GET /api/v1/workflows/{id}`. Para reimportar uno:",
        "",
        "```bash",
        "# opcion A: importar desde la UI de n8n (Import from File -> <id>.json)",
        "# opcion B: PUT a la API (quitar antes claves de solo lectura: id/createdAt/updatedAt/isArchived)",
        "```",
        "",
        "## Contenido",
        "",
        "| id | flujo | origen | estado | nodos | bytes | sha256 (12) |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in registros:
        estado = "archivado" if r["archivado"] else ("activo" if r["activo"] else "inactivo")
        lineas.append(
            f"| `{r['id']}` | {r['nombre']} | {r['origen']} | {estado} | {r['nodos']} | {r['bytes']} | "
            f"`{r['sha256'][:12]}` |"
        )
    if correos:
        lineas += [
            "",
            "## Sensibilidad",
            "",
            f"{sum(len(v) for v in correos.values())} direcciones reales en {len(correos)} flujos "
            "(enmascaradas a proposito). Muestra:",
            "",
        ]
        for nombre, direcciones in sorted(correos.items()):
            lineas.append(f"- {nombre}: {', '.join(direcciones)}")
    with open(os.path.join(out, "MANIFEST.md"), "w", encoding="utf-8") as handle:
        handle.write("\n".join(lineas) + "\n")

    print(f"Archivados {len(registros)} flujos en {out}")
    print(f"  tamano total: {bytes_totales / 1024:.0f} KB | errores: {errores}")
    print(f"  correos reales: {sum(len(v) for v in correos.values())} en {len(correos)} flujos (enmascarados en el manifiesto)")
    print("  manifiesto: manifest.json + MANIFEST.md")
    if errores:
        print("  ATENCION: hubo flujos que no se pudieron leer; volver a correr para completar.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
