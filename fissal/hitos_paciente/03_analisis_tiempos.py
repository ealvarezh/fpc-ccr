import sys
import pandas as pd
import numpy as np
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
pd.set_option('display.max_columns', None)

SILVER = Path(r"C:\Users\eah\apoyoconsultoria.com\File Server - Analytics\7 Datos\Datos abiertos\fissal\01_silver")
ARCHIVO_HITOS = SILVER / "FISSAL_CCR_HITOS_PACIENTE.parquet"

RANGOS_EDAD = ["0-17", "18-29", "30-39", "40-49", "50-59", "60-69", "70-79", "80+"]

print("=" * 70)
print("ANALISIS TRANSVERSAL DE TIEMPOS — TODOS LOS HITOS")
print("CANCER COLORRECTAL — FISSAL 2016-2022")
print("=" * 70)
print("""
Este script mira los tiempos de la trayectoria COMPLETA (no un hito a la
vez): cuanto tarda cada tramo, si hay diferencias por sexo o edad, y donde
se concentra la hospitalizacion. Complementa a 02_analisis_hitos.py, que
analiza cada hito por separado.
""")

hp = pd.read_parquet(ARCHIVO_HITOS)
n_total = len(hp)
print(f"Pacientes: {n_total:,}")

# --- Intervalos derivados que cruzan hitos ---
hp["TIEMPO_TOTAL_TRAYECTORIA_DIAS"] = (hp["FECHA_DESENLACE"] - hp["FECHA_DIAGNOSTICO"]).dt.days
con_trat_fin = hp["FECHA_FIN_TRATAMIENTO"].notna()
hp["TIEMPO_TRATAMIENTO_A_DESENLACE_DIAS"] = np.nan
hp.loc[con_trat_fin, "TIEMPO_TRATAMIENTO_A_DESENLACE_DIAS"] = (
    hp.loc[con_trat_fin, "FECHA_DESENLACE"] - hp.loc[con_trat_fin, "FECHA_FIN_TRATAMIENTO"]
).dt.days

INTERVALOS = [
    ("DIAS_DESPISTAJE_A_DIAGNOSTICO", "Despistaje -> Diagnostico", "solo con despistaje detectado"),
    ("DIAS_DIAGNOSTICO_A_TRATAMIENTO", "Diagnostico -> Inicio tratamiento", "solo con tratamiento detectado"),
    ("DURACION_CIRUGIA_DIAS", "Duracion de la cirugia (1ra a ultima sesion)", "solo con cirugia"),
    ("DURACION_QUIMIOTERAPIA_DIAS", "Duracion de la quimioterapia", "solo con quimioterapia"),
    ("TIEMPO_TRATAMIENTO_A_DESENLACE_DIAS", "Fin de tratamiento -> Desenlace", "solo con tratamiento detectado"),
    ("TIEMPO_TOTAL_TRAYECTORIA_DIAS", "Diagnostico -> Desenlace (trayectoria total)", "todos los pacientes"),
]


def stats_dias(serie):
    s = serie.dropna()
    s = s[s >= 0]
    if len(s) == 0:
        return None
    return {
        "n": len(s), "media": s.mean(), "mediana": s.median(),
        "p25": s.quantile(.25), "p75": s.quantile(.75),
    }


# =====================================================================
# 1. RESUMEN GENERAL DE TIEMPOS (TODOS LOS TRAMOS)
# =====================================================================
print("=" * 70)
print("1. RESUMEN DE TIEMPOS EN TODA LA TRAYECTORIA")
print("=" * 70)

for col, titulo, nota in INTERVALOS:
    st = stats_dias(hp[col])
    print(f"\n  {titulo} ({nota}):")
    if st is None:
        print("    (sin datos)")
        continue
    print(f"    n={st['n']:>6,}  media={st['media']:>7.1f}d ({st['media']/30:.1f}m)  "
          f"mediana={st['mediana']:>6.0f}d ({st['mediana']/30:.1f}m)  "
          f"P25={st['p25']:>5.0f}d  P75={st['p75']:>5.0f}d")


# =====================================================================
# 2. TIEMPOS POR SEXO — ¿HAY DIFERENCIAS DE CUMPLIMIENTO?
# =====================================================================
print("\n" + "=" * 70)
print("2. TIEMPOS POR SEXO")
print("=" * 70)

for col, titulo, nota in INTERVALOS:
    print(f"\n  {titulo}:")
    medianas = {}
    for sexo in ["F", "M"]:
        sub = hp[hp["SEXO"] == sexo]
        st = stats_dias(sub[col])
        if st is None:
            continue
        medianas[sexo] = st["mediana"]
        print(f"    {sexo} (n={st['n']:>5,}): media={st['media']:>7.1f}d  mediana={st['mediana']:>6.0f}d")
    if len(medianas) == 2:
        mas_lento = max(medianas, key=medianas.get)
        diff = abs(medianas["F"] - medianas["M"])
        if diff >= 5:
            print(f"    -> {mas_lento} tiene la mediana mas alta en este tramo (+{diff:.0f}d vs el otro sexo)")

print("\n  --- Adherencia durante tratamiento (brechas > 45d), por sexo ---")
con_trat = hp[hp["SECUENCIA_TRATAMIENTO"] != "SIN_TRATAMIENTO_DETECTADO"]
for sexo in ["F", "M"]:
    sub = con_trat[con_trat["SEXO"] == sexo]
    if len(sub) == 0:
        continue
    n_brecha = sub["TUVO_BRECHA_ADHERENCIA"].sum()
    print(f"    {sexo} (n={len(sub):,}): con brecha larga = {n_brecha:,} ({n_brecha/len(sub)*100:5.1f}%) "
          f"| SIN brecha (mas puntuales) = {len(sub)-n_brecha:,} ({(len(sub)-n_brecha)/len(sub)*100:5.1f}%)")
