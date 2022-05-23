# %%
import rumps
import time
import subprocess
import shlex
import os
from pathlib import Path

import tasks
from tasks import Task

rumps.debug_mode(True)

SEC_TO_MIN = 60


# def timez():
#     return time.strftime("%a, %d %b %Y %H:%M:%S +0000", time.localtime())

def timestamp():
    return time.strftime("%Y-%m-%d %H:%M:%S.000", time.localtime())

# %%

def hour_formatter(minutes):
    if minutes // 60 > 0:
        if spare_min := minutes % 60:
            return f"{minutes // 60}h, {spare_min}m of work today!"
        else:
            return f"{minutes // 60}h of work today!"
    else:
        return f"{minutes}m of work today!"

def task_to_csv(task, interval):
    return '{},{},{},{}\n'.format(timestamp(), task.url, task.title, interval)

# %%
class TimerApp(object):
    def __init__(self, timer_interval=1):
        self.timer = rumps.Timer(self.on_tick, 1)
        self.timer.stop()  # timer running when initialized
        self.timer.count = 0

        self.app = rumps.App("Timebox", "⏱")
        self.interval = SEC_TO_MIN

        self.current_task = Task()

        self.control_buttons = {}
        self.control_buttons['start_pause'] = rumps.MenuItem(
            title="Start Timer",
            callback=lambda _: self.start_timer(_, self.interval),
            key="s",
        )
        self.control_buttons['stop'] = rumps.MenuItem(title="Stop Timer", callback=None, key="x")
        self.control_buttons['sync'] = rumps.MenuItem(
            title="Sync", callback=lambda _: self.sync_data(), key="r"
        )

        self.buttons = {}
        self.buttons_callback = {}
        for i in [5, 10, 15, 20, 25]:
            task = Task(i, str(i) + " minutes", '')

            def callback(_):
                self.set_current_task(_, task)
                for btn in [*self.things_buttons.values(), *self.buttons.values()]:
                    btn.set_callback(None)
                self.timer.count = 0
                self.timer.end = self.interval
                self.control_buttons['start_pause'].title = "Pause Timer"
                self.timer.start()
            self.buttons["btn_" + str(i)] = rumps.MenuItem(
                title=task.title, callback=callback
            )
            self.buttons_callback[task.title] = callback

        self.things_buttons = {}

        self.sum_menu_item = rumps.MenuItem(title="hours_spent", callback=None)
        self.app.menu = [
            self.control_buttons['start_pause'],
            None,
            self.control_buttons['sync'],
            None,
            self.sum_menu_item,
            # *self.things_buttons.values(),
            None,
            *self.buttons.values(),
            None,
            self.control_buttons['stop'],
        ]
        self.sync_data()

    def create_time_callback(self, task: Task):
        def inner_callback(_):
            self.set_current_task(_, task)
            for btn in [*self.things_buttons.values(), *self.buttons.values()]:
                btn.set_callback(None)
            self.timer.count = 0
            self.timer.end = self.interval
            self.control_buttons['start_pause'].title = "Pause Timer"
            self.timer.start()
        return inner_callback

    def sync_data(self):
        self.things_tasks = tasks.get_things_today_tasks()
        self.things_processed_tasks = tasks.process_tasks(self.things_tasks)

        self.sum_of_tasks_scheduled = sum(
            list(map(lambda x: x.minutes, self.things_processed_tasks.values()))
        )

        self.sum_menu_item = rumps.MenuItem(title="hours_spent", callback=None)
        self.app.menu[
            "hours_spent"
        ].title = f"{hour_formatter(self.sum_of_tasks_scheduled)}"

        prev_things_buttons = self.things_buttons

        for title in prev_things_buttons.keys():
            del self.app.menu[prev_things_buttons[title].title]

            # for idx, (title, (link, time)) in enumerate(self.things_processed_tasks.items())
        self.things_buttons = {}
        for idx, (title, task) in reversed(list(enumerate(self.things_processed_tasks.items()))):

            menu_item = rumps.MenuItem(
                title=f"({task.minutes} min) {task.url} {task.title}",
                callback=self.create_time_callback(task),
                key=str((idx + 1) % 10) if idx < 10 else ""
            )
            self.things_buttons[title] = menu_item
            self.app.menu.insert_after("hours_spent", menu_item)


    def run(self):
        self.app.menu[
            "hours_spent"
        ].title = f"{hour_formatter(self.sum_of_tasks_scheduled)}"
        self.app.run()

    def set_current_task(self, sender, task: Task):
        self.current_task = task

        for btn in [*self.things_buttons.values(), *self.buttons.values()]:
            if sender.key == btn.key:
                self.interval = task.minutes * SEC_TO_MIN
                print(f"here: {self.interval}")
                # remove time from title
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

            setattr(self, "_taskname", getattr(self, "menu_title", ""))
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
            self.on_last_tick(sender)
        else:
            self.control_buttons['stop'].set_callback(self.stop_timer)
            self.app.title = "⏱ {:2d}:{:02d}".format(
                    mins, secs
            )
        sender.count += 1

    def on_last_tick(self, sender):
        rumps.notification(
                title="Timebox",
                subtitle="Time is up! Take a break :)",
                message="",
            )
        if self.current_task.url is not '':
            subprocess.call(
                shlex.split("open '" + self.current_task.url + "'")
            )

        self.stop_timer(sender)
        self.control_buttons['stop'].set_callback(None)
        self.sync_data()

    def stop_timer(self, sender:rumps.MenuItem=None):

# TODO: add buttons?
#     :param action_button: title for the action button.
#    :param other_button: title for the other button.
#    :param has_reply_button: whether or not the notification has a reply button.
        rumps.notification(
                title="Timebox",
                subtitle="Time is up! Take a break :)",
                message="",
            )
        self.timer.stop()
        prev_count = self.timer.count - 1
        self.timer.count = 0
        self.app.title = "⏱"
        self.control_buttons['stop'].set_callback(None)

        for key, btn in self.buttons.items():
            btn.set_callback(self.buttons_callback[btn.title])

        for (title, btn) in self.things_buttons.items():
            btn.set_callback(
                lambda _: self.set_current_task(
                    _, self.things_processed_tasks[title]
                )
            )

        os.system('afplay /System/Library/Sounds/Submarine.aiff')

        self.sync_data()
        self.control_buttons['start_pause'].title = "Start Timer"
        downloads_path = str(Path.home() / "Downloads" / 'log.csv')
        with open(downloads_path, 'a+', encoding="utf-8") as f:
            f.write(task_to_csv(self.current_task, prev_count))

# %%
if __name__ == "__main__":
    app = TimerApp(timer_interval=1)
    app.run()
