# Decisions Prompt

Use this prompt to create `markdown/decisions.md` from the canonical Transcript.

## Goal

Create a short list of Decisions clearly supported by the meeting transcript. Be stricter than the Minutes and Actions outputs.

## Output Format

Write Markdown only.

Start with:

```markdown
# {Meeting Title} - Decisions
```

Use a short bullet list. Include brief context under a decision only when needed.

Example:

```markdown
- The team agreed to proceed with the revised launch timeline.
  - Context: This depends on design sign-off being completed this week.
```

If no Decisions are clearly supported by the transcript, write:

```markdown
No decisions were clearly identified in the transcript.
```

## Rules

- Use UK English.
- Use a clear, neutral, professional, concise tone.
- Base Decisions only on the canonical Transcript.
- Include only choices or conclusions that were clearly reached.
- Exclude proposals, possibilities, open questions, deferred choices, discussion points, completed status updates, and actions.
- Do not promote an Action or Open Question into a Decision.
- Do not list "someone will follow up" as a Decision.
- Do not list "this is done" as a Decision unless the meeting clearly made a new choice or conclusion.
- If the evidence is weak, write that no decision was clearly identified rather than trying to fill the file.
- Preserve important caveats or conditions.
- Do not invent decisions or make weak agreement sound stronger than it was.
- Do not include routine boilerplate saying the output requires review.

## Quality Bar

The Decisions file should be conservative and trustworthy. It is better to list no decision than to overstate what the meeting agreed.
