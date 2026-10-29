<!--
NOTAS PARA ESTELA (borrar antes de pegar en el informe)
- Este texto reemplaza, en el .docx, las secciones "Estimación del ausentismo laboral por licencias" y "Pérdida de productividad por discapacidad o muerte prematura", y añade una sección nueva de gasto de bolsillo. Se deja intacta la parte de muerte prematura y cuidador informal, solo con retoques de redacción.
- Los parámetros de días perdidos por cirugía (10/20/30) y por sesión de quimioterapia (1/2/3) son supuestos propios, aún sin fuente. Conviene validarlos con un clínico o citar una referencia antes de enviar. El texto los presenta como supuestos explícitos.
- Las cifras salen de: complementarios/gasto_bolsillo/02_gasto_bolsillo_enaho.py y complementarios/ausentismo_discapacidad/06_ausentismo_bottom_up_paciente_ccr.py.
- Las cifras de muerte prematura y cuidador son las que ya están en el informe, sin cambios.
-->

## Gasto de bolsillo (ENAHO) — BORRADOR, referencia general

El costo directo de atención reportado en la sección 10.2 (mediana de S/ 4,802 por paciente) es el que FISSAL cubre; no es lo que paga la familia. Existe, además, un gasto que recae directamente sobre el hogar y que la base de FISSAL no registra. Para dimensionarlo se utilizó la Encuesta Nacional de Hogares (ENAHO) 2025, módulo de Salud.

### Metodología

Se consideró el monto que el hogar pagó de su bolsillo por los servicios de salud que efectivamente utilizó: consultas, medicinas, análisis, imágenes, otros exámenes, hospitalización e intervenciones quirúrgicas. Cada monto se llevó a un año según su período de referencia (4 semanas, 3 meses o 12 meses) y se ponderó con el factor de expansión de la encuesta. La población de análisis son los adultos de 40 años o más, grupo de edad que concentra el cáncer colorrectal.

La ENAHO no identifica a las personas con cáncer. Lo más cercano es la pregunta sobre enfermedad crónica, y las preguntas sobre hospitalización o cirugía en los últimos 12 meses. Por ello, las cifras describen el gasto de adultos con enfermedad crónica o con un evento hospitalario, y no el de un paciente con cáncer colorrectal. Se presentan como una referencia de magnitud.

### Resultados

| Escenario | Población de referencia (adultos de 40 años o más) | Gasto de bolsillo anual por persona |
|---|---|---|
| Bajo | Con enfermedad crónica (promedio, incluye a quienes no gastaron) | S/ 585 |
| Base | Cuyo hogar pagó una hospitalización o cirugía en los últimos 12 meses | S/ 4,023 (mediana S/ 2,300) |
| Alto | Mismo grupo que el escenario base, percentil 75 | S/ 5,320 |

En el escenario base, el gasto de bolsillo anual equivale a cerca del 84% del costo mediano que FISSAL cubre por paciente (S/ 4,802). Si se aplicara a la duración mediana de la trayectoria clínica en FISSAL (1.8 años), el gasto alcanzaría unos S/ 7,200 por paciente.

### Qué significa ese gasto para el hogar (gasto catastrófico)

Un gasto de salud se considera catastrófico cuando absorbe una proporción tan alta del presupuesto del hogar que obliga a recortar otros consumos básicos. Se usó el umbral habitual de más del 25% del gasto total anual del hogar. Con la Sumaria de la ENAHO 2025 se dividió a los hogares en cinco grupos de igual tamaño según su gasto por persona (Q1 es el más pobre) y se calculó qué proporción superaría el umbral si enfrentara un gasto de bolsillo anual de ese monto. Es una simulación: no se observa a hogares con un paciente de cáncer colorrectal, sino que se asigna un gasto hipotético a todos los hogares.

| Grupo de hogares | Gasto anual de S/ 585 (escenario bajo) | Gasto anual de S/ 4,023 (escenario base) |
|---|---|---|
| Q1 (más pobre) | 1% | 64% |
| Q3 | 0% | 22% |
| Q5 (más rico) | 0% | 7% |
| Total | 0% | 25% |

El mismo gasto es casi irrelevante para el quintil más alto y catastrófico para la mayoría de hogares del más pobre, que es el perfil de los asegurados del SIS cubiertos por FISSAL. Esta cifra no debe leerse como el porcentaje de pacientes con cáncer colorrectal que sufre un gasto catastrófico.

### Limitaciones

