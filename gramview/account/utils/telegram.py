from asgiref.sync import sync_to_async
from telethon.sync import TelegramClient
from django.conf import settings
from telethon.sessions import StringSession
from datetime import datetime, timedelta, date
from django.utils.timezone import make_aware, is_naive
from account.models import Channels, Post, Comment, SubscriberGrowth
from django.core.files import File
import os
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
def save_channel(username, title, photo_path):
    obj, _ = Channels.objects.get_or_create(username=username)
    obj.name = title

    if photo_path:
        with open(photo_path, 'rb') as f:
            obj.photo.save(os.path.basename(photo_path), File(f), save=False)

    obj.save()
    return obj, _


async def save_post(msg, channel, reactions_count=0, forwards_count=0):
    return await Post.objects.aupdate_or_create(
        channel=channel,
        tg_post_id=msg.id,
        defaults={
            'text': msg.message,
            'published_at': msg.date,
            'views_count': msg.views or 0,
            'reactions_count': reactions_count,
            'forwards_count': forwards_count,
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
def save_subscriber_growth(channel, subscribers_count):
    today = date.today()
    SubscriberGrowth.objects.create(
        channel=channel,
        date=today,
        subscribers_count=subscribers_count
    )


async def get_channel_data(username, session_string, is_advanced):
    client = TelegramClient(StringSession(session_string), settings.API_ID, settings.API_HASH)
    await client.connect()

    try:
        channel = await client.get_entity(username)
        photo_url = await client.download_profile_photo(channel)

        db_channel, _ = await save_channel(channel.username, channel.title, photo_url)

        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=180)
        posts = []
        async for msg in client.iter_messages(channel, offset_date=end_date):
            if msg.date < start_date:
                break
            if not msg.message:
                continue

            reactions_count = 0
            forwards_count = 0
            if is_advanced:
                if msg.reactions:
                    reactions_count = sum(reaction.count for reaction in msg.reactions.results)
                forwards_count = getattr(msg, "forwards", 0)

            post_obj, _ = await save_post(msg, db_channel, reactions_count=reactions_count,
                                          forwards_count=forwards_count)

            comment_count = 0
            async for reply in client.iter_messages(channel, reply_to=msg.id):
                if not reply.message:
                    continue
                await save_comment(reply, post_obj)
                comment_count += 1

            await update_comment_count(post_obj, comment_count)
            posts.append(post_obj)
        
        if is_advanced:
            full_channel = await client.get_entity(channel.username)
            subscribers = full_channel.participants_count
    
            save_subscriber_growth(db_channel, subscribers)

        return {
            'title': db_channel.name,
            'username': db_channel.username,
            'photo_url': photo_url
        }

    except Exception as e:
        print(f"ERROR: {e}")
        return None
    finally:
        await client.disconnect()
