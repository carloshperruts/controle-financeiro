import os
import re
from datetime import datetime
import flet as ft
from supabase import create_client, Client

# Configuração do Supabase
SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://vmkkdenzkoqklvlulajo.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "sb_publishable_ax9nD4u05T1fdUnz-okKlw_a_iB20Hj")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
CATEGORIAS = ["Alimentação", "Moradia", "Transporte", "Lazer", "Saúde", "Trabalho", "Outros"]

def limpar_e_converter_numero(texto):
    texto_limpo = re.sub(r'[^\d.,]', '', texto)
    if not texto_limpo:
        raise ValueError("Nenhum número encontrado")

    if '.' in texto_limpo and ',' in texto_limpo:
        pos_ponto = texto_limpo.rfind('.')
        pos_virgula = texto_limpo.rfind(',')
        if pos_virgula > pos_ponto:
            texto_limpo = texto_limpo.replace('.', '').replace(',', '.')
        else:
            texto_limpo = texto_limpo.replace(',', '')
    elif ',' in texto_limpo:
        texto_limpo = texto_limpo.replace(',', '.')
    elif texto_limpo.count('.') > 1:
        partes = texto_limpo.split('.')
        if len(partes[-1]) == 2:
            texto_limpo = "".join(partes[:-1]) + "." + partes[-1]
        else:
            texto_limpo = "".join(partes)

    return float(texto_limpo)

