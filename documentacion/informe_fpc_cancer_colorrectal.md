**Análisis de la trayectoria clínica y costos en pacientes con cáncer colorrectal en el sistema FISSAL**

**Documentación metodológica del análisis**

**Elaborado por**

*[imagen/figura en el documento original]*

**Presentado para**

**Fundación Peruana de Cáncer**

**
**

**Lima, 23 de Septiembre del 2026**

*Este estudio refleja la mejor opinión de APOYO Consultoría, con la información disponible a la fecha, respecto del tema en cuestión; por lo que en concordancia con el código de ética del Grupo APOYO constituye una opinión independiente y no condicionada por el cliente contratante.*


| Control de Versiones | Control de Versiones | Control de Versiones | Control de Versiones | Control de Versiones | Control de Versiones |
|---|---|---|---|---|---|
| Número Versión | Responsables técnicos | Responsables del negocio | Fecha | Descripción del cambio |
| 1 | Estela Alvarez | Fátima Luna | 23/09/2026 | Documentación metodológica del análisis |
|  |  |  |  |  |

# **Alcance y objetivo**

Este documento describe la metodología utilizada para el análisis de la trayectoria clínica y los costos de atención de pacientes con cáncer colorrectal (CCR) en el Fondo Intangible Solidario de Salud (FISSAL). El análisis busca caracterizar el proceso completo de atención oncológica, desde el ingreso del paciente al sistema hasta su desenlace, y estimar el costo económico que dicho proceso representa para el sistema de salud.

Los objetivos específicos son:

- Identificar y caracterizar a los pacientes con diagnóstico de CCR financiados por FISSAL entre 2016 y 2026.
- Reconstruir la trayectoria clínica de cada paciente mediante la secuencia de hitos de atención (ingreso, intervención oncológica y cierre).
- Calcular los tiempos transcurridos entre cada hito para estimar la velocidad de acceso al tratamiento y la duración del proceso.
- Estimar los costos de atención por paciente, desagregados según el tipo de recurso y su atribuibilidad al CCR, expresados en soles constantes de 2024.
- Analizar el comportamiento hospitalario, la mortalidad y la distribución del gasto por año y por categoría clínica.
- Incorporar datos de EsSalud y SIS como fuentes complementarias para ampliar el contexto.
# **Fuentes de información**

## **FISSAL (fuente principal)**

La fuente principal de información es la base de datos del FISSAL, que contiene los registros de atención financiados por el mismo, incluyendo datos demográficos del paciente, diagnóstico, tipo de atención, consumo de recursos y montos netos y brutos facturados. La información abarca el período 2016 al 2026, con fecha de corte al 31 de marzo de 2026, y corresponde a diagnósticos CIE-10: C18 (colon) y C19 (unión rectosigmoidea).

Las principales variables de esta fuente son:

- **Paciente:** código de identificación, sexo, fecha de nacimiento, fecha de fallecimiento.
- **Diagnóstico: **código CIE-10, grupo y descripción del diagnóstico.
- **Atención:** fecha, tipo de atención (ambulatorio, emergencia, referido), fechas de ingreso y alta de hospitalización, establecimiento de salud.
- **Consumo de recursos:** descripción del ítem, tipo de consumo, montos netos y brutos facturados.
## **EsSalud – GCOP (fuente complementaria)**

El Sistema de Gestión de Consulta Oncológica de Pacientes (GCOP) de EsSalud registra las atenciones ambulatorias de pacientes con diagnóstico oncológico en esa institución. A diferencia de FISSAL, GCOP registra eventos de consulta por especialidad, no ítems de consumo individuales, por lo que no es posible calcular costos directamente desde esta fuente (ver sección 11.1).

Las principales variables disponibles en GCOP son:

- **Identificación:** ID compuesto anonimizado (construido a partir de DNI enmascarado, sexo y fecha de nacimiento implícita).
- **Atención:** fecha de atención, especialidad (servicio), resultado de la atención (RESULT_ATENCION: "Atención médica ambulatoria", "Cirugía", "Hospitalización", etc.).
- **Diagnóstico:** código CIE-10 del diagnóstico principal.
## **SIS - Seguro Integral de Salud (fuente complementaria)**

La base de datos del SIS contiene registros de atención de pacientes CCR cubiertos por ese seguro, que son una población distinta a la de FISSAL. Esta fuente permite dimensionar la población con CCR fuera del radar de FISSAL, aunque con un alcance geográfico limitado, ya que los 1,315 pacientes del extracto se atendieron en establecimientos de Lima. Además, presenta una limitación estructural importante: el 91.6% de los pacientes SIS tiene un único registro de atención, lo que impide reconstruir trayectorias o calcular costos con la misma metodología aplicada a FISSAL. El análisis SIS se limita a un perfil descriptivo (ver sección 11).

Las variables disponibles en la fuente SIS son:

- **Paciente:** código de persona (anonimizado), sexo.
- **Atención:** fecha de atención, tipo de atención, año de atención, departamento del establecimiento.
- **Diagnóstico:** código CIE-10, tipo de diagnóstico (definitivo/presuntivo/repetitivo).
*Nota: La fuente SIS no incluye fecha de nacimiento ni edad, por lo que no es posible perfilar a los pacientes por grupo etario ni cruzar ese dato con FISSAL.*

# **Completitud de la información**

La base de datos FISSAL incluye la totalidad de registros de atención financiados por ese fondo en el período analizado. Todos los pacientes tienen al menos un registro con diagnóstico CCR (C18/C19), tal como lo exige el criterio de construcción de la cohorte.

**Fecha de fallecimiento centinela:** La variable Fecha_fallecimiento presenta el valor 01/01/1900 en los casos en que se cuenta con registro de fallecimiento, pero no se dispone de la fecha exacta. Estos casos se identifican mediante el indicador FECHA_FALLECIMIENTO_EXACTA = False. Para los cálculos que requieren determinar el tiempo hasta el fallecimiento, se utiliza la fecha de última atención registrada como fecha de referencia, ya que la fecha centinela no corresponde a la fecha real de defunción y generaría resultados inconsistentes.

Este valor centinela se presenta en 3,757 de los 4,818 fallecidos (78.0%) de la cohorte completa y en 2,157 de los 2,549 fallecidos (84.6%) del subconjunto Track A + FISSAL Regular utilizado para el análisis de tiempos y costos (sección “Resultados principales”). Por ello, los tiempos hasta el fallecimiento presentados en este informe deben interpretarse como una aproximación basada en la última atención registrada y no como el tiempo calculado a partir de la fecha real de defunción.

# **Construcción de la cohorte de pacientes con CCR**

La cohorte se define como el conjunto de pacientes que tienen al menos un registro en FISSAL con un código CIE-10 de cáncer colorrectal.

Una vez identificados los pacientes CCR, se extrae la totalidad de sus registros en FISSAL, no solo los codificados como CCR. Esto permite capturar el costo completo de atención, incluyendo comorbilidades, atenciones previas al diagnóstico formal de CCR y costos de soporte que no siempre llevan el código CIE-10 del tumor.

La localización del tumor se determina a partir del primer registro codificado específicamente como CCR para cada paciente. Esa misma fecha se registra como FECHA_DIAGNOSTICO_CCR y es la referencia para calcular la edad al diagnóstico y la supervivencia.

# **Reconstrucción de la trayectoria clínica en FISSAL**

Para caracterizar la trayectoria de cada paciente se construyó un modelo de tres hitos secuenciales: ingreso al sistema, intervención oncológica y cierre. Este enfoque permite calcular tiempos de espera, duración del tratamiento y tiempo de seguimiento post-intervención de manera estandarizada. La Figura 1 presenta de manera esquemática la trayectoria clínica de los 8,016 pacientes del subconjunto de referencia (Track A + FISSAL Regular), diferenciando los dos sub-perfiles identificados según el tipo de tratamiento recibido.

*[imagen/figura en el documento original]*

**Figura 1. Flujo clínico de pacientes del subconjunto de referencia en FISSAL (Track A + FISSAL Regular, n = 8,016): sub-perfiles A.1 (sin quimioterapia) y A.2 (con quimioterapia)**

## **Hito 1: Ingreso al sistema FISSAL**

El hito de ingreso es el primer contacto del paciente en FISSAL, independientemente del motivo de atención. Un paciente puede ingresar por una enfermedad distinta al CCR, como una comorbilidad, y ser diagnosticado con CCR después; por eso el hito de ingreso usa el primer registro general, no el primer registro CCR.

Las variables construidas en este hito son:

- **TIPO_INGRESO:** tipo de atención en el primer contacto: Ambulatorio, Emergencia o Referido.
- **IPRESS_INGRESO:** establecimiento de salud donde se realizó el primer contacto.
- **LOCALIZACION:** sitio del tumor, derivado del primer registro específicamente codificado como CCR.
- **INGRESO_GRAVE:** indicador que vale "Verdadero" si el primer contacto fue por emergencia o implicó hospitalización.
*Nota: La variable **Tipo_atencion** solo contempla los valores "AMBULATORIO", "EMERGENCIA" y "REFERIDO". La hospitalización se identifica a partir de la presencia de fechas de ingreso y alta hospitalaria (**Fecha_ingreso_hospitalizacion** y **Fecha_alta_hospitalizacion**), y no mediante **Tipo_atencion**.*

