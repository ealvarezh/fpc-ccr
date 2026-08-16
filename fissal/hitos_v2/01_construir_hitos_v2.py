import pyodbc
import pandas as pd
import numpy as np
import unicodedata
from pathlib import Path
import gc

# =====================================================================
# CONFIGURACION
# =====================================================================
OUTPUT = Path(r"C:\Users\eah\apoyoconsultoria.com\File Server - Analytics\7 Datos\Datos abiertos\fissal\01_silver")
DICCIONARIO = r"C:\Users\eah\apoyoconsultoria.com\File Server - Analytics\3 Proyectos\2025\2025-116-L FPC Dashboard 25\4 Analisis\3 Programas\adicional 2026\diccionario_ATE_DESCCONSUMO_502_estandarizado.xlsx"
FECHA_CORTE = pd.Timestamp("2026-06-30")

print("=" * 70)
print("HITOS V2 — Construccion de hitos con SQL Server + Diccionario 502")
print("=" * 70)


# Clave normalizada para el join con el diccionario. Se aplica IDENTICA en
# ambos lados (diccionario y SQL) a partir del texto crudo -- ver seccion 1
# para por que no se usa la columna clave_normalizada que ya trae el excel.
def normalizar_clave(s):
    if pd.isna(s):
        return ""
    s = str(s).strip().upper()
    s = s.replace("  ", " ")
    s = s.replace("(", "").replace(")", "")
    s = s.replace(";", "").replace(",", "")  # quitar puntuacion
    s = s.replace('"', "").replace("'", "")   # quitar comillas
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")
    return s


# =====================================================================
# 1. CARGAR DICCIONARIO
# =====================================================================
print("\n1. Cargando diccionario de categorias...")
dic = pd.read_excel(DICCIONARIO)
# OJO: NO usamos la columna clave_normalizada que ya trae el excel. Esa
# columna se genero con una normalizacion propia del diccionario que no es
# identica a la de aca (ej.: "material(es)" -> "MATERIAL ES" alla vs.
# "MATERIALES" con un simple borrado de parentesis), lo que rompe el join
# para items que en realidad SI estan clasificados. Recalculamos la clave
# desde ATE_DESCCONSUMO (texto crudo) con normalizar_clave(), la MISMA
# funcion que se le aplica a Descripcion_Consumo del lado de SQL mas abajo,
# para garantizar que ambos lados usen exactamente la misma logica.
# Esto recupera ~89% del costo que antes quedaba "sin clasificar" por el
# desajuste de normalizacion (confirmado con 03_ampliar_diccionario.py).
dic["clave_normalizada"] = dic["ATE_DESCCONSUMO"].apply(normalizar_clave)
dic = dic[["clave_normalizada", "categoria_recurso_502", "subcategoria_recurso_502",
           "atribucion_crc_sugerida", "uso_sugerido_502"]].drop_duplicates(subset="clave_normalizada")
print(f"   {len(dic):,} items unicos en diccionario")

# =====================================================================
# 2. CONECTAR A SQL Y EXTRAER PACIENTES CCR
# =====================================================================
print("\n2. Extrayendo pacientes CCR de SQL Server...")
conn = pyodbc.connect(
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=localhost;"
    "DATABASE=Reporte_Transparencia;"
    "Trusted_Connection=yes;"
)