- La ENAHO no distingue el cáncer colorrectal de otras enfermedades; el gasto de un paciente oncológico probablemente sea mayor.
- No se incluyen transporte ni alojamiento, que la literatura señala como componentes relevantes, en particular para pacientes que se atienden fuera de su región de residencia.
- Quienes tienen hospitalización o cirugía pagadas por el hogar se atienden, en una proporción importante, en establecimientos privados o fuera de su seguro; la cifra puede no ser representativa de pacientes atendidos plenamente por FISSAL, cuya cobertura reduce el gasto directo.

---

## Gasto cubierto por FISSAL en pacientes con prestaciones puntuales (aproximación al gasto de bolsillo evitado) — BORRADOR

FISSAL no financia a todos sus pacientes de la misma forma. Una parte recibe una cobertura prolongada, con trayectoria completa de diagnóstico, tratamiento y seguimiento. Otra parte aparece en la base con una o dos atenciones, es decir, FISSAL habría financiado solo piezas puntuales del proceso, y el resto del cuidado habría estado a cargo de otro financiador (por ejemplo, el SIS). Estas prestaciones puntuales se pueden interpretar como el tipo de gasto que, sin FISSAL, habría recaído sobre el hogar: no representan el gasto de bolsillo observado, sino una aproximación a la exposición financiera que el fondo evitó.

### Definición

Se clasificó como paciente con prestaciones puntuales a quien tiene una o dos fechas de atención y no es un valor atípico de costo. Los pacientes con tres o más atenciones se consideran de trayectoria regular.

| Segmento | Pacientes | % de pacientes | Mediana de atenciones | Costo mediano por paciente | Costo medio | Costo total | % del costo | % fallecidos |
|---|---|---|---|---|---|---|---|---|
| Puntual (1 a 2 atenciones) | 10,939 | 44.8% | 1 | S/ 77 | S/ 394 | S/ 4.3 M | 5.0% | 8.2% |
| Trayectoria regular (3 o más) | 13,011 | 53.3% | 13 | S/ 2,047 | S/ 5,227 | S/ 68.0 M | 78.3% | 29.2% |
| Valor atípico de costo | 444 | 1.8% | 10.5 | S/ 16,501 | S/ 32,701 | S/ 14.5 M | 16.7% | 26.8% |

Casi la mitad de los pacientes (44.8%) es puntual, pero concentra solo el 5.0% del costo. El costo mediano de un paciente puntual (S/ 77) equivale a 0.07 meses de Remuneración Mínima Vital.

### Qué dicen los datos sobre la interpretación

- **No es un efecto de ingreso reciente.** El porcentaje de pacientes puntuales es 42.2% entre quienes tienen al menos 12 meses de seguimiento y 38.0% con al menos 24 meses, por lo que no se debe solo a pacientes que aún no han tenido tiempo de acumular atenciones.
- **No es mortalidad temprana.** Solo el 8.2% de los pacientes puntuales consta como fallecido, frente al 29.2% de los de trayectoria regular. Es decir, no son pacientes que abandonaron o murieron al poco tiempo, lo que es coherente con que sigan su tratamiento en otro lugar.
- **Sí compran algo distinto: lo de apoyo, no el tratamiento de fondo.** Entre los pacientes puntuales, solo el 0.7% registra medicamento oncológico, el 4.0% cirugía y ninguno radioterapia, frente a 24.8%, 30.7% y 3.5% en los de trayectoria regular. Lo que sí aparece son consultas (56.1%), medicamentos no oncológicos (53.3%), laboratorio (44.2%) e insumos médicos (37.7%). Es decir, FISSAL aparece financiando el soporte alrededor del tratamiento, mientras el tratamiento oncológico de fondo no figura en su registro.

### Limitaciones

- FISSAL no registra por qué paga una prestación, ni si el hogar habría podido costearla. La lectura como gasto de bolsillo evitado es una interpretación, no una medición, y debe contrastarse con la norma de cobertura de FISSAL y con el SIS.
- No es posible enlazar a estos pacientes con la base del SIS, por lo que no se puede confirmar que el resto de su atención haya sido financiada por otro prestador.
- El monto corresponde al costo que FISSAL reconoce, no al precio que habría pagado el hogar.

---

## Estimación del ausentismo laboral por licencias

El ausentismo laboral se analiza desde dos perspectivas distintas, que responden a preguntas diferentes y no deben sumarse ni compararse entre sí: la pérdida de horas de trabajo de la población trabajadora en general, y la pérdida de horas de trabajo asociada al proceso oncológico de un paciente con cáncer colorrectal.

### Perspectiva poblacional: línea de base

