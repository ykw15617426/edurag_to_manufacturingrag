"""Resolve one authoritative YAML source, then call the existing file loader."""
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory

import yaml
from pydantic import ValidationError

from rag_qa.schemas.manufacturing_metadata import ManufacturingDocumentMetadata
from rag_qa.ingestion.fingerprints import sha256_file


class ManufacturingMetadataError(ValueError):
    def __init__(self, source_file, metadata_source, field, reason):
        self.source_file = str(source_file)
        self.metadata_source = str(metadata_source)
        self.field = field
        self.reason = reason
        super().__init__(f"file={self.source_file}; metadata={self.metadata_source}; "
                         f"field={field}; reason={reason}")


class MissingMetadataError(ManufacturingMetadataError):
    pass


class MetadataSourceConflictError(ManufacturingMetadataError):
    pass


class InvalidYamlMetadataError(ManufacturingMetadataError):
    pass


class InvalidManufacturingMetadataError(ManufacturingMetadataError):
    pass


class MetadataMergeConflictError(ManufacturingMetadataError):
    pass


class _UniqueSafeLoader(yaml.SafeLoader):
    """SafeLoader with duplicate mapping keys rejected instead of overwritten."""


def _unique_mapping(loader, node, deep=False):
    mapping = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        try:
            duplicate = key in mapping
        except TypeError:
            raise yaml.constructor.ConstructorError(None, None, "invalid mapping key", key_node.start_mark)
        if duplicate:
            raise yaml.constructor.ConstructorError(None, None, "duplicate mapping key", key_node.start_mark)
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


_UniqueSafeLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _unique_mapping)


@dataclass(frozen=True)
class ResolvedMetadata:
    source_file: Path
    metadata_source: str
    metadata_location: str
    business_metadata: dict
    body: str | None = None


def resolve_metadata(source_file):
    """Manufacturing-only discovery. Legacy callers never invoke this function."""
    path = Path(source_file)
    sidecar = Path(str(path) + ".yaml")
    lines = None
    has_front_matter = False
    if path.suffix.lower() in {".md", ".txt"}:
        try:
            lines = path.read_text(encoding="utf-8-sig").splitlines(keepends=True)
        except (OSError, UnicodeError):
            raise InvalidYamlMetadataError(path, "front_matter", "<document>", "cannot read UTF-8 text") from None
        has_front_matter = bool(lines and lines[0].strip() == "---")
    if has_front_matter and sidecar.exists():
        raise MetadataSourceConflictError(path, f"front_matter + {sidecar}", "<source>",
                                          "one authoritative metadata source is required")
    body = None
    if has_front_matter:
        kind, location = "front_matter", f"{path}:front_matter"
        end = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
        if end is None:
            raise InvalidYamlMetadataError(path, location, "<yaml>", "missing closing front matter delimiter")
        yaml_text = "".join(lines[1:end])
        body = "".join(lines[end + 1:])
    elif sidecar.exists():
        kind, location = "sidecar", str(sidecar)
        try:
            yaml_text = sidecar.read_text(encoding="utf-8-sig")
        except (OSError, UnicodeError):
            raise InvalidYamlMetadataError(path, location, "<yaml>", "cannot read UTF-8 sidecar") from None
    else:
        raise MissingMetadataError(path, sidecar, "<source>", "no front matter or full-filename sidecar")
    try:
        # Reject ambiguous duplicate keys before safe_load's last-key-wins behavior.
        yaml.load(yaml_text, Loader=_UniqueSafeLoader)
        data = yaml.safe_load(yaml_text)
    except yaml.YAMLError as exc:
        mark = getattr(exc, "problem_mark", None)
        reason = "invalid or unsafe YAML"
        if mark is not None:
            reason += f" at line {mark.line + 1}, column {mark.column + 1}"
        raise InvalidYamlMetadataError(path, location, "<yaml>", reason) from None
    if not isinstance(data, dict) or not data:
        raise InvalidYamlMetadataError(path, location, "<yaml>", "nonempty top-level mapping required")
    try:
        validated = ManufacturingDocumentMetadata.model_validate(data)
    except ValidationError as exc:
        errors = exc.errors(include_input=False, include_context=False, include_url=False)
        fields = "; ".join(".".join(str(part) for part in error["loc"]) or "<model>" for error in errors)
        reasons = "; ".join(error["msg"] for error in errors)
        raise InvalidManufacturingMetadataError(path, location, fields, reasons) from None
    return ResolvedMetadata(path, kind, location, validated.to_metadata(), body)


def load_with_metadata(source_file, load_file):
    """load_file(path) uses the caller's existing loader; no new parsing engine."""
    resolved = resolve_metadata(source_file)  # fail before the file loader runs
    # Hash the original file, never the sanitized Front Matter body/sidecar.
    document_sha256 = sha256_file(source_file)
    if resolved.body is None:
        documents = load_file(str(source_file))
    else:
        # Keep the original extension/name for the existing TXT/Markdown loader.
        # Windows loaders must open the file after it has been closed.
        with TemporaryDirectory(prefix="manufacturing_metadata_") as directory:
            sanitized = Path(directory) / resolved.source_file.name
            sanitized.write_text(resolved.body, encoding="utf-8")
            documents = load_file(str(sanitized))
            for document in documents:
                for key in ("source", "file_path"):
                    if document.metadata.get(key) == str(sanitized):
                        document.metadata[key] = str(source_file)
    additions = dict(resolved.business_metadata,
                     document_sha256=document_sha256,
                     source_file=str(resolved.source_file.resolve()),
                     metadata_source=resolved.metadata_source)
    for document in documents:
        overlap = document.metadata.keys() & additions.keys()
        if overlap:
            raise MetadataMergeConflictError(source_file, resolved.metadata_location,
                                              ",".join(sorted(overlap)), "loader metadata conflicts with validated metadata")
        document.metadata.update(additions)
    return documents
