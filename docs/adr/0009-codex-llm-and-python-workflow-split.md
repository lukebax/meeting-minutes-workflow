# Codex LLM and Python Workflow Split

The v1 workflow will use Python for deterministic machinery such as file detection, transcript extraction, local transcription, output folder creation, validation, Word export, and `run.json`. Codex provides the LLM work for transcript cleanup when needed and for generating overview, minutes, actions, and decisions, avoiding separate LLM API keys while making Codex a required part of the workflow.
