# Diccionario de datos

El contrato ejecutable completo está en [`data/schema.json`](../data/schema.json). Esta vista resume el grano y la responsabilidad de cada entidad.

| Entidad | Grano | Clave | Propósito |
|---|---|---|---|
| DimFecha | un mes | AñoMes | calendario común de análisis |
| DimEquipo | un equipo | EquipoId | jerarquía técnica, área, línea y criticidad |
| DimMaterial | un material | MaterialId | catálogo y criticidad de repuestos |
| FactOrdenesMtto | una orden | OrdenId | ejecución, estado, horas y costo de mantenimiento |
| FactAvisos | un aviso | AvisoId | falla, causa, detención y relación con la orden |
| FactPlanes | una posición de plan | PlanPosicionId | programación y cumplimiento preventivo |
| FactCostos | un registro de costo | CostoId | costo real, plan y comprometido por orden |
| FactMateriales | un movimiento/posición | MovimientoId | consumo, stock y quiebre por material |
| FactProduccion | equipo y mes | ProduccionId | producción, operación y detención |

## Convenciones

- Identificadores terminados en `Id` son texto y conservan el formato del origen.
- `AñoMes` usa `YYYY-MM` y gobierna todas las comparaciones temporales.
- Campos `nullable_*` del esquema aceptan vacío; el resto es obligatorio.
- Montos y cantidades son no negativos en el dataset analítico.
- Banderas de calidad se agregan como conteos de defectos detectados; no se interpretan como órdenes.

## Relaciones

Las dimensiones filtran los hechos en relaciones 1:N y dirección única. `DimFecha` y `DimEquipo` son dimensiones conformadas. Las relaciones entre aviso y orden se resuelven mediante identificadores de negocio sin crear filtros bidireccionales ambiguos.

## Evolución del contrato

Cualquier alta, baja o cambio de tipo requiere actualizar `schema.json`, el generador, Power Query/TMDL, las medidas afectadas y las pruebas. La CI debe quedar verde antes de integrar el cambio.
