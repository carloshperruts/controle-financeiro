import flet as ft
import random
import asyncio

def criar_fundo_matrix_animado(page: ft.Page):
    """Cria a animação de fundo estilo Matrix em código caindo."""
    chars = "01PERRUT$#@%&*+-="
    num_columns = 16
    column_controls = []

    for _ in range(num_columns):
        txt = ft.Text(
            value="\n".join(random.choices(chars, k=15)),
            size=12,
            color="#00FF66",
            opacity=random.uniform(0.1, 0.35),
            weight=ft.FontWeight.BOLD,
            font_family="Courier"
        )
        column_controls.append(txt)

    rain_row = ft.Row(
        controls=column_controls,
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        expand=True
    )

    async def animar():
        while True:
            try:
                for col in column_controls:
                    if random.random() > 0.4:
                        lines = [random.choice(chars) for _ in range(12)]
                        col.value = "\n".join(lines)
                        col.opacity = random.uniform(0.08, 0.3)
                page.update()
                await asyncio.sleep(0.15)
            except Exception:
                break

    asyncio.create_task(animar())
    return rain_row