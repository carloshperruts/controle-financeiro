import flet as ft
import random
import asyncio

# Caracteres usados na "chuva" (mistura de binário, símbolos e a marca do app)
CHARS = "01$%&*+-=<>#@PERRUT"


def criar_fundo_matrix_animado(page: ft.Page, num_colunas: int = 20, altura_trilha: int = 15):
    """
    Cria o efeito clássico de "chuva digital" (estilo Matrix): colunas de
    caracteres caem continuamente, cada uma com uma "cabeça" bem clara na
    frente e um rastro verde que vai apagando conforme se afasta dela.

    Em telas estreitas (celular/tablet), usa menos colunas para não
    espremer/sobrepor os caracteres — é isso que causava o efeito de
    "letras embaralhadas" no fundo em telas pequenas.

    Cancela qualquer animação anterior ainda rodando em segundo plano,
    evitando que várias animações se acumulem ao trocar de tela (login/cadastro/etc.).
    """
    tarefa_anterior = getattr(page, "_matrix_bg_task", None)
    if tarefa_anterior:
        tarefa_anterior.cancel()

    try:
        largura_tela = page.width or 1200
    except Exception:
        largura_tela = 1200
    if largura_tela < 500:
        num_colunas = 8
    elif largura_tela < 900:
        num_colunas = 14

    colunas = []      # uma lista de células (ft.Text) por coluna
    posicoes = []      # posição atual da "cabeça" de cada coluna (pode ser negativa = ainda não entrou na tela)
    velocidades = []   # velocidade de queda de cada coluna (varia pra não ficarem todas sincronizadas)

    for _ in range(num_colunas):
        celulas = [
            ft.Text(
                value=" ",
                size=13,
                weight=ft.FontWeight.BOLD,
                font_family="Courier New",
                color="#00FF41",
                opacity=0,
            )
            for _ in range(altura_trilha)
        ]
        colunas.append(celulas)
        # Começa "atrasada" (fora da tela, acima do topo), pra cada coluna
        # entrar em um momento diferente e a chuva parecer mais orgânica
        posicoes.append(random.uniform(-altura_trilha * 2, 0))
        velocidades.append(random.uniform(0.5, 1.3))

    rain_row = ft.Row(
        controls=[
            ft.Column(controls=celulas, spacing=2, alignment=ft.MainAxisAlignment.START)
            for celulas in colunas
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        expand=True,
        spacing=4,
    )

    def renderizar_coluna(celulas, head):
        for i, celula in enumerate(celulas):
            dist = head - i
            if dist < 0 or dist > altura_trilha:
                # Ainda não chegou nessa célula, ou o rastro já passou por completo: apagada
                celula.opacity = 0
            elif dist < 1:
                # A "cabeça" do rastro: bem clara/brilhante, e pisca trocando de caractere
                if random.random() < 0.5:
                    celula.value = random.choice(CHARS)
                celula.color = "#D6FFE0"
                celula.opacity = 1
            else:
                # Corpo do rastro: verde, apagando gradualmente quanto mais longe da cabeça
                if celula.value == " " or random.random() < 0.05:
                    celula.value = random.choice(CHARS)
                celula.color = "#00FF41"
                celula.opacity = max(0.05, 1 - (dist / altura_trilha))

    async def animar():
        try:
            while True:
                for idx, celulas in enumerate(colunas):
                    posicoes[idx] += velocidades[idx]
                    # Quando a coluna sai totalmente pela parte de baixo, reinicia
                    # em uma posição/velocidade aleatória (efeito contínuo e variado)
                    if posicoes[idx] > altura_trilha * 2:
                        posicoes[idx] = random.uniform(-altura_trilha * 2, -1)
                        velocidades[idx] = random.uniform(0.5, 1.3)
                    renderizar_coluna(celulas, posicoes[idx])
                page.update()
                await asyncio.sleep(0.08)
        except Exception:
            pass

    # Guarda a referência da tarefa na própria página, pra poder cancelá-la
    # da próxima vez que essa função for chamada
    page._matrix_bg_task = asyncio.create_task(animar())
    return rain_row