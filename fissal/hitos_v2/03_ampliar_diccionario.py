"""
Genera una PROPUESTA de ampliacion del diccionario de categorias (502) para los
items de consumo que hoy no matchean (quedan "Revisar atribucion" / sin
categoria). Prioriza por impacto en costo, y sugiere categoria/subcategoria/
atribucion/uso por similitud textual contra los items YA clasificados del
diccionario (mismo criterio que se uso para expandir el diccionario original,
a juzgar por las columnas confianza_auto/prioridad_revision/comentario_revision
que ya trae el archivo).

Esto NO modifica el diccionario maestro. Escribe un Excel de revision; una vez
que alguien valide/corrija las sugerencias, esas filas se pueden pegar/appendear
al diccionario maestro (mismas columnas) para que 01_construir_hitos_v2.py las
reconozca en la proxima corrida.

Uso:
    python 03_ampliar_diccionario.py
"""
import pyodbc
import pandas as pd
import numpy as np
import unicodedata
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import NearestNeighbors

DICCIONARIO = r"C:\Users\eah\apoyoconsultoria.com\File Server - Analytics\3 Proyectos\2025\2025-116-L FPC Dashboard 25\4 Analisis\3 Programas\adicional 2026\diccionario_ATE_DESCCONSUMO_502_estandarizado.xlsx"
SALIDA = Path(r"C:\estela\github\fpc-ccr\output")
SALIDA.mkdir(parents=True, exist_ok=True)
EXCEL_OUT = SALIDA / "propuesta_ampliacion_diccionario.xlsx"

# Umbrales de similitud (coseno sobre TF-IDF de n-gramas de caracteres) para
# la confianza automatica. Se calibraron para que la distribucion resultante
# se parezca a la que ya tiene el diccionario (Alta ~80%, Media ~13%, Baja ~7%).
UMBRAL_ALTA = 0.75
UMBRAL_MEDIA = 0.50

print("=" * 70)
print("Propuesta de ampliacion del diccionario 502")
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
# 1. CARGAR DICCIONARIO ACTUAL
# =====================================================================
print("\n1. Cargando diccionario actual...")
dic_full = pd.read_excel(DICCIONARIO)
# Recalculamos la clave desde ATE_DESCCONSUMO (texto crudo) en vez de usar la
# columna clave_normalizada del excel: esa se genero con una normalizacion
# distinta a normalizar_clave() y rompe el join para items que en realidad SI
# estan clasificados (ej. "material(es)" -> "MATERIAL ES" alla vs "MATERIALES"
# aca). Con esto, ~89% del costo que antes parecia "sin clasificar" en
# realidad si tenia match -- solo el resto es un gap real de cobertura.
dic_full["clave_normalizada"] = dic_full["ATE_DESCCONSUMO"].apply(normalizar_clave)
dic = dic_full.drop_duplicates(subset="clave_normalizada").copy()
print(f"   {len(dic_full):,} filas totales, {len(dic):,} claves unicas")

# =====================================================================
# 2. EXTRAER CONSUMO DE LA COHORTE CCR AGRUPADO (mismo universo que 01_construir_hitos_v2.py)
# =====================================================================
print("\n2. Extrayendo consumo agregado de la cohorte CCR desde SQL Server...")
conn = pyodbc.connect(
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=localhost;"
    "DATABASE=Reporte_Transparencia;"
    "Trusted_Connection=yes;"
)
query = """
SELECT Descripcion_Consumo, TipoConsumo, Codigo_Consumo, Descripcio_servicio,
       COUNT(*) AS n_registros,
       COUNT(DISTINCT Codigo_identificacion_paciente) AS n_pacientes,
       SUM(MONTO_NETO) AS costo_total
FROM [Reporte_2016_2026_v1]
WHERE Codigo_identificacion_paciente IN (
    SELECT DISTINCT Codigo_identificacion_paciente
    FROM [Reporte_2016_2026_v1]
    WHERE Codigo_CIE10 LIKE 'C18%' OR Codigo_CIE10 LIKE 'C19%' OR Codigo_CIE10 LIKE 'C20%'
)
GROUP BY Descripcion_Consumo, TipoConsumo, Codigo_Consumo, Descripcio_servicio
"""
consumo = pd.read_sql(query, conn)
conn.close()
print(f"   Combinaciones (descripcion x consumo x servicio): {len(consumo):,}")

consumo["clave_normalizada"] = consumo["Descripcion_Consumo"].apply(normalizar_clave)

# Colapsar a nivel de clave_normalizada (una fila por item de consumo unico)
def moda_ponderada(sub, col_valor, col_peso):
    return sub.loc[sub[col_peso].idxmax(), col_valor]

