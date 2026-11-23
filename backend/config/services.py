"""
集中存放 AI、数据库等外部服务配置。

说明：
- 本文件只负责「配置与连接参数」，不实现业务逻辑。
- 各业务模块通过 import 本文件读取配置，再自行建立连接 / 调用 SDK。
- 当前均为占位值，部署前请替换为真实环境变量或密钥管理方案。
"""

import os

# ---------------------------------------------------------------------------
# 关系数据库（面向：多维度数据展示模块的关系库查询；
#           个性化模块的用户信息 / 听歌记录 / 人格结果持久化；
#           个人资料读写）
# ---------------------------------------------------------------------------
RELATIONAL_DB = {
    'ENGINE': os.getenv('DB_ENGINE', 'mssql'),
    'NAME': os.getenv('DB_NAME', 'music_db'),
    'USER': os.getenv('DB_USER', ''),
    'PASSWORD': os.getenv('DB_PASSWORD', ''),
    'HOST': os.getenv('DB_HOST', 'localhost'),
    'PORT': os.getenv('DB_PORT', '1433'),
    'DRIVER': os.getenv('DB_DRIVER', 'ODBC Driver 18 for SQL Server'),
    'EXTRA_PARAMS': os.getenv(
        'DB_EXTRA_PARAMS',
        'Encrypt=yes;TrustServerCertificate=yes;Trusted_Connection=yes',
    ),
    # 服务对象注释：
    # - data_display.relational_query：大类介绍、小类列表、歌曲列表、音频/词云/评论等资源查询
    # - personalization：用户资料、听歌记录、人格测试结果读写
    # - profile 接口：用户详细信息查询与更新
}

# ---------------------------------------------------------------------------
# Neo4j 图数据库 · 1（面向：多维度数据展示模块的图谱展示 / KG-RAG）
# 严禁回退：本库连不上直接报错，不会转连其它 Neo4j。
# ---------------------------------------------------------------------------
NEO4J = {
    'URI': os.getenv('NEO4J_URI', 'neo4j://127.0.0.1:7687'),
    'USER': os.getenv('NEO4J_USER', 'neo4j'),
    'PASSWORD': os.getenv('NEO4J_PASSWORD', ''),
    'DATABASE': os.getenv('NEO4J_DATABASE', 'neo4j'),
    'MAX_POOL': int(os.getenv('NEO4J_MAX_POOL', '50')),
    # 服务对象注释：
    # - data_display.neo4j_client.get_driver：大类小类图谱、KG-RAG 问答
}

# ---------------------------------------------------------------------------
# Neo4j 图数据库 · 2（面向：imagery 圈层/场景/事物/情感图查询）
# 严禁回退：本库连不上直接报错，不会转连其它 Neo4j。
# ---------------------------------------------------------------------------
IMAGERY_NEO4J = {
    'URI': os.getenv('IMAGERY_NEO4J_URI', os.getenv('NEO4J_URI', 'neo4j://127.0.0.1:7687')),
    'USER': os.getenv('IMAGERY_NEO4J_USER', os.getenv('NEO4J_USER', 'neo4j')),
    'PASSWORD': os.getenv('IMAGERY_NEO4J_PASSWORD', os.getenv('NEO4J_PASSWORD', '')),
    'DATABASE': os.getenv('IMAGERY_NEO4J_DATABASE', os.getenv('NEO4J_DATABASE', 'neo4j')),
    # 服务对象注释：
    # - imagery.match_user_circle：用户七大元素 → 文化圈层
    # - imagery.query_possible_emotions：场景+事物 → 可能情感（反向）
    # - imagery.query_common_scenes_things：情感 → 常触发场景/事物（正向）
}

