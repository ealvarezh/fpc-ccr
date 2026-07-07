import sys
import pandas as pd
import numpy as np
import gc
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
pd.set_option('display.max_columns', None)

SILVER = Path(r"C:\Users\eah\apoyoconsultoria.com\File Server - Analytics\7 Datos\Datos abiertos\fissal\01_silver")
ARCHIVO_CCR = SILVER / "FISSAL_CANCER_COLORRECTAL_2016_2022.parquet"
ARCHIVO_PERFIL = SILVER / "FISSAL_CCR_PERFIL_PACIENTES_AMPLIADO.parquet"

FECHA_CORTE = pd.Timestamp("2022-12-31")
ANIOS = range(2016, 2023)

# Umbral para considerar que un paciente "salio del sistema" sin fallecer ni
# recibir cuidados paliativos: dias desde su ultima atencion hasta la fecha de
# corte. Es una SUPOSICION explicita (no un hecho confirmado por FISSAL):
# puede ser alta/remision, cambio de aseguradora, migracion o perdida de
# seguimiento administrativo. 540 dias =~ 18 meses.
UMBRAL_SIN_SEGUIMIENTO_DIAS = 540

# Brecha entre atenciones consecutivas DURANTE el tramo de tratamiento activo
# que se interpreta como posible inasistencia / abandono temporal. Se elige
# 45 dias porque los esquemas de quimioterapia tipicos (FOLFOX/FOLFIRI/CAPOX)
# ciclan cada 14-21 dias; un vacio >45d duplica el ciclo mas largo esperado.
UMBRAL_BRECHA_ADHERENCIA_DIAS = 45

print("=" * 70)
print("CONSTRUCCION DE HITOS DEL PACIENTE — CANCER COLORRECTAL")
print("FISSAL 2016-2022")
print("=" * 70)
print("""
Hitos definidos:
  1. DESPISTAJE/DETECCION  — procedimientos de sospecha ANTES del diagnostico
  2. DIAGNOSTICO           — primera atencion codificada como CCR (C18/19/20)
  3. TRATAMIENTO           — episodios de cirugia, quimioterapia, radioterapia
  4. DESENLACE             — fallecido / paliativo / posible remision-alta / activo
""")

df = pd.read_parquet(ARCHIVO_CCR)
perfil = pd.read_parquet(ARCHIVO_PERFIL)
print(f"Registros CCR: {len(df):,} | Pacientes: {perfil.shape[0]:,}")

pac_ccr = set(perfil["NUM_DOC_CRYPTO"])
primera_atencion = perfil.set_index("NUM_DOC_CRYPTO")["PRIMERA_ATENCION"]


# =====================================================================
# HITO 1: DESPISTAJE / DETECCION (antes del diagnostico CCR)
# =====================================================================
# El filtro C18/19/20 solo captura registros YA codificados como cancer
# colorrectal. Para ver el camino de sospecha/deteccion que llevo al
# diagnostico (biopsias, endoscopias, imagenes) hay que buscar en la data
# COMPLETA de FISSAL (todos los CIE10), en fechas ANTERIORES a la primera
# atencion CCR de cada paciente.
print("\n" + "=" * 70)
print("HITO 1: DESPISTAJE / DETECCION (buscando en data completa pre-diagnostico)")
print("=" * 70)

PAT_DESPISTAJE = {
    "BIOPSIA": r"(?i)BIOPSI|ANATOMOPATOLOG",
    "ENDOSCOPIA": r"(?i)COLONOSCOP|ENDOSCOP|RECTOSCOP|SIGMOIDOSCOP",
    "IMAGEN": r"(?i)TOMOGRAF|RESONAN|ECOGRAF|GAMMAGRAF|PET.?SCAN|RADIOGRAF",
    "LABORATORIO_MARCADOR": r"(?i)\bCEA\b|ANTIGEN.*CARCINO|SANGRE.*OCULTA",
}
COLS_YR = ["NUM_DOC_CRYPTO", "ATE_FECATENCION", "ATE_DESCCONSUMO", "ATE_TIPOCONSUMO",
           "ATE_CODCIE10", "ATE_DESCCIE10", "ATE_MONTONETO", "ATE_MONTOBRUTO",
           "TIPO_ATENC", "ATE_NOMIPRESS", "ATE_FUA"]

primer_contacto = {}
agg_pre_dx_list = []
eventos_despistaje_list = []

