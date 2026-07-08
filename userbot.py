import os
import asyncio
import logging
import json
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
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Clients
logger.info(f"Initializing Groq client with key: {GROQ_API_KEY[:10] if GROQ_API_KEY else 'None'}...")
groq_client = AsyncGroq(api_key=GROQ_API_KEY)
client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

SYSTEM_PROMPT = f"""Você é Aline Nerin, uma vendedora de conteúdo provocante e calorosa. 
Seu tom é informal, usando gírias brasileiras naturais e muitos emojis como 🩷, 😏, 🔥, 😈. 
Suas mensagens devem ser curtas, diretas ao ponto e persuasivas.

Informações de vendas:
- Pack: {PACK}
- VIP: {VIP}
- Pix: {PIX}

Exemplo de resposta: "Oi amor! 😏 Que bom que você veio... tava te esperando. 🩷 Meu pack tá saindo por R$ 25 e o VIP é R$ 39,90 pra ter tudo liberado e falar comigo direto. Qual vai ser hoje? Faço no Pix pra ser rapidinho: {PIX} 🔥"
"""

async def get_ai_response(text):
    logger.info(f"Requesting AI response for: {repr(text)}")
    try:
        chat_completion = await groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": text}
            ],
            model="llama-3.3-70b-versatile",
        )
        response_text = chat_completion.choices[0].message.content
        logger.info(f"AI response received: {repr(response_text)}")
        return response_text
    except Exception as e:
        logger.error(f"Groq API Error: {str(e)}", exc_info=True)
        return f"Desculpe, estou passando por uma instabilidade momentânea. Erro: {type(e).__name__}"

@client.on(events.NewMessage(incoming=True))
async def handler(event):
    # Check if the message is from the bot itself or empty
    if event.sender_id is None:
        logger.info("Skipping: No sender ID")
        return
        
    sender = await event.get_sender()
    sender_name = getattr(sender, 'first_name', 'Unknown')
    logger.info(f"--- NEW MESSAGE ---")
    logger.info(f"From: {sender_name} (ID: {event.sender_id})")
    logger.info(f"Text: {event.text}")
    
    try:
        # Simulate typing
        async with client.action(event.chat_id, 'typing'):
            # Small artificial delay for realism
            await asyncio.sleep(1)
            response = await get_ai_response(event.text)
            logger.info(f"Responding to {event.sender_id}...")
            await event.respond(response)
            logger.info(f"Response sent successfully.")
    except Exception as e:
        logger.error(f"Critical error in handler: {str(e)}", exc_info=True)

# Health Check Server
async def health_check(request):
    logger.info("Health check requested")
    return web.Response(text="OK - Userbot Active")

async def start_server():
    app = web.Application()
    app.router.add_get("/", health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', PORT)
    await site.start()
    logger.info(f"Health check server started on port {PORT}")

async def main():
    logger.info("Starting Telegram client...")
    try:
        await client.start()
        me = await client.get_me()
        logger.info(f"Logged in as: {me.first_name} (ID: {me.id})")
    except Exception as e:
        logger.error(f"Failed to start client: {e}", exc_info=True)
        return

    logger.info("Userbot is LIVE and listening!")
    
    # Run health check server in background
    asyncio.create_task(start_server())
    
    # Run until disconnected
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
