/*
 Navicat Premium Dump SQL

 Source Server         : 大创数据库
 Source Server Type    : SQL Server
 Source Server Version : 17004045 (17.00.4045)
 Source Host           : rm-bp1jvcvqpzffh5g0xko.sqlserver.rds.aliyuncs.com:1433
 Source Catalog        : music_db
 Source Schema         : behave

 Target Server Type    : SQL Server
 Target Server Version : 17004045 (17.00.4045)
 File Encoding         : 65001

 Date: 16/07/2026 08:47:37
*/


-- ----------------------------
-- Table structure for PersonalityTests
-- ----------------------------
IF EXISTS (SELECT * FROM sys.all_objects WHERE object_id = OBJECT_ID(N'[behave].[PersonalityTests]') AND type IN ('U'))
	DROP TABLE [behave].[PersonalityTests]
GO

CREATE TABLE [behave].[PersonalityTests] (
  [test_id] bigint  IDENTITY(1,1) NOT NULL,
  [user_id] varchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS  NULL,
  [personality_type] nvarchar(20) COLLATE SQL_Latin1_General_CP1_CI_AS  NULL,
  [result_detail] nvarchar(max) COLLATE SQL_Latin1_General_CP1_CI_AS  NULL,
  [test_date] datetime  NULL
)
GO

ALTER TABLE [behave].[PersonalityTests] SET (LOCK_ESCALATION = TABLE)
GO


-- ----------------------------
-- Records of PersonalityTests
-- ----------------------------
SET IDENTITY_INSERT [behave].[PersonalityTests] ON
GO

INSERT INTO [behave].[PersonalityTests] ([test_id], [user_id], [personality_type], [result_detail], [test_date]) VALUES (N'2', N'6', N'喜欢探索', N'{"scores": {"openness": 70, "conscientiousness": 75, "extraversion": 75, "agreeableness": 70, "neuroticism": 70}, "tags": ["喜欢探索", "规划型", "社交型", "包容型", "情绪敏感", "文化体验者"], "description": "你的画像：喜欢探索、规划型、社交型、包容型、情绪敏感、文化体验者。你对新事物保持适度的好奇，喜欢分享和社交，情绪感受适中。适合体验具有历史背景的中国传统音乐。", "recommendations": [{"id": 146, "title": "秦王破阵乐", "genre": "编钟", "audio_url": "audio/乐器/编钟/秦王破阵乐(编钟乐队与歌队).mp3", "cover_url": "images/poster/乐器/编钟.jpg"}, {"id": 147, "title": "霓裳羽衣曲", "genre": "编钟", "audio_url": "audio/乐器/编钟/霓裳羽衣曲.mp3", "cover_url": "images/poster/乐器/编钟.jpg"}, {"id": 148, "title": "春江花月夜", "genre": "编钟", "audio_url": "audio/乐器/编钟/春江花月夜《编钟与编磬》.mp3", "cover_url": "images/poster/乐器/编钟.jpg"}, {"id": 149, "title": "采薇", "genre": "大鼓", "audio_url": "audio/乐器/大鼓/采薇.mp3", "cover_url": "images/poster/乐器/大鼓.jpg"}, {"id": 150, "title": "神舞", "genre": "大鼓", "audio_url": "audio/乐器/大鼓/神舞 ( 孝淑 bootleg ）.mp3", "cover_url": "images/poster/乐器/大鼓.jpg"}, {"id": 151, "title": "执羽", "genre": "大鼓", "audio_url": "audio/乐器/大鼓/执羽（选自舞剧孔子）.mp3", "cover_url": "images/poster/乐器/大鼓.jpg"}, {"id": 152, "title": "沧海一声笑", "genre": "笛子", "audio_url": "audio/乐器/笛子/沧海一声笑.mp3", "cover_url": "images/poster/乐器/笛子.jpg"}, {"id": 153, "title": "大鱼", "genre": "笛子", "audio_url": "audio/乐器/笛子/大鱼.mp3", "cover_url": "images/poster/乐器/笛子.jpg"}], "recommend_directions": ["笛子", "葫芦丝", "马头琴", "阮", "古琴", "编钟", "大鼓", "唢呐", "琵琶", "古筝", "箫", "埙"], "ai_reason": "你这般热爱探源新意、行事妥帖热络的文化体验者，恰好能在这三首传世古乐里饱览不同切面的东方古典气韵。铿锵雄健的《秦王破阵乐》呼应你外向爽利的舒展气场，绮丽缥缈的《霓裳羽衣曲》接住你情绪敏感的细腻感知，澄明悠缓的《春江花月夜》则贴合你包容松弛的心境，刚好满足你逐层深挖传统乐韵意趣的探索欲。"}', N'2026-07-14 16:29:12.870')
GO

