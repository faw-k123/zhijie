"""
API 视图层：识别前端来源请求，分发到四大业务模块。

约定：多数 POST 接口可带 source 字段便于日志识别；路径本身已区分业务。
具体业务逻辑在各独立 Django 应用的 services.py 中实现（当前多为占位）：
- data_display.services
- emotion_analysis.services
- propagation.services
- personalization.services
"""

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .translation import translate_texts
from django.db import connection

from data_display import services as data_display
from emotion_analysis import services as emotion_analysis
from propagation import services as propagation
from personalization import services as personalization
from imagery import services as imagery


# ========================= 内容展示模块（从b项目迁移） =========================

@api_view(['GET'])
def content_home_feed(request):
    keyword = (request.query_params.get('keyword') or '').strip()
    refresh = str(request.query_params.get('refresh') or '0') in ('1', 'true', 'True')
    data = data_display.query_home_feed(keyword=keyword, refresh=refresh)
    return Response({'success': True, 'data': data})


@api_view(['GET'])
def content_music_resource(request):
    song_id = (request.query_params.get('id') or '').strip()
    if not song_id:
        return Response({'success': False, 'message': 'id 必填'}, status=status.HTTP_400_BAD_REQUEST)
    data = data_display.query_music_resource(song_id)
    return Response({'success': True, 'data': data})


@api_view(['GET'])
def content_search_suggestions(request):
    keyword = (request.query_params.get('keyword') or '').strip()
    data = data_display.query_search_suggestions(keyword)
    return Response({'success': True, 'data': data})


# ========================= 歌曲意象解析模块 =========================

@api_view(['GET'])
def test_mode_options(request):
    """联调测试开关与下拉选项（文化圈层 / 音乐画像）。"""
    from config import services as svc_config
    return Response({'success': True, 'data': svc_config.get_test_ui_options()})


@api_view(['POST'])
def imagery_translate(request):
    """
    意象解析（缓冲池模式）：
    先查缓冲池，未命中则申请解析并写入，响应始终来自缓冲池内容。
    测试模式下可传 circle_override=auto|1~5。
    """
    song_id = (request.data.get('song_id') or '').strip()
    language = (request.data.get('language') or 'zh-CN').strip()
    user_id = (request.data.get('user_id') or request.data.get('username') or '').strip()
    circle_override = request.data.get('circle_override', None)
    if circle_override is None:
        circle_override = request.data.get('cultural_circle', None)
    if not song_id:
        return Response({'success': False, 'message': 'song_id 必填'}, status=status.HTTP_400_BAD_REQUEST)
    scene_tags = request.data.get('scene_tags')
    thing_tags = request.data.get('thing_tags')
    emotion_tags = request.data.get('emotion_tags')
    data = imagery.ensure_imagery_buffered(
        song_id=song_id,
        language=language,
        user_id=user_id,
        circle_override=circle_override,
        scene_tags=list(scene_tags) if isinstance(scene_tags, list) else None,
        thing_tags=list(thing_tags) if isinstance(thing_tags, list) else None,
        emotion_tags=list(emotion_tags) if isinstance(emotion_tags, list) else None,
    )
    return Response({'success': True, 'data': data})


# ========================= 认证（数据库存储：behave.Users） =========================

@api_view(['POST'])
def register(request):
    username = (request.data.get('username') or '').strip()
    password = request.data.get('password') or ''
    country = (request.data.get('country') or '').strip()
    if not username or not password:
        return Response({'success': False, 'message': '用户名和密码不能为空'}, status=status.HTTP_400_BAD_REQUEST)
    with connection.cursor() as cur:
        cur.execute("SELECT user_id FROM behave.Users WHERE username = %s", [username])
        if cur.fetchone():
            return Response({'success': False, 'message': '用户名已存在'}, status=status.HTTP_400_BAD_REQUEST)
        # 顺序自增 user_id（1, 2, 3, ...）
        cur.execute("SELECT MAX(TRY_CAST(user_id AS INT)) FROM behave.Users")
        max_id = cur.fetchone()[0]
        user_id = str((max_id or 0) + 1)
        cur.execute(
            "INSERT INTO behave.Users (user_id, username, password, country, register_date) "
            "VALUES (%s, %s, %s, %s, GETDATE())",
            [user_id, username, password, country],
        )
    return Response({'success': True, 'message': '注册成功', 'user_id': user_id, 'username': username, 'country': country})