for yr in ANIOS:
    archivo = SILVER / f"FISSAL_PRESTACIONES_{yr}.parquet"
    if not archivo.exists():
        continue
    print(f"  Procesando {yr}...", end=" ")
    df_yr = pd.read_parquet(archivo, columns=COLS_YR)
    df_yr = df_yr[df_yr["NUM_DOC_CRYPTO"].isin(pac_ccr)].copy()
    df_yr["FECHA_DX"] = df_yr["NUM_DOC_CRYPTO"].map(primera_atencion)

    # Primer contacto del paciente con FISSAL (cualquier diagnostico)
    contacto_yr = df_yr.groupby("NUM_DOC_CRYPTO")["ATE_FECATENCION"].min()
    for pid, fecha in contacto_yr.items():
        if pid not in primer_contacto or fecha < primer_contacto[pid]:
            primer_contacto[pid] = fecha

    # Registros ANTERIORES al diagnostico CCR de ese paciente
    df_pre = df_yr[df_yr["ATE_FECATENCION"] < df_yr["FECHA_DX"]]
    n_pre = len(df_pre)

    if n_pre > 0:
        agg_yr = df_pre.groupby("NUM_DOC_CRYPTO").agg(
            N_FUA_PRE=("ATE_FUA", "nunique"),
            N_REG_PRE=("ATE_FECATENCION", "size"),
            COSTO_NETO_PRE=("ATE_MONTONETO", "sum"),
            COSTO_BRUTO_PRE=("ATE_MONTOBRUTO", "sum"),
        ).reset_index()
        agg_pre_dx_list.append(agg_yr)

        for cat, pat in PAT_DESPISTAJE.items():
            mask = df_pre["ATE_DESCCONSUMO"].str.contains(pat, na=False)
            if mask.any():
                sub = df_pre.loc[mask, ["NUM_DOC_CRYPTO", "ATE_FECATENCION", "ATE_DESCCONSUMO",
                                         "ATE_DESCCIE10", "ATE_NOMIPRESS"]].copy()
                sub["TIPO_DESPISTAJE"] = cat
                eventos_despistaje_list.append(sub)

    print(f"{n_pre:,} registros pre-diagnostico")
    del df_yr, df_pre
    gc.collect()

# --- Agregado de actividad pre-diagnostico (todos los registros, no solo despistaje) ---
if agg_pre_dx_list:
    agg_pre_dx = pd.concat(agg_pre_dx_list, ignore_index=True).groupby("NUM_DOC_CRYPTO").agg(
        N_FUA_PRE_DIAGNOSTICO=("N_FUA_PRE", "sum"),
        N_REGISTROS_PRE_DIAGNOSTICO=("N_REG_PRE", "sum"),
        COSTO_NETO_PRE_DIAGNOSTICO=("COSTO_NETO_PRE", "sum"),
        COSTO_BRUTO_PRE_DIAGNOSTICO=("COSTO_BRUTO_PRE", "sum"),
    ).reset_index()
else:
    agg_pre_dx = pd.DataFrame(columns=["NUM_DOC_CRYPTO", "N_FUA_PRE_DIAGNOSTICO",
                                        "N_REGISTROS_PRE_DIAGNOSTICO", "COSTO_NETO_PRE_DIAGNOSTICO",
                                        "COSTO_BRUTO_PRE_DIAGNOSTICO"])

# --- Primer evento de despistaje detectado, por paciente ---
if eventos_despistaje_list:
    eventos_despistaje = pd.concat(eventos_despistaje_list, ignore_index=True)
    primer_desp = (
        eventos_despistaje.sort_values("ATE_FECATENCION")
        .groupby("NUM_DOC_CRYPTO")
        .first()[["ATE_FECATENCION", "TIPO_DESPISTAJE", "ATE_DESCCIE10", "ATE_NOMIPRESS"]]
        .rename(columns={
            "ATE_FECATENCION": "FECHA_PRIMER_DESPISTAJE",
            "ATE_DESCCIE10": "DX_EN_DESPISTAJE",
            "ATE_NOMIPRESS": "IPRESS_DESPISTAJE",
        })
        .reset_index()
    )
else:
    eventos_despistaje = pd.DataFrame()
    primer_desp = pd.DataFrame(columns=["NUM_DOC_CRYPTO", "FECHA_PRIMER_DESPISTAJE",
                                         "TIPO_DESPISTAJE", "DX_EN_DESPISTAJE", "IPRESS_DESPISTAJE"])

hito1 = pd.DataFrame({"NUM_DOC_CRYPTO": list(pac_ccr)})
hito1["FECHA_DIAGNOSTICO"] = hito1["NUM_DOC_CRYPTO"].map(primera_atencion)
hito1["FECHA_PRIMER_CONTACTO_SISTEMA"] = hito1["NUM_DOC_CRYPTO"].map(primer_contacto)
hito1 = hito1.merge(agg_pre_dx, on="NUM_DOC_CRYPTO", how="left")
hito1 = hito1.merge(primer_desp, on="NUM_DOC_CRYPTO", how="left")

for c in ["N_FUA_PRE_DIAGNOSTICO", "N_REGISTROS_PRE_DIAGNOSTICO",
          "COSTO_NETO_PRE_DIAGNOSTICO", "COSTO_BRUTO_PRE_DIAGNOSTICO"]:
    hito1[c] = hito1[c].fillna(0)

