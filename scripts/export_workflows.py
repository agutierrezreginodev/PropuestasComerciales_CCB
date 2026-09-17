#!/usr/bin/env python3
"""Export the CCB production workflows from n8n and anonymize them for this
public repository.

Usage:
    N8N_API_URL="https://<instance>" N8N_API_KEY="<key>" python3 scripts/export_workflows.py

The credentials are read from the environment only; they are never written to
disk nor printed. The script applies exactly the replacement table documented
in README.md ("Anonimización") and drops the `shared` block that n8n adds to
every export.

It prints a per-workflow report and fails loudly if any e-mail address from a
non-placeholder domain survives the anonymization pass, so a leak cannot slip
into a commit unnoticed.
"""
from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.request

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(REPO_ROOT, "workflows")

# file name (without extension) -> workflow id in n8n
WORKFLOWS = {
    "w1-extraccion-informacion-cliente": "w6h0qSblUESIpSVc",
    "w2-formulario-solicitud": "lIcdT6nGd0w1G2i0",
    "w2a-guardar-criterios-cotizar-servicio": "VChcasvisGKekezR",
    "w2c-recepcion-formulario-externo": "u6KCMnLwFOp6Ja0N",
    "w3-motor-criterios-precio": "cHOIOEFB5nbltN82",
    "w4a-router-aprobacion": "7gmpPMBJtEb0W3J5",
    "w4b-aprobacion-propuesta-teams": "5RJdnHDQ8NuWZJG7",
    "w4c-consultar-propuesta-revision": "KuLSIzBZgaRIjuSu",
    "w4d-procesar-decision-propuesta": "W0TDH4b0tHCNOzFQ",
    "w5a-router-envio": "gvIn6mbAn2Y1bMRR",
    "w5b-envio-al-cliente": "XWBHgbmtBubA4gqx",
    "w6-finalizador-cotizaciones": "mPwl4qUb0zQkmDHN",
    "error-workflow-catchall": "Dh2lAQTzyoZBpXie",
}

# Literal replacements — see README.md "Anonimización" for the documented table.
#
# The literals themselves are the very values we are hiding, so they must NEVER be
# committed: they live in `scripts/anonymization.local.json`, which is git-ignored.
# Copy `scripts/anonymization.example.json` and fill in the real values.
# Order matters: put the full name before the given name, and the longest match first.
LITERALS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "anonymization.local.json")


def load_literals() -> list[tuple[str, str]]:
    if not os.path.exists(LITERALS_FILE):
        raise SystemExit(
            f"Missing {os.path.basename(LITERALS_FILE)}. "
            "Copy anonymization.example.json to anonymization.local.json and fill in the real values."
        )
    with open(LITERALS_FILE, encoding="utf-8") as handle:
        pairs = json.load(handle)
    return [(entry["original"], entry["placeholder"]) for entry in pairs]

# Pattern replacements — name, regex, placeholder.
PATTERNS = [
    # Defensive: a URL carrying inline credentials must never reach a public repo.
    ("url_con_credenciales", re.compile(r"https?://[^/\s\"'<>:@]+:[^/\s\"'<>@]+@"), "https://<REDACTED_AUTH>@"),
    ("url_microservicio_pdf", re.compile(r"https?://[a-zA-Z0-9-]+\.ngrok[a-zA-Z0-9.-]*"), "https://pdf-service.example.com"),
    ("url_sharepoint", re.compile(r"https?://[a-zA-Z0-9-]+(?:-my)?\.sharepoint\.com[^\"'\s\\]*"), "https://<EXCEL_SITE_ID>/<EXCEL_WORKBOOK_ID>"),
    # Microsoft Teams chat identifiers (tenant-scoped, e.g. 19:<hash>@unq.gbl.spaces).
    ("teams_chat_id", re.compile(r"\d+:[A-Za-z0-9_-]+@unq\.gbl\.spaces"), "<TEAMS_CHAT_ID>"),
    # Outlook folder/message identifiers (base64-ish, start with AAMk).
    ("outlook_folder_id", re.compile(r"AAMk[A-Za-z0-9+/=_-]{30,}"), "<OUTLOOK_FOLDER_ID>"),
]

