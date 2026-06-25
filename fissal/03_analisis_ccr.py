import pandas as pd
import numpy as np
import sys
import gc
from pathlib import Path

SILVER = Path(r"C:\Users\eah\apoyoconsultoria.com\File Server - Analytics\7 Datos\Datos abiertos\fissal\01_silver")
ARCHIVO = SILVER / "FISSAL_CANCER_COLORRECTAL_2016_2022.parquet"

print("=" * 70)
print("ANALISIS PROFUNDO DE PROCEDIMIENTOS POR PACIENTE")
print("CANCER COLORRECTAL (C18/C19/C20) — FISSAL 2016-2022")
print("=" * 70)

df = pd.read_parquet(ARCHIVO)
print(f"Registros totales: {len(df):,} | Pacientes: {df['NUM_DOC_CRYPTO'].nunique():,}")

PAT = {
    "CIRUGIA": r"(?i)COLECTOM|RESECC|HEMICOLEC|COLOSTOM|LAPAROTOM|ANASTOMOS|LAPAROSCOP",
    "QUIMIOTERAPIA_PROC": r"(?i)QUIMIOTER|INFUSION.*QUIMIO|ADMINISTRACION.*QUIMIO",
    "QUIMIO_MEDICAMENTO": r"(?i)OXALIPLAT|FLUOROURAC|CAPECITAB|IRINOTECAN|LEUCOVORIN|BEVACIZUM|CETUXIMAB|PANITUMUM|RALTITREX|REGORAFEN|TRIFLURID",
    "RADIOTERAPIA": r"(?i)RADIOTER|COBALTOT|BRAQUIT|ACELERADOR",
    "BIOPSIA": r"(?i)BIOPSI|ANATOMOPATOLOG",
    "ENDOSCOPIA": r"(?i)COLONOSCOP|ENDOSCOP|RECTOSCOP|SIGMOIDOSCOP",
    "IMAGEN": r"(?i)TOMOGRAF|RESONAN|ECOGRAF|GAMMAGRAF|PET.?SCAN",
    "LABORATORIO": r"(?i)HEMOGRAM|CEA|ANTIGEN.*CARCINO|CREATININ|TRANSAMIN|ALBUMIN|HEMOGLOBIN|BILIRRUBIN|FOSFATASA",
    "TRANSFUSION": r"(?i)TRANSFUS|CONCENTRADO.*GLOBUL|PAQUETE.*GLOBUL",
    "CUIDADO_PALIATIVO": r"(?i)PALIATIV|DOLOR.*CRONICO|MANEJO.*DOLOR",
    "NUTRICION": r"(?i)NUTRICION.*PARENTERAL|NUTRICION.*ENTERAL|SOPORTE.*NUTRIC",
    "CONSULTA": r"(?i)CONSULTA.*MEDIC|CONSULTA.*AMBULAT|CONSULTA.*ESPECIAL",
    "ENFERMERIA": r"(?i)ATENCION.*ENFERM|CUIDADO.*ENFERM",
    "UCI": r"(?i)CUIDADO.*INTENSIV|UCI",
}


def clasificar_registro(desc):
    if pd.isna(desc):
        return "SIN_DESCRIPCION"
    for cat, pat in PAT.items():
        if pd.notna(desc) and bool(pd.Series([desc]).str.contains(pat, na=False).iloc[0]):
            return cat
    return "OTRO"


print("\nClasificando registros por categoria...")
df["CATEGORIA"] = "OTRO"
df.loc[df["ATE_DESCCONSUMO"].isna(), "CATEGORIA"] = "SIN_DESCRIPCION"
for cat, pat in reversed(list(PAT.items())):
    mask = df["ATE_DESCCONSUMO"].str.contains(pat, na=False)
    df.loc[mask, "CATEGORIA"] = cat

total_cat = df["CATEGORIA"].value_counts()
print("\n--- Registros por categoria ---")
for cat, n in total_cat.items():
    n_pac = df.loc[df["CATEGORIA"] == cat, "NUM_DOC_CRYPTO"].nunique()
    monto = df.loc[df["CATEGORIA"] == cat, "ATE_MONTONETO"].sum()
    print(f"  {cat:>25s}: {n:>8,} reg | {n_pac:>6,} pac | S/{monto:>14,.2f}")


# =====================================================================
# 1. CATEGORIAS DE TRATAMIENTO POR PACIENTE
# =====================================================================
print("\n" + "=" * 70)
print("1. COMBINACIONES DE TRATAMIENTO POR PACIENTE")
print("=" * 70)

cats_clave = ["CIRUGIA", "QUIMIOTERAPIA_PROC", "QUIMIO_MEDICAMENTO", "RADIOTERAPIA",
              "ENDOSCOPIA", "BIOPSIA", "IMAGEN", "LABORATORIO", "TRANSFUSION"]

pac_cats = df.groupby("NUM_DOC_CRYPTO")["CATEGORIA"].apply(set).reset_index()
pac_cats.columns = ["NUM_DOC_CRYPTO", "CATEGORIAS"]

for cat in cats_clave:
    pac_cats[cat] = pac_cats["CATEGORIAS"].apply(lambda x: cat in x)

pac_cats["TUVO_QUIMIO"] = pac_cats["QUIMIOTERAPIA_PROC"] | pac_cats["QUIMIO_MEDICAMENTO"]

print("\n--- Pacientes por tipo de tratamiento recibido ---")
for cat in ["CIRUGIA", "TUVO_QUIMIO", "RADIOTERAPIA", "ENDOSCOPIA", "BIOPSIA",
            "IMAGEN", "LABORATORIO", "TRANSFUSION"]:
    n = pac_cats[cat].sum()
    print(f"  {cat:>20s}: {n:>6,} ({n/len(pac_cats)*100:5.1f}%)")

