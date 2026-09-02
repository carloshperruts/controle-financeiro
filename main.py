import ssl
ssl._create_default_https_context = ssl._create_unverified_context

import csv
import json
import re
from datetime import datetime
import flet as ft
import matplotlib.pyplot as plt

ARQUIVO = "dados_financeiros.json"
CATEGORIAS = ["Alimentação", "Moradia", "Transporte", "Lazer", "Saúde", "Trabalho", "Outros"]

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
    page.window_height = 800
    page.scroll = ft.ScrollMode.AUTO

    dados = carregar_dados()

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
            # Garante compatibilidade com itens antigos salvos sem data
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
                                ft.Text(f"📅 {data_hora}", size=11, color=ft.Colors.GREY_400), # Exibe Data e Hora
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
            salvar_dados(dados)
            atualizar_tela()
            mostrar_mensagem("✅ Renda atualizada!", ft.Colors.GREEN_400)
        except ValueError:
            mostrar_mensagem("⚠️ Erro: Valor de renda inválido.", ft.Colors.RED_400)

    def adicionar_transacao(tipo):
        desc = entry_desc.value.strip() if entry_desc.value else ""
        valor_raw = entry_valor.value.strip() if entry_valor.value else ""
        cat = combo_cat.value

        if not desc:
            mostrar_mensagem("⚠️ Preencha a descrição antes de continuar!", ft.Colors.RED_400)
            return

        if not valor_raw:
            mostrar_mensagem("⚠️ Digite um valor para a transação!", ft.Colors.RED_400)
            return

        try:
            valor = limpar_e_converter_numero(valor_raw)
            
            if valor <= 0:
                mostrar_mensagem("⚠️ O valor precisa ser maior que zero!", ft.Colors.RED_400)
                return

            # Captura a data e hora exata da operação
            agora = datetime.now().strftime("%d/%m/%Y às %H:%M")

            dados["gastos"].append({
                "descricao": desc,
                "valor": valor,
                "categoria": cat,
                "tipo": tipo,
                "data_hora": agora
            })
            
            salvar_dados(dados)
            entry_desc.value = ""
            entry_valor.value = ""
            atualizar_tela()
            mostrar_mensagem(f"✅ {'Receita' if tipo == 'receita' else 'Gasto'} adicionado com sucesso!", ft.Colors.GREEN_400)
        except ValueError:
            mostrar_mensagem("❌ Erro: Digite um valor numérico válido.", ft.Colors.RED_400)

    def remover_transacao(item):
        dados["gastos"].remove(item)
        salvar_dados(dados)
        atualizar_tela()
        mostrar_mensagem("Item removido.", ft.Colors.AMBER)

    def limpar_todos(e):
        if not dados["gastos"]:
            return
        dados["gastos"] = []
        salvar_dados(dados)
        atualizar_tela()
        mostrar_mensagem("Todas as transações foram removidas!", ft.Colors.AMBER)

    def exportar_csv(e):
        if not dados["gastos"]:
            mostrar_mensagem("Sem transações para exportar.", ft.Colors.AMBER)
            return
        try:
            with open("relatorio_financeiro.csv", mode="w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f, delimiter=";")
                # Adiciona Data/Hora no relatório CSV
                writer.writerow(["Descrição", "Valor (R$)", "Categoria", "Tipo", "Data/Hora"])
                for item in dados["gastos"]:
                    writer.writerow([
                        item["descricao"],
                        f"{item['valor']:.2f}",
                        item.get("categoria", "Outros"),
                        item.get("tipo", "gasto"),
                        item.get("data_hora", "N/A")
                    ])
            mostrar_mensagem("Exportado para relatorio_financeiro.csv!", ft.Colors.GREEN_400)
        except Exception as ex:
            mostrar_mensagem(f"Erro ao exportar: {ex}", ft.Colors.RED_400)

    def exibir_grafico(e):
        gastos_apenas = [g for g in dados["gastos"] if g.get("tipo", "gasto") == "gasto"]
        if not gastos_apenas:
            mostrar_mensagem("Sem gastos para gerar gráfico.", ft.Colors.AMBER)
            return
        totais_cat = {}
        for g in gastos_apenas:
            c = g.get("categoria", "Outros")
            totais_cat[c] = totais_cat.get(c, 0.0) + g["valor"]

        plt.figure(figsize=(6, 5))
        plt.pie(totais_cat.values(), labels=totais_cat.keys(), autopct='%1.1f%%', startangle=140)
        plt.title("Distribuição de Gastos por Categoria")
        plt.tight_layout()
        plt.show()

    entry_busca.on_change = lambda e: atualizar_tabela()
    combo_filtro_cat.on_change = lambda e: atualizar_tabela()

    page.add(
        ft.Container(
            padding=10,
            content=ft.Column([
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
                ft.Row([
                    ft.ElevatedButton("📊 Ver Gráfico", on_click=exibir_grafico),
                    ft.OutlinedButton("📁 Exportar CSV", on_click=exportar_csv),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Divider(),
                lista_gastos_vview,
                ft.ElevatedButton("🗑️ Limpar Todos", on_click=limpar_todos, color=ft.Colors.WHITE, bgcolor=ft.Colors.RED_900, width=400)
            ])
        )
    )

    atualizar_tela()

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8550))
    host = "0.0.0.0" if "PORT" in os.environ else "localhost"
    ft.app(target=main, view=ft.AppView.WEB_BROWSER, host=host, port=port)