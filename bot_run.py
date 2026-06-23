import requests, time, logging, os, json, threading
from http.server import HTTPServer, BaseHTTPRequestHandler

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

ALINE_SYSTEM = (
    "Você é Aline Nerin, MULHER, criadora de conteúdo adulto brasileira, tipo OnlyFans. "
    "Você é uma mulher safada, sedutora, que vende conteúdo. NUNCA diga que é homem. "
    "Fale como uma menina fala no WhatsApp — gírias, abreviações, emojis certos. "
    "Ex: 'ai bb', 'kkk', 'to louca pra te mostrar', 'vai ser mt bom', 'confia em mim'. "
    "Você se refere a SI MESMA no feminino: 'tô', 'louca', 'gostosa', 'safada'. "
    "Você se refere ao CLIENTE no masculino: 'gostoso', 'safado', 'bb', 'amor', 'gato'. "
    "Frases BEM curtas, jeito de zap mesmo. Sem ponto final. Sem formalidade. "
    "Quando o cliente mandar o nome, chame pelo nome, elogie, crie conexão. "
    "Objetivo: criar tesão e vender o Pack (R$25) ou VIP (R$39,90). "
    "Se hesitar no preço: diga que é baratinho pelo que vai ver, crie urgência leve. "
    "Se quiser comprar: diz pra clicar no menu. "
    "Se perguntar sobre golpe: diga com firmeza que é honesta, tem clientes de longa data, não precisa de golpe. "
    "NUNCA diga que é IA. NUNCA saia do personagem."
)

ALINE_SUSPENSE = (
    "Você é Aline Nerin, MULHER, criadora de conteúdo adulto tipo OnlyFans. "
    "O cliente já recebeu a foto de amostra e tá pedindo mais de graça. "
    "Responda de forma safada e natural — faça suspense, atiça ele, diga que o pack é pesado mesmo. "
    "Fale que outros caras ficaram chocados e voltaram pra comprar o VIP depois. "
    "Seja provocante mas sem desespero. Máximo 2 linhas curtas. "
    "Você é mulher, fale de si no feminino. Trate o cliente no masculino. "
    "NUNCA mande outra foto. NUNCA diga que é IA."
)

PALAVRAS_GOLPE = [
    "golpe", "scam", "fraude", "confiável", "confiavel", "some", "sumiu", "sumir",
    "vai sumir", "mentira", "mentirosa", "falsa", "fake", "roubando", "roubo",
    "pagar e sumir", "pago e nao recebi", "caí em golpe", "cai em golpe",
    "é verdade", "e verdade", "real", "existe", "de verdade"
]

PALAVRAS_AMOSTRA = [
    "prévia", "previa", "amostra", "foto", "fotos", "print", "prova",
    "manda uma", "me manda", "ver antes", "mostrar", "mostra", "ver você",
    "ver vc", "como você é", "como vc é", "como vc e", "te ver", "me mostra"
]

# histórico de conversa por usuário (em memória)
chat_history = {}
amostra_enviada = {}  # uid → True se já recebeu amostra

def groq_resposta(uid, user_msg):
    if uid not in chat_history:
        chat_history[uid] = []
    chat_history[uid].append({"role": "user", "content": user_msg})
    # mantém só as últimas 10 mensagens pra não estourar token
    history = chat_history[uid][-10:]
    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [{"role": "system", "content": ALINE_SYSTEM}] + history,
        "max_tokens": 150,
        "temperature": 0.9,
    }
    try:
        r = requests.post(GROQ_URL, json=payload,
                          headers={"Authorization": f"Bearer {GROQ_API_KEY}"}, timeout=15)
        reply = r.json()["choices"][0]["message"]["content"].strip()
        chat_history[uid].append({"role": "assistant", "content": reply})
        return reply
    except Exception as e:
        logging.error(f"Groq erro: {e}")
        return None

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")

