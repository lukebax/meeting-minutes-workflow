# Project Plan

This plan consolidates the decisions made before implementation. It is a practical build map, not a PRD.

## v1 Goal

Build a Codex-run workflow that turns one English-language meeting recording or transcript into reviewable meeting outputs for non-technical colleagues.

Current implementation status: the transcript-only path is implemented and tested. Audio transcription remains planned.

The user-facing flow should be:

1. Put exactly one source file in `input/`.
2. Ask Codex to run the workflow and provide a short meeting title.
3. Review the generated files in `outputs/<run>/`.
4. Empty `input/` manually after the run.

The workflow does not delete source files, copy audio into outputs, send audio to an LLM, or manage review/distribution after outputs are produced.

## Core Concepts

Canonical language lives in [CONTEXT.md](../CONTEXT.md). In brief:

- Source material is either a meeting recording or an existing transcript.
- A workflow run handles exactly one meeting.
- The meeting title is the only required user-provided meeting metadata.
- All source material becomes a lightly cleaned Transcript before summary outputs are created.
- Summary outputs are drafts for human review.
- Actions and Decisions must not invent certainty.

## User-Facing Outputs

Each successful run creates:

```text
outputs/
  <run-date>-<meeting-title>/
    run.json
    markdown/
      transcript.md
      overview.md
      minutes.md
      actions.md
      decisions.md
      combined.md
    docx/
      transcript.docx
      overview.docx
      minutes.docx
      actions.docx
      decisions.docx
      combined.docx
```

Markdown is canonical. Word files are exported from Markdown and should contain the same information.

`combined.md` and `combined.docx` assemble the same human-facing content from the separate overview, minutes, actions, and decisions outputs. They are not shorter variants.

Generated outputs are local-only and ignored by Git.

## Supported Inputs

v1 officially supports transcript source files in:

- `.txt`
- `.md`
- `.vtt`
- `.docx`

Unsupported transcript formats should fail with a clear message. There are no best-effort imports in v1.

Audio input is planned, but supported audio formats should be documented only after implementation research chooses the local transcription tool and media stack.

PDF transcript input, pasted transcript text, batching, and multiple source files are out of scope for v1.

## Processing Flow

Codex is the orchestrator. Python provides deterministic helper commands.

The operator checklist for running the current transcript-only workflow is in [RUNBOOK.md](./RUNBOOK.md).

Current transcript-only flow:

1. Check that `input/` contains exactly one supported source file.
2. Create a new output folder using the run date and meeting title.
3. If the source is a transcript file, extract plain working text.
4. Store working artifacts under a hidden `.work/` area inside the run folder.
5. Use Codex to create the canonical `markdown/transcript.md` from the working text.
6. Validate the canonical Transcript has at least 10 words.
7. Use Codex to generate `overview.md`, `minutes.md`, `actions.md`, and `decisions.md` separately.
8. Assemble `combined.md` from the separate summary outputs.
9. Validate expected Markdown files exist and are non-empty.
10. Export matching `.docx` files from Markdown when Pandoc is available.
11. Validate expected `.docx` files exist and are non-empty.
12. Write or update `run.json` with status, source metadata, generated files, and errors if any.

Audio transcription will later add a local transcription step before Transcript cleanup.

If the preferred output folder already exists, create a numbered folder such as `<name>-2` rather than overwriting or failing.

Runs are not resumable in v1. Rerunning creates a new output folder. Failed and incomplete run folders are preserved.

## Codex and Python Split

Python should handle:

- input detection
- source file hashing
- output folder creation and numbering
- `.txt`, `.md`, `.vtt`, and `.docx` text extraction
- local audio transcription integration
- Markdown output validation
- Markdown-to-Word export orchestration
- `.docx` validation
- `run.json`
- setup and doctor checks

Codex should handle:

- transcript cleanup/light standardisation
- overview generation
- minutes generation
- actions generation
- decisions generation
- writing canonical Markdown files directly

The Python command should not call an LLM API directly in v1. The workflow is intentionally Codex-run and does not require users to configure LLM API keys.

## Output Content Rules

All generated summary outputs should use UK English and a clear, neutral, professional, concise tone.

`transcript.md`:

- starts with a title using the meeting title
- is lightly cleaned but not summarized
- removes routine caption timestamps
- preserves speaker labels when available
- does not invent speaker names or speaker turns
- preserves source structure where useful

`overview.md`:

- starts with a title
- uses a short opening sentence followed by structured bullets

`minutes.md`:

- starts with a title
- is topic-based, roughly following meeting order
- includes Open Questions when unresolved questions or deferred choices are present
- does not pretend inferred topics are official agenda items

