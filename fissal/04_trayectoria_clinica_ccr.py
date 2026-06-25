import pandas as pd
import numpy as np
import sys
import gc
from pathlib import Path

SILVER = Path(r"C:\Users\eah\apoyoconsultoria.com\File Server - Analytics\7 Datos\Datos abiertos\fissal\01_silver")
ARCHIVO = SILVER / "FISSAL_CANCER_COLORRECTAL_2016_2022.parquet"

print("=" * 70)
print("TRAYECTORIA CLINICA: CANCER COLORRECTAL (C18/C19/C20)")
print("FISSAL 2016-2022")
print("=" * 70)

df = pd.read_parquet(ARCHIVO)
print(f"Registros: {len(df):,} | Pacientes: {df['NUM_DOC_CRYPTO'].nunique():,}")


# =====================================================================
# 1. ANALISIS DE PROCEDIMIENTOS
# =====================================================================
print("\n" + "=" * 70)
print("1. PROCEDIMIENTOS")
print("=" * 70)

proc = df[df["ATE_TIPOCONSUMO"] == "Procedimiento"]
print(f"\n  Total registros de procedimientos: {len(proc):,}")
print(f"  Pacientes con procedimientos:     {proc['NUM_DOC_CRYPTO'].nunique():,}")
print(f"  Codigos de procedimiento unicos:  {proc['ATE_CODCONSUMO'].nunique():,}")

print("\n--- Top 30 procedimientos mas frecuentes ---")
top_proc = proc["ATE_DESCCONSUMO"].value_counts().head(30)
for i, (desc, n) in enumerate(top_proc.items(), 1):
    n_pac = proc[proc["ATE_DESCCONSUMO"] == desc]["NUM_DOC_CRYPTO"].nunique()
    print(f"  {i:>2d}. {n:>7,} reg | {n_pac:>5,} pac | {desc}")

PAT_CIRUGIA = r"(?i)COLECTOM|RESECC|HEMICOLEC|COLOSTOM|LAPAROSCOP|LAPAROTOM|ANASTOMOS"
PAT_QUIMIO = r"(?i)QUIMIO|OXALIPLAT|FLUOROURAC|CAPECITAB|IRINOTECAN|BEVACIZUM|CETUXIMAB|FOLFOX|FOLFIRI|LEUCOVORIN|PANITUMUM"
PAT_RADIO = r"(?i)RADIOTER|COBALTOT|BRAQUIT|ACELERADOR"
PAT_BIOPSIA = r"(?i)BIOPSI|ANATOMOPATOLOG"
PAT_IMAGEN = r"(?i)TOMOGRAF|RESONAN|ECOGRAF|RADIOGRAF|GAMMAGRAF|PET.?SCAN"
PAT_ENDOSCOPIA = r"(?i)COLONOSCOP|ENDOSCOP|RECTOSCOP|SIGMOIDOSCOP"
PAT_LABORATORIO = r"(?i)HEMOGRAM|CEA|ANTIGEN|MARCADOR|CREATININ|TRANSAMIN|ALBUMIN|HEMOGLOBIN|GLUCOS|BILIRRUBIN"

categorias = {
    "CIRUGIA": PAT_CIRUGIA,
    "QUIMIOTERAPIA": PAT_QUIMIO,
    "RADIOTERAPIA": PAT_RADIO,
    "BIOPSIA/PATOLOGIA": PAT_BIOPSIA,
    "IMAGEN": PAT_IMAGEN,
    "ENDOSCOPIA": PAT_ENDOSCOPIA,
    "LABORATORIO": PAT_LABORATORIO,
}

print("\n--- Procedimientos por categoria (aproximacion) ---")
for cat, pat in categorias.items():
    mask = df["ATE_DESCCONSUMO"].str.contains(pat, na=False)
    n_reg = mask.sum()
    n_pac = df.loc[mask, "NUM_DOC_CRYPTO"].nunique()
    print(f"  {cat:>20s}: {n_reg:>7,} reg | {n_pac:>5,} pac")


# =====================================================================
# 2. MEDICAMENTOS
# =====================================================================
print("\n" + "=" * 70)
print("2. MEDICAMENTOS")
print("=" * 70)

