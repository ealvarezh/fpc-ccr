import sys
import pandas as pd
import numpy as np
import gc
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
pd.set_option("display.max_columns", None)

SILVER = Path(r"C:\Users\eah\apoyoconsultoria.com\File Server - Analytics\7 Datos\Datos abiertos\fissal\01_silver")
ARCHIVO_EST = SILVER / "FISSAL_CANCER_ESTOMAGO_2016_2022.parquet"
ARCHIVO_PERFIL = SILVER / "FISSAL_ESTOMAGO_PERFIL_PACIENTES.parquet"
DICCIONARIO_502 = Path(
    r"C:\Users\eah\apoyoconsultoria.com\File Server - Analytics\3 Proyectos\2025"
    r"\2025-116-L FPC Dashboard 25\4 Analisis\3 Programas\adicional 2026"
    r"\diccionario_ATE_DESCCONSUMO_502_estandarizado.xlsx"
)
ANIOS = range(2016, 2023)

print("=" * 70)
print("CONSTRUCCION DE HITOS DEL PACIENTE — CANCER DE ESTOMAGO (C16)")
print("FISSAL 2016-2022")
print("=" * 70)
print("""
Mismo marco de 4 hitos que cancer colorrectal (Despistaje, Diagnostico,
Tratamiento, Desenlace), mismas ventanas de tiempo/costo. Diferencias:
  - CIRUGIA: regex de gastrectomia/gastroyeyunostomia/esofagoyeyunostomia
    (en vez de colectomia/hemicolectomia).
  - QUIMIOTERAPIA: mismos farmacos de CRC + DOCETAXEL/CISPLATINO/EPIRUBICINA
    (esquemas gastricos tipo ECF).
  - HITO 4 (Desenlace) SIMPLIFICADO: FECHA_DESENLACE = fallecimiento o
    ultima atencion, SIN la clasificacion de recaida/paliativo/remision que
    tiene CRC (no se necesita para comparar costo/tiempo por hito).
""")

df = pd.read_parquet(ARCHIVO_EST)
perfil = pd.read_parquet(ARCHIVO_PERFIL)
print(f"Registros estomago: {len(df):,} | Pacientes: {perfil.shape[0]:,}")

pac_est = set(perfil["NUM_DOC_CRYPTO"])
primera_atencion = perfil.set_index("NUM_DOC_CRYPTO")["PRIMERA_ATENCION"]

# =====================================================================
# HITO 1: DESPISTAJE / DETECCION (antes del diagnostico)
# =====================================================================
print("\n" + "=" * 70)
print("HITO 1: DESPISTAJE / DETECCION")
print("=" * 70)

PAT_DESPISTAJE = {
    "BIOPSIA": r"(?i)BIOPSI|ANATOMOPATOLOG",
    "ENDOSCOPIA": r"(?i)COLONOSCOP|ENDOSCOP|RECTOSCOP|SIGMOIDOSCOP|GASTROSCOP",
    "IMAGEN": r"(?i)TOMOGRAF|RESONAN|ECOGRAF|GAMMAGRAF|PET.?SCAN|RADIOGRAF",
    "LABORATORIO_MARCADOR": r"(?i)\bCEA\b|ANTIGEN.*CARCINO|SANGRE.*OCULTA|\bCA.?19.?9\b",
}
COLS_YR = ["NUM_DOC_CRYPTO", "ATE_FECATENCION", "ATE_DESCCONSUMO", "ATE_MONTONETO", "ATE_MONTOBRUTO"]

primer_contacto = {}
agg_pre_dx_list = []
eventos_despistaje_list = []

for yr in ANIOS:
    archivo = SILVER / f"FISSAL_PRESTACIONES_{yr}.parquet"
    if not archivo.exists():
        continue
    print(f"  Procesando {yr}...", end=" ")
    df_yr = pd.read_parquet(archivo, columns=COLS_YR)
    df_yr = df_yr[df_yr["NUM_DOC_CRYPTO"].isin(pac_est)].copy()
    df_yr["FECHA_DX"] = df_yr["NUM_DOC_CRYPTO"].map(primera_atencion)

    contacto_yr = df_yr.groupby("NUM_DOC_CRYPTO")["ATE_FECATENCION"].min()
    for pid, fecha in contacto_yr.items():
        if pid not in primer_contacto or fecha < primer_contacto[pid]:
            primer_contacto[pid] = fecha

    df_pre = df_yr[df_yr["ATE_FECATENCION"] < df_yr["FECHA_DX"]]
    n_pre = len(df_pre)

    if n_pre > 0:
        agg_yr = df_pre.groupby("NUM_DOC_CRYPTO").agg(
            N_REG_PRE=("ATE_FECATENCION", "size"),
            COSTO_NETO_PRE=("ATE_MONTONETO", "sum"),
            COSTO_BRUTO_PRE=("ATE_MONTOBRUTO", "sum"),
        ).reset_index()
        agg_pre_dx_list.append(agg_yr)

        for cat, pat in PAT_DESPISTAJE.items():
            mask = df_pre["ATE_DESCCONSUMO"].str.contains(pat, na=False)
            if mask.any():
                sub = df_pre.loc[mask, ["NUM_DOC_CRYPTO", "ATE_FECATENCION"]].copy()
                sub["TIPO_DESPISTAJE"] = cat
                eventos_despistaje_list.append(sub)

    print(f"{n_pre:,} registros pre-diagnostico")
    del df_yr, df_pre
    gc.collect()

