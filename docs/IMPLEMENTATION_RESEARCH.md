# Implementation Research

Research date: 2026-06-12

This document records implementation research for the v1 workflow. It is not a final implementation spec; use it as background for the current transcript and Apple Silicon audio implementation.

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

Current implementation direction:

- Use a standard Python package with `pyproject.toml` and `src/` layout.
- Use `argparse` initially unless CLI complexity grows.
- Use `pytest` configured in `pyproject.toml`.
- Use Mammoth for `.docx` transcript text extraction, with a minimal standard-library fallback only as defensive resilience.
- Use a small custom parser for `.vtt` extraction first, backed by tests.
- Use Pandoc for Markdown-to-`.docx` export.
- Use WhisperKit CLI as the local audio transcription path for this Apple Silicon team.
- Keep large transcription model files in user-level tool caches, not in the repository or `.venv`.

## Python Project Shape

Use `pyproject.toml` as the project configuration file. The Python Packaging User Guide describes it as the place for build backend configuration, project metadata, dependencies, scripts, and tool-specific configuration.

Use `src/meeting_minutes_workflow/` rather than a flat package. The PyPA guide notes that `src/` layout helps avoid accidentally importing code directly from the repository root rather than from the installed package.

Implemented package structure:

```text
pyproject.toml
src/
  meeting_minutes_workflow/
    __init__.py
    __main__.py
    audio.py
    cli.py
    combined.py
    commands.py
    doctor.py
    first_time_setup.py
    run_metadata.py
    setup_readiness.py
    source_material.py
    validation.py
    workflow.py
    workflow_run.py
    extractors/
      __init__.py
    export/
      __init__.py
      docx_tables.py
      pandoc.py
      word.py
scripts/
  setup_project.py
docs/
  SETUP.md
  agents/
tests/
```

Use a console script entry point in `pyproject.toml`, for example:

```toml
[project.scripts]
meeting-minutes = "meeting_minutes_workflow.cli:main"
```

Implemented subcommands:

- `meeting-minutes doctor`
- `meeting-minutes prepare-run --title "..."`
- `meeting-minutes validate-transcript <run-folder>`
- `meeting-minutes validate-markdown <run-folder>`
- `meeting-minutes assemble-combined <run-folder>`
- `meeting-minutes export-docx <run-folder>`
- `meeting-minutes finish-run <run-folder>`

There is no single fully automated `run` command in v1. Codex orchestrates these deterministic Python commands between LLM file-writing steps.

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

Use Mammoth for transcript extraction.

Rationale:

- Mammoth has a direct `extract_raw_text` API that returns raw document text with paragraph breaks.
- The project needs transcript text, not fine Word styling.
- Mammoth is pip-installable and focused on converting/extracting from `.docx`.

The current implementation falls back to direct `.docx` XML paragraph extraction from the Python standard library only if Mammoth is not available in the environment. `python-docx` remains another fallback candidate if real Teams exports need more structure-aware traversal.

Current status: Mammoth is a normal project dependency in `pyproject.toml` and is installed in the project `.venv`. Basic `.docx` extraction is implemented and covered by small synthetic `.docx` tests. Real Teams-style `.docx` transcript validation remains a follow-up when a representative file is available.

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

Implemented export command shape:

```text
pandoc --from gfm --to docx --standalone --reference-doc reference.docx input.md --output output.docx
```

The Word export module generates a minimal reference `.docx` in the system temporary directory and post-processes generated `.docx` files so bullet lists render visibly in Word, action tables keep stable widths, and Pandoc heading bookmarks are removed. The Pandoc module is the local command adapter. Markdown remains canonical.

Validate after export:

- expected `.docx` file exists
- file size is greater than zero
- file is a valid Word package
- when Pandoc is available, Pandoc can read the `.docx` back

Manual review should still inspect `docx/combined.docx` for obvious readability problems after real workflow runs.

## Local Audio Transcription

### Recommended Candidate for This Team: WhisperKit CLI

Treat WhisperKit CLI as the recommended transcription path for this team's v1 audio workflow.

Reasons:

- All intended users are on relatively modern Apple Silicon Macs.
- It is Apple-native and can use Apple compute units, including Neural Engine-oriented defaults.
- MacWhisper's fast local model options are also WhisperKit/Apple-native, so this path matches the observed performance profile better than CPU-only transcription.
- It is installed as a normal Homebrew command-line tool, outside the repository and outside Codex.
- Models are stored in a persistent user-level folder, not in the repository.
- The CLI supports common audio formats used by this workflow, including `.wav`, `.mp3`, `.m4a`, and `.flac`.

