"""
歌曲意象解析模块（Django 应用：imagery）

HTTP 路由仍由 api.views / api.urls 统一对外暴露；
本应用只承载业务实现。

流程（对齐 test_query.cypher）：
1. 用户七大元素占比 → 匹配文化圈层（余弦相似度 Top1）
2. 【反向】场景标签(N) + 事物标签(T) → 该圈层下可能触发的情感(F)
3. 【正向】情感标签(F) → 该圈层下常触发这些情感的场景(N)与事物(T)
4. 把 2) + 3) 两大结果包装成提示词，调用 IMAGERY_AI 生成解释文案返回前端

测试开关（IMAGERY_TEST_MODE）：
- True  → 前端可下发 circle_override，强制圈层做对比演示
- False → 按用户七大元素自动匹配圈层
结果经缓冲池返回前端；未命中时计算并写入缓冲池。

配置见 config.services：IMAGERY_NEO4J / IMAGERY_AI / IMAGERY_TEST_MODE
"""

from __future__ import annotations

import json
import threading
import time
from typing import Any, Optional

import requests
from neo4j import Driver, GraphDatabase

from config import services as svc_config

# ---------------------------------------------------------------------------
# Neo4j Driver（意象专用；严格只读 IMAGERY_NEO4J，连不上直接报错，不回退其它库）
# ---------------------------------------------------------------------------
_imagery_driver: Optional[Driver] = None


def _get_imagery_driver() -> Driver:
    global _imagery_driver
    if _imagery_driver is not None:
        return _imagery_driver
    cfg = svc_config.IMAGERY_NEO4J or {}
    uri = (cfg.get('URI') or '').strip()
    if not uri:
        raise RuntimeError('意象 Neo4j 未配置：请填写 config.services.IMAGERY_NEO4J')
    user = cfg.get('USER', 'neo4j')
    password = cfg.get('PASSWORD', '')
    _imagery_driver = GraphDatabase.driver(uri, auth=(user, password))
    return _imagery_driver


def _get_imagery_database() -> str:
    return (svc_config.IMAGERY_NEO4J or {}).get('DATABASE', 'neo4j')