if agg_pre_dx_list:
    agg_pre_dx = pd.concat(agg_pre_dx_list, ignore_index=True).groupby("NUM_DOC_CRYPTO").agg(
        N_REGISTROS_PRE_DIAGNOSTICO=("N_REG_PRE", "sum"),
        COSTO_NETO_PRE_DIAGNOSTICO=("COSTO_NETO_PRE", "sum"),
        COSTO_BRUTO_PRE_DIAGNOSTICO=("COSTO_BRUTO_PRE", "sum"),
    ).reset_index()
else:
    agg_pre_dx = pd.DataFrame(columns=["NUM_DOC_CRYPTO", "N_REGISTROS_PRE_DIAGNOSTICO",
                                        "COSTO_NETO_PRE_DIAGNOSTICO", "COSTO_BRUTO_PRE_DIAGNOSTICO"])

if eventos_despistaje_list:
    eventos_despistaje = pd.concat(eventos_despistaje_list, ignore_index=True)
    primer_desp = (
        eventos_despistaje.sort_values("ATE_FECATENCION")
        .groupby("NUM_DOC_CRYPTO").first()[["ATE_FECATENCION", "TIPO_DESPISTAJE"]]
        .rename(columns={"ATE_FECATENCION": "FECHA_PRIMER_DESPISTAJE"})
        .reset_index()
    )
else:
    primer_desp = pd.DataFrame(columns=["NUM_DOC_CRYPTO", "FECHA_PRIMER_DESPISTAJE", "TIPO_DESPISTAJE"])

hito1 = pd.DataFrame({"NUM_DOC_CRYPTO": list(pac_est)})
hito1["FECHA_DIAGNOSTICO"] = hito1["NUM_DOC_CRYPTO"].map(primera_atencion)
hito1["FECHA_PRIMER_CONTACTO_SISTEMA"] = hito1["NUM_DOC_CRYPTO"].map(primer_contacto)
hito1 = hito1.merge(agg_pre_dx, on="NUM_DOC_CRYPTO", how="left")
hito1 = hito1.merge(primer_desp, on="NUM_DOC_CRYPTO", how="left")

for c in ["N_REGISTROS_PRE_DIAGNOSTICO", "COSTO_NETO_PRE_DIAGNOSTICO", "COSTO_BRUTO_PRE_DIAGNOSTICO"]:
    hito1[c] = hito1[c].fillna(0)

hito1["TUVO_DESPISTAJE_PREVIO"] = hito1["FECHA_PRIMER_DESPISTAJE"].notna()
hito1["DIAS_DESPISTAJE_A_DIAGNOSTICO"] = (hito1["FECHA_DIAGNOSTICO"] - hito1["FECHA_PRIMER_DESPISTAJE"]).dt.days

print(f"\n  Pacientes con despistaje previo detectado: {hito1['TUVO_DESPISTAJE_PREVIO'].sum():,} "
      f"({hito1['TUVO_DESPISTAJE_PREVIO'].mean()*100:.1f}%)")
print(f"  Pacientes con alguna actividad pre-diagnostico: "
      f"{(hito1['N_REGISTROS_PRE_DIAGNOSTICO']>0).sum():,} "
      f"({(hito1['N_REGISTROS_PRE_DIAGNOSTICO']>0).mean()*100:.1f}%)")

# =====================================================================
# HITO 3: TRATAMIENTO (cirugia, quimioterapia, radioterapia — gastrico)
# =====================================================================
print("\n" + "=" * 70)
print("HITO 3: TRATAMIENTO")
print("=" * 70)

