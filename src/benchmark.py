"""
Automatiza las mediciones de rendimiento que pide el entregable:
  - Corre la version secuencial y la paralela (con 1, 2, 4 y 8 procesos)
  - Repite cada configuracion 3 veces (minimo pedido) para reducir el
    efecto de variaciones aleatorias del sistema operativo
  - Calcula aceleracion, eficiencia, y estima la fraccion secuencial
    usando la Ley de Amdahl
  - Genera las graficas de aceleracion y eficiencia en PNG
"""

from pathlib import Path
import time
import csv
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from secuencial import procesar_secuencial
from paralelo import procesar_paralelo

BASE_DIR = Path(__file__).resolve().parent.parent
RUTA_DATOS = BASE_DIR / "data" / "sample" / "muestra_grande.csv"
RUTA_TIEMPOS = BASE_DIR / "resultados" / "tiempos.csv"
RUTA_GRAFICAS = BASE_DIR / "resultados" / "graficas"
COLUMNAS_NECESARIAS = ["app_name", "review_score", "review_votes"]

# Numeros de procesos a probar, y cuantas veces repetir cada uno
NUM_PROCESOS = [1, 2, 4, 8]
CORRIDAS = 3


def medir_tiempo(funcion, *args):
    """
    Funcion auxiliar generica: ejecuta cualquier funcion pasandole los
    argumentos dados, y regresa cuanto tiempo tardo (en segundos).
    El *args permite reutilizar esta misma funcion tanto para
    procesar_secuencial(df) como para procesar_paralelo(df, n).
    """
    inicio = time.perf_counter()
    funcion(*args)
    return time.perf_counter() - inicio


def correr_benchmark():
    """
    Ejecuta todas las mediciones (secuencial + cada nivel de paralelismo,
    repetido CORRIDAS veces) y guarda cada tiempo individual en una lista
    de diccionarios, que luego se exporta a CSV.
    """
    RUTA_GRAFICAS.mkdir(parents=True, exist_ok=True)
    filas = []

    # El CSV se carga UNA SOLA VEZ aqui, y se reutiliza el mismo
    # DataFrame en todas las 15 mediciones (3 + 4x3). Si se leyera
    # dentro de cada corrida, ese tiempo de I/O (identico sin importar
    # el numero de procesos) inflaria artificialmente todas las
    # mediciones por igual, ocultando el efecto real del paralelismo.
    print("Cargando datos (una sola vez, fuera de las mediciones)...")
    df = pd.read_csv(RUTA_DATOS, usecols=COLUMNAS_NECESARIAS)
    print(f"Filas cargadas: {len(df)}")

    print("Corriendo version secuencial...")
    for corrida in range(1, CORRIDAS + 1):
        t = medir_tiempo(procesar_secuencial, df)
        filas.append({"tipo": "secuencial", "n_procesos": 1, "corrida": corrida, "tiempo": t})
        print(f"  corrida {corrida}: {t:.4f}s")

    for n in NUM_PROCESOS:
        print(f"Corriendo version paralela con {n} proceso(s)...")
        for corrida in range(1, CORRIDAS + 1):
            t = medir_tiempo(procesar_paralelo, df, n)
            filas.append({"tipo": "paralelo", "n_procesos": n, "corrida": corrida, "tiempo": t})
            print(f"  corrida {corrida}: {t:.4f}s")

    guardar_csv(filas)
    return filas


def guardar_csv(filas):
    """Exporta todas las mediciones individuales (sin promediar) a CSV,
    para que quede como evidencia cruda reproducible en el reporte."""
    with open(RUTA_TIEMPOS, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["tipo", "n_procesos", "corrida", "tiempo"])
        writer.writeheader()
        writer.writerows(filas)
    print(f"\nTiempos guardados en {RUTA_TIEMPOS}")


def promediar_por_n(filas, tipo="paralelo"):
    """Calcula el tiempo promedio de las 3 corridas para cada numero
    de procesos, filtrando solo las filas del 'tipo' indicado."""
    promedios = {}
    for n in NUM_PROCESOS:
        tiempos = [f["tiempo"] for f in filas if f["tipo"] == tipo and f["n_procesos"] == n]
        promedios[n] = sum(tiempos) / len(tiempos)
    return promedios


