import csv
import json
import re
import customtkinter as ctk
from tkinter import messagebox
import matplotlib.pyplot as plt

# Configuração de tema do CustomTkinter
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

ARQUIVO = "dados_financeiros.json"
CATEGORIAS = ["Alimentação", "Moradia", "Transporte", "Lazer", "Saúde", "Outros"]

# --- LÓGICA DE DADOS ---
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
class AppFinancas(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Controle Financeiro Pessoal")
        self.geometry("700x680")
        self.resizable(False, False)
        
        self.dados = carregar_dados()

        # 1. RESUMO FINANCEIRO
        frame_topo = ctk.CTkFrame(self)
        frame_topo.pack(fill="x", padx=15, pady=10)

        ctk.CTkLabel(frame_topo, text="Renda Mensal (R$):", font=("Roboto", 13, "bold")).grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.entry_renda = ctk.CTkEntry(frame_topo, width=120)
        self.entry_renda.grid(row=0, column=1, padx=5, pady=10)
        self.entry_renda.insert(0, f"{self.dados['renda']:.2f}")

        btn_renda = ctk.CTkButton(frame_topo, text="Atualizar Renda", width=120, command=self.atualizar_renda)
        btn_renda.grid(row=0, column=2, padx=5, pady=10)

        btn_grafico = ctk.CTkButton(frame_topo, text="📊 Ver Gráfico", width=120, fg_color="#2FA572", hover_color="#1E6B49", command=self.exibir_grafico)
        btn_grafico.grid(row=0, column=3, padx=10, pady=10)

        self.lbl_total_gasto = ctk.CTkLabel(frame_topo, text="Total Gasto: R$ 0.00", font=("Roboto", 14, "bold"))
        self.lbl_total_gasto.grid(row=1, column=0, columnspan=2, padx=10, pady=(0, 10), sticky="w")

        self.lbl_saldo = ctk.CTkLabel(frame_topo, text="Saldo: R$ 0.00", font=("Roboto", 14, "bold"))
        self.lbl_saldo.grid(row=1, column=2, columnspan=2, padx=10, pady=(0, 10), sticky="e")

        # 2. ADICIONAR GASTO
        frame_cadastro = ctk.CTkFrame(self)
        frame_cadastro.pack(fill="x", padx=15, pady=5)

        ctk.CTkLabel(frame_cadastro, text="Descrição:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.entry_desc = ctk.CTkEntry(frame_cadastro, width=180)
        self.entry_desc.grid(row=0, column=1, padx=5, pady=5)

        ctk.CTkLabel(frame_cadastro, text="Valor (R$):").grid(row=0, column=2, padx=10, pady=5, sticky="w")
        self.entry_valor = ctk.CTkEntry(frame_cadastro, width=100)
        self.entry_valor.grid(row=0, column=3, padx=5, pady=5)

        ctk.CTkLabel(frame_cadastro, text="Categoria:").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.combo_cat = ctk.CTkOptionMenu(frame_cadastro, values=CATEGORIAS, width=180)
        self.combo_cat.grid(row=1, column=1, padx=5, pady=5)

        btn_add = ctk.CTkButton(frame_cadastro, text="➕ Adicionar Gasto", command=self.adicionar_gasto)
        btn_add.grid(row=1, column=2, columnspan=2, padx=5, pady=10, sticky="ew")

        # 3. FILTROS E BUSCA
        frame_filtro = ctk.CTkFrame(self, fg_color="transparent")
        frame_filtro.pack(fill="x", padx=15, pady=5)

        ctk.CTkLabel(frame_filtro, text="🔎 Buscar:").grid(row=0, column=0, sticky="w")
        self.entry_busca = ctk.CTkEntry(frame_filtro, width=180)
        self.entry_busca.grid(row=0, column=1, padx=5)
        self.entry_busca.bind("<KeyRelease>", lambda event: self.atualizar_tabela())

        ctk.CTkLabel(frame_filtro, text="Filtrar Categoria:").grid(row=0, column=2, padx=(20, 5), sticky="w")
        self.combo_filtro_cat = ctk.CTkOptionMenu(frame_filtro, values=["Todas"] + CATEGORIAS, command=lambda _: self.atualizar_tabela(), width=140)
        self.combo_filtro_cat.grid(row=0, column=3, padx=5)

        # 4. LISTA DE GASTOS
        self.scroll_frame = ctk.CTkScrollableFrame(self, label_text="Lista de Gastos", height=220)
        self.scroll_frame.pack(fill="both", expand=True, padx=15, pady=5)

        # 5. BOTÕES INFERIORES
        frame_botoes = ctk.CTkFrame(self, fg_color="transparent")
        frame_botoes.pack(fill="x", padx=15, pady=10)

        btn_exportar = ctk.CTkButton(frame_botoes, text="📁 Exportar CSV", fg_color="#1F6AA5", command=self.exportar_csv)
        btn_exportar.pack(side="left")

        btn_remover_tudo = ctk.CTkButton(frame_botoes, text="🗑️ Limpar Todos", fg_color="#D32F2F", hover_color="#9A0007", command=self.limpar_todos_gastos)
        btn_remover_tudo.pack(side="right")

        self.atualizar_tela()

    def atualizar_renda(self):
        try:
            val = limpar_e_converter_numero(self.entry_renda.get())
            self.dados["renda"] = val
            salvar_dados(self.dados)
            self.atualizar_tela()
            messagebox.showinfo("Sucesso", "Renda atualizada!")
        except ValueError:
            messagebox.showerror("Erro", "Digite um valor válido de renda.")

    def adicionar_gasto(self):
        desc = self.entry_desc.get().strip()
        valor_raw = self.entry_valor.get().strip()
        cat = self.combo_cat.get()

        if not desc:
            messagebox.showwarning("Atenção", "Preencha a descrição.")
            return

        try:
            valor = limpar_e_converter_numero(valor_raw)
            self.dados["gastos"].append({"descricao": desc, "valor": valor, "categoria": cat})
            salvar_dados(self.dados)

            self.entry_desc.delete(0, 'end')
            self.entry_valor.delete(0, 'end')

            self.atualizar_tela()
        except ValueError:
            messagebox.showerror("Erro", "Digite um valor válido.")

    def remover_gasto_individual(self, item_alvo):
        self.dados["gastos"].remove(item_alvo)
        salvar_dados(self.dados)
        self.atualizar_tela()

    def limpar_todos_gastos(self):
        if not self.dados["gastos"]:
            return
        if messagebox.askyesno("Confirmar", "Deseja realmente apagar todos os gastos cadastrados?"):
            self.dados["gastos"] = []
            salvar_dados(self.dados)
            self.atualizar_tela()

    def exportar_csv(self):
        if not self.dados["gastos"]:
            messagebox.showwarning("Atenção", "Não há gastos para exportar.")
            return

        nome_arquivo = "relatorio_financeiro.csv"
        try:
            with open(nome_arquivo, mode="w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f, delimiter=";")
                writer.writerow(["Descrição", "Valor (R$)", "Categoria"])
                for item in self.dados["gastos"]:
                    cat = item.get("categoria", "Outros")
                    writer.writerow([item["descricao"], f"{item['valor']:.2f}", cat])

            messagebox.showinfo("Sucesso", f"Relatório exportado com sucesso!\nArquivo: {nome_arquivo}")
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao exportar: {e}")

    def exibir_grafico(self):
        if not self.dados["gastos"]:
            messagebox.showwarning("Atenção", "Sem gastos para exibir gráfico.")
            return

        totais_cat = {}
        for g in self.dados["gastos"]:
            c = g.get("categoria", "Outros")
            totais_cat[c] = totais_cat.get(c, 0.0) + g["valor"]

        plt.figure(figsize=(6, 5))
        plt.pie(totais_cat.values(), labels=totais_cat.keys(), autopct='%1.1f%%', startangle=140)
        plt.title("Distribuição de Gastos por Categoria")
        plt.tight_layout()
        plt.show()

    def atualizar_tabela(self):
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        termo_busca = self.entry_busca.get().lower().strip()
        cat_filtro = self.combo_filtro_cat.get()

        for item in self.dados["gastos"]:
            cat = item.get("categoria", "Outros")
            desc = item["descricao"]

            if (cat_filtro == "Todas" or cat == cat_filtro) and (termo_busca in desc.lower()):
                row_frame = ctk.CTkFrame(self.scroll_frame)
                row_frame.pack(fill="x", pady=2, padx=5)

                ctk.CTkLabel(row_frame, text=desc, width=220, anchor="w").pack(side="left", padx=10)
                ctk.CTkLabel(row_frame, text=f"R$ {item['valor']:.2f}", width=120, anchor="w").pack(side="left", padx=5)
                ctk.CTkLabel(row_frame, text=cat, width=120, anchor="w").pack(side="left", padx=5)

                btn_del = ctk.CTkButton(row_frame, text="❌", width=30, fg_color="#D32F2F", hover_color="#9A0007", command=lambda i=item: self.remover_gasto_individual(i))
                btn_del.pack(side="right", padx=5)

    def atualizar_tela(self):
        self.atualizar_tabela()

        total = sum(g["valor"] for g in self.dados["gastos"])
        saldo = self.dados["renda"] - total
        
        self.lbl_total_gasto.configure(text=f"Total Gasto: R$ {total:.2f}")
        
        if saldo < 0:
            self.lbl_saldo.configure(text=f"Saldo: R$ {saldo:.2f}", text_color="#FF5555")
        else:
            self.lbl_saldo.configure(text=f"Saldo: R$ {saldo:.2f}", text_color="#50FA7B")

# --- EXECUÇÃO DO APP ---
if __name__ == "__main__":
    app = AppFinancas()
    app.mainloop()