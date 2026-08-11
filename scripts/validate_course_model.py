#!/usr/bin/env python3
"""Validate an adaptive-stem-tutor course-model.json file.

This validator deliberately checks structural claims only. It can prove that a
route is complete and prerequisite-safe; it cannot prove that the objectives or
relationships are educationally correct.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any


SCHEMA_VERSION = 1
RELATION_TYPES = {
    "related",
    "application",
    "extension",
    "contrast",
    "co_requisite",
}
SEQUENCE_STATUSES = {"declared", "derived", "conflicted", "provisional"}
CONFIDENCE_LEVELS = {"high", "medium", "low"}
EVIDENCE_KINDS = {"outcome", "teaching", "practice", "assessment"}
SPINE_STATUSES = {"verified", "bounded", "absent", "uncertain"}
AUTHORITY_AXES = {"scope", "sequence", "notation", "explanatory_support"}


class ModelValidationError(RuntimeError):
    """A deterministic structural validation failure."""


def require_object(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ModelValidationError(f"{field} must be an object")
    return value


def require_list(value: Any, field: str) -> list[Any]:
    if not isinstance(value, list):
        raise ModelValidationError(f"{field} must be a list")
    return value


def require_text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ModelValidationError(f"{field} must be a non-empty string")
    return value.strip()


def load_model(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ModelValidationError(f"course model does not exist: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ModelValidationError(f"invalid JSON: {exc}") from exc
    return require_object(payload, "course model")


def find_cycle(prerequisites: dict[str, list[str]]) -> list[str] | None:
    state = {objective_id: 0 for objective_id in prerequisites}
    stack: list[str] = []

    def visit(objective_id: str) -> list[str] | None:
        state[objective_id] = 1
        stack.append(objective_id)
        for prerequisite in prerequisites[objective_id]:
            if state[prerequisite] == 0:
                cycle = visit(prerequisite)
                if cycle:
                    return cycle
            elif state[prerequisite] == 1:
                start = stack.index(prerequisite)
                return stack[start:] + [prerequisite]
        stack.pop()
        state[objective_id] = 2
        return None

    for objective_id in prerequisites:
        if state[objective_id] == 0:
            cycle = visit(objective_id)
            if cycle:
                return cycle
    return None


def validate_model(model: dict[str, Any]) -> dict[str, int | str]:
    if model.get("schema_version") != SCHEMA_VERSION:
        raise ModelValidationError(
            f"schema_version must be {SCHEMA_VERSION}, got "
            f"{model.get('schema_version')!r}"
        )

    course = require_object(model.get("course"), "course")
    require_text(course.get("course_id"), "course.course_id")
    require_text(course.get("title"), "course.title")

    course_spine = require_object(model.get("course_spine"), "course_spine")
    spine_status = require_text(course_spine.get("status"), "course_spine.status")
    if spine_status not in SPINE_STATUSES:
        raise ModelValidationError(
            f"course_spine.status must be one of {sorted(SPINE_STATUSES)}"
        )

    spine_source_id = course_spine.get("source_id")
    if spine_status in {"verified", "bounded"}:
        require_text(spine_source_id, "course_spine.source_id")
    elif spine_source_id is not None:
        require_text(spine_source_id, "course_spine.source_id")

    raw_axes = require_list(
        course_spine.get("authority_axes"), "course_spine.authority_axes"
    )
    authority_axes = [
        require_text(value, f"course_spine.authority_axes[{index}]")
        for index, value in enumerate(raw_axes)
    ]
    if len(authority_axes) != len(set(authority_axes)):
        raise ModelValidationError("course_spine.authority_axes contains duplicates")
    unknown_axes = set(authority_axes) - AUTHORITY_AXES
    if unknown_axes:
        raise ModelValidationError(
            f"unknown course_spine authority axes: {sorted(unknown_axes)}"
        )
    if spine_status == "verified" and not {"scope", "sequence"}.issubset(
        authority_axes
    ):
        raise ModelValidationError(
            "verified course_spine requires scope and sequence authority"
        )
    if spine_status == "bounded" and not authority_axes:
        raise ModelValidationError(
            "bounded course_spine requires at least one authority axis"
        )
    if spine_status == "absent" and (
        spine_source_id is not None or authority_axes
    ):
        raise ModelValidationError(
            "absent course_spine requires null source_id and no authority axes"
        )

    spine_basis = require_list(course_spine.get("basis"), "course_spine.basis")
    if not spine_basis:
        raise ModelValidationError("course_spine.basis must not be empty")
    for index, value in enumerate(spine_basis):
        require_text(value, f"course_spine.basis[{index}]")
    spine_limitations = require_list(
        course_spine.get("limitations"), "course_spine.limitations"
    )
    for index, value in enumerate(spine_limitations):
        require_text(value, f"course_spine.limitations[{index}]")

    objectives = require_list(model.get("objectives"), "objectives")
    if not objectives:
        raise ModelValidationError("objectives must not be empty")

    by_id: dict[str, dict[str, Any]] = {}
    prerequisites: dict[str, list[str]] = {}
    for index, raw_objective in enumerate(objectives):
        field = f"objectives[{index}]"
        objective = require_object(raw_objective, field)
        objective_id = require_text(objective.get("objective_id"), f"{field}.objective_id")
        if objective_id in by_id:
            raise ModelValidationError(f"duplicate objective_id: {objective_id}")
        by_id[objective_id] = objective
        require_text(objective.get("title"), f"{field}.title")
        require_text(objective.get("criterion"), f"{field}.criterion")
        require_text(objective.get("section_id"), f"{field}.section_id")

        anchors = require_list(objective.get("source_anchors"), f"{field}.source_anchors")
        if not anchors:
            raise ModelValidationError(f"{field}.source_anchors must not be empty")
        for anchor_index, raw_anchor in enumerate(anchors):
            anchor_field = f"{field}.source_anchors[{anchor_index}]"
            anchor = require_object(raw_anchor, anchor_field)
            require_text(anchor.get("source_id"), f"{anchor_field}.source_id")
            require_text(anchor.get("locator"), f"{anchor_field}.locator")
            evidence_kind = require_text(
                anchor.get("evidence_kind"), f"{anchor_field}.evidence_kind"
            )
            if evidence_kind not in EVIDENCE_KINDS:
                raise ModelValidationError(
                    f"{anchor_field}.evidence_kind must be one of "
                    f"{sorted(EVIDENCE_KINDS)}"
                )

        prerequisite_list = require_list(
            objective.get("prerequisites"), f"{field}.prerequisites"
        )
        prerequisites[objective_id] = [
            require_text(value, f"{field}.prerequisites[{item_index}]")
            for item_index, value in enumerate(prerequisite_list)
        ]

        relations = require_list(objective.get("relations"), f"{field}.relations")
        for relation_index, raw_relation in enumerate(relations):
            relation_field = f"{field}.relations[{relation_index}]"
            relation = require_object(raw_relation, relation_field)
            relation_type = require_text(relation.get("type"), f"{relation_field}.type")
            if relation_type not in RELATION_TYPES:
                raise ModelValidationError(
                    f"{relation_field}.type must be one of {sorted(RELATION_TYPES)}"
                )
            require_text(relation.get("target"), f"{relation_field}.target")

        sequence_status = require_text(
            objective.get("sequence_status"), f"{field}.sequence_status"
        )
        if sequence_status not in SEQUENCE_STATUSES:
            raise ModelValidationError(
                f"{field}.sequence_status must be one of {sorted(SEQUENCE_STATUSES)}"
            )
        sequence_confidence = require_text(
            objective.get("sequence_confidence"), f"{field}.sequence_confidence"
        )
        if sequence_confidence not in CONFIDENCE_LEVELS:
            raise ModelValidationError(
                f"{field}.sequence_confidence must be one of {sorted(CONFIDENCE_LEVELS)}"
            )

    objective_ids = set(by_id)
    for objective_id, prerequisite_ids in prerequisites.items():
        if len(prerequisite_ids) != len(set(prerequisite_ids)):
            raise ModelValidationError(f"duplicate prerequisite on {objective_id}")
        for prerequisite_id in prerequisite_ids:
            if prerequisite_id == objective_id:
                raise ModelValidationError(f"self prerequisite on {objective_id}")
            if prerequisite_id not in objective_ids:
                raise ModelValidationError(
                    f"unknown prerequisite {prerequisite_id} on {objective_id}"
                )

        for relation in by_id[objective_id]["relations"]:
            target = relation["target"].strip()
            if target == objective_id:
                raise ModelValidationError(f"self relation on {objective_id}")
            if target not in objective_ids:
                raise ModelValidationError(
                    f"unknown relation target {target} on {objective_id}"
                )

    cycle = find_cycle(prerequisites)
    if cycle:
        raise ModelValidationError(
            "hard prerequisite cycle: " + " -> ".join(cycle)
        )

    route = require_list(model.get("route"), "route")
    if len(route) != len(objectives):
        raise ModelValidationError(
            f"route must contain every objective exactly once: "
            f"expected {len(objectives)}, got {len(route)}"
        )

    route_ids: list[str] = []
    for index, raw_step in enumerate(route):
        field = f"route[{index}]"
        step = require_object(raw_step, field)
        position = step.get("position")
        if not isinstance(position, int) or isinstance(position, bool):
            raise ModelValidationError(f"{field}.position must be an integer")
        if position != index + 1:
            raise ModelValidationError(
                f"route positions must be consecutive from 1; {field} is {position}"
            )
        objective_id = require_text(step.get("objective_id"), f"{field}.objective_id")
        route_ids.append(objective_id)
        basis = require_list(step.get("basis"), f"{field}.basis")
        if not basis:
            raise ModelValidationError(f"{field}.basis must not be empty")
        for basis_index, value in enumerate(basis):
            require_text(value, f"{field}.basis[{basis_index}]")
        confidence = require_text(step.get("confidence"), f"{field}.confidence")
        if confidence not in CONFIDENCE_LEVELS:
            raise ModelValidationError(
                f"{field}.confidence must be one of {sorted(CONFIDENCE_LEVELS)}"
            )

    if len(route_ids) != len(set(route_ids)):
        raise ModelValidationError("route contains a duplicate objective_id")
    missing = objective_ids - set(route_ids)
    unknown = set(route_ids) - objective_ids
    if missing or unknown:
        raise ModelValidationError(
            f"route objective mismatch; missing={sorted(missing)}, unknown={sorted(unknown)}"
        )

    position_by_id = {objective_id: index + 1 for index, objective_id in enumerate(route_ids)}
    for objective_id, prerequisite_ids in prerequisites.items():
        for prerequisite_id in prerequisite_ids:
            if position_by_id[prerequisite_id] >= position_by_id[objective_id]:
                raise ModelValidationError(
                    f"prerequisite {prerequisite_id} must precede {objective_id} in route"
                )

    conflicts = require_list(model.get("unresolved_conflicts"), "unresolved_conflicts")
    for index, raw_conflict in enumerate(conflicts):
        field = f"unresolved_conflicts[{index}]"
        conflict = require_object(raw_conflict, field)
        require_text(conflict.get("conflict_id"), f"{field}.conflict_id")
        conflict_objectives = require_list(
            conflict.get("objective_ids"), f"{field}.objective_ids"
        )
        if not conflict_objectives:
            raise ModelValidationError(f"{field}.objective_ids must not be empty")
        for objective_index, value in enumerate(conflict_objectives):
            objective_id = require_text(
                value, f"{field}.objective_ids[{objective_index}]"
            )
            if objective_id not in objective_ids:
                raise ModelValidationError(
                    f"unknown conflict objective {objective_id} in {field}"
                )
        require_text(conflict.get("summary"), f"{field}.summary")
        require_text(conflict.get("material_effect"), f"{field}.material_effect")

    return {
        "result": "valid",
        "course_spine_status": spine_status,
        "objective_count": len(objectives),
        "route_count": len(route),
        "conflict_count": len(conflicts),
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate a structured adaptive STEM course model."
    )
    parser.add_argument("course_model", help="path to course-model.json")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        result = validate_model(load_model(Path(args.course_model)))
    except ModelValidationError as exc:
        print(
            json.dumps({"result": "invalid", "error": str(exc)}, ensure_ascii=False),
            file=sys.stderr,
        )
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
