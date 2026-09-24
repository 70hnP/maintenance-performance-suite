# Proyecto Power BI (PBIP)

Este repositorio incluye el modelo y el informe en **formato PBIP**: carpetas de archivos de texto en lugar de un `.pbix` binario. Eso permite revisar un cambio de medida en un *pull request*, hacer *diff* de una relación y resolver conflictos como en cualquier otro código.

```
pbip/
├── MaintenancePerformanceSuite.pbip          ← abre este archivo en Power BI Desktop
├── MaintenancePerformanceSuite.SemanticModel/
│   ├── definition.pbism
│   ├── diagramLayout.json                    ← disposición del esquema en estrella
│   └── definition/
│       ├── database.tmdl
│       ├── model.tmdl
│       ├── expressions.tmdl                  ← parámetros RutaDatos, MargenHora, CapacidadSemanal
│       ├── relationships.tmdl                ← 20 relaciones 1:N
│       └── tables/                           ← 15 archivos TMDL, uno por tabla
└── MaintenancePerformanceSuite.Report/
    ├── definition.pbir
    ├── StaticResources/                      ← tema corporativo
    └── definition/
        ├── report.json
        └── pages/                            ← 12 páginas, un archivo JSON por visual
```

---

## Cómo abrirlo

1. **Power BI Desktop** — versión de junio 2024 o posterior.
2. Habilita el formato: *Archivo › Opciones › Características de vista previa › **Power BI Project (.pbip) save option***. Reinicia Desktop.
3. Abre `pbip/MaintenancePerformanceSuite.pbip`.
4. Ajusta el parámetro de datos: *Inicio › Transformar datos › Administrar parámetros › **RutaDatos***. Escribe la ruta absoluta de la carpeta `data/sample` de este repositorio, por ejemplo `C:\repos\maintenance-performance-suite\data\sample`.
5. *Cerrar y aplicar*. El modelo carga los ocho CSV sintéticos.

> El parámetro existe precisamente para que el proyecto no lleve rutas absolutas dentro del código. Es el único ajuste necesario tras clonar.

---

## Parámetros del modelo

| Parámetro | Tipo | Defecto | Para qué sirve |
|---|---|---|---|
| `RutaDatos` | Texto | — | Carpeta con los CSV. Único valor obligatorio al clonar. |
| `MargenHora` | Número | 34 | Margen de contribución por hora de detención, en k$/h. Monetiza el árbol de pérdidas de la Mejora Enfocada. Debe venir de Controlling. |
| `CapacidadSemanal` | Número | 540 | Capacidad global de mantenimiento en HH por semana. Se usa cuando no hay filtro de gremio; con filtro, manda la capacidad de `DimGrupoPlanificador`. |

---

## Modelo semántico

**15 tablas**: 6 de hechos, 8 de dimensiones y `_Medidas` como contenedor de la capa semántica.

| Hechos | Grano | Fuente SAP |
|---|---|---|
| `FactOrdenesMtto` | una orden | `IW39` / `IW38` |
| `FactAvisosMtto` | un aviso | `IW28` / `IW29` |
| `FactPlanesMtto` | posición de plan por mes | `IP15` / `IP24` |
| `FactMaterialesMtto` | material por mes y área | `MB51` |
| `FactProduccion` | línea por mes | `COOIS` / LIS |
| `FactKaizen` | un A3 | registro propio del pilar, validado en CO |

| Dimensiones | Fuente |
|---|---|
| `DimFecha` | generada en M, marcada como tabla de fechas |
| `DimEquipo` | `IH08` / `IE03` |
| `DimMaterial` | `MM03` / `MB52` |
| `DimTipoOrden`, `DimArea`, `DimLinea`, `DimCriticidad`, `DimGrupoPlanificador` | catálogos en M |

**Nota de honestidad sobre el modelo.** La especificación describe siete tablas de hechos, con `FactCostosMtto` (`KOB1`) y `FactConfirmacionesHH` (`IW47`) separadas. En esta implementación sintética ambas vienen **denormalizadas dentro de `FactOrdenesMtto`**, porque el generador produce costo y horas hombre al grano de la orden. En una implementación real contra SAP conviene separarlas: el costo tiene grano de documento contable y las confirmaciones grano de operación, y agregarlos a la orden pierde información de clase de coste y de técnico.

**20 relaciones**, todas 1:N de dimensión a hecho con filtro cruzado en dirección única. No hay relaciones bidireccionales ni ambigüedad de rutas.

