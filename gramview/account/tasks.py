from celery import shared_task
from telethon.sync import TelegramClient
from telethon.sessions import StringSession
from datetime import date
from django.conf import settings
from .models import Channels, SubscriberGrowth

@shared_task
def update_subscriber_growth():
    from main.utils import save_subscriber_growth  # или куда ты определила функцию

    for channel in Channels.objects.all():
        access = channel.userchannelaccess_set.filter(is_owner=True).first()
        if not access or not access.user.profile.session_string:
            continue  # без session_string не получить данные

        session_string = access.user.profile.session_string
        client = TelegramClient(StringSession(session_string), settings.API_ID, settings.API_HASH)
        client.connect()

        try:
            full_channel = client.get_entity(channel.username)
            subscribers = full_channel.participants_count
            save_subscriber_growth(channel, subscribers)
        except Exception as e:
            print(f"Ошибка при обновлении подписчиков {channel.username}: {e}")
        finally:
            client.disconnect()
