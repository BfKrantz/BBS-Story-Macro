"""Headless CLI front end (no window required)."""

import time

from .core import AutoFarmer


def main():
    farmer = AutoFarmer(window_title_hint="Bleach")
    farmer.start()
    print("Running. Press Ctrl+C to stop.")
    try:
        while farmer.running:
            time.sleep(0.5)
    except KeyboardInterrupt:
        farmer.stop()


if __name__ == "__main__":
    main()
