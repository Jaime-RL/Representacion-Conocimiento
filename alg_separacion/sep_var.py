import networkx as nx

def crear_grafo_prueba():
    G = nx.DiGraph()
    G.add_edges_from([
                (1, 3), (2, 3),
                (3, 4), (3, 5), (3, 6)
    ])
    return G


def recorrido_postorden(grafo, nodo_actual, visitados=None, resultado=None):
    if visitados is None:
        visitados = set()
    if resultado is None:
        resultado = []

    visitados.add(nodo_actual)

    for hijo in grafo.successors(nodo_actual):
        if hijo not in visitados:
            recorrido_postorden(grafo, hijo, visitados, resultado)

    resultado.append(nodo_actual)
    return resultado


def eliminar_nodos_hoja(grafo, x, y, z):
    nodos_postorden = recorrido_postorden(grafo, grafo.root)

    nodos_estudio = list(x + y + z)

    for nodo in nodos_postorden:
        if len(list(grafo.successors(nodo))) == 0 and nodo not in nodos_estudio:
            grafo.remove_node(nodo)


def unir_padres_con_hijos_comunes_sin_direccion(grafo):
    for nodo in list(grafo):
        padres_nodo = list(grafo.predecessors(nodo))
        if len(padres_nodo) >= 2:
            conectar_padres_nodo(grafo, padres_nodo)

    return grafo_sin_direcciones(grafo)


def conectar_padres_nodo(grafo, padres_nodo):
    num_padres = len(padres_nodo)

    for i in range(num_padres):
        for j in range(i+1, num_padres):
            padre1 = padres_nodo[i]
            padre2 = padres_nodo[j]

            grafo.add_edge(padre1, padre2)

    return grafo


def grafo_sin_direcciones(grafo):
    aristas_originales = []

    for nodo in list(grafo):
        for hijo in grafo.sucessors(nodo):
            aristas_originales.append((nodo, hijo))

    for origen, destino in aristas_originales:
        grafo.add_edge(destino, origen)

    return grafo


def comprobar_camino(grafo, x, y, z):

    eliminar_nodos_hoja(grafo, x, y, z)
    unir_padres_con_hijos_comunes_sin_direccion(grafo)


    grafo = eliminar_nodos_z(grafo, z)
    if hay_camino(grafo, x, y):
        return True
    else:
        return False

def eliminar_nodos_z(grafo, z):
    for nodo_z in z:
        grafo.remove_node(nodo_z)
    return grafo


def hay_camino(grafo, x, y):
    
    analizar = [x]
    visitados = set()

    while analizar:
        nodo_a_analizar = analizar.pop()
        if nodo_a_analizar == y:
            return True

        if nodo_a_analizar in visitados:
            continue

        visitados.add(nodo_a_analizar)
    
        for conexion in grafo.successors(nodo_a_analizar):
            analizar.append(conexion)
    
    return False
    

G = crear_grafo_prueba()
print("¿Camino entre 1 y 2 si Z=[3]?", comprobar_camino(G, [1], [2], [3]))


#IA

def eliminar_nodos_hoja(grafo, x, y, z):
    # Encontrar las raíces manualmente (nodos sin padres)
    raices = [n for n in list(grafo) if len(list(grafo.predecessors(n))) == 0]
    nodos_postorden = []
    for raiz in raices:
        nodos_postorden.extend(recorrido_postorden(grafo, raiz))

    nodos_estudio = [x, y] + z

    for nodo in nodos_postorden:
        # Asegurarse de comprobar la longitud de los sucesores para ver si es hoja
        if len(list(grafo.successors(nodo))) == 0 and nodo not in nodos_estudio:
            grafo.remove_node(nodo)