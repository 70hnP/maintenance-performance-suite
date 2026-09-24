# Contrato de extracción SAP

Esta matriz define la procedencia esperada. Los nombres de campos pueden variar por versión, parametrización y extractores corporativos; el equipo de datos debe mantener un mapeo versionado hacia el esquema de `data/schema.json`.

| Dominio | Transacciones | Entidades de destino | Uso analítico |
|---|---|---|---|
| Órdenes PM | IW39, IW38 | FactOrdenesMtto, DimEquipo | mix, ciclo, cierre, HH y costo por orden |
| Avisos PM | IW28, IW29, IW59 | FactAvisos | fallas, causa, duración, reincidencia y MTTR |
| Confirmaciones | IW47 | FactOrdenesMtto | horas reales y avance técnico |
| Planes | IP15, IP24, IP30 | FactPlanes | cumplimiento, vencimientos y adherencia |
| Equipos | IH08, IH06, IE03 | DimEquipo | jerarquía, área, línea y criticidad |
| Costos CO | KOB1, KSB1, S_ALR_87013558 | FactCostos | real, plan, comprometido y clase de costo |
| Materiales MM | MB51, MB52, MM03, ME2N | FactMateriales, DimMaterial | consumo, stock, criticidad y abastecimiento |
| Producción PP | COOIS, MCRE | FactProduccion | toneladas, horas operativas y detención |

## Controles mínimos por carga

- Registrar sociedad, centro, fecha/hora de extracción, variante y responsable.
- Conservar claves SAP sin truncar ceros y normalizar fechas a ISO 8601.
- Validar duplicados por clave primaria antes de publicar.
- Conciliar conteos y montos contra una variante SAP congelada.
- Rechazar claves foráneas inexistentes o enviarlas a una cola de excepción explícita.
- Separar dato fuente de derivaciones analíticas; ninguna medida debe modificar el extracto.

## Propiedad y frecuencia sugerida

PM y MM se refrescan diariamente; CO al menos al cierre diario y mensual; PP de acuerdo con la latencia del sistema productivo. El dueño funcional aprueba reglas de negocio y el dueño de datos certifica completitud, puntualidad y reconciliación.
