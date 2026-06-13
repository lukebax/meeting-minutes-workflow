from __future__ import annotations

import shutil
import tempfile
import zipfile
from pathlib import Path
from xml.etree import ElementTree


WORD_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS = {"w": WORD_NS}
ACTION_TABLE_WIDTHS = [3600, 1000, 1300, 3000]


def optimise_docx_tables(docx_file: Path) -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir) / docx_file.name
        shutil.copyfile(docx_file, temp_path)
        with zipfile.ZipFile(temp_path) as source:
            document_xml = source.read("word/document.xml")
            entries = {info.filename: source.read(info.filename) for info in source.infolist()}

        root = ElementTree.fromstring(document_xml)
        changed = False
        for table in root.findall(".//w:tbl", NS):
            if _column_count(table) == 4:
                _set_table_widths(table, ACTION_TABLE_WIDTHS)
                changed = True

        if not changed:
            return

        entries["word/document.xml"] = ElementTree.tostring(root, encoding="utf-8", xml_declaration=True)
        with zipfile.ZipFile(docx_file, "w", zipfile.ZIP_DEFLATED) as output:
            for filename, content in entries.items():
                output.writestr(filename, content)


def _column_count(table: ElementTree.Element) -> int:
    first_row = table.find("w:tr", NS)
    if first_row is None:
        return 0
    return len(first_row.findall("w:tc", NS))


def _set_table_widths(table: ElementTree.Element, widths: list[int]) -> None:
    table_properties = _child(table, "tblPr", before=table[0] if len(table) else None)
    table_width = _child(table_properties, "tblW")
    table_width.set(f"{{{WORD_NS}}}type", "dxa")
    table_width.set(f"{{{WORD_NS}}}w", str(sum(widths)))
    table_layout = _child(table_properties, "tblLayout")
    table_layout.set(f"{{{WORD_NS}}}type", "fixed")

    grid = table.find("w:tblGrid", NS)
    if grid is None:
        grid = ElementTree.Element(f"{{{WORD_NS}}}tblGrid")
        table.insert(1 if table.find("w:tblPr", NS) is not None else 0, grid)
    grid.clear()
    for width in widths:
        column = ElementTree.SubElement(grid, f"{{{WORD_NS}}}gridCol")
        column.set(f"{{{WORD_NS}}}w", str(width))

    for row in table.findall("w:tr", NS):
        for index, cell in enumerate(row.findall("w:tc", NS)):
            cell_properties = _child(cell, "tcPr", before=cell[0] if len(cell) else None)
            cell_width = _child(cell_properties, "tcW")
            cell_width.set(f"{{{WORD_NS}}}type", "dxa")
            cell_width.set(f"{{{WORD_NS}}}w", str(widths[index]))


def _child(parent: ElementTree.Element, tag: str, *, before: ElementTree.Element | None = None) -> ElementTree.Element:
    qualified = f"{{{WORD_NS}}}{tag}"
    existing = parent.find(f"w:{tag}", NS)
    if existing is not None:
        return existing
    child = ElementTree.Element(qualified)
    if before is not None:
        parent.insert(list(parent).index(before), child)
    else:
        parent.append(child)
    return child