INSERT INTO [behave].[PersonalityTests] ([test_id], [user_id], [personality_type], [result_detail], [test_date]) VALUES (N'3', N'4', N'喜欢探索', N'{"scores": {"openness": 90, "conscientiousness": 80, "extraversion": 90, "agreeableness": 100, "neuroticism": 70}, "tags": ["喜欢探索", "规划型", "社交型", "包容型", "情绪敏感", "文化体验者"], "description": "你的画像：喜欢探索、规划型、社交型、包容型、情绪敏感、文化体验者。你乐于接受不同文化，喜欢探索新的音乐风格，喜欢分享和社交，情绪感受适中。适合体验具有历史背景的中国传统音乐。", "recommendations": [{"id": 146, "title": "秦王破阵乐", "genre": "编钟", "audio_url": "audio/乐器/编钟/秦王破阵乐(编钟乐队与歌队).mp3", "cover_url": "images/poster/乐器/编钟.jpg"}, {"id": 147, "title": "霓裳羽衣曲", "genre": "编钟", "audio_url": "audio/乐器/编钟/霓裳羽衣曲.mp3", "cover_url": "images/poster/乐器/编钟.jpg"}, {"id": 148, "title": "春江花月夜", "genre": "编钟", "audio_url": "audio/乐器/编钟/春江花月夜《编钟与编磬》.mp3", "cover_url": "images/poster/乐器/编钟.jpg"}, {"id": 149, "title": "采薇", "genre": "大鼓", "audio_url": "audio/乐器/大鼓/采薇.mp3", "cover_url": "images/poster/乐器/大鼓.jpg"}, {"id": 150, "title": "神舞", "genre": "大鼓", "audio_url": "audio/乐器/大鼓/神舞 ( 孝淑 bootleg ）.mp3", "cover_url": "images/poster/乐器/大鼓.jpg"}, {"id": 151, "title": "执羽", "genre": "大鼓", "audio_url": "audio/乐器/大鼓/执羽（选自舞剧孔子）.mp3", "cover_url": "images/poster/乐器/大鼓.jpg"}, {"id": 152, "title": "沧海一声笑", "genre": "笛子", "audio_url": "audio/乐器/笛子/沧海一声笑.mp3", "cover_url": "images/poster/乐器/笛子.jpg"}, {"id": 153, "title": "大鱼", "genre": "笛子", "audio_url": "audio/乐器/笛子/大鱼.mp3", "cover_url": "images/poster/乐器/笛子.jpg"}], "recommend_directions": ["笛子", "葫芦丝", "马头琴", "阮", "古琴", "编钟", "大鼓", "唢呐", "琵琶", "古筝", "箫", "埙"], "ai_reason": "您开放性、外向性得分极高又素来热爱文化体验，雄浑铿锵的《秦王破阵乐》载着初唐开疆的凌云意气，飘逸灵动的《霓裳羽衣曲》藏着盛唐宫苑的浪漫遐想，既能满足你探索古乐背后厚重历史脉络的好奇心，也适配你社交型特质和同好围坐畅谈的喜好。\n宜人性拉满、情绪敏感的你，聆听《春江花月夜》里滟滟江波伴着悠悠笛箫的舒展意境，很容易接住那份共通的古典诗意，妥帖安放细腻的情绪感知。\n三首古乐从金戈铁马到仙乐缥缈再到水月闲意的排布错落有致，刚好契合你规划型的行事习惯，顺着脉络走下来便是层次丰富的完整文化体验。"}', N'2026-07-14 16:31:07.720')
GO