def _run_cypher(query: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    driver = _get_imagery_driver()
    database = _get_imagery_database()
    with driver.session(database=database) as session:
        result = session.run(query, params or {})
        return [dict(record) for record in result]


# ---------------------------------------------------------------------------
# 用户圈层属性（七大元素占比）
# TODO【待接入网页用户数据库】：按 user_id 查询用户七大元素占比列表
# 当前返回固定占位值，仅用于联调圈层匹配与后续查询。
# ---------------------------------------------------------------------------
# 顺序对应 Factor F1~F7（宗教信仰/生计生态/社会制度/族群血脉/历史时段/阶层生活/审美艺术）
_FIXED_USER_FACTORS = [35, 20, 30, 15, 0, 0, 0]
_FIXED_USER_COUNTRY = '中国'

# 常用圈层 → 默认国家（其余圈层 country 置空，图查询不过滤国家）
_CIRCLE_DEFAULT_COUNTRY: dict[str, str] = {
    '东亚文化圈': '中国',
    '中华文化圈': '中国',
    '朝鲜半岛文化圈': '韩国',
    '日本文化圈': '日本',
    '哈萨克斯坦草原文化圈层': '哈萨克斯坦',
    '苏联集体主义/工农兵圈层': '俄罗斯',
}


def _normalize_circle_override(raw: Any) -> tuple[str | None, str]:
    """
    规范 circle_override。
    返回 (circle_name_or_None, source)：
    - None + 'missing'：请求未提供，可读配置默认
    - '' + source：真实属性计算（auto/0）
    - 圈层名 + source：强制该圈层
    """
    if raw is None:
        return None, 'missing'
    if isinstance(raw, (int, float)) and not isinstance(raw, bool):
        n = int(raw)
        if n <= 0:
            return '', 'request'
        id_map = getattr(svc_config, 'TEST_CIRCLE_ID_TO_NAME', {}) or {}
        name = id_map.get(n) or ''
        return (name if name else ''), 'request'
    s = str(raw).strip()
    if not s:
        return None, 'missing'
    low = s.lower()
    if low in ('auto', 'real', 'none', '0'):
        return '', 'request'
    if s.isdigit():
        n = int(s)
        if n <= 0:
            return '', 'request'
        id_map = getattr(svc_config, 'TEST_CIRCLE_ID_TO_NAME', {}) or {}
        return (id_map.get(n) or ''), 'request'
    return s, 'request'


def _resolve_test_circle_override(request_override: Any = None) -> dict[str, Any]:
    """
    解析测试圈层覆盖。

    仅当 IMAGERY_TEST_MODE=True 且指定了有效圈层名时 enabled=True。
    优先级：请求参数 circle_override（圈层名或 1~5）> 配置 IMAGERY_TEST_CIRCLE_OVERRIDE。
    请求显式传 auto/0 → 真实属性计算（不覆盖）。
    """
    test_mode = bool(getattr(svc_config, 'IMAGERY_TEST_MODE', False))
    if not test_mode:
        return {'enabled': False, 'override': '', 'circle': '', 'country': '', 'source': 'test_off'}

    circle_name, src = _normalize_circle_override(request_override)
    if circle_name is None:
        # 未传参：回退配置编号 0~5
        cfg = int(getattr(svc_config, 'IMAGERY_TEST_CIRCLE_OVERRIDE', 0) or 0)
        id_map = getattr(svc_config, 'TEST_CIRCLE_ID_TO_NAME', {}) or {}
        circle_name = id_map.get(cfg) or ''
        src = 'config_default'

    if not circle_name:
        return {
            'enabled': False,
            'override': '',
            'circle': '',
            'country': '',
            'source': src,
        }

    country = _CIRCLE_DEFAULT_COUNTRY.get(circle_name, '')
    return {
        'enabled': True,
        'override': circle_name,
        'circle': circle_name,
        'country': country,
        'source': src,
    }


def get_user_circle_factors(user_id: str = '') -> dict[str, Any]:
    """
    查询当前用户的圈层属性（七大元素占比）与国家。

    TODO【待接入网页用户数据库】：
    - 用 user_id 查用户画像 / 圈层问卷结果
    - 返回真实的 factors(list[float|int] 长度7) 与 country
    """
    _ = user_id  # 占位：接入用户库后使用
    return {
        'user_id': user_id or 'guest',
        'factors': list(_FIXED_USER_FACTORS),
        'country': _FIXED_USER_COUNTRY,
        'source': 'fixed_placeholder',
        'message': '占位：用户圈层属性尚未接入用户库，当前返回固定七大元素占比',
    }


# ---------------------------------------------------------------------------
# Cypher：三步查询（参数化，对应 test_query.cypher）
# ---------------------------------------------------------------------------
_CYPHER_MATCH_CIRCLE = """
WITH $user_factors AS uf
MATCH (c:Circle)
WITH c, uf,
     [(c)-[r:HAS_FACTOR]->(:Factor {factor_id:'F1'}) | r.proportion][0] AS p1,
     [(c)-[r:HAS_FACTOR]->(:Factor {factor_id:'F2'}) | r.proportion][0] AS p2,
     [(c)-[r:HAS_FACTOR]->(:Factor {factor_id:'F3'}) | r.proportion][0] AS p3,
     [(c)-[r:HAS_FACTOR]->(:Factor {factor_id:'F4'}) | r.proportion][0] AS p4,
     [(c)-[r:HAS_FACTOR]->(:Factor {factor_id:'F5'}) | r.proportion][0] AS p5,
     [(c)-[r:HAS_FACTOR]->(:Factor {factor_id:'F6'}) | r.proportion][0] AS p6,
     [(c)-[r:HAS_FACTOR]->(:Factor {factor_id:'F7'}) | r.proportion][0] AS p7
WITH c, uf,
     coalesce(p1,0) AS p1, coalesce(p2,0) AS p2, coalesce(p3,0) AS p3,
     coalesce(p4,0) AS p4, coalesce(p5,0) AS p5, coalesce(p6,0) AS p6, coalesce(p7,0) AS p7
WITH c, uf, p1,p2,p3,p4,p5,p6,p7,
     uf[0]*p1 + uf[1]*p2 + uf[2]*p3 + uf[3]*p4 + uf[4]*p5 + uf[5]*p6 + uf[6]*p7 AS dot,
     sqrt(uf[0]^2 + uf[1]^2 + uf[2]^2 + uf[3]^2 + uf[4]^2 + uf[5]^2 + uf[6]^2) AS ufNorm,
     sqrt(p1^2 + p2^2 + p3^2 + p4^2 + p5^2 + p6^2 + p7^2) AS cfNorm
WITH c, dot, CASE WHEN ufNorm*cfNorm = 0 THEN 0.0 ELSE dot/(ufNorm*cfNorm) END AS cos
ORDER BY cos DESC LIMIT 1
RETURN c.name AS user_circle, round(cos*1000)/1000 AS similarity
"""

_CYPHER_POSSIBLE_EMOTIONS = """
WITH $user_circle AS userCircle,
     $user_country AS userCountry,
     $scene_tags AS sceneTags,
     $thing_tags AS thingTags
MATCH (c:Circle {name: userCircle})-[he:HAS_EMOTION]->(e:Emotion)
WHERE (userCountry IS NULL OR he.country = userCountry)
OPTIONAL MATCH (e)-[os:OCCURS_IN_SCENE]->(s:Scene)
  WHERE os.circle = userCircle AND (userCountry IS NULL OR os.country = userCountry)
    AND s.scene_id IN sceneTags
OPTIONAL MATCH (e)-[ot:INVOLVES_THING]->(t:Thing)
  WHERE ot.circle = userCircle AND (userCountry IS NULL OR ot.country = userCountry)
    AND t.thing_id IN thingTags
WITH c, he, e,
     collect(DISTINCT s) AS _s,
     collect(DISTINCT t) AS _t
WITH c, he, e,
     [x IN _s WHERE x IS NOT NULL] AS matchedScenes,
     [x IN _t WHERE x IS NOT NULL] AS matchedThings
WHERE size(matchedScenes) > 0 OR size(matchedThings) > 0
RETURN
    e.emotion_id            AS possible_emotion_id,
    e.emotion_name          AS possible_emotion_name,
    he.region_emotion       AS region_emotion,
    he.uniqueness           AS uniqueness,
    he.cultural_source      AS cultural_source,
    he.imagery_explanation  AS imagery_explanation,
    [x IN matchedScenes | {scene_id: x.scene_id, scene_name: x.scene_name}] AS hit_scenes,
    [x IN matchedThings | {thing_id: x.thing_id, thing_name: x.thing_name}] AS hit_things
ORDER BY e.emotion_id, he.region_emotion
"""

_CYPHER_COMMON_SCENES_THINGS = """
WITH $user_circle AS userCircle,
     $user_country AS userCountry,
     $emotion_tags AS emotionTags
MATCH (c:Circle {name: userCircle})-[he:HAS_EMOTION]->(e:Emotion)
WHERE e.emotion_id IN emotionTags
  AND (userCountry IS NULL OR he.country = userCountry)
OPTIONAL MATCH (e)-[os:OCCURS_IN_SCENE]->(s:Scene)
  WHERE os.circle = userCircle AND (userCountry IS NULL OR os.country = userCountry)
OPTIONAL MATCH (e)-[ot:INVOLVES_THING]->(t:Thing)
  WHERE ot.circle = userCircle AND (userCountry IS NULL OR ot.country = userCountry)
WITH c, he, e,
     [x IN collect(DISTINCT s) WHERE x IS NOT NULL] AS allScenes,
     [x IN collect(DISTINCT t) WHERE x IS NOT NULL] AS allThings
RETURN
    e.emotion_id            AS emotion_id,
    e.emotion_name          AS emotion_name,
    he.region_emotion       AS region_emotion,
    he.uniqueness           AS uniqueness,
    he.cultural_source      AS cultural_source,
    he.imagery_explanation  AS imagery_explanation,
    [x IN allScenes | {scene_id: x.scene_id, scene_name: x.scene_name}] AS common_scenes,
    [x IN allThings | {thing_id: x.thing_id, thing_name: x.thing_name}] AS common_things
ORDER BY e.emotion_id, he.region_emotion
"""


def match_user_circle(user_factors: list[float | int]) -> dict[str, Any]:
    """步骤1：用户七大元素占比 → 最近文化圈层。"""
    rows = _run_cypher(_CYPHER_MATCH_CIRCLE, {'user_factors': [float(x) for x in user_factors]})
    if not rows:
        return {'user_circle': '', 'similarity': 0.0}
    return {
        'user_circle': rows[0].get('user_circle') or '',
        'similarity': rows[0].get('similarity') or 0.0,
    }


def query_possible_emotions(
    user_circle: str,
    user_country: str | None,
    scene_tags: list[str],
    thing_tags: list[str],
) -> list[dict[str, Any]]:
    """步骤2【反向】：场景+事物 → 该圈层下可能触发的情感。"""
    return _run_cypher(
        _CYPHER_POSSIBLE_EMOTIONS,
        {
            'user_circle': user_circle,
            'user_country': user_country,
            'scene_tags': scene_tags,
            'thing_tags': thing_tags,
        },
    )


def query_common_scenes_things(
    user_circle: str,
    user_country: str | None,
    emotion_tags: list[str],
) -> list[dict[str, Any]]:
    """步骤3【正向】：情感标签 → 该圈层下常触发的场景与事物。"""
    return _run_cypher(
        _CYPHER_COMMON_SCENES_THINGS,
        {
            'user_circle': user_circle,
            'user_country': user_country,
            'emotion_tags': emotion_tags,
        },
    )


# ---------------------------------------------------------------------------
# 正式模式：包装提示词 + 调用 AI（占位）
# ---------------------------------------------------------------------------
def _build_ai_prompt_payload(
    *,
    song_id: str,
    language: str,
    scene_tags: list[str],
    thing_tags: list[str],
    emotion_tags: list[str],
    user_circle: str,
    possible_emotions: list[dict[str, Any]],
    common_scenes_things: list[dict[str, Any]],
) -> dict[str, Any]:
    """把两大查询结果整理成适合发给 AI 的结构，并附带解释提示词。"""
    data_for_ai = {
        'song_id': song_id,
        'language': language,
        'user_circle': user_circle,
        'input_tags': {
            'scene_tags': scene_tags,
            'thing_tags': thing_tags,
            'emotion_tags': emotion_tags,
        },
        'possible_emotions_from_scene_thing': possible_emotions,
        'common_scenes_things_from_emotion': common_scenes_things,
    }
    system_prompt = (
        '你是国风音乐意象解析助手。请基于给定的文化圈层与图谱查询结果，'
        '用通俗、有文化温度的语言向用户解释这首歌可能唤起的情感，以及相关场景、事物意象。'
        f'请使用目标语言输出：{language}。'
    )
    user_prompt = (
        '【任务】结合下列两份图谱结果，写一段面向听众的关于该歌曲表达的解析，要求先根据用户可能与原意共鸣的地方向用户说明，再对于用户理解可能与愿意表达差异最大地方进行针对于该用户的独特解释\n'
        '【结果A·反向】由本曲场景/事物标签推断、该圈层用户可能触发的情感（含意象解释/文化源流）。\n'
        '【结果B·正向】由本曲情感标签推断、该圈层用户常触发这些情感的场景与事物。\n'
        '【希望得到的回复】一段连贯短文（可分小标题），避免罗列原始 ID；'
        '点明圈层视角、情感共鸣、典型场景与器物意象，语气亲切专业。\n'
        f'【结构化数据】\n{json.dumps(data_for_ai, ensure_ascii=False, indent=2)}'
    )
    return {
        'system_prompt': system_prompt,
        'user_prompt': user_prompt,
        'structured_data': data_for_ai,
    }


def _call_imagery_ai(prompt_payload: dict[str, Any]) -> dict[str, Any]:
    """
    调用意象解析 AI。

    TODO【待接入 IMAGERY_AI】：填写 config.services.IMAGERY_AI 后启用真实请求。
    当前若未配置，返回包装好的提示词占位，便于联调前端/提示词。
    """
    cfg = svc_config.IMAGERY_AI or {}
    base_url = (cfg.get('BASE_URL') or '').rstrip('/')
    api_key = cfg.get('API_KEY') or ''
    model = cfg.get('MODEL') or ''
    timeout = int(cfg.get('TIMEOUT_SECONDS') or 60)

    if not base_url or not api_key or not model:
        return {
            'source': 'imagery_ai_placeholder',
            'text': (
                '【意象 AI 占位】尚未配置 IMAGERY_AI。\n'
                '已准备好提示词与结构化数据，待接入后将生成正式解释文案。'
            ),
            'prompt_payload': prompt_payload,
            'message': '占位：请填写 config.services.IMAGERY_AI',
        }

    # OpenAI 兼容格式占位调用
    url = f'{base_url}/chat/completions'
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
    }
    body = {
        'model': model,
        'messages': [
            {'role': 'system', 'content': prompt_payload['system_prompt']},
            {'role': 'user', 'content': prompt_payload['user_prompt']},
        ],
    }
    # 外部模型偶发 SSL/网络抖动，做有限次重试，避免一次失败直接产出错误文案
    last_exc: Exception | None = None
    resp = None
    for attempt in range(3):
        try:
            resp = requests.post(url, headers=headers, json=body, timeout=timeout)
            resp.raise_for_status()
            break
        except requests.RequestException as exc:
            last_exc = exc
            if attempt < 2:
                time.sleep(1 + attempt)
    if resp is None:
        raise last_exc
    data = resp.json()
    text = ''
    try:
        text = data['choices'][0]['message']['content']
    except (KeyError, IndexError, TypeError):
        text = json.dumps(data, ensure_ascii=False)
    return {
        'source': 'imagery_ai',
        'text': text,
        'raw': data,
        'message': '意象 AI 解释完成',
    }


