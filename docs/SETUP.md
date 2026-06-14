# First-Time Setup

This is the Codex-facing setup guide for preparing a fresh clone of the meeting minutes workflow.

The user-facing guide is [HOW_TO_USE.md](../HOW_TO_USE.md). Keep that guide simple; put operator detail here.

## Setup Promise

Codex may create the project-local Python environment and install Python project dependencies.

Codex must ask before installing or downloading system-level tools or large model files, including:

- Homebrew
- Pandoc
- WhisperKit CLI
- WhisperKit model files

Do not send meeting recordings to an LLM during setup or workflow runs.

## Fresh Clone Setup

In Codex, the user should create the project with **Use an existing folder** and select the downloaded `meeting-minutes-workflow` folder. Use one setup chat for this first-time setup.

From the repository root, run:

```bash
python3 scripts/setup_project.py
```

The setup helper:

1. Checks whether the machine is an Apple Silicon Mac.
2. Checks whether Homebrew, Pandoc, WhisperKit CLI, and the WhisperKit model are available.
3. Creates or reuses `.venv`.
4. Installs the project and test dependencies into `.venv`.
5. Runs `meeting-minutes doctor`.
6. Runs the test suite.

If Python dependency installation fails because network access is blocked, rerun the setup command with Codex approval for Python package installation.

## Missing System Tools

If Homebrew is missing, stop and ask the user whether they want Codex to install Homebrew or whether they prefer to install it themselves.

If Homebrew is present but Pandoc or WhisperKit CLI is missing, ask before running:

```bash
brew install pandoc whisperkit-cli
```

Install only the missing tools.

Pandoc is required for Word export. WhisperKit CLI and the Large v3 Turbo model are required for meeting recordings. Transcript source material can still be processed without audio readiness.

## WhisperKit Model

The expected model folder is:

```text
~/Library/Application Support/WhisperKit/Models/models/argmaxinc/whisperkit-coreml/openai_whisper-large-v3-v20240930_turbo
```

Model files must stay in the normal user-level WhisperKit location, not in this repository or `.venv`.

If the model is missing, Codex should ask before preparing or downloading it. Use WhisperKit's normal model download flow; do not commit model files.

## Verification

Setup is complete when:

```bash
.venv/bin/meeting-minutes doctor
.venv/bin/python -m pytest
```

both succeed, and `doctor` reports the required workflow areas ready for the user's intended source material.
