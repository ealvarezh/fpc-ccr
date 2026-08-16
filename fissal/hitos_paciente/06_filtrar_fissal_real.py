import pandas as pd
import numpy as np
from pathlib import Path

SILVER = Path(r"C:\Users\eah\apoyoconsultoria.com\File Server - Analytics\7 Datos\Datos abiertos\fissal\01_silver")

print("=" * 70)
print("FILTRO DE PACIENTES 'FISSAL-REALES' Y DETECCION DE OUTLIERS")
print("=" * 70)

hitos = pd.read_parquet(SILVER / "FISSAL_CCR_HITOS_PACIENTE.parquet")
perfil = pd.read_parquet(SILVER / "FISSAL_CCR_PERFIL_PACIENTES.parquet",
                         columns=["NUM_DOC_CRYPTO", "N_PRESTACIONES"])

df = hitos.merge(perfil, on="NUM_DOC_CRYPTO", how="left")
N_TOTAL = len(df)

# =================================================================
# 1. DISTRIBUCION COSTO vs TIEMPO
# =================================================================
print("\n1. COSTO vs TIEMPO EN SISTEMA (todos los pacientes)")
print("-" * 85)
bins_t = [0, 1, 30, 90, 180, 365, 730, 99999]
labels_t = ["0-1d", "1-30d", "30-90d", "90-180d", "180d-1a", "1-2a", "2a+"]
df["RANGO_TIEMPO"] = pd.cut(df["TIEMPO_EN_SISTEMA_DIAS"].fillna(0), bins=bins_t, labels=labels_t, right=True)

print(f"{'Rango':>12s} {'n':>7s} {'At med':>7s} {'Costo med':>11s} {'Costo mean':>12s} {'P95':>11s} {'Max':>13s}")
print("-" * 80)
for r in labels_t:
    sub = df[df["RANGO_TIEMPO"] == r]
    if len(sub) == 0:
        continue
    print(f"{r:>12s} {len(sub):>7,} {sub['N_ATENCIONES'].median():>7.0f} "
          f"S/{sub['MONTO_NETO_TOTAL'].median():>9,.0f} S/{sub['MONTO_NETO_TOTAL'].mean():>10,.0f} "
          f"S/{sub['MONTO_NETO_TOTAL'].quantile(.95):>9,.0f} S/{sub['MONTO_NETO_TOTAL'].max():>11,.0f}")

# =================================================================
# 2. IDENTIFICACION DE OUTLIERS
# =================================================================
print("\n" + "=" * 70)
print("2. IDENTIFICACION DE OUTLIERS (pocas atenciones + costo anormalmente alto)")
print("=" * 70)

# Metodo: por cada grupo de N_ATENCIONES, calcular el rango intercuartilico
# del costo. Todo paciente con costo > Q3 + 3*IQR se marca como outlier.
df["ES_OUTLIER_COSTO"] = False
n_outliers_total = 0

for n_at in sorted(df["N_ATENCIONES"].unique()):
    grupo = df[df["N_ATENCIONES"] == n_at]["MONTO_NETO_TOTAL"]
    if len(grupo) < 5:
        continue
    q1 = grupo.quantile(0.25)
    q3 = grupo.quantile(0.75)
    iqr = q3 - q1
    limite = q3 + 3 * iqr
    mask = (df["N_ATENCIONES"] == n_at) & (df["MONTO_NETO_TOTAL"] > limite)
    n_outs = mask.sum()
    if n_outs > 0:
        df.loc[mask, "ES_OUTLIER_COSTO"] = True
        n_outliers_total += n_outs
        costo_max_out = df.loc[mask, "MONTO_NETO_TOTAL"].max()
        print(f"  {n_at:>4d} atenciones: {len(grupo):>6,} pac, limite=S/{limite:>9,.0f}, "
              f"outliers={n_outs:>4,} (max=S/{costo_max_out:>10,.0f})")

print(f"\n  Total outliers detectados: {n_outliers_total:,} ({n_outliers_total/N_TOTAL*100:.2f}%)")