`actions.md`:

- starts with a title
- uses a table with columns: Action, Owner, Due date, Review note
- includes follow-up work only when clearly stated or strongly implied
- marks unclear owners and due dates visibly
- omits borderline discussion points rather than overstating them

`decisions.md`:

- starts with a title
- uses a short list
- includes only clearly supported choices or conclusions
- excludes proposals, deferred choices, open questions, actions, and completed status updates

## Setup and Dependencies

Use Python for v1, configured with `pyproject.toml`.

Use a repo-local `.venv/` for Python dependencies. Do not commit `.venv/`.

Use separate conceptual commands:

- setup: prepare project-local dependencies and guide larger downloads
- doctor: report readiness
- run: process one meeting

Readiness should be reported separately for:

- transcript workflows
- audio transcription
- Word export

Transcript workflows should work even when audio transcription dependencies are missing.

Large transcription model files should live in the transcription tool's normal user-level cache, not in the repo or `.venv/`.

Setup may download the required transcription model after making that visible to the user.

System-level tools, such as audio decoders and Pandoc, should be detected and explained separately from project-local Python dependencies. Codex may help install them, but installation requires explicit user approval.

## Implementation Research

Initial findings are recorded in [IMPLEMENTATION_RESEARCH.md](./IMPLEMENTATION_RESEARCH.md).

First-pass recommendations:

- use `pyproject.toml` with `src/` layout
- use Mammoth for `.docx` transcript extraction
- use a tested custom `.vtt` parser first
- use Pandoc for Markdown-to-`.docx` export
- treat `faster-whisper` as the leading local transcription candidate
- build the transcript-only path before audio transcription

Validation spikes are still needed for:

- Python version compatibility, especially because this machine currently has Python 3.14
- `faster-whisper` installation and transcription quality
- supported audio formats after the transcription tool is chosen
- whether `ffmpeg` is required or only useful for future media handling
- Mammoth extraction quality on real Teams `.docx` transcripts
- Pandoc installation and output quality on target machines

Local transcription must prioritize accuracy over speed for short and long meetings. There is no fixed meeting-length limit.

## Testing Plan

Use `pytest`.

Start with deterministic tests:

- input folder has exactly one source file
- zero or multiple input files fail clearly
- unsupported source extensions fail clearly
- output folder names use run date and meeting title
- duplicate output folders are numbered
- source file hash is recorded
- `.vtt` extraction removes timestamps and preserves speaker labels
- obvious `.vtt` subtitle duplication is removed where possible
- `.docx` transcript extraction produces working text
- canonical Transcript validation fails below 10 words
- expected Markdown outputs are non-empty before Word export
- Pandoc export creates expected non-empty `.docx` files
- `run.json` records success, incomplete, and failed statuses

LLM output quality should be guided by prompt files and reviewed manually at first. Avoid brittle tests that assert exact LLM prose.

## Planned Repository Shape

```text
.
  AGENTS.md
  CONTEXT.md
  HOW_TO_USE.md
  README.md
  LICENSE
  pyproject.toml
  input/
    .gitkeep
  outputs/
    .gitkeep
  prompts/
    transcript-cleanup.md
    overview.md
    minutes.md
    actions.md
    decisions.md
  docs/
    PROJECT_PLAN.md
    adr/
  src/
    meeting_minutes_workflow/
  tests/
```

Prompt files are instruction files. `combined.md` is assembled deterministically from the separate summary outputs.

## Out of Scope for v1

- GUI or web app
- standalone non-Codex LLM provider configuration
- separate LLM API keys
- sending audio files to an LLM
- custom organisation Word templates
- configurable output language or writing style
- non-English meeting support
- PDF transcript input
- pasted transcript text as source material
- batch processing multiple meetings
- review/sign-off workflow
- automatic deletion or cleanup of source files
- automatic sharing by email, Teams, or other tools
- task-manager exports such as Planner, Trello, Jira, or CSV
- debug mode or exposed intermediate files
- resumable runs
- token/cost reporting
- synthetic examples before the real workflow can generate them

## Next Steps

1. Test additional transcript formats, especially `.vtt` and real Teams-style `.docx` transcripts.
2. Add or document setup support for creating `.venv` and installing Python dependencies from a clean checkout.
3. Decide whether to keep the current Codex-run Markdown generation as v1 or add more automation around prompt execution.
4. Research and integrate local audio transcription after the transcript-only path is stable across supported transcript formats.
5. Publish the repository to GitHub when the transcript-only workflow, docs, and example-free Git hygiene are coherent.
