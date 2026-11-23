"""
个性化与互动性模块（Django 应用：personalization）

数据存储：
- 题库：dbo.question（大五人格 20 题）
- 人格测试结果：behave.PersonalityTests（user_id 关联）
- 用户表：behave.Users
- 文化圈层测试结果：cultural_circle_test（Django ORM）

已实现能力：
1. 人格评测（大五人格 20 题问卷 → 评分 → 画像标签 → 音乐推荐）
2. 文化圈层测试（35题问卷 → 七维得分 → 文化圈层匹配）
3. 猜你喜欢 / 个性化推荐（依赖人格结果推荐传统音乐）
4. 听歌行为记录
5. AI 生成国风音乐（接口预留）
"""

from __future__ import annotations

import json
import urllib.parse
from typing import Any

import requests
from django.db import connection

from config import services as svc_config

# 内存占位：听歌记录（待改为关系数据库持久化）
_LISTEN_LOGS: dict[str, list[dict[str, Any]]] = {}


def get_similar_songs(song_id: str, limit: int = 3) -> dict[str, Any]:
    """返回与当前歌曲相近的曲目，兼容本地资源 ID 和数据库数字 ID。"""
    if song_id.startswith('res-'):
        from data_display.services import refresh_catalog

        catalog = refresh_catalog()
        current = next((item for item in catalog if item.get('id') == song_id), None)
        if not current:
            return {'items': []}
        current_tags = set(
            (current.get('scene_tags') or [])
            + (current.get('thing_tags') or [])
            + (current.get('emotion_tags') or [])
        )

        def similarity(item: dict[str, Any]) -> tuple[int, int, str]:
            item_tags = set(
                (item.get('scene_tags') or [])
                + (item.get('thing_tags') or [])
                + (item.get('emotion_tags') or [])
            )
            return (
                len(current_tags & item_tags),
                1 if item.get('featured') else 0,
                str(item.get('title') or ''),
            )

        candidates = [item for item in catalog if item.get('id') != song_id and str(item.get('id', '')).startswith('res-')]
        candidates.sort(key=similarity, reverse=True)
        items = [
            {
                'id': str(item.get('id') or ''),
                'title': item.get('title') or '',
                'intro': item.get('intro') or '',
                'mv_url': item.get('mv_url') or '',
                'audio_url': item.get('audio_url') or '',
                'cover_url': item.get('cover_url') or '',
                'resource_url': f"/api/content/music-resource/?id={urllib.parse.quote(str(item.get('id') or ''))}",
            }
            for item in candidates[:limit]
        ]
        return {'items': items}

    try:
        numeric_id = int(song_id)
    except (TypeError, ValueError):
        return {'items': []}

    with connection.cursor() as cur:
        cur.execute("SELECT category_id FROM dbo.traditional_song WHERE id = %s", [numeric_id])
        row = cur.fetchone()
        if not row:
            return {'items': []}
        cur.execute(
            """
            SELECT TOP (%s) id, title, genre, audio_url, cover_url
            FROM dbo.traditional_song
            WHERE category_id = %s AND id <> %s
            ORDER BY CASE WHEN audio_url LIKE 'audio/%%' THEN 0 ELSE 1 END, id
            """,
            [limit, row[0], numeric_id],
        )
        rows = cur.fetchall()

    items = []
    for item in rows:
        audio_url = item[3] or ''
        if audio_url.startswith('audio/'):
            audio_url = '/media/' + '/'.join(urllib.parse.quote(part) for part in audio_url.split('/'))
        cover_url = item[4] or ''
        if cover_url and not cover_url.startswith(('http://', 'https://', '/')):
            cover_url = '/media/' + '/'.join(urllib.parse.quote(part) for part in cover_url.split('/'))
        items.append({
            'id': str(item[0]),
            'title': item[1] or '',
            'intro': item[2] or '',
            'mv_url': '',
            'audio_url': audio_url,
            'cover_url': cover_url,
            'resource_url': f'/api/emotion/song-resources/?song_id={item[0]}',
        })
    return {'items': items}


# ========================= 题库 =========================

def get_questions() -> list[dict[str, Any]]:
    """从数据库获取人格测试题库（大五人格 20 题）。"""
    with connection.cursor() as cur:
        cur.execute("SELECT id, text, dimension, reverse FROM question ORDER BY id")
        rows = cur.fetchall()
    return [
        {'id': r[0], 'text': r[1], 'dimension': r[2], 'reverse': bool(r[3])}
        for r in rows
    ]


# ========================= 人格评测 =========================

# 维度中文名
DIM_NAMES = {
    'O': '开放性',
    'C': '责任心',
    'E': '外向性',
    'A': '宜人性',
    'N': '神经质',
}

# 维度 → 推荐的乐器/曲种
DIM_RECOMMEND_GENRES = {
    'O': ['笛子', '葫芦丝', '马头琴', '阮'],        # 创新探索
    'C': ['古琴', '编钟'],                          # 古典经典
    'E': ['大鼓', '唢呐', '琵琶'],                  # 热烈激昂
    'A': ['古筝', '箫'],                            # 温和柔美
    'N': ['古琴', '埙', '箫'],                       # 舒缓安抚
}

# 维度 → 高分标签
DIM_TAGS = {
    'O': '喜欢探索',
    'C': '规划型',
    'E': '社交型',
    'A': '包容型',
    'N': '情绪敏感',
}


def evaluate_personality(user_id: str, answers: list[dict[str, Any]]) -> dict[str, Any]:
    """
    人格评测核心：
    1. 按维度计算平均分，换算百分制
    2. 生成画像标签
    3. 推荐音乐
    4. 写入 behave.PersonalityTests 表
    5. 调用 LLM 生成画像描述

    answers: [{question_id, score}, ...]  score: 1-5
    """
    # 1. 按维度汇总得分
    dim_scores: dict[str, list[int]] = {'O': [], 'C': [], 'E': [], 'A': [], 'N': []}
    with connection.cursor() as cur:
        cur.execute("SELECT id, dimension, reverse FROM question")
        q_map = {r[0]: (r[1], bool(r[2])) for r in cur.fetchall()}

    for a in answers:
        qid = a['question_id']
        score = int(a['score'])
        if qid not in q_map:
            continue
        dim, reverse = q_map[qid]
        if reverse:
            score = 6 - score  # 反向计分
        dim_scores[dim].append(score)

    # 2. 计算百分制得分
    dim_percent = {}
    for dim, scores in dim_scores.items():
        if scores:
            avg = sum(scores) / len(scores)  # 1.0 - 5.0
            dim_percent[dim] = round(avg * 20)  # 20 - 100
        else:
            dim_percent[dim] = 0

    # 3. 生成标签
    tags = []
    for dim, percent in dim_percent.items():
        if percent >= 70:
            tags.append(DIM_TAGS[dim])
    # 补充综合标签
    o = dim_percent['O']
    a_score = dim_percent['A']
    if o >= 70 and a_score >= 70:
        tags.append('文化体验者')
    if dim_percent['C'] >= 70 and dim_percent['N'] <= 40:
        tags.append('沉稳型')
    if not tags:
        tags.append('均衡型')

    # 4. 生成描述
    description = _build_description(dim_percent, tags)

    # 5. 推荐音乐
    recommendations = _recommend_songs(dim_percent)

    # 6. 生成 AI 推荐理由（调用 LLM）
    ai_reason = _generate_ai_reason(dim_percent, tags, recommendations[:3])

    # 7. 推荐方向
    recommend_directions = []
    seen = set()
    for dim, percent in dim_percent.items():
        if percent >= 70:
            for g in DIM_RECOMMEND_GENRES.get(dim, []):
                if g not in seen:
                    seen.add(g)
                    recommend_directions.append(g)
    if not recommend_directions:
        recommend_directions = ['古琴', '古筝', '笛子']

    # 8. 组装完整结果
    result = {
        'scores': {
            'openness': dim_percent['O'],
            'conscientiousness': dim_percent['C'],
            'extraversion': dim_percent['E'],
            'agreeableness': dim_percent['A'],
            'neuroticism': dim_percent['N'],
        },
        'tags': tags,
        'description': description,
        'recommendations': recommendations,
        'recommend_directions': recommend_directions,
        'ai_reason': ai_reason,
    }

    # 9. 写入 behave.PersonalityTests 表（仅当用户存在时）
    personality_type = tags[0] if tags else '均衡型'
    result_json = json.dumps(result, ensure_ascii=False)
    with connection.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM behave.Users WHERE user_id = %s", [user_id])
        exists = cur.fetchone()[0]
        if exists:
            cur.execute(
                "INSERT INTO behave.PersonalityTests (user_id, personality_type, result_detail, test_date) "
                "VALUES (%s, %s, %s, GETDATE())",
                [user_id, personality_type, result_json],
            )

    return result


def _build_description(scores: dict[str, int], tags: list[str]) -> str:
    """根据维度得分和标签生成画像描述。"""
    o, c, e, a, n = scores['O'], scores['C'], scores['E'], scores['A'], scores['N']
    parts = []
    if o > 70:
        parts.append('你乐于接受不同文化，喜欢探索新的音乐风格')
    elif o < 40:
        parts.append('你偏好熟悉的事物，喜欢经典的传统音乐')
    else:
        parts.append('你对新事物保持适度的好奇')

    if e > 70:
        parts.append('喜欢分享和社交')
    elif e < 40:
        parts.append('更喜欢独自沉浸于音乐世界')
    else:
        parts.append('在独处与社交间保持平衡')

    if n > 70:
        parts.append('容易被音乐触动情绪')
    elif n < 40:
        parts.append('情绪较为稳定')
    else:
        parts.append('情绪感受适中')

    tag_str = '、'.join(tags) if tags else '均衡型'
    return f'你的画像：{tag_str}。{"，".join(parts)}。适合体验具有历史背景的中国传统音乐。'


def _recommend_songs(scores: dict[str, int]) -> list[dict[str, Any]]:
    """根据人格维度得分推荐音乐。"""
    recommended_genres = set()
    for dim, percent in scores.items():
        if percent >= 70:
            recommended_genres.update(DIM_RECOMMEND_GENRES.get(dim, []))

    # 如果没有高分维度，推荐综合性的曲目
    if not recommended_genres:
        recommended_genres = {'古琴', '古筝', '笛子'}

    # 从数据库查询推荐曲目
    placeholders = ','.join(['%s'] * len(recommended_genres))
    query = (
        f"SELECT TOP 8 id, title, genre, audio_url, cover_url "
        f"FROM traditional_song WHERE genre IN ({placeholders}) "
        f"AND audio_url IS NOT NULL AND audio_url != '' "
        f"ORDER BY id"
    )
    with connection.cursor() as cur:
        cur.execute(query, list(recommended_genres))
        rows = cur.fetchall()

    result = []
    for r in rows:
        audio_url = r[3]
        cover_url = r[4]
        
        if audio_url and not audio_url.startswith('http'):
            if audio_url.startswith('audio/'):
                parts = audio_url.split('/')
                if len(parts) >= 2:
                    encoded_parts = [urllib.parse.quote(p) for p in parts[1:] if p]
                    audio_url = f'/media/audio/{"/".join(encoded_parts)}'
        
        if cover_url and not cover_url.startswith('http'):
            if cover_url.startswith('images/'):
                parts = cover_url.split('/')
                if len(parts) >= 2:
                    encoded_parts = [urllib.parse.quote(p) for p in parts[1:] if p]
                    cover_url = f'/media/images/{"/".join(encoded_parts)}'
        
        result.append({
            'id': r[0],
            'title': r[1],
            'genre': r[2],
            'audio_url': audio_url,
            'cover_url': cover_url,
        })
    
    return result


def _generate_ai_reason(scores: dict[str, int], tags: list[str],
                        recommendations: list[dict]) -> str:
    """调用 LLM 生成推荐理由。"""
    song_list = '、'.join(s['title'] for s in recommendations)
    tag_str = '、'.join(tags)

    prompt = (
        f'用户完成了大五人格测试，画像标签为：{tag_str}。'
        f'五维得分：开放性{scores["O"]}、责任心{scores["C"]}、'
        f'外向性{scores["E"]}、宜人性{scores["A"]}、神经质{scores["N"]}。'
        f'为其推荐了以下中国传统音乐：{song_list}。'
        f'请用2-3句话说明推荐理由，语气亲切自然，突出人格特点与音乐风格的契合。'
    )

    try:
        import requests
        cfg = svc_config.LLM
        resp = requests.post(
            f'{cfg["BASE_URL"]}/chat/completions',
            headers={
                'Authorization': f'Bearer {cfg["API_KEY"]}',
                'Content-Type': 'application/json',
            },
            json={
                'model': cfg['MODEL'],
                'messages': [
                    {'role': 'system', 'content': '你是一位中国传统音乐推荐顾问，语言简洁优雅。'},
                    {'role': 'user', 'content': prompt},
                ],
                'max_tokens': 200,
            },
            timeout=cfg.get('TIMEOUT_SECONDS', 30),
        )
        resp.raise_for_status()
        data = resp.json()
        return data['choices'][0]['message']['content'].strip()
    except Exception:
        # LLM 调用失败时返回规则版理由
        return _build_fallback_reason(scores, tags, recommendations)


