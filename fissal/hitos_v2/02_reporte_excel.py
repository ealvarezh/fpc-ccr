import pyodbc
import pandas as pd
import numpy as np
from pathlib import Path
import unicodedata

SALIDA = Path(r"C:\estela\github\fpc-ccr\output")
DICCIONARIO = r"C:\Users\eah\apoyoconsultoria.com\File Server - Analytics\3 Proyectos\2025\2025-116-L FPC Dashboard 25\4 Analisis\3 Programas\adicional 2026\diccionario_ATE_DESCCONSUMO_502_estandarizado.xlsx"
SALIDA.mkdir(parents=True, exist_ok=True)
EXCEL_OUT = SALIDA / "FISSAL_CCR_Analisis_Completo.xlsx"

def normalizar(s):
    if pd.isna(s): return ""
    s = str(s).strip().upper()
    s = s.replace("  ", " ").replace("(", "").replace(")", "").replace(";", "").replace(",", "")
    s = s.replace('"', "").replace("'", "")
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")

print("=" * 70)
print("Reporte Excel Completo — FISSAL CCR v2")
print("=" * 70)

# =====================================================================
# 0. VERIFICACION IDs
# =====================================================================
print("\n0. Verificando IDs...")
conn = pyodbc.connect("DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost;DATABASE=Reporte_Transparencia;Trusted_Connection=yes;")
df_ids = pd.read_sql("""
    SELECT Codigo_identificacion_paciente, COUNT(*) as n_reg,
           COUNT(DISTINCT Codigo_sexo) as sexos, MIN(Fecha_Nacimiento) fnac_min, MAX(Fecha_Nacimiento) fnac_max
    FROM [Reporte_2016_2026_v1] WHERE Codigo_identificacion_paciente IS NOT NULL
    GROUP BY Codigo_identificacion_paciente
    HAVING COUNT(DISTINCT Codigo_sexo) > 1 OR MIN(Fecha_Nacimiento) != MAX(Fecha_Nacimiento)
""", conn)
print(f"  IDs con datos inconsistentes: {len(df_ids):,} (0 = perfecto)")

# =====================================================================
# 1. CARGAR HITOS Y DICCIONARIO
# =====================================================================
print("\n1. Cargando datos...")
OUTPUT = Path(r"C:\Users\eah\apoyoconsultoria.com\File Server - Analytics\7 Datos\Datos abiertos\fissal\01_silver")
h = pd.read_parquet(OUTPUT / "FISSAL_CCR_HITOS_V2.parquet")
dic = pd.read_excel(DICCIONARIO)
# Recalculamos la clave desde ATE_DESCCONSUMO (texto crudo) en vez de usar la
# columna clave_normalizada del excel: esa se genero con una normalizacion
# distinta a normalizar() y rompe el join para items que si estan
# clasificados (ver nota en 01_construir_hitos_v2.py).
dic["clave_norm"] = dic["ATE_DESCCONSUMO"].apply(normalizar)
dic = dic[["clave_norm", "categoria_recurso_502", "subcategoria_recurso_502", "atribucion_crc_sugerida"]].drop_duplicates(subset="clave_norm")

track = h[(h["TRACK"] == "A_COMPLETO") & (h["FISSAL_REGULAR"])].copy()
n_track = len(track)
n_total = len(h)
print(f"  Todos: {n_total:,}  |  Track A regular: {n_track:,}")

# =====================================================================
# 2. CARGAR DATOS DETALLADOS SQL + JOIN DICCIONARIO
# =====================================================================
print("\n2. Cargando datos detallados SQL...")
ids_track = [int(x) for x in track["Codigo_identificacion_paciente"]]

# Temp table
cursor = conn.cursor()
cursor.execute("CREATE TABLE #t (id INT PRIMARY KEY)")
for i in range(0, len(ids_track), 1000):
    batch = ids_track[i:i + 1000]
    vals = ",".join(f"({x})" for x in batch)
    cursor.execute(f"INSERT INTO #t (id) VALUES {vals}")