## ** Hito 2: Intervención oncológica**

El hito de intervención agrupa los recursos de tratamiento oncológico activo recibidos por el paciente en FISSAL. La clasificación se basa en las categorías del Diccionario 502 (ver sección 6), no en patrones de texto libre.

Se consideran tratamientos oncológicos las siguientes cuatro categorías:

- **Procedimiento quirúrgico:** cirugía de resección u otros procedimientos quirúrgicos relacionados con el tumor.
- **Medicamento oncológico:** quimioterapia sistémica (agentes alquilantes, antimetabolitos, anticuerpos monoclonales, etc.).
- **Radioterapia:** sesiones de radioterapia externa o braquiterapia.
- **Endoscopía / colonoscopía:** estudios endoscópicos diagnósticos o terapéuticos.
Para cada modalidad se calcula la fecha de inicio (primera atención en esa categoría), la fecha de fin (última atención) y el número de sesiones o días únicos. La fecha de inicio de la intervención general es el mínimo de los cuatro inicios; la fecha de fin general es el máximo de los cuatro fines.

### ** Clasificación en Tracks (perfiles de tratamiento)**

Los pacientes se clasifican en dos grandes grupos según el nivel de intervención registrado:

- Track A COMPLETO (n = 11,095, 45.5%): el paciente tiene al menos un registro en alguna de las cuatro categorías de tratamiento oncológico activo.
- Track B PARCIAL (n = 13,299, 54.5%): el paciente no tiene registros de ninguna de las cuatro categorías. Puede reflejar manejo exclusivamente paliativo, atenciones insuficientes para reconstruir la trayectoria, o registros incompletos.
### **Sub-perfiles dentro del Track A**

Dentro de los 8,016 pacientes del subconjunto de referencia (Track A + FISSAL Regular), los pacientes se dividen en dos sub-perfiles según hayan recibido o no algún registro de quimioterapia ("Medicamento oncológico" en el diccionario 502). La Figura 1 ilustra el flujo clínico de ambos sub-perfiles, con los tiempos medianos observados entre cada paso:


| Característica | Sub-perfil A.1 - Sin quimioterapia | Sub-perfil A.2 - Con quimioterapia |
|---|---|---|
| n (% del subconjunto de referencia) | 4,795 (59.8%) | 3,221 (40.2%) |
| Tratamiento principal | Endoscopía ± cirugía | Quimio ± cirugía ± radio |
| Mortalidad | 28.0% | 37.4% |
| Trayectoria total (mediana) | 587 días | 722 días |
| Trayectoria total (media) | 840 días | 927 días |
| Hospitalizaciones (≥1 episodio) | 66.0% | 79.2% |
| Días hospitalizados — mediana | 0 días (entre todos) | 7 días (entre todos) |
| Ingreso grave al FISSAL | 66.9% | 79.9% |
| Diagnóstico a inicio de intervención (mediana) | 32 días | 30 días |
| Costo total (mediana / media) | S/ 3,200 / S/ 6,262 | S/ 7,358 / S/ 10,580 |

Los tiempos desde el diagnóstico hasta el inicio de cada modalidad de tratamiento, en el subconjunto de referencia, son:


| Modalidad | Diagnóstico a inicio (mediana) | Diagnóstico a inicio (media) | Duración (mediana) | Duración (media) |
|---|---|---|---|---|
| Endoscopía / colonoscopía (n=4,518) | 46 días | 248 días | 0 días (puntual) | 226 días |
| Cirugía (n=3,500) | 53 días | 182 días | 0 días (puntual) | 92 días |
| Quimioterapia (n=2,554) | 76 días | 139 días | 72 días | 162 días |
| Radioterapia (n=311) | 164 días | 361 días | 0 días | 43 días |

*Nota: La "duración" de endoscopía**,** cirugía **y radioterapia **es 0 días en la mediana porque el mismo día de inicio se registra como fin. La "duración" de quimioterapia refleja el ciclo completo entre la primera y la última sesión registrada, no la duración de una sesión individual.*

Para los pacientes que reciben tanto cirugía como quimioterapia, el tiempo entre el fin de la cirugía y el inicio de la quimioterapia adyuvante (solo casos donde la quimio inicia el mismo día o después del fin de la cirugía, 56% de esos pacientes) tiene una mediana de 61 días y una media de 100 días.

Para los pacientes que reciben endoscopía antes de cirugía, el tiempo entre la primera endoscopía y la cirugía (n=1,261, 61% de los 2,064 pacientes con ambas modalidades) tiene una mediana de 31 días y una media de 165 días.

## ** Hito 3: Cierre**

El hito de cierre representa el estado final del paciente según la información disponible hasta el 31 de marzo de 2026. Se establecen cuatro categorías mutuamente excluyentes, asignadas según el siguiente orden de prioridad:

- **FALLECIDO:** se registra una fecha de fallecimiento. Cuando esta corresponde al valor centinela (01/01/1900), se utiliza la fecha de última atención como referencia.
- **PALIATIVO:** se registran atenciones de cuidados paliativos en el Diccionario 502, sin registro de fallecimiento.
- **POSIBLE_REMISIÓN_O_ALTA:** han transcurrido más de 18 meses (540 días) desde la última atención, sin nuevos registros de atención y sin registro de fallecimiento.
- **EN_SEGUIMIENTO_ACTIVO:** la última atención se encuentra dentro de los 18 meses previos a la fecha de corte.
La variable FECHA_CIERRE corresponde a la fecha de fallecimiento para los pacientes fallecidos y a la fecha de última atención para las demás categorías.

## **Tiempos entre hitos**

A partir de los tres hitos se calculan los siguientes intervalos, expresados en días:


| Intervalo | Definición | Fórmula (campos de la base de datos) |
|---|---|---|
| Diagnóstico a Intervención | Tiempo desde el diagnóstico de cáncer colorrectal hasta el inicio del primer tratamiento oncológico. Mide la velocidad de acceso al tratamiento tras el diagnóstico. | FECHA_INICIO_INTERVENCION - FECHA_DIAGNOSTICO_CCR |
| Intervención a Cierre | Tiempo desde el fin del último tratamiento hasta el cierre. Mide el seguimiento postratamiento. | FECHA_CIERRE - FECHA_FIN_INTERVENCION |
| Trayectoria total | Tiempo desde el primer contacto hasta el cierre. | FECHA_CIERRE - PRIMERA_ATENCION |
| Tiempo en sistema | Tiempo entre la primera y última atención registrada en FISSAL. | ULTIMA_ATENCION - PRIMERA_ATENCION |

*Nota: Los intervalos negativos (cuando la fecha de cierre es anterior a la fecha de intervención, lo que puede ocurrir con el valor centinela de fallecimiento) se excluyen de los cálculos de tiempos.** En el intervalo Diagnóstico a Intervención se excluyen, además, 1,131 pacientes (14.1% del subconjunto de referencia) cuyo tratamiento aparece antes del primer registro codificado como CCR; por ello, el n de este intervalo es 6,885 y no 8,016.*

# **Clasificación de ítems de consumo mediante el Diccionario 502**

Cada ítem de consumo registrado en FISSAL (campo Descripcion_Consumo) se clasifica mediante el Diccionario estandarizado de ítems de consumo (versión 502). Este diccionario asigna a cada descripción: (i) una categoría clínica, (ii) una subcategoría, (iii) una atribuibilidad al CCR y (iv) una recomendación de uso en el análisis principal.

## **Normalización de la clave de cruce**

El cruce entre la base FISSAL y el diccionario se realiza sobre una clave normalizada, calculada desde el texto crudo de Descripcion_Consumo mediante los siguientes pasos en orden:

- Convertir a mayúsculas.
- Eliminar espacios dobles.
- Eliminar paréntesis, punto y coma, comas y comillas.
- Convertir a ASCII (eliminar tildes y caracteres especiales).
La misma función se aplica tanto al diccionario como a la base de datos, garantizando que ambos lados usen exactamente la misma lógica.

*Nota: No se utiliza la columna **clave_normalizada** incluida en el archivo del diccionario debido a diferencias en su criterio de normalización. En su lugar, la clave se recalcula a partir del texto original, lo que permitió recuperar aproximadamente el 89 % del costo previamente identificado como "sin clasificar".*

## ** Categorías del diccionario**


| Tipo | Categoría | Descripción |
|---|---|---|
| Tratamiento | Procedimiento quirúrgico | Cirugía de resección y otros procedimientos quirúrgicos |
| Tratamiento | Medicamento oncológico | Quimioterapia sistémica |
| Tratamiento | Radioterapia | Radioterapia externa o braquiterapia |
| Tratamiento | Endoscopía / colonoscopía | Estudios endoscópicos diagnósticos o terapéuticos |
| Soporte | Laboratorio | Hemograma, marcadores tumorales, bioquímica |
| Soporte | Imagenología | Tomografía, ecografía, resonancia magnética |
| Soporte | Medicamento no oncológico | Antieméticos, analgésicos y otros medicamentos de soporte |
| Soporte | Anatomía patológica / biopsia | Diagnóstico histológico |
| Soporte | Transfusión / banco de sangre | Hemoderivados |
| Soporte | Hospitalización / estancia | Costos de internamiento |
| Soporte | Cuidados paliativos | Atención paliativa y de confort |
| Soporte | Consulta / evaluación | Consultas médicas y evaluaciones especializadas |

