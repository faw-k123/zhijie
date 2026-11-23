"""研究数据统计层。

所有“是否允许排行/是否允许下结论”的判断都在这里完成，前端不再自行计算。
当前 P1 数据只有 3 个案例，因此 sample.status=insufficient，排行榜返回 unavailable。
"""

from __future__ import annotations

import re
from collections import Counter
from datetime import datetime
from math import ceil
from typing import Any

from .research_data import INDICATOR_IDS, ResearchBundle

SAMPLE_THRESHOLDS = {"exploratory": 5, "descriptive": 20}
ANALYSIS_SAMPLES = {
    "all": "全部扩展案例",
    "strict_candidate": "严格样本候选（待审批）",
    "strict_individual": "正式严格样本（已批准）",
    "extended_cross_cultural": "扩展跨文化传播样本",
    "pending_review": "待核实案例",
}
MUSIC_KEYS = (
    "emotional_resonance",
    "timbre_identity",
    "melody_accessibility",
    "cultural_story",
    "adaptation_space",
    "visual_expressiveness",
    "era_theme_relevance",
    "existing_evidence",
)

ACCEPTANCE_MECHANISMS = {
    "M1": "情绪共鸣",
    "M2": "独特音色",
    "M3": "熟悉性桥梁",
    "M4": "文化叙事",
    "M5": "跨文化转译",
    "M6": "演奏者可信度",
    "M7": "视觉与表演性",
    "M8": "数字平台适配",
    "M9": "教育与参与转化",
}

MECHANISM_STATUS_LABELS = {
    "strong": "强证据",
    "partial": "部分证据",
    "not_evidenced": "未见证据",
}

OUTCOME_STATUS_LABELS = {
    "acceptance": "接受与认可",
    "engagement": "互动参与",
    "conversion": "学习或行动转化",
    "institutionalized": "机构化延续",
}

STRICT_ADMISSION_RULES = [
    {"code": "G1", "label": "个人身份", "requirement": "具名自然人，不以学校、乐团或机构代替个人身份"},
    {"code": "G2", "label": "非中国国籍", "requirement": "来源明确外国国籍，不从姓名、外貌或居住地推断"},
    {"code": "G3", "label": "中国音乐对象", "requirement": "明确中国传统乐器、传统曲目或以其为核心的跨文化改编"},
    {"code": "G4", "label": "实际演奏", "requirement": "演出后报道、录像、档案或持续履历确认实际演奏"},
    {"code": "G5", "label": "传播场景", "requirement": "中国境外现场或面向跨国受众的公开数字传播"},
    {"code": "G6", "label": "可追溯来源", "requirement": "至少两条可共同覆盖身份、乐器和演奏事实的独立来源"},
]

PILOT_RESPONSE_FIELDS = [
    {"key": "response_id", "label": "反馈编号", "required": True, "rule": "去标识化唯一编号"},
    {"key": "country", "label": "测试国家", "required": True, "rule": "日本/泰国/英国/美国/阿联酋/巴西"},
    {"key": "music_id", "label": "曲目编号", "required": True, "rule": "MU001—MU020"},
    {"key": "variant", "label": "版本", "required": True, "rule": "original/adapted；随机呈现"},
    {"key": "prior_exposure", "label": "既往接触", "required": True, "rule": "none/limited/familiar"},
    {"key": "completion_rate", "label": "完整观看率", "required": True, "rule": "0—100"},
    {"key": "emotional_resonance", "label": "情绪共鸣", "required": True, "rule": "1—5"},
    {"key": "timbre_identity", "label": "音色辨识", "required": True, "rule": "1—5"},
    {"key": "melody_accessibility", "label": "旋律可进入性", "required": True, "rule": "1—5"},
    {"key": "cultural_understanding", "label": "文化理解", "required": True, "rule": "1—5并附开放回答"},
    {"key": "cultural_story", "label": "文化故事性", "required": True, "rule": "1—5；对故事/背景可理解性的直接评分"},
    {"key": "adaptation_space", "label": "跨文化改编空间", "required": True, "rule": "1—5；对改编自然度/空间判断的直接评分"},
    {"key": "visual_expressiveness", "label": "视觉表现力", "required": True, "rule": "1—5；仅针对提供的视觉呈现直接评分"},
    {"key": "era_theme_relevance", "label": "时代主题相关性", "required": True, "rule": "1—5；仅针对明确主题框架直接评分"},
    {"key": "save_share_intent", "label": "收藏分享意愿", "required": True, "rule": "1—5，辅助指标，不替代八项"},
    {"key": "learning_intent", "label": "学习参与意愿", "required": True, "rule": "1—5，辅助指标，不替代八项"},
    {"key": "open_response", "label": "开放回答", "required": True, "rule": "记录喜欢、不理解及文化联想"},
    {"key": "cultural_risk_flag", "label": "文化风险标记", "required": False, "rule": "宗教、刻板印象、误读或不适"},
    {"key": "consent", "label": "研究同意", "required": True, "rule": "yes后方可纳入"},
    {"key": "collected_at", "label": "采集时间", "required": True, "rule": "ISO日期时间"},
    {"key": "protocol_version", "label": "协议版本", "required": False, "rule": "正式数据默认当前冻结协议"},
    {"key": "dataset_kind", "label": "数据用途", "required": False, "rule": "formal/pilot_rehearsal/demo；试运行不进入正式聚合"},
]

PILOT_RATING_FIELDS = (
    "emotional_resonance",
    "timbre_identity",
    "melody_accessibility",
    "cultural_understanding",
    "cultural_story",
    "adaptation_space",
    "visual_expressiveness",
    "era_theme_relevance",
    "save_share_intent",
    "learning_intent",
)


class CaseNotFound(Exception):
    pass


def eligible_cases(bundle: ResearchBundle) -> list[dict[str, Any]]:
    return [
        case
        for case in bundle.cases
        if case.get("review_status") in {"A", "B"} and case.get("display_allowed") is True
    ]


def filter_by_analysis_sample(cases: list[dict[str, Any]], analysis_sample: str) -> list[dict[str, Any]]:
    """按案例分析样本过滤；不改变原始案例、评分或来源。"""
    if analysis_sample == "all":
        return list(cases)
    if analysis_sample == "strict_candidate":
        return [case for case in cases if case.get("analysis_sample") == "strict_individual"]
    if analysis_sample == "strict_individual":
        return [
            case for case in cases
            if case.get("analysis_sample") == "strict_individual"
            and case.get("owner_approval_status") == "approved"
        ]
    return [case for case in cases if case.get("analysis_sample") == analysis_sample]


