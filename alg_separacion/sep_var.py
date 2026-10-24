import networkx as nx

# ============================================================================
# Algoritmo de separación de variables (criterio gráfico de d-separación)
#
#   1) Elimina los nodos hoja de G que no pertenezcan a X ∪ Y ∪ Z.
#   2) Une (casa) entre sí a los padres que comparten un hijo común,
#      e ignora la dirección de las aristas.
#   3) X ⊥ Y | Z  si y solo si no existe ningún camino entre X e Y
#      que no pase por un nodo de Z (aquí, eliminando físicamente Z).
# ============================================================================


def crear_grafo_prueba():
    """Grafo de ejemplo: 1 -> 3 <- 2, y 3 -> 4, 3 -> 5, 3 -> 6."""
    G = nx.DiGraph()
    G.add_edges_from([
        (1, 3), (2, 3),
        (3, 4), (3, 5), (3, 6),
    ])
    return G


def recorrido_postorden(grafo, nodo_actual, visitados=None, resultado=None):
    """
    Recorre el grafo en POSTORDEN a partir de `nodo_actual`.

    "Postorden" significa: primero se visitan recursivamente todos los
    descendientes del nodo, y solo DESPUÉS se añade el propio nodo a
    `resultado`. Consecuencia clave para el algoritmo: en la lista final,
    todo nodo aparece DESPUÉS que todos sus descendientes.

    `visitados` y `resultado` se pueden pasar ya creados desde fuera para
    poder encadenar varias llamadas (por ejemplo, una por cada raíz del
    grafo) y que comparen el mismo estado, evitando visitar el mismo nodo
    dos veces.
    """
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
    """
    PASO 1 del algoritmo: borra del grafo los nodos hoja (sin sucesores)
    que no estén en el conjunto de estudio X ∪ Y ∪ Z.

    `x`, `y`, `z` son LISTAS de nodos (conjuntos), no nodos sueltos, por
    ejemplo x=['a'], y=['b'], z=['c', 'd'].

    Se recorre el grafo en postorden para poder borrar "en cascada": si al
    quitar una hoja su padre se convierte también en hoja, ese padre
    aparece más adelante en el mismo recorrido (los hijos siempre salen
    antes que el padre en postorden) y se evaluará correctamente en la
    misma pasada del bucle.
    """
    # El grafo puede tener varias "raíces" (nodos sin padres), así que
    # buscamos todas para no dejar ninguna rama sin recorrer.
    raices = [n for n in list(grafo) if len(list(grafo.predecessors(n))) == 0]

    # Importante: usamos UN SOLO `visitados` (y un solo `resultado`)
    # compartido entre todas las raíces. Si usáramos uno nuevo por cada
    # raíz, un nodo alcanzable desde dos raíces distintas (como el nodo 3
    # en el grafo de prueba, hijo de 1 y de 2) aparecería dos veces en
    # `nodos_postorden`, y el bucle de abajo intentaría borrarlo dos
    # veces, lo que lanza un error la segunda vez.
    visitados = set()
    nodos_postorden = []
    for raiz in raices:
        if raiz not in visitados:
            recorrido_postorden(grafo, raiz, visitados, nodos_postorden)

    # Conjunto plano de nodos "protegidos": no se pueden borrar aunque
    # sean hoja, porque forman parte de lo que se está estudiando.
    # x, y, z ya son listas de nodos sueltos, así que basta concatenarlas.
    nodos_estudio = x + y + z

    for nodo in nodos_postorden:
        es_hoja = len(list(grafo.successors(nodo))) == 0
        if es_hoja and nodo not in nodos_estudio:
            grafo.remove_node(nodo)


def conectar_padres_nodo(grafo, padres_nodo):
    """
    Añade una arista entre cada PAR de padres de un mismo nodo
    ("casar" a los padres). Si un nodo tiene padres [p1, p2, p3], se
    añaden las aristas (p1,p2), (p1,p3) y (p2,p3).
    """
    num_padres = len(padres_nodo)

    for i in range(num_padres):
        for j in range(i + 1, num_padres):
            padre1 = padres_nodo[i]
            padre2 = padres_nodo[j]
            grafo.add_edge(padre1, padre2)

    return grafo


def grafo_sin_direcciones(grafo):
    """
    Convierte el grafo dirigido en "no dirigido": por cada arista
    (origen -> destino) que exista, añade también la arista inversa
    (destino -> origen), de forma que moverse en successors() funcione
    en ambos sentidos.
    """
    # Primero se copian las aristas actuales a una lista aparte, porque
    # no conviene modificar el grafo (añadir aristas) mientras se está
    # iterando sobre él.
    aristas_originales = []
    for nodo in list(grafo):
        for hijo in grafo.successors(nodo):
            aristas_originales.append((nodo, hijo))

    for origen, destino in aristas_originales:
        grafo.add_edge(destino, origen)

    return grafo


def unir_padres_con_hijos_comunes_sin_direccion(grafo):
    """
    PASO 2 del algoritmo: por cada nodo con dos o más padres, los conecta
    entre sí (moralización), y después quita la dirección de todas las
    aristas del grafo.
    """
    for nodo in list(grafo):
        padres_nodo = list(grafo.predecessors(nodo))
        if len(padres_nodo) >= 2:
            conectar_padres_nodo(grafo, padres_nodo)

    return grafo_sin_direcciones(grafo)


def eliminar_nodos_z(grafo, z):
    """Quita del grafo todos los nodos del conjunto Z (lista de nodos)."""
    for nodo_z in z:
        grafo.remove_node(nodo_z)
    return grafo


def hay_camino(grafo, x, y):
    """
    Busca en profundidad (DFS) si existe algún camino desde CUALQUIER
    nodo de `x` hasta CUALQUIER nodo de `y`.

    `analizar` hace de pila: se arranca metiendo todos los nodos de `x`
    por separado (no la lista `x` entera como un solo elemento), y en
    cada paso se comprueba si el nodo actual PERTENECE al conjunto `y`
    (con `in`, no con `==`, porque `y` puede tener varios nodos).
    """
    analizar = list()
    for nodo_x in x:
        analizar.append(nodo_x)

    visitados = set()

    while analizar:
        nodo_a_analizar = analizar.pop()

        if nodo_a_analizar in y:
            return True

        if nodo_a_analizar in visitados:
            continue

        visitados.add(nodo_a_analizar)

        for conexion in grafo.successors(nodo_a_analizar):
            analizar.append(conexion)

    return False


def comprobar_camino(grafo, x, y, z):
    """
    Aplica los 3 pasos del algoritmo de separación de variables y
    devuelve True si queda un camino entre X e Y (es decir, X e Y NO
    están d-separados dado Z), o False si no queda ninguno (X ⊥ Y | Z).
    """
    eliminar_nodos_hoja(grafo, x, y, z)
    unir_padres_con_hijos_comunes_sin_direccion(grafo)
    grafo = eliminar_nodos_z(grafo, z)

    return hay_camino(grafo, x, y)


if __name__ == "__main__":
    # La ejecución del script va al final, después de TODAS las
    # definiciones de función. Si esto se ejecutara antes de que Python
    # hubiera leído la definición de alguna función usada aquí, se
    # usaría una versión antigua o incompleta de esa función (o fallaría
    # directamente porque todavía no existe).
    G = crear_grafo_prueba()
    print("¿Camino entre 1 y 2 si Z=[3]?", comprobar_camino(G, [1], [2], [3]))
