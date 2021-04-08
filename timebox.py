# %%
import rumps
import time
import subprocess
import csv
import sqlite3
import os

try:
    from urllib import urlretrieve
except ImportError:
    from urllib.request import urlretrieve

rumps.debug_mode(True)

SEC_TO_MIN = 60


def timez():
    return time.strftime("%a, %d %b %Y %H:%M:%S +0000", time.localtime())


# %%
def get_things_today_tasks(index=0, complete_task=False):
    conn = sqlite3.connect(
        os.path.expanduser(
            "~/Library/Group Containers/JLMPQHK86H.com.culturedcode.ThingsMac/Things Database.thingsdatabase/main.sqlite"
        )
    )
    sql = (
        "SELECT\n"
        "            TAG.title,\n"
        "            TASK.title,\n"
        '            "things:///show?id=" || TASK.uuid\n'
        "            FROM TMTask as TASK\n"
        "            LEFT JOIN TMTaskTag TAGS ON TAGS.tasks = TASK.uuid\n"
        "            LEFT JOIN TMTag TAG ON TAGS.tags = TAG.uuid\n"
        "            LEFT OUTER JOIN TMTask PROJECT ON TASK.project = PROJECT.uuid\n"
        "            LEFT OUTER JOIN TMArea AREA ON TASK.area = AREA.uuid\n"
        "            LEFT OUTER JOIN TMTask HEADING ON TASK.actionGroup = HEADING.uuid\n"
        "            WHERE TASK.trashed = 0 AND TASK.status = 0 AND TASK.type = 0 AND TAG.title IS NOT NULL\n"
        "            AND TASK.start = 1\n"
        "            AND TASK.startdate is NOT NULL\n"
        "            ORDER BY TASK.todayIndex\n"
        "            LIMIT 100"
    )
    tasks = []
    try:
        for row in conn.execute(sql):
            tasks.append(row)
    except Exception as e:
        print(e)
    conn.close()
    return tasks


def process_tasks(list_of_tasks):
    processed_tasks = {}

    for task_tuple in list_of_tasks:
        if task_tuple[0][-3:] == "min":
            processed_tasks[task_tuple[1]] = int(task_tuple[0][:-3])

    return processed_tasks


def hour_formatter(minutes):
    if minutes // 60 > 0:
        if spare_min := minutes % 60:
            return f"{minutes // 60}h, {spare_min}m of work today!"
        else:
            return f"{minutes // 60}h of work today!"
    else:
        return f"{minutes}m of work today!"


