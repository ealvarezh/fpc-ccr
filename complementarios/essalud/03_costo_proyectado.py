"""
Costo proyectado para los pacientes candidatos de EsSalud (GCOP), usando los
patrones de costo observados en FISSAL como benchmark.

IMPORTANTE — por que NO se hace a nivel de item/consumo:
GCOP no trae items de consumo (medicamentos/insumos/procedimientos con su
propio costo), solo registros de CONSULTA/VISITA por especialidad (95% son
"ATENCION MEDICA AMBULATORIA", y el resultado de esa consulta -RESULT_ATENCION-
a veces indica que se deriva a cirugia/hospitalizacion, pero no factura esos
eventos aca). Multiplicar conteos de consultas por un costo unitario de FISSAL
subestimaria muchisimo el costo real, porque en FISSAL el grueso del costo
esta en cirugia/quimio/radio/hospitalizacion -- justamente lo que GCOP no
factura, solo referencia como resultado de la consulta.

Por eso la proyeccion se hace a nivel de TRAYECTORIA COMPLETA, no de item:
  1. A cada paciente candidato de EsSalud se le asigna un TRACK (A_COMPLETO
     si en algun momento su RESULT_ATENCION o especialidad sugiere
     tratamiento oncologico activo -cirugia, hospitalizacion, radioterapia-,
     B_PARCIAL si solo tuvo consultas/evaluacion) y una LOCALIZACION (Colon/
     Union rectosigmoidea/Recto por CIE10) -- exactamente los mismos criterios
     que ya se usan en fissal/hitos_v2.
  2. Se arma un benchmark con la mediana de costo TOTAL observado en FISSAL
     para pacientes reales con ese mismo TRACK + LOCALIZACION + nivel de
     N_ATENCIONES (como proxy de intensidad/duracion de la trayectoria).
  3. A cada paciente de EsSalud se le asigna el costo mediano del grupo FISSAL
     mas parecido (con fallback a un grupo mas amplio si el especifico tiene
     pocos casos para ser confiable).

Esto es una PROYECCION (que costaria esta poblacion bajo los patrones de
costo/uso de FISSAL), no una medicion. EsSalud puede tener tarifario e
intensidad de atencion distintos -- util para dimensionar la magnitud, no
para presupuestar con precision.
"""
import pyodbc
import pandas as pd
import numpy as np
from pathlib import Path

FISSAL_PARQUET = Path(r"C:\Users\eah\apoyoconsultoria.com\File Server - Analytics\7 Datos\Datos abiertos\fissal\01_silver\FISSAL_CCR_HITOS_V2.parquet")
ESSALUD_DIR = Path(r"C:\estela\github\fpc-ccr\complementarios\essalud\output")
OUTPUT = ESSALUD_DIR
FECHA_CORTE_ANIO = 2026
FACTORES_IPC = {2018: 1.26, 2019: 1.24, 2020: 1.22, 2021: 1.14, 2022: 1.05, 2023: 1.02, 2024: 1.00, 2025: 1.00, 2026: 1.00}

MIN_N_BENCHMARK = 20  # minimo de pacientes FISSAL en un grupo para confiar en su mediana

print("=" * 70)
print("Costo proyectado — EsSalud (GCOP) a partir de patrones FISSAL")
print("=" * 70)

# =====================================================================
# 1. BENCHMARK FISSAL: costo total deflactado por TRACK x LOCALIZACION x nivel de N_ATENCIONES
# =====================================================================
print("\n1. Construyendo benchmark de costo desde FISSAL...")
h = pd.read_parquet(FISSAL_PARQUET)

cost_cols = [c for c in h.columns if c.startswith("COSTO_20") and "_DEFLACTADO" not in c]
for c in cost_cols:
    yr = int(c.split("_")[1])
    h[f"{c}_DEFL"] = h[c] * FACTORES_IPC.get(yr, 1.0)
