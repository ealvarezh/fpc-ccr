# Hitos del Paciente — Cancer Colorrectal (FISSAL 2016-2022)

**Objetivo:** reconstruir la trayectoria clinica del paciente de CCR en 4 hitos
(Despistaje → Diagnostico → Tratamiento → Desenlace) para poder comparar
costos, demografia, duracion, hospitalizacion y adherencia entre cada etapa.

---

## Pipeline

```
01_silver/FISSAL_CANCER_COLORRECTAL_2016_2022.parquet   (data ya filtrada a C18/19/20)
01_silver/FISSAL_CCR_PERFIL_PACIENTES_AMPLIADO.parquet  (de 03_perfil + 05_supervivencia)
01_silver/FISSAL_PRESTACIONES_YYYY.parquet              (data COMPLETA, todos los CIE10, 2016-2022)
    │
    ▼ 01_construir_hitos.py
01_silver/FISSAL_CCR_HITOS_PACIENTE.parquet   (1 fila por paciente, ancha)
01_silver/FISSAL_CCR_HITOS_EVENTOS.parquet    (1 fila por paciente x hito, larga — para graficos)
    │
    ├──► 02_analisis_hitos.py     ──► Reporte por hito: embudo, demografia, costos,
    │                                  duracion, hospitalizacion, adherencia
    │
    ├──► 03_analisis_tiempos.py   ──► Reporte transversal: tiempos entre TODOS los
    │                                  hitos juntos, comparados por sexo y edad
    │
    └──► 04_exportar_powerbi.py   ──► 03_output/hitos_paciente/*.csv listos para Power BI
```

Ejecutar en orden: `01_construir_hitos.py` -> `02_analisis_hitos.py` -> `03_analisis_tiempos.py`
-> (opcional) `04_exportar_powerbi.py`.

---

## Los 4 hitos

### 1. Despistaje / Deteccion

El filtro C18/19/20 (`02_cancer_colorrectal.py`) solo captura registros que
YA estan codificados como cancer colorrectal. No existe una "cita de
descarte" explicita en FISSAL. Para reconstruir el trayecto de sospecha que
llevo al diagnostico, este script busca en la **data completa** (todos los
CIE10, `FISSAL_PRESTACIONES_YYYY.parquet`) los registros de cada paciente CCR
**anteriores** a su primera atencion codificada como CCR (`PRIMERA_ATENCION`),
clasificandolos en:

| Categoria | Patron |
|-----------|--------|
| `BIOPSIA` | `BIOPSI\|ANATOMOPATOLOG` |
| `ENDOSCOPIA` | `COLONOSCOP\|ENDOSCOP\|RECTOSCOP\|SIGMOIDOSCOP` |
| `IMAGEN` | `TOMOGRAF\|RESONAN\|ECOGRAF\|GAMMAGRAF\|PET-?SCAN\|RADIOGRAF` |
| `LABORATORIO_MARCADOR` | `CEA\|ANTIGEN.*CARCINO\|SANGRE.*OCULTA` |

**Hallazgo clave:** solo **6.6%** de los pacientes CCR tienen un evento de
despistaje detectable en FISSAL antes de su diagnostico. El **93.4%** aparece
en FISSAL por primera vez ya con el diagnostico puesto. Esto casi seguro
**no significa que no se hicieron examenes previos** — significa que esos
examenes probablemente ocurrieron en otro subsistema (consulta particular,
EsSalud, MINSA sin cobertura FISSAL) antes de que el caso fuera derivado a
FISSAL, que cubre especificamente enfermedades de alto costo. Interpretar
`TUVO_DESPISTAJE_PREVIO=False` como "no tuvo despistaje" seria incorrecto;
lo correcto es "no hay rastro de despistaje **dentro de FISSAL**".

Variables clave: `FECHA_PRIMER_DESPISTAJE`, `TIPO_DESPISTAJE`,
`DIAS_DESPISTAJE_A_DIAGNOSTICO`, `N_REGISTROS_PRE_DIAGNOSTICO`,
`COSTO_NETO_PRE_DIAGNOSTICO`, `FECHA_PRIMER_CONTACTO_SISTEMA`.

### 2. Diagnostico