# ---------------------------------------------------------------------------
# 对外主入口
# ---------------------------------------------------------------------------
def analyze_song_imagery(
    *,
    song_id: str,
    scene_tags: list[str] | None = None,
    thing_tags: list[str] | None = None,
    emotion_tags: list[str] | None = None,
    user_id: str = '',
    language: str = 'zh-CN',
    circle_override: Any = None,
) -> dict[str, Any]:
    """
    歌曲详情 · 意象解析主流程。

    入参：
    - song_id：歌曲 id（如 res-故梦）
    - scene_tags / thing_tags / emotion_tags：前端传入的三大标签列表（N/T/F）
    - user_id：用于查用户圈层属性（当前占位固定值）
    - language：目标解释语言
    - circle_override：测试模式下的圈层覆盖（auto/0 或 1~5）
    """
    scene_tags = list(scene_tags or [])
    thing_tags = list(thing_tags or [])
    emotion_tags = list(emotion_tags or [])

    user_profile = get_user_circle_factors(user_id)
    factors = user_profile.get('factors') or list(_FIXED_USER_FACTORS)
    country = user_profile.get('country') or _FIXED_USER_COUNTRY

    test_mode = bool(getattr(svc_config, 'IMAGERY_TEST_MODE', False))
    override_info = _resolve_test_circle_override(circle_override)
    circle_override_active = bool(override_info.get('enabled'))

    try:
        if circle_override_active:
            # 测试模式 · 强制圈层：跳过余弦匹配，直接用选定圈层名
            user_circle = override_info['circle']
            # 无默认国家时传 None，图查询不过滤 country
            country = override_info.get('country') or None
            circle_info = {
                'user_circle': user_circle,
                'similarity': 1.0,
                'source': 'test_circle_override',
                'override': override_info['override'],
            }
        else:
            # 自动匹配（正式模式 或 测试模式未设覆盖）
            circle_info = match_user_circle(factors)
            user_circle = circle_info.get('user_circle') or ''
        possible_emotions = query_possible_emotions(
            user_circle, country, scene_tags, thing_tags,
        ) if user_circle else []
        common_scenes_things = query_common_scenes_things(
            user_circle, country, emotion_tags,
        ) if user_circle else []
        query_error = ''
    except Exception as exc:  # noqa: BLE001 — 联调阶段把图库错误带回前端
        circle_info = {'user_circle': '', 'similarity': 0.0}
        user_circle = ''
        possible_emotions = []
        common_scenes_things = []
        query_error = str(exc)

    base = {
        'source': 'imagery_analyze',
        'song_id': song_id,
        'language': language,
        'test_mode': test_mode,
        'user_profile': user_profile,
        'matched_circle': circle_info,
        # 测试圈层覆盖状态（便于前端/调试确认当前生效圈层）
        'test_circle_override': override_info,
        'input_tags': {
            'scene_tags': scene_tags,
            'thing_tags': thing_tags,
            'emotion_tags': emotion_tags,
        },
        # 两大核心查询结果（一并回传，便于前端做结构化展示/调试）
        'possible_emotions': possible_emotions,
        'common_scenes_things': common_scenes_things,
        'query_error': query_error,
    }

    # 无论测试开关如何，查询结果都包装成提示词交给 AI，AI 解释文案推到网页
    if query_error:
        base['text'] = (
            f'【意象查询异常】{query_error}\n'
            '（请检查 IMAGERY_NEO4J 配置与图数据是否已入库）'
        )
        base['message'] = '图查询异常，未调用 AI'
        return base

    prompt_payload = _build_ai_prompt_payload(
        song_id=song_id,
        language=language,
        scene_tags=scene_tags,
        thing_tags=thing_tags,
        emotion_tags=emotion_tags,
        user_circle=user_circle,
        possible_emotions=possible_emotions,
        common_scenes_things=common_scenes_things,
    )
    try:
        ai_result = _call_imagery_ai(prompt_payload)
    except Exception as exc:  # noqa: BLE001 — AI 调用失败不阻断接口
        ai_result = {
            'source': 'imagery_ai_error',
            'text': f'【意象 AI 调用失败】{exc}',
            'message': 'AI 调用异常，已返回错误提示',
        }
    base['ai'] = ai_result
    base['prompt_payload'] = prompt_payload
    base['text'] = ai_result.get('text') or ''
    if circle_override_active:
        base['message'] = (
            f"已调用意象 AI（强制圈层：{user_circle} / 国家={country}）"
        )
    else:
        base['message'] = '已调用意象 AI 生成解释文案'
    return base


