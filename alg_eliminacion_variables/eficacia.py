"""
➋ Eficacia: comprobar con ejemplos variados que la eliminación de variables (EV) es correcta.

Estrategia:
  1. Ejemplos calculados a mano.
  2. Un ejemplo clásico con resultado conocido (red de la alarma, Russell & Norvig).
  3. El ejemplo de los apuntes (factores no normalizados) con TODOS los órdenes de eliminación.
  4. Redes aleatorias (variables binarias y multivaluadas, con y sin evidencia),
     comparando siempre con un cálculo por FUERZA BRUTA (multiplicar todo y sumar).

Requisitos: Python 3.10+ y el archivo elim_var.py en la misma carpeta.
"""

import itertools
import math
import random

from elim_var import (
    Factor, Variable, aplicar_evidencia, eliminacion_variables_inferencia_condicional,
    eliminacion_variables_inferencia_marginal, marginalizacion, producto_lista,
)

TOLERANCIA = 1e-9
resultados = {"OK": 0, "FALLO": 0}


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------
def normalizar(factor: Factor) -> Factor:
    # Copia normalizada (para comparar resultados de factores no probabilísticos)
    total = sum(factor.tabla.values())
    copia = Factor(factor.ambito)
    copia.tabla = {k: v / total for k, v in factor.tabla.items()}
    return copia


def fuerza_bruta(factores: list[Factor], consulta: list[Variable], evidencia: dict | None = None) -> Factor:
    """
    Referencia: aplica la evidencia, multiplica TODOS los factores (distribución conjunta)
    y suma todas las variables que no son de consulta. Exponencial, pero obviamente correcta.
    """
    evidencia = evidencia or {}
    reducidos = []
    for f in factores:
        for var, val in evidencia.items():
            f = aplicar_evidencia(f, var, val)
        reducidos.append(f)

    conjunta = producto_lista(reducidos)
    for var in list(conjunta.ambito):
        if var not in consulta:
            conjunta = marginalizacion(var, conjunta)
    return normalizar(conjunta)


def iguales(f1: Factor, f2: Factor, tol: float = TOLERANCIA) -> bool:
    # Mismo ámbito, mismas llaves y valores iguales con tolerancia
    return (f1.ambito == f2.ambito
            and f1.tabla.keys() == f2.tabla.keys()
            and all(math.isclose(f1.tabla[k], f2.tabla[k], abs_tol=tol) for k in f1.tabla))


def comprobar(nombre: str, condicion: bool, detalle: str = "") -> None:
    estado = "OK" if condicion else "FALLO"
    resultados[estado] += 1
    print(f"  [{estado}] {nombre}" + (f"  {detalle}" if detalle else ""))


def red_aleatoria(n: int, max_padres: int, cardinalidades: list[int], rng: random.Random):
    """
    Red bayesiana aleatoria: variables X00..X(n-1), cada una con hasta 'max_padres' padres
    elegidos entre las anteriores (así el grafo es acíclico). CPTs aleatorias normalizadas.
    """
    variables = [Variable(f"X{i:02d}", list(range(rng.choice(cardinalidades)))) for i in range(n)]
    factores = []
    for i, hijo in enumerate(variables):
        padres = rng.sample(variables[:i], k=min(i, rng.randint(0, max_padres)))
        factores.append(cpt_aleatoria(hijo, padres, rng))
    return variables, factores


def cpt_aleatoria(hijo: Variable, padres: list[Variable], rng: random.Random) -> Factor:
    # P(hijo | padres): valores aleatorios positivos normalizados para cada combinación de padres
    f = Factor({hijo, *padres})
    f.iniciar_tabla()
    for llave in f.tabla:
        f.tabla[llave] = rng.uniform(0.05, 1.0)

    pos_hijo = f.ambito.index(hijo)
    sumas: dict[tuple, float] = {}
    for llave, valor in f.tabla.items():
        llave_padres = llave[:pos_hijo] + llave[pos_hijo + 1:]
        sumas[llave_padres] = sumas.get(llave_padres, 0.0) + valor
    for llave in f.tabla:
        f.tabla[llave] /= sumas[llave[:pos_hijo] + llave[pos_hijo + 1:]]
    return f