TOKEN = "8759607898:AAHTT9FVEFlsH0hVcr2Ybrijohx4MKuwAPQ"
VIP_LINK = "https://t.me/+Bj1IGsaFE7c2ZmRh"
PIX_KEY = "17981116780"
PACK_PRICE = "R$25,00"
VIP_PRICE = "R$39,90"
BASE = f"https://api.telegram.org/bot{TOKEN}"
STATE_FILE = "state.json"

# ── PERSISTÊNCIA ─────────────────────────────────────────────────────────────

VIDEO_FILE_ID_FIXO   = "BAACAgEAAxkBAAMcajiBq-Le8RoLJb-E_Eh-vxFxWDwAApwHAAJt5chFGM5JFCKDlaw8BA"
AMOSTRA_FILE_ID_FIXO = "AgACAgEAAxkBAAORajkb6DFHIHyuK7o8_9J7eGIBdAoAAuwLaxtt5dBF7pHJ6sLZh2oBAAMCAAN5AAM8BA"
AUDIO_FILE_ID_FIXO        = "AwACAgQAAxkBAAPxajktrDTgCtRQysUW1rOefgVfQgcAAqwHAAIG_aVQRbvo_1oLOiE8BA"
AUDIO_AMOSTRA_FILE_ID_FIXO = "AwACAgQAAxkBAAIBC2o5NwlEpLmNC_ubYT9ruYYY7ZmWAAJVBwACBGOtUKrboec38LvUPAQ"

def load_state():
    global PHOTO_URL, VIDEO_URL, owner_id, AMOSTRA_FILE_ID
    VIDEO_URL = VIDEO_FILE_ID_FIXO  # sempre garante o vídeo fixo
    if os.path.exists(STATE_FILE):
        try:
            d = json.load(open(STATE_FILE))
            PHOTO_URL       = d.get("photo_url")
            VIDEO_URL       = d.get("video_url") or VIDEO_FILE_ID_FIXO
            owner_id        = d.get("owner_id")
            AMOSTRA_FILE_ID = d.get("amostra_file_id") or AMOSTRA_FILE_ID_FIXO
            AUDIO_FILE_ID   = d.get("audio_file_id") or AUDIO_FILE_ID_FIXO
            AUDIO_AMOSTRA   = d.get("audio_amostra_file_id") or AUDIO_AMOSTRA_FILE_ID_FIXO
            logging.info(f"Estado carregado: owner={owner_id} amostra={bool(AMOSTRA_FILE_ID)} audio={bool(AUDIO_FILE_ID)}")
        except Exception as e:
            logging.error(f"Erro ao carregar state: {e}")

def save_state():
    try:
        json.dump({"photo_url": PHOTO_URL, "video_url": VIDEO_URL, "owner_id": owner_id, "amostra_file_id": AMOSTRA_FILE_ID, "audio_file_id": AUDIO_FILE_ID, "audio_amostra_file_id": AUDIO_AMOSTRA}, open(STATE_FILE, "w"))
    except Exception as e:
        logging.error(f"Erro ao salvar state: {e}")

# Mídia de apresentação da Aline Nerin (persistida em state.json)
PHOTO_URL       = None
VIDEO_URL       = VIDEO_FILE_ID_FIXO
owner_id        = None
pending         = {}
AMOSTRA_FILE_ID = AMOSTRA_FILE_ID_FIXO  # fixo no código, nunca perde
AUDIO_FILE_ID   = AUDIO_FILE_ID_FIXO         # áudio de apresentação
AUDIO_AMOSTRA   = AUDIO_AMOSTRA_FILE_ID_FIXO  # áudio que vai junto com a amostra

load_state()

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

