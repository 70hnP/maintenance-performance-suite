from __future__ import annotations

import csv
import json
import re
import subprocess
import tempfile
import unittest
import zipfile
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ScriptCollector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.current = None
        self.scripts = []

    def handle_starttag(self, tag, attrs):
        if tag == "script":
            self.current = dict(attrs)
            self.scripts.append([self.current, ""])

    def handle_data(self, data):
        if self.current is not None:
            self.scripts[-1][1] += data

    def handle_endtag(self, tag):
        if tag == "script":
            self.current = None


def load_csv(table: str):
    path = ROOT / "data" / "sample" / f"{table}.csv"
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


class DataContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema = json.loads((ROOT / "data" / "schema.json").read_text(encoding="utf-8"))
        cls.rows = {name: load_csv(name) for name in cls.schema["tables"]}

    def test_headers_row_counts_and_primary_keys(self):
        for name, contract in self.schema["tables"].items():
            with self.subTest(table=name):
                rows = self.rows[name]
                self.assertGreaterEqual(len(rows), contract["minRows"])
                self.assertEqual(list(rows[0]), list(contract["columns"]))
                keys = [tuple(row[col] for col in contract["primaryKey"]) for row in rows]
                self.assertEqual(len(keys), len(set(keys)), f"PK duplicada en {name}")

    def test_column_types(self):
        ym = re.compile(r"^20\d{2}-(0[1-9]|1[0-2])$")
        for name, contract in self.schema["tables"].items():
            for row_number, row in enumerate(self.rows[name], start=2):
                for column, kind in contract["columns"].items():
                    value = row[column]
                    with self.subTest(table=name, row=row_number, column=column):
                        if kind.startswith("nullable_") and value == "":
                            continue
                        base = kind.removeprefix("nullable_")
                        if base == "integer":
                            int(value)
                        elif base == "number":
                            self.assertGreaterEqual(float(value), 0)
                        elif base == "boolean":
                            self.assertIn(value, {"True", "False"})
                        elif base == "year_month":
                            self.assertRegex(value, ym)
                        else:
                            self.assertNotEqual(value, "")

    def test_foreign_keys(self):
        for fk in self.schema["foreignKeys"]:
            allowed = {row[fk["refColumn"]] for row in self.rows[fk["refTable"]]}
            actual = {row[fk["column"]] for row in self.rows[fk["table"]]}
            if fk.get("nullable"):
                actual.discard("")
            self.assertLessEqual(actual, allowed, f"FK inválida: {fk}")

    def test_business_invariants(self):
        orders = self.rows["FactOrdenesMtto"]
        self.assertEqual({row["Criticidad"] for row in orders}, {"A", "B", "C"})
        self.assertEqual({row["EstadoCierre"] for row in orders}, {"Abierta", "Cerrada"})
        self.assertTrue(any(int(row["FlagsCalidad"]) > 0 for row in orders))
        for row in orders:
            if row["EstadoCierre"] == "Abierta":
                self.assertEqual(row["DiasCierre"], "")
        production = self.rows["FactProduccion"]
        self.assertTrue(all(float(row["HorasDetencion"]) <= float(row["HorasOperacion"]) for row in production))


class ProductTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = (ROOT / "src" / "mockup" / "index.html").read_text(encoding="utf-8")
        cls.parser = ScriptCollector()
        cls.parser.feed(cls.html)

    def test_embedded_dataset_is_current(self):
        embedded = next(text for attrs, text in self.parser.scripts if attrs.get("id") == "ds")
        self.assertEqual(json.loads(embedded), json.loads((ROOT / "data" / "dataset.json").read_text(encoding="utf-8")))

    def test_dashboard_contract(self):
        page_block = re.search(r"const PAGES=\[(.*?)\];", self.html, re.DOTALL)
        self.assertIsNotNone(page_block)
        self.assertEqual(len(re.findall(r"\{id:\d+", page_block.group(1))), 12)
        self.assertIn("function chips()", self.html)
        self.assertIn("sapchip", self.html)
        self.assertIn("referencia orientativa", self.html.lower())
        self.assertIn("datos sintéticos", self.html.lower())
        self.assertNotIn("localStorage", self.html)

    def test_javascript_syntax(self):
        inline = [text for attrs, text in self.parser.scripts if not attrs.get("src") and attrs.get("type") != "application/json"]
        with tempfile.TemporaryDirectory() as tmp:
            js = Path(tmp) / "app.js"
            js.write_text("\n".join(inline), encoding="utf-8")
            result = subprocess.run(["node", "--check", str(js)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_power_bi_project(self):
        pages = ROOT / "pbip" / "MaintenancePerformanceSuite.Report" / "definition" / "pages"
        page_dirs = [path for path in pages.iterdir() if path.is_dir() and re.fullmatch(r"p\d+", path.name)]
        self.assertEqual(len(page_dirs), 12)
        visual_files = list(pages.rglob("visual.json"))
        self.assertGreaterEqual(len(visual_files), 170)
        for path in list((ROOT / "pbip").rglob("*.json")) + list((ROOT / "pbip").rglob("*.pbir")) + list((ROOT / "pbip").rglob("*.pbism")):
            with self.subTest(path=path.relative_to(ROOT)):
                json.loads(path.read_text(encoding="utf-8"))

    def test_semantic_model(self):
        tables = list((ROOT / "pbip" / "MaintenancePerformanceSuite.SemanticModel" / "definition" / "tables").glob("*.tmdl"))
        self.assertEqual(len(tables), 15)
        measures = (ROOT / "pbip" / "MaintenancePerformanceSuite.SemanticModel" / "definition" / "tables" / "_Medidas.tmdl").read_text(encoding="utf-8")
        self.assertGreaterEqual(len(re.findall(r"^\s*measure\s+", measures, re.MULTILINE)), 40)

    def test_executive_deliverables(self):
        expected = {
            "modelo-semantico.xlsx": ("xl/workbook.xml", 8_000),
            "toolkit-tecnico.docx": ("word/document.xml", 20_000),
            "presentacion-ejecutiva.pptx": ("ppt/presentation.xml", 20_000),
        }
        for filename, (required_member, minimum_size) in expected.items():
            path = ROOT / "deliverables" / filename
            with self.subTest(file=filename):
                self.assertTrue(path.exists(), f"Falta {filename}")
                self.assertGreater(path.stat().st_size, minimum_size)
                with zipfile.ZipFile(path) as package:
                    self.assertIn(required_member, package.namelist())
        with zipfile.ZipFile(ROOT / "deliverables" / "presentacion-ejecutiva.pptx") as package:
            slides = [name for name in package.namelist() if re.fullmatch(r"ppt/slides/slide\d+\.xml", name)]
            self.assertEqual(len(slides), 8)


if __name__ == "__main__":
    unittest.main(verbosity=2)
