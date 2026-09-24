import fs from "node:fs/promises";
import path from "node:path";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const root = path.resolve(import.meta.dirname, "..");
const outDir = path.join(root, "deliverables");
await fs.mkdir(outDir, { recursive: true });
await fs.mkdir(path.join(root, ".artifact-qa"), { recursive: true });
const schema = JSON.parse(await fs.readFile(path.join(root, "data", "schema.json"), "utf8"));
const measuresText = await fs.readFile(path.join(root, "pbip", "MaintenancePerformanceSuite.SemanticModel", "definition", "tables", "_Medidas.tmdl"), "utf8");
const measures = [...measuresText.matchAll(/^\s*measure\s+'?([^'=]+?)'?\s*=/gm)].map((m, i) => [i + 1, m[1].trim()]);

const relations = [
  ["DimFecha", "Fecha", "FactOrdenesMtto", "FechaEntrada", "IW39"],
  ["DimFecha", "Fecha", "FactAvisosMtto", "FechaAviso", "IW29"],
  ["DimFecha", "Fecha", "FactProduccion", "Fecha", "COOIS"],
  ["DimEquipo", "Equipo", "FactOrdenesMtto", "Equipo", "IH08 / IW39"],
  ["DimEquipo", "Equipo", "FactAvisosMtto", "Equipo", "IH08 / IW29"],
  ["DimEquipo", "Equipo", "FactPlanesMtto", "Equipo", "IH08 / IP24"],
  ["DimTipoOrden", "ClaseOrden", "FactOrdenesMtto", "ClaseOrden", "Catálogo / IW39"],
  ["DimMaterial", "Material", "FactMaterialesMtto", "Material", "MM03 / MB51"],
  ["DimLinea", "Linea", "FactProduccion", "Linea", "COOIS"],
  ["DimArea", "Area", "FactOrdenesMtto", "Area", "IW39"],
];

const workbook = Workbook.create();
const summary = workbook.worksheets.add("Resumen");
const dictionary = workbook.worksheets.add("Diccionario");
const relationshipSheet = workbook.worksheets.add("Relaciones");
const measureSheet = workbook.worksheets.add("Medidas DAX");
const font = "Arial";
const navy = "#0E1C33", blue = "#2F6FED", pale = "#EEF4FF", line = "#D9E2F2", grey = "#667085";

for (const sheet of [summary, dictionary, relationshipSheet, measureSheet]) {
  sheet.showGridLines = false;
}

summary.getRange("A2:H2").merge();
summary.getRange("A2").values = [["Modelo semántico de mantenimiento"]];
summary.getRange("A2").format.font = { name: font, size: 16, bold: true, color: navy };
summary.getRange("A3:H3").format.borders = { bottom: { style: "thin", color: blue } };
summary.getRange("A5:B9").values = [
  ["Componente", "Cobertura"],
  ["Tablas TMDL", 15],
  ["Medidas DAX", measures.length],
  ["Relaciones documentadas", relations.length],
  ["Páginas PBIR", 12],
];
summary.getRange("A5:B5").format = { fill: navy, font: { name: font, bold: true, color: "#FFFFFF" }, horizontalAlignment: "center" };
summary.getRange("A5:B9").format.borders = { preset: "all", style: "thin", color: line };
summary.getRange("D5:H5").merge();
summary.getRange("D5").values = [["Principios de control"]];
summary.getRange("D5").format = { fill: navy, font: { name: font, bold: true, color: "#FFFFFF" } };
summary.getRange("D6:H10").values = [
  ["Trazabilidad", "Cada KPI declara la transacción SAP de origen", null, null, null],
  ["Cálculo", "MTTR usa duración de aviso, no horas hombre", null, null, null],
  ["Backlog", "Solo órdenes abiertas con HH pendientes", null, null, null],
  ["Gobierno", "Relaciones 1 a N y filtro unidireccional", null, null, null],
  ["Alcance", "Datos sintéticos y benchmark orientativo", null, null, null],
];
summary.getRange("D6:D10").format.font = { name: font, bold: true, color: navy };
summary.getRange("D5:H10").format.borders = { preset: "all", style: "thin", color: line };
summary.getRange("E6:H10").merge(true);
summary.getRange("A12:H14").merge(true);
summary.getRange("A12").values = [["Uso recomendado"]];
summary.getRange("A12").format.font = { name: font, bold: true, color: navy };
summary.getRange("A13").values = [["Este libro documenta el contrato analítico. Las definiciones ejecutables viven en TMDL y PBIR dentro de la carpeta pbip."]];
summary.getRange("A13").format.font = { name: font, italic: true, color: grey };
summary.getRange("A:A").format.columnWidth = 28;
summary.getRange("B:B").format.columnWidth = 18;
summary.getRange("C:C").format.columnWidth = 4;
summary.getRange("D:D").format.columnWidth = 20;
summary.getRange("E:H").format.columnWidth = 16;
summary.tabColor = navy;

