"""
Factores, producto, marginalización y eliminación de variables (EV).

Formato de las llaves: cada valor de una variable se escribe como "<nombre>_<índice>",
por ejemplo "A_0", "A_1". Usa Variable.valor(i) para obtenerlo sin escribirlo a mano.

Requisitos: Python 3.10+ (sin librerías externas).
"""

import math


class Variable:

    def __init__(self, nombre: str, valores: list):
        self.nombre: str = nombre
        # Etiquetas descriptivas de los valores (solo informativas).
        # Las llaves de las tablas NO las usan: usan el formato "<nombre>_<índice>".
        self.valores = valores
        self.cardinalidad: int = len(valores)

    def valor(self, indice: int) -> str:
        # Único sitio donde se define el formato de los valores en las llaves
        if not 0 <= indice < self.cardinalidad:
            raise ValueError(f"{self.nombre} no tiene el valor de índice {indice}")
        return f"{self.nombre}_{indice}"

    def __repr__(self) -> str:
        # Facilita depurar: print(factor.ambito) muestra [A, B] en vez de direcciones de memoria
        return self.nombre


class Factor:

    def __init__(self, ambito: set):
        # Ámbito ordenado por nombre: define el orden de los valores dentro de cada llave
        self.ambito = sorted(ambito, key=lambda v: v.nombre)
        self.tabla: dict[tuple[str, ...], float] = dict()

    def crear_llaves(self) -> list[tuple[str, ...]]:
        # Aquí preparamos una lista vacía donde guardaremos todas las combinaciones.
        llaves = []
        # Empezamos a construir cada combinación desde la primera variable.
        self.crear_llaves_recursivo(self.ambito, 0, [], llaves)
        return llaves

    def crear_llaves_recursivo(self, variables, posicion, llave, llaves):
        # Si ya hemos usado todas las variables, la combinación está terminada.
        if posicion == len(variables):
            # Las tuplas sirven como claves del diccionario de la tabla.
            llaves.append(tuple(llave))
            return

        # Elegimos la variable que toca en este paso.
        var = variables[posicion]

        # Probamos todos los valores posibles de esa variable.
        for i in range(var.cardinalidad):
            # Creamos una copia de la combinación y añadimos el valor actual.
            nueva_llave = llave + [var.valor(i)]
            # Repetimos el proceso con la siguiente variable.
            self.crear_llaves_recursivo(variables, posicion + 1, nueva_llave, llaves)

    def iniciar_tabla(self) -> None:
        # Todas las llaves posibles con valor 0.0
        for llave in self.crear_llaves():
            self.tabla[llave] = 0.0

    def completar_tabla(self, valores: list[float]) -> None:
        # Rellena la tabla con 'valores', en el mismo orden en que crear_llaves() genera las llaves.
        # Ejemplo con ámbito [A, B]: (A_0,B_0), (A_0,B_1), (A_1,B_0), (A_1,B_1)
        llaves = self.crear_llaves()
        if len(valores) != len(llaves):
            raise ValueError(
                f"El factor sobre {self.ambito} necesita {len(llaves)} valores, "
                f"pero se han dado {len(valores)}"
            )
        self.tabla = dict(zip(llaves, valores))


def producto(factor1: Factor, factor2: Factor) -> Factor:
    # El constructor ordena el ámbito por nombre, así que las llaves del factor nuevo siguen ese orden
    factor_nuevo = Factor(set(factor1.ambito) | set(factor2.ambito))

    # Posiciones de las variables de cada factor dentro de las llaves del factor nuevo
    pos1 = [i for i, v in enumerate(factor_nuevo.ambito) if v in factor1.ambito]
    pos2 = [i for i, v in enumerate(factor_nuevo.ambito) if v in factor2.ambito]

    factor_nuevo.iniciar_tabla()

    for llave in factor_nuevo.tabla.keys():
        # Restringir la llave completa al ámbito de cada factor
        llave1 = tuple(llave[i] for i in pos1)
        llave2 = tuple(llave[i] for i in pos2)

        factor_nuevo.tabla[llave] = factor1.tabla[llave1] * factor2.tabla[llave2]

    return factor_nuevo


def marginalizacion(var: Variable, factor_viejo: Factor) -> Factor:
    # Nuevo ámbito: el del original sin la variable a marginalizar
    factor_nuevo = Factor(set(factor_viejo.ambito) - {var})

    # Posiciones (en las llaves del original) de las variables que se quedan
    posiciones_variables_nuevas = [i for i, v in enumerate(factor_viejo.ambito) if v is not var]

    # Todas las llaves del nuevo factor a 0.0, para poder acumular sobre ellas
    factor_nuevo.iniciar_tabla()

    for llave in factor_viejo.tabla.keys():
        # Quitar de la llave el valor de la variable marginalizada
        llave_nueva = tuple(llave[i] for i in posiciones_variables_nuevas)
        # Varias llaves originales caen en la misma llave nueva: se suman
        factor_nuevo.tabla[llave_nueva] += factor_viejo.tabla[llave]

    return factor_nuevo


def factor_uno() -> Factor:
    # Factor constante 1 (ámbito vacío): elemento neutro del producto
    uno = Factor(set())
    uno.tabla[()] = 1.0
    return uno


def producto_lista(factores: list[Factor]) -> Factor:
    # Multiplica todos los factores de la lista, empezando por el neutro
    resultado = factor_uno()
    for factor in factores:
        resultado = producto(resultado, factor)
    return resultado


