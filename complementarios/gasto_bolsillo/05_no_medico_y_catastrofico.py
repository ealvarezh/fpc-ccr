"""
Recalculo de gasto de bolsillo con la investigacion extra (investigacion_extra.md):
  Parte A  Cuantos pacientes FISSAL se atienden fuera de su region y que costo NO MEDICO
           (transporte, alojamiento, alimentacion) implicaria -- parametros Robles 2023 y Semaforo Oncologico.
  Parte B  Gasto catastrofico: ENAHO 2025 Sumaria como DENOMINADOR (capacidad de pago por quintil),
           con montos de gasto de bolsillo de los escenarios como NUMERADOR.
Cohorte: FISSAL CCR 2016-2022 (lineas), unica con IPRESS por linea. ENAHO: sumaria-2025.
Limites: IPRESS->departamento mapeado a mano para los 33 establecimientos mas frecuentes.
"""
import pandas as pd, numpy as np
from pathlib import Path
B = Path(r"C:\Users\eah\apoyoconsultoria.com\File Server - Analytics\7 Datos\Datos abiertos\fissal\01_silver")
E = Path(r"C:\Users\eah\apoyoconsultoria.com\File Server - Analytics\7 Datos\ENAHO\2025")
OUT = Path(__file__).parent / "output"; OUT.mkdir(exist_ok=True)
pd.set_option("display.width", 220); pd.set_option("display.float_format", "{:,.1f}".format)

# ---- parametros (Robles 2023: US$69.65/semana radioterapia, TC 3.80; Semaforo Oncologico/RPP 2023)
DIA_ASIST = 69.65 * 3.80 / 5          # S/ por dia de asistencia ambulatoria (5 sesiones/sem)
VIAJE_INTER = 410                     # S/ por viaje interregional: pasaje ~270 + alojamiento ~80 + comida ~60

LIMA = "LIMA_CALLAO"
IPRESS_DEPTO = {6210:LIMA,6207:LIMA,6206:LIMA,7633:LIMA,5987:LIMA,6218:LIMA,5946:LIMA,6211:LIMA,6219:LIMA,7634:LIMA,
  7639:LIMA,23159:LIMA,5617:LIMA, 7277:"LA LIBERTAD",5195:"LA LIBERTAD", 11470:"LAMBAYEQUE",4317:"LAMBAYEQUE",
  7397:"AREQUIPA",1232:"AREQUIPA",1231:"AREQUIPA", 27857:"JUNIN",753:"JUNIN", 3543:"AYACUCHO",2289:"CUSCO",2305:"CUSCO",
  2864:"TACNA",3358:"ICA",7686:"CAJAMARCA",2084:"PIURA",754:"HUANUCO",6918:"SAN MARTIN"}

l = pd.read_parquet(B / "FISSAL_CANCER_COLORRECTAL_2016_2022.parquet",
    columns=["NUM_DOC_CRYPTO","ATE_IDEESS","DEPARTAMENTO_PAC","ATE_FECATENCION","TIPO_ATENC"])
l["depto_ipress"] = l.ATE_IDEESS.map(IPRESS_DEPTO)
l["depto_res"] = l.DEPARTAMENTO_PAC.str.upper().replace({"LIMA":LIMA,"CALLAO":LIMA})
cob = l.depto_ipress.notna().mean(); print(f"Lineas con IPRESS mapeado: {cob:.1%}")

# IPRESS principal por paciente (la de mas dias distintos de atencion)
dias = l.dropna(subset=["depto_ipress"]).drop_duplicates(["NUM_DOC_CRYPTO","ATE_FECATENCION","ATE_IDEESS"])
main = dias.groupby(["NUM_DOC_CRYPTO","depto_ipress"]).size().reset_index(name="n").sort_values("n",ascending=False).drop_duplicates("NUM_DOC_CRYPTO")
res = l.drop_duplicates("NUM_DOC_CRYPTO").set_index("NUM_DOC_CRYPTO").depto_res
p = main.set_index("NUM_DOC_CRYPTO").join(res)
p["fuera_region"] = p.depto_ipress != p.depto_res
print(f"Pacientes con IPRESS principal mapeado: {len(p):,} de {l.NUM_DOC_CRYPTO.nunique():,}")
print(f"% que se atiende fuera de su departamento: {p.fuera_region.mean():.1%}")
print("% que reside fuera de Lima/Callao y se atiende en Lima/Callao:",
      f"{((p.depto_ipress==LIMA)&(p.depto_res!=LIMA)).mean():.1%}")
