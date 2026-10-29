# Análisis previo — Ausentismo laboral y pérdida de productividad (discapacidad/muerte prematura)

**Estado:** investigación de fuentes y metodología, previo a construir código de cálculo y previo a redactar texto para el informe.
**Objetivo de esta carpeta:** los dos puntos que faltan en el informe de impacto económico del cáncer colorrectal (CCR) en Perú:

1. Estimación del ausentismo laboral por licencias (médicas)
2. Pérdida de productividad por discapacidad o muerte prematura

Para ambos, la idea es enriquecer lo que ya sabemos por FISSAL con fuentes complementarias, y solo después decidir qué entra al informe.

---

## 1. Ausentismo laboral por licencias médicas

### 1.1 La idea original (tal como la planteó Estela)

Un cascada tipo "de cada 100 horas de trabajo de la PEA, X se pierden por razón A, Y por razón B, Z por razón C", con una estimación intuitiva de que el total ronda 8-9 horas, de las cuales 2-3 serían por salud. El problema es que no hay una única fuente en Perú que ya venga armada así — hay que construirla combinando piezas.

### 1.2 Piezas encontradas para construir la cascada

| Fuente | Cifra | Qué mide | Confiabilidad |
|---|---|---|---|
| OIT (citado en tesis UPCH 2018) | El costo del ausentismo reduce el PBI mundial en ~4% | Ausentismo laboral general, no solo salud | Cifra agregada, sin desagregar por causa — usar solo como contexto, no como insumo del cálculo |
| Adecco Perú (encuesta, vía diario Gestión, citada en tesis UPCH 2018) | 56.35% de las ausencias reportadas son por problemas de salud, 45.77% por trámites personales, 15% por problemas privados (categorías no excluyentes, no suman 100%) | Motivo declarado de ausencia entre trabajadores en Lima | Encuesta de percepción, no registro administrativo — sirve para saber el *peso relativo* de salud frente a otras causas, no para calcular horas |
| Perú, vía Adecco 2013 (citado en tesis UPCH 2018) | 5% de días al año se pierden por trabajador por causas **justificadas** | Ausentismo justificado total (todas las causas, no solo salud) | Es la cifra más citable de "cuántos días se pierden en Perú"; de cada 100 días laborables, ~5 se pierden por causas justificadas |
| SEDAPAL Perú 2001-2013 (tesis Rodríguez G., citada en UPCH 2018) | 138,673 días perdidos por enfermedad en 31,433 descansos médicos, para una planilla de 1,684-2,408 trabajadores a lo largo de 13 años | Ausentismo médico en una sola empresa estatal peruana (agua/saneamiento) | Es dato real de registros administrativos peruanos, pero de una sola empresa — útil como *benchmark de orden de magnitud*, no generalizable |
| Zenodo 2025 — "Ausentismo laboral por uso de licencias médicas en cuatro sectores económicos en Perú, 2000-2025" (Mesa-Mesina et al., Rev. Universidad del Zulia) | Compara sector hospitalario, minero, poder judicial y servicios básicos en Perú; metodología de revisión de 11 estudios/tesis previos | Ausentismo por licencia médica, comparado entre 4 sectores peruanos | **Pendiente de leer el PDF completo** (DOI 10.5281/zenodo.17058338) — el resumen no trae las cifras, hay que descargar el artículo completo para sacar los números por sector |
| EsSalud — Subsidio por Incapacidad Temporal para el Trabajo (ITT) | El subsidio EsSalud empieza el día 21 de incapacidad y dura hasta 11 meses y 10 días | Define el "umbral" de licencia médica larga en Perú | Es la base normativa, no una estadística; explica por qué el sistema peruano diferencia incapacidad corta (a cargo del empleador, días 1-20) de incapacidad larga (a cargo de EsSalud, desde el día 21) |
| `complementarios/essalud/` (ya en este repo) | Solo tiene datos SAIP de consultas/atenciones de EsSalud (GCOP y GCPS), **no tiene datos de subsidios ni de descansos médicos (ITT)** | — | Confirmado al revisar `01_explorar_essalud.py` y `03_costo_proyectado.py`: no sirve para este punto tal cual está |

