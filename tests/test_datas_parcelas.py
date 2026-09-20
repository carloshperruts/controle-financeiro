"""
Testes automatizados para o dia da data de cada parcela
(utils/helpers.py: ultimo_dia_do_mes e calcular_data_parcela).

Uma compra feita no dia 29, 30 ou 31 tem que ficar registrada com a data real,
e o dia so pode diminuir quando o mes da parcela e mais curto.

Como rodar (na raiz do projeto):
    python -m pytest
"""
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.helpers import calcular_data_parcela, ultimo_dia_do_mes


class TestUltimoDiaDoMes:
    def test_meses_de_31_dias(self):
        for mes in (1, 3, 5, 7, 8, 10, 12):
            assert ultimo_dia_do_mes(2026, mes) == 31

    def test_meses_de_30_dias(self):
        for mes in (4, 6, 9, 11):
            assert ultimo_dia_do_mes(2026, mes) == 30

    def test_fevereiro_comum(self):
        assert ultimo_dia_do_mes(2026, 2) == 28

    def test_fevereiro_bissexto(self):
        assert ultimo_dia_do_mes(2028, 2) == 29

    def test_seculo_nao_bissexto(self):
        assert ultimo_dia_do_mes(2100, 2) == 28


class TestCompraNaDataReal:
    """A 1a parcela (e a compra a vista) nao pode ter o dia alterado."""

    def test_dias_29_30_e_31_na_primeira_parcela(self):
        for dia in (29, 30, 31):
            dt = datetime(2026, 1, dia, 22, 30, 0)
            assert calcular_data_parcela(dt, 0) == dt

    def test_dia_31_em_mes_de_31_dias(self):
        dt = datetime(2026, 12, 31, 8, 15, 0)
        assert calcular_data_parcela(dt, 0) == dt


class TestDiaAoLongoDasParcelas:
    def test_dia_31_acompanha_o_fim_de_cada_mes(self):
        dt = datetime(2026, 1, 31, 12, 0, 0)
        dias = [calcular_data_parcela(dt, i).day for i in range(5)]
        assert dias == [31, 28, 31, 30, 31]

    def test_dia_30_em_janeiro(self):
        dt = datetime(2026, 1, 30, 12, 0, 0)
        dias = [calcular_data_parcela(dt, i).day for i in range(5)]
        assert dias == [30, 28, 30, 30, 30]

    def test_fevereiro_bissexto_tem_29(self):
        dt = datetime(2028, 1, 31, 12, 0, 0)
        assert calcular_data_parcela(dt, 1) == datetime(2028, 2, 29, 12, 0, 0)

    def test_nunca_gera_data_invalida_nem_dia_maior_que_o_original(self):
        for mes in range(1, 13):
            for dia in range(1, ultimo_dia_do_mes(2026, mes) + 1):
                for i in range(0, 25):
                    r = calcular_data_parcela(datetime(2026, mes, dia, 8, 0, 0), i)
                    assert 1 <= r.day <= dia
                    assert r.day <= ultimo_dia_do_mes(r.year, r.month)
