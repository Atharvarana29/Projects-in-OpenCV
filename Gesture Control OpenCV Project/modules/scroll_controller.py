"""
scroll_controller.py
────────────────────
Two-finger (index + middle) vertical movement scrolls the active window.
Horizontal movement triggers horizontal scroll.
Scroll speed scales with gesture velocity.
"""

import cv2
import time
import numpy as np
import pyautogui
from modules.gesture_engine import GestureResults, LM

pyautogui.PAUSE = 0.0

SCROLL_SCALE = 0.03       # multiplier: pixels moved → scroll clicks
MIN_DELTA    = 8          # minimum pixel movement to register scroll


class ScrollController:
    def __init__(self):
        self._prev_y    : float | None = None
        self._prev_x    : float | None = None
        self._direction : str  = "–"
        self._velocity  : float = 0.0
        self.status     : str  = "Scroll | Index + Middle finger"

    def process(self, results: GestureResults, frame: np.ndarray) -> None:
        hand = results.primary
        if hand is None:
            self.status = "No hand detected"
            self._prev_y = None
            self._prev_x = None
            return

        fingers = hand.fingers_up
        # Require exactly index + middle raised
        scroll_active = (fingers[1] and fingers[2]
                         and not fingers[0]
                         and not fingers[3]
                         and not fingers[4])

        if not scroll_active:
            self.status = "Raise Index + Middle to scroll"
            self._prev_y = None
            self._prev_x = None
            return

        # Use midpoint of index and middle tips
        ix, iy = hand.landmarks[LM.INDEX_TIP]
        mx, my = hand.landmarks[LM.MIDDLE_TIP]
        cx = (ix + mx) / 2
        cy = (iy + my) / 2

        if self._prev_y is not None:
            dy = cy - self._prev_y
            dx = cx - self._prev_x

            # Dominant axis
            if abs(dy) >= abs(dx) and abs(dy) > MIN_DELTA:
                clicks = -int(dy * SCROLL_SCALE)   # negative = scroll up
                if clicks != 0:
                    pyautogui.scroll(clicks)
                self._direction = "↑" if dy < 0 else "↓"
                self._velocity  = abs(dy)
            elif abs(dx) > abs(dy) and abs(dx) > MIN_DELTA:
                clicks = int(dx * SCROLL_SCALE)
                if clicks != 0:
                    pyautogui.hscroll(clicks)
                self._direction = "→" if dx > 0 else "←"
                self._velocity  = abs(dx)

        self._prev_y = cy
        self._prev_x = cx

        self.status = f"Scrolling {self._direction}  speed={self._velocity:.0f}"

        # ── Visual: trail between fingers ─────────────────────────
        cv2.line(frame,
                 hand.landmarks[LM.INDEX_TIP],
                 hand.landmarks[LM.MIDDLE_TIP],
                 (0, 255, 180), 3)
        for tip in [LM.INDEX_TIP, LM.MIDDLE_TIP]:
            cv2.circle(frame, hand.landmarks[tip], 10, (0, 255, 180), -1)

        # Scroll direction arrow
        acx, acy = int(cx), int(cy)
        arrow_dy = -30 if self._direction == "↑" else 30
        cv2.arrowedLine(frame,
                        (acx, acy),
                        (acx, acy + arrow_dy),
                        (255, 255, 100), 3, tipLength=0.4)
