import sys
import os
import time
import importlib.util
import numpy as np
import pandas as pd

_here = os.path.dirname(os.path.abspath(__file__))
_mapping_path = os.path.join(_here, "01_mapeo_cie10_grupo110.py")
_spec = importlib.util.spec_from_file_location("mapeo_cie10", _mapping_path)
_mapeo = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mapeo)

map_ciex_to_grupo110 = _mapeo.map_ciex_to_grupo110
GRUPOS_110 = _mapeo.GRUPOS_110

# ── Paths ──────────────────────────────────────────────────────────────────
SINADEF_CSV = (
    r"C:\Users\eah\apoyoconsultoria.com\File Server - Analytics"
    r"\7 Datos\Datos abiertos\sinadef\SINADEF_DATOS_ABIERTOS.csv"
)
INEI_GRUPO110_XLSX = (
    r"C:\Users\eah\apoyoconsultoria.com\File Server - Analytics"
    r"\7 Datos\Datos abiertos\sinadef\TASA MORTALIDAD\Tasa_Grupo110_LM_v1.xlsx"
)
INEI_GRUPO10_XLSX = (
    r"C:\Users\eah\apoyoconsultoria.com\File Server - Analytics"
    r"\7 Datos\Datos abiertos\sinadef\TASA MORTALIDAD\Tasa_Grupo10_LM_v1.xlsx"
)
OUTPUT_DIR = r"C:\estela\github\fpc\output"

os.makedirs(OUTPUT_DIR, exist_ok=True)

sys.stdout.reconfigure(encoding="utf-8")

# ── Constants ──────────────────────────────────────────────────────────────
CHUNK_SIZE = 200_000
YEARS_SINADEF = range(2017, 2027)  # 2017-2026
YEARS_COMPARE = range(2017, 2025)  # 2017-2024 (overlap)

CIEX_COLS = [
    "CAUSA_F_CIEX",
    "CAUSA_E_CIEX",
    "CAUSA_D_CIEX",
    "CAUSA_C_CIEX",
    "CAUSA_B_CIEX",
    "CAUSA_A_CIEX",
]

MUERTE_VIOLENTA_MAP = {
    "ACCIDENTE DE TRANSITO": "Accidentes de transporte terrestre",
    "SUICIDIO": "Suicidios (lesiones autoinfligidas intencionalmente)",
    "HOMICIDIO": "Homicidios (agresiones infligidas por otra persona)",
    "ACCIDENTE DE TRABAJO": "Las demás causas externas",
    "OTRO ACCIDENTE": "Las demás causas externas",
    "NO SE CONOCE": "Lesiones de intención no determinada",
}

SEXO_MAP = {"MASCULINO": "Hombre", "FEMENINO": "Mujer"}

# ── Build grupo110 → grupo10 mapping ──────────────────────────────────────
# 10 groups as used by INEI
GRUPO10_NAMES = [
    "Enfermedades Infecciosas y Parasitarias",
    "Enfermedades neoplasicas",
    "Enfermedades del aparato circulatorio",
    "Afecciones perinatales",
    "Lesiones y causas externas",
    "Enfermedades del sistema respiratorio",
    "Enfermedades del sistema digestivo",
    "Enfermedades mentales y del sistema nervioso",
    "Enfermedades metabolicas y nutricionales",
    "Demas enfermedades",
]

_G110_TO_G10 = {}
# Infectious (groups 1-11)
_infectious = {
    "Enfermedades infecciosas intestinales",
    "Tuberculosis",
    "Ciertas enfermedades transmitidas por vectores y rabia",
    "Ciertas enfermedades inmunoprevenibles",
    "Meningitis",
    "Septicemia, excepto neonatal",
    "Hepatitis B",
    "Enfermedad por el VIH (SIDA)",
    "Otras enfermedades infecciosas y parasitarias",
    "Sífilis congénita",
    "Infecciones especificas del periodo perinatal",
    "Encefalitis viral",
    "Covid-19",
}
for g in _infectious:
    _G110_TO_G10[g] = "Enfermedades Infecciosas y Parasitarias"