conn.commit()

query = """
    SELECT d.Codigo_identificacion_paciente, d.Fecha_atencion, d.Tipo_atencion,
           d.Fecha_ingreso_hospitalizacion, d.Fecha_alta_hospitalizacion,
           d.Codigo_CIE10, d.Descripcion_CIE10,
           d.TipoConsumo, d.Descripcion_Consumo, d.MONTO_NETO, d.MONTO_BRUTO,
           d.Descripcio_servicio, d.Año_produccion
    FROM [Reporte_2016_2026_v1] d
    INNER JOIN #t t ON d.Codigo_identificacion_paciente = t.id
    ORDER BY d.Codigo_identificacion_paciente, d.Fecha_atencion
"""
df = pd.read_sql(query, conn)
conn.close()

for col in ["Fecha_atencion", "Fecha_ingreso_hospitalizacion", "Fecha_alta_hospitalizacion"]:
    df[col] = pd.to_datetime(df[col], errors="coerce")

# Join con diccionario
df["clave_norm"] = df["Descripcion_Consumo"].apply(normalizar)
df = df.merge(dic, on="clave_norm", how="left")
df["categoria_recurso_502"] = df["categoria_recurso_502"].fillna("Sin clasificar")
df["subcategoria_recurso_502"] = df["subcategoria_recurso_502"].fillna("Sin subcategoria")

# Flags
df["ES_CCR"] = df["Codigo_CIE10"].str.match(r"^C(18|19|20)", na=False)
df["ES_OTRO_CANCER"] = df["Codigo_CIE10"].str.match(r"^C", na=False) & ~df["ES_CCR"]
df["ES_NO_CANCER"] = ~df["Codigo_CIE10"].str.match(r"^C", na=False)

print(f"  Registros: {len(df):,}  |  Pacientes: {df['Codigo_identificacion_paciente'].nunique():,}")
print(f"  CCR: {(df['ES_CCR']).sum():,} ({df['ES_CCR'].mean()*100:.0f}%)")
print(f"  Otro cancer: {(df['ES_OTRO_CANCER']).sum():,} ({df['ES_OTRO_CANCER'].mean()*100:.0f}%)")
print(f"  No cancer: {(df['ES_NO_CANCER']).sum():,} ({df['ES_NO_CANCER'].mean()*100:.0f}%)")

# =====================================================================
# 2b. DEFLACTAR COSTOS A SOLES DE 2024
# =====================================================================
FACTORES_IPC = {2018: 1.26, 2019: 1.24, 2020: 1.22, 2021: 1.14, 2022: 1.05, 2023: 1.02, 2024: 1.00, 2025: 1.00, 2026: 1.00}

# Deflactar en track (nivel paciente)
for yr, factor in FACTORES_IPC.items():
    col = f"COSTO_{yr}"
    if col in track.columns:
        track[f"COSTO_{yr}_DEFLACTADO"] = track[col] * factor

# Costo total deflactado = suma de costos anuales deflactados
cols_defl = [f"COSTO_{yr}_DEFLACTADO" for yr in FACTORES_IPC if f"COSTO_{yr}_DEFLACTADO" in track.columns]
track["MONTO_NETO_TOTAL_DEFLACTADO"] = track[cols_defl].sum(axis=1)

# Mismo criterio para los 3 buckets de atribucion CRC: deflactar año a año
# (en vez de un factor IPC promedio plano sobre el total nominal, que
# sobreestima el costo real cuando el gasto se concentra en años recientes)
for bucket in ["CRC_ATRIBUIBLE", "SOPORTE", "NO_ATRIBUIBLE"]:
    prefijo = f"COSTO_{bucket}"
    for yr, factor in FACTORES_IPC.items():
        col = f"{prefijo}_{yr}"
        if col in track.columns:
            track[f"{col}_DEFLACTADO"] = track[col] * factor
    cols_defl_b = [f"{prefijo}_{yr}_DEFLACTADO" for yr in FACTORES_IPC if f"{prefijo}_{yr}_DEFLACTADO" in track.columns]
    track[f"{prefijo}_DEFLACTADO"] = track[cols_defl_b].sum(axis=1)

