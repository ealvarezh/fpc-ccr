"""Exploracion: gasto de bolsillo en salud, ENAHO 2025 modulo 400 (Salud)."""
import pandas as pd, numpy as np
from pathlib import Path
P = Path(r"C:\Users\eah\apoyoconsultoria.com\File Server - Analytics\7 Datos\ENAHO\2025\2025Salud.dta")
cols = ['conglome','vivienda','hogar','codperso','dominio','p401','p400a3','factor07']
cols += [f'p4151_{i:02d}' for i in range(1,17)] + [f'p416{i:02d}' for i in range(1,17)]
cols += [f'p414_{i:02d}' for i in range(1,17)] + ['p4191','p4192','p4193','p4194','p4195']
d = pd.read_stata(P, columns=cols, convert_categoricals=False)
print(d.shape)
print(d.p401.value_counts(dropna=False).head())
print(d[['p4151_01','p414_01','p41601','p4151_13','p41613','p41614']].describe().T)
print(d.p4151_01.value_counts(dropna=False))
print(d.p4151_13.value_counts(dropna=False)); print(d.p414_13.value_counts(dropna=False))
print(d[d.p41613>0][['p41613','p4151_13']].describe())
