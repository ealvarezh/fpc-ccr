# Gasto de bolsillo y costos indirectos del cáncer colorrectal en Perú: fuentes, métodos y hoja de ruta para el capítulo de costos (FPC – FISSAL/SEPA)

**Respuesta directa:** el capítulo dejará de verse "general" si se deja de usar ENAHO como fuente principal del gasto de bolsillo del CCR y se pasa a usarla como *denominador* (ingreso, gasto y capacidad de pago del hogar por quintil, región y tipo de seguro). El *numerador* se construiría por componentes con un modelo "frecuencia × costo unitario". La frecuencia sale de los registros FISSAL y del protocolo (ciclos FOLFOX/CAPOX, sesiones de radioterapia, viajes). El costo unitario sale de las entrevistas, de tarifas observadas y de estudios peruanos. Con eso se simula el gasto catastrófico y el empobrecimiento hogar por hogar.

## TL;DR

- **ENAHO sirve, pero como denominador y filtro, no como medida del gasto oncológico.** Su módulo 400 (preguntas 401, 403, 407F–407H y bloque de gasto en salud) y la Sumaria permiten calcular capacidad de pago, gasto catastrófico (10%/25%/40%), empobrecimiento (línea 2025: S/ 462 per cápita mensual; extrema S/ 260) y desagregar por quintil, región, ámbito y seguro. Sin embargo, no identifica cáncer, así que todo "gasto de bolsillo CCR" estimado solo con ENAHO será genérico. La ENUT 2024 (INEI, 6 056 viviendas, diario de actividades) sirve para fijar horas de cuidado de referencia y su valorización. ENDES y ENSUSALUD (última edición confirmada: 2016) son de utilidad marginal.
- **La evidencia peruana específica muestra que el grueso del gasto de bolsillo con FISSAL es no médico e indirecto.** En el INEN-Centro (Junín), el traslado por radioterapia costó en promedio US$ 69,65 por semana (transporte US$ 17,04, alojamiento US$ 6,69, alimentación US$ 45,91), el 23,3% del ingreso laboral mensual regional.\[1\] En cáncer de recto, los esquemas con FOLFOX generan más de 850 horas en el hospital frente a menos de 100 con CAPOX. Las pérdidas de productividad del paciente y del acompañante equivalen al 36% del ingreso anual del hogar con LCRT+FOLFOX frente al 8% con SCRT+CAPOX.\[2\]
- **Hay que pedir a FISSAL/SIS una base nominada (anonimizada) a nivel de prestación**, con ubigeo de residencia, IPRESS, fechas, esquema, ciclos, días de hospitalización, traslados financiados y estado vital. Con ella se construye una matriz origen–destino de viajes, días de alojamiento y días perdidos por paciente, y se simula (Monte Carlo) la distribución del gasto de bolsillo y del gasto catastrófico por estadio, región y quintil. Esto se triangula con las entrevistas y la encuesta a oncólogos.

## Key Findings

1. **Magnitud del problema.** Según GLOBOCAN 2024 (versión de septiembre de 2026), el CCR en Perú suma 5 313 casos nuevos al año (6,9% del total, 4.º lugar), 2 823 muertes (7,6%, 4.º lugar) y 14 107 casos prevalentes a 5 años. Afecta algo más a mujeres (2 929 casos) que a hombres (2 384).\[3\] Esto da el universo para extrapolar costos por paciente a costos nacionales.
2. **Cobertura financiera formal vs. real.** FISSAL financia el CCR (colon está entre sus 7 cánceres) "desde el diagnóstico" e incluye pasajes de ida y vuelta para paciente y acompañante cuando el paciente estable debe atenderse fuera de su región.\[4\]\[5\]\[6\] Sin embargo, el uso del beneficio de traslado es bajo en relación con el universo atendido: 4 130 pacientes y 3 019 acompañantes en 2024, frente a los "cerca de 169 000 asegurados con diversos diagnósticos oncológicos" para cuya atención el SIS transfirió más de S/ 386 millones, según El Peruano (27/09/2024; otra versión de la cifra la sitúa en 168 294 asegurados). En la práctica, alimentación, alojamiento, transporte urbano, viajes no cubiertos, medicinas por desabastecimiento y tiempo perdido quedan a cargo de la familia.
3. **El gasto de bolsillo general en Perú está sesgado hacia medicamentos en farmacias privadas.** DIGEMID muestra que la compra de medicamentos es el principal tipo de gasto de bolsillo y que más del 90% ocurre en farmacia o botica.\[7\] Más del 70% del gasto de bolsillo en 2020–2021 lo hicieron afiliados al SIS o a EsSalud.\[8\] Según el INEI, en 2024 nueve de cada diez asegurados de EsSalud compraron su receta en una farmacia.\[9\] Para CCR esto se traduce en un componente concreto: "medicinas no cubiertas o por desabastecimiento" (antieméticos, soporte, ostomía, capecitabina en quiebre de stock).
4. **Protección financiera nacional.** Según Acta Médica Peruana 2023;40(2):91–103 (ENAHO 2010, 2014 y 2019, método de Xu), el gasto de bolsillo mensual promedio del hogar pasó de S/ 119,9 (2010) a S/ 107,9 (2019). Los hogares con gasto catastrófico bajaron de 4,06% a 3,47%, y el empobrecimiento por gasto en salud de 1,78% a 1,51%. El estudio concluye que "los hogares afiliados sólo al SIS tienen una mayor vulnerabilidad frente al gasto de bolsillo en salud catastrófico y al empobrecimiento", y que tener un miembro con enfermedad crónica también eleva el riesgo. Estas cifras sirven de *línea base poblacional* contra la cual contrastar el gasto simulado de los hogares con CCR.
5. **Referencias internacionales de la magnitud esperable.** Una revisión sistemática en países de ingresos bajos y medios (BMC Health Services Research, 2025) estima gasto catastrófico en el 56,27% de los pacientes en el subgrupo "todos los cánceres" (IC95% 48,70–63,84; 24 estudios) y en el 71,96% en cánceres gastrointestinales (IC95% 54,67–89,26; 4 estudios). La estimación global combinada del mismo artículo es 58,42% (IC95% 52,29–64,55). Un metaanálisis sobre CCR (International Journal for Equity in Health 2026;25:77, 65 estudios) reporta una prevalencia combinada de gasto catastrófico de 0,69 (IC95% 0,45–0,94), y de 0,74 (IC95% 0,58–0,90) con COST-PROM. En Colombia, una tesis de la Universidad de Antioquia con una muestra aleatoria de 126 pacientes con cáncer del régimen subsidiado atendidos en el Hospital Pablo Tobón Uribe en 2020 encontró que la proporción con gasto de bolsillo pasaba de 19,0% a 43,3% al incluir transporte, alimentación y hotelería, y llegaba a 74,1% en los pacientes de la región Occidente. Es decir, *omitir lo no médico subestima el problema a menos de la mitad*.

