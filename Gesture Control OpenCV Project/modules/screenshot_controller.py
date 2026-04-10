"""
screenshot_controller.py
─────────────────────────
Open-palm gesture (all 5 fingers raised, held for ~1 s) captures
a full-screen screenshot and saves it with a timestamp.
"""

import cv2
import time
import datetime
import os
import numpy as np
import pyautogui
from modules.gesture_engine import GestureResults

SAVE_DIR         = os.path.expanduser("~/Pictures/gesture_screenshots")
HOLD_SECONDS     = 1.2    # seconds palm must be held to trigger
COOLDOWN_SECONDS = 3.0    # seconds between consecutive shots
FLASH_FRAMES     = 20     # white-flash duration in frames


class ScreenshotController:
    def __init__(self):
        os.makedirs(SAVE_DIR, exist_ok=True)
        self._hold_start  : float | None = None
        self._last_shot   : float        = 0.0
        self._flash       : int          = 0
        self._last_file   : str          = ""
        self.status       : str          = "Open palm & hold to screenshot"

    def process(self, results: GestureResults, frame: np.ndarray) -> None:
        hand = results.primary

        palm_open = (
            hand is not None
            and all(hand.fingers_up)
        )

        if palm_open:
            if self._hold_start is None:
                self._hold_start = time.time()

            elapsed = time.time() - self._hold_start
            progress = min(elapsed / HOLD_SECONDS, 1.0)
            self._draw_progress(frame, hand, progress)

            if elapsed >= HOLD_SECONDS:
                now = time.time()
                if now - self._last_shot >= COOLDOWN_SECONDS:
                    self._capture(frame)
                    self._hold_start = None
                else:
                    self.status = "Cooldown…"
        else:
            self._hold_start = None
            if self._flash <= 0:
                self.status = "Open palm & hold to screenshot"

        # White flash after capture
        if self._flash > 0:
            alpha = self._flash / FLASH_FRAMES
            white = np.full_like(frame, 255)
            cv2.addWeighted(white, alpha * 0.6, frame, 1 - alpha * 0.6, 0, frame)
            self._flash -= 1

    # ── Private ───────────────────────────────────────────────────

    def _capture(self, frame: np.ndarray) -> None:
        ts   = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        path = os.path.join(SAVE_DIR, f"gesture_shot_{ts}.png")
        screenshot = pyautogui.screenshot()
        screenshot.save(path)
        self._last_shot  = time.time()
        self._last_file  = path
        self._flash      = FLASH_FRAMES
        self.status      = f"Saved: {os.path.basename(path)}"
        print(f"[SCREENSHOT] Saved → {path}")

    def _draw_progress(self, frame: np.ndarray, hand, progress: float) -> None:
        wx, wy = hand.landmarks[0]   # wrist
        r = 40
        # Background circle
        cv2.circle(frame, (wx, wy), r, (60, 60, 60), 4)
        # Progress arc
        end_angle = int(-90 + 360 * progress)
        cv2.ellipse(frame, (wx, wy), (r, r), 0, -90, end_angle,
                    (0, 255, 150), 4)
        pct_text = f"{int(progress * 100)}%"
        (tw, th), _ = cv2.getTextSize(pct_text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
        cv2.putText(frame, pct_text,
                    (wx - tw // 2, wy + th // 2),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
        self.status = f"Hold… {int(progress * 100)}%"
