import flet as ft
import asyncio
from views.login_view import LoginView
from views.dashboard_view import DashboardView

async def main(page: ft.Page):
    # Configurações gerais da janela
    page.title = "Perrut - Controle Financeiro"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#0D0D0D"
    page.padding = 15
    page.scroll = ft.ScrollMode.AUTO

    # Estado da sessão
    sessao_usuario = {"user": None, "session": None}

    async def fechar_sessao():
        sessao_usuario["user"] = None
        sessao_usuario["session"] = None
        exibir_login()

    async def login_sucesso(user, session):
        sessao_usuario["user"] = user
        sessao_usuario["session"] = session
        await carregar_dashboard()

    async def carregar_dashboard():
        dashboard = DashboardView(page, sessao_usuario, fechar_sessao)
        await dashboard.inicializar()

    def exibir_login():
        login_screen = LoginView(page, login_sucesso)
        login_screen.renderizar()

    # Inicia a aplicação na tela de login
    exibir_login()

if __name__ == "__main__":
    ft.app(target=main)