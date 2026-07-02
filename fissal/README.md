# FISSAL — Procesamiento y Analisis de Cancer Colorrectal (CCR)

**Proyecto:** Estudio de trayectoria clinica de pacientes con cancer colorrectal en Peru  
**Fuente:** FISSAL (Fondo Intangible Solidario de Salud)  
**Periodo:** 2016–2022  
**Pacientes CCR:** 15,698 (1,559,428 registros)  
**Fecha de corte:** 2022-12-31  

---

## Pipeline de procesamiento

```
00_bronce (CSV crudos)
    │
    ▼ 00_revision_fissal.py
01_silver (Parquet por año)
    │
    ▼ 01_procesar_fissal.py
01_silver (Parquet limpios + resumen pacientes)
    │
    ▼ 02_cancer_colorrectal.py
01_silver (FISSAL_CANCER_COLORRECTAL_2016_2022.parquet)
    │
    ├──► 03_perfil_pacientes_ccr.py  ──► FISSAL_CCR_PERFIL_PACIENTES.parquet
    │
    ├──► 03_analisis_ccr.py          ──► Analisis de tratamientos, medicamentos, costos
    │
    ├──► 04_trayectoria_clinica_ccr.py──► Procedimientos, hospitalizacion, recurrencia
    │
    ├──► 05_supervivencia_ccr.py     ──► Kaplan-Meier, enfermedad avanzada, plots PNG
    │        │
    │        ▼ FISSAL_CCR_PERFIL_PACIENTES_AMPLIADO.parquet
    │
    └──► hitos_paciente/              ──► Trayectoria en 4 hitos: Despistaje → Diagnostico →
                                          Tratamiento → Desenlace (ver hitos_paciente/README.md)
```

---

## 1. `00_revision_fissal.py` — Consolidacion de datos crudos

**Objetivo:** Unir los chunks CSV anuales (separados por `|`) en un solo Parquet por año.

| Concepto | Detalle |
|----------|---------|
| **Input** | `00_bronce/FISSAL_PRESTACIONES_YYYY_N_v2.csv` (pipe-separated, utf-8) |
| **Output** | `00_bronce/FISSAL_PRESTACIONES_YYYY.parquet` (7 archivos) |
| **Transformaciones** | Todas las columnas object → `astype(str)` |
| **Chunks por año** | 2022: 14 partes, 2021: 11, 2020: 12, 2019: 7, 2018: 10, 2017: 7, 2016: 8 |

---

## 2. `01_procesar_fissal.py` — Limpieza, fechas y variables derivadas

**Objetivo:** Transformar datos bronze → silver: parsear fechas, limpiar nulos, calcular edad, periodos y hospitalizacion.

### Input / Output

| Tipo | Ruta |
|------|------|
| **Input** | `00_bronce/FISSAL_PRESTACIONES_YYYY.parquet` |
| **Output** | `01_silver/FISSAL_PRESTACIONES_YYYY.parquet` (limpio) |
| **Output** | `01_silver/FISSAL_PACIENTES_LONGITUDINAL.parquet` |
| **Output** | `01_silver/FISSAL_RESUMEN_PACIENTES_POR_ANIO.parquet` |

### Variables creadas

| Variable | Descripcion | Formula |
|----------|-------------|---------|
| `ATE_ANOPROD` | Año de produccion | Renombrado de `ATE_A*OPROD` (la columna original varia por año fiscal) |
| `COD_UBIGEO` | Codigo ubigeo 6 digitos | `.astype(int).astype(str).str.zfill(6)` |
| `EDAD` | Edad al momento de la atencion | `int((ATE_FECATENCION - ATE_FECNAC).days / 365.25)` |
| `CAPITULO_CIE10` | Capitulo CIE-10 | Primer caracter de `ATE_CODCIE10` |
| `PERIODO_PRODUCCION` | Periodo de produccion | `ATE_ANOPROD + "-" + ATE_MESPROD.zfill(2)` |
| `ANIO_ATENCION` | Año de la atencion | `.dt.year` de `ATE_FECATENCION` |
| `MES_ATENCION` | Mes de la atencion | `.dt.month` de `ATE_FECATENCION` |
| `PERIODO_ATENCION` | Periodo de la atencion | `ANIO_ATENCION + "-" + MES_ATENCION.zfill(2)` |
| `DIAS_HOSPITALIZACION` | Dias de estancia | `(ATE_FECALTHOSP - ATE_FECINGHOSP).days` |
| `SEXO_CONSISTENTE` | Sexo no cambia entre años | `SEXOS_DISTINTOS == 1` (en resumen longitudinal) |

