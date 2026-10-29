"""
Ausentismo laboral de un paciente CCR -- enfoque bottom-up desde eventos clinicos FISSAL.

Reemplaza el "piso" de S/ 326 (tasa poblacional ENUT x 1.8 anios) por una estimacion
construida desde lo que le ocurre al paciente: cirugia, ciclos de quimioterapia y
hospitalizacion (subconjunto de referencia FISSAL, 8,016 pacientes, secc. 10.5).

Perspectivas (NO mezclar):
  A. linea base poblacional (ENUT): 0.63% de la jornada, 15.6 h/anio -> CONTEXTO, no costo CCR.
  B. costo por paciente CCR en edad laboral y ocupado (este script).
  C. costo agregado de la cohorte FISSAL = B x pacientes laboralmente activos (esperado).

Parametros clinicos (dias LABORABLES perdidos) -- supuestos, rango bajo/base/alto:
  cirugia: convalecencia posterior al alta   10 / 20 / 30
  cada sesion de quimioterapia (infusion+recuperacion) 1 / 2 / 3
  dias de hospitalizacion: se cuentan x 5/7 (laborables)
Para no doble contar, la hospitalizacion de un paciente operado se descuenta de la convalecencia.
Valor del dia = 8 h x S/ 11.55 (salario/hora ENUT 2024, ver 04_cascada_ausentismo_horas.py).
Probabilidad de estar empleado: edad < 65 y tasa de empleo = 69.5% x 95.1% (EPEN 2025).
"""
import pandas as pd, numpy as np
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).parent / "output"; OUT.mkdir(exist_ok=True)
d = pd.read_parquet(ROOT / "complementarios" / "fissal_subperfil_quimio.parquet")
col = lambda p: next(c for c in d.columns if c.startswith(p))

cirugia = d[col('TIENE_PROCEDIMIENTO_QUIR')].astype(bool)
sesiones_qt = d[col('N_SESIONES_Medicamento_oncologico')].fillna(0)
dias_hosp = d['DIAS_HOSPITALIZACION_TOTAL'].fillna(0)
edad = d['EDAD_PRIMERA_ATENCION']
HORA, JORNADA = 11.55, 8
P_EMPLEO = 0.695 * 0.951
laboral = edad.lt(65)
p_ocupado = np.where(laboral, P_EMPLEO, 0.0)

ESC = {'Bajo': (10, 1, 'low'), 'Base': (20, 2, 'base'), 'Alto': (30, 3, 'high')}
rows = []
for nom, (conv, qt, _) in ESC.items():
    hosp_lab = dias_hosp * 5/7
    conv_neta = np.where(cirugia, np.maximum(conv - hosp_lab, 0), 0)
    dias = conv_neta + qt * sesiones_qt + hosp_lab                     # dias laborables por paciente
    costo = dias * JORNADA * HORA
    rows.append(dict(escenario=nom,
        dias_lab_perdidos_prom_si_ocupado=dias.mean(),
        costo_por_paciente_ocupado=costo.mean(),
        costo_esperado_por_paciente_fissal=(costo * p_ocupado).mean(),
        n_pacientes=len(d), n_edad_laboral=int(laboral.sum()),
        pacientes_ocupados_esperados=p_ocupado.sum(),
        costo_agregado_cohorte=(costo * p_ocupado).sum(),
        pct_de_jornada_trayectoria=100 * dias.mean() / (d['DIAS_TRAYECTORIA_TOTAL'].mean() * 5/7)))
res = pd.DataFrame(rows)
# comparacion contra el piso poblacional previo
res['piso_poblacional_previo'] = 326
res['multiplo_vs_piso'] = res.costo_por_paciente_ocupado / 326
pd.set_option('display.width', 250); pd.set_option('display.float_format', '{:,.1f}'.format)
print(res.T)
print(f"\ncirugia {cirugia.mean():.1%}  con quimio {(sesiones_qt>0).mean():.1%}  sesiones QT prom (si>0) {sesiones_qt[sesiones_qt>0].mean():.1f}  dias hosp prom {dias_hosp.mean():.1f}  edad<65 {laboral.mean():.1%}")
res.to_csv(OUT / "ausentismo_bottom_up_escenarios.csv", index=False, encoding='utf-8-sig')
