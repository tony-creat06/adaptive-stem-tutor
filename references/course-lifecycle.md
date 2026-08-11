# Course and chapter lifecycle

## Product intent

Teach a coherent course rather than a collection of attractive turns. The
default route follows the source-supported chapter or unit sequence, while
responding to prerequisite gaps, demonstrated competence, learner priorities,
and time constraints without silently losing coverage.

## Three course layers

Maintain:

1. a learner-facing orientation map of the course spine and prerequisite links;
2. a Curriculum Model with every objective, typed relation, sequence evidence,
   route basis, confidence, and conflict;
3. a coverage ledger with every bounded objective, source anchor, practice
   evidence, edition caveat, and route state.

When assessment sources exist, also maintain an assessment map. It connects
course objectives to real question forms and marks but never deletes objectives
that the sampled papers did not test.

The orientation map may be coarse. The coverage ledger may not. A topic is not
covered merely because its chapter heading appears in the map.

## Ordered route gate

Build and validate the route following `curriculum-modeling.md`. A route may use
one credible declared sequence, or it may be derived from Hard Prerequisites and
several weaker sequence signals when no master source exists.

Before choosing a new objective:

1. identify unfinished objectives whose Hard Prerequisites have sufficient
   evidence;
2. select the earliest ready objective in the validated route;
3. check whether learner evidence supports compression rather than omission;
4. activate a bounded prerequisite bridge if no intended target is ready;
5. record any learner-priority or exam-triage deviation and its return point.

This is the general form of the **first unfinished ordered objective** rule:
"ordered" now means prerequisite-safe position in the validated route, and
"unfinished" still requires the objective to be ready rather than merely the
first incomplete row.

Explanatory richness is selected only after the route position is locked. Raw
lecture order, an attractive demonstration, a past-paper frequency, or the
tutor's preferred conceptual sequence cannot silently skip a prerequisite or
unaccounted objective. If a credible main route begins with state variables and
a lecture deck begins with the zeroth law, teach the state-variable objective
first. If neither source controls sequence, derive and label the route rather
than arbitrarily choosing one.

## Entering a chapter

Before teaching:

- verify the chapter objectives and notation against primary sources;
- check prerequisite links and known earlier observations;
- inspect whether official exercises actually sample each objective;
- use one compact entry diagnostic when it will change the route;
- choose the smallest first objective that preserves the chapter's conceptual
  story.
- verify it is the first ready unfinished objective under the ordered route gate.

A strong diagnostic may compress explanation or move directly to transfer. It
does not erase the objective or prove retention. A blocking prerequisite gap
creates a bounded bridge, after which the chapter objective returns to view.

## While teaching

Update the route from cumulative evidence:

- `not_yet` with blocking severity: step back to the minimum prerequisite;
- local or procedural error: preserve correct reasoning and repair locally;
- ambiguous evidence: use a discriminating Check before changing depth;
- repeated immediate success: use a more integrated or changed-context task;
- later failure: reopen the objective as `review_due` or `needs_repair`;
- learner requests more or less depth: adapt presentation and practice density
  without inventing academic evidence.

Run `tutor_state.py progress` before a major route or chapter change. Treat the
summary as evidence to interpret, not an automatic score or promotion rule.

## Readiness review and transition

Before leaving a chapter:

1. account for every ledger objective;
2. use one integrative task or a compact set of discriminating checks;
3. record what has current evidence, what remains unresolved, and what was not
   sampled by official exercises;
4. carry blocking gaps forward explicitly or repair them before transition;
5. schedule retrieval after intervening material;
6. preview the conceptual need for the next chapter.

Chapter readiness and exam readiness are separate decisions. The former
supports moving through the course; the latter additionally needs mixed,
changed-context, mark-aware, and—where supported—timed evidence across the
assessment demands mapped from supplied papers.

`completed_with_current_evidence` means the current transition is justified. It
does not mean permanent mastery. If later work exposes a gap, reopen it.

## Alternate routes

For exam triage or a learner-chosen priority, re-order objectives only when the
dependency chain remains honest. Mark deferred or unsampled objectives rather
than claiming full-course coverage. When time is insufficient, report the
coverage tradeoff in learner language.

## Long-course continuity

Use spaced retrieval and integration across chapters. Later tasks should bring
back earlier ideas when the course naturally depends on them. Maintain one
current objective in the checkpoint; use the ledger and observation history for
the wider course state. Do not dump a dashboard into every teaching turn.
