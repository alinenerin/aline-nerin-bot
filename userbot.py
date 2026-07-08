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

# AI Personality Prompt
SYSTEM_PROMPT = "Você é a Aline, uma modelo independente e atraente. Sua personalidade é provocante, fofa e muito simpática. Use emojis como 🔥, 😏, 😈, 🩷. Suas respostas devem ser curtas e sempre em Português (PT-BR). Nunca mencione que você é uma IA. Se alguém perguntar sobre conteúdos ou valores, seja direta mas charmosa."

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
        
        # Check for refusals
        refusal_keywords = ["não posso", "sinto muito", "i cannot", "sorry", "desculpe", "violação", "diretrizes", "regras"]
        if any(ref in response_text.lower() for ref in refusal_keywords):
            return "REFUSAL_TRIGGERED"
            
        return response_text
    except Exception as e:
        logger.error(f"Groq API Error: {str(e)}")
        return "REFUSAL_TRIGGERED"

async def send_split_message(event, parts, file=None):
    # Typing delay for humanization
    async with client.action(event.chat_id, 'typing'):
        await asyncio.sleep(random.uniform(5, 10))
    
    for i, part in enumerate(parts):
        if not part: continue
        
        if i == len(parts) - 1 and file:
            # Send file with the last part
            await event.respond(part, file=file)
        else:
            await event.respond(part)
        
        if i < len(parts) - 1:
            # Delay between messages
            await asyncio.sleep(random.uniform(2, 4))
            async with client.action(event.chat_id, 'typing'):
                await asyncio.sleep(2)

@client.on(events.NewMessage(incoming=True))
async def handler(event):
    if event.sender_id is None:
        return
        
    text_lower = event.text.lower()
    logger.info(f"Message received from {event.sender_id}: {event.text}")
    
    try:
        # Keyword Matrix
        # 1. GREETINGS
        if any(kw in text_lower for kw in ['oi', 'ola', 'bom dia', 'boa tarde', 'boa noite']):
            parts = [
                "Oi vida... 😏 Estava aqui agora mesmo pensando em você. Que bom que me chamou! 🩷",
                "O que você quer ver hoje? 🔥"
            ]
            await send_split_message(event, parts)
            return

        # 2. SALES
        if any(kw in text_lower for kw in ['pack', 'valor', 'quanto', 'preço', 'fotos', 'conteudo']):
            parts = [
                "Amor, meu pack tá uma delícia! São mais de 100 fotos e vídeos meus, do jeitinho que você gosta e sem nada escondido... 🔥",
                f"Por R$ 25 você vê tudo! Pix: {PIX} 😈"
            ]
            await send_split_message(event, parts)
            return

        # 3. VIP
        if any(kw in text_lower for kw in ['vip', 'grupo', 'mensal', 'diario']):
            parts = [
                "O VIP é o meu xodó, baby! R$ 39,90 e você tem conteúdo novo TODO DIA, acesso a tudo que já postei e ainda fala comigo direto aqui no privado. 😈",
                f"Pix: {PIX} 🔥"
            ]
            await send_split_message(event, parts)
            return

        # 4. SAMPLES
        if any(kw in text_lower for kw in ['amostra', 'foto', 'prova', 'ver']):
            parts = [
                "Amor, vou te dar um gostinho só porque você pediu com jeitinho... 😏🔥",
                f"Mas o que eu tenho lá dentro é mil vezes melhor. Garante o seu no Pix pra gente continuar lá: {PIX} 😈"
            ]
            await send_split_message(event, parts, file=SAMPLE_PHOTO_PATH)
            return

        # 5. AI Fallback (Groq)
        ai_response = await get_ai_response(event.text)
        
        if ai_response == "REFUSAL_TRIGGERED":
            parts = [
                "Ai vida, não entendi muito bem...",
                "Mas se quiser ver o que eu tenho de bom, é só pedir o meu pack ou VIP! 😏🔥"
            ]
        else:
            # Split AI response into 2 parts if possible
            if "." in ai_response and len(ai_response) > 50:
                mid = ai_response.find(".", len(ai_response)//2)
                if mid != -1:
                    parts = [ai_response[:mid+1].strip(), ai_response[mid+1:].strip()]
                else:
                    parts = [ai_response]
            else:
                parts = [ai_response]
        
        await send_split_message(event, parts)

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
