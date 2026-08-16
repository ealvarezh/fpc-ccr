"""
Construye un ID compuesto (surrogate ID) para el archivo GCOP de EsSalud, que
NO trae un identificador de paciente utilizable (el DNI viene con 4 digitos
centrales enmascarados, ej. "72****7").

Idea: combinar 3 variables que, juntas, tienen alta capacidad de discriminar
pacientes reales aunque ninguna sola alcance:
  1. DNI enmascarado (2 digitos visibles al inicio + 1-2 al final)
  2. SEXO
  3. Fecha de nacimiento IMPLICITA: cada registro trae la edad exacta del
     paciente en años/meses/dias AL MOMENTO de esa atencion (ANNOS/MESES/DIAS)
     y la FECHA_ATENCION. Restando la edad a la fecha de atencion se obtiene
     una fecha de nacimiento estimada. Si dos registros son del mismo paciente
     real, esa fecha deberia coincidir exactamente (no es una fecha declarada
     directamente, se recalcula en cada registro).

Se probo primero usar solo (DNI + SEXO): da apenas 1,385 combos unicos para
101 mil registros y la mayoria mezcla claramente a mas de una persona (rango
de fecha de nacimiento implicita de años/decadas dentro del mismo combo).
Sumar la fecha de nacimiento implicita resuelve la colision: sube a ~17,500
IDs candidatos, con una distribucion de registros por ID que ya luce a nivel
de paciente (mediana 2, top decil 16+, maximo 120).

Esto es un ID PROBABILISTICO, no una certeza. El riesgo residual es que dos
personas reales distintas compartan exactamente los mismos 3-4 digitos
visibles del DNI + sexo + fecha de nacimiento -- posible pero poco probable
dado el tamaño de la base. No reemplaza un cruce real por DNI completo.
"""
import pandas as pd
import numpy as np
from pathlib import Path

BASE = Path(r"C:\Users\eah\apoyoconsultoria.com\File Server - Analytics\7 Datos\Datos abiertos\EsSalud")
OUTPUT = Path(r"C:\estela\github\fpc-ccr\complementarios\essalud\output")
OUTPUT.mkdir(parents=True, exist_ok=True)

print("=" * 70)
print("Construccion de ID compuesto — EsSalud GCOP")
print("=" * 70)

print("\n1. Cargando GCOP...")
g = pd.read_excel(BASE / "SAIP_-_Ciudadano_GCOP.xlsx", sheet_name="Pedico_Info_2026")
g = g.dropna(subset=["FECHA_ATENCION"]).copy()
g["FECHA_ATENCION"] = pd.to_datetime(g["FECHA_ATENCION"])
print(f"   {len(g):,} registros con fecha de atencion valida")

# =====================================================================
# 2. FECHA DE NACIMIENTO IMPLICITA
# =====================================================================
print("\n2. Calculando fecha de nacimiento implicita (FECHA_ATENCION - edad exacta)...")


def fecha_nac_implicita(row):
    return row["FECHA_ATENCION"] - pd.DateOffset(
        years=int(row["ANNOS"]), months=int(row["MESES"]), days=int(row["DIAS"])
    )


g["FECHA_NAC_IMPLICITA"] = g.apply(fecha_nac_implicita, axis=1)
g["FECHA_NAC_DIA"] = g["FECHA_NAC_IMPLICITA"].dt.date

# Filtrar edades no plausibles (posible error de digitacion en ANNOS/MESES/DIAS)
g["EDAD_APROX"] = g["ANNOS"] + g["MESES"] / 12 + g["DIAS"] / 365
n_edad_rara = ((g["EDAD_APROX"] < 0) | (g["EDAD_APROX"] > 110)).sum()
print(f"   Registros con edad implausible (<0 o >110 años): {n_edad_rara:,} -- se mantienen pero conviene revisarlos")