`FECHA_DIAGNOSTICO` = primera atencion con CIE-10 C18/19/20 (ya calculada
como `PRIMERA_ATENCION` en `03_perfil_pacientes_ccr.py`). Se agrega el tipo
de atencion de ingreso (`TIPO_ATENCION_DIAGNOSTICO`: AMBULATORIO / EMERGENCIA
/ HOSPITALIZACIÓN) como proxy de gravedad al momento del diagnostico, la
IPRESS donde se diagnostica y el codigo CIE-10 especifico (C18 colon / C19
union rectosigmoidea / C20 recto).

### 3. Tratamiento

Se identifican episodios de 3 modalidades por paciente (mismo patron de
`03_analisis_ccr.py`, pero cada una con su propia fecha de inicio/fin,
numero de sesiones y costo): `CIRUGIA`, `QUIMIOTERAPIA` (procedimiento +
medicamento), `RADIOTERAPIA`. De ahi se derivan:

- `SECUENCIA_TRATAMIENTO`: orden cronologico de modalidades (p.ej.
  `CIRUGIA > QUIMIOTERAPIA` = adyuvante, `QUIMIOTERAPIA > CIRUGIA` =
  neoadyuvante).
- `DIAS_DIAGNOSTICO_A_TRATAMIENTO`: tiempo hasta el primer tratamiento
  detectado — indicador clave de oportunidad de atencion.
- `N_HOSPITALIZACIONES` / `DIAS_HOSPITALIZACION_TOTAL`: hospitalizaciones
  ocurridas durante todo el seguimiento del paciente.
- `N_BRECHAS_TRATAMIENTO` / `TUVO_BRECHA_ADHERENCIA` / `BRECHA_MAX_DIAS`:
  proxy de inasistencia. FISSAL no registra citas programadas vs. citas
  perdidas, asi que se aproxima contando vacios > 45 dias entre atenciones
  **dentro de la ventana de tratamiento activo** (45d porque los esquemas de
  quimio tipicos ciclan cada 14-21 dias; un vacio de 45+ dias duplica el
  ciclo mas largo esperado).
- `COSTO_NETO_TRATAMIENTO_TOTAL`: todo lo facturado (no solo cirugia/quimio/
  radio, tambien labs, medicamentos de soporte, hospitalizacion) dentro de
  la ventana de tratamiento.

**Hallazgo clave:** el **68.1%** de los pacientes CCR no tiene ninguna de
las 3 modalidades detectada por estos patrones. Es coherente con la
limitacion ya documentada en el README principal (los patrones de cirugia/
quimio son aproximaciones por texto), pero conviene revisarlo — puede haber
codigos de procedimiento sin descripcion reconocible, o pacientes que solo
reciben manejo sintomatico/paliativo sin quimio/cirugia formal.

### 4. Desenlace

FISSAL **no tiene un campo de "alta" o "recuperacion"**. Solo se sabe con
certeza si el paciente fallecio (`FEC_FALLECIMIENTO`) o si recibio cuidados
paliativos (`TUVO_PALIATIVO`, proxy de enfermedad avanzada calculado en
`05_supervivencia_ccr.py`). Para el resto se distingue si la pausa larga fue
el FINAL de su historia o si el paciente **regreso** despues:

| Categoria | Criterio |
|-----------|----------|
| `FALLECIDO` | `FEC_FALLECIMIENTO` no nulo |
| `PALIATIVO` | Recibio cuidados paliativos (proxy) |
| `RECAIDA_PROBABLE` | Tuvo una pausa ≥540d sin atenciones y LUEGO volvio a aparecer con cirugia/quimio/radio/hospitalizacion |
| `CONTROL_POST_PAUSA` | Tuvo una pausa ≥540d y volvio, pero solo con consulta/laboratorio/imagen (sin tratamiento activo) |
| `POSIBLE_REMISION_O_ALTA` | La pausa ≥540d es lo ULTIMO que se ve de el en FISSAL antes del corte — nunca volvio |
| `EN_SEGUIMIENTO_ACTIVO` | Sin pausas ≥540d en toda su historia |

**Por que se separo en 2 categorias tras una pausa larga:** una pausa de 18
meses que termina con el paciente de vuelta en cirugia/quimio no es lo mismo
que una pausa que termina en una simple consulta de control. Lo primero
sugiere que la enfermedad volvio (recaida); lo segundo es compatible con
seguimiento de rutina despues de una posible remision. Esta distincion se
calcula revisando, sobre TODA la historia de atenciones CCR del paciente
(no solo dentro del tramo de tratamiento), cada brecha ≥540 dias entre
atenciones consecutivas y clasificando lo que ocurre en los 60 dias
siguientes al regreso (`VENTANA_RETORNO_DIAS` en el codigo).