## ** Ítems sin correspondencia en el diccionario**

Los ítems sin correspondencia en el diccionario reciben una clasificación de respaldo según el campo TipoConsumo. Los registros correspondientes a "Medicamento" se clasifican como "Medicamento no oncológico"; los correspondientes a "Procedimiento", como "Procedimiento no quirúrgico" y los correspondientes a "Insumo", como "Insumo médico". Los casos restantes se mantienen como "Sin clasificar".

Adicionalmente, se generó una propuesta de ampliación del diccionario mediante similitud textual con los ítems previamente clasificados. Las coincidencias se agruparon según su nivel de similitud en alta (≥ 0.75), media (0.50–0.74) y baja (< 0.50). Esta propuesta queda sujeta a validación manual antes de su incorporación al diccionario maestro.

# **Estimación de los costos por paciente al año**

El costo de atención de cada paciente se estima a partir de la suma de los montos netos de todos sus registros de consumo en FISSAL, en dos versiones: nominal (soles corrientes del año de atención) y deflactada (soles constantes de 2024).

## **Deflactación a soles de 2024**

Dado que la base cubre casi diez años, los montos nominales no son directamente comparables entre pacientes que iniciaron su atención en años distintos. Se aplican factores de conversión basados en el Índice de Precios al Consumidor (IPC) del Perú, con 2024 como año base:


| Año | Factor IPC | Interpretación |
|---|---|---|
| 2018 | 1.26 | S/ 1 de 2018 equivale a S/ 1.26 de 2024 |
| 2019 | 1.24 |  |
| 2020 | 1.22 |  |
| 2021 | 1.14 |  |
| 2022 | 1.05 |  |
| 2023 | 1.02 |  |
| 2024 | 1.00 | Año base |
| 2025–2026 | 1.00 | Sin corrección (datos recientes, sin factor definitivo) |

La deflactación se aplica año a año por componente de costo (CRC_ATRIBUIBLE, SOPORTE, NO_ATRIBUIBLE), no como un factor promedio sobre el total nominal. Esto evita sobreestimar el costo real cuando el gasto se concentra en años recientes.

## **Desglose por atribuibilidad al CCR**

El costo total de cada paciente se desglosa en tres componentes:

- **COSTO_CRC_ATRIBUIBLE:** ítems clasificados como "Atribuible/compatible con manejo de CCR". Incluye los tratamientos oncológicos directos y otros recursos estrechamente relacionados con el tumor.
- **COSTO_SOPORTE:** ítems clasificados como "Soporte del episodio de atención oncológica". Incluye laboratorios, imágenes, medicamentos de soporte, hospitalización, etc.
- **COSTO_NO_ATRIBUIBLE:** ítems no atribuibles al CCR (atención por otras enfermedades subsidiadas, vacunas, insumos generales).
## **Métricas reportadas**

Para cada subconjunto de pacientes, el análisis reporta:

- Mediana del costo total deflactado por paciente (métrica principal, robusta frente a valores extremos).
- Media del costo total deflactado (complementaria).
- Costo anualizado: costo total deflactado dividido entre el tiempo en sistema (en años), como proxy del costo por año de atención.
- Desglose por componente: mediana y media de CRC_ATRIBUIBLE, SOPORTE y NO_ATRIBUIBLE, cada uno en soles de 2024.
## **Subconjunto de referencia para los cálculos de costo (FISSAL Regular)**

No todos los pacientes de la cohorte son comparables para el análisis de costos. El subconjunto de referencia se define como Track A + FISSAL Regular:

- **Track A (COMPLETO):** paciente con al menos una intervención oncológica activa registrada.
- **FISSAL Regular:** paciente con 3 o más atenciones registradas, tiempo en sistema ≥ 1 día, y sin ser un outlier de costo.
Los outliers de costo se identifican por grupos de frecuencia de atención: para cada grupo con 5 o más pacientes y 5 o más atenciones se calcula el límite superior como Q3 + 3 × IQR. Los pacientes cuyo costo supera ese límite en su grupo se excluyen del análisis principal.

# **Análisis de hospitalizaciones**

Las hospitalizaciones se detectan por la presencia de un valor no nulo en el campo Fecha_ingreso_hospitalizacion. En la base de datos, cada episodio de hospitalización genera múltiples líneas de consumo (medicamentos, procedimientos e insumos administrados durante la internación) que comparten las mismas fechas de ingreso y alta. Para evitar que el conteo de episodios y días de estancia se multiplique por el número de ítems facturados, los registros se colapsan a nivel de episodio, definido por la combinación única de (paciente, fecha de ingreso, fecha de alta).

A partir de estos episodios se construyen las siguientes métricas:

- **DIAS_ESTANCIA:** diferencia entre la fecha de alta y la fecha de ingreso, expresada en días. Se restringe al rango [0, 365]; los valores fuera de este rango se consideran nulos.
- **N_HOSPITALIZACIONES (por paciente):** número de episodios distintos de hospitalización.
- **DIAS_HOSPITALIZACION_TOTAL (por paciente):** suma de los días de estancia correspondientes a los episodios de hospitalización del paciente.
El campo Tipo_atencion no incluye el valor "HOSPITALIZACION"; únicamente contiene "EMERGENCIA", "AMBULATORIO" y "REFERIDO". Por ello, la identificación de hospitalizaciones se realiza mediante la presencia de las fechas de ingreso y alta, y no a partir del tipo de atención.

# **Otros diagnósticos y comorbilidades**

Como se indicó en la sección 4, se extraen todos los registros de los pacientes CCR, no solo los codificados con C18/C19. Esto permite analizar el costo atribuible a otros diagnósticos concomitantes. Los registros se clasifican en tres grupos:

- **CCR:** registros con diagnóstico de cáncer colorrectal.
- **Otro cáncer (C…, no CCR):** registros con otro tipo de cáncer (p. ej. C16 estómago, C50 mama, C61 próstata).
- **No cáncer:** registros con diagnóstico no oncológico (p. ej. N18 insuficiencia renal crónica, E11 diabetes tipo 2).
Esta desagregación permite estimar qué proporción del costo total de atención es directamente atribuible al CCR y cuánto corresponde a otras condiciones del mismo paciente.

# **Resultados principales e interpretación**

Esta sección presenta los resultados obtenidos al aplicar la metodología descrita en las secciones anteriores, con énfasis en su interpretación, qué significan estos valores para la carga clínica y económica del cáncer colorrectal, más que en la estructura técnica del análisis. Salvo que se indique lo contrario, todas las cifras de costo están expresadas en soles constantes de 2024, y todas las métricas de tiempo, costo y hospitalización corresponden al subconjunto de referencia Track A + FISSAL Regular.

## **Perfil general de la cohorte**

La cohorte identificada comprende 24,394 pacientes con diagnóstico de cáncer colorrectal financiados por FISSAL entre 2016 y 2026. De ellos, 14,307 (58.6%) son mujeres y 10,087 (41.4%) hombres. Por localización del tumor, 24,121 pacientes (98.9%) están codificados como cáncer de colon (C18) y 273 (1.1%) como unión rectosigmoidea (C19); no se registra ningún caso de cáncer de recto (C20) en este período.

Un hallazgo relevante para la interpretación clínica es la proporción de casos de aparición temprana: 2,060 pacientes (8.4% de la cohorte) fueron diagnosticados antes de los 40 años, y 5,104 (20.9%) antes de los 50. Esta proporción es consistente con la tendencia documentada internacionalmente de incremento del cáncer colorrectal en adultos menores de 50 años, y sugiere que este fenómeno también está presente en la población peruana cubierta por FISSAL.

Del total de la cohorte, 8,016 pacientes (32.9%) cuentan con evidencia de tratamiento oncológico activo y trayectoria suficiente (3 o más atenciones) para el análisis detallado de tiempos y costos que se presenta a continuación. La sección “Quiénes quedan fuera del análisis detallado”, al final de este capítulo, explica el perfil de los 16,378 pacientes restantes.

## **Costo de atención: magnitud e interpretación**

El costo total deflactado de atención por paciente, en el subconjunto de referencia, tiene una mediana de S/ 4,802 y una media de S/ 7,997. El desglose por atribuibilidad muestra un patrón que conviene destacar:


| Componente | Mediana | Media | Qué incluye |
|---|---|---|---|
| Tratamiento | S/ 812 | S/ 1,326 | Cirugía, quimioterapia, radioterapia, endoscopía |
| Soporte | S/ 3,240 | S/ 5,942 | Laboratorio, imágenes, medicamentos no oncológicos, hospitalización, etc. |
| No atribuible | S/ 294 | S/ 729 | Atención por otras condiciones, vacunas, insumos generales |

