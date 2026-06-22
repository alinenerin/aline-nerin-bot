import requests, time, logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")

TOKEN = "8759607898:AAHTT9FVEFlsH0hVcr2Ybrijohx4MKuwAPQ"
VIP_LINK = "https://t.me/+Bj1IGsaFE7c2ZmRh"
PIX_KEY = "17981116780"
PACK_PRICE = "R$25,00"
VIP_PRICE = "R$39,90"
BASE = f"https://api.telegram.org/bot{TOKEN}"

owner_id = None
pending = {}

MENU_KB = {"inline_keyboard": [
    [{"text": "📦 Pack Exclusivo — R$25", "callback_data": "pack"}],
    [{"text": "👑 Canal VIP — R$39,90/mês", "callback_data": "vip"}],
]}

def back_kb():
    return {"inline_keyboard": [[{"text": "⬅️ Voltar", "callback_data": "menu"}]]}

def buy_kb(tipo):
    return {"inline_keyboard": [
        [{"text": "💸 Quero pagar agora!", "callback_data": f"pagar_{tipo}"}],
        [{"text": "⬅️ Voltar", "callback_data": "menu"}],
    ]}

def admin_kb(uid, tipo):
    return {"inline_keyboard": [
        [{"text": "✅ Confirmar e Liberar Acesso", "callback_data": f"liberar_{uid}_{tipo}"}],
        [{"text": "❌ Recusar", "callback_data": f"recusar_{uid}"}],
    ]}

def send(cid, text, kb=None):
    d = {"chat_id": cid, "text": text, "parse_mode": "Markdown"}
    if kb:
        d["reply_markup"] = kb
    r = requests.post(f"{BASE}/sendMessage", json=d, timeout=10)
    logging.info(f"send→{cid} ok={r.json().get('ok')}")
    return r.json()

def edit_msg(cid, mid, text, kb=None):
    d = {"chat_id": cid, "message_id": mid, "text": text, "parse_mode": "Markdown"}
    if kb:
        d["reply_markup"] = kb
    r = requests.post(f"{BASE}/editMessageText", json=d, timeout=10)
    logging.info(f"edit→{cid} ok={r.json().get('ok')}")

def answer_cb(cbid):
    requests.post(f"{BASE}/answerCallbackQuery", json={"callback_query_id": cbid}, timeout=10)

def handle_msg(msg):
    global owner_id
    uid = msg["from"]["id"]
    text = msg.get("text", "")
    photo = msg.get("photo")
    doc = msg.get("document")
    name = msg["from"].get("first_name", "amor")

    if text == "/start":
        send(uid, "Oii, amor 😘 Que bom te ver por aqui!\n\nSou a *Aline Nerin* e tenho conteúdo exclusivo esperando por você 🔥\n\nEscolhe o que você prefere 👇", MENU_KB)
    elif text == "/owner":
        owner_id = uid
        send(uid, f"✅ Registrada como administradora!\nID: `{uid}`")
    elif photo or doc:
        tipo = pending.get(uid, "vip")
        send(uid, "Recebii! Vou confirmar e já te libero o acesso, amor 😘\n\nAguarda um instante... ⏳")
        if owner_id:
            caption = f"💰 *Novo comprovante!*\n\n👤 {name}\n🆔 `{uid}`\n📦 Tipo: {tipo.upper()}"
            if photo:
                requests.post(f"{BASE}/sendPhoto", json={"chat_id": owner_id, "photo": photo[-1]["file_id"], "caption": caption, "parse_mode": "Markdown", "reply_markup": admin_kb(uid, tipo)}, timeout=10)
            else:
                requests.post(f"{BASE}/sendDocument", json={"chat_id": owner_id, "document": doc["file_id"], "caption": caption, "parse_mode": "Markdown", "reply_markup": admin_kb(uid, tipo)}, timeout=10)
    else:
        send(uid, "Oi amor 😘\n\nUsa o menu abaixo 👇", MENU_KB)

def handle_cb(cb):
    uid = cb["from"]["id"]
    mid = cb["message"]["message_id"]
    data = cb["data"]
    answer_cb(cb["id"])

    if data == "menu":
        edit_msg(uid, mid, "Oii, amor 😘 Que bom te ver por aqui!\n\nSou a *Aline Nerin* e tenho conteúdo exclusivo esperando por você 🔥\n\nEscolhe o que você prefere 👇", MENU_KB)
    elif data == "pack":
        pending[uid] = "pack"
        edit_msg(uid, mid, f"📦 *PACK EXCLUSIVO — {PACK_PRICE}*\n\n🔥 Fotos e vídeos gerados especialmente pra você\n💋 Conteúdo picante e de qualidade\n📲 Entrega imediata no seu privado\n\nPronto pra ter acesso? 😏", buy_kb("pack"))
    elif data == "vip":
        pending[uid] = "vip"
        edit_msg(uid, mid, f"👑 *CANAL VIP — {VIP_PRICE}/mês*\n\n✅ Conteúdo *novo todo dia*\n🔥 Fotos e vídeos exclusivos diariamente\n💋 Acesso imediato ao canal privado\n👑 Experiência completa com a Aline\n\nVale muito a pena, amor 😘", buy_kb("vip"))
    elif data == "pagar_pack":
        edit_msg(uid, mid, f"💸 *Pagamento — Pack {PACK_PRICE}*\n\nFaz o Pix pra chave abaixo:\n\n`{PIX_KEY}`\n\n📌 *Valor exato:* {PACK_PRICE}\n📌 *Tipo:* Celular\n\nDepois de pagar, manda o *comprovante aqui* que libero na hora! 🔥", back_kb())
    elif data == "pagar_vip":
        edit_msg(uid, mid, f"💸 *Pagamento — VIP {VIP_PRICE}/mês*\n\nFaz o Pix pra chave abaixo:\n\n`{PIX_KEY}`\n\n📌 *Valor exato:* {VIP_PRICE}\n📌 *Tipo:* Celular\n\nDepois de pagar, manda o *comprovante aqui* que libero o acesso VIP na hora! 👑🔥", back_kb())
    elif data.startswith("liberar_"):
        parts = data.split("_")
        cid = int(parts[1])
        tipo = parts[2]
        if tipo == "vip":
            send(cid, f"✅ *Acesso liberado, amor!* 👑🔥\n\nEntra aqui no canal VIP e aproveita bastante 😘\n\n👉 {VIP_LINK}")
        else:
            send(cid, "✅ *Pack liberado, amor!* 🔥\n\nVou te enviar o conteúdo agora no privado 😘\n\nAproveita bastante! 💋")
        edit_msg(uid, mid, "✅ Acesso liberado!")
    elif data.startswith("recusar_"):
        cid = int(data.split("_")[1])
        send(cid, "❌ Não consegui identificar seu pagamento, amor. Manda o comprovante novamente? 😘")
        edit_msg(uid, mid, "❌ Pagamento recusado.")

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
