#!/usr/bin/env python3
"""Small, local persistence helper for adaptive-stem-tutor.

The helper stores resumable course context and concise answer observations. It
does not generate lessons, evaluate learners, or assign mastery scores.
"""

from __future__ import annotations

import argparse
import contextlib
import fcntl
import hashlib
import json
import os
from pathlib import Path
import tempfile
from typing import Any, Iterator
from datetime import datetime, timedelta, timezone


SCHEMA_VERSION = 1
STATE_DIR_NAME = ".adaptive-stem-tutor"
STATE_FILE = "state.json"
SOURCE_FILE = "source-index.json"
OBSERVATION_FILE = "observations.jsonl"
RETRIEVAL_FILE = "retrieval-plan.json"
ATTEMPT_FILE = "assessment-attempts.jsonl"
LOCK_FILE = ".lock"

SOURCE_ROLES = {
    "primary_teaching",
    "assessment",
    "practice",
    "solution_reference",
    "administrative",
    "supplementary",
    "unreviewed",
}
REVIEW_STATES = {"reviewed", "partially_reviewed", "unreviewed", "unreadable"}
SESSION_STATUSES = {"not_started", "active", "paused", "complete"}
JUDGMENTS = {
    "observed_once",
    "transfer_observed",
    "retained_later",
    "integrated",
    "partial",
    "not_yet",
    "uncertain",
}
ERROR_TYPES = {
    "none",
    "concept",
    "procedure",
    "representation",
    "interpretation",
    "arithmetic",
    "communication",
    "mixed",
    "uncertain",
}
UNCERTAINTIES = {"low", "medium", "high"}
SEVERITIES = {"none", "harmless", "local", "blocking", "uncertain"}
CHECKPOINT_FIELDS = {
    "status",
    "chapter_id",
    "chapter_title",
    "chapter_stage",
    "section",
    "objective_id",
    "objective_title",
    "focus",
    "last_teaching_summary",
    "pending_check",
    "next_action",
}
CHAPTER_STAGES = {
    "diagnostic",
    "teaching",
    "consolidation",
    "readiness_review",
    "review_due",
    "transitioned",
}
SOURCE_EXPOSURES = {
    "unseen_before_attempt",
    "seen_before_attempt",
    "unknown",
}
ATTEMPT_KINDS = {
    "baseline",
    "chapter_exam_bridge",
    "retrieval",
    "timed_section",
    "full_paper",
    "posttest",
}
FORM_STATUSES = {"held_out_unseen", "previously_exposed", "unknown"}


class TutorStateError(RuntimeError):
    """Expected user-facing command error."""


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def clean_text(value: Any, field: str, *, required: bool = False) -> str | None:
    if value is None:
        if required:
            raise TutorStateError(f"{field} is required")
        return None
    if not isinstance(value, str):
        raise TutorStateError(f"{field} must be a string or null")
    value = value.strip()
    if required and not value:
        raise TutorStateError(f"{field} must not be empty")
    if len(value) > 20_000:
        raise TutorStateError(f"{field} is unexpectedly long")
    return value


def resolve_workspace(raw: str, *, create: bool = False) -> Path:
    candidate = Path(raw).expanduser()
    if create:
        candidate.mkdir(parents=True, exist_ok=True)
    try:
        workspace = candidate.resolve(strict=True)
    except FileNotFoundError as exc:
        raise TutorStateError(f"workspace does not exist: {candidate}") from exc
    if not workspace.is_dir():
        raise TutorStateError(f"workspace is not a directory: {workspace}")
    return workspace


def paths_for(workspace: Path) -> dict[str, Path]:
    state_dir = workspace / STATE_DIR_NAME
    return {
        "dir": state_dir,
        "state": state_dir / STATE_FILE,
        "sources": state_dir / SOURCE_FILE,
        "observations": state_dir / OBSERVATION_FILE,
        "retrievals": state_dir / RETRIEVAL_FILE,
        "attempts": state_dir / ATTEMPT_FILE,
        "lock": state_dir / LOCK_FILE,
        "checkpoint": workspace / "checkpoint.md",
    }


@contextlib.contextmanager
def locked(paths: dict[str, Path]) -> Iterator[None]:
    paths["dir"].mkdir(mode=0o700, parents=True, exist_ok=True)
    if paths["dir"].is_symlink():
        raise TutorStateError("state directory must not be a symbolic link")
    with paths["lock"].open("a+", encoding="utf-8") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    body = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary_path = Path(temporary)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(body)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, path)
        directory_fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        if temporary_path.exists():
            temporary_path.unlink()