h["MONTO_NETO_TOTAL_DEFLACTADO"] = h[[f"{c}_DEFL" for c in cost_cols]].sum(axis=1)

bins_at = [0, 2, 5, 10, 20, 10_000]
labels_at = ["1-2", "3-5", "6-10", "11-20", "21+"]
h["NIVEL_ATENCIONES"] = pd.cut(h["N_ATENCIONES"], bins=bins_at, labels=labels_at)

bench = h.groupby(["TRACK", "LOCALIZACION", "NIVEL_ATENCIONES"], observed=True).agg(
    n_pacientes=("Codigo_identificacion_paciente", "count"),
    costo_mediano=("MONTO_NETO_TOTAL_DEFLACTADO", "median"),
).reset_index()
bench_confiable = bench[bench["n_pacientes"] >= MIN_N_BENCHMARK].copy()
print(f"   Grupos TRACK x LOCALIZACION x NIVEL_ATENCIONES: {len(bench)}  "
      f"(con n>={MIN_N_BENCHMARK}: {len(bench_confiable)})")

# Fallbacks mas amplios para cuando el grupo especifico no tiene suficientes casos
bench_track_nivel = h.groupby(["TRACK", "NIVEL_ATENCIONES"], observed=True).agg(
    n_pacientes=("Codigo_identificacion_paciente", "count"),
    costo_mediano=("MONTO_NETO_TOTAL_DEFLACTADO", "median"),
).reset_index()
bench_track = h.groupby(["TRACK"], observed=True).agg(
    n_pacientes=("Codigo_identificacion_paciente", "count"),
    costo_mediano=("MONTO_NETO_TOTAL_DEFLACTADO", "median"),
).reset_index()

print("\n   Vista del benchmark (grupos confiables, ordenado por costo):")
print(bench_confiable.sort_values("costo_mediano", ascending=False).to_string(index=False))

# =====================================================================
# 2. CLASIFICAR PACIENTES DE ESSALUD (TRACK, LOCALIZACION, NIVEL_ATENCIONES)
# =====================================================================
print("\n2. Cargando y clasificando pacientes candidatos de EsSalud...")
g = pd.read_parquet(ESSALUD_DIR / "essalud_gcop_con_id.parquet")

RESULT_TRATAMIENTO = {"CIRUGIA", "CIRUGIA CON INTERNAMIENTO", "HOSPITALIZACION (INTERNAMIENTO)"}
SERVICIO_TRATAMIENTO = {"RADIOTERAPIA", "CIRUGIA ONCOLOGICA"}

g["ES_EVENTO_TRATAMIENTO"] = (
    g["RESULT_ATENCION"].isin(RESULT_TRATAMIENTO)
    | g["SERVICIO"].isin(SERVICIO_TRATAMIENTO)
)

tiene_trat = g.groupby("ID_ESSALUD_GCOP")["ES_EVENTO_TRATAMIENTO"].any()
localizacion = g.groupby("ID_ESSALUD_GCOP")["DIAGNOSTICO3"].first().str[:3].map({
    "C18": "Colon", "C19": "Union rectosigmoidea", "C20": "Recto"
}).fillna("Otro CCR")
n_atenciones = g.groupby("ID_ESSALUD_GCOP")["FECHA_ATENCION"].nunique()

perfil = pd.DataFrame({
    "ID_ESSALUD_GCOP": tiene_trat.index,
    "TRACK": np.where(tiene_trat.values, "A_COMPLETO", "B_PARCIAL"),
    "LOCALIZACION": localizacion.reindex(tiene_trat.index).values,
    "N_ATENCIONES": n_atenciones.reindex(tiene_trat.index).values,
})
perfil["NIVEL_ATENCIONES"] = pd.cut(perfil["N_ATENCIONES"], bins=bins_at, labels=labels_at)

