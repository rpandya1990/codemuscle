from pathlib import Path

from openpyxl import Workbook

from codemuscle.application.imports.parser import read_tabular_file


def test_read_csv_handles_utf8_bom(tmp_path: Path) -> None:
    path = tmp_path / "problems.csv"
    path.write_text("\ufeffProblem Title,Difficulty\nTwo Sum,Easy\n", encoding="utf-8")

    headers, rows = read_tabular_file(path)

    assert headers == ["Problem Title", "Difficulty"]
    assert rows == [{"Problem Title": "Two Sum", "Difficulty": "Easy"}]


def test_read_xlsx_uses_cached_values_and_never_executes_formulas(tmp_path: Path) -> None:
    path = tmp_path / "problems.xlsx"
    workbook = Workbook()
    worksheet = workbook.active
    assert worksheet is not None
    worksheet.append(["Problem Title", "Notes"])
    worksheet.append(["Binary Search", "=1+1"])
    workbook.save(path)

    headers, rows = read_tabular_file(path)

    assert headers == ["Problem Title", "Notes"]
    assert rows[0]["Problem Title"] == "Binary Search"
    assert rows[0]["Notes"] is None
