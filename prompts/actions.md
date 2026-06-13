# Actions Prompt

Use this prompt to create `markdown/actions.md` from the canonical Transcript.

## Goal

Create a table of follow-up Actions identified from the meeting. Be conservative: include only follow-up work that the transcript clearly supports as something someone should do after the meeting.

## Output Format

Write Markdown only.

Start with:

```markdown
# {Meeting Title} - Actions
```

Then use this exact table structure:

```markdown
| Action | Owner | Due date | Review note |
|---|---|---|---|
```

If no Actions are supported by the transcript, write a short sentence after the title:

```markdown
No actions were clearly identified in the transcript.
```

## Rules

- Use UK English.
- Use a clear, neutral, professional, concise tone.
- Base Actions only on the canonical Transcript.
- Include an Action only when follow-up work is clearly stated or strongly implied as post-meeting work.
- Do not include ordinary status updates, concerns, observations, completed items, or things merely discussed.
- Do not turn "we should discuss this later" into an Action unless the transcript clearly supports a concrete follow-up.
- Confirm the owner only when the transcript clearly supports the owner.
- Confirm the due date only when the transcript clearly supports the due date.
- Use `Unclear` for unclear owners.
- Use `Not stated` for missing due dates.
- Use the Review note column to explain uncertainty briefly.
- If an item is borderline, omit it from the table rather than overstating it.
- Do not invent owners, due dates, wording, or obligations.
- Do not turn every discussion point into an Action.
- Do not include routine boilerplate saying the output requires review.

## Quality Bar

The Actions table should help a human reviewer see what follow-up work may be needed without silently assigning unsupported responsibility.
