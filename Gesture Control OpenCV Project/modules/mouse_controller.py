"""
mouse_controller.py
───────────────────
Maps index-finger tip position inside a reduced "active zone" to
full-screen cursor coordinates.  Pinch (thumb ↔ index) triggers
a left click; double-pinch within 400 ms triggers double-click;
peace sign (index + middle) triggers right-click.
"""

import time
import numpy as np
import pyautogui
from modules.gesture_engine import GestureResults, LM

pyautogui.FAILSAFE = True       #Allows you to kill the script by slamming mouse to a corner
pyautogui.PAUSE    = 0.0          # remove default 0.1 s delay


class MouseController:
    # Fraction of frame used as the active movement zone
    ZONE_MARGIN = 0.20            # 20 % margins on each side

    # Click thresholds
    PINCH_RATIO   = 0.045         # pinch distance / frame_width
    CLICK_DELAY   = 0.35          # seconds — debounce for single click
    DOUBLE_DELAY  = 0.40          # seconds — max gap for double-click

    def __init__(self):
        self.screen_w, self.screen_h = pyautogui.size()
        self._smooth_x = self.screen_w  / 2
        self._smooth_y = self.screen_h  / 2
        self._smooth   = 0.55           # EMA factor (higher = more smoothing)

        self._click_time   = 0.0
        self._last_click   = 0.0
        self._clicking     = False
        self._right_click  = False
        self.status        = "Move: index finger | Click: pinch"

    def process(self, results: GestureResults, frame: np.ndarray) -> None:
        hand = results.primary
        if hand is None:
            self.status = "No hand detected"
            return

        h, w = frame.shape[:2]
        ix, iy = hand.landmarks[LM.INDEX_TIP]

        # ── Map active zone → screen coords ──────────────────────
        margin_x = int(w * self.ZONE_MARGIN)
        margin_y = int(h * self.ZONE_MARGIN)
        zone_w   = w - 2 * margin_x
        zone_h   = h - 2 * margin_y

        mapped_x = np.interp(ix, [margin_x, margin_x + zone_w], [0, self.screen_w])
        mapped_y = np.interp(iy, [margin_y, margin_y + zone_h], [0, self.screen_h])

        # ── Smooth movement ───────────────────────────────────────
        s = self._smooth
        self._smooth_x = s * self._smooth_x + (1 - s) * mapped_x
        self._smooth_y = s * self._smooth_y + (1 - s) * mapped_y

        cx = int(np.clip(self._smooth_x, 0, self.screen_w  - 1))
        cy = int(np.clip(self._smooth_y, 0, self.screen_h - 1))

        # Only move cursor; avoid jerking when clicking
        fingers = hand.fingers_up
        is_moving = fingers[1] and not fingers[2]   # index only

        if is_moving:
            pyautogui.moveTo(cx, cy)
            self.status = f"Moving → ({cx}, {cy})"

        # ── Pinch → left click ────────────────────────────────────
        pinch_thresh = w * self.PINCH_RATIO
        pinch = hand.distance(LM.THUMB_TIP, LM.INDEX_TIP) < pinch_thresh

        if pinch and not self._clicking:
            now = time.time()
            gap = now - self._last_click
            if gap < self.DOUBLE_DELAY:
                pyautogui.doubleClick()
                self.status = "Double-click!"
            else:
                pyautogui.click()
                self.status = "Click!"
            self._last_click = now
            self._clicking   = True

        elif not pinch:
            self._clicking = False

        # ── Peace sign → right click ──────────────────────────────
        peace = fingers[1] and fingers[2] and not fingers[3] and not fingers[4]
        if peace and not self._right_click:
            pyautogui.rightClick()
            self.status = "Right-click!"
            self._right_click = True
        elif not peace:
            self._right_click = False

        # ── Fist → drag (hold left button) ───────────────────────
        fist = not any(fingers[1:])
        if fist:
            pyautogui.mouseDown()
            self.status = "Dragging…"
        else:
            pyautogui.mouseUp()
