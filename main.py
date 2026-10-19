
#!/usr/bin/env python3
"""DUO: Plataforma Cooperativa Offline
Controles:
 Jogador 1: A/D mover, W pular
 Jogador 2: setas mover, seta para cima pular
 E: ativar a alavanca perto dela
 R: reiniciar a fase
 ESPAÇO: próxima fase após vencer

Requer Python 3 + Tkinter.
"""

import tkinter as tk

W, H = 900, 600
GRAVITY = 0.65
SPEED = 4.2
JUMP = -12.5
PLAYER_W, PLAYER_H = 28, 38

LEVELS = [
    {
        "name": "A ponte precisa de dois",
        "platforms": [
            (0, 550, 900, 50),
            (70, 450, 170, 18),
            (300, 380, 130, 18),
            (530, 450, 120, 18),
            (735, 370, 110, 18),
        ],
        "switch": (350, 345, 28, 35),
        "door": (700, 470, 35, 80),
        "exit": (820, 500, 45, 50),
        "goal": "Ative a alavanca com E e os dois cheguem a saída.",
    },
    {
        "name": "Um segura, o outro passa",
        "platforms": [
            (0, 550, 900, 50),
            (55, 455, 125, 18),
            (235, 390, 120, 18),
            (425, 330, 120, 18),
            (610, 390, 115, 18),
            (760, 455, 100, 18),
        ],
        "switch": (465, 295, 28, 35),
        "door": (720, 470, 35, 80),
        "exit": (820, 500, 45, 50),
        "goal": "Cooperem para subir, ativem a alavanca e cheguem a saida.",
    },
    {
        "name": "A saída dupla",
        "platforms": [
            (0, 550, 900, 50),
            (100, 460, 120, 18),
            (280, 400, 120, 18),
            (470, 460, 120, 18),
            (650, 400, 120, 18),
        ],
        "switch": (310, 365, 28, 35),
        "door": (720, 470, 35, 80),
        "exit": (820, 500, 45, 50),
        "goal": "Ativem a alavanca e cheguem juntos a saida.",
    },
]


class Player:
    def __init__(self, x, y, color, name, left, right, jump):
        self.x = x
        self.y = y
        self.vx = 0
        self.vy = 0
        self.color = color
        self.name = name
        self.left = left
        self.right = right
        self.jump_key = jump
        self.on_ground = False
        self.jump_held = False
        self.alive = True

    def rect(self):
        return (
            self.x,
            self.y,
            self.x + PLAYER_W,
            self.y + PLAYER_H,
        )


