import sys
import pandas as pd
import numpy as np
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
pd.set_option('display.max_columns', None)

SILVER = Path(r"C:\Users\eah\apoyoconsultoria.com\File Server - Analytics\7 Datos\Datos abiertos\fissal\01_silver")
ARCHIVO_CCR = SILVER / "FISSAL_CANCER_COLORRECTAL_2016_2022.parquet"
ARCHIVO_HITOS = SILVER / "FISSAL_CCR_HITOS_PACIENTE.parquet"
ARCHIVO_EVENTOS = SILVER / "FISSAL_CCR_HITOS_EVENTOS.parquet"

RANGOS_EDAD = ["0-17", "18-29", "30-39", "40-49", "50-59", "60-69", "70-79", "80+"]

print("=" * 70)
print("CARACTERIZACION DE HITOS DEL PACIENTE — CANCER COLORRECTAL")
print("FISSAL 2016-2022")
print("=" * 70)

hp = pd.read_parquet(ARCHIVO_HITOS)
ev = pd.read_parquet(ARCHIVO_EVENTOS)
df = pd.read_parquet(ARCHIVO_CCR)
n_total = len(hp)
print(f"Pacientes: {n_total:,}")


def resumen_costo(serie, titulo, indent=4):
    s = serie.dropna()
    pre = " " * indent
    if len(s) == 0:
        print(f"{pre}(sin datos)")
        return
    print(f"{pre}{titulo}")
    print(f"{pre}  Media: S/{s.mean():>10,.2f}  Mediana: S/{s.median():>10,.2f}  "
          f"P25: S/{s.quantile(.25):>10,.2f}  P75: S/{s.quantile(.75):>10,.2f}  "
          f"P90: S/{s.quantile(.90):>10,.2f}  Max: S/{s.max():>12,.2f}")


def resumen_dias(serie, titulo, indent=4):
    s = serie.dropna()
    s = s[s >= 0]
    pre = " " * indent
    if len(s) == 0:
        print(f"{pre}(sin datos)")
        return
    print(f"{pre}{titulo}")
    print(f"{pre}  Media: {s.mean():>7.1f}d  Mediana: {s.median():>6.0f}d  "
          f"P25: {s.quantile(.25):>5.0f}d  P75: {s.quantile(.75):>5.0f}d  P95: {s.quantile(.95):>5.0f}d")


def dist_demografica(sub, indent=4):
    pre = " " * indent
    n = len(sub)
    if n == 0:
        print(f"{pre}(sin pacientes)")
        return
    for sexo, n_s in sub["SEXO"].value_counts().items():
        print(f"{pre}  {sexo}: {n_s:,} ({n_s/n*100:.1f}%)")
    edad = sub["EDAD_PRIMERA_ATENCION"].dropna()
    if len(edad) > 0:
        print(f"{pre}  Edad media: {edad.mean():.1f}  Edad mediana: {edad.median():.0f}")
    lima = (sub["DEPARTAMENTO"] == "LIMA").sum()
    print(f"{pre}  Lima: {lima:,} ({lima/n*100:.1f}%)  Regiones: {n-lima:,} ({(n-lima)/n*100:.1f}%)")


# =====================================================================
# 0. EMBUDO DE PACIENTES POR HITO
# =====================================================================
print("\n" + "=" * 70)
print("0. EMBUDO DE PACIENTES POR HITO")
print("=" * 70)

n_desp = hp["TUVO_DESPISTAJE_PREVIO"].sum()
n_dx = len(hp)
n_trat = (hp["SECUENCIA_TRATAMIENTO"] != "SIN_TRATAMIENTO_DETECTADO").sum()
n_fallecido = (hp["DESENLACE"] == "FALLECIDO").sum()
n_paliativo = (hp["DESENLACE"] == "PALIATIVO").sum()

print(f"""
  1. Despistaje detectado en FISSAL:  {n_desp:>6,} ({n_desp/n_dx*100:5.1f}% del total)
  2. Diagnostico CCR (base):          {n_dx:>6,} (100.0%)
  3. Algun tratamiento detectado:     {n_trat:>6,} ({n_trat/n_dx*100:5.1f}%)
  4. Desenlace = Fallecido:           {n_fallecido:>6,} ({n_fallecido/n_dx*100:5.1f}%)
     Desenlace = Paliativo:           {n_paliativo:>6,} ({n_paliativo/n_dx*100:5.1f}%)
""")


# =====================================================================
# 1. HITO 1: DESPISTAJE / DETECCION
# =====================================================================
print("=" * 70)
print("1. HITO: DESPISTAJE / DETECCION (antes del diagnostico)")
print("=" * 70)

