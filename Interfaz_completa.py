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
#---------------------------------------------------------------------
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


# Menu 
if __name__ == "__main__":
    root = tk.Tk()
    app = JuegoApp(root) # control y Logica 
    root.mainloop()