# Neoplasms (groups 12-37)
_neoplasms = {
    "Neoplasia maligna de estómago",
    "Neoplasia maligna de colon y de la unión rectosigmoidea",
    "Neoplasia maligna de los órganos digestivos y del peritoneo, excepto estomago",
    "Neoplasia maligna de pancreas",
    "Neoplasia maligna de la tráquea, los bronquios y el pulmón",
    "Neoplasia maligna de los órganos respiratorios e intratorácicos, excepto traquea y pulmon",
    "Neoplasia maligna de la mama",
    "Neoplasia maligna del cuello del útero",
    "Neoplasia maligna del cuerpo del útero",
    "Neoplasia maligna del útero, parte no especificada",
    "Neoplasia maligna de la próstata",
    "Neoplasia maligna de los órganos genitourinarios",
    "Neoplasia maligna de ojo, encefalo y de otras partes del sistema nervioso",
    "Neoplasia maligna de tejido linfático, de otros órganos hematopoyeticos",
    "Leucemia",
    "Neoplasia maligna del labio, de la cavidad bucal y de la faringe",
    "Neoplasia maligna de la piel",
    "Neoplasia maligna de los huesos, cartilagos y tejido conjuntivo",
    "Neoplasia maligna de la glandula tiroides y de otras glandulas endocrinas",
    "Neoplasia maligna de sitios mal definidos, de comportamiento incierto y los no especificados",
    "Neoplasia maligna de higado y vias biliares",
    "Neoplasia maligna secundaria (metastasis)",
    "Neoplasias benignas",
}
for g in _neoplasms:
    _G110_TO_G10[g] = "Enfermedades neoplasicas"

# Circulatory (groups 38-48)
_circulatory = {
    "Fiebre reumática aguda y enfermedades cardíacas reumáticas cronicas",
    "Enfermedades hipertensivas",
    "Enfermedades isquémicas del corazón",
    "Enfermedad cardiopulmonar, enfermedades de la circulación pulmonar",
    "Enfermedades cerebrovasculares",
    "Arteriosclerosis",
    "Aneurimas",
    "Embolia, trombosis arteriales y otros trastornos arteriales o arteriolares",
    "Insuficiencia cardíaca",
    "Paro cardiaco",
    "Otras enfermedades del sistema circulatorio",
}
for g in _circulatory:
    _G110_TO_G10[g] = "Enfermedades del aparato circulatorio"

# Perinatal (groups 49-57)
_perinatal = {
    "Feto y recién nacido afectados por ciertas afecciones materna",
    "Feto y recién nacido afectados por complicaciones obstétrica",
    "Retardo del crecimiento fetal, desnutrición fetal, gestación",
    "Trastornos respiratorios específicos del periodo perinatal",
    "Trastornos cardiovasculares originados en el periodo perinatal",
    "Trastornos hemorragicos y hematologicos del feto y del recien nacido",
    "Trastornos endocrinos y metabolicos del feto y del recien nacido",
    "Trastornos del sistema digestivo del feto y del recien nacido",
    "Otras ciertas afecciones originadas en el periodo perinatal",
}
for g in _perinatal:
    _G110_TO_G10[g] = "Afecciones perinatales"

# Respiratory (groups 58-68)
_respiratory = {
    "Infecciones respiratorias agudas altas",
    "Infecciones respiratorias agudas bajas",
    "Enfermedades del pulmon debidas a agentes externos",
    "Enfermedad pulmonar obstructiva cronica (EPOC)",
    "Asma",
    "Edema Pulmonar",
    "Enfermedad pulmonar intersticial",
    "Afecciones de la pleura",
    "Insuficiencia respiratoria",
    "Trastornos respiratorios no especificados",
    "Otras enfermedades del sistema respiratorio",
}
for g in _respiratory:
    _G110_TO_G10[g] = "Enfermedades del sistema respiratorio"

# Digestive (groups 69-78)
_digestive = {
    "Enfermedades del esofago, estomago y del duodeno",
    "Apendicitis, hernia de la cavidad abdominal y obstrucción intestinal",
    "Enfermedades del peritoneo, peritonitis y otros",
    "Cirrosis y ciertas otras enfermedades crónicas del hígado",
    "Enfermedades del sistema urinario",
    "Hiperplasia de próstata",
    "Trastornos de la vesícula biliar, vias biliares y del pancreas",
    "Hemorragia gastrointestinal (hematemesis, melena y las no especificadas)",
    "Insuficiencia renal, incluye la aguda, cronica y la no especificadas",
    "Otras enfermedades del sistema digestivo",
}
for g in _digestive:
    _G110_TO_G10[g] = "Enfermedades del sistema digestivo"