# Extraer TODOS los registros de pacientes CCR (cualquier CIE-10)
query_all = """
SELECT
    Codigo_identificacion_paciente,
    Codigo_sexo,
    Fecha_Nacimiento,
    Fecha_fallecimiento,
    Fecha_atencion,
    Fecha_ingreso_hospitalizacion,
    Fecha_alta_hospitalizacion,
    Tipo_atencion,
    Codigo_CIE10,
    Grupo_CIE10,
    Descripcion_CIE10,
    TipoConsumo,
    Descripcion_Consumo,
    MONTO_NETO,
    MONTO_BRUTO,
    Codigo_EESS,
    Nombre_EESS,
    Descripcio_servicio,
    Año_produccion,
    Mes_Produccion
FROM [Reporte_2016_2026_v1]
WHERE Codigo_identificacion_paciente IN (
    SELECT DISTINCT Codigo_identificacion_paciente
    FROM [Reporte_2016_2026_v1]
    WHERE Codigo_CIE10 LIKE 'C18%' OR Codigo_CIE10 LIKE 'C19%' OR Codigo_CIE10 LIKE 'C20%'
)
ORDER BY Codigo_identificacion_paciente, Fecha_atencion
"""
print("   Extrayendo TODOS los registros de pacientes CCR (cualquier CIE-10)...")
df = pd.read_sql(query_all, conn)
conn.close()

n_pac = df["Codigo_identificacion_paciente"].nunique()
n_ccr = df[df["Codigo_CIE10"].str.match(r"^C(18|19|20)", na=False)].shape[0]
print(f"   Registros totales: {len(df):,}")
print(f"   Registros CCR (C18/19/20): {n_ccr:,} ({n_ccr/len(df)*100:.1f}%)")
print(f"   Registros NO-CCR: {len(df)-n_ccr:,} ({(len(df)-n_ccr)/len(df)*100:.1f}%)")
print(f"   Pacientes unicos: {n_pac:,}")

# =====================================================================
# 3. LIMPIAR FECHAS Y CAMPOS
# =====================================================================
print("\n3. Limpiando fechas y campos...")
date_cols = ["Fecha_Nacimiento", "Fecha_fallecimiento", "Fecha_atencion",
             "Fecha_ingreso_hospitalizacion", "Fecha_alta_hospitalizacion"]
for col in date_cols:
    df[col] = pd.to_datetime(df[col], errors="coerce")

# Estandarizar clave para join con diccionario (normalizar_clave definida al inicio del archivo)
df["clave_normalizada"] = df["Descripcion_Consumo"].apply(normalizar_clave)

# Sexo
# Codigo_sexo llega como texto ('0'/'1'), no como entero (1/2) -- el mapeo
# anterior nunca matcheaba y todo quedaba en "U". Verificado empiricamente
# cruzando contra diagnosticos exclusivos de un sexo: de los pacientes con
# Codigo_sexo='0', 0 tienen cancer de prostata (C61x) y 844 tienen un cancer
# ginecologico (cervix/utero/ovario, C51/53/54/56x) -> '0'=Femenino. De los
# que tienen Codigo_sexo='1', 629 tienen cancer de prostata y solo 1 un
# diagnostico ginecologico -> '1'=Masculino.
df["SEXO"] = df["Codigo_sexo"].astype(str).str.strip().map({"0": "F", "1": "M"}).fillna("U")

# =====================================================================
# 4. JOIN CON DICCIONARIO PARA CATEGORIAS
# =====================================================================
print("\n4. Asignando categorias clinicas del diccionario...")
df = df.merge(dic, on="clave_normalizada", how="left")

# Items sin match en diccionario -> clasificar basico por TipoConsumo
sin_cat = df["categoria_recurso_502"].isna()
print(f"   Items sin categoria en diccionario: {sin_cat.sum():,} ({sin_cat.sum()/len(df)*100:.1f}%)")

# Mostrar ejemplos de lo que no matchea
if sin_cat.sum() > 0:
    ejemplos_sin = df.loc[sin_cat, "Descripcion_Consumo"].value_counts().head(10)
    print("   Ejemplos sin match:")
    for d, n in ejemplos_sin.items():
        print(f"      {n:>6,} | {str(d)[:120]}")

df.loc[sin_cat & (df["TipoConsumo"] == "Medicamento"), "categoria_recurso_502"] = "Medicamento no oncológico"
df.loc[sin_cat & (df["TipoConsumo"] == "Procedimiento"), "categoria_recurso_502"] = "Procedimiento no quirúrgico"
df.loc[sin_cat & (df["TipoConsumo"] == "Insumo"), "categoria_recurso_502"] = "Insumo médico"
df["categoria_recurso_502"] = df["categoria_recurso_502"].fillna("Sin clasificar")