INSERT INTO [behave].[PersonalityTests] ([test_id], [user_id], [personality_type], [result_detail], [test_date]) VALUES (N'4', N'1001', N'喜欢探索', N'{"scores": {"openness": 75, "conscientiousness": 75, "extraversion": 60, "agreeableness": 60, "neuroticism": 75}, "tags": ["喜欢探索", "规划型", "情绪敏感"], "description": "你的画像：喜欢探索、规划型、情绪敏感。你乐于接受不同文化，喜欢探索新的音乐风格，在独处与社交间保持平衡，容易被音乐触动情绪。适合体验具有历史背景的中国传统音乐。", "recommendations": [{"id": 146, "title": "秦王破阵乐", "genre": "编钟", "audio_url": "audio/乐器/编钟/秦王破阵乐(编钟乐队与歌队).mp3", "cover_url": "images/poster/乐器/编钟.jpg"}, {"id": 147, "title": "霓裳羽衣曲", "genre": "编钟", "audio_url": "audio/乐器/编钟/霓裳羽衣曲.mp3", "cover_url": "images/poster/乐器/编钟.jpg"}, {"id": 148, "title": "春江花月夜", "genre": "编钟", "audio_url": "audio/乐器/编钟/春江花月夜《编钟与编磬》.mp3", "cover_url": "images/poster/乐器/编钟.jpg"}, {"id": 152, "title": "沧海一声笑", "genre": "笛子", "audio_url": "audio/乐器/笛子/沧海一声笑.mp3", "cover_url": "images/poster/乐器/笛子.jpg"}, {"id": 153, "title": "大鱼", "genre": "笛子", "audio_url": "audio/乐器/笛子/大鱼.mp3", "cover_url": "images/poster/乐器/笛子.jpg"}, {"id": 154, "title": "何以歌", "genre": "笛子", "audio_url": "audio/乐器/笛子/何以歌（竹笛版）.mp3", "cover_url": "images/poster/乐器/笛子.jpg"}, {"id": 157, "title": "广陵散", "genre": "古琴", "audio_url": "audio/乐器/古琴/广陵散 (古琴独奏).mp3", "cover_url": "images/poster/乐器/古琴.jpg"}, {"id": 158, "title": "梅花三弄", "genre": "古琴", "audio_url": "audio/乐器/古琴/梅花三弄.mp3", "cover_url": "images/poster/乐器/古琴.jpg"}], "recommend_directions": ["笛子", "葫芦丝", "马头琴", "阮", "古琴", "编钟", "埙", "箫"], "ai_reason": "这份曲单特意贴合你爱探索新意、行事条理妥帖又情绪细腻敏感的特质挑选，刚好覆盖你不同状态下的聆听需求。铿锵恢宏的《秦王破阵乐》呼应你向外探鲜的敞亮兴致，绮丽缥缈的《霓裳羽衣曲》妥帖接住你敏感情绪里的细碎涟漪，澄澈悠然的《春江花月夜》恰好适配你惯于规整心绪、从容安排日常的规划型习惯。"}', N'2026-07-14 16:44:20.037')
GO

INSERT INTO [behave].[PersonalityTests] ([test_id], [user_id], [personality_type], [result_detail], [test_date]) VALUES (N'5', N'1003', N'喜欢探索', N'{"scores": {"openness": 70, "conscientiousness": 85, "extraversion": 70, "agreeableness": 75, "neuroticism": 75}, "tags": ["喜欢探索", "规划型", "社交型", "包容型", "情绪敏感", "文化体验者"], "description": "你的画像：喜欢探索、规划型、社交型、包容型、情绪敏感、文化体验者。你对新事物保持适度的好奇，在独处与社交间保持平衡，容易被音乐触动情绪。适合体验具有历史背景的中国传统音乐。", "recommendations": [{"id": 146, "title": "秦王破阵乐", "genre": "编钟", "audio_url": "audio/乐器/编钟/秦王破阵乐(编钟乐队与歌队).mp3", "cover_url": "images/poster/乐器/编钟.jpg"}, {"id": 147, "title": "霓裳羽衣曲", "genre": "编钟", "audio_url": "audio/乐器/编钟/霓裳羽衣曲.mp3", "cover_url": "images/poster/乐器/编钟.jpg"}, {"id": 148, "title": "春江花月夜", "genre": "编钟", "audio_url": "audio/乐器/编钟/春江花月夜《编钟与编磬》.mp3", "cover_url": "images/poster/乐器/编钟.jpg"}, {"id": 149, "title": "采薇", "genre": "大鼓", "audio_url": "audio/乐器/大鼓/采薇.mp3", "cover_url": "images/poster/乐器/大鼓.jpg"}, {"id": 150, "title": "神舞", "genre": "大鼓", "audio_url": "audio/乐器/大鼓/神舞 ( 孝淑 bootleg ）.mp3", "cover_url": "images/poster/乐器/大鼓.jpg"}, {"id": 151, "title": "执羽", "genre": "大鼓", "audio_url": "audio/乐器/大鼓/执羽（选自舞剧孔子）.mp3", "cover_url": "images/poster/乐器/大鼓.jpg"}, {"id": 152, "title": "沧海一声笑", "genre": "笛子", "audio_url": "audio/乐器/笛子/沧海一声笑.mp3", "cover_url": "images/poster/乐器/笛子.jpg"}, {"id": 153, "title": "大鱼", "genre": "笛子", "audio_url": "audio/乐器/笛子/大鱼.mp3", "cover_url": "images/poster/乐器/笛子.jpg"}], "recommend_directions": ["笛子", "葫芦丝", "马头琴", "阮", "古琴", "编钟", "大鼓", "唢呐", "琵琶", "古筝", "箫", "埙"], "ai_reason": "你热爱探索传统文化、共情细腻的特质，恰好与这三首传世古曲分外相契，层次分明的选曲排布也刚好贴合你做事有条理的规划型偏好。从雄浑壮阔的《秦王破阵乐》、绮丽浪漫的《霓裳羽衣曲》到清旷柔婉的《春江花月夜》，全维度铺展了中式传统乐舞的千年意趣，适配你包容多元的审美取向。你情绪敏感的性子能精准接住乐声里藏着的千年前的意气与柔情，无论独自沉心沉浸式体验古文化韵致，还是邀约同好共赏叙旧都格外妥帖舒服。"}', N'2026-07-14 17:20:05.140')
GO

