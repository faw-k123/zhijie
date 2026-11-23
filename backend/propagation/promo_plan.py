"""P7 区域传播方案生成器（规则模板，不调用 LLM）。

设计原则：
- 已有证据：只来自 P2/P6 的评分、案例、区域策略；
- 策略建议：根据用户输入和已有信息生成，必须标注“建议”；
- 待验证假设：没有数据支持的判断，必须给验证方式；
- 证据缺口：明确写出当前不能生成的模块；
- 不虚构受众偏好、文化禁忌、宗教注意事项或效果提升百分比。
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from .research_analytics import build_music_context, build_sample, build_success_factors, eligible_cases
from .research_data import ResearchBundle

REQUIRED_INPUTS = (
    "title",
    "target_country",
    "target_city",
    "target_audience",
    "age_range",
    "purpose",
    "platform",
    "content_format",
    "adaptation_allowed",
    "budget_range",
    "duration",
    "language",
)

ADAPTATION_VALUES = {"yes", "no", "undecided"}

THEME_BY_PURPOSE = {
    "文化交流": "文明交流",
    "非遗传播": "非遗保护",
    "青年交流": "青年文化交流",
    "旅游推广": "城市化与传统记忆",
    "教育推广": "非遗保护",
    "商业发布": "数字技术与传统音乐",
}


def validate_plan_inputs(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for key in REQUIRED_INPUTS:
        value = payload.get(key)
        if value is None or not str(value).strip():
            errors.append(key)
    adaptation = str(payload.get("adaptation_allowed") or "").strip().lower()
    if adaptation and adaptation not in ADAPTATION_VALUES:
        errors.append("adaptation_allowed")
    return errors


def _text(value: Any, default: str = "未提供") -> str:
    text = str(value or "").strip()
    return text or default


def _evidence(
    text: str,
    *,
    case_ids: list[str] | None = None,
    source_ids: list[str] | None = None,
    source_links: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return {
        "text": text,
        "case_ids": case_ids or [],
        "source_ids": source_ids or [],
        "source_links": source_links or [],
        "kind": "evidence",
    }


def _suggestion(text: str, basis: str) -> dict[str, Any]:
    return {"text": text, "basis": basis, "kind": "suggestion"}


def _hypothesis(text: str, validation: str) -> dict[str, Any]:
    return {"text": text, "validation": validation, "kind": "hypothesis"}


def _gap(text: str, action: str) -> dict[str, Any]:
    return {"text": text, "action": action, "kind": "gap"}


def _module(
    module_id: str,
    title: str,
    *,
    evidence: list[dict[str, Any]] | None = None,
    suggestions: list[dict[str, Any]] | None = None,
    hypotheses: list[dict[str, Any]] | None = None,
    gaps: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return {
        "id": module_id,
        "title": title,
        "evidence": evidence or [],
        "suggestions": suggestions or [],
        "hypotheses": hypotheses or [],
        "gaps": gaps or [],
    }


def _case_evidence(cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output = []
    for item in cases:
        source_ids = [str(s) for s in (item.get("source_ids") or [])]
        case_id = str(item.get("case_id") or "")
        output.append(
            _evidence(
                f"案例 {case_id}（{item.get('country') or '国家未知'}，"
                f"{'、'.join(item.get('instrument') or []) or '乐器未知'}）"
                f"可作为相关传播先例；编码均分 "
                f"{item.get('mean_score') if item.get('mean_score') is not None else '未知'} / 3。",
                case_ids=[case_id] if case_id else [],
                source_ids=source_ids,
                source_links=item.get("source_links") or [],
            )
        )
    return output


def build_promo_plan(bundle: ResearchBundle, payload: dict[str, Any]) -> dict[str, Any]:
    """根据输入与精确研究上下文生成 9 个结构化模块。"""
    title = _text(payload.get("title"))
    target_country = _text(payload.get("target_country"))
    target_city = _text(payload.get("target_city"))
    audience = _text(payload.get("target_audience"))
    age_range = _text(payload.get("age_range"))
    purpose = _text(payload.get("purpose"))
    platform = _text(payload.get("platform"))
    content_format = _text(payload.get("content_format"))
    adaptation = str(payload.get("adaptation_allowed") or "undecided").strip().lower()
    budget = _text(payload.get("budget_range"))
    duration = _text(payload.get("duration"))
    language = _text(payload.get("language"))
    origin_city = _text(payload.get("origin_city"), "") or None

    context = build_music_context(
        bundle,
        title=title,
        category=str(payload.get("category") or "").strip(),
        subcategory=str(payload.get("subcategory") or "").strip(),
        song_id=str(payload.get("song_id") or "").strip(),
    )
    potential = context.get("potential")
    cases = (
        context.get("related_cases")
        or context.get("matched_cases")
        or (context.get("global_reference") or {}).get("cases")
        or []
    )
    music_regional_rows = context.get("regional_rows") or []
    country_regional_rows = [
        row for row in (bundle.regional_doc.get("rows") or [])
        if row.get("display_allowed") is True and str(row.get("country") or "") == target_country
    ]
    regional_rows = [
        row for row in music_regional_rows if str(row.get("country") or "") == target_country
    ] or country_regional_rows
    sample = build_sample(bundle)

    country_factor_data = build_success_factors(bundle, analysis_sample="all", country=target_country)
    country_factors = sorted(
        [factor for factor in (country_factor_data.get("factors") or []) if factor.get("mean_score") is not None],
        key=lambda factor: (-float(factor["mean_score"]), int(factor.get("order") or 999)),
    )[:3]
    country_cases = [
        case for case in eligible_cases(bundle)
        if str(case.get("country") or "") == target_country
        and case.get("owner_approval_status") == "approved"
    ]
    country_case_ids = [str(case.get("case_id")) for case in country_cases]
    country_source_ids = list(dict.fromkeys(
        str(source_id)
        for case in country_cases for source_id in (case.get("source_ids") or [])
    ))

    source_ids: list[str] = []
    for item in cases:
        for source_id in item.get("source_ids") or []:
            if source_id not in source_ids:
                source_ids.append(source_id)
    for row in regional_rows:
        for source_id in row.get("source_ids") or []:
            if source_id not in source_ids:
                source_ids.append(source_id)

    evidence_summary = {
        "potential": {
            "status": "unregistered" if potential is None else potential.get("status"),
            "total_score": potential.get("total_score") if potential else None,
            "tier": (
                "未纳入候选曲实测" if potential is None
                else potential.get("tier") if potential.get("total_score") is not None
                else "待实测（已有案例参考）"
            ),
            "valid_count": potential.get("valid_count") if potential else 0,
        },
        "case_count": len(cases),
        "case_scope_label": context.get("factor_reference", {}).get("scope_label"),
        "country_case_count": len(country_cases),
        "country_factor_count": len(country_factors),
        "regional_count": len(regional_rows),
        "source_count": len(source_ids),
        "association": context.get("association"),
        "music_status": context.get("music_status"),
        "music_status_label": context.get("music_status_label"),
    }

    theme = THEME_BY_PURPOSE.get(purpose, "文明交流")

    music_profile_evidence: list[dict[str, Any]] = []
    if potential:
        profile_parts = [
            f"候选等级：{potential.get('selection_tier') or '未分级'}",
            f"时代主题：{potential.get('era_theme') or '未记录'}",
            f"国际呈现：{potential.get('international_format') or '未记录'}",
            f"选择依据：{potential.get('selection_reason') or '未记录'}",
        ]
        music_profile_evidence.append(_evidence("；".join(profile_parts)))
    country_factor_evidence: list[dict[str, Any]] = []
    if country_factors:
        factor_text = "、".join(
            f"{factor['label']} {factor['mean_score']}/3（有效n={factor['n']}）"
            for factor in country_factors
        )
        country_factor_evidence.append(_evidence(
            f"{target_country}现有{len(country_cases)}个已审批案例中，编码均值靠前的三项为：{factor_text}。这是案例内描述性结果。",
            case_ids=country_case_ids,
            source_ids=country_source_ids,
        ))
    adaptation_text = {
        "yes": "允许跨文化改编：建议在保留核心旋律与乐器辨识度的前提下，尝试与当地编制或视觉语言对话。",
        "no": "明确不允许改编：保持原编制、原演奏方式与核心段落，不做跨文化重构。",
        "undecided": "改编尚未决定：建议先做原版与轻改编两个小样，在小范围受众中测试后再决定。",
    }.get(adaptation, "改编策略未确定，建议先做小范围测试。")

    modules: list[dict[str, Any]] = []

    # 01 音乐与文化定位
    m01_evidence = []
    if potential and potential.get("valid_count", 0) > 0:
        m01_evidence.append(
            _evidence(
                f"该曲已有 {potential.get('valid_count', 0)} / 8 项音乐潜力评分；"
                f"综合得分 {'暂无' if potential.get('total_score') is None else potential.get('total_score')}，"
                f"分级「{potential.get('tier') or '资料不足'}」。"
            )
        )
    m01_evidence.extend(music_profile_evidence)
    m01_evidence.extend(_case_evidence(cases))
    m01_suggestions = [
        _suggestion(
            f"以《{title}》的曲目名称、乐器与音乐类型作为方案的第一层文化定位；"
            "所有背景说明先核对研究资料，再进入对外文案。",
            "基于用户输入的音乐名称与方案生成规则",
        )
    ]
    m01_hypotheses = []
    m01_gaps = []
    if origin_city:
        m01_suggestions.append(
            _suggestion(
                f"可将「{origin_city}」作为作品来源城市，围绕城市文化场景做辅助叙事；"
                "具体城市文化锚点、场景与来源仍需补充，不能仅凭城市名写文化判断。",
                "用户输入的作品来源城市",
            )
        )
        m01_hypotheses.append(
            _hypothesis(
                f"来源城市「{origin_city}」的叙事是否能提升目标受众的理解与兴趣，尚待验证。",
                "在试点内容中做 A/B 版本对比，并收集目标受众反馈。",
            )
        )
    else:
        m01_gaps.append(
            _gap(
                "未提供作品来源城市，暂不启用北京/上海城市叙事。",
                "如确有城市外宣需要，先补充来源城市与可核验的城市文化资料。",
            )
        )
    if not potential:
        m01_gaps.append(
            _gap(
                "当前曲目未纳入20首候选曲档案，无法给出候选等级和曲目画像。",
                "先建立曲目档案，再完成8项真实受众测试评分。",
            )
        )
    elif potential.get("valid_count", 0) == 0:
        m01_gaps.append(_gap(
            "当前曲目已有候选画像和案例参考，但8项真实受众测试尚未完成。",
            "保留现有案例证据用于方案设计，同时开展原版/适配版小样测试；不得把待实测写成没有任何资料。",
        ))

    modules.append(
        _module(
            "01_music_positioning",
            "音乐与文化定位",
            evidence=m01_evidence,
            suggestions=m01_suggestions,
            hypotheses=m01_hypotheses,
            gaps=m01_gaps,
        )
    )

    # 02 目标区域分析
    m02_evidence = list(country_factor_evidence)
    for row in regional_rows:
        m02_evidence.append(
            _evidence(
                f"{row.get('region') or target_country} / {row.get('country') or '国家待补'} 的已有策略："
                f"{row.get('match_reason') or '未记录适配理由'}",
                case_ids=[str(c) for c in (row.get("case_ids") or [])],
                source_ids=[str(s) for s in (row.get("source_ids") or [])],
            )
        )
    m02_suggestions = [
        _suggestion(
            f"在进入{target_city} / {target_country}前，由熟悉当地语言、宗教与习俗的本地顾问审阅文案、图像与活动形式。",
            "跨文化传播执行前的通用风控流程，不是对当地文化的具体判断",
        )
    ]
    m02_hypotheses = [
        _hypothesis(
            f"{target_country}目标受众对《{title}》相关内容的接受方式与关注点，尚待本地调查或试点验证。",
            "开展小样本受众访谈或试点内容测试，记录受众原话与参与行为。",
        )
    ]
    m02_gaps = []
    if not regional_rows and not country_factor_evidence:
        m02_gaps.append(
            _gap(
                "当前没有目标国家/区域的文化、宗教或习俗来源，不能生成具体禁忌清单或适配结论。",
                "补充该区域的文化背景与宗教习俗来源，并由本地顾问复核。",
            )
        )

    modules.append(
        _module(
            "02_target_region",
            "目标区域分析",
            evidence=m02_evidence,
            suggestions=m02_suggestions,
            hypotheses=m02_hypotheses,
            gaps=m02_gaps,
        )
    )

    # 03 目标受众分析
    modules.append(
        _module(
            "03_audience",
            "目标受众分析",
            evidence=country_factor_evidence + _case_evidence(cases[:3]),
            suggestions=[
                _suggestion(
                    f"将「{age_range} / {audience}」作为本次方案的受众假设，围绕其媒介习惯选择内容长度与互动方式。",
                    "用户输入的受众与年龄范围，不是研究结论",
                ),
                _suggestion(
                    f"首发内容优先适配「{platform}」的观看节奏，并准备一版更完整的「{content_format}」用于深度受众。",
                    "基于用户选择的平台与内容形式",
                ),
            ],
            hypotheses=[
                _hypothesis(
                    "该受众群体对曲目、乐器音色和文化故事的兴趣强度尚待验证。",
                    "用首轮内容的完播率、评论主题和主动搜索行为做探索性判断；不预设偏好。",
                )
            ],
            gaps=[
                _gap(
                    "当前没有该受众群体的问卷、访谈或平台行为数据。",
                    "补充受众调研，或把首轮发布当作探索性测试并记录反馈。",
                )
            ],
        )
    )

    # 04 音乐适配分析
    m04_evidence = []
    if potential and potential.get("valid_count", 0) > 0:
        m04_evidence.append(
            _evidence(
                f"音乐潜力当前为「{potential.get('tier') or '资料不足'}」，"
                f"有效评分 {potential.get('valid_count', 0)} / 8。"
            )
        )
    m04_evidence.extend(music_profile_evidence)
    m04_evidence.extend(_case_evidence(cases))
    if regional_rows:
        m04_evidence.append(
            _evidence(
                f"已有 {len(regional_rows)} 条区域策略明确包含该曲目。",
                case_ids=[str(c) for row in regional_rows for c in (row.get("case_ids") or [])],
                source_ids=[str(s) for row in regional_rows for s in (row.get("source_ids") or [])],
            )
        )
    m04_gaps = []
    if not potential and not cases and not regional_rows:
        m04_gaps.append(
            _gap(
                "没有该曲的评分、精确关联案例或区域策略，无法判断音乐与目标区域/受众的适配性。",
                "先完成单曲评分，并补充 related_case_ids 与区域策略的 music_ids。",
            )
        )
    modules.append(
        _module(
            "04_music_fit",
            "音乐适配分析",
            evidence=m04_evidence,
            suggestions=[
                _suggestion(
                    "把适配性拆成“音乐可听性、文化可解释性、场景可用性”三项，在首轮试点中分别收集反馈。",
                    "评估框架建议，不是对适配结果的断言",
                )
            ],
            hypotheses=[
                _hypothesis(
                    f"《{title}》与{target_country}目标受众的适配度尚待试点验证。",
                    "用同一内容的不同呈现版本做小样本测试，比较理解度与继续观看意愿。",
                )
            ],
            gaps=m04_gaps,
        )
    )

    # 05 跨文化表达策略
    m05_evidence = music_profile_evidence + _case_evidence(cases)
    modules.append(
        _module(
            "05_adaptation",
            "跨文化表达策略",
            evidence=m05_evidence,
            suggestions=[
                _suggestion(adaptation_text, "用户选择的改编许可 + 跨文化改编的通用原则"),
                _suggestion(
                    f"为{target_country}受众准备「{language}」的字幕或导赏，优先解释乐器音色、曲目意象和情绪，而不是堆叠历史知识。",
                    "基于输出语言与受众设定的表达建议",
                ),
            ],
            hypotheses=[
                _hypothesis(
                    "改编版本是否比原版更容易被目标受众理解，尚待对照测试。",
                    "准备原版与改编版两个小样，分别收集理解度、情绪反应和分享意愿。",
                )
            ],
            gaps=[] if cases else [
                _gap(
                    "当前没有与该曲精确关联的改编案例，改编方向只是原则建议。",
                    "补充相关案例或做小范围版本测试后再定稿。",
                )
            ],
        )
    )

    # 06 传播主题设计
    m06_evidence = list(music_profile_evidence)
    for case in cases:
        themes = [str(t) for t in (case.get("era_theme") or [])]
        if themes:
            m06_evidence.append(
                _evidence(
                    f"案例 {case.get('case_id')} 记录的主题：{'、'.join(themes)}。",
                    case_ids=[str(case.get("case_id"))],
                    source_ids=[str(s) for s in (case.get("source_ids") or [])],
                )
            )
    modules.append(
        _module(
            "06_theme",
            "传播主题设计",
            evidence=m06_evidence,
            suggestions=[
                _suggestion(
                    f"建议把本次传播主题聚焦为「{theme}」，用“音乐如何被听见、被理解、被参与”组织叙事；"
                    "这是主题建议，不是研究结论。",
                    f"用户传播目的「{purpose}」+ 研究主题词表",
                ),
                _suggestion(
                    f"核心宣传语控制在 1 句主张 + 3 个支撑点；{language}版本需由母语者复核，避免直译。",
                    "跨文化文案的通用执行建议",
                ),
            ],
            hypotheses=[
                _hypothesis(
                    f"「{theme}」这一主题在{target_country}受众中的共鸣强度尚待验证。",
                    "用同一素材的两个主题标题做 A/B 测试，观察点击、完播和评论主题。",
                )
            ],
            gaps=[] if m06_evidence else [
                _gap(
                    "当前没有与该曲关联的案例主题证据，主题建议来自研究框架与用户输入。",
                    "补充相关案例或做主题测试后再确定。",
                )
            ],
        )
    )

    # 07 渠道与内容规划
    m07_evidence = []
    for case in cases[:3]:
        channels = [str(value) for value in (case.get("channel") or [])]
        if channels:
            m07_evidence.append(
                _evidence(
                    f"案例 {case.get('case_id')} 已使用传播渠道：{'、'.join(channels)}。",
                    case_ids=[str(case.get("case_id"))],
                    source_ids=[str(value) for value in (case.get("source_ids") or [])],
                )
            )
    modules.append(
        _module(
            "07_channels",
            "渠道与内容规划",
            evidence=m07_evidence or (music_profile_evidence + _case_evidence(cases[:1])),
            suggestions=[
                _suggestion(
                    f"以「{platform}」为主渠道，首发「{content_format}」，配合{language}字幕或导赏；"
                    "发布节奏采用“预热—首发—互动—复盘”四段式。",
                    "用户选择的平台、内容形式与语言",
                ),
                _suggestion(
                    f"为{target_city}准备一版线下/本地化场景的延展内容；如果线下条件不具备，先保留为待验证方案。",
                    "目标城市输入 + 渠道组合建议",
                ),
            ],
            hypotheses=[
                _hypothesis(
                    f"「{platform}」是否是该受众的主要信息入口，尚待平台数据或受众调研验证。",
                    "首轮发布后记录来源渠道、完播与互动，不预设平台效率。",
                )
            ],
            gaps=[
                _gap(
                    "当前没有该目标区域的渠道效果数据。",
                    "用首轮小规模发布收集渠道数据，再调整主渠道。",
                )
            ],
        )
    )

    # 08 执行计划
    m08_evidence = []
    for row in regional_rows[:3]:
        m08_evidence.append(
            _evidence(
                f"已审批区域策略 {row.get('strategy_id') or '未编号'} 提供了目标受众、适配方式与试点执行依据。",
                source_ids=[str(value) for value in (row.get("source_ids") or [])],
            )
        )
    modules.append(
        _module(
            "08_execution",
            "执行计划",
            evidence=m08_evidence or (country_factor_evidence + music_profile_evidence + _case_evidence(cases[:1])),
            suggestions=[
                _suggestion(
                    f"按「{duration}」拆分为四段：准备与审校（约 25%）、内容制作（约 35%）、发布与互动（约 25%）、复盘（约 15%）。"
                    "百分比是排期建议，不是承诺。",
                    "用户输入的活动周期 + 通用项目管理框架",
                ),
                _suggestion(
                    f"预算档位为「{budget}」；在活动规模、制作规格和本地合作方确定前，不虚构具体金额或分配比例。",
                    "用户输入的预算范围",
                ),
            ],
            hypotheses=[
                _hypothesis(
                    "当前周期与预算档位是否足以完成一次有效试点，尚待执行前复核。",
                    "在启动会中确认制作、翻译、审校、投放和线下执行的实际成本。",
                )
            ],
            gaps=[
                _gap(
                    "没有历史项目成本与排期数据，无法给出精确预算表。",
                    "补充同类项目成本或向执行方询价后再细化。",
                )
            ],
        )
    )

    # 09 效果评估
    modules.append(
        _module(
            "09_evaluation",
            "效果评估",
            evidence=country_factor_evidence + _case_evidence(cases[:3]),
            suggestions=[
                _suggestion(
                    "建议同时记录过程指标（触达、完播、互动、媒体转载）与理解指标（评论主题、问卷、访谈），"
                    "不要只看播放量。",
                    "传播效果评估框架建议",
                ),
                _suggestion(
                    "设置试点前基线、试点后复测和受众原话摘录；所有效果判断标注样本量与采集日期。",
                    "研究数据可追溯原则",
                ),
            ],
            hypotheses=[
                _hypothesis(
                    "本方案是否能提升理解或参与，尚待试点前后对比；不预设提升百分比。",
                    "采用试点前后对照或小范围 A/B 测试，报告样本、时间和不确定性。",
                )
            ],
            gaps=[
                _gap(
                    "当前没有该曲/该区域的历史传播基线数据。",
                    "在活动前采集基线，活动后按同一口径复测。",
                )
            ],
        )
    )

    counts = {
        "evidence": sum(len(module["evidence"]) for module in modules),
        "suggestions": sum(len(module["suggestions"]) for module in modules),
        "hypotheses": sum(len(module["hypotheses"]) for module in modules),
        "gaps": sum(len(module["gaps"]) for module in modules),
    }

    return {
        "meta": {
            "plan_id": f"PLAN-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{uuid4().hex[:6]}",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "generation_mode": "rule_template",
            "ai_generated": False,
            "data_version": bundle.version,
            "module_count": len(modules),
            "inputs": {
                "title": title,
                "target_country": target_country,
                "target_city": target_city,
                "target_audience": audience,
                "age_range": age_range,
                "purpose": purpose,
                "platform": platform,
                "content_format": content_format,
                "adaptation_allowed": adaptation,
                "budget_range": budget,
                "duration": duration,
                "language": language,
                "origin_city": origin_city,
            },
        },
        "sample": sample,
        "evidence_summary": evidence_summary,
        "counts": counts,
        "modules": modules,
        "warnings": context.get("warnings") or [],
        "disclaimer": (
            "本方案由规则模板生成，不调用大模型。"
            "“已有证据”只来自已审核研究数据；“策略建议”和“待验证假设”不是研究结论。"
            "文化、宗教、受众偏好和效果提升均需本地调查、试点或人工审核，不得当作事实。"
        ),
    }
