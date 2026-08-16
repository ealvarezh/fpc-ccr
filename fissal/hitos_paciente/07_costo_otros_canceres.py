import pandas as pd
import numpy as np
from pathlib import Path
import gc

SILVER = Path(r"C:\Users\eah\apoyoconsultoria.com\File Server - Analytics\7 Datos\Datos abiertos\fissal\01_silver")

print("=" * 70)
print("COSTO DE OTROS CANCERES DURANTE EL PROCESO CCR")
print("=" * 70)

hitos = pd.read_parquet(SILVER / "FISSAL_CCR_HITOS_PACIENTE.parquet")
print(f"Pacientes FISSAL_REAL_B: {hitos['FISSAL_REAL_B'].sum():,}")

# Pacientes a analizar
pac_real_b = hitos.loc[hitos["FISSAL_REAL_B"], "NUM_DOC_CRYPTO"].tolist()
pac_set = set(pac_real_b)

# Fechas de referencia por paciente
fechas_dx = hitos.set_index("NUM_DOC_CRYPTO")["FECHA_DIAGNOSTICO"]
fechas_desenlace = hitos.set_index("NUM_DOC_CRYPTO")["FECHA_DESENLACE"]

# Codigos de otros canceres a buscar
CODIGOS_OTROS = {
    "C16_ESTOMAGO": r"^C16",
    "C50_MAMA": r"^C50",
    "C53_CERVIX": r"^C53",
    "C61_PROSTATA": r"^C61",
    "C83_LINFOMA": r"^C83",
    "OTROS_C": r"^C(?!18|19|20)",  # cualquier C que no sea CCR
}

# Inicializar acumuladores
costo_otros = {pid: 0.0 for pid in pac_real_b}
costo_por_codigo = {pid: {k: 0.0 for k in CODIGOS_OTROS} for pid in pac_real_b}
n_registros_otros = {pid: 0 for pid in pac_real_b}

ANIOS = range(2016, 2023)
for yr in ANIOS:
    archivo = SILVER / f"FISSAL_PRESTACIONES_{yr}.parquet"
    if not archivo.exists():
        continue
    print(f"  {yr}...", end=" ")
    df_yr = pd.read_parquet(archivo, columns=["NUM_DOC_CRYPTO", "ATE_CODCIE10", "ATE_FECATENCION", "ATE_MONTONETO"])
    df_yr = df_yr[df_yr["NUM_DOC_CRYPTO"].isin(pac_set)].copy()
    if len(df_yr) == 0:
        print("sin registros")
        del df_yr; gc.collect()
        continue

    # Agregar fechas de referencia
    df_yr["FECHA_DX"] = df_yr["NUM_DOC_CRYPTO"].map(fechas_dx)
    df_yr["FECHA_DESENLACE"] = df_yr["NUM_DOC_CRYPTO"].map(fechas_desenlace)

    # Solo registros DURANTE el proceso CCR (entre diagnostico y desenlace)
    mask_ventana = (
        (df_yr["ATE_FECATENCION"] >= df_yr["FECHA_DX"])
        & (df_yr["ATE_FECATENCION"] <= df_yr["FECHA_DESENLACE"])
        & df_yr["FECHA_DX"].notna()
        & df_yr["FECHA_DESENLACE"].notna()
    )
    df_ccr = df_yr[mask_ventana]

    for cod_nombre, patron in CODIGOS_OTROS.items():
        mask = df_ccr["ATE_CODCIE10"].str.contains(patron, na=False)
        if mask.any():
            sub = df_ccr[mask]
            for pid in sub["NUM_DOC_CRYPTO"].unique():
                monto = sub.loc[sub["NUM_DOC_CRYPTO"] == pid, "ATE_MONTONETO"].sum()
                n_reg = sub.loc[sub["NUM_DOC_CRYPTO"] == pid].shape[0]
                costo_por_codigo[pid][cod_nombre] += monto
                costo_otros[pid] += monto
                n_registros_otros[pid] += n_reg

    print(f"OK ({len(df_ccr):,} en ventana CCR)")
    del df_yr, df_ccr
    gc.collect()

# Agregar resultados al hitos
hitos["COSTO_OTROS_CANCERES"] = hitos["NUM_DOC_CRYPTO"].map(costo_otros).fillna(0)
hitos["N_REG_OTROS_CANCERES"] = hitos["NUM_DOC_CRYPTO"].map(n_registros_otros).fillna(0).astype(int)
hitos["COSTO_TOTAL_INCL_OTROS"] = hitos["MONTO_NETO_TOTAL"] + hitos["COSTO_OTROS_CANCERES"]

# Reporting
print("\n" + "=" * 70)
print("RESULTADOS (solo FISSAL_REAL_B)")
print("=" * 70)

real_b = hitos[hitos["FISSAL_REAL_B"]]
n_con_otros = (real_b["COSTO_OTROS_CANCERES"] > 0).sum()
print(f"\n  Pacientes con otros canceres durante proceso CCR: {n_con_otros:,} ({n_con_otros/len(real_b)*100:.1f}%)")
print(f"  Registros de otros canceres en ventana CCR: {real_b['N_REG_OTROS_CANCERES'].sum():,}")

print(f"\n  --- Comparacion de costos ---")
print(f"  Costo neto CCR original (mediana):     S/ {real_b['MONTO_NETO_TOTAL'].median():>10,.0f}")
print(f"  Costo neto CCR original (media):       S/ {real_b['MONTO_NETO_TOTAL'].mean():>10,.0f}")
print(f"  Costo otros canceres (mediana):        S/ {real_b['COSTO_OTROS_CANCERES'].median():>10,.0f}")
print(f"  Costo otros canceres (media):          S/ {real_b['COSTO_OTROS_CANCERES'].mean():>10,.0f}")
print(f"  COSTO TOTAL INCL. OTROS (mediana):     S/ {real_b['COSTO_TOTAL_INCL_OTROS'].median():>10,.0f}")
print(f"  COSTO TOTAL INCL. OTROS (media):       S/ {real_b['COSTO_TOTAL_INCL_OTROS'].mean():>10,.0f}")

# Cuanto aporta cada codigo
print(f"\n  --- Aporte por codigo (ventana CCR, solo FISSAL_REAL_B) ---")
for cod_nombre in CODIGOS_OTROS:
    total = sum(costo_por_codigo[pid][cod_nombre] for pid in pac_real_b)
    n_pac = sum(1 for pid in pac_real_b if costo_por_codigo[pid][cod_nombre] > 0)
    print(f"  {cod_nombre:<20s}: S/ {total:>12,.0f}  |  {n_pac:>5,} pacientes")

# Guardar
salida = SILVER / "FISSAL_CCR_HITOS_PACIENTE.parquet"
hitos.to_parquet(salida, index=False)
print(f"\n  Nuevas columnas: COSTO_OTROS_CANCERES, N_REG_OTROS_CANCERES, COSTO_TOTAL_INCL_OTROS")
print(f"  Guardado: {salida}")
print("\nFin.")
