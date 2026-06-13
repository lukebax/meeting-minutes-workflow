# Transcript Cleanup Prompt

Use this prompt to turn extracted transcript text into the canonical `markdown/transcript.md`.

## Goal

Create a lightly cleaned Transcript that preserves what was said in the meeting. Do not summarize, shorten, reinterpret, or reorganize the meeting beyond light readability cleanup.

## Output Format

Write Markdown only.

Start with:

```markdown
# {Meeting Title} - Transcript
```

Then provide the cleaned transcript content.

## Rules

- Preserve what was said, not just the substance.
- Keep the output transcript-like: use speaker turns when speaker labels are present, or short chronological paragraphs when they are not.
- Do not compress a long discussion into a short narrative summary.
- Do not replace conversational content with topic summaries.
- Keep the transcript roughly proportional to the source. If the source is long, the cleaned Transcript should still be long.
- Remove routine caption timestamps, cue numbers, and file-format noise.
- Remove obvious mechanical duplication from subtitle/caption exports.
- Preserve speaker names or labels when they are present.
- Lightly normalize speaker-label formatting, for example `Name -` to `Name:`.
- Do not invent speaker names.
- Do not invent speaker turns.
- If the source has useful speaker-labelled turns, keep them.
- If the source is one block of text, turn it into readable paragraphs.
- Preserve uncertainty, disagreement, caveats, and meaningful hesitations where they affect interpretation.
- Do not add agenda items, topics, decisions, actions, or commentary.
- Do not mention whether the source came from audio or a transcript file.

## Quality Bar

The result should be readable enough to review and use as the source for summary outputs, while remaining recognisably faithful to the source transcript. A reviewer should still be able to trace the meeting flow and wording from the source into this Transcript.
