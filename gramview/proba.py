from telethon.sync import TelegramClient
from telethon.sessions import StringSession

api_id = 22828730
api_hash = '685999f55f2060b6817c3e70546205b6'

with TelegramClient(StringSession(), api_id, api_hash) as client:
    print("🔑 Ваша строка сессии:")
    print(client.session.save())  # Сохрани это значение!