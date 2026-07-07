import sys
import pandas as pd
import numpy as np
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SILVER = Path(r"C:\Users\eah\apoyoconsultoria.com\File Server - Analytics\7 Datos\Datos abiertos\fissal\01_silver")
ARCHIVO_CCR = SILVER / "FISSAL_CANCER_COLORRECTAL_2016_2022.parquet"
ARCHIVO_HITOS = SILVER / "FISSAL_CCR_HITOS_PACIENTE.parquet"
ARCHIVO_COSTEO_HITO = SILVER / "FISSAL_CCR_COSTEO_HITO.parquet"
ARCHIVO_COSTEO_SUBCAT = SILVER / "FISSAL_CCR_COSTEO_HITO_SUBCATEGORIA.parquet"
ARCHIVO_COSTEO_HITO_ANIO_CAL = SILVER / "FISSAL_CCR_COSTEO_HITO_ANIO_CALENDARIO.parquet"

SALIDA_DIR = SILVER.parent / "03_output" / "hitos_paciente"
SALIDA_DIR.mkdir(parents=True, exist_ok=True)
SALIDA_XLSX = SALIDA_DIR / "FISSAL_CCR_Analisis_Costos_Tiempos.xlsx"

ORDEN_HITOS = ["1_DESPISTAJE", "2_DIAGNOSTICO", "3_TRATAMIENTO", "4_DESENLACE"]

# Etiquetas de "transicion" para la hoja 3_EvolucionDias (mismos 4 hitos, solo
# se renombran para dejar explicito el recorrido de un hito al siguiente).
HITO_TRANSICION = {
    "1_DESPISTAJE": "1_Despistaje_a_Diagnostico",
    "2_DIAGNOSTICO": "2_Diagnostico",
    "3_TRATAMIENTO": "3_Diagnostico_a_FinTratamiento",
    "4_DESENLACE": "4_FinTratamiento_a_Desenlace",
}

print("=" * 70)
print("EXPORTANDO ANALISIS DE COSTOS Y TIEMPOS POR HITO A EXCEL")
print("=" * 70)

hp = pd.read_parquet(ARCHIVO_HITOS, columns=[
    "NUM_DOC_CRYPTO", "FECHA_DIAGNOSTICO", "FECHA_FIN_TRATAMIENTO", "FECHA_DESENLACE",
    "SECUENCIA_TRATAMIENTO", "DIAS_DESPISTAJE_A_DIAGNOSTICO", "DIAS_DIAGNOSTICO_A_TRATAMIENTO",
])
hp["ANIO_DIAGNOSTICO"] = hp["FECHA_DIAGNOSTICO"].dt.year
tuvo_trat = hp["SECUENCIA_TRATAMIENTO"] != "SIN_TRATAMIENTO_DETECTADO"
hp["TRAT_A_DESENLACE"] = np.where(
    tuvo_trat, (hp["FECHA_DESENLACE"] - hp["FECHA_FIN_TRATAMIENTO"]).dt.days, np.nan)
hp["DX_A_DESENLACE"] = (hp["FECHA_DESENLACE"] - hp["FECHA_DIAGNOSTICO"]).dt.days

costeo_hito = pd.read_parquet(ARCHIVO_COSTEO_HITO)
costeo_subcat = pd.read_parquet(ARCHIVO_COSTEO_SUBCAT)
costeo_hito = costeo_hito.merge(hp[["NUM_DOC_CRYPTO", "ANIO_DIAGNOSTICO"]], on="NUM_DOC_CRYPTO", how="left")
costeo_subcat = costeo_subcat.merge(hp[["NUM_DOC_CRYPTO", "ANIO_DIAGNOSTICO"]], on="NUM_DOC_CRYPTO", how="left")

print(f"Pacientes: {len(hp):,}")


def poblacion_hito(df_hito, hito):
    """Para el Hito 1 (despistaje), solo cuentan los pacientes con actividad
    pre-diagnostico real (N_LINEAS > 0) -- de lo contrario el 86.6% de pacientes
    cuyo primer contacto YA es el diagnostico infla el grupo con duracion/costo=0
    y aplana las medianas. Los demas hitos ya vienen filtrados desde el parquet
    intermedio (Hito 3 solo incluye pacientes con tratamiento detectado)."""
    if hito == "1_DESPISTAJE":
        return df_hito[df_hito["N_LINEAS"] > 0]
    return df_hito


# =====================================================================
# ANALISIS 1: COSTO Y TIEMPO POR HITO
# =====================================================================
print("\nAnalisis 1: costo y tiempo por hito...")


def stats_costo_tiempo(sub):
    return {
        "N_PACIENTES": len(sub),
        "COSTO_NETO_MEDIA": sub["COSTO_NETO"].mean(),
        "COSTO_NETO_MEDIANA": sub["COSTO_NETO"].median(),
        "DURACION_DIAS_MEDIA": sub["DURACION_DIAS"].mean(),
        "DURACION_DIAS_MEDIANA": sub["DURACION_DIAS"].median(),
    }


