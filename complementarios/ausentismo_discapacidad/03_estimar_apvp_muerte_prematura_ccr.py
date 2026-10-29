"""
Punto 2.A: perdida de productividad por muerte prematura de CCR en Peru, con el
metodo del capital humano (ECH) / anios potenciales de vida productiva perdidos
(APVP), version simple: edad de jubilacion fija en 65 anios (sin escenario "+5
anios" de jubilacion efectiva informal -- se dejo fuera a pedido de Estela para
mantenerlo comparable 1 a 1 con el benchmark sudamericano).

Formula (siguiendo a Mosegui et al. 2023, "Perdida de Productividad Atribuida a
Neoplasias en America del Sur", Rev Bras Cancerologia -- ver
00_analisis_previo_metodologia.md seccion 2.A):

  APVP_persona   = max(0, edad_jubilacion - edad_muerte)   si edad_muerte < 65, si no 0
  VP_persona     = ingreso_anual x [(1 - (1+r)^-APVP) / r]   (valor presente de esos
                                                               años de sueldo, tasa r=3%)
  costo_persona  = VP_persona x tasa_actividad x tasa_empleo
  costo_total    = suma de costo_persona para todas las muertes CCR del año

tasa_actividad, tasa_empleo e ingreso vienen de los cuadros EPEN de INEI ya
descargados (output/inei_epen/), son nacionales (no por sexo ni edad -- version
simple). El benchmark sudamericano (Mosegui et al.) usa salario MINIMO; aqui se
usa el ingreso PROMEDIO de INEI, que es mas alto y mas realista -- por eso el
costo por muerte deberia salir mayor al benchmark, no hay que alarmarse si asi es.

Fuente de mortalidad: SINADEF (registro civil de defunciones), NO FISSAL -- SINADEF
cubre a todo el pais (SIS, EsSalud, privados), FISSAL solo a la poblacion SIS.
"""
import pandas as pd
import numpy as np
from pathlib import Path

SINADEF_CSV = Path(
    r"C:\Users\eah\apoyoconsultoria.com\File Server - Analytics\7 Datos\Datos abiertos"
    r"\sinadef\SINADEF_DATOS_ABIERTOS.csv"
)
EPEN_DIR = Path(__file__).parent / "output" / "inei_epen"
OUTPUT = Path(__file__).parent / "output"
OUTPUT.mkdir(exist_ok=True)

ANIO = 2025  # ultimo anio completo disponible tanto en SINADEF como en los cuadros EPEN
EDAD_JUBILACION = 65
TASA_DESCUENTO = 0.03
TIPO_CAMBIO_REF = 3.75  # soles por USD, referencial, solo para comparar con el benchmark en USD

CAUSAS_CCR = ("C18", "C19", "C20")
CIEX_COLS = ["CAUSA_A_CIEX", "CAUSA_B_CIEX", "CAUSA_C_CIEX", "CAUSA_D_CIEX", "CAUSA_E_CIEX", "CAUSA_F_CIEX"]

# Benchmark sudamericano (Mosegui et al. 2023), Peru, 2019, TODOS los canceres, 15-69 anios,
# salario MINIMO, descuento 3%, jubilacion 65 -- ver 00_analisis_previo_metodologia.md
BENCHMARK_PERU_2019 = {
    "muertes_15_69": 6840 + 4949,
    "apvp_total": (8650.80 + 88613.20) + (12447.42 + 61485.52),
    "costo_total_nominal_usd": 181_323_126.60 + 185_814_563.83,
    "costo_por_muerte_usd": 31_142.39,
}

print("=" * 70)
print(f"APVP y perdida de productividad -- muerte prematura por CCR, Peru {ANIO}")
print("=" * 70)

# =====================================================================
# 1. INSUMOS ECONOMICOS (EPEN, ya descargados)
# =====================================================================
print("\n1. Cargando insumos EPEN (INEI)...")


