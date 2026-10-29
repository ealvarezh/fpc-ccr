"""
Variante del gasto catastrofico: el gasto de bolsillo se mide contra el INGRESO neto del hogar
(inghog2d, Sumaria ENAHO 2025) en vez de contra el gasto total o la capacidad de pago (gasto - alimentos).
Quintiles: por gasto per capita (igual que 05_no_medico_y_catastrofico.py) para poder comparar.
Hogares con ingreso <= 0 se excluyen (se reporta cuantos).
"""
import pandas as pd, numpy as np
from pathlib import Path
E = Path(r"C:\Users\eah\apoyoconsultoria.com\File Server - Analytics\7 Datos\ENAHO\2025")
OUT = Path(__file__).parent / "output"
s = pd.read_stata(E/"sumaria-2025.dta", columns=["gashog2d","inghog2d","mieperho","factor07"], convert_categoricals=False)
s = s[s.gashog2d>0].copy()
n0 = len(s); s_ing = s[s.inghog2d>0].copy()
print(f"Hogares: {n0:,}; con ingreso <= 0 (excluidos): {n0-len(s_ing):,} ({(n0-len(s_ing))/n0:.1%})")
s_ing["gpc_m"] = s_ing.gashog2d / s_ing.mieperho / 12
w = s_ing.factor07 * s_ing.mieperho
o = np.argsort(s_ing.gpc_m.values); cw = np.cumsum(w.values[o]) / w.sum()
q = np.empty(len(s_ing), int); q[o] = np.minimum((cw*5).astype(int), 4) + 1; s_ing["quintil"] = q
rows=[]
for gb in (585, 4023):
    for qq in range(6):
        d = s_ing if qq==0 else s_ing[s_ing.quintil==qq]; ww = d.factor07
        r = {"gasto_bolsillo":gb, "quintil":"Total" if qq==0 else f"Q{qq}"}
        for t in (.10,.25,.40): r[f"ing>{int(t*100)}%"] = 100*ww[(gb/d.inghog2d)>t].sum()/ww.sum()
        rows.append(r)
t = pd.DataFrame(rows); t.to_csv(OUT/"catastrofico_con_ingresos.csv", index=False, encoding="utf-8-sig")
pd.set_option("display.float_format","{:,.0f}".format); pd.set_option("display.width",200)
for gb in (585,4023): print(f"\nGasto de bolsillo anual S/ {gb}\n", t[t.gasto_bolsillo==gb].drop(columns="gasto_bolsillo").to_string(index=False))
# comparacion con la version anterior (gasto total y capacidad de pago)
c = pd.read_csv(OUT/"catastrofico_enaho_escenarios.csv"); c = c[c.gasto_bolsillo==4023][["quintil","cat25","cat40_ctp"]]
print("\nComparacion con la version anterior (S/ 4,023):\n", c.merge(t[t.gasto_bolsillo==4023][["quintil","ing>25%","ing>40%"]], on="quintil").rename(columns={"cat25":"gasto>25%","cat40_ctp":"CTP>=40%"}).to_string(index=False))