filas = []
for h in ORDEN_HITOS:
    sub = poblacion_hito(costeo_hito[costeo_hito["HITO"] == h], h)
    filas.append({"HITO": h, **stats_costo_tiempo(sub)})
tabla1_general = pd.DataFrame(filas)

filas = []
for h in ORDEN_HITOS:
    sub_h = poblacion_hito(costeo_hito[costeo_hito["HITO"] == h], h)
    for anio, sub in sub_h.groupby("ANIO_DIAGNOSTICO"):
        filas.append({"ANIO_DIAGNOSTICO": int(anio), "HITO": h, **stats_costo_tiempo(sub)})
tabla1_por_anio = pd.DataFrame(filas).sort_values(["ANIO_DIAGNOSTICO", "HITO"])

TRANSICIONES = [
    ("DIAS_DESPISTAJE_A_DIAGNOSTICO", "1. Despistaje -> Diagnostico"),
    ("DIAS_DIAGNOSTICO_A_TRATAMIENTO", "2. Diagnostico -> Tratamiento"),
    ("TRAT_A_DESENLACE", "3. Tratamiento -> Desenlace"),
    ("DX_A_DESENLACE", "4. Diagnostico -> Desenlace (trayectoria total)"),
]


def stats_dias(s):
    s = s.dropna()
    s = s[s >= 0]
    if len(s) == 0:
        return {"N": 0, "DIAS_MEDIA": np.nan, "DIAS_MEDIANA": np.nan}
    return {"N": len(s), "DIAS_MEDIA": s.mean(), "DIAS_MEDIANA": s.median()}


filas = []
for col, label in TRANSICIONES:
    filas.append({"TRANSICION": label, **stats_dias(hp[col])})
tabla1_trans_general = pd.DataFrame(filas)

filas = []
for col, label in TRANSICIONES:
    for anio, sub in hp.groupby("ANIO_DIAGNOSTICO"):
        filas.append({"ANIO_DIAGNOSTICO": int(anio), "TRANSICION": label, **stats_dias(sub[col])})
tabla1_trans_por_anio = pd.DataFrame(filas).sort_values(["ANIO_DIAGNOSTICO", "TRANSICION"])

# =====================================================================
# ANALISIS 2: DESGLOSE DE GASTO POR SUBCATEGORIA DENTRO DE CADA HITO
# =====================================================================
print("Analisis 2: desglose de gasto por subcategoria...")


def desglose_grupo(costeo_hito_g, costeo_subcat_g):
    pac_pop = costeo_hito_g["NUM_DOC_CRYPTO"].unique()
    n_pac = len(pac_pop)
    costo_total_hito = costeo_hito_g["COSTO_NETO"].sum()
    lineas_total_hito = costeo_hito_g["N_LINEAS"].sum()
    # Duracion (dias) del hito, PARA CADA PACIENTE -- para poder decir "de los
    # X dias que duro este hito PARA ESTE PACIENTE, cuantos tuvieron actividad
    # de esta subcategoria". >0 evita dividir entre 0 en el hito 2 (evento
    # puntual, duracion=0) o pacientes con duracion=0.
    duracion_por_pac = costeo_hito_g.set_index("NUM_DOC_CRYPTO")["DURACION_DIAS"].reindex(pac_pop)
    duracion_valida = duracion_por_pac.where(duracion_por_pac > 0)
    filas = []
    for (cat, subcat), sub in costeo_subcat_g.groupby(["categoria_recurso_502", "subcategoria_recurso_502"]):
        costo_por_pac = sub.set_index("NUM_DOC_CRYPTO")["COSTO_NETO"].reindex(pac_pop, fill_value=0)
        dias_por_pac = sub.set_index("NUM_DOC_CRYPTO")["N_DIAS_DISTINTOS"].reindex(pac_pop, fill_value=0)
        pct_dias_por_pac = (dias_por_pac / duracion_valida * 100)
        filas.append({
            "CATEGORIA": cat, "SUBCATEGORIA": subcat,
            "N_PACIENTES_CON_GASTO": int((costo_por_pac > 0).sum()),
            "COSTO_NETO_MEDIA": costo_por_pac.mean(),
            "COSTO_NETO_MEDIANA": costo_por_pac.median(),
            "COSTO_NETO_TOTAL": sub["COSTO_NETO"].sum(),
            "N_DIAS_MEDIA": dias_por_pac.mean(),
            "N_DIAS_MEDIANA": dias_por_pac.median(),
            "PCT_DIAS_DEL_HITO_MEDIA": pct_dias_por_pac.mean(),
            "PCT_DIAS_DEL_HITO_MEDIANA": pct_dias_por_pac.median(),
            "PCT_COSTO_DEL_HITO": (sub["COSTO_NETO"].sum() / costo_total_hito * 100) if costo_total_hito else np.nan,
            "PCT_LINEAS_DEL_HITO": (sub["N_LINEAS"].sum() / lineas_total_hito * 100) if lineas_total_hito else np.nan,
        })
    out = pd.DataFrame(filas)
    if len(out) == 0:
        return out
    out.insert(0, "N_PACIENTES_HITO", n_pac)
    return out.sort_values("PCT_COSTO_DEL_HITO", ascending=False)


