#!/opt/homebrew/Caskroom/miniconda/base/envs/distraction_free/bin/python3

import os

import psutil
import rumps
from Quartz import CGWindowListCopyWindowInfo, kCGWindowListOptionOnScreenOnly

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
COOL_OFF_APPS = [
    # Add cool off apps you want to prevent using immediately after
]
TIMER_COUNTDOWN = 60 * 10
COOL_OFF_TIMER_COUNTDOWN = 60 * 15


class CountdownApp(object):
    def __init__(self):
        self.config = {
           "app_name": "Countdown", 
           "interval": TIMER_COUNTDOWN,
           "cooloff_interval": COOL_OFF_TIMER_COUNTDOWN
        }
        self.app = rumps.App(self.config["app_name"])
        self.timer = rumps.Timer(self.on_tick, 1)
        self.interval = self.config["interval"]
        self.cool_off = False
        self.cool_off_interval = self.config["cooloff_interval"]
        self.start_timer()

    def on_tick(self, sender):
        time_left = sender.end - sender.count
        mins = time_left // 60 if time_left >= 0 else time_left // 60 + 1
        secs = time_left % 60 if time_left >= 0 else (-1 * time_left) % 60

        if self.cool_off:
            terminate_unallowed_foreground_processes()

        if mins == 0 and time_left < 0:
            terminate_unallowed_foreground_processes()
            self.cool_off = not self.cool_off
            self.start_timer()
        else:
            self.app.title = "{:2d}:{:02d}".format(mins, secs)
            if self.cool_off:
                self.app.title = "❄" + self.app.title
            sender.count += 1

    def start_timer(self):
        self.timer.count = 0
        self.timer.end = self.cool_off_interval if self.cool_off else self.interval
        self.timer.start()

    def run(self):
        self.app.run()


def get_foreground_processes():
    """Return a set of process names that are currently visible on screen."""
    window_list = CGWindowListCopyWindowInfo(kCGWindowListOptionOnScreenOnly, 0)
    foreground_processes = set()
    for window in window_list:
        app_name = window.get("kCGWindowOwnerName", "")
        if app_name:
            foreground_processes.add(app_name)
    return foreground_processes


def terminate_unallowed_foreground_processes():
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
                    proc.terminate()
                    proc.wait()  # Wait for process termination
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass


if __name__ == "__main__":
    app = CountdownApp()
    app.run()
