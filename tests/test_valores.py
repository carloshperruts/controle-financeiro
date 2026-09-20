"""
Testes automatizados para a leitura de valores digitados (parse_valor_br),
cobrindo o que um usuario real digita no campo de valor.

Como rodar (na raiz do projeto):
    pytest
"""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.helpers import parse_valor_br


class TestPontoDecimal:
    """Quem digita com ponto decimal nao pode ter o valor multiplicado por 100."""

    def test_ponto_decimal_com_duas_casas(self):
        assert parse_valor_br("1234.56") == 1234.56

    def test_ponto_decimal_com_uma_casa(self):
        assert parse_valor_br("12.5") == 12.5

    def test_ponto_decimal_pequeno(self):
        assert parse_valor_br("89.90") == 89.90

    def test_ponto_com_tres_digitos_e_milhar(self):
        # Convencao brasileira: 1.234 = mil duzentos e trinta e quatro
        assert parse_valor_br("1.234") == 1234.0


class TestSimboloEEspacos:
    def test_com_simbolo_de_real(self):
        assert parse_valor_br("R$ 50,00") == 50.0

    def test_com_simbolo_colado(self):
        assert parse_valor_br("R$1.234,56") == 1234.56

    def test_espacos_nas_pontas(self):
        assert parse_valor_br("  89,90  ") == 89.90

    def test_so_espacos_retorna_padrao(self):
        assert parse_valor_br("   ") == 0.0


class TestEntradasRecusadas:
    """Entradas que nao sao dinheiro valido devem devolver o padrao, nunca nan/inf."""

    def test_nan_retorna_padrao(self):
        assert parse_valor_br("nan") == 0.0

    def test_inf_retorna_padrao(self):
        assert parse_valor_br("inf") == 0.0

    def test_infinity_retorna_padrao(self):
        assert parse_valor_br("infinity", padrao=-1.0) == -1.0

    def test_notacao_cientifica_retorna_padrao(self):
        assert parse_valor_br("1e3") == 0.0

    def test_formato_americano_retorna_padrao(self):
        # "1,234.56" seria lido errado como 1,23456; melhor recusar do que errar em silencio
        assert parse_valor_br("1,234.56") == 0.0


class TestFormatoBrasileiroContinuaIgual:
    """Garante que a correcao nao mudou o que ja funcionava."""

    def test_milhar_e_decimal(self):
        assert parse_valor_br("1.234,56") == 1234.56

    def test_milhoes(self):
        assert parse_valor_br("1.234.567,89") == 1234567.89

    def test_negativo_com_virgula(self):
        assert parse_valor_br("-50,00") == -50.0

    def test_inteiro_simples(self):
        assert parse_valor_br("100") == 100.0

    def test_aceita_numero_ja_convertido(self):
        assert parse_valor_br(12.5) == 12.5