# Mental + Nervous (groups 79-88)
_mental_nervous = {
    "Trastornos mentales y del comportamiento",
    "Enfermedad de Alzheimer",
    "Enfermedad del parkinson",
    "Esclerosis multiple",
    "Epilepsia y estado de mal epileptico",
    "Edema cerebral",
    "Encefalitis, mielitis y encefalomielitis",
    "Otras enfermedades del sistema nervioso, excepto meningitis",
    "Degeneracion de sistemas multiples",
}
for g in _mental_nervous:
    _G110_TO_G10[g] = "Enfermedades mentales y del sistema nervioso"

# Metabolic + Nutritional (groups 89-93)
_metabolic = {
    "Diabetes mellitus",
    "Deficiencias nutricionales y anemias nutricionales",
    "Anemias hemoliticas, aplasticas y otras anemias",
    "Trastornos de la glandula tiroides, endocrinas y otras metabolicas",
    "Defectos de la coagulación en organos hematopoyeticos y trastornos que afectan al mecanismo de la inmunidad",
}
for g in _metabolic:
    _G110_TO_G10[g] = "Enfermedades metabolicas y nutricionales"

# External causes (groups 94-109)
_external = {
    "Accidentes de transporte terrestre",
    "Accidentes por otro tipo de transporte",
    "Caídas",
    "Accidentes por fuerzas mecanicas (inanimadas y animadas)",
    "Accidentes por Ahogamiento y sumersión",
    "Accidentes que obstruyen la respiración",
    "Exposición a la corriente eléctrica",
    "Exposición al humo, fuego y llamas",
    "Accidentes por fuerzas de la naturaleza",
    "Envenenamientos por, y exposición a sustancias nocivas",
    "Accidentes por disparo de arma de fuego",
    "Incidentes ocurridos al paciente durante la atencion medica y quirurgica",
    "Suicidios (lesiones autoinfligidas intencionalmente)",
    "Homicidios (agresiones infligidas por otra persona)",
    "Lesiones de intención no determinada",
    "Las demás causas externas",
}
for g in _external:
    _G110_TO_G10[g] = "Lesiones y causas externas"

# Demas (everything else: 110-114 + unclassified)
_demas = {
    "Eventos relacionados al embarazo, parto y puerperio",
    "Malformaciones congénitas, deformidades y anomalías cromosomicas",
    "Enfermedades de la piel",
    "Resto de las demas enfermedades",
}
for g in _demas:
    _G110_TO_G10[g] = "Demas enfermedades"

# Ensure all 114 groups are mapped (plus Covid-19 makes 115 entries in the list)
# Validate
for g in GRUPOS_110:
    if g not in _G110_TO_G10:
        _G110_TO_G10[g] = "Demas enfermedades"
        print(f"WARNING: Unmapped grupo110 -> grupo10: {g}")


def map_g110_to_g10(grupo110_name):
    return _G110_TO_G10.get(grupo110_name, "Demas enfermedades")


# ── Helpers ────────────────────────────────────────────────────────────────
def determine_best_ciex(chunk):
    """Vectorized best-CIEX extraction from the chain F→E→D→C→B→A."""
    vals = chunk[CIEX_COLS].fillna("SIN REGISTRO").to_numpy(dtype=str)
    mask = vals != "SIN REGISTRO"
    any_valid = mask.any(axis=1)
    idx = np.where(any_valid, np.argmax(mask, axis=1), len(CIEX_COLS) - 1)
    return vals[np.arange(len(vals)), idx]


def compute_comparison(df_merged, key_cols, col_sinadef="ndefunciones", col_inei="ndefun_"):
    """Given a merged DataFrame, compute comparison metrics."""
    df = df_merged.copy()
    df["ndefun_sinadef"] = df[col_sinadef].fillna(0).astype(int)
    df["ndefun_inei"] = df[col_inei].fillna(0).astype(int)
    df["diferencia"] = df["ndefun_inei"] - df["ndefun_sinadef"]
    mask = df["ndefun_inei"] != 0
    df["pct_diferencia"] = np.where(
        mask,
        (df["diferencia"] / df["ndefun_inei"]) * 100,
        np.nan,
    )
    df["ratio"] = np.where(
        mask,
        df["ndefun_sinadef"] / df["ndefun_inei"],
        np.nan,
    )
    return df[key_cols + ["ndefun_sinadef", "ndefun_inei", "diferencia", "pct_diferencia", "ratio"]]


