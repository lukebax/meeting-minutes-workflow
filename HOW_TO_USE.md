# How to Use This Workflow

This guide describes the current Codex-run workflow for transcript files and local audio transcription on Apple Silicon Macs.

## What this workflow does

This workflow turns one transcript file or meeting recording into reviewable meeting outputs:

- Transcript
- Overview
- Minutes
- Actions
- Decisions
- Combined document

The outputs are drafts. Review them before sharing them with anyone else.

## Open the workflow in Codex

After downloading this project from GitHub, open Codex and create a project from it:

1. Open Codex.
2. Choose **Use an existing folder**.
3. Select the downloaded `meeting-minutes-workflow` folder.

Use this one Codex project for the workflow. Within that project, use separate chats:

- one setup chat for first-time setup
- one new chat for each meeting

Using one chat per meeting keeps each Workflow Run separate and reduces the chance that details from one meeting are mixed into another.

## First-time setup

Before the first run, start a new setup chat in the Codex project and copy this message into Codex:

```text
Please set up this meeting minutes workflow project so it is ready to run.
```

Codex should check the local Python environment, install or use the project-local `.venv`, run the workflow tests, check whether Pandoc is available for Word export, and check whether WhisperKit audio transcription is ready. Pandoc is required for `.docx` files. WhisperKit CLI and the local model are required for meeting recordings.

Codex may ask for approval before installing Homebrew tools or downloading large model files. This is expected.

## Before each run

Put exactly one source file in the `input` folder.

Supported transcript formats for v1:

- `.txt`
- `.md`
- `.vtt`
- `.docx`

Supported audio formats for v1:

- `.m4a`
- `.mp3`
- `.wav`
- `.flac`

Audio transcription uses local WhisperKit tooling on Apple Silicon Macs. The meeting recording is transcribed locally into a hidden working transcript before Codex creates the reviewable outputs.

When Codex runs audio transcription, it may ask for approval to let WhisperKit write Apple runtime cache files under your normal user cache folder. Approve this for meeting recordings. This does not send the meeting recording to an LLM.

Do not use the `input` folder as a storage area. Keep it empty unless you are about to run the workflow. After the run is finished, remove your source file from `input` yourself.

The workflow will not delete your source file.

## Run the workflow in Codex

For each meeting, start a new chat in the Codex project. Use one chat for one meeting only.

Copy this message into Codex and replace the meeting title:

```text
Please run the meeting minutes workflow using the file in the input folder.
Meeting title: [replace this with your meeting title]
```

The meeting title should be short and clear, for example:

```text
Finance Planning
```

Codex will then:

1. Check the project is ready.
2. Prepare a new workflow run folder.
3. Extract or locally transcribe the source material into a hidden working transcript.
4. Create and validate the cleaned Transcript.
5. Create the Overview, Minutes, Actions, Decisions, and Combined Markdown outputs.
6. Validate the Markdown outputs.
7. Export matching Word documents if Pandoc is available.
8. Mark the workflow run as successful when all checks pass.

If a run folder with the same date and meeting title already exists, Codex will create a numbered folder such as `2026-06-13-finance-planning-2`.

If an audio transcription attempt fails and Codex retries, you may see one failed numbered folder and one later successful numbered folder. This is expected; failed folders are preserved so Codex can inspect what went wrong.

For the next meeting, empty the `input` folder, put in the next source file, and start another new chat.

## Find the outputs

The workflow will create a new folder in `outputs`.

Example:

```text
outputs/
  2026-06-12-finance-planning/
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

The Markdown files are the canonical outputs. The Word documents are exported from the Markdown files and should contain the same information.

The outputs are drafts. Check them before sharing, especially:

- names and project terms
- actions, owners, and due dates
- decisions
- sensitive material
- anything that sounds more certain than the meeting really was

## Important notes

- Audio files are never copied into the output folder.
- Audio transcription happens locally with WhisperKit; the audio file is not sent to an LLM.
- The transcript in the output folder is the transcript used for summarisation.
- Actions may include unclear owners or due dates if the transcript did not confirm them.
- Decisions are only listed when the transcript clearly supports them.
- Open questions may appear in the minutes when something was unresolved.
- The workflow is intended for English-language meetings in v1.
