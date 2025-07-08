import csv
import re
import sqlite3
from enum import Enum, IntEnum
from pathlib import Path
from random import choice
from string import ascii_lowercase


class TaskStatus(IntEnum):
    CREATED = 0
    ONGOING = 1
    COMPLETED = 2

    @classmethod
    def formatted_options(cls):
        return [x.name.title() for x in cls]


class TaskierDBOption(Enum):
    DB_CSV = "tasks.csv"
    DB_SQLITE = "tasks.sqlite"


class TaskierError(Exception):
    pass


class Task:
    con: sqlite3.Connection = sqlite3.connect(TaskierDBOption.DB_SQLITE.value)

    def __init__(
        self, task_id: str, title: str, desc: str, urgency: int, status=TaskStatus.CREATED, completion_note=""
    ):
        self.task_id = task_id
        self.title = title
        self.desc = desc
        self.urgency = urgency
        self.status = TaskStatus(status)
        self.completion_note = completion_note

    @classmethod
    def task_from_form_entry(cls, title: str, desc: str, urgency: int):
        task_id = cls.random_string()
        task = cls(task_id, title, desc, urgency)

        return task

    @staticmethod
    def random_string(length=8):
        return "".join(choice(ascii_lowercase) for _ in range(length))

    @classmethod
    def create_sqlite_database(cls):
        with sqlite3.connect(TaskierDBOption.DB_SQLITE.value) as con:
            cls.con = con
            cursor = con.cursor()
            cursor.execute(
                "CREATE TABLE task (task_id text, title text, desc text, urgency integer, status integer, completion_note text);"
            )
            cls.con.commit()

    def save_to_db(self):
        if app_db == TaskierDBOption.DB_CSV.value:
            with open(app_db, "a", newline="") as file:
                csv_writer = csv.writer(file)
                db_record = self._formatted_db_record()
                csv_writer.writerow(db_record)
        else:
            with self.con as con:
                cursor = con.cursor()
                sql_stmt = "INSERT INTO task VALUES (?, ?, ?, ?, ?, ?);"
                cursor.execute(sql_stmt, self._formatted_db_record())
                con.commit()

    def _formatted_db_record(self):
        db_record = (self.task_id, self.title, self.desc, self.urgency, self.status, self.completion_note)

        return db_record

    @classmethod
    def load_tasks(cls, statuses: list[TaskStatus] = None, urgencies: list[int] = None, content: str = ""):
        tasks = []

        if app_db == TaskierDBOption.DB_CSV.value:
            with open(app_db, newline="") as file:
                reader = csv.reader(file)

                for row in reader:
                    task_id, title, desc, urgency_str, status_str, note = row
                    urgency = int(urgency_str)
                    status = TaskStatus(int(status_str))

                    if statuses and (status not in statuses):
                        continue
                    if urgencies and (status not in urgencies):
                        continue

                    if content and all([note.find(content) < 0, desc.find(content) < 0, title.find(content) < 0]):
                        continue
                    task = cls(task_id, title, desc, urgency, status, note)
                    tasks.append(task)
        else:
            with cls.con as con:
                if statuses is None:
                    statuses = tuple(map(int, TaskStatus))
                else:
                    statuses = tuple(statuses) * 2
                if urgencies is None:
                    urgencies = tuple(range(1, 6))
                else:
                    urgencies = tuple(urgencies) * 2
                sql_stmt = f"SELECT * FROM task WHERE status in {statuses} and  urgency in {urgencies}"
                if content:
                    sql_stmt += f" and ((completion_note LIKE '%{content}%') or (desc LIKE '%{content}%') or (title LIKE '%{content}%'))"
                cursor = con.cursor()
                cursor.execute(sql_stmt)
                con.commit()
                task_tuple = cursor.fetchall()
                tasks = [Task(*x) for x in task_tuple]

        return tasks

    def update_in_db(self):
        if app_db == TaskierDBOption.DB_CSV.value:
            updated_record = f"{','.join(map(str, self._formatted_db_record()))}\n"

            with open(app_db, "r+") as file:
                saved_records = file.read()
                pattern = re.compile(rf"{self.task_id}.+?\n")
                if re.search(pattern, saved_records):
                    updated_records = re.sub(pattern, updated_record, saved_records)
                    file.seek(0)
                    file.truncate()
                    file.write(updated_records)
                else:
                    raise TaskierError("The task appears to be removed already!")
        else:
            with self.con as con:
                cursor = con.cursor()
                count_sql = f"SELECT COUNT(*) FROM task WHERE task_id = {self.task_id!r}"
                row_count = cursor.execute(count_sql).fetchone()[0]
                if row_count > 0:
                    sql_stmt = f"UPDATE task SET task_id = ?, title = ?, desc = ?, urgency = ?,status = ?, completion_note = ? WHERE task_id = {self.task_id!r}"
                    cursor.execute(sql_stmt, self._formatted_db_record())
                    con.commit()
                else:
                    raise TaskierError("The task appears to be removed already!")

    def delete_from_db(self):
        if app_db == TaskierDBOption.DB_CSV.value:
            with open(app_db, "r+") as file:
                lines = file.readlines()
                for line in lines:
                    if line.startswith(self.task_id):
                        lines.remove(line)
                        break
                file.seek(0)
                file.truncate()
                file.writelines(lines)
        else:
            with self.con as con:
                cursor = con.cursor()
                cursor.execute(f"DELETE FROM task WHERE task_id = {self.task_id!r}")
                con.commit()

    @classmethod
    def load_seed_data(cls):
        task0 = cls.task_from_form_entry("Laundry", "Wash Cloths", 3)
        task1 = cls.task_from_form_entry("Homework", "Math and Physics", 5)
        task2 = cls.task_from_form_entry("Museum", "Eqypt things", 4)

        with sqlite3.connect(TaskierDBOption.DB_SQLITE.value) as con:
            cursor = con.cursor()
            tasks = [task0, task1, task2]
            formatted_records = [task._formatted_db_record() for task in tasks]
            sql_stmt = "INSERT INTO task VALUES (?, ?, ?, ?, ?, ?);"
            cursor.executemany(sql_stmt, formatted_records)
            con.commit()

    def __str__(self) -> str:
        stars = "\u2605" * self.urgency

        return f"{self.title} ({self.desc}) {stars}"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__} ({self.task_id!r}, {self.title!r}. {self.desc!r}, {self.urgency}, {self.status}, {self.completion_note!r})"


app_db = TaskierDBOption.DB_CSV.value


def set_db_options(option):
    global app_db
    app_db = option
    db_path = Path(option)

    if not db_path.exists():
        if app_db == TaskierDBOption.DB_SQLITE.value:
            Task.create_sqlite_database()
            Task.load_seed_data()
    elif app_db == TaskierDBOption.DB_SQLITE.value:
        Task.con = sqlite3.connect(app_db, check_same_thread=False)