def build_analysis_scope(
    bundle: ResearchBundle,
    cases: list[dict[str, Any]],
    analysis_sample: str,
) -> dict[str, Any]:
    case_ids = {case.get("case_id") for case in cases}
    valid_score_count = 0
    scored_cases: set[str] = set()
    for score in bundle.scores:
        if score.get("case_id") in case_ids and score.get("score") is not None:
            valid_score_count += 1
            scored_cases.add(str(score.get("case_id")))
    display_cases = eligible_cases(bundle)
    strict_candidates = [
        case for case in display_cases
        if case.get("analysis_sample") == "strict_individual"
    ]
    approved_strict = [
        case for case in strict_candidates
        if case.get("owner_approval_status") == "approved"
    ]
    status_counts = Counter(str(case.get("owner_approval_status")) for case in strict_candidates)
    return {
        "key": analysis_sample,
        "label": ANALYSIS_SAMPLES.get(analysis_sample, analysis_sample),
        "case_count": len(cases),
        "scored_case_count": len(scored_cases),
        "valid_score_count": valid_score_count,
        "strict_candidate_count": len(strict_candidates),
        "owner_approved_count": len(approved_strict),
        "strict_approved_case_count": len(approved_strict),
        "pending_owner_review_count": status_counts.get("pending_owner_review", 0),
        "rejected_count": status_counts.get("rejected", 0),
        "needs_more_evidence_count": status_counts.get("needs_more_evidence", 0),
        "thresholds": SAMPLE_THRESHOLDS,
    }


def sample_status(n: int) -> str:
    if n <= 0:
        return "empty"
    if n < 5:
        return "insufficient"
    if n < 20:
        return "exploratory"
    return "descriptive"


def sample_label(status: str) -> str:
    return {
        "empty": "暂无已审核案例",
        "insufficient": "证据不足：样本少于5例",
        "exploratory": "探索性观察：5—19例，不作普遍性推断",
        "descriptive": "描述性统计：20例及以上，仍不作因果推断",
    }.get(status, "样本状态未知")


