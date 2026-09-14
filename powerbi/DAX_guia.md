# Guía de modelo y DAX — réplica del dashboard en Power BI
"S/. "#,##0.00;-"S/. "#,##0.00
Este documento explica cómo usar los parquets generados por `build_powerbi_parquets.py`
para reconstruir cada sección del dashboard HTML (`dashboard/index.html`) en Power BI,
sin que Power BI necesite tocar SQL Server. Corre el script, apunta Power BI (modo
**Import**, no DirectQuery) a la carpeta de salida, y copia las medidas de abajo tal
cual — están escritas para que **una sola medida sirva en todas las páginas**, sin
tener que repetir filtros dentro de cada fórmula (así hay menos texto que copiar y
menos lugares donde equivocarse).

Ruta de los parquets:
`C:\Users\eah\apoyoconsultoria.com\File Server - Analytics\3 Proyectos\2025\2025-116-L FPC Dashboard 25\4 Analisis\4 Resultados\Adicional 2026`

---

## 0. Lo primero: entender el filtro de cohorte (léelo antes de crear nada)

El dashboard HTML usa dos cohortes distintas según la sección, y **todas mis tablas
parquet traen a los 24,394 pacientes** (la cohorte completa) — el recorte a "Track A +
FISSAL regular" (8,016 pacientes) lo tienes que poner tú como **filtro de página o de
visual** en Power BI, no está aplicado en los datos. Esta tabla te dice exactamente
dónde ponerlo:

| Página / sección | ¿Filtrar a Track A + FISSAL regular? | Filtro exacto |
|---|---|---|
| Resumen → Cohorte (Pacientes totales, Fallecidos como % de qué) | Solo para los KPIs de costo/tiempo, NO para "Pacientes CCR totales" | Ver nota abajo |
| Resumen → Costo por paciente, Desglose | **Sí** | `fact_pacientes_fissal[TRACK] = "A_COMPLETO"` y `fact_pacientes_fissal[FISSAL_REGULAR] = TRUE()` |
| Resumen → Perfil general (sexo/localización/edad) | **No** — es sobre los 24,394 | — |
| Tiempos entre hitos | **Sí** | igual que arriba — medidas y tabla en la sección 15 |
| Hospitalización | **Sí** | igual que arriba |
| Costo por categoría / subcategoría | **Sí** | igual que arriba |
| Severidad al ingreso | **Sí** | igual que arriba |
| Fallecidos | **Sí**, más `fact_pacientes_fissal[FALLECIDO] = TRUE()` | los 3 filtros juntos |
| Evolución anual | **Sí** | igual que arriba |
| Otros males | **Sí** | igual que arriba |
| EsSalud | No aplica (es otra cohorte, otro ID) | — |
| SIS | No aplica (es otra cohorte, otro ID) | — |

**Cómo ponerlo en Power BI**: ve a la página → panel "Filtros" → arrastra
`fact_pacientes_fissal[TRACK]` y `fact_pacientes_fissal[FISSAL_REGULAR]` al área
"Filtros en esta página" → selecciona `A_COMPLETO` y `Verdadero`. Hazlo una vez por
página (no por visual), así no se te olvida en ningún gráfico de esa página.

**Nota sobre "Pacientes CCR totales" (24,394) vs. "Con tratamiento activo" (8,016)**:
esos dos KPIs específicos del bloque "Cohorte" del Resumen van EN LA MISMA página que
el resto (que sí lleva el filtro), así que si pones el filtro de página quedarían mal.
Para esos dos KPIs puntuales, usa las medidas `[Pacientes CCR Totales]` (sin filtro,
definida abajo) y `[Pacientes Con Tratamiento]` (con su propio `CALCULATE`, también
abajo) — son la excepción a la regla del filtro de página porque necesitan mostrar
ambos números a la vez, uno con cohorte completa y otro sin ella.

> **Si un número te sale más alto de lo esperado**, antes de sospechar de la medida
> verifica que el filtro de página realmente esté aplicado — nos pasó dos veces en
> esta guía (una tarjeta con `TRACK`/`FISSAL_REGULAR` sin aplicar dio 13,265 en vez de
> 2,206; una tabla con solo `TRACK` sin aplicar dio 3,804 en vez de 2,549). El síntoma
> típico: el filtro aparece en el panel como "es X", pero el checkbox de esa opción no
> quedó realmente marcado (a veces basta con escribir el valor en el buscador del
> filtro sin tocar el check). Para confirmar: haz una tarjeta nueva y vacía con
> `[Conteo Pacientes]` sola en esa misma página — si no da el número esperado
> (8,016 con Track A + FISSAL regular puestos, o 2,549 si además está `FALLECIDO`),
> el filtro de página no se está aplicando, no importa qué midas. Prueba quitar el
> filtro y volver a agregarlo.

> **Si una medida "% del total" te da 100% en todas las filas** (en vez de un problema
> de filtro de página), sospecha del **"Ordenar por columna"**: si la columna del eje
> tiene un "Ordenar por columna" asignado (como `Tramo Fallecimiento` → `Orden Tramo
> Fallecimiento`, o `Rango Estancia` → `Orden Rango Estancia`), cualquier `ALL()` que
> uses en un `CALCULATE` para "romper" ese filtro tiene que limpiar **las dos
> columnas juntas** — `ALL(Tabla[ColumnaEje], Tabla[ColumnaOrden])` — no solo la que
> se ve. Ver el ejemplo resuelto en la sección 9.

---

## 1. Relaciones del modelo

Antes de crear ninguna medida, arma estas relaciones en la vista de modelo (todas
"uno a varios", flecha desde la tabla chica hacia la tabla grande):