def translate_song_imagery(
    song_id: str,
    language: str = 'zh-CN',
    *,
    user_id: str = '',
    circle_override: Any = None,
    scene_tags: list[str] | None = None,
    thing_tags: list[str] | None = None,
    emotion_tags: list[str] | None = None,
) -> dict[str, Any]:
    """从本地资源包补齐三大标签后走主流程（可带测试圈层覆盖）。"""
    from data_display.services import query_music_resource

    resource = query_music_resource(song_id)
    return analyze_song_imagery(
        song_id=song_id,
        scene_tags=list(scene_tags if scene_tags is not None else (resource.get('scene_tags') or [])),
        thing_tags=list(thing_tags if thing_tags is not None else (resource.get('thing_tags') or [])),
        emotion_tags=list(emotion_tags if emotion_tags is not None else (resource.get('emotion_tags') or [])),
        user_id=user_id,
        language=language,
        circle_override=circle_override,
    )


# ---------------------------------------------------------------------------
# 意象解析缓冲池：页面只从池中取内容；未命中则申请解析并写入
# key = song_id | language | circle_slot（auto 或 1~5）
# ---------------------------------------------------------------------------
_IMAGERY_BUFFER: dict[str, dict[str, Any]] = {}
_IMAGERY_BUFFER_LOCK = threading.Lock()


