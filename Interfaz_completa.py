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