from __future__ import annotations

import json
import os
import uuid
from dataclasses import asdict, dataclass
from datetime import date, datetime

TASKS_FILE = "./tasks.json"

STATUS_TODO = "todo"
STATUS_IN_PROGRESS = "in_progress"
STATUS_DONE = "done"

PRIORITY_HIGH = "high"
PRIORITY_MEDIUM = "medium"
PRIORITY_LOW = "low"

ALL_STATUSES = [STATUS_TODO, STATUS_IN_PROGRESS, STATUS_DONE]
ALL_PRIORITIES = [PRIORITY_HIGH, PRIORITY_MEDIUM, PRIORITY_LOW]


@dataclass
class Task:
    id: str
    title: str
    priority: str
    status: str
    created_at: str
    due_date: str | None = None
    description: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> Task:
        return cls(
            id=data["id"],
            title=data["title"],
            priority=data["priority"],
            status=data["status"],
            created_at=data["created_at"],
            due_date=data.get("due_date"),
            description=data.get("description", ""),
        )

    @classmethod
    def create(
            cls,
            title: str,
            priority: str = PRIORITY_MEDIUM,
            due_date: date | None = None,
            description: str = "",
    ) -> Task:
        return cls(
            id=str(uuid.uuid4()),
            title=title,
            priority=priority,
            status=STATUS_TODO,
            created_at=datetime.now().isoformat(),
            due_date=due_date.isoformat() if due_date else None,
            description=description,
        )

    def get_due_date(self) -> date | None:
        if self.due_date:
            return date.fromisoformat(self.due_date)
        return None

    def get_created_at(self) -> datetime:
        return datetime.fromisoformat(self.created_at)


def load_tasks(file_path: str | None = None) -> list[Task]:
    if file_path is None:
        file_path = TASKS_FILE

    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return [Task.from_dict(t) for t in data]
        except (KeyError, ValueError):
            pass
    return []


def save_tasks(tasks: list[Task], file_path: str | None = None) -> None:
    if file_path is None:
        file_path = TASKS_FILE

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump([t.to_dict() for t in tasks], f, indent=2)


def add_task(tasks: list[Task], task: Task) -> list[Task]:
    tasks.append(task)
    save_tasks(tasks)
    return tasks


def delete_task(tasks: list[Task], task_id: str) -> list[Task]:
    tasks = [t for t in tasks if t.id != task_id]
    save_tasks(tasks)
    return tasks


def update_task_status(tasks: list[Task], task_id: str, new_status: str) -> list[Task]:
    for task in tasks:
        if task.id == task_id:
            task.status = new_status
            break
    save_tasks(tasks)
    return tasks


def _apply_task_updates(
    task: Task,
    title: str | None,
    description: str | None,
    priority: str | None,
    due_date: date | None,
    clear_due_date: bool,
) -> None:
    if title is not None:
        task.title = title
    if description is not None:
        task.description = description
    if priority is not None:
        task.priority = priority
    if clear_due_date:
        task.due_date = None
    elif due_date is not None:
        task.due_date = due_date.isoformat()


def update_task(
    tasks: list[Task],
    task_id: str,
    title: str | None = None,
    description: str | None = None,
    priority: str | None = None,
    due_date: date | None = None,
    clear_due_date: bool = False,
) -> list[Task]:
    for task in tasks:
        if task.id == task_id:
            _apply_task_updates(task, title, description, priority, due_date, clear_due_date)
            break
    save_tasks(tasks)
    return tasks


def get_tasks_by_status(tasks: list[Task], status: str) -> list[Task]:
    return [t for t in tasks if t.status == status]


def reorder_tasks_from_kanban(
        tasks: list[Task],
        todo_ids: list[str],
        in_progress_ids: list[str],
        done_ids: list[str],
) -> list[Task]:
    id_to_status = {}
    for tid in todo_ids:
        id_to_status[tid] = STATUS_TODO
    for tid in in_progress_ids:
        id_to_status[tid] = STATUS_IN_PROGRESS
    for tid in done_ids:
        id_to_status[tid] = STATUS_DONE

    for task in tasks:
        if task.id in id_to_status:
            task.status = id_to_status[task.id]

    save_tasks(tasks)
    return tasks
