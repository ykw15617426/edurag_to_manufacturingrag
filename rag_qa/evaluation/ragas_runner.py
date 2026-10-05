"""Optional explicit 0.2.6 judges. No import-time RAGAS, judges or API calls."""
import importlib.metadata
import math
import hashlib
import json
from pydantic import BaseModel, ConfigDict, Field, StrictStr, TypeAdapter, field_validator
from .schemas import Hash


class AnswerEvaluationSample(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    sample_id: StrictStr = Field(min_length=1, max_length=128)
    query: StrictStr = Field(min_length=1, max_length=16384)
    retrieved_contexts: tuple[StrictStr, ...] = Field(min_length=1, max_length=4096)
    generated_answer: StrictStr = Field(min_length=1, max_length=65535)
    reference_answer: StrictStr = Field(min_length=1, max_length=65535)

    @field_validator("*")
    @classmethod
    def nonblank(cls, value):
        for text in value if isinstance(value, tuple) else [value]:
            if not text.strip() or len(text.encode("utf-8")) > 65535: raise ValueError("nonempty bounded UTF-8 required")
        return value


def run_ragas(samples, *, enabled=False, judge_llm=None, judge_embeddings=None,
              judge_model=None, embedding_model=None, dataset_sha256=None, git_sha=None):
    provenance = dict(ragas_version="0.2.6", judge_model=judge_model, embedding_model=embedding_model,
                      dataset_sha256=dataset_sha256, git_sha=git_sha, input_sample_count=len(samples), sample_count=0)
    def not_run(reason): return dict(status="NOT RUN", reason=reason, metadata=provenance, metrics=None)
    if not enabled: return not_run("explicit_judge_execution_disabled")
    if judge_llm is None or judge_embeddings is None or not judge_model or not embedding_model:
        return not_run("explicit_judges_required")
    try:
        checked = [s if isinstance(s, AnswerEvaluationSample) else AnswerEvaluationSample.model_validate(s) for s in samples]
        if not checked: return not_run("no_eligible_samples")
        if len({s.sample_id for s in checked}) != len(checked): return not_run("duplicate_sample_id")
        # Invalid/incomplete samples never enter RAGAS; callers supply an explicit eligible subset.
        TypeAdapter(Hash).validate_python(dataset_sha256)
        if not isinstance(git_sha, str) or len(git_sha) != 40 or any(c not in "0123456789abcdef" for c in git_sha):
            return not_run("invalid_git_sha")
        provenance["sample_count"] = len(checked)
        provenance["judge_input_sha256"] = hashlib.sha256(json.dumps([s.model_dump(mode="json") for s in checked],
            sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")).hexdigest()
        if importlib.metadata.version("ragas") != "0.2.6": return not_run("pinned_version_required")
        from ragas import evaluate, EvaluationDataset
        from ragas.metrics import Faithfulness, ResponseRelevancy, LLMContextPrecisionWithReference, LLMContextRecall
        from ragas.run_config import RunConfig
        data = EvaluationDataset.from_list([dict(user_input=s.query, retrieved_contexts=list(s.retrieved_contexts),
                response=s.generated_answer, reference=s.reference_answer) for s in checked])
        metrics = [Faithfulness(), ResponseRelevancy(), LLMContextPrecisionWithReference(), LLMContextRecall()]
        result = evaluate(data, metrics=metrics, llm=judge_llm, embeddings=judge_embeddings,
                          run_config=RunConfig(timeout=60, max_retries=1, max_workers=2),
                          raise_exceptions=True, show_progress=False)
        scores = [{name: float(score) for name, score in row.items()} for row in result.scores]
        expected = {m.name for m in metrics}
        if len(scores) != len(checked) or any(set(row) != expected or any(not math.isfinite(v) for v in row.values()) for row in scores):
            return not_run("invalid_judge_scores")
        return dict(status="PASS", metadata=provenance, per_sample_scores=[dict(sample_id=s.sample_id, **row) for s, row in zip(checked, scores)],
                    metrics={name: sum(row[name] for row in scores) / len(scores) for name in expected},
                    scope="LLM_based_auxiliary_quality_not_absolute_ground_truth")
    except Exception as exc:
        return not_run(type(exc).__name__)
