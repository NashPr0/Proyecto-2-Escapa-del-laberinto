import tkinter as tk
from tkinter import simpledialog
import tkinter.messagebox as messagebox
import random
import time
import os
from collections import deque

# -----------------------------
# CONSTANTES
# -----------------------------
CAMINO = 0
MURO = 1
LIANA = 2
TUNEL = 3
SALIDA = 4

TAM_CELDA = 32
ANCHO_MAPA = 23
ALTO_MAPA = 15

# -----------------------------
# SoundManager (silencioso si pygame no existe)
# -----------------------------
class SoundManager:
    def __init__(self):
        self.enabled = False
        self.bg_playing = False
        try:
            import pygame
            self.pygame = pygame
            pygame.mixer.init()
            self.enabled = True
        except Exception:
            # no hay sonido; continuamos sin fallar
            self.enabled = False

    def play_boton(self):
        pass
    def toggle_bg_music(self):
        pass
    def adjust_volume(self, delta):
        pass

# -----------------------------
# TU LÓGICA: jugador + enemigo
# -----------------------------
MAX_ENERGIA = 10
COSTO_CORRER = 3
REGEN_ENERGIA = 1
RESPAWN_ENEMIGO_SEG = 5.0

class jugador:
    def __init__(self, fila, col):
        self.fila = fila
        self.col = col
        self.energia = MAX_ENERGIA

    def posicion(self):
        return (self.fila, self.col)

    def mover(self, df, dc, mapa, corriendo=False):
        nf = self.fila + df
        nc = self.col + dc
        if mapa.es_valido_jugador(nf, nc):
            self.fila = nf
            self.col = nc
            costo = COSTO_CORRER if corriendo else 1
            self.energia = max(0, self.energia - costo)
            return True
        return False

    def regenerar(self):
        if self.energia < MAX_ENERGIA:
            self.energia = min(MAX_ENERGIA, self.energia + REGEN_ENERGIA)

class enemigo:
    def __init__(self, fila, col, sprite_index=0,
                 respawn_fila=None, respawn_col=None,
                 respawn_delay=RESPAWN_ENEMIGO_SEG):
        self.fila = fila
        self.col = col
        self.sprite_index = sprite_index
        self.vivo = True
        self.respawn_delay = respawn_delay
        self.tiempo_respawn = None
        self.respawn_fila = respawn_fila if respawn_fila is not None else fila
        self.respawn_col = respawn_col if respawn_col is not None else col
        self.stuck = 0

    def posicion(self):
        return (self.fila, self.col)

    def matar(self, ahora):
        self.vivo = False
        self.tiempo_respawn = ahora + self.respawn_delay
        self.stuck = 0

    def intentar_revivir(self, ahora, mapa, sound_manager=None):
        if not self.vivo and self.tiempo_respawn is not None and ahora >= self.tiempo_respawn:
            self.respawn_instantaneo(mapa)

    def respawn_instantaneo(self, mapa):
        alto, ancho = getattr(mapa, "alto", ALTO_MAPA), getattr(mapa, "ancho", ANCHO_MAPA)
        for _ in range(200):
            r = random.randint(0, alto - 1)
            c = random.randint(0, ancho - 1)
            if mapa.es_valido_enemigo(r, c):
                self.fila, self.col = r, c
                self.vivo = True
                self.tiempo_respawn = None
                return
        # fallback
        self.fila, self.col = self.respawn_fila, self.respawn_col
        self.vivo = True
        self.tiempo_respawn = None

    # MODO ESCAPA: perseguir jugador (usa mapa.siguiente_paso_enemigo)
    def mover_hacia(self, destino, mapa):
        if not self.vivo:
            return

        origen = self.posicion()
        # pedir paso al mapa (BFS) si existe
        try:
            df, dc = mapa.siguiente_paso_enemigo(origen, destino)
        except Exception:
            # fallback simple: moverse hacia Manhattan
            df = 1 if destino[0] > origen[0] else -1 if destino[0] < origen[0] else 0
            dc = 1 if destino[1] > origen[1] else -1 if destino[1] < origen[1] else 0

        # si BFS devuelve (0,0) y no estamos en destino, probar vecinos que acerquen
        if df == 0 and dc == 0 and origen != destino:
            of, oc = origen
            mejor_mov = None
            mejor_dist = abs(of - destino[0]) + abs(oc - destino[1])
            for dr, dc2 in [(-1,0),(1,0),(0,-1),(0,1)]:
                nf, nc = of + dr, oc + dc2
                if not mapa.es_valido_enemigo(nf, nc):
                    continue
                d = abs(nf - destino[0]) + abs(nc - destino[1])
                if d < mejor_dist:
                    mejor_dist = d
                    mejor_mov = (dr, dc2)
            if mejor_mov:
                df, dc = mejor_mov
            else:
                self.stuck += 1
                if self.stuck >= 4:
                    dirs = [(-1,0),(1,0),(0,-1),(0,1)]
                    random.shuffle(dirs)
                    for dr, dc2 in dirs:
                        nf, nc = of + dr, oc + dc2
                        if mapa.es_valido_enemigo(nf, nc):
                            self.fila, self.col = nf, nc
                            self.stuck = 0
                            return
                return

        nf = self.fila + df
        nc = self.col + dc
        if mapa.es_valido_enemigo(nf, nc):
            self.fila, self.col = nf, nc
            self.stuck = 0
        else:
            self.stuck += 1

    # MODO CAZADOR: huir del jugador
    def mover_huir(self, jugador_pos, mapa):
        if not self.vivo:
            return

        jr, jc = jugador_pos
        mejor_dist = -1
        mejores = []
        for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
            nr = self.fila + dr
            nc = self.col + dc
            if not mapa.es_valido_enemigo(nr, nc):
                continue
            d = abs(nr - jr) + abs(nc - jc)
            if d > mejor_dist:
                mejor_dist = d
                mejores = [(dr, dc)]
            elif d == mejor_dist:
                mejores.append((dr, dc))

        if mejores:
            dr, dc = random.choice(mejores)
            self.fila += dr
            self.col += dc
            self.stuck = 0
            return

        self.stuck += 1
        if self.stuck >= 4:
            dirs = [(-1,0),(1,0),(0,-1),(0,1)]
            random.shuffle(dirs)
            for dr, dc in dirs:
                nr = self.fila + dr
                nc = self.col + dc
                if mapa.es_valido_enemigo(nr, nc):
                    self.fila, self.col = nr, nc
                    self.stuck = 0
                    return