---

## Capa semántica

**79 medidas** en ocho carpetas de visualización, para que el modelo sea navegable por alguien que llega nuevo:

| Carpeta | Contenido |
|---|---|
| `01 · Volumen y mix` | Conteos, mix preventivo/correctivo, % planificado, cumplimiento PM |
| `02 · Confiabilidad` | MTTR, MTBF, disponibilidad, horas de detención, OEE parcial |
| `03 · Backlog y ejecución` | Backlog HH y semanas, SLA, retrasos, HH bloqueadas |
| `04 · Costos` | Costo real y plan, varianza, costo por tonelada, repuestos, lead time |
| `05 · Calidad de datos` | Las cinco anomalías y el índice compuesto |
| `06 · Mejora Enfocada` | Pérdida monetizada, ahorro validado, cobertura de la cartera A3 |
| `07 · Madurez y benchmark` | Scores por pilar, brechas contra cuartil superior, valor de la brecha |
| `08 · Semáforos` | Medidas de color para formato condicional |

Cada medida lleva **descripción** en el modelo. Varias documentan una decisión de cálculo que es fácil equivocar:

| Medida | Advertencia que incluye |
|---|---|
| `MTTR (h)` | Se calcula desde la duración de parada del aviso, no desde las HH de la orden: las HH son horas hombre, no horas de reloj. |
| `Horas Equipo` | Convierte horas de línea a horas por equipo; sin esa conversión el MTBF queda subestimado. |
| `Backlog HH` | Solo órdenes abiertas; incluir las cerradas devuelve cero o negativo. |
| `Índice de Calidad de Datos` | Condición habilitante: bajo 95% ningún otro KPI debe usarse para comprometer inversión. |
| `OEE Parcial` | Brecha declarada: solo Disponibilidad viene de dato real; Rendimiento y Calidad usan supuestos fijos. |
| `Valor de la Brecha M$` | Referencia orientativa, no dato auditado. |

> **Separador DAX.** En los archivos TMDL las expresiones usan **coma** como separador de argumentos, que es la forma canónica de almacenamiento. Power BI la muestra con punto y coma si tu configuración regional así lo define; es una diferencia de presentación, no de contenido.

---

## Informe

**12 páginas** de 1280 × 720, una por cada página del mockup HTML, con el mismo hilo narrativo: de lo gerencial a lo técnico, luego mejora y benchmark.

Cada página tiene la misma anatomía:

1. Encabezado con número y objetivo de la página.
2. Cinco segmentaciones sincronizadas: año, área, línea, criticidad y tipo de mantenimiento.
3. Cuatro tarjetas de KPI con su meta declarada.
4. Dos o tres visuales analíticos, con la transacción SAP de origen en el propio título.
5. **Banda narrativa** de cuatro campos: qué dice el dato, correlación, riesgo si no se actúa y decisión recomendada.

El tema corporativo vive en `StaticResources/RegisteredResources/MPSCorporate.json` y define paleta, tipografía, bordes y sombras. Editarlo cambia las 12 páginas a la vez.

---

## Qué está validado y qué no

**Validado automáticamente en este repositorio:**

- Los 194 archivos JSON son sintácticamente válidos.
- Las 20 relaciones apuntan a columnas que existen.
- Las 79 medidas no referencian medidas ni columnas inexistentes.
- Los 174 visuales referencian solo campos presentes en el modelo.
- Ningún visual se sale del lienzo ni se solapa con otro.

**No validado:** la apertura en Power BI Desktop. El proyecto se generó de forma programática contra el formato documentado de PBIP, pero no se abrió en Desktop para confirmarlo. Si algo falla al abrir, lo más probable es el informe, no el modelo: el modelo TMDL es la parte robusta y se puede abrir por sí solo.

**Si el informe no carga**, en `definition/report.json` elimina el bloque `customTheme` de `themeCollection` y su entrada en `resourcePackages`, y vuelve a abrir. El informe queda con el tema base y el resto del proyecto no cambia.

---

## Flujo de trabajo en git

- Un cambio de medida es un *diff* de pocas líneas en `tables/_Medidas.tmdl`.
- Un cambio de visual toca un único `visual.json`, sin afectar al resto de la página.
- `.gitignore` excluye `*.pbix`, la carpeta `.pbi/` y los archivos de caché que Desktop genera al abrir.

Para revisar un *pull request* basta leer el TMDL: es texto plano con la misma estructura que tendría el modelo en Tabular Editor.
