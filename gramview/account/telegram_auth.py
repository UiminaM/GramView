from telethon.sync import TelegramClient
from telethon.sessions import StringSession
from django.conf import settings

def authenticate_user(phone, code):
    session = StringSession()
    client = TelegramClient(
        session,
        settings.TELEGRAM_API_ID,
        settings.TELEGRAM_API_HASH
    )

    client.connect()
    try:
        sent = client.send_code_request(phone)
        client.sign_in(phone, code)

        if client.is_user_authorized() is False:
            raise Exception("2FA включена, нужно добавить поддержку пароля.")

        return client, session.save()
    finally:
        client.disconnect()