print("    Nota: 'con brecha larga' = al menos un vacio >45d en su facturacion durante el")
print("    tratamiento activo. Menor % de brechas sugiere mayor regularidad/cumplimiento.")


# =====================================================================
# 3. TIEMPOS POR RANGO DE EDAD
# =====================================================================
print("\n" + "=" * 70)
print("3. TIEMPOS POR RANGO DE EDAD")
print("=" * 70)

for col, titulo, nota in INTERVALOS:
    print(f"\n  {titulo}:")
    for r in RANGOS_EDAD:
        sub = hp[hp["RANGO_EDAD"] == r]
        st = stats_dias(sub[col])
        if st is None or st["n"] < 5:
            continue
        print(f"    {r:>5s} (n={st['n']:>5,}): media={st['media']:>7.1f}d  mediana={st['mediana']:>6.0f}d")

print("\n  --- Adherencia durante tratamiento (brechas > 45d), por rango de edad ---")
for r in RANGOS_EDAD:
    sub = con_trat[con_trat["RANGO_EDAD"] == r]
    if len(sub) < 5:
        continue
    n_brecha = sub["TUVO_BRECHA_ADHERENCIA"].sum()
    print(f"    {r:>5s} (n={len(sub):>5,}): con brecha larga = {n_brecha:>4,} ({n_brecha/len(sub)*100:5.1f}%)")


# =====================================================================
# 4. HOSPITALIZACION: VISTA GENERAL (TODA LA TRAYECTORIA, NO SOLO TRATAMIENTO)
# =====================================================================
print("\n" + "=" * 70)
print("4. HOSPITALIZACION EN TODA LA TRAYECTORIA")
print("=" * 70)

con_hosp = hp[hp["N_HOSPITALIZACIONES"] > 0]
print(f"\n  Pacientes con al menos 1 hospitalizacion: {len(con_hosp):,} ({len(con_hosp)/n_total*100:.1f}%)")

print("\n  --- Dias totales de hospitalizacion, por sexo ---")
for sexo in ["F", "M"]:
    sub = con_hosp[con_hosp["SEXO"] == sexo]
    if len(sub) == 0:
        continue
    st = stats_dias(sub["DIAS_HOSPITALIZACION_TOTAL"])
    print(f"    {sexo} (n={st['n']:>5,}): media={st['media']:>6.1f}d  mediana={st['mediana']:>5.0f}d  "
          f"n hospitalizaciones media={sub['N_HOSPITALIZACIONES'].mean():.1f}")

print("\n  --- Dias totales de hospitalizacion, por rango de edad ---")
for r in RANGOS_EDAD:
    sub = con_hosp[con_hosp["RANGO_EDAD"] == r]
    if len(sub) < 5:
        continue
    st = stats_dias(sub["DIAS_HOSPITALIZACION_TOTAL"])
    print(f"    {r:>5s} (n={st['n']:>5,}): media={st['media']:>6.1f}d  mediana={st['mediana']:>5.0f}d")

print("\n  --- % de pacientes con hospitalizacion, por desenlace ---")
for cat, n in hp["DESENLACE"].value_counts().items():
    sub = hp[hp["DESENLACE"] == cat]
    n_hosp = (sub["N_HOSPITALIZACIONES"] > 0).sum()
    print(f"    {cat:>25s}: {n_hosp:>5,} / {n:>5,} ({n_hosp/n*100:5.1f}%)")


# =====================================================================
# 5. RESUMEN: ¿QUIEN "CUMPLE MEJOR" LOS TIEMPOS?
# =====================================================================
print("\n" + "=" * 70)
print("5. RESUMEN COMPARATIVO DE CUMPLIMIENTO")
print("=" * 70)
print("""
  Se compara, por sexo y por rango de edad, el tiempo mediano de
  diagnostico->tratamiento (oportunidad de atencion) y el % con brechas
  largas de adherencia durante el tratamiento (regularidad). Un tiempo
  mediano MENOR y un % de brechas MENOR indican mejor "cumplimiento".
""")

filas = []
for sexo in ["F", "M"]:
    sub_dx = hp[(hp["SEXO"] == sexo)]
    st = stats_dias(sub_dx["DIAS_DIAGNOSTICO_A_TRATAMIENTO"])
    sub_trat = con_trat[con_trat["SEXO"] == sexo]
    pct_brecha = sub_trat["TUVO_BRECHA_ADHERENCIA"].mean() * 100 if len(sub_trat) > 0 else np.nan
    filas.append({"GRUPO": sexo, "MEDIANA_DX_A_TRAT_DIAS": st["mediana"] if st else np.nan,
                   "PCT_CON_BRECHA_ADHERENCIA": pct_brecha})
for r in RANGOS_EDAD:
    sub_dx = hp[hp["RANGO_EDAD"] == r]
    st = stats_dias(sub_dx["DIAS_DIAGNOSTICO_A_TRATAMIENTO"])
    sub_trat = con_trat[con_trat["RANGO_EDAD"] == r]
    pct_brecha = sub_trat["TUVO_BRECHA_ADHERENCIA"].mean() * 100 if len(sub_trat) > 0 else np.nan
    filas.append({"GRUPO": r, "MEDIANA_DX_A_TRAT_DIAS": st["mediana"] if st else np.nan,
                   "PCT_CON_BRECHA_ADHERENCIA": pct_brecha})

resumen = pd.DataFrame(filas)
print(resumen.to_string(index=False))

print(f"\n{'=' * 70}")
print("Fin del analisis de tiempos.")
print(f"{'=' * 70}")