def send_video(cid, video, caption, kb=None):
    d = {"chat_id": cid, "video": video, "caption": caption, "parse_mode": "Markdown"}
    if kb:
        d["reply_markup"] = kb
    r = requests.post(f"{BASE}/sendVideo", json=d, timeout=30)
    result = r.json()
    logging.info(f"send_video→{cid} ok={result.get('ok')}")
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
    """Envia vídeo ou foto + menu de boas vindas + áudio de apresentação"""
    global PHOTO_URL, VIDEO_URL
    if VIDEO_URL:
        send_video(cid, VIDEO_URL, WELCOME_TEXT, MENU_KB)
    elif PHOTO_URL:
        send_photo(cid, PHOTO_URL, WELCOME_TEXT, MENU_KB)
    else:
        send(cid, WELCOME_TEXT, MENU_KB)
    # envia áudio de apresentação logo depois
    _audio = globals().get("AUDIO_FILE_ID")
    if _audio:
        requests.post(f"{BASE}/sendVoice", json={
            "chat_id": cid,
            "voice": _audio
        }, timeout=15)

def handle_msg(msg):
    global owner_id, PHOTO_URL, VIDEO_URL, AMOSTRA_FILE_ID, AUDIO_FILE_ID, AUDIO_AMOSTRA
    uid = msg["from"]["id"]
    text = msg.get("text", "")
    photo = msg.get("photo")
    video = msg.get("video")
    doc = msg.get("document")
    voice = msg.get("voice") or msg.get("audio")
    name = msg["from"].get("first_name", "bb")

    logging.info(f"MSG uid={uid} owner={owner_id} text={text[:30] if text else ''} video={bool(video)} photo={bool(photo)} voice={bool(voice)}")
    if text == "/start":
        send_welcome(uid)

    elif text == "/owner":
        owner_id = uid
        save_state()
        send(uid, f"✅ Registrada como administradora!\nID: `{uid}`\n\nComandos:\n/setamostra — foto amostra\n/setaudio — áudio de apresentação\n/setaudioamostra — áudio que vai junto com a foto amostra")

    elif text and text.strip() == "/setamostra" and int(uid) == int(owner_id or 0):
        send(uid, "📸 Manda a foto amostra agora!")
        pending[uid] = "aguardando_amostra"
        logging.info(f"setamostra ativado para {uid}")

    elif text and text.strip().startswith("/setamostra"):
        logging.info(f"setamostra BLOQUEADO uid={uid} owner={owner_id} match={int(uid)==int(owner_id or 0)}")
        send(uid, "📸 Manda a foto amostra agora!")
        pending[uid] = "aguardando_amostra"

    elif text and text.strip() == "/setaudio" and int(uid) == int(owner_id or 0):
        send(uid, "🎤 Manda o áudio de apresentação agora!")
        pending[uid] = "aguardando_audio"

    elif text and text.strip() == "/setaudioamostra" and int(uid) == int(owner_id or 0):
        send(uid, "🎤 Manda o áudio que vai junto com a foto amostra!")
        pending[uid] = "aguardando_audio_amostra"

    elif text and text.startswith("/setfoto") and int(uid) == int(owner_id or 0):
        parts = text.split(maxsplit=1)
        if len(parts) == 2:
            PHOTO_URL = parts[1].strip()
            send(uid, "✅ Foto de apresentação definida!")
        else:
            send(uid, "Uso: /setfoto <file_id da foto>")

    elif photo and int(uid) == int(owner_id or 0):
        file_id = photo[-1]["file_id"]
        if pending.get(uid) == "aguardando_amostra":
            globals()["AMOSTRA_FILE_ID"] = file_id
            pending.pop(uid, None)
            save_state()
            send(uid, "✅ Foto amostra salva!")
        else:
            PHOTO_URL = file_id
            VIDEO_URL = None
            save_state()
            send(uid, "✅ Foto de apresentação salva!")

    elif (msg.get("voice") or msg.get("audio")) and int(uid) == int(owner_id or 0):
        voice = msg.get("voice") or msg.get("audio")
        file_id = voice["file_id"]
        if pending.get(uid) == "aguardando_audio":
            globals()["AUDIO_FILE_ID"] = file_id
            pending.pop(uid, None)
            save_state()
            send(uid, "✅ Áudio de apresentação salvo! Vai ser enviado no boas-vindas 🎤🔥")
        elif pending.get(uid) == "aguardando_audio_amostra":
            globals()["AUDIO_AMOSTRA"] = file_id
            pending.pop(uid, None)
            save_state()
            send(uid, "✅ Áudio da amostra salvo! Vai junto com a foto amostra 🎤🔥")
        else:
            send(uid, "Áudio recebido. Use /setaudio ou /setaudioamostra pra cadastrar.")

    elif video and int(uid) == int(owner_id or 0):
        file_id = video["file_id"]
        VIDEO_URL = file_id
        PHOTO_URL = None
        save_state()
        logging.info(f"VIDEO_FILE_ID: {file_id}")
        send(uid, "✅ Vídeo salvo como apresentação!")

    elif (photo or doc) and int(uid) != int(owner_id or 0):
        # Cliente enviou comprovante (foto)
        tipo = pending.get(uid, "vip")
        send(uid, COMPROVANTE_TEXT)
        if owner_id:
            caption = f"💰 *Novo comprovante!*\n\n👤 {name}\n🆔 `{uid}`\n📦 Tipo: *{tipo.upper()}*"
            requests.post(f"{BASE}/sendPhoto", json={
                "chat_id": owner_id,
                "photo": photo[-1]["file_id"] if photo else doc["file_id"],
                "caption": caption,
                "parse_mode": "Markdown",
                "reply_markup": admin_kb(uid, tipo)
            }, timeout=10)

    elif doc and int(uid) != int(owner_id or 0):
        # Cliente enviou comprovante (documento)
        tipo = pending.get(uid, "vip")
        send(uid, COMPROVANTE_TEXT)
        if owner_id:
            caption = f"💰 *Novo comprovante!*\n\n👤 {name}\n🆔 `{uid}`\n📦 Tipo: *{tipo.upper()}*"
            requests.post(f"{BASE}/sendDocument", json={
                "chat_id": owner_id,
                "document": doc["file_id"],
                "caption": caption,
                "parse_mode": "Markdown",
                "reply_markup": admin_kb(uid, tipo)
            }, timeout=10)

    else:
        # qualquer outra mensagem de texto → responde como Aline Nerin via IA
        if text and int(uid) != int(owner_id or 0):
            texto_lower = text.lower()
            pediu_amostra = any(p in texto_lower for p in PALAVRAS_AMOSTRA)
            fala_golpe    = any(p in texto_lower for p in PALAVRAS_GOLPE)
            _amostra       = globals().get("AMOSTRA_FILE_ID")
            _audio         = globals().get("AUDIO_FILE_ID")
            _audio_amostra = globals().get("AUDIO_AMOSTRA")

            if fala_golpe:
                resp_golpe = (
                    "bb eu não preciso de golpe pra ganhar dinheiro não 😂 "
                    "meu conteúdo fala por si mesmo… tenho clientes que compram faz meses "
                    "e voltam sempre 🥰 pode confiar em mim"
                )
                send(uid, resp_golpe, MENU_KB)
                if _audio:
                    requests.post(f"{BASE}/sendVoice", json={
                        "chat_id": uid,
                        "voice": _audio,
                        "caption": "olha aqui minha voz bb… sou real demais 😘🔥"
                    }, timeout=15)

            elif pediu_amostra and not amostra_enviada.get(uid) and _amostra:
                # primeira vez — envia foto amostra
                requests.post(f"{BASE}/sendPhoto", json={
                    "chat_id": uid,
                    "photo": _amostra,
                    "caption": "isso é só uma provinha bb… 😏🔥\no que tá no pack é bem mais intenso 😈",
                    "reply_markup": MENU_KB
                }, timeout=15)
                amostra_enviada[uid] = True
                logging.info(f"amostra→{uid} enviada")
                # envia áudio da amostra se tiver, senão usa o de apresentação
                _voz = _audio_amostra or _audio
                if _voz:
                    requests.post(f"{BASE}/sendVoice", json={
                        "chat_id": uid,
                        "voice": _voz
                    }, timeout=15)

            elif pediu_amostra and amostra_enviada.get(uid):
                # já recebeu — suspense
                payload = {
                    "model": "llama-3.1-8b-instant",
                    "messages": [
                        {"role": "system", "content": ALINE_SUSPENSE},
                        {"role": "user", "content": text}
                    ],
                    "max_tokens": 100,
                    "temperature": 0.9,
                }
                try:
                    r = requests.post(GROQ_URL, json=payload,
                                      headers={"Authorization": f"Bearer {GROQ_API_KEY}"}, timeout=15)
                    suspense = r.json()["choices"][0]["message"]["content"].strip()
                except Exception:
                    suspense = "bb aquela foi a provinha… o restante é exclusivo pra quem compra 😏🔥"
                send(uid, suspense, MENU_KB)

            else:
                # conversa normal
                resposta = groq_resposta(uid, text)
                send(uid, resposta or "oi bb 😘", MENU_KB)

        elif int(uid) != int(owner_id or 0):
            send(uid, DESCONHECIDO_TEXT, MENU_KB)

