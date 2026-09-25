import pandas as pd

df_grande = pd.read_csv("data/raw/dataset.csv", nrows=1500000)
df_grande.to_csv("data/sample/muestra_grande.csv", index=False)
print(f"Muestra guardada: {len(df_grande)} filas")