class DuoGame:
    def __init__(self, root):
        self.root = root
        root.title("DUO - Plataforma Cooperativa Offline")
        root.resizable(False, False)

        self.canvas = tk.Canvas(
            root,
            width=W,
            height=H,
            bg="#172333",
            highlightthickness=0,
        )
        self.canvas.pack()

        self.info = tk.Label(
            root,
            text=(
                "P1: A/D mover, W pular  |  "
                "P2: ←/→ mover, ↑ pular  |  "
                "E: alavanca  |  R: reiniciar"
            ),
            bg="#25374b",
            fg="white",
            font=("Arial", 11),
            pady=8,
        )
        self.info.pack(fill="x")

        self.keys = set()
        self.level_index = 0

        self.root.bind("<KeyPress>", self.key_down)
        self.root.bind("<KeyRelease>", self.key_up)
        self.root.protocol("WM_DELETE_WINDOW", root.destroy)

        self.reset_level()
        self.tick()

    def reset_level(self):
        self.level = LEVELS[self.level_index]

        self.p1 = Player(
            45, 500, "#53b7ff",
            "JOGADOR 1", "a", "d", "w"
        )
        self.p2 = Player(
            95, 500, "#ffbd59",
            "JOGADOR 2", "left", "right", "up"
        )

        self.switch_on = False
        self.won = False
        self.message = ""
        self.keys.clear()

    @staticmethod
    def overlap(a, b):
        return (
            a[0] < b[0] + b[2]
            and a[2] > b[0]
            and a[1] < b[1] + b[3]
            and a[3] > b[1]
        )

    def near_switch(self, p):
        sx, sy, sw, sh = self.level["switch"]
        margin = 35

        area = (
            sx - margin,
            sy - margin,
            sw + margin * 2,
            sh + margin * 2,
        )

        return self.overlap(p.rect(), area)

    def key_down(self, event):
        key = event.keysym.lower()

        # Evita repetir a mesma ação enquanto a tecla fica pressionada.
        if key in self.keys:
            return

        self.keys.add(key)

        if key == "r":
            self.reset_level()
            return

        # A alavanca só é ativada ao pressionar E perto dela.
        if key == "e" and not self.switch_on and not self.won:
            for player in (self.p1, self.p2):
                if player.alive and self.near_switch(player):
                    self.switch_on = True
                    self.message = ""
                    break

        # Avança somente depois de concluir a fase.
        if key == "space" and self.won:
            if self.level_index < len(LEVELS) - 1:
                self.level_index += 1
            else:
                self.level_index = 0

            self.reset_level()

    def key_up(self, event):
        self.keys.discard(event.keysym.lower())

    def move_player(self, p):
        if not p.alive or self.won:
            return

        # Movimento horizontal
        p.vx = 0

        if p.left in self.keys:
            p.vx -= SPEED
        if p.right in self.keys:
            p.vx += SPEED

        # Pulo
        if p.jump_key in self.keys:
            if p.on_ground and not p.jump_held:
                p.vy = JUMP
                p.on_ground = False
            p.jump_held = True
        else:
            p.jump_held = False

        # Guarda a posição anterior para a colisão com a porta.
        old_x = p.x
        p.x += p.vx
        p.x = max(0, min(W - PLAYER_W, p.x))

        # A porta bloqueia os jogadores enquanto a alavanca
        # não tiver sido ativada.
        if not self.switch_on:
            door = self.level["door"]

            if self.overlap(p.rect(), door):
                if p.vx > 0:
                    p.x = door[0] - PLAYER_W
                elif p.vx < 0:
                    p.x = door[0] + door[2]
                else:
                    p.x = old_x

        # Gravidade e movimento vertical
        old_bottom = p.y + PLAYER_H
        p.vy += GRAVITY
        p.y += p.vy
        p.on_ground = False

        for plat in self.level["platforms"]:
            x, y, width, height = plat

            if (
                p.vy >= 0
                and old_bottom <= y + 4
                and p.x + PLAYER_W > x
                and p.x < x + width
                and p.y + PLAYER_H >= y
            ):
                p.y = y - PLAYER_H
                p.vy = 0
                p.on_ground = True

        # Caiu para fora do cenário.
        if p.y > H + 80:
            p.alive = False
            self.message = (
                f"{p.name} caiu! Pressione R para tentar novamente."
            )

    def update_game(self):
        if self.won:
            return

        if not self.p1.alive or not self.p2.alive:
            return

        self.move_player(self.p1)
        self.move_player(self.p2)

        # Vitória: os dois precisam chegar à saída.
        if (
            self.switch_on
            and self.overlap(self.p1.rect(), self.level["exit"])
            and self.overlap(self.p2.rect(), self.level["exit"])
        ):
            self.won = True
            self.message = "FASE CONCLUIDA! Os dois conseguiram juntos."

        if not self.p1.alive or not self.p2.alive:
            self.message = "Um parceiro caiu. Pressione R para reiniciar."

    def draw_player(self, p):
        if not p.alive:
            return

        x1, y1, x2, y2 = p.rect()

        self.canvas.create_rectangle(
            x1, y1, x2, y2,
            fill=p.color,
            outline="white",
            width=2,
        )

        self.canvas.create_oval(
            x1 + 6, y1 + 8, x1 + 10, y1 + 12,
            fill="#172333", outline=""
        )
        self.canvas.create_oval(
            x1 + 18, y1 + 8, x1 + 22, y1 + 12,
            fill="#172333", outline=""
        )

        self.canvas.create_text(
            (x1 + x2) / 2,
            y1 - 12,
            text=p.name,
            fill=p.color,
            font=("Arial", 9, "bold"),
        )

    def draw(self):
        c = self.canvas
        c.delete("all")

        # Estrelas no fundo
        stars = [
            (60, 70), (180, 120), (280, 55),
            (440, 95), (580, 60), (760, 125),
            (840, 70), (670, 210), (120, 235),
        ]

        for x, y in stars:
            c.create_oval(
                x, y, x + 3, y + 3,
                fill="#71859c", outline=""
            )

        c.create_text(
            18, 18,
            anchor="nw",
            text=(
                f"DUO | FASE {self.level_index + 1}/"
                f"{len(LEVELS)}: {self.level['name']}"
            ),
            fill="white",
            font=("Arial", 15, "bold"),
        )

        c.create_text(
            18, 48,
            anchor="nw",
            text=self.level["goal"],
            fill="#c9d8e8",
            font=("Arial", 10),
        )

        # Plataformas
        for x, y, width, height in self.level["platforms"]:
            c.create_rectangle(
                x, y, x + width, y + height,
                fill="#50677c",
                outline="#8ca7be",
                width=2,
            )
            c.create_rectangle(
                x, y, x + width, y + 4,
                fill="#8ca7be",
                outline="",
            )

        # Alavanca
        sx, sy, sw, sh = self.level["switch"]

        c.create_rectangle(
            sx, sy, sx + sw, sy + sh,
            fill="#55e6a5" if self.switch_on else "#d65b6b",
            outline="white",
            width=2,
        )

        c.create_text(
            sx + sw / 2, sy - 12,
            text="ALAVANCA",
            fill="white",
            font=("Arial", 9, "bold"),
        )

        if not self.switch_on:
            c.create_text(
                sx + sw / 2, sy + sh + 13,
                text="E",
                fill="#ffe08a",
                font=("Arial", 11, "bold"),
            )

        # Porta
        dx, dy, dw, dh = self.level["door"]

        if not self.switch_on:
            c.create_rectangle(
                dx, dy, dx + dw, dy + dh,
                fill="#b44859",
                outline="#ffb3bd",
                width=3,
            )
            c.create_text(
                dx + dw / 2, dy + dh / 2,
                text="X",
                fill="white",
                font=("Arial", 22, "bold"),
            )
        else:
            c.create_rectangle(
                dx, dy, dx + dw, dy + dh,
                outline="#55e6a5",
                width=2,
                dash=(4, 3),
            )

        # Saída
        ex, ey, ew, eh = self.level["exit"]

        c.create_rectangle(
            ex, ey, ex + ew, ey + eh,
            fill="#4d3e86",
            outline="#bba8ff",
            width=3,
        )
        c.create_text(
            ex + ew / 2, ey + eh / 2,
            text="SAIDA",
            fill="white",
            font=("Arial", 9, "bold"),
            angle=90,
        )

        self.draw_player(self.p1)
        self.draw_player(self.p2)

        c.create_text(
            W - 15, 20,
            anchor="ne",
            text=(
                "Alavanca: ATIVADA"
                if self.switch_on
                else "Alavanca: DESATIVADA"
            ),
            fill="#55e6a5" if self.switch_on else "#ff929e",
            font=("Arial", 11, "bold"),
        )

        # Orientação para ativar a alavanca
        if not self.switch_on and not self.won:
            nearby = (
                (self.p1.alive and self.near_switch(self.p1))
                or (self.p2.alive and self.near_switch(self.p2))
            )

            if nearby:
                c.create_text(
                    450, 100,
                    text="PRESSIONE E PARA ATIVAR A ALAVANCA",
                    fill="#ffe08a",
                    font=("Arial", 13, "bold"),
                )

        # Mensagens de vitória ou derrota
        if self.message:
            c.create_rectangle(
                150, 235, 750, 350,
                fill="#101923",
                outline="#dce9f6",
                width=2,
            )
            c.create_text(
                450, 275,
                text=self.message,
                fill="white",
                font=("Arial", 16, "bold"),
                width=560,
            )

            if self.won:
                c.create_text(
                    450, 315,
                    text="Pressione ESPACO para a proxima fase",
                    fill="#ffe08a",
                    font=("Arial", 12, "bold"),
                )
            else:
                c.create_text(
                    450, 315,
                    text="Pressione R para reiniciar a fase",
                    fill="#ffe08a",
                    font=("Arial", 12, "bold"),
                )

    def tick(self):
        self.update_game()
        self.draw()
        self.root.after(16, self.tick)


if __name__ == "__main__":
    root = tk.Tk()
    game = DuoGame(root)
    root.mainloop()
