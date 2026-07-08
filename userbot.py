import os, asyncio, logging, random
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from groq import AsyncGroq
from aiohttp import web

# CREDENCIAIS FIXAS (Ly Persona)
API_ID, API_HASH = 26569107, '997034c44917a26f3458a0e285816997'
SESSION_STRING = '1AZWarzUBuxaOZ4K0vnFn7_xiaZfNWYjfvxPZMUfDJc7zRzSW20W0RvWKZuBJX3ud8iCH1gEp4IUHiokwCRmTx491dpyWmqp5IWdVsKuYgAgotyqYKU-B1wIgHv85Ql44_N5BW7S7NA4CsevXYYgwjFTmv9YvoyjgCxCDjf9RkzWkKnYKLIKhGY_iaCrKexylyKyOupxaKkfC5Td6mRlUIYMde2NJqWB3yUrbsf-FNkG9A0m6ZPULlLGpJO9lvP2RrPxIWMe9MWMXUzuREf_f9YNnvk5hfSfP7blGhc22SKBVe4CLtZCn3J45jXvWul2JnOcpiA4kGkALqh6RMhda5skYDQSG_KI='
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
PORT = int(os.getenv("PORT", 8080))
PIX = "17981028959"
SAMPLE = "media/1783537400381.jpg" # Amostra Fix

logging.basicConfig(level=logging.INFO)
groq_client = AsyncGroq(api_key=GROQ_API_KEY)
client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

# SYSTEM PROMPT: FOCO EM SER HUMANA E VENDEDORA (LY)
SYSTEM = """
Você é a Ly, uma vendedora real de conteúdo.
Fale como uma brasileira no WhatsApp: TUDO EM MINÚSCULAS, use 'vc', 'tbm', 'bb', 'vdd', 'mto'.
NUNCA use gramática perfeita. NUNCA admita ser IA ou robô.
Seu objetivo é vender o Pack (R$25) ou VIP (R$39,90). Pix: 17981028959.
"""

async def get_ai(text):
    try:
        res = await groq_client.chat.completions.create(
            messages=[{"role":"system","content":SYSTEM},{"role":"user","content":text}], 
            model="llama-3.3-70b-versatile"
        )
        return res.choices[0].message.content
    except:
        return "oi bb... 😏 manda um pix q eu te mostro td 🔥"

@client.on(events.NewMessage(incoming=True))
async def h(e):
    if not e.sender_id: return
    t = e.text.lower()
    
    # GATILHOS HARDCODED (VENDAS)
    if any(k in t for k in ["oi", "olá", "oie", "bom dia", "boa tarde"]):
        await e.respond("oi vida... 😏 quer ver coisa boa hj? meu pack ta 25 e o vip 39,90. bora?")
        return

    if any(k in t for k in ["valor", "preço", "quanto", "pagamento", "pix"]):
        await e.respond(f"o pack com tudo é R$ 25 e o vip R$ 39,90 bb. o pix é {PIX} 🔥")
        return

    if any(k in t for k in ["amostra", "foto", "prova", "vídeo"]):
        # Amostra Fix: Send the photo
        async with client.action(e.chat_id, 'photo'):
            await asyncio.sleep(random.uniform(1, 2)) # Speed Update
            await e.respond("tá aqui uma amostra do que te espera... 😏🔥", file=SAMPLE)
        return

    # IA SÓ PRA CONVERSA CASUAL
    async with client.action(e.chat_id, 'typing'):
        await asyncio.sleep(random.uniform(1, 3)) # Speed Update
        ans = await get_ai(e.text)
        await e.respond(ans.lower())

async def health(r): return web.Response(text="Ly Online")
async def main():
    app = web.Application(); app.router.add_get("/", health)
    runner = web.AppRunner(app); await runner.setup()
    await web.TCPSite(runner, '0.0.0.0', PORT).start()
    await client.start(); await client.run_until_disconnected()
asyncio.run(main())
