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


# =====================================================================
# CORRECCION DE OUTLIERS DE CANTIDAD (ATE_CANTBRUTA)
# =====================================================================
# Hallazgo (ver fissal/hitos_paciente/README.md): algunos registros de
# HOSPITAL NACIONAL DANIEL ALCIDES CARRION tienen una cantidad facturada
# absurda para el item (p.ej. 1,112,500 unidades de una "recarga para
# grapadora quirurgica" cuando ese mismo item normalmente se factura de a 1,
# o 1,531 "mascarillas oronasales" cuando lo normal es 1). El precio
# unitario (ATE_PRECIO) en esos registros es realista -- el error esta en
# la CANTIDAD, probablemente un digito de mas al capturar el dato. Se
# corrige comparando cada registro contra la mediana historica de cantidad
# de ESE MISMO item (ATE_CODCONSUMO) en TODOS los anios (algunos items
# aparecen pocas veces en un solo anio, por eso la referencia es global).

FACTOR_OUTLIER_CANTIDAD = 1000  # cantidad > 1000x la mediana del item = sospechoso
MIN_MUESTRAS_REFERENCIA = 5     # minimo de registros historicos del item para confiar en su mediana

# Excepcion para OXIGENO MEDICINAL: se investigo si la regla de cantidad
# estaba confundiendo el alza real de precio/consumo de oxigeno en la
# pandemia (2020-2021) con un error de captura. Los datos NO respaldan esa
# hipotesis (los outliers de oxigeno se concentran en 2018 y 2022, no en
# 2020-2021, y su precio unitario es cercano a cero en todos los anios).
# Pero SI se encontro que 62 de 254 registros de oxigeno marcados como
# outlier ya tenian, ANTES de corregir, un ATE_MONTONETO dentro del rango
# real de mercado de un balon de oxigeno medicinal en Peru (S/450-2,000
# segun capacidad y kit de accesorios). Para esos, la mediana historica de
# cantidad del item no es confiable (a veces se codifica el balon completo,
# a veces una unidad mas fina) y reescalar el monto lo distorsiona en vez
# de corregirlo. Por eso no se toca ningun registro de oxigeno cuyo monto
# original ya caiga en este rango plausible.
OXIGENO_MONTO_PLAUSIBLE_MIN = 300   # margen bajo el precio de balon simple (S/450)
OXIGENO_MONTO_PLAUSIBLE_MAX = 3000  # margen sobre el precio de balon + kit (S/2,000)

# Correccion manual: GRAPADORA QUIRURGICA LINEAL CORTANTE ENDOSCOPICA 12mm
# (ATE_CODCONSUMO 23851) aparece una unica vez en los 7 anios de datos, con
# ATE_CANTBRUTA=11,250 (precio unitario implicito S/1,150, monto S/12.9M en un
# solo registro). corregir_outliers_cantidad no puede detectarlo porque exige
# MIN_MUESTRAS_REFERENCIA items historicos para calcular una mediana de
# referencia, y este item no tiene ningun otro registro con el que comparar.
# Cantidad real verificada manualmente: 1 (no existe insumo quirurgico que se
# facture en lotes de miles de unidades por atencion).
CODIGO_GRAPADORA_OUTLIER = "23851"


def calcular_referencia_cantidad(anios, carpeta_bronce):
    """Pasada liviana (solo 2 columnas) sobre todos los anios crudos para
    obtener la mediana de ATE_CANTBRUTA por item (ATE_CODCONSUMO), usada
    como referencia para detectar outliers de cantidad."""
    partes = []
    for yr in anios:
        archivo = carpeta_bronce / f"FISSAL_PRESTACIONES_{yr}.parquet"
        if not archivo.exists():
            continue
        partes.append(pd.read_parquet(archivo, columns=["ATE_CODCONSUMO", "ATE_CANTBRUTA"]))
    todo = pd.concat(partes, ignore_index=True)
    ref = todo.groupby("ATE_CODCONSUMO")["ATE_CANTBRUTA"].agg(MEDIANA_CANT_REF="median", N_ITEM_REF="count")
    return ref


