"""P8.5 研究数据挖掘：当前 10 个案例的描述性分析与只读音乐库连接。"""

from __future__ import annotations

from collections import Counter
from itertools import combinations
from typing import Any

from django.db import connection

from .research_analytics import (
    ANALYSIS_SAMPLES,
    INDICATOR_IDS,
    build_analysis_scope,
    build_sample,
    eligible_cases,
    indicator_gate,
)
from .research_data import ResearchBundle


def _distribution(cases: list[dict[str, Any]], field: str, multi: bool = False) -> list[dict[str, Any]]:
    counter: Counter[str] = Counter()
    for case in cases:
        value = case.get(field)
        values = value if multi and isinstance(value, list) else [value]
        for item in values:
            if item:
                counter[str(item)] += 1
    return [{"key": k, "count": v} for k, v in sorted(counter.items(), key=lambda x: (-x[1], x[0]))]


def _rank(values: list[float]) -> list[float]:
    order = sorted(range(len(values)), key=lambda i: values[i])
    ranks = [0.0] * len(values)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and values[order[j + 1]] == values[order[i]]:
            j += 1
        avg = (i + j) / 2 + 1
        for k in range(i, j + 1):
            ranks[order[k]] = avg
        i = j + 1
    return ranks


def _spearman(x: list[float], y: list[float]) -> float | None:
    if len(x) < 2:
        return None
    rx, ry = _rank(x), _rank(y)
    mx = sum(rx) / len(rx)
    my = sum(ry) / len(ry)
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    dx = sum((a - mx) ** 2 for a in rx) ** 0.5
    dy = sum((b - my) ** 2 for b in ry) ** 0.5
    if dx == 0 or dy == 0:
        return None
    return round(num / (dx * dy), 3)


def _analysis_db_status(version: str) -> dict[str, Any]:
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM dbo.research_case_analysis WHERE data_version = %s", [version])
            case_count = int(cursor.fetchone()[0])
            cursor.execute("SELECT COUNT(*), SUM(CASE WHEN score IS NULL THEN 1 ELSE 0 END) FROM dbo.research_score_analysis WHERE data_version = %s", [version])
            score_count, null_count = cursor.fetchone()
            cursor.execute("SELECT COUNT(*) FROM dbo.research_source_analysis WHERE data_version = %s", [version])
            source_count = int(cursor.fetchone()[0])
        return {
            "status": "connected",
            "tables": ["research_case_analysis", "research_score_analysis", "research_source_analysis"],
            "case_count": case_count,
            "score_count": int(score_count),
            "null_score_count": int(null_count or 0),
            "source_count": source_count,
        }
    except Exception as exc:  # pragma: no cover
        return {
            "status": "unavailable",
            "tables": ["research_case_analysis", "research_score_analysis", "research_source_analysis"],
            "case_count": None,
            "score_count": None,
            "null_score_count": None,
            "source_count": None,
            "note": f"分析表读取失败：{exc.__class__.__name__}",
        }


def _library_status() -> dict[str, Any]:
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM traditional_song")
            count = int(cursor.fetchone()[0])
        return {
            "status": "connected",
            "database": "SQL Server",
            "table": "traditional_song",
            "song_count": count,
            "mapping_count": 0,
            "mapped_count": 0,
            "note": "只读连接；当前没有可精确匹配的案例曲目，未按乐器/国家模糊映射。",
        }
    except Exception as exc:  # pragma: no cover - depends on local SQL Server
        return {
            "status": "unavailable",
            "database": "SQL Server",
            "table": "traditional_song",
            "song_count": None,
            "mapping_count": 0,
            "mapped_count": 0,
            "note": f"只读连接失败：{exc.__class__.__name__}",
        }