El componente de “soporte” cuesta, en promedio, cerca de 4.5 veces más que el tratamiento oncológico directo. Esto es contraintuitivo frente a la percepción común de que “la cirugía” o “la quimioterapia” concentran el gasto: en la práctica, la carga económica del cáncer colorrectal está dispersa en todo el aparataje diagnóstico y de soporte que rodea el tratamiento (exámenes de laboratorio, imágenes, medicamentos de acompañamiento, días de hospitalización), precisamente el tipo de gasto que, sin un mecanismo de cobertura catastrófica como FISSAL, con mayor facilidad terminaría cayendo directamente sobre la familia, en vez de concentrarse en un evento grande y visible como una cirugía.

Para dimensionar la magnitud de este costo, se compara contra la Remuneración Mínima Vital (RMV) vigente en Perú, S/ 1,130 mensuales (D.S. N.° 006-2024-TR, desde enero de 2025):


|  | Costo mediano | Equivalente en meses de RMV | Costo medio | Equivalente en meses de RMV |
|---|---|---|---|---|
| Subconjunto de referencia | S/ 4,802 | 4.3 meses | S/ 7,997 | 7.1 meses |

Esta comparación tiene un propósito de magnitud, no de gasto de bolsillo: el costo reportado es el que FISSAL efectivamente cubre, no lo que paga la familia. Interpretarlo como "lo que le costaría al hogar" sería incorrecto, precisamente porque describe lo contrario, la carga económica que este mecanismo de aseguramiento catastrófico absorbe en nombre del paciente. Su utilidad está en dar una noción de escala: un costo mediano equivalente a 4.3 meses de RMV, y de hasta 7.1 meses en promedio, dimensiona la magnitud de la carga que representaría este proceso si no existiera un mecanismo de cobertura catastrófica como FISSAL.

Dicho esto, la cobertura de FISSAL no es integral. La literatura sobre gasto catastrófico en salud (OPS) documenta de forma consistente una serie de gastos que sí recaen directamente sobre el paciente y su familia, y que esta base de datos no permite cuantificar: transporte hacia el centro de atención, especialmente relevante para pacientes de regiones fuera de Lima, alojamiento cuando el tratamiento se realiza en otra ciudad, medicamentos o insumos no incluidos en el petitorio, y la pérdida de ingresos del paciente o de su cuidador durante el proceso. Este es, en sentido estricto, el gasto de bolsillo real del proceso oncológico, y queda fuera del alcance de los datos de FISSAL analizados en este informe.

## **Tiempos de acceso al tratamiento**

La tabla siguiente resume, para el subconjunto de referencia, los intervalos definidos en la sección “Tiempos entre hitos”, ya con sus valores observados:


| Intervalo | n | Mediana (días) | Media (días) | P95 (días) |
|---|---|---|---|---|
| Diagnóstico a Intervención | 6,885 | 31 | 133 | 730 |
| Intervención a Cierre | 7,999 | 152 | 332 | 1,287 |
| Trayectoria total | 8,016 | 641 (1.8 años) | 875 (2.4 años) | 2,430 |

La mediana de 31 días desde el diagnóstico hasta el inicio del tratamiento oncológico (equivalente a 4.4 semanas) se ubica dentro del rango de referencia internacional para el intervalo diagnóstico-tratamiento (2 a 6 semanas en sistemas de salud de Reino Unido, Australia o Dinamarca). Sin embargo, la mediana por sí sola oculta una cola larga de espera: el percentil 95 llega a 730 días, es decir, 1 de cada 20 pacientes del subconjunto de referencia enfrenta una espera de hasta 2 años entre su diagnóstico y el inicio de tratamiento oncológico activo. Es este subgrupo, no la mediana, el que concentra el mayor riesgo clínico y económico asociado a la demora.

## **Sub-perfiles de tratamiento: pacientes con y sin quimioterapia (A.1 / A.2)**

Dentro del subconjunto de referencia, los pacientes se dividen en dos sub-perfiles según hayan recibido o no algún registro de quimioterapia en la categoría “Medicamento oncológico” del diccionario 502, con el mismo criterio descrito en la sección 5.2.2.

Los pacientes que reciben quimioterapia (A.2, 40.2% del subconjunto de referencia) cuestan en mediana 2.3 veces más que quienes no la reciben (S/ 7,358 vs. S/ 3,200), se hospitalizan con mayor frecuencia (79.2% vs. 66.0%) y por más tiempo (mediana 7 días vs. 0, entre todos los pacientes de cada sub-perfil) e ingresan en estado grave con mayor frecuencia (79.9% vs. 66.9%), un patrón coherente con perfiles clínicos más complejos. En cambio, el tiempo desde el diagnóstico hasta el inicio de la intervención es similar en ambos sub-perfiles (mediana de 32 días en A.1 y 30 días en A.2).

La mortalidad de A.2 (37.4%) es notablemente mayor que la de A.1 (28.0%). Esta diferencia no debe interpretarse como que la quimioterapia empeora el pronóstico: es consistente con confusión por indicación, a quien se le administra quimioterapia suele ser, precisamente, porque su caso es clínicamente más avanzado o complejo desde el inicio, no al revés. Sin información de estadio tumoral (no disponible en esta base, ver Limitaciones), no es posible aislar el efecto del tratamiento del efecto de la severidad de base.

## **Hospitalización**

En el subconjunto de referencia, 5,718 pacientes (71.3%) registran al menos un episodio de hospitalización, con una mediana de 2 episodios por paciente (media 5.3). El 70.7% de los episodios de hospitalización (21,409 de 30,296) tienen una estancia de 0 días, ingreso y alta el mismo día, compatible con cirugía ambulatoria o procedimientos breves, lo cual es un patrón esperado y no un error de registro. Entre los episodios con estancia mayor a 0 días, la mediana es de 6 días (media 8.6).

Por esta razón conviene distinguir dos métricas de costo de hospitalización que responden preguntas distintas: el costo de un episodio individual tiene una mediana de solo S/ 72 (media S/ 999), arrastrada hacia abajo por la mayoría de episodios cortos o ambulatorios; en cambio, el costo de hospitalización acumulado por paciente, sumando todos sus episodios a lo largo de la trayectoria, tiene una mediana de S/ 3,224 (media S/ 5,295), y es esta la cifra que responde a “cuánto le cuesta a un paciente hospitalizarse en total durante su proceso oncológico”.

## **Severidad al ingreso y mortalidad**

La mortalidad observada varía fuertemente según la gravedad del primer contacto del paciente con FISSAL (INGRESO_GRAVE: emergencia u hospitalización en la primera atención):


| Localización | Ingreso ambulatorio | Ingreso grave |
|---|---|---|
| Colon | 21.9% (n=2,206) | 35.5% (n=5,662) |
| Unión rectosigmoidea | 10.0% (n=30) | 45.8% (n=118) |

La mortalidad es mayor entre quienes ingresan en un estado ya grave que entre quienes lo hacen de forma ambulatoria, un patrón esperable clínicamente y consistente en ambas localizaciones: en colon es 1.6 veces mayor (35.5% frente a 21.9%) y en unión rectosigmoidea, 4.6 veces mayor (45.8% frente a 10.0%). El subgrupo de unión rectosigmoidea es pequeño (n=30 y n=118), por lo que sus porcentajes deben leerse como indicativos de una tendencia, no como una estimación precisa.

## **Fallecidos**

De los 8,016 pacientes del subconjunto de referencia, 2,549 (31.8%) constan como fallecidos. La distribución del tiempo transcurrido en FISSAL hasta el cierre por fallecimiento muestra que 70.7% de los fallecidos (1,803) permaneció 2 o más años en el sistema, mientras que solo 3.8% (97) falleció dentro del primer trimestre. Recuérdese que, como se detalla en la sección de Completitud de la información, el 84.6% de estas fechas de cierre son en realidad la fecha de última atención, no la fecha real de defunción, por lo que esta distribución debe leerse como un límite inferior del tiempo transcurrido, no como cronología exacta.

El costo mediano también varía por tramo de fallecimiento: el más alto corresponde a quienes fallecen entre 1 y 2 años (S/ 6,532); quienes fallecen después de 2 o más años, que representan 70.7% del total de fallecidos, tienen un costo mediano de S/ 5,593, mientras que quienes fallecen en el primer mes tienen un costo mediano de S/ 1,539, consistente con trayectorias más cortas y, probablemente, presentaciones más agresivas o diagnósticos más tardíos.

## **Evolución anual del gasto**

El gasto total deflactado del subconjunto de referencia creció de forma sostenida, de S/ 113,513 en 2018 a S/ 13,139,214 en 2025, lo que representa un incremento superior a 100 veces. Este incremento está asociado, en parte, al aumento del número de pacientes atendidos por FISSAL a lo largo del período. Asimismo, la comparación interanual debe interpretarse considerando que los años presentan diferente volumen de observación y que 2026 corresponde a un período parcial, con información disponible únicamente hasta el 31 de marzo de 2026. Por ello, el gasto registrado para 2026 no debe interpretarse como una disminución respecto de 2025.

## **Criterios de exclusión del análisis detallado**

El análisis de tiempos y costos de las secciones anteriores se concentra en los 8,016 pacientes (32.9% de la cohorte) con evidencia de tratamiento oncológico activo y trayectoria suficiente para una reconstrucción confiable. Los 16,378 pacientes restantes no fueron excluidos por no tener cáncer colorrectal ni por error de registro: su perfil de datos simplemente no permite el mismo nivel de detalle. El cruce completo de TRACK (evidencia de tratamiento) y FISSAL_REGULAR (3 o más atenciones) sobre el total de la cohorte es el siguiente:


|  | FISSAL Regular (3+ atenciones) | No regular (1-2 atenciones) |
|---|---|---|
| Track A (evidencia de tratamiento) | 8,016 (32.9%) — mediana 25 atenciones, mortalidad 31.8% | 3,079 (12.6%) — mediana 1 atención, mortalidad 10.7% |
| Track B (solo consulta/evaluación) | 4,995 (20.5%) — mediana 6 atenciones, mortalidad 25.1% | 8,304 (34.0%) — mediana 1 atención, mortalidad 8.2% |

Los 3,079 pacientes (12.6%) con evidencia de un evento de tratamiento, pero una sola atención registrada probablemente tuvieron ese evento documentado en FISSAL mientras el resto de su trayectoria ocurrió fuera de este registro, o fueron derivados a otra institución. Los 8,304 pacientes (34.0%) solo registran una atención sin evidencia de tratamiento, compatible con diagnóstico reciente, una primera consulta sin continuidad, o egreso temprano del sistema.

La mortalidad notablemente más baja en ambos grupos “no regulares” no debe leerse como mejor pronóstico: es, con alta probabilidad, un artefacto de la ventana de observación, una trayectoria de una sola atención tiene mecánicamente menos tiempo dentro de FISSAL para que se registre un desenlace fatal.

Un control de calidad adicional, relevante para la interpretación de cualquier cifra de “costo total del subconjunto de referencia”: al extraer todos los registros de los 8,016 pacientes, el gasto total asciende a S/ 60,942,529, del cual solo 74.6% es atribuible al cáncer colorrectal. El 20.7% corresponde a otros cánceres que estos mismos pacientes también padecen, el más frecuente, por lejos, es el cáncer de estómago, con 1,392 pacientes, y el 4.7% restante a condiciones no oncológicas.

## **Gasto de bolsillo**

El costo directo de atención reportado en la sección 10.2 (mediana de S/ 4,802 por paciente) es el que FISSAL cubre, no es lo que paga la familia. Existe, además, un gasto que recae directamente sobre el hogar y que la base de FISSAL no registra. Para dimensionarlo se utilizó la Encuesta Nacional de Hogares (ENAHO) 2025, módulo de Salud.

Se consideró el monto que el hogar pagó de su bolsillo por los servicios de salud que efectivamente utilizó: consultas, medicinas, análisis, imágenes, otros exámenes, hospitalización e intervenciones quirúrgicas. Cada monto se llevó a un año según su período de referencia (4 semanas, 3 meses o 12 meses) y se ponderó con el factor de expansión de la encuesta. La población de análisis son los adultos de 40 años o más, grupo de edad que concentra el cáncer colorrectal.

La ENAHO no identifica a las personas con cáncer. Lo más cercano es la pregunta sobre enfermedad crónica, y las preguntas sobre hospitalización o cirugía en los últimos 12 meses. Por ello, las cifras describen el gasto de adultos con enfermedad crónica o con un evento hospitalario, y no el de un paciente con cáncer colorrectal. Se presentan como una referencia de magnitud.


| Escenario | Población de referencia (adultos de 40 años o más) | Gasto de bolsillo anual por persona |
|---|---|---|
| Bajo | Con enfermedad crónica (promedio, incluye a quienes no gastaron) | S/ 585 |
| Base | Cuyo hogar pagó una hospitalización o cirugía en los últimos 12 meses | S/ 4,023 (mediana S/ 2,300) |
| Alto | Mismo grupo que el escenario base, percentil 75 | S/ 5,320 |

En el escenario base, el gasto de bolsillo anual equivale a cerca del 84% del costo mediano que FISSAL cubre por paciente (S/ 4,802). Si se aplicara a la duración mediana de la trayectoria clínica en FISSAL (1.8 años), el gasto alcanzaría unos S/ 7,200 por paciente.

### **Qué significa ese gasto para el hogar (gasto catastrófico)**

Un gasto de salud se considera catastrófico cuando absorbe una proporción tan alta del presupuesto del hogar que obliga a recortar otros consumos básicos. Se usó el umbral habitual de más del 25% del gasto total anual del hogar. Con la Sumaria de la ENAHO 2025 se dividió a los hogares en cinco grupos de igual tamaño según su gasto por persona (Q1 es el más pobre) y se calculó qué proporción superaría el umbral si enfrentara un gasto de bolsillo anual de ese monto. Es una simulación, no se observa a hogares con un paciente de cáncer colorrectal, sino que se asigna un gasto hipotético a todos los hogares.


| Grupo de hogares | Gasto anual de S/ 585 (escenario bajo) | Gasto anual de S/ 4,023 (escenario base) |
|---|---|---|
| Q1 | 1% | 64% |
| Q3 | 0% | 22% |
| Q5 | 0% | 7% |
| Total | 0% | 25% |

El mismo gasto es casi irrelevante para el quintil más alto y catastrófico para la mayoría de hogares del más pobre, que es el perfil de los asegurados del SIS cubiertos por FISSAL. Esta cifra no debe leerse como el porcentaje de pacientes con cáncer colorrectal que sufre un gasto catastrófico.

### **Limitaciones**

La ENAHO no distingue el cáncer colorrectal de otras enfermedades; el gasto de un paciente oncológico probablemente sea mayor. No se incluyen transporte ni alojamiento, que la literatura señala como componentes relevantes, en particular para pacientes que se atienden fuera de su región de residencia.

Quienes tienen hospitalización o cirugía pagadas por el hogar se atienden, en una proporción importante, en establecimientos privados o fuera de su seguro; la cifra puede no ser representativa de pacientes atendidos plenamente por FISSAL, cuya cobertura reduce el gasto directo.

### **Referencias metodológicas para futuras investigaciones**

Esta sección no forma parte de los resultados principales, resume cómo la literatura mide el gasto de bolsillo en cáncer colorrectal, en qué se diferencia de lo hecho aquí y qué podría mejorarse en un estudio futuro. La literatura más sólida sobre cómo se mide en otros estudios se diferencia de este análisis en tres aspectos metodológicos:

- Población: mide el gasto en pacientes con CCR identificados, no en un grupo aproximado. En países de ingreso medio el referente es la cohorte prospectiva, con entrevista al inicio del tratamiento y seguimiento a las 6 semanas, 3 y 6 meses, que registra gastos médicos, no médicos (transporte, alojamiento, alimentación) e ingreso perdido (CROCODILE Study Group, 2022; ACTION Study Group, 2015). En India, el 90.1% de los hogares con un paciente con CCR tuvo gasto catastrófico a los 6 meses, y el gasto no médico representó el 22% del gasto de bolsillo.
- Atribución: estima el gasto adicional que causa el cáncer, comparando a los pacientes con personas sin cáncer antes y después del diagnóstico (Rose et al., 2025) o restando el gasto del año previo (Nguyen et al., 2025; Chin et al., 2017), en lugar de reportar el gasto bruto.
- Gasto catastrófico: se calcula hogar por hogar con el ingreso o gasto real de cada uno, con varios umbrales (de 10% a 40%) y por capacidad de pago, y se complementa con el gasto empobrecedor (OMS y Banco Mundial, 2023; Huang et al., 2017).
Otros estudios aportan técnicas puntuales: separar el gasto por fases del tratamiento, ya que se concentra alrededor de la cirugía (Paro et al., 2022), usar modelos de dos partes por la alta proporción de personas sin gasto (Harris et al., 2020) y expresar el gasto en dólares por mes y como proporción del ingreso del hogar para compararlo entre países (Iragorri et al., 2021). Los estudios de EE. UU. utilizan registros de aseguradoras y definen el gasto de bolsillo como copagos, coseguros y deducibles. Esta definición no es aplicable al SIS, por lo que su principal aporte para este análisis radica en el diseño metodológico, más que en la fuente de datos.

Los datos de la ENAHO no permiten identificar a pacientes con cáncer, atribuir los gastos al CCR ni conocer el estadio de la enfermedad y los gastos no médicos asociados al tratamiento. Por ello, el gasto catastrófico estimado corresponde a una simulación y no a una medición directa. Por su parte, las entrevistas de la FPC recogen gastos médicos y no médicos, así como las formas de financiamiento del hogar, pero no incluyen información sobre el ingreso o gasto total del hogar, necesario para calcular el indicador.

Para mejorar el análisis, se propone estimar el gasto catastrófico observado por hogar con la ENAHO, incorporando la capacidad de pago, el gasto empobrecedor, la afiliación al SIS y el diseño muestral. Asimismo, las entrevistas de la FPC podrían incluir el ingreso mensual del hogar y el gasto por fases de atención. A futuro, una cohorte prospectiva de pacientes con CCR vinculada a FISSAL permitiría comparar la cobertura del fondo con los gastos asumidos por las familias.

# **Fuentes complementarias: EsSalud y SIS**