### 1.3 Actualización — la cascada de 100 horas YA SE CALCULÓ con microdatos reales (no con Adecco/tesis)

Estela preguntó qué faltaba exactamente para este punto. La respuesta: faltaba una fuente peruana que preguntara, con muestra representativa, "por qué no trabajaste tu semana normal de horas" con una categoría de salud separada — y resultó que **la ENUT que ya estábamos usando para el punto 2.B tiene exactamente esa pregunta**, dos veces:
- `P707A`: para quien tiene trabajo pero no trabajó nada esa semana (12 categorías, incluye "enfermedad, dolencia, accidente" y "otra licencia personal — cuidar familia").
- `P732`: para quien trabajó, pero menos horas de las normales (9 categorías, incluye "por salud, enfermedad, accidente, licencia de salud").

Con estas + horas normales (`P731`) y horas efectivamente trabajadas (`P718_T`+`P728_T`), se construyó la cascada real en [`04_cascada_ausentismo_horas.py`](04_cascada_ausentismo_horas.py), sobre empleados/obreros dependientes (la base estándar para estadísticas de ausentismo, no independientes/informales cuyas "horas normales" varían demasiado semana a semana).

**Corrección importante (bug detectado y corregido antes de usar el número en el informe):** la primera corrida de `04_cascada_ausentismo_horas.py` rellenaba con 0 las horas normales (`P731`) cuando venían vacías, y esto disparó la pérdida total a un implausible 34-36 de cada 100 horas. La causa: el cuestionario de ENUT **salta `P731` a propósito** cuando `P730==1` ("sí, trabajo normalmente esas horas") — porque en ese caso las horas normales son, por definición, las mismas que trabajó esa semana. Rellenar esos casos con 0 diluía el denominador (afectaba al 90% de la muestra: 3,346 de 3,721 empleados/obreros). Se corrigió imputando horas normales = horas trabajadas cuando `P730==1`, verificado contra el patrón exacto del cuestionario (`P731` nulo ⟺ `P730==1` en el 100% de los casos, confirmado con los datos).

**Resultado final, ya corregido — dos versiones, porque la cascada completa mezcla cosas que no son comparables:**

| | De cada 100 horas normales... | Comparable a la literatura (~5%)? |
|---|---|---|
| Cascada completa (incluye vacaciones, turno flexible, temporada) | se pierden **3.46 horas** | No — mezcla ausencia planificada/estructural con involuntaria |
| Cascada **estricta** (solo salud, licencias, discapacidad, cuidado familiar, suspensión, motivos personales) | se pierden **1.37 horas** | Mismo orden de magnitud, algo más bajo |
| **De esas, solo por SALUD** (enfermedad/dolencia/accidente, ambas preguntas) | **0.63 horas** | Más bajo que el ~2.8 estimado antes vía Adecco/tesis, pero del mismo orden de magnitud que el hallazgo de SEDAPAL (ver 1.2): ~2 días/año vs ~5.3 días/año en esa fuente |

**A nivel de persona** (trabajador dependiente promedio, jornada normal 47.4 h/semana — cifra que en sí misma es un chequeo de sensatez útil, calza con la jornada legal peruana de 48h):
- **15.6 horas/año perdidas por salud** (~2.0 días de 8 horas)
- Valorizado a S/11.55/hora (salario/hora ENUT, ver 1.3): **S/ 181/año**
- Equivalente a **0.16 meses de RMV** (S/1,130, D.S. N.° 006-2024-TR — misma referencia que usa el informe principal en la sección 10.2)

**Recomendación:** para el informe, usar el número de **salud (0.63 de cada 100 horas ≈ 2 días/año ≈ S/181/año por trabajador)** como la cifra principal — es el que responde directamente la pregunta original, está calculado con datos reales (ya corregidos), y no depende de la controversia sobre qué cuenta como "ausentismo total". Presentar el 3.46/1.37 solo como contexto metodológico.

### 1.3b Insumo adicional ya disponible: salario/hora nacional (INEI EPEN 2025)

Descargamos los cuadros oficiales de la Encuesta Permanente de Empleo Nacional (EPEN) del INEI (`output/inei_epen/`), que Estela identificó como fuente. Cifras nacionales 2025:

| Indicador | Valor 2025 |
|---|---|
| Población en edad de trabajar (PET) | 26.60 millones |
| PEA | 18.48 millones |
| Tasa de actividad (PEA/PET) | 69.46% |
| Tasa de desempleo | 4.88% |
| PEA ocupada | 17.58 millones |
| Ingreso promedio mensual del trabajo | S/ 1,887 |

Estos cuadros vienen desagregados por área urbana/rural y departamento (no por edad ni sexo en la versión "cuad-1"; existen versiones "cuad-2"/"cuad-3" separadas por hombre/mujer si se necesitan). Sirven tanto para el punto 1 (contexto de PEA/empleo) como, sobre todo, para el punto 2.A (ver abajo).

Adicionalmente, procesando directamente la ENUT 2024 (ver sección 2.B) obtuvimos un salario/hora nacional calculado desde microdatos: **S/ 11.55/hora en promedio ponderado** (mediana S/ 9.78/hora), con hombres en S/ 12.24 y mujeres en S/ 10.83 — consistente en orden de magnitud con el ingreso mensual de INEI (S/1,887 ÷ ~4.3 semanas ÷ ~47.7 horas/semana ≈ S/9.1/hora). Esta cifra puede usarse para valorizar tanto el punto 1 (horas perdidas × salario/hora) como el 2.B (tiempo de cuidado × salario/hora).

### 1.4 Qué falta / decisión pendiente

No existe una fuente pública peruana que ya reporte "de cada 100 horas de trabajo, X se pierden por salud". Hay dos caminos:

- **Camino A (más simple, defendible):** usar la cifra de "5% de días perdidos al año por causas justificadas" (Adecco/OIT vía tesis UPCH) como el total, y aplicarle el peso relativo de salud (~56% según la misma fuente) para aislar la porción atribuible a salud → **≈2.8% de los días laborables se pierden por razones de salud**. Sobre una base de 100 horas eso son **~2.8 horas**, que calza razonablemente con la intuición de "2-3 horas por salud" que mencionaste.
- **Camino B (más robusto pero más lento):** conseguir el artículo completo de Zenodo 2025 (tiene cifras específicas por sector para Perú, y cubre 25 años) y usarlo como fuente primaria peruana en vez de la tesis de pregrado de una sola empresa.

Recomendación: intentar el Camino B primero (es rápido, un solo PDF) y usar el Camino A como respaldo/contraste si el Zenodo no trae el desagregado necesario.

**Falta decidir contigo:** ¿la cascada de 100 horas debe cubrir *todas* las causas de ausentismo (salud + trámites + desmotivación + etc., como aparece en la data de Adecco) o solo enfocarse en salud y dejar las demás como "resto"? Y ¿el marco debe ser sobre días laborables al año, o específicamente sobre horas semanales? Esto cambia cómo se arma la tabla.

---

## 2. Pérdida de productividad por discapacidad o muerte prematura

Este punto en realidad tiene **dos componentes distintos** que conviene tratar por separado y que después se pueden sumar o presentar en paralelo:

### 2.A. Muerte prematura del propio paciente (método del capital humano / APVP)

Esto es lo que en la literatura de economía de la salud se llama **enfoque de capital humano (ECH)**: cuánta producción económica se pierde porque alguien muere antes de la edad de jubilación, en años de vida potencialmente perdidos (APVP / YPLL).

**Fórmula estándar** (Mosegui et al. 2023, "Pérdida de Productividad Atribuida a Neoplasias en América del Sur", Rev. Bras. Cancerologia — ver referencia abajo):

```
APVP (por muerte) = edad de jubilación − edad de muerte
Pérdida de productividad = Σ APVP × proporción de la PEA × tasa de empleo × salario anual × (1 − tasa de descuento)^años
```

**Benchmark Perú ya calculado por ese estudio (2019, todos los cánceres, no solo CCR):**

| | Mujeres | Hombres |
|---|---|---|
| APVP (25-69 años) | 6,840 | 4,949 |
| Muertes en edad laboral | 6,649 | 4,673 |
| Proporción PEA | 0.65 | 0.89 |
| Tasa de empleo | 0.97 | 0.98 |
| Pérdida de productividad (salario mínimo, nominal) | US$ 181.3 millones | US$ 185.8 millones |
| Costo por muerte | US$ 25,741 | US$ 34,980 |

