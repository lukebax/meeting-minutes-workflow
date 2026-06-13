# Codex Runbook

This runbook is for Codex agents operating the transcript-only meeting minutes workflow. The user-facing instructions live in [HOW_TO_USE.md](../HOW_TO_USE.md).

## Scope

This runbook covers the current v1 transcript workflow for one source file in `input/`.

Supported transcript source formats:

- `.txt`
- `.md`
- `.vtt`
- `.docx`

Audio transcription is not implemented yet. Do not process audio source material as part of this runbook.

## Before Starting

1. Read [AGENTS.md](../AGENTS.md), [CONTEXT.md](../CONTEXT.md), and this runbook.
2. Confirm there is exactly one source file in `input/`.
3. Confirm the user supplied a Meeting Title.
4. Run:

```bash
.venv/bin/meeting-minutes doctor
.venv/bin/python -m pytest
```

Proceed when transcript workflow readiness is ready and tests pass. Word export requires Pandoc readiness. If Pandoc is not ready, continue through Markdown validation but do not run `export-docx` or `finish-run`; report that Word export is blocked.

## Run Sequence

Replace `{title}` with the user's Meeting Title.

```bash
.venv/bin/meeting-minutes prepare-run --title "{title}"
```

Use the run folder path printed by the command as `{run}` for all later steps.

The command creates:

```text
{run}/
  run.json
  .work/extracted-transcript.txt
  markdown/
  docx/
```

## Generate Markdown Outputs

Codex first writes:

```text
{run}/markdown/transcript.md
```

Then validate the Transcript before generating summary outputs:

```bash
.venv/bin/meeting-minutes validate-transcript "{run}"
```

After transcript validation passes, Codex writes:

```text
{run}/markdown/overview.md
{run}/markdown/minutes.md
{run}/markdown/actions.md
{run}/markdown/decisions.md
```

Use the prompt files in `prompts/`:

- `prompts/transcript-cleanup.md`
- `prompts/overview.md`
- `prompts/minutes.md`
- `prompts/actions.md`
- `prompts/decisions.md`

Important rules:

- `transcript.md` must be transcript-like and roughly proportional to the source. Do not summarize it into meeting minutes.
- `overview.md`, `minutes.md`, `actions.md`, and `decisions.md` must be based on the validated `transcript.md`, not directly on `.work/extracted-transcript.txt`.
- Be conservative with Actions and Decisions. Do not invent owners, due dates, decisions, or certainty.
- Preserve uncertainty and unresolved questions.
- Use UK English.

## If Transcript Validation Fails

Inspect `markdown/transcript.md`, fix it, and rerun validation before generating or trusting summary outputs.

## Assemble and Validate Markdown

After `overview.md`, `minutes.md`, `actions.md`, and `decisions.md` exist, run:

```bash
.venv/bin/meeting-minutes assemble-combined "{run}"
.venv/bin/meeting-minutes validate-markdown "{run}"
```

Do not write `combined.md` by hand. It must be assembled from the separate Markdown outputs so it cannot silently diverge.

## Export Word Documents

Run only when `doctor` reports Word export ready:

```bash
.venv/bin/meeting-minutes export-docx "{run}"
```

The Markdown files remain canonical. Word files are convenience exports.

For Word readability, action tables may be exported as action blocks in `.docx`. This does not change canonical `actions.md`.

## Finish Run

When Markdown validation and Word export have succeeded, run:

```bash
.venv/bin/meeting-minutes finish-run "{run}"
```

Then confirm:

```bash
sed -n '1,220p' "{run}/run.json"
```

Expected final status:

```json
"status": "success"
```

## Quality Review

Before reporting completion, inspect:

- `markdown/transcript.md` for transcript faithfulness
- `markdown/actions.md` for unsupported owners, due dates, or obligations
- `markdown/decisions.md` for over-claimed decisions
- `markdown/combined.md` for complete assembled sections
- `docx/combined.docx` for obvious formatting problems

Run tests once more before finishing:

```bash
.venv/bin/python -m pytest
```

## What To Tell The User

Report:

- the run folder path
- whether Markdown validation passed
- whether Word export passed
- the final `run.json` status
- any manual review concerns

Do not ask the user to run commands. This is a Codex-run workflow.