INSERT INTO [behave].[PersonalityTests] ([test_id], [user_id], [personality_type], [result_detail], [test_date]) VALUES (N'6', N'6', N'规划型', N'{"scores": {"openness": 65, "conscientiousness": 80, "extraversion": 90, "agreeableness": 85, "neuroticism": 70}, "tags": ["规划型", "社交型", "包容型", "情绪敏感"], "description": "你的画像：规划型、社交型、包容型、情绪敏感。你对新事物保持适度的好奇，喜欢分享和社交，情绪感受适中。适合体验具有历史背景的中国传统音乐。", "recommendations": [{"id": 146, "title": "秦王破阵乐", "genre": "编钟", "audio_url": "audio/乐器/编钟/秦王破阵乐(编钟乐队与歌队).mp3", "cover_url": "images/poster/乐器/编钟.jpg"}, {"id": 147, "title": "霓裳羽衣曲", "genre": "编钟", "audio_url": "audio/乐器/编钟/霓裳羽衣曲.mp3", "cover_url": "images/poster/乐器/编钟.jpg"}, {"id": 148, "title": "春江花月夜", "genre": "编钟", "audio_url": "audio/乐器/编钟/春江花月夜《编钟与编磬》.mp3", "cover_url": "images/poster/乐器/编钟.jpg"}, {"id": 149, "title": "采薇", "genre": "大鼓", "audio_url": "audio/乐器/大鼓/采薇.mp3", "cover_url": "images/poster/乐器/大鼓.jpg"}, {"id": 150, "title": "神舞", "genre": "大鼓", "audio_url": "audio/乐器/大鼓/神舞 ( 孝淑 bootleg ）.mp3", "cover_url": "images/poster/乐器/大鼓.jpg"}, {"id": 151, "title": "执羽", "genre": "大鼓", "audio_url": "audio/乐器/大鼓/执羽（选自舞剧孔子）.mp3", "cover_url": "images/poster/乐器/大鼓.jpg"}, {"id": 157, "title": "广陵散", "genre": "古琴", "audio_url": "audio/乐器/古琴/广陵散 (古琴独奏).mp3", "cover_url": "images/poster/乐器/古琴.jpg"}, {"id": 158, "title": "梅花三弄", "genre": "古琴", "audio_url": "audio/乐器/古琴/梅花三弄.mp3", "cover_url": "images/poster/乐器/古琴.jpg"}], "recommend_directions": ["古琴", "编钟", "大鼓", "唢呐", "琵琶", "古筝", "箫", "埙"], "ai_reason": "这三首中国传统古曲恰好适配你热忱外向、行事妥帖又心思柔软的特质，你素来擅长张罗好友相聚、凡事都安排得周全妥当，铿锵飒爽的《秦王破阵乐》能瞬间烘起欢聚的热闹气场，雍容灵动的盛唐仙乐《霓裳羽衣曲》也完全衬得上你舒展随和的包容气度。待到聚罢独处时，清润澄明的《春江花月夜》便刚好妥帖接住你敏感细腻的细碎心绪，把喧嚣后的余韵慢慢揉成松弛安宁的怡人暖意。"}', N'2026-07-14 17:32:44.567')
GO

