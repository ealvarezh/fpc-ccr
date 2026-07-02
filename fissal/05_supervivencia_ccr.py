import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from pathlib import Path
from lifelines import KaplanMeierFitter
from lifelines.statistics import logrank_test
import gc

SILVER = Path(r"C:\Users\eah\apoyoconsultoria.com\File Server - Analytics\7 Datos\Datos abiertos\fissal\01_silver")
ARCHIVO_CCR = SILVER / "FISSAL_CANCER_COLORRECTAL_2016_2022.parquet"
ARCHIVO_PERFIL = SILVER / "FISSAL_CCR_PERFIL_PACIENTES.parquet"
SALIDA_PLOTS = SILVER.parent / "03_output" / "supervivencia"

plt.rcParams["figure.dpi"] = 150
plt.rcParams["savefig.dpi"] = 150
plt.rcParams["font.size"] = 9

# =====================================================================
# 0. CARGA DE DATOS
# =====================================================================
print("=" * 70)
print("ANALISIS DE SUPERVIVENCIA Y ENFERMEDAD AVANZADA")
print("CANCER COLORRECTAL (C18/C19/C20) — FISSAL 2016-2022")
print("=" * 70)

df_ccr = pd.read_parquet(ARCHIVO_CCR)
perfil = pd.read_parquet(ARCHIVO_PERFIL)
print(f"\nRegistros CCR: {len(df_ccr):,}")
print(f"Pacientes en perfil: {len(perfil):,}")

FECHA_CORTE = pd.Timestamp("2022-12-31")

# =====================================================================
# 1. DETECCION DE ENFERMEDAD AVANZADA / METASTASIS
# =====================================================================
print("\n" + "=" * 70)
print("1. DETECCION DE ENFERMEDAD AVANZADA (PROXIES)")
print("=" * 70)

# Estrategia: como FISSAL no registra C77/C79 ni la palabra "metastasis",
# usamos dos proxies de enfermedad avanzada:
#
#   1. CUIDADOS PALIATIVOS: confirmado, el paciente recibio atencion
#      paliativa domiciliaria. Indica enfermedad avanzada/terminal.
#
#   2. PROCEDIMIENTOS EN ORGANOS A DISTANCIA: biopsias, resecciones,
#      drenajes, laparoscopias en higado, pulmon, peritoneo, ganglios
#      o medula osea. Sugieren estudio/tratamiento de metastasis.
#      Solo contamos procedimientos, no insumos ni medicamentos.
#
# Buscamos en los archivos anuales COMPLETOS (todos los diagnosticos)
# filtrando solo pacientes CCR.

pac_ccr = set(perfil["NUM_DOC_CRYPTO"].unique())
print(f"  Pacientes CCR a buscar: {len(pac_ccr):,}")

ANIOS = range(2016, 2023)

# --- Patrones de busqueda ---
PATRON_PALIATIVO = r"(?i)\bPALIATIV"

# Sitios anatomicos (solo en procedimientos, no insumos ni medicamentos)
# Cada sitio con su patron regex
SITIOS_METASTASIS = {
    "HIGADO": r"(?i)\bHEPATECTOMIA|RESECC[IO].*HEPAT|BIOPSIA.*HEPAT|METASTASECTOMIA.*HEPAT|ABLACION.*HEPAT|QUIMIOEMBOLIZ.*HEPAT",
    "PULMON": r"(?i)\bLOBECTOMIA.*PULMON|SEGMENTECTOMIA.*PULMON|BIOPSIA.*PULMON|RESECC[IO].*PULMON|TORACOTOMIA.*BIOPSIA",
    "PERITONEO": r"(?i)\bLAPAROSCOPIA.*DIAGN.*PERITON|DRENAJE.*ABSCESO.*PERITON|RESECC[IO].*PERITON|CARCINOMATOSIS|CITORREDUCCION",
    "GANGLIO": r"(?i)\bBIOPSIA.*GANGLIO.*LINFATICO|ESCISION.*GANGLIO.*LINFATICO|LINFADENECTOMIA|VACIAMIENTO.*GANGLIONAR",
    "MEDULA_OSEA": r"(?i)\bASPIRACION.*MEDULA.*OSEA|BIOPSIA.*MEDULA.*OSEA",
}

