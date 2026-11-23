"""
多维度数据展示与问答服务模块（Django 应用：data_display）

HTTP 路由仍由 api.views / api.urls 统一对外暴露；
本应用只承载业务实现，请在本文件（services.py）中继续完善具体逻辑。

待实现能力总览：
1. Neo4j 图谱查询（首页右下）
2. KG-RAG 问答（首页左下）
3. 关系数据库查询：大类介绍/小类/歌曲/音频/词云/评论等
4. 用户资料查询与更新（个人界面）
5. 内容展示模块：首页Feed、单曲资源包、搜索建议（从b项目迁移）
"""

from __future__ import annotations

import json
import os
import random
import re
import urllib.parse
from pathlib import Path
from typing import Any

from config import services as svc_config
from django.conf import settings

RESOURCES_ROOT = Path(settings.MEDIA_ROOT) / 'resources'

_LRC_LINE_RE = re.compile(
    r'\[(\d{1,2}):(\d{2})(?:\.(\d{1,3}))?\](.*)'
)


def _parse_lrc(text: str) -> list[dict[str, Any]]:
    lines: list[dict[str, Any]] = []
    for raw in text.splitlines():
        raw = raw.strip()
        if not raw:
            continue
        m = _LRC_LINE_RE.match(raw)
        if not m:
            continue
        minute = int(m.group(1))
        second = int(m.group(2))
        frac = m.group(3) or '0'
        if len(frac) == 1:
            frac_sec = int(frac) / 10
        elif len(frac) == 2:
            frac_sec = int(frac) / 100
        else:
            frac_sec = int(frac[:3]) / 1000
        t = minute * 60 + second + frac_sec
        lyric = (m.group(4) or '').strip()
        if lyric:
            lines.append({'time': round(t, 3), 'text': lyric})
    lines.sort(key=lambda x: x['time'])
    return lines


def _pick_file(folder: Path, names: tuple[str, ...]) -> Path | None:
    for name in names:
        p = folder / name
        if p.exists() and p.is_file():
            return p
    exts = {Path(n).suffix.lower() for n in names if Path(n).suffix}
    for p in folder.iterdir():
        if p.is_file() and p.suffix.lower() in exts:
            return p
    return None


def _media_url(rel: Path) -> str:
    try:
        media_root = Path(settings.MEDIA_ROOT).resolve()
        rel_resolved = rel.resolve()
        if not rel_resolved.is_relative_to(media_root):
            return ''
        rel_to_media = rel_resolved.relative_to(media_root)
        return f"{settings.MEDIA_URL.rstrip('/')}/{rel_to_media.as_posix()}"
    except (OSError, ValueError):
        return ''


def _load_song_tags(folder: Path) -> dict[str, Any]:
    """读取歌曲文件夹内 tags.json（场景/事物/情感编号列表 + 演示置顶字段）。"""
    empty = {
        'scene_tags': [],
        'thing_tags': [],
        'emotion_tags': [],
        'featured': False,
        'display_order': 999,
    }
    tags_path = folder / 'tags.json'
    if not tags_path.exists():
        return empty
    try:
        raw = json.loads(tags_path.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError):
        return empty
    return {
        'scene_tags': list(raw.get('scene_tags') or []),
        'thing_tags': list(raw.get('thing_tags') or []),
        'emotion_tags': list(raw.get('emotion_tags') or []),
        # 演示置顶：featured=True 的歌曲排在 catalog 最前；display_order 越小越靠前
        'featured': bool(raw.get('featured') or False),
        'display_order': int(raw.get('display_order') or 999),
    }


def _load_folder_resource(folder: Path) -> dict[str, Any] | None:
    if not folder.is_dir():
        return None
    title = folder.name
    song_id = f'res-{title}'

    intro_path = _pick_file(folder, ('intro.txt', '简介.txt'))
    lrc_path = _pick_file(folder, ('lyric.lrc', 'lyrics.lrc', '歌词.lrc'))
    audio_path = _pick_file(folder, ('audio.mp3', 'audio.wav', 'audio.flac', '音频.mp3'))
    mv_path = _pick_file(folder, ('mv.mp4', 'mv.webm', 'video.mp4', 'MV.mp4'))
    cover_path = _pick_file(folder, ('cover.jpg', 'cover.png', '封面.jpg', '封面.png', 'cover.jpeg', '封面.jpeg'))

    intro = ''
    if intro_path:
        intro = intro_path.read_text(encoding='utf-8', errors='ignore').strip()

    lyrics: list[dict[str, Any]] = []
    lyrics_lrc_url = ''
    if lrc_path:
        lrc_text = lrc_path.read_text(encoding='utf-8', errors='ignore')
        lyrics = _parse_lrc(lrc_text)
        lyrics_lrc_url = _media_url(lrc_path)

    tags = _load_song_tags(folder)

    return {
        'id': song_id,
        'title': title,
        'intro': intro or f'【本地资源】{title}',
        'mv_url': _media_url(mv_path) if mv_path else '',
        'audio_url': _media_url(audio_path) if audio_path else '',
        'cover_url': _media_url(cover_path) if cover_path else '',
        'lyrics_lrc_url': lyrics_lrc_url,
        'lyrics': lyrics,
        'source_folder': title,
        # 意象解析用：视频三大元素标签（N/T/F 编号）
        'scene_tags': tags['scene_tags'],
        'thing_tags': tags['thing_tags'],
        'emotion_tags': tags['emotion_tags'],
        # 演示置顶标记（供 _scan_local_resources 排序使用）
        'featured': tags['featured'],
        'display_order': tags['display_order'],
    }


def _scan_local_resources() -> list[dict[str, Any]]:
    if not RESOURCES_ROOT.exists():
        return []
    items: list[dict[str, Any]] = []
    for child in sorted(RESOURCES_ROOT.iterdir(), key=lambda p: p.name):
        if not child.is_dir():
            continue
        song = _load_folder_resource(child)
        if song:
            items.append(song)
    # 演示置顶：featured=True 优先按 display_order 升序；其余按文件夹名升序
    items.sort(
        key=lambda s: (
            0 if s.get('featured') else 1,
            s.get('display_order', 999),
            s.get('title', ''),
        )
    )
    return items


_PLACEHOLDER_TITLES = [
    '茉莉花', '高山流水', '梁祝', '二泉映月', '春江花月夜',
    '十面埋伏', '渔舟唱晚', '梅花三弄', '平沙落雁', '阳关三叠',
    '广陵散', '胡笳十八拍', '秦王破阵乐', '霓裳羽衣曲', '汉宫秋月',
    '月儿高', '流水', '酒狂', '潇湘水云', '幽兰',
    '忆故人', '苏武牧羊', '塞上曲', '关山月',
]


