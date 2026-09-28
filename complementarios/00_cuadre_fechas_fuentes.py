"""
Diagnostico de cuadre de fechas y costos entre las tres fuentes:
  FISSAL  — base principal (SQL Server + parquet hitos_v2)
  SIS     — atenciones/consumos (parquet)
  EsSalud — GCOP consultas (parquet)

El script responde tres preguntas:
  1. ¿Se solapan temporalmente las tres fuentes? (rangos de fechas)
  2. ¿Fecha_atencion de FISSAL coincide con la ventana de hospitalizacion?
     (desalineacion interna de fechas FISSAL)
  3. ¿Hay pacientes cruzables entre fuentes? (intento de match por perfil)

Requiere SQL Server activo para la seccion 2 (lineas-nivel FISSAL).
Si SQL no esta disponible, esa seccion se omite y se trabaja solo con parquets.
"""
import sys
import warnings
import pandas as pd
import numpy as np
from pathlib import Path

warnings.filterwarnings("ignore")

SILVER = Path(r"C:\Users\eah\apoyoconsultoria.com\File Server - Analytics\7 Datos\Datos abiertos\fissal\01_silver")
SIS_OUT = Path(r"C:\estela\github\fpc-ccr\complementarios\sis\output")
ESS_OUT = Path(r"C:\estela\github\fpc-ccr\complementarios\essalud\output")
OUTPUT = Path(r"C:\estela\github\fpc-ccr\complementarios")

FECHA_CORTE = pd.Timestamp("2026-06-30")

SEP = "=" * 70


def banner(titulo):
    print(f"\n{SEP}")
    print(titulo)
    print(SEP)


# =====================================================================
# CARGA DE DATOS
# =====================================================================
banner("CARGA DE DATOS")

print("\n[FISSAL] Cargando FISSAL_CCR_HITOS_V2.parquet ...")
fis = pd.read_parquet(SILVER / "FISSAL_CCR_HITOS_V2.parquet")
print(f"  Pacientes: {len(fis):,}  |  Columnas: {fis.shape[1]}")

print("[SIS] Cargando sis_atenciones.parquet ...")
sis_a = pd.read_parquet(SIS_OUT / "sis_atenciones.parquet")
sis_a["FECHA_ATENCION"] = pd.to_datetime(sis_a["FECHA_ATENCION"], format="%d/%m/%y", errors="coerce")
print(f"  Registros: {len(sis_a):,}  |  Pacientes: {sis_a['CODIGO_PERSONA'].nunique():,}")

print("[SIS] Cargando sis_consumos.parquet ...")
sis_c = pd.read_parquet(SIS_OUT / "sis_consumos.parquet")
print(f"  Registros: {len(sis_c):,}")

print("[EsSalud] Cargando essalud_gcop_con_id.parquet ...")
gcop = pd.read_parquet(ESS_OUT / "essalud_gcop_con_id.parquet")
gcop["FECHA_ATENCION"] = pd.to_datetime(gcop["FECHA_ATENCION"], errors="coerce")
print(f"  Registros: {len(gcop):,}  |  Pacientes: {gcop['ID_ESSALUD_GCOP'].nunique():,}")


# =====================================================================
# SECCION 1: RANGOS TEMPORALES COMPARADOS
# =====================================================================
banner("1. RANGOS TEMPORALES POR FUENTE")

for nombre, serie in [
    ("FISSAL  — primera atencion", fis["PRIMERA_ATENCION"]),
    ("FISSAL  — diagnostico CCR",  fis["FECHA_DIAGNOSTICO_CCR"]),
    ("FISSAL  — ultima atencion",  fis["ULTIMA_ATENCION"]),
    ("SIS     — atenciones",       sis_a["FECHA_ATENCION"]),
    ("EsSalud — consultas",        gcop["FECHA_ATENCION"]),
]:
    s = pd.to_datetime(serie, errors="coerce").dropna()
    print(f"\n  {nombre}")
    print(f"    Min : {s.min().date()}   Max : {s.max().date()}")
    print(f"    Años con datos: {sorted(s.dt.year.unique().tolist())}")

print("\n--- Distribucion anual de pacientes por fuente ---")
print("\nFISSAL — pacientes segun año de primer diagnostico CCR:")
print(fis["PRIMERA_ATENCION"].dt.year.value_counts().sort_index().to_string())

print("\nSIS — pacientes segun año de primera atencion:")
primer_sis = sis_a.sort_values("FECHA_ATENCION").drop_duplicates("CODIGO_PERSONA", keep="first")
print(primer_sis["FECHA_ATENCION"].dt.year.value_counts().sort_index().to_string())