Adicionalmente al análisis de la cohorte FISSAL, se exploraron dos fuentes complementarias: EsSalud y el Seguro Integral de Salud (SIS). Ninguna de las dos es integrable con la cohorte FISSAL a nivel de paciente, no existe un identificador común entre ellas y ninguna de las dos captura el costo de facturación completa de un episodio oncológico del modo en que lo hace FISSAL. Se presentan aquí no como fuentes comparables, sino por el valor genuino que aportan de forma independiente: dimensionar la magnitud de la enfermedad fuera del radar de FISSAL y, en el caso de EsSalud, complementar precisamente el segmento diagnóstico que la cohorte FISSAL no cubre en este período.

## **Análisis EsSalud – GCOP**

### **Base recibida y construcción de pacientes**

Se solicitó a EsSalud, vía acceso a la información pública, una base de pacientes con diagnóstico de cáncer de colon (C18-C19) y cáncer de recto (C20) para el período 2016-2026. La respuesta recibida de la Gerencia Central de Prestaciones de Salud consiste en 101,119 registros de consulta ambulatoria. La base no contiene campos de costo ni fechas reales de hospitalización desagregadas, información que el área responsable confirmó no tener disponible en esta fuente.

El DNI se encuentra parcialmente enmascarado, con cuatro dígitos centrales ocultos. Para aproximar la identificación de pacientes únicos, se construyó un identificador probabilístico combinando el DNI enmascarado, el sexo y una fecha de nacimiento implícita, calculada a partir de la edad exacta registrada en cada atención y la fecha correspondiente. Este procedimiento permitió identificar 17,534 pacientes candidatos.

### **Principales hallazgos**

El principal hallazgo de esta fuente es de carácter diagnóstico. El 96.4% de los registros de EsSalud corresponde al código C20 (cáncer de recto), mientras que la cohorte FISSAL analizada en este informe no registra pacientes con este código durante el mismo período. Esta diferencia se desarrolla con mayor detalle en la sección de Limitaciones, en "Cobertura diagnóstica de FISSAL".

En este sentido, GCOP constituye una fuente complementaria a FISSAL: mientras la cohorte FISSAL permite analizar con mayor detalle la trayectoria asistencial y los costos asociados al cáncer de colon financiado por el fondo, GCOP aporta información sobre el volumen y las características de la demanda ambulatoria oncológica registrada en EsSalud, con una presencia predominante de cáncer de recto.

De los 17,534 pacientes candidatos identificados, 6,367 (36.3%) presentan evidencia de tratamiento activo, cirugía, hospitalización o radioterapia, en algún momento de su historial de consultas.

## **Análisis SIS - Seguro Integral de Salud**

### **Naturaleza y alcance de los datos SIS**

Los datos disponibles del Seguro Integral de Salud (SIS) corresponden a registros de atención y consumo de pacientes con diagnóstico de cáncer colorrectal (CCR) cuya atención fue financiada directamente por el SIS. Esta población es distinta de la cohorte FISSAL analizada en este informe: no existe un cruce directo entre ambas cohortes y las fuentes presentan diferencias tanto en su estructura como en el tipo de información registrada.

Se identificaron 1,315 pacientes con diagnóstico de CCR, de los cuales el 86.8% corresponde a diagnósticos definitivos y el 13.2% restante (174 pacientes) a diagnósticos repetitivos; no se registran diagnósticos presuntivos. Ninguno de los registros de esta base presenta financiamiento FISSAL, por lo que se trata de una población íntegramente diferenciada de la cohorte FISSAL.

La principal limitación estructural de esta fuente es la baja continuidad de los registros: el 91.6% de los pacientes cuenta con una única atención registrada. Esta característica limita el análisis longitudinal y tiene las siguientes implicancias:

- No permite reconstruir trayectorias clínicas: una sola atención no permite identificar una secuencia de diagnóstico, tratamiento y seguimiento.
- No permite calcular tiempos entre hitos asistenciales: no es posible distinguir de manera consistente eventos como el primer contacto, inicio o finalización del tratamiento.
- No permite estimar el costo de una trayectoria completa: los registros de SIS corresponden a atenciones y consumos puntuales y no representan necesariamente el costo acumulado de la atención de un paciente con CCR.
Asimismo, los costos registrados en esta fuente no son directamente comparables con los de FISSAL. En SIS se observan principalmente copagos e ítems puntuales, mientras que la base FISSAL permite identificar la facturación asociada a episodios de atención de manera más completa.

### **Análisis exploratorio**

El análisis del SIS es exploratorio y descriptivo, orientado a dimensionar la población con CCR atendida directamente por el seguro. Los pacientes identificados fuera del mecanismo de cobertura catastrófica de FISSAL que se registran en el extracto pasan de 46 en 2018 a 356 en 2025, aumento que puede reflejar una mejor captura de la información y no necesariamente un mayor número de casos. Esta fuente complementa la caracterización de la población atendida en el sistema público, pero no se utiliza para estimar costos de trayectoria ni compararlos con la cohorte FISSAL, debido a la baja continuidad de los registros y las diferencias en la estructura de costos.

# **Estimación del ausentismo laboral por licencias**

El costo directo de atención reportado en la sección 10.2, mediana de S/ 4,802 por paciente es el que FISSAL efectivamente cubre. Como se señala en esa misma sección, hay un componente adicional de gasto de bolsillo que la base de datos de FISSAL no permite cuantificar: la pérdida de ingresos del paciente o de su cuidador durante el proceso oncológico. Esta sección y la siguiente abordan ese componente, usando fuentes complementarias a FISSAL.

## **Metodología**

La fuente utilizada es la Encuesta Nacional de Uso del Tiempo 2024 (ENUT, INEI), que permite identificar las horas de trabajo que se dejan de realizar durante la semana de referencia y los principales motivos asociados.

Para ello, se consideran tanto los casos en que una persona ocupada no trabajó durante toda la semana como aquellos en los que trabajó menos horas de las que realiza habitualmente. En ambos casos, la encuesta recoge el motivo de la ausencia o reducción de la jornada, incluyendo razones relacionadas con enfermedad, dolencia, accidentes, licencias de salud y responsabilidades de cuidado familiar. A partir de esta información se estiman las horas de trabajo perdidas asociadas a motivos de salud y cuidado, diferenciando entre la ausencia completa de la jornada y la reducción parcial de las horas trabajadas.

Combinando estas dos preguntas con las horas normales de trabajo declaradas y las horas efectivamente trabajadas en la semana de referencia, se calcula, para cada trabajador dependiente, cuántas horas de su jornada habitual se perdieron esa semana y por qué motivo. El resultado se pondera con el factor de expansión muestral de la encuesta para obtener una cifra representativa a nivel nacional.

El valor monetario de cada hora se calculó de la misma fuente (ENUT 2024): entre los trabajadores dependientes pagados mensualmente, con horas e ingreso válidos, el salario/hora promedio ponderado a nivel nacional es de S/ 11.55.

## **Resultado**

De cada 100 horas de la jornada normal de un trabajador dependiente en Perú, 0.63 horas se pierden por razones de salud (enfermedad, dolencia o accidente, cualquiera de las dos preguntas). Llevado a un año:


| Métrica | Valor |
|---|---|
| Horas perdidas por salud al año, por trabajador | 15.6 horas (≈ 2 días de 8 horas) |
| Valor monetario (a S/ 11.55/hora) | S/ 181 al año |
| Equivalente en Remuneración Mínima Vital (RMV, S/ 1,130 mensuales) | 0.16 meses |

Este orden de magnitud es consistente con el hallazgo de un estudio sobre el personal de SEDAPAL (Rodríguez García, 2014), que documentó 136,873 días perdidos por enfermedad para una planilla de entre 1,684 y 2,408 trabajadores a lo largo de 13 años, aproximadamente 5.3 días por trabajador al año, medido con registros administrativos de descansos médicos en lugar de una encuesta de una sola semana de referencia como la ENUT.

## **Ausentismo asociado al tratamiento oncológico**

Aplicar la tasa poblacional a un paciente con cáncer subestimaría su realidad, el tratamiento oncológico implica ausencias mucho más frecuentes y prolongadas que las que capta una encuesta de uso del tiempo. Por ello, el ausentismo se estimó a partir de la duración real del tratamiento de cada paciente en FISSAL, para el subconjunto de referencia (8,016 pacientes).

Para cada paciente se calculó la duración de su intervención oncológica, como los días transcurridos entre la fecha de inicio y la de fin de la intervención registradas en FISSAL. La mediana de esa duración es de 68 días. En el 41.0% de los pacientes es de 0 días, porque su intervención se limita a un único día.

FISSAL registra prestaciones facturadas y no el tiempo que el paciente se ausenta de su trabajo. Por ello se asumió que el paciente permanece fuera del trabajo durante una fracción de la duración de su tratamiento, y se plantearon tres escenarios:


| Escenario | Fracción de la duración del tratamiento fuera del trabajo | Mediana de días fuera del trabajo (pacientes con cirugía o quimioterapia) |
|---|---|---|
| Bajo | 25% | 37 días |
| Base | 50% | 74 días |
| Alto | 75% | 112 días |

Se aplicaron, además, las siguientes reglas:

- El periodo fuera del trabajo se limitó a 365 días por paciente.
- Si los días de hospitalización superan el periodo calculado, se toman los días de hospitalización.
- Los días calendario se convirtieron a días laborables (5 de cada 7).
- Cada día laborable se valorizó con una jornada de 8 horas a S/ 11.55 por hora (S/ 92.4 por día).

