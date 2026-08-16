import pyodbc
conn = pyodbc.connect("DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost;DATABASE=Reporte_Transparencia;Trusted_Connection=yes;")
c = conn.cursor()

# Check hospitalization fields
c.execute("SELECT COUNT(*) as total, COUNT(Fecha_ingreso_hospitalizacion) as con_ingreso, COUNT(Fecha_alta_hospitalizacion) as con_alta FROM [Reporte_2016_2026_v1] WHERE (Codigo_CIE10 LIKE 'C18%' OR Codigo_CIE10 LIKE 'C19%' OR Codigo_CIE10 LIKE 'C20%')")
r = c.fetchone()
print(f"Total CCR: {r[0]:,}")
print(f"  con Fecha_ingreso_hospitalizacion: {r[1]:,} ({r[1]/r[0]*100:.1f}%)")
print(f"  con Fecha_alta_hospitalizacion: {r[2]:,} ({r[2]/r[0]*100:.1f}%)")

# Check Tipo_atencion values
c.execute("SELECT DISTINCT TOP 30 Tipo_atencion FROM [Reporte_2016_2026_v1] WHERE (Codigo_CIE10 LIKE 'C18%' OR Codigo_CIE10 LIKE 'C19%' OR Codigo_CIE10 LIKE 'C20%')")
print("\nTipos de atencion:")
for r in c.fetchall():
    print(f"  [{r[0]}]")

# Examples with hospital dates
c.execute("SELECT TOP 10 Tipo_atencion, Fecha_ingreso_hospitalizacion, Fecha_alta_hospitalizacion FROM [Reporte_2016_2026_v1] WHERE (Codigo_CIE10 LIKE 'C18%') AND Fecha_ingreso_hospitalizacion IS NOT NULL")
print("\nEjemplos con fechas de hospitalizacion:")
for r in c.fetchall():
    print(f"  Tipo: [{r[0]}] Ing: {r[1]} Alta: {r[2]}")

conn.close()
