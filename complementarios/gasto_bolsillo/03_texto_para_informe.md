## Gasto de bolsillo y ausentismo laboral: texto propuesto (reemplaza el cálculo de "piso S/ 326")

### Gasto de bolsillo (ENAHO 2025, módulo 400 Salud)

**Fuente y definición.** Monto pagado directamente por el hogar (p4151_xx = 1, monto p416xx) por servicios de salud efectivamente usados (p414_xx = 1), anualizado según el período de referencia de cada rubro (4 semanas ×13; 3 meses ×4; 12 meses ×1). Población: adultos de 40+ años, expandida con `factor07`. Script: `gasto_bolsillo/02_gasto_bolsillo_enaho.py`.

**Limitación central.** La ENAHO no identifica cáncer; lo más cercano es "padece enfermedad crónica" (p401). Las cifras describen a un adulto con enfermedad crónica o con hospitalización/cirugía, no a un paciente CCR, por lo que son una referencia de magnitud y no el gasto de bolsillo real del CCR. No incluye transporte ni alojamiento.

| Escenario | Población ENAHO | Gasto anual por persona (S/) |
|---|---|---|
| Bajo | Adultos 40+ con enfermedad crónica (promedio, incluye ceros) | 585 |
| Base | Adultos 40+ cuyo hogar pagó hospitalización o cirugía (12 m): ambulatorio 1,452 + hosp/cirugía 2,571 | 4,023 (mediana 2,300) |
| Alto | Mismo grupo, percentil 75 | 5,320 |

Equivale, en el escenario base, a ~84% del costo mediano que FISSAL cubre por paciente (S/ 4,802). Con la duración mediana de trayectoria (1.8 años) el escenario base sube a ~S/ 7,200.

### Ausentismo laboral por licencias: dos lecturas que no deben mezclarse

1. **Línea base poblacional (ENUT 2024).** 0.63 de cada 100 horas de la jornada normal de un trabajador dependiente se pierden por salud: 15.6 h/año (≈ 2 días de 8 horas), S/ 181/año. Es una tasa de **toda la población trabajadora**, que no está asociada a cáncer. Es contexto, no costo del CCR.
2. **Costo del paciente CCR (bottom-up).** Se construye desde los eventos clínicos de la cohorte FISSAL (8,016 pacientes): cirugía (49.8%), sesiones de quimioterapia (40.2% con quimio; 4.7 sesiones promedio entre quienes la reciben) y días de hospitalización (9.6 promedio). Supuestos en días laborables: convalecencia post-cirugía 10/20/30; 1/2/3 días por sesión de quimio; hospitalización ×5/7, descontada de la convalecencia para no duplicar. Valor del día: 8 h × S/ 11.55. Script: `ausentismo_discapacidad/06_ausentismo_bottom_up_paciente_ccr.py`.

| Escenario | Días laborables perdidos | Costo por paciente ocupado (S/) | Veces el piso previo (S/ 326) |
|---|---|---|---|
| Bajo | 10.7 | 991 | 3.0 |
| Base | 16.4 | 1,520 | 4.7 |
| Alto | 22.8 | 2,109 | 6.5 |

**Costo esperado en la cohorte FISSAL.** Solo el 60.8% de los pacientes tiene menos de 65 años y se aplica la tasa de empleo de 66.1% (actividad 69.5% × empleo 95.1%): ≈ 3,221 pacientes ocupados esperados, y un costo agregado de S/ 3.3 M (bajo), **S/ 5.0 M (base)** y S/ 6.9 M (alto) para la cohorte. No es una cifra nacional: no incluye CCR atendido fuera de FISSAL.

**Limitaciones.** Los días por evento son supuestos clínicos, no mediciones peruanas. No se registra ausentismo por consultas, exámenes o radioterapia, ni informalidad (el ingreso perdido de un independiente es probablemente mayor). Las sesiones de quimioterapia provienen de registros de prestación y pueden diferir de ciclos clínicos. No se incluye el tiempo del cuidador (ver sección de cuidador informal), que se suma aparte.