# Palabras que indican que NO es procedimiento sino material/insumo
# (filtro adicional de seguridad)
EXCLUIR_INSUMOS = r"(?i)\bAGUJA\b|\bSET\b|\bLINEA\b|\bPROLONGADOR\b|\bTUBULADURA\b|\bOBTURADOR\b|\bSOLUCION\b.*DIALISIS|\bFILTRO\b"

# --- Buscar en cada anio ---
pac_paliativo = set()
pac_sitios = {sitio: set() for sitio in SITIOS_METASTASIS}
fechas_paliativo = {}
fechas_sitios = {sitio: {} for sitio in SITIOS_METASTASIS}

for yr in ANIOS:
    archivo = SILVER / f"FISSAL_PRESTACIONES_{yr}.parquet"
    if not archivo.exists():
        continue
    print(f"  Procesando {yr}...", end=" ")
    df_yr = pd.read_parquet(
        archivo,
        columns=["NUM_DOC_CRYPTO", "ATE_DESCCONSUMO", "ATE_TIPOCONSUMO", "ATE_FECATENCION", "ATE_CODCIE10"],
    )

    mask_ccr = df_yr["NUM_DOC_CRYPTO"].isin(pac_ccr)
    df_ccr_pac = df_yr[mask_ccr]
    n_pal = 0
    n_sit = 0

    # --- Paliativo (cualquier tipo de consumo) ---
    mask_pal = df_ccr_pac["ATE_DESCCONSUMO"].str.contains(PATRON_PALIATIVO, na=False)
    if mask_pal.any():
        pals = df_ccr_pac.loc[mask_pal]
        nuevos = set(pals["NUM_DOC_CRYPTO"]) - pac_paliativo
        pac_paliativo.update(nuevos)
        # Guardar primera fecha de paliativo por paciente
        for pid in nuevos:
            fechas_paliativo[pid] = pals.loc[pals["NUM_DOC_CRYPTO"] == pid, "ATE_FECATENCION"].min()
        n_pal = mask_pal.sum()

    # --- Sitios anatomicos (solo procedimientos) ---
    mask_proc = df_ccr_pac["ATE_TIPOCONSUMO"] == "Procedimiento"
    df_proc = df_ccr_pac[mask_proc]

    for sitio, patron in SITIOS_METASTASIS.items():
        mask_sitio = df_proc["ATE_DESCCONSUMO"].str.contains(patron, na=False)
        # Excluir insumos que pudieron colarse como procedimiento
        mask_insumo = df_proc["ATE_DESCCONSUMO"].str.contains(EXCLUIR_INSUMOS, na=False)
        mask_sitio = mask_sitio & ~mask_insumo

        if mask_sitio.any():
            hits = df_proc.loc[mask_sitio]
            nuevos = set(hits["NUM_DOC_CRYPTO"]) - pac_sitios[sitio]
            pac_sitios[sitio].update(nuevos)
            for pid in nuevos:
                fechas_sitios[sitio][pid] = hits.loc[hits["NUM_DOC_CRYPTO"] == pid, "ATE_FECATENCION"].min()
            n_sit += mask_sitio.sum()

    print(f"paliativo={n_pal}  sitios={n_sit}")
    del df_yr, df_ccr_pac
    gc.collect()

# --- Construir indicadores en el perfil ---
perfil["TUVO_PALIATIVO"] = perfil["NUM_DOC_CRYPTO"].isin(pac_paliativo)

for sitio in SITIOS_METASTASIS:
    col = f"SITIO_{sitio}"
    perfil[col] = perfil["NUM_DOC_CRYPTO"].isin(pac_sitios[sitio])

# N de sitios anatomicos afectados
cols_sitios = [f"SITIO_{s}" for s in SITIOS_METASTASIS]
perfil["N_SITIOS"] = perfil[cols_sitios].sum(axis=1)

# Clasificacion compuesta de enfermedad avanzada
def clasificar_avanzada(row):
    if row["TUVO_PALIATIVO"]:
        return "PALIATIVO"
    if row["N_SITIOS"] >= 2:
        return "MULTISITIO"
    if row["N_SITIOS"] == 1:
        return "UN_SITIO"
    return "SIN_INDICADORES"

perfil["ENFERMEDAD_AVANZADA"] = perfil.apply(clasificar_avanzada, axis=1)

# =====================================================================
# REPORTE DE HALLAZGOS
# =====================================================================
print(f"\n  --- Cuidados paliativos ---")
print(f"  Pacientes con cuidados paliativos: {len(pac_paliativo):,}")