tablas2 = []
for h in ORDEN_HITOS:
    chg = poblacion_hito(costeo_hito[costeo_hito["HITO"] == h], h)
    pac_set = set(chg["NUM_DOC_CRYPTO"])
    csg = costeo_subcat[(costeo_subcat["HITO"] == h) & (costeo_subcat["NUM_DOC_CRYPTO"].isin(pac_set))]
    t = desglose_grupo(chg, csg)
    t.insert(0, "HITO", h)
    tablas2.append(t)
tabla2_general = pd.concat(tablas2, ignore_index=True)

tablas2_anio = []
for h in ORDEN_HITOS:
    chg = poblacion_hito(costeo_hito[costeo_hito["HITO"] == h], h)
    for anio, chg_a in chg.groupby("ANIO_DIAGNOSTICO"):
        pac_set = set(chg_a["NUM_DOC_CRYPTO"])
        csg = costeo_subcat[(costeo_subcat["HITO"] == h) & (costeo_subcat["NUM_DOC_CRYPTO"].isin(pac_set))]
        t = desglose_grupo(chg_a, csg)
        if len(t) == 0:
            continue
        t.insert(0, "ANIO_DIAGNOSTICO", int(anio))
        t.insert(1, "HITO", h)
        tablas2_anio.append(t)
tabla2_por_anio = pd.concat(tablas2_anio, ignore_index=True)

# =====================================================================
# ANALISIS 3: EVOLUCION DE LA COMPOSICION DE GASTO/ACTIVIDAD ENTRE HITOS
# =====================================================================
print("Analisis 3: evolucion de composicion entre hitos...")


def pivotear_evolucion(tabla2, by_anio):
    idx = (["ANIO_DIAGNOSTICO"] if by_anio else []) + ["CATEGORIA", "SUBCATEGORIA"]
    piv_costo = tabla2.pivot_table(index=idx, columns="HITO", values="PCT_COSTO_DEL_HITO", fill_value=0)
    piv_costo.columns = [f"PCT_COSTO_{c}" for c in piv_costo.columns]
    piv_lineas = tabla2.pivot_table(index=idx, columns="HITO", values="PCT_LINEAS_DEL_HITO", fill_value=0)
    piv_lineas.columns = [f"PCT_LINEAS_{c}" for c in piv_lineas.columns]
    out = piv_costo.join(piv_lineas, how="outer").reset_index()
    return out


def pivotear_evolucion_soles(tabla2, by_anio):
    """Misma idea que pivotear_evolucion, pero con el gasto APROXIMADO POR
    PACIENTE en soles (media y mediana, ya calculadas en desglose_grupo sobre
    la poblacion completa del hito, incluyendo pacientes con $0 en esa
    subcategoria) en vez del % que representa dentro de cada hito. La mediana
    es la lectura mas segura cuando hay pocos pacientes u outliers (ver
    seccion de calidad de datos del README de hitos_paciente)."""
    idx = (["ANIO_DIAGNOSTICO"] if by_anio else []) + ["CATEGORIA", "SUBCATEGORIA"]
    piv_media = tabla2.pivot_table(index=idx, columns="HITO", values="COSTO_NETO_MEDIA", fill_value=0)
    piv_media.columns = [f"COSTO_MEDIA_{c}" for c in piv_media.columns]
    piv_mediana = tabla2.pivot_table(index=idx, columns="HITO", values="COSTO_NETO_MEDIANA", fill_value=0)
    piv_mediana.columns = [f"COSTO_MEDIANA_{c}" for c in piv_mediana.columns]
    return piv_media.join(piv_mediana, how="outer").reset_index()


