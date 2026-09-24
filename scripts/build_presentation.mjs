import fs from "node:fs/promises";
import path from "node:path";
import { pathToFileURL } from "node:url";
import { Presentation, PresentationFile } from "@oai/artifact-tool";

const root = path.resolve(import.meta.dirname, "..");
const { SKILL_DIR, TMP_DIR, RUNTIME_PYTHON } = process.env;
const { resolvePresentationFont, applyPresentationChartFont, makeNativeBulletParagraphs, finalizePresentation } = await import(
  pathToFileURL(path.join(SKILL_DIR, "container_tools", "artifact_tool_utils.mjs")).href,
);
await fs.mkdir(TMP_DIR, { recursive: true });
await fs.mkdir(path.join(root, "deliverables"), { recursive: true });
const D = JSON.parse(await fs.readFile(path.join(root, "data", "dataset.json"), "utf8"));
const family = resolvePresentationFont({ fontFamily: "Arial" });
const p = Presentation.create({ slideSize: { width: 1280, height: 720 } });
const navy = "#0E1C33", blue = "#2F6FED", orange = "#D97706", green = "#12805C", red = "#B42318", grey = "#667085", pale = "#EEF4FF";

function box(slide, text, x, y, w, h, size = 25, color = navy, bold = false) {
  const shape = slide.shapes.add({ geometry: "textbox", position: { left: x, top: y, width: w, height: h }, fill: "none", line: { fill: "none", width: 0 } });
  shape.text = text;
  shape.text.style = { typeface: family, fontSize: size, color, bold, autoFit: "shrinkText" };
  return shape;
}
function title(slide, text, number) {
  box(slide, text, 70, 45, 1000, 58, 36, navy, true);
}
function note(slide, text) { slide.speakerNotes.textFrame.setText(text); }
function bullets(slide, items, x, y, w, h, size = 24) {
  const shape = box(slide, "", x, y, w, h, size, navy, false);
  shape.text = makeNativeBulletParagraphs(items, { marginLeftPoints: 18, hangingPoints: 9, spaceAfterPoints: 9 });
  shape.text.style = { typeface: family, fontSize: size, color: navy, autoFit: "shrinkText" };
}
function ordersByMonth(type) {
  return D.meta.meses.map(month => D.ordenes.filter(o => o[1] === month && (!type || o[7] === type)).length);
}
const totalCost = D.ordenes.reduce((a, o) => a + o[13], 0);
const totalPlan = D.ordenes.reduce((a, o) => a + o[12], 0);
const failures = D.avisos.length;
const availability = 1 - D.produccion.reduce((a, r) => a + r[5], 0) / D.produccion.reduce((a, r) => a + r[4], 0);
const savings = D.kaizen.reduce((a, r) => a + r[6], 0);