# Atribucion CRC
df["atribucion_crc_sugerida"] = df["atribucion_crc_sugerida"].fillna("Revisar atribución")
df["uso_sugerido_502"] = df["uso_sugerido_502"].fillna("Revisar antes de análisis principal")

# Subconjunto de registros codificados especificamente como CCR (C18/19/20).
# Se usa solo para el diagnostico especifico de CCR y la localizacion del
# tumor; el "hito de ingreso" (seccion 6) usa el primer contacto general del
# paciente en FISSAL, sea cual sea el motivo (puede entrar por otra
# enfermedad y ser diagnosticado con CCR en paralelo o despues).
df_ccr = df[df["Codigo_CIE10"].str.match(r"^C(18|19|20)", na=False)]

# =====================================================================
# 5. CONSTRUIR PERFIL POR PACIENTE
# =====================================================================
print("\n5. Construyendo perfil por paciente...")

perfil = df.groupby("Codigo_identificacion_paciente", sort=False).agg(
    SEXO=("SEXO", "first"),
    FECHA_NACIMIENTO=("Fecha_Nacimiento", "first"),
    FECHA_FALLECIMIENTO=("Fecha_fallecimiento", "first"),
    PRIMERA_ATENCION=("Fecha_atencion", "min"),
    ULTIMA_ATENCION=("Fecha_atencion", "max"),
    N_ATENCIONES=("Fecha_atencion", "nunique"),  # proxy FUA count
    N_REGISTROS=("Fecha_atencion", "size"),
    PRIMER_ANIO=("Fecha_atencion", lambda x: x.min().year),
    ULTIMO_ANIO=("Fecha_atencion", lambda x: x.max().year),
    MONTO_NETO_TOTAL=("MONTO_NETO", "sum"),
    MONTO_BRUTO_TOTAL=("MONTO_BRUTO", "sum"),
).reset_index()

# Fecha de diagnostico CCR: primera atencion codificada especificamente como
# C18/19/20 (distinta de PRIMERA_ATENCION, que puede ser una atencion previa
# por otro motivo subsidiado por FISSAL). Todo paciente en esta cohorte tiene
# al menos un registro CCR por construccion de la query, asi que no deberia
# quedar NaT. Se usa para edad/supervivencia (estandar clinico: al Dx), NO
# para el hito de ingreso (que es general, ver seccion 6).
fecha_dx_ccr = df_ccr.groupby("Codigo_identificacion_paciente")["Fecha_atencion"].min()
perfil["FECHA_DIAGNOSTICO_CCR"] = perfil["Codigo_identificacion_paciente"].map(fecha_dx_ccr)

# Edad (al diagnostico de CCR, no al primer contacto por cualquier motivo)
perfil["EDAD_PRIMERA_ATENCION"] = np.floor(
    (perfil["FECHA_DIAGNOSTICO_CCR"] - perfil["FECHA_NACIMIENTO"]).dt.days / 365.25
)
# Filtrar outliers
perfil.loc[(perfil["EDAD_PRIMERA_ATENCION"] < 10) | (perfil["EDAD_PRIMERA_ATENCION"] > 100), "EDAD_PRIMERA_ATENCION"] = pd.NA

perfil["FALLECIDO"] = perfil["FECHA_FALLECIMIENTO"].notna()

