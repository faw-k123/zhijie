from __future__ import annotations

import csv
import hashlib
import json
import re
from copy import deepcopy
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = ROOT / "research" / "data"
BASE_ROOT = DATA_ROOT / "v1.6"
TARGET_ROOT = DATA_ROOT / "v1.7"
CANDIDATE_ROOT = ROOT / "research" / "candidates" / "v1.7-teacher-revision"
APPROVER = "项目负责人（用户确认）"
APPROVAL_DATE = "2026-11-08"
FULL_CASE_APPROVAL_DATE = "2026-11-12"

CASE_ID_MAP = {
    "SC001": "CASE005",
    "SC002": "CASE006",
    "SC003": "CASE001",
    "SC004": "CASE041",
    "SC005": "CASE042",
    "SC006": "CASE010",
    "SC007": "CASE043",
    "SC008": "CASE044",
    "SC009": "CASE045",
    "SC010": "CASE007",
}

OUTCOME_STATUS = {
    "SC001": "acceptance",
    "SC002": "acceptance",
    "SC003": "conversion",
    "SC004": "engagement",
    "SC005": "engagement",
    "SC006": "acceptance",
    "SC007": "engagement",
    "SC008": "institutionalized",
    "SC009": "conversion",
    "SC010": "engagement",
}

SCORE_PROFILES = {
    "SC001": [2, 3, 1, 3, None, 2, None, 2, 2, 3],
    "SC002": [2, 2, 3, 2, 2, 2, 2, 3, 2, 3],
    "SC003": [2, 3, 3, 3, 2, 2, 3, 3, 3, 3],
    "SC004": [1, 1, 3, 1, 2, 3, 2, 2, 2, 3],
    "SC005": [1, 3, 2, 3, 1, 3, 1, 2, 2, 3],
    "SC006": [1, 3, 3, 3, None, 2, 1, 3, 3, 3],
    "SC007": [1, 3, 3, 3, 2, 2, 1, 3, 3, 3],
    "SC008": [2, 2, 2, 3, 1, 3, 2, 3, 2, 3],
    "SC009": [1, 1, 3, 2, 2, 3, 3, 3, 3, 3],
    "SC010": [1, 2, 3, 2, 3, 3, 2, 3, 2, 3],
}

INDICATOR_EVIDENCE = {
    "emotional_resonance": "受众/专业反馈中的情绪表达，按直接性与数量依据0—3锚点编码。",
    "timbre_identity": "反馈或专业评论明确涉及中国乐器音色、技法或声音辨识。",
    "story_explainability": "身份、学习经历、文化背景与传播过程构成可追溯叙事。",
    "cross_cultural_adaptation": "曲目、编制、风格或呈现存在可核验的跨文化转译。",
    "education_support": "公开材料显示教学、课程、讲座、工作坊或持续学习转化。",
    "bridge_role": "机构、媒体或持续项目确认演奏者的跨文化中介作用。",
    "audience_participation": "反馈显示评论、提问、学习、复邀或其他由观看向参与的转化。",
    "channel_fit": "线上、线下、教育或机构渠道与音乐呈现形成可核验组合。",
    "era_theme_relevance": "材料可直接连接文明交流、青年、生态、女性、数字文化等时代主题。",
    "sustainability": "公开履历和活动记录显示传播跨越单次事件并持续发生。",
}

SUBREGIONS = {
    "澳大利亚": "大洋洲",
    "美国": "北美",
    "法国": "西欧",
    "加拿大": "北美",
    "日本": "东亚",
    "巴西": "南美",
    "英国": "西欧",
}


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read_csv(name: str) -> list[dict[str, str]]:
    with (CANDIDATE_ROOT / name).open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def split_pipe(value: str) -> list[str]:
    return [item.strip() for item in (value or "").split("|") if item.strip()]


def split_instruments(value: str) -> list[str]:
    return [item.strip() for item in re.split(r"[、，,/]+", value or "") if item.strip()]


def reliability_zh(value: str) -> str:
    return {"high": "高", "medium": "中", "low": "低", "A": "高", "B": "中", "C": "低"}.get(value, "中")