def _build_catalog() -> list[dict[str, Any]]:
    local = _scan_local_resources()
    local_titles = {x['title'] for x in local}
    placeholders: list[dict[str, Any]] = []
    for i, title in enumerate(_PLACEHOLDER_TITLES, start=1):
        if title in local_titles:
            continue
        placeholders.append(
            {
                'id': f'song-{i:02d}',
                'title': title,
                'intro': f'【占位简介】「{title}」——国风音乐海外传播主题演示资源。',
                'mv_url': '',
                'audio_url': '',
                'lyrics_lrc_url': '',
                'lyrics': [
                    {'time': 0.0, 'text': f'（占位歌词）{title} · 第一句'},
                    {'time': 3.0, 'text': f'（占位歌词）{title} · 第二句'},
                    {'time': 6.0, 'text': f'（占位歌词）{title} · 第三句'},
                ],
                'scene_tags': [],
                'thing_tags': [],
                'emotion_tags': [],
                'featured': False,
                'display_order': 999,
            }
        )
    return local + placeholders


_PLACEHOLDER_CATALOG: list[dict[str, Any]] = _build_catalog()


def refresh_catalog() -> list[dict[str, Any]]:
    global _PLACEHOLDER_CATALOG
    _PLACEHOLDER_CATALOG = _build_catalog()
    return _PLACEHOLDER_CATALOG


def query_home_feed(keyword: str = '', refresh: bool = False) -> dict[str, Any]:
    _ = svc_config.RELATIONAL_DB
    if refresh:
        refresh_catalog()
    items = list(_PLACEHOLDER_CATALOG)
    kw = (keyword or '').strip()
    if kw:
        items = [x for x in items if kw in x['title'] or kw in x.get('intro', '')]
    if refresh:
        random.shuffle(items)
    items = items[:9]
    feed = [
        {
            'id': x['id'],
            'title': x['title'],
            'intro': x.get('intro') or '',
            'mv_url': x.get('mv_url') or '',
            'audio_url': x.get('audio_url') or '',
            'lyrics_url': x.get('lyrics_lrc_url') or f'/api/content/music-resource/?id={x["id"]}',
            'resource_url': f'/api/content/music-resource/?id={x["id"]}',
        }
        for x in items
    ]
    return {
        'source': 'content_display_home_feed',
        'items': feed,
        'suggestions': ['国风热歌', '古风 MV', '民乐合奏', '戏曲精选', '牡丹江', '新锐国风'],
        'message': '内容展示模块返回资源 URL 列表（最多 9 条）',
        'refreshed': refresh,
    }


def query_music_resource(song_id: str) -> dict[str, Any]:
    _ = svc_config.RELATIONAL_DB
    if not any(x['id'] == song_id for x in _PLACEHOLDER_CATALOG):
        refresh_catalog()
    song = next((x for x in _PLACEHOLDER_CATALOG if x['id'] == song_id), None)
    if not song:
        return {
            'id': song_id,
            'title': f'未知歌曲 {song_id}',
            'intro': '资源不存在或尚未入库',
            'mv_url': '',
            'audio_url': '',
            'lyrics_lrc_url': '',
            'lyrics': [],
            'scene_tags': [],
            'thing_tags': [],
            'emotion_tags': [],
            'message': '未找到资源',
        }
    cover_url = song.get('cover_url') or ''
    if not cover_url and song.get('mv_url'):
        cover_url = song['mv_url']
    
    return {
        'id': song['id'],
        'title': song['title'],
        'intro': song.get('intro') or '',
        'mv_url': song.get('mv_url') or '',
        'audio_url': song.get('audio_url') or '',
        'cover_url': cover_url,
        'lyrics_lrc_url': song.get('lyrics_lrc_url') or '',
        'lyrics': song.get('lyrics') or [],
        'scene_tags': list(song.get('scene_tags') or []),
        'thing_tags': list(song.get('thing_tags') or []),
        'emotion_tags': list(song.get('emotion_tags') or []),
        'message': '歌曲资源包',
    }


def query_search_suggestions(keyword: str = '') -> dict[str, Any]:
    base = ['国风热歌', '古风 MV', '民乐合奏', '戏曲精选', '新锐国风', '海外翻唱', '牡丹江']
    kw = (keyword or '').strip()
    if kw:
        titles = [x['title'] for x in _PLACEHOLDER_CATALOG if kw in x['title']]
        suggestions = (titles + base)[:8]
    else:
        suggestions = base
    return {'suggestions': suggestions}

# 大类-小类-歌曲对应关系（全球传播效果等界面使用；后续可改为你手工维护的正式内容）
# 路径：backend/data/music_taxonomy.json
TAXONOMY_PATH = Path(__file__).resolve().parents[1] / 'data' / 'music_taxonomy.json'


def _load_taxonomy() -> dict[str, Any]:
    if TAXONOMY_PATH.exists():
        with open(TAXONOMY_PATH, encoding='utf-8') as f:
            return json.load(f)
    return {}


def get_music_taxonomy() -> dict[str, Any]:
    """
    返回音乐大类 → 小类 → 歌曲列表的 JSON 结构。

    优先从 Neo4j 查询实际内容；查询失败或为空时退回静态 JSON。
    """
    neo4j_tax = get_neo4j_taxonomy()
    if neo4j_tax:
        return neo4j_tax
    return _load_taxonomy()


