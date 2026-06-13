# Codex-Run Workflow

The workflow is intended to be run inside Codex and will rely on the LLM capability available there, rather than asking users to configure separate LLM providers or API keys. The implementation may expose a normal local command so Codex has something reliable and testable to run, but the documented user path is Codex-first. This keeps v1 simple for non-technical colleagues, at the cost of making Codex the required way to run the workflow.
