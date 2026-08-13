"""Configuração comercial segura da Ly.

Os valores reais devem ser fornecidos por variáveis de ambiente no servidor.
"""
import os

PACK_PRICE = os.getenv("LY_PACK_PRICE", "R$ 25")
VIP_PRICE = os.getenv("LY_VIP_PRICE", "R$ 39,90")
PIX_KEY = os.getenv("LY_PIX_KEY", "")
VIP_GROUP_LINK = os.getenv("LY_VIP_GROUP_LINK", "")
PACK_LINK = os.getenv("LY_PACK_LINK", "")
SAMPLE_MEDIA_ID = os.getenv("LY_SAMPLE_MEDIA_ID", "")
PACK_MEDIA_ID = os.getenv("LY_PACK_MEDIA_ID", "")
AUDIO_MEDIA_ID = os.getenv("LY_AUDIO_MEDIA_ID", "")
AI_PROVIDER = os.getenv("LY_AI_PROVIDER", "openrouter")
AI_MODEL = os.getenv("LY_AI_MODEL", "mistralai/pixtral-12b:free")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")


def validate_for_payment():
    if not PIX_KEY:
        raise RuntimeError("LY_PIX_KEY não configurada")
    return PIX_KEY
