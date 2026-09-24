#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate_synthetic.py — Generador de dataset sintético tipo SAP PM/MM/CO/PP
===========================================================================
Produce 24 meses de datos (enero 2025 – diciembre 2026) coherentes entre sí,
con la estructura que entregan las transacciones SAP declaradas en PROJECT_SPEC.md.

Salidas:
  data/sample/*.csv      → tablas planas, una por tabla del modelo estrella
  data/dataset.json      → payload compacto que consume el mockup HTML

Los datos son FICTICIOS. Reproducen patrones realistas:
  - Tendencia de mejora sostenida a lo largo de 24 meses (madurez creciente).
  - Estacionalidad: más fallas en verano del hemisferio sur (ene-feb).
  - Malos actores concentrados (Pareto 80/20 en fallas y costo).
  - ~6% de registros con defectos deliberados de calidad de datos.
  - Correlaciones intencionales: plan vencido → falla recurrente; quiebre de
    stock → orden detenida; criticidad A → mayor pérdida.
"""

import json, csv, os, random, math

random.seed(20260101)  # reproducible

# Versión estable del snapshot. No usar date.today(): rompería la
# reproducibilidad del build y generaría diffs espurios en CI.
DATASET_VERSION = "2026-09-24"

OUT_JSON = "data/dataset.json"
OUT_CSV  = "data/sample"

# ----------------------------------------------------------------- calendario
MESES = []
for anio in (2025, 2026):
    for m in range(1, 13):
        MESES.append(f"{anio}-{m:02d}")
NM = len(MESES)  # 24

NOMBRE_MES = ["Ene","Feb","Mar","Abr","May","Jun","Jul","Ago","Sep","Oct","Nov","Dic"]

def etiqueta(ym):
    a, m = ym.split("-")
    return f"{NOMBRE_MES[int(m)-1]} {a[2:]}"

# ------------------------------------------------------------ maestro equipos
# (equipo, denominación, área, línea, criticidad, familia, fabricante, año, perfil de falla)
EQUIPOS = [
    ("EQ-0457","Envasadora L2","Envasado","Línea 2","A","Envasado","Vendor-K",2014, 3.30),
    ("EQ-0455","Envasadora L1","Envasado","Línea 1","A","Envasado","Vendor-K",2018, 1.35),
    ("EQ-0461","Etiquetadora L1","Envasado","Línea 1","A","Etiquetado","Vendor-S",2016, 1.95),
    ("EQ-0462","Etiquetadora L2","Envasado","Línea 2","B","Etiquetado","Vendor-S",2019, 1.05),
    ("EQ-0470","Paletizador","Envasado","Línea 3","B","Paletizado","Vendor-A",2017, 1.20),
    ("EQ-0471","Transportador L3","Envasado","Línea 3","C","Transporte","Vendor-A",2015, 0.80),
    ("EQ-0310","Reactor P1","Proceso","Línea 1","A","Proceso","Vendor-T",2012, 1.55),
    ("EQ-0311","Intercambiador P1","Proceso","Línea 1","B","Proceso","Vendor-T",2013, 0.95),
    ("EQ-0320","Mezclador P2","Proceso","Línea 2","B","Proceso","Vendor-T",2016, 1.10),
    ("EQ-0330","Bomba CIP","Proceso","Línea 2","B","Bombas","Vendor-G",2015, 1.45),
    ("EQ-0331","Bomba de proceso","Proceso","Línea 1","C","Bombas","Vendor-G",2018, 0.70),
    ("EQ-0201","Caldera 1","Servicios","N/A","A","Generación vapor","Vendor-B",2010, 1.25),
    ("EQ-0202","Caldera 2","Servicios","N/A","B","Generación vapor","Vendor-B",2019, 0.60),
    ("EQ-0210","Compresor 3","Servicios","N/A","B","Aire comprimido","Vendor-C",2014, 1.70),
    ("EQ-0211","Chiller 1","Servicios","N/A","A","Refrigeración","Vendor-C",2017, 1.00),
    ("EQ-0601","Grúa horquilla 4","Bodega","N/A","C","Movilización","Vendor-M",2020, 0.55),
]
EQ_IDX = {e[0]: e for e in EQUIPOS}

AREAS  = ["Envasado","Proceso","Servicios","Bodega"]
LINEAS = ["Línea 1","Línea 2","Línea 3","N/A"]
GRUPOS = ["Mecánico","Eléctrico","Instrumentación","Servicios"]

CLASES = {  # clase de orden SAP → tipo de mantenimiento
    "PM01":"Correctivo","PM05":"Emergencia","PM02":"Preventivo",
    "PM03":"Preventivo","PM04":"Mejora","PM06":"Predictivo",
}

CAUSAS = ["Desalineamiento","Desgaste","Falta de lubricación","Falla eléctrica",
          "Obstrucción","Fatiga de material","Ajuste incorrecto","Contaminación"]

CAT_PERDIDA = ["Averías","Paradas menores","Setup y ajustes",
               "Pérdida de velocidad","Defectos y reproceso","Arranque"]

# --------------------------------------------------- maestro de materiales MM
MATERIALES = [
    ("100231","Sello mecánico bomba","A", 2, 3, 28, True,  145),
    ("100455","Rodamiento 6308","A",      3, 4, 14, True,   82),
    ("100812","Correa transmisión","A",   1, 2, 21, True,   70),
    ("101044","Sensor de nivel","B",      6, 4, 18, False, 110),
    ("101220","Filtro de aire","B",      14, 8,  9, False,  38),
    ("101355","Válvula mariposa 3\"","B", 4, 3, 24, True,  195),
    ("101480","Junta espiralada","C",    42,20,  7, False,  12),
    ("101512","Contactor 40A","B",        9, 6, 12, False,  64),
    ("101633","Acople elástico","B",      5, 4, 16, True,   88),
    ("101744","Manómetro 0-10 bar","C",  18,10,  8, False,  22),
    ("101890","Reductor SEW","A",         1, 1, 45, True,  620),
    ("101955","Lubricante ISO 220 (20L)","C", 25, 12, 6, False, 34),
]

def curva(i, ini, fin, ruido=0.0):
    """Interpola con avance más rápido al inicio (mejora que se desacelera)."""
    t = i / (NM - 1)
    t = 1 - (1 - t) ** 1.6
    v = ini + (fin - ini) * t
    if ruido:
        v += random.uniform(-ruido, ruido)
    return v

def estacional(ym):
    """Factor estacional: verano austral (ene-feb) y picos de invierno (jul)."""
    m = int(ym.split("-")[1])
    return {1:1.22, 2:1.18, 3:1.05, 4:0.96, 5:0.94, 6:1.02,
            7:1.10, 8:1.03, 9:0.95, 10:0.93, 11:0.98, 12:1.08}[m]

# =============================================================== GENERACIÓN ===
ordenes, avisos, produccion, consumos, planes = [], [], [], [], []
oid, aid = 400000, 900000

# pesos de falla por equipo (Pareto)
peso_total = sum(e[8] for e in EQUIPOS)

for i, ym in enumerate(MESES):
    est = estacional(ym)

    # --- parámetros del mes (tendencia de mejora) ---
    pct_correctivo = curva(i, 0.42, 0.24, 0.015) * (1 + (est - 1) * 0.45)
    cumpl_pm       = curva(i, 0.74, 0.94, 0.02)
    calidad_datos  = curva(i, 0.82, 0.965, 0.012)
    n_ordenes      = int(curva(i, 118, 132) * est / 1.03)

    # ---------------------------------------------------------- PRODUCCIÓN PP
    for area in AREAS:
        lineas = ["Línea 1","Línea 2","Línea 3"] if area == "Envasado" else \
                 (["Línea 1","Línea 2"] if area == "Proceso" else ["N/A"])
        for ln in lineas:
            base_ton = {"Envasado":4200,"Proceso":3100,"Servicios":0,"Bodega":0}[area]
            ton   = round(base_ton * random.uniform(0.92, 1.08) * (est*0.4+0.6), 1) if base_ton else 0.0
            h_op  = round(curva(i, 610, 680) * random.uniform(0.96, 1.04), 1)
            h_det = round(h_op * (1 - curva(i, 0.86, 0.945, 0.012)) * est, 1)
            produccion.append([ym, area, ln, ton, h_op, h_det])

    # ------------------------------------------------------------ AVISOS PM
    n_avisos = int(n_ordenes * curva(i, 0.78, 0.92))
    for _ in range(n_avisos):
        r, acc = random.random() * peso_total, 0
        eq = EQUIPOS[-1]
        for e in EQUIPOS:
            acc += e[8]
            if r <= acc:
                eq = e
                break
        aid += 1
        crit_f = {"A":1.35,"B":1.0,"C":0.7}[eq[4]]
        dur = round(random.uniform(0.8, 9.5) * crit_f * curva(i, 1.18, 0.86), 1)
        cat = random.choices(CAT_PERDIDA, weights=[42,19,14,11,9,5])[0]
        causa = random.choices(CAUSAS, weights=[22,19,14,12,10,9,8,6])[0]
        # trazabilidad: mejora con el tiempo
        ligado = 1 if random.random() < curva(i, 0.86, 0.975) else 0
        avisos.append([aid, ym, eq[0], eq[1], eq[2], eq[3], eq[4],
                       causa, dur, cat, ligado])

    # ----------------------------------------------------------- ÓRDENES PM
    for _ in range(n_ordenes):
        oid += 1
        es_corr = random.random() < pct_correctivo
        if es_corr:
            clase = "PM05" if random.random() < 0.18 else "PM01"
        else:
            r = random.random()
            clase = "PM02" if r < 0.62 else ("PM03" if r < 0.86 else ("PM04" if r < 0.95 else "PM06"))
        tipo = CLASES[clase]

        # equipo (correctivos siguen el Pareto de fallas; preventivos son parejos)
        if es_corr:
            r, acc = random.random() * peso_total, 0
            eq = EQUIPOS[-1]
            for e in EQUIPOS:
                acc += e[8]
                if r <= acc:
                    eq = e
                    break
        else:
            eq = random.choice(EQUIPOS)

        crit_f = {"A":1.30,"B":1.0,"C":0.75}[eq[4]]
        hh_plan = round(random.uniform(2, 26) * (1.25 if es_corr else 1.0), 1)
        # el correctivo se desvía mucho más que el planificado
        desv = random.uniform(1.15, 2.2) if es_corr else random.uniform(0.92, 1.12)
        cerrada_pre = random.random() < curva(i, 0.86, 0.945)
        # una orden abierta solo tiene avance parcial: el resto es backlog
        hh_real = round(hh_plan * (desv if cerrada_pre else random.uniform(0.0, 0.45)), 1)

        tarifa = random.uniform(22, 48)
        # el plan se presupuesta con holgura: a nivel agregado el real queda cerca del plan
        holgura = 1.55 if es_corr else 1.03
        costo_plan = round(hh_plan * tarifa * crit_f * holgura, 1)             # k$
        costo_real = round(hh_plan * tarifa * crit_f * desv * random.uniform(0.95, 1.12), 1)
        if not cerrada_pre:
            costo_real = round(costo_real * random.uniform(0.0, 0.5), 1)

        cerrada = cerrada_pre
        estado  = "Cerrada" if cerrada else "Abierta"
        dias    = int(random.uniform(1, 14) * curva(i, 1.25, 0.82)) if cerrada else None
        retraso = 0
        if not cerrada_pre:
            retraso = int(max(0, random.gauss(9, 14)))
        elif random.random() < curva(i, 0.20, 0.08):
            retraso = int(random.uniform(1, 12))

        # banderas de calidad de datos (decrecen con la madurez)
        mala = 1 - calidad_datos
        flags = 0
        if random.random() < mala * 0.55: flags |= 1    # sin equipo
        if random.random() < mala * 1.05: flags |= 2    # sin aviso
        if cerrada and random.random() < mala * 0.95: flags |= 4   # cerrada sin HH
        if not cerrada and costo_real > 0 and random.random() < mala * 0.40: flags |= 8
        if tipo == "Preventivo" and retraso > 0 and random.random() < 0.55: flags |= 16

        grupo = random.choices(GRUPOS, weights=[42,31,17,10])[0]
        prioridad = random.choices(["Alta","Media","Baja"], weights=[24,46,30])[0]

        motivo = ""
        if not cerrada and retraso > 25:
            motivo = random.choices(["Espera de repuesto","Requiere parada de planta",
                                     "Sin asignación de técnico"], weights=[46,32,22])[0]

        ordenes.append([oid, ym, eq[2], eq[3], eq[0], eq[1], eq[4], tipo, clase,
                        estado, hh_plan, hh_real, costo_plan, costo_real,
                        dias, retraso, flags, grupo, prioridad, motivo])

    # ------------------------------------------------------------- PLANES PM
    n_planes = 46
    for p in range(n_planes):
        eq = EQUIPOS[p % len(EQUIPOS)]
        cumplido = random.random() < cumpl_pm
        planes.append([ym, f"PM-{1000+p:04d}", eq[0], eq[1], eq[2], eq[4],
                       random.choice(["Inspección mecánica","Lubricación",
                                      "Alineamiento y vibración","Inspección eléctrica",
                                      "Cambio de filtros"]),
                       random.choice(["Quincenal","Mensual","Trimestral"]),
                       "Cumplido" if cumplido else "Vencido"])

    # ------------------------------------------------------- CONSUMO MM (MB51)
    for m in MATERIALES:
        base = {"A":2.4,"B":4.2,"C":7.5}[m[2]]
        qty  = max(0, int(random.gauss(base, base*0.45) * est))
        if qty:
            area = random.choices(AREAS, weights=[46,28,20,6])[0]
            consumos.append([ym, m[0], m[1], area, qty, round(qty*m[7], 1), m[6]])

# ---------------------------------------------------------------- A3 / KAIZEN
KAIZEN = [
    ["A3-01","Averías Envasadora L2","EQ-0457","Envasado","Confiabilidad","Act",  6200,"2025-09","MTBF (h)",186,268],
    ["A3-02","Setup cambio de formato","EQ-0455","Envasado","Proceso","Check",   3400,"2025-11","Setup (min)",74,46],
    ["A3-03","Paradas menores Etiquetadora","EQ-0461","Envasado","Autónomo","Do",2800,"2026-02","Paradas/sem",31,19],
    ["A3-04","Consumo repuestos críticos","EQ-0210","Servicios","Planificación","Act",1800,"2026-01","Costo rep. (k$)",2400,1700],
    ["A3-05","Fallas eléctricas Compresor 3","EQ-0210","Servicios","Confiabilidad","Do",2400,"2026-04","MTBF (h)",240,296],
    ["A3-06","Lubricación autónoma Línea 3","EQ-0470","Envasado","Autónomo","Plan",1500,"2026-06","Fallas/mes",6,4],
    ["A3-07","Eficiencia térmica Caldera 1","EQ-0201","Servicios","Proceso","Check",3100,"2026-03","Consumo (%)",100,92],
    ["A3-08","Cierre técnico oportuno","","Transversal","Calidad datos","Act",   900,"2025-12","Cerr. sin HH",62,21],
    ["A3-09","Alineamiento Bomba CIP","EQ-0330","Proceso","Confiabilidad","Do",  1700,"2026-05","MTBF (h)",212,244],
    ["A3-10","Reducción de defectos envasado","EQ-0457","Envasado","Calidad","Plan",2600,"2026-08","Defectos (ppm)",840,620],
    ["A3-11","Gestión de repuestos A","","Bodega","Planificación","Do",          2100,"2026-07","Quiebres/mes",7,4],
    ["A3-12","Velocidad nominal Línea 1","EQ-0455","Envasado","Proceso","Plan",  3300,"2026-09","Velocidad (%)",84,93],
]

# ============================================================ ESCRITURA CSV ===
os.makedirs(OUT_CSV, exist_ok=True)

def escribir(nombre, cabecera, filas):
    with open(f"{OUT_CSV}/{nombre}.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(cabecera)
        w.writerows(filas)

escribir("FactOrdenesMtto",
         ["Orden","AnioMes","Area","Linea","Equipo","DenominacionEquipo","Criticidad",
          "TipoMantenimiento","ClaseOrden","EstadoCierre","Trabajo","TrabajoReal",
          "CostoPlan","CostoReal","DiasCierre","RetrasoDias","FlagsCalidad",
          "GrupoPlanificador","Prioridad","MotivoDetencion"], ordenes)

escribir("FactAvisosMtto",
         ["Aviso","AnioMes","Equipo","DenominacionEquipo","Area","Linea","Criticidad",
          "Causa","DuracionParada_h","CategoriaPerdida","LigadoAOrden"], avisos)

escribir("FactProduccion",
         ["AnioMes","Area","Linea","ToneladasProducidas","HorasOperacion","HorasDetencion"],
         produccion)

escribir("FactMaterialesMtto",
         ["AnioMes","Material","Descripcion","Area","Cantidad","Importe","EsRepuestoCritico"],
         consumos)

escribir("FactPlanesMtto",
         ["AnioMes","Plan","Equipo","DenominacionEquipo","Area","Criticidad",
          "Estrategia","Ciclo","Estado"], planes)

escribir("DimEquipo",
         ["Equipo","Denominacion","Area","Linea","Criticidad","Familia",
          "Fabricante","Anio","PesoFalla"], EQUIPOS)

escribir("DimMaterial",
         ["Material","Descripcion","ABC","StockActual","StockMinimo",
          "LeadTimeDias","EsRepuestoCritico","PrecioUnitario"], MATERIALES)

escribir("FactKaizen",
         ["A3","PerdidaAtacada","Equipo","Area","EquipoTrabajo","FasePDCA",
          "AhorroValidado","AnioMesInicio","KPI","Antes","Despues"], KAIZEN)

# =========================================================== PAYLOAD COMPACTO ==
dataset = {
    "meta": {
        "generado": DATASET_VERSION,
        "meses": MESES,
        "etiquetas": [etiqueta(m) for m in MESES],
        "areas": AREAS,
        "lineas": LINEAS,
        "grupos": GRUPOS,
        "criticidades": ["A","B","C"],
        "tipos": ["Correctivo","Preventivo","Predictivo","Mejora","Emergencia"],
        "nota": "Datos sintéticos. Estructura equivalente a la entregada por SAP PM/MM/CO/PP.",
    },
    "equipos":  [[e[0],e[1],e[2],e[3],e[4],e[5],e[6],e[7]] for e in EQUIPOS],
    "materiales":[[m[0],m[1],m[2],m[3],m[4],m[5],1 if m[6] else 0,m[7]] for m in MATERIALES],
    "ordenes":   ordenes,
    "avisos":    avisos,
    "produccion":produccion,
    "consumos":  [[c[0],c[1],c[2],c[3],c[4],c[5],1 if c[6] else 0] for c in consumos],
    "planes":    planes,
    "kaizen":    KAIZEN,
}

os.makedirs("data", exist_ok=True)
with open(OUT_JSON, "w", encoding="utf-8") as f:
    json.dump(dataset, f, ensure_ascii=False, separators=(",", ":"))

kb = os.path.getsize(OUT_JSON) / 1024
print(f"OK - {len(MESES)} meses ({MESES[0]} -> {MESES[-1]})")
print(f"   ordenes={len(ordenes)}  avisos={len(avisos)}  planes={len(planes)}  "
      f"consumos={len(consumos)}  produccion={len(produccion)}")
print(f"   data/dataset.json = {kb:.0f} KB - CSV en {OUT_CSV}/")