# Fecha_fallecimiento = 1900-01-01 es un valor centinela: el paciente SI
# fallecio pero no se conserva la fecha exacta (confirmado por el usuario).
# Se distingue con un flag, y para cualquier calculo de tiempo se usa como
# proxy la fecha de ultima atencion (ultimo contacto conocido) en vez de la
# fecha centinela, que arrastraria supervivencias absurdas (negativas, de
# decenas de miles de dias).
perfil["FECHA_FALLECIMIENTO_EXACTA"] = perfil["FALLECIDO"] & (perfil["FECHA_FALLECIMIENTO"].dt.year > 1900)
perfil["FECHA_FALLECIMIENTO_EFECTIVA"] = pd.to_datetime(np.where(
    perfil["FECHA_FALLECIMIENTO_EXACTA"],
    perfil["FECHA_FALLECIMIENTO"],
    perfil["ULTIMA_ATENCION"],
))
n_centinela = (perfil["FALLECIDO"] & ~perfil["FECHA_FALLECIMIENTO_EXACTA"]).sum()
print(f"   Fallecidos con fecha centinela (1900-01-01, fecha exacta desconocida): {n_centinela:,} "
      f"de {perfil['FALLECIDO'].sum():,} fallecidos -> se usa ULTIMA_ATENCION como proxy de cierre")

# Supervivencia (desde el diagnostico de CCR, no desde el primer contacto por cualquier motivo)
perfil["SUPERVIVENCIA_DIAS"] = np.where(
    perfil["FALLECIDO"],
    (perfil["FECHA_FALLECIMIENTO_EFECTIVA"] - perfil["FECHA_DIAGNOSTICO_CCR"]).dt.days,
    (FECHA_CORTE - perfil["FECHA_DIAGNOSTICO_CCR"]).dt.days,
)
perfil["TIEMPO_EN_SISTEMA_DIAS"] = (perfil["ULTIMA_ATENCION"] - perfil["PRIMERA_ATENCION"]).dt.days

# Rango de edad
bins_edad = [0, 18, 30, 40, 50, 60, 70, 80, 101]
labels_edad = ["0-17", "18-29", "30-39", "40-49", "50-59", "60-69", "70-79", "80+"]
perfil["RANGO_EDAD"] = pd.cut(perfil["EDAD_PRIMERA_ATENCION"], bins=bins_edad, labels=labels_edad, right=False)

print(f"   Pacientes en perfil: {len(perfil):,}")

# =====================================================================
# 6. HITO 1: INGRESO
# =====================================================================
print("\n6. HITO 1: INGRESO")

# Tipo de ingreso: primer contacto del paciente en FISSAL, por cualquier
# motivo subsidiado (no necesariamente CCR: puede entrar por otra condicion
# y ser diagnosticado con CCR en paralelo o despues de cursar ese otro mal).
primer_reg = df.sort_values("Fecha_atencion").groupby("Codigo_identificacion_paciente").first()
ingreso = primer_reg[["Tipo_atencion", "Nombre_EESS", "Codigo_CIE10", "Grupo_CIE10"]].reset_index()
ingreso.columns = ["Codigo_identificacion_paciente", "TIPO_INGRESO", "IPRESS_INGRESO",
                   "CIE10_INGRESO", "GRUPO_CIE10_INGRESO"]

# Localizacion del tumor: a diferencia del ingreso (que puede ser por
# cualquier motivo), esto describe el sitio del cancer, asi que se deriva del
# primer registro codificado especificamente como CCR (df_ccr), no del primer
# contacto general.
primer_reg_ccr = df_ccr.sort_values("Fecha_atencion").groupby("Codigo_identificacion_paciente").first()
localizacion = primer_reg_ccr["Codigo_CIE10"].str[:3].map({
    "C18": "Colon", "C19": "Union rectosigmoidea", "C20": "Recto"
}).rename("LOCALIZACION").reset_index()
ingreso = ingreso.merge(localizacion, on="Codigo_identificacion_paciente", how="left")

# Proxy de gravedad al ingreso: fue hospitalizado o emergencia en su primer
# contacto con el sistema (mismo recorte general de "ingreso" de arriba)
ingreso["INGRESO_GRAVE"] = (
    ingreso["TIPO_INGRESO"].str.contains("EMERG", case=False, na=False)
    | (df.groupby("Codigo_identificacion_paciente")["Fecha_ingreso_hospitalizacion"].first().notna()
       .reindex(ingreso["Codigo_identificacion_paciente"]).fillna(False).values)
)

