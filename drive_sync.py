"""Read-only, source-aware Google Drive synchronization for the Europa 2027 app.

No credentials are stored here. The workbook's formulas are independently reproduced
from its 03 PREMISSAS inputs, and cached XLSM outputs are cross-checked, not trusted.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from io import BytesIO
import re
from typing import Any
from xml.etree import ElementTree as ET
from zipfile import ZipFile

DOC_IDS = {
    "decisions": "12O55HyOZsyv68qntsZbbVAeiw4tQnKrpG61i2_kZJBo",
    "tasks": "1kFvDkGO8tGXoVGcBMisntyoVGZNTDHwUT7Me7vVH1pY",
    "finance": "1LeTrUWLLzIe_mZS26gMt_KMnnX4jelZ4",
}
SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]
NS = {"x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
CATEGORIES = (
    "Passagens e deslocamentos aéreos do casal",
    "Itália (~10 dias)",
    "França · aluguel mobiliado",
    "França · supermercado",
    "França · bares e restaurantes",
    "França · transporte urbano",
    "França · passeios e viagens",
    "Instalação na França",
    "Seguro viagem do casal",
    "Taxas e despesas diversas",
    "Reserva emergencial (incluída)",
)


def parse_decisions(text: str) -> list[dict[str, str]]:
    out = []
    for line in text.splitlines():
        match = re.match(r"\s*(D-\d+)\s*\|\s*([^|]+)\|\s*(.+?)\s*$", line)
        if match:
            code, status, description = match.groups()
            out.append({"id": code, "status": status.strip(), "title": description.strip(), "note": description.strip()})
    if not out or not any(d["id"] == "D-001" for d in out):
        raise ValueError("Documento de decisões não corresponde ao formato esperado")
    return out


def parse_tasks(text: str) -> list[dict[str, str]]:
    out, priority = [], None
    for line in text.splitlines():
        header = re.match(r"\s*P([0-3])\s*[—–-]\s+", line)
        if header:
            priority = f"P{header.group(1)}"
            continue
        if line.strip().startswith("REGISTRO DE PROGRESSO"):
            break
        match = re.match(r"\s*\[([ xX])\]\s*(.+)", line)
        if priority and match:
            out.append({"priority": priority, "title": match.group(2).strip(),
                        "status": "concluído" if match.group(1).lower() == "x" else "pendente"})
    if not out or not any(x["priority"] == "P0" for x in out):
        raise ValueError("Documento de pendências não corresponde ao formato esperado")
    return out


def parse_sheet_cells(xml: bytes, shared_strings: list[str]) -> dict[str, Any]:
    root = ET.fromstring(xml)
    cells = {}
    for cell in root.findall(".//x:sheetData/x:row/x:c", NS):
        address = cell.attrib["r"]
        val = cell.find("x:v", NS)
        inline = cell.find("x:is", NS)
        kind = cell.attrib.get("t")
        if kind == "inlineStr" and inline is not None:
            cells[address] = "".join(inline.itertext())
        elif val is not None and val.text is not None:
            raw = val.text
            if kind == "s":
                cells[address] = shared_strings[int(raw)]
            elif kind in ("str", "e"):
                cells[address] = raw
            else:
                try:
                    cells[address] = float(raw)
                except ValueError:
                    cells[address] = raw
    return cells


def parse_workbook(content: bytes) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    # Canonical workbook was inspected: sheet2=02 ORÇAMENTO, sheet3=03 PREMISSAS,
    # sheet4=04 ROTEIRO E TRABALHO. Guard against sheet reordering.
    with ZipFile(BytesIO(content)) as archive:
        book = ET.fromstring(archive.read("xl/workbook.xml"))
        names = [node.attrib["name"] for node in book.findall(".//x:sheets/x:sheet", NS)]
        if names[1:4] != ["02 ORÇAMENTO", "03 PREMISSAS", "04 ROTEIRO E TRABALHO"]:
            raise ValueError("Abas oficiais alteradas; atualizar mapeamento antes de sincronizar")
        shared = []
        if "xl/sharedStrings.xml" in archive.namelist():
            strings = ET.fromstring(archive.read("xl/sharedStrings.xml"))
            shared = ["".join(n.itertext()) for n in strings]
        budget = parse_sheet_cells(archive.read("xl/worksheets/sheet2.xml"), shared)
        assumptions = parse_sheet_cells(archive.read("xl/worksheets/sheet3.xml"), shared)
        itinerary = parse_sheet_cells(archive.read("xl/worksheets/sheet4.xml"), shared)
    if "DESPESA" not in str(budget.get("A1", "")) or "PREMISSA" not in str(assumptions.get("A1", "")):
        raise ValueError("Cabeçalho do modelo financeiro inesperado")
    return budget, assumptions, itinerary


def excel_date(value: float) -> str:
    return (datetime(1899, 12, 30) + timedelta(days=int(value))).date().isoformat()


def model_budget(assumptions: dict[str, Any], budget: dict[str, Any]) -> dict[str, Any]:
    """Reproduce the 02 ORÇAMENTO formulas from the validated 03 PREMISSAS layout."""
    scenarios, issues = [], []
    for col, scenario_id in (("B", "60k"), ("C", "70k")):
        def n(row: int) -> float:
            v = assumptions.get(f"{col}{row}")
            if not isinstance(v, (float, int)):
                raise ValueError(f"Premissa {col}{row} ausente ou não numérica")
            return float(v)

        fx = n(5) * (1 + n(30))
        components = [
            sum(n(r) for r in range(12, 17)), n(17), n(18) * n(19) * fx,
            n(9) * n(20) * fx, n(21) * n(22) * fx,
            n(23) * fx, n(24), n(25), n(26), n(27), n(28),
        ]
        total = sum(components)
        cache_total = budget.get(f"{col}15")
        if not isinstance(cache_total, (int, float)):
            issues.append(f"{scenario_id}: total de fórmula sem cache; valor recalculado a partir das premissas")
        elif abs(total - cache_total) > 0.10:
            issues.append(f"{scenario_id}: cache da planilha diverge das premissas (diferença R$ {abs(total-cache_total):.2f})")
        if n(2) != 2 or n(7) not in (60000, 70000) or n(8) <= n(10):
            raise ValueError("Premissas críticas do casal foram alteradas; revisar modelo")
        scenarios.append({
            "id": scenario_id, "label": f"R$ {int(n(7)/1000)} mil",
            "cap_brl": n(7), "reported_total_brl": total,
            "emergency_reserve_brl": n(28), "days": int(n(8)),
            "components": [{"name": label, "amount": val} for label, val in zip(CATEGORIES, components)],
            "evidence_status": "estimativa da planilha — não cotação real",
        })
    if excel_date(assumptions["B3"]) != "2027-09-04":
        raise ValueError("Data do casamento diverge da premissa fixa")
    departure = excel_date(assumptions["B4"])
    if departure <= "2027-09-04":
        raise ValueError("Hipótese de saída deve ser posterior ao casamento")
    meta = {
        "wedding_date": "2027-09-04", "departure_candidate": departure,
        "travelers": 2, "duration_min_days": int(assumptions["B8"]),
        "duration_max_days": int(assumptions["C8"]),
        "italy_days_approx": int(assumptions["B10"]),
        "france_days_estimate": f"{int(assumptions['B9'])}–{int(assumptions['C9'])} dias",
        "initial_vacation_days": f"{int(assumptions['B11'])} dias (premissa financeira)",
    }
    return {"budget_scenarios": scenarios, "metadata": meta, "issues": issues}


def model_timeline(cells: dict[str, Any]) -> list[dict[str, str]]:
    if "PERÍODO" not in str(cells.get("A1", "")):
        raise ValueError("Cronograma de referência não reconhecido")
    out = []
    for row in range(2, 10):
        period, place, description, status = (str(cells.get(f"{col}{row}", "")).strip() for col in "ABCD")
        if all((period, place, description, status)):
            out.append({"stage": place, "period": period, "status": status.lower(), "details": description})
    if len(out) < 6 or "Casamento" not in out[0]["details"]:
        raise ValueError("Cronograma oficial vazio ou incompatível")
    return out


def chosen_city(decisions: list[dict[str, str]]) -> str | None:
    """Only mark a city as chosen if D-004 explicitly records an approved decision."""
    candidate = next((x for x in decisions if x["id"] == "D-004"), None)
    if candidate is None or not candidate["status"].strip().lower().startswith(("vigente", "aprovada", "decidida")):
        return None
    found = [c for c in ("mulhouse", "strasbourg", "metz", "nancy") if re.search(r"\b"+c+r"\b", candidate["title"].lower())]
    return found[0] if len(found) == 1 else None


def update_map_places(places: list[dict], decisions: list[dict]) -> list[dict]:
    chosen = chosen_city(decisions)
    updated = [dict(place) for place in places]
    for place in updated:
        if place["id"] == chosen:
            place["status"] = "roteiro_proposto"
            place["description"] = "Cidade-base aprovada no documento 01_ESTADO_ATUAL; confirmar locação e transportes."
            place["source"] = "decisions"
    return updated


def load_live_updates(service_account: dict[str, Any]) -> dict[str, Any]:
    from google.oauth2 import service_account as google_service_account
    from googleapiclient.discovery import build
    credentials = google_service_account.Credentials.from_service_account_info(service_account, scopes=SCOPES)
    drive = build("drive", "v3", credentials=credentials, cache_discovery=False)
    results: dict[str, Any] = {"synced_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                                "source_status": {}, "issues": []}
    for key, file_id in DOC_IDS.items():
        try:
            metadata = drive.files().get(fileId=file_id, fields="id,name,mimeType,modifiedTime,webViewLink").execute()
            if key == "finance":
                if metadata.get("mimeType") != "application/vnd.ms-excel.sheet.macroenabled.12":
                    raise ValueError("Planilha oficial não é mais XLSM")
                raw = drive.files().get_media(fileId=file_id).execute()
                b, a, i = parse_workbook(raw)
                financial = model_budget(a, b)
                results.update(financial)
                results["timeline"] = model_timeline(i)
                results["issues"].extend(financial["issues"])
                # Prevent unknown top-level keys from overwriting unexpected source metadata.
                results.pop("metadata", None)
                results["trip_metadata"] = financial["metadata"]
            else:
                content = drive.files().export(fileId=file_id, mimeType="text/plain").execute()
                text = content.decode("utf-8-sig") if isinstance(content, bytes) else str(content)
                results[key] = parse_decisions(text) if key == "decisions" else parse_tasks(text)
            results["source_status"][key] = {"status": "live", "modified_at": metadata.get("modifiedTime", "unknown")}
        except Exception as exc:
            # Keep a snapshot for this individual section; do not print OAuth secrets or URLs.
            results["source_status"][key] = {"status": "snapshot", "reason": type(exc).__name__}
            results["issues"].append(f"{key}: falha de leitura/validação ({type(exc).__name__}); exibindo snapshot")
    return results