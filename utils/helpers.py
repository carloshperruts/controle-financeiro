import os
import csv
import re
import uuid
from datetime import datetime
from zoneinfo import ZoneInfo

# Chaves usadas no client_storage do Flet para o "Lembrar login"
CHAVE_ACCESS_TOKEN = "perrut.auth.access_token"
CHAVE_REFRESH_TOKEN = "perrut.auth.refresh_token"

# Regex simples de formato de e-mail: não valida se o e-mail existe de fato
# (isso só o Supabase Auth pode confirmar), só pega erros óbvios de digitação
# como "sememail", "nome@", ou "nome@dominio" sem extensão.
_PADRAO_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def validar_formato_email(email):
    """Retorna True se o texto tem o formato básico de um e-mail válido."""
    if not email:
        return False
    return bool(_PADRAO_EMAIL.match(email.strip()))


def parse_valor_br(texto, padrao=0.0):
    """
    Converte um valor digitado no formato brasileiro (ex.: '1.234,56')
    para float (ex.: 1234.56).

    Centraliza a regra usada em vários campos do formulário (renda, valor do
    lançamento, etc.) para que uma mudança futura nessa conversão precise ser
    feita em um único lugar, em vez de em cada tela separadamente.

    Se o texto vier vazio ou inválido, retorna 'padrao' em vez de lançar erro.

    Regras de leitura:
      - "R$" e espaços são ignorados ("R$ 50,00" -> 50.0).
      - Com vírgula, vale o formato brasileiro: ponto = milhar, vírgula = decimal.
      - Sem vírgula e com um único ponto seguido de 1 ou 2 dígitos, o ponto é
        decimal ("1234.56" -> 1234.56). Com 3 dígitos depois ("1.234"), é milhar.
      - Notação científica, "nan", "inf" e formato americano ("1,234.56") são
        recusados e devolvem 'padrao'.
    """
    if not texto:
        return padrao
    t = re.sub(r"(?i)R\$|\s", "", str(texto))
    if "," in t:
        if t.rfind(".") > t.rfind(","):
            return padrao
        t = t.replace(".", "").replace(",", ".")
    elif t.count(".") == 1 and len(t.split(".")[1]) != 3:
        pass
    else:
        t = t.replace(".", "")
    if not re.fullmatch(r"-?\d+(\.\d+)?", t):
        return padrao
    return float(t)


def calcular_valor_parcela(valor_total, num_parcelas):
    """
    Divide o valor total de uma compra pelo número de parcelas, arredondado
    para 2 casas decimais (padrão de moeda).

    Ex.: calcular_valor_parcela(100.0, 3) -> 33.33
    """
    return round(valor_total / num_parcelas, 2)


def calcular_valores_parcelas(valor_total, num_parcelas):
    """
    Devolve a lista com o valor de cada parcela, garantindo que a SOMA delas
    seja exatamente o valor total (sem perder nem inventar centavos).

    Dividir e arredondar igual para todas as parcelas perde centavos
    (100,00 em 3x virava 33,33 x 3 = 99,99). Aqui o cálculo é feito em
    centavos inteiros e os centavos que sobram são distribuídos, de 1 em 1,
    entre as primeiras parcelas. Assim nenhuma parcela fica negativa e a
    diferença entre duas parcelas quaisquer é de no máximo 1 centavo.

    Ex.: calcular_valores_parcelas(100.0, 3) -> [33.34, 33.33, 33.33]
    """
    centavos_total = round(valor_total * 100)
    base, sobra = divmod(centavos_total, num_parcelas)
    return [(base + (1 if i < sobra else 0)) / 100 for i in range(num_parcelas)]