Installed during spike:

```text
/opt/homebrew/bin/whisperkit-cli
```

Persistent model folder used during spike:

```text
~/Library/Application Support/WhisperKit/Models
```

Model tested:

```text
large-v3-v20240930_turbo
```

Direct CLI shape used during spike:

```text
whisperkit-cli transcribe \
  --audio-path input/test_audio.m4a \
  --model-path "$HOME/Library/Application Support/WhisperKit/Models/models/argmaxinc/whisperkit-coreml/openai_whisper-large-v3-v20240930_turbo" \
  --language en
```

Performance observed on the user's M2 Pro MacBook Pro:

- First 5 minute run, including first-use model setup: about 198 seconds.
- Repeated 5 minute run using the installed model: about 17 seconds.
- Full 33 minute 49 second `.m4a` recording using the installed model: about 100 seconds.
- Temporary 30 second `.wav`, `.mp3`, and `.flac` excerpts generated from the same recording also transcribed successfully.
- Raw transcript quality looked plausible for meeting use, though Codex cleanup is still needed for punctuation, names, acronyms, and lightly cleaned transcript formatting.

This performance is much closer to MacWhisper than the earlier CPU-only `faster-whisper` spike and is the current preferred implementation path.

### Earlier Baseline: `faster-whisper`

`faster-whisper` was tested first because it is Python-native and portable, but it should not be the v1 default for this Apple Silicon team unless WhisperKit later proves unsuitable.

Spike update, 2026-06-13:

- `faster-whisper==1.2.1` installed successfully in a temporary Python 3.14.5 virtual environment on this Apple Silicon machine.
- Installed native dependencies included `ctranslate2==4.8.0`, `av==17.1.0`, `onnxruntime==1.26.0`, `tokenizers==0.23.1`, and `numpy==2.4.6`.
- Import checks passed for `faster_whisper`, CTranslate2, PyAV, and ONNX Runtime.
- A `tiny.en` model downloaded to `/private/tmp` and loaded successfully with `device="cpu"` and `compute_type="int8"`.
- The temporary Python environment used about 228 MiB. The downloaded `tiny.en` model used about 74 MiB.
- A local synthetic speech attempt using macOS `say` produced empty audio containers in this environment, so transcription quality has not yet been tested.
- The `large-v3` model downloaded and loaded successfully with `device="cpu"` and `compute_type="int8"`. It is cached under the normal Hugging Face user cache at `~/.cache/huggingface/hub` and uses about 2.9 GiB.
- A real 33 minute 49 second `.m4a` recording was available for testing. A one-minute excerpt transcribed successfully in about 26 seconds and produced plausible meeting text.
- A five-minute excerpt transcribed successfully in about 139 seconds and produced 36 timestamped transcript lines.
- A full-file single-call transcription was attempted, but it produced no progress output for many minutes and was interrupted after it had reached roughly the first 15 minutes of audio. The underlying transcription worked, but the integration should write incrementally and report progress rather than making one long silent call.
- Raw transcription quality was plausible for meeting use, but imperfect on names, acronyms, and unclear phrases. The existing Codex Transcript cleanup step remains necessary before summary outputs are generated.

Model metadata checked through Hugging Face on 2026-06-13:

| Model | Approximate download size |
|---|---:|
| `Systran/faster-whisper-tiny.en` | 75 MiB |
| `Systran/faster-whisper-base.en` | 141 MiB |
| `Systran/faster-whisper-small.en` | 464 MiB |
| `Systran/faster-whisper-medium.en` | 1.4 GiB |
| `Systran/faster-whisper-large-v3` | 2.9 GiB |

Accuracy should still be prioritized over speed for real meeting use, but Apple-native acceleration is now a requirement for practical runtime on long meetings.

Implementation update: WhisperKit CLI is integrated into `prepare-run` for supported audio source material. The helper writes `.work/extracted-transcript.txt`, records engine, model, model path, and elapsed seconds in `run.json`, and prints elapsed-time progress while transcription is running.

Operational note: in the Codex managed sandbox, WhisperKit may abort if Apple runtime cache writes under `~/Library/Caches/whisperkit-cli` are blocked. The workflow reports this as an actionable local cache-permission error. Rerunning `prepare-run` with approval for WhisperKit cache access resolves the issue without sending audio to an LLM.

