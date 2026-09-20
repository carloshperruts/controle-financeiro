import os
import sys
from dotenv import load_dotenv
load_dotenv()

import flet as ft
import asyncio
from views.login_view import LoginView
from views.dashboard_view import DashboardView
from utils.helpers import obter_sessao_local, limpar_sessao_local
from config.supabase_client import criar_cliente_supabase

async def main(page: ft.Page):
    # Configurações gerais da janela
    page.title = "Perrut - Controle Financeiro"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#0D0D0D"
    page.padding = 15
    page.scroll = ft.ScrollMode.AUTO

    # Estado da sessão
    sessao_usuario = {"user": None, "session": None}

    # Cliente do Supabase exclusivo desta sessão (não é compartilhado com os
    # outros usuários conectados ao mesmo tempo)
    supabase = criar_cliente_supabase()

    async def fechar_sessao():
        sessao_usuario["user"] = None
        sessao_usuario["session"] = None
        await limpar_sessao_local(page)  # apaga o login salvo, se houver
        page.overlay.clear()  # limpa snackbars/diálogos da sessão anterior
        exibir_login()

    async def login_sucesso(user, session):
        sessao_usuario["user"] = user
        sessao_usuario["session"] = session
        await carregar_dashboard()

    async def carregar_dashboard():
        import traceback
        try:
            dashboard = DashboardView(page, sessao_usuario, fechar_sessao, supabase)
            await dashboard.inicializar()
        except Exception:
            print("=== ERRO REAL AO CARREGAR O DASHBOARD ===")
            traceback.print_exc()

    def exibir_login():
        login_screen = LoginView(page, login_sucesso, supabase)
        login_screen.renderizar()

    async def tentar_auto_login():
        """Se existir um login salvo (checkbox 'Lembrar login'), tenta entrar direto.
        Qualquer falha aqui cai para a tela de login normal, nunca trava a tela."""
        import traceback
        try:
            access_token, refresh_token = await obter_sessao_local(page)
            if not access_token or not refresh_token:
                exibir_login()
                return

            def api_call():
                return supabase.auth.set_session(access_token, refresh_token)

            res = await asyncio.to_thread(api_call)
            if res.user and res.session:
                await login_sucesso(res.user, res.session)
            else:
                await limpar_sessao_local(page)
                exibir_login()
        except Exception:
            print("=== ERRO NO AUTO-LOGIN (caindo para tela de login normal) ===")
            traceback.print_exc()
            try:
                await limpar_sessao_local(page)
            except Exception:
                pass
            exibir_login()

    # Inicia a aplicação tentando restaurar o login salvo (se houver)
    asyncio.create_task(tentar_auto_login())

if __name__ == "__main__":
    os.makedirs(os.path.join(os.getcwd(), "assets", "exports"), exist_ok=True)
    # Roda em modo web (view=ft.AppView.WEB_BROWSER) se "--web" for passado
    # na linha de comando; caso contrário, mantém o comportamento padrão de
    # abrir como janela desktop.
    modo_web = "--web" in sys.argv
    if modo_web:
        ft.run(main, assets_dir="assets", view=ft.AppView.WEB_BROWSER)
    else:
        ft.run(main, assets_dir="assets")