INSERT INTO [behave].[PersonalityTests] ([test_id], [user_id], [personality_type], [result_detail], [test_date]) VALUES (N'7', N'7', N'喜欢探索', N'{"scores": {"openness": 100, "conscientiousness": 100, "extraversion": 100, "agreeableness": 100, "neuroticism": 100}, "tags": ["喜欢探索", "规划型", "社交型", "包容型", "情绪敏感", "文化体验者"], "description": "你的画像：喜欢探索、规划型、社交型、包容型、情绪敏感、文化体验者。你乐于接受不同文化，喜欢探索新的音乐风格，喜欢分享和社交，容易被音乐触动情绪。适合体验具有历史背景的中国传统音乐。", "recommendations": [{"id": 146, "title": "秦王破阵乐", "genre": "编钟", "audio_url": "audio/乐器/编钟/秦王破阵乐(编钟乐队与歌队).mp3", "cover_url": "images/poster/乐器/编钟.jpg"}, {"id": 147, "title": "霓裳羽衣曲", "genre": "编钟", "audio_url": "audio/乐器/编钟/霓裳羽衣曲.mp3", "cover_url": "images/poster/乐器/编钟.jpg"}, {"id": 148, "title": "春江花月夜", "genre": "编钟", "audio_url": "audio/乐器/编钟/春江花月夜《编钟与编磬》.mp3", "cover_url": "images/poster/乐器/编钟.jpg"}, {"id": 149, "title": "采薇", "genre": "大鼓", "audio_url": "audio/乐器/大鼓/采薇.mp3", "cover_url": "images/poster/乐器/大鼓.jpg"}, {"id": 150, "title": "神舞", "genre": "大鼓", "audio_url": "audio/乐器/大鼓/神舞 ( 孝淑 bootleg ）.mp3", "cover_url": "images/poster/乐器/大鼓.jpg"}, {"id": 151, "title": "执羽", "genre": "大鼓", "audio_url": "audio/乐器/大鼓/执羽（选自舞剧孔子）.mp3", "cover_url": "images/poster/乐器/大鼓.jpg"}, {"id": 152, "title": "沧海一声笑", "genre": "笛子", "audio_url": "audio/乐器/笛子/沧海一声笑.mp3", "cover_url": "images/poster/乐器/笛子.jpg"}, {"id": 153, "title": "大鱼", "genre": "笛子", "audio_url": "audio/乐器/笛子/大鱼.mp3", "cover_url": "images/poster/乐器/笛子.jpg"}], "recommend_directions": ["笛子", "葫芦丝", "马头琴", "阮", "古琴", "编钟", "大鼓", "唢呐", "琵琶", "古筝", "箫", "埙"], "ai_reason": "专为你挑选的这三首传世古乐各有千秋，从雄健铿锵的《秦王破阵乐》、浪漫绮丽的《霓裳羽衣曲》到清和幽远的《春江花月夜》，覆盖了截然不同的中式美学维度，恰好适配你满点的探索欲与文化体验需求，也能妥帖安放你敏感细腻的情绪起伏。\n它们的文化脉络清晰可溯源，既方便你顺着乐史脉络梳理品味、满足规划爱好，又足够适配多人共赏的雅聚场景，刚好贴合你热络包容的社交属性呀。"}', N'2026-07-14 18:05:58.327')
GO

INSERT INTO [behave].[PersonalityTests] ([test_id], [user_id], [personality_type], [result_detail], [test_date]) VALUES (N'9', N'6', N'喜欢探索', N'{"scores": {"openness": 95, "conscientiousness": 100, "extraversion": 100, "agreeableness": 100, "neuroticism": 100}, "tags": ["喜欢探索", "规划型", "社交型", "包容型", "情绪敏感", "文化体验者"], "description": "你的画像：喜欢探索、规划型、社交型、包容型、情绪敏感、文化体验者。你乐于接受不同文化，喜欢探索新的音乐风格，喜欢分享和社交，容易被音乐触动情绪。适合体验具有历史背景的中国传统音乐。", "recommendations": [{"id": 146, "title": "秦王破阵乐", "genre": "编钟", "audio_url": "audio/乐器/编钟/秦王破阵乐(编钟乐队与歌队).mp3", "cover_url": "images/poster/乐器/编钟.jpg"}, {"id": 147, "title": "霓裳羽衣曲", "genre": "编钟", "audio_url": "audio/乐器/编钟/霓裳羽衣曲.mp3", "cover_url": "images/poster/乐器/编钟.jpg"}, {"id": 148, "title": "春江花月夜", "genre": "编钟", "audio_url": "audio/乐器/编钟/春江花月夜《编钟与编磬》.mp3", "cover_url": "images/poster/乐器/编钟.jpg"}, {"id": 149, "title": "采薇", "genre": "大鼓", "audio_url": "audio/乐器/大鼓/采薇.mp3", "cover_url": "images/poster/乐器/大鼓.jpg"}, {"id": 150, "title": "神舞", "genre": "大鼓", "audio_url": "audio/乐器/大鼓/神舞 ( 孝淑 bootleg ）.mp3", "cover_url": "images/poster/乐器/大鼓.jpg"}, {"id": 151, "title": "执羽", "genre": "大鼓", "audio_url": "audio/乐器/大鼓/执羽（选自舞剧孔子）.mp3", "cover_url": "images/poster/乐器/大鼓.jpg"}, {"id": 152, "title": "沧海一声笑", "genre": "笛子", "audio_url": "audio/乐器/笛子/沧海一声笑.mp3", "cover_url": "images/poster/乐器/笛子.jpg"}, {"id": 153, "title": "大鱼", "genre": "笛子", "audio_url": "audio/乐器/笛子/大鱼.mp3", "cover_url": "images/poster/乐器/笛子.jpg"}], "recommend_directions": ["笛子", "葫芦丝", "马头琴", "阮", "古琴", "编钟", "大鼓", "唢呐", "琵琶", "古筝", "箫", "埙"], "ai_reason": "为你挑选的《秦王破阵乐》《霓裳羽衣曲》《春江花月夜》，铺展了从大唐雄健军乐、仙姿宫廷雅乐到江南水月清声的错落脉络，刚好适配你热爱探索的文化体验者属性。\n你满点的规划力、热络的社交属性，既能让你顺着乐舞沿革脉络梳理细节邀约同好共赏，极致敏锐细腻的情绪触角也能妥帖接住旋律里藏着的千年余韵，沉浸式浸在传统乐韵里得趣。"}', N'2026-07-14 18:35:30.203')
GO

