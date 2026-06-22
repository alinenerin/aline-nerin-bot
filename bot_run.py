import requests, time, logging, os

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")

TOKEN = "8759607898:AAHTT9FVEFlsH0hVcr2Ybrijohx4MKuwAPQ"
VIP_LINK = "https://t.me/+Bj1IGsaFE7c2ZmRh"
PIX_KEY = "17981116780"
PACK_PRICE = "R$25,00"
VIP_PRICE = "R$39,90"
BASE = f"https://api.telegram.org/bot{TOKEN}"

# Foto de apresentação da Aline Nerin (URL pública ou file_id do Telegram)
PHOTO_URL = None  # Será preenchido com file_id após primeiro envio

owner_id = None
pending = {}

MENU_KB = {"inline_keyboard": [
    [{"text": "🔥 Pack Exclusivo — R$25", "callback_data": "pack"}],
    [{"text": "👑 Canal VIP — R$39,90/mês", "callback_data": "vip"}],
]}

def back_kb():
    return {"inline_keyboard": [[{"text": "⬅️ Voltar", "callback_data": "menu"}]]}

def buy_kb(tipo):
    return {"inline_keyboard": [
        [{"text": "💸 Quero pagar agora 😈", "callback_data": f"pagar_{tipo}"}],
        [{"text": "⬅️ Voltar", "callback_data": "menu"}],
    ]}

def admin_kb(uid, tipo):
    return {"inline_keyboard": [
        [{"text": "✅ Confirmar e Liberar Acesso", "callback_data": f"liberar_{uid}_{tipo}"}],
        [{"text": "❌ Recusar", "callback_data": f"recusar_{uid}"}],
    ]}

# ── TEXTOS CONVERTEDORES ────────────────────────────────────────────────────

WELCOME_TEXT = (
    "Oi bb 😏 Você caiu no lugar certo…\n\n"
    "Sou a *Aline Nerin* e aqui eu não tenho vergonha de nada 🔥\n\n"
    "Tenho conteúdo exclusivo esperando por você… "
    "Fotos e vídeos que você não vai encontrar em nenhum outro lugar 😈\n\n"
    "O que você prefere, gostoso? 👇"
)

PACK_TEXT = (
    "📦 *PACK EXCLUSIVO — R$25*\n\n"
    "Aquele conteúdo que eu guardo só pra quem merece… 😏\n\n"
    "🔥 Fotos e vídeos bem safadinhos\n"
    "💋 Do jeitinho que você tá imaginando\n"
    "📲 Cai no seu privado na hora\n\n"
    "Preparado pra ver tudo? 😈"
)

VIP_TEXT = (
    "👑 *CANAL VIP — R$39,90/mês*\n\n"
    "Aqui é onde a *Aline Nerin* solta o jogo de verdade… 🔥\n\n"
    "✅ Conteúdo *novo todo dia* — fotos e vídeos exclusivos\n"
    "🔞 Sem censura, sem filtro\n"
    "💋 Acesso imediato ao canal privado\n"
    "😈 Uma experiência que você não vai querer perder\n\n"
    "Bora, bb? 👇"
)

PIX_PACK_TEXT = (
    "💸 *Pagamento — Pack R$25*\n\n"
    "Faz o Pix e em segundos o conteúdo tá no seu privado 😈\n\n"
    "🔑 Chave Pix:\n`{pix}`\n\n"
    "📌 Valor: *R$25,00*\n"
    "📌 Tipo: Celular\n\n"
    "Depois manda o *comprovante aqui* que libero na hora 🔥"
).format(pix=PIX_KEY)

PIX_VIP_TEXT = (
    "💸 *Pagamento — VIP R$39,90/mês*\n\n"
    "Um mês inteiro de conteúdo novo todo dia… vale cada centavo 😏\n\n"
    "🔑 Chave Pix:\n`{pix}`\n\n"
    "📌 Valor: *R$39,90*\n"
    "📌 Tipo: Celular\n\n"
    "Manda o *comprovante aqui* que libero seu acesso VIP na hora 👑🔥"
).format(pix=PIX_KEY)

COMPROVANTE_TEXT = (
    "Recebi bb 😘\n\n"
    "Deixa eu confirmar aqui e já libero tudo pra você… ⏳🔥"
)

VIP_LIBERADO_TEXT = (
    "✅ *Acesso liberado, gostoso!* 👑🔥\n\n"
    "Entra aqui e aproveita cada detalhe 😈\n\n"
    "👉 {link}\n\n"
    "Qualquer coisa me chama no privado 💋"
).format(link=VIP_LINK)

PACK_LIBERADO_TEXT = (
    "✅ *Pack liberado, bb!* 🔥\n\n"
    "Vou mandar tudo no seu privado agora 😈\n\n"
    "Aproveita bastante… e se quiser mais, você sabe onde me achar 💋"
)

DESCONHECIDO_TEXT = (
    "Oi bb 😏\n\n"
    "Usa o menu abaixo pra ver o que tenho pra você 🔥👇"
)

# ── FUNÇÕES ─────────────────────────────────────────────────────────────────

def send(cid, text, kb=None):
    d = {"chat_id": cid, "text": text, "parse_mode": "Markdown"}
    if kb:
        d["reply_markup"] = kb
    r = requests.post(f"{BASE}/sendMessage", json=d, timeout=10)
    logging.info(f"send→{cid} ok={r.json().get('ok')}")
    return r.json()