def pivotear_evolucion_dias(tabla2, by_anio):
    """Misma idea, pero con el tiempo APROXIMADO POR PACIENTE dentro de cada
    transicion, no un total sumado entre pacientes (eso no era una medida
    confiable: mezclaba el tamano del grupo con la duracion real). Para cada
    paciente se calcula, de los dias que le tomo esa transicion completa
    (DURACION_DIAS del hito para ESE paciente), cuantos tuvieron actividad de
    esta subcategoria -- luego se promedia (media/mediana) entre pacientes:
      N_DIAS_*        : dias (absolutos) con actividad de la subcategoria.
      PCT_DIAS_HITO_*  : lo mismo, como % de la duracion total de la transicion
                         (ej. si la transicion duro 100 dias y 22 tuvieron
                         actividad de Laboratorio, PCT_DIAS_HITO = 22%).
    El hito 2 (Diagnostico) es un evento puntual (duracion 0), asi que
    PCT_DIAS_HITO no aplica ahi (queda vacio).
    Los 4 hitos se renombran como HITO_TRANSICION para dejar explicito el
    recorrido de un hito al siguiente (mismos 4 grupos, distinta etiqueta)."""
    idx = (["ANIO_DIAGNOSTICO"] if by_anio else []) + ["CATEGORIA", "SUBCATEGORIA"]

    def pivotear(valor, prefijo, fill_value=None):
        piv = tabla2.pivot_table(index=idx, columns="HITO", values=valor, fill_value=fill_value)
        piv.columns = [f"{prefijo}_{HITO_TRANSICION.get(c, c)}" for c in piv.columns]
        return piv

    # N_DIAS: combinacion sin datos = 0 dias de actividad. PCT_DIAS: se deja
    # NaN (no forzar a 0) cuando la duracion del hito es 0 para ese paciente
    # (hito 2) o el grupo no tiene ningun paciente con duracion valida.
    piv_dias_media = pivotear("N_DIAS_MEDIA", "N_DIAS_MEDIA", fill_value=0)
    piv_dias_mediana = pivotear("N_DIAS_MEDIANA", "N_DIAS_MEDIANA", fill_value=0)
    piv_pct_media = pivotear("PCT_DIAS_DEL_HITO_MEDIA", "PCT_DIAS_HITO_MEDIA")
    piv_pct_mediana = pivotear("PCT_DIAS_DEL_HITO_MEDIANA", "PCT_DIAS_HITO_MEDIANA")
    out = piv_dias_media.join([piv_dias_mediana, piv_pct_media, piv_pct_mediana], how="outer")
    return out.reset_index()


tabla3_general = pivotear_evolucion(tabla2_general, by_anio=False)
tabla3_por_anio = pivotear_evolucion(tabla2_por_anio, by_anio=True)
tabla3_soles_general = pivotear_evolucion_soles(tabla2_general, by_anio=False)
tabla3_soles_por_anio = pivotear_evolucion_soles(tabla2_por_anio, by_anio=True)
tabla3_dias_general = pivotear_evolucion_dias(tabla2_general, by_anio=False)
tabla3_dias_por_anio = pivotear_evolucion_dias(tabla2_por_anio, by_anio=True)

# =====================================================================
# ANALISIS 4 (ADICIONAL): COSTO POR PACIENTE, POR ANIO CALENDARIO
# =====================================================================
print("Analisis 4: costo por paciente, por anio calendario...")
ccr_costo = pd.read_parquet(ARCHIVO_CCR, columns=["NUM_DOC_CRYPTO", "ATE_FECATENCION", "ATE_MONTONETO"])
ccr_costo["ANIO_CALENDARIO"] = ccr_costo["ATE_FECATENCION"].dt.year
# Un pequeño numero de registros trae ATE_FECATENCION anterior a 2016 (error de captura /
# atencion registrada retroactivamente); se excluyen para no ensuciar la serie 2016-2022.
n_fuera_rango = (~ccr_costo["ANIO_CALENDARIO"].between(2016, 2022)).sum()
print(f"  Registros con ATE_FECATENCION fuera de 2016-2022 (excluidos): {n_fuera_rango:,}")
ccr_costo = ccr_costo[ccr_costo["ANIO_CALENDARIO"].between(2016, 2022)]
costo_pac_anio = ccr_costo.groupby(["NUM_DOC_CRYPTO", "ANIO_CALENDARIO"], as_index=False)["ATE_MONTONETO"].sum()
tabla4 = costo_pac_anio.groupby("ANIO_CALENDARIO").agg(
    N_PACIENTES=("ATE_MONTONETO", "count"),
    COSTO_NETO_MEDIA=("ATE_MONTONETO", "mean"),
    COSTO_NETO_MEDIANA=("ATE_MONTONETO", "median"),
    COSTO_NETO_P25=("ATE_MONTONETO", lambda s: s.quantile(.25)),
    COSTO_NETO_P75=("ATE_MONTONETO", lambda s: s.quantile(.75)),
    COSTO_NETO_TOTAL=("ATE_MONTONETO", "sum"),
).reset_index()

# =====================================================================
# ANALISIS 5: DIAS HOSPITALIZADO POR HITO
# =====================================================================
print("Analisis 5: dias hospitalizado por hito...")

hosp = pd.read_parquet(ARCHIVO_CCR, columns=[
    "NUM_DOC_CRYPTO", "ATE_FECINGHOSP", "ATE_FECALTHOSP", "DIAS_HOSPITALIZACION"])
hosp = hosp.dropna(subset=["ATE_FECINGHOSP", "ATE_FECALTHOSP"])
# Un mismo episodio de hospitalizacion genera varias lineas de facturacion
# (procedimientos, medicamentos, etc. durante la estancia); se deduplica por
# (paciente, fecha ingreso, fecha alta) para no sumar los mismos dias varias veces.
hosp = hosp.drop_duplicates(subset=["NUM_DOC_CRYPTO", "ATE_FECINGHOSP", "ATE_FECALTHOSP"])

