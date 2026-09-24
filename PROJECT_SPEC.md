# Maintenance Performance Suite

**Sistema de análisis y gestión de mantenimiento industrial sobre datos SAP, con metodología de Mejora Enfocada (Kobetsu Kaizen) y benchmark externo.**

> Especificación maestra de proyecto. Este documento es la **única fuente de verdad**: un agente de IA que desarrolle código debe poder construir el sistema completo leyendo solo este archivo. No requiere contexto conversacional previo.

---

## 0. Cómo usar este documento

| Si eres… | Lee |
|---|---|
| Agente de IA que va a codificar | Todo, en orden. Las secciones 4–9 son el contrato técnico. |
| Revisor humano / reclutador | §1, §2, §3, §13 |
| Analista de negocio | §2, §3, §7, §10, §11 |

**Reglas no negociables para el implementador:**

1. **Neutralidad.** El proyecto es un desarrollo personal genérico. No debe contener nombres de empresas, marcas, logos, plantas reales, nombres de personas, ni datos productivos. Todo dato es sintético.
2. **Trazabilidad SAP.** Todo indicador, visual y tabla declara explícitamente la transacción SAP de origen. Si no hay origen, se declara como *brecha de información*.
3. **Honestidad analítica.** Donde SAP no entrega el dato, se declara la brecha y se usa un *proxy* etiquetado como tal. Nunca se finge precisión.
4. **Mejora Enfocada como hilo conductor.** El sistema no reporta KPI: convierte pérdidas en iniciativas priorizadas con ahorro verificable.
5. **Calidad visual de nivel mundial.** El estándar estético es el de un producto BI comercial, no el de un dashboard interno. Ver §9.

---

## 1. Resumen del proyecto

### 1.1 Problema

En plantas de producción masiva con SAP PM, los datos de mantenimiento existen pero no se convierten en decisiones:

- Los indicadores viven en planillas dispersas y cada área los calcula distinto.
- Predomina la cultura reactiva; el preventivo no se mide ni se cumple.
- El costo real no se descompone por equipo, causa ni tipo de mantenimiento.
- Los registros incompletos en SAP restan credibilidad a todo KPI.

### 1.2 Solución

Una cadena de valor de datos gobernada:

```
SAP PM/MM/CO/PP  →  Power Query (M)  →  Modelo estrella  →  DAX  →  Dashboard 12 páginas
   extracción        limpieza y          7 hechos           40        decisión ejecutiva
                     derivadas           8 dimensiones    medidas        y técnica
```

Sobre esa base se monta el **pilar de Mejora Enfocada**: árbol de pérdidas → priorización impacto/esfuerzo → cartera A3 con ciclo PDCA → ahorro verificado en CO → estándar actualizado.

### 1.3 Entregables del repositorio

| # | Entregable | Formato | Estado |
|---|---|---|---|
| 1 | Especificación maestra (este documento) | `.md` | ✅ |
| 2 | Aplicación navegable con filtros funcionales | `.html` autocontenido | ✅ |
| 3 | Modelo semántico (diccionario + relaciones) | `.xlsx` | ✅ |
| 4 | Toolkit técnico completo | `.docx` | ✅ |
| 5 | Presentación ejecutiva | `.pptx` | ✅ |
| 6 | Consultas Power Query | integradas en las particiones TMDL | ✅ |
| 7 | Medidas DAX | 79 medidas en `_Medidas.tmdl` | ✅ |
| 8 | Generador de dataset sintético | Python | ✅ |
| 9 | Proyecto Power BI | `.pbip` (TMDL + PBIR) | ✅ |

---

## 2. Marco metodológico

### 2.1 Los 5 Fundacionales del Mantenimiento

Cada indicador del sistema se ancla a un pilar. Esto evita el "muro de KPIs" sin narrativa.

| Pilar | Nombre | Qué gobierna | KPIs ancla |
|---|---|---|---|
| **F1** | Gestión de Activos | Maestro de equipos, criticidad, jerarquía técnica | Órdenes sin equipo, cobertura de criticidad |
| **F2** | Planificación y Programación | Planes preventivos, programación, backlog, capacidad | Cumplimiento PM, backlog en semanas, % preventivo |
| **F3** | Ejecución y Cierre | Órdenes ejecutadas, confirmaciones, disciplina de cierre | Tiempo de cierre, SLA, % retrasadas, desviación HH |
| **F4** | Costos y Recursos | Costo real vs. plan, repuestos, servicios, mano de obra | Costo total, varianza, % costo preventivo, costo/ton |
| **F5** | Confiabilidad | MTTR, MTBF, disponibilidad, causa raíz | MTBF, MTTR, disponibilidad, Pareto de fallas |
| **T** | Transversal (TPM) | Calidad de datos y madurez cultural | Índice de calidad de datos, score de madurez |

### 2.2 Mejora Enfocada (Kobetsu Kaizen) — el motor del sistema

La Mejora Enfocada es el pilar del TPM que **ataca pérdidas específicas y cuantificadas** con equipos multidisciplinarios. Su lógica estructura todo el dashboard:

**Paso 1 — Identificar la pérdida.** Convertir horas de detención y desperdicio en dinero:

```
Pérdida_M$ = horas_de_pérdida × margen_de_contribución_por_hora
```

**Paso 2 — Árbol de pérdidas (las 6 grandes pérdidas).** Toda pérdida se clasifica en una de estas categorías, con su fuente:

| # | Pérdida | Componente OEE | Fuente de dato |
|---|---|---|---|
| 1 | Averías / fallas | Disponibilidad | `IW29` (avisos) + duración de parada |
| 2 | Setup y ajustes | Disponibilidad | `COOIS` / registro de cambio de formato |
| 3 | Paradas menores / vacío | Rendimiento | MES o registro de línea (**brecha**) |
| 4 | Pérdida de velocidad | Rendimiento | `COOIS` vs. velocidad nominal (**brecha**) |
| 5 | Defectos y reproceso | Calidad | Sistema de calidad (**brecha**) |
| 6 | Arranque / puesta en régimen | Calidad | `COOIS` (**brecha**) |

**Paso 3 — Priorizar** en matriz impacto (M$/año) × esfuerzo (complejidad 1–5). Se atacan primero las burbujas de alto impacto y bajo esfuerzo.

**Paso 4 — Ciclo PDCA con criterio de salida verificable:**

| Fase | Actividad | Criterio de salida |
|---|---|---|
| **Plan** | Cuantificar la pérdida en SAP, definir meta, causa raíz (5 por qué / Ishikawa) | A3 con meta numérica y causa raíz validada |
| **Do** | Ejecutar contramedidas como órdenes `PM04` (mejora) trazables al A3 | Órdenes cerradas con HH confirmadas |
| **Check** | Verificar MTBF, disponibilidad y costo a 30/60/90 días | Delta medido en el tablero |
| **Act** | Estandarizar: actualizar plan preventivo, procedimiento, lección aprendida | Plan `IP02` actualizado |

**Regla del pilar:** ninguna iniciativa se cierra sin (a) ahorro confirmado en CO y (b) estándar actualizado en el plan de mantenimiento. Sin esto, la mejora se revierte.

### 2.3 Benchmark externo

El sistema compara el desempeño contra referencias públicas de industria para responder *"¿cuánto vale cerrar la brecha?"*.

