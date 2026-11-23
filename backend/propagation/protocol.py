"""六国首轮试验协议：测量工具、本地化清单、冻结与分配。

协议默认是 pending_approval，不会自动冻结。
"""

from __future__ import annotations

import hashlib
import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .research_data import ResearchBundle

PROTOCOL_VERSION = "IRP-SIX-COUNTRY-2026-V1"
COUNTRIES = ["日本", "泰国", "英国", "美国", "阿联酋", "巴西"]
LANGUAGES = {"日本": "ja", "泰国": "th", "英国": "en", "美国": "en", "阿联酋": "ar", "巴西": "pt-BR"}
TARGETS = {
    "per_variant_per_cell": 20,
    "per_cell": 40,
    "per_country_total": 120,
    "per_country_cells": 12,
}

MEASUREMENT_ITEMS = [
    {"id": "emotional_resonance", "label": "情绪共鸣", "source": "audience", "prompt_zh": "这段音乐在多大程度上触动了你的情绪？", "anchor_1": "完全没有情绪反应", "anchor_5": "强烈触动，愿意继续听或分享", "reverse": False, "required": True},
    {"id": "timbre_identity", "label": "音色辨识", "source": "audience", "prompt_zh": "你能多清楚地辨认出这种乐器/声音的独特音色？", "anchor_1": "听不出独特音色", "anchor_5": "音色非常独特且能描述", "reverse": False, "required": True},
    {"id": "melody_accessibility", "label": "旋律可进入性", "source": "audience", "prompt_zh": "旋律对你来说有多容易跟随和记住？", "anchor_1": "难以跟随或记住", "anchor_5": "很容易跟随，能哼出片段", "reverse": False, "required": True},
    {"id": "cultural_story", "label": "文化故事性", "source": "audience", "prompt_zh": "音乐和导赏让你理解了多少背后的文化故事？", "anchor_1": "完全没有理解", "anchor_5": "能清楚复述故事和背景", "reverse": False, "required": True},
    {"id": "adaptation_space", "label": "跨文化改编空间", "source": "audience", "prompt_zh": "你觉得这种音乐与当地音乐元素结合的空间有多大？", "anchor_1": "完全不适合结合", "anchor_5": "结合自然，愿意听更多", "reverse": False, "required": True},
    {"id": "visual_expressiveness", "label": "视觉表现力", "source": "audience", "prompt_zh": "提供的视觉呈现与音乐有多匹配、多有表现力？", "anchor_1": "视觉与音乐不匹配或没有视觉材料", "anchor_5": "视觉显著增强音乐表现", "reverse": False, "required": True, "no_visual_rule": "没有视觉材料时记 missing，不补 3 分"},
    {"id": "era_theme_relevance", "label": "时代主题相关性", "source": "audience", "prompt_zh": "音乐与导赏提出的当代主题有多相关？", "anchor_1": "看不出关联", "anchor_5": "关联清晰且与我的当代经验相连", "reverse": False, "required": True},
    {"id": "existing_evidence", "label": "既有传播证据", "source": "researcher_evidence", "prompt_zh": "由研究人员依据来源编码，不向受众提问", "anchor_1": "无可核实传播证据", "anchor_5": "多来源、持续、可核实的传播记录", "reverse": False, "required": True},
]
AUXILIARY_ITEMS = [
    {"id": "prior_exposure", "label": "既往中国音乐接触", "values": ["none", "limited", "familiar"]},
    {"id": "save_share_intent", "label": "收藏/分享意愿", "scale": "1—5"},
    {"id": "learning_intent", "label": "学习参与意愿", "scale": "1—5"},
    {"id": "open_response", "label": "开放回答", "type": "text"},
]


def _root() -> Path:
    return Path(os.environ.get("PILOT_STORE_DIR") or Path(__file__).resolve().parents[2] / "research" / "candidates" / "v1.7-six-country-pilot")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _write(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)