# Deflactar en df (nivel registro)
df["FACTOR_IPC"] = df["Año_produccion"].map(FACTORES_IPC).fillna(1.0)
df["MONTO_NETO_DEFLACTADO"] = df["MONTO_NETO"] * df["FACTOR_IPC"]

print(f"\n  Costo mediano nominal:     {track['MONTO_NETO_TOTAL'].median():,.0f}")
print(f"  Costo mediano deflactado:  {track['MONTO_NETO_TOTAL_DEFLACTADO'].median():,.0f}")

# =====================================================================
# SHEET 1: RESUMEN
# =====================================================================
print("\n3. Generando sheets...")
t_anos = track["TIEMPO_EN_SISTEMA_DIAS"] / 365
costo_anual = track["MONTO_NETO_TOTAL_DEFLACTADO"] / t_anos.replace(0, np.nan)

resumen = pd.DataFrame([
    ["Pacientes totales", n_total, "", ""],
    ["Pacientes con tratamiento", n_track, "", "Track A + FISSAL regular: que si recibieron cirugía/quimio/radio/endoscopía"],
    ["--- Costos nominales ---", "", "", ""],
    ["mediana", round(track["MONTO_NETO_TOTAL"].median(), 0), "Soles corrientes", ""],
    ["media", round(track["MONTO_NETO_TOTAL"].mean(), 0), "Soles corrientes", ""],
    ["--- Costos deflactados ---", "", "", ""],
    ["mediana", round(track["MONTO_NETO_TOTAL_DEFLACTADO"].median(), 0), "Soles 2024", "Ajustado por IPC a valor presente, año a año"],
    ["media", round(track["MONTO_NETO_TOTAL_DEFLACTADO"].mean(), 0), "Soles 2024", ""],
    ["--- Desglose deflactado - mediana ---", "", "", ""],
    ["Costo tratamiento", round(track["COSTO_CRC_ATRIBUIBLE_DEFLACTADO"].median(), 0), "Soles 2024", "Solo cirugía/quimio/radio/endoscopía"],
    ["Costo soporte", round(track["COSTO_SOPORTE_DEFLACTADO"].median(), 0), "Soles 2024", "Labs, imágenes, medicamentos, etc"],
    ["Costo no atribuible", round(track["COSTO_NO_ATRIBUIBLE_DEFLACTADO"].median(), 0), "Soles 2024", "Vacunas, utensilios médicos, etc"],
    ["--- Desglose deflactado - media ---", "", "", ""],
    ["Costo tratamiento", round(track["COSTO_CRC_ATRIBUIBLE_DEFLACTADO"].mean(), 0), "Soles 2024", "Solo cirugía/quimio/radio/endoscopía"],
    ["Costo soporte", round(track["COSTO_SOPORTE_DEFLACTADO"].mean(), 0), "Soles 2024", "Labs, imágenes, medicamentos, etc"],
    ["Costo no atribuible", round(track["COSTO_NO_ATRIBUIBLE_DEFLACTADO"].mean(), 0), "Soles 2024", "Vacunas, utensilios médicos, etc"],
    ["--- Tiempos en sistema ---", "", "", ""],
    ["mediana (días)", round(track["TIEMPO_EN_SISTEMA_DIAS"].median(), 0), "Dias", ""],
    ["media (días)", round(track["TIEMPO_EN_SISTEMA_DIAS"].mean(), 0), "Dias", ""],
    ["mediana (años)", round(t_anos.median(), 1), "Años", ""],
    ["media (años)", round(t_anos.mean(), 1), "Años", ""],
    ["--- Gasto por año/paciente - deflactado ---", "", "", ""],
    ["mediana", round(costo_anual.median(), 0), "Soles 2024/año", ""],
    ["media", round(costo_anual.mean(), 0), "Soles 2024/año", ""],
    ["--- Hospitalizacion ---", "", "", ""],
    ["Dias - mediana", round(track["DIAS_HOSPITALIZACION_TOTAL"].median(), 0), "Dias", ""],
    ["n° hospitalizaciones - mediana", round(track["N_HOSPITALIZACIONES"].median(), 0), "Episodios", ""],
    ["--- Mortalidad ---", "", "", ""],
    ["Fallecidos", int(track["FALLECIDO"].sum()), "Pacientes", f"de {n_track:,} en Track A + FISSAL regular"],
    ["proporción", round(track["FALLECIDO"].mean(), 3), "Proporcion", ""],
], columns=["Metrica", "Valor", "Unidad", "Nota"])
print("  Sheet 1 OK")