# ── 1. Process SINADEF ────────────────────────────────────────────────────
print("=" * 70)
print("STEP 1: Processing SINADEF data ...")
t0 = time.time()

# Accumulators
rows_all = []
rows_dept = []
rows_natl = []
total_sin_registro = 0
chunk_idx = 0

dtype_dict = {
    "ANIO": "int32",
    "DEPARTAMENTO_FALLECIMIENTO": "str",
    "SEXO": "str",
    "EDAD": "str",
    "MUERTE_VIOLENTA": "str",
    "CAUSA_A_CIEX": "str",
    "CAUSA_B_CIEX": "str",
    "CAUSA_C_CIEX": "str",
    "CAUSA_D_CIEX": "str",
    "CAUSA_E_CIEX": "str",
    "CAUSA_F_CIEX": "str",
}

use_cols = [
    "ANIO",
    "DEPARTAMENTO_FALLECIMIENTO",
    "SEXO",
    "MUERTE_VIOLENTA",
    "CAUSA_A_CIEX",
    "CAUSA_B_CIEX",
    "CAUSA_C_CIEX",
    "CAUSA_D_CIEX",
    "CAUSA_E_CIEX",
    "CAUSA_F_CIEX",
]

for chunk in pd.read_csv(
    SINADEF_CSV,
    encoding="latin-1",
    usecols=use_cols,
    dtype=dtype_dict,
    chunksize=CHUNK_SIZE,
    low_memory=False,
):
    chunk_idx += 1
    n_in = len(chunk)

    # Filter years 2017-2024 (comparison range)
    chunk = chunk[chunk["ANIO"].between(2017, 2024)].copy()
    if len(chunk) == 0:
        continue

    # Map SEXO
    chunk["sexo"] = chunk["SEXO"].map(SEXO_MAP)
    chunk = chunk[chunk["sexo"].notna()].copy()

    # --- Determine best CIEX ---
    chunk["best_ciex"] = determine_best_ciex(chunk)

    # --- MUERTE_VIOLENTA override ---
    chunk["mv_grupo"] = chunk["MUERTE_VIOLENTA"].map(MUERTE_VIOLENTA_MAP)
    has_mv = chunk["mv_grupo"].notna()

    # Map CIEX to grupo110
    grupo_from_ciex = chunk["best_ciex"].apply(map_ciex_to_grupo110)
    chunk["grupo110"] = np.where(has_mv, chunk["mv_grupo"], grupo_from_ciex)

    # Count SIN REGISTRO cases (CIEX chain all SIN REGISTRO)
    all_sin = (
        chunk[CIEX_COLS]
        .fillna("SIN REGISTRO")
        .apply(lambda r: (r == "SIN REGISTRO").all(), axis=1)
    )
    total_sin_registro += all_sin.sum()

    # --- Group by: ANIO, DEPARTAMENTO_FALLECIMIENTO, sexo, grupo110 ---
    grp_cols = ["ANIO", "DEPARTAMENTO_FALLECIMIENTO", "sexo", "grupo110"]
    grp = chunk.groupby(grp_cols, dropna=False).size().reset_index(name="ndefunciones")
    rows_all.append(grp)

    # Department-level aggregation (keep as-is)
    grp_dept = chunk.groupby(
        ["ANIO", "DEPARTAMENTO_FALLECIMIENTO", "grupo110"], dropna=False
    ).size().reset_index(name="ndefunciones")
    rows_dept.append(grp_dept)

    # National-level aggregation (sum across departments, by sexo + grupo110)
    grp_natl = chunk.groupby(
        ["ANIO", "sexo", "grupo110"], dropna=False
    ).size().reset_index(name="ndefunciones")
    rows_natl.append(grp_natl)

    print(
        f"  Chunk {chunk_idx:>3d}: {n_in:>7d} rows read, "
        f"{len(chunk):>7d} mapped | elapsed {time.time() - t0:.1f}s"
    )

# Concatenate accumulated results
print("  Aggregating SINADEF results ...")
sinadef_all = pd.concat(rows_all, ignore_index=True)
sinadef_all = sinadef_all.groupby(
    ["ANIO", "DEPARTAMENTO_FALLECIMIENTO", "sexo", "grupo110"], dropna=False
)["ndefunciones"].sum().reset_index()