med = df[df["ATE_TIPOCONSUMO"] == "Medicamento"]
print(f"\n  Total registros de medicamentos: {len(med):,}")
print(f"  Pacientes con medicamentos:     {med['NUM_DOC_CRYPTO'].nunique():,}")
print(f"  Medicamentos unicos:            {med['ATE_CODCONSUMO'].nunique():,}")

print("\n--- Top 30 medicamentos mas frecuentes ---")
top_med = med.groupby("ATE_DESCCONSUMO").agg(
    N_REG=("ATE_DESCCONSUMO", "size"),
    N_PAC=("NUM_DOC_CRYPTO", "nunique"),
    MONTO_TOTAL=("ATE_MONTONETO", "sum"),
).nlargest(30, "N_REG")
for i, (desc, row) in enumerate(top_med.iterrows(), 1):
    print(f"  {i:>2d}. {row['N_REG']:>7,} reg | {row['N_PAC']:>5,} pac | S/{row['MONTO_TOTAL']:>12,.2f} | {desc}")

PAT_QUIMIO_MED = r"(?i)OXALIPLAT|FLUOROURAC|CAPECITAB|IRINOTECAN|LEUCOVORIN|BEVACIZUM|CETUXIMAB|PANITUMUM|RALTITREX|REGORAFENIB|TRIFLURID"
mask_quimio = med["ATE_DESCCONSUMO"].str.contains(PAT_QUIMIO_MED, na=False)
quimio_med = med[mask_quimio]

print(f"\n--- Medicamentos de quimioterapia/terapia dirigida ---")
print(f"  Registros: {len(quimio_med):,}")
print(f"  Pacientes: {quimio_med['NUM_DOC_CRYPTO'].nunique():,}")
if len(quimio_med) > 0:
    top_q = quimio_med.groupby("ATE_DESCCONSUMO").agg(
        N_REG=("ATE_DESCCONSUMO", "size"),
        N_PAC=("NUM_DOC_CRYPTO", "nunique"),
        MONTO=("ATE_MONTONETO", "sum"),
    ).nlargest(15, "N_REG")
    for desc, row in top_q.iterrows():
        print(f"    {row['N_REG']:>6,} reg | {row['N_PAC']:>5,} pac | S/{row['MONTO']:>12,.2f} | {desc}")


# =====================================================================
# 3. INSUMOS
# =====================================================================
print("\n" + "=" * 70)
print("3. INSUMOS")
print("=" * 70)

ins = df[df["ATE_TIPOCONSUMO"] == "Insumo"]
print(f"\n  Total registros de insumos: {len(ins):,}")
print(f"  Pacientes con insumos:     {ins['NUM_DOC_CRYPTO'].nunique():,}")

print("\n--- Top 20 insumos mas frecuentes ---")
top_ins = ins["ATE_DESCCONSUMO"].value_counts().head(20)
for i, (desc, n) in enumerate(top_ins.items(), 1):
    print(f"  {i:>2d}. {n:>7,} reg | {desc}")


# =====================================================================
# 4. HOSPITALIZACIONES
# =====================================================================
print("\n" + "=" * 70)
print("4. HOSPITALIZACIONES")
print("=" * 70)

hosp = df[df["TIPO_ATENC"].str.contains("HOSP", case=False, na=False)]
print(f"\n  Registros en hospitalizacion: {len(hosp):,}")
print(f"  Pacientes hospitalizados:     {hosp['NUM_DOC_CRYPTO'].nunique():,}")

hosp_episodes = (
    hosp.groupby(["NUM_DOC_CRYPTO", "ATE_FUA"], sort=False)
    .agg(
        FECHA_ING=("ATE_FECINGHOSP", "min"),
        FECHA_ALT=("ATE_FECALTHOSP", "max"),
        FECHA_ATENCION=("ATE_FECATENCION", "min"),
        IPRESS=("ATE_NOMIPRESS", "first"),
        N_ITEMS=("ATE_TIPOCONSUMO", "size"),
        MONTO_BRUTO=("ATE_MONTOBRUTO", "sum"),
        MONTO_NETO=("ATE_MONTONETO", "sum"),
    )
    .reset_index()
)