| Indicador | Promedio industria | Cuartil superior | Fuente del rango |
|---|---|---|---|
| % trabajo planificado (PMP) | ~80% | ≥ 85% | Benchmark de industria (80% es el umbral aceptado; 85%+ = alto desempeño) |
| % reactivo | 40–50% | ≤ 20% | Investigación McKinsey citada por la industria: cerca de la mitad de la actividad de mantenimiento sigue siendo reactiva |
| Disponibilidad | ~90% | ≥ 95% | Práctica de industria |
| OEE | ~60% | ≥ 85% | Umbral "world-class" ampliamente aceptado |
| Costo mantenimiento / RAV | 2–5% | ≤ 2,5% | Marco SMRP (costo anual / valor de reemplazo del activo) |
| Prima de reparación reactiva | — | — | El correctivo de emergencia cuesta del orden de 3–5× el mismo trabajo planificado |
| Retorno de mantenimiento predictivo | — | — | Reducciones reportadas de 30–50% en detención no planificada y 18–25% en costo |

**Advertencia obligatoria en el código y en la UI:** estos rangos provienen de literatura secundaria de industria que cita estudios de McKinsey & Company y del marco SMRP. Deben mostrarse como *referencia orientativa*, nunca como dato auditado, y con nota al pie visible. Los valores "actual" del mockup son sintéticos.

---

## 3. Arquitectura

```
┌────────────────────────────────────────────────────────────────┐
│ CAPA 1 · ORIGEN — SAP ECC/S4                                   │
│ PM (órdenes, avisos, confirmaciones, equipos, planes)          │
│ MM (movimientos y stock de materiales)                         │
│ CO (costos reales, plan, comprometido)                         │
│ PP (producción: toneladas y horas de operación)                │
└───────────────────────────┬────────────────────────────────────┘
                            │ extracción por transacción (§4)
┌───────────────────────────▼────────────────────────────────────┐
│ CAPA 2 · TRANSFORMACIÓN — Power Query (M)                      │
│ tipificación · derivadas · DimFecha · banderas de calidad      │
└───────────────────────────┬────────────────────────────────────┘
┌───────────────────────────▼────────────────────────────────────┐
│ CAPA 3 · MODELO — esquema en estrella                          │
│ 7 tablas de hechos · 8 dimensiones · relaciones 1:N unidirecc. │
└───────────────────────────┬────────────────────────────────────┘
┌───────────────────────────▼────────────────────────────────────┐
│ CAPA 4 · SEMÁNTICA — 40 medidas DAX                            │
│ agrupadas por pilar fundacional                                │
└───────────────────────────┬────────────────────────────────────┘
┌───────────────────────────▼────────────────────────────────────┐
│ CAPA 5 · PRESENTACIÓN — 12 páginas                             │
│ gerencial → técnico → detalle → mejora enfocada → benchmark    │
└────────────────────────────────────────────────────────────────┘
```

**Principio de diseño:** una sola tabla de calendario (`DimFecha`) conecta los 7 hechos por su fecha relevante, de modo que toda medida temporal funcione igual en todas las páginas sin recalcular fechas por tabla.

---

## 4. Mapa de fuentes SAP

### 4.1 Por módulo

| Módulo | Qué entrega | Transacciones clave | Tablas destino |
|---|---|---|---|
| **PM** | Órdenes, avisos, confirmaciones HH, equipos, ubicaciones, planes | `IW39`/`IW38`, `IW28`/`IW29`/`IW59`, `IW47`/`IW45`, `IH08`/`IE03`, `IH06`/`IL05`, `IP15`/`IP24` | `FactOrdenesMtto`, `FactAvisosMtto`, `FactConfirmacionesHH`, `FactPlanesMtto`, `DimEquipo`, `DimUbicacionTecnica` |
| **MM** | Movimientos y stock de repuestos, compras, lead time | `MB51`, `MB52`/`MMBE`, `MM03`, `ME2N`/`ME2L` | `FactMaterialesMtto`, `DimMaterial` |
| **CO** | Costos reales, plan y comprometido por orden y centro de costo | `KOB1`, `CJI3`/`CJI5`, `KSB1`, `S_ALR_87013558` | `FactCostosMtto`, `DimCentroCosto`, `DimClaseCosto` |
| **PP** | Volumen producido y horas de operación | `COOIS`, `MCRE`/LIS | `FactProduccion`, `DimLinea` |

### 4.2 Matriz transacción → destino (contrato de extracción)

| Transacción | Descripción | Tabla destino | Frecuencia |
|---|---|---|---|
| `IW39` / `IW38` | Lista de órdenes de mantenimiento | `FactOrdenesMtto` | Diaria |
| `IW28` / `IW29` / `IW59` | Lista de avisos | `FactAvisosMtto` | Diaria |
| `IW47` / `IW45` / `IW49N` | Confirmaciones de operaciones (HH) | `FactConfirmacionesHH` | Diaria |
| `KOB1` / `CJI3` / `KSB1` | Costos reales por orden | `FactCostosMtto` | Diaria |
| `S_ALR_87013558` | Plan vs. real vs. comprometido | `FactCostosMtto` | Mensual |
| `MB51` | Movimientos de material | `FactMaterialesMtto` | Diaria |
| `MB52` / `MMBE` | Stock por almacén | `DimMaterial` | Diaria |
| `ME2N` / `ME2L` | Pedidos abiertos y lead time | `DimMaterial` | Semanal |
| `IP15` / `IP18` / `IP24` / `IP30` | Planes y programación preventiva | `FactPlanesMtto` | Diaria |
| `COOIS` / LIS | Producción y horas de operación | `FactProduccion` | Diaria |
| `IH08` / `IE05` / `IE03` | Maestro de equipos | `DimEquipo` | Semanal |
| `IH06` / `IL05` / `IH01` | Ubicaciones técnicas y jerarquía | `DimUbicacionTecnica` | Semanal |
| `MM03` | Maestro de materiales | `DimMaterial` | Semanal |
| `IK13` / `IK11` | Lecturas de contador (horas de operación) | `FactProduccion` | Diaria (**brecha**) |
| `CR03` | Capacidad de puesto de trabajo | `DimTecnico` | Mensual |

> **Requisito de UI:** cada visual del dashboard muestra un *chip* con su transacción de origen. Esto es parte del diseño, no un extra. Ver §9.4.

---

## 5. Modelo de datos

### 5.1 Tablas de hechos

| Tabla | Grano (una fila por…) | Clave | Fuente |
|---|---|---|---|
| `FactOrdenesMtto` | orden de mantenimiento | `Orden` | `IW39` |
| `FactAvisosMtto` | aviso de mantenimiento | `Aviso` | `IW29` |
| `FactConfirmacionesHH` | confirmación de operación | `Orden`+`Operacion`+`Contador` | `IW47` |
| `FactCostosMtto` | documento de costo imputado | `Documento` | `KOB1` |
| `FactMaterialesMtto` | movimiento de material | `DocumentoMaterial` | `MB51` |
| `FactPlanesMtto` | posición de plan / ciclo programado | `Plan`+`Posicion` | `IP24` |
| `FactProduccion` | línea–día–turno | `Fecha`+`Linea`+`Turno` | `COOIS` |

### 5.2 Dimensiones

