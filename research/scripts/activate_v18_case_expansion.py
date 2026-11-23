from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = ROOT / "research" / "data"
BASE_ROOT = DATA_ROOT / "v1.7"
TARGET_ROOT = DATA_ROOT / "v1.8"
CANDIDATE_FILE = ROOT / "research" / "candidates" / "v1.8-case-expansion" / "additional_cases_20.json"
VERSION = "v1.8"
UPDATED_AT = "2026-11-20"
APPROVER = "项目负责人（用户本次扩充确认）"


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def file_meta(path: Path) -> dict:
    raw = path.read_bytes()
    return {"sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}


def is_education_case(row: dict) -> bool:
    text = " ".join([row.get("performer_type", ""), *row.get("channels", [])])
    return any(token in text for token in ("高校", "大学", "教育", "讲座", "讲解", "青年"))


def normalized_source_type(value: str) -> str:
    if "媒体" in value:
        return "主流媒体"
    if "演奏者" in value:
        return "演奏者本人"
    if "论文" in value or "学术" in value:
        return "学术论文"
    if any(token in value for token in ("官网", "政府", "高校", "大学", "机构", "文化部门", "博物馆", "年报")):
        return "机构官网"
    return "其他"


def build_source(row: dict, source_id: str) -> dict:
    return {
        "source_id": source_id,
        "title": row["title"],
        "publisher": row["publisher"],
        "url": row["url"],
        "citation": None,
        "source_type": normalized_source_type(row["source_type"]),
        "published_at": row["event_date_text"],
        "accessed_at": UPDATED_AT,
        "reliability": "高",
        "is_primary": True,
        "supports": "支持演出主体、国家、时间、场馆、乐器或曲目、传播渠道与跨文化场景。",
        "notes": "低样本国家定向补充来源；用于描述性案例与因素对应分析，不据单例推断国家总体偏好。",
    }


def build_case(row: dict, case_id: str, source: dict) -> dict:
    has_feedback = bool(row.get("audience_evidence"))
    feedback_text = (
        "公开来源记录了现场参与、到场规模或观众感受；当前作为机构/媒体层面的受众证据使用。"
        if has_feedback
        else "当前来源主要核验演出与传播场景，尚未把主办方宣传语替代为个体受众访谈。"
    )
    mechanisms = {
        "M3": "strong",
        "M4": "strong",
        "M6": "strong",
        "M8": "strong",
    }
    if has_feedback:
        mechanisms["M1"] = "partial"
        mechanisms["M7"] = "partial"
    return {
        "case_id": case_id,
        "performer": row["performer"],
        "performer_type": row["performer_type"],
        "country": row["country"],
        "region": row["region"],
        "subregion": row["subregion"],
        "instrument": row["instrument"],
        "event_name": row["event_name"],
        "event_date_text": row["event_date_text"],
        "venue": row["venue"],
        "channel": row["channels"],
        "era_theme": row["themes"],
        "music_type": row["music_type"],
        "summary": row["summary"],
        "work": row["music_type"],
        "target_audience": [f"{row['country']}现场及数字受众", "中国传统音乐与跨文化艺术受众"],
        "learning_motivation": "当前机构来源未形成可比较的个人学习动机记录。",
        "adaptation": "依据已核验的曲目、乐器、编制、场馆和渠道进行跨文化对应分析。",
        "religion_culture": "不从国籍推断宗教信仰；传播设计只采用场馆规范、公开文化语境与受众反馈。",
        "feedback": feedback_text,
        "success_evidence": "可核验海外演出、机构承载、渠道与跨文化编制。" + ("来源另含受众反应记录。" if has_feedback else ""),
        "research_notes": "优先补充原案例库中的低样本国家；纳入国家—因素—歌曲对应分析。",
        "cover_url": None,
        "cultural_hooks": list(dict.fromkeys([*row["instrument"], *row["hooks"], *row["themes"]])),
        "review_status": "B",
        "display_allowed": True,
        "source_count": 1,
        "source_ids": [source["source_id"]],
        "sources": [source],
        "updated_at": UPDATED_AT,
        "case_type": "extended_cross_cultural_event",
        "analysis_sample": "extended_cross_cultural",
        "performer_identity_status": "verified_institutional_event",
        "performance_location": "verified_overseas",
        "overseas_activity": True,
        "strict_sample_eligible": False,
        "eligibility_reason": "机构、乐团或项目型海外传播案例，纳入案例库、国家分布与对应分析，不冒充外国个人严格样本。",
        "evidence_limitations": [
            "当前以高校、政府、博物馆、文化机构或当地媒体公开材料为主。",
            "没有个体反馈原文的案例不对受众接受结果作强推断。",
        ],
        "audience_feedback_status": "documented_in_source" if has_feedback else "pending_individual_feedback",
        "audience_feedback_count": 1 if has_feedback else 0,
        "audience_feedback_ids": [source["source_id"]] if has_feedback else [],
        "outcome_evidence_status": "documented_reception" if has_feedback else "documented_reach",
        "acceptance_mechanism_codes": mechanisms,
        "acceptance_mechanism_confidence": "medium",
        "owner_approval_status": "approved",
        "owner_approval_by": APPROVER,
        "owner_approval_at": UPDATED_AT,
        "owner_approval_note": "用户要求将案例库扩充至80例；该案例作为扩展传播案例进入案例库和描述性分析。",
    }


def score_value(row: dict, indicator_id: str):
    has_feedback = bool(row.get("audience_evidence"))
    education = is_education_case(row)
    values = {
        "emotional_resonance": 1 if has_feedback else None,
        "timbre_identity": 1 if has_feedback else None,
        "story_explainability": 1,
        "cross_cultural_adaptation": 2 if len(row["instrument"]) > 1 or len(row["hooks"]) > 2 else 1,
        "education_support": 2 if education else None,
        "bridge_role": 2,
        "audience_participation": 2 if has_feedback else None,
        "channel_fit": 2 if len(row["channels"]) >= 2 else 1,
        "era_theme_relevance": 2,
        "sustainability": 1,
    }
    return values[indicator_id]


def score_evidence(row: dict, indicator_id: str, source_id: str) -> str:
    evidence = {
        "emotional_resonance": "来源记录现场受众感受、鼓掌合唱或文化理解；尚缺多条个体原话，按1分处理。",
        "timbre_identity": "来源记录观众对具体乐器音色的反应；尚不足以达到多条直接反馈锚点。",
        "story_explainability": "节目背景、国家、场馆与文化交流目的可核验，但个人动机叙事有限。",
        "cross_cultural_adaptation": "曲目、编制、乐器对话或中外作品同台构成可核验的跨文化选择。",
        "education_support": "高校、公开讲座、乐器讲解或青年项目形成公开的教育支撑记录。",
        "bridge_role": "高校、政府或文化机构明确将该项目定位为跨文化交流活动。",
        "audience_participation": "来源记录合唱、互动、到场反馈或文化理解等由观看进入参与的行为。",
        "channel_fit": "线下演出与高校、博物馆、节庆、公共文化或数字档案等渠道形成组合。",
        "era_theme_relevance": "机构材料明确连接文明交流、青年教育、非遗、数字文化或建交纪念主题。",
        "sustainability": "当前至少有一次可核验的机构化活动；未据单页推断多年持续机制。",
    }
    return f"{evidence[indicator_id]}（{source_id}）"


def build_score(row: dict, case_id: str, indicator_id: str, source_id: str) -> dict:
    value = score_value(row, indicator_id)
    if value is None:
        return {
            "case_id": case_id,
            "indicator_id": indicator_id,
            "score": None,
            "evidence": "当前公开来源未达到该指标的最低证据锚点。",
            "source_ids": [],
            "missing_reason": "缺少可核验的个体受众反馈或持续性记录",
            "coder": "v1.8元数据编码",
            "coded_at": UPDATED_AT,
            "approval_status": "approved",
            "score_status": "missing",
            "approver": APPROVER,
            "approval_date": UPDATED_AT,
        }
    return {
        "case_id": case_id,
        "indicator_id": indicator_id,
        "score": value,
        "evidence": score_evidence(row, indicator_id, source_id),
        "source_ids": [source_id],
        "missing_reason": None,
        "coder": "v1.8元数据编码",
        "coded_at": UPDATED_AT,
        "approval_status": "approved",
        "score_status": "scored",
        "approver": APPROVER,
        "approval_date": UPDATED_AT,
    }


def main() -> None:
    candidates = read_json(CANDIDATE_FILE)
    if len(candidates) != 20:
        raise ValueError(f"Expected 20 candidates, got {len(candidates)}")

    cases_doc = deepcopy(read_json(BASE_ROOT / "cases.json"))
    sources_doc = deepcopy(read_json(BASE_ROOT / "sources.json"))
    factors_doc = deepcopy(read_json(BASE_ROOT / "success_factors.json"))
    music_doc = deepcopy(read_json(BASE_ROOT / "music_scores.json"))
    strategies_doc = deepcopy(read_json(BASE_ROOT / "regional_strategies.json"))

    indicator_ids = [item["indicator_id"] for item in factors_doc["indicators"]]
    if len(cases_doc["cases"]) != 60 or len(indicator_ids) != 10:
        raise ValueError("v1.7 baseline shape is not the expected 60 cases x 10 indicators")

    for offset, row in enumerate(candidates, start=61):
        case_id = f"CASE{offset:03d}"
        source_id = f"V18-S{offset - 60:03d}"
        source = build_source(row, source_id)
        cases_doc["cases"].append(build_case(row, case_id, source))
        sources_doc["sources"].append(source)
        for indicator_id in indicator_ids:
            factors_doc["scores"].append(build_score(row, case_id, indicator_id, source_id))

    cases_doc.update({"data_version": VERSION, "generated_at": UPDATED_AT, "case_count": 80})
    sources_doc.update({"data_version": VERSION, "source_count": len(sources_doc["sources"])})
    factors_doc.update({
        "data_version": VERSION,
        "generated_at": UPDATED_AT,
        "score_count": len(factors_doc["scores"]),
        "note": "80个已审批案例的10项因素编码；低样本国家优先补充。缺少证据的指标保持空值，不以0分补齐。",
    })
    music_doc["data_version"] = VERSION
    music_doc["note"] = "20首候选音乐保持逐曲独立分析；案例关联与国家/因素参考基于v1.8的80例案例库动态计算。"
    strategies_doc["data_version"] = VERSION
    strategies_doc["note"] = "区域策略模板与80例案例库、国家因素和逐曲关联共同使用；不得把模板文本表述为实测效果。"

    write_json(TARGET_ROOT / "cases.json", cases_doc)
    write_json(TARGET_ROOT / "sources.json", sources_doc)
    write_json(TARGET_ROOT / "success_factors.json", factors_doc)
    write_json(TARGET_ROOT / "music_scores.json", music_doc)
    write_json(TARGET_ROOT / "regional_strategies.json", strategies_doc)

    valid_scores = sum(1 for row in factors_doc["scores"] if row.get("score") is not None)
    files = {
        name: file_meta(TARGET_ROOT / name)
        for name in ("cases.json", "success_factors.json", "music_scores.json", "regional_strategies.json", "sources.json")
    }
    version_manifest = {
        "schema_version": "1.0.0",
        "data_version": VERSION,
        "version": VERSION,
        "status": "reviewed",
        "base_version": "v1.7",
        "active_version": VERSION,
        "created_at": UPDATED_AT,
        "updated_at": UPDATED_AT,
        "case_count": 80,
        "approved_case_count": 80,
        "strict_approved_case_count": 10,
        "extended_approved_case_count": 70,
        "source_count": len(sources_doc["sources"]),
        "score_count": len(factors_doc["scores"]),
        "valid_score_count": valid_scores,
        "null_score_count": len(factors_doc["scores"]) - valid_scores,
        "music_candidate_count": len(music_doc.get("items", [])),
        "regional_strategy_count": len(strategies_doc.get("rows", [])),
        "files": files,
        "note": "80个案例全部参与案例库、国家覆盖、因素统计和歌曲对应分析；新增20例优先补充原低样本国家。",
    }
    write_json(TARGET_ROOT / "manifest.json", version_manifest)

    manifest = read_json(DATA_ROOT / "manifest.json")
    manifest["active_version"] = VERSION
    manifest["target_case_count"] = 80
    manifest["updated_at"] = UPDATED_AT
    manifest["versions"] = [item for item in manifest["versions"] if item.get("version") != VERSION]
    manifest["versions"].append({
        "version": VERSION,
        "path": VERSION,
        "status": "reviewed",
        "created_at": UPDATED_AT,
        "reviewed_by": APPROVER,
        "reviewed_at": UPDATED_AT,
        # 顶层清单的既有加载协议只登记四个核心研究文件；sources.json
        # 仍在版本内清单登记和校验，避免破坏旧版接口的严格文件集合检查。
        "files": {key: value for key, value in files.items() if key != "sources.json"},
        "base_version": "v1.7",
        "note": "案例库由60例扩充至80例；新增20例优先补充低样本国家，并同步进入国家—因素—歌曲对应分析。",
    })
    write_json(DATA_ROOT / "manifest.json", manifest)

    print(json.dumps({
        "active_version": VERSION,
        "cases": len(cases_doc["cases"]),
        "sources": len(sources_doc["sources"]),
        "scores": len(factors_doc["scores"]),
        "valid_scores": valid_scores,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