fechas_hosp = hp.set_index("NUM_DOC_CRYPTO")[
    ["FECHA_DIAGNOSTICO", "FECHA_FIN_TRATAMIENTO", "FECHA_DESENLACE", "SECUENCIA_TRATAMIENTO"]]
hosp = hosp.join(fechas_hosp, on="NUM_DOC_CRYPTO")
tuvo_trat_h = hosp["SECUENCIA_TRATAMIENTO"] != "SIN_TRATAMIENTO_DETECTADO"
inicio_4_h = pd.to_datetime(np.where(tuvo_trat_h, hosp["FECHA_FIN_TRATAMIENTO"], hosp["FECHA_DIAGNOSTICO"]))

# Un episodio se asigna al hito segun su fecha de INGRESO (ATE_FECINGHOSP),
# con el mismo criterio de ventanas que clasifica cada linea de facturacion
# en 06_costeo_categoria_hito.py (por ATE_FECATENCION).
episodios_hito = []
m1 = hosp["ATE_FECINGHOSP"] < hosp["FECHA_DIAGNOSTICO"]
e1 = hosp.loc[m1, ["NUM_DOC_CRYPTO", "DIAS_HOSPITALIZACION"]].copy()
e1["HITO"] = "1_DESPISTAJE"
episodios_hito.append(e1)

m2 = hosp["ATE_FECINGHOSP"] == hosp["FECHA_DIAGNOSTICO"]
e2 = hosp.loc[m2, ["NUM_DOC_CRYPTO", "DIAS_HOSPITALIZACION"]].copy()
e2["HITO"] = "2_DIAGNOSTICO"
episodios_hito.append(e2)

m3 = tuvo_trat_h & (hosp["ATE_FECINGHOSP"] > hosp["FECHA_DIAGNOSTICO"]) & \
    (hosp["ATE_FECINGHOSP"] <= hosp["FECHA_FIN_TRATAMIENTO"])
e3 = hosp.loc[m3, ["NUM_DOC_CRYPTO", "DIAS_HOSPITALIZACION"]].copy()
e3["HITO"] = "3_TRATAMIENTO"
episodios_hito.append(e3)

m4 = (hosp["ATE_FECINGHOSP"] > inicio_4_h) & (hosp["ATE_FECINGHOSP"] <= hosp["FECHA_DESENLACE"])
e4 = hosp.loc[m4, ["NUM_DOC_CRYPTO", "DIAS_HOSPITALIZACION"]].copy()
e4["HITO"] = "4_DESENLACE"
episodios_hito.append(e4)

hosp_hito = pd.concat(episodios_hito, ignore_index=True).groupby(
    ["NUM_DOC_CRYPTO", "HITO"], as_index=False)["DIAS_HOSPITALIZACION"].sum().rename(
    columns={"DIAS_HOSPITALIZACION": "DIAS_HOSPITALIZACION_HITO"})

costeo_hito_hosp = costeo_hito.merge(hosp_hito, on=["NUM_DOC_CRYPTO", "HITO"], how="left")
costeo_hito_hosp["DIAS_HOSPITALIZACION_HITO"] = costeo_hito_hosp["DIAS_HOSPITALIZACION_HITO"].fillna(0)


def stats_hospitalizacion(sub):
    return {
        "N_PACIENTES": len(sub),
        "N_PAC_CON_HOSPITALIZACION": int((sub["DIAS_HOSPITALIZACION_HITO"] > 0).sum()),
        "DIAS_HOSP_MEDIA": sub["DIAS_HOSPITALIZACION_HITO"].mean(),
        "DIAS_HOSP_MEDIANA": sub["DIAS_HOSPITALIZACION_HITO"].median(),
    }


filas = []
for h in ORDEN_HITOS:
    sub = poblacion_hito(costeo_hito_hosp[costeo_hito_hosp["HITO"] == h], h)
    filas.append({"HITO": h, **stats_hospitalizacion(sub)})
tabla5_general = pd.DataFrame(filas)

filas = []
for h in ORDEN_HITOS:
    sub_h = poblacion_hito(costeo_hito_hosp[costeo_hito_hosp["HITO"] == h], h)
    for anio, sub in sub_h.groupby("ANIO_DIAGNOSTICO"):
        filas.append({"ANIO_DIAGNOSTICO": int(anio), "HITO": h, **stats_hospitalizacion(sub)})
tabla5_por_anio = pd.DataFrame(filas).sort_values(["ANIO_DIAGNOSTICO", "HITO"])