# ---------------------------------------------------------------------------
# 1. Cadena A -> B -> C (resultados calculados a mano)
# ---------------------------------------------------------------------------
def prueba_cadena() -> None:
    print("\n1. Cadena A -> B -> C (calculado a mano)")
    A, B, C = Variable("A", [0, 1]), Variable("B", [0, 1]), Variable("C", [0, 1])
    pA = Factor({A});        pA.completar_tabla([0.6, 0.4])
    pB_A = Factor({A, B});   pB_A.completar_tabla([0.7, 0.3, 0.2, 0.8])
    pC_B = Factor({B, C});   pC_B.completar_tabla([0.9, 0.1, 0.4, 0.6])
    factores = [pA, pB_A, pC_B]
    copia_original = dict(pA.tabla)

    marginal = eliminacion_variables_inferencia_marginal(factores, [A, B])
    comprobar("P(C) = [0.65, 0.35]",
              math.isclose(marginal.tabla[("C_0",)], 0.65) and math.isclose(marginal.tabla[("C_1",)], 0.35))

    cond = eliminacion_variables_inferencia_condicional(factores, [B], {A: A.valor(1)})
    comprobar("P(C | A=1) = [0.5, 0.5]",
              math.isclose(cond.tabla[("C_0",)], 0.5) and math.isclose(cond.tabla[("C_1",)], 0.5))

    # Razonamiento "hacia atrás": P(A | C=1) por Bayes = 0.6*0.27/0.35 y 0.4*0.5/0.35
    cond_inv = eliminacion_variables_inferencia_condicional(factores, [B], {C: C.valor(1)})
    comprobar("P(A | C=1) (diagnóstico, contra la flecha)",
              math.isclose(cond_inv.tabla[("A_1",)], 0.4 * 0.5 / 0.35))

    comprobar("Los factores originales no se modifican", pA.tabla == copia_original)


# ---------------------------------------------------------------------------
# 2. Red de la alarma (ejemplo clásico de Russell & Norvig)
# ---------------------------------------------------------------------------
def prueba_alarma() -> None:
    print("\n2. Red de la alarma (Russell & Norvig), índice 0 = falso, 1 = verdadero")
    Rb = Variable("Burglary", [0, 1]); Te = Variable("Earthquake", [0, 1])
    Al = Variable("Alarm", [0, 1]); Jc = Variable("JohnCalls", [0, 1]); Mc = Variable("MaryCalls", [0, 1])

    def cpt_binaria(hijo, padres, p_verdadero: dict) -> Factor:
        # p_verdadero: {tupla de índices de los padres: P(hijo = 1 | padres)}
        f = Factor({hijo, *padres})
        f.iniciar_tabla()
        pos_hijo = f.ambito.index(hijo)
        for llave in f.tabla:
            indices_padres = tuple(int(llave[f.ambito.index(p)].split("_")[-1]) for p in padres)
            p1 = p_verdadero[indices_padres]
            f.tabla[llave] = p1 if llave[pos_hijo] == hijo.valor(1) else 1 - p1
        return f

    factores = [
        cpt_binaria(Rb, [], {(): 0.001}),
        cpt_binaria(Te, [], {(): 0.002}),
        cpt_binaria(Al, [Rb, Te], {(1, 1): 0.95, (1, 0): 0.94, (0, 1): 0.29, (0, 0): 0.001}),
        cpt_binaria(Jc, [Al], {(1,): 0.90, (0,): 0.05}),
        cpt_binaria(Mc, [Al], {(1,): 0.70, (0,): 0.01}),
    ]
    evidencia = {Jc: Jc.valor(1), Mc: Mc.valor(1)}
    resultado = eliminacion_variables_inferencia_condicional(factores, [Te, Al], evidencia)
    p = resultado.tabla[("Burglary_1",)]
    comprobar("P(Burglary | John y Mary llaman) ≈ 0.284 (valor del libro)",
              math.isclose(p, 0.284, abs_tol=5e-4), f"obtenido {p:.4f}")
    comprobar("Coincide con fuerza bruta", iguales(resultado, fuerza_bruta(factores, [Rb], evidencia)))