print("\nEsSalud — pacientes segun año de primera consulta:")
primer_ess = gcop.sort_values("FECHA_ATENCION").drop_duplicates("ID_ESSALUD_GCOP", keep="first")
print(primer_ess["FECHA_ATENCION"].dt.year.value_counts().sort_index().to_string())


# =====================================================================
# SECCION 2: DESALINEACION INTERNA DE FECHAS EN FISSAL
# (lineas-nivel: requiere SQL Server)
# =====================================================================
banner("2. DESALINEACION INTERNA: Fecha_atencion vs ventana de hospitalizacion (FISSAL)")

SQL_OK = False
try:
    import pyodbc
    conn = pyodbc.connect(
        "DRIVER={ODBC Driver 17 for SQL Server};"
        "SERVER=localhost;"
        "DATABASE=Reporte_Transparencia;"
        "Trusted_Connection=yes;",
        timeout=5,
    )

    print("\n  SQL disponible. Cargando lineas con hospitalizacion...")
    q = """
    SELECT
        Codigo_identificacion_paciente,
        Fecha_atencion,
        Fecha_ingreso_hospitalizacion,
        Fecha_alta_hospitalizacion,
        MONTO_NETO
    FROM [Reporte_2016_2026_v1]
    WHERE (Codigo_CIE10 LIKE 'C18%' OR Codigo_CIE10 LIKE 'C19%' OR Codigo_CIE10 LIKE 'C20%')
      AND Fecha_ingreso_hospitalizacion IS NOT NULL
    """
    raw = pd.read_sql(q, conn)
    conn.close()
    SQL_OK = True
    print(f"  Lineas con hospitalizacion: {len(raw):,}")

    raw["Fecha_atencion"] = pd.to_datetime(raw["Fecha_atencion"], errors="coerce")
    raw["Fecha_ingreso"] = pd.to_datetime(raw["Fecha_ingreso_hospitalizacion"], errors="coerce")
    raw["Fecha_alta"] = pd.to_datetime(raw["Fecha_alta_hospitalizacion"], errors="coerce")

    # ¿Cae Fecha_atencion dentro del episodio ingreso–alta?
    raw["dentro_ventana"] = (
        raw["Fecha_atencion"].between(raw["Fecha_ingreso"], raw["Fecha_alta"])
    )
    raw["gap_dias_atencion_ingreso"] = (raw["Fecha_atencion"] - raw["Fecha_ingreso"]).dt.days

    n_tot = len(raw)
    n_dentro = raw["dentro_ventana"].sum()
    print(f"\n  Lineas cuya Fecha_atencion esta DENTRO de [ingreso, alta]:  {n_dentro:,} / {n_tot:,} ({n_dentro/n_tot*100:.1f}%)")
    print(f"  Lineas con Fecha_atencion FUERA de la ventana:              {n_tot - n_dentro:,} / {n_tot:,} ({(n_tot-n_dentro)/n_tot*100:.1f}%)")

    print("\n  Distribucion del gap (Fecha_atencion − Fecha_ingreso) en dias:")
    pcts = raw["gap_dias_atencion_ingreso"].describe(percentiles=[.05, .25, .5, .75, .95])
    print(pcts.to_string())

    # Costo en juego segun el filtro
    costo_dentro  = raw.loc[raw["dentro_ventana"], "MONTO_NETO"].sum()
    costo_fuera   = raw.loc[~raw["dentro_ventana"], "MONTO_NETO"].sum()
    costo_total   = raw["MONTO_NETO"].sum()
    print(f"\n  Costo total en lineas de hospitalizacion:  S/ {costo_total:>14,.0f}")
    print(f"  Costo de lineas DENTRO de ventana:         S/ {costo_dentro:>14,.0f}  ({costo_dentro/costo_total*100:.1f}%)")
    print(f"  Costo de lineas FUERA de ventana:          S/ {costo_fuera:>14,.0f}  ({costo_fuera/costo_total*100:.1f}%)")
    print("\n  --> Si filtras costos de hospitalizacion por Fecha_atencion (en vez")
    print("      de por Fecha_ingreso_hospitalizacion notna), pierdes el costo de arriba.")

    # Costo por episodio de hospitalizacion
    print("\n--- Costo por EPISODIO de hospitalizacion ---")
    ep = raw.groupby(
        ["Codigo_identificacion_paciente", "Fecha_ingreso", "Fecha_alta"],
        dropna=False,
    ).agg(
        costo_ep=("MONTO_NETO", "sum"),
        n_lineas=("MONTO_NETO", "size"),
    ).reset_index()
    ep["dias_estancia"] = (ep["Fecha_alta"] - ep["Fecha_ingreso"]).dt.days
    ep = ep[(ep["dias_estancia"] >= 0) & (ep["dias_estancia"] <= 365)]
    ep["costo_por_dia"] = np.where(ep["dias_estancia"] > 0, ep["costo_ep"] / ep["dias_estancia"], ep["costo_ep"])

    print(f"  Episodios unicos de hospitalizacion: {len(ep):,}")
    print("\n  Costo por episodio (S/):")
    print(ep["costo_ep"].describe(percentiles=[.25, .5, .75, .9]).to_string())
    print("\n  Dias de estancia por episodio:")
    print(ep["dias_estancia"].describe(percentiles=[.25, .5, .75, .9]).to_string())
    print("\n  Costo por dia de estancia (S/):")
    print(ep["costo_por_dia"].describe(percentiles=[.25, .5, .75, .9]).to_string())

    ep_out = OUTPUT / "fissal_episodios_hospitalizacion.parquet"
    ep.to_parquet(ep_out, index=False)
    print(f"\n  Guardado: {ep_out}")

