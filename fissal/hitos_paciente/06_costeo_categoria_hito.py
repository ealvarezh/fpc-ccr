import sys
import pandas as pd
import numpy as np
import gc
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SILVER = Path(r"C:\Users\eah\apoyoconsultoria.com\File Server - Analytics\7 Datos\Datos abiertos\fissal\01_silver")
ARCHIVO_CCR = SILVER / "FISSAL_CANCER_COLORRECTAL_2016_2022.parquet"
ARCHIVO_HITOS = SILVER / "FISSAL_CCR_HITOS_PACIENTE.parquet"
DICCIONARIO_502 = Path(
    r"C:\Users\eah\apoyoconsultoria.com\File Server - Analytics\3 Proyectos\2025"
    r"\2025-116-L FPC Dashboard 25\4 Analisis\3 Programas\adicional 2026"
    r"\diccionario_ATE_DESCCONSUMO_502_estandarizado.xlsx"
)
ANIOS = range(2016, 2023)

print("=" * 70)
print("COSTEO POR HITO Y SUBCATEGORIA — CANCER COLORRECTAL")
print("=" * 70)
print("""
Ventanas de costo por hito:
  1. DESPISTAJE   : toda actividad ANTES del diagnostico (misma ventana que
                     COSTO_NETO_PRE_DIAGNOSTICO ya existente)
  2. DIAGNOSTICO  : mismo dia del diagnostico (evento puntual)
  3. TRATAMIENTO  : (diagnostico, fin de tratamiento] — solo pacientes con
                     tratamiento detectado. NOTA: esta ventana es mas ancha que
                     COSTO_NETO_TRATAMIENTO_TOTAL (que arranca en el INICIO del
                     tratamiento, no en el diagnostico), a proposito: cierra el
                     hueco de tiempo/gasto entre diagnostico e inicio de
                     tratamiento que hoy no queda asignado a ningun hito.
  4. DESENLACE    : (fin de tratamiento, desenlace] si tuvo tratamiento, o
                     (diagnostico, desenlace] si no tuvo tratamiento detectado.
""")

hp = pd.read_parquet(ARCHIVO_HITOS, columns=[
    "NUM_DOC_CRYPTO", "FECHA_DIAGNOSTICO", "FECHA_PRIMER_CONTACTO_SISTEMA",
    "FECHA_INICIO_TRATAMIENTO", "FECHA_FIN_TRATAMIENTO", "FECHA_DESENLACE",
    "SECUENCIA_TRATAMIENTO",
])
pac_ccr = set(hp["NUM_DOC_CRYPTO"])
fechas = hp.set_index("NUM_DOC_CRYPTO")
print(f"Pacientes CCR: {len(hp):,}")

# =====================================================================
# DICCIONARIO DE CATEGORIAS (categoria_recurso_502 / subcategoria_recurso_502)
# =====================================================================
print("\nCargando diccionario de categorias (Diccionario_502)...")
dic = pd.read_excel(DICCIONARIO_502, sheet_name="Diccionario_502",
                     usecols=["ATE_DESCCONSUMO", "categoria_recurso_502", "subcategoria_recurso_502"])
dic["ATE_DESCCONSUMO"] = dic["ATE_DESCCONSUMO"].str.strip()
dic = dic.drop_duplicates(subset="ATE_DESCCONSUMO")
print(f"  Items en diccionario: {len(dic):,}")


def clasificar(df_in):
    df_in = df_in.copy()
    df_in["_DESC_STRIP"] = df_in["ATE_DESCCONSUMO"].str.strip()
    df_in = df_in.merge(dic, left_on="_DESC_STRIP", right_on="ATE_DESCCONSUMO",
                         how="left", suffixes=("", "_DIC"))
    df_in = df_in.drop(columns=["_DESC_STRIP", "ATE_DESCCONSUMO_DIC"])
    df_in["categoria_recurso_502"] = df_in["categoria_recurso_502"].fillna("SIN_CLASIFICAR")
    df_in["subcategoria_recurso_502"] = df_in["subcategoria_recurso_502"].fillna("SIN_CLASIFICAR")
    return df_in


