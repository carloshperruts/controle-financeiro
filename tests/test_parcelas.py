"""
Testes automatizados para o cálculo de parcelas de cartão de crédito
(utils/helpers.py: calcular_valor_parcela e calcular_data_parcela).

Como rodar (na raiz do projeto):
    pytest
"""
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.helpers import calcular_valor_parcela, calcular_data_parcela


class TestCalcularValorParcela:
    """Divisão do valor total de uma compra pelo número de parcelas."""

    def test_divisao_exata(self):
        assert calcular_valor_parcela(300.0, 3) == 100.0

    def test_divisao_com_arredondamento(self):
        # 100 / 3 = 33.333... -> arredonda para 33.33
        assert calcular_valor_parcela(100.0, 3) == 33.33

    def test_uma_parcela_a_vista(self):
        assert calcular_valor_parcela(89.90, 1) == 89.90

    def test_muitas_parcelas(self):
        assert calcular_valor_parcela(1200.0, 12) == 100.0


class TestCalcularDataParcela:
    """Data (ano/mês/dia/hora) de cada parcela, avançando mês a mês a partir
    de uma data base, com rolagem correta de ano."""

    def test_primeira_parcela_mantem_data_base(self):
        dt_base = datetime(2026, 9, 15, 18, 30, 0)
        resultado = calcular_data_parcela(dt_base, 0)
        assert resultado == datetime(2026, 9, 15, 18, 30, 0)

    def test_segunda_parcela_avanca_um_mes(self):
        dt_base = datetime(2026, 9, 15, 18, 30, 0)
        resultado = calcular_data_parcela(dt_base, 1)
        assert resultado == datetime(2026, 10, 15, 18, 30, 0)

    def test_rola_para_o_ano_seguinte(self):
        # Compra em novembro/2026, parcela 3 (índice 2) cai em janeiro/2027,
        # não no inexistente "mês 14" de 2026.
        dt_base = datetime(2026, 11, 15, 18, 30, 0)
        resultado = calcular_data_parcela(dt_base, 2)
        assert resultado == datetime(2027, 1, 15, 18, 30, 0)

    def test_dezembro_para_janeiro(self):
        dt_base = datetime(2026, 12, 10, 9, 0, 0)
        resultado = calcular_data_parcela(dt_base, 1)
        assert resultado == datetime(2027, 1, 10, 9, 0, 0)

    def test_dia_31_e_limitado_a_28(self):
        # Todo mês tem pelo menos 28 dias, então isso nunca gera data inválida
        # (ex.: dia 31 de janeiro não pode virar "31 de fevereiro").
        dt_base = datetime(2026, 1, 31, 12, 0, 0)
        resultado = calcular_data_parcela(dt_base, 1)
        assert resultado.day == 28
        assert resultado.month == 2

    def test_hora_e_preservada(self):
        dt_base = datetime(2026, 5, 10, 14, 25, 37)
        resultado = calcular_data_parcela(dt_base, 5)
        assert resultado.hour == 14
        assert resultado.minute == 25
        assert resultado.second == 37

    def test_doze_parcelas_completa_um_ano(self):
        dt_base = datetime(2026, 3, 10, 10, 0, 0)
        resultado = calcular_data_parcela(dt_base, 12)
        assert resultado == datetime(2027, 3, 10, 10, 0, 0)