# =================================================================
# 3. CRITERIOS DE PACIENTE "FISSAL-REAL"
# =================================================================
print("\n" + "=" * 70)
print("3. CRITERIOS DE PACIENTE FISSAL-REAL")
print("=" * 70)

# Un paciente es "FISSAL-real" si cumple TODOS estos criterios:
#   a) >= 3 atenciones (descartan visitas unicas o de paso)
#   b) NO es outlier de costo (no tiene costo anormalmente alto para sus atenciones)
#   c) Tiempo en sistema >= 1 dia (descartan atencion de un solo dia sin seguimiento)

df["FISSAL_REAL_A"] = (
    (df["N_ATENCIONES"] >= 3)
    & (~df["ES_OUTLIER_COSTO"])
    & (df["TIEMPO_EN_SISTEMA_DIAS"] >= 1)
)
df["FISSAL_REAL_B"] = (
    df["FISSAL_REAL_A"]
    & (df["SECUENCIA_TRATAMIENTO"] != "SIN_TRATAMIENTO_DETECTADO")
)

print(f"\n  Pacientes totales:                       {N_TOTAL:>6,} (100.0%)")
print(f"  Con >= 3 atenciones:                      {(df['N_ATENCIONES'] >= 3).sum():>6,} ({(df['N_ATENCIONES'] >= 3).sum()/N_TOTAL*100:.1f}%)")
print(f"  + no outlier costo:                       {((df['N_ATENCIONES'] >= 3) & (~df['ES_OUTLIER_COSTO'])).sum():>6,}")
print(f"  + tiempo en sistema >= 1 dia:             {df['FISSAL_REAL_A'].sum():>6,} ({df['FISSAL_REAL_A'].mean()*100:.1f}%)  <- Opcion A")
print(f"  + con tratamiento detectado:              {df['FISSAL_REAL_B'].sum():>6,} ({df['FISSAL_REAL_B'].mean()*100:.1f}%)  <- Opcion B")

# =================================================================
# 4. COMPARACION OPCION A vs OPCION B
# =================================================================
print("\n" + "=" * 70)
print("4. COMPARACION: TODOS vs OPCION A vs OPCION B")
print("=" * 70)

real_a = df[df["FISSAL_REAL_A"]]
real_b = df[df["FISSAL_REAL_B"]]
no_real = df[~df["FISSAL_REAL_A"]]

print(f"\n  Opcion A (>=3 aten, no outlier, >=1 dia):                {len(real_a):>6,} ({len(real_a)/N_TOTAL*100:.1f}%)")
print(f"  Opcion B (Opcion A + con tratamiento detectado):          {len(real_b):>6,} ({len(real_b)/N_TOTAL*100:.1f}%)")
print(f"  Excluidos en ambas opciones:                              {len(no_real):>6,} ({len(no_real)/N_TOTAL*100:.1f}%)")

metricas = [
    ("N_ATENCIONES", "Atenciones (mediana)"),
    ("N_PRESTACIONES", "Prestaciones (mediana)"),
    ("TIEMPO_EN_SISTEMA_DIAS", "Tiempo en sistema (mediana, dias)"),
    ("MONTO_NETO_TOTAL", "Costo neto total (mediana)"),
]
cabeceras = f"{'Metrica':<35s} {'TODOS (n='+str(N_TOTAL)+')':>20s} {'Opcion A (n='+str(len(real_a))+')':>22s} {'Opcion B (n='+str(len(real_b))+')':>22s} {'Excluidos (n='+str(len(no_real))+')':>24s}"
print(f"\n{cabeceras}")
print("-" * 130)
for col, label in metricas:
    v_all = df[col].median()
    v_a = real_a[col].median()
    v_b = real_b[col].median()
    v_no = no_real[col].median()
    if col == "MONTO_NETO_TOTAL":
        print(f"{label:<35s} S/{v_all:>18,.0f} S/{v_a:>20,.0f} S/{v_b:>20,.0f} S/{v_no:>22,.0f}")
    else:
        print(f"{label:<35s} {v_all:>20.0f} {v_a:>22.0f} {v_b:>22.0f} {v_no:>24.0f}")