# ---------------------------------------------------------------------------
# Neo4j 图数据库 · 3（面向：个性化模块 · 基于用户人设的曲目推荐）
# 严禁回退：本库连不上直接报错，不会转连其它 Neo4j。
#
# 图结构（对应 Desktop import CSV + Cypher）：
#   (UserCluster)-[:HAS_ATTR {value,side:'user'}]->(Attribute)
#   (UserCluster)-[:MAPS_TO {count,weight}]->(MusicCluster)
#   (UserCluster)-[:LIKES {count}]->(Music)
#   (MusicCluster)-[:CONTAINS]->(Music)
#   (MusicCluster)-[:HAS_ATTR {value,side:'music_cluster'}]->(Attribute)
#   (Music)-[:HAS_ATTR {value,side:'music'}]->(Attribute)
# 主推荐路径：人设→五属性 → 最近 UserCluster → LIKES 热度 Top3 歌曲
# 属性：潮流娱乐 / 中国文化 / 旅行户外 / 健康养生 / 美妆时尚
# ---------------------------------------------------------------------------
NEO4J_3 = {
    'URI': os.getenv('RECOMMEND_NEO4J_URI', os.getenv('NEO4J_URI', 'neo4j://127.0.0.1:7687')),
    'USER': os.getenv('RECOMMEND_NEO4J_USER', os.getenv('NEO4J_USER', 'neo4j')),
    'PASSWORD': os.getenv('RECOMMEND_NEO4J_PASSWORD', os.getenv('NEO4J_PASSWORD', '')),
    'DATABASE': os.getenv('RECOMMEND_NEO4J_DATABASE', os.getenv('NEO4J_DATABASE', 'neo4j')),
    'LABELS': {
        'UserCluster': 'UserCluster',
        'MusicCluster': 'MusicCluster',
        'Music': 'Music',
        'Attribute': 'Attribute',
    },
    'RELS': {
        # (UserCluster|MusicCluster|Music)-[:HAS_ATTR {value, side}]->(Attribute)
        'cluster_attr': 'HAS_ATTR',
        # (UserCluster)-[:MAPS_TO {count, weight}]->(MusicCluster)
        'maps_to': 'MAPS_TO',
        # (UserCluster)-[:LIKES {count}]->(Music)
        'likes': 'LIKES',
        # (MusicCluster)-[:CONTAINS]->(Music)
        'contains': 'CONTAINS',
    },
    # 服务对象注释：
    # - personalization.recommend_by_persona：
    #   人设→五属性 → 最近 UserCluster → LIKES Top3（不足再 CONTAINS / 随机补）
}

# ---------------------------------------------------------------------------
# 可选兜底：MusicCluster → 歌曲 id（图 CONTAINS 不可用时才读此表）
# ---------------------------------------------------------------------------
MUSIC_CLUSTER_SONGS: dict[str, list[int | str]] = {
}

# ---------------------------------------------------------------------------
# music_id（图 Music.id）→ 本地资源
# title = 展示名；detail_id = media/resources 目录对应的 res-*（可与展示名略有差异）
# ---------------------------------------------------------------------------
MUSIC_ID_MAP: dict[int | str, dict[str, str]] = {
    1: {'title': '男儿当自强（唢呐版）', 'detail_id': 'res-男儿当自强（唢呐版）'},
    2: {'title': '故梦', 'detail_id': 'res-故梦'},
    3: {'title': '偷功', 'detail_id': 'res-偷功'},
    4: {'title': '水墨兰亭', 'detail_id': 'res-水墨兰亭'},
    5: {'title': '往事只能回味', 'detail_id': 'res-往事只能回味'},
    6: {'title': '八方来财', 'detail_id': 'res-八方来财'},
    7: {'title': '辞九门回忆', 'detail_id': 'res-辞九门回忆'},
    8: {'title': '没有理由', 'detail_id': 'res-没有理由'},
    # 图侧「宏」→ 本地文件夹「鸿」
    9: {'title': '大展宏图', 'detail_id': 'res-大展鸿图'},
    10: {'title': 'Eutopia（竹笛版）', 'detail_id': 'res-Eutopia（竹笛版）'},
    11: {'title': '国风配乐（三顾茅庐）-凯枫', 'detail_id': 'res-国风配乐（三顾茅庐）'},
    12: {'title': '一笑江湖', 'detail_id': 'res-一笑江湖'},
    13: {'title': '万疆', 'detail_id': 'res-万疆'},
    14: {'title': '凉凉', 'detail_id': 'res-凉凉'},
    15: {'title': '芒种', 'detail_id': 'res-芒种'},
    16: {'title': '莫问归期', 'detail_id': 'res-莫问归期'},
    17: {'title': '江上清风游', 'detail_id': 'res-江上清风游'},
    # 图侧「笛箫版」→ 本地「纯音独享版」
    18: {'title': '弱水三千（笛箫版）', 'detail_id': 'res-弱水三千（纯音独享版）'},
    # 图侧「纯男声版」→ 本地「男声版」
    19: {'title': '美丽的神话（纯男声版）', 'detail_id': 'res-美丽的神话（男声版）'},
    20: {'title': '我的新衣（VaVa娃娃）', 'detail_id': 'res-我的新衣'},
    21: {'title': '今生缘（烟嗓版）', 'detail_id': 'res-今生缘（烟嗓版）'},
    22: {'title': '弥渡山歌', 'detail_id': 'res-弥渡山歌'},
    23: {'title': '半山听雨', 'detail_id': 'res-半山听雨'},
    24: {'title': '离开我的依赖', 'detail_id': 'res-离开我的依赖'},
    25: {'title': '美丽的神话', 'detail_id': 'res-美丽的神话'},
    26: {'title': '霍元甲', 'detail_id': 'res-霍元甲'},
    27: {'title': '精卫（旧梦散入尘埃DJ版）', 'detail_id': 'res-精卫（旧梦散入尘埃DJ版）'},
}

