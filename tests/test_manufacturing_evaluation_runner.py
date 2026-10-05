"""Recording adapters test evaluator correctness, not real retrieval quality."""
from copy import deepcopy
from dataclasses import replace
import json
import os
from types import SimpleNamespace
import pytest
from rag_qa.evaluation.benchmark import controlled_benchmark
from rag_qa.evaluation.schemas import EvaluationDataset, EvaluationProfile
from rag_qa.evaluation.evaluator import RetrievalObservation, evaluate_retrieval, compare_direct_strategy
from rag_qa.evaluation.adapters import ComponentEvaluationAdapter
from rag_qa.evaluation.runner import main, checked_collection, validate_live_labels, provision_new_benchmark, ControlledPlanner
from rag_qa.evaluation.ragas_runner import AnswerEvaluationSample, run_ragas
from rag_qa.query import QueryAnalyzer
from rag_qa.retrieval.settings import RetrievalSettings
from rag_qa.retrieval.fast_path import FastPathResult, MatchType
from test_manufacturing_milvus_schema import vector_store_unit

METADATA = dict(execution_mode="unit_test", knowledge_revision="synthetic_test_revision", git_sha="d" * 40,
                collection="recording_only", schema_version="manufacturing_v1", planner_type="controlled_strategy_test")


def fixture_dataset():
    dataset, children, _ = controlled_benchmark()
    samples = dataset.samples[:2]
    return EvaluationDataset(**{**dataset.model_dump(exclude={"samples"}), "samples": samples}), children


def parent(sample, **updates):
    return SimpleNamespace(page_content="SYNTHETIC", metadata=dict(parent_id=sample.expected_parent_ids[0],
        document_id=sample.expected_document_ids[0], equipment_model=sample.expected_equipment_model,
        alarm_code=sample.expected_alarm_code, part_number=sample.expected_part_number, **updates))


def recording(observations):
    results = iter(observations)
    def retrieve(query):
        result = next(results)
        if isinstance(result, Exception): raise result
        return result
    return SimpleNamespace(retrieve=retrieve)


def test_per_sample_layer_metrics_slicing_error_denominator_and_safe_errors():
    dataset, children = fixture_dataset(); first, second = dataset.samples
    selected = tuple(c for c in children if c.metadata["child_id"] in first.expected_child_ids)
    obs = RetrievalObservation(selected, (parent(first),), analysis=QueryAnalyzer().analyze(first.query))
    report = evaluate_retrieval(dataset, recording([obs, RuntimeError("secret password")]), metadata=METADATA)
    assert report["aggregate_metrics"]["parent"]["hit"] == .5
    assert report["aggregate_metrics"]["error_count"] == 1
    assert len(report["per_sample_results"]) == 2
    row = next(r for r in report["per_sample_results"] if r["error"])
    assert row["error"] == "RuntimeError" and "secret" not in json.dumps(report)
    assert report["metrics_by_intent"] and report["metrics_by_tag"]["SYNTHETIC"]["sample_count"] == 2
    assert report["latency_scope"] == "unit_test_timing_not_retrieval_performance"
    assert not report["metadata"]["production_quality_claim"]


@pytest.mark.parametrize("field", ["equipment_model", "alarm_code", "part_number"])
def test_measured_hard_leak_including_missing_metadata(field):
    dataset, _ = fixture_dataset()
    sample = dataset.samples[0].model_copy(update={"expected_" + field: "EXPECTED-001"})
    dataset = dataset.model_copy(update={"samples": (sample,)})
    doc = parent(sample); doc.metadata[field] = None
    report = evaluate_retrieval(dataset, recording([RetrievalObservation(parents=(doc,))]), metadata=METADATA)
    assert report["aggregate_metrics"]["hard_identifier_leak_count"] == 1
    assert report["aggregate_metrics"]["hard_identifier_leak_rate"] == 1
    assert report["per_sample_results"][0]["hard_identifier_leaks"][0]["fields"] == [field]


def test_child_leak_not_hidden_by_clean_parent():
    dataset, children = fixture_dataset(); sample = dataset.samples[0]
    dataset = dataset.model_copy(update={"samples": (sample,)})
    child = deepcopy(children[0]); child.metadata["equipment_model"] = "WRONG-100"
    report = evaluate_retrieval(dataset, recording([RetrievalObservation(children=(child,), parents=(parent(sample),))]), metadata=METADATA)
    assert report["aggregate_metrics"]["hard_identifier_leak_count"] == 1


