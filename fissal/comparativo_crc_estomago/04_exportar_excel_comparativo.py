import sys
import pandas as pd
import numpy as np
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SILVER = Path(r"C:\Users\eah\apoyoconsultoria.com\File Server - Analytics\7 Datos\Datos abiertos\fissal\01_silver")
SALIDA_DIR = SILVER.parent / "03_output" / "hitos_paciente"
SALIDA_DIR.mkdir(parents=True, exist_ok=True)
SALIDA_XLSX = SALIDA_DIR / "FISSAL_Comparativo_CRC_vs_Estomago.xlsx"

ORDEN_HITOS = ["1_DESPISTAJE", "2_DIAGNOSTICO", "3_TRATAMIENTO", "4_DESENLACE"]

print("=" * 70)
print("EXPORTANDO COMPARATIVO CRC vs CANCER DE ESTOMAGO")
print("=" * 70)


def cargar_cancer(nombre, archivo_hitos, archivo_costeo_hito):
    hp = pd.read_parquet(archivo_hitos, columns=[
        "NUM_DOC_CRYPTO", "FECHA_DIAGNOSTICO", "FECHA_FIN_TRATAMIENTO", "FECHA_DESENLACE",
        "SECUENCIA_TRATAMIENTO", "DIAS_DESPISTAJE_A_DIAGNOSTICO", "DIAS_DIAGNOSTICO_A_TRATAMIENTO",
        "MONTO_NETO_TOTAL",
    ])
    hp["ANIO_DIAGNOSTICO"] = hp["FECHA_DIAGNOSTICO"].dt.year
    tuvo_trat = hp["SECUENCIA_TRATAMIENTO"] != "SIN_TRATAMIENTO_DETECTADO"
    hp["TRAT_A_DESENLACE"] = np.where(
        tuvo_trat, (hp["FECHA_DESENLACE"] - hp["FECHA_FIN_TRATAMIENTO"]).dt.days, np.nan)
    hp["DX_A_DESENLACE"] = (hp["FECHA_DESENLACE"] - hp["FECHA_DIAGNOSTICO"]).dt.days
    hp["CANCER"] = nombre

    costeo_hito = pd.read_parquet(archivo_costeo_hito)
    costeo_hito = costeo_hito.merge(hp[["NUM_DOC_CRYPTO", "ANIO_DIAGNOSTICO"]], on="NUM_DOC_CRYPTO", how="left")
    costeo_hito["CANCER"] = nombre
    return hp, costeo_hito


print("Cargando CRC...")
hp_crc, costeo_crc = cargar_cancer(
    "CRC", SILVER / "FISSAL_CCR_HITOS_PACIENTE.parquet", SILVER / "FISSAL_CCR_COSTEO_HITO.parquet")
print(f"  {len(hp_crc):,} pacientes")

print("Cargando Cancer de Estomago...")
hp_est, costeo_est = cargar_cancer(
    "ESTOMAGO", SILVER / "FISSAL_ESTOMAGO_HITOS_PACIENTE.parquet",
    SILVER / "FISSAL_ESTOMAGO_COSTEO_HITO.parquet")
print(f"  {len(hp_est):,} pacientes")

hp_todos = pd.concat([hp_crc, hp_est], ignore_index=True)
costeo_todos = pd.concat([costeo_crc, costeo_est], ignore_index=True)


def poblacion_hito(df_hito, hito):
    """Igual criterio que el Excel de CRC: Hito 1 solo cuenta pacientes con
    actividad pre-diagnostico real (N_LINEAS > 0), para no aplanar la
    mediana con el grupo mayoritario cuyo primer contacto YA es el
    diagnostico."""
    if hito == "1_DESPISTAJE":
        return df_hito[df_hito["N_LINEAS"] > 0]
    return df_hito


def stats_costo_tiempo(sub):
    return {
        "N_PACIENTES": len(sub),
        "COSTO_NETO_MEDIA": sub["COSTO_NETO"].mean(),
        "COSTO_NETO_MEDIANA": sub["COSTO_NETO"].median(),
        "DURACION_DIAS_MEDIA": sub["DURACION_DIAS"].mean(),
        "DURACION_DIAS_MEDIANA": sub["DURACION_DIAS"].median(),
    }


