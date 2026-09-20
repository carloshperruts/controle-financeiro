"""
Testes automatizados para o cliente do Supabase por sessao
(config/supabase_client.py: criar_cliente_supabase).

Cada usuario conectado ao app precisa ter o SEU cliente. Um cliente guarda o
token de quem fez login nele; se dois usuarios dividissem o mesmo cliente, o
ultimo login sobrescreveria o token do outro.

Estes testes nao usam internet, conta nem banco: simulam o evento de login
da propria biblioteca com tokens falsos.

Como rodar (na raiz do projeto):
    python -m pytest
"""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# O modulo exige estas variaveis ao ser importado. Valores falsos bastam:
# nenhum teste aqui chega a falar com o Supabase.
os.environ.setdefault("SUPABASE_URL", "https://exemplo.supabase.co")
os.environ.setdefault("SUPABASE_KEY", "aaaa.bbbb.cccc")

from config import supabase_client
from config.supabase_client import criar_cliente_supabase


class SessaoFalsa:
    """Imita o que o Supabase devolve num login: so o access_token importa."""

    def __init__(self, token):
        self.access_token = token


def _token_em_uso(cliente):
    return cliente.options.headers.get("Authorization")


class TestClientePorSessao:
    def test_cada_chamada_cria_um_cliente_novo(self):
        assert criar_cliente_supabase() is not criar_cliente_supabase()

    def test_login_em_um_cliente_nao_afeta_o_outro(self):
        a = criar_cliente_supabase()
        b = criar_cliente_supabase()
        token_b_antes = _token_em_uso(b)

        a._listen_to_auth_events("SIGNED_IN", SessaoFalsa("TOKEN_A"))

        assert _token_em_uso(a) == "Bearer TOKEN_A"
        assert _token_em_uso(b) == token_b_antes

    def test_logins_alternados_mantem_cada_token_no_seu_cliente(self):
        a = criar_cliente_supabase()
        b = criar_cliente_supabase()

        a._listen_to_auth_events("SIGNED_IN", SessaoFalsa("TOKEN_A"))
        b._listen_to_auth_events("SIGNED_IN", SessaoFalsa("TOKEN_B"))

        # Antes da correcao, o login do B sobrescrevia o token do A
        assert _token_em_uso(a) == "Bearer TOKEN_A"
        assert _token_em_uso(b) == "Bearer TOKEN_B"

    def test_modulo_nao_expoe_cliente_global(self):
        # Um cliente global compartilhado por todos os usuarios e justamente o bug
        assert not hasattr(supabase_client, "supabase")
