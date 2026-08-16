"""
Arma dashboard/index.html a partir de:
  - output/FISSAL_CCR_Analisis_Completo.xlsx (fissal/hitos_v2/02_reporte_excel.py)
  - complementarios/essalud/output/*.parquet
  - complementarios/sis/output/*.parquet

Lee dashboard/template.html (contiene el placeholder __DASHBOARD_DATA__),
inyecta un JSON con todos los datos, y escribe dashboard/index.html — un
archivo HTML autocontenido (sin dependencias externas) que se puede abrir
directamente en el navegador.

Volver a correr este script cada vez que se actualicen los datos fuente.
"""
import json
import math
import pandas as pd
from pathlib import Path

REPO = Path(r"C:\estela\github\fpc-ccr")
FISSAL_XLSX = REPO / "output" / "FISSAL_CCR_Analisis_Completo.xlsx"
ESSALUD_DIR = REPO / "complementarios" / "essalud" / "output"
SIS_DIR = REPO / "complementarios" / "sis" / "output"
DASHBOARD_DIR = REPO / "dashboard"

print("Cargando FISSAL...")
xl = pd.ExcelFile(FISSAL_XLSX)


def clean(v):
    if isinstance(v, float) and math.isnan(v):
        return None
    if isinstance(v, (pd.Timestamp,)):
        return str(v)
    return v


def records(df):
    return [{k: clean(v) for k, v in row.items()} for row in df.to_dict(orient="records")]


resumen_df = pd.read_excel(xl, "1_Resumen")


def val(metrica_exacta, col="Valor"):
    row = resumen_df[resumen_df["Metrica"] == metrica_exacta]
    return None if row.empty else clean(row.iloc[0][col])


# El sheet 1_Resumen tiene "mediana"/"media" repetidos bajo distintas secciones;
# los tomamos por posicion (mismo orden que arma 02_reporte_excel.py)
r = resumen_df["Valor"].tolist()
fissal_resumen = {
    "pacientes_totales": int(r[0]),
    "pacientes_tratamiento": int(r[1]),
    "costo_nominal": {"mediana": r[3], "media": r[4]},
    "costo_deflactado": {"mediana": r[6], "media": r[7]},
    "desglose_mediana": {"tratamiento": r[9], "soporte": r[10], "no_atribuible": r[11]},
    "desglose_media": {"tratamiento": r[13], "soporte": r[14], "no_atribuible": r[15]},
    "tiempo_dias": {"mediana": r[17], "media": r[18]},
    "tiempo_anios": {"mediana": r[19], "media": r[20]},
    "gasto_anual_deflactado": {"mediana": r[22], "media": r[23]},
    "hospitalizacion": {"dias_mediana": r[25], "n_hosp_mediana": r[26]},
    "mortalidad": {"fallecidos": int(r[28]), "proporcion": r[29]},
}

tiempos = records(pd.read_excel(xl, "2_Tiempos"))
hosp_resumen = records(pd.read_excel(xl, "3_Hospitalizacion"))
hosp_pac = records(pd.read_excel(xl, "3b_Hosp_x_Paciente"))
hosp_dist = records(pd.read_excel(xl, "3c_Distribucion_Estancia"))
otros_males = records(pd.read_excel(xl, "4_Otros_Males_Costos"))
categorias = records(pd.read_excel(xl, "5_Categorias"))
severidad = records(pd.read_excel(xl, "6_Severidad_Ingreso"))
fallecidos = records(pd.read_excel(xl, "7_Fallecidos"))

# --- Top CIE-10 no-CCR: costo por paciente + descripcion corta -------------
# Nombres cortos curados a mano para los codigos mas frecuentes (a partir de
# la version que ya tenia el usuario); fallback automatico para el resto.
DESCRIPCION_CORTA = {
    "C920": "Leucemia mieloide aguda", "C833": "Linfoma no Hodgkin células grandes",
    "N180": "Insuf. renal terminal", "N185": "Enf. renal crónica etapa 5",
    "C859": "Linfoma no Hodgkin", "C61X": "Cáncer de próstata",
    "C819": "Enfermedad de Hodgkin", "C851": "Linfoma de células B",
    "C169": "Cáncer de estómago", "C509": "Cáncer de mama",
    "C539": "Cáncer de cuello uterino", "N189": "Insuf. renal crónica",
    "C531": "Cáncer de exocérvix", "C839": "Linfoma no Hodgkin difuso",
    "C504": "Cáncer de mama (cuadrante sup. ext.)", "C163": "Cáncer gástrico (antro pilórico)",
    "C162": "Cáncer de cuerpo gástrico", "C530": "Cáncer de endocérvix",
    "C160": "Cáncer de cardias", "E119": "Diabetes tipo 2",
}


