import pandas as pd
import numpy as np
import sys
import gc
from pathlib import Path

SILVER = Path(r"C:\Users\eah\apoyoconsultoria.com\File Server - Analytics\7 Datos\Datos abiertos\fissal\01_silver")
ARCHIVO = SILVER / "FISSAL_CANCER_COLORRECTAL_2016_2022.parquet"
FECHA_CORTE = pd.Timestamp("2022-12-31")

print("=" * 70)
print("PERFIL DE PACIENTES CON CANCER COLORRECTAL (C18/C19/C20)")
print("FISSAL 2016-2022")
print("=" * 70)

df = pd.read_parquet(ARCHIVO)
print(f"\nRegistros totales: {len(df):,}")
print(f"Pacientes unicos: {df['NUM_DOC_CRYPTO'].nunique():,}")


# =====================================================================
# 1. TABLA RESUMEN POR PACIENTE
# =====================================================================
print("\n" + "=" * 70)
print("1. CONSTRUYENDO TABLA DE PERFIL POR PACIENTE")
print("=" * 70)

pac = (
    df.groupby("NUM_DOC_CRYPTO", sort=False)
    .agg(
        SEXO=("SEXO", "first"),
        ATE_FECNAC=("ATE_FECNAC", "first"),
        PRIMERA_ATENCION=("ATE_FECATENCION", "min"),
        ULTIMA_ATENCION=("ATE_FECATENCION", "max"),
        FEC_FALLECIMIENTO=("FEC_FALLECIMIENTO", "first"),
        DEPARTAMENTO=("DEPARTAMENTO_PAC", lambda x: x.mode().iloc[0] if not x.mode().empty else pd.NA),
        PROVINCIA=("PROVINCIA_PAC", lambda x: x.mode().iloc[0] if not x.mode().empty else pd.NA),
        IPRESS_PRINCIPAL=("ATE_NOMIPRESS", lambda x: x.mode().iloc[0] if not x.mode().empty else pd.NA),
        N_IPRESS=("ATE_NOMIPRESS", "nunique"),
        N_ATENCIONES=("ATE_FUA", "nunique"),
        N_PRESTACIONES=("ATE_FECATENCION", "size"),
        N_ANIOS=("ANIO_ATENCION", "nunique"),
        ANIOS=("ANIO_ATENCION", lambda x: sorted(x.dropna().unique().tolist())),
        PRIMER_ANIO=("ANIO_ATENCION", "min"),
        ULTIMO_ANIO=("ANIO_ATENCION", "max"),
        CIE10_PRINCIPAL=("ATE_CODCIE10", lambda x: x.mode().iloc[0] if not x.mode().empty else pd.NA),
        N_DIAGNOSTICOS=("ATE_CODCIE10", "nunique"),
        TIPOS_ATENCION=("TIPO_ATENC", lambda x: "|".join(sorted(x.dropna().unique()))),
        TIPOS_CONSUMO=("ATE_TIPOCONSUMO", lambda x: "|".join(sorted(x.dropna().unique()))),
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
pac["EDAD_PRIMERA_ATENCION"] = np.floor(
    (pac["PRIMERA_ATENCION"] - pac["ATE_FECNAC"]).dt.days / 365.25
)
# Filtrar outliers de edad. El cancer colorrectal pediatrico es extremadamente
# raro en la literatura medica (casos documentados casi siempre >=10 anios,
# asociados a sindromes hereditarios como poliposis adenomatosa familiar o
# Lynch de inicio temprano). Edades negativas (FECNAC posterior a la atencion)
# o < 10 anios casi siempre reflejan un error de captura de ATE_FECNAC o de
# codificacion CIE-10, no un caso real. Se marcan como no confiables (NA) en
# vez de eliminar al paciente, para no perder el resto de su informacion.
n_edad_invalida = ((pac["EDAD_PRIMERA_ATENCION"] < 10) | (pac["EDAD_PRIMERA_ATENCION"] > 100)).sum()
print(f"\n[Calidad de datos] Pacientes con EDAD_PRIMERA_ATENCION no confiable "
      f"(<10 o >120 anios, ver README): {n_edad_invalida:,} -> se marcan como NA")
pac.loc[(pac["EDAD_PRIMERA_ATENCION"] < 10) | (pac["EDAD_PRIMERA_ATENCION"] > 100), "EDAD_PRIMERA_ATENCION"] = pd.NA
pac["TIEMPO_EN_SISTEMA_DIAS"] = (pac["ULTIMA_ATENCION"] - pac["PRIMERA_ATENCION"]).dt.days
pac["SUPERVIVENCIA_DIAS"] = np.where(
    pac["FALLECIDO"],
    (pac["FEC_FALLECIMIENTO"] - pac["PRIMERA_ATENCION"]).dt.days,
    (FECHA_CORTE - pac["PRIMERA_ATENCION"]).dt.days,
)
pac["SUPERVIVENCIA_DIAS"] = pd.to_numeric(pac["SUPERVIVENCIA_DIAS"], errors="coerce")
pac["ANIOS"] = pac["ANIOS"].astype(str)

tuvo_hosp = df[df["TIPO_ATENC"].str.contains("HOSP", case=False, na=False)]["NUM_DOC_CRYPTO"].unique()
tuvo_emergencia = df[df["TIPO_ATENC"].str.contains("EMERG", case=False, na=False)]["NUM_DOC_CRYPTO"].unique()

pac["TUVO_HOSPITALIZACION"] = pac["NUM_DOC_CRYPTO"].isin(tuvo_hosp)
pac["TUVO_EMERGENCIA"] = pac["NUM_DOC_CRYPTO"].isin(tuvo_emergencia)

tuvo_medicamento = df[df["ATE_TIPOCONSUMO"] == "Medicamento"]["NUM_DOC_CRYPTO"].unique()
tuvo_procedimiento = df[df["ATE_TIPOCONSUMO"] == "Procedimiento"]["NUM_DOC_CRYPTO"].unique()
tuvo_cirugia = df[df["ATE_DESCCONSUMO"].str.contains("COLECTOM|RESECC|CIRUG|HEMICOLEC|COLOSTOM|LAPAROSCOP", case=False, na=False)]["NUM_DOC_CRYPTO"].unique()
tuvo_quimio = df[df["ATE_DESCCONSUMO"].str.contains("QUIMIO|OXALIPLAT|FLUOROURAC|CAPECITAB|IRINOTECAN|BEVACIZUM|CETUXIMAB|FOLFOX|FOLFIRI", case=False, na=False)]["NUM_DOC_CRYPTO"].unique()

pac["TUVO_MEDICAMENTO"] = pac["NUM_DOC_CRYPTO"].isin(tuvo_medicamento)
pac["TUVO_PROCEDIMIENTO"] = pac["NUM_DOC_CRYPTO"].isin(tuvo_procedimiento)
pac["TUVO_CIRUGIA"] = pac["NUM_DOC_CRYPTO"].isin(tuvo_cirugia)
pac["TUVO_QUIMIOTERAPIA"] = pac["NUM_DOC_CRYPTO"].isin(tuvo_quimio)

print(f"  Pacientes procesados: {len(pac):,}")


# =====================================================================
# 2. DEMOGRAFIA
# =====================================================================
print("\n" + "=" * 70)
print("2. DEMOGRAFIA")
print("=" * 70)

print("\n--- Distribucion por sexo ---")
sexo = pac["SEXO"].value_counts()
for s, n in sexo.items():
    print(f"  {s}: {n:>6,} ({n/len(pac)*100:.1f}%)")

print("\n--- Edad a la primera atencion ---")
edad = pac["EDAD_PRIMERA_ATENCION"].dropna()
print(f"  N validos: {len(edad):,}")
print(f"  Media:     {edad.mean():.1f} anios")
print(f"  Mediana:   {edad.median():.1f} anios")
print(f"  Std:       {edad.std():.1f}")
print(f"  Min:       {edad.min()}")
print(f"  Max:       {edad.max()}")

print("\n  Distribucion por rango de edad:")
bins = [0, 18, 30, 40, 50, 60, 70, 80, 120]
labels = ["0-17", "18-29", "30-39", "40-49", "50-59", "60-69", "70-79", "80+"]
pac["RANGO_EDAD"] = pd.cut(pac["EDAD_PRIMERA_ATENCION"], bins=bins, labels=labels, right=False)
rango = pac["RANGO_EDAD"].value_counts().sort_index()
for r, n in rango.items():
    print(f"    {r:>6s}: {n:>6,} ({n/len(pac)*100:.1f}%)")

print("\n  Edad por sexo:")
for s in ["F", "M"]:
    e = pac.loc[pac["SEXO"] == s, "EDAD_PRIMERA_ATENCION"].dropna()
    print(f"    {s}: media={e.mean():.1f}, mediana={e.median():.0f}, n={len(e):,}")


# =====================================================================
# 3. MORTALIDAD Y SUPERVIVENCIA
# =====================================================================
print("\n" + "=" * 70)
print("3. MORTALIDAD Y SUPERVIVENCIA")
print("=" * 70)

n_fallecidos = pac["FALLECIDO"].sum()
n_vivos = (~pac["FALLECIDO"]).sum()
print(f"\n  Fallecidos:  {n_fallecidos:>6,} ({n_fallecidos/len(pac)*100:.1f}%)")
print(f"  Sin registro fallecimiento: {n_vivos:>6,} ({n_vivos/len(pac)*100:.1f}%)")

if n_fallecidos > 0:
    fallecidos = pac[pac["FALLECIDO"]]
    sup = fallecidos["SUPERVIVENCIA_DIAS"].dropna()
    print(f"\n  Supervivencia (primera atencion -> fallecimiento):")
    print(f"    Media:   {sup.mean():.0f} dias ({sup.mean()/30:.1f} meses)")
    print(f"    Mediana: {sup.median():.0f} dias ({sup.median()/30:.1f} meses)")
    print(f"    Min:     {sup.min():.0f} dias")
    print(f"    Max:     {sup.max():.0f} dias")

    print(f"\n  Edad al fallecimiento:")
    fallecidos_edad = fallecidos["EDAD_PRIMERA_ATENCION"].dropna()
    print(f"    Media:   {fallecidos_edad.mean():.1f} anios")
    print(f"    Mediana: {fallecidos_edad.median():.0f} anios")

    print(f"\n  Fallecidos por anio de fallecimiento:")
    fall_anio = fallecidos["FEC_FALLECIMIENTO"].dt.year.value_counts().sort_index()
    for yr, n in fall_anio.items():
        print(f"    {int(yr)}: {n:>5,}")

    print(f"\n  Supervivencia por rangos:")
    sup_meses = sup / 30
    rangos_sup = [(0, 3), (3, 6), (6, 12), (12, 24), (24, 36), (36, 60), (60, 999)]
    etiquetas_sup = ["0-3m", "3-6m", "6-12m", "1-2a", "2-3a", "3-5a", "5a+"]
    for (lo, hi), etq in zip(rangos_sup, etiquetas_sup):
        n = ((sup_meses >= lo) & (sup_meses < hi)).sum()
        print(f"    {etq:>6s}: {n:>5,} ({n/len(sup)*100:.1f}%)")

    print(f"\n  Fallecidos por sexo:")
    for s in ["F", "M"]:
        n = fallecidos[fallecidos["SEXO"] == s].shape[0]
        total_s = pac[pac["SEXO"] == s].shape[0]
        print(f"    {s}: {n:>5,} de {total_s:,} ({n/total_s*100:.1f}%)")

vivos = pac[~pac["FALLECIDO"]]
print(f"\n  Pacientes sin registro de fallecimiento:")
print(f"    Tiempo en sistema (media):   {vivos['TIEMPO_EN_SISTEMA_DIAS'].mean():.0f} dias")
print(f"    Tiempo en sistema (mediana): {vivos['TIEMPO_EN_SISTEMA_DIAS'].median():.0f} dias")


# =====================================================================
# 4. DISTRIBUCION GEOGRAFICA
# =====================================================================
print("\n" + "=" * 70)
print("4. DISTRIBUCION GEOGRAFICA DE PACIENTES")
print("=" * 70)

print("\n--- Top 15 departamentos de residencia ---")
dep = pac["DEPARTAMENTO"].value_counts().head(15)
for d, n in dep.items():
    print(f"  {d:>20s}: {n:>5,} ({n/len(pac)*100:.1f}%)")

print("\n--- Top 15 provincias ---")
prov = pac["PROVINCIA"].value_counts().head(15)
for p, n in prov.items():
    print(f"  {p:>25s}: {n:>5,} ({n/len(pac)*100:.1f}%)")

lima = pac[pac["DEPARTAMENTO"] == "LIMA"].shape[0]
no_lima = pac[pac["DEPARTAMENTO"] != "LIMA"].shape[0]
print(f"\n  Lima vs Regiones:")
print(f"    Lima:     {lima:>6,} ({lima/len(pac)*100:.1f}%)")
print(f"    Regiones: {no_lima:>6,} ({no_lima/len(pac)*100:.1f}%)")


# =====================================================================
# 5. ESTABLECIMIENTOS DE SALUD (IPRESS)
# =====================================================================
print("\n" + "=" * 70)
print("5. ESTABLECIMIENTOS DE SALUD DONDE SE ATIENDEN")
print("=" * 70)

print(f"\n  IPRESS distintas en toda la data: {df['ATE_NOMIPRESS'].nunique():,}")
print(f"  IPRESS por paciente (media): {pac['N_IPRESS'].mean():.1f}")
print(f"  IPRESS por paciente (mediana): {pac['N_IPRESS'].median():.0f}")

print("\n--- Top 20 IPRESS por numero de pacientes ---")
ipress_pac = df.groupby("ATE_NOMIPRESS")["NUM_DOC_CRYPTO"].nunique().nlargest(20)
for ip, n in ipress_pac.items():
    print(f"  {n:>5,} pac | {ip}")

print("\n--- Top 20 IPRESS por monto neto ---")
ipress_monto = df.groupby("ATE_NOMIPRESS")["ATE_MONTONETO"].sum().nlargest(20)
for ip, m in ipress_monto.items():
    print(f"  S/{m:>14,.2f} | {ip}")


# =====================================================================
# 6. PACIENTES NUEVOS VS RECURRENTES POR ANIO
# =====================================================================
print("\n" + "=" * 70)
print("6. PACIENTES NUEVOS VS RECURRENTES POR ANIO")
print("=" * 70)

print(f"\n  {'Anio':>6s} {'Total':>7s} {'Nuevos':>7s} {'Recurr':>7s} {'%Nuevos':>8s}")
print("  " + "-" * 40)
anios_presentes = sorted(pac["PRIMER_ANIO"].dropna().unique())
for yr in anios_presentes:
    yr_str = str(int(yr))
    total = pac[pac["ANIOS"].str.contains(yr_str)].shape[0]
    nuevos = pac[pac["PRIMER_ANIO"] == yr].shape[0]
    recurr = total - nuevos
    pct = nuevos / total * 100 if total > 0 else 0
    print(f"  {int(yr):>6d} {total:>7,} {nuevos:>7,} {recurr:>7,} {pct:>7.1f}%")


# =====================================================================
# 7. PERFIL CLINICO GENERAL
# =====================================================================
print("\n" + "=" * 70)
print("7. PERFIL CLINICO GENERAL")
print("=" * 70)

print(f"\n  Pacientes que tuvieron hospitalizacion: {pac['TUVO_HOSPITALIZACION'].sum():>6,} ({pac['TUVO_HOSPITALIZACION'].mean()*100:.1f}%)")
print(f"  Pacientes que tuvieron emergencia:      {pac['TUVO_EMERGENCIA'].sum():>6,} ({pac['TUVO_EMERGENCIA'].mean()*100:.1f}%)")
print(f"  Pacientes con medicamentos:             {pac['TUVO_MEDICAMENTO'].sum():>6,} ({pac['TUVO_MEDICAMENTO'].mean()*100:.1f}%)")
print(f"  Pacientes con procedimientos:           {pac['TUVO_PROCEDIMIENTO'].sum():>6,} ({pac['TUVO_PROCEDIMIENTO'].mean()*100:.1f}%)")
print(f"  Pacientes con cirugia (proxy):          {pac['TUVO_CIRUGIA'].sum():>6,} ({pac['TUVO_CIRUGIA'].mean()*100:.1f}%)")
print(f"  Pacientes con quimioterapia (proxy):    {pac['TUVO_QUIMIOTERAPIA'].sum():>6,} ({pac['TUVO_QUIMIOTERAPIA'].mean()*100:.1f}%)")

print(f"\n--- Codigo CIE-10 principal por paciente ---")
cie = pac["CIE10_PRINCIPAL"].value_counts().head(10)
for c, n in cie.items():
    print(f"  {c:>6s}: {n:>5,} ({n/len(pac)*100:.1f}%)")

print(f"\n--- Numero de atenciones por paciente ---")
at = pac["N_ATENCIONES"]
print(f"  Media:   {at.mean():.1f}")
print(f"  Mediana: {at.median():.0f}")
print(f"  P25:     {at.quantile(0.25):.0f}")
print(f"  P75:     {at.quantile(0.75):.0f}")
print(f"  P95:     {at.quantile(0.95):.0f}")
print(f"  Max:     {at.max():,}")


# =====================================================================
# GUARDAR
# =====================================================================
salida = SILVER / "FISSAL_CCR_PERFIL_PACIENTES.parquet"
pac.to_parquet(salida, index=False)
print(f"\n{'=' * 70}")
print(f"Guardado perfil de {len(pac):,} pacientes en:")
print(f"  {salida}")
print(f"Columnas: {list(pac.columns)}")