# ---------------------------------------------------------------------------
# 3. Ejemplo de los apuntes: φ1(a,d,e) φ2(a,b) φ3(c,e) φ4(d) φ5(e), todos los órdenes
# ---------------------------------------------------------------------------
def prueba_apuntes(rng: random.Random) -> None:
    print("\n3. Ejemplo de los apuntes (factores no normalizados), los 24 órdenes de eliminación")
    a, b, c, d, e = (Variable(n, [0, 1]) for n in "abcde")

    def factor_aleatorio(*vs) -> Factor:
        f = Factor(set(vs))
        f.completar_tabla([rng.uniform(0.1, 5.0) for _ in range(2 ** len(vs))])
        return f

    factores = [factor_aleatorio(a, d, e), factor_aleatorio(a, b), factor_aleatorio(c, e),
                factor_aleatorio(d), factor_aleatorio(e)]
    referencia = fuerza_bruta(factores, [b])

    todos_ok = all(
        iguales(normalizar(eliminacion_variables_inferencia_marginal(factores, list(orden))), referencia)
        for orden in itertools.permutations([a, c, d, e])
    )
    comprobar("p(b): los 24 órdenes coinciden con fuerza bruta", todos_ok)


# ---------------------------------------------------------------------------
# 4. Redes aleatorias: binarias, multivaluadas, con y sin evidencia
# ---------------------------------------------------------------------------
def prueba_redes_aleatorias(rng: random.Random, n_redes: int = 40) -> None:
    print(f"\n4. {n_redes} redes aleatorias por configuración, comparadas con fuerza bruta")
    configuraciones = [
        ("binarias, sin evidencia", [2], 0),
        ("binarias, 1-2 evidencias", [2], 2),
        ("multivaluadas (2-4), sin evidencia", [2, 3, 4], 0),
        ("multivaluadas (2-4), 1-2 evidencias", [2, 3, 4], 2),
    ]
    for nombre, cards, max_evid in configuraciones:
        fallos = 0
        for _ in range(n_redes):
            variables, factores = red_aleatoria(n=rng.randint(3, 7), max_padres=3, cardinalidades=cards, rng=rng)
            consulta = rng.choice(variables)
            resto = [v for v in variables if v is not consulta]
            observadas = rng.sample(resto, k=min(len(resto), rng.randint(1, max_evid))) if max_evid else []
            evidencia = {v: v.valor(rng.randrange(v.cardinalidad)) for v in observadas}
            ocultas = [v for v in resto if v not in evidencia]
            rng.shuffle(ocultas)  # orden de eliminación aleatorio: el resultado no debe depender de él

            if evidencia:
                ev = eliminacion_variables_inferencia_condicional(factores, ocultas, evidencia)
            else:
                ev = eliminacion_variables_inferencia_marginal(factores, ocultas)

            if not (iguales(ev, fuerza_bruta(factores, [consulta], evidencia))
                    and math.isclose(sum(ev.tabla.values()), 1.0)):
                fallos += 1
        comprobar(nombre, fallos == 0, f"({n_redes - fallos}/{n_redes} correctas)")


# ---------------------------------------------------------------------------
# 5. Casos límite
# ---------------------------------------------------------------------------
def prueba_casos_limite() -> None:
    print("\n5. Casos límite")
    A, B = Variable("A", [0, 1, 2]), Variable("B", [0, 1])
    pA = Factor({A}); pA.completar_tabla([0.2, 0.3, 0.5])
    pB_A = Factor({A, B}); pB_A.completar_tabla([0.1, 0.9, 0.5, 0.5, 0.8, 0.2])

    sin_eliminar = eliminacion_variables_inferencia_marginal([pA], [])
    comprobar("Sin variables que eliminar devuelve el propio factor", sin_eliminar.tabla == pA.tabla)

    todo = eliminacion_variables_inferencia_marginal([pA, pB_A], [A, B])
    comprobar("Eliminar todas las variables da un factor constante igual a 1",
              todo.ambito == [] and math.isclose(todo.tabla[()], 1.0))

    Z = Variable("Z", [0, 1])
    con_ajena = eliminacion_variables_inferencia_marginal([pA, pB_A], [Z, A])
    comprobar("Eliminar una variable que no está en ningún factor no altera el resultado",
              iguales(con_ajena, fuerza_bruta([pA, pB_A], [B])))

    try:
        eliminacion_variables_inferencia_condicional([pA, pB_A], [], {A: "A_9"})
        comprobar("Evidencia imposible lanza ValueError", False)
    except ValueError:
        comprobar("Evidencia imposible lanza ValueError", True)


if __name__ == "__main__":
    rng = random.Random(2026)  # semilla fija: resultados reproducibles
    prueba_cadena()
    prueba_alarma()
    prueba_apuntes(rng)
    prueba_redes_aleatorias(rng)
    prueba_casos_limite()
    print(f"\nResumen: {resultados['OK']} correctas, {resultados['FALLO']} fallidas")