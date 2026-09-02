import ssl
ssl._create_default_https_context = ssl._create_unverified_context

import csv
import json
import os
import re
from datetime import datetime
import flet as ft
import matplotlib.pyplot as plt

ARQUIVO_USUARIOS = "usuarios.json"
CATEGORIAS = ["Alimentação", "Moradia", "Transporte", "Lazer", "Saúde", "Trabalho", "Outros"]

# --- GERENCIAMENTO DE USUÁRIOS E DADOS ---

def carregar_usuarios():
    if not os.path.exists(ARQUIVO_USUARIOS):
        return {}
    with open(ARQUIVO_USUARIOS, "r") as f:
        return json.load(f)

def salvar_usuarios(usuarios):
    with open(ARQUIVO_USUARIOS, "w") as f:
        json.dump(usuarios, f, indent=4)

def obter_caminho_dados(usuario):
    return f"dados_{usuario}.json"

def carregar_dados_usuario(usuario):
    caminho = obter_caminho_dados(usuario)
    if not os.path.exists(caminho):
        return {"renda": 0.0, "gastos": []}
    with open(caminho, "r") as f:
        return json.load(f)

def salvar_dados_usuario(usuario, dados):
    caminho = obter_caminho_dados(usuario)
    with open(caminho, "w") as f:
        json.dump(dados, f, indent=4)

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

# --- APLICAÇÃO PRINCIPAL ---