def corregir_outliers_cantidad(df, ref):
    """Si ATE_CANTBRUTA de un registro supera FACTOR_OUTLIER_CANTIDAD veces
    la mediana historica de su item, se reescala TODA la fila (cantidad
    bruta/neta y monto bruto/neto) por el mismo factor, preservando el
    precio unitario y la relacion bruto/neto original. Items sin suficiente
    historial (< MIN_MUESTRAS_REFERENCIA) no se tocan."""
    faltantes = {"ATE_CODCONSUMO", "ATE_CANTBRUTA", "ATE_CANTNETA", "ATE_MONTOBRUTO", "ATE_MONTONETO"} - set(df.columns)
    if faltantes:
        return df

    df = df.merge(ref, left_on="ATE_CODCONSUMO", right_index=True, how="left")
    mask = (
        (df["N_ITEM_REF"] >= MIN_MUESTRAS_REFERENCIA)
        & (df["MEDIANA_CANT_REF"] > 0)
        & (df["ATE_CANTBRUTA"] > df["MEDIANA_CANT_REF"] * FACTOR_OUTLIER_CANTIDAD)
    )

    oxigeno_monto_plausible = (
        df["ATE_DESCCONSUMO"].str.contains("OXIGENO", case=False, na=False)
        & (df["ATE_MONTONETO"] >= OXIGENO_MONTO_PLAUSIBLE_MIN)
        & (df["ATE_MONTONETO"] <= OXIGENO_MONTO_PLAUSIBLE_MAX)
    )
    mask = mask & ~oxigeno_monto_plausible

    n_outliers = int(mask.sum())
    if n_outliers > 0:
        monto_antes = df.loc[mask, "ATE_MONTONETO"].sum()
        print(f"  [Calidad de datos] {n_outliers} registro(s) con ATE_CANTBRUTA > "
              f"{FACTOR_OUTLIER_CANTIDAD}x la mediana historica de su item:")
        for _, row in df.loc[mask, ["ATE_DESCCONSUMO", "ATE_CANTBRUTA", "MEDIANA_CANT_REF", "ATE_MONTONETO"]].iterrows():
            desc = str(row["ATE_DESCCONSUMO"])[:55]
            print(f"      {desc:<55s} | cant {row['ATE_CANTBRUTA']:>10,.0f} -> "
                  f"{row['MEDIANA_CANT_REF']:>6,.0f} (mediana del item) | "
                  f"monto S/{row['ATE_MONTONETO']:>14,.2f} se reescala")

        factor = df.loc[mask, "MEDIANA_CANT_REF"] / df.loc[mask, "ATE_CANTBRUTA"]
        for col in ["ATE_CANTBRUTA", "ATE_CANTNETA", "ATE_MONTOBRUTO", "ATE_MONTONETO"]:
            if df[col].dtype.kind in "iu":  # entero -> pasar a float antes de reescalar
                df[col] = df[col].astype(float)
            df.loc[mask, col] = df.loc[mask, col] * factor

        monto_despues = df.loc[mask, "ATE_MONTONETO"].sum()
        print(f"      Monto neto de estos registros: S/{monto_antes:,.2f} -> S/{monto_despues:,.2f} "
              f"(se descuenta S/{monto_antes - monto_despues:,.2f} del total facturado)")

    return df.drop(columns=["MEDIANA_CANT_REF", "N_ITEM_REF"])


def corregir_outlier_manual_grapadora(df):
    """Ver nota de CODIGO_GRAPADORA_OUTLIER: item con un unico registro en toda
    la historia FISSAL, por lo que corregir_outliers_cantidad no tiene con que
    calcular una mediana de referencia y lo deja pasar sin corregir."""
    if "ATE_CODCONSUMO" not in df.columns:
        return df

    mask = (df["ATE_CODCONSUMO"].astype(str) == CODIGO_GRAPADORA_OUTLIER) & (df["ATE_CANTBRUTA"] > 1)
    n_outliers = int(mask.sum())
    if n_outliers > 0:
        monto_antes = df.loc[mask, "ATE_MONTONETO"].sum()
        factor = 1 / df.loc[mask, "ATE_CANTBRUTA"]
        for col in ["ATE_CANTBRUTA", "ATE_CANTNETA", "ATE_MONTOBRUTO", "ATE_MONTONETO"]:
            if df[col].dtype.kind in "iu":
                df[col] = df[col].astype(float)
            df.loc[mask, col] = df.loc[mask, col] * factor
        monto_despues = df.loc[mask, "ATE_MONTONETO"].sum()
        print(f"  [Calidad de datos] Correccion manual (item sin historial suficiente): "
              f"{n_outliers} registro(s) de grapadora quirurgica (codigo {CODIGO_GRAPADORA_OUTLIER}), "
              f"cantidad reescalada a 1. Monto neto: S/{monto_antes:,.2f} -> S/{monto_despues:,.2f}")
    return df


def agregar_columnas_derivadas(df):
    mask_edad = df["ATE_FECATENCION"].notna() & df["ATE_FECNAC"].notna()
    df["EDAD"] = pd.NA
    if mask_edad.any():
        dias = (df.loc[mask_edad, "ATE_FECATENCION"] - df.loc[mask_edad, "ATE_FECNAC"]).dt.days
        edad_calc = (dias / 365.25).astype(int)
        # Filtrar outliers: edad negativa (fecha nacimiento > fecha atencion)
        # o edad > 120 (fecha nacimiento claramente erronea). Este archivo cubre
        # TODAS las enfermedades de FISSAL (no solo CCR), incluyendo patologias
        # pediatricas reales, asi que aqui NO se acota la edad minima mas alla de
        # 0 -- ese filtro clinico especifico de cancer colorrectal (edad < 10
        # implausible para CCR) se aplica solo en 03_perfil_pacientes_ccr.py,
        # sobre la poblacion ya filtrada a CCR.
        edad_calc = edad_calc.where((edad_calc >= 0) & (edad_calc <= 100), other=pd.NA)
        df.loc[mask_edad, "EDAD"] = edad_calc

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

print("\nCalculando referencia de cantidad por item (pasada liviana, todos los anios)...")
REF_CANTIDAD = calcular_referencia_cantidad(ANIOS, BRONCE)
print(f"  Items distintos (ATE_CODCONSUMO): {len(REF_CANTIDAD):,}")

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
    df = corregir_outliers_cantidad(df, REF_CANTIDAD)
    df = corregir_outlier_manual_grapadora(df)
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



