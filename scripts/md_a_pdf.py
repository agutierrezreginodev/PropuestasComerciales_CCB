#!/usr/bin/env python3
"""Convierte un documento Markdown del proyecto a PDF.

**Para que sirve.** Los documentos del proyecto se escriben en Markdown y se leen en GitHub o VS Code, pero
para compartirlos fuera (un correo, Tecnologia) hace falta un PDF: un `.md` adjunto se ve con las marcas
crudas (`###`, `| tabla |`, `**negrita**`) porque el cliente de correo no las interpreta.

**Por que no usa pandoc.** En este entorno no hay `pandoc`, `wkhtmltopdf`, `weasyprint` ni LibreOffice. Pero
el microservicio de PDF del proyecto ya descarga **Chrome for Testing** via Puppeteer, asi que se reutiliza
ese binario para renderizar. No instala nada ni necesita red.

Uso:
    # Genera el PDF al lado del Markdown (mismo nombre, extension .pdf)
    python3 scripts/md_a_pdf.py docs/PROPUESTA_TECNOLOGIA_2026-09-24.md

    # Destino explicito
    python3 scripts/md_a_pdf.py <entrada.md> --out /ruta/salida.pdf

    # Deja tambien el HTML intermedio (util para revisar el render sin abrir el PDF)
    python3 scripts/md_a_pdf.py <entrada.md> --html

    # Solo el HTML, sin PDF
    python3 scripts/md_a_pdf.py <entrada.md> --solo-html

    # Binario de Chrome explicito
    python3 scripts/md_a_pdf.py <entrada.md> --chrome /ruta/a/chrome

Cobertura del subconjunto de Markdown que usa este repositorio: titulos (1 a 6), negrita, cursiva, codigo en
linea, bloques de codigo con fences, tablas con alineacion, listas con anidamiento, casillas (`- [ ]`),
citas (`>`), lineas horizontales, enlaces, imagenes (como texto alternativo) y comentarios HTML (se omiten).
"""
from __future__ import annotations

import argparse
import glob
import html as html_mod
import os
import re
import subprocess
import sys

CSS = """
@page { size: A4; margin: 18mm 16mm; }
* { box-sizing: border-box; }
body {
  font-family: "Segoe UI", -apple-system, Roboto, "Helvetica Neue", Arial, sans-serif;
  font-size: 10.5pt; line-height: 1.55; color: #1f2328; margin: 0;
}
h1 { font-size: 19pt; margin: 0 0 4px; padding-bottom: 6px; border-bottom: 2px solid #d0d7de; }
h2 { font-size: 14pt; margin: 22px 0 8px; padding-bottom: 4px; border-bottom: 1px solid #e5e7eb; }
h3 { font-size: 11.8pt; margin: 18px 0 6px; }
h4, h5, h6 { font-size: 10.8pt; margin: 14px 0 4px; }
h1, h2, h3, h4 { page-break-after: avoid; }
p { margin: 8px 0; }
p.meta { margin: 3px 0; }
ul, ol { margin: 8px 0; padding-left: 22px; }
li { margin: 3px 0; }
table { border-collapse: collapse; width: 100%; margin: 10px 0; font-size: 9.4pt; page-break-inside: avoid; }
th, td { border: 1px solid #d0d7de; padding: 5px 7px; vertical-align: top; text-align: left; }
th { background: #f6f8fa; font-weight: 600; }
code {
  background: #f6f8fa; padding: 1px 4px; border-radius: 3px;
  font-family: "DejaVu Sans Mono", Consolas, "Courier New", monospace; font-size: 9pt;
}
pre {
  background: #f6f8fa; border: 1px solid #d0d7de; border-radius: 6px;
  padding: 8px 10px; margin: 10px 0; overflow-x: auto; page-break-inside: avoid;
}
pre code { background: none; padding: 0; font-size: 8.8pt; }
blockquote {
  border-left: 3px solid #d0d7de; margin: 10px 0; padding: 2px 12px;
  background: #fbfcfd; color: #444c56;
}
blockquote h2, blockquote h3 { font-size: 11pt; margin: 8px 0 4px; border: none; padding: 0; }
blockquote p { margin: 4px 0; }
hr { border: none; border-top: 1px solid #d0d7de; margin: 16px 0; }
a { color: #0969da; text-decoration: none; word-break: break-word; }
img { max-width: 100%; }
"""