### Fechas procesadas

| Columna original | Significado |
|-----------------|-------------|
| `ATE_FECNAC` | Fecha de nacimiento |
| `ATE_FECATENCION` | Fecha de la atencion/prestacion |
| `ATE_FECINGHOSP` | Fecha de ingreso hospitalario |
| `ATE_FECALTHOSP` | Fecha de alta hospitalaria |
| `FEC_FALLECIMIENTO` | Fecha de fallecimiento |

### Constantes

- `NAN_STRINGS`: `{"nan", "NaN", "None", "none", "NaT", "nat", ""}`
- Division de edad: `365.25` dias/año
- Ubigeo: zero-fill a `6` digitos

---

## 3. `02_cancer_colorrectal.py` — Filtrado CCR

**Objetivo:** Filtrar registros con diagnostico C18, C19 o C20 (cancer colorrectal).

### Input / Output

| Tipo | Ruta |
|------|------|
| **Input** | `01_silver/FISSAL_PRESTACIONES_YYYY.parquet` |
| **Output** | `01_silver/FISSAL_CANCER_COLORRECTAL_2016_2022.parquet` |

### Filtro

- **Patron CIE-10:** `^C(18|19|20)` — incluye C180, C189, C19X, C169, C163, C187, C182, C162, C160

### Reportes impresos

- Registros filtrados por año (vs total)
- Distribucion por codigo CIE-10 (top 20)
- Distribucion por grupo CIE-10
- Pacientes por año de atencion
- Distribucion por sexo
- Tipo de atencion (HOSP, EMERG, etc.)
- Tipo de consumo (Medicamento, Procedimiento, Insumo)

---

## 4. `03_perfil_pacientes_ccr.py` — Tabla de perfil por paciente

**Objetivo:** Construir una tabla de 1 fila por paciente con todas sus caracteristicas demograficas, clinicas y economicas.

### Input / Output

| Tipo | Ruta |
|------|------|
| **Input** | `01_silver/FISSAL_CANCER_COLORRECTAL_2016_2022.parquet` |
| **Output** | `01_silver/FISSAL_CCR_PERFIL_PACIENTES.parquet` |

### Variables creadas (31 columnas)

#### Demografia

| Variable | Descripcion | Calculo |
|----------|-------------|---------|
| `SEXO` | Sexo del paciente | `first` |
| `ATE_FECNAC` | Fecha de nacimiento | `first` |
| `EDAD_PRIMERA_ATENCION` | Edad a la 1ra atencion | `floor((PRIMERA_ATENCION - ATE_FECNAC).days / 365.25)` |
| `RANGO_EDAD` | Grupo etario | `0-17, 18-29, 30-39, 40-49, 50-59, 60-69, 70-79, 80+` |
| `DEPARTAMENTO` | Depto. de residencia | Moda |
| `PROVINCIA` | Provincia de residencia | Moda |

#### Atenciones

| Variable | Descripcion | Calculo |
|----------|-------------|---------|
| `PRIMERA_ATENCION` | Fecha 1ra atencion | `min(ATE_FECATENCION)` |
| `ULTIMA_ATENCION` | Fecha ultima atencion | `max(ATE_FECATENCION)` |
| `N_ATENCIONES` | Numero de atenciones (FUA) | `ATE_FUA.nunique()` |
| `N_PRESTACIONES` | Total de prestaciones | `size()` |
| `N_ANIOS` | Años con atenciones | `ANIO_ATENCION.nunique()` |
| `ANIOS` | Lista de años | sorted unique |
| `PRIMER_ANIO` | Primer año con atencion | `min(ANIO_ATENCION)` |
| `ULTIMO_ANIO` | Ultimo año con atencion | `max(ANIO_ATENCION)` |
| `TIPOS_ATENCION` | Tipos de atencion | `TIPO_ATENC` unicos separados por `\|` |
| `TIPOS_CONSUMO` | Tipos de consumo | `ATE_TIPOCONSUMO` unicos separados por `\|` |