Audio validation update, 2026-06-13: the full workflow ran successfully end to end from the real `.m4a` recording through cleaned Transcript, summary Markdown, combined output, Word export, and final `run.json` status. The raw WhisperKit transcript was plausible for meeting use after Codex cleanup. The main remaining audio limitation is the lack of speaker diarisation, so Actions and speaker-linked details must remain conservative when attribution is unclear.

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

Use as fallback if WhisperKit CLI proves unsuitable on the target Apple Silicon machines.

#### MLX Whisper

Pros:

- Potentially attractive for Apple Silicon acceleration.

Cons:

- Apple-specific, like the chosen WhisperKit direction.
- Adds another model/runtime family to set up and document.

Consider only if WhisperKit CLI stops meeting the team's accuracy or speed needs.

## Audio Format Support

WhisperKit CLI documents support for `.wav`, `.mp3`, `.m4a`, and `.flac`. The workflow supports those formats in v1. A real `.m4a` recording and temporary `.wav`, `.mp3`, and `.flac` excerpts have been smoke-tested successfully.

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
Audio transcription: not ready - WhisperKit CLI found, model not found at the configured model path
Word export: not ready - pandoc not found
```

First-time setup is handled by `scripts/setup_project.py` plus Codex approval for system-level work. The setup helper should:

- create `.venv`
- install project dependencies
- run `doctor`
- report whether Pandoc is missing
- report whether `whisperkit-cli` or the WhisperKit Large v3 Turbo model is missing

Codex should ask before installing Homebrew tools or preparing large model files. Do not silently install system-level tools.

## Testing Priorities

Create tests before or alongside implementation for:

- input folder contains exactly one non-placeholder source file
- `.txt` extraction
- `.md` extraction
- `.vtt` timestamp removal
- `.vtt` voice span preservation
- `.vtt` obvious duplicate removal
- `.docx` extraction with a small fixture
- output folder naming and numbering
- source hash calculation
- run metadata writes and status transitions
- transcript minimum word validation
- Markdown file validation
- Pandoc missing produces a clear doctor failure
- Word export creates non-empty `.docx` when Pandoc is available
- audio source material invokes WhisperKit CLI and writes `.work/extracted-transcript.txt`
- audio transcription metadata is recorded in `run.json`
- failed audio transcription writes a failed `run.json` without claiming generated transcript files

Keep Pandoc-dependent tests isolated from the local machine state. Unit tests should be able to fake Pandoc; any real Pandoc smoke checks should skip clearly when Pandoc is not installed.

## Implementation Status Notes

As of the current implementation pass:

- `pyproject.toml` and the `src/` package layout exist.
- Deterministic helpers exist for Workflow Run layout, prepare metadata, and stage gates; typed Source Material intake; transcript extraction; local WhisperKit audio transcription; setup readiness; validation; combined-output assembly; Word export; `doctor`; and `run.json`.
- Readiness checks carry user-facing display labels with their readiness facts so setup and `doctor` do not duplicate label knowledge.
- A first-time setup helper exists at `scripts/setup_project.py`, with package implementation in `meeting_minutes_workflow.first_time_setup`.
- The command runbook lives in [RUNBOOK.md](./RUNBOOK.md).
- First-time setup instructions live in [SETUP.md](./SETUP.md), and the non-technical user flow lives in [HOW_TO_USE.md](../HOW_TO_USE.md).
- The transcript path has been proven end to end on a `.txt` transcript.
- The transcript path has been proven end to end on a synthetic Teams-style `.vtt` transcript.
- The `.vtt` extractor removes timestamp and metadata noise, preserves speaker labels, and now removes obvious rolling caption fragments while preserving genuine repeated statements.
- Basic `.docx` extraction exists, but real Teams-style `.docx` transcript validation remains open until a real sample is available.
- Audio transcription with WhisperKit CLI is implemented in `prepare-run` and has been tested on a real `.m4a` recording through cleaned Transcript, summary Markdown, combined output, Word export, and final successful `run.json`.

## Decisions and Follow-ups

- Whether additional progress detail is needed for very long recordings.
- Whether the current `.docx` extraction approach is sufficient for real Teams `.docx` transcripts when a sample is available.
- Whether the current generated reference `.docx` is sufficient on target machines or should later become a custom organisation template.
- Whether setup should eventually become a first-class CLI command instead of a repository script.

## Immediate Next Build Step

Validate setup from a clean checkout on a second Apple Silicon Mac, including the Codex project shape: **Use an existing folder**, one setup chat, then one new chat per meeting.

Keep real Teams-style `.docx` transcript validation as a follow-up when a representative file is available.