def main(page: ft.Page):
    page.title = "Controle Financeiro Pessoal"
    page.theme_mode = ft.ThemeMode.DARK
    page.window_width = 450
    page.window_height = 800
    page.scroll = ft.ScrollMode.AUTO

    usuario_atual = None
    dados = {"renda": 0.0, "gastos": []}

    # Campos de Entrada
    entry_email = ft.TextField(
        label="E-mail", 
        hint_text="seuemail@exemplo.com", 
        width=320
    )
    entry_senha = ft.TextField(
        label="Senha", 
        password=True, 
        can_reveal_password=True, 
        width=320
    )
    
    lbl_auth_aviso = ft.Text(value="", size=14, weight=ft.FontWeight.BOLD)

    def mostrar_aviso_auth(texto, cor="red"):
        lbl_auth_aviso.value = texto
        lbl_auth_aviso.color = cor
        page.update()

    # --- FUNÇÕES DE AUTENTICAÇÃO ---

    def fazer_login(e):
        nonlocal usuario_atual
        email = entry_email.value.strip() if entry_email.value else ""
        senha = entry_senha.value.strip() if entry_senha.value else ""

        if not email or not senha:
            mostrar_aviso_auth("⚠️ Digite e-mail e senha!")
            return

        try:
            res = supabase.auth.sign_in_with_password({"email": email, "password": senha})
            usuario_atual = res.user
            carregar_dados_supabase()
            carregar_tela_financeira()
        except Exception:
            mostrar_aviso_auth("❌ E-mail ou senha incorretos.")

    def criar_conta(e):
        email = entry_email.value.strip() if entry_email.value else ""
        senha = entry_senha.value.strip() if entry_senha.value else ""

        if not email or not senha:
            mostrar_aviso_auth("⚠️ Digite e-mail e crie uma senha!")
            return

        if len(senha) < 6:
            mostrar_aviso_auth("⚠️ A senha precisa ter 6+ caracteres!")
            return

        try:
            supabase.auth.sign_up({"email": email, "password": senha})
            mostrar_aviso_auth("✅ Conta criada! Verifique o e-mail.", "green")
        except Exception as err:
            mostrar_aviso_auth(f"❌ Erro ao cadastrar: {str(err)}")

    def recuperar_senha(e):
        email = entry_email.value.strip() if entry_email.value else ""
        if not email:
            mostrar_aviso_auth("⚠️ Preencha o e-mail acima primeiro!")
            return

        try:
            supabase.auth.reset_password_for_email(email)
            mostrar_aviso_auth("📧 E-mail de redefinição enviado!", "green")
        except Exception as err:
            mostrar_aviso_auth(f"❌ Erro ao solicitar: {str(err)}")

    def carregar_tela_login():
        page.controls.clear()
        lbl_auth_aviso.value = ""

        page.add(
            ft.Column([
                ft.Text("🔑 Acesso ao Sistema", size=22, weight=ft.FontWeight.BOLD),
                lbl_auth_aviso,
                entry_email,
                entry_senha,
                ft.Container(height=10),
                ft.ElevatedButton(
                    "Entrar", 
                    on_click=fazer_login, 
                    width=320
                ),
                ft.OutlinedButton(
                    "Criar Conta com este E-mail", 
                    on_click=criar_conta, 
                    width=320
                ),
                ft.TextButton(
                    "Esqueceu a senha?", 
                    on_click=recuperar_senha
                )
            ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        )
        page.update()

    # --- BANCO DE DADOS (SUPABASE) ---

    def carregar_dados_supabase():
        nonlocal dados
        try:
            res = supabase.table("gastos").select("*").execute()
            dados["gastos"] = res.data
        except Exception as err:
            print(f"Erro ao carregar dados: {err}")
            dados["gastos"] = []

    # --- TELA FINANCEIRA ---

    def carregar_tela_financeira():
        page.controls.clear()

        lbl_boas_vindas = ft.Text(value=f"👤 {usuario_atual.email}", size=13, weight=ft.FontWeight.BOLD)
        lbl_total_gasto = ft.Text(value="Gastos: R$ 0.00", size=14, color="red", weight=ft.FontWeight.BOLD)
        lbl_total_receita = ft.Text(value="Receitas: R$ 0.00", size=14, color="green", weight=ft.FontWeight.BOLD)
        lbl_saldo = ft.Text(value="Saldo: R$ 0.00", size=16, weight=ft.FontWeight.BOLD)
        lbl_aviso = ft.Text(value="", size=14, weight=ft.FontWeight.BOLD)

        entry_renda = ft.TextField(label="Renda Base (R$)", value=f"{dados['renda']:.2f}", width=180)
        entry_desc = ft.TextField(label="Descrição", expand=True)
        entry_valor = ft.TextField(label="Valor (R$)", width=130)

        combo_cat = ft.Dropdown(
            label="Categoria",
            options=[ft.dropdown.Option(c) for c in CATEGORIAS],
            value="Alimentação",
            width=160
        )

        entry_busca = ft.TextField(label="🔎 Buscar", expand=True)
        combo_filtro_cat = ft.Dropdown(
            label="Filtrar Categoria",
            options=[ft.dropdown.Option("Todas")] + [ft.dropdown.Option(c) for c in CATEGORIAS],
            value="Todas",
            width=160
        )

        lista_gastos_vview = ft.Column(scroll=ft.ScrollMode.AUTO, height=250)

        def mostrar_mensagem(texto, cor="orange"):
            lbl_aviso.value = texto
            lbl_aviso.color = cor
            page.update()

        def atualizar_tela():
            total_gastos = sum(g["valor"] for g in dados["gastos"] if g.get("tipo") == "gasto")
            total_receitas = sum(g["valor"] for g in dados["gastos"] if g.get("tipo") == "receita")
            saldo = dados["renda"] + total_receitas - total_gastos

            lbl_total_gasto.value = f"Gastos: R$ {total_gastos:.2f}"
            lbl_total_receita.value = f"Receitas: R$ {total_receitas:.2f}"
            lbl_saldo.value = f"Saldo: R$ {saldo:.2f}"
            lbl_saldo.color = "red" if saldo < 0 else "green"

            atualizar_tabela()
            page.update()

        def atualizar_tabela():
            lista_gastos_vview.controls.clear()
            termo = entry_busca.value.lower().strip() if entry_busca.value else ""
            cat_filtro = combo_filtro_cat.value

            for item in dados["gastos"]:
                cat = item.get("categoria", "Outros")
                desc = item["descricao"]
                tipo = item.get("tipo", "gasto")
                data_hora = item.get("data_hora", "")

                if (cat_filtro == "Todas" or cat == cat_filtro) and (termo in desc.lower()):
                    def criar_remover_handler(item_alvo):
                        return lambda e: remover_transacao(item_alvo)

                    cor_valor = "green" if tipo == "receita" else "red"
                    sinal = "+" if tipo == "receita" else "-"

                    card = ft.Card(
                        content=ft.Container(
                            padding=10,
                            content=ft.Row([
                                ft.Column([
                                    ft.Text(desc, weight=ft.FontWeight.BOLD, size=15),
                                    ft.Text(f"{cat} • {sinal}R$ {item['valor']:.2f}", color=cor_valor, size=13),
                                    ft.Text(f"📅 {data_hora}", size=11, color="grey"),
                                ], expand=True),
                                ft.IconButton(
                                    icon="delete",
                                    icon_color="red",
                                    tooltip="Remover",
                                    on_click=criar_remover_handler(item)
                                )
                            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
                        )
                    )
                    lista_gastos_vview.controls.append(card)

            page.update()

        def atualizar_renda(e):
            try:
                val = limpar_e_converter_numero(entry_renda.value)
                dados["renda"] = val
                atualizar_tela()
                mostrar_mensagem("✅ Renda atualizada!", "green")
            except ValueError:
                mostrar_mensagem("⚠️ Erro: Valor de renda inválido.", "red")

        def adicionar_transacao(tipo):
            desc = entry_desc.value.strip() if entry_desc.value else ""
            valor_raw = entry_valor.value.strip() if entry_valor.value else ""
            cat = combo_cat.value

            if not desc or not valor_raw:
                mostrar_mensagem("⚠️ Preencha descrição e valor!", "red")
                return

            try:
                valor = limpar_e_converter_numero(valor_raw)
                if valor <= 0:
                    mostrar_mensagem("⚠️ O valor precisa ser maior que zero!", "red")
                    return

                agora = datetime.now().strftime("%d/%m/%Y às %H:%M")
                novo_item = {
                    "user_id": usuario_atual.id,
                    "descricao": desc,
                    "valor": valor,
                    "categoria": cat,
                    "tipo": tipo,
                    "data_hora": agora
                }

                res = supabase.table("gastos").insert(novo_item).execute()
                if res.data:
                    dados["gastos"].append(res.data[0])

                entry_desc.value = ""
                entry_valor.value = ""
                atualizar_tela()
                mostrar_mensagem(f"✅ {'Receita' if tipo == 'receita' else 'Gasto'} adicionado!", "green")
            except Exception as err:
                mostrar_mensagem(f"❌ Erro ao salvar: {str(err)}", "red")

        def remover_transacao(item):
            try:
                supabase.table("gastos").delete().eq("id", item["id"]).execute()
                dados["gastos"].remove(item)
                atualizar_tela()
                mostrar_mensagem("Item removido.", "orange")
            except Exception as err:
                mostrar_mensagem(f"❌ Erro ao remover: {str(err)}", "red")

        def sair_conta(e):
            supabase.auth.sign_out()
            carregar_tela_login()

        entry_busca.on_change = lambda e: atualizar_tabela()
        combo_filtro_cat.on_change = lambda e: atualizar_tabela()

        page.add(
            ft.Container(
                padding=10,
                content=ft.Column([
                    ft.Row([lbl_boas_vindas, ft.TextButton("🚪 Sair", on_click=sair_conta)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Row([entry_renda, ft.ElevatedButton("Atualizar", on_click=atualizar_renda)]),
                    ft.Row([lbl_total_receita, lbl_total_gasto], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Row([lbl_saldo], alignment=ft.MainAxisAlignment.CENTER),
                    ft.Divider(),
                    ft.Row([lbl_aviso], alignment=ft.MainAxisAlignment.CENTER),
                    ft.Row([entry_desc]),
                    ft.Row([entry_valor, combo_cat]),
                    ft.Row([
                        ft.ElevatedButton("➕ Receita", on_click=lambda e: adicionar_transacao("receita"), expand=True),
                        ft.ElevatedButton("➖ Gasto", on_click=lambda e: adicionar_transacao("gasto"), expand=True),
                    ]),
                    ft.Divider(),
                    ft.Row([entry_busca, combo_filtro_cat]),
                    ft.Divider(),
                    lista_gastos_vview,
                ])
            )
        )
        atualizar_tela()

    carregar_tela_login()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8550))
    host = "0.0.0.0" if "PORT" in os.environ else "localhost"
    ft.app(target=main, view=ft.AppView.WEB_BROWSER, host=host, port=port)