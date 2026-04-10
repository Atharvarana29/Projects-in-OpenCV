# """
# keyboard_controller.py
# ──────────────────────
# Renders a QWERTY on-screen keyboard onto the video frame.
# Index-finger tip hovers over keys; pinch (thumb ↔ index) types them.
# Supports Shift, Backspace, Space, and Enter.
# """

# import cv2
# import time
# import numpy as np
# import pyautogui
# from modules.gesture_engine import GestureResults, LM


# # ── Layout ────────────────────────────────────────────────────────
# ROWS = [
#     ['`','1','2','3','4','5','6','7','8','9','0','-','=','BKSP'],
#     ['TAB','q','w','e','r','t','y','u','i','o','p','[',']','\\'],
#     ['CAPS','a','s','d','f','g','h','j','k','l',';',"'",'ENTER'],
#     ['SHIFT','z','x','c','v','b','n','m',',','.','/','SHIFT'],
#     ['SPACE'],
# ]

# SPECIAL = {'BKSP', 'TAB', 'CAPS', 'ENTER', 'SHIFT', 'SPACE'}

# KEY_W   = 52
# KEY_H   = 50
# PAD     = 4
# ORIGIN  = (20, 340)          # top-left of keyboard on frame

# PINCH_RATIO   = 0.045
# CLICK_COOLDOWN= 0.35          # seconds between keystrokes


# class Key:
#     def __init__(self, label: str, x: int, y: int, w: int, h: int):
#         self.label = label
#         self.x, self.y, self.w, self.h = x, y, w, h

#     def hit(self, px: int, py: int) -> bool:
#         return self.x <= px <= self.x + self.w and self.y <= py <= self.y + self.h

#     @property
#     def center(self):
#         return (self.x + self.w // 2, self.y + self.h // 2)


# def build_keys() -> list:
#     keys = []
#     ox, oy = ORIGIN
#     special_widths = {
#         'BKSP': KEY_W * 2 + PAD,
#         'TAB':  KEY_W + KEY_W // 2,
#         'CAPS': KEY_W + KEY_W // 2,
#         'ENTER':KEY_W * 2,
#         'SHIFT':KEY_W + KEY_W // 2,
#         'SPACE':KEY_W * 8,
#     }
#     for row_i, row in enumerate(ROWS):
#         cx = ox
#         for label in row:
#             kw = special_widths.get(label, KEY_W)
#             keys.append(Key(label, cx, oy + row_i * (KEY_H + PAD), kw, KEY_H))
#             cx += kw + PAD
#     return keys


# class KeyboardController:
#     def __init__(self):
#         self.keys        = build_keys()
#         self.typed_text  = ""
#         self.shift_on    = False
#         self.caps_on     = False
#         self._last_key   = 0.0
#         self._pinching   = False
#         self.status      = "Virtual Keyboard active | Pinch to type"

#     # ── Public API ────────────────────────────────────────────────

#     def process(self, results: GestureResults, frame: np.ndarray) -> None:
#         self._draw_keyboard(frame)

#         hand = results.primary
#         if hand is None:
#             return

#         h, w = frame.shape[:2]
#         ix, iy = hand.landmarks[LM.INDEX_TIP]

#         # Highlight hovered key
#         hovered = self._get_hovered(ix, iy)
#         if hovered:
#             self._draw_key(frame, hovered, highlight=True)
#             cv2.circle(frame, (ix, iy), 8, (255, 255, 255), -1)

#         # Pinch detection
#         pinch_thresh = w * PINCH_RATIO
#         pinch = hand.distance(LM.THUMB_TIP, LM.INDEX_TIP) < pinch_thresh

#         if pinch and not self._pinching:
#             now = time.time()
#             if now - self._last_key > CLICK_COOLDOWN and hovered:
#                 self._type_key(hovered.label)
#                 self._last_key = now
#             self._pinching = True
#         elif not pinch:
#             self._pinching = False

#         # Show typed buffer
#         self._draw_buffer(frame)

#     # ── Drawing ───────────────────────────────────────────────────

