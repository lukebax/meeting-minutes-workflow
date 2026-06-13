# Local Transcription Requirements

Original decision: the workflow would use a high-quality local transcription approach chosen during implementation research, with no API key required. Transcription quality would take priority over speed for both short and long meetings, while still using hardware acceleration when available and supporting CPU-only machines where practical.

Update: [ADR 0011](./0011-use-whisperkit-for-apple-silicon-audio.md) narrows v1 audio support to Apple Silicon Macs for this team. CPU-only transcription is no longer a v1 requirement, because the tested CPU-first path was too slow for long meetings.
