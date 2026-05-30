from ursina import *
from itertools import *
import heapq
import random


#El estado objetivo contiene una tupla de acuerdo a los 9 stickers que contiene cada cara
#Del 0 al 9 es una cara que en este caso 
ESTADO_OBJETIVO = tuple([0]*9 + [1]*9 + [2]*9 + [3]*9 + [4]*9 + [5]*9)
estado_global_ia = ESTADO_OBJETIVO

# Son las permutaciones posibles de cada pegatina, son las posiciones de cada cara,
# U es para el TOP osea la cara blanca
# D es para el DOWN osea la cara amarilla
# F es para el FRONT osea la cara roja
# B es para el BACK osea la cara naranja
# L es para el LEFT osea la cara verde
# R es para el RIGHT osea la cara azul

PERMUTACIONES_BASE = {
    'U': [(0,2,8,6), (1,5,7,3), (18,27,36,9), (19,28,37,10), (20,29,38,11)],
    'D': [(45,47,53,51), (46,50,52,48), (24,15,42,33), (25,16,43,34), (26,17,44,35)],
    'F': [(18,20,26,24), (19,23,25,21), (6,27,47,17), (7,30,46,14), (8,33,45,11)],
    'B': [(36,38,44,42), (37,41,43,39), (2,9,51,35), (1,12,52,32), (0,15,53,29)],
    'L': [(9,11,17,15), (10,14,16,12), (0,18,45,44), (3,21,48,41), (6,24,51,38)],
    'R': [(27,29,35,33), (28,32,34,30), (8,36,53,26), (5,39,50,23), (2,42,47,20)]
}

MOVIMIENTOS = {
    'U': ('y', 1, 90), "U'": ('y', 1, -90),
    'D': ('y', -1, -90), "D'": ('y', -1, 90),
    'F': ('z', -1, 90), "F'": ('z', -1, -90),
    'B': ('z', 1, -90), "B'": ('z', 1, 90),
    'R': ('x', 1, 90), "R'": ('x', 1, -90),
    'L': ('x', -1, -90), "L'": ('x', -1, 90)
}

MOVES = {}
for m, ciclos in PERMUTACIONES_BASE.items():
    MOVES[m] = ciclos
    MOVES[m + "'"] = [(d, c, b, a) for a, b, c, d in ciclos]
    
def rotar_matriz(estado, accion):
    nuevo_estado = list(estado)
    for a, b, c, d in MOVES[accion]:
        nuevo_estado[a], nuevo_estado[b], nuevo_estado[c], nuevo_estado[d] = \
        nuevo_estado[d], nuevo_estado[a], nuevo_estado[b], nuevo_estado[c]
    return tuple(nuevo_estado)
    
class NodoArbol:
    def __init__(self, estado, padre=None, accion=None, g=0):
        self.estado = estado
        self.padre = padre
        self.accion = accion
        self.g = g          
        
        # El nodo calcula su propia heurística al nacer
        self.h = self.heuristica()
        self.f = self.g + self.h 

    def __lt__(self, otro): 
        return self.f < otro.f

    def heuristica(self):
        """Método de instancia: El nodo se evalúa a sí mismo"""
        mal_colocadas = sum(1 for i in range(54) if self.state_match(i))
        return mal_colocadas // 8

    def state_match(self, i):
        return self.estado[i] != ESTADO_OBJETIVO[i]

    def generar_hijos(self):
        """El nodo genera sus propios descendientes"""
        hijos = []
        # MOVES contiene el diccionario de permutaciones de la matriz
        for accion in MOVES.keys():
            #Evitar deshacer el paso inmediato del padre
            if self.padre and (accion == self.accion + "'" or self.accion == accion + "'"):
                continue
                
            estado_hijo = rotar_matriz(self.estado, accion)
            # Pasamos 'self' como el padre del nuevo nodo
            nuevo_hijo = NodoArbol(estado_hijo, padre=self, accion=accion, g=self.g + 1)
            hijos.append(nuevo_hijo)
        return hijos
    
