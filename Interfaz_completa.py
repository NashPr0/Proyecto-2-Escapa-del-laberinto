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