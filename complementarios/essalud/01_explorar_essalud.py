"""
Exploracion inicial de los 2 archivos que entrego EsSalud via SAIP:
  - SAIP_-_Ciudadano_GCOP.xlsx (hoja Pedico_Info_2026): 101,121 registros,
    44 columnas. Trae DNI PARCIALMENTE enmascarado (ej. "72****7") + edad
    exacta (ANNOS/MESES/DIAS) a la fecha de cada atencion + sexo. NO trae
    costos ni consumos/medicamentos (confirma lo que dijo EsSalud: el area
    que respondio no tiene esa info).
  - SAIP_-_Ciudadano_GCPS.xlsx (hoja Datos): 10 columnas simples (red,
    centro, servicio, fecha, sexo, CIE10). NO trae DNI ni edad -> no hay
    forma de reconstruir pacientes individuales con este archivo, solo sirve
    para conteos agregados (ej. atenciones por servicio/CIE10 en el tiempo).

Este script solo perfila la estructura y calidad de datos; no construye el ID
(eso esta en 02_construir_id_essalud.py).
"""
import pandas as pd
from pathlib import Path

BASE = Path(r"C:\Users\eah\apoyoconsultoria.com\File Server - Analytics\7 Datos\Datos abiertos\EsSalud")

print("=" * 70)
print("EXPLORACION — EsSalud (SAIP)")
print("=" * 70)

# =====================================================================
# GCOP: Gerencia Central de Prestaciones/Operaciones — tiene DNI enmascarado + edad
# =====================================================================
print("\n--- GCOP (Pedico_Info_2026) ---")
gcop = pd.read_excel(BASE / "SAIP_-_Ciudadano_GCOP.xlsx", sheet_name="Pedico_Info_2026")
print(f"Filas: {len(gcop):,}  |  Columnas: {gcop.shape[1]}")
print(f"Columnas: {list(gcop.columns)}")

print(f"\nRango FECHA_ATENCION: {gcop['FECHA_ATENCION'].min()} a {gcop['FECHA_ATENCION'].max()}")
print(f"Diagnosticos (DIAGNOSTICO3) unicos: {sorted(gcop['DIAGNOSTICO3'].unique())}")
print(f"Sexo: {dict(gcop['SEXO'].value_counts())}")

print("\nPatron de enmascaramiento del DNI (longitud del string):")
print(gcop["DNI"].astype(str).str.len().value_counts())
print("Ejemplos:", gcop["DNI"].astype(str).sample(10, random_state=1).tolist())
print("--> Se enmascaran SIEMPRE 4 digitos centrales (****). DNI de 7 digitos:")
print("    quedan visibles 2 al inicio + 1 al final. DNI de 8 digitos: 2 + 2.")

print("\nNulos en columnas clave:")
for c in ["DNI", "ANNOS", "MESES", "DIAS", "SEXO", "FECHA_ATENCION", "COD_CENTRO", "DIAGNOSTICO3"]:
    print(f"  {c}: {gcop[c].isna().sum():,} de {len(gcop):,}")

print("\nColumnas de costo/consumo presentes: NINGUNA (confirma respuesta de EsSalud)")
print("Columnas de servicio/procedimiento disponibles: SERVICIO, ACTIVIDAD, SUBACTIVIDAD")
print(gcop["SERVICIO"].value_counts().head(15))

# =====================================================================
# GCPS: Gerencia Central de Prestaciones de Salud — sin DNI ni edad
# =====================================================================
print("\n\n--- GCPS (Datos) ---")
gcps = pd.read_excel(BASE / "SAIP_-_Ciudadano_GCPS.xlsx", sheet_name="Datos")
print(f"Filas: {len(gcps):,}  |  Columnas: {gcps.shape[1]}")
print(f"Columnas: {list(gcps.columns)}")
print(f"\nTiene DNI o similar? {'DNI' in gcps.columns or 'CODIGO_PERSONA' in gcps.columns}")
print(f"Tiene edad? {'ANNOS' in gcps.columns or 'EDAD' in gcps.columns}")
print("--> Sin ningun campo de paciente (ni siquiera enmascarado) y sin edad:")
print("    NO se puede construir un ID ni reconstruir trayectorias individuales")
print("    con este archivo. Solo sirve para conteos agregados.")
print(f"\nCIE10 unicos: {sorted(gcps['CIE10'].unique())}")
print(f"Servicios mas frecuentes:")
print(gcps["SERVICIO"].value_counts().head(15))
print(f"\nRango de fechas (texto, revisar formato): {gcps['FECHA_ATENCION'].min()} a {gcps['FECHA_ATENCION'].max()}")

print("\nFin de exploracion.")