| Tabla | Clave | Atributos principales | Fuente |
|---|---|---|---|
| `DimFecha` | `Fecha` | Año, Mes, NombreMes, Trimestre, Semana, AñoMes, OrdenAñoMes, EsLaboral | Generada en M |
| `DimEquipo` | `Equipo` | Denominación, UbicaciónTécnica, Área, Línea, Tipo, Fabricante, Año, **Criticidad (A/B/C)**, EsEquipoCrítico | `IH08` |
| `DimUbicacionTecnica` | `UbicacionTecnica` | Descripción, Planta, Área, Línea, NivelJerárquico, UbicaciónPadre | `IH06` |
| `DimTipoOrden` | `ClaseOrden` | TipoMantenimiento, Descripción, banderas EsCorrectivo/EsPreventivo | Catálogo |
| `DimMaterial` | `Material` | Descripción, Tipo, Grupo, Stock actual/mín/máx, LeadTime, ABC, EsRepuestoCrítico | `MM03`+`MB52` |
| `DimCentroCosto` | `CentroCosto` | Nombre, Área, Planta, Gerencia | `KSB1` |
| `DimClaseCosto` | `ClaseCosto` | Descripción, TipoGasto (Repuesto/Servicio/ManoObra) | Catálogo CO |
| `DimTecnico` | `Tecnico` | Especialidad, Turno, **CapacidadSemanalHH** | Maestro PM + `CR03` |
| `DimArea` / `DimGrupoPlanificador` / `DimLinea` | respectiva | descripción y jerarquía | Maestros PM |

### 5.3 Columnas clave de `FactOrdenesMtto`

| Columna | Tipo | Rol | Notas |
|---|---|---|---|
| `Orden` | Texto | PK | **Texto**, no número: preserva ceros a la izquierda |
| `ClaseOrden` | Texto | FK → `DimTipoOrden` | PM01…PM06 |
| `TipoMantenimiento` | Texto | Derivada | Correctivo/Preventivo/Predictivo/Mejora/Emergencia |
| `Aviso` | Texto | FK | puede ser nulo |
| `Equipo` | Texto | FK → `DimEquipo` | nulo ⇒ bandera de calidad |
| `UbicacionTecnica` | Texto | FK | |
| `Trabajo` | Decimal | Medida | HH planificadas |
| `TrabajoReal` | Decimal | Medida | HH reales (proxy de duración de reparación) |
| `FechaEntrada` | Fecha | FK → `DimFecha` | fecha activa de la relación |
| `FechaFinExtrema` | Fecha | — | base del cálculo de retraso |
| `StatusSistema` | Texto | — | LIB, ABIE, CTEC, CERR… |
| `EstadoCierre` | Texto | Derivada | Abierta / Cerrada |
| `CostoPlan`, `CostoReal` | Decimal | Medida | |
| `DiasCierre`, `RetrasoDias`, `AnioMes` | Entero/Texto | Derivadas | |

### 5.4 Relaciones

Todas **1:N**, de la dimensión (lado 1) al hecho (lado N), **filtro cruzado unidireccional**.

| Dimensión | Clave | Hecho | Clave | Habilita |
|---|---|---|---|---|
| `DimFecha` | `Fecha` | los 7 hechos | su fecha relevante | Inteligencia de tiempo (YTD, MoM) |
| `DimEquipo` | `Equipo` | Órdenes, Avisos, Planes | `Equipo` | Análisis por activo |
| `DimUbicacionTecnica` | `UbicacionTecnica` | Órdenes | `UbicacionTecnica` | Jerarquía técnica |
| `DimTipoOrden` | `ClaseOrden` | Órdenes | `ClaseOrden` | Mix preventivo/correctivo |
| `DimTecnico` | `Tecnico` | Confirmaciones | `Tecnico` | Productividad / capacidad |
| `DimCentroCosto` | `CentroCosto` | Costos | `CentroCosto` | Costo por centro |
| `DimClaseCosto` | `ClaseCosto` | Costos | `ClaseCosto` | Tipificación de gasto |
| `DimMaterial` | `Material` | Materiales | `Material` | Repuestos / ABC |
| `DimLinea` | `Linea` | Producción | `Linea` | Volumen por línea |

**Relaciones hecho-hecho** (mismo grano *orden*): `FactOrdenesMtto` ← `FactCostosMtto`, `FactConfirmacionesHH`, `FactAvisosMtto`. Son aceptables porque comparten la clave `Orden`. Para filtrar costos por equipo, navegar vía `FactOrdenesMtto` o desnormalizar `Equipo` en `FactCostosMtto` durante la transformación.

---

## 6. Transformaciones (Power Query M)

### 6.1 `DimFecha`

```m
let
    Inicio = #date(2024,1,1),
    Fin    = #date(2030,12,31),
    Dias   = Duration.Days(Fin - Inicio) + 1,
    Lista  = List.Dates(Inicio, Dias, #duration(1,0,0,0)),
    Tabla  = Table.FromList(Lista, Splitter.SplitByNothing(), {"Fecha"}),
    Tipo   = Table.TransformColumnTypes(Tabla, {{"Fecha", type date}}),
    Cols   = Table.AddColumn(Tipo, "Anio",         each Date.Year([Fecha]), Int64.Type),
    C2     = Table.AddColumn(Cols, "Mes",          each Date.Month([Fecha]), Int64.Type),
    C3     = Table.AddColumn(C2,  "NombreMes",     each Date.MonthName([Fecha]), type text),
    C4     = Table.AddColumn(C3,  "Trimestre",     each Date.QuarterOfYear([Fecha]), Int64.Type),
    C5     = Table.AddColumn(C4,  "Semana",        each Date.WeekOfYear([Fecha]), Int64.Type),
    C6     = Table.AddColumn(C5,  "NumDiaSemana",  each Date.DayOfWeek([Fecha], Day.Monday) + 1, Int64.Type),
    C7     = Table.AddColumn(C6,  "NombreDia",     each Date.DayOfWeekName([Fecha]), type text),
    C8     = Table.AddColumn(C7,  "AnioMes",       each Date.ToText([Fecha], "yyyy-MM"), type text),
    C9     = Table.AddColumn(C8,  "OrdenAnioMes",  each [Anio]*100 + [Mes], Int64.Type),
    C10    = Table.AddColumn(C9,  "InicioMes",     each Date.StartOfMonth([Fecha]), type date),
    C11    = Table.AddColumn(C10, "FinMes",        each Date.EndOfMonth([Fecha]), type date),
    C12    = Table.AddColumn(C11, "EsLaboral",     each if [NumDiaSemana] <= 5 then "Sí" else "No", type text)
in
    C12
```

> Marcar como **tabla de fechas** en Power BI y ordenar `NombreMes` por `OrdenAnioMes`.

### 6.2 Derivadas de `FactOrdenesMtto`

```m
// Tipificación del mantenimiento desde la clase de orden
AddTipo = Table.AddColumn(Origen, "TipoMantenimiento", each
    if List.Contains({"PM01","PM05"}, [ClaseOrden]) then "Correctivo"
    else if List.Contains({"PM02","PM03"}, [ClaseOrden]) then "Preventivo"
    else if [ClaseOrden] = "PM04" then "Mejora"
    else if [ClaseOrden] = "PM06" then "Predictivo"
    else "Otro", type text),

// Estado de cierre desde el status de sistema
AddEstado = Table.AddColumn(AddTipo, "EstadoCierre", each
    if Text.Contains([StatusSistema], "CTEC") or Text.Contains([StatusSistema], "CERR")
    then "Cerrada" else "Abierta", type text),

// Días de cierre y retraso
AddDias = Table.AddColumn(AddEstado, "DiasCierre", each
    if [EstadoCierre] = "Cerrada" and [FechaEntrada] <> null
    then Duration.Days(Date.From(DateTime.LocalNow()) - [FechaEntrada])
    else null, Int64.Type),

AddRetraso = Table.AddColumn(AddDias, "RetrasoDias", each
    if [FechaFinExtrema] <> null and [EstadoCierre] = "Abierta"
    then Duration.Days(Date.From(DateTime.LocalNow()) - [FechaFinExtrema])
    else null, Int64.Type),

AddAnioMes = Table.AddColumn(AddRetraso, "AnioMes", each
    Date.ToText([FechaEntrada], "yyyy-MM"), type text)
```

