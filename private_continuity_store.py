"""Optional UX 3.6 owner-only private persistence in Google Cloud Storage.

Requires a dedicated private GCS bucket, configured explicitly in Streamlit
secrets. Never sends archives, tokens or notes to the public GitHub repository.
GCS object generations provide optimistic concurrency across browser sessions.
"""
from __future__ import annotations

import hashlib
import re
from urllib.parse import quote

from google.auth.transport.requests import AuthorizedSession
from google.auth.exceptions import GoogleAuthError
from requests.exceptions import RequestException
from google.oauth2.service_account import Credentials

MAX_ARCHIVE_BYTES = 450_000
_SCOPE = ["https://www.googleapis.com/auth/devstorage.read_write"]
_BUCKET = re.compile(r"^[a-z0-9][a-z0-9._-]{2,221}[a-z0-9]$")


class StorageConflict(Exception):
    """Remote content changed since this session last retrieved it."""


class StorageUnavailable(Exception):
    """Private storage not configured or temporarily unavailable."""


def object_key(owner_email: str) -> str:
    """Opaque per-owner namespace; no raw email addresses in object names."""
    if not isinstance(owner_email, str) or "@" not in owner_email:
        raise ValueError("Proprietário inválido")
    digest = hashlib.sha256(owner_email.strip().casefold().encode()).hexdigest()
    return f"ux36/owners/{digest}/current.json"


def validate_private_config(bucket: str, account: dict) -> None:
    if not isinstance(bucket, str) or not _BUCKET.fullmatch(bucket):
        raise StorageUnavailable("Bucket privado não configurado")
    if not isinstance(account, dict) or not account.get("client_email") or not account.get("private_key"):
        raise StorageUnavailable("Credencial privada indisponível")


class PrivateArchiveStore:
    def __init__(self, bucket: str, service_account: dict, owner_email: str):
        validate_private_config(bucket, service_account)
        self.bucket = bucket
        self.key = object_key(owner_email)
        credentials = Credentials.from_service_account_info(service_account, scopes=_SCOPE)
        self.http = AuthorizedSession(credentials)

    def _metadata_url(self):
        return ("https://storage.googleapis.com/storage/v1/b/"
                + quote(self.bucket, safe="") + "/o/" + quote(self.key, safe=""))

    def load(self) -> tuple[bytes, int] | None:
        try:
            response = self.http.get(self._metadata_url(), timeout=12)
        except (GoogleAuthError, RequestException) as exc:
            raise StorageUnavailable("Não foi possível acessar armazenamento privado") from exc
        if response.status_code == 404:
            return None
        if response.status_code != 200:
            raise StorageUnavailable("Não foi possível consultar cópia privada")
        metadata = response.json()
        try:
            generation = int(metadata["generation"])
        except (ValueError, TypeError, KeyError) as exc:
            raise StorageUnavailable("Metadados inválidos da cópia privada") from exc
        try:
            data = self.http.get(self._metadata_url(), params={"alt": "media", "generation": generation}, timeout=12)
        except (GoogleAuthError, RequestException) as exc:
            raise StorageUnavailable("Não foi possível baixar cópia privada") from exc
        if data.status_code in (404, 412):
            raise StorageConflict("A cópia mudou durante a leitura")
        if data.status_code != 200 or len(data.content) > MAX_ARCHIVE_BYTES:
            raise StorageUnavailable("Cópia privada indisponível ou muito grande")
        return data.content, generation

    def save(self, raw: bytes, expected_generation: int | None) -> int:
        if not isinstance(raw, bytes) or not 0 < len(raw) <= MAX_ARCHIVE_BYTES:
            raise ValueError("Cópia privada inválida")
        if expected_generation is not None and (
            type(expected_generation) is not int or expected_generation < 1
        ):
            raise ValueError("Versão de salvamento inválida")
        # Never overwrite an existing object without its exact generation.
        try:
            response = self.http.post(
            "https://storage.googleapis.com/upload/storage/v1/b/"
            + quote(self.bucket, safe="") + "/o",
            params={
                "uploadType": "media",
                "name": self.key,
                "ifGenerationMatch": str(expected_generation or 0),
            },
            data=raw,
            headers={"Content-Type": "application/json; charset=utf-8"},
            timeout=15,
            )
        except (GoogleAuthError, RequestException) as exc:
            raise StorageUnavailable("Conexão indisponível; nenhuma cópia privada foi confirmada") from exc
        if response.status_code in (409, 412):
            raise StorageConflict("Outra sessão salvou alterações; recupere e compare antes de sobrescrever")
        if response.status_code not in (200, 201):
            raise StorageUnavailable("Falha ao salvar cópia privada; mantenha o backup local")
        try:
            return int(response.json()["generation"])
        except (KeyError, TypeError, ValueError) as exc:
            raise StorageUnavailable("A gravação não retornou versão confirmada") from exc