hito1["TUVO_DESPISTAJE_PREVIO"] = hito1["FECHA_PRIMER_DESPISTAJE"].notna()
hito1["DIAS_DESPISTAJE_A_DIAGNOSTICO"] = (
    hito1["FECHA_DIAGNOSTICO"] - hito1["FECHA_PRIMER_DESPISTAJE"]
).dt.days
hito1["DIAS_PRIMER_CONTACTO_A_DIAGNOSTICO"] = (
    hito1["FECHA_DIAGNOSTICO"] - hito1["FECHA_PRIMER_CONTACTO_SISTEMA"]
).dt.days
# Diagnostico "de entrada" = el primer contacto del paciente en FISSAL YA es
# el diagnostico CCR (no hubo trayecto previo visible en el sistema)
hito1["DIAGNOSTICO_ES_PRIMER_CONTACTO"] = (
    hito1["DIAS_PRIMER_CONTACTO_A_DIAGNOSTICO"].fillna(0) == 0
)

print(f"\n  Pacientes con despistaje previo detectado: {hito1['TUVO_DESPISTAJE_PREVIO'].sum():,} "
      f"({hito1['TUVO_DESPISTAJE_PREVIO'].mean()*100:.1f}%)")
print(f"  Pacientes cuyo primer contacto en FISSAL YA es el diagnostico CCR: "
      f"{hito1['DIAGNOSTICO_ES_PRIMER_CONTACTO'].sum():,} "
      f"({hito1['DIAGNOSTICO_ES_PRIMER_CONTACTO'].mean()*100:.1f}%)")


# =====================================================================
# HITO 2: DIAGNOSTICO (primera atencion codificada C18/19/20)
# =====================================================================
print("\n" + "=" * 70)
print("HITO 2: DIAGNOSTICO")
print("=" * 70)

primeros_reg = (
    df.sort_values("ATE_FECATENCION")
    .groupby("NUM_DOC_CRYPTO")
    .first()[["ATE_NOMIPRESS", "TIPO_ATENC", "ATE_CODCIE10", "ATE_DESCCIE10",
              "ATE_GRUPOCIE10", "DEPARTAMENTO_PAC"]]
    .rename(columns={
        "ATE_NOMIPRESS": "IPRESS_DIAGNOSTICO",
        "TIPO_ATENC": "TIPO_ATENCION_DIAGNOSTICO",
        "ATE_CODCIE10": "CIE10_DIAGNOSTICO",
        "ATE_DESCCIE10": "DESC_CIE10_DIAGNOSTICO",
        "ATE_GRUPOCIE10": "GRUPO_CIE10_DIAGNOSTICO",
        "DEPARTAMENTO_PAC": "DEPARTAMENTO_DIAGNOSTICO",
    })
    .reset_index()
)
hito2 = primeros_reg
print(f"  Pacientes con hito de diagnostico: {len(hito2):,}")
print("\n  Tipo de atencion en el momento del diagnostico:")
for tipo, n in hito2["TIPO_ATENCION_DIAGNOSTICO"].value_counts().items():
    print(f"    {tipo:>20s}: {n:>6,} ({n/len(hito2)*100:5.1f}%)")


# =====================================================================
# HITO 3: TRATAMIENTO (cirugia, quimioterapia, radioterapia)
# =====================================================================
print("\n" + "=" * 70)
print("HITO 3: TRATAMIENTO")
print("=" * 70)

PAT_TRAT = {
    "CIRUGIA": r"(?i)COLECTOM|RESECC|HEMICOLEC|COLOSTOM|LAPAROTOM|ANASTOMOS|LAPAROSCOP",
    "QUIMIOTERAPIA": r"(?i)QUIMIOTER|INFUSION.*QUIMIO|ADMINISTRACION.*QUIMIO|OXALIPLAT|FLUOROURAC|CAPECITAB|IRINOTECAN|LEUCOVORIN|BEVACIZUM|CETUXIMAB|PANITUMUM|RALTITREX|REGORAFEN|TRIFLURID",
    "RADIOTERAPIA": r"(?i)RADIOTER|COBALTOT|BRAQUIT|ACELERADOR",
}

df["CATEGORIA_TRAT"] = "OTRO"
for cat, pat in PAT_TRAT.items():
    mask = df["ATE_DESCCONSUMO"].str.contains(pat, na=False)
    df.loc[mask, "CATEGORIA_TRAT"] = cat