# -----------------------------
# MapaSimple (opción B)
# -----------------------------
class MapaSimple:
    def __init__(self, alto=15, ancho=23):
        self.alto = alto
        self.ancho = ancho
        self.entrada = (1, 1)

    def es_valido_jugador(self, r, c):
        return 0 <= r < self.alto and 0 <= c < self.ancho

    def es_valido_enemigo(self, r, c):
        return 0 <= r < self.alto and 0 <= c < self.ancho

    def siguiente_paso_enemigo(self, origen, destino):
        (fo, co) = origen
        (fd, cd) = destino
        if origen == destino:
            return (0, 0)

        visitado = set()
        cola = deque()
        padre = {}
        cola.append((fo, co))
        visitado.add((fo, co))
        dirs = [(-1,0),(1,0),(0,-1),(0,1)]
        found = False
        while cola:
            r, c = cola.popleft()
            if (r, c) == destino:
                found = True
                break
            for dr, dc in dirs:
                nr, nc = r + dr, c + dc
                if 0 <= nr < self.alto and 0 <= nc < self.ancho:
                    if (nr, nc) not in visitado:
                        padre[(nr, nc)] = (r, c)
                        visitado.add((nr, nc))
                        cola.append((nr, nc))
        if not found:
            return (0, 0)
        actual = (fd, cd)
        while padre.get(actual) != origen:
            actual = padre.get(actual)
            if actual is None:
                return (0, 0)
        df = actual[0] - fo
        dc = actual[1] - co
        return (df, dc)