def _read(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _digest(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def _audio_hashes(bundle: ResearchBundle) -> list[dict[str, Any]]:
    root = Path(__file__).resolve().parents[2]
    result = []
    for item in bundle.music_doc.get("items") or []:
        asset = str(item.get("asset_path") or "")
        path = root / asset
        result.append({
            "music_id": item.get("music_id"),
            "title": item.get("title"),
            "asset_path": asset,
            "asset_sha256": hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None,
            "asset_exists": path.exists(),
        })
    return result


def build_protocol(bundle: ResearchBundle, *, version: str = PROTOCOL_VERSION) -> dict[str, Any]:
    music = _audio_hashes(bundle)
    localization = []
    for country in COUNTRIES:
        localization.append({
            "country": country,
            "language": LANGUAGES[country],
            "source_language": "zh-CN",
            "title": None,
            "intro": None,
            "background_100": None,
            "consent": None,
            "questionnaire": None,
            "open_questions": None,
            "risk_notice": None,
            "recruitment": None,
            "operator_manual": None,
            "translator": None,
            "reviewer": None,
            "translation_status": "pending_native_review",
            "version": f"LOC-{version}-{LANGUAGES[country]}",
            "note": "本地语言材料待母语翻译与审校；不得把中文或机器草稿当作已审校文本。",
        })
    country_plan = []
    for row in bundle.regional_doc.get("rows") or []:
        if row.get("display_allowed") is not True:
            continue
        fits = row.get("fits") or {}
        country_plan.append({
            "country": row.get("country"),
            "region": row.get("region"),
            "a_count": len(row.get("priority_music_ids") or []),
            "b_count": len(row.get("secondary_music_ids") or []),
            "c_count": len(row.get("context_required_music_ids") or []),
            "priority_music_ids": row.get("priority_music_ids") or [],
            "secondary_music_ids": row.get("secondary_music_ids") or [],
            "context_required_music_ids": row.get("context_required_music_ids") or [],
            "note": "A/B/C是试验优先级，不是国家偏好。",
        })
    payload = {
        "protocol_version": version,
        "status": "pending_approval",
        "created_at": _now(),
        "approved_by": None,
        "approved_at": None,
        "research_lead": None,
        "music": music,
        "countries": COUNTRIES,
        "country_plan": country_plan,
        "design": {
            "type": "between_subject_single_version",
            "description": "每名参与者随机分配一首曲目和一个版本；原版/适配版按国家×曲目配额平衡。",
            "randomization": "SHA-256(seed|protocol|participant|country) 确定性分配；保存 seed 与分配日志。",
            "order_balance": "本轮为组间单版本设计；不以同一参与者内顺序平衡冒充组内对照。",
        },
        "targets": TARGETS,
        "inclusion": [
            "年满18岁并完成研究同意",
            "能够使用所在国语言完成问卷",
            "完成至少一次完整试听并提交",
        ],
        "exclusion": [
            "未同意",
            "重复 participant 编号",
            "完成率低于 70%",
            "缺失任一必填八项测量且无合规缺失规则",
            "试运行/演示数据",
        ],
        "measurement": {
            "items": MEASUREMENT_ITEMS,
            "auxiliary": AUXILIARY_ITEMS,
            "scale": "前七项 1—5；既有证据 0—100；正式聚合统一转 0—100",
            "reverse": "本版本无反向题；若新增反向题，必须在编码规则中先反向计分再转换",
            "missing": "缺失不补 3 分；视觉材料缺失时 visual_expressiveness 记 missing；任一必填项缺失则不进入正式评分",
            "no_visual_rule": "无适用视觉材料时 visual_expressiveness 保持 null，不补分",
        },
        "formula": {
            "survey_conversion": "(mean_1_5 - 1) / 4 × 100",
            "score": "Σ(survey_100_i × 0.125) + evidence_0_100 × 0.125",
            "range": "0—100；越界报错，不截断",
            "evidence": "必须来自经审批证据分，不由受众填写",
        },
        "analysis": {
            "within_country": "按国家×曲目×版本统计 n、均值、标准差、有效率、原版/适配差异",
            "cross_country": "先国家内聚合，再对国家等权；权重规则须在评分版本中固定",
            "ranking": "只有 active/published 版本且八项完整的单元进入排名",
        },
        "localization": localization,
        "ethics": [
            "不从国籍推断宗教、价值观或音乐偏好",
            "阿联酋场景审查宗教符号、服饰、舞蹈和娱乐场景",
            "日本、泰国等文化接近地区不假定天然理解",
            "不使用刻板印象或本质化国家性格",
            "退出研究的数据不进入分析",
        ],
        "note": "协议为候选稿；研究负责人审批后才可冻结。本地化材料未完成母语审校前不得正式招募。",
    }
    payload["sha256"] = _digest({k: v for k, v in payload.items() if k not in {"sha256"}})
    return payload


def save_protocol(protocol: dict[str, Any]) -> dict[str, Any]:
    _write(_root() / "protocol" / f"{protocol['protocol_version']}.json", protocol)
    return protocol


def current_protocol() -> dict[str, Any] | None:
    root = _root() / "protocol"
    if not root.exists():
        return None
    active_path = root / "active.json"
    if active_path.exists():
        active = _read(active_path)
        version_path = root / f"{active.get('protocol_version')}.json"
        if version_path.exists():
            doc = _read(version_path)
            if doc.get("sha256") == active.get("sha256"):
                return doc
    files = sorted(
        (path for path in root.glob("*.json") if path.name != "active.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    return _read(files[0]) if files else None


def approve_protocol(version: str, approver: str) -> dict[str, Any]:
    path = _root() / "protocol" / f"{version}.json"
    if not path.exists():
        raise FileNotFoundError(version)
    doc = _read(path)
    if doc.get("status") == "frozen":
        return doc
    doc.update({"status": "frozen", "approved_by": approver or "unknown", "approved_at": _now()})
    doc["sha256"] = _digest({k: v for k, v in doc.items() if k not in {"sha256"}})
    _write(path, doc)
    _write(_root() / "protocol" / "active.json", {"protocol_version": version, "sha256": doc["sha256"]})
    return doc


def _localization_path(protocol_version: str, country: str) -> Path:
    if country not in COUNTRIES:
        raise ValueError("国家不在六国范围内")
    return _root() / "localization" / protocol_version / f"{country}.json"


def build_localization_source(bundle: ResearchBundle, protocol_version: str, country: str, actor: str) -> dict[str, Any]:
    """生成中文母版和待填写的本地语言包；不伪造翻译或母语审校。"""
    protocol_path = _root() / "protocol" / f"{protocol_version}.json"
    if not protocol_path.exists():
        raise FileNotFoundError(protocol_version)
    protocol_doc = _read(protocol_path)
    if protocol_doc.get("status") != "frozen":
        raise ValueError("协议尚未冻结，不能生成本地化母版")
    strategy = next(
        (row for row in (bundle.regional_doc.get("rows") or []) if row.get("country") == country),
        {},
    )
    audience_items = [item for item in MEASUREMENT_ITEMS if item.get("source") == "audience"]
    source_zh = {
        "title": f"中国传统音乐受众研究（{country}测试）",
        "intro": "本研究比较中国传统音乐原版与适配版的理解、情绪和传播接受情况。参与完全自愿，回答只用于研究分析。",
        "background_100": f"本轮以{strategy.get('theme_frame') or '跨文化理解与音乐交流'}为导赏框架。A/B/C仅表示试验安排，不代表任何国家或个人的固定偏好。",
        "consent": "我已年满18岁，理解研究目的、数据用途和退出权利；我同意以去标识化方式记录试听与问卷数据，并可在提交后申请撤回。",
        "questionnaire": [
            {
                "id": item["id"],
                "prompt": item["prompt_zh"],
                "anchor_1": item["anchor_1"],
                "anchor_5": item["anchor_5"],
            }
            for item in audience_items
        ],
        "open_questions": [
            "你最喜欢或最不理解的部分是什么？为什么？",
            "这段音乐让你联想到哪些文化、场景或当代主题？",
            "是否有任何宗教、文化或呈现方式令你感到不适或容易误解？",
        ],
        "risk_notice": strategy.get("religion_and_cultural_safeguard") or "不得从国籍推断个人宗教、价值观或音乐偏好。",
        "recruitment": "招募年满18岁、能够使用测试语言完成试听和问卷的参与者。既往是否接触中国音乐均可，但必须如实记录。",
        "operator_manual": [
            "确认参与者阅读并同意知情同意文本后再创建分配。",
            "不得替参与者选择曲目或版本，不得透露研究假设。",
            "记录开始、播放、完成和提交事件；技术故障单独标记。",
            "参与者退出后立即执行撤回，不得继续纳入分析。",
            "正式数据、试运行数据和演示数据必须分别标记。",
        ],
    }
    payload = {
        "protocol_version": protocol_version,
        "protocol_sha256": protocol_doc.get("sha256"),
        "country": country,
        "language": LANGUAGES[country],
        "source_language": "zh-CN",
        "localization_version": f"LOC-{protocol_version}-{LANGUAGES[country]}-V1",
        "status": "source_ready",
        "source_zh": source_zh,
        "translations": {key: ([] if isinstance(value, list) else None) for key, value in source_zh.items()},
        "translator": None,
        "submitted_at": None,
        "reviewer": None,
        "reviewed_at": None,
        "created_by": actor,
        "created_at": _now(),
        "history": [{"at": _now(), "action": "source_created", "by": actor}],
    }
    payload["sha256"] = _digest({key: value for key, value in payload.items() if key != "sha256"})
    return payload


def ensure_localization_sources(bundle: ResearchBundle, protocol_version: str, actor: str) -> list[dict[str, Any]]:
    result = []
    for country in COUNTRIES:
        path = _localization_path(protocol_version, country)
        if path.exists():
            result.append(_read(path))
            continue
        item = build_localization_source(bundle, protocol_version, country, actor)
        _write(path, item)
        result.append(item)
    return result


def localization_overview(protocol_version: str | None = None) -> dict[str, Any]:
    if not protocol_version:
        current = current_protocol() or {}
        protocol_version = str(current.get("protocol_version") or "")
    items = []
    if protocol_version:
        for country in COUNTRIES:
            path = _localization_path(protocol_version, country)
            if path.exists():
                items.append(_read(path))
            else:
                items.append({
                    "protocol_version": protocol_version,
                    "country": country,
                    "language": LANGUAGES[country],
                    "status": "not_created",
                    "localization_version": None,
                    "translator": None,
                    "reviewer": None,
                    "sha256": None,
                })
    counts = {status: sum(1 for item in items if item.get("status") == status) for status in (
        "not_created", "source_ready", "pending_native_review", "approved", "revoked",
    )}
    return {
        "protocol_version": protocol_version or None,
        "items": items,
        "counts": counts,
        "recruitment_ready": bool(items) and all(item.get("status") == "approved" for item in items),
        "note": "只有六国本地化材料全部经过母语审校后，才允许启动正式招募。",
    }


def _validate_translations(translations: dict[str, Any]) -> None:
    text_fields = ("title", "intro", "background_100", "consent", "risk_notice", "recruitment")
    missing = [field for field in text_fields if not str(translations.get(field) or "").strip()]
    questions = translations.get("questionnaire")
    if not isinstance(questions, list) or len(questions) != 7:
        missing.append("questionnaire(7 items)")
    else:
        expected = {item["id"] for item in MEASUREMENT_ITEMS if item.get("source") == "audience"}
        actual = {str(item.get("id") or "") for item in questions if isinstance(item, dict)}
        if actual != expected or any(
            not all(str(item.get(key) or "").strip() for key in ("prompt", "anchor_1", "anchor_5"))
            for item in questions if isinstance(item, dict)
        ):
            missing.append("questionnaire content")
    for field in ("open_questions", "operator_manual"):
        values = translations.get(field)
        if not isinstance(values, list) or not values or any(not str(value).strip() for value in values):
            missing.append(field)
    if missing:
        raise ValueError("本地化材料不完整：" + "、".join(missing))


def submit_localization(protocol_version: str, country: str, translations: dict[str, Any], translator: str) -> dict[str, Any]:
    path = _localization_path(protocol_version, country)
    if not path.exists():
        raise FileNotFoundError(country)
    doc = _read(path)
    if doc.get("status") == "approved":
        raise ValueError("已审批材料不可覆盖；请创建新的本地化版本")
    if not isinstance(translations, dict):
        raise ValueError("translations 必须是对象")
    _validate_translations(translations)
    doc.update({
        "translations": translations,
        "translator": translator,
        "submitted_at": _now(),
        "reviewer": None,
        "reviewed_at": None,
        "status": "pending_native_review",
    })
    doc.setdefault("history", []).append({"at": _now(), "action": "submitted_for_native_review", "by": translator})
    doc["sha256"] = _digest({key: value for key, value in doc.items() if key != "sha256"})
    _write(path, doc)
    return doc


def approve_localization(protocol_version: str, country: str, reviewer: str) -> dict[str, Any]:
    path = _localization_path(protocol_version, country)
    if not path.exists():
        raise FileNotFoundError(country)
    doc = _read(path)
    if doc.get("status") != "pending_native_review":
        raise ValueError("只有待母语审校材料可以审批")
    if doc.get("translator") == reviewer:
        raise ValueError("翻译者不能审批自己的本地化材料")
    doc.update({"status": "approved", "reviewer": reviewer, "reviewed_at": _now()})
    doc.setdefault("history", []).append({"at": _now(), "action": "native_review_approved", "by": reviewer})
    doc["sha256"] = _digest({key: value for key, value in doc.items() if key != "sha256"})
    _write(path, doc)
    return doc


def participant_code(raw: str) -> str:
    return "P-" + hashlib.sha256(f"pilot-participant|{raw}".encode("utf-8")).hexdigest()[:16].upper()


def _assignment_rows() -> list[dict[str, Any]]:
    root = _root() / "assignments"
    return [_read(path) for path in root.glob("*.json")] if root.exists() else []


def create_assignment(
    protocol_version: str,
    participant_ref: str,
    country: str,
    *,
    consent: bool = False,
    seed: str = "2026-six-country",
    dataset_kind: str = "formal",
) -> dict[str, Any]:
    protocol = _read(_root() / "protocol" / f"{protocol_version}.json")
    if protocol.get("status") != "frozen":
        raise ValueError("协议尚未冻结，不能分配")
    if country not in COUNTRIES:
        raise ValueError("国家不在六国范围内")
    if not participant_ref.strip():
        raise ValueError("participant_ref 必填")
    if consent is not True:
        raise ValueError("未完成研究同意，不能开始正式采集")
    if dataset_kind not in {"formal", "pilot_rehearsal", "demo"}:
        raise ValueError("dataset_kind 只能是 formal/pilot_rehearsal/demo")
    localization_path = _localization_path(protocol_version, country)
    localization = _read(localization_path) if localization_path.exists() else {}
    if localization and localization.get("protocol_sha256") != protocol.get("sha256"):
        raise ValueError("本地化材料绑定的协议摘要与当前冻结协议不一致")
    if dataset_kind == "formal" and localization.get("status") != "approved":
        raise ValueError("该国家本地化材料尚未完成母语审校，不能正式招募")
    if dataset_kind == "pilot_rehearsal" and localization.get("status") not in {"pending_native_review", "approved"}:
        raise ValueError("试运行前至少需要提交完整本地化材料")
    code = participant_code(participant_ref)
    root = _root() / "assignments"
    existing_rows = _assignment_rows()
    for existing in existing_rows:
        if existing.get("participant_code") == code and existing.get("status") != "withdrawn":
            raise ValueError("该参与者已分配，不能重复提交")
    available_music = [item for item in protocol["music"] if item.get("asset_exists") is True]
    if not available_music:
        raise ValueError("协议没有可用音频，不能分配")
    counts = {
        (str(item["music_id"]), variant): 0
        for item in available_music for variant in ("original", "adapted")
    }
    for existing in existing_rows:
        key = (str(existing.get("music_id") or ""), str(existing.get("variant") or ""))
        if (
            existing.get("protocol_version") == protocol_version
            and existing.get("country") == country
            and existing.get("dataset_kind") == dataset_kind
            and existing.get("status") != "withdrawn"
            and key in counts
        ):
            counts[key] += 1
    minimum = min(counts.values())
    candidates = sorted(key for key, count in counts.items() if count == minimum)
    selector = int(hashlib.sha256(f"{seed}|{protocol_version}|{code}|{country}|{dataset_kind}".encode("utf-8")).hexdigest(), 16)
    music_id, variant = candidates[selector % len(candidates)]
    music = next(item for item in available_music if str(item.get("music_id")) == music_id)
    assignment = {
        "assignment_id": f"PA-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}",
        "protocol_version": protocol_version,
        "participant_code": code,
        "country": country,
        "music_id": music["music_id"],
        "title": music["title"],
        "variant": variant,
        "seed": seed,
        "assignment_hash": _digest({
            "seed": seed, "protocol": protocol_version, "participant": code,
            "country": country, "dataset_kind": dataset_kind, "music_id": music_id, "variant": variant,
        }),
        "status": "assigned",
        "created_at": _now(),
        "started_at": None,
        "played_at": None,
        "completed_at": None,
        "submitted_at": None,
        "completion_rate": None,
        "consent": True,
        "dataset_kind": dataset_kind,
        "localization_version": localization.get("localization_version"),
        "localization_sha256": localization.get("sha256"),
        "events": [{"at": _now(), "event": "assigned"}],
    }
    _write(root / f"{assignment['assignment_id']}.json", assignment)
    return assignment


def record_assignment_event(assignment_id: str, event: str, *, completion_rate: float | None = None) -> dict[str, Any]:
    path = _root() / "assignments" / f"{assignment_id}.json"
    if not path.exists():
        raise FileNotFoundError(assignment_id)
    doc = _read(path)
    if doc.get("status") == "withdrawn":
        raise ValueError("已退出分配不能继续记录事件")
    transitions = {
        "started": {"assigned"},
        "played": {"started"},
        "completed": {"played"},
        "submitted": {"completed"},
    }
    if event not in transitions:
        raise ValueError("event 只能是 started/played/completed/submitted")
    if doc.get("status") == event:
        return doc
    if doc.get("status") not in transitions[event]:
        raise ValueError(f"状态不能从 {doc.get('status')} 变为 {event}")
    if event == "completed":
        if completion_rate is None or not 0 <= float(completion_rate) <= 100:
            raise ValueError("completed事件必须提供0—100的completion_rate")
        doc["completion_rate"] = round(float(completion_rate), 2)
    timestamp = _now()
    doc["status"] = event
    doc[f"{event}_at"] = timestamp
    doc.setdefault("events", []).append({"at": timestamp, "event": event, "completion_rate": completion_rate})
    _write(path, doc)
    return doc


def withdraw_assignment(assignment_id: str) -> dict[str, Any]:
    path = _root() / "assignments" / f"{assignment_id}.json"
    if not path.exists():
        raise FileNotFoundError(assignment_id)
    doc = _read(path)
    timestamp = _now()
    doc.update({"status": "withdrawn", "withdrawn_at": timestamp})
    doc.setdefault("events", []).append({"at": timestamp, "event": "withdrawn"})
    _write(path, doc)
    return doc


def assignment_counts() -> dict[str, Any]:
    rows = _assignment_rows()
    if not rows:
        return {"total": 0, "active": 0, "withdrawn": 0, "by_country": {}, "by_status": {}, "by_variant": {}, "cells": []}
    by_country: dict[str, int] = {}
    by_status: dict[str, int] = {}
    by_variant: dict[str, int] = {}
    cells: dict[tuple[str, str], dict[str, Any]] = {}
    for row in rows:
        status = str(row.get("status") or "unknown")
        by_status[status] = by_status.get(status, 0) + 1
        if row.get("status") != "withdrawn":
            country = str(row.get("country") or "")
            variant = str(row.get("variant") or "")
            music_id = str(row.get("music_id") or "")
            by_country[country] = by_country.get(country, 0) + 1
            by_variant[variant] = by_variant.get(variant, 0) + 1
            cell = cells.setdefault((country, music_id), {
                "country": country, "music_id": music_id, "original": 0, "adapted": 0,
            })
            if variant in {"original", "adapted"}:
                cell[variant] += 1
    cell_rows = list(cells.values())
    return {
        "total": len(rows),
        "active": sum(1 for row in rows if row.get("status") != "withdrawn"),
        "withdrawn": sum(1 for row in rows if row.get("status") == "withdrawn"),
        "by_country": by_country,
        "by_status": by_status,
        "by_variant": by_variant,
        "cells": cell_rows,
        "imbalanced_cells": sum(1 for cell in cell_rows if abs(cell["original"] - cell["adapted"]) > 1),
    }
