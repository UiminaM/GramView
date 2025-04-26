from telethon.sync import TelegramClient
from django.conf import settings
from telethon.sessions import StringSession
from .models import PrivateChannelStats, BaseChannelStats


async def get_telegram_client():
    session_string = settings.TELEGRAM_STRING_SESSION
    return TelegramClient(StringSession(session_string), settings.TELEGRAM_API_ID, settings.TELEGRAM_API_HASH)


async def check_channel(username, client):
    async with client:
        try:
            result = await client.get_entity(username)
            return True if result else None
        except:
            return None


async def get_channel_data(username, client, session_str=None):
    async with client:
        try:
            channel = await client.get_entity(username)
            photo = await client.download_profile_photo(channel)
            photo_url = photo if photo else None
            if session_str:
                PrivateChannelStats.objects.create(
                    channel=channel,
                    views=123,
                    subscribers=456,
                    forwards=10,
                    reactions=5,
                    engagement_rate=0.1,
                    retention_rate=0.8,
                    session_string=session_str
                )
            else:
                BaseChannelStats.objects.create(
                    channel=channel,
                    views=123,
                    subscribers=456,
                )
            return {
                'name': channel.title,
                'username': channel.username,
                'photo_url': photo_url
            }
        except Exception as e:
            print(f"Error: {e}")
            return None
