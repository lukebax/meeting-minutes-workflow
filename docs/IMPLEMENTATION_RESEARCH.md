# Implementation Research

Research date: 2026-06-12

This document records first-pass implementation research for the v1 workflow. It is not a final implementation spec; use it as background for the current transcript-only implementation and remaining technical spikes.

## Local Environment Observed

On the current machine:

- CPU architecture: `arm64`
- Python: `3.14.5`
- `ffmpeg`: present at `/opt/homebrew/bin/ffmpeg`
- `pandoc`: initially absent during research; later installed via Homebrew at `/opt/homebrew/bin/pandoc`

Python 3.14 is very new relative to many ML/audio packages. During implementation, verify dependency compatibility before assuming the local default Python is the right interpreter for `.venv`. If wheels are missing or installs become fragile, prefer a more widely supported Python such as 3.12 or 3.13 for the project environment.

## Sources Checked

- [OpenAI Whisper GitHub](https://github.com/openai/whisper)
- [SYSTRAN faster-whisper GitHub](https://github.com/SYSTRAN/faster-whisper)
- [ggml-org whisper.cpp GitHub](https://github.com/ggml-org/whisper.cpp)
- [Pandoc website](https://pandoc.org/)
- [Pandoc installing guide](https://pandoc.org/installing.html)
- [Pandoc manual](https://pandoc.org/MANUAL.html)
- [Mammoth Python GitHub](https://github.com/mwilliamson/python-mammoth)
- [python-docx docs](https://python-docx.readthedocs.io/en/latest/)
- [Python Packaging User Guide: pyproject.toml](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/)
- [Python Packaging User Guide: virtual environments](https://packaging.python.org/en/latest/guides/installing-using-pip-and-virtual-environments/)
- [Python Packaging User Guide: src layout](https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/)
- [pytest configuration docs](https://docs.pytest.org/en/stable/reference/customize.html)
- [W3C WebVTT specification](https://www.w3.org/TR/webvtt1/)

## Recommendation Summary

For the first implementation:

- Use a standard Python package with `pyproject.toml` and `src/` layout.
- Use `argparse` initially unless CLI complexity grows.
- Use `pytest` configured in `pyproject.toml`.
- Use Mammoth for `.docx` transcript text extraction.
- Use a small custom parser for `.vtt` extraction first, backed by tests.
- Use Pandoc for Markdown-to-`.docx` export.
- Treat `faster-whisper` as the leading local transcription candidate.
- Build transcript-only v1 first; add audio transcription after the deterministic workflow is solid.

## Python Project Shape

Use `pyproject.toml` as the project configuration file. The Python Packaging User Guide describes it as the place for build backend configuration, project metadata, dependencies, scripts, and tool-specific configuration.

Use `src/meeting_minutes_workflow/` rather than a flat package. The PyPA guide notes that `src/` layout helps avoid accidentally importing code directly from the repository root rather than from the installed package.

Suggested starting structure:

```text
pyproject.toml
src/
  meeting_minutes_workflow/
    __init__.py
    __main__.py
    cli.py
    paths.py
    run_metadata.py
    inputs.py
    extractors/
      __init__.py
      txt.py
      markdown.py
      vtt.py
      docx.py
    export/
      __init__.py
      pandoc.py
    validation.py
tests/
```

Use a console script entry point in `pyproject.toml`, for example:

```toml
[project.scripts]
meeting-minutes = "meeting_minutes_workflow.cli:main"
```

Conceptual subcommands:

- `meeting-minutes setup`
- `meeting-minutes doctor`
- `meeting-minutes prepare-run --title "..."`
- `meeting-minutes validate-markdown <run-folder>`
- `meeting-minutes export-docx <run-folder>`
- `meeting-minutes finish-run <run-folder>`

The exact command names can change during implementation. The key design point is that Codex can orchestrate deterministic Python commands between LLM file-writing steps.

## Transcript Input Extraction

### `.txt`

Use Python standard library text reading. Detect or default to UTF-8, and fail clearly if decoding fails.

### `.md`

Read as text and preserve structure. Do not parse Markdown deeply for v1. The Codex cleanup prompt can lightly standardise it into `markdown/transcript.md`.

### `.vtt`

Use a small custom extractor first, backed by tests.

Rationale:

- WebVTT is a structured text format with cues, timings, optional identifiers, notes, style blocks, and voice spans.
- The project only needs plain transcript extraction, not browser-accurate cue rendering.
- A custom extractor keeps dependencies low and makes Teams-specific quirks easy to test.

Extraction rules:

- Skip `WEBVTT` header lines.
- Skip cue timing lines.
- Skip cue identifiers when obvious.
- Skip `NOTE`, `STYLE`, and metadata blocks unless real transcript text appears.
- Preserve cue text.
- Convert WebVTT voice spans like `<v Speaker Name>Text` into `Speaker Name: Text` where practical.
- Strip basic markup such as `<i>` while preserving the text.
- Remove obvious repeated subtitle fragments where mechanical duplication is clear.

The W3C WebVTT examples confirm that cue text can include voice spans such as `<v Roger Bingham>...`, and cues are tied to time intervals.

### `.docx`

Prefer Mammoth for transcript extraction.

Rationale:

- Mammoth has a direct `extract_raw_text` API that returns raw document text with paragraph breaks.
- The project needs transcript text, not fine Word styling.
- Mammoth is pip-installable and focused on converting/extracting from `.docx`.

`python-docx` remains a fallback candidate. It is good for creating/updating Word documents and can read paragraphs/tables, but raw transcript extraction would require more manual traversal.

## Canonical Transcript

Do not use parser output directly as the canonical Transcript.

Extractor output should go to the hidden working area:

```text
outputs/<run>/.work/extracted-transcript.txt
```

Codex then uses `prompts/transcript-cleanup.md` to write:

```text
outputs/<run>/markdown/transcript.md
```

Validation should fail before summarisation if the canonical Transcript has fewer than 10 words after cleanup.

## Word Export

Use Pandoc as the preferred Markdown-to-`.docx` exporter.

Rationale:

- Pandoc describes itself as a universal document converter and supports Markdown and Microsoft Word `.docx`.
- Pandoc can later support reference `.docx` styling if custom templates become desirable after v1.
- Pandoc is an external tool, so `doctor` must check for it.

Current machine status: `pandoc` is installed at `/opt/homebrew/bin/pandoc`.

On macOS, Pandoc documents Homebrew as an installation option:

```text
brew install pandoc
```

Do not install Pandoc silently. Setup should explain that Word export requires Pandoc and ask for user approval before installing it.

Initial export command shape:

```text
pandoc --from gfm --to docx --standalone --output output.docx input.md
```

Validate after export:

- expected `.docx` file exists
- file size is greater than zero

Do not attempt deep Word rendering validation in v1.

## Local Audio Transcription

### Leading Candidate: `faster-whisper`

Treat `faster-whisper` as the leading candidate for the audio spike.

Reasons:

- It is Python-first, which fits this project.
- It reimplements Whisper using CTranslate2.
- Its README claims up to 4x faster inference than `openai/whisper` for the same accuracy, with lower memory usage.
- It supports CPU and GPU modes.
- Its usage is straightforward from Python:

```python
from faster_whisper import WhisperModel

model = WhisperModel("large-v3", device="cpu", compute_type="int8")
segments, info = model.transcribe("audio.mp3", beam_size=5)
```

Important nuance: unlike `openai-whisper`, `faster-whisper` says system FFmpeg does not need to be installed because audio is decoded with PyAV, which bundles FFmpeg libraries. Keep `ffmpeg` checks as potentially useful for future media handling, but do not assume `ffmpeg` is required if `faster-whisper` is chosen.

Model recommendation for the spike:

- Start with `large-v3` because accuracy is the priority.
- Force or default language to English where the API supports it.
- Use CPU `int8` as the broad compatibility baseline.
- Detect Apple Silicon and investigate whether a better local backend is warranted after baseline works.

Open question: Python 3.14 compatibility may be a practical blocker because `faster-whisper` depends on packages such as CTranslate2, PyAV, ONNX Runtime, tokenizers, and Hugging Face Hub. Validate installability in `.venv` before committing.

### Alternatives

#### `openai-whisper`

Pros:

- Official OpenAI open-source Whisper implementation.
- Simple Python and CLI usage.
- MIT-licensed code and model weights.

Cons:

- Requires system `ffmpeg`.
- PyTorch dependency can be heavier.
- May be slower or heavier than `faster-whisper` for this use.

Use as fallback or comparison baseline.

#### `whisper.cpp`

Pros:

- C/C++ implementation with low-level performance focus.
- Supports quantized models and many hardware/backend options.
- Strong option for CPU/local binary usage.

Cons:

- Less Python-native.
- Setup/build/binary management may be more involved.
- Python orchestration would likely shell out to a binary rather than use a clean Python API.

Use as fallback if `faster-whisper` installability or performance is poor.

#### MLX Whisper

Pros:

- Potentially attractive for Apple Silicon acceleration.

Cons:

- Apple-specific, which may conflict with colleague-machine variability.
- Should not be the only v1 path unless all intended users are on compatible Macs.

Consider as a later optimization, not the v1 baseline.

## Audio Format Support

Do not document promised audio extensions until after the transcription spike.

If `faster-whisper` is adopted, supported input formats are likely governed by PyAV/FFmpeg decoding support. The user guide should still list a small recommended set after validation, for example `.mp3`, `.m4a`, and `.wav`, while saying unsupported formats fail clearly.

## Setup and Doctor

`doctor` should report separately:

- Python project environment
- transcript workflow
- audio transcription
- Pandoc/Word export

Example:

```text
Python environment: ready
Transcript workflow: ready
Audio transcription: not ready - model not downloaded
Word export: not ready - pandoc not found
```

Setup should:

- create `.venv`
- install project dependencies
- run `doctor`
- offer to install Pandoc if missing
- later offer to download the transcription model if audio support is being set up

Do not silently install system-level tools.

## Testing Priorities

Create tests before or alongside implementation for:

- input folder contains exactly one non-placeholder source file
- `.txt` extraction
- `.md` extraction
- `.vtt` timestamp removal
- `.vtt` voice span preservation
- `.vtt` obvious duplicate removal
- Mammoth `.docx` extraction with a small fixture
- output folder naming and numbering
- source hash calculation
- run metadata writes and status transitions
- transcript minimum word validation
- Markdown file validation
- Pandoc missing produces a clear doctor failure
- Pandoc export creates non-empty `.docx` when Pandoc is available

Keep Pandoc-dependent tests isolated from the local machine state. Unit tests should be able to fake Pandoc; any real Pandoc smoke checks should skip clearly when Pandoc is not installed.

## Implementation Status Notes

As of the first transcript-only implementation pass:

- `pyproject.toml` and the `src/` package layout exist.
- Deterministic helpers exist for input discovery, output folder numbering, source hashing, transcript extraction, validation, combined-output assembly, Word export, `doctor`, and `run.json`.
- The command runbook lives in [RUNBOOK.md](./RUNBOOK.md).
- The transcript-only path has been proven end to end on a `.txt` transcript.
- Audio transcription has not been implemented.

## Decisions to Make After Spikes

After additional transcript-format validation and the audio transcription spike:

- Whether to adopt `faster-whisper` as the actual v1 transcription dependency.
- Which Python version range to declare in `pyproject.toml`.
- Which audio formats to officially support in `HOW_TO_USE.md`.
- Whether `ffmpeg` remains a doctor dependency or only a nice-to-have diagnostic.
- Whether Mammoth extraction is sufficient for real Teams `.docx` transcripts.
- Whether Pandoc output quality is acceptable without a reference `.docx`.

## Immediate Next Build Step

Validate the transcript-only path against additional realistic source formats, especially `.vtt` and Teams-style `.docx` transcripts. Do audio transcription after the transcript-only path and Word export path are stable.
