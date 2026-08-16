import pandas as pd
import numpy as np
from pathlib import Path
import gc

SILVER = Path(r"C:\Users\eah\apoyoconsultoria.com\File Server - Analytics\7 Datos\Datos abiertos\fissal\01_silver")

print("=" * 70)
print("COSTO TOTAL DEL PACIENTE EN VENTANA CCR (todos los CIE-10)")
print("=" * 70)

hitos = pd.read_parquet(SILVER / "FISSAL_CCR_HITOS_PACIENTE.parquet")
pac_set = set(hitos.loc[hitos["FISSAL_REAL_B"], "NUM_DOC_CRYPTO"])
fechas_dx = hitos.set_index("NUM_DOC_CRYPTO")["FECHA_DIAGNOSTICO"]
fechas_des = hitos.set_index("NUM_DOC_CRYPTO")["FECHA_DESENLACE"]
n_total = len(pac_set)

# Acumuladores
costo_total_ventana = {pid: 0.0 for pid in pac_set}
costo_ccr_ventana = {pid: 0.0 for pid in pac_set}      # solo C18/19/20 dentro de ventana
costo_no_ccr_ventana = {pid: 0.0 for pid in pac_set}    # todo lo demas dentro de ventana

ANIOS = range(2016, 2023)
for yr in ANIOS:
    archivo = SILVER / f"FISSAL_PRESTACIONES_{yr}.parquet"
    if not archivo.exists():
        continue
    print(f"  {yr}...", end=" ")
    df = pd.read_parquet(archivo, columns=["NUM_DOC_CRYPTO", "ATE_CODCIE10", "ATE_FECATENCION", "ATE_MONTONETO"])
    df = df[df["NUM_DOC_CRYPTO"].isin(pac_set)].copy()
    df["DX"] = df["NUM_DOC_CRYPTO"].map(fechas_dx)
    df["DES"] = df["NUM_DOC_CRYPTO"].map(fechas_des)

    # SOLO dentro de la ventana CCR (diagnostico -> desenlace)
    mask = (df["ATE_FECATENCION"] >= df["DX"]) & (df["ATE_FECATENCION"] <= df["DES"]) & df["DX"].notna() & df["DES"].notna()
    df = df[mask]

    if len(df) == 0:
        print("sin datos")
        del df; gc.collect()
        continue

    df["ES_CCR"] = df["ATE_CODCIE10"].str.contains(r"^C(18|19|20)", na=False)

    for pid, grp in df.groupby("NUM_DOC_CRYPTO"):
        monto = grp["ATE_MONTONETO"].sum()
        monto_ccr = grp.loc[grp["ES_CCR"], "ATE_MONTONETO"].sum()
        costo_total_ventana[pid] += monto
        costo_ccr_ventana[pid] += monto_ccr
        costo_no_ccr_ventana[pid] += monto - monto_ccr

    print(f"OK")
    del df; gc.collect()

# Agregar al hitos
hitos["COSTO_TOTAL_VENTANA"] = hitos["NUM_DOC_CRYPTO"].map(costo_total_ventana).fillna(0)
hitos["COSTO_CCR_VENTANA"] = hitos["NUM_DOC_CRYPTO"].map(costo_ccr_ventana).fillna(0)
hitos["COSTO_NO_CCR_VENTANA"] = hitos["NUM_DOC_CRYPTO"].map(costo_no_ccr_ventana).fillna(0)

real_b = hitos[hitos["FISSAL_REAL_B"]]

print("\n" + "=" * 70)
print("COMPARACION DE COSTOS (FISSAL_REAL_B, n=3,968)")
print("=" * 70)

print(f"\n{'Concepto':<45s} {'Mediana':>12s} {'Media':>13s}")
print("-" * 72)
print(f"{'MONTO_NETO_TOTAL (original, solo C18/19/20)':<45s} S/{real_b['MONTO_NETO_TOTAL'].median():>10,.0f} S/{real_b['MONTO_NETO_TOTAL'].mean():>11,.0f}")
print(f"{'COSTO_CCR_VENTANA (C18/19/20 en ventana)':<45s} S/{real_b['COSTO_CCR_VENTANA'].median():>10,.0f} S/{real_b['COSTO_CCR_VENTANA'].mean():>11,.0f}")
print(f"{'COSTO_NO_CCR_VENTANA (todo lo demas)':<45s} S/{real_b['COSTO_NO_CCR_VENTANA'].median():>10,.0f} S/{real_b['COSTO_NO_CCR_VENTANA'].mean():>11,.0f}")
print(f"{'COSTO_TOTAL_VENTANA (TODO en ventana CCR)':<45s} S/{real_b['COSTO_TOTAL_VENTANA'].median():>10,.0f} S/{real_b['COSTO_TOTAL_VENTANA'].mean():>11,.0f}")

# Cuantos pacientes tienen algun consumo no-CCR
n_con_no_ccr = (real_b["COSTO_NO_CCR_VENTANA"] > 0).sum()
print(f"\n  Pacientes con ALGUN consumo no-CCR en ventana: {n_con_no_ccr:,} ({n_con_no_ccr/len(real_b)*100:.1f}%)")

# Cuanto % del costo total es no-CCR
total_ccr = real_b["COSTO_CCR_VENTANA"].sum()
total_no_ccr = real_b["COSTO_NO_CCR_VENTANA"].sum()
total_all = total_ccr + total_no_ccr
print(f"\n  Distribucion del costo total en ventana CCR:")
print(f"    C18/19/20 (CCR):            S/ {total_ccr:>12,.0f} ({total_ccr/total_all*100:.1f}%)")
print(f"    Todo lo demas (no CCR):     S/ {total_no_ccr:>12,.0f} ({total_no_ccr/total_all*100:.1f}%)")
print(f"    TOTAL:                      S/ {total_all:>12,.0f}")

# Guardar
salida = SILVER / "FISSAL_CCR_HITOS_PACIENTE.parquet"
hitos.to_parquet(salida, index=False)
print(f"\n  Guardado: {salida}")
print(f"  Columnas nuevas: COSTO_TOTAL_VENTANA, COSTO_CCR_VENTANA, COSTO_NO_CCR_VENTANA")
print("\nFin.")
