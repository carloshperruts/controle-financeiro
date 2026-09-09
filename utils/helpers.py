import os
import csv
import uuid
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
    Gera o arquivo CSV com os registros do mês/ano selecionado.

    Importante: como o app roda num servidor (Render), não faz sentido salvar
    o arquivo na pasta "Downloads" do servidor — quem usa o site pelo navegador
    nunca teria acesso a ele. Em vez disso, o arquivo é salvo numa subpasta
    dentro de 'assets' (que o Flet expõe publicamente pela web), com um nome
    aleatório e imprevisível, e devolvemos o link relativo pra abrir no navegador
    (o próprio navegador do usuário faz o download a partir daí).
    """
    if not registros_cache:
        return False, "⚠️ Nenhum registro para exportar!", None

    mes_sel = str(mes_sel).zfill(2)
    ano_sel = str(ano_sel)

    dados_filtrados = [
        (item, dt) for item in registros_cache 
        if (m_ef := obter_mes_ano_efetivo(item))[0] == mes_sel and m_ef[1] == ano_sel 
        for dt in [m_ef[2]]
    ]

    if not dados_filtrados:
        return False, f"⚠️ Nenhum lançamento para o mês {mes_sel}/{ano_sel}!", None

    try:
        # Pasta pública dentro de 'assets', servida pelo próprio Flet
        pasta_destino = os.path.join(os.getcwd(), "assets", "exports")
        os.makedirs(pasta_destino, exist_ok=True)

        # Nome de arquivo com um token aleatório, pra ninguém conseguir
        # adivinhar/acessar o relatório exportado por outra pessoa
        token = uuid.uuid4().hex[:12]
        nome_arquivo = f"Relatorio_{mes_sel}_{ano_sel}_{token}.csv"
        caminho_completo = os.path.join(pasta_destino, nome_arquivo)

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

        # Caminho relativo que o navegador consegue abrir/baixar direto
        url_relativa = f"/exports/{nome_arquivo}"
        return True, "✔ Relatório gerado! Iniciando o download...", url_relativa
    except Exception as err:
        return False, f"❌ Erro ao exportar: {str(err)}", None