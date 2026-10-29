"""
Exploracion inicial de ENUT 2024 (Encuesta Nacional de Uso del Tiempo, INEI) para
el punto "perdida de productividad por discapacidad o muerte prematura" del informe,
componente 2.B: cuidador informal.

IMPORTANTE - lo que este script NO hace: no aisla cancer. ENUT no pregunta el
diagnostico de la persona cuidada (ver 00_analisis_previo_metodologia.md, seccion 2.B
y el hallazgo sobre ENDES: ninguna encuesta de hogares peruana identifica cancer a
nivel de hogar). Lo que SI permite ENUT es identificar, a nivel nacional, a personas
que dejaron de trabajar o estudiar por cuidar a un integrante del hogar (P756==7 y
P770==10), y estimar cuanto ganarian esas personas si trabajaran (comparando con
personas similares que si trabajan). Esta es una cota general del "costo de
oportunidad de cuidar", no especifica a CCR -- el numero final del informe tendria
que aplicarle algun factor de FISSAL (ej. proporcion de pacientes CCR con cuidador
familiar directo) si se quiere bajar de "cuidado en general" a "cuidado por cancer".

Fuente de datos (no versionada en git, ruta local del usuario):
  C:\\Users\\eah\\apoyoconsultoria.com\\File Server - Analytics\\3 Proyectos\\2025\\
  2025-116-L FPC Dashboard 25\\4 Analisis\\2 Bases trabajadas\\Adicional 2026 - ENUT

Variables clave usadas (ver 04_DICCIONARIO_ENUT_2024.pdf):
  P756 (700_800_900): "Por que no busco trabajo" -- 7 = "Se dedica al cuidado de un
      miembro del hogar", 8 = "Razones de salud"
  P770 (700_800_900): "Por que no asiste a un centro de estudios" -- 10 = misma razon
      de cuidado
  P731 (700_800_900): horas normales trabajadas a la semana (ocupados)
  P738/P739_1 (700_800_900): frecuencia de pago / monto de ingreso (dependientes)
  P742 (700_800_900): ganancia neta mensual (independientes)
  P204/P205_A (200): sexo / edad de cada miembro del hogar
  FACTORFINAL: factor de expansion muestral (para estimaciones poblacionales)
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

print("=" * 70)
print("ENUT 2024 -- exploracion de cuidadores informales (no especifico a CCR)")
print("=" * 70)

# =====================================================================
# 1. CARGA
# =====================================================================
print("\n1. Cargando archivos...")
KEY_DTYPES = {k: str for k in KEYS}

personas = pd.read_csv(
    BASE / "V_ENUT2024_200.csv",
    usecols=KEYS + ["P203", "P204", "P205_A", "P209", "P210"],
    dtype=KEY_DTYPES,
    encoding="latin-1",
)
empleo = pd.read_csv(
    BASE / "V_ENUT2024_700_800_900.csv",
    usecols=KEYS
    + ["P756", "P770", "P703", "P731", "P738", "P739_1", "P742", "P742_F", "FACTORFINAL"],
    dtype=KEY_DTYPES,
    encoding="latin-1",
)
print(f"   Personas (cap 200): {len(personas):,}")
print(f"   Empleo/salud (cap 700-900): {len(empleo):,}")

for k in KEYS:
    personas[k] = personas[k].astype(str).str.strip()
    empleo[k] = empleo[k].astype(str).str.strip()

dup = personas.duplicated(subset=KEYS).sum()
if dup:
    print(f"   AVISO: {dup} duplicados en cap 200 por llave {KEYS} -- se descartan")
    personas = personas.drop_duplicates(subset=KEYS)

df = empleo.merge(personas, on=KEYS, how="left")
print(f"   Merge: {len(df):,} personas (deberia calzar con cap 700-900)")
print(f"   Sin match en cap 200: {df['P204'].isna().sum():,}")

NUMERIC_COLS = [
    "P756", "P770", "P703", "P731", "P738", "P739_1", "P742", "P742_F",
    "FACTORFINAL", "P204", "P205_A", "P209", "P210",
]
for c in NUMERIC_COLS:
    df[c] = pd.to_numeric(df[c], errors="coerce")

# =====================================================================
# 2. IDENTIFICAR CUIDADORES (no trabajan / no estudian por cuidar a alguien del hogar)
# =====================================================================
print("\n2. Identificando personas que no trabajan o no estudian por cuidar a un")
print("   integrante del hogar (P756==7 o P770==10)...")

df["ES_CUIDADOR_NO_TRABAJA"] = df["P756"] == 7
df["ES_CUIDADOR_NO_ESTUDIA"] = df["P770"] == 10
df["ES_CUIDADOR"] = df["ES_CUIDADOR_NO_TRABAJA"] | df["ES_CUIDADOR_NO_ESTUDIA"]

n_cuidadores = df["ES_CUIDADOR"].sum()
pob_cuidadores = df.loc[df["ES_CUIDADOR"], "FACTORFINAL"].sum()
pob_total = df["FACTORFINAL"].sum()

print(f"   Casos en la muestra: {n_cuidadores:,} de {len(df):,}")
print(f"   Poblacion estimada (factor de expansion): {pob_cuidadores:,.0f} de {pob_total:,.0f}")
print(f"   Proporcion de la poblacion 12+ años: {pob_cuidadores/pob_total*100:.2f}%")

print("\n   Por sexo (1=Hombre, 2=Mujer):")
tab_sexo = df[df["ES_CUIDADOR"]].groupby("P204")["FACTORFINAL"].sum()
print(tab_sexo.to_string())
print(f"   -> {(tab_sexo.get(2, 0) / tab_sexo.sum() * 100):.1f}% de los cuidadores identificados son mujeres")

bins_edad = [0, 18, 30, 45, 60, 75, 120]
labels_edad = ["12-17", "18-29", "30-44", "45-59", "60-74", "75+"]
df["GRUPO_EDAD"] = pd.cut(df["P205_A"], bins=bins_edad, labels=labels_edad, right=False)
print("\n   Por grupo de edad:")
tab_edad = df[df["ES_CUIDADOR"]].groupby("GRUPO_EDAD", observed=True)["FACTORFINAL"].sum()
print(tab_edad.to_string())

# =====================================================================
# 3. ESTIMAR SALARIO DE REFERENCIA (para valorizar el tiempo de cuidado)
# =====================================================================
print("\n3. Estimando salario/hora de referencia con personas ocupadas dependientes")
print("   pagadas mensualmente (P738==4), para valorizar el tiempo del cuidador...")

ocupados_mes = df[(df["P703"] == 1) & (df["P738"] == 4) & (df["P731"] > 0) & (df["P739_1"] > 0)].copy()
ocupados_mes["SALARIO_HORA"] = ocupados_mes["P739_1"] / (ocupados_mes["P731"] * 4.345)

print(f"   Ocupados dependientes pagados mensualmente, con horas e ingreso validos: {len(ocupados_mes):,}")


def media_ponderada(valores, pesos):
    return (valores * pesos).sum() / pesos.sum()


salario_hora_prom = media_ponderada(ocupados_mes["SALARIO_HORA"], ocupados_mes["FACTORFINAL"])
salario_hora_mediana = ocupados_mes["SALARIO_HORA"].median()
horas_semana_prom = media_ponderada(ocupados_mes["P731"], ocupados_mes["FACTORFINAL"])

print(f"   Salario/hora promedio ponderado (nacional): S/ {salario_hora_prom:.2f}")
print(f"   Salario/hora mediana (sin ponderar): S/ {salario_hora_mediana:.2f}")
print(f"   Horas/semana promedio (referencia jornada completa): {horas_semana_prom:.1f}")

print("\n   Por sexo:")
for sexo, nombre in [(1, "Hombre"), (2, "Mujer")]:
    sub = ocupados_mes[ocupados_mes["P204"] == sexo]
    if len(sub):
        sh = media_ponderada(sub["SALARIO_HORA"], sub["FACTORFINAL"])
        print(f"     {nombre}: S/ {sh:.2f}/hora (n={len(sub):,})")

# =====================================================================
# 4. COTA GRUESA DE COSTO DE OPORTUNIDAD ANUAL DEL CUIDADO
# =====================================================================
print("\n4. Cota gruesa: si cada cuidador identificado trabajara la jornada promedio")
print("   (horas_semana_prom) a salario/hora promedio, valor anual estimado:")

valor_semanal_por_cuidador = horas_semana_prom * salario_hora_prom
valor_anual_por_cuidador = valor_semanal_por_cuidador * 52
valor_anual_total = valor_anual_por_cuidador * pob_cuidadores

print(f"   Valor semanal por cuidador: S/ {valor_semanal_por_cuidador:,.0f}")
print(f"   Valor anual por cuidador:   S/ {valor_anual_por_cuidador:,.0f}")
print(f"   Poblacion de cuidadores (estimada): {pob_cuidadores:,.0f}")
print(f"   COSTO DE OPORTUNIDAD ANUAL AGREGADO (todo tipo de cuidado, no solo CCR):")
print(f"      S/ {valor_anual_total:,.0f}  (~US$ {valor_anual_total/3.75:,.0f} a tipo de cambio ~3.75)")
print("\n   ADVERTENCIA: esto asume que TODOS los cuidadores trabajarian jornada")
print("   completa si no cuidaran -- es un techo, no una medicion. Para un numero")
print("   mas conservador, se podria usar solo las horas que el cuidador reporta")
print("   querer trabajar (P733/P734) o una fraccion de la jornada.")

# =====================================================================
# 5. GUARDAR
# =====================================================================
resumen = pd.DataFrame([{
    "poblacion_cuidadores_estimada": pob_cuidadores,
    "pct_poblacion_12mas": pob_cuidadores / pob_total * 100,
    "pct_mujeres": tab_sexo.get(2, 0) / tab_sexo.sum() * 100,
    "salario_hora_promedio_soles": salario_hora_prom,
    "horas_semana_promedio_referencia": horas_semana_prom,
    "costo_oportunidad_anual_soles": valor_anual_total,
}])
resumen.to_csv(OUTPUT / "enut_cuidadores_resumen.csv", index=False)
df[df["ES_CUIDADOR"]].to_csv(OUTPUT / "enut_cuidadores_detalle.csv", index=False)
print(f"\n5. Guardado en {OUTPUT}")
print("\nFin.")
