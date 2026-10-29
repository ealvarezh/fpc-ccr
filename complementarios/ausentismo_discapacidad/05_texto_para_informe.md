## Estimación del ausentismo laboral por licencias

El costo directo de atención reportado en la sección 10.2 —mediana de S/ 4,802 por paciente— es el que FISSAL efectivamente cubre. Como se señala en esa misma sección, hay un componente adicional de gasto de bolsillo que la base de datos de FISSAL no permite cuantificar: la pérdida de ingresos del paciente o de su cuidador durante el proceso oncológico. Esta sección y la siguiente abordan ese componente, usando fuentes complementarias a FISSAL.

### Metodología

La fuente utilizada es la Encuesta Nacional de Uso del Tiempo 2024 (ENUT, INEI), que incluye —dentro de su módulo de empleo— dos preguntas que permiten reconstruir directamente cuántas horas de la jornada normal de un trabajador se pierden y por qué motivo:

- **P707A**: para trabajadores que, teniendo empleo, no trabajaron nada en la semana de referencia, se pregunta el motivo de la ausencia completa (12 categorías, entre ellas "enfermedad, dolencia, accidente" y "otra licencia personal —cuidar familia—").
- **P732**: para trabajadores que sí trabajaron, pero menos horas de las que trabajan normalmente, se pregunta el motivo de esa reducción (9 categorías, entre ellas "por salud, enfermedad, accidente, licencia de salud").

Combinando estas dos preguntas con las horas normales de trabajo declaradas (P731) y las horas efectivamente trabajadas en la semana de referencia (P718+P728), se calcula, para cada trabajador dependiente (empleado u obrero, la población estándar para estadísticas de ausentismo laboral, a diferencia de independientes e informales cuya jornada "normal" es intrínsecamente variable), cuántas horas de su jornada habitual se perdieron esa semana y por qué motivo. El resultado se pondera con el factor de expansión muestral de la encuesta para obtener una cifra representativa a nivel nacional.

El valor monetario de cada hora se calculó de la misma fuente (ENUT 2024): entre los trabajadores dependientes pagados mensualmente, con horas e ingreso válidos, el salario/hora promedio ponderado a nivel nacional es de **S/ 11.55**.

### Resultado

De cada 100 horas de la jornada normal de un trabajador dependiente en Perú, **0.63 horas se pierden por razones de salud** (enfermedad, dolencia o accidente, cualquiera de las dos preguntas). Llevado a un año:

| Métrica | Valor |
|---|---|
| Horas perdidas por salud al año, por trabajador | 15.6 horas (≈ 2 días de 8 horas) |
| Valor monetario (a S/ 11.55/hora) | S/ 181 al año |
| Equivalente en Remuneración Mínima Vital (RMV, S/ 1,130 mensuales) | 0.16 meses |

Este orden de magnitud es consistente con el hallazgo de un estudio sobre el personal de SEDAPAL (Rodríguez García, 2014), que documentó, para una planilla de entre 1,684 y 2,408 trabajadores a lo largo de 2001–2013, un total de 31,433 certificados de descanso médico que representaron 136,873 días de ausentismo por enfermedad —con un promedio por trabajador que subió de 3.03 días/año en 2001 a 6.48 días/año en 2013—, medido con registros administrativos de descansos médicos (SIGA-SAP) en lugar de una encuesta de una sola semana de referencia como la ENUT.

### De la cifra general a un paciente con cáncer colorrectal

La cifra anterior describe a un trabajador peruano promedio, no a un paciente oncológico: la ENUT no permite aislar licencias médicas por cáncer de las de un resfrío o una torcedura de tobillo. Usarla directamente para un paciente CCR subestimaría severamente su realidad, porque el proceso oncológico no se parece en nada a la ausencia típica que capta esta encuesta.

Como referencia de magnitud, si se aplica este valor unitario (S/ 181 al año) a la duración mediana de la trayectoria clínica de un paciente CCR en FISSAL —1.8 años, según la sección 10.3—, se obtiene un **piso de S/ 326** en pérdida de ingresos por licencias médicas durante todo el proceso. Se trata explícitamente de un piso, no de una estimación del caso real: un paciente en tratamiento activo de cáncer colorrectal enfrenta cirugía (semanas de convalecencia), ciclos de quimioterapia (con días de recuperación post-infusión en cada uno) y, en 71.3% de los casos del subconjunto de referencia, al menos un episodio de hospitalización (sección 10.5) —ausencias mucho más frecuentes y prolongadas que las que capta una encuesta de uso del tiempo de la población general en una sola semana de referencia.