def eliminacion_variables_inferencia_marginal(factores: list[Factor], variables: list[Variable]) -> Factor:
    """
    Elimina, en el orden dado, cada variable de 'variables' y devuelve el producto de
    los factores restantes (la distribución de las variables no eliminadas).
    """
    factores_actuales = factores.copy()

    for variable_a_eliminar in variables:
        factores_con_variable = []
        factores_sin_variable = []

        # Clasificar los factores según contengan la variable que se eliminará.
        for factor in factores_actuales:
            if variable_a_eliminar in factor.ambito:
                factores_con_variable.append(factor)
            else:
                factores_sin_variable.append(factor)

        # Multiplicar los factores relacionados y marginalizar la variable una vez.
        factor_combinado = producto_lista(factores_con_variable)
        factor_marginalizado = marginalizacion(variable_a_eliminar, factor_combinado)

        factores_actuales = factores_sin_variable + [factor_marginalizado]

    # Multiplicar los factores restantes para obtener la distribución final.
    return producto_lista(factores_actuales)


def aplicar_evidencia(factor: Factor, var: Variable, val: str) -> Factor:
    # Si el factor no contiene la variable observada, no hay nada que reducir
    if var not in factor.ambito:
        return factor

    # Copia: el factor original (por ejemplo, una CPT de la red) no se modifica
    copia_factor = Factor(factor.ambito)
    copia_factor.tabla = factor.tabla.copy()

    pos = factor.ambito.index(var)

    # Filas incompatibles con lo observado a 0
    for llave in copia_factor.tabla.keys():
        if llave[pos] != val:
            copia_factor.tabla[llave] = 0.0

    return copia_factor


def eliminacion_variables_inferencia_condicional(
    factores: list[Factor],
    variables: list[Variable],
    evidencia: dict[Variable, str],
) -> Factor:
    """
    Calcula P(consulta | evidencia).

    - variables: variables a eliminar (ocultas). Las de la evidencia se eliminan también;
      si no están en la lista, se añaden automáticamente al final.
    - evidencia: {Variable: valor}, con el valor en formato de llave (usa var.valor(i)).
    """
    # Aplicar toda la evidencia a cada factor (encadenada) y guardar cada factor una vez
    factores_finales = []
    for factor in factores:
        for var, val in evidencia.items():
            factor = aplicar_evidencia(factor, var, val)
        factores_finales.append(factor)

    # Las variables de evidencia también se eliminan, para que no queden en el resultado
    a_eliminar = variables + [v for v in evidencia if v not in variables]

    # El resultado es P(consulta, evidencia): todavía sin normalizar
    resultado = eliminacion_variables_inferencia_marginal(factores_finales, a_eliminar)

    # Normalizar: la suma es P(evidencia)
    normalizador = sum(resultado.tabla.values())
    if normalizador == 0:
        raise ValueError("La evidencia tiene probabilidad 0 (valor imposible o inexistente)")

    resultado.tabla = {k: v / normalizador for k, v in resultado.tabla.items()}
    return resultado


# ---------------------------------------------------------------------------
# Pruebas con la cadena A -> B -> C (resultados calculados a mano)
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    A = Variable("A", ["no", "si"])
    B = Variable("B", ["no", "si"])
    C = Variable("C", ["no", "si"])

    pA = Factor({A})
    pA.completar_tabla([0.6, 0.4])

    pB_A = Factor({A, B})
    pB_A.completar_tabla([0.7, 0.3,     # A_0: B_0, B_1
                          0.2, 0.8])    # A_1: B_0, B_1

    pC_B = Factor({B, C})
    pC_B.completar_tabla([0.9, 0.1,     # B_0: C_0, C_1
                          0.4, 0.6])    # B_1: C_0, C_1

    factores = [pA, pB_A, pC_B]

    def comprobar(nombre: str, factor: Factor, esperado: dict) -> None:
        # Compara con tolerancia: los decimales en coma flotante no son exactos
        ok = all(math.isclose(factor.tabla[k], v) for k, v in esperado.items())
        print(f"[{'OK' if ok else 'FALLO'}] {nombre}: {factor.tabla}")

    # Marginal: P(C) = [0.65, 0.35]
    comprobar("P(C)",
              eliminacion_variables_inferencia_marginal(factores, [A, B]),
              {("C_0",): 0.65, ("C_1",): 0.35})

    # Distinto orden de eliminación: debe dar lo mismo
    comprobar("P(C), orden B, A",
              eliminacion_variables_inferencia_marginal(factores, [B, A]),
              {("C_0",): 0.65, ("C_1",): 0.35})

    # Condicional: P(C | A = A_1) = [0.5, 0.5]
    comprobar("P(C | A=A_1)",
              eliminacion_variables_inferencia_condicional(factores, [B], {A: A.valor(1)}),
              {("C_0",): 0.5, ("C_1",): 0.5})

    # Fuerza bruta: multiplicar todo y marginalizar debe coincidir con EV
    conjunta = producto_lista(factores)
    bruta = marginalizacion(B, marginalizacion(A, conjunta))
    comprobar("P(C) por fuerza bruta", bruta, {("C_0",): 0.65, ("C_1",): 0.35})

    # Los factores originales no deben haber cambiado tras la condicional
    print(f"[{'OK' if pA.tabla[('A_0',)] == 0.6 else 'FALLO'}] pA sin modificar: {pA.tabla}")

    # Evidencia imposible: error claro en lugar de ZeroDivisionError
    try:
        eliminacion_variables_inferencia_condicional(factores, [B], {A: "A_7"})
        print("[FALLO] evidencia imposible no ha lanzado error")
    except ValueError as e:
        print(f"[OK] evidencia imposible: {e}")