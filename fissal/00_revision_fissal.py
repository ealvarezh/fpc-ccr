import pandas as pd
from pathlib import Path

ruta = Path(r"C:\Users\eah\apoyoconsultoria.com\File Server - Analytics\7 Datos\Datos abiertos\fissal\2022")
ruta_final = Path(r"C:\Users\eah\apoyoconsultoria.com\File Server - Analytics\7 Datos\Datos abiertos\fissal\00_bronce")
df_final = pd.concat([pd.read_csv(ruta / f"FISSAL_PRESTACIONES_2022_{i}_v2.csv", sep="|", encoding="utf-8", low_memory=False) for i in range(1, 15)], ignore_index=True)

for col in df_final.select_dtypes(include="object").columns:
    df_final[col] = df_final[col].astype(str)

df_final.to_parquet(ruta_final / "FISSAL_PRESTACIONES_2022.parquet", index=False)
print(df_final.shape)

###########################################################################
ruta = Path(r"C:\Users\eah\apoyoconsultoria.com\File Server - Analytics\7 Datos\Datos abiertos\fissal\2021")

df_final = pd.concat([pd.read_csv(ruta / f"FISSAL_PRESTACIONES_2021_{i}_v2.csv", sep="|", encoding="utf-8", low_memory=False) for i in range(1, 12)], ignore_index=True)

for col in df_final.select_dtypes(include="object").columns:
    df_final[col] = df_final[col].astype(str)

df_final.to_parquet(ruta_final / "FISSAL_PRESTACIONES_2021.parquet", index=False)
print(df_final.shape)

###########################################################################
ruta = Path(r"C:\Users\eah\apoyoconsultoria.com\File Server - Analytics\7 Datos\Datos abiertos\fissal\2020")

df_final = pd.concat([pd.read_csv(ruta / f"FISSAL_PRESTACIONES_2020_{i}_v2.csv", sep="|", encoding="utf-8", low_memory=False) for i in range(1, 13)], ignore_index=True)

for col in df_final.select_dtypes(include="object").columns:
    df_final[col] = df_final[col].astype(str)

df_final.to_parquet(ruta_final / "FISSAL_PRESTACIONES_2020.parquet", index=False)
print(df_final.shape)

###########################################################################
ruta = Path(r"C:\Users\eah\apoyoconsultoria.com\File Server - Analytics\7 Datos\Datos abiertos\fissal\2019")

df_final = pd.concat([pd.read_csv(ruta / f"FISSAL_PRESTACIONES_2019_{i}_v2.csv", sep="|", encoding="utf-8", low_memory=False) for i in range(1, 8)], ignore_index=True)

for col in df_final.select_dtypes(include="object").columns:
    df_final[col] = df_final[col].astype(str)

df_final.to_parquet(ruta_final / "FISSAL_PRESTACIONES_2019.parquet", index=False)
print(df_final.shape)

###########################################################################
ruta = Path(r"C:\Users\eah\apoyoconsultoria.com\File Server - Analytics\7 Datos\Datos abiertos\fissal\2018")

df_final = pd.concat([pd.read_csv(ruta / f"FISSAL_PRESTACIONES_2018_{i}_v2.csv", sep="|", encoding="utf-8", low_memory=False) for i in range(1,11)], ignore_index=True)

for col in df_final.select_dtypes(include="object").columns:
    df_final[col] = df_final[col].astype(str)

df_final.to_parquet(ruta_final / "FISSAL_PRESTACIONES_2018.parquet", index=False)
print(df_final.shape)


###########################################################################
ruta = Path(r"C:\Users\eah\apoyoconsultoria.com\File Server - Analytics\7 Datos\Datos abiertos\fissal\2017")

df_final = pd.concat([pd.read_csv(ruta / f"FISSAL_PRESTACIONES_2017_{i}_v2.csv", sep="|", encoding="utf-8", low_memory=False) for i in range(1,8)], ignore_index=True)

for col in df_final.select_dtypes(include="object").columns:
    df_final[col] = df_final[col].astype(str)

df_final.to_parquet(ruta_final / "FISSAL_PRESTACIONES_2017.parquet", index=False)
print(df_final.shape)

###########################################################################
ruta = Path(r"C:\Users\eah\apoyoconsultoria.com\File Server - Analytics\7 Datos\Datos abiertos\fissal\2016")

df_final = pd.concat([pd.read_csv(ruta / f"FISSAL_PRESTACIONES_2016_{i}_v2.csv", sep="|", encoding="utf-8", low_memory=False) for i in range(1,9)], ignore_index=True)

for col in df_final.select_dtypes(include="object").columns:
    df_final[col] = df_final[col].astype(str)

df_final.to_parquet(ruta_final / "FISSAL_PRESTACIONES_2016.parquet", index=False)
print(df_final.shape)