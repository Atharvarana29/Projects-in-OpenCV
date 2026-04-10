"""
brightness_controller.py
────────────────────────
Maps vertical position of the open palm (wrist Y) to screen brightness.

Linux: uses 'brightnessctl' or writes to /sys/class/backlight/
macOS: uses 'brightness' CLI tool (brew install brightness)
"""

import cv2
import subprocess
import platform
import numpy as np
from modules.gesture_engine import GestureResults, LM

SYSTEM = platform.system()


def set_brightness(pct: int) -> None:
    pct = int(np.clip(pct, 5, 100))
    try:
        if SYSTEM == "Linux":
            subprocess.run(
                ["brightnessctl", "set", f"{pct}%"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
        elif SYSTEM == "Darwin":
            val = pct / 100.0
            subprocess.run(
                ["brightness", str(val)],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
        elif SYSTEM == "Windows":
            try:
                import wmi
                c = wmi.WMI(namespace="wmi")
                methods = c.WmiMonitorBrightnessMethods()[0]
                methods.WmiSetBrightness(pct, 0)
            except Exception as e:
                print("Brightness control not available:", e)
    except Exception:
        pass


class BrightnessController:
    def __init__(self):
        self._brightness = 80
        self._bar_pct    = 80.0
        self.status      = "Brightness | Move palm up/down"

    def process(self, results: GestureResults, frame: np.ndarray) -> None:
        hand = results.primary
        if hand is None:
            self.status = "No hand detected"
            return

        h, w = frame.shape[:2]
        # Open palm only
        if hand.count_fingers() < 4:
            self.status = "Open palm to control brightness"
            return

        wy = hand.landmarks[LM.WRIST][1]
        # Map wrist Y (top=bright, bottom=dim)
        self._bar_pct = float(np.interp(wy, [h * 0.1, h * 0.85], [100.0, 5.0]))
        target = int(self._bar_pct)

        if abs(target - self._brightness) >= 2:
            self._brightness = target
            set_brightness(self._brightness)

        self.status = f"Brightness: {self._brightness}%"

        # Sun icon at wrist
        wx, wy2 = hand.landmarks[LM.WRIST]
        cv2.circle(frame, (wx, wy2), 18, (0, 220, 255), 2)
        for a in range(0, 360, 45):
            import math
            r_in, r_out = 22, 32
            x1 = int(wx + r_in  * math.cos(math.radians(a)))
            y1 = int(wy2 + r_in  * math.sin(math.radians(a)))
            x2 = int(wx + r_out * math.cos(math.radians(a)))
            y2 = int(wy2 + r_out * math.sin(math.radians(a)))
            cv2.line(frame, (x1, y1), (x2, y2), (0, 220, 255), 2)

        self._draw_bar(frame)

    def _draw_bar(self, frame: np.ndarray) -> None:
        bx, by_top, bw, bh = 60, 150, 30, 300
        by_bot = by_top + bh
        cv2.rectangle(frame, (bx, by_top), (bx + bw, by_bot), (40, 40, 40), -1)
        fill_h = int(bh * self._bar_pct / 100.0)
        fill_y = by_bot - fill_h
        brightness_color = (0, int(220 * self._bar_pct / 100), 255)
        cv2.rectangle(frame, (bx, fill_y), (bx + bw, by_bot), brightness_color, -1)
        cv2.rectangle(frame, (bx, by_top), (bx + bw, by_bot), (120, 180, 255), 2)
        cv2.putText(frame, f"{int(self._bar_pct)}%",
                    (bx - 5, by_bot + 25), cv2.FONT_HERSHEY_SIMPLEX,
                    0.6, (200, 230, 255), 1, cv2.LINE_AA)
        cv2.putText(frame, "BRT",
                    (bx, by_top - 10), cv2.FONT_HERSHEY_SIMPLEX,
                    0.5, (200, 230, 255), 1, cv2.LINE_AA)
