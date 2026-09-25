import pandas as pd

df_muestra = pd.read_csv("data/raw/dataset.csv", nrows=100000)
df_muestra.to_csv("data/sample/muestra.csv", index=False)
print(f"Muestra guardada: {len(df_muestra)} filas")