@api_view(['POST'])
def login(request):
    username = (request.data.get('username') or '').strip()
    password = request.data.get('password') or ''
    country = (request.data.get('country') or '').strip()
    if not username or not password:
        return Response({'success': False, 'message': '用户名和密码不能为空'}, status=status.HTTP_400_BAD_REQUEST)
    with connection.cursor() as cur:
        cur.execute(
            "SELECT user_id FROM behave.Users WHERE username = %s AND password = %s",
            [username, password],
        )
        row = cur.fetchone()
        if not row:
            return Response({'success': False, 'message': '用户名或密码错误'}, status=status.HTTP_401_UNAUTHORIZED)
        # 登录时更新用户当前所在国家
        if country:
            cur.execute("UPDATE behave.Users SET country = %s WHERE user_id = %s", [country, row[0]])
    return Response({'success': True, 'message': '登录成功', 'user_id': row[0], 'username': username, 'country': country})


# ========================= 模块一：数据展示与问答 =========================

@api_view(['POST'])
def home_graph(request):
    """首页右下：大类+小类 → Neo4j 图谱展示模块。"""
    category = (request.data.get('category') or '').strip()
    subcategory = (request.data.get('subcategory') or '').strip()
    if not category or not subcategory:
        return Response({'success': False, 'message': 'category 与 subcategory 必填'}, status=status.HTTP_400_BAD_REQUEST)
    data = data_display.query_neo4j_graph(category, subcategory)
    return Response({'success': True, 'data': data})


@api_view(['POST'])
def home_qa(request):
    """首页左下：问题 → KG-RAG 问答模块。"""
    question = (request.data.get('question') or '').strip()
    if not question:
        return Response({'success': False, 'message': 'question 必填'}, status=status.HTTP_400_BAD_REQUEST)
    locale = (request.data.get('locale') or 'zh-CN').strip()
    data = data_display.ask_kg_rag(question, locale=locale)
    return Response({'success': True, 'data': data})