> **Brecha declarada:** `DiasCierre` usa la fecha actual como proxy porque `IW39` no exporta la fecha de cierre técnico. Si la planta extrae la fecha real de cierre (status CTEC), reemplazar `DateTime.LocalNow()` por esa columna.

### 6.3 Banderas de calidad de datos

```m
Calidad = Table.AddColumn(AddAnioMes, "FlagsCalidad", each [
    SinEquipo     = if [Equipo] = null then 1 else 0,
    SinAviso      = if [Aviso]  = null then 1 else 0,
    CerradaSinHH  = if [EstadoCierre] = "Cerrada" and ([TrabajoReal] ?? 0) = 0 then 1 else 0,
    CostoSinCierre= if ([CostoReal] ?? 0) > 0 and [EstadoCierre] = "Abierta" then 1 else 0,
    PrevVencida   = if [TipoMantenimiento] = "Preventivo" and ([RetrasoDias] ?? 0) > 0 then 1 else 0
], type record),
Expandir = Table.ExpandRecordColumn(Calidad, "FlagsCalidad",
    {"SinEquipo","SinAviso","CerradaSinHH","CostoSinCierre","PrevVencida"}),
Dedup    = Table.Distinct(Expandir, {"Orden"})
```

---

## 7. Capa semántica — 40 medidas DAX

Separador de argumentos: **punto y coma (`;`)**. Tabla base: `FactOrdenesMtto`.

### 7.1 Volumen y mix (F2/F3)

```dax
ÓrdenesTotales  = COUNTROWS( 'FactOrdenesMtto' )
ÓrdenesCerradas = CALCULATE( [ÓrdenesTotales]; 'FactOrdenesMtto'[EstadoCierre] = "Cerrada" )
ÓrdenesAbiertas = CALCULATE( [ÓrdenesTotales]; 'FactOrdenesMtto'[EstadoCierre] = "Abierta" )
Correctivas     = CALCULATE( [ÓrdenesTotales]; 'FactOrdenesMtto'[TipoMantenimiento] = "Correctivo" )
Preventivas     = CALCULATE( [ÓrdenesTotales]; 'FactOrdenesMtto'[TipoMantenimiento] = "Preventivo" )

%ÓrdenesCorrectivas = DIVIDE( [Correctivas]; [ÓrdenesTotales]; 0 )
%ÓrdenesPreventivas = DIVIDE( [Preventivas]; [ÓrdenesTotales]; 0 )
RatioPrevCorr       = DIVIDE( [Preventivas]; [Correctivas]; 0 )

CumplimientoPM =
VAR CerradasPM =
    CALCULATE( [ÓrdenesTotales];
        'FactOrdenesMtto'[TipoMantenimiento] = "Preventivo";
        'FactOrdenesMtto'[EstadoCierre]      = "Cerrada" )
RETURN DIVIDE( CerradasPM; [Preventivas]; 0 )
```

### 7.2 Confiabilidad (F5)

```dax
NumFallas = CALCULATE( COUNTROWS( 'FactAvisosMtto' ); 'FactAvisosMtto'[TipoAviso] <> "M3" )

-- MTTR: proxy con HH reales. BRECHA: sin downtime real, no es tiempo de reparación exacto.
MTTR_h =
AVERAGEX(
    FILTER( 'FactOrdenesMtto'; 'FactOrdenesMtto'[TipoMantenimiento] = "Correctivo" );
    'FactOrdenesMtto'[TrabajoReal] )

-- MTBF: requiere horas de operación. BRECHA si FactProduccion no está poblada.
HorasOperacion = SUM( 'FactProduccion'[HorasOperacion] )
MTBF_h         = DIVIDE( [HorasOperacion]; [NumFallas]; BLANK() )

DisponibilidadOper = DIVIDE( [MTBF_h]; [MTBF_h] + [MTTR_h]; BLANK() )
```

### 7.3 Backlog, cierre y SLA (F2/F3)

```dax
Backlog_HH =
SUMX(
    FILTER( 'FactOrdenesMtto'; 'FactOrdenesMtto'[EstadoCierre] = "Abierta" );
    COALESCE( 'FactOrdenesMtto'[Trabajo] - 'FactOrdenesMtto'[TrabajoReal];
              'FactOrdenesMtto'[Trabajo] ) )

CapacidadSemanalHH = SUM( 'DimTecnico'[CapacidadSemanalHH] )
Backlog_Semanas    = DIVIDE( [Backlog_HH]; [CapacidadSemanalHH]; 0 )

TiempoPromedioCierre_d =
AVERAGEX( FILTER( 'FactOrdenesMtto'; NOT ISBLANK( 'FactOrdenesMtto'[DiasCierre] ) );
          'FactOrdenesMtto'[DiasCierre] )

SLA_7d_Cumpl =
VAR CerradasEnSLA =
    CALCULATE( [ÓrdenesTotales];
        'FactOrdenesMtto'[EstadoCierre] = "Cerrada";
        'FactOrdenesMtto'[DiasCierre]  <= 7 )
RETURN DIVIDE( CerradasEnSLA; [ÓrdenesCerradas]; 0 )

ÓrdenesRetrasadas  = CALCULATE( [ÓrdenesTotales]; 'FactOrdenesMtto'[RetrasoDias] > 0 )
%ÓrdenesRetrasadas = DIVIDE( [ÓrdenesRetrasadas]; [ÓrdenesTotales]; 0 )
```

### 7.4 Costos (F4)

```dax
CostoTotal      = SUM( 'FactOrdenesMtto'[CostoReal] )
CostoPlan       = SUM( 'FactOrdenesMtto'[CostoPlan] )
CostoCorrectivo = CALCULATE( [CostoTotal]; 'FactOrdenesMtto'[TipoMantenimiento] = "Correctivo" )
CostoPreventivo = CALCULATE( [CostoTotal]; 'FactOrdenesMtto'[TipoMantenimiento] = "Preventivo" )

%CostoPreventivo    = DIVIDE( [CostoPreventivo]; [CostoPreventivo] + [CostoCorrectivo]; 0 )
CostoPromedioOrden  = DIVIDE( [CostoTotal]; [ÓrdenesTotales]; 0 )
VarianzaCosto       = [CostoTotal] - [CostoPlan]
%VarianzaCosto      = DIVIDE( [VarianzaCosto]; [CostoPlan]; 0 )

ToneladasProducidas = SUM( 'FactProduccion'[ToneladasProducidas] )
CostoPorTonelada    = DIVIDE( [CostoTotal]; [ToneladasProducidas]; 0 )
HHPorTonelada       = DIVIDE( [HHReales];   [ToneladasProducidas]; 0 )
```

### 7.5 Horas hombre (F3)

```dax
HHPlanificadas  = SUM( 'FactOrdenesMtto'[Trabajo] )
HHReales        = SUM( 'FactOrdenesMtto'[TrabajoReal] )
DesviacionHH    = [HHReales] - [HHPlanificadas]
%CumplimientoHH = DIVIDE( [HHReales]; [HHPlanificadas]; 0 )
```

