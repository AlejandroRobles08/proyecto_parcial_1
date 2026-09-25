#versión sin paralelismo
#se usará tanto para verificar resultados como para tu tiempo base (n=1):
from pathlib import Path
from collections import defaultdict
import pandas as pd
import time

# Rutas calculadas desde la ubicación del script, así no dependen
# de cual sea el "working directory" configurado en PyCharm
BASE_DIR = Path(__file__).resolve().parent.parent
RUTA_MUESTRA = BASE_DIR / "data" / "sample" / "muestra.csv"
RUTA_COMPLETA = BASE_DIR / "data" / "raw" / "dataset.csv"


def procesar_secuencial(ruta_csv):
    # Lee el CSV y cuenta reseñas positivas/negativas y votos útiles por juego.
    # Devuelve: {app_name: {"positivas": int, "negativas": int, "votos_utiles": int}}
    resultados = defaultdict(lambda: {"positivas": 0, "negativas": 0, "votos_utiles": 0})

    df = pd.read_csv(ruta_csv)

    # Usamos itertuples() en vez de un groupby vectorizado a propósito:
    # el objetivo del proyecto es que TU implementes la logica de paralelizacion,
    # y un groupby de pandas ya resuelve todo internamente en C, dejando
    # nada que paralelizar de forma significativa.
    for fila in df.itertuples(index=False):
        juego = fila.app_name
        if pd.isna(juego):
            continue

        if fila.review_score == 1:
            resultados[juego]["positivas"] += 1
        else:
            resultados[juego]["negativas"] += 1

        resultados[juego]["votos_utiles"] += fila.review_votes

    return dict(resultados)


if __name__ == "__main__":
    ruta = RUTA_MUESTRA  # cambia a RUTA_COMPLETA cuando corras las mediciones finales

    inicio = time.perf_counter()
    resultados = procesar_secuencial(ruta)
    fin = time.perf_counter()

    print(f"Tiempo secuencial: {fin - inicio:.4f} segundos")
    print(f"Juegos procesados: {len(resultados)}")

    for juego, datos in list(resultados.items())[:5]:
        print(f"{juego}: {datos}")