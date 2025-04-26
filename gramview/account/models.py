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
    views = models.IntegerField()
    subscribers = models.IntegerField()


class PrivateChannelStats(BaseChannelStats):
    forwards = models.IntegerField()
    reactions = models.IntegerField()
    engagement_rate = models.FloatField()
    retention_rate = models.FloatField(null=True, blank=True)
    session_string = models.CharField(max_length=255, null=True, blank=True)
