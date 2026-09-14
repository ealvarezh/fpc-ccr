"""
Arma el set de parquets para replicar el dashboard HTML en Power BI, SIN que
Power BI tenga que conectarse a SQL Server (import mode con archivos livianos
en vez de una conexion pesada en vivo).

Filosofia del modelo (esquema estrella):
  - dim_anio                     : 1 fila por año, con el factor IPC. Se
                                    relaciona con fact_costo_anual para poder
                                    deflactar con una medida DAX (nunca se
                                    guarda un costo "ya deflactado" fijo,
                                    salvo el costo proyectado de EsSalud, que
                                    por su naturaleza de benchmark ya viene
                                    resuelto -- ver nota en esa seccion).
  - fact_pacientes_fissal        : 1 fila por paciente (grano mas fino =
                                    dimension de paciente + hechos que ya son
                                    naturalmente 1:1 con el paciente: track,
                                    localizacion, fechas, mortalidad, costo
                                    NOMINAL total). Se relaciona 1-a-muchos
                                    con el resto de tablas fact_* via
                                    Codigo_identificacion_paciente.
  - fact_costo_anual             : paciente x año x bucket (TOTAL /
                                    CRC_ATRIBUIBLE / SOPORTE / NO_ATRIBUIBLE),
                                    formato largo. Reemplaza a las columnas
                                    anchas COSTO_2018..COSTO_2026 que trae el
                                    parquet de hitos -- en Power BI es mucho
                                    mas facil de agregar/filtrar en formato
                                    largo que en columnas anchas.
  - fact_costo_categoria         : paciente x categoria x subcategoria (502).
                                    Grano fino a proposito: permite que Power
                                    BI calcule la MEDIANA de costo por
                                    paciente en cualquier categoria (con
                                    MEDIANX), algo que un pre-agregado no deja
                                    hacer. Requiere una extraccion nueva de
                                    SQL (no estaba guardada en ningun parquet
                                    existente).
  - fact_costo_otros_diagnosticos: paciente x CIE10 (solo diagnosticos NO CCR)
                                    -- para replicar "Otros males".
  - fact_hospitalizacion         : paciente x episodio de hospitalizacion, ya
                                    deduplicado por (ingreso, alta) -- mismo
                                    criterio que el fix aplicado en
                                    01_construir_hitos_v2.py.
  - fact_essalud_gcop            : paciente candidato de EsSalud (perfil +
                                    costo proyectado). El costo proyectado ya
                                    viene resuelto (no es una medida DAX)
                                    porque depende de un match difuso contra
                                    un benchmark de FISSAL -- replicar esa
                                    logica en DAX no vale la pena.
  - fact_sis                     : paciente SIS (fuera de FISSAL).

Guarda todo en OUTPUT_DIR (ver abajo). Volver a correr cuando cambien los
datos fuente.
"""
import pyodbc
import pandas as pd
import numpy as np
import unicodedata
from pathlib import Path

DICCIONARIO = r"C:\Users\eah\apoyoconsultoria.com\File Server - Analytics\3 Proyectos\2025\2025-116-L FPC Dashboard 25\4 Analisis\3 Programas\adicional 2026\diccionario_ATE_DESCCONSUMO_502_estandarizado.xlsx"
HITOS_PARQUET = Path(r"C:\Users\eah\apoyoconsultoria.com\File Server - Analytics\7 Datos\Datos abiertos\fissal\01_silver\FISSAL_CCR_HITOS_V2.parquet")
ESSALUD_DIR = Path(r"C:\estela\github\fpc-ccr\complementarios\essalud\output")
SIS_DIR = Path(r"C:\estela\github\fpc-ccr\complementarios\sis\output")
OUTPUT_DIR = Path(r"C:\Users\eah\apoyoconsultoria.com\File Server - Analytics\3 Proyectos\2025\2025-116-L FPC Dashboard 25\4 Analisis\4 Resultados\Adicional 2026")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

FACTORES_IPC = {2018: 1.26, 2019: 1.24, 2020: 1.22, 2021: 1.14, 2022: 1.05, 2023: 1.02, 2024: 1.00, 2025: 1.00, 2026: 1.00}

print("=" * 70)
print("Construccion de parquets para Power BI")
print("=" * 70)


def normalizar_clave(s):
    if pd.isna(s):
        return ""
    s = str(s).strip().upper()
    s = s.replace("  ", " ")
    s = s.replace("(", "").replace(")", "")
    s = s.replace(";", "").replace(",", "")
    s = s.replace('"', "").replace("'", "")
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")
    return s