grp = consumo.groupby("clave_normalizada", sort=False)
items = grp.agg(
    ATE_DESCCONSUMO=("Descripcion_Consumo", lambda x: x.iloc[0]),
    tipo_consumo_fuente=("TipoConsumo", lambda x: x.mode().iloc[0] if not x.mode().empty else x.iloc[0]),
    n_registros=("n_registros", "sum"),
    n_pacientes=("n_pacientes", "max"),  # aproximado: no se puede sumar sin duplicar pacientes entre variantes
    costo_total=("costo_total", "sum"),
).reset_index()

# Codigo de consumo y servicio mas frecuentes por clave (por n_registros)
cod_top = consumo.sort_values("n_registros", ascending=False).drop_duplicates("clave_normalizada")
items = items.merge(
    cod_top[["clave_normalizada", "Codigo_Consumo", "Descripcio_servicio"]]
    .rename(columns={"Codigo_Consumo": "codconsumo_mas_frecuente", "Descripcio_servicio": "servicio_mas_frecuente"}),
    on="clave_normalizada", how="left",
)
n_cod = consumo.groupby("clave_normalizada")["Codigo_Consumo"].nunique().rename("n_codconsumo")
items = items.merge(n_cod, on="clave_normalizada", how="left")

print(f"   Items unicos (por clave_normalizada) en la cohorte CCR: {len(items):,}")

# =====================================================================
# 3. IDENTIFICAR ITEMS SIN MATCH EN EL DICCIONARIO
# =====================================================================
print("\n3. Identificando items sin match...")
matched_keys = set(dic["clave_normalizada"])
nuevos = items[~items["clave_normalizada"].isin(matched_keys)].copy()
nuevos = nuevos.sort_values("costo_total", ascending=False).reset_index(drop=True)

costo_total_cohorte = items["costo_total"].sum()
costo_gap = nuevos["costo_total"].sum()
print(f"   Items sin clasificar: {len(nuevos):,} de {len(items):,} ({len(nuevos)/len(items)*100:.1f}%)")
print(f"   Costo de esos items: S/ {costo_gap:,.0f} ({costo_gap/costo_total_cohorte*100:.1f}% del costo total de la cohorte)")

nuevos["pct_acumulado_costo"] = (nuevos["costo_total"].cumsum() / costo_gap).round(4)
for umbral in [0.5, 0.8, 0.9, 0.95]:
    n_items = (nuevos["pct_acumulado_costo"] <= umbral).sum() + 1
    print(f"   Revisando los {n_items:,} items mas costosos se cubre el {umbral*100:.0f}% del costo sin clasificar")

# =====================================================================
# 4. SUGERIR CATEGORIA POR SIMILITUD TEXTUAL (TF-IDF de n-gramas + vecino mas cercano)
# =====================================================================
print("\n4. Sugiriendo categoria por similitud textual contra el diccionario ya clasificado...")

vec = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), min_df=1)
X_dic = vec.fit_transform(dic["clave_normalizada"])
X_nuevos = vec.transform(nuevos["clave_normalizada"])

nn = NearestNeighbors(n_neighbors=1, metric="cosine")
nn.fit(X_dic)
dist, idx = nn.kneighbors(X_nuevos)
similitud = (1 - dist.ravel()).clip(0, 1)
match_idx = idx.ravel()

cols_dic = ["ATE_DESCCONSUMO", "categoria_recurso_502", "subcategoria_recurso_502",
            "atribucion_crc_sugerida", "uso_sugerido_502"]
match_ref = dic.iloc[match_idx][cols_dic].reset_index(drop=True)
match_ref.columns = ["match_referencia_desc", "categoria_recurso_502", "subcategoria_recurso_502",
                      "atribucion_crc_sugerida", "uso_sugerido_502"]

nuevos["similitud"] = similitud.round(3)
for c in match_ref.columns:
    nuevos[c] = match_ref[c].values

nuevos["confianza_auto"] = np.select(
    [nuevos["similitud"] >= UMBRAL_ALTA, nuevos["similitud"] >= UMBRAL_MEDIA],
    ["Alta", "Media"], default="Baja",
)
nuevos["prioridad_revision"] = np.select(
    [nuevos["similitud"] >= UMBRAL_ALTA, nuevos["similitud"] >= UMBRAL_MEDIA],
    ["Baja", "Media"], default="Alta",
)
nuevos["comentario_revision"] = (
    "Item nuevo detectado en cohorte CCR (no estaba en diccionario). Clasificado por "
    "similitud textual con '" + nuevos["match_referencia_desc"].astype(str) + "' (similitud="
    + nuevos["similitud"].round(2).astype(str) + "). Pendiente de validacion manual."
)

print(f"   Confianza automatica sugerida: {dict(nuevos['confianza_auto'].value_counts())}")

sin_sugerencia_confiable = nuevos[nuevos["similitud"] < UMBRAL_MEDIA]
print(f"   Items sin match razonable (similitud<{UMBRAL_MEDIA}), requieren categorizacion 100% manual: "
      f"{len(sin_sugerencia_confiable):,} (costo S/ {sin_sugerencia_confiable['costo_total'].sum():,.0f})")