# =====================================================================
# 3. ID COMPUESTO
# =====================================================================
print("\n3. Construyendo ID compuesto (DNI enmascarado + SEXO + fecha nac. implicita)...")
g["ID_ESSALUD_GCOP"] = (
    g["DNI"].astype(str) + "_" + g["SEXO"].astype(str) + "_" + g["FECHA_NAC_DIA"].astype(str)
)

n_ids = g["ID_ESSALUD_GCOP"].nunique()
vc = g["ID_ESSALUD_GCOP"].value_counts()
print(f"   IDs candidatos unicos: {n_ids:,} (de {len(g):,} registros, {len(g)/n_ids:.1f} registros/ID en promedio)")
print(f"   IDs con 1 solo registro (sin trayectoria util): {(vc == 1).sum():,} ({(vc == 1).sum()/n_ids*100:.1f}%)")
print(f"   IDs con 2+ registros: {(vc >= 2).sum():,} ({(vc >= 2).sum()/n_ids*100:.1f}%)")
print(f"   IDs con 5+ registros: {(vc >= 5).sum():,}")
print(f"   IDs con 10+ registros: {(vc >= 10).sum():,}")

# Validacion cruzada: dentro de cada ID, el sitio del tumor (CIE10) deberia
# ser mayormente consistente (un paciente puede tener 2-3 codigos C18/19/20
# distintos por sub-localizacion, pero no debería saltar de colon a recto
# aleatoriamente en cada visita si es la misma persona)
cie_por_id = g.groupby("ID_ESSALUD_GCOP")["DIAGNOSTICO3"].nunique()
print(f"\n   Validacion: de los IDs con 2+ registros, {(cie_por_id[vc[vc>=2].index] == 1).mean()*100:.1f}% "
      f"tienen un solo codigo CIE10 en todos sus registros (esperado si el ID esta bien construido)")

# =====================================================================
# 4. PERFIL POR ID (equivalente a "perfil" de FISSAL)
# =====================================================================
print("\n4. Construyendo perfil de trayectoria por ID...")
perfil = g.groupby("ID_ESSALUD_GCOP").agg(
    SEXO=("SEXO", "first"),
    FECHA_NAC_IMPLICITA=("FECHA_NAC_IMPLICITA", "first"),
    PRIMERA_ATENCION=("FECHA_ATENCION", "min"),
    ULTIMA_ATENCION=("FECHA_ATENCION", "max"),
    N_ATENCIONES=("FECHA_ATENCION", "nunique"),
    N_REGISTROS=("FECHA_ATENCION", "size"),
    N_CENTROS=("COD_CENTRO", "nunique"),
    CIE10_PRINCIPAL=("DIAGNOSTICO3", lambda x: x.mode().iloc[0] if not x.mode().empty else None),
).reset_index()
perfil["TIEMPO_EN_SISTEMA_DIAS"] = (perfil["ULTIMA_ATENCION"] - perfil["PRIMERA_ATENCION"]).dt.days

print(f"   Pacientes candidatos: {len(perfil):,}")
print(f"   Tiempo en sistema (dias) - mediana: {perfil['TIEMPO_EN_SISTEMA_DIAS'].median():.0f}  "
      f"media: {perfil['TIEMPO_EN_SISTEMA_DIAS'].mean():.0f}")
print(f"   N atenciones - mediana: {perfil['N_ATENCIONES'].median():.0f}  media: {perfil['N_ATENCIONES'].mean():.1f}")

# =====================================================================
# 5. GUARDAR
# =====================================================================
g.to_parquet(OUTPUT / "essalud_gcop_con_id.parquet", index=False)
perfil.to_parquet(OUTPUT / "essalud_gcop_perfil.parquet", index=False)
print(f"\n5. Guardado:")
print(f"   {OUTPUT / 'essalud_gcop_con_id.parquet'}  (detalle, con ID_ESSALUD_GCOP)")
print(f"   {OUTPUT / 'essalud_gcop_perfil.parquet'}  (1 fila por paciente candidato)")
print("\nFin.")