### Limitaciones de esta estimación

- La ENUT mide una sola semana de referencia por hogar encuestado, no un promedio anual robusto por persona; si las ausencias se agrupan en el tiempo, esto puede introducir variabilidad en la estimación semana a semana (aunque el operativo de campo de la encuesta se distribuye a lo largo del año, lo que atenúa el problema).
- No es posible aislar cáncer, ni ninguna otra enfermedad específica, dentro de la categoría "salud" de la encuesta.
- El valor no incorpora a trabajadores independientes o informales, que representan una parte importante de la fuerza laboral peruana y para quienes el concepto de "licencia médica" con continuidad de ingreso no suele aplicar de la misma manera (su pérdida, cuando enferman, es probablemente mayor y más directa, no menor).
- La cifra de S/ 326 (piso, sección "De la cifra general a un paciente con cáncer colorrectal") es una extrapolación lineal de una tasa poblacional general a la duración de la trayectoria FISSAL, no una medición directa de licencias médicas en pacientes CCR; se presenta únicamente como cota inferior y orden de magnitud.

---

## Pérdida de productividad por discapacidad o muerte prematura

Este punto tiene dos componentes de naturaleza distinta, que se presentan por separado para evitar doble conteo: la producción que deja de generar un paciente que **fallece** antes de la edad de jubilación, y la de su **cuidador familiar**, que sigue con vida y trabajando pero con menos horas disponibles mientras dura el cuidado.

### A. Muerte prematura del paciente

#### Metodología

Se utilizó el enfoque de capital humano (ECH), el método más empleado en la literatura de economía de la salud para este tipo de estimación, siguiendo la formulación de Mosegui et al. (2023) para países sudamericanos —el único estudio identificado que calcula esta métrica específicamente para Perú—:

1. Se identificaron todas las muertes por cáncer colorrectal (CIE-10 C18–C20) registradas en SINADEF (Registro Nacional de Defunciones) durante 2025, el último año con información completa. A diferencia de FISSAL, SINADEF cubre a toda la población fallecida en el país, independientemente de su afiliación a un seguro.
2. Para cada muerte ocurrida antes de los 65 años (edad de jubilación de referencia), se calcularon los años potenciales de vida productiva perdidos (APVP) como la diferencia entre 65 y la edad al fallecer.
3. El valor de cada año de vida productiva perdido se calculó como el ingreso anual promedio (INEI, Encuesta Permanente de Empleo Nacional, 2025: S/ 1,887 mensuales), ajustado por la tasa de actividad (69.5%) y la tasa de empleo (95.1%) nacionales, y descontado a valor presente con una tasa del 3% anual —la misma convención que usa la literatura internacional de referencia—.

A diferencia del estudio de Mosegui et al., que usa el salario mínimo como proxy (una elección deliberadamente conservadora), aquí se utilizó el ingreso promedio de INEI, más representativo del ingreso real de un trabajador peruano; por eso el costo por muerte que resulta es más alto que el del estudio de referencia, y no debe leerse como una discrepancia o un error.

#### Resultado

En 2025 se registraron 2,363 muertes por cáncer colorrectal en Perú, de las cuales **676 (28.6%) ocurrieron antes de los 65 años** —el resto, la mayoría, en personas ya en edad de jubilación, para quienes el método de capital humano no imputa pérdida de productividad laboral formal—.

| Métrica | Valor |
|---|---|
| Años potenciales de vida productiva perdidos, promedio por muerte prematura | 12.0 años |
| Costo de productividad por muerte prematura (valor presente) | **S/ 136,388** |
| Equivalente en meses de Remuneración Mínima Vital | 120.7 meses (≈ 10 años) |
| Costo total agregado (676 muertes, Perú, 2025) | S/ 92.2 millones |

