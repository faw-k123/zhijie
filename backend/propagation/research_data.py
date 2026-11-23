"""研究数据服务层。

职责限定：
- 读取 research/data/manifest.json 与 active_version；
- 对四个 JSON 做 SHA256、大小、版本校验；
- 统一缓存并暴露 load_* 函数；
- 对单条坏数据做隔离，返回 warnings。

本模块不写数据库、不依赖 SQL Server / Neo4j，也不修改现有传播分析逻辑。
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from django.conf import settings

SCHEMA_VERSION = "1.0.0"
DATA_FILES = (
    "cases.json",
    "success_factors.json",
    "music_scores.json",
    "regional_strategies.json",
)
REQUIRED_CASE_FIELDS = (
    "case_id",
    "performer",
    "performer_type",
    "country",
    "region",
    "instrument",
    "work",
    "music_type",
    "event_date_text",
    "event_name",
    "venue",
    "channel",
    "target_audience",
    "learning_motivation",
    "adaptation",
    "era_theme",
    "religion_culture",
    "feedback",
    "success_evidence",
    "research_notes",
    "summary",
    "review_status",
    "display_allowed",
    "source_count",
    "source_ids",
    "sources",
    "updated_at",
)
INDICATOR_IDS = (
    "emotional_resonance",
    "timbre_identity",
    "story_explainability",
    "cross_cultural_adaptation",
    "education_support",
    "bridge_role",
    "audience_participation",
    "channel_fit",
    "era_theme_relevance",
    "sustainability",
)
ALLOWED_REVIEW_STATUS = {"A", "B", "C", "D"}
ALLOWED_SOURCE_TYPES = {"主流媒体", "机构官网", "学术论文", "演奏者本人", "视频平台", "演出主办方", "其他"}


class ResearchDataError(Exception):
    """数据文件级错误：返回 503，不进入统计。"""

    def __init__(self, code: str, message: str, details: Any = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details


@dataclass(frozen=True)
class ResearchBundle:
    manifest: dict[str, Any]
    version: str
    version_meta: dict[str, Any]
    cases_doc: dict[str, Any]
    success_doc: dict[str, Any]
    music_doc: dict[str, Any]
    regional_doc: dict[str, Any]
    warnings: list[dict[str, Any]] = field(default_factory=list)

    @property
    def cases(self) -> list[dict[str, Any]]:
        return list(self.cases_doc.get("cases") or [])

    @property
    def scores(self) -> list[dict[str, Any]]:
        return list(self.success_doc.get("scores") or [])

    @property
    def target_case_count(self) -> int:
        try:
            return int(self.manifest.get("target_case_count") or 0)
        except (TypeError, ValueError):
            return 0


_CACHE: dict[tuple[str, str], ResearchBundle] = {}


def clear_cache() -> None:
    """测试或版本切换后清空缓存。"""
    _CACHE.clear()


def get_data_root() -> Path:
    configured = getattr(settings, "RESEARCH_DATA_DIR", None)
    if configured:
        return Path(configured).expanduser().resolve()
    return (Path(settings.BASE_DIR).parent / "research" / "data").resolve()


def _manifest_path() -> Path:
    return get_data_root() / "manifest.json"


def _read_json_file(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ResearchDataError("data_file_missing", f"研究数据文件不存在：{path.name}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        raise ResearchDataError(
            "invalid_json",
            f"研究数据 JSON 解析失败：{path.name}",
            {"line": exc.lineno, "column": exc.colno, "error": exc.msg},
        ) from exc
    except OSError as exc:
        raise ResearchDataError("data_file_unreadable", f"研究数据文件无法读取：{path.name}", str(exc)) from exc
    if not isinstance(payload, dict):
        raise ResearchDataError("invalid_json_root", f"{path.name} 顶层必须是对象")
    return payload


def load_manifest() -> dict[str, Any]:
    """读取并做结构校验，不加载数据文件。"""
    manifest = _read_json_file(_manifest_path())
    _validate_manifest_shape(manifest)
    return manifest


def get_active_version(manifest: dict[str, Any] | None = None) -> str:
    manifest = manifest or load_manifest()
    _validate_manifest_shape(manifest)
    return str(manifest["active_version"])


def _validate_manifest_shape(manifest: dict[str, Any]) -> None:
    if manifest.get("schema_version") != SCHEMA_VERSION:
        raise ResearchDataError(
            "schema_version_mismatch",
            "manifest schema_version 与当前契约不一致",
            {"expected": SCHEMA_VERSION, "actual": manifest.get("schema_version")},
        )
    active = manifest.get("active_version")
    if not isinstance(active, str) or not active:
        raise ResearchDataError("missing_active_version", "manifest 缺少 active_version")
    versions = manifest.get("versions")
    if not isinstance(versions, list) or not versions:
        raise ResearchDataError("missing_versions", "manifest 缺少 versions")
    version_meta = next((v for v in versions if isinstance(v, dict) and v.get("version") == active), None)
    if not version_meta:
        raise ResearchDataError("active_version_not_found", f"active_version={active} 不在 versions 中")
    if version_meta.get("status") != "reviewed":
        status = version_meta.get("status")
        raise ResearchDataError(
            "version_not_reviewed",
            f"数据版本 {active} 尚未审核（status={status}），接口不加载",
            {"version": active, "status": status},
        )
    path = version_meta.get("path")
    if not isinstance(path, str) or not _safe_version_path(path):
        raise ResearchDataError("invalid_version_path", f"版本路径不合法：{path!r}")
    files = version_meta.get("files")
    if not isinstance(files, dict) or set(files) != set(DATA_FILES):
        raise ResearchDataError(
            "manifest_files_mismatch",
            "manifest 的文件清单必须且只能包含四个研究数据文件",
            {"expected": list(DATA_FILES), "actual": list(files or {})},
        )
    try:
        target = int(manifest.get("target_case_count") or 0)
    except (TypeError, ValueError) as exc:
        raise ResearchDataError("invalid_target_count", "target_case_count 必须是整数") from exc
    if target <= 0:
        raise ResearchDataError("invalid_target_count", "target_case_count 必须大于 0")


def _safe_version_path(path: str) -> bool:
    return bool(re.fullmatch(r"v\d+\.\d+", path))


def validate_hash(version: str, filename: str, expected: dict[str, Any]) -> bool:
    """校验单个文件的大小与 SHA256；失败抛 ResearchDataError。"""
    if filename not in DATA_FILES:
        raise ResearchDataError("invalid_data_file", f"未知的数据文件：{filename}")
    path = get_data_root() / version / filename
    if not path.exists():
        raise ResearchDataError("data_file_missing", f"研究数据文件不存在：{version}/{filename}")
    try:
        content = path.read_bytes()
    except OSError as exc:
        raise ResearchDataError("data_file_unreadable", f"研究数据文件无法读取：{version}/{filename}", str(exc)) from exc
    expected_bytes = expected.get("bytes")
    actual_bytes = len(content)
    if expected_bytes != actual_bytes:
        raise ResearchDataError(
            "file_size_mismatch",
            f"文件大小与 manifest 不一致：{version}/{filename}",
            {"expected": expected_bytes, "actual": actual_bytes},
        )
    expected_hash = str(expected.get("sha256") or "").lower()
    actual_hash = hashlib.sha256(content).hexdigest()
    if expected_hash != actual_hash:
        raise ResearchDataError(
            "hash_mismatch",
            f"文件 SHA256 与 manifest 不一致：{version}/{filename}",
            {"expected": expected_hash, "actual": actual_hash},
        )
    return True


def _clean_cases(doc: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    cases = doc.get("cases")
    if not isinstance(cases, list):
        raise ResearchDataError("invalid_cases", "cases.json 的 cases 必须是数组")
    warnings: list[dict[str, Any]] = []
    seen: set[str] = set()
    cleaned: list[dict[str, Any]] = []
    for index, case in enumerate(cases):
        if not isinstance(case, dict):
            warnings.append({"file": "cases.json", "record": f"index={index}", "reason": "案例不是对象"})
            continue
        case_id = str(case.get("case_id") or "")
        if not re.fullmatch(r"CASE\d{3}", case_id):
            warnings.append({"file": "cases.json", "record": f"index={index}", "reason": "case_id 格式不合法"})
            continue
        if case_id in seen:
            warnings.append({"file": "cases.json", "record": case_id, "reason": "case_id 重复"})
            continue
        missing = [name for name in REQUIRED_CASE_FIELDS if name not in case]
        if missing:
            warnings.append({"file": "cases.json", "record": case_id, "reason": f"缺少字段：{missing}"})
            continue
        if case.get("review_status") not in ALLOWED_REVIEW_STATUS:
            warnings.append({"file": "cases.json", "record": case_id, "reason": "review_status 非法"})
            continue
        if case.get("review_status") in {"C", "D"} and case.get("display_allowed") is True:
            warnings.append({"file": "cases.json", "record": case_id, "reason": "C/D 不得 display_allowed=true"})
            continue
        sources = case.get("sources")
        if not isinstance(sources, list) or not sources:
            warnings.append({"file": "cases.json", "record": case_id, "reason": "sources 不能为空"})
            continue
        source_ids = [str(s.get("source_id") or "") for s in sources if isinstance(s, dict)]
        if len(source_ids) != len(sources) or len(set(source_ids)) != len(source_ids):
            warnings.append({"file": "cases.json", "record": case_id, "reason": "来源编号缺失或重复"})
            continue
        if set(source_ids) != set(case.get("source_ids") or []):
            warnings.append({"file": "cases.json", "record": case_id, "reason": "source_ids 与 sources 不一致"})
            continue
        try:
            stored_source_count = int(case.get("source_count"))
        except (TypeError, ValueError):
            warnings.append({"file": "cases.json", "record": case_id, "reason": "source_count 不是整数"})
            continue
        if stored_source_count != len(sources):
            warnings.append({"file": "cases.json", "record": case_id, "reason": "source_count 与 sources 数量不一致"})
            continue
        bad_source = next(
            (s for s in sources if isinstance(s, dict) and s.get("source_type") not in ALLOWED_SOURCE_TYPES),
            None,
        )
        if bad_source is not None:
            warnings.append({"file": "cases.json", "record": case_id, "reason": f"来源类型非法：{bad_source.get('source_type')}"})
            continue
        cleaned.append(case)
        seen.add(case_id)
    doc = dict(doc)
    doc["cases"] = cleaned
    doc["case_count"] = len(cleaned)
    return doc, warnings


def _clean_scores(
    doc: dict[str, Any],
    case_ids: set[str],
    case_source_ids: dict[str, set[str]],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    records = doc.get("scores")
    if not isinstance(records, list):
        raise ResearchDataError("invalid_scores", "success_factors.json 的 scores 必须是数组")
    warnings: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    cleaned: list[dict[str, Any]] = []
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            warnings.append({"file": "success_factors.json", "record": f"index={index}", "reason": "评分不是对象"})
            continue
        case_id = str(record.get("case_id") or "")
        indicator_id = str(record.get("indicator_id") or "")
        if case_id not in case_ids:
            warnings.append({"file": "success_factors.json", "record": f"{case_id}/{indicator_id}", "reason": "引用不存在的案例"})
            continue
        if indicator_id not in INDICATOR_IDS:
            warnings.append({"file": "success_factors.json", "record": f"{case_id}/{indicator_id}", "reason": "未知指标 ID"})
            continue
        key = (case_id, indicator_id)
        if key in seen:
            warnings.append({"file": "success_factors.json", "record": f"{case_id}/{indicator_id}", "reason": "评分重复"})
            continue
        source_ids = record.get("source_ids")
        if not isinstance(source_ids, list):
            warnings.append({"file": "success_factors.json", "record": f"{case_id}/{indicator_id}", "reason": "source_ids 必须是数组"})
            continue
        unknown_sources = set(str(item) for item in source_ids) - case_source_ids.get(case_id, set())
        if unknown_sources:
            warnings.append({
                "file": "success_factors.json",
                "record": f"{case_id}/{indicator_id}",
                "reason": f"source_ids 不属于该案例：{sorted(unknown_sources)}",
            })
            continue
        value = record.get("score")
        if value is not None and (not isinstance(value, int) or isinstance(value, bool) or value < 0 or value > 3):
            warnings.append({"file": "success_factors.json", "record": f"{case_id}/{indicator_id}", "reason": "score 必须是 0—3 或 null"})
            continue
        if value is not None and not source_ids:
            warnings.append({"file": "success_factors.json", "record": f"{case_id}/{indicator_id}", "reason": "非空评分缺少 source_ids"})
            continue
        if value is not None and not str(record.get("evidence") or "").strip():
            warnings.append({"file": "success_factors.json", "record": f"{case_id}/{indicator_id}", "reason": "非空评分缺少证据"})
            continue
        if value is None and not str(record.get("missing_reason") or "").strip():
            warnings.append({"file": "success_factors.json", "record": f"{case_id}/{indicator_id}", "reason": "未知评分缺少 missing_reason"})
            continue
        cleaned.append(record)
        seen.add(key)
    doc = dict(doc)
    doc["scores"] = cleaned
    return doc, warnings


def _validate_doc_version(doc: dict[str, Any], version: str, filename: str) -> None:
    if doc.get("schema_version") != SCHEMA_VERSION:
        raise ResearchDataError(
            "schema_version_mismatch",
            f"{filename} schema_version 与契约不一致",
            {"expected": SCHEMA_VERSION, "actual": doc.get("schema_version")},
        )
    if doc.get("data_version") != version:
        raise ResearchDataError(
            "data_version_mismatch",
            f"{filename} data_version 与 active_version 不一致",
            {"expected": version, "actual": doc.get("data_version")},
        )


def _validate_music(doc: dict[str, Any]) -> list[dict[str, Any]]:
    warnings: list[dict[str, Any]] = []
    if doc.get("status") not in {"pending", "partial", "complete"}:
        raise ResearchDataError("invalid_music_status", "music_scores.json status 非法")
    weights = doc.get("weights")
    if not isinstance(weights, dict):
        raise ResearchDataError("invalid_music_weights", "music_scores.json 缺少 weights")
    try:
        total_weight = sum(float(v) for v in weights.values())
    except (TypeError, ValueError) as exc:
        raise ResearchDataError("invalid_music_weights", "music_scores.json weights 必须是数字") from exc
    if abs(total_weight - 1.0) > 0.0001:
        raise ResearchDataError("invalid_music_weights", "音乐潜力权重合计必须为 1.0", {"actual": total_weight})
    if doc.get("status") == "pending" and doc.get("items"):
        warnings.append({"file": "music_scores.json", "record": "items", "reason": "status=pending 但 items 非空，接口将按待补充处理"})
    return warnings


def _validate_regional(doc: dict[str, Any]) -> list[dict[str, Any]]:
    warnings: list[dict[str, Any]] = []
    if doc.get("status") not in {"pending", "partial", "complete"}:
        raise ResearchDataError("invalid_regional_status", "regional_strategies.json status 非法")
    if doc.get("status") == "pending" and doc.get("rows"):
        warnings.append({"file": "regional_strategies.json", "record": "rows", "reason": "status=pending 但 rows 非空，接口将按待补充处理"})
    return warnings


def load_bundle() -> ResearchBundle:
    """读取 manifest、校验四个文件哈希，并返回清洗后的 bundle。"""
    manifest_path = _manifest_path()
    if not manifest_path.exists():
        raise ResearchDataError("manifest_missing", f"研究数据 manifest 不存在：{manifest_path}")
    try:
        manifest_bytes = manifest_path.read_bytes()
    except OSError as exc:
        raise ResearchDataError("manifest_unreadable", "研究数据 manifest 无法读取", str(exc)) from exc

    manifest = _read_json_file(manifest_path)
    _validate_manifest_shape(manifest)
    version = str(manifest["active_version"])
    version_meta = next(v for v in manifest["versions"] if v.get("version") == version)
    version_path = str(version_meta["path"])

    signature = []
    for filename in DATA_FILES:
        path = get_data_root() / version_path / filename
        if not path.exists():
            raise ResearchDataError("data_file_missing", f"研究数据文件不存在：{version_path}/{filename}")
        stat = path.stat()
        signature.append((filename, stat.st_mtime_ns, stat.st_size))
    cache_key = (str(manifest_path), hashlib.sha256(manifest_bytes).hexdigest(), tuple(signature))
    if cache_key in _CACHE:
        return _CACHE[cache_key]

    for filename in DATA_FILES:
        validate_hash(version_path, filename, version_meta["files"][filename])

    docs: dict[str, dict[str, Any]] = {}
    for filename in DATA_FILES:
        doc = _read_json_file(get_data_root() / version_path / filename)
        _validate_doc_version(doc, version, filename)
        docs[filename] = doc

    warnings: list[dict[str, Any]] = []
    cases_doc, case_warnings = _clean_cases(docs["cases.json"])
    warnings.extend(case_warnings)
    case_ids = {case["case_id"] for case in cases_doc["cases"]}
    case_source_ids = {
        case["case_id"]: set(case.get("source_ids") or [])
        for case in cases_doc["cases"]
    }
    success_doc, score_warnings = _clean_scores(docs["success_factors.json"], case_ids, case_source_ids)
    warnings.extend(score_warnings)
    warnings.extend(_validate_music(docs["music_scores.json"]))
    warnings.extend(_validate_regional(docs["regional_strategies.json"]))

    bundle = ResearchBundle(
        manifest=manifest,
        version=version,
        version_meta=version_meta,
        cases_doc=cases_doc,
        success_doc=success_doc,
        music_doc=docs["music_scores.json"],
        regional_doc=docs["regional_strategies.json"],
        warnings=warnings,
    )
    _CACHE[cache_key] = bundle
    return bundle


def load_cases(version: str | None = None) -> dict[str, Any]:
    bundle = load_bundle()
    if version and version != bundle.version:
        raise ResearchDataError("version_not_active", f"只能读取 active_version，当前为 {bundle.version}")
    return bundle.cases_doc


def load_success_factors(version: str | None = None) -> dict[str, Any]:
    bundle = load_bundle()
    if version and version != bundle.version:
        raise ResearchDataError("version_not_active", f"只能读取 active_version，当前为 {bundle.version}")
    return bundle.success_doc


def load_music_scores(version: str | None = None) -> dict[str, Any]:
    bundle = load_bundle()
    if version and version != bundle.version:
        raise ResearchDataError("version_not_active", f"只能读取 active_version，当前为 {bundle.version}")
    return bundle.music_doc


def load_regional_matrix(version: str | None = None) -> dict[str, Any]:
    bundle = load_bundle()
    if version and version != bundle.version:
        raise ResearchDataError("version_not_active", f"只能读取 active_version，当前为 {bundle.version}")
    return bundle.regional_doc
