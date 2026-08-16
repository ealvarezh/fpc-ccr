import pandas as pd
from pathlib import Path
p = Path(r"C:\Users\eah\apoyoconsultoria.com\File Server - Analytics\7 Datos\Datos abiertos\fissal\01_silver")
h = pd.read_parquet(p / "FISSAL_CCR_HITOS_V2.parquet")

track = h[(h["TRACK"] == "A_COMPLETO") & (h["FISSAL_REGULAR"])]
n = len(track)

print(f"Pacientes Track A COMPLETO + FISSAL regular: {n:,}")
print()
print(f"Costo neto total (mediana):  S/ {track['MONTO_NETO_TOTAL'].median():>10,.0f}")
print(f"Costo neto total (media):    S/ {track['MONTO_NETO_TOTAL'].mean():>10,.0f}")
print(f"Costo CRC atribuible (med):   S/ {track['COSTO_CRC_ATRIBUIBLE'].median():>10,.0f}")
print(f"Costo soporte (med):          S/ {track['COSTO_SOPORTE'].median():>10,.0f}")
print(f"Costo NO atribuible (med):    S/ {track['COSTO_NO_ATRIBUIBLE'].median():>10,.0f}")

t_dias = track["TIEMPO_EN_SISTEMA_DIAS"]
t_anos = t_dias / 365
print(f"\nTiempo en sistema (mediana):  {t_dias.median():.0f} dias ({t_anos.median():.1f} anos)")
print(f"Tiempo en sistema (media):    {t_dias.mean():.0f} dias ({t_anos.mean():.1f} anos)")

mask = t_anos > 0.1
costo_anual = track.loc[mask, "MONTO_NETO_TOTAL"] / t_anos[mask]
print(f"\nCosto ANUAL por paciente (mediana): S/ {costo_anual.median():>10,.0f}")
print(f"Costo ANUAL por paciente (media):   S/ {costo_anual.mean():>10,.0f}")

print()
cost_cols = sorted([c for c in track.columns if c.startswith("COSTO_20")])
print("Costo mediano por ano (solo pacientes con gasto ese ano):")
for cc in cost_cols:
    yr = cc.split("_")[1]
    vals = track[cc]
    vals_pos = vals[vals > 0]
    if len(vals_pos) > 0:
        print(f"  {yr}: S/ {vals_pos.median():>10,.0f} (n={len(vals_pos):>6,})")

# Total cohort cost by year
print(f"\nGasto total de la cohorte por ano:")
for cc in cost_cols:
    yr = cc.split("_")[1]
    total = track[cc].sum()
    print(f"  {yr}: S/ {total:>14,.0f}")