Para contexto de magnitud: el costo de productividad de una sola muerte prematura (S/ 136,388) equivale a **28 veces** el costo médico mediano por paciente que cubre FISSAL (S/ 4,802, sección 10.2). Dicho de otro modo, lo que la sociedad deja de producir cuando un paciente de CCR muere antes de tiempo es un orden de magnitud mayor que lo que cuesta tratarlo médicamente.

Como chequeo de sensatez, el estudio de referencia (Mosegui et al., 2023) estimó, para Perú en 2019 y **todos los tipos de cáncer**, un total de 11,789 muertes en edad laboral y un costo de productividad de US$ 367.1 millones (costo por muerte: US$ 31,142, con salario mínimo). Las 676 muertes de CCR en edad laboral de este cálculo representan 5.7% de esa cifra de referencia (todos los cánceres), y el costo total de CCR (~US$ 24.6 millones) representa 6.7% del costo total del estudio de referencia —proporciones cercanas entre sí, lo que sugiere que el orden de magnitud del cálculo es razonable, aunque no son estrictamente comparables (años distintos, y CCR es solo un tipo de cáncer dentro del total).

### B. Cuidador informal

#### Metodología

A diferencia del punto anterior, aquí se buscó una estimación específica de pacientes con cáncer colorrectal, construida en dos pasos:

1. **Población de pacientes**: se tomaron los pacientes de la cohorte FISSAL (la misma base de este informe) con trayectoria activa durante 2024 —10,599 de los 24,394 pacientes históricos—, y se calcularon las semanas de esa trayectoria que caen dentro del año 2024 para cada paciente (dato observado, no supuesto).
2. **Supuestos de carga del cuidador**: no se identificó un estudio peruano sobre cuánto tiempo dedica un cuidador familiar a un paciente de cáncer colorrectal, ni sobre qué proporción de pacientes lo tiene. Por ello se plantearon tres escenarios de supuestos propios, contrastados con la evidencia internacional disponible (de países de ingresos altos, donde se concentra la investigación):
   - **Proporción de pacientes con un cuidador familiar directo**: 60% (bajo) / 75% (base) / 90% (alto). Referencia: un análisis de la Medical Expenditure Panel Survey de Estados Unidos estimó que 55.2% de los sobrevivientes de cáncer en tratamiento reciente reportó contar con un cuidador informal (Borsky et al., 2021). Los escenarios de este informe son más altos que esa referencia, porque se asume que los pacientes de FISSAL —población de alto costo, con alta proporción de ingreso grave (sección 10.6)— requieren más apoyo; este es un supuesto del equipo, no un dato medido.
   - **Horas de cuidado por semana**: 10h (bajo) / 20h (base) / 30h (alto). Referencia: una revisión sistemática reciente de 26 estudios reportó un promedio combinado de 48 horas semanales de cuidado no remunerado en cáncer, con un rango muy amplio (1.3 a 113.8 horas) y casi sin datos de países de ingresos bajos y medios (Gao et al., 2026); otras estimaciones para Estados Unidos ubican el promedio entre 28.6 y 32.9 horas semanales. Los escenarios de este informe son deliberadamente conservadores frente a esa evidencia.
3. El tiempo del cuidador se valorizó al mismo salario/hora de la ENUT 2024 (S/ 11.55).

#### Resultado

| Escenario | % pacientes con cuidador | Horas/semana | Costo anual por paciente | Equivalente en meses de RMV |
|---|---|---|---|---|
| Bajo | 60% | 10h | S/ 2,086 | 1.8 meses |
| **Base** | **75%** | **20h** | **S/ 5,215** | **4.6 meses** |
| Alto | 90% | 30h | S/ 9,387 | 8.3 meses |

En el escenario base, el costo de oportunidad del cuidador informal (S/ 5,215 al año por paciente) es del mismo orden de magnitud que el costo médico mediano que FISSAL cubre por paciente (S/ 4,802, sección 10.2) —es decir, lo que la familia pierde en ingresos del cuidador es comparable a lo que el fondo gasta en la atención médica del paciente—. Esta comparación ilustra por qué el gasto de bolsillo real del proceso oncológico, como se anota en la sección 10.2, va bastante más allá de lo que FISSAL cubre o de lo que este informe puede cuantificar con la base de datos disponible.

#### Nota sobre un enfoque alternativo (no usado como cifra principal)

