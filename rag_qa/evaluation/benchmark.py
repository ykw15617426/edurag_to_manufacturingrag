"""Fixed authored SYNTHETIC benchmark. None of these are production facts."""
import hashlib
from types import SimpleNamespace
from rag_qa.ingestion.fingerprints import sha256_content, build_parent_id, build_child_id
from rag_qa.schemas.manufacturing_metadata import ManufacturingDocumentMetadata
from rag_qa.retrieval.fast_path import FastPathCorpus
from .schemas import EvaluationDataset, RetrievalEvaluationSample

DISCLAIMER = "SYNTHETIC / NOT PRODUCTION FACTS; authored equipment, values and repair examples, not approved production data."
MODELS = ("SYN-CNC-100", "SYN-CNC-200", "SYN-CNC-300")
KINDS = ("alarm", "fault", "maintenance", "parameter", "parts", "manual", "case")


def controlled_benchmark():
    children, entries, samples = [], [], []
    for i, model in enumerate(MODELS, 1):
        part = ("PN-001", "PN-001A", "PN-010")[i - 1]
        for kind in KINDS:
            docid = f"SYNTHETIC-{model}-{kind}"
            queries = dict(alarm=f"设备型号 {model} 报警码 E102 的原因是什么？",
                fault=f"设备型号 {model} 主轴振动故障如何排查？",
                maintenance=f"设备型号 {model} 维护保养周期是什么？",
                parameter=f"设备型号 {model} 主轴转速参数是多少？",
                parts=f"设备型号 {model} 备件号 {part} 的规格是什么？",
                manual=f"设备型号 {model} 操作手册中的启动顺序是什么？",
                case=f"设备型号 {model} 主轴振动故障维修案例是什么？")
            facts = dict(alarm=f"E102 在本合成型号表示模拟润滑压力报警，示例原因编号 {i}。",
                fault=f"本合成型号的振动排查示例是检查模拟支座 {i}。",
                maintenance=f"本合成型号的模拟保养周期为 {i * 100} 小时。",
                parameter=f"本合成型号 V2 的模拟主轴转速为 {i * 1000} rpm，V1 历史值不适用。",
                parts=f"本合成型号的模拟备件 {part} 标记为规格 {i}。",
                manual=f"本合成型号的模拟启动顺序为检查、确认、启动，步骤编号 {i}。",
                case=f"本合成维修案例中的主轴振动源是模拟支座 {i}，仅作评估示例。")
            business = dict(document_id=docid, document_version="V2" if kind == "parameter" else "V1",
                title=f"SYNTHETIC {model} {kind}", knowledge_type=kind, equipment_model=model,
                equipment_type="合成数控机床", manufacturer="SYNTHETIC",
                alarm_code="E102" if kind == "alarm" else None,
                part_number=part if kind == "parts" else None,
                fault_symptom="主轴振动" if kind == "fault" else None,
                maintenance_type="模拟保养" if kind == "maintenance" else None)
            business = ManufacturingDocumentMetadata(**business).to_metadata()
            segments = [DISCLAIMER + "\n" + model + "\n" + facts[kind], "模拟证据补充：" + facts[kind]]
            parent = "\n".join(segments)
            parent_hash = sha256_content(parent)
            parent_id = build_parent_id(docid, parent_hash)
            child_ids = []
            for segment in segments:
                child_hash = sha256_content(segment)
                child_id = build_child_id(docid, parent_id, child_hash)
                child_ids.append(child_id)
                metadata = dict(business, id=child_id, child_id=child_id, parent_id=parent_id, parent_content=parent,
                    document_sha256=hashlib.sha256(parent.encode("utf-8")).hexdigest(),
                    parent_content_sha256=parent_hash, child_content_sha256=child_hash,
                    source_file=f"synthetic/{docid}.txt", metadata_source="front_matter", source="controlled_synthetic")
                children.append(SimpleNamespace(page_content=segment, metadata=metadata))
            intent = dict(alarm="alarm_fault", fault="alarm_fault", maintenance="maintenance", parameter="parameter",
                          parts="parts", manual="knowledge", case="alarm_fault")[kind]
            tags = ["SYNTHETIC", kind, model]
            if kind == "alarm": tags.append("same_alarm_different_model")
            if kind in {"fault", "case"}: tags.append("similar_fault")
            if kind == "parts": tags.append("similar_part_number")
            if kind == "parameter": tags.append("active_V2_not_historical_V1")
            sample = RetrievalEvaluationSample(sample_id=f"{model}-{kind}", query=queries[kind],
                expected_parent_ids=(parent_id,), expected_document_ids=(docid,), expected_child_ids=tuple(child_ids),
                expected_intent=intent, expected_equipment_model=model,
                expected_alarm_code=business["alarm_code"], expected_part_number=business["part_number"],
                reference_answer=facts[kind], tags=tuple(tags),
                fast_path_labels=("exact_alarm",) if kind == "alarm" else ("exact_faq",))
            samples.append(sample)
            entries.append(dict(business, entry_id=sample.sample_id, question=sample.query,
                                evidence_text=parent, parent_id=parent_id, source_file=metadata["source_file"]))
    # Paraphrase FAQ opportunities measure raw BM25 diagnostic scores without enabling acceptance.
    for sample in tuple(samples):
        if "maintenance" in sample.tags:
            samples.append(sample.model_copy(update=dict(sample_id=sample.sample_id + "-paraphrase",
                query=sample.query.replace("维护保养周期是什么", "需要多久进行维护保养"), fast_path_labels=("bm25_faq",))))
    # Two relevant documents/parents, same equipment; exercises macro recall and subquery experiments.
    maintenance, parameter = [s for s in samples if s.sample_id == MODELS[0] + "-" + "maintenance"][0], [s for s in samples if s.sample_id == MODELS[0] + "-" + "parameter"][0]
    samples.append(RetrievalEvaluationSample(sample_id="multi-relevant", query=f"设备型号 {MODELS[0]} 维护保养周期和主轴转速参数分别是什么？",
        expected_parent_ids=maintenance.expected_parent_ids + parameter.expected_parent_ids,
        expected_child_ids=maintenance.expected_child_ids + parameter.expected_child_ids,
        expected_document_ids=maintenance.expected_document_ids + parameter.expected_document_ids,
        expected_equipment_model=MODELS[0], tags=("SYNTHETIC", "multiple_relevant")))
    dataset = EvaluationDataset(dataset_type="controlled_synthetic", provenance_note=DISCLAIMER, samples=tuple(samples))
    return dataset, tuple(children), FastPathCorpus(entries)
