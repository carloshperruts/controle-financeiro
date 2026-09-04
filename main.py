import flet as ft
from supabase import create_client, Client
import os
from datetime import datetime
import random
import asyncio

# --- CONFIGURAÇÃO SUPABASE ---
SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://vmkkdenzkoqklvlulajo.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "sb_publishable_ax9nD4u05T1fdUnz-okKlw_a_iB20Hj")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- COMPONENTE DE FUNDO MATRIX ---
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

    watermark = ft.Container(
        content=ft.Text(
            "PERRUT",
            size=120,
            weight=ft.FontWeight.BOLD,
            color="#00FF66",
            opacity=0.06,
        ),
        alignment=ft.Alignment(0, 0),
        expand=True
    )

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

    return ft.Stack([watermark, rain_row], expand=True)

# --- APLICAÇÃO PRINCIPAL ---
async def main(page: ft.Page):
    page.title = "Perrut - Controle Financeiro"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 15
    page.scroll = ft.ScrollMode.AUTO

    usuario_atual = {"session": None}
    msg_erro = ft.Text("", color=ft.Colors.RED_400)

    email_input = ft.TextField(label="E-mail", width=300)
    senha_input = ft.TextField(label="Senha", password=True, can_reveal_password=True, width=300)

    def mostrar_notificacao(texto, cor=ft.Colors.GREEN_600):
        snack = ft.SnackBar(
            content=ft.Text(texto, color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD),
            bgcolor=cor,
            duration=4000
        )
        page.overlay.append(snack)
        snack.open = True
        page.update()

    def realizar_login(e):
        msg_erro.value = ""
        try:
            res = supabase.auth.sign_in_with_password({
                "email": email_input.value.strip(),
                "password": senha_input.value
            })
            usuario_atual["session"] = res.session
            carregar_tela_principal()
        except Exception as ex:
            msg_erro.value = f"❌ Erro ao entrar: {str(ex)}"
            page.update()

    def realizar_cadastro(e):
        msg_erro.value = ""
        try:
            res = supabase.auth.sign_up({
                "email": email_input.value.strip(),
                "password": senha_input.value
            })
            mostrar_notificacao("✔ Conta criada! Verifique seu e-mail.")
        except Exception as ex:
            msg_erro.value = f"❌ Erro ao criar conta: {str(ex)}"
            page.update()

    def logout(e):
        try:
            supabase.auth.sign_out()
        except Exception:
            pass
        usuario_atual["session"] = None
        carregar_tela_login()

    def carregar_tela_login():
        page.clean()
        
        conteudo_login = ft.Column(
            [
                ft.Text("Perrut - Controle Financeiro", size=26, weight=ft.FontWeight.BOLD, color="#00FF66"),
                ft.Divider(color="#00FF66", height=20),
                msg_erro,
                email_input,
                senha_input,
                ft.Row(
                    [
                        ft.ElevatedButton("Entrar", on_click=realizar_login, bgcolor="#00AA44", color=ft.Colors.WHITE),
                        ft.OutlinedButton("Criar Conta", on_click=realizar_cadastro),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER
                )
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

        page.add(
            ft.Stack(
                [
                    criar_fundo_matrix_animado(page),
                    ft.Container(content=conteudo_login, alignment=ft.Alignment(0, 0), padding=20)
                ],
                expand=True
            )
        )
        page.update()

    def carregar_tela_principal():
        try:
            page.clean()

            user_session = usuario_atual.get("session")
            user_email = user_session.user.email if user_session and user_session.user else "Usuário"
            user_id = user_session.user.id if user_session and user_session.user else None

            txt_renda_base = ft.TextField(label="Renda Base (R$)", value="1.600,00", width=150)
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

            dd_mes_relatorio = ft.Dropdown(
                label="Mês do Relatório",
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
                ]
            )

            lbl_receitas = ft.Text("Receitas: R$ 0.00", color=ft.Colors.GREEN_400, weight=ft.FontWeight.BOLD)
            lbl_gastos = ft.Text("Gastos: R$ 0.00", color=ft.Colors.RED_400, weight=ft.FontWeight.BOLD)
            lbl_saldo = ft.Text("Saldo: R$ 0.00", color=ft.Colors.GREEN_400, size=18, weight=ft.FontWeight.BOLD)

            lista_gastos_ui = ft.Column()
            grafico_ui = ft.Column()

            registros_cache = []

            def calcular_totais(registros):
                tot_receita = sum(float(r["valor"]) for r in registros if r.get("tipo") == "Receita")
                tot_gasto = sum(float(r["valor"]) for r in registros if r.get("tipo") == "Gasto")
                
                try:
                    renda_base = float(txt_renda_base.value.replace(".", "").replace(",", "."))
                except ValueError:
                    renda_base = 0.0

                saldo = renda_base + tot_receita - tot_gasto

                lbl_receitas.value = f"Receitas: R$ {tot_receita:.2f}"
                lbl_gastos.value = f"Gastos: R$ {tot_gasto:.2f}"
                lbl_saldo.value = f"Saldo: R$ {saldo:.2f}"
                lbl_saldo.color = ft.Colors.GREEN_400 if saldo >= 0 else ft.Colors.RED_400

            def atualizar_grafico(registros):
                grafico_ui.controls.clear()
                gastos = [r for r in registros if r.get("tipo", "Gasto") == "Gasto"]
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
                    renda_base = float(txt_renda_base.value.replace(".", "").replace(",", "."))
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

            def carregar_registros(e=None):
                nonlocal registros_cache
                lista_gastos_ui.controls.clear()
                msg_erro.value = ""
                try:
                    # FILTRA REGISTROS APENAS DO USUÁRIO CONECTADO
                    query = supabase.table("gastos").select("*")
                    if user_id:
                        query = query.eq("user_id", user_id)
                    
                    res = query.order("id", desc=True).execute()
                    registros = res.data or []
                    registros_cache = registros

                    termo_busca = txt_busca.value.lower() if txt_busca.value else ""
                    cat_filtro = dd_filtro.value

                    for item in registros:
                        desc = str(item.get("descricao", ""))
                        cat = str(item.get("categoria", ""))

                        if termo_busca and termo_busca not in desc.lower():
                            continue
                        if cat_filtro != "Todas" and cat != cat_filtro:
                            continue

                        item_id = item["id"]
                        tipo = item.get("tipo", "Gasto")
                        valor = float(item.get("valor", 0))
                        cor_valor = ft.Colors.GREEN_400 if tipo == "Receita" else ft.Colors.RED_400
                        sinal = "+" if tipo == "Receita" else "-"

                        raw_data = item.get("created_at") or item.get("data")
                        if raw_data:
                            try:
                                dt = datetime.fromisoformat(str(raw_data).replace("Z", "+00:00"))
                                str_data_hora = dt.strftime("%d/%m/%Y %H:%M")
                            except Exception:
                                str_data_hora = str(raw_data)
                        else:
                            str_data_hora = datetime.now().strftime("%d/%m/%Y %H:%M")

                        btn_deletar = ft.IconButton(
                            icon=ft.Icons.DELETE_OUTLINE,
                            icon_color=ft.Colors.RED_400,
                            tooltip="Excluir",
                            on_click=lambda e, i=item_id: deletar_registro(i)
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

                    calcular_totais(registros)
                    atualizar_grafico(registros)
                except Exception as ex:
                    msg_erro.value = f"Erro ao carregar dados: {str(ex)}"
                
                page.update()

            def salvar_transacao(tipo):
                msg_erro.value = ""
                
                if not txt_descricao.value or not txt_valor.value:
                    mostrar_notificacao("Preencha a descrição e o valor!", ft.Colors.RED_600)
                    return

                try:
                    valor_num = float(txt_valor.value.replace(".", "").replace(",", "."))
                    
                    payload = {
                        "descricao": txt_descricao.value.strip(),
                        "valor": valor_num,
                        "categoria": dd_categoria.value,
                        "tipo": tipo,
                        "user_id": user_id  # GRAVA O ID DO USUÁRIO LOGADO
                    }

                    supabase.table("gastos").insert(payload).execute()
                    
                    txt_descricao.value = ""
                    txt_valor.value = ""
                    mostrar_notificacao("✔ Lançamento salvo com sucesso no banco!")
                    carregar_registros()
                except Exception as ex:
                    mostrar_notificacao(f"Erro ao salvar: {str(ex)}", ft.Colors.RED_600)

            def deletar_registro(item_id):
                try:
                    supabase.table("gastos").delete().eq("id", item_id).execute()
                    mostrar_notificacao("🗑️ Registro excluído!")
                    carregar_registros()
                except Exception as ex:
                    mostrar_notificacao(f"Erro ao excluir: {str(ex)}", ft.Colors.RED_600)

            txt_busca.on_change = carregar_registros
            dd_filtro.on_change = carregar_registros

            btn_receita = ft.ElevatedButton(
                content=ft.Text("+ Receita", color=ft.Colors.WHITE),
                bgcolor=ft.Colors.GREEN_700,
                on_click=lambda e: salvar_transacao("Receita"),
                expand=True
            )

            btn_gasto = ft.ElevatedButton(
                content=ft.Text("- Despesa", color=ft.Colors.WHITE),
                bgcolor=ft.Colors.RED_700,
                on_click=lambda e: salvar_transacao("Gasto"),
                expand=True
            )

            btn_gerar_relatorio = ft.ElevatedButton(
                "📊 Ver Relatório Mensal",
                on_click=abrir_relatorio_mensal,
                bgcolor=ft.Colors.BLUE_800,
                color=ft.Colors.WHITE,
                icon=ft.Icons.ASSESSMENT
            )

            header_app = ft.Row(
                [
                    ft.Text("Perrut - Controle Financeiro", size=24, weight=ft.FontWeight.BOLD, color="#00FF66"),
                    ft.Row(
                        [
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
                    ft.Row([txt_renda_base, ft.ElevatedButton("Atualizar", on_click=carregar_registros)]),
                    
                    ft.Container(
                        content=ft.Row([
                            dd_mes_relatorio,
                            dd_ano_relatorio,
                            btn_gerar_relatorio
                        ], alignment=ft.MainAxisAlignment.START),
                        padding=10,
                        bgcolor=ft.Colors.GREY_900,
                        border_radius=8
                    ),

                    ft.Row([lbl_receitas, lbl_gastos], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Row([lbl_saldo], alignment=ft.MainAxisAlignment.CENTER),
                    grafico_ui,
                    msg_erro,
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

            carregar_registros()
        except Exception as main_err:
            page.add(ft.Text(f"⚠️ Erro ao carregar tela principal: {str(main_err)}", color=ft.Colors.RED_400))
            page.update()

    carregar_tela_login()

ft.app(target=main)