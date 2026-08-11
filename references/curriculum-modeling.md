# Curriculum modeling

## Contents

1. Product rule
2. Inputs and outputs
3. Course Spine decision
4. Objective collection
5. Canonicalization
6. Relationship typing
7. Sequence evidence
8. Route construction
9. Conflict and confidence
10. Coverage audit
11. Dynamic routing
12. Corpus patterns
13. Required model fields

## Product rule

Treat a professor-curated, course-wide notebook, textbook, reader, student
version, or set of notes as a valuable Course Spine candidate. Do not equate its
filename, table of contents, lecture chronology, folder order, or exam frequency
with verified course authority. Make the spine decision from inspected content,
then compile a Curriculum Model before producing a course route.

The model must distinguish:

- what the learner should be able to do;
- why that capability belongs in the course;
- what it genuinely depends on;
- which weaker relationships connect it to other capabilities;
- what sources say about order;
- what route was chosen and with what confidence.

## Inputs and outputs

Inspect all sources needed to establish scope before claiming a complete model.
An initial model may be explicitly partial when unreadable or missing material
prevents full coverage.

Produce:

1. `course-model.json`: structured objectives, edges, source anchors, sequence
   evidence, route, confidence, and conflicts;
2. `coverage-ledger.md`: readable projection accounting for every objective;
3. `course-map.md`: compact learner orientation projected from the model;
4. `assessment-map.md` when supplied assessments are used.

The map is not the model. The route is not the extraction order.

## Course Spine decision

Search for a Course Spine candidate before assembling the route. Names such as
`textbook`, `notebook`, `course notes`, `student version`, `reader`, and
`lecture notes` are discovery hints only. A generic adopted textbook may qualify
when the course actually follows it; an impressive professor PDF may not qualify
when it is a revision summary, selected chapters, solutions, or an older edition.

Inspect internal evidence across the beginning, middle, and end of each serious
candidate, and compare it with the syllabus, exercise set, and supplied
assessments where available. Check:

- course identity, instructor or departmental provenance, and currentness;
- breadth across the declared units rather than a long page count;
- coherent cross-unit progression and explicit prerequisite assumptions;
- stable notation, definitions, and conventions;
- sufficient explanatory depth rather than headings or formula summary only;
- visible omissions, enrichment chapters, legacy content, and edition drift.

Record exactly one spine status in `course-model.json`:

- `verified`: one current source coherently covers the course and may scaffold
  both scope and sequence;
- `bounded`: a coherent source is useful but only for declared units, editions,
  or Authority Axes;
- `absent`: no supplied source plausibly serves as a course-wide spine;
- `uncertain`: a candidate exists but unreadable content, version ambiguity, or
  conflict prevents a safe decision.

For `verified`, initialize candidate objectives and section order from the spine,
then cross-check all other source roles. Preserve exercise-only capabilities,
assessment depth, notation conflicts, and gaps; do not force them out because
they are absent from a heading. For `bounded`, use only its recorded axes and
locations. For `absent` or `uncertain`, collect across the corpus and derive the
route from prerequisites plus sequence evidence. Never make the learner choose a
file merely because several filenames look plausible when content can settle it.

## Objective collection

Read across the corpus in bounded passes:

1. collect declared learning outcomes and syllabus sections;
2. inspect teaching sources for concepts, mechanisms, derivations, methods,
   representations, conditions, and applications;
3. inspect exercises for capabilities the learner must perform but the notes
   may only imply;
4. inspect assessments for expected depth and answer form, not for syllabus
   replacement;
5. record gaps, conflicting conventions, and material that is merely enrichment.

Write each Learning Objective as one observable capability: explain, distinguish,
derive, calculate, construct, interpret, prove, debug, design, or apply. Split a
heading that hides several independent capabilities. Do not create a separate
objective for every example, anecdote, formula occurrence, or slide.

Every objective needs at least one precise Objective Evidence anchor. A heading
alone may propose a candidate but does not prove its criterion or depth.

## Canonicalization

Merge candidates only when they require the same learner capability under the
same relevant conditions. Preserve aliases and all source anchors.

Keep separate objectives when they differ in:

- action: state versus derive versus apply;
- representation: symbolic, graphical, computational, experimental;
- assumptions or validity range;
- expected depth or assessment demand;
- prerequisite structure.

Do not merge two objectives merely because their nouns match. Do not keep two
objectives merely because different files use different names.

## Relationship typing

Use `hard_prerequisite` only when the learner cannot meaningfully perform the
target without the source capability. Support it with an explicit source signal,
a task dependency, or a short domain justification.

Use weaker typed relations instead of inflating the prerequisite graph:

- `related`: useful conceptual connection;
- `application`: source capability is used in the target context;
- `extension`: target generalizes or deepens the source;
- `contrast`: the distinction itself prevents confusion;
- `co_requisite`: best learned together, but neither is a strict prerequisite.

Page adjacency, lecture chronology, and shared vocabulary are not prerequisite
evidence. A later assessment question using two topics proves integration, not
necessarily a one-way prerequisite.

## Sequence evidence

