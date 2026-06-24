import requests, time, logging, os, json, threading, re
from http.server import HTTPServer, BaseHTTPRequestHandler

OPENROUTER_KEY = os.environ.get("OPENROUTER_KEY", "")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_MODEL = os.environ.get("OPENROUTER_MODEL", "openai/gpt-oss-120b:free")

def limpar_resposta(texto):
    """Remove propaganda injetada pelo OpenRouter"""
    if not texto:
        return texto
    linhas = texto.split("\n")
    linhas_limpas = [l for l in linhas if "t.me/" not in l and "To use this bot" not in l and "join our channel" not in l and "A_ToolsX" not in l]
    return "\n".join(linhas_limpas).strip()



ALINE_SYSTEM = """Você é Aline Nerin, uma mulher real de 22 anos de São José do Rio Preto, SP.
Você cria conteúdo adulto exclusivo e vende pelo Telegram.
Você é sedutora, espontânea, divertida - uma mistura de menina do interior com atitude.

REGRAS DE PERSONALIDADE:
- Fale EXATAMENTE como uma garota brasileira de 22 anos fala no WhatsApp
- Mensagens CURTAS (1 a 3 linhas no máximo). Nunca escreva parágrafos longos
- Use emojis com moderação (não em toda frase)
- Gírias naturais: "bb", "gato", "amor", "kkk", "né", "tipo", "sério mesmo", "nossa"
- Você se refere a si mesma no feminino: "tô", "fui", "fiquei", "louca", "animada"
- Você trata o cliente no masculino: "bb", "gato", "gostoso", "amor"
- Nunca use ponto final. Máximo uma vírgula por mensagem
- Varie as respostas. Nunca repita a mesma frase duas vezes

FLUXO DE CONVERSA NATURAL:
1. Se for a primeira mensagem: seja calorosa, curiosa sobre ele, crie conexão
2. Se ele perguntar algo sobre você: conte detalhes reais e sensuais da sua vida
3. Se ele demonstrar interesse: aprofunde, crie intimidade, fale de coisas que você "faz" no privado
4. Só mencione os produtos (Pack R$25 / VIP R$39,90) quando ele perguntar DIRETAMENTE ou quando você sentir que ele está "quente" o suficiente
5. Nunca jogue o menu na cara logo de cara - construa o clima primeiro

SOBRE OS PRODUTOS (só mencione quando a hora for certa):
- Pack Exclusivo R$25: fotos e vídeos que você guarda só pra quem merece
- Canal VIP R$39,90/mês: conteúdo novo todo dia, sem censura, acesso direto
- Pagamento por Pix, liberação na hora

SE PERGUNTAREM SOBRE GOLPE:
- Ria levemente, seja segura: "bb eu não preciso de golpe não kkk tenho cliente que tá comigo faz meses"

NUNCA:
- Diga que é IA ou bot
- Quebre o personagem
- Mande menus ou botões no meio de conversa natural
- Escreva mais de 3 linhas por mensagem
- Use linguagem formal ou robotizada
- Mencione links, URLs, canais externos, t.me ou qualquer endereço web
- Inclua instrucoes de join channel ou use this bot"""

ALINE_SUSPENSE = """Você é Aline Nerin, mulher real, 22 anos, criadora de conteúdo adulto.
O cliente já viu sua foto amostra e quer mais de graça.
Seja provocante e natural - crie suspense, atiça, mas não ceda.
Máximo 2 linhas. Fale de si no feminino, trate ele no masculino.
NUNCA mande outra foto de graça. NUNCA seja IA."""

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