#### Clinicas

| Variable | Descripcion | Calculo |
|----------|-------------|---------|
| `FEC_FALLECIMIENTO` | Fecha de fallecimiento | `first` |
| `FALLECIDO` | ¿Fallecio? | `FEC_FALLECIMIENTO.notna()` |
| `SUPERVIVENCIA_DIAS` | Dias hasta muerte o censura | Si fallecio: `FEC_FALLECIMIENTO - PRIMERA_ATENCION`; si no: `FECHA_CORTE - PRIMERA_ATENCION` |
| `TIEMPO_EN_SISTEMA_DIAS` | Dias entre 1ra y ultima atencion | `ULTIMA_ATENCION - PRIMERA_ATENCION` |
| `CIE10_PRINCIPAL` | Codigo CIE-10 mas frecuente | Moda de `ATE_CODCIE10` |
| `N_DIAGNOSTICOS` | Diagnosticos distintos | `ATE_CODCIE10.nunique()` |

#### Tratamiento (flags booleanos)

| Variable | Criterio |
|----------|----------|
| `TUVO_HOSPITALIZACION` | `TIPO_ATENC` contiene "HOSP" |
| `TUVO_EMERGENCIA` | `TIPO_ATENC` contiene "EMERG" |
| `TUVO_MEDICAMENTO` | `ATE_TIPOCONSUMO == "Medicamento"` |
| `TUVO_PROCEDIMIENTO` | `ATE_TIPOCONSUMO == "Procedimiento"` |
| `TUVO_CIRUGIA` | Descripcion contiene: `COLECTOM\|RESECC\|CIRUG\|HEMICOLEC\|COLOSTOM\|LAPAROSCOP` |
| `TUVO_QUIMIOTERAPIA` | Descripcion contiene: `QUIMIO\|OXALIPLAT\|FLUOROURAC\|CAPECITAB\|IRINOTECAN\|BEVACIZUM\|CETUXIMAB\|FOLFOX\|FOLFIRI` |

#### Institucionales y economicas

| Variable | Descripcion | Calculo |
|----------|-------------|---------|
| `IPRESS_PRINCIPAL` | IPRESS mas frecuente | Moda de `ATE_NOMIPRESS` |
| `N_IPRESS` | IPRESS distintos visitados | `ATE_NOMIPRESS.nunique()` |
| `MONTO_BRUTO_TOTAL` | Monto bruto total | `sum(ATE_MONTOBRUTO)` |
| `MONTO_NETO_TOTAL` | Monto neto total | `sum(ATE_MONTONETO)` |

### Secciones del reporte

1. **Demografia:** distribucion por sexo, edad (media, mediana, std, min, max), edad por sexo, rango de edad
2. **Mortalidad y supervivencia:** fallecidos (n, %), supervivencia en dias/meses (media, mediana, min, max), edad al fallecimiento, fallecidos por año, rangos de supervivencia (`0-3m, 3-6m, 6-12m, 1-2a, 2-3a, 3-5a, 5a+`), fallecidos por sexo, tiempo en sistema de vivos
3. **Geografia:** top 15 departamentos, top 15 provincias, Lima vs Regiones
4. **IPRESS:** IPRESS unicos, media/mediana por paciente, top 20 por pacientes, top 20 por monto
5. **Nuevos vs recurrentes:** tabla por año: Total, Nuevos, Recurrentes, % Nuevos
6. **Perfil clinico:** % con hospitalizacion, emergencia, medicamentos, procedimientos, cirugia, quimioterapia; top 10 CIE-10; distribucion de atenciones (media, mediana, P25, P75, P95, max)

### Constantes

- `FECHA_CORTE`: `2022-12-31`
- Bins de edad: `[0, 18, 30, 40, 50, 60, 70, 80, 120]`
- Rangos de supervivencia (meses): `[(0,3), (3,6), (6,12), (12,24), (24,36), (36,60), (60,999)]`

---

## 5. `03_analisis_ccr.py` — Analisis profundo de tratamientos

