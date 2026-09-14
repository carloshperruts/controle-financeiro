"""
Montagem visual (puro layout) do DashboardView.

Este módulo só constrói e devolve os componentes visuais do dashboard.
Não acessa o Supabase nem contém lógica de negócio — isso continua em
dashboard_view.py. A ideia é que, quando o layout precisar de um ajuste
(cores, espaçamento, textos, posição de um campo), este é o único lugar
a procurar, sem precisar navegar pelo resto da lógica da classe.

Recebe a instância de DashboardView (chamada aqui de `dash`) e usa os
componentes que já foram criados em DashboardView.__init__ (self.txt_renda,
self.dd_cat etc.) e os handlers de eventos (self.salvar_renda_usuario etc.).
"""
import flet as ft
import asyncio


def montar_header(dash):
    user = dash.sessao_usuario.get("user")
    email_str = user.email if user else ""

    return ft.Row([
        ft.Column([
            ft.Text("Perrut - Painel Financeiro", size=22, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_400),
            ft.Text(f"Usuário: {email_str}", color=ft.Colors.GREY_400, size=12),
        ]),
        ft.Row([
            ft.IconButton(
                icon=ft.Icons.REFRESH,
                icon_color=ft.Colors.GREEN_400,
                tooltip="Atualizar",
                on_click=lambda e: asyncio.create_task(dash.atualizar_manual(e))
            ),
            ft.IconButton(
                icon=ft.Icons.LOGOUT,
                tooltip="Sair",
                icon_color=ft.Colors.RED_400,
                on_click=lambda _: asyncio.create_task(dash.fechar_sessao_cb())
            ),
        ])
    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, wrap=True)


def montar_card_renda(dash):
    largura_disponivel = (dash.page.width or 800) - 16
    return ft.Container(
        content=ft.Row([
            dash.txt_renda,
            ft.Row([dash.btn_salvar_renda, dash.loading_renda], spacing=10)
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, wrap=True),
        padding=15, bgcolor=ft.Colors.GREY_900, border_radius=8,
        width=largura_disponivel
    )


def montar_card_resumo(dash):
    largura_disponivel = (dash.page.width or 800) - 16
    return ft.Container(
        content=ft.Column([
            dash.lbl_saldo,
            ft.Row([dash.lbl_receita, dash.lbl_despesa], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, wrap=True)
        ]),
        padding=15, bgcolor=ft.Colors.GREY_900, border_radius=8,
        width=largura_disponivel
    )


def montar_form_lancamento(dash):
    return ft.Container(
        content=ft.Column([
            ft.Text("➕ Novo Lançamento", size=16, weight=ft.FontWeight.BOLD),
            dash.txt_desc,
            ft.Row([dash.txt_val, dash.dd_cat, dash.dd_forma], wrap=True),
            ft.Row([dash.dd_parc, dash.dd_venc, dash.dd_venc_mes], wrap=True),
            ft.Row([
                dash.btn_add_receita,
                dash.btn_add_despesa,
                dash.loading_registro,
            ], alignment=ft.MainAxisAlignment.END, wrap=True)
        ]),
        padding=15, bgcolor=ft.Colors.GREY_900, border_radius=8
    )


def montar_barra_filtros(dash):
    return ft.Row([
        dash.dd_mes_relatorio,
        dash.dd_ano_relatorio,
        ft.ElevatedButton("Relatório", icon=ft.Icons.ASSESSMENT, on_click=dash.abrir_relatorio_mensal),
        ft.ElevatedButton("Exportar CSV", icon=ft.Icons.DOWNLOAD, on_click=dash.acao_exportar_csv),
    ], wrap=True)


def montar_busca_e_categoria(dash):
    return ft.Row([dash.txt_busca, dash.dd_filtro_cat, dash.dd_filtro_forma], wrap=True)


def montar_rodape():
    return ft.Container(
        content=ft.Row(
            [
                ft.Text("Desenvolvido por Carlos Perrut", size=12, color=ft.Colors.GREY_500),
                ft.Text("•", size=12, color=ft.Colors.GREY_700),
                ft.TextButton(
                    "GitHub",
                    icon=ft.Icons.CODE,
                    url="https://github.com/carloshperruts",
                    style=ft.ButtonStyle(color=ft.Colors.GREY_400),
                ),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=8,
        ),
        padding=ft.Padding(0, 20, 0, 10),
    )


def montar_dashboard(dash):
    """
    Monta e devolve a lista de controles principais do dashboard, na ordem
    em que devem ser adicionados à página (dash.page.add(*controles)).
    """
    header = montar_header(dash)
    card_renda = montar_card_renda(dash)
    card_resumo = montar_card_resumo(dash)
    form_lancamento = montar_form_lancamento(dash)
    barra_filtros = montar_barra_filtros(dash)
    busca_e_categoria = montar_busca_e_categoria(dash)
    rodape = montar_rodape()

    return [
        header,
        card_renda,
        card_resumo,
        form_lancamento,
        ft.Divider(height=20),
        barra_filtros,
        busca_e_categoria,
        dash.grafico_ui,
        ft.Divider(height=10),
        ft.Text("📋 Registros do Mês", weight=ft.FontWeight.BOLD, size=16),
        dash.lista_gastos_ui,
        rodape
    ]