## Details

### A. Inventario de fuentes de datos: qué sirve y qué no

| Fuente | Institución / última edición identificada | Variables clave para CCR | Limitaciones | Veredicto |
|---|---|---|---|---|
| **ENAHO** (Condiciones de Vida y Pobreza) | INEI; ENAHO 2025 (cifras de pobreza 2025 publicadas el 5/5/2026) | Mód. 400: p401 (enfermedad crónica), p402 (síntoma/recaída en últimas 4 semanas), p403 (lugar de atención), **p407F (tiempo desde la solicitud de cita hasta la atención), p407G (tiempo para llegar al establecimiento), p407H (tiempo de espera para ser atendido)**;\[10\] bloque de gasto en salud por servicio (consulta, medicinas, análisis, imágenes, hospitalización, cirugía) con forma de obtención (pagado por el hogar, SIS, EsSalud, donación) y monto; afiliación a seguros. Mód. 500: ocupación, horas, ingreso laboral (para costo de oportunidad). Mód. 100: vivienda, activos. Sumaria: gasto e ingreso del hogar, gasto en alimentos, rubro "cuidados de la salud", línea de pobreza, pobreza, miembros, factor de expansión | No identifica cáncer ni CCR; períodos de recuerdo cortos (4 semanas / 3 meses / 12 meses); el gasto de transporte por salud no está separado del gasto general de transporte; tamaño muestral insuficiente para pacientes oncológicos | **Sí, como denominador**: capacidad de pago, línea de pobreza, quintiles, ingreso por hora regional, perfil de hogares SIS con enfermo crónico |
| **ENUT 2024** | INEI; trabajo de campo 20/8–30/11/2024, 6 056 viviendas, personas de 12+ años, diario del día anterior; publicada en marzo de 2025 (la anterior fue en 2010)\[11\] | Trabajo de cuidado no remunerado a miembros del hogar por grupo específico (incluye personas dependientes/enfermas), por sexo, área, edad, educación y condición de ocupación; cuidado a otros hogares; traslados | No identifica la enfermedad de la persona cuidada; muestra pequeña para subgrupos; diario de un solo día (varianza alta) | **Sí, para parámetros** de horas de cuidado y brecha de género, y para validar las horas reportadas en las entrevistas |
| **ENDES** | INEI; anual | Afiliación a seguros, barreras de acceso (centradas en mujeres en edad fértil), módulo de salud para adultos con factores de riesgo y tamizajes | Diseñada para salud materno-infantil y enfermedades no transmisibles; no mide gasto de bolsillo oncológico ni trayectoria de tratamiento | **Marginal**: solo para contexto de factores de riesgo y tamizaje; no usar para costos |
| **ENSUSALUD** | SUSALUD–INEI; ediciones 2014, 2015 y **2016** (última confirmada)\[12\] | Satisfacción, tiempo de espera (mediana de 60 min en consulta externa),\[13\] acceso a medicamentos, usuarios SIS | Desactualizada; usuarios de consulta externa general, no oncológica | **Marginal / histórica**: solo como referencia de tiempos de espera; confirmar con SUSALUD si hubo ediciones posteriores |
| **GLOBOCAN / IARC** | GCO, estimaciones 2024 (versión 1.0, septiembre de 2026) | Incidencia, mortalidad y prevalencia a 5 años de CCR | Estimaciones modeladas a partir de registros subnacionales | **Sí**: denominador epidemiológico |
| **Global Health Expenditure Database (OMS) / Banco Mundial** | Serie SH.XPD.OOPC.CH.ZS hasta 2023 (actualizada el 12/12/2025)\[14\] | Gasto de bolsillo como % del gasto corriente en salud | Las cifras difieren según la fuente: 28,13% (2019, réplica de datos del Banco Mundial), 27,22% (2021, perfil OPS), 22,8% (artículo de 2026 que cita a la OMS)\[7\]\[15\]\[16\] | **Sí, para contexto macro**; descargar el valor 2023 directamente del CSV del Banco Mundial y reportar la discrepancia |
| **SIS–FISSAL** | Reportes institucionales y notas de prensa; base de prestaciones a pedido | Prestaciones, montos, IPRESS, traslados financiados | Las cifras públicas no se desagregan por CCR | **Esencial** (ver sección C) |
| **INEN** (estadísticas, servicio social, albergues) | INEN; 5 100 casos de acogida 2022–2026 con organizaciones de la sociedad civil\[17\] | Procedencia de pacientes, acogida residencial | Datos agregados; pedir por localización CIE-10 | **Sí**, para la proporción de pacientes de provincia y la demanda de alojamiento |
| **Normas** | Ley N° 31336 (modificada por la Ley N° 31870) y su reglamento DS N° 004-2022-SA; NTS N° 218-MINSA/DGIESP-2024 "sobre el acceso a la cobertura oncológica" (RM N° 876-2024/MINSA, 18/12/2024)\[18\]\[19\] | Cobertura universal y gratuita; tiempos máximos de diagnóstico, tratamiento y seguimiento; referencia y contrarreferencia\[20\]\[21\] | Brecha entre norma y práctica | **Sí**: marco para medir "gasto por demoras" contra los tiempos normados |
| **Precios y parámetros macro** | MTPE: RMV S/ 1 130 desde el 1/1/2025 (DS 006-2024-TR), vigente en 2026;\[22\] UIT 2026 S/ 5 500;\[23\] INEI: línea de pobreza 2025 S/ 462 y extrema S/ 260; gasto real per cápita S/ 920;\[24\] IPC Lima | Valorización del tiempo, deflactores, umbrales | La propuesta de subir la RMV a S/ 1 300 no estaba aprobada a septiembre de 2026\[22\] | **Sí** |
| **Observatorio de precios DIGEMID, tarifarios de SIS/EsSalud/INEN/clínicas, pasajes (terminales, aerolíneas), albergues** | Consultas directas | Costos unitarios de medicamentos pagados de bolsillo, consultas y exámenes particulares, pasajes por ruta, cama en albergue | Requieren levantamiento propio (fecha y fuente documentadas) | **Sí**: costos unitarios para la simulación |