sinadef_dept = pd.concat(rows_dept, ignore_index=True)
sinadef_dept = sinadef_dept.groupby(
    ["ANIO", "DEPARTAMENTO_FALLECIMIENTO", "grupo110"], dropna=False
)["ndefunciones"].sum().reset_index()

sinadef_natl = pd.concat(rows_natl, ignore_index=True)
sinadef_natl = sinadef_natl.groupby(
    ["ANIO", "sexo", "grupo110"], dropna=False
)["ndefunciones"].sum().reset_index()

# Total annual deaths from SINADEF
sinadef_total_anual = sinadef_all.groupby(["ANIO"])["ndefunciones"].sum().reset_index()

t1 = time.time()
print(f"\nSINADEF processing completed in {t1 - t0:.1f}s")
print(f"  Total rows accumulated: {sinadef_all['ndefunciones'].sum():,}")
print(f"  SIN REGISTRO (all CIEX): {total_sin_registro:,}")
print(f"  Total rows in chunks  : {chunk_idx * CHUNK_SIZE:,}")

# ── 2. Read INEI data ─────────────────────────────────────────────────────
print("\n" + "=" * 70)
print("STEP 2: Reading INEI data ...")
t2 = time.time()

inei_110 = pd.read_excel(INEI_GRUPO110_XLSX)
inei_110 = inei_110[inei_110["anofall"].between(2017, 2024)].copy()
# Standardize types
inei_110["anofall"] = inei_110["anofall"].astype(int)
inei_110["ndefun_"] = inei_110["ndefun_"].astype(int)

inei_10 = pd.read_excel(INEI_GRUPO10_XLSX, sheet_name="Tasa_Grupo10_LM_v1")
inei_10 = inei_10[inei_10["anofall"].between(2017, 2024)].copy()
inei_10["anofall"] = inei_10["anofall"].astype(int)
inei_10["ndefun_"] = inei_10["ndefun_"].astype(int)

print(f"  INEI grupo110 rows: {len(inei_110):,}")
print(f"  INEI grupo10  rows: {len(inei_10):,}")

# ── Department mapping setup ───────────────────────────────────────────────
# For INEI department-level: compute LIMA = LIMA METROPOLITANA + LIMA PROVINCIAS
inei_lima_110 = (
    inei_110[
        inei_110["Departamento"].isin(["LIMA METROPOLITANA", "LIMA PROVINCIAS"])
    ]
    .groupby(["anofall", "sexo", "grupo110"], dropna=False)["ndefun_"]
    .sum()
    .reset_index()
)
inei_lima_110["Departamento"] = "LIMA"

inei_lima_10 = (
    inei_10[
        inei_10["Departamento"].isin(["LIMA METROPOLITANA", "LIMA PROVINCIAS"])
    ]
    .groupby(["anofall", "sexo", "ggrupos"], dropna=False)["ndefun_"]
    .sum()
    .reset_index()
)
inei_lima_10["Departamento"] = "LIMA"

# Remove LIMA METROPOLITANA and LIMA PROVINCIAS from INEI, add computed LIMA
inei_110_dept = inei_110[
    ~inei_110["Departamento"].isin(["#PERU", "LIMA", "LIMA METROPOLITANA", "LIMA PROVINCIAS"])
].copy()
inei_110_dept = pd.concat([inei_110_dept, inei_lima_110], ignore_index=True)

inei_10_dept = inei_10[
    ~inei_10["Departamento"].isin(["#PERU", "LIMA", "LIMA METROPOLITANA", "LIMA PROVINCIAS"])
].copy()
inei_10_dept = pd.concat([inei_10_dept, inei_lima_10], ignore_index=True)

t3 = time.time()
print(f"INEI data loaded in {t3 - t2:.1f}s")

# ── 3. Comparisons ────────────────────────────────────────────────────────
print("\n" + "=" * 70)
print("STEP 3: Running comparisons ...")

# --- a) National by year and grupo110 ---
print("  a) National by year and grupo110")
sinadef_nat_g110 = (
    sinadef_natl.groupby(["ANIO", "grupo110"], dropna=False)["ndefunciones"]
    .sum()
    .reset_index()
)
inei_nat_g110 = inei_110[inei_110["sexo"] == "#Total"].copy()
inei_nat_g110 = inei_nat_g110[inei_nat_g110["Departamento"] == "#PERU"].copy()