# %%
class TimerApp(object):
    def __init__(self, timer_interval=1):
        self.timer = rumps.Timer(self.on_tick, 1)
        self.timer.stop()  # timer running when initialized
        self.timer.count = 0
        self.app = rumps.App("Timebox", "🥊")
        self.interval = SEC_TO_MIN
        self.start_pause_button = rumps.MenuItem(
            title="Start Timer",
            callback=lambda _: self.start_timer(_, self.interval),
            key="s",
        )
        self.stop_button = rumps.MenuItem(title="Stop Timer", callback=None, key="x")
        self.buttons = {}
        self.buttons_callback = {}
        for i in [5, 10, 15, 20, 25]:
            title = str(i) + " Minutes"
            def callback(_, j=i):
                self.set_mins(_, j)
                self.timer.count = 0
                self.timer.end = j 
                self.timer.start()
            self.buttons["btn_" + str(i)] = rumps.MenuItem(
                title=title, callback=callback
            )
            self.buttons_callback[title] = callback

        self.sync_button = rumps.MenuItem(
            title="Sync", callback=lambda _: self.sync_data(), key="r"
        )

        self.things_tasks = get_things_today_tasks()

        self.things_processed_tasks = process_tasks(self.things_tasks)

        self.sum_of_tasks_scheduled = sum(self.things_processed_tasks.values())

        self.sum_menu_item = rumps.MenuItem(title="hours_spent", callback=None)
        
        def callback(time):
            def inner_callback(_, j=time):
                self.set_mins(_, j)
                for btn in [*self.things_buttons.values(), *self.buttons.values()]:
                    btn.set_callback(None)
                self.timer.count = 0
                self.timer.end = self.interval
                self.start_pause_button.title = "Pause Timer"
                self.timer.start()
            return inner_callback

        self.things_buttons = {
            f"{title}": rumps.MenuItem(
                title=f"({time} min) {title}",
                callback=callback(time),
                key=str(idx % 10) if idx < 10 else ""
            )
            for idx, (title, time) in enumerate(self.things_processed_tasks.items())
        }
        
        self.app.menu = [
            self.start_pause_button,
            None,
            self.sync_button,
            None,
            self.sum_menu_item,
            *self.things_buttons.values(),
            None,
            *self.buttons.values(),
            None,
            self.stop_button,
        ]

    def sync_data(self):
        self.things_tasks = get_things_today_tasks()

        self.things_processed_tasks = process_tasks(self.things_tasks)

        self.sum_of_tasks_scheduled = sum(self.things_processed_tasks.values())

        self.app.menu[
            "hours_spent"
        ].title = f"{hour_formatter(self.sum_of_tasks_scheduled)}"
        
        prev_things_buttons = self.things_buttons
        
        for title in prev_things_buttons.keys():
            del self.app.menu[prev_things_buttons[title].title]

        def callback(time):
            def inner_callback(_, j=time):
                self.set_mins(_, j)
                for btn in [*self.things_buttons.values(), *self.buttons.values()]:
                    btn.set_callback(None)
                self.timer.count = 0
                self.timer.end = self.interval
                self.start_pause_button.title = "Pause Timer"
                self.timer.start()
            return inner_callback

        self.things_buttons = {}
        for idx, (title, time) in reversed(list(enumerate(self.things_processed_tasks.items()))):
            menu_item = rumps.MenuItem(
                title=f"({time} min) {title}",
                callback=callback(time),
                key=str(idx % 10) if idx < 10 else ""
            )
            self.things_buttons[title] = menu_item
            self.app.menu.insert_after("hours_spent", menu_item) 

    def run(self):
        self.app.menu[
            "hours_spent"
        ].title = f"{hour_formatter(self.sum_of_tasks_scheduled)}"
        self.app.run()

    def set_mins(self, sender, interval):
        for btn in [*self.things_buttons.values(), *self.buttons.values()]:
            if sender.title == btn.title:
                self.interval = interval * SEC_TO_MIN
                cleaned_title = " ".join(sender.title.split()[2:])
                self.menu_title = (
                    " ".join(cleaned_title.split()[:4])
                    if len(cleaned_title.split()) > 4
                    else cleaned_title
                )
                btn.state = True
            elif sender.title != btn.title:
                btn.state = False

    def start_timer(self, sender, interval):
        for btn in [*self.things_buttons.values(), *self.buttons.values()]:
            btn.set_callback(None)

        if sender.title.lower().startswith(("start", "continue")):

            if sender.title == "Start Timer":
                # reset timer & set stop time
                self.timer.count = 0
                self.timer.end = interval

            # change title of MenuItem from 'Start timer' to 'Pause timer'
            sender.title = "Pause Timer"

            # lift off! start the timer
            self.timer.start()
        else:  # 'Pause Timer'
            sender.title = "Continue Timer"
            self.timer.stop()

    def on_tick(self, sender):
        time_left = sender.end - sender.count
        mins = time_left // 60 if time_left >= 0 else time_left // 60 + 1
        secs = time_left % 60 if time_left >= 0 else (-1 * time_left) % 60
        if mins == 0 and time_left < 0:
            rumps.notification(
                title="Timebox", subtitle="Time is up! Take a break :)", message=""
            )
            self.stop_timer(sender)
            self.stop_button.set_callback(None)
        else:
            self.stop_button.set_callback(self.stop_timer)
            self.app.title = "{} {:2d}:{:02d}".format(
                getattr(self, "menu_title", ""), mins, secs
            )
        sender.count += 1

    def stop_timer(self, sender=None):
        self.timer.stop()
        self.timer.count = 0
        self.app.title = "🥊"
        self.stop_button.set_callback(None)

        for key, btn in self.buttons.items():
            btn.set_callback(self.buttons_callback[btn.title])

        for (title, btn) in self.things_buttons.items():
            btn.set_callback(
                lambda _: self.set_mins(_, self.things_processed_tasks[title])
            )

        self.start_pause_button.title = "Start Timer"


# %%
if __name__ == "__main__":
    app = TimerApp(timer_interval=1)
    app.run()