COLS_SALIDA = ["NUM_DOC_CRYPTO", "HITO", "categoria_recurso_502", "subcategoria_recurso_502",
               "ATE_MONTONETO", "ATE_FECATENCION"]
registros_hito = []

# =====================================================================
# HITO 1: DESPISTAJE / PRE-DIAGNOSTICO (recorre data completa, 7 anios)
# =====================================================================
print("\nHITO 1: recorriendo 7 anios de data completa (pre-diagnostico)...")
COLS_YR = ["NUM_DOC_CRYPTO", "ATE_FECATENCION", "ATE_DESCCONSUMO", "ATE_MONTONETO"]
for yr in ANIOS:
    archivo = SILVER / f"FISSAL_PRESTACIONES_{yr}.parquet"
    if not archivo.exists():
        continue
    print(f"  {yr}...", end=" ")
    df_yr = pd.read_parquet(archivo, columns=COLS_YR)
    df_yr = df_yr[df_yr["NUM_DOC_CRYPTO"].isin(pac_ccr)].copy()
    df_yr["FECHA_DX"] = df_yr["NUM_DOC_CRYPTO"].map(fechas["FECHA_DIAGNOSTICO"])
    df_pre = df_yr[df_yr["ATE_FECATENCION"] < df_yr["FECHA_DX"]].copy()
    print(f"{len(df_pre):,} registros pre-diagnostico")
    if len(df_pre) > 0:
        df_pre = clasificar(df_pre)
        df_pre["HITO"] = "1_DESPISTAJE"
        registros_hito.append(df_pre[COLS_SALIDA])
    del df_yr, df_pre
    gc.collect()

# =====================================================================
# HITOS 2, 3, 4: desde el parquet ya filtrado a CCR (mas liviano)
# =====================================================================
print("\nCargando data CCR (ya filtrada) para Hitos 2, 3 y 4...")
ccr = pd.read_parquet(ARCHIVO_CCR, columns=["NUM_DOC_CRYPTO", "ATE_FECATENCION", "ATE_DESCCONSUMO", "ATE_MONTONETO"])
ccr = ccr.merge(
    fechas[["FECHA_DIAGNOSTICO", "FECHA_INICIO_TRATAMIENTO", "FECHA_FIN_TRATAMIENTO",
            "FECHA_DESENLACE", "SECUENCIA_TRATAMIENTO"]],
    left_on="NUM_DOC_CRYPTO", right_index=True, how="left",
)
print(f"  Registros CCR: {len(ccr):,}")
ccr = clasificar(ccr)

tuvo_trat = ccr["SECUENCIA_TRATAMIENTO"] != "SIN_TRATAMIENTO_DETECTADO"

print("  Hito 2 (dia del diagnostico)...")
m2 = ccr["ATE_FECATENCION"] == ccr["FECHA_DIAGNOSTICO"]
h2 = ccr.loc[m2].copy()
h2["HITO"] = "2_DIAGNOSTICO"
registros_hito.append(h2[COLS_SALIDA])
print(f"    {len(h2):,} registros")

print("  Hito 3 (diagnostico -> fin de tratamiento, solo con tratamiento detectado)...")
m3 = tuvo_trat & (ccr["ATE_FECATENCION"] > ccr["FECHA_DIAGNOSTICO"]) & \
    (ccr["ATE_FECATENCION"] <= ccr["FECHA_FIN_TRATAMIENTO"])
h3 = ccr.loc[m3].copy()
h3["HITO"] = "3_TRATAMIENTO"
registros_hito.append(h3[COLS_SALIDA])
print(f"    {len(h3):,} registros")