# Medias
print(f"\n{'Costo neto (media)':<35s} S/{df['MONTO_NETO_TOTAL'].mean():>18,.0f} S/{real_a['MONTO_NETO_TOTAL'].mean():>20,.0f} S/{real_b['MONTO_NETO_TOTAL'].mean():>20,.0f} S/{no_real['MONTO_NETO_TOTAL'].mean():>22,.0f}")

# Tratamiento
pct_all = (df["SECUENCIA_TRATAMIENTO"] != "SIN_TRATAMIENTO_DETECTADO").mean() * 100
pct_a = (real_a["SECUENCIA_TRATAMIENTO"] != "SIN_TRATAMIENTO_DETECTADO").mean() * 100
pct_b = 100.0
print(f"{'Con tratamiento detectado':<35s} {pct_all:>19.1f}% {pct_a:>21.1f}% {pct_b:>21.1f}%")

# Hospitalizacion
pct_h_all = (df["N_HOSPITALIZACIONES"] > 0).mean() * 100
pct_h_a = (real_a["N_HOSPITALIZACIONES"] > 0).mean() * 100
pct_h_b = (real_b["N_HOSPITALIZACIONES"] > 0).mean() * 100
print(f"{'Con hospitalizacion':<35s} {pct_h_all:>19.1f}% {pct_h_a:>21.1f}% {pct_h_b:>21.1f}%")

# Fallecidos
pct_f_all = (df["DESENLACE"] == "FALLECIDO").mean() * 100
pct_f_a = (real_a["DESENLACE"] == "FALLECIDO").mean() * 100
pct_f_b = (real_b["DESENLACE"] == "FALLECIDO").mean() * 100
print(f"{'Fallecidos':<35s} {pct_f_all:>19.1f}% {pct_f_a:>21.1f}% {pct_f_b:>21.1f}%")

# Desenlace
print(f"\n  Desenlace Opcion A:")
for cat, n in real_a["DESENLACE"].value_counts().items():
    print(f"    {cat:>25s}: {n:>5,} ({n/len(real_a)*100:5.1f}%)")
print(f"\n  Desenlace Opcion B:")
for cat, n in real_b["DESENLACE"].value_counts().items():
    print(f"    {cat:>25s}: {n:>5,} ({n/len(real_b)*100:5.1f}%)")

# =================================================================
# 4b. COMPARACION DETALLADA: PERFIL TRATAMIENTO vs PERFIL CONSUMO PARCIAL
# =================================================================
print("\n" + "=" * 70)
print("4b. DOS PERFILES: TRATAMIENTO COMPLETO vs CONSUMO PARCIAL")
print("=" * 70)

# Perfil A: Tratamiento completo (FISSAL_REAL_B)
# Perfil B: Consumo parcial (FISSAL_REAL_A pero NO FISSAL_REAL_B)
tratamiento = df[df["FISSAL_REAL_B"]]
consumo_parcial = df[df["FISSAL_REAL_A"] & ~df["FISSAL_REAL_B"]]

print(f"\n  Perfil TRATAMIENTO COMPLETO (cirugia/quimio/radio + seguimiento): {len(tratamiento):,} pacientes")
print(f"    Hacen TODO su proceso oncologico en FISSAL: diagnostico, tratamiento, seguimiento.")
print(f"\n  Perfil CONSUMO PARCIAL (consultas, labs, imagenes, sin tto. oncol. detectado): {len(consumo_parcial):,} pacientes")
print(f"    Van regularmente a FISSAL pero su cirugia/quimio/radio no esta registrada aqui.")
print(f"    Posiblemente derivados a otra institucion para tratamiento, o en vigilancia activa.")

# Tabla comparativa detallada
print(f"\n{'Metrica':<45s} {'TRATAMIENTO (n='+str(len(tratamiento))+')':>30s} {'CONSUMO PARCIAL (n='+str(len(consumo_parcial))+')':>32s}")
print("-" * 112)

