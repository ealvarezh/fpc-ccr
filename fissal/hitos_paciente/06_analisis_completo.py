import pandas as pd
import numpy as np
from pathlib import Path
import gc

SILVER = Path(r"C:\Users\eah\apoyoconsultoria.com\File Server - Analytics\7 Datos\Datos abiertos\fissal\01_silver")

print("Cargando datos...")
hitos = pd.read_parquet(SILVER / "FISSAL_CCR_HITOS_PACIENTE.parquet")
perfil = pd.read_parquet(SILVER / "FISSAL_CCR_PERFIL_PACIENTES.parquet")

# Mergear lo necesario (hitos ya tiene MONTO_NETO_TOTAL y MONTO_BRUTO_TOTAL)
cols_p = ["NUM_DOC_CRYPTO", "N_ATENCIONES", "N_PRESTACIONES",
          "TIEMPO_EN_SISTEMA_DIAS", "TUVO_CIRUGIA", "TUVO_QUIMIOTERAPIA", "TUVO_HOSPITALIZACION"]
df = hitos.merge(perfil[cols_p], on="NUM_DOC_CRYPTO", how="left")

N_TOTAL = len(df)

# =================================================================
# 1. COSTO POR RANGO DE TIEMPO EN SISTEMA
# =================================================================
print("\n" + "=" * 70)
print("1. COSTO SEGUN TIEMPO EN SISTEMA")
print("=" * 70)

bins_t = [0, 1, 30, 90, 180, 365, 730, 99999]
labels_t = ["0-1 dia", "1-30 dias", "30-90 dias", "90-180 dias", "180d-1a", "1-2a", "2a+"]
df["RANGO_TIEMPO"] = pd.cut(df["TIEMPO_EN_SISTEMA_DIAS"].fillna(0), bins=bins_t, labels=labels_t, right=True)

print(f"\n{'Rango':>15s} {'n':>7s} {'At. med':>8s} {'Costo med':>12s} {'Costo media':>13s} {'P95':>12s} {'Max':>14s}")
print("-" * 85)
for r in labels_t:
    sub = df[df["RANGO_TIEMPO"] == r]
    if len(sub) == 0:
        continue
    at_med = sub["N_ATENCIONES"].median()
    c_med = sub["MONTO_NETO_TOTAL"].median()
    c_mean = sub["MONTO_NETO_TOTAL"].mean()
    c_p95 = sub["MONTO_NETO_TOTAL"].quantile(0.95)
    c_max = sub["MONTO_NETO_TOTAL"].max()
    print(f"{r:>15s} {len(sub):>7,} {at_med:>8.0f} S/{c_med:>10,.0f} S/{c_mean:>11,.0f} S/{c_p95:>10,.0f} S/{c_max:>12,.0f}")

# =================================================================
# 2. DISTRIBUCION DE ATENCIONES
# =================================================================
print("\n" + "=" * 70)
print("2. PACIENTES POR CANTIDAD DE ATENCIONES")
print("=" * 70)

bins_a = [0, 1, 2, 3, 5, 10, 20, 50, 99999]
labels_a = ["1", "2", "3-4", "5-9", "10-19", "20-49", "50-99", "100+"]
df["RANGO_AT"] = pd.cut(df["N_ATENCIONES"].fillna(0), bins=bins_a, labels=labels_a, right=True)

print(f"\n{'Atenciones':>12s} {'n':>7s} {'%':>7s} {'% acum':>8s} {'Costo med':>12s} {'Con trat':>9s}")
print("-" * 60)
cum = 0
for r in labels_a:
    sub = df[df["RANGO_AT"] == r]
    n = len(sub)
    pct = n / N_TOTAL * 100
    cum += pct
    c_med = sub["MONTO_NETO_TOTAL"].median()
    pct_trat = (sub["SECUENCIA_TRATAMIENTO"] != "SIN_TRATAMIENTO_DETECTADO").mean() * 100
    print(f"{r:>12s} {n:>7,} {pct:>6.1f}% {cum:>7.1f}% S/{c_med:>10,.0f} {pct_trat:>8.1f}%")

# =================================================================
# 3. FILTRANDO: SOLO PACIENTES FISSAL REALES
# =================================================================
print("\n" + "=" * 70)
print("3. APLICANDO FILTROS DE 'COMPROMISO REAL' CON FISSAL")
print("=" * 70)

filtros = [
    ("Todos los pacientes", df),
    (">= 2 atenciones (descartan los de 1 sola visita)", df[df["N_ATENCIONES"] >= 2]),
    (">= 3 atenciones", df[df["N_ATENCIONES"] >= 3]),
    (">= 5 atenciones", df[df["N_ATENCIONES"] >= 5]),
    (">= 3 atenciones + con tratamiento detectado", df[(df["N_ATENCIONES"] >= 3) & (df["SECUENCIA_TRATAMIENTO"] != "SIN_TRATAMIENTO_DETECTADO")]),
    (">= 5 atenciones + con tratamiento detectado", df[(df["N_ATENCIONES"] >= 5) & (df["SECUENCIA_TRATAMIENTO"] != "SIN_TRATAMIENTO_DETECTADO")]),
]