**Por qué no basta ENAHO:** con 5 313 casos nuevos de CCR al año en una población de unos 34 millones, la probabilidad de captar hogares con un paciente de CCR en tratamiento activo en una muestra anual de ENAHO es mínima. Además, la variable p401 agrupa "enfermedad crónica" (hipertensión, diabetes, etc.). Cualquier filtro "hogares con enfermo crónico" es un *proxy* débil y conviene presentarlo explícitamente así.

### B. Métodos y fórmulas por componente

**Principio general (microcosteo de abajo hacia arriba):**

Costo_bolsillo(i) = Σ_k [ Q_ik × P_k × (1 − s_ik) ]

donde *Q_ik* es la cantidad del recurso k usada por el paciente i (visitas, viajes, noches, cajas de medicamento), *P_k* el costo unitario y *s_ik* la fracción cubierta (FISSAL, ONG, donación). Q proviene de FISSAL y del protocolo, P de las entrevistas y tarifas, y s de las entrevistas y de los traslados FISSAL.

**1. Costos directos médicos de bolsillo** (consultas particulares, medicinas no cubiertas, laboratorio, imágenes, quimio/radio pagada, hospitalización, cirugía)
- GB_médico(i) = Σ_k p_k × n_ik × P_k, donde p_k es la probabilidad de pagar el ítem k de bolsillo (de las entrevistas) y n_ik el número de veces.
- "Gasto por demoras": GB_demora(i) = 1[t_espera_i > t_norma] × (P_particular_examen + P_consulta_particular), con t_norma tomado de la NTS 218 y t_espera de FISSAL (fecha de diagnóstico → inicio de tratamiento) o de las entrevistas.
- Precios: Observatorio DIGEMID (capecitabina, oxaliplatino, bevacizumab, cetuximab, antieméticos), tarifarios de clínicas e INEN particular. Referencia institucional pública: en el INEN-Centro, oxaliplatino 100 mg costaba S/ 29,00 por unidad, capecitabina 500 mg S/ 0,75 por tableta y fluorouracilo 500 mg S/ 11,16.\[2\] Son precios institucionales; los de farmacia privada serán varias veces mayores.

**2. Costos directos no médicos** (transporte, alojamiento, alimentación)
- Viajes por paciente: V_i = N_visitas_i, derivado del esquema: CAPOX = 1 visita por ciclo (21 días; 6–8 ciclos); FOLFOX = 1 ingreso por ciclo (14 días; 9–12 ciclos), que en el INEN-Centro implica **4 días de hospitalización por curso**; radioterapia larga = 25–28 sesiones en 5–5,5 semanas; corta = 5 sesiones; más consultas, exámenes y seguimiento.\[2\]
- Transporte: C_trans_i = V_i × (2 × tarifa_ruta(o_i, d_i) × (1 + a_i)) + V_i × urbano_d, donde a_i = 1 si hay acompañante (en Robles y Olivera, el 100% de los pacientes iba acompañado).\[2\]
- Alojamiento: C_aloj_i = Σ_v noches_iv × tarifa_noche. Las noches por visita son 0 si la distancia es menor que un umbral (p. ej., ≤ 3 h de viaje) y, si no, la duración de la estancia más 1. Para radioterapia de 5–6 semanas se modela como estancia continua.
- Alimentación: C_alim_i = días_fuera_i × (1 + a_i) × costo_diario.
- Restar lo que cubre FISSAL: s_trans_i = 1 si el paciente figura en la base de traslados financiados.
- Parámetros de referencia: Robles (2023), con 398 pacientes de radioterapia, encontró US$ 69,65 por semana, con la alimentación como mayor componente; más del 40% viajaba más de 30 km.\[25\]\[26\] El Semáforo Oncológico (estimación de asociaciones de pacientes, no un estudio, difundida por RPP el 10/05/2023 bajo el titular "Pacientes con cáncer gastan hasta S/ 6 mil al año para atenderse en Lima") calcula pasajes terrestres Tumbes/Tacna–Lima de S/ 240–300 ida y vuelta, cama de albergue cerca del INEN de S/ 10–30 por noche (unos S/ 80 por estancia), alimentación de unos S/ 60, más de S/ 500 por viaje y hasta S/ 6 000 al año.