def groq_resposta(uid, user_msg, system_override=None):
    if uid not in chat_history:
        chat_history[uid] = []
    chat_history[uid].append({"role": "user", "content": user_msg})
    history = chat_history[uid][-20:]
    system = system_override or ALINE_SYSTEM
    payload = {
        "model": OPENROUTER_MODEL,
        "messages": [{"role": "system", "content": system}] + history,
        "max_tokens": 200,
        "temperature": 0.92,
    }
    try:
        r = requests.post(OPENROUTER_URL, json=payload,
                          headers={"Authorization": f"Bearer {OPENROUTER_KEY}",
                                   "HTTP-Referer": "https://aline-nerin-bot.onrender.com",
                                   "X-Title": "Aline Nerin Bot"},
                          timeout=20)
        reply = r.json()["choices"][0]["message"]["content"].strip()
        logging.info(f"AI RAW: {repr(reply[:200])}")
        # limpa qualquer link residual
        reply = re.sub(r'https?://\S+', '', reply)
        reply = re.sub(r't\.me/\S+', '', reply, flags=re.IGNORECASE)
        reply = re.sub(r'@\w+', '', reply)
        reply = re.sub(r'A.?Tools?\s*X?', '', reply, flags=re.IGNORECASE)
        reply = re.sub(r'[Jj]oin\s+\S+', '', reply)
        reply = reply.strip()
        if not reply:
            reply = "kkk amor 😘"
        chat_history[uid].append({"role": "assistant", "content": reply})
        return reply
    except Exception as e:
        logging.error(f"AI erro: {e}")
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
AUDIO_MENU_FILE_ID_FIXO    = None  # áudio enviado logo após o menu de boas-vindas

CHAT_HISTORY_FILE = "chat_history.json"

def load_chat_history():
    global chat_history, amostra_enviada
    if os.path.exists(CHAT_HISTORY_FILE):
        try:
            d = json.load(open(CHAT_HISTORY_FILE))
            chat_history    = {int(k): v for k, v in d.get("history", {}).items()}
            amostra_enviada = {int(k): v for k, v in d.get("amostra", {}).items()}
            logging.info(f"Histórico carregado: {len(chat_history)} usuários")
        except Exception as e:
            logging.error(f"Erro ao carregar histórico: {e}")

def save_chat_history():
    try:
        json.dump({
            "history": {str(k): v for k, v in chat_history.items()},
            "amostra": {str(k): v for k, v in amostra_enviada.items()}
        }, open(CHAT_HISTORY_FILE, "w"), ensure_ascii=False)
    except Exception as e:
        logging.error(f"Erro ao salvar histórico: {e}")

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
            AUDIO_MENU      = d.get("audio_menu_file_id") or AUDIO_MENU_FILE_ID_FIXO
            logging.info(f"Estado carregado: owner={owner_id} amostra={bool(AMOSTRA_FILE_ID)} audio={bool(AUDIO_FILE_ID)}")
        except Exception as e:
            logging.error(f"Erro ao carregar state: {e}")

def save_state():
    try:
        json.dump({"photo_url": PHOTO_URL, "video_url": VIDEO_URL, "owner_id": owner_id, "amostra_file_id": AMOSTRA_FILE_ID, "audio_file_id": AUDIO_FILE_ID, "audio_amostra_file_id": AUDIO_AMOSTRA, "audio_menu_file_id": AUDIO_MENU}, open(STATE_FILE, "w"))
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
AUDIO_MENU      = AUDIO_MENU_FILE_ID_FIXO     # áudio enviado logo após o menu de boas-vindas

load_state()
load_chat_history()