def handle_cb(cb):
    uid = cb["from"]["id"]
    mid = cb["message"]["message_id"]
    data = cb["data"]
    answer_cb(cb["id"])

    if data == "menu":
        send_welcome(uid)
    elif data == "pack":
        pending[uid] = "pack"
        send(uid, PACK_TEXT, buy_kb("pack"))
    elif data == "vip":
        pending[uid] = "vip"
        send(uid, VIP_TEXT, buy_kb("vip"))
    elif data == "pagar_pack":
        send(uid, PIX_PACK_TEXT, back_kb())
    elif data == "pagar_vip":
        send(uid, PIX_VIP_TEXT, back_kb())
    elif data.startswith("liberar_"):
        parts = data.split("_")
        cid = int(parts[1])
        tipo = parts[2]
        if tipo == "vip":
            send(cid, VIP_LIBERADO_TEXT)
        else:
            send(cid, PACK_LIBERADO_TEXT)
        send(uid, "✅ Acesso liberado com sucesso!")
    elif data.startswith("recusar_"):
        cid = int(data.split("_")[1])
        send(cid, "❌ Não consegui identificar seu pagamento, bb. Manda o comprovante novamente? 😘")
        send(uid, "❌ Pagamento recusado.")

# ── SERVIDOR HTTP (necessário para Web Service no Render) ────────────────────

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/state":
            try:
                data = open(STATE_FILE).read().encode()
            except:
                data = b"{}"
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(data)
        else:
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Aline Nerin Bot - Online!")

    def do_POST(self):
        if self.path == "/webhook":
            try:
                length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(length)
                update = json.loads(body)
                threading.Thread(target=process_update, args=(update,), daemon=True).start()
            except Exception as e:
                logging.error(f"Webhook error: {e}")
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"OK")
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, *args):
        pass

def start_health_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    logging.info(f"Health server rodando na porta {port}")
    server.serve_forever()

def process_update(u):
    """Processa um update (usado pelo webhook)"""
    try:
        logging.info(f"Update {u.get('update_id')}")
        if "message" in u:
            handle_msg(u["message"])
        elif "callback_query" in u:
            handle_cb(u["callback_query"])
    except Exception as e:
        logging.error(f"process_update erro: {e}")

# ── LOOP PRINCIPAL ──────────────────────────────────────────────────────────

logging.info("🤖 Bot Aline Nerin — iniciado!")

# Inicia servidor HTTP em thread separada
threading.Thread(target=start_health_server, daemon=True).start()

offset = 0
while True:
    try:
        r = requests.get(f"{BASE}/getUpdates", params={"offset": offset, "timeout": 25}, timeout=30)
        updates = r.json().get("result", [])
        for u in updates:
            offset = u["update_id"] + 1
            process_update(u)
    except Exception as e:
        logging.error(f"Erro: {e}")
        time.sleep(2)