# Resource-locator parameters whose value identifies internal infrastructure.
PARAM_KEYS = {
    "folderId": "<OUTLOOK_FOLDER_ID>",
    "workbook": "<EXCEL_WORKBOOK_ID>",
    "worksheet": "<EXCEL_WORKSHEET_ID>",
}

EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
ALLOWED_EMAIL_DOMAINS = {"example.com"}


def fetch(base: str, key: str, workflow_id: str) -> dict:
    request = urllib.request.Request(
        f"{base}/api/v1/workflows/{workflow_id}",
        headers={"X-N8N-API-KEY": key, "accept": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=90) as response:
        return json.load(response)


def scrub_resource_locators(payload: dict) -> int:
    """Replace the value of every sensitive resource-locator parameter."""
    replaced = 0

    def walk(node):
        nonlocal replaced
        if isinstance(node, dict):
            for key, value in list(node.items()):
                placeholder = PARAM_KEYS.get(key)
                if placeholder and isinstance(value, dict) and "value" in value:
                    if value.get("value") not in (None, "", placeholder):
                        value["value"] = placeholder
                        replaced += 1
                    value.pop("cachedResultUrl", None)
                elif placeholder and isinstance(value, str) and value not in ("", placeholder):
                    node[key] = placeholder
                    replaced += 1
                else:
                    walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(payload)
    return replaced


def mask(address: str) -> str:
    local, _, domain = address.partition("@")
    return f"{local[:2]}***@{domain}"


def main() -> int:
    base = os.environ.get("N8N_API_URL", "").rstrip("/")
    key = os.environ.get("N8N_API_KEY", "")
    if not base or not key:
        print("N8N_API_URL and N8N_API_KEY must be set in the environment.", file=sys.stderr)
        return 2

    literals = load_literals()
    os.makedirs(OUT_DIR, exist_ok=True)
    rows = []
    leaks = {}
    pattern_totals = {name: 0 for name, _, _ in PATTERNS}

    for filename, workflow_id in WORKFLOWS.items():
        try:
            workflow = fetch(base, key, workflow_id)
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
            rows.append((filename, "ERROR", type(exc).__name__, "-", "-"))
            continue

        workflow.pop("shared", None)
        locator_hits = scrub_resource_locators(workflow)

        text = json.dumps(workflow, indent=2, ensure_ascii=False)
        literal_hits = 0
        for original, placeholder in literals:
            occurrences = text.count(original)
            if occurrences:
                literal_hits += occurrences
                text = text.replace(original, placeholder)
        for name, pattern, placeholder in PATTERNS:
            text, hits = pattern.subn(placeholder, text)
            pattern_totals[name] += hits

        surviving = {
            address
            for address in EMAIL_RE.findall(text)
            if address.split("@")[1].lower() not in ALLOWED_EMAIL_DOMAINS
        }
        if surviving:
            leaks[filename] = sorted(mask(address) for address in surviving)

        with open(os.path.join(OUT_DIR, f"{filename}.json"), "w", encoding="utf-8") as handle:
            handle.write(text + "\n")

        rows.append(
            (
                filename,
                str(len(workflow.get("nodes", []))),
                str(workflow.get("versionCounter", "-")),
                str(literal_hits),
                str(locator_hits),
            )
        )

    print(f"{'archivo':<42}{'nodos':>7}{'version':>9}{'literales':>11}{'locators':>10}")
    for row in rows:
        print(f"{row[0]:<42}{row[1]:>7}{row[2]:>9}{row[3]:>11}{row[4]:>10}")
    print("\nReemplazos por patron:", pattern_totals)

    if leaks:
        print("\nATENCION - correos fuera de la lista de placeholders:", file=sys.stderr)
        for filename, addresses in leaks.items():
            print(f"  {filename}: {', '.join(addresses)}", file=sys.stderr)
        print("Revisar y ampliar la tabla de anonimizacion antes de commitear.", file=sys.stderr)
        return 1

    print("\nSin correos pendientes de anonimizar.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
