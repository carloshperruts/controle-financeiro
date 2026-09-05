import flet as ft
import os
from datetime import datetime, timedelta
import random
import asyncio
import csv
from supabase import create_client, Client

# --- CONFIGURAÇÃO DO SUPABASE ---
SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://vmkkdenzkoqklvlulajo.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZta2tkZW56a29xa2x2bHVsYWpvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODgzNzg4NDIsImV4cCI6MjEwMzk1NDg0Mn0.vdCNnUnrRCQJuBKme-YYm9FqnyyV_BZ3Wh077uckxYA")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- LISTA EXPANDIDA DE CATEGORIAS ---
CATEGORIAS = [
    "Alimentação",
    "Moradia",
    "Transporte",
    "Saúde & Bem-Estar",
    "Educação",
    "Lazer & Viagens",
    "Assinaturas & Serviços",
    "Compras & Vestuário",
    "Dívidas & Empréstimos",
    "Investimentos & Reserva",
    "Rendimento & Salário",
    "Outros"
]

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

    usuario_atual = {"session": None, "user": None}
    msg_erro = ft.Text("", color=ft.Colors.RED_400, size=13, weight=ft.FontWeight.BOLD)
    msg_sucesso = ft.Text("", color=ft.Colors.GREEN_400, size=13, weight=ft.FontWeight.BOLD)

    modo_auth = "login"

    email_input = ft.TextField(label="E-mail", width=320, hint_text="exemplo@email.com")
    senha_input = ft.TextField(label="Senha", password=True, can_reveal_password=True, width=320)
    confirmar_senha_input = ft.TextField(
        label="Confirmar Senha", password=True, can_reveal_password=True, width=320
    )

    watermark = ft.Container(
        content=ft.Text("PERRUT", size=100, weight=ft.FontWeight.BOLD, color="#00FF66", opacity=0.08),
        margin=ft.Margin(0, 10, 0, 0)
    )

    dicas_cadastro = ft.Container(
        content=ft.Column(
            [
                ft.Row([
                    ft.Icon(ft.Icons.INFO_OUTLINE, color="#00FF66", size=18),
                    ft.Text("Instruções para Cadastro:", weight=ft.FontWeight.BOLD, color="#00FF66", size=13)
                ]),
                ft.Text("• Insira um endereço de e-mail válido.", size=12, color=ft.Colors.GREY_300),
                ft.Text("• A senha deve conter pelo menos 6 caracteres.", size=12, color=ft.Colors.GREY_300),
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
            duration=2500
        )
        page.overlay.append(snack)
        snack.open = True
        page.update()

    def mudar_modo_auth(novo_modo):
        nonlocal modo_auth
        modo_auth = novo_modo
        carregar_tela_login()

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
            def api_call():
                return supabase.auth.sign_in_with_password({
                    "email": email_val,
                    "password": senha_val
                })

            res = await asyncio.to_thread(api_call)

            if res.user and res.session:
                usuario_atual["session"] = res.session
                usuario_atual["user"] = res.user
                await carregar_tela_principal()
            else:
                msg_erro.value = "❌ Falha ao autenticar. Verifique seus dados."
                page.update()

        except Exception as ex:
            msg_erro.value = f"❌ Erro ao entrar: {str(ex)}"
            page.update()

    async def realizar_cadastro(e):
        msg_erro.value = ""
        msg_sucesso.value = ""

        email_val = email_input.value.strip().lower()
        senha_val = senha_input.value.strip()
        conf_senha_val = confirmar_senha_input.value.strip()

        if not email_val:
            msg_erro.value = "⚠️ Informe um e-mail válido."
            page.update()
            return

        if len(senha_val) < 6 or senha_val != conf_senha_val:
            msg_erro.value = "⚠️ Verifique as senhas informadas (mínimo 6 caracteres)."
            page.update()
            return

        try:
            def api_call():
                return supabase.auth.sign_up({
                    "email": email_val,
                    "password": senha_val
                })

            await asyncio.to_thread(api_call)
            mudar_modo_auth("login")
            msg_sucesso.value = "✔ Conta criada com sucesso! Digite sua senha para entrar."
            page.update()
        except Exception as ex:
            msg_erro.value = f"❌ Erro: {str(ex)}"
            page.update()

    async def recuperar_senha(e):
        msg_erro.value = ""
        msg_sucesso.value = ""
        email_val = email_input.value.strip().lower()

        if not email_val:
            msg_erro.value = "⚠️ Informe um e-mail válido."
            page.update()
            return

        try:
            def api_call():
                return supabase.auth.reset_password_for_email(email_val)

            await asyncio.to_thread(api_call)
            mudar_modo_auth("login")
            msg_sucesso.value = "✉️ E-mail de recuperação enviado!"
            page.update()
        except Exception as ex:
            msg_erro.value = f"❌ Erro: {str(ex)}"
            page.update()

    async def logout(e):
        try:
            await asyncio.to_thread(supabase.auth.sign_out)
        except Exception:
            pass
        usuario_atual["session"] = None
        usuario_atual["user"] = None
        mudar_modo_auth("login")

    def carregar_tela_login():
        page.clean()

        if modo_auth == "login":
            conteudo = [
                titulo_auth,
                ft.Text("Acesse sua conta para continuar", size=14, color=ft.Colors.GREY_400),
                ft.Divider(color="#00FF66", height=15),
                msg_erro, msg_sucesso,
                email_input, senha_input,
                ft.TextButton("Esqueceu sua senha?", on_click=lambda _: mudar_modo_auth("recuperar")),
                ft.ElevatedButton("Entrar", width=150, bgcolor="#00AA44", color=ft.Colors.WHITE, on_click=lambda ev: asyncio.create_task(realizar_login(ev))),
                ft.TextButton("Não tem uma conta? Cadastre-se aqui", on_click=lambda _: mudar_modo_auth("cadastro")),
                watermark
            ]
        elif modo_auth == "cadastro":
            conteudo = [
                titulo_auth,
                dicas_cadastro,
                msg_erro, msg_sucesso,
                email_input, senha_input, confirmar_senha_input,
                ft.ElevatedButton("Cadastrar", width=150, bgcolor="#00AA44", color=ft.Colors.WHITE, on_click=lambda ev: asyncio.create_task(realizar_cadastro(ev))),
                ft.TextButton("Voltar para a tela de login", on_click=lambda _: mudar_modo_auth("login")),
                watermark
            ]
        else:
            conteudo = [
                titulo_auth,
                msg_erro, msg_sucesso,
                email_input,
                ft.ElevatedButton("Enviar E-mail", width=160, bgcolor="#00AA44", color=ft.Colors.WHITE, on_click=lambda ev: asyncio.create_task(recuperar_senha(ev))),
                ft.TextButton("Voltar para o login", on_click=lambda _: mudar_modo_auth("login")),
                watermark
            ]

        page.add(
            ft.Stack([
                criar_fundo_matrix_animado(page),
                ft.Container(content=ft.Column(conteudo, alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10), alignment=ft.Alignment(0, 0), padding=20)
            ], expand=True)
        )
        page.update()

    async def carregar_tela_principal():
        try:
            page.clean()

            user_obj = usuario_atual.get("user")
            user_email = user_obj.email if user_obj else "Usuário"
            user_id = user_obj.id if user_obj else None

            txt_renda_base = ft.TextField(label="Renda Base (R$)", value="0,00", width=150)
            txt_descricao = ft.TextField(label="Descrição", expand=True)
            txt_valor = ft.TextField(label="Valor Total (R$)", width=130)

            dd_categoria = ft.Dropdown(
                label="Categoria",
                value="Outros",
                width=180,
                options=[ft.dropdown.Option(cat) for cat in CATEGORIAS]
            )

            dd_parcelas = ft.Dropdown(
                label="Parcelas",
                value="1",
                width=110,
                options=[ft.dropdown.Option(str(i), f"{i}x") for i in range(1, 25)]
            )

            dd_dia_vencimento = ft.Dropdown(
                label="Vencimento",
                value="10",
                width=120,
                options=[ft.dropdown.Option(str(i), f"Dia {i:02d}") for i in range(1, 32)]
            )

            dd_forma_pagamento = ft.Dropdown(
                label="Pagamento / Origem",
                value="Débito / Pix",
                width=180,
                options=[
                    ft.dropdown.Option("Dinheiro"),
                    ft.dropdown.Option("Débito / Pix"),
                    ft.dropdown.Option("Cartão de Crédito"),
                ]
            )

            txt_busca = ft.TextField(
                label="Buscar", 
                prefix_icon=ft.Icons.SEARCH, 
                expand=True
            )

            dd_filtro = ft.Dropdown(
                label="Filtrar Categoria",
                value="Todas",
                width=180,
                options=[ft.dropdown.Option("Todas")] + [ft.dropdown.Option(cat) for cat in CATEGORIAS]
            )

            mes_atual_str = str(datetime.now().month).zfill(2)
            ano_atual_str = str(datetime.now().year)

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

            dd_ano_relatorio = ft.Dropdown(
                label="Ano",
                value=ano_atual_str,
                width=110,
                options=[
                    ft.dropdown.Option("2024"),
                    ft.dropdown.Option("2025"),
                    ft.dropdown.Option("2026"),
                    ft.dropdown.Option("2027"),
                ]
            )

            lbl_receitas = ft.Text("Receitas: R$ 0.00", color=ft.Colors.GREEN_400, weight=ft.FontWeight.BOLD)
            lbl_gastos = ft.Text("Despesas: R$ 0.00", color=ft.Colors.RED_400, weight=ft.FontWeight.BOLD)
            lbl_saldo = ft.Text("Saldo do Mês: R$ 0.00", color=ft.Colors.GREEN_400, size=18, weight=ft.FontWeight.BOLD)

            lista_gastos_ui = ft.Column()
            grafico_ui = ft.Column()
            registros_cache = []

            def obter_mes_ano_efetivo(item):
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

            async def carregar_registros(e=None):
                nonlocal registros_cache
                try:
                    def sync_get():
                        return supabase.table("gastos").select("*").eq("user_id", user_id).execute()

                    res = await asyncio.to_thread(sync_get)
                    registros_cache = res.data or []
                    renderizar_registros()
                except Exception as ex:
                    mostrar_notificacao_global(f"❌ Erro de conexão: {str(ex)}", ft.Colors.RED_600)

            def renderizar_registros(e=None):
                lista_gastos_ui.controls.clear()
                mes_sel = dd_mes_relatorio.value
                ano_sel = dd_ano_relatorio.value
                busca_query = txt_busca.value.strip().lower() if txt_busca.value else ""
                filtro_cat = dd_filtro.value

                filtrados = []
                for item in registros_cache:
                    m_ef, a_ef, _ = obter_mes_ano_efetivo(item)
                    if m_ef != mes_sel or a_ef != ano_sel:
                        continue
                    desc = str(item.get("descricao", "")).lower()
                    if busca_query and busca_query not in desc:
                        continue
                    cat = item.get("categoria", "Outros")
                    if filtro_cat != "Todas" and cat != filtro_cat:
                        continue
                    filtrados.append(item)

                calcular_totais(filtrados)
                atualizar_grafico(filtrados)

                if not filtrados:
                    lista_gastos_ui.controls.append(
                        ft.Text("Nenhum lançamento encontrado para os filtros selecionados.", color=ft.Colors.GREY_500)
                    )
                else:
                    for item in filtrados:
                        reg_id = item.get("id")
                        desc = item.get("descricao", "")
                        cat = item.get("categoria", "Outros")
                        forma = item.get("forma_pagamento", "Débito / Pix")
                        tipo = item.get("tipo", "Despesa")
                        val = float(item.get("valor", 0))
                        venc = item.get("data_vencimento")

                        detalhes_str = f"{cat} • {forma}"
                        if venc:
                            detalhes_str += f" • Vencimento: Dia {venc}"

                        is_receita = tipo == "Receita"
                        cor_val = ft.Colors.GREEN_400 if is_receita else ft.Colors.RED_400
                        sinal = "+" if is_receita else "-"

                        card = ft.Container(
                            content=ft.Row([
                                ft.Column([
                                    ft.Text(desc, weight=ft.FontWeight.BOLD, size=14),
                                    ft.Text(detalhes_str, size=12, color=ft.Colors.GREY_400),
                                ], expand=True),
                                ft.Text(f"{sinal}R$ {val:.2f}", color=cor_val, weight=ft.FontWeight.BOLD, size=14),
                                ft.IconButton(
                                    icon=ft.Icons.DELETE_OUTLINE,
                                    icon_color=ft.Colors.RED_400,
                                    tooltip="Excluir",
                                    on_click=lambda _, r_id=reg_id: asyncio.create_task(deletar_registro(r_id))
                                )
                            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                            padding=10,
                            bgcolor=ft.Colors.GREY_900,
                            border_radius=8,
                            margin=ft.Margin(0, 2, 0, 2)
                        )
                        lista_gastos_ui.controls.append(card)

                page.update()

            # VINCULAÇÃO DOS EVENTOS DE ATUALIZAÇÃO APÓS A FUNÇÃO RENDERIZAR ESTAR DEFINIDA
            txt_busca.on_change = lambda e: renderizar_registros()
            dd_filtro.on_change = lambda e: renderizar_registros()
            dd_mes_relatorio.on_change = lambda e: renderizar_registros()
            dd_ano_relatorio.on_change = lambda e: renderizar_registros()

            def exportar_para_excel(e):
                if not registros_cache:
                    mostrar_notificacao_global("⚠️ Nenhum registro para exportar!", ft.Colors.AMBER_600)
                    return

                mes_sel = str(dd_mes_relatorio.value).zfill(2)
                ano_sel = str(dd_ano_relatorio.value)
                
                dados_filtrados = [(item, dt) for item in registros_cache if (m_ef := obter_mes_ano_efetivo(item))[0] == mes_sel and m_ef[1] == ano_sel for dt in [m_ef[2]]]

                if not dados_filtrados:
                    mostrar_notificacao_global(f"⚠️ Nenhum lançamento para o mês {mes_sel}/{ano_sel}!", ft.Colors.AMBER_600)
                    return

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

                    mostrar_notificacao_global(f"✔ Relatório salvo em: {caminho_completo}")
                except Exception as err:
                    mostrar_notificacao_global(f"❌ Erro ao exportar: {str(err)}", ft.Colors.RED_600)

            async def carregar_renda_usuario():
                try:
                    def get_renda():
                        return supabase.table("configuracoes").select("renda_base").eq("user_id", user_id).execute()

                    res = await asyncio.to_thread(get_renda)
                    if res.data:
                        valor_renda = res.data[0].get("renda_base", 0.0)
                        txt_renda_base.value = f"{float(valor_renda):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                        page.update()
                except Exception:
                    pass

            async def salvar_renda_base(e=None):
                try:
                    val_clean = txt_renda_base.value.strip().replace(".", "").replace(",", ".")
                    renda_num = float(val_clean)
                    
                    def upsert_renda():
                        return supabase.table("configuracoes").upsert({"user_id": user_id, "renda_base": renda_num}).execute()

                    await asyncio.to_thread(upsert_renda)
                    mostrar_notificacao_global("✔ Renda base atualizada!")
                    await carregar_registros()
                except Exception as ex:
                    mostrar_notificacao_global(f"❌ Erro: {str(ex)}", ft.Colors.RED_600)

            def calcular_totais(registros_filtrados):
                tot_receita = sum(float(r["valor"]) for r in registros_filtrados if r.get("tipo") == "Receita")
                tot_despesa = sum(float(r["valor"]) for r in registros_filtrados if r.get("tipo") in ("Despesa", "Gasto"))

                try:
                    renda_base = float(txt_renda_base.value.strip().replace(".", "").replace(",", "."))
                except ValueError:
                    renda_base = 0.0

                saldo = renda_base + tot_receita - tot_despesa
                lbl_receitas.value = f"Receitas: R$ {tot_receita:.2f}"
                lbl_gastos.value = f"Despesas: R$ {tot_despesa:.2f}"
                lbl_saldo.value = f"Saldo do Mês: R$ {saldo:.2f}"
                lbl_saldo.color = ft.Colors.GREEN_400 if saldo >= 0 else ft.Colors.RED_400

            def atualizar_grafico(registros_filtrados):
                grafico_ui.controls.clear()
                despesas = [r for r in registros_filtrados if r.get("tipo", "Despesa") in ("Despesa", "Gasto")]
                tot_despesa = sum(float(r["valor"]) for r in despesas)
                if tot_despesa == 0: return

                categorias = {}
                for d in despesas:
                    cat = d.get("categoria", "Outros")
                    categorias[cat] = categorias.get(cat, 0.0) + float(d.get("valor", 0))

                cores = [
                    "#00FF66", "#FFB703", "#9D4EDD", "#00B4D8", "#F72585", 
                    "#4CC9F0", "#FF4D6D", "#70E000", "#FF8FA3", "#3A86FF"
                ]
                grafico_ui.controls.append(ft.Text("📊 Distribuição de Receitas/Despesas Por Categoria", weight=ft.FontWeight.BOLD, size=16))

                for idx, (cat, val) in enumerate(categorias.items()):
                    porcentagem = (val / tot_despesa) * 100
                    cor = cores[idx % len(cores)]
                    grafico_ui.controls.append(
                        ft.Column([
                            ft.Row([ft.Text(f"{cat}", weight=ft.FontWeight.BOLD), ft.Text(f"R$ {val:.2f} ({porcentagem:.1f}%)", color=cor, weight=ft.FontWeight.BOLD)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                            ft.ProgressBar(value=porcentagem / 100, color=cor, bgcolor=ft.Colors.GREY_800, height=8)
                        ])
                    )

            def abrir_relatorio_mensal(e):
                mes_sel, ano_sel = dd_mes_relatorio.value, dd_ano_relatorio.value
                itens_mes = [(item, dt) for item in registros_cache if (m_ef := obter_mes_ano_efetivo(item))[0] == mes_sel and m_ef[1] == ano_sel for dt in [m_ef[2]]]
                
                tot_receitas = sum(float(x[0]["valor"]) for x in itens_mes if x[0].get("tipo") == "Receita")
                tot_despesas = sum(float(x[0]["valor"]) for x in itens_mes if x[0].get("tipo") in ("Despesa", "Gasto"))
                try:
                    renda_base = float(txt_renda_base.value.strip().replace(".", "").replace(",", "."))
                except ValueError:
                    renda_base = 0.0

                saldo_final = renda_base + tot_receitas - tot_despesas
                status_text = f"🟢 SUPERÁVIT DE R$ {saldo_final:.2f}" if saldo_final >= 0 else f"🔴 DÉFICIT DE R$ {abs(saldo_final):.2f}"
                status_color = ft.Colors.GREEN_400 if saldo_final >= 0 else ft.Colors.RED_400

                lista_itens_dialog = ft.Column(spacing=5, scroll=ft.ScrollMode.AUTO, height=200)
                if not itens_mes:
                    lista_itens_dialog.controls.append(ft.Text("Nenhum registro encontrado.", color=ft.Colors.GREY_400))
                else:
                    for item, dt in itens_mes:
                        tipo = item.get("tipo", "Despesa")
                        sinal = "+" if tipo == "Receita" else "-"
                        cor_v = ft.Colors.GREEN_400 if tipo == "Receita" else ft.Colors.RED_400
                        lista_itens_dialog.controls.append(
                            ft.Container(
                                content=ft.Row([
                                    ft.Text(f"{dt.strftime('%d/%m')} - {item.get('descricao', '')} ({item.get('forma_pagamento', 'Débito / Pix')})", size=13),
                                    ft.Text(f"{sinal}R$ {float(item.get('valor', 0)):.2f}", color=cor_v, weight=ft.FontWeight.BOLD, size=13)
                                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                                padding=5, bgcolor=ft.Colors.GREY_900, border_radius=4
                            )
                        )

                dialog = ft.AlertDialog(
                    title=ft.Text(f"📋 Relatório Mensal: {mes_sel}/{ano_sel}", weight=ft.FontWeight.BOLD),
                    content=ft.Container(
                        width=400,
                        content=ft.Column([
                            ft.Container(
                                content=ft.Column([
                                    ft.Text("RESULTADO FINAL", size=12, color=ft.Colors.GREY_400, weight=ft.FontWeight.BOLD),
                                    ft.Text(status_text, color=status_color, size=18, weight=ft.FontWeight.BOLD),
                                ]),
                                padding=10, bgcolor=ft.Colors.GREY_900, border_radius=8,
                            ),
                            ft.Divider(),
                            ft.Row([
                                ft.Text(f"Renda: R$ {renda_base:.2f}", size=12, color=ft.Colors.GREY_300),
                                ft.Text(f"Receitas: R$ {tot_receitas:.2f}", size=12, color=ft.Colors.GREEN_400),
                                ft.Text(f"Despesas: R$ {tot_despesas:.2f}", size=12, color=ft.Colors.RED_400),
                            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                            ft.Divider(),
                            ft.Text("Lançamentos do Mês:", weight=ft.FontWeight.BOLD),
                            lista_itens_dialog,
                        ], tight=True, spacing=10)
                    ),
                    actions=[ft.TextButton("Fechar", on_click=lambda _: setattr(dialog, 'open', False) or page.update())],
                    actions_alignment=ft.MainAxisAlignment.END
                )
                page.overlay.append(dialog)
                dialog.open = True
                page.update()

            async def deletar_registro(reg_id):
                try:
                    def sync_del():
                        return supabase.table("gastos").delete().eq("id", reg_id).execute()

                    await asyncio.to_thread(sync_del)
                    mostrar_notificacao_global("✔ Registro excluído!")
                    await carregar_registros()
                except Exception as ex:
                    mostrar_notificacao_global(f"❌ Erro ao excluir: {str(ex)}", ft.Colors.RED_600)

            async def adicionar_registro(tipo_registro):
                desc = txt_descricao.value.strip()
                val_raw = txt_valor.value.strip().replace(".", "").replace(",", ".")

                if not desc or not val_raw:
                    mostrar_notificacao_global("⚠️ Preencha descrição e valor!", ft.Colors.AMBER_600)
                    return

                try:
                    val_num = float(val_raw)
                    if val_num <= 0: raise ValueError()
                except ValueError:
                    mostrar_notificacao_global("⚠️ Valor inválido!", ft.Colors.AMBER_600)
                    return

                num_parcelas = int(dd_parcelas.value)
                valor_parcela = val_num / num_parcelas

                try:
                    for i in range(num_parcelas):
                        desc_final = f"{desc} ({i+1}/{num_parcelas})" if num_parcelas > 1 else desc
                        dt_lancamento = datetime.now() + timedelta(days=30 * i)

                        payload = {
                            "user_id": user_id,
                            "descricao": desc_final,
                            "valor": valor_parcela,
                            "categoria": dd_categoria.value,
                            "forma_pagamento": dd_forma_pagamento.value,
                            "tipo": tipo_registro,
                            "data_vencimento": dd_dia_vencimento.value,
                            "created_at": dt_lancamento.isoformat()
                        }

                        def insert_sync():
                            return supabase.table("gastos").insert(payload).execute()

                        await asyncio.to_thread(insert_sync)

                    txt_descricao.value = ""
                    txt_valor.value = ""
                    dd_parcelas.value = "1"
                    mostrar_notificacao_global("✔ Lançamento adicionado com sucesso!")
                    await carregar_registros()
                except Exception as ex:
                    mostrar_notificacao_global(f"❌ Erro ao salvar: {str(ex)}", ft.Colors.RED_600)

            header = ft.Row([
                ft.Column([
                    ft.Text("Perrut - Painel Financeiro", size=20, weight=ft.FontWeight.BOLD, color="#00FF66"),
                    ft.Text(f"Usuário: {user_email}", size=12, color=ft.Colors.GREY_400),
                ]),
                ft.Row([
                    ft.IconButton(
                        icon=ft.Icons.REFRESH,
                        tooltip="Forçar busca de dados no banco",
                        icon_color="#00FF66",
                        on_click=lambda _: (
                            mostrar_notificacao_global("🔄 Sincronizando com o servidor...", ft.Colors.BLUE_700),
                            asyncio.create_task(carregar_registros())
                        )
                    ),
                    ft.IconButton(icon=ft.Icons.LOGOUT, tooltip="Sair", on_click=logout, icon_color=ft.Colors.RED_400)
                ])
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

            card_renda = ft.Container(
                content=ft.Row([
                    txt_renda_base,
                    ft.ElevatedButton("Salvar Renda", on_click=lambda ev: asyncio.create_task(salvar_renda_base(ev)), bgcolor="#00AA44", color=ft.Colors.WHITE)
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                padding=12, bgcolor=ft.Colors.GREY_900, border_radius=8
            )

            card_resumo = ft.Container(
                content=ft.Column([
                    lbl_saldo,
                    ft.Row([lbl_receitas, lbl_gastos], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
                ]),
                padding=12, bgcolor=ft.Colors.GREY_900, border_radius=8
            )

            form_lancamento = ft.Container(
                content=ft.Column([
                    ft.Text("➕ Novo Lançamento", weight=ft.FontWeight.BOLD, size=16),
                    txt_descricao,
                    ft.Row([txt_valor, dd_categoria, dd_forma_pagamento], wrap=True),
                    ft.Row([dd_parcelas, dd_dia_vencimento], wrap=True),
                    ft.Row([
                        ft.ElevatedButton("Adicionar Receita", icon=ft.Icons.ADD_CIRCLE_OUTLINE, bgcolor=ft.Colors.GREEN_700, color=ft.Colors.WHITE, on_click=lambda _: asyncio.create_task(adicionar_registro("Receita"))),
                        ft.ElevatedButton("Adicionar Despesa", icon=ft.Icons.REMOVE_CIRCLE_OUTLINE, bgcolor=ft.Colors.RED_700, color=ft.Colors.WHITE, on_click=lambda _: asyncio.create_task(adicionar_registro("Despesa"))),
                    ], alignment=ft.MainAxisAlignment.END, spacing=10)
                ]),
                padding=15, bgcolor=ft.Colors.GREY_900, border_radius=8
            )

            barra_filtros = ft.Row([
                dd_mes_relatorio,
                dd_ano_relatorio,
                ft.ElevatedButton("Relatório", icon=ft.Icons.ASSESSMENT, on_click=abrir_relatorio_mensal),
                ft.ElevatedButton("Exportar CSV", icon=ft.Icons.DOWNLOAD, on_click=exportar_para_excel)
            ], wrap=True)

            busca_e_categoria = ft.Row([txt_busca, dd_filtro])

            page.add(
                header,
                card_renda,
                card_resumo,
                form_lancamento,
                ft.Divider(height=20),
                barra_filtros,
                busca_e_categoria,
                grafico_ui,
                ft.Divider(height=10),
                ft.Text("📋 Registros do Mês", weight=ft.FontWeight.BOLD, size=16),
                lista_gastos_ui
            )

            await carregar_renda_usuario()
            await carregar_registros()

        except Exception as err:
            mostrar_notificacao_global(f"❌ Erro ao carregar painel: {str(err)}", ft.Colors.RED_600)

    carregar_tela_login()

if __name__ == "__main__":
    ft.app(target=main)