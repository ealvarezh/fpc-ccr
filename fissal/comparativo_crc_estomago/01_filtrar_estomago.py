import sys
import pandas as pd
import numpy as np
import gc
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SILVER = Path(r"C:\Users\eah\apoyoconsultoria.com\File Server - Analytics\7 Datos\Datos abiertos\fissal\01_silver")
ANIOS = range(2016, 2023)
PATRON_CIE = r"^C16"
FECHA_CORTE = pd.Timestamp("2022-12-31")

print("=" * 70)
print("FILTRADO CANCER DE ESTOMAGO (C16)")
print("=" * 70)

frames = []
for yr in ANIOS:
    df = pd.read_parquet(SILVER / f"FISSAL_PRESTACIONES_{yr}.parquet")
    mask = df["ATE_CODCIE10"].str.contains(PATRON_CIE, case=False, na=False)
    sub = df[mask].copy()
    frames.append(sub)
    print(f"  {yr}: {len(sub):>8,} registros  (de {len(df):>12,})")
    del df
    gc.collect()

df_est = pd.concat(frames, ignore_index=True)
del frames
gc.collect()

print(f"\nTotal registros: {len(df_est):>10,}")
print(f"Pacientes unicos: {df_est['NUM_DOC_CRYPTO'].nunique():>8,}")

salida = SILVER / "FISSAL_CANCER_ESTOMAGO_2016_2022.parquet"
df_est.to_parquet(salida, index=False)
print(f"\nGuardado: {salida}")

# =====================================================================
# PERFIL DE PACIENTE SIMPLIFICADO
# =====================================================================
print("\n" + "=" * 70)
print("PERFIL DE PACIENTE (SIMPLIFICADO)")
print("=" * 70)

pac = (
    df_est.groupby("NUM_DOC_CRYPTO", sort=False)
    .agg(
        SEXO=("SEXO", "first"),
        ATE_FECNAC=("ATE_FECNAC", "first"),
        PRIMERA_ATENCION=("ATE_FECATENCION", "min"),
        ULTIMA_ATENCION=("ATE_FECATENCION", "max"),
        FEC_FALLECIMIENTO=("FEC_FALLECIMIENTO", "first"),
        DEPARTAMENTO=("DEPARTAMENTO_PAC", lambda x: x.mode().iloc[0] if not x.mode().empty else pd.NA),
        PROVINCIA=("PROVINCIA_PAC", lambda x: x.mode().iloc[0] if not x.mode().empty else pd.NA),
        MONTO_BRUTO_TOTAL=("ATE_MONTOBRUTO", "sum"),
        MONTO_NETO_TOTAL=("ATE_MONTONETO", "sum"),
    )
    .reset_index()
)

pac["PRIMERA_ATENCION"] = pd.to_datetime(pac["PRIMERA_ATENCION"], errors="coerce")
pac["ULTIMA_ATENCION"] = pd.to_datetime(pac["ULTIMA_ATENCION"], errors="coerce")
pac["ATE_FECNAC"] = pd.to_datetime(pac["ATE_FECNAC"], errors="coerce")
pac["FEC_FALLECIMIENTO"] = pd.to_datetime(pac["FEC_FALLECIMIENTO"], errors="coerce")

pac["FALLECIDO"] = pac["FEC_FALLECIMIENTO"].notna()
pac["EDAD_PRIMERA_ATENCION"] = np.floor((pac["PRIMERA_ATENCION"] - pac["ATE_FECNAC"]).dt.days / 365.25)

# Mismo criterio conservador que CRC: cancer gastrico pediatrico es igual de
# raro en la literatura medica: edades negativas o <10 anios casi siempre
# reflejan error de captura de ATE_FECNAC o codificacion CIE-10.
n_edad_invalida = ((pac["EDAD_PRIMERA_ATENCION"] < 10) | (pac["EDAD_PRIMERA_ATENCION"] > 100)).sum()
print(f"\n[Calidad de datos] Pacientes con EDAD_PRIMERA_ATENCION no confiable "
      f"(<10 o >100 anios): {n_edad_invalida:,} -> se marcan como NA")
pac.loc[(pac["EDAD_PRIMERA_ATENCION"] < 10) | (pac["EDAD_PRIMERA_ATENCION"] > 100), "EDAD_PRIMERA_ATENCION"] = pd.NA

bins = [0, 18, 30, 40, 50, 60, 70, 80, 120]
labels = ["0-17", "18-29", "30-39", "40-49", "50-59", "60-69", "70-79", "80+"]
pac["RANGO_EDAD"] = pd.cut(pac["EDAD_PRIMERA_ATENCION"], bins=bins, labels=labels, right=False)

pac["SUPERVIVENCIA_DIAS"] = np.where(
    pac["FALLECIDO"],
    (pac["FEC_FALLECIMIENTO"] - pac["PRIMERA_ATENCION"]).dt.days,
    (FECHA_CORTE - pac["PRIMERA_ATENCION"]).dt.days,
)
pac["SUPERVIVENCIA_DIAS"] = pd.to_numeric(pac["SUPERVIVENCIA_DIAS"], errors="coerce")

print(f"\nPacientes procesados: {len(pac):,}")
print(f"Fallecidos: {pac['FALLECIDO'].sum():,} ({pac['FALLECIDO'].mean()*100:.1f}%)")
print(f"Sexo:\n{pac['SEXO'].value_counts().to_string()}")

salida_pac = SILVER / "FISSAL_ESTOMAGO_PERFIL_PACIENTES.parquet"
pac.to_parquet(salida_pac, index=False)
print(f"\nGuardado: {salida_pac}")
print("\nFin.")