def allowed_source_type(value: str, *, feedback: bool = False) -> str:
    if value in {"主流媒体", "机构官网", "学术论文", "演奏者本人", "视频平台", "演出主办方", "其他"}:
        return value
    if feedback:
        return {
            "professional_review": "主流媒体",
            "direct_platform_comment": "视频平台",
            "organizer_audience_summary": "演出主办方",
            "institutional_review": "机构官网",
            "relayed_audience_quote": "演出主办方",
        }.get(value, "其他")
    if "媒体" in value or "出版" in value:
        return "主流媒体"
    if "履历" in value or "个人" in value:
        return "演奏者本人"
    if any(token in value for token in ("政府", "高校", "协会", "机构", "经纪", "组织")):
        return "机构官网"
    return "其他"


def batch_source_to_record(row: dict[str, str]) -> dict:
    supports = "；".join(
        value for value in (
            row.get("supports_identity"),
            row.get("supports_instrument"),
            row.get("supports_performance"),
            row.get("supports_outcome"),
        ) if value and value != "无"
    )
    return {
        "source_id": row["source_id"],
        "title": row["title"],
        "publisher": row["publisher"],
        "url": row["url"],
        "citation": None,
        "source_type": allowed_source_type(row["source_type"]),
        "published_at": None,
        "accessed_at": row["accessed_at"],
        "reliability": reliability_zh(row["reliability"]),
        "is_primary": True,
        "supports": supports,
        "notes": row.get("notes") or None,
    }


def feedback_source_to_record(row: dict[str, str]) -> dict:
    publisher = urlparse(row["source_url"]).netloc or "公开来源"
    return {
        "source_id": row["feedback_id"],
        "title": f"受众反馈：{row['performer']} / {row['feedback_id']}",
        "publisher": publisher,
        "url": row["source_url"],
        "citation": row.get("original_excerpt") or None,
        "source_type": allowed_source_type(row["evidence_type"], feedback=True),
        "published_at": None,
        "accessed_at": row["accessed_at"],
        "reliability": reliability_zh(row["evidence_grade"]),
        "is_primary": row["evidence_type"] in {"direct_platform_comment", "direct_student_quote", "audience_action"},
        "supports": row["zh_summary"],
        "notes": row["limitations"],
        "feedback_evidence_type": row["evidence_type"],
        "feedback_grade": row["evidence_grade"],
        "feedback_country_basis": row["feedback_country_basis"],
        "feedback_language": row["language"],
        "feedback_valence": row["valence"],
        "mechanism_codes": split_pipe(row["mechanism_codes"]),
        "coding_eligible": row["coding_eligible"] == "yes",
    }


def country_source_to_record(row: dict[str, str]) -> dict:
    return {
        "source_id": row["source_id"],
        "title": row["title"],
        "publisher": row["publisher"],
        "url": row["url"],
        "citation": None,
        "source_type": allowed_source_type(row["source_type"]),
        "published_at": None,
        "accessed_at": row["accessed_at"],
        "reliability": "高",
        "is_primary": True,
        "supports": row["supports"],
        "notes": row["limitation"],
    }


def mechanisms_for(row: dict[str, str]) -> dict[str, str]:
    return {
        key.split("_", 1)[0]: value
        for key, value in row.items()
        if re.match(r"^M\d_", key) and value
    }


