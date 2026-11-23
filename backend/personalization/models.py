from django.db import models


class SongLike(models.Model):
    user_id = models.CharField(max_length=50, db_index=True, verbose_name='用户ID')
    song_id = models.CharField(max_length=50, db_index=True, verbose_name='歌曲ID')
    reaction_type = models.CharField(max_length=10, choices=[('like', '喜欢'), ('dislike', '不喜欢')], verbose_name='反应类型')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        verbose_name = '歌曲喜欢/不喜欢记录'
        verbose_name_plural = '歌曲喜欢/不喜欢记录'
        db_table = 'song_like'
        unique_together = ('user_id', 'song_id')


class FavoriteFolder(models.Model):
    user_id = models.CharField(max_length=50, db_index=True, verbose_name='用户ID')
    name = models.CharField(max_length=100, verbose_name='收藏夹名称')
    icon_url = models.CharField(max_length=500, blank=True, verbose_name='图标URL')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        verbose_name = '收藏夹'
        verbose_name_plural = '收藏夹'
        db_table = 'favorite_folder'


class FavoriteSong(models.Model):
    folder = models.ForeignKey(FavoriteFolder, on_delete=models.CASCADE, verbose_name='所属收藏夹')
    song_id = models.CharField(max_length=50, verbose_name='歌曲ID')
    title = models.CharField(max_length=200, verbose_name='歌曲标题')
    intro = models.TextField(blank=True, verbose_name='歌曲简介')
    mv_url = models.CharField(max_length=500, blank=True, verbose_name='MV URL')
    audio_url = models.CharField(max_length=500, blank=True, verbose_name='音频URL')
    cover_url = models.CharField(max_length=500, blank=True, verbose_name='封面URL')
    added_at = models.DateTimeField(auto_now_add=True, verbose_name='添加时间')

    class Meta:
        verbose_name = '收藏歌曲'
        verbose_name_plural = '收藏歌曲'
        db_table = 'favorite_song'
        unique_together = ('folder', 'song_id')


class CulturalCircleTest(models.Model):
    user_id = models.CharField(max_length=50, db_index=True, verbose_name='用户ID')
    f1_score = models.IntegerField(verbose_name='宗教信仰体系得分')
    f2_score = models.IntegerField(verbose_name='生计生态地理得分')
    f3_score = models.IntegerField(verbose_name='社会政治制度得分')
    f4_score = models.IntegerField(verbose_name='族群语言血脉得分')
    f5_score = models.IntegerField(verbose_name='历史时段变迁得分')
    f6_score = models.IntegerField(verbose_name='阶层生活方式得分')
    f7_score = models.IntegerField(verbose_name='审美艺术传统得分')
    matched_circles = models.JSONField(verbose_name='匹配的文化圈层列表')
    answers = models.JSONField(verbose_name='用户答题记录')
    test_date = models.DateTimeField(auto_now_add=True, verbose_name='测试时间')

    class Meta:
        verbose_name = '文化圈层测试结果'
        verbose_name_plural = '文化圈层测试结果'
        db_table = 'cultural_circle_test'
        ordering = ['-test_date']




# ============================================================
# 【新增】追加到 personalization/models.py 文件末尾
# 与 CulturalCircleTest 保持同样的字段风格
# ============================================================

class GuofengPersonaTest(models.Model):
    """国风兴趣人设测试（15题问卷）结果。"""

    user_id = models.CharField(max_length=50, db_index=True, verbose_name='用户ID')

    # 六维人设匹配向量（0-100）
    d1_traditionalism = models.IntegerField(verbose_name='传统认同度')
    d2_consumption = models.IntegerField(verbose_name='消费投入度')
    d3_social = models.IntegerField(verbose_name='社交活跃度')
    d4_self_expression = models.IntegerField(verbose_name='自我表达欲')
    d5_trend = models.IntegerField(verbose_name='潮流敏感度')
    d6_cultural_life = models.IntegerField(verbose_name='文化生活参与度')

    tag_scores = models.JSONField(verbose_name='原始标签打分明细')
    matched_personas = models.JSONField(verbose_name='匹配的人设列表')
    answers = models.JSONField(verbose_name='用户答题记录')
    test_date = models.DateTimeField(auto_now_add=True, verbose_name='测试时间')

    class Meta:
        verbose_name = '国风人设测试结果'
        verbose_name_plural = '国风人设测试结果'
        db_table = 'guofeng_persona_test'
        ordering = ['-test_date']

