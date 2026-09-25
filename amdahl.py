import time
import multiprocessing as mp

def parte_secuencial(duracion):
    # Simula trabajo que no se puede dividir (ej: I/O, lógica dependiente)
    time.sleep(duracion)

def tarea_paralelizable(_):
    # Simula una unidad de trabajo paralelizable (ej: procesar un chunk de datos)
    total = 0
    for i in range(10_000_000):
        total += i
    return total

def ejecutar(n_procesos, n_tareas=8):
    inicio = time.time()

    parte_secuencial(0.5)  # parte fija, no paralelizable

    with mp.Pool(n_procesos) as pool:
        pool.map(tarea_paralelizable, range(n_tareas))

    return time.time() - inicio

if __name__ == "__main__":
    tiempo_base = ejecutar(1)
    print(f"Con 1 proceso: {tiempo_base:.2f}s (referencia)")

    for n in [2, 4, 8]:
        t = ejecutar(n)
        print(f"Con {n} procesos: {t:.2f}s -> aceleración real = {tiempo_base/t:.2f}x")