def build_mining(bundle: ResearchBundle, analysis_sample: str = "all") -> dict[str, Any]:
    cases = [c for c in eligible_cases(bundle) if analysis_sample == "all" or c.get("analysis_sample") == analysis_sample]
    sample = build_sample(bundle, cases)
    scope = build_analysis_scope(bundle, cases, analysis_sample)
    case_ids = {c.get("case_id") for c in cases}
    scores_by_case: dict[str, dict[str, Any]] = {str(c.get("case_id")): {} for c in cases}
    for score in bundle.scores:
        if score.get("case_id") in case_ids:
            scores_by_case[str(score.get("case_id"))][str(score.get("indicator_id"))] = score.get("score")

    labels = {i.get("indicator_id"): i.get("label_zh") for i in bundle.success_doc.get("indicators") or []}
    indicators = []
    for indicator_id in INDICATOR_IDS:
        values = [scores_by_case[c["case_id"]].get(indicator_id) for c in cases]
        valid = [v for v in values if v is not None]
        gate = indicator_gate(len(valid))
        indicators.append({
            "indicator_id": indicator_id,
            "label": labels.get(indicator_id, indicator_id),
            "n": len(valid),
            "missing_count": len(cases) - len(valid),
            "coverage_rate": round(len(valid) / len(cases), 4) if cases else 0.0,
            "mean_score": round(sum(valid) / len(valid), 2) if valid else None,
            "max_score": 3,
            **gate,
        })

    correlations = []
    for a, b in combinations(INDICATOR_IDS, 2):
        pairs = [
            (scores_by_case[c["case_id"]].get(a), scores_by_case[c["case_id"]].get(b))
            for c in cases
            if scores_by_case[c["case_id"]].get(a) is not None
            and scores_by_case[c["case_id"]].get(b) is not None
        ]
        n = len(pairs)
        value = _spearman([float(x) for x, _ in pairs], [float(y) for _, y in pairs]) if n >= 5 else None
        correlations.append({
            "x": a, "y": b, "n": n, "rho": value,
            "status": "exploratory" if n >= 5 else "insufficient",
            "note": "成对完整样本 n≥5 才计算；探索性，不作因果解释。" if n >= 5 else "成对完整样本少于5，不计算相关系数。",
        })

    case_rows = []
    for c in cases:
        cid = str(c["case_id"])
        values = [scores_by_case[cid].get(i) for i in INDICATOR_IDS]
        valid = [v for v in values if v is not None]
        case_rows.append({
            "case_id": cid,
            "performer": c.get("performer"),
            "country": c.get("country"),
            "region": c.get("region"),
            "instrument": c.get("instrument") or [],
            "case_type": c.get("case_type"),
            "analysis_sample": c.get("analysis_sample"),
            "source_count": c.get("source_count") or 0,
            "valid_count": len(valid),
            "missing_count": len(INDICATOR_IDS) - len(valid),
            "mean_score": round(sum(valid) / len(valid), 2) if valid else None,
            "scores": {i: scores_by_case[cid].get(i) for i in INDICATOR_IDS},
        })

    return {
        "sample": sample,
        "analysis_scope": scope,
        "case_count": len(cases),
        "score_count": sum(len(v) for v in scores_by_case.values()),
        "valid_score_count": sum(1 for c in cases for i in INDICATOR_IDS if scores_by_case[str(c["case_id"])].get(i) is not None),
        "cases": case_rows,
        "distributions": {
            "country": _distribution(cases, "country"),
            "instrument": _distribution(cases, "instrument", True),
            "case_type": _distribution(cases, "case_type"),
            "analysis_sample": _distribution(cases, "analysis_sample"),
            "review_status": _distribution(cases, "review_status"),
        },
        "indicators": indicators,
        "correlations": correlations,
        "library": _library_status(),
        "analysis_db": _analysis_db_status(bundle.version),
        "scope_note": f"当前 n={len(cases)}，其中新扩展案例多数指标为 null；只能做描述性/探索性分析，不进行聚类、PCA、因果推断或榜单。",
        "data_version": bundle.version,
        "warnings": bundle.warnings,
    }