Record sequence evidence separately from prerequisite edges. Useful signals,
roughly from stronger to weaker, are:

1. explicit current syllabus dependencies or numbered outcomes;
2. a coherent current course text or instructor-declared route;
3. current lecture chronology with visible conceptual continuity;
4. exercise progression that requires earlier methods;
5. repeated order across independent teaching sources;
6. a domain-supported pedagogical preference.

Assessment frequency affects practice allocation and revision priority. It does
not by itself move a later objective ahead of its foundations.

For every source used as scope, sequence, notation, or explanatory support,
record the relevant Authority Axis. No file must control all axes.

## Route construction

Construct the Teaching Route in this order:

1. create the directed graph of `hard_prerequisite` edges;
2. reject or resolve cycles; do not break them silently;
3. topologically identify the currently ready objectives;
4. among ready objectives, prefer stronger sequence evidence;
5. when evidence ties, prefer conceptual continuity and lower context switching;
6. retain every objective exactly once in the complete route;
7. attach route basis and confidence to each position;
8. project chapter or unit groupings without changing the dependency order.

The next teaching target is the first `ready` unfinished objective, not simply
the first row whose status is incomplete. An objective is ready only when every
Hard Prerequisite has sufficient current evidence or an explicit bounded bridge
is active.

Do not use an LLM preference as an invisible tie-break. Record it as
`domain_inference` with a justification and no higher than medium confidence
unless corroborated.

## Conflict and confidence

Use route confidence:

- `high`: explicit current order and prerequisite evidence agree;
- `medium`: prerequisites are clear but remaining order uses corroborated or
  domain-supported inference;
- `low`: material is incomplete or several materially different routes remain.

Use sequence status:

- `declared`: directly supported by a designated current source;
- `derived`: constructed from prerequisites and multiple evidence signals;
- `conflicted`: credible sources disagree or a cycle remains unresolved;
- `provisional`: insufficient material for a stable route.

Record a Route Conflict when alternatives would change prerequisites, omit
content, change notation authority, or materially alter the first study units.
Ask the learner only when the unresolved choice materially changes the course
and cannot be resolved from the supplied material. Otherwise choose the safest
provisional route, label it, and preserve the conflict.

## Coverage audit

Before teaching from a supposedly complete course model, verify:

- every collected objective appears exactly once in the route;
- every objective has Objective Evidence;
- every prerequisite target exists and precedes its dependent;
- no hard-prerequisite cycle remains;
- duplicate aliases were merged without losing anchors;
- objectives inferred only from exercises are labeled;
- gaps and unreadable sources remain visible;
- course-map sections project all route objectives;
- assessments map to objectives rather than creating silent syllabus items.

Run `scripts/validate_course_model.py <course-model.json>`. Structural validation
does not prove semantic correctness; manually inspect the objective wording,
edge justifications, conflicts, and learner-facing route.

## Dynamic routing

The complete route stays durable while the active path adapts:

- compress an objective only after relevant learner evidence;
- open a bounded prerequisite bridge when a gap blocks the current target;
- return to the target after the bridge;
- mark a learner-prioritized or exam-triage detour and its return point;
- reopen earlier objectives when later evidence exposes a gap;
- never delete deferred objectives from coverage.

Dynamic adaptation changes pacing and active path, not the historical evidence
for why the course contains and orders its objectives.

## Corpus patterns

### One coherent current textbook

Use its order as strong sequence evidence, but still split compound headings,
audit exercises, and validate prerequisites. A textbook can omit a bridge or
assume prior knowledge.

### Slide collection with no master notes

Collect objectives across all decks, infer prerequisites from explanations and
tasks, then use lecture chronology only among prerequisite-ready objectives.
Mark uncorroborated order as derived or provisional.

### Lab- or project-led course

Start from the capabilities required by each lab or milestone, recursively add
their prerequisites, and retain conceptual objectives that support explanation
and debugging. Project order is sequence evidence, not proof that every
prerequisite is taught before use.

### Problem sheets plus sparse notes

Reverse-map each task to required capabilities, separate practice from solution
evidence, and label teaching gaps. Do not pretend the problem order alone is a
complete curriculum.

### Assessment-only corpus

Build only a provisional demand map and prerequisite scaffold. State that course
coverage is not established; do not manufacture a complete syllabus from past
papers.

### Conflicting editions or instructors

Resolve current scope and notation first. Preserve both sequence proposals as
evidence, then derive a prerequisite-safe route and record remaining conflicts.

## Required model fields

Each objective in `course-model.json` must include:

- stable `objective_id`, `title`, and observable `criterion`;
- `section_id` or explicit ungrouped status;
- one or more `source_anchors` with source ID and locator;
- `prerequisites` and typed `relations`;
- `sequence_status` and `sequence_confidence`.

The complete `route` must include each objective exactly once with a consecutive
position, non-empty basis, and confidence. `unresolved_conflicts` must list
material conflicts rather than hiding them in prose.

The model must also contain `course_spine` with `status`, nullable `source_id`,
supported `authority_axes`, non-empty decision `basis`, and `limitations`.
`verified` requires scope and sequence authority; `absent` requires no source ID
or authority axes.
