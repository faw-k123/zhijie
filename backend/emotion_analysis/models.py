from django.db import models

class EmotionTimeSeries(models.Model):
    song_id = models.IntegerField()
    date = models.DateField()
    positive_count = models.IntegerField(default=0)
    negative_count = models.IntegerField(default=0)
    neutral_count = models.IntegerField(default=0)
    total_count = models.IntegerField(default=0)
    positive_rate = models.FloatField(default=0)
    negative_rate = models.FloatField(default=0)
    emotion_index = models.FloatField(default=0)

    class Meta:
        db_table = 'emotion_time_series'
        unique_together = ('song_id', 'date')

class Event(models.Model):
    song_id = models.IntegerField()
    event_date = models.DateField()
    event_name = models.CharField(max_length=200)
    event_type = models.CharField(max_length=50, default='宣传活动')
    description = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'emotion_event'
        unique_together = ('song_id', 'event_date', 'event_name')
