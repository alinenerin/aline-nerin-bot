from ly_core import LyMemory, reply_for


def run(text, expected_intent, human=False):
    reply = reply_for(text, LyMemory(':memory:'), 'test')
    assert reply.intent == expected_intent, (text, reply)
    assert reply.needs_human is human, (text, reply)
    return reply.text


def test_core_flows():
    assert '25 fotos' in run('o que vem no pack?', 'pack')
    assert 'acesso permanente' in run('me explica o vip', 'vip')
    assert 'amostra' in run('pode mandar amostra?', 'amostra')
    assert run('pare', 'opt_out').startswith('tudo bem')
    assert run('pare, não quero mais', 'opt_out').startswith('tudo bem')
    assert run('enviei o comprovante', 'comprovante', human=True).startswith('recebi')
    assert run('parece golpe', 'desconfianca').startswith('entendo')
    assert run('tenho 17 anos', 'menoridade').startswith('não posso')


if __name__ == '__main__':
    test_core_flows()
    print('Ly core tests: OK')