INSERT INTO [behave].[PersonalityTests] ([test_id], [user_id], [personality_type], [result_detail], [test_date]) VALUES (N'10', N'6', N'社交型', N'{"scores": {"openness": 60, "conscientiousness": 65, "extraversion": 85, "agreeableness": 85, "neuroticism": 80}, "tags": ["社交型", "包容型", "情绪敏感"], "description": "你的画像：社交型、包容型、情绪敏感。你对新事物保持适度的好奇，喜欢分享和社交，容易被音乐触动情绪。适合体验具有历史背景的中国传统音乐。", "recommendations": [{"id": 149, "title": "采薇", "genre": "大鼓", "audio_url": "audio/乐器/大鼓/采薇.mp3", "cover_url": "images/poster/乐器/大鼓.jpg"}, {"id": 150, "title": "神舞", "genre": "大鼓", "audio_url": "audio/乐器/大鼓/神舞 ( 孝淑 bootleg ）.mp3", "cover_url": "images/poster/乐器/大鼓.jpg"}, {"id": 151, "title": "执羽", "genre": "大鼓", "audio_url": "audio/乐器/大鼓/执羽（选自舞剧孔子）.mp3", "cover_url": "images/poster/乐器/大鼓.jpg"}, {"id": 157, "title": "广陵散", "genre": "古琴", "audio_url": "audio/乐器/古琴/广陵散 (古琴独奏).mp3", "cover_url": "images/poster/乐器/古琴.jpg"}, {"id": 158, "title": "梅花三弄", "genre": "古琴", "audio_url": "audio/乐器/古琴/梅花三弄.mp3", "cover_url": "images/poster/乐器/古琴.jpg"}, {"id": 159, "title": "高山流水", "genre": "古琴", "audio_url": "audio/乐器/古琴/高山流水.mp3", "cover_url": "images/poster/乐器/古琴.jpg"}, {"id": 160, "title": "渔舟唱晚", "genre": "古筝", "audio_url": "audio/乐器/古筝/渔舟唱晚 (古筝独奏).mp3", "cover_url": "images/poster/乐器/古筝.jpg"}, {"id": 161, "title": "画心", "genre": "古筝", "audio_url": "audio/乐器/古筝/画心.mp3", "cover_url": "images/poster/乐器/古筝.jpg"}], "recommend_directions": ["大鼓", "唢呐", "琵琶", "古筝", "箫", "古琴", "埙"], "ai_reason": "你素来热忱外向爱结伴同游，心性包容软和又对情绪感知格外敏锐，这三支源自先秦雅乐脉络的乐舞曲目，刚好妥帖踩中你的喜好点。《采薇》裹着诗里代代相传的柔婉共情，能稳稳接住你偶然泛起的细碎情绪涟漪，《神舞》与《执羽》里众乐齐鸣、联袂踏节的和乐氛围感，正适配你爱呼朋引伴、同频欢享的热络脾性。"}', N'2026-07-14 18:50:47.177')
GO

INSERT INTO [behave].[PersonalityTests] ([test_id], [user_id], [personality_type], [result_detail], [test_date]) VALUES (N'11', N'1004', N'喜欢探索', N'{"scores": {"openness": 75, "conscientiousness": 70, "extraversion": 45, "agreeableness": 75, "neuroticism": 55}, "tags": ["喜欢探索", "规划型", "包容型", "文化体验者"], "description": "你的画像：喜欢探索、规划型、包容型、文化体验者。你乐于接受不同文化，喜欢探索新的音乐风格，在独处与社交间保持平衡，情绪感受适中。适合体验具有历史背景的中国传统音乐。", "recommendations": [{"id": 146, "title": "秦王破阵乐", "genre": "编钟", "audio_url": "audio/乐器/编钟/秦王破阵乐(编钟乐队与歌队).mp3", "cover_url": "images/poster/乐器/编钟.jpg"}, {"id": 147, "title": "霓裳羽衣曲", "genre": "编钟", "audio_url": "audio/乐器/编钟/霓裳羽衣曲.mp3", "cover_url": "images/poster/乐器/编钟.jpg"}, {"id": 148, "title": "春江花月夜", "genre": "编钟", "audio_url": "audio/乐器/编钟/春江花月夜《编钟与编磬》.mp3", "cover_url": "images/poster/乐器/编钟.jpg"}, {"id": 152, "title": "沧海一声笑", "genre": "笛子", "audio_url": "audio/乐器/笛子/沧海一声笑.mp3", "cover_url": "images/poster/乐器/笛子.jpg"}, {"id": 153, "title": "大鱼", "genre": "笛子", "audio_url": "audio/乐器/笛子/大鱼.mp3", "cover_url": "images/poster/乐器/笛子.jpg"}, {"id": 154, "title": "何以歌", "genre": "笛子", "audio_url": "audio/乐器/笛子/何以歌（竹笛版）.mp3", "cover_url": "images/poster/乐器/笛子.jpg"}, {"id": 157, "title": "广陵散", "genre": "古琴", "audio_url": "audio/乐器/古琴/广陵散 (古琴独奏).mp3", "cover_url": "images/poster/乐器/古琴.jpg"}, {"id": 158, "title": "梅花三弄", "genre": "古琴", "audio_url": "audio/乐器/古琴/梅花三弄.mp3", "cover_url": "images/poster/乐器/古琴.jpg"}], "recommend_directions": ["笛子", "葫芦丝", "马头琴", "阮", "古琴", "编钟", "古筝", "箫"], "ai_reason": "您热爱探索的高开放性特质天生适配沉浸式的传统文化体验，这份选单特意按照意境从雄阔到绮丽再到清悠的逻辑排布，恰好贴合你条理明晰的规划型习惯。三首曲目兼容了沙场豪情、宫阙逸趣与江天清韵的不同意涵，也妥帖呼应你包容和善的高宜人性特质，动静相宜的旋律刚好适配你松紧适度的情绪节律，闲时聆听便可沿声游遍千年中式雅境。"}', N'2026-07-14 20:37:11.230')
GO

