import flet as ft
from supabase import create_client, Client
import os

# Configurações do Supabase
SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://vmkkdenzkoqklvlulajo.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "sb_publishable_ax9nD4u05T1fdUnz-okKlw_a_iB20Hj")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def main(page: ft.Page):
    page.title = "Controle Financeiro"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 20
    page.scroll = ft.ScrollMode.AUTO

    usuario_atual = {"session": None}

    msg_erro = ft.Text("", color="red400")
    msg_sucesso = ft.Text("", color="green400")

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
            msg_erro.value = f"❌ Usuário ou senha incorretos! ({str(ex)})"
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
                            ft.ElevatedButton("Entrar", on_click=realizar_login, bgcolor="blue700", color="white"),
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

        txt_busca = ft.TextField(label="Buscar", prefix_icon="search", expand=True)
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

        lbl_receitas = ft.Text("Receitas: R$ 0.00", color="green400", weight=ft.FontWeight.BOLD)
        lbl_gastos = ft.Text("Gastos: R$ 0.00", color="red400", weight=ft.FontWeight.BOLD)
        lbl_saldo = ft.Text("Saldo: R$ 0.00", color="green400", size=18, weight=ft.FontWeight.BOLD)

        lista_gastos_ui = ft.Column()

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
            lbl_saldo.color = "green400" if saldo >= 0 else "red400"

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
                    cor_valor = "green400" if tipo == "Receita" else "red400"
                    sinal = "+" if tipo == "Receita" else "-"

                    btn_deletar = ft.IconButton(
                        icon="delete_outline",
                        icon_color="red400",
                        tooltip="Excluir",
                        on_click=lambda e, i=item_id: deletar_registro(i)
                    )

                    card_item = ft.Container(
                        content=ft.Row(
                            [
                                ft.Column(
                                    [
                                        ft.Text(desc, weight=ft.FontWeight.BOLD, size=16),
                                        ft.Text(f"{cat} • {sinal}R$ {valor:.2f}", color=cor_valor),
                                    ],
                                    expand=True
                                ),
                                btn_deletar
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                        ),
                        padding=10,
                        border_radius=8,
                        bgcolor="grey900"
                    )
                    lista_gastos_ui.controls.append(card_item)

                calcular_totais(registros)
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
                    "tipo": tipo
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

        # Botões com as cores exatas desejadas (GREEN_700 e RED_700)
        btn_receita = ft.ElevatedButton(
            text="+ Receita",
            bgcolor="green700",
            color="white",
            on_click=lambda e: salvar_transacao("Receita"),
            expand=True
        )

        btn_gasto = ft.ElevatedButton(
            text="- Gasto",
            bgcolor="red700",
            color="white",
            on_click=lambda e: salvar_transacao("Gasto"),
            expand=True
        )

        page.add(
            ft.Row(
                [
                    ft.Text(f"👤 {user_email}", weight=ft.FontWeight.BOLD),
                    ft.TextButton("Sair", on_click=logout, style=ft.ButtonStyle(color="red400"))
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN
            ),
            ft.Row([txt_renda_base, ft.ElevatedButton("Atualizar", on_click=carregar_registros)]),
            ft.Row([lbl_receitas, lbl_gastos], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Container(content=lbl_saldo, alignment=ft.alignment.center),
            msg_erro,
            msg_sucesso,
            ft.Row([txt_descricao]),
            ft.Row([txt_valor, dd_categoria]),
            ft.Row([btn_receita, btn_gasto]),
            ft.Row([txt_busca, dd_filtro]),
            lista_gastos_ui
        )

        carregar_registros()

    carregar_tela_login()

ft.app(target=main)