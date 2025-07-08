from enum import Enum


class TaskierMenuOption(Enum):
    SHOW_TASKS = "Show Tasks"
    NEW_TASK = "NEW TASK"
    SHOW_TASK_DETAIL = "Show Task Detail"


class TaskierFilterKey(Enum):
    SORTING_KEY = "sorting_key"
    SORTING_ORDER = "sorting_order"
    SELECTED_STATUSES = "selected_statuses"
    SELECTED_URGENCIES = "selcted_urgencies"
    SELECTED_CONTENT = "selected_content"