except Exception as e:
    print(f"\n  SQL no disponible ({e}). Seccion 2 se omite.")
    print("  Analisis de desalineacion requiere SQL Server activo con la base Reporte_Transparencia.")


# =====================================================================
# SECCION 3: CRUCE DE POBLACIONES — ¿mismos pacientes entre fuentes?
# =====================================================================
banner("3. CRUCE DE POBLACIONES")

print("""
  Identificadores por fuente:
    FISSAL   → Codigo_identificacion_paciente  (hash interno de FISSAL, NO es DNI)
    SIS      → CODIGO_PERSONA                  (codigo de beneficiario SIS)
    EsSalud  → DNI enmascarado (4 digitos centrales = ****)

  Conclusion directa: NO hay campo comun para hacer un JOIN exacto entre fuentes.
  El siguiente analisis evalua si la poblacion es comparable por PERFIL.
""")

# Distribucion por localizacion (sexo no disponible en SIS consumos directamente)
print("--- Localizacion del tumor (distribucion relativa) ---\n")

fissal_loc = fis["LOCALIZACION"].value_counts(normalize=True).mul(100).round(1)
fissal_loc.name = "FISSAL %"

sis_loc_raw = sis_a["COD_DIAGNOSTICO"].str[:3].map(
    {"C18": "Colon", "C19": "Union rectosigmoidea", "C20": "Recto"}
).dropna()
sis_loc = sis_loc_raw.value_counts(normalize=True).mul(100).round(1)
sis_loc.name = "SIS %"

ess_loc_raw = gcop["DIAGNOSTICO3"].str[:3].map(
    {"C18": "Colon", "C19": "Union rectosigmoidea", "C20": "Recto"}
).dropna()
ess_loc = ess_loc_raw.value_counts(normalize=True).mul(100).round(1)
ess_loc.name = "EsSalud %"

tabla_loc = pd.concat([fissal_loc, sis_loc, ess_loc], axis=1).fillna(0)
print(tabla_loc.to_string())

# Sexo (donde disponible)
print("\n--- Sexo (distribucion relativa) ---\n")
fis_sexo = fis["SEXO"].value_counts(normalize=True).mul(100).round(1)
fis_sexo.name = "FISSAL %"

sis_sexo = sis_a.drop_duplicates("CODIGO_PERSONA")["SEXO"].value_counts(normalize=True).mul(100).round(1)
sis_sexo.name = "SIS %"

ess_sexo = gcop.drop_duplicates("ID_ESSALUD_GCOP")["SEXO"].value_counts(normalize=True).mul(100).round(1)
ess_sexo.name = "EsSalud %"

tabla_sexo = pd.concat([fis_sexo, sis_sexo, ess_sexo], axis=1).fillna(0)
print(tabla_sexo.to_string())


# =====================================================================
# SECCION 4: COMPARACION DE COSTOS ENTRE FUENTES
# =====================================================================
banner("4. COMPARACION DE COSTOS: lo que cada fuente captura")

print("\n--- SIS consumos: estructura de costos ---")
if "PRECIO_NETO" in sis_c.columns:
    precio_col = "PRECIO_NETO"
elif "MONTO_NETO" in sis_c.columns:
    precio_col = "MONTO_NETO"
else:
    precio_col = None

if precio_col:
    print(f"  Costo total capturado en SIS consumos: S/ {sis_c[precio_col].sum():>14,.0f}")
    print(f"  Costo por linea (percentiles):")
    print(sis_c[precio_col].describe(percentiles=[.25, .5, .75, .9, .99]).to_string())
    costo_por_atencion = sis_c.groupby("CODiGO_ATENCION" if "CODiGO_ATENCION" in sis_c.columns else sis_c.columns[0])[precio_col].sum()
    print(f"  Costo por atencion (percentiles):")
    print(costo_por_atencion.describe(percentiles=[.25, .5, .75, .9]).to_string())