SET IDENTITY_INSERT [behave].[PersonalityTests] OFF
GO


-- ----------------------------
-- Table structure for PlayRecords
-- ----------------------------
IF EXISTS (SELECT * FROM sys.all_objects WHERE object_id = OBJECT_ID(N'[behave].[PlayRecords]') AND type IN ('U'))
	DROP TABLE [behave].[PlayRecords]
GO

CREATE TABLE [behave].[PlayRecords] (
  [record_id] bigint  IDENTITY(1,1) NOT NULL,
  [user_id] varchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS  NULL,
  [song_id] varchar(20) COLLATE SQL_Latin1_General_CP1_CI_AS  NULL,
  [play_duration] int  NULL,
  [play_time] datetime  NULL
)
GO

ALTER TABLE [behave].[PlayRecords] SET (LOCK_ESCALATION = TABLE)
GO


-- ----------------------------
-- Records of PlayRecords
-- ----------------------------
SET IDENTITY_INSERT [behave].[PlayRecords] ON
GO

SET IDENTITY_INSERT [behave].[PlayRecords] OFF
GO


-- ----------------------------
-- Table structure for Users
-- ----------------------------
IF EXISTS (SELECT * FROM sys.all_objects WHERE object_id = OBJECT_ID(N'[behave].[Users]') AND type IN ('U'))
	DROP TABLE [behave].[Users]
GO

CREATE TABLE [behave].[Users] (
  [user_id] varchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS  NOT NULL,
  [username] nvarchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS  NOT NULL,
  [country] nvarchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS  NULL,
  [register_date] datetime  NULL,
  [password] nvarchar(100) COLLATE SQL_Latin1_General_CP1_CI_AS  NULL
)
GO

ALTER TABLE [behave].[Users] SET (LOCK_ESCALATION = TABLE)
GO


-- ----------------------------
-- Records of Users
-- ----------------------------
INSERT INTO [behave].[Users] ([user_id], [username], [country], [register_date], [password]) VALUES (N'1', N'user1', NULL, N'2026-07-13 10:03:29.850', N'123456')
GO

INSERT INTO [behave].[Users] ([user_id], [username], [country], [register_date], [password]) VALUES (N'1000', N'testuser123', N'中国', N'2026-07-14 16:09:50.467', N'test123')
GO

INSERT INTO [behave].[Users] ([user_id], [username], [country], [register_date], [password]) VALUES (N'1001', N'111', N'中国', N'2026-07-14 16:43:01.557', N'111')
GO

INSERT INTO [behave].[Users] ([user_id], [username], [country], [register_date], [password]) VALUES (N'1002', N'1234', N'中国', N'2026-07-14 17:02:30.120', N'123')
GO

INSERT INTO [behave].[Users] ([user_id], [username], [country], [register_date], [password]) VALUES (N'1003', N'1', N'中国', N'2026-07-14 17:18:36.060', N'1')
GO

INSERT INTO [behave].[Users] ([user_id], [username], [country], [register_date], [password]) VALUES (N'1004', N'Q', N'中国', N'2026-07-14 20:35:29.090', N'123456')
GO

INSERT INTO [behave].[Users] ([user_id], [username], [country], [register_date], [password]) VALUES (N'2', N'user2', NULL, N'2026-07-13 10:03:30.353', N'123456')
GO

INSERT INTO [behave].[Users] ([user_id], [username], [country], [register_date], [password]) VALUES (N'3', N'user3', NULL, N'2026-07-13 10:03:30.733', N'123456')
GO

INSERT INTO [behave].[Users] ([user_id], [username], [country], [register_date], [password]) VALUES (N'4', N'hua', NULL, N'2026-07-13 10:04:10.810', N'123456')
GO