Edad de jubilación usada: 65 años. Tasa de descuento: 3%.

**Lo que este repo ya tiene para construir la versión específica de CCR:**

- `sinadef/` ya procesa mortalidad nacional con `EDAD` y causa CIE-10 mapeada — con un filtro a C18-C20 (colon/unión rectosigmoidea/recto) se puede sacar la distribución de edad de muerte por CCR en Perú, en vez de usar el promedio "todos los cánceres" del estudio sudamericano.
- Con esa distribución de edad al morir + edad de jubilación (65 años, o la que corresponda por régimen) se calcula APVP específico de CCR.
- **Ya descargado y disponible** (`output/inei_epen/`, ver sección 1.3): tasa de actividad nacional 2025 (69.46%), tasa de desempleo (4.88%) e ingreso promedio mensual (S/1,887) — con esto ya se puede correr la fórmula de Mosegui et al. con salario **promedio** real en vez del salario mínimo que usa el paper original (esto sube la cifra respecto al benchmark sudamericano, que es conservador a propósito). Los cuadros descargados son nacionales/departamentales, no por grupo de edad — para replicar exactamente la desagregación por edad del paper habría que bajar además las tasas de actividad/empleo por grupo etario (no están en los cuadros ya bajados, pero el mismo portal EPEN del INEI las tiene en otros reportes técnicos trimestrales).
- **Pendiente:** correr el script que cruce SINADEF (edad de muerte por CCR) con estos insumos. No se ha hecho todavía en esta sesión — es el siguiente paso lógico para 2.A.

**Revisión de los datos de SINADEF antes de construir el script (a pedido de Estela, aún no es el cálculo final):**

