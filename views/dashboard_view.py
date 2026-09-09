import flet as ft
import asyncio
from datetime import datetime
from config.supabase_client import supabase, CATEGORIAS
from utils.helpers import obter_mes_ano_efetivo, exportar_para_csv

MESES_NOMES = [
    "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
]

FORMAS_PAGAMENTO = ["Débito / Pix", "Cartão de Crédito", "Dinheiro"]

class DashboardView:
    def __init__(self, page: ft.Page, sessao_usuario: dict, fechar_sessao_cb):
        self.page = page
        self.sessao_usuario = sessao_usuario
        self.fechar_sessao_cb = fechar_sessao_cb
        self.registros_cache = []

        # Ativa scroll geral na página para evitar telas cinzas/cortadas
        self.page.scroll = ft.ScrollMode.AUTO

        # Componentes UI
        self.txt_renda = ft.TextField(label="Renda Base (R$)", value="0,00", width=200, keyboard_type=ft.KeyboardType.NUMBER)
        self.lbl_saldo = ft.Text("Saldo do Mês: R$ 0.00", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_400)
        self.lbl_receita = ft.Text("Receitas: R$ 0.00", color=ft.Colors.GREEN_400)
        self.lbl_despesa = ft.Text("Despesas: R$ 0.00", color=ft.Colors.RED_400)

        # Formulário
        self.txt_desc = ft.TextField(label="Descrição", expand=True)
        self.txt_val = ft.TextField(label="Valor Total (R$)", width=150, keyboard_type=ft.KeyboardType.NUMBER)
        self.dd_cat = ft.Dropdown(label="Categoria", options=[ft.dropdown.Option(c) for c in CATEGORIAS], value=CATEGORIAS[0], width=200)
        self.dd_forma = ft.Dropdown(
            label="Pagamento / Origem",
            options=[ft.dropdown.Option(f) for f in FORMAS_PAGAMENTO],
            value="Débito / Pix",
            width=200
        )
        self.dd_parc = ft.Dropdown(
            label="Parcelas",
            options=[ft.dropdown.Option(f"{i}x") for i in range(1, 13)],
            value="1x",
            width=100,
            visible=False
        )
        self.dd_venc = ft.Dropdown(
            label="Vencimento Dia",
            options=[ft.dropdown.Option(f"Dia {i}") for i in range(1, 32)],
            value="Dia 10",
            width=130,
            visible=False
        )
        self.dd_venc_mes = ft.Dropdown(
            label="Vencimento Mês",
            options=[ft.dropdown.Option(m) for m in MESES_NOMES],
            value=MESES_NOMES[datetime.now().month - 1],
            width=160,
            visible=False
        )
        # Só mostra Parcelas/Vencimento quando a forma de pagamento for Cartão de Crédito
        self.dd_forma.on_select = self.atualizar_visibilidade_parcelas
        # Filtros
        mes_atual_idx = datetime.now().month - 1
        self.dd_mes_relatorio = ft.Dropdown(
            label="Mês do Período",
            options=[ft.dropdown.Option(m) for m in MESES_NOMES],
            value=MESES_NOMES[mes_atual_idx],
            width=150
        )
        self.dd_mes_relatorio.on_select = lambda _: self.renderizar_registros()
        
        self.dd_ano_relatorio = ft.Dropdown(
            label="Ano",
            options=[ft.dropdown.Option(str(a)) for a in range(2024, 2031)],
            value="2026",
            width=100
        )
        self.dd_ano_relatorio.on_select = lambda _: self.renderizar_registros()

        self.txt_busca = ft.TextField(
            label="Buscar", 
            prefix_icon=ft.Icons.SEARCH, 
            expand=True, 
            on_change=lambda _: self.renderizar_registros()
        )

        self.dd_filtro_cat = ft.Dropdown(
            label="Filtrar Categoria",
            options=[ft.dropdown.Option("Todas")] + [ft.dropdown.Option(c) for c in CATEGORIAS],
            value="Todas",
            width=180
        )
        self.dd_filtro_cat.on_select = lambda _: self.renderizar_registros()

        self.dd_filtro_forma = ft.Dropdown(
            label="Filtrar Pagamento",
            options=[ft.dropdown.Option("Todas")] + [ft.dropdown.Option(f) for f in FORMAS_PAGAMENTO],
            value="Todas",
            width=180
        )
        self.dd_filtro_forma.on_select = lambda _: self.renderizar_registros()

        self.grafico_ui = ft.Column()
        self.lista_gastos_ui = ft.Column()

        # Cria UMA ÚNICA vez o snackbar e o diálogo de relatório, reaproveitados
        # em cada chamada (em vez de criar um novo componente a cada clique,
        # o que fazia a página acumular controles escondidos com o tempo)
        self.snack = ft.SnackBar(content=ft.Text(""), bgcolor=ft.Colors.GREEN_700)
        self.dlg_relatorio = ft.AlertDialog(title=ft.Text(""), content=ft.Container())

    async def carregar_renda_usuario(self):
        user = self.sessao_usuario.get("user")
        if not user:
            return
        try:
            res = supabase.table("profiles").select("renda_base").eq("id", user.id).execute()
            if res.data:
                renda = res.data[0].get("renda_base", 0)
                self.txt_renda.value = f"{float(renda):.2f}".replace(".", ",")
                self.page.update()
        except Exception as err:
            self.mostrar_snack(f"Erro ao carregar renda: {str(err)}", True)

    async def salvar_renda_usuario(self, e):
        user = self.sessao_usuario.get("user")
        if not user:
            return
        try:
            val_str = self.txt_renda.value.replace(".", "").replace(",", ".")
            val_float = float(val_str)
            supabase.table("profiles").upsert({"id": user.id, "renda_base": val_float}).execute()
            self.mostrar_snack("Renda atualizada com sucesso!")
            await self.carregar_registros()
        except Exception as err:
            self.mostrar_snack(f"Erro ao salvar renda: {str(err)}", True)

    async def atualizar_manual(self, e=None):
        self.mostrar_snack("🔄 Sincronizando com o servidor...", cor_bg=ft.Colors.BLUE_600)
        await self.carregar_registros()

    async def carregar_registros(self):
        user = self.sessao_usuario.get("user")
        if not user:
            return
        try:
            res = supabase.table("gastos").select("*").eq("user_id", user.id).order("created_at", desc=True).execute()
            self.registros_cache = res.data or []
            self.renderizar_registros()
        except Exception as err:
            self.mostrar_snack(f"Erro ao carregar lançamentos: {str(err)}", True)

    def atualizar_visibilidade_parcelas(self, e=None):
        """Mostra os campos de Parcelas/Vencimento só quando a forma de pagamento é Cartão de Crédito."""
        eh_credito = self.dd_forma.value == "Cartão de Crédito"
        self.dd_parc.visible = eh_credito
        self.dd_venc.visible = eh_credito
        self.dd_venc_mes.visible = eh_credito
        self.page.update()

    async def adicionar_registro(self, tipo):
        user = self.sessao_usuario.get("user")
        if not user or not self.txt_desc.value or not self.txt_val.value:
            self.mostrar_snack("Preencha descrição e valor!", True)
            return
        try:
            val_total = float(self.txt_val.value.replace(".", "").replace(",", "."))
            eh_credito = self.dd_forma.value == "Cartão de Crédito"
            num_parcelas = int(self.dd_parc.value.replace("x", "")) if eh_credito else 1
            venc_dia = self.dd_venc.value.replace("Dia ", "") if eh_credito else None

            valor_parcela = round(val_total / num_parcelas, 2)
            novos_registros = []

            if eh_credito:
                # Usa o Dia/Mês de Vencimento escolhidos como base da 1ª parcela
                dia_base = min(int(venc_dia), 28)
                mes_base = MESES_NOMES.index(self.dd_venc_mes.value) + 1
                ano_base = datetime.now().year
                # Se o mês escolhido já passou este ano, assume que é pro próximo ano
                if mes_base < datetime.now().month:
                    ano_base += 1
                dt_base = datetime(ano_base, mes_base, dia_base)
            else:
                dt_base = datetime.now()

            for i in range(num_parcelas):
                desc_final = self.txt_desc.value
                if num_parcelas > 1:
                    desc_final += f" ({i+1}/{num_parcelas})"

                mes_parc = dt_base.month + i
                ano_parc = dt_base.year + ((mes_parc - 1) // 12)
                mes_parc = ((mes_parc - 1) % 12) + 1

                data_registro = datetime(ano_parc, mes_parc, min(dt_base.day, 28)).isoformat()

                novos_registros.append({
                    "user_id": user.id,
                    "descricao": desc_final,
                    "valor": valor_parcela,
                    "categoria": self.dd_cat.value,
                    "forma_pagamento": self.dd_forma.value,
                    "tipo": tipo,
                    "data_vencimento": venc_dia,
                    "created_at": data_registro
                })

            supabase.table("gastos").insert(novos_registros).execute()
            self.txt_desc.value = ""
            self.txt_val.value = ""
            self.dd_parc.value = "1x"
            self.dd_venc_mes.value = MESES_NOMES[datetime.now().month - 1]
            self.mostrar_snack(f"{tipo} adicionada com sucesso ({num_parcelas}x)!")
            await self.carregar_registros()
        except Exception as err:
            self.mostrar_snack(f"Erro ao adicionar: {str(err)}", True)

    async def deletar_registro(self, reg_id):
        user = self.sessao_usuario.get("user")
        if not user:
            return
        try:
            supabase.table("gastos").delete().eq("id", reg_id).eq("user_id", user.id).execute()
            self.mostrar_snack("Lançamento excluído!")
            await self.carregar_registros()
        except Exception as err:
            self.mostrar_snack(f"Erro ao excluir: {str(err)}", True)

    def calcular_totais(self, filtrados):
        try:
            renda_base = float(self.txt_renda.value.replace(".", "").replace(",", "."))
        except Exception:
            renda_base = 0.0

        total_rec = sum(float(i.get("valor", 0)) for i in filtrados if i.get("tipo") == "Receita")
        total_desp = sum(float(i.get("valor", 0)) for i in filtrados if i.get("tipo") == "Despesa")
        saldo = (renda_base + total_rec) - total_desp

        self.lbl_receita.value = f"Receitas: R$ {total_rec:.2f}"
        self.lbl_despesa.value = f"Despesas: R$ {total_desp:.2f}"
        self.lbl_saldo.value = f"Saldo do Mês: R$ {saldo:.2f}"
        self.lbl_saldo.color = ft.Colors.GREEN_400 if saldo >= 0 else ft.Colors.RED_400

    def obter_cor_categoria(self, cat):
        cores = {
            "Alimentação": ft.Colors.CYAN_400,
            "Moradia": ft.Colors.RED_300,
            "Transporte": ft.Colors.BLUE_400,
            "Saúde & Bem-Estar": ft.Colors.PINK_300,
            "Educação": ft.Colors.INDIGO_300,
            "Lazer & Viagens": ft.Colors.GREEN_400,
            "Assinaturas & Serviços": ft.Colors.ORANGE_400,
            "Compras & Vestuário": ft.Colors.YELLOW_400,
            "Dívidas & Empréstimos": ft.Colors.PURPLE_300,
            "Investimentos & Reserva": ft.Colors.TEAL_400,
            "Rendimento & Salário": ft.Colors.GREEN_400,
            "Outros": ft.Colors.AMBER_400,
        }
        return cores.get(cat, ft.Colors.GREY_400)

    def atualizar_grafico(self, filtrados):
        self.grafico_ui.controls.clear()

        # Separa receitas e despesas ANTES de calcular as porcentagens,
        # pra não misturar "dinheiro entrando" com "dinheiro saindo" no mesmo gráfico
        despesas = [i for i in filtrados if i.get("tipo") == "Despesa"]
        receitas = [i for i in filtrados if i.get("tipo") == "Receita"]

        def montar_bloco(titulo, itens):
            totais = {}
            total_geral = 0.0
            for item in itens:
                cat = item.get("categoria", "Outros")
                try:
                    val = float(item.get("valor", 0))
                except (ValueError, TypeError):
                    val = 0.0
                totais[cat] = totais.get(cat, 0.0) + val
                total_geral += val

            if total_geral <= 0:
                return None

            bloco = [ft.Text(titulo, weight=ft.FontWeight.BOLD, size=16)]
            for cat, val in totais.items():
                if val <= 0:
                    continue
                pct = max(0.0, min(1.0, val / total_geral))
                cor_cat = self.obter_cor_categoria(cat)
                bloco.append(
                    ft.Column([
                        ft.Row([
                            ft.Text(cat, weight=ft.FontWeight.BOLD),
                            ft.Text(f"R$ {val:.2f} ({pct*100:.1f}%)", color=cor_cat)
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        ft.ProgressBar(value=pct, color=cor_cat, height=8)
                    ], spacing=2)
                )
            return bloco

        bloco_despesas = montar_bloco("📊 Distribuição de Despesas Por Categoria", despesas)
        bloco_receitas = montar_bloco("💰 Distribuição de Receitas Por Categoria", receitas)

        if bloco_despesas:
            self.grafico_ui.controls.extend(bloco_despesas)
        if bloco_receitas:
            if bloco_despesas:
                self.grafico_ui.controls.append(ft.Divider(height=15))
            self.grafico_ui.controls.extend(bloco_receitas)

    def renderizar_registros(self):
        self.lista_gastos_ui.controls.clear()
        
        mes_nome_sel = self.dd_mes_relatorio.value
        mes_num_sel = str(MESES_NOMES.index(mes_nome_sel) + 1).zfill(2) if mes_nome_sel in MESES_NOMES else "09"
        ano_sel = self.dd_ano_relatorio.value
        busca_query = self.txt_busca.value.strip().lower() if self.txt_busca.value else ""
        filtro_cat = self.dd_filtro_cat.value
        filtro_forma = self.dd_filtro_forma.value

        filtrados = []
        for item in self.registros_cache:
            m_ef, a_ef, _ = obter_mes_ano_efetivo(item)
            if m_ef != mes_num_sel or a_ef != ano_sel:
                continue
            desc = str(item.get("descricao", "")).lower()
            if busca_query and busca_query not in desc:
                continue
            cat = item.get("categoria", "Outros")
            if filtro_cat != "Todas" and cat != filtro_cat:
                continue
            forma = item.get("forma_pagamento", "Débito / Pix")
            if filtro_forma != "Todas" and forma != filtro_forma:
                continue
            filtrados.append(item)

        self.calcular_totais(filtrados)

        try:
            self.atualizar_grafico(filtrados)
        except Exception as err:
            self.grafico_ui.controls.clear()
            self.grafico_ui.controls.append(
                ft.Text(f"⚠️ Aviso ao gerar gráfico: {str(err)}", color=ft.Colors.AMBER_400, size=12)
            )

        if not filtrados:
            self.lista_gastos_ui.controls.append(ft.Text("Nenhum lançamento encontrado para os filtros selecionados.", color=ft.Colors.GREY_500))
        else:
            for item in filtrados:
                reg_id = item.get("id")
                desc = item.get("descricao", "")
                cat = item.get("categoria", "Outros")
                forma = item.get("forma_pagamento", "Débito / Pix")
                tipo = item.get("tipo", "Despesa")
                
                try:
                    val = float(item.get("valor", 0))
                except (ValueError, TypeError):
                    val = 0.0

                venc = item.get("data_vencimento")

                detalles_str = f"{cat} • {forma}"
                if venc:
                    detalles_str += f" • Vencimento: Dia {venc}"

                is_receita = tipo == "Receita"
                cor_val = ft.Colors.GREEN_400 if is_receita else ft.Colors.RED_400
                sinal = "+" if is_receita else "-"

                card = ft.Container(
                    content=ft.Row([
                        ft.Column([
                            ft.Text(desc, weight=ft.FontWeight.BOLD, size=14),
                            ft.Text(detalles_str, size=12, color=ft.Colors.GREY_400),
                        ], expand=True),
                        ft.Text(f"{sinal}R$ {val:.2f}", color=cor_val, weight=ft.FontWeight.BOLD, size=14),
                        ft.IconButton(
                            icon=ft.Icons.DELETE_OUTLINE,
                            icon_color=ft.Colors.RED_400,
                            tooltip="Excluir",
                            on_click=lambda _, r_id=reg_id: asyncio.create_task(self.deletar_registro(r_id))
                        )
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    padding=10, bgcolor=ft.Colors.GREY_900, border_radius=8, margin=ft.Margin(0, 2, 0, 2)
                )
                self.lista_gastos_ui.controls.append(card)

        self.page.update()

    def acao_exportar_csv(self, e):
        mes_nome_sel = self.dd_mes_relatorio.value
        mes_num_sel = str(MESES_NOMES.index(mes_nome_sel) + 1).zfill(2) if mes_nome_sel in MESES_NOMES else "09"
        sucesso, msg, url_download = exportar_para_csv(self.registros_cache, mes_num_sel, self.dd_ano_relatorio.value)
        self.mostrar_snack(msg, not sucesso)
        if sucesso and url_download:
            # Abre o link numa nova aba, o que faz o navegador baixar o CSV
            self.page.launch_url(url_download)

    def abrir_relatorio_mensal(self, e):
        mes_nome_sel = self.dd_mes_relatorio.value
        mes_num_sel = str(MESES_NOMES.index(mes_nome_sel) + 1).zfill(2) if mes_nome_sel in MESES_NOMES else "09"
        ano_sel = self.dd_ano_relatorio.value

        try:
            renda_base = float(self.txt_renda.value.replace(".", "").replace(",", "."))
        except Exception:
            renda_base = 0.0

        filtrados = [
            i for i in self.registros_cache 
            if obter_mes_ano_efetivo(i)[0] == mes_num_sel and obter_mes_ano_efetivo(i)[1] == ano_sel
        ]

        total_rec = sum(float(i.get("valor", 0)) for i in filtrados if i.get("tipo") == "Receita")
        total_desp = sum(float(i.get("valor", 0)) for i in filtrados if i.get("tipo") == "Despesa")
        resultado_final = (renda_base + total_rec) - total_desp

        eh_superavit = resultado_final >= 0
        cor_resultado = ft.Colors.GREEN_400 if eh_superavit else ft.Colors.RED_400
        texto_resultado = f"SUPERÁVIT DE R$ {resultado_final:.2f}" if eh_superavit else f"DÉFICIT DE R$ {abs(resultado_final):.2f}"

        card_resultado = ft.Container(
            content=ft.Column([
                ft.Text("RESULTADO FINAL", size=10, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_400),
                ft.Row([
                    ft.Icon(ft.Icons.CIRCLE, color=cor_resultado, size=16),
                    ft.Text(texto_resultado, size=16, weight=ft.FontWeight.BOLD, color=cor_resultado)
                ])
            ]),
            padding=12,
            bgcolor=ft.Colors.GREY_900,
            border_radius=8
        )

        resumo_valores = ft.Row([
            ft.Text(f"Renda: R$ {renda_base:.2f}", color=ft.Colors.WHITE, size=12),
            ft.Text(f"Receitas: R$ {total_rec:.2f}", color=ft.Colors.GREEN_400, size=12),
            ft.Text(f"Despesas: R$ {total_desp:.2f}", color=ft.Colors.RED_400, size=12),
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

        lista_itens = ft.Column(spacing=6, scroll=ft.ScrollMode.AUTO, height=200)

        for item in filtrados:
            desc = item.get("descricao", "")
            forma = item.get("forma_pagamento", "Débito / Pix")
            tipo = item.get("tipo", "Despesa")
            val = float(item.get("valor", 0))
            
            dt_raw = item.get("created_at", "")
            try:
                dt_obj = datetime.fromisoformat(dt_raw.replace("Z", "+00:00"))
                data_str = dt_obj.strftime("%d/%m")
            except Exception:
                data_str = "01/09"

            is_rec = tipo == "Receita"
            cor_val = ft.Colors.GREEN_400 if is_rec else ft.Colors.RED_400
            sinal = "+" if is_rec else "-"

            item_row = ft.Container(
                content=ft.Row([
                    ft.Text(f"{data_str} - {desc} ({forma})", color=ft.Colors.WHITE, size=12, expand=True),
                    ft.Text(f"{sinal}R$ {val:.2f}", color=cor_val, weight=ft.FontWeight.BOLD, size=12)
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                padding=8,
                bgcolor=ft.Colors.GREY_900,
                border_radius=6
            )
            lista_itens.controls.append(item_row)

        # Reaproveita o mesmo AlertDialog, só atualizando título/conteúdo
        self.dlg_relatorio.title = ft.Row([
            ft.Text("📋", size=20),
            ft.Text(f"Relatório Mensal: {mes_num_sel}/{ano_sel}", weight=ft.FontWeight.BOLD, size=18)
        ])
        self.dlg_relatorio.content = ft.Container(
            content=ft.Column([
                card_resultado,
                ft.Divider(height=10),
                resumo_valores,
                ft.Divider(height=10),
                ft.Text("Lançamentos do Mês:", weight=ft.FontWeight.BOLD, size=14),
                lista_itens
            ], tight=True),
            width=400
        )
        self.dlg_relatorio.actions = [ft.TextButton("Fechar", on_click=lambda _: self.fechar_dialogo(self.dlg_relatorio))]
        self.dlg_relatorio.open = True
        self.page.update()

    def fechar_dialogo(self, dlg):
        dlg.open = False
        self.page.update()

    def mostrar_snack(self, msg, e_erro=False, cor_bg=None):
        if cor_bg is None:
            cor_bg = ft.Colors.RED_700 if e_erro else ft.Colors.GREEN_700

        self.snack.content = ft.Row([
            ft.Icon(ft.Icons.SYNC, color=ft.Colors.WHITE) if "Sincronizando" in msg else ft.Container(),
            ft.Text(msg, color=ft.Colors.WHITE)
        ])
        self.snack.bgcolor = cor_bg
        self.snack.open = True
        self.page.update()

    async def inicializar(self):
        self.page.controls.clear()

        user = self.sessao_usuario.get("user")
        email_str = user.email if user else ""

        header = ft.Row([
            ft.Column([
                ft.Text("Perrut - Painel Financeiro", size=22, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_400),
                ft.Text(f"Usuário: {email_str}", color=ft.Colors.GREY_400, size=12),
            ]),
            ft.Row([
                ft.IconButton(
                    icon=ft.Icons.REFRESH, 
                    icon_color=ft.Colors.GREEN_400, 
                    tooltip="Atualizar", 
                    on_click=lambda e: asyncio.create_task(self.atualizar_manual(e))
                ),
                ft.IconButton(
                    icon=ft.Icons.LOGOUT, 
                    tooltip="Sair", 
                    icon_color=ft.Colors.RED_400, 
                    on_click=lambda _: asyncio.create_task(self.fechar_sessao_cb())
                ),
            ])
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

        card_renda = ft.Container(
            content=ft.Row([
                self.txt_renda,
                ft.ElevatedButton("Salvar Renda", bgcolor=ft.Colors.GREEN_700, color=ft.Colors.WHITE, on_click=lambda e: asyncio.create_task(self.salvar_renda_usuario(e)))
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=10, bgcolor=ft.Colors.GREY_900, border_radius=8
        )

        card_resumo = ft.Container(
            content=ft.Column([
                self.lbl_saldo,
                ft.Row([self.lbl_receita, self.lbl_despesa], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
            ]),
            padding=15, bgcolor=ft.Colors.GREY_900, border_radius=8
        )

        form_lancamento = ft.Container(
            content=ft.Column([
                ft.Text("➕ Novo Lançamento", size=16, weight=ft.FontWeight.BOLD),
                self.txt_desc,
                ft.Row([self.txt_val, self.dd_cat, self.dd_forma], wrap=True),
                ft.Row([self.dd_parc, self.dd_venc, self.dd_venc_mes], wrap=True),
                ft.Row([
                    ft.ElevatedButton("Adicionar Receita", icon=ft.Icons.ADD_CIRCLE_OUTLINE, bgcolor=ft.Colors.GREEN_700, color=ft.Colors.WHITE, on_click=lambda _: asyncio.create_task(self.adicionar_registro("Receita"))),
                    ft.ElevatedButton("Adicionar Despesa", icon=ft.Icons.REMOVE_CIRCLE_OUTLINE, bgcolor=ft.Colors.RED_700, color=ft.Colors.WHITE, on_click=lambda _: asyncio.create_task(self.adicionar_registro("Despesa"))),
                ], alignment=ft.MainAxisAlignment.END)
            ]),
            padding=15, bgcolor=ft.Colors.GREY_900, border_radius=8
        )

        barra_filtros = ft.Row([
            self.dd_mes_relatorio,
            self.dd_ano_relatorio,
            ft.ElevatedButton("Relatório", icon=ft.Icons.ASSESSMENT, on_click=self.abrir_relatorio_mensal),
            ft.ElevatedButton("Exportar CSV", icon=ft.Icons.DOWNLOAD, on_click=self.acao_exportar_csv),
        ], wrap=True)

        busca_e_categoria = ft.Row([self.txt_busca, self.dd_filtro_cat, self.dd_filtro_forma])

        self.page.add(
            header,
            card_renda,
            card_resumo,
            form_lancamento,
            ft.Divider(height=20),
            barra_filtros,
            busca_e_categoria,
            self.grafico_ui,
            ft.Divider(height=10),
            ft.Text("📋 Registros do Mês", weight=ft.FontWeight.BOLD, size=16),
            self.lista_gastos_ui
        )

        # Registra o snackbar e o diálogo de relatório uma única vez no overlay da página
        if self.snack not in self.page.overlay:
            self.page.overlay.append(self.snack)
        if self.dlg_relatorio not in self.page.overlay:
            self.page.overlay.append(self.dlg_relatorio)

        await self.carregar_renda_usuario()
        await self.carregar_registros()