Se evaluó también un enfoque top-down, usando la misma ENUT 2024: personas que, a nivel nacional, declaran no trabajar o no estudiar por dedicarse a cuidar a un integrante del hogar (variables P756 y P770). Esto arroja una población estimada de 733,700 personas (2.7% de la población de 12 años a más; 95.8% mujeres), con un costo de oportunidad agregado de ~S/ 21,000 millones al año si se asume que todas trabajarían jornada completa de no cuidar —una cota superior, no una medición, y que no es específica a cáncer sino a cuidado en general (adultos mayores, discapacidad, enfermedades crónicas, niños con necesidades especiales)—. No se usa como cifra principal porque no es trazable a la población de pacientes CCR de este informe; se documenta aquí solo como referencia de contexto sobre la magnitud del cuidado no remunerado en el país.

### Limitaciones de esta estimación

- **Muerte prematura**: el método de capital humano solo valora la pérdida de productividad laboral formal hasta la edad de jubilación; no captura la pérdida de productividad de quienes fallecen después de los 65 años (71.4% de las muertes CCR de 2025), a pesar de que en la economía informal peruana es común seguir trabajando después de esa edad. La cifra reportada, por tanto, es conservadora en ese sentido.
- **Cuidador informal**: los dos parámetros (% con cuidador, horas/semana) son supuestos del equipo, contrastados con estudios internacionales que no son peruanos ni específicos de cáncer colorrectal; se presentan como rango de escenarios precisamente por esta incertidumbre, y no como un número único.
- La población de pacientes usada para el cuidador informal (10,599, FISSAL 2024) no incluye a los pacientes CCR atendidos exclusivamente por EsSalud, el sector privado, o el SIS fuera de FISSAL (ver sección 11); el universo real de pacientes con cuidador familiar en el país es mayor.
- Ambos cálculos usan tasas de descuento, tasas de actividad/empleo e ingresos promedio nacionales, no específicos por edad ni sexo (las fuentes de INEI consultadas para este informe no las desagregan a ese nivel); una estimación con esa granularidad podría refinar el resultado, particularmente porque la mortalidad por CCR y el perfil de los cuidadores no se distribuyen igual entre hombres y mujeres.

---

## Fuentes citadas en estas dos secciones

- Instituto Nacional de Estadística e Informática (INEI). *Encuesta Nacional de Uso del Tiempo 2024* (ENUT). Microdatos.
- Instituto Nacional de Estadística e Informática (INEI). Indicadores de la Encuesta Permanente de Empleo Nacional (EPEN): tasa de actividad, tasa de desempleo, ingreso promedio mensual proveniente del trabajo, 2022–2025.
- Registro Nacional de Identificación y Estado Civil / Ministerio de Salud. SINADEF — Sistema Informático Nacional de Defunciones, datos abiertos.
- Mosegui, G. B. G., Vianna, C. M. M., Antoñanzas Villar, F., & Rodrigues, M. P. S. (2023). Pérdida de Productividad Atribuida a Neoplasias en América del Sur. *Revista Brasileira de Cancerologia*, 69(1), e-223289. https://doi.org/10.32635/2176-9745.RBC.2023v69n1.3289
- Rodríguez García, Juan Arturo (2014). *Análisis del ausentismo laboral por enfermedad en el personal de SEDAPAL, en el periodo 2001-2013*. Trabajo de investigación, Segunda Especialidad, Facultad de Medicina, Universidad Nacional Mayor de San Marcos. Disponible en: https://hdl.handle.net/20.500.12672/13186 — verificado directamente en el repositorio institucional (Cybertesis UNMSM).
- Borsky, A. E., et al. (2021). Understanding the characteristics of US cancer survivors with informal caregivers. *Cancer*. https://doi.org/10.1002/cncr.33535
- Gao, et al. (2026). Global Inequities in Unpaid Cancer Caregiving: A Systematic Review and Exploratory Meta-Analysis of Time and Cost Burden. *Cancer Medicine*. https://doi.org/10.1002/cam4.71657
- Base de datos FISSAL (misma fuente que el resto de este informe, ver sección 2.1), subconjunto de pacientes con trayectoria activa en 2024.
- D.S. N.° 006-2024-TR (Remuneración Mínima Vital, misma referencia que la sección 10.2 de este informe).
