"""Conservative contextual extraction. No enterprise dictionary is assumed."""
from dataclasses import dataclass
import re

from rag_qa.query.schemas import QueryEntities, ENTITY_BYTE_LIMITS

TOKEN = r"(?<![A-Za-z0-9_.-])[A-Za-z0-9][A-Za-z0-9_-]*(?![A-Za-z0-9_.-])"
LABELS = {
    "equipment_model": r"设备型号|型号|(?<![A-Za-z])(?:equipment\s+model|model)(?![A-Za-z])",
    "alarm_code": r"报警码|故障码|报警|(?<![A-Za-z])(?:alarm\s+code|fault\s+code|alarm)(?![A-Za-z])",
    "part_number": r"备件号|配件号|零件号|物料号|(?<![A-Za-z])part\s+(?:number|no\.?)(?![A-Za-z])",
}
NUMERIC_MEASURE = re.compile(r"\d+(?:\.\d+)?(?:MPa|Pa|kPa|mm|cm|m|rpm|Hz|kW|V|A|h|kg|%)\Z", re.I)
DATE = re.compile(r"\d{4}[-_]\d{1,2}[-_]\d{1,2}\Z")
UNIT_TAIL = re.compile(r"^(?:小时|分钟|秒|天|个月|年|毫米|厘米|转/分|度|个|次|%|MPa|Pa|kPa|rpm|mm|cm|Hz|kW|kg)(?![A-Za-z])", re.I)
PLACEHOLDERS = frozenset({"unknown", "none", "null", "model", "alarm", "part"})


def evidence_spans(query, value):
    """Case-sensitive full-token evidence, never a substring of another identifier."""
    return list(re.finditer(r"(?<![A-Za-z0-9_.-])" + re.escape(value) + r"(?![A-Za-z0-9_.-])", query))


def valid_identifier(value, query, span, *, explicit=False):
    if DATE.fullmatch(value) or NUMERIC_MEASURE.fullmatch(value) or value.lower() in PLACEHOLDERS:
        return False
    if value.endswith(("-", "_")) or UNIT_TAIL.match(query[span[1]:].lstrip()):
        return False
    if not explicit and not (re.search(r"[A-Za-z]", value) and re.search(r"\d", value)):
        return False
    return True


@dataclass(frozen=True)
class ExtractionResult:
    entities: QueryEntities
    warnings: tuple[str, ...]
    ambiguous_fields: frozenset[str]


def extract_entities(query):
    candidates = {name: [] for name in QueryEntities.model_fields}
    claimed = set()
    warnings = []

    def add(field, value):
        if len(value.encode("utf-8")) <= ENTITY_BYTE_LIMITS[field]:
            candidates[field].append(value)
        else:
            warnings.append("entity_too_long_" + field)

    for field, label in LABELS.items():
        # Bound separator scanning; repeated unbounded whitespace groups can backtrack excessively.
        pattern = re.compile(r"(?:" + label + r")(?:\s|[:：=\"'“‘]|为|是){0,16}(?P<value>" + TOKEN + r")", re.I)
        for match in pattern.finditer(query):
            value = match.group("value")
            if valid_identifier(value, query, match.span("value"), explicit=True):
                add(field, value)
                claimed.add(match.span("value"))

    def near(span, expression, distance=24):
        return bool(re.search(expression, query[max(0, span[0] - distance):span[1] + distance], re.I))

    # Infer a role only with nearby manufacturing words and a narrow token shape.
    tokens = list(re.finditer(TOKEN, query))
    for match in tokens:
        if match.span() in claimed or not valid_identifier(match.group(), query, match.span()):
            continue
        value = match.group()
        if re.fullmatch(r"[A-Za-z]+[-_]\d+[-_][A-Za-z0-9_-]+", value) and near(match.span(), r"备件|配件|零件|物料|\bparts?\b"):
            add("part_number", value); claimed.add(match.span())
        elif re.fullmatch(r"(?:ALM[-_]\d{2,}|E\d{2,})", value, re.I) and near(match.span(), r"报警|故障|\balarm\b|\bfault\b", 16):
            add("alarm_code", value); claimed.add(match.span())
    for match in tokens:
        value = match.group()
        if (match.span() not in claimed and valid_identifier(value, query, match.span())
                and re.fullmatch(r"[A-Za-z]+[-_]\d+(?:[-_][A-Za-z0-9]+)*", value)
                and near(match.span(), r"型号|设备|机床|主轴|润滑|保养|维护|参数|规格|报警|故障|转速|\bmodel\b|\bmachine\b|\bmaintenance\b")):
            add("equipment_model", value)

    for field, labels in {"manufacturer": "制造商|厂家|manufacturer", "equipment_type": "设备类型|equipment type",
                          "fault_symptom": "故障现象|故障症状|fault symptom"}.items():
        pattern = re.compile(r"(?:" + labels + r")\s*[:：=]\s*([^，。；;!?？\n]+)", re.I)
        for match in pattern.finditer(query):
            value = match.group(1).strip()
            if value:
                add(field, value)
    values, ambiguous = {}, set()
    for field, found in candidates.items():
        unique = list(dict.fromkeys(found))
        if len(unique) > 1:
            ambiguous.add(field)
            warnings.append("ambiguous_" + field)
        values[field] = unique[0] if len(unique) == 1 else None
    return ExtractionResult(QueryEntities(**values), tuple(dict.fromkeys(warnings)), frozenset(ambiguous))
