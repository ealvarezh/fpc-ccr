"""
FISSAL como "pagador de ultimo recurso": pacientes con prestaciones puntuales.

Hipotesis (Estela): FISSAL cubre a algunos pacientes SIS de forma integral (toda la
trayectoria), pero a otros solo paga piezas puntuales que el paciente/hogar no podia
solventar. Esas piezas serian el analogo de un gasto de bolsillo "evitado".

Este script NO prueba la hipotesis (FISSAL no dice por que paga); describe el perfil
puntual y verifica si los datos son coherentes con ella.
  Parte 1 (cohorte 24,394, HITOS_V2): segmentos, censura, mortalidad, montos.
  Parte 2 (cohorte 15,698, 2016-2022, lineas): que compra el perfil puntual.
Definicion puntual: <=2 fechas de atencion y no outlier de costo.
"""
import pandas as pd, numpy as np
from pathlib import Path
B = Path(r"C:\Users\eah\apoyoconsultoria.com\File Server - Analytics\7 Datos\Datos abiertos\fissal\01_silver")
OUT = Path(__file__).parent / "output"; OUT.mkdir(exist_ok=True)
RMV = 1130; CORTE = pd.Timestamp("2026-06-30")
pd.set_option("display.width", 220); pd.set_option("display.float_format", "{:,.2f}".format)

# ---------------- Parte 1
h = pd.read_parquet(B / "FISSAL_CCR_HITOS_V2.parquet")
h["puntual"] = (h.N_ATENCIONES <= 2) & ~h.ES_OUTLIER_COSTO
h["seg"] = np.select([h.puntual, h.FISSAL_REGULAR], ["Puntual (1-2 atenciones)", "Trayectoria regular (3+)"], "Otro (outlier de costo)")
h["seg_dias"] = (CORTE - h.PRIMERA_ATENCION).dt.days
res = h.groupby("seg").agg(pacientes=("seg", "size"), atenciones_med=("N_ATENCIONES", "median"),
    monto_mediano=("MONTO_NETO_TOTAL", "median"), monto_medio=("MONTO_NETO_TOTAL", "mean"),
    monto_p90=("MONTO_NETO_TOTAL", lambda s: s.quantile(.9)), monto_total=("MONTO_NETO_TOTAL", "sum"),
    pct_fallecido=("FALLECIDO", lambda s: 100 * s.mean()))
res["pct_pacientes"] = 100 * res.pacientes / res.pacientes.sum(); res["pct_monto"] = 100 * res.monto_total / res.monto_total.sum()
res["mediana_en_RMV"] = res.monto_mediano / RMV
print(res.T); res.to_csv(OUT / "fissal_segmentos_puntual_regular.csv", encoding="utf-8-sig")

# robustez a censura: no son solo ingresos recientes
rob = pd.DataFrame({f">= {m} meses de seguimiento": [ (h[h.seg_dias >= m*30.4].puntual.mean()*100), (h.seg_dias >= m*30.4).sum()] for m in (0, 12, 24)}, index=["% puntual", "n"]).T
print("\n", rob); rob.to_csv(OUT / "fissal_puntual_robustez_censura.csv", encoding="utf-8-sig")
por_anio = h.groupby(h.PRIMERA_ATENCION.dt.year).puntual.mean().mul(100).rename("% puntual por año de 1a atencion")
print(por_anio)

# ---------------- Parte 2: que compra el perfil puntual (cohorte 2016-2022)
l = pd.read_parquet(B / "FISSAL_CANCER_COLORRECTAL_2016_2022.parquet",
    columns=["NUM_DOC_CRYPTO", "ATE_FECATENCION", "ATE_MONTONETO"])
n = l.groupby("NUM_DOC_CRYPTO").ATE_FECATENCION.nunique()
c = pd.read_parquet(B / "FISSAL_CCR_COSTEO_HITO_SUBCATEGORIA.parquet")
c["puntual"] = c.NUM_DOC_CRYPTO.map(n) <= 2
comp = c.groupby(["puntual", "categoria_recurso_502"]).COSTO_NETO.sum().unstack(0).fillna(0)
comp = comp.div(comp.sum()) * 100; comp.columns = ["% costo regular", "% costo puntual"]
comp = comp.sort_values("% costo puntual", ascending=False)
print("\nComposicion del costo por categoria (cohorte 2016-2022):\n", comp.head(12))
comp.to_csv(OUT / "fissal_composicion_puntual_vs_regular.csv", encoding="utf-8-sig")