PAT_TRAT = {
    "CIRUGIA": r"(?i)GASTRECTOM|GASTROYEYUNO|ESOFAGOYEYUNO|ESOFAGOGASTRECTOM|BILLROTH",
    "QUIMIOTERAPIA": r"(?i)QUIMIOTER|INFUSION.*QUIMIO|ADMINISTRACION.*QUIMIO|OXALIPLAT|FLUOROURAC|CAPECITAB|IRINOTECAN|LEUCOVORIN|BEVACIZUM|CETUXIMAB|PANITUMUM|RALTITREX|REGORAFEN|TRIFLURID|DOCETAXEL|CISPLATINO|EPIRUBICIN",
    "RADIOTERAPIA": r"(?i)RADIOTER|COBALTOT|BRAQUIT|ACELERADOR",
}

df["CATEGORIA_TRAT"] = "OTRO"
for cat, pat in PAT_TRAT.items():
    mask = df["ATE_DESCCONSUMO"].str.contains(pat, na=False)
    df.loc[mask, "CATEGORIA_TRAT"] = cat

# --- Complemento: deteccion via diccionario categoria_recurso_502 (misma logica que CRC) ---
print("  Cargando diccionario 502 para complementar deteccion de tratamiento...")
dic = pd.read_excel(DICCIONARIO_502, sheet_name="Diccionario_502",
                     usecols=["ATE_DESCCONSUMO", "categoria_recurso_502", "subcategoria_recurso_502"])
dic["ATE_DESCCONSUMO"] = dic["ATE_DESCCONSUMO"].str.strip()
dic = dic.drop_duplicates(subset="ATE_DESCCONSUMO")

df["_DESC_STRIP"] = df["ATE_DESCCONSUMO"].str.strip()
df = df.merge(dic, left_on="_DESC_STRIP", right_on="ATE_DESCCONSUMO", how="left", suffixes=("", "_DIC"))
df = df.drop(columns=["_DESC_STRIP", "ATE_DESCCONSUMO_DIC"])

# Nota: a diferencia de CRC (que usa la subcategoria "Cirugia colorrectal" /
# "Cirugia digestiva"), aqui NO existe una subcategoria "Cirugia gastrica"
# separada en el diccionario -- la cirugia gastrica cae bajo "Cirugia
# digestiva", asi que esa es la unica subcategoria que se usa como señal de
# CIRUGIA (no se usa "Cirugia colorrectal", que es especifica de colon/recto).
SUBCAT_A_TRAT = {
    "Antineoplásico / terapia oncológica sistémica": "QUIMIOTERAPIA",
    "Administración de quimioterapia": "QUIMIOTERAPIA",
    "Cirugía digestiva": "CIRUGIA",
}
sin_clasificar_regex = df["CATEGORIA_TRAT"] == "OTRO"
for subcat, cat in SUBCAT_A_TRAT.items():
    mask = sin_clasificar_regex & (df["subcategoria_recurso_502"] == subcat)
    df.loc[mask, "CATEGORIA_TRAT"] = cat
mask_radio = sin_clasificar_regex & (df["categoria_recurso_502"] == "Radioterapia")
df.loc[mask_radio, "CATEGORIA_TRAT"] = "RADIOTERAPIA"
df = df.drop(columns=["categoria_recurso_502", "subcategoria_recurso_502"])

n_reclasificado_dic = (sin_clasificar_regex & (df["CATEGORIA_TRAT"] != "OTRO")).sum()
print(f"  [Diccionario 502] {n_reclasificado_dic:,} registro(s) reclasificados via diccionario.")

modalidades = []
for cat in PAT_TRAT:
    sub = df[df["CATEGORIA_TRAT"] == cat]
    ep = sub.groupby("NUM_DOC_CRYPTO").agg(**{
        f"N_SESIONES_{cat}": ("ATE_FECATENCION", "nunique"),
        f"FECHA_INICIO_{cat}": ("ATE_FECATENCION", "min"),
        f"FECHA_FIN_{cat}": ("ATE_FECATENCION", "max"),
        f"COSTO_NETO_{cat}": ("ATE_MONTONETO", "sum"),
    }).reset_index()
    modalidades.append(ep)

hito3 = modalidades[0]
for m in modalidades[1:]:
    hito3 = hito3.merge(m, on="NUM_DOC_CRYPTO", how="outer")

fecha_inicio_cols = [f"FECHA_INICIO_{c}" for c in PAT_TRAT]
hito3["FECHA_INICIO_TRATAMIENTO"] = hito3[fecha_inicio_cols].min(axis=1)
hito3["FECHA_FIN_TRATAMIENTO"] = hito3[[f"FECHA_FIN_{c}" for c in PAT_TRAT]].max(axis=1)


def secuencia(row):
    pares = [(row[f"FECHA_INICIO_{c}"], c) for c in PAT_TRAT if pd.notna(row[f"FECHA_INICIO_{c}"])]
    pares.sort(key=lambda x: x[0])
    return " > ".join(c for _, c in pares) if pares else "SIN_TRATAMIENTO_DETECTADO"


