"""Manufacturing Parent identity and evidence; no runtime model/SDK imports."""
from dataclasses import dataclass
from copy import deepcopy
from math import isfinite
from numbers import Real
from types import MappingProxyType
from typing import Mapping

from rag_qa.core.milvus_schema import HASH_PATTERN, manufacturing_fields

# Dimension is irrelevant to scalar fields; derive provenance from the Stage 3 contract.
PARENT_FIELDS = tuple(f.name for f in manufacturing_fields(1)
                      if f.name not in {"id", "child_id", "child_content_sha256", "text",
                                        "dense_vector", "sparse_vector"})
CHILD_FIELDS = {"id", "child_id", "child_content_sha256", "retrieval_score"}
SIGNAL_FIELDS = {"best_retrieval_score", "rerank_score", "child_hit_count", "matched_child_ids",
                 "first_child_rank", "matched_children"}


class ParentAggregationError(ValueError):
    """Invalid or conflicting child evidence; messages never include document text."""


@dataclass(frozen=True)
class ChildMatch:
    child_id: str
    child_content_sha256: str
    retrieval_score: float
    child_rank: int


@dataclass(frozen=True)
class ParentEvidence:
    page_content: str
    metadata: Mapping
    matched_children: tuple[ChildMatch, ...]
    best_retrieval_score: float
    first_child_rank: int

    @property
    def parent_id(self):
        return self.metadata["parent_id"]

    @property
    def child_hit_count(self):
        return len(self.matched_children)

    @property
    def matched_child_ids(self):
        return tuple(m.child_id for m in self.matched_children)


def finite_score(value, error_type, field):
    if isinstance(value, bool) or not isinstance(value, Real) or not isfinite(value):
        raise error_type(field + ": finite numeric score required")
    return value


def parent_order(parent):
    return (-parent.best_retrieval_score, parent.first_child_rank, parent.parent_id)


def aggregate_parents(children):
    groups, seen = {}, set()
    for rank, child in enumerate(children, start=1):
        metadata = getattr(child, "metadata", None)
        if not isinstance(metadata, Mapping):
            raise ParentAggregationError("child metadata mapping required")
        missing = set(PARENT_FIELDS) | CHILD_FIELDS
        if missing - metadata.keys():
            raise ParentAggregationError("missing fields: " + ",".join(sorted(missing - metadata.keys())))
        if SIGNAL_FIELDS & metadata.keys():
            raise ParentAggregationError("parent signals cannot be supplied as child metadata")
        for name in ("id", "child_id", "parent_id", "child_content_sha256"):
            if not isinstance(metadata[name], str) or not HASH_PATTERN.fullmatch(metadata[name]):
                raise ParentAggregationError(name + ": stable SHA256 required")
        child_id, parent_id = metadata["child_id"], metadata["parent_id"]
        if metadata["id"] != child_id:
            raise ParentAggregationError("id must equal child_id")
        if child_id in seen:
            raise ParentAggregationError("duplicate child_id in retrieval results")
        seen.add(child_id)
        content = metadata["parent_content"]
        if not isinstance(content, str) or not content.strip():
            raise ParentAggregationError("parent_content must be nonempty text")
        score = finite_score(metadata["retrieval_score"], ParentAggregationError, "retrieval_score")
        # Preserve all non-child metadata, including any future provenance.
        parent_metadata = deepcopy({name: value for name, value in metadata.items() if name not in CHILD_FIELDS})
        match = ChildMatch(child_id, metadata["child_content_sha256"], score, rank)
        if parent_id in groups:
            previous, matches = groups[parent_id]
            if previous != parent_metadata:
                conflicts = sorted(name for name in previous.keys() | parent_metadata.keys()
                                   if name not in previous or name not in parent_metadata
                                   or previous[name] != parent_metadata[name])
                raise ParentAggregationError("conflicting parent metadata: " + ",".join(conflicts))
            matches.append(match)
        else:
            groups[parent_id] = (parent_metadata, [match])
    parents = [ParentEvidence(metadata["parent_content"], MappingProxyType(metadata), tuple(matches),
                              max(m.retrieval_score for m in matches), matches[0].child_rank)
               for metadata, matches in groups.values()]
    return tuple(sorted(parents, key=parent_order))