comparaciones = [
    ("N_ATENCIONES", "Atenciones por paciente (mediana)", "mediana"),
    ("N_PRESTACIONES", "Prestaciones por paciente (mediana)", "mediana"),
    ("TIEMPO_EN_SISTEMA_DIAS", "Tiempo en sistema (mediana, dias)", "mediana"),
    ("MONTO_NETO_TOTAL", "Costo neto CCR (mediana, S/)", "mediana"),
    ("MONTO_NETO_TOTAL", "Costo neto CCR (media, S/)", "media"),
]
for col, label, stat in comparaciones:
    if stat == "mediana":
        v_t = tratamiento[col].median()
        v_c = consumo_parcial[col].median()
    else:
        v_t = tratamiento[col].mean()
        v_c = consumo_parcial[col].mean()
    if "S/" in label:
        print(f"{label:<45s} S/{v_t:>28,.0f} S/{v_c:>30,.0f}")
    else:
        print(f"{label:<45s} {v_t:>30.0f} {v_c:>32.0f}")

# Tratamiento y hospitalizacion
pct_h_t = (tratamiento["N_HOSPITALIZACIONES"] > 0).mean() * 100
pct_h_c = (consumo_parcial["N_HOSPITALIZACIONES"] > 0).mean() * 100
print(f"{'Con hospitalizacion':<45s} {pct_h_t:>29.1f}% {pct_h_c:>31.1f}%")

pct_f_t = (tratamiento["DESENLACE"] == "FALLECIDO").mean() * 100
pct_f_c = (consumo_parcial["DESENLACE"] == "FALLECIDO").mean() * 100
print(f"{'Fallecidos':<45s} {pct_f_t:>29.1f}% {pct_f_c:>31.1f}%")

# Desenlace detallado
print(f"\n  Desenlace - TRATAMIENTO COMPLETO:")
for cat, n in tratamiento["DESENLACE"].value_counts().items():
    print(f"    {cat:>25s}: {n:>5,} ({n/len(tratamiento)*100:5.1f}%)")
print(f"\n  Desenlace - CONSUMO PARCIAL:")
for cat, n in consumo_parcial["DESENLACE"].value_counts().items():
    print(f"    {cat:>25s}: {n:>5,} ({n/len(consumo_parcial)*100:5.1f}%)")

# =================================================================
# 5. AGREGAR FLAGS AL HITOS Y GUARDAR
# =================================================================
print("\n" + "=" * 70)
print("5. GUARDANDO FLAGS EN HITOS")
print("=" * 70)

hitos_out = hitos.copy()
hitos_out["FISSAL_REAL_A"] = hitos_out["NUM_DOC_CRYPTO"].isin(
    df.loc[df["FISSAL_REAL_A"], "NUM_DOC_CRYPTO"]
)
hitos_out["FISSAL_REAL_B"] = hitos_out["NUM_DOC_CRYPTO"].isin(
    df.loc[df["FISSAL_REAL_B"], "NUM_DOC_CRYPTO"]
)
# Perfil consumo parcial: va regularmente pero sin tto oncológico detectado
hitos_out["CONSUMO_PARCIAL"] = hitos_out["FISSAL_REAL_A"] & ~hitos_out["FISSAL_REAL_B"]
hitos_out["ES_OUTLIER_COSTO"] = hitos_out["NUM_DOC_CRYPTO"].isin(
    df.loc[df["ES_OUTLIER_COSTO"], "NUM_DOC_CRYPTO"]
)
salida = SILVER / "FISSAL_CCR_HITOS_PACIENTE.parquet"
hitos_out.to_parquet(salida, index=False)
print(f"  Columnas nuevas: FISSAL_REAL_A, FISSAL_REAL_B, CONSUMO_PARCIAL, ES_OUTLIER_COSTO")
print(f"  Guardado: {salida}")
print(f"  Pacientes FISSAL_REAL_A (regular en FISSAL):    {hitos_out['FISSAL_REAL_A'].sum():,}")
print(f"  Pacientes FISSAL_REAL_B (tratamiento completo):  {hitos_out['FISSAL_REAL_B'].sum():,}")
print(f"  Pacientes CONSUMO_PARCIAL (regular sin tto):     {hitos_out['CONSUMO_PARCIAL'].sum():,}")