def calcular_data_parcela(dt_base, indice_parcela):
    """
    Calcula a data (ano, mês, dia, hora) da N-ésima parcela de uma compra
    parcelada, a partir de uma data base (dt_base) e do índice da parcela
    (0 para a 1ª parcela, 1 para a 2ª, etc.).

    O mês avança 'indice_parcela' meses a partir de dt_base, rolando para o
    ano seguinte automaticamente quando ultrapassa dezembro (ex.: parcela 3
    de uma compra em novembro/2026 cai em janeiro/2027, não mês 14).

    O dia é limitado a 28, para evitar erros em meses com menos dias (todo
    mês tem pelo menos 28 dias, então isso nunca gera uma data inválida).

    Retorna um datetime "naive" (sem timezone), com a mesma hora/minuto/
    segundo de dt_base — preservando a hora real do cadastro.
    """
    mes_parc = dt_base.month + indice_parcela
    ano_parc = dt_base.year + ((mes_parc - 1) // 12)
    mes_parc = ((mes_parc - 1) % 12) + 1
    return datetime(
        ano_parc, mes_parc, min(dt_base.day, 28),
        dt_base.hour, dt_base.minute, dt_base.second
    )

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

# Fuso usado para decidir em qual mês/ano um lançamento cai. O servidor (Render)
# e o banco trabalham em UTC, mas o mês que o usuário espera ver é o de Brasília.
FUSO_BR = ZoneInfo("America/Sao_Paulo")


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
        # Datas com fuso (ex.: UTC vindo do Supabase) são convertidas para Brasília;
        # datas sem fuso já são tratadas como horário local e ficam como estão.
        if dt.tzinfo is not None:
            dt = dt.astimezone(FUSO_BR).replace(tzinfo=None)
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


def exportar_para_pdf(registros_cache, mes_sel, ano_sel, renda_base=0.0):
    """
    Gera um relatório em PDF com os registros do mês/ano selecionado,
    incluindo um resumo (Receitas/Despesas/Saldo) no topo.

    Segue o mesmo padrão de segurança e localização de arquivo usado em
    exportar_para_csv: salvo em assets/exports com um nome imprevisível,
    servido publicamente pelo Flet para o navegador baixar.

    O import do reportlab é feito aqui dentro (não no topo do arquivo) para
    que, se a biblioteca não estiver instalada, apenas a exportação em PDF
    falhe com uma mensagem clara — sem quebrar o restante do app, que não
    depende dela.
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
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import cm
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet

        total_receitas = sum(float(item.get("valor", 0)) for item, _ in dados_filtrados if item.get("tipo") == "Receita")
        total_despesas = sum(float(item.get("valor", 0)) for item, _ in dados_filtrados if item.get("tipo") == "Despesa")
        saldo = (renda_base + total_receitas) - total_despesas

        pasta_destino = os.path.join(os.getcwd(), "assets", "exports")
        os.makedirs(pasta_destino, exist_ok=True)

        token = uuid.uuid4().hex[:12]
        nome_arquivo = f"Relatorio_{mes_sel}_{ano_sel}_{token}.pdf"
        caminho_completo = os.path.join(pasta_destino, nome_arquivo)

        doc = SimpleDocTemplate(caminho_completo, pagesize=A4, topMargin=1.5 * cm, bottomMargin=1.5 * cm)
        estilos = getSampleStyleSheet()
        elementos = []

        elementos.append(Paragraph(f"Perrut - Relatório Mensal: {mes_sel}/{ano_sel}", estilos["Title"]))
        elementos.append(Spacer(1, 0.3 * cm))
        elementos.append(Paragraph(
            f"Renda: R$ {renda_base:.2f} &nbsp;&nbsp; "
            f"Receitas: R$ {total_receitas:.2f} &nbsp;&nbsp; "
            f"Despesas: R$ {total_despesas:.2f} &nbsp;&nbsp; "
            f"Saldo: R$ {saldo:.2f}",
            estilos["Normal"]
        ))
        elementos.append(Spacer(1, 0.5 * cm))

        cabecalho = ["Data", "Descrição", "Categoria", "Pagamento", "Tipo", "Valor (R$)"]
        linhas_tabela = [cabecalho]
        for item, dt in dados_filtrados:
            linhas_tabela.append([
                dt.strftime("%d/%m/%Y"),
                item.get("descricao", ""),
                item.get("categoria", ""),
                item.get("forma_pagamento", "Débito / Pix"),
                item.get("tipo", "Despesa"),
                f"{float(item.get('valor', 0)):.2f}".replace(".", ","),
            ])

        tabela = Table(linhas_tabela, repeatRows=1)
        tabela.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2E7D32")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F0F0F0")]),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        elementos.append(tabela)

        doc.build(elementos)

        url_relativa = f"/exports/{nome_arquivo}"
        return True, "✔ PDF gerado! Iniciando o download...", (url_relativa, caminho_completo)
    except Exception as err:
        return False, f"❌ Erro ao exportar PDF: {str(err)}", None