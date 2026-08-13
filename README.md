# Ly — núcleo de atendimento

Esta branch contém apenas o núcleo comercial da Ly. A integração com Telegram e WhatsApp fica separada e só será ativada depois dos testes.

## Regras atuais
- Pack: R$ 25 — 25 fotos, 75 vídeos e vídeo chamada combinada.
- VIP: R$ 39,90 — pagamento único, acesso permanente ao grupo, fotos, vídeos e vídeos ao vivo dentro do grupo.
- Pagamento e comprovante exigem validação antes da liberação.
- Opt-out encerra o contato.
- Menoridade, reclamação e reembolso são encaminhados/encerrados.

## Memória
`ly_core.py` usa SQLite para manter mensagens recentes, oferta apresentada e opt-out por conversa. Não usar armazenamento temporário em produção.

## Segurança
Não guardar tokens, chaves Pix, sessões ou credenciais no código. Use variáveis de ambiente/secret manager. Esta branch não faz deploy nem envia mensagens.