print(f"\n  --- Procedimientos en organos a distancia ---")
sitios_presentes = []
for sitio in SITIOS_METASTASIS:
    col = f"SITIO_{sitio}"
    n_pac = perfil[col].sum()
    if n_pac > 0:
        sitios_presentes.append(sitio)
    print(f"  {sitio:<15s}: {n_pac:>5,} pacientes")

print(f"\n  --- Clasificacion de enfermedad avanzada ---")
for cat in ["PALIATIVO", "MULTISITIO", "UN_SITIO", "SIN_INDICADORES"]:
    n = (perfil["ENFERMEDAD_AVANZADA"] == cat).sum()
    print(f"  {cat:<20s}: {n:>6,} ({n/len(perfil)*100:5.1f}%)")

# --- Comparacion entre grupos ---
print(f"\n--- Perfil de los grupos de enfermedad avanzada ---")
for cat in ["PALIATIVO", "MULTISITIO", "UN_SITIO", "SIN_INDICADORES"]:
    sub = perfil[perfil["ENFERMEDAD_AVANZADA"] == cat]
    n = len(sub)
    if n == 0:
        print(f"\n  {cat} (n=0): sin pacientes")
        continue
    fallecidos = sub["FALLECIDO"].sum()
    edad = sub["EDAD_PRIMERA_ATENCION"].dropna()
    pct_fall = fallecidos / n * 100 if n > 0 else 0
    print(f"\n  {cat} (n={n:,}):")
    if len(edad) > 0:
        print(f"    Edad media 1ra atencion:  {edad.mean():.1f}")
    print(f"    Fallecidos:               {fallecidos:,} ({pct_fall:.1f}%)")
    print(f"    Cirugia:                  {sub['TUVO_CIRUGIA'].sum():,} ({sub['TUVO_CIRUGIA'].mean()*100:.1f}%)")
    print(f"    Quimioterapia:            {sub['TUVO_QUIMIOTERAPIA'].sum():,} ({sub['TUVO_QUIMIOTERAPIA'].mean()*100:.1f}%)")
    print(f"    Hospitalizacion:          {sub['TUVO_HOSPITALIZACION'].sum():,} ({sub['TUVO_HOSPITALIZACION'].mean()*100:.1f}%)")

# =====================================================================
# 2. KAPLAN-MEIER: SUPERVIVENCIA GLOBAL
# =====================================================================
print("\n" + "=" * 70)
print("2. CURVAS DE SUPERVIVENCIA KAPLAN-MEIER")
print("=" * 70)

# Kaplan-Meier usa:
#   duration = tiempo hasta evento o censura (SUPERVIVENCIA_DIAS)
#   event_observed = 1 si fallecio, 0 si censurado (FALLECIDO)
kmf = KaplanMeierFitter()

SALIDA_PLOTS.mkdir(parents=True, exist_ok=True)

# --- 2a. Supervivencia global ---
fig, ax = plt.subplots(figsize=(10, 6))
kmf.fit(
    durations=perfil["SUPERVIVENCIA_DIAS"] / 30,
    event_observed=perfil["FALLECIDO"].astype(int),
    label="Todos los pacientes",
)
kmf.plot_survival_function(ax=ax, ci_show=True, color="#2166ac", linewidth=2)

mediana = kmf.median_survival_time_
ax.axhline(y=0.5, color="gray", linestyle="--", alpha=0.4)
ax.axvline(x=mediana, color="gray", linestyle="--", alpha=0.4)
ax.text(mediana + 1, 0.52, f"Mediana: {mediana:.1f} meses", fontsize=8, color="gray")

ax.set_title("Supervivencia Global — Cancer Colorrectal (FISSAL 2016-2022)", fontsize=11, fontweight="bold")
ax.set_xlabel("Tiempo desde primera atencion (meses)")
ax.set_ylabel("Probabilidad de supervivencia")
ax.set_ylim(0, 1.05)
ax.legend(fontsize=8, loc="lower left")
ax.grid(True, alpha=0.2)
fig.tight_layout()
fig.savefig(SALIDA_PLOTS / "km_global.png")
plt.close(fig)
print(f"\n  [OK] KM global guardado")