def get_neo4j_taxonomy() -> dict[str, Any]:
    """
    从 Neo4j 查询实际的大类 → 小类列表（用于前端下拉与 Neo4j 实际内容一致）。

    图谱结构（实测）：
        TradMusicRoot -[:HAS_CATEGORY]-> MusicCategory(大类) -[:CONTAIN]-> 小类 -[]-> MusicWork(作品)

    返回结构与 music_taxonomy.json 一致：{大类: {小类: [歌曲...]}}
    """
    from .neo4j_client import get_driver, get_database

    try:
        driver = get_driver()
        database = get_database()
        with driver.session(database=database) as session:
            # 1. 大类：优先找 MusicCategory 标签；没有则退回「有 CONTAIN 出边」的节点
            cat_records = session.run(
                """
                MATCH (c:MusicCategory)
                RETURN elementId(c) AS cid, c.name AS name
                """
            ).data()
            if not cat_records:
                cat_records = session.run(
                    """
                    MATCH (c)-[:CONTAIN]->()
                    WHERE NOT ()-[:CONTAIN]->(c)
                    RETURN DISTINCT elementId(c) AS cid, c.name AS name
                    """
                ).data()
            if not cat_records:
                return {}

            taxonomy: dict[str, Any] = {}
            for cat in cat_records:
                cid = cat['cid']
                cat_name = cat.get('name') or f'类别{cid}'

                # 2. 小类：大类的 CONTAIN 目标
                sub_records = session.run(
                    """
                    MATCH (c)-[:CONTAIN]->(s)
                    WHERE elementId(c) = $cid
                    RETURN elementId(s) AS sid, s.name AS name
                    """,
                    cid=cid,
                ).data()

                sub_map: dict[str, list[str]] = {}
                for sub in sub_records:
                    sid = sub['sid']
                    sub_name = sub.get('name') or f'子类{sid}'

                    # 3. 歌曲：小类的任意出边目标（排除指回大类的边）
                    song_records = session.run(
                        """
                        MATCH (s)-[r]->(w)
                        WHERE elementId(s) = $sid AND type(r) <> 'CONTAIN'
                        RETURN DISTINCT w.name AS name
                        """,
                        sid=sid,
                    ).data()
                    songs = [w['name'] for w in song_records if w.get('name')]
                    sub_map[sub_name] = songs

                if sub_map:
                    taxonomy[cat_name] = sub_map
        return taxonomy
    except Exception:
        return {}


def query_neo4j_graph(category: str, subcategory: str) -> dict[str, Any]:
    """
    连接 Neo4j（配置见 config.services.NEO4J），
    按音乐大类 + 小类查询图谱子图，返回可供前端渲染的节点/边数据。

    实现策略：
    1. 在图谱里按 label/name/category 属性匹配小类节点（兜底匹配 category 大类）
    2. 从匹配节点向外扩展 1~2 跳，采集节点与关系
    3. 去重后按 ECharts/D3 graph 格式返回 {nodes, links}
    图谱 schema 未知时也能跑通：扫描所有 label 与关系类型，按名字模糊匹配。
    """
    from .neo4j_client import get_driver, get_database

    nodes: dict[str, dict[str, Any]] = {}
    links: list[dict[str, Any]] = []
    seen_rels: set[tuple[str, str, str]] = set()

    try:
        driver = get_driver()
        database = get_database()
        with driver.session(database=database) as session:
            # 1) 找到与小类名匹配的根节点；找不到再退回大类名匹配
            #    匹配范围：节点属性值 + 节点 label（兼容 label 即名字的图谱）
            root_records = session.run(
                """
                MATCH (n)
                WHERE any(k IN keys(n) WHERE toLower(toString(n[k])) CONTAINS toLower($keyword))
                   OR any(l IN labels(n) WHERE toLower(l) CONTAINS toLower($keyword))
                RETURN elementId(n) AS eid, labels(n) AS labels, properties(n) AS props
                LIMIT 20
                """,
                keyword=subcategory or category,
            ).data()

            if not root_records and category:
                root_records = session.run(
                    """
                    MATCH (n)
                    WHERE any(k IN keys(n) WHERE toLower(toString(n[k])) CONTAINS toLower($keyword))
                       OR any(l IN labels(n) WHERE toLower(l) CONTAINS toLower($keyword))
                    RETURN elementId(n) AS eid, labels(n) AS labels, properties(n) AS props
                    LIMIT 20
                    """,
                    keyword=category,
                ).data()

            root_ids = [r['eid'] for r in root_records]
            for r in root_records:
                _collect_node(nodes, r['eid'], r['labels'], r['props'])

            # 2) 从根节点向外扩展 2 跳
            if root_ids:
                rel_records = session.run(
                    """
                    MATCH path = (n)-[r*1..2]-(m)
                    WHERE elementId(n) IN $root_ids
                    UNWIND relationships(path) AS rel
                    WITH rel, startNode(rel) AS a, endNode(rel) AS b
                    RETURN elementId(a) AS src_id, labels(a) AS src_labels, properties(a) AS src_props,
                           elementId(b) AS dst_id, labels(b) AS dst_labels, properties(b) AS dst_props,
                           type(rel) AS rel_type, elementId(rel) AS rel_id
                    """,
                    root_ids=root_ids,
                ).data()

                for r in rel_records:
                    _collect_node(nodes, r['src_id'], r['src_labels'], r['src_props'])
                    _collect_node(nodes, r['dst_id'], r['dst_labels'], r['dst_props'])
                    key = (str(r['src_id']), str(r['dst_id']), r['rel_type'])
                    if key not in seen_rels:
                        seen_rels.add(key)
                        links.append({
                            'source': str(r['src_id']),
                            'target': str(r['dst_id']),
                            'rel': r['rel_type'],
                        })

            # 兜底：图谱里没有任何匹配时，返回库内前 30 条任意节点 + 关系
            if not nodes:
                any_records = session.run(
                    """
                    MATCH (n)-[r]->(m)
                    RETURN elementId(n) AS src_id, labels(n) AS src_labels, properties(n) AS src_props,
                           elementId(m) AS dst_id, labels(m) AS dst_labels, properties(m) AS dst_props,
                           type(r) AS rel_type
                    LIMIT 30
                    """
                ).data()
                for r in any_records:
                    _collect_node(nodes, r['src_id'], r['src_labels'], r['src_props'])
                    _collect_node(nodes, r['dst_id'], r['dst_labels'], r['dst_props'])
                    key = (str(r['src_id']), str(r['dst_id']), r['rel_type'])
                    if key not in seen_rels:
                        seen_rels.add(key)
                        links.append({
                            'source': str(r['src_id']),
                            'target': str(r['dst_id']),
                            'rel': r['rel_type'],
                        })
    except Exception as e:
        return {
            'source': 'neo4j_error',
            'category': category,
            'subcategory': subcategory,
            'nodes': [],
            'links': [],
            'error': f'Neo4j 查询失败：{e}',
        }

    return {
        'source': 'neo4j_graph',
        'category': category,
        'subcategory': subcategory,
        'nodes': list(nodes.values()),
        'links': links,
        'message': f'已从 Neo4j 取得 {len(nodes)} 个节点 / {len(links)} 条关系',
    }


