import os
import csv
from datetime import datetime

def obter_mes_ano_efetivo(item):
    """
    Calcula o mês e ano do lançamento.
    Se for Cartão de Crédito, lança o gasto para o mês seguinte.
    """
    raw_data = item.get("created_at") or item.get("data")
    forma = item.get("forma_pagamento", "Débito / Pix")
    try:
        dt = datetime.fromisoformat(str(raw_data).replace("Z", "+00:00")) if raw_data else datetime.now()
    except Exception:
        dt = datetime.now()

    if forma == "Cartão de Crédito":
        if dt.month == 12:
            return "01", str(dt.year + 1), dt
        else:
            return str(dt.month + 1).zfill(2), str(dt.year), dt
    return str(dt.month).zfill(2), str(dt.year), dt

def exportar_para_csv(registros_cache, mes_sel, ano_sel):
    """
    Gera o arquivo CSV com os registros do mês/ano selecionado
    e salva diretamente na pasta Downloads do usuário.
    """
    if not registros_cache:
        return False, "⚠️ Nenhum registro para exportar!"

    mes_sel = str(mes_sel).zfill(2)
    ano_sel = str(ano_sel)

    dados_filtrados = [
        (item, dt) for item in registros_cache 
        if (m_ef := obter_mes_ano_efetivo(item))[0] == mes_sel and m_ef[1] == ano_sel 
        for dt in [m_ef[2]]
    ]

    if not dados_filtrados:
        return False, f"⚠️ Nenhum lançamento para o mês {mes_sel}/{ano_sel}!"

    try:
        caminho_user = os.path.expanduser("~")
        pasta_destino = os.path.join(caminho_user, "Downloads")
        if not os.path.exists(pasta_destino):
            pasta_destino = caminho_user

        caminho_completo = os.path.join(pasta_destino, f"Relatorio_Financeiro_{mes_sel}_{ano_sel}.csv")

        with open(caminho_completo, mode="w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f, delimiter=";")
            writer.writerow(["Data Lançamento", "Descrição", "Categoria", "Forma Pagamento", "Vencimento", "Tipo", "Valor (R$)"])
            for item, dt in dados_filtrados:
                writer.writerow([
                    dt.strftime("%d/%m/%Y %H:%M"),
                    item.get("descricao", ""),
                    item.get("categoria", ""),
                    item.get("forma_pagamento", "Débito / Pix"),
                    item.get("data_vencimento", "-"),
                    item.get("tipo", "Despesa"),
                    f"{float(item.get('valor', 0)):.2f}".replace(".", ",")
                ])

        return True, f"✔ Relatório salvo em: {caminho_completo}"
    except Exception as err:
        return False, f"❌ Erro ao exportar: {str(err)}"