con_desp = hp[hp["TUVO_DESPISTAJE_PREVIO"]]
sin_desp = hp[~hp["TUVO_DESPISTAJE_PREVIO"]]

print(f"\n  Con despistaje detectado: {len(con_desp):,} ({len(con_desp)/n_total*100:.1f}%)")
print(f"  Sin despistaje detectado (diagnostico es su 1er registro CCR-relevante): "
      f"{len(sin_desp):,} ({len(sin_desp)/n_total*100:.1f}%)")

print("\n  --- Tipo de procedimiento de despistaje (primer evento detectado) ---")
for tipo, n in con_desp["TIPO_DESPISTAJE"].value_counts().items():
    print(f"    {tipo:>22s}: {n:>5,} ({n/len(con_desp)*100:5.1f}%)")

print("\n  --- Tiempo desde despistaje hasta diagnostico formal ---")
resumen_dias(con_desp["DIAS_DESPISTAJE_A_DIAGNOSTICO"], "Dias despistaje -> diagnostico:")

print("\n  --- Costo acumulado ANTES del diagnostico (todos los registros previos) ---")
resumen_costo(hp.loc[hp["N_REGISTROS_PRE_DIAGNOSTICO"] > 0, "COSTO_NETO_PRE_DIAGNOSTICO"],
              "Costo neto pre-diagnostico (pacientes con actividad previa):")

print("\n  --- Demografia: con despistaje vs sin despistaje ---")
print("    CON despistaje:")
dist_demografica(con_desp)
print("    SIN despistaje:")
dist_demografica(sin_desp)

print("\n  --- Top 10 IPRESS donde ocurre el despistaje ---")
top_ipress_desp = con_desp["IPRESS_DESPISTAJE"].value_counts().head(10)
for ipress, n in top_ipress_desp.items():
    print(f"    {n:>4,} | {ipress}")


# =====================================================================
# 2. HITO 2: DIAGNOSTICO
# =====================================================================
print("\n" + "=" * 70)
print("2. HITO: DIAGNOSTICO")
print("=" * 70)

print("\n  --- Tipo de atencion en el momento del diagnostico ---")
for tipo, n in hp["TIPO_ATENCION_DIAGNOSTICO"].value_counts().items():
    print(f"    {tipo:>20s}: {n:>6,} ({n/n_total*100:5.1f}%)")
print("    Nota: diagnostico via EMERGENCIA/HOSPITALIZACION sugiere cuadro mas urgente/avanzado")
print("    que diagnostico via consulta AMBULATORIA.")

print("\n  --- Distribucion CIE10 al diagnostico (C18 colon / C19 union rectosigmoidea / C20 recto) ---")
hp["CIE10_PREFIJO"] = hp["CIE10_DIAGNOSTICO"].str[:3]
for cod, n in hp["CIE10_PREFIJO"].value_counts().items():
    print(f"    {cod:>10s}: {n:>6,} ({n/n_total*100:5.1f}%)")

print("\n  --- Diagnosticos por anio ---")
hp["ANIO_DIAGNOSTICO"] = hp["FECHA_DIAGNOSTICO"].dt.year
for yr, n in hp["ANIO_DIAGNOSTICO"].value_counts().sort_index().items():
    print(f"    {int(yr)}: {n:>5,}")

print("\n  --- Top 15 IPRESS de diagnostico ---")
for ipress, n in hp["IPRESS_DIAGNOSTICO"].value_counts().head(15).items():
    print(f"    {n:>5,} | {ipress}")

print("\n  --- Demografia al diagnostico (todos los pacientes) ---")
dist_demografica(hp)

print("\n  --- Diagnostico via emergencia/hospitalizacion segun edad ---")
hp["INGRESO_URGENTE"] = hp["TIPO_ATENCION_DIAGNOSTICO"].isin(["EMERGENCIA", "HOSPITALIZACIÓN"])
for r in RANGOS_EDAD:
    sub = hp[hp["RANGO_EDAD"] == r]
    if len(sub) == 0:
        continue
    n_urg = sub["INGRESO_URGENTE"].sum()
    print(f"    {r:>5s} (n={len(sub):>5,}): urgente/hosp={n_urg:>4,} ({n_urg/len(sub)*100:5.1f}%)")


# =====================================================================
# 3. HITO 3: TRATAMIENTO
# =====================================================================
print("\n" + "=" * 70)
print("3. HITO: TRATAMIENTO")
print("=" * 70)

print("\n  --- Combinaciones de tratamiento recibidas ---")
for combo, n in hp["SECUENCIA_TRATAMIENTO"].value_counts().head(15).items():
    print(f"    {n:>5,} ({n/n_total*100:4.1f}%) | {combo}")