# =====================================================================
# 5. ARMAR TABLA DE SALIDA (mismo esquema que el diccionario maestro + columnas de impacto)
# =====================================================================
nuevos["descconsumo_estandar"] = nuevos["ATE_DESCCONSUMO"]
nuevos["count"] = nuevos["n_registros"]
nuevos["monto_neto_total"] = nuevos["costo_total"]
nuevos["n_lineas_parquet"] = nuevos["n_registros"]
nuevos["categoria_final"] = ""       # para que la persona que revise corrija si hace falta
nuevos["subcategoria_final"] = ""
nuevos["atribucion_final"] = ""
nuevos["uso_final"] = ""
nuevos["aprobado"] = ""              # marcar SI/NO tras revisar

cols_salida = [
    "clave_normalizada", "ATE_DESCCONSUMO", "descconsumo_estandar", "tipo_consumo_fuente",
    "n_registros", "n_pacientes", "costo_total", "pct_acumulado_costo",
    "similitud", "match_referencia_desc",
    "categoria_recurso_502", "subcategoria_recurso_502", "atribucion_crc_sugerida", "uso_sugerido_502",
    "confianza_auto", "prioridad_revision", "comentario_revision",
    "categoria_final", "subcategoria_final", "atribucion_final", "uso_final", "aprobado",
    "count", "codconsumo_mas_frecuente", "n_codconsumo", "servicio_mas_frecuente",
    "n_lineas_parquet", "monto_neto_total",
]
salida = nuevos[cols_salida].copy()

resumen = pd.DataFrame([
    ["Items unicos en la cohorte CCR", len(items), ""],
    ["Items ya clasificados en diccionario", len(items) - len(nuevos), ""],
    ["Items SIN clasificar (esta propuesta)", len(nuevos), f"{len(nuevos)/len(items)*100:.1f}% de los items"],
    ["Costo total cohorte CCR", round(costo_total_cohorte, 0), "Soles nominales"],
    ["Costo de items sin clasificar (gap)", round(costo_gap, 0), f"{costo_gap/costo_total_cohorte*100:.1f}% del costo total"],
    ["Items con sugerencia Alta confianza", (nuevos["confianza_auto"] == "Alta").sum(), "similitud >= " + str(UMBRAL_ALTA)],
    ["Items con sugerencia Media confianza", (nuevos["confianza_auto"] == "Media").sum(), f"{UMBRAL_MEDIA} <= similitud < {UMBRAL_ALTA}"],
    ["Items con sugerencia Baja confianza / manual", (nuevos["confianza_auto"] == "Baja").sum(), f"similitud < {UMBRAL_MEDIA}"],
], columns=["Metrica", "Valor", "Nota"])

print("\n5. Escribiendo Excel de revision...")
with pd.ExcelWriter(EXCEL_OUT, engine="openpyxl") as writer:
    resumen.to_excel(writer, sheet_name="0_Resumen", index=False)
    salida.to_excel(writer, sheet_name="1_Propuesta_ordenada_x_costo", index=False)

print(f"\nListo: {EXCEL_OUT}")
print("""
Como usarlo:
  1. Abrir la hoja '1_Propuesta_ordenada_x_costo' (ya viene ordenada de mayor a
     menor costo, con pct_acumulado_costo para saber cuanto del gap cubres).
  2. Revisar categoria_recurso_502 / subcategoria_recurso_502 / atribucion_crc_sugerida /
     uso_sugerido_502 (columnas sugeridas por similitud). Si estan bien, no hace
     falta tocar nada. Si hay que corregir, llenar las columnas *_final
     correspondientes y marcar 'aprobado' = SI.
  3. Priorizar por confianza_auto=Baja y prioridad_revision=Alta primero (son los
     que el modelo de similitud no supo ubicar bien), y por costo_total /
     pct_acumulado_costo para maximizar cobertura con el menor esfuerzo.
  4. Una vez revisado: tomar las filas aprobadas, quedarse con las columnas del
     esquema del diccionario maestro (ATE_DESCCONSUMO, count, descconsumo_estandar,
     categoria_recurso_502, subcategoria_recurso_502, atribucion_crc_sugerida,
     uso_sugerido_502, confianza_auto, prioridad_revision, comentario_revision,
     tipo_consumo_fuente, codconsumo_mas_frecuente, n_codconsumo,
     servicio_mas_frecuente, n_lineas_parquet, monto_neto_total,
     clave_normalizada — usando los valores *_final donde se corrigieron) y
     pegarlas al final de diccionario_ATE_DESCCONSUMO_502_estandarizado.xlsx.
  5. Volver a correr 01_construir_hitos_v2.py y 02_reporte_excel.py.
""")
