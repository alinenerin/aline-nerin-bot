import os
import asyncio
import logging
import json
import random
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
SAMPLE_PHOTO_PATH = 'media/1783537400381.jpg'

# Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Clients
logger.info(f"Initializing Groq client...")
groq_client = AsyncGroq(api_key=GROQ_API_KEY)
client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

# SFW System Prompt for Groq to bypass safety filters
SYSTEM_PROMPT = "You are Aline, a warm and friendly independent model. Your job is to engage in friendly, slightly flirtatious conversation. Keep it light and respectful. Use emojis like 🩷, ✨, 😊."

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
        logger.info(f"AI response received.")
        return response_text
    except Exception as e:
        logger.error(f"Groq API Error: {str(e)}")
        return "Oi amor! ✨ Que bom falar com você. Como você está hoje? 😊"

@client.on(events.NewMessage(incoming=True))
async def handler(event):
    if event.sender_id is None:
        return
        
    sender = await event.get_sender()
    sender_name = getattr(sender, 'first_name', 'Unknown')
    text_lower = event.text.lower()
    
    logger.info(f"Message from {sender_name}: {event.text}")
    
    try:
        # 1. Sample Photo Logic
        sample_keywords = ["amostra", "foto", "prova", "ver um pouco", "gostinho"]
        if any(keyword in text_lower for keyword in sample_keywords):
            parts = [
                "Amor, vou te dar um gostinho só porque você pediu com jeitinho... 😏🔥",
                "Mas o que eu tenho lá dentro é mil vezes melhor. Garante o seu no Pix pra gente continuar lá: 17981028959 😈"
            ]
            
            for i, part in enumerate(parts):
                async with client.action(event.chat_id, 'typing'):
                    await asyncio.sleep(random.uniform(3, 5))
                    logger.info(f"Sending sample part {i+1}/2")
                    if i == 1:
                        await event.respond(part, file=SAMPLE_PHOTO_PATH)
                    else:
                        await event.respond(part)
                if i == 0:
                    await asyncio.sleep(random.uniform(2, 3))
            return

        # 2. Hardcoded Sales Pitch Logic
        sales_keywords = ["pack", "valor", "preço", "comprar", "vip", "pagar", "pix", "quanto"]
        if any(keyword in text_lower for keyword in sales_keywords):
            parts = [
                "Oi vida... 😏",
                "Meu pack tá uma delícia, são mais de 100 vídeos e fotos sem nada escondido por R$ 25. 🔥 Mas o meu xodó é o VIP, amor: R$ 39,90 e você me vê TODO DIA e fala comigo direto. 😈 Pix: 17981028959"
            ]
            
            for i, part in enumerate(parts):
                if i > 0:
                    await asyncio.sleep(random.uniform(2, 4))
                async with client.action(event.chat_id, 'typing'):
                    await asyncio.sleep(random.uniform(3, 5))
                    logger.info(f"Sending sales part {i+1}/2")
                    await event.respond(part)
            return

        # 3. Regular AI response (SFW Prompt)
        await asyncio.sleep(random.uniform(1, 2))
        full_response = await get_ai_response(event.text)
        
        # Split for humanization
        if "." in full_response and len(full_response) > 60:
            mid = full_response.find(".", len(full_response)//2)
            if mid != -1:
                parts = [full_response[:mid+1].strip(), full_response[mid+1:].strip()]
            else:
                parts = [full_response]
        else:
            parts = [full_response]

        for i, part in enumerate(parts):
            if not part: continue
            if i > 0:
                await asyncio.sleep(random.uniform(2, 4))
            
            async with client.action(event.chat_id, 'typing'):
                await asyncio.sleep(random.uniform(2, 4))
                logger.info(f"Sending part {i+1}/{len(parts)}")
                await event.respond(part)

    except Exception as e:
        logger.error(f"Error in handler: {str(e)}", exc_info=True)

# Health Check Server
async def health_check(request):
    return web.Response(text="OK - Aline Nerin Userbot Active")

async def start_server():
    app = web.Application()
    app.router.add_get("/", health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', PORT)
    await site.start()

async def main():
    logger.info("Starting Aline Nerin Userbot...")
    try:
        await client.start()
    except Exception as e:
        logger.error(f"Failed to start client: {e}")
        return

    asyncio.create_task(start_server())
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