def main(page: ft.Page):
    page.title = "Controle Financeiro Pessoal"
    page.theme_mode = ft.ThemeMode.DARK
    page.window_width = 450
    page.window_height = 800
    page.scroll = ft.ScrollMode.AUTO

    usuario_atual = None
    dados = {"renda": 0.0, "gastos": []}

    # --- TELA DE LOGIN ---
    entry_login_user = ft.TextField(label="Usuário", width=300)
    entry_login_pass = ft.TextField(label="Senha", password=True, can_reveal_password=True, width=300)
    lbl_login_aviso = ft.Text(value="", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.RED_400)

    def fazer_login(e):
        nonlocal usuario_atual, dados
        user = entry_login_user.value.strip().lower()
        senha = entry_login_pass.value.strip()

        if not user or not senha:
            lbl_login_aviso.value = "⚠️ Preencha usuário e senha!"
            page.update()
            return

        usuarios = carregar_usuarios()
        if user in usuarios and usuarios[user] == senha:
            usuario_atual = user
            dados = carregar_dados_usuario(usuario_atual)
            carregar_tela_financeira()
        else:
            lbl_login_aviso.value = "❌ Usuário ou senha incorretos!"
            page.update()

    def criar_conta(e):
        user = entry_login_user.value.strip().lower()
        senha = entry_login_pass.value.strip()

        if not user or not senha:
            lbl_login_aviso.value = "⚠️ Digite usuário e senha para cadastrar!"
            page.update()
            return

        usuarios = carregar_usuarios()
        if user in usuarios:
            lbl_login_aviso.value = "⚠️ Usuário já existe! Escolha outro nome."
            page.update()
            return

        usuarios[user] = senha
        salvar_usuarios(usuarios)
        lbl_login_aviso.value = "✅ Conta criada com sucesso! Clique em Entrar."
        lbl_login_aviso.color = ft.Colors.GREEN_400
        page.update()

    def carregar_tela_login():
        page.controls.clear()
        lbl_login_aviso.value = ""
        entry_login_user.value = ""
        entry_login_pass.value = ""

        page.add(
            ft.Container(
                padding=20,
                alignment=ft.alignment.center,
                content=ft.Column([
                    ft.Text("🔐 Acesso ao Sistema", size=22, weight=ft.FontWeight.BOLD),
                    ft.Divider(),
                    lbl_login_aviso,
                    entry_login_user,
                    entry_login_pass,
                    ft.Row([
                        ft.ElevatedButton("Entrar", on_click=fazer_login, bgcolor=ft.Colors.BLUE_700, color=ft.Colors.WHITE, expand=True),
                        ft.OutlinedButton("Criar Conta", on_click=criar_conta, expand=True),
                    ]),
                ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
            )
        )
        page.update()

    # --- TELA FINANCEIRA ---
    def carregar_tela_financeira():
        page.controls.clear()

        lbl_boas_vindas = ft.Text(value=f"👤 Usuário: {usuario_atual.capitalize()}", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_200)
        lbl_total_gasto = ft.Text(value="Gastos: R$ 0.00", size=14, color=ft.Colors.RED_400, weight=ft.FontWeight.BOLD)
        lbl_total_receita = ft.Text(value="Receitas: R$ 0.00", size=14, color=ft.Colors.GREEN_400, weight=ft.FontWeight.BOLD)
        lbl_saldo = ft.Text(value="Saldo: R$ 0.00", size=16, weight=ft.FontWeight.BOLD)
        lbl_aviso = ft.Text(value="", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.AMBER)

        entry_renda = ft.TextField(label="Renda Base (R$)", value=f"{dados['renda']:.2f}", width=180, keyboard_type=ft.KeyboardType.NUMBER)
        entry_desc = ft.TextField(label="Descrição", expand=True)
        entry_valor = ft.TextField(label="Valor (R$)", width=130, keyboard_type=ft.KeyboardType.NUMBER)

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

        def mostrar_mensagem(texto, cor=ft.Colors.AMBER):
            lbl_aviso.value = texto
            lbl_aviso.color = cor
            page.update()

        def atualizar_tela():
            total_gastos = sum(g["valor"] for g in dados["gastos"] if g.get("tipo", "gasto") == "gasto")
            total_receitas = sum(g["valor"] for g in dados["gastos"] if g.get("tipo") == "receita")
            saldo = dados["renda"] + total_receitas - total_gastos

            lbl_total_gasto.value = f"Gastos: R$ {total_gastos:.2f}"
            lbl_total_receita.value = f"Receitas: R$ {total_receitas:.2f}"
            lbl_saldo.value = f"Saldo: R$ {saldo:.2f}"
            lbl_saldo.color = ft.Colors.RED_400 if saldo < 0 else ft.Colors.GREEN_400

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
                data_hora = item.get("data_hora", "Data não registrada")

                if (cat_filtro == "Todas" or cat == cat_filtro) and (termo in desc.lower()):
                    def criar_remover_handler(item_alvo):
                        return lambda e: remover_transacao(item_alvo)

                    cor_valor = ft.Colors.GREEN_400 if tipo == "receita" else ft.Colors.RED_400
                    sinal = "+" if tipo == "receita" else "-"

                    card = ft.Card(
                        content=ft.Container(
                            padding=10,
                            content=ft.Row([
                                ft.Column([
                                    ft.Text(desc, weight=ft.FontWeight.BOLD, size=15),
                                    ft.Text(f"{cat} • {sinal}R$ {item['valor']:.2f}", color=cor_valor, size=13),
                                    ft.Text(f"📅 {data_hora}", size=11, color=ft.Colors.GREY_400),
                                ], expand=True),
                                ft.IconButton(
                                    icon=ft.Icons.DELETE_OUTLINED,
                                    icon_color=ft.Colors.RED_400,
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
                salvar_dados_usuario(usuario_atual, dados)
                atualizar_tela()
                mostrar_mensagem("✅ Renda atualizada!", ft.Colors.GREEN_400)
            except ValueError:
                mostrar_mensagem("⚠️ Erro: Valor de renda inválido.", ft.Colors.RED_400)

        def adicionar_transacao(tipo):
            desc = entry_desc.value.strip() if entry_desc.value else ""
            valor_raw = entry_valor.value.strip() if entry_valor.value else ""
            cat = combo_cat.value

            if not desc or not valor_raw:
                mostrar_mensagem("⚠️ Preencha a descrição e o valor!", ft.Colors.RED_400)
                return

            try:
                valor = limpar_e_converter_numero(valor_raw)
                if valor <= 0:
                    mostrar_mensagem("⚠️ O valor precisa ser maior que zero!", ft.Colors.RED_400)
                    return

                agora = datetime.now().strftime("%d/%m/%Y às %H:%M")
                dados["gastos"].append({
                    "descricao": desc,
                    "valor": valor,
                    "categoria": cat,
                    "tipo": tipo,
                    "data_hora": agora
                })

                salvar_dados_usuario(usuario_atual, dados)
                entry_desc.value = ""
                entry_valor.value = ""
                atualizar_tela()
                mostrar_mensagem(f"✅ {'Receita' if tipo == 'receita' else 'Gasto'} adicionado!", ft.Colors.GREEN_400)
            except ValueError:
                mostrar_mensagem("❌ Erro: Digite um valor numérico válido.", ft.Colors.RED_400)

        def remover_transacao(item):
            dados["gastos"].remove(item)
            salvar_dados_usuario(usuario_atual, dados)
            atualizar_tela()
            mostrar_mensagem("Item removido.", ft.Colors.AMBER)

        def sair_conta(e):
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
                        ft.ElevatedButton("➕ Receita", on_click=lambda e: adicionar_transacao("receita"), bgcolor=ft.Colors.GREEN_700, color=ft.Colors.WHITE, expand=True),
                        ft.ElevatedButton("➖ Gasto", on_click=lambda e: adicionar_transacao("gasto"), bgcolor=ft.Colors.RED_700, color=ft.Colors.WHITE, expand=True),
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
    import os
    port = int(os.environ.get("PORT", 8550))
    host = "0.0.0.0" if "PORT" in os.environ else "localhost"
    ft.app(target=main, view=ft.AppView.WEB_BROWSER, host=host, port=port)