# =====================================================================
# SHEET 2: TIEMPOS ENTRE HITOS
# =====================================================================
tiempos_def = [
    ("Ingreso a Intervencion", "DIAS_INGRESO_A_INTERVENCION",
     "Dias desde la primera atencion en FISSAL hasta que inicia el primer tratamiento oncoloógico (cirugia/quimio/radio). Mide el tiempo de espera."),
    ("Intervencion a Cierre", "DIAS_INTERVENCION_A_CIERRE",
     "Dias desde que termina el ultimo tratamiento hasta el cierre (fallecimiento o ultima atencion). Mide el seguimiento post-tratamiento."),
    ("Trayectoria total", "DIAS_TRAYECTORIA_TOTAL",
     "Dias desde la primera atencion hasta el cierre. Es la suma de los dos anteriores mas la duracion del tratamiento."),
    ("Tiempo en sistema", "TIEMPO_EN_SISTEMA_DIAS",
     "Dias entre la primera y ultima atencion registrada en FISSAL. Si el paciente sigue activo, es hasta su ultima visita."),
    ("Hospitalizacion total (dias)", "DIAS_HOSPITALIZACION_TOTAL",
     "Suma de dias de TODAS las hospitalizaciones del paciente. Si es 0, nunca estuvo hospitalizado o las fechas de ingreso/alta no se registraron."),
    ("Numero de hospitalizaciones", "N_HOSPITALIZACIONES",
     "Cantidad de episodios de hospitalizacion distintos. Si es 0, nunca fue hospitalizado."),
]

tiempos_rows = []
for label, col, nota in tiempos_def:
    s = track[col].dropna()
    if "N_HOSP" in col:
        s_pos = s
    else:
        s_pos = s[s >= 0]
    if len(s_pos) == 0:
        continue
    tiempos_rows.append({
        "Intervalo": label,
        "Explicacion": nota,
        "n": len(s_pos),
        "Media": round(s_pos.mean(), 1),
        "Mediana": round(s_pos.median(), 0),
        "P25": round(s_pos.quantile(0.25), 0),
        "P75": round(s_pos.quantile(0.75), 0),
        "P95": round(s_pos.quantile(0.95), 0),
        "Max": round(s_pos.max(), 0),
    })
df_tiempos = pd.DataFrame(tiempos_rows)
print("  Sheet 2 OK")

# =====================================================================
# SHEET 3: HOSPITALIZACION - DISTRIBUCION REAL
# =====================================================================
hosp = df[df["Fecha_ingreso_hospitalizacion"].notna() | df["Fecha_alta_hospitalizacion"].notna()].copy()
hosp["ESTANCIA"] = (hosp["Fecha_alta_hospitalizacion"] - hosp["Fecha_ingreso_hospitalizacion"]).dt.days
hosp["ESTANCIA"] = hosp["ESTANCIA"].where((hosp["ESTANCIA"] >= 0) & (hosp["ESTANCIA"] <= 365), np.nan)

