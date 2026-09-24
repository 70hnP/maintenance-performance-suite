#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_pbip.py — Genera el proyecto Power BI en formato PBIP
===========================================================
Emite la estructura completa, legible y versionable en git:

  MaintenancePerformanceSuite.pbip
  MaintenancePerformanceSuite.SemanticModel/   → modelo en TMDL
  MaintenancePerformanceSuite.Report/          → informe en PBIR

El modelo lee los CSV sintéticos de data/sample mediante el parámetro
RutaDatos, de modo que el proyecto refresca sin conexión a SAP.
"""

import json, os, shutil, uuid

OUT   = "pbip"
NAME  = "MaintenancePerformanceSuite"
SM    = f"{OUT}/{NAME}.SemanticModel"
RP    = f"{OUT}/{NAME}.Report"
NS    = uuid.UUID("7f1c9a2e-3b5d-4e6f-8a90-112233445566")

def lt(s):           return str(uuid.uuid5(NS, s))
def w(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f: f.write(text)
def wj(path, obj):   w(path, json.dumps(obj, ensure_ascii=False, indent=2))

if os.path.isdir(OUT): shutil.rmtree(OUT)

# ════════════════════════════════════════════════════════ PALETA / TEMA ═══
PAL = dict(navy="#0E1C33", blue="#2F6FED", orange="#D97706", green="#12805C",
           amber="#B54708", red="#B42318", ink="#101828", grey="#5A6473",
           line="#E4E9F2", light="#EEF2F8", bg="#F4F6FA", card="#FFFFFF",
           violet="#6941C6", slate="#667085")

TEMA = {
  "name": "MPS Corporate",
  "dataColors": [PAL["blue"], PAL["navy"], PAL["orange"], PAL["green"], PAL["violet"],
                 PAL["amber"], PAL["red"], PAL["slate"], "#7BA4F5", "#4C6A9B"],
  "background": PAL["bg"], "foreground": PAL["ink"], "tableAccent": PAL["blue"],
  "good": PAL["green"], "neutral": PAL["amber"], "bad": PAL["red"],
  "maximum": PAL["navy"], "center": PAL["blue"], "minimum": PAL["light"],
  "textClasses": {
    "title":     {"fontFace": "Segoe UI Semibold", "fontSize": 13, "color": PAL["navy"]},
    "header":    {"fontFace": "Segoe UI Semibold", "fontSize": 12, "color": PAL["navy"]},
    "label":     {"fontFace": "Segoe UI",          "fontSize": 10, "color": PAL["ink"]},
    "callout":   {"fontFace": "Segoe UI",          "fontSize": 30, "color": PAL["navy"]},
    "largeTitle":{"fontFace": "Segoe UI Semibold", "fontSize": 18, "color": PAL["navy"]},
  },
  "visualStyles": {
    "*": {"*": {
      "background":  [{"show": True, "color": {"solid": {"color": PAL["card"]}}, "transparency": 0}],
      "border":      [{"show": True, "color": {"solid": {"color": PAL["line"]}}, "radius": 8}],
      "dropShadow":  [{"show": True, "preset": "Subtle"}],
      "title":       [{"show": True, "fontColor": {"solid": {"color": PAL["navy"]}},
                       "fontSize": 12, "fontFamily": "Segoe UI Semibold", "alignment": "left"}],
      "visualHeader":[{"show": False}],
      "labels":      [{"color": {"solid": {"color": PAL["ink"]}}, "fontSize": 9}],
      "categoryAxis":[{"gridlineShow": False, "labelColor": {"solid": {"color": PAL["grey"]}}, "fontSize": 9}],
      "valueAxis":   [{"gridlineColor": {"solid": {"color": PAL["line"]}},
                       "labelColor": {"solid": {"color": PAL["grey"]}}, "fontSize": 9}],
      "legend":      [{"position": "Bottom", "labelColor": {"solid": {"color": PAL["grey"]}}, "fontSize": 9}],
    }},
    "card": {"*": {
      "labels":    [{"color": {"solid": {"color": PAL["navy"]}}, "fontSize": 26, "fontFamily": "Segoe UI Semibold"}],
      "categoryLabels": [{"color": {"solid": {"color": PAL["grey"]}}, "fontSize": 9}]}},
    "page": {"*": {"background": [{"color": {"solid": {"color": PAL["bg"]}}, "transparency": 0}]}},
  },
}

# ═══════════════════════════════════════════════ 1 · MODELO SEMÁNTICO ════
# ---- parámetros y expresiones compartidas -------------------------------
EXPR = """/// Carpeta local que contiene los CSV sintéticos (data/sample).
/// Cámbiala en Power BI: Inicio > Transformar datos > Administrar parámetros.
expression RutaDatos = "C:\\\\repo\\\\maintenance-performance-suite\\\\data\\\\sample" meta [IsParameterQuery=true, List={}, DefaultValue="", Type="Text", IsParameterQueryRequired=true]
\tlineageTag: __LT_RUTA__
\tqueryGroup: '00 · Parámetros'

\tannotation PBI_ResultType = Text

/// Margen de contribución por hora de detención (k$/h). Parámetro de Controlling
/// que monetiza el árbol de pérdidas de la Mejora Enfocada.
expression MargenHora = 34 meta [IsParameterQuery=true, List={}, DefaultValue=34, Type="Number", IsParameterQueryRequired=true]
\tlineageTag: __LT_MARGEN__
\tqueryGroup: '00 · Parámetros'

\tannotation PBI_ResultType = Number

/// Capacidad instalada de mantenimiento, en HH por semana (maestro CR03).
expression CapacidadSemanal = 540 meta [IsParameterQuery=true, List={}, DefaultValue=540, Type="Number", IsParameterQueryRequired=true]
\tlineageTag: __LT_CAP__
\tqueryGroup: '00 · Parámetros'

\tannotation PBI_ResultType = Number

