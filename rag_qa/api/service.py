"""One async orchestration; synchronous dependencies always run off-loop."""
import asyncio
from dataclasses import dataclass
from rag_qa.generation.schemas import GroundedAnswerResult, GenerationError
from .cache import build_cache_key, validate_cached_answer
from .schemas import ServiceError, RequestDisconnected


@dataclass(frozen=True)
class OnlineOutcome:
    answer: GroundedAnswerResult
    cache_hit: bool


async def check_connected(disconnected):
    if await disconnected():
        raise RequestDisconnected()


class ManufacturingOnlineService:
    def __init__(self, analyzer, retriever, generator, revision_provider, *, cache=None,
                 llm_model, retrieval_k, candidate_m, retrieval_settings=None):
        self.analyzer, self.retriever, self.generator = analyzer, retriever, generator
        self.revision_provider, self.cache = revision_provider, cache
        self.key_options = dict(llm_model=llm_model, retrieval_k=retrieval_k, candidate_m=candidate_m,
                                retrieval_settings=retrieval_settings)

    async def events(self, query, disconnected):
        await check_connected(disconnected)
        try:
            analysis = await asyncio.to_thread(self.analyzer.analyze, query)
            await check_connected(disconnected)
            revision = await asyncio.to_thread(self.revision_provider)
            key = build_cache_key(query, analysis, revision, **self.key_options)
        except RequestDisconnected:
            raise
        except Exception:
            raise ServiceError("INTERNAL_ERROR") from None
        cached = await asyncio.to_thread(self.cache.get, key) if self.cache else None
        await check_connected(disconnected)
        if cached is not None:
            yield "result", OnlineOutcome(cached, True)
            return
        yield "analysis", {"intent": analysis.intent.value}
        await check_connected(disconnected)
        try:
            retrieval = await asyncio.to_thread(self.retriever.retrieve, query, analysis)
        except Exception:
            raise ServiceError("RETRIEVAL_ERROR") from None
        yield "retrieval", {"strategy": retrieval.strategy.value}
        await check_connected(disconnected)
        try:
            generated = await asyncio.to_thread(self.generator.generate, query, analysis, retrieval)
            # Revalidate even an injectable runtime's declared result before emission.
            if not isinstance(generated, GroundedAnswerResult):
                raise GenerationError("grounded_result_required")
            if generated.status.value == "answered":
                generated = validate_cached_answer(generated.model_dump(mode="json"))
            else:
                generated = GroundedAnswerResult.model_validate(generated.model_dump(mode="json"))
                if generated.claims or generated.citations or generated.used_evidence_ids:
                    raise GenerationError("invalid_insufficient_result")
        except Exception:
            raise ServiceError("GENERATION_ERROR") from None
        await check_connected(disconnected)
        yield "generation", {"status": "validated"}
        await check_connected(disconnected)
        if self.cache and generated.status.value == "answered":
            # Thread cancellation cannot retract an already submitted Redis command.
            await asyncio.to_thread(self.cache.put, key, generated)
        await check_connected(disconnected)
        yield "result", OnlineOutcome(generated, False)

    async def query(self, query, disconnected):
        async for event, value in self.events(query, disconnected):
            if event == "result":
                return value
        raise ServiceError("INTERNAL_ERROR")