print(p.groupby("depto_res").fuera_region.agg(["size","mean"]).sort_values("size",ascending=False).head(10))

# dias ambulatorios y meses con atencion por paciente
amb = l[l.TIPO_ATENC.str.upper().str.startswith("AMBUL", na=False)].drop_duplicates(["NUM_DOC_CRYPTO","ATE_FECATENCION"])
d_amb = amb.groupby("NUM_DOC_CRYPTO").size().rename("dias_amb")
meses = l.assign(m=l.ATE_FECATENCION.dt.to_period("M")).drop_duplicates(["NUM_DOC_CRYPTO","m"]).groupby("NUM_DOC_CRYPTO").size().rename("meses")
p = p.join(d_amb).join(meses); p[["dias_amb","meses"]] = p[["dias_amb","meses"]].fillna(0)
# solo pacientes con trayectoria (>=3 dias) para no inflar con 1 visita
p["costo_local"] = p.dias_amb * DIA_ASIST
p["costo_inter"] = np.where(p.fuera_region, p.meses * VIAJE_INTER, 0.0)
p["nm_A"] = p.costo_local                 # solo costo por dia de asistencia (Robles)
p["nm_B"] = p.costo_local + p.costo_inter # + traslado interregional (Semaforo)
reg = p[p.meses >= 2]
sm = pd.DataFrame({"n":[len(reg)]*2, "escenario":["A: Robles (dia de asistencia)","B: A + viajes interregionales (Semaforo)"],
    "mediana":[reg.nm_A.median(), reg.nm_B.median()], "media":[reg.nm_A.mean(), reg.nm_B.mean()],
    "p90":[reg.nm_A.quantile(.9), reg.nm_B.quantile(.9)]})
print("\nCosto NO MEDICO por paciente (solo pacientes con >=2 meses de atencion):\n", sm)
print("Fuera de region (con >=2 meses): ", f"{reg.fuera_region.mean():.1%}", "| costo B mediano fuera de region:", f"S/ {reg[reg.fuera_region].nm_B.median():,.0f}")
sm.to_csv(OUT/"no_medico_escenarios.csv", index=False, encoding="utf-8-sig")
p.reset_index().to_csv(OUT/"no_medico_paciente.csv", index=False, encoding="utf-8-sig")

# ---------------- Parte B: gasto catastrofico con ENAHO como denominador
s = pd.read_stata(E/"sumaria-2025.dta", columns=["gashog2d","gru11hd","mieperho","factor07","pobreza","linea"], convert_categoricals=False)
s = s[s.gashog2d>0].copy()
s["gpc_m"] = s.gashog2d / s.mieperho / 12
s["ctp"] = (s.gashog2d - s.gru11hd).clip(lower=1)           # variante simple de Xu: gasto - gasto en alimentos
w = s.factor07 * s.mieperho                                     # ponderar por personas para quintiles de poblacion
o = np.argsort(s.gpc_m.values); cw = np.cumsum(w.values[o]) / w.sum()
q = np.empty(len(s), int); q[o] = np.minimum((cw*5).astype(int), 4) + 1; s["quintil"] = q
esc = {"ENAHO cronico (S/ 585)":585, "Medico+hosp ENAHO (S/ 4,023)":4023,
       "Base + no medico A (mediana)":4023+reg.nm_A.median(), "Base + no medico B (mediana)":4023+reg.nm_B.median()}
rows=[]
for nom, gb in esc.items():
    for qq in [0,1,2,3,4,5]:
        d = s if qq==0 else s[s.quintil==qq]; ww = d.factor07
        r = dict(escenario=nom, gasto_bolsillo=gb, quintil="Total" if qq==0 else f"Q{qq}",
                 cat10=100*ww[(gb/d.gashog2d)>.10].sum()/ww.sum(), cat25=100*ww[(gb/d.gashog2d)>.25].sum()/ww.sum(),
                 cat40_ctp=100*ww[(gb/d.ctp)>=.40].sum()/ww.sum())
        rows.append(r)
cat = pd.DataFrame(rows); print("\n% de hogares ENAHO que serian catastroficos si enfrentaran ese gasto anual:\n")
print(cat.pivot(index="quintil", columns="escenario", values="cat25").round(0).rename_axis("cat>25% gasto total"))
print(cat.pivot(index="quintil", columns="escenario", values="cat40_ctp").round(0).rename_axis("cat>=40% CTP (Xu simple)"))
cat.to_csv(OUT/"catastrofico_enaho_escenarios.csv", index=False, encoding="utf-8-sig")