comp_a = sinadef_nat_g110.merge(
    inei_nat_g110[["anofall", "grupo110", "ndefun_"]],
    left_on=["ANIO", "grupo110"],
    right_on=["anofall", "grupo110"],
    how="outer",
)
comp_a = compute_comparison(comp_a, ["ANIO", "grupo110"])
comp_a.rename(columns={"ANIO": "year"}, inplace=True)
comp_a = comp_a.dropna(subset=["year"]).copy()
comp_a["year"] = comp_a["year"].astype(int)
comp_a.sort_values(["year", "grupo110"], inplace=True)

# --- b) National by year, sex, grupo110 ---
print("  b) National by year, sex, grupo110")
inei_nat_sex_g110 = inei_110[inei_110["sexo"].isin(["Hombre", "Mujer"])].copy()
inei_nat_sex_g110 = inei_nat_sex_g110[
    inei_nat_sex_g110["Departamento"] == "#PERU"
].copy()

comp_b = sinadef_natl.merge(
    inei_nat_sex_g110[["anofall", "sexo", "grupo110", "ndefun_"]],
    left_on=["ANIO", "sexo", "grupo110"],
    right_on=["anofall", "sexo", "grupo110"],
    how="outer",
)
comp_b = compute_comparison(comp_b, ["ANIO", "sexo", "grupo110"])
comp_b.rename(columns={"ANIO": "year"}, inplace=True)
comp_b = comp_b.dropna(subset=["year"]).copy()
comp_b["year"] = comp_b["year"].astype(int)
comp_b.sort_values(["year", "sexo", "grupo110"], inplace=True)

# --- c) Department by year and grupo110 (total, matching depts) ---
print("  c) Department by year and grupo110")
# Skip EXTRANJERO and SIN REGISTRO from SINADEF
sinadef_dept_filtered = sinadef_dept[
    ~sinadef_dept["DEPARTAMENTO_FALLECIMIENTO"].isin(["EXTRANJERO", "SIN REGISTRO"])
]
inei_dept_total_g110 = inei_110_dept[inei_110_dept["sexo"] == "#Total"].copy()

# Get departments present in both
depts_sinadef = set(sinadef_dept_filtered["DEPARTAMENTO_FALLECIMIENTO"].unique())
depts_inei = set(inei_dept_total_g110["Departamento"].unique())
common_depts = depts_sinadef & depts_inei
print(f"  Common departments ({len(common_depts)}): {sorted(common_depts)}")

comp_c = sinadef_dept_filtered[
    sinadef_dept_filtered["DEPARTAMENTO_FALLECIMIENTO"].isin(common_depts)
].merge(
    inei_dept_total_g110[inei_dept_total_g110["Departamento"].isin(common_depts)][
        ["anofall", "Departamento", "grupo110", "ndefun_"]
    ],
    left_on=["ANIO", "DEPARTAMENTO_FALLECIMIENTO", "grupo110"],
    right_on=["anofall", "Departamento", "grupo110"],
    how="outer",
)
comp_c = compute_comparison(
    comp_c, ["ANIO", "DEPARTAMENTO_FALLECIMIENTO", "grupo110"]
)
comp_c.rename(
    columns={"ANIO": "year", "DEPARTAMENTO_FALLECIMIENTO": "departamento"},
    inplace=True,
)
comp_c = comp_c.dropna(subset=["year"]).copy()
comp_c["year"] = comp_c["year"].astype(int)
comp_c.sort_values(["year", "departamento", "grupo110"], inplace=True)

# --- d) National by year, grupo10 ---
print("  d) National by year and grupo10")
sinadef_nat_g10 = sinadef_nat_g110.copy()
sinadef_nat_g10["ggrupos"] = sinadef_nat_g10["grupo110"].apply(map_g110_to_g10)
sinadef_nat_g10 = (
    sinadef_nat_g10.groupby(["ANIO", "ggrupos"], dropna=False)["ndefunciones"]
    .sum()
    .reset_index()
)

# INEI grupo10: national, #Total
inei_nat_g10 = inei_10[(inei_10["sexo"] == "#Total") & (inei_10["Departamento"] == "#PERU")].copy()