# --- Funcion auxiliar para KM por grupos ---
def km_por_grupo(df, col_grupo, titulo, nombre_archivo, colores=None, etiquetas=None, orden=None):
    """Genera curva KM estratificada, test log-rank, y guarda PNG."""
    if orden is not None:
        grupos = [g for g in orden if g in df[col_grupo].dropna().unique()]
    else:
        grupos = sorted(df[col_grupo].dropna().unique())
    if len(grupos) < 2:
        print(f"  [!] {titulo}: solo {len(grupos)} grupo(s), se omite")
        return

    fig, ax = plt.subplots(figsize=(10, 6))
    supervivencias = {}

    for i, g in enumerate(grupos):
        mask = df[col_grupo] == g
        sub = df[mask]
        label = etiquetas.get(g, str(g)) if etiquetas else str(g)
        color = colores[i] if colores and i < len(colores) else None

        kmf_temp = KaplanMeierFitter()
        kmf_temp.fit(
            durations=sub["SUPERVIVENCIA_DIAS"] / 30,
            event_observed=sub["FALLECIDO"].astype(int),
            label=f"{label} (n={mask.sum():,})",
        )
        kmf_temp.plot_survival_function(ax=ax, ci_show=True, color=color, linewidth=2)
        supervivencias[str(g)] = kmf_temp

        med = kmf_temp.median_survival_time_
        if med != float("inf"):
            print(f"    {label}: mediana={med:.1f} meses, n={mask.sum():,}")

    # Log-rank test entre los dos primeros grupos (o todos si hay >2)
    if len(grupos) == 2:
        g0, g1 = grupos
        mask0 = df[col_grupo] == g0
        mask1 = df[col_grupo] == g1
        lr = logrank_test(
            durations_A=df.loc[mask0, "SUPERVIVENCIA_DIAS"] / 30,
            durations_B=df.loc[mask1, "SUPERVIVENCIA_DIAS"] / 30,
            event_observed_A=df.loc[mask0, "FALLECIDO"].astype(int),
            event_observed_B=df.loc[mask1, "FALLECIDO"].astype(int),
        )
        p_val = lr.p_value
        ax.text(0.98, 0.02, f"Log-rank p = {p_val:.4f}",
                transform=ax.transAxes, fontsize=8, ha="right",
                bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8))

    ax.set_title(titulo, fontsize=11, fontweight="bold")
    ax.set_xlabel("Tiempo desde primera atencion (meses)")
    ax.set_ylabel("Probabilidad de supervivencia")
    ax.set_ylim(0, 1.05)
    ax.legend(fontsize=8, loc="lower left")
    ax.grid(True, alpha=0.2)
    fig.tight_layout()
    fig.savefig(SALIDA_PLOTS / nombre_archivo)
    plt.close(fig)
    print(f"  [OK] {nombre_archivo}")


# =====================================================================
# 3. KM POR SEXO
# =====================================================================
print("\n" + "=" * 70)
print("3. SUPERVIVENCIA POR SEXO")
print("=" * 70)
km_por_grupo(
    perfil, "SEXO",
    "Supervivencia por Sexo — Cancer Colorrectal",
    "km_sexo.png",
    colores=["#d6604d", "#4393c3"],
    etiquetas={"F": "Femenino", "M": "Masculino"},
)

# =====================================================================
# 4. KM POR RANGO DE EDAD
# =====================================================================
print("\n" + "=" * 70)
print("4. SUPERVIVENCIA POR RANGO DE EDAD")
print("=" * 70)

# Chequear si RANGO_EDAD existe; si no, crearlo
if "RANGO_EDAD" not in perfil.columns:
    bins = [0, 18, 40, 50, 60, 70, 120]
    labels = ["0-17", "18-39", "40-49", "50-59", "60-69", "70+"]
    perfil["RANGO_EDAD"] = pd.cut(
        perfil["EDAD_PRIMERA_ATENCION"], bins=bins, labels=labels, right=False
    )

COLORES_EDAD = ["#a6cee3", "#1f78b4", "#b2df8a", "#33a02c", "#fb9a99", "#e31a1c"]
km_por_grupo(perfil, "RANGO_EDAD", "Supervivencia por Rango de Edad", "km_edad.png", colores=COLORES_EDAD)

# =====================================================================
# 5. KM POR CIRUGIA
# =====================================================================
print("\n" + "=" * 70)
print("5. SUPERVIVENCIA SEGUN CIRUGIA")
print("=" * 70)
km_por_grupo(
    perfil, "TUVO_CIRUGIA",
    "Supervivencia: Pacientes con vs sin Cirugia",
    "km_cirugia.png",
    colores=["#d6604d", "#4393c3"],
    etiquetas={True: "Con cirugia", False: "Sin cirugia"},
)