| Escenario | Días laborables perdidos por paciente | Costo por paciente que trabaja |
|---|---|---|
| Bajo | 54 | S/ 5,006 |
| Base | 79 | S/ 7,341 |
| Alto | 95 | S/ 8,741 |

En el escenario base, un paciente que trabaja pierde en promedio 79 días laborables, valorizados en S/ 7,341. Esto equivale a unas 22 veces el valor que resulta de aplicar la tasa poblacional (S/ 326 durante los 1.8 años de la trayectoria mediana). Entre los pacientes con cirugía o quimioterapia (71.9% del subconjunto), el costo medio del escenario base es de S/ 9,420.

Estos valores corresponden a pacientes que trabajan. Para estimar el costo en el subconjunto de referencia se tuvo en cuenta que solo el 60.8% de los pacientes tiene menos de 65 años y que la tasa de empleo nacional es de 66.1% (tasa de actividad de 69.5% por tasa de empleo de 95.1%, INEI, 2025). Con ello se esperan unos 3,221 pacientes ocupados, y un costo agregado para el subconjunto de referencia de S/ 23.6 millones en el escenario base (S/ 16.1 millones en el escenario bajo y S/ 28.2 millones en el alto).

## **Limitaciones de esta estimación**

- La fracción de la duración del tratamiento en que el paciente está fuera del trabajo es un supuesto del estudio, calibrado con la literatura internacional y no con mediciones en pacientes peruanos; por eso se presenta en escenarios. Una validación con datos de descansos médicos de EsSalud o con especialistas mejoraría la estimación.
- La duración del tratamiento se mide entre la primera y la última prestación de la intervención oncológica registradas en FISSAL, que puede incluir periodos sin atención activa. Para evitar sobrestimar, se limitó a 365 días por paciente.
- Los pacientes con una intervención de un solo día (41.0%) solo aportan sus días de hospitalización, por lo que la estimación puede subestimar las ausencias por consultas, exámenes de control o radioterapia, y las que ocurren durante el seguimiento posterior al tratamiento.
- Los trabajadores independientes e informales, que son una parte importante de la fuerza laboral peruana, no cuentan con licencia médica con continuidad de ingreso; su pérdida real, cuando enferman, probablemente sea mayor.
- El costo agregado corresponde al subconjunto de referencia de la cohorte FISSAL y no al total de pacientes con cáncer colorrectal del país.
- La tasa poblacional de la ENUT, usada como referencia, se basa en una sola semana de referencia por hogar, por lo que es un promedio menos robusto que uno calculado a partir de registros anuales.
# **Pérdida de productividad por discapacidad o muerte prematura**

Este punto tiene dos componentes de naturaleza distinta, que se presentan por separado para evitar doble conteo: la producción que deja de generar un paciente que fallece antes de la edad de jubilación, y la de su cuidador familiar, que sigue con vida y trabajando, pero con menos horas disponibles mientras dura el cuidado.

## **Muerte prematura del paciente**

### **Metodología**

Se utilizó el enfoque de capital humano (ECH), el método más empleado en la literatura de economía de la salud para este tipo de estimación, siguiendo la formulación de Mosegui et al. (2023) para países sudamericanos:

- Se identificaron todas las muertes por cáncer colorrectal registradas en SINADEF (Registro Nacional de Defunciones) durante 2025, el último año con información completa, definidas como aquellas cuya causa básica de defunción corresponde a los códigos CIE-10 C18-C20. A diferencia de FISSAL, SINADEF cubre a toda la población fallecida en el país, independientemente de su afiliación a un seguro.
- Para cada muerte ocurrida antes de los 65 años (edad de jubilación de referencia), se calcularon los años potenciales de vida productiva perdidos (APVP) como la diferencia entre 65 y la edad al fallecer.
- El valor de cada año de vida productiva perdido se calculó como el ingreso anual promedio (INEI, Encuesta Permanente de Empleo Nacional, 2025: S/ 1,887 mensuales), ajustado por la tasa de actividad (69.5%) y la tasa de empleo (95.1%) nacionales, y descontado a valor presente con una tasa del 3% anual, la misma convención que usa la literatura internacional de referencia.
A diferencia del estudio de Mosegui et al., que usa el salario mínimo como proxy aquí se utilizó el ingreso promedio de INEI, más representativo del ingreso real de un trabajador peruano, por eso el costo por muerte que resulta es más alto que el del estudio de referencia, y no debe leerse como una discrepancia o un error.

### **Resultado**

En 2025 se registraron 1,958 muertes por cáncer colorrectal (causa básica) en Perú, de las cuales 564 (28.8%) ocurrieron antes de los 65 años, el resto, la mayoría, en personas ya en edad de jubilación, para quienes el método de capital humano no imputa pérdida de productividad laboral formal.


| Métrica | Valor |
|---|---|
| Años potenciales de vida productiva perdidos, promedio por muerte prematura | 11.7 años |
| Costo de productividad por muerte prematura (valor presente) | S/ 133,800 |
| Equivalente en meses de Remuneración Mínima Vital | 118.4 meses (≈ 10 años) |
| Costo total agregado (564 muertes, Perú, 2025) | S/ 75.5 millones |

Para contexto de magnitud: el costo de productividad de una sola muerte prematura (S/ 133,800) equivale a 28 veces el costo médico mediano por paciente que cubre FISSAL (S/ 4,802, sección 10.2). Dicho de otro modo, lo que la sociedad deja de producir cuando un paciente de CCR muere antes de tiempo es un orden de magnitud mayor que lo que cuesta tratarlo médicamente.

## **Cuidador informal**

### **Metodología**

A diferencia del punto anterior, aquí se buscó una estimación específica de pacientes con cáncer colorrectal, construida en dos pasos:

- Población de pacientes: se tomaron los pacientes de la cohorte FISSAL con trayectoria activa durante 2024, 10,599 de los 24,394 pacientes históricos, y se calcularon las semanas de esa trayectoria que caen dentro del año 2024 para cada paciente.
- Se plantearon tres escenarios:
- Pacientes con cuidador: 60% (bajo), 75% (base) y 90% (alto).
- Horas de cuidado por semana: 10 (bajo), 20 (base) y 30 (alto).
- Las horas estimadas de cuidado se valorizaron a S/ 11.55 por hora, correspondiente al salario por hora de la ENUT 2024.
### **Resultados**


| Escenario | % pacientes con cuidador | Horas/semana | Costo anual por paciente | Equivalente en meses de RMV |
|---|---|---|---|---|
| Bajo | 60% | 10h | S/ 2,086 | 1.8 meses |
| Base | 75% | 20h | S/ 5,215 | 4.6 meses |
| Alto | 90% | 30h | S/ 9,387 | 8.3 meses |

En el escenario base, el costo de oportunidad del cuidador informal (S/ 5,215 al año por paciente) es del mismo orden de magnitud que el costo médico mediano que FISSAL cubre por paciente (S/ 4,802, sección 10.2), es decir, lo que la familia pierde en ingresos del cuidador es comparable a lo que el fondo gasta en la atención médica del paciente. Esta comparación ilustra por qué el gasto de bolsillo real del proceso oncológico, como se anota en la sección 10.2, va bastante más allá de lo que FISSAL cubre o de lo que este informe puede cuantificar con la base de datos disponible.

## **Limitaciones de esta estimación**

- **Muerte prematura:** el método de capital humano considera la pérdida de productividad laboral formal hasta la edad de jubilación. Por ello, no incorpora la productividad potencial de las personas que fallecen después de los 65 años, quienes representaron el 71.2% de las muertes por CCR en 2025. Esto puede generar una subestimación del costo asociado a la pérdida de productividad.
- **Cuidador informal:** los parámetros utilizados para estimar la proporción de pacientes con cuidador y las horas de cuidado semanal provienen de estudios internacionales y no de evidencia específica para cáncer colorrectal en Perú. Por ello, los resultados se presentan mediante escenarios bajo, base y alto.
- **Cobertura de la población:** la estimación del costo del cuidador informal se basa en los 10,599 pacientes con trayectoria activa en FISSAL durante 2024. Esta población no incluye a pacientes con CCR atendidos exclusivamente por EsSalud, el sector privado u otras modalidades de atención fuera de FISSAL.
- **Desagregación de los parámetros:** las estimaciones utilizan tasas de descuento, actividad, empleo e ingresos promedio a nivel nacional, sin diferenciación por edad o sexo. La disponibilidad de parámetros desagregados permitiría una estimación más precisa, considerando las diferencias en los perfiles de mortalidad y cuidado según estas características.
## **Referencias metodológicas para futuras investigaciones**

Esta sección no forma parte de los resultados principales y resume cómo la literatura mide el impacto económico del cáncer sobre el trabajo, en qué se diferencia de este análisis y qué podría mejorarse en futuras investigaciones. La literatura presenta tres diferencias metodológicas principales:

