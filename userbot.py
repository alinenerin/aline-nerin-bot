import os
import asyncio
import logging
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from groq import AsyncGroq
from aiohttp import web

# Configuration
API_ID = 26569107  
API_HASH = '997034c44917a26f3458a0e285816997'
SESSION_STRING = '1AZWarzUBuxaOZ4K0vnFn7_xiaZfNWYjfvxPZMUfDJc7zRzSW20W0RvWKZuBJX3ud8iCH1gEp4IUHiokwCRmTx491dpyWmqp5IWdVsKuYgAgotyqYKU-B1wIgHv85Ql44_N5BW7S7NA4CsevXYYgwjFTmv9YvoyjgCxCDjf9RkzWkKnYKLIKhGY_iaCrKexylyKyOupxaKkfC5Td6mRlUIYMde2NJqWB3yUrbsf-FNkG9A0m6ZPULlLGpJO9lvP2RrPxIWMe9MWMXUzuREf_f9YNnvk5hfSfP7blGhc22SKBVe4CLtZCn3J45jXvWul2JnOcpiA4kGkALqh6RMhda5skYDQSG_KI='
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
PORT = int(os.getenv("PORT", 8080))

# Constants
PIX = '17981028959'
PACK = 'R$ 25,00'
VIP = 'R$ 39,90'

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Clients
groq_client = AsyncGroq(api_key=GROQ_API_KEY)
client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

async def get_ai_response(text):
    try:
        chat_completion = await groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": f"Você é uma assistente prestativa. Informações: Pix: {PIX}, Pack: {PACK}, VIP: {VIP}."},
                {"role": "user", "content": text}
            ],
            model="llama-3.3-70b-versatile",
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        logger.error(f"Groq Error: {e}")
        return "Desculpe, estou passando por uma instabilidade momentânea. Pode repetir?"

@client.on(events.NewMessage(incoming=True, func=lambda e: e.is_private))
async def handler(event):
    logger.info(f"Message from {event.sender_id}: {event.text}")
    response = await get_ai_response(event.text)
    await event.respond(response)

# Health Check Server
async def health_check(request):
    return web.Response(text="OK")

async def start_server():
    app = web.Application()
    app.router.add_get("/", health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', PORT)
    await site.start()
    logger.info(f"Health check server started on port {PORT}")

async def main():
    await client.start()
    logger.info("Userbot started!")
    
    # Run health check server in background
    asyncio.create_task(start_server())
    
    # Run until disconnected
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
