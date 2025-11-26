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
    try:
        with open(archivo, "a", encoding="utf-8") as f:
            linea = f"{nombre};{modo};{puntaje};{1 if gano else 0};{int(tiempo)}\n"
            f.write(linea)
    except Exception as e:
        print("Error guardando puntaje:", e)


def leer_puntajes(archivo):
    if not os.path.exists(archivo):
        return []
    resultados = []
    try:
        with open(archivo, "r", encoding="utf-8") as f:
            for linea in f:
                linea = linea.strip()
                if not linea:
                    continue
                partes = linea.split(";")
                if len(partes) != 5:
                    continue
                nombre, modo, puntaje, gano, tiempo = partes
                try:
                    puntaje = int(puntaje)
                    gano = bool(int(gano))
                    tiempo = int(tiempo)
                except ValueError:
                    continue
                resultados.append({
                    "nombre": nombre,
                    "modo": modo,
                    "puntaje": puntaje,
                    "gano": gano,
                    "tiempo": tiempo
                })
    except Exception as e:
        print("Error leyendo puntajes:", e)
    return resultados


def top5_por_archivo(archivo):
    datos = leer_puntajes(archivo)
    datos.sort(key=lambda x: x["puntaje"], reverse=True)
    return datos[:5]


def stats_por_jugador(nombre, archivo):
    datos = leer_puntajes(archivo)
    jugadas = [d for d in datos if d["nombre"].lower() == nombre.lower()]
    if not jugadas:
        return None
    total = len(jugadas)
    ganadas = sum(1 for j in jugadas if j["gano"])
    mejor = max(jugadas, key=lambda j: j["puntaje"])
    return {
        "total": total,
        "ganadas": ganadas,
        "mejor_puntaje": mejor["puntaje"],
        "mejor_tiempo": mejor["tiempo"]
    }

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
        self.enabled = False
        self.bg_playing = False
        self.bg_music_path = None

        try:
            import pygame
            self.pygame = pygame
            pygame.mixer.init()
            base_dir = os.path.dirname(os.path.abspath(__file__))

            # Carga de efectos de sonido (busca .mp3, .wav, .ogg)
            self.snd_boton = self._cargar_sonido_multi(base_dir, "sonido_boton")
            self.snd_ganar = self._cargar_sonido_multi(base_dir, "sonido_ganar")
            self.snd_perder = self._cargar_sonido_multi(base_dir, "sonido_perder")
            self.snd_jugador_caminar = self._cargar_sonido_multi(base_dir, "sonido_jugador_caminata")
            self.snd_jugador_muerte = self._cargar_sonido_multi(base_dir, "sonido_jugador_muerte")
            self.snd_robot_caminar = self._cargar_sonido_multi(base_dir, "sonido_robot_caminata")
            self.snd_robot_muerte = self._cargar_sonido_multi(base_dir, "sonido_robot_muerte")
            self.snd_robot_regeneracion = self._cargar_sonido_multi(base_dir, "sonido_robot_regeneracion")

            # Música de fondo
            self.bg_music_path = self._buscar_archivo_multi(base_dir, "sonido_fondo")

            self.enabled = True
        except Exception as e:
            print("Sonido desactivado:", e)
            self.enabled = False

    # utilidades internas 

    def _buscar_archivo_multi(self, base_dir, nombre_sin_ext):
        """Busca nombre_sin_ext con extensiones comunes de audio."""
        for ext in (".mp3", ".wav", ".ogg"):
            ruta = os.path.join(base_dir, nombre_sin_ext + ext)
            if os.path.exists(ruta):
                return ruta
        return None

    def _cargar_sonido_multi(self, base_dir, nombre_sin_ext):
        """Carga un sonido si existe, o devuelve None."""
        try:
            ruta = self._buscar_archivo_multi(base_dir, nombre_sin_ext)
            if ruta:
                return self.pygame.mixer.Sound(ruta)
        except Exception as e:
            print(f"No se pudo cargar sonido {nombre_sin_ext}:", e)
        return None

    #  efectos varios

    def play_boton(self):
        if self.enabled and self.snd_boton:
            self.snd_boton.play()

    def play_jugador_caminar(self):
        if self.enabled and self.snd_jugador_caminar:
            self.snd_jugador_caminar.play()

    def play_jugador_muerte(self):
        if self.enabled and self.snd_jugador_muerte:
            self.snd_jugador_muerte.play()

    def play_robot_caminar(self):
        if self.enabled and self.snd_robot_caminar:
            self.snd_robot_caminar.play()

    def play_robot_muerte(self):
        if self.enabled and self.snd_robot_muerte:
            self.snd_robot_muerte.play()

    def play_robot_regeneracion(self):
        if self.enabled and self.snd_robot_regeneracion:
            self.snd_robot_regeneracion.play()

    #  música de fondo 
    def play_bg_music(self):
        if not self.enabled or self.bg_playing or not self.bg_music_path:
            return
        try:
            self.pygame.mixer.music.load(self.bg_music_path)
            self.pygame.mixer.music.play(-1)
            self.bg_playing = True
        except Exception as e:
            print("No se pudo reproducir música:", e)

    def stop_bg_music(self):
        if not self.enabled:
            return
        try:
            self.pygame.mixer.music.stop()
            self.bg_playing = False
        except Exception as e:
            print("No se pudo detener música:", e)

    def toggle_bg_music(self):
        if not self.enabled:
            return
        if self.bg_playing:
            self.stop_bg_music()
        else:
            self.play_bg_music()

    def adjust_volume(self, delta):
        """Sube/baja volumen global de la música de fondo."""
        if not self.enabled:
            return
        try:
            vol = self.pygame.mixer.music.get_volume()
            vol = min(1.0, max(0.0, vol + delta))
            self.pygame.mixer.music.set_volume(vol)
        except Exception as e:
            print("No se pudo ajustar volumen:", e)

    # ganar / perder

    def play_ganar(self):
        """
        Sonido de victoria.
        Se reproduce por encima de la música de fondo.
        """
        if not self.enabled:
            return
        if self.snd_ganar:
            self.snd_ganar.play()
        else:
            print("Advertencia: snd_ganar no cargado.")

    def play_perder(self):
        """
        Sonido de derrota.
        """
        if not self.enabled:
            return
        if self.snd_perder:
            self.snd_perder.play()
        else:
            print("Advertencia: snd_perder no cargado.")

