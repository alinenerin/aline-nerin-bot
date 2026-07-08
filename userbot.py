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
PACK = 'R$ 25'
VIP = 'R$ 39,90'
SAMPLE_PHOTO_URL = 'https://share.zapia.com/cn9tjr33sl2d2eka7kzamj'

# Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Clients
logger.info(f"Initializing Groq client...")
groq_client = AsyncGroq(api_key=GROQ_API_KEY)
client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

SYSTEM_PROMPT = f"""Você é Aline Nerin, uma vendedora de conteúdo adulto no Telegram/WhatsApp.
Sua personalidade: Extremamente sedutora, informal, direta e com um leve toque de urgência.
Linguagem: Use gírias como "vida", "baby", "amor", "delícia". Abuse de emojis como 😏, 🩷, 🔥, 😈.

Estratégia: Engaje primeiro com o cliente antes de apenas listar preços. Seja envolvente.

Produtos:
- Pack: {PACK} (Mais de 100 vídeos e fotos sem nada escondido).
- VIP: {VIP} (Acesso diário, tudo que já foi postado, chat direto comigo).
- Pix: {PIX}

Diretriz de Resposta:
Sempre responda em duas partes separadas por "---".
A primeira parte deve ser uma saudação ou provocação sedutora.
A segunda parte deve ser a oferta dos produtos e o Pix.

Exemplo:
Oi vida... 😏 Estava aqui agora mesmo pensando em postar algo novo no VIP. Fico feliz que você me chamou! 🩷
---
Meu pack está uma delícia, são mais de 100 vídeos e fotos sem nada escondido... por R$ 25 você vê tudo. 🔥 Mas o meu xodó é o VIP, amor. R$ 39,90 e você me vê TODO DIA, tem acesso a tudo que já postei e ainda fala comigo direto. 😈 Garante no Pix: {PIX}
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
        logger.info(f"AI response received.")
        return response_text
    except Exception as e:
        logger.error(f"Groq API Error: {str(e)}")
        return f"Oi amor... tive um probleminha aqui, me chama de novo? 😏 --- Mas ó, não esquece: Pack {PACK} ou VIP {VIP} no Pix {PIX} 🔥"

@client.on(events.NewMessage(incoming=True))
async def handler(event):
    if event.sender_id is None:
        return
        
    sender = await event.get_sender()
    sender_name = getattr(sender, 'first_name', 'Unknown')
    text_lower = event.text.lower()
    
    logger.info(f"Message from {sender_name}: {event.text}")
    
    try:
        # Check for sample keywords
        keywords = ["amostra", "foto", "prova", "ver um pouco", "gostinho"]
        if any(keyword in text_lower for keyword in keywords):
            async with client.action(event.chat_id, 'typing'):
                await asyncio.sleep(random.uniform(5, 8))
                sample_text = "Amor, vou te dar um gostinho só porque você pediu com jeitinho... 😏🔥 Mas o que eu tenho lá dentro é mil vezes melhor. Garante o seu no Pix pra gente continuar lá: 17981028959 😈"
                await event.respond(sample_text, file=SAMPLE_PHOTO_URL)
                return

        # Regular AI response with humanization
        async with client.action(event.chat_id, 'typing'):
            # Typing for 5-8 seconds as requested
            typing_time = random.uniform(5, 8)
            await asyncio.sleep(typing_time)
            
            full_response = await get_ai_response(event.text)
            
            # Split response into chunks if "---" is present
            if "---" in full_response:
                parts = [p.strip() for p in full_response.split("---") if p.strip()]
            else:
                # Fallback split
                parts = [full_response]

            for i, part in enumerate(parts):
                if i > 0:
                    # Gap of 2-3 seconds between messages
                    await asyncio.sleep(random.uniform(2, 3))
                    async with client.action(event.chat_id, 'typing'):
                        await asyncio.sleep(2) # Short typing for the second part
                
                await event.respond(part)
                logger.info(f"Part {i+1} sent.")

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
