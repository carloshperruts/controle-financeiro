import flet as ft
import os
from datetime import datetime
import random
import asyncio
import requests
import re
import csv

# --- CONFIGURAÇÃO DO SUPABASE ---
SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://vmkkdenzkoqklvlulajo.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZta2tkZW56a29xa2x2bHVsYWpvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODgzNzg4NDIsImV4cCI6MjEwMzk1NDg0Mn0.vdCNnUnrRCQJuBKme-YYm9FqnyyV_BZ3Wh077uckxYA")

# --- HELPER DE SESSÃO / USUÁRIO ---
class User:
    def __init__(self, udata):
        self.id = udata.get("id")
        self.email = udata.get("email")

class Session:
    def __init__(self, sdata):
        self.access_token = sdata.get("access_token")
        self.user = User(sdata.get("user", {}))

# --- COMPONENTE DO FUNDO MATRIX ANIMADO ---
def criar_fundo_matrix_animado(page: ft.Page):
    chars = "01PERRUT$#@%&*+-="
    num_columns = 16
    column_controls = []

    for _ in range(num_columns):
        txt = ft.Text(
            value="\n".join(random.choices(chars, k=15)),
            size=12,
            color="#00FF66",
            opacity=random.uniform(0.1, 0.35),
            weight=ft.FontWeight.BOLD,
            font_family="Courier"
        )
        column_controls.append(txt)

    rain_row = ft.Row(
        controls=column_controls,
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        expand=True
    )

    async def animar():
        while True:
            try:
                for col in column_controls:
                    if random.random() > 0.4:
                        lines = [random.choice(chars) for _ in range(12)]
                        col.value = "\n".join(lines)
                        col.opacity = random.uniform(0.08, 0.3)
                page.update()
                await asyncio.sleep(0.15)
            except Exception:
                break

    asyncio.create_task(animar())

    return rain_row