print(f"\n{'Filtro':<55s} {'n':>7s} {'%':>6s} {'Costo med':>12s} {'Costo media':>13s} {'At med':>7s} {'Tpo med(d)':>10s}")
print("-" * 115)
for nombre, sub in filtros:
    n = len(sub)
    c_med = sub["MONTO_NETO_TOTAL"].median()
    c_mean = sub["MONTO_NETO_TOTAL"].mean()
    at_med = sub["N_ATENCIONES"].median()
    t_med = sub["TIEMPO_EN_SISTEMA_DIAS"].median()
    print(f"{nombre:<55s} {n:>7,} {n/N_TOTAL*100:>5.1f}% S/{c_med:>10,.0f} S/{c_mean:>11,.0f} {at_med:>7.0f} {t_med:>10.0f}")

# =================================================================
# 4. RUIDO: ALTO COSTO CON POCAS ATENCIONES
# =================================================================
print("\n" + "=" * 70)
print("4. RUIDO: PACIENTES CON <=2 ATENCIONES Y COSTO ALTO (top 10)")
print("=" * 70)

ruido = df[df["N_ATENCIONES"] <= 2].nlargest(10, "MONTO_NETO_TOTAL")
for _, row in ruido.iterrows():
    print(f"  at={int(row['N_ATENCIONES'])}  t={int(row['TIEMPO_EN_SISTEMA_DIAS'])}d  "
          f"S/{row['MONTO_NETO_TOTAL']:>12,.0f}  desenlace={row['DESENLACE']}  "
          f"trat={row['SECUENCIA_TRATAMIENTO']}")

# =================================================================
# 5. COMORBILIDADES: TODOS LOS CIE-10 DE PACIENTES CCR
# =================================================================
print("\n" + "=" * 70)
print("5. COMORBILIDADES: TODOS LOS DIAGNOSTICOS DE PACIENTES CCR")
print("=" * 70)

pac_ccr = set(df["NUM_DOC_CRYPTO"])
print(f"Buscando en archivos anuales completos para {len(pac_ccr):,} pacientes...")

# Contar CIE-10 por paciente (todos los codigos, no solo C18/19/20)
cie_counts = {}
for yr in range(2016, 2023):
    archivo = SILVER / f"FISSAL_PRESTACIONES_{yr}.parquet"
    if not archivo.exists():
        continue
    print(f"  {yr}...", end=" ")
    yr_df = pd.read_parquet(archivo, columns=["NUM_DOC_CRYPTO", "ATE_CODCIE10"])
    yr_df = yr_df[yr_df["NUM_DOC_CRYPTO"].isin(pac_ccr)]
    for cie, n in yr_df["ATE_CODCIE10"].value_counts().items():
        cie_counts[cie] = cie_counts.get(cie, 0) + n
    del yr_df
    gc.collect()
    print(f"OK")

cie_series = pd.Series(cie_counts).sort_values(ascending=False)
n_unicos = len(cie_series)
print(f"\n  Codigos CIE-10 unicos encontrados: {n_unicos:,}")

# Top 30 mas frecuentes (excluyendo C18/C19/C20)
PATRON_CCR = r"^C(18|19|20)"
cie_no_ccr = cie_series[~cie_series.index.str.contains(PATRON_CCR, na=False)]
print(f"\n  Top 30 diagnosticos NO-CCR mas frecuentes:")
for cie, n in cie_no_ccr.head(30).items():
    n_pac = 0  # dificil de calcular sin recargar data, aproximamos
    pct = n / N_TOTAL
    print(f"    {cie:>8s}: {n:>8,} registros ({pct:.1f} por paciente)")

# Agrupar por capitulo CIE-10
cie_series.index = cie_series.index.astype(str)
capitulos = cie_series.groupby(lambda x: x[0]).sum().sort_values(ascending=False)
print(f"\n  Distribucion por CAPITULO CIE-10:")
desc_capitulos = {
    "A": "A-B: Infecciosas y parasitarias",
    "C": "C: Neoplasias (tumores)",
    "D": "D: Neoplasias in situ/benignas",
    "E": "E: Endocrinas/metabolicas",
    "F": "F: Trastornos mentales",
    "G": "G: Sistema nervioso",
    "H": "H: Ojo/oido",
    "I": "I: Circulatorias",
    "J": "J: Respiratorias",
    "K": "K: Digestivas",
    "L": "L: Piel",
    "M": "M: Musculoesqueleticas",
    "N": "N: Genitourinarias",
    "O": "O: Embarazo/parto",
    "R": "R: Sintomas/signos",
    "S": "S-T: Traumatismos",
    "Z": "Z: Factores de influencia en salud",
}
for cap, n in capitulos.items():
    desc = desc_capitulos.get(cap, f"{cap}: Otras")
    pct = n / cie_series.sum() * 100
    print(f"    {cap}: {desc:<40s} {n:>10,} reg ({pct:>5.1f}%)")

print("\nFin del analisis.")
