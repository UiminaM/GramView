from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Channels(models.Model):
    name = models.CharField(max_length=255)
    username = models.CharField(max_length=255, unique=True)
    photo_url = models.URLField(blank=True, null=True)
    users = models.ManyToManyField(User, through='UserChannelAccess', related_name='channels')
    last_updated = models.DateTimeField(auto_now=True)

class UserChannelAccess(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    channel = models.ForeignKey('Channels', on_delete=models.CASCADE)
    is_owner = models.BooleanField(default=False)

    class Meta:
        unique_together = ('user', 'channel')


class BaseChannelStats(models.Model):
    channel = models.ForeignKey('Channels', on_delete=models.CASCADE)
    date = models.DateField(auto_now=True)
    subscribers = models.IntegerField()


class PrivateChannelStats(BaseChannelStats):
    engagement_rate = models.FloatField()
    retention_rate = models.FloatField(null=True, blank=True)
    session_string = models.CharField(max_length=255, null=True, blank=True)


class Post(models.Model):
    channel = models.ForeignKey(Channels, on_delete=models.CASCADE, related_name='posts')
    tg_post_id = models.BigIntegerField()
    text = models.TextField()
    published_at = models.DateTimeField()
    views_count = models.PositiveIntegerField(default=0)
    reactions_count = models.PositiveIntegerField(default=0)
    forwards_count = models.PositiveIntegerField(default=0, null=True, blank=True)
    comments_count = models.PositiveIntegerField(default=0)


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    author_name = models.CharField(max_length=255)
    text = models.TextField()
    published_at = models.DateTimeField()

    CLASS_CHOICES = [
        ('positive', 'Positive'),
        ('negative', 'Negative'),
        ('neutral', 'Neutral'),
    ]
    classification = models.CharField(max_length=10, choices=CLASS_CHOICES, default='neutral')


class SubscriberGrowth(models.Model):
    channel = models.ForeignKey(Channels, on_delete=models.CASCADE, related_name='subscriber_growth')
    date = models.DateField()
    subscribers_count = models.PositiveIntegerField()

    class Meta:
        unique_together = ('channel', 'date')