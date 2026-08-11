# Course workspace contract

## Purpose

Persist only the information needed for grounded continuity. The workspace must
remain understandable without a database browser or internal service.

## Recommended layout

```text
<course-workspace>/
  course-model.json
  course-map.md
  coverage-ledger.md
  assessment-map.md          # required when assessment sources are used
  checkpoint.md
  materials/                 # optional; existing material roots may stay external
  .adaptive-stem-tutor/
    state.json
    source-index.json
    observations.jsonl
    retrieval-plan.json
    assessment-attempts.jsonl
```

`course-map.md` and `checkpoint.md` are readable study records. The hidden
directory contains structured local state. Never mix generated state into the
original material directory when the learner has not designated it as a course
workspace.

`course-model.json` is the structured Curriculum Model defined in
`curriculum-modeling.md`. Validate it with `scripts/validate_course_model.py`
before calling setup complete. It records the complete objective set, typed
relations, route, confidence, and conflicts; it is not learner performance
state.

It also records the Course Spine decision. A verified full-course note may seed
scope and sequence; a bounded, absent, or uncertain decision must preserve its
limitations and trigger the corresponding multi-source audit path. Do not infer
this field from a display name.

Use:

```bash
python3 scripts/validate_course_model.py <course-workspace>/course-model.json
```

A valid result establishes structural completeness and prerequisite-safe order.
It does not replace manual review of whether the objectives, evidence anchors,
edge justifications, and route conflicts are academically sound.

`course-map.md` is a compact orientation projected from the Curriculum Model,
not a coverage or ordering claim by itself.
`coverage-ledger.md` accounts for every source-supported chapter objective,
prerequisite, practice type, source anchor, edition caveat, and current evidence
state. Useful evidence states include `not_started`, `source_checked`,
`in_progress`, `needs_repair`, `review_due`, `completed_with_current_evidence`,
and `coverage_gap`. These are route states, not mastery labels or percentages.

The coverage ledger should include route position, objective ID, observable
criterion, Hard Prerequisites, source anchors, sequence basis/confidence,
practice coverage, and route state. Every `course-model.json` objective must
appear exactly once.

`assessment-map.md` records supplied paper years, verified conditions,
question-to-objective mappings, marks, answer forms, demand types, and solution
quality. It is required before claiming exam alignment when past papers are in
the corpus. It must distinguish the newest supplied format from historical
formats and must label unstated conditions as unknown.

## Initialization

Use:

```bash
python3 scripts/tutor_state.py init \
  --workspace <course-workspace> \
  --course-code <code> \
  --course-title <title> \
  --learner-language <language>
```

Initialization must not overwrite existing files. If another learning system is
present, inspect it read-only and ask before migration.

## Source index

Register only sources that were actually inspected. A source record contains a
stable ID, display label, absolute resolved path, role, review state, file hash,
optional scope note, and optional edition and authority notes. The hash supports
change detection; it is not learner-facing content. Edition metadata prevents a
mixed-year corpus from silently presenting an older file as current authority.

Use:

```bash
python3 scripts/tutor_state.py register-source \
  --workspace <course-workspace> \
  --source-id <id> \
  --path <material-path> \
  --label <label> \
  --role <role> \
  --review-state reviewed \
  --scope <bounded-scope> \
  --edition <course-year-or-edition> \
  --authority-note <why-this-version-is-authoritative-or-bounded>
```

Do not register a directory as if it had been reviewed file by file.

For a question paper, use role `assessment`. Register a separate paired answer
as `solution_reference`. A scan can be marked `reviewed` only after visual
inspection; put defects and restrictions in `authority-note` rather than
silently upgrading it to a clean marking authority.

## Checkpoint updates

Write an update JSON file with only the fields being changed:

```json
{
  "status": "active",
  "chapter_id": "ch3",
  "chapter_title": "Chapter 3 — Core concepts of statistical mechanics",
  "chapter_stage": "teaching",
  "section": "Chapter 3",
  "objective_id": "ch3.micro-macro",
  "objective_title": "Distinguish microstates and macrostates",
  "focus": "Why multiplicity changes macrostate probability",
  "last_teaching_summary": "Used ordered dice outcomes to connect multiplicity to probability.",
  "pending_check": "List the microstates for exactly two heads in three distinguishable coins.",
  "next_action": "Interpret the learner's answer and repair only an enumeration gap."
}
```

Then run:

```bash
python3 scripts/tutor_state.py update \
  --workspace <course-workspace> \
  --from-json <update.json>
```

