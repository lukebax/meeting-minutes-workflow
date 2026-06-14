from __future__ import annotations

import tempfile
import zipfile
from collections.abc import Callable
from pathlib import Path

from meeting_minutes_workflow.export.docx_tables import optimise_docx_tables
from meeting_minutes_workflow.export.pandoc import run_pandoc_to_docx
from meeting_minutes_workflow.validation import EXPECTED_MARKDOWN_OUTPUTS


Runner = Callable[[list[str]], None]


def export_markdown_to_word(
    markdown_file: Path,
    docx_file: Path,
    *,
    reference_doc: Path | None = None,
    runner: Runner | None = None,
) -> None:
    if reference_doc is None:
        reference_doc = ensure_reference_doc()
    run_pandoc_to_docx(markdown_file, docx_file, reference_doc=reference_doc, runner=runner)
    optimise_docx_tables(docx_file)


def export_run_markdown_to_word(run_folder: Path, *, runner: Runner | None = None) -> None:
    reference_doc = ensure_reference_doc()
    for markdown_filename in EXPECTED_MARKDOWN_OUTPUTS:
        markdown_file = run_folder / "markdown" / markdown_filename
        docx_file = run_folder / "docx" / markdown_filename.replace(".md", ".docx")
        export_markdown_to_word(markdown_file, docx_file, reference_doc=reference_doc, runner=runner)


def ensure_reference_doc() -> Path:
    reference_doc = Path(tempfile.gettempdir()) / "meeting-minutes-workflow" / "reference.docx"
    if reference_doc.is_file():
        return reference_doc
    reference_doc.parent.mkdir(parents=True, exist_ok=True)
    _write_minimal_reference_doc(reference_doc)
    return reference_doc


def _write_minimal_reference_doc(path: Path) -> None:
    files = {
        "[Content_Types].xml": """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
  <Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
</Types>
""",
        "_rels/.rels": """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>
""",
        "word/_rels/document.xml.rels": """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"/>
""",
        "word/document.xml": """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
    <w:p><w:r><w:t>Reference document</w:t></w:r></w:p>
    <w:sectPr>
      <w:pgSz w:w="11906" w:h="16838"/>
      <w:pgMar w:top="1440" w:right="1080" w:bottom="1440" w:left="1080" w:header="720" w:footer="720" w:gutter="0"/>
    </w:sectPr>
  </w:body>
</w:document>
""",
        "word/styles.xml": """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:style w:type="paragraph" w:default="1" w:styleId="Normal">
    <w:name w:val="Normal"/>
    <w:qFormat/>
    <w:rPr><w:rFonts w:ascii="Arial" w:hAnsi="Arial"/><w:sz w:val="22"/></w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="Heading1">
    <w:name w:val="heading 1"/>
    <w:basedOn w:val="Normal"/>
    <w:next w:val="Normal"/>
    <w:qFormat/>
    <w:pPr><w:spacing w:before="360" w:after="160"/></w:pPr>
    <w:rPr><w:rFonts w:ascii="Arial" w:hAnsi="Arial"/><w:b/><w:color w:val="0F4C5C"/><w:sz w:val="34"/></w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="Heading2">
    <w:name w:val="heading 2"/>
    <w:basedOn w:val="Normal"/>
    <w:next w:val="Normal"/>
    <w:qFormat/>
    <w:pPr><w:spacing w:before="280" w:after="120"/></w:pPr>
    <w:rPr><w:rFonts w:ascii="Arial" w:hAnsi="Arial"/><w:b/><w:color w:val="0F4C5C"/><w:sz w:val="28"/></w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="Heading3">
    <w:name w:val="heading 3"/>
    <w:basedOn w:val="Normal"/>
    <w:next w:val="Normal"/>
    <w:qFormat/>
    <w:pPr><w:spacing w:before="220" w:after="80"/></w:pPr>
    <w:rPr><w:rFonts w:ascii="Arial" w:hAnsi="Arial"/><w:b/><w:color w:val="0F4C5C"/><w:sz w:val="24"/></w:rPr>
  </w:style>
  <w:style w:type="table" w:default="1" w:styleId="Table">
    <w:name w:val="Table"/>
    <w:tblPr>
      <w:tblInd w:w="0" w:type="dxa"/>
      <w:tblCellMar>
        <w:top w:w="100" w:type="dxa"/>
        <w:left w:w="100" w:type="dxa"/>
        <w:bottom w:w="100" w:type="dxa"/>
        <w:right w:w="100" w:type="dxa"/>
      </w:tblCellMar>
      <w:tblBorders>
        <w:top w:val="single" w:sz="4" w:space="0" w:color="D9E2E7"/>
        <w:left w:val="single" w:sz="4" w:space="0" w:color="D9E2E7"/>
        <w:bottom w:val="single" w:sz="4" w:space="0" w:color="D9E2E7"/>
        <w:right w:val="single" w:sz="4" w:space="0" w:color="D9E2E7"/>
        <w:insideH w:val="single" w:sz="4" w:space="0" w:color="D9E2E7"/>
        <w:insideV w:val="single" w:sz="4" w:space="0" w:color="D9E2E7"/>
      </w:tblBorders>
    </w:tblPr>
  </w:style>
</w:styles>
""",
    }
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        for filename, content in files.items():
            archive.writestr(filename, content)
