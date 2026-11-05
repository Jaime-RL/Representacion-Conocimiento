"""
Eliminación de variables (versión sencilla).

Un factor es simplemente un diccionario con dos cosas:
  - "variables": la lista de nombres de variables, por ejemplo ["A", "B"]
  - "tabla": un diccionario que asocia cada combinación de valores con su probabilidad,
             por ejemplo {(0, 0): 0.7, (0, 1): 0.3, ...}
             (el primer número es el valor de A y el segundo el de B)
"""

from itertools import product


# Valores posibles de cada variable de la red
VALORES = {
    "A": [0, 1, 2],
    "B": [0, 1],
    "C": [0, 1, 2],
    "D": [0, 1],
    "E": [0, 1],
}


def crear_factor(variables, tabla):
    return {"variables": variables, "tabla": tabla}


def todas_las_combinaciones(variables):
    """Devuelve todas las combinaciones de valores de las variables dadas.
    Ej: ["B", "D"] -> [(0, 0), (0, 1), (1, 0), (1, 1)]"""
    listas_de_valores = [VALORES[var] for var in variables]
    return list(product(*listas_de_valores))


def multiplicar(factor1, factor2):
    """Multiplica dos factores. El resultado tiene las variables de los dos."""
    # Variables del resultado: las del primero y luego las del segundo que no estén ya
    variables = list(factor1["variables"])
    for var in factor2["variables"]:
        if var not in variables:
            variables.append(var)

    tabla = {}
    for combinacion in todas_las_combinaciones(variables):
        # Guardamos qué valor tiene cada variable en esta combinación
        valor_de = dict(zip(variables, combinacion))

        # Buscamos la fila que corresponde en cada factor
        fila1 = tuple(valor_de[var] for var in factor1["variables"])
        fila2 = tuple(valor_de[var] for var in factor2["variables"])

        tabla[combinacion] = factor1["tabla"][fila1] * factor2["tabla"][fila2]

    return crear_factor(variables, tabla)


def sumar_variable(factor, var_a_quitar):
    """Elimina una variable del factor sumando sobre todos sus valores (marginalizar)."""
    variables = [var for var in factor["variables"] if var != var_a_quitar]
    posicion = factor["variables"].index(var_a_quitar)

    tabla = {}
    for combinacion, probabilidad in factor["tabla"].items():
        # Quitamos de la combinación el valor de la variable eliminada
        nueva = combinacion[:posicion] + combinacion[posicion + 1:]

        # Las combinaciones que quedan iguales se suman
        tabla[nueva] = tabla.get(nueva, 0.0) + probabilidad

    return crear_factor(variables, tabla)


def normalizar(factor):
    """Hace que las probabilidades del factor sumen 1."""
    total = sum(factor["tabla"].values())
    for combinacion in factor["tabla"]:
        factor["tabla"][combinacion] /= total
    return factor


def eliminar_variables(factores, orden):
    """Algoritmo de eliminación de variables.

    Para cada variable del orden:
      1. Cogemos los factores en los que aparece.
      2. Los multiplicamos todos en uno solo.
      3. Sumamos sobre la variable para quitarla.
      4. Ese nuevo factor sustituye a los que hemos cogido.
    """
    for var in orden:
        con_var = [f for f in factores if var in f["variables"]]
        sin_var = [f for f in factores if var not in f["variables"]]

        if not con_var:
            continue

        resultado = con_var[0]
        for f in con_var[1:]:
            resultado = multiplicar(resultado, f)

        resultado = sumar_variable(resultado, var)

        factores = sin_var + [resultado]

    # Multiplicamos lo que quede (normalmente un único factor)
    final = factores[0]
    for f in factores[1:]:
        final = multiplicar(final, f)

    return normalizar(final)


# ----------------------------------------------------------------------
# Ejemplo 2.2: queremos P(B)
# ----------------------------------------------------------------------

# P(D)
p_d = crear_factor(["D"], {
    (0,): 0.6,
    (1,): 0.4,
})

# P(E)
p_e = crear_factor(["E"], {
    (0,): 0.8,
    (1,): 0.2,
})

# P(A | D, E)   -> claves (A, D, E)
p_a_de = crear_factor(["A", "D", "E"], {
    (0, 0, 0): 0.3, (1, 0, 0): 0.4, (2, 0, 0): 0.3,
    (0, 0, 1): 0.1, (1, 0, 1): 0.2, (2, 0, 1): 0.7,
    (0, 1, 0): 0.7, (1, 1, 0): 0.2, (2, 1, 0): 0.1,
    (0, 1, 1): 0.2, (1, 1, 1): 0.3, (2, 1, 1): 0.5,
})

# P(B | A)      -> claves (B, A)
p_b_a = crear_factor(["B", "A"], {
    (0, 0): 0.7, (1, 0): 0.3,
    (0, 1): 0.4, (1, 1): 0.6,
    (0, 2): 0.1, (1, 2): 0.9,
})

# P(C | E)      -> claves (C, E)
p_c_e = crear_factor(["C", "E"], {
    (0, 0): 0.6, (1, 0): 0.3, (2, 0): 0.1,
    (0, 1): 0.3, (1, 1): 0.4, (2, 1): 0.3,
})


if __name__ == "__main__":
    factores = [p_d, p_e, p_a_de, p_b_a, p_c_e]
    orden = ["C", "E", "D", "A"]

    p_b = eliminar_variables(factores, orden)

    print("P(B):")
    for combinacion, probabilidad in p_b["tabla"].items():
        print(f"  B = {combinacion[0]}  ->  {probabilidad:.4f}")