def leer_total_epen(archivo, anio):
    df = pd.read_excel(EPEN_DIR / archivo, header=None)
    fila_anios = df[df.iloc[:, 0].astype(str).str.contains("Área de residencia", na=False)].index[0]
    anios = df.iloc[fila_anios, 1:].tolist()
    fila_total = df[df.iloc[:, 0].astype(str).str.strip() == "Total"].index[0]
    valores = df.iloc[fila_total, 1:].tolist()
    d = dict(zip([int(a) for a in anios], valores))
    return d[anio]


tasa_actividad = leer_total_epen("tasa-cuad-1_8.xlsx", ANIO) / 100
tasa_desempleo = leer_total_epen("desem-cuad-1_6.xlsx", ANIO) / 100
tasa_empleo = 1 - tasa_desempleo
ingreso_promedio_mensual = leer_total_epen("ing-cuad-1_8.xlsx", ANIO)
ingreso_anual = ingreso_promedio_mensual * 12

print(f"   Tasa de actividad (PEA/PET) {ANIO}: {tasa_actividad:.2%}")
print(f"   Tasa de empleo (1 - desempleo) {ANIO}: {tasa_empleo:.2%}")
print(f"   Ingreso promedio mensual {ANIO}: S/ {ingreso_promedio_mensual:,.2f}  (anual: S/ {ingreso_anual:,.2f})")

# =====================================================================
# 2. MORTALIDAD CCR (SINADEF)
# =====================================================================
print(f"\n2. Cargando SINADEF y filtrando muertes CCR (C18-C20) del año {ANIO}...")
cols = ["SEXO", "TIEMPO_EDAD", "EDAD", "ANIO"] + CIEX_COLS
df = pd.read_csv(SINADEF_CSV, usecols=cols)

mask_ccr = pd.Series(False, index=df.index)
for c in CIEX_COLS:
    mask_ccr = mask_ccr | df[c].astype(str).str.upper().str.startswith(CAUSAS_CCR, na=False)

ccr = df[mask_ccr & (df["ANIO"] == ANIO) & (df["TIEMPO_EDAD"] == "AÑOS")].copy()
ccr["EDAD"] = pd.to_numeric(ccr["EDAD"], errors="coerce")
ccr = ccr.dropna(subset=["EDAD"])

print(f"   Muertes CCR {ANIO} (con edad en años): {len(ccr):,}")
print(f"   Edad mediana: {ccr['EDAD'].median():.0f} años | Edad promedio: {ccr['EDAD'].mean():.1f} años")

ccr_bajo65 = ccr[ccr["EDAD"] < EDAD_JUBILACION].copy()
print(f"   Muertes antes de los {EDAD_JUBILACION} años (las únicas que generan APVP > 0): "
      f"{len(ccr_bajo65):,} de {len(ccr):,} ({len(ccr_bajo65)/len(ccr)*100:.1f}%)")

# =====================================================================
# 3. APVP Y VALOR PRESENTE POR PERSONA
# =====================================================================
print("\n3. Calculando APVP y valor presente del ingreso perdido por persona...")

ccr_bajo65["APVP"] = EDAD_JUBILACION - ccr_bajo65["EDAD"]


def valor_presente_anualidad(n_anios, monto_anual, tasa=TASA_DESCUENTO):
    n_anios = np.asarray(n_anios, dtype=float)
    factor = (1 - (1 + tasa) ** (-n_anios)) / tasa
    return monto_anual * factor


ccr_bajo65["VALOR_PRESENTE_INGRESO"] = valor_presente_anualidad(ccr_bajo65["APVP"], ingreso_anual)
ccr_bajo65["COSTO_PRODUCTIVIDAD"] = ccr_bajo65["VALOR_PRESENTE_INGRESO"] * tasa_actividad * tasa_empleo

apvp_total = ccr_bajo65["APVP"].sum()
costo_total = ccr_bajo65["COSTO_PRODUCTIVIDAD"].sum()
costo_total_sin_descuento = (ccr_bajo65["APVP"] * ingreso_anual * tasa_actividad * tasa_empleo).sum()
n_muertes = len(ccr_bajo65)
costo_por_muerte = costo_total / n_muertes if n_muertes else 0