**Objetivo:** Clasificar cada registro en categorias clinicas, analizar combinaciones de tratamiento, tiempos entre hitos, medicamentos y quimioterapia.

### Input / Output

| Tipo | Ruta |
|------|------|
| **Input** | `01_silver/FISSAL_CANCER_COLORRECTAL_2016_2022.parquet` |
| **Input** | `01_silver/FISSAL_CCR_PERFIL_PACIENTES.parquet` |
| **Output** | (comentado) `FISSAL_CCR_HITOS_TRATAMIENTO.parquet`, `FISSAL_CCR_PROCEDIMIENTOS_POR_PACIENTE.parquet`, `FISSAL_CCR_MEDICAMENTOS_POR_PACIENTE.parquet`, `FISSAL_CCR_ESQUEMAS_QUIMIO.parquet`, `FISSAL_CCR_CICLOS_QUIMIO.parquet` |

### Categorias de tratamiento (`CATEGORIA`)

Clasificacion por regex sobre `ATE_DESCCONSUMO`:

| Categoria | Ejemplos de terminos |
|-----------|---------------------|
| `CIRUGIA` | COLECTOM, RESECC, HEMICOLEC, COLOSTOM, LAPAROTOM, ANASTOMOS, LAPAROSCOP |
| `QUIMIOTERAPIA_PROC` | QUIMIOTER, INFUSION QUIMIO, ADMINISTRACION QUIMIO |
| `QUIMIO_MEDICAMENTO` | OXALIPLAT, FLUOROURAC, CAPECITAB, IRINOTECAN, LEUCOVORIN, BEVACIZUM, CETUXIMAB, PANITUMUM, RALTITREX, REGORAFEN, TRIFLURID |
| `RADIOTERAPIA` | RADIOTER, COBALTOT, BRAQUIT, ACELERADOR |
| `BIOPSIA` | BIOPSI, ANATOMOPATOLOG |
| `ENDOSCOPIA` | COLONOSCOP, ENDOSCOP, RECTOSCOP, SIGMOIDOSCOP |
| `IMAGEN` | TOMOGRAF, RESONAN, ECOGRAF, GAMMAGRAF, PET-SCAN |
| `LABORATORIO` | HEMOGRAM, CEA, ANTIGEN CARCINO, CREATININ, TRANSAMIN, ALBUMIN, HEMOGLOBIN, BILIRRUBIN, FOSFATASA |
| `TRANSFUSION` | TRANSFUS, CONCENTRADO GLOBUL, PAQUETE GLOBUL |
| `CUIDADO_PALIATIVO` | PALIATIV, DOLOR CRONICO, MANEJO DOLOR |
| `NUTRICION` | NUTRICION PARENTERAL, NUTRICION ENTERAL, SOPORTE NUTRIC |
| `CONSULTA` | CONSULTA MEDIC, CONSULTA AMBULAT, CONSULTA ESPECIAL |
| `ENFERMERIA` | ATENCION ENFERM, CUIDADO ENFERM |
| `UCI` | CUIDADO INTENSIV, UCI |
| `SIN_DESCRIPCION` | Descripcion nula |
| `OTRO` | Ninguna de las anteriores |

### Categorias de medicamentos (`CAT_MED`)