Para dimensionar el ausentismo por salud en la población trabajadora se utilizó la Encuesta Nacional de Uso del Tiempo 2024 (ENUT, INEI). La encuesta pregunta, a quienes tienen empleo, por qué no trabajaron durante la semana de referencia (ausencia completa) o por qué trabajaron menos horas de las habituales (ausencia parcial), con una categoría específica para enfermedad, dolencia, accidente o licencia de salud. Combinando estas respuestas con las horas habituales y las horas efectivamente trabajadas, se calculó, para cada trabajador dependiente, cuántas horas de su jornada normal se perdieron y por qué motivo. El resultado se ponderó con el factor de expansión de la encuesta. Cada hora se valorizó con el salario por hora promedio de los trabajadores dependientes pagados mensualmente, calculado con la misma fuente: S/ 11.55.

De cada 100 horas de la jornada normal de un trabajador dependiente en el Perú, 0.63 se pierden por razones de salud.

| Métrica | Valor |
|---|---|
| Horas perdidas por salud al año, por trabajador | 15.6 horas (aproximadamente 2 días de 8 horas) |
| Valor monetario (a S/ 11.55 por hora) | S/ 181 al año |
| Equivalente en Remuneración Mínima Vital (RMV, S/ 1,130 mensuales) | 0.16 meses |

Esta cifra corresponde a **cualquier trabajador dependiente del país y a cualquier problema de salud**, desde un resfrío hasta un accidente; no tiene relación específica con el cáncer. Se presenta como línea de base para dar contexto a lo que sigue, no como el costo del cáncer colorrectal.

Su orden de magnitud es consistente con el estudio del personal de SEDAPAL (Rodríguez García, 2014), que con registros administrativos de descansos médicos documentó entre 3.0 y 6.5 días de ausentismo por enfermedad al año por trabajador entre 2001 y 2013.

### Perspectiva del paciente: ausentismo asociado al tratamiento oncológico

Aplicar la tasa poblacional a un paciente con cáncer subestimaría su realidad: el tratamiento oncológico implica ausencias mucho más frecuentes y prolongadas que las que capta una encuesta de uso del tiempo. Por ello se estimó el ausentismo a partir de la duración real del tratamiento de cada paciente en FISSAL, para el subconjunto de referencia (8,016 pacientes).

Para cada paciente se calculó la duración de su intervención oncológica como los días transcurridos entre la fecha de inicio y la fecha de fin de la intervención registradas en FISSAL. La mediana de esa duración es de 68 días, y en el 41.0% de los pacientes es de 0 días, porque su intervención se limita a un único día (por ejemplo, una endoscopía). FISSAL registra prestaciones facturadas y no el tiempo que el paciente se ausenta de su trabajo; por ello se asumió que el paciente permanece fuera del trabajo durante una fracción de ese periodo, con tres escenarios:

| Escenario | Fracción de la duración del tratamiento fuera del trabajo | Mediana de días fuera del trabajo (pacientes con cirugía o quimioterapia) |
|---|---|---|
| Bajo | 25% | 48 días |
| Base | 50% | 89 días |
| Alto | 75% | 134 días |

El escenario base se calibró con la literatura internacional: en una cohorte australiana de trabajadores con cáncer colorrectal que volvieron al trabajo, la mediana de días fuera fue de 91 (rango intercuartil de 14 a 183) (estudio de cohorte pareada sobre el regreso al trabajo de trabajadores australianos de mediana edad con cáncer colorrectal, BMC Public Health 2014;14:963), valor cercano al del escenario base. Otro estudio, de registros en los Países Bajos (317 pacientes con cáncer de colon o recto), reporta una mediana de 423 días hasta un regreso pleno y sostenido al trabajo, por lo que el escenario alto no puede considerarse extremo. No se encontró un estudio peruano que mida estos días.

Se aplicaron además las siguientes reglas: el periodo fuera del trabajo se limitó a 365 días por paciente; si los días de hospitalización superan el periodo calculado, se toman los días de hospitalización; los días calendario se convirtieron a días laborables (5 de cada 7); y cada día laborable se valorizó con una jornada de 8 horas a S/ 11.55 por hora (S/ 92.4 por día).

| Escenario | Días laborables perdidos por paciente | Costo por paciente que trabaja |
|---|---|---|
| Bajo | 54 | S/ 5,006 |
| Base | 79 | S/ 7,341 |
| Alto | 95 | S/ 8,741 |

En el escenario base, un paciente que trabaja pierde en promedio 79 días laborables, valorizados en S/ 7,341, es decir, unas 22 veces el valor que resulta de aplicar la tasa poblacional (S/ 326 durante los 1.8 años de la trayectoria mediana). Entre los pacientes con cirugía o quimioterapia (65.5% del subconjunto), el costo medio del escenario base es de S/ 9,420.

