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
Seja provocante, flerte e foque em levar o cliente para o seu Pack de R$25 ou VIP de R$39,90.
"""

async def get_uncensored_ai(text):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "cognitivecomputations/dolphin-mistral-24b-venice-edition:free",
        "messages": [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": text}]
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as resp:
                data = await resp.json()
                return data['choices'][0]['message']['content']
    except: return "ai baby... 😏 vc me deixa louca. quer ver o que eu tenho de bom pra vc hj, anjo? 🔥"

@client.on(events.NewMessage(incoming=True))
async def handle_message(e):
    if not e.sender_id: return
    text = e.text.lower()
    
    # 1. DEFESA CONTRA ACUSAÇÃO DE GOLPE
    if any(k in text for k in ["golpe", "fake", "mentira", "enganando", "scam", "roubo"]):
        async with client.action(e.chat_id, 'typing'):
            await asyncio.sleep(random.uniform(1, 2))
            await e.respond("poxa vida, não fala assim... 🥺 eu sou super séria com meu trabalho e valorizo mto cada um de vcs. eu jamais faria algo pra te enganar, anjo, prezo mto pela minha reputação e pelo carinho que recebo aqui. pode confiar em mim, bb. 🩷")
            return

    # 2. TEXTOS DA LY (HARDCODED - SEM IA)
    if any(k in text for k in ["oi", "ola", "eai", "olá", "oii"]):
        async with client.action(e.chat_id, 'typing'):
            await asyncio.sleep(random.uniform(1, 2))
            await e.respond("oi, baby! 😏 acabei de receber sua mensagem e já estou pensando em como posso te fazer feliz, vida... 🩷 estou toda animada para saber o que você está procurando, anjo! 😈")
            return

    if any(k in text for k in ["como funciona", "valor", "preço", "quanto", "pack", "vip", "pix"]):
        async with client.action(e.chat_id, 'typing'):
            await asyncio.sleep(random.uniform(1, 3))
            await e.respond("meu amor, tenho exatamente o que você precisa! 🤗 meu pack é uma delícia, vem com mais de 100 vídeos e fotos sem nada escondido, tudo por R$ 25, vida. 🔥")
            await asyncio.sleep(1)
            await e.respond("mas, se você quer o melhor, o vip é o caminho, anjo! por R$ 39,90, você ganha acesso diário, tudo que já postei e ainda tem chat direto comigo, eu mesma! 😏 não perca tempo, bb, garante já no pix: 17981028959")
            return

    if any(k in text for k in ["amostra", "foto", "prova", "foto agora"]):
        async with client.action(e.chat_id, 'typing'):
            await asyncio.sleep(random.uniform(1, 2))
            await e.respond("olha um gostinho do q tem lá no vip, vida... 😏🔥")
            await asyncio.sleep(1)
            await e.respond("mas no vip é mto melhor, bb! garante no pix q te mando o link: 17981028959 😈", file=SAMPLE)
            return

    # 3. PAPO SEM CENSURA (OPENROUTER DOLPHIN)
    async with client.action(e.chat_id, 'typing'):
        await asyncio.sleep(random.uniform(2, 4))
        ai_reply = await get_uncensored_ai(e.text)
        
        # Filtro final para garantir que não saia bobagem de ajuda
        if any(m in ai_reply.lower() for m in ["ajudar", "específico", "novidade legal", "assistente"]):
            ai_reply = "ai vida, deixa de papo furado e vem ver o que eu tenho de bom pra vc, anjo... 😏🔥"
        
        await e.respond(ai_reply.lower())

async def health(r): return web.Response(text="Ly Carinhosa Online")
async def main():
    app = web.Application(); app.router.add_get("/", health)
    runner = web.AppRunner(app); await runner.setup()
    await web.TCPSite(runner, '0.0.0.0', PORT).start()
    await client.start(); await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
