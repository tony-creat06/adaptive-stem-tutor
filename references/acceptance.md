# Acceptance review

Tests protect mechanics. The release decision comes from manually reading the
actual learner-visible outputs produced in realistic forward use.

## Course setup

- Material roles were established from inspected content.
- A Course Spine candidate was searched for and classified as `verified`,
  `bounded`, `absent`, or `uncertain` from internal content rather than filename.
- A verified spine scaffolds scope and sequence but remains cross-checked against
  exercises, assessments, omissions, notation conflicts, and edition drift.
- `course-model.json` contains source-anchored observable objectives, typed
  relationships, sequence evidence, route confidence, and conflicts.
- The model validates with no missing route objective, duplicate objective,
  unknown edge target, Hard Prerequisite cycle, or prerequisite ordered after
  its dependent.
- The map reflects the validated Curriculum Model and labels gaps honestly.
- The coverage ledger accounts for every chapter objective; a coarse contents
  list is not accepted as no-omission evidence.
- Assessment material influences goals without replacing primary teaching.
- Every supplied past paper is paired by its internal academic year and mapped
  question by question; filenames alone are not accepted as year evidence.
- The newest supplied format is distinguished from historical formats, and
  duration or permitted aids are never inferred when absent.
- Scanned solutions are visually inspected, and solution defects or mismatches
  are carried into grading restrictions.
- Formula-critical claims were checked against rendered pages rather than trusted
  from extracted text alone.
- Formula, diagram, annotation, and adjacent prose were compared for internal
  convention conflicts; inconsistent slide wording was quarantined.
- Mixed editions or academic years have an explicit current-authority decision.
- Scope, sequence, notation, and explanatory-support authority are designated
  separately when evidence supports them. Absence of a single sequence authority
  produces a derived or provisional route rather than an arbitrary master file.
- The first response gives orientation and starts useful teaching.
- A zero-start response follows the raw lecture's motivating problem or visual
  material inside the first ordered objective rather than converting extracted
  headings into a definition list or jumping to a later concept.
- The learner is not asked to operate internal commands or choose internal IDs.

## Teaching turn

- The opening creates a real question, contrast, or purpose.
- The source's strongest relevant experiment, diagram, derivation, or problem
  performs explanatory work; it was not replaced by a generic scenario for
  convenience.
- Intuition precedes new abstraction when appropriate.
- The learner can see how evidence or constraints support the formal idea; the
  central conclusion is not merely asserted after an anecdote.
- The lesson explicitly answers the question promised by its title or opening;
  “why possible,” “why useful,” “what it means,” and “how to recognize it” are
  not silently substituted for one another.
- Formalism is accurate and course-consistent.
- Necessary and sufficient directions, one-way diagnostics, single-case
  evidence, and tempting converses have correct boundaries.
- Symbols and numerical constants are defined with correct dimensions and units;
  counts, constants, densities, totals, approximations, and identities are not
  conflated.
- A worked example exposes decisions and intermediate reasoning.
- The lesson defines the relevant system boundary and equilibrium assumption
  when those conditions control the meaning of a state description.
- Basis or representation changes state what the coefficients mean and what is
  invariant.
- Conditions and a high-value misconception are handled without bloating the
  turn.
- The prose is natural in the learner's language.
- A Check, if present, uses a new context and asks one main question.
- The Check changes at least two meaningful dimensions among system, operation,
  representation, inference direction, constraints, and required output. A
  noun-swapped two-path comparison, copied combine/split setup, or changed
  numbers alone is rejected as transfer.
- The Check is not tautological: its premises do not already state the requested
  conclusion.
- With nouns and symbols removed, the Check does not reduce to the immediately
  preceding implication, converse, classification, or completed procedure.
- The response stops after the next learner action.
- A first or cold-resume Check is preceded in the current visible context by a
  physical purpose, reasoning bridge or worked decision, and the consequential
  convention trap; a formula plus question is rejected as insufficient teaching.

## Answer and repair

- Non-answer messages are not graded.
- Equivalent reasoning is accepted without exact-phrase matching.
- Correct work is preserved.
- A correct conclusion with circular, copied, or absent reasoning is not treated
  as equivalent to a well-supported answer.
- Feedback isolates the earliest consequential gap.
- Repair is bounded and changes the representation when useful.
- Retry is independent and criterion-linked.
- Different learner reasons produce materially different next explanations;
  verdict labels pasted onto the same paragraph are rejected as adaptation.
- One correct response is not called long-term mastery.

## Continuity

- Pause/resume returns to the same instructional situation.
- A cold re-entry reconstructs enough teaching to make the preserved pending
  Check fair; session status alone is not treated as proof that prior prose is
  still visible to the learner.
- The checkpoint is readable and contains no hidden chain-of-thought.
- Source changes can be detected.
- Learner-visible output contains no private paths, hashes, schemas, logs, or
  internal workflow language.