def modelo_amdahl(n, p):
    """
    Formula de la Ley de Amdahl: dado un numero de procesos n y una
    fraccion paralelizable p (entre 0 y 1), calcula la aceleracion
    TEORICA maxima esperada.

    (1 - p) es la fraccion secuencial: la parte del trabajo que NO
    se beneficia de agregar mas procesos.
    """
    return 1 / ((1 - p) + p / n)


def estimar_fraccion_paralela(ns, aceleraciones):
    """
    Despeja algebraicamente el valor de p (fraccion paralelizable) de
    la formula de Amdahl, usando cada punto medido (n, aceleracion)
    donde n > 1 (con n=1 la formula no aporta informacion, ya que la
    aceleracion siempre es 1.0 por definicion).

    Se promedian las estimaciones de p obtenidas con cada n para dar
    un resultado mas robusto que depender de un solo punto de datos.
    """
    estimaciones = []
    for n, s in zip(ns, aceleraciones):
        if n == 1:
            continue
        p = (1 - 1 / s) / (1 - 1 / n)
        estimaciones.append(p)
    return sum(estimaciones) / len(estimaciones)


def analizar_resultados(filas):
    """
    A partir de las mediciones crudas, calcula:
    - Aceleracion: T(1) / T(n), donde T(1) es el tiempo con 1 solo
      proceso (nuestra linea base)
    - Eficiencia: aceleracion / n (que tan bien se aprovecha cada
      proceso agregado; 100% seria aprovechamiento perfecto)
    - La fraccion secuencial estimada segun Amdahl
    """
    promedios = promediar_por_n(filas, tipo="paralelo")
    t1 = promedios[1]

    ns = sorted(promedios.keys())
    aceleraciones = [t1 / promedios[n] for n in ns]
    eficiencias = [a / n for a, n in zip(aceleraciones, ns)]

    p_estimado = estimar_fraccion_paralela(ns, aceleraciones)
    fraccion_secuencial = 1 - p_estimado

    print("\n--- Resultados ---")
    for n, a, e in zip(ns, aceleraciones, eficiencias):
        print(f"n={n}: tiempo={promedios[n]:.4f}s, aceleracion={a:.2f}x, eficiencia={e:.2%}")

    print(f"\nFraccion paralelizable estimada (p): {p_estimado:.4f}")
    print(f"Fraccion secuencial estimada (1-p): {fraccion_secuencial:.4f}")

    graficar(ns, aceleraciones, eficiencias, p_estimado)
    return ns, aceleraciones, eficiencias, p_estimado


def graficar(ns, aceleraciones, eficiencias, p_estimado):
    """Genera y guarda dos graficas PNG: aceleracion vs. numero de
    procesos (comparando lo medido contra lo ideal y lo predicho por
    Amdahl), y eficiencia vs. numero de procesos."""

    # 200 puntos entre 1 y el maximo de procesos, para dibujar la curva
    # teorica de Amdahl como una linea suave en vez de solo 4 puntos
    ns_finos = np.linspace(1, max(ns), 200)
    aceleracion_teorica = [modelo_amdahl(n, p_estimado) for n in ns_finos]

    plt.figure(figsize=(8, 5))
    plt.plot(ns, aceleraciones, "o-", label="Aceleracion medida")
    plt.plot(ns_finos, aceleracion_teorica, "--", label=f"Amdahl teorico (p={p_estimado:.2f})")
    plt.plot(ns_finos, ns_finos, ":", color="gray", label="Aceleracion ideal (lineal)")
    plt.xlabel("Numero de procesos")
    plt.ylabel("Aceleracion")
    plt.title("Aceleracion vs numero de procesos")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.savefig(RUTA_GRAFICAS / "aceleracion.png", dpi=150, bbox_inches="tight")
    plt.close()

    plt.figure(figsize=(8, 5))
    plt.plot(ns, eficiencias, "o-", color="darkorange")
    plt.axhline(1.0, color="gray", linestyle=":", label="Eficiencia ideal")
    plt.xlabel("Numero de procesos")
    plt.ylabel("Eficiencia")
    plt.title("Eficiencia vs numero de procesos")
    plt.ylim(0, 1.1)
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.savefig(RUTA_GRAFICAS / "eficiencia.png", dpi=150, bbox_inches="tight")
    plt.close()

    print(f"Graficas guardadas en {RUTA_GRAFICAS}")


if __name__ == "__main__":
    filas = correr_benchmark()
    analizar_resultados(filas)