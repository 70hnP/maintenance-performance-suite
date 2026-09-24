# Sistema de diseño

La experiencia prioriza lectura ejecutiva, trazabilidad y densidad controlada.

## Principios visuales

- **Una pregunta por página:** el título formula la decisión que la vista debe habilitar.
- **Jerarquía estable:** KPI arriba, diagnóstico al centro y narrativa/decisión al pie.
- **Color con significado:** azul para estructura, verde para desempeño favorable, ámbar para atención y rojo para riesgo.
- **Trazabilidad visible:** cada visual presenta un chip con su transacción SAP.
- **Brechas honestas:** proxies y datos faltantes aparecen junto al indicador, no en notas ocultas.

## Tokens principales

| Token | Valor | Uso |
|---|---|---|
| Navy | `#0B172A` | encabezados, navegación y texto estructural |
| Blue | `#2563EB` | énfasis, selección y series principales |
| Teal | `#0F766E` | desempeño favorable y mejora |
| Amber | `#D97706` | advertencias y desvíos |
| Red | `#B91C1C` | pérdidas críticas y fallas |
| Slate 50 | `#F8FAFC` | fondo de superficie |

## Accesibilidad y comportamiento

- No comunicar estado solo por color; acompañar con texto, icono o etiqueta.
- Mantener contraste legible y etiquetas compactas en español.
- Los filtros actualizan KPIs, gráficos y narrativa; el estado sin datos se declara explícitamente.
- La vista se adapta a escritorio y móvil sin ocultar la trazabilidad.

## Componentes

Los componentes base son navegación lateral, barra de filtros, tarjetas KPI, gráficos, tablas, chips SAP, llamadas de brecha y banda narrativa. Cualquier nueva página debe reutilizarlos y conservar el orden visual.
