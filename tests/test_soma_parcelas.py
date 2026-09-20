"""
Testes automatizados para a divisao de uma compra em parcelas
(utils/helpers.py: calcular_valores_parcelas).

A soma das parcelas tem que ser SEMPRE igual ao valor total da compra.

Como rodar (na raiz do projeto):
    python -m pytest
"""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.helpers import calcular_valores_parcelas


def _em_centavos(valores):
    return sum(round(v * 100) for v in valores)


class TestSomaDasParcelas:
    def test_cem_em_tres_soma_cem(self):
        valores = calcular_valores_parcelas(100.0, 3)
        assert valores == [33.34, 33.33, 33.33]
        assert _em_centavos(valores) == 10000

    def test_cem_em_seis_soma_cem(self):
        valores = calcular_valores_parcelas(100.0, 6)
        assert _em_centavos(valores) == 10000

    def test_valor_quebrado_em_doze(self):
        valores = calcular_valores_parcelas(89.90, 12)
        assert len(valores) == 12
        assert _em_centavos(valores) == 8990

    def test_divisao_exata_nao_muda(self):
        assert calcular_valores_parcelas(300.0, 3) == [100.0, 100.0, 100.0]

    def test_uma_parcela_e_o_proprio_valor(self):
        assert calcular_valores_parcelas(89.90, 1) == [89.90]

    def test_quantidade_de_parcelas(self):
        assert len(calcular_valores_parcelas(500.0, 5)) == 5


class TestValoresPequenos:
    def test_valor_minusculo_nao_gera_parcela_negativa(self):
        # 0,10 em 12x: arredondar cada parcela para 0,01 passaria do total
        valores = calcular_valores_parcelas(0.10, 12)
        assert min(valores) >= 0
        assert _em_centavos(valores) == 10

    def test_um_centavo_em_tres(self):
        valores = calcular_valores_parcelas(0.01, 3)
        assert valores == [0.01, 0.0, 0.0]


class TestTodasAsCombinacoes:
    """Testa de 1 centavo a R$ 50,00, com 1 a 12 parcelas."""

    def test_soma_sempre_igual_ao_total(self):
        for total_centavos in range(1, 5001):
            for n in range(1, 13):
                valores = calcular_valores_parcelas(total_centavos / 100, n)
                assert _em_centavos(valores) == total_centavos, (total_centavos, n)

    def test_nenhuma_parcela_negativa(self):
        for total_centavos in range(1, 5001):
            for n in range(1, 13):
                valores = calcular_valores_parcelas(total_centavos / 100, n)
                assert min(valores) >= 0, (total_centavos, n)

    def test_parcelas_diferem_no_maximo_um_centavo(self):
        for total_centavos in range(1, 5001):
            for n in range(1, 13):
                valores = calcular_valores_parcelas(total_centavos / 100, n)
                assert round((max(valores) - min(valores)) * 100) <= 1, (total_centavos, n)
