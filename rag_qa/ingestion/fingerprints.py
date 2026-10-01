"""Stage 2 fingerprints and deterministic identities; no persistence or skip logic."""
import hashlib
import json
from pathlib import Path
import unicodedata


def sha256_file(path: str | Path) -> str:
    """Fingerprint original source bytes, excluding any sidecar metadata."""
    digest = hashlib.sha256()
    with open(path, "rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def normalize_content_for_hash(text: str) -> str:
    """Normalize formatting only; never change stored/displayed page_content."""
    text = unicodedata.normalize("NFC", text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    return "\n".join(line.rstrip() for line in text.split("\n")).strip()


def sha256_content(text: str) -> str:
    return hashlib.sha256(normalize_content_for_hash(text).encode("utf-8")).hexdigest()


def _identity(components: list) -> str:
    # Ordered JSON array preserves component boundaries and integer occurrences.
    payload = json.dumps(components, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def build_parent_id(document_id: str, parent_content_sha256: str, occurrence: int = 0) -> str:
    return _identity(["parent", document_id, parent_content_sha256, occurrence])


def build_child_id(document_id: str, parent_id: str, child_content_sha256: str,
                   occurrence: int = 0) -> str:
    return _identity(["child", document_id, parent_id, child_content_sha256, occurrence])
