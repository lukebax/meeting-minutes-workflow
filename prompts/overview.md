# Overview Prompt

Use this prompt to create `markdown/overview.md` from the canonical Transcript.

## Goal

Create a brief Overview for someone who needs the gist of the meeting without reading the full Minutes.

## Output Format

Write Markdown only.

Start with:

```markdown
# {Meeting Title} - Overview
```

Then write:

1. One short opening sentence summarising the meeting focus.
2. A concise bullet list of the main points.

## Rules

- Use UK English.
- Use a clear, neutral, professional, concise tone.
- Base the Overview only on the canonical Transcript.
- Do not invent context, outcomes, owners, or dates.
- Do not include routine boilerplate saying the output requires review.
- Do not make the meeting sound more positive, certain, or polished than the transcript supports.
- If the meeting had no clear outcome, say so plainly.

## Quality Bar

The Overview should be quick to scan and useful to someone who missed the meeting.
