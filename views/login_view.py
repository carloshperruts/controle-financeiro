import flet as ft
import asyncio
from config.supabase_client import supabase
from components.matrix_bg import criar_fundo_matrix_animado
from utils.helpers import salvar_sessao_local, limpar_sessao_local

class LoginView:
    def __init__(self, page: ft.Page, ao_sucesso):
        self.page = page
        self.ao_sucesso = ao_sucesso
        self.modo_auth = "login"

        # Mensagens de status
        self.msg_erro = ft.Text("", color=ft.Colors.RED_400, size=13, weight=ft.FontWeight.BOLD)
        self.msg_sucesso = ft.Text("", color=ft.Colors.GREEN_400, size=13, weight=ft.FontWeight.BOLD)

        # Campos do formulário
        self.email_input = ft.TextField(label="E-mail", width=320, hint_text="exemplo@email.com")
        self.senha_input = ft.TextField(label="Senha", password=True, can_reveal_password=True, width=320)
        self.confirmar_senha_input = ft.TextField(label="Confirmar Senha", password=True, can_reveal_password=True, width=320)
        self.lembrar_login_check = ft.Checkbox(
            label="Lembrar login",
            value=False,
            label_style=ft.TextStyle(size=13, color=ft.Colors.GREY_300),
            scale=0.85,
        )

        # Marca d'água visual
        self.watermark = ft.Container(
            content=ft.Text("PERRUT", size=100, weight=ft.FontWeight.BOLD, color="#00FF66", opacity=0.08),
            margin=ft.Margin(0, 10, 0, 0)
        )

        self.dicas_cadastro = ft.Container(
            content=ft.Column(
                [
                    ft.Row([
                        ft.Icon(ft.Icons.INFO_OUTLINE, color="#00FF66", size=18),
                        ft.Text("Instruções para Cadastro:", weight=ft.FontWeight.BOLD, color="#00FF66", size=13)
                    ]),
                    ft.Text("• Insira um endereço de e-mail válido.", size=12, color=ft.Colors.GREY_300),
                    ft.Text("• A senha deve conter pelo menos 6 caracteres.", size=12, color=ft.Colors.GREY_300),
                ],
                spacing=4
            ),
            padding=12,
            bgcolor=ft.Colors.GREY_900,
            border=ft.Border(
                ft.BorderSide(1, "#00FF66"),
                ft.BorderSide(1, "#00FF66"),
                ft.BorderSide(1, "#00FF66"),
                ft.BorderSide(1, "#00FF66")
            ),
            border_radius=8,
            width=320
        )

        self.titulo_auth = ft.Text("Perrut - Controle Financeiro", size=24, weight=ft.FontWeight.BOLD, color="#00FF66")

    def mudar_modo(self, novo_modo):
        self.modo_auth = novo_modo
        self.renderizar()

    async def realizar_login(self, e):
        self.msg_erro.value = ""
        self.msg_sucesso.value = ""

        email_val = self.email_input.value.strip().lower()
        senha_val = self.senha_input.value.strip()

        if not email_val or not senha_val:
            self.msg_erro.value = "⚠️ Por favor, informe o e-mail e a senha."
            self.page.update()
            return

        try:
            def api_call():
                return supabase.auth.sign_in_with_password({"email": email_val, "password": senha_val})

            res = await asyncio.to_thread(api_call)

            if res.user and res.session:
                if self.lembrar_login_check.value:
                    await salvar_sessao_local(self.page, res.session.access_token, res.session.refresh_token)
                else:
                    await limpar_sessao_local(self.page)
                await self.ao_sucesso(res.user, res.session)
            else:
                self.msg_erro.value = "❌ Falha ao autenticar. Verifique seus dados."
                self.page.update()

        except Exception as ex:
            self.msg_erro.value = f"❌ Erro ao entrar: {str(ex)}"
            self.page.update()

    async def realizar_cadastro(self, e):
        self.msg_erro.value = ""
        self.msg_sucesso.value = ""

        email_val = self.email_input.value.strip().lower()
        senha_val = self.senha_input.value.strip()
        conf_senha_val = self.confirmar_senha_input.value.strip()

        if not email_val:
            self.msg_erro.value = "⚠️ Informe um e-mail válido."
            self.page.update()
            return

        if len(senha_val) < 6 or senha_val != conf_senha_val:
            self.msg_erro.value = "⚠️ Verifique as senhas informadas (mínimo 6 caracteres)."
            self.page.update()
            return

        try:
            def api_call():
                return supabase.auth.sign_up({"email": email_val, "password": senha_val})

            await asyncio.to_thread(api_call)
            self.mudar_modo("login")
            self.msg_sucesso.value = "✔ Conta criada com sucesso! Digite sua senha para entrar."
            self.page.update()
        except Exception as ex:
            self.msg_erro.value = f"❌ Erro: {str(ex)}"
            self.page.update()

    async def recuperar_senha(self, e):
        self.msg_erro.value = ""
        self.msg_sucesso.value = ""
        email_val = self.email_input.value.strip().lower()

        if not email_val:
            self.msg_erro.value = "⚠️ Informe um e-mail válido."
            self.page.update()
            return

        try:
            def api_call():
                return supabase.auth.reset_password_for_email(email_val)

            await asyncio.to_thread(api_call)
            self.mudar_modo("login")
            self.msg_sucesso.value = "✉️ E-mail de recuperação enviado!"
            self.page.update()
        except Exception as ex:
            self.msg_erro.value = f"❌ Erro: {str(ex)}"
            self.page.update()

    def renderizar(self):
        self.page.clean()

        if self.modo_auth == "login":
            conteudo = [
                self.titulo_auth,
                ft.Text("Acesse sua conta para continuar", size=14, color=ft.Colors.GREY_400),
                ft.Divider(color="#00FF66", height=15),
                self.msg_erro, self.msg_sucesso,
                self.email_input, self.senha_input,
                ft.Container(content=self.lembrar_login_check, width=320, alignment=ft.Alignment(-1, 0)),
                ft.TextButton("Esqueceu sua senha?", on_click=lambda _: self.mudar_modo("recuperar")),
                ft.ElevatedButton("Entrar", width=150, bgcolor="#00AA44", color=ft.Colors.WHITE, on_click=lambda ev: asyncio.create_task(self.realizar_login(ev))),
                ft.TextButton("Não tem uma conta? Cadastre-se aqui", on_click=lambda _: self.mudar_modo("cadastro")),
                self.watermark
            ]
        elif self.modo_auth == "cadastro":
            conteudo = [
                self.titulo_auth,
                self.dicas_cadastro,
                self.msg_erro, self.msg_sucesso,
                self.email_input, self.senha_input, self.confirmar_senha_input,
                ft.ElevatedButton("Cadastrar", width=150, bgcolor="#00AA44", color=ft.Colors.WHITE, on_click=lambda ev: asyncio.create_task(self.realizar_cadastro(ev))),
                ft.TextButton("Voltar para a tela de login", on_click=lambda _: self.mudar_modo("login")),
                self.watermark
            ]
        else:
            conteudo = [
                self.titulo_auth,
                self.msg_erro, self.msg_sucesso,
                self.email_input,
                ft.ElevatedButton("Enviar E-mail", width=160, bgcolor="#00AA44", color=ft.Colors.WHITE, on_click=lambda ev: asyncio.create_task(self.recuperar_senha(ev))),
                ft.TextButton("Voltar para o login", on_click=lambda _: self.mudar_modo("login")),
                self.watermark
            ]

        self.page.add(
            ft.Stack([
                criar_fundo_matrix_animado(self.page),
                ft.Container(
                    content=ft.Column(conteudo, alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
                    alignment=ft.Alignment(0, 0),
                    padding=20
                )
            ], expand=True)
        )
        self.page.update()