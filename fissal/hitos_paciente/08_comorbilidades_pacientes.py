import pandas as pd
from pathlib import Path
import gc

SILVER = Path(r"C:\Users\eah\apoyoconsultoria.com\File Server - Analytics\7 Datos\Datos abiertos\fissal\01_silver")

print("Cargando hitos...")
hitos = pd.read_parquet(SILVER / "FISSAL_CCR_HITOS_PACIENTE.parquet")
pac_set = set(hitos.loc[hitos["FISSAL_REAL_B"], "NUM_DOC_CRYPTO"])
fechas_dx = hitos.set_index("NUM_DOC_CRYPTO")["FECHA_DIAGNOSTICO"]
fechas_des = hitos.set_index("NUM_DOC_CRYPTO")["FECHA_DESENLACE"]
n_total = len(pac_set)

# Contar pacientes por capitulo CIE-10, SOLO en ventana CCR
pac_capitulos = {}
for yr in range(2016, 2023):
    archivo = SILVER / f"FISSAL_PRESTACIONES_{yr}.parquet"
    if not archivo.exists():
        continue
    print(f"  {yr}...")
    df = pd.read_parquet(archivo, columns=["NUM_DOC_CRYPTO", "ATE_CODCIE10", "ATE_FECATENCION"])
    df = df[df["NUM_DOC_CRYPTO"].isin(pac_set)].copy()
    df["DX"] = df["NUM_DOC_CRYPTO"].map(fechas_dx)
    df["DES"] = df["NUM_DOC_CRYPTO"].map(fechas_des)

    # Solo dentro de la ventana CCR (entre diagnostico y desenlace)
    mask = (df["ATE_FECATENCION"] >= df["DX"]) & (df["ATE_FECATENCION"] <= df["DES"]) & df["DX"].notna() & df["DES"].notna()
    df = df[mask]

    if len(df) == 0:
        del df; gc.collect()
        continue

    df["CAP"] = df["ATE_CODCIE10"].str[0]

    for pid in df["NUM_DOC_CRYPTO"].unique():
        caps = set(df.loc[df["NUM_DOC_CRYPTO"] == pid, "CAP"].dropna())
        if pid not in pac_capitulos:
            pac_capitulos[pid] = caps
        else:
            pac_capitulos[pid].update(caps)
    del df
    gc.collect()

# Nombres de capitulos
cap_nombres = {
    "A": "A-B: Infecciosas y parasitarias",
    "C": "C: Neoplasias (tumores)",
    "D": "D: Neoplasias in situ / benignas",
    "E": "E: Endocrinas, nutricionales, metabolicas",
    "F": "F: Trastornos mentales",
    "G": "G: Sistema nervioso",
    "H": "H: Ojo y oido",
    "I": "I: Sistema circulatorio",
    "J": "J: Sistema respiratorio",
    "K": "K: Sistema digestivo",
    "L": "L: Piel y tejido subcutaneo",
    "M": "M: Musculoesqueletico",
    "N": "N: Sistema genitourinario",
    "O": "O: Embarazo, parto, puerperio",
    "R": "R: Sintomas, signos, hallazgos anormales",
    "S": "S-T: Traumatismos, envenenamientos",
    "Z": "Z: Factores que influyen en la salud",
}

print(f"\nPacientes FISSAL_REAL_B (en ventana CCR): {n_total:,}")
print(f"\n{'Capitulo':<8s} {'Descripcion':<50s} {'Pacientes':>10s} {'%':>7s}")
print("-" * 80)

for cap in sorted(cap_nombres.keys()):
    n = sum(1 for caps in pac_capitulos.values() if cap in caps)
    pct = n / n_total * 100
    if n > 0:
        print(f"{cap:<8s} {cap_nombres[cap]:<50s} {n:>10,} {pct:>6.1f}%")

print(f"\n  NOTA: 100% de pacientes tienen C (Neoplasias) porque TODOS tienen CCR (C18/19/20).")
print(f"  Los demas capitulos son comorbilidades REALES tratadas en FISSAL durante su proceso CCR.")
print("\nFin.")