Estos valores corresponden a pacientes que trabajan. Para estimar el costo en la cohorte se tuvo en cuenta que solo el 60.8% de los pacientes tiene menos de 65 años y que la tasa de empleo nacional es de 66.1% (tasa de actividad de 69.5% por tasa de empleo de 95.1%, INEI, 2025). Con ello se esperan unos 3,221 pacientes ocupados, y un costo agregado para la cohorte de S/ 25.8 millones en el escenario base (S/ 17.8 millones en el escenario bajo y S/ 30.6 millones en el alto).

### Limitaciones de esta estimación

- La fracción de la duración del tratamiento en que el paciente está fuera del trabajo es un supuesto del estudio, calibrado con la literatura internacional y no con mediciones en pacientes peruanos; por eso se presenta en escenarios. Una validación con datos de descansos médicos de EsSalud mejoraría la estimación.
- La duración del tratamiento se mide entre la primera y la última prestación de la intervención oncológica registradas en FISSAL, que puede incluir periodos sin atención activa; para evitar sobrestimar se limitó a 365 días.
- Los pacientes con una intervención de un solo día (41.0%) solo aportan días de hospitalización, por lo que la estimación puede subestimar las ausencias por consultas, exámenes y seguimiento.
- Los trabajadores independientes e informales, que son una parte importante de la fuerza laboral peruana, no cuentan con licencia médica con continuidad de ingreso; su pérdida real, cuando enferman, probablemente sea mayor.
- El costo agregado corresponde a la cohorte FISSAL y no al total de pacientes con cáncer colorrectal del país.
- La tasa poblacional de la ENUT se basa en una sola semana de referencia por hogar, por lo que es un promedio menos robusto que uno calculado a partir de registros anuales.

---

## Pérdida de productividad por discapacidad o muerte prematura

Esta pérdida tiene dos componentes de naturaleza distinta, que se presentan por separado para evitar el doble conteo: la producción que deja de generar un paciente que fallece antes de la edad de jubilación, y la del cuidador familiar, que sigue con vida y trabajando, pero con menos horas disponibles mientras dura el cuidado. El tiempo que el propio paciente deja de trabajar durante el tratamiento se cubre en la sección anterior.

### Muerte prematura del paciente

#### Metodología

Se utilizó el enfoque de capital humano, el método más empleado en la literatura de economía de la salud para este tipo de estimación, siguiendo la formulación de Mosegui et al. (2023) para países sudamericanos:

1. Se identificaron las muertes por cáncer colorrectal (CIE-10 C18 a C20) registradas en SINADEF durante 2025, último año con información completa. A diferencia de FISSAL, SINADEF cubre a toda la población fallecida del país, independientemente de su seguro.
2. Para cada muerte ocurrida antes de los 65 años (edad de jubilación de referencia) se calcularon los años potenciales de vida productiva perdidos, como la diferencia entre 65 y la edad al fallecer.
3. Cada año perdido se valorizó con el ingreso anual promedio (INEI, Encuesta Permanente de Empleo Nacional 2025: S/ 1,887 mensuales), ajustado por las tasas de actividad (69.5%) y de empleo (95.1%), y se descontó a valor presente con una tasa de 3% anual, convención habitual en la literatura internacional.

Mosegui et al. usan el salario mínimo como aproximación, una elección deliberadamente conservadora. Aquí se utilizó el ingreso promedio de INEI, más representativo del ingreso de un trabajador peruano. Por ello el costo por muerte resulta más alto que en el estudio de referencia, sin que esto signifique una discrepancia.

#### Resultados

En 2025 se registraron 2,363 muertes por cáncer colorrectal en el Perú, de las cuales 676 (28.6%) ocurrieron antes de los 65 años. En el resto, la mayoría, el método de capital humano no imputa pérdida de productividad laboral formal.

| Métrica | Valor |
|---|---|
| Años potenciales de vida productiva perdidos, promedio por muerte prematura | 12.0 años |
| Costo de productividad por muerte prematura (valor presente) | S/ 136,388 |
| Equivalente en meses de RMV | 120.7 meses (aproximadamente 10 años) |
| Costo total agregado (676 muertes, Perú, 2025) | S/ 92.2 millones |

Como referencia de magnitud, el costo de productividad de una muerte prematura equivale a 28 veces el costo médico mediano por paciente que cubre FISSAL (S/ 4,802). Lo que la sociedad deja de producir cuando un paciente fallece antes de tiempo supera ampliamente lo que cuesta tratarlo.

### Cuidador informal

#### Metodología

Para el cuidador se buscó una estimación específica para pacientes con cáncer colorrectal, en dos pasos:

