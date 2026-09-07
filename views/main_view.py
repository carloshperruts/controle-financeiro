import flet as ft
import json
import re
import asyncio
from datetime import datetime
from config.supabase_client import CATEGORIAS, supabase
from utils.helpers import (
    buscar_registros_usuario,
    deletar_registro_banco,
    buscar_renda_usuario,
    salvar_renda_usuario,
    salvar_novo_registro,
    exportar_relatorio_csv,
    obter_mes_ano_efetivo,
)

# Definições globais de apoio ao código legado
ARQUIVO = "dados_financeiros.json"

# Nulifica chamadas antigas de ctk/messagebox para não quebrar a interface Flet
class DummyCTK:
    def __getattr__(self, name): return lambda *a, **k: None
ctk = DummyCTK()
messagebox = DummyCTK()

# --- LÓGICA DE DADOS ---
def carregar_dados():
    try:
        with open(ARQUIVO, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"renda": 0.0, "gastos": []}

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

# --- INTERFACE GRÁFICA (CUSTOMTKINTER) ---
async def renderizar_tela_principal(page: ft.Page, user_id: str, usuario_nome: str, ao_deslogar):
    """Renderiza a interface do Perrut - Painel Financeiro usando Flet."""
    page.title = f"Perrut - Painel Financeiro"
    page.bgcolor = "#0D1117"
    page.scroll = ft.ScrollMode.AUTO

    # --- ESTADOS DO PAINEL ---
    mes_selecionado = str(datetime.now().month).zfill(2)
    ano_selecionado = str(datetime.now().year)

    # --- COMPONENTES VISUAIS ---
    campo_renda = ft.TextField(
        label="Renda Base (R$)",
        value="0,00",
        width=200,
        border_color="#30363D",
        color="#FFFFFF"
    )

    lbl_saldo = ft.Text("Saldo do Mês: R$ 0,00", size=18, weight=ft.FontWeight.BOLD, color="#FF5555")
    lbl_receitas = ft.Text("Receitas: R$ 0,00", size=14, color="#00FF66", weight=ft.FontWeight.BOLD)
    lbl_despesas = ft.Text("Despesas: R$ 0,00", size=14, color="#FF5555", weight=ft.FontWeight.BOLD)

    # Formulário de Lançamento
    txt_desc = ft.TextField(label="Descrição", border_color="#30363D", color="#FFFFFF", expand=True)
    txt_valor = ft.TextField(label="Valor Total (R$)", border_color="#30363D", color="#FFFFFF", width=150)
    dd_categoria = ft.Dropdown(
        label="Categoria",
        options=[ft.dropdown.Option(c) for c in CATEGORIAS],
        value="Outros",
        border_color="#30363D",
        width=200
    )
    dd_pagamento = ft.Dropdown(
        label="Pagamento / Origem",
        options=[ft.dropdown.Option("Débito / Pix"), ft.dropdown.Option("Crédito")],
        value="Débito / Pix",
        border_color="#30363D",
        width=200
    )

    coluna_categorias = ft.Column(spacing=10)
    coluna_registros = ft.Column(spacing=10)

    # --- FUNÇÃO DE CARREGAMENTO DE DADOS ---
    async def carregar_painel():
        registros = buscar_registros_usuario(user_id)
        renda = buscar_renda_usuario(user_id)
        campo_renda.value = f"{renda:.2f}"

        m_efetivo, a_efetivo = obter_mes_ano_efetivo(mes_selecionado, ano_selecionado)
        
        tot_rec = sum(float(r["valor"]) for r in registros if r.get("tipo") == "Receita" and r.get("mes") == m_efetivo and str(r.get("ano")) == a_efetivo)
        tot_desp = sum(float(r["valor"]) for r in registros if r.get("tipo") != "Receita" and r.get("mes") == m_efetivo and str(r.get("ano")) == a_efetivo)
        
        saldo = renda + tot_rec - tot_desp

        lbl_saldo.value = f"Saldo do Mês: R$ {saldo:.2f}"
        lbl_saldo.color = "#00FF66" if saldo >= 0 else "#FF5555"
        lbl_receitas.value = f"Receitas: R$ {tot_rec:.2f}"
        lbl_despesas.value = f"Despesas: R$ {tot_desp:.2f}"

        # Atualiza Lista de Lançamentos
        coluna_registros.controls.clear()
        for reg in registros:
            if reg.get("mes") == m_efetivo and str(reg.get("ano")) == a_efetivo:
                val = float(reg["valor"])
                is_rec = reg.get("tipo") == "Receita"
                cor_txt = "#00FF66" if is_rec else "#FF5555"
                sinal = "+" if is_rec else "-"

                def criar_acao_deletar(r_id):
                    def deletar(e):
                        deletar_registro_banco(r_id)
                        asyncio.create_task(carregar_painel())
                    return deletar

                card = ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Column(
                                controls=[
                                    ft.Text(reg.get("descricao", ""), weight=ft.FontWeight.BOLD, color="#FFFFFF"),
                                    ft.Text(f"{reg.get('categoria', '')} • {reg.get('forma_pagamento', '')}", size=12, color="#8B949E")
                                ],
                                expand=True
                            ),
                            ft.Text(f"{sinal}R$ {val:.2f}", color=cor_txt, weight=ft.FontWeight.BOLD),
                            ft.IconButton(ft.Icons.DELETE_OUTLINE, icon_color="#FF5555", on_click=criar_acao_deletar(reg["id"]))
                        ]
                    ),
                    padding=15,
                    bgcolor="#161B22",
                    border_radius=8,
                    border=ft.Border.all(1, "#30363D")
                )
                coluna_registros.controls.append(card)

        page.update()

    async def salvar_renda_evt(e):
        try:
            val = float(campo_renda.value.replace(",", "."))
            salvar_renda_usuario(user_id, val)
            await carregar_painel()
        except ValueError:
            pass

    async def adicionar_registro(tipo):
        try:
            val = float(txt_valor.value.replace(",", "."))
            if not txt_desc.value.strip():
                return
            salvar_novo_registro(
                user_id=user_id,
                descricao=txt_desc.value.strip(),
                valor=val,
                categoria=dd_categoria.value,
                forma_pagamento=dd_pagamento.value,
                tipo=tipo,
                mes=mes_selecionado,
                ano=ano_selecionado
            )
            txt_desc.value = ""
            txt_valor.value = ""
            await carregar_painel()
        except ValueError:
            pass

    # Header da aplicação
    header = ft.Row(
        controls=[
            ft.Text("Perrut - Painel Financeiro", size=22, weight=ft.FontWeight.BOLD, color="#00FF66", expand=True),
            ft.IconButton(ft.Icons.REFRESH, icon_color="#00FF66", on_click=lambda e: asyncio.create_task(carregar_painel())),
            ft.IconButton(ft.Icons.LOGOUT, icon_color="#FF5555", on_click=lambda e: ao_deslogar())
        ]
    )

    card_renda = ft.Container(
        content=ft.Row(
            controls=[
                campo_renda,
                ft.ElevatedButton("Salvar Renda", bgcolor="#00FF66", color="#0D1117", on_click=salvar_renda_evt)
            ]
        ),
        padding=15, bgcolor="#161B22", border_radius=8, border=ft.Border.all(1, "#30363D")
    )

    card_saldo = ft.Container(
        content=ft.Column(
            controls=[
                lbl_saldo,
                ft.Row(controls=[lbl_receitas, lbl_despesas], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
            ]
        ),
        padding=15, bgcolor="#161B22", border_radius=8, border=ft.Border.all(1, "#30363D")
    )

    card_novo = ft.Container(
        content=ft.Column(
            controls=[
                ft.Text("+ Novo Lançamento", size=16, weight=ft.FontWeight.BOLD, color="#FFFFFF"),
                txt_desc,
                ft.Row(controls=[txt_valor, dd_categoria, dd_pagamento]),
                ft.Row(
                    controls=[
                        ft.ElevatedButton("Adicionar Receita", bgcolor="#00FF66", color="#0D1117", on_click=lambda e: asyncio.create_task(adicionar_registro("Receita"))),
                        ft.ElevatedButton("Adicionar Despesa", bgcolor="#FF5555", color="#FFFFFF", on_click=lambda e: asyncio.create_task(adicionar_registro("Gasto")))
                    ],
                    alignment=ft.MainAxisAlignment.END
                )
            ]
        ),
        padding=20, bgcolor="#161B22", border_radius=8, border=ft.Border.all(1, "#30363D")
    )

    page.views.clear()
    page.views.append(
        ft.View(
            route="/main",
            controls=[
                ft.Column(
                    controls=[
                        header,
                        ft.Text(f"Usuário: {usuario_nome}", size=12, color="#8B949E"),
                        card_renda,
                        card_saldo,
                        card_novo,
                        ft.Text("📋 Registros do Mês", size=16, weight=ft.FontWeight.BOLD, color="#FFFFFF"),
                        coluna_registros
                    ],
                    spacing=15
                )
            ],
            padding=20
        )
    )
    page.update()
    await carregar_painel()