print(f"   APVP total (suma de años potenciales de vida productiva perdidos): {apvp_total:,.0f} años")
print(f"   Costo total CON descuento 3% (valor presente): S/ {costo_total:,.0f}")
print(f"   Costo total SIN descuento (referencia, sobreestima): S/ {costo_total_sin_descuento:,.0f}")
print(f"   Costo por muerte (con descuento): S/ {costo_por_muerte:,.0f}  "
      f"(~US$ {costo_por_muerte/TIPO_CAMBIO_REF:,.0f} a T.C. {TIPO_CAMBIO_REF})")

print("\n   Por sexo:")
for sexo in ["FEMENINO", "MASCULINO"]:
    sub = ccr_bajo65[ccr_bajo65["SEXO"] == sexo]
    if len(sub):
        print(f"     {sexo}: {len(sub):,} muertes, APVP={sub['APVP'].sum():,.0f}, "
              f"costo=S/ {sub['COSTO_PRODUCTIVIDAD'].sum():,.0f}, "
              f"costo/muerte=S/ {sub['COSTO_PRODUCTIVIDAD'].sum()/len(sub):,.0f}")

# =====================================================================
# 4. COMPARACION CON EL BENCHMARK SUDAMERICANO (Mosegui et al. 2023, Peru 2019, todos los canceres)
# =====================================================================
print("\n4. Comparación con el benchmark sudamericano (Mosegui et al. 2023):")
print(f"   Benchmark Perú 2019 (TODOS los cánceres, salario mínimo):")
print(f"     Muertes 15-69: {BENCHMARK_PERU_2019['muertes_15_69']:,}")
print(f"     APVP total: {BENCHMARK_PERU_2019['apvp_total']:,.0f} años")
print(f"     Costo total: US$ {BENCHMARK_PERU_2019['costo_total_nominal_usd']:,.0f}")
print(f"     Costo por muerte: US$ {BENCHMARK_PERU_2019['costo_por_muerte_usd']:,.0f}")

print(f"\n   Este cálculo, SOLO CCR, {ANIO} (ingreso promedio, no mínimo):")
print(f"     Muertes <65 años: {n_muertes:,}")
print(f"     APVP total: {apvp_total:,.0f} años")
print(f"     Costo total: US$ {costo_total/TIPO_CAMBIO_REF:,.0f}")
print(f"     Costo por muerte: US$ {costo_por_muerte/TIPO_CAMBIO_REF:,.0f}")

pct_muertes_ccr_del_total_cancer = n_muertes / BENCHMARK_PERU_2019["muertes_15_69"] * 100
print(f"\n   CCR representa el {pct_muertes_ccr_del_total_cancer:.1f}% de las muertes por cáncer en edad")
print(f"   laboral del benchmark 2019 -- como referencia (el benchmark es de todos los cánceres,")
print(f"   este cálculo es solo CCR, y son años distintos -- no son directamente comparables 1 a 1,")
print(f"   pero el orden de magnitud debería ser razonable frente a ese {pct_muertes_ccr_del_total_cancer:.0f}%.")
print(f"   El costo/muerte de este cálculo sale más alto que el benchmark porque usa ingreso PROMEDIO")
print(f"   de INEI (S/ {ingreso_promedio_mensual:,.0f}/mes) en vez de salario MÍNIMO -- es esperable y")
print(f"   más realista, no es un error.")

# =====================================================================
# 5. GUARDAR
# =====================================================================
resumen = pd.DataFrame([{
    "anio": ANIO,
    "muertes_ccr_totales": len(ccr),
    "muertes_ccr_bajo_65": n_muertes,
    "apvp_total_anios": apvp_total,
    "costo_total_soles_con_descuento": costo_total,
    "costo_total_soles_sin_descuento": costo_total_sin_descuento,
    "costo_por_muerte_soles": costo_por_muerte,
    "tasa_actividad": tasa_actividad,
    "tasa_empleo": tasa_empleo,
    "ingreso_promedio_mensual_soles": ingreso_promedio_mensual,
}])
resumen.to_csv(OUTPUT / "ccr_apvp_muerte_prematura_resumen.csv", index=False)
ccr_bajo65.to_csv(OUTPUT / "ccr_apvp_muerte_prematura_detalle.csv", index=False)
print(f"\n5. Guardado en {OUTPUT}")
print("\nFin.")