annotation PBI_QueryGroupOrder = ["00 · Parámetros","01 · Hechos","02 · Dimensiones"]
"""
EXPR = (EXPR.replace("__LT_RUTA__", lt("expr.RutaDatos"))
            .replace("__LT_MARGEN__", lt("expr.MargenHora"))
            .replace("__LT_CAP__", lt("expr.CapacidadSemanal")))

# ---- definición de tablas ----------------------------------------------
# (nombre, grupo, descripción, columnas[(nombre,tipo,resumen,desc)], M)
TXT, INT, DEC, DAT, BOO = "string", "int64", "double", "dateTime", "boolean"

def csv_m(archivo, tipos, extra=""):
    """Consulta M que lee un CSV del parámetro RutaDatos y tipa sus columnas."""
    tl = ", ".join(f'{{"{c}", {t}}}' for c, t in tipos)
    return (f'let\n'
            f'    Origen = Csv.Document(\n'
            f'        File.Contents(RutaDatos & "\\{archivo}"),\n'
            f'        [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]\n'
            f'    ),\n'
            f'    Encabezados = Table.PromoteHeaders(Origen, [PromoteAllScalars = true]),\n'
            f'    Tipos = Table.TransformColumnTypes(Encabezados, {{{tl}}})'
            f'{extra}\n'
            f'in\n'
            f'    {"Final" if extra else "Tipos"}')

FECHA_M = ',\n    ConFecha = Table.AddColumn(Tipos, "Fecha", each Date.FromText([AnioMes] & "-01"), type date),\n    Final = ConFecha'

ORD_EXTRA = (
 ',\n    ConFecha = Table.AddColumn(Tipos, "Fecha", each Date.FromText([AnioMes] & "-01"), type date)'
 ',\n    // FlagsCalidad es una máscara de bits: se expande a cinco banderas auditables'
 ',\n    Flags = Table.AddColumn(ConFecha, "Banderas", each ['
 '\n            SinEquipo      = Number.BitwiseAnd([FlagsCalidad], 1),'
 '\n            SinAviso       = Number.BitwiseAnd([FlagsCalidad], 2) / 2,'
 '\n            CerradaSinHH   = Number.BitwiseAnd([FlagsCalidad], 4) / 4,'
 '\n            CostoSinCierre = Number.BitwiseAnd([FlagsCalidad], 8) / 8,'
 '\n            PrevVencida    = Number.BitwiseAnd([FlagsCalidad], 16) / 16'
 '\n        ], type record)'
 ',\n    Expandir = Table.ExpandRecordColumn(Flags, "Banderas",'
 '\n        {"SinEquipo","SinAviso","CerradaSinHH","CostoSinCierre","PrevVencida"})'
 ',\n    TiposFlags = Table.TransformColumnTypes(Expandir, {'
 '\n        {"SinEquipo", Int64.Type}, {"SinAviso", Int64.Type}, {"CerradaSinHH", Int64.Type},'
 '\n        {"CostoSinCierre", Int64.Type}, {"PrevVencida", Int64.Type}})'
 ',\n    Final = Table.Distinct(TiposFlags, {"Orden"})')

DIMFECHA_M = '''let
    // Calendario generado en M: cubre el dataset sintético con margen a ambos lados.
    Inicio = #date(2025, 1, 1),
    Fin    = #date(2026, 12, 31),
    Dias   = Duration.Days(Fin - Inicio) + 1,
    Lista  = List.Dates(Inicio, Dias, #duration(1, 0, 0, 0)),
    Tabla  = Table.FromList(Lista, Splitter.SplitByNothing(), {"Fecha"}),
    Tipo   = Table.TransformColumnTypes(Tabla, {{"Fecha", type date}}),
    C1  = Table.AddColumn(Tipo, "Anio",         each Date.Year([Fecha]), Int64.Type),
    C2  = Table.AddColumn(C1,   "Mes",          each Date.Month([Fecha]), Int64.Type),
    C3  = Table.AddColumn(C2,   "NombreMes",    each Date.MonthName([Fecha]), type text),
    C4  = Table.AddColumn(C3,   "Trimestre",    each "T" & Text.From(Date.QuarterOfYear([Fecha])), type text),
    C5  = Table.AddColumn(C4,   "Semestre",     each "S" & Text.From(Number.RoundUp(Date.Month([Fecha]) / 6)), type text),
    C6  = Table.AddColumn(C5,   "AnioMes",      each Date.ToText([Fecha], "yyyy-MM"), type text),
    C7  = Table.AddColumn(C6,   "OrdenAnioMes", each [Anio] * 100 + [Mes], Int64.Type),
    C8  = Table.AddColumn(C7,   "MesCorto",     each Text.Proper(Text.Start(Date.MonthName([Fecha]), 3)) & " " & Text.End(Text.From([Anio]), 2), type text),
    C9  = Table.AddColumn(C8,   "InicioMes",    each Date.StartOfMonth([Fecha]), type date),
    C10 = Table.AddColumn(C9,   "EsLaboral",    each Date.DayOfWeek([Fecha], Day.Monday) < 5, type logical)
in
    C10'''

def inline_tbl(cols, filas):
    c = ", ".join(f'"{x}"' for x in cols)
    f = ",\n        ".join("{" + ", ".join(f'"{v}"' for v in r) + "}" for r in filas)
    return f'let\n    Origen = #table(\n        {{{c}}},\n        {{\n        {f}\n        }}\n    )\nin\n    Origen'

TABLAS = [
 ("FactOrdenesMtto", "01 · Hechos",
  "Hechos de órdenes de mantenimiento. Fuente: SAP PM · IW39 / IW38. Grano: una fila por orden. "
  "Costos (CO · KOB1) y horas hombre (IW47) vienen denormalizados en este dataset sintético.",
  [("Orden",TXT,"none","N.º de orden SAP. Texto para preservar ceros a la izquierda."),
   ("AnioMes",TXT,"none","Clave aaaa-MM."),("Fecha",DAT,"none","Primer día del mes. Relaciona con DimFecha."),
   ("Area",TXT,"none","Área de empresa."),("Linea",TXT,"none","Línea productiva."),
   ("Equipo",TXT,"none","Código de equipo. FK a DimEquipo."),
   ("DenominacionEquipo",TXT,"none","Denominación del equipo."),
   ("Criticidad",TXT,"none","A crítico · B esencial · C general."),
   ("TipoMantenimiento",TXT,"none","Derivada de la clase de orden."),
   ("ClaseOrden",TXT,"none","PM01 a PM06. FK a DimTipoOrden."),
   ("EstadoCierre",TXT,"none","Abierta o Cerrada, derivada del status de sistema."),
   ("Trabajo",DEC,"sum","HH planificadas."),("TrabajoReal",DEC,"sum","HH reales confirmadas."),
   ("CostoPlan",DEC,"sum","Costo planificado en k$."),("CostoReal",DEC,"sum","Costo real imputado en k$."),
   ("DiasCierre",INT,"none","Días entre creación y cierre técnico."),
   ("RetrasoDias",INT,"none","Días de retraso contra la fecha fin extrema."),
   ("FlagsCalidad",INT,"none","Máscara de bits de calidad de datos."),
   ("GrupoPlanificador",TXT,"none","Gremio responsable."),("Prioridad",TXT,"none","Alta, Media o Baja."),
   ("MotivoDetencion",TXT,"none","Causa de la detención cuando la orden está bloqueada."),
   ("SinEquipo",INT,"sum","Bandera: orden sin equipo asignado."),
   ("SinAviso",INT,"sum","Bandera: orden sin aviso de origen."),
   ("CerradaSinHH",INT,"sum","Bandera: cerrada sin horas confirmadas."),
   ("CostoSinCierre",INT,"sum","Bandera: costo imputado con orden abierta."),
   ("PrevVencida",INT,"sum","Bandera: preventiva fuera de ventana.")],
  csv_m("FactOrdenesMtto.csv",
        [("Orden",TXT),("AnioMes",TXT),("Area",TXT),("Linea",TXT),("Equipo",TXT),
         ("DenominacionEquipo",TXT),("Criticidad",TXT),("TipoMantenimiento",TXT),("ClaseOrden",TXT),
         ("EstadoCierre",TXT),("Trabajo","type number"),("TrabajoReal","type number"),
         ("CostoPlan","type number"),("CostoReal","type number"),("DiasCierre","Int64.Type"),
         ("RetrasoDias","Int64.Type"),("FlagsCalidad","Int64.Type"),("GrupoPlanificador",TXT),
         ("Prioridad",TXT),("MotivoDetencion",TXT)], ORD_EXTRA)),

 ("FactAvisosMtto", "01 · Hechos",
  "Hechos de avisos de mantenimiento. Fuente: SAP PM · IW28 / IW29. Grano: un aviso. "
  "Aporta la duración de parada, única fuente válida para el MTTR.",
  [("Aviso",TXT,"none","N.º de aviso SAP."),("AnioMes",TXT,"none","Clave aaaa-MM."),
   ("Fecha",DAT,"none","Relaciona con DimFecha."),
   ("Equipo",TXT,"none","FK a DimEquipo."),("DenominacionEquipo",TXT,"none","Denominación."),
   ("Area",TXT,"none","Área."),("Linea",TXT,"none","Línea."),("Criticidad",TXT,"none","A, B o C."),
   ("Causa",TXT,"none","Código de daño. Base del Pareto de causas."),
   ("DuracionParada_h",DEC,"sum","Horas de detención declaradas. Base del MTTR y del árbol de pérdidas."),
   ("CategoriaPerdida",TXT,"none","Una de las 6 grandes pérdidas del TPM."),
   ("LigadoAOrden",INT,"sum","1 si el aviso derivó en orden.")],
  csv_m("FactAvisosMtto.csv",
        [("Aviso",TXT),("AnioMes",TXT),("Equipo",TXT),("DenominacionEquipo",TXT),("Area",TXT),
         ("Linea",TXT),("Criticidad",TXT),("Causa",TXT),("DuracionParada_h","type number"),
         ("CategoriaPerdida",TXT),("LigadoAOrden","Int64.Type")], FECHA_M)),

 ("FactPlanesMtto", "01 · Hechos",
  "Posiciones de planes preventivos. Fuente: SAP PM · IP15 / IP24. Grano: posición por mes.",
  [("AnioMes",TXT,"none","Clave aaaa-MM."),("Fecha",DAT,"none","Relaciona con DimFecha."),
   ("Plan",TXT,"none","Código del plan de mantenimiento."),
   ("Equipo",TXT,"none","FK a DimEquipo."),("DenominacionEquipo",TXT,"none","Denominación."),
   ("Area",TXT,"none","Área."),("Criticidad",TXT,"none","A, B o C."),
   ("Estrategia",TXT,"none","Tipo de intervención programada."),
   ("Ciclo",TXT,"none","Frecuencia del ciclo."),
   ("Estado",TXT,"none","Cumplido o Vencido en su ventana.")],
  csv_m("FactPlanesMtto.csv",
        [("AnioMes",TXT),("Plan",TXT),("Equipo",TXT),("DenominacionEquipo",TXT),("Area",TXT),
         ("Criticidad",TXT),("Estrategia",TXT),("Ciclo",TXT),("Estado",TXT)], FECHA_M)),

 ("FactMaterialesMtto", "01 · Hechos",
  "Consumo de repuestos. Fuente: SAP MM · MB51. Grano: material por mes y área.",
  [("AnioMes",TXT,"none","Clave aaaa-MM."),("Fecha",DAT,"none","Relaciona con DimFecha."),
   ("Material",TXT,"none","FK a DimMaterial."),("Descripcion",TXT,"none","Descripción del material."),
   ("Area",TXT,"none","Área que consume."),("Cantidad",DEC,"sum","Unidades consumidas."),
   ("Importe",DEC,"sum","Valor del consumo en k$."),
   ("EsRepuestoCritico",BOO,"none","Marca de criticidad del repuesto.")],
  csv_m("FactMaterialesMtto.csv",
        [("AnioMes",TXT),("Material",TXT),("Descripcion",TXT),("Area",TXT),
         ("Cantidad","Int64.Type"),("Importe","type number"),("EsRepuestoCritico","type logical")], FECHA_M)),

 ("FactProduccion", "01 · Hechos",
  "Producción y horas de operación. Fuente: SAP PP · COOIS / LIS. Grano: línea por mes. "
  "Habilita MTBF, disponibilidad y los indicadores por tonelada.",
  [("AnioMes",TXT,"none","Clave aaaa-MM."),("Fecha",DAT,"none","Relaciona con DimFecha."),
   ("Area",TXT,"none","Área."),("Linea",TXT,"none","Línea."),
   ("ToneladasProducidas",DEC,"sum","Volumen producido."),
   ("HorasOperacion",DEC,"sum","Horas operativas de la línea."),
   ("HorasDetencion",DEC,"sum","Horas de detención de la línea.")],
  csv_m("FactProduccion.csv",
        [("AnioMes",TXT),("Area",TXT),("Linea",TXT),("ToneladasProducidas","type number"),
         ("HorasOperacion","type number"),("HorasDetencion","type number")], FECHA_M)),

 ("FactKaizen", "01 · Hechos",
  "Cartera de iniciativas A3 de Mejora Enfocada. Registro propio del pilar, no nativo de SAP: "
  "el ahorro se valida contra documentos de costo en CO.",
  [("A3",TXT,"none","Identificador de la iniciativa."),
   ("PerdidaAtacada",TXT,"none","Pérdida que la iniciativa ataca."),
   ("Equipo",TXT,"none","Equipo intervenido."),("Area",TXT,"none","Área."),
   ("EquipoTrabajo",TXT,"none","Equipo multidisciplinario responsable."),
   ("FasePDCA",TXT,"none","Plan, Do, Check o Act."),
   ("AhorroValidado",DEC,"sum","Ahorro confirmado en CO, en k$."),
   ("AnioMesInicio",TXT,"none","Mes de apertura del A3."),
   ("KPI",TXT,"none","Indicador que mide el efecto."),
   ("Antes",DEC,"none","Valor del KPI antes de la contramedida."),
   ("Despues",DEC,"none","Valor del KPI después de la contramedida.")],
  csv_m("FactKaizen.csv",
        [("A3",TXT),("PerdidaAtacada",TXT),("Equipo",TXT),("Area",TXT),("EquipoTrabajo",TXT),
         ("FasePDCA",TXT),("AhorroValidado","type number"),("AnioMesInicio",TXT),("KPI",TXT),
         ("Antes","type number"),("Despues","type number")])),

 ("DimFecha", "02 · Dimensiones",
  "Calendario generado en M. Marcada como tabla de fechas: conecta los cinco hechos por su fecha relevante.",
  [("Fecha",DAT,"none","Clave de relación."),("Anio",INT,"none","Año."),("Mes",INT,"none","Mes."),
   ("NombreMes",TXT,"none","Nombre del mes."),("Trimestre",TXT,"none","T1 a T4."),
   ("Semestre",TXT,"none","S1 o S2."),("AnioMes",TXT,"none","aaaa-MM."),
   ("OrdenAnioMes",INT,"none","Clave de ordenamiento cronológico."),
   ("MesCorto",TXT,"none","Etiqueta corta para ejes."),("InicioMes",DAT,"none","Primer día del mes."),
   ("EsLaboral",BOO,"none","Verdadero de lunes a viernes.")],
  DIMFECHA_M),

 ("DimEquipo", "02 · Dimensiones",
  "Maestro de equipos. Fuente: SAP PM · IH08 / IE03. La criticidad gobierna la priorización de todo el sistema.",
  [("Equipo",TXT,"none","Código de equipo SAP."),("Denominacion",TXT,"none","Nombre del equipo."),
   ("Area",TXT,"none","Área."),("Linea",TXT,"none","Línea."),
   ("Criticidad",TXT,"none","A crítico · B esencial · C general."),
   ("Familia",TXT,"none","Taxonomía de activos."),("Fabricante",TXT,"none","Fabricante."),
   ("Anio",INT,"none","Año de puesta en marcha."),
   ("PesoFalla",DEC,"none","Propensión a falla usada por el generador sintético.")],
  csv_m("DimEquipo.csv",
        [("Equipo",TXT),("Denominacion",TXT),("Area",TXT),("Linea",TXT),("Criticidad",TXT),
         ("Familia",TXT),("Fabricante",TXT),("Anio","Int64.Type"),("PesoFalla","type number")])),

 ("DimMaterial", "02 · Dimensiones",
  "Maestro de materiales. Fuente: SAP MM · MM03 / MB52. Stock, mínimo y lead time habilitan la alerta de quiebre.",
  [("Material",TXT,"none","Código de material."),("Descripcion",TXT,"none","Descripción."),
   ("ABC",TXT,"none","Clasificación ABC."),("StockActual",INT,"sum","Stock disponible."),
   ("StockMinimo",INT,"sum","Stock mínimo definido."),("LeadTimeDias",INT,"none","Plazo de aprovisionamiento."),
   ("EsRepuestoCritico",BOO,"none","Marca de criticidad."),("PrecioUnitario",DEC,"none","Precio en k$.")],
  csv_m("DimMaterial.csv",
        [("Material",TXT),("Descripcion",TXT),("ABC",TXT),("StockActual","Int64.Type"),
         ("StockMinimo","Int64.Type"),("LeadTimeDias","Int64.Type"),
         ("EsRepuestoCritico","type logical"),("PrecioUnitario","type number")])),

 ("DimTipoOrden", "02 · Dimensiones",
  "Catálogo de clases de orden SAP y su tipificación de mantenimiento.",
  [("ClaseOrden",TXT,"none","PM01 a PM06."),("TipoMantenimiento",TXT,"none","Tipificación."),
   ("Descripcion",TXT,"none","Descripción de la clase."),
   ("EsPlanificado",TXT,"none","Sí para trabajo planificado, No para reactivo.")],
  inline_tbl(["ClaseOrden","TipoMantenimiento","Descripcion","EsPlanificado"], [
    ["PM01","Correctivo","Correctivo estándar","No"],
    ["PM02","Preventivo","Preventivo por tiempo","Sí"],
    ["PM03","Preventivo","Preventivo por condición","Sí"],
    ["PM04","Mejora","Mejora / contramedida A3","Sí"],
    ["PM05","Emergencia","Correctivo de emergencia","No"],
    ["PM06","Predictivo","Predictivo por monitoreo","Sí"]])),

 ("DimArea", "02 · Dimensiones", "Áreas de empresa del alcance.",
  [("Area",TXT,"none","Área de empresa."),("TipoArea",TXT,"none","Productiva o de soporte.")],
  inline_tbl(["Area","TipoArea"], [["Envasado","Productiva"],["Proceso","Productiva"],
                                   ["Servicios","Soporte"],["Bodega","Soporte"]])),

 ("DimLinea", "02 · Dimensiones", "Líneas productivas.",
  [("Linea",TXT,"none","Línea productiva."),("EsProductiva",TXT,"none","Sí o No.")],
  inline_tbl(["Linea","EsProductiva"], [["Línea 1","Sí"],["Línea 2","Sí"],
                                        ["Línea 3","Sí"],["N/A","No"]])),

 ("DimCriticidad", "02 · Dimensiones",
  "Matriz de criticidad de activos. Gobierna la priorización de planes, repuestos y RCA.",
  [("Criticidad",TXT,"none","A, B o C."),("Descripcion",TXT,"none","Significado operacional."),
   ("Orden",INT,"none","Orden de despliegue.")],
  inline_tbl(["Criticidad","Descripcion","Orden"], [
    ["A","Crítico · detiene producción","1"],["B","Esencial · degrada producción","2"],
    ["C","General · sin impacto inmediato","3"]])),

 ("DimGrupoPlanificador", "02 · Dimensiones",
  "Gremios de mantenimiento y su capacidad semanal declarada en CR03.",
  [("GrupoPlanificador",TXT,"none","Especialidad."),
   ("CapacidadSemanalHH",INT,"sum","HH semanales disponibles.")],
  inline_tbl(["GrupoPlanificador","CapacidadSemanalHH"], [
    ["Mecánico","240"],["Eléctrico","140"],["Instrumentación","90"],["Servicios","70"]])),
]

# ---- medidas DAX --------------------------------------------------------
# (nombre, dax, carpeta, formato, descripción)
M = [
 # ── F2/F3 · Volumen y mix ───────────────────────────────────────────────
 ("Órdenes Totales", "COUNTROWS ( FactOrdenesMtto )", "01 · Volumen y mix", "#,0",
  "Conteo de órdenes en el contexto de filtro. Fuente: IW39."),
 ("Órdenes Cerradas", 'CALCULATE ( [Órdenes Totales], FactOrdenesMtto[EstadoCierre] = "Cerrada" )',
  "01 · Volumen y mix", "#,0", "Órdenes con cierre técnico."),
 ("Órdenes Abiertas", 'CALCULATE ( [Órdenes Totales], FactOrdenesMtto[EstadoCierre] = "Abierta" )',
  "01 · Volumen y mix", "#,0", "Órdenes pendientes. Base del backlog."),
 ("Correctivas", 'CALCULATE ( [Órdenes Totales], FactOrdenesMtto[TipoMantenimiento] IN { "Correctivo", "Emergencia" } )',
  "01 · Volumen y mix", "#,0", "Correctivo estándar más emergencia."),
 ("Preventivas", 'CALCULATE ( [Órdenes Totales], FactOrdenesMtto[TipoMantenimiento] = "Preventivo" )',
  "01 · Volumen y mix", "#,0", "Órdenes preventivas."),
 ("% Órdenes Correctivas", "DIVIDE ( [Correctivas], [Órdenes Totales], 0 )", "01 · Volumen y mix", "0.0%",
  "Meta ≤ 30%; cuartil superior ≤ 20%. Cuidado: un valor bajo puede ser sub-registro, no buen desempeño."),
 ("% Órdenes Preventivas", "DIVIDE ( [Preventivas], [Órdenes Totales], 0 )", "01 · Volumen y mix", "0.0%",
  "Meta ≥ 70%."),
 ("% Trabajo Planificado",
  'VAR Planificado = CALCULATE ( [Órdenes Totales], DimTipoOrden[EsPlanificado] = "Sí" )\nRETURN\n    DIVIDE ( Planificado, [Órdenes Totales], 0 )',
  "01 · Volumen y mix", "0.0%", "Referencia de industria: 80%; alto desempeño ≥ 85%."),
 ("Ratio Preventivo / Correctivo", "DIVIDE ( [Preventivas], [Correctivas], 0 )", "01 · Volumen y mix", "0.00",
  "Meta ≥ 2,3."),
 ("Cumplimiento PM",
  'VAR CerradasPM =\n    CALCULATE (\n        [Órdenes Totales],\n        FactOrdenesMtto[TipoMantenimiento] = "Preventivo",\n        FactOrdenesMtto[EstadoCierre] = "Cerrada"\n    )\nRETURN\n    DIVIDE ( CerradasPM, [Preventivas], 0 )',
  "01 · Volumen y mix", "0.0%", "Preventivas cerradas sobre preventivas creadas."),
 ("Posiciones de Plan", "COUNTROWS ( FactPlanesMtto )", "01 · Volumen y mix", "#,0",
  "Posiciones de plan preventivo del período. Fuente: IP24."),
 ("Planes Vencidos", 'CALCULATE ( [Posiciones de Plan], FactPlanesMtto[Estado] = "Vencido" )',
  "01 · Volumen y mix", "#,0", "Posiciones fuera de su ventana."),
 ("Cumplimiento Plan Preventivo",
  'DIVIDE (\n    CALCULATE ( [Posiciones de Plan], FactPlanesMtto[Estado] = "Cumplido" ),\n    [Posiciones de Plan],\n    0\n)',
  "01 · Volumen y mix", "0.0%", "Meta ≥ 90%; cuartil superior ≥ 95%."),

 # ── F5 · Confiabilidad ──────────────────────────────────────────────────
 ("N.º Avisos", "COUNTROWS ( FactAvisosMtto )", "02 · Confiabilidad", "#,0", "Avisos registrados. Fuente: IW29."),
 ("N.º Averías", 'CALCULATE ( [N.º Avisos], FactAvisosMtto[CategoriaPerdida] = "Averías" )',
  "02 · Confiabilidad", "#,0", "Avisos clasificados como avería. Denominador del MTBF."),
 ("Horas de Detención", "SUM ( FactAvisosMtto[DuracionParada_h] )", "02 · Confiabilidad", "#,0.0",
  "Horas de parada declaradas en el aviso."),
 ("MTTR (h)", "AVERAGE ( FactAvisosMtto[DuracionParada_h] )", "02 · Confiabilidad", "#,0.0",
  "Tiempo medio de reparación. Se calcula desde la duración de parada del aviso, NO desde las HH de la orden: "
  "las HH son horas hombre, no horas de reloj."),
 ("Horas de Operación", "SUM ( FactProduccion[HorasOperacion] )", "02 · Confiabilidad", "#,0",
  "Horas operativas de línea. Fuente: COOIS."),
 ("Horas Equipo",
  "VAR LineasActivas = MAX ( 1, DISTINCTCOUNT ( FactProduccion[Linea] ) )\nVAR EquiposActivos = COUNTROWS ( DimEquipo )\nRETURN\n    DIVIDE ( [Horas de Operación], LineasActivas ) * EquiposActivos",
  "02 · Confiabilidad", "#,0",
  "Horas operativas expresadas por equipo. Sin esta conversión el MTBF queda subestimado."),
 ("MTBF (h)", "DIVIDE ( [Horas Equipo], [N.º Averías], BLANK () )", "02 · Confiabilidad", "#,0",
  "Tiempo medio entre fallas."),
 ("Disponibilidad Operacional",
  "1 - DIVIDE ( SUM ( FactProduccion[HorasDetencion] ), SUM ( FactProduccion[HorasOperacion] ), 0 )",
  "02 · Confiabilidad", "0.0%", "Meta ≥ 92%; cuartil superior ≥ 95%. Fuente: COOIS."),
 ("OEE Parcial", "[Disponibilidad Operacional] * 0.86 * 0.94", "02 · Confiabilidad", "0.0%",
  "BRECHA DECLARADA: solo el componente Disponibilidad proviene de dato real. Rendimiento y Calidad usan "
  "supuestos fijos porque SAP PM no entrega velocidad de línea ni defectos. No comprometer metas sobre esta medida."),

 # ── F2/F3 · Backlog, cierre y SLA ───────────────────────────────────────
 ("HH Planificadas", "SUM ( FactOrdenesMtto[Trabajo] )", "03 · Backlog y ejecución", "#,0", "Horas hombre planificadas."),
 ("HH Reales", "SUM ( FactOrdenesMtto[TrabajoReal] )", "03 · Backlog y ejecución", "#,0", "Horas hombre confirmadas."),
 ("Desviación HH", "[HH Reales] - [HH Planificadas]", "03 · Backlog y ejecución", "#,0", "Diferencia absoluta."),
 ("% Cumplimiento HH", "DIVIDE ( [HH Reales], [HH Planificadas], 0 )", "03 · Backlog y ejecución", "0.0%",
  "Rango sano 90% a 110%."),
 ("Backlog HH",
  'SUMX (\n    FILTER ( FactOrdenesMtto, FactOrdenesMtto[EstadoCierre] = "Abierta" ),\n    MAX ( 0, FactOrdenesMtto[Trabajo] - FactOrdenesMtto[TrabajoReal] )\n)',
  "03 · Backlog y ejecución", "#,0",
  "HH pendientes de órdenes ABIERTAS. Incluir las cerradas devuelve cero o negativo."),
 ("Capacidad Semanal HH",
  "VAR PorGrupo = SUM ( DimGrupoPlanificador[CapacidadSemanalHH] )\nRETURN\n    IF ( ISBLANK ( PorGrupo ), CapacidadSemanal, PorGrupo )",
  "03 · Backlog y ejecución", "#,0", "Capacidad del gremio filtrado, o el parámetro global si no hay filtro."),
 ("Backlog Semanas", "DIVIDE ( [Backlog HH], [Capacidad Semanal HH], 0 )", "03 · Backlog y ejecución", "0.0",
  "Rango sano 2 a 4 semanas. Bajo 1 indica falta de trabajo preparado; sobre 6, saturación."),
 ("Tiempo Promedio de Cierre (d)", "AVERAGE ( FactOrdenesMtto[DiasCierre] )", "03 · Backlog y ejecución", "0.0",
  "Días entre creación y cierre técnico."),
 ("Órdenes Retrasadas", "CALCULATE ( [Órdenes Totales], FactOrdenesMtto[RetrasoDias] > 0 )",
  "03 · Backlog y ejecución", "#,0", "Órdenes fuera de su fecha fin extrema."),
 ("% Órdenes Retrasadas", "DIVIDE ( [Órdenes Retrasadas], [Órdenes Totales], 0 )",
  "03 · Backlog y ejecución", "0.0%", "Meta ≤ 10%."),
 ("SLA Cierre 7 días",
  'VAR EnSLA =\n    CALCULATE (\n        [Órdenes Totales],\n        FactOrdenesMtto[EstadoCierre] = "Cerrada",\n        FactOrdenesMtto[DiasCierre] <= 7\n    )\nRETURN\n    DIVIDE ( EnSLA, [Órdenes Cerradas], 0 )',
  "03 · Backlog y ejecución", "0.0%", "Meta ≥ 85%."),
 ("Órdenes Envejecidas", "CALCULATE ( [Órdenes Abiertas], FactOrdenesMtto[RetrasoDias] > 30 )",
  "03 · Backlog y ejecución", "#,0", "Abiertas con más de 30 días de retraso."),
 ("HH Bloqueadas por Repuesto",
  'CALCULATE ( [Backlog HH], FactOrdenesMtto[MotivoDetencion] = "Espera de repuesto" )',
  "03 · Backlog y ejecución", "#,0", "Correlaciona abastecimiento con backlog."),

 # ── F4 · Costos ─────────────────────────────────────────────────────────
 ("Costo Total", "SUM ( FactOrdenesMtto[CostoReal] )", "04 · Costos", "#,0.0", "Costo real en k$. Fuente: KOB1."),
 ("Costo Plan", "SUM ( FactOrdenesMtto[CostoPlan] )", "04 · Costos", "#,0.0", "Costo planificado en k$."),
 ("Costo Total M$", "DIVIDE ( [Costo Total], 1000 )", "04 · Costos", "#,0.0", "Costo real en millones."),
 ("Costo Correctivo",
  'CALCULATE ( [Costo Total], FactOrdenesMtto[TipoMantenimiento] IN { "Correctivo", "Emergencia" } )',
  "04 · Costos", "#,0.0", "Gasto reactivo."),
 ("Costo Preventivo", 'CALCULATE ( [Costo Total], FactOrdenesMtto[TipoMantenimiento] = "Preventivo" )',
  "04 · Costos", "#,0.0", "Gasto planificado."),
 ("% Costo Preventivo", "DIVIDE ( [Costo Preventivo], [Costo Preventivo] + [Costo Correctivo], 0 )",
  "04 · Costos", "0.0%", "Meta ≥ 60%."),
 ("Costo Promedio por Orden", "DIVIDE ( [Costo Total], [Órdenes Totales], 0 )", "04 · Costos", "#,0.0",
  "Costo unitario medio."),
 ("Varianza Costo", "[Costo Total] - [Costo Plan]", "04 · Costos", "#,0.0", "Real menos plan, en k$."),
 ("% Varianza Costo", "DIVIDE ( [Varianza Costo], [Costo Plan], 0 )", "04 · Costos", "0.0%",
  "Rango aceptable ±10%. Reportar separada por tipo de mantenimiento, nunca agregada."),
 ("Toneladas Producidas", "SUM ( FactProduccion[ToneladasProducidas] )", "04 · Costos", "#,0", "Volumen. Fuente: COOIS."),
 ("Costo por Tonelada", "DIVIDE ( [Costo Total] * 1000, [Toneladas Producidas], 0 )", "04 · Costos", "#,0",
  "Costo de mantenimiento normalizado por volumen, en $ por tonelada."),
 ("HH por Tonelada", "DIVIDE ( [HH Reales], [Toneladas Producidas], 0 )", "04 · Costos", "0.000",
  "Esfuerzo de mantenimiento por unidad producida."),
 ("Consumo de Repuestos", "SUM ( FactMaterialesMtto[Importe] )", "04 · Costos", "#,0.0",
  "Valor consumido en k$. Fuente: MB51."),
 ("Repuestos Críticos Bajo Stock",
  "CALCULATE (\n    COUNTROWS ( DimMaterial ),\n    DimMaterial[EsRepuestoCritico] = TRUE (),\n    FILTER ( DimMaterial, DimMaterial[StockActual] <= DimMaterial[StockMinimo] )\n)",
  "04 · Costos", "#,0", "Materiales críticos en o bajo su mínimo: riesgo directo de parada extendida."),
 ("Lead Time Promedio", "AVERAGE ( DimMaterial[LeadTimeDias] )", "04 · Costos", "#,0",
  "Días de aprovisionamiento. Fuente: MM03 / ME2N."),

 # ── T · Calidad de datos ────────────────────────────────────────────────
 ("Órdenes sin Equipo", "SUM ( FactOrdenesMtto[SinEquipo] )", "05 · Calidad de datos", "#,0",
  "Rompen la jerarquía técnica: distorsionan MTBF y todos los análisis por activo."),
 ("Órdenes sin Aviso", "SUM ( FactOrdenesMtto[SinAviso] )", "05 · Calidad de datos", "#,0",
  "Pierden la trazabilidad de la falla: sin ellas no hay causa raíz."),
 ("Cerradas sin HH", "SUM ( FactOrdenesMtto[CerradaSinHH] )", "05 · Calidad de datos", "#,0",
  "Subestiman el MTTR y el backlog: hacen que la operación parezca mejor de lo que es."),
 ("Costo sin Cierre", "SUM ( FactOrdenesMtto[CostoSinCierre] )", "05 · Calidad de datos", "#,0",
  "Desplazan el costo al período equivocado."),
 ("Preventivas Vencidas", "SUM ( FactOrdenesMtto[PrevVencida] )", "05 · Calidad de datos", "#,0",
  "Inflan el mix preventivo aparente."),
 ("Índice de Calidad de Datos",
  "VAR Banderas =\n    [Órdenes sin Equipo] + [Órdenes sin Aviso] + [Cerradas sin HH]\n        + [Costo sin Cierre] + [Preventivas Vencidas]\nVAR Controles = [Órdenes Totales] * 5\nRETURN\n    1 - DIVIDE ( Banderas, Controles, 0 )",
  "05 · Calidad de datos", "0.0%",
  "CONDICIÓN HABILITANTE. Meta ≥ 95%. Bajo ese umbral ningún otro KPI es plenamente confiable "
  "y no debe usarse para comprometer inversión."),
 ("Trazabilidad Aviso → Orden",
  "DIVIDE ( SUM ( FactAvisosMtto[LigadoAOrden] ), [N.º Avisos], 0 )",
  "05 · Calidad de datos", "0.0%", "Avisos que derivaron en orden."),

 # ── Mejora Enfocada ─────────────────────────────────────────────────────
 ("Margen por Hora", "MargenHora", "06 · Mejora Enfocada", "#,0",
  "Parámetro de Controlling en k$ por hora de detención. Monetiza el árbol de pérdidas."),
 ("Pérdida Total",
  "DIVIDE ( [Horas de Detención] * [Margen por Hora], 1000 )", "06 · Mejora Enfocada", "#,0.0",
  "Pérdida del período en M$: horas de detención por el margen de contribución por hora."),
 ("Pérdida por Averías",
  'DIVIDE (\n    CALCULATE ( [Horas de Detención], FactAvisosMtto[CategoriaPerdida] = "Averías" ) * [Margen por Hora],\n    1000\n)',
  "06 · Mejora Enfocada", "#,0.0", "Pérdida atribuible a averías, la categoría dominante."),
 ("Ahorro Validado",
  'DIVIDE ( CALCULATE ( SUM ( FactKaizen[AhorroValidado] ), FactKaizen[FasePDCA] = "Act" ), 1000 )',
  "06 · Mejora Enfocada", "#,0.0",
  "Solo A3 en fase Act, es decir con ahorro confirmado en CO y estándar actualizado. "
  "Nunca se contabiliza ahorro estimado."),
 ("Kaizen Activos", 'CALCULATE ( COUNTROWS ( FactKaizen ), FactKaizen[FasePDCA] <> "Act" )',
  "06 · Mejora Enfocada", "#,0", "Iniciativas en Plan, Do o Check."),
 ("Kaizen Totales", "COUNTROWS ( FactKaizen )", "06 · Mejora Enfocada", "#,0", "Cartera completa."),
 ("% Pérdidas Atacadas",
  'VAR Cubiertas =\n    CALCULATE (\n        [Pérdida Total],\n        FactAvisosMtto[CategoriaPerdida] IN { "Averías", "Paradas menores", "Setup y ajustes" }\n    )\nRETURN\n    DIVIDE ( Cubiertas, [Pérdida Total], 0 )',
  "06 · Mejora Enfocada", "0.0%",
  "Proporción de la pérdida con A3 asignado. El resto marca el techo del ahorro cuando cierren los actuales."),

 # ── Madurez y benchmark ─────────────────────────────────────────────────
 ("Score F1 Activos",
  "VAR Limpieza = 1 - DIVIDE ( [Órdenes sin Equipo], [Órdenes Totales], 0 )\nRETURN\n    MAX ( 1, MIN ( 5, 1 + 4 * DIVIDE ( Limpieza - 0.93, 0.07 ) ) )",
  "07 · Madurez y benchmark", "0.0", "Gestión de activos, escalado 1 a 5 desde el propio dato SAP."),
 ("Score F2 Planificación",
  "MAX ( 1, MIN ( 5, 1 + 4 * DIVIDE ( [Cumplimiento Plan Preventivo] - 0.78, 0.20 ) ) )",
  "07 · Madurez y benchmark", "0.0", "Planificación y programación."),
 ("Score F3 Ejecución",
  "VAR Limpieza = 1 - DIVIDE ( [Cerradas sin HH], [Órdenes Totales], 0 )\nRETURN\n    MAX ( 1, MIN ( 5, 1 + 4 * DIVIDE ( Limpieza - 0.93, 0.07 ) ) )",
  "07 · Madurez y benchmark", "0.0", "Ejecución y disciplina de cierre."),
 ("Score F4 Costos",
  "VAR Ajuste = 1 - ABS ( [% Varianza Costo] )\nRETURN\n    MAX ( 1, MIN ( 5, 1 + 4 * DIVIDE ( Ajuste - 0.92, 0.08 ) ) )",
  "07 · Madurez y benchmark", "0.0", "Control de costos."),
 ("Score F5 Confiabilidad",
  "MAX ( 1, MIN ( 5, 1 + 4 * DIVIDE ( [Disponibilidad Operacional] - 0.885, 0.08 ) ) )",
  "07 · Madurez y benchmark", "0.0", "Confiabilidad y mejora continua."),
 ("Madurez Promedio",
  "AVERAGEX (\n    { [Score F1 Activos], [Score F2 Planificación], [Score F3 Ejecución], [Score F4 Costos], [Score F5 Confiabilidad] },\n    [Value]\n)",
  "07 · Madurez y benchmark", "0.0", "Promedio de los cinco pilares. Meta 4,0."),
 ("Brecha % Planificado", "[% Trabajo Planificado] - 0.85", "07 · Madurez y benchmark", "0.0%",
  "Distancia al cuartil superior de industria (85%)."),
 ("Brecha Disponibilidad", "[Disponibilidad Operacional] - 0.95", "07 · Madurez y benchmark", "0.0%",
  "Distancia al cuartil superior (95%)."),
 ("KPI Bajo Referencia",
  "VAR B1 = IF ( [% Trabajo Planificado] < 0.85, 1, 0 )\nVAR B2 = IF ( [% Órdenes Correctivas] > 0.20, 1, 0 )\nVAR B3 = IF ( [Disponibilidad Operacional] < 0.95, 1, 0 )\nVAR B4 = IF ( [Cumplimiento Plan Preventivo] < 0.95, 1, 0 )\nVAR B5 = IF ( [Índice de Calidad de Datos] < 0.95, 1, 0 )\nRETURN\n    B1 + B2 + B3 + B4 + B5",
  "07 · Madurez y benchmark", "#,0",
  "Número de indicadores bajo la referencia externa de cuartil superior."),
 ("Valor de la Brecha M$",
  "VAR GapPlan = MAX ( 0, 0.85 - [% Trabajo Planificado] ) * 100 * 0.62\nVAR GapDisp = MAX ( 0, 0.95 - [Disponibilidad Operacional] ) * 100 * 1.35\nRETURN\n    GapPlan + GapDisp",
  "07 · Madurez y benchmark", "#,0.0",
  "Valor anual recuperable al cerrar la brecha, estimado por punto porcentual. "
  "Referencia orientativa, no dato auditado."),

 # ── Semáforos ───────────────────────────────────────────────────────────
 ("Semáforo Correctivo",
  'SWITCH (\n    TRUE (),\n    [% Órdenes Correctivas] <= 0.30, "#12805C",\n    [% Órdenes Correctivas] <= 0.45, "#B54708",\n    "#B42318"\n)',
  "08 · Semáforos", None, "Color para formato condicional. Meta ≤ 30%."),
 ("Semáforo Cumplimiento PM",
  'SWITCH (\n    TRUE (),\n    [Cumplimiento Plan Preventivo] >= 0.90, "#12805C",\n    [Cumplimiento Plan Preventivo] >= 0.80, "#B54708",\n    "#B42318"\n)',
  "08 · Semáforos", None, "Color para formato condicional. Meta ≥ 90%."),
 ("Semáforo Disponibilidad",
  'SWITCH (\n    TRUE (),\n    [Disponibilidad Operacional] >= 0.92, "#12805C",\n    [Disponibilidad Operacional] >= 0.88, "#B54708",\n    "#B42318"\n)',
  "08 · Semáforos", None, "Color para formato condicional. Meta ≥ 92%."),
 ("Semáforo Calidad de Datos",
  'SWITCH (\n    TRUE (),\n    [Índice de Calidad de Datos] >= 0.95, "#12805C",\n    [Índice de Calidad de Datos] >= 0.85, "#B54708",\n    "#B42318"\n)',
  "08 · Semáforos", None, "Color para formato condicional. Meta ≥ 95%."),
 ("Semáforo Backlog",
  'SWITCH (\n    TRUE (),\n    [Backlog Semanas] >= 2 && [Backlog Semanas] <= 4, "#12805C",\n    [Backlog Semanas] <= 6, "#B54708",\n    "#B42318"\n)',
  "08 · Semáforos", None, "Color para formato condicional. Rango sano 2 a 4 semanas."),
]

def ind(text, n=1):
    pad = "\t" * n
    return "\n".join(pad + l if l.strip() else l for l in text.split("\n"))

def tabla_tmdl(nombre, grupo, desc, cols, m):
    out = [f"/// {desc}", f"table {nombre}", f"\tlineageTag: {lt('t.'+nombre)}", ""]
    if nombre == "DimFecha":
        out.insert(3, "\tdataCategory: Time")
    for c, t, s, cd in cols:
        out += [f"\t/// {cd}", f"\tcolumn {c}", f"\t\tdataType: {t}"]
        if nombre == "DimFecha" and c == "Fecha":
            out.append("\t\tisKey")
        if t == DAT:
            out.append('\t\tformatString: yyyy-mm-dd')
        out += [f"\t\tlineageTag: {lt('c.'+nombre+'.'+c)}",
                f"\t\tsummarizeBy: {s}", f"\t\tsourceColumn: {c}", "",
                "\t\tannotation SummarizationSetBy = Automatic", ""]
        if nombre == "DimFecha" and c == "NombreMes":
            out.insert(len(out) - 2, "\t\tsortByColumn: OrdenAnioMes")
    out += [f"\tpartition {nombre} = m", "\t\tmode: import", "\t\tsource =", ind(m, 4), "",
            f"\tqueryGroup: '{grupo}'", "",
            "\tannotation PBI_ResultType = Table", ""]
    return "\n".join(out)

def medidas_tmdl():
    out = ["/// Tabla contenedora de la capa semántica. Las medidas se agrupan por pilar",
           "/// fundamental para que el modelo sea navegable por un analista que llega nuevo.",
           "table '_Medidas'", f"\tlineageTag: {lt('t._Medidas')}", ""]
    for nombre, dax, folder, fmt, d in M:
        out += [f"\t/// {d}", f"\tmeasure '{nombre}' = ", ind(dax, 3)]
        if fmt:
            out.append(f"\t\tformatString: {fmt}")
        out += [f"\t\tlineageTag: {lt('m.'+nombre)}", f"\t\tdisplayFolder: {folder}", ""]
    out += ["\tcolumn Marcador", "\t\tisHidden", "\t\tformatString: 0", f"\t\tlineageTag: {lt('c._Medidas.Marcador')}",
            "\t\tsummarizeBy: sum", "\t\tsourceColumn: [Marcador]", "\t\tisNameInferred", "",
            "\t\tannotation SummarizationSetBy = Automatic", "",
            "\tpartition '_Medidas' = calculated", "\t\tmode: import",
            '\t\tsource = SELECTCOLUMNS ( { 0 }, "Marcador", [Value] )', "",
            "\tannotation PBI_Id = medidas", ""]
    return "\n".join(out)

# ---- relaciones ---------------------------------------------------------
REL = [
 ("DimFecha","Fecha","FactOrdenesMtto","Fecha"),      ("DimFecha","Fecha","FactAvisosMtto","Fecha"),
 ("DimFecha","Fecha","FactPlanesMtto","Fecha"),       ("DimFecha","Fecha","FactMaterialesMtto","Fecha"),
 ("DimFecha","Fecha","FactProduccion","Fecha"),
 ("DimEquipo","Equipo","FactOrdenesMtto","Equipo"),   ("DimEquipo","Equipo","FactAvisosMtto","Equipo"),
 ("DimEquipo","Equipo","FactPlanesMtto","Equipo"),
 ("DimMaterial","Material","FactMaterialesMtto","Material"),
 ("DimTipoOrden","ClaseOrden","FactOrdenesMtto","ClaseOrden"),
 ("DimArea","Area","FactOrdenesMtto","Area"),         ("DimArea","Area","FactAvisosMtto","Area"),
 ("DimArea","Area","FactProduccion","Area"),          ("DimArea","Area","FactMaterialesMtto","Area"),
 ("DimLinea","Linea","FactOrdenesMtto","Linea"),      ("DimLinea","Linea","FactAvisosMtto","Linea"),
 ("DimLinea","Linea","FactProduccion","Linea"),
 ("DimCriticidad","Criticidad","FactOrdenesMtto","Criticidad"),
 ("DimCriticidad","Criticidad","FactAvisosMtto","Criticidad"),
 ("DimGrupoPlanificador","GrupoPlanificador","FactOrdenesMtto","GrupoPlanificador"),
]

def relaciones_tmdl():
    out = []
    for dt, dc, ft, fc in REL:
        rid = lt(f"r.{dt}.{dc}.{ft}.{fc}")
        out += [f"relationship {rid}", f"\tfromColumn: {ft}.{fc}", f"\ttoColumn: {dt}.{dc}", ""]
    return "\n".join(out)

# ---- escritura del modelo ----------------------------------------------
wj(f"{SM}/definition.pbism", {
  "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/semanticModel/definitionProperties/1.0.0/schema.json",
  "version": "4.2",
  "settings": {}})
w(f"{SM}/definition/database.tmdl", "database\n\tcompatibilityLevel: 1567\n")
w(f"{SM}/definition/expressions.tmdl", EXPR)
w(f"{SM}/definition/relationships.tmdl", relaciones_tmdl())

for nombre, grupo, desc, cols, m in TABLAS:
    w(f"{SM}/definition/tables/{nombre}.tmdl", tabla_tmdl(nombre, grupo, desc, cols, m))
w(f"{SM}/definition/tables/_Medidas.tmdl", medidas_tmdl())

modelo = ["model Model", "\tculture: es-CL", "\tdefaultPowerBIDataSourceVersion: powerBI_V3",
          "\tdiscourageImplicitMeasures", "\tsourceQueryCulture: es-CL", "",
          "\tdataAccessOptions", "\t\tlegacyRedirects", "\t\treturnErrorValuesAsNull", "",
          "\tannotation PBI_QueryOrder = " + json.dumps(
              ["RutaDatos", "MargenHora", "CapacidadSemanal"] + [t[0] for t in TABLAS], ensure_ascii=False), ""]
modelo += [f"ref table {t[0]}" for t in TABLAS]
modelo += ["ref table '_Medidas'", ""]
w(f"{SM}/definition/model.tmdl", "\n".join(modelo))

wj(f"{SM}/diagramLayout.json", {
  "version": "1.1.0",
  "diagrams": [{
    "ordinal": 0, "scrollPosition": {"x": 0, "y": 0}, "nodeIndex": 0, "zoomValue": 80,
    "name": "Modelo en estrella", "hideKeyFieldsWhenCollapsed": False, "pinKeyFieldsToTop": False,
    "nodes": [{"location": {"x": x, "y": y}, "nodeIndex": t, "size": {"height": 220, "width": 220},
               "zIndex": i, "nodeLineageTag": lt("t." + t)}
      for i, (t, x, y) in enumerate([
        ("DimFecha", 40, 40), ("DimEquipo", 40, 300), ("DimArea", 40, 560),
        ("DimLinea", 300, 620), ("DimCriticidad", 560, 660), ("DimGrupoPlanificador", 820, 620),
        ("DimTipoOrden", 1080, 560), ("DimMaterial", 1080, 300),
        ("FactOrdenesMtto", 560, 300), ("FactAvisosMtto", 820, 60), ("FactProduccion", 300, 60),
        ("FactPlanesMtto", 820, 300), ("FactMaterialesMtto", 1080, 60), ("FactKaizen", 560, 40),
        ("_Medidas", 300, 300)])]}]})

wj(f"{SM}/.platform", {
  "$schema": "https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json",
  "metadata": {"type": "SemanticModel", "displayName": NAME},
  "config": {"version": "2.0", "logicalId": lt("logical.semanticmodel")}})

# ════════════════════════════════════════════════════ 2 · INFORME PBIR ═══
SCH = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition"
W, H = 1280, 720

def fld(spec):
    """('M','Medida') o ('C','Tabla','Columna') → proyección PBIR."""
    if spec[0] == "M":
        t, p = "_Medidas", spec[1]
        return {"field": {"Measure": {"Expression": {"SourceRef": {"Entity": t}}, "Property": p}},
                "queryRef": f"{t}.{p}", "nativeQueryRef": p}
    t, p = spec[1], spec[2]
    return {"field": {"Column": {"Expression": {"SourceRef": {"Entity": t}}, "Property": p}},
            "queryRef": f"{t}.{p}", "nativeQueryRef": p}

def titulo(txt):
    return {"title": [{"properties": {
        "show":  {"expr": {"Literal": {"Value": "true"}}},
        "text":  {"expr": {"Literal": {"Value": f"'{txt}'"}}},
        "alignment": {"expr": {"Literal": {"Value": "'left'"}}}}}]}

VIS = []
def vis(page, name, vtype, x, y, wd, ht, roles, title=None, objects=None, z=None):
    v = {"$schema": f"{SCH}/visualContainer/1.4.0/schema.json",
         "name": name,
         "position": {"x": x, "y": y, "z": z if z is not None else len(VIS),
                      "width": wd, "height": ht, "tabOrder": len(VIS) * 10},
         "visual": {"visualType": vtype,
                    "query": {"queryState": {r: {"projections": [fld(f) for f in fs]}
                                             for r, fs in roles.items() if fs}},
                    "drillFilterOtherVisuals": True}}
    if objects: v["visual"]["objects"] = objects
    if title:   v["visual"]["visualContainerObjects"] = titulo(title)
    VIS.append((page, name, v)); return v

def texto(page, name, x, y, wd, ht, runs):
    v = {"$schema": f"{SCH}/visualContainer/1.4.0/schema.json",
         "name": name,
         "position": {"x": x, "y": y, "z": len(VIS), "width": wd, "height": ht, "tabOrder": len(VIS) * 10},
         "visual": {"visualType": "textbox",
                    "objects": {"general": [{"properties": {"paragraphs": [
                        {"textRuns": [{"value": t, "textStyle": s} for t, s in p]} for p in runs]}}]},
                    "drillFilterOtherVisuals": True}}
    VIS.append((page, name, v)); return v

TS_H  = {"fontSize": "11pt", "fontWeight": "bold", "color": PAL["orange"], "fontFamily": "Segoe UI"}
TS_B  = {"fontSize": "10pt", "color": PAL["navy"], "fontWeight": "bold", "fontFamily": "Segoe UI"}
TS_P  = {"fontSize": "10pt", "color": PAL["ink"], "fontFamily": "Segoe UI"}
TS_D  = {"fontSize": "10pt", "color": PAL["red"], "fontWeight": "bold", "fontFamily": "Segoe UI"}

def narrativa(page, name, titulo_, que, corr, riesgo, decision, y=560, ht=142):
    texto(page, name, 16, y, W - 32, ht, [
        [(titulo_.upper(), TS_H)],
        [("Qué dice el dato · ", TS_B), (que, TS_P)],
        [("Correlación · ", TS_B), (corr, TS_P)],
        [("Riesgo si no se actúa · ", TS_B), (riesgo, TS_P)],
        [("Decisión recomendada: ", TS_D), (decision, TS_P)]])

def kpi_fila(page, medidas, y=88, ht=96, pref="k"):
    n = len(medidas); wd = (W - 32 - (n - 1) * 10) // n
    for i, (m, tt) in enumerate(medidas):
        vis(page, f"{page}{pref}{i}", "card", 16 + i * (wd + 10), y, wd, ht,
            {"Values": [("M", m)]}, tt)

def slicers(page):
    campos = [("DimFecha", "Anio"), ("DimArea", "Area"), ("DimLinea", "Linea"),
              ("DimCriticidad", "Criticidad"), ("DimTipoOrden", "TipoMantenimiento")]
    wd = (W - 32 - 4 * 8) // 5
    for i, (t, c) in enumerate(campos):
        vis(page, f"{page}s{i}", "slicer", 16 + i * (wd + 8), 44, wd, 38,
            {"Values": [("C", t, c)]}, None,
            {"general": [{"properties": {"orientation": {"expr": {"Literal": {"Value": "1D"}}}}}]})

def encabezado(page, num, titulo_, sub):
    texto(page, f"{page}h", 16, 8, W - 32, 34,
          [[(f"{num} · {titulo_}", {"fontSize": "15pt", "fontWeight": "bold",
                                    "color": PAL["navy"], "fontFamily": "Segoe UI"}),
            ("     " + sub, {"fontSize": "10pt", "color": PAL["grey"], "fontFamily": "Segoe UI"})]])

MES = ("C", "DimFecha", "MesCorto")
PAGINAS = []
def pagina(pid, num, nombre, sub):
    PAGINAS.append((pid, f"{num} · {nombre}"))
    encabezado(pid, num, nombre, sub); slicers(pid)

# ─────────────────────────────────────────────── P01 Resumen ejecutivo ───
p = "p01"; pagina(p, "01", "Resumen Ejecutivo", "Salud global de la gestión en una vista")
kpi_fila(p, [("% Órdenes Correctivas", "% Correctivas · meta ≤ 30%"),
             ("Cumplimiento Plan Preventivo", "Cumplimiento PM · meta ≥ 90%"),
             ("Disponibilidad Operacional", "Disponibilidad · meta ≥ 92%"),
             ("Índice de Calidad de Datos", "Calidad de datos · meta ≥ 95%")])
kpi_fila(p, [("MTTR (h)", "MTTR · horas"), ("MTBF (h)", "MTBF · horas"),
             ("Backlog Semanas", "Backlog · semanas"), ("Costo Total M$", "Costo total · M$")],
         y=190, pref="j")
vis(p, "p01v1", "lineChart", 16, 296, 420, 250,
    {"Category": [MES], "Y": [("M", "Costo Total M$"), ("M", "Costo Plan")]},
    "Tendencia de costo · real vs. plan   |   KOB1 · S_ALR_87013558")
vis(p, "p01v2", "lineChart", 444, 296, 400, 250,
    {"Category": [MES], "Y": [("M", "% Órdenes Preventivas"), ("M", "% Órdenes Correctivas")]},
    "Evolución del mix   |   IW39")
vis(p, "p01v3", "clusteredBarChart", 852, 296, 412, 250,
    {"Category": [("C", "DimEquipo", "Denominacion")], "Y": [("M", "Costo Total M$")]},
    "Top equipos por costo   |   KOB1 × IH08")
narrativa(p, "p01n", "Lectura ejecutiva del período",
  "El mix correctivo, la disponibilidad y el cumplimiento preventivo definen la salud del período; los cuatro KPI de cabecera se leen siempre juntos.",
  "Los equipos que encabezan el ranking de costo son los mismos que lideran fallas: la pérdida está concentrada, no distribuida.",
  "Si el preventivo cae bajo meta, el correctivo recupera terreno en dos meses y el backlog supera la capacidad disponible.",
  "Priorizar los planes vencidos de los dos equipos con mayor frecuencia de falla y abrir un A3 de Mejora Enfocada sobre averías.")

# ──────────────────────────────────────────────── P02 Gestión de órdenes ─
p = "p02"; pagina(p, "02", "Gestión de Órdenes", "Controlar el flujo y la disciplina de cierre")
kpi_fila(p, [("Órdenes Totales", "Órdenes totales"), ("Órdenes Abiertas", "Órdenes abiertas"),
             ("Tiempo Promedio de Cierre (d)", "Cierre promedio · días"),
             ("% Órdenes Retrasadas", "% retrasadas · meta ≤ 10%")])
vis(p, "p02v1", "clusteredColumnChart", 16, 196, 620, 250,
    {"Category": [MES], "Y": [("M", "Órdenes Cerradas"), ("M", "Órdenes Abiertas")]},
    "Órdenes por mes · abiertas vs. cerradas   |   IW39")
vis(p, "p02v2", "clusteredColumnChart", 644, 196, 620, 250,
    {"Category": [("C", "DimTipoOrden", "ClaseOrden")], "Y": [("M", "Órdenes Totales")]},
    "Distribución por clase de orden   |   IW39")
vis(p, "p02v3", "tableEx", 16, 454, 1248, 100,
    {"Values": [("C", "DimArea", "Area"), ("C", "DimGrupoPlanificador", "GrupoPlanificador"),
                ("M", "Órdenes Totales"), ("M", "% Órdenes Retrasadas"), ("M", "SLA Cierre 7 días")]},
    "Matriz área × grupo planificador   |   IW39")
narrativa(p, "p02n", "Disciplina de ejecución",
  "El ciclo aviso → orden → cierre pierde registros en cada paso; solo una parte de las órdenes termina con HH confirmadas.",
  "Las semanas con menor cumplimiento de programación coinciden con los picos de emergencia: cada trabajo no planificado desplaza trabajo programado.",
  "Un backlog que envejece sin priorizar genera trabajo repetido y pérdida de trazabilidad, base de todo el análisis de confiabilidad.",
  "Congelar la programación semanal con 48 h de anticipación y limitar la inserción de trabajo no planificado a un cupo del 15% de la capacidad.",
  y=562, ht=140)

# ────────────────────────────────────────────── P03 Preventivo vs corr. ──
p = "p03"; pagina(p, "03", "Preventivo vs. Correctivo", "Evaluar la madurez de la planificación")
kpi_fila(p, [("% Órdenes Preventivas", "% Preventivas · meta ≥ 70%"),
             ("Cumplimiento Plan Preventivo", "Cumplimiento de planes"),
             ("Planes Vencidos", "Planes vencidos"),
             ("Ratio Preventivo / Correctivo", "Ratio prev./corr. · meta ≥ 2,3")])
vis(p, "p03v1", "donutChart", 16, 196, 400, 250,
    {"Category": [("C", "DimTipoOrden", "TipoMantenimiento")], "Y": [("M", "Órdenes Totales")]},
    "Mix por tipo de mantenimiento   |   IW39")
vis(p, "p03v2", "lineChart", 424, 196, 420, 250,
    {"Category": [MES], "Y": [("M", "Cumplimiento Plan Preventivo")]},
    "Cumplimiento del plan preventivo   |   IP24 / IP30")
vis(p, "p03v3", "clusteredBarChart", 852, 196, 412, 250,
    {"Category": [("C", "FactPlanesMtto", "Plan")], "Y": [("M", "Planes Vencidos")]},
    "Planes con posiciones vencidas   |   IP15 · IP24")
vis(p, "p03v4", "tableEx", 16, 454, 1248, 100,
    {"Values": [("C", "DimEquipo", "Denominacion"), ("C", "DimEquipo", "Criticidad"),
                ("M", "Correctivas"), ("M", "Planes Vencidos"), ("M", "Costo Total M$")]},
    "Correctivos recurrentes y sus planes vencidos   |   IW29 × IP24 × IH08")
narrativa(p, "p03n", "Madurez de la planificación",
  "El cumplimiento de planes y el mix preventivo miden lo mismo desde dos ángulos: cuánta prevención se ejecuta realmente.",
  "Los equipos con correctivos recurrentes son los que acumulan planes vencidos: la reincidencia no es aleatoria, es consecuencia del plan no ejecutado.",
  "El ciclo plan vencido → falla → emergencia consume la capacidad que permitiría ejecutar el propio plan; se refuerza solo.",
  "Ejecutar primero los planes vencidos de equipos criticidad A aunque implique postergar preventivo de criticidad C, y abrir RCA formal en los equipos recurrentes.",
  y=562, ht=140)

# ──────────────────────────────────────────────────── P04 Confiabilidad ──
p = "p04"; pagina(p, "04", "Confiabilidad", "Identificar malos actores y priorizar mejora")
kpi_fila(p, [("Disponibilidad Operacional", "Disponibilidad · meta ≥ 92%"),
             ("MTTR (h)", "MTTR · horas"), ("MTBF (h)", "MTBF · horas"),
             ("Horas de Detención", "Horas de detención")])
vis(p, "p04v1", "clusteredColumnChart", 16, 196, 620, 250,
    {"Category": [("C", "DimEquipo", "Denominacion")],
     "Y": [("M", "MTTR (h)"), ("M", "N.º Averías")]},
    "MTTR y frecuencia por equipo   |   IW29 × IH08")
vis(p, "p04v2", "clusteredBarChart", 644, 196, 620, 250,
    {"Category": [("C", "FactAvisosMtto", "Causa")], "Y": [("M", "N.º Avisos")]},
    "Pareto de causas de falla   |   IW28 · código de daño")
vis(p, "p04v3", "tableEx", 16, 454, 1248, 100,
    {"Values": [("C", "DimEquipo", "Denominacion"), ("C", "DimEquipo", "Criticidad"),
                ("M", "N.º Averías"), ("M", "MTBF (h)"), ("M", "MTTR (h)"), ("M", "Costo Total M$")]},
    "Ranking de malos actores   |   IW29 × KOB1 × IH08")
narrativa(p, "p04n", "Dónde está la confiabilidad perdida",
  "El MTTR proviene de la duración de parada del aviso, no de las horas hombre de la orden: son horas de reloj, no esfuerzo.",
  "MTBF bajo más MTTR alto más criticidad A concentra la mayor pérdida de disponibilidad, y coincide con el mayor consumo de repuestos críticos.",
  "Cada falla adicional en esos activos cuesta más en producción perdida que la reparación misma, y se extiende si el repuesto no está en bodega.",
  "Evaluar overhaul del peor actor contra su costo correctivo acumulado y asegurar el kit de repuestos críticos asociado.",
  y=562, ht=140)

# ────────────────────────────────────────────────────────── P05 Costos ───
p = "p05"; pagina(p, "05", "Costos", "Controlar el gasto y su varianza")
kpi_fila(p, [("Costo Total M$", "Costo total · M$"), ("% Costo Preventivo", "% preventivo · meta ≥ 60%"),
             ("% Varianza Costo", "Varianza vs. plan"), ("Costo por Tonelada", "Costo por tonelada")])
vis(p, "p05v1", "clusteredColumnChart", 16, 196, 620, 250,
    {"Category": [MES], "Y": [("M", "Costo Total M$"), ("M", "Costo Plan")]},
    "Costo real vs. plan por mes   |   KOB1 · S_ALR_87013558")
vis(p, "p05v2", "stackedColumnChart", 644, 196, 620, 250,
    {"Category": [("C", "DimArea", "Area")], "Y": [("M", "Costo Total M$")],
     "Series": [("C", "DimTipoOrden", "TipoMantenimiento")]},
    "Costo por área y tipo de mantenimiento   |   KOB1 × IW39")
vis(p, "p05v3", "tableEx", 16, 454, 1248, 100,
    {"Values": [("C", "DimEquipo", "Denominacion"), ("M", "Costo Plan"), ("M", "Costo Total"),
                ("M", "Varianza Costo"), ("M", "% Varianza Costo")]},
    "Varianza por equipo   |   IW39 × KOB1")
narrativa(p, "p05n", "El costo no está fuera de control, está mal distribuido",
  "El costo agregado puede cuadrar contra el presupuesto mientras el % de costo preventivo queda bajo meta.",
  "Las órdenes con mayor desviación son correctivas; las preventivas cierran cerca del plan. El trabajo planificado es predecible, el reactivo no.",
  "Un presupuesto que cuadra por menor ejecución preventiva no es ahorro: es gasto diferido que reaparece como correctivo con prima de 3 a 5 veces.",
  "Proteger el presupuesto preventivo del recorte trimestral y reportar la varianza separada por tipo de mantenimiento, nunca en un único agregado.",
  y=562, ht=140)

# ──────────────────────────────────────────────── P06 Backlog y capacidad ─
p = "p06"; pagina(p, "06", "Backlog y Capacidad", "Equilibrar carga y capacidad")
kpi_fila(p, [("Backlog HH", "Backlog · HH"), ("Backlog Semanas", "Backlog · semanas (meta 2 a 4)"),
             ("Órdenes Envejecidas", "Órdenes > 30 días"),
             ("HH Bloqueadas por Repuesto", "HH bloqueadas por repuesto")])
vis(p, "p06v1", "clusteredColumnChart", 16, 196, 620, 250,
    {"Category": [("C", "DimGrupoPlanificador", "GrupoPlanificador")],
     "Y": [("M", "Backlog HH"), ("M", "Capacidad Semanal HH")]},
    "Backlog vs. capacidad por especialidad   |   IW47 × CR03")
vis(p, "p06v2", "lineChart", 644, 196, 620, 250,
    {"Category": [MES], "Y": [("M", "HH Reales"), ("M", "HH Planificadas")]},
    "Carga ejecutada vs. planificada   |   IW47 · IW39")
vis(p, "p06v3", "tableEx", 16, 454, 1248, 100,
    {"Values": [("C", "FactOrdenesMtto", "Prioridad"), ("C", "FactOrdenesMtto", "MotivoDetencion"),
                ("M", "Órdenes Abiertas"), ("M", "Backlog HH"), ("M", "Órdenes Envejecidas")]},
    "Backlog por prioridad y motivo de detención   |   IW39")
narrativa(p, "p06n", "El backlog global engaña",
  "Un backlog total dentro del rango sano puede esconder una especialidad saturada muy por sobre su capacidad.",
  "Las órdenes detenidas por espera de material corresponden a los repuestos bajo mínimo: el cuello de botella es de abastecimiento, no de dotación.",
  "El trabajo de más de 30 días suele rehacerse o cerrarse administrativamente sin ejecución, lo que contamina el histórico de confiabilidad.",
  "Separar el backlog en tres colas — ejecutable, en espera de repuesto y en espera de parada — con responsable distinto para cada una.",
  y=562, ht=140)

# ────────────────────────────────────────── P07 Materiales y repuestos ───
p = "p07"; pagina(p, "07", "Materiales y Repuestos", "Asegurar disponibilidad de repuestos críticos")
kpi_fila(p, [("Consumo de Repuestos", "Consumo · k$"), ("Lead Time Promedio", "Lead time · días"),
             ("Repuestos Críticos Bajo Stock", "Críticos bajo stock"),
             ("HH Bloqueadas por Repuesto", "HH bloqueadas")])
vis(p, "p07v1", "clusteredBarChart", 16, 196, 620, 250,
    {"Category": [("C", "DimMaterial", "Descripcion")], "Y": [("M", "Consumo de Repuestos")]},
    "Top repuestos por consumo   |   MB51 × MM03")
vis(p, "p07v2", "lineChart", 644, 196, 620, 250,
    {"Category": [MES], "Y": [("M", "Consumo de Repuestos")]},
    "Consumo mensual de repuestos   |   MB51")
vis(p, "p07v3", "tableEx", 16, 454, 1248, 100,
    {"Values": [("C", "DimMaterial", "Material"), ("C", "DimMaterial", "Descripcion"),
                ("C", "DimMaterial", "ABC"), ("C", "DimMaterial", "StockActual"),
                ("C", "DimMaterial", "StockMinimo"), ("C", "DimMaterial", "LeadTimeDias")]},
    "Materiales críticos: stock contra mínimo   |   MB52 · MM03")
narrativa(p, "p07n", "El repuesto crítico decide la disponibilidad",
  "Los repuestos bajo mínimo y el lead time de aprovisionamiento definen cuánto puede durar una parada.",
  "Los materiales quebrados corresponden a los equipos de criticidad A con peor MTBF: el riesgo de stock está justo donde la falla es más probable y más cara.",
  "Con lead time sobre 21 días y MTBF bajo en los activos críticos, una parada extendida por espera de repuesto es cuestión de tiempo.",
  "Definir stock de seguridad con la fórmula consumo × lead time + margen para materiales de equipos criticidad A, y contrato marco para las referencias quebradas.",
  y=562, ht=140)

# ────────────────────────────────────────────────── P08 Calidad de datos ─
p = "p08"; pagina(p, "08", "Calidad de Datos SAP", "Sanear el dato como condición habilitante")
kpi_fila(p, [("Índice de Calidad de Datos", "Índice · meta ≥ 95%"),
             ("Órdenes sin Aviso", "Órdenes sin aviso"), ("Cerradas sin HH", "Cerradas sin HH"),
             ("Trazabilidad Aviso → Orden", "Trazabilidad aviso → orden")])
vis(p, "p08v1", "lineChart", 16, 196, 620, 250,
    {"Category": [MES], "Y": [("M", "Índice de Calidad de Datos")]},
    "Evolución del índice de calidad   |   IW39 · IW29")
vis(p, "p08v2", "clusteredColumnChart", 644, 196, 620, 250,
    {"Category": [("C", "DimGrupoPlanificador", "GrupoPlanificador")],
     "Y": [("M", "Índice de Calidad de Datos")]},
    "Calidad por grupo planificador   |   IW39")
vis(p, "p08v3", "tableEx", 16, 454, 1248, 100,
    {"Values": [("C", "DimArea", "Area"), ("M", "Órdenes sin Equipo"), ("M", "Órdenes sin Aviso"),
                ("M", "Cerradas sin HH"), ("M", "Costo sin Cierre"), ("M", "Preventivas Vencidas")]},
    "Anomalías por área   |   IW39 · IW29 · IW47")
narrativa(p, "p08n", "Sin dato confiable, ningún KPI es una decisión",
  "El índice mide cinco controles sobre cada orden. Bajo 95% la página se convierte en condición habilitante del resto del tablero.",
  "Las órdenes cerradas sin HH deprimen artificialmente el MTTR y el backlog: los dos KPI que las páginas 04 y 06 usan para concluir que la operación mejora.",
  "Decidir un overhaul o una dotación sobre KPI distorsionados compromete inversión con evidencia defectuosa.",
  "Bloquear el cierre técnico en SAP cuando falte equipo, aviso de origen u HH confirmadas, y revisar la calidad por grupo planificador antes que cualquier otro indicador.",
  y=562, ht=140)

# ───────────────────────────────────────────── P09 TPM y fundacionales ───
p = "p09"; pagina(p, "09", "TPM y 5 Fundacionales", "Medir madurez y orientar la mejora cultural")
kpi_fila(p, [("Madurez Promedio", "Madurez promedio · meta 4,0"),
             ("Score F2 Planificación", "F2 · Planificación"),
             ("Score F5 Confiabilidad", "F5 · Confiabilidad"),
             ("Índice de Calidad de Datos", "Transversal · calidad de datos")])
vis(p, "p09v1", "clusteredColumnChart", 16, 196, 620, 250,
    {"Category": [("C", "DimArea", "Area")],
     "Y": [("M", "Score F1 Activos"), ("M", "Score F2 Planificación"), ("M", "Score F3 Ejecución"),
           ("M", "Score F4 Costos"), ("M", "Score F5 Confiabilidad")]},
    "Score por pilar y área   |   modelo de score sobre dato SAP")
vis(p, "p09v2", "lineChart", 644, 196, 620, 250,
    {"Category": [MES], "Y": [("M", "Madurez Promedio")]},
    "Evolución de la madurez   |   assessment + SAP")
vis(p, "p09v3", "tableEx", 16, 454, 1248, 100,
    {"Values": [("C", "DimArea", "Area"), ("M", "Score F1 Activos"), ("M", "Score F2 Planificación"),
                ("M", "Score F3 Ejecución"), ("M", "Score F4 Costos"), ("M", "Score F5 Confiabilidad"),
                ("M", "Madurez Promedio")]},
    "Matriz de madurez por área   |   modelo de score")
narrativa(p, "p09n", "La madurez explica por qué los KPI se estancan",
  "Los cinco scores se calculan desde el propio dato SAP, no desde una encuesta: miden práctica instalada, no percepción.",
  "El pilar más débil gobierna directamente el KPI que no mejora: el cumplimiento preventivo depende de F2 y la disponibilidad de F5.",
  "Perseguir la meta numérica sin instalar la rutina produce mejoras que se revierten al trimestre siguiente.",
  "Priorizar las acciones de los dos pilares más débiles por sobre cualquier otra iniciativa del trimestre, con evidencia de cierre verificable.",
  y=562, ht=140)

# ───────────────────────────────────────────── P10 Drillthrough equipo ───
p = "p10"; pagina(p, "10", "Detalle de Equipo", "Diagnóstico 360° de un activo")
vis(p, "p10s", "slicer", 16, 88, 300, 96, {"Values": [("C", "DimEquipo", "Denominacion")]},
    "Seleccionar equipo   |   IH08")
kpi_fila(p, [("MTTR (h)", "MTTR del activo"), ("MTBF (h)", "MTBF del activo"),
             ("Costo Total M$", "Costo acumulado · M$"), ("Planes Vencidos", "Planes vencidos")],
         y=88, ht=96, pref="k")
for i, (_, n, v) in enumerate(VIS):
    if n.startswith("p10k"):
        v["position"]["x"] = 324 + (int(n[-1])) * 240
        v["position"]["width"] = 232
vis(p, "p10v1", "lineChart", 16, 196, 620, 250,
    {"Category": [MES], "Y": [("M", "N.º Averías"), ("M", "Costo Total M$")]},
    "Historial de fallas y costo del activo   |   IW29 · KOB1")
vis(p, "p10v2", "tableEx", 644, 196, 620, 250,
    {"Values": [("C", "FactPlanesMtto", "Estrategia"), ("C", "FactPlanesMtto", "Ciclo"),
                ("M", "Posiciones de Plan"), ("M", "Planes Vencidos")]},
    "Planes preventivos asociados   |   IP24 · IP15")
vis(p, "p10v3", "tableEx", 16, 454, 1248, 100,
    {"Values": [("C", "FactAvisosMtto", "Causa"), ("C", "FactAvisosMtto", "CategoriaPerdida"),
                ("M", "N.º Avisos"), ("M", "Horas de Detención"), ("M", "Pérdida por Averías")]},
    "Modos de falla del activo   |   IW28 · IW29")
narrativa(p, "p10n", "Diagnóstico del activo",
  "MTTR, MTBF y costo acumulado describen al activo; los planes vencidos explican por qué llegó a ese estado.",
  "Cuando un equipo acumula avisos mientras sus planes están vencidos, la correlación entre prevención no ejecutada y falla repetida es directa.",
  "Intervenir el síntoma sin corregir la causa repite el gasto y mantiene el activo entre los principales contribuyentes a la pérdida de planta.",
  "Ejecutar los planes vencidos con medición de condición antes de cualquier nuevo reemplazo, y elevar el hallazgo a la cartera de Mejora Enfocada.",
  y=562, ht=140)

# ────────────────────────────────────────────────── P11 Mejora Enfocada ──
p = "p11"; pagina(p, "11", "Mejora Enfocada", "Convertir pérdidas en iniciativas con ahorro verificable")
kpi_fila(p, [("Pérdida Total", "Pérdida capturada · M$"), ("Kaizen Activos", "A3 activos"),
             ("Ahorro Validado", "Ahorro validado · M$"), ("% Pérdidas Atacadas", "% pérdidas atacadas")])
vis(p, "p11v1", "clusteredBarChart", 16, 196, 620, 250,
    {"Category": [("C", "FactAvisosMtto", "CategoriaPerdida")], "Y": [("M", "Pérdida Total")]},
    "Árbol de pérdidas · las 6 grandes pérdidas   |   IW29 · COOIS · KOB1")
vis(p, "p11v2", "lineChart", 644, 196, 620, 250,
    {"Category": [MES], "Y": [("M", "Pérdida Total"), ("M", "Pérdida por Averías")]},
    "Evolución de la pérdida   |   IW29")
vis(p, "p11v3", "tableEx", 16, 454, 1248, 100,
    {"Values": [("C", "FactKaizen", "A3"), ("C", "FactKaizen", "PerdidaAtacada"),
                ("C", "FactKaizen", "FasePDCA"), ("C", "FactKaizen", "KPI"),
                ("C", "FactKaizen", "Antes"), ("C", "FactKaizen", "Despues"),
                ("M", "Ahorro Validado")]},
    "Cartera de kaizen con efecto medido   |   registro A3 validado en CO")
narrativa(p, "p11n", "La mejora se valida con dinero y con estándar, no con intención",
  "La pérdida se monetiza como horas de detención por el margen de contribución por hora, parámetro de Controlling editable en el modelo.",
  "Los A3 de mayor ahorro atacan la categoría que encabeza el árbol de pérdidas y corresponde a los malos actores del ranking de confiabilidad.",
  "Las categorías sin iniciativa asignada marcan el techo del ahorro cuando los A3 actuales cierren.",
  "Abrir A3 sobre las categorías sin cobertura y condicionar el cierre de todo A3 a la actualización del plan preventivo correspondiente.",
  y=562, ht=140)

# ───────────────────────────────────────────────────── P12 Benchmark ─────
p = "p12"; pagina(p, "12", "Benchmark Externo", "Distancia al cuartil superior y valor de la brecha")
kpi_fila(p, [("% Trabajo Planificado", "% planificado · cuartil sup. ≥ 85%"),
             ("% Órdenes Correctivas", "% reactivo · cuartil sup. ≤ 20%"),
             ("KPI Bajo Referencia", "KPI bajo referencia"),
             ("Valor de la Brecha M$", "Valor de la brecha · M$/año")])
vis(p, "p12v1", "clusteredBarChart", 16, 196, 620, 250,
    {"Category": [("C", "DimArea", "Area")],
     "Y": [("M", "% Trabajo Planificado"), ("M", "Disponibilidad Operacional"),
           ("M", "Cumplimiento Plan Preventivo")]},
    "Desempeño por área contra referencia externa   |   todas las fuentes")
vis(p, "p12v2", "lineChart", 644, 196, 620, 250,
    {"Category": [MES], "Y": [("M", "% Trabajo Planificado"), ("M", "Disponibilidad Operacional")]},
    "Trayectoria hacia el cuartil superior   |   IW39 · COOIS")
vis(p, "p12v3", "tableEx", 16, 454, 1248, 100,
    {"Values": [("C", "DimArea", "Area"), ("M", "% Trabajo Planificado"), ("M", "Brecha % Planificado"),
                ("M", "Disponibilidad Operacional"), ("M", "Brecha Disponibilidad"),
                ("M", "OEE Parcial"), ("M", "Valor de la Brecha M$")]},
    "Brecha por área y su valor   |   referencia de industria")
narrativa(p, "p12n", "Cuánto vale llegar al cuartil superior",
  "El % planificado y el % reactivo son el mismo fenómeno medido de dos formas, y ambos dependen del pilar de Planificación.",
  "Los rangos provienen de literatura pública que cita estudios de McKinsey & Company y del marco SMRP: son referencia orientativa, no dato auditado.",
  "La brecha de OEE no es cerrable hoy porque faltan velocidad y calidad de línea. Comprometer esa meta sería comprometer un número que nadie puede verificar.",
  "Comprometer ante Gerencia solo las metas sostenidas por dato disponible y abrir en paralelo el proyecto de captura de velocidad y calidad.",
  y=562, ht=140)

# ---- escritura del informe ---------------------------------------------
wj(f"{RP}/definition.pbir", {
  "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definitionProperties/1.0.0/schema.json",
  "version": "4.0",
  "datasetReference": {"byPath": {"path": f"../{NAME}.SemanticModel"}}})

wj(f"{RP}/definition/report.json", {
  "$schema": f"{SCH}/report/1.0.0/schema.json",
  "themeCollection": {
    "baseTheme": {"name": "CY24SU10", "reportVersionAtImport": "5.55", "type": "SharedResources"},
    "customTheme": {"name": "MPSCorporate", "type": "RegisteredResources"}},
  "layoutOptimization": "None",
  "resourcePackages": [
    {"name": "SharedResources", "type": "SharedResources",
     "items": [{"name": "CY24SU10", "path": "BaseThemes/CY24SU10.json", "type": "BaseTheme"}]},
    {"name": "RegisteredResources", "type": "RegisteredResources",
     "items": [{"name": "MPSCorporate", "path": "MPSCorporate.json", "type": "CustomTheme"}]}],
  "settings": {"useStylableVisualContainerHeader": True,
               "defaultDrillFilterOtherVisuals": True,
               "allowChangeFilterTypes": True,
               "useNewFilterPaneExperience": True}})

wj(f"{RP}/definition/pages/pages.json", {
  "$schema": f"{SCH}/pagesMetadata/1.0.0/schema.json",
  "pageOrder": [p for p, _ in PAGINAS],
  "activePageName": PAGINAS[0][0]})

for pid, disp in PAGINAS:
    wj(f"{RP}/definition/pages/{pid}/page.json", {
      "$schema": f"{SCH}/page/1.0.0/schema.json",
      "name": pid, "displayName": disp, "displayOption": "FitToPage",
      "height": H, "width": W})

for pid, vname, v in VIS:
    wj(f"{RP}/definition/pages/{pid}/visuals/{vname}/visual.json", v)

wj(f"{RP}/StaticResources/RegisteredResources/MPSCorporate.json", TEMA)
BASE = dict(TEMA); BASE["name"] = "CY24SU10"
wj(f"{RP}/StaticResources/SharedResources/BaseThemes/CY24SU10.json", BASE)
wj(f"{RP}/.platform", {
  "$schema": "https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json",
  "metadata": {"type": "Report", "displayName": NAME},
  "config": {"version": "2.0", "logicalId": lt("logical.report")}})

# ---- archivo raíz .pbip -------------------------------------------------
wj(f"{OUT}/{NAME}.pbip", {
  "$schema": "https://developer.microsoft.com/json-schemas/fabric/pbip/pbipProperties/1.0.0/schema.json",
  "version": "1.0",
  "artifacts": [{"report": {"path": f"{NAME}.Report"}}],
  "settings": {"enableAutoRecovery": True}})

w(f"{OUT}/.gitignore", "\n".join([
  "# Artefactos locales de Power BI Desktop",
  "*.pbix", ".pbi/localSettings.json", ".pbi/cache.abf", "**/.pbi/", "*.abf", ""]))

n_tbl = len(TABLAS) + 1
print(f"PBIP generado en ./{OUT}")
print(f"  modelo  : {n_tbl} tablas · {len(M)} medidas · {len(REL)} relaciones")
print(f"  informe : {len(PAGINAS)} páginas · {len(VIS)} visuales")