print("  Hito 4 (fin de tratamiento -> desenlace, o diagnostico -> desenlace si no hubo tratamiento)...")
inicio_4 = pd.to_datetime(np.where(tuvo_trat, ccr["FECHA_FIN_TRATAMIENTO"], ccr["FECHA_DIAGNOSTICO"]))
ccr["_INICIO_HITO4"] = inicio_4
m4 = (ccr["ATE_FECATENCION"] > ccr["_INICIO_HITO4"]) & (ccr["ATE_FECATENCION"] <= ccr["FECHA_DESENLACE"])
h4 = ccr.loc[m4].copy()
h4["HITO"] = "4_DESENLACE"
registros_hito.append(h4[COLS_SALIDA])
print(f"    {len(h4):,} registros")

del ccr, h2, h3, h4
gc.collect()

# =====================================================================
# CONSOLIDACION Y AGREGADOS
# =====================================================================
print("\nConsolidando detalle de todos los hitos...")
detalle = pd.concat(registros_hito, ignore_index=True)
del registros_hito
gc.collect()
print(f"  Total lineas clasificadas: {len(detalle):,}")

# Dia calendario de cada linea (varias lineas el mismo dia cuentan 1 sola vez en
# N_DIAS_DISTINTOS), para tener un proxy de "tiempo" por subcategoria -- no hay
# fecha de inicio/fin propia de una subcategoria, solo de todo el hito.
detalle["ATE_FECHA"] = detalle["ATE_FECATENCION"].dt.normalize()

print("\nAgregando por (paciente, hito, subcategoria)...")
costeo_subcat = detalle.groupby(
    ["NUM_DOC_CRYPTO", "HITO", "categoria_recurso_502", "subcategoria_recurso_502"], as_index=False
).agg(
    COSTO_NETO=("ATE_MONTONETO", "sum"),
    N_LINEAS=("ATE_MONTONETO", "size"),
    N_DIAS_DISTINTOS=("ATE_FECHA", "nunique"),
)

print("Agregando por (paciente, hito)...")
costeo_hito_costo = detalle.groupby(["NUM_DOC_CRYPTO", "HITO"], as_index=False).agg(
    COSTO_NETO=("ATE_MONTONETO", "sum"), N_LINEAS=("ATE_MONTONETO", "size"))

# Mismo costo por (paciente, hito), pero partido por el ANIO CALENDARIO real de
# cada linea (ATE_FECATENCION), en vez de atribuir todo el gasto del hito al
# anio de diagnostico de la cohorte. Un hito puede extenderse por mas de un
# anio calendario (p.ej. Tratamiento o Desenlace), asi que aqui un mismo
# paciente puede aportar costo a varios anios dentro del mismo hito.
print("Agregando por (paciente, hito, anio calendario)...")
detalle["ANIO_CALENDARIO"] = detalle["ATE_FECATENCION"].dt.year
costeo_hito_anio_cal = detalle.groupby(
    ["NUM_DOC_CRYPTO", "HITO", "ANIO_CALENDARIO"], as_index=False
).agg(COSTO_NETO=("ATE_MONTONETO", "sum"), N_LINEAS=("ATE_MONTONETO", "size"))

del detalle
gc.collect()

# --- Ventanas de fecha/duracion por hito (paciente x hito), para Analisis 1 ---
ventanas = []

v1 = hp[["NUM_DOC_CRYPTO", "FECHA_PRIMER_CONTACTO_SISTEMA", "FECHA_DIAGNOSTICO"]].copy()
v1["HITO"] = "1_DESPISTAJE"
v1 = v1.rename(columns={"FECHA_PRIMER_CONTACTO_SISTEMA": "FECHA_INICIO", "FECHA_DIAGNOSTICO": "FECHA_FIN"})
v1["DURACION_DIAS"] = (v1["FECHA_FIN"] - v1["FECHA_INICIO"]).dt.days
ventanas.append(v1[["NUM_DOC_CRYPTO", "HITO", "FECHA_INICIO", "FECHA_FIN", "DURACION_DIAS"]])

