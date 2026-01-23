from __future__ import annotations

from datetime import date

import streamlit as st
from streamlit_sortables import sort_items

from ui.constants import Icons, SessionKeys
from ui.i18n import Keys, t
from utils.logging_config import get_logger
from utils.task_manager import (
    ALL_PRIORITIES,
    ALL_STATUSES,
    PRIORITY_HIGH,
    PRIORITY_LOW,
    PRIORITY_MEDIUM,
    STATUS_DONE,
    STATUS_IN_PROGRESS,
    STATUS_TODO,
    Task,
    add_task,
    delete_task,
    get_tasks_by_status,
    reorder_tasks_from_kanban,
    save_tasks,
    update_task,
)

logger = get_logger("tab_task_planner")

PRIORITY_ICONS = {
    PRIORITY_HIGH: "🔴",
    PRIORITY_MEDIUM: "🟡",
    PRIORITY_LOW: "🟢",
}

PRIORITY_LABELS = {
    PRIORITY_HIGH: Keys.TASK_PRIORITY_HIGH,
    PRIORITY_MEDIUM: Keys.TASK_PRIORITY_MEDIUM,
    PRIORITY_LOW: Keys.TASK_PRIORITY_LOW,
}

STATUS_LABELS = {
    STATUS_TODO: Keys.TASK_STATUS_TODO,
    STATUS_IN_PROGRESS: Keys.TASK_STATUS_IN_PROGRESS,
    STATUS_DONE: Keys.TASK_STATUS_DONE,
}

STATUS_ICONS = {
    STATUS_TODO: "📋",
    STATUS_IN_PROGRESS: "🔄",
    STATUS_DONE: "✅",
}


def _format_priority(i: int) -> str:
    return f"{PRIORITY_ICONS[ALL_PRIORITIES[i]]} {t(PRIORITY_LABELS[ALL_PRIORITIES[i]])}"


def _format_status(i: int) -> str:
    return f"{STATUS_ICONS[ALL_STATUSES[i]]} {t(STATUS_LABELS[ALL_STATUSES[i]])}"


@st.fragment
def render(_context: dict | None = None) -> None:
    try:
        _render_content()
    except Exception as e:
        logger.exception("Error in Task Planner")
        st.error(f"{Icons.ERROR} {t(Keys.ERR_TASK_PLANNER).format(error=str(e))}")


def _migrate_tasks(tasks: list[Task]) -> list[Task]:
    migrated = False
    for task in tasks:
        if not hasattr(task, "description"):
            task.description = ""
            migrated = True
    if migrated:
        save_tasks(tasks)
    return tasks


def _render_content() -> None:
    st.title(t(Keys.TITLE_TASK_PLANNER))

    tasks: list[Task] = st.session_state.get(SessionKeys.TASKS, [])
    tasks = _migrate_tasks(tasks)

    _render_add_task_form(tasks)
    st.divider()
    _render_task_list(tasks)
    st.divider()
    _render_kanban_board(tasks)


def _render_add_task_form(tasks: list[Task]) -> None:
    with st.expander(t(Keys.TASK_ADD_NEW), expanded=False):
        col1, col2, col3 = st.columns([3, 1, 1])

        with col1:
            title = st.text_input(
                t(Keys.TASK_TITLE),
                placeholder=t(Keys.TASK_TITLE_PLACEHOLDER),
                key="new_task_title",
            )

        with col2:
            due_date = st.date_input(
                t(Keys.TASK_DUE_DATE),
                value=None,
                key="new_task_due_date",
            )

        with col3:
            priority_options = [t(PRIORITY_LABELS[p]) for p in ALL_PRIORITIES]
            priority_idx = st.selectbox(
                t(Keys.TASK_PRIORITY),
                options=range(len(priority_options)),
                format_func=lambda i: f"{PRIORITY_ICONS[ALL_PRIORITIES[i]]} {priority_options[i]}",
                key="new_task_priority",
            )

        description = st.text_area(
            t(Keys.TASK_DESCRIPTION),
            placeholder=t(Keys.TASK_DESCRIPTION_PLACEHOLDER),
            help=t(Keys.TASK_DESCRIPTION_HELP),
            key="new_task_description",
            height=100,
        )

        if st.button(t(Keys.TASK_ADD_BTN), type="primary"):
            if not title or not title.strip():
                st.error(t(Keys.ERR_TASK_TITLE_REQUIRED))
            else:
                new_task = Task.create(
                    title=title.strip(),
                    priority=ALL_PRIORITIES[priority_idx],
                    due_date=due_date if due_date else None,
                    description=description.strip() if description else "",
                )
                tasks = add_task(tasks, new_task)
                st.session_state[SessionKeys.TASKS] = tasks
                st.rerun()