def _build_fallback_reason(scores: dict[str, int], tags: list[str],
                           recommendations: list[dict]) -> str:
    """LLM 不可用时的规则版推荐理由。"""
    if not recommendations:
        return '根据你的画像，为你推荐相关中国传统音乐。'
    first = recommendations[0]
    o = scores['O']
    if o > 70:
        return (
            f'你具有较高的开放性，喜欢探索不同文化，'
            f'《{first["title"]}》的{first["genre"]}音色更符合你的审美偏好。'
        )
    if scores['N'] > 70:
        return (
            f'你对音乐情绪敏感，'
            f'《{first["title"]}》的宁静旋律能带来心灵的平静与慰藉。'
        )
    return f'根据你的画像特征，为你推荐《{first["title"]}》。'


# ========================= 获取画像 =========================

def get_profile(user_id: str) -> dict[str, Any]:
    """获取用户的人格画像（从 behave.PersonalityTests 读取最新记录）。"""
    with connection.cursor() as cur:
        cur.execute(
            "SELECT TOP 1 personality_type, result_detail, test_date "
            "FROM behave.PersonalityTests WHERE user_id = %s "
            "ORDER BY test_date DESC",
            [user_id],
        )
        row = cur.fetchone()

    if not row:
        return {'has_profile': False, 'message': '尚未完成人格测试'}

    # 查用户名
    with connection.cursor() as cur:
        cur.execute("SELECT username FROM behave.Users WHERE user_id = %s", [user_id])
        user_row = cur.fetchone()
    username = user_row[0] if user_row else ''

    result = json.loads(row[1]) if row[1] else {}
    
    recommendations = result.get('recommendations', [])
    for song in recommendations:
        audio_url = song.get('audio_url', '')
        if audio_url and not audio_url.startswith('http') and not audio_url.startswith('/media/'):
            if audio_url.startswith('audio/'):
                parts = audio_url.split('/')
                if len(parts) >= 2:
                    encoded_parts = [urllib.parse.quote(p) for p in parts[1:] if p]
                    song['audio_url'] = f'/media/audio/{"/".join(encoded_parts)}'
        
        cover_url = song.get('cover_url', '')
        if cover_url and not cover_url.startswith('http') and not cover_url.startswith('/media/'):
            if cover_url.startswith('images/'):
                parts = cover_url.split('/')
                if len(parts) >= 2:
                    encoded_parts = [urllib.parse.quote(p) for p in parts[1:] if p]
                    song['cover_url'] = f'/media/images/{"/".join(encoded_parts)}'
    
    result['has_profile'] = True
    result['user_id'] = user_id
    result['username'] = username
    result['personality_type'] = row[0]
    result['update_time'] = str(row[2]) if row[2] else ''
    return result


# ========================= 猜你喜欢 =========================

def recommend_songs(user_id: str) -> dict[str, Any]:
    """猜你喜欢：基于人格画像推荐音乐。"""
    profile = get_profile(user_id)

    if not profile.get('has_profile'):
        # 没有人格画像，返回默认推荐
        with connection.cursor() as cur:
            cur.execute(
                "SELECT TOP 6 id, title, genre, audio_url, cover_url "
                "FROM traditional_song WHERE audio_url IS NOT NULL AND audio_url != '' "
                "ORDER BY id"
            )
            rows = cur.fetchall()
        songs = [
            {'id': r[0], 'title': r[1], 'genre': r[2], 'audio_url': r[3], 'cover_url': r[4]}
            for r in rows
        ]
        return {
            'user_id': user_id,
            'songs': songs,
            'used_personality': False,
            'message': '完成人格测试后可获得更精准的推荐',
        }

    # 有人格画像，基于维度得分推荐
    scores = profile.get('scores', {})
    dim_scores = {'O': scores.get('openness', 0), 'C': scores.get('conscientiousness', 0),
                  'E': scores.get('extraversion', 0), 'A': scores.get('agreeableness', 0),
                  'N': scores.get('neuroticism', 0)}
    recommendations = _recommend_songs(dim_scores)
    return {
        'user_id': user_id,
        'songs': recommendations,
        'used_personality': True,
        'personality_tags': profile.get('tags', []),
        'message': '基于你的人格画像推荐',
    }


# ========================= 听歌记录 =========================

def record_listen(user_id: str, song: dict[str, Any]) -> dict[str, Any]:
    """用户听歌时记录行为（写入 behave.PlayRecords）。"""
    song_id = str(song.get('song_id') or song.get('id') or '').strip()
    if not song_id:
        return {'success': False, 'message': 'song_id 不能为空'}

    canonical_user_id = str(user_id).strip()
    with connection.cursor() as cur:
        # 页面历史上有的传 username、有的传 user_id，统一保存数据库用户 ID。
        cur.execute(
            "SELECT TOP 1 user_id FROM behave.Users WHERE user_id = %s OR username = %s",
            [canonical_user_id, canonical_user_id],
        )
        user_row = cur.fetchone()
        if user_row:
            canonical_user_id = str(user_row[0])
        cur.execute(
            "INSERT INTO behave.PlayRecords (user_id, song_id, play_time) "
            "VALUES (%s, %s, GETDATE())",
            [canonical_user_id, song_id],
        )
    return {'success': True, 'message': '听歌记录已保存'}


# ========================= AI 生成国风音乐 =========================

def generate_guofeng_music(user_id: str, form: dict[str, Any]) -> dict[str, Any]:
    """
    AI 生成国风音乐：调用 Apiframe Suno API。
    流程：POST /v2/music/generate 提交任务 → 轮询 GET /v2/jobs/:id 直至 COMPLETED。
    """
    import time
    import requests

    cfg = svc_config.MUSIC_GENERATION_AI
    base_url = cfg['BASE_URL'].rstrip('/')
    api_key = cfg.get('API_KEY', '')
    if not api_key:
        return {
            'user_id': user_id,
            'form': form,
            'audio_url': '',
            'title': form.get('title') or '未命名国风作品',
            'message': 'AI 音乐生成 API Key 未配置',
        }

    mood = (form.get('mood') or '').strip()
    style = (form.get('style') or '古风').strip()
    user_prompt = (form.get('prompt') or '').strip()
    title = (form.get('title') or '国风作品').strip()[:80]

    desc_parts = []
    if user_prompt:
        desc_parts.append(user_prompt)
    if style:
        desc_parts.append(f'风格：{style}')
    if mood:
        desc_parts.append(f'情绪：{mood}')
    desc_parts.append('中国传统音乐元素，国风韵味')
    prompt = '，'.join(desc_parts)[:500]

    headers = {
        'X-API-Key': api_key,
        'Content-Type': 'application/json',
    }

    submit_payload = {
        'prompt': prompt,
        'model': 'suno',
        'sunoParams': {
            'custom_mode': False,
            'instrumental': True,  # 国风器乐，无人声
            'model_version': 'V4_5PLUS',
            'style': f'{style}, traditional chinese, guofeng',
            'title': title,
        },
    }
    try:
        submit_resp = requests.post(
            f'{base_url}/v2/music/generate',
            headers=headers,
            json=submit_payload,
            timeout=30,
        )
        submit_resp.raise_for_status()
        job_data = submit_resp.json()
    except requests.RequestException as e:
        return {
            'user_id': user_id,
            'form': form,
            'audio_url': '',
            'title': title,
            'message': f'提交生成任务失败：{e}',
        }

    job_id = job_data.get('jobId')
    if not job_id:
        return {
            'user_id': user_id,
            'form': form,
            'audio_url': '',
            'title': title,
            'message': f'未获取到任务 ID：{job_data}',
        }

    # 2. 轮询任务状态（每 8 秒查询一次，最长等待 4 分钟）
    max_wait = cfg.get('TIMEOUT_SECONDS', 300)
    poll_interval = 8
    deadline = time.time() + max_wait
    last_status = 'QUEUED'

    while time.time() < deadline:
        try:
            poll_resp = requests.get(
                f'{base_url}/v2/jobs/{job_id}',
                headers=headers,
                timeout=15,
            )
            poll_resp.raise_for_status()
            job = poll_resp.json()
        except requests.RequestException:
            time.sleep(poll_interval)
            continue

        last_status = job.get('status', 'UNKNOWN')
        if last_status == 'COMPLETED':
            tracks = (job.get('result') or {}).get('tracks') or []
            if not tracks:
                return {
                    'user_id': user_id,
                    'form': form,
                    'audio_url': '',
                    'title': title,
                    'message': '任务完成但未返回音频',
                }
            track = tracks[0]
            return {
                'user_id': user_id,
                'form': form,
                'audio_url': track.get('audioUrl', ''),
                'cover_url': track.get('imageUrl', ''),
                'title': track.get('title') or title,
                'duration': track.get('duration'),
                'tags': track.get('tags', ''),
                'job_id': job_id,
                'message': f'生成成功：{track.get("title") or title}',
            }
        if last_status == 'FAILED':
            err = job.get('error') or '生成失败'
            return {
                'user_id': user_id,
                'form': form,
                'audio_url': '',
                'title': title,
                'message': f'生成失败：{err}',
            }
        time.sleep(poll_interval)

    return {
        'user_id': user_id,
        'form': form,
        'audio_url': '',
        'title': title,
        'job_id': job_id,
        'message': f'生成超时（{last_status}），可稍后用 job_id 查询',
    }

    if vocal_gender in ('m', 'f'):
        suno_params['vocal_gender'] = vocal_gender

    payload = {
        'prompt': prompt,
        'model': 'suno',
        'sunoParams': suno_params,
    }

    try:
        response = requests.post(f"{base_url}/v2/music/generate", headers=headers, json=payload, timeout=timeout)
        result = response.json()

        if 'jobId' in result:
            task_id = result['jobId']
            return {
                'source': 'apiframe_suno',
                'user_id': user_id,
                'form': form,
                'audio_url': '',
                'title': title,
                'message': '音乐生成任务已提交，请等待生成完成',
                'success': True,
                'task_id': task_id,
                'status': 'pending',
            }

        if result.get('code') == 401:
            return {
                'source': 'apiframe_suno',
                'user_id': user_id,
                'form': form,
                'audio_url': '',
                'title': title,
                'message': 'API Key 无效，请检查配置',
                'success': False,
            }

        if result.get('code') == 400:
            return {
                'source': 'apiframe_suno',
                'user_id': user_id,
                'form': form,
                'audio_url': '',
                'title': title,
                'message': f'参数错误: {result.get("message", "未知错误")}',
                'success': False,
            }

        return {
            'source': 'apiframe_suno',
            'user_id': user_id,
            'form': form,
            'audio_url': '',
            'title': title,
            'message': f'API 返回数据异常: {result}',
            'success': False,
        }

    except requests.exceptions.RequestException as e:
        return {
            'source': 'ai_music_generate_error',
            'user_id': user_id,
            'form': form,
            'audio_url': '',
            'title': title,
            'message': f'调用 Apiframe Suno API 失败: {str(e)}',
            'success': False,
        }


def generate_lyrics_by_doubao(style: str, mood: str, theme: str = '', keywords: str = '') -> dict[str, Any]:
    """
    调用豆包 AI 生成国风歌词。
    
    参数：
    - style: 音乐风格（古风/民乐/戏曲风/融合流行）
    - mood: 情绪（宁静/激昂/欢快/忧伤等）
    - theme: 主题（可选，如：山水、江湖、爱情、思乡等）
    - keywords: 关键词（可选，用逗号分隔）
    """
    llm_config = svc_config.LLM
    base_url = llm_config.get('BASE_URL', '')
    api_key = llm_config.get('API_KEY', '')
    model = llm_config.get('MODEL', '')
    timeout = llm_config.get('TIMEOUT_SECONDS', 60)

    if not api_key or not base_url:
        return {
            'success': False,
            'message': '豆包 API 配置未完成',
            'lyrics': '',
        }

    prompt = f"""你是一个专业的国风歌词创作助手。请根据以下信息创作一首优美的国风歌词：

风格：{style}
情绪：{mood}
主题：{theme if theme else '自由创作'}
关键词：{keywords if keywords else '无'}

要求：
1. 歌词要有完整的结构，包含 [Verse 1]、[Chorus]、[Verse 2] 等部分
2. 语言优美，富有诗意，符合国风韵味
3. 押韵自然，朗朗上口
4. 字数适中，适合演唱
5. 只返回歌词内容，不要包含解释或说明
"""

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}',
    }

    payload = {
        'model': model,
        'messages': [
            {
                'role': 'system',
                'content': '你是一个专业的国风歌词创作助手，擅长创作古风、民乐、戏曲风格的歌词。',
            },
            {
                'role': 'user',
                'content': prompt,
            },
        ],
        'temperature': 0.7,
        'max_tokens': 2000,
    }

    try:
        response = requests.post(f"{base_url}/chat/completions", headers=headers, json=payload, timeout=timeout)
        result = response.json()

        if response.status_code != 200:
            return {
                'success': False,
                'message': f'豆包 API 调用失败: {result.get("error", {}).get("message", "未知错误")}',
                'lyrics': '',
            }

        if 'choices' in result and result['choices']:
            lyrics = result['choices'][0]['message']['content'].strip()
            return {
                'success': True,
                'message': '歌词生成成功',
                'lyrics': lyrics,
            }

        return {
            'success': False,
            'message': '豆包 API 返回数据异常',
            'lyrics': '',
        }

    except requests.exceptions.RequestException as e:
        return {
            'success': False,
            'message': f'调用豆包 API 失败: {str(e)}',
            'lyrics': '',
        }


