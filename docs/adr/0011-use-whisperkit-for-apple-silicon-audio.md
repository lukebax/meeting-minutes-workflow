# Use WhisperKit for Apple Silicon Audio

The workflow will use WhisperKit CLI for v1 meeting recording transcription on Apple Silicon Macs, rather than a portable CPU-first Python transcription stack.

The intended users are this team and their relatively modern Apple computers, not a broad cross-platform audience. A `faster-whisper` CPU spike proved that local transcription works, but it was too slow for long meetings. WhisperKit Large v3 Turbo transcribed the same 33 minute 49 second `.m4a` recording in about 100 seconds after first-use setup, which is a better fit for away-day meetings and other long recordings.

WhisperKit CLI is installed as normal user-level software through Homebrew, and model files live in the user's application support area rather than in this repository or `.venv`. This keeps large model files outside Git while making the transcription tool available outside Codex.

The trade-off is that v1 audio support is intentionally Mac-specific. Transcript file workflows remain available without audio transcription readiness.