# Cada hospitalizacion genera varias lineas de consumo que comparten las
# mismas fechas de ingreso/alta: hay que colapsar a nivel de episodio antes
# de contar o sumar dias, si no se multiplica por el numero de items facturados.
hosp_ep = hosp.groupby(
    ["Codigo_identificacion_paciente", "Fecha_ingreso_hospitalizacion", "Fecha_alta_hospitalizacion"],
    dropna=False,
).agg(ESTANCIA=("ESTANCIA", "first")).reset_index()

# Cuantos tienen 0 dias y por que
n_est0 = (hosp_ep["ESTANCIA"] == 0).sum()
n_total_hosp = len(hosp_ep)

hosp_stats = pd.DataFrame([
    ["Total episodios con fecha ingreso/alta", n_total_hosp, "", ""],
    ["Episodios con estancia = 0 dias", n_est0, f"{n_est0/n_total_hosp*100:.1f}%",
     "Ingreso y alta el mismo dia (cirugia ambulatoria, consulta con internamiento breve, o fechas iguales por registro administrativo)"],
    ["Episodios con estancia > 0", n_total_hosp - n_est0, "", ""],
    ["Estancia mediana (todos los episodios)", round(hosp_ep["ESTANCIA"].median(), 1), "dias", ""],
    ["Estancia media (todos los episodios)", round(hosp_ep["ESTANCIA"].mean(), 1), "dias", ""],
    ["Estancia mediana (solo >0)", round(hosp_ep.loc[hosp_ep["ESTANCIA"] > 0, "ESTANCIA"].median(), 1) if (hosp_ep["ESTANCIA"] > 0).any() else "N/D", "dias", ""],
], columns=["Metrica", "Valor", "%", "Nota"])

# Distribucion de estancia (>0)
bins_h = [0, 1, 2, 3, 4, 7, 15, 30, 99999]
labels_h = ["1 dia", "2 dias", "3-4 dias", "5-7 dias", "8-15 dias", "16-30 dias", "31-90 dias", "91+ dias"]
hosp_pos = hosp_ep[hosp_ep["ESTANCIA"] > 0].copy()
hosp_pos["RANGO"] = pd.cut(hosp_pos["ESTANCIA"], bins=bins_h, labels=labels_h, right=True)
hosp_dist = []
for r in labels_h:
    sub = hosp_pos[hosp_pos["RANGO"] == r]
    if len(sub) == 0: continue
    hosp_dist.append({"Rango_estancia": r, "Episodios": len(sub), "Proporcion": round(len(sub)/len(hosp_pos), 3)})
df_hosp_dist = pd.DataFrame(hosp_dist)

# Por paciente (episodios y dias, a nivel de episodio ya deduplicado; el costo
# de hospitalizacion si se suma a nivel de linea porque cada item facturado
# es un monto real distinto, no una repeticion del mismo dato)
hosp_pac_ep = hosp_ep.groupby("Codigo_identificacion_paciente").agg(
    episodios=("ESTANCIA", "size"),
    dias_totales=("ESTANCIA", "sum"),
    estancia_mediana=("ESTANCIA", "median"),
).reset_index()
hosp_pac_costo = hosp.groupby("Codigo_identificacion_paciente")["MONTO_NETO"].sum().reset_index(name="costo_hosp")
hosp_pac = hosp_pac_ep.merge(hosp_pac_costo, on="Codigo_identificacion_paciente", how="left")