def fetch_music_task(task_id: str) -> dict[str, Any]:
    """
    查询音乐生成任务状态：调用 Apiframe Suno API 查询任务结果。
    """
    config = svc_config.MUSIC_GENERATION_AI
    base_url = config.get('BASE_URL', 'https://api.apiframe.ai')
    api_key = config.get('API_KEY', '')
    timeout = config.get('TIMEOUT_SECONDS', 300)

    if not api_key:
        return {
            'success': False,
            'message': 'API Key 未配置',
        }

    headers = {
        'X-API-Key': api_key,
        'Content-Type': 'application/json',
    }

    try:
        response = requests.get(f"{base_url}/v2/jobs/{task_id}", headers=headers, timeout=timeout)
        result = response.json()

        status = result.get('status')

        if status == 'COMPLETED' and 'result' in result:
            result_data = result['result']
            audio_url = None
            title = None

            if isinstance(result_data, dict) and 'tracks' in result_data:
                tracks = result_data['tracks']
                if tracks and isinstance(tracks, list):
                    first_track = tracks[0]
                    audio_url = first_track.get('audioUrl')
                    title = first_track.get('title')

            if audio_url:
                return {
                    'success': True,
                    'message': '音乐生成完成',
                    'audio_url': audio_url,
                    'status': 'complete',
                    'title': title or '未命名作品',
                    'suno_data': result,
                }
            else:
                return {
                    'success': False,
                    'message': '任务已完成但未获取到音频链接',
                    'status': 'complete',
                    'raw_data': result,
                }

        elif status == 'FAILED':
            error_msg = result.get('error', {}).get('message', '生成失败')
            return {
                'success': False,
                'message': f'生成失败：{error_msg}',
                'status': 'failed',
            }

        elif status in ('PENDING', 'PROCESSING', 'STARTED'):
            progress = result.get('progress', 0)
            return {
                'success': False,
                'message': f'生成中: {progress}%',
                'status': 'processing',
                'progress': progress,
            }

        else:
            return {
                'success': False,
                'message': f'任务状态: {status}',
                'status': 'unknown',
                'raw_data': result,
            }

    except requests.exceptions.RequestException as e:
        return {
            'success': False,
            'message': f'查询任务状态失败: {str(e)}',
        }


# ========================= 文化圈层测试 =========================

def save_cultural_circle_test(user_id: str, answers: dict[int, int], user_vector: list[int],
                               matched_circles: list[dict]) -> dict[str, Any]:
    """
    保存文化圈层测试结果到数据库。
    
    参数：
    - user_id: 用户ID
    - answers: 用户答题记录 {question_id: score}
    - user_vector: 七维得分向量 [F1, F2, F3, F4, F5, F6, F7]
    - matched_circles: 匹配的文化圈层列表
    """
    from .models import CulturalCircleTest
    
    try:
        test = CulturalCircleTest(
            user_id=user_id,
            f1_score=user_vector[0] if len(user_vector) > 0 else 0,
            f2_score=user_vector[1] if len(user_vector) > 1 else 0,
            f3_score=user_vector[2] if len(user_vector) > 2 else 0,
            f4_score=user_vector[3] if len(user_vector) > 3 else 0,
            f5_score=user_vector[4] if len(user_vector) > 4 else 0,
            f6_score=user_vector[5] if len(user_vector) > 5 else 0,
            f7_score=user_vector[6] if len(user_vector) > 6 else 0,
            matched_circles=matched_circles,
            answers=answers,
        )
        test.save()
        return {
            'success': True,
            'message': '测试结果已保存',
            'test_id': test.id,
        }
    except Exception as e:
        return {
            'success': False,
            'message': f'保存失败：{str(e)}',
        }


def get_cultural_circle_test(user_id: str) -> dict[str, Any]:
    """
    获取用户最新的文化圈层测试结果。
    
    返回：
    - has_test: 是否有测试记录
    - user_vector: 七维得分向量
    - matched_circles: 匹配的文化圈层列表
    - test_date: 测试时间
    """
    from .models import CulturalCircleTest
    
    try:
        test = CulturalCircleTest.objects.filter(user_id=user_id).order_by('-test_date').first()
        if not test:
            return {'has_test': False, 'message': '尚未完成文化圈层测试'}
        
        return {
            'has_test': True,
            'user_vector': [
                test.f1_score,
                test.f2_score,
                test.f3_score,
                test.f4_score,
                test.f5_score,
                test.f6_score,
                test.f7_score,
            ],
            'matched_circles': test.matched_circles,
            'answers': test.answers,
            'test_date': str(test.test_date),
            'test_id': test.id,
        }
    except Exception as e:
        return {
            'has_test': False,
            'message': f'查询失败：{str(e)}',
        }


# ========================= 歌曲喜欢/不喜欢 =========================

def toggle_song_like(user_id: str, song_id: str, reaction_type: str) -> dict[str, Any]:
    """
    切换歌曲喜欢/不喜欢状态。
    
    参数：
    - user_id: 用户ID
    - song_id: 歌曲ID
    - reaction_type: 'like' 或 'dislike'
    
    返回：
    - success: 是否成功
    - message: 提示信息
    """
    from .models import SongLike
    
    try:
        existing = SongLike.objects.filter(user_id=user_id, song_id=song_id).first()
        
        if existing:
            if existing.reaction_type == reaction_type:
                existing.delete()
                return {
                    'success': True,
                    'message': f'已取消{reaction_type}',
                    'liked': False,
                }
            else:
                existing.reaction_type = reaction_type
                existing.save()
                return {
                    'success': True,
                    'message': f'已{reaction_type}',
                    'liked': reaction_type == 'like',
                }
        else:
            SongLike.objects.create(user_id=user_id, song_id=song_id, reaction_type=reaction_type)
            return {
                'success': True,
                'message': f'已{reaction_type}',
                'liked': reaction_type == 'like',
            }
    except Exception as e:
        return {
            'success': False,
            'message': f'操作失败：{str(e)}',
        }


def get_song_like_status(user_id: str, song_id: str) -> dict[str, Any]:
    """
    获取歌曲的喜欢状态。
    
    返回：
    - liked: 是否喜欢
    - disliked: 是否不喜欢
    """
    from .models import SongLike
    
    try:
        record = SongLike.objects.filter(user_id=user_id, song_id=song_id).first()
        if not record:
            return {'liked': False, 'disliked': False}
        return {'liked': record.reaction_type == 'like', 'disliked': record.reaction_type == 'dislike'}
    except Exception as e:
        return {'liked': False, 'disliked': False}


def get_user_liked_songs(user_id: str) -> dict[str, Any]:
    """
    获取用户喜欢的歌曲列表。
    
    返回：
    - success: 是否成功
    - data: {songs}
    """
    from .models import SongLike
    
    try:
        liked_records = SongLike.objects.filter(user_id=user_id, reaction_type='like').order_by('-created_at')
        song_ids = [str(r.song_id) for r in liked_records]
        
        if not song_ids:
            return {'success': True, 'data': {'songs': []}}
        
        int_song_ids = []
        non_int_song_ids = []
        
        for sid in song_ids:
            try:
                int_song_ids.append(int(sid))
            except (ValueError, TypeError):
                non_int_song_ids.append(sid)
        
        songs = []
        
        if int_song_ids:
            placeholders = ','.join(['%s'] * len(int_song_ids))
            query = (
                f"SELECT id, title, audio_url, cover_url "
                f"FROM traditional_song WHERE id IN ({placeholders}) "
                f"ORDER BY id"
            )
            with connection.cursor() as cur:
                cur.execute(query, int_song_ids)
                rows = cur.fetchall()
            
            for r in rows:
                audio_url = r[2] if r[2] else ''
                cover_url = r[3] if r[3] else ''
                
                if audio_url and not audio_url.startswith('http'):
                    if audio_url.startswith('audio/'):
                        parts = audio_url.split('/')
                        if len(parts) >= 2:
                            encoded_parts = [urllib.parse.quote(p) for p in parts[1:] if p]
                            audio_url = f'/media/audio/{"/".join(encoded_parts)}'
                
                if cover_url and not cover_url.startswith('http'):
                    if '大创' in cover_url:
                        relative_path = cover_url.split('大创/', 1)[-1]
                    else:
                        relative_path = cover_url
                    cover_url = f'/media/{relative_path}'
                
                songs.append({
                    'id': str(r[0]),
                    'title': r[1] if r[1] else '',
                    'intro': '',
                    'mv_url': '',
                    'audio_url': audio_url,
                    'cover_url': cover_url,
                })
        
        for sid in non_int_song_ids:
            try:
                from data_display.services import query_music_resource
                resource = query_music_resource(sid)
                cover_url = resource.get('cover_url', '')
                if cover_url and not cover_url.startswith('http') and not cover_url.startswith('/media/'):
                    if '大创' in cover_url:
                        relative_path = cover_url.split('大创/', 1)[-1]
                        cover_url = f'/media/{relative_path}'
                    else:
                        cover_url = f'/media/{cover_url}'
                songs.append({
                    'id': sid,
                    'title': resource.get('title', sid),
                    'intro': resource.get('intro', ''),
                    'mv_url': resource.get('mv_url', ''),
                    'audio_url': resource.get('audio_url', ''),
                    'cover_url': cover_url,
                })
            except Exception:
                songs.append({
                    'id': sid,
                    'title': sid,
                    'intro': '',
                    'mv_url': '',
                    'audio_url': '',
                    'cover_url': '',
                })
        
        return {'success': True, 'data': {'songs': songs}}
    except Exception as e:
        return {'success': False, 'message': f'查询失败：{str(e)}'}


# ========================= 收藏夹功能 =========================

def get_favorite_folders(username: str) -> dict[str, Any]:
    """
    获取用户收藏夹列表。
    
    返回：
    - success: 是否成功
    - data: {folders}
    """
    from .models import FavoriteFolder, FavoriteSong
    
    try:
        folders = FavoriteFolder.objects.filter(user_id=username).order_by('created_at')
        
        if not folders.exists():
            default_folder = FavoriteFolder.objects.create(
                user_id=username,
                name='默认收藏夹',
                icon_url='',
            )
            return {
                'success': True,
                'data': {
                    'username': username,
                    'folders': [{
                        'id': str(default_folder.id),
                        'name': default_folder.name,
                        'icon_url': default_folder.icon_url,
                        'song_count': 0,
                    }],
                },
            }
        
        result = []
        for folder in folders:
            song_count = FavoriteSong.objects.filter(folder=folder).count()
            result.append({
                'id': str(folder.id),
                'name': folder.name,
                'icon_url': folder.icon_url,
                'song_count': song_count,
            })
        
        return {
            'success': True,
            'data': {
                'username': username,
                'folders': result,
            },
        }
    except Exception as e:
        return {
            'success': False,
            'message': f'查询失败：{str(e)}',
        }


def get_folder_songs(username: str, folder_id: str) -> dict[str, Any]:
    """
    获取收藏夹中的歌曲列表。
    
    参数：
    - username: 用户ID
    - folder_id: 收藏夹ID
    
    返回：
    - success: 是否成功
    - data: {folder_id, folder_name, songs}
    """
    from .models import FavoriteFolder, FavoriteSong
    
    try:
        folder = FavoriteFolder.objects.filter(id=folder_id, user_id=username).first()
        if not folder:
            return {'success': False, 'message': '收藏夹不存在'}
        
        songs = FavoriteSong.objects.filter(folder=folder).order_by('-added_at')
        
        song_list = []
        for song in songs:
            song_list.append({
                'id': song.song_id,
                'title': song.title,
                'intro': song.intro,
                'mv_url': song.mv_url,
                'audio_url': getattr(song, 'audio_url', ''),
                'cover_url': getattr(song, 'cover_url', ''),
            })
        
        return {
            'success': True,
            'data': {
                'folder_id': str(folder.id),
                'folder_name': folder.name,
                'songs': song_list,
            },
        }
    except Exception as e:
        return {'success': False, 'message': f'查询失败：{str(e)}'}


def create_favorite_folder(username: str, name: str) -> dict[str, Any]:
    """
    创建新的收藏夹。
    
    参数：
    - username: 用户ID
    - name: 收藏夹名称
    
    返回：
    - success: 是否成功
    - data: {folder}
    """
    from .models import FavoriteFolder
    
    try:
        folder = FavoriteFolder.objects.create(
            user_id=username,
            name=name,
            icon_url='',
        )
        
        return {
            'success': True,
            'data': {
                'folder': {
                    'id': str(folder.id),
                    'name': folder.name,
                    'icon_url': folder.icon_url,
                    'song_count': 0,
                },
            },
        }
    except Exception as e:
        return {'success': False, 'message': f'创建失败：{str(e)}'}


def delete_favorite_folder(username: str, folder_id: str) -> dict[str, Any]:
    """
    删除收藏夹。
    
    参数：
    - username: 用户ID
    - folder_id: 收藏夹ID
    
    返回：
    - success: 是否成功
    - message: 提示信息
    """
    from .models import FavoriteFolder
    
    try:
        folder = FavoriteFolder.objects.filter(id=folder_id, user_id=username).first()
        if not folder:
            return {'success': False, 'message': '收藏夹不存在'}
        
        if folder.name == '默认收藏夹':
            return {'success': False, 'message': '默认收藏夹不能删除'}
        
        folder.delete()
        return {
            'success': True,
            'message': '收藏夹已删除',
            'data': {'folder_id': folder_id},
        }
    except Exception as e:
        return {'success': False, 'message': f'删除失败：{str(e)}'}