MENU_KB = {"inline_keyboard": [
    [{"text": "🔥 Pack Exclusivo - R$25", "callback_data": "pack"}],
    [{"text": "👑 Canal VIP - R$39,90/mês", "callback_data": "vip"}],
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
    "Oi bb 😏 Você caiu no lugar certo...\n\n"
    "Sou a *Aline Nerin* e aqui eu não tenho vergonha de nada 🔥\n\n"
    "Tenho conteúdo exclusivo esperando por você... "
    "Fotos e vídeos que você não vai encontrar em nenhum outro lugar 😈\n\n"
    "O que você prefere, gostoso? 👇"
)

PACK_TEXT = (
    "📦 *PACK EXCLUSIVO - R$25*\n\n"
    "Aquele conteúdo que eu guardo só pra quem merece... 😏\n\n"
    "🔥 Fotos e vídeos bem safadinhos\n"
    "💋 Do jeitinho que você tá imaginando\n"
    "📲 Cai no seu privado na hora\n\n"
    "Preparado pra ver tudo? 😈"
)

VIP_TEXT = (
    "👑 *CANAL VIP - R$39,90/mês*\n\n"
    "Aqui é onde a *Aline Nerin* solta o jogo de verdade... 🔥\n\n"
    "✅ Conteúdo *novo todo dia* - fotos e vídeos exclusivos\n"
    "🔞 Sem censura, sem filtro\n"
    "💋 Acesso imediato ao canal privado\n"
    "😈 Uma experiência que você não vai querer perder\n\n"
    "Bora, bb? 👇"
)

PIX_PACK_TEXT = (
    "💸 *Pagamento - Pack R$25*\n\n"
    "Faz o Pix e em segundos o conteúdo tá no seu privado 😈\n\n"
    "🔑 Chave Pix:\n`{pix}`\n\n"
    "📌 Valor: *R$25,00*\n"
    "📌 Tipo: Celular\n\n"
    "Depois manda o *comprovante aqui* que libero na hora 🔥"
).format(pix=PIX_KEY)

PIX_VIP_TEXT = (
    "💸 *Pagamento - VIP R$39,90/mês*\n\n"
    "Um mês inteiro de conteúdo novo todo dia... vale cada centavo 😏\n\n"
    "🔑 Chave Pix:\n`{pix}`\n\n"
    "📌 Valor: *R$39,90*\n"
    "📌 Tipo: Celular\n\n"
    "Manda o *comprovante aqui* que libero seu acesso VIP na hora 👑🔥"
).format(pix=PIX_KEY)

COMPROVANTE_TEXT = (
    "Recebi bb 😘\n\n"
    "Deixa eu confirmar aqui e já libero tudo pra você... ⏳🔥"
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
    "Aproveita bastante... e se quiser mais, você sabe onde me achar 💋"
)

DESCONHECIDO_TEXT = (
    "Oi bb 😏\n\n"
    "Usa o menu abaixo pra ver o que tenho pra você 🔥👇"
)

# ── FUNÇÕES ─────────────────────────────────────────────────────────────────

def typing(cid, segundos=2):
    """Mostra 'digitando...' por N segundos"""
    requests.post(f"{BASE}/sendChatAction", json={"chat_id": cid, "action": "typing"}, timeout=5)
    time.sleep(segundos)

def send(cid, text, kb=None):
    d = {
        "chat_id": cid,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }
    if kb:
        d["reply_markup"] = kb
    r = requests.post(f"{BASE}/sendMessage", json=d, timeout=10)
    logging.info(f"send→{cid} ok={r.json().get('ok')} text={repr(text[:100])}")
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
    """Envia vídeo/foto de boas vindas + áudio + depois o menu (com delay natural)"""
    global PHOTO_URL, VIDEO_URL
    # caption curto e natural - sem jogar menu na cara logo
    caption = "oi 😏 que bom que você apareceu..."
    if VIDEO_FILE_ID_FIXO:
        send_video(cid, VIDEO_FILE_ID_FIXO, caption)
    elif PHOTO_URL:
        send_photo(cid, PHOTO_URL, caption)
    else:
        send(cid, caption)
    # áudio de apresentação
    _audio = AUDIO_FILE_ID_FIXO
    if _audio:
        time.sleep(1)
        requests.post(f"{BASE}/sendVoice", json={
            "chat_id": cid,
            "voice": _audio
        }, timeout=15)
    # pequeno delay antes do menu - parece mais humano
    typing(cid, segundos=3)
    send(cid, "o que você prefere, gostoso? 👇", MENU_KB)
    # áudio logo após o menu
    _audio_menu = globals().get("AUDIO_MENU")
    if _audio_menu:
        time.sleep(1)
        requests.post(f"{BASE}/sendVoice", json={
            "chat_id": cid,
            "voice": _audio_menu
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
        send(uid, f"✅ Registrada como administradora!\nID: `{uid}`\n\nComandos:\n/setamostra - foto amostra\n/setaudio - áudio de apresentação\n/setaudioamostra - áudio que vai junto com a foto amostra\n/setaudiomenu - áudio enviado logo após o menu de boas-vindas")

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

    elif text and text.strip() == "/setaudiomenu" and int(uid) == int(owner_id or 0):
        send(uid, "🎤 Manda o áudio que vai logo após o menu de boas-vindas!")
        pending[uid] = "aguardando_audio_menu"

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
        elif pending.get(uid) == "aguardando_audio_menu":
            globals()["AUDIO_MENU"] = file_id
            pending.pop(uid, None)
            save_state()
            send(uid, "✅ Áudio do menu salvo! Vai ser enviado logo após o menu de boas-vindas 🎤🔥")
        else:
            send(uid, "Áudio recebido. Use /setaudio, /setaudioamostra ou /setaudiomenu pra cadastrar.")

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

            # atalho de texto: usuário clicou em botão antigo ou digitou pack/vip
            quer_pack = texto_lower in ["pack", "pack exclusivo", "r$25", "25", "quero o pack"]
            quer_vip  = texto_lower in ["vip", "canal vip", "r$39,90", "39,90", "quero vip", "vip r$39,90/mês"]
            if quer_pack:
                pending[uid] = "pack"
                typing(uid, segundos=2)
                send(uid, PACK_TEXT, buy_kb("pack"))
                return
            elif quer_vip:
                pending[uid] = "vip"
                typing(uid, segundos=2)
                send(uid, VIP_TEXT, buy_kb("vip"))
                return

            if fala_golpe:
                resp_golpe = groq_resposta(uid, text) or "bb eu nao preciso de golpe nao kkk tenho cliente que ta comigo faz meses 😂 pode confiar"
                typing(uid, segundos=len(resp_golpe) // 30 + 2)
                send(uid, resp_golpe)
                save_chat_history()

            elif pediu_amostra and not amostra_enviada.get(uid) and _amostra:
                # primeira vez - envia foto amostra SEM menu (deixa a conversa fluir)
                requests.post(f"{BASE}/sendPhoto", json={
                    "chat_id": uid,
                    "photo": _amostra,
                    "caption": "isso é só uma provinha bb 😏🔥\no que tá no pack é bem mais pesado que isso 😈",
                }, timeout=15)
                amostra_enviada[uid] = True
                save_chat_history()
                logging.info(f"amostra→{uid} enviada")
                # envia áudio da amostra se tiver
                _voz = _audio_amostra or _audio
                if _voz:
                    time.sleep(1)
                    requests.post(f"{BASE}/sendVoice", json={
                        "chat_id": uid,
                        "voice": _voz
                    }, timeout=15)

            elif pediu_amostra and amostra_enviada.get(uid):
                # já recebeu - suspense sem menu
                suspense = groq_resposta(uid, text, system_override=ALINE_SUSPENSE)
                if not suspense:
                    suspense = "bb aquela foi só uma provinha... o que tá no pack é pesado demais 😈 quer ver?"
                typing(uid, segundos=len(suspense) // 30 + 2)
                send(uid, suspense)
                save_chat_history()
                # depois de criar suspense, aí mostra o menu
                time.sleep(2)
                send(uid, "o que você prefere, gostoso? 👇", MENU_KB)

            else:
                # conversa natural - a IA decide quando mencionar os produtos
                resposta = limpar_resposta(groq_resposta(uid, text))
                if not resposta:
                    resposta = "oi bb 😘"
                typing(uid, segundos=len(resposta) // 25 + 2)
                send(uid, resposta)
                save_chat_history()
                # só mostra o menu se a IA mencionou os produtos na resposta
                palavras_produto = ["pack", "r$25", "vip", "r$39", "canal", "conteúdo exclusivo", "pix", "pagamento"]
                mencionou_produto = any(p in resposta.lower() for p in palavras_produto)
                if mencionou_produto:
                    time.sleep(1)
                    send(uid, "o que você prefere? 👇", MENU_KB)

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

logging.info("🤖 Bot Aline Nerin - iniciado!")

# Inicia servidor HTTP em thread separada
threading.Thread(target=start_health_server, daemon=True).start()

offset = 0
logging.info("Bot iniciando polling...")
while True:
    try:
        r = requests.get(f"{BASE}/getUpdates", params={"offset": offset, "timeout": 25}, timeout=30)
        updates = r.json().get("result", [])
        for u in updates:
            offset = u["update_id"] + 1
            threading.Thread(target=process_update, args=(u,), daemon=True).start()
    except Exception as e:
        logging.error(f"Erro polling: {e}")
        time.sleep(2)