### 7.6 Calidad de datos (T)

```dax
OrdenesSinEquipo   = CALCULATE( [ÓrdenesTotales]; 'FactOrdenesMtto'[SinEquipo]      = 1 )
AvisosSinOrden     = CALCULATE( COUNTROWS('FactAvisosMtto'); ISBLANK('FactAvisosMtto'[Orden]) )
CerradasSinHH      = CALCULATE( [ÓrdenesTotales]; 'FactOrdenesMtto'[CerradaSinHH]   = 1 )
CostoSinCierre     = CALCULATE( [ÓrdenesTotales]; 'FactOrdenesMtto'[CostoSinCierre] = 1 )

IndiceCalidadDatos =
VAR Banderas =
    SUM('FactOrdenesMtto'[SinEquipo]) + SUM('FactOrdenesMtto'[SinAviso]) +
    SUM('FactOrdenesMtto'[CerradaSinHH]) + SUM('FactOrdenesMtto'[CostoSinCierre])
VAR Controles = [ÓrdenesTotales] * 4
RETURN 1 - DIVIDE( Banderas; Controles; 0 )
```

### 7.7 Mejora Enfocada y benchmark (nuevas)

```dax
-- Parametrizar en una tabla de parámetros, no hardcodear:
MargenContribucionHora = SELECTEDVALUE( 'Parametros'[MargenHora]; 0 )

HorasPerdidaAverias = CALCULATE( SUM('FactAvisosMtto'[DuracionParada_h]);
                                 'FactAvisosMtto'[CategoriaPerdida] = "Averia" )

PerdidaAverias_M = DIVIDE( [HorasPerdidaAverias] * [MargenContribucionHora]; 1000000; 0 )

PerdidaTotal_M =
SUMX( VALUES('DimCategoriaPerdida'[Categoria]);
      DIVIDE( [HorasPerdida] * [MargenContribucionHora]; 1000000; 0 ) )

AhorroValidadoYTD =
CALCULATE( SUM('FactKaizen'[AhorroValidado]);
           'FactKaizen'[EstadoPDCA] = "Act";
           DATESYTD( 'DimFecha'[Fecha] ) )

%PerdidasAtacadas =
DIVIDE( CALCULATE( [PerdidaTotal_M]; 'FactKaizen'[TieneA3Activo] = TRUE() );
        [PerdidaTotal_M]; 0 )

-- Brecha vs. cuartil superior (targets en tabla de parámetros)
BrechaPlanificado_pp = [%TrabajoPlanificado] - SELECTEDVALUE('Benchmark'[Q1_Planificado])

ValorBrecha_M =
SUMX( 'Benchmark';
      MAX( 0; ( 'Benchmark'[Q1_Target] - 'Benchmark'[Actual] ) * 'Benchmark'[ValorPorPunto] ) )
```

### 7.8 Top 8 ejecutivos

Los indicadores de cabecera que ve Gerencia, con su meta y semáforo:

| # | Indicador | Meta | Semáforo | Pilar |
|---|---|---|---|---|
| 1 | % Órdenes Correctivas | ≤ 30% (world-class ≤ 20%) | verde ≤30, ámbar 30–45, rojo >45 | F2 |
| 2 | Cumplimiento Preventivo | ≥ 90% | verde ≥90, ámbar 80–90, rojo <80 | F2 |
| 3 | MTTR | tendencia ↓ | vs. mes anterior | F5 |
| 4 | MTBF | tendencia ↑ | vs. mes anterior | F5 |
| 5 | Disponibilidad Operacional | ≥ 92% | verde ≥92, ámbar 88–92, rojo <88 | F5 |
| 6 | Backlog en Semanas | 2–4 sem | verde 2–4, ámbar 4–6, rojo >6 o <1 | F2 |
| 7 | Costo Total de Mantenimiento | ≤ presupuesto | verde ≤100%, ámbar 100–110%, rojo >110% | F4 |
| 8 | Índice de Calidad de Datos | ≥ 95% | verde ≥95, ámbar 85–95, rojo <85 | T |

**Nota de interpretación obligatoria** (debe aparecer como tooltip en la UI): un % correctivo bajo puede indicar *sub-registro*, no buen desempeño. Siempre se cruza con el Índice de Calidad de Datos antes de celebrar.

---

## 8. Dashboard — 12 páginas

| # | Página | Objetivo | Visuales principales | Fuente SAP |
|---|---|---|---|---|
| 1 | **Resumen Ejecutivo** | Salud global en una vista | Cards Top 8 con MoM, semáforo por pilar, tendencia de costo, mix apilado, Top 10 equipos, alertas | `IW39`·`IW29`·`KOB1`·`IP24` |
| 2 | **Gestión de Órdenes** | Flujo y disciplina de cierre | Abiertas vs. cerradas, clase de orden, tabla de retrasadas (drillthrough), matriz Área×Grupo | `IW39`/`IW38` |
| 3 | **Preventivo vs. Correctivo** | Madurez de la planificación | Donut del mix, gauge cumplimiento PM, evolución mensual, Pareto de correctivos | `IW39`·`IP24` |
| 4 | **Confiabilidad** | Malos actores y priorización | Gauge disponibilidad, MTTR/MTBF por equipo, Pareto de fallas, mapa de calor equipo×mes | `IW29`·`IW47`·`IK13` |
| 5 | **Costos** | Gasto y varianza | Real vs. plan, waterfall de varianza, apiladas por área, Pareto 80/20, árbol de descomposición | `KOB1`·`CJI3`·`S_ALR_*` |
| 6 | **Backlog y Capacidad** | Equilibrar carga | Aging (0–7/8–15/16–30/>30 d), capacidad vs. demanda, matriz prioridad×antigüedad | `IW39`·`IW47`·`CR03` |
| 7 | **Materiales y Repuestos** | Disponibilidad de críticos | Top repuestos por costo, consumo mensual, críticos bajo stock, lead time | `MB51`·`MB52`·`MM03` |
| 8 | **Calidad de Datos SAP** | Condición habilitante | Gauge del índice, componentes, tabla accionable de anomalías | `IW39`·`IW29`·`IW47` |
| 9 | **TPM y 5 Fundacionales** | Madurez cultural | Radar actual vs. meta, score por pilar, matriz de brechas y acciones | Assessment + SAP |
| 10 | **Drillthrough de Equipo** | Diagnóstico 360° de un activo | Ficha técnica, historial fallas/costo, MTTR/MTBF del equipo, recomendación | `IE03`·`IW39`·`KOB1` |
| 11 | **Mejora Enfocada** | Pérdidas → iniciativas con ahorro | Árbol de pérdidas, matriz impacto×esfuerzo, cartera A3, ciclo PDCA | `IW29`·`COOIS`·`KOB1` |
| 12 | **Benchmark Externo** | Distancia al cuartil superior | Brecha actual vs. Q1, valor de la brecha por palanca, tabla de trayectoria | Todas |

### 8.1 Navegación y controles

| Control | Función |
|---|---|
| Menú lateral | Navegar entre las 12 páginas, con numeración y estado activo |
| Toggle **Vista Gerencial / Vista Técnica** | Gerencial muestra cards, semáforos y tendencias; Técnica revela tablas de detalle, Pareto y matrices |
| Panel de filtros ocultable | Periodo, área, línea, criticidad, tipo de orden |
| Botón Reset | Vuelve al estado base de todas las segmentaciones |
| Drillthrough | Clic derecho en equipo/área/orden → Página 10 |
| Tooltips personalizados | Ficha de equipo al pasar el cursor |
| **Chip de transacción SAP** | Cada visual muestra su origen (`IW39`, `KOB1`…) |

