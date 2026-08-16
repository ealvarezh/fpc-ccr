"""
Perfil descriptivo de los pacientes CCR financiados por SIS (no FISSAL) --
util como argumento de cobertura ("cuanta gente con CCR hay fuera del radar
de FISSAL"), no como fuente de costos ni trayectorias (ver 01_explorar_sis.py
para el porque: 91.6% de estos pacientes tiene una sola atencion registrada).
"""
import pandas as pd
from pathlib import Path

INPUT = Path(r"C:\estela\github\fpc-ccr\complementarios\sis\output")
OUTPUT = INPUT

print("=" * 70)
print("Perfil SIS-only")
print("=" * 70)

a = pd.read_parquet(INPUT / "sis_atenciones.parquet")
n_pac = a["CODIGO_PERSONA"].nunique()
print(f"\nPacientes unicos: {n_pac:,}")

# Un registro por paciente (primer registro cronologico) para el perfil
a["FECHA_ATENCION"] = pd.to_datetime(a["FECHA_ATENCION"], format="%d/%m/%y", errors="coerce")
primer = a.sort_values("FECHA_ATENCION").drop_duplicates("CODIGO_PERSONA", keep="first")

print("\n--- Sexo ---")
print(primer["SEXO"].value_counts().to_string())
print((primer["SEXO"].value_counts(normalize=True) * 100).round(1).to_string())

print("\n--- Localizacion (CIE10) ---")
loc = primer["COD_DIAGNOSTICO"].str[:3].map({"C18": "Colon", "C19": "Union rectosigmoidea", "C20": "Recto"})
print(loc.value_counts().to_string())

print("\n--- Departamento del establecimiento de atencion (top 15) ---")
print(primer["DEPARTAMENTO_EESS"].value_counts().head(15).to_string())

print("\n--- Tipo de atencion ---")
print(primer["TIPOO_ATENCION"].value_counts().to_string())

print("\n--- Año de primera atencion (aproxima año de deteccion/entrada al sistema) ---")
print(a.groupby("CODIGO_PERSONA")["ANIO_ATENCION"].min().value_counts().sort_index().to_string())

print("\n--- Tipo de diagnostico (definitivo/presuntivo/repetitivo) ---")
print(primer["TIPO_DIAGNOSTICO"].value_counts().to_string())

# Cuantos SI tienen trayectoria util (3+ atenciones) -- el subgrupo chico
# donde SI valdria la pena mirar el detalle
n_at = a.groupby("CODIGO_PERSONA")["FECHA_ATENCION"].nunique()
regulares = n_at[n_at >= 3].index
print(f"\n--- Subgrupo con 3+ atenciones (posible trayectoria), n={len(regulares)} ---")
sub = a[a["CODIGO_PERSONA"].isin(regulares)]
print(f"Atenciones de este subgrupo: {len(sub):,}")
print(sub.groupby("CODIGO_PERSONA")["FECHA_ATENCION"].nunique().describe().to_string())

print("\nNota: no hay campo de edad/fecha de nacimiento en este archivo SIS,")
print("por lo que no se puede perfilar por edad ni cruzar contra la edad de FISSAL.")

print("\nFin.")
