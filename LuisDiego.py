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



    
