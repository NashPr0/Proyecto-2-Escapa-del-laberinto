import tkinter as tk
from tkinter import simpledialog
import tkinter.messagebox as messagebox
import random
import time
import os
from collections import deque

# CONSTANTES GENERALES

CAMINO = 0
MURO = 1
LIANA = 2
TUNEL = 3
SALIDA = 4

TAM_CELDA = 32

ANCHO_MAPA = 23
ALTO_MAPA = 15

ARCHIVO_PUNTAJES_CAZADOR = "puntajes_cazador.txt"
ARCHIVO_PUNTAJES_ESCAPA  = "puntajes_escapa.txt"

TIEMPO_PREVIEW = 5.0

# Utilidades

def guardar_puntaje(nombre, modo, puntaje, gano, tiempo, archivo):
    pass
def leer_puntajes(archivo):
    pass
def top5_por_archivo(archivo):
    pass
def stats_por_jugador(nombre, archivo):
    pass

#_________________creacion de clases___________________
# Manejo de sonido

class SoundManager:
    """
    Maneja todos los sonidos del juego:
      - efectos (botón, caminar, muerte, respawn)
      - música de fondo
      - sonidos de ganar / perder
    """
    def __init__(self):
        pass

    def _buscar_archivo_multi(self, base_dir, nombre_sin_ext):
        pass

    def _cargar_sonido_multi(self, base_dir, nombre_sin_ext):
        pass

    def play_boton(self):
        pass

    def play_jugador_caminar(self):
        pass

    def play_jugador_muerte(self):
        pass

    def play_robot_caminar(self):
        pass

    def play_robot_muerte(self):
        pass

    def play_robot_regeneracion(self):
        pass

    def play_bg_music(self):
        pass

    def stop_bg_music(self):
        pass

    def toggle_bg_music(self):
        pass

    def adjust_volume(self, delta):
        pass

    def play_ganar(self):
        pass

    def play_perder(self):
        pass


class SpriteManager:
    def __init__(self, root):
        pass


class Terreno:
    codigo = None

    def permite_jugador(self):
        pass

    def permite_enemigo(self):
        pass


class Camino(Terreno):
    codigo = None


class Muro(Terreno):
    codigo = None

    def permite_jugador(self):
        pass

    def permite_enemigo(self):
        pass


class Liana(Terreno):
    codigo = None

    def permite_jugador(self):
        pass

    def permite_enemigo(self):
        pass


class Tunel(Terreno):
    codigo = None

    def permite_jugador(self):
        pass

    def permite_enemigo(self):
        pass


class Salida(Terreno):
    codigo = None



    def _colocar_terrenos_especiales(self):
        pass

    def casilla(self, f, c):
        pass

    def es_valido_jugador(self, f, c):
        pass

    def es_valido_enemigo(self, f, c):
        pass

    def siguiente_paso_enemigo(self, origen, destino):
        pass

class Mapa:
    def __init__(self, ancho, alto):
        self.ancho = ancho
        self.alto = alto
        self.m = [[MURO for _ in range(ancho)] for _ in range(alto)]

        self.entrada = (alto - 2, 1)

        self.salidas = [
            (1, ancho // 2),
            (alto - 2, ancho // 2),
            (alto // 2, 1),
            (alto // 2, ancho - 2),
        ]

        self._generar_laberinto()
        self._garantizar_camino_valido()
        self._colocar_terrenos_especiales()

    def _generar_laberinto(self):
        ALTO, ANCHO = self.alto, self.ancho
        visitado = [[False] * ANCHO for _ in range(ALTO)]

        def vecinos(r, c):
            vs = []
            for dr, dc in [(-2, 0), (2, 0), (0, -2), (0, 2)]:
                nr, nc = r + dr, c + dc
                if 1 <= nr < ALTO - 1 and 1 <= nc < ANCHO - 1 and not visitado[nr][nc]:
                    vs.append((nr, nc))
            random.shuffle(vs)
            return vs

        er, ec = self.entrada
        start_r, start_c = er - 1, ec
        if start_r < 1:
            start_r = 1
        self.m[start_r][start_c] = CAMINO
        visitado[start_r][start_c] = True
        stack = [(start_r, start_c)]

        while stack:
            r, c = stack[-1]
            vs = vecinos(r, c)
            if not vs:
                stack.pop()
                continue
            nr, nc = vs.pop()
            visitado[nr][nc] = True
            self.m[nr][nc] = CAMINO
            mr, mc = (r + nr) // 2, (c + nc) // 2
            self.m[mr][mc] = CAMINO
            stack.append((nr, nc))

        for r in range(ALTO):
            for c in range(ANCHO):
                if r in (0, ALTO - 1) or c in (0, ANCHO - 1):
                    self.m[r][c] = MURO

        er, ec = self.entrada
        self.m[er][ec] = CAMINO
        for sr, sc in self.salidas:
            self.m[sr][sc] = SALIDA

    def _colocar_terrenos_especiales(self):
        pass

    def casilla(self, f, c):
        pass

    def es_valido_jugador(self, f, c):
        pass

    def es_valido_enemigo(self, f, c):
        pass

    def siguiente_paso_enemigo(self, origen, destino):
        pass





class JuegoApp:
    #  util GUI

    def _center_root(self, width, height):
        pass

    def _on_configure(self, event):
        pass

    def mostrar_frame(self, frame):
        pass

    def _wrap_button(self, action):
        pass

    def _aplicar_fondo(self, frame):
        pass

    # ----------------- construcción pantallas -----------------

    def _construir_menu_principal(self):
        pass

    def _construir_seleccion_modo(self):
        pass

    def _construir_pantalla_puntajes(self):
        pass  

    def _construir_pantalla_creditos(self):
        pass

    #  acciones de menú 

    def _accion_puntajes(self):
        pass

    def _accion_creditos(self):
        pass

    def _volver_menu_principal(self):
        pass

    def _toggle_music(self):
        pass

    #  spawns y modos (sin crear enemigos, solo posiciones) 

    def _spawn_en_corners(self, cantidad):
        pass

    #  puntajes (pantalla) 

    def _actualizar_texto_puntajes(self):
        pass

# Menu 
if __name__ == "__main__":
    root = tk.Tk()
    app = JuegoApp(root) # control y Logica 
    root.mainloop()
