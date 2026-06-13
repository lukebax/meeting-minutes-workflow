# Minutes Prompt

Use this prompt to create `markdown/minutes.md` from the canonical Transcript.

## Goal

Create topic-based Minutes that record key discussion points, decisions, actions, and unresolved questions from the meeting.

## Output Format

Write Markdown only.

Start with:

```markdown
# {Meeting Title} - Minutes
```

Use topic sections that roughly follow the order of the meeting where possible.

Include an `## Open Questions` section only when the transcript contains unresolved questions, dependencies, or deferred choices.

## Rules

- Use UK English.
- Use a clear, neutral, professional, concise tone.
- Base the Minutes only on the canonical Transcript.
- Organise by inferred Topic, not by official agenda.
- Do not pretend inferred Topics were agenda items.
- Do not produce a speaker-by-speaker play script.
- Mention speakers only when relevant to an Action, Decision, or important context.
- Preserve uncertainty where it affects interpretation.
- Do not invent decisions, actions, owners, due dates, attendees, agenda items, or meeting metadata.
- Put proposals, open questions, and deferred choices in the Minutes, not in Decisions.
- Do not include routine boilerplate saying the output requires review.

## Quality Bar

The Minutes should be readable as a faithful meeting record without forcing the transcript into a structure it does not support.
