"""
Ausentismo del paciente CCR -- ruta por DURACION real del tratamiento (alternativa a 06, por eventos).

Para cada paciente del subconjunto de referencia (8,016):
  duracion = FECHA_FIN_INTERVENCION - FECHA_INICIO_INTERVENCION (dias calendario, observado en FISSAL)
  dias fuera del trabajo (calendario) = max( min(f x duracion, TOPE) , dias de hospitalizacion )
  dias laborables perdidos = dias fuera x 5/7 ; valor = dias laborables x 8 h x S/ 11.55
Escenarios por la fraccion f del periodo de tratamiento en que el paciente esta fuera:
  bajo 0.25 / base 0.50 / alto 0.75. TOPE = 365 dias (la literatura mide 91 a 423 dias hasta volver a trabajar).
Calibracion: con f = 0.50 la mediana en pacientes con cirugia o quimioterapia es ~89 dias, cercana a los
91 dias (RIC 14-183) de la cohorte australiana de cancer colorrectal (BMC Public Health 2014).
"""
import pandas as pd, numpy as np
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]; OUT = Path(__file__).parent / "output"
d = pd.read_parquet(ROOT/"complementarios"/"fissal_subperfil_quimio.parquet")
col = lambda p: next(c for c in d.columns if c.startswith(p))
dur = (d.FECHA_FIN_INTERVENCION - d.FECHA_INICIO_INTERVENCION).dt.days.clip(lower=0)
hosp = d.DIAS_HOSPITALIZACION_TOTAL.fillna(0)
cir = d[col('TIENE_PROCEDIMIENTO_QUIR')].astype(bool); qt = d[col('N_SESIONES_Medicamento_oncologico')].fillna(0) >= 2
trat = cir | qt
VALOR_DIA = 8 * 11.55; TOPE = 365
laboral = d.EDAD_PRIMERA_ATENCION.lt(65); P_EMPLEO = 0.695 * 0.951
p_ocup = np.where(laboral, P_EMPLEO, 0.0)
rows = []
for nom, f in {"Bajo": .25, "Base": .50, "Alto": .75}.items():
    off = np.maximum(np.minimum(f * dur, TOPE), hosp)          # dias calendario fuera
    lab = off * 5/7; costo = lab * VALOR_DIA
    rows.append(dict(escenario=nom, fraccion=f,
        dias_fuera_mediana_tratados=off[trat].median(), dias_fuera_media_todos=off.mean(),
        dias_laborables_media_todos=lab.mean(), costo_medio_por_paciente_que_trabaja=costo.mean(),
        costo_medio_tratados=costo[trat].mean(),
        pacientes_ocupados_esperados=p_ocup.sum(), costo_agregado_cohorte=(costo*p_ocup).sum()))
r = pd.DataFrame(rows); pd.set_option("display.width",220); pd.set_option("display.float_format","{:,.1f}".format)
print(r.T); print(f"\ntratados (cirugia o quimio>=2): {trat.sum():,} ({trat.mean():.1%}); duracion mediana {dur.median():.0f} d, sin duracion (0 d) {(dur==0).mean():.1%}")
r.to_csv(OUT/"ausentismo_por_duracion_escenarios.csv", index=False, encoding="utf-8-sig")