| Desde (lado "1") | Hasta (lado "*") | Columna |
|---|---|---|
| `dim_anio` | `fact_costo_anual` | `anio` |
| `fact_pacientes_fissal` | `fact_costo_anual` | `Codigo_identificacion_paciente` |
| `fact_pacientes_fissal` | `fact_costo_categoria` | `Codigo_identificacion_paciente` |
| `fact_pacientes_fissal` | `fact_costo_otros_diagnosticos` | `Codigo_identificacion_paciente` |
| `fact_pacientes_fissal` | `fact_hospitalizacion` | `Codigo_identificacion_paciente` |
| `fact_pacientes_fissal` | `fact_tiempos_hitos` | `Codigo_identificacion_paciente` |
| `dim_intervalo` | `fact_tiempos_hitos` | `intervalo` |
| `fact_essalud_gcop` | `fact_essalud_gcop_detalle` | `ID_ESSALUD_GCOP` |

`fact_essalud_gcop`, `fact_sis_atenciones` y `fact_sis_consumos` NO se relacionan con
nada de lo anterior (son otro universo de pacientes, con otro ID) — van sueltas, cada
una alimenta sus propios visuales.

---

## 2. Medidas base — costo deflactado (crear primero, todo lo demás depende de esto)

Copiar tal cual, una por una, como medida nueva sobre `fact_costo_anual`:

```dax
Costo Deflactado Total =
SUMX(
    FILTER(fact_costo_anual, fact_costo_anual[bucket] = "TOTAL"),
    fact_costo_anual[costo_nominal] * RELATED(dim_anio[factor_ipc])
)
```

```dax
Costo Deflactado Tratamiento =
SUMX(
    FILTER(fact_costo_anual, fact_costo_anual[bucket] = "CRC_ATRIBUIBLE"),
    fact_costo_anual[costo_nominal] * RELATED(dim_anio[factor_ipc])
)
```

```dax
Costo Deflactado Soporte =
SUMX(
    FILTER(fact_costo_anual, fact_costo_anual[bucket] = "SOPORTE"),
    fact_costo_anual[costo_nominal] * RELATED(dim_anio[factor_ipc])
)
```

```dax
Costo Deflactado No Atribuible =
SUMX(
    FILTER(fact_costo_anual, fact_costo_anual[bucket] = "NO_ATRIBUIBLE"),
    fact_costo_anual[costo_nominal] * RELATED(dim_anio[factor_ipc])
)
```

Estas 4 dan el TOTAL de lo que esté filtrado en ese momento (útil tal cual para
"Evolución anual", ver sección 6). Para mediana/media POR PACIENTE (lo que pide
"Resumen"), sigue con la sección 3.

---

## 3. Medidas de mediana/media por paciente (para Resumen)

Estas SÍ respetan cualquier filtro de página que pongas (incluido el de Track A +
FISSAL regular de la sección 0) porque arman una tabla de "1 fila por paciente" al
vuelo. Copiar tal cual, sobre cualquier tabla (por convención, sobre
`fact_pacientes_fissal`):

```dax
Costo Deflactado Mediana =
VAR PorPaciente =
    ADDCOLUMNS(
        VALUES(fact_pacientes_fissal[Codigo_identificacion_paciente]),
        "@Costo", [Costo Deflactado Total]
    )
RETURN
    MEDIANX(PorPaciente, [@Costo])
```

```dax
Costo Deflactado Media =
VAR PorPaciente =
    ADDCOLUMNS(
        VALUES(fact_pacientes_fissal[Codigo_identificacion_paciente]),
        "@Costo", [Costo Deflactado Total]
    )
RETURN
    AVERAGEX(PorPaciente, [@Costo])
```

```dax
Costo Tratamiento Mediana =
VAR PorPaciente =
    ADDCOLUMNS(
        VALUES(fact_pacientes_fissal[Codigo_identificacion_paciente]),
        "@Costo", [Costo Deflactado Tratamiento]
    )
RETURN
    MEDIANX(PorPaciente, [@Costo])
```

```dax
Costo Tratamiento Media =
VAR PorPaciente =
    ADDCOLUMNS(
        VALUES(fact_pacientes_fissal[Codigo_identificacion_paciente]),
        "@Costo", [Costo Deflactado Tratamiento]
    )
RETURN
    AVERAGEX(PorPaciente, [@Costo])
```

```dax
Costo Soporte Mediana =
VAR PorPaciente =
    ADDCOLUMNS(
        VALUES(fact_pacientes_fissal[Codigo_identificacion_paciente]),
        "@Costo", [Costo Deflactado Soporte]
    )
RETURN
    MEDIANX(PorPaciente, [@Costo])
```

```dax
Costo Soporte Media =
VAR PorPaciente =
    ADDCOLUMNS(
        VALUES(fact_pacientes_fissal[Codigo_identificacion_paciente]),
        "@Costo", [Costo Deflactado Soporte]
    )
RETURN
    AVERAGEX(PorPaciente, [@Costo])
```

```dax
Costo No Atribuible Mediana =
VAR PorPaciente =
    ADDCOLUMNS(
        VALUES(fact_pacientes_fissal[Codigo_identificacion_paciente]),
        "@Costo", [Costo Deflactado No Atribuible]
    )
RETURN
    MEDIANX(PorPaciente, [@Costo])
```

```dax
Costo No Atribuible Media =
VAR PorPaciente =
    ADDCOLUMNS(
        VALUES(fact_pacientes_fissal[Codigo_identificacion_paciente]),
        "@Costo", [Costo Deflactado No Atribuible]
    )
RETURN
    AVERAGEX(PorPaciente, [@Costo])
```

Y las versiones **nominales** (las que el dashboard muestra chiquitas, como
"nominal S/ 4,599"), estas van directo sobre la columna nominal, sin pasar por
`fact_costo_anual`:

```dax
Costo Nominal Mediana =
MEDIANX(fact_pacientes_fissal, fact_pacientes_fissal[MONTO_NETO_TOTAL])
```

```dax
Costo Nominal Media =
AVERAGEX(fact_pacientes_fissal, fact_pacientes_fissal[MONTO_NETO_TOTAL])
```

---