# Stats por paciente
hosp_pac_stats = pd.DataFrame({
    "Metrica": ["n_pacientes", "episodios_media", "episodios_mediana", "dias_totales_media", "dias_totales_mediana",
                "estancia_por_episodio_media", "estancia_por_episodio_mediana", "costo_hosp_media", "costo_hosp_mediana"],
    "Valor": [
        len(hosp_pac),
        round(hosp_pac["episodios"].mean(), 1), round(hosp_pac["episodios"].median(), 0),
        round(hosp_pac["dias_totales"].mean(), 0), round(hosp_pac["dias_totales"].median(), 0),
        round(hosp_pac["estancia_mediana"].mean(), 1), round(hosp_pac["estancia_mediana"].median(), 0),
        round(hosp_pac["costo_hosp"].mean(), 0), round(hosp_pac["costo_hosp"].median(), 0),
    ],
})
print("  Sheet 3 OK")

# =====================================================================
# SHEET 4: COSTO DE OTROS MALES (NO-CCR)
# =====================================================================
# Costo por tipo de codigo
costo_tipo = df.groupby("Codigo_identificacion_paciente").agg(
    costo_CCR=("MONTO_NETO", lambda x: x[df.loc[x.index, "ES_CCR"]].sum()),
    costo_OTRO_CANCER=("MONTO_NETO", lambda x: x[df.loc[x.index, "ES_OTRO_CANCER"]].sum()),
    costo_NO_CANCER=("MONTO_NETO", lambda x: x[df.loc[x.index, "ES_NO_CANCER"]].sum()),
    costo_TOTAL=("MONTO_NETO", "sum"),
).reset_index()

for c in costo_tipo.columns:
    costo_tipo[c] = costo_tipo[c].fillna(0)

costo_tipo["pct_CCR"] = costo_tipo["costo_CCR"] / costo_tipo["costo_TOTAL"].replace(0, np.nan)
costo_tipo["pct_OTRO_CANCER"] = costo_tipo["costo_OTRO_CANCER"] / costo_tipo["costo_TOTAL"].replace(0, np.nan)
costo_tipo["pct_NO_CANCER"] = costo_tipo["costo_NO_CANCER"] / costo_tipo["costo_TOTAL"].replace(0, np.nan)

otros_males = pd.DataFrame([
    ["Costo total cohorte (millones)", round(costo_tipo["costo_TOTAL"].sum() / 1e6, 1), "", ""],
    ["% que es CCR (C18/19/20)", round(costo_tipo["costo_CCR"].sum() / costo_tipo["costo_TOTAL"].sum(), 3), "", ""],
    ["% que es OTRO CANCER (C, no CCR)", round(costo_tipo["costo_OTRO_CANCER"].sum() / costo_tipo["costo_TOTAL"].sum(), 3), "", "Ej: C16 estomago, C50 mama, C61 prostata"],
    ["% que es NO CANCER", round(costo_tipo["costo_NO_CANCER"].sum() / costo_tipo["costo_TOTAL"].sum(), 3), "", "Ej: N18 renal, E11 diabetes, J respiratorias"],
    ["Pacientes CON gasto en otro cancer", (costo_tipo["costo_OTRO_CANCER"] > 0).sum(), "", f"{(costo_tipo['costo_OTRO_CANCER'] > 0).mean()*100:.1f}% de pacientes"],
    ["Pacientes CON gasto no-cancer", (costo_tipo["costo_NO_CANCER"] > 0).sum(), "", f"{(costo_tipo['costo_NO_CANCER'] > 0).mean()*100:.1f}% de pacientes"],
    ["Mediana gasto en otro cancer (solo >0)", round(costo_tipo.loc[costo_tipo["costo_OTRO_CANCER"] > 0, "costo_OTRO_CANCER"].median(), 0), "", ""],
    ["Mediana gasto no-cancer (solo >0)", round(costo_tipo.loc[costo_tipo["costo_NO_CANCER"] > 0, "costo_NO_CANCER"].median(), 0), "", ""],
    ["Costo total de otros canceres", round(costo_tipo["costo_OTRO_CANCER"].sum(), 0), "", ""],
    ["Costo total no-cancer", round(costo_tipo["costo_NO_CANCER"].sum(), 0), "", ""],
], columns=["Metrica", "Valor", "Unidad", "Nota"])