#     def _draw_keyboard(self, frame: np.ndarray) -> None:
#         for key in self.keys:
#             self._draw_key(frame, key, highlight=False)

#     def _draw_key(self, frame: np.ndarray, key: Key,
#                   highlight: bool = False) -> None:
#         x, y, w, h = key.x, key.y, key.w, key.h

#         # Background
#         overlay = frame.copy()
#         if highlight:
#             bg = (200, 200, 255)
#         elif key.label in SPECIAL:
#             bg = (50, 50, 80)
#         else:
#             bg = (30, 30, 50)
#         cv2.rectangle(overlay, (x, y), (x + w, y + h), bg, -1)
#         cv2.addWeighted(overlay, 0.75, frame, 0.25, 0, frame)

#         # Border
#         border_col = (120, 180, 255) if highlight else (80, 100, 150)
#         cv2.rectangle(frame, (x, y), (x + w, y + h), border_col, 1)

#         # Label
#         label = key.label
#         if len(label) == 1 and (self.shift_on or self.caps_on):
#             label = label.upper()
#         font_scale = 0.45 if key.label not in SPECIAL else 0.38
#         (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX,
#                                        font_scale, 1)
#         tx = x + (w - tw) // 2
#         ty = y + (h + th) // 2
#         color = (255, 255, 255) if not highlight else (20, 20, 60)
#         cv2.putText(frame, label, (tx, ty),
#                     cv2.FONT_HERSHEY_SIMPLEX, font_scale, color, 1,
#                     cv2.LINE_AA)

#     def _draw_buffer(self, frame: np.ndarray) -> None:
#         ox, oy = ORIGIN
#         bx, by, bw, bh = ox, oy - 50, 720, 40
#         overlay = frame.copy()
#         cv2.rectangle(overlay, (bx, by), (bx + bw, by + bh), (20, 20, 40), -1)
#         cv2.addWeighted(overlay, 0.8, frame, 0.2, 0, frame)
#         cv2.rectangle(frame, (bx, by), (bx + bw, by + bh), (80, 120, 200), 1)
#         display = self.typed_text[-55:] if len(self.typed_text) > 55 else self.typed_text
#         cv2.putText(frame, display + "▌", (bx + 8, by + 28),
#                     cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 230, 255), 1, cv2.LINE_AA)

#     # ── Key action ────────────────────────────────────────────────

#     def _get_hovered(self, px: int, py: int) -> Key | None:
#         for key in self.keys:
#             if key.hit(px, py):
#                 return key
#         return None

#     def _type_key(self, label: str) -> None:
#         if label == 'BKSP':
#             pyautogui.press('backspace')
#             self.typed_text = self.typed_text[:-1]
#             self.status = "⌫ Backspace"
#         elif label == 'SPACE':
#             pyautogui.press('space')
#             self.typed_text += ' '
#             self.status = "Space"
#         elif label == 'ENTER':
#             pyautogui.press('enter')
#             self.typed_text += '\n'
#             self.status = "↵ Enter"
#         elif label == 'TAB':
#             pyautogui.press('tab')
#             self.typed_text += '  '
#             self.status = "⇥ Tab"
#         elif label == 'SHIFT':
#             self.shift_on = not self.shift_on
#             self.status = f"Shift {'ON' if self.shift_on else 'OFF'}"
#         elif label == 'CAPS':
#             self.caps_on = not self.caps_on
#             self.status = f"Caps {'ON' if self.caps_on else 'OFF'}"
#         else:
#             char = label.upper() if (self.shift_on or self.caps_on) else label.lower()
#             pyautogui.typewrite(char, interval=0.01)
#             self.typed_text += char
#             if self.shift_on:
#                 self.shift_on = False        # shift auto-releases
#             self.status = f"Typed: {char}"



"""
keyboard_controller.py
──────────────────────
Simplified version to prevent system-wide import crashes.
"""

import cv2
import time
import numpy as np
import pyautogui

