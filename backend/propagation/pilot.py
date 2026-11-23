"""六国国际传播实测：导入批次、阈值聚合、待审批评分。

设计边界：
- 只写 research/candidates/v1.7-six-country-pilot/，不写 v1.7 正式数据；
- 描述性统计与正式评分分离；
- 真实数据不足时 formal_score 为 null，不补 0；
- 排名必须经过负责人审批，且只使用八项完整单元。
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import statistics
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .research_analytics import PILOT_RESPONSE_FIELDS, validate_pilot_responses
from .research_data import ResearchBundle

DIMENSIONS = [
    {"key": "emotional_resonance", "label": "情绪共鸣", "source": "survey", "order": 1},
    {"key": "timbre_identity", "label": "音色辨识", "source": "survey", "order": 2},
    {"key": "melody_accessibility", "label": "旋律可进入性", "source": "survey", "order": 3},
    {"key": "cultural_story", "label": "文化故事性", "source": "survey", "order": 4},
    {"key": "adaptation_space", "label": "跨文化改编空间", "source": "survey", "order": 5},
    {"key": "visual_expressiveness", "label": "视觉表现力", "source": "survey", "order": 6},
    {"key": "era_theme_relevance", "label": "时代主题相关性", "source": "survey", "order": 7},
    {"key": "existing_evidence", "label": "既有传播证据", "source": "evidence", "order": 8},
]
SURVEY_DIMENSIONS = [item for item in DIMENSIONS if item["source"] == "survey"]
ALL_KEYS = [item["key"] for item in DIMENSIONS]
FIELD_LABELS = {field["key"]: field["label"] for field in PILOT_RESPONSE_FIELDS}

DEFAULT_CONFIG = {
    "config_version": "PILOT-THRESHOLDS-2026-11-08-proposed",
    "status": "proposed",
    "approved_by": None,
    "approved_at": None,
    "min_per_variant": 20,
    "min_per_cell": 40,
    "variant_balance_tolerance": 0.25,
    "min_country_total": 120,
    "min_country_cells": 12,
    "min_completion_rate": 70,
    "max_missing_ratio": 0.20,
    "winsorize_low": 0.01,
    "winsorize_high": 0.99,
    "cross_country_min_countries": 3,
    "cross_country_min_cells": 12,
    "weights": {key: 1 / 8 for key in ALL_KEYS},
    "note": "建议值，尚未获得负责人确认；确认前不得开放正式排名。",
}


def _root() -> Path:
    configured = os.environ.get("PILOT_STORE_DIR")
    if configured:
        return Path(configured)
    return Path(__file__).resolve().parents[2] / "research" / "candidates" / "v1.7-six-country-pilot"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _canonical_rows(rows: list[dict[str, Any]]) -> str:
    return json.dumps(rows, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _deidentify(row: dict[str, Any]) -> dict[str, Any]:
    allowed = {field["key"] for field in PILOT_RESPONSE_FIELDS}
    return {key: row.get(key) for key in allowed if key in row}


def _countries(bundle: ResearchBundle) -> list[str]:
    result = []
    for row in bundle.regional_doc.get("rows") or []:
        if row.get("display_allowed") is True and row.get("country") and row["country"] not in result:
            result.append(str(row["country"]))
    return result


def _music_items(bundle: ResearchBundle) -> list[dict[str, Any]]:
    return [item for item in (bundle.music_doc.get("items") or []) if item.get("display_allowed") is True]



def config() -> dict[str, Any]:
    path = _root() / "config_active.json"
    if path.exists():
        active = _read_json(path)
        version_path = _root() / "config_versions" / f"{active.get('config_version')}.json"
        if version_path.exists():
            return _read_json(version_path)
    return json.loads(json.dumps(DEFAULT_CONFIG, ensure_ascii=False))


def _config_validation(payload: dict[str, Any]) -> dict[str, float]:
    numeric = {
        "min_per_variant": (1, 10000, int),
        "min_per_cell": (1, 20000, int),
        "variant_balance_tolerance": (0, 1, float),
        "min_country_total": (1, 200000, int),
        "min_country_cells": (1, 120, int),
        "min_completion_rate": (0, 100, float),
        "max_missing_ratio": (0, 1, float),
        "winsorize_low": (0, 0.5, float),
        "winsorize_high": (0.5, 1, float),
        "cross_country_min_countries": (1, 6, int),
        "cross_country_min_cells": (1, 120, int),
    }
    result = {}
    for key, (low, high, typ) in numeric.items():
        try:
            value = typ(payload.get(key, DEFAULT_CONFIG[key]))
        except (TypeError, ValueError) as exc:
            raise ValueError(f"{key} 不是有效数值") from exc
        if not low <= value <= high:
            raise ValueError(f"{key} 超出允许范围 {low}—{high}")
        result[key] = value
    if result["winsorize_low"] >= result["winsorize_high"]:
        raise ValueError("winsorize_low 必须小于 winsorize_high")
    if result["min_per_cell"] < result["min_per_variant"] * 2:
        raise ValueError("min_per_cell 必须至少是 min_per_variant 的两倍")
    return result


def submit_config(payload: dict[str, Any], actor: str) -> dict[str, Any]:
    if config().get("status") == "approved":
        # 已审批版本不可覆盖；新值只能创建新版本。
        pass
    values = _config_validation(payload)
    version = f"CV-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"
    cfg = {**DEFAULT_CONFIG, **values, "config_version": version, "status": "pending_approval",
           "created_by": actor or "unknown", "created_at": _now(),
           "approved_by": None, "approved_at": None,
           "sha256": hashlib.sha256(json.dumps(values, sort_keys=True).encode()).hexdigest(),
           "note": "待审批配置版本；批准后不可修改，修改必须新建版本。"}
    _write_json(_root() / "config_versions" / f"{version}.json", cfg)
    return cfg


def approve_config(approver: str, config_version: str | None = None) -> dict[str, Any]:
    if config_version:
        path = _root() / "config_versions" / f"{config_version}.json"
        if not path.exists():
            raise FileNotFoundError(config_version)
        cfg = _read_json(path)
        if cfg.get("status") == "approved":
            raise ValueError("该配置版本已经审批，不能重复审批")
    else:
        cfg = json.loads(json.dumps(DEFAULT_CONFIG, ensure_ascii=False))
    cfg.update({"status": "approved", "approved_by": approver or "unknown", "approved_at": _now()})
    cfg["sha256"] = hashlib.sha256(json.dumps({k: cfg[k] for k in DEFAULT_CONFIG if k in cfg and k not in {"status", "approved_by", "approved_at", "sha256", "note", "config_version", "created_by", "created_at"}}, sort_keys=True).encode()).hexdigest()
    _write_json(_root() / "config_versions" / f"{cfg['config_version']}.json", cfg)
    active_path = _root() / "config_active.json"
    if active_path.exists():
        old = _read_json(active_path)
        old_path = _root() / "config_versions" / f"{old.get('config_version')}.json"
        if old_path.exists():
            old_cfg = _read_json(old_path)
            old_cfg["status"] = "superseded"
            _write_json(old_path, old_cfg)
    _write_json(active_path, {"config_version": cfg["config_version"], "sha256": cfg["sha256"], "activated_at": _now()})
    return cfg


def evidence_scores() -> list[dict[str, Any]]:
    root = _root() / "evidence"
    if not root.exists():
        return []
    return [_read_json(path) for path in sorted(root.glob("*.json"))]


def approved_evidence() -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for item in evidence_scores():
        if item.get("status") == "approved":
            result[str(item.get("music_id"))] = item
    return result


def submit_evidence(payload: dict[str, Any], actor: str) -> dict[str, Any]:
    music_id = str(payload.get("music_id") or "").strip()
    if not music_id:
        raise ValueError("music_id 必填")
    try:
        score = float(payload.get("score_0_100", payload.get("score")))
    except (TypeError, ValueError) as exc:
        raise ValueError("证据分必须是 0—100 数值") from exc
    if not 0 <= score <= 100:
        raise ValueError("证据分必须在 0—100 之间")
    source = str(payload.get("source") or "").strip()
    rule = str(payload.get("rule_version") or "").strip()
    if not source or not rule:
        raise ValueError("source 和 rule_version 必填")
    evidence_id = f"EV-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"
    record = {"evidence_id": evidence_id, "music_id": music_id, "score_0_100": score,
              "source": source, "rule_version": rule, "status": "pending_approval",
              "entered_by": actor or "unknown", "entered_at": _now(),
              "approved_by": None, "approved_at": None, "revoked_at": None,
              "revoke_reason": None, "history": [{"at": _now(), "action": "submitted", "by": actor or "unknown"}]}
    _write_json(_root() / "evidence" / f"{evidence_id}.json", record)
    return record


def approve_evidence(evidence_id: str, approver: str) -> dict[str, Any]:
    path = _root() / "evidence" / f"{evidence_id}.json"
    if not path.exists():
        raise FileNotFoundError(evidence_id)
    record = _read_json(path)
    if record.get("status") != "pending_approval":
        raise ValueError("只有待审批证据分可以审批")
    for other in evidence_scores():
        if other.get("music_id") == record.get("music_id") and other.get("status") == "approved":
            other_path = _root() / "evidence" / f"{other['evidence_id']}.json"
            other.update({"status": "superseded", "superseded_at": _now()})
            other.setdefault("history", []).append({"at": _now(), "action": "superseded", "by": approver or "unknown"})
            _write_json(other_path, other)
    record.update({"status": "approved", "approved_by": approver or "unknown", "approved_at": _now()})
    record.setdefault("history", []).append({"at": _now(), "action": "approved", "by": approver or "unknown"})
    _write_json(path, record)
    return record


def revoke_evidence(evidence_id: str, approver: str, reason: str) -> dict[str, Any]:
    path = _root() / "evidence" / f"{evidence_id}.json"
    if not path.exists():
        raise FileNotFoundError(evidence_id)
    record = _read_json(path)
    record.update({"status": "revoked", "revoked_at": _now(), "revoke_reason": reason})
    record.setdefault("history", []).append({"at": _now(), "action": "revoked", "by": approver or "unknown", "reason": reason})
    _write_json(path, record)
    return record

def _winsorize(values: list[float], low: float, high: float) -> list[float]:
    if len(values) < 5:
        return list(values)
    ordered = sorted(values)
    lo = ordered[max(0, min(len(ordered) - 1, math.floor((len(ordered) - 1) * low)))]
    hi = ordered[max(0, min(len(ordered) - 1, math.ceil((len(ordered) - 1) * high)))]
    return [min(max(value, lo), hi) for value in values]


def _mean_sd(values: list[float]) -> tuple[float | None, float | None]:
    if not values:
        return None, None
    mean = statistics.fmean(values)
    sd = statistics.stdev(values) if len(values) > 1 else 0.0
    return round(mean, 3), round(sd, 3)


def _variant_rows(rows: list[dict[str, Any]], variant: str) -> list[dict[str, Any]]:
    return [row for row in rows if str(row.get("variant") or "").lower() == variant]


def _eligible_rows_from_validation(rows: list[dict[str, Any]], validation: dict[str, Any]) -> list[dict[str, Any]]:
    bad_rows = {int(item["row_number"]) for item in validation.get("errors") or []}
    result = []
    for index, row in enumerate(rows, start=2):
        if index not in bad_rows:
            result.append(_deidentify(row))
    return result


def _unit_stats(
    *,
    country: str,
    music_id: str,
    title: str,
    original_rows: list[dict[str, Any]],
    adapted_rows: list[dict[str, Any]],
    evidence_score: float | None,
    cfg: dict[str, Any],
) -> dict[str, Any]:
    variants: dict[str, Any] = {}
    for variant, rows in (("original", original_rows), ("adapted", adapted_rows)):
        variant_stats = {}
        for dim in SURVEY_DIMENSIONS:
            values = []
            for row in rows:
                raw = row.get(dim["key"])
                if raw is not None and str(raw).strip() != "":
                    values.append(float(raw))
            values = _winsorize(values, float(cfg["winsorize_low"]), float(cfg["winsorize_high"]))
            mean, sd = _mean_sd(values)
            variant_stats[dim["key"]] = {
                "n": len(values),
                "mean": mean,
                "sd": sd,
                "missing": len(rows) - len(values),
            }
        variants[variant] = {"n": len(rows), "dimensions": variant_stats}

    all_rows = original_rows + adapted_rows
    n_original = len(original_rows)
    n_adapted = len(adapted_rows)
    n_total = n_original + n_adapted
    balance = abs(n_original - n_adapted) / n_total if n_total else 0.0

    survey_means: dict[str, float | None] = {}
    for dim in SURVEY_DIMENSIONS:
        values = [
            float(row[dim["key"]])
            for row in all_rows
            if row.get(dim["key"]) is not None and str(row.get(dim["key"])).strip() != ""
        ]
        values = _winsorize(values, float(cfg["winsorize_low"]), float(cfg["winsorize_high"]))
        survey_means[dim["key"]] = _mean_sd(values)[0]
    survey_means["existing_evidence"] = evidence_score

    status = "not_started"
    reason = "尚无有效反馈"
    if n_total:
        status = "descriptive_only"
        reason = "样本未达到正式评分门槛"
        if n_original < int(cfg["min_per_variant"]) or n_adapted < int(cfg["min_per_variant"]):
            status = "insufficient_sample"
            reason = f"每个版本至少需要 {cfg['min_per_variant']} 份有效反馈"
        elif balance > float(cfg["variant_balance_tolerance"]):
            status = "variant_imbalance"
            reason = f"原版/适配版样本差异超过 {cfg['variant_balance_tolerance']:.0%}"
        elif n_total < int(cfg["min_per_cell"]):
            status = "insufficient_sample"
            reason = f"每单元至少需要 {cfg['min_per_cell']} 份有效反馈"
        elif any(
            variants[variant]["dimensions"][dim["key"]]["n"] < int(cfg["min_per_variant"])
            for variant in ("original", "adapted")
            for dim in SURVEY_DIMENSIONS
        ):
            status = "incomplete_measurement"
            reason = "存在测量项有效样本不足"
        else:
            missing = sum(
                variants[variant]["dimensions"][dim["key"]]["missing"]
                for variant in ("original", "adapted")
                for dim in SURVEY_DIMENSIONS
            )
            total_required = n_total * len(SURVEY_DIMENSIONS)
            if total_required and missing / total_required > float(cfg["max_missing_ratio"]):
                status = "incomplete_measurement"
                reason = f"测量项缺失率超过 {cfg['max_missing_ratio']:.0%}"
        if status == "descriptive_only":
            if evidence_score is None:
                status = "awaiting_evidence"
                reason = "缺少经审批的既有传播证据分，不能用受众评分替代"
            else:
                status = "eligible_for_review"
                reason = "达到门槛，可生成待审批评分"

    formal_score = None
    if status == "eligible_for_review":
        # 统一量纲：问卷 1—5 先转 0—100；证据分本来就是 0—100。
        weighted = 0.0
        for key in SURVEY_DIMENSIONS:
            mean_1_5 = survey_means[key["key"]]
            mean_100 = (float(mean_1_5) - 1) / 4 * 100
            weighted += mean_100 * float(cfg["weights"][key["key"]])
        weighted += float(evidence_score) * float(cfg["weights"]["existing_evidence"])
        if not 0 <= weighted <= 100:
            raise ValueError("formal_score 超出 0—100")
        formal_score = round(weighted, 2)

    variant_diff = {}
    for dim in SURVEY_DIMENSIONS:
        original_mean = variants["original"]["dimensions"][dim["key"]]["mean"]
        adapted_mean = variants["adapted"]["dimensions"][dim["key"]]["mean"]
        variant_diff[dim["key"]] = (
            round(adapted_mean - original_mean, 3)
            if original_mean is not None and adapted_mean is not None
            else None
        )

    return {
        "country": country,
        "music_id": music_id,
        "title": title,
        "n_total": n_total,
        "n_original": n_original,
        "n_adapted": n_adapted,
        "variant_balance": round(balance, 4),
        "variants": variants,
        "survey_means": survey_means,
        "variant_diff": variant_diff,
        "evidence_score": evidence_score,
        "formal_score": formal_score,
        "status": status,
        "status_reason": reason,
        "open_responses": [
            row.get("open_response") for row in all_rows if str(row.get("open_response") or "").strip()
        ],
        "cultural_risk_flags": [
            row.get("cultural_risk_flag") for row in all_rows if str(row.get("cultural_risk_flag") or "").strip()
        ],
    }


def aggregate(
    bundle: ResearchBundle,
    rows: list[dict[str, Any]],
    cfg: dict[str, Any] | None = None,
    protocol_version: str | None = None,
) -> dict[str, Any]:
    cfg = cfg or config()
    validation = validate_pilot_responses(bundle, rows)
    eligible = _eligible_rows_from_validation(rows, validation)
    protocol_excluded = 0
    if protocol_version:
        before_protocol = len(eligible)
        eligible = [row for row in eligible if str(row.get("protocol_version") or "") == protocol_version]
        protocol_excluded = before_protocol - len(eligible)
    # 低完成率剔除；在清洗层保留原始记录，不覆盖。
    rehearsal_excluded = sum(1 for row in eligible if str(row.get("dataset_kind") or "formal") == "pilot_rehearsal")
    eligible = [
        row for row in eligible
        if str(row.get("dataset_kind") or "formal") != "pilot_rehearsal"
        and str(row.get("completion_rate") or "").strip()
        and float(row.get("completion_rate")) >= float(cfg["min_completion_rate"])
    ]
    # 防御性去重：即使上游漏检，也不让同一 response_id 重复计数。
    seen_ids = set()
    deduped = []
    for row in eligible:
        rid = str(row.get("response_id") or "")
        if rid and rid in seen_ids:
            continue
        if rid:
            seen_ids.add(rid)
        deduped.append(row)
    duplicate_rows_excluded = len(eligible) - len(deduped)
    eligible = deduped
    countries = _countries(bundle)
    music_items = _music_items(bundle)
    evidence = approved_evidence()
    units = []
    for country in countries:
        for item in music_items:
            music_id = str(item.get("music_id"))
            title = str(item.get("title") or "")
            cell_rows = [row for row in eligible if row.get("country") == country and row.get("music_id") == music_id]
            evidence_record = evidence.get(music_id)
            unit = _unit_stats(
                country=country,
                music_id=music_id,
                title=title,
                original_rows=_variant_rows(cell_rows, "original"),
                adapted_rows=_variant_rows(cell_rows, "adapted"),
                evidence_score=float(evidence_record["score_0_100"]) if evidence_record else None,
                cfg=cfg,
            )
            unit["evidence_record_id"] = evidence_record.get("evidence_id") if evidence_record else None
            units.append(unit)

    country_summary = []
    for country in countries:
        country_units = [unit for unit in units if unit["country"] == country]
        country_summary.append({
            "country": country,
            "cells": len(country_units),
            "cells_with_data": sum(1 for unit in country_units if unit["n_total"] > 0),
            "eligible_cells": sum(1 for unit in country_units if unit["status"] == "eligible_for_review"),
            "valid_n": sum(unit["n_total"] for unit in country_units),
            "minimum_cells": cfg["min_country_cells"],
            "minimum_total": cfg["min_country_total"],
            "country_ready": (
                sum(1 for unit in country_units if unit["n_total"] > 0) >= cfg["min_country_cells"]
                and sum(unit["n_total"] for unit in country_units) >= cfg["min_country_total"]
            ),
        })

    # 跨国汇总：先国家内聚合，再对国家等权；避免样本量大的国家支配。
    cross_country = []
    for item in music_items:
        music_id = str(item.get("music_id"))
        per_country = []
        for unit in units:
            if unit["music_id"] == music_id and unit["formal_score"] is not None:
                per_country.append(unit["formal_score"])
        cross_country.append({
            "music_id": music_id,
            "title": item.get("title"),
            "countries_with_score": len(per_country),
            "cells_with_score": len(per_country),
            "cross_country_score": (
                round(statistics.fmean(per_country), 2)
                if len(per_country) >= cfg["cross_country_min_countries"]
                and sum(1 for unit in units if unit.get("formal_score") is not None) >= cfg["cross_country_min_cells"]
                else None
            ),
            "weighting": "each country equal; no sample-size weighting",
            "ready_for_ranking": False,
        })

    status_counts = {
        status: sum(1 for unit in units if unit["status"] == status)
        for status in (
            "not_started", "descriptive_only", "insufficient_sample", "variant_imbalance",
            "incomplete_measurement", "awaiting_evidence", "eligible_for_review",
        )
    }
    return {
        "sample": {"countries": len(countries), "music": len(music_items), "cells": len(units)},
        "config": cfg,
        "validation": validation,
        "eligible_rows": len(eligible),
        "defensive_duplicate_rows_excluded": duplicate_rows_excluded,
        "rehearsal_rows_excluded": rehearsal_excluded,
        "protocol_rows_excluded": protocol_excluded,
        "protocol_version": protocol_version,
        "units": units,
        "country_summary": country_summary,
        "cross_country": cross_country,
        "status_counts": status_counts,
        "formula": {
            "scale": "1—5 -> 0—100",
            "weights": cfg["weights"],
            "weights_note": "八项等权仅为建议；未审批前不得用于正式排名。",
            "score": "Σ(((mean_1_5_i - 1) / 4 × 100) × weight_i) + evidence_0_100 × weight_evidence",
            "existing_evidence": "必须来自经审批的 0—100 证据分；不得用受众评分替代。",
        },
        "formal_scoring_allowed": False,
        "ranking_allowed": False,
        "scope_note": "描述性聚合已完成；正式评分和排名未开放。缺少八项完整测量的单元保持 null。",
        "warnings": bundle.warnings,
    }


def import_batch(
    bundle: ResearchBundle,
    rows: list[dict[str, Any]],
    *,
    operator: str = "unknown",
    batch_label: str = "",
    protocol_version: str | None = None,
) -> dict[str, Any]:
    if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
        raise ValueError("rows 必须是对象数组")
    if len(rows) > 20000:
        raise ValueError("单次最多导入20000行")
    rows = [
        {
            **row,
            "dataset_kind": str(row.get("dataset_kind") or "formal"),
            "protocol_version": str(row.get("protocol_version") or protocol_version or "IRP-SIX-COUNTRY-2026-V1"),
        }
        for row in rows
    ]
    validation = validate_pilot_responses(bundle, rows)
    batch_id = f"PB-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"
    root = _root() / "batches" / batch_id
    raw_deid = [_deidentify(row) for row in rows]
    existing_ids: dict[str, str] = {}
    for batch in list_batches():
        for layer in ("clean.json", "rejected.json"):
            path = _root() / "batches" / batch["batch_id"] / layer
            if path.exists():
                for item in _read_json(path):
                    rid = str(item.get("response_id") or "")
                    if rid:
                        existing_ids[rid] = batch["batch_id"]
    conflicts = []
    seen_current: dict[str, int] = {}
    for index, row in enumerate(rows, start=2):
        rid = str(row.get("response_id") or "").strip()
        if not rid:
            continue
        if rid in seen_current:
            conflicts.append({"batch_id": batch_id, "response_id": rid, "source_batch_id": batch_id,
                              "row_number": index, "reason": "同一批次内重复"})
            validation.setdefault("errors", []).append({
                "row_number": index, "response_id": rid, "field": "response_id",
                "field_label": "反馈编号", "code": "duplicate_cross_batch",
                "message": "同一批次内反馈编号重复，已隔离",
            })
        elif rid in existing_ids:
            conflicts.append({"batch_id": batch_id, "response_id": rid, "source_batch_id": existing_ids[rid],
                              "row_number": index, "reason": "与候选/已审批批次冲突"})
            validation.setdefault("errors", []).append({
                "row_number": index, "response_id": rid, "field": "response_id",
                "field_label": "反馈编号", "code": "duplicate_cross_batch",
                "message": f"反馈编号已存在于批次 {existing_ids[rid]}，已隔离",
            })
        seen_current[rid] = index
    if conflicts:
        validation["status"] = "partial"
        summary = validation.setdefault("summary", {})
        summary["error_count"] = len(validation.get("errors") or [])
        summary["invalid_rows"] = len(rows) - len(_eligible_rows_from_validation(rows, validation))
    clean = _eligible_rows_from_validation(rows, validation)
    bad_rows = {int(item["row_number"]) for item in validation.get("errors") or []}
    rejected = [_deidentify(row) for index, row in enumerate(rows, start=2) if index in bad_rows]
    digest = hashlib.sha256(_canonical_rows(raw_deid).encode("utf-8")).hexdigest()
    _write_json(root / "raw_deidentified.json", raw_deid)
    _write_json(root / "clean.json", clean)
    _write_json(root / "rejected.json", rejected)
    with (root / "errors.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["row_number", "response_id", "field", "code", "message"])
        writer.writeheader()
        for item in validation.get("errors") or []:
            writer.writerow({key: item.get(key) for key in writer.fieldnames})
    with (root / "conflicts.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["batch_id", "response_id", "source_batch_id", "row_number", "reason"])
        writer.writeheader()
        writer.writerows(conflicts)
    metadata = {
        "batch_id": batch_id,
        "batch_label": batch_label or batch_id,
        "source_file": None,
        "file_digest": digest,
        "imported_at": _now(),
        "imported_by": operator or "unknown",
        "approval_status": "pending_approval",
        "approved_by": None,
        "approved_at": None,
        "rows_total": len(rows),
        "rows_clean": len(clean),
        "rows_rejected": len(rejected),
        "error_count": len(validation.get("errors") or []),
        "duplicate_conflicts": len(conflicts),
        "validation_status": validation.get("status"),
        "note": "原始层已去标识化；清洗层与拒绝层分开保存，不覆盖原始记录。",
    }
    _write_json(root / "metadata.json", metadata)
    return metadata


def list_batches() -> list[dict[str, Any]]:
    root = _root() / "batches"
    if not root.exists():
        return []
    result = []
    for path in sorted(root.glob("*/metadata.json")):
        result.append(_read_json(path))
    return sorted(result, key=lambda item: item.get("imported_at") or "", reverse=True)


def approve_batch(batch_id: str, approver: str) -> dict[str, Any]:
    path = _root() / "batches" / batch_id / "metadata.json"
    if not path.exists():
        raise FileNotFoundError(batch_id)
    metadata = _read_json(path)
    if metadata.get("approval_status") == "approved":
        return metadata
    if int(metadata.get("duplicate_conflicts") or 0) > 0:
        raise ValueError("批次存在重复反馈冲突，不能审批；请修复后重新导入")
    clean_path = _root() / "batches" / batch_id / "clean.json"
    current_ids = {str(row.get("response_id") or "") for row in (_read_json(clean_path) if clean_path.exists() else []) if row.get("response_id")}
    for other in list_batches():
        if other["batch_id"] == batch_id or other.get("approval_status") != "approved":
            continue
        other_path = _root() / "batches" / other["batch_id"] / "clean.json"
        if not other_path.exists():
            continue
        other_ids = {str(row.get("response_id") or "") for row in _read_json(other_path) if row.get("response_id")}
        conflict = current_ids & other_ids
        if conflict:
            raise ValueError(f"批次与已审批批次 {other['batch_id']} 存在重复反馈：{', '.join(sorted(conflict)[:5])}")
    metadata.update({"approval_status": "approved", "approved_by": approver, "approved_at": _now()})
    _write_json(path, metadata)
    return metadata


def approved_rows(batch_ids: list[str] | None = None) -> list[dict[str, Any]]:
    selected = set(batch_ids or [])
    rows = []
    for batch in list_batches():
        if batch.get("approval_status") != "approved":
            continue
        if selected and batch.get("batch_id") not in selected:
            continue
        path = _root() / "batches" / batch["batch_id"] / "clean.json"
        if path.exists():
            rows.extend(_read_json(path))
    return rows


def _approved_rows() -> list[dict[str, Any]]:
    return approved_rows()


def create_score_draft(
    bundle: ResearchBundle,
    *,
    title: str,
    created_by: str,
    batch_ids: list[str] | None = None,
    protocol_version: str | None = None,
) -> dict[str, Any]:
    batches = list_batches()
    if batch_ids:
        batches = [batch for batch in batches if batch.get("batch_id") in set(batch_ids)]
    approved = [batch for batch in batches if batch.get("approval_status") == "approved"]
    if not approved:
        raise ValueError("没有已审批的导入批次，不能生成评分草稿")
    rows = []
    for batch in approved:
        path = _root() / "batches" / batch["batch_id"] / "clean.json"
        if path.exists():
            rows.extend(_read_json(path))
    cfg = config()
    result = aggregate(bundle, rows, cfg, protocol_version)
    score_id = f"PS-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"
    payload = {
        "score_id": score_id,
        "title": title or "六国实测评分草稿",
        "status": "pending_approval",
        "created_at": _now(),
        "created_by": created_by or "unknown",
        "approved_by": None,
        "approved_at": None,
        "published_version": None,
        "published_at": None,
        "published_by": None,
        "revoked_at": None,
        "revoke_reason": None,
        "input_batches": [batch["batch_id"] for batch in approved],
        "formula": result["formula"],
        "config": cfg,
        "config_version": cfg.get("config_version"),
        "config_sha256": cfg.get("sha256"),
        "summary": result["status_counts"],
        "units": result["units"],
        "cross_country": result["cross_country"],
        "ranking_allowed": False,
        "history": [{"at": _now(), "action": "created", "by": created_by or "unknown"}],
        "note": "待审批草稿；没有写入 v1.7 正式数据。",
    }
    _write_json(_root() / "scores" / f"{score_id}.json", payload)
    return payload


def list_scores() -> list[dict[str, Any]]:
    root = _root() / "scores"
    if not root.exists():
        return []
    result = []
    for path in sorted(root.glob("*.json")):
        item = _read_json(path)
        result.append({
            "score_id": item.get("score_id"),
            "title": item.get("title"),
            "status": item.get("status"),
            "created_at": item.get("created_at"),
            "created_by": item.get("created_by"),
            "approved_by": item.get("approved_by"),
            "approved_at": item.get("approved_at"),
            "published_version": item.get("published_version"),
            "config_version": item.get("config_version"),
            "input_batches": item.get("input_batches"),
            "summary": item.get("summary"),
        })
    return sorted(result, key=lambda item: item.get("created_at") or "", reverse=True)


def get_score(score_id: str) -> dict[str, Any]:
    path = _root() / "scores" / f"{score_id}.json"
    if not path.exists():
        raise FileNotFoundError(score_id)
    return _read_json(path)


def approve_score(score_id: str, approver: str) -> dict[str, Any]:
    score = get_score(score_id)
    if score.get("status") in {"approved_candidate", "published"}:
        return score
    if score.get("status") != "pending_approval":
        raise ValueError("只有待审批评分可以审批")
    score.update({"status": "approved_candidate", "approved_by": approver, "approved_at": _now(), "ranking_allowed": False})
    score.setdefault("history", []).append({"at": _now(), "action": "approved", "by": approver})
    score["note"] = "已审批候选评分；未写入正式 v1.7，仍需单独发布审批。"
    _write_json(_root() / "scores" / f"{score_id}.json", score)
    return score


def revoke_score(score_id: str, approver: str, reason: str) -> dict[str, Any]:
    score = get_score(score_id)
    if score.get("status") == "published":
        raise ValueError("已发布版本必须通过撤销发布操作关闭")
    score.update({"status": "revoked", "revoked_at": _now(), "revoke_reason": reason, "ranking_allowed": False})
    score.setdefault("history", []).append({"at": _now(), "action": "revoked", "by": approver, "reason": reason})
    _write_json(_root() / "scores" / f"{score_id}.json", score)
    return score


def publish_score(score_id: str, publisher: str) -> dict[str, Any]:
    score = get_score(score_id)
    if score.get("status") != "approved_candidate":
        raise ValueError("只有已审批候选评分可以发布")
    cfg = config()
    if cfg.get("status") != "approved":
        raise ValueError("门槛配置尚未审批")
    if score.get("config_version") != cfg.get("config_version"):
        raise ValueError("评分草稿绑定的门槛版本不是当前已审批版本")
    complete_units = [unit for unit in score.get("units") or [] if unit.get("formal_score") is not None]
    if not complete_units:
        raise ValueError("没有八项完整的可发布单元")
    # 旧活动版本变为 superseded，不能继续进入排名。
    active_path = _root() / "published" / "active.json"
    if active_path.exists():
        old = _read_json(active_path)
        old_path = _root() / "published" / f"{old.get('version')}.json"
        if old_path.exists():
            old_doc = _read_json(old_path)
            old_doc["status"] = "superseded"
            old_doc.setdefault("history", []).append({"at": _now(), "action": "superseded", "by": publisher})
            _write_json(old_path, old_doc)
    version = f"PV-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"
    doc = {
        "version": version,
        "status": "published",
        "score_id": score_id,
        "published_by": publisher or "unknown",
        "published_at": _now(),
        "config_version": cfg.get("config_version"),
        "config_sha256": cfg.get("sha256"),
        "formula": score.get("formula"),
        "input_batches": score.get("input_batches") or [],
        "units": complete_units,
        "ranking_allowed": True,
        "history": [{"at": _now(), "action": "published", "by": publisher or "unknown"}],
    }
    _write_json(_root() / "published" / f"{version}.json", doc)
    _write_json(active_path, {"version": version, "score_id": score_id, "activated_at": _now()})
    score.update({"status": "published", "published_version": version, "published_at": _now(),
                  "published_by": publisher or "unknown", "ranking_allowed": True})
    score.setdefault("history", []).append({"at": _now(), "action": "published", "by": publisher or "unknown", "version": version})
    _write_json(_root() / "scores" / f"{score_id}.json", score)
    return doc


def revoke_published(version: str, actor: str, reason: str) -> dict[str, Any]:
    path = _root() / "published" / f"{version}.json"
    if not path.exists():
        raise FileNotFoundError(version)
    doc = _read_json(path)
    doc.update({"status": "revoked_published", "ranking_allowed": False, "revoked_at": _now(),
                "revoked_by": actor or "unknown", "revoke_reason": reason})
    doc.setdefault("history", []).append({"at": _now(), "action": "revoked_published", "by": actor or "unknown", "reason": reason})
    _write_json(path, doc)
    active_path = _root() / "published" / "active.json"
    if active_path.exists():
        active = _read_json(active_path)
        if active.get("version") == version:
            active_path.unlink()
    score_path = _root() / "scores" / f"{doc.get('score_id')}.json"
    if score_path.exists():
        score = _read_json(score_path)
        score.update({"status": "revoked_published", "ranking_allowed": False})
        score.setdefault("history", []).append({"at": _now(), "action": "published_revoked", "by": actor or "unknown", "reason": reason})
        _write_json(score_path, score)
    return doc


def active_published() -> dict[str, Any] | None:
    active_path = _root() / "published" / "active.json"
    if not active_path.exists():
        return None
    active = _read_json(active_path)
    path = _root() / "published" / f"{active.get('version')}.json"
    if not path.exists():
        return None
    doc = _read_json(path)
    return doc if doc.get("status") == "published" else None


def rankings() -> list[dict[str, Any]]:
    active_path = _root() / "published" / "active.json"
    if not active_path.exists():
        return []
    active = _read_json(active_path)
    path = _root() / "published" / f"{active.get('version')}.json"
    if not path.exists():
        return []
    doc = _read_json(path)
    if doc.get("status") != "published":
        return []
    seen = set()
    result = []
    for unit in doc.get("units") or []:
        if unit.get("formal_score") is None:
            continue
        key = (unit.get("country"), unit.get("music_id"))
        if key in seen:
            continue
        seen.add(key)
        result.append({
            "version": doc.get("version"),
            "score_id": doc.get("score_id"),
            "country": unit.get("country"),
            "music_id": unit.get("music_id"),
            "title": unit.get("title"),
            "formal_score": unit.get("formal_score"),
            "eight_complete": True,
            "published_by": doc.get("published_by"),
            "config_version": doc.get("config_version"),
        })
    return sorted(result, key=lambda item: item["formal_score"], reverse=True)
