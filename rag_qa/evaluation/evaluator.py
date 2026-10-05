"""Observable evaluation over injected adapters; fake runs are unit validation only."""
from dataclasses import dataclass, field
from time import perf_counter
import re
from types import SimpleNamespace
import math
from .metrics import ranking_metrics, macro_metrics, stable_unique
from .schemas import EvaluationDataset, EvaluationProfile


@dataclass(frozen=True)
class RetrievalObservation:
    children: tuple = ()
    parents: tuple = ()
    strategy: str = "direct"
    decision_source: str = "default"
    fallback_reason: str | None = None
    filter_attempts: tuple = ()
    fast_path: object | None = None
    analysis: object | None = None
    timings: dict = field(default_factory=dict)


def hard_leaks(sample, documents):
    expected = {name: getattr(sample, "expected_" + name) for name in ("equipment_model", "alarm_code", "part_number")
                if getattr(sample, "expected_" + name) is not None}
    return [dict(item_index=i, fields=[name for name, value in expected.items() if doc.metadata.get(name) != value])
            for i, doc in enumerate(documents, 1) if any(doc.metadata.get(name) != value for name, value in expected.items())]


def _fast_details(sample, fast):
    if fast is None: return None
    candidates = []
    for candidate in fast.candidates:
        entry = candidate.entry
        candidates.append(dict(parent_id=entry.parent_id, document_id=entry.document_id,
            raw_score=candidate.raw_score, rank=candidate.rank, candidate_scope_size=candidate.candidate_scope_size,
            corpus_size=candidate.corpus_size, matched_token_count=candidate.matched_token_count,
            correct=(entry.parent_id in sample.expected_parent_ids and entry.document_id in sample.expected_document_ids
                     and not hard_leaks(sample, [SimpleNamespace(metadata=entry.model_dump(mode="json"))]))))
    return dict(status=fast.status, match_type=fast.match_type.value, reason=fast.reason,
                candidates=candidates, corpus_size=fast.corpus_size)


def _aggregate(rows, profile):
    layers = {layer: dict(cutoff=profile.retrieval_k if layer == "child" else profile.candidate_m,
                **macro_metrics(r["metrics"][layer] for r in rows if r["metrics"][layer] is not None))
              for layer in ("child", "parent", "document")}
    successful = [r for r in rows if r["error"] is None]
    hard_rows = [r for r in successful if r["has_hard_identifier"]]
    leak_count = sum(bool(r["hard_identifier_leaks"]) for r in hard_rows)
    layers.update(sample_count=len(rows), error_count=len(rows) - len(successful),
        zero_result_count=sum(not r["returned_parent_ids"] for r in rows),
        zero_result_rate=sum(not r["returned_parent_ids"] for r in rows) / len(rows) if rows else None,
        hard_identifier_sample_count=len(hard_rows), hard_identifier_leak_count=leak_count,
        hard_identifier_leak_rate=leak_count / len(hard_rows) if hard_rows else None,
        hard_identifier_leaked_item_count=sum(len(r["hard_identifier_leaks"]) for r in hard_rows),
        identifier_analysis_mismatch_count=sum(bool(r["analysis_identifier_mismatches"]) for r in successful),
        intent_mismatch_count=sum(r["intent_match"] is False for r in successful),
        strategy_counts={s: sum(r["strategy"] == s for r in successful) for s in ("direct", "rewrite", "subquery")},
        planner_fallback_count=sum(r["decision_source"] == "fallback" for r in successful),
        variant_rejection_count=sum(r["fallback_reason"] in {"hard_identifier_not_preserved", "new_identifier_token", "duplicate_query_variant", "invalid_query"}
                                    for r in successful),
        fast_path_accepted_count=sum(r["fast_path"] is not None and r["fast_path"]["status"] == "ACCEPTED" for r in successful),
        fast_path_fallback_count=sum(r["fast_path"] is not None and r["fast_path"]["status"] == "FALLBACK" for r in successful))
    return layers