mask_fechas = hosp_episodes["FECHA_ING"].notna() & hosp_episodes["FECHA_ALT"].notna()
hosp_episodes.loc[mask_fechas, "DIAS_ESTANCIA"] = (
    hosp_episodes.loc[mask_fechas, "FECHA_ALT"] - hosp_episodes.loc[mask_fechas, "FECHA_ING"]
).dt.days

print(f"\n  Episodios de hospitalizacion (por FUA): {len(hosp_episodes):,}")

dias = hosp_episodes["DIAS_ESTANCIA"].dropna()
dias_positivos = dias[dias >= 0]
if len(dias_positivos) > 0:
    print(f"\n  Dias de estancia (cuando hay fechas):")
    print(f"    N episodios con fechas: {len(dias_positivos):,}")
    print(f"    Media:   {dias_positivos.mean():.1f} dias")
    print(f"    Mediana: {dias_positivos.median():.0f} dias")
    print(f"    P25:     {dias_positivos.quantile(0.25):.0f}")
    print(f"    P75:     {dias_positivos.quantile(0.75):.0f}")
    print(f"    P95:     {dias_positivos.quantile(0.95):.0f}")
    print(f"    Max:     {dias_positivos.max():.0f}")

hosp_por_pac = hosp_episodes.groupby("NUM_DOC_CRYPTO").size()
print(f"\n  Hospitalizaciones por paciente:")
print(f"    Media:   {hosp_por_pac.mean():.1f}")
print(f"    Mediana: {hosp_por_pac.median():.0f}")
print(f"    Max:     {hosp_por_pac.max()}")

print(f"\n  Hospitalizaciones por anio:")
hosp_episodes["ANIO"] = hosp_episodes["FECHA_ATENCION"].dt.year
for yr, n in hosp_episodes["ANIO"].value_counts().sort_index().items():
    print(f"    {int(yr)}: {n:>6,}")

# hosp_episodes.to_parquet(SILVER / "FISSAL_CCR_HOSPITALIZACIONES.parquet", index=False)


# =====================================================================
# 5. ANALISIS DE COSTOS
# =====================================================================
print("\n" + "=" * 70)
print("5. ANALISIS DE COSTOS")
print("=" * 70)

print("\n--- Costos globales ---")
print(f"  Monto bruto total:  S/{df['ATE_MONTOBRUTO'].sum():>15,.2f}")
print(f"  Monto neto total:   S/{df['ATE_MONTONETO'].sum():>15,.2f}")
diff = df["ATE_MONTOBRUTO"].sum() - df["ATE_MONTONETO"].sum()
print(f"  Diferencia (bruto - neto): S/{diff:>12,.2f}")
print(f"  Nota: Monto bruto = costo total del servicio")
print(f"        Monto neto  = lo que FISSAL efectivamente paga")

print("\n--- Costos por tipo de consumo ---")
costo_tipo = df.groupby("ATE_TIPOCONSUMO").agg(
    MONTO_BRUTO=("ATE_MONTOBRUTO", "sum"),
    MONTO_NETO=("ATE_MONTONETO", "sum"),
    N_REG=("ATE_TIPOCONSUMO", "size"),
    N_PAC=("NUM_DOC_CRYPTO", "nunique"),
).sort_values("MONTO_NETO", ascending=False)
for tipo, row in costo_tipo.iterrows():
    print(f"  {tipo:>15s}: bruto=S/{row['MONTO_BRUTO']:>14,.2f}  neto=S/{row['MONTO_NETO']:>14,.2f}  |  {row['N_REG']:>8,} reg  {row['N_PAC']:>5,} pac")

print("\n--- Costo neto por anio de atencion ---")
costo_anio = df.groupby("ANIO_ATENCION").agg(
    MONTO_BRUTO=("ATE_MONTOBRUTO", "sum"),
    MONTO_NETO=("ATE_MONTONETO", "sum"),
    N_PAC=("NUM_DOC_CRYPTO", "nunique"),
).sort_index()
for yr, row in costo_anio.iterrows():
    costo_pac = row["MONTO_NETO"] / row["N_PAC"] if row["N_PAC"] > 0 else 0
    print(f"  {int(yr)}: bruto=S/{row['MONTO_BRUTO']:>14,.2f}  neto=S/{row['MONTO_NETO']:>14,.2f}  |  {row['N_PAC']:>5,} pac  |  S/{costo_pac:>10,.2f}/pac")