def _collect_node(
    bucket: dict[str, dict[str, Any]],
    eid: int | str,
    labels: list[str],
    props: dict[str, Any],
) -> None:
    """将 Neo4j 节点塞进 bucket 去重。"""
    sid = str(eid)
    if sid in bucket:
        return
    # 选一个可读的标签作为 label，优先 name/title/标题
    name = (
        props.get('name')
        or props.get('title')
        or props.get('标题')
        or props.get('名称')
        or (labels[0] if labels else 'node')
    )
    bucket[sid] = {
        'id': sid,
        'label': name,
        'type': labels[0] if labels else 'node',
        'properties': props,
    }

def ask_kg_rag(question: str, locale: str = 'zh-CN') -> dict[str, Any]:
    """
    KG-RAG 问答：基于 Neo4j 知识图谱检索 + LLM 总结生成回答。

    流程：
    1. 从问题中抽取关键词，在 Neo4j 中按属性模糊匹配节点
    2. 从匹配节点向外扩展 1~2 跳，采集子图作为上下文
    3. 把子图序列化为文本上下文，交给 LLM 总结回答
    4. 未配置 LLM API Key 时，直接返回检索到的图谱事实作为答案

    LLM 配置见 config.services.LLM。
    """
    from .neo4j_client import get_driver, get_database

    # 1) 在 Neo4j 中按问题关键词检索相关子图
    context_facts: list[str] = []
    retrieved_nodes: list[dict[str, Any]] = []
    retrieved_rels: list[dict[str, Any]] = []
    retrieval_error: str | None = None

    try:
        driver = get_driver()
        database = get_database()
        keywords = _extract_keywords(question)
        with driver.session(database=database) as session:
            nodes_map: dict[str, dict[str, Any]] = {}
            seen_rels: set[tuple[str, str, str]] = set()

            for kw in keywords:
                records = session.run(
                    """
                    MATCH (n)
                    WHERE any(k IN keys(n) WHERE toLower(toString(n[k])) CONTAINS toLower($kw))
                       OR any(l IN labels(n) WHERE toLower(l) CONTAINS toLower($kw))
                    RETURN elementId(n) AS eid, labels(n) AS labels, properties(n) AS props
                    LIMIT 10
                    """,
                    kw=kw,
                ).data()
                root_ids = [r['eid'] for r in records]
                for r in records:
                    _collect_node(nodes_map, r['eid'], r['labels'], r['props'])

                if root_ids:
                    rel_records = session.run(
                        """
                        MATCH path = (n)-[r*1..2]-(m)
                        WHERE elementId(n) IN $root_ids
                        UNWIND relationships(path) AS rel
                        WITH rel, startNode(rel) AS a, endNode(rel) AS b
                        RETURN elementId(a) AS src_id, labels(a) AS src_labels, properties(a) AS src_props,
                               elementId(b) AS dst_id, labels(b) AS dst_labels, properties(b) AS dst_props,
                               type(rel) AS rel_type
                        LIMIT 100
                        """,
                        root_ids=root_ids,
                    ).data()
                    for r in rel_records:
                        _collect_node(nodes_map, r['src_id'], r['src_labels'], r['src_props'])
                        _collect_node(nodes_map, r['dst_id'], r['dst_labels'], r['dst_props'])
                        key = (str(r['src_id']), str(r['dst_id']), r['rel_type'])
                        if key not in seen_rels:
                            seen_rels.add(key)
                            retrieved_rels.append({
                                'source': str(r['src_id']),
                                'target': str(r['dst_id']),
                                'rel': r['rel_type'],
                            })

            retrieved_nodes = list(nodes_map.values())
            context_facts = _summarize_subgraph_as_facts(retrieved_nodes, retrieved_rels)
    except Exception as e:
        retrieval_error = f'Neo4j 检索失败：{e}'

    # 2) 把检索到的图谱事实交给 LLM 总结
    llm_cfg = svc_config.LLM
    answer: str
    used_llm: bool = False
    if context_facts and llm_cfg.get('API_KEY'):
        try:
            answer = _llm_answer(question, context_facts, llm_cfg, locale)
            used_llm = True
        except Exception as e:
            answer = _build_natural_answer(question, retrieved_nodes, retrieved_rels) or (
                f'图谱检索成功，但 LLM 总结失败：{e}'
            )
    elif context_facts:
        # 未配 LLM：基于图谱结构生成自然语言答案
        answer = _build_natural_answer(question, retrieved_nodes, retrieved_rels)
    else:
        answer = (
            retrieval_error
            or '知识图谱中未检索到与该问题相关的节点，请换一种问法或检查图谱内容。'
        )

    return {
        'source': 'kg_rag',
        'question': question,
        'answer': answer,
        'used_llm': used_llm,
        'answer_pipeline': '知识图谱检索 + 大模型丰富生成' if used_llm else '知识图谱检索',
        'references': {
            'nodes_count': len(retrieved_nodes),
            'relations_count': len(retrieved_rels),
            'sample_nodes': retrieved_nodes[:5],
            'sample_relations': retrieved_rels[:5],
        },
        'retrieval_error': retrieval_error,
    }


def _extract_keywords(question: str) -> list[str]:
    """
    从中文问题里抽关键词。

    使用 jieba 分词，并：
    - 过滤停用词（疑问词、助词、标点等）
    - 保留长度 ≥ 2 的实词
    - 兜底：若分词后无关键词，整个问题作为一条匹配
    """
    import re
    import logging
    logger = logging.getLogger(__name__)

    # 国风音乐领域词典，让 jieba 不要把这些专有名词切错
    domain_words = [
        '中国传统音乐', '传统音乐', '黄梅戏', '京剧', '昆曲', '评剧', '秦腔',
        '越剧', '豫剧', '二胡', '古筝', '古琴', '笛子', '琵琶', '编钟',
        '马头琴', '葫芦丝', '大鼓', '东北二人转', '二人转', '说唱',
        '民歌', '戏曲', '乐器', '代表作品', '代表曲目',
    ]
    try:
        import jieba
        for w in domain_words:
            jieba.add_word(w)
        tokens = list(jieba.cut(question, cut_all=False))
        logger.info('[KG-RAG] jieba 分词结果: %s -> %s', question, tokens)
    except ImportError as e:
        logger.warning('[KG-RAG] jieba 未安装: %s，退回简单切分', e)
        # jieba 未安装时退回简单切分
        tokens = re.split(r'[，。？！,?.!\s、的了吗呢吧有哪是和与及什么怎么如何]', question)

    stop_words = {
        '的', '了', '吗', '呢', '吧', '有', '哪', '是', '和', '与', '及',
        '什么', '怎么', '如何', '些', '包括', '包含', '关于', '请问',
        '一下', '告诉', '知道', '想要', '看看', '查看', '查询', '帮我',
        '我', '你', '他', '她', '它', '们', '这', '那', '些', '个', '种',
        '几', '多', '少', '都', '请', '啊', '呀', '哦', '哎',
    }
    keywords: list[str] = []
    for w in tokens:
        w = w.strip()
        if not w:
            continue
        # 过滤纯标点 / 纯数字
        if re.fullmatch(r'[\W\d_]+', w):
            continue
        if w in stop_words:
            continue
        if len(w) < 2:
            continue
        keywords.append(w)

    # 去重保序
    seen: set[str] = set()
    deduped: list[str] = []
    for k in keywords:
        if k not in seen:
            seen.add(k)
            deduped.append(k)

    # 兜底：整个问题作为一条
    if not deduped:
        deduped = [question.strip()]
    return deduped[:5]