def _fast_metrics(rows):
    result = {}
    for channel in ("exact_alarm", "exact_faq", "bm25_faq"):
        eligible = [r for r in rows if channel in r["fast_path_labels"]]
        accepted = [r for r in rows if r["fast_path"] and r["fast_path"]["status"] == "ACCEPTED"
                    and r["fast_path"]["match_type"] == channel]
        correct = sum(bool(set(r["returned_parent_ids"]) & set(r["expected_parent_ids"]))
                      and bool(set(r["returned_document_ids"]) & set(r["expected_document_ids"]))
                      and not r["hard_identifier_leaks"] for r in accepted)
        eligible_accepted = sum(channel in r["fast_path_labels"] for r in accepted)
        result[channel] = dict(eligible_samples=len(eligible), accepted_samples=len(accepted),
            correct_accepted_samples=correct, incorrect_accepted_samples=len(accepted) - correct,
            accepted_without_eligibility_label=len(accepted) - eligible_accepted,
            fallback_samples=len(eligible) - eligible_accepted,
            coverage=eligible_accepted / len(eligible) if eligible else None,
            precision=correct / len(accepted) if accepted else None,
            fallback_rate=1 - eligible_accepted / len(eligible) if eligible else None)
    return result


def evaluate_retrieval(dataset, retriever, *, profile=None, metadata):
    if not isinstance(dataset, EvaluationDataset): raise TypeError("validated dataset required")
    profile = profile or EvaluationProfile()
    if not isinstance(profile, EvaluationProfile): raise TypeError("validated profile required")
    if metadata.get("execution_mode") not in {"unit_test", "real_components"}:
        raise ValueError("explicit execution_mode required")
    if metadata["execution_mode"] == "real_components":
        if (metadata.get("components") != {"BGE-M3": "REAL", "Milvus": "REAL", "CrossEncoder": "REAL"}
                or not re.fullmatch(r"[0-9a-f]{64}", metadata.get("knowledge_revision", ""))
                or not metadata.get("collection") or not metadata.get("schema_version")):
            raise ValueError("real evaluation requires component and active snapshot provenance")
    rows = []
    for sample in sorted(dataset.samples, key=lambda s: s.sample_id):
        row = dict(sample.model_dump(mode="json"), returned_child_ids=[], returned_parent_ids=[], returned_document_ids=[],
            strategy=None, decision_source=None, fallback_reason=None, fast_path=None, filter_attempts=[],
            hard_identifier_leaks=[], analysis_identifier_mismatches=[], intent_match=None,
            has_hard_identifier=any(getattr(sample, "expected_" + n) is not None for n in ("equipment_model", "alarm_code", "part_number")),
            analysis=None, error=None, timings_ms={}, child_metric_scope="retrieved_children")
        start = perf_counter()
        try:
            observation = retriever.retrieve(sample.query)
            if not isinstance(observation, RetrievalObservation): raise TypeError("observation required")
            children, parents = tuple(observation.children), tuple(observation.parents)
            row.update(returned_child_ids=stable_unique([c.metadata["child_id"] for c in children]),
                       returned_parent_ids=stable_unique([p.metadata["parent_id"] for p in parents]),
                       returned_document_ids=stable_unique([p.metadata["document_id"] for p in parents]),
                       strategy=observation.strategy, decision_source=observation.decision_source,
                       fallback_reason=observation.fallback_reason, filter_attempts=list(observation.filter_attempts),
                       fast_path=_fast_details(sample, observation.fast_path), timings_ms=dict(observation.timings))
            if (observation.strategy not in {"direct", "rewrite", "subquery"}
                    or any(not re.fullmatch(r"[0-9a-f]{64}", value) for value in row["returned_child_ids"] + row["returned_parent_ids"])):
                raise ValueError("invalid observed stable identity or strategy")
            if any(isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0
                   for value in observation.timings.values()): raise ValueError("invalid observed latency")
            # Inspect every returned child, including children removed by aggregation/rerank.
            row["hard_identifier_leaks"] = hard_leaks(sample, children + parents)
            if observation.analysis is not None:
                row["analysis"] = observation.analysis.to_metadata()
                row["intent_match"] = (observation.analysis.intent == sample.expected_intent) if sample.expected_intent else None
                row["analysis_identifier_mismatches"] = [name for name in ("equipment_model", "alarm_code", "part_number")
                    if getattr(sample, "expected_" + name) is not None
                    and getattr(observation.analysis.entities, name) != getattr(sample, "expected_" + name)]
            if observation.fast_path is not None and observation.fast_path.status == "ACCEPTED":
                if children: raise ValueError("fast path must not fabricate children")
                row["child_metric_scope"] = "not_applicable_fast_path"
        except Exception as exc:
            # Keep the failed sample in denominators, without dependency message/credentials.
            row.update(error=type(exc).__name__, returned_child_ids=[], returned_parent_ids=[], returned_document_ids=[],
                       child_metric_scope="failed_sample", fast_path=None)
        row["timings_ms"]["total_retrieval"] = (perf_counter() - start) * 1000
        row["metrics"] = {layer: (None if layer == "child" and row["child_metric_scope"] == "not_applicable_fast_path"
            else ranking_metrics(getattr(sample, "expected_" + layer + "_ids"), row["returned_" + layer + "_ids"],
                                 profile.retrieval_k if layer == "child" else profile.candidate_m))
                          for layer in ("child", "parent", "document")}
        rows.append(row)
    report_metadata = dict(metadata, dataset_type=dataset.dataset_type, provenance_note=dataset.provenance_note,
                          sample_count=len(rows), dataset_sha256=dataset.sha256(),
                          production_quality_claim=False, production_tuning="NOT AUTHORIZED BY DATA",
                          quality_scope="metric_unit_validation" if metadata["execution_mode"] == "unit_test" else dataset.dataset_type)
    def sliced(key, labels): return {label: _aggregate([r for r in rows if key(r, label)], profile) for label in labels}
    latency = {}
    for name in sorted({key for row in rows for key in row["timings_ms"]}):
        values = sorted(row["timings_ms"][name] for row in rows if row["error"] is None and name in row["timings_ms"])
        latency[name] = dict(sample_count=len(values), mean_ms=sum(values) / len(values) if values else None,
                             p95_ms=values[math.ceil(.95 * len(values)) - 1] if values else None)
    return dict(metadata=report_metadata, config_snapshot=profile.model_dump(mode="json"),
                retrieval_config_fingerprint=profile.fingerprint(), aggregate_metrics=_aggregate(rows, profile),
                metrics_by_intent=sliced(lambda r, label: (r["expected_intent"] or "unlabeled") == label,
                                          sorted({r["expected_intent"] or "unlabeled" for r in rows})),
                metrics_by_tag=sliced(lambda r, label: label in r["tags"], sorted({t for r in rows for t in r["tags"]})),
                metrics_by_identifier=sliced(lambda r, label: r["has_hard_identifier"] == (label == "hard"), ["hard", "no_hard"]),
                metrics_by_alarm=sliced(lambda r, label: bool(r["expected_alarm_code"]) == (label == "alarm"), ["alarm", "non_alarm"]),
                fast_path_metrics=_fast_metrics(rows), per_sample_results=rows,
                latency_metrics=latency,
                ragas=dict(status="NOT RUN", reason="requires_answer_context_reference_and_explicit_judge"),
                latency_scope="unit_test_timing_not_retrieval_performance" if metadata["execution_mode"] == "unit_test" else "local_real_components")


