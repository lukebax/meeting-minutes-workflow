# Agent Instructions

This repository is a Codex-run meeting minutes workflow. Before making changes, read:

- `CONTEXT.md` for project language
- `docs/adr/` for architectural decisions
- `docs/PROJECT_PLAN.md` for the implementation plan
- `docs/IMPLEMENTATION_RESEARCH.md` for researched tool recommendations and open technical questions
- `HOW_TO_USE.md` for the intended non-technical user flow

## Documentation Rules

- Keep `CONTEXT.md` as a glossary only. Do not add implementation details, plans, checklists, or specs there.
- Add or update an ADR only for decisions that are hard to reverse, surprising without context, and based on a real trade-off.
- Keep `HOW_TO_USE.md` simple and user-facing.
- Keep `README.md` high-level and repo-facing.
- Update `docs/PROJECT_PLAN.md` when v1 scope or implementation sequencing changes.

## Workflow Rules

- The workflow is Codex-run in v1. Do not add separate LLM API key requirements.
- Python handles deterministic helper work. Codex handles LLM cleanup and summary generation.
- Markdown is canonical. Word documents are exports from Markdown.
- Do not send audio files to an LLM.
- Do not delete user source files.
- Do not copy audio files into generated outputs.
- Preserve only the canonical Transcript as a normal user-facing transcript output.

## Git Hygiene

- Do not commit real meeting recordings, transcripts, or generated outputs.
- `input/` and `outputs/` are kept in Git with `.gitkeep`, but their contents are ignored.
- `.venv/` is ignored and should remain local.
- `.DS_Store` files should not be committed.

## Implementation Notes

- Use Python for v1.
- Use `pyproject.toml` for project configuration.
- Use `pytest` for tests.
- Prefer Pandoc for Markdown-to-`.docx` export unless implementation research finds a strong reason not to.
- Prefer high-quality local transcription over speed.
- Report readiness separately for transcript workflows, audio transcription, and Word export.

## Testing Expectations

When implementation exists, run the relevant tests before finishing changes. Focus tests on deterministic behaviour such as input validation, parsing, output folder naming, Markdown validation, Word export checks, and `run.json` status handling.
