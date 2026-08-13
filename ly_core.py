"""Núcleo comercial da Ly, sem integração de canal.

A camada de Telegram/WhatsApp deve chamar `reply_for` depois de validar
consentimento e aplicar rate limit. Nenhum segredo fica neste arquivo.
"""
from dataclasses import dataclass
from pathlib import Path
import json
import sqlite3
import time

PACK_PRICE = "R$ 25"
VIP_PRICE = "R$ 39,90"

@dataclass
class Reply:
    text: str
    intent: str
    needs_human: bool = False

class LyMemory:
    def __init__(self, path="ly_memory.sqlite3"):
        self.db = sqlite3.connect(path, check_same_thread=False)
        self.db.execute("CREATE TABLE IF NOT EXISTS conversations (id TEXT PRIMARY KEY, summary TEXT DEFAULT '', last_offer TEXT DEFAULT '', opt_out INTEGER DEFAULT 0, updated REAL)")
        self.db.execute("CREATE TABLE IF NOT EXISTS messages (conversation_id TEXT, role TEXT, text TEXT, created REAL)")
        self.db.commit()

    def add(self, conversation_id, role, text):
        self.db.execute("INSERT INTO messages VALUES (?, ?, ?, ?)", (conversation_id, role, text, time.time()))
        self.db.execute("INSERT INTO conversations(id, updated) VALUES (?, ?) ON CONFLICT(id) DO UPDATE SET updated=excluded.updated", (conversation_id, time.time()))
        self.db.commit()

    def recent(self, conversation_id, limit=10):
        rows = self.db.execute("SELECT role, text FROM messages WHERE conversation_id=? ORDER BY created DESC LIMIT ?", (conversation_id, limit)).fetchall()
        return list(reversed(rows))

    def set_offer(self, conversation_id, offer):
        self.db.execute("UPDATE conversations SET last_offer=?, updated=? WHERE id=?", (offer, time.time(), conversation_id))
        self.db.commit()

    def opted_out(self, conversation_id):
        row = self.db.execute("SELECT opt_out FROM conversations WHERE id=?", (conversation_id,)).fetchone()
        return bool(row and row[0])

    def opt_out(self, conversation_id):
        self.db.execute("UPDATE conversations SET opt_out=1, updated=? WHERE id=?", (time.time(), conversation_id))
        self.db.commit()


def classify(text):
    t = text.lower().strip()
    if any(x in t for x in ("não quero", "nao quero", "pare", "stop", "remover")): return "opt_out"
    if any(x in t for x in ("comprovante", "paguei", "pagamento feito")): return "comprovante"
    if any(x in t for x in ("golpe", "fake", "fraude", "confiável", "confiavel")): return "desconfianca"
    if any(x in t for x in ("amostra", "prévia", "previa", "prova", "mostra")): return "amostra"
    if any(x in t for x in ("vip", "grupo", "diário", "diario")): return "vip"
    if any(x in t for x in ("pack", "25 fotos", "75 vídeos", "75 videos")): return "pack"
    if any(x in t for x in ("pix", "vou pagar", "pagar agora")): return "pagamento"
    if any(x in t for x in ("menor", "17 anos", "16 anos", "15 anos")): return "menoridade"
    return "geral"


def reply_for(text, memory=None, conversation_id="local"):
    """Retorna uma resposta determinística segura para testes do fluxo."""
    memory = memory or LyMemory(":memory:")
    intent = classify(text)
    if memory.opted_out(conversation_id): return Reply("tudo bem, bb 🩷 não vou mais te chamar.", intent)
    memory.add(conversation_id, "user", text)
    if intent == "opt_out":
        memory.opt_out(conversation_id); answer = "tudo bem, bb 🩷 se cuida. não vou mais te chamar."
    elif intent == "menoridade":
        answer = "não posso continuar essa conversa. se cuida."
    elif intent == "comprovante":
        answer = "recebi, vida 🩷 vou verificar e já te mando tuuudinho, bb 😍"; human = True
    elif intent == "desconfianca":
        answer = "entendo sua preocupação, bb 🩷 posso te mandar uma amostra pra vc conhecer o estilo. o pack completo é liberado depois que o pagamento for validado, tudo certinho e sem surpresa 😏"
    elif intent == "amostra":
        answer = "sim, bb, posso te mandar uma amostra pra vc conhecer o estilo 🩷 o pack completo é liberado depois que o pagamento for validado, tudo certinho e sem surpresa 😏"
    elif intent == "pack":
        memory.set_offer(conversation_id, "pack")
        answer = "meu pack custa R$ 25 e vem com 25 fotos, 75 vídeos e uma vídeo chamada combinada 😏"
    elif intent == "vip":
        memory.set_offer(conversation_id, "vip")
        answer = "o vip custa R$ 39,90 em pagamento único, sem mensalidade 🩷 vc fica com acesso permanente ao grupo, com fotos, vídeos e vídeos ao vivo dentro do grupo 😏"
    elif intent == "pagamento":
        answer = "perfeito, vida 🩷 vou te passar meu Pix, bb, pode ser? depois que fizer, me envie o comprovante que eu libero seu acesso."
        human = True
    else:
        answer = "oii bb 🩷 tudo bem? vc quer conhecer meu pack ou saber do vip?"
    memory.add(conversation_id, "assistant", answer)
    return Reply(answer, intent, locals().get("human", False))
