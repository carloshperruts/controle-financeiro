"""
Testes automatizados para utils/helpers.py.

Como rodar (na raiz do projeto):
    pip install pytest
    pytest

Estes testes não acessam o Supabase nem a internet — testam só a lógica
pura das funções, então rodam instantaneamente e não dependem de conexão.
"""
import sys
import os

# Garante que a raiz do projeto está no caminho de import, independente
# de onde o pytest for executado a partir.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.helpers import parse_valor_br


class TestParseValorBR:
    """Testes da conversão de valores em formato brasileiro (1.234,56) para float."""

    def test_valor_simples(self):
        assert parse_valor_br("89,90") == 89.90

    def test_valor_com_milhar(self):
        assert parse_valor_br("1.234,56") == 1234.56

    def test_valor_com_milhoes(self):
        assert parse_valor_br("1.234.567,89") == 1234567.89

    def test_valor_inteiro_sem_decimais(self):
        assert parse_valor_br("100") == 100.0

    def test_valor_zero(self):
        assert parse_valor_br("0,00") == 0.0

    def test_texto_vazio_retorna_padrao(self):
        assert parse_valor_br("") == 0.0

    def test_none_retorna_padrao(self):
        assert parse_valor_br(None) == 0.0

    def test_texto_invalido_retorna_padrao(self):
        assert parse_valor_br("abc") == 0.0

    def test_padrao_customizado(self):
        assert parse_valor_br("", padrao=999.0) == 999.0
        assert parse_valor_br("texto_invalido", padrao=-1.0) == -1.0

    def test_valor_negativo(self):
        # A função em si não bloqueia negativos (isso é feito na camada de UI,
        # em dashboard_view.py) — aqui só confirmamos que o parse é fiel.
        assert parse_valor_br("-50,00") == -50.0