def build_cases(base_doc: dict, strict_rows, source_rows, feedback_rows, coding_rows) -> dict:
    cases = deepcopy(base_doc["cases"])
    by_id = {case["case_id"]: case for case in cases}
    source_by_id = {row["source_id"]: batch_source_to_record(row) for row in source_rows}
    feedback_by_case: dict[str, list[dict[str, str]]] = {}
    for row in feedback_rows:
        feedback_by_case.setdefault(row["candidate_id"], []).append(row)
    coding_by_case = {row["candidate_id"]: row for row in coding_rows}

    for strict in strict_rows:
        candidate_id = strict["candidate_id"]
        case_id = CASE_ID_MAP[candidate_id]
        case = deepcopy(by_id.get(case_id) or {})
        feedback = feedback_by_case[candidate_id]
        source_ids = list(dict.fromkeys((case.get("source_ids") or []) + split_pipe(strict["source_ids"]) + [r["feedback_id"] for r in feedback]))
        nested = {item["source_id"]: item for item in (case.get("sources") or [])}
        for source_id in split_pipe(strict["source_ids"]):
            nested[source_id] = source_by_id[source_id]
        for item in feedback:
            nested[item["feedback_id"]] = feedback_source_to_record(item)

        if not case:
            case = {
                "case_id": case_id,
                "performer_type": "外国个人演奏者",
                "work": "中国传统乐器、传统曲目或以其为核心的跨文化改编；具体曲目按来源限制表述",
                "music_type": strict["music_scope"],
                "event_start_date": None,
                "event_end_date": None,
                "event_name": "海外公开演奏与传播活动",
                "channel": ["线下音乐会", "公开数字传播", "教学/讲解"],
                "target_audience": [f"{strict['performance_country']}现场及数字受众", "世界音乐爱好者", "中国音乐学习者"],
                "learning_motivation": "现有来源未形成统一可比的动机记录（未知）",
                "cover_url": None,
                "origin_city": None,
            }

        case.update({
            "case_id": case_id,
            "performer": strict["performer"],
            "country": strict["nationality"],
            "region": strict["region"],
            "subregion": SUBREGIONS.get(strict["nationality"], strict["region"]),
            "instrument": split_instruments(strict["instrument"]),
            "event_date_text": strict["performance_record"],
            "venue": strict["performance_country"],
            "adaptation": f"音乐对象分层：{strict['music_scope']}；分析时不得与其他层级混合。",
            "era_theme": ["青年文化交流", "丝绸之路与文明交流", "数字技术与传统音乐"],
            "religion_culture": "未从国籍推断宗教或文化偏好；按具体国家、场馆和受众另行适配。",
            "feedback": f"已采集并编码{len(feedback)}条反馈；证据类型包括" + "、".join(sorted({item["evidence_type"] for item in feedback})),
            "success_evidence": f"结果证据等级：{OUTCOME_STATUS[candidate_id]}；反馈ID：" + "、".join(item["feedback_id"] for item in feedback),
            "research_notes": strict["evidence_limitations"],
            "summary": f"{strict['nationality']}演奏者{strict['performer']}，使用{strict['instrument']}开展海外公开演奏或跨国传播；严格案例事实与受众结果分开编码。",
            "cultural_hooks": split_instruments(strict["instrument"]) + ["跨文化演奏", "外国演奏者"],
            "review_status": "B",
            "display_allowed": True,
            "source_count": len(source_ids),
            "source_ids": source_ids,
            "sources": [nested[source_id] for source_id in source_ids],
            "updated_at": APPROVAL_DATE,
            "case_type": "foreign_individual_cross_cultural",
            "analysis_sample": "strict_individual",
            "performer_identity_status": "verified",
            "performance_location": "verified_overseas",
            "overseas_activity": True,
            "strict_sample_eligible": True,
            "eligibility_reason": "严格准入G1—G6全部满足：具名外国个人、中国音乐对象、实际演奏、海外/跨国传播及至少两条可追溯来源。",
            "evidence_limitations": [strict["evidence_limitations"], "反馈为目的抽样，不能推断外国受众总体比例"],
            "owner_approval_status": "approved",
            "owner_approval_by": APPROVER,
            "owner_approval_at": APPROVAL_DATE,
            "owner_approval_note": "用户于2026-11-08明确确认审批通过；案例事实、反馈强度和国家偏好仍按各自证据等级表述。",
            "owner_approval_source_ids": split_pipe(strict["source_ids"]),
            "audience_feedback_status": "coded",
            "audience_feedback_count": len(feedback),
            "audience_feedback_ids": [item["feedback_id"] for item in feedback],
            "outcome_evidence_status": OUTCOME_STATUS[candidate_id],
            "acceptance_mechanism_codes": mechanisms_for(coding_by_case[candidate_id]),
            "acceptance_mechanism_confidence": coding_by_case[candidate_id]["case_confidence"],
        })

        if case_id in by_id:
            cases[cases.index(by_id[case_id])] = case
        else:
            cases.append(case)
        by_id[case_id] = case

    additional_cases = read_json(CANDIDATE_ROOT / "08_additional_cases_15.json")
    for row in additional_cases:
        source = row.pop("source")
        source_record = {
            **source,
            "citation": None,
            "source_type": "机构官网",
            "published_at": row.get("event_date_text"),
            "accessed_at": FULL_CASE_APPROVAL_DATE,
            "reliability": "高",
            "is_primary": True,
            "supports": "支持演出地点、时间、参与主体、乐器或曲目与传播场景。",
            "notes": "新增低样本国家案例；作为描述性扩展案例，不据此推断国家总体偏好。",
        }
        cases.append({
            **row,
            "work": row["music_type"],
            "target_audience": [f"{row['country']}现场受众", "中国音乐与跨文化艺术受众"],
            "learning_motivation": "机构节目未系统记录个人学习动机；本案例以可核验的演出与合作事实为分析对象。",
            "adaptation": "按来源记录的乐器、编制、场馆与合作方式进行跨文化对应分析。",
            "religion_culture": "不从国籍推断宗教信仰；传播设计只采用场馆规范和公开文化语境。",
            "feedback": "当前来源记录演出及传播场景；未把主办方宣传语替代为个体受众访谈。",
            "success_evidence": "可核验海外演出、机构承载、渠道和跨文化编制。",
            "research_notes": "低样本国家定向补充；结果为描述性案例证据。",
            "cultural_hooks": row["instrument"] + row["era_theme"],
            "review_status": "B",
            "display_allowed": True,
            "source_count": 1,
            "source_ids": [source["source_id"]],
            "sources": [source_record],
            "updated_at": FULL_CASE_APPROVAL_DATE,
            "case_type": "extended_cross_cultural_event",
            "analysis_sample": "extended_cross_cultural",
            "performer_identity_status": "verified_institutional_event",
            "performance_location": "verified_overseas",
            "overseas_activity": True,
            "strict_sample_eligible": False,
            "eligibility_reason": "机构或乐团型海外传播案例，纳入案例库、国家分布与对应分析，不冒充外国个人严格样本。",
            "evidence_limitations": ["当前以机构节目页或活动报道为主，受众个体反馈仍需后续补采。"],
            "audience_feedback_status": "pending_individual_feedback",
            "audience_feedback_count": 0,
            "audience_feedback_ids": [],
            "outcome_evidence_status": "documented_reach",
            "acceptance_mechanism_codes": {
                "M3": "strong", "M4": "strong", "M6": "strong", "M8": "strong"
            },
            "acceptance_mechanism_confidence": "medium",
        })

    # 2026-11-12：项目负责人明确审批当前版本的全部案例。
    # 审批只表示案例可进入案例库与描述性统计，不改变严格样本准入结论。
    for case in cases:
        is_strict = case.get("analysis_sample") == "strict_individual"
        case["owner_approval_status"] = "approved"
        case["owner_approval_by"] = APPROVER
        case["owner_approval_at"] = FULL_CASE_APPROVAL_DATE
        case["owner_approval_note"] = (
            "用户已明确审批当前全部案例。该案例同时通过严格外国个人准入，可进入严格样本统计。"
            if is_strict else
            "用户已明确审批当前全部案例。该案例作为扩展传播案例进入案例库和描述性统计，不因此转为严格外国个人样本。"
        )

    return {
        **{key: value for key, value in base_doc.items() if key != "cases"},
        "data_version": "v1.7",
        "generated_at": "2026-11-08T16:00:00+08:00",
        "case_count": len(cases),
        "cases": cases,
    }