def send_photo(cid, photo, caption, kb=None):
    d = {"chat_id": cid, "photo": photo, "caption": caption, "parse_mode": "Markdown"}
    if kb:
        d["reply_markup"] = kb
    r = requests.post(f"{BASE}/sendPhoto", json=d, timeout=15)
    result = r.json()
    logging.info(f"send_photo→{cid} ok={result.get('ok')}")
    return result

def edit_msg(cid, mid, text, kb=None):
    d = {"chat_id": cid, "message_id": mid, "text": text, "parse_mode": "Markdown"}
    if kb:
        d["reply_markup"] = kb
    r = requests.post(f"{BASE}/editMessageText", json=d, timeout=10)
    logging.info(f"edit→{cid} ok={r.json().get('ok')}")

def answer_cb(cbid):
    requests.post(f"{BASE}/answerCallbackQuery", json={"callback_query_id": cbid}, timeout=10)

def send_welcome(cid):
    """Envia foto + menu de boas vindas"""
    global PHOTO_URL
    if PHOTO_URL:
        send_photo(cid, PHOTO_URL, WELCOME_TEXT, MENU_KB)
    else:
        send(cid, WELCOME_TEXT, MENU_KB)

def handle_msg(msg):
    global owner_id, PHOTO_URL
    uid = msg["from"]["id"]
    text = msg.get("text", "")
    photo = msg.get("photo")
    doc = msg.get("document")
    name = msg["from"].get("first_name", "bb")

    if text == "/start":
        send_welcome(uid)

    elif text == "/owner":
        owner_id = uid
        send(uid, f"✅ Registrada como administradora!\nID: `{uid}`\n\nAgora você recebe todos os comprovantes aqui 🔥")

    elif text and text.startswith("/setfoto") and uid == owner_id:
        # /setfoto <file_id> — define a foto de apresentação
        parts = text.split(maxsplit=1)
        if len(parts) == 2:
            PHOTO_URL = parts[1].strip()
            send(uid, "✅ Foto de apresentação definida!")
        else:
            send(uid, "Uso: /setfoto <file_id da foto>")

    elif photo and uid == owner_id:
        # Dona enviou foto → usar como apresentação
        file_id = photo[-1]["file_id"]
        PHOTO_URL = file_id
        send(uid, f"✅ Foto salva como apresentação do bot!\n\nfile_id: `{file_id}`")

    elif photo or doc:
        # Cliente enviou comprovante
        tipo = pending.get(uid, "vip")
        send(uid, COMPROVANTE_TEXT)
        if owner_id:
            caption = f"💰 *Novo comprovante!*\n\n👤 {name}\n🆔 `{uid}`\n📦 Tipo: *{tipo.upper()}*"
            if photo:
                requests.post(f"{BASE}/sendPhoto", json={
                    "chat_id": owner_id,
                    "photo": photo[-1]["file_id"],
                    "caption": caption,
                    "parse_mode": "Markdown",
                    "reply_markup": admin_kb(uid, tipo)
                }, timeout=10)
            else:
                requests.post(f"{BASE}/sendDocument", json={
                    "chat_id": owner_id,
                    "document": doc["file_id"],
                    "caption": caption,
                    "parse_mode": "Markdown",
                    "reply_markup": admin_kb(uid, tipo)
                }, timeout=10)
    else:
        send(uid, DESCONHECIDO_TEXT, MENU_KB)

def handle_cb(cb):
    uid = cb["from"]["id"]
    mid = cb["message"]["message_id"]
    data = cb["data"]
    answer_cb(cb["id"])

    if data == "menu":
        edit_msg(uid, mid, WELCOME_TEXT, MENU_KB)
    elif data == "pack":
        pending[uid] = "pack"
        edit_msg(uid, mid, PACK_TEXT, buy_kb("pack"))
    elif data == "vip":
        pending[uid] = "vip"
        edit_msg(uid, mid, VIP_TEXT, buy_kb("vip"))
    elif data == "pagar_pack":
        edit_msg(uid, mid, PIX_PACK_TEXT, back_kb())
    elif data == "pagar_vip":
        edit_msg(uid, mid, PIX_VIP_TEXT, back_kb())
    elif data.startswith("liberar_"):
        parts = data.split("_")
        cid = int(parts[1])
        tipo = parts[2]
        if tipo == "vip":
            send(cid, VIP_LIBERADO_TEXT)
        else:
            send(cid, PACK_LIBERADO_TEXT)
        edit_msg(uid, mid, "✅ Acesso liberado com sucesso!")
    elif data.startswith("recusar_"):
        cid = int(data.split("_")[1])
        send(cid, "❌ Não consegui identificar seu pagamento, bb. Manda o comprovante novamente? 😘")
        edit_msg(uid, mid, "❌ Pagamento recusado.")

# ── LOOP PRINCIPAL ──────────────────────────────────────────────────────────

logging.info("🤖 Bot Aline Nerin — iniciado!")
offset = 0
while True:
    try:
        r = requests.get(f"{BASE}/getUpdates", params={"offset": offset, "timeout": 25}, timeout=30)
        updates = r.json().get("result", [])
        for u in updates:
            offset = u["update_id"] + 1
            logging.info(f"Update {u['update_id']}")
            if "message" in u:
                handle_msg(u["message"])
            elif "callback_query" in u:
                handle_cb(u["callback_query"])
    except Exception as e:
        logging.error(f"Erro: {e}")
        time.sleep(2)