hitos = ingreso.copy()

# =====================================================================
# 7. HITO 2: INTERVENCION (con categorias del diccionario)
# =====================================================================
print("7. HITO 2: INTERVENCION")

# Agrupar categorias del diccionario por paciente
cats_pac = df.groupby("Codigo_identificacion_paciente")["categoria_recurso_502"].apply(
    lambda x: dict(x.value_counts())
).reset_index(name="CONTEO_CATEGORIAS")

# Flags de tratamiento (usando categorias del diccionario, no regex!)
TRAT_CATS = [
    "Procedimiento quirúrgico",
    "Medicamento oncológico",
    "Radioterapia",
    "Endoscopía / colonoscopía",
]
SOPORTE_CATS = [
    "Medicamento no oncológico",
    "Laboratorio",
    "Imagenología",
    "Transfusión / banco de sangre",
    "Anatomía patológica / biopsia",
    "Procedimiento no quirúrgico",
    "Consulta / evaluación",
    "Insumo médico",
    "Dispositivo médico",
    "Hospitalización / estancia",
    "Rehabilitación / terapia",
    "Cuidados paliativos",
    "Emergencia",
]

# Flags booleanos por categoria
for cat in TRAT_CATS + SOPORTE_CATS:
    col_name = "TIENE_" + cat.replace(" / ", "_").replace(" ", "_").replace("ó", "o").upper()
    pacs_con_cat = df[df["categoria_recurso_502"] == cat]["Codigo_identificacion_paciente"].unique()
    hitos[col_name] = hitos["Codigo_identificacion_paciente"].isin(pacs_con_cat)

# Fechas de inicio/fin por modalidad
for cat in TRAT_CATS:
    col_fecha = cat.replace(" / ", "_").replace(" ", "_").replace("ó", "o")
    sub = df[df["categoria_recurso_502"] == cat]
    fechas = sub.groupby("Codigo_identificacion_paciente")["Fecha_atencion"].agg(
        **{f"INICIO_{col_fecha}": "min", f"FIN_{col_fecha}": "max", f"N_SESIONES_{col_fecha}": "nunique"}
    ).reset_index()
    hitos = hitos.merge(fechas, on="Codigo_identificacion_paciente", how="left")

# Track: A (completo) vs B (parcial)
cols_trat = [f"TIENE_{c.replace(' / ', '_').replace(' ', '_').replace('ó', 'o').upper()}" for c in TRAT_CATS]
hitos["TIENE_TRATAMIENTO_ONCOLOGICO"] = hitos[cols_trat].any(axis=1)

# Fecha inicio/fin intervencion
cols_inicio = [f"INICIO_{c.replace(' / ', '_').replace(' ', '_').replace('ó', 'o')}" for c in TRAT_CATS]
cols_fin = [f"FIN_{c.replace(' / ', '_').replace(' ', '_').replace('ó', 'o')}" for c in TRAT_CATS]
hitos["FECHA_INICIO_INTERVENCION"] = hitos[cols_inicio].min(axis=1)
hitos["FECHA_FIN_INTERVENCION"] = hitos[cols_fin].max(axis=1)

# Track A vs B
hitos["TRACK"] = np.where(hitos["TIENE_TRATAMIENTO_ONCOLOGICO"], "A_COMPLETO", "B_PARCIAL")

# =====================================================================
# 8. COSTOS POR ATRIBUCION CRC
# =====================================================================
print("8. Calculando costos por atribucion CRC...")

# Costo total en ventana de intervencion (solo items CRC-atribuibles o soporte)
df["ES_CRC_ATRIBUIBLE"] = df["atribucion_crc_sugerida"] == "Atribuible/compatible con manejo de CRC"
df["ES_SOPORTE"] = df["atribucion_crc_sugerida"] == "Soporte del episodio de atención oncológica"
df["ES_INCLUIBLE"] = df["uso_sugerido_502"].str.contains("Incluir", na=False)

