# Meeting Minutes Workflow

A Codex-run workflow for turning one transcript into draft meeting outputs for human review.

The transcript workflow produces:

- Transcript
- Overview
- Minutes
- Actions
- Decisions
- Combined document

Markdown is the canonical output format. Matching Word documents are exported from the Markdown files for colleagues who prefer `.docx`.

## Current Status

The transcript-only workflow is implemented and covered by tests. It can prepare a workflow run, validate generated Markdown outputs, assemble the combined output, export Word files when Pandoc is installed, and mark a run as finished.

Audio transcription is not implemented yet. Word export requires Pandoc to be installed on the machine.

## User Guide

For the current end-user workflow, see [HOW_TO_USE.md](./HOW_TO_USE.md).

For the Codex operator checklist, see [docs/RUNBOOK.md](./docs/RUNBOOK.md).

## Project Context

Domain language is captured in [CONTEXT.md](./CONTEXT.md).

Architectural decisions are recorded in [docs/adr/](./docs/adr/).

Implementation research is captured in [docs/IMPLEMENTATION_RESEARCH.md](./docs/IMPLEMENTATION_RESEARCH.md).
