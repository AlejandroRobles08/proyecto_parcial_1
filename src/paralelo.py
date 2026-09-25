from pathlib import Path
from collections import defaultdict
import multiprocessing as mp
import pandas as pd
import numpy as np
import time
import sys

BASE_DIR = Path(__file__).resolve().parent.parent
RUTA_MUESTRA = BASE_DIR / "data" / "sample" / "muestra.csv"
RUTA_COMPLETA = BASE_DIR / "data" / "raw" / "dataset.csv"


def procesar_bloque(bloque):
    resultados = defaultdict(lambda: {"positivas": 0, "negativas": 0, "votos_utiles": 0})

    for fila in bloque.itertuples(index=False):
        juego = fila.app_name
        if pd.isna(juego):
            continue

        if fila.review_score == 1:
            resultados[juego]["positivas"] += 1
        else:
            resultados[juego]["negativas"] += 1

        resultados[juego]["votos_utiles"] += fila.review_votes

    return dict(resultados)


def combinar_resultados(lista_resultados):
    combinado = defaultdict(lambda: {"positivas": 0, "negativas": 0, "votos_utiles": 0})

    for parcial in lista_resultados:
        for juego, datos in parcial.items():
            combinado[juego]["positivas"] += datos["positivas"]
            combinado[juego]["negativas"] += datos["negativas"]
            combinado[juego]["votos_utiles"] += datos["votos_utiles"]

    return dict(combinado)


def dividir_dataframe(df, n_partes):
    # Divide los INDICES en n_partes y extrae cada bloque con iloc,
    # asi cada pedazo sigue siendo un DataFrame real (no un ndarray)
    indices = np.array_split(np.arange(len(df)), n_partes)
    return [df.iloc[idx] for idx in indices]


def procesar_paralelo(ruta_csv, n_procesos):
    df = pd.read_csv(ruta_csv)
    bloques = dividir_dataframe(df, n_procesos)  # <- clave: usa esta funcion, no np.array_split(df, ...)

    with mp.Pool(processes=n_procesos) as pool:
        resultados_parciales = pool.map(procesar_bloque, bloques)

    return combinar_resultados(resultados_parciales)


if __name__ == "__main__":
    ruta = RUTA_MUESTRA
    n_procesos = int(sys.argv[1]) if len(sys.argv) > 1 else 4

    inicio = time.perf_counter()
    resultados = procesar_paralelo(ruta, n_procesos)
    fin = time.perf_counter()

    print(f"Procesos usados: {n_procesos}")
    print(f"Tiempo paralelo: {fin - inicio:.4f} segundos")
    print(f"Juegos procesados: {len(resultados)}")

    for juego, datos in list(resultados.items())[:5]:
        print(f"{juego}: {datos}")