comp_d = sinadef_nat_g10.merge(
    inei_nat_g10[["anofall", "ggrupos", "ndefun_"]],
    left_on=["ANIO", "ggrupos"],
    right_on=["anofall", "ggrupos"],
    how="outer",
)
comp_d = compute_comparison(comp_d, ["ANIO", "ggrupos"])
comp_d.rename(columns={"ANIO": "year"}, inplace=True)
comp_d = comp_d.dropna(subset=["year"]).copy()
comp_d["year"] = comp_d["year"].astype(int)
comp_d.sort_values(["year", "ggrupos"], inplace=True)

# --- e) Total defunciones by year ---
print("  e) Total defunciones by year")
inei_total_anual = (
    inei_nat_g110.groupby("anofall")["ndefun_"].sum().reset_index()
)

comp_e = sinadef_total_anual.merge(
    inei_total_anual,
    left_on="ANIO",
    right_on="anofall",
    how="outer",
)
comp_e = compute_comparison(comp_e, ["ANIO"])
comp_e.rename(columns={"ANIO": "year"}, inplace=True)
comp_e = comp_e.dropna(subset=["year"]).copy()
comp_e["year"] = comp_e["year"].astype(int)
comp_e.sort_values("year", inplace=True)

# --- f) Resumen de variacion ---
print("  f) Resumen de variacion")

# By year
resumen_year = comp_a.groupby("year", dropna=False).agg(
    ndefun_sinadef=("ndefun_sinadef", "sum"),
    ndefun_inei=("ndefun_inei", "sum"),
    causas_con_datos=("grupo110", "count"),
).reset_index()
resumen_year["diferencia_total"] = resumen_year["ndefun_inei"] - resumen_year["ndefun_sinadef"]
mask_y = resumen_year["ndefun_inei"] != 0
resumen_year["pct_diferencia"] = np.where(
    mask_y,
    (resumen_year["diferencia_total"] / resumen_year["ndefun_inei"]) * 100,
    np.nan,
)
# Filter out NaN years (from outer join) and convert to int
resumen_year = resumen_year.dropna(subset=["year"]).copy()
resumen_year["year"] = resumen_year["year"].astype(int)

# By grupo110
resumen_g110 = comp_a.groupby("grupo110", dropna=False).agg(
    ndefun_sinadef=("ndefun_sinadef", "sum"),
    ndefun_inei=("ndefun_inei", "sum"),
    years_with_data=("year", "nunique"),
).reset_index()
resumen_g110["diferencia_total"] = resumen_g110["ndefun_inei"] - resumen_g110["ndefun_sinadef"]
mask_g = resumen_g110["ndefun_inei"] != 0
resumen_g110["pct_diferencia"] = np.where(
    mask_g,
    (resumen_g110["diferencia_total"] / resumen_g110["ndefun_inei"]) * 100,
    np.nan,
)

t4 = time.time()
print(f"Comparisons completed in {t4 - t3:.1f}s")

# ── 4. Write output CSVs ──────────────────────────────────────────────────
print("\n" + "=" * 70)
print("STEP 4: Writing CSV outputs ...")

outputs = {
    "comparacion_nacional_grupo110.csv": comp_a,
    "comparacion_nacional_sexo_grupo110.csv": comp_b,
    "comparacion_departamental_grupo110.csv": comp_c,
    "comparacion_nacional_grupo10.csv": comp_d,
    "comparacion_total_anual.csv": comp_e,
    "resumen_variacion.csv": resumen_year,
}

for fname, df in outputs.items():
    path = os.path.join(OUTPUT_DIR, fname)
    df.to_csv(path, index=False, encoding="utf-8-sig")
    print(f"  {fname} ({len(df)} rows)")

# ── 5. Write Excel ────────────────────────────────────────────────────────
print("\nSTEP 5: Writing Excel workbook ...")
xlsx_path = os.path.join(OUTPUT_DIR, "comparacion_completa.xlsx")
if os.path.exists(xlsx_path):
    os.remove(xlsx_path)
with pd.ExcelWriter(xlsx_path, engine="openpyxl") as writer:
    comp_a.to_excel(writer, sheet_name="Nacional_Grupo110", index=False)
    comp_b.to_excel(writer, sheet_name="Nacional_Sexo_Grupo110", index=False)
    comp_c.to_excel(writer, sheet_name="Departamental_Grupo110", index=False)
    comp_d.to_excel(writer, sheet_name="Nacional_Grupo10", index=False)
    comp_e.to_excel(writer, sheet_name="Total_Anual", index=False)
    resumen_year.to_excel(writer, sheet_name="Resumen_Variacion", index=False)
