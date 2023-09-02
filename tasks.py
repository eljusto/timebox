import os
import re
import things
from dataclasses import dataclass

@dataclass
class Task:
    minutes: int = 0
    title: str = ''
    url: str = ''

def _get_today_tasks():
    try:
        DB = os.path.expanduser( "~/Library/Group Containers/JLMPQHK86H.com.culturedcode.ThingsMac/ThingsData-SOCLQ/Things Database.thingsdatabase/main.sqlite")
        mytasks = []
        tasks = things.today(filepath=DB)
        for task in tasks:
            try: 
                duration_tag = next((tag for tag in task.get('tags', []) if re.match(r"[0-9]+min", tag)), '')
                mytasks.append((duration_tag, task['title'], things.link(task['uuid'])))
            except Exception as e:
                mytasks.append(('', task['title'], things.link(task['uuid'])))
        return mytasks

    except Exception as e:
        print(e)
        return []

def get_things_today_tasks():
    list_of_tasks = _get_today_tasks()
    processed_tasks = {}

    for task_tuple in list_of_tasks:
        processed_tasks[task_tuple[1]] = Task(
                minutes = int(task_tuple[0][:-3]) if task_tuple[0][-3:] == "min" else 0,
                title = task_tuple[1],
                url = task_tuple[2]
           )

    return processed_tasks