Se filtró `SINADEF_DATOS_ABIERTOS.csv` (fuente: `7 Datos\Datos abiertos\sinadef\`) a causas C18-C20 (colon / unión rectosigmoidea / recto) en cualquiera de los 6 campos de causa (A-F). Hallazgos:

| | |
|---|---|
| Muertes CCR registradas 2017-2026 (2026 parcial) | 16,114 |
| Con edad registrada en años (excluye bebés en meses/días, irrelevante para CCR) | 16,077 |
| Edad promedio al morir | 70.9 años |
| Edad mediana al morir | 73 años |
| Rango | 4 a 106 años (el caso de 4 años es un outlier a revisar — posible error de registro o un cáncer colorrectal pediátrico genuino, rarísimo) |
| Sexo | 53% mujeres, 47% hombres |
| **Muertes antes de los 65 años (edad de jubilación de referencia)** | **4,117 de 16,077 = 25.6%** |
| Muertes 65+ | 74.4% |

**Implicación para el cálculo de APVP:** solo ~1 de cada 4 muertes por CCR en Perú ocurre antes de la edad de jubilación estándar (65 años) — la mayoría de las muertes son en adultos mayores que, bajo el método de capital humano clásico, ya no "pierden" productividad laboral formal (aunque sí pueden seguir trabajando informalmente, que es común en Perú — el paper de Mosegui et al. señala esto como una limitación del método en economías con alta informalidad). Esto significa que la cifra final de "pérdida de productividad por muerte prematura" en CCR va a ser bastante más chica, en términos relativos, que si se mirara la carga de enfermedad total (AVISA) del CCR — porque el AVISA sí cuenta los años de vida perdidos de los adultos mayores, pero el enfoque de productividad laboral (ECH) solo cuenta hasta la jubilación. **Vale la pena decidir contigo si el informe quiere mostrar el número "solo hasta jubilación" (más conservador, comparable al benchmark sudamericano) o también una variante que extienda algunos años más la edad de jubilación efectiva** (Mosegui et al. corrieron un escenario con +5 años, dado que en Perú es común seguir trabajando después de los 65 en la economía informal).

**Cálculo final — hecho, ver [`03_estimar_apvp_muerte_prematura_ccr.py`](03_estimar_apvp_muerte_prematura_ccr.py).** Versión simple confirmada por Estela: jubilación fija en 65 años (sin el escenario "+5 años"), comparado contra el benchmark sudamericano.

**Resultado (SINADEF, año 2025, ingreso promedio de INEI en vez de salario mínimo, descuento 3%):**

| | Este cálculo — solo CCR, Perú 2025 | Benchmark Mosegui et al. — todos los cánceres, Perú 2019 |
|---|---|---|
| Muertes en edad laboral (<65 años) | 676 (28.6% de 2,363 muertes CCR totales) | 11,789 |
| APVP total | 8,142 años | 171,197 años |
| Costo total | S/ 92.2 millones (~US$ 24.6 millones) | US$ 367.1 millones |
| Costo por muerte | S/ 136,388 (~US$ 36,370) | US$ 31,142 |

El costo por muerte de este cálculo sale más alto que el benchmark porque usa el **ingreso promedio** de INEI (S/1,887/mes) en vez del salario mínimo que usa el paper original — es lo esperado, no un error. Como chequeo de sensatez: las 676 muertes CCR bajo 65 años representan el 5.7% de las 11,789 muertes de todos los cánceres del benchmark, y el costo total de CCR (US$24.6M) es el 6.7% del costo total del benchmark (US$367M) — proporciones cercanas, buena señal de que el orden de magnitud es razonable (aunque no son estrictamente comparables: distintos años y el benchmark es "todos los cánceres" vs. este cálculo que es solo CCR).

**Nota sobre el descuento:** se calculó también la versión SIN descuento (S/121.8 millones) para referencia — la diferencia (S/92.2M vs S/121.8M) es la corrección por valor presente de años futuros de sueldo, siguiendo la misma convención que el benchmark (tasa 3%).

También se revisó `FISSAL_CCR_HITOS_V2.parquet` (24,394 pacientes CCR históricos en FISSAL/SIS, 10,599 con trayectoria activa en 2024) — esta base tiene fechas de fallecimiento propias (`FECHA_FALLECIMIENTO`, `FALLECIDO`) que en teoría se podrían cruzar con SINADEF, pero **SINADEF es la fuente más completa para la mortalidad nacional** (incluye EsSalud y privados, no solo SIS), así que el cálculo de APVP debería hacerse sobre SINADEF y no sobre FISSAL.

### 2.B. Cuidador informal (tiempo de cuidado no remunerado dentro del hogar)

Esto es un componente distinto: no es la productividad perdida del paciente, sino la del **familiar que lo cuida** — lo que mencionaste que ya habías hecho antes con "la ENDES".

**Metodología que describiste:** filtrar hogares con algún integrante con cáncer → identificar quién lo cuida → cuántas horas dedica → horas × salario promedio por hora = pérdida económica del cuidador.

**Estado de la verificación — YA REVISADO, conclusión: ENDES 2025 no sirve para esto.**

Se exploraron los diccionarios de variables de los 4 módulos que dejaste en `Adicional 2026 - ENDES` (RECH0/RECH1/RECH4/RECHM, RECH23, DIT/REC42/REC43/REC95, CSALUD01/CSALUD08). Hallazgos:

- **No existe ninguna variable** de "quién cuida a un miembro del hogar enfermo/discapacitado", "cuántas horas/días le dedica", ni "dejó de trabajar por cuidar a alguien" — ni en el cuestionario del hogar, ni en el individual, ni en el de salud.
- La **discapacidad (preguntas tipo Washington Group)** solo se releva para niñas/niños menores de 6 años (dentro del cuestionario individual) y para **una única persona de 15+ años seleccionada al azar por hogar** en CSALUD01 (`QS25C1`-`QS25C6`) — nunca para "cualquier miembro del hogar", que es lo que se necesitaría para identificar al paciente con cáncer dentro de una familia y a su cuidador por separado.
- El **diagnóstico médico confirmado** en CSALUD01 solo cubre hipertensión (`QS102`) y diabetes (`QS109`). Las preguntas relacionadas a cáncer (`QS401`-`QS419A`) son de **conocimiento y tamizaje** (PAP, mamografía, PSA, chequeos), no "¿le diagnosticaron cáncer?" — no hay forma de identificar pacientes con cáncer en la base.
- **Horas de trabajo/empleo** solo se releva para la mujer entrevistada de 12-49 años (sección de trabajo del cónyuge/mujer), no para un cuidador cualquiera del hogar (que podría ser el esposo, un hijo adulto, o los padres del jefe de hogar).
- Los módulos DIT, REC42, REC43 y REC95 son en su totalidad salud materno-infantil y reproductiva (lactancia, vacunas, anemia, desarrollo infantil) — no tocan el tema.

**En síntesis: ENDES sigue siendo esencialmente una encuesta de salud materno-infantil y reproductiva**, con módulos anexos de enfermedades no transmisibles aplicados a una sola persona por hogar — no un instrumento de cuidado de adultos con enfermedades crónicas. Es muy probable que la fuente que usaste antes haya sido **ENAHO**, no ENDES: ENAHO sí tiene el Módulo 400 (Salud, con preguntas de acompañamiento a consulta y tiempo dedicado) y un Módulo de Empleo e Ingresos que cubre a todos los miembros del hogar (no solo a la mujer entrevistada), lo cual encaja con "filtrar hogares con un enfermo, ver quién lo cuida, cuántas horas, y multiplicar por salario/hora".

**Actualización — Estela confirmó que ENAHO tampoco trae un indicador de tiempo de cuidadores, y en su lugar identificó la ENUT (Encuesta Nacional de Uso del Tiempo) 2024 del INEI, que sí sirve.** Carpeta: `Adicional 2026 - ENUT` (mismo directorio base). Revisando el diccionario (`04_DICCIONARIO_ENUT_2024.pdf`) confirmamos que ENUT sí tiene lo que se necesita, aunque **tampoco identifica cáncer específicamente** — es un análisis general de cuidado no remunerado, tal como Estela sugirió ("se puede hacer un análisis más exploratorio general").

**Variables clave encontradas en ENUT 2024:**
- `P756` (capítulo 700, archivo `V_ENUT2024_700_800_900.csv`): "¿Por qué no buscó trabajo?" — código 7 = "Se dedica al cuidado de un miembro del hogar", código 8 = "Razones de salud". A nivel de **cualquier persona de 12+ años del hogar**, no solo mujeres.
- `P770`: misma lógica para "¿por qué no asiste a un centro de estudios?" — código 10 = cuidado de un miembro del hogar.
- `P731` (horas normales trabajadas/semana), `P738`/`P739_1` (frecuencia e ingreso mensual de dependientes), `P742` (ganancia neta mensual de independientes) — permiten estimar salario/hora.
- `P209`/`P210` (capítulo 200): dificultad para realizar actividades diarias, a nivel de **cada miembro del hogar** (a diferencia de ENDES, que solo preguntaba a una persona seleccionada).
- Capítulo 600 (`V_ENUT2024_600.csv`): diario de uso del tiempo cada 10 minutos (3 días: entre semana, sábado, domingo) con hasta 3 actividades paralelas por franja — en teoría el más preciso para medir horas de cuidado, pero **los códigos de actividad (tabla de clasificación CAUTAL) no vienen en el diccionario que se leyó**; quedaría pendiente ubicarlos si se quiere una medición más fina que la de P756/P770.
- **No encontrado:** una variable de enfermedad crónica a nivel de hogar (`P304` está descrita en el cuestionario pero no aparece en ninguno de los 4 CSV entregados — puede que ese módulo no se haya incluido en el extracto, o que no se recolecte a nivel nacional).

**Script corrido:** [`01_explorar_enut_cuidadores.py`](01_explorar_enut_cuidadores.py). Resultados (poblacional, con factor de expansión):

| Resultado | Valor |
|---|---|
| Personas que no trabajan o no estudian por cuidar a alguien del hogar | ~733,700 (2.68% de la población de 12+ años) |
| % mujeres entre esas personas | 95.8% |
| Grupo de edad más frecuente | 30-44 años |
| Salario/hora de referencia (nacional, ponderado) | S/ 11.55 |
| "Techo" de costo de oportunidad anual agregado | ~S/ 21,000 millones/año (~US$ 5,600 millones) |

**Importante sobre esa última cifra:** es un techo, no una medición — asume que las ~734 mil personas trabajarían jornada completa (47.7 h/semana) si no cuidaran, lo cual sobreestima bastante (no todas buscarían trabajo de tiempo completo). Sirve como cota superior de referencia, no como el número final del informe. Para acotarlo mejor se podría, por ejemplo, usar solo una fracción de la jornada, o cruzarlo con `P733`/`P734` (si querían trabajar más horas).

**Cómo conectar esto con FISSAL/CCR — YA HECHO, ver script [`02_estimar_costo_cuidador_ccr.py`](02_estimar_costo_cuidador_ccr.py):**

En vez de bajar el número general con un factor de prorrateo, se armó un cálculo **bottom-up independiente** directamente desde FISSAL, para poder comparar los dos enfoques:

```
costo_anual = pacientes_CCR_activos_en_el_año (FISSAL)
            x % de pacientes con cuidador familiar directo   [supuesto de literatura: 60/75/90%]
            x horas de cuidado por semana                     [supuesto de literatura: 10/20/30h]
            x semanas de trayectoria del paciente ese año      [calculado de FISSAL, no supuesto]
            x salario/hora (S/ 11.55, calculado de ENUT)
```

Los supuestos de % con cuidador y horas/semana vienen de estudios internacionales/LatAm de "carga del cuidador oncológico" (ninguno específico de Perú ni de CCR) — con muchísima dispersión: un estudio de cabeza y cuello reportó 92h/semana, otro de cuidados paliativos 126h/semana, otro que el 57% de cuidadores dedica más de 21h/semana. Por eso se corrió como **rango de escenarios**, no como número único.

**Resultado (FISSAL, 10,599 pacientes CCR con trayectoria activa en 2024):**

| Escenario | % con cuidador | Horas/semana | Costo anual |
|---|---|---|---|
| Bajo | 60% | 10h | S/ 22.1 millones |
| **Base** | **75%** | **20h** | **S/ 55.3 millones** |
| Alto | 90% | 30h | S/ 99.5 millones |

**Comparación de los dos enfoques (esto responde la pregunta de cuál es más "entendible"):**

| | Enfoque 1 (ENUT, top-down) | Enfoque 2 (FISSAL, bottom-up) |
|---|---|---|
| Población base | ~734,000 cuidadores (cualquier motivo, todo el país) | 10,599 pacientes CCR activos en FISSAL 2024 |
| Qué mide | Costo de oportunidad de TODO el cuidado no remunerado en Perú | Costo de oportunidad específico de cuidar pacientes CCR (solo SIS/FISSAL) |
| Cifra base | ~S/ 21,000 millones/año | ~S/ 55.3 millones/año |
| Fortaleza | Usa datos reales de una encuesta representativa (ENUT), sin supuestos sobre % con cuidador ni horas | Está directamente atado a la población de pacientes CCR real — mucho más fácil de explicar y defender en el informe ("de nuestros N pacientes CCR, asumimos que X% tiene cuidador que le dedica Y horas...") |
| Debilidad | No es específico a CCR; requiere un factor de prorrateo inventado si se quiere bajar a CCR, lo cual sería poco defendible | Depende de 2 supuestos de literatura no peruana (% con cuidador, horas/semana) — mitigado presentando rango, no punto único; y FISSAL no cubre EsSalud/privados (subestima el universo real de pacientes) |
| Recomendación | Útil como **contexto/comparación** en el informe ("el cuidado no remunerado mueve X% del PBI en Perú") | **Este es el que debería ir como cifra principal del informe** para el punto 2.B, justamente porque es trazable a una población nombrada (pacientes CCR de FISSAL) y no a una extrapolación nacional abstracta |

### 2.C. Cómo se relacionan A y B con el informe

- A (muerte prematura) da una cifra de **pérdida social/nacional** agregada — útil para dimensionar el problema a nivel país.
- B (cuidador informal) da una cifra de **carga familiar directa** — más alineada con el eje "impacto económico familiar" que ya describe `proceso_oncologico_ccr.md`.
- No hay doble conteo entre A y B (uno mide la producción perdida del paciente que fallece; el otro, la del cuidador que sigue vivo y trabajando pero con menos horas) — sí conviene aclarar eso explícitamente si ambos se presentan juntos en el informe, para que no se lean como "lo mismo dos veces".

---

## 3. Estado actual y próximos pasos

**Hecho en esta sesión:**
- ✅ Punto 1: cascada de 100 horas calculada con microdatos reales de ENUT 2024 (no con Adecco/tesis) — **0.63 de cada 100 horas normales se pierden por salud** (≈15.6 h/año ≈ S/181/año por trabajador; ver sección 1.3, incluye una corrección de bug importante). Zenodo no tenía la info necesaria, así que se descartó como fuente.
- ✅ Punto 2.B (cuidador informal): dos enfoques calculados y comparados. **Decidido con Estela: usar el enfoque FISSAL/bottom-up como cifra principal del informe** (S/55.3 millones/año, escenario base; rango S/22.1M–S/99.5M).
- ✅ Punto 2.A (muerte prematura): calculado y comparado contra el benchmark sudamericano. S/92.2 millones/año (676 muertes CCR bajo 65 años, año 2025).

### Números finales recomendados para el informe (punto 2 completo)

| Componente | Cifra recomendada | Fuente / script |
|---|---|---|
| 2.A — Muerte prematura (capital humano/APVP) | **S/ 92.2 millones/año** | `03_estimar_apvp_muerte_prematura_ccr.py`, SINADEF + INEI EPEN |
| 2.B — Cuidador informal | **S/ 55.3 millones/año** (escenario base; rango S/22.1M–S/99.5M) | `02_estimar_costo_cuidador_ccr.py`, FISSAL + ENUT |
| **Suma (si se presentan juntos)** | **~S/ 147.5 millones/año** | — |

**Importante si se suman:** no hay doble conteo — 2.A mide la producción perdida de pacientes que **fallecen**, 2.B mide la de sus **cuidadores, que siguen vivos y trabajando pero con menos horas**. Son poblaciones distintas. Sí conviene aclarar esto explícitamente en el informe para que no se lean como "lo mismo dos veces". El enfoque ENUT de 2.B (~S/21,000 millones/año) queda como dato de contexto/comparación, no como parte de esta suma.

**Pendiente / decisiones para Estela:**
1. ~~Zenodo 2025~~ — revisado, no tenía cifras utilizables; se reemplazó por el cálculo directo con ENUT (ver 1.3).
2. (Opcional) Acotar aún más el rango de escenarios de 2.B con datos peruanos reales si aparece algún estudio local de carga del cuidador oncológico (los 3 supuestos usados son de estudios internacionales).
3. Revisar el outlier de 4 años en la mortalidad SINADEF CCR (ver sección 2.A) — probablemente error de registro, no afecta el cálculo (queda fuera del grupo <65 de todas formas, pero vale la pena confirmar que no distorsiona nada aguas abajo).
4. Decidir si el 1.37/100 (cascada estricta, punto 1) se menciona en el informe como contexto, o si solo se usa el 0.63/100 de salud para no abrir la discusión de qué cuenta como "ausentismo total".

---

## Referencias

- Mosegui GBG, Vianna CMM, Antoñanzas Villar F, Rodrigues MPS. "Pérdida de Productividad Atribuida a Neoplasias en América del Sur." *Revista Brasileira de Cancerologia* 2023;69(1):e-223289. https://doi.org/10.32635/2176-9745.RBC.2023v69n1.3289
- Carbajal Puertas I, Palomino Amenero GH. "Ausentismo laboral por causas médicas en trabajadores en una empresa metal-mecánica. Enero a julio 2018." Trabajo académico, Universidad Peruana Cayetano Heredia, 2018.
- Mesa-Mesina F, Quevedo-León, Espinoza-Téllez T. "Ausentismo laboral por uso de licencias médicas en cuatro sectores económicos en Perú, 2000-2025." Zenodo, 2025. https://doi.org/10.5281/zenodo.17058338 (pendiente leer texto completo)
- EsSalud. "Subsidio por Incapacidad Temporal." https://www.essalud.gob.pe/incapacidad-temporal/
- INEI. Encuesta Nacional de Uso del Tiempo (ENUT) 2024. Microdatos y diccionario de variables en `Adicional 2026 - ENUT` (carpeta local del usuario).
- INEI. Indicadores EPEN (PEA, tasa de actividad, tasa de desempleo, ingreso promedio mensual, PET), 2022-2025. Cuadros descargados en `output/inei_epen/`.
