"""
➌ Coste temporal empírico de la eliminación de variables (EV).

Coste teórico: el trabajo de EV está dominado por el tamaño de los factores intermedios ψ.
Si n es el número de variables, d la cardinalidad y w el número de variables del mayor ψ,
el coste es aproximadamente O(n · d^w). Por eso se mide el tiempo en función de:

  Exp. 1  n  (longitud de una cadena, d = 2, w = 2 fijo)        → se espera crecimiento LINEAL
  Exp. 2  d  (cardinalidad en una cadena, n fijo, w = 2)        → se espera crecimiento CUADRÁTICO (d^2)
  Exp. 3  w  (red en estrella con buen y mal orden de eliminación) → se espera crecimiento EXPONENCIAL (2^w)
  Exp. 4  tiempo frente al tamaño del mayor factor intermedio   → se espera relación casi LINEAL
          (en esta implementación cada entrada cuesta O(w), porque las llaves son tuplas de w valores)

Requisitos: Python 3.10+ y elim_var.py en la misma carpeta.
Opcional: matplotlib (pip install matplotlib) para guardar las gráficas en PNG.
"""

import csv
import random
import time

from elim_var import Factor, Variable, eliminacion_variables_inferencia_marginal

REPETICIONES = 7  # se toma el mínimo: la ejecución con menos interferencias del sistema operativo


# ---------------------------------------------------------------------------
# Construcción de redes
# ---------------------------------------------------------------------------
def cpt_aleatoria(hijo: Variable, padres: list[Variable], rng: random.Random) -> Factor:
    # P(hijo | padres) aleatoria y normalizada para cada combinación de los padres
    f = Factor({hijo, *padres})
    f.iniciar_tabla()
    for llave in f.tabla:
        f.tabla[llave] = rng.uniform(0.05, 1.0)
    pos = f.ambito.index(hijo)
    sumas: dict[tuple, float] = {}
    for llave, valor in f.tabla.items():
        clave_padres = llave[:pos] + llave[pos + 1:]
        sumas[clave_padres] = sumas.get(clave_padres, 0.0) + valor
    for llave in f.tabla:
        f.tabla[llave] /= sumas[llave[:pos] + llave[pos + 1:]]
    return f


def red_cadena(n: int, d: int, rng: random.Random):
    # X00 -> X01 -> ... -> X(n-1): cada factor tiene como mucho 2 variables
    variables = [Variable(f"X{i:03d}", list(range(d))) for i in range(n)]
    factores = [cpt_aleatoria(variables[0], [], rng)]
    factores += [cpt_aleatoria(variables[i], [variables[i - 1]], rng) for i in range(1, n)]
    return variables, factores


def red_estrella(k: int, rng: random.Random):
    # Un nodo central H con k hijos L0..L(k-1): H -> Li
    H = Variable("H", [0, 1])
    hojas = [Variable(f"L{i:02d}", [0, 1]) for i in range(k)]
    factores = [cpt_aleatoria(H, [], rng)] + [cpt_aleatoria(h, [H], rng) for h in hojas]
    return H, hojas, factores


# ---------------------------------------------------------------------------
# Medición
# ---------------------------------------------------------------------------
def medir(funcion) -> float:
    # Mínimo de varias ejecuciones, en milisegundos
    tiempos = []
    for _ in range(REPETICIONES):
        inicio = time.perf_counter()
        funcion()
        tiempos.append((time.perf_counter() - inicio) * 1000)
    return min(tiempos)


def tamano_max_intermedio(factores: list[Factor], orden: list[Variable]) -> tuple[int, int]:
    """
    Simula la EV solo con ámbitos (sin calcular valores) y devuelve
    (número de variables del mayor ψ, número de entradas del mayor ψ).
    Es el parámetro del que depende el coste teórico.
    """
    ambitos = [set(f.ambito) for f in factores]
    max_vars, max_entradas = 0, 1
    for var in orden:
        con = [a for a in ambitos if var in a]
        sin = [a for a in ambitos if var not in a]
        psi = set().union(*con) if con else set()
        entradas = 1
        for v in psi:
            entradas *= v.cardinalidad
        max_vars, max_entradas = max(max_vars, len(psi)), max(max_entradas, entradas)
        ambitos = sin + [psi - {var}]
    return max_vars, max_entradas


# ---------------------------------------------------------------------------
# Experimentos
# ---------------------------------------------------------------------------
def experimento_n(rng: random.Random) -> list[dict]:
    print("\nExp. 1: tiempo frente a n (cadena, d = 2). Esperado: lineal")
    print(f"{'n':>6} {'tiempo (ms)':>12} {'ms / n':>10}")
    filas = []
    for n in range(20, 401, 40):
        variables, factores = red_cadena(n, 2, rng)
        orden = variables[:-1]  # consulta: la última variable
        t = medir(lambda: eliminacion_variables_inferencia_marginal(factores, orden))
        filas.append({"n": n, "tiempo_ms": t})
        print(f"{n:>6} {t:>12.2f} {t / n:>10.4f}")
    return filas


def experimento_d(rng: random.Random) -> list[dict]:
    print("\nExp. 2: tiempo frente a d (cadena, n = 20). Esperado: cuadrático (∝ d²)")
    print(f"{'d':>6} {'tiempo (ms)':>12} {'ms / d²':>10}")
    filas = []
    for d in range(2, 33, 3):
        variables, factores = red_cadena(20, d, rng)
        orden = variables[:-1]
        t = medir(lambda: eliminacion_variables_inferencia_marginal(factores, orden))
        filas.append({"d": d, "tiempo_ms": t})
        print(f"{d:>6} {t:>12.2f} {t / d**2:>10.4f}")
    return filas


