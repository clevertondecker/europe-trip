"""Read-only synchronization of decisions and tasks from Google Drive."""
from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

DOC_IDS = {
    "decisions": "12O55HyOZsyv68qntsZbbVAeiw4tQnKrpG61i2_kZJBo",
    "tasks": "1kFvDkGO8tGXoVGcBMisntyoVGZNTDHwUT7Me7vVH1pY",
}
SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]

def parse_decisions(text: str) -> list[dict[str, str]]:
    result = []
    for line in text.splitlines():
        m = re.match(r"\s*(D-\d+)\s*\|\s*([^|]+)\|\s*(.+?)\s*$", line)
        if m:
            ident, status, description = m.groups()
            result.append({"id": ident, "status": status.strip(), "title": description.strip(), "note": description.strip()})
    return result

def parse_tasks(text: str) -> list[dict[str, str]]:
    tasks, priority = [], None
    for line in text.splitlines():
        header = re.match(r"\s*P([0-3])\s*[—–-]\s+", line)
        if header:
            priority = f"P{header.group(1)}"
            continue
        if line.strip().startswith("REGISTRO DE PROGRESSO"):
            break
        m = re.match(r"\s*\[([ xX])\]\s*(.+)", line)
        if m and priority:
            tasks.append({"priority": priority, "title": m.group(2).strip(),
                          "status": "concluído" if m.group(1).lower() == "x" else "pendente"})
    return tasks

def google_docs_text(service: Any, file_id: str) -> str:
    content = service.files().export(fileId=file_id, mimeType="text/plain").execute()
    return content.decode("utf-8-sig") if isinstance(content, bytes) else str(content)

def load_live_updates(service_account: dict[str, Any]) -> dict[str, Any]:
    from google.oauth2 import service_account as google_service_account
    from googleapiclient.discovery import build
    creds = google_service_account.Credentials.from_service_account_info(service_account, scopes=SCOPES)
    service = build("drive", "v3", credentials=creds, cache_discovery=False)
    decisions = parse_decisions(google_docs_text(service, DOC_IDS["decisions"]))
    tasks = parse_tasks(google_docs_text(service, DOC_IDS["tasks"]))
    if not decisions or not tasks:
        raise ValueError("Unexpected source format; keeping snapshot")
    return {"decisions": decisions, "tasks": tasks,
            "synced_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}