def save_to_favorite(username: str, song_id: str, folder_id: str) -> dict[str, Any]:
    """
    将歌曲保存到指定收藏夹。
    
    参数：
    - username: 用户ID
    - song_id: 歌曲ID
    - folder_id: 收藏夹ID
    
    返回：
    - success: 是否成功
    - data: {folder_id, song_id}
    """
    from .models import FavoriteFolder, FavoriteSong
    
    try:
        folder = FavoriteFolder.objects.filter(id=folder_id, user_id=username).first()
        if not folder:
            return {'success': False, 'message': '收藏夹不存在'}
        
        existing = FavoriteSong.objects.filter(folder=folder, song_id=song_id).first()
        if existing:
            return {'success': True, 'data': {'folder_id': str(folder.id), 'song_id': song_id}, 'message': '歌曲已在收藏夹中'}
        
        title = song_id
        intro = ''
        mv_url = ''
        audio_url = ''
        cover_url = ''
        
        try:
            song_int_id = int(song_id)
            query = f"SELECT title, audio_url, cover_url FROM traditional_song WHERE id = %s"
            with connection.cursor() as cur:
                cur.execute(query, [song_int_id])
                row = cur.fetchone()
                if row:
                    title = row[0] if row[0] else song_id
                    audio_url = row[1] if row[1] else ''
                    cover_url = row[2] if row[2] else ''
        except (ValueError, TypeError):
            try:
                from data_display.services import query_music_resource
                resource = query_music_resource(song_id)
                if resource.get('title'):
                    title = resource['title']
                intro = resource.get('intro', '')
                mv_url = resource.get('mv_url', '')
                audio_url = resource.get('audio_url', '')
                cover_url = resource.get('cover_url', '')
            except Exception:
                pass
        
        if audio_url and not audio_url.startswith('http'):
            if audio_url.startswith('audio/'):
                parts = audio_url.split('/')
                if len(parts) >= 2:
                    encoded_parts = [urllib.parse.quote(p) for p in parts[1:] if p]
                    audio_url = f'/media/audio/{"/".join(encoded_parts)}'
        
        if cover_url and not cover_url.startswith('http'):
            if cover_url.startswith('/media/'):
                pass
            elif '大创' in cover_url:
                relative_path = cover_url.split('大创/', 1)[-1]
                cover_url = f'/media/{relative_path}'
            else:
                cover_url = f'/media/{cover_url}'
        
        FavoriteSong.objects.create(
            folder=folder,
            song_id=song_id,
            title=title,
            intro=intro,
            mv_url=mv_url,
            audio_url=audio_url,
            cover_url=cover_url,
        )
        
        return {
            'success': True,
            'data': {'folder_id': str(folder.id), 'song_id': song_id},
        }
    except Exception as e:
        return {'success': False, 'message': f'收藏失败：{str(e)}'}


def delete_favorite_song(username: str, folder_id: str, song_id: str) -> dict[str, Any]:
    """
    从收藏夹中删除歌曲。
    
    参数：
    - username: 用户ID
    - folder_id: 收藏夹ID
    - song_id: 歌曲ID
    
    返回：
    - success: 是否成功
    - data: {folder_id, song_id}
    """
    from .models import FavoriteFolder, FavoriteSong
    
    try:
        folder = FavoriteFolder.objects.filter(id=folder_id, user_id=username).first()
        if not folder:
            return {'success': False, 'message': '收藏夹不存在'}
        
        song = FavoriteSong.objects.filter(folder=folder, song_id=song_id).first()
        if not song:
            return {'success': False, 'message': '歌曲不在收藏夹中'}
        
        song.delete()
        return {
            'success': True,
            'data': {'folder_id': str(folder.id), 'song_id': song_id},
        }
    except Exception as e:
        return {'success': False, 'message': f'删除失败：{str(e)}'}


def get_favorite_status(username: str, song_id: str) -> dict[str, Any]:
    """
    检查歌曲是否已被用户收藏。
    
    参数：
    - username: 用户ID
    - song_id: 歌曲ID
    
    返回：
    - success: 是否成功
    - data: {favorited, folder_id}
    """
    from .models import FavoriteFolder, FavoriteSong
    
    try:
        folders = FavoriteFolder.objects.filter(user_id=username)
        for folder in folders:
            song = FavoriteSong.objects.filter(folder=folder, song_id=song_id).first()
            if song:
                return {'success': True, 'data': {'favorited': True, 'folder_id': str(folder.id)}}
        
        return {'success': True, 'data': {'favorited': False}}
    except Exception as e:
        return {'success': False, 'message': f'查询失败：{str(e)}'}


def calculate_cultural_circle_vector(answers: dict) -> list[int]:
    """
    根据用户答案计算七维得分向量（0-100分）。
    
    每道题1-5分，每个维度5题，原始分5-25分，归一化到0-100。
    """
    raw_scores = {'F1': 0, 'F2': 0, 'F3': 0, 'F4': 0, 'F5': 0, 'F6': 0, 'F7': 0}
    
    DIMENSION_MAP = {
        1: 'F1', 2: 'F1', 3: 'F1', 4: 'F1', 5: 'F1',
        6: 'F2', 7: 'F2', 8: 'F2', 9: 'F2', 10: 'F2',
        11: 'F3', 12: 'F3', 13: 'F3', 14: 'F3', 15: 'F3',
        16: 'F4', 17: 'F4', 18: 'F4', 19: 'F4', 20: 'F4',
        21: 'F5', 22: 'F5', 23: 'F5', 24: 'F5', 25: 'F5',
        26: 'F6', 27: 'F6', 28: 'F6', 29: 'F6', 30: 'F6',
        31: 'F7', 32: 'F7', 33: 'F7', 34: 'F7', 35: 'F7',
    }
    
    for q_id, score in answers.items():
        try:
            q_id_int = int(q_id)
            dim = DIMENSION_MAP.get(q_id_int)
            if dim:
                raw_scores[dim] += int(score)
        except (ValueError, TypeError):
            pass
    
    vector = []
    for i in range(1, 8):
        dim = f'F{i}'
        raw = raw_scores[dim]
        vector.append(max(0, min(100, round(((raw - 5) / 20) * 100))))
    
    return vector


def cosine_similarity(vec1: list[int], vec2: list[int]) -> float:
    """计算余弦相似度。"""
    dot_product = 0
    norm1 = 0
    norm2 = 0
    len_min = min(len(vec1), len(vec2))
    for i in range(len_min):
        v1 = vec1[i] if i < len(vec1) else 0
        v2 = vec2[i] if i < len(vec2) else 0
        dot_product += v1 * v2
        norm1 += v1 * v1
        norm2 += v2 * v2
    denom = (norm1 ** 0.5) * (norm2 ** 0.5)
    return dot_product / denom if denom > 0 else 0


CULTURAL_CIRCLES = [
    {'name': '东亚文化圈', 'factors': [0.6, 0.7, 0.65, 0.75, 0.6, 0.65, 0.7]},
    {'name': '中华文化圈', 'factors': [0.55, 0.75, 0.7, 0.8, 0.7, 0.65, 0.75]},
    {'name': '日本文化圈', 'factors': [0.5, 0.65, 0.6, 0.7, 0.65, 0.7, 0.75]},
    {'name': '朝鲜半岛文化圈', 'factors': [0.55, 0.6, 0.65, 0.65, 0.6, 0.6, 0.7]},
    {'name': '兰纳泰北文化圈', 'factors': [0.45, 0.7, 0.5, 0.55, 0.5, 0.5, 0.6]},
    {'name': '印度教文化圈', 'factors': [0.85, 0.6, 0.55, 0.6, 0.7, 0.5, 0.75]},
    {'name': '佛教文化圈', 'factors': [0.7, 0.55, 0.5, 0.55, 0.6, 0.55, 0.7]},
    {'name': '伊斯兰教文化圈', 'factors': [0.8, 0.6, 0.65, 0.6, 0.65, 0.55, 0.65]},
    {'name': '基督教文化圈', 'factors': [0.75, 0.65, 0.7, 0.65, 0.7, 0.65, 0.7]},
    {'name': '儒家文化圈', 'factors': [0.4, 0.65, 0.75, 0.7, 0.75, 0.65, 0.6]},
    {'name': '游牧文化圈', 'factors': [0.35, 0.8, 0.4, 0.5, 0.55, 0.4, 0.55]},
    {'name': '农耕文化圈', 'factors': [0.3, 0.7, 0.6, 0.65, 0.65, 0.55, 0.6]},
    {'name': '海洋文化圈', 'factors': [0.35, 0.65, 0.55, 0.6, 0.5, 0.6, 0.65]},
    {'name': '草原文化圈', 'factors': [0.4, 0.75, 0.45, 0.55, 0.5, 0.45, 0.5]},
    {'name': '高原文化圈', 'factors': [0.5, 0.7, 0.4, 0.5, 0.55, 0.4, 0.55]},
    {'name': '热带雨林文化圈', 'factors': [0.6, 0.8, 0.45, 0.5, 0.45, 0.45, 0.55]},
    {'name': '沙漠文化圈', 'factors': [0.7, 0.65, 0.55, 0.55, 0.6, 0.45, 0.5]},
    {'name': '地中海文化圈', 'factors': [0.65, 0.6, 0.65, 0.65, 0.75, 0.6, 0.7]},
    {'name': '西欧文化圈', 'factors': [0.6, 0.6, 0.7, 0.65, 0.7, 0.7, 0.75]},
    {'name': '北欧文化圈', 'factors': [0.5, 0.55, 0.75, 0.6, 0.65, 0.75, 0.7]},
    {'name': '东欧文化圈', 'factors': [0.55, 0.6, 0.6, 0.6, 0.65, 0.6, 0.65]},
    {'name': '拉美文化圈', 'factors': [0.7, 0.7, 0.55, 0.55, 0.55, 0.55, 0.65]},
    {'name': '非洲文化圈', 'factors': [0.65, 0.75, 0.45, 0.5, 0.5, 0.45, 0.6]},
    {'name': '北美文化圈', 'factors': [0.55, 0.6, 0.7, 0.6, 0.55, 0.7, 0.7]},
    {'name': '大洋洲文化圈', 'factors': [0.45, 0.7, 0.65, 0.5, 0.45, 0.65, 0.65]},
    {'name': '东南亚文化圈', 'factors': [0.6, 0.75, 0.5, 0.55, 0.5, 0.5, 0.6]},
    {'name': '西亚文化圈', 'factors': [0.75, 0.6, 0.6, 0.65, 0.65, 0.5, 0.6]},
    {'name': '南亚文化圈', 'factors': [0.7, 0.7, 0.5, 0.65, 0.6, 0.5, 0.65]},
    {'name': '中亚文化圈', 'factors': [0.6, 0.7, 0.5, 0.6, 0.6, 0.45, 0.55]},
    {'name': '西伯利亚文化圈', 'factors': [0.3, 0.75, 0.4, 0.45, 0.5, 0.4, 0.45]},
    {'name': '印第安文化圈', 'factors': [0.55, 0.75, 0.4, 0.5, 0.55, 0.45, 0.5]},
    {'name': '玛雅文化圈', 'factors': [0.6, 0.7, 0.5, 0.5, 0.6, 0.5, 0.6]},
    {'name': '阿兹特克文化圈', 'factors': [0.65, 0.7, 0.55, 0.55, 0.55, 0.5, 0.55]},
    {'name': '印加文化圈', 'factors': [0.6, 0.75, 0.5, 0.5, 0.55, 0.45, 0.55]},
    {'name': '美索不达米亚文化圈', 'factors': [0.75, 0.65, 0.6, 0.65, 0.75, 0.55, 0.6]},
    {'name': '古埃及文化圈', 'factors': [0.7, 0.7, 0.65, 0.6, 0.8, 0.6, 0.65]},
    {'name': '古希腊文化圈', 'factors': [0.55, 0.55, 0.7, 0.65, 0.7, 0.65, 0.8]},
    {'name': '古罗马文化圈', 'factors': [0.5, 0.55, 0.75, 0.65, 0.7, 0.7, 0.75]},
    {'name': '波斯文化圈', 'factors': [0.65, 0.6, 0.6, 0.65, 0.65, 0.55, 0.65]},
    {'name': '阿拉伯文化圈', 'factors': [0.8, 0.6, 0.6, 0.6, 0.65, 0.55, 0.6]},
    {'name': '突厥文化圈', 'factors': [0.55, 0.65, 0.5, 0.6, 0.55, 0.5, 0.55]},
    {'name': '蒙古文化圈', 'factors': [0.4, 0.75, 0.45, 0.55, 0.5, 0.45, 0.5]},
    {'name': '满洲文化圈', 'factors': [0.45, 0.7, 0.55, 0.65, 0.6, 0.55, 0.55]},
    {'name': '岭南文化圈', 'factors': [0.4, 0.7, 0.6, 0.7, 0.6, 0.6, 0.65]},
    {'name': '江南文化圈', 'factors': [0.35, 0.65, 0.65, 0.75, 0.65, 0.65, 0.7]},
    {'name': '中原文化圈', 'factors': [0.4, 0.65, 0.7, 0.75, 0.7, 0.65, 0.65]},
    {'name': '关中文化圈', 'factors': [0.45, 0.6, 0.7, 0.7, 0.75, 0.6, 0.6]},
    {'name': '燕赵文化圈', 'factors': [0.45, 0.6, 0.65, 0.7, 0.65, 0.6, 0.55]},
    {'name': '齐鲁文化圈', 'factors': [0.4, 0.6, 0.7, 0.75, 0.7, 0.65, 0.6]},
    {'name': '荆楚文化圈', 'factors': [0.5, 0.7, 0.6, 0.7, 0.65, 0.55, 0.65]},
    {'name': '巴蜀文化圈', 'factors': [0.45, 0.7, 0.55, 0.65, 0.6, 0.55, 0.6]},
    {'name': '吴越文化圈', 'factors': [0.35, 0.65, 0.6, 0.7, 0.6, 0.65, 0.7]},
    {'name': '闽粤文化圈', 'factors': [0.4, 0.7, 0.55, 0.65, 0.55, 0.6, 0.65]},
    {'name': '客家文化圈', 'factors': [0.45, 0.65, 0.55, 0.7, 0.6, 0.55, 0.6]},
    {'name': '滇黔文化圈', 'factors': [0.5, 0.75, 0.45, 0.55, 0.5, 0.45, 0.55]},
    {'name': '青藏文化圈', 'factors': [0.7, 0.75, 0.4, 0.45, 0.5, 0.4, 0.5]},
    {'name': '西域文化圈', 'factors': [0.6, 0.65, 0.5, 0.55, 0.6, 0.45, 0.55]},
    {'name': '草原游牧文化圈', 'factors': [0.35, 0.8, 0.4, 0.5, 0.5, 0.4, 0.5]},
    {'name': '渔猎文化圈', 'factors': [0.3, 0.7, 0.4, 0.45, 0.45, 0.4, 0.45]},
    {'name': '商业文化圈', 'factors': [0.35, 0.55, 0.7, 0.6, 0.5, 0.7, 0.65]},
    {'name': '工业文化圈', 'factors': [0.3, 0.5, 0.75, 0.6, 0.5, 0.75, 0.6]},
    {'name': '信息文化圈', 'factors': [0.3, 0.45, 0.7, 0.6, 0.4, 0.75, 0.7]},
    {'name': '宫廷文化圈', 'factors': [0.5, 0.55, 0.8, 0.75, 0.7, 0.8, 0.75]},
    {'name': '贵族文化圈', 'factors': [0.55, 0.5, 0.7, 0.7, 0.65, 0.75, 0.75]},
    {'name': '士大夫文化圈', 'factors': [0.4, 0.55, 0.65, 0.7, 0.7, 0.65, 0.75]},
    {'name': '市民文化圈', 'factors': [0.35, 0.6, 0.55, 0.65, 0.55, 0.6, 0.65]},
    {'name': '农民文化圈', 'factors': [0.3, 0.7, 0.5, 0.6, 0.6, 0.5, 0.55]},
    {'name': '工匠文化圈', 'factors': [0.35, 0.6, 0.55, 0.6, 0.55, 0.55, 0.65]},
    {'name': '文人文化圈', 'factors': [0.4, 0.55, 0.6, 0.65, 0.65, 0.6, 0.75]},
    {'name': '艺术家文化圈', 'factors': [0.45, 0.55, 0.55, 0.6, 0.6, 0.6, 0.8]},
    {'name': '宗教文化圈', 'factors': [0.8, 0.5, 0.5, 0.55, 0.6, 0.5, 0.6]},
    {'name': '民间信仰文化圈', 'factors': [0.6, 0.65, 0.5, 0.6, 0.6, 0.55, 0.6]},
    {'name': '原始信仰文化圈', 'factors': [0.7, 0.75, 0.4, 0.5, 0.5, 0.45, 0.5]},
    {'name': '现代流行文化圈', 'factors': [0.3, 0.5, 0.6, 0.6, 0.4, 0.7, 0.75]},
    {'name': '传统文化圈', 'factors': [0.5, 0.6, 0.65, 0.7, 0.7, 0.6, 0.7]},
    {'name': '古典文化圈', 'factors': [0.55, 0.55, 0.7, 0.75, 0.75, 0.65, 0.75]},
    {'name': '浪漫主义文化圈', 'factors': [0.45, 0.55, 0.55, 0.6, 0.6, 0.6, 0.75]},
    {'name': '理性主义文化圈', 'factors': [0.35, 0.5, 0.75, 0.65, 0.6, 0.7, 0.65]},
    {'name': '神秘主义文化圈', 'factors': [0.7, 0.6, 0.5, 0.55, 0.65, 0.5, 0.65]},
    {'name': '自然主义文化圈', 'factors': [0.4, 0.75, 0.5, 0.55, 0.55, 0.5, 0.6]},
    {'name': '理想主义文化圈', 'factors': [0.4, 0.55, 0.6, 0.6, 0.6, 0.6, 0.7]},
    {'name': '现实主义文化圈', 'factors': [0.35, 0.6, 0.65, 0.65, 0.55, 0.65, 0.6]},
    {'name': '后现代文化圈', 'factors': [0.4, 0.5, 0.65, 0.6, 0.4, 0.7, 0.75]},
    {'name': '民族主义文化圈', 'factors': [0.5, 0.6, 0.6, 0.8, 0.65, 0.6, 0.6]},
    {'name': '国际主义文化圈', 'factors': [0.35, 0.5, 0.7, 0.55, 0.45, 0.65, 0.65]},
    {'name': '地方主义文化圈', 'factors': [0.5, 0.7, 0.5, 0.65, 0.55, 0.55, 0.55]},
    {'name': '全球主义文化圈', 'factors': [0.3, 0.45, 0.75, 0.55, 0.4, 0.7, 0.7]},
]