{
  const s = p.slides.add(); s.background.fill = navy;
  box(s, "Maintenance Performance Suite", 84, 160, 1080, 90, 52, "#FFFFFF", true);
  box(s, "Sistema analítico para mantenimiento industrial", 88, 260, 900, 50, 27, "#D7E3F8", false);
  box(s, "SAP PM MM CO PP  |  Power BI  |  Mejora Enfocada", 88, 540, 1000, 40, 19, "#AFC6EA", false);
  box(s, "Datos sintéticos", 88, 590, 400, 30, 15, "#9AAED0", false);
  note(s, "Todos los datos son sintéticos. El producto no representa una operación real.");
}
{
  const s = p.slides.add(); s.background.fill = "#FFFFFF"; title(s, "Resumen ejecutivo", 2);
  box(s, `${D.ordenes.length.toLocaleString("es-CL")} órdenes`, 80, 155, 250, 60, 34, blue, true);
  box(s, `${failures.toLocaleString("es-CL")} avisos`, 380, 155, 250, 60, 34, orange, true);
  box(s, `${(availability*100).toFixed(1)}% disponibilidad`, 680, 155, 430, 60, 34, green, true);
  box(s, `M$ ${(totalCost/1000).toFixed(1)} costo real`, 80, 265, 430, 60, 31, navy, true);
  box(s, `M$ ${(savings/1000).toFixed(1)} ahorro validado`, 580, 265, 520, 60, 31, blue, true);
  bullets(s, ["La base cubre 24 meses y concentra las fallas en pocos activos.", "El modelo conecta costo, confiabilidad, backlog y cumplimiento preventivo.", "La cartera A3 exige ahorro confirmado y actualización del estándar."], 85, 390, 1040, 190, 24);
  note(s, "Fuente: dataset sintético generado por data/generate_synthetic.py.");
}
{
  const s = p.slides.add(); s.background.fill = "#FFFFFF"; title(s, "Arquitectura", 3);
  box(s, "SAP PM MM CO PP", 90, 170, 210, 55, 26, navy, true);
  box(s, "Power Query", 335, 170, 180, 55, 26, blue, true);
  box(s, "Modelo TMDL", 550, 170, 190, 55, 26, navy, true);
  box(s, "79 medidas DAX", 775, 170, 220, 55, 26, blue, true);
  box(s, "12 páginas PBIR", 1030, 170, 190, 55, 26, navy, true);
  box(s, "Cada capa conserva la fuente, el grano y la definición del indicador.", 125, 280, 1030, 55, 29, navy, true);
  bullets(s, ["15 tablas semánticas con relaciones controladas.", "174 visuales con transacción SAP visible.", "Build reproducible, pruebas automatizadas y publicación continua."], 170, 390, 900, 180, 25);
  note(s, "Fuente: estructura PBIP y PROJECT_SPEC.md del repositorio.");
}
{
  const s = p.slides.add(); s.background.fill = "#FFFFFF"; title(s, "El correctivo disminuye", 4);
  const chart = s.charts.add("line", { position: { left: 90, top: 150, width: 1100, height: 430 }, categories: D.meta.etiquetas, series: [
    { name: "Correctivo", values: ordersByMonth("Correctivo"), line: { color: red, width: 3 } },
    { name: "Preventivo", values: ordersByMonth("Preventivo"), line: { color: blue, width: 3 } },
  ], hasLegend: true, legend: { position: "bottom" } });
  chart.title = "Órdenes por mes"; applyPresentationChartFont(chart, { fontFamily: family });
  note(s, "Fuente: IW39 simulado. Datos sintéticos. El gráfico usa conteos de órdenes por tipo y mes.");
}
{
  const s = p.slides.add(); s.background.fill = "#FFFFFF"; title(s, "Concentración de fallas", 5);
  const groups = new Map(); for (const a of D.avisos) groups.set(a[3], (groups.get(a[3]) || 0) + 1);
  const top = [...groups.entries()].sort((a,b) => b[1]-a[1]).slice(0, 7);
  const chart = s.charts.add("bar", { position: { left: 100, top: 150, width: 1080, height: 430 }, categories: top.map(x=>x[0]), series: [{ name: "Avisos", values: top.map(x=>x[1]), fill: orange }], barOptions: { direction: "bar", grouping: "clustered" }, hasLegend: false, dataLabels: { showValue: true, position: "outEnd" } });
  chart.title = "Avisos acumulados"; applyPresentationChartFont(chart, { fontFamily: family });
  note(s, "Fuente: IW29 e IH08 simulados. Datos sintéticos.");
}
{
  const s = p.slides.add(); s.background.fill = "#FFFFFF"; title(s, "Costo y capacidad", 6);
  box(s, `Costo real M$ ${(totalCost/1000).toFixed(1)}`, 90, 155, 480, 60, 34, navy, true);
  box(s, `Plan M$ ${(totalPlan/1000).toFixed(1)}`, 690, 155, 420, 60, 34, blue, true);
  const open = D.ordenes.filter(o => o[9] === "Abierta");
  const backlog = open.reduce((a,o)=>a+Math.max(0,o[10]-o[11]),0);
  const waiting = open.filter(o=>o[19]==="Espera de repuesto").length;
  bullets(s, [`Backlog abierto: ${backlog.toFixed(0)} HH pendientes.`, `${waiting} órdenes esperan repuesto en el período seleccionado.`, "El correctivo muestra mayor dispersión de costo que el preventivo."], 130, 300, 1020, 210, 27);
  box(s, "Prioridad: programación semanal por especialidad y protección de repuestos A.", 130, 545, 1020, 50, 24, red, true);
  note(s, "Fuentes simuladas: IW39, IW47, KOB1, MB51 y CR03.");
}
{
  const s = p.slides.add(); s.background.fill = "#FFFFFF"; title(s, "Cartera A3", 7);
  const phase = new Map(); for (const k of D.kaizen) phase.set(k[5], (phase.get(k[5])||0)+1);
  const phaseOrder = ["Plan", "Do", "Check", "Act"];
  const chart = s.charts.add("bar", { position: { left: 90, top: 155, width: 500, height: 370 }, categories: phaseOrder, series: [{ name: "A3", values: phaseOrder.map(key => phase.get(key) || 0), fill: blue }], barOptions: { direction: "column", grouping: "clustered" }, hasLegend: false, dataLabels: { showValue: true, position: "outEnd" } });
  chart.title = "Iniciativas por fase PDCA"; applyPresentationChartFont(chart, { fontFamily: family });
  box(s, `M$ ${(savings/1000).toFixed(1)}`, 730, 210, 350, 70, 48, green, true);
  box(s, "Ahorro validado", 730, 285, 350, 40, 22, grey, false);
  bullets(s, ["Las iniciativas se originan en pérdidas cuantificadas.", "El cierre exige verificación en CO.", "Act requiere actualizar el plan preventivo."], 670, 375, 450, 180, 23);
  note(s, "Fuente: cartera A3 sintética y KOB1 simulado.");
}
{
  const s = p.slides.add(); s.background.fill = navy;
  box(s, "Decisiones para la implementación", 70, 45, 1000, 58, 36, "#FFFFFF", true);
  box(s, "1", 95, 170, 50, 50, 30, "#7FB0FF", true); box(s, "Asignar dueño por KPI y por fuente SAP", 170, 166, 880, 60, 28, "#FFFFFF", true);
  box(s, "2", 95, 285, 50, 50, 30, "#7FB0FF", true); box(s, "Reconciliar los ocho KPI principales con tolerancia de 1%", 170, 281, 950, 60, 28, "#FFFFFF", true);
  box(s, "3", 95, 400, 50, 50, 30, "#7FB0FF", true); box(s, "Publicar el piloto y cerrar la primera mejora con ahorro confirmado", 170, 396, 980, 70, 28, "#FFFFFF", true);
  box(s, "El OEE permanece parcial hasta integrar velocidad y calidad de línea.", 170, 550, 920, 45, 21, "#C7D8F5", false);
  note(s, "El benchmark es orientativo. Los valores actuales son sintéticos y no constituyen una medición auditada.");
}

const finalPath = path.join(root, "deliverables", "presentacion-ejecutiva-validada.pptx");
const requirements = { explicitTotalSlideCount: 8, requiredNativeTableOwnerSlides: [], requiredNativeChartOwnerSlides: [4,5,7], materializeLiteralChartWorkbooks: true };
const fontPolicy = { basis: "design", families: [family] };
const candidatePath = path.join(TMP_DIR, "candidate.pptx");
await (await PresentationFile.exportPptx(p)).save(candidatePath);
await finalizePresentation({ ...requirements, workspaceDir: root, candidatePath, finalPath, pythonExecutable: RUNTIME_PYTHON, integrityValidatorPath: path.join(SKILL_DIR, "container_tools", "inspect_presentation_package_integrity.py"), layoutValidatorPath: path.join(SKILL_DIR, "container_tools", "inspect_presentation_layout_geometry.py"), layoutArgs: ["--expected-slide-size-emu", "12192000,6858000", "--validate-bullet-geometry", "--validate-heading-fit"], requiredNativeTableOwnerSlides: [], fontPolicy, verifyArtifactToolImport: true, receiptPath: path.join(TMP_DIR, "presentation-v4.validation.json") });
console.log(finalPath);