**3. Costos indirectos del paciente** (productividad)
- Enfoque de capital humano: CI_pac_i = (días_descanso_i + días_hosp_i + horas_ambulatorias_i/8) × w_r × e_i, donde w_r es el ingreso laboral diario de la región r (ENAHO mód. 500 / planilla electrónica MTPE) y e_i = 1 si el paciente trabajaba (de las entrevistas o, por imputación, de ENAHO según edad, sexo y región).
- Enfoque de costos de fricción (sensibilidad): se limita la pérdida al período de fricción (p. ej., 3 meses). Es relevante porque en Perú una gran parte del empleo es informal: no hay subsidio EsSalud y la pérdida de ingreso recae directamente en el hogar.
- Para trabajadores formales de EsSalud, separar la pérdida para el hogar (ingreso no cubierto por el subsidio) de la pérdida social (producción).
- Mortalidad prematura (opcional, perspectiva social): años potenciales de vida laboral perdidos × ingreso anual, descontados al 3–5%.

**4. Costos indirectos del cuidador**
- Horas: H_cuid_i = horas_acompañamiento_visitas (de V_i × duración) + horas_cuidado_domiciliario_semanales × semanas_tratamiento.
- Valorización con tres métodos, para reportar un rango:
  - Costo de oportunidad: H × w_hora del cuidador según su sexo, edad, educación y región (ENAHO).
  - Costo de reemplazo: H × salario por hora de trabajadora del hogar o cuidadora. Mínimo legal: RMV S/ 1 130 / (48 h × 4,33) ≈ S/ 5,4 por hora.\[27\]
  - Costo de oportunidad para quien deja el empleo: ingreso mensual perdido × meses.
- Referencia peruana: en Robles y Olivera, los acompañantes tenían 24,6 años en promedio y el 73,7% no trabajaba, y el ingreso mensual del hogar era de S/ 1 031,7.\[2\] Esto ilustra que valorizar solo a cuidadores "ocupados" subestima el costo, porque el trabajo no remunerado también tiene un costo de reemplazo.

**5. Gasto catastrófico y empobrecimiento** (simulados)
- Capacidad de pago (método de Xu/OMS): CTP_h = gasto_total_h − gasto_subsistencia_h, donde la subsistencia es el gasto en alimentos equivalente (percentiles 45–55 de la participación alimentaria, escala de equivalencia con β = 0,56). Si el gasto en alimentos es menor que la subsistencia, CTP = gasto total − gasto en alimentos.
- Catastrófico (OMS/Xu): GB_h / CTP_h ≥ 40%.\[28\]\[29\]\[30\]
- ODS 3.8.2 (Banco Mundial/OMS): GB_h / gasto_total_h > 10% y > 25%.
- Empobrecimiento: (gasto_pc_h ≥ línea) y (gasto_pc_h − GB_h/miembros < línea), con la línea 2025 de S/ 462 (o la regional de la Sumaria). Reportar también la brecha de pobreza generada.
- **Paso clave:** asignar a cada hogar ENAHO "elegible" (perfil similar al paciente SIS: región, ámbito, quintil, tamaño) un gasto de bolsillo de CCR simulado (de las secciones B1–B4), recalcular los indicadores y reportarlos por quintil, región y seguro. Esto es lo que vuelve el análisis específico sin requerir que ENAHO capture pacientes con cáncer.

**6. Toxicidad financiera subjetiva y afrontamiento**
- Aplicar el instrumento COST (COmprehensive Score for financial Toxicity; 11 ítems, 0–44, donde un puntaje menor indica mayor toxicidad) en las entrevistas. En Argentina (cáncer de pulmón), la mediana fue 20 y el 70,3% reportó algún grado de toxicidad;\[31\] en Brasil y México se han usado medidas similares.
- Estrategias de afrontamiento: proporción de hogares que usó ahorros, vendió bienes, se endeudó o recibió colectas/ONG, y el monto como % del ingreso anual.

**7. Ajustes**
- Inflación: P_2026 = P_t × (IPC_2026 / IPC_t), con el IPC de Lima Metropolitana del INEI (o el de "cuidado y conservación de la salud" para ítems médicos).
- Conversión a dólares: tipo de cambio promedio del año (BCRP). Para comparaciones internacionales, usar PPA del Banco Mundial.
- Descuento para costos de por vida: 3% (sensibilidad 0–5%).

### C. Lista priorizada de datos para solicitar

