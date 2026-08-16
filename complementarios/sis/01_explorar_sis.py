"""
Exploracion de los 2 archivos que entrego SIS:
  - REPORTE_CANCER_COLON_RECTO_2018_2026.xlsx (hoja REPORTE): atenciones.
  - REPORTE_CANCER_COLON_RECTO_CONSUMOS_2018_2026.xlsx (hoja REPORTE): consumos.

A diferencia de EsSalud, SIS SI entrego un identificador de paciente
utilizable directamente (CODIGO_PERSONA) -- no hace falta construir un ID.
El problema aca no es de identificacion, es de VOLUMEN/PROFUNDIDAD: son muy
pocos registros por paciente, y el costo capturado en "consumos" es minimo
comparado con FISSAL (parece ser solo copagos/items puntuales, no la
facturacion completa del episodio).
"""
import pandas as pd
from pathlib import Path

BASE = Path(r"C:\Users\eah\apoyoconsultoria.com\File Server - Analytics\7 Datos\Datos abiertos\SIS")
OUTPUT = Path(r"C:\estela\github\fpc-ccr\complementarios\sis\output")
OUTPUT.mkdir(parents=True, exist_ok=True)

print("=" * 70)
print("EXPLORACION — SIS")
print("=" * 70)

# =====================================================================
# 1. ATENCIONES
# =====================================================================
print("\n1. Cargando REPORTE (atenciones)...")
a = pd.read_excel(BASE / "REPORTE_CANCER_COLON_RECTO_2018_2026.xlsx", sheet_name="REPORTE")
print(f"   Filas: {len(a):,}  |  Columnas: {a.shape[1]}")
print(f"   Columnas: {list(a.columns)}")

print(f"\n   TIPO_FINANCIAMIENTO:")
print(a["TIPO_FINANCIAMIENTO"].value_counts().to_string())
print("   --> 0% FISSAL: esta base NO se solapa con la base FISSAL que ya se usa")
print("       en fissal/hitos_v2 (esa es financiamiento FISSAL puro). Es una")
print("       cohorte de pacientes CCR financiados directamente por SIS, sin")
print("       escalar (o antes de escalar) a la cobertura catastrofica FISSAL.")

print(f"\n   Pacientes unicos (CODIGO_PERSONA): {a['CODIGO_PERSONA'].nunique():,}")
print(f"   Atenciones totales: {len(a):,}")
print(f"   Atenciones / paciente: {len(a) / a['CODIGO_PERSONA'].nunique():.2f}")

print(f"\n   Atenciones por año:")
print(a["ANIO_ATENCION"].value_counts().sort_index().to_string())

print(f"\n   Diagnostico (prefijo CIE10):")
print(a["COD_DIAGNOSTICO"].str[:3].value_counts().to_string())

# Profundidad de trayectoria por paciente
n_at_pac = a.groupby("CODIGO_PERSONA")["FECHA_ATENCION"].nunique()
print(f"\n   Profundidad de trayectoria (atenciones distintas por paciente):")
print(n_at_pac.describe(percentiles=[.5, .75, .9, .95, .99]).to_string())
print(f"   Pacientes con 1 sola atencion: {(n_at_pac == 1).sum():,} ({(n_at_pac==1).mean()*100:.1f}%)")
print(f"   Pacientes con 3+ atenciones (umbral 'FISSAL_REGULAR' usado en el otro proyecto): "
      f"{(n_at_pac >= 3).sum():,} ({(n_at_pac>=3).mean()*100:.1f}%)")

# =====================================================================
# 2. CONSUMOS
# =====================================================================
print("\n\n2. Cargando REPORTE (consumos)...")
c = pd.read_excel(BASE / "REPORTE_CANCER_COLON_RECTO_CONSUMOS_2018_2026.xlsx", sheet_name="REPORTE")
print(f"   Filas: {len(c):,}  |  Columnas: {c.shape[1]}")
print(f"   Columnas: {list(c.columns)}")
print(f"\n   TIPO de consumo:")
print(c["TIPO"].value_counts().to_string())
print(f"\n   Costo total capturado: S/ {c['PRECIO_NETO'].sum():,.2f}")
print(f"   Costo promedio por linea: S/ {c['PRECIO_NETO'].mean():.2f}")
print(f"   Costo promedio por atencion (de las que tienen consumo): "
      f"S/ {c.groupby('CODiGO_ATENCION')['PRECIO_NETO'].sum().mean():.2f}")
print("   --> Comparar con FISSAL: ahi el costo mediano por paciente Track A")
print("       regular es de miles de soles. Este archivo de consumos SIS")
print("       parece capturar solo items puntuales (ej. 'Dosaje de creatinina'")
print("       S/3.5, 'Cuidados hospitalarios iniciales' S/16.75), NO la")
print("       facturacion completa de cirugia/quimio/radio/hospitalizacion.")
print("       No es comparable como medida de costo total del episodio.")

n_atenc_con_consumo = c["CODiGO_ATENCION"].nunique()
n_atenc_total = a["CODIGO_ATENCION"].nunique()
print(f"\n   Atenciones con al menos 1 consumo: {n_atenc_con_consumo:,} de {n_atenc_total:,} "
      f"({n_atenc_con_consumo/n_atenc_total*100:.1f}%)")

# =====================================================================
# 3. GUARDAR
# =====================================================================
a.to_parquet(OUTPUT / "sis_atenciones.parquet", index=False)
c.to_parquet(OUTPUT / "sis_consumos.parquet", index=False)
print(f"\n3. Guardado en {OUTPUT}")
print("\nFin de exploracion.")