costo_atrib = df.groupby("Codigo_identificacion_paciente").agg(
    COSTO_CRC_ATRIBUIBLE=("MONTO_NETO", lambda x: x[df.loc[x.index, "ES_CRC_ATRIBUIBLE"]].sum()),
    COSTO_SOPORTE=("MONTO_NETO", lambda x: x[df.loc[x.index, "ES_SOPORTE"]].sum()),
    COSTO_NO_ATRIBUIBLE=("MONTO_NETO", lambda x: x[~(df.loc[x.index, "ES_CRC_ATRIBUIBLE"] | df.loc[x.index, "ES_SOPORTE"])].sum()),
).reset_index()

for c in ["COSTO_CRC_ATRIBUIBLE", "COSTO_SOPORTE", "COSTO_NO_ATRIBUIBLE"]:
    costo_atrib[c] = costo_atrib[c].fillna(0)

hitos = hitos.merge(costo_atrib, on="Codigo_identificacion_paciente", how="left")

# Costo por año (pivot para ver evolucion)
costo_anual = df.groupby(["Codigo_identificacion_paciente", df["Fecha_atencion"].dt.year])["MONTO_NETO"].sum().unstack(fill_value=0)
costo_anual.columns = [f"COSTO_{int(c)}" for c in costo_anual.columns]
hitos = hitos.merge(costo_anual, on="Codigo_identificacion_paciente", how="left")

# Mismo costo por año pero desglosado por bucket de atribucion (para poder
# deflactar CRC_ATRIBUIBLE/SOPORTE/NO_ATRIBUIBLE año a año en vez de aplicar
# un factor IPC promedio plano sobre el total nominal)
df["BUCKET_ATRIB"] = np.select(
    [df["ES_CRC_ATRIBUIBLE"], df["ES_SOPORTE"]],
    ["CRC_ATRIBUIBLE", "SOPORTE"],
    default="NO_ATRIBUIBLE",
)
for bucket, prefijo in [("CRC_ATRIBUIBLE", "COSTO_CRC_ATRIBUIBLE"),
                         ("SOPORTE", "COSTO_SOPORTE"),
                         ("NO_ATRIBUIBLE", "COSTO_NO_ATRIBUIBLE")]:
    sub = df[df["BUCKET_ATRIB"] == bucket]
    piv = sub.groupby(["Codigo_identificacion_paciente", sub["Fecha_atencion"].dt.year])["MONTO_NETO"].sum().unstack(fill_value=0)
    piv.columns = [f"{prefijo}_{int(c)}" for c in piv.columns]
    hitos = hitos.merge(piv, on="Codigo_identificacion_paciente", how="left")
    hitos[piv.columns] = hitos[piv.columns].fillna(0)

# =====================================================================
# 9. HITO 3: CIERRE
# =====================================================================
print("9. HITO 3: CIERRE")

# Agregar columnas del perfil que hacen falta
perfil_cols = ["Codigo_identificacion_paciente", "SEXO", "EDAD_PRIMERA_ATENCION", "RANGO_EDAD",
               "SUPERVIVENCIA_DIAS", "PRIMERA_ATENCION", "FECHA_DIAGNOSTICO_CCR", "ULTIMA_ATENCION",
               "FECHA_FALLECIMIENTO", "FECHA_FALLECIMIENTO_EXACTA", "FECHA_FALLECIMIENTO_EFECTIVA",
               "FALLECIDO", "N_ATENCIONES", "TIEMPO_EN_SISTEMA_DIAS", "MONTO_NETO_TOTAL"]
hitos = hitos.merge(perfil[perfil_cols], on="Codigo_identificacion_paciente", how="left")

hitos["DIAS_DESDE_ULTIMA_ATENCION"] = (FECHA_CORTE - hitos["ULTIMA_ATENCION"]).dt.days

UMBRAL_SIN_SEGUIMIENTO = 540  # 18 meses