def _summarize_subgraph_as_facts(
    nodes: list[dict[str, Any]], rels: list[dict[str, Any]]
) -> list[str]:
    """把子图转成『主-谓-宾』的事实文本，供 LLM 当上下文。"""
    node_by_id = {n['id']: n for n in nodes}
    facts: list[str] = []
    for r in rels:
        src = node_by_id.get(r['source'], {})
        dst = node_by_id.get(r['target'], {})
        s_name = src.get('label', r['source'])
        d_name = dst.get('label', r['target'])
        s_type = src.get('type', '')
        d_type = dst.get('type', '')
        facts.append(
            f"({s_type}: {s_name}) -[{r['rel']}]-> ({d_type}: {d_name})"
        )
    for node in nodes[:30]:
        props = node.get('properties') or {}
        readable_props = []
        for key, value in props.items():
            if key in {'name', '名称'} or value in (None, '', [], {}):
                continue
            text = str(value)
            if len(text) > 180:
                text = f'{text[:177]}...'
            readable_props.append(f'{key}={text}')
        if readable_props:
            facts.append(
                f"({node.get('type', '实体')}: {node.get('label', node.get('id', ''))}) "
                f"属性：{'; '.join(readable_props[:10])}"
            )
    return facts


def _build_natural_answer(
    question: str, nodes: list[dict[str, Any]], rels: list[dict[str, Any]]
) -> str:
    """
    基于图谱结构生成自然语言回答（不依赖 LLM）。

    策略：按图谱的层级关系，把检索到的子图组织成「XX 包括 A、B、C，其中 A 的代表作品有 a1、a2」。
    """
    if not nodes or not rels:
        return ''

    # 建立节点索引
    node_by_id = {n['id']: n for n in nodes}
    # 按关系类型分组：src_id -> [(rel, target_id)]
    out_edges: dict[str, list[tuple[str, str]]] = {}
    for r in rels:
        out_edges.setdefault(r['source'], []).append((r['rel'], r['target']))

    # 找根节点：没有入度或入度最少的节点
    in_degree = {n['id']: 0 for n in nodes}
    for r in rels:
        in_degree[r['target']] = in_degree.get(r['target'], 0) + 1
    roots = sorted(in_degree.items(), key=lambda x: x[1])
    # 根节点 label
    root_node = node_by_id.get(roots[0][0]) if roots else nodes[0]
    root_label = root_node.get('label', '中国传统音乐文化')

    lines: list[str] = []
    lines.append(f'关于「{question}」，知识图谱中有以下内容：')

    # 按层级遍历
    # 第一层：根节点的子节点
    root_children = out_edges.get(root_node['id'], [])
    for rel, child_id in root_children:
        child = node_by_id.get(child_id, {})
        child_label = child.get('label', child_id)
        child_type = child.get('type', '')
        lines.append('')
        lines.append(f'【{child_label}】')

        # 第二层：子节点的子节点
        grandchildren = out_edges.get(child_id, [])
        if not grandchildren:
            continue

        # 按类型分组
        grouped: dict[str, list[str]] = {}
        for sub_rel, sub_id in grandchildren:
            sub_node = node_by_id.get(sub_id, {})
            sub_label = sub_node.get('label', sub_id)
            sub_type = sub_node.get('type', '')
            grouped.setdefault(sub_type or '其他', []).append(sub_label)

            # 第三层：孙节点的代表作品
            works = out_edges.get(sub_id, [])
            if works:
                work_names = []
                for w_rel, w_id in works[:5]:  # 只取前5个作品
                    w_node = node_by_id.get(w_id, {})
                    w_label = w_node.get('label', w_id)
                    work_names.append(w_label)
                if work_names:
                    lines.append(f'  - {sub_label}：代表作品《{"、".join(work_names)}》')
        # 没作品的子节点统一列出
        for group_name, items in grouped.items():
            listed_items = [i for i in items if not _has_works(i, out_edges, node_by_id)]
            if listed_items:
                lines.insert(
                    len(lines) - sum(1 for _ in grouped if _),
                    f'  包括：{"、".join(listed_items)}'
                )
    if len(lines) == 1:
        # 兜底：把所有节点按类型列出
        by_type: dict[str, list[str]] = {}
        for n in nodes:
            by_type.setdefault(n.get('type', '其他'), []).append(n.get('label', n['id']))
        for t, items in by_type.items():
            lines.append(f'- {t}：{"、".join(items[:10])}')
    return '\n'.join(lines)


def _has_works(
    node_label: str,
    out_edges: dict[str, list[tuple[str, str]]],
    node_by_id: dict[str, dict[str, Any]],
) -> bool:
    """检查节点是否有子节点（用于判断是否已展开作品列表）。"""
    # 通过 label 找到 id
    for nid, n in node_by_id.items():
        if n.get('label') == node_label:
            return bool(out_edges.get(nid))
    return False


