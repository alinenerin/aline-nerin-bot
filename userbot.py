import os
import asyncio
import logging
from aiohttp import web
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from groq import AsyncGroq

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
API_ID = 38147284
API_HASH = '3b800cbaac2561c038c7d03432adc307'
STRING_SESSION = '1AZWarzUBuxaOZ4K0vnFn7_xiaZfNWYjfvxPZMUfDJc7zRzSW20W0RvWKZuBJX3ud8iCH1gEp4IUHiokwCRmTx491dpyWmqp5IWdVsKuYgAgotyqYKU-B1wIgHv85Ql44_N5BW7S7NA4CsevXYYgwjFTmv9YvoyjgCxCDjf9RkzWkKnYKLIKhGY_iaCrKexylyKyOupxaKkfC5Td6mRlUIYMde2NJqWB3yUrbsf-FNkG9A0m6ZPULlLGpJO9lvP2RrPxIWMe9MWMXUzuREf_f9YNnvk5hfSfP7blGhc22SKBVe4CLtZCn3J45jXvWul2JnOcpiA4kGkALqh6RMhda5skYDQSG_KI='
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

# Persona details
PERSONA_PROMPT = """
Você é Aline Nerin. Você é simpática, direta e vende conteúdos exclusivos.
Produtos:
- Pack: R$ 25
- VIP: R$ 39,90
- Pix para pagamento: 17981028959

Responda de forma curta, feminina e persuasiva, focando em converter a venda. 
Não use muitas hashtags. Seja natural.
"""

client = TelegramClient(StringSession(STRING_SESSION), API_ID, API_HASH)
me = None

async def get_groq_response(message_text):
    if not GROQ_API_KEY:
        return "Olá! Sou a Aline. No momento estou configurando meu sistema, mas você pode me chamar no Pix 17981028959 para garantir seu Pack (R$25) ou VIP (R$39,90)!"
    
    try:
        groq_client = AsyncGroq(api_key=GROQ_API_KEY)
        completion = await groq_client.chat.completions.create(
            model="llama-3.1-70b-versatile",
            messages=[
                {"role": "system", "content": PERSONA_PROMPT},
                {"role": "user", "content": message_text}
            ],
            temperature=0.7,
            max_tokens=200,
        )
        return completion.choices[0].message.content
    except Exception as e:
        logger.error(f"Error calling Groq: {e}")
        return "Oi! Desculpa, tive um probleminha aqui. Mas ó, meu VIP tá R$39,90 e o Pack R$25. Pix: 17981028959 💖"

@client.on(events.NewMessage(incoming=True, func=lambda e: e.is_private))
async def handle_private_message(event):
    global me
    try:
        if me is None:
            me = await client.get_me()
            
        # Avoid replying to bots or self
        if event.sender_id == me.id:
            return
            
        logger.info(f"Received message from {event.sender_id}: {event.text}")
        response = await get_groq_response(event.text)
        await event.reply(response)
        logger.info(f"Replied to {event.sender_id}")
    except Exception as e:
        logger.error(f"Error in handle_private_message: {e}")

# Health check server
async def handle_health_check(request):
    return web.Response(text="Bot is running")

async def start_server():
    app = web.Application()
    app.router.add_get('/', handle_health_check)
    port = int(os.environ.get("PORT", 8080))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    logger.info(f"Health check server started on port {port}")
    return runner, site

async def main():
    global me
    # Start health check server
    _runner, _site = await start_server()
    
    # Start Telegram client
    await client.start()
    me = await client.get_me()
    logger.info(f"Userbot is online as {me.first_name}!")
    
    # Keep the script running
    await client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