# Filtros para FISSAL-real (>=3 atenciones + no outlier + >=1 dia)
# Outliers de costo: IQR por grupo de atenciones
hitos_temp = hitos.copy()
hitos_temp["ES_OUTLIER"] = False
for n_at in sorted(hitos_temp["N_ATENCIONES"].unique()):
    if n_at < 5:
        continue
    grupo = hitos_temp.loc[hitos_temp["N_ATENCIONES"] == n_at, "MONTO_NETO_TOTAL"]
    if len(grupo) < 5:
        continue
    q1, q3 = grupo.quantile(0.25), grupo.quantile(0.75)
    limite = q3 + 3 * (q3 - q1)
    mask = (hitos_temp["N_ATENCIONES"] == n_at) & (hitos_temp["MONTO_NETO_TOTAL"] > limite)
    hitos_temp.loc[mask, "ES_OUTLIER"] = True

hitos["ES_OUTLIER_COSTO"] = hitos_temp["ES_OUTLIER"]
hitos["FISSAL_REGULAR"] = (
    (hitos["N_ATENCIONES"] >= 3)
    & (~hitos["ES_OUTLIER_COSTO"])
    & (hitos["TIEMPO_EN_SISTEMA_DIAS"] >= 1)
)

def clasificar_cierre(row):
    if row["FALLECIDO"]:
        return "FALLECIDO"
    if row.get("TIENE_CUIDADOS_PALIATIVOS", False):
        return "PALIATIVO"
    if row["DIAS_DESDE_ULTIMA_ATENCION"] >= UMBRAL_SIN_SEGUIMIENTO:
        return "POSIBLE_REMISION_O_ALTA"
    if row["DIAS_DESDE_ULTIMA_ATENCION"] < UMBRAL_SIN_SEGUIMIENTO:
        return "EN_SEGUIMIENTO_ACTIVO"
    return "INDETERMINADO"

hitos["CIERRE"] = hitos.apply(clasificar_cierre, axis=1)

# Fecha de cierre (para fallecidos con fecha centinela, FECHA_FALLECIMIENTO_EFECTIVA
# ya cae en ULTIMA_ATENCION como proxy; ver seccion 5)
hitos["FECHA_CIERRE"] = np.where(
    hitos["FALLECIDO"],
    hitos["FECHA_FALLECIMIENTO_EFECTIVA"],
    hitos["ULTIMA_ATENCION"]
)

# =====================================================================
# 10. TIEMPOS ENTRE HITOS
# =====================================================================
print("10. Calculando tiempos entre hitos...")

hitos["DIAS_INGRESO_A_INTERVENCION"] = (
    hitos["FECHA_INICIO_INTERVENCION"] - hitos["FECHA_DIAGNOSTICO_CCR"]
).dt.days

hitos["DIAS_INTERVENCION_A_CIERRE"] = np.where(
    hitos["FECHA_FIN_INTERVENCION"].notna(),
    (hitos["FECHA_CIERRE"] - hitos["FECHA_FIN_INTERVENCION"]).dt.days,
    np.nan
)

hitos["DIAS_TRAYECTORIA_TOTAL"] = (
    hitos["FECHA_CIERRE"] - hitos["PRIMERA_ATENCION"]
).dt.days

# =====================================================================
# 11. HOSPITALIZACIONES
# =====================================================================
print("11. Contando hospitalizaciones (por fecha de ingreso, no por Tipo_atencion)...")

# La hospitalizacion se detecta por Fecha_ingreso_hospitalizacion != null
# (el Tipo_atencion en este SQL no tiene valor HOSPITALIZACION, solo EMERGENCIA/AMBULATORIO/REFERIDO)
hosp = df[df["Fecha_ingreso_hospitalizacion"].notna()].copy()

