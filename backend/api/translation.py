from __future__ import annotations

import json
import logging
import re
import threading
from pathlib import Path
from typing import Any

import requests

from config import services as svc_config


LANGUAGE_NAMES = {
    'zh-TW': '繁體中文',
    'en': 'English',
    'ru': 'Russian',
    'th': 'Thai',
    'ko': 'Korean',
    'ja': 'Japanese',
}

_CACHE_PATH = Path(__file__).resolve().parent.parent / 'data' / 'translation_cache.json'


def _load_cache() -> dict[tuple[str, str], str]:
    try:
        payload = json.loads(_CACHE_PATH.read_text(encoding='utf-8'))
        return {
            (locale, source): str(target)
            for locale, entries in payload.items()
            if isinstance(entries, dict)
            for source, target in entries.items()
        }
    except (OSError, ValueError, TypeError):
        return {}


_CACHE: dict[tuple[str, str], str] = _load_cache()
_CACHE_LOCK = threading.Lock()
logger = logging.getLogger(__name__)


def _save_cache() -> None:
    payload: dict[str, dict[str, str]] = {}
    for (locale, source), target in _CACHE.items():
        payload.setdefault(locale, {})[source] = target
    try:
        _CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        temporary = _CACHE_PATH.with_suffix('.tmp')
        temporary.write_text(json.dumps(payload, ensure_ascii=False), encoding='utf-8')
        temporary.replace(_CACHE_PATH)
    except OSError as exc:
        logger.warning('Could not persist translation cache: %s', exc)


def _parse_translations(content: str, sources: list[str]) -> list[str]:
    cleaned = content.strip()
    cleaned = re.sub(r'^```(?:json)?\s*', '', cleaned, flags=re.I)
    cleaned = re.sub(r'\s*```$', '', cleaned)
    try:
        payload: Any = json.loads(cleaned)
    except json.JSONDecodeError:
        start = cleaned.find('{')
        end = cleaned.rfind('}')
        if start < 0 or end <= start:
            raise
        payload = json.loads(cleaned[start:end + 1])

    values = payload.get('translations') if isinstance(payload, dict) else payload
    if not isinstance(values, list) or not values:
        raise ValueError('翻译结果格式无效')
    translated = [str(value) for value in values[:len(sources)]]
    if len(translated) < len(sources):
        translated.extend(sources[len(translated):])
    return translated


def _translate_chunk(texts: list[str], locale: str) -> list[str]:
    llm = svc_config.LLM
    if not llm.get('API_KEY'):
        raise RuntimeError('LLM_API_KEY 未配置')

    target_language = LANGUAGE_NAMES[locale]
    system_prompt = (
        f'你是中国传统音乐网站的专业本地化译者。将输入翻译为{target_language}。'
        '保留数字、百分比、日期、专有名词、书名号内的曲名和原有标点。'
        '文案要简洁自然，适合网页界面。不得增删信息。'
        '只返回 JSON 对象，格式为 {"translations":["..."]}，顺序和数量必须与输入一致。'
    )
    response = requests.post(
        f"{llm['BASE_URL'].rstrip('/')}/chat/completions",
        headers={
            'Authorization': f"Bearer {llm['API_KEY']}",
            'Content-Type': 'application/json',
        },
        json={
            'model': llm['MODEL'],
            'messages': [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': json.dumps(texts, ensure_ascii=False)},
            ],
            'temperature': 0.1,
            'response_format': {'type': 'json_object'},
        },
        timeout=llm.get('TIMEOUT_SECONDS', 60),
    )
    response.raise_for_status()
    content = response.json()['choices'][0]['message']['content']
    return _parse_translations(content, texts)


def _translate_resilient(texts: list[str], locale: str) -> tuple[list[str], int]:
    """Translate a batch without allowing one malformed model reply to fail the page."""
    for attempt in range(2):
        try:
            return _translate_chunk(texts, locale), 0
        except Exception as exc:
            logger.warning(
                'Translation attempt %s failed for %s item(s): %s',
                attempt + 1,
                len(texts),
                exc,
            )
    # Keep sources in their original positions. The browser retries only these items.
    return texts, len(texts)


def translate_texts(texts: list[str], locale: str) -> dict[str, Any]:
    if locale == 'zh-CN':
        return {'locale': locale, 'translations': texts, 'translated': True, 'cached': len(texts)}
    if locale not in LANGUAGE_NAMES:
        raise ValueError('不支持的目标语言')

    normalized = [str(text).strip()[:4000] for text in texts[:120]]
    results: list[str | None] = [None] * len(normalized)
    missing_by_text: dict[str, list[int]] = {}
    cached_count = 0

    with _CACHE_LOCK:
        for index, text in enumerate(normalized):
            cached = _CACHE.get((locale, text))
            if cached is not None:
                results[index] = cached
                cached_count += 1
            else:
                missing_by_text.setdefault(text, []).append(index)

    missing_texts = list(missing_by_text)
    failed_count = 0
    for start in range(0, len(missing_texts), 30):
        chunk = missing_texts[start:start + 30]
        translated, chunk_failed = _translate_resilient(chunk, locale)
        failed_count += chunk_failed
        with _CACHE_LOCK:
            for source, target in zip(chunk, translated):
                if source != target:
                    _CACHE[(locale, source)] = target
                for index in missing_by_text[source]:
                    results[index] = target
            if any(source != target for source, target in zip(chunk, translated)):
                _save_cache()

    return {
        'locale': locale,
        'translations': [value if value is not None else normalized[index] for index, value in enumerate(results)],
        'translated': failed_count == 0,
        'cached': cached_count,
        'failed': failed_count,
    }
