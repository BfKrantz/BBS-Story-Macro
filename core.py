"""
Core screen-watching / clicking engine, shared by the GUI and CLI front ends.
"""

import random
import sys
import threading
import time
from pathlib import Path

import cv2
import numpy as np
import mss
import pyautogui

try:
    import pygetwindow as gw
except ImportError:
    gw = None


def _base_path():
    """Resolve the app's base directory, whether running from source or
    as a PyInstaller-frozen .exe (where files live under sys._MEIPASS)."""
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS)
    return Path(__file__).parent.parent


TEMPLATES_DIR = _base_path() / "templates"

CLICK_PRIORITY = [
    {"name": "skip",               "file": "skip_template.png",               "threshold": 0.85},
    {"name": "tap_screen",         "file": "tap_template.png",                "threshold": 0.82},
    {"name": "quest_clear_banner", "file": "story_template.png",              "threshold": 0.80},
    {"name": "close",              "file": "close_template.png",              "threshold": 0.85},
    {"name": "next_quest",         "file": "next_quest_template.png",         "threshold": 0.85},
    {"name": "prepare_for_quest",  "file": "prepare_for_quest_template.png",  "threshold": 0.85},
    {"name": "start_quest",        "file": "start_quest_template.png",        "threshold": 0.85},
]

LOOP_DELAY_RANGE = (0.35, 0.65)
POST_CLICK_DELAY_RANGE = (0.25, 0.45)
MATCH_SCALES = [0.95, 1.0, 1.05]

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0


def find_game_region(window_title_hint="Bleach", log=print):
    """Return (left, top, width, height) of the game window, or None for full screen."""
    if gw is None:
        log("pygetwindow not installed - scanning the entire primary screen instead.")
        return None
    matches = [w for w in gw.getAllWindows() if window_title_hint.lower() in w.title.lower()]
    if not matches:
        log(f"No window found containing '{window_title_hint}' - scanning entire screen.")
        return None
    win = matches[0]
    try:
        win.activate()
    except Exception:
        pass
    time.sleep(0.3)
    return (win.left, win.top, win.width, win.height)


def load_templates(log=print):
    templates = []
    for entry in CLICK_PRIORITY:
        path = TEMPLATES_DIR / entry["file"]
        img = cv2.imread(str(path), cv2.IMREAD_COLOR)
        if img is None:
            log(f"Could not load template: {path}")
            continue
        templates.append({**entry, "image": img})
    return templates


def best_match(screen_bgr, template_bgr, scales=MATCH_SCALES):
    best_val, best_loc, best_size = -1, None, None
    th, tw = template_bgr.shape[:2]
    for scale in scales:
        w, h = int(tw * scale), int(th * scale)
        if w < 5 or h < 5:
            continue
        if h >= screen_bgr.shape[0] or w >= screen_bgr.shape[1]:
            continue
        resized = cv2.resize(template_bgr, (w, h), interpolation=cv2.INTER_AREA)
        result = cv2.matchTemplate(screen_bgr, resized, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)
        if max_val > best_val:
            best_val, best_loc, best_size = max_val, max_loc, (w, h)
    return best_val, best_loc, best_size


class AutoFarmer:
    """
    Runs the watch/click loop on a background thread.

    Usage:
        farmer = AutoFarmer(log_callback=my_log_fn, status_callback=my_status_fn)
        farmer.start()
        ...
        farmer.pause()   # toggle
        farmer.stop()
    """

    def __init__(self, window_title_hint="Bleach", log_callback=None, status_callback=None,
                 click_callback=None):
        self.window_title_hint = window_title_hint
        self.log = log_callback or print
        self.status_callback = status_callback or (lambda s: None)
        self.click_callback = click_callback or (lambda name, count: None)

        self._thread = None
        self._stop_event = threading.Event()
        self._paused = False
        self.click_count = 0

    @property
    def running(self):
        return self._thread is not None and self._thread.is_alive()

    def start(self):
        if self.running:
            return
        self._stop_event.clear()
        self._paused = False
        self.click_count = 0
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        self.status_callback("running")

    def stop(self):
        self._stop_event.set()
        self.status_callback("stopped")

    def toggle_pause(self):
        self._paused = not self._paused
        self.status_callback("paused" if self._paused else "running")

    def _run(self):
        self.log("Locating game window...")
        region = find_game_region(self.window_title_hint, log=self.log)
        templates = load_templates(log=self.log)
        if not templates:
            self.log("No templates loaded - aborting.")
            self.status_callback("stopped")
            return

        self.log("Watching for buttons. Click Stop to end.")

        with mss.mss() as sct:
            if region:
                left, top, width, height = region
                monitor = {"left": left, "top": top, "width": width, "height": height}
            else:
                monitor = sct.monitors[1]

            while not self._stop_event.is_set():
                if self._paused:
                    time.sleep(0.2)
                    continue

                shot = np.array(sct.grab(monitor))
                screen_bgr = cv2.cvtColor(shot, cv2.COLOR_BGRA2BGR)

                clicked_this_frame = False
                for tmpl in templates:
                    val, loc, size = best_match(screen_bgr, tmpl["image"])
                    if val >= tmpl["threshold"]:
                        w, h = size
                        cx = monitor["left"] + loc[0] + w // 2
                        cy = monitor["top"] + loc[1] + h // 2
                        pyautogui.moveTo(cx, cy, duration=random.uniform(0.05, 0.15))
                        pyautogui.click()
                        self.click_count += 1
                        self.log(f"[{self.click_count}] clicked '{tmpl['name']}' "
                                 f"(conf={val:.2f}) at ({cx},{cy})")
                        self.click_callback(tmpl["name"], self.click_count)
                        clicked_this_frame = True
                        time.sleep(random.uniform(*POST_CLICK_DELAY_RANGE))
                        break

                if not clicked_this_frame:
                    time.sleep(random.uniform(*LOOP_DELAY_RANGE))

        self.log(f"Stopped. Total clicks: {self.click_count}")
        self.status_callback("stopped")