def _llm_answer(
    question: str,
    facts: list[str],
    llm_cfg: dict[str, Any],
    locale: str = 'zh-CN',
) -> str:
    """调用 OpenAI 兼容接口，让 LLM 基于图谱事实回答问题。"""
    import json
    import urllib.request
    import urllib.parse

    base_url = llm_cfg.get('BASE_URL', 'https://api.openai.com/v1').rstrip('/')
    model = llm_cfg.get('MODEL', 'gpt-4o-mini')
    api_key = llm_cfg.get('API_KEY', '')
    timeout = int(llm_cfg.get('TIMEOUT_SECONDS', 60))

    language_names = {
        'zh-CN': '简体中文', 'zh-TW': '繁體中文', 'en': 'English',
        'ru': 'Russian', 'th': 'Thai', 'ko': 'Korean', 'ja': 'Japanese',
    }
    target_language = language_names.get(locale, '简体中文')
    system_prompt = (
        '你是国风音乐知识图谱问答助手。先根据给定的 Neo4j 图谱事实得出答案，'
        '再把节点属性、历史背景、地域特征、演奏方式和代表作品组织成完整易读的回答。'
        '直接回答问题，优先使用短段落和简短列表，不要复述提示词。'
        '不得编造人物、年代、作品或数据；图谱未收录的核心信息要明确说明。'
        f'请使用{target_language}回答。'
    )
    user_prompt = f"图谱事实：\n{chr(10).join(facts)}\n\n用户问题：{question}"

    payload = {
        'model': model,
        'messages': [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_prompt},
        ],
        'temperature': 0.35,
    }
    req = urllib.request.Request(
        f"{base_url}/chat/completions",
        data=json.dumps(payload).encode('utf-8'),
        headers={
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
        },
        method='POST',
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode('utf-8'))
    return data['choices'][0]['message']['content']


def query_category_show_bundle(category: str) -> dict[str, Any]:
    """
    关系数据库查询模块 —— 音乐展示页所需整包数据：
    - 大类介绍（文案 + 背景图 URL）
    - 小类列表
    - 每个小类下的歌曲列表（每小类取前3首）
    - 歌曲音频等资源 URL
    """
    from django.db import connection

    INTROS = {
        '乐器': '中国传统乐器历史悠久，种类繁多，每一种乐器都蕴含着独特的文化内涵和艺术魅力。从古朴典雅的古琴，到婉转悠扬的笛子，再到气势恢宏的编钟，传统乐器以其独特的音色和表现力，传递着华夏文明的深厚底蕴。',
        '戏曲': '中国戏曲是一种综合舞台艺术形式，集唱、念、做、打于一体。包含京剧、昆曲、豫剧、越剧等多个剧种，每个剧种都有独特的唱腔和表演风格，展现了中国传统文化的博大精深。',
        '民歌': '民歌是劳动人民在长期生活实践中集体创作、口头传唱的歌曲形式。不同地域的民歌有着鲜明的地方特色，从江南水乡的婉转清丽，到西北高原的高亢悠扬，民歌以质朴的旋律讲述着一方水土的故事。',
        '说唱': '说唱艺术是一种以口语表达为主的传统表演形式，包括评书、相声、快板、大鼓等多种类型。说唱艺术以其生动的语言和幽默的风格，深受广大群众喜爱。',
    }

    subcategories: dict[str, list[dict[str, Any]]] = {}

    try:
        with connection.cursor() as cursor:
            is_sqlite = connection.vendor == 'sqlite'
            cursor.execute(
                "SELECT category_id, category_name FROM music_category WHERE parent_category = %s",
                [category]
            )
            subcat_rows = cursor.fetchall()

            for subcat_id, subcat_name in subcat_rows:
                if is_sqlite:
                    # 本地 SQLite 兜底：返回该小类全部歌曲
                    cursor.execute(
                        "SELECT id, title, audio_url FROM traditional_song WHERE category_id = %s ORDER BY id",
                        [subcat_id]
                    )
                elif category == '乐器':
                    cursor.execute(
                        "SELECT id, title, audio_url FROM traditional_song WHERE category_id = %s AND (id BETWEEN 146 AND 185 OR id IN (4, 65) OR id >= 225) ORDER BY id",
                        [subcat_id]
                    )
                else:
                    cursor.execute(
                        "SELECT id, title, audio_url FROM traditional_song WHERE category_id = %s ORDER BY id",
                        [subcat_id]
                    )
                song_rows = cursor.fetchall()
                subcategories[subcat_name] = []
                for song_id, title, audio_url in song_rows:
                    if audio_url and audio_url.startswith('audio/'):
                        parts = audio_url.split('/')
                        if len(parts) >= 4:
                            encoded_parts = [urllib.parse.quote(p) for p in parts[1:]]
                            audio_url = f'http://localhost:8000/media/audio/{"/".join(encoded_parts)}'
                    subcategories[subcat_name].append({
                        'id': str(song_id),
                        'title': title,
                        'audio_url': audio_url or '',
                    })

        return {
            'source': 'relational_db',
            'category': category,
            'intro': INTROS.get(category, f'这里是「{category}」的大类介绍'),
            'cover_image_url': '',
            'subcategories': subcategories,
            'message': f'从数据库查询到 {len(subcategories)} 个小类',
        }
    except Exception as e:
        return {
            'source': 'relational_db_error',
            'category': category,
            'intro': '',
            'cover_image_url': '',
            'subcategories': {},
            'message': f'数据库查询失败：{e}',
        }


def query_subcategories_by_category(category: str) -> dict[str, Any]:
    """
    情感分析半遮挡页 —— 按大类查小类列表（网格展示用）。
    """
    from django.db import connection

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT category_id, category_name FROM music_category WHERE parent_category = %s",
                [category]
            )
            rows = cursor.fetchall()
            items = [{'id': str(cat_id), 'name': cat_name, 'thumb_url': ''} for cat_id, cat_name in rows]

        return {
            'source': 'relational_db',
            'category': category,
            'subcategories': items,
            'message': f'从数据库查询到 {len(items)} 个小类',
        }
    except Exception as e:
        return {
            'source': 'relational_db_error',
            'category': category,
            'subcategories': [],
            'message': f'数据库查询失败：{e}',
        }


