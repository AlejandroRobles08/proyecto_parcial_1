"""
Version SECUENCIAL (sin paralelismo) del procesamiento del dataset Steam Reviews.
Este script sirve dos propositos:
1. Es la version de REFERENCIA para verificar que la version paralela
   produce exactamente los mismos resultados (correctitud).
2. Su tiempo de ejecucion es la base (T1) para calcular aceleracion
   y eficiencia en el benchmark.

Metrica calculada: por cada juego (app_name), cuenta cuantas resenas son
positivas, cuantas negativas, y suma el total de votos utiles.
"""

from pathlib import Path
from collections import defaultdict
import pandas as pd
import time

# BASE_DIR sube dos niveles desde este archivo (src/ -> raiz del proyecto)
# Usar Path(__file__) en vez de rutas fijas evita errores si el proyecto
# se mueve o se renombra la carpeta contenedora.
BASE_DIR = Path(__file__).resolve().parent.parent

RUTA_MUESTRA = BASE_DIR / "data" / "sample" / "muestra_grande.csv"
RUTA_COMPLETA = BASE_DIR / "data" / "raw" / "dataset.csv"

# Solo necesitamos estas 3 columnas para el calculo. Cargar/mover columnas
# de mas (como review_text, que puede ser texto largo) desperdicia memoria
# y tiempo, sobre todo cuando se comparte entre procesos en paralelo.py.
COLUMNAS_NECESARIAS = ["app_name", "review_score", "review_votes"]


def procesar_secuencial(df):
    """
    Recorre el DataFrame fila por fila y acumula conteos por juego.

    Se usa un defaultdict con un diccionario por defecto (positivas=0,
    negativas=0, votos_utiles=0) para no tener que checar manualmente
    si el juego ya existe en el diccionario antes de sumarle algo.

    itertuples(index=False) se elige sobre iterrows() porque es
    significativamente mas rapido (itertuples genera namedtuples en vez
    de Series de pandas, que tienen mucho mas overhead por fila).

    A proposito NO se usa df.groupby() (que seria mucho mas rapido, ya
    que esta implementado en C dentro de pandas), porque el objetivo del
    proyecto es implementar Y MEDIR nuestra propia logica de paralelismo,
    algo que no seria posible si dejamos que pandas resuelva todo
    internamente de forma ya optimizada.
    """
    resultados = defaultdict(lambda: {"positivas": 0, "negativas": 0, "votos_utiles": 0})

    for fila in df.itertuples(index=False):
        juego = fila.app_name

        # Algunas filas pueden no tener nombre de juego (dato faltante);
        # las saltamos para no ensuciar el diccionario de resultados
        if pd.isna(juego):
            continue

        # En este dataset, review_score = 1 significa resena positiva,
        # cualquier otro valor (tipicamente -1) se trata como negativa
        if fila.review_score == 1:
            resultados[juego]["positivas"] += 1
        else:
            resultados[juego]["negativas"] += 1

        resultados[juego]["votos_utiles"] += fila.review_votes

    # Convertimos de defaultdict a dict normal antes de retornar, para
    # evitar que el llamador cree entradas nuevas por accidente al
    # consultar una clave que no existe
    return dict(resultados)


if __name__ == "__main__":
    # La lectura del CSV se hace aqui, FUERA de la medicion de tiempo,
    # porque el objetivo es medir el costo del PROCESAMIENTO, no del
    # I/O de disco (que es igual sin importar si es secuencial o paralelo)
    df = pd.read_csv(RUTA_MUESTRA, usecols=COLUMNAS_NECESARIAS)

    # perf_counter() es mas preciso que time.time() para medir duraciones
    # cortas, ya que no se ve afectado por ajustes del reloj del sistema
    inicio = time.perf_counter()
    resultados = procesar_secuencial(df)
    fin = time.perf_counter()

    print(f"Tiempo secuencial: {fin - inicio:.4f} segundos")
    print(f"Juegos procesados: {len(resultados)}")

    # Solo mostramos los primeros 5 como muestra, para no inundar la consola
    # con potencialmente cientos de juegos distintos
    for juego, datos in list(resultados.items())[:5]:
        print(f"{juego}: {datos}")