def match_cultural_circles(user_vector: list[int], top_k: int = 5) -> list[dict]:
    """
    根据用户七维得分向量匹配文化圈层。
    
    返回：匹配度最高的前K个文化圈层列表
    """
    results = []
    for circle in CULTURAL_CIRCLES:
        similarity = cosine_similarity(user_vector, [int(f * 100) for f in circle['factors']])
        results.append({
            'name': circle['name'],
            'similarity': round(similarity * 100),
            'factors': circle['factors'],
        })
    
    results.sort(key=lambda x: x['similarity'], reverse=True)
    return results[:top_k]


# ============================================================
# 【新增】追加到 personalization/services.py 文件末尾
# 国风兴趣人设测试（15题问卷）
# ============================================================

# ---------- 题库（来自 用户问卷.xlsx） ----------
# type: single=单选 / multi=多选(不限项数)
# options 里的 tags: {标签名: 分值}，分值已按"主维度+5，次维度(括号内)+3"的规则换算，
# 个别"两者各半/以某项为主"的选项按业务含义做了折中取值，可按需调整。

GUOFENG_QUESTIONS: list[dict[str, Any]] = [
    {
        'id': 1, 'type': 'single', 'dimension_group': '基础信息',
        'text': '您的年龄段是？',
        'options': [
            {'label': 'A', 'text': '30岁以下', 'tags': {'Age_Young': 5}},
            {'label': 'B', 'text': '31-45岁', 'tags': {'Age_Middle': 5}},
            {'label': 'C', 'text': '46岁以上', 'tags': {'Age_Old': 5}},
        ],
    },
    {
        'id': 2, 'type': 'single', 'dimension_group': '基础信息',
        'text': '您的性别是？',
        'options': [
            {'label': 'A', 'text': '男', 'tags': {'Gender_Male': 5}},
            {'label': 'B', 'text': '女', 'tags': {'Gender_Female': 5}},
            {'label': 'C', 'text': '不愿透露/其他', 'tags': {'Gender_Neutral': 5}},
        ],
    },
    {
        'id': 3, 'type': 'multi', 'dimension_group': '兴趣内容',
        'text': '以下内容类型您感兴趣的有哪些？（第一组）',
        'options': [
            {'label': 'A', 'text': '舞蹈', 'tags': {'Interest_Dance': 5}},
            {'label': 'B', 'text': '音乐', 'tags': {'Interest_Music': 5}},
            {'label': 'C', 'text': '游戏', 'tags': {'Interest_Gaming': 5}},
            {'label': 'D', 'text': '户外运动', 'tags': {'Interest_Outdoor': 5}},
            {'label': 'E', 'text': '美食', 'tags': {'Interest_Food': 5}},
            {'label': 'F', 'text': '时尚', 'tags': {'Interest_Fashion': 5}},
        ],
    },
    {
        'id': 4, 'type': 'multi', 'dimension_group': '兴趣内容',
        'text': '以下内容类型您感兴趣的有哪些？（第二组）',
        'options': [
            {'label': 'A', 'text': '旅行', 'tags': {'Interest_Travel': 5}},
            {'label': 'B', 'text': '艺术', 'tags': {'Interest_Art': 5}},
            {'label': 'C', 'text': '科技', 'tags': {'Interest_Technology': 5}},
            {'label': 'D', 'text': '体育', 'tags': {'Interest_Sports': 5}},
            {'label': 'E', 'text': '传统文化', 'tags': {'Interest_Culture': 5}},
            {'label': 'F', 'text': '美妆', 'tags': {'Interest_Beauty': 5}},
        ],
    },
    {
        'id': 5, 'type': 'single', 'dimension_group': '消费习惯',
        'text': '您平时为兴趣内容（如国风音乐周边、演出门票、线上课程等）愿意花费的程度？',
        'options': [
            {'label': 'A', 'text': '愿意大量投入（月均500元以上）', 'tags': {'Consumption_High': 5}},
            {'label': 'B', 'text': '适度消费（月均100-500元）', 'tags': {'Consumption_Medium': 5}},
            {'label': 'C', 'text': '很少消费，以免费内容为主', 'tags': {'Consumption_Low': 5}},
        ],
    },
    {
        'id': 6, 'type': 'single', 'dimension_group': '社交互动',
        'text': '您在社交平台上与国风/文化类内容互动的频率？',
        'options': [
            {'label': 'A', 'text': '经常评论、转发、参与话题讨论', 'tags': {'Social_Strong': 5}},
            {'label': 'B', 'text': '偶尔点赞或评论', 'tags': {'Social_Medium': 5}},
            {'label': 'C', 'text': '基本只浏览，很少互动', 'tags': {'Social_Weak': 5}},
        ],
    },
    {
        'id': 7, 'type': 'single', 'dimension_group': '价值观',
        'text': '关于传统与现代，您更认同以下哪种说法？',
        'options': [
            {'label': 'A', 'text': '传统文化的传承与坚守非常重要', 'tags': {'Value_Traditional': 5}},
            {'label': 'B', 'text': '更喜欢融合创新、与时俱进的表达方式', 'tags': {'Value_Modern': 5}},
            {'label': 'C', 'text': '两者兼顾，传统与现代结合',
             'tags': {'Value_Traditional': 2.5, 'Value_Modern': 2.5}},
        ],
    },
    {
        'id': 8, 'type': 'single', 'dimension_group': '价值观',
        'text': '以下哪种描述更符合您？',
        'options': [
            {'label': 'A', 'text': '我更看重个人独特性和自我表达', 'tags': {'Value_SelfExpression': 5}},
            {'label': 'B', 'text': '我更看重群体归属感和集体认同', 'tags': {'Value_Collectivism': 5}},
            {'label': 'C', 'text': '我追求独立思考，不受他人观点左右', 'tags': {'Value_Individualism': 5}},
        ],
    },
    {
        'id': 9, 'type': 'single', 'dimension_group': '价值观',
        'text': '选择内容或产品时，您最看重什么？',
        'options': [
            {'label': 'A', 'text': '品质与制作的精良程度', 'tags': {'Value_Quality': 5}},
            {'label': 'B', 'text': '性价比', 'tags': {'Value_Quality': 3, 'Consumption_Medium': 3}},
            {'label': 'C', 'text': '独特性与创意', 'tags': {'Value_SelfExpression': 5}},
        ],
    },
    {
        'id': 10, 'type': 'single', 'dimension_group': '平台偏好',
        'text': '您最常使用的娱乐/内容平台类型是？',
        'options': [
            {'label': 'A', 'text': '短视频平台（抖音/快手等）', 'tags': {'Entertainment_TikTok': 5}},
            {'label': 'B', 'text': '音乐类App（网易云/QQ音乐等）', 'tags': {'Entertainment_Music': 5}},
            {'label': 'C', 'text': '长视频平台（B站/爱奇艺等）', 'tags': {'Entertainment_Video': 5}},
        ],
    },
    {
        'id': 11, 'type': 'single', 'dimension_group': '生活方式',
        'text': '以下哪种最符合您的日常生活状态？（动静倾向）',
        'options': [
            {'label': 'A', 'text': '积极运动、户外活动多',
             'tags': {'Lifestyle_Active': 5, 'Interest_Outdoor': 3}},
            {'label': 'B', 'text': '喜欢宅家放松、休闲娱乐',
             'tags': {'Lifestyle_Relaxed': 5, 'Lifestyle_Home': 3}},
            {'label': 'C', 'text': '热衷夜生活、聚会社交', 'tags': {'Lifestyle_NightLife': 5}},
        ],
    },
    {
        'id': 12, 'type': 'single', 'dimension_group': '生活方式',
        'text': '以下哪种最符合您的日常生活状态？（文化倾向）',
        'options': [
            {'label': 'A', 'text': '喜欢看展览、听音乐会、观演出等文化活动', 'tags': {'Lifestyle_Cultural': 5}},
            {'label': 'B', 'text': '喜欢户外探索、徒步、旅行', 'tags': {'Lifestyle_Outdoor': 5}},
            {'label': 'C', 'text': '日常平淡，居家为主',
             'tags': {'Lifestyle_Home': 5, 'Lifestyle_Relaxed': 3}},
        ],
    },
    {
        'id': 13, 'type': 'single', 'dimension_group': '流行态度',
        'text': '您对流行趋势的态度是？',
        'options': [
            {'label': 'A', 'text': '喜欢追逐最新潮流和热点', 'tags': {'Trend_Follower': 5}},
            {'label': 'B', 'text': '更喜欢做自己，不太跟风', 'tags': {'Trend_Independent': 5}},
            {'label': 'C', 'text': '视情况而定，两者都会关注',
             'tags': {'Trend_Follower': 2.5, 'Trend_Independent': 2.5}},
        ],
    },
    {
        'id': 14, 'type': 'single', 'dimension_group': '自我表达',
        'text': '您是否喜欢通过穿搭、内容创作等方式展现自己？',
        'options': [
            {'label': 'A', 'text': '非常喜欢，经常通过多种方式表达自己', 'tags': {'SelfExpr_High': 5}},
            {'label': 'B', 'text': '比较低调，不太主动展示自己', 'tags': {'SelfExpr_Low': 5}},
            {'label': 'C', 'text': '偶尔会，看心情',
             'tags': {'SelfExpr_High': 3, 'SelfExpr_Low': 2}},
        ],
    },
    {
        'id': 15, 'type': 'multi', 'dimension_group': '国风呈现偏好',
        'text': '在国风音乐相关内容中，您最希望看到哪些呈现形式？',
        'options': [
            {'label': 'A', 'text': '武术/功夫展示',
             'tags': {'Interest_Sports': 5, 'Interest_Culture': 3}},
            {'label': 'B', 'text': '古风舞蹈',
             'tags': {'Interest_Dance': 5, 'Interest_Culture': 3}},
            {'label': 'C', 'text': '传统乐器演奏',
             'tags': {'Interest_Music': 5, 'Interest_Culture': 3}},
            {'label': 'D', 'text': '古装造型美妆',
             'tags': {'Interest_Beauty': 5, 'Interest_Fashion': 3}},
            {'label': 'E', 'text': '文化历史故事',
             'tags': {'Interest_Culture': 5, 'Value_Traditional': 3}},
            {'label': 'F', 'text': '现代改编/融合演绎',
             'tags': {'Value_Modern': 5, 'Entertainment_Video': 3}},
        ],
    },
]


