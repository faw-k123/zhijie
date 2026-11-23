"""
传播分析与宣传报告生成模块（Django 应用：propagation）

HTTP 路由仍由 api.views / api.urls 统一对外暴露；
本应用只承载业务实现，请在本文件（services.py）中继续完善具体逻辑。

待实现能力：
1. 全球传播效果页：传播数据分析 + 传播异常/预测分析
2. 详情页 AI 报告生成：按歌曲调用 AI 分析模块生成报告
3. 宣传报告生成页：按主题/平台/人群/核心表达调用文生模型
"""

from __future__ import annotations

from typing import Any

from config import services as svc_config


_CHINA_COUNTRY_ALIASES = {
    'cn', 'chn', 'china', 'mainland china', "people's republic of china",
    'pr china', 'prc', '中国', '中国大陆', '中华人民共和国', '大陆',
}


def _is_china_country(country: str) -> bool:
    normalized = ' '.join(str(country or '').strip().lower().split())
    return normalized in _CHINA_COUNTRY_ALIASES or normalized.startswith('中国')


def _country_sentiment_ranking(song_id: str, limit: int = 8) -> list[dict[str, Any]]:
    """Aggregate overseas comment sentiment by country; China is excluded by design."""
    from django.db import connection

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT country, polarity, sentiment_score
                FROM dbo.comment
                WHERE song_id = %s
                  AND country IS NOT NULL
                  AND LTRIM(RTRIM(country)) <> ''
                """,
                [song_id],
            )
            rows = cursor.fetchall()
    except Exception:
        return []

    grouped: dict[str, dict[str, Any]] = {}
    for raw_country, raw_polarity, raw_score in rows:
        country = str(raw_country or '').strip()
        if not country or _is_china_country(country):
            continue

        item = grouped.setdefault(
            country,
            {'country': country, 'sample_count': 0, 'positive_count': 0, 'negative_count': 0},
        )
        item['sample_count'] += 1
        polarity = str(raw_polarity or '').strip().lower()
        if polarity in {'积极', '正面', 'positive', '1'}:
            item['positive_count'] += 1
        elif polarity in {'消极', '负面', 'negative', '-1'}:
            item['negative_count'] += 1
        elif raw_score is not None:
            try:
                score = float(raw_score)
                if score > 0.1:
                    item['positive_count'] += 1
                elif score < -0.1:
                    item['negative_count'] += 1
            except (TypeError, ValueError):
                pass

    ranking = []
    for item in grouped.values():
        total = item['sample_count']
        positive_rate = item['positive_count'] / total if total else 0
        negative_rate = item['negative_count'] / total if total else 0
        ranking.append({
            'country': item['country'],
            'sample_count': total,
            'positive_rate': round(positive_rate, 4),
            'negative_rate': round(negative_rate, 4),
            'emotion_index': round(positive_rate - negative_rate, 4),
        })

    ranking.sort(key=lambda item: (-item['emotion_index'], -item['sample_count'], item['country']))
    return [dict(item, rank=index + 1) for index, item in enumerate(ranking[:limit])]


def analyze_and_predict(category: str, subcategory: str, song_title: str) -> dict[str, Any]:
    """
    待实现：调用传播分析与预测服务（config.services.PROPAGATION_MODEL）。

    返回拆成两块，供全球传播效果页右上 / 右下分别渲染：
    - spread_analysis：传播数据分析
    - anomaly_prediction：传播异常分析 / 预测
    """
    _ = svc_config.PROPAGATION_MODEL
    # TODO: 请求 PROPAGATION_MODEL['ENDPOINT']，解析指标与异常点
    return {
        'source': 'propagation_analyze_placeholder',
        'category': category,
        'subcategory': subcategory,
        'song_title': song_title,
        'spread_analysis': {
            'title': '传播数据分析（占位）',
            'metrics': {
                'play_count': 0,
                'share_count': 0,
                'comment_count': 0,
                'regions': [],
            },
            'text': f'【占位】「{song_title}」传播数据待接入传播分析服务。',
        },
        'anomaly_prediction': {
            'title': '传播异常分析（占位）',
            'alerts': [],
            'forecast': [],
            'text': f'【占位】「{song_title}」异常与预测待接入。',
        },
        'message': '待实现：传播分析与预测模块',
    }


def generate_ai_report(category: str, subcategory: str, song_id: str, song_title: str = '') -> dict[str, Any]:
    """根据真实评论情感统计生成可解释的 AI 传播分析报告。"""
    from emotion_analysis.services import analyze_song_emotion

    title = song_title or song_id
    try:
        emotion = analyze_song_emotion(category, subcategory, song_id, title)
    except Exception:
        emotion = {
            'summary': f'「{title}」暂无完整情感时序数据。',
            'trend': '待观察',
            'scores': {'积极': 0, '中性': 0, '消极': 0},
            'overall_stats': {
                'total_comments': 0,
                'positive_count': 0,
                'neutral_count': 0,
                'negative_count': 0,
                'positive_rate': 0,
                'negative_rate': 0,
                'emotion_index': 0,
            },
            'chart_data': {
                'dates': [], 'emotion_indices': [], 'positive_rates': [],
                'negative_rates': [], 'total_counts': [],
            },
        }

    stats = emotion['overall_stats']
    fallback_report = (
        f'「{title}」当前共纳入 {stats["total_comments"]} 条评论，'
        f'整体情感指数为 {stats["emotion_index"]:.2f}，'
        f'正面评论占比 {stats["positive_rate"] * 100:.1f}%，'
        f'近期趋势为「{emotion["trend"]}」。\n\n'
        '传播建议：优先强化歌曲的地域文化背景和代表性乐器解读，'
        '针对海外用户增加多语种字幕、意象译析与短视频版本，'
        '并持续追踪不同国家的情感反馈差异。'
    )

    llm = svc_config.LLM
    report = fallback_report
    used_llm = False
    if llm.get('API_KEY'):
        prompt = (
            f'曲目：{title}\n分类：{category} / {subcategory}\n'
            f'评论总数：{stats["total_comments"]}\n'
            f'情感指数：{stats["emotion_index"]:.4f}\n'
            f'正面率：{stats["positive_rate"]:.4f}\n'
            f'负面率：{stats["negative_rate"]:.4f}\n'
            f'近期趋势：{emotion["trend"]}\n'
            f'统计摘要：{emotion["summary"]}\n\n'
            '请生成一份精炼的国际传播效果 AI 研判。包含：'
            '1. 整体判断；2. 情感结构解读；3. 潜在海外受众；'
            '4. 两到三条可执行的传播建议。严格基于给定数据，不编造国家排名或平台数据。'
        )
        try:
            response = requests.post(
                f"{llm['BASE_URL'].rstrip('/')}/chat/completions",
                headers={
                    'Authorization': f"Bearer {llm['API_KEY']}",
                    'Content-Type': 'application/json',
                },
                json={
                    'model': llm['MODEL'],
                    'messages': [
                        {
                            'role': 'system',
                            'content': '你是中国传统音乐国际传播数据分析师，输出专业、准确、可执行的中文分析。',
                        },
                        {'role': 'user', 'content': prompt},
                    ],
                    'temperature': 0.35,
                },
                timeout=llm.get('TIMEOUT_SECONDS', 60),
            )
            response.raise_for_status()
            report = response.json()['choices'][0]['message']['content'].strip()
            used_llm = True
        except Exception:
            report = fallback_report

    return {
        'source': 'emotion_ai_report',
        'category': category,
        'subcategory': subcategory,
        'song_id': song_id,
        'song_title': title,
        'report': report,
        'used_llm': used_llm,
        'summary': emotion['summary'],
        'trend': emotion['trend'],
        'scores': emotion['scores'],
        'overall_stats': stats,
        'chart_data': emotion['chart_data'],
        'country_ranking': _country_sentiment_ranking(song_id),
        'message': 'AI 分析报告生成完成',
    }


import requests


def generate_promo_report(
    theme: str,
    platform: str,
    audience: str,
    core_text: str,
) -> dict[str, Any]:
    """
    调用豆包（火山方舟，OpenAI兼容接口）生成宣传文案。
    """
    llm = svc_config.LLM

    system_prompt = "你是一名资深新媒体文案策划，擅长根据主题、平台和目标人群写出有吸引力的宣传文案。"
    user_prompt = (
        f"主题：{theme}\n"
        f"发布平台：{platform}\n"
        f"目标人群：{audience}\n"
        f"需要重点表达的核心内容：{core_text}\n\n"
        f"请直接输出文案正文，不要输出多余说明，语气要贴合该平台调性。"
    )

    try:
        resp = requests.post(
            f"{llm['BASE_URL']}/chat/completions",
            headers={
                "Authorization": f"Bearer {llm['API_KEY']}",
                "Content-Type": "application/json",
            },
            json={
                "model": llm['MODEL'],
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            },
            timeout=llm.get('TIMEOUT_SECONDS', 60),
        )
        resp.raise_for_status()
        result = resp.json()
        content = result['choices'][0]['message']['content']
    except Exception as e:
        content = f"【生成失败】调用AI接口出错：{e}"

    return {
        'source': 'promo_report_doubao',
        'theme': theme,
        'platform': platform,
        'audience': audience,
        'core_text': core_text,
        'content': content,
        'message': '宣传报告生成成功' if not content.startswith('【生成失败】') else '宣传报告生成失败',
    }