# --- APLICAÇÃO PRINCIPAL ---
async def main(page: ft.Page):
    page.title = "Perrut - Controle Financeiro"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 15
    page.scroll = ft.ScrollMode.AUTO

    usuario_atual = {"session": None}
    msg_erro = ft.Text("", color=ft.Colors.RED_400, size=13, weight=ft.FontWeight.BOLD)
    msg_sucesso = ft.Text("", color=ft.Colors.GREEN_400, size=13, weight=ft.FontWeight.BOLD)

    modo_auth = "login"

    email_input = ft.TextField(label="E-mail", width=320, hint_text="exemplo@email.com")
    senha_input = ft.TextField(label="Senha", password=True, can_reveal_password=True, width=320)
    confirmar_senha_input = ft.TextField(
        label="Confirmar Senha", password=True, can_reveal_password=True, width=320
    )

    watermark = ft.Container(
        content=ft.Text(
            "PERRUT",
            size=100,
            weight=ft.FontWeight.BOLD,
            color="#00FF66",
            opacity=0.08,
        ),
        margin=ft.Margin(0, 10, 0, 0)
    )

    dicas_cadastro = ft.Container(
        content=ft.Column(
            [
                ft.Row([
                    ft.Icon(ft.Icons.INFO_OUTLINE, color="#00FF66", size=18),
                    ft.Text("Instruções para Cadastro:", weight=ft.FontWeight.BOLD, color="#00FF66", size=13)
                ]),
                ft.Text("• Insira um endereço de e-mail válido ao qual você tem acesso.", size=12, color=ft.Colors.GREY_300),
                ft.Text("• A senha deve conter pelo menos 6 caracteres.", size=12, color=ft.Colors.GREY_300),
                ft.Text("• Verifique sua caixa de entrada caso receba confirmação.", size=12, color=ft.Colors.GREY_300)
            ],
            spacing=4
        ),
        padding=12,
        bgcolor=ft.Colors.GREY_900,
        border=ft.Border(
            ft.BorderSide(1, "#00FF66"),
            ft.BorderSide(1, "#00FF66"),
            ft.BorderSide(1, "#00FF66"),
            ft.BorderSide(1, "#00FF66")
        ),
        border_radius=8,
        width=320
    )

    titulo_auth = ft.Text("Perrut - Controle Financeiro", size=24, weight=ft.FontWeight.BOLD, color="#00FF66")

    def mostrar_notificacao_global(texto, cor=ft.Colors.GREEN_600):
        snack = ft.SnackBar(
            content=ft.Text(texto, color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD),
            bgcolor=cor,
            duration=4000
        )
        page.overlay.append(snack)
        snack.open = True
        page.update()

    def mudar_modo_auth(novo_modo):
        nonlocal modo_auth
        modo_auth = novo_modo
        carregar_tela_login()

    def validar_email(email_str):
        regex = r"^[\w\.-]+@[\w\.-]+\.\w+$"
        return re.match(regex, email_str) is not None

    async def realizar_login(e):
        msg_erro.value = ""
        msg_sucesso.value = ""

        email_val = email_input.value.strip().lower()
        senha_val = senha_input.value.strip()

        if not email_val or not senha_val:
            msg_erro.value = "⚠️ Por favor, informe o e-mail e a senha."
            page.update()
            return

        try:
            url = f"{SUPABASE_URL}/auth/v1/token?grant_type=password"
            headers = {
                "apikey": SUPABASE_KEY,
                "Content-Type": "application/json"
            }
            payload = {
                "email": email_val,
                "password": senha_val
            }

            def api_call():
                return requests.post(url, json=payload, headers=headers)

            response = await asyncio.to_thread(api_call)
            data = response.json()

            if response.status_code != 200:
                err_msg = data.get("error_description") or data.get("msg") or "E-mail ou senha incorretos."
                msg_erro.value = f"❌ Erro ao entrar: {err_msg}"
                page.update()
                return

            usuario_atual["session"] = Session(data)
            await carregar_tela_principal()

        except Exception as ex:
            msg_erro.value = f"❌ Erro de conexão: {str(ex)}"
            page.update()

    async def realizar_cadastro(e):
        msg_erro.value = ""
        msg_sucesso.value = ""

        email_val = email_input.value.strip().lower()
        senha_val = senha_input.value.strip()
        conf_senha_val = confirmar_senha_input.value.strip()

        if not email_val:
            msg_erro.value = "⚠️ Por favor, informe um endereço de e-mail."
            page.update()
            return

        if not validar_email(email_val):
            msg_erro.value = "⚠️ Por favor, insira um e-mail válido (ex: seunome@email.com)."
            page.update()
            return

        if not senha_val:
            msg_erro.value = "⚠️ Por favor, crie uma senha."
            page.update()
            return

        if len(senha_val) < 6:
            msg_erro.value = "⚠️ A senha deve ter no mínimo 6 caracteres."
            page.update()
            return

        if senha_val != conf_senha_val:
            msg_erro.value = "⚠️ As senhas não coincidem. Verifique a digitação."
            page.update()
            return

        try:
            url = f"{SUPABASE_URL}/auth/v1/signup"
            headers = {
                "apikey": SUPABASE_KEY,
                "Content-Type": "application/json"
            }
            payload = {
                "email": email_val,
                "password": senha_val
            }

            def api_call():
                return requests.post(url, json=payload, headers=headers)

            response = await asyncio.to_thread(api_call)
            data = response.json()

            if response.status_code not in (200, 201):
                err_msg = data.get("msg") or data.get("error_description") or str(data)
                msg_erro.value = f"❌ Não foi possível criar a conta: {err_msg}"
                page.update()
                return

            mudar_modo_auth("login")
            msg_sucesso.value = "✔ Conta criada com sucesso! Digite sua senha para entrar."
            page.update()

        except Exception as ex:
            msg_erro.value = f"❌ Erro ao tentar cadastrar: {str(ex)}"
            page.update()

    async def recuperar_senha(e):
        msg_erro.value = ""
        msg_sucesso.value = ""

        email_val = email_input.value.strip().lower()

        if not email_val or not validar_email(email_val):
            msg_erro.value = "⚠️ Informe um e-mail válido para a recuperação."
            page.update()
            return

        try:
            url = f"{SUPABASE_URL}/auth/v1/recover"
            headers = {
                "apikey": SUPABASE_KEY,
                "Content-Type": "application/json"
            }
            payload = {"email": email_val}

            def api_call():
                return requests.post(url, json=payload, headers=headers)

            response = await asyncio.to_thread(api_call)

            if response.status_code in (200, 201):
                mudar_modo_auth("login")
                msg_sucesso.value = "✉️ E-mail de recuperação enviado! Verifique sua caixa de entrada."
            else:
                data = response.json()
                err_msg = data.get("msg") or data.get("error_description") or data.get("error") or str(data)
                msg_erro.value = f"❌ Erro ao solicitar recuperação: {err_msg}"

            page.update()

        except Exception as ex:
            msg_erro.value = f"❌ Erro de conexão: {str(ex)}"
            page.update()

    async def logout(e):
        usuario_atual["session"] = None
        mudar_modo_auth("login")

    def carregar_tela_login():
        page.clean()

        if modo_auth == "login":
            subtitulo = ft.Text("Acesse sua conta para continuar", size=14, color=ft.Colors.GREY_400)
            btn_acao = ft.ElevatedButton(
                "Entrar", 
                width=150, 
                bgcolor="#00AA44", 
                color=ft.Colors.WHITE,
                on_click=lambda ev: asyncio.create_task(realizar_login(ev))
            )
            btn_esqueci = ft.TextButton(
                "Esqueceu sua senha?", 
                on_click=lambda _: mudar_modo_auth("recuperar"),
                style=ft.ButtonStyle(color=ft.Colors.GREY_400)
            )
            btn_trocar = ft.TextButton(
                "Não tem uma conta? Cadastre-se aqui", 
                on_click=lambda _: mudar_modo_auth("cadastro")
            )

            conteudo_login = ft.Column(
                [
                    titulo_auth,
                    subtitulo,
                    ft.Divider(color="#00FF66", height=15),
                    msg_erro,
                    msg_sucesso,
                    email_input,
                    senha_input,
                    btn_esqueci,
                    ft.Row([btn_acao], alignment=ft.MainAxisAlignment.CENTER),
                    btn_trocar,
                    watermark
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=10
            )

        elif modo_auth == "cadastro":
            subtitulo = ft.Text("Preencha os dados abaixo para criar sua conta", size=14, color=ft.Colors.GREY_400)
            btn_acao = ft.ElevatedButton(
                "Cadastrar", 
                width=150, 
                bgcolor="#00AA44", 
                color=ft.Colors.WHITE,
                on_click=lambda ev: asyncio.create_task(realizar_cadastro(ev))
            )
            btn_trocar = ft.TextButton(
                "Voltar para a tela de login", 
                on_click=lambda _: mudar_modo_auth("login")
            )

            conteudo_login = ft.Column(
                [
                    titulo_auth,
                    subtitulo,
                    ft.Divider(color="#00FF66", height=15),
                    dicas_cadastro,
                    msg_erro,
                    msg_sucesso,
                    email_input,
                    senha_input,
                    confirmar_senha_input,
                    ft.Row([btn_acao], alignment=ft.MainAxisAlignment.CENTER),
                    btn_trocar,
                    watermark
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=10
            )

        elif modo_auth == "recuperar":
            subtitulo = ft.Text("Recuperação de Acesso", size=14, color=ft.Colors.GREY_400)
            instrucoes = ft.Text(
                "Digite seu e-mail cadastrado. Enviaremos as instruções para redefinir sua senha.",
                size=12,
                color=ft.Colors.GREY_300,
                text_align=ft.TextAlign.CENTER,
                width=320
            )
            btn_acao = ft.ElevatedButton(
                "Enviar E-mail", 
                width=160, 
                bgcolor="#00AA44", 
                color=ft.Colors.WHITE,
                on_click=lambda ev: asyncio.create_task(recuperar_senha(ev))
            )
            btn_trocar = ft.TextButton(
                "Voltar para o login", 
                on_click=lambda _: mudar_modo_auth("login")
            )

            conteudo_login = ft.Column(
                [
                    titulo_auth,
                    subtitulo,
                    ft.Divider(color="#00FF66", height=15),
                    instrucoes,
                    msg_erro,
                    msg_sucesso,
                    email_input,
                    ft.Row([btn_acao], alignment=ft.MainAxisAlignment.CENTER),
                    btn_trocar,
                    watermark
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=12
            )

        page.add(
            ft.Stack(
                [
                    criar_fundo_matrix_animado(page),
                    ft.Container(
                        content=conteudo_login, 
                        alignment=ft.Alignment(0, 0), 
                        padding=20
                    )
                ],
                expand=True
            )
        )
        page.update()

    async def carregar_tela_principal():
        try:
            page.clean()

            user_session = usuario_atual.get("session")
            user_email = user_session.user.email if user_session and user_session.user else "Usuário"
            user_id = user_session.user.id if user_session and user_session.user else None
            token = user_session.access_token if user_session else SUPABASE_KEY

            txt_renda_base = ft.TextField(label="Renda Base (R$)", value="0,00", width=150)
            txt_descricao = ft.TextField(label="Descrição", expand=True)
            txt_valor = ft.TextField(label="Valor (R$)", width=150)

            dd_categoria = ft.Dropdown(
                label="Categoria",
                value="Outros",
                width=150,
                options=[
                    ft.dropdown.Option("Alimentação"),
                    ft.dropdown.Option("Moradia"),
                    ft.dropdown.Option("Transporte"),
                    ft.dropdown.Option("Lazer"),
                    ft.dropdown.Option("Outros"),
                ]
            )

            txt_busca = ft.TextField(label="Buscar", prefix_icon=ft.Icons.SEARCH, expand=True)
            dd_filtro = ft.Dropdown(
                label="Filtrar Categoria",
                value="Todas",
                width=150,
                options=[
                    ft.dropdown.Option("Todas"),
                    ft.dropdown.Option("Alimentação"),
                    ft.dropdown.Option("Moradia"),
                    ft.dropdown.Option("Transporte"),
                    ft.dropdown.Option("Lazer"),
                    ft.dropdown.Option("Outros"),
                ]
            )

            mes_atual_str = str(datetime.now().month).zfill(2)
            ano_atual_str = str(datetime.now().year)

            def ao_mudar_periodo(e):
                asyncio.create_task(carregar_registros())

            dd_mes_relatorio = ft.Dropdown(
                label="Mês do Período",
                value=mes_atual_str,
                width=130,
                options=[
                    ft.dropdown.Option("01", "Janeiro"),
                    ft.dropdown.Option("02", "Fevereiro"),
                    ft.dropdown.Option("03", "Março"),
                    ft.dropdown.Option("04", "Abril"),
                    ft.dropdown.Option("05", "Maio"),
                    ft.dropdown.Option("06", "Junho"),
                    ft.dropdown.Option("07", "Julho"),
                    ft.dropdown.Option("08", "Agosto"),
                    ft.dropdown.Option("09", "Setembro"),
                    ft.dropdown.Option("10", "Outubro"),
                    ft.dropdown.Option("11", "Novembro"),
                    ft.dropdown.Option("12", "Dezembro"),
                ]
            )
            dd_mes_relatorio.on_change = ao_mudar_periodo

            dd_ano_relatorio = ft.Dropdown(
                label="Ano",
                value=ano_atual_str,
                width=110,
                options=[
                    ft.dropdown.Option("2024"),
                    ft.dropdown.Option("2025"),
                    ft.dropdown.Option("2026"),
                ]
            )
            dd_ano_relatorio.on_change = ao_mudar_periodo

            lbl_receitas = ft.Text("Receitas (Mês): R$ 0.00", color=ft.Colors.GREEN_400, weight=ft.FontWeight.BOLD)
            lbl_gastos = ft.Text("Gastos (Mês): R$ 0.00", color=ft.Colors.RED_400, weight=ft.FontWeight.BOLD)
            lbl_saldo = ft.Text("Saldo do Mês: R$ 0.00", color=ft.Colors.GREEN_400, size=18, weight=ft.FontWeight.BOLD)

            lista_gastos_ui = ft.Column()
            grafico_ui = ft.Column()

            registros_cache = []

            # --- LÓGICA DE EXPORTAÇÃO EXCEL / CSV DIRETA ---
            def exportar_para_excel(e):
                if not registros_cache:
                    mostrar_notificacao_global("⚠️ Nenhum registro encontrado para exportar!", ft.Colors.AMBER_600)
                    return

                mes_sel = str(dd_mes_relatorio.value).zfill(2)
                ano_sel = str(dd_ano_relatorio.value)
                
                dados_filtrados = []
                for item in registros_cache:
                    raw_data = item.get("created_at") or item.get("data")
                    if raw_data:
                        try:
                            dt = datetime.fromisoformat(str(raw_data).replace("Z", "+00:00"))
                            if str(dt.month).zfill(2) == mes_sel and str(dt.year) == ano_sel:
                                dados_filtrados.append(item)
                        except Exception:
                            dados_filtrados.append(item)
                    else:
                        dados_filtrados.append(item)

                if not dados_filtrados:
                    mostrar_notificacao_global(f"⚠️ Nenhum lançamento para o mês {mes_sel}/{ano_sel}!", ft.Colors.AMBER_600)
                    return

                try:
                    # Salva direto na pasta Downloads ou pasta do Usuário
                    caminho_user = os.path.expanduser("~")
                    pasta_destino = os.path.join(caminho_user, "Downloads")
                    if not os.path.exists(pasta_destino):
                        pasta_destino = caminho_user

                    nome_arquivo = f"Relatorio_Financeiro_{mes_sel}_{ano_sel}.csv"
                    caminho_completo = os.path.join(pasta_destino, nome_arquivo)

                    with open(caminho_completo, mode="w", newline="", encoding="utf-8-sig") as f:
                        writer = csv.writer(f, delimiter=";")
                        writer.writerow(["Data", "Descrição", "Categoria", "Tipo", "Valor (R$)"])
                        for item in dados_filtrados:
                            raw_d = item.get("created_at") or item.get("data")
                            dt_fmt = ""
                            if raw_d:
                                try:
                                    dt = datetime.fromisoformat(str(raw_d).replace("Z", "+00:00"))
                                    dt_fmt = dt.strftime("%d/%m/%Y %H:%M")
                                except Exception:
                                    dt_fmt = str(raw_d)

                            val_str = f"{float(item.get('valor', 0)):.2f}".replace(".", ",")
                            writer.writerow([
                                dt_fmt,
                                item.get("descricao", ""),
                                item.get("categoria", ""),
                                item.get("tipo", "Gasto"),
                                val_str
                            ])

                    mostrar_notificacao_global(f"✔ Relatório salvo em: {caminho_completo}")

                except Exception as err:
                    mostrar_notificacao_global(f"❌ Erro ao exportar: {str(err)}", ft.Colors.RED_600)

            async def carregar_renda_usuario():
                try:
                    url = f"{SUPABASE_URL}/rest/v1/configuracoes?user_id=eq.{user_id}&select=renda_base"
                    headers = {
                        "apikey": SUPABASE_KEY,
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json"
                    }

                    def fetch_renda():
                        return requests.get(url, headers=headers)

                    res = await asyncio.to_thread(fetch_renda)
                    if res.status_code == 200 and res.json():
                        valor_renda = res.json()[0].get("renda_base", 0.0)
                        txt_renda_base.value = f"{float(valor_renda):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                        page.update()
                except Exception:
                    pass

            async def salvar_renda_base(e=None):
                try:
                    raw_val = txt_renda_base.value.strip()
                    val_clean = raw_val.replace(".", "").replace(",", ".")
                    renda_num = float(val_clean)

                    headers = {
                        "apikey": SUPABASE_KEY,
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json",
                        "Prefer": "return=representation"
                    }

                    url_patch = f"{SUPABASE_URL}/rest/v1/configuracoes?user_id=eq.{user_id}"
                    payload = {"renda_base": renda_num}

                    def sync_patch():
                        return requests.patch(url_patch, json=payload, headers=headers)

                    res = await asyncio.to_thread(sync_patch)

                    if res.status_code == 200 and len(res.json()) == 0:
                        url_post = f"{SUPABASE_URL}/rest/v1/configuracoes"
                        payload_post = {"user_id": user_id, "renda_base": renda_num}

                        def sync_post():
                            return requests.post(url_post, json=payload_post, headers=headers)

                        res = await asyncio.to_thread(sync_post)

                    if res.status_code in (200, 201, 204):
                        mostrar_notificacao_global("✔ Renda base atualizada com sucesso!")
                        await carregar_registros()
                    else:
                        mostrar_notificacao_global(f"❌ Erro RLS Supabase ({res.status_code}): Verifique as permissões da tabela 'configuracoes'", ft.Colors.RED_600)
                except ValueError:
                    mostrar_notificacao_global("⚠️ Valor de renda inválido!", ft.Colors.RED_600)
                except Exception as ex:
                    mostrar_notificacao_global(f"❌ Erro: {str(ex)}", ft.Colors.RED_600)

            def calcular_totais(registros_filtrados):
                tot_receita = sum(float(r["valor"]) for r in registros_filtrados if r.get("tipo") == "Receita")
                tot_gasto = sum(float(r["valor"]) for r in registros_filtrados if r.get("tipo") == "Gasto")

                try:
                    val_clean = txt_renda_base.value.strip().replace(".", "").replace(",", ".")
                    renda_base = float(val_clean)
                except ValueError:
                    renda_base = 0.0

                saldo = renda_base + tot_receita - tot_gasto

                lbl_receitas.value = f"Receitas: R$ {tot_receita:.2f}"
                lbl_gastos.value = f"Gastos: R$ {tot_gasto:.2f}"
                lbl_saldo.value = f"Saldo do Mês: R$ {saldo:.2f}"
                lbl_saldo.color = ft.Colors.GREEN_400 if saldo >= 0 else ft.Colors.RED_400

            def atualizar_grafico(registros_filtrados):
                grafico_ui.controls.clear()
                gastos = [r for r in registros_filtrados if r.get("tipo", "Gasto") == "Gasto"]
                tot_gasto = sum(float(r["valor"]) for r in gastos)

                if tot_gasto == 0:
                    return

                categorias = {}
                for g in gastos:
                    cat = g.get("categoria", "Outros")
                    val = float(g.get("valor", 0))
                    categorias[cat] = categorias.get(cat, 0.0) + val

                cores = [
                    "#00FF66",
                    ft.Colors.AMBER_400,
                    ft.Colors.PURPLE_400,
                    ft.Colors.TEAL_400,
                    ft.Colors.ORANGE_400,
                    ft.Colors.PINK_400
                ]

                grafico_ui.controls.append(ft.Text("📊 Distribuição de Gastos Por Categoria", weight=ft.FontWeight.BOLD, size=16))

                for idx, (cat, val) in enumerate(categorias.items()):
                    porcentagem = (val / tot_gasto) * 100
                    cor = cores[idx % len(cores)]

                    grafico_ui.controls.append(
                        ft.Column(
                            [
                                ft.Row(
                                    [
                                        ft.Text(f"{cat}", weight=ft.FontWeight.BOLD),
                                        ft.Text(f"R$ {val:.2f} ({porcentagem:.1f}%)", color=cor, weight=ft.FontWeight.BOLD),
                                    ],
                                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                                ),
                                ft.ProgressBar(value=porcentagem / 100, color=cor, bgcolor=ft.Colors.GREY_800, height=8)
                            ]
                        )
                    )

            def abrir_relatorio_mensal(e):
                mes_sel = dd_mes_relatorio.value
                ano_sel = dd_ano_relatorio.value

                itens_mes = []
                for item in registros_cache:
                    raw_data = item.get("created_at") or item.get("data")
                    if raw_data:
                        try:
                            dt = datetime.fromisoformat(str(raw_data).replace("Z", "+00:00"))
                            m_str = str(dt.month).zfill(2)
                            a_str = str(dt.year)
                            if m_str == mes_sel and a_str == ano_sel:
                                itens_mes.append((item, dt))
                        except Exception:
                            pass

                tot_receitas = sum(float(x[0]["valor"]) for x in itens_mes if x[0].get("tipo") == "Receita")
                tot_gastos = sum(float(x[0]["valor"]) for x in itens_mes if x[0].get("tipo") == "Gasto")

                try:
                    val_clean = txt_renda_base.value.strip().replace(".", "").replace(",", ".")
                    renda_base = float(val_clean)
                except ValueError:
                    renda_base = 0.0

                saldo_final = renda_base + tot_receitas - tot_gastos

                if saldo_final >= 0:
                    status_text = f"🟢 SUPERÁVIT DE R$ {saldo_final:.2f}"
                    status_color = ft.Colors.GREEN_400
                    diag_desc = "Suas contas fecharam no positivo neste mês!"
                else:
                    status_text = f"🔴 DÉFICIT DE R$ {abs(saldo_final):.2f}"
                    status_color = ft.Colors.RED_400
                    diag_desc = "Atenção: Suas despesas superaram os rendimentos neste mês!"

                lista_itens_dialog = ft.Column(spacing=5, scroll=ft.ScrollMode.AUTO, height=200)
                if not itens_mes:
                    lista_itens_dialog.controls.append(ft.Text("Nenhum registro encontrado para este período.", color=ft.Colors.GREY_400))
                else:
                    for item, dt in itens_mes:
                        tipo = item.get("tipo", "Gasto")
                        val = float(item.get("valor", 0))
                        sinal = "+" if tipo == "Receita" else "-"
                        cor_v = ft.Colors.GREEN_400 if tipo == "Receita" else ft.Colors.RED_400

                        lista_itens_dialog.controls.append(
                            ft.Container(
                                content=ft.Row([
                                    ft.Text(f"{dt.strftime('%d/%m')} - {item.get('descricao', '')} ({item.get('categoria', '')})", size=13),
                                    ft.Text(f"{sinal}R$ {val:.2f}", color=cor_v, weight=ft.FontWeight.BOLD, size=13)
                                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                                padding=5,
                                bgcolor=ft.Colors.GREY_900,
                                border_radius=4
                            )
                        )

                def fechar_dialog(ev):
                    dialog.open = False
                    page.update()

                dialog = ft.AlertDialog(
                    title=ft.Text(f"📋 Relatório Mensal: {mes_sel}/{ano_sel}", weight=ft.FontWeight.BOLD),
                    content=ft.Column(
                        [
                            ft.Container(
                                content=ft.Column([
                                    ft.Text("RESULTADO FINAL", size=12, color=ft.Colors.GREY_400, weight=ft.FontWeight.BOLD),
                                    ft.Text(status_text, size=20, weight=ft.FontWeight.BOLD, color=status_color),
                                    ft.Text(diag_desc, size=12, italic=True),
                                ]),
                                padding=10,
                                border=ft.Border(
                                    ft.BorderSide(1, status_color),
                                    ft.BorderSide(1, status_color),
                                    ft.BorderSide(1, status_color),
                                    ft.BorderSide(1, status_color)
                                ),
                                border_radius=8,
                                bgcolor=ft.Colors.GREY_800
                            ),
                            ft.Divider(),
                            ft.Row([
                                ft.Text(f"Renda Base: R$ {renda_base:.2f}"),
                                ft.Text(f"Receitas Extra: R$ {tot_receitas:.2f}", color=ft.Colors.GREEN_400),
                            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                            ft.Row([
                                ft.Text(f"Total Gastos: R$ {tot_gastos:.2f}", color=ft.Colors.RED_400),
                                ft.Text(f"Total Lançamentos: {len(itens_mes)}"),
                            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                            ft.Divider(),
                            ft.Text("Lançamentos do Mês:", weight=ft.FontWeight.BOLD),
                            lista_itens_dialog
                        ],
                        tight=True,
                        width=450
                    ),
                    actions=[
                        ft.TextButton("Fechar", on_click=fechar_dialog)
                    ],
                )

                page.overlay.append(dialog)
                dialog.open = True
                page.update()

            async def carregar_registros(e=None):
                nonlocal registros_cache
                lista_gastos_ui.controls.clear()
                try:
                    url = f"{SUPABASE_URL}/rest/v1/gastos?select=*&order=id.desc"
                    if user_id:
                        url += f"&user_id=eq.{user_id}"

                    headers = {
                        "apikey": SUPABASE_KEY,
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json"
                    }

                    def fetch_db():
                        return requests.get(url, headers=headers)

                    res = await asyncio.to_thread(fetch_db)
                    registros = res.json() if res.status_code == 200 else []

                    if not isinstance(registros, list):
                        registros = []

                    registros_cache = registros

                    termo_busca = txt_busca.value.lower() if txt_busca.value else ""
                    cat_filtro = dd_filtro.value
                    mes_sel = str(dd_mes_relatorio.value).zfill(2)
                    ano_sel = str(dd_ano_relatorio.value)

                    registros_filtrados_mes = []

                    for item in registros:
                        desc = str(item.get("descricao", ""))
                        cat = str(item.get("categoria", ""))
                        raw_data = item.get("created_at") or item.get("data")

                        data_valida = True
                        str_data_hora = ""
                        if raw_data:
                            try:
                                dt = datetime.fromisoformat(str(raw_data).replace("Z", "+00:00"))
                                m_str = str(dt.month).zfill(2)
                                a_str = str(dt.year)
                                str_data_hora = dt.strftime("%d/%m/%Y %H:%M")

                                if m_str != mes_sel or a_str != ano_sel:
                                    data_valida = False
                            except Exception:
                                str_data_hora = str(raw_data)
                        else:
                            str_data_hora = datetime.now().strftime("%d/%m/%Y %H:%M")

                        if not data_valida:
                            continue

                        registros_filtrados_mes.append(item)

                        if termo_busca and termo_busca not in desc.lower():
                            continue
                        if cat_filtro != "Todas" and cat != cat_filtro:
                            continue

                        item_id = item["id"]
                        tipo = item.get("tipo", "Gasto")
                        valor = float(item.get("valor", 0))
                        cor_valor = ft.Colors.GREEN_400 if tipo == "Receita" else ft.Colors.RED_400
                        sinal = "+" if tipo == "Receita" else "-"

                        btn_deletar = ft.IconButton(
                            icon=ft.Icons.DELETE_OUTLINE,
                            icon_color=ft.Colors.RED_400,
                            tooltip="Excluir",
                            on_click=lambda e, i=item_id: asyncio.create_task(deletar_registro(i))
                        )

                        card_item = ft.Container(
                            content=ft.Row(
                                [
                                    ft.Column(
                                        [
                                            ft.Text(desc, weight=ft.FontWeight.BOLD, size=16),
                                            ft.Text(f"{cat} • {str_data_hora} • {sinal}R$ {valor:.2f}", color=cor_valor),
                                        ],
                                        expand=True
                                    ),
                                    btn_deletar
                                ],
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                            ),
                            padding=10,
                            border_radius=8,
                            bgcolor=ft.Colors.GREY_900
                        )
                        lista_gastos_ui.controls.append(card_item)

                    if not lista_gastos_ui.controls:
                        lista_gastos_ui.controls.append(
                            ft.Container(
                                content=ft.Text("Nenhum lançamento para este mês até o momento.", color=ft.Colors.GREY_500, size=13),
                                padding=15,
                                alignment=ft.Alignment(0, 0)
                            )
                        )

                    calcular_totais(registros_filtrados_mes)
                    atualizar_grafico(registros_filtrados_mes)
                except Exception as ex:
                    mostrar_notificacao_global(f"Erro ao carregar dados: {str(ex)}", ft.Colors.RED_600)

                page.update()

            async def salvar_transacao(tipo):
                if not txt_descricao.value or not txt_valor.value:
                    mostrar_notificacao_global("Preencha a descrição e o valor!", ft.Colors.RED_600)
                    return

                try:
                    valor_num = float(txt_valor.value.replace(".", "").replace(",", "."))

                    payload = {
                        "descricao": txt_descricao.value.strip(),
                        "valor": valor_num,
                        "categoria": dd_categoria.value,
                        "tipo": tipo,
                        "user_id": user_id
                    }

                    url = f"{SUPABASE_URL}/rest/v1/gastos"
                    headers = {
                        "apikey": SUPABASE_KEY,
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json",
                        "Prefer": "return=representation"
                    }

                    def post_db():
                        return requests.post(url, json=payload, headers=headers)

                    res = await asyncio.to_thread(post_db)

                    if res.status_code not in (200, 201):
                        mostrar_notificacao_global(f"Erro ao salvar: {res.text}", ft.Colors.RED_600)
                        return

                    txt_descricao.value = ""
                    txt_valor.value = ""
                    mostrar_notificacao_global("✔ Lançamento salvo com sucesso no banco!")
                    await carregar_registros()
                except Exception as ex:
                    mostrar_notificacao_global(f"Erro ao salvar: {str(ex)}", ft.Colors.RED_600)

            async def deletar_registro(item_id):
                try:
                    url = f"{SUPABASE_URL}/rest/v1/gastos?id=eq.{item_id}"
                    headers = {
                        "apikey": SUPABASE_KEY,
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json"
                    }

                    def delete_db():
                        return requests.delete(url, headers=headers)

                    await asyncio.to_thread(delete_db)
                    mostrar_notificacao_global("🗑️ Registro excluído!")
                    await carregar_registros()
                except Exception as ex:
                    mostrar_notificacao_global(f"Erro ao excluir: {str(ex)}", ft.Colors.RED_600)

            txt_busca.on_change = lambda e: asyncio.create_task(carregar_registros(e))
            dd_filtro.on_change = lambda e: asyncio.create_task(carregar_registros(e))

            btn_receita = ft.ElevatedButton(
                content=ft.Text("+ Receita", color=ft.Colors.WHITE),
                bgcolor=ft.Colors.GREEN_700,
                on_click=lambda e: asyncio.create_task(salvar_transacao("Receita")),
                expand=True
            )

            btn_gasto = ft.ElevatedButton(
                content=ft.Text("- Despesa", color=ft.Colors.WHITE),
                bgcolor=ft.Colors.RED_700,
                on_click=lambda e: asyncio.create_task(salvar_transacao("Gasto")),
                expand=True
            )

            btn_gerar_relatorio = ft.ElevatedButton(
                "📊 Ver Relatório Mensal",
                on_click=abrir_relatorio_mensal,
                bgcolor=ft.Colors.BLUE_800,
                color=ft.Colors.WHITE,
                icon=ft.Icons.ASSESSMENT
            )

            btn_exportar_excel = ft.ElevatedButton(
                "📥 Exportar CSV/Excel",
                on_click=exportar_para_excel,
                bgcolor=ft.Colors.TEAL_800,
                color=ft.Colors.WHITE,
                icon=ft.Icons.FILE_DOWNLOAD
            )

            btn_salvar_renda = ft.ElevatedButton(
                "Salvar Renda", 
                on_click=lambda e: asyncio.create_task(salvar_renda_base()),
                icon=ft.Icons.SAVE
            )

            btn_refresh = ft.IconButton(
                icon=ft.Icons.REFRESH,
                tooltip="Atualizar Dados",
                icon_color="#00FF66",
                on_click=lambda e: asyncio.create_task(carregar_registros(e))
            )

            header_app = ft.Row(
                [
                    ft.Text("Perrut - Controle Financeiro", size=24, weight=ft.FontWeight.BOLD, color="#00FF66"),
                    ft.Row(
                        [
                            btn_refresh,
                            ft.Text(f"👤 {user_email.split('@')[0]}", weight=ft.FontWeight.BOLD, size=13),
                            ft.TextButton("Sair", on_click=logout, style=ft.ButtonStyle(color=ft.Colors.RED_400))
                        ]
                    )
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN
            )

            conteudo_principal = ft.Column(
                [
                    header_app,
                    ft.Divider(color="#00FF66", height=1),
                    ft.Row([txt_renda_base, btn_salvar_renda]),

                    ft.Container(
                        content=ft.Row([
                            dd_mes_relatorio,
                            dd_ano_relatorio,
                            btn_gerar_relatorio,
                            btn_exportar_excel
                        ], alignment=ft.MainAxisAlignment.START, wrap=True),
                        padding=10,
                        bgcolor=ft.Colors.GREY_900,
                        border_radius=8
                    ),

                    ft.Row([lbl_receitas, lbl_gastos], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Row([lbl_saldo], alignment=ft.MainAxisAlignment.CENTER),
                    grafico_ui,
                    ft.Row([txt_descricao]),
                    ft.Row([txt_valor, dd_categoria]),
                    ft.Row([btn_receita, btn_gasto]),
                    ft.Row([txt_busca, dd_filtro]),
                    lista_gastos_ui
                ]
            )

            page.add(
                ft.Stack(
                    [
                        criar_fundo_matrix_animado(page),
                        conteudo_principal
                    ],
                    expand=True
                )
            )

            await carregar_renda_usuario()
            await carregar_registros()
        except Exception as main_err:
            page.add(ft.Text(f"⚠️ Erro ao carregar tela principal: {str(main_err)}", color=ft.Colors.RED_400))
            page.update()

    carregar_tela_login()

ft.app(target=main)