# """
# mode_manager.py
# ───────────────
# Manages the active control mode and delegates execution to the
# appropriate controller module.

# Modes (cycle with specific gestures or keyboard shortcuts):
#   0  MOUSE       — virtual mouse / cursor control
#   1  KEYBOARD    — virtual on-screen keyboard
#   2  VOLUME      — system volume control
#   3  BRIGHTNESS  — screen brightness control
#   4  SCROLL      — page scroll control
#   5  SCREENSHOT  — gesture-triggered screenshots
# """

# import cv2
# import time
# import numpy as np
# from enum import IntEnum

# print("1: Importing GestureEngine")
# from modules.gesture_engine    import GestureResults, LM
# print("2: Importing mouse_controller")
# from modules.mouse_controller  import MouseController
# print("3: Importing screenshot_controller")
# from modules.screenshot_controller import ScreenshotController
# print("5: Importing scroll_controller")
# from modules.scroll_controller import ScrollController
# print("6: Importing brightness_controller")
# from modules.brightness_controller import BrightnessController
# print("7: Importing volume_controller")
# from modules.volume_controller import VolumeController
# print("4: Importing keyboard_controller")
# from modules.keyboard_controller import KeyboardController



# class Mode(IntEnum):
#     MOUSE      = 0
#     KEYBOARD   = 1
#     VOLUME     = 2
#     BRIGHTNESS = 3
#     SCROLL     = 4
#     SCREENSHOT = 5


# MODE_NAMES = {
#     Mode.MOUSE:      "🖱  Virtual Mouse",
#     Mode.KEYBOARD:   "⌨  Virtual Keyboard",
#     Mode.VOLUME:     "🔊 Volume Control",
#     Mode.BRIGHTNESS: "☀  Brightness Control",
#     Mode.SCROLL:     "↕  Scroll Control",
#     Mode.SCREENSHOT: "📷 Screenshot Mode",
# }

# # Finger count → mode switch (hold for HOLD_FRAMES consecutive frames)
# # [T, I, M, R, P]  raised fingers count
# FINGER_COUNT_TO_MODE = {
#     1: Mode.MOUSE,
#     2: Mode.KEYBOARD,
#     3: Mode.VOLUME,
#     4: Mode.BRIGHTNESS,
#     5: Mode.SCROLL,         # open palm
# }

# HOLD_FRAMES   = 20   # consecutive frames needed to switch mode
# COOLDOWN_SEC  = 1.5  # seconds before another auto-switch is allowed


# class ModeManager:
#     def __init__(self, initial_mode: Mode = Mode.MOUSE):
# # # LOCAL IMPORTS
# #         from modules.gesture_engine    import GestureResults, LM
# #         from modules.mouse_controller  import MouseController
# #         from modules.keyboard_controller import KeyboardController
# #         from modules.volume_controller import VolumeController
# #         from modules.brightness_controller import BrightnessController
# #         from modules.scroll_controller import ScrollController
# #         from modules.screenshot_controller import ScreenshotController

#         self.mode     : Mode  = initial_mode
#         self.prev_mode: Mode  = initial_mode

#         self._controllers = {
#             Mode.MOUSE:      MouseController(),
#             Mode.KEYBOARD:   KeyboardController(),
#             Mode.VOLUME:     VolumeController(),
#             Mode.BRIGHTNESS: BrightnessController(),
#             Mode.SCROLL:     ScrollController(),
#             Mode.SCREENSHOT: ScreenshotController(),
#         }

#         self._hold_count    = 0
#         self._candidate     = None
#         self._last_switch   = 0.0
#         self.switch_flash   = 0   # frames remaining for switch UI flash

#     # ── Public API ────────────────────────────────────────────────

#     def update(self, results: GestureResults) -> None:
#         """
#         Detect mode-switch gesture: secondary hand (left) showing N fingers
#         held for HOLD_FRAMES consecutive frames.
#         """
#         if not results.secondary:
#             self._hold_count = 0
#             self._candidate  = None
#             return

#         n = results.secondary.count_fingers()
#         target = FINGER_COUNT_TO_MODE.get(n)

#         if target is None or target == self.mode:
#             self._hold_count = 0
#             self._candidate  = None
#             return

#         if target == self._candidate:
#             self._hold_count += 1
#         else:
#             self._candidate  = target
#             self._hold_count = 1

#         if self._hold_count >= HOLD_FRAMES:
#             now = time.time()
#             if now - self._last_switch > COOLDOWN_SEC:
#                 self._switch(target)
#                 self._hold_count = 0