def test_fast_path_precision_coverage_correct_incorrect_and_child_not_applicable():
    dataset, _ = fixture_dataset(); a, b = dataset.samples
    a = a.model_copy(update={"fast_path_labels": ("exact_alarm",)})
    b = b.model_copy(update={"fast_path_labels": ("exact_alarm",)})
    dataset = dataset.model_copy(update={"samples": (a, b)})
    def fast(): return FastPathResult("ACCEPTED", MatchType.EXACT_ALARM, (), None, None, None, 2, "synthetic_test")
    incorrect = parent(b); incorrect.metadata["parent_id"] = "e" * 64
    report = evaluate_retrieval(dataset, recording([RetrievalObservation(parents=(parent(a),), fast_path=fast()),
        RetrievalObservation(parents=(incorrect,), fast_path=fast())]), metadata=METADATA)
    metric = report["fast_path_metrics"]["exact_alarm"]
    assert metric["precision"] == .5 and metric["coverage"] == 1 and metric["incorrect_accepted_samples"] == 1
    assert report["aggregate_metrics"]["child"]["sample_count"] == 0
    assert report["aggregate_metrics"]["child"]["hit"] is None
    assert all(r["metrics"]["child"] is None for r in report["per_sample_results"])


def test_paired_direct_strategy_and_provenance_rejection():
    dataset, _ = fixture_dataset(); a, b = dataset.samples
    direct = evaluate_retrieval(dataset, recording([RetrievalObservation(), RetrievalObservation()]), metadata=METADATA)
    strategy = evaluate_retrieval(dataset, recording([RetrievalObservation(parents=(parent(a),), strategy="rewrite"),
        RetrievalObservation(parents=(parent(b),), strategy="subquery")]), metadata=METADATA)
    paired = compare_direct_strategy(direct, strategy)
    assert paired["delta_strategy_vs_direct"]["hit"] == 1 and paired["zero_result_rate_delta"] == -1
    assert paired["scope"] == "controlled_strategy_test" and len(paired["per_sample"]) == 2
    changed = deepcopy(strategy); changed["metadata"]["knowledge_revision"] = "other"
    with pytest.raises(ValueError): compare_direct_strategy(direct, changed)
    changed = deepcopy(strategy); changed["retrieval_config_fingerprint"] = "other"
    with pytest.raises(ValueError): compare_direct_strategy(direct, changed)


def test_real_stage5_to9_methods_recorded_once_and_raw_bm25(vector_store_unit):
    dataset, children, corpus = controlled_benchmark()
    sample = next(s for s in dataset.samples if "-maintenance-paraphrase" in s.sample_id)
    profile = EvaluationProfile()
    calls, rerank_calls = [], []
    chosen = []
    from rag_qa.core.milvus_schema import manufacturing_fields
    fields = [f.name for f in manufacturing_fields(1) if f.datatype not in {"FLOAT_VECTOR", "SPARSE_FLOAT_VECTOR"}]
    for child in children:
        if child.metadata["child_id"] in sample.expected_child_ids:
            metadata = {name: child.metadata.get(name) for name in fields if name != "text"}
            metadata.update(schema_version="manufacturing_v1", retrieval_score=.8)
            chosen.append(SimpleNamespace(page_content=child.page_content, metadata=metadata))
    vector = SimpleNamespace(schema_mode="manufacturing", retrieval_settings=profile.retrieval_settings(),
        hybrid_search_children=lambda query, **kwargs: calls.append((query, kwargs)) or chosen,
        reranker=SimpleNamespace(predict=lambda pairs: rerank_calls.append(pairs) or [.5] * len(pairs)))
    adapter = ComponentEvaluationAdapter(vector, QueryAnalyzer(), profile, mode="strategy", corpus=corpus)
    report = evaluate_retrieval(dataset.model_copy(update={"samples": (sample,)}), adapter, profile=profile, metadata=METADATA)
    assert report["aggregate_metrics"]["error_count"] == 0
    row = report["per_sample_results"][0]
    assert len(calls) == len(rerank_calls) == 1
    assert row["filter_attempts"][0]["hard_filters"]["equipment_model"] == sample.expected_equipment_model
    assert row["fast_path"]["status"] == "FALLBACK" and row["fast_path"]["candidates"]
    assert row["fast_path"]["candidates"][0]["raw_score"] is not None
    assert row["metrics"]["child"]["hit"] == row["metrics"]["parent"]["hit"] == 1


def test_strategy_M_experiment_rejected_without_global_config_change():
    from base.config import config
    before = config.CANDIDATE_M
    profile = EvaluationProfile(candidate_m=before + 1)
    vector = SimpleNamespace(schema_mode="manufacturing", retrieval_settings=profile.retrieval_settings())
    with pytest.raises(ValueError): ComponentEvaluationAdapter(vector, QueryAnalyzer(), profile, mode="strategy")
    assert config.CANDIDATE_M == before