1. **Población de pacientes.** Se tomaron los pacientes de la cohorte FISSAL con trayectoria activa durante 2024 (10,599 de los 24,394 pacientes históricos) y se calcularon, para cada uno, las semanas de trayectoria que caen dentro de ese año.
2. **Carga del cuidador.** No se identificó un estudio peruano sobre el tiempo que un familiar dedica al cuidado de un paciente con cáncer colorrectal. Se utilizaron parámetros de la literatura internacional sobre cuidado informal oncológico, que muestran amplia variabilidad, en tres escenarios: proporción de pacientes con cuidador familiar (60%, 75% y 90%) y horas de cuidado por semana (10, 20 y 30). Las horas se valorizaron a S/ 11.55, el salario por hora de la ENUT 2024.

#### Resultados

| Escenario | Pacientes con cuidador | Horas por semana | Costo anual por paciente | Equivalente en meses de RMV |
|---|---|---|---|---|
| Bajo | 60% | 10 | S/ 2,086 | 1.8 meses |
| Base | 75% | 20 | S/ 5,215 | 4.6 meses |
| Alto | 90% | 30 | S/ 9,387 | 8.3 meses |

En el escenario base, el costo de oportunidad del cuidador (S/ 5,215 al año por paciente) es del mismo orden que el costo médico mediano que cubre FISSAL (S/ 4,802): lo que la familia deja de ganar es comparable a lo que el fondo gasta en la atención del paciente. Este costo se suma al gasto de bolsillo descrito antes, que mide un tipo de gasto distinto.

### Limitaciones de esta estimación

- **Muerte prematura.** El método considera únicamente la productividad laboral formal hasta los 65 años, por lo que no incorpora a quienes fallecen después (71.4% de las muertes por cáncer colorrectal en 2025), aunque en la economía informal peruana es común seguir trabajando a esa edad. La cifra es, por tanto, conservadora.
- **Cuidador informal.** La proporción de pacientes con cuidador y las horas de cuidado provienen de estudios internacionales, no de evidencia peruana sobre cáncer colorrectal; por eso se presentan en escenarios.
- **Cobertura.** El cálculo del cuidador se basa en los pacientes de FISSAL; no incluye a quienes se atienden solo en EsSalud, el sector privado u otras modalidades.
- **Parámetros nacionales.** Las tasas de actividad y de empleo, el ingreso promedio y la tasa de descuento son nacionales, sin diferenciación por edad ni sexo. Contar con parámetros desagregados permitiría una estimación más precisa.

---

## Nota complementaria: gasto no médico con la cohorte 2016–2022 (no forma parte del análisis principal)

Los resultados anteriores usan la base actual de FISSAL (24,394 pacientes, hasta junio de 2026). Esa base no incluye el lugar de residencia del paciente, por lo que no permite estimar cuánto viaja. Como ejercicio exploratorio se utilizó la versión anterior de la base (2016–2022, 15,698 pacientes), que sí incluye el departamento de residencia y el establecimiento de cada atención. Estos resultados se presentan solo como referencia de magnitud y no se integran a las cifras del informe.

- **Atención fuera de la región de residencia.** Asignando cada establecimiento a su departamento, el 23.7% de los pacientes se atendió en un departamento distinto al de su residencia, y el 15.9% residía fuera de Lima y Callao y se atendió allí. La proporción es mayor en departamentos como Áncash, Cajamarca y Piura.
- **Costo no médico por paciente.** Con los parámetros de Robles (2023, radioterapia ambulatoria en la macrorregión Centro del Perú: US$ 69.65 por semana en transporte, alojamiento y alimentación, equivalente a unos S/ 53 por día de asistencia), la mediana por paciente fue de S/ 529. Al añadir un costo de S/ 410 por viaje interregional (estimación de una asociación de pacientes, no un estudio) para quienes se atienden fuera de su región, la mediana fue de S/ 926, y de S/ 3,148 entre quienes viajan.
- **Gasto catastrófico.** Sumando ese costo no médico al escenario base (S/ 4,023), el porcentaje de hogares del quintil más pobre que superaría el 25% de su gasto pasa de 64% a 73% (escenario A) y 80% (escenario B).

Limitaciones: el departamento de cada establecimiento se asignó manualmente para los 33 más frecuentes (97% de las atenciones) y debe verificarse contra el registro oficial de establecimientos; el costo por día de asistencia se extrapola de un estudio de radioterapia a todos los pacientes; FISSAL financia pasajes para algunos pacientes y no se descontó esa cobertura, por lo que las cifras pueden estar sobrestimadas.