**Prioridad 1 – FISSAL/SIS (base anonimizada a nivel de prestación, 2019–2025, CIE-10 C18–C21):**
1. ID anonimizado del paciente, edad, sexo, **ubigeo de residencia** (distrito) y ubigeo de la IPRESS de atención.
2. Fechas de diagnóstico definitivo, de referencia, de primera atención oncológica, de inicio de cada modalidad y de última atención; fecha de fallecimiento (cruce con RENIEC/SINADEF si es posible).
3. Estadio clínico (TNM) y localización (colon vs. recto).
4. Por prestación: código de procedimiento (CPT/tarifario SIS), medicamento (código SISMED), cantidad, monto valorizado y pagado, y tipo de atención (ambulatoria, hospitalaria, emergencia, hospital de día).
5. Esquema de quimioterapia (FOLFOX, CAPOX, FOLFIRI, ± bevacizumab/cetuximab), número de ciclos programados y administrados, sesiones de radioterapia.
6. Días de hospitalización por episodio.
7. **Traslados financiados** (pasajes para paciente y acompañante: fecha, ruta, modo, monto).
8. Indicadores de abandono o interrupción y transferencias entre IPRESS.

**Prioridad 2 – INEN, IREN y hospitales de referencia:** procedencia de los pacientes con CCR por departamento, proporción alojada en albergues, informes de servicio social (exoneraciones, donaciones), desabastecimiento de oncológicos por mes y tiempos de espera por procedimiento (colonoscopía, TAC, cirugía).

**Prioridad 3 – EsSalud:** subsidios por incapacidad temporal pagados con diagnóstico C18–C21 (días y montos), para medir días de incapacidad reales en trabajadores formales y comparar con FISSAL (informales).

**Prioridad 4 – SUSALUD:** reclamos de usuarios oncológicos (desabastecimiento, demoras) por IPRESS; confirmar si existe una ENSUSALUD posterior a 2016.

**Encuesta a oncólogos (ya prevista):** pedir distribuciones (mínimo, moda, máximo) y no solo promedios, para alimentar distribuciones triangulares o PERT en Monte Carlo.

### D. Cálculos sofisticados con FISSAL

- **Matriz origen–destino:** distancia y tiempo por carretera entre el centroide del distrito de residencia y la IPRESS (OSRM u OpenRouteService con la red vial), tarifa por ruta (precios observados en terminales y aerolíneas para las 20–30 rutas principales; para el resto, una regresión tarifa ~ km + modo + región). Esto da C_trans por paciente sin preguntarle a cada uno.
- **Días de alojamiento:** regla según tiempo de viaje y esquema (p. ej., viaje > 6 h ⇒ al menos 1 noche por visita; radioterapia de 25–28 sesiones ⇒ estancia de 5–6 semanas), calibrada con las entrevistas.
- **Costos por estadio y línea:** sumar costos médicos (FISSAL) y de bolsillo simulados por paciente, y agrupar por estadio, colon/recto, región de residencia y "viaja a Lima sí/no".
- **Supervivencia y costos de por vida:** Kaplan-Meier por estadio; el costo esperado de por vida se calcula como Σ_t S(t) × costo_medio(t) / (1+r)^t (método de Lin para datos censurados), en fases inicial, continuación y terminal.
- **Monte Carlo:** 10 000 iteraciones extrayendo P_k (lognormal/gamma de las entrevistas), Q_k (de FISSAL y de la encuesta a oncólogos) y w (ENAHO). Se reportan media, mediana, IC 95% y el porcentaje de hogares catastróficos con su intervalo. Complementar con análisis de sensibilidad univariado (gráfico tornado).
- **Equidad:** índices de concentración del gasto de bolsillo simulado por quintil y comparación Lima vs. provincia y rural vs. urbano.
- **Microsimulación de políticas:** escenarios contrafactuales como (i) cobertura universal de alojamiento y alimentación, (ii) mayor uso del beneficio de traslado FISSAL, (iii) descentralización (tratamiento en un IREN o en la región) y (iv) sustitución de FOLFOX por CAPOX cuando sea clínicamente apropiado. El último es especialmente potente: Robles y Olivera muestran que CAPOX reduce las horas en el hospital de más de 850 a menos de 100.\[2\]

### E. Código de ejemplo (Python/pandas)

```python
import pandas as pd, numpy as np
# ENAHO Sumaria + gasto CCR simulado por hogar
s = pd.read_stata("sumaria-2025.dta")
s["gpc"] = s["gashog2d"]/s["mieperho"]/12                       # gasto per cápita mensual
s["food_sh"] = s["gru11hd"]/s["gashog2d"]                        # verificar nombre de variable en diccionario
s["eqsize"] = s["mieperho"]**0.56
s["eqfood"] = s["gru11hd"]/s["eqsize"]
p45, p55 = s["food_sh"].quantile([.45,.55])
se = s.loc[s.food_sh.between(p45,p55),"eqfood"].mean()           # subsistencia por adulto eq.
s["subs"] = se*s["eqsize"]
s["ctp"] = np.where(s["gru11hd"]>=s["subs"], s["gashog2d"]-s["subs"], s["gashog2d"]-s["gru11hd"])
def indicadores(df, gb):                                        # gb = gasto de bolsillo anual CCR simulado
    out = {"cat40": (gb/df.ctp>=.40), "cat10": (gb/df.gashog2d>.10), "cat25": (gb/df.gashog2d>.25),
           "empob": (df.gpc>=df.linea) & ((df.gpc - gb/df.mieperho/12) < df.linea)}
    return pd.DataFrame(out).mul(df.factor07, axis=0).sum()/df.factor07.sum()
# Monte Carlo: gb ~ transporte + alojamiento + alimentación + médico + pérdida de ingreso
rng = np.random.default_rng(1)
def sim_gb(n, viajes, tarifa, noches, cama, comida, p_med, med):
    return (viajes*2*tarifa*2 + noches*cama + noches*2*comida + rng.binomial(1,p_med,n)*med)
```