# =====================================================================
# 1. DIM_ANIO
# =====================================================================
dim_anio = pd.DataFrame([{"anio": a, "factor_ipc": f} for a, f in FACTORES_IPC.items()])
dim_anio.to_parquet(OUTPUT_DIR / "dim_anio.parquet", index=False)
print(f"1. dim_anio.parquet  ({len(dim_anio)} filas)")

# =====================================================================
# 2. FACT_PACIENTES_FISSAL + FACT_COSTO_ANUAL (desde el parquet de hitos, sin SQL)
# =====================================================================
print("\n2. Cargando hitos FISSAL (parquet ya existente)...")
h = pd.read_parquet(HITOS_PARQUET)

cols_paciente = [
    "Codigo_identificacion_paciente", "SEXO", "EDAD_PRIMERA_ATENCION", "RANGO_EDAD",
    "LOCALIZACION", "TIPO_INGRESO", "IPRESS_INGRESO", "GRUPO_CIE10_INGRESO", "INGRESO_GRAVE",
    "FECHA_DIAGNOSTICO_CCR", "PRIMERA_ATENCION", "ULTIMA_ATENCION",
    "FALLECIDO", "FECHA_FALLECIMIENTO", "FECHA_FALLECIMIENTO_EXACTA", "FECHA_FALLECIMIENTO_EFECTIVA",
    "N_ATENCIONES", "TIEMPO_EN_SISTEMA_DIAS",
    "TRACK", "TIENE_TRATAMIENTO_ONCOLOGICO", "FECHA_INICIO_INTERVENCION", "FECHA_FIN_INTERVENCION",
    "FISSAL_REGULAR", "ES_OUTLIER_COSTO",
    "CIERRE", "FECHA_CIERRE",
    "DIAS_INGRESO_A_INTERVENCION", "DIAS_INTERVENCION_A_CIERRE", "DIAS_TRAYECTORIA_TOTAL",
    "N_HOSPITALIZACIONES", "DIAS_HOSPITALIZACION_TOTAL",
    "MONTO_NETO_TOTAL", "COSTO_CRC_ATRIBUIBLE", "COSTO_SOPORTE", "COSTO_NO_ATRIBUIBLE",
]
fact_pacientes = h[cols_paciente].copy()
fact_pacientes.to_parquet(OUTPUT_DIR / "fact_pacientes_fissal.parquet", index=False)
print(f"   fact_pacientes_fissal.parquet  ({len(fact_pacientes):,} filas, {len(cols_paciente)} columnas)")

# Melt de las columnas anchas COSTO_{anio} y COSTO_{bucket}_{anio} a formato largo
print("   Reestructurando costo anual a formato largo...")
piezas = []
for anio in FACTORES_IPC:
    col_total = f"COSTO_{anio}"
    if col_total in h.columns:
        piezas.append(pd.DataFrame({
            "Codigo_identificacion_paciente": h["Codigo_identificacion_paciente"],
            "anio": anio, "bucket": "TOTAL", "costo_nominal": h[col_total],
        }))
    for bucket in ["CRC_ATRIBUIBLE", "SOPORTE", "NO_ATRIBUIBLE"]:
        col_b = f"COSTO_{bucket}_{anio}"
        if col_b in h.columns:
            piezas.append(pd.DataFrame({
                "Codigo_identificacion_paciente": h["Codigo_identificacion_paciente"],
                "anio": anio, "bucket": bucket, "costo_nominal": h[col_b],
            }))
fact_costo_anual = pd.concat(piezas, ignore_index=True)
fact_costo_anual = fact_costo_anual[fact_costo_anual["costo_nominal"] > 0]  # aligerar: no guardar ceros
fact_costo_anual.to_parquet(OUTPUT_DIR / "fact_costo_anual.parquet", index=False)
print(f"   fact_costo_anual.parquet  ({len(fact_costo_anual):,} filas)")