print("\n--- Distribucion de costo neto total por paciente ---")
costo_pac = df.groupby("NUM_DOC_CRYPTO")["ATE_MONTONETO"].sum()
print(f"  Media:   S/{costo_pac.mean():>12,.2f}")
print(f"  Mediana: S/{costo_pac.median():>12,.2f}")
print(f"  P25:     S/{costo_pac.quantile(0.25):>12,.2f}")
print(f"  P75:     S/{costo_pac.quantile(0.75):>12,.2f}")
print(f"  P90:     S/{costo_pac.quantile(0.90):>12,.2f}")
print(f"  P95:     S/{costo_pac.quantile(0.95):>12,.2f}")
print(f"  Max:     S/{costo_pac.max():>12,.2f}")

print("\n--- Top 10 items mas costosos (monto neto total) ---")
top_cost = df.groupby("ATE_DESCCONSUMO").agg(
    MONTO_NETO=("ATE_MONTONETO", "sum"),
    N_PAC=("NUM_DOC_CRYPTO", "nunique"),
    TIPO=("ATE_TIPOCONSUMO", "first"),
).nlargest(10, "MONTO_NETO")
for desc, row in top_cost.iterrows():
    print(f"  S/{row['MONTO_NETO']:>14,.2f} | {row['N_PAC']:>5,} pac | {row['TIPO']:>15s} | {desc}")

costos_pac_anio = df.groupby(["NUM_DOC_CRYPTO", "ANIO_ATENCION"]).agg(
    MONTO_BRUTO=("ATE_MONTOBRUTO", "sum"),
    MONTO_NETO=("ATE_MONTONETO", "sum"),
    N_PRESTACIONES=("ANIO_ATENCION", "size"),
    TIPOS_CONSUMO=("ATE_TIPOCONSUMO", lambda x: "|".join(sorted(x.unique()))),
).reset_index()
# costos_pac_anio.to_parquet(SILVER / "FISSAL_CCR_COSTOS_POR_PACIENTE_ANIO.parquet", index=False)


# =====================================================================
# 6. DETECCION DE POSIBLES RECURRENCIAS
# =====================================================================
print("\n" + "=" * 70)
print("6. DETECCION DE POSIBLES RECURRENCIAS")
print("=" * 70)
print("  (Pacientes con brecha > 180 dias sin atencion, que luego regresan)")

atenciones = (
    df.groupby("NUM_DOC_CRYPTO")["ATE_FECATENCION"]
    .apply(lambda x: sorted(x.dropna().unique().tolist()))
    .reset_index()
)
atenciones.columns = ["NUM_DOC_CRYPTO", "FECHAS"]

recurrencias = []
for _, row in atenciones.iterrows():
    fechas = row["FECHAS"]
    if len(fechas) < 2:
        continue
    for i in range(1, len(fechas)):
        gap = (fechas[i] - fechas[i - 1]).days
        if gap > 180:
            recurrencias.append({
                "NUM_DOC_CRYPTO": row["NUM_DOC_CRYPTO"],
                "FECHA_ANTES_GAP": fechas[i - 1],
                "FECHA_REGRESO": fechas[i],
                "DIAS_GAP": gap,
            })