def build_sample(bundle: ResearchBundle, cases: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    cases = eligible_cases(bundle) if cases is None else cases
    n = len(cases)
    target = bundle.target_case_count
    status = sample_status(n)
    return {
        "n": n,
        "target": target,
        "status": status,
        "label": sample_label(status),
        "progress_percent": round((n / target) * 100, 1) if target else 0.0,
        "thresholds": SAMPLE_THRESHOLDS,
    }


def _scores_for(bundle: ResearchBundle, case_id: str) -> list[dict[str, Any]]:
    return [score for score in bundle.scores if score.get("case_id") == case_id]


def score_summary(bundle: ResearchBundle, case_id: str) -> dict[str, Any]:
    records = _scores_for(bundle, case_id)
    valid = [r for r in records if r.get("score") is not None]
    missing = [r for r in records if r.get("score") is None]
    mean = round(sum(int(r["score"]) for r in valid) / len(valid), 2) if valid else None
    source_ids: list[str] = []
    for r in records:
        for source_id in r.get("source_ids") or []:
            if source_id not in source_ids:
                source_ids.append(source_id)
    return {
        "mean_score": mean,
        "score_scale": 3,
        "valid_count": len(valid),
        "missing_count": len(missing),
        "low_coverage": len(valid) < 6,
        "source_ids": source_ids,
    }


def _case_summary(bundle: ResearchBundle, case: dict[str, Any]) -> dict[str, Any]:
    source_links = [
        {
            "source_id": source.get("source_id"),
            "title": source.get("title"),
            "publisher": source.get("publisher"),
            "url": source.get("url"),
        }
        for source in (case.get("sources") or [])
        if isinstance(source, dict) and source.get("url")
    ]
    summary = {
        "case_id": case.get("case_id"),
        "performer": case.get("performer"),
        "performer_type": case.get("performer_type"),
        "country": case.get("country"),
        "region": case.get("region"),
        "subregion": case.get("subregion"),
        "instrument": case.get("instrument") or [],
        "work": case.get("work"),
        "music_type": case.get("music_type"),
        "event_date_text": case.get("event_date_text"),
        "channel": case.get("channel") or [],
        "target_audience": case.get("target_audience") or [],
        "era_theme": case.get("era_theme") or [],
        "review_status": case.get("review_status"),
        "source_count": case.get("source_count") or 0,
        "source_ids": case.get("source_ids") or [],
        "source_links": source_links,
        "cover_url": case.get("cover_url"),
        "summary": case.get("summary"),
        "cultural_hooks": case.get("cultural_hooks") or [],
        "case_type": case.get("case_type"),
        "analysis_sample": case.get("analysis_sample"),
        "performer_identity_status": case.get("performer_identity_status"),
        "performance_location": case.get("performance_location"),
        "overseas_activity": case.get("overseas_activity"),
        "strict_sample_eligible": case.get("strict_sample_eligible"),
        "owner_approval_status": case.get("owner_approval_status"),
        "eligibility_reason": case.get("eligibility_reason"),
        "evidence_limitations": case.get("evidence_limitations") or [],
    }
    summary.update(score_summary(bundle, str(case.get("case_id"))))
    return summary


def build_status(bundle: ResearchBundle) -> dict[str, Any]:
    cases = eligible_cases(bundle)
    source_count = sum(len(case.get("sources") or []) for case in cases)
    countries = sorted({str(case.get("country")) for case in cases if case.get("country")})
    instruments = sorted({str(item) for case in cases for item in (case.get("instrument") or [])})
    grade_counts = Counter(str(case.get("review_status")) for case in bundle.cases)
    analysis_sample_counts = Counter(str(case.get("analysis_sample")) for case in cases)
    approved_case_count = sum(
        1 for case in cases if case.get("owner_approval_status") == "approved"
    )
    strict_reviewed_count = sum(
        1
        for case in cases
        if case.get("analysis_sample") == "strict_individual"
        and case.get("owner_approval_status") == "approved"
    )
    return {
        "sample": build_sample(bundle),
        "version": {
            "active_version": bundle.version,
            "status": bundle.version_meta.get("status"),
            "updated_at": bundle.manifest.get("updated_at"),
            "created_at": bundle.version_meta.get("created_at"),
        },
        "counts": {
            "cases": len(cases),
            "approved": approved_case_count,
            "strict_reviewed": strict_reviewed_count,
            "extended_reference": analysis_sample_counts.get("extended_cross_cultural", 0),
            "pending_review": analysis_sample_counts.get("pending_review", 0),
            "sources": source_count,
            "countries": len(countries),
            "instruments": len(instruments),
        },
        "countries": countries,
        "instruments": instruments,
        "grade_counts": {grade: grade_counts.get(grade, 0) for grade in ("A", "B", "C", "D")},
        "warnings": bundle.warnings,
    }


def build_statistics(bundle: ResearchBundle, analysis_sample: str = "all") -> dict[str, Any]:
    all_cases = eligible_cases(bundle)
    cases = filter_by_analysis_sample(all_cases, analysis_sample)
    sample = build_sample(bundle, cases)
    scope = build_analysis_scope(bundle, cases, analysis_sample)

    def distribution(field: str, multi: bool = False) -> list[dict[str, Any]]:
        counter: Counter[str] = Counter()
        for case in cases:
            value = case.get(field)
            values = value if multi and isinstance(value, list) else [value]
            for item in values:
                if item:
                    counter[str(item)] += 1
        return [
            {"key": key, "count": count}
            for key, count in sorted(counter.items(), key=lambda item: (-item[1], item[0]))
        ]

    eligible_ids = {c.get("case_id") for c in cases}
    scores_by_indicator: dict[str, list[dict[str, Any]]] = {indicator_id: [] for indicator_id in INDICATOR_IDS}
    for score in bundle.scores:
        indicator_id = score.get("indicator_id")
        if indicator_id in scores_by_indicator and score.get("case_id") in eligible_ids:
            scores_by_indicator[indicator_id].append(score)

    indicator_coverage = []
    labels = {
        item.get("indicator_id"): item.get("label_zh")
        for item in bundle.success_doc.get("indicators") or []
    }
    for indicator_id in INDICATOR_IDS:
        records = scores_by_indicator[indicator_id]
        valid = [r for r in records if r.get("score") is not None]
        indicator_coverage.append({
            "indicator_id": indicator_id,
            "label": labels.get(indicator_id, indicator_id),
            "valid_count": len(valid),
            "missing_count": len(cases) - len(valid),
            "coverage_rate": round(len(valid) / len(cases), 4) if cases else 0.0,
        })

    # 国家—因素对应分析：保留全球总体排行不变，另按每个国家的已审批案例
    # 计算可用指标均值前三项。小样本明确标为探索性，不做国家总体推断。
    country_factor_correspondence = []
    for country_row in distribution("country"):
        country = country_row["key"]
        country_case_ids = {
            case.get("case_id") for case in cases if str(case.get("country") or "") == country
        }
        top_factors = []
        for indicator_id in INDICATOR_IDS:
            valid = [
                score for score in scores_by_indicator[indicator_id]
                if score.get("case_id") in country_case_ids and score.get("score") is not None
            ]
            if not valid:
                continue
            top_factors.append({
                "indicator_id": indicator_id,
                "label": labels.get(indicator_id, indicator_id),
                "mean_score": round(sum(int(item["score"]) for item in valid) / len(valid), 2),
                "n": len(valid),
                "missing_count": len(country_case_ids) - len(valid),
            })
        top_factors.sort(key=lambda item: (-item["mean_score"], INDICATOR_IDS.index(item["indicator_id"])))
        country_factor_correspondence.append({
            "country": country,
            "case_count": len(country_case_ids),
            "analysis_status": sample_status(len(country_case_ids)),
            "top_factors": top_factors[:3],
            "note": "案例内描述性对应关系，不代表该国总体偏好。",
        })

    return {
        "sample": sample,
        "distributions": {
            "country": distribution("country"),
            "region": distribution("region"),
            "instrument": distribution("instrument", multi=True),
            "channel": distribution("channel", multi=True),
            "theme": distribution("era_theme", multi=True),
            "evidence_grade": distribution("review_status"),
        },
        "indicator_coverage": indicator_coverage,
        "country_factor_correspondence": country_factor_correspondence,
        "analysis_scope": scope,
        "rankings_allowed": sample["n"] >= SAMPLE_THRESHOLDS["descriptive"],
        "success_factors_available": sample["n"] >= SAMPLE_THRESHOLDS["exploratory"],
        "indicator_rank_min": SAMPLE_THRESHOLDS["descriptive"],
        "warnings": bundle.warnings,
    }


def indicator_gate(n: int) -> dict[str, Any]:
    """指标级样本门禁：n=0 / 1—4 / 5—19 / ≥20。"""
    if n <= 0:
        return {
            "status": "empty",
            "status_label": "暂无数据",
            "ranking_allowed": False,
            "gate_note": "该指标尚无任何有效评分，不展示均值、不参与排序。",
        }
    if n < 5:
        return {
            "status": "insufficient",
            "status_label": "证据不足",
            "ranking_allowed": False,
            "gate_note": "有效评分少于5例，不参与排行榜；仅可作为单案例记录。",
        }
    if n < 20:
        return {
            "status": "exploratory",
            "status_label": "探索性",
            "ranking_allowed": False,
            "gate_note": "有效评分5—19例，可作探索性展示；必须同时显示样本量和缺失量，不排序。",
        }
    return {
        "status": "descriptive",
        "status_label": "描述性",
        "ranking_allowed": True,
        "gate_note": "有效评分不少于20例，可做描述性排序；仍不代表因果结论。",
    }


def build_success_factors(
    bundle: ResearchBundle,
    analysis_sample: str = "all",
    country: str = "",
) -> dict[str, Any]:
    all_cases = eligible_cases(bundle)
    cases = filter_by_analysis_sample(all_cases, analysis_sample)
    country = str(country or "").strip()
    if country:
        cases = [case for case in cases if str(case.get("country") or "") == country]
    sample = build_sample(bundle, cases)
    scope = build_analysis_scope(bundle, cases, analysis_sample)
    scope["country"] = country or None
    if country:
        scope["label"] = f"{country}已审批案例"
    case_ids = {c.get("case_id") for c in cases}
    labels = {
        item.get("indicator_id"): item.get("label_zh")
        for item in bundle.success_doc.get("indicators") or []
    }
    orders = {
        item.get("indicator_id"): item.get("order")
        for item in bundle.success_doc.get("indicators") or []
    }

    records_by_indicator: dict[str, list[dict[str, Any]]] = {indicator_id: [] for indicator_id in INDICATOR_IDS}
    for score in bundle.scores:
        if score.get("case_id") in case_ids:
            indicator_id = score.get("indicator_id")
            if indicator_id in records_by_indicator:
                records_by_indicator[indicator_id].append(score)

    factors = []
    for indicator_id in INDICATOR_IDS:
        records = records_by_indicator[indicator_id]
        valid = [r for r in records if r.get("score") is not None]
        mean = round(sum(int(r["score"]) for r in valid) / len(valid), 2) if valid else None
        factor = {
            "indicator_id": indicator_id,
            "label": labels.get(indicator_id, indicator_id),
            "order": orders.get(indicator_id),
            "n": len(valid),
            "missing_count": len(cases) - len(valid),
            "coverage_rate": round(len(valid) / len(cases), 4) if cases else 0.0,
            "mean_score": mean,
            "score_scale": 3,
        }
        factor.update(indicator_gate(len(valid)))
        factors.append(factor)

    if sample["n"] < SAMPLE_THRESHOLDS["exploratory"]:
        availability = "unavailable"
        reason = "整体样本不足5例，统计层不提供成功因素排行；指标级门禁仍列出覆盖情况。"
        rankings = None
    elif sample["n"] < SAMPLE_THRESHOLDS["descriptive"]:
        availability = "exploratory"
        reason = (
            "整体样本为探索性（5—19例）；仅展示指标覆盖与均值，不生成排行榜。"
            "只有单个指标有效评分达到20例，才允许描述性排序。"
        )
        rankings = []
    else:
        availability = "descriptive"
        reason = None
        rankings = sorted(
            [f for f in factors if f["ranking_allowed"] and f["mean_score"] is not None],
            key=lambda f: (-f["mean_score"], f["order"] or 999),
        )
        for rank, factor in enumerate(rankings, start=1):
            factor["rank"] = rank

    for factor in factors:
        factor.setdefault("rank", None)

    gate_counts = {status: 0 for status in ("empty", "insufficient", "exploratory", "descriptive")}
    for factor in factors:
        gate_counts[factor["status"]] += 1

    return {
        "sample": sample,
        "analysis_scope": scope,
        "availability": availability,
        "rankings": rankings,
        "factors": factors,
        "reason": reason,
        "thresholds": {
            **SAMPLE_THRESHOLDS,
            "indicator_exploratory_min": SAMPLE_THRESHOLDS["exploratory"],
            "indicator_rank_min": SAMPLE_THRESHOLDS["descriptive"],
        },
        "gate_counts": gate_counts,
        "warnings": bundle.warnings,
    }

def _tier_for_score(score: float, tiers: list[dict[str, Any]]) -> str:
    for tier in tiers:
        if float(tier.get("min", 0)) <= score <= float(tier.get("max", 100)):
            return str(tier.get("label"))
    return "未分级"


def _music_total(score_map: dict[str, Any], weights: dict[str, Any]) -> float | None:
    if any(score_map.get(key) is None for key in MUSIC_KEYS):
        return None
    try:
        total = sum(float(score_map[key]) * float(weights[key]) for key in MUSIC_KEYS)
    except (TypeError, ValueError, KeyError):
        return None
    return round(total, 1)


def build_music_potential(bundle: ResearchBundle) -> dict[str, Any]:
    sample = build_sample(bundle)
    doc = bundle.music_doc
    status = doc.get("status") or "pending"
    items = doc.get("items") or []
    scored = [item for item in items if _music_total(item.get("scores") or {}, doc.get("weights") or {}) is not None]
    music_sample_status = sample_status(len(scored))
    result = {
        "sample": sample,
        "availability": "pending" if status == "pending" else ("partial" if status == "partial" else "available"),
        "status": status,
        "status_label": doc.get("status_label"),
        "note": doc.get("note"),
        "music_sample": {
            "n": len(scored),
            "target": int(doc.get("target_count") or 20),
            "status": music_sample_status,
        },
        "weights": doc.get("weights") or {},
        "tiers": doc.get("tiers") or [],
        "items": [],
        "rankings": None,
        "warnings": bundle.warnings,
    }
    if status == "pending" or not items:
        return result
    enriched = []
    for item in items:
        total = _music_total(item.get("scores") or {}, doc.get("weights") or {})
        entry = dict(item)
        entry["total_score"] = total
        entry["tier"] = _tier_for_score(total, doc.get("tiers") or []) if total is not None else "资料不足"
        enriched.append(entry)
    result["items"] = enriched
    if status == "complete" and scored:
        result["rankings"] = sorted(
            [item for item in enriched if item["total_score"] is not None],
            key=lambda item: (-item["total_score"], str(item.get("music_id") or "")),
        )
        for rank, item in enumerate(result["rankings"], start=1):
            item["rank"] = rank
    return result


def build_regional_matrix(bundle: ResearchBundle) -> dict[str, Any]:
    sample = build_sample(bundle)
    doc = bundle.regional_doc
    status = doc.get("status") or "pending"
    rows = doc.get("rows") or []
    return {
        "sample": sample,
        "availability": "pending" if status == "pending" else ("partial" if status == "partial" else "available"),
        "status": status,
        "status_label": doc.get("status_label"),
        "note": doc.get("note"),
        "regions": doc.get("regions") or [],
        "audiences": doc.get("audiences") or [],
        "themes": doc.get("themes") or [],
        "rows": [] if status == "pending" else rows,
        "matrix": None if status == "pending" or not rows else rows,
        "independent_of_case_sample": True,
        "scope_note": "区域矩阵是独立的研究框架，不随案例样本筛选变化；当前 rows=0。",
        "warnings": bundle.warnings,
    }


def build_teacher_revision_outcomes(bundle: ResearchBundle) -> dict[str, Any]:
    """汇总教师意见专项成果，供前端按案例—机制—曲目—国家连续查看。"""
    strict_cases = [
        case for case in eligible_cases(bundle)
        if case.get("analysis_sample") == "strict_individual"
        and case.get("owner_approval_status") == "approved"
    ]
    strict_cases.sort(key=lambda case: str(case.get("case_id") or ""))

    aggregate = {
        code: {
            "code": code,
            "label": label,
            "strong": 0,
            "partial": 0,
            "not_evidenced": 0,
            "total": len(strict_cases),
        }
        for code, label in ACCEPTANCE_MECHANISMS.items()
    }
    case_results = []
    feedback_total = 0
    coding_eligible_total = 0

    for case in strict_cases:
        mechanism_values = case.get("acceptance_mechanism_codes") or {}
        mechanisms = []
        for code, label in ACCEPTANCE_MECHANISMS.items():
            value = mechanism_values.get(code, "not_evidenced")
            if value not in MECHANISM_STATUS_LABELS:
                value = "not_evidenced"
            aggregate[code][value] += 1
            mechanisms.append({
                "code": code,
                "label": label,
                "status": value,
                "status_label": MECHANISM_STATUS_LABELS[value],
            })

        feedback_ids = set(case.get("audience_feedback_ids") or [])
        feedback = []
        for source in case.get("sources") or []:
            if source.get("source_id") not in feedback_ids:
                continue
            coding_eligible = bool(source.get("coding_eligible", True))
            feedback.append({
                "feedback_id": source.get("source_id"),
                "evidence_type": source.get("feedback_evidence_type") or source.get("source_type"),
                "evidence_grade": source.get("feedback_grade") or source.get("reliability"),
                "country_basis": source.get("feedback_country_basis") or "来源页面所示海外语境",
                "language": source.get("feedback_language"),
                "valence": source.get("feedback_valence"),
                "excerpt": source.get("citation"),
                "summary": source.get("supports"),
                "limitations": source.get("notes"),
                "mechanism_codes": source.get("mechanism_codes") or [],
                "coding_eligible": coding_eligible,
                "source_url": source.get("url"),
                "publisher": source.get("publisher"),
            })
            feedback_total += 1
            if coding_eligible:
                coding_eligible_total += 1

        case_results.append({
            "case_id": case.get("case_id"),
            "performer": case.get("performer"),
            "country": case.get("country"),
            "region": case.get("region"),
            "instrument": case.get("instrument") or [],
            "work": case.get("work"),
            "summary": case.get("summary"),
            "outcome_status": case.get("outcome_evidence_status"),
            "outcome_label": OUTCOME_STATUS_LABELS.get(
                case.get("outcome_evidence_status"), "结果证据待解释"
            ),
            "mechanism_confidence": case.get("acceptance_mechanism_confidence"),
            "mechanisms": mechanisms,
            "feedback": feedback,
            "evidence_limitations": case.get("evidence_limitations") or [],
            "admission_audit": [
                {"code": "G1", "passed": bool(case.get("performer")), "evidence": case.get("performer")},
                {"code": "G2", "passed": case.get("country") not in {None, "", "中国"}, "evidence": case.get("country")},
                {"code": "G3", "passed": bool(case.get("instrument") or case.get("music_type")), "evidence": "、".join(case.get("instrument") or []) or case.get("music_type")},
                {"code": "G4", "passed": case.get("strict_sample_eligible") is True, "evidence": case.get("event_date_text") or case.get("success_evidence")},
                {"code": "G5", "passed": case.get("overseas_activity") is True, "evidence": case.get("venue") or case.get("performance_location")},
                {"code": "G6", "passed": len(case.get("owner_approval_source_ids") or []) >= 2, "evidence": f"{len(case.get('owner_approval_source_ids') or [])}条准入来源"},
            ],
            "source_count": len(case.get("source_ids") or []),
            "owner_approval_status": case.get("owner_approval_status"),
        })

    music_doc = bundle.music_doc
    music_items = []
    for item in music_doc.get("items") or []:
        if item.get("display_allowed") is not True:
            continue
        scores = item.get("scores") or {}
        total = _music_total(scores, music_doc.get("weights") or {})
        music_items.append({
            **item,
            "total_score": total,
            "score_status": "scored" if total is not None else "awaiting_six_country_pilot",
            "score_status_label": "已评分" if total is not None else "待六国实测",
        })

    country_rows = []
    for row in bundle.regional_doc.get("rows") or []:
        if row.get("display_allowed") is not True:
            continue
        priority = set(row.get("priority_music_ids") or [])
        secondary = set(row.get("secondary_music_ids") or [])
        context_required = set(row.get("context_required_music_ids") or [])
        fits = {}
        for music in music_items:
            music_id = music.get("music_id")
            if music_id in priority:
                fits[music_id] = "A"
            elif music_id in secondary:
                fits[music_id] = "B"
            elif music_id in context_required:
                fits[music_id] = "C"
            else:
                fits[music_id] = "待核验"
        country_rows.append({**row, "fits": fits})

    matrix = [
        {
            "music_id": music.get("music_id"),
            "title": music.get("title"),
            "selection_tier": music.get("selection_tier"),
            "countries": {
                row.get("country"): row.get("fits", {}).get(music.get("music_id"), "待核验")
                for row in country_rows
            },
        }
        for music in music_items
    ]

    return {
        "sample": build_sample(bundle, strict_cases),
        "status": "approved",
        "status_label": "教师意见专项成果已审批",
        "counts": {
            "strict_cases": len(case_results),
            "feedback": feedback_total,
            "coding_eligible_feedback": coding_eligible_total,
            "mechanisms": len(ACCEPTANCE_MECHANISMS),
            "music_candidates": len(music_items),
            "countries": len(country_rows),
            "matrix_cells": len(music_items) * len(country_rows),
        },
        "cases": case_results,
        "mechanisms": list(aggregate.values()),
        "admission_rules": STRICT_ADMISSION_RULES,
        "music": {
            "status": music_doc.get("status"),
            "status_label": music_doc.get("status_label"),
            "note": music_doc.get("note"),
            "items": music_items,
        },
        "countries": country_rows,
        "matrix": matrix,
        "pilot": {
            "status": "not_started",
            "status_label": "方案就绪，真实测试尚未开始",
            "design_principles": [
                "每首曲目比较原版与适配版，版本顺序随机，避免顺序效应",
                "记录既往中国音乐接触，避免把熟悉度误当成曲目效果",
                "六国使用同一核心量表，开放问题和文化风险项由当地顾问审校",
                "只有获得研究同意且字段完整的反馈才能进入评分",
                "先报告国家内结果，再讨论跨国共性；不由国籍推断个人宗教或偏好",
            ],
            "response_fields": PILOT_RESPONSE_FIELDS,
            "planned_cells": len(music_items) * len(country_rows),
            "completed_cells": 0,
        },
        "scope_note": "案例、反馈和机制编码用于探索接受机制；六国A/B/C为试验优先级，不代表国家总体偏好；八项音乐评分须在真实测试后填写。",
        "warnings": bundle.warnings,
    }


def validate_pilot_responses(bundle: ResearchBundle, rows: list[dict[str, Any]]) -> dict[str, Any]:
    """校验六国受众反馈；仅返回质量报告，不写入版本数据或生成正式评分。"""
    countries = [
        str(row.get("country")) for row in (bundle.regional_doc.get("rows") or [])
        if row.get("display_allowed") is True and row.get("country")
    ]
    music_items = [
        item for item in (bundle.music_doc.get("items") or [])
        if item.get("display_allowed") is True
    ]
    music_ids = {str(item.get("music_id")) for item in music_items}
    field_labels = {field["key"]: field["label"] for field in PILOT_RESPONSE_FIELDS}
    required_fields = [field["key"] for field in PILOT_RESPONSE_FIELDS if field["required"]]
    response_ids = [str(row.get("response_id") or "").strip() for row in rows]
    duplicate_ids = {key for key, count in Counter(response_ids).items() if key and count > 1}
    errors: list[dict[str, Any]] = []
    eligible_rows: list[dict[str, Any]] = []

    def add_error(row_number: int, response_id: str, field: str, code: str, message: str) -> None:
        errors.append({
            "row_number": row_number,
            "response_id": response_id or None,
            "field": field,
            "field_label": field_labels.get(field, field),
            "code": code,
            "message": message,
        })

    for index, raw in enumerate(rows, start=2):
        row = {str(key).strip(): value for key, value in raw.items()}
        response_id = str(row.get("response_id") or "").strip()
        before = len(errors)
        for field in required_fields:
            if str(row.get(field) if row.get(field) is not None else "").strip() == "":
                add_error(index, response_id, field, "required", f"{field_labels[field]}为必填项")

        if response_id in duplicate_ids:
            add_error(index, response_id, "response_id", "duplicate", "反馈编号重复")
        country = str(row.get("country") or "").strip()
        if country and country not in countries:
            add_error(index, response_id, "country", "invalid_choice", "国家不在本轮六国范围内")
        music_id = str(row.get("music_id") or "").strip()
        if music_id and music_id not in music_ids:
            add_error(index, response_id, "music_id", "invalid_choice", "曲目编号不在MU001—MU020范围内")
        variant = str(row.get("variant") or "").strip().lower()
        if variant and variant not in {"original", "adapted"}:
            add_error(index, response_id, "variant", "invalid_choice", "版本只能是original或adapted")
        exposure = str(row.get("prior_exposure") or "").strip().lower()
        if exposure and exposure not in {"none", "limited", "familiar"}:
            add_error(index, response_id, "prior_exposure", "invalid_choice", "既往接触只能是none/limited/familiar")
        consent = str(row.get("consent") or "").strip().lower()
        if consent and consent != "yes":
            add_error(index, response_id, "consent", "not_consented", "只有consent=yes的反馈可纳入")

        completion_raw = str(row.get("completion_rate") if row.get("completion_rate") is not None else "").strip()
        if completion_raw:
            try:
                completion = float(completion_raw)
                if not 0 <= completion <= 100:
                    raise ValueError
            except ValueError:
                add_error(index, response_id, "completion_rate", "out_of_range", "完整观看率应为0—100")

        for field in PILOT_RATING_FIELDS:
            raw_value = str(row.get(field) if row.get(field) is not None else "").strip()
            if not raw_value:
                continue
            try:
                value = float(raw_value)
                if not 1 <= value <= 5:
                    raise ValueError
            except ValueError:
                add_error(index, response_id, field, "out_of_range", f"{field_labels[field]}应为1—5")

        collected_at = str(row.get("collected_at") or "").strip()
        if collected_at:
            try:
                datetime.fromisoformat(collected_at.replace("Z", "+00:00"))
            except ValueError:
                add_error(index, response_id, "collected_at", "invalid_datetime", "采集时间应为ISO日期时间")

        dataset_kind = str(row.get("dataset_kind") or "formal").strip()
        if dataset_kind not in {"formal", "pilot_rehearsal", "demo"}:
            add_error(index, response_id, "dataset_kind", "invalid_choice", "数据用途只能是formal/pilot_rehearsal/demo")
        protocol_version = str(row.get("protocol_version") or "").strip()

        if len(errors) == before:
            eligible_rows.append({
                **row,
                "response_id": response_id,
                "country": country,
                "music_id": music_id,
                "variant": variant,
            })

    coverage_map: dict[tuple[str, str], dict[str, int]] = {
        (country, music_id): {"original": 0, "adapted": 0}
        for country in countries for music_id in sorted(music_ids)
    }
    for row in eligible_rows:
        key = (row["country"], row["music_id"])
        if key in coverage_map:
            coverage_map[key][row["variant"]] += 1
    coverage = [
        {
            "country": country,
            "music_id": music_id,
            "original_n": counts["original"],
            "adapted_n": counts["adapted"],
            "has_both_variants": counts["original"] > 0 and counts["adapted"] > 0,
        }
        for (country, music_id), counts in coverage_map.items()
    ]
    observed_cells = sum(1 for item in coverage if item["original_n"] + item["adapted_n"] > 0)
    balanced_cells = sum(1 for item in coverage if item["has_both_variants"])
    descriptive_metrics = []
    for field in PILOT_RATING_FIELDS:
        values = [
            float(row[field]) for row in eligible_rows
            if str(row.get(field) if row.get(field) is not None else "").strip()
        ]
        descriptive_metrics.append({
            "key": field,
            "label": field_labels[field],
            "n": len(values),
            "mean_1_5": round(sum(values) / len(values), 2) if values else None,
        })

    return {
        "sample": build_sample(bundle),
        "status": "valid" if rows and not errors else ("partial" if eligible_rows else "invalid"),
        "summary": {
            "total_rows": len(rows),
            "eligible_rows": len(eligible_rows),
            "invalid_rows": len(rows) - len(eligible_rows),
            "error_count": len(errors),
            "duplicate_response_ids": len(duplicate_ids),
            "planned_cells": len(coverage),
            "observed_cells": observed_cells,
            "balanced_cells": balanced_cells,
        },
        "errors": errors,
        "coverage": coverage,
        "descriptive_metrics": descriptive_metrics,
        "formal_scoring_allowed": False,
        "scope_note": "本接口只做格式、同意和覆盖校验；描述性均值不能直接写入八项音乐评分，也不生成国家或曲目排名。",
        "warnings": bundle.warnings,
    }


def list_cases(
    bundle: ResearchBundle,
    *,
    q: str = "",
    country: str = "",
    region: str = "",
    instrument: str = "",
    channel: str = "",
    theme: str = "",
    grade: str = "",
    analysis_sample: str = "all",
    page: int = 1,
    page_size: int = 12,
) -> dict[str, Any]:
    all_cases = eligible_cases(bundle)
    cases = filter_by_analysis_sample(all_cases, analysis_sample)
    q_lower = q.strip().lower()

    def matches(case: dict[str, Any]) -> bool:
        if country and case.get("country") != country:
            return False
        if region and case.get("region") != region:
            return False
        if instrument and instrument not in (case.get("instrument") or []):
            return False
        if channel and channel not in (case.get("channel") or []):
            return False
        if theme and theme not in (case.get("era_theme") or []):
            return False
        if grade and case.get("review_status") != grade:
            return False
        if q_lower:
            haystack = " ".join(str(case.get(field) or "") for field in (
                "case_id", "performer", "country", "region", "work", "music_type",
                "summary", "learning_motivation", "adaptation", "success_evidence",
                "instrument", "channel", "era_theme", "cultural_hooks",
            )).lower()
            if not all(token in haystack for token in q_lower.split()):
                return False
        return True

    filtered = [case for case in cases if matches(case)]
    filtered.sort(key=lambda case: str(case.get("case_id") or ""))
    total = len(filtered)
    pages = ceil(total / page_size) if total else 0
    start = (page - 1) * page_size
    page_cases = filtered[start:start + page_size]
    return {
        "sample": build_sample(bundle, cases),
        "analysis_scope": build_analysis_scope(bundle, cases, analysis_sample),
        "items": [_case_summary(bundle, case) for case in page_cases],
        "total": total,
        "result_count": len(page_cases),
        "pagination": {
            "page": page,
            "page_size": page_size,
            "pages": pages,
            "has_next": page < pages,
            "has_previous": page > 1,
        },
        "filters": {
            "q": q,
            "country": country,
            "region": region,
            "instrument": instrument,
            "channel": channel,
            "theme": theme,
            "grade": grade,
            "analysis_sample": analysis_sample,
        },
    }


def _similar_cases(bundle: ResearchBundle, case: dict[str, Any], limit: int = 3) -> list[dict[str, Any]]:
    current_id = case.get("case_id")
    current_themes = set(case.get("era_theme") or [])
    current_channels = set(case.get("channel") or [])
    current_instruments = set(case.get("instrument") or [])
    results = []
    for other in eligible_cases(bundle):
        if other.get("case_id") == current_id:
            continue
        score = 0
        reasons = []
        if current_instruments & set(other.get("instrument") or []):
            score += 40
            reasons.append("使用相同乐器")
        if case.get("music_type") == other.get("music_type"):
            score += 15
            reasons.append("音乐类型相同")
        if case.get("country") == other.get("country"):
            score += 15
            reasons.append("同一国家")
        elif case.get("region") == other.get("region"):
            score += 10
            reasons.append("同一区域")
        theme_overlap = current_themes & set(other.get("era_theme") or [])
        if theme_overlap:
            score += min(24, len(theme_overlap) * 8)
            reasons.append("共同主题：" + "、".join(sorted(theme_overlap)))
        channel_overlap = current_channels & set(other.get("channel") or [])
        if channel_overlap:
            score += min(12, len(channel_overlap) * 4)
            reasons.append("共同渠道：" + "、".join(sorted(channel_overlap)))
        if score <= 0:
            continue
        summary = _case_summary(bundle, other)
        summary["match_score"] = score
        summary["match_reasons"] = reasons
        results.append(summary)
    results.sort(key=lambda item: (-item["match_score"], str(item.get("case_id") or "")))
    return results[:limit]


def get_case_detail(bundle: ResearchBundle, case_id: str) -> dict[str, Any]:
    cases = eligible_cases(bundle)
    case = next((item for item in cases if item.get("case_id") == case_id), None)
    if not case:
        raise CaseNotFound(case_id)
    score_map = {
        score.get("indicator_id"): score
        for score in _scores_for(bundle, case_id)
    }
    labels = {
        item.get("indicator_id"): item
        for item in bundle.success_doc.get("indicators") or []
    }
    coding = []
    for indicator_id in INDICATOR_IDS:
        definition = labels.get(indicator_id, {})
        record = score_map.get(indicator_id)
        coding.append({
            "indicator_id": indicator_id,
            "label": definition.get("label_zh", indicator_id),
            "order": definition.get("order"),
            "score": record.get("score") if record else None,
            "evidence": record.get("evidence") if record else None,
            "source_ids": record.get("source_ids") if record else [],
            "missing_reason": record.get("missing_reason") if record else "评分记录缺失",
            "approval_status": record.get("approval_status") if record else None,
            "score_status": record.get("score_status") if record else None,
            "approver": record.get("approver") if record else None,
            "approval_date": record.get("approval_date") if record else None,
        })

    feedback_ids = set(case.get("audience_feedback_ids") or [])
    audience_feedback = []
    for source in case.get("sources") or []:
        if source.get("source_id") not in feedback_ids:
            continue
        audience_feedback.append({
            "feedback_id": source.get("source_id"),
            "evidence_type": source.get("feedback_evidence_type") or source.get("source_type"),
            "evidence_grade": source.get("feedback_grade") or source.get("reliability"),
            "country_basis": source.get("feedback_country_basis") or "来源页面所示海外语境",
            "language": source.get("feedback_language"),
            "valence": source.get("feedback_valence"),
            "excerpt": source.get("citation"),
            "summary": source.get("supports"),
            "limitations": source.get("notes"),
            "mechanism_codes": source.get("mechanism_codes") or [],
            "coding_eligible": bool(source.get("coding_eligible", True)),
            "source_url": source.get("url"),
            "publisher": source.get("publisher"),
        })

    mechanism_values = case.get("acceptance_mechanism_codes") or {}
    acceptance_mechanisms = []
    for code, label in ACCEPTANCE_MECHANISMS.items():
        value = mechanism_values.get(code, "not_evidenced")
        if value not in MECHANISM_STATUS_LABELS:
            value = "not_evidenced"
        acceptance_mechanisms.append({
            "code": code,
            "label": label,
            "status": value,
            "status_label": MECHANISM_STATUS_LABELS[value],
        })
    return {
        "sample": build_sample(bundle),
        "case": case,
        "coding": {
            **score_summary(bundle, case_id),
            "indicators": coding,
        },
        "audience_feedback": audience_feedback,
        "acceptance_mechanisms": acceptance_mechanisms,
        "acceptance_mechanism_confidence": case.get("acceptance_mechanism_confidence"),
        "outcome_status": case.get("outcome_evidence_status"),
        "outcome_label": OUTCOME_STATUS_LABELS.get(
            case.get("outcome_evidence_status"), "结果证据待解释"
        ),
        "similar_cases": _similar_cases(bundle, case),
        "warnings": bundle.warnings,
    }


def _normalize_title(value: object) -> str:
    """保守的曲名归一化：只去空白和常见标点，不做模糊匹配。"""
    raw = str(value or "").strip().lower()
    return re.sub(r"[\s\u3000·・:：,，。.!！?？'\"“”‘’（）()《》<>/\\\-_—]+", "", raw)


def build_music_context(
    bundle: ResearchBundle,
    *,
    title: str,
    category: str = "",
    subcategory: str = "",
    song_id: str = "",
) -> dict[str, Any]:
    """P6 单曲研究上下文。

    关联原则：
    - 曲目评分只按 music_scores 的 music_id 或曲名精确匹配；
    - 案例只按 music_scores.related_case_ids 关联；
    - 区域策略只按 regional_strategies.music_ids 关联；
    - 不使用曲名/乐器模糊匹配，不把无关案例挂到歌曲下面。
    """
    sample = build_sample(bundle)
    music_doc = bundle.music_doc
    weights = music_doc.get("weights") or {}
    tiers = music_doc.get("tiers") or []
    target_title = str(title or "").strip()
    normalized = _normalize_title(target_title)
    items = [item for item in (music_doc.get("items") or []) if isinstance(item, dict)]
    item = None
    matched_by = None

    if song_id:
        item = next((entry for entry in items if str(entry.get("music_id") or "") == str(song_id)), None)
        if item:
            matched_by = "music_id"

    if item is None and normalized:
        candidates = [entry for entry in items if _normalize_title(entry.get("title")) == normalized]
        if category:
            candidates = [entry for entry in candidates if str(entry.get("category") or "") == category]
        if subcategory:
            candidates = [entry for entry in candidates if str(entry.get("subcategory") or "") == subcategory]
        if len(candidates) == 1:
            item = candidates[0]
            matched_by = "exact_title"

    category_reference_items = []
    if item is None and category:
        category_reference_items = [
            entry for entry in items
            if str(entry.get("category") or "") == category
            and entry.get("display_allowed") is True
        ][:4]

    related_cases: list[dict[str, Any]] = []
    regional_rows: list[dict[str, Any]] = []
    if item is not None:
        related_ids = {str(case_id) for case_id in (item.get("related_case_ids") or [])}
        for case in eligible_cases(bundle):
            if case.get("case_id") in related_ids:
                summary = _case_summary(bundle, case)
                summary["relation"] = "related_case_ids"
                related_cases.append(summary)
        music_id = str(item.get("music_id") or "")
        for row in (bundle.regional_doc.get("rows") or []):
            if not isinstance(row, dict) or row.get("display_allowed") is not True:
                continue
            if music_id and music_id in (row.get("music_ids") or []):
                regional_rows.append(row)

    scores = item.get("scores") if item else {}
    valid_scores = {key: scores.get(key) for key in MUSIC_KEYS if scores.get(key) is not None}
    missing_indicators = [key for key in MUSIC_KEYS if scores.get(key) is None]
    total = _music_total(scores or {}, weights) if item else None
    potential = None
    if item:
        potential = {
            "status": "complete" if total is not None else ("pending" if music_doc.get("status") == "pending" else "incomplete"),
            "music_id": item.get("music_id"),
            "title": item.get("title"),
            "scores": scores,
            "valid_count": len(valid_scores),
            "missing_indicators": missing_indicators,
            "total_score": total,
            "tier": _tier_for_score(total, tiers) if total is not None else "资料不足",
            "rank": None,
            "selection_tier": item.get("selection_tier"),
            "primary_mechanisms": item.get("primary_mechanisms") or [],
            "era_theme": item.get("era_theme"),
            "international_format": item.get("international_format"),
            "selection_reason": item.get("selection_reason"),
            "main_risk": item.get("main_risk"),
        }

    analysis_cases = [
        case for case in eligible_cases(bundle)
        if case.get("owner_approval_status") == "approved"
    ]
    analysis_cases.sort(key=lambda case: str(case.get("case_id") or ""))
    reference_mechanisms = set(item.get("primary_mechanisms") or []) if item else set()
    reference_instrument = str(item.get("instrument_or_form") or "") if item else str(subcategory or "")
    profile_terms = {
        value for value in (
            subcategory,
            reference_instrument,
            str(item.get("research_category") or "") if item else "",
        ) if value
    }
    item_theme = str(item.get("era_theme") or "") if item else ""
    matched_cases = []
    for analysis_case in analysis_cases:
        match_score = 0
        match_reasons = []
        case_instruments = {str(value) for value in (analysis_case.get("instrument") or [])}
        case_text = " ".join(str(analysis_case.get(field) or "") for field in (
            "performer", "work", "music_type", "event_name", "summary", "adaptation",
            "instrument", "cultural_hooks", "era_theme",
        ))
        if target_title and _normalize_title(target_title) in _normalize_title(case_text):
            match_score += 100
            match_reasons.append(f"案例材料直接出现曲名《{target_title}》")
        if reference_instrument and (
            reference_instrument in case_instruments or reference_instrument in case_text
        ):
            match_score += 40
            match_reasons.append(f"同类乐器：{reference_instrument}")
        elif subcategory and (subcategory in case_instruments or subcategory in case_text):
            match_score += 32
            match_reasons.append(f"同类音乐/乐器：{subcategory}")
        type_terms = sorted(term for term in profile_terms if len(term) >= 2 and term in case_text)
        if type_terms:
            match_score += min(24, len(type_terms) * 8)
            match_reasons.append("曲目类型重合：" + "、".join(type_terms))
        mechanism_values = analysis_case.get("acceptance_mechanism_codes") or {}
        strong_overlap = sorted(
            code for code in reference_mechanisms if mechanism_values.get(code) == "strong"
        )
        partial_overlap = sorted(
            code for code in reference_mechanisms if mechanism_values.get(code) == "partial"
        )
        if strong_overlap:
            match_score += len(strong_overlap) * 10
            match_reasons.append(
                "强机制重合：" + "、".join(ACCEPTANCE_MECHANISMS.get(code, code) for code in strong_overlap)
            )
        if partial_overlap:
            match_score += len(partial_overlap) * 5
            match_reasons.append(
                "部分机制重合：" + "、".join(ACCEPTANCE_MECHANISMS.get(code, code) for code in partial_overlap)
            )
        if item_theme:
            theme_fragments = [fragment for fragment in re.split(r"[、，,与和及/]+", item_theme) if len(fragment) >= 2]
            theme_hits = [fragment for fragment in theme_fragments if fragment in case_text]
            if theme_hits:
                match_score += min(15, len(theme_hits) * 5)
                match_reasons.append("主题重合：" + "、".join(theme_hits))
        if match_score <= 0:
            continue
        summary = _case_summary(bundle, analysis_case)
        summary.update({
            "relation": "candidate_mechanism_reference",
            "match_score": match_score,
            "match_reasons": match_reasons,
        })
        matched_cases.append(summary)
    matched_cases.sort(
        key=lambda row: (-row["match_score"], -int(row.get("source_count") or 0), str(row.get("case_id") or ""))
    )

    if related_cases:
        factor_case_ids = [str(row.get("case_id")) for row in related_cases]
        factor_scope = "direct"
        factor_scope_label = "当前曲目直接关联案例的因素构成"
    elif matched_cases:
        factor_case_ids = [str(row.get("case_id")) for row in matched_cases[:5]]
        factor_scope = "matched"
        factor_scope_label = "当前曲目机制匹配案例的因素构成"
    else:
        factor_case_ids = []
        factor_scope = "unavailable"
        factor_scope_label = "暂无当前曲目可用的案例因素参考"

    factor_case_id_set = set(factor_case_ids)
    factor_labels = {
        entry.get("indicator_id"): entry.get("label_zh")
        for entry in bundle.success_doc.get("indicators") or []
    }
    song_factor_means = []
    for indicator_id in INDICATOR_IDS:
        values = [
            float(score["score"])
            for score in bundle.scores
            if str(score.get("case_id")) in factor_case_id_set
            and score.get("indicator_id") == indicator_id
            and score.get("score") is not None
        ]
        if values:
            song_factor_means.append({
                "indicator_id": indicator_id,
                "label": factor_labels.get(indicator_id, indicator_id),
                "mean_score": round(sum(values) / len(values), 2),
                "n": len(values),
            })
    song_factor_total = sum(float(row["mean_score"]) for row in song_factor_means)
    song_factor_shares = [
        {
            **row,
            "share": round(float(row["mean_score"]) / song_factor_total * 100, 1)
            if song_factor_total else 0,
        }
        for row in song_factor_means
    ]
    song_factor_shares.sort(key=lambda row: (-row["share"], str(row["indicator_id"])))
    approved_factors = build_success_factors(bundle, "all").get("factors") or []
    scored_factors = [factor for factor in approved_factors if factor.get("mean_score") is not None]
    factor_total = sum(float(factor["mean_score"]) for factor in scored_factors)
    factor_shares = [
        {
            "indicator_id": factor.get("indicator_id"),
            "label": factor.get("label"),
            "mean_score": factor.get("mean_score"),
            "n": factor.get("n"),
            "share": round(float(factor["mean_score"]) / factor_total * 100, 1) if factor_total else 0,
        }
        for factor in scored_factors
    ]
    factor_shares.sort(key=lambda factor: (-factor["share"], str(factor["indicator_id"])))
    reference_regions = [
        row for row in (bundle.regional_doc.get("rows") or [])
        if isinstance(row, dict) and row.get("display_allowed") is True
    ]

    reasons = []
    if item is None:
        reasons.append(f"music_scores.json 中没有与《{target_title}》精确匹配的评分记录。")
        reasons.append("未命中候选曲评分条目；案例参考仅按当前类别、乐器和已编码机制生成，并明确标注为同类参考。")
    else:
        reasons.append(f"已通过 {matched_by} 关联到音乐评分条目。")
        if not related_cases:
            reasons.append("该曲目没有人工登记 related_case_ids；下方案例按曲名、乐器/类型、主题和接受机制计算匹配，并展示匹配理由。")
    if item is not None and not regional_rows:
        reasons.append("没有 music_ids 包含该曲目的已审核区域策略。")
    if item is None and not regional_rows:
        reasons.append("regional_strategies.rows 当前没有可关联的区域策略。")

    return {
        "sample": sample,
        "music": {
            "song_id": song_id or None,
            "title": target_title,
            "category": category,
            "subcategory": subcategory,
        },
        "association": {
            "status": "linked" if item is not None else ("category_reference" if category_reference_items else "unmapped"),
            "matched_by": matched_by,
            "label": "已建立曲目关联" if item is not None else ("同类候选参考" if category_reference_items else "未建立曲目关联"),
            "reasons": reasons,
        },
        "music_status": music_doc.get("status") or "pending",
        "music_status_label": music_doc.get("status_label") or "待补充",
        "music_note": music_doc.get("note"),
        "weights": weights,
        "tiers": tiers,
        "potential": potential,
        "related_cases": related_cases,
        "matched_cases": matched_cases[:5],
        "factor_reference": {
            "scope": factor_scope,
            "scope_label": factor_scope_label,
            "case_ids": factor_case_ids,
            "factor_shares": song_factor_shares,
        },
        "regional_rows": regional_rows,
        "category_reference": {
            "scope_label": f"{category}类候选曲传播画像（非本曲实测）",
            "items": [
                {
                    "music_id": entry.get("music_id"),
                    "title": entry.get("title"),
                    "selection_tier": entry.get("selection_tier"),
                    "primary_mechanisms": entry.get("primary_mechanisms") or [],
                    "era_theme": entry.get("era_theme"),
                    "international_format": entry.get("international_format"),
                    "selection_reason": entry.get("selection_reason"),
                    "main_risk": entry.get("main_risk"),
                }
                for entry in category_reference_items
            ],
            "primary_mechanisms": sorted(reference_mechanisms),
        } if category_reference_items else None,
        "global_reference": {
            "scope_label": f"{len(analysis_cases)}个已审批海外案例库整体参考（非单曲结论）",
            "cases": [_case_summary(bundle, case) for case in analysis_cases[:3]],
            "factor_shares": factor_shares,
            "regional_rows": reference_regions,
        },
        "warnings": bundle.warnings,
    }