print(f"  {xlsx_path}")

# ── 6. Print summary statistics ───────────────────────────────────────────
print("\n" + "=" * 70)
print("SUMMARY STATISTICS")
print("=" * 70)

# Overall match percentage per year
print("\n--- Overall match percentage by year ---")
for _, row in resumen_year.iterrows():
    y = int(row["year"])
    pct = row["pct_diferencia"]
    if pd.notna(pct):
        match_pct = 100.0 - abs(pct)
        print(
            f"  {y}: SINADEF={row['ndefun_sinadef']:>10,}  "
            f"INEI={row['ndefun_inei']:>10,}  "
            f"diff={pct:>+6.1f}%  "
            f"match={match_pct:.1f}%"
        )

# Top 10 causes with biggest discrepancies (by abs pct_diferencia)
print("\n--- Top 10 causas con mayores discrepancias (grupo110) ---")
top_causes = (
    comp_a.dropna(subset=["pct_diferencia"])
    .copy()
)
top_causes["abs_pct"] = top_causes["pct_diferencia"].abs()
top_causes = (
    top_causes.groupby("grupo110")
    .agg(
        ndefun_sinadef=("ndefun_sinadef", "sum"),
        ndefun_inei=("ndefun_inei", "sum"),
        pct_diferencia_avg=("pct_diferencia", "mean"),
    )
    .reset_index()
)
top_causes["diferencia"] = top_causes["ndefun_inei"] - top_causes["ndefun_sinadef"]
top_causes["abs_dif"] = top_causes["diferencia"].abs()
top_causes = top_causes.sort_values("abs_dif", ascending=False).head(10)
for _, row in top_causes.iterrows():
    g = row["grupo110"][:65]
    print(
        f"  {g:<65}  SIN={row['ndefun_sinadef']:>8,}  "
        f"INEI={row['ndefun_inei']:>8,}  "
        f"diff={row['diferencia']:>+8,}  "
        f"pct={row['pct_diferencia_avg']:>+6.1f}%"
    )

# Departments with best/worst match
print("\n--- Top 5 deptos con mejor/peor match (por diferencia absoluta total) ---")
dept_summary = (
    comp_c.dropna(subset=["pct_diferencia"])
    .groupby("departamento")
    .agg(
        ndefun_sinadef=("ndefun_sinadef", "sum"),
        ndefun_inei=("ndefun_inei", "sum"),
    )
    .reset_index()
)
dept_summary["diferencia"] = dept_summary["ndefun_inei"] - dept_summary["ndefun_sinadef"]
mask_d = dept_summary["ndefun_inei"] != 0
dept_summary["pct"] = np.where(
    mask_d,
    (dept_summary["diferencia"] / dept_summary["ndefun_inei"]) * 100,
    np.nan,
)
dept_summary = dept_summary.sort_values("diferencia")

print("  Best (most negative diff → SINADEF > INEI):")
for _, row in dept_summary.head(5).iterrows():
    print(
        f"    {row['departamento']:<25}  SIN={row['ndefun_sinadef']:>10,}  "
        f"INEI={row['ndefun_inei']:>10,}  diff={row['diferencia']:>+10,}  "
        f"pct={row['pct']:>+6.1f}%"
    )
print("  Worst (most positive diff → INEI > SINADEF):")
for _, row in dept_summary.tail(5).iterrows():
    print(
        f"    {row['departamento']:<25}  SIN={row['ndefun_sinadef']:>10,}  "
        f"INEI={row['ndefun_inei']:>10,}  diff={row['diferencia']:>+10,}  "
        f"pct={row['pct']:>+6.1f}%"
    )

# How many SINADEF deaths couldn't be mapped (SIN REGISTRO)
print(f"\n--- Registros SIN REGISTRO ---")
print(f"  Muertes con todos los CIEX = 'SIN REGISTRO': {total_sin_registro:,}")
print(f"  Porcentaje del total procesado: {total_sin_registro / max(sinadef_all['ndefunciones'].sum(), 1) * 100:.2f}%")

print("\n" + "=" * 70)
print("DONE")
print(f"Total elapsed: {time.time() - t0:.1f}s")
print(f"Output directory: {OUTPUT_DIR}")