def stats_dias(s):
    s = s.dropna()
    s = s[s >= 0]
    if len(s) == 0:
        return {"N": 0, "DIAS_MEDIA": np.nan, "DIAS_MEDIANA": np.nan}
    return {"N": len(s), "DIAS_MEDIA": s.mean(), "DIAS_MEDIANA": s.median()}


# =====================================================================
# HOJA 1: COMPARATIVO GENERAL (cuanto se invirtio en cada cancer)
# =====================================================================
print("\nHoja 1: comparativo general...")
filas = []
for nombre, hp in [("CRC", hp_crc), ("ESTOMAGO", hp_est)]:
    m = hp["MONTO_NETO_TOTAL"]
    filas.append({
        "CANCER": nombre, "N_PACIENTES": len(hp),
        "COSTO_NETO_TOTAL": m.sum(), "COSTO_NETO_MEDIA_PACIENTE": m.mean(),
        "COSTO_NETO_MEDIANA_PACIENTE": m.median(),
    })
tabla1_general = pd.DataFrame(filas)

filas = []
for nombre, hp in [("CRC", hp_crc), ("ESTOMAGO", hp_est)]:
    for anio, sub in hp.groupby("ANIO_DIAGNOSTICO"):
        m = sub["MONTO_NETO_TOTAL"]
        filas.append({
            "ANIO_DIAGNOSTICO": int(anio), "CANCER": nombre, "N_PACIENTES": len(sub),
            "COSTO_NETO_TOTAL": m.sum(), "COSTO_NETO_MEDIA_PACIENTE": m.mean(),
            "COSTO_NETO_MEDIANA_PACIENTE": m.median(),
        })
tabla1_por_anio = pd.DataFrame(filas).sort_values(["ANIO_DIAGNOSTICO", "CANCER"])

# =====================================================================
# HOJA 2: COSTO Y TIEMPO POR HITO, CRC vs ESTOMAGO
# =====================================================================
print("Hoja 2: costo y tiempo por hito, comparativo...")
filas = []
for nombre in ["CRC", "ESTOMAGO"]:
    ct = costeo_todos[costeo_todos["CANCER"] == nombre]
    for h in ORDEN_HITOS:
        sub = poblacion_hito(ct[ct["HITO"] == h], h)
        filas.append({"CANCER": nombre, "HITO": h, **stats_costo_tiempo(sub)})
tabla2_general = pd.DataFrame(filas)

filas = []
for nombre in ["CRC", "ESTOMAGO"]:
    ct = costeo_todos[costeo_todos["CANCER"] == nombre]
    for h in ORDEN_HITOS:
        sub_h = poblacion_hito(ct[ct["HITO"] == h], h)
        for anio, sub in sub_h.groupby("ANIO_DIAGNOSTICO"):
            filas.append({"ANIO_DIAGNOSTICO": int(anio), "CANCER": nombre, "HITO": h, **stats_costo_tiempo(sub)})
tabla2_por_anio = pd.DataFrame(filas).sort_values(["ANIO_DIAGNOSTICO", "HITO", "CANCER"])

# =====================================================================
# HOJA 3: TRANSICIONES ENTRE HITOS, CRC vs ESTOMAGO
# =====================================================================
print("Hoja 3: transiciones entre hitos, comparativo...")
TRANSICIONES = [
    ("DIAS_DESPISTAJE_A_DIAGNOSTICO", "1. Despistaje -> Diagnostico"),
    ("DIAS_DIAGNOSTICO_A_TRATAMIENTO", "2. Diagnostico -> Tratamiento"),
    ("TRAT_A_DESENLACE", "3. Tratamiento -> Desenlace"),
    ("DX_A_DESENLACE", "4. Diagnostico -> Desenlace (trayectoria total)"),
]

filas = []
for nombre, hp in [("CRC", hp_crc), ("ESTOMAGO", hp_est)]:
    for col, label in TRANSICIONES:
        filas.append({"CANCER": nombre, "TRANSICION": label, **stats_dias(hp[col])})
tabla3_general = pd.DataFrame(filas)

filas = []
for nombre, hp in [("CRC", hp_crc), ("ESTOMAGO", hp_est)]:
    for col, label in TRANSICIONES:
        for anio, sub in hp.groupby("ANIO_DIAGNOSTICO"):
            filas.append({"ANIO_DIAGNOSTICO": int(anio), "CANCER": nombre, "TRANSICION": label,
                          **stats_dias(sub[col])})