# --- Complemento: deteccion de tratamiento vía el diccionario categoria_recurso_502 ---
# El regex de arriba solo mira texto libre y deja ~68% de los pacientes en
# SIN_TRATAMIENTO_DETECTADO (ver README). El diccionario
# `diccionario_ATE_DESCCONSUMO_502_estandarizado.xlsx` (hoja Diccionario_502) da una
# clasificacion mas confiable de cada ATE_DESCCONSUMO, y detecta casos que el regex
# no captura (p.ej. marcas comerciales de quimioterapicos no listadas, o procedimientos
# de radioterapia sin la palabra "RADIOTER" en la descripcion). Se usa como señal
# ADICIONAL (OR con el regex, nunca lo reemplaza): si el regex ya clasifico la fila, se
# respeta; si no, se usa la señal del diccionario.
DICCIONARIO_502 = Path(
    r"C:\Users\eah\apoyoconsultoria.com\File Server - Analytics\3 Proyectos\2025"
    r"\2025-116-L FPC Dashboard 25\4 Analisis\3 Programas\adicional 2026"
    r"\diccionario_ATE_DESCCONSUMO_502_estandarizado.xlsx"
)
dic = pd.read_excel(DICCIONARIO_502, sheet_name="Diccionario_502",
                     usecols=["ATE_DESCCONSUMO", "categoria_recurso_502", "subcategoria_recurso_502"])
dic["ATE_DESCCONSUMO"] = dic["ATE_DESCCONSUMO"].str.strip()
dic = dic.drop_duplicates(subset="ATE_DESCCONSUMO")

df["_DESC_STRIP"] = df["ATE_DESCCONSUMO"].str.strip()
df = df.merge(dic, left_on="_DESC_STRIP", right_on="ATE_DESCCONSUMO", how="left", suffixes=("", "_DIC"))
df = df.drop(columns=["_DESC_STRIP", "ATE_DESCCONSUMO_DIC"])