# =====================================================================
# ANALISIS 6 (EXTRA): 1_CostoTiempo_PorAnio, pero por ANIO CALENDARIO REAL
# en vez del anio de DIAGNOSTICO de la cohorte. Un hito que dura varios anios
# (Tratamiento, Desenlace) reparte su costo Y su duracion entre cada anio
# calendario que realmente toca -- misma poblacion e idea que 1_CostoTiempo_
# PorAnio (se rellena con 0 costo/0 dias a quien "pertenece" al hito ese anio
# pero no tuvo actividad), solo que el eje ya no es el anio de diagnostico.
# =====================================================================
print("Analisis 6: costo y duracion por hito, por anio calendario real...")

costeo_hito_anio_cal = pd.read_parquet(ARCHIVO_COSTEO_HITO_ANIO_CAL)
ANIOS_CALENDARIO = range(2012, 2023)


def ventana_por_anio(df_hito):
    """Para cada paciente de df_hito, genera 1 fila por cada anio calendario
    que su ventana [FECHA_INICIO, FECHA_FIN] toca, con DIAS_EN_ANIO = dias de
    esa ventana recortados (clip) a ese anio especifico."""
    df_hito = df_hito.dropna(subset=["FECHA_INICIO", "FECHA_FIN"])
    filas = []
    for anio in ANIOS_CALENDARIO:
        ini_anio = pd.Timestamp(f"{anio}-01-01")
        fin_anio = pd.Timestamp(f"{anio}-12-31")
        solapa = (df_hito["FECHA_INICIO"] <= fin_anio) & (df_hito["FECHA_FIN"] >= ini_anio)
        if not solapa.any():
            continue
        sub = df_hito.loc[solapa, ["NUM_DOC_CRYPTO"]].copy()
        inicio_clip = df_hito.loc[solapa, "FECHA_INICIO"].clip(lower=ini_anio)
        fin_clip = df_hito.loc[solapa, "FECHA_FIN"].clip(upper=fin_anio)
        sub["ANIO_CALENDARIO"] = anio
        sub["DIAS_EN_ANIO"] = (fin_clip - inicio_clip).dt.days
        filas.append(sub)
    if not filas:
        return pd.DataFrame(columns=["NUM_DOC_CRYPTO", "ANIO_CALENDARIO", "DIAS_EN_ANIO"])
    return pd.concat(filas, ignore_index=True)


filas6 = []
for h in ORDEN_HITOS:
    pobl = poblacion_hito(costeo_hito[costeo_hito["HITO"] == h], h)
    van = ventana_por_anio(pobl)
    # costo real de ESE paciente en ESE hito, en ESE anio calendario (ya
    # calculado a partir de la fecha real de cada linea, mas preciso que
    # repartir el costo total del hito de forma proporcional a los dias)
    costo_h = costeo_hito_anio_cal[costeo_hito_anio_cal["HITO"] == h][
        ["NUM_DOC_CRYPTO", "ANIO_CALENDARIO", "COSTO_NETO"]]
    van = van.merge(costo_h, on=["NUM_DOC_CRYPTO", "ANIO_CALENDARIO"], how="left")
    van["COSTO_NETO"] = van["COSTO_NETO"].fillna(0)
    for anio, sub in van.groupby("ANIO_CALENDARIO"):
        filas6.append({
            "ANIO_CALENDARIO": int(anio), "HITO": h,
            "N_PACIENTES": len(sub),
            "COSTO_NETO_MEDIA": sub["COSTO_NETO"].mean(),
            "COSTO_NETO_MEDIANA": sub["COSTO_NETO"].median(),
            "DURACION_DIAS_MEDIA": sub["DIAS_EN_ANIO"].mean(),
            "DURACION_DIAS_MEDIANA": sub["DIAS_EN_ANIO"].median(),
        })
tabla6_por_anio_cal = pd.DataFrame(filas6).sort_values(["ANIO_CALENDARIO", "HITO"])