| Categoria | Ejemplos |
|-----------|----------|
| `QUIMIO_CITOTOXICO` | OXALIPLAT, FLUOROURAC, CAPECITAB, IRINOTECAN, LEUCOVORIN, FOLINATO |
| `TERAPIA_DIRIGIDA` | BEVACIZUM, CETUXIMAB, PANITUMUM, NIVOLUMAB, PEMBROLIZU, ATEZOLIZU |
| `ANTIEMETICO` | ONDANSETRON, METOCLOPRAMID, DIMENHIDRINAT, GRANISETRON |
| `ANALGESICO_OPIOIDE` | TRAMADOL, MORFIN, FENTANIL, OXICODON, CODEINA |
| `ANALGESICO_NO_OPIOIDE` | PARACETAMOL, METAMIZOL, KETOPROFEN, DICLOFENAC, IBUPROFENO |
| `PROTECTOR_GASTRICO` | OMEPRAZOL, RANITIDINA, LANSOPRAZOL, PANTOPRAZOL |
| `CORTICOIDE` | DEXAMETASON, PREDNISON, METILPREDNISOL, HIDROCORTISON |
| `ANTIBIOTICO` | METRONIDAZOL, CEFTRIAXON, CIPROFLOXACIN, MEROPENEM, VANCOMIC |
| `ANTICOAGULANTE` | ENOXAPARIN, HEPARINA, WARFARIN |
| `SOLUCION_FLUIDO` | SODIO CLORURO, DEXTROSA, LACTATO RINGER, MANITOL |
| `SUPLEMENTO_HIERRO` | HIERRO, SULFATO FERROSO, SACARATO HIERRO |
| `LAXANTE` | LACTULOS, MACROGOL, BISACODIL |
| `CONTRASTE` | IOPAMIDOL, IOPROMID, IOHEXOL, GADOLINI |
| `ANTIFUNGICO` | FLUCONAZOL, NISTATINA, CASPOFUNGIN |
| `ANSIO_SEDANTE` | MIDAZOLAM, DIAZEPAM, PROPOFOL, LORAZEPAM |
| `ANTIHIPERTENSIVO` | ENALAPRIL, LOSARTAN, AMLODIP, CAPTOPRIL |
| `ANTIDIARREICO` | LOPERAMID, RACECADOTRIL |
| `ERITROPOYETINA` | ERITROPOYETIN, EPO, DARBEPOETIN |

### Regimenes de quimioterapia identificados

| Regimen | Drogas |
|---------|--------|
| `FOLFOX` | FLUOROURACILO + LEUCOVORIN + OXALIPLATINO |
| `CAPOX/XELOX` | CAPECITABINA + OXALIPLATINO |
| `FOLFIRI` | FLUOROURACILO + LEUCOVORIN + IRINOTECAN |
| `CAPECITABINA_MONO` | Solo CAPECITABINA |
| `5FU/LV` | FLUOROURACILO + LEUCOVORIN |
| `5FU_MONO` | Solo FLUOROURACILO |
| `OXALIPLATINO_MONO` | Solo OXALIPLATINO |
| `OTRO` | Otras combinaciones |

Ademas se detecta si el paciente recibio **Bevacizumab** o **Cetuximab** como terapia añadida.

### Secciones del reporte (16 secciones)

1. **Combinaciones de tratamiento:** Cirugia + Quimio + Radio (CIR+QT+RT, CIR+QT, QT solo, etc.)
2. **Volumen de procedimientos:** Nº registros, Nº FUA, items distintos por paciente; distribucion FUA (`1, 2, 3-5, 6-10, 11-20, 21-50, 51-100, 100+`)
3. **Tiempos entre hitos:** Dias desde 1ra atencion hasta 1ra biopsia, endoscopia, imagen, cirugia, quimio, radioterapia (media, mediana, P25, P75, P95). Dias entre cirugia y quimio (neoadyuvante vs adyuvante)
4. **Top procedimientos por categoria:** Top 15 por Nº registros, pacientes y monto
5. **Intensidad de tratamiento:** Items por paciente-mes, meses activos por paciente
6. **Primera categoria:** Primera categoria registrada por paciente
7. **Categorias por tipo de atencion:** Tabla cruzada `TIPO_ATENC` × `CATEGORIA`
8. **Tratamiento segun perfil:** Por sexo, rango de edad, Lima vs Regiones, fallecidos vs vivos
9. **Analisis de medicamentos:** Registros por categoria (N_REG, N_PAC, MONTO)
10. **Esquemas de quimioterapia:** Pacientes por regimen, combinaciones exactas (top 15), con bevacizumab/cetuximab
11. **Volumen de medicamentos:** Registros, medicamentos distintos, categorias distintas, duracion por paciente
12. **Costo de medicamentos:** Distribucion (P25, P50, P75, P90, P95, max), costo por categoria, costo por paciente
13. **Top medicamentos por categoria:** Top 10 de cada categoria clinica
14. **Medicamentos segun perfil:** Por sexo, rango de edad, fallecidos
15. **Cronologia de medicamentos:** Dias desde 1ra atencion hasta 1er uso de cada categoria
16. **Ciclos de quimioterapia:** Nº sesiones por paciente, duracion total, distribucion (`1, 2-3, 4-6, 7-12, 13-24, 25-50, 50+`)

