# Guía de modelo y DAX — réplica del dashboard en Power BI

Este documento explica cómo usar los parquets generados por `build_powerbi_parquets.py`
para reconstruir cada sección del dashboard HTML (`dashboard/index.html`) en Power BI,
sin que Power BI necesite tocar SQL Server. Corre el script, apunta Power BI (modo
**Import**, no DirectQuery) a la carpeta de salida, y usa las medidas de abajo.

Ruta de los parquets:
`C:\Users\eah\apoyoconsultoria.com\File Server - Analytics\3 Proyectos\2025\2025-116-L FPC Dashboard 25\4 Analisis\4 Resultados\Adicional 2026`

## 1. Las tablas y cómo se relacionan

```
dim_anio (anio, factor_ipc)
     │ 1
     │
     │ *
fact_costo_anual (paciente, anio, bucket, costo_nominal)
     │ *
     │
     │ 1
fact_pacientes_fissal (paciente, sexo, localizacion, track, fechas, costo nominal total...)
     │ 1                              │ 1                        │ 1
     │                                │                           │
     │ *                              │ *                         │ *
fact_costo_categoria          fact_costo_otros_diagnosticos   fact_hospitalizacion
(paciente, categoria,         (paciente, CIE10, tipo,         (paciente, fecha_ingreso,
 subcategoria, costo)          costo)                          fecha_alta, dias_estancia,
                                                                 costo_episodio)

fact_essalud_gcop   (independiente — otro universo de pacientes, otro ID)
fact_sis_atenciones / fact_sis_consumos  (independiente — otro universo, otro ID)
```

**Cómo armar las relaciones en Power BI**: todas las `fact_*` de FISSAL se relacionan
con `fact_pacientes_fissal` por `Codigo_identificacion_paciente` (cardinalidad
uno-a-varios, dirección única desde `fact_pacientes_fissal`). `dim_anio` se relaciona
con `fact_costo_anual` por `anio`. EsSalud y SIS no se relacionan con nada de FISSAL
(son universos de pacientes distintos, con IDs distintos) — van en páginas/visuales
separados, igual que en el dashboard HTML.

**Por qué el costo no viene "ya deflactado" en las tablas** (salvo EsSalud): la
deflactación depende de EN QUÉ AÑO se gastó cada sol, así que vive mejor como una
medida DAX que multiplica `fact_costo_anual[costo_nominal]` por el `factor_ipc` del año
correspondiente — así cualquier filtro (track, sexo, localización, categoría) deflacta
correctamente en automático, sin tener que recalcular columnas fijas cada vez que algo
cambia.

---

## 2. Medidas base (crear una vez, se reutilizan en todos lados)

```dax
Costo Deflactado (Total) =
SUMX(
    FILTER(fact_costo_anual, fact_costo_anual[bucket] = "TOTAL"),
    fact_costo_anual[costo_nominal] * RELATED(dim_anio[factor_ipc])
)

Costo Deflactado (Tratamiento) =
SUMX(
    FILTER(fact_costo_anual, fact_costo_anual[bucket] = "CRC_ATRIBUIBLE"),
    fact_costo_anual[costo_nominal] * RELATED(dim_anio[factor_ipc])
)

Costo Deflactado (Soporte) =
SUMX(
    FILTER(fact_costo_anual, fact_costo_anual[bucket] = "SOPORTE"),
    fact_costo_anual[costo_nominal] * RELATED(dim_anio[factor_ipc])
)

Costo Deflactado (No atribuible) =
SUMX(
    FILTER(fact_costo_anual, fact_costo_anual[bucket] = "NO_ATRIBUIBLE"),
    fact_costo_anual[costo_nominal] * RELATED(dim_anio[factor_ipc])
)
```