# =====================================================================
# HOJA DE NOTAS
# =====================================================================
notas = pd.DataFrame({"Nota": [
    "Este archivo resume 4 analisis sobre la trayectoria de pacientes de cancer colorrectal en FISSAL 2016-2022.",
    "",
    "DEFINICION DE LOS 4 HITOS Y SU VENTANA DE COSTO:",
    "  1_DESPISTAJE: toda actividad ANTES del diagnostico CCR (misma ventana que COSTO_NETO_PRE_DIAGNOSTICO).",
    "  2_DIAGNOSTICO: solo el dia exacto del diagnostico (evento puntual).",
    "  3_TRATAMIENTO: (diagnostico, fin de tratamiento], solo pacientes con tratamiento detectado.",
    "  4_DESENLACE: (fin de tratamiento, desenlace] si tuvo tratamiento, o (diagnostico, desenlace] si no.",
    "Cada registro de facturacion cae en exactamente 1 hito (particion sin huecos ni doble conteo).",
    "",
    "HOJAS '..._General' vs '..._PorAnio':",
    "  Las hojas 1, 2 y 3 segmentan 'por anio' usando el AÑO DE DIAGNOSTICO (cohorte): todo lo que le",
    "  pasa a un paciente diagnosticado en 2019 se reporta bajo 2019, aunque su tratamiento o desenlace",
    "  ocurra despues.",
    "  La hoja 4 (analisis adicional) usa el AÑO CALENDARIO de cada atencion, no la cohorte de",
    "  diagnostico, porque responde una pregunta distinta: cuanto gasto el sistema en estos pacientes",
    "  cada año calendario.",
    "",
    "Hito 1 (despistaje): las estadisticas de costo/tiempo/desglose solo consideran a los pacientes con",
    "actividad real antes del diagnostico (N_LINEAS > 0). El 86.6% de los pacientes CCR no tiene ningun",
    "registro previo en FISSAL (su primer contacto YA es el diagnostico), y si se incluyeran inflarian",
    "el grupo con duracion/costo = 0.",
    "",
    "Deteccion de tratamiento (Hito 3): combina el regex de texto original con una señal adicional del",
    "diccionario diccionario_ATE_DESCCONSUMO_502_estandarizado.xlsx (categoria/subcategoria_recurso_502),",
    "ver README de fissal/hitos_paciente para el detalle de las reglas usadas.",
    "",
    "Analisis 2 (desglose): subcategoria_recurso_502 del diccionario 502 (mas fina que la categoria",
    "general, para distinguir p.ej. quimioterapia de radioterapia). COSTO_NETO_MEDIA/MEDIANA son por",
    "paciente DENTRO del hito (incluye pacientes con $0 en esa subcategoria). PCT_COSTO_DEL_HITO / ",
    "PCT_LINEAS_DEL_HITO son el % que representa esa subcategoria del costo/actividad TOTAL de ese hito.",
    "",
    "Analisis 3 (evolucion): mismo % de la hoja 2, pivoteado para comparar una misma subcategoria a",
    "traves de los 4 hitos. PCT_COSTO_* usa el gasto neto; PCT_LINEAS_* usa el N de lineas facturadas",
    "como proxy de actividad/tiempo (no hay una medida de 'dias' por subcategoria).",
    "",
    "Hojas '3_EvolucionSoles_...': mismo pivote que el Analisis 3, pero con el gasto APROXIMADO POR",
    "PACIENTE en SOLES (COSTO_MEDIA_* y COSTO_MEDIANA_*) en vez del % dentro del hito. Ambas se",
    "calculan sobre TODOS los pacientes del hito (incluye $0 en esa subcategoria si no la usaron), no",
    "solo sobre quienes gastaron. Util para comparar cuanto gasta en promedio un paciente en una",
    "subcategoria en el hito de Tratamiento de la cohorte 2016 vs. la cohorte 2017. Preferir la",
    "MEDIANA cuando el grupo es chico o hay outliers (ver calidad de datos en el README principal).",
    "",
    "Hojas '3_EvolucionDias_...': tiempo APROXIMADO POR PACIENTE dentro de cada transicion (no un",
    "total sumado entre pacientes, que mezclaba tamano del grupo con duracion real). Para cada",
    "paciente: de los dias que le tomo esa transicion completa (su propia DURACION_DIAS, ver hoja 1),",
    "cuantos tuvieron al menos 1 registro de esa subcategoria. Luego se promedia entre pacientes:",
    "  N_DIAS_MEDIA/MEDIANA_*       : dias absolutos con actividad de la subcategoria.",
    "  PCT_DIAS_HITO_MEDIA/MEDIANA_*: lo mismo, como % de la duracion total de la transicion (ej. si",
    "                                 la transicion duro 100 dias y 22 tuvieron Laboratorio, PCT=22%).",
    "Si un paciente tuvo 3 lineas de Laboratorio el mismo dia, ese dia cuenta 1 vez, no 3. El hito 2",
    "(Diagnostico) es un evento puntual (duracion 0 dias), asi que PCT_DIAS_HITO no aplica ahi (queda",
    "vacio). Los 4 hitos se renombran como transicion (p.ej. '3_Diagnostico_a_FinTratamiento') para",
    "dejar explicito el recorrido; siguen siendo los mismos 4 grupos de 1_CostoTiempo, solo con otra",
    "etiqueta.",
    "",
    "Hoja '1_CostoTiempo_PorAnioCalendario' (EXTRA, no reemplaza a 1_CostoTiempo_PorAnio): la misma",
    "hoja 1 (mismas columnas: N_PACIENTES, COSTO_NETO_MEDIA/MEDIANA, DURACION_DIAS_MEDIA/MEDIANA), pero",
    "agrupada por el ANIO CALENDARIO REAL en el que cae cada hito, no por el anio de DIAGNOSTICO de la",
    "cohorte. Un hito que dura varios anios (Tratamiento, Desenlace) ahora aporta una fila a CADA anio",
    "calendario que toca: DURACION_DIAS_MEDIA/MEDIANA es la duracion de la ventana del paciente",
    "RECORTADA a ese anio especifico (p.ej. una ventana del 2016-11-01 al 2017-03-01 aporta ~61 dias a",
    "2016 y ~59 dias a 2017, no la duracion completa en ambos), y COSTO_NETO_MEDIA/MEDIANA usa el gasto",
    "real facturado en ESE anio (no un reparto proporcional a los dias). Se rellena con 0 costo a quien",
    "'pertenece' al hito ese anio (su ventana lo toca) pero no factura nada en el, igual que hace",
    "1_CostoTiempo_PorAnio con el anio de diagnostico -- por eso N_PACIENTES aqui puede no coincidir",
    "exacto con 4_CostoPacientePorAnio (esa hoja solo cuenta a quien SI factura algo ese anio).",
    "",
    "Hojas '1_DiasHospitalizacion_...': dias de hospitalizacion por hito (episodios deduplicados por",
    "paciente + fecha ingreso + fecha alta, para no contar 2 veces el mismo internamiento por tener",
    "varias lineas de facturacion). Un episodio se asigna al hito segun su FECHA DE INGRESO, con el",
    "mismo criterio de ventanas que clasifica las lineas de costo (ver Analisis 2/3). DIAS_HOSP_MEDIA/",
    "MEDIANA se calculan sobre TODOS los pacientes del hito (incluye 0 dias si no tuvo hospitalizacion",
    "en esa ventana), igual que en 1_CostoTiempo.",
]})

