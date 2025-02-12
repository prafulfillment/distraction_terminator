#!/opt/homebrew/Caskroom/miniconda/base/envs/distraction_free/bin/python3

import os
import subprocess

import psutil
import rumps
from Quartz import CGWindowListCopyWindowInfo, kCGWindowListOptionOnScreenOnly
import time

# List of allowed process names for MacOSX
SYSTEM_PROCESSES = [
    "spotlight",
    "finder",
    "systemuiserver",
    "universalaccessauthwarn",
    "dock",
    "system settings",
    "loginwindow",
]
ALLOWED_PROCESSES = [

APP_NAME = "Countdown"
TIMER_COUNTDOWN = 60 * 70
COOL_OFF_TIMER_COUNTDOWN = TIMER_COUNTDOWN // 2

class CountdownApp(object):
    def __init__(self):
        self.app = rumps.App(APP_NAME)
        self.interval = TIMER_COUNTDOWN
        self.cool_off_interval = COOL_OFF_TIMER_COUNTDOWN

        self.timer = rumps.Timer(self.on_tick, 1)
        self.cool_off = True
        self.pause = False

        self.start_timer()

    def on_tick(self, sender):
        time_left = sender.end - sender.count
        mins = time_left // 60 if time_left >= 0 else time_left // 60 + 1
        secs = time_left % 60 if time_left >= 0 else (-1 * time_left) % 60

        self.pause = False
        if len(PAUSING_PROCESSES) > 0:
            all_processes = [item.name() for item in psutil.process_iter(['name'])]
            for process, count in PAUSING_PROCESSES:
                is_process_running = all_processes.count(process) == count
                if is_process_running:
                    self.pause = True

        if self.cool_off:
            if (time_left % 19 == 0) and (not self.pause):
                terminate_then_kill()

        if mins == 0 and time_left < 0:
            bring_todo_to_foreground()
            if not self.pause:
                terminate_then_kill()
            self.cool_off = not self.cool_off
            self.start_timer()
        else:
            self.app.title = "{:2d}:{:02d}".format(mins, secs)
            if self.pause:
                self.app.title = "⏸" + self.app.title
            elif self.cool_off:
                self.app.title = "❄" + self.app.title
            if not self.pause:
                sender.count += 1

    def start_timer(self):
        self.timer.count = 0
        self.timer.end = self.cool_off_interval if self.cool_off else self.interval
        self.timer.start()

    def run(self):
        self.app.run()


def bring_todo_to_foreground():
    applescript_code = f"""
tell application "Notes"
    show note "TODO"
    activate
end tell
"""
    subprocess.run(["osascript", "-e", applescript_code])


def get_foreground_processes():
    """Return a set of process names that are currently visible on screen."""
    window_list = CGWindowListCopyWindowInfo(kCGWindowListOptionOnScreenOnly, 0)
    foreground_processes = set()
    for window in window_list:
        app_name = window.get("kCGWindowOwnerName", "")
        if app_name:
            foreground_processes.add(app_name)
    return foreground_processes


def terminate_unallowed_foreground_processes(should_kill=False):
    foreground_processes = get_foreground_processes()

    for proc in psutil.process_iter(["pid", "name"]):
        try:
            process_name = proc.info["name"]
            if process_name in foreground_processes:
                if not any(
                    process_name.lower().startswith(allowed_name)
                    for allowed_name in (SYSTEM_PROCESSES + ALLOWED_PROCESSES)
                ):
                    print(f"Terminating {process_name} (PID: {proc.info['pid']})")
                    if should_kill:
                        proc.kill()
                    else:
                        proc.terminate()
                        proc.wait(timeout=5)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass

def terminate_then_kill():
    terminate_unallowed_foreground_processes()
    terminate_unallowed_foreground_processes(should_kill=True)

if __name__ == "__main__":
    app = CountdownApp()
    app.run()