def a_estrella(estado_inicial):
    nodo_raiz = NodoArbol(estado_inicial)
    frontera = []
    heapq.heappush(frontera, nodo_raiz)
    
    nodos_expandidos = 0

    while frontera and nodos_expandidos < 500000: #Pongo como limite 500000 para que no me explote la compu
        nodo_actual = heapq.heappop(frontera)
        nodos_expandidos += 1

        if nodo_actual.h == 0: 
            print(f"Nodos explorados: {nodos_expandidos}")
            camino = []
            while nodo_actual.padre:
                camino.append(nodo_actual.accion)
                nodo_actual = nodo_actual.padre
            return camino[::-1]

        for nodo_hijo in nodo_actual.generar_hijos():
            heapq.heappush(frontera, nodo_hijo)
            
    print("Limite del arbol.")
    return None

def iniciar():

    app = Ursina(title='CUBO RUBIK 3D', development_mode=False, size=(1700,1000), color=color.gray, borderless=False)
    EditorCamera()

    #Por qué -1, 0 y 1?. Debido a las posiciones de cada pieza. Está centrado de acuerdo al mapa 3D que genera la libreria URSINA que está en 0,0,0. Nos servirá centrarlo para poder realizar las rotaciones de manera más eficiente más adelante
    # El 0 representa la posición central
    # El -1 representa la posición hacia atras, izquierda o abajo
    # El 1 representa la posición hacia adelante, derecha o arriba

    cubes = [] # Necesitamos de una lista para contener todos los cubos en un espacio predefinido
    dist_stick = 0.55 # Variable que usaremos para las distancias entre cada pegatina o sticker
    tam_stick = (0.85, 0.85) # Variable que usaremos para el tamaño de cada sticker, en este caso son 2D por lo que solo necesitamos x, y
    pivote = Entity() #Creamos una entidad para que sea el centro de las rotaciones
    animacion = False #Variable que nos ayudará a saber si hay una animación en curso
    duracion_giro = 0.2 # Variable que usaremos para la duración de cada giro
    
    #Asiganamos los colores correspondientes a cada caro del cubo, siempre usando la función Entity para poder mostrar la entidad visualmente
    for x,y,z in product((-1,0,1), repeat=3):
        cube = Entity(model='cube', color=color.black, position=(x,y,z) ,scale=0.95)
        
        def numero_cara(color_cara, pos, rot, offset, fila, col):
            #Creamos la entidad del numero que será el que despues pegaremos sobre las pegatinas en los colores correspondientes
            p = Entity(parent=cube, model='quad', color=color_cara, position=pos, rotation=rot, scale=tam_stick)
            
            #Indice para calcular la posicion de la pegatina
            indice = offset + (fila*3) + col
            
            #Pegamos el numero encima de la pegatina
            Text(parent=p, text=str(indice), origin=(0,0), z=-0.01, color=color.black, scale=8)
        
        if y == 1:  numero_cara(color.white,  (0, dist_stick, 0), (90, 0, 0),   0, 1 - z, x + 1) # Cara blanca
        if x == -1: numero_cara(color.green,  (-dist_stick, 0, 0), (0, 90, 0),   9, 1 - y, 1 - z) # Cara verde
        if z == -1: numero_cara(color.red,    (0, 0, -dist_stick), (0, 0, 0),   18, 1 - y, x + 1) # Cara roja
        if x == 1:  numero_cara(color.blue,   (dist_stick, 0, 0), (0, -90, 0),  27, 1 - y, z + 1) # Cara azul
        if z == 1:  numero_cara(color.orange, (0, 0, dist_stick), (0, 180, 0),  36, 1 - y, 1 - x) # Cara naranja
        if y == -1: numero_cara(color.yellow, (0, -dist_stick, 0), (-90, 0, 0), 45, z + 1, x + 1) # Cara amarilla
        cubes.append(cube) 
        
        # De ambas formas es lógicamente bien
        # Por qué?, Gracias a la biblioteca itertools.product tenemos que la función product genera el producto cartesiano que basicamente
        # es la combinación de todos los arreglos posibles entre los conjuntos, el -1,0,1 es el mismo recorrido que se haría en cada uno de los ciclos anidados que va de -1 a 1, ya que el limite superior nunca se toma y con la instrucción repeat pues lo repite n veces que se desee, la biblioteca fue creada para eliminar ciclos anidados y en general para simplificar iteraciones engorrosas
        ''' for x in range(-1,2):
            for y in range(-1,2):
                for z in range(-1,2):
        '''
    
    def girar(movimiento):
        nonlocal animacion
        if animacion: return
        animacion = True
        
        eje, valor_eje, angulo = MOVIMIENTOS[movimiento]
        pivote.rotation = (0,0,0)
        piezas_cara = []

        for c in cubes:
            x,y,z = round(c.world_x), round(c.world_y), round(c.world_z)
            
            if eje == 'x' and x == valor_eje: piezas_cara.append(c)
            elif eje == 'y' and y == valor_eje: piezas_cara.append(c)
            elif eje == 'z' and z == valor_eje: piezas_cara.append(c)
        
        for p in piezas_cara:
            p.parent = pivote
        
        if eje == 'x': pivote.animate_rotation_x(angulo, duration=duracion_giro)
        elif eje == 'y': pivote.animate_rotation_y(angulo, duration=duracion_giro)
        elif eje == 'z': pivote.animate_rotation_z(angulo, duration=duracion_giro)
        
        def terminar_giro():
            nonlocal animacion
            for p in piezas_cara:
                p.world_parent = scene
                p.x = round(p.x)
                p.y = round(p.y)
                p.z = round(p.z)
                
            animacion = False
            
        invoke(terminar_giro, delay=duracion_giro + 0.05)
    
    
    def revolver(movimientos=7):
        global estado_global_ia
        if movimientos <= 0: return
        if animacion:
            invoke(revolver, movimientos, delay=0.1)
            return
            
        accion = random.choice(list(MOVES.keys()))
        estado_global_ia = rotar_matriz(estado_global_ia, accion)
        girar(accion)
        
        invoke(revolver, movimientos - 1, delay=duracion_giro + 0.1)
    
    def animar_solucion(camino):
        global estado_global_ia
        if not camino: 
            print("Cubo resuelto.")
            return
        if animacion:
            invoke(animar_solucion, camino, delay=0.1)
            return
            
        accion = camino.pop(0)
        estado_global_ia = rotar_matriz(estado_global_ia, accion)
        girar(accion)
        
        invoke(animar_solucion, camino, delay=duracion_giro + 0.1)
    
    def boton_algoritmo():
        if animacion: return
        camino_solucion = a_estrella(estado_global_ia)
        
        if camino_solucion is not None:
            print(f"Ruta {camino_solucion}")
            animar_solucion(camino_solucion)
    
    def detectar_teclas(key):
        global estado_global_ia
        if animacion: return 

        movimiento = None
        
        es_prima = held_keys['shift'] or held_keys['left shift'] or held_keys['right shift']
        
        # Minúsculas = Normal, Shift + Letra = Inverso (Ej: U')
        if key == 'u': movimiento = "U'" if es_prima else 'U'
        elif key == 'd': movimiento = "D'" if es_prima else 'D'
        elif key == 'f': movimiento = "F'" if es_prima else 'F'
        elif key == 'b': movimiento = "B'" if es_prima else 'B'
        elif key == 'l': movimiento = "L'" if es_prima else 'L'
        elif key == 'r': movimiento = "R'" if es_prima else 'R'

        if movimiento:
            print(f"Movimiento: {movimiento}")
            estado_global_ia = rotar_matriz(estado_global_ia, movimiento)
            girar(movimiento)

    # Creamos una entidad que nos permitirá mover las piezas de acuerdo a nuestra funcion de teclas
    controlador = Entity()
    controlador.input = detectar_teclas    
    
    Button(text='Revolver', color=color.blue, position=(-0.65, 0.4), scale=(0.25, 0.08), on_click=revolver)
    Button(text='Resolver(A*)', color=color.red, position=(-0.65, 0.3), scale=(0.25, 0.08), on_click=boton_algoritmo)     
    
    app.run()

    
iniciar()
    