- Ordinary teaching contains no bare PDF/slide/note filenames or retrieval-style
  citation residue.
- Essential teaching remains inline after artifact access failure.
- Cumulative observations, not just the latest turn, influence route decisions.
- The default route is chapter-by-chapter, with prerequisite bridges and
  learner-chosen prioritization recorded without silent omissions.
- A chapter transition includes a readiness review or integrative task,
  unresolved-gap carryover, and a later retrieval plan.
- A `retained_later` claim is backed by a due scheduled retrieval, a changed
  unseen task, and an independent attempt rather than an immediate retry.

## Exercises, solutions, and teaching material

- Each chapter maps objectives to foundational, transfer, integrative, and
  exam-style practice where the source supports them.
- Uneven official exercise coverage is labeled and supplemented only with
  clearly generated, source-grounded tasks.
- Combined problem-and-solution files have bounded practice and solution roles;
  no answer is exposed before an authentic attempt.
- Feedback exposes the solution strategy, decisions, checks, and reusable
  method rather than copying an official answer.
- Lecture notes were reviewed for conceptual continuity, missing derivation
  bridges, notation, examples, visual dependencies, and exercise alignment.
- Exam readiness is supported by chapter bridges, changed-context transfer,
  cumulative mixed retrieval, and a timed supplied format—not by chapter
  completion or problem-sheet coverage alone.

## Artifact decision

- Markdown is used for normal teaching and ordinary mathematics.
- Any enhanced artifact has named added value.
- Interactive artifacts are actually operated, not accepted from source review
  or a static screenshot alone.
- A text-equivalent HTML copy is rejected.

## Minimum forward-test matrix

Before replacing an installed Skill, manually inspect at least:

1. course start from a multi-file STEM corpus;
2. one concept turn with a derivation or worked example;
3. correct answer in different wording;
4. partial answer requiring local repair and independent retry;
5. misconception requiring a prerequisite bridge;
6. clarification and direct-explanation requests that must not be graded;
7. pause and resume;
8. artifact access failure;
9. solution-material boundary;
10. a second real discipline with different representations;
11. one formula-fidelity check on a visually rendered source page;
12. one representation change where coefficients acquire new meaning.
13. complete source-to-objective coverage ledgers for two real courses;
14. chapter entry, local repair, readiness review, transition, and delayed
    revisit on both courses;
15. official exercise coverage and solution-quality review for every chapter or
    teaching unit in scope;
16. a combined question-and-solution file registered with safe bounded roles;
17. a route decision based on cumulative observations, including reopening an
    earlier objective after later evidence.
18. a complete past-paper inventory and question-level assessment map when the
    course corpus contains past papers;
19. one visual audit of a scanned or layout-dependent model solution, including
    any defect or authority restriction;
20. one mark-aware changed-context answer and one timed section using conditions
    stated by a supplied paper.
21. one due delayed retrieval that succeeds or fails without prior answer
    exposure, followed by the appropriate evidence judgment;
22. one protected timed baseline and a distinct protected timed posttest whose
    numerical difference is reported only as observed, non-causal change;
23. one leave-one-year-out past-paper audit that records novel held-out demands
    and explicitly refuses future-question prediction.
24. one cold re-entry with an unanswered Check that preserves position while
    rebuilding a self-contained explanation, and one warm continuation that
    does not unnecessarily replay it;
25. one source-specific convention taught naturally without leaking a raw
    filename into learner-facing prose.
26. one real zero-start lesson that teaches a complete conceptual arc without
    collapsing adjacent headings into a definition-and-quiz summary;
27. one classification lesson whose worked reasoning and changed-context Check
    use different objects or operations;
28. one raw-lecture page where formula, figure, or prose disagree, with the
    inconsistency resolved against the designated primary evidence.
29. one real multi-turn instructional episode in which a plausible learner
    misconception changes the evidence or representation used by the tutor;
30. one immediate transfer Check that differs from the worked case on at least
    two named dimensions and cannot be answered by noun substitution;
31. one zero-start forward lesson in a second real STEM course showing the same
    depth without copying the first course's prose structure.
32. one multi-source course whose main notes and raw lecture order topics
    differently, proving that sequence authority controls the first objective
    while the lecture enriches only the current boundary.
33. one non-physics, multi-source course with no master notes, proving that
    objective collection, canonicalization, typed prerequisites, route
    derivation, complete coverage, and conflict reporting work without a
    course-specific fixture.
34. one course with a professor-curated full-course notebook or textbook,
    proving that content inspection recognizes it as a Course Spine regardless
    of filename, preserves its supported sequence, and still captures
    exercise-only objectives and explicit limitations.
35. one teaching turn with a tempting false converse or single-case
    generalization, proving that the explanation states the inference boundary,
    uses dimensionally correct notation, closes its opening promise, and ends
    with a logically independent Check.

Report implementation verification separately from evidence of learner benefit.
No synthetic test can establish learning effectiveness.