print("\n--- Combinaciones de tratamiento (Cirugia + Quimio + Radio) ---")
pac_cats["COMBO"] = (
    pac_cats["CIRUGIA"].map({True: "CIR", False: ""}) + "+" +
    pac_cats["TUVO_QUIMIO"].map({True: "QT", False: ""}) + "+" +
    pac_cats["RADIOTERAPIA"].map({True: "RT", False: ""})
)
pac_cats["COMBO"] = pac_cats["COMBO"].str.strip("+").str.replace(r"\++", "+", regex=True)
pac_cats.loc[pac_cats["COMBO"] == "", "COMBO"] = "NINGUNO"

combos = pac_cats["COMBO"].value_counts()
for combo, n in combos.items():
    print(f"  {combo:>20s}: {n:>6,} ({n/len(pac_cats)*100:5.1f}%)")


# =====================================================================
# 2. VOLUMEN DE PROCEDIMIENTOS POR PACIENTE
# =====================================================================
print("\n" + "=" * 70)
print("2. VOLUMEN DE PROCEDIMIENTOS POR PACIENTE")
print("=" * 70)

proc_pac = df.groupby("NUM_DOC_CRYPTO").agg(
    N_REGISTROS=("ATE_DESCCONSUMO", "size"),
    N_FUA=("ATE_FUA", "nunique"),
    N_ITEMS_DISTINTOS=("ATE_CODCONSUMO", "nunique"),
).reset_index()

print(f"\n--- Registros (prestaciones) por paciente ---")
for stat, val in proc_pac["N_REGISTROS"].describe().items():
    print(f"  {stat:>5s}: {val:>10,.1f}")

print(f"\n--- Atenciones (FUA) por paciente ---")
for stat, val in proc_pac["N_FUA"].describe().items():
    print(f"  {stat:>5s}: {val:>10,.1f}")

print(f"\n--- Distribucion de atenciones por paciente ---")
bins = [0, 1, 2, 5, 10, 20, 50, 100, 500]
labels = ["1", "2", "3-5", "6-10", "11-20", "21-50", "51-100", "100+"]
proc_pac["RANGO_FUA"] = pd.cut(proc_pac["N_FUA"], bins=bins, labels=labels, right=True)
dist = proc_pac["RANGO_FUA"].value_counts().sort_index()
for r, n in dist.items():
    print(f"  {r:>8s} atenciones: {n:>6,} pac ({n/len(proc_pac)*100:5.1f}%)")


# =====================================================================
# 3. TIEMPOS ENTRE HITOS CLAVE DEL TRATAMIENTO
# =====================================================================
print("\n" + "=" * 70)
print("3. TIEMPOS ENTRE HITOS CLAVE DEL TRATAMIENTO")
print("=" * 70)

print("\nCalculando hitos por paciente...")
hitos = df.groupby("NUM_DOC_CRYPTO")["ATE_FECATENCION"].agg(
    PRIMERA_ATENCION="min", ULTIMA_ATENCION="max"
).reset_index()

for cat_name, col_name in [("BIOPSIA", "PRIMERA_BIOPSIA"),
                             ("ENDOSCOPIA", "PRIMERA_ENDOSCOPIA"),
                             ("CIRUGIA", "PRIMERA_CIRUGIA"),
                             ("IMAGEN", "PRIMERA_IMAGEN"),
                             ("RADIOTERAPIA", "PRIMERA_RADIO")]:
    sub = (df[df["CATEGORIA"] == cat_name]
           .groupby("NUM_DOC_CRYPTO")["ATE_FECATENCION"].min()
           .reset_index().rename(columns={"ATE_FECATENCION": col_name}))
    hitos = hitos.merge(sub, on="NUM_DOC_CRYPTO", how="left")

sub_qt = (df[df["CATEGORIA"].isin(["QUIMIOTERAPIA_PROC", "QUIMIO_MEDICAMENTO"])]
          .groupby("NUM_DOC_CRYPTO")["ATE_FECATENCION"].min()
          .reset_index().rename(columns={"ATE_FECATENCION": "PRIMERA_QUIMIO"}))
hitos = hitos.merge(sub_qt, on="NUM_DOC_CRYPTO", how="left")

print("\n--- Dias desde primera atencion hasta cada hito ---")
for hito in ["PRIMERA_BIOPSIA", "PRIMERA_ENDOSCOPIA", "PRIMERA_IMAGEN",
             "PRIMERA_CIRUGIA", "PRIMERA_QUIMIO", "PRIMERA_RADIO"]:
    dias = (hitos[hito] - hitos["PRIMERA_ATENCION"]).dt.days.dropna()
    if len(dias) == 0:
        continue
    dias_pos = dias[dias >= 0]
    n_total = dias.notna().sum()
    print(f"\n  {hito}:")
    print(f"    N pacientes: {n_total:,}")
    if len(dias_pos) > 0:
        print(f"    Media:   {dias_pos.mean():>7.1f} dias ({dias_pos.mean()/30:.1f} meses)")
        print(f"    Mediana: {dias_pos.median():>7.0f} dias ({dias_pos.median()/30:.1f} meses)")
        print(f"    P25:     {dias_pos.quantile(0.25):>7.0f} dias")
        print(f"    P75:     {dias_pos.quantile(0.75):>7.0f} dias")
        print(f"    P95:     {dias_pos.quantile(0.95):>7.0f} dias")