def get_guofeng_questions() -> list[dict[str, Any]]:
    """获取国风人设测试题库（15题）。"""
    return GUOFENG_QUESTIONS


# ---------- 标签打分 ----------

def _guofeng_question_map() -> dict[int, dict[str, Any]]:
    return {q['id']: q for q in GUOFENG_QUESTIONS}


def calculate_guofeng_tag_scores(answers: dict) -> dict[str, float]:
    """
    根据用户答案累加标签分。

    answers 格式：{question_id: option_label 或 [option_label, ...]}
    单选题传字符串（如 'A'），多选题传列表（如 ['A','C']）。
    """
    q_map = _guofeng_question_map()
    tag_scores: dict[str, float] = {}

    for q_id, selected in answers.items():
        try:
            q_id_int = int(q_id)
        except (ValueError, TypeError):
            continue
        question = q_map.get(q_id_int)
        if not question:
            continue

        labels = selected if isinstance(selected, list) else [selected]
        option_map = {opt['label']: opt for opt in question['options']}
        for label in labels:
            opt = option_map.get(str(label).strip().upper())
            if not opt:
                continue
            for tag, score in opt['tags'].items():
                tag_scores[tag] = tag_scores.get(tag, 0) + score

    return tag_scores


# ---------- 六维人设匹配向量 ----------

# 每个维度由哪些标签构成，及每个标签在该维度上代表的"锚点值"（0-100）。
# 维度得分 = 该维度下出现过的标签，按各自分值加权后的锚点加权平均。
# 没有任何相关标签命中时，默认取中间值 50（表示信息不足，不偏向任何一边）。
PERSONA_DIMENSION_ANCHORS: dict[str, dict[str, float]] = {
    'traditionalism': {          # 传统认同度
        'Value_Traditional': 100,
        'Value_Modern': 0,
    },
    'consumption': {              # 消费投入度
        'Consumption_High': 100,
        'Consumption_Medium': 55,
        'Consumption_Low': 10,
    },
    'social': {                   # 社交活跃度
        'Social_Strong': 100,
        'Social_Medium': 55,
        'Social_Weak': 10,
    },
    'self_expression': {          # 自我表达欲
        'SelfExpr_High': 100,
        'Value_SelfExpression': 90,
        'SelfExpr_Low': 10,
    },
    'trend': {                    # 潮流敏感度
        'Trend_Follower': 100,
        'Trend_Independent': 10,
    },
    'cultural_life': {            # 文化生活参与度
        'Lifestyle_Cultural': 100,
        'Interest_Culture': 85,
        'Lifestyle_Outdoor': 60,
        'Lifestyle_Active': 55,
        'Lifestyle_NightLife': 35,
        'Lifestyle_Relaxed': 25,
        'Lifestyle_Home': 15,
    },
}

# 六维顺序固定，供人设向量比对使用
PERSONA_DIMENSIONS = [
    'traditionalism', 'consumption', 'social',
    'self_expression', 'trend', 'cultural_life',
]


def calculate_guofeng_persona_vector(tag_scores: dict[str, float]) -> list[int]:
    """将标签打分归一化为六维人设匹配向量（0-100）。"""
    vector = []
    for dim in PERSONA_DIMENSIONS:
        anchors = PERSONA_DIMENSION_ANCHORS[dim]
        weighted_sum = 0.0
        weight_total = 0.0
        for tag, anchor_value in anchors.items():
            w = tag_scores.get(tag, 0)
            if w:
                weighted_sum += w * anchor_value
                weight_total += w
        value = round(weighted_sum / weight_total) if weight_total > 0 else 50
        vector.append(max(0, min(100, value)))
    return vector


# ---------- 预设人设 ----------
# factors 顺序对应 PERSONA_DIMENSIONS：
# [传统认同度, 消费投入度, 社交活跃度, 自我表达欲, 潮流敏感度, 文化生活参与度]
GUOFENG_PERSONAS = [
    {
        'name': '国风挚爱型',
        'description': '对传统文化认同度高，愿意为国风内容付费，热衷参与文化活动，是核心付费用户。',
        'factors': [85, 80, 60, 55, 30, 85],
    },
    {
        'name': '潮流融合型',
        'description': '偏爱现代化的表达方式，追新敏感，更喜欢国风与流行元素的融合改编内容。',
        'factors': [40, 60, 65, 70, 85, 55],
    },
    {
        'name': '社交达人型',
        'description': '社交平台互动活跃，喜欢通过内容展示自己，是传播扩散的核心力量。',
        'factors': [45, 55, 90, 85, 70, 50],
    },
    {
        'name': '静赏体验型',
        'description': '消费和社交都比较克制，但文化参与度不低，偏好安静深度地体验内容。',
        'factors': [70, 25, 25, 30, 20, 70],
    },
    {
        'name': '泛兴趣尝鲜型',
        'description': '各项倾向都比较均衡，暂无明显偏好，属于待培养、待进一步引导的潜力用户。',
        'factors': [50, 50, 50, 50, 55, 45],
    },
]


def match_guofeng_personas(user_vector: list[int], top_k: int = 3) -> list[dict]:
    """
    根据用户六维人设向量匹配预设人设。

    复用 cosine_similarity()（与文化圈层测试共用同一相似度算法）。
    """
    results = []
    for persona in GUOFENG_PERSONAS:
        similarity = cosine_similarity(user_vector, persona['factors'])
        results.append({
            'name': persona['name'],
            'description': persona['description'],
            'similarity': round(similarity * 100),
            'factors': persona['factors'],
        })

    results.sort(key=lambda x: x['similarity'], reverse=True)
    return results[:top_k]


# ---------- 保存 / 查询 ----------

def save_guofeng_persona_test(user_id: str, answers: dict, tag_scores: dict[str, float],
                               user_vector: list[int], matched_personas: list[dict]) -> dict[str, Any]:
    """保存国风人设测试结果到数据库。"""
    from .models import GuofengPersonaTest

    try:
        test = GuofengPersonaTest(
            user_id=user_id,
            d1_traditionalism=user_vector[0],
            d2_consumption=user_vector[1],
            d3_social=user_vector[2],
            d4_self_expression=user_vector[3],
            d5_trend=user_vector[4],
            d6_cultural_life=user_vector[5],
            tag_scores=tag_scores,
            matched_personas=matched_personas,
            answers=answers,
        )
        test.save()
        return {
            'success': True,
            'message': '测试结果已保存',
            'test_id': test.id,
        }
    except Exception as e:
        return {
            'success': False,
            'message': f'保存失败：{str(e)}',
        }


def get_guofeng_persona_test(user_id: str) -> dict[str, Any]:
    """获取用户最新的国风人设测试结果。"""
    from .models import GuofengPersonaTest

    try:
        test = GuofengPersonaTest.objects.filter(user_id=user_id).order_by('-test_date').first()
        if not test:
            return {'has_test': False, 'message': '尚未完成国风人设测试'}

        return {
            'has_test': True,
            'user_vector': [
                test.d1_traditionalism,
                test.d2_consumption,
                test.d3_social,
                test.d4_self_expression,
                test.d5_trend,
                test.d6_cultural_life,
            ],
            'tag_scores': test.tag_scores,
            'matched_personas': test.matched_personas,
            'answers': test.answers,
            'test_date': str(test.test_date),
            'test_id': test.id,
        }
    except Exception as e:
        return {
            'has_test': False,
            'message': f'查询失败：{str(e)}',
        }


# ============================================================
# 基于用户人设的曲目推荐（NEO4J_3 · 精简图）
# ============================================================
# 图（NEO4J_3）：
#   UserCluster -[:HAS_ATTR side=user]-> Attribute
#   UserCluster -[:LIKES count]-> Music
#   UserCluster -[:MAPS_TO]-> MusicCluster -[:CONTAINS]-> Music
# 主流程：
#   1. guofeng_persona_test 六维 → 图谱五属性
#   2. 与各 UserCluster HAS_ATTR(side=user) 余弦相似度 → 最近用户类别
#   3. 该 UserCluster -[:LIKES]-> Music，按 count 降序取 Top3
#   4. LIKES 不足 → MAPS_TO→CONTAINS 补足 → 仍不足则随机
#   5. Music.id 经 MUSIC_ID_MAP 落本地资源

from typing import Optional as _Optional
from neo4j import Driver as _Driver, GraphDatabase as _GraphDatabase

_n3_driver: _Optional[_Driver] = None

# 人设六维 → 图谱五属性（0 traditionalism / 1 consumption / 2 social /
# 3 self_expression / 4 trend / 5 cultural_life）
_PERSONA_TO_GRAPH_ATTR: dict[str, list[tuple[int, float]]] = {
    '中国文化': [(0, 1.0)],
    '美妆时尚': [(1, 0.6), (3, 0.4)],
    '潮流娱乐': [(2, 0.4), (4, 0.6)],
    '旅行户外': [(5, 0.7)],
    '健康养生': [(5, 0.3)],
}
_GRAPH_ATTR_ORDER = ['中国文化', '健康养生', '旅行户外', '潮流娱乐', '美妆时尚']


def _get_n3_driver() -> _Driver:
    """严格只读 config.NEO4J_3，连不上直接报错，不回退其它库。"""
    global _n3_driver
    if _n3_driver is not None:
        return _n3_driver
    cfg = svc_config.NEO4J_3 or {}
    uri = (cfg.get('URI') or '').strip()
    if not uri:
        raise RuntimeError('推荐 Neo4j 未配置：请填写 config.services.NEO4J_3')
    _n3_driver = _GraphDatabase.driver(
        uri, auth=(cfg.get('USER', 'neo4j'), cfg.get('PASSWORD', '')),
    )
    return _n3_driver


def _n3_database() -> str:
    return (svc_config.NEO4J_3 or {}).get('DATABASE', 'neo4j')


def _n3_run(cypher: str, params: dict | None = None) -> list[dict]:
    driver = _get_n3_driver()
    with driver.session(database=_n3_database()) as s:
        return [dict(r) for r in s.run(cypher, params or {})]


def _persona_vector_to_graph_attrs(persona_vector: list[int | float]) -> dict[str, float]:
    """六维人设(0-100) → 图谱五属性（归一化到约 -1..1）。"""
    norm = [(float(v) - 50.0) / 50.0 for v in persona_vector]
    result: dict[str, float] = {}
    for attr, weights in _PERSONA_TO_GRAPH_ATTR.items():
        total_w = sum(w for _, w in weights) or 1.0
        result[attr] = sum(norm[i] * w for i, w in weights) / total_w
    return result


def _get_user_persona_vector(user_id: str) -> list[float] | None:
    """从 guofeng_persona_test 读取最新六维向量。"""
    try:
        from .models import GuofengPersonaTest
        test = GuofengPersonaTest.objects.filter(user_id=user_id).order_by('-test_date').first()
        if not test:
            return None
        return [
            float(test.d1_traditionalism),
            float(test.d2_consumption),
            float(test.d3_social),
            float(test.d4_self_expression),
            float(test.d5_trend),
            float(test.d6_cultural_life),
        ]
    except Exception:
        return None


def _cosine(a: list[float], b: list[float]) -> float:
    import math
    if len(a) != len(b) or not a:
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a)) or 1e-9
    nb = math.sqrt(sum(x * x for x in b)) or 1e-9
    return dot / (na * nb)