- **Método de valoración:** el enfoque de capital humano valora toda la producción perdida, mientras que el costo de fricción considera solo el tiempo necesario para reemplazar al trabajador (Gol-Montserrat et al., 2017). Se recomienda reportar ambos como análisis principal y de sensibilidad.
- **Muerte prematura:** los estudios valoran los años de vida laboral perdidos según los ingresos por edad y sexo, ajustados por desempleo y descontados al 3% (Darbà y Marsà, 2020; Mosegui et al., 2023).
- **Pérdidas laborales:** se miden los días de contacto con el sistema de salud y los cambios en empleo e ingresos después del diagnóstico. Los estudios encuentran menor empleo, reducción de horas trabajadas e ingresos más bajos (Gupta et al., 2025; Moran et al., 2011; Heinesen y Kolodziejczyk, 2013; Statistics Canada, 2014). También se consideran el tiempo de cuidado familiar y el impacto de la salud mental en la productividad (Urwin et al., 2021; So et al., 2022).
Los datos disponibles no permiten identificar los días de ausencia laboral de pacientes con CCR, compararlos con un grupo de referencia ni seguir su situación laboral en el tiempo. Por ello, no es posible estimar el efecto causal del cáncer sobre el empleo y los ingresos. Además, los parámetros de ausentismo y cuidado provienen de supuestos o estudios internacionales, los ingresos son promedios nacionales sin desagregación por edad y sexo, y no se consideran el presentismo ni el impacto emocional.

Para mejorar el análisis a futuro, la validación de los días perdidos mediante registros de descansos médicos de EsSalud y el seguimiento de los pacientes frente a un grupo comparable permitirían estimar con mayor precisión el impacto del CCR sobre el empleo y los ingresos.

# **Limitaciones del análisis**

- **Fecha de diagnóstico:** ante la ausencia de una variable que identifique de manera explícita la fecha de diagnóstico, se utiliza como aproximación la fecha del primer registro de CCR en la base FISSAL. Esta fecha puede ser posterior al diagnóstico clínico efectivo cuando este se haya realizado previamente en otro establecimiento o no haya quedado registrado en la fuente analizada.
- **Ausencia de información sobre estadio clínico:** la base de datos no contiene información directa sobre el estadio tumoral al momento del diagnóstico (I–IV). Por ello, no es posible caracterizar de manera directa la severidad de la enfermedad al diagnóstico. Como aproximación exploratoria, se utiliza el tipo de atención inicial, emergencia u hospitalización, como indicador de mayor complejidad asistencial; esta variable no equivale al estadio clínico y debe interpretarse únicamente como un proxy de la condición de ingreso.
- **Fecha de fallecimiento:** en el subconjunto de referencia, 2,549 pacientes presentan registro de fallecimiento, de los cuales 2,157 (84.6%) no cuentan con una fecha exacta de defunción en el sistema. En estos casos, el valor centinela 01/01/1900 se reemplaza por la fecha de la última atención registrada, utilizada como aproximación a la fecha de fallecimiento. En consecuencia, los tiempos hasta el fallecimiento calculados para estos pacientes deben interpretarse como una aproximación y, en términos metodológicos, como un límite inferior respecto del tiempo real hasta la defunción.
- **Cobertura diagnóstica de FISSAL:** durante el período analizado, la base FISSAL no registra casos con código C20 (cáncer de recto), sino únicamente C18 (cáncer de colon; 98.9% de la cohorte) y C19 (unión rectosigmoidea; 1.1%). Con la información disponible no es posible establecer si esta diferencia responde a criterios específicos de cobertura catastrófica, convenciones de codificación clínica o características del proceso de extracción de la información. Por ello, los resultados de este informe deben interpretarse con cautela al extenderlos a pacientes con cáncer de recto (C20).
- **Representatividad de la cohorte:** la población analizada está conformada por pacientes financiados por FISSAL, correspondientes a una población específica de asegurados del SIS con condiciones de alto costo. En consecuencia, los resultados no son directamente generalizables a la totalidad de pacientes con CCR del país ni a poblaciones atendidas bajo otros esquemas de aseguramiento o financiamiento.
- **Deflactación de costos para 2025–2026:** los costos correspondientes a 2025 y 2026 no se ajustan por inflación, debido a que no se dispone de factores de corrección definitivos para dichos períodos. En particular, la información correspondiente a 2026 es parcial y comprende únicamente los registros disponibles hasta marzo. Por tanto, las comparaciones de costos que involucren estos períodos deben interpretarse considerando esta limitación.
# **Bibliografía**

ACTION Study Group. (2015). Catastrophic health expenditure and 12-month mortality associated with cancer in Southeast Asia: Results from a longitudinal study in eight countries. BMC Medicine, 13, 190.

Azzani, M., et al. (2024). Subjective and objective financial toxicity among colorectal cancer patients: A systematic review. BMC Cancer. https://doi.org/10.1186/s12885-023-11814-1

Chin, A. L., et al. (2017). Impact of intensity-modulated radiotherapy on health care costs of patients with anal squamous cell carcinoma. Journal of Oncology Practice. https://doi.org/10.1200/JOP.2017.024810

CROCODILE Study Group. (2022). Catastrophic expenditure and treatment attrition in patients seeking comprehensive colorectal cancer treatment in India: A prospective multicentre study. The Lancet Regional Health – Southeast Asia. https://doi.org/10.1016/j.lansea.2022.100058

Darbà, J., & Marsà, A. (2020). Evaluation of productivity losses due to premature mortality from colorectal cancer. PLoS ONE. https://pmc.ncbi.nlm.nih.gov/articles/PMC7757866

Gol-Montserrat, J., et al. (2017). Analysis of productivity costs in cancer: A systematic review. Global & Regional Health Technology Assessment. https://journals.aboutscience.eu/index.php/grhta/article/view/384

Gupta, A., et al. (2025). Health care contact days in older adults with metastatic cancer. JAMA Network Open. https://jamanetwork.com/journals/jamanetworkopen/fullarticle/2842561

Harris, J. P., et al. (2020). The clinical and financial cost of mental disorders among elderly patients with gastrointestinal malignancies. Cancer Medicine. https://doi.org/10.1002/cam4.3509

Heinesen, E., & Kolodziejczyk, C. (2013). Effects of breast and colorectal cancer on labour market outcomes: Average effects and educational gradients (Study Paper 59). Rockwool Foundation Research Unit. Publicado también en Journal of Health Economics. https://rockwoolfonden.s3.eu-central-1.amazonaws.com/wp-content/uploads/2022/07/Study-Paper-59.pdf

Huang, H.-Y., et al. (2017). Expenditure and financial burden for the diagnosis and treatment of colorectal cancer in China. Chinese Journal of Cancer. https://cancercommun.biomedcentral.com/articles/10.1186/s40880-017-0209-4

Iragorri, N., de Oliveira, C., Fitzgerald, N., & Essue, B. (2021). The out-of-pocket cost burden of cancer care: A systematic literature review. Current Oncology, 28(2), 1216-1248. https://doi.org/10.3390/curroncol28020117

Moran, J. R., Short, P. F., & Hollenbeak, C. S. (2011). Long-term employment effects of surviving cancer. Journal of health economics, 30(3), 505–514.

Mosegui, G. B. G., Vianna, C. M. M., Antoñanzas Villar, F., & Rodrigues, M. P. S. (2023). Lost productivity attributed to neoplasms in South America. Revista Brasileira de Cancerologia, 69(1), e-223289. https://doi.org/10.32635/2176-9745.RBC.2023v69n1.3289

Nguyen, C. M., et al. (2025). Initial-care medical and prescription costs for incident metastatic versus nonmetastatic colorectal cancer. Cancer Research Communications. https://doi.org/10.1158/2767-9764.CRC-25-0367

Paro, A., Hyer, J. M., Shaikh, C. F., & Pawlik, T. M. (2022). Financial Impact of Out-of-Pocket Costs Among Patients Undergoing Resection for Colorectal Carcinoma. Annals of surgical oncology, 29(9), 5387–5397. https://doi.org/10.1245/s10434-022-11755-2

Rodríguez García. (2014). Análisis del ausentismo laboral por enfermedad en el personal de SEDAPAL, en el periodo 2001-2013. LILACS (lil-757623). https://pesquisa.bvsalud.org/portal/resource/pt/lil-757623

Rose, L., et al. (2025). Estimated out-of-pocket costs for patients with common cancers and private insurance. JAMA Network Open. https://doi.org/10.1001/jamanetworkopen.2025.21575

So, S. C. Y., Ng, D. W. L., Liao, Q., Fielding, R., Soong, I., Chan, K. K. L., Lee, C., Ng, A. W. Y., Sze, W. K., Chan, W. L., Lee, V. H. F., & Lam, W. W. T. (2022). Return to work and work productivity during the first year after cancer treatment. Frontiers in Psychology, 13. https://doi.org/10.3389/fpsyg.2022.866346

Statistics Canada. (2014). The effects of cancer on employment and earnings of cancer survivors (Analytical Studies Branch Research Paper Series, No. 362). https://www150.statcan.gc.ca/n1/pub/11f0019m/11f0019m2014362-eng.htm

Urwin, S., Van den Berg, B., Lau, Y.-S., Rowland, C., Hanratty, B., & Grande, G. (2021). The monetary valuation of informal care to cancer decedents at end-of-life: Evidence from a national census survey. Palliative Medicine, 35(4), 750-758.
