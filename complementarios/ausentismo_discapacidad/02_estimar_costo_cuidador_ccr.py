"""
Version CCR-especifica del costo de oportunidad del cuidador informal (punto 2.B),
para comparar contra el "techo" general de 01_explorar_enut_cuidadores.py.

Enfoque (bottom-up, a diferencia del enfoque top-down de 01_):
  costo_anual = N_pacientes_activos_CCR_en_el_anio
              x %_pacientes_con_cuidador_familiar   (supuesto de literatura)
              x horas_de_cuidado_por_semana          (supuesto de literatura, con rango)
              x semanas_activas_del_paciente_en_el_anio  (calculado de FISSAL, no supuesto)
              x salario_hora                          (calculado de ENUT 2024, ver 01_)

Fuente de pacientes: FISSAL_CCR_HITOS_V2.parquet (ya construido en este repo, ver
fissal/hitos_v2/01_construir_hitos_v2.py). OJO: FISSAL cubre solo la poblacion
afiliada al SIS (no asegurados / de bajos recursos) -- un paciente CCR real en
Peru tambien puede estar en EsSalud o en el sector privado, que no estan en esta
base. Este numero es entonces un PISO (subestima el total nacional de pacientes
CCR), al reves del "techo" del script 01_ (que sobreestima porque asume jornada
completa para todo cuidador). Comparar ambos deberia darle a Estela una banda
razonable para decidir que numero usar en el informe.

Supuestos de literatura (NO son datos peruanos, son de estudios internacionales/
LatAm sobre carga del cuidador oncologico -- ver 00_analisis_previo_metodologia.md
seccion 2.B para las fuentes). Se presentan 3 escenarios para que se vea cuanto
pesa cada supuesto:
  - % de pacientes con cuidador familiar directo: 60% / 75% / 90%
  - horas de cuidado por semana: 10h / 20h / 30h
"""
import pandas as pd
from pathlib import Path

FISSAL_PARQUET = Path(
    r"C:\Users\eah\apoyoconsultoria.com\File Server - Analytics\7 Datos\Datos abiertos"
    r"\fissal\01_silver\FISSAL_CCR_HITOS_V2.parquet"
)
OUTPUT = Path(__file__).parent / "output"
OUTPUT.mkdir(exist_ok=True)

ANIO = 2024
SALARIO_HORA = 11.55  # calculado en 01_explorar_enut_cuidadores.py (ENUT 2024, ponderado nacional)

ESCENARIOS_PCT_CUIDADOR = {"bajo": 0.60, "base": 0.75, "alto": 0.90}
ESCENARIOS_HORAS_SEMANA = {"bajo": 10, "base": 20, "alto": 30}

print("=" * 70)
print(f"Costo del cuidador informal CCR-especifico -- FISSAL {ANIO}")
print("=" * 70)

# =====================================================================
# 1. PACIENTES ACTIVOS EN EL AÑO Y SEMANAS DE TRAYECTORIA DENTRO DEL AÑO
# =====================================================================
print("\n1. Cargando FISSAL y calculando pacientes activos + semanas en el año...")
df = pd.read_parquet(
    FISSAL_PARQUET,
    columns=["Codigo_identificacion_paciente", "PRIMERA_ATENCION", "ULTIMA_ATENCION",
             "LOCALIZACION", "TRACK", "FALLECIDO"],
)
df["PRIMERA_ATENCION"] = pd.to_datetime(df["PRIMERA_ATENCION"], errors="coerce")
df["ULTIMA_ATENCION"] = pd.to_datetime(df["ULTIMA_ATENCION"], errors="coerce")

ini_anio = pd.Timestamp(f"{ANIO}-01-01")
fin_anio = pd.Timestamp(f"{ANIO}-12-31")

activos = df[(df["PRIMERA_ATENCION"] <= fin_anio) & (df["ULTIMA_ATENCION"] >= ini_anio)].copy()
print(f"   Pacientes CCR (FISSAL/SIS) con trayectoria en {ANIO}: {len(activos):,}")
print(f"   (de un total historico de {len(df):,} pacientes CCR en FISSAL 2016-2026)")

