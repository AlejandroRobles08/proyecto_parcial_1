PROYECTO PARCIAL 1 - Computo Paralelo con Ley de Amdahl
=========================================================

Descripcion
-----------
Este proyecto procesa el dataset "Steam Reviews" (Kaggle, andrewmvd/steam-reviews)
para contar resenas positivas y negativas por juego, junto con el total de votos
utiles, comparando una implementacion secuencial contra una implementacion
paralela con multiprocessing (patron maestro-trabajador). Se mide aceleracion,
eficiencia y se estima la fraccion secuencial usando la Ley de Amdahl.

Requisitos
----------
- Python 3.10 o superior
- pip

Instalacion
-----------
1. Crea y activa un entorno virtual (PyCharm lo hace automaticamente al crear
   el proyecto):

   python -m venv .venv
   .venv\Scripts\activate      (Windows)

2. Instala las dependencias:

   pip install pandas numpy matplotlib

Preparacion del dataset
------------------------
1. Descarga el dataset "Steam Reviews" desde:
   https://www.kaggle.com/datasets/andrewmvd/steam-reviews

2. Descomprime el zip descargado y coloca el archivo CSV resultante en:
   data/raw/dataset.csv

3. Genera una muestra reducida para desarrollo (recomendado):
   Ejecuta lo siguiente en la consola de Python dentro del proyecto:

   import pandas as pd
   df = pd.read_csv("data/raw/dataset.csv", nrows=100000)
   df.to_csv("data/sample/muestra.csv", index=False)

Estructura del proyecto
------------------------
data/
  raw/        Dataset completo (no incluido en el repositorio, se descarga aparte)
  sample/     Muestra reducida para desarrollo y pruebas rapidas
resultados/
  tiempos.csv Tiempos registrados por el benchmark
  graficas/   Graficas de aceleracion y eficiencia generadas por benchmark.py
src/
  secuencial.py   Version de referencia sin paralelismo
  paralelo.py     Version paralela con multiprocessing (maestro-trabajador)
  benchmark.py    Automatiza las mediciones y genera las graficas

Como ejecutar
--------------
Todos los scripts se ejecutan directamente (no desde la consola interactiva
de PyCharm, por el uso de multiprocessing).

1. Version secuencial (referencia):
   python src/secuencial.py

2. Version paralela (por defecto usa 4 procesos; puede indicarse otro numero
   como argumento):
   python src/paralelo.py 4

3. Benchmark completo (corre secuencial y paralelo con 1, 2, 4 y 8 procesos,
   3 repeticiones cada uno, y genera las graficas):
   python src/benchmark.py

Los resultados se guardan en resultados/tiempos.csv, y las graficas de
aceleracion y eficiencia en resultados/graficas/.

Notas
-----
- Por defecto, los scripts trabajan sobre data/sample/muestra.csv. Para las
  mediciones finales del reporte, cambia la ruta usada (RUTA_DATOS en
  benchmark.py, o la variable "ruta" en secuencial.py y paralelo.py) para
  apuntar a RUTA_COMPLETA (data/raw/dataset.csv) o a un subconjunto mas
  grande, segun el tiempo de computo disponible.
- El dataset completo pesa varios GB y no esta incluido en este repositorio;
  debe descargarse por separado siguiendo las instrucciones de arriba.