Estas 4 miden el TOTAL del filtro activo (ej. toda la cohorte, o solo un año si hay un
slicer de año). Para la **mediana/media por paciente** (lo que muestra el dashboard en
Resumen), hay que forzar una tabla virtual de "1 fila por paciente" con `ADDCOLUMNS` +
`VALUES`, porque `MEDIANX` necesita filas discretas, no un total ya agregado:

```dax
Costo Deflactado Mediana (por paciente) =
VAR PorPaciente =
    ADDCOLUMNS(
        VALUES(fact_pacientes_fissal[Codigo_identificacion_paciente]),
        "@Costo", [Costo Deflactado (Total)]
    )
RETURN MEDIANX(PorPaciente, [@Costo])

Costo Deflactado Media (por paciente) =
VAR PorPaciente =
    ADDCOLUMNS(
        VALUES(fact_pacientes_fissal[Codigo_identificacion_paciente]),
        "@Costo", [Costo Deflactado (Total)]
    )
RETURN AVERAGEX(PorPaciente, [@Costo])
```

Repite el mismo patrón con `[Costo Deflactado (Tratamiento)]`, `(Soporte)`, `(No
atribuible)` para las medianas/medias del desglose. Filtra por
`fact_pacientes_fissal[TRACK] = "A_COMPLETO"` y `fact_pacientes_fissal[FISSAL_REGULAR] =
TRUE` (con un slicer, o metiéndolo en un `CALCULATE`) para replicar el corte "Track A +
FISSAL regular" que usa el dashboard en toda la sección de costos.

---

## 3. Resumen

| Elemento del dashboard | DAX |
|---|---|
| Pacientes CCR totales | `DISTINCTCOUNT(fact_pacientes_fissal[Codigo_identificacion_paciente])` |
| Pacientes con tratamiento | Igual, con filtro `TRACK="A_COMPLETO"` y `FISSAL_REGULAR=TRUE` |
| Fallecidos / proporción | `CALCULATE([Pacientes...], fact_pacientes_fissal[FALLECIDO]=TRUE)` y `DIVIDE(Fallecidos, Pacientes con tratamiento)` |
| Tiempo en sistema (mediana) | `MEDIANX(fact_pacientes_fissal, fact_pacientes_fissal[TIEMPO_EN_SISTEMA_DIAS])` |
| Costo nominal mediana/media | `MEDIANX`/`AVERAGEX` sobre `fact_pacientes_fissal[MONTO_NETO_TOTAL]` |
| Costo deflactado, desglose | Medidas de la sección 2 |
| Hospitalización (días/n° mediana) | `MEDIANX(fact_pacientes_fissal, [DIAS_HOSPITALIZACION_TOTAL])` / `[N_HOSPITALIZACIONES]` |
| **Perfil general** (sexo/localización/edad) | Sin DAX: usa `SEXO`, `LOCALIZACION`, `RANGO_EDAD` de `fact_pacientes_fissal` directo como eje de un gráfico de barras + `COUNTROWS` |

> Nota sobre `LOCALIZACION`: la base fuente no trae ningún registro con CIE-10 que
> empiece en C20 (recto) — todo es C18 (colon, 98.9%) o C19 (unión rectosigmoidea,
> 1.1%). No es un filtro del pipeline, lo confirmé directo contra SQL. Vale la pena
> preguntarle a FISSAL si el recto se codifica distinto en su sistema.

---

## 4. Costo por categoría / subcategoría

Grano de `fact_costo_categoria`: paciente × categoría × subcategoría. Para el "costo
mediano por paciente" de una categoría (lo que pide el gráfico de barras del
dashboard), primero hay que colapsar a 1 fila por paciente DENTRO de la categoría, y
recién ahí sacar la mediana — si no, `MEDIANX` calcularía la mediana de las líneas, no
de los pacientes:

```dax
Costo Mediano Categoria =
VAR PorPaciente =
    SUMMARIZE(
        fact_costo_categoria,
        fact_costo_categoria[Codigo_identificacion_paciente],
        "@Costo", SUM(fact_costo_categoria[costo_nominal])
    )
RETURN MEDIANX(PorPaciente, [@Costo])

Pacientes por Categoria = DISTINCTCOUNT(fact_costo_categoria[Codigo_identificacion_paciente])

% del Costo Total =
DIVIDE(
    SUM(fact_costo_categoria[costo_nominal]),
    CALCULATE(SUM(fact_costo_categoria[costo_nominal]), ALL(fact_costo_categoria[categoria_recurso_502]))
)
```

Para replicar el "top 13" del dashboard: pon `[Costo Mediano Categoria]` en un gráfico
de barras con `categoria_recurso_502` en el eje, y usa un filtro visual "Top N = 13" por
esa misma medida (Power BI trae esto nativo en el panel de filtros del visual, no hace
falta DAX).

El gráfico pareado (costo vs. volumen) es el mismo dato en dos visuales lado a lado,
ambos ordenados por `[Costo Mediano Categoria]` descendente (fija el orden en un
visual y copia el "Top N" al otro para que no se desalineen).

**Subcategoría**: mismo patrón, pero agrupando por `subcategoria_recurso_502` en vez de
`categoria_recurso_502`. El dashboard usa **promedio** (`costo_total / pacientes`) para
subcategoría en vez de mediana, porque a ese nivel de detalle no hay percentiles reales
guardados — si quieres la mediana real, es el mismo patrón de `SUMMARIZE` +
`MEDIANX` de arriba, ya que `fact_costo_categoria` sí tiene el grano correcto para
sacarla (a diferencia del Excel original, que solo traía el total).

---

## 5. Otros males (diagnósticos no-CCR)

```dax
Costo Otros Diagnosticos = SUM(fact_costo_otros_diagnosticos[costo_nominal])

Costo por Paciente (Otro Diagnostico) =
DIVIDE(
    SUM(fact_costo_otros_diagnosticos[costo_nominal]),
    DISTINCTCOUNT(fact_costo_otros_diagnosticos[Codigo_identificacion_paciente])
)

Costo Total Cohorte = SUM(fact_pacientes_fissal[MONTO_NETO_TOTAL])
Costo No-CCR = CALCULATE([Costo Otros Diagnosticos], ALL())   -- ver nota
Costo CCR = [Costo Total Cohorte] - [Costo No-CCR]

% CCR = DIVIDE([Costo CCR], [Costo Total Cohorte])
% Otro Cancer = DIVIDE(CALCULATE([Costo Otros Diagnosticos], fact_costo_otros_diagnosticos[tipo_diagnostico]="OTRO_CANCER"), [Costo Total Cohorte])
% No Cancer = DIVIDE(CALCULATE([Costo Otros Diagnosticos], fact_costo_otros_diagnosticos[tipo_diagnostico]="NO_CANCER"), [Costo Total Cohorte])
```

> Ojo con `[Costo No-CCR]`: si tu visual ya está filtrado por paciente (ej. un
> slicer), `SUM(fact_costo_otros_diagnosticos[costo_nominal])` ya respeta ese filtro
> por la relación con `fact_pacientes_fissal` — no necesitas el `ALL()`, lo puse solo
> para el caso "total de toda la cohorte sin filtros". Bórralo si tu visual ya vive
> dentro de un contexto filtrado y quieres que respete esos filtros.

Para el ranking "más caro por paciente" (como tu Excel original, con
`costo_x_paciente` y ordenado de mayor a menor): pon `Codigo_CIE10` +
`Descripcion_CIE10` en una tabla, `[Costo por Paciente (Otro Diagnostico)]` como
medida, y ordena la tabla por esa medida descendente. El gráfico pareado
costo-vs-volumen es igual que en categorías: dos visuales, mismo orden, uno con
`[Costo por Paciente...]` y otro con `DISTINCTCOUNT(paciente)`.