v2 = hp[["NUM_DOC_CRYPTO", "FECHA_DIAGNOSTICO"]].copy()
v2["HITO"] = "2_DIAGNOSTICO"
v2["FECHA_INICIO"] = v2["FECHA_DIAGNOSTICO"]
v2["FECHA_FIN"] = v2["FECHA_DIAGNOSTICO"]
v2["DURACION_DIAS"] = 0
ventanas.append(v2[["NUM_DOC_CRYPTO", "HITO", "FECHA_INICIO", "FECHA_FIN", "DURACION_DIAS"]])

v3 = hp.loc[hp["SECUENCIA_TRATAMIENTO"] != "SIN_TRATAMIENTO_DETECTADO",
            ["NUM_DOC_CRYPTO", "FECHA_DIAGNOSTICO", "FECHA_FIN_TRATAMIENTO"]].copy()
v3["HITO"] = "3_TRATAMIENTO"
v3 = v3.rename(columns={"FECHA_DIAGNOSTICO": "FECHA_INICIO", "FECHA_FIN_TRATAMIENTO": "FECHA_FIN"})
v3["DURACION_DIAS"] = (v3["FECHA_FIN"] - v3["FECHA_INICIO"]).dt.days
ventanas.append(v3[["NUM_DOC_CRYPTO", "HITO", "FECHA_INICIO", "FECHA_FIN", "DURACION_DIAS"]])

v4 = hp[["NUM_DOC_CRYPTO", "FECHA_DIAGNOSTICO", "FECHA_FIN_TRATAMIENTO", "FECHA_DESENLACE",
         "SECUENCIA_TRATAMIENTO"]].copy()
v4["FECHA_INICIO"] = np.where(
    v4["SECUENCIA_TRATAMIENTO"] != "SIN_TRATAMIENTO_DETECTADO",
    v4["FECHA_FIN_TRATAMIENTO"], v4["FECHA_DIAGNOSTICO"],
)
v4["FECHA_INICIO"] = pd.to_datetime(v4["FECHA_INICIO"])
v4["HITO"] = "4_DESENLACE"
v4["FECHA_FIN"] = v4["FECHA_DESENLACE"]
v4["DURACION_DIAS"] = (v4["FECHA_FIN"] - v4["FECHA_INICIO"]).dt.days
ventanas.append(v4[["NUM_DOC_CRYPTO", "HITO", "FECHA_INICIO", "FECHA_FIN", "DURACION_DIAS"]])

ventanas_df = pd.concat(ventanas, ignore_index=True)

costeo_hito = ventanas_df.merge(costeo_hito_costo, on=["NUM_DOC_CRYPTO", "HITO"], how="left")
costeo_hito["COSTO_NETO"] = costeo_hito["COSTO_NETO"].fillna(0)
costeo_hito["N_LINEAS"] = costeo_hito["N_LINEAS"].fillna(0)

# =====================================================================
# GUARDADO
# =====================================================================
out_hito = SILVER / "FISSAL_CCR_COSTEO_HITO.parquet"
out_subcat = SILVER / "FISSAL_CCR_COSTEO_HITO_SUBCATEGORIA.parquet"
out_hito_anio_cal = SILVER / "FISSAL_CCR_COSTEO_HITO_ANIO_CALENDARIO.parquet"
costeo_hito.to_parquet(out_hito, index=False)
costeo_subcat.to_parquet(out_subcat, index=False)
costeo_hito_anio_cal.to_parquet(out_hito_anio_cal, index=False)
print(f"\nGuardado: {out_hito}  ({len(costeo_hito):,} filas)")
print(f"Guardado: {out_subcat}  ({len(costeo_subcat):,} filas)")
print(f"Guardado: {out_hito_anio_cal}  ({len(costeo_hito_anio_cal):,} filas)")

print("\n--- Chequeo rapido: costo total por hito (todos los pacientes) ---")
for hito, sub in costeo_hito.groupby("HITO"):
    print(f"  {hito:>15s}: n_pac={len(sub):>7,}  costo_total=S/{sub['COSTO_NETO'].sum():>14,.2f}  "
          f"costo_medio=S/{sub['COSTO_NETO'].mean():>10,.2f}  costo_mediana=S/{sub['COSTO_NETO'].median():>10,.2f}")

print("\nFin.")