En Stata, el mismo flujo usa `svyset conglome [pw=factor07], strata(estrato)`. Para reproducir series 2004–2025 de gasto catastrófico y empobrecimiento por tipo de seguro existe un repositorio público en Zenodo (Python/DuckDB) basado en ENAHO.\[32\] Es útil como referencia de código, pero no fue revisado en profundidad para este informe.

### F. Indicadores para el tablero (Power BI / DAX)

- Gasto de bolsillo medio y mediano por paciente y por ciclo, por componente (S/ 2026).
- % del gasto de bolsillo que es no médico.
- % de hogares con gasto catastrófico (10/25/40) y % empobrecidos, por quintil, región y estadio.
- Horas de cuidado por semana y su valor (3 métodos).
- Días de trabajo perdidos por el paciente y por el cuidador, por esquema.
- % que usó ahorros, préstamos o venta de bienes; % que recibió apoyo de ONG; cobertura efectiva del beneficio de traslado FISSAL (pacientes con traslado / pacientes de provincia).
- DAX ejemplo: `Cat40 % = DIVIDE(SUMX(FILTER(Hogares, Hogares[GB]/Hogares[CTP]>=0.4), Hogares[factor07]), SUM(Hogares[factor07]))`.

### G. Literatura de referencia con cifras

- **Perú, cáncer de recto (Robles Díaz y Olivera Changra, ecancermedicalscience 2022; INEN-Centro, Junín; 38 pacientes, 2020–2021):** costo directo para el financiador de S/ 3 409,81–27 928,36 según el esquema; costo indirecto para paciente y familia de S/ 1 089,62 (SCRT VMAT+CAPOX) a S/ 4 950,42 (LCRT+FOLFOX).\[33\] En LCRT+CAPOX, el transporte costó S/ 445,50 en la fase neoadyuvante.\[2\]
- **Perú, radioterapia (Robles Díaz, ecancermedicalscience 2023; 398 pacientes):** gasto semanal de traslado de US$ 69,65 (tipo de cambio de 3,80), correlacionado con la distancia.\[1\]\[25\]
- **Perú, cáncer de colon avanzado (Value in Health 2015):** costo anual para el financiador (MINSA/SIS, 2014) de US$ 38,35 millones, el 20,7% del presupuesto anual del PP 024; el 97,1% correspondía a tratamiento.\[34\]
- **Perú, XELOX vs. FOLFOX-4 adyuvante (Hinojosa y Battilana, 2005):** costo integral a 6 meses de S/ 19 100 vs. S/ 22 553. La terapia oral reduce costos asociados a la infusión.\[35\]
- **Perú, protección financiera (Acta Médica Peruana 2023):** cifras de 2010–2019 ya citadas en Key Findings.\[36\]
- **Regional:** Argentina (cáncer de pulmón; COST y gasto catastrófico; gasto de bolsillo de 18,5% del ingreso del hogar); Colombia (tesis de la Universidad de Antioquia, 126 pacientes del régimen subsidiado del Hospital Pablo Tobón Uribe en 2020: 19,0% → 43,3% al incluir transporte, alimentación y hotelería, y 74,1% en la región Occidente); Colombia (costo de CCR por estadio con la metodología de caso tipo); México (toxicidad financiera en adultos mayores, métodos mixtos); Brasil (cohorte prospectiva de pacientes asegurados).
- **Revisiones:** CCR (definición objetiva = gasto catastrófico, subjetiva = COST; costo médico directo anual de US$ 2 045–10 772); países de ingresos bajos y medios (BMC Health Services Research, 2025: gasto catastrófico de 56,27% en el subgrupo "todos los cánceres", IC95% 48,70–63,84, y estimación global combinada de 58,42%, IC95% 52,29–64,55).

## Recommendations

1. **Reestructure el capítulo de costos en 7 secciones:** (1) costos directos médicos para el financiador (FISSAL), como contexto; (2) gasto de bolsillo directo médico; (3) gasto directo no médico; (4) costos indirectos del paciente; (5) costos indirectos del cuidador; (6) gasto catastrófico y empobrecimiento simulados; (7) estrategias de afrontamiento y toxicidad financiera (COST). Abra cada sección con un número "titular" y un caso tipo.
2. **Presente "casos tipo" o personas:** p. ej., un paciente de Cajamarca (pobreza de 41,0% en 2025),\[37\] estadio III de colon, CAPOX ×8, que viaja al INEN, frente a un paciente de Lima en estadio II, y frente a uno de recto con LCRT+FOLFOX. Calcule el costo por componente para cada uno. Esto vuelve tangible el análisis.
3. **Triangule explícitamente ENAHO y las entrevistas** con una tabla de tres columnas por componente: ENAHO (población general / enfermos crónicos), entrevistas CCR (media, mediana y P90) y simulación FISSAL+protocolo. Discuta las diferencias; la brecha misma es un hallazgo ("ENAHO subestima el gasto oncológico porque no capta lo no médico ni la estacionalidad del tratamiento").
4. **Reporte medianas, P75/P90 y proporciones**, no solo promedios: el gasto de bolsillo es muy asimétrico.
5. **Mida la "cobertura efectiva" de FISSAL:** cruce los pacientes de provincia con la base de traslados financiados. Si la proporción es baja, esa es una recomendación de política accionable (difusión del beneficio, simplificación del trámite, extensión a alimentación y alojamiento).
6. **Use la NTS 218 como vara:** calcule el % de pacientes cuyo tiempo de diagnóstico a tratamiento excede lo normado y el gasto por demoras asociado.
7. **Cierre con una microsimulación de políticas** (alojamiento, descentralización, CAPOX) y su impacto en el % de hogares catastróficos.