tabla3_por_anio = pd.DataFrame(filas).sort_values(["ANIO_DIAGNOSTICO", "TRANSICION", "CANCER"])

# =====================================================================
# HOJA DE NOTAS
# =====================================================================
notas = pd.DataFrame({"Nota": [
    "Comparativo de inversion: Cancer Colorrectal (CRC, CIE-10 C18/C19/C20) vs Cancer de Estomago",
    "(CIE-10 C16), FISSAL 2016-2022.",
    "",
    "MISMO MARCO DE 4 HITOS que el analisis de CRC (ver README de fissal/hitos_paciente):",
    "  1_DESPISTAJE: toda actividad ANTES del diagnostico.",
    "  2_DIAGNOSTICO: solo el dia exacto del diagnostico.",
    "  3_TRATAMIENTO: (diagnostico, fin de tratamiento], solo pacientes con tratamiento detectado.",
    "  4_DESENLACE: (fin de tratamiento, desenlace] si tuvo tratamiento, o (diagnostico, desenlace] si no.",
    "",
    "DIFERENCIA IMPORTANTE EN EL HITO 4 DE ESTOMAGO:",
    "  Para CRC, FECHA_DESENLACE viene de una clasificacion elaborada (RECAIDA_PROBABLE,",
    "  CONTROL_POST_PAUSA, POSIBLE_REMISION_O_ALTA, PALIATIVO). Para Estomago se SIMPLIFICO:",
    "  FECHA_DESENLACE = fecha de fallecimiento si fallecio, o fecha de ultima atencion si no.",
    "  Los NUMEROS de costo/tiempo del Hito 4 son comparables igual (la ventana temporal es la",
    "  misma), pero Estomago no tiene esa sub-clasificacion cualitativa del desenlace.",
    "",
    "DETECCION DE TRATAMIENTO (Hito 3): regex de texto + diccionario categoria/subcategoria_recurso_502",
    "(diccionario_ATE_DESCCONSUMO_502_estandarizado.xlsx), igual metodologia que CRC. Para estomago,",
    "CIRUGIA usa terminos de gastrectomia/gastroyeyunostomia/esofagoyeyunostomia (en vez de",
    "colectomia), y QUIMIOTERAPIA agrega DOCETAXEL/CISPLATINO/EPIRUBICINA (esquemas gastricos tipo",
    "ECF) a la lista de farmacos ya usada en CRC. La subcategoria del diccionario usada para CIRUGIA",
    "es 'Cirugia digestiva' (no existe una subcategoria 'Cirugia gastrica' separada).",
    "",
    "Hito 1 (despistaje): las estadisticas de costo/tiempo solo consideran pacientes con actividad",
    "real antes del diagnostico (N_LINEAS > 0), igual criterio que el Excel de CRC.",
    "",
    "'PorAnio' usa el AÑO DE DIAGNOSTICO (cohorte) de cada cancer por separado, no año calendario.",
]})

# =====================================================================
# GUARDADO
# =====================================================================
print(f"\nGuardando Excel: {SALIDA_XLSX}")
with pd.ExcelWriter(SALIDA_XLSX, engine="openpyxl") as writer:
    notas.to_excel(writer, sheet_name="0_Notas", index=False)
    tabla1_general.to_excel(writer, sheet_name="1_General", index=False)
    tabla1_por_anio.to_excel(writer, sheet_name="1_General_PorAnio", index=False)
    tabla2_general.to_excel(writer, sheet_name="2_PorHito", index=False)
    tabla2_por_anio.to_excel(writer, sheet_name="2_PorHito_PorAnio", index=False)
    tabla3_general.to_excel(writer, sheet_name="3_Transiciones", index=False)
    tabla3_por_anio.to_excel(writer, sheet_name="3_Transiciones_PorAnio", index=False)

print(f"  {len(tabla1_general)} filas en 1_General_Comparativo")
print(f"  {len(tabla1_por_anio)} filas en 1_General_Comparativo_PorAnio")
print(f"  {len(tabla2_general)} filas en 2_PorHito_Comparativo")
print(f"  {len(tabla2_por_anio)} filas en 2_PorHito_Comparativo_PorAnio")
print(f"  {len(tabla3_general)} filas en 3_Transiciones_Comparativo")
print(f"  {len(tabla3_por_anio)} filas en 3_Transiciones_Comparativo_PorAnio")

print("\nFin.")
