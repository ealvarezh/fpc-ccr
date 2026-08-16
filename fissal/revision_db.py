import pyodbc
import pandas as pd

def get_connection():
    conn = pyodbc.connect(
        "DRIVER={ODBC Driver 17 for SQL Server};"
        "SERVER=localhost;"
        "DATABASE=Reporte_Transparencia;"
        "Trusted_Connection=yes;"
    )
    return conn

conn = get_connection()

query = """
SELECT TOP (100) *
FROM dbo.Reporte_2016_2026_v1;
"""

df = pd.read_sql(query, conn)
df.head()

conn.close()