print("\n--- Dias entre cirugia y primera quimio (adyuvante) ---")
mask = hitos["PRIMERA_CIRUGIA"].notna() & hitos["PRIMERA_QUIMIO"].notna()
if mask.any():
    dias_cir_qt = (hitos.loc[mask, "PRIMERA_QUIMIO"] - hitos.loc[mask, "PRIMERA_CIRUGIA"]).dt.days
    qt_post_cir = dias_cir_qt[dias_cir_qt > 0]
    qt_pre_cir = dias_cir_qt[dias_cir_qt < 0]
    qt_mismo = dias_cir_qt[dias_cir_qt == 0]
    print(f"  Pacientes con ambos: {mask.sum():,}")
    print(f"    Quimio ANTES de cirugia (neoadyuvante): {len(qt_pre_cir):,}")
    print(f"    Quimio DESPUES de cirugia (adyuvante):  {len(qt_post_cir):,}")
    print(f"    Mismo dia:                              {len(qt_mismo):,}")
    if len(qt_post_cir) > 0:
        print(f"    Dias cirugia -> quimio (adyuvante):")
        print(f"      Media:   {qt_post_cir.mean():.0f} dias ({qt_post_cir.mean()/30:.1f} meses)")
        print(f"      Mediana: {qt_post_cir.median():.0f} dias ({qt_post_cir.median()/30:.1f} meses)")
    if len(qt_pre_cir) > 0:
        print(f"    Dias quimio -> cirugia (neoadyuvante):")
        pre = qt_pre_cir.abs()
        print(f"      Media:   {pre.mean():.0f} dias ({pre.mean()/30:.1f} meses)")
        print(f"      Mediana: {pre.median():.0f} dias ({pre.median()/30:.1f} meses)")


# =====================================================================
# 4. PROCEDIMIENTOS TOP POR CATEGORIA DETALLADO
# =====================================================================
print("\n" + "=" * 70)
print("4. TOP PROCEDIMIENTOS POR CATEGORIA")
print("=" * 70)

for cat in ["CIRUGIA", "QUIMIOTERAPIA_PROC", "QUIMIO_MEDICAMENTO", "ENDOSCOPIA",
            "BIOPSIA", "IMAGEN", "TRANSFUSION", "RADIOTERAPIA"]:
    sub = df[df["CATEGORIA"] == cat]
    if len(sub) == 0:
        continue
    print(f"\n--- {cat} ({len(sub):,} reg | {sub['NUM_DOC_CRYPTO'].nunique():,} pac) ---")
    top = sub.groupby("ATE_DESCCONSUMO").agg(
        N_REG=("ATE_DESCCONSUMO", "size"),
        N_PAC=("NUM_DOC_CRYPTO", "nunique"),
        MONTO=("ATE_MONTONETO", "sum"),
    ).nlargest(15, "N_REG")
    for desc, row in top.iterrows():
        print(f"  {row['N_REG']:>6,} reg | {row['N_PAC']:>5,} pac | S/{row['MONTO']:>12,.2f} | {desc}")


# =====================================================================
# 5. INTENSIDAD DE TRATAMIENTO EN EL TIEMPO
# =====================================================================
print("\n" + "=" * 70)
print("5. INTENSIDAD DE TRATAMIENTO: PROCEDIMIENTOS POR MES POR PACIENTE")
print("=" * 70)

df["MES_ATENCION"] = df["ATE_FECATENCION"].dt.to_period("M")
intensidad = df.groupby(["NUM_DOC_CRYPTO", "MES_ATENCION"]).size().reset_index(name="N_ITEMS")

print(f"\n--- Items por paciente-mes (cuando hay actividad) ---")
for stat, val in intensidad["N_ITEMS"].describe().items():
    print(f"  {stat:>5s}: {val:>8,.1f}")

meses_activos = intensidad.groupby("NUM_DOC_CRYPTO").size()
print(f"\n--- Meses activos por paciente ---")
print(f"  Media:   {meses_activos.mean():.1f}")
print(f"  Mediana: {meses_activos.median():.0f}")
print(f"  P75:     {meses_activos.quantile(0.75):.0f}")
print(f"  P95:     {meses_activos.quantile(0.95):.0f}")
print(f"  Max:     {meses_activos.max()}")


# =====================================================================
# 6. TRAYECTORIA TIPICA: SECUENCIA DE CATEGORIAS
# =====================================================================
print("\n" + "=" * 70)
print("6. PRIMERA CATEGORIA DE ATENCION POR PACIENTE")
print("=" * 70)

primera_cat = (
    df.sort_values("ATE_FECATENCION")
    .groupby("NUM_DOC_CRYPTO")["CATEGORIA"]
    .first()
    .value_counts()
)
print("\n--- Primera categoria registrada ---")
for cat, n in primera_cat.items():
    print(f"  {cat:>25s}: {n:>6,} ({n/len(pac_cats)*100:5.1f}%)")


# =====================================================================
# 7. ANALISIS POR TIPO DE ATENCION Y CATEGORIA
# =====================================================================
print("\n" + "=" * 70)
print("7. CATEGORIAS POR TIPO DE ATENCION")
print("=" * 70)

cross = pd.crosstab(df["TIPO_ATENC"], df["CATEGORIA"], margins=True)
print(f"\n{cross.to_string()}")


# =====================================================================
# 8. PROCEDIMIENTOS SEGUN PERFIL DEL PACIENTE
# =====================================================================
print("\n" + "=" * 70)
print("8. TRATAMIENTO SEGUN PERFIL DEL PACIENTE")
print("=" * 70)