class SpriteManager:
    def __init__(self, root):
        pass

# CLASES DE TERRENO

class Terreno:
    codigo = CAMINO
    def permite_jugador(self): return True
    def permite_enemigo(self): return True

class Camino(Terreno):
    codigo = CAMINO

class Muro(Terreno):
    codigo = MURO
    def permite_jugador(self): return False
    def permite_enemigo(self): return False

class Liana(Terreno):
    codigo = LIANA
    def permite_jugador(self): return False   # Para enemigo 
    def permite_enemigo(self): return True

class Tunel(Terreno):
    codigo = TUNEL
    def permite_jugador(self): return True    # Para jugaador
    def permite_enemigo(self): return False

class Salida(Terreno):
    codigo = SALIDA

CLASES_TERRENO = {
    CAMINO: Camino,
    MURO: Muro,
    LIANA: Liana,
    TUNEL: Tunel,
    SALIDA: Salida,
}
class Mapa:
    def __init__(self, ancho, alto):
        self.ancho = ancho
        self.alto = alto
        self.m = [[MURO for _ in range(ancho)] for _ in range(alto)]

        # Entrada fija
        self.entrada = (alto - 2, 1)

         # Cuatro posibles salidas (centro de cada lado
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

        # bordes como muros
        for r in range(ALTO):
            for c in range(ANCHO):
                if r in (0, ALTO - 1) or c in (0, ANCHO - 1):
                    self.m[r][c] = MURO

        # abrir entrada y salidas
        er, ec = self.entrada
        self.m[er][ec] = CAMINO
        for sr, sc in self.salidas:
            self.m[sr][sc] = SALIDA

    #  garantizar camino entre entrada y alguna salida 
    def _garantizar_camino_valido(self):
        def hay_camino(origen, destino):
            cola = deque([origen])
            vis = {origen}
            while cola:
                r, c = cola.popleft()
                if (r, c) == destino:
                    return True
                for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < self.alto and 0 <= nc < self.ancho:
                        if self.m[nr][nc] != MURO and (nr, nc) not in vis:
                            vis.add((nr, nc))
                            cola.append((nr, nc))
            return False

        for s in self.salidas:
            if hay_camino(self.entrada, s):
                return

        # si no hay camino se abre uno recto a una salida aleatoria
        er, ec = self.entrada
        sr, sc = random.choice(self.salidas)

        r, c = er, ec
        while r != sr:
            self.m[r][c] = CAMINO
            r += 1 if sr > r else -1
        while c != sc:
            self.m[r][c] = CAMINO
            c += 1 if sc > c else -1
        self.m[sr][sc] = SALIDA

    # colocar túneles y lianas útiles
    def _colocar_terrenos_especiales(self):

        tuneles_deseados = random.randint(6, 10)
        lianas_deseadas = random.randint(3, 6)

        candidatos = []

        for r in range(2, self.alto - 2):
            for c in range(2, self.ancho - 2):

                # Debe ser MURO
                if self.m[r][c] != MURO:
                    continue

                #  Condición 1: entre dos muros 
                horizontal_muro = self.m[r][c - 1] == MURO and self.m[r][c + 1] == MURO
                vertical_muro   = self.m[r - 1][c] == MURO and self.m[r + 1][c] == MURO

                if not (horizontal_muro or vertical_muro):
                    continue

                # Condición 2: entre dos caminos 
                horizontal_camino = self.m[r][c - 2] == CAMINO and self.m[r][c + 2] == CAMINO \
                                    if 0 <= c - 2 < self.ancho and 0 <= c + 2 < self.ancho else False

                vertical_camino   = self.m[r - 2][c] == CAMINO and self.m[r + 2][c] == CAMINO \
                                    if 0 <= r - 2 < self.alto and 0 <= r + 2 < self.alto else False

                # Debe cumplir MURO y CAMINO en el mismo eje
                if not (
                    (horizontal_muro and horizontal_camino) or
                    (vertical_muro and vertical_camino)
                ):
                    continue

                candidatos.append((r, c))

        # Mezclar
        random.shuffle(candidatos)

        # Selección real según cantidad disponible
        n_tuneles = min(tuneles_deseados, len(candidatos))
        tuneles = candidatos[:n_tuneles]

        resto = candidatos[n_tuneles:]
        n_lianas = min(lianas_deseadas, len(resto))
        lianas = resto[:n_lianas]

        # Asignar
        for r, c in tuneles:
            self.m[r][c] = TUNEL

        for r, c in lianas:
            self.m[r][c] = LIANA
    # consultas 
    def casilla(self, f, c):
        return CLASES_TERRENO[self.m[f][c]]()

    def es_valido_jugador(self, f, c):
        return 0 <= f < self.alto and 0 <= c < self.ancho and self.casilla(f, c).permite_jugador()

    def es_valido_enemigo(self, f, c):
        return 0 <= f < self.alto and 0 <= c < self.ancho and self.casilla(f, c).permite_enemigo()

    # BFS para enemigos (perseguir objetivos)
    def siguiente_paso_enemigo(self, origen, destino):
        (fo, co) = origen
        (fd, cd) = destino
        if origen == destino:
            return (0, 0)

        dirs = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        cola = deque([origen])
        visitado = {origen}
        padre = {}

        while cola:
            f, c = cola.popleft()
            if (f, c) == destino:
                break
            for dr, dc in dirs:
                nf, nc = f + dr, c + dc
                if 0 <= nf < self.alto and 0 <= nc < self.ancho:
                    if (nf, nc) not in visitado and self.es_valido_enemigo(nf, nc):
                        visitado.add((nf, nc))
                        padre[(nf, nc)] = (f, c)
                        cola.append((nf, nc))

        if destino not in padre:
            return (0, 0)

        actual = destino
        while padre.get(actual) != origen:
            actual = padre.get(actual)
            if actual is None:
                return (0, 0)

        df = actual[0] - fo
        dc = actual[1] - co
        return (df, dc)



