"""
Punto 1: "de cada 100 horas de trabajo, cuantas se pierden y por que razon"
-- version construida con microdatos reales de ENUT 2024 (no con la tesis de
una sola empresa ni con cifras de Adecco/OIT de una encuesta de terceros, como
en el primer intento -- ver 00_analisis_previo_metodologia.md seccion 1).

LO QUE FALTABA (y por que este script lo resuelve): se necesitaba una fuente
peruana que preguntara, con una muestra representativa, "por que no trabajaste
tu semana normal de horas" con una categoria de salud separada de las demas.
Sin darnos cuenta, la ENUT que ya estabamos usando para el punto 2.B (cuidador
informal) TIENE exactamente esa pregunta -- dos, de hecho:

  P707A (semana COMPLETA de ausencia, para quien tiene trabajo pero no
         trabajo nada esa semana): 12 categorias, incluye "3. Enfermedad,
         dolencia, accidente" y "6. Otra licencia personal (cuidar familia)"
  P732  (semana PARCIAL: trabajo, pero menos horas de las normales): 9
         categorias, incluye "7. Por salud, enfermedad, accidente, licencia
         de salud"

Con estas dos preguntas + las horas normales (P731) y las horas efectivamente
trabajadas (P718_T + P728_T) se puede construir la cascada real: de cada 100
horas normales de trabajo de la PEA ocupada, cuantas se pierden en la semana
de referencia, y por que motivo -- separando salud del resto.

Limitacion honesta: esto es UNA semana de referencia (la semana antes de la
encuesta), no un promedio anual -- puede haber estacionalidad (ej. menos
licencias de salud en la semana particular en que se levanto la encuesta que
en otra). Para un numero anual mas robusto habria que promediar varias
semanas/trimestres de la EPEN, que no tenemos en este extracto. Aun asi, es
un dato real y trazable, mejor que una cifra de una tesis de una sola empresa.
"""
import pandas as pd
from pathlib import Path

BASE = Path(
    r"C:\Users\eah\apoyoconsultoria.com\File Server - Analytics\3 Proyectos\2025"
    r"\2025-116-L FPC Dashboard 25\4 Analisis\2 Bases trabajadas\Adicional 2026 - ENUT"
)
OUTPUT = Path(__file__).parent / "output"
OUTPUT.mkdir(exist_ok=True)

KEYS = ["ID", "CONG", "NSELV", "HOGAR", "P201"]
KEY_DTYPES = {k: str for k in KEYS}

COLS = KEYS + [
    "P703", "P704", "P705", "P707A", "P710",
    "P718_T", "P728_T", "P730", "P731", "P732",
    "FACTORFINAL",
]

print("=" * 70)
print("Cascada de 100 horas -- ausentismo laboral ENUT 2024 (semana de referencia)")
print("=" * 70)

# =====================================================================
# 1. CARGA Y UNIVERSO: personas con empleo esa semana (trabajaron o tienen
#    trabajo/negocio al que van a volver)
# =====================================================================
print("\n1. Cargando y filtrando personas 'con empleo' (P703==1, o P703==2 con")
print("   P704==1 o P705==1)...")

df = pd.read_csv(BASE / "V_ENUT2024_700_800_900.csv", usecols=COLS,
                  dtype=KEY_DTYPES, encoding="latin-1")
for c in ["P703", "P704", "P705", "P707A", "P710", "P718_T", "P728_T", "P730",
          "P731", "P732", "FACTORFINAL"]:
    df[c] = pd.to_numeric(df[c], errors="coerce")

tiene_empleo = (df["P703"] == 1) | ((df["P703"] == 2) & ((df["P704"] == 1) | (df["P705"] == 1)))
d = df[tiene_empleo].copy()

print(f"   Personas con empleo en la muestra: {len(d):,}")
print(f"   Poblacion estimada (factor de expansion): {d['FACTORFINAL'].sum():,.0f}")

print("\n   AVISO: la primera corrida (incluyendo independientes/informales, cuyas")
print("   'horas normales' declaradas son muy variables semana a semana) daba una")
print("   perdida implausible de ~35 de cada 100 horas. Se acota la poblacion a")
print("   EMPLEADO U OBRERO dependiente (P710==3) -- la base estandar de las")
print("   estadisticas de ausentismo laboral -- para un numero mas creible.")
d = d[d["P710"] == 3].copy()
print(f"   Personas empleado/obrero dependiente en la muestra: {len(d):,}")
print(f"   Poblacion estimada: {d['FACTORFINAL'].sum():,.0f}")

# =====================================================================
# 2. HORAS PERDIDAS Y MOTIVO, POR CASO
# =====================================================================
print("\n2. Calculando horas perdidas respecto a la jornada normal (P731)...")