def _render_task_list(tasks: list[Task]) -> None:
    st.subheader(t(Keys.TASK_LIST))

    col1, col2 = st.columns(2)
    with col1:
        status_options = [t(Keys.TASK_FILTER_ALL)] + [t(STATUS_LABELS[s]) for s in ALL_STATUSES]
        status_filter = st.selectbox(
            t(Keys.TASK_FILTER_STATUS),
            options=status_options,
            key="task_list_status_filter",
        )
    with col2:
        priority_options = [t(Keys.TASK_FILTER_ALL)] + [
            f"{PRIORITY_ICONS[p]} {t(PRIORITY_LABELS[p])}" for p in ALL_PRIORITIES
        ]
        priority_filter = st.selectbox(
            t(Keys.TASK_FILTER_PRIORITY),
            options=priority_options,
            key="task_list_priority_filter",
        )

    filtered_tasks = _filter_tasks(tasks, status_filter, priority_filter)

    if not filtered_tasks:
        st.info(t(Keys.TASK_NO_TASKS))
        return

    for task in filtered_tasks:
        _render_task_card(task, tasks)


def _filter_tasks(tasks: list[Task], status_filter: str, priority_filter: str) -> list[Task]:
    result = tasks

    if status_filter != t(Keys.TASK_FILTER_ALL):
        for status, label_key in STATUS_LABELS.items():
            if status_filter == t(label_key):
                result = [task for task in result if task.status == status]
                break

    if priority_filter != t(Keys.TASK_FILTER_ALL):
        for priority in ALL_PRIORITIES:
            label = f"{PRIORITY_ICONS[priority]} {t(PRIORITY_LABELS[priority])}"
            if priority_filter == label:
                result = [task for task in result if task.priority == priority]
                break

    return result


def _render_task_card(task: Task, tasks: list[Task]) -> None:
    due = task.get_due_date()
    due_indicator = ""
    if due:
        today = date.today()
        if due < today:
            due_indicator = "🔴"
        elif due == today:
            due_indicator = "🟡"
        else:
            due_indicator = "🟢"

    header = f"{PRIORITY_ICONS.get(task.priority, '')} **{task.title}**"
    if due:
        header += f" {due_indicator} {due.strftime('%Y-%m-%d')}"

    with st.expander(header, expanded=False):
        if task.description:
            st.markdown(task.description)
            st.divider()

        _render_task_edit_form(task, tasks)


def _get_index_safe(items: list, value: str, default: int) -> int:
    return items.index(value) if value in items else default


def _handle_save_task(
    task: Task,
    tasks: list[Task],
    new_title: str,
    new_description: str,
    new_priority_idx: int,
    new_due: date | None,
    current_due: date | None,
    new_status_idx: int,
) -> None:
    clear_due = new_due is None and current_due is not None
    tasks = update_task(
        tasks,
        task.id,
        title=new_title.strip() if new_title else task.title,
        description=new_description.strip() if new_description is not None else task.description,
        priority=ALL_PRIORITIES[new_priority_idx],
        due_date=new_due if new_due else None,
        clear_due_date=clear_due,
    )
    new_status = ALL_STATUSES[new_status_idx]
    if new_status != task.status:
        from utils.task_manager import update_task_status
        tasks = update_task_status(tasks, task.id, new_status)
    st.session_state[SessionKeys.TASKS] = tasks
    st.rerun()