#     def execute(self, results: GestureResults, frame: np.ndarray) -> None:
#         """Delegate processing to the active controller."""
#         ctrl = self._controllers[self.mode]
#         ctrl.process(results, frame)
#         if self.switch_flash > 0:
#             self.switch_flash -= 1

#     def force_mode(self, mode: Mode) -> None:
#         self._switch(mode)

#     @property
#     def name(self) -> str:
#         return MODE_NAMES[self.mode]

#     @property
#     def hold_progress(self) -> float:
#         """0.0–1.0 progress toward a mode switch (for UI ring)."""
#         return min(self._hold_count / HOLD_FRAMES, 1.0)

#     @property
#     def candidate_name(self) -> str:
#         if self._candidate is not None:
#             return MODE_NAMES[self._candidate]
#         return ""

#     def get_controller_status(self) -> str:
#         """Get status string from the active controller."""
#         ctrl = self._controllers[self.mode]
#         return getattr(ctrl, "status", "")

#     # ── Private ───────────────────────────────────────────────────

#     def _switch(self, mode: Mode) -> None:
#         self.prev_mode    = self.mode
#         self.mode         = mode
#         self._last_switch = time.time()
#         self.switch_flash = 45
#         print(f"[MODE] Switched to {MODE_NAMES[mode]}")



import cv2
import time
import numpy as np
from enum import IntEnum

class Mode(IntEnum):
    MOUSE      = 0
    KEYBOARD   = 1
    VOLUME     = 2
    BRIGHTNESS = 3
    SCROLL     = 4
    SCREENSHOT = 5

MODE_NAMES = {
    Mode.MOUSE:      "🖱  Virtual Mouse",
    Mode.KEYBOARD:   "⌨  Virtual Keyboard",
    Mode.VOLUME:     "🔊 Volume Control",
    Mode.BRIGHTNESS: "☀  Brightness Control",
    Mode.SCROLL:     "↕  Scroll Control",
    Mode.SCREENSHOT: "📷 Screenshot Mode",
}

FINGER_COUNT_TO_MODE = {1: Mode.MOUSE, 2: Mode.KEYBOARD, 3: Mode.VOLUME, 4: Mode.BRIGHTNESS, 5: Mode.SCROLL}
HOLD_FRAMES = 20
COOLDOWN_SEC = 1.5

class ModeManager:
    def __init__(self, initial_mode: Mode = Mode.MOUSE):
        # LOCAL IMPORTS - This prevents the circular crash
        from modules.mouse_controller import MouseController
        from modules.keyboard_controller import KeyboardController
        from modules.volume_controller import VolumeController
        from modules.brightness_controller import BrightnessController
        from modules.scroll_controller import ScrollController
        from modules.screenshot_controller import ScreenshotController

        self.mode = initial_mode
        self.prev_mode = initial_mode

        self._controllers = {
            Mode.MOUSE:      MouseController(),
            Mode.KEYBOARD:   KeyboardController(),
            Mode.VOLUME:     VolumeController(),
            Mode.BRIGHTNESS: BrightnessController(),
            Mode.SCROLL:     ScrollController(),
            Mode.SCREENSHOT: ScreenshotController(),
        }

        self._hold_count = 0
        self._candidate = None
        self._last_switch = 0.0
        self.switch_flash = 0

    def update(self, results) -> None:
        if not results.secondary:
            self._hold_count = 0
            self._candidate = None
            return

        n = results.secondary.count_fingers()
        target = FINGER_COUNT_TO_MODE.get(n)

        if target is None or target == self.mode:
            self._hold_count = 0
            self._candidate = None
            return

        if target == self._candidate:
            self._hold_count += 1
        else:
            self._candidate = target
            self._hold_count = 1

        if self._hold_count >= HOLD_FRAMES:
            now = time.time()
            if now - self._last_switch > COOLDOWN_SEC:
                self._switch(target)
                self._hold_count = 0

    def execute(self, results, frame: np.ndarray) -> None:
        ctrl = self._controllers[self.mode]
        ctrl.process(results, frame)
        if self.switch_flash > 0:
            self.switch_flash -= 1

    @property
    def name(self) -> str:
        return MODE_NAMES[self.mode]

    @property
    def hold_progress(self) -> float:
        return min(self._hold_count / HOLD_FRAMES, 1.0)

    @property
    def candidate_name(self) -> str:
        return MODE_NAMES[self._candidate] if self._candidate is not None else ""

    def get_controller_status(self) -> str:
        ctrl = self._controllers[self.mode]
        return getattr(ctrl, "status", "")

    def _switch(self, mode: Mode) -> None:
        self.prev_mode = self.mode
        self.mode = mode
        self._last_switch = time.time()
        self.switch_flash = 45
        print(f"[MODE] Switched to {MODE_NAMES[mode]}")