def atomic_text(path: Path, body: str) -> None:
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary_path = Path(temporary)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(body)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, path)
        directory_fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        if temporary_path.exists():
            temporary_path.unlink()


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise TutorStateError(f"missing state file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise TutorStateError(f"invalid JSON in {path.name}: {exc}") from exc
    if not isinstance(value, dict):
        raise TutorStateError(f"{path.name} must contain a JSON object")
    if value.get("schema_version") != SCHEMA_VERSION:
        raise TutorStateError(
            f"unsupported schema version in {path.name}: "
            f"{value.get('schema_version')!r}"
        )
    return value


def read_payload(path_string: str) -> dict[str, Any]:
    path = Path(path_string).expanduser().resolve(strict=True)
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TutorStateError("input JSON must contain an object")
    return value


def parse_timestamp(value: Any, field: str) -> tuple[datetime, str]:
    text = clean_text(value, field, required=True)
    assert text is not None
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise TutorStateError(f"{field} must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise TutorStateError(f"{field} must include a timezone")
    normalized = parsed.astimezone(timezone.utc)
    return normalized, normalized.isoformat(timespec="seconds")


def clean_bool(value: Any, field: str, *, required: bool = False) -> bool | None:
    if value is None and not required:
        return None
    if not isinstance(value, bool):
        raise TutorStateError(f"{field} must be a boolean")
    return value


def clean_number(
    value: Any,
    field: str,
    *,
    required: bool = False,
    minimum: float | None = None,
) -> float | None:
    if value is None and not required:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TutorStateError(f"{field} must be a number")
    result = float(value)
    if minimum is not None and result < minimum:
        raise TutorStateError(f"{field} must be at least {minimum:g}")
    return result


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def checkpoint_markdown(state: dict[str, Any]) -> str:
    course = state["course"]
    current = state["current"]
    language = course.get("learner_language", "en")
    if language.lower().startswith("zh"):
        labels = {
            "heading": "学习检查点",
            "course": "课程",
            "status": "状态",
            "chapter": "当前章节",
            "stage": "章节阶段",
            "section": "当前位置",
            "objective": "当前目标",
            "focus": "当前重点",
            "summary": "最近学习",
            "check": "待回答问题",
            "next": "下一步",
            "updated": "更新时间",
            "empty": "尚未确定",
        }
    else:
        labels = {
            "heading": "Learning checkpoint",
            "course": "Course",
            "status": "Status",
            "chapter": "Current chapter",
            "stage": "Chapter stage",
            "section": "Current section",
            "objective": "Current objective",
            "focus": "Current focus",
            "summary": "Latest teaching",
            "check": "Pending check",
            "next": "Next move",
            "updated": "Updated",
            "empty": "Not set",
        }

    def shown(value: Any) -> str:
        if value is None or value == "":
            return labels["empty"]
        return str(value).replace("\n", " ").strip()

    if language.lower().startswith("zh"):
        status_names = {
            "not_started": "未开始",
            "active": "学习中",
            "paused": "已暂停",
            "complete": "已结束",
        }
        stage_names = {
            "diagnostic": "起点诊断",
            "teaching": "学习中",
            "consolidation": "整合练习",
            "readiness_review": "转章准备",
            "review_due": "需要回顾",
            "transitioned": "已转入下一章",
        }
    else:
        status_names = {
            "not_started": "Not started",
            "active": "Active",
            "paused": "Paused",
            "complete": "Complete",
        }
        stage_names = {
            "diagnostic": "Entry diagnostic",
            "teaching": "Teaching",
            "consolidation": "Consolidation",
            "readiness_review": "Readiness review",
            "review_due": "Review due",
            "transitioned": "Transitioned",
        }

    return (
        f"# {labels['heading']}\n\n"
        f"- {labels['course']}: {shown(course.get('code'))} — "
        f"{shown(course.get('title'))}\n"
        f"- {labels['status']}: "
        f"{shown(status_names.get(current.get('status'), current.get('status')))}\n"
        f"- {labels['chapter']}: {shown(current.get('chapter_title'))}\n"
        f"- {labels['stage']}: "
        f"{shown(stage_names.get(current.get('chapter_stage'), current.get('chapter_stage')))}\n"
        f"- {labels['section']}: {shown(current.get('section'))}\n"
        f"- {labels['objective']}: {shown(current.get('objective_title'))}\n"
        f"- {labels['focus']}: {shown(current.get('focus'))}\n"
        f"- {labels['summary']}: {shown(current.get('last_teaching_summary'))}\n"
        f"- {labels['check']}: {shown(current.get('pending_check'))}\n"
        f"- {labels['next']}: {shown(current.get('next_action'))}\n"
        f"- {labels['updated']}: {shown(state.get('updated_at'))}\n"
    )


def save_state(paths: dict[str, Path], state: dict[str, Any]) -> None:
    state["updated_at"] = now_utc()
    atomic_json(paths["state"], state)
    atomic_text(paths["checkpoint"], checkpoint_markdown(state))


def command_init(args: argparse.Namespace) -> dict[str, Any]:
    workspace = resolve_workspace(args.workspace, create=True)
    paths = paths_for(workspace)
    with locked(paths):
        existing = [
            path.name
            for path in (
                paths["state"],
                paths["sources"],
                paths["observations"],
                paths["retrievals"],
                paths["attempts"],
            )
            if path.exists()
        ]
        if existing:
            raise TutorStateError(
                "refusing to overwrite existing tutor state: " + ", ".join(existing)
            )
        created_at = now_utc()
        state = {
            "schema_version": SCHEMA_VERSION,
            "course": {
                "code": clean_text(args.course_code, "course_code", required=True),
                "title": clean_text(args.course_title, "course_title", required=True),
                "learner_language": clean_text(
                    args.learner_language, "learner_language", required=True
                ),
            },
            "current": {
                "status": "not_started",
                "chapter_id": None,
                "chapter_title": None,
                "chapter_stage": None,
                "section": None,
                "objective_id": None,
                "objective_title": None,
                "focus": None,
                "last_teaching_summary": None,
                "pending_check": None,
                "next_action": "Review primary materials and build the first course map.",
            },
            "last_observation": None,
            "created_at": created_at,
            "updated_at": created_at,
            "paused_at": None,
            "resumed_at": None,
        }
        sources = {
            "schema_version": SCHEMA_VERSION,
            "sources": [],
            "created_at": created_at,
            "updated_at": created_at,
        }
        atomic_json(paths["state"], state)
        atomic_json(paths["sources"], sources)
        paths["observations"].touch(mode=0o600, exist_ok=False)
        atomic_json(
            paths["retrievals"],
            {
                "schema_version": SCHEMA_VERSION,
                "retrievals": [],
                "created_at": created_at,
                "updated_at": created_at,
            },
        )
        paths["attempts"].touch(mode=0o600, exist_ok=False)
        atomic_text(paths["checkpoint"], checkpoint_markdown(state))
    return {"result": "initialized", "workspace": str(workspace)}


def command_register_source(args: argparse.Namespace) -> dict[str, Any]:
    workspace = resolve_workspace(args.workspace)
    paths = paths_for(workspace)
    source_path = Path(args.path).expanduser().resolve(strict=True)
    if not source_path.is_file():
        raise TutorStateError(f"source is not a regular file: {source_path}")
    if args.role not in SOURCE_ROLES:
        raise TutorStateError(f"unsupported source role: {args.role}")
    if args.review_state not in REVIEW_STATES:
        raise TutorStateError(f"unsupported review state: {args.review_state}")
    record = {
        "source_id": clean_text(args.source_id, "source_id", required=True),
        "label": clean_text(args.label, "label", required=True),
        "path": str(source_path),
        "role": args.role,
        "review_state": args.review_state,
        "scope": clean_text(args.scope, "scope"),
        "sha256": file_sha256(source_path),
        "size_bytes": source_path.stat().st_size,
        "registered_at": now_utc(),
    }
    edition = clean_text(args.edition, "edition")
    authority_note = clean_text(args.authority_note, "authority_note")
    if edition is not None:
        record["edition"] = edition
    if authority_note is not None:
        record["authority_note"] = authority_note
    with locked(paths):
        index = read_json(paths["sources"])
        matching = [
            item
            for item in index.get("sources", [])
            if item.get("source_id") == record["source_id"]
        ]
        if matching and not args.replace:
            comparable = dict(record)
            comparable.pop("registered_at")
            existing = dict(matching[0])
            existing.pop("registered_at", None)
            if existing == comparable:
                return {"result": "unchanged", "source_id": record["source_id"]}
            raise TutorStateError(
                "source_id already exists with different content or metadata; "
                "inspect it and use --replace only when the change is intended"
            )
        remaining = [
            item
            for item in index.get("sources", [])
            if item.get("source_id") != record["source_id"]
        ]
        remaining.append(record)
        index["sources"] = sorted(remaining, key=lambda item: item["source_id"])
        index["updated_at"] = now_utc()
        atomic_json(paths["sources"], index)
    return {"result": "registered", "source_id": record["source_id"]}


def command_update(args: argparse.Namespace) -> dict[str, Any]:
    workspace = resolve_workspace(args.workspace)
    paths = paths_for(workspace)
    update = read_payload(args.from_json)
    unknown = set(update) - CHECKPOINT_FIELDS
    if unknown:
        raise TutorStateError("unknown checkpoint fields: " + ", ".join(sorted(unknown)))
    if "status" in update and update["status"] not in SESSION_STATUSES:
        raise TutorStateError(f"unsupported status: {update['status']}")
    if (
        "chapter_stage" in update
        and update["chapter_stage"] is not None
        and update["chapter_stage"] not in CHAPTER_STAGES
    ):
        raise TutorStateError(f"unsupported chapter_stage: {update['chapter_stage']}")
    for field in CHECKPOINT_FIELDS - {"status", "chapter_stage"}:
        if field in update:
            update[field] = clean_text(update[field], field)
    with locked(paths):
        state = read_json(paths["state"])
        state["current"].update(update)
        save_state(paths, state)
    return {"result": "updated", "changed_fields": sorted(update)}


def empty_retrieval_plan(created_at: str | None = None) -> dict[str, Any]:
    timestamp = created_at or now_utc()
    return {
        "schema_version": SCHEMA_VERSION,
        "retrievals": [],
        "created_at": timestamp,
        "updated_at": timestamp,
    }


def read_retrieval_plan(path: Path, *, missing_ok: bool = False) -> dict[str, Any]:
    if missing_ok and not path.exists():
        return empty_retrieval_plan()
    plan = read_json(path)
    retrievals = plan.get("retrievals")
    if not isinstance(retrievals, list):
        raise TutorStateError("retrieval-plan.json must contain a retrievals list")
    return plan


def read_jsonl_records(
    path: Path, label: str, *, missing_ok: bool = False
) -> list[dict[str, Any]]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError as exc:
        if missing_ok:
            return []
        raise TutorStateError(f"{label} is missing") from exc
    records: list[dict[str, Any]] = []
    for number, line in enumerate(lines, start=1):
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise TutorStateError(f"invalid {label} at line {number}: {exc}") from exc
        if not isinstance(value, dict):
            raise TutorStateError(f"invalid {label} at line {number}: not an object")
        records.append(value)
    return records


def append_jsonl_record(path: Path, record: dict[str, Any], label: str) -> None:
    line = json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n"
    if len(line.encode("utf-8")) > 64 * 1024:
        raise TutorStateError(f"{label} record is unexpectedly large")
    try:
        existing = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        existing = ""
    if len(existing.encode("utf-8")) > 32 * 1024 * 1024:
        raise TutorStateError(f"{label} is too large for a safe atomic append")
    atomic_text(path, existing + line)


def command_schedule_retrieval(args: argparse.Namespace) -> dict[str, Any]:
    workspace = resolve_workspace(args.workspace)
    paths = paths_for(workspace)
    request = read_payload(args.from_json)
    allowed = {
        "retrieval_id",
        "chapter_id",
        "objective_id",
        "criterion",
        "prior_evidence_at",
        "due_at",
        "minimum_delay_days",
        "context_change",
    }
    unknown = set(request) - allowed
    if unknown:
        raise TutorStateError("unknown retrieval fields: " + ", ".join(sorted(unknown)))
    retrieval_id = clean_text(request.get("retrieval_id"), "retrieval_id", required=True)
    objective_id = clean_text(request.get("objective_id"), "objective_id", required=True)
    criterion = clean_text(request.get("criterion"), "criterion", required=True)
    chapter_id = clean_text(request.get("chapter_id"), "chapter_id")
    context_change = clean_text(
        request.get("context_change"), "context_change", required=True
    )
    minimum_delay = clean_number(
        request.get("minimum_delay_days"),
        "minimum_delay_days",
        required=True,
        minimum=1,
    )
    assert minimum_delay is not None
    if not minimum_delay.is_integer():
        raise TutorStateError("minimum_delay_days must be a whole number")
    prior_time, prior_text = parse_timestamp(
        request.get("prior_evidence_at"), "prior_evidence_at"
    )
    due_time, due_text = parse_timestamp(request.get("due_at"), "due_at")
    if due_time < prior_time + timedelta(days=int(minimum_delay)):
        raise TutorStateError("due_at does not satisfy minimum_delay_days")
    record = {
        "retrieval_id": retrieval_id,
        "chapter_id": chapter_id,
        "objective_id": objective_id,
        "criterion": criterion,
        "prior_evidence_at": prior_text,
        "due_at": due_text,
        "minimum_delay_days": int(minimum_delay),
        "context_change": context_change,
        "status": "pending",
        "scheduled_at": now_utc(),
        "completed_at": None,
    }
    with locked(paths):
        plan = read_retrieval_plan(paths["retrievals"], missing_ok=True)
        if any(
            item.get("retrieval_id") == retrieval_id
            for item in plan.get("retrievals", [])
        ):
            raise TutorStateError("retrieval_id already exists")
        plan["retrievals"].append(record)
        plan["retrievals"] = sorted(
            plan["retrievals"],
            key=lambda item: (
                item.get("due_at", ""),
                item.get("retrieval_id", ""),
            ),
        )
        plan["updated_at"] = now_utc()
        atomic_json(paths["retrievals"], plan)
    return {"result": "scheduled", "retrieval_id": retrieval_id, "due_at": due_text}


def command_due_retrievals(args: argparse.Namespace) -> dict[str, Any]:
    workspace = resolve_workspace(args.workspace)
    paths = paths_for(workspace)
    if args.as_of:
        as_of, as_of_text = parse_timestamp(args.as_of, "as_of")
    else:
        as_of_text = now_utc()
        as_of, as_of_text = parse_timestamp(as_of_text, "as_of")
    with locked(paths):
        plan = read_retrieval_plan(paths["retrievals"], missing_ok=True)
    pending = [
        item for item in plan.get("retrievals", []) if item.get("status") == "pending"
    ]
    due = [
        item
        for item in pending
        if parse_timestamp(item.get("due_at"), "due_at")[0] <= as_of
    ]
    upcoming = [item for item in pending if item not in due]
    return {
        "as_of": as_of_text,
        "due_count": len(due),
        "upcoming_count": len(upcoming),
        "due": due,
        "upcoming": upcoming,
    }


def clean_string_list(value: Any, field: str) -> list[str]:
    if not isinstance(value, list) or not value:
        raise TutorStateError(f"{field} must be a non-empty list")
    cleaned: list[str] = []
    for number, item in enumerate(value, start=1):
        text = clean_text(item, f"{field}[{number}]", required=True)
        assert text is not None
        if text not in cleaned:
            cleaned.append(text)
    return cleaned


def command_record_attempt(args: argparse.Namespace) -> dict[str, Any]:
    workspace = resolve_workspace(args.workspace)
    paths = paths_for(workspace)
    request = read_payload(args.from_json)
    allowed = {
        "attempt_id",
        "kind",
        "task_id",
        "objective_ids",
        "marks_awarded",
        "marks_available",
        "timed",
        "duration_seconds",
        "independent",
        "solution_seen_before_attempt",
        "form_status",
        "protocol_id",
        "form_id",
        "evidence_summary",
        "conditions_note",
        "attempted_at",
    }
    unknown = set(request) - allowed
    if unknown:
        raise TutorStateError("unknown attempt fields: " + ", ".join(sorted(unknown)))
    attempt_id = clean_text(request.get("attempt_id"), "attempt_id", required=True)
    kind = request.get("kind")
    if kind not in ATTEMPT_KINDS:
        raise TutorStateError(f"unsupported attempt kind: {kind!r}")
    task_id = clean_text(request.get("task_id"), "task_id", required=True)
    objective_ids = clean_string_list(request.get("objective_ids"), "objective_ids")
    marks_available = clean_number(
        request.get("marks_available"), "marks_available", required=True, minimum=0.01
    )
    marks_awarded = clean_number(
        request.get("marks_awarded"), "marks_awarded", required=True, minimum=0
    )
    assert marks_available is not None and marks_awarded is not None
    if marks_awarded > marks_available:
        raise TutorStateError("marks_awarded cannot exceed marks_available")
    timed = clean_bool(request.get("timed"), "timed", required=True)
    independent = clean_bool(
        request.get("independent"), "independent", required=True
    )
    solution_seen = clean_bool(
        request.get("solution_seen_before_attempt"),
        "solution_seen_before_attempt",
        required=True,
    )
    duration = clean_number(
        request.get("duration_seconds"), "duration_seconds", minimum=1
    )
    if duration is not None and not duration.is_integer():
        raise TutorStateError("duration_seconds must be a whole number")
    if timed and duration is None:
        raise TutorStateError("a timed attempt requires duration_seconds")
    if not timed and duration is not None:
        raise TutorStateError("duration_seconds requires timed=true")
    form_status = request.get("form_status", "unknown")
    if form_status not in FORM_STATUSES:
        raise TutorStateError(f"unsupported form_status: {form_status!r}")
    protocol_id = clean_text(request.get("protocol_id"), "protocol_id")
    form_id = clean_text(request.get("form_id"), "form_id")
    evidence_summary = clean_text(
        request.get("evidence_summary"), "evidence_summary", required=True
    )
    conditions_note = clean_text(request.get("conditions_note"), "conditions_note")
    if request.get("attempted_at") is None:
        attempted_at = now_utc()
    else:
        attempted_at = parse_timestamp(request.get("attempted_at"), "attempted_at")[1]

    if kind in {"baseline", "posttest"}:
        if independent is not True or solution_seen is not False:
            raise TutorStateError(
                "baseline and posttest attempts must be independent and solution-blind"
            )
        if timed is not True:
            raise TutorStateError("baseline and posttest attempts must be timed")
        if form_status != "held_out_unseen":
            raise TutorStateError(
                "baseline and posttest forms must be held_out_unseen before the attempt"
            )
        if protocol_id is None or form_id is None:
            raise TutorStateError(
                "baseline and posttest attempts require protocol_id and form_id"
            )
    if kind in {"timed_section", "full_paper"} and timed is not True:
        raise TutorStateError(f"{kind} must be timed")

    record = {
        "attempt_id": attempt_id,
        "kind": kind,
        "task_id": task_id,
        "objective_ids": objective_ids,
        "marks_awarded": marks_awarded,
        "marks_available": marks_available,
        "score_fraction": marks_awarded / marks_available,
        "timed": timed,
        "duration_seconds": int(duration) if duration is not None else None,
        "independent": independent,
        "solution_seen_before_attempt": solution_seen,
        "form_status": form_status,
        "protocol_id": protocol_id,
        "form_id": form_id,
        "evidence_summary": evidence_summary,
        "conditions_note": conditions_note,
        "attempted_at": attempted_at,
        "recorded_at": now_utc(),
    }
    with locked(paths):
        attempts = read_jsonl_records(
            paths["attempts"], "assessment-attempts.jsonl", missing_ok=True
        )
        if any(item.get("attempt_id") == attempt_id for item in attempts):
            raise TutorStateError("attempt_id already exists")
        if kind in {"baseline", "posttest"} and any(
            item.get("kind") == kind
            and item.get("protocol_id") == protocol_id
            for item in attempts
        ):
            raise TutorStateError(
                f"protocol_id already contains a {kind} attempt"
            )
        if kind == "posttest":
            baselines = [
                item
                for item in attempts
                if item.get("kind") == "baseline"
                and item.get("protocol_id") == protocol_id
            ]
            if not baselines:
                raise TutorStateError("posttest requires an earlier baseline in the protocol")
            posttest_time = parse_timestamp(attempted_at, "attempted_at")[0]
            if not any(
                parse_timestamp(item.get("attempted_at"), "attempted_at")[0]
                < posttest_time
                for item in baselines
            ):
                raise TutorStateError(
                    "posttest attempted_at must be later than the baseline"
                )
            if any(item.get("form_id") == form_id for item in baselines):
                raise TutorStateError("posttest must use a form distinct from the baseline")
        append_jsonl_record(paths["attempts"], record, "assessment-attempts.jsonl")
    return {
        "result": "recorded",
        "attempt_id": attempt_id,
        "score": {"awarded": marks_awarded, "available": marks_available},
    }


def command_attempts(args: argparse.Namespace) -> dict[str, Any]:
    workspace = resolve_workspace(args.workspace)
    paths = paths_for(workspace)
    protocol_filter = clean_text(args.protocol_id, "protocol_id")
    with locked(paths):
        attempts = read_jsonl_records(
            paths["attempts"], "assessment-attempts.jsonl", missing_ok=True
        )
    if protocol_filter is not None:
        attempts = [
            item for item in attempts if item.get("protocol_id") == protocol_filter
        ]
    by_kind = {kind: 0 for kind in sorted(ATTEMPT_KINDS)}
    for item in attempts:
        kind = item.get("kind")
        if kind in by_kind:
            by_kind[kind] += 1
    comparisons: list[dict[str, Any]] = []
    protocol_ids = sorted(
        {
            str(item.get("protocol_id"))
            for item in attempts
            if item.get("protocol_id")
        }
    )
    for protocol_id in protocol_ids:
        baselines = sorted(
            [
                item
                for item in attempts
                if item.get("protocol_id") == protocol_id
                and item.get("kind") == "baseline"
            ],
            key=lambda item: item.get("attempted_at", ""),
        )
        posttests = sorted(
            [
                item
                for item in attempts
                if item.get("protocol_id") == protocol_id
                and item.get("kind") == "posttest"
            ],
            key=lambda item: item.get("attempted_at", ""),
        )
        if baselines and posttests:
            baseline = baselines[0]
            posttest = posttests[-1]
            comparisons.append(
                {
                    "protocol_id": protocol_id,
                    "baseline_attempt_id": baseline.get("attempt_id"),
                    "posttest_attempt_id": posttest.get("attempt_id"),
                    "percentage_point_change": round(
                        100
                        * (
                            float(posttest.get("score_fraction", 0))
                            - float(baseline.get("score_fraction", 0))
                        ),
                        2,
                    ),
                    "claim_status": "observed_change_not_causal_effect",
                }
            )
    return {
        "filters": {"protocol_id": protocol_filter},
        "attempt_count": len(attempts),
        "by_kind": by_kind,
        "comparisons": comparisons,
        "attempts": attempts,
    }


def command_observe(args: argparse.Namespace) -> dict[str, Any]:
    workspace = resolve_workspace(args.workspace)
    paths = paths_for(workspace)
    observation = read_payload(args.from_json)
    allowed = {
        "chapter_id",
        "objective_id",
        "criterion",
        "judgment",
        "evidence_summary",
        "error_type",
        "severity",
        "uncertainty",
        "next_action",
        "retrieval_id",
        "independent",
        "source_exposure",
    }
    unknown = set(observation) - allowed
    if unknown:
        raise TutorStateError("unknown observation fields: " + ", ".join(sorted(unknown)))
    for field in ("objective_id", "criterion", "evidence_summary"):
        observation[field] = clean_text(observation.get(field), field, required=True)
    observation["chapter_id"] = clean_text(observation.get("chapter_id"), "chapter_id")
    observation["next_action"] = clean_text(observation.get("next_action"), "next_action")
    retrieval_id = clean_text(observation.get("retrieval_id"), "retrieval_id")
    if retrieval_id is not None:
        observation["retrieval_id"] = retrieval_id
    independent = clean_bool(observation.get("independent"), "independent")
    if independent is not None:
        observation["independent"] = independent
    source_exposure = observation.get("source_exposure")
    if source_exposure is not None and source_exposure not in SOURCE_EXPOSURES:
        raise TutorStateError(f"unsupported source_exposure: {source_exposure!r}")
    judgment = observation.get("judgment")
    if judgment not in JUDGMENTS:
        raise TutorStateError(f"unsupported judgment: {judgment!r}")
    error_type = observation.get("error_type", "none")
    if error_type not in ERROR_TYPES:
        raise TutorStateError(f"unsupported error_type: {error_type!r}")
    uncertainty = observation.get("uncertainty", "medium")
    if uncertainty not in UNCERTAINTIES:
        raise TutorStateError(f"unsupported uncertainty: {uncertainty!r}")
    observation["error_type"] = error_type
    severity = observation.get("severity", "uncertain")
    if severity not in SEVERITIES:
        raise TutorStateError(f"unsupported severity: {severity!r}")
    observation["severity"] = severity
    observation["uncertainty"] = uncertainty
    observation["observed_at"] = now_utc()
    if judgment == "retained_later":
        if retrieval_id is None:
            raise TutorStateError("retained_later requires a scheduled retrieval_id")
        if independent is not True:
            raise TutorStateError("retained_later requires an independent attempt")
        if source_exposure != "unseen_before_attempt":
            raise TutorStateError(
                "retained_later requires an unseen task before the attempt"
            )

    with locked(paths):
        state = read_json(paths["state"])
        retrieval_plan = None
        retrieval_record = None
        if retrieval_id is not None:
            retrieval_plan = read_retrieval_plan(paths["retrievals"], missing_ok=True)
            matches = [
                item
                for item in retrieval_plan.get("retrievals", [])
                if item.get("retrieval_id") == retrieval_id
            ]
            if not matches:
                raise TutorStateError("retrieval_id is not scheduled")
            retrieval_record = matches[0]
            if retrieval_record.get("status") != "pending":
                raise TutorStateError("retrieval_id is not pending")
            if judgment == "retained_later":
                due_time = parse_timestamp(
                    retrieval_record.get("due_at"), "due_at"
                )[0]
                observed_time = parse_timestamp(
                    observation["observed_at"], "observed_at"
                )[0]
                if observed_time < due_time:
                    raise TutorStateError(
                        "retained_later cannot be recorded before the retrieval is due"
                    )
        append_jsonl_record(paths["observations"], observation, "observations.jsonl")
        if retrieval_record is not None and retrieval_plan is not None:
            retrieval_record["status"] = "completed"
            retrieval_record["completed_at"] = observation["observed_at"]
            retrieval_record["result_judgment"] = judgment
            retrieval_plan["updated_at"] = now_utc()
            atomic_json(paths["retrievals"], retrieval_plan)
        state["last_observation"] = observation
        if observation.get("next_action"):
            state["current"]["next_action"] = observation["next_action"]
        save_state(paths, state)
    return {"result": "recorded", "judgment": judgment}


def change_status(workspace_raw: str, status: str) -> dict[str, Any]:
    workspace = resolve_workspace(workspace_raw)
    paths = paths_for(workspace)
    with locked(paths):
        state = read_json(paths["state"])
        current = state["current"]
        if status == "paused":
            if current.get("status") == "complete":
                raise TutorStateError("a complete session cannot be paused")
            current["status"] = "paused"
            state["paused_at"] = now_utc()
        elif status == "active":
            if current.get("status") == "complete":
                raise TutorStateError("a complete session cannot be resumed")
            current["status"] = "active"
            state["resumed_at"] = now_utc()
        save_state(paths, state)
    return {"result": status}


def source_changes(index: dict[str, Any]) -> list[dict[str, str]]:
    changes: list[dict[str, str]] = []
    for source in index.get("sources", []):
        path = Path(source.get("path", ""))
        if not path.is_file():
            changes.append({"source_id": source.get("source_id", "?"), "state": "missing"})
            continue
        if file_sha256(path) != source.get("sha256"):
            changes.append({"source_id": source.get("source_id", "?"), "state": "changed"})
    return changes


def command_show(args: argparse.Namespace) -> dict[str, Any]:
    workspace = resolve_workspace(args.workspace)
    paths = paths_for(workspace)
    with locked(paths):
        state = read_json(paths["state"])
        sources = read_json(paths["sources"])
        retrieval_plan = read_retrieval_plan(paths["retrievals"], missing_ok=True)
        attempts = read_jsonl_records(
            paths["attempts"], "assessment-attempts.jsonl", missing_ok=True
        )
    now = datetime.now(timezone.utc)
    due_retrieval_count = sum(
        1
        for item in retrieval_plan.get("retrievals", [])
        if item.get("status") == "pending"
        and parse_timestamp(item.get("due_at"), "due_at")[0] <= now
    )
    return {
        "course": state["course"],
        "current": state["current"],
        "last_observation": state.get("last_observation"),
        "source_count": len(sources.get("sources", [])),
        "source_changes": source_changes(sources),
        "due_retrieval_count": due_retrieval_count,
        "assessment_attempt_count": len(attempts),
        "updated_at": state.get("updated_at"),
    }


def read_observations(path: Path) -> list[dict[str, Any]]:
    return read_jsonl_records(path, "observation")


def command_progress(args: argparse.Namespace) -> dict[str, Any]:
    """Summarize cumulative evidence without converting it into mastery scores."""
    workspace = resolve_workspace(args.workspace)
    paths = paths_for(workspace)
    chapter_filter = clean_text(args.chapter_id, "chapter_id")
    objective_filter = clean_text(args.objective_id, "objective_id")
    with locked(paths):
        state = read_json(paths["state"])
        observations = read_observations(paths["observations"])

    if chapter_filter is not None:
        observations = [
            item for item in observations if item.get("chapter_id") == chapter_filter
        ]
    if objective_filter is not None:
        observations = [
            item for item in observations if item.get("objective_id") == objective_filter
        ]

    judgment_counts = {judgment: 0 for judgment in sorted(JUDGMENTS)}
    latest_by_objective: dict[str, dict[str, Any]] = {}
    chapter_counts: dict[str, int] = {}
    for item in observations:
        judgment = item.get("judgment")
        if judgment in judgment_counts:
            judgment_counts[judgment] += 1
        objective_id = str(item.get("objective_id", "?"))
        latest_by_objective[objective_id] = {
            "chapter_id": item.get("chapter_id"),
            "judgment": judgment,
            "severity": item.get("severity", "uncertain"),
            "uncertainty": item.get("uncertainty", "medium"),
            "observed_at": item.get("observed_at"),
            "next_action": item.get("next_action"),
        }
        chapter_id = item.get("chapter_id") or "unassigned"
        chapter_counts[chapter_id] = chapter_counts.get(chapter_id, 0) + 1

    return {
        "course": state["course"],
        "current": {
            "chapter_id": state["current"].get("chapter_id"),
            "chapter_stage": state["current"].get("chapter_stage"),
            "objective_id": state["current"].get("objective_id"),
        },
        "filters": {
            "chapter_id": chapter_filter,
            "objective_id": objective_filter,
        },
        "observation_count": len(observations),
        "judgment_counts": judgment_counts,
        "chapter_counts": dict(sorted(chapter_counts.items())),
        "latest_by_objective": dict(sorted(latest_by_objective.items())),
    }


def command_verify(args: argparse.Namespace) -> dict[str, Any]:
    workspace = resolve_workspace(args.workspace)
    paths = paths_for(workspace)
    issues: list[str] = []
    retrieval_count = 0
    attempt_count = 0
    with locked(paths):
        state = read_json(paths["state"])
        sources = read_json(paths["sources"])
        try:
            lines = paths["observations"].read_text(encoding="utf-8").splitlines()
        except FileNotFoundError:
            issues.append("observations.jsonl is missing")
            lines = []
        for number, line in enumerate(lines, start=1):
            try:
                value = json.loads(line)
                if not isinstance(value, dict):
                    raise ValueError("record is not an object")
            except (json.JSONDecodeError, ValueError) as exc:
                issues.append(f"invalid observation at line {number}: {exc}")
        try:
            retrieval_plan = read_retrieval_plan(
                paths["retrievals"], missing_ok=True
            )
            retrievals = retrieval_plan.get("retrievals", [])
            retrieval_count = len(retrievals)
            retrieval_ids = [item.get("retrieval_id") for item in retrievals]
            if len(retrieval_ids) != len(set(retrieval_ids)):
                issues.append("retrieval plan contains duplicate retrieval_id values")
            for number, item in enumerate(retrievals, start=1):
                if item.get("status") not in {"pending", "completed"}:
                    issues.append(f"retrieval {number} contains an invalid status")
                try:
                    parse_timestamp(item.get("due_at"), "due_at")
                except TutorStateError as exc:
                    issues.append(f"retrieval {number} is invalid: {exc}")
        except TutorStateError as exc:
            issues.append(str(exc))
        try:
            attempts = read_jsonl_records(
                paths["attempts"], "assessment-attempts.jsonl", missing_ok=True
            )
            attempt_count = len(attempts)
            attempt_ids = [item.get("attempt_id") for item in attempts]
            if len(attempt_ids) != len(set(attempt_ids)):
                issues.append("assessment attempts contain duplicate attempt_id values")
        except TutorStateError as exc:
            issues.append(str(exc))
        if state.get("current", {}).get("status") not in SESSION_STATUSES:
            issues.append("state contains an invalid session status")
    for change in source_changes(sources):
        issues.append(f"source {change['source_id']} is {change['state']}")
    return {
        "result": "ok" if not issues else "issues_found",
        "issues": issues,
        "observation_count": len(lines),
        "retrieval_count": retrieval_count,
        "assessment_attempt_count": attempt_count,
        "source_count": len(sources.get("sources", [])),
    }


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(
        description="Persist minimal local state for adaptive-stem-tutor."
    )
    commands = result.add_subparsers(dest="command", required=True)

    init = commands.add_parser("init", help="initialize a new course workspace")
    init.add_argument("--workspace", required=True)
    init.add_argument("--course-code", required=True)
    init.add_argument("--course-title", required=True)
    init.add_argument("--learner-language", default="en")
    init.set_defaults(handler=command_init)

    register = commands.add_parser("register-source", help="register an inspected source")
    register.add_argument("--workspace", required=True)
    register.add_argument("--source-id", required=True)
    register.add_argument("--path", required=True)
    register.add_argument("--label", required=True)
    register.add_argument("--role", choices=sorted(SOURCE_ROLES), required=True)
    register.add_argument("--review-state", choices=sorted(REVIEW_STATES), required=True)
    register.add_argument("--scope")
    register.add_argument("--edition")
    register.add_argument("--authority-note")
    register.add_argument("--replace", action="store_true")
    register.set_defaults(handler=command_register_source)

    update = commands.add_parser("update", help="atomically update the checkpoint")
    update.add_argument("--workspace", required=True)
    update.add_argument("--from-json", required=True)
    update.set_defaults(handler=command_update)

    observe = commands.add_parser("observe", help="append an answer observation")
    observe.add_argument("--workspace", required=True)
    observe.add_argument("--from-json", required=True)
    observe.set_defaults(handler=command_observe)

    schedule_retrieval = commands.add_parser(
        "schedule-retrieval", help="schedule a delayed changed-context retrieval"
    )
    schedule_retrieval.add_argument("--workspace", required=True)
    schedule_retrieval.add_argument("--from-json", required=True)
    schedule_retrieval.set_defaults(handler=command_schedule_retrieval)

    due_retrievals = commands.add_parser(
        "due-retrievals", help="list due and upcoming retrieval checks"
    )
    due_retrievals.add_argument("--workspace", required=True)
    due_retrievals.add_argument("--as-of")
    due_retrievals.set_defaults(handler=command_due_retrievals)

    record_attempt = commands.add_parser(
        "record-attempt", help="record a minimal blind or timed assessment result"
    )
    record_attempt.add_argument("--workspace", required=True)
    record_attempt.add_argument("--from-json", required=True)
    record_attempt.set_defaults(handler=command_record_attempt)

    attempts = commands.add_parser(
        "attempts", help="summarize recorded assessment attempts without causal claims"
    )
    attempts.add_argument("--workspace", required=True)
    attempts.add_argument("--protocol-id")
    attempts.set_defaults(handler=command_attempts)

    pause = commands.add_parser("pause", help="pause without moving the checkpoint")
    pause.add_argument("--workspace", required=True)
    pause.set_defaults(handler=lambda args: change_status(args.workspace, "paused"))

    resume = commands.add_parser("resume", help="resume the same checkpoint")
    resume.add_argument("--workspace", required=True)
    resume.set_defaults(handler=lambda args: change_status(args.workspace, "active"))

    show = commands.add_parser("show", help="show the current private checkpoint")
    show.add_argument("--workspace", required=True)
    show.set_defaults(handler=command_show)

    progress = commands.add_parser(
        "progress", help="summarize cumulative criterion-linked observations"
    )
    progress.add_argument("--workspace", required=True)
    progress.add_argument("--chapter-id")
    progress.add_argument("--objective-id")
    progress.set_defaults(handler=command_progress)

    verify = commands.add_parser("verify", help="verify state and registered sources")
    verify.add_argument("--workspace", required=True)
    verify.set_defaults(handler=command_verify)

    return result


def main() -> int:
    args = parser().parse_args()
    try:
        result = args.handler(args)
    except (TutorStateError, OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"result": "error", "message": str(exc)}, ensure_ascii=False))
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    if args.command == "verify" and result.get("issues"):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
