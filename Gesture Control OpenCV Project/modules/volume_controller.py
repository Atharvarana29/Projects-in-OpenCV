"""
volume_controller.py
────────────────────
Maps the Euclidean distance between thumb tip and index tip to
system audio volume (0–100 %).

Cross-platform:
  • Linux  : pulsectl (PulseAudio) or pactl subprocess fallback
  • macOS  : osascript
  • Windows: pycaw
"""

# import cv2
# import math
# import platform
# import subprocess
# import numpy as np
# from modules.gesture_engine import GestureResults, LM

# SYSTEM = platform.system()
# print("SYSTEM:", SYSTEM)

# def _set_volume_windows(pct: int) -> None:
#     try:
#         from ctypes import cast, POINTER
#         import numpy as np

#         # 🔥 Import INSIDE function (safe)
#         import comtypes
#         from comtypes import CLSCTX_ALL
#         from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

#         devices = AudioUtilities.GetSpeakers()
#         interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
#         volume = cast(interface, POINTER(IAudioEndpointVolume))

#         vol_db = np.interp(pct, [0, 100], [-65.25, 0.0])
#         volume.SetMasterVolumeLevel(vol_db, None)

#     except Exception as e:
#         print("Volume control error:", e)


# def _set_volume_mac(pct: int) -> None:
#     subprocess.run(
#         ["osascript", "-e", f"set volume output volume {pct}"],
#         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
#     )


# def _set_volume_windows(pct: int) -> None:
#     try:
#         from ctypes import cast, POINTER
#         from comtypes import CLSCTX_ALL
#         from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
#         devices = AudioUtilities.GetSpeakers()
#         interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
#         volume = cast(interface, POINTER(IAudioEndpointVolume))
#         vol_db = np.interp(pct, [0, 100], [-65.25, 0.0])
#         volume.SetMasterVolumeLevel(vol_db, None)
#     except Exception:
#         pass


# def _set_volume_linux(pct: int):
#     pass

# def set_system_volume(pct: int) -> None:
#     pct = int(np.clip(pct, 0, 100))
#     if SYSTEM == "Linux":
#         # _set_volume_linux(pct)
#         pass
#     elif SYSTEM == "Darwin":
#         _set_volume_mac(pct)
#     if SYSTEM == "Windows":
#         _set_volume_windows(pct)


# Distance range (pixels) that maps 0 → 100 % volume
DIST_MIN = 30
DIST_MAX = 220

import cv2
import numpy as np
import platform
from modules.gesture_engine import GestureResults, LM

SYSTEM = platform.system()

def set_system_volume(pct: int) -> None:
    pct = int(np.clip(pct, 0, 100))
    
    if SYSTEM == "Windows":
        try:
            from ctypes import cast, POINTER
            from comtypes import CLSCTX_ALL
            from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
            
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume = cast(interface, POINTER(IAudioEndpointVolume))
            vol_db = np.interp(pct, [0, 100], [-65.25, 0.0])
            volume.SetMasterVolumeLevel(vol_db, None)
        except Exception as e:
            print(f"Windows Volume Error: {e}")

    elif SYSTEM == "Darwin": # macOS
        import subprocess
        subprocess.run(["osascript", "-e", f"set volume output volume {pct}"], 
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

# ... rest of your VolumeController class ...

class VolumeController:
    def __init__(self):
        self._volume    = 50
        self._bar_pct   = 50.0
        self.status     = "Volume Control | Spread fingers to adjust"

    def process(self, results: GestureResults, frame: np.ndarray) -> None:
        hand = results.primary
        if hand is None:
            self.status = "No hand detected"
            return

        dist = hand.distance(LM.THUMB_TIP, LM.INDEX_TIP)
        mid  = hand.midpoint(LM.THUMB_TIP, LM.INDEX_TIP)

        # Smooth bar display
        self._bar_pct = float(
            np.interp(dist, [DIST_MIN, DIST_MAX], [0.0, 100.0])
        )
        target_vol = int(self._bar_pct)

        if abs(target_vol - self._volume) >= 2:      # threshold to reduce calls
            self._volume = target_vol
            set_system_volume(self._volume)

        self.status = f"Volume: {self._volume}%"

        # ── Visual feedback ────────────────────────────────────────
        tx, ty = hand.landmarks[LM.THUMB_TIP]
        ix, iy = hand.landmarks[LM.INDEX_TIP]
        cv2.line(frame, (tx, ty), (ix, iy), (100, 200, 255), 3)
        cv2.circle(frame, (tx, ty), 10, (0, 200, 255), -1)
        cv2.circle(frame, (ix, iy), 10, (0, 200, 255), -1)
        cv2.circle(frame, mid, 6, (255, 255, 255), -1)

        self._draw_bar(frame)

    def _draw_bar(self, frame: np.ndarray) -> None:
        h = frame.shape[0]
        bx, by_top, bw, bh = 60, 150, 30, 300
        by_bot = by_top + bh

        # Background
        cv2.rectangle(frame, (bx, by_top), (bx + bw, by_bot), (40, 40, 40), -1)

        # Fill level
        fill_h  = int(bh * self._bar_pct / 100.0)
        fill_y  = by_bot - fill_h
        color   = (0, int(200 * self._bar_pct / 100), int(255 * (1 - self._bar_pct / 100)))
        cv2.rectangle(frame, (bx, fill_y), (bx + bw, by_bot), color, -1)

        # Border + label
        cv2.rectangle(frame, (bx, by_top), (bx + bw, by_bot), (120, 180, 255), 2)
        cv2.putText(frame, f"{int(self._bar_pct)}%",
                    (bx - 5, by_bot + 25), cv2.FONT_HERSHEY_SIMPLEX,
                    0.6, (200, 230, 255), 1, cv2.LINE_AA)
        cv2.putText(frame, "VOL",
                    (bx + 2, by_top - 10), cv2.FONT_HERSHEY_SIMPLEX,
                    0.5, (200, 230, 255), 1, cv2.LINE_AA)
