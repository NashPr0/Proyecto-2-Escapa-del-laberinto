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
    

    
