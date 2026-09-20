"""
Testes automatizados para o fuso horario em utils/helpers.py
(obter_mes_ano_efetivo).

Como rodar (na raiz do projeto):
    pytest

O Supabase devolve datas em UTC. Uma compra feita a noite no Brasil ja e
"dia seguinte" em UTC, e antes da correcao caia no mes errado.
"""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.helpers import obter_mes_ano_efetivo


class TestFusoHorario:
    """O mes/ano deve ser sempre o de Brasilia, mesmo que a data venha em UTC."""

    def test_virada_de_mes_utc_fica_no_mes_certo(self):
        # 01/10 01:30 em UTC = 30/09 22:30 em Brasilia -> deve ser SETEMBRO
        item = {"created_at": "2026-10-01T01:30:00+00:00"}
        mes, ano, _ = obter_mes_ano_efetivo(item)
        assert (mes, ano) == ("09", "2026")

    def test_virada_de_ano_utc_fica_no_ano_certo(self):
        # 01/01/2027 01:00 UTC = 31/12/2026 22:00 em Brasilia -> deve ser DEZEMBRO/2026
        item = {"created_at": "2027-01-01T01:00:00+00:00"}
        mes, ano, _ = obter_mes_ano_efetivo(item)
        assert (mes, ano) == ("12", "2026")

    def test_sufixo_z_tambem_e_convertido(self):
        # Mesma data do primeiro teste, mas com "Z" no lugar de "+00:00"
        item = {"created_at": "2026-10-01T01:30:00Z"}
        mes, ano, _ = obter_mes_ano_efetivo(item)
        assert (mes, ano) == ("09", "2026")

    def test_meio_do_mes_nao_muda(self):
        item = {"created_at": "2026-09-15T15:00:00+00:00"}
        mes, ano, _ = obter_mes_ano_efetivo(item)
        assert (mes, ano) == ("09", "2026")

    def test_data_sem_fuso_e_mantida_como_esta(self):
        # Datas sem fuso ja sao horario local: nao devem ser deslocadas
        item = {"created_at": "2026-10-01T01:30:00"}
        mes, ano, _ = obter_mes_ano_efetivo(item)
        assert (mes, ano) == ("10", "2026")

    def test_horario_devolvido_e_o_de_brasilia(self):
        item = {"created_at": "2026-10-01T01:30:00+00:00"}
        _, _, dt = obter_mes_ano_efetivo(item)
        assert (dt.day, dt.hour, dt.minute) == (30, 22, 30)