def _render_task_edit_form(task: Task, tasks: list[Task]) -> None:
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        new_title = st.text_input(t(Keys.TASK_TITLE), value=task.title, key=f"edit_title_{task.id}")

    current_due = task.get_due_date()
    with col2:
        new_due = st.date_input(t(Keys.TASK_DUE_DATE), value=current_due, key=f"edit_due_{task.id}")

    with col3:
        new_priority_idx = st.selectbox(
            t(Keys.TASK_PRIORITY),
            options=range(len(ALL_PRIORITIES)),
            index=_get_index_safe(ALL_PRIORITIES, task.priority, 1),
            format_func=_format_priority,
            key=f"edit_priority_{task.id}",
        )

    new_description = st.text_area(
        t(Keys.TASK_DESCRIPTION), value=task.description, help=t(Keys.TASK_DESCRIPTION_HELP),
        key=f"edit_desc_{task.id}", height=150,
    )

    col_status, col_save, col_delete = st.columns([2, 1, 1])

    with col_status:
        new_status_idx = st.selectbox(
            "Status",
            options=range(len(ALL_STATUSES)),
            index=_get_index_safe(ALL_STATUSES, task.status, 0),
            format_func=_format_status,
            key=f"edit_status_{task.id}",
        )

    with col_save:
        if st.button(t(Keys.TASK_SAVE_BTN), key=f"save_{task.id}", type="primary"):
            _handle_save_task(
                task, tasks, new_title, new_description, new_priority_idx,
                new_due, current_due, new_status_idx,
            )

    with col_delete:
        if st.button(f"🗑️ {t(Keys.TASK_DELETE_BTN)}", key=f"delete_{task.id}"):
            tasks = delete_task(tasks, task.id)
            st.session_state[SessionKeys.TASKS] = tasks
            st.rerun()


def _render_kanban_board(tasks: list[Task]) -> None:
    st.subheader(t(Keys.TASK_KANBAN))

    todo_tasks = get_tasks_by_status(tasks, STATUS_TODO)
    in_progress_tasks = get_tasks_by_status(tasks, STATUS_IN_PROGRESS)
    done_tasks = get_tasks_by_status(tasks, STATUS_DONE)

    card_to_id_map: dict[str, str] = {}

    def task_to_card(task: Task) -> str:
        priority_icon = PRIORITY_ICONS.get(task.priority, "")
        due = task.get_due_date()
        due_str = f" ({due.strftime('%m-%d')})" if due else ""
        card_label = f"{priority_icon} {task.title}{due_str}"
        card_to_id_map[card_label] = task.id
        return card_label

    todo_items = [task_to_card(tk) for tk in todo_tasks]
    in_progress_items = [task_to_card(tk) for tk in in_progress_tasks]
    done_items = [task_to_card(tk) for tk in done_tasks]

    kanban_items = [
        {
            "header": f"{STATUS_ICONS[STATUS_TODO]} {t(Keys.TASK_STATUS_TODO)}",
            "items": todo_items,
        },
        {
            "header": f"{STATUS_ICONS[STATUS_IN_PROGRESS]} {t(Keys.TASK_STATUS_IN_PROGRESS)}",
            "items": in_progress_items,
        },
        {
            "header": f"{STATUS_ICONS[STATUS_DONE]} {t(Keys.TASK_STATUS_DONE)}",
            "items": done_items,
        },
    ]

    sorted_items = sort_items(kanban_items, multi_containers=True, direction="horizontal")

    if sorted_items != kanban_items:
        new_todo_ids = [card_to_id_map.get(card, "") for card in sorted_items[0]["items"]]
        new_in_progress_ids = [card_to_id_map.get(card, "") for card in sorted_items[1]["items"]]
        new_done_ids = [card_to_id_map.get(card, "") for card in sorted_items[2]["items"]]

        new_todo_ids = [x for x in new_todo_ids if x]
        new_in_progress_ids = [x for x in new_in_progress_ids if x]
        new_done_ids = [x for x in new_done_ids if x]

        tasks = reorder_tasks_from_kanban(tasks, new_todo_ids, new_in_progress_ids, new_done_ids)
        st.session_state[SessionKeys.TASKS] = tasks
        st.rerun()
