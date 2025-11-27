
#CONSTANTES DE JUGADOR Y ENEMIGOS
MAX_ENERGIA = 10
COSTO_CORRER = 3
REGEN_ENERGIA = 1

MAX_TRAMPAS = 3
COOLDOWN_TRAMPA = 5.0
RESPAWN_ENEMIGO_SEG = 10.0

DURACION_PARTIDA_CAZADOR = 60
DURACION_PARTIDA_ESCAPA = 60

PLAYER_INTERVAL = 0.4  # base para calcular la velocidad


class jugador:
    def __init__(self, fila, col):
        self.fila = fila
        self.col = col
        self.energia = MAX_ENERGIA
        
    def posicion(self):
        return(self.fila, self.col)
    
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
    """Esta clase se usa
    para los dos modos, modo escapa y modo cazador.
    La lógica de cuando persigue o huye está en JuegoApp,
    aquí solo está el cómo se mueve y revive.
    """
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

        #Utilidades básicas    

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
        """
        Revive al enemigo en una casilla válida del mapa.
        Reglas:
          - No respawnea pegado a la entrada (para no bloquear al jugador).
          - No respawnea EXACTAMENTE en el mismo punto anterior.
          - Solo usa casillas válidas para enemigos.
        """
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
    
    #IA QUE PERSIGUE AL JUGADOR (MODO ESCAPA)
    def mover_hacia(self, destino, mapa):
        if not self.vivo:
            return

        origen = self.posicion()
        df, dc = mapa.siguiente_paso_enemigo(origen, destino)

        if df == 0 and dc == 0:

            of, oc = origen
            mejor_df, mejor_dc = 0, 0
            dist_actual = abs(of - destino[0]) + abs(oc - destino[1])

            for dr, dc2 in [(-1,0),(1,0),(0,-1),(0,1)]:
                nf = of + dr
                nc = oc + dc2
                if not mapa.es_valido_enemigo(nf, nc):
                    continue
                dist = abs(nf - destino[0]) + abs(nc - destino[1])
                if dist < dist_actual:
                    mejor_df, mejor_dc = dr, dc2
                    dist_actual = dist

            if mejor_df != 0 or mejor_dc != 0:
                df, dc = mejor_df, mejor_dc
        if df == 0 and dc == 0:
            self.stuck += 1

            if self.stuck >= 10:
                dirs = [(-1,0),(1,0),(0,-1),(0,1)]
                random.shuffle(dirs)
                for dr, dc2 in dirs:
                    nf = self.fila + dr
                    nc = self.col + dc2
                    if mapa.es_valido_enemigo(nf, nc):
                        self.fila = nf
                        self.col = nc
                        self.stuck = 0
                        return
            return
        
        nf = self.fila + df
        nc = self.col + dc

        if mapa.es_valido_enemigo(nf, nc):
            self.fila = nf
            self.col = nc
            self.stuck = 0
        else:
            self.stuck += 1

    #IA para huir (MODOD ESCAPA)
    def mover_huir(self, jugador_pos, mapa):

        if not self.vivo:
            return

        jr, jc = jugador_pos
        mejor_dist = -1
        mejores = []

        # buscar casilla que lo deje MÁS LEJOS del jugador
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
        else:
            # movimiento aleatorio para evitar atasco
            self.stuck += 1
            if self.stuck >= 8:
                dirs = [(-1,0),(1,0),(0,-1),(0,1)]
                random.shuffle(dirs)
                for dr, dc in dirs:
                    nr = self.fila + dr
                    nc = self.col + dc
                    if mapa.es_valido_enemigo(nr, nc):
                        self.fila = nr
                        self.col = nc
                        self.stuck = 0
                        break

 

   

class JuegoApp:
   def __init__(self, mapa, sound_manager, modo):
        self.mapa = mapa
        self.sound = sound_manager
        self.modo = modo.lower()  
        er, ec = self.mapa.entrada
        self.player = jugador(er, ec)
        self.enemigos = self._spawn_enemigos(4)
        self.tiempo_inicio = time.time()
        





    

 



    