@api_view(['POST'])
def translate_batch(request):
    """批量翻译页面文字，为现有静态词典补齐硬编码和动态内容。"""
    locale = (request.data.get('locale') or '').strip()
    texts = request.data.get('texts') or []
    if not locale or not isinstance(texts, list):
        return Response(
            {'success': False, 'message': 'locale 与 texts 必填'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    try:
        data = translate_texts(texts, locale)
    except ValueError as exc:
        return Response({'success': False, 'message': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as exc:
        return Response(
            {'success': False, 'message': f'翻译服务暂时不可用：{exc}'},
            status=status.HTTP_502_BAD_GATEWAY,
        )
    return Response({'success': True, 'data': data})


@api_view(['GET'])
def music_show_bundle(request):
    """音乐展示页：按大类返回介绍+小类+歌曲列表等。"""
    category = (request.query_params.get('category') or '').strip()
    if not category:
        return Response({'success': False, 'message': 'category 必填'}, status=status.HTTP_400_BAD_REQUEST)
    data = data_display.query_category_show_bundle(category)
    return Response({'success': True, 'data': data})


@api_view(['GET'])
def emotion_subcategories(request):
    """情感分析半遮挡：按大类返回小类列表（网格）。默认民歌。"""
    category = (request.query_params.get('category') or '民歌').strip()
    data = data_display.query_subcategories_by_category(category)
    return Response({'success': True, 'data': data})


@api_view(['GET'])
def emotion_subcategory_songs(request):
    """情感分析：点击小类 → 歌曲列表 + 首曲资源包。"""
    category = (request.query_params.get('category') or '').strip()
    subcategory = (request.query_params.get('subcategory') or '').strip()
    if not category or not subcategory:
        return Response({'success': False, 'message': 'category 与 subcategory 必填'}, status=status.HTTP_400_BAD_REQUEST)
    data = data_display.query_subcategory_song_resources(category, subcategory)
    return Response({'success': True, 'data': data})


@api_view(['GET'])
def emotion_song_resources(request):
    """情感分析详情：切换下拉歌曲 → 该曲资源包。"""
    category = (request.query_params.get('category') or '').strip()
    subcategory = (request.query_params.get('subcategory') or '').strip()
    song_id = (request.query_params.get('song_id') or '').strip()
    song_title = (request.query_params.get('song_title') or '').strip()
    if not category or not subcategory or not song_id:
        return Response(
            {'success': False, 'message': 'category、subcategory、song_id 必填'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    data = data_display.query_song_resources(category, subcategory, song_id, song_title)
    return Response({'success': True, 'data': data})


@api_view(['GET'])
def global_song_comments(request):
    """全球传播效果：指定歌曲评论前 50 条。"""
    category = (request.query_params.get('category') or '').strip()
    subcategory = (request.query_params.get('subcategory') or '').strip()
    song_title = (request.query_params.get('song_title') or '').strip()
    if not category or not subcategory or not song_title:
        return Response(
            {'success': False, 'message': 'category、subcategory、song_title 必填'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    data = data_display.query_song_comments_top50(category, subcategory, song_title)
    return Response({'success': True, 'data': data})


@api_view(['GET'])
def music_taxonomy(request):
    """返回大类-小类-歌曲 JSON（全球传播效果下拉等使用）。"""
    data = data_display.get_music_taxonomy()
    return Response({'success': True, 'data': data})


@api_view(['GET'])
def song_wordcloud(request):
    """情感分析页面：按歌曲 ID 获取词云数据（ECharts wordcloud 标准格式）。"""
    song_id = (request.query_params.get('song_id') or '').strip()
    if not song_id:
        return Response({'success': False, 'message': 'song_id 必填'}, status=status.HTTP_400_BAD_REQUEST)
    data = data_display.get_wordcloud_by_songid(song_id)
    return Response({'success': True, 'data': data})


@api_view(['GET'])
def song_emotion_polarity(request):
    """情感分析页面：按歌曲 ID 获取评论情感极性统计。"""
    song_id = (request.query_params.get('song_id') or '').strip()
    if not song_id:
        return Response({'success': False, 'message': 'song_id 必填'}, status=status.HTTP_400_BAD_REQUEST)
    data = data_display.get_emotion_polarity(int(song_id))
    return Response({'success': True, 'data': data})


@api_view(['GET', 'PUT', 'POST'])
def user_profile(request):
    """个人界面：GET 查资料；PUT/POST 更新资料。"""
    username = (
        request.query_params.get('username')
        or request.data.get('username')
        or ''
    ).strip()
    if not username:
        return Response({'success': False, 'message': 'username 必填'}, status=status.HTTP_400_BAD_REQUEST)
    if request.method == 'GET':
        data = data_display.get_user_profile(username)
        return Response({'success': True, 'data': data})
    payload = {
        'nickname': request.data.get('nickname'),
        'email': request.data.get('email'),
        'bio': request.data.get('bio'),
        'password': request.data.get('password'),
    }
    data = data_display.update_user_profile(username, payload)
    return Response({'success': True, 'data': data})


# ========================= 模块二：情感分析 =========================

@api_view(['POST'])
def song_emotion_analysis(request):
    """详情页底部「情感分析」Tab：按歌曲调用情感分析模块。"""
    category = (request.data.get('category') or '').strip()
    subcategory = (request.data.get('subcategory') or '').strip()
    song_id = (request.data.get('song_id') or '').strip()
    song_title = (request.data.get('song_title') or '').strip()
    if not category or not subcategory or not song_id:
        return Response(
            {'success': False, 'message': 'category、subcategory、song_id 必填'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    data = emotion_analysis.analyze_song_emotion(category, subcategory, song_id, song_title)
    return Response({'success': True, 'data': data})


@api_view(['POST'])
def emotion_trend_prediction(request):
    """情感趋势预测：基于历史数据预测未来7天情感走势。"""
    song_id = (request.data.get('song_id') or '').strip()
    days = int(request.data.get('days') or 7)
    if not song_id:
        return Response({'success': False, 'message': 'song_id 必填'}, status=status.HTTP_400_BAD_REQUEST)
    data = emotion_analysis.predict_emotion_trend(int(song_id), days)
    return Response({'success': True, 'data': data})


@api_view(['POST'])
def emotion_causal_impact(request):
    """因果影响分析：分析特定事件对歌曲情感的影响（模拟CausalImpact）。"""
    song_id = (request.data.get('song_id') or '').strip()
    event_date = request.data.get('event_date')
    if not song_id:
        return Response({'success': False, 'message': 'song_id 必填'}, status=status.HTTP_400_BAD_REQUEST)
    data = emotion_analysis.analyze_causal_impact(int(song_id), event_date)
    return Response({'success': True, 'data': data})


# ========================= 模块三：传播分析与宣传报告 =========================

@api_view(['POST'])
def global_propagation_analysis(request):
    """全球传播效果：选好歌曲后请求传播数据 + 异常/预测。"""
    category = (request.data.get('category') or '').strip()
    subcategory = (request.data.get('subcategory') or '').strip()
    song_title = (request.data.get('song_title') or '').strip()
    if not category or not subcategory or not song_title:
        return Response(
            {'success': False, 'message': 'category、subcategory、song_title 必填'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    data = propagation.analyze_and_predict(category, subcategory, song_title)
    return Response({'success': True, 'data': data})


@api_view(['POST'])
def song_ai_report(request):
    """详情页底部「AI报告生成」：按歌曲生成 AI 分析报告。"""
    category = (request.data.get('category') or '').strip()
    subcategory = (request.data.get('subcategory') or '').strip()
    song_id = (request.data.get('song_id') or '').strip()
    song_title = (request.data.get('song_title') or '').strip()
    if not category or not subcategory or not song_id:
        return Response(
            {'success': False, 'message': 'category、subcategory、song_id 必填'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    data = propagation.generate_ai_report(category, subcategory, song_id, song_title)
    return Response({'success': True, 'data': data})


@api_view(['POST'])
def promo_report(request):
    """宣传报告生成页提交。"""
    theme = (request.data.get('theme') or '').strip()
    platform = (request.data.get('platform') or '').strip()
    audience = (request.data.get('audience') or '').strip()
    core_text = (request.data.get('core_text') or '').strip()
    if not theme or not platform or not audience or not core_text:
        return Response({'success': False, 'message': 'theme/platform/audience/core_text 必填'}, status=status.HTTP_400_BAD_REQUEST)
    data = propagation.generate_promo_report(theme, platform, audience, core_text)
    return Response({'success': True, 'data': data})


# ========================= 模块四：个性化与互动 =========================

@api_view(['GET'])
def personality_questions(request):
    """人格测试：获取大五人格题库（20题）。"""
    data = personalization.get_questions()
    return Response({'success': True, 'data': data})


@api_view(['POST'])
def personality_submit(request):
    """人格测试提交 → 评分 + 画像 + 推荐。"""
    user_id = (request.data.get('user_id') or '').strip() or 'guest'
    answers = request.data.get('answers') or []
    if not isinstance(answers, list) or not answers:
        return Response({'success': False, 'message': 'answers 必填'}, status=status.HTTP_400_BAD_REQUEST)
    data = personalization.evaluate_personality(user_id, answers)
    return Response({'success': True, 'data': data})


@api_view(['GET'])
def personality_profile(request):
    """获取用户人格画像。"""
    user_id = (request.query_params.get('user_id') or '').strip() or 'guest'
    data = personalization.get_profile(user_id)
    return Response({'success': True, 'data': data})


@api_view(['POST'])
def cultural_circle_submit(request):
    """文化圈层测试提交 → 七维得分 + 文化圈层匹配 + 保存到数据库。"""
    user_id = (request.data.get('user_id') or '').strip()
    answers = request.data.get('answers') or {}
    if not user_id:
        return Response({'success': False, 'message': 'user_id 必填'}, status=status.HTTP_400_BAD_REQUEST)
    if not isinstance(answers, dict) or not answers:
        return Response({'success': False, 'message': 'answers 必填'}, status=status.HTTP_400_BAD_REQUEST)
    
    user_vector = personalization.calculate_cultural_circle_vector(answers)
    matched_circles = personalization.match_cultural_circles(user_vector, 5)
    
    save_result = personalization.save_cultural_circle_test(user_id, answers, user_vector, matched_circles)
    
    return Response({
        'success': True,
        'data': {
            'user_vector': user_vector,
            'matched_circles': matched_circles,
            'save_result': save_result,
        },
    })


@api_view(['GET'])
def cultural_circle_profile(request):
    """获取用户最新的文化圈层测试结果。"""
    user_id = (request.query_params.get('user_id') or '').strip()
    if not user_id:
        return Response({'success': False, 'message': 'user_id 必填'}, status=status.HTTP_400_BAD_REQUEST)
    data = personalization.get_cultural_circle_test(user_id)
    return Response({'success': True, 'data': data})


@api_view(['POST'])
def guess_like(request):
    """猜你喜欢：提交当前用户信息 → 个性化推荐。"""
    user_id = (request.data.get('user_id') or '').strip()
    if not user_id:
        return Response({'success': False, 'message': 'user_id 必填'}, status=status.HTTP_400_BAD_REQUEST)
    data = personalization.recommend_songs(user_id)
    return Response({'success': True, 'data': data})


@api_view(['POST'])
def listen_record(request):
    """听歌行为记录（个性化数据沉淀）。"""
    user_id = (request.data.get('user_id') or '').strip()
    song = request.data.get('song') or {}
    if not user_id or not song:
        return Response({'success': False, 'message': 'user_id 与 song 必填'}, status=status.HTTP_400_BAD_REQUEST)
    data = personalization.record_listen(user_id, song)
    return Response({'success': True, 'data': data})


@api_view(['POST'])
def ai_generate_music(request):
    """AI 生成国风音乐：提交 Suno 任务并返回 task_id，前端轮询获取结果。"""
    user_id = (request.data.get('user_id') or '').strip()
    form = request.data.get('form') or {}
    if not user_id:
        return Response({'success': False, 'message': 'user_id 必填'}, status=status.HTTP_400_BAD_REQUEST)
    data = personalization.generate_guofeng_music(user_id, form)
    return Response({'success': True, 'data': data})


@api_view(['POST'])
def ai_generate_lyrics(request):
    """AI 生成国风歌词（调用豆包）。"""
    username = (request.data.get('username') or '').strip()
    style = (request.data.get('style') or '').strip()
    mood = (request.data.get('mood') or '').strip()
    theme = (request.data.get('theme') or '').strip()
    keywords = (request.data.get('keywords') or '').strip()

    if not username:
        return Response({'success': False, 'message': 'username 必填'}, status=status.HTTP_400_BAD_REQUEST)
    if not style:
        return Response({'success': False, 'message': 'style 必填'}, status=status.HTTP_400_BAD_REQUEST)
    if not mood:
        return Response({'success': False, 'message': 'mood 必填'}, status=status.HTTP_400_BAD_REQUEST)

    data = personalization.generate_lyrics_by_doubao(style, mood, theme, keywords)
    return Response({'success': True, 'data': data})


@api_view(['GET'])
def ai_music_status(request):
    """查询 AI 音乐生成任务状态。"""
    task_id = (request.GET.get('task_id') or '').strip()
    if not task_id:
        return Response({'success': False, 'message': 'task_id 必填'}, status=status.HTTP_400_BAD_REQUEST)
    data = personalization.fetch_music_task(task_id)
    return Response({'success': True, 'data': data})


# ========================= 模块五：视频配乐 =========================

@api_view(['POST'])
def video_bgm_analyze(request):
    """上传视频截图 → AI分析 → 推荐音乐 → 生成理由"""
    image_data = request.data.get('image')
    if not image_data:
        return Response({'success': False, 'message': '请上传视频截图'}, status=status.HTTP_400_BAD_REQUEST)
    from video_bgm_services import analyze_video_frame, recommend_music, generate_reason
    analysis = analyze_video_frame(image_data)
    recommendations = recommend_music(analysis)
    reason = generate_reason(analysis, recommendations)
    return Response({
        'success': True,
        'analysis': analysis,
        'recommendations': recommendations,
        'reason': reason,
    })

# ============================================================
# 【新增】加入 api/views.py
# 建议插入位置：紧跟在 cultural_circle_profile 函数之后
# （即模块四"个性化与互动"分组内，与文化圈层测试相邻）
# ============================================================

@api_view(['GET'])
def guofeng_persona_questions(request):
    """国风人设测试：获取题库（15题）。"""
    data = personalization.get_guofeng_questions()
    return Response({'success': True, 'data': data})


@api_view(['POST'])
def guofeng_persona_submit(request):
    """国风人设测试提交 → 标签打分 + 六维向量 + 人设匹配 + 保存到数据库。"""
    user_id = (request.data.get('user_id') or '').strip()
    answers = request.data.get('answers') or {}
    if not user_id:
        return Response({'success': False, 'message': 'user_id 必填'}, status=status.HTTP_400_BAD_REQUEST)
    if not isinstance(answers, dict) or not answers:
        return Response({'success': False, 'message': 'answers 必填'}, status=status.HTTP_400_BAD_REQUEST)

    tag_scores = personalization.calculate_guofeng_tag_scores(answers)
    user_vector = personalization.calculate_guofeng_persona_vector(tag_scores)
    matched_personas = personalization.match_guofeng_personas(user_vector, 3)

    save_result = personalization.save_guofeng_persona_test(
        user_id, answers, tag_scores, user_vector, matched_personas
    )

    return Response({
        'success': True,
        'data': {
            'tag_scores': tag_scores,
            'user_vector': user_vector,
            'matched_personas': matched_personas,
            'save_result': save_result,
        },
    })


@api_view(['GET'])
def guofeng_persona_profile(request):
    """获取用户最新的国风人设测试结果。"""
    user_id = (request.query_params.get('user_id') or '').strip()
    if not user_id:
        return Response({'success': False, 'message': 'user_id 必填'}, status=status.HTTP_400_BAD_REQUEST)
    data = personalization.get_guofeng_persona_test(user_id)
    return Response({'success': True, 'data': data})


# ========================= 收藏夹功能 =========================
# 服务实现见 personalization.services（get_favorite_folders 等）；
# 这里只做参数透传与 HTTP 包装。前端用 user_id 标识用户。


@api_view(['POST'])
def personal_recommend(request):
    """私人空间 · 基于用户人设的推荐曲目（NEO4J_3 图查询）。"""
    user_id = (request.data.get('user_id') or request.data.get('username') or '').strip()
    if not user_id:
        return Response({'success': False, 'message': 'user_id 必填'}, status=status.HTTP_400_BAD_REQUEST)
    persona_override = (
        request.data.get('persona_override')
        or request.data.get('music_persona')
        or request.data.get('music_persona_override')
        or ''
    )
    circle_override = (
        request.data.get('circle_override')
        or request.data.get('cultural_circle')
        or ''
    )
    data = personalization.recommend_by_persona(
        user_id,
        persona_override=str(persona_override).strip() or None,
        circle_override=str(circle_override).strip() or None,
    )
    return Response({'success': True, 'data': data})


@api_view(['POST'])
def personal_similar(request):
    """单曲页相似推荐：本地资源按意象标签，数据库曲目按同一小类。"""
    song_id = (request.data.get('song_id') or '').strip()
    if not song_id:
        return Response({'success': False, 'message': 'song_id 必填'}, status=status.HTTP_400_BAD_REQUEST)
    data = personalization.get_similar_songs(song_id)
    return Response({'success': True, 'data': data})


@api_view(['POST'])
def personal_reaction(request):
    """兼容旧版单曲页反馈接口。"""
    user_id = (request.data.get('user_id') or request.data.get('username') or '').strip()
    song_id = (request.data.get('song_id') or '').strip()
    reaction = (request.data.get('reaction') or 'like').strip()
    if not user_id or not song_id:
        return Response({'success': False, 'message': 'user_id 与 song_id 必填'}, status=status.HTTP_400_BAD_REQUEST)
    reaction_type = 'dislike' if reaction in ('cry', 'dislike') else 'like'
    data = personalization.toggle_song_like(user_id, song_id, reaction_type)
    return Response({'success': data.get('success', True), 'data': data, 'message': data.get('message', '')})


@api_view(['GET'])
def favorite_folders(request):
    """获取用户收藏夹列表（无则自动创建默认收藏夹）。"""
    user_id = (request.query_params.get('user_id') or '').strip()
    if not user_id:
        return Response({'success': False, 'message': 'user_id 必填'}, status=status.HTTP_400_BAD_REQUEST)
    data = personalization.get_favorite_folders(user_id)
    return Response(data)


@api_view(['GET'])
def favorite_folder_songs(request):
    """获取指定收藏夹内的歌曲列表。"""
    user_id = (request.query_params.get('user_id') or '').strip()
    folder_id = (request.query_params.get('folder_id') or '').strip()
    if not user_id or not folder_id:
        return Response({'success': False, 'message': 'user_id 与 folder_id 必填'}, status=status.HTTP_400_BAD_REQUEST)
    data = personalization.get_folder_songs(user_id, folder_id)
    return Response(data)

@api_view(['POST'])
def favorite_folder_create(request):
    """创建新收藏夹。"""
    user_id = (request.data.get('user_id') or '').strip()
    name = (request.data.get('name') or '').strip()
    if not user_id or not name:
        return Response({'success': False, 'message': 'user_id 与 name 必填'}, status=status.HTTP_400_BAD_REQUEST)
    data = personalization.create_favorite_folder(user_id, name)
    return Response(data)


@api_view(['DELETE'])
def favorite_folder_delete(request):
    """删除收藏夹（默认收藏夹不可删）。"""
    user_id = (request.query_params.get('user_id') or '').strip()
    folder_id = (request.query_params.get('folder_id') or '').strip()
    if not user_id or not folder_id:
        return Response({'success': False, 'message': 'user_id 与 folder_id 必填'}, status=status.HTTP_400_BAD_REQUEST)
    data = personalization.delete_favorite_folder(user_id, folder_id)
    return Response(data)


@api_view(['POST'])
def favorite_save(request):
    """将歌曲保存到指定收藏夹。"""
    user_id = (request.data.get('user_id') or '').strip()
    song_id = (request.data.get('song_id') or '').strip()
    folder_id = (request.data.get('folder_id') or '').strip()
    if not user_id or not song_id or not folder_id:
        return Response({'success': False, 'message': 'user_id、song_id、folder_id 必填'}, status=status.HTTP_400_BAD_REQUEST)
    data = personalization.save_to_favorite(user_id, song_id, folder_id)
    return Response(data)


@api_view(['DELETE'])
def favorite_song_remove(request):
    """从收藏夹中移除歌曲。"""
    user_id = (request.query_params.get('user_id') or '').strip()
    folder_id = (request.query_params.get('folder_id') or '').strip()
    song_id = (request.query_params.get('song_id') or '').strip()
    if not user_id or not folder_id or not song_id:
        return Response({'success': False, 'message': 'user_id、folder_id、song_id 必填'}, status=status.HTTP_400_BAD_REQUEST)
    data = personalization.delete_favorite_song(user_id, folder_id, song_id)
    return Response(data)


@api_view(['GET'])
def favorite_status(request):
    """查询歌曲是否已被用户收藏。"""
    user_id = (request.query_params.get('user_id') or '').strip()
    song_id = (request.query_params.get('song_id') or '').strip()
    if not user_id or not song_id:
        return Response({'success': False, 'message': 'user_id 与 song_id 必填'}, status=status.HTTP_400_BAD_REQUEST)
    data = personalization.get_favorite_status(user_id, song_id)
    return Response(data)


# ========================= 歌曲喜欢 / 我喜欢的 =========================

@api_view(['POST'])
def song_like_toggle(request):
    """切换歌曲喜欢/不喜欢状态。"""
    user_id = (request.data.get('user_id') or request.data.get('username') or '').strip()
    song_id = (request.data.get('song_id') or '').strip()
    reaction_type = (request.data.get('reaction_type') or 'like').strip()
    if not user_id or not song_id:
        return Response({'success': False, 'message': 'user_id 与 song_id 必填'}, status=status.HTTP_400_BAD_REQUEST)
    data = personalization.toggle_song_like(user_id, song_id, reaction_type)
    return Response(data)


@api_view(['GET'])
def song_like_status(request):
    """查询歌曲喜欢/不喜欢状态。"""
    user_id = (request.query_params.get('user_id') or '').strip()
    song_id = (request.query_params.get('song_id') or '').strip()
    if not user_id or not song_id:
        return Response({'success': False, 'message': 'user_id 与 song_id 必填'}, status=status.HTTP_400_BAD_REQUEST)
    data = personalization.get_song_like_status(user_id, song_id)
    return Response({'success': True, 'data': data})


@api_view(['GET'])
def liked_songs(request):
    """获取用户喜欢的歌曲列表。"""
    user_id = (request.query_params.get('user_id') or '').strip()
    if not user_id:
        return Response({'success': False, 'message': 'user_id 必填'}, status=status.HTTP_400_BAD_REQUEST)
    data = personalization.get_user_liked_songs(user_id)
    return Response(data)


@api_view(['POST'])
def speech_recognize(request):
    """语音识别占位接口（前端当前使用 vosk-browser 在浏览器端识别）。"""
    return Response({'success': False, 'message': '语音识别服务未启用'}, status=status.HTTP_501_NOT_IMPLEMENTED)