# ---------------------------------------------------------------------------
# 意象解析 · 内接 AI（面向：把两大查询结果 + 提示词交给模型生成用户可读解释）
# ---------------------------------------------------------------------------
IMAGERY_AI = {
    'PROVIDER': os.getenv('IMAGERY_AI_PROVIDER', 'deepseek'),
    'BASE_URL': os.getenv('IMAGERY_AI_BASE_URL', 'https://api.deepseek.com'),
    'API_KEY': os.getenv('IMAGERY_AI_API_KEY', ''),
    'MODEL': os.getenv('IMAGERY_AI_MODEL', 'deepseek-chat'),
    'TIMEOUT_SECONDS': 60,
    # 服务对象注释：
    # - imagery.explain_with_ai：TEST_MODE=False 时调用，生成意象解析文案
}

# ---------------------------------------------------------------------------
# 联调 / 演示测试开关（意象译析 + 私人空间推荐共用）
# True  → 前端菜单栏显示「文化圈层」「音乐画像」下拉框；请求可携带覆盖值
# False → 不下发测试 UI，一律走真实属性计算（用户问卷/人设结果）
# 说明：意象三大查询结果仍会交给 IMAGERY_AI 生成解释文案后返回前端。
# ---------------------------------------------------------------------------
IMAGERY_TEST_MODE = os.getenv('IMAGERY_TEST_MODE', 'false').lower() in ('1', 'true', 'yes', 'on')

# ---------------------------------------------------------------------------
# 意象解析 · 服务端默认圈层覆盖（仅当 IMAGERY_TEST_MODE=True 且请求未带 circle_override 时生效）
# 日常联调请用前端下拉框选择；此处保留作无前端参数时的兜底。
# 0  → 真实属性计算（自动匹配）
# 1  → 东亚文化圈                  / 中国
# 2  → 朝鲜半岛文化圈              / 韩国
# 3  → 日本文化圈                  / 日本
# 4  → 哈萨克斯坦草原文化圈层      / 哈萨克斯坦
# 5  → 苏联集体主义/工农兵圈层     / 俄罗斯
# ---------------------------------------------------------------------------
IMAGERY_TEST_CIRCLE_OVERRIDE = 0

# 测试 UI：文化圈层置顶五项（联调常用；其余圈层仍会出现在下拉框中）
TEST_PRIORITY_CULTURAL_CIRCLES = [
    '东亚文化圈',
    '朝鲜半岛文化圈',
    '日本文化圈',
    '哈萨克斯坦草原文化圈层',
    '苏联集体主义/工农兵圈层',
]

# 兼容旧编号 → 圈层名（前端若仍传 1~5）
TEST_CIRCLE_ID_TO_NAME = {
    1: '东亚文化圈',
    2: '朝鲜半岛文化圈',
    3: '日本文化圈',
    4: '哈萨克斯坦草原文化圈层',
    5: '苏联集体主义/工农兵圈层',
}

# 测试 UI：音乐画像类别（与 personalization.GUOFENG_PERSONAS 名称对齐；auto=真实计算）
TEST_MUSIC_PERSONA_OPTIONS = [
    {'value': 'auto', 'label': '真实属性计算'},
    {'value': '国风挚爱型', 'label': '国风挚爱型'},
    {'value': '潮流融合型', 'label': '潮流融合型'},
    {'value': '社交达人型', 'label': '社交达人型'},
    {'value': '静赏体验型', 'label': '静赏体验型'},
    {'value': '泛兴趣尝鲜型', 'label': '泛兴趣尝鲜型'},
]


def is_test_mode() -> bool:
    return bool(IMAGERY_TEST_MODE)


def _all_cultural_circle_names() -> list[str]:
    """
    全部可选文化圈层名：
    1) 置顶五圈
    2) 前端 culturalCircles 全量（对齐意象图 Circle.name）
    3) personalization.CULTURAL_CIRCLES 补遗
    """
    ordered: list[str] = []
    seen: set[str] = set()

    def _add(name: str) -> None:
        n = (name or '').strip()
        if not n or n in seen:
            return
        seen.add(n)
        ordered.append(n)

    for n in TEST_PRIORITY_CULTURAL_CIRCLES:
        _add(n)

    try:
        from config._cultural_circle_names_gen import ALL_CULTURAL_CIRCLE_NAMES
        for n in ALL_CULTURAL_CIRCLE_NAMES:
            _add(n)
    except Exception:
        pass

    try:
        from personalization.services import CULTURAL_CIRCLES
        for row in CULTURAL_CIRCLES:
            _add(str(row.get('name') or ''))
    except Exception:
        pass

    return ordered


def get_test_cultural_circle_options() -> list[dict]:
    """下拉选项：真实属性计算 + 置顶五圈 + 其余全部圈层。"""
    options = [{'value': 'auto', 'label': '真实属性计算'}]
    for name in _all_cultural_circle_names():
        options.append({'value': name, 'label': name})
    return options


