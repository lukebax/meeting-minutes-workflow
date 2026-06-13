# Meeting Minutes Workflow

This context describes a workflow for turning recorded meetings into structured written outputs for colleagues who need clear follow-up material.

## Language

**Source Material**:
The meeting content provided to the workflow, either as a meeting recording or an existing transcript.
_Avoid_: Input, upload

**Input Folder**:
A temporary holding place for the single source file used by the next workflow run. It is not a storage area for recordings or transcripts.
_Avoid_: Archive, library

**Workflow Run**:
A single use of the workflow for one meeting, starting from source material and a meeting title and ending with generated outputs for human review. Each workflow run handles exactly one meeting.
_Avoid_: Job, session

**Meeting Recording**:
A source audio file containing a recorded meeting. A meeting recording may be used to produce a transcript, but it is not itself a workflow output.
_Avoid_: Audio input, raw audio

**Transcript**:
A lightly cleaned written representation of what was said in a meeting. All source material is turned into or treated as a transcript before summary outputs are created, and the transcript is preserved with the summary outputs.
_Avoid_: Transcription output, text dump

**Speaker Name**:
An optional name or label identifying who said part of a transcript. Speaker names may be lightly normalized when present, but they are not invented when absent.
_Avoid_: Speaker attribution, diarisation label

**Meeting Title**:
A short user-provided name for the meeting, used to identify a workflow run and its outputs. It is the only required user-provided meeting metadata.
_Avoid_: Generated title, inferred title

**Topic**:
A subject or theme discussed during a meeting and inferred from the transcript. Topics are not official agenda items.
_Avoid_: Agenda item, section

**Summary Output**:
A draft written artifact derived from a transcript, such as minutes, an overview, or a list of actions. Summary outputs are intended for human review before being shared.
_Avoid_: Summary, report

**Combined Output**:
A convenience summary output that gathers the same overview, minutes, actions, and decisions into one document.
_Avoid_: Full report, bundle

**Overview**:
A brief summary output for someone who needs the gist of a meeting without reading the full minutes.
_Avoid_: Executive summary, recap

**Minutes**:
A structured summary output that records the key discussion points, decisions, and follow-up from a meeting.
_Avoid_: Meeting notes

**Action**:
A follow-up item identified from a meeting. An action may have unclear details, but its owner, due date, and wording are only confirmed when they are clearly supported by the transcript.
_Avoid_: Task, todo

**Decision**:
A clearly supported choice or conclusion reached during a meeting that should be recorded for future reference. Proposals, open questions, and deferred choices are not decisions.
_Avoid_: Outcome, resolution

**Open Question**:
An unresolved question, dependency, or deferred choice identified from a meeting.
_Avoid_: Pending decision, issue
