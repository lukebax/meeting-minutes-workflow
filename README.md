# Meeting Minutes Workflow

A Codex-run workflow for turning one meeting recording or transcript into draft meeting outputs for human review.

The workflow produces:

- Transcript
- Overview
- Minutes
- Actions
- Decisions
- Combined document

Markdown is the canonical output format. Matching Word documents are exported from the Markdown files for colleagues who prefer `.docx`.

## Current Status

Transcript inputs are implemented and covered by tests. Local audio transcription is implemented for Apple Silicon Macs using WhisperKit CLI. The workflow can prepare a workflow run, validate generated Markdown outputs, assemble the combined output, export Word files when Pandoc is installed, and mark a run as finished.

Word export requires Pandoc. Meeting recordings require Apple Silicon, WhisperKit CLI, and the configured local WhisperKit model. The setup helper checks these areas and tells Codex what still needs approval or installation.

## User Guide

For the current end-user workflow, see [HOW_TO_USE.md](./HOW_TO_USE.md).

In Codex, create the project with **Use an existing folder** and select this repository folder. Use one setup chat, then one new chat per meeting.

For first-time Codex setup from a fresh clone, see [docs/SETUP.md](./docs/SETUP.md).

For the Codex operator checklist, see [docs/RUNBOOK.md](./docs/RUNBOOK.md).

## Project Context

Domain language is captured in [CONTEXT.md](./CONTEXT.md).

Architectural decisions are recorded in [docs/adr/](./docs/adr/).

Implementation research is captured in [docs/IMPLEMENTATION_RESEARCH.md](./docs/IMPLEMENTATION_RESEARCH.md).