# Top CIE-10 no-CCR mas costosos
otros_cie = df[~df["ES_CCR"]].groupby("Codigo_CIE10").agg(
    n_pac=("Codigo_identificacion_paciente", "nunique"),
    costo_total=("MONTO_NETO", "sum"),
    descripcion=("Descripcion_CIE10", "first"),
).sort_values("costo_total", ascending=False).head(20).reset_index()
print("  Sheet 4 OK")

# =====================================================================
# SHEET 5: TOP CATEGORIAS Y SUBCATEGORIAS
# =====================================================================
# Agrupar por categoria -> top 1 subcategoria de cada una
cat_agg = df.groupby("categoria_recurso_502").agg(
    n_registros=("clave_norm", "size"),
    n_pacientes=("Codigo_identificacion_paciente", "nunique"),
    costo_total=("MONTO_NETO", "sum"),
    costo_mediano=("MONTO_NETO", "median"),
).sort_values("costo_total", ascending=False)

cat_agg["pct_costo"] = (cat_agg["costo_total"] / df["MONTO_NETO"].sum()).round(3)
cat_agg = cat_agg.reset_index()
cat_agg.index = range(1, len(cat_agg) + 1)
cat_agg.index.name = "Rank"

# Top 5 subcategorias dentro de cada categoria
subcat_rows = []
for cat in cat_agg["categoria_recurso_502"]:
    sub = df[df["categoria_recurso_502"] == cat].groupby("subcategoria_recurso_502").agg(
        n_reg=("clave_norm", "size"),
        n_pac=("Codigo_identificacion_paciente", "nunique"),
        costo=("MONTO_NETO", "sum"),
    ).sort_values("costo", ascending=False).head(5)
    for rank, (subcat, row) in enumerate(sub.iterrows(), 1):
        subcat_rows.append({
            "Categoria": cat, "Subcategoria_rank": rank, "Subcategoria": subcat,
            "n_registros": row["n_reg"], "n_pacientes": row["n_pac"],
            "costo_total": row["costo"], "pct_del_costo_categoria": round(row["costo"] / sub["costo"].sum(), 3),
        })
df_subcats = pd.DataFrame(subcat_rows)
print("  Sheet 5 OK")

# =====================================================================
# SHEET 6: SEVERIDAD AL INGRESO
# =====================================================================
severidad = track.groupby(["INGRESO_GRAVE", "LOCALIZACION"]).agg(
    n_pacientes=("Codigo_identificacion_paciente", "count"),
    costo_mediano_nominal=("MONTO_NETO_TOTAL", "median"),
    costo_mediano_deflactado=("MONTO_NETO_TOTAL_DEFLACTADO", "median"),
    costo_medio_deflactado=("MONTO_NETO_TOTAL_DEFLACTADO", "mean"),
    tiempo_mediano=("TIEMPO_EN_SISTEMA_DIAS", "median"),
    pct_fallecidos=("FALLECIDO", "mean"),
    dias_hosp_mediano=("DIAS_HOSPITALIZACION_TOTAL", "median"),
).reset_index()
severidad["pct_fallecidos"] = severidad["pct_fallecidos"].round(3)
for c in ["costo_mediano_nominal", "costo_mediano_deflactado", "costo_medio_deflactado", "tiempo_mediano", "dias_hosp_mediano"]:
    severidad[c] = severidad[c].round(0)

severidad["Tipo_ingreso"] = severidad["INGRESO_GRAVE"].map({True: "Grave (Emergencia/Hosp)", False: "Ambulatorio"})
severidad = severidad.drop(columns=["INGRESO_GRAVE"])
print("  Sheet 6 OK")

# =====================================================================
# SHEET 7: FALLECIDOS
# =====================================================================
fall = track[track["FALLECIDO"]].copy()
bins_fall = [0, 30, 90, 180, 365, 730, 99999]
labels_fall = ["0-1 mes", "1-3 meses", "3-6 meses", "6m-1a", "1-2a", "2a+"]
fall["RANGO"] = pd.cut(fall["TIEMPO_EN_SISTEMA_DIAS"], bins=bins_fall, labels=labels_fall, right=True)