def compare_direct_strategy(direct, strategy):
    for field in ("dataset_sha256", "knowledge_revision", "execution_mode"):
        if direct["metadata"].get(field) != strategy["metadata"].get(field): raise ValueError("paired provenance mismatch")
    if direct["retrieval_config_fingerprint"] != strategy["retrieval_config_fingerprint"]:
        raise ValueError("paired config mismatch")
    left, right = direct["per_sample_results"], strategy["per_sample_results"]
    if [r["sample_id"] for r in left] != [r["sample_id"] for r in right]: raise ValueError("paired sample mismatch")
    if any(r["strategy"] not in {"direct", None} or r["fast_path"] is not None for r in left):
        raise ValueError("DIRECT baseline must bypass planner and fast path")
    def delta(a, b): return b - a if a is not None and b is not None else None
    return dict(scope=strategy["metadata"].get("planner_type", "unrecorded"),
        delta_strategy_vs_direct={name: delta(direct["aggregate_metrics"]["parent"][name], strategy["aggregate_metrics"]["parent"][name])
                                  for name in ("hit", "recall", "mrr")},
        zero_result_rate_delta=delta(direct["aggregate_metrics"]["zero_result_rate"], strategy["aggregate_metrics"]["zero_result_rate"]),
        per_sample=[dict(sample_id=a["sample_id"], parent_hit_delta=b["metrics"]["parent"]["hit"] - a["metrics"]["parent"]["hit"],
                         parent_mrr_delta=b["metrics"]["parent"]["mrr"] - a["metrics"]["parent"]["mrr"]) for a, b in zip(left, right)])
