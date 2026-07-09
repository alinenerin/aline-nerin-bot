import asyncio
import datetime
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.tl.types import PeerUser

# Credentials
API_ID = 26569107
API_HASH = '997034c44917a26f3458a0e285816997'
SESSION_STRING = '1AZWarzUBuxaOZ4K0vnFn7_xiaZfNWYjfvxPZMUfDJc7zRzSW20W0RvWKZuBJX3ud8iCH1gEp4IUHiokwCRmTx491dpyWmqp5IWdVsKuYgAgotyqYKU-B1wIgHv85Ql44_N5BW7S7NA4CsevXYYgwjFTmv9YvoyjgCxCDjf9RkzWkKnYKLIKhGY_iaCrKexylyKyOupxaKkfC5Td6mRlUIYMde2NJqWB3yUrbsf-FNkG9A0m6ZPULlLGpJO9lvP2RrPxIWMe9MWMXUzuREf_f9YNnvk5hfSfP7blGhc22SKBVe4CLtZCn3J45jXvWul2JnOcpiA4kGkALqh6RMhda5skYDQSG_KI='

# Persona Messages
MSG_1 = "vixi baby, demorei mas cheguei... tava aqui gravando umas coisas e quase esqueci de vc 😏🔥"
MSG_2 = "inclusive, acabei de liberar um pack novo lá no meu vip, tá uma delícia... quer ver umas prévias? 😈"

async def main():
    client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
    await client.connect()
    
    if not await client.is_user_authorized():
        print("Erro: Sessão inválida ou não autorizada.")
        return

    print("Iniciando varredura de chats privados para re-engajamento...")
    
    # 24 hours ago
    now = datetime.datetime.now(datetime.timezone.utc)
    threshold = now - datetime.timedelta(hours=24)

    async for dialog in client.iter_dialogs():
        # Only private chats
        if not dialog.is_user:
            continue
            
        user = dialog.entity
        # Skip bots if possible, though unlikely to be "waiting for reply"
        if getattr(user, 'bot', False):
            continue

        # Get last message
        last_msg = dialog.message
        
        # Condition: Last message was FROM the user (out=False)
        # AND it happened more than 24 hours ago (meaning we haven't replied)
        if last_msg and not last_msg.out:
            if last_msg.date < threshold:
                print(f"Re-engajando com: {user.id} - {getattr(user, 'first_name', 'User')}")
                
                try:
                    # Send seductive message
                    await client.send_message(user.id, MSG_1)
                    await asyncio.sleep(2) # Natural delay
                    
                    # Send soft sales pitch
                    await client.send_message(user.id, MSG_2)
                    print(f"Mensagens enviadas para {user.id}")
                except Exception as e:
                    print(f"Erro ao enviar para {user.id}: {e}")
                
                # Small delay between users to avoid flood limits
                await asyncio.sleep(3)

    print("Processo de re-engajamento concluído.")
    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
