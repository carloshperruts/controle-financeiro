import ssl
ssl._create_default_https_context = ssl._create_unverified_context

import csv
import json
import re
import flet as ft
import matplotlib.pyplot as plt

ARQUIVO = "dados_financeiros.json"
CATEGORIAS = ["Alimentação", "Moradia", "Transporte", "Lazer", "Saúde", "Outros"]

def carregar_dados():
    try:
        with open(ARQUIVO, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"renda": 0.0, "gastos": []}

def salvar_dados(dados):
    with open(ARQUIVO, "w") as f:
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

def main(page: ft.Page):
    page.title = "Controle Financeiro Pessoal"
    page.theme_mode = ft.ThemeMode.DARK
    page.window_width = 450
    page.window_height = 750
    page.scroll = ft.ScrollMode.AUTO

    dados = carregar_dados()

    lbl_total_gasto = ft.Text(value="Total Gasto: R$ 0.00", size=16, weight=ft.FontWeight.BOLD)
    lbl_saldo = ft.Text(value="Saldo: R$ 0.00", size=16, weight=ft.FontWeight.BOLD)

    entry_renda = ft.TextField(label="Renda Mensal (R$)", value=f"{dados['renda']:.2f}", width=180, keyboard_type=ft.KeyboardType.NUMBER)
    entry_desc = ft.TextField(label="Descrição do Gasto", expand=True)
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

    def atualizar_tela():
        total = sum(g["valor"] for g in dados["gastos"])
        saldo = dados["renda"] - total

        lbl_total_gasto.value = f"Total Gasto: R$ {total:.2f}"
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

            if (cat_filtro == "Todas" or cat == cat_filtro) and (termo in desc.lower()):
                def criar_remover_handler(item_alvo):
                    return lambda e: remover_gasto(item_alvo)

                card = ft.Card(
                    content=ft.Container(
                        padding=10,
                        content=ft.Row([
                            ft.Column([
                                ft.Text(desc, weight=ft.FontWeight.BOLD, size=15),
                                ft.Text(f"{cat} • R$ {item['valor']:.2f}", color=ft.Colors.GREY_400, size=13),
                            ], expand=True),
                            ft.IconButton(
                                icon=ft.Icons.DELETE_OUTLINED,
                                icon_color=ft.Colors.RED_400,
                                tooltip="Remover Gasto",
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
            salvar_dados(dados)
            atualizar_tela()
            page.open(ft.SnackBar(ft.Text("Renda atualizada!")))
        except ValueError:
            page.open(ft.SnackBar(ft.Text("Erro: Valor de renda inválido.")))

    def adicionar_gasto(e):
        desc = entry_desc.value.strip() if entry_desc.value else ""
        valor_raw = entry_valor.value.strip() if entry_valor.value else ""
        cat = combo_cat.value

        if not desc:
            page.open(ft.SnackBar(ft.Text("Preencha a descrição do gasto.")))
            return

        try:
            valor = limpar_e_converter_numero(valor_raw)
            dados["gastos"].append({"descricao": desc, "valor": valor, "categoria": cat})
            salvar_dados(dados)
            entry_desc.value = ""
            entry_valor.value = ""
            atualizar_tela()
        except ValueError:
            page.open(ft.SnackBar(ft.Text("Erro: Digite um valor válido.")))

    def remover_gasto(item):
        dados["gastos"].remove(item)
        salvar_dados(dados)
        atualizar_tela()

    def limpar_todos(e):
        if not dados["gastos"]:
            return
        dados["gastos"] = []
        salvar_dados(dados)
        atualizar_tela()
        page.open(ft.SnackBar(ft.Text("Todos os gastos foram removidos!")))

    def exportar_csv(e):
        if not dados["gastos"]:
            page.open(ft.SnackBar(ft.Text("Sem gastos para exportar.")))
            return
        try:
            with open("relatorio_financeiro.csv", mode="w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f, delimiter=";")
                writer.writerow(["Descrição", "Valor (R$)", "Categoria"])
                for item in dados["gastos"]:
                    writer.writerow([item["descricao"], f"{item['valor']:.2f}", item.get("categoria", "Outros")])
            page.open(ft.SnackBar(ft.Text("Exportado para relatorio_financeiro.csv!")))
        except Exception as ex:
            page.open(ft.SnackBar(ft.Text(f"Erro ao exportar: {ex}")))

    def exibir_grafico(e):
        if not dados["gastos"]:
            page.open(ft.SnackBar(ft.Text("Sem gastos para gerar gráfico.")))
            return
        totais_cat = {}
        for g in dados["gastos"]:
            c = g.get("categoria", "Outros")
            totais_cat[c] = totais_cat.get(c, 0.0) + g["valor"]

        plt.figure(figsize=(6, 5))
        plt.pie(totais_cat.values(), labels=totais_cat.keys(), autopct='%1.1f%%', startangle=140)
        plt.title("Distribuição de Gastos")
        plt.tight_layout()
        plt.show()

    entry_busca.on_change = lambda e: atualizar_tabela()
    combo_filtro_cat.on_change = lambda e: atualizar_tabela()

    page.add(
        ft.Container(
            padding=10,
            content=ft.Column([
                ft.Row([entry_renda, ft.ElevatedButton("Atualizar", on_click=atualizar_renda)]),
                ft.Row([lbl_total_gasto, lbl_saldo], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Divider(),
                ft.Row([entry_desc]),
                ft.Row([entry_valor, combo_cat]),
                ft.ElevatedButton("➕ Adicionar Gasto", on_click=adicionar_gasto, width=400),
                ft.Divider(),
                ft.Row([entry_busca, combo_filtro_cat]),
                ft.Row([
                    ft.ElevatedButton("📊 Ver Gráfico", on_click=exibir_grafico),
                    ft.OutlinedButton("📁 Exportar CSV", on_click=exportar_csv),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Divider(),
                lista_gastos_vview,
                ft.ElevatedButton("🗑️ Limpar Todos", on_click=limpar_todos, color=ft.Colors.WHITE, bgcolor=ft.Colors.RED_600, width=400)
            ])
        )
    )

    atualizar_tela()

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8550))
    ft.app(target=main, view=ft.AppView.WEB_BROWSER, host="0.0.0.0", port=port)