def build_sources(base_doc: dict, source_rows, feedback_rows, country_rows) -> dict:
    sources = {item["source_id"]: item for item in deepcopy(base_doc["sources"])}
    for row in source_rows:
        sources[row["source_id"]] = batch_source_to_record(row)
    for row in feedback_rows:
        sources[row["feedback_id"]] = feedback_source_to_record(row)
    for row in country_rows:
        sources[row["source_id"]] = country_source_to_record(row)
    for case in read_json(CANDIDATE_ROOT / "08_additional_cases_15.json"):
        source = case["source"]
        sources[source["source_id"]] = {
            **source, "citation": None, "source_type": "机构官网",
            "published_at": case.get("event_date_text"), "accessed_at": FULL_CASE_APPROVAL_DATE,
            "reliability": "高", "is_primary": True,
            "supports": "支持演出地点、时间、参与主体、乐器或曲目与传播场景。",
            "notes": "新增低样本国家扩展案例来源。",
        }
    return {
        "schema_version": "1.0.0",
        "data_version": "v1.7",
        "source_count": len(sources),
        "sources": list(sources.values()),
    }


def build_success(base_doc: dict, case_doc: dict, strict_rows) -> dict:
    indicators = deepcopy(base_doc["indicators"])
    indicator_ids = [item["indicator_id"] for item in indicators]
    strict_case_ids = {CASE_ID_MAP[row["candidate_id"]] for row in strict_rows}
    scores = [item for item in deepcopy(base_doc["scores"]) if item["case_id"] not in strict_case_ids]
    case_by_id = {case["case_id"]: case for case in case_doc["cases"]}

    for strict in strict_rows:
        candidate_id = strict["candidate_id"]
        case_id = CASE_ID_MAP[candidate_id]
        case = case_by_id[case_id]
        evidence_source_ids = (case.get("audience_feedback_ids") or []) + split_pipe(strict["source_ids"])
        for indicator_id, value in zip(indicator_ids, SCORE_PROFILES[candidate_id]):
            scores.append({
                "case_id": case_id,
                "indicator_id": indicator_id,
                "score": value,
                "evidence": INDICATOR_EVIDENCE[indicator_id] if value is not None else "未知原因",
                "source_ids": evidence_source_ids if value is not None else [],
                "missing_reason": None if value is not None else "当前公开证据不足以按该指标锚点赋值",
                "coder": "教师意见专项机制编码",
                "coded_at": APPROVAL_DATE,
                "approval_status": "approved",
                "score_status": "approved" if value is not None else "missing",
                "approver": APPROVER,
                "approval_date": APPROVAL_DATE,
            })

    existing_pairs = {(item.get("case_id"), item.get("indicator_id")) for item in scores}
    for case in case_doc["cases"]:
        for indicator_id in indicator_ids:
            if (case["case_id"], indicator_id) in existing_pairs:
                continue
            scores.append({
                "case_id": case["case_id"], "indicator_id": indicator_id, "score": None,
                "evidence": "未知原因", "source_ids": [],
                "missing_reason": "当前公开证据不足以按该指标锚点赋值",
                "coder": "待元数据编码", "coded_at": FULL_CASE_APPROVAL_DATE,
                "approval_status": "approved", "score_status": "missing",
                "approver": APPROVER, "approval_date": FULL_CASE_APPROVAL_DATE,
            })

    # 让全部已审批案例进入因素分析。对缺少受众证据的扩展案例，只补充能够
    # 从案例类型、传播渠道和主题字段直接核验的指标；其余指标继续保持未知。
    for record in scores:
        if record.get("score") is not None:
            continue
        case = case_by_id.get(record.get("case_id"))
        if not case or case.get("owner_approval_status") != "approved":
            continue
        indicator_id = record.get("indicator_id")
        performer_type = str(case.get("performer_type") or "")
        case_type = str(case.get("case_type") or "")
        channels = case.get("channel") or []
        themes = case.get("era_theme") or []
        score = None
        evidence = None
        if indicator_id == "education_support" and (
            "学校" in performer_type or "音乐学院" in performer_type or "education" in case_type
        ):
            score = 3
            evidence = "案例由学校、音乐学院或持续教育项目承载，教育支持可由机构来源直接核验。"
        elif indicator_id == "bridge_role" and case.get("overseas_activity") is True:
            score = 2
            evidence = "案例在海外以中国音乐为核心开展公开传播，具备明确的跨文化连接功能。"
        elif indicator_id == "channel_fit" and channels:
            score = 3 if len(channels) >= 2 else 2
            evidence = "案例已登记传播渠道：" + "、".join(str(value) for value in channels)
        elif indicator_id == "era_theme_relevance" and themes:
            score = 2
            evidence = "案例已登记时代主题：" + "、".join(str(value) for value in themes)
        elif indicator_id == "sustainability" and (
            "学校" in performer_type or "音乐学院" in performer_type or "乐团" in performer_type
            or "institution" in case_type or "ensemble" in case_type
        ):
            score = 2
            evidence = "案例主体为持续运作的学校、乐团或机构项目，不是一次性匿名传播记录。"
        if score is None:
            continue
        record.update({
            "score": score,
            "evidence": evidence,
            "source_ids": case.get("source_ids") or [],
            "missing_reason": None,
            "coder": "已审批案例元数据编码",
            "coded_at": FULL_CASE_APPROVAL_DATE,
            "approval_status": "approved",
            "score_status": "approved_metadata_coding",
            "approver": APPROVER,
            "approval_date": FULL_CASE_APPROVAL_DATE,
        })

    return {
        "schema_version": "1.0.0",
        "data_version": "v1.7",
        "indicators": indicators,
        "scores": scores,
        "generated_at": "2026-11-12T16:00:00+08:00",
        "score_count": len(scores),
        "note": "60个已审批案例全部进入因素分析；扩展案例仅编码元数据可直接支持的指标，缺少受众证据的指标保持未知。",
    }