# =====================================================================
# 6. KM POR QUIMIOTERAPIA
# =====================================================================
print("\n" + "=" * 70)
print("6. SUPERVIVENCIA SEGUN QUIMIOTERAPIA")
print("=" * 70)
km_por_grupo(
    perfil, "TUVO_QUIMIOTERAPIA",
    "Supervivencia: Pacientes con vs sin Quimioterapia",
    "km_quimio.png",
    colores=["#d6604d", "#4393c3"],
    etiquetas={True: "Con quimioterapia", False: "Sin quimioterapia"},
)

# =====================================================================
# 7. KM POR ENFERMEDAD AVANZADA (PROXY COMPUESTO)
# =====================================================================
print("\n" + "=" * 70)
print("7. SUPERVIVENCIA SEGUN ENFERMEDAD AVANZADA")
print("=" * 70)

COLORES_AVANZADA = ["#d73027", "#fc8d59", "#fee090", "#4575b4"]
ETIQUETAS_AVANZADA = {
    "PALIATIVO": "Paliativo",
    "MULTISITIO": "Multisitio (2+)",
    "UN_SITIO": "Un sitio",
    "SIN_INDICADORES": "Sin indicadores",
}
ORDEN_AVANZADA = ["PALIATIVO", "MULTISITIO", "UN_SITIO", "SIN_INDICADORES"]
km_por_grupo(
    perfil, "ENFERMEDAD_AVANZADA",
    "Supervivencia segun Enfermedad Avanzada (proxy compuesto)",
    "km_enfermedad_avanzada.png",
    colores=COLORES_AVANZADA,
    etiquetas=ETIQUETAS_AVANZADA,
    orden=ORDEN_AVANZADA,
)

# =====================================================================
# 8. KM POR REGION (LIMA vs REGIONES)
# =====================================================================
print("\n" + "=" * 70)
print("8. SUPERVIVENCIA: LIMA vs REGIONES")
print("=" * 70)
perfil["REGION_LIMA"] = np.where(
    perfil["DEPARTAMENTO"] == "LIMA", "Lima", "Regiones"
)
km_por_grupo(
    perfil, "REGION_LIMA",
    "Supervivencia: Lima vs Regiones",
    "km_region.png",
    colores=["#4393c3", "#d6604d"],
)

# =====================================================================
# 9. KM COMPARATIVO MULTIPLE (resumen en una sola figura)
# =====================================================================
print("\n" + "=" * 70)
print("9. RESUMEN COMPARATIVO DE SUPERVIVENCIA")
print("=" * 70)

fig, axes = plt.subplots(3, 2, figsize=(14, 18))
axes = axes.flatten()

comparaciones = [
    ("SEXO", {"F": "Femenino", "M": "Masculino"}, ["#d6604d", "#4393c3"], "Por Sexo"),
    ("TUVO_CIRUGIA", {True: "Con cirugia", False: "Sin cirugia"}, ["#d6604d", "#4393c3"], "Por Cirugia"),
    ("TUVO_QUIMIOTERAPIA", {True: "Con quimio", False: "Sin quimio"}, ["#d6604d", "#4393c3"], "Por Quimioterapia"),
    ("ENFERMEDAD_AVANZADA", ETIQUETAS_AVANZADA, COLORES_AVANZADA, "Por Enf. Avanzada"),
    ("RANGO_EDAD", None, COLORES_EDAD, "Por Rango de Edad"),
    ("REGION_LIMA", None, ["#4393c3", "#d6604d"], "Lima vs Regiones"),
]

