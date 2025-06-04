from asgiref.sync import sync_to_async
from telethon.sync import TelegramClient
from django.conf import settings
from telethon.sessions import StringSession
from datetime import datetime, timedelta
from django.utils.timezone import make_aware, is_naive
from account.models import Channels, Post, Comment, BaseChannelStats, PrivateChannelStats
import joblib


TEMP_SESSIONS = {}


async def start_telegram_auth(phone_number):
    client = TelegramClient(StringSession(), settings.API_ID, settings.API_HASH)
    await client.connect()
    try:
        sent = await client.send_code_request(phone_number)
        TEMP_SESSIONS[phone_number] = {
            'client': client,
            'phone_code_hash': sent.phone_code_hash
        }
        return True
    except Exception as e:
        await client.disconnect()
        raise e


async def authenticate_user(phone_number, code):
    session_data = TEMP_SESSIONS.get(phone_number)
    if not session_data:
        raise ValueError("Сначала отправьте код.")

    client = session_data['client']
    phone_code_hash = session_data['phone_code_hash']

    try:
        await client.sign_in(phone=phone_number, code=code, phone_code_hash=phone_code_hash)
        session_str = client.session.save()
        return client, session_str
    except Exception as e:
        await client.disconnect()
        raise e


async def check_channel(username, session_string):
    async with TelegramClient(StringSession(session_string), settings.API_ID, settings.API_HASH) as client:
        try:
            result = await client.get_entity(username)
            return True if result else None
        except:
            return None


model = joblib.load("account/model/LogisticRegression.pkl")
def classify_comment(text):
    return model.predict(text)


@sync_to_async
def save_channel(username, title, photo):
    return Channels.objects.update_or_create(
        username=username,
        defaults={'name': title, 'photo_url': photo}
    )


@sync_to_async
def save_post(msg, db_channel):
    published_at = make_aware(msg.date) if is_naive(msg.date) else msg.date

    return Post.objects.update_or_create(
        tg_post_id=msg.id,
        channel=db_channel,
        defaults={
            'text': msg.message,
            'published_at': published_at,
            'views_count': msg.views or 0,
            'reactions_count': sum([r.count for r in msg.reactions.results]) if msg.reactions else 0,
            'forwards_count': msg.forwards or 0,
        }
    )


@sync_to_async
def save_comment(reply, post_obj):
    published_at = make_aware(reply.date) if is_naive(reply.date) else reply.date

    return Comment.objects.update_or_create(
        post=post_obj,
        author_name=(reply.sender.username or "Unknown") if reply.sender else "Unknown",
        text=reply.message,
        published_at=published_at,
        defaults={'classification': classify_comment(reply.message)}
    )


@sync_to_async
def update_comment_count(post_obj, count):
    post_obj.comments_count = count
    post_obj.save()


@sync_to_async
def save_base_stats(channel, date, subscribers):
    return BaseChannelStats.objects.create(
        channel=channel,
        date=date,
        subscribers=subscribers
    )


@sync_to_async
def save_private_stats(base_stat, engagement_rate, retention_rate, session_string):
    return PrivateChannelStats.objects.create(
        basechannelstats_ptr=base_stat,
        engagement_rate=engagement_rate,
        retention_rate=retention_rate,
        session_string=session_string
    )


async def get_channel_data(username, session_string, is_advanced):
    client = TelegramClient(StringSession(session_string), settings.API_ID, settings.API_HASH)
    await client.connect()

    try:
        channel = await client.get_entity(username)
        photo = await client.download_profile_photo(channel) or ''

        db_channel, _ = await save_channel(channel.username, channel.title, photo)
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=180)
        posts = []

        async for msg in client.iter_messages(channel, offset_date=end_date):
            if msg.date < start_date:
                break
            if not msg.message:
                continue

            post_obj, _ = await save_post(msg, db_channel)
            comment_count = 0
            async for reply in client.iter_messages(channel, reply_to=msg.id):
                if not reply.message:
                    continue

                await save_comment(reply, post_obj)
                comment_count += 1

            await update_comment_count(post_obj, comment_count)
            posts.append(post_obj)


        return {
            'title': db_channel.title,
            'username': db_channel.username,
            'photo_url': db_channel.photo
        }

    except Exception as e:
        print(f"ERROR: {e}")
        return None
    finally:
        await client.disconnect()