### 8.2 Visuales complementarios (catálogo completo)

Cada página incorpora visuales adicionales que responden a la pregunta *"¿y entonces qué hago?"*. Todos trazan a una tabla SAP; ninguno se apoya en supuestos externos al modelo.

| Pág. | Visual | Tipo | Fuente SAP | Decisión que habilita |
|---|---|---|---|---|
| 2 | Embudo aviso → orden → cierre | Funnel | `IW29` → `IW39` → `IW47` | Detectar dónde se pierde trazabilidad del ciclo |
| 2 | Cumplimiento de programación semanal | Línea + meta | `IW39` · `IP24` | Decidir si congelar la programación semanal |
| 3 | Correctivos recurrentes (<30 d) | Tabla | `IW29` × `IH08` | Seleccionar candidatos a RCA formal |
| 3 | Preventivas vencidas por plan | Barras | `IP24` · `IP15` | Priorizar qué plan ejecutar primero |
| 4 | Pareto de causas de falla | Pareto | `IW28` (código de daño) | Atacar el modo de falla, no el equipo |
| 4 | Ranking de malos actores | Tabla | `IW29` × `KOB1` × `IH08` | Decidir overhaul vs. reemplazo |
| 5 | Costo por clase de coste | Barras H | `KOB1` · `KSB1` | Separar gasto controlable de estructural |
| 5 | Top órdenes por costo y desviación | Tabla | `IW39` × `KOB1` | Explicar la varianza al directorio |
| 6 | Backlog por especialidad | Barras agrupadas | `IW47` × `CR03` | Dimensionar dotación o apoyo externo |
| 6 | Órdenes envejecidas (>30 d) con motivo | Tabla | `IW39` | Separar el backlog en colas gestionables |
| 7 | Órdenes detenidas por falta de repuesto | Tabla | `IW39` (status MSPT) · `MB51` | Cuantificar el costo del quiebre de stock |
| 7 | Clasificación ABC y cobertura | Barras + línea | `MB52` × `MM03` | Diferenciar política de stock por clase |
| 8 | Evolución del índice de calidad | Línea + meta | `IW39` · `IW29` | Verificar si la disciplina se sostiene |
| 8 | Calidad por grupo planificador | Barras | `IW39` | Asignar responsabilidad local del dato |
| 8 | Impacto del dato incompleto sobre los KPI | Tabla | `IW39` · `IW29` · `IW47` | Saber qué KPI **no** se puede usar aún |
| 9 | Evolución mensual de madurez | Línea + meta | Assessment + SAP | Distinguir mejora real de esfuerzo puntual |
| 9 | Plan de cierre de brechas | Tabla | Modelo de score | Comprometer acción con evidencia verificable |
| 10 | Repuestos consumidos por el equipo | Tabla | `MB51` | Detectar reemplazo repetido del mismo componente |
| 10 | Planes preventivos asociados | Tabla | `IP24` · `IP15` | Correlacionar plan vencido con falla recurrente |
| 11 | Ahorro acumulado vs. meta | Línea | `KOB1` | Verificar ahorro con documento de costo |
| 11 | Efecto medido por A3 (antes/después) | Barras | `IW29` · `KOB1` | Confirmar o devolver el A3 a fase Do |
| 12 | Plan de cierre de brecha a 12 meses | Tabla | Benchmark + modelo | Secuenciar el compromiso ante Gerencia |

### 8.3 Banda narrativa (componente obligatorio)

Cada página cierra con un bloque `.insight` de cuatro campos. No es decoración: es lo que convierte el tablero en una herramienta de decisión.

```
┌─────────────────────────────────────────────────────────────┐
│ TÍTULO DE LA LECTURA                                        │
├──────────────────┬──────────────────┬───────────────────────┤
│ Qué dice el dato │ Correlación      │ Riesgo si no se actúa │
│ Hecho observado  │ Cruce entre dos  │ Consecuencia esperada │
│ con cifra        │ o más fuentes    │ si nada cambia        │
├──────────────────┴──────────────────┴───────────────────────┤
│ Decisión recomendada: acción concreta y asignable           │
└─────────────────────────────────────────────────────────────┘
```

**Reglas de redacción:**

1. *Qué dice el dato* cita siempre una cifra que existe en la página. Nunca un dato que el usuario no puede ver.
2. *Correlación* cruza **al menos dos fuentes SAP distintas** (por ejemplo `IP24` × `IW29`, o `MB52` × `IH08`). Es el campo que aporta valor analítico real; sin cruce, el bloque se omite.
3. *Riesgo* proyecta la consecuencia en horizonte explícito, no en abstracto.
4. *Decisión* es una acción ejecutable por un rol identificable, no una recomendación genérica.
5. Ninguna narrativa afirma causalidad donde solo hay correlación. Se usa "coincide con", "se concentra en", "depende de".

**Correlaciones implementadas** (el implementador debe preservarlas, son el hilo analítico del producto):

| Correlación | Fuentes cruzadas | Página |
|---|---|---|
| Plan PM vencido → falla recurrente del mismo equipo | `IP24` × `IW29` | 3, 10 |
| MTBF bajo + MTTR alto + criticidad A → máxima pérdida | `IW29` × `IW47` × `IH08` | 4 |
| Malos actores = mayor consumo de repuestos críticos | `IW29` × `MB51` | 4, 7 |
| Quiebre de stock → backlog envejecido por espera | `MB52` × `IW39` | 6, 7 |
| Órdenes cerradas sin HH → MTTR y backlog subestimados | `IW47` × `IW39` | 8 |
| Pilar de madurez débil → KPI estancado que depende de él | Assessment × SAP | 9 |
| % planificado y % reactivo son el mismo fenómeno | `IW39` | 12 |
| Categorías de pérdida sin A3 → techo del ahorro | Árbol × cartera | 11 |

---

## 9. Sistema de diseño

El estándar visual es el de un producto BI comercial. La belleza no es decorativa: reduce la carga cognitiva del ejecutivo.

### 9.1 Tokens de color

```css
:root{
  --navy:#0E1C33;   /* superficie de marca, títulos, serie primaria */
  --blue:#2F6FED;   /* serie de datos principal */
  --orange:#D97706; /* acento de interfaz y segunda serie */
  --green:#12805C;  /* estado positivo */
  --amber:#B54708;  /* estado de advertencia */
  --red:#B42318;    /* estado crítico */
  --ink:#101828;    /* texto principal */
  --grey:#5A6473;   /* texto secundario */
  --line:#E4E9F2;   /* bordes */
  --light:#EEF2F8;  /* fondos sutiles */
  --bg:#F4F6FA;     /* lienzo */
  --card:#FFFFFF;   /* tarjetas */
}
```

**Regla:** el color nunca es el único portador de significado. Todo semáforo lleva además texto de meta.

### 9.2 Tipografía y espaciado

