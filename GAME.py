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

MAX_ENERGIA = 10
COSTO_CORRER = 3
REGEN_ENERGIA = 1

MAX_TRAMPAS = 3
COOLDOWN_TRAMPA = 5.0
RESPAWN_ENEMIGO_SEG = 10.0

DURACION_PARTIDA_CAZADOR = 60
DURACION_PARTIDA_ESCAPA = 60

ARCHIVO_PUNTAJES_CAZADOR = "puntajes_cazador.txt"
ARCHIVO_PUNTAJES_ESCAPA = "puntajes_escapa.txt"

TAM_CELDA = 32

PLAYER_INTERVAL = 0.4  # base para calcular la velocidad

ANCHO_MAPA = 23
ALTO_MAPA = 15

TIEMPO_PREVIEW = 5.0

# UTILIDADES PUNTAJES

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

# MANEJO DE SONIDO

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

    #  utilidades internas 

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

    # efectos varios 

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

# MANEJO DE SPRITES

class SpriteManager:
    def __init__(self, root):
        base_dir = os.path.dirname(os.path.abspath(__file__))

        def load_gif(nombre):
            ruta = os.path.join(base_dir, nombre + ".gif")
            if os.path.exists(ruta):
                return tk.PhotoImage(master=root, file=ruta)
            return None

        def scale(img):
            if not img:
                return None
            w, h = img.width(), img.height()
            sx = max(1, w // TAM_CELDA)
            sy = max(1, h // TAM_CELDA)
            if sx > 1 or sy > 1:
                img = img.subsample(sx, sy)
            return img

        self.img_suelo = scale(load_gif("suelo"))
        self.img_muro = scale(load_gif("Muros"))
        self.img_liana = scale(load_gif("Lianas"))
        self.img_trampa = scale(load_gif("Trampas"))
        self.img_puerta = scale(load_gif("puerta"))
        self.img_jugador = scale(load_gif("Jugador"))
        self.img_tunel = scale(load_gif("Tunel"))

        self.img_enemigos = [
            scale(load_gif("enemigo1")),
            scale(load_gif("enemigo2")),
            scale(load_gif("enemigo3")),
            scale(load_gif("enemigo4")),
        ]

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
    def permite_jugador(self): return False   # solo enemigos
    def permite_enemigo(self): return True

class Tunel(Terreno):
    codigo = TUNEL
    def permite_jugador(self): return True    # solo jugador
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


# MAPA CON LABERINTO Y GARANTÍA DE CAMINO

class Mapa:
    def __init__(self, ancho, alto):
        self.ancho = ancho
        self.alto = alto
        self.m = [[MURO for _ in range(ancho)] for _ in range(alto)]

        # Entrada fija
        self.entrada = (alto - 2, 1)

        # Cuatro posibles salidas (centro de cada lado)
        self.salidas = [
            (1, ancho // 2),
            (alto - 2, ancho // 2),
            (alto // 2, 1),
            (alto // 2, ancho - 2),
        ]

        self._generar_laberinto()
        self._garantizar_camino_valido()
        self._colocar_terrenos_especiales()

    #  generación de laberinto (DFS) 
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

    # ------------ garantizar camino entre entrada y alguna salida ------------
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

        # si no hay camino, abrimos uno recto a una salida aleatoria
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

    #  colocar túneles y lianas útiles 
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
    #  consultas básicas 
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


# JUGADOR Y ENEMIGOS


class Jugador:
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


class Enemigo:
 

    def __init__(self, fila, col, sprite_index=0,
                 respawn_fila=None, respawn_col=None,
                 respawn_delay=RESPAWN_ENEMIGO_SEG):
        # Posición actual
        self.fila = fila
        self.col = col

        # Índice del sprite (0..3)
        self.sprite_index = sprite_index

        # Estado de vida
        self.vivo = True
        self.respawn_delay = respawn_delay
        self.tiempo_respawn = None

        # Punto base de respawn
        self.respawn_fila = respawn_fila if respawn_fila is not None else fila
        self.respawn_col = respawn_col if respawn_col is not None else col

        # Contador de atascos
        self.stuck = 0

        # Último lugar de respawn para no repetir siempre el mismo
        self._ultimo_respawn = (fila, col)

    # Utilidades básicas
    

    def posicion(self):
        return (self.fila, self.col)

    def matar(self, ahora):
        """Marca al enemigo como muerto y programa su respawn."""
        self.vivo = False
        self.tiempo_respawn = ahora + self.respawn_delay
        self.stuck = 0

    def intentar_revivir(self, ahora, mapa, sound_manager):
        """Si llegó la hora, revive al enemigo en una posición válida."""
        if not self.vivo and self.tiempo_respawn is not None and ahora >= self.tiempo_respawn:
            self.respawn_instantaneo(mapa, sound_manager)

    def respawn_instantaneo(self, mapa, sound_manager=None):
   
        alto, ancho = mapa.alto, mapa.ancho
        entrada = mapa.entrada
        min_dist_entrada = 5  # distancia mínima a la entrada

        candidatos = []

        # Intentamos primero alrededor de su punto base de respawn
        base_r, base_c = self.respawn_fila, self.respawn_col
        radios = [0, 1, 2, 3]

        for radio in radios:
            for dr in range(-radio, radio + 1):
                for dc in range(-radio, radio + 1):
                    r = base_r + dr
                    c = base_c + dc
                    if not (0 <= r < alto and 0 <= c < ancho):
                        continue
                    if not mapa.es_valido_enemigo(r, c):
                        continue
                    if (r, c) == entrada:
                        continue
                    if abs(r - entrada[0]) + abs(c - entrada[1]) < min_dist_entrada:
                        continue
                    if (r, c) == self._ultimo_respawn:
                        continue
                    candidatos.append((r, c))

        # Si no hay candidatos razonables, probamos aleatorio en todo el mapa
        if not candidatos:
            for _ in range(100):
                r = random.randint(1, alto - 2)
                c = random.randint(1, ancho - 2)
                if not mapa.es_valido_enemigo(r, c):
                    continue
                if abs(r - entrada[0]) + abs(c - entrada[1]) < min_dist_entrada:
                    continue
                if (r, c) == self._ultimo_respawn:
                    continue
                candidatos.append((r, c))
                break

        # Si aún así no hay, caemos de vuelta a su punto base (y si no es válido,
        # buscamos la primera casilla válida que encontremos).
        if not candidatos:
            r, c = base_r, base_c
            if not mapa.es_valido_enemigo(r, c):
                for _ in range(100):
                    rr = random.randint(1, alto - 2)
                    cc = random.randint(1, ancho - 2)
                    if mapa.es_valido_enemigo(rr, cc):
                        r, c = rr, cc
                        break
        else:
            r, c = random.choice(candidatos)

        self.fila, self.col = r, c
        self.vivo = True
        self.tiempo_respawn = None
        self.stuck = 0
        self._ultimo_respawn = (r, c)

        if sound_manager:
            sound_manager.play_robot_regeneracion()


    # IA para perseguir (modo ESCAPA)
    

    def mover_hacia(self, destino, mapa):
 
        if not self.vivo:
            return

        origen = self.posicion()
        df, dc = mapa.siguiente_paso_enemigo(origen, destino)

        if df == 0 and dc == 0:
            # No hay paso directo -> heurística local
            of, oc = origen
            df_mejor, dc_mejor = 0, 0
            dist_actual = abs(of - destino[0]) + abs(oc - destino[1])
            for dr, dc2 in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nf, nc = of + dr, oc + dc2
                if not mapa.es_valido_enemigo(nf, nc):
                    continue
                d = abs(nf - destino[0]) + abs(nc - destino[1])
                if d < dist_actual:
                    df_mejor, dc_mejor = dr, dc2
                    dist_actual = d

            if df_mejor != 0 or dc_mejor != 0:
                df, dc = df_mejor, dc_mejor

        if df == 0 and dc == 0:
            # Seguimos sin salida, contamos como atasco
            self.stuck += 1
            if self.stuck >= 10:
                dirs = [(-1, 0), (1, 0), (0, -1), (0, 1)]
                random.shuffle(dirs)
                for dr, dc2 in dirs:
                    nf, nc = self.fila + dr, self.col + dc2
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

    # IA para huir (modo CAZADOR cuando el jugador está cerca)
   

    def mover_huir(self, jugador_pos, mapa):
        """
        Mueve al enemigo tratando de alejarse del jugador.
        - Busca entre los 4 vecinos válidos el que deje más lejos al jugador.
        - Si está muy encerrado, usa un poco de aleatoriedad para no
          quedarse rebotando siempre en el mismo lugar.
        """
        if not self.vivo:
            return

        jr, jc = jugador_pos
        mejores = []
        mejor_dist = -1

        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = self.fila + dr, self.col + dc
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
        else:
            # No hay ningún movimiento que mejore: atasco
            self.stuck += 1
            if self.stuck >= 8:
                dirs = [(-1, 0), (1, 0), (0, -1), (0, 1)]
                random.shuffle(dirs)
                for dr, dc in dirs:
                    nr, nc = self.fila + dr, self.col + dc
                    if mapa.es_valido_enemigo(nr, nc):
                        self.fila, self.col = nr, nc
                        self.stuck = 0
                        break


# APLICACIÓN PRINCIPAL

class JuegoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Escapa del laberinto / Cazador")
        self.root.resizable(False, False)

        width = ANCHO_MAPA * TAM_CELDA
        height = ALTO_MAPA * TAM_CELDA + 80
        self._fixed_geometry = None
        self._center_root(width, height)

        self.sound = SoundManager()
        self.sound.play_bg_music()
        self.sprites = SpriteManager(root)

        base_dir = os.path.dirname(os.path.abspath(__file__))
        ruta_fondo = os.path.join(base_dir, "Fondo_Inicio.gif")
        self.img_fondo_inicio = None
        if os.path.exists(ruta_fondo):
            self.img_fondo_inicio = tk.PhotoImage(master=root, file=ruta_fondo)

        self.nombre_jugador = None

        self.mapa = None
        self.jugador = None
        self.enemigos = []
        self.trampas = []

        self.modo_actual = None
        self.running = False
        self.en_preview = False
        self.preview_fin = 0.0

        self.puntaje = 0
        self.tiempo_inicio = 0
        self.ultimo_mov_enemigos = 0.0

        self.salida_actual_escapa = None
        self.puertas_activas_cazador = []

        self.frame_menu_principal = tk.Frame(root, bg="#202020")
        self.frame_seleccion_modo = tk.Frame(root, bg="#202020")
        self.frame_juego = tk.Frame(root, bg="#000000")
        self.frame_puntajes = tk.Frame(root, bg="#202020")
        self.frame_creditos = tk.Frame(root, bg="#202020")

        self.canvas = tk.Canvas(
            self.frame_juego,
            width=ANCHO_MAPA * TAM_CELDA,
            height=ALTO_MAPA * TAM_CELDA,
            bg="black"
        )
        self.canvas.pack()

        info_bar = tk.Frame(self.frame_juego, bg="#000000")
        info_bar.pack(fill="x")

        self.lbl_info = tk.Label(info_bar, text="", bg="#000000", fg="white")
        self.lbl_info.pack(side="left", padx=5, pady=5)
        
        ###actualizacion final.

        self.btn_salir_juego = tk.Button(
            info_bar,
            text="volver al menu juego",
            command=self._wrap_button(self._volver_menu_principal)
        )
        self.btn_salir_juego.pack(side="right", padx=5) 

        self.btn_music = tk.Button(
            info_bar,
            text="Música: ON",
            command=self._toggle_music
        )
        self.btn_music.pack(side="right", padx=5)

        self.btn_volver_fin = tk.Button(
            self.frame_juego,
            text="Volver al menú",
            command=self._volver_menu_principal
        )

        self._construir_menu_principal()
        self._construir_seleccion_modo()
        self._construir_pantalla_puntajes()
        self._construir_pantalla_creditos()

        self.mostrar_frame(self.frame_menu_principal)

    #  util GUI 

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
        for f in [self.frame_menu_principal, self.frame_seleccion_modo,
                  self.frame_juego, self.frame_puntajes, self.frame_creditos]:
            f.pack_forget()
        frame.pack(fill="both", expand=True)

    def _wrap_button(self, action):
        def cmd():
            self.sound.play_boton()
            action()
        return cmd

    def _aplicar_fondo(self, frame):
        if self.img_fondo_inicio:
            lbl = tk.Label(frame, image=self.img_fondo_inicio)
            lbl.place(x=0, y=0, relwidth=1, relheight=1)

    # ----------------- construcción pantallas -----------------

    def _construir_menu_principal(self):
        f = self.frame_menu_principal
        self._aplicar_fondo(f)

        btn_salir = tk.Button(f, text="Salir", command=self._wrap_button(self.root.destroy))
        btn_salir.place(x=10, y=10)

        titulo = tk.Label(
            f,
            text="Proyecto 2: Laberinto",
            font=("Arial", 24, "bold"),
            bg="#202020",
            fg="white"
        )
        titulo.place(relx=0.5, rely=0.18, anchor="center")

        cont = tk.Frame(f, bg="#202020")
        cont.place(relx=0.5, rely=0.5, anchor="center")

        tk.Button(cont, text="Jugar", width=20,
                  command=self._wrap_button(self._accion_jugar)).pack(pady=10)
        tk.Button(cont, text="Puntajes", width=20,
                  command=self._wrap_button(self._accion_puntajes)).pack(pady=10)
        tk.Button(cont, text="Créditos", width=20,
                  command=self._wrap_button(self._accion_creditos)).pack(pady=10)
        
        # boton de sonido

        sound_bar = tk.Frame(f, bg="#202020")
        sound_bar.place(x=10, rely=0.9, relheight=0.1, anchor="sw", relx=0.0)

        tk.Button(sound_bar, text="Música ON/OFF",
                  command=self._wrap_button(self._toggle_music)).pack(side="left", padx=5)

        tk.Button(sound_bar, text="Vol +",
                  command=lambda: self.sound.adjust_volume(+0.1)).pack(side="left", padx=5)

        tk.Button(sound_bar, text="Vol -",
                  command=lambda: self.sound.adjust_volume(-0.1)).pack(side="left", padx=5)

    def _construir_seleccion_modo(self):
        f = self.frame_seleccion_modo
        self._aplicar_fondo(f)

        titulo = tk.Label(
            f,
            text="Seleccione modo de juego",
            font=("Arial", 20, "bold"),
            bg="#202020",
            fg="white"
        )
        titulo.pack(pady=30)

        tk.Button(
            f, text="Modo Cazador", width=20,
            command=self._wrap_button(lambda: self.iniciar_modo("cazador"))
        ).pack(pady=10)

        tk.Button(
            f, text="Modo Escapa", width=20,
            command=self._wrap_button(lambda: self.iniciar_modo("escapa"))
        ).pack(pady=10)

        tk.Button(
            f, text="Volver", width=12,
            command=self._wrap_button(self._volver_menu_principal)
        ).pack(pady=20)

    def _construir_pantalla_puntajes(self):
        f = self.frame_puntajes
        self._aplicar_fondo(f)

        titulo = tk.Label(
            f,
            text="Puntajes",
            font=("Arial", 18, "bold"),
            bg="#202020",
            fg="white"
        )
        titulo.pack(pady=10)

        self.txt_puntajes = tk.Text(f, width=60, height=20, state="disabled")
        self.txt_puntajes.pack(pady=10)

        self.entry_nombre_stats = tk.Entry(f)
        self.entry_nombre_stats.pack(pady=5)
        tk.Button(
            f,
            text="Ver estadísticas de jugador",
            command=self._wrap_button(self._mostrar_stats_jugador)
        ).pack(pady=5)

        tk.Button(
            f,
            text="Volver al menú",
            width=20,
            command=self._wrap_button(self._volver_menu_principal)
        ).pack(pady=10)

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

        tk.Label(col1, text="Montiel López Anthony", font=("Arial", 16),
                 bg="#202020", fg="white").pack()
        tk.Label(col1, text="Carne: 2025132603",
                 bg="#202020", fg="white").pack()
        tk.Label(col1, text="Carrera: Ing. en Computadores",
                 bg="#202020", fg="white").pack()
        tk.Label(col1, text="Curso: Intro a la Programación",
                 bg="#202020", fg="white").pack()

        col2 = tk.Frame(contenedor, bg="#202020")
        col2.grid(row=0, column=1, padx=40)

        tk.Label(col2, text="Murillo Luis Diego", font=("Arial", 16),
                 bg="#202020", fg="white").pack()
        tk.Label(col2, text="Carne: 2025069058",
                 bg="#202020", fg="white").pack()
        tk.Label(col2, text="Carrera: Ing. en Computadores",
                 bg="#202020", fg="white").pack()
        tk.Label(col2, text="Curso: Intro a la Programación",
                 bg="#202020", fg="white").pack()

    #  acciones de menú 

    def _accion_jugar(self):
        if not self.nombre_jugador:
            nombre = simpledialog.askstring("Registro", "Ingrese su nombre de jugador:")
            if not nombre:
                return
            self.nombre_jugador = nombre.strip()
        self.mostrar_frame(self.frame_seleccion_modo)

    def _accion_puntajes(self):
        self.mostrar_frame(self.frame_puntajes)
        self._actualizar_texto_puntajes()

    def _accion_creditos(self):
        self.mostrar_frame(self.frame_creditos)

    def _volver_menu_principal(self):
        self.running = False
        self.mostrar_frame(self.frame_menu_principal)

    def _toggle_music(self):
        self.sound.toggle_bg_music()
        self.btn_music.config(text=f"Música: {'ON' if self.sound.bg_playing else 'OFF'}")
    
    def _salir_del_juego(self):
        """Salir completamente del juego desde modo cazador / escapa."""
        try:
            self.sound.stop_bg_music()
        except Exception:
            pass
        self.root.destroy()  # cierra la ventana principal

    # spawns y modos 

    def _corner_positions(self):
        entrada = self.mapa.entrada
        cr = self.mapa.alto // 2
        cc = self.mapa.ancho // 2
        candidatos = [
            (cr - 2, cc - 2),
            (cr - 2, cc + 2),
            (cr + 2, cc - 2),
            (cr + 2, cc + 2),
        ]
        posiciones = []
        for f, c in candidatos:
            if not (0 <= f < self.mapa.alto and 0 <= c < self.mapa.ancho):
                continue
            if (f, c) == entrada:
                continue
            if self.mapa.es_valido_enemigo(f, c):
                if abs(f - entrada[0]) + abs(c - entrada[1]) >= 7:
                    posiciones.append((f, c))
        return posiciones

    def _spawn_en_corners(self, cantidad):
        corners = self._corner_positions()
        random.shuffle(corners)
        return corners[:cantidad]

    def iniciar_modo(self, modo):
        self.modo_actual = modo
        self.mapa = Mapa(ANCHO_MAPA, ALTO_MAPA)

        ef, ec = self.mapa.entrada
        self.jugador = Jugador(ef, ec)

        cantidad = simpledialog.askinteger(
            "Configuración",
            "¿Cuántos cazadores/NPC deseas? (1 - 4)",
            minvalue=1,
            maxvalue=4
        )
        if not cantidad:
            self._volver_menu_principal()
            return
        self.cantidad_enemigos = cantidad

        self.enemigos = []

        if modo == "escapa":
            # una única salida activa
            self.salida_actual_escapa = random.choice(self.mapa.salidas)
            nuevas_salidas = [self.salida_actual_escapa]
            for sf, sc in self.mapa.salidas:
                if (sf, sc) != self.salida_actual_escapa:
                    self.mapa.m[sf][sc] = MURO
            self.mapa.salidas = nuevas_salidas
            sf, sc = self.salida_actual_escapa
            self.mapa.m[sf][sc] = SALIDA

            self.puertas_activas_cazador = []
            spawn_positions = self._spawn_en_corners(self.cantidad_enemigos)
            for i, (f, c) in enumerate(spawn_positions):
                self.enemigos.append(
                    Enemigo(f, c, sprite_index=i % 4,
                            respawn_fila=f, respawn_col=c,
                            respawn_delay=RESPAWN_ENEMIGO_SEG)
                )
        else:
            # --- MODO CAZADOR: número de puertas = número de NPCs ---
            todas_salidas = list(self.mapa.salidas)
            # primero todo se vuelve muro
            for sr, sc in todas_salidas:
                self.mapa.m[sr][sc] = MURO

            k = min(self.cantidad_enemigos, len(todas_salidas))
            self.puertas_activas_cazador = random.sample(todas_salidas, k=k)

            # estas son las únicas salidas activas
            for sr, sc in self.puertas_activas_cazador:
                self.mapa.m[sr][sc] = SALIDA

            self.mapa.salidas = list(self.puertas_activas_cazador)
            self.salida_actual_escapa = None

            spawn_positions = self._spawn_en_corners(self.cantidad_enemigos)
            for i, (f, c) in enumerate(spawn_positions):
                self.enemigos.append(
                    Enemigo(f, c, sprite_index=i % 4,
                            respawn_fila=f, respawn_col=c,
                            respawn_delay=RESPAWN_ENEMIGO_SEG)
                )

        self.trampas = []
        self.ultimo_tiempo_trampa = 0.0

        self.puntaje = 0
        self.tiempo_inicio = 0.0

        self.en_preview = True
        self.preview_fin = time.time() + TIEMPO_PREVIEW
        self.ultimo_mov_enemigos = time.time()

        self.running = True
        self.mostrar_frame(self.frame_juego)
        self.btn_volver_fin.pack_forget()

        self.root.bind("<KeyPress>", self._on_key_press)
        self._loop_juego()

    #  teclado 

    def _on_key_press(self, event):
        if not self.running or self.en_preview:
            return

        tecla = event.keysym
        df, dc = 0, 0
        if tecla == "Up":
            df, dc = -1, 0
        elif tecla == "Down":
            df, dc = 1, 0
        elif tecla == "Left":
            df, dc = 0, -1
        elif tecla == "Right":
            df, dc = 0, 1
        elif tecla.lower() == "z":
            if self.modo_actual == "escapa":
                self.colocar_trampa()
            return
        else:
            return

        corriendo = (event.state & 0x0001) != 0
        if self.jugador.mover(df, dc, self.mapa, corriendo=corriendo):
            self.sound.play_jugador_caminar()

    def colocar_trampa(self):
        if self.modo_actual != "escapa":
            return
        ahora = time.time()
        if len(self.trampas) >= MAX_TRAMPAS:
            return
        if ahora - self.ultimo_tiempo_trampa < COOLDOWN_TRAMPA:
            return
        pos = self.jugador.posicion()
        r, c = pos
        if self.mapa.m[r][c] == SALIDA:
            return
        if pos not in self.trampas:
            self.trampas.append(pos)
            self.ultimo_tiempo_trampa = ahora

    #  loop principal 

    def _loop_juego(self):
        if not self.running:
            return

        ahora = time.time()

        if self.en_preview:
            if ahora >= self.preview_fin:
                self.en_preview = False
                self.tiempo_inicio = ahora
                self.lbl_info.config(
                    text=f"Modo: {self.modo_actual.capitalize()} | "
                         f"Jugador: {self.nombre_jugador} | "
                         f"Energía: {self.jugador.energia}"
                )
            else:
                restante = int(self.preview_fin - ahora)
                modo_txt = "Cazador" if self.modo_actual == "cazador" else "Escapa"
                self.lbl_info.config(
                    text=f"Modo: {modo_txt} | Observa el mapa. "
                         f"El juego inicia en {restante} s"
                )
                self._dibujar()
                self.root.after(160, self._loop_juego)
                return

        if self.modo_actual == "cazador":
            self._update_modo_cazador(ahora)
        else:
            self._update_modo_escapa(ahora)

        self._dibujar()
        self.root.after(160, self._loop_juego)

    #  ayuda para puertas 

    def _puerta_mas_cercana(self, pos, jugador_pos=None):
        if not self.puertas_activas_cazador:
            return None

        puertas = list(self.puertas_activas_cazador)

        if jugador_pos is not None:
            jf, jc = jugador_pos
            filtradas = [
                p for p in puertas
                if abs(p[0] - jf) + abs(p[1] - jc) > 1
            ]
            if filtradas:
                puertas = filtradas

        f, c = pos
        return min(puertas, key=lambda p: abs(p[0] - f) + abs(p[1] - c))

    #  lógica modo cazador 

    def _update_modo_cazador(self, ahora):
        tiempo_transc = ahora - self.tiempo_inicio
        restante = max(0, DURACION_PARTIDA_CAZADOR - int(tiempo_transc))

        for enemigo in self.enemigos:
            enemigo.intentar_revivir(ahora, self.mapa, self.sound)

        # velocidad de enemigos (boost inicial 200%, después 75%)
        if ahora - self.tiempo_inicio < 3:
            factor_vel = 2.0
        else:
            factor_vel = 0.75

        intervalo = PLAYER_INTERVAL / factor_vel

        if ahora - self.ultimo_mov_enemigos >= intervalo:
            self.ultimo_mov_enemigos = ahora
            jf, jc = self.jugador.posicion()

            for enemigo in self.enemigos:
                if not enemigo.vivo:
                    continue

                puerta = self._puerta_mas_cercana(enemigo.posicion(), (jf, jc))
                if not puerta:
                    continue

                dist_jugador = abs(enemigo.fila - jf) + abs(enemigo.col - jc)
                if dist_jugador <= 2:
                    enemigo.mover_huir((jf, jc), self.mapa)
                else:
                    enemigo.mover_hacia(puerta, self.mapa)

                self.sound.play_robot_caminar()

                if enemigo.posicion() in self.puertas_activas_cazador:
                    self.puntaje -= 50
                    enemigo.respawn_instantaneo(self.mapa, self.sound)

        for enemigo in self.enemigos:
            if enemigo.vivo and enemigo.posicion() == self.jugador.posicion():
                self.puntaje += 100
                self.sound.play_robot_muerte()
                enemigo.respawn_instantaneo(self.mapa, self.sound)

        if restante <= 0:
            gano = self.puntaje > 0
            self._fin_partida(gano, tiempo_transc)

        self.lbl_info.config(
            text=f"Modo: Cazador | Jugador: {self.nombre_jugador} | "
                 f"Puntaje: {self.puntaje} | "
                 f"Energía: {self.jugador.energia} | "
                 f"Tiempo restante: {restante}s"
        )

    # lógica modo escapa 

    def _update_modo_escapa(self, ahora):
        tiempo_transc = ahora - self.tiempo_inicio
        tiempo_restante = max(0, DURACION_PARTIDA_ESCAPA - int(tiempo_transc))

        jf, jc = self.jugador.posicion()

        for enemigo in self.enemigos:
            enemigo.intentar_revivir(ahora, self.mapa, self.sound)

        intervalo = PLAYER_INTERVAL
        if ahora - self.ultimo_mov_enemigos >= intervalo:
            self.ultimo_mov_enemigos = ahora

            for enemigo in self.enemigos:
                if not enemigo.vivo:
                    continue
                enemigo.mover_hacia((jf, jc), self.mapa)
                self.sound.play_robot_caminar()

        # trampas (solo modo escapa)
        trampas_a_eliminar = []
        for tpos in self.trampas:
            for enemigo in self.enemigos:
                if enemigo.vivo and enemigo.posicion() == tpos:
                    self.puntaje += 100
                    self.sound.play_robot_muerte()
                    enemigo.matar(ahora)
                    trampas_a_eliminar.append(tpos)
                    self.ultimo_tiempo_trampa = ahora
                    break
        for tpos in trampas_a_eliminar:
            if tpos in self.trampas:
                self.trampas.remove(tpos)

        if self.jugador.posicion() in self.trampas:
            self.sound.play_jugador_muerte()
            self._fin_partida(False, int(tiempo_transc))
            return

        for enemigo in self.enemigos:
            if enemigo.vivo and enemigo.posicion() == self.jugador.posicion():
                self.sound.play_jugador_muerte()
                self._fin_partida(False, int(tiempo_transc))
                return

        if self.salida_actual_escapa and self.jugador.posicion() == self.salida_actual_escapa:
            segundos = max(1, int(tiempo_transc))
            puntaje_base = 100 * (0.9 ** (segundos - 1))
            self.puntaje += int(puntaje_base)
            self._fin_partida(True, int(tiempo_transc))
            return

        if tiempo_restante <= 0:
            self._fin_partida(False, int(tiempo_transc))
            return

        self.lbl_info.config(
            text=f"Modo: Escapa | Jugador: {self.nombre_jugador} | "
                 f"Puntaje: {self.puntaje} | Energía: {self.jugador.energia} | "
                 f"Tiempo restante: {tiempo_restante}s"
        )

    # fin de partida 

    def _fin_partida(self, gano, tiempo_total):
        self.running = False

        if self.modo_actual == "cazador":
            archivo = ARCHIVO_PUNTAJES_CAZADOR
        else:
            archivo = ARCHIVO_PUNTAJES_ESCAPA

        guardar_puntaje(
            self.nombre_jugador,
            self.modo_actual,
            self.puntaje,
            gano,
            tiempo_total,
            archivo
        )

        if gano:
            self.sound.play_ganar()
        else:
            self.sound.play_perder()

        resultado = "GANASTE" if gano else "PERDISTE"
        messagebox.showinfo(
            "Fin de partida",
            f"{resultado}\n\nPuntaje: {self.puntaje}\nTiempo: {int(tiempo_total)} s"
        )

        self.btn_volver_fin.pack(pady=10)

    # dibujo 

    def _dibujar(self):
        self.canvas.delete("all")

        for f in range(self.mapa.alto):
            for c in range(self.mapa.ancho):
                casilla = self.mapa.casilla(f, c)
                x = c * TAM_CELDA
                y = f * TAM_CELDA

                if isinstance(casilla, Muro):
                    if self.sprites.img_muro:
                        self.canvas.create_image(x, y, image=self.sprites.img_muro, anchor="nw")
                    else:
                        self.canvas.create_rectangle(
                            x, y, x + TAM_CELDA, y + TAM_CELDA,
                            fill="black", outline="#303030"
                        )
                elif isinstance(casilla, Camino):
                    if self.sprites.img_suelo:
                        self.canvas.create_image(x, y, image=self.sprites.img_suelo, anchor="nw")
                    else:
                        self.canvas.create_rectangle(
                            x, y, x + TAM_CELDA, y + TAM_CELDA,
                            fill="white", outline="#303030"
                        )
                elif isinstance(casilla, Tunel):
                    if self.sprites.img_tunel:
                        self.canvas.create_image(x, y, image=self.sprites.img_tunel, anchor="nw")
                    elif self.sprites.img_suelo:
                        self.canvas.create_image(x, y, image=self.sprites.img_suelo, anchor="nw")
                    else:
                        self.canvas.create_rectangle(
                            x, y, x + TAM_CELDA, y + TAM_CELDA,
                            fill="#0000ff", outline="#303030"  # azul
                        )
                elif isinstance(casilla, Liana):
                    if self.sprites.img_muro:
                        self.canvas.create_image(x, y, image=self.sprites.img_muro, anchor="nw")
                    else:
                        self.canvas.create_rectangle(
                            x, y, x + TAM_CELDA, y + TAM_CELDA,
                            fill="black", outline="#303030"
                        )
                    if self.sprites.img_liana:
                        self.canvas.create_image(x, y, image=self.sprites.img_liana, anchor="nw")
                elif isinstance(casilla, Salida):
                    if self.sprites.img_puerta:
                        self.canvas.create_image(x, y, image=self.sprites.img_puerta, anchor="nw")
                    elif self.sprites.img_suelo:
                        self.canvas.create_image(x, y, image=self.sprites.img_suelo, anchor="nw")
                    else:
                        self.canvas.create_rectangle(
                            x, y, x + TAM_CELDA, y + TAM_CELDA,
                            fill="#ffff00", outline="#303030"  # amarillo
                        )

                if isinstance(casilla, Salida):
                    color_marco = "#ffff00"
                    if self.modo_actual == "escapa":
                        if (f, c) != self.salida_actual_escapa:
                            color_marco = "#808080"
                    else:
                        if (f, c) not in self.puertas_activas_cazador:
                            color_marco = "#808080"
                    self.canvas.create_rectangle(
                        x + 2, y + 2, x + TAM_CELDA - 2, y + TAM_CELDA - 2,
                        outline=color_marco, width=3
                    )

        ef, ec = self.mapa.entrada
        x = ec * TAM_CELDA
        y = ef * TAM_CELDA
        if self.sprites.img_puerta:
            self.canvas.create_image(x, y, image=self.sprites.img_puerta, anchor="nw")
        else:
            self.canvas.create_rectangle(
                x + 3, y + 3, x + TAM_CELDA - 3, y + TAM_CELDA - 3,
                outline="#ffff00", width=2
            )

        for (f, c) in self.trampas:
            x = c * TAM_CELDA
            y = f * TAM_CELDA
            if self.sprites.img_trampa:
                self.canvas.create_image(x, y, image=self.sprites.img_trampa, anchor="nw")
            else:
                self.canvas.create_rectangle(
                    x + 8, y + 8, x + TAM_CELDA - 8, y + TAM_CELDA - 8,
                    fill="#ff8800", outline="black"
                )

        jf, jc = self.jugador.posicion()
        x = jc * TAM_CELDA
        y = jf * TAM_CELDA
        if self.sprites.img_jugador:
            self.canvas.create_image(x, y, image=self.sprites.img_jugador, anchor="nw")
        else:
            self.canvas.create_oval(
                x + 4, y + 4, x + TAM_CELDA - 4, y + TAM_CELDA - 4,
                fill="#8000ff", outline="white", width=2   # morado
            )

        for enemigo in self.enemigos:
            if not enemigo.vivo:
                continue
            ef, ec = enemigo.posicion()
            x = ec * TAM_CELDA
            y = ef * TAM_CELDA
            sprite = None
            if 0 <= enemigo.sprite_index < len(self.sprites.img_enemigos):
                sprite = self.sprites.img_enemigos[enemigo.sprite_index]
            if sprite:
                self.canvas.create_image(x, y, image=sprite, anchor="nw")
            else:
                self.canvas.create_rectangle(
                    x + 8, y + 8, x + TAM_CELDA - 8, y + TAM_CELDA - 8,
                    fill="red", outline="black", width=2
                )

    # puntajes pantalla 

    def _mostrar_stats_jugador(self):
        nombre = self.entry_nombre_stats.get().strip()
        if not nombre:
            messagebox.showwarning("Atención", "Debe escribir un nombre.")
            return

        stats_escapa = stats_por_jugador(nombre, ARCHIVO_PUNTAJES_ESCAPA)
        stats_cazador = stats_por_jugador(nombre, ARCHIVO_PUNTAJES_CAZADOR)

        texto = f"Estadísticas para {nombre}:\n\n"

        if stats_escapa:
            texto += (
                f"Modo Escapa:\n"
                f"  Partidas: {stats_escapa['total']}\n"
                f"  Ganadas: {stats_escapa['ganadas']}\n"
                f"  Mejor puntaje: {stats_escapa['mejor_puntaje']}\n"
                f"  Mejor tiempo: {stats_escapa['mejor_tiempo']} s\n\n"
            )
        else:
            texto += "Modo Escapa:\n  Sin registros.\n\n"

        if stats_cazador:
            texto += (
                f"Modo Cazador:\n"
                f"  Partidas: {stats_cazador['total']}\n"
                f"  Ganadas: {stats_cazador['ganadas']}\n"
                f"  Mejor puntaje: {stats_cazador['mejor_puntaje']}\n"
                f"  Mejor tiempo: {stats_cazador['mejor_tiempo']} s\n\n"
            )
        else:
            texto += "Modo Cazador:\n  Sin registros.\n\n"

        messagebox.showinfo("Estadísticas", texto)

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


# MAIN

if __name__ == "__main__":
    root = tk.Tk()
    app = JuegoApp(root)
    root.mainloop()