def test_scripted_planner_runs_actual_stage9_subquery_and_single_rerank(vector_store_unit):
    from rag_qa.core.milvus_schema import manufacturing_fields
    dataset, children, _ = controlled_benchmark()
    sample = next(s for s in dataset.samples if s.sample_id == "multi-relevant")
    profile = EvaluationProfile()
    fields = [f.name for f in manufacturing_fields(1) if f.datatype not in {"FLOAT_VECTOR", "SPARSE_FLOAT_VECTOR"}]
    chosen = []
    for c in children:
        if c.metadata["child_id"] in sample.expected_child_ids:
            metadata = {name: c.metadata.get(name) for name in fields if name != "text"}
            metadata.update(schema_version="manufacturing_v1", retrieval_score=.8)
            chosen.append(SimpleNamespace(page_content=c.page_content, metadata=metadata))
    searches, reranks = [], []
    vector = SimpleNamespace(schema_mode="manufacturing", retrieval_settings=profile.retrieval_settings(),
        hybrid_search_children=lambda query, **kwargs: searches.append(query) or chosen,
        reranker=SimpleNamespace(predict=lambda pairs: reranks.append(pairs) or [.5] * len(pairs)))
    adapter = ComponentEvaluationAdapter(vector, QueryAnalyzer(), profile, mode="strategy", planner=ControlledPlanner())
    observation = adapter.retrieve(sample.query)
    assert observation.strategy == "subquery" and observation.decision_source == "planner" and observation.fallback_reason is None
    assert len(searches) == 3 and len(reranks) == 1 and len(observation.children) == 4
    assert observation.timings["rerank"] >= 0


@pytest.mark.parametrize("reason", ["hard_identifier_not_preserved", "new_identifier_token", "duplicate_query_variant", "planner_timeout"])
def test_planner_rejection_observability_uses_actual_reason_codes(reason):
    dataset, _ = fixture_dataset(); dataset = dataset.model_copy(update={"samples": (dataset.samples[0],)})
    report = evaluate_retrieval(dataset, recording([RetrievalObservation(decision_source="fallback", fallback_reason=reason)]), metadata=METADATA)
    assert report["aggregate_metrics"]["planner_fallback_count"] == 1
    assert report["aggregate_metrics"]["variant_rejection_count"] == int(reason != "planner_timeout")


def test_real_mode_requires_provenance_and_invalid_returned_hash_is_error():
    dataset, _ = fixture_dataset()
    with pytest.raises(ValueError): evaluate_retrieval(dataset, recording([]), metadata=dict(execution_mode="real_components"))
    sample = dataset.samples[0]; doc = parent(sample); doc.metadata["parent_id"] = "not-a-stable-id"
    report = evaluate_retrieval(dataset.model_copy(update={"samples": (sample,)}), recording([RetrievalObservation(parents=(doc,))]), metadata=METADATA)
    assert report["aggregate_metrics"]["error_count"] == 1 and report["aggregate_metrics"]["parent"]["hit"] == 0


@pytest.mark.parametrize("name", ["manufacturing_rag_v1", "edu_rag", "manufacturing_rag_eval_", "manufacturing_rag_eval_v1;drop", ""])
def test_eval_collection_safety(name):
    with pytest.raises(ValueError): checked_collection(name)


def test_offline_cli_artifact_null_quality_and_no_live_optin(monkeypatch, tmp_path):
    from rag_qa.evaluation import runner
    monkeypatch.delenv("STAGE12_LIVE", raising=False)
    output = tmp_path / "result.json"
    assert main(["--output", str(output)]) == 0
    report = json.loads(output.read_text(encoding="utf-8"))
    assert report["status"] == "NOT RUN" and report["aggregate_metrics"] is None
    assert report["metadata"]["sample_count"] == 25 and all(r["metrics"] is None for r in report["per_sample_results"])
    assert main(["--live", "--output", str(output), "--manifest", str(tmp_path / "eval.sqlite")]) == 1
    assert json.loads(output.read_text(encoding="utf-8"))["status"] == "PARTIAL"
    assert not (tmp_path / "eval.sqlite").exists()


def test_provision_and_manifest_isolation(tmp_path):
    dataset, children, _ = controlled_benchmark()
    stored = {}
    vector = SimpleNamespace(collection_name="manufacturing_rag_eval_test", schema_mode="manufacturing")
    def add(docs):
        stored[docs[0].metadata["document_id"]] = tuple(d.metadata["child_id"] for d in docs)
    vector.add_documents = add
    vector.verify_document_snapshot = lambda docid, ids: set(stored[docid]) == set(ids)
    vector.list_document_child_ids = lambda docid: list(stored[docid])
    def query(**kwargs):
        ids = set(json.loads(kwargs["filter"].removeprefix("child_id in ")))
        return [dict(parent_id=c.metadata["parent_id"]) for c in children if c.metadata["child_id"] in ids]
    vector.client = SimpleNamespace(query=query)
    manifest = tmp_path / "eval.sqlite"
    provision_new_benchmark(vector, manifest, children)
    validate_live_labels(dataset, vector, manifest)
    with pytest.raises(ValueError): provision_new_benchmark(vector, manifest, children)
    stored[children[0].metadata["document_id"]] = ()
    with pytest.raises(ValueError): validate_live_labels(dataset, vector, manifest)