def _find_nearest_user_cluster(user_attrs: dict[str, float]) -> dict[str, Any]:
    """
    网页用户五属性 vs 各 UserCluster 的 HAS_ATTR(side=user) → 余弦相似度 Top1。
    簇属性已在图里预聚合，无需再扫个体用户。
    """
    labels = (svc_config.NEO4J_3 or {}).get('LABELS', {})
    rels = (svc_config.NEO4J_3 or {}).get('RELS', {})
    lbl_uc = labels.get('UserCluster', 'UserCluster')
    lbl_a = labels.get('Attribute', 'Attribute')
    rel_ha = rels.get('cluster_attr', 'HAS_ATTR')

    cypher = f"""
MATCH (uc:{lbl_uc})-[r:{rel_ha}]->(a:{lbl_a})
WHERE coalesce(r.side, 'user') = 'user'
RETURN uc.id AS cluster, a.id AS attr, r.value AS value
"""
    rows = _n3_run(cypher)
    by_cluster: dict[str, dict[str, float]] = {}
    for row in rows:
        cid = str(row.get('cluster') or '')
        attr = str(row.get('attr') or '')
        if not cid or not attr:
            continue
        by_cluster.setdefault(cid, {})[attr] = float(row.get('value') or 0)

    uf = [float(user_attrs.get(a, 0)) for a in _GRAPH_ATTR_ORDER]
    scored: list[dict[str, Any]] = []
    for cid, attrs in by_cluster.items():
        cf = [float(attrs.get(a, 0)) for a in _GRAPH_ATTR_ORDER]
        scored.append({
            'cluster': cid,
            'similarity': round(_cosine(uf, cf), 4),
            'cluster_attrs': attrs,
        })
    scored.sort(key=lambda x: x['similarity'], reverse=True)
    if not scored:
        return {'cluster': '', 'similarity': 0.0, 'cluster_attrs': {}}
    return scored[0]


def _maps_to_music_clusters(user_cluster: str, top_k: int = 3) -> list[dict]:
    """UserCluster -[:MAPS_TO]-> MusicCluster，按 weight 降序取 TopK。"""
    labels = (svc_config.NEO4J_3 or {}).get('LABELS', {})
    rels = (svc_config.NEO4J_3 or {}).get('RELS', {})
    cypher = f"""
MATCH (uc:{labels.get('UserCluster', 'UserCluster')} {{id: $uc}})
      -[m:{rels.get('maps_to', 'MAPS_TO')}]->
      (mc:{labels.get('MusicCluster', 'MusicCluster')})
RETURN mc.id AS music_cluster,
       coalesce(m.weight, 0) AS weight,
       coalesce(m.count, 0) AS count
ORDER BY weight DESC, count DESC
LIMIT $top_k
"""
    return _n3_run(cypher, {'uc': user_cluster, 'top_k': top_k})


def _likes_songs_from_user_cluster(user_cluster: str, limit: int = 3) -> list[dict[str, Any]]:
    """
    UserCluster -[:LIKES {count}]-> Music，按点赞热度降序取歌。
    返回 [{'music_id': str, 'like_count': int}, ...]
    """
    labels = (svc_config.NEO4J_3 or {}).get('LABELS', {})
    rels = (svc_config.NEO4J_3 or {}).get('RELS', {})
    cypher = f"""
MATCH (uc:{labels.get('UserCluster', 'UserCluster')} {{id: $uc}})
      -[lk:{rels.get('likes', 'LIKES')}]->
      (m:{labels.get('Music', 'Music')})
RETURN toString(m.id) AS music_id,
       coalesce(lk.count, 0) AS like_count
ORDER BY like_count DESC, music_id ASC
LIMIT $limit
"""
    rows = _n3_run(cypher, {'uc': user_cluster, 'limit': int(limit)})
    out: list[dict[str, Any]] = []
    for row in rows:
        mid = str(row.get('music_id') or '').strip()
        if not mid:
            continue
        out.append({
            'music_id': mid,
            'like_count': int(row.get('like_count') or 0),
        })
    return out


def _contains_songs_from_user_cluster(
    user_cluster: str,
    limit: int = 10,
    exclude: set[str] | None = None,
) -> list[dict[str, Any]]:
    """
    兜底：UserCluster -[:MAPS_TO]-> MusicCluster -[:CONTAINS]-> Music
    按 MAPS_TO.weight 优先，再按 music_id。
    """
    exclude = exclude or set()
    labels = (svc_config.NEO4J_3 or {}).get('LABELS', {})
    rels = (svc_config.NEO4J_3 or {}).get('RELS', {})
    cypher = f"""
MATCH (uc:{labels.get('UserCluster', 'UserCluster')} {{id: $uc}})
      -[mp:{rels.get('maps_to', 'MAPS_TO')}]->
      (mc:{labels.get('MusicCluster', 'MusicCluster')})
      -[:{rels.get('contains', 'CONTAINS')}]->
      (m:{labels.get('Music', 'Music')})
RETURN toString(m.id) AS music_id,
       mc.id AS music_cluster,
       coalesce(mp.weight, 0) AS weight
ORDER BY weight DESC, music_id ASC
LIMIT $limit
"""
    rows = _n3_run(cypher, {'uc': user_cluster, 'limit': int(limit)})
    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in rows:
        mid = str(row.get('music_id') or '').strip()
        if not mid or mid in exclude or mid in seen:
            continue
        seen.add(mid)
        out.append({
            'music_id': mid,
            'music_cluster': str(row.get('music_cluster') or ''),
            'weight': float(row.get('weight') or 0),
        })
    return out


def _all_graph_music_ids(limit: int = 200) -> list[str]:
    """图中全部 Music.id，供随机补足。"""
    labels = (svc_config.NEO4J_3 or {}).get('LABELS', {})
    cypher = f"""
MATCH (m:{labels.get('Music', 'Music')})
RETURN toString(m.id) AS music_id
ORDER BY music_id
LIMIT $limit
"""
    try:
        return [
            str(r.get('music_id'))
            for r in _n3_run(cypher, {'limit': int(limit)})
            if r.get('music_id') is not None
        ]
    except Exception:
        return []


def _catalog_by_id() -> dict[str, dict[str, Any]]:
    """本地资源目录索引：detail_id → catalog 项（优先用已缓存目录，避免反复扫盘）。"""
    try:
        from data_display import services as dd
        items = list(getattr(dd, '_PLACEHOLDER_CATALOG', None) or [])
        if not items:
            items = list(dd.refresh_catalog())
        return {str(x['id']): x for x in items if x.get('id')}
    except Exception:
        return {}


def _resolve_song_ref(ref: int | str) -> dict[str, str]:
    """
    解析一首歌：
    - int / 纯数字字符串 → MUSIC_ID_MAP
    - 其它字符串 → 当作 detail_id（本地资源 id）
    """
    music_map = getattr(svc_config, 'MUSIC_ID_MAP', {}) or {}
    catalog = _catalog_by_id()

    if isinstance(ref, int) or (isinstance(ref, str) and ref.isdigit()):
        key: int | str = int(ref) if str(ref).isdigit() else ref
        info = music_map.get(key) or music_map.get(str(key)) or {}
        mid = str(ref)
        detail_id = info.get('detail_id') or f'graph-music-{mid}'
        cat = catalog.get(str(detail_id)) or {}
        return {
            'id': str(detail_id),
            'title': info.get('title') or cat.get('title') or f'图谱歌曲 {mid}',
            'audio_url': info.get('audio_url') or cat.get('audio_url') or '',
            'intro': info.get('intro') or cat.get('intro') or '',
            'mv_url': info.get('mv_url') or cat.get('mv_url') or '',
            'graph_music_id': mid,
        }

    # detail_id 直接引用（如 res-青花瓷）
    detail_id = str(ref)
    cat = catalog.get(detail_id) or {}
    # 若 MUSIC_ID_MAP 里有以 detail_id 为值的项，补全 title/audio
    for _k, info in music_map.items():
        if info.get('detail_id') == detail_id:
            return {
                'id': detail_id,
                'title': info.get('title') or cat.get('title') or detail_id,
                'audio_url': info.get('audio_url') or cat.get('audio_url') or '',
                'intro': info.get('intro') or cat.get('intro') or '',
                'mv_url': info.get('mv_url') or cat.get('mv_url') or '',
                'graph_music_id': str(_k),
            }
    title = cat.get('title') or (detail_id[4:] if detail_id.startswith('res-') else detail_id)
    audio = cat.get('audio_url') or (
        f'/media/resources/{title}/audio.mp3' if title else ''
    )
    return {
        'id': detail_id,
        'title': title,
        'audio_url': audio,
        'intro': cat.get('intro') or '',
        'mv_url': cat.get('mv_url') or '',
        'graph_music_id': '',
    }


def _songs_from_music_cluster(music_cluster: str) -> list[int | str]:
    """MUSIC_CLUSTER_SONGS[cluster] → 歌曲引用列表。"""
    mapping = getattr(svc_config, 'MUSIC_CLUSTER_SONGS', {}) or {}
    return list(mapping.get(music_cluster) or mapping.get(str(music_cluster)) or [])


def _local_resource_song_refs() -> list[str]:
    """扫描 media/resources 本地歌曲，返回 detail_id 列表（如 res-青花瓷）。"""
    try:
        from data_display.services import refresh_catalog
        catalog = refresh_catalog()
        return [str(x['id']) for x in catalog if str(x.get('id', '')).startswith('res-')]
    except Exception:
        return []


def _all_mapped_song_refs() -> list[int | str]:
    """
    可随机抽取的歌曲引用：
    1) 图 Music 节点
    2) MUSIC_ID_MAP / MUSIC_CLUSTER_SONGS
    3) 本地 media/resources
    """
    refs: list[int | str] = []
    seen: set[str] = set()

    def _add(r: int | str) -> None:
        k = str(r)
        if k and k not in seen:
            seen.add(k)
            refs.append(r)

    for mid in _all_graph_music_ids():
        _add(mid)
    for lst in (getattr(svc_config, 'MUSIC_CLUSTER_SONGS', {}) or {}).values():
        for r in lst or []:
            _add(r)
    for k in (getattr(svc_config, 'MUSIC_ID_MAP', {}) or {}):
        _add(k)
    if not refs:
        for detail_id in _local_resource_song_refs():
            _add(detail_id)
    return refs


def _random_song_refs(count: int = 3, exclude: set[str] | None = None) -> list[int | str]:
    """从图 Music / 映射池 / 本地资源随机抽歌。"""
    import random
    exclude = exclude or set()
    pool = [r for r in _all_mapped_song_refs() if str(r) not in exclude]
    if not pool:
        return []
    random.shuffle(pool)
    return pool[:count]


def _resolve_persona_vector_for_recommend(
    user_id: str,
    persona_override: str | None = None,
) -> tuple[list[float] | None, str]:
    """
    解析推荐用人设向量。
    测试模式 + 指定画像名 → 使用 GUOFENG_PERSONAS 预设向量；
    否则读用户真实国风人设测试结果。
    返回 (vector, source)。
    """
    test_mode = bool(getattr(svc_config, 'IMAGERY_TEST_MODE', False))
    name = (persona_override or '').strip()
    if test_mode and name and name.lower() not in ('auto', 'real', 'none', '0'):
        for persona in GUOFENG_PERSONAS:
            if persona['name'] == name:
                return [float(x) for x in persona['factors']], f'test_persona:{name}'
        # 名称不匹配时仍回退真实结果，并在 message 侧可感知
    vector = _get_user_persona_vector(user_id)
    if vector is not None:
        return vector, 'user_persona_test'
    return None, 'missing'


def _resolve_circle_for_recommend(
    user_id: str,
    circle_override: str | None = None,
) -> tuple[list[float] | None, str, str]:
    """返回文化圈层七维向量、圈层名称及来源。"""
    selected = (circle_override or '').strip()
    if selected and selected.lower() not in ('auto', 'real', 'none', '0'):
        matched = next((row for row in CULTURAL_CIRCLES if row['name'] == selected), None)
        vector = [float(v) * 100 for v in matched['factors']] if matched else None
        return vector, selected, 'selected_circle'

    result = get_cultural_circle_test(user_id)
    if not result.get('has_test'):
        return None, '', 'missing'
    matched_circles = result.get('matched_circles') or []
    circle_name = ''
    if matched_circles:
        first = matched_circles[0]
        circle_name = str(first.get('name') if isinstance(first, dict) else first)
    return [float(v) for v in result.get('user_vector') or []], circle_name, 'user_circle_test'


def _recommend_user_aliases(user_id: str) -> list[str]:
    """兼容前端曾分别使用 username 与 user_id 写入的历史记录。"""
    value = str(user_id).strip()
    aliases = {value}
    try:
        with connection.cursor() as cur:
            cur.execute(
                "SELECT TOP 1 user_id, username FROM behave.Users "
                "WHERE user_id = %s OR username = %s",
                [value, value],
            )
            row = cur.fetchone()
        if row:
            aliases.update(str(v).strip() for v in row if v is not None)
    except Exception:
        pass
    return [value for value in aliases if value]


def _media_url(path: Any) -> str:
    value = str(path or '').strip().replace('\\', '/')
    if not value or value.startswith(('http://', 'https://', '/')):
        return value
    return '/media/' + '/'.join(urllib.parse.quote(part) for part in value.split('/'))