perfil = pd.read_parquet(SILVER / "FISSAL_CCR_PERFIL_PACIENTES.parquet")
pac_merged = pac_cats.merge(
    perfil[["NUM_DOC_CRYPTO", "SEXO", "EDAD_PRIMERA_ATENCION", "DEPARTAMENTO",
            "FALLECIDO", "SUPERVIVENCIA_DIAS", "RANGO_EDAD"]],
    on="NUM_DOC_CRYPTO", how="left"
)

print("\n--- Tratamiento por sexo ---")
for sexo in ["F", "M"]:
    sub = pac_merged[pac_merged["SEXO"] == sexo]
    n = len(sub)
    print(f"\n  {sexo} (n={n:,}):")
    for cat in ["CIRUGIA", "TUVO_QUIMIO", "RADIOTERAPIA", "ENDOSCOPIA", "BIOPSIA", "IMAGEN"]:
        ct = sub[cat].sum()
        print(f"    {cat:>15s}: {ct:>5,} ({ct/n*100:5.1f}%)")

print("\n--- Tratamiento por rango de edad ---")
for rango in ["0-17", "18-29", "30-39", "40-49", "50-59", "60-69", "70-79", "80+"]:
    sub = pac_merged[pac_merged["RANGO_EDAD"] == rango]
    n = len(sub)
    if n == 0:
        continue
    cir = sub["CIRUGIA"].sum()
    qt = sub["TUVO_QUIMIO"].sum()
    rt = sub["RADIOTERAPIA"].sum()
    fall = sub["FALLECIDO"].sum() if "FALLECIDO" in sub.columns else 0
    print(f"  {rango:>5s} (n={n:>5,}): CIR={cir:>4,}({cir/n*100:4.1f}%)  QT={qt:>4,}({qt/n*100:4.1f}%)  RT={rt:>3,}({rt/n*100:4.1f}%)  Fallecidos={fall:>4,}({fall/n*100:4.1f}%)")

print("\n--- Tratamiento por region (Lima vs Regiones) ---")
for region, label in [(pac_merged["DEPARTAMENTO"] == "LIMA", "LIMA"),
                      (pac_merged["DEPARTAMENTO"] != "LIMA", "REGIONES")]:
    sub = pac_merged[region]
    n = len(sub)
    if n == 0:
        continue
    print(f"\n  {label} (n={n:,}):")
    for cat in ["CIRUGIA", "TUVO_QUIMIO", "RADIOTERAPIA", "ENDOSCOPIA", "BIOPSIA", "IMAGEN"]:
        ct = sub[cat].sum()
        print(f"    {cat:>15s}: {ct:>5,} ({ct/n*100:5.1f}%)")

print("\n--- Tratamiento en fallecidos vs no fallecidos ---")
for estado, label in [(True, "FALLECIDOS"), (False, "NO FALLECIDOS")]:
    sub = pac_merged[pac_merged["FALLECIDO"] == estado]
    n = len(sub)
    if n == 0:
        continue
    print(f"\n  {label} (n={n:,}):")
    for cat in ["CIRUGIA", "TUVO_QUIMIO", "RADIOTERAPIA", "ENDOSCOPIA", "BIOPSIA", "IMAGEN", "TRANSFUSION"]:
        ct = sub[cat].sum()
        print(f"    {cat:>15s}: {ct:>5,} ({ct/n*100:5.1f}%)")


# =====================================================================
# 9. ANALISIS PROFUNDO DE MEDICAMENTOS
# =====================================================================
print("\n" + "=" * 70)
print("9. ANALISIS PROFUNDO DE MEDICAMENTOS")
print("=" * 70)

med = df[df["ATE_TIPOCONSUMO"] == "Medicamento"].copy()
print(f"\n  Registros de medicamentos: {len(med):,}")
print(f"  Pacientes con medicamentos: {med['NUM_DOC_CRYPTO'].nunique():,}")
print(f"  Medicamentos distintos (codigo): {med['ATE_CODCONSUMO'].nunique():,}")