---

## 6. `04_trayectoria_clinica_ccr.py` — Trayectoria clinica y costos

**Objetivo:** Analizar procedimientos, medicamentos, insumos, hospitalizaciones, costos, recurrencias y servicios.

### Input / Output

| Tipo | Ruta |
|------|------|
| **Input** | `01_silver/FISSAL_CANCER_COLORRECTAL_2016_2022.parquet` |
| **Output** | (comentado) `FISSAL_CCR_HOSPITALIZACIONES.parquet`, `FISSAL_CCR_COSTOS_POR_PACIENTE_ANIO.parquet`, `FISSAL_CCR_BRECHAS_TRATAMIENTO.parquet` |

### Secciones del reporte (10 secciones)

1. **Procedimientos:** Top 30 mas frecuentes. Clasificacion en 7 categorias: CIRUGIA, QUIMIOTERAPIA, RADIOTERAPIA, BIOPSIA/PATOLOGIA, IMAGEN, ENDOSCOPIA, LABORATORIO
2. **Medicamentos:** Top 30 por frecuencia, pacientes y monto. Detalle de quimio y terapia dirigida
3. **Insumos:** Top 20 insumos
4. **Hospitalizaciones:** Episodios, distribucion de dias de estancia, hospitalizaciones por paciente, hospitalizaciones por año
5. **Costos:** Monto bruto/neto global, por tipo de consumo, por año, distribucion por paciente (P25/P50/P75/P90/P95/max), top 10 items mas costosos
6. **Recurrencias:** Brechas > 180 dias sin atencion, distribucion de gaps, rangos (`180-365d, 1-2a, 2-3a, 3a+`)
7. **Evolucion del tipo de atencion:** Tablas cruzadas por año
8. **Servicios:** Top 20 servicios (`ATE_DESCSERVICIO`)
9. **Tipo de documento:** Distribucion de tipos de documento (DNI, Carnet extranjeria, Pasaporte, Otro)
10. **Resumen general:** Totales generales

### Constantes

- **Umbral de recurrencia:** `180` dias sin atencion
- **Bins de gaps:** `[(180,365), (365,730), (730,1095), (1095,9999)]`
- **Periodo:** 2016–2022

---

## 7. `05_supervivencia_ccr.py` — Curvas Kaplan-Meier y enfermedad avanzada

**Objetivo:** Analisis de supervivencia con curvas KM estratificadas, log-rank test, y deteccion de enfermedad avanzada usando proxies de FISSAL.

### Input / Output

| Tipo | Ruta |
|------|------|
| **Input** | `01_silver/FISSAL_CANCER_COLORRECTAL_2016_2022.parquet` |
| **Input** | `01_silver/FISSAL_CCR_PERFIL_PACIENTES.parquet` |
| **Input** | `01_silver/FISSAL_PRESTACIONES_YYYY.parquet` (7 años, para deteccion en datos completos) |
| **Output** | `03_output/supervivencia/*.png` (8 graficos) |
| **Output** | `01_silver/FISSAL_CCR_PERFIL_PACIENTES_AMPLIADO.parquet` |

### Proxies de enfermedad avanzada

Como FISSAL **no registra** codigos C77/C79 (metastasis) ni la palabra "metastasis" en descripciones, se usan dos proxies:

#### A. Cuidados paliativos (`TUVO_PALIATIVO`)

- **Patron:** `PALIATIV` en `ATE_DESCCONSUMO`
- **Registros encontrados:** 337 (solo 2016-2018)
- **Pacientes:** 26
- **Interpretacion:** Enfermedad avanzada/terminal confirmada

#### B. Procedimientos en organos a distancia (`SITIO_*`)

Solo se cuentan **procedimientos** (no insumos, no medicamentos) en otros organos:

| Sitio | Patron | Pacientes |
|-------|--------|-----------|
| `SITIO_PERITONEO` | Laparoscopia diagnostica, drenaje absceso, reseccion peritoneal, carcinomatosis, citorreduccion | 96 |
| `SITIO_PULMON` | Lobectomia, segmentectomia, biopsia pulmonar, toracotomia | 15 |
| `SITIO_GANGLIO` | Biopsia/escision de ganglio linfatico, linfadenectomia | 12 |
| `SITIO_MEDULA_OSEA` | Aspiracion/biopsia de medula osea | 7 |
| `SITIO_HIGADO` | Hepatectomia, reseccion hepatica, biopsia hepatica, ablacion | 0 |

