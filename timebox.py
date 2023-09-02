
# %%
from pathlib import Path
import os
import rumps
import shlex
import subprocess
import time

import tasks
from tasks import Task

from Foundation import (NSLog)

rumps.debug_mode(True)

global _log

SEC_TO_MIN = 60
DEFAULT_MINUTES = 25
DEBUG_FILE = str(Path.home() / "Downloads" / 'debug.log')
LOG_FILE = str(Path.home() / "Downloads" / 'log.csv')
APP_ICON = 'icons/t3_0530_7.png'

# %%
def timestamp():
    return time.strftime("%Y-%m-%d %H:%M:%S.000", time.localtime())

def hour_formatter(minutes):
    if minutes // 60 > 0:
        if spare_min := minutes % 60:
            return f"{minutes // 60}h, {spare_min}m of work today!"
        else:
            return f"{minutes // 60}h of work today!"
    else:
        return f"{minutes}m of work today!"

def task_to_csv(task, interval):
    return '{};"{}";"{}";{}\n'.format(timestamp(), task.url, task.title, interval)

# %%
class TimerApp(object):
    def __init__(self, timer_interval=1):
        self.timer = rumps.Timer(self.on_tick, 1)
        self.timer.stop()  # timer running when initialized
        
        self.timer.count = 0

        self.app = rumps.App("Timebox", icon = APP_ICON, template=True)
    
        self.current_task = Task()

        self.control_buttons = {}
        self.control_buttons['start_pause'] = rumps.MenuItem(
            title="Start Timer",
            callback=lambda _: self.on_press_start_pause(_, DEFAULT_MINUTES * SEC_TO_MIN),
            key="s",
            template=True
        )
        self.control_buttons['stop'] = rumps.MenuItem(title="Stop Timer", callback=None, key="x")
        self.control_buttons['sync'] = rumps.MenuItem(
            title="Sync", callback=lambda _: self.sync_data(), key="r"
        )
        self.control_buttons['open_things'] = rumps.MenuItem(
            title="Things Today",
            callback = self.open_things, 
            key="t"
        )

        self.buttons = {}
        self.buttons_callback = {}
        for i in [1, 5, 10, 15, 20, 25, 30, 35]:
            task_title_postfix = " minute" if i == 1 else " minutes"
            task = Task(i, str(i) + task_title_postfix, '')

            callback = self.create_task_callback(task)
            self.buttons["btn_" + str(i)] = rumps.MenuItem(
                title=task.title, callback=callback
            )
            self.buttons_callback[task.title] = callback


        self.things_buttons = {}

        self.sum_menu_item = rumps.MenuItem(title="hours_spent", callback=None)
        self.app.menu = [
            self.control_buttons['open_things'],
            None,
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

    def create_task_callback(self, task: Task):
        def inner_callback(_):
            self.set_current_task(_, task)
            self.restart_timer((task.minutes or DEFAULT_MINUTES) * SEC_TO_MIN)
        return inner_callback

    def open_things(self, sender):
        subprocess.call(
            shlex.split("open things:///show?id=today")
        )

    def sync_data(self):
        self.things_processed_tasks = tasks.get_things_today_tasks()

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
            callback = self.create_task_callback(task) 
            button_title=f"{task.title} ({task.minutes} min)" if task.minutes else task.title
            menu_item = rumps.MenuItem(
                title = button_title,
                callback = callback,
                key = str((idx + 1) % 10) if idx < 10 else ""
            )

            self.things_buttons[button_title] = menu_item
            self.buttons_callback[button_title] = callback

            self.app.menu.insert_after("hours_spent", menu_item)

    def run(self):
        self.app.menu[
            "hours_spent"
        ].title = f"{hour_formatter(self.sum_of_tasks_scheduled)}"
        self.app.run()

    def set_current_task(self, sender, task: Task):
        self.current_task = task

        for btn in [*self.things_buttons.values(), *self.buttons.values()]:
            if sender.title == btn.title:
                btn.state = True
            else:
                btn.state = False
    
    def disable_task_items(self):
        for btn in [*self.things_buttons.values(), *self.buttons.values()]:
            btn.set_callback(None)
    
    def enable_task_items(self):
        for btn in [*self.things_buttons.values(), *self.buttons.values()]:
            btn.set_callback(self.buttons_callback[btn.title])

    def on_press_start_pause(self, sender, interval):
        if sender.title.lower().startswith(("start", "continue")):

            if sender.title == "Start Timer":
                # reset timer & set stop time
                self.timer.count = 0
                self.timer.end = interval

            # change title of MenuItem from 'Start timer' to 'Pause timer'
            sender.title = "Pause Timer"

            self.timer.start()
            # lift off! start the timer
        else:  # 'Pause Timer'
            sender.title = "Continue Timer"
            self.timer.stop()
    
    def restart_timer(self, interval):
        self.disable_task_items()

        self.control_buttons['start_pause'].title = "Pause Timer"

        self.timer.count = 0
        self.timer.end = interval
        self.timer.start()

    def on_tick(self, sender):
        time_left = sender.end - sender.count
        mins = time_left // 60 if time_left >= 0 else time_left // 60 + 1
        secs = time_left % 60 if time_left >= 0 else (-1 * time_left) % 60

        if mins == 0 and time_left < 0:
            self.on_last_tick(sender)
        else:
            self.control_buttons['stop'].set_callback(self.stop_timer)
            self.app.title = "{:2d}:{:02d}".format(
                    mins, secs
            )
            # 0 = 360
            # 50% = (360 * 50 / 100)
            # end = 0
            angle = 360 * (sender.count / sender.end)
            rounded_angle = 360 - int((angle // 10) * 10)
            self.app.icon = './icons/icon' + '{:03}'.format(rounded_angle) + '.pdf'
        sender.count += 1

    def on_last_tick(self, sender):
        # TODO: add buttons?
        #     :param action_button: title for the action button.
        #    :param other_button: title for the other button.
        #    :param has_reply_button: whether or not the notification has a reply button.
        rumps.notification(
                title="Timebox",
                subtitle="Time is up! Take a break :)",
                message=self.current_task.title,
            )
            
        os.system('afplay /System/Library/Sounds/Submarine.aiff')

        if self.current_task.url != '':
            subprocess.call(
                shlex.split("open '" + self.current_task.url + "'")
            )

        self.stop_timer(sender)
        self.control_buttons['stop'].set_callback(None)
        self.sync_data()

    def stop_timer(self, sender):
        self.enable_task_items()
        
        #     :param action_button: title for the action button.
        #    :param other_button: title for the other button.
        #    :param has_reply_button: whether or not the notification has a reply button.
        
        self.timer.stop()
        prev_count = self.timer.count - 1
        self.timer.count = 0
        self.app.title = ""
        self.app.icon = APP_ICON
        self.control_buttons['stop'].set_callback(None)

        self.control_buttons['start_pause'].title = "Start Timer"
        
        self.sync_data()
        
        data = {
            'time': self.current_task.title,
        }
        
        with open(LOG_FILE, 'a+', encoding="utf-8") as f:
            f.write(task_to_csv(self.current_task, prev_count))
        
        rumps.notification(
                title="Timebox",
                subtitle="Time is up! Take a break :)",
                action_button="Start break pomo",
                message=self.current_task.title,
                data=data,
        )


@rumps.notifications
def notification_center(info):
    __log(info.items())

def __log(*args):
    log_str = ' '.join(map(str, args))
    with open(DEBUG_FILE, 'a+', encoding="utf-8") as f:
        f.write(log_str)
    NSLog(log_str)
# %%
if __name__ == "__main__":
    app = TimerApp(timer_interval=1)
    app.run()
