
import pandas as pd
from mapeogrupo110 import map_ciex_to_grupo110

CIEX_COLS = ["CAUSA_F_CIEX","CAUSA_E_CIEX","CAUSA_D_CIEX",
             "CAUSA_C_CIEX","CAUSA_B_CIEX","CAUSA_A_CIEX"]

MUERTE_VIOLENTA_MAP = {
    "ACCIDENTE DE TRANSITO": "Accidentes de transporte terrestre",
    "SUICIDIO": "Suicidios (lesiones autoinfligidas intencionalmente)",
    "HOMICIDIO": "Homicidios (agresiones infligidas por otra persona)",
    "ACCIDENTE DE TRABAJO": "Las demás causas externas",
    "OTRO ACCIDENTE": "Las demás causas externas",
    "NO SE CONOCE": "Lesiones de intención no determinada",
}

def clasificar_causa(row):
    # 1. Si hay muerte violenta conocida, usar ese mapeo (más confiable)
    mv = str(row.get("MUERTE_VIOLENTA","")).strip().upper()
    if mv in MUERTE_VIOLENTA_MAP:
        return MUERTE_VIOLENTA_MAP[mv]
    # 2. Buscar el último CIEX no-SIN REGISTRO (F→E→D→C→B→A)
    for col in CIEX_COLS:
        code = str(row.get(col,"")).strip()
        if code and code != "SIN REGISTRO":
            return map_ciex_to_grupo110(code)
    # 3. Si todo es SIN REGISTRO
    return "Resto de las demas enfermedades"

df = pd.read_csv(r"C:\Users\eah\apoyoconsultoria.com\File Server - Analytics\7 Datos\Datos abiertos\sinadef\SINADEF_DATOS_ABIERTOS.csv")
df["grupo110"] = df.apply(clasificar_causa, axis=1)