class JuegoApp:
    #  GUI
    def __init__(self, root):
        self.root = root
        self.root.title("Laberinto: versión congelada")
        self.root.resizable(False, False)

        width = ANCHO_MAPA * TAM_CELDA
        height = ALTO_MAPA * TAM_CELDA + 80
        self._fixed_geometry = None
        self._center_root(width, height)

        self.mapa = None
        self.modo_actual = None

        # Frames
        self.frame_menu = tk.Frame(root, bg="#202020")
        self.frame_seleccion_modo = tk.Frame(root, bg="#202020")
        self.frame_juego = tk.Frame(root, bg="#000000") 
        self.frame_menu = tk.Frame(root, bg="#202020")
        self.frame_juego = tk.Frame(root, bg="#000000")
        self.frame_puntajes = tk.Frame(root, bg="#202020")
        self.frame_creditos = tk.Frame(root, bg="#202020")

        self._construir_menu_principal()
        self._construir_seleccion_modo()
        self._construir_pantalla_juego()
        self._construir_pantalla_puntajes()
        self._construir_pantalla_creditos()
        self.mostrar_frame(self.frame_menu) 


    def _center_root(self, width, height):
        self.root.update_idletasks()
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = (sw - width) // 2
        y = (sh - height) // 2
        geom = f"{width}x{height}+{x}+{y}"
        self.root.geometry(geom)
        self._fixed_geometry = geom
        self.root.bind("<Configure>", self._on_configure)

    def _on_configure(self, event):
        if self._fixed_geometry and self.root.wm_geometry() != self._fixed_geometry:
            self.root.geometry(self._fixed_geometry)

    def mostrar_frame(self, frame):
        for f in (
            self.frame_menu,
            self.frame_seleccion_modo,
            self.frame_juego,
            self.frame_puntajes,
            self.frame_creditos,
        ):
            f.pack_forget()
        frame.pack(fill="both", expand=True)
        

    def _wrap_button(self, action):
        pass

    def _aplicar_fondo(self, frame):
        pass

    #  construcción pantallas 
    def _construir_menu_principal(self):
        titulo = tk.Label(
        self.frame_menu,
        text="LABERINTO",
        font=("Arial", 24, "bold"),
        fg="white",
        bg="#202020"
        )
        titulo.pack(pady=20)

        btn_jugar = tk.Button(
            self.frame_menu,
            text="Jugar",
            width=20,
            command=lambda: self.mostrar_frame(self.frame_seleccion_modo)
        )
        btn_jugar.pack(pady=10)

        btn_puntajes = tk.Button(
            self.frame_menu,
            text="Puntajes",
            width=20,
            command=self._mostrar_pantalla_puntajes  # la creamos 
        )
        btn_puntajes.pack(pady=10)

        btn_puntajes = tk.Button(
            self.frame_menu,
            text="Creditos",
            width=20,
            command=self._mostrar_pantalla_creditos  # la creamos 
        )
        btn_puntajes.pack(pady=10)

       

        btn_salir = tk.Button(
            self.frame_menu,
            text="Salir",
            width=20,
            command=self.root.destroy
        )
        btn_salir.pack(pady=20)
    
    def iniciar_modo(self, modo):
    
        #Arranca una partida en el modo indicado
        # Guardamos el modo actual
        self.modo_actual = modo
        if hasattr(self, "lbl_modo"):
            self.lbl_modo.config(text=f"Modo: {modo.capitalize()}")
        self.mapa = Mapa(ANCHO_MAPA, ALTO_MAPA)
        self.dibujar_mapa()
        self.mostrar_frame(self.frame_juego)
    
    def _construir_pantalla_juego(self):
        # Barra de info arriba
        info_frame = tk.Frame(self.frame_juego, bg="#111111")
        info_frame.pack(fill="x")

        self.lbl_modo = tk.Label(
            info_frame,
            text="Modo: -",
            fg="white",
            bg="#111111",
            font=("Arial", 12, "bold")
        )
        self.lbl_modo.pack(side="left", padx=10, pady=5)

        self.lbl_tiempo = tk.Label(
            info_frame,
            text="Tiempo: --",
            fg="white",
            bg="#111111",
            font=("Arial", 12)
        )
        self.lbl_tiempo.pack(side="left", padx=10)

        self.lbl_energia = tk.Label(
            info_frame,
            text="Energía: --",
            fg="white",
            bg="#111111",
            font=("Arial", 12)
        )
        self.lbl_energia.pack(side="left", padx=10)

        # Canvas del mapa
        ancho_px = ANCHO_MAPA * TAM_CELDA
        alto_px = ALTO_MAPA * TAM_CELDA
        self.canvas = tk.Canvas(
            self.frame_juego,
            width=ancho_px,
            height=alto_px,
            bg="black",
            highlightthickness=0
        )
        self.canvas.pack(padx=10, pady=10)

        # Botón volver al menú
        btn_volver = tk.Button(
            self.frame_juego,
            text="Volver al menú",
            command=lambda: self.mostrar_frame(self.frame_menu)
        )
        btn_volver.pack(pady=10)
        
    def dibujar_mapa(self):
        self.canvas.delete("all")

        colores = {
            CAMINO: "#303030",
            MURO:   "#101010",
            LIANA:  "#00AA00",
            TUNEL:  "#0000AA",
            SALIDA: "#FFD700"
        }

        # FILA (f) y COLUMNA (c)
        for f in range(self.mapa.alto):
            for c in range(self.mapa.ancho):
                tipo = self.mapa.m[f][c]      # aquí está el 0,1,2,3,4
                color = colores.get(tipo, "#FF00FF")

                x1 = c * TAM_CELDA            # columna → X
                y1 = f * TAM_CELDA            # fila    → Y
                x2 = x1 + TAM_CELDA
                y2 = y1 + TAM_CELDA

                self.canvas.create_rectangle(
                    x1, y1, x2, y2,
                    fill=color,
                    outline="#404040"
                )

        # Entrada 
        ef, ec = self.mapa.entrada
        x1 = ec * TAM_CELDA
        y1 = ef * TAM_CELDA
        x2 = x1 + TAM_CELDA
        y2 = y1 + TAM_CELDA
        self.canvas.create_rectangle(
            x1, y1, x2, y2,
            fill="#00FF00",
            outline="#00FF00"
        )
    def _construir_seleccion_modo(self):
        titulo = tk.Label(
        self.frame_seleccion_modo,
        text="Selecciona el modo",
        font=("Arial", 18, "bold"),
        fg="white",
        bg="#202020"
        )
        titulo.pack(pady=20)

        btn_cazador = tk.Button(
            self.frame_seleccion_modo,
            text="Modo Cazador",
            width=20,
            command=lambda: self.iniciar_modo("cazador")
        )
        btn_cazador.pack(pady=10)

        btn_escapa = tk.Button(
            self.frame_seleccion_modo,
            text="Modo Escapa",
            width=20,
            command=lambda: self.iniciar_modo("escapa")
        )
        btn_escapa.pack(pady=10)

        btn_volver = tk.Button(
            self.frame_seleccion_modo,
            text="Volver al menú",
            width=20,
            command=lambda: self.mostrar_frame(self.frame_menu)
        )
        btn_volver.pack(pady=20)

    def _accion_jugar(self):
        # Pedir nombre del jugador
        nombre = simpledialog.askstring(
            "Nombre",
            "Ingresa tu nombre:",
            parent=self.root
        )
        if not nombre:
            # Si cancela o deja vacío, volvemos al menú
            return
        self.nombre_jugador = nombre.strip()
        self.mostrar_frame(self.frame_seleccion_modo)

    def _construir_pantalla_puntajes(self):
        f = self.frame_puntajes

        titulo = tk.Label(
            f,
            text="Puntajes",
            font=("Arial", 18, "bold"),
            fg="white",
            bg="#202020"
        )
        titulo.pack(pady=10)

        self.txt_puntajes = tk.Text(
            f,
            width=50,
            height=15,
            bg="#111111",
            fg="white"
        )
        self.txt_puntajes.pack(padx=10, pady=10)

        btn_actualizar = tk.Button(
            f,
            text="Actualizar",
            command=self._actualizar_texto_puntajes
        )
        btn_actualizar.pack(pady=5)

        btn_volver = tk.Button(
            f,
            text="Volver al menú",
            command=lambda: self.mostrar_frame(self.frame_menu)
        )
        btn_volver.pack(pady=10)

    def _mostrar_pantalla_puntajes(self): ###
        self.txt_puntajes.delete("1.0", tk.END)
        self.txt_puntajes.insert(tk.END, "Sistema de puntajes aún en construcción...\n")
        self.mostrar_frame(self.frame_puntajes)

    def _construir_pantalla_creditos(self):
        f = self.frame_creditos
        self._aplicar_fondo(f)

        btn_volver = tk.Button(
            f, text="← Volver",
            command=self._wrap_button(self._volver_menu_principal)
        )
        btn_volver.place(x=10, y=10)

        titulo = tk.Label(
            f,
            text="Créditos",
            font=("Arial", 24, "bold"),
            bg="#202020",
            fg="white"
        )
        titulo.pack(pady=30)

        contenedor = tk.Frame(f, bg="#202020")
        contenedor.pack()

        col1 = tk.Frame(contenedor, bg="#202020")
        col1.grid(row=0, column=0, padx=40)

        tk.Label(col1, text="Montiel Anthony", font=("Arial", 16),
                 bg="#202020", fg="white").pack()
        tk.Label(col1, text="Carne: 2025132603",
                 bg="#202020", fg="white").pack()
        tk.Label(col1, text="Carrera: Ing. en Computadores",
                 bg="#202020", fg="white").pack()
        tk.Label(col1, text="Curso: Intro a la Programación",
                 bg="#202020", fg="white").pack()

        col2 = tk.Frame(contenedor, bg="#202020")
        col2.grid(row=0, column=1, padx=40)

        tk.Label(col2, text="Murillo Luis", font=("Arial", 16),
                 bg="#202020", fg="white").pack()
        tk.Label(col2, text="Carne: 00000000",
                 bg="#202020", fg="white").pack()
        tk.Label(col2, text="Carrera: Ing. en Computadores",
                 bg="#202020", fg="white").pack()
        tk.Label(col2, text="Curso: Intro a la Programación",
                 bg="#202020", fg="white").pack()


    def _mostrar_pantalla_creditos(self): ####
        self.mostrar_frame(self.frame_creditos)

    #  acciones de menú 

    def _accion_puntajes(self): #
        self._actualizar_texto_puntajes() #
        self.mostrar_frame(self.frame_puntajes) 

    def _accion_creditos(self): #
         self.mostrar_frame(self.frame_creditos)

    def _volver_menu_principal(self): # 
        self.mostrar_frame(self.frame_menu) 

    def _toggle_music(self):
        pass

    #  spawns y modos (sin crear enemigos, solo posiciones) 

    def _spawn_en_corners(self, cantidad):
        pass

    #  puntajes (pantalla) 

    def _actualizar_texto_puntajes(self):
        top_escapa = top5_por_archivo(ARCHIVO_PUNTAJES_ESCAPA)
        top_cazador = top5_por_archivo(ARCHIVO_PUNTAJES_CAZADOR)

        self.txt_puntajes.config(state="normal")
        self.txt_puntajes.delete("1.0", "end")

        self.txt_puntajes.insert("end", "TOP 5 Modo Escapa:\n")
        if top_escapa:
            for i, d in enumerate(top_escapa, start=1):
                linea = f"{i}. {d['nombre']} - Puntaje: {d['puntaje']} - Tiempo: {d['tiempo']} s\n"
                self.txt_puntajes.insert("end", linea)
        else:
            self.txt_puntajes.insert("end", "Sin puntajes registrados.\n")
        self.txt_puntajes.insert("end", "\n")

        self.txt_puntajes.insert("end", "TOP 5 Modo Cazador:\n")
        if top_cazador:
            for i, d in enumerate(top_cazador, start=1):
                linea = f"{i}. {d['nombre']} - Puntaje: {d['puntaje']} - Tiempo: {d['tiempo']} s\n"
                self.txt_puntajes.insert("end", linea)
        else:
            self.txt_puntajes.insert("end", "Sin puntajes registrados.\n")

        self.txt_puntajes.config(state="disabled")


# Menu 
if __name__ == "__main__":
    root = tk.Tk()
    app = JuegoApp(root) # control y Logica 
    root.mainloop()
