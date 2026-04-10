"""
ui_overlay.py
─────────────
Renders the on-screen HUD:
  • Top-left  : mode name + status message
  • Top-right : FPS counter + hand-count badge
  • Left edge : mode-switch progress ring (when switching)
  • Centre    : mode-switch flash banner
  • Overlay   : landmark skeleton (optional)
  • 'H' key   : full help screen
"""

import cv2
import math
import numpy as np
from modules.gesture_engine import GestureResults, LM


# ── Palette ───────────────────────────────────────────────────────
COL_ACCENT   = (100, 200, 255)      # cyan-ish blue
COL_WARN     = (50,  200, 100)      # green
COL_WHITE    = (255, 255, 255)
COL_DIM      = (120, 120, 120)
COL_BG       = (20,  20,  40)
COL_FLASH    = (60,  180, 255)


HELP_TEXT = [
    ("GESTURE CONTROL SYSTEM — HELP", True),
    ("", False),
    ("MODE SWITCHING  (left hand finger count):", True),
    ("  1 finger  →  Virtual Mouse", False),
    ("  2 fingers →  Virtual Keyboard", False),
    ("  3 fingers →  Volume Control", False),
    ("  4 fingers →  Brightness Control", False),
    ("  5 fingers →  Scroll Control", False),
    ("", False),
    ("VIRTUAL MOUSE:", True),
    ("  Index finger only  →  Move cursor", False),
    ("  Thumb + Index pinch  →  Left click", False),
    ("  Pinch twice quickly  →  Double click", False),
    ("  Index + Middle  →  Right click", False),
    ("  Fist  →  Click & drag", False),
    ("", False),
    ("VIRTUAL KEYBOARD:", True),
    ("  Hover index over key, then pinch to type", False),
    ("", False),
    ("VOLUME / BRIGHTNESS:", True),
    ("  Spread / close thumb & index  →  Volume", False),
    ("  Move open palm up / down  →  Brightness", False),
    ("", False),
    ("SCROLL:", True),
    ("  Index + Middle, move up/down  →  Scroll", False),
    ("", False),
    ("SCREENSHOT:", True),
    ("  Open palm, hold 1 s  →  Capture screen", False),
    ("", False),
    ("KEYBOARD SHORTCUTS:", True),
    ("  Q  →  Quit    H  →  Toggle help    D  →  Debug", False),
]