Para los nombres cortos (`descripcion_corta` que armé a mano en el dashboard HTML): no
está en el parquet — si lo quieres en Power BI, arma una tabla chica aparte
(`Codigo_CIE10` → nombre corto) y crúzala, o simplemente usa `Descripcion_CIE10` tal
cual (más largo pero sin mantenimiento manual).

---

## 6. Hospitalización

`fact_hospitalizacion` ya viene a nivel de episodio (deduplicado por ingreso/alta, no
por línea de consumo) — cada fila = 1 hospitalización real.

```dax
Episodios = COUNTROWS(fact_hospitalizacion)
Dias Estancia Mediana = MEDIANX(fact_hospitalizacion, fact_hospitalizacion[dias_estancia])
Costo Hospitalizacion Mediana = MEDIANX(fact_hospitalizacion, fact_hospitalizacion[costo_episodio])
```

Para la distribución por rango de estancia (1 día / 2 días / 3-4 días / ...), crea una
**columna calculada** en `fact_hospitalizacion`:

```dax
Rango Estancia =
SWITCH(
    TRUE(),
    fact_hospitalizacion[dias_estancia] = 0, "0 días",
    fact_hospitalizacion[dias_estancia] = 1, "1 día",
    fact_hospitalizacion[dias_estancia] = 2, "2 días",
    fact_hospitalizacion[dias_estancia] <= 4, "3-4 días",
    fact_hospitalizacion[dias_estancia] <= 7, "5-7 días",
    fact_hospitalizacion[dias_estancia] <= 15, "8-15 días",
    fact_hospitalizacion[dias_estancia] <= 30, "16-30 días",
    fact_hospitalizacion[dias_estancia] <= 90, "31-90 días",
    fact_hospitalizacion[dias_estancia] > 90, "91+ días",
    "Sin dato"
)
```
y úsala como eje de un gráfico de barras con `COUNTROWS` como medida.

---

## 7. Severidad al ingreso

No necesita tabla nueva: `fact_pacientes_fissal[LOCALIZACION]` y
`fact_pacientes_fissal[INGRESO_GRAVE]` ya son atributos por paciente. Arma una matriz
o gráfico con esas dos columnas como ejes, y estas medidas:

```dax
Mortalidad % = DIVIDE(CALCULATE(COUNTROWS(fact_pacientes_fissal), fact_pacientes_fissal[FALLECIDO]=TRUE), COUNTROWS(fact_pacientes_fissal))
Tiempo Sistema Mediana = MEDIANX(fact_pacientes_fissal, fact_pacientes_fissal[TIEMPO_EN_SISTEMA_DIAS])
```
Combínalas con `[Costo Deflactado Mediana (por paciente)]` de la sección 2.

---

## 8. Fallecidos

Columna calculada en `fact_pacientes_fissal` (solo tiene sentido para `FALLECIDO=TRUE`,
usa `TIEMPO_EN_SISTEMA_DIAS` como proxy del tiempo hasta el cierre):

```dax
Tramo Fallecimiento =
IF(
    fact_pacientes_fissal[FALLECIDO] = FALSE(), BLANK(),
    SWITCH(
        TRUE(),
        fact_pacientes_fissal[TIEMPO_EN_SISTEMA_DIAS] <= 30, "0-1 mes",
        fact_pacientes_fissal[TIEMPO_EN_SISTEMA_DIAS] <= 90, "1-3 meses",
        fact_pacientes_fissal[TIEMPO_EN_SISTEMA_DIAS] <= 180, "3-6 meses",
        fact_pacientes_fissal[TIEMPO_EN_SISTEMA_DIAS] <= 365, "6m-1a",
        fact_pacientes_fissal[TIEMPO_EN_SISTEMA_DIAS] <= 730, "1-2a",
        "2a+"
    )
)
```
Úsala como eje, con `COUNTROWS` y `[Costo Deflactado Mediana (por paciente)]` como
medidas.

---

## 9. Evolución anual