# Melt de las 6 columnas de "tiempos entre hitos" a formato largo (paciente x
# intervalo x dias) -- para que en Power BI cada intervalo se pueda agregar
# con una medida generica (MEDIANX/AVERAGEX/PERCENTILEX.INC) en vez de tener
# que escribir un SWITCH distinto por columna.
print("   Reestructurando tiempos entre hitos a formato largo...")
INTERVALOS = {
    "Ingreso a Intervencion": "DIAS_INGRESO_A_INTERVENCION",
    "Intervencion a Cierre": "DIAS_INTERVENCION_A_CIERRE",
    "Trayectoria total": "DIAS_TRAYECTORIA_TOTAL",
    "Tiempo en sistema": "TIEMPO_EN_SISTEMA_DIAS",
    "Hospitalizacion total (dias)": "DIAS_HOSPITALIZACION_TOTAL",
    "Numero de hospitalizaciones": "N_HOSPITALIZACIONES",
}
DESCRIPCIONES_INTERVALO = {
    "Ingreso a Intervencion": "Dias desde la primera atencion en FISSAL hasta que inicia el primer tratamiento oncologico (cirugia/quimio/radio). Mide el tiempo de espera.",
    "Intervencion a Cierre": "Dias desde que termina el ultimo tratamiento hasta el cierre (fallecimiento o ultima atencion). Mide el seguimiento post-tratamiento.",
    "Trayectoria total": "Dias desde la primera atencion hasta el cierre. Es la suma de los dos anteriores mas la duracion del tratamiento.",
    "Tiempo en sistema": "Dias entre la primera y ultima atencion registrada en FISSAL. Si el paciente sigue activo, es hasta su ultima visita.",
    "Hospitalizacion total (dias)": "Suma de dias de TODAS las hospitalizaciones del paciente. Si es 0, nunca estuvo hospitalizado.",
    "Numero de hospitalizaciones": "Cantidad de episodios de hospitalizacion distintos. Si es 0, nunca fue hospitalizado.",
}
piezas_t = []
for intervalo, col in INTERVALOS.items():
    sub = h[["Codigo_identificacion_paciente", col]].rename(columns={col: "dias"}).copy()
    sub["intervalo"] = intervalo
    sub = sub.dropna(subset=["dias"])
    sub = sub[sub["dias"] >= 0]  # mismo filtro que 02_reporte_excel.py: descartar negativos
    piezas_t.append(sub[["Codigo_identificacion_paciente", "intervalo", "dias"]])
fact_tiempos_hitos = pd.concat(piezas_t, ignore_index=True)
fact_tiempos_hitos.to_parquet(OUTPUT_DIR / "fact_tiempos_hitos.parquet", index=False)
print(f"   fact_tiempos_hitos.parquet  ({len(fact_tiempos_hitos):,} filas)")

dim_intervalo = pd.DataFrame([
    {"intervalo": k, "explicacion": v, "orden": i + 1}
    for i, (k, v) in enumerate(DESCRIPCIONES_INTERVALO.items())
])
dim_intervalo.to_parquet(OUTPUT_DIR / "dim_intervalo.parquet", index=False)
print(f"   dim_intervalo.parquet  ({len(dim_intervalo)} filas)")

# =====================================================================
# 3. EXTRACCION SQL DETALLADA (para categoria/subcategoria, otros diagnosticos, hospitalizacion)
# =====================================================================
print("\n3. Extrayendo detalle de SQL Server (una sola pasada para las 3 tablas siguientes)...")
dic = pd.read_excel(DICCIONARIO)
dic["clave_normalizada"] = dic["ATE_DESCCONSUMO"].apply(normalizar_clave)
dic = dic[["clave_normalizada", "categoria_recurso_502", "subcategoria_recurso_502"]].drop_duplicates(subset="clave_normalizada")

conn = pyodbc.connect(
    "DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost;DATABASE=Reporte_Transparencia;Trusted_Connection=yes;"
)
query = """
SELECT
    Codigo_identificacion_paciente, Fecha_atencion,
    Codigo_CIE10, Descripcion_CIE10,
    Descripcion_Consumo, MONTO_NETO,
    Fecha_ingreso_hospitalizacion, Fecha_alta_hospitalizacion
FROM [Reporte_2016_2026_v1]
WHERE Codigo_identificacion_paciente IN (
    SELECT DISTINCT Codigo_identificacion_paciente
    FROM [Reporte_2016_2026_v1]
    WHERE Codigo_CIE10 LIKE 'C18%' OR Codigo_CIE10 LIKE 'C19%' OR Codigo_CIE10 LIKE 'C20%'
)
"""
df = pd.read_sql(query, conn)
conn.close()
print(f"   Registros: {len(df):,}")