**Este supuesto sigue sin ser una confirmacion clinica.** La pausa tambien
puede deberse a cambio de aseguradora, migracion o perdida de seguimiento
administrativo, y el hito de despistaje ya establecio que FISSAL no ve toda
la actividad del paciente en el sistema de salud. Variables de apoyo:
`TIPO_RETORNO_TRAS_BRECHA` (ACTIVO/CONTROL), `FECHA_RETORNO_TRAS_BRECHA`,
`DIAS_BRECHA_PREVIA_RETORNO`.

Resultado observado (ya con la correccion de outliers de cantidad aplicada,
ver seccion de calidad de datos):

| Categoria | n | % |
|-----------|---|---|
| `POSIBLE_REMISION_O_ALTA` | 7,989 | 50.9% |
| `EN_SEGUIMIENTO_ACTIVO` | 4,538 | 28.9% |
| `FALLECIDO` | 2,390 | 15.2% |
| `CONTROL_POST_PAUSA` | 663 | 4.2% |
| `RECAIDA_PROBABLE` | 99 | 0.6% |
| `PALIATIVO` | 19 | 0.1% |

La gran mayoria de las pausas largas resultan ser el final de la historia
del paciente en FISSAL; los 762 casos de `RECAIDA_PROBABLE` + `CONTROL_POST_PAUSA`
son una minoria pero identifican concretamente a los pacientes que "se
fueron y volvieron" — utiles para revisar caso por caso. Dato de contraste:
los `RECAIDA_PROBABLE` tienen la tasa de hospitalizacion mas alta de todos
los grupos de desenlace (65.7%, vs. 26-43% en el resto), consistente con
que su regreso implico atencion mas intensiva.

---

## Tablas generadas

| Archivo | Grano | Uso |
|---------|-------|-----|
| `FISSAL_CCR_HITOS_PACIENTE.parquet` | 1 fila/paciente (71 columnas) | Analisis cruzado, filtros, tablas |
| `FISSAL_CCR_HITOS_EVENTOS.parquet` | 1 fila/paciente x hito (formato largo) | Graficos comparativos entre hitos (timelines, boxplots de costo/duracion por hito) |
| `03_output/hitos_paciente/*.csv` | Copia CSV de las 2 tablas anteriores | Importar a Power BI (generado por `04_exportar_powerbi.py`) |

---

## Calidad de datos: outliers de cantidad y edad (corregidos en `01_procesar_fissal.py` / `03_perfil_pacientes_ccr.py`)

### Outliers de CANTIDAD (no de precio)

Se detectaron 3 registros del **HOSPITAL NACIONAL DANIEL ALCIDES CARRION**
con cantidades facturadas absurdas para el item: 1,112,500 "recargas para
grapadora quirurgica" (normal: 1), 11,250 "grapadoras" (normal: 1) y 1,531
"mascarillas oronasales" (normal: 1) — una sola linea llegaba a **S/723
millones**. En los 3 casos el precio unitario (`ATE_PRECIO`) es realista;
el error esta en `ATE_CANTBRUTA` (probable digito de mas al capturar).

**Correccion implementada** en `01_procesar_fissal.py`
(`calcular_referencia_cantidad` + `corregir_outliers_cantidad`): se calcula
la mediana historica de `ATE_CANTBRUTA` por item (`ATE_CODCONSUMO`) usando
**todos los anios** (algunos items casi no se repiten dentro de un solo
anio), y cualquier registro con cantidad > 1000x esa mediana (y con al
menos 5 registros historicos del mismo item para confiar en la mediana) se
reescala completo — cantidad bruta/neta y monto bruto/neto — por el mismo
factor, preservando el precio unitario y la relacion bruto/neto original.
Se eligio reescalar sobre eliminar el registro para no perder informacion
del resto de la atencion de ese paciente. La correccion imprime un log con
cada registro corregido y el monto total descontado.