def descripcion_corta(codigo, descripcion):
    if codigo in DESCRIPCION_CORTA:
        return DESCRIPCION_CORTA[codigo]
    d = descripcion.strip()
    for pat in ["TUMOR MALIGNO DE LA ", "TUMOR MALIGNO DEL ", "TUMOR MALIGNO DE ", "TUMOR MALIGNO "]:
        if d.startswith(pat):
            return "Cáncer de " + d[len(pat):].capitalize()
    d = d.capitalize()
    return d if len(d) <= 42 else d[:39] + "…"


top_cie10_df = pd.read_excel(xl, "4b_Top20_CIE10_NoCCR")
top_cie10_df["costo_x_paciente"] = (top_cie10_df["costo_total"] / top_cie10_df["n_pac"]).round(0)
top_cie10_df["descripcion_corta"] = [
    descripcion_corta(c, d) for c, d in zip(top_cie10_df["Codigo_CIE10"], top_cie10_df["descripcion"])
]
top_cie10_df = top_cie10_df.sort_values("costo_x_paciente", ascending=False)
top_cie10 = records(top_cie10_df)

# --- Subcategorias: costo promedio por paciente (no hay costo mediano a --
# este nivel de detalle sin volver a consultar SQL a nivel de linea; se usa
# total/pacientes como aproximacion, rotulado como "promedio" en el dashboard)
subcat_df = pd.read_excel(xl, "5b_Subcategorias_Top5")
subcat_df["costo_promedio"] = (subcat_df["costo_total"] / subcat_df["n_pacientes"]).round(0)
subcategorias = records(subcat_df)
subcategorias_top13 = records(subcat_df.sort_values("costo_promedio", ascending=False).head(13))

# --- Evolucion anual: excluir año en curso (parcial, distorsiona la serie) -
evol_df = pd.read_excel(xl, "8_Evolucion_Anual")
anio_actual = int(evol_df["Año"].max())
fila_actual = evol_df[evol_df["Año"] == anio_actual].iloc[0]
evolucion_nota = (
    f"Se excluye {anio_actual}: año en curso, datos parciales "
    f"({int(fila_actual['pacientes_con_gasto']):,} pacientes con gasto registrado a la fecha de corte, "
    f"vs. {int(evol_df[evol_df['Año'] < anio_actual]['pacientes_con_gasto'].mean()):,} en promedio en años completos)"
)
evolucion = records(evol_df[evol_df["Año"] < anio_actual])

fissal_data = {
    "resumen": fissal_resumen,
    "tiempos": tiempos,
    "hospitalizacion": {"resumen": hosp_resumen, "por_paciente": hosp_pac, "distribucion": hosp_dist},
    "otros_males": {"metricas": otros_males, "top_cie10": top_cie10},
    "categorias": categorias,
    "subcategorias": subcategorias,
    "subcategorias_top13": subcategorias_top13,
    "evolucion_nota": evolucion_nota,
    "severidad": severidad,
    "fallecidos": fallecidos,
    "evolucion": evolucion,
}

# --- Perfil general (sexo, localizacion, edad) desde el parquet de hitos ---
print("Cargando perfil general (sexo/localizacion/edad) desde hitos...")
FISSAL_PARQUET = Path(r"C:\Users\eah\apoyoconsultoria.com\File Server - Analytics\7 Datos\Datos abiertos\fissal\01_silver\FISSAL_CCR_HITOS_V2.parquet")
hitos_full = pd.read_parquet(FISSAL_PARQUET, columns=["SEXO", "LOCALIZACION", "RANGO_EDAD", "EDAD_PRIMERA_ATENCION"])

orden_edad = ["0-17", "18-29", "30-39", "40-49", "50-59", "60-69", "70-79", "80+"]
rango_edad_counts = hitos_full["RANGO_EDAD"].value_counts()
fissal_data["perfil"] = {
    "sexo": {k: int(v) for k, v in hitos_full["SEXO"].value_counts().items()},
    "localizacion": {k: int(v) for k, v in hitos_full["LOCALIZACION"].value_counts(dropna=False).items()},
    "rango_edad": [{"rango": r, "n": int(rango_edad_counts.get(r, 0))} for r in orden_edad],
    "edad_mediana": float(hitos_full["EDAD_PRIMERA_ATENCION"].median()),
    "n_localizacion_nula": int(hitos_full["LOCALIZACION"].isna().sum()),
}

# =====================================================================
# EsSalud
# =====================================================================
print("Cargando EsSalud...")
g = pd.read_parquet(ESSALUD_DIR / "essalud_gcop_con_id.parquet")
perfil = pd.read_parquet(ESSALUD_DIR / "essalud_gcop_perfil.parquet")
costo = pd.read_parquet(ESSALUD_DIR / "essalud_gcop_costo_proyectado.parquet")

n_ids = perfil["ID_ESSALUD_GCOP"].nunique()
vc = g["ID_ESSALUD_GCOP"].value_counts()
cie_por_id = g.groupby("ID_ESSALUD_GCOP")["DIAGNOSTICO3"].nunique()
ids_2mas = vc[vc >= 2].index
validacion_pct = round((cie_por_id.reindex(ids_2mas) == 1).mean() * 100, 1) if len(ids_2mas) else None