TOKEN = "\x00"


def buscar_chrome(explicito: str | None) -> str | None:
    if explicito:
        return explicito if os.path.exists(explicito) else None
    patrones = [
        "~/.cache/puppeteer/chrome/*/chrome-linux*/chrome",
        "~/.cache/puppeteer/chrome-headless-shell/*/chrome-headless-shell-linux*/chrome-headless-shell",
        "/usr/bin/google-chrome",
        "/usr/bin/chromium",
        "/usr/bin/chromium-browser",
    ]
    encontrados: list[str] = []
    for patron in patrones:
        encontrados += sorted(glob.glob(os.path.expanduser(patron)))
    for candidato in encontrados:
        if os.path.exists(candidato) and os.access(candidato, os.X_OK):
            return candidato
    return None


def en_linea(texto: str) -> str:
    """Aplica el formato en linea. Primero protege el codigo, despues escapa el resto."""
    trozos: list[str] = []

    def guardar(match: re.Match) -> str:
        trozos.append(match.group(1))
        return f"{TOKEN}{len(trozos) - 1}{TOKEN}"

    texto = re.sub(r"`([^`]+)`", guardar, texto)
    texto = html_mod.escape(texto, quote=False)
    texto = re.sub(r"!\[([^\]]*)\]\([^)]*\)", r"<em>[imagen: \1]</em>", texto)
    texto = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", r'<a href="\2">\1</a>', texto)
    texto = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", texto)
    texto = re.sub(r"(?<![\w*])\*([^*\n]+)\*(?![\w*])", r"<em>\1</em>", texto)
    texto = re.sub(r"(?<![\w_])_([^_\n]+)_(?![\w_])", r"<em>\1</em>", texto)
    texto = re.sub(r"^\[ \]\s*", "☐ ", texto)
    texto = re.sub(r"^\[[xX]\]\s*", "☑ ", texto)

    def devolver(match: re.Match) -> str:
        return "<code>" + html_mod.escape(trozos[int(match.group(1))]) + "</code>"

    return re.sub(rf"{TOKEN}(\d+){TOKEN}", devolver, texto)


RE_TITULO = re.compile(r"^(#{1,6})\s+(.*)$")
RE_HR = re.compile(r"^\s*(-{3,}|\*{3,}|_{3,})\s*$")
RE_VINETA = re.compile(r"^(\s*)([-*+])\s+(.*)$")
RE_NUMERO = re.compile(r"^(\s*)(\d+)[.)]\s+(.*)$")
RE_SEPARADOR_TABLA = re.compile(r"^\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?\s*$")
# Bloque de encabezado: lineas consecutivas que empiezan con una etiqueta en negrita, del tipo `**Fecha:** ...`.
# En Markdown son un solo parrafo, pero la intencion del autor es una linea por campo.
RE_ETIQUETA = re.compile(r"^\*\*[^*]+:\*\*")


def es_fila_tabla(linea: str) -> bool:
    return linea.count("|") >= 2


def celdas(linea: str) -> list[str]:
    linea = linea.strip()
    if linea.startswith("|"):
        linea = linea[1:]
    if linea.endswith("|"):
        linea = linea[:-1]
    return [c.strip() for c in linea.split("|")]


def tabla_html(bloque: list[str]) -> str:
    encabezado = celdas(bloque[0])
    alineaciones: list[str] = []
    for celda in celdas(bloque[1]):
        if celda.startswith(":") and celda.endswith(":"):
            alineaciones.append("center")
        elif celda.endswith(":"):
            alineaciones.append("right")
        elif celda.startswith(":"):
            alineaciones.append("left")
        else:
            alineaciones.append("")
    filas = bloque[2:]
    partes = ["<table><thead><tr>"]
    for indice, celda in enumerate(encabezado):
        estilo = f' style="text-align: {alineaciones[indice]}"' if indice < len(alineaciones) and alineaciones[indice] else ""
        partes.append(f"<th{estilo}>{en_linea(celda)}</th>")
    partes.append("</tr></thead><tbody>")
    for fila in filas:
        partes.append("<tr>")
        valores = celdas(fila)
        for indice in range(len(encabezado)):
            valor = valores[indice] if indice < len(valores) else ""
            estilo = f' style="text-align: {alineaciones[indice]}"' if indice < len(alineaciones) and alineaciones[indice] else ""
            partes.append(f"<td{estilo}>{en_linea(valor)}</td>")
        partes.append("</tr>")
    partes.append("</tbody></table>")
    return "".join(partes)


