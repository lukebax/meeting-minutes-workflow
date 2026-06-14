from __future__ import annotations

import shutil
import tempfile
import zipfile
from pathlib import Path
from xml.etree import ElementTree


WORD_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS = {"w": WORD_NS}
ACTION_TABLE_WIDTHS = [3600, 1000, 1300, 3000]

ElementTree.register_namespace("w", WORD_NS)


def optimise_docx_tables(docx_file: Path) -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir) / docx_file.name
        shutil.copyfile(docx_file, temp_path)
        with zipfile.ZipFile(temp_path) as source:
            document_xml = source.read("word/document.xml")
            entries = {info.filename: source.read(info.filename) for info in source.infolist()}

        root = ElementTree.fromstring(document_xml)
        changed = False
        if _remove_bookmarks(root):
            changed = True
        for table in root.findall(".//w:tbl", NS):
            if _column_count(table) == 4:
                _set_table_widths(table, ACTION_TABLE_WIDTHS)
                changed = True

        if _inline_visible_bullets(root, entries):
            changed = True

        if _normalise_bullet_numbering(entries):
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


def _normalise_bullet_numbering(entries: dict[str, bytes]) -> bool:
    numbering_xml = entries.get("word/numbering.xml")
    if numbering_xml is None:
        return False

    root = ElementTree.fromstring(numbering_xml)
    changed = False
    for level in root.findall(".//w:lvl", NS):
        number_format = level.find("w:numFmt", NS)
        level_text = level.find("w:lvlText", NS)
        if (
            number_format is None
            or level_text is None
            or number_format.get(f"{{{WORD_NS}}}val") != "bullet"
        ):
            continue

        current_marker = level_text.get(f"{{{WORD_NS}}}val", "")
        if current_marker != "\u2022":
            level_text.set(f"{{{WORD_NS}}}val", "\u2022")
            changed = True

        run_properties = _child(level, "rPr")
        fonts = _child(run_properties, "rFonts")
        for attribute in ("ascii", "hAnsi", "cs"):
            qualified_attribute = f"{{{WORD_NS}}}{attribute}"
            if fonts.get(qualified_attribute) != "Arial":
                fonts.set(qualified_attribute, "Arial")
                changed = True

    if changed:
        entries["word/numbering.xml"] = ElementTree.tostring(root, encoding="utf-8", xml_declaration=True)
    return changed


def _inline_visible_bullets(document_root: ElementTree.Element, entries: dict[str, bytes]) -> bool:
    bullet_number_ids = _bullet_number_ids(entries)
    if not bullet_number_ids:
        return False

    changed = False
    for paragraph in document_root.findall(".//w:p", NS):
        properties = paragraph.find("w:pPr", NS)
        if properties is None:
            continue
        numbering = properties.find("w:numPr", NS)
        if numbering is None:
            continue
        number_id = numbering.find("w:numId", NS)
        if number_id is None or number_id.get(f"{{{WORD_NS}}}val") not in bullet_number_ids:
            continue

        properties.remove(numbering)
        bullet_run = ElementTree.Element(f"{{{WORD_NS}}}r")
        bullet_text = ElementTree.SubElement(bullet_run, f"{{{WORD_NS}}}t")
        bullet_text.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
        bullet_text.text = "\u2022 "
        insert_at = 1 if len(paragraph) and paragraph[0] is properties else 0
        paragraph.insert(insert_at, bullet_run)
        changed = True
    return changed


def _bullet_number_ids(entries: dict[str, bytes]) -> set[str]:
    numbering_xml = entries.get("word/numbering.xml")
    if numbering_xml is None:
        return set()

    root = ElementTree.fromstring(numbering_xml)
    bullet_abstract_ids = set()
    for abstract in root.findall("w:abstractNum", NS):
        abstract_id = abstract.get(f"{{{WORD_NS}}}abstractNumId")
        if abstract_id is None:
            continue
        if any(_is_bullet_level(level) for level in abstract.findall("w:lvl", NS)):
            bullet_abstract_ids.add(abstract_id)

    bullet_number_ids = set()
    for number in root.findall("w:num", NS):
        abstract = number.find("w:abstractNumId", NS)
        number_id = number.get(f"{{{WORD_NS}}}numId")
        if abstract is not None and number_id is not None and abstract.get(f"{{{WORD_NS}}}val") in bullet_abstract_ids:
            bullet_number_ids.add(number_id)
    return bullet_number_ids


def _is_bullet_level(level: ElementTree.Element) -> bool:
    number_format = level.find("w:numFmt", NS)
    return number_format is not None and number_format.get(f"{{{WORD_NS}}}val") == "bullet"


def _remove_bookmarks(element: ElementTree.Element) -> bool:
    changed = False
    for child in list(element):
        if child.tag in {f"{{{WORD_NS}}}bookmarkStart", f"{{{WORD_NS}}}bookmarkEnd"}:
            element.remove(child)
            changed = True
        elif _remove_bookmarks(child):
            changed = True
    return changed


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