for cat in ["CIRUGIA", "QUIMIOTERAPIA", "RADIOTERAPIA"]:
    sub = hp[hp[f"TUVO_{cat}"]]
    print(f"\n  --- {cat} (n={len(sub):,}) ---")
    resumen_dias(sub[f"DURACION_{cat}_DIAS"], "Duracion del tratamiento (primera a ultima sesion):")
    print(f"    Sesiones/registros por paciente -> media: {sub[f'N_SESIONES_{cat}'].mean():.1f}  "
          f"mediana: {sub[f'N_SESIONES_{cat}'].median():.0f}  max: {sub[f'N_SESIONES_{cat}'].max():.0f}")
    resumen_costo(sub[f"COSTO_NETO_{cat}"], "Costo neto:")
    dist_demografica(sub)

print("\n  --- Tiempo diagnostico -> inicio de tratamiento, por grupo ---")
for col, etiquetas in [("SEXO", None), ("RANGO_EDAD", RANGOS_EDAD)]:
    valores = etiquetas if etiquetas else sorted(hp[col].dropna().unique())
    print(f"\n    Por {col}:")
    for v in valores:
        sub = hp[hp[col] == v]
        if len(sub) == 0:
            continue
        dias = sub["DIAS_DIAGNOSTICO_A_TRATAMIENTO"].dropna()
        dias = dias[dias >= 0]
        if len(dias) == 0:
            continue
        print(f"      {str(v):>8s} (n={len(dias):>5,}): media={dias.mean():>6.1f}d  mediana={dias.median():>5.0f}d")

print("\n  --- Hospitalizacion asociada al tratamiento ---")
con_hosp = hp[hp["N_HOSPITALIZACIONES"] > 0]
print(f"    Pacientes con >=1 hospitalizacion: {len(con_hosp):,} ({len(con_hosp)/n_total*100:.1f}%)")
resumen_dias(con_hosp["DIAS_HOSPITALIZACION_TOTAL"], "Dias totales de hospitalizacion (acumulado por paciente):")
print(f"    N hospitalizaciones/paciente -> media: {con_hosp['N_HOSPITALIZACIONES'].mean():.1f}  "
      f"mediana: {con_hosp['N_HOSPITALIZACIONES'].median():.0f}")

print("\n  --- Adherencia: brechas > 45 dias durante el tratamiento activo ---")
con_trat = hp[hp["SECUENCIA_TRATAMIENTO"] != "SIN_TRATAMIENTO_DETECTADO"]
n_con_brecha = con_trat["TUVO_BRECHA_ADHERENCIA"].sum()
print(f"    Pacientes en tratamiento con al menos 1 brecha: {n_con_brecha:,} "
      f"({n_con_brecha/len(con_trat)*100:.1f}% de los que tuvieron tratamiento)")
resumen_dias(con_trat.loc[con_trat["TUVO_BRECHA_ADHERENCIA"], "BRECHA_MAX_DIAS"],
             "Brecha maxima (dias) en pacientes con brechas:")
print("\n    Adherencia por rango de edad:")
for r in RANGOS_EDAD:
    sub = con_trat[con_trat["RANGO_EDAD"] == r]
    if len(sub) == 0:
        continue
    nb = sub["TUVO_BRECHA_ADHERENCIA"].sum()
    print(f"      {r:>5s} (n={len(sub):>5,}): con brecha={nb:>4,} ({nb/len(sub)*100:5.1f}%)")

print("\n  --- Top 15 procedimientos de CIRUGIA (por N de registros) ---")
cir = df[df["ATE_DESCCONSUMO"].str.contains(
    r"(?i)COLECTOM|RESECC|HEMICOLEC|COLOSTOM|LAPAROTOM|ANASTOMOS|LAPAROSCOP", na=False)]
top_cir = cir.groupby("ATE_DESCCONSUMO").agg(
    N_REG=("ATE_DESCCONSUMO", "size"), N_PAC=("NUM_DOC_CRYPTO", "nunique"),
    MONTO=("ATE_MONTONETO", "sum"),
).nlargest(15, "N_REG")
for desc, row in top_cir.iterrows():
    print(f"    {row['N_REG']:>5,} reg | {row['N_PAC']:>4,} pac | S/{row['MONTO']:>11,.2f} | {desc}")

print("\n  --- Costo total del tramo de tratamiento (todo lo facturado entre inicio y fin) ---")
resumen_costo(con_trat["COSTO_NETO_TRATAMIENTO_TOTAL"], "Costo neto total del tramo:")


# =====================================================================
# 4. HITO 4: DESENLACE
# =====================================================================
print("\n" + "=" * 70)
print("4. HITO: DESENLACE")
print("=" * 70)

print("\n  --- Distribucion de desenlaces ---")
for cat, n in hp["DESENLACE"].value_counts().items():
    print(f"    {cat:>25s}: {n:>6,} ({n/n_total*100:5.1f}%)")

