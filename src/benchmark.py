from pathlib import Path
import time
import csv
import numpy as np
import matplotlib.pyplot as plt

from secuencial import procesar_secuencial
from paralelo import procesar_paralelo

BASE_DIR = Path(__file__).resolve().parent.parent
RUTA_DATOS = BASE_DIR / "data" / "sample" / "muestra.csv"  # cambia a un archivo mas grande para la corrida final
RUTA_TIEMPOS = BASE_DIR / "resultados" / "tiempos.csv"
RUTA_GRAFICAS = BASE_DIR / "resultados" / "graficas"

NUM_PROCESOS = [1, 2, 4, 8]
CORRIDAS = 3


def medir_tiempo(funcion, *args):
    inicio = time.perf_counter()
    funcion(*args)
    return time.perf_counter() - inicio


def correr_benchmark():
    RUTA_GRAFICAS.mkdir(parents=True, exist_ok=True)
    filas = []

    print("Corriendo version secuencial...")
    for corrida in range(1, CORRIDAS + 1):
        t = medir_tiempo(procesar_secuencial, RUTA_DATOS)
        filas.append({"tipo": "secuencial", "n_procesos": 1, "corrida": corrida, "tiempo": t})
        print(f"  corrida {corrida}: {t:.4f}s")

    for n in NUM_PROCESOS:
        print(f"Corriendo version paralela con {n} proceso(s)...")
        for corrida in range(1, CORRIDAS + 1):
            t = medir_tiempo(procesar_paralelo, RUTA_DATOS, n)
            filas.append({"tipo": "paralelo", "n_procesos": n, "corrida": corrida, "tiempo": t})
            print(f"  corrida {corrida}: {t:.4f}s")

    guardar_csv(filas)
    return filas


def guardar_csv(filas):
    with open(RUTA_TIEMPOS, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["tipo", "n_procesos", "corrida", "tiempo"])
        writer.writeheader()
        writer.writerows(filas)
    print(f"\nTiempos guardados en {RUTA_TIEMPOS}")


def promediar_por_n(filas, tipo="paralelo"):
    promedios = {}
    for n in NUM_PROCESOS:
        tiempos = [f["tiempo"] for f in filas if f["tipo"] == tipo and f["n_procesos"] == n]
        promedios[n] = sum(tiempos) / len(tiempos)
    return promedios


def modelo_amdahl(n, p):
    return 1 / ((1 - p) + p / n)


def estimar_fraccion_paralela(ns, aceleraciones):
    estimaciones = []
    for n, s in zip(ns, aceleraciones):
        if n == 1:
            continue
        p = (1 - 1 / s) / (1 - 1 / n)
        estimaciones.append(p)
    return sum(estimaciones) / len(estimaciones)


def analizar_resultados(filas):
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