def convertir(markdown: str) -> str:
    lineas = markdown.split("\n")
    salida: list[str] = []
    parrafo: list[str] = []
    pila_listas: list[tuple[str, int]] = []
    indice = 0

    def cerrar_parrafo() -> None:
        if not parrafo:
            return
        if len(parrafo) > 1 and all(RE_ETIQUETA.match(una) for una in parrafo):
            # Encabezados del tipo `**Para:** ...` / `**Fecha:** ...`: una linea por campo, no un parrafo corrido.
            salida.append('<p class="meta">' + "<br>".join(en_linea(una) for una in parrafo) + "</p>")
        else:
            salida.append("<p>" + en_linea(" ".join(parrafo)) + "</p>")
        parrafo.clear()

    def cerrar_listas() -> None:
        while pila_listas:
            salida.append(f"</{pila_listas.pop()[0]}>")

    while indice < len(lineas):
        linea = lineas[indice]

        # Bloques de codigo con fences
        if linea.strip().startswith("```"):
            cerrar_parrafo()
            cerrar_listas()
            indice += 1
            cuerpo: list[str] = []
            while indice < len(lineas) and not lineas[indice].strip().startswith("```"):
                cuerpo.append(lineas[indice])
                indice += 1
            indice += 1
            salida.append("<pre><code>" + html_mod.escape("\n".join(cuerpo)) + "</code></pre>")
            continue

        # Comentarios HTML
        if linea.strip().startswith("<!--"):
            cerrar_parrafo()
            while indice < len(lineas) and "-->" not in lineas[indice]:
                indice += 1
            indice += 1
            continue

        # Tablas
        if es_fila_tabla(linea) and indice + 1 < len(lineas) and RE_SEPARADOR_TABLA.match(lineas[indice + 1]):
            cerrar_parrafo()
            cerrar_listas()
            bloque = [linea, lineas[indice + 1]]
            indice += 2
            while indice < len(lineas) and es_fila_tabla(lineas[indice]) and lineas[indice].strip():
                bloque.append(lineas[indice])
                indice += 1
            salida.append(tabla_html(bloque))
            continue

        # Citas (se convierten recursivamente para admitir titulos y listas dentro)
        if linea.lstrip().startswith(">"):
            cerrar_parrafo()
            cerrar_listas()
            interno: list[str] = []
            while indice < len(lineas) and lineas[indice].lstrip().startswith(">"):
                interno.append(re.sub(r"^\s*>\s?", "", lineas[indice]))
                indice += 1
            salida.append("<blockquote>\n" + convertir("\n".join(interno)) + "\n</blockquote>")
            continue

        if not linea.strip():
            cerrar_parrafo()
            cerrar_listas()
            indice += 1
            continue

        titulo = RE_TITULO.match(linea)
        if titulo:
            cerrar_parrafo()
            cerrar_listas()
            nivel = len(titulo.group(1))
            salida.append(f"<h{nivel}>{en_linea(titulo.group(2).strip())}</h{nivel}>")
            indice += 1
            continue

        if RE_HR.match(linea):
            cerrar_parrafo()
            cerrar_listas()
            salida.append("<hr>")
            indice += 1
            continue

        vineta = RE_VINETA.match(linea)
        numero = RE_NUMERO.match(linea)
        if vineta or numero:
            cerrar_parrafo()
            coincidencia = vineta or numero
            sangria = len(coincidencia.group(1).expandtabs(4))
            tipo = "ul" if vineta else "ol"

            # Continuacion del item: las lineas siguientes mas indentadas que el marcador pertenecen al mismo
            # item (el texto del repositorio esta envuelto a ~110 columnas), no a un parrafo aparte.
            partes_item = [coincidencia.group(3)]
            siguiente = indice + 1
            while siguiente < len(lineas):
                proxima = lineas[siguiente]
                if not proxima.strip():
                    break
                if (RE_TITULO.match(proxima) or RE_HR.match(proxima) or es_fila_tabla(proxima)
                        or proxima.lstrip().startswith((">", "```"))
                        or RE_VINETA.match(proxima) or RE_NUMERO.match(proxima)):
                    break
                if len(proxima) - len(proxima.lstrip()) <= sangria:
                    break
                partes_item.append(proxima.strip())
                siguiente += 1
            contenido = " ".join(partes_item)
            indice = siguiente

            while pila_listas and sangria < pila_listas[-1][1]:
                salida.append(f"</{pila_listas.pop()[0]}>")
            if not pila_listas:
                pila_listas.append((tipo, sangria))
                salida.append(f"<{tipo}>")
            elif sangria > pila_listas[-1][1]:
                pila_listas.append((tipo, sangria))
                salida.append(f"<{tipo}>")
            elif tipo != pila_listas[-1][0]:
                salida.append(f"</{pila_listas.pop()[0]}>")
                pila_listas.append((tipo, sangria))
                salida.append(f"<{tipo}>")

            salida.append(f"<li>{en_linea(contenido)}</li>")
            continue

        parrafo.append(linea.strip())
        indice += 1

    cerrar_parrafo()
    cerrar_listas()
    return "\n".join(salida)