print("\n   NOTA IMPORTANTE (bug corregido): P731 (horas normales/semana) solo se")
print("   pregunta en el cuestionario cuando P730==2 ('no, no trabajo normalmente")
print("   esas horas'). Cuando P730==1, el cuestionario SALTA P731 porque las horas")
print("   normales son, por definicion, las mismas que trabajo esa semana (P718_T).")
print("   Rellenar P731 con 0 en ese caso (como se hizo en la primera version de este")
print("   script) diluia el denominador y disparaba la perdida total a ~35-36 de cada")
print("   100 horas -- un artefacto, no un hallazgo real. Se corrige imputando P731")
print("   = horas trabajadas cuando P730==1.")

horas_trabajadas = d[["P718_T", "P728_T"]].fillna(0).sum(axis=1)
d["HORAS_TRABAJADAS"] = horas_trabajadas

# Horas normales efectivas: P731 si esta poblado (P730==2), si no, = horas trabajadas esa semana (P730==1)
d["HORAS_NORMALES"] = d["P731"].fillna(d["HORAS_TRABAJADAS"])

d["HORAS_PERDIDAS"] = 0.0
d["MOTIVO_COD"] = pd.NA

# Caso A: ausente TODA la semana (P703==2, tiene empleo al que volver) -> pierde HORAS_NORMALES completo, motivo = P707A
mask_a = d["P703"] == 2
d.loc[mask_a, "HORAS_PERDIDAS"] = d.loc[mask_a, "HORAS_NORMALES"]
d.loc[mask_a, "MOTIVO_COD"] = d.loc[mask_a, "P707A"]

# Caso B: trabajo, pero menos horas de las normales (P703==1 & P730==2) -> pierde HORAS_NORMALES - horas_trabajadas, motivo = P732
mask_b = (d["P703"] == 1) & (d["P730"] == 2)
d.loc[mask_b, "HORAS_PERDIDAS"] = (d.loc[mask_b, "HORAS_NORMALES"] - d.loc[mask_b, "HORAS_TRABAJADAS"]).clip(lower=0)
d.loc[mask_b, "MOTIVO_COD"] = d.loc[mask_b, "P732"] + 100  # +100 para distinguir codigo de P732 vs P707A

# Caso C: trabajo su semana normal (P703==1 & P730==1) -> sin perdida, ya queda en 0.0

MOTIVOS_707A = {
    1: "Turno/horario flexible, naturaleza del trabajo", 2: "Vacaciones, feriados",
    3: "SALUD: enfermedad, dolencia, accidente", 4: "Licencia maternidad/paternidad",
    5: "Licencia por estudios/capacitacion", 6: "Otra licencia personal (cuidar familia)",
    7: "Suspension temporal, menos clientes", 8: "Mal clima, desastres naturales",
    9: "Huelga o conflicto laboral", 10: "Discapacidad de larga duracion",
    11: "Trabajo de temporada", 12: "Otro",
}
MOTIVOS_732 = {
    101: "Vacaciones o dias festivos", 102: "Falta de clientes/pedidos/financiamiento",
    103: "Su trabajo asi lo exige", 104: "Motivos personales o familiares",
    105: "Reduccion de jornada (produccion, clima, huelga)", 106: "Exceso de trabajo/clientes",
    107: "SALUD: enfermedad, accidente, licencia de salud", 108: "Estar de viaje/paseo",
    109: "Otro",
}
MOTIVOS = {**MOTIVOS_707A, **MOTIVOS_732}
d["MOTIVO"] = d["MOTIVO_COD"].map(MOTIVOS)

# =====================================================================
# 3. LA CASCADA: de cada 100 horas normales, cuantas se pierden y por que
# =====================================================================
print("\n3. Construyendo la cascada (ponderada por factor de expansion)...")

horas_normales_totales = (d["HORAS_NORMALES"] * d["FACTORFINAL"]).sum()
horas_perdidas_totales = (d["HORAS_PERDIDAS"] * d["FACTORFINAL"]).sum()

horas_normales_prom_persona = horas_normales_totales / d["FACTORFINAL"].sum()
horas_perdidas_prom_persona_anual = (horas_perdidas_totales / d["FACTORFINAL"].sum()) * 52

print(f"\n   Horas normales promedio por persona (semana): {horas_normales_prom_persona:.1f}")
print(f"   Horas normales totales (semana, poblacion expandida): {horas_normales_totales:,.0f}")
print(f"   Horas perdidas totales: {horas_perdidas_totales:,.0f}")
print(f"   -> De cada 100 horas normales de trabajo, se pierden "
      f"{horas_perdidas_totales/horas_normales_totales*100:.2f} horas en la semana de referencia")

d["HORAS_PERDIDAS_POND"] = d["HORAS_PERDIDAS"] * d["FACTORFINAL"]
cascada = d.groupby("MOTIVO", observed=True)["HORAS_PERDIDAS_POND"].sum().sort_values(ascending=False)
cascada_pct_de_100 = cascada / horas_normales_totales * 100