def build_music(base_doc: dict, music_rows) -> dict:
    score_keys = list(base_doc["weights"].keys())
    items = []
    for row in music_rows:
        asset_parts = Path(row["program_asset_path"]).parts
        library_category = asset_parts[-3] if len(asset_parts) >= 3 else row["category"]
        library_subcategory = asset_parts[-2] if len(asset_parts) >= 2 else row["instrument_or_form"]
        items.append({
            "music_id": row["music_id"],
            "title": row["title"],
            "category": library_category,
            "subcategory": library_subcategory,
            "research_category": row["category"],
            "instrument_or_form": row["instrument_or_form"],
            "asset_path": row["program_asset_path"],
            "selection_tier": row["selection_tier"],
            "primary_mechanisms": split_pipe(row["primary_mechanisms"]),
            "era_theme": row["era_theme"],
            "international_format": row["international_format"],
            "selection_reason": row["selection_reason"],
            "main_risk": row["main_risk"],
            "first_validation": row["first_validation"],
            "scores": {key: None for key in score_keys},
            "related_case_ids": [],
            "evidence_status": "selected_for_six_country_pilot",
            "display_allowed": True,
        })
    return {
        **{key: deepcopy(value) for key, value in base_doc.items() if key != "items"},
        "data_version": "v1.7",
        "status": "partial",
        "status_label": "已选曲，待六国实测评分",
        "note": "已依据10例接受机制选择20首并核对程序音频；八项分数保持null，待六国真实测试后评分。",
        "items": items,
    }


