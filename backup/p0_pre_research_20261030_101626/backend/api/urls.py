from django.urls import path
from . import views

urlpatterns = [
    # 认证
    path('register/', views.register, name='register'),
    path('login/', views.login, name='login'),

    # 内容展示模块（从b项目迁移）
    path('content/home-feed/', views.content_home_feed, name='content_home_feed'),
    path('content/music-resource/', views.content_music_resource, name='content_music_resource'),
    path('content/search-suggestions/', views.content_search_suggestions, name='content_search_suggestions'),

    # 联调测试开关 / 下拉选项
    path('test/options/', views.test_mode_options, name='test_mode_options'),

    # 歌曲意象解析模块（缓冲池模式）
    path('imagery/translate/', views.imagery_translate, name='imagery_translate'),

    # 模块一：多维度数据展示与问答
    path('home/graph/', views.home_graph, name='home_graph'),
    path('home/qa/', views.home_qa, name='home_qa'),
    path('i18n/translate/', views.translate_batch, name='translate_batch'),
    path('music-show/', views.music_show_bundle, name='music_show_bundle'),
    path('emotion/subcategories/', views.emotion_subcategories, name='emotion_subcategories'),
    path('emotion/subcategory-songs/', views.emotion_subcategory_songs, name='emotion_subcategory_songs'),
    path('emotion/song-resources/', views.emotion_song_resources, name='emotion_song_resources'),
    path('global/comments/', views.global_song_comments, name='global_song_comments'),
    path('music/taxonomy/', views.music_taxonomy, name='music_taxonomy'),
    path('music/wordcloud/', views.song_wordcloud, name='song_wordcloud'),
    path('music/emotion-polarity/', views.song_emotion_polarity, name='song_emotion_polarity'),
    path('user/profile/', views.user_profile, name='user_profile'),

    # 模块二：情感分析
    path('emotion/analyze/', views.song_emotion_analysis, name='song_emotion_analysis'),
    path('emotion/trend-prediction/', views.emotion_trend_prediction, name='emotion_trend_prediction'),
    path('emotion/causal-impact/', views.emotion_causal_impact, name='emotion_causal_impact'),

    # 模块三：传播分析与宣传报告
    path('global/propagation/', views.global_propagation_analysis, name='global_propagation_analysis'),
    path('emotion/ai-report/', views.song_ai_report, name='song_ai_report'),
    path('promo/report/', views.promo_report, name='promo_report'),

    # 模块四：个性化与互动
    path('fun/questions/', views.personality_questions, name='personality_questions'),
    path('fun/personality/', views.personality_submit, name='personality_submit'),
    path('fun/profile/', views.personality_profile, name='personality_profile'),
    path('fun/cultural-circle/submit/', views.cultural_circle_submit, name='cultural_circle_submit'),
    path('fun/cultural-circle/profile/', views.cultural_circle_profile, name='cultural_circle_profile'),
    path('fun/guess-like/', views.guess_like, name='guess_like'),
    path('fun/listen/', views.listen_record, name='listen_record'),
    path('fun/ai-music/', views.ai_generate_music, name='ai_generate_music'),
 
    # 模块五：视频配乐
    path('video-bgm/analyze/', views.video_bgm_analyze, name='video_bgm_analyze'),
    path('fun/ai-music/status/', views.ai_music_status, name='ai_music_status'),
    path('fun/ai-lyrics/', views.ai_generate_lyrics, name='ai_generate_lyrics'),

    # 国风人设测试
    path('fun/guofeng-persona/questions/', views.guofeng_persona_questions, name='guofeng_persona_questions'),
    path('fun/guofeng-persona/submit/', views.guofeng_persona_submit, name='guofeng_persona_submit'),
    path('fun/guofeng-persona/profile/', views.guofeng_persona_profile, name='guofeng_persona_profile'),

    # 个性化推荐（基于人设 · NEO4J_3）
    path('personal/recommend/', views.personal_recommend, name='personal_recommend'),
    path('personal/similar/', views.personal_similar, name='personal_similar'),
    path('personal/reaction/', views.personal_reaction, name='personal_reaction'),

    # 收藏夹
    path('personal/favorites/', views.favorite_folders, name='favorite_folders'),
    path('personal/favorites/songs/', views.favorite_folder_songs, name='favorite_folder_songs'),
    path('personal/favorites/create/', views.favorite_folder_create, name='favorite_folder_create'),
    path('personal/favorites/delete/', views.favorite_folder_delete, name='favorite_folder_delete'),
    path('personal/favorites/save/', views.favorite_save, name='favorite_save'),
    path('personal/favorites/remove-song/', views.favorite_song_remove, name='favorite_song_remove'),
    path('personal/favorites/status/', views.favorite_status, name='favorite_status'),

    # 歌曲喜欢 / 我喜欢的
    path('personal/like/', views.song_like_toggle, name='song_like_toggle'),
    path('personal/like/status/', views.song_like_status, name='song_like_status'),
    path('personal/liked-songs/', views.liked_songs, name='liked_songs'),

    # 语音识别
    path('speech/recognize/', views.speech_recognize, name='speech_recognize'),
]
 
