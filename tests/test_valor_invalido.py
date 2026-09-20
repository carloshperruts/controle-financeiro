"""
Testes automatizados para distinguir "valor invalido" de "valor zero"
(utils/helpers.py: parse_valor_br com padrao=None).

A tela usa padrao=None para recusar o que nao e dinheiro, em vez de gravar
um lancamento de R$ 0,00 sem avisar.

Como rodar (na raiz do projeto):
    python -m pytest
"""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.helpers import parse_valor_br


class TestValorInvalidoDevolveNone:
    def test_texto_qualquer(self):
        assert parse_valor_br("abc", padrao=None) is None

    def test_vazio(self):
        assert parse_valor_br("", padrao=None) is None

    def test_nan_e_inf(self):
        assert parse_valor_br("nan", padrao=None) is None
        assert parse_valor_br("inf", padrao=None) is None

    def test_notacao_cientifica(self):
        assert parse_valor_br("1e3", padrao=None) is None

    def test_formato_americano(self):
        assert parse_valor_br("1,234.56", padrao=None) is None


class TestValorValidoNaoViraNone:
    def test_zero_digitado_e_valido(self):
        assert parse_valor_br("0", padrao=None) == 0.0
        assert parse_valor_br("0,00", padrao=None) == 0.0

    def test_formatos_comuns(self):
        assert parse_valor_br("10,50", padrao=None) == 10.5
        assert parse_valor_br("1234.56", padrao=None) == 1234.56
        assert parse_valor_br("R$ 50,00", padrao=None) == 50.0
        assert parse_valor_br("1.234,56", padrao=None) == 1234.56
        assert parse_valor_br("100", padrao=None) == 100.0

    def test_padrao_continua_valendo_quando_informado(self):
        assert parse_valor_br("abc") == 0.0
        assert parse_valor_br("abc", padrao=-1.0) == -1.0