**Exclusion de insumos:** Se filtran descripciones que contienen `AGUJA, SET, LINEA, PROLONGADOR, TUBULADURA, OBTURADOR, SOLUCION.*DIALISIS, FILTRO`.

#### Clasificacion compuesta (`ENFERMEDAD_AVANZADA`)

| Grupo | Criterio | n |
|-------|----------|---|
| `PALIATIVO` | Recibio cuidados paliativos | 26 |
| `MULTISITIO` | Procedimientos en 2+ organos | 2 |
| `UN_SITIO` | Procedimientos en 1 organo | 126 |
| `SIN_INDICADORES` | Sin indicadores detectados | 15,544 |

### Curvas Kaplan-Meier generadas

| Archivo | Estratificacion | Log-rank |
|---------|----------------|----------|
| `km_global.png` | Todos los pacientes | — |
| `km_sexo.png` | Femenino vs Masculino | Si |
| `km_edad.png` | 7 rangos de edad | No (multigrupo) |
| `km_cirugia.png` | Con vs Sin cirugia | Si |
| `km_quimio.png` | Con vs Sin quimioterapia | Si |
| `km_enfermedad_avanzada.png` | 4 grupos (paliativo, multisitio, un sitio, sin indicadores) | No (multigrupo) |
| `km_region.png` | Lima vs Regiones | Si |
| `km_resumen_comparativo.png` | 6 paneles (todos los anteriores juntos) | Si (2-grupos) |

### Metodo Kaplan-Meier

- **Tiempo:** `SUPERVIVENCIA_DIAS` / 30 → meses
- **Evento:** `FALLECIDO` (True = muerte, False = censura)
- **Censura:** Pacientes vivos al `2022-12-31` se censuran en esa fecha
- **Mediana de supervivencia:** Tiempo donde la curva cruza 0.5
- **Log-rank test:** `lifelines.statistics.logrank_test` (p-value para diferencia entre curvas)

### Constantes

- `FECHA_CORTE`: `2022-12-31`
- Bins de edad (fallback): `[0, 18, 40, 50, 60, 70, 120]`
- DPI plots: `150`
- Figura individual: `10×6`, comparativa: `14×18`

---

## Diccionario consolidado de variables clave

### Variables de fecha

| Variable | Archivo origen | Significado |
|----------|---------------|-------------|
| `ATE_FECNAC` | `01_procesar` | Fecha de nacimiento |
| `ATE_FECATENCION` | `01_procesar` | Fecha de la atencion |
| `ATE_FECINGHOSP` | `01_procesar` | Fecha ingreso hospitalario |
| `ATE_FECALTHOSP` | `01_procesar` | Fecha alta hospitalaria |
| `FEC_FALLECIMIENTO` | `01_procesar` | Fecha de fallecimiento |
| `PRIMERA_ATENCION` | `03_perfil` | Primera fecha de atencion del paciente |
| `ULTIMA_ATENCION` | `03_perfil` | Ultima fecha de atencion del paciente |

### Variables de periodo

| Variable | Archivo origen | Significado |
|----------|---------------|-------------|
| `ATE_ANOPROD` | `01_procesar` | Año de produccion |
| `ATE_MESPROD` | `01_procesar` | Mes de produccion |
| `PERIODO_PRODUCCION` | `01_procesar` | `YYYY-MM` de produccion |
| `ANIO_ATENCION` | `01_procesar` | Año de la atencion |
| `MES_ATENCION` | `01_procesar` | Mes de la atencion |
| `PERIODO_ATENCION` | `01_procesar` | `YYYY-MM` de la atencion |

### Variables demograficas

| Variable | Archivo origen | Significado |
|----------|---------------|-------------|
| `SEXO` | `03_perfil` | Sexo (F/M) |
| `EDAD_PRIMERA_ATENCION` | `03_perfil` | Edad en años a la 1ra atencion |
| `RANGO_EDAD` | `03_perfil` | Grupo etario categorico |
| `DEPARTAMENTO` | `03_perfil` | Departamento de residencia |
| `PROVINCIA` | `03_perfil` | Provincia de residencia |