df_rec = pd.DataFrame(recurrencias)
if len(df_rec) > 0:
    pac_recurrentes = df_rec["NUM_DOC_CRYPTO"].nunique()
    print(f"\n  Episodios de brecha > 180 dias: {len(df_rec):,}")
    print(f"  Pacientes con al menos una brecha: {pac_recurrentes:,}")

    print(f"\n  Distribucion de brechas (dias):")
    print(f"    Media:   {df_rec['DIAS_GAP'].mean():.0f}")
    print(f"    Mediana: {df_rec['DIAS_GAP'].median():.0f}")
    print(f"    Max:     {df_rec['DIAS_GAP'].max():.0f}")

    print(f"\n  Brechas por rango:")
    bins_gap = [(180, 365), (365, 730), (730, 1095), (1095, 9999)]
    labels_gap = ["6m-1a", "1-2a", "2-3a", "3a+"]
    for (lo, hi), etq in zip(bins_gap, labels_gap):
        n = ((df_rec["DIAS_GAP"] >= lo) & (df_rec["DIAS_GAP"] < hi)).sum()
        print(f"    {etq:>6s}: {n:>5,}")

    # df_rec.to_parquet(SILVER / "FISSAL_CCR_BRECHAS_TRATAMIENTO.parquet", index=False)
else:
    print("  No se encontraron brechas > 180 dias.")


# =====================================================================
# 7. EVOLUCION TEMPORAL DEL TIPO DE ATENCION
# =====================================================================
print("\n" + "=" * 70)
print("7. EVOLUCION DEL TIPO DE ATENCION POR ANIO DE ATENCION")
print("=" * 70)

tipo_anio = pd.crosstab(df["ANIO_ATENCION"], df["TIPO_ATENC"])
print(f"\n{tipo_anio.to_string()}")

print("\n--- Tipo de consumo por anio de atencion ---")
consumo_anio = pd.crosstab(df["ANIO_ATENCION"], df["ATE_TIPOCONSUMO"])
print(f"\n{consumo_anio.to_string()}")


# =====================================================================
# 8. SERVICIOS (ATE_DESCSERVICIO)
# =====================================================================
print("\n" + "=" * 70)
print("8. SERVICIOS DONDE SE ATIENDEN")
print("=" * 70)

serv = df["ATE_DESCSERVICIO"].dropna()
print(f"\n  Servicios unicos: {serv.nunique()}")
print("\n--- Top 20 servicios ---")
top_serv = serv.value_counts().head(20)
for s, n in top_serv.items():
    n_pac = df[df["ATE_DESCSERVICIO"] == s]["NUM_DOC_CRYPTO"].nunique()
    print(f"  {n:>8,} reg | {n_pac:>5,} pac | {s}")


# =====================================================================
# 9. TIPO DE DOCUMENTO (ATE_TIPODOC)
# =====================================================================
print("\n" + "=" * 70)
print("9. TIPO DE DOCUMENTO DE PACIENTES")
print("=" * 70)

TIPODOC_MAP = {1: "DNI", 2: "Carnet extranjeria", 3: "Pasaporte", 4: "Otro"}
tipodoc = df.groupby("NUM_DOC_CRYPTO")["ATE_TIPODOC"].first().map(TIPODOC_MAP).fillna("Desconocido")
print(tipodoc.value_counts().to_string())


# =====================================================================
# 10. RESUMEN GENERAL
# =====================================================================
print("\n" + "=" * 70)
print("10. RESUMEN GENERAL DEL ANALISIS")
print("=" * 70)

n_pac = df["NUM_DOC_CRYPTO"].nunique()
print(f"""
  Periodo:                  2016-2022
  Registros totales:        {len(df):>10,}
  Pacientes unicos:         {n_pac:>10,}
  Atenciones (FUA) unicas:  {df['ATE_FUA'].nunique():>10,}
  IPRESS involucradas:      {df['ATE_NOMIPRESS'].nunique():>10,}
  Monto bruto total:        S/{df['ATE_MONTOBRUTO'].sum():>14,.2f}
  Monto neto total:         S/{df['ATE_MONTONETO'].sum():>14,.2f}
  Costo neto medio/paciente:S/{df.groupby('NUM_DOC_CRYPTO')['ATE_MONTONETO'].sum().mean():>14,.2f}
""")

print("Archivos generados:")
print(f"  {SILVER / 'FISSAL_CCR_HOSPITALIZACIONES.parquet'}")
print(f"  {SILVER / 'FISSAL_CCR_COSTOS_POR_PACIENTE_ANIO.parquet'}")
print(f"  {SILVER / 'FISSAL_CCR_BRECHAS_TRATAMIENTO.parquet'}")
print("\nFin.")