def test_provision_helper_rejects_production_before_writes(tmp_path):
    from base.config import config
    _, children, _ = controlled_benchmark()
    vector = SimpleNamespace(collection_name=config.MILVUS_MANUFACTURING_COLLECTION_NAME,
        add_documents=lambda docs: pytest.fail("must not write production"))
    with pytest.raises(ValueError): provision_new_benchmark(vector, tmp_path / "eval.sqlite", children)
    assert not (tmp_path / "eval.sqlite").exists()
    vector.collection_name = "manufacturing_rag_eval_safe"
    with pytest.raises(ValueError): provision_new_benchmark(vector, config.MANUFACTURING_MANIFEST_DB_PATH, children)


def test_ragas_optin_and_four_required_fields_no_fake_scores():
    assert run_ragas([])["status"] == "NOT RUN"
    assert run_ragas([], enabled=True)["reason"] == "explicit_judges_required"
    kwargs = dict(enabled=True, judge_llm=object(), judge_embeddings=object(), judge_model="synthetic", embedding_model="synthetic",
                  dataset_sha256="a" * 64, git_sha="b" * 40)
    assert run_ragas([], **kwargs)["reason"] == "no_eligible_samples"
    assert run_ragas([dict(sample_id="x", query="q", generated_answer="a", reference_answer="r")], **kwargs)["status"] == "NOT RUN"
    sample = AnswerEvaluationSample(sample_id="x", query="q", retrieved_contexts=("ctx",), generated_answer="a", reference_answer="r")
    result = run_ragas([sample], **kwargs)
    assert result["status"] == "NOT RUN" and result["metrics"] is None


@pytest.mark.parametrize("nonfinite", [False, True])
def test_ragas_026_recording_boundary_and_nan_rejected(monkeypatch, nonfinite):
    import sys
    from rag_qa.evaluation import ragas_runner
    calls = []
    monkeypatch.setattr(ragas_runner.importlib.metadata, "version", lambda name: "0.2.6")
    names = ("faithfulness", "answer_relevancy", "context_precision", "context_recall")
    classes = {name: (lambda value=value: SimpleNamespace(name=value)) for name, value in zip(
        ("Faithfulness", "ResponseRelevancy", "LLMContextPrecisionWithReference", "LLMContextRecall"), names)}
    def evaluate(data, **kwargs):
        calls.append((data, kwargs))
        return SimpleNamespace(scores=[dict.fromkeys(names, float("nan") if nonfinite else .5)])
    monkeypatch.setitem(sys.modules, "ragas", SimpleNamespace(evaluate=evaluate,
        EvaluationDataset=SimpleNamespace(from_list=lambda rows: rows)))
    monkeypatch.setitem(sys.modules, "ragas.metrics", SimpleNamespace(**classes))
    monkeypatch.setitem(sys.modules, "ragas.run_config", SimpleNamespace(RunConfig=lambda **kwargs: kwargs))
    sample = AnswerEvaluationSample(sample_id="x", query="q", retrieved_contexts=("ctx",), generated_answer="a", reference_answer="r")
    result = run_ragas([sample], enabled=True, judge_llm=object(), judge_embeddings=object(), judge_model="recording_fake_judge",
                      embedding_model="recording_fake_embedding", dataset_sha256="a" * 64, git_sha="b" * 40)
    assert calls[0][0] == [dict(user_input="q", retrieved_contexts=["ctx"], response="a", reference="r")]
    assert calls[0][1]["run_config"]["timeout"] == 60 and calls[0][1]["raise_exceptions"]
    assert result["status"] == ("NOT RUN" if nonfinite else "PASS")
    assert result["metrics"] is None if nonfinite else result["metrics"]["faithfulness"] == .5


@pytest.mark.skipif(os.getenv("STAGE12_LIVE") != "1", reason="STAGE12_LIVE not enabled; real BGE/Milvus/CrossEncoder NOT RUN")
def test_optional_real_live(tmp_path):
    collection, manifest = os.getenv("STAGE12_EVAL_COLLECTION"), os.getenv("STAGE12_EVAL_MANIFEST")
    if not collection or not manifest: pytest.skip("explicit prepared evaluation collection/manifest not configured")
    assert main(["--live", "--collection", collection, "--manifest", manifest, "--output", str(tmp_path / "real.json")]) == 0