### Variables de mortalidad y supervivencia

| Variable | Archivo origen | Significado |
|----------|---------------|-------------|
| `FALLECIDO` | `03_perfil` | ¿Fallecio? (bool) |
| `SUPERVIVENCIA_DIAS` | `03_perfil` | Dias desde 1ra atencion hasta muerte o censura |
| `TIEMPO_EN_SISTEMA_DIAS` | `03_perfil` | Dias entre 1ra y ultima atencion |

### Variables de tratamiento

| Variable | Archivo origen | Significado |
|----------|---------------|-------------|
| `TUVO_HOSPITALIZACION` | `03_perfil` | ¿Tuvo al menos una hospitalizacion? |
| `TUVO_EMERGENCIA` | `03_perfil` | ¿Tuvo al menos una emergencia? |
| `TUVO_MEDICAMENTO` | `03_perfil` | ¿Recibio medicamentos? |
| `TUVO_PROCEDIMIENTO` | `03_perfil` | ¿Tuvo procedimientos? |
| `TUVO_CIRUGIA` | `03_perfil` | ¿Tuvo cirugia? (proxy por descripcion) |
| `TUVO_QUIMIOTERAPIA` | `03_perfil` | ¿Tuvo quimioterapia? (proxy por descripcion) |
| `CATEGORIA` | `03_analisis` | Categoria clinica del registro (14 valores) |
| `CAT_MED` | `03_analisis` | Categoria del medicamento (19 valores) |
| `REGIMEN` | `03_analisis` | Regimen de quimioterapia (FOLFOX, FOLFIRI, etc.) |

### Variables de enfermedad avanzada

| Variable | Archivo origen | Significado |
|----------|---------------|-------------|
| `TUVO_PALIATIVO` | `05_supervivencia` | ¿Recibio cuidados paliativos? |
| `SITIO_*` | `05_supervivencia` | ¿Procedimiento en ese organo? (5 sitios) |
| `N_SITIOS` | `05_supervivencia` | Cantidad de organos con procedimientos |
| `ENFERMEDAD_AVANZADA` | `05_supervivencia` | Clasificacion: PALIATIVO / MULTISITIO / UN_SITIO / SIN_INDICADORES |

### Variables economicas

| Variable | Archivo origen | Significado |
|----------|---------------|-------------|
| `MONTO_BRUTO_TOTAL` | `03_perfil` | Suma de montos brutos |
| `MONTO_NETO_TOTAL` | `03_perfil` | Suma de montos netos |

### Variables institucionales

| Variable | Archivo origen | Significado |
|----------|---------------|-------------|
| `IPRESS_PRINCIPAL` | `03_perfil` | IPRESS mas frecuente |
| `N_IPRESS` | `03_perfil` | Cantidad de IPRESS distintos |
| `N_ATENCIONES` | `03_perfil` | Cantidad de atenciones (FUA) |
| `N_PRESTACIONES` | `03_perfil` | Cantidad total de prestaciones |

---

## Limitaciones conocidas

1. **Sin codigos de metastasis (C77/C79):** FISSAL no registra estos codigos en absoluto. La deteccion de metastasis es indirecta (proxies).
2. **Sin estadiaje TNM:** No hay datos de estadio clinico en FISSAL.
3. **Mediana de supervivencia no alcanzada:** Solo 15.2% de pacientes fallecio en el periodo 2016-2022. La mayoria sigue viva al corte → la curva KM nunca cruza el 50%.
4. **Paliativos solo 2016-2018:** El registro de cuidados paliativos desaparece despues de 2018, posiblemente por cambios administrativos.
5. **CIRUGIA y QUIMIOTERAPIA son aproximaciones:** Se detectan por palabras clave en la descripcion, no por codigos especificos.
6. **Sin datos de recurrencia directa:** La recurrencia se infiere por gaps > 180 dias sin atencion.
7. **Periodo limitado:** 7 años (2016-2022). El seguimiento maximo es insuficiente para observar la historia natural completa del cancer colorrectal.
