"""
Version PARALELA del procesamiento, usando el patron maestro-trabajador
con la libreria multiprocessing.

Cada worker es un PROCESO independiente del sistema operativo (no un hilo),
lo que significa que cada uno tiene su propia copia de memoria: el "maestro"
(este script) tiene que enviarle a cada worker su porcion de datos (esto se
hace automaticamente via pickle/serializacion), y luego recolectar y combinar
los resultados parciales que cada worker regresa.
"""

from pathlib import Path
from collections import defaultdict
import multiprocessing as mp
import pandas as pd
import numpy as np
import time
import sys

BASE_DIR = Path(__file__).resolve().parent.parent
RUTA_MUESTRA = BASE_DIR / "data" / "sample" / "muestra_grande.csv"
RUTA_COMPLETA = BASE_DIR / "data" / "raw" / "dataset.csv"
COLUMNAS_NECESARIAS = ["app_name", "review_score", "review_votes"]


def procesar_bloque(bloque):
    """
    Funcion que ejecuta CADA WORKER de forma independiente sobre su
    porcion del DataFrame (su "bloque"). La logica interna es identica
    a procesar_secuencial(), la diferencia es que aqui solo se ve una
    fraccion de los datos totales, no el DataFrame completo.

    Esta funcion debe estar definida a nivel de modulo (no anidada
    dentro de otra funcion) para que multiprocessing pueda "picklearla"
    y enviarla a cada proceso worker.
    """
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
    """
    Este es el paso de REDUCCION: el proceso maestro recibe una lista
    de diccionarios parciales (uno por cada worker) y los suma en un
    solo diccionario final.

    Es importante notar que esta suma es conmutativa y asociativa
    (sumar en cualquier orden da el mismo resultado), lo cual es lo
    que hace seguro combinar resultados de workers que terminaron en
    momentos distintos y en cualquier orden.
    """
    combinado = defaultdict(lambda: {"positivas": 0, "negativas": 0, "votos_utiles": 0})

    for parcial in lista_resultados:
        for juego, datos in parcial.items():
            combinado[juego]["positivas"] += datos["positivas"]
            combinado[juego]["negativas"] += datos["negativas"]
            combinado[juego]["votos_utiles"] += datos["votos_utiles"]

    return dict(combinado)


def dividir_dataframe(df, n_partes):
    """
    Divide el DataFrame en n_partes bloques aproximadamente iguales.

    IMPORTANTE: dividimos los INDICES (numeros de fila) con
    np.array_split(), y luego extraemos cada bloque con .iloc[].
    Si en vez de esto se hace np.array_split(df, n_partes) directamente
    sobre el DataFrame, numpy puede convertir cada pedazo en un arreglo
    plano (numpy.ndarray) en vez de mantenerlo como DataFrame, lo cual
    rompe el uso de itertuples() dentro de procesar_bloque().
    """
    indices = np.array_split(np.arange(len(df)), n_partes)
    return [df.iloc[idx] for idx in indices]


def procesar_paralelo(df, n_procesos):
    """
    Orquesta el patron maestro-trabajador completo:
      1. El maestro divide el DataFrame en n_procesos bloques (dividir_dataframe)
      2. Crea un Pool de procesos y les asigna un bloque a cada uno (pool.map)
      3. Cada worker procesa su bloque de forma independiente (procesar_bloque)
      4. El maestro combina todos los resultados parciales (combinar_resultados)

    pool.map() es BLOQUEANTE: espera a que todos los workers terminen
    antes de continuar, lo cual es justo lo que queremos para medir el
    tiempo total de la operacion paralela completa.
    """
    bloques = dividir_dataframe(df, n_procesos)

    # El "with" asegura que el Pool cierre sus procesos correctamente
    # al terminar, incluso si ocurre un error durante el procesamiento
    with mp.Pool(processes=n_procesos) as pool:
        resultados_parciales = pool.map(procesar_bloque, bloques)

    return combinar_resultados(resultados_parciales)


if __name__ == "__main__":
    # Igual que en secuencial.py: la lectura del CSV queda fuera de la
    # medicion de tiempo, para medir solo el costo del paralelismo en si
    df = pd.read_csv(RUTA_MUESTRA, usecols=COLUMNAS_NECESARIAS)

    # Permite indicar el numero de procesos como argumento de linea de
    # comandos (por ejemplo: python paralelo.py 8), o usa 4 por defecto
    n_procesos = int(sys.argv[1]) if len(sys.argv) > 1 else 4

    inicio = time.perf_counter()
    resultados = procesar_paralelo(df, n_procesos)
    fin = time.perf_counter()

    print(f"Procesos usados: {n_procesos}")
    print(f"Tiempo paralelo: {fin - inicio:.4f} segundos")
    print(f"Juegos procesados: {len(resultados)}")

    for juego, datos in list(resultados.items())[:5]:
        print(f"{juego}: {datos}")