# =================================================================
# 6. COMORBILIDADES ONCOLOGICAS (rapido, sin recargar anuales)
# =================================================================
print("\n" + "=" * 70)
print("6. RESUMEN DE COMORBILIDADES (ya calculado antes)")
print("=" * 70)

print("""
  Las comorbilidades detectadas en los 15,698 pacientes CCR son
  mayoritariamente otros CANCERES (93% de registros no-CCR):
    - C16 (estomago):     40,651 reg
    - C50 (mama):         25,937 reg
    - C53 (cervix):       20,521 reg
    - C61 (prostata):     16,205 reg
    - C83 (linfoma):      16,408 reg
    - N18 (enf. renal):   99,199 reg (unica no-oncologica frecuente)

  NOTA IMPORTANTE: estos NO son codigos de metastasis (C77/C79).
  Son codigos de tumores PRIMARIOS en otros organos. La presencia de
  multiples canceres primarios en un mismo paciente puede deberse a:
    a) Segundos primarios reales (el paciente desarrollo otro cancer)
    b) Error de codificacion (el mismo tumor codificado con dos CIE-10)
    c) Metastasis codificadas con el codigo del primario (practica
       incorrecta pero comun cuando no se usa C77/C79)

  No se puede distinguir entre estas causas con los datos disponibles.
  Los procedimientos en otros organos (SITIO_HIGADO, SITIO_PULMON, etc.
  de 05_supervivencia_ccr.py) son un mejor proxy de metastasis.
""")

# Agregar flags de comorbilidad oncologica frecuente al hitos
print("  Agregando flags de comorbilidades al hitos...")
# Cargar data completa rapidamente solo para CIE-10
pac_ccr = set(df["NUM_DOC_CRYPTO"])
comorb_pacs = {}
patrones_comorb = {
    "COMORB_C16_ESTOMAGO": r"^C16",
    "COMORB_C50_MAMA": r"^C50",
    "COMORB_C53_CERVIX": r"^C53",
    "COMORB_C61_PROSTATA": r"^C61",
    "COMORB_C83_LINFOMA": r"^C83",
    "COMORB_N18_RENAL": r"^N18",
}

for nombre in patrones_comorb:
    comorb_pacs[nombre] = set()

for yr in range(2016, 2023):
    archivo = SILVER / f"FISSAL_PRESTACIONES_{yr}.parquet"
    if not archivo.exists():
        continue
    yr_df = pd.read_parquet(archivo, columns=["NUM_DOC_CRYPTO", "ATE_CODCIE10"])
    yr_df = yr_df[yr_df["NUM_DOC_CRYPTO"].isin(pac_ccr)]
    for nombre, patron in patrones_comorb.items():
        mask = yr_df["ATE_CODCIE10"].str.contains(patron, na=False)
        comorb_pacs[nombre].update(yr_df.loc[mask, "NUM_DOC_CRYPTO"].unique())
    del yr_df

for nombre, pacs in comorb_pacs.items():
    hitos_out[nombre] = hitos_out["NUM_DOC_CRYPTO"].isin(pacs)
    n = hitos_out[nombre].sum()
    n_a = hitos_out.loc[hitos_out["FISSAL_REAL_A"], nombre].sum()
    n_b = hitos_out.loc[hitos_out["FISSAL_REAL_B"], nombre].sum()
    print(f"  {nombre:<25s}: {n:>6,} total  |  {n_a:>6,} Opcion A  |  {n_b:>6,} Opcion B")

# Reguardar con comorbilidades
hitos_out.to_parquet(salida, index=False)
print(f"\n  Guardado final: {salida} ({hitos_out.shape[1]} columnas)")
print("\nFin.")
