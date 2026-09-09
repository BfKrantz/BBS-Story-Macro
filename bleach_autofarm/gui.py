"""
Simple Tkinter GUI for the auto-farm clicker: Start / Pause / Stop buttons
and a live scrolling log.
"""

import queue
import tkinter as tk
from tkinter import scrolledtext, ttk

from .core import AutoFarmer

STATUS_COLORS = {
    "stopped": "#b0413e",
    "running": "#3e9b4f",
    "paused": "#c48a1c",
}


class App:
    def __init__(self, root):
        self.root = root
        root.title("Bleach: Brave Souls - Auto Farm")
        root.geometry("620x420")
        root.minsize(480, 320)

        self.log_queue = queue.Queue()
        self.farmer = AutoFarmer(
            window_title_hint="Bleach",
            log_callback=self._enqueue_log,
            status_callback=self._on_status_change,
            click_callback=self._on_click,
        )

        self._build_widgets()
        self.root.after(100, self._drain_log_queue)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_widgets(self):
        top = ttk.Frame(self.root, padding=10)
        top.pack(fill="x")

        ttk.Label(top, text="Game window title contains:").grid(row=0, column=0, sticky="w")
        self.title_var = tk.StringVar(value="Bleach")
        ttk.Entry(top, textvariable=self.title_var, width=20).grid(row=0, column=1, sticky="w", padx=(6, 0))

        btns = ttk.Frame(self.root, padding=(10, 0))
        btns.pack(fill="x")

        self.start_btn = ttk.Button(btns, text="Start", command=self._on_start)
        self.start_btn.pack(side="left", padx=(0, 6))

        self.pause_btn = ttk.Button(btns, text="Pause", command=self._on_pause, state="disabled")
        self.pause_btn.pack(side="left", padx=6)

        self.stop_btn = ttk.Button(btns, text="Stop", command=self._on_stop, state="disabled")
        self.stop_btn.pack(side="left", padx=6)

        status_frame = ttk.Frame(self.root, padding=10)
        status_frame.pack(fill="x")
        ttk.Label(status_frame, text="Status:").pack(side="left")
        self.status_dot = tk.Canvas(status_frame, width=14, height=14, highlightthickness=0)
        self.status_dot.pack(side="left", padx=(6, 4))
        self._dot = self.status_dot.create_oval(2, 2, 12, 12, fill=STATUS_COLORS["stopped"], outline="")
        self.status_label = ttk.Label(status_frame, text="Stopped")
        self.status_label.pack(side="left")

        self.clicks_label = ttk.Label(status_frame, text="Clicks: 0")
        self.clicks_label.pack(side="right")

        log_frame = ttk.Frame(self.root, padding=(10, 0, 10, 10))
        log_frame.pack(fill="both", expand=True)
        self.log_widget = scrolledtext.ScrolledText(log_frame, wrap="word", state="disabled",
                                                      font=("Consolas", 9))
        self.log_widget.pack(fill="both", expand=True)

        hint = ttk.Label(
            self.root,
            text="Tip: fling the mouse into a screen corner at any time to force-abort.",
            padding=(10, 0, 10, 10),
            foreground="#666",
        )
        hint.pack(fill="x")

    # --- button handlers -------------------------------------------------

    def _on_start(self):
        self.farmer.window_title_hint = self.title_var.get() or "Bleach"
        self.farmer.start()
        self.start_btn.config(state="disabled")
        self.pause_btn.config(state="normal", text="Pause")
        self.stop_btn.config(state="normal")

    def _on_pause(self):
        self.farmer.toggle_pause()

    def _on_stop(self):
        self.farmer.stop()
        self.start_btn.config(state="normal")
        self.pause_btn.config(state="disabled", text="Pause")
        self.stop_btn.config(state="disabled")

    def _on_close(self):
        self.farmer.stop()
        self.root.after(200, self.root.destroy)

    # --- callbacks from the background thread (must be thread-safe) -----

    def _enqueue_log(self, message):
        self.log_queue.put(message)

    def _on_status_change(self, status):
        # called from the worker thread; just queue a UI update
        self.log_queue.put(("__status__", status))

    def _on_click(self, name, count):
        self.log_queue.put(("__clicks__", count))

    # --- UI-thread polling ------------------------------------------------

    def _drain_log_queue(self):
        try:
            while True:
                item = self.log_queue.get_nowait()
                if isinstance(item, tuple):
                    kind, value = item
                    if kind == "__status__":
                        self._apply_status(value)
                    elif kind == "__clicks__":
                        self.clicks_label.config(text=f"Clicks: {value}")
                else:
                    self._append_log(item)
        except queue.Empty:
            pass
        self.root.after(100, self._drain_log_queue)

    def _apply_status(self, status):
        self.status_dot.itemconfig(self._dot, fill=STATUS_COLORS.get(status, "#999"))
        self.status_label.config(text=status.capitalize())
        if status == "stopped":
            self.start_btn.config(state="normal")
            self.pause_btn.config(state="disabled", text="Pause")
            self.stop_btn.config(state="disabled")
        elif status == "paused":
            self.pause_btn.config(text="Resume")
        elif status == "running":
            self.pause_btn.config(text="Pause")

    def _append_log(self, message):
        self.log_widget.config(state="normal")
        self.log_widget.insert("end", message + "\n")
        self.log_widget.see("end")
        self.log_widget.config(state="disabled")


def main():
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