# -----------------------------
# GUI (versión simple integrada)
# -----------------------------
class JuegoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Laberinto - Integrado")
        self.root.resizable(False, False)

        width = ANCHO_MAPA * TAM_CELDA
        height = ALTO_MAPA * TAM_CELDA + 80
        self.root.geometry(f"{width}x{height}")

        # estado
        self.mapa = None
        self.modo_actual = None
        self.player = None
        self.enemigos = []
        self.juego_activo = False

        self.sound = SoundManager()

        # frames
        self.frame_menu = tk.Frame(root, bg="#202020")
        self.frame_sel = tk.Frame(root, bg="#202020")
        self.frame_juego = tk.Frame(root, bg="#000000")
        self.frame_punt = tk.Frame(root, bg="#202020")

        self._construir_menu()
        self._construir_seleccion_modo()
        self._construir_pantalla_juego()

        self.mostrar_frame(self.frame_menu)

    def mostrar_frame(self, f):
        for frm in (self.frame_menu, self.frame_sel, self.frame_juego, self.frame_punt):
            frm.pack_forget()
        f.pack(fill="both", expand=True)

    def _construir_menu(self):
        lbl = tk.Label(self.frame_menu, text="LABERINTO", fg="white", bg="#202020", font=("Arial", 24, "bold"))
        lbl.pack(pady=20)
        tk.Button(self.frame_menu, text="Jugar", width=20, command=self._accion_jugar).pack(pady=8)
        tk.Button(self.frame_menu, text="Salir", width=20, command=self.root.destroy).pack(pady=8)

    def _accion_jugar(self):
        nombre = simpledialog.askstring("Nombre", "Ingresa tu nombre:", parent=self.root)
        if not nombre:
            return
        self.nombre = nombre.strip()
        self.mostrar_frame(self.frame_sel)

    def _construir_seleccion_modo(self):
        lbl = tk.Label(self.frame_sel, text="Selecciona modo", fg="white", bg="#202020", font=("Arial", 18, "bold"))
        lbl.pack(pady=20)
        tk.Button(self.frame_sel, text="Modo Escapa", width=20, command=lambda: self.iniciar_modo("escapa")).pack(pady=6)
        tk.Button(self.frame_sel, text="Modo Cazador", width=20, command=lambda: self.iniciar_modo("cazador")).pack(pady=6)
        tk.Button(self.frame_sel, text="Volver", width=20, command=lambda: self.mostrar_frame(self.frame_menu)).pack(pady=6)

    def _construir_pantalla_juego(self):
        info = tk.Frame(self.frame_juego, bg="#111111")
        info.pack(fill="x")
        self.lbl_modo = tk.Label(info, text="Modo: -", fg="white", bg="#111111")
        self.lbl_modo.pack(side="left", padx=10)
        self.lbl_energia = tk.Label(info, text="Energía: --", fg="white", bg="#111111")
        self.lbl_energia.pack(side="left", padx=10)

        w = ANCHO_MAPA * TAM_CELDA
        h = ALTO_MAPA * TAM_CELDA
        self.canvas = tk.Canvas(self.frame_juego, width=w, height=h, bg="black")
        self.canvas.pack()
        self.root.bind("<KeyPress>", self._teclas)

    def iniciar_modo(self, modo):
        try:
            self.modo_actual = modo
            self.mapa = MapaSimple()
            pf, pc = self.mapa.entrada
            # center spawn
            self.player = jugador(5, 5)
            self.enemigos = [enemigo(2,2), enemigo(10,15), enemigo(8,3)]
            self.juego_activo = True
            self.mostrar_frame(self.frame_juego)
            # comenzar loop
            self.root.after(100, self._loop_juego)
        except Exception as e:
            print("Error iniciar_modo:", e)

    def _teclas(self, event):
        if not self.juego_activo:
            return
        k = event.keysym.lower()
        movs = {"w":(-1,0),"s":(1,0),"a":(0,-1),"d":(0,1)}
        if k in movs:
            df, dc = movs[k]
            self.player.mover(df, dc, self.mapa)
        if k == "e":
            self.modo_actual = "escapa"
        if k == "c":
            self.modo_actual = "cazador"

    def _loop_juego(self):
        if not self.juego_activo:
            return
        try:
            pr, pc = self.player.posicion()
            self.player.regenerar()
            for e in self.enemigos:
                if e.vivo:
                    if self.modo_actual == "escapa":
                        e.mover_hacia((pr, pc), self.mapa)
                        if e.posicion() == (pr, pc):
                            e.matar(time.time())
                    else:
                        e.mover_huir((pr, pc), self.mapa)
                else:
                    e.intentar_revivir(time.time(), self.mapa, None)
            self._dibujar()
        except Exception as e:
            print("Error en loop:", e)
        self.root.after(150, self._loop_juego)

    def _dibujar(self):
        self.canvas.delete("all")
        # dibujar grid opcional (comentar si quieres)
        for r in range(self.mapa.alto):
            for c in range(self.mapa.ancho):
                x1 = c * TAM_CELDA
                y1 = r * TAM_CELDA
                x2 = x1 + TAM_CELDA
                y2 = y1 + TAM_CELDA
                # cuadro fondo
                self.canvas.create_rectangle(x1, y1, x2, y2, fill="#202020", outline="#262626")
        # jugador
        pr, pc = self.player.posicion()
        self._cell(pr, pc, "blue")
        # enemigos
        for e in self.enemigos:
            r, c = e.posicion()
            color = "red" if e.vivo else "gray"
            self._cell(r, c, color)
        # labels
        self.lbl_modo.config(text=f"Modo: {self.modo_actual}")
        self.lbl_energia.config(text=f"Energía: {self.player.energia}")

    def _cell(self, r, c, color):
        x1 = c * TAM_CELDA
        y1 = r * TAM_CELDA
        x2 = x1 + TAM_CELDA
        y2 = y1 + TAM_CELDA
        self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="")

# -----------------------------
# RUN
# -----------------------------
if __name__ == "__main__":
    root = tk.Tk()
    app = JuegoApp(root)
    root.mainloop()