## 4. Resumen — el resto de las tarjetas

```dax
Pacientes CCR Totales =
DISTINCTCOUNT(fact_pacientes_fissal[Codigo_identificacion_paciente])
```

```dax
Pacientes Con Tratamiento =
CALCULATE(
    [Pacientes CCR Totales],
    fact_pacientes_fissal[TRACK] = "A_COMPLETO",
    fact_pacientes_fissal[FISSAL_REGULAR] = TRUE()
)
```

```dax
Fallecidos =
CALCULATE(
    [Pacientes CCR Totales],
    fact_pacientes_fissal[TRACK] = "A_COMPLETO",
    fact_pacientes_fissal[FISSAL_REGULAR] = TRUE(),
    fact_pacientes_fissal[FALLECIDO] = TRUE()
)
```

```dax
% Fallecidos = DIVIDE([Fallecidos], [Pacientes Con Tratamiento])
```

```dax
Tiempo Sistema Mediana Dias =
MEDIANX(fact_pacientes_fissal, fact_pacientes_fissal[TIEMPO_EN_SISTEMA_DIAS])
```

```dax
Tiempo Sistema Media Dias =
AVERAGEX(fact_pacientes_fissal, fact_pacientes_fissal[TIEMPO_EN_SISTEMA_DIAS])
```

```dax
Tiempo Sistema Mediana Anios = DIVIDE([Tiempo Sistema Mediana Dias], 365)
```

```dax
Tiempo Sistema Media Anios = DIVIDE([Tiempo Sistema Media Dias], 365)
```

```dax
Dias Hospitalizado Mediana =
MEDIANX(fact_pacientes_fissal, fact_pacientes_fissal[DIAS_HOSPITALIZACION_TOTAL])
```

```dax
N Hospitalizaciones Mediana =
MEDIANX(fact_pacientes_fissal, fact_pacientes_fissal[N_HOSPITALIZACIONES])
```

**Perfil general** (sexo / localización / edad): no necesita medida nueva. Arrastra
`fact_pacientes_fissal[SEXO]`, `[LOCALIZACION]` o `[RANGO_EDAD]` al eje de un gráfico
de barras y usa esta única medida como valor:

```dax
Conteo Pacientes = COUNTROWS(fact_pacientes_fissal)
```

Para la edad mediana (dato suelto, "Mediana: 61 años"):

```dax
Edad Mediana = MEDIANX(fact_pacientes_fissal, fact_pacientes_fissal[EDAD_PRIMERA_ATENCION])
```

> **Sin filtro de página en esta sección de Perfil**: si pusiste el filtro de Track A +
> FISSAL regular en toda la página de Resumen, estas 2 medidas van a salir sobre el
> subconjunto filtrado, no sobre los 24,394. Si quieres el perfil de TODA la cohorte
> en la misma página que el resto (que sí necesita el filtro), pon estas 2 medidas
> dentro de un `CALCULATE(..., ALL(fact_pacientes_fissal[TRACK]), ALL(fact_pacientes_fissal[FISSAL_REGULAR]))`
> para que ignoren el filtro de página. Ejemplo para `Conteo Pacientes`:
> `CALCULATE(COUNTROWS(fact_pacientes_fissal), ALL(fact_pacientes_fissal[TRACK]), ALL(fact_pacientes_fissal[FISSAL_REGULAR]))`.

---

## 5. Costo por categoría y subcategoría

Estas 5 medidas sirven para **ambos** gráficos (categoría Y subcategoría) — cuál de
las dos agrupa depende solo de si pones `categoria_recurso_502` o
`subcategoria_recurso_502` en el eje del visual, no hace falta duplicar nada:

```dax
Costo Total 502 = SUM(fact_costo_categoria[costo_nominal])
```

```dax
Pacientes 502 = DISTINCTCOUNT(fact_costo_categoria[Codigo_identificacion_paciente])
```

```dax
Costo Mediano por Paciente 502 =
VAR PorPaciente =
    SUMMARIZE(
        fact_costo_categoria,
        fact_costo_categoria[Codigo_identificacion_paciente],
        "@Costo", SUM(fact_costo_categoria[costo_nominal])
    )
RETURN
    MEDIANX(PorPaciente, [@Costo])
```

```dax
Costo Promedio por Paciente 502 = DIVIDE([Costo Total 502], [Pacientes 502])
```

```dax
% del Costo Total 502 =
DIVIDE(
    [Costo Total 502],
    CALCULATE(
        [Costo Total 502],
        ALL(fact_costo_categoria[categoria_recurso_502]),
        ALL(fact_costo_categoria[subcategoria_recurso_502])
    )
)
```

**Cómo armar los gráficos igual que el dashboard**:
- Categoría: eje = `categoria_recurso_502`, valor = `[Costo Mediano por Paciente 502]`, filtro visual "Top N = 13" por esa misma medida. El gráfico pareado de al lado: mismo eje, valor = `[Pacientes 502]`.
- Subcategoría: eje = `subcategoria_recurso_502`, valor = `[Costo Promedio por Paciente 502]` (el dashboard usa promedio, no mediana, para subcategoría), Top N = 13. Pareado: mismo eje, `[Pacientes 502]`.

---

## 6. Otros males (diagnósticos no-CCR)

```dax
Costo Otros Diagnosticos = SUM(fact_costo_otros_diagnosticos[costo_nominal])
```

```dax
Pacientes Otros Diagnosticos =
DISTINCTCOUNT(fact_costo_otros_diagnosticos[Codigo_identificacion_paciente])
```

```dax
Costo por Paciente Otro Diagnostico =
DIVIDE([Costo Otros Diagnosticos], [Pacientes Otros Diagnosticos])
```

```dax
Costo Total Cohorte Otros Males = SUM(fact_pacientes_fissal[MONTO_NETO_TOTAL])
```

```dax
Costo CCR = [Costo Total Cohorte Otros Males] - [Costo Otros Diagnosticos]
```