print(f"   Pacientes candidatos: {len(perfil):,}")
print(f"   Track A (evidencia de tratamiento activo): {(perfil['TRACK']=='A_COMPLETO').sum():,} "
      f"({(perfil['TRACK']=='A_COMPLETO').mean()*100:.1f}%)")
print(f"   Track B (solo consultas/evaluacion en este archivo): {(perfil['TRACK']=='B_PARCIAL').sum():,}")
print(f"\n   Distribucion NIVEL_ATENCIONES:")
print(perfil["NIVEL_ATENCIONES"].value_counts().to_string())

# =====================================================================
# 3. ASIGNAR COSTO PROYECTADO (con fallback a grupos mas amplios)
# =====================================================================
print("\n3. Asignando costo proyectado por match a FISSAL...")

m1 = perfil.merge(bench_confiable[["TRACK", "LOCALIZACION", "NIVEL_ATENCIONES", "costo_mediano"]],
                   on=["TRACK", "LOCALIZACION", "NIVEL_ATENCIONES"], how="left")
sin_match_1 = m1["costo_mediano"].isna()

m2 = m1.loc[sin_match_1, ["ID_ESSALUD_GCOP", "TRACK", "NIVEL_ATENCIONES"]].merge(
    bench_track_nivel[["TRACK", "NIVEL_ATENCIONES", "costo_mediano"]],
    on=["TRACK", "NIVEL_ATENCIONES"], how="left"
)
m1.loc[sin_match_1, "costo_mediano"] = m2["costo_mediano"].values
m1["NIVEL_MATCH"] = np.where(sin_match_1, "fallback_track+nivel", "match_completo")

sin_match_2 = m1["costo_mediano"].isna()
if sin_match_2.any():
    m3 = m1.loc[sin_match_2, ["ID_ESSALUD_GCOP", "TRACK"]].merge(
        bench_track[["TRACK", "costo_mediano"]], on="TRACK", how="left"
    )
    m1.loc[sin_match_2, "costo_mediano"] = m3["costo_mediano"].values
    m1.loc[sin_match_2, "NIVEL_MATCH"] = "fallback_solo_track"

m1 = m1.rename(columns={"costo_mediano": "COSTO_PROYECTADO_2024"})
print(m1["NIVEL_MATCH"].value_counts().to_string())
print(f"   Sin ningun match (no debería pasar): {m1['COSTO_PROYECTADO_2024'].isna().sum()}")

# =====================================================================
# 4. RESUMEN
# =====================================================================
print("\n" + "=" * 70)
print("4. RESUMEN")
print("=" * 70)
print(f"\n  Pacientes candidatos EsSalud (GCOP): {len(m1):,}")
print(f"  Costo proyectado por paciente (soles 2024) — mediana: S/ {m1['COSTO_PROYECTADO_2024'].median():>10,.0f}")
print(f"  Costo proyectado por paciente (soles 2024) — media:   S/ {m1['COSTO_PROYECTADO_2024'].mean():>10,.0f}")
print(f"\n  Costo proyectado TOTAL de la cohorte:      S/ {m1['COSTO_PROYECTADO_2024'].sum():>14,.0f}")
print(f"  (para contexto, esto es la carga que representaria esta poblacion")
print(f"   si su costo de atencion siguiera los mismos patrones que FISSAL)")

por_track = m1.groupby("TRACK")["COSTO_PROYECTADO_2024"].agg(["count", "median", "sum"])
print(f"\n  Por track:")
print(por_track.to_string())

# =====================================================================
# 5. GUARDAR
# =====================================================================
m1.to_parquet(OUTPUT / "essalud_gcop_costo_proyectado.parquet", index=False)
bench.to_csv(OUTPUT / "fissal_benchmark_costo.csv", index=False)
print(f"\n5. Guardado:")
print(f"   {OUTPUT / 'essalud_gcop_costo_proyectado.parquet'}")
print(f"   {OUTPUT / 'fissal_benchmark_costo.csv'}")
print("\nFin.")