def plantilla(titulo: str, cuerpo: str) -> str:
    return (
        "<!DOCTYPE html>\n"
        '<html lang="es"><head><meta charset="utf-8">'
        f"<title>{html_mod.escape(titulo)}</title><style>{CSS}</style></head>\n"
        f"<body>\n{cuerpo}\n</body></html>\n"
    )


def a_pdf(chrome: str, html_path: str, pdf_path: str) -> tuple[bool, str]:
    orden = [
        chrome,
        "--headless=new",
        "--disable-gpu",
        "--no-sandbox",
        "--hide-scrollbars",
        "--no-pdf-header-footer",
        f"--print-to-pdf={pdf_path}",
        "file://" + os.path.abspath(html_path),
    ]
    proceso = subprocess.run(orden, capture_output=True, text=True, timeout=300)
    if os.path.exists(pdf_path) and os.path.getsize(pdf_path) > 1000:
        return True, proceso.stderr.strip()[-400:]
    return False, (proceso.stderr or proceso.stdout).strip()[-400:]


def paginas(pdf_path: str) -> int:
    with open(pdf_path, "rb") as handle:
        crudo = handle.read()
    return max(crudo.count(b"/Type /Page\n"), crudo.count(b"/Type/Page"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Convierte un Markdown del proyecto a PDF.")
    parser.add_argument("entrada", help="archivo .md de entrada")
    parser.add_argument("--out", default=None, help="PDF de salida (por defecto, al lado del .md)")
    parser.add_argument("--html", action="store_true", help="deja tambien el HTML intermedio")
    parser.add_argument("--solo-html", action="store_true", help="genera solo el HTML, sin PDF")
    parser.add_argument("--chrome", default=None, help="binario de Chrome o Chromium a usar")
    args = parser.parse_args()

    if not os.path.isfile(args.entrada):
        print(f"No existe el archivo de entrada: {args.entrada}", file=sys.stderr)
        return 2

    with open(args.entrada, encoding="utf-8") as handle:
        markdown = handle.read()

    base = os.path.splitext(os.path.abspath(args.entrada))[0]
    # El HTML intermedio se deja junto a la SALIDA, no junto a la entrada: asi no ensucia el repositorio
    # con archivos sin rastrear cuando el PDF se escribe fuera.
    base_html = os.path.splitext(os.path.abspath(args.out))[0] if args.out else base
    html_path = base_html + ".render.html"
    with open(html_path, "w", encoding="utf-8") as handle:
        handle.write(plantilla(os.path.basename(args.entrada), convertir(markdown)))
    print(f"HTML: {html_path} ({os.path.getsize(html_path) / 1024:.0f} KB)")

    if args.solo_html:
        return 0

    pdf_path = os.path.abspath(args.out) if args.out else base + ".pdf"
    chrome = buscar_chrome(args.chrome)
    if not chrome:
        print("No se encontro Chrome ni Chromium. Usa --chrome <ruta>.", file=sys.stderr)
        return 2
    print(f"Chromium: {chrome}")

    ok, detalle = a_pdf(chrome, html_path, pdf_path)
    if not ok:
        print(f"Fallo la generacion del PDF: {detalle}", file=sys.stderr)
        return 1

    print(f"PDF: {pdf_path} ({os.path.getsize(pdf_path) / 1024:.0f} KB, ~{paginas(pdf_path)} paginas)")
    if not args.html:
        os.remove(html_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