> No hace falta una medida aparte para "Costo No CCR": es exactamente
> `[Costo Otros Diagnosticos]` (ya la creaste arriba), así que `Costo CCR` la resta
> directo. Tampoco hace falta envolver `Costo Total Cohorte Otros Males` en nada
> especial: como `Codigo_CIE10` vive en `fact_costo_otros_diagnosticos` y la relación
> es de un solo sentido (de `fact_pacientes_fissal` hacia esa tabla, no al revés), un
> filtro por CIE10 en un gráfico NO afecta a `fact_pacientes_fissal` — esta medida ya
> da el total de la cohorte sin importar qué fila de CIE10 estés mirando al lado.

```dax
% CCR = DIVIDE([Costo CCR], [Costo Total Cohorte Otros Males])
```

Para las tarjetas "Costo en otros cánceres" / "Costo no-cáncer" con su conteo de
pacientes al lado:

```dax
Costo Otro Cancer =
CALCULATE([Costo Otros Diagnosticos], fact_costo_otros_diagnosticos[tipo_diagnostico] = "OTRO_CANCER")
```

```dax
Costo No Cancer =
CALCULATE([Costo Otros Diagnosticos], fact_costo_otros_diagnosticos[tipo_diagnostico] = "NO_CANCER")
```

```dax
Pacientes Otro Cancer =
CALCULATE(
    DISTINCTCOUNT(fact_costo_otros_diagnosticos[Codigo_identificacion_paciente]),
    fact_costo_otros_diagnosticos[tipo_diagnostico] = "OTRO_CANCER"
)
```

```dax
Pacientes No Cancer =
CALCULATE(
    DISTINCTCOUNT(fact_costo_otros_diagnosticos[Codigo_identificacion_paciente]),
    fact_costo_otros_diagnosticos[tipo_diagnostico] = "NO_CANCER"
)
```

```dax
% Otro Cancer = DIVIDE([Costo Otro Cancer], [Costo Total Cohorte Otros Males])
```

```dax
% No Cancer = DIVIDE([Costo No Cancer], [Costo Total Cohorte Otros Males])
```

**Nombre corto**: `fact_costo_otros_diagnosticos` ya trae la columna
`descripcion_corta` (los mismos ~20 nombres curados a mano del dashboard, con un
fallback automático para el resto de códigos que simplifica "TUMOR MALIGNO DE(L)..."
a "Cáncer de..."). Actualiza la consulta en Power BI (clic derecho → Actualizar) para
traerla, y úsala en vez de `Descripcion_CIE10` en los ejes.

**Cómo armar el gráfico pareado, paso a paso** (esto es fácil de armar mal — el orden
importa):

1. Crea los dos visuales de barras: uno con eje `descripcion_corta` y valor
   `[Costo por Paciente Otro Diagnostico]`, el otro con el mismo eje y valor
   `[Pacientes Otros Diagnosticos]`.
2. **El filtro "Top N" tiene que ir por costo TOTAL, no por costo por paciente** — si
   filtras el Top 20 usando `[Costo por Paciente Otro Diagnostico]` directamente, te
   van a aparecer diagnósticos rarísimos con 1-2 pacientes donde ese promedio es puro
   ruido estadístico (ej. un trasplante de riñón de un solo paciente saliendo primero).
   La lista original arma el Top 20 por relevancia (costo total) y RECIÉN ahí lo
   reordena por costo/paciente.
   Ponlo como **filtro de página** (no de visual, para que quede igual en ambos
   gráficos): panel de Filtros → agrega `descripcion_corta` (o `Codigo_CIE10`) a
   "Filtros en esta página" → Tipo de filtro: **Top N** → N = 20 → campo **"Por
   valor"**: `Costo Otros Diagnosticos` (el total, sección 6 — NO
   `Costo por Paciente Otro Diagnostico`).
3. Ahora ordena las barras dentro de esos 20 por costo por paciente: en el visual de
   "Costo por paciente", ya debería ordenar solo por su propio valor (es lo que está
   graficando). En el visual de "N° de pacientes", agrega
   `Costo por Paciente Otro Diagnostico` al pozo de Tooltips y usa "..." → Ordenar por
   → esa medida, igual que en la sección de Categoría/Subcategoría — así los dos
   gráficos quedan en el mismo orden.

Si después de esto los números todavía no te cuadran con lo que tenías, revisa que el
filtro de página de Track A + FISSAL regular (sección 0) también esté puesto en esta
página — sin él, el Top N sale de los 24,394 pacientes en vez de los 8,016 con
tratamiento.

---

## 7. Hospitalización

`fact_hospitalizacion` ya viene 1 fila = 1 episodio real (deduplicado por
ingreso/alta, no por línea de consumo).

```dax
Episodios Hospitalizacion = COUNTROWS(fact_hospitalizacion)
```

```dax
Pacientes Hospitalizados =
DISTINCTCOUNT(fact_hospitalizacion[Codigo_identificacion_paciente])
```

```dax
Episodios por Paciente Mediana =
VAR PorPaciente =
    SUMMARIZE(
        fact_hospitalizacion,
        fact_hospitalizacion[Codigo_identificacion_paciente],
        "@Episodios", COUNTROWS(fact_hospitalizacion)
    )
RETURN
    MEDIANX(PorPaciente, [@Episodios])
```

```dax
Episodios por Paciente Media =
VAR PorPaciente =
    SUMMARIZE(
        fact_hospitalizacion,
        fact_hospitalizacion[Codigo_identificacion_paciente],
        "@Episodios", COUNTROWS(fact_hospitalizacion)
    )
RETURN
    AVERAGEX(PorPaciente, [@Episodios])
```

```dax
Dias Estancia Mediana = MEDIANX(fact_hospitalizacion, fact_hospitalizacion[dias_estancia])
```

```dax
Dias Estancia Media = AVERAGEX(fact_hospitalizacion, fact_hospitalizacion[dias_estancia])
```