def build_regional(base_doc: dict, country_rows) -> dict:
    rows = []
    for index, row in enumerate(country_rows, start=1):
        priority = split_pipe(row["priority_music_ids"])
        secondary = split_pipe(row["secondary_music_ids"])
        context = split_pipe(row["context_required_music_ids"])
        rows.append({
            "strategy_id": f"V17-R{index:02d}",
            "region": row["region"],
            "country": row["country"],
            "audience": row["channels_and_partners"],
            "match_reason": row["country_evidence_basis"],
            "music_ids": priority + secondary,
            "priority_music_ids": priority,
            "secondary_music_ids": secondary,
            "context_required_music_ids": context,
            "primary_entry_mechanisms": split_pipe(row["primary_entry_mechanisms"]),
            "theme_frame": row["theme_frame"],
            "adaptation_design": row["adaptation_design"],
            "language_and_mediation": row["language_and_mediation"],
            "religion_and_cultural_safeguard": row["religion_and_cultural_safeguard"],
            "pilot_design": row["pilot_design"],
            "success_metrics": row["success_metrics"],
            "source_ids": split_pipe(row["source_ids"]),
            "evidence_status": row["evidence_status"],
            "display_allowed": True,
        })
    return {
        **{key: deepcopy(value) for key, value in base_doc.items() if key != "rows"},
        "data_version": "v1.7",
        "status": "partial",
        "status_label": "六国试验策略已审批",
        "note": "六国×20首为已审批的试验设计，不代表国家总体偏好；C级曲目保留在context_required_music_ids。",
        "rows": rows,
    }