PAT_MED = {
    "QUIMIO_CITOTOXICO": r"(?i)OXALIPLAT|FLUOROURAC|CAPECITAB|IRINOTECAN|LEUCOVORIN|FOLINATO|RALTITREX|REGORAFEN|TRIFLURID",
    "TERAPIA_DIRIGIDA": r"(?i)BEVACIZUM|CETUXIMAB|PANITUMUM|NIVOLUMAB|PEMBROLIZU|ATEZOLIZU",
    "ANTIEMETICO": r"(?i)ONDANSETRON|METOCLOPRAMID|DIMENHIDRINAT|GRANISETRON|PALONOSETRON|APREPITANT",
    "ANALGESICO_OPIOIDE": r"(?i)TRAMADOL|MORFIN|FENTANIL|OXICODON|CODEINA|PETIDINA|BUPRENORFIN",
    "ANALGESICO_NO_OPIOIDE": r"(?i)PARACETAMOL|METAMIZOL|KETOPROFEN|DICLOFENAC|IBUPROFENO|KETOROLAC|NAPROXEN|CELECOXIB",
    "PROTECTOR_GASTRICO": r"(?i)OMEPRAZOL|RANITIDINA|LANSOPRAZOL|PANTOPRAZOL|ESOMEPRAZOL|SUCRALFATO",
    "CORTICOIDE": r"(?i)DEXAMETASON|PREDNISON|METILPREDNISOL|HIDROCORTISON|BETAMETAS",
    "ANTIBIOTICO": r"(?i)METRONIDAZOL|CEFTRIAXON|CIPROFLOXACIN|CEFAZOLIN|AMIKACIN|MEROPENEM|VANCOMIC|CLINDAMIC|PIPERACIL|CEFTAZIDIM|IMIPENEM|AMPICILIN|AMOXICILIN|GENTAMIC|LEVOFLOXAC",
    "ANTICOAGULANTE": r"(?i)ENOXAPARIN|HEPARINA|WARFARIN",
    "SOLUCION_FLUIDO": r"(?i)SODIO CLORURO|DEXTROSA|AGUA PARA INYEC|LACTATO.*RINGER|POLIELECTROLIT|MANITOL",
    "SUPLEMENTO_HIERRO": r"(?i)HIERRO|SULFATO FERROSO|SACARATO.*HIERRO|FERR",
    "LAXANTE": r"(?i)LACTULOS|MACROGOL|BISACODIL|POLIETILENGL",
    "CONTRASTE": r"(?i)IOPAMIDOL|IOPROMID|IOHEXOL|IOXAGLATO|GADOLINI",
    "ANTIFUNGICO": r"(?i)FLUCONAZOL|NISTATINA|CASPOFUNGIN|ANFOTERICIN",
    "ANSIO_SEDANTE": r"(?i)MIDAZOLAM|DIAZEPAM|PROPOFOL|LORAZEPAM|ALPRAZOLAM",
    "ANTIHIPERTENSIVO": r"(?i)ENALAPRIL|LOSARTAN|AMLODIP|CAPTOPRIL|NIFEDIP|ATENOLOL|CARVEDILOL|VALSARTAN",
    "ANTIDIARREICO": r"(?i)LOPERAMID|RACECADOTRIL",
    "ERITROPOYETINA": r"(?i)ERITROPOYETIN|EPO|DARBEPOETIN",
}

med["CAT_MED"] = "OTRO_MED"
for cat, pat in reversed(list(PAT_MED.items())):
    mask = med["ATE_DESCCONSUMO"].str.contains(pat, na=False)
    med.loc[mask, "CAT_MED"] = cat

print("\n--- Registros por categoria de medicamento ---")
cat_med_stats = med.groupby("CAT_MED").agg(
    N_REG=("CAT_MED", "size"),
    N_PAC=("NUM_DOC_CRYPTO", "nunique"),
    MONTO_NETO=("ATE_MONTONETO", "sum"),
    MONTO_BRUTO=("ATE_MONTOBRUTO", "sum"),
).sort_values("N_REG", ascending=False)
for cat, row in cat_med_stats.iterrows():
    print(f"  {cat:>25s}: {row['N_REG']:>7,} reg | {row['N_PAC']:>5,} pac | S/{row['MONTO_NETO']:>12,.2f}")


# =====================================================================
# 10. ESQUEMAS DE QUIMIOTERAPIA
# =====================================================================
print("\n" + "=" * 70)
print("10. ESQUEMAS DE QUIMIOTERAPIA (APROXIMACION)")
print("=" * 70)

quimio = med[med["CAT_MED"].isin(["QUIMIO_CITOTOXICO", "TERAPIA_DIRIGIDA"])].copy()
print(f"\n  Registros quimio/terapia dirigida: {len(quimio):,}")
print(f"  Pacientes: {quimio['NUM_DOC_CRYPTO'].nunique():,}")

qt_drogas = quimio.groupby("NUM_DOC_CRYPTO")["ATE_DESCCONSUMO"].apply(
    lambda x: frozenset(
        "OXALIPLATINO" if "OXALIPLAT" in v.upper() else
        "CAPECITABINA" if "CAPECITAB" in v.upper() else
        "FLUOROURACILO" if "FLUOROURAC" in v.upper() else
        "LEUCOVORIN" if "FOLINATO" in v.upper() or "LEUCOVORIN" in v.upper() else
        "IRINOTECAN" if "IRINOTECAN" in v.upper() else
        "BEVACIZUMAB" if "BEVACIZUM" in v.upper() else
        "CETUXIMAB" if "CETUXIMAB" in v.upper() else
        v.upper()
        for v in x.dropna().unique()
    )
).reset_index()
qt_drogas.columns = ["NUM_DOC_CRYPTO", "DROGAS"]

qt_drogas["ESQUEMA"] = qt_drogas["DROGAS"].apply(lambda x: " + ".join(sorted(x)))

PAT_ESQUEMA = {
    "FOLFOX": lambda d: {"FLUOROURACILO", "LEUCOVORIN", "OXALIPLATINO"}.issubset(d),
    "CAPOX/XELOX": lambda d: {"CAPECITABINA", "OXALIPLATINO"}.issubset(d) and "FLUOROURACILO" not in d,
    "FOLFIRI": lambda d: {"FLUOROURACILO", "LEUCOVORIN", "IRINOTECAN"}.issubset(d),
    "CAPECITABINA_MONO": lambda d: d == {"CAPECITABINA"},
    "5FU/LV": lambda d: {"FLUOROURACILO", "LEUCOVORIN"}.issubset(d) and len(d) == 2,
    "5FU_MONO": lambda d: d == {"FLUOROURACILO"},
    "OXALIPLATINO_MONO": lambda d: d == {"OXALIPLATINO"},
}

qt_drogas["REGIMEN"] = "OTRO"
for nombre, fn in PAT_ESQUEMA.items():
    mask = qt_drogas["DROGAS"].apply(fn)
    qt_drogas.loc[mask, "REGIMEN"] = nombre

qt_drogas["CON_BEVACIZUMAB"] = qt_drogas["DROGAS"].apply(lambda d: "BEVACIZUMAB" in d)
qt_drogas["CON_CETUXIMAB"] = qt_drogas["DROGAS"].apply(lambda d: "CETUXIMAB" in d)