# Cada hospitalizacion genera varias lineas de consumo (medicamentos, insumos,
# procedimientos) que comparten las mismas fechas de ingreso/alta. Hay que
# colapsar a nivel de episodio ANTES de sumar dias o contar hospitalizaciones,
# si no, se multiplica la estancia y el conteo por el numero de items facturados.
hosp_ep = hosp.groupby(
    ["Codigo_identificacion_paciente", "Fecha_ingreso_hospitalizacion", "Fecha_alta_hospitalizacion"],
    dropna=False,
).size().reset_index(name="N_LINEAS")
hosp_ep["DIAS_ESTANCIA"] = (hosp_ep["Fecha_alta_hospitalizacion"] - hosp_ep["Fecha_ingreso_hospitalizacion"]).dt.days
hosp_ep["DIAS_ESTANCIA"] = hosp_ep["DIAS_ESTANCIA"].where((hosp_ep["DIAS_ESTANCIA"] >= 0) & (hosp_ep["DIAS_ESTANCIA"] <= 365), pd.NA)

hosp_pac = hosp_ep.groupby("Codigo_identificacion_paciente").agg(
    N_HOSPITALIZACIONES=("N_LINEAS", "size"),
    DIAS_HOSPITALIZACION_TOTAL=("DIAS_ESTANCIA", "sum"),
).reset_index()

hitos = hitos.merge(hosp_pac, on="Codigo_identificacion_paciente", how="left")
hitos["N_HOSPITALIZACIONES"] = hitos["N_HOSPITALIZACIONES"].fillna(0).astype(int)
hitos["DIAS_HOSPITALIZACION_TOTAL"] = hitos["DIAS_HOSPITALIZACION_TOTAL"].fillna(0)

# =====================================================================
# 12. RESUMEN FINAL Y GUARDADO
# =====================================================================
print("\n" + "=" * 70)
print("12. RESUMEN FINAL")
print("=" * 70)

print(f"\n  Pacientes totales:                  {len(hitos):,}")
print(f"  Fallecidos:                         {hitos['FALLECIDO'].sum():,} ({hitos['FALLECIDO'].mean()*100:.1f}%)")
print(f"  Track A (tratamiento completo):     {(hitos['TRACK']=='A_COMPLETO').sum():,}")
print(f"  Track B (intervencion parcial):     {(hitos['TRACK']=='B_PARCIAL').sum():,}")
print(f"  FISSAL regular (>=3 aten):          {hitos['FISSAL_REGULAR'].sum():,}")
print(f"  Outliers costo:                     {hitos['ES_OUTLIER_COSTO'].sum():,}")

print(f"\n  --- Costos (todos los pacientes) ---")
print(f"  MONTO_NETO_TOTAL (mediana):         S/ {hitos['MONTO_NETO_TOTAL'].median():>10,.0f}")
print(f"  COSTO_CRC_ATRIBUIBLE (mediana):     S/ {hitos['COSTO_CRC_ATRIBUIBLE'].median():>10,.0f}")
print(f"  COSTO_SOPORTE (mediana):            S/ {hitos['COSTO_SOPORTE'].median():>10,.0f}")

track_a = hitos[hitos["TRACK"] == "A_COMPLETO"]
track_a_reg = track_a[track_a["FISSAL_REGULAR"]]
print(f"\n  --- Track A COMPLETO + FISSAL regular (n={len(track_a_reg):,}) ---")
print(f"  Costo neto total (mediana):         S/ {track_a_reg['MONTO_NETO_TOTAL'].median():>10,.0f}")
print(f"  Costo neto total (media):           S/ {track_a_reg['MONTO_NETO_TOTAL'].mean():>10,.0f}")
print(f"  Costo CRC atribuible (mediana):     S/ {track_a_reg['COSTO_CRC_ATRIBUIBLE'].median():>10,.0f}")
print(f"  Costo soporte (mediana):            S/ {track_a_reg['COSTO_SOPORTE'].median():>10,.0f}")

# Guardar
salida = OUTPUT / "FISSAL_CCR_HITOS_V2.parquet"
hitos.to_parquet(salida, index=False)
print(f"\n  Guardado: {salida}")
print(f"  Columnas: {hitos.shape[1]}")
print("\nFin de construccion de hitos v2.")
