import pandas as pd
import numpy as np
from pathlib import Path
import gc

BRONCE = Path(r"C:\Users\eah\apoyoconsultoria.com\File Server - Analytics\7 Datos\Datos abiertos\fissal\00_bronce")
SILVER = Path(r"C:\Users\eah\apoyoconsultoria.com\File Server - Analytics\7 Datos\Datos abiertos\fissal\01_silver")
ANIOS = range(2016, 2023)

NAN_STRINGS = {"nan", "NaN", "None", "none", "NaT", "nat", ""}


def limpiar_nombres_columnas(df):
    renombrar = {}
    for c in df.columns:
        if c.startswith("ATE_A") and c.endswith("OPROD"):
            renombrar[c] = "ATE_ANOPROD"
    return df.rename(columns=renombrar)


def limpiar_nan_strings(df):
    for col in df.select_dtypes(include=["object", "string"]).columns:
        mask = df[col].isin(NAN_STRINGS)
        if mask.any():
            df[col] = df[col].where(~mask, other=pd.NA)
    return df


def procesar_fechas(df):
    cols_fecha = ["ATE_FECNAC", "FEC_FALLECIMIENTO", "ATE_FECATENCION",
                  "ATE_FECINGHOSP", "ATE_FECALTHOSP"]
    for col in cols_fecha:
        if col not in df.columns:
            continue
        if df[col].dtype in ("float64", "int64"):
            df[col] = pd.NaT
        else:
            df[col] = pd.to_datetime(df[col], errors="coerce")
    return df


def procesar_ubigeo(df):
    ubigeo = df["COD_UBIGEO"]
    mask = ubigeo.notna()
    df["COD_UBIGEO"] = pd.array([pd.NA] * len(df), dtype="string")
    df.loc[mask, "COD_UBIGEO"] = ubigeo[mask].astype(int).astype(str).str.zfill(6)
    return df


def agregar_columnas_derivadas(df):
    mask_edad = df["ATE_FECATENCION"].notna() & df["ATE_FECNAC"].notna()
    df["EDAD"] = pd.NA
    if mask_edad.any():
        dias = (df.loc[mask_edad, "ATE_FECATENCION"] - df.loc[mask_edad, "ATE_FECNAC"]).dt.days
        df.loc[mask_edad, "EDAD"] = (dias / 365.25).astype(int)

    df["CAPITULO_CIE10"] = df["ATE_CODCIE10"].str[0]

    df["PERIODO_PRODUCCION"] = (
        df["ATE_ANOPROD"].astype(str) + "-" + df["ATE_MESPROD"].astype(str).str.zfill(2)
    )

    mask_fec = df["ATE_FECATENCION"].notna()
    df["ANIO_ATENCION"] = pd.NA
    df["MES_ATENCION"] = pd.NA
    df["PERIODO_ATENCION"] = pd.NA
    if mask_fec.any():
        df.loc[mask_fec, "ANIO_ATENCION"] = df.loc[mask_fec, "ATE_FECATENCION"].dt.year
        df.loc[mask_fec, "MES_ATENCION"] = df.loc[mask_fec, "ATE_FECATENCION"].dt.month
        df.loc[mask_fec, "PERIODO_ATENCION"] = (
            df.loc[mask_fec, "ANIO_ATENCION"].astype(str)
            + "-"
            + df.loc[mask_fec, "MES_ATENCION"].astype(str).str.zfill(2)
        )

    mask_hosp = df["ATE_FECINGHOSP"].notna() & df["ATE_FECALTHOSP"].notna()
    df["DIAS_HOSPITALIZACION"] = pd.NA
    if mask_hosp.any():
        df.loc[mask_hosp, "DIAS_HOSPITALIZACION"] = (
            df.loc[mask_hosp, "ATE_FECALTHOSP"] - df.loc[mask_hosp, "ATE_FECINGHOSP"]
        ).dt.days

    return df


def resumen_pacientes_anio(df):
    return (
        df.groupby("NUM_DOC_CRYPTO", sort=False)
        .agg(
            ANIO=("ATE_ANOPROD", "first"),
            SEXO=("SEXO", "first"),
            ATE_FECNAC=("ATE_FECNAC", "first"),
            N_ATENCIONES=("ATE_FUA", "nunique"),
            N_PRESTACIONES=("ATE_ANOPROD", "size"),
            N_DIAGNOSTICOS=("ATE_CODCIE10", "nunique"),
            DIAG_PRINCIPAL=("ATE_GRUPOCIE10", lambda x: x.value_counts().index[0] if x.notna().any() else pd.NA),
            MONTO_NETO=("ATE_MONTONETO", "sum"),
        )
        .reset_index()
    )


