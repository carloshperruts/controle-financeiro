import os
import csv
import uuid
from datetime import datetime

# Chaves usadas no client_storage do Flet para o "Lembrar login"
CHAVE_ACCESS_TOKEN = "perrut.auth.access_token"
CHAVE_REFRESH_TOKEN = "perrut.auth.refresh_token"

def parse_valor_br(texto, padrao=0.0):
    """
    Converte um valor digitado no formato brasileiro (ex.: '1.234,56')
    para float (ex.: 1234.56).

    Centraliza a regra usada em vários campos do formulário (renda, valor do
    lançamento, etc.) para que uma mudança futura nessa conversão precise ser
    feita em um único lugar, em vez de em cada tela separadamente.

    Se o texto vier vazio ou inválido, retorna 'padrao' em vez de lançar erro.
    """
    if not texto:
        return padrao
    try:
        return float(str(texto).replace(".", "").replace(",", "."))
    except (ValueError, TypeError):
        return padrao

async def salvar_sessao_local(page, access_token, refresh_token):
    """Guarda os tokens da sessão no armazenamento local do dispositivo."""
    await page.shared_preferences.set(CHAVE_ACCESS_TOKEN, access_token)
    await page.shared_preferences.set(CHAVE_REFRESH_TOKEN, refresh_token)

async def limpar_sessao_local(page):
    """Remove os tokens salvos (usado no logout ou se a sessão expirar)."""
    await page.shared_preferences.remove(CHAVE_ACCESS_TOKEN)
    await page.shared_preferences.remove(CHAVE_REFRESH_TOKEN)

async def obter_sessao_local(page):
    """Retorna (access_token, refresh_token) salvos, ou (None, None) se não houver
    ou se a leitura falhar por qualquer motivo (ex.: chave inexistente)."""
    try:
        access_token = await page.shared_preferences.get(CHAVE_ACCESS_TOKEN)
        refresh_token = await page.shared_preferences.get(CHAVE_REFRESH_TOKEN)
        return access_token, refresh_token
    except Exception:
        return None, None

def obter_mes_ano_efetivo(item):
    """
    Calcula o mês e ano do lançamento.

    O campo 'created_at' já é gravado por adicionar_registro() com a data de
    vencimento escolhida pelo usuário (Vencimento Dia/Mês), inclusive para
    Cartão de Crédito. Por isso, aqui usamos o mês/ano diretamente dessa data,
    sem somar +1 mês novamente (isso duplicava o deslocamento e fazia uma
    compra com vencimento em Setembro aparecer no filtro de Outubro).
    """
    raw_data = item.get("created_at") or item.get("data")
    try:
        dt = datetime.fromisoformat(str(raw_data).replace("Z", "+00:00")) if raw_data else datetime.now()
    except Exception:
        dt = datetime.now()

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

        # Caminho relativo (usado quando o app roda como web, servido pelo Flet)
        url_relativa = f"/exports/{nome_arquivo}"
        return True, "✔ Relatório gerado! Iniciando o download...", (url_relativa, caminho_completo)
    except Exception as err:
        return False, f"❌ Erro ao exportar: {str(err)}", None