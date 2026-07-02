import sys
import pandas as pd
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SILVER = Path(r"C:\Users\eah\apoyoconsultoria.com\File Server - Analytics\7 Datos\Datos abiertos\fissal\01_silver")
SALIDA = SILVER.parent / "03_output" / "hitos_paciente"
SALIDA.mkdir(parents=True, exist_ok=True)

print("=" * 70)
print("EXPORTANDO TABLAS DE HITOS PARA POWER BI")
print("=" * 70)
print("""
Genera 2 CSV listos para importar a Power BI:
  - hitos_paciente.csv : 1 fila por paciente (tabla ancha, para tarjetas/
    segmentadores y para relacionar con otras tablas por NUM_DOC_CRYPTO)
  - hitos_eventos.csv  : 1 fila por paciente x hito (formato largo, ideal
    para un grafico de linea de tiempo / Gantt o un grafico de barras
    comparando costo o duracion ENTRE hitos)
Sugerencia de modelo en Power BI: cargar ambas tablas y relacionarlas 1-a-N
por NUM_DOC_CRYPTO (hitos_paciente = 1, hitos_eventos = N). El campo HITO
de hitos_eventos.csv sirve como eje/leyenda en visuales comparativos.
""")

hp = pd.read_parquet(SILVER / "FISSAL_CCR_HITOS_PACIENTE.parquet")
ev = pd.read_parquet(SILVER / "FISSAL_CCR_HITOS_EVENTOS.parquet")

# Columnas de fecha a formato ISO simple (Power BI las detecta solas)
for df_ in (hp, ev):
    cols_fecha = [c for c in df_.columns if pd.api.types.is_datetime64_any_dtype(df_[c])]
    for col in cols_fecha:
        df_[col] = df_[col].dt.strftime("%Y-%m-%d")

salida_pac = SALIDA / "hitos_paciente.csv"
salida_ev = SALIDA / "hitos_eventos.csv"
hp.to_csv(salida_pac, index=False, encoding="utf-8-sig")
ev.to_csv(salida_ev, index=False, encoding="utf-8-sig")

print(f"  Guardado: {salida_pac}  ({len(hp):,} filas x {hp.shape[1]} columnas)")
print(f"  Guardado: {salida_ev}  ({len(ev):,} filas x {ev.shape[1]} columnas)")
print("\nFin.")