def _circle_slot_for_buffer(circle_override: Any) -> str:
    """缓冲池分片键：测试关 / auto → auto；强制圈层 → 圈层名。"""
    if not bool(getattr(svc_config, 'IMAGERY_TEST_MODE', False)):
        return 'auto'
    info = _resolve_test_circle_override(circle_override)
    if info.get('enabled'):
        return str(info.get('circle') or info.get('override') or 'auto')
    return 'auto'


def _imagery_buffer_key(song_id: str, language: str, circle_override: Any) -> str:
    return f'{song_id}|{language}|{_circle_slot_for_buffer(circle_override)}'


def peek_imagery_buffer(
    song_id: str,
    language: str = 'zh-CN',
    circle_override: Any = None,
) -> dict[str, Any] | None:
    """只读查看缓冲池，不触发解析。"""
    key = _imagery_buffer_key(song_id, language, circle_override)
    with _IMAGERY_BUFFER_LOCK:
        cached = _IMAGERY_BUFFER.get(key)
        if not cached:
            return None
        return {**cached, 'from_buffer': True, 'buffer_key': key}


def ensure_imagery_buffered(
    *,
    song_id: str,
    language: str = 'zh-CN',
    user_id: str = '',
    circle_override: Any = None,
    scene_tags: list[str] | None = None,
    thing_tags: list[str] | None = None,
    emotion_tags: list[str] | None = None,
) -> dict[str, Any]:
    """
    缓冲池模式入口：
    1) 池中有该曲（同语言/同圈层分片）→ 直接返回
    2) 否则申请意象解析，写入缓冲池后再返回
    网页应只调用本接口取文案。
    """
    key = _imagery_buffer_key(song_id, language, circle_override)

    with _IMAGERY_BUFFER_LOCK:
        cached = _IMAGERY_BUFFER.get(key)
        if cached is not None:
            return {**cached, 'from_buffer': True, 'buffer_key': key}

    result = translate_song_imagery(
        song_id,
        language=language,
        user_id=user_id,
        circle_override=circle_override,
        scene_tags=scene_tags,
        thing_tags=thing_tags,
        emotion_tags=emotion_tags,
    )

    # 仅缓存成功生成的文案；查询异常或 AI 调用失败的占位结果不缓存，
    # 否则一次网络抖动会被固化，后续请求永远命中错误文案
    ai_source = (result.get('ai') or {}).get('source')
    if ai_source == 'imagery_ai' and not result.get('query_error'):
        with _IMAGERY_BUFFER_LOCK:
            # 并发下以先写入者为准，后写覆盖亦可（结果等价）
            _IMAGERY_BUFFER[key] = result
    return {**result, 'from_buffer': False, 'buffer_key': key}


def clear_imagery_buffer(song_id: str | None = None) -> dict[str, Any]:
    """清空缓冲池（可选按 song_id 前缀清理）。"""
    with _IMAGERY_BUFFER_LOCK:
        if not song_id:
            n = len(_IMAGERY_BUFFER)
            _IMAGERY_BUFFER.clear()
            return {'cleared': n}
        keys = [k for k in _IMAGERY_BUFFER if k.startswith(f'{song_id}|')]
        for k in keys:
            _IMAGERY_BUFFER.pop(k, None)
        return {'cleared': len(keys), 'song_id': song_id}