def query_subcategory_song_resources(category: str, subcategory: str) -> dict[str, Any]:
    """
    点击网格小类后 —— 返回该小类歌曲列表（供下拉框），
    以及列表中第一首歌的：音频、词云、评论、情感极性图等资源。
    """
    from django.db import connection

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT category_id FROM music_category WHERE parent_category = %s AND category_name = %s",
                [category, subcategory]
            )
            subcat_result = cursor.fetchone()
            if not subcat_result:
                return {
                    'source': 'relational_db',
                    'category': category,
                    'subcategory': subcategory,
                    'songs': [],
                    'first_song_resources': None,
                    'message': '未找到该小类',
                }

            subcat_id = subcat_result[0]

            # 情感分析只列出有评论数据的歌曲，避免空图表
            cursor.execute(
                "SELECT id, title, audio_url, cover_url FROM traditional_song "
                "WHERE category_id = %s AND EXISTS (SELECT 1 FROM [comment] cm WHERE cm.song_id = traditional_song.id) "
                "ORDER BY id",
                [subcat_id]
            )
            song_rows = cursor.fetchall()
            songs = [
                {'id': str(song_id), 'title': title}
                for song_id, title, audio_url, cover_url in song_rows
            ]

            first_resources = None
            if song_rows:
                first_id, first_title, first_audio, first_cover = song_rows[0]
                
                if first_audio and not first_audio.startswith('http'):
                    if first_audio.startswith('audio/'):
                        parts = first_audio.split('/')
                        if len(parts) >= 2:
                            encoded_parts = [urllib.parse.quote(p) for p in parts[1:] if p]
                            first_audio = f'/media/audio/{"/".join(encoded_parts)}'
                        else:
                            first_audio = ''
                    elif '大创' in first_audio:
                        relative_path = first_audio.split('大创/', 1)[-1]
                        if relative_path.startswith('audio/'):
                            relative_path = relative_path[6:]
                        encoded_parts = [urllib.parse.quote(p) for p in relative_path.split('/') if p]
                        first_audio = f'/media/audio/{"/".join(encoded_parts)}'
                
                first_resources = {
                    'song_id': str(first_id),
                    'title': first_title,
                    'category': category,
                    'subcategory': subcategory,
                    'audio_url': first_audio or '',
                    'wordcloud_url': '',
                    'emotion_polarity_chart_url': '',
                    'cover_url': first_cover or '',
                    'comments': _get_song_comments(first_id),
                    'message': '从数据库查询的歌曲资源',
                }

        return {
            'source': 'relational_db',
            'category': category,
            'subcategory': subcategory,
            'songs': songs,
            'first_song_resources': first_resources,
            'message': f'从数据库查询到 {len(songs)} 首歌曲',
        }
    except Exception as e:
        return {
            'source': 'relational_db_error',
            'category': category,
            'subcategory': subcategory,
            'songs': [],
            'first_song_resources': None,
            'message': f'数据库查询失败：{e}',
        }


def query_song_resources(category: str, subcategory: str, song_id: str, song_title: str = '') -> dict[str, Any]:
    """
    详情页切换下拉歌曲后 —— 按歌曲拉取音频、词云、评论、情感极性图。
    """
    from django.db import connection

    try:
        song_int_id = int(song_id)
    except ValueError:
        song_int_id = None

    if song_int_id is None:
        return {
            'source': 'relational_db_error',
            'song_id': song_id,
            'message': '无效的歌曲ID',
        }

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT title, audio_url, cover_url FROM traditional_song WHERE id = %s",
                [song_int_id]
            )
            song_result = cursor.fetchone()
            if not song_result:
                return {
                    'source': 'relational_db',
                    'song_id': str(song_int_id),
                    'message': '未找到该歌曲',
                }

            title, audio_url, cover_url = song_result

            if audio_url and not audio_url.startswith('http'):
                if audio_url.startswith('audio/'):
                    parts = audio_url.split('/')
                    if len(parts) >= 2:
                        encoded_parts = [urllib.parse.quote(p) for p in parts[1:] if p]
                        audio_url = f'/media/audio/{"/".join(encoded_parts)}'
                    else:
                        audio_url = ''
                elif '大创' in audio_url:
                    relative_path = audio_url.split('大创/', 1)[-1]
                    if relative_path.startswith('audio/'):
                        relative_path = relative_path[6:]
                    encoded_parts = [urllib.parse.quote(p) for p in relative_path.split('/') if p]
                    audio_url = f'/media/audio/{"/".join(encoded_parts)}'
                else:
                    services_dir = os.path.dirname(os.path.abspath(__file__))
                    backend_dir = os.path.dirname(services_dir)
                    media_audio_path = os.path.join(backend_dir, 'media', 'audio', category, subcategory)
                    if os.path.exists(media_audio_path):
                        audio_files = [f for f in os.listdir(media_audio_path) if f.endswith('.mp3')]
                        if audio_files:
                            encoded_category = urllib.parse.quote(category)
                            encoded_subcategory = urllib.parse.quote(subcategory)
                            encoded_filename = urllib.parse.quote(audio_files[0])
                            audio_url = f'/media/audio/{encoded_category}/{encoded_subcategory}/{encoded_filename}'
                        else:
                            audio_url = ''
                    else:
                        audio_url = ''
            if cover_url and not cover_url.startswith('http'):
                if '大创' in cover_url:
                    relative_path = cover_url.split('大创/', 1)[-1]
                else:
                    relative_path = cover_url
                cover_url = f'http://localhost:8000/media/{relative_path}'

            return {
                'song_id': str(song_int_id),
                'title': title,
                'category': category,
                'subcategory': subcategory,
                'audio_url': audio_url or '',
                'wordcloud_url': '',
                'emotion_polarity_chart_url': '',
                'cover_url': cover_url or '',
                'comments': _get_song_comments(song_int_id),
                'message': '从数据库查询的歌曲资源',
            }
    except Exception as e:
        return {
            'source': 'relational_db_error',
            'song_id': str(song_int_id),
            'message': f'数据库查询失败：{e}',
        }


def _get_song_comments(song_id: int) -> list[dict[str, Any]]:
    """从数据库获取歌曲评论。"""
    from django.db import connection

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT DISTINCT TOP 50 id, content, likes FROM [comment] WHERE song_id = %s AND content IS NOT NULL AND content != '' ORDER BY likes DESC",
                [song_id]
            )
            rows = cursor.fetchall()
            return [{'id': cid, 'text': content, 'likes': likes or 0} for cid, content, likes in rows]
    except Exception:
        return []