## Caveats

- **Supuestos sobre ENAHO:** los nombres de variables (p. ej., gashog2d, gru11hd, linea, factor07, numeración de 407F–407H) deben verificarse en el diccionario de cada edición. Las preguntas de tiempo de traslado y espera (407F–407H) se confirmaron en el cuestionario 2022.
- **Cifras de FISSAL:** el agregado de "cerca de 169 000 asegurados con diversos diagnósticos oncológicos" y más de S/ 386 millones proviene de El Peruano (27/09/2024); otra versión lo sitúa en 168 294 asegurados, y el período exacto que cubre debe confirmarse con el SIS. No hay cifras públicas verificadas específicas de CCR por año, por lo que hay que solicitarlas.
- **ENSUSALUD:** solo se confirmaron las ediciones 2014–2016; no afirme que no existen posteriores sin consultar a SUSALUD.
- **Gasto de bolsillo como % del gasto corriente en salud:** hay discrepancias entre fuentes (22,8%–28,13% según año y fuente).\[7\]\[15\] Use el valor 2023 descargado directamente de la base de la OMS o del Banco Mundial y cite la fecha de consulta.
- **Estimaciones de asociaciones (Semáforo Oncológico, "hasta S/ 6 000 al año", difundida por RPP el 10/05/2023)** son de incidencia y no estudios; úselas como contraste, no como parámetro central.
- **Generalización:** los estudios de Robles provienen de un solo instituto (Junín), con muestras pequeñas (38 pacientes en recto)\[2\] y tipo de cambio de 3,80. Ajústelos por IPC y no los extrapole sin calibrar con las entrevistas.
- **NTS 218 y Ley 31336:** no se verificó en esta investigación el articulado específico sobre transporte, albergues y protección financiera del reglamento (DS 004-2022-SA), ni si la NTS 218 incluye disposiciones específicas para CCR. Revise el texto completo antes de citar obligaciones concretas.
- **Doble conteo:** no sume la pérdida de productividad del paciente y el "costo de reemplazo" del cuidador por las mismas horas. Tampoco sume el subsidio EsSalud como pérdida del hogar.
- **Sesgo de supervivencia en las entrevistas:** los pacientes entrevistados son los que continúan en tratamiento; quienes abandonaron por razones económicas (los de mayor toxicidad financiera) están subrepresentados. Use la base de FISSAL (abandono) para dimensionar este sesgo.

## Fuentes