def experimento_w(rng: random.Random) -> list[dict]:
    print("\nExp. 3: red en estrella con k hojas. Buen orden (hojas primero) frente a mal orden (centro primero)")
    print(f"{'k':>4} {'w bueno':>8} {'t bueno (ms)':>13} {'w malo':>7} {'t malo (ms)':>12} {'entradas ψ malo':>16}")
    filas = []
    for k in range(2, 17, 2):
        H, hojas, factores = red_estrella(k, rng)
        consulta = hojas[0]
        bueno = hojas[1:] + [H]          # cada hoja se elimina sola: ψ(H, Li) → w = 2
        malo = [H] + hojas[1:]           # al quitar H se juntan todos sus hijos: w = k + 1

        w_b, _ = tamano_max_intermedio(factores, bueno)
        w_m, ent_m = tamano_max_intermedio(factores, malo)
        t_b = medir(lambda: eliminacion_variables_inferencia_marginal(factores, bueno))
        t_m = medir(lambda: eliminacion_variables_inferencia_marginal(factores, malo))
        filas.append({"k": k, "w_bueno": w_b, "t_bueno_ms": t_b, "w_malo": w_m, "t_malo_ms": t_m,
                      "entradas_malo": ent_m})
        print(f"{k:>4} {w_b:>8} {t_b:>13.2f} {w_m:>7} {t_m:>12.2f} {ent_m:>16}")
    return filas


def experimento_tamano(filas_w: list[dict]) -> None:
    print("\nExp. 4: tiempo frente al tamaño del mayor factor intermedio (orden malo del Exp. 3)")
    print(f"{'entradas ψ':>11} {'tiempo (ms)':>12} {'µs / entrada':>13}")
    for f in filas_w:
        print(f"{f['entradas_malo']:>11} {f['t_malo_ms']:>12.2f} {1000 * f['t_malo_ms'] / f['entradas_malo']:>13.3f}")
    print("  Si µs/entrada fuera constante, el tiempo sería exactamente lineal en el tamaño de ψ.")
    print("  Crece algo porque cada entrada cuesta O(w): las llaves son tuplas de w valores que hay que")
    print("  construir y recortar. El coste real de esta implementación es más bien O(w · d^w).")


# ---------------------------------------------------------------------------
# Salida: CSV y gráficas
# ---------------------------------------------------------------------------
def guardar_csv(nombre: str, filas: list[dict]) -> None:
    with open(nombre, "w", newline="", encoding="utf-8") as fichero:
        escritor = csv.DictWriter(fichero, fieldnames=filas[0].keys())
        escritor.writeheader()
        escritor.writerows(filas)


def graficar(filas_n, filas_d, filas_w) -> None:
    try:
        import matplotlib
        matplotlib.use("Agg")  # sin ventana: solo guarda el PNG
        import matplotlib.pyplot as plt
    except ImportError:
        print("\nmatplotlib no está instalado: se omiten las gráficas (pip install matplotlib).")
        return

    fig, ejes = plt.subplots(2, 2, figsize=(11, 8))

    ejes[0, 0].plot([f["n"] for f in filas_n], [f["tiempo_ms"] for f in filas_n], "o-")
    ejes[0, 0].set(title="Exp. 1: cadena, d = 2 (lineal)", xlabel="n (variables)", ylabel="tiempo (ms)")

    ejes[0, 1].plot([f["d"] ** 2 for f in filas_d], [f["tiempo_ms"] for f in filas_d], "o-")
    ejes[0, 1].set(title="Exp. 2: cadena, n = 20 (lineal en d²)", xlabel="d²", ylabel="tiempo (ms)")

    k = [f["k"] for f in filas_w]
    ejes[1, 0].semilogy(k, [f["t_malo_ms"] for f in filas_w], "o-", label="mal orden (w = k+1)")
    ejes[1, 0].semilogy(k, [f["t_bueno_ms"] for f in filas_w], "s-", label="buen orden (w = 2)")
    ejes[1, 0].set(title="Exp. 3: estrella (escala log)", xlabel="k (hojas)", ylabel="tiempo (ms)")
    ejes[1, 0].legend()

    ejes[1, 1].plot([f["entradas_malo"] for f in filas_w], [f["t_malo_ms"] for f in filas_w], "o-")
    ejes[1, 1].set(title="Exp. 4: tiempo vs. tamaño del mayor ψ", xlabel="entradas del mayor ψ",
                   ylabel="tiempo (ms)")

    fig.tight_layout()
    fig.savefig("coste_temporal.png", dpi=120)
    print("\nGráficas guardadas en coste_temporal.png")


if __name__ == "__main__":
    rng = random.Random(2026)
    filas_n = experimento_n(rng)
    filas_d = experimento_d(rng)
    filas_w = experimento_w(rng)
    experimento_tamano(filas_w)

    guardar_csv("exp1_n.csv", filas_n)
    guardar_csv("exp2_d.csv", filas_d)
    guardar_csv("exp3_w.csv", filas_w)
    print("\nDatos guardados en exp1_n.csv, exp2_d.csv y exp3_w.csv")
    graficar(filas_n, filas_d, filas_w)