# dias de trayectoria del paciente que caen DENTRO del año (recorte a [ini_anio, fin_anio])
inicio_en_anio = activos["PRIMERA_ATENCION"].clip(lower=ini_anio)
fin_en_anio = activos["ULTIMA_ATENCION"].clip(upper=fin_anio)
activos["DIAS_EN_ANIO"] = (fin_en_anio - inicio_en_anio).dt.days.clip(lower=1)
activos["SEMANAS_EN_ANIO"] = (activos["DIAS_EN_ANIO"] / 7).clip(upper=52)

print(f"   Semanas de trayectoria dentro de {ANIO} -- mediana: {activos['SEMANAS_EN_ANIO'].median():.1f}, "
      f"promedio: {activos['SEMANAS_EN_ANIO'].mean():.1f}")
print("   (mediana baja porque incluye pacientes que solo tuvieron 1-2 atenciones puntuales ese año;")
print("    esto es evidencia real de FISSAL, no un supuesto)")

semanas_promedio = activos["SEMANAS_EN_ANIO"].mean()
n_activos = len(activos)

# =====================================================================
# 2. ESCENARIOS
# =====================================================================
print(f"\n2. Aplicando escenarios de % con cuidador x horas/semana (salario/hora S/ {SALARIO_HORA}):")

resultados = []
for nivel_pct, pct in ESCENARIOS_PCT_CUIDADOR.items():
    for nivel_horas, horas in ESCENARIOS_HORAS_SEMANA.items():
        costo_anual = n_activos * pct * horas * semanas_promedio * SALARIO_HORA
        resultados.append({
            "pct_con_cuidador": nivel_pct,
            "horas_semana": nivel_horas,
            "pct_valor": pct,
            "horas_valor": horas,
            "costo_anual_soles": costo_anual,
        })
        if nivel_pct == "base" or (nivel_pct == "bajo" and nivel_horas == "bajo") or (nivel_pct == "alto" and nivel_horas == "alto"):
            print(f"   %cuidador={nivel_pct:5s} ({pct:.0%})  x  horas/sem={nivel_horas:5s} ({horas}h)  "
                  f"->  S/ {costo_anual:,.0f}/año")

resumen = pd.DataFrame(resultados)
base = resumen[(resumen["pct_con_cuidador"] == "base") & (resumen["horas_semana"] == "base")]["costo_anual_soles"].iloc[0]
piso = resumen["costo_anual_soles"].min()
techo = resumen["costo_anual_soles"].max()

print(f"\n   ESCENARIO BASE (75% con cuidador, 20h/semana): S/ {base:,.0f}/año")
print(f"   Rango completo (9 combinaciones): S/ {piso:,.0f} -- S/ {techo:,.0f}/año")

# =====================================================================
# 3. COMPARACION CON EL "TECHO" GENERAL (script 01_)
# =====================================================================
print("\n3. Comparacion con el enfoque general (01_explorar_enut_cuidadores.py):")
print(f"   Techo general (cuidado de cualquier tipo, todo Peru): ~S/ 21,000,000,000/año")
print(f"   Escenario base CCR-especifico (solo pacientes FISSAL):  S/ {base:,.0f}/año")
print(f"   -> el numero CCR-especifico es ~{21_000_000_000/base:,.0f}x mas chico que el techo general,")
print(f"      lo cual tiene sentido: CCR es una fraccion pequeña de todas las razones de cuidado")
print(f"      (enfermedades cronicas, adultos mayores, discapacidad, niños con necesidades")
print(f"      especiales, etc. en TODO el pais), y ademas FISSAL no cubre EsSalud ni privados.")

# =====================================================================
# 4. GUARDAR
# =====================================================================
resumen.to_csv(OUTPUT / "ccr_costo_cuidador_escenarios.csv", index=False)
print(f"\n4. Guardado en {OUTPUT / 'ccr_costo_cuidador_escenarios.csv'}")
print("\nFin.")
