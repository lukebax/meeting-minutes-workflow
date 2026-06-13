from __future__ import annotations

import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree


SUPPORTED_TRANSCRIPT_EXTENSIONS = {".txt", ".md", ".vtt", ".docx"}


def extract_transcript_text(source_file: Path) -> str:
    extension = source_file.suffix.lower()
    if extension in {".txt", ".md"}:
        return source_file.read_text(encoding="utf-8")
    if extension == ".vtt":
        return _extract_vtt(source_file.read_text(encoding="utf-8"))
    if extension == ".docx":
        return _extract_docx(source_file)
    raise ValueError(f"Unsupported source file extension: {source_file.suffix}")


def _extract_vtt(vtt_text: str) -> str:
    blocks = re.split(r"\n\s*\n", vtt_text.replace("\ufeff", "").replace("\r\n", "\n").replace("\r", "\n"))
    transcript_lines: list[str] = []
    skip_block = False
    for block in blocks:
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        if not lines:
            continue
        first = lines[0]
        if first == "WEBVTT" or first.startswith(("NOTE", "STYLE", "REGION")):
            skip_block = True
            continue
        if skip_block and "-->" not in block:
            continue
        skip_block = False
        cue_lines = [line for line in lines if not _is_vtt_metadata_line(line)]
        if cue_lines and "-->" not in cue_lines[0] and len(cue_lines) > 1:
            cue_lines = cue_lines[1:]
        text = " ".join(line for line in cue_lines if "-->" not in line)
        text = _clean_vtt_markup(text)
        if text and (not transcript_lines or transcript_lines[-1] != text):
            transcript_lines.append(text)
    return "\n\n".join(transcript_lines)


def _is_vtt_metadata_line(line: str) -> bool:
    return line == "WEBVTT" or "-->" in line


def _clean_vtt_markup(text: str) -> str:
    voice_match = re.match(r"<v\s+([^>]+)>(.*)", text)
    speaker = None
    if voice_match:
        speaker = voice_match.group(1).strip()
        text = voice_match.group(2)
    text = re.sub(r"</?[^>]+>", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    if speaker and text:
        return f"{speaker}: {text}"
    return text


def _extract_docx(source_file: Path) -> str:
    try:
        import mammoth
    except ImportError:
        return _extract_docx_with_stdlib(source_file)

    with source_file.open("rb") as handle:
        result = mammoth.extract_raw_text(handle)
    return result.value.strip()


def _extract_docx_with_stdlib(source_file: Path) -> str:
    namespace = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    with zipfile.ZipFile(source_file) as archive:
        document_xml = archive.read("word/document.xml")
    root = ElementTree.fromstring(document_xml)
    paragraphs: list[str] = []
    for paragraph in root.findall(".//w:p", namespace):
        text = "".join(node.text or "" for node in paragraph.findall(".//w:t", namespace)).strip()
        if text:
            paragraphs.append(text)
    return "\n\n".join(paragraphs)