class UIOverlay:
    def __init__(self, cam_w: int = 1280, cam_h: int = 720):
        self.cam_w     = cam_w
        self.cam_h     = cam_h
        self._show_help = False

    def toggle_help(self) -> None:
        self._show_help = not self._show_help

    # ── Main draw entry point ─────────────────────────────────────

    def draw(self, frame: np.ndarray, results: GestureResults,
             mode_manager) -> np.ndarray:

        if self._show_help:
            return self._draw_help(frame)

        # Skeleton landmarks
        for hand in results.hands:
            self._draw_skeleton(frame, hand)

        # Mode switch flash banner
        if mode_manager.switch_flash > 0:
            self._draw_mode_banner(frame, mode_manager.name,
                                   mode_manager.switch_flash)

        # Mode-switch progress ring
        prog = mode_manager.hold_progress
        if prog > 0 and mode_manager.candidate_name:
            self._draw_progress_ring(frame, prog, mode_manager.candidate_name)

        # HUD panels
        self._draw_top_left(frame, mode_manager)
        self._draw_top_right(frame, results)
        self._draw_gesture_badge(frame, results)

        return frame

    # ── Sub-renders ───────────────────────────────────────────────

    def _draw_skeleton(self, frame, hand) -> None:
        CONNECTIONS = [
            (0,1),(1,2),(2,3),(3,4),
            (0,5),(5,6),(6,7),(7,8),
            (5,9),(9,10),(10,11),(11,12),
            (9,13),(13,14),(14,15),(15,16),
            (13,17),(17,18),(18,19),(19,20),
            (0,17),
        ]
        lm = hand.landmarks
        for a, b in CONNECTIONS:
            cv2.line(frame, lm[a], lm[b], (60, 120, 180), 2)
        for i, (px, py) in enumerate(lm):
            col = COL_ACCENT if i in LM.TIPS else (80, 150, 220)
            cv2.circle(frame, (px, py), 5 if i in LM.TIPS else 3, col, -1)

    def _draw_top_left(self, frame, mode_manager) -> None:
        # Semi-transparent panel
        overlay = frame.copy()
        cv2.rectangle(overlay, (10, 10), (440, 80), COL_BG, -1)
        cv2.addWeighted(overlay, 0.65, frame, 0.35, 0, frame)
        cv2.rectangle(frame, (10, 10), (440, 80), COL_ACCENT, 1)

        # Mode name
        cv2.putText(frame, mode_manager.name,
                    (20, 38), cv2.FONT_HERSHEY_SIMPLEX,
                    0.75, COL_ACCENT, 2, cv2.LINE_AA)

        # Status message
        status = mode_manager.get_controller_status()
        cv2.putText(frame, status[:55],
                    (20, 65), cv2.FONT_HERSHEY_SIMPLEX,
                    0.45, COL_WHITE, 1, cv2.LINE_AA)

    def _draw_top_right(self, frame, results: GestureResults) -> None:
        fps_str  = f"FPS: {results.fps:.0f}"
        hand_str = f"Hands: {results.hand_count}"
        overlay = frame.copy()
        cv2.rectangle(overlay,
                      (self.cam_w - 180, 10),
                      (self.cam_w - 10, 75), COL_BG, -1)
        cv2.addWeighted(overlay, 0.65, frame, 0.35, 0, frame)
        cv2.rectangle(frame,
                      (self.cam_w - 180, 10),
                      (self.cam_w - 10, 75), COL_ACCENT, 1)

        fps_color = COL_WARN if results.fps >= 25 else (50, 50, 255)
        cv2.putText(frame, fps_str,
                    (self.cam_w - 165, 38),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, fps_color, 2, cv2.LINE_AA)
        cv2.putText(frame, hand_str,
                    (self.cam_w - 165, 62),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, COL_WHITE, 1, cv2.LINE_AA)

    def _draw_gesture_badge(self, frame, results: GestureResults) -> None:
        label = results.gesture_label
        if label in ("none", "unknown"):
            return
        text = f"✦ {label.upper()}"
        (tw, _), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
        bx = self.cam_w // 2 - tw // 2 - 10
        overlay = frame.copy()
        cv2.rectangle(overlay, (bx - 5, self.cam_h - 55),
                      (bx + tw + 20, self.cam_h - 20), COL_BG, -1)
        cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)
        cv2.putText(frame, text,
                    (bx + 5, self.cam_h - 28),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, COL_ACCENT, 2, cv2.LINE_AA)

    def _draw_mode_banner(self, frame, name: str, flash: int) -> None:
        alpha = min(flash / 20, 1.0)
        overlay = frame.copy()
        bh = 60
        cy = self.cam_h // 2
        cv2.rectangle(overlay, (0, cy - bh // 2),
                      (self.cam_w, cy + bh // 2), COL_FLASH, -1)
        cv2.addWeighted(overlay, alpha * 0.5, frame, 1 - alpha * 0.5, 0, frame)

        (tw, th), _ = cv2.getTextSize(name, cv2.FONT_HERSHEY_SIMPLEX, 1.1, 3)
        cv2.putText(frame, name,
                    (self.cam_w // 2 - tw // 2, cy + th // 2),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.1, COL_BG, 3, cv2.LINE_AA)

    def _draw_progress_ring(self, frame, progress: float,
                             candidate: str) -> None:
        cx, cy = 100, 180
        r      = 45
        cv2.circle(frame, (cx, cy), r, (50, 50, 70), 4)
        end_angle = int(-90 + 360 * progress)
        cv2.ellipse(frame, (cx, cy), (r, r), 0, -90, end_angle,
                    COL_ACCENT, 5)
        cv2.putText(frame, f"{int(progress * 100)}%",
                    (cx - 20, cy + 7),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, COL_WHITE, 1, cv2.LINE_AA)
        # Candidate name beneath ring
        short = candidate.split()[-1]  # e.g. "Mouse"
        cv2.putText(frame, f"→ {short}",
                    (cx - 28, cy + r + 22),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, COL_ACCENT, 1, cv2.LINE_AA)

    def _draw_help(self, frame: np.ndarray) -> np.ndarray:
        overlay = np.zeros_like(frame)
        cv2.rectangle(overlay, (60, 30), (self.cam_w - 60, self.cam_h - 30),
                      (15, 15, 35), -1)
        cv2.addWeighted(overlay, 0.92, frame, 0.08, 0, frame)
        cv2.rectangle(frame, (60, 30), (self.cam_w - 60, self.cam_h - 30),
                      COL_ACCENT, 2)

        y = 70
        for text, bold in HELP_TEXT:
            if not text:
                y += 12
                continue
            scale  = 0.55 if bold else 0.48
            thick  = 2    if bold else 1
            color  = COL_ACCENT if bold else COL_WHITE
            cv2.putText(frame, text, (90, y),
                        cv2.FONT_HERSHEY_SIMPLEX, scale, color, thick,
                        cv2.LINE_AA)
            y += 22 if bold else 20
            if y > self.cam_h - 50:
                break

        cv2.putText(frame, "Press H to close",
                    (self.cam_w // 2 - 80, self.cam_h - 45),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, COL_DIM, 1, cv2.LINE_AA)
        return frame