def _recommend_from_sql_signals(
    user_id: str,
    persona_vector: list[float] | None,
    persona_source: str,
    circle_vector: list[float] | None,
    circle_name: str,
    circle_source: str,
    limit: int = 3,
) -> dict[str, Any]:
    """按文化圈层、国风画像与听歌历史综合打分可播放曲目。"""
    aliases = _recommend_user_aliases(user_id)
    placeholders = ','.join(['%s'] * len(aliases))
    with connection.cursor() as cur:
        cur.execute(
            f"SELECT TOP 300 song_id, play_time FROM behave.PlayRecords "
            f"WHERE user_id IN ({placeholders}) ORDER BY play_time DESC",
            aliases,
        )
        history_rows = cur.fetchall()
        cur.execute(
            """
            SELECT s.id, s.title, s.genre, s.audio_url, s.cover_url,
                   c.category_name, c.parent_category
            FROM dbo.traditional_song s
            LEFT JOIN dbo.music_category c ON c.category_id = s.category_id
            WHERE s.audio_url LIKE 'audio/%'
            """
        )
        song_rows = cur.fetchall()

    songs: list[dict[str, Any]] = []
    by_id: dict[str, dict[str, Any]] = {}
    for row in song_rows:
        item = {
            'id': str(row[0]),
            'title': row[1] or '',
            'genre': row[2] or '',
            'audio_url': _media_url(row[3]),
            'cover_url': _media_url(row[4]),
            'category': row[5] or '',
            'parent_category': row[6] or '',
        }
        songs.append(item)
        by_id[item['id']] = item

    play_counts: dict[str, int] = {}
    category_counts: dict[str, int] = {}
    parent_counts: dict[str, int] = {}
    genre_counts: dict[str, int] = {}
    valid_history_count = 0
    for song_id, _play_time in history_rows:
        key = str(song_id or '').strip()
        played = by_id.get(key)
        if not played:
            continue
        valid_history_count += 1
        play_counts[key] = play_counts.get(key, 0) + 1
        for bucket, value in (
            (category_counts, played['category']),
            (parent_counts, played['parent_category']),
            (genre_counts, played['genre']),
        ):
            if value:
                bucket[value] = bucket.get(value, 0) + 1

    history_peak = max([1, *category_counts.values(), *parent_counts.values(), *genre_counts.values()])
    persona = list(persona_vector or [50, 50, 50, 50, 50, 50])
    persona += [50] * (6 - len(persona))
    circle = list(circle_vector or [50, 50, 50, 50, 50, 50, 50])
    circle += [50] * (7 - len(circle))

    circle_keyword_rules = {
        '江南': ('江南', '吴越'),
        '吴越': ('江南', '吴越'),
        '草原': ('草原', '蒙古'),
        '蒙古': ('草原', '蒙古'),
        '西域': ('新疆', '西域'),
        '岭南': ('广东', '岭南'),
        '齐鲁': ('山东', '齐鲁'),
        '巴蜀': ('四川', '巴蜀'),
        '闽粤': ('福建', '广东'),
    }

    ranked: list[tuple[float, int, dict[str, Any]]] = []
    for song in songs:
        parent = str(song['parent_category'])
        category = str(song['category'])
        genre = str(song['genre'])
        haystack = f'{parent} {category} {genre} {song["title"]}'
        score = 10.0
        reasons: list[str] = []

        # 人设六维：[传统、消费、社交、表达、潮流、文化生活]
        if parent == '民歌':
            score += persona[0] * .11 + persona[2] * .04
        elif parent == '戏曲':
            score += persona[0] * .15 + persona[5] * .09
        elif parent == '乐器':
            score += persona[0] * .10 + persona[5] * .12
        elif parent == '说唱':
            score += persona[2] * .06 + persona[3] * .08 + persona[4] * .15
        if persona_source != 'missing':
            reasons.append('符合用户画像')

        # 圈层七维中的地域/族群与审美艺术维度影响最大。
        if parent == '民歌':
            score += circle[3] * .12
        elif parent in ('戏曲', '乐器'):
            score += circle[6] * .13
        elif parent == '说唱':
            score += circle[5] * .08
        matched_circle_keyword = False
        for marker, keywords in circle_keyword_rules.items():
            if marker in circle_name and any(word in haystack for word in keywords):
                score += 22
                matched_circle_keyword = True
                break
        if circle_source != 'missing':
            reasons.append('契合文化圈层' if not matched_circle_keyword else f'契合{circle_name}')

        history_score = (
            parent_counts.get(parent, 0) * 22
            + category_counts.get(category, 0) * 30
            + genre_counts.get(genre, 0) * 14
        ) / history_peak
        if history_score:
            score += history_score
            reasons.append('延续常听曲风')
        repeat_count = play_counts.get(song['id'], 0)
        if repeat_count:
            score -= min(18, repeat_count * 6)

        song['recommend_score'] = round(score, 2)
        song['recommend_reason'] = '、'.join(dict.fromkeys(reasons)) or '国风曲库精选'
        song['recommend_source'] = 'hybrid_sql'
        ranked.append((score, int(song['id']), song))

    ranked.sort(key=lambda item: (-item[0], item[1]))
    items = [entry[2] for entry in ranked[:limit]]
    persona_label = persona_source.split(':', 1)[1] if persona_source.startswith('test_persona:') else (
        '测试结果' if persona_source == 'user_persona_test' else '待完成测试'
    )
    circle_label = circle_name or '待完成测试'
    return {
        'source': 'personalization_recommend',
        'user_id': user_id,
        'items': items,
        'recommend_mode': 'hybrid',
        'persona_source': persona_source,
        'circle_source': circle_source,
        'cultural_circle': circle_label,
        'history_count': valid_history_count,
        'message': (
            f'基于文化圈层（{circle_label}）、用户画像（{persona_label}）'
            f'和 {valid_history_count} 条有效听歌记录生成'
        ),
    }


def recommend_by_persona(
    user_id: str,
    persona_override: str | None = None,
    circle_override: str | None = None,
) -> dict[str, Any]:
    """
    私人空间 · 推荐曲目（固定 3 首）。

    主路径：
      人设五属性 → 最近 UserCluster → LIKES 热度 Top3 → MUSIC_ID_MAP

    兜底：MAPS_TO→CONTAINS → 随机
    persona_override：测试模式下前端下发的音乐画像类别名（或 auto）。
    recommend_mode: likes | mixed | random
    """
    NEED = 3
    persona_vector, persona_source = _resolve_persona_vector_for_recommend(
        user_id, persona_override,
    )
    circle_vector, circle_name, circle_source = _resolve_circle_for_recommend(
        user_id, circle_override,
    )

    try:
        sql_result = _recommend_from_sql_signals(
            user_id=user_id,
            persona_vector=persona_vector,
            persona_source=persona_source,
            circle_vector=circle_vector,
            circle_name=circle_name,
            circle_source=circle_source,
            limit=NEED,
        )
        if sql_result.get('items'):
            return sql_result
    except Exception:
        # SQL 曲库异常时继续使用原有 Neo4j 推荐链路。
        pass

    def _pack_random(msg_prefix: str, persona: list[float] | None = None) -> dict[str, Any]:
        refs = _random_song_refs(NEED)
        items = [_resolve_song_ref(r) for r in refs]
        for it in items:
            it['from_cluster'] = ''
            it['from_music_cluster'] = ''
            it['like_count'] = 0
            it['recommend_source'] = 'random'
        if items:
            msg = f'{msg_prefix}，已随机抽取 {len(items)} 首'
        else:
            msg = (
                f'{msg_prefix}，但图中 Music / MUSIC_ID_MAP / 本地资源均为空'
            )
        return {
            'source': 'personalization_recommend',
            'user_id': user_id,
            'items': items,
            'matched_user_cluster': {},
            'liked_music': [],
            'mapped_music_clusters': [],
            'persona_vector': persona,
            'recommend_mode': 'random',
            'message': msg,
        }

    if not persona_vector:
        packed = _pack_random('【随机推荐】未找到国风人设测试结果')
        packed['persona_source'] = persona_source
        packed['test_mode'] = bool(getattr(svc_config, 'IMAGERY_TEST_MODE', False))
        return packed

    user_attrs = _persona_vector_to_graph_attrs(persona_vector)

    try:
        nearest = _find_nearest_user_cluster(user_attrs)
        user_cluster = nearest.get('cluster') or ''
        if not user_cluster:
            packed = _pack_random(
                '【随机推荐】图中未找到任何 UserCluster',
                persona_vector,
            )
            packed['persona_source'] = persona_source
            packed['test_mode'] = bool(getattr(svc_config, 'IMAGERY_TEST_MODE', False))
            return packed
        liked_rows = _likes_songs_from_user_cluster(user_cluster, limit=NEED)
    except Exception as exc:
        packed = _pack_random(
            f'【随机推荐】图查询异常（{exc}）',
            persona_vector,
        )
        packed['persona_source'] = persona_source
        packed['test_mode'] = bool(getattr(svc_config, 'IMAGERY_TEST_MODE', False))
        return packed

    items: list[dict[str, Any]] = []
    seen: set[str] = set()
    likes_count = 0
    contains_count = 0
    liked_meta: list[dict[str, Any]] = []

    # 主路径：LIKES 热度
    for row in liked_rows:
        if len(items) >= NEED:
            break
        mid = str(row['music_id'])
        if mid in seen:
            continue
        seen.add(mid)
        info = _resolve_song_ref(mid)
        info['from_cluster'] = user_cluster
        info['from_music_cluster'] = ''
        info['like_count'] = int(row.get('like_count') or 0)
        info['recommend_source'] = 'likes'
        items.append(info)
        likes_count += 1
        liked_meta.append({'music_id': mid, 'like_count': info['like_count']})

    # 兜底 1：MAPS_TO → CONTAINS
    if len(items) < NEED:
        for row in _contains_songs_from_user_cluster(
            user_cluster, limit=NEED * 5, exclude=seen,
        ):
            if len(items) >= NEED:
                break
            mid = str(row['music_id'])
            seen.add(mid)
            info = _resolve_song_ref(mid)
            info['from_cluster'] = user_cluster
            info['from_music_cluster'] = str(row.get('music_cluster') or '')
            info['like_count'] = 0
            info['recommend_source'] = 'contains'
            items.append(info)
            contains_count += 1

    # 兜底 2：本地 MUSIC_CLUSTER_SONGS 配置表
    if len(items) < NEED:
        for mc_row in _maps_to_music_clusters(user_cluster, top_k=5):
            if len(items) >= NEED:
                break
            mc = str(mc_row.get('music_cluster') or '')
            for ref in _songs_from_music_cluster(mc):
                if len(items) >= NEED:
                    break
                key = str(ref)
                if key in seen:
                    continue
                seen.add(key)
                info = _resolve_song_ref(ref)
                info['from_cluster'] = user_cluster
                info['from_music_cluster'] = mc
                info['like_count'] = 0
                info['recommend_source'] = 'cluster_map'
                items.append(info)
                contains_count += 1

    # 兜底 3：随机
    random_count = 0
    need_random = NEED - len(items)
    if need_random > 0:
        for ref in _random_song_refs(need_random, exclude=seen):
            seen.add(str(ref))
            info = _resolve_song_ref(ref)
            info['from_cluster'] = user_cluster
            info['from_music_cluster'] = ''
            info['like_count'] = 0
            info['recommend_source'] = 'random'
            items.append(info)
            random_count += 1

    graph_hits = likes_count + contains_count
    if likes_count >= NEED:
        mode = 'likes'
        msg = (
            f'【LIKES 推荐】用户类别 {user_cluster}'
            f'（相似度 {nearest.get("similarity")}）'
            f'→ 热度 Top{likes_count}：'
            + ', '.join(f'{x["music_id"]}({x["like_count"]})' for x in liked_meta)
        )
    elif graph_hits > 0 and random_count > 0:
        mode = 'mixed'
        msg = (
            f'【混合推荐】用户类别 {user_cluster}（相似度 {nearest.get("similarity")}）'
            f'→ LIKES {likes_count} + CONTAINS/映射 {contains_count}'
            f' + 随机 {random_count}'
        )
    elif graph_hits > 0:
        mode = 'likes' if likes_count else 'contains'
        msg = (
            f'【图推荐】用户类别 {user_cluster}（相似度 {nearest.get("similarity")}）'
            f'→ LIKES {likes_count} + CONTAINS/映射 {contains_count}'
        )
    else:
        mode = 'random'
        msg = (
            f'【随机推荐】已匹配用户类别 {user_cluster}'
            f'（相似度 {nearest.get("similarity")}），'
            f'但无 LIKES/CONTAINS 歌曲，已随机抽取 {len(items)} 首'
        )

    if persona_source.startswith('test_persona:'):
        msg = f'【测试画像:{persona_source.split(":", 1)[1]}】{msg}'

    return {
        'source': 'personalization_recommend',
        'user_id': user_id,
        'persona_vector': persona_vector,
        'persona_source': persona_source,
        'test_mode': bool(getattr(svc_config, 'IMAGERY_TEST_MODE', False)),
        'graph_attrs': user_attrs,
        'matched_user_cluster': {
            'cluster': user_cluster,
            'similarity': nearest.get('similarity'),
            'cluster_attrs': nearest.get('cluster_attrs'),
        },
        'liked_music': liked_meta,
        'mapped_music_clusters': _maps_to_music_clusters(user_cluster, top_k=5),
        'recommend_mode': mode,
        'items': items[:NEED],
        'message': msg,
    }