const dictRows = [];
for (const [table, contract] of Object.entries(schema.tables)) {
  for (const [column, type] of Object.entries(contract.columns)) {
    const role = contract.primaryKey.includes(column) ? "PK" : (schema.foreignKeys.some(fk => fk.table === table && fk.column === column) ? "FK" : "Atributo / medida");
    dictRows.push([table, column, type, role]);
  }
}
dictionary.getRange("A2:D2").merge();
dictionary.getRange("A2").values = [["Diccionario de datos"]];
dictionary.getRange("A2").format.font = { name: font, size: 16, bold: true, color: navy };
dictionary.getRange("A4:D4").values = [["Tabla", "Columna", "Tipo", "Rol"]];
dictionary.getRange("A5").write(dictRows);
dictionary.getRange(`A4:D${4 + dictRows.length}`).format.borders = { preset: "all", style: "thin", color: line };
dictionary.getRange("A4:D4").format = { fill: navy, font: { name: font, bold: true, color: "#FFFFFF" }, horizontalAlignment: "center" };
dictionary.getRange(`A5:A${4 + dictRows.length}`).format.fill = pale;
dictionary.getRange("A:D").format.columnWidth = 24;
dictionary.getRange("B:B").format.columnWidth = 30;
dictionary.freezePanes.freezeRows(4);
dictionary.tabColor = blue;

relationshipSheet.getRange("A2:E2").merge();
relationshipSheet.getRange("A2").values = [["Relaciones principales del modelo"]];
relationshipSheet.getRange("A2").format.font = { name: font, size: 16, bold: true, color: navy };
relationshipSheet.getRange("A4:E4").values = [["Dimensión", "Clave", "Hecho", "Clave", "Fuente SAP"]];
relationshipSheet.getRange("A5").write(relations);
relationshipSheet.getRange(`A4:E${4 + relations.length}`).format.borders = { preset: "all", style: "thin", color: line };
relationshipSheet.getRange("A4:E4").format = { fill: navy, font: { name: font, bold: true, color: "#FFFFFF" }, horizontalAlignment: "center" };
relationshipSheet.getRange("A:E").format.columnWidth = 24;
relationshipSheet.getRange("C:C").format.columnWidth = 28;
relationshipSheet.freezePanes.freezeRows(4);

measureSheet.getRange("A2:C2").merge();
measureSheet.getRange("A2").values = [["Inventario de medidas DAX"]];
measureSheet.getRange("A2").format.font = { name: font, size: 16, bold: true, color: navy };
measureSheet.getRange("A4:C4").values = [["N°", "Medida", "Modelo"]];
measureSheet.getRange("A5").write(measures.map(row => [row[0], row[1], "_Medidas.tmdl"]));
measureSheet.getRange(`A4:C${4 + measures.length}`).format.borders = { preset: "all", style: "thin", color: line };
measureSheet.getRange("A4:C4").format = { fill: navy, font: { name: font, bold: true, color: "#FFFFFF" }, horizontalAlignment: "center" };
measureSheet.getRange("A:A").format.columnWidth = 8;
measureSheet.getRange("B:B").format.columnWidth = 44;
measureSheet.getRange("C:C").format.columnWidth = 24;
measureSheet.freezePanes.freezeRows(4);

for (const sheet of [summary, dictionary, relationshipSheet, measureSheet]) {
  sheet.getUsedRange().format.font.name = font;
}

workbook.recalculate();
const inspect = await workbook.inspect({ kind: "sheet,table", maxChars: 5000, tableMaxRows: 8, tableMaxCols: 8 });
console.log(inspect.ndjson);
const errors = await workbook.inspect({ kind: "match", searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!", options: { useRegex: true, maxResults: 50 }, summary: "formula errors" });
console.log(errors.ndjson);
for (const name of ["Resumen", "Diccionario", "Relaciones", "Medidas DAX"]) {
  const preview = await workbook.render({ sheetName: name, autoCrop: "all", scale: 1, format: "png" });
  await fs.writeFile(path.join(root, ".artifact-qa", `xlsx-${name.replaceAll(" ", "-")}.png`), new Uint8Array(await preview.arrayBuffer()));
}
const output = await SpreadsheetFile.exportXlsx(workbook);
await output.save(path.join(outDir, "modelo-semantico.xlsx"));
console.log(`Workbook written: ${path.join(outDir, "modelo-semantico.xlsx")}`);