- Familia: `Calibri` / `Segoe UI` / `system-ui` (sans neutra). Monoespaciada (`Consolas`) solo para código y chips SAP.
- Escala: KPI 30px/700 · título de página 18px/700 · título de tarjeta 13px/700 · cuerpo 12px · caption 11px · chip 9px.
- Grid de 4px. Gap entre tarjetas: 14px. Padding de tarjeta: 14–16px.
- Radio de tarjeta: 10px. Sombra en reposo `0 1px 3px rgba(20,40,80,.06)`, en hover `0 4px 14px rgba(16,24,40,.10)`.

### 9.3 Anatomía de una tarjeta

```
┌──────────────────────────────────────────┐
│ Título de la tarjeta   [CHIP SAP]        │  ← 13px/700 + chip monoespaciado
│ Caption explicativa en gris              │  ← 11px, dice cómo leerlo
│                                          │
│            [ visual ]                    │  ← altura fija: 180/230/300px
│                                          │
│ Nota de interpretación (cursiva)         │  ← opcional, 11px
└──────────────────────────────────────────┘
```

Toda tarjeta responde a tres preguntas: **qué muestro**, **de dónde viene** (chip), **cómo se lee** (caption).

### 9.4 Reglas duras

1. Nunca más de 4 KPI por fila ni más de 6 series por gráfico.
2. Eje Y de porcentajes siempre con sufijo `%`; de dinero, en M$ con separador decimal coma (convención es-CL).
3. Gráficos sin bordes 3D, sin degradados decorativos, sin ejes duplicados innecesarios.
4. Grilla horizontal tenue (`--line`), grilla vertical desactivada.
5. Estados de carga y vacío explícitos: *"Sin datos para este filtro"*, nunca un gráfico en blanco.
6. Contraste mínimo 4.5:1 en texto (WCAG AA).
7. Responsive: sidebar colapsa a íconos bajo 900px; las grillas g3/g4 pasan a 1–2 columnas.

---

## 10. Brechas de información declaradas

Estas no son fallas del sistema: son límites del dato de origen que el sistema **declara** en lugar de disimular.

| Dato faltante | Impacto | Fuente / método propuesto | Prioridad |
|---|---|---|---|
| Tiempo de detención (downtime) por falla | MTTR usa HH como proxy; disponibilidad inexacta | Campos de inicio/fin de avería en el aviso (`IW22`) o paradas de línea desde PP/MES | **Alta** |
| Horas de operación reales por equipo | MTBF requiere horas operativas, no calendario | Contadores SAP (`IK11`/`IK13`) u horas de línea desde producción | **Alta** |
| Toneladas / unidades producidas | Normaliza costo/ton y HH/ton | `FactProduccion` desde `COOIS`/LIS | **Alta** |
| Velocidad nominal y real de línea | Impide calcular el componente Rendimiento del OEE | MES / historiador | Media |
| Defectos y reproceso | Impide el componente Calidad del OEE | Sistema de calidad | Media |
| Tipificación de avisos de seguridad | No separa mantenimiento de eventos EHS | Catálogo de clase de aviso / código de daño en `IW28` | Media |
| Valor de reemplazo del activo (RAV) | Sin él no se calcula costo/RAV del benchmark | Activo fijo (`AS03`) o tasación de ingeniería | Media |
| Margen de contribución por hora | Sin él no se monetiza el árbol de pérdidas | Controlling / finanzas | **Alta** |

Mientras una brecha esté abierta, el KPI afectado se muestra con un indicador visual de *proxy* y su tooltip explica la limitación.

---

## 11. Roadmap de implementación (12 semanas)

| Semana | Entregable | Criterio de aceptación |
|---|---|---|
| S1 | Diagnóstico de fuentes SAP y línea base de calidad | Extractos de las 4 fuentes obtenidos; índice de calidad inicial medido |
| S2 | Modelo semántico y diccionario de datos | Las 15 tablas documentadas con grano, PK y FK |
| S3 | Power Query: limpieza, derivadas, `DimFecha` | Consultas parametrizadas y con *query folding* donde aplique |
| S4 | Dimensiones y relaciones | Modelo en estrella sin relaciones bidireccionales ni ambigüedad |
| S5 | Medidas DAX y validación | **Hito:** los Top 8 reconcilian contra un extracto SAP (tolerancia ±1%) |
| S6 | Dashboard páginas 1–10 | Navegación, bookmarks y drillthrough operativos |
| S7 | Páginas 11–12 (Mejora Enfocada y Benchmark) | Árbol de pérdidas monetizado; brecha valorizada |
| S8 | Validación con Mantenimiento, Operaciones y Finanzas | Acta de definiciones firmada por las tres áreas |
| S9 | Publicación piloto y capacitación | Workspace publicado, 2 sesiones de capacitación |
| S10 | Automatización de refresco | Gateway configurado, refresco diario sin intervención |
| S11 | Gobierno de datos | Roles RLS, diccionario publicado, responsable por KPI asignado |
| S12 | Cierre y mejora continua | Primer ciclo PDCA cerrado con ahorro verificado |

---

## 12. Estructura del repositorio

```
maintenance-performance-suite/
├── README.md                     # portada: qué es, captura, cómo correrlo
├── PROJECT_SPEC.md               # este documento
├── LICENSE                       # MIT
├── docs/
│   ├── methodology.md            # 5 Fundacionales + Mejora Enfocada
│   ├── sap-transactions.md       # matriz completa de transacciones
│   ├── data-dictionary.md        # diccionario de las 15 tablas
│   ├── benchmark.md              # referencias externas y su alcance
│   ├── design-system.md          # tokens, componentes, reglas
│   └── images/                   # capturas de las 12 páginas
├── src/
│   ├── powerquery/
│   │   ├── DimFecha.pq
│   │   ├── FactOrdenesMtto.pq
│   │   ├── FactAvisosMtto.pq
│   │   ├── FactCostosMtto.pq
│   │   └── ...
│   ├── dax/
│   │   ├── 01-volumen-y-mix.dax
│   │   ├── 02-confiabilidad.dax
│   │   ├── 03-backlog-sla.dax
│   │   ├── 04-costos.dax
│   │   ├── 05-calidad-datos.dax
│   │   └── 06-mejora-enfocada.dax
│   └── mockup/
│       ├── index.html            # mockup navegable (autocontenido)
│       └── assets/
├── data/
│   ├── generate_synthetic.py     # generador de dataset sintético
│   ├── schema.json               # contrato de columnas por tabla
│   └── sample/                   # CSV de ejemplo (sintéticos)
├── deliverables/
│   ├── toolkit.docx
│   ├── modelo-semantico.xlsx
│   └── presentacion-ejecutiva.pptx
└── tests/
    ├── test_schema.py            # valida que los CSV cumplan schema.json
    └── test_measures.md          # casos de prueba de cada medida DAX
```

---

## 13. Instrucciones para el agente de IA desarrollador

### 13.1 Orden de construcción sugerido

1. **`data/generate_synthetic.py`** — genera 18–24 meses de datos sintéticos coherentes: ~1.300 órdenes, ~900 avisos, confirmaciones, costos, materiales, planes y producción. Los datos deben reproducir patrones realistas (estacionalidad, malos actores concentrados, Pareto 80/20, un 6% de registros con defectos de calidad deliberados para que el Índice de Calidad tenga algo que detectar).
2. **`schema.json` + `tests/test_schema.py`** — contrato y validación.
3. **`src/powerquery/*.pq`** — transformaciones según §6.
4. **`src/dax/*.dax`** — las 40 medidas según §7, con comentario de pilar y de brecha donde aplique.
5. **`src/mockup/index.html`** — refinar o regenerar el mockup según §8 y §9.
6. **`docs/*`** — expandir desde las secciones de este documento.
7. **`README.md`** — portada con captura, stack, y cómo levantar el mockup.