fall_dist = []
for r in labels_fall:
    sub = fall[fall["RANGO"] == r]
    if len(sub) == 0: continue
    fall_dist.append({
        "Tiempo_hasta_fallecer_en_FISSAL": r,
        "Explicacion": f"El paciente estuvo entre {r} en FISSAL desde su primer registro hasta su muerte",
        "n_pacientes": len(sub),
        "proporcion": round(len(sub) / len(fall), 3),
        "costo_mediano_nominal": round(sub["MONTO_NETO_TOTAL"].median(), 0),
        "costo_mediano_deflactado": round(sub["MONTO_NETO_TOTAL_DEFLACTADO"].median(), 0),
        "dias_hosp_mediano": round(sub["DIAS_HOSPITALIZACION_TOTAL"].median(), 0),
    })
df_fall = pd.DataFrame(fall_dist)
print("  Sheet 7 OK")

# =====================================================================
# SHEET 8: EVOLUCION ANUAL
# =====================================================================
cost_cols = sorted([c for c in track.columns if c.startswith("COSTO_20") and "_DEFLACTADO" not in c])
evol_rows = []
for cc in cost_cols:
    yr = int(cc.split("_")[1])
    vals_nom = track[cc]
    vals_pos = vals_nom[vals_nom > 0]
    col_defl = f"{cc}_DEFLACTADO"
    vals_defl = track[col_defl] if col_defl in track.columns else vals_nom * FACTORES_IPC.get(yr, 1.0)
    vals_defl_pos = vals_defl[vals_defl > 0]
    evol_rows.append({
        "Año": yr,"Factor_IPC": FACTORES_IPC.get(yr, 1.0),
        "pacientes_con_gasto": len(vals_pos),
        "gasto_total_nominal": round(vals_nom.sum(), 0),
        "gasto_total_deflactado": round(vals_defl.sum(), 0),
        "gasto_mediano_nominal": round(vals_pos.median(), 0) if len(vals_pos) > 0 else 0,
        "gasto_mediano_deflactado": round(vals_defl_pos.median(), 0) if len(vals_defl_pos) > 0 else 0,
    })
df_evol = pd.DataFrame(evol_rows)
print("  Sheet 8 OK")

# =====================================================================
# WRITE EXCEL
# =====================================================================
print(f"\n4. Escribiendo: {EXCEL_OUT}")
with pd.ExcelWriter(EXCEL_OUT, engine="openpyxl") as writer:
    resumen.to_excel(writer, sheet_name="1_Resumen", index=False)
    df_tiempos.to_excel(writer, sheet_name="2_Tiempos", index=False)
    hosp_stats.to_excel(writer, sheet_name="3_Hospitalizacion", index=False)
    hosp_pac_stats.to_excel(writer, sheet_name="3b_Hosp_x_Paciente", index=False)
    df_hosp_dist.to_excel(writer, sheet_name="3c_Distribucion_Estancia", index=False)
    otros_males.to_excel(writer, sheet_name="4_Otros_Males_Costos", index=False)
    otros_cie.to_excel(writer, sheet_name="4b_Top20_CIE10_NoCCR", index=False)
    cat_agg.to_excel(writer, sheet_name="5_Categorias", index=True)
    df_subcats.to_excel(writer, sheet_name="5b_Subcategorias_Top5", index=False)
    severidad.to_excel(writer, sheet_name="6_Severidad_Ingreso", index=False)
    df_fall.to_excel(writer, sheet_name="7_Fallecidos", index=False)
    df_evol.to_excel(writer, sheet_name="8_Evolucion_Anual", index=False)

print(f"\nExcel: {EXCEL_OUT}")
print(f"Sheets: 15")
print("Fin.")