Se uso una regla relativa por item (no un tope absoluto) porque items como
`OXIGENO MEDICINAL` legitimamente se facturan en cantidades de cientos de
miles (unidad de medida muy fina, precio unitario ~S/0.01) — un tope
absoluto los habria corregido por error.

**Resultado al correr sobre los 7 anios completos:** 415 registros
corregidos, S/861.5 millones en montos absurdos reescalados a valores
razonables. Los casos mas claros (cantidades con patron de "dedo pesado":
digitos repetidos o miles/millones donde el item normalmente es 1-2
unidades) incluyen un filtro de ventilador facturado en S/79,999,992 (3.3M
unidades, mediana del item = 1), una pinza laparoscopica en S/31,640,625
(5,625 unidades, mediana = 1), y 2 cateteres de hemodialisis en
S/2,406,950 cada uno (1,610 unidades, mediana = 1) — ademas del caso ya
descrito del Hospital Carrion. **La categoria menos certera es `OXIGENO
MEDICINAL`** (253 de los 415 registros): su precio unitario varia mucho
entre registros (de S/0.001 a S/10 por "unidad"), lo que sugiere que el
item mezcla distintas unidades de medida bajo el mismo codigo — no hay
forma de estar 100% seguro de cuales de esas correcciones son errores reales
vs. uso legitimo de oxigeno muy prolongado. El impacto en soles de esa
categoria especifica es comparativamente chico frente a los casos de arriba.
Si se necesita mas precision, lo siguiente seria revisar `OXIGENO MEDICINAL`
por separado (p.ej. exigir tambien que el precio unitario del item sea
estable entre registros antes de confiar en su mediana de cantidad).

### Edades clinicamente implausibles para CCR

Se encontraron 75 pacientes con `EDAD_PRIMERA_ATENCION` < 18 años (incluyendo
7 con edad 0-3 años y 1 con edad negativa, fecha de nacimiento posterior a
la atencion). El cancer colorrectal en la primera infancia es
practicamente inexistente en la literatura medica (los pocos casos
pediatricos documentados son casi siempre ≥10 años, asociados a sindromes
hereditarios como poliposis adenomatosa familiar). Esto sugiere un error en
`ATE_FECNAC` o en la codificacion CIE-10, no un caso real.

**Correccion implementada** en `03_perfil_pacientes_ccr.py`: se extendio el
filtro existente (que ya descartaba edades negativas o >120) para tambien
marcar como no confiable (`NA`) cualquier `EDAD_PRIMERA_ATENCION` < 10 años
**dentro de la poblacion CCR** (umbral deliberadamente conservador: 10 años,
no 18, para no descartar los pocos casos adolescentes que si son plausibles
segun la literatura). Resultado: 19 pacientes con edad <10 o >120 marcados
como NA. Este filtro clinico especifico de CCR NO se aplica en
`01_procesar_fissal.py` (el campo `EDAD` generico de ahi cubre TODAS las
enfermedades de FISSAL, incluyendo patologias pediatricas reales que no
deben descartarse).

**Como leer los reportes:** con las 2 correcciones aplicadas, el promedio
(media) de costo dejo de estar dominado por outliers extremos — por ejemplo
el costo neto medio de `POSIBLE_REMISION_O_ALTA` bajo de S/90,967 a
S/3,443.57 (la mediana, en cambio, casi no se movio: S/219.98 -> S/213.59,
confirmando que la mediana ya era confiable antes). Aun asi, para lecturas
rapidas sigue siendo mas seguro citar la **mediana**.

---

## Limitaciones

1. El hito de despistaje solo ve lo que paso **dentro de FISSAL**; un
   despistaje "no detectado" no implica que no ocurrio en otro sistema de
   salud.
2. `SECUENCIA_TRATAMIENTO` y las modalidades de tratamiento siguen siendo
   aproximaciones por texto (mismo patron que `03_analisis_ccr.py`), no
   codigos estructurados de procedimiento.
3. `POSIBLE_REMISION_O_ALTA` es una inferencia por inactividad, no un dato
   clinico confirmado — tratarla siempre como hipotesis, no como hecho.
4. La adherencia (`N_BRECHAS_TRATAMIENTO`) mide vacios en la facturacion, no
   inasistencias a citas programadas (FISSAL no tiene agenda de citas).
5. Ver la nota de calidad de datos arriba antes de reportar promedios de
   costo sin revisar percentiles/mediana.