print("\n--- Regimenes de quimioterapia identificados ---")
reg_counts = qt_drogas["REGIMEN"].value_counts()
for reg, n in reg_counts.items():
    print(f"  {reg:>25s}: {n:>5,} pac ({n/len(qt_drogas)*100:5.1f}%)")

print(f"\n  Pacientes con Bevacizumab anadido: {qt_drogas['CON_BEVACIZUMAB'].sum():,}")
print(f"  Pacientes con Cetuximab anadido:   {qt_drogas['CON_CETUXIMAB'].sum():,}")

print("\n--- Top 15 combinaciones exactas de drogas ---")
esq_exact = qt_drogas["ESQUEMA"].value_counts().head(15)
for esq, n in esq_exact.items():
    print(f"  {n:>5,} pac | {esq}")


# =====================================================================
# 11. MEDICAMENTOS POR PACIENTE: VOLUMEN Y DIVERSIDAD
# =====================================================================
print("\n" + "=" * 70)
print("11. VOLUMEN DE MEDICAMENTOS POR PACIENTE")
print("=" * 70)

med_pac = med.groupby("NUM_DOC_CRYPTO").agg(
    N_REGISTROS_MED=("ATE_DESCCONSUMO", "size"),
    N_MED_DISTINTOS=("ATE_CODCONSUMO", "nunique"),
    N_CATEGORIAS_MED=("CAT_MED", "nunique"),
    MONTO_NETO_MED=("ATE_MONTONETO", "sum"),
    MONTO_BRUTO_MED=("ATE_MONTOBRUTO", "sum"),
    PRIMERA_MED=("ATE_FECATENCION", "min"),
    ULTIMA_MED=("ATE_FECATENCION", "max"),
).reset_index()
med_pac["DURACION_MED_DIAS"] = (med_pac["ULTIMA_MED"] - med_pac["PRIMERA_MED"]).dt.days

print(f"\n--- Registros de medicamentos por paciente ---")
for stat, val in med_pac["N_REGISTROS_MED"].describe().items():
    print(f"  {stat:>5s}: {val:>8,.1f}")

print(f"\n--- Medicamentos distintos por paciente ---")
for stat, val in med_pac["N_MED_DISTINTOS"].describe().items():
    print(f"  {stat:>5s}: {val:>8,.1f}")

print(f"\n--- Categorias de medicamento por paciente ---")
for stat, val in med_pac["N_CATEGORIAS_MED"].describe().items():
    print(f"  {stat:>5s}: {val:>8,.1f}")

print(f"\n--- Duracion del uso de medicamentos (dias, primera -> ultima) ---")
dur = med_pac["DURACION_MED_DIAS"].dropna()
print(f"  Media:   {dur.mean():>8.1f} dias ({dur.mean()/30:.1f} meses)")
print(f"  Mediana: {dur.median():>8.0f} dias ({dur.median()/30:.1f} meses)")
print(f"  P75:     {dur.quantile(0.75):>8.0f} dias")
print(f"  P95:     {dur.quantile(0.95):>8.0f} dias")
print(f"  Max:     {dur.max():>8.0f} dias")


# =====================================================================
# 12. COSTO DE MEDICAMENTOS POR PACIENTE
# =====================================================================
print("\n" + "=" * 70)
print("12. COSTO DE MEDICAMENTOS POR PACIENTE")
print("=" * 70)

print(f"\n--- Distribucion del costo neto total en medicamentos ---")
costo = med_pac["MONTO_NETO_MED"]
print(f"  Media:   S/{costo.mean():>10,.2f}")
print(f"  Mediana: S/{costo.median():>10,.2f}")
print(f"  P25:     S/{costo.quantile(0.25):>10,.2f}")
print(f"  P75:     S/{costo.quantile(0.75):>10,.2f}")
print(f"  P90:     S/{costo.quantile(0.90):>10,.2f}")
print(f"  P95:     S/{costo.quantile(0.95):>10,.2f}")
print(f"  Max:     S/{costo.max():>10,.2f}")

print(f"\n--- Costo por categoria de medicamento ---")
costo_cat = med.groupby("CAT_MED").agg(
    MONTO_NETO=("ATE_MONTONETO", "sum"),
    N_PAC=("NUM_DOC_CRYPTO", "nunique"),
).sort_values("MONTO_NETO", ascending=False)
costo_cat["COSTO_POR_PAC"] = costo_cat["MONTO_NETO"] / costo_cat["N_PAC"]
for cat, row in costo_cat.iterrows():
    print(f"  {cat:>25s}: S/{row['MONTO_NETO']:>12,.2f} total | {row['N_PAC']:>5,} pac | S/{row['COSTO_POR_PAC']:>8,.2f}/pac")


# =====================================================================
# 13. TOP MEDICAMENTOS POR CATEGORIA
# =====================================================================
print("\n" + "=" * 70)
print("13. TOP MEDICAMENTOS POR CATEGORIA CLINICA")
print("=" * 70)

