import os, asyncio, logging, random
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from groq import AsyncGroq
from aiohttp import web

API_ID, API_HASH = 26569107, '997034c44917a26f3458a0e285816997'
SESSION_STRING = '1AZWarzUBuxaOZ4K0vnFn7_xiaZfNWYjfvxPZMUfDJc7zRzSW20W0RvWKZuBJX3ud8iCH1gEp4IUHiokwCRmTx491dpyWmqp5IWdVsKuYgAgotyqYKU-B1wIgHv85Ql44_N5BW7S7NA4CsevXYYgwjFTmv9YvoyjgCxCDjf9RkzWkKnYKLIKhGY_iaCrKexylyKyOupxaKkfC5Td6mRlUIYMde2NJqWB3yUrbsf-FNkG9A0m6ZPULlLGpJO9lvP2RrPxIWMe9MWMXUzuREf_f9YNnvk5hfSfP7blGhc22SKBVe4CLtZCn3J45jXvWul2JnOcpiA4kGkALqh6RMhda5skYDQSG_KI='
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
PORT = int(os.getenv("PORT", 8080))
PIX, SAMPLE = '17981028959', 'media/1783537400381.jpg'

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
groq_client = AsyncGroq(api_key=GROQ_API_KEY)
client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

SYSTEM = "Você é Aline, uma modelo brasileira simpática e envolvente. Responda SEMPRE em português do Brasil com gírias naturais e emojis (🩷, ✨). Seja charmosa e direta."

async def get_ai(text):
    try:
        res = await groq_client.chat.completions.create(messages=[{"role":"system","content":SYSTEM},{"role":"user","content":text}], model="llama-3.3-70b-versatile")
        return res.choices[0].message.content
    except: return "Oi vida... 😏 Me chamou na hora certa. O que quer ver hoje? 🔥"

@client.on(events.NewMessage(incoming=True))
async def h(e):
    if not e.sender_id: return
    t = e.text.lower()
    if any(k in t for k in ["amostra", "foto", "prova"]):
        async with client.action(e.chat_id, 'typing'):
            await asyncio.sleep(6)
            await e.respond("Amor, olha um gostinho do que te espera... 😏🔥")
            await asyncio.sleep(3)
            await e.respond("Mas no VIP é mil vezes melhor! Garante no Pix: 17981028959 😈", file=SAMPLE)
        return
    if any(k in t for k in ["pack", "valor", "preço", "vip", "pix", "quanto"]):
        async with client.action(e.chat_id, 'typing'):
            await asyncio.sleep(6)
            await e.respond("Oi vida... 😏 Meu pack (100+ conteúdos) é R$ 25 e o VIP (diário) é R$ 39,90. 😈 Pix: 17981028959 🔥")
        return
    async with client.action(e.chat_id, 'typing'):
        await asyncio.sleep(6)
        ans = await get_ai(e.text)
        if any(m in ans.lower() for m in ["não posso", "cannot", "impróprio"]):
            ans = "Ai vida, não entendi bem... 😏 mas se quiser ver coisa boa, pede meu pack ou VIP! 🔥😈"
        await e.respond(ans)

async def health(r): return web.Response(text="OK")
async def main():
    app = web.Application(); app.router.add_get("/", health)
    runner = web.AppRunner(app); await runner.setup()
    await web.TCPSite(runner, '0.0.0.0', PORT).start()
    await client.start(); await client.run_until_disconnected()
asyncio.run(main())
