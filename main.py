import flet as ft
from supabase import create_client, Client
import os
from datetime import datetime

SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://vmkkdenzkoqklvlulajo.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "sb_publishable_ax9nD4u05T1fdUnz-okKlw_a_iB20Hj")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def main(page: ft.Page):
    page.title = "Controle Financeiro"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 20
    page.scroll = ft.ScrollMode.AUTO

    usuario_atual = {"session": None}

    msg_erro = ft.Text("", color=ft.Colors.RED_400)
    msg_sucesso = ft.Text("", color=ft.Colors.GREEN_400)

    email_input = ft.TextField(label="E-mail", width=300)
    senha_input = ft.TextField(label="Senha", password=True, can_reveal_password=True, width=300)

    def realizar_login(e):
        msg_erro.value = ""
        msg_sucesso.value = ""
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
        msg_sucesso.value = ""
        try:
            res = supabase.auth.sign_up({
                "email": email_input.value.strip(),
                "password": senha_input.value
            })
            msg_sucesso.value = "✔ Conta criada! Verifique seu e-mail."
            page.update()
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
        page.add(
            ft.Column(
                [
                    ft.Text("🔐 Acesso ao Sistema", size=24, weight=ft.FontWeight.BOLD),
                    msg_erro,
                    msg_sucesso,
                    email_input,
                    senha_input,
                    ft.Row(
                        [
                            ft.ElevatedButton("Entrar", on_click=realizar_login, bgcolor=ft.Colors.BLUE_700, color=ft.Colors.WHITE),
                            ft.OutlinedButton("Criar Conta", on_click=realizar_cadastro),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER
                    )
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            )
        )
        page.update()

    def carregar_tela_principal():
        try:
            page.clean()
            user_email = usuario_atual["session"].user.email if usuario_atual["session"] else ""

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

            lbl_receitas = ft.Text("Receitas: R$ 0.00", color=ft.Colors.GREEN_400, weight=ft.FontWeight.BOLD)
            lbl_gastos = ft.Text("Gastos: R$ 0.00", color=ft.Colors.RED_400, weight=ft.FontWeight.BOLD)
            lbl_saldo = ft.Text("Saldo: R$ 0.00", color=ft.Colors.GREEN_400, size=18, weight=ft.FontWeight.BOLD)

            lista_gastos_ui = ft.Column()
            pie_chart_ui = ft.Column(horizontal_alignment=ft.CrossAxisAlignment.CENTER)

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
                pie_chart_ui.controls.clear()
                
                # Agrupa apenas gastos por categoria
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
                    ft.Colors.BLUE_400,
                    ft.Colors.AMBER_400,
                    ft.Colors.PURPLE_400,
                    ft.Colors.TEAL_400,
                    ft.Colors.ORANGE_400,
                    ft.Colors.PINK_400
                ]

                sections = []
                legenda_controls = []

                for idx, (cat, val) in enumerate(categorias.items()):
                    porcentagem = (val / tot_gasto) * 100
                    cor = cores[idx % len(cores)]

                    sections.append(
                        ft.PieChartSection(
                            val,
                            title=f"{porcentagem:.1f}%",
                            color=cor,
                            radius=40,
                            title_style=ft.TextStyle(size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)
                        )
                    )

                    legenda_controls.append(
                        ft.Row(
                            [
                                ft.Container(width=12, height=12, bgcolor=cor, border_radius=3),
                                ft.Text(f"{cat}: R$ {val:.2f} ({porcentagem:.1f}%)", size=12)
                            ],
                            alignment=ft.MainAxisAlignment.CENTER
                        )
                    )

                chart = ft.PieChart(
                    sections=sections,
                    sections_space=2,
                    center_space_radius=30,
                    height=180
                )

                pie_chart_ui.controls.append(ft.Text("📊 Distribuição de Gastos", weight=ft.FontWeight.BOLD, size=16))
                pie_chart_ui.controls.append(chart)
                pie_chart_ui.controls.append(ft.Column(legenda_controls))

            def carregar_registros(e=None):
                lista_gastos_ui.controls.clear()
                msg_erro.value = ""
                try:
                    res = supabase.table("gastos").select("*").order("id", desc=True).execute()
                    registros = res.data or []

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
                msg_sucesso.value = ""
                
                if not txt_descricao.value or not txt_valor.value:
                    msg_erro.value = "Preencha a descrição e o valor!"
                    page.update()
                    return

                try:
                    valor_num = float(txt_valor.value.replace(".", "").replace(",", "."))
                    
                    payload = {
                        "descricao": txt_descricao.value.strip(),
                        "valor": valor_num,
                        "categoria": dd_categoria.value,
                        "tipo": tipo,
                        "created_at": datetime.now().isoformat()
                    }

                    supabase.table("gastos").insert(payload).execute()
                    
                    txt_descricao.value = ""
                    txt_valor.value = ""
                    msg_sucesso.value = f"✔ {tipo} adicionado(a)!"
                    carregar_registros()
                except Exception as ex:
                    msg_erro.value = f"Erro ao salvar: {str(ex)}"
                    page.update()

            def deletar_registro(item_id):
                try:
                    supabase.table("gastos").delete().eq("id", item_id).execute()
                    carregar_registros()
                except Exception as ex:
                    msg_erro.value = f"Erro ao excluir: {str(ex)}"
                    page.update()

            txt_busca.on_change = carregar_registros
            dd_filtro.on_change = carregar_registros

            btn_receita = ft.ElevatedButton(
                content=ft.Text("+ Receita", color=ft.Colors.WHITE),
                bgcolor=ft.Colors.GREEN_700,
                on_click=lambda e: salvar_transacao("Receita"),
                expand=True
            )

            btn_gasto = ft.ElevatedButton(
                content=ft.Text("- Gasto", color=ft.Colors.WHITE),
                bgcolor=ft.Colors.RED_700,
                on_click=lambda e: salvar_transacao("Gasto"),
                expand=True
            )

            page.add(
                ft.Row(
                    [
                        ft.Text(f"👤 {user_email}", weight=ft.FontWeight.BOLD),
                        ft.TextButton("Sair", on_click=logout, style=ft.ButtonStyle(color=ft.Colors.RED_400))
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                ),
                ft.Row([txt_renda_base, ft.ElevatedButton("Atualizar", on_click=carregar_registros)]),
                ft.Row([lbl_receitas, lbl_gastos], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Row([lbl_saldo], alignment=ft.MainAxisAlignment.CENTER),
                pie_chart_ui,  # RESTAURAÇÃO DO GRÁFICO
                msg_erro,
                msg_sucesso,
                ft.Row([txt_descricao]),
                ft.Row([txt_valor, dd_categoria]),
                ft.Row([btn_receita, btn_gasto]),
                ft.Row([txt_busca, dd_filtro]),
                lista_gastos_ui
            )

            carregar_registros()
        except Exception as main_err:
            page.add(ft.Text(f"⚠️ Erro ao carregar tela principal: {str(main_err)}", color=ft.Colors.RED_400))
            page.update()

    carregar_tela_login()

ft.app(target=main)