1. [Impact of outpatient radiotherapy on direct non-medical cost in patients in the Central Macro Region of Peru 2021](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC10393304/)
2. <https://pmc.ncbi.nlm.nih.gov/articles/PMC9377803/>
3. <https://gco.iarc.who.int/media/globocan/factsheets/populations/604-peru-fact-sheet.pdf>
4. [¿Qué enfermedades tienen cobertura por Fissal? - Orientación - Fondo Intangible Solidario de Salud - Plataforma del Estado Peruano](https://www.gob.pe/9491-que-enfermedades-tienen-cobertura-por-fissal)
5. [Asegurados del SIS con cáncer cuentan con cobertura al 100 % para su tratamiento y traslados - Noticias - Fondo Intangible Solidario de Salud - Plataforma del Estado Peruano](https://www.gob.pe/institucion/fissal/noticias/756663-asegurados-del-sis-con-cancer-cuentan-con-cobertura-al-100-para-su-tratamiento-y-traslados)
6. [Fissal transfirió más de S/ 126 millones para el tratamiento del cáncer - Noticias - Fondo Intangible Solidario de Salud - Gobierno del Perú](https://www.gob.pe/institucion/fissal/noticias/582204-fissal-transfirio-mas-de-s-126-millones-para-el-tratamiento-del-cancer)
7. [Frontiersin](https://www.frontiersin.org/journals/behavioral-economics/articles/10.3389/frbhe.2026.1747754/xml)
8. [Gasto de bolsillo en salud y medicamentos. Periodo 2020-2021](https://repositorio-digemid.minsa.gob.pe/items/ff39a476-eb94-435d-8670-c422cc94be1e)
9. [La inestabilidad que frena a EsSalud: 9 presidentes en cinco años, ¿qué futuro le espera al seguro social?](https://elcomercio.pe/economia/peru/la-inestabilidad-que-frena-a-essalud-9-presidentes-en-cinco-anos-que-futuro-le-espera-al-seguro-social-essalud-ipe-noticia/)
10. <https://www.inei.gob.pe/media/encuestas/documentos/enaho/2022/02_Enaho01A_2022_Educacion_Salud_y_Empleo.pdf>
11. <https://www.inei.gob.pe/media/MenuRecursivo/publicaciones_digitales/Est/Lib2010/libro.pdf>
12. [Satisfacción y tiempo de espera de usuarios de establecimientos de salud peruanos: análisis secundario de ENSUSALUD 2014-2016](https://www.scielo.org.pe/scielo.php?script=sci_arttext&pid=S1025-55832019000300003)
13. [análisis secundario de ENSUSALUD 2014-2016](http://www.scielo.org.pe/pdf/afm/v80n3/a03v80n3.pdf)
14. [World Bank Open Data](https://data.worldbank.org/indicator/SH.XPD.OOPC.CH.ZS?locations=PE)
15. [Peru - Out-of-pocket expenditure (% of current health expenditure)](https://www.indexmundi.com/facts/peru/indicator/SH.XPD.OOPC.CH.ZS)
16. [Peru Country Profile](https://hia.paho.org/en/node/127)
17. [INEN: Más de 5 mil pacientes oncológicos de regiones accedieron a acogida residencial que facilitó la continuidad de sus tratamientos - Noticias - Instituto Nacional de Enfermedades Neoplásicas - Plataforma del Estado Peruano](https://www.gob.pe/institucion/inen/noticias/1397374-inen-mas-de-5-mil-pacientes-oncologicos-de-regiones-accedieron-a-acogida-residencial-que-facilito-la-continuidad-de-sus-tratamientos)
18. [Ley 31336, Ley Nacional del Cáncer](https://leyes.congreso.gob.pe/Documentos/2021_2026/ADLP/Texto_Consolidado/31870-TXM.pdf)
19. [Resolución Ministerial N.° 876-2024-MINSA - Normas y documentos legales - Ministerio de Salud - Plataforma del Estado Peruano](https://www.gob.pe/institucion/minsa/normas-legales/6303564-876-2024-minsa)
20. [Gobierno aprobó el Reglamento de la Ley Nacional del Cáncer](https://andina.pe/agencia/noticia-gobierno-aprobo-reglamento-de-ley-nacional-del-cancer-886816.aspx)
21. [Aprueban norma que mejora el acceso a la cobertura oncológica en los establecimientos de salud de todo el país - Caretas Salud](https://caretas.pe/salud/aprueban-norma-que-mejora-el-acceso-a-la-cobertura-oncologica-en-los-establecimientos-de-salud-de-todo-el-pais/)
22. [Sueldo mínimo en Perú 2026: cuánto es la RMV vigente](https://empleoenperu.com/sueldo-minimo/)
23. [Sueldo Mínimo Perú 2026: S/ 1,130](https://sueldojusto.pe/blog/sueldo-minimo-peru/)
24. [La pobreza en 2025 retrocede a 25,7%, pero 1 de cada 3 peruanos aún puede caer en cualquier momento - Infobae](https://www.infobae.com/peru/2026/05/05/la-pobreza-en-peru-se-reduce-a-257-en-2025-pero-1-de-cada-3-podria-caer-en-cualquier-momento-segun-inei/)
25. [Impact of outpatient radiotherapy on direct non-medical cost in patients in the Central Macro Region of Peru 2021 - PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC10393304)
26. [Impact of outpatient radiotherapy on direct non-medical cost in patients in the Central Macro Region of Peru 2021 - ecancer](https://ecancer.org/en/journal/article/1580-impact-of-outpatient-radiotherapy-on-direct-non-medical-cost-in-patients-in-the-central-macro-region-of-peru-2021/abstract)
27. [Sueldo Mínimo en Perú: Cuánto Es \[Actualizado 2025\]](https://www.interseguro.pe/blog/sueldo-minimo-peru)
28. [Frontiers](https://www.frontiersin.org/journals/public-health/articles/10.3389/fpubh.2023.1266533/full)
29. [(PDF) GASTO DE BOLSILLO EN SALUD Y RIESGO DE POBREZA EN HOGARES PERUANOS. PERÚ 2017](https://www.researchgate.net/publication/347647078_GASTO_DE_BOLSILLO_EN_SALUD_Y_RIESGO_DE_POBREZA_EN_HOGARES_PERUANOS_PERU_2017)
30. [Determinantes del gasto de bolsillo en salud en el Perú](https://www.researchgate.net/publication/367862562_Determinantes_del_gasto_de_bolsillo_en_salud_en_el_Peru)
31. [Health-related Quality of life, Financial Toxicity, Productivity Loss and Catastrophic Health Expenditures After Lung Cancer Diagnosis in Argentina](https://arxiv.org/pdf/2312.16710)
32. [Protección financiera por tipo de seguro de salud en el Perú: gasto catastrófico y empobrecedor, 2004-2025 — código y datos agregados](https://zenodo.org/records/20978569)
33. [Análisis de costos de la Terapia Neoadyuvante Total con ...](https://ecancer.org/en/journal/article/1406-cost-analysis-of-total-neoadjuvant-therapy-with-5-5-gy-radiation-therapy-versus-conventional-chemoradiotherapy-for-locally-advanced-rectal-cancer-among-peruvians/pdf/es)
34. [Costo De Cáncer De Colon Avanzado En Los Establecimientos Hospitalarios Del Perú - Value in Health](<https://www.valueinhealthjournal.com/article/S1098-3015(15)02152-X/fulltext>)
35. [Revista DIAGNOSTICO](http://www.fihu.org.pe/revista/numeros/2005/jul-set05/116.html)
36. [91 ISSN electrónica 1728-5917 Acta Med Peru. 2023;40(2):091-103 XXXXXX XXXXXX](http://www.scielo.org.pe/pdf/amp/v40n2/1728-5917-amp-40-02-91.pdf)
37. [INEI: Pobreza monetaria alcanzó al 25,7% de la población en Perú durante 2025 - Energiminas](https://energiminas.com/2026/05/05/inei-pobreza-monetaria-alcanzo-al-257-de-la-poblacion-en-peru-durante-2025/)