# =====================================================================
# GUARDADO EN UN SOLO EXCEL
# =====================================================================
print(f"\nGuardando Excel consolidado: {SALIDA_XLSX}")
with pd.ExcelWriter(SALIDA_XLSX, engine="openpyxl") as writer:
    notas.to_excel(writer, sheet_name="0_Notas", index=False)
    tabla1_general.to_excel(writer, sheet_name="1_CostoTiempo_General", index=False)
    tabla1_por_anio.to_excel(writer, sheet_name="1_CostoTiempo_PorAnio", index=False)
    tabla1_trans_general.to_excel(writer, sheet_name="1_Transiciones_General", index=False)
    tabla1_trans_por_anio.to_excel(writer, sheet_name="1_Transiciones_PorAnio", index=False)
    tabla2_general.to_excel(writer, sheet_name="2_Desglose_General", index=False)
    tabla2_por_anio.to_excel(writer, sheet_name="2_Desglose_PorAnio", index=False)
    tabla3_general.to_excel(writer, sheet_name="3_Evolucion_General", index=False)
    tabla3_por_anio.to_excel(writer, sheet_name="3_Evolucion_PorAnio", index=False)
    tabla3_soles_general.to_excel(writer, sheet_name="3_EvolucionSoles_General", index=False)
    tabla3_soles_por_anio.to_excel(writer, sheet_name="3_EvolucionSoles_PorAnio", index=False)
    tabla3_dias_general.to_excel(writer, sheet_name="3_EvolucionDias_General", index=False)
    tabla3_dias_por_anio.to_excel(writer, sheet_name="3_EvolucionDias_PorAnio", index=False)
    tabla4.to_excel(writer, sheet_name="4_CostoPacientePorAnio", index=False)
    tabla5_general.to_excel(writer, sheet_name="1_DiasHospitalizacion_General", index=False)
    tabla5_por_anio.to_excel(writer, sheet_name="1_DiasHospitalizacion_PorAnio", index=False)
    tabla6_por_anio_cal.to_excel(writer, sheet_name="1_CostoTiempo_PorAnioCalendario", index=False)

print(f"  {len(tabla1_general)} filas en 1_CostoTiempo_General")
print(f"  {len(tabla1_por_anio)} filas en 1_CostoTiempo_PorAnio")
print(f"  {len(tabla1_trans_general)} filas en 1_Transiciones_General")
print(f"  {len(tabla1_trans_por_anio)} filas en 1_Transiciones_PorAnio")
print(f"  {len(tabla2_general)} filas en 2_Desglose_General")
print(f"  {len(tabla2_por_anio)} filas en 2_Desglose_PorAnio")
print(f"  {len(tabla3_general)} filas en 3_Evolucion_General")
print(f"  {len(tabla3_por_anio)} filas en 3_Evolucion_PorAnio")
print(f"  {len(tabla3_soles_general)} filas en 3_EvolucionSoles_General")
print(f"  {len(tabla3_soles_por_anio)} filas en 3_EvolucionSoles_PorAnio")
print(f"  {len(tabla3_dias_general)} filas en 3_EvolucionDias_General")
print(f"  {len(tabla3_dias_por_anio)} filas en 3_EvolucionDias_PorAnio")
print(f"  {len(tabla4)} filas en 4_CostoPacientePorAnio")
print(f"  {len(tabla5_general)} filas en 1_DiasHospitalizacion_General")
print(f"  {len(tabla5_por_anio)} filas en 1_DiasHospitalizacion_PorAnio")
print(f"  {len(tabla6_por_anio_cal)} filas en 1_CostoTiempo_PorAnioCalendario")

print("\nFin.")