The update is atomic. Omitted fields retain their values. Set `pending_check` to
`null` only when the Check is resolved or explicitly abandoned.

## Answer observations

An observation JSON file contains:

```json
{
  "chapter_id": "ch3",
  "objective_id": "ch3.micro-macro",
  "criterion": "Enumerates all distinguishable microstates in a macrostate",
  "judgment": "partial",
  "evidence_summary": "Listed HHT and HTH but omitted THH.",
  "error_type": "procedure",
  "severity": "local",
  "uncertainty": "low",
  "next_action": "Repair exhaustive enumeration by classifying the position of T."
}
```

Record it with:

```bash
python3 scripts/tutor_state.py observe \
  --workspace <course-workspace> \
  --from-json <observation.json>
```

Keep summaries concise and observable. Do not store hidden reasoning, personality
inferences, or a global mastery percentage.

Before changing chapters or choosing whether to compress, repair, revisit, or
advance, inspect cumulative evidence:

```bash
python3 scripts/tutor_state.py progress \
  --workspace <course-workspace> \
  --chapter-id <chapter-id>
```

This summary reports observations and their latest criterion-linked judgments;
it does not calculate a mastery score. Older observations without a chapter ID
remain valid and appear as `unassigned` unless filtered by objective.

## Delayed retrieval evidence

Schedule a retrieval only after recording when the earlier evidence occurred.
The due time must be at least one full day later, and `context_change` must say
how the new task will differ:

```json
{
  "retrieval_id": "ch3-multiplicity-r1",
  "chapter_id": "ch3",
  "objective_id": "ch3.multiplicity",
  "criterion": "Connect multiplicity to probability",
  "prior_evidence_at": "2026-08-10T09:00:00+08:00",
  "due_at": "2026-08-13T09:00:00+08:00",
  "minimum_delay_days": 2,
  "context_change": "Use distinguishable coins rather than dice."
}
```

```bash
python3 scripts/tutor_state.py schedule-retrieval \
  --workspace <course-workspace> \
  --from-json <retrieval.json>

python3 scripts/tutor_state.py due-retrievals \
  --workspace <course-workspace>
```

To record `retained_later`, the observation must include the scheduled
`retrieval_id`, `independent: true`, and
`source_exposure: "unseen_before_attempt"`. The tool rejects an early,
unscheduled, exposed, or assisted claim. The learner sees a natural recap, not
these internal fields.

## Protected and timed assessment attempts

Record minimal result metadata after a real attempt. Do not store full learner
answers by default:

```json
{
  "attempt_id": "pilot-baseline-a",
  "kind": "baseline",
  "task_id": "protected-form-a",
  "objective_ids": ["ch1.first-law", "ch3.microstates"],
  "marks_awarded": 40,
  "marks_available": 100,
  "timed": true,
  "duration_seconds": 7200,
  "independent": true,
  "solution_seen_before_attempt": false,
  "form_status": "held_out_unseen",
  "protocol_id": "course-pilot-1",
  "form_id": "form-a",
  "evidence_summary": "Completed without hints under the declared conditions.",
  "conditions_note": "No interruption; calculator permitted by the paper."
}
```

```bash
python3 scripts/tutor_state.py record-attempt \
  --workspace <course-workspace> \
  --from-json <attempt.json>

python3 scripts/tutor_state.py attempts \
  --workspace <course-workspace> \
  --protocol-id <protocol-id>
```

Baseline and posttest forms must be distinct, timed, independent,
solution-blind, and held out before use. The comparison reports an observed
percentage-point change with a non-causal claim boundary. Use
`learning-evidence.md` to decide whether the forms are genuinely comparable.

## Pause and resume

`pause` changes only the status and pause timestamp. `show` returns the current
checkpoint. Resume by updating status to `active` while retaining the same
objective and pending Check unless the learner requests a route change.

```bash
python3 scripts/tutor_state.py pause --workspace <course-workspace>
python3 scripts/tutor_state.py show --workspace <course-workspace>
python3 scripts/tutor_state.py resume --workspace <course-workspace>
```

The tutor translates this state into a short learner-facing recap and never
shows raw JSON, paths, hashes, or internal identifiers.

## Privacy and durability

- Local storage is the default.
- Do not copy original course files unless the learner requests organization.
- Do not persist full conversation transcripts by default.
- Do not store more personal data than continuity requires.
- Atomic writes protect against partial state replacement; they do not replace
  backups.
- Preserve unknown fields when reading a newer compatible state; reject unknown
  schema versions rather than guessing.