def get_emotion_polarity(song_id: int) -> dict[str, Any]:
    """从数据库获取歌曲评论情感极性统计。"""
    from django.db import connection

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT polarity 
                FROM [comment] 
                WHERE song_id = %s AND polarity IS NOT NULL
                """,
                [song_id]
            )
            rows = cursor.fetchall()
            
            total = len(rows)
            if total == 0:
                return {
                    'polarity_data': [
                        {'name': '中性', 'value': 1, 'percentage': 100},
                    ],
                    'total': 0
                }
            
            positive_count = 0
            negative_count = 0
            neutral_count = 0
            
            for polarity, in rows:
                if isinstance(polarity, str):
                    p = polarity.strip()
                    if p in ('正面', 'positive', '1', '积极'):
                        positive_count += 1
                    elif p in ('负面', 'negative', '-1', '消极'):
                        negative_count += 1
                    else:
                        neutral_count += 1
                else:
                    try:
                        score = float(polarity)
                        if score > 0:
                            positive_count += 1
                        elif score < 0:
                            negative_count += 1
                        else:
                            neutral_count += 1
                    except (ValueError, TypeError):
                        neutral_count += 1
            
            result = []
            if positive_count > 0:
                result.append({
                    'name': '积极',
                    'value': positive_count,
                    'percentage': round(positive_count / total * 100, 1)
                })
            if negative_count > 0:
                result.append({
                    'name': '消极',
                    'value': negative_count,
                    'percentage': round(negative_count / total * 100, 1)
                })
            if neutral_count > 0:
                result.append({
                    'name': '中性',
                    'value': neutral_count,
                    'percentage': round(neutral_count / total * 100, 1)
                })
            
            if not result:
                result = [{'name': '中性', 'value': 1, 'percentage': 100}]
            
            return {
                'polarity_data': result,
                'total': total
            }
    except Exception as e:
        return {
            'polarity_data': [{'name': '中性', 'value': 1, 'percentage': 100}],
            'total': 0,
            'error': str(e)
        }


def _placeholder_song_resources(
    category: str, subcategory: str, title: str, song_id: str
) -> dict[str, Any]:
    return {
        'song_id': song_id,
        'title': title,
        'category': category,
        'subcategory': subcategory,
        'audio_url': '',  # 待返回真实音频，前端缓存播放
        'wordcloud_url': '',  # 词云图资源占位
        'emotion_polarity_chart_url': '',  # 左下方情感极性图占位
        'comments': [
            {'id': 1, 'text': f'占位评论：{title} 真好听', 'likes': 120},
            {'id': 2, 'text': f'占位评论：喜欢{subcategory}风格', 'likes': 88},
            {'id': 3, 'text': '占位评论：国风永不过时', 'likes': 66},
            {'id': 4, 'text': '占位评论：循环中', 'likes': 40},
            {'id': 5, 'text': '占位评论：推荐给朋友了', 'likes': 21},
        ],
        'message': '占位歌曲资源包',
    }


def query_song_comments_top50(category: str, subcategory: str, song_title: str) -> dict[str, Any]:
    """查询指定歌曲点赞数最高的 50 条真实评论。"""
    from django.db import connection

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT TOP 50 c.id, c.content, COALESCE(c.likes, 0), c.polarity,
                          c.source, c.country, c.comment_time
            FROM dbo.comment AS c
            INNER JOIN dbo.traditional_song AS s ON s.id = c.song_id
            INNER JOIN dbo.music_category AS mc ON mc.category_id = s.category_id
            WHERE s.title = %s
              AND mc.parent_category = %s
              AND mc.category_name = %s
            ORDER BY COALESCE(c.likes, 0) DESC, c.id ASC
            """,
            [song_title, category, subcategory],
        )
        rows = cursor.fetchall()

    comments = [
        {
            'id': row[0],
            'text': row[1] or '',
            'likes': row[2] or 0,
            'polarity': row[3] or '',
            'source': row[4] or '',
            'country': row[5] or '',
            'comment_time': row[6].isoformat() if row[6] else '',
        }
        for row in rows
    ]
    return {
        'source': 'sqlserver',
        'category': category,
        'subcategory': subcategory,
        'song_title': song_title,
        'comments': comments,
        'message': f'已读取 {len(comments)} 条评论',
    }


def get_user_profile(username: str) -> dict[str, Any]:
    """从登录用户表读取可用的资料字段。"""
    from django.db import connection

    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT user_id, username, country, register_date "
            "FROM behave.Users WHERE username = %s",
            [username],
        )
        row = cursor.fetchone()

    if not row:
        return {
            'source': 'sqlserver',
            'username': username,
            'nickname': username,
            'email': '',
            'bio': '',
            'avatar_url': '',
            'message': '用户不存在',
        }

    return {
        'source': 'sqlserver',
        'user_id': str(row[0]),
        'username': row[1],
        'nickname': row[1],
        'country': row[2] or '',
        'register_date': row[3].isoformat() if row[3] else '',
        'email': '',
        'bio': '',
        'avatar_url': '',
        'message': '用户资料读取成功',
    }


def update_user_profile(username: str, payload: dict[str, Any]) -> dict[str, Any]:
    """更新 Users 表中实际存在的字段，并返回最新资料。"""
    from django.db import connection

    password = payload.get('password')
    if password:
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE behave.Users SET password = %s WHERE username = %s",
                [password, username],
            )
    profile = get_user_profile(username)
    profile['message'] = '用户资料已更新' if password else '当前数据库无可更新的扩展资料字段'
    return profile


from collections import defaultdict


def get_wordcloud_by_songid(song_id: str) -> list[dict[str, Any]]:
    """
    根据歌曲唯一ID获取词云ECharts标准数据数组
    归属模块：关系数据库查询模块（需求文档第3点）
    :param song_id: 歌曲唯一标识，格式 category-subcategory-title 或纯数字ID
    :return: [{name: 关键词, value: 出现频次}]
    """
    from django.db import connection

    try:
        song_int_id = int(song_id)
    except ValueError:
        song_int_id = None

    word_freq_dict = defaultdict(int)

    try:
        with connection.cursor() as cursor:
            if song_int_id is not None:
                cursor.execute(
                    "SELECT TOP 100 keywords FROM [comment] WHERE song_id = %s AND keywords IS NOT NULL AND keywords != ''",
                    [song_int_id]
                )
            else:
                parts = song_id.split('-')
                if len(parts) >= 3:
                    title = parts[-1]
                    cursor.execute("SELECT id FROM traditional_song WHERE title LIKE %s", [f'%{title}%'])
                    song_result = cursor.fetchone()
                    if song_result:
                        cursor.execute(
                            "SELECT TOP 100 keywords FROM [comment] WHERE song_id = %s AND keywords IS NOT NULL AND keywords != ''",
                            [song_result[0]]
                        )
                    else:
                        return []
                else:
                    return []

            results = cursor.fetchall()
            for row in results:
                keywords_str = row[0]
                if keywords_str:
                    try:
                        keywords = json.loads(keywords_str)
                    except (json.JSONDecodeError, TypeError):
                        try:
                            keywords = eval(keywords_str)
                        except (SyntaxError, TypeError):
                            continue
                    
                    if isinstance(keywords, list):
                        for word in keywords:
                            if word and isinstance(word, str) and len(word.strip()) > 0:
                                word_freq_dict[word.strip()] += 1

    except Exception:
        pass

    result = [{"name": word, "value": count} for word, count in word_freq_dict.items() if count > 0]
    result.sort(key=lambda x: x['value'], reverse=True)
    return result[:100]