print("=" * 60)
print("PREPROCESAMIENTO FISSAL 2016-2022")
print("=" * 60)

lista_pacientes = []

for yr in ANIOS:
    print(f"\n--- {yr} ---")
    archivo = BRONCE / f"FISSAL_PRESTACIONES_{yr}.parquet"
    df = pd.read_parquet(archivo)
    print(f"  Leido: {df.shape[0]:>12,} filas x {df.shape[1]} cols")

    df = limpiar_nombres_columnas(df)
    df = limpiar_nan_strings(df)
    df = procesar_fechas(df)
    df = procesar_ubigeo(df)
    df = agregar_columnas_derivadas(df)

    salida = SILVER / f"FISSAL_PRESTACIONES_{yr}.parquet"
    df.to_parquet(salida, index=False)
    print(f"  Guardado: {salida.name}")

    pac = resumen_pacientes_anio(df)
    lista_pacientes.append(pac)
    n_pac = len(pac)
    print(f"  Pacientes unicos: {n_pac:>10,}")

    del df
    gc.collect()

print("\n" + "=" * 60)
print("ANALISIS LONGITUDINAL DE PACIENTES")
print("=" * 60)

df_pac = pd.concat(lista_pacientes, ignore_index=True)
del lista_pacientes
gc.collect()

longitudinal = (
    df_pac.groupby("NUM_DOC_CRYPTO", sort=False)
    .agg(
        N_ANIOS=("ANIO", "nunique"),
        ANIOS=("ANIO", lambda x: sorted(x.unique().tolist())),
        SEXOS_DISTINTOS=("SEXO", "nunique"),
        SEXO=("SEXO", "first"),
        FECNAC=("ATE_FECNAC", "first"),
        N_ATENCIONES_TOTAL=("N_ATENCIONES", "sum"),
        N_PRESTACIONES_TOTAL=("N_PRESTACIONES", "sum"),
        N_DIAGNOSTICOS_TOTAL=("N_DIAGNOSTICOS", "sum"),
        MONTO_NETO_TOTAL=("MONTO_NETO", "sum"),
    )
    .reset_index()
)

longitudinal["ANIOS"] = longitudinal["ANIOS"].astype(str)
longitudinal["SEXO_CONSISTENTE"] = longitudinal["SEXOS_DISTINTOS"] == 1

longitudinal.to_parquet(SILVER / "FISSAL_PACIENTES_LONGITUDINAL.parquet", index=False)

print(f"\nTotal pacientes unicos: {len(longitudinal):>12,}")
print(f"\nPacientes por cantidad de anios que aparecen:")
dist = longitudinal["N_ANIOS"].value_counts().sort_index()
for n_anios, count in dist.items():
    pct = count / len(longitudinal) * 100
    print(f"  {n_anios} anio(s): {count:>10,}  ({pct:5.1f}%)")

multi = longitudinal[longitudinal["N_ANIOS"] > 1]
print(f"\nPacientes multi-anio: {len(multi):>10,}")
print(f"Pacientes en 7 anios: {(longitudinal['N_ANIOS'] == 7).sum():>10,}")

inconsistentes = longitudinal[~longitudinal["SEXO_CONSISTENTE"]]
print(f"Pacientes con SEXO inconsistente: {len(inconsistentes):>6,}")

print(f"\nTop 10 pacientes por prestaciones totales:")
top = longitudinal.nlargest(10, "N_PRESTACIONES_TOTAL")[
    ["NUM_DOC_CRYPTO", "N_ANIOS", "N_ATENCIONES_TOTAL", "N_PRESTACIONES_TOTAL", "MONTO_NETO_TOTAL"]
]
print(top.to_string(index=False))

df_pac.to_parquet(SILVER / "FISSAL_RESUMEN_PACIENTES_POR_ANIO.parquet", index=False)

print(f"\nArchivos guardados en: {SILVER}")
print("  - FISSAL_PRESTACIONES_YYYY.parquet  (datos limpios por anio)")
print("  - FISSAL_PACIENTES_LONGITUDINAL.parquet  (resumen por paciente)")
print("  - FISSAL_RESUMEN_PACIENTES_POR_ANIO.parquet  (resumen paciente-anio)")
print("\nFin.")

import pandas as pd
df = pd.read_parquet(r"C:\Users\eah\apoyoconsultoria.com\File Server - Analytics\7 Datos\Datos abiertos\fissal\01_silver\FISSAL_CANCER_COLORRECTAL_2016_2022.parquet")