for cat in ["QUIMIO_CITOTOXICO", "TERAPIA_DIRIGIDA", "ANTIEMETICO", "ANALGESICO_OPIOIDE",
            "ANALGESICO_NO_OPIOIDE", "PROTECTOR_GASTRICO", "CORTICOIDE", "ANTIBIOTICO",
            "ANTICOAGULANTE", "LAXANTE", "ERITROPOYETINA", "ANTIDIARREICO"]:
    sub = med[med["CAT_MED"] == cat]
    if len(sub) == 0:
        continue
    print(f"\n--- {cat} ({len(sub):,} reg | {sub['NUM_DOC_CRYPTO'].nunique():,} pac) ---")
    top = sub.groupby("ATE_DESCCONSUMO").agg(
        N_REG=("ATE_DESCCONSUMO", "size"),
        N_PAC=("NUM_DOC_CRYPTO", "nunique"),
        MONTO=("ATE_MONTONETO", "sum"),
    ).nlargest(10, "N_REG")
    for desc, row in top.iterrows():
        print(f"  {row['N_REG']:>6,} reg | {row['N_PAC']:>5,} pac | S/{row['MONTO']:>10,.2f} | {desc}")


# =====================================================================
# 14. MEDICAMENTOS SEGUN PERFIL DEL PACIENTE
# =====================================================================
print("\n" + "=" * 70)
print("14. MEDICAMENTOS SEGUN PERFIL DEL PACIENTE")
print("=" * 70)

perfil = pd.read_parquet(SILVER / "FISSAL_CCR_PERFIL_PACIENTES.parquet")
med_perfil = med_pac.merge(
    perfil[["NUM_DOC_CRYPTO", "SEXO", "RANGO_EDAD", "DEPARTAMENTO", "FALLECIDO"]],
    on="NUM_DOC_CRYPTO", how="left"
)

pac_cat_med = med.groupby("NUM_DOC_CRYPTO")["CAT_MED"].apply(set).reset_index()
pac_cat_med.columns = ["NUM_DOC_CRYPTO", "CATS_MED"]
for cat in ["QUIMIO_CITOTOXICO", "TERAPIA_DIRIGIDA", "ANALGESICO_OPIOIDE",
            "ANTIEMETICO", "ANTIBIOTICO", "CORTICOIDE", "ERITROPOYETINA"]:
    pac_cat_med[cat] = pac_cat_med["CATS_MED"].apply(lambda x: cat in x)
med_perfil = med_perfil.merge(pac_cat_med.drop(columns="CATS_MED"), on="NUM_DOC_CRYPTO", how="left")

print("\n--- Medicamentos por sexo ---")
for sexo in ["F", "M"]:
    sub = med_perfil[med_perfil["SEXO"] == sexo]
    n = len(sub)
    print(f"\n  {sexo} (n={n:,}):")
    print(f"    Medicamentos distintos (media): {sub['N_MED_DISTINTOS'].mean():.1f}")
    print(f"    Costo neto medio: S/{sub['MONTO_NETO_MED'].mean():,.2f}")
    for cat in ["QUIMIO_CITOTOXICO", "TERAPIA_DIRIGIDA", "ANALGESICO_OPIOIDE", "ANTIEMETICO", "ANTIBIOTICO"]:
        ct = sub[cat].sum()
        print(f"    {cat:>25s}: {ct:>5,} ({ct/n*100:5.1f}%)")

print("\n--- Medicamentos por rango de edad ---")
for rango in ["0-17", "18-29", "30-39", "40-49", "50-59", "60-69", "70-79", "80+"]:
    sub = med_perfil[med_perfil["RANGO_EDAD"] == rango]
    n = len(sub)
    if n == 0:
        continue
    qt = sub["QUIMIO_CITOTOXICO"].sum()
    td = sub["TERAPIA_DIRIGIDA"].sum()
    op = sub["ANALGESICO_OPIOIDE"].sum()
    ab = sub["ANTIBIOTICO"].sum()
    print(f"  {rango:>5s} (n={n:>5,}): QT={qt:>4,}({qt/n*100:4.1f}%) TD={td:>3,}({td/n*100:4.1f}%) Opioide={op:>4,}({op/n*100:4.1f}%) ATB={ab:>4,}({ab/n*100:4.1f}%)")

print("\n--- Medicamentos en fallecidos vs no fallecidos ---")
for estado, label in [(True, "FALLECIDOS"), (False, "NO FALLECIDOS")]:
    sub = med_perfil[med_perfil["FALLECIDO"] == estado]
    n = len(sub)
    if n == 0:
        continue
    print(f"\n  {label} (n={n:,}):")
    print(f"    Medicamentos distintos (media): {sub['N_MED_DISTINTOS'].mean():.1f}")
    print(f"    Costo neto medio: S/{sub['MONTO_NETO_MED'].mean():,.2f}")
    print(f"    Duracion media: {sub['DURACION_MED_DIAS'].mean():.0f} dias")
    for cat in ["QUIMIO_CITOTOXICO", "TERAPIA_DIRIGIDA", "ANALGESICO_OPIOIDE",
                "ANTIEMETICO", "ANTIBIOTICO", "CORTICOIDE", "ERITROPOYETINA"]:
        ct = sub[cat].sum()
        print(f"    {cat:>25s}: {ct:>5,} ({ct/n*100:5.1f}%)")


# =====================================================================
# 15. CRONOLOGIA DE MEDICAMENTOS
# =====================================================================
print("\n" + "=" * 70)
print("15. CRONOLOGIA: CUANDO SE INTRODUCEN LOS MEDICAMENTOS")
print("=" * 70)

primera_atencion = df.groupby("NUM_DOC_CRYPTO")["ATE_FECATENCION"].min().rename("PRIMERA_ATENCION")