### 13.2 Restricciones técnicas del mockup

- Un solo archivo `.html` autocontenido. Única dependencia externa: Chart.js 4.4.x por CDN.
- Sin frameworks, sin build step, sin `localStorage`.
- Todos los datos embebidos como constantes JS, claramente marcados como sintéticos.
- Debe funcionar abriendo el archivo con doble clic, sin servidor.
- Accesible por teclado (navegación entre páginas con Tab/Enter).

### 13.3 Criterios de aceptación del proyecto

- [ ] Ninguna referencia a empresas, marcas, plantas o personas reales en ningún archivo.
- [ ] Las 12 páginas del mockup renderizan sin errores de consola.
- [ ] Cada visual muestra su chip de transacción SAP.
- [ ] Las 40 medidas DAX están escritas con separador `;` y comentadas por pilar.
- [ ] Toda brecha de información está declarada en el código y visible en la UI.
- [ ] El benchmark externo lleva nota de alcance visible.
- [ ] `test_schema.py` pasa contra el dataset sintético.
- [ ] `README.md` incluye al menos 3 capturas.

### 13.4 Preguntas abiertas que el autor debe responder

Estas decisiones no están cerradas y cambian la implementación:

1. **Stack del mockup:** ¿se mantiene HTML+Chart.js autocontenido, o se migra a React + Vite + Recharts (más "portafolio de desarrollador", pero pierde el doble-clic)?
2. **Idioma del repositorio:** ¿todo en español, todo en inglés, o código y nombres técnicos en inglés con documentación en español? Para visibilidad internacional en GitHub, lo habitual es README en inglés.
3. **Alcance del `.pbit`:** ¿se incluye una plantilla Power BI real, o el repositorio se queda en spec + mockup + scripts?
4. **Volumen del dataset sintético:** ¿18 meses (ligero, ~5 MB) o 36 meses (más realista para tendencias, ~15 MB)?
5. **Benchmark:** ¿se dejan los rangos de industria como valores fijos en una tabla de parámetros, o se hace configurable por el usuario en la UI?
6. **Módulo de pérdidas:** ¿`FactKaizen` y `DimCategoriaPerdida` se modelan como tablas SAP-derivadas, o como un registro manual en Excel/SharePoint que se integra al modelo? (En la práctica suele ser manual al inicio.)
7. **CI:** ¿se agrega GitHub Actions para correr los tests y publicar el mockup en GitHub Pages?
8. **Licencia:** ¿MIT (permisiva, recomendada para portafolio) u otra?

---

## 15. Dataset sintético implementado

El generador `data/generate_synthetic.py` produce 24 meses (enero 2025 – diciembre 2026) con semilla fija, de modo que el resultado es reproducible.

| Tabla | Filas | Grano |
|---|---|---|
| `FactOrdenesMtto` | 3.044 | una orden de mantenimiento |
| `FactAvisosMtto` | 2.623 | un aviso con duración de parada y categoría de pérdida |
| `FactPlanesMtto` | 1.104 | una posición de plan por mes, cumplida o vencida |
| `FactMaterialesMtto` | 274 | un consumo de material por mes |
| `FactProduccion` | 168 | línea–mes con toneladas y horas de operación |
| `FactKaizen` | 12 | un A3 con KPI antes/después y fase PDCA |
| `DimEquipo` | 16 | equipos en 4 áreas, con criticidad A/B/C |
| `DimMaterial` | 12 | materiales con ABC, stock, mínimo y lead time |

### 15.1 Patrones deliberados

El dataset no es ruido aleatorio: reproduce el comportamiento que hace el análisis significativo.

| Patrón | Implementación | Qué demuestra en el tablero |
|---|---|---|
| Mejora sostenida | Curva desacelerada sobre 24 meses | Correctivo 54% → 24%; calidad de datos 82% → 96% |
| Estacionalidad | Factor por mes, pico en verano austral | Picos de falla en enero–febrero |
| Pareto de activos | Peso de falla por equipo | 3 equipos concentran gran parte de fallas y costo |
| Criticidad | Multiplicador A/B/C sobre duración y costo | Los activos A dominan la pérdida |
| Defectos de calidad | ~6% de registros con banderas | El índice de calidad tiene qué detectar |
| Backlog real | Órdenes abiertas con avance parcial | HH pendientes ≠ 0, aging con sentido |
| Varianza de costo | Correctivo se desvía 15–120%; preventivo ±12% | El planificado es predecible, el reactivo no |
| Quiebre de stock | Motivo de detención ligado a materiales bajo mínimo | Correlación abastecimiento → backlog |

### 15.2 Definiciones de cálculo aplicadas

Decisiones que el implementador debe conservar, porque determinan si el KPI es correcto:

| Métrica | Fuente correcta | Error a evitar |
|---|---|---|
| **MTTR** | Duración de parada del aviso (`IW29`) | Usar HH de la orden: son horas-hombre, no horas de reloj |
| **MTBF** | Horas-equipo operativas ÷ n.º de averías | Usar horas de línea sin multiplicar por equipos |
| **Backlog HH** | Σ (HH plan − HH real) de órdenes **abiertas** | Incluir cerradas: da cero o negativo |
| **Disponibilidad** | 1 − horas detención ÷ horas operación (`COOIS`) | Derivarla solo de MTBF/MTTR proxy |
| **Costo/tonelada** | Costo real ÷ toneladas (`KOB1` ÷ `COOIS`) | Omitir el denominador productivo |
| **Índice de calidad** | 1 − banderas ÷ (órdenes × n.º de controles) | Contar banderas sobre el total de órdenes |
| **Madurez por pilar** | Escalado 1–5 desde el propio dato SAP | Usar encuesta sin anclaje en dato |

### 15.3 Comportamiento de los filtros

Los cinco filtros globales más el selector de equipo recalculan **todos** los visuales, KPI y narrativas; nada está precalculado.

- El período define la ventana; los deltas comparan contra la **ventana anterior de igual longitud**.
- Área, línea y criticidad filtran órdenes, avisos, producción, consumos y planes de forma consistente.
- El tipo de orden filtra solo el conjunto de órdenes, porque un aviso no tiene tipo de mantenimiento.
- La capacidad de referencia se escala cuando el filtro restringe el alcance organizativo.
- Si una combinación no devuelve órdenes, la interfaz lo declara explícitamente en lugar de renderizar gráficos vacíos.


## 14. Notas de alcance y honestidad

- Todos los datos numéricos de los entregables son **sintéticos e ilustrativos**. No provienen de ninguna operación real.
- Los rangos de benchmark provienen de literatura pública de industria que cita estudios de McKinsey & Company y del marco de métricas SMRP. Se presentan como referencia orientativa, no como dato auditado, y pueden variar significativamente por sector, criticidad de activos y madurez de la operación.
- El sistema calcula el componente **Disponibilidad** del OEE. Los componentes Rendimiento y Calidad requieren datos que SAP PM no entrega (ver §10); mientras esa brecha esté abierta, el OEE mostrado es parcial y así se declara.
- Este es un **desarrollo personal** de arquitectura analítica y metodología de mantenimiento. No es un producto comercial ni está asociado a ningún empleador.

---

*Licencia sugerida: MIT. Documento versionado junto al código; cualquier cambio de definición de KPI o de modelo debe reflejarse aquí en el mismo commit.*
