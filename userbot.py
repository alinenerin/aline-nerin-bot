import os, asyncio, logging, random, aiohttp
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from aiohttp import web

# CONFIGURAÇÕES DE ACESSO
API_ID, API_HASH = 26569107, '997034c44917a26f3458a0e285816997'
SESSION_STRING = '1AZWarzUBuxaOZ4K0vnFn7_xiaZfNWYjfvxPZMUfDJc7zRzSW20W0RvWKZuBJX3ud8iCH1gEp4IUHiokwCRmTx491dpyWmqp5IWdVsKuYgAgotyqYKU-B1wIgHv85Ql44_N5BW7S7NA4CsevXYYgwjFTmv9YvoyjgCxCDjf9RkzWkKnYKLIKhGY_iaCrKexylyKyOupxaKkfC5Td6mRlUIYMde2NJqWB3yUrbsf-FNkG9A0m6ZPULlLGpJO9lvP2RrPxIWMe9MWMXUzuREf_f9YNnvk5hfSfP7blGhc22SKBVe4CLtZCn3J45jXvWul2JnOcpiA4kGkALqh6RMhda5skYDQSG_KI='
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
PORT = int(os.getenv("PORT", 8080))
PIX, SAMPLE = '17981028959', 'media/1783537400381.jpg'

logging.basicConfig(level=logging.INFO)
client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

# PERSONA LY - CARINHOSA E SEDUTORA
SYSTEM_PROMPT = """
Você é a Ly, uma vendedora brasileira real, carinhosa e sensual de conteúdo adulto.
NUNCA use termos agressivos como 'paga e seca'. Seja doce, envolvente e carinhosa.
Fale como uma mulher real: use 'vc', 'tbm', 'bb', 'vdd', 'mto', 'vida', 'anjo', 'baby', tudo em minúsculas.
Se alguém te acusar de golpe (golpe, fake, mentira), defenda-se com doçura: diga que você é séria, valoriza mto seus assinantes e jamais enganaria ninguém porque preza mto pela sua reputação e pelo carinho deles.
Seja provocante, flerte e foque em levar o cliente para o seu Pack de R$25 (fotos + vídeos + vídeo chamada) ou VIP de R$39,90. Pix: 17981028959.
"""

FALLBACKS = [
    "ai vida, me conta mais no vip... 😈 lá eu te mostro tudo sem censura, anjo! garante o pix: 17981028959",
    "meu amor, vc fala mto... rsrs. pq não aproveita logo o meu pack de R$25 com video chamada? tá uma delícia! 😈",
    "bb, eu fico toda arrepiada com o jeito que vc fala... 😈 mas o que eu tenho no vip é ainda melhor, quer ver?",
    "anjo, se vc soubesse o que eu tô fazendo agora... 😏 vem pro meu vip que eu te mostro tudo! 🩷"
]

async def get_uncensored_ai(text):
    if not OPENROUTER_API_KEY: return random.choice(FALLBACKS)
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "mistralai/pixtral-12b:free",
        "messages": [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": text}]
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload, timeout=10) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data['choices'][0]['message']['content']
    except: pass
    return random.choice(FALLBACKS)

@client.on(events.NewMessage(incoming=True, func=lambda e: e.is_private))
async def handle_message(e):
    text = (e.text or "").lower()
    
    # 1. BOT DE VENDAS (PIX)
    if any(k in text for k in ["valor", "preço", "quanto", "pix", "pagar", "pagamento", "comprar", "vip", "pack"]):
        async with client.action(e.chat_id, 'typing'):
            await asyncio.sleep(random.uniform(1, 2))
            await e.respond("ai vida, no meu pack de R$ 25 já vem tudo: fotos, muitos vídeos e a gente ainda faz uma video chamada pra vc me ver todinha ao vivo... 🩷 vc vai amar, anjo! garante no pix: 17981028959")
            return

    if any(k in text for k in ["chamada", "videochamada", "call", "ver ao vivo", "ligação", "video call"]):
        async with client.action(e.chat_id, 'typing'):
            await asyncio.sleep(random.uniform(1, 2))
            await e.respond("ai que delícia, vida! 😈 no meu pack de R$ 25 ya vem tudo: fotos, muitos vídeos e a gente ainda faz uma video chamada pra vc me ver todinha ao vivo... 🩷 vc vai amar, anjo! garante no pix: 17981028959")
            return

    if any(k in text for k in ["amostra", "foto", "prova", "foto agora", "sim", "me mostra"]):
        async with client.action(e.chat_id, 'typing'):
            await asyncio.sleep(random.uniform(1, 2))
            await e.respond("olha um gostinho do q tem lá no vip, vida... 😏🔥")
            await asyncio.sleep(1)
            f = SAMPLE if os.path.exists(SAMPLE) else None
            await e.respond("mas no vip é mto melhor, bb! garante no pix q te mando o link: 17981028959 😈", file=f)
            return

    # 3. PAPO SEM CENSURA (OPENROUTER)
    async with client.action(e.chat_id, 'typing'):
        await asyncio.sleep(random.uniform(2, 4))
        ai_reply = await get_uncensored_ai(e.text)
        await e.respond(ai_reply.lower())

async def health(r): return web.Response(text="Ly VideoChamada Online")

async def main():
    server = web.Application()
    server.router.add_get("/", health)
    runner = web.AppRunner(server)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', PORT)
    await site.start()
    logging.info(f"Health check running on port {PORT}")
    
    await client.connect()
    logging.info("Telethon client connected")
    if not await client.is_user_authorized():
        logging.error("Session is NOT authorized! Please check SESSION_STRING.")
    else:
        logging.info("Session is authorized!")
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
