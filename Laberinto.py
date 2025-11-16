# Mini prueba de mapa en Python
# 0 = muro (#)
# 1 = camino ( )
# 2 = liana (L)
# 3 = tunel (T)

MURO   = 0
CAMINO = 1
LIANA  = 2
TUNEL  = 3

mapa = [
    [0,0,0,0,0,0,0,0,0,0],
    [0,1,1,1,1,1,1,1,1,0],
    [0,1,2,0,0,0,0,0,1,0],
    [0,1,2,3,3,3,3,0,1,0],
    [0,1,2,0,0,0,0,0,1,0],
    [0,1,1,1,1,1,1,1,1,0],
    [0,0,0,0,0,0,0,0,0,0]
]

def simbolo(valor):
    if valor == MURO:   return "#"
    if valor == CAMINO: return " "
    if valor == LIANA:  return "L"
    if valor == TUNEL:  return "T"
    return "?"

def dibujar_mapa():
    for fila in mapa:
        linea = "".join(simbolo(v) for v in fila)
        print(linea)

if __name__ == "__main__":
    print("Mapa de prueba (7x10):\n")
    dibujar_mapa()

    print("\nLeyenda:")
    print("  # = muro")
    print("  C  = camino")
    print("  L = liana")
    print("  T = tunel")

    input("\nPresione ENTER para salir...")
