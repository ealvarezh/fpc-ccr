import pandas as pd
import gc
from pathlib import Path

SILVER = Path(r"C:\Users\eah\apoyoconsultoria.com\File Server - Analytics\7 Datos\Datos abiertos\fissal\01_silver")
ANIOS = range(2016, 2023)
PATRON_CIE = r"^C(18|19|20)"

print("=" * 60)
print("FILTRADO CANCER COLORRECTAL (C18, C19, C20)")
print("=" * 60)

frames = []
for yr in ANIOS:
    df = pd.read_parquet(SILVER / f"FISSAL_PRESTACIONES_{yr}.parquet")
    mask = df["ATE_CODCIE10"].str.contains(PATRON_CIE, case=False, na=False)
    sub = df[mask].copy()
    frames.append(sub)
    print(f"  {yr}: {len(sub):>8,} registros  (de {len(df):>12,})")
    del df
    gc.collect()

df_ccr = pd.concat(frames, ignore_index=True)
del frames
gc.collect()

print(f"\nTotal registros: {len(df_ccr):>10,}")
print(f"Pacientes unicos: {df_ccr['NUM_DOC_CRYPTO'].nunique():>8,}")

print(f"\nRegistros por codigo CIE-10:")
print(df_ccr["ATE_CODCIE10"].value_counts().head(20).to_string())

print(f"\nRegistros por grupo CIE-10:")
print(df_ccr["ATE_GRUPOCIE10"].value_counts().to_string())

print(f"\nPacientes por anio de atencion:")
for yr in sorted(df_ccr["ANIO_ATENCION"].dropna().unique()):
    n = df_ccr.loc[df_ccr["ANIO_ATENCION"] == yr, "NUM_DOC_CRYPTO"].nunique()
    print(f"  {int(yr)}: {n:>6,}")

print(f"\nDistribucion por sexo:")
print(df_ccr.groupby("SEXO")["NUM_DOC_CRYPTO"].nunique().to_string())

print(f"\nTipo de atencion:")
print(df_ccr["TIPO_ATENC"].value_counts().to_string())

print(f"\nTipo de consumo:")
print(df_ccr["ATE_TIPOCONSUMO"].value_counts().to_string())

salida = SILVER / "FISSAL_CANCER_COLORRECTAL_2016_2022.parquet"
df_ccr.to_parquet(salida, index=False)
print(f"\nGuardado en: {salida}")
print(f"Shape: {df_ccr.shape}")