```dax
Gasto Total Nominal = SUM(fact_costo_anual[costo_nominal])   -- filtrar bucket="TOTAL" en el visual o en CALCULATE
Gasto Total Deflactado = [Costo Deflactado (Total)]
```
Eje: `dim_anio[anio]`. **Excluye el año en curso** con un filtro de página/visual
(`anio < AÑO_ACTUAL`) — el dashboard lo saca porque el año corriente trae datos
parciales (muchos menos pacientes con gasto que un año completo) y distorsiona la
serie. Deja una nota de texto en el reporte explicando la exclusión, igual que en el
HTML.

---

## 10. EsSalud

Todo vive en `fact_essalud_gcop` (grano: 1 fila por paciente candidato, ID compuesto).

```dax
Pacientes EsSalud = DISTINCTCOUNT(fact_essalud_gcop[ID_ESSALUD_GCOP])
Costo Proyectado Mediana = MEDIANX(fact_essalud_gcop, fact_essalud_gcop[COSTO_PROYECTADO_2024])
Costo Proyectado Total = SUM(fact_essalud_gcop[COSTO_PROYECTADO_2024])
```

**Comparación FISSAL vs. EsSalud**: combina `[Costo Deflactado Mediana (por
paciente)]` (filtrado a Track A + FISSAL regular) con `[Costo Proyectado Mediana]` en
el mismo gráfico de barras — son medidas de tablas distintas sin relación entre sí,
así que Power BI las trata bien como dos series independientes mientras no dependan de
un eje compartido con relación real (usa una tabla "Fuente" desconectada con 2 filas,
"FISSAL" / "EsSalud", y `SWITCH` sobre `SELECTEDVALUE` si quieres un solo visual
parametrizado; o simplemente dos tarjetas/barras separadas, más simple).

> El costo proyectado de EsSalud NO se recalcula en DAX — ya viene resuelto desde
> Python (`complementarios/essalud/03_costo_proyectado.py`) porque depende de un match
> difuso contra un benchmark de costos de FISSAL (Track × localización × nivel de
> atenciones). Replicar ese matching en DAX sería mucho trabajo para cero beneficio;
> si cambian los datos fuente, vuelve a correr ese script y luego
> `build_powerbi_parquets.py`.

---

## 11. SIS

`fact_sis_atenciones` (grano: 1 fila por atención) y `fact_sis_consumos` (grano: 1 fila
por línea de consumo, se relacionan por `CODIGO_ATENCION` / `CODiGO_ATENCION` si quieres
cruzarlas, aunque el dashboard las usa por separado).

```dax
Pacientes SIS = DISTINCTCOUNT(fact_sis_atenciones[CODIGO_PERSONA])
Atenciones SIS = COUNTROWS(fact_sis_atenciones)
Costo Consumos SIS = SUM(fact_sis_consumos[PRECIO_NETO])
```
Sexo/localización/tendencia anual: ejes directos sobre `SEXO`, `COD_DIAGNOSTICO` (o una
columna calculada que mapee el prefijo a Colon/Recto/Unión, igual que
`LOCALIZACION` en FISSAL) y `ANIO_ATENCION`.

> Recordatorio del hallazgo del dashboard: el 100% de estos pacientes fue atendido en
> Lima (`DEPARTAMENTO_EESS`) — no es representativo a nivel nacional. Vale la pena
> ponerlo como nota fija en la página de Power BI también.

---

## 12. Qué NO replicar con DAX

- **ID compuesto de EsSalud** (DNI enmascarado + sexo + fecha de nacimiento
  implícita): ya viene resuelto en `fact_essalud_gcop[ID_ESSALUD_GCOP]`. No hace falta
  rehacerlo.
- **Costo proyectado de EsSalud**: ídem, ya resuelto (ver sección 10).
- **Fix de normalización del diccionario / deduplicación de hospitalización**: ya
  están aplicados en el pipeline Python que genera estos parquets — no hay nada que
  replicar en Power BI, solo consumir los datos ya limpios.