hito3["SECUENCIA_TRATAMIENTO"] = hito3.apply(secuencia, axis=1)
hito3 = hito3.merge(hito1[["NUM_DOC_CRYPTO"]], on="NUM_DOC_CRYPTO", how="right")
hito3["SECUENCIA_TRATAMIENTO"] = hito3["SECUENCIA_TRATAMIENTO"].fillna("SIN_TRATAMIENTO_DETECTADO")

for c in PAT_TRAT:
    hito3[f"N_SESIONES_{c}"] = hito3[f"N_SESIONES_{c}"].fillna(0)
    hito3[f"COSTO_NETO_{c}"] = hito3[f"COSTO_NETO_{c}"].fillna(0)
    hito3[f"TUVO_{c}"] = hito3[f"N_SESIONES_{c}"] > 0

hito3 = hito3.merge(hito1[["NUM_DOC_CRYPTO", "FECHA_DIAGNOSTICO"]], on="NUM_DOC_CRYPTO", how="left")
hito3["DIAS_DIAGNOSTICO_A_TRATAMIENTO"] = (hito3["FECHA_INICIO_TRATAMIENTO"] - hito3["FECHA_DIAGNOSTICO"]).dt.days

n_trat = (hito3["SECUENCIA_TRATAMIENTO"] != "SIN_TRATAMIENTO_DETECTADO").sum()
print(f"\n  Pacientes con algun tratamiento detectado: {n_trat:,} ({n_trat/len(hito3)*100:.1f}%)")
for c in PAT_TRAT:
    n = hito3[f"TUVO_{c}"].sum()
    print(f"    {c:>15s}: {n:>6,} ({n/len(hito3)*100:5.1f}%)")

del df
gc.collect()

# =====================================================================
# HITO 4: DESENLACE (SIMPLIFICADO — sin recaida/paliativo)
# =====================================================================
print("\n" + "=" * 70)
print("HITO 4: DESENLACE (simplificado)")
print("=" * 70)
print("""
  NOTA: a diferencia de CRC, aqui NO se construye la clasificacion de
  RECAIDA_PROBABLE/CONTROL_POST_PAUSA/POSIBLE_REMISION_O_ALTA/PALIATIVO
  (requeria datos de cuidados paliativos y sitios de metastasis que no
  se necesitan para comparar costo/tiempo por hito). FECHA_DESENLACE es
  simplemente fecha de fallecimiento si fallecio, o ultima atencion si no.
""")

hito4 = perfil[["NUM_DOC_CRYPTO", "FALLECIDO", "FEC_FALLECIMIENTO", "ULTIMA_ATENCION"]].copy()
hito4["FECHA_DESENLACE"] = np.where(hito4["FALLECIDO"], hito4["FEC_FALLECIMIENTO"], hito4["ULTIMA_ATENCION"])
hito4["FECHA_DESENLACE"] = pd.to_datetime(hito4["FECHA_DESENLACE"])

print(f"  Fallecidos: {hito4['FALLECIDO'].sum():,} ({hito4['FALLECIDO'].mean()*100:.1f}%)")

# =====================================================================
# CONSOLIDACION
# =====================================================================
print("\n" + "=" * 70)
print("CONSOLIDANDO TABLA DE HITOS POR PACIENTE (ESTOMAGO)")
print("=" * 70)

cols_perfil = ["NUM_DOC_CRYPTO", "SEXO", "EDAD_PRIMERA_ATENCION", "RANGO_EDAD",
               "DEPARTAMENTO", "PROVINCIA", "MONTO_NETO_TOTAL", "MONTO_BRUTO_TOTAL"]
hitos_pac = perfil[cols_perfil].merge(hito1, on="NUM_DOC_CRYPTO", how="left")
hitos_pac = hitos_pac.merge(hito3.drop(columns=["FECHA_DIAGNOSTICO"]), on="NUM_DOC_CRYPTO", how="left")
hitos_pac = hitos_pac.merge(hito4.drop(columns=["FEC_FALLECIMIENTO"]), on="NUM_DOC_CRYPTO", how="left")

print(f"  Tabla final: {len(hitos_pac):,} pacientes x {hitos_pac.shape[1]} columnas")

out_pac = SILVER / "FISSAL_ESTOMAGO_HITOS_PACIENTE.parquet"
hitos_pac.to_parquet(out_pac, index=False)
print(f"  Guardado: {out_pac}")

print(f"\n{'=' * 70}")
print("Fin de la construccion de hitos de estomago.")
print(f"{'=' * 70}")