por_track = costo.groupby("TRACK")["COSTO_PROYECTADO_2024"].agg(["count", "median", "sum"]).reset_index()

essalud_data = {
    "gcop": {
        "n_registros": int(len(g)),
        "n_pacientes_candidatos": int(n_ids),
        "cobertura_1_registro": int((vc == 1).sum()),
        "cobertura_2mas": int((vc >= 2).sum()),
        "cobertura_5mas": int((vc >= 5).sum()),
        "cobertura_10mas": int((vc >= 10).sum()),
        "validacion_cie10_consistente_pct": validacion_pct,
        "servicios_top": [{"servicio": k, "n": int(v)} for k, v in g["SERVICIO"].value_counts().head(10).items()],
        "track": {
            row["TRACK"]: {"n": int(row["count"]), "pct": round(row["count"] / len(perfil) * 100, 1)}
            for _, row in por_track.iterrows()
        },
        "costo_proyectado": {
            "mediana": round(float(costo["COSTO_PROYECTADO_2024"].median()), 0),
            "media": round(float(costo["COSTO_PROYECTADO_2024"].mean()), 0),
            "total": round(float(costo["COSTO_PROYECTADO_2024"].sum()), 0),
            "por_track": [
                {"track": row["TRACK"], "n": int(row["count"]), "mediana": round(float(row["median"]), 0),
                 "total": round(float(row["sum"]), 0)}
                for _, row in por_track.iterrows()
            ],
        },
    },
    "gcps": {
        "n_registros": 376221,
        "rango_fechas": "01/02/2016 a 31/12/2025",
    },
}

# =====================================================================
# SIS
# =====================================================================
print("Cargando SIS...")
a = pd.read_parquet(SIS_DIR / "sis_atenciones.parquet")
c = pd.read_parquet(SIS_DIR / "sis_consumos.parquet")
a["FECHA_ATENCION"] = pd.to_datetime(a["FECHA_ATENCION"], errors="coerce")
primer = a.sort_values("FECHA_ATENCION").drop_duplicates("CODIGO_PERSONA", keep="first")
n_at_pac = a.groupby("CODIGO_PERSONA")["FECHA_ATENCION"].nunique()
loc = primer["COD_DIAGNOSTICO"].str[:3].map({"C18": "Colon", "C19": "Union rectosigmoidea", "C20": "Recto"})

sis_data = {
    "atenciones": {
        "n": int(len(a)),
        "pacientes": int(a["CODIGO_PERSONA"].nunique()),
        "atenciones_por_paciente": round(len(a) / a["CODIGO_PERSONA"].nunique(), 2),
    },
    "financiamiento": {k: int(v) for k, v in a["TIPO_FINANCIAMIENTO"].value_counts().items()},
    "sexo": {k: int(v) for k, v in primer["SEXO"].value_counts().items()},
    "localizacion": {k: int(v) for k, v in loc.value_counts().items()},
    "departamento_pct_lima": round((primer["DEPARTAMENTO_EESS"] == "15 LIMA").mean() * 100, 1),
    "tendencia_anual": [
        {"anio": int(k), "n": int(v)} for k, v in a["ANIO_ATENCION"].value_counts().sort_index().items()
    ],
    "profundidad": {
        "una_atencion_pct": round((n_at_pac == 1).mean() * 100, 1),
        "tres_mas": int((n_at_pac >= 3).sum()),
    },
    "consumos": {
        "costo_total": round(float(c["PRECIO_NETO"].sum()), 2),
        "costo_promedio_atencion": round(float(c.groupby("CODiGO_ATENCION")["PRECIO_NETO"].sum().mean()), 2),
        "n_lineas": int(len(c)),
    },
}

# =====================================================================
# Ensamblar y escribir
# =====================================================================
data = {
    "meta": {"generado": pd.Timestamp.now().strftime("%Y-%m-%d")},
    "fissal": fissal_data,
    "essalud": essalud_data,
    "sis": sis_data,
}

json_str = json.dumps(data, ensure_ascii=False)
json_str = json_str.replace("</", "<\\/")  # evitar que "</script>" dentro de un string cierre el <script>
print(f"JSON: {len(json_str):,} caracteres")

template = (DASHBOARD_DIR / "template.html").read_text(encoding="utf-8")
if "__DASHBOARD_DATA__" not in template:
    raise SystemExit("No se encontro el placeholder __DASHBOARD_DATA__ en template.html")
final_html = template.replace("__DASHBOARD_DATA__", json_str)

out_path = DASHBOARD_DIR / "index.html"
out_path.write_text(final_html, encoding="utf-8")
print(f"Escrito: {out_path}  ({out_path.stat().st_size / 1024:.0f} KB)")