# Reglas por subcategoria (mas fina que la categoria general, evita mezclar
# quimio/radio con otros insumos/medicamentos de la misma categoria amplia):
#  - Antineoplasico/terapia oncologica sistemica  -> QUIMIOTERAPIA (el farmaco en si)
#  - Administracion de quimioterapia              -> QUIMIOTERAPIA (el procedimiento de infusion)
#  - Radioterapia (categoria completa)            -> RADIOTERAPIA (bloque chico, no ambiguo)
#  - Cirugia colorrectal / Cirugia digestiva       -> CIRUGIA (se excluyen deliberadamente
#    Cirugia urologica/toracica/gineco-obstetrica y la generica "Cirugia u otra intervencion
#    quirurgica" para no arrastrar comorbilidades no relacionadas a CRC)
SUBCAT_A_TRAT = {
    "Antineoplásico / terapia oncológica sistémica": "QUIMIOTERAPIA",
    "Administración de quimioterapia": "QUIMIOTERAPIA",
    "Cirugía colorrectal": "CIRUGIA",
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
print(f"  [Diccionario 502] {n_reclasificado_dic:,} registro(s) reclasificados de OTRO a "
      f"CIRUGIA/QUIMIOTERAPIA/RADIOTERAPIA que el regex de texto no habia detectado.")

modalidades = []
for cat in PAT_TRAT:
    sub = df[df["CATEGORIA_TRAT"] == cat]
    ep = sub.groupby("NUM_DOC_CRYPTO").agg(**{
        f"N_SESIONES_{cat}": ("ATE_FECATENCION", "nunique"),
        f"FECHA_INICIO_{cat}": ("ATE_FECATENCION", "min"),
        f"FECHA_FIN_{cat}": ("ATE_FECATENCION", "max"),
        f"COSTO_NETO_{cat}": ("ATE_MONTONETO", "sum"),
        f"COSTO_BRUTO_{cat}": ("ATE_MONTOBRUTO", "sum"),
    }).reset_index()
    ep[f"DURACION_{cat}_DIAS"] = (ep[f"FECHA_FIN_{cat}"] - ep[f"FECHA_INICIO_{cat}"]).dt.days
    modalidades.append(ep)

hito3 = modalidades[0]
for m in modalidades[1:]:
    hito3 = hito3.merge(m, on="NUM_DOC_CRYPTO", how="outer")

fecha_inicio_cols = [f"FECHA_INICIO_{c}" for c in PAT_TRAT]
hito3["FECHA_INICIO_TRATAMIENTO"] = hito3[fecha_inicio_cols].min(axis=1)
hito3["FECHA_FIN_TRATAMIENTO"] = hito3[[f"FECHA_FIN_{c}" for c in PAT_TRAT]].max(axis=1)

# Secuencia: orden cronologico de las modalidades que recibio cada paciente
def secuencia(row):
    pares = [(row[f"FECHA_INICIO_{c}"], c) for c in PAT_TRAT if pd.notna(row[f"FECHA_INICIO_{c}"])]
    pares.sort(key=lambda x: x[0])
    return " > ".join(c for _, c in pares) if pares else "SIN_TRATAMIENTO_DETECTADO"

hito3["SECUENCIA_TRATAMIENTO"] = hito3.apply(secuencia, axis=1)

# IMPORTANTE: el right-merge de abajo agrega pacientes sin NINGUNA modalidad
# de tratamiento (filas nuevas, todo NaN). El fillna/TUVO_ debe calcularse
# DESPUES de ese merge para que tambien cubra a esos pacientes.
hito3 = hito3.merge(hito2[["NUM_DOC_CRYPTO"]], on="NUM_DOC_CRYPTO", how="right")
hito3["SECUENCIA_TRATAMIENTO"] = hito3["SECUENCIA_TRATAMIENTO"].fillna("SIN_TRATAMIENTO_DETECTADO")

for c in PAT_TRAT:
    hito3[f"N_SESIONES_{c}"] = hito3[f"N_SESIONES_{c}"].fillna(0)
    hito3[f"COSTO_NETO_{c}"] = hito3[f"COSTO_NETO_{c}"].fillna(0)
    hito3[f"COSTO_BRUTO_{c}"] = hito3[f"COSTO_BRUTO_{c}"].fillna(0)
    hito3[f"TUVO_{c}"] = hito3[f"N_SESIONES_{c}"] > 0

hito3 = hito3.merge(hito1[["NUM_DOC_CRYPTO", "FECHA_DIAGNOSTICO"]], on="NUM_DOC_CRYPTO", how="left")
hito3["DIAS_DIAGNOSTICO_A_TRATAMIENTO"] = (
    hito3["FECHA_INICIO_TRATAMIENTO"] - hito3["FECHA_DIAGNOSTICO"]
).dt.days

print(f"\n  Pacientes por modalidad de tratamiento:")
for c in PAT_TRAT:
    n = hito3[f"TUVO_{c}"].sum()
    print(f"    {c:>15s}: {n:>6,} ({n/len(hito3)*100:5.1f}%)")

tt_pos = hito3["DIAS_DIAGNOSTICO_A_TRATAMIENTO"].dropna()
tt_pos = tt_pos[tt_pos >= 0]
if len(tt_pos) > 0:
    print(f"\n  Tiempo diagnostico -> inicio de tratamiento (dias), n={len(tt_pos):,}:")
    print(f"    Media:   {tt_pos.mean():.1f}   Mediana: {tt_pos.median():.0f}   "
          f"P25: {tt_pos.quantile(.25):.0f}   P75: {tt_pos.quantile(.75):.0f}   P95: {tt_pos.quantile(.95):.0f}")

# --- Hospitalizaciones dentro del tramo de tratamiento ---
hosp = df[df["TIPO_ATENC"].str.contains("HOSP", case=False, na=False)]
hosp_ep = (
    hosp.groupby(["NUM_DOC_CRYPTO", "ATE_FUA"])
    .agg(FECHA_ING=("ATE_FECINGHOSP", "min"), FECHA_ALT=("ATE_FECALTHOSP", "max"))
    .reset_index()
)
mask_f = hosp_ep["FECHA_ING"].notna() & hosp_ep["FECHA_ALT"].notna()
hosp_ep.loc[mask_f, "DIAS_ESTANCIA"] = (hosp_ep.loc[mask_f, "FECHA_ALT"] - hosp_ep.loc[mask_f, "FECHA_ING"]).dt.days
hosp_pac = hosp_ep.groupby("NUM_DOC_CRYPTO").agg(
    N_HOSPITALIZACIONES=("ATE_FUA", "nunique"),
    DIAS_HOSPITALIZACION_TOTAL=("DIAS_ESTANCIA", "sum"),
).reset_index()
hito3 = hito3.merge(hosp_pac, on="NUM_DOC_CRYPTO", how="left")
hito3["N_HOSPITALIZACIONES"] = hito3["N_HOSPITALIZACIONES"].fillna(0)
hito3["DIAS_HOSPITALIZACION_TOTAL"] = hito3["DIAS_HOSPITALIZACION_TOTAL"].fillna(0)

# --- Adherencia: brechas largas entre atenciones durante el tratamiento activo ---
print("\n  Calculando brechas de adherencia durante el tratamiento activo...")
en_trat = df.merge(hito3[["NUM_DOC_CRYPTO", "FECHA_INICIO_TRATAMIENTO", "FECHA_FIN_TRATAMIENTO"]],
                    on="NUM_DOC_CRYPTO", how="left")
en_trat = en_trat[
    en_trat["FECHA_INICIO_TRATAMIENTO"].notna()
    & (en_trat["ATE_FECATENCION"] >= en_trat["FECHA_INICIO_TRATAMIENTO"])
    & (en_trat["ATE_FECATENCION"] <= en_trat["FECHA_FIN_TRATAMIENTO"])
]

brechas_rows = []
for pid, fechas in en_trat.groupby("NUM_DOC_CRYPTO")["ATE_FECATENCION"]:
    fechas = sorted(fechas.dropna().unique())
    if len(fechas) < 2:
        continue
    gaps = [(fechas[i] - fechas[i - 1]) / np.timedelta64(1, "D") for i in range(1, len(fechas))]
    n_brechas = sum(1 for g in gaps if g > UMBRAL_BRECHA_ADHERENCIA_DIAS)
    if n_brechas > 0 or len(gaps) > 0:
        brechas_rows.append({
            "NUM_DOC_CRYPTO": pid,
            "N_BRECHAS_TRATAMIENTO": n_brechas,
            "BRECHA_MAX_DIAS": max(gaps),
        })
brechas_df = pd.DataFrame(brechas_rows) if brechas_rows else pd.DataFrame(
    columns=["NUM_DOC_CRYPTO", "N_BRECHAS_TRATAMIENTO", "BRECHA_MAX_DIAS"])
hito3 = hito3.merge(brechas_df, on="NUM_DOC_CRYPTO", how="left")
hito3["N_BRECHAS_TRATAMIENTO"] = hito3["N_BRECHAS_TRATAMIENTO"].fillna(0)
hito3["TUVO_BRECHA_ADHERENCIA"] = hito3["N_BRECHAS_TRATAMIENTO"] > 0

print(f"  Pacientes con al menos una brecha > {UMBRAL_BRECHA_ADHERENCIA_DIAS}d durante tratamiento: "
      f"{hito3['TUVO_BRECHA_ADHERENCIA'].sum():,} ({hito3['TUVO_BRECHA_ADHERENCIA'].mean()*100:.1f}%)")

# --- Costo total del tramo de tratamiento (todo lo facturado entre inicio y fin) ---
costo_trat = en_trat.groupby("NUM_DOC_CRYPTO").agg(
    COSTO_NETO_TRATAMIENTO_TOTAL=("ATE_MONTONETO", "sum"),
    COSTO_BRUTO_TRATAMIENTO_TOTAL=("ATE_MONTOBRUTO", "sum"),
).reset_index()
hito3 = hito3.merge(costo_trat, on="NUM_DOC_CRYPTO", how="left")
hito3["COSTO_NETO_TRATAMIENTO_TOTAL"] = hito3["COSTO_NETO_TRATAMIENTO_TOTAL"].fillna(0)
hito3["COSTO_BRUTO_TRATAMIENTO_TOTAL"] = hito3["COSTO_BRUTO_TRATAMIENTO_TOTAL"].fillna(0)

del en_trat
gc.collect()


# =====================================================================
# HITO 4: DESENLACE
# =====================================================================
print("\n" + "=" * 70)
print("HITO 4: DESENLACE")
print("=" * 70)
print(f"""
  NOTA IMPORTANTE: FISSAL no registra si un paciente se "recupero". Solo se
  sabe si fallecio o si recibio cuidados paliativos (proxy de enfermedad
  avanzada). Para el resto se distingue entre:
   - RECAIDA_PROBABLE: el paciente tuvo una pausa >= {UMBRAL_SIN_SEGUIMIENTO_DIAS}d
     ({UMBRAL_SIN_SEGUIMIENTO_DIAS/30:.0f} meses) sin atenciones y LUEGO volvio a aparecer
     en FISSAL con cirugia/quimio/radio/hospitalizacion — la pausa no era el
     final de su historia, sino un posible periodo de remision seguido de recaida.
   - POSIBLE_REMISION_O_ALTA: la pausa >= {UMBRAL_SIN_SEGUIMIENTO_DIAS}d es lo ULTIMO que se ve
     de el en FISSAL antes del corte ({FECHA_CORTE.date()}) — nunca volvio. Sigue
     siendo un SUPUESTO (tambien puede ser cambio de aseguradora, migracion o
     perdida de seguimiento), no una confirmacion clinica de recuperacion.
""")

# --- Deteccion de brechas largas SEGUIDAS de un retorno (posible recaida) ---
# A diferencia de la adherencia del Hito 3 (que solo mira brechas DENTRO del
# tramo de tratamiento), aqui se revisa TODA la historia de atenciones CCR del
# paciente para detectar si alguna vez hubo una brecha larga que luego se
# "rompio" con un regreso. Se distingue el tipo de regreso:
#   ACTIVO  -> el regreso incluye cirugia/quimio/radio/hospitalizacion (recaida probable)
#   CONTROL -> el regreso es solo consulta/laboratorio/imagen (posible chequeo de rutina)
VENTANA_RETORNO_DIAS = 60

df["ES_TRATAMIENTO_ACTIVO"] = (
    df["CATEGORIA_TRAT"].isin(["CIRUGIA", "QUIMIOTERAPIA", "RADIOTERAPIA"])
    | df["TIPO_ATENC"].str.contains("HOSP", case=False, na=False)
)
fechas_actividad = (
    df.groupby(["NUM_DOC_CRYPTO", "ATE_FECATENCION"])["ES_TRATAMIENTO_ACTIVO"]
    .any()
    .reset_index()
    .sort_values(["NUM_DOC_CRYPTO", "ATE_FECATENCION"])
)

print("  Buscando brechas largas seguidas de retorno (posible recaida)...")
recaida_rows = []
for pid, g in fechas_actividad.groupby("NUM_DOC_CRYPTO"):
    fechas = g["ATE_FECATENCION"].tolist()
    activos = g["ES_TRATAMIENTO_ACTIVO"].tolist()
    if len(fechas) < 2:
        continue
    tipo_retorno = None
    fecha_retorno = None
    dias_brecha = None
    for i in range(1, len(fechas)):
        gap = (fechas[i] - fechas[i - 1]) / np.timedelta64(1, "D")
        if gap >= UMBRAL_SIN_SEGUIMIENTO_DIAS:
            ventana_fin = fechas[i] + pd.Timedelta(days=VENTANA_RETORNO_DIAS)
            en_ventana_activo = any(a for f, a in zip(fechas[i:], activos[i:]) if f <= ventana_fin)
            if en_ventana_activo:
                tipo_retorno, fecha_retorno, dias_brecha = "ACTIVO", fechas[i], gap
                break  # nos quedamos con la primera recaida activa detectada
            elif tipo_retorno is None:
                tipo_retorno, fecha_retorno, dias_brecha = "CONTROL", fechas[i], gap
    if tipo_retorno is not None:
        recaida_rows.append({
            "NUM_DOC_CRYPTO": pid,
            "TIPO_RETORNO_TRAS_BRECHA": tipo_retorno,
            "FECHA_RETORNO_TRAS_BRECHA": fecha_retorno,
            "DIAS_BRECHA_PREVIA_RETORNO": dias_brecha,
        })
recaida_df = pd.DataFrame(recaida_rows) if recaida_rows else pd.DataFrame(
    columns=["NUM_DOC_CRYPTO", "TIPO_RETORNO_TRAS_BRECHA", "FECHA_RETORNO_TRAS_BRECHA", "DIAS_BRECHA_PREVIA_RETORNO"])

n_recaida = (recaida_df["TIPO_RETORNO_TRAS_BRECHA"] == "ACTIVO").sum()
n_control = (recaida_df["TIPO_RETORNO_TRAS_BRECHA"] == "CONTROL").sum()
print(f"    Pacientes con retorno tras brecha larga -> con tratamiento activo: {n_recaida:,} | "
      f"solo control/chequeo: {n_control:,}")

hito4 = perfil[["NUM_DOC_CRYPTO", "FALLECIDO", "FEC_FALLECIMIENTO", "TUVO_PALIATIVO",
                "ENFERMEDAD_AVANZADA", "ULTIMA_ATENCION", "SUPERVIVENCIA_DIAS"]].copy()
hito4["DIAS_DESDE_ULTIMA_ATENCION"] = (FECHA_CORTE - hito4["ULTIMA_ATENCION"]).dt.days
hito4 = hito4.merge(recaida_df, on="NUM_DOC_CRYPTO", how="left")


def clasificar_desenlace(row):
    if row["FALLECIDO"]:
        return "FALLECIDO"
    if row["TUVO_PALIATIVO"]:
        return "PALIATIVO"
    if row["TIPO_RETORNO_TRAS_BRECHA"] == "ACTIVO":
        return "RECAIDA_PROBABLE"
    if row["TIPO_RETORNO_TRAS_BRECHA"] == "CONTROL":
        return "CONTROL_POST_PAUSA"
    if row["DIAS_DESDE_ULTIMA_ATENCION"] >= UMBRAL_SIN_SEGUIMIENTO_DIAS:
        return "POSIBLE_REMISION_O_ALTA"
    return "EN_SEGUIMIENTO_ACTIVO"


hito4["DESENLACE"] = hito4.apply(clasificar_desenlace, axis=1)
hito4["FECHA_DESENLACE"] = np.where(hito4["FALLECIDO"], hito4["FEC_FALLECIMIENTO"], hito4["ULTIMA_ATENCION"])
hito4["FECHA_DESENLACE"] = pd.to_datetime(hito4["FECHA_DESENLACE"])

print("  Distribucion de desenlaces:")
for cat, n in hito4["DESENLACE"].value_counts().items():
    print(f"    {cat:>25s}: {n:>6,} ({n/len(hito4)*100:5.1f}%)")


# =====================================================================
# CONSOLIDACION: TABLA ANCHA (1 fila por paciente)
# =====================================================================
print("\n" + "=" * 70)
print("CONSOLIDANDO TABLA DE HITOS POR PACIENTE")
print("=" * 70)

cols_perfil = ["NUM_DOC_CRYPTO", "SEXO", "EDAD_PRIMERA_ATENCION", "RANGO_EDAD",
               "DEPARTAMENTO", "PROVINCIA", "MONTO_NETO_TOTAL", "MONTO_BRUTO_TOTAL"]
hitos_pac = perfil[cols_perfil].merge(hito1, on="NUM_DOC_CRYPTO", how="left")
hitos_pac = hitos_pac.merge(hito2, on="NUM_DOC_CRYPTO", how="left")
hitos_pac = hitos_pac.merge(hito3.drop(columns=["FECHA_DIAGNOSTICO"]), on="NUM_DOC_CRYPTO", how="left")
hitos_pac = hitos_pac.merge(hito4.drop(columns=["FEC_FALLECIMIENTO"]), on="NUM_DOC_CRYPTO", how="left")

print(f"  Tabla final: {len(hitos_pac):,} pacientes x {hitos_pac.shape[1]} columnas")

out_pac = SILVER / "FISSAL_CCR_HITOS_PACIENTE.parquet"
hitos_pac.to_parquet(out_pac, index=False)
print(f"  Guardado: {out_pac}")


# =====================================================================
# TABLA LARGA: 1 FILA POR PACIENTE x HITO (para analisis/graficos comparativos)
# =====================================================================
eventos = []

e1 = hito1[["NUM_DOC_CRYPTO"]].copy()
e1["HITO"] = "1_DESPISTAJE"
e1["FECHA_INICIO"] = hito1["FECHA_PRIMER_DESPISTAJE"]
e1["FECHA_FIN"] = hito1["FECHA_PRIMER_DESPISTAJE"]
e1["DURACION_DIAS"] = 0
e1["COSTO_NETO"] = hito1["COSTO_NETO_PRE_DIAGNOSTICO"]
e1["COSTO_BRUTO"] = hito1["COSTO_BRUTO_PRE_DIAGNOSTICO"]
e1["N_EVENTOS"] = hito1["N_REGISTROS_PRE_DIAGNOSTICO"]
eventos.append(e1)

e2 = hito2[["NUM_DOC_CRYPTO"]].copy()
e2 = e2.merge(hito1[["NUM_DOC_CRYPTO", "FECHA_DIAGNOSTICO"]], on="NUM_DOC_CRYPTO", how="left")
e2["HITO"] = "2_DIAGNOSTICO"
e2["FECHA_INICIO"] = e2["FECHA_DIAGNOSTICO"]
e2["FECHA_FIN"] = e2["FECHA_DIAGNOSTICO"]
e2["DURACION_DIAS"] = 0
e2["COSTO_NETO"] = np.nan
e2["COSTO_BRUTO"] = np.nan
e2["N_EVENTOS"] = 1
e2 = e2.drop(columns=["FECHA_DIAGNOSTICO"])
eventos.append(e2)

e3 = hito3[["NUM_DOC_CRYPTO", "FECHA_INICIO_TRATAMIENTO", "FECHA_FIN_TRATAMIENTO",
            "COSTO_NETO_TRATAMIENTO_TOTAL", "COSTO_BRUTO_TRATAMIENTO_TOTAL"]].copy()
e3["HITO"] = "3_TRATAMIENTO"
e3["DURACION_DIAS"] = (e3["FECHA_FIN_TRATAMIENTO"] - e3["FECHA_INICIO_TRATAMIENTO"]).dt.days
e3["N_EVENTOS"] = (
    hito3["N_SESIONES_CIRUGIA"] + hito3["N_SESIONES_QUIMIOTERAPIA"] + hito3["N_SESIONES_RADIOTERAPIA"]
)
e3 = e3.rename(columns={
    "FECHA_INICIO_TRATAMIENTO": "FECHA_INICIO", "FECHA_FIN_TRATAMIENTO": "FECHA_FIN",
    "COSTO_NETO_TRATAMIENTO_TOTAL": "COSTO_NETO", "COSTO_BRUTO_TRATAMIENTO_TOTAL": "COSTO_BRUTO",
})
eventos.append(e3)

e4 = hito4[["NUM_DOC_CRYPTO", "FECHA_DESENLACE"]].copy()
e4["HITO"] = "4_DESENLACE"
e4["FECHA_INICIO"] = e4["FECHA_DESENLACE"]
e4["FECHA_FIN"] = e4["FECHA_DESENLACE"]
e4["DURACION_DIAS"] = 0
e4["COSTO_NETO"] = np.nan
e4["COSTO_BRUTO"] = np.nan
e4["N_EVENTOS"] = 1
e4 = e4.drop(columns=["FECHA_DESENLACE"])
eventos.append(e4)

cols_orden = ["NUM_DOC_CRYPTO", "HITO", "FECHA_INICIO", "FECHA_FIN", "DURACION_DIAS",
              "COSTO_NETO", "COSTO_BRUTO", "N_EVENTOS"]
eventos_df = pd.concat([e[cols_orden] for e in eventos], ignore_index=True)
eventos_df = eventos_df.merge(perfil[["NUM_DOC_CRYPTO", "SEXO", "RANGO_EDAD", "DEPARTAMENTO"]],
                               on="NUM_DOC_CRYPTO", how="left")

out_eventos = SILVER / "FISSAL_CCR_HITOS_EVENTOS.parquet"
eventos_df.to_parquet(out_eventos, index=False)
print(f"  Guardado: {out_eventos}")

print(f"\n{'=' * 70}")
print("Fin de la construccion de hitos.")
print(f"{'=' * 70}")
