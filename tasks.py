import os
import re
import things
from dataclasses import dataclass

@dataclass
class Task:
    minutes: int = 0
    title: str = ''
    url: str = ''

def get_things_today_tasks_raw():
    DB = os.path.expanduser(
        "~/Library/Group Containers/JLMPQHK86H.com.culturedcode.ThingsMac/Things Database.thingsdatabase/main.sqlite"
    )
    return things.today(filepath=DB)

def get_things_today_tasks():
    DB = os.path.expanduser(
        "~/Library/Group Containers/JLMPQHK86H.com.culturedcode.ThingsMac/Things Database.thingsdatabase/main.sqlite"
    )
    mytasks = []
    tasks = things.today(filepath=DB)
    for task in tasks:
        duration_tag = next((tag for tag in task.get('tags', []) if re.match(r"[0-9]+min", tag)), '')
        mytasks.append((duration_tag, task['title'], things.link(task['uuid'])))
    return mytasks

def process_tasks(list_of_tasks):
    processed_tasks = {}

    for task_tuple in list_of_tasks:
        if task_tuple[0][-3:] == "min":
            processed_tasks[task_tuple[1]] = Task(
                minutes = int(task_tuple[0][:-3]),
                title = task_tuple[1],
                url = task_tuple[2]
            )
        else:
            processed_tasks[task_tuple[1]] = Task(
                minutes = 25,
                title = task_tuple[1],
                url = task_tuple[2],
            )

    return processed_tasks