# ── Keyboard Configuration ────────────────────────────────────────
ROWS = [
    ['`','1','2','3','4','5','6','7','8','9','0','-','=','BKSP'],
    ['TAB','q','w','e','r','t','y','u','i','o','p','[',']','\\'],
    ['CAPS','a','s','d','f','g','h','j','k','l',';',"'",'ENTER'],
    ['SHIFT','z','x','c','v','b','n','m',',','.','/','SHIFT'],
    ['SPACE'],
]

SPECIAL = {'BKSP', 'TAB', 'CAPS', 'ENTER', 'SHIFT', 'SPACE'}
ORIGIN  = (20, 340)
KEY_W, KEY_H, PAD = 52, 50, 4

class Key:
    def __init__(self, label, x, y, w, h):
        self.label = label
        self.x, self.y, self.w, self.h = x, y, w, h
    def hit(self, px, py):
        return self.x <= px <= self.x + self.w and self.y <= py <= self.y + self.h

def build_keys():
    keys = []
    ox, oy = ORIGIN
    sw = {'BKSP': 108, 'TAB': 78, 'CAPS': 78, 'ENTER': 104, 'SHIFT': 78, 'SPACE': 416}
    for row_i, row in enumerate(ROWS):
        cx = ox
        for label in row:
            kw = sw.get(label, KEY_W)
            keys.append(Key(label, cx, oy + row_i * (KEY_H + PAD), kw, KEY_H))
            cx += kw + PAD
    return keys

class KeyboardController:
    def __init__(self):
        self.keys = build_keys()
        self.typed_text = ""
        self.shift_on = False
        self.caps_on = False
        self._last_key = 0.0
        self._pinching = False
        self.status = "Keyboard Active"

    def process(self, results, frame: np.ndarray):
        # 🔥 CRITICAL: Local import inside the method breaks the crash loop
        from modules.gesture_engine import LM

        self._draw_keyboard(frame)
        hand = results.primary
        if not hand: return

        # Get index tip landmarks
        ix, iy = hand.landmarks[LM.INDEX_TIP]
        hovered = next((k for k in self.keys if k.hit(ix, iy)), None)

        if hovered:
            self._draw_key(frame, hovered, highlight=True)
            # Pinch detection (Thumb to Index)
            if hand.distance(LM.THUMB_TIP, LM.INDEX_TIP) < (frame.shape[1] * 0.045):
                if not self._pinching and (time.time() - self._last_key > 0.35):
                    self._type_key(hovered.label)
                    self._last_key = time.time()
                self._pinching = True
            else:
                self._pinching = False

        self._draw_buffer(frame)

    def _type_key(self, label):
        if label == 'BKSP':
            pyautogui.press('backspace')
            self.typed_text = self.typed_text[:-1]
        elif label == 'SPACE':
            pyautogui.press('space')
            self.typed_text += ' '
        elif label == 'ENTER':
            pyautogui.press('enter')
            self.typed_text += '\n'
        elif label in ['SHIFT', 'CAPS']:
            if label == 'SHIFT': self.shift_on = not self.shift_on
            else: self.caps_on = not self.caps_on
        else:
            char = label.upper() if (self.shift_on or self.caps_on) else label.lower()
            pyautogui.write(char)
            self.typed_text += char
            self.shift_on = False 

    def _draw_keyboard(self, frame):
        for key in self.keys: self._draw_key(frame, key)

    def _draw_key(self, frame, key, highlight=False):
        color = (200, 200, 255) if highlight else (30, 30, 50)
        cv2.rectangle(frame, (key.x, key.y), (key.x+key.w, key.y+key.h), color, -1)
        cv2.rectangle(frame, (key.x, key.y), (key.x+key.w, key.y+key.h), (120, 180, 255), 1)
        label = key.label.upper() if (self.shift_on or self.caps_on) and len(key.label)==1 else key.label
        cv2.putText(frame, label, (key.x+5, key.y+30), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255,255,255), 1)

    def _draw_buffer(self, frame):
        cv2.rectangle(frame, (ORIGIN[0], ORIGIN[1]-50), (ORIGIN[0]+720, ORIGIN[1]-10), (20,20,40), -1)
        cv2.putText(frame, self.typed_text[-50:] + "|", (ORIGIN[0]+10, ORIGIN[1]-20), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1)