import pandas as pd
import pyodbc

excel = r"C:\Users\eah\apoyoconsultoria.com\File Server - Analytics\3 Proyectos\2025\2025-116-L FPC Dashboard 25\4 Analisis\3 Programas\adicional 2026\diccionario_ATE_DESCCONSUMO_502_estandarizado.xlsx"
dic = pd.read_excel(excel)

# Check a specific item
target = "CONSULTA AMBULATORIA PARA LA EVALUACION Y MANEJO DE UN PACIENTE NUEVO NIVEL DE ATENCION III"
match = dic[dic["clave_normalizada"] == target]
print(f"Match in dic: {len(match)}")

# Get SQL version
conn = pyodbc.connect("DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost;DATABASE=Reporte_Transparencia;Trusted_Connection=yes;")
c = conn.cursor()
c.execute("SELECT TOP 1 Descripcion_Consumo FROM [Reporte_2016_2026_v1] WHERE Descripcion_Consumo LIKE 'consulta ambulatoria%'")
r = c.fetchone()
if r:
    raw = r[0]
    normalized = raw.strip().upper().replace("  ", " ").replace("(", "").replace(")", "")
    print(f"SQL raw: [{raw}]")
    print(f"Normalized: [{normalized}]")
    print(f"Match with normalized: {normalized == target}")
    print(f"len(dict)={len(target)}, len(sql)={len(normalized)}")
    
# Check what normalization the dictionary does
# Compare some random dictionary entries
print("\nSample raw vs normalized from dictionary:")
for _, row in dic.head(10).iterrows():
    raw = row["ATE_DESCCONSUMO"]
    norm = row["clave_normalizada"]
    if raw != norm:
        print(f"  RAW: [{str(raw)[:80]}]")
        print(f"  NORM: [{str(norm)[:80]}]")
        print()

conn.close()