df["Fecha_atencion"] = pd.to_datetime(df["Fecha_atencion"], errors="coerce")
df["Fecha_ingreso_hospitalizacion"] = pd.to_datetime(df["Fecha_ingreso_hospitalizacion"], errors="coerce")
df["Fecha_alta_hospitalizacion"] = pd.to_datetime(df["Fecha_alta_hospitalizacion"], errors="coerce")
df["clave_normalizada"] = df["Descripcion_Consumo"].apply(normalizar_clave)
df = df.merge(dic, on="clave_normalizada", how="left")
df["categoria_recurso_502"] = df["categoria_recurso_502"].fillna("Sin clasificar")
df["subcategoria_recurso_502"] = df["subcategoria_recurso_502"].fillna("Sin subcategoria")

# --- 3a. fact_costo_categoria (paciente x categoria x subcategoria) --------
fact_costo_categoria = df.groupby(
    ["Codigo_identificacion_paciente", "categoria_recurso_502", "subcategoria_recurso_502"]
).agg(costo_nominal=("MONTO_NETO", "sum"), n_registros=("MONTO_NETO", "size")).reset_index()
fact_costo_categoria.to_parquet(OUTPUT_DIR / "fact_costo_categoria.parquet", index=False)
print(f"3a. fact_costo_categoria.parquet  ({len(fact_costo_categoria):,} filas)")

# --- 3b. fact_costo_otros_diagnosticos (paciente x CIE10 no-CCR) ----------
es_ccr = df["Codigo_CIE10"].str.match(r"^C(18|19|20)", na=False)
otros = df[~es_ccr].copy()
otros["tipo_diagnostico"] = np.where(otros["Codigo_CIE10"].str.match(r"^C", na=False), "OTRO_CANCER", "NO_CANCER")
fact_otros = otros.groupby(
    ["Codigo_identificacion_paciente", "Codigo_CIE10", "Descripcion_CIE10", "tipo_diagnostico"]
).agg(costo_nominal=("MONTO_NETO", "sum"), n_registros=("MONTO_NETO", "size")).reset_index()

# Nombre corto por CIE10 (mismos ~20 curados a mano que en el dashboard, con
# un fallback automatico -que simplifica "TUMOR MALIGNO DE(L)..." a "Cancer
# de..."- para el resto, asi ningun codigo se queda con el nombre largo).
DESCRIPCION_CORTA = {
    "C920": "Leucemia mieloide aguda", "C833": "Linfoma no Hodgkin celulas grandes",
    "N180": "Insuf. renal terminal", "N185": "Enf. renal cronica etapa 5",
    "C859": "Linfoma no Hodgkin", "C61X": "Cancer de prostata",
    "C819": "Enfermedad de Hodgkin", "C851": "Linfoma de celulas B",
    "C169": "Cancer de estomago", "C509": "Cancer de mama",
    "C539": "Cancer de cuello uterino", "N189": "Insuf. renal cronica",
    "C531": "Cancer de exocervix", "C839": "Linfoma no Hodgkin difuso",
    "C504": "Cancer de mama (cuadrante sup. ext.)", "C163": "Cancer gastrico (antro pilorico)",
    "C162": "Cancer de cuerpo gastrico", "C530": "Cancer de endocervix",
    "C160": "Cancer de cardias", "E119": "Diabetes tipo 2",
}


def descripcion_corta(codigo, descripcion):
    if codigo in DESCRIPCION_CORTA:
        return DESCRIPCION_CORTA[codigo]
    d = str(descripcion).strip()
    for pat in ["TUMOR MALIGNO DE LA ", "TUMOR MALIGNO DEL ", "TUMOR MALIGNO DE ", "TUMOR MALIGNO "]:
        if d.startswith(pat):
            return "Cancer de " + d[len(pat):].capitalize()
    d = d.capitalize()
    return d if len(d) <= 42 else d[:39] + "..."


fact_otros["descripcion_corta"] = [
    descripcion_corta(c, d) for c, d in zip(fact_otros["Codigo_CIE10"], fact_otros["Descripcion_CIE10"])
]
fact_otros.to_parquet(OUTPUT_DIR / "fact_costo_otros_diagnosticos.parquet", index=False)
print(f"3b. fact_costo_otros_diagnosticos.parquet  ({len(fact_otros):,} filas)")