else:
    print(f"  Columnas disponibles: {list(sis_c.columns)}")

print("\n--- FISSAL: costos resumidos por paciente (del parquet hitos_v2) ---")
print(f"  Pacientes con hospitalizacion registrada: {(fis['N_HOSPITALIZACIONES'] > 0).sum():,}")
print(f"  Pacientes sin hospitalizacion registrada: {(fis['N_HOSPITALIZACIONES'] == 0).sum():,}")

fis_reg = fis[fis["FISSAL_REGULAR"] == True]
print(f"\n  Costo neto total (todos los pacientes) — mediana: S/ {fis['MONTO_NETO_TOTAL'].median():>12,.0f}")
print(f"  Costo neto total (todos los pacientes) — media:   S/ {fis['MONTO_NETO_TOTAL'].mean():>12,.0f}")
print(f"\n  Pacientes FISSAL regular (>=3 atenciones, n={len(fis_reg):,}):")
print(f"  Costo neto total — mediana: S/ {fis_reg['MONTO_NETO_TOTAL'].median():>12,.0f}")
print(f"  Costo neto total — media:   S/ {fis_reg['MONTO_NETO_TOTAL'].mean():>12,.0f}")

print("\n  Costo por track (FISSAL regular):")
print(fis_reg.groupby("TRACK")["MONTO_NETO_TOTAL"].agg(["count", "median", "mean"]).to_string())

print("\n  Hospitalizaciones por paciente (FISSAL — todos):")
print(fis["N_HOSPITALIZACIONES"].describe(percentiles=[.5, .75, .9, .99]).to_string())

print("\n  Dias totales de hospitalizacion por paciente (solo los que tienen >=1 hospitalizacion):")
hosp_mask = fis["N_HOSPITALIZACIONES"] > 0
print(fis.loc[hosp_mask, "DIAS_HOSPITALIZACION_TOTAL"].describe(percentiles=[.25, .5, .75, .9]).to_string())


# =====================================================================
# SECCION 5: RESUMEN DIAGNOSTICO
# =====================================================================
banner("5. RESUMEN DIAGNOSTICO")

print("""
  POR QUE NO CUADRAN LOS COSTOS ENTRE FUENTES:
  ─────────────────────────────────────────────

  A) Poblaciones diferentes
     • SIS: pacientes con CCR financiados directamente por SIS, sin escalar a
       cobertura catastrofica FISSAL. Son pacientes "antes de" o "en vez de"
       FISSAL — distinto set de personas.
     • EsSalud/GCOP: asegurados de EsSalud atendidos en sus propios centros.
       No hay traslape directo con pacientes FISSAL (regimen diferente).
     • FISSAL: pacientes escalados a cobertura catastrofica (enfermedades de
       alto costo financiadas por el SIS-FISSAL).

  B) Nivel de captura de costos diferente
     • SIS consumos: captura copagos e items puntuales (S/3 a S/100), NO la
       facturacion completa de cirugia/quimio/radio/hospitalizacion.
     • EsSalud/GCOP: solo registra consultas externas. No hay datos de costo.
     • FISSAL: facturacion completa del episodio oncologico (items, insumos,
       medicamentos, hospitalizacion, cirugia).

  C) Desalineacion de fechas dentro de FISSAL
     • Fecha_atencion puede diferir de Fecha_ingreso_hospitalizacion por ser
       la fecha de "produccion" del mes, no la del acto medico.
     • Si filtras costos de hospitalizacion por Fecha_atencion pierdes una
       fraccion significativa del costo real del episodio.
     • Solucion: usar Fecha_ingreso_hospitalizacion NOT NULL como discriminador
       (ya implementado en hitos_v2; ver seccion 2 de este script).

  D) Sin ID comun entre fuentes
     • No es posible hacer un JOIN exacto paciente-a-paciente entre FISSAL,
       SIS y EsSalud. Solo se pueden comparar distribuciones de perfil.

  QUE SI ES COMPARABLE:
  ─────────────────────
  • Distribucion de localizacion (Colon/Union/Recto) y sexo entre las tres
    fuentes — ver seccion 3 de este script.
  • Tendencias temporales (actividad por año) — ver seccion 1.
  • Costo de hospitalizacion vs. ambulatorio DENTRO de FISSAL — ver seccion 2
    (requiere SQL) o usar N_HOSPITALIZACIONES / DIAS_HOSPITALIZACION_TOTAL
    del parquet hitos_v2 como proxy.
""")

print("Fin del diagnostico.")