print("\n   Cascada por motivo (horas perdidas de cada 100 horas normales):")
tabla = pd.DataFrame({
    "horas_perdidas_de_cada_100": cascada_pct_de_100.round(3),
    "pct_del_total_perdido": (cascada / cascada.sum() * 100).round(1),
})
print(tabla.to_string())

horas_salud = cascada[cascada.index.str.startswith("SALUD", na=False)].sum()
pct_salud_de_100 = horas_salud / horas_normales_totales * 100
print(f"\n   SUBTOTAL SALUD (enfermedad/dolencia/accidente, ambas preguntas): "
      f"{pct_salud_de_100:.2f} de cada 100 horas")
print(f"   (para contexto: la estimacion anterior via Adecco/OIT daba ~2.8 de cada 100 -- "
      f"este numero, calculado directo de microdatos ENUT, es el que debería reemplazarla)")

# --- Traduccion a nivel de persona (horas/año, soles/año, meses de RMV) ---
SALARIO_HORA = 11.55  # de 01_explorar_enut_cuidadores.py
RMV_MENSUAL = 1130.0  # D.S. N.° 006-2024-TR

horas_salud_anuales_persona = (pct_salud_de_100 / 100) * horas_normales_prom_persona * 52
soles_salud_anuales_persona = horas_salud_anuales_persona * SALARIO_HORA
meses_rmv_salud = soles_salud_anuales_persona / RMV_MENSUAL

print(f"\n   TRADUCCION A NIVEL DE PERSONA (trabajador dependiente promedio, jornada")
print(f"   normal {horas_normales_prom_persona:.1f} h/semana):")
print(f"   Horas/año perdidas por salud: {horas_salud_anuales_persona:.1f} h/año "
      f"(~{horas_salud_anuales_persona/8:.1f} dias de 8h)")
print(f"   Valorizado a S/{SALARIO_HORA}/hora: S/ {soles_salud_anuales_persona:,.0f}/año")
print(f"   Equivalente en meses de RMV (S/{RMV_MENSUAL:.0f}): {meses_rmv_salud:.2f} meses")

# =====================================================================
# 3B. ADVERTENCIA METODOLOGICA + CASCADA "ESTRICTA" (solo ausencia involuntaria)
# =====================================================================
print("\n" + "=" * 70)
print("ADVERTENCIA: el 36% de perdida total (paso 3) NO es comparable a la cifra")
print("de ~5% de la literatura de ausentismo. Eso es porque mezcla categorias")
print("estructurales/planificadas (vacaciones, feriados, 'su trabajo asi lo exige',")
print("turno flexible, trabajo de temporada) con ausencia involuntaria real (salud,")
print("licencias, discapacidad, cuidado familiar). La cifra de ~5% de la literatura")
print("SOLO cuenta ausencia involuntaria. Por eso se calcula tambien una cascada")
print("'estricta' excluyendo lo planificado/estructural:")
print("=" * 70)

CATEGORIAS_INVOLUNTARIAS = {
    "SALUD: enfermedad, dolencia, accidente",
    "SALUD: enfermedad, accidente, licencia de salud",
    "Licencia maternidad/paternidad",
    "Licencia por estudios/capacitacion",
    "Otra licencia personal (cuidar familia)",
    "Discapacidad de larga duracion",
    "Motivos personales o familiares",
    "Suspension temporal, menos clientes",
    "Falta de clientes/pedidos/financiamiento",
}
cascada_estricta = cascada[cascada.index.isin(CATEGORIAS_INVOLUNTARIAS)]
pct_estricta_de_100 = cascada_estricta.sum() / horas_normales_totales * 100

print(f"\n   Cascada ESTRICTA (solo ausencia involuntaria, excluye vacaciones/feriados/")
print(f"   flexibilidad/estacionalidad):")
tabla_estricta = (cascada_estricta / horas_normales_totales * 100).round(3).sort_values(ascending=False)
print(tabla_estricta.to_string())
print(f"\n   TOTAL ESTRICTO: {pct_estricta_de_100:.2f} de cada 100 horas normales")
print(f"   (de las cuales {pct_salud_de_100:.2f} son por salud -- {pct_salud_de_100/pct_estricta_de_100*100:.0f}% del total estricto)")
print(f"   Esta cifra SI es comparable con el ~5% de dias perdidos/año de la literatura")
print(f"   internacional de ausentismo (aunque mide semanas, no dias, y es de una sola")
print(f"   semana de referencia, no un promedio anual robusto).")

# =====================================================================
# 4. GUARDAR
# =====================================================================
tabla.to_csv(OUTPUT / "cascada_ausentismo_horas.csv")
print(f"\n4. Guardado en {OUTPUT / 'cascada_ausentismo_horas.csv'}")
print("\nFin.")
