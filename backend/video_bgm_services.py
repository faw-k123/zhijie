"""视频配乐模块：AI分析视频截图 → 推荐音乐 → 生成理由

使用阿里云百炼 Qwen3.6-Plus 视觉模型分析视频截图。
"""

import os
import json
from django.db import connection
from config import services as svc_config


def _call_qwen_vision(prompt: str, image_data: str = '') -> str:
    """
    调用阿里云百炼 Qwen 视觉模型（OpenAI 兼容格式）。

    :param prompt: 文本提示
    :param image_data: base64 编码的图片（data:image/...;base64,...）；为空则纯文本调用
    :return: 模型回复的文本内容
    """
    import requests

    cfg = svc_config.VIDEO_VISION_AI
    base_url = cfg['BASE_URL'].rstrip('/')
    api_key = cfg.get('API_KEY', '')
    model = cfg.get('MODEL', 'qwen3.6-plus')
    timeout = cfg.get('TIMEOUT_SECONDS', 60)

    # 组装消息：支持多模态（图片+文本）
    if image_data:
        content = [
            {'type': 'text', 'text': prompt},
            {'type': 'image_url', 'image_url': {'url': image_data}},
        ]
    else:
        content = prompt

    resp = requests.post(
        f'{base_url}/chat/completions',
        headers={
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
        },
        json={
            'model': model,
            'messages': [{'role': 'user', 'content': content}],
            'max_tokens': 800,
        },
        timeout=timeout,
    )
    resp.raise_for_status()
    return resp.json()['choices'][0]['message']['content']


def analyze_video_frame(image_data):
    """
    调用 Qwen3.6-Plus 视觉模型分析视频截图。

    image_data: base64编码的图片（data:image/jpeg;base64,...）
    返回: {"scene":"场景","mood":"情绪","character":"人物","rhythm":"节奏"}
    """
    prompt = (
        '请分析这张视频截图，输出严格的 JSON 格式（不要其他内容、不要 markdown 代码块）：'
        '{"scene":"场景描述(如江南园林/山水自然/古建筑等)",'
        '"mood":"情绪(如宁静/激昂/欢快/悲伤/神秘)",'
        '"character":"人物或服饰特征(如汉服/无人物)",'
        '"rhythm":"节奏(如舒缓/紧凑/中等)"}'
    )
    try:
        content = _call_qwen_vision(prompt, image_data)
        # 兼容模型可能输出 markdown 代码块的情况
        if '```' in content:
            # 提取 ``` 之间的内容
            parts = content.split('```')
            for p in parts:
                p = p.strip()
                if p.startswith('json'):
                    p = p[4:].strip()
                if p.startswith('{') and p.endswith('}'):
                    content = p
                    break
        start = content.find('{')
        end = content.rfind('}') + 1
        if start >= 0 and end > start:
            return json.loads(content[start:end])
    except Exception as e:
        # 诊断信息打印到 stderr（Django 日志可见）
        import sys
        print(f'[video_bgm] analyze_video_frame failed: {e}', file=sys.stderr)
    return {'scene': '自然风景', 'mood': '宁静', 'character': '无人物', 'rhythm': '舒缓'}


# 情绪→乐器 映射
MOOD_GENRE_MAP = {
    '宁静': ['古琴', '古筝', '箫'],
    '激昂': ['唢呐', '大鼓', '琵琶'],
    '欢快': ['笛子', '葫芦丝', '琵琶'],
    '悲伤': ['二胡', '埙', '箫'],
    '神秘': ['古琴', '埙'],
    '舒缓': ['古琴', '古筝', '箫'],
    '紧凑': ['琵琶', '唢呐', '笛子'],
}

SCENE_GENRE_MAP = {
    '园林': ['古琴', '古筝'],
    '山水': ['古琴', '箫'],
    '宫廷': ['编钟', '大鼓'],
    '战争': ['琵琶', '唢呐', '大鼓'],
    '田园': ['笛子', '葫芦丝'],
    '节日': ['唢呐', '大鼓'],
    '茶': ['古琴', '箫'],
}


def recommend_music(analysis):
    """根据分析结果推荐音乐"""
    mood = analysis.get('mood', '宁静')
    scene = analysis.get('scene', '')
    genres = set()
    for key, glist in MOOD_GENRE_MAP.items():
        if key in mood:
            genres.update(glist)
    for key, glist in SCENE_GENRE_MAP.items():
        if key in scene:
            genres.update(glist)
    if not genres:
        genres = {'古琴', '古筝', '笛子'}
    placeholders = ','.join(['%s'] * len(genres))
    with connection.cursor() as cur:
        cur.execute(
            f"SELECT TOP 5 id, title, genre, audio_url, cover_url "
            f"FROM traditional_song WHERE genre IN ({placeholders}) "
            f"AND audio_url IS NOT NULL AND audio_url != '' ORDER BY id",
            list(genres)
        )
        rows = cur.fetchall()
    return [
        {'id': r[0], 'title': r[1], 'genre': r[2], 'audio_url': r[3], 'cover_url': r[4]}
        for r in rows
    ]


def generate_reason(analysis, recommendations):
    """调用 Qwen3.6-Plus 生成推荐理由"""
    song_list = '、'.join(s['title'] for s in recommendations[:3])
    prompt = (
        f'视频分析结果：场景={analysis["scene"]}，情绪={analysis["mood"]}，'
        f'人物={analysis["character"]}，节奏={analysis["rhythm"]}。'
        f'推荐了以下中国传统音乐：{song_list}。'
        f'请用2-3句话说明推荐理由，突出视频内容与音乐风格的契合。'
    )
    try:
        return _call_qwen_vision(prompt).strip()
    except Exception as e:
        import sys
        print(f'[video_bgm] generate_reason failed: {e}', file=sys.stderr)
        return (
            f'视频整体{analysis["mood"]}，节奏{analysis["rhythm"]}，'
            f'推荐的传统音乐在情感氛围和文化意境上与视频高度契合。'
        )