# --- 3c. fact_hospitalizacion (paciente x episodio, deduplicado) ----------
hosp = df[df["Fecha_ingreso_hospitalizacion"].notna()].copy()
fact_hosp = hosp.groupby(
    ["Codigo_identificacion_paciente", "Fecha_ingreso_hospitalizacion", "Fecha_alta_hospitalizacion"],
    dropna=False,
).agg(costo_episodio=("MONTO_NETO", "sum"), n_lineas=("MONTO_NETO", "size")).reset_index()
fact_hosp["dias_estancia"] = (fact_hosp["Fecha_alta_hospitalizacion"] - fact_hosp["Fecha_ingreso_hospitalizacion"]).dt.days
fact_hosp["dias_estancia"] = fact_hosp["dias_estancia"].where(
    (fact_hosp["dias_estancia"] >= 0) & (fact_hosp["dias_estancia"] <= 365), pd.NA
)
fact_hosp = fact_hosp.rename(columns={
    "Fecha_ingreso_hospitalizacion": "fecha_ingreso", "Fecha_alta_hospitalizacion": "fecha_alta",
})
fact_hosp.to_parquet(OUTPUT_DIR / "fact_hospitalizacion.parquet", index=False)
print(f"3c. fact_hospitalizacion.parquet  ({len(fact_hosp):,} filas)")

del df, otros, hosp

# =====================================================================
# 4. ESSALUD
# =====================================================================
print("\n4. Copiando EsSalud (perfil + costo proyectado)...")
perfil_e = pd.read_parquet(ESSALUD_DIR / "essalud_gcop_perfil.parquet")
costo_e = pd.read_parquet(ESSALUD_DIR / "essalud_gcop_costo_proyectado.parquet")
fact_essalud = perfil_e.merge(
    costo_e[["ID_ESSALUD_GCOP", "TRACK", "LOCALIZACION", "N_ATENCIONES", "COSTO_PROYECTADO_2024", "NIVEL_MATCH"]],
    on="ID_ESSALUD_GCOP", how="left", suffixes=("", "_track")
)
fact_essalud.to_parquet(OUTPUT_DIR / "fact_essalud_gcop.parquet", index=False)
print(f"   fact_essalud_gcop.parquet  ({len(fact_essalud):,} filas)")
print("   NOTA: COSTO_PROYECTADO_2024 ya viene resuelto (match contra benchmark FISSAL,")
print("   ver complementarios/essalud/03_costo_proyectado.py) -- no requiere DAX adicional.")

# Detalle a nivel de registro (no de paciente) -- necesario para "Especialidades
# mas frecuentes" y para la validacion de consistencia de CIE10 del ID compuesto,
# que fact_essalud_gcop (1 fila por paciente) no puede replicar.
g_detalle = pd.read_parquet(ESSALUD_DIR / "essalud_gcop_con_id.parquet")
fact_essalud_detalle = g_detalle[[
    "ID_ESSALUD_GCOP", "SERVICIO", "DIAGNOSTICO3", "FECHA_ATENCION", "RESULT_ATENCION", "TIPO_CONSULTA",
]].copy()
fact_essalud_detalle.to_parquet(OUTPUT_DIR / "fact_essalud_gcop_detalle.parquet", index=False)
print(f"   fact_essalud_gcop_detalle.parquet  ({len(fact_essalud_detalle):,} filas)")

# =====================================================================
# 5. SIS
# =====================================================================
print("\n5. Copiando SIS...")
sis_at = pd.read_parquet(SIS_DIR / "sis_atenciones.parquet")
sis_con = pd.read_parquet(SIS_DIR / "sis_consumos.parquet")
# FECHA_ATENCION llega como texto "dd/mm/aa" (ej. "16/12/24") -- convertir a
# fecha real antes de guardar, si no Power BI puede interpretarla ambiguo
# (dd/mm vs mm/dd segun la configuracion regional) o dejarla como texto.
sis_at["FECHA_ATENCION"] = pd.to_datetime(sis_at["FECHA_ATENCION"], format="%d/%m/%y", errors="coerce")
sis_at.to_parquet(OUTPUT_DIR / "fact_sis_atenciones.parquet", index=False)
sis_con.to_parquet(OUTPUT_DIR / "fact_sis_consumos.parquet", index=False)
print(f"   fact_sis_atenciones.parquet  ({len(sis_at):,} filas)")
print(f"   fact_sis_consumos.parquet  ({len(sis_con):,} filas)")

print(f"\nListo. Todo guardado en:\n  {OUTPUT_DIR}")
print("\nFin.")
