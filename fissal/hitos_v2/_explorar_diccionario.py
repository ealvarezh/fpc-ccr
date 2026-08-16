import pandas as pd

EXCEL = r"C:\Users\eah\apoyoconsultoria.com\File Server - Analytics\3 Proyectos\2025\2025-116-L FPC Dashboard 25\4 Analisis\3 Programas\adicional 2026\diccionario_ATE_DESCCONSUMO_502_estandarizado.xlsx"
df = pd.read_excel(EXCEL)

print("=== 19 CATEGORIAS DEL DICCIONARIO ===")
for c, n in df["categoria_recurso_502"].value_counts().items():
    sub = df[df["categoria_recurso_502"] == c]
    n_crc = (sub["atribucion_crc_sugerida"] == "Atribuible/compatible con manejo de CRC").sum()
    n_soporte = (sub["atribucion_crc_sugerida"] == "Soporte del episodio de atencion oncologica").sum()
    n_revisar = (sub["atribucion_crc_sugerida"] == "Revisar atribucion").sum()
    n_no = (sub["atribucion_crc_sugerida"] == "No atribuible probable / comorbilidad").sum()
    print(f"{c:<40s} {n:>5,} items   CRC={n_crc:>3}   Soporte={n_soporte:>4}   Revisar={n_revisar:>3}   NoAtrib={n_no:>3}")

print(f"\n=== ATRIBUCION CRC SUGERIDA ===")
print(df["atribucion_crc_sugerida"].value_counts().to_string())

print(f"\n=== USO SUGERIDO ===")
print(df["uso_sugerido_502"].value_counts().to_string())

print(f"\nEjemplos de 'Atribuible/compatible con manejo de CRC':")
crc_items = df[df["atribucion_crc_sugerida"] == "Atribuible/compatible con manejo de CRC"]
for cat in crc_items["categoria_recurso_502"].value_counts().index:
    ejemplos = crc_items[crc_items["categoria_recurso_502"] == cat]["ATE_DESCCONSUMO"].head(3).tolist()
    print(f"  {cat}: {ejemplos}")