print("\n  --- Caracteristicas por tipo de desenlace ---")
for cat in ["FALLECIDO", "PALIATIVO", "RECAIDA_PROBABLE", "CONTROL_POST_PAUSA",
            "POSIBLE_REMISION_O_ALTA", "EN_SEGUIMIENTO_ACTIVO"]:
    sub = hp[hp["DESENLACE"] == cat]
    if len(sub) == 0:
        continue
    print(f"\n    {cat} (n={len(sub):,}):")
    dist_demografica(sub, indent=6)
    for c in ["TUVO_CIRUGIA", "TUVO_QUIMIOTERAPIA", "TUVO_RADIOTERAPIA"]:
        pct = sub[c].mean() * 100
        print(f"      {c:>18s}: {pct:5.1f}%")
    print(f"      Combinacion de tratamiento mas comun: "
          f"{sub['SECUENCIA_TRATAMIENTO'].value_counts().idxmax() if sub['SECUENCIA_TRATAMIENTO'].notna().any() else 'N/A'}")
    con_hosp_sub = sub[sub["N_HOSPITALIZACIONES"] > 0]
    print(f"      Con hospitalizacion: {len(con_hosp_sub):,} ({len(con_hosp_sub)/len(sub)*100:5.1f}%)")
    resumen_dias(sub["SUPERVIVENCIA_DIAS"], "Dias desde diagnostico hasta fin de seguimiento/muerte:", indent=6)
    resumen_costo(sub["MONTO_NETO_TOTAL"], "Costo neto TOTAL acumulado del paciente:", indent=6)
    if cat in ("RECAIDA_PROBABLE", "CONTROL_POST_PAUSA"):
        resumen_dias(sub["DIAS_BRECHA_PREVIA_RETORNO"], "Dias de la brecha previa al retorno:", indent=6)

print("\n  --- Desenlace segun si recibio tratamiento detectado o no ---")
for combo_grupo, label in [
    (hp["SECUENCIA_TRATAMIENTO"] != "SIN_TRATAMIENTO_DETECTADO", "CON tratamiento detectado"),
    (hp["SECUENCIA_TRATAMIENTO"] == "SIN_TRATAMIENTO_DETECTADO", "SIN tratamiento detectado"),
]:
    sub = hp[combo_grupo]
    print(f"\n    {label} (n={len(sub):,}):")
    for cat, n in sub["DESENLACE"].value_counts().items():
        print(f"      {cat:>25s}: {n:>6,} ({n/len(sub)*100:5.1f}%)")


# =====================================================================
# 5. COMPARACION ENTRE HITOS: COSTO Y DURACION
# =====================================================================
print("\n" + "=" * 70)
print("5. COMPARACION ENTRE HITOS")
print("=" * 70)

resumen_hitos = []
resumen_hitos.append({
    "HITO": "1. Despistaje", "N_PAC": len(con_desp),
    "COSTO_NETO_MEDIO": hp.loc[hp["N_REGISTROS_PRE_DIAGNOSTICO"] > 0, "COSTO_NETO_PRE_DIAGNOSTICO"].mean(),
    "DURACION_MEDIA_DIAS": hp["DIAS_DESPISTAJE_A_DIAGNOSTICO"].dropna().pipe(lambda s: s[s >= 0]).mean(),
})
resumen_hitos.append({
    "HITO": "3. Tratamiento", "N_PAC": len(con_trat),
    "COSTO_NETO_MEDIO": con_trat["COSTO_NETO_TRATAMIENTO_TOTAL"].mean(),
    "DURACION_MEDIA_DIAS": con_trat["DURACION_DIAS"].mean() if "DURACION_DIAS" in con_trat.columns else
        (hp["FECHA_FIN_TRATAMIENTO"] - hp["FECHA_INICIO_TRATAMIENTO"]).dt.days.mean(),
})
resumen_df = pd.DataFrame(resumen_hitos)
print(f"\n{resumen_df.to_string(index=False)}")

print("\n  --- Costo neto TOTAL del paciente, por tipo de desenlace (de mayor a menor) ---")
costo_desenlace = hp.groupby("DESENLACE")["MONTO_NETO_TOTAL"].agg(["mean", "median", "sum", "count"])
costo_desenlace = costo_desenlace.sort_values("mean", ascending=False)
for cat, row in costo_desenlace.iterrows():
    print(f"    {cat:>25s}: media=S/{row['mean']:>10,.2f}  mediana=S/{row['median']:>10,.2f}  "
          f"n={int(row['count']):>5,}")

print(f"\n{'=' * 70}")
print("Fin del analisis de hitos.")
print(f"{'=' * 70}")