def get_test_ui_options() -> dict:
    """供前端菜单栏读取：是否显示测试下拉框及选项列表。"""
    return {
        'test_mode': is_test_mode(),
        'cultural_circles': get_test_cultural_circle_options(),
        'music_personas': list(TEST_MUSIC_PERSONA_OPTIONS),
    }

# KG-RAG问答AI接口（后续接入大模型，现在占位）
KG_RAG = {
    'ENDPOINT': 'http://127.0.0.1:8001/rag/chat',
    'TIMEOUT': 10
}

# 情感分析、传播预测AI接口统一放这里
EMOTION_AI = {
    'ENDPOINT': 'http://127.0.0.1:8002/emotion'
}
# ---------------------------------------------------------------------------
# 通用大模型 / 文生接口（面向：宣传报告生成、人格评测中的 AI 分析、AI 报告等）
# ---------------------------------------------------------------------------
LLM = {
    'PROVIDER': 'doubao',  # 豆包（火山方舟）API，兼容 OpenAI 格式
    'BASE_URL': 'https://ark.cn-beijing.volces.com/api/v3',
    'API_KEY': os.getenv('LLM_API_KEY', ''),
    'MODEL': os.getenv('LLM_MODEL', 'doubao-seed-2-0-lite-260428'),
    'TIMEOUT_SECONDS': 60,
    # 服务对象注释：
    # - propagation.promo_report_generate：宣传报告生成页文案生成
    # - propagation.ai_report_generate：情感分析详情页「AI报告生成」Tab
    # - personalization.personality_evaluate：人格测试提交后的 AI 评测报告
}

# ---------------------------------------------------------------------------
# 情感分析模型服务（面向：情感分析与预测模块）
# ---------------------------------------------------------------------------
EMOTION_MODEL = {
    'ENDPOINT': 'http://127.0.0.1:9002/emotion/analyze',
    'API_KEY': '',
    'TIMEOUT_SECONDS': 90,
    # 服务对象注释：
    # - emotion_analysis.analyze_song_emotion：详情页「情感分析」Tab，按歌曲返回情感分析结果
}

# ---------------------------------------------------------------------------
# 传播分析与预测服务（面向：传播分析与宣传报告生成模块）
# ---------------------------------------------------------------------------
PROPAGATION_MODEL = {
    'ENDPOINT': 'http://127.0.0.1:9003/propagation/analyze',
    'API_KEY': '',
    'TIMEOUT_SECONDS': 90,
    # 服务对象注释：
    # - propagation.analyze_and_predict：全球传播效果页右侧「传播数据分析 / 传播异常分析」
}

# ---------------------------------------------------------------------------
# 音乐生成 AI（面向：个性化与互动性模块 · AI 生成国风音乐）
# 使用 Apiframe Suno AI：https://docs.apiframe.ai/api
# 提交任务后异步轮询，返回音频 URL
# ---------------------------------------------------------------------------
MUSIC_GENERATION_AI = {
    'BASE_URL': os.getenv('MUSIC_GENERATION_BASE_URL', 'https://api.apiframe.ai'),
    'API_KEY': os.getenv('MUSIC_GENERATION_API_KEY', ''),
    'TIMEOUT_SECONDS': 300,
    # 服务对象注释：
    # - personalization.generate_guofeng_music：趣味互动「AI生成国风音乐」页
}

# ---------------------------------------------------------------------------
# 视频分析 AI（面向：视频配乐模块 · 分析视频截图）
# 阿里云百炼 Qwen3.6-Plus（OpenAI 兼容模式，多模态视觉模型）
# 工作空间专属接入点：{workspaceId}.cn-beijing.maas.aliyuncs.com/compatible-mode/v1
# 文档：https://help.aliyun.com/zh/model-studio/qwen-vl-compatible-with-openai
# ---------------------------------------------------------------------------
VIDEO_VISION_AI = {
    'API_HOST': os.getenv('VIDEO_VISION_API_HOST', 'dashscope.aliyuncs.com'),
    'BASE_URL': f"https://{os.getenv('VIDEO_VISION_API_HOST', 'dashscope.aliyuncs.com')}/compatible-mode/v1",
    'API_KEY': os.getenv('VIDEO_VISION_API_KEY', ''),
    'MODEL': os.getenv('VIDEO_VISION_MODEL', 'qwen3.6-plus'),
    'WORKSPACE_ID': os.getenv('VIDEO_VISION_WORKSPACE_ID', ''),
    'TIMEOUT_SECONDS': 60,
    # 服务对象注释：
    # - video_bgm_services.analyze_video_frame：分析视频截图场景/情绪/人物/节奏
    # - video_bgm_services.generate_reason：基于分析结果生成推荐理由
}