INSERT INTO [behave].[Users] ([user_id], [username], [country], [register_date], [password]) VALUES (N'5', N'test_cn', N'??', N'2026-07-13 10:07:00.153', N'123456')
GO

INSERT INTO [behave].[Users] ([user_id], [username], [country], [register_date], [password]) VALUES (N'6', N'123', N'中国', N'2026-07-13 15:10:12.437', N'111')
GO

INSERT INTO [behave].[Users] ([user_id], [username], [country], [register_date], [password]) VALUES (N'7', N'hua1', N'中国', N'2026-07-13 17:48:55.103', N'1111111')
GO

INSERT INTO [behave].[Users] ([user_id], [username], [country], [register_date], [password]) VALUES (N'999', N'testuser', N'中国', N'2026-07-14 11:12:34.833', N'test123')
GO


-- ----------------------------
-- Table structure for ViewRecords
-- ----------------------------
IF EXISTS (SELECT * FROM sys.all_objects WHERE object_id = OBJECT_ID(N'[behave].[ViewRecords]') AND type IN ('U'))
	DROP TABLE [behave].[ViewRecords]
GO

CREATE TABLE [behave].[ViewRecords] (
  [view_id] bigint  IDENTITY(1,1) NOT NULL,
  [user_id] varchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS  NULL,
  [target_type] nvarchar(20) COLLATE SQL_Latin1_General_CP1_CI_AS  NULL,
  [target_id] varchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS  NULL,
  [view_time] datetime  NULL
)
GO

ALTER TABLE [behave].[ViewRecords] SET (LOCK_ESCALATION = TABLE)
GO


-- ----------------------------
-- Records of ViewRecords
-- ----------------------------
SET IDENTITY_INSERT [behave].[ViewRecords] ON
GO

SET IDENTITY_INSERT [behave].[ViewRecords] OFF
GO


-- ----------------------------
-- Auto increment value for PersonalityTests
-- ----------------------------
DBCC CHECKIDENT ('[behave].[PersonalityTests]', RESEED, 11)
GO


-- ----------------------------
-- Primary Key structure for table PersonalityTests
-- ----------------------------
ALTER TABLE [behave].[PersonalityTests] ADD CONSTRAINT [PK__Personal__F3FF1C028FFB1359] PRIMARY KEY CLUSTERED ([test_id])
WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON)  
ON [PRIMARY]
GO


-- ----------------------------
-- Auto increment value for PlayRecords
-- ----------------------------
DBCC CHECKIDENT ('[behave].[PlayRecords]', RESEED, 285)
GO


-- ----------------------------
-- Primary Key structure for table PlayRecords
-- ----------------------------
ALTER TABLE [behave].[PlayRecords] ADD CONSTRAINT [PK__PlayReco__BFCFB4DD83575C0E] PRIMARY KEY CLUSTERED ([record_id])
WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON)  
ON [PRIMARY]
GO


-- ----------------------------
-- Primary Key structure for table Users
-- ----------------------------
ALTER TABLE [behave].[Users] ADD CONSTRAINT [PK__Users__B9BE370FB4A061B0] PRIMARY KEY CLUSTERED ([user_id])
WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON)  
ON [PRIMARY]
GO


-- ----------------------------
-- Auto increment value for ViewRecords
-- ----------------------------
DBCC CHECKIDENT ('[behave].[ViewRecords]', RESEED, 1)
GO


-- ----------------------------
-- Primary Key structure for table ViewRecords
-- ----------------------------
ALTER TABLE [behave].[ViewRecords] ADD CONSTRAINT [PK__ViewReco__B5A34EE26EB8EDA3] PRIMARY KEY CLUSTERED ([view_id])
WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON)  
ON [PRIMARY]
GO


-- ----------------------------
-- Foreign Keys structure for table PersonalityTests
-- ----------------------------
ALTER TABLE [behave].[PersonalityTests] ADD CONSTRAINT [FK_PersonalityTests_Users] FOREIGN KEY ([user_id]) REFERENCES [behave].[Users] ([user_id]) ON DELETE NO ACTION ON UPDATE NO ACTION
GO


-- ----------------------------
-- Foreign Keys structure for table PlayRecords
-- ----------------------------
ALTER TABLE [behave].[PlayRecords] ADD CONSTRAINT [FK_PlayRecords_Users] FOREIGN KEY ([user_id]) REFERENCES [behave].[Users] ([user_id]) ON DELETE NO ACTION ON UPDATE NO ACTION
GO


-- ----------------------------
-- Foreign Keys structure for table ViewRecords
-- ----------------------------
ALTER TABLE [behave].[ViewRecords] ADD CONSTRAINT [FK_ViewRecords_Users] FOREIGN KEY ([user_id]) REFERENCES [behave].[Users] ([user_id]) ON DELETE NO ACTION ON UPDATE NO ACTION
GO

