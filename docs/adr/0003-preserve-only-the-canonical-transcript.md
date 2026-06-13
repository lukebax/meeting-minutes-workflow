# Preserve Only the Canonical Transcript

The workflow may use hidden working files during a run, but it will not expose raw intermediate transcript files as normal outputs. Each run preserves the transcript used for summarisation as `markdown/transcript.md`, with a matching `docx/transcript.docx` derived from it, so users have one clear transcript to review.
