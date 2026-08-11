# Adaptive STEM Tutor

An evidence-grounded Codex Skill for learning university-level STEM from your
own course materials. It turns notes, slides, textbooks, problem sheets, and
past papers into a coherent learning route, then teaches turn by turn with
source-aware explanations, transfer Checks, answer-specific feedback, and
resumable progress.

> 中文简介：这是一个面向大学 STEM 课程的 Codex Skill。它会先审查你提供的讲义、
> 教材、习题和真题，建立有来源依据的课程路线，再以自然教学、迁移问题、局部纠错和
> 可恢复进度带你学习，而不是逐页翻译资料或机械播放内容。

## What it does

- Builds an evidence-backed curriculum model instead of trusting filenames or
  folder order.
- Recognizes a complete professor-curated textbook, notebook, reader, or set of
  notes as an optional **Course Spine** when its content supports that role.
- Derives a prerequisite-safe route from multiple sources when no complete
  Course Spine exists.
- Teaches complete instructional episodes: motivation, intuition, formalism,
  visible reasoning, conditions, misconceptions, and a meaningful next step.
- Uses Checks that require transfer rather than repeating the worked example
  with different nouns or numbers.
- Responds differently to correct reasoning, partial understanding,
  misconceptions, clarification requests, and non-answer control messages.
- Preserves pause/resume continuity without exposing internal IDs, hashes,
  databases, or file paths to the learner.
- Separates immediate correctness, transfer, delayed retrieval, cumulative
  integration, and assessment change instead of calling one answer “mastery.”
- Uses Markdown by default; HTML or visual artifacts are optional and created
  only when they add real teaching value.

## Material and evidence model

The Skill assigns bounded roles to supplied sources:

- primary teaching;
- practice;
- assessment;
- solution reference;
- supplementary or administrative context.

It keeps scope, sequence, notation, and explanatory authority separate. A
solution cannot silently become the teaching source, and past-paper frequency
cannot silently redefine the syllabus.

For course setup, it produces a structured `course-model.json`, a learner-facing
course map, and a coverage ledger. The included validator rejects missing or
duplicate objectives, unknown relation targets, prerequisite cycles, and routes
that teach a dependency before its prerequisite.

## Installation

Clone the repository into your Codex Skills directory. The target directory
should not already exist:

```bash
git clone https://github.com/tony-creat06/adaptive-stem-tutor.git \
  ~/.codex/skills/adaptive-stem-tutor
```

Restart or reload Codex so it discovers the Skill.

This Skill disables implicit invocation. Invoke it explicitly as
`$adaptive-stem-tutor` when starting or resuming a course.

To update a clone without rewriting local history:

```bash
git -C ~/.codex/skills/adaptive-stem-tutor pull --ff-only
```

## Quick start

Place or identify your course materials, then ask Codex something like:

```text
Use $adaptive-stem-tutor to teach me this course from zero using the materials
in <material-folder>. I want to understand the concepts and eventually solve
exam questions independently. Teach in Chinese and keep my progress resumable.
```

Other useful requests:

```text
Use $adaptive-stem-tutor to resume my existing course workspace.
```

```text
Use $adaptive-stem-tutor to audit these lecture notes, exercises, and past
papers, build the course route, and start the first lesson.
```

```text
Use $adaptive-stem-tutor to explain this derivation directly without grading
my message as an answer.
```

## Teaching principles

The learner-facing default is:

```text
concrete problem or phenomenon
→ intuition
→ formal idea
→ visible reasoning or worked example
→ assumptions and traps
→ connection
→ new-context Check
```

This is a reasoning order, not a rigid template. The lesson must answer the
question promised by its opening, distinguish necessary from sufficient
conditions, use quantitatively precise notation, and keep the Check logically
independent from the preceding explanation.

## Local workspace

The Skill can maintain a compact course workspace containing:

```text
course-model.json
course-map.md
coverage-ledger.md
assessment-map.md        # when assessment sources are used
checkpoint.md
.adaptive-stem-tutor/    # structured local continuity state
```

Generated state stays separate from original course materials. The public
repository contains no course PDFs, learner records, or private test data.

## Included files

```text
SKILL.md
agents/openai.yaml
references/
  acceptance.md
  assessment-quality.md
  course-lifecycle.md
  curriculum-modeling.md
  exercise-quality.md
  learning-evidence.md
  source-grounding.md
  teaching-contract.md
  workspace-contract.md
scripts/
  tutor_state.py
  validate_course_model.py
```

`tutor_state.py` owns minimal persistence, not pedagogy.
`validate_course_model.py` performs deterministic structural checks; it does not
replace academic review of objectives, evidence anchors, and prerequisite
judgments.

## Boundaries

- The Skill does not guarantee exam scores or long-term retention.
- A passing structural validation does not prove that supplied materials are
  complete or academically correct.
- Assessment-only material can support a provisional demand map, not a claimed
  complete syllabus.
- Original course files should remain unchanged; generated outputs and learner
  state belong in a separate workspace.
- Solution material should not be used as primary teaching before an authentic
  attempt.

The goal is not to automate page delivery. It is to support careful,
source-grounded teaching that helps the learner reason independently.