> Esta mediana da **0** con Track A + FISSAL regular puesto — es correcto, no es un
> error: 70.7% de los episodios tienen estancia = 0 días (ingreso y alta el mismo
> día). Si quieres un número más útil para una tarjeta ("cuánto dura una
> hospitalización quenta"), usa la mediana **solo de los episodios con estancia > 0**:

```dax
Dias Estancia Mediana Solo Mayor a Cero =
CALCULATE(
    MEDIANX(fact_hospitalizacion, fact_hospitalizacion[dias_estancia]),
    fact_hospitalizacion[dias_estancia] > 0
)
```

```dax
Dias Estancia Media Solo Mayor a Cero =
CALCULATE(
    AVERAGEX(fact_hospitalizacion, fact_hospitalizacion[dias_estancia]),
    fact_hospitalizacion[dias_estancia] > 0
)
```

> Con Track A + FISSAL regular puesto, esta da 6 días mediana / 8.6 días media — el
> mismo número que ya tenías en el dashboard original ("Estancia mediana (solo >0)").

```dax
Costo Episodio Mediana = MEDIANX(fact_hospitalizacion, fact_hospitalizacion[costo_episodio])
```

```dax
Costo Episodio Media = AVERAGEX(fact_hospitalizacion, fact_hospitalizacion[costo_episodio])
```

> `Costo Episodio Mediana/Media` es el costo de **un** episodio (fila de
> `fact_hospitalizacion`, ya deduplicada por ingreso/alta). Como la mayoría de
> episodios son cortos o ambulatorios (64% con estancia = 0 días), esta mediana sale
> baja (~S/72) aunque haya internaciones largas y caras — esas jalan la MEDIA hacia
> arriba (~S/999) pero no la mediana, porque son minoría. Si lo que quieres es
> replicar la tarjeta "Costo por hospitalización" del dashboard original (cuánto le
> cuesta a UN PACIENTE la hospitalización en total, sumando TODOS sus episodios), es
> una medida distinta:

```dax
Costo Hospitalizacion por Paciente Mediana =
VAR PorPaciente =
    SUMMARIZE(
        fact_hospitalizacion,
        fact_hospitalizacion[Codigo_identificacion_paciente],
        "@Costo", SUM(fact_hospitalizacion[costo_episodio])
    )
RETURN
    MEDIANX(PorPaciente, [@Costo])
```

```dax
Costo Hospitalizacion por Paciente Media =
VAR PorPaciente =
    SUMMARIZE(
        fact_hospitalizacion,
        fact_hospitalizacion[Codigo_identificacion_paciente],
        "@Costo", SUM(fact_hospitalizacion[costo_episodio])
    )
RETURN
    AVERAGEX(PorPaciente, [@Costo])
```

> Esta es la que da S/ 3,224 mediana / S/ 5,295 media con el filtro de Track A +
> FISSAL regular puesto — la que coincide con el S/ 3,175 del dashboard original (la
> pequeña diferencia es solo por el refresh de datos entre corridas).

Para la distribución por rango de estancia (1 día / 2 días / 3-4 días / ...), esto NO
es una medida — es una **columna calculada** nueva dentro de `fact_hospitalizacion`
(clic derecho en la tabla → Nueva columna):

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

Para la tarjeta "Episodios con estancia = 0 días" (ingreso y alta el mismo día):

```dax
Episodios Estancia Cero =
CALCULATE(COUNTROWS(fact_hospitalizacion), fact_hospitalizacion[dias_estancia] = 0)
```

```dax
% Episodios Estancia Cero =
DIVIDE([Episodios Estancia Cero], [Episodios Hospitalizacion])
```

Úsala como eje de un gráfico de barras, con `[Episodios Hospitalizacion]` como valor.

---

## 8. Severidad al ingreso

No necesita tabla nueva. En una matriz o gráfico, usa `fact_pacientes_fissal[LOCALIZACION]`
y `fact_pacientes_fissal[INGRESO_GRAVE]` como ejes, y estas medidas:

```dax
Mortalidad % =
DIVIDE(
    CALCULATE(COUNTROWS(fact_pacientes_fissal), fact_pacientes_fissal[FALLECIDO] = TRUE()),
    COUNTROWS(fact_pacientes_fissal)
)
```

Combínala con `[Costo Deflactado Mediana]`, `[Costo Deflactado Media]`,
`[Tiempo Sistema Mediana Dias]` y `[Dias Hospitalizado Mediana]` de las secciones 3 y 4
— ya están hechas para respetar cualquier filtro/eje que pongas, no hace falta
reescribirlas.

---

## 9. Fallecidos

Columna calculada nueva en `fact_pacientes_fissal` (clic derecho en la tabla → Nueva
columna):

```dax
Tramo Fallecimiento =
IF(
    fact_pacientes_fissal[FALLECIDO] = FALSE(),
    BLANK(),
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

**Para el orden de las filas** (0-1 mes → 1-3 meses → 3-6 meses → 6m-1a → 1-2a → 2a+,
no alfabético): esta vez SÍ se puede resolver con una columna calculada, sin riesgo de
dependencia circular — porque la nueva columna se basa en `TIEMPO_EN_SISTEMA_DIAS` y
`FALLECIDO` (no en `Tramo Fallecimiento` misma):

```dax
Orden Tramo Fallecimiento =
IF(
    fact_pacientes_fissal[FALLECIDO] = FALSE(),
    BLANK(),
    SWITCH(
        TRUE(),
        fact_pacientes_fissal[TIEMPO_EN_SISTEMA_DIAS] <= 30, 1,
        fact_pacientes_fissal[TIEMPO_EN_SISTEMA_DIAS] <= 90, 2,
        fact_pacientes_fissal[TIEMPO_EN_SISTEMA_DIAS] <= 180, 3,
        fact_pacientes_fissal[TIEMPO_EN_SISTEMA_DIAS] <= 365, 4,
        fact_pacientes_fissal[TIEMPO_EN_SISTEMA_DIAS] <= 730, 5,
        6
    )
)
```

Luego: selecciona la columna `Tramo Fallecimiento` → Herramientas de columna →
Ordenar por columna → `Orden Tramo Fallecimiento`.

Úsala como eje, con `[Conteo Pacientes]` (sección 4) y `[Costo Deflactado Mediana]`
(sección 3) como medidas. No hace falta filtrar `FALLECIDO = TRUE()` aparte: la
columna ya da `BLANK()` para los vivos, y Power BI no los muestra en el eje.

Para la columna "% del total" (qué proporción de TODOS los fallecidos cae en ese
tramo):

```dax
% del Total Fallecidos =
DIVIDE(
    COUNTROWS(fact_pacientes_fissal),
    CALCULATE(
        COUNTROWS(fact_pacientes_fissal),
        ALL(fact_pacientes_fissal[Tramo Fallecimiento], fact_pacientes_fissal[Orden Tramo Fallecimiento]),
        fact_pacientes_fissal[FALLECIDO] = TRUE()
    )
)
```

> **Ojo con el "Ordenar por columna"**: si le pusiste "Ordenar por columna" a
> `Tramo Fallecimiento` apuntando a `Orden Tramo Fallecimiento` (como se indica más
> abajo), Power BI arma el contexto de fila de la tabla usando **las dos columnas
> juntas**, no solo la que se ve. Por eso `ALL()` tiene que limpiar ambas a la vez —
> si solo le pones `ALL(fact_pacientes_fissal[Tramo Fallecimiento])`, queda el filtro
> escondido de `Orden Tramo Fallecimiento` sin limpiar, y la medida da 100% en todas
> las filas (numerador = denominador siempre). Es un comportamiento real de Power BI,
> no un error tuyo — pasa cada vez que combinas "Ordenar por columna" con un `ALL()`
> que solo limpia la columna visible.

---

## 10. Evolución anual

```dax
Gasto Total Nominal =
CALCULATE(
    SUM(fact_costo_anual[costo_nominal]),
    fact_costo_anual[bucket] = "TOTAL"
)
```

```dax
Gasto Total Deflactado = [Costo Deflactado Total]
```

Eje: `dim_anio[anio]`. **Excluye el año en curso**: filtro visual o de página
`dim_anio[anio] < AÑO_ACTUAL` (hoy sería `< 2026`, ajústalo cuando cambie el año). El
dashboard lo saca porque el año corriente trae muchos menos pacientes con gasto que un
año completo y distorsiona la serie — deja una caja de texto con esa nota en el reporte,
igual que el HTML.

---

## 11. EsSalud

Todo vive en `fact_essalud_gcop` (1 fila por paciente candidato, ID compuesto). Esta
tabla NO lleva el filtro de Track A + FISSAL regular de FISSAL (es una cohorte
completamente distinta) — úsala tal cual, sin agregar esos dos filtros.

```dax
Pacientes EsSalud = DISTINCTCOUNT(fact_essalud_gcop[ID_ESSALUD_GCOP])
```

```dax
Pacientes EsSalud 2+ Atenciones =
CALCULATE([Pacientes EsSalud], fact_essalud_gcop[N_ATENCIONES] >= 2)
```

```dax
Pacientes EsSalud 10+ Atenciones =
CALCULATE([Pacientes EsSalud], fact_essalud_gcop[N_ATENCIONES] >= 10)
```

```dax
Costo Proyectado Mediana = MEDIANX(fact_essalud_gcop, fact_essalud_gcop[COSTO_PROYECTADO_2024])
```

```dax
Costo Proyectado Media = AVERAGEX(fact_essalud_gcop, fact_essalud_gcop[COSTO_PROYECTADO_2024])
```

```dax
Costo Proyectado Total = SUM(fact_essalud_gcop[COSTO_PROYECTADO_2024])
```

**Comparación FISSAL (real) vs. EsSalud (proyectado)**: como son tablas sin relación
entre sí, la forma más simple es una tabla/matriz con 4 tarjetas sueltas — dos con
`[Costo Deflactado Mediana]` / `[Costo Deflactado Media]` (filtradas a Track A +
FISSAL regular, sección 0) rotuladas "FISSAL", y dos con `[Costo Proyectado Mediana]`
/ `[Costo Proyectado Media]` rotuladas "EsSalud". No hace falta DAX adicional para
"unirlas" en un solo visual.

> El costo proyectado **no se recalcula en DAX** — ya viene resuelto desde Python
> (`complementarios/essalud/03_costo_proyectado.py`) porque depende de un match difuso
> contra un benchmark de costos de FISSAL (Track × localización × nivel de
> atenciones). Si cambian los datos fuente, vuelve a correr ese script y luego
> `build_powerbi_parquets.py` — no hay nada que tocar en Power BI.

### Especialidades más frecuentes y validación del ID

Estas dos NO se pueden armar con `fact_essalud_gcop` (1 fila por paciente) — necesitan
`fact_essalud_gcop_detalle` (1 fila por **registro/consulta**, 101,119 filas). Arma la
relación `fact_essalud_gcop[ID_ESSALUD_GCOP]` (1) → `fact_essalud_gcop_detalle[ID_ESSALUD_GCOP]` (*)
si no la pusiste en la sección 1.

```dax
Registros EsSalud Detalle = COUNTROWS(fact_essalud_gcop_detalle)
```

Úsala con `fact_essalud_gcop_detalle[SERVICIO]` en el eje de un gráfico de barras
horizontal, ordenado descendente — eso es "Especialidades más frecuentes (GCOP)".

La validación ("92.8% de los IDs con 2+ registros tienen un solo código CIE-10") es
más avanzada — solo vale la pena si de verdad quieres mostrar ese dato en el reporte,
no es crítica para nada más:

```dax
Validacion CIE10 % =
VAR PacientesConDatos =
    FILTER(
        VALUES(fact_essalud_gcop_detalle[ID_ESSALUD_GCOP]),
        CALCULATE(COUNTROWS(fact_essalud_gcop_detalle)) >= 2
    )
VAR PacientesConsistentes =
    FILTER(
        PacientesConDatos,
        CALCULATE(DISTINCTCOUNT(fact_essalud_gcop_detalle[DIAGNOSTICO3])) = 1
    )
RETURN
    DIVIDE(COUNTROWS(PacientesConsistentes), COUNTROWS(PacientesConDatos))
```

---

## 12. SIS

```dax
Pacientes SIS = DISTINCTCOUNT(fact_sis_atenciones[CODIGO_PERSONA])
```

```dax
Atenciones SIS = COUNTROWS(fact_sis_atenciones)
```

```dax
Costo Consumos SIS = SUM(fact_sis_consumos[PRECIO_NETO])
```

```dax
Atenciones por Paciente SIS = DIVIDE([Atenciones SIS], [Pacientes SIS])
```

```dax
Costo por Atencion SIS =
DIVIDE(
    SUM(fact_sis_consumos[PRECIO_NETO]),
    DISTINCTCOUNT(fact_sis_consumos[CODiGO_ATENCION])
)
```

```dax
Pacientes SIS Con 3+ Atenciones =
VAR PorPaciente =
    SUMMARIZE(
        fact_sis_atenciones,
        fact_sis_atenciones[CODIGO_PERSONA],
        "@Atenciones", DISTINCTCOUNT(fact_sis_atenciones[FECHA_ATENCION])
    )
RETURN
    COUNTROWS(FILTER(PorPaciente, [@Atenciones] >= 3))
```

```dax
% Pacientes SIS Con 1 Atencion =
VAR PorPaciente =
    SUMMARIZE(
        fact_sis_atenciones,
        fact_sis_atenciones[CODIGO_PERSONA],
        "@Atenciones", DISTINCTCOUNT(fact_sis_atenciones[FECHA_ATENCION])
    )
VAR Con1 = FILTER(PorPaciente, [@Atenciones] = 1)
RETURN
    DIVIDE(COUNTROWS(Con1), COUNTROWS(PorPaciente))
```

Sexo / tendencia anual: ejes directos sobre `fact_sis_atenciones[SEXO]` y
`[ANIO_ATENCION]`, con `DISTINCTCOUNT(fact_sis_atenciones[CODIGO_PERSONA])` como valor
(no `[Atenciones SIS]`/`COUNTROWS` — eso cuenta atenciones, no pacientes, y un
paciente con 2+ atenciones se contaría más de una vez).

Localización (Colon/Recto/Unión rectosigmoidea): no viene como columna lista, es el
prefijo de `COD_DIAGNOSTICO`. Columna calculada nueva en `fact_sis_atenciones`:

```dax
Localizacion SIS =
SWITCH(
    TRUE(),
    LEFT(fact_sis_atenciones[COD_DIAGNOSTICO], 3) = "C18", "Colon",
    LEFT(fact_sis_atenciones[COD_DIAGNOSTICO], 3) = "C19", "Union rectosigmoidea",
    LEFT(fact_sis_atenciones[COD_DIAGNOSTICO], 3) = "C20", "Recto",
    "Otro"
)
```

> Úsala en el eje del gráfico de localización con `DISTINCTCOUNT(fact_sis_atenciones[CODIGO_PERSONA])`
> como valor, mismo motivo que arriba. Nota chica: si un paciente tiene 2+ atenciones
> con códigos CIE-10 de sitios distintos (colon en una visita, unión rectosigmoidea en
> otra), contaría en ambas categorías — afecta como máximo a los 32 pacientes con 3+
> atenciones, así que no vale la pena resolverlo con DAX adicional a menos que te
> importe la precisión exacta ahí.

> Recordatorio del hallazgo del dashboard: el 100% de estos pacientes fue atendido en
> Lima (`DEPARTAMENTO_EESS`) — no es representativo a nivel nacional. Ponlo como nota
> fija en la página de Power BI también.

---

## 13. Checklist rápido de creación (orden recomendado)

1. Carga los 12 parquets en Power BI (Obtener datos → Carpeta, o uno por uno).
2. Arma las 8 relaciones de la sección 1.
3. Crea las 4 medidas base de la sección 2.
4. Crea las 8 medidas de mediana/media de la sección 3, más las 2 nominales.
5. Crea las medidas de Resumen (sección 4) — incluye las 2 medidas del Perfil general.
6. Crea las 5 medidas de Categoría/Subcategoría (sección 5).
7. Crea las 12 medidas de Otros males (sección 6).
8. Crea las 13 medidas + 1 columna calculada de Hospitalización (sección 7).
9. Crea la medida de Severidad (sección 8) — reutiliza medidas ya hechas.
10. Crea la columna calculada + 1 medida de Fallecidos (sección 9).
11. Crea las 2 medidas de Evolución anual (sección 10).
12. Crea las 8 medidas de EsSalud (sección 11) — incluye las 2 de "Especialidades/Validación".
13. Crea las 7 medidas + 1 columna calculada de SIS (sección 12).
14. Crea las 7 medidas de Tiempos entre hitos (sección 15).
15. Recién ahí pon los filtros de página de la sección 0, página por página.

> Este checklist ya refleja la versión más reciente de la guía (con los huecos que
> fuiste encontrando ya tapados: Pacientes Hospitalizados, Episodios por Paciente,
> Episodios Estancia Cero, % del Total Fallecidos, Costo/Pacientes por tipo de cáncer
> en Otros males, Especialidades/Validación de EsSalud, y las 4 medidas nuevas de
> SIS). Si tenías medidas creadas de una versión anterior, no hay que borrar nada,
> solo agregar las que falten.

## 14. Qué NO replicar con DAX

- **ID compuesto de EsSalud** (DNI enmascarado + sexo + fecha de nacimiento
  implícita): ya viene resuelto en `fact_essalud_gcop[ID_ESSALUD_GCOP]`.
- **Costo proyectado de EsSalud**: ídem (sección 11).
- **Fix de normalización del diccionario, deduplicación de hospitalización, corrección
  del código de sexo**: ya están aplicados en el pipeline Python que genera estos
  parquets — no hay nada que replicar en Power BI, solo consumir los datos ya limpios.

---

## 15. Tiempos entre hitos

Esta tabla del dashboard tiene una fila por CADA INTERVALO (Ingreso a Intervención,
Intervención a Cierre, Trayectoria total, Tiempo en sistema, Hospitalización total,
N° de hospitalizaciones), y cada fila trae su propio n / media / mediana / P25 / P75 /
P95 / máximo. En `fact_pacientes_fissal` esos 6 datos viven como 6 columnas separadas
(una por paciente) — para no tener que escribir un `SWITCH` distinto por cada
estadística, ya vienen reestructurados en **formato largo** en dos tablas nuevas:

- **`fact_tiempos_hitos`**: 1 fila por paciente × intervalo, con la columna `dias`.
  Ya excluye los nulos y los negativos (mismo criterio que usaba el Excel original).
- **`dim_intervalo`**: 6 filas, una por intervalo, con su `explicacion` en texto — para
  poder mostrar la descripción de cada fila en una tarjeta o un tooltip.

Arma la relación `dim_intervalo[intervalo]` (1) → `fact_tiempos_hitos[intervalo]` (*)
si no la pusiste ya en la sección 1. Copiar estas 7 medidas tal cual:

```dax
Tiempos N =
COUNTROWS(fact_tiempos_hitos)
```

```dax
Tiempos Media =
AVERAGEX(fact_tiempos_hitos, fact_tiempos_hitos[dias])
```

```dax
Tiempos Mediana =
MEDIANX(fact_tiempos_hitos, fact_tiempos_hitos[dias])
```

```dax
Tiempos P25 =
PERCENTILEX.INC(fact_tiempos_hitos, fact_tiempos_hitos[dias], 0.25)
```

```dax
Tiempos P75 =
PERCENTILEX.INC(fact_tiempos_hitos, fact_tiempos_hitos[dias], 0.75)
```

```dax
Tiempos P95 =
PERCENTILEX.INC(fact_tiempos_hitos, fact_tiempos_hitos[dias], 0.95)
```

```dax
Tiempos Max =
MAXX(fact_tiempos_hitos, fact_tiempos_hitos[dias])
```

**Cómo armar la tabla igual que el dashboard**: crea un visual de tabla, y en
"Columnas" arrastra en este orden: `dim_intervalo[intervalo]`, `dim_intervalo[explicacion]`,
`[Tiempos N]`, `[Tiempos Media]`, `[Tiempos Mediana]`, `[Tiempos P25]`, `[Tiempos P75]`,
`[Tiempos P95]`, `[Tiempos Max]`. Usa `dim_intervalo[intervalo]` (no
`fact_tiempos_hitos[intervalo]`) para que el orden de las filas sea estable.

No olvides el filtro de página de la sección 0 (`TRACK="A_COMPLETO"` y
`FISSAL_REGULAR=TRUE()` sobre `fact_pacientes_fissal`) — como `fact_tiempos_hitos` se
relaciona con `fact_pacientes_fissal`, el filtro se propaga solo. Verificación rápida:
con ese filtro puesto, "Ingreso a Intervencion" debería dar `Tiempos N = 6,885` y
`Tiempos Mediana = 31`; "Trayectoria total" debería dar `Tiempos N = 8,016` y
`Tiempos Mediana = 641` — son los mismos números que ya viste en el dashboard HTML.

### Orden de las filas

Por defecto Power BI ordena `intervalo` alfabéticamente (Hospitalización, Ingreso,
Intervención, Número, Tiempo, Trayectoria), no en el orden narrativo del dashboard
(Ingreso → Intervención → Trayectoria → Tiempo en sistema → Hospitalización → N°
hospitalizaciones).

**No lo resuelvas con una columna calculada tipo `SWITCH(dim_intervalo[intervalo], ...)`**
— Power BI la rechaza con "dependencia circular", porque para ordenar `intervalo`
usando esa columna, `intervalo` pasaría a depender de una columna que a su vez
depende de `intervalo` (el `SWITCH` la lee). Es un ciclo real, no un bug de Power BI.

Por eso ya agregué el orden directo en el archivo fuente: `dim_intervalo.parquet`
trae una tercera columna, **`orden`** (1 a 6, en el mismo orden narrativo de arriba),
que no depende de `intervalo` — así no hay ciclo posible. Si ya habías cargado los
datos en Power BI antes de este cambio, dale clic derecho a la consulta
`dim_intervalo` → **Actualizar** para traer la columna nueva.

Con `orden` ya en el modelo: selecciona la columna `dim_intervalo[intervalo]` (clic
sobre la columna en el panel de campos, no sobre una medida) → pestaña **Herramientas
de columna** → botón **Ordenar por columna** → elige `orden`. Con eso, cualquier
visual que use `intervalo` (tabla, gráfico de barras, lo que sea) va a respetar ese
orden en vez del alfabético — no hace falta tocar cada visual por separado, y no
hiciste ninguna columna calculada.

> Nota aparte sobre tu captura: la fila "Total" del final que te está mostrando Power
> BI es el total automático del visual de tabla — como mezcla los 6 intervalos en una
> sola mediana/percentil, ese número no tiene una lectura clara (no es "la suma de las
> medianas", es la mediana de las 46,948 filas de todos los intervalos juntos, cosas
> que no son comparables entre sí). Si no lo quieres, apágalo en Formato del visual →
> Estilo de celda → Totales → Fila (o "Total" en versiones más nuevas de Power BI).