for idx, (col, etq, cols_pal, tit) in enumerate(comparaciones):
    ax = axes[idx]
    if col == "ENFERMEDAD_AVANZADA":
        grupos = [g for g in ORDEN_AVANZADA if g in perfil[col].dropna().unique()]
    else:
        grupos = sorted(perfil[col].dropna().unique())
    p_values = ""
    for j, g in enumerate(grupos):
        sub = perfil[perfil[col] == g]
        label = (etq.get(g, str(g)) if etq else str(g)) if not isinstance(g, bool) else (etq.get(g, str(g)) if etq else str(g))
        color = cols_pal[j] if j < len(cols_pal) else None
        kmf_temp = KaplanMeierFitter()
        kmf_temp.fit(
            durations=sub["SUPERVIVENCIA_DIAS"] / 30,
            event_observed=sub["FALLECIDO"].astype(int),
            label=f"{label} (n={len(sub):,})",
        )
        kmf_temp.plot_survival_function(ax=ax, ci_show=False, color=color, linewidth=2)
        med = kmf_temp.median_survival_time_
        if med != float("inf"):
            p_values += f"{label}: med={med:.0f}m  "

    if len(grupos) == 2:
        g0, g1 = grupos[:2]
        m0 = perfil[col] == g0
        m1 = perfil[col] == g1
        lr = logrank_test(
            durations_A=perfil.loc[m0, "SUPERVIVENCIA_DIAS"] / 30,
            durations_B=perfil.loc[m1, "SUPERVIVENCIA_DIAS"] / 30,
            event_observed_A=perfil.loc[m0, "FALLECIDO"].astype(int),
            event_observed_B=perfil.loc[m1, "FALLECIDO"].astype(int),
        )
        ax.set_title(f"{tit}  [log-rank p={lr.p_value:.4f}]", fontsize=10, fontweight="bold")
    else:
        ax.set_title(tit, fontsize=10, fontweight="bold")

    ax.set_xlabel("Meses desde primera atencion")
    ax.set_ylabel("Probabilidad de supervivencia")
    ax.set_ylim(0, 1.05)
    ax.legend(fontsize=7, loc="lower left")
    ax.grid(True, alpha=0.2)

fig.suptitle("Supervivencia en Cancer Colorrectal — FISSAL 2016-2022", fontsize=13, fontweight="bold")
fig.tight_layout(rect=[0, 0, 1, 0.97])
fig.savefig(SALIDA_PLOTS / "km_resumen_comparativo.png")
plt.close(fig)
print(f"  [OK] km_resumen_comparativo.png")

# =====================================================================
# 10. TABLA DE MEDIANAS DE SUPERVIVENCIA
# =====================================================================
print("\n" + "=" * 70)
print("10. RESUMEN DE MEDIANAS DE SUPERVIVENCIA")
print("=" * 70)

def mediana_grupo(df, col):
    """Calcula mediana de supervivencia por grupo usando lifelines."""
    resultados = []
    for g in sorted(df[col].dropna().unique()):
        sub = df[df[col] == g]
        kmf_temp = KaplanMeierFitter()
        kmf_temp.fit(
            durations=sub["SUPERVIVENCIA_DIAS"] / 30,
            event_observed=sub["FALLECIDO"].astype(int),
        )
        med = kmf_temp.median_survival_time_
        resultados.append({
            "grupo": str(g),
            "n": len(sub),
            "n_fallecidos": sub["FALLECIDO"].sum(),
            "mediana_meses": med if med != float("inf") else np.nan,
        })
    return pd.DataFrame(resultados)

print(f"\n{'=' * 60}")
print("MEDIANAS DE SUPERVIVENCIA POR SUBGRUPO")
print(f"{'=' * 60}")

for col, nombre in [
    ("SEXO", "Sexo"),
    ("RANGO_EDAD", "Rango de edad"),
    ("TUVO_CIRUGIA", "Cirugia"),
    ("TUVO_QUIMIOTERAPIA", "Quimioterapia"),
    ("ENFERMEDAD_AVANZADA", "Enfermedad avanzada"),
    ("REGION_LIMA", "Region"),
]:
    print(f"\n--- {nombre} ---")
    res = mediana_grupo(perfil, col)
    for _, row in res.iterrows():
        med_str = f"{row['mediana_meses']:.1f}" if not np.isnan(row["mediana_meses"]) else "N/A"
        print(f"  {row['grupo']:>20s}: n={row['n']:>6,}  fallecidos={row['n_fallecidos']:>5,}  mediana={med_str:>7s} meses")

# =====================================================================
# 11. GUARDAR PERFIL AMPLIADO
# =====================================================================
perfil_out = SILVER / "FISSAL_CCR_PERFIL_PACIENTES_AMPLIADO.parquet"
cols_guardar = [c for c in perfil.columns if c not in ("CATEGORIAS",)]
perfil[cols_guardar].to_parquet(perfil_out, index=False)
print(f"\n{'=' * 70}")
print(f"Guardado perfil ampliado ({len(perfil):,} pacientes) en:")
print(f"  {perfil_out}")
print(f"Graficos de supervivencia en:")
print(f"  {SALIDA_PLOTS}")
print("\nFin del analisis de supervivencia.")
