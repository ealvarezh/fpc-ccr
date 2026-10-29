"""
Gasto de bolsillo en salud -- ENAHO 2025, modulo 400 (Salud).

Que mide: monto pagado POR EL HOGAR (p4151_xx==1) por servicio de salud utilizado
(p414_xx==1), monto total p416xx (soles). No identifica cancer: lo mas cercano es
p401 (enfermedad cronica). Por eso se presenta como PISO/referencia, no como
gasto de bolsillo de un paciente CCR.

Periodos de referencia: items 01-05 = 4 semanas (x13 anual); 06-12 = 3 meses (x4);
13-16 = 12 meses (x1). Se usan solo rubros relevantes a un proceso oncologico:
 ambulatorio: 01 consulta, 02 medicinas, 03 analisis, 04 imagenes, 05 otro examen, 12 otros
 hospitalizacion: 13 ; cirugia: 14
"""
import pandas as pd, numpy as np
from pathlib import Path

P = Path(r"C:\Users\eah\apoyoconsultoria.com\File Server - Analytics\7 Datos\ENAHO\2025\2025Salud.dta")
OUT = Path(__file__).parent / "output"; OUT.mkdir(exist_ok=True)

ITEMS = {1:('consulta',13), 2:('medicinas',13), 3:('analisis',13), 4:('imagenes',13),
         5:('otro_examen',13), 12:('otros_gastos',4), 13:('hospitalizacion',1), 14:('cirugia',1)}
AMB = ['consulta','medicinas','analisis','imagenes','otro_examen','otros_gastos']

cols = ['conglome','vivienda','hogar','codperso','p401','p400a3','mes','factor07','p4191','p4192','p4193','p4194','p4195']
for i in ITEMS: cols += [f'p414_{i:02d}', f'p4151_{i:02d}', f'p416{i:02d}']
d = pd.read_stata(P, columns=cols, convert_categoricals=False)
d = d[d.factor07.notna()].copy()
d['edad'] = 2025 - d.p400a3
d['cronico'] = d.p401 == 1
for c in ['p4191','p4192','p4193','p4194','p4195']:
    d[c] = d[c].notna() & (d[c].astype(str).str.strip().isin(['1','1.0']))
d['seguro'] = np.select([d.p4191|d.p4194, d.p4192|d.p4193, d.p4195], ['EsSalud/FFAA','Privado/EPS','SIS'], 'Sin seguro')

for i,(nm,fa) in ITEMS.items():
    paid = (d[f'p414_{i:02d}']==1) & (d[f'p4151_{i:02d}']==1)
    d[nm] = np.where(paid, d[f'p416{i:02d}'].fillna(0), 0.0) * fa   # soles anualizados
d['amb_anual'] = d[AMB].sum(axis=1)
d['hosp_cir'] = d.hospitalizacion + d.cirugia
d['total_anual'] = d.amb_anual + d.hosp_cir
d['uso_hosp_cir'] = ((d.p414_13==1)|(d.p414_14==1))
d['paga_hosp_cir'] = d.hosp_cir > 0

def wmean(x, w): 
    m = x.notna(); return np.average(x[m], weights=w[m]) if m.any() else np.nan
def wq(x, w, q):
    o = np.argsort(x.values); xs = x.values[o]; cw = np.cumsum(w.values[o]); return xs[np.searchsorted(cw, q*cw[-1])]

pops = {
 'Adultos 40+ (todos)': (d.edad>=40),
 'Adultos 40+ con enfermedad cronica': (d.edad>=40)&d.cronico,
 'Adultos 40+ cronicos, con algun gasto de bolsillo': (d.edad>=40)&d.cronico&(d.total_anual>0),
 'Adultos 40+ con hospitalizacion/cirugia (12m)': (d.edad>=40)&d.uso_hosp_cir,
 'Adultos 40+ con hosp/cirugia pagada por hogar': (d.edad>=40)&d.paga_hosp_cir,
 'Hosp/cirugia pagada por hogar, SIS/sin seguro': (d.edad>=40)&d.paga_hosp_cir&d.seguro.isin(['SIS','Sin seguro']),
}
rows=[]
for k,m in pops.items():
    s=d[m]; w=s.factor07
    rows.append(dict(poblacion=k, n_muestra=len(s), n_expandido=w.sum(),
        amb_anual_media=wmean(s.amb_anual,w), hosp_cir_media=wmean(s.hosp_cir,w),
        total_anual_media=wmean(s.total_anual,w), total_anual_mediana=wq(s.total_anual,w,.5),
        total_anual_p75=wq(s.total_anual,w,.75), pct_con_gasto=100*w[s.total_anual>0].sum()/w.sum()))
res = pd.DataFrame(rows); pd.set_option('display.width',250); pd.set_option('display.float_format','{:,.1f}'.format)
print(res.to_string(index=False)); res.to_csv(OUT/'enaho_gasto_bolsillo_resumen.csv', index=False, encoding='utf-8-sig')

# por rubro, cronicos 40+
s=d[(d.edad>=40)&d.cronico]; det=pd.DataFrame({r:[wmean(s[r],s.factor07)] for r in AMB+['hospitalizacion','cirugia']}).T
det.columns=['media_anual_soles']; print(det); det.to_csv(OUT/'enaho_gasto_bolsillo_rubros_cronicos40.csv', encoding='utf-8-sig')
print(d.seguro.value_counts())