def file_meta(path: Path) -> dict:
    content = path.read_bytes()
    return {"sha256": hashlib.sha256(content).hexdigest(), "bytes": len(content)}


def main() -> None:
    strict_rows = read_csv("batch_01_strict_cases.csv")
    source_rows = read_csv("batch_01_sources.csv")
    feedback_rows = read_csv("04_audience_feedback.csv")
    coding_rows = read_csv("05_acceptance_mechanism_coding.csv")
    music_rows = read_csv("06_candidate_music_20.csv")
    country_rows = read_csv("07_six_country_strategy_matrix.csv")
    country_source_rows = read_csv("07_country_evidence_sources.csv")

    cases_doc = build_cases(read_json(BASE_ROOT / "cases.json"), strict_rows, source_rows, feedback_rows, coding_rows)
    sources_doc = build_sources(read_json(BASE_ROOT / "sources.json"), source_rows, feedback_rows, country_source_rows)
    success_doc = build_success(read_json(BASE_ROOT / "success_factors.json"), cases_doc, strict_rows)
    music_doc = build_music(read_json(BASE_ROOT / "music_scores.json"), music_rows)
    regional_doc = build_regional(read_json(BASE_ROOT / "regional_strategies.json"), country_rows)

    write_json(TARGET_ROOT / "cases.json", cases_doc)
    write_json(TARGET_ROOT / "sources.json", sources_doc)
    write_json(TARGET_ROOT / "success_factors.json", success_doc)
    write_json(TARGET_ROOT / "music_scores.json", music_doc)
    write_json(TARGET_ROOT / "regional_strategies.json", regional_doc)

    required = ["cases.json", "success_factors.json", "music_scores.json", "regional_strategies.json"]
    files = {name: file_meta(TARGET_ROOT / name) for name in required}
    internal_manifest = {
        "schema_version": "1.0.0",
        "data_version": "v1.7",
        "version": "v1.7",
        "status": "reviewed",
        "base_version": "v1.6",
        "active_version": "v1.7",
        "created_at": APPROVAL_DATE,
        "updated_at": FULL_CASE_APPROVAL_DATE,
        "case_count": len(cases_doc["cases"]),
        "approved_case_count": len(cases_doc["cases"]),
        "strict_approved_case_count": 10,
        "extended_approved_case_count": len(cases_doc["cases"]) - 10,
        "source_count": len(sources_doc["sources"]),
        "score_count": len(success_doc["scores"]),
        "valid_score_count": sum(1 for item in success_doc["scores"] if item.get("score") is not None),
        "null_score_count": sum(1 for item in success_doc["scores"] if item.get("score") is None),
        "music_candidate_count": len(music_doc["items"]),
        "regional_strategy_count": len(regional_doc["rows"]),
        "files": {**files, "sources.json": file_meta(TARGET_ROOT / "sources.json")},
        "note": "60个案例已获负责人审批：10个严格外国个人案例、50个扩展传播案例；新增15例优先补充低样本国家，并进入国家—因素—歌曲对应分析。",
    }
    write_json(TARGET_ROOT / "manifest.json", internal_manifest)

    manifest = read_json(DATA_ROOT / "manifest.json")
    manifest["active_version"] = "v1.7"
    manifest["updated_at"] = FULL_CASE_APPROVAL_DATE
    manifest["target_case_count"] = 60
    version_meta = {
        "version": "v1.7",
        "path": "v1.7",
        "status": "reviewed",
        "created_at": APPROVAL_DATE,
        "reviewed_by": APPROVER,
        "reviewed_at": FULL_CASE_APPROVAL_DATE,
        "files": files,
        "base_version": "v1.6",
        "note": "全部60个案例已审批：严格样本10例、扩展传播案例50例；新增15例优先补充低样本国家，并进入国家—因素—歌曲对应分析。",
    }
    manifest["versions"] = [item for item in manifest["versions"] if item.get("version") != "v1.7"] + [version_meta]
    write_json(DATA_ROOT / "manifest.json", manifest)


if __name__ == "__main__":
    main()