for cat in ["QUIMIO_CITOTOXICO", "TERAPIA_DIRIGIDA", "ANALGESICO_OPIOIDE",
            "ANTIEMETICO", "PROTECTOR_GASTRICO", "CORTICOIDE", "ANTIBIOTICO",
            "LAXANTE", "ERITROPOYETINA"]:
    sub = med[med["CAT_MED"] == cat]
    if len(sub) == 0:
        continue
    primera_med = sub.groupby("NUM_DOC_CRYPTO")["ATE_FECATENCION"].min().rename("PRIMERA_MED_CAT")
    merged = pd.merge(primera_med, primera_atencion, left_index=True, right_index=True)
    dias = (merged["PRIMERA_MED_CAT"] - merged["PRIMERA_ATENCION"]).dt.days
    dias_pos = dias[dias >= 0]
    if len(dias_pos) == 0:
        continue
    print(f"\n  {cat} (n={len(dias_pos):,} pac):")
    print(f"    Dias desde 1ra atencion -> 1er {cat}:")
    print(f"    Media:   {dias_pos.mean():>7.0f} dias ({dias_pos.mean()/30:.1f} meses)")
    print(f"    Mediana: {dias_pos.median():>7.0f} dias ({dias_pos.median()/30:.1f} meses)")
    print(f"    P25:     {dias_pos.quantile(0.25):>7.0f}")
    print(f"    P75:     {dias_pos.quantile(0.75):>7.0f}")


# =====================================================================
# 16. CICLOS DE QUIMIOTERAPIA
# =====================================================================
print("\n" + "=" * 70)
print("16. CICLOS DE QUIMIOTERAPIA POR PACIENTE")
print("=" * 70)

qt_registros = med[med["CAT_MED"] == "QUIMIO_CITOTOXICO"].copy()
if len(qt_registros) > 0:
    qt_sesiones = qt_registros.groupby(["NUM_DOC_CRYPTO", "ATE_FECATENCION"]).size().reset_index(name="N_DROGAS")
    ciclos_pac = qt_sesiones.groupby("NUM_DOC_CRYPTO").agg(
        N_SESIONES=("ATE_FECATENCION", "nunique"),
        PRIMERA_SESION=("ATE_FECATENCION", "min"),
        ULTIMA_SESION=("ATE_FECATENCION", "max"),
    ).reset_index()
    ciclos_pac["DURACION_QT_DIAS"] = (ciclos_pac["ULTIMA_SESION"] - ciclos_pac["PRIMERA_SESION"]).dt.days

    print(f"\n  Pacientes con quimioterapia citotoxica: {len(ciclos_pac):,}")

    print(f"\n--- Sesiones de quimioterapia por paciente ---")
    for stat, val in ciclos_pac["N_SESIONES"].describe().items():
        print(f"  {stat:>5s}: {val:>8,.1f}")

    print(f"\n--- Duracion total del tratamiento quimioterapico ---")
    dur_qt = ciclos_pac["DURACION_QT_DIAS"]
    print(f"  Media:   {dur_qt.mean():>7.0f} dias ({dur_qt.mean()/30:.1f} meses)")
    print(f"  Mediana: {dur_qt.median():>7.0f} dias ({dur_qt.median()/30:.1f} meses)")
    print(f"  P25:     {dur_qt.quantile(0.25):>7.0f} dias")
    print(f"  P75:     {dur_qt.quantile(0.75):>7.0f} dias")
    print(f"  P95:     {dur_qt.quantile(0.95):>7.0f} dias")

    print(f"\n--- Distribucion de sesiones ---")
    bins_ses = [0, 1, 3, 6, 12, 24, 50, 999]
    labels_ses = ["1", "2-3", "4-6", "7-12", "13-24", "25-50", "50+"]
    ciclos_pac["RANGO_SESIONES"] = pd.cut(ciclos_pac["N_SESIONES"], bins=bins_ses, labels=labels_ses, right=True)
    for r, n in ciclos_pac["RANGO_SESIONES"].value_counts().sort_index().items():
        print(f"    {r:>6s} sesiones: {n:>5,} pac ({n/len(ciclos_pac)*100:5.1f}%)")

    # ciclos_pac.to_parquet(SILVER / "FISSAL_CCR_CICLOS_QUIMIO.parquet", index=False)


# =====================================================================
# GUARDAR
# =====================================================================
# hitos.to_parquet(SILVER / "FISSAL_CCR_HITOS_TRATAMIENTO.parquet", index=False)

pac_resumen = pac_cats.merge(proc_pac, on="NUM_DOC_CRYPTO")
# pac_resumen.to_parquet(SILVER / "FISSAL_CCR_PROCEDIMIENTOS_POR_PACIENTE.parquet", index=False)

# med_pac.to_parquet(SILVER / "FISSAL_CCR_MEDICAMENTOS_POR_PACIENTE.parquet", index=False)
qt_drogas_out = qt_drogas.copy()
qt_drogas_out["DROGAS"] = qt_drogas_out["DROGAS"].apply(lambda x: "|".join(sorted(x)))
# qt_drogas_out.to_parquet(SILVER / "FISSAL_CCR_ESQUEMAS_QUIMIO.parquet", index=False)

print(f"\n{'=' * 70}")
print("Archivos generados:")
print(f"  {SILVER / 'FISSAL_CCR_HITOS_TRATAMIENTO.parquet'}")
print(f"  {SILVER / 'FISSAL_CCR_PROCEDIMIENTOS_POR_PACIENTE.parquet'}")
print(f"  {SILVER / 'FISSAL_CCR_MEDICAMENTOS_POR_PACIENTE.parquet'}")
print(f"  {SILVER / 'FISSAL_CCR_ESQUEMAS_QUIMIO.parquet'}")
print(f"  {SILVER / 'FISSAL_CCR_CICLOS_QUIMIO.parquet'}")
print("Fin.")
