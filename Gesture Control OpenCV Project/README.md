# 🖐 Virtual Mouse & Keyboard via Hand Gestures

> **OpenCV + MediaPipe real-time hand tracking system** that lets you control
> your computer entirely through mid-air gestures — no hardware required beyond
> a standard webcam.

---

## ✨ Features

| Mode | Gesture | Action |
|------|---------|--------|
| **Virtual Mouse** | Index finger only | Move cursor |
| | Thumb + Index pinch | Left click |
| | Double-pinch (< 400 ms) | Double click |
| | Index + Middle raised | Right click |
| | Fist | Click & drag |
| **Virtual Keyboard** | Hover index, pinch | Type key |
| | SHIFT / CAPS keys | Toggle case |
| **Volume Control** | Spread thumb ↔ index | Adjust volume 0–100 % |
| **Brightness** | Open palm up / down | Adjust brightness |
| **Scroll** | Index + Middle, swipe | Scroll page |
| **Screenshot** | Open palm, hold 1 s | Capture & save screenshot |

---

## 🏗 Project Structure

```
gesture_control/
├── main.py                         # Entry point & argument parsing
├── requirements.txt
├── README.md
└── modules/
    ├── gesture_engine.py           # MediaPipe hand tracking + gesture recognition
    ├── mode_manager.py             # Mode switching logic
    ├── mouse_controller.py         # Virtual mouse
    ├── keyboard_controller.py      # On-screen QWERTY keyboard
    ├── volume_controller.py        # System audio volume
    ├── brightness_controller.py    # Screen brightness
    ├── scroll_controller.py        # Page scrolling
    ├── screenshot_controller.py    # Screenshot capture
    └── ui_overlay.py               # HUD, FPS, help screen
```

---

## 🚀 Quick Start

### 1. Clone / Download
```bash
git clone https://github.com/your-username/gesture-control.git
cd gesture-control
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

> **Linux users**: install `brightnessctl` for brightness control:
> ```bash
> sudo apt install brightnessctl
> ```
>
> **macOS users**: install `brightness` for brightness control:
> ```bash
> brew install brightness
> ```
>
> **Windows users**: uncomment `pycaw` and `wmi` in `requirements.txt`.

### 3. Run
```bash
python main.py
```

### Optional flags
```
--camera  INT    Camera device index (default: 0)
--width   INT    Capture width  (default: 1280)
--height  INT    Capture height (default: 720)
--smooth  FLOAT  Cursor smoothing 0–1 (default: 0.5)
--debug          Show raw landmark numbers
```

---

## 🎮 Mode Switching

Hold up fingers on your **left hand** to pre-select a mode.
Keep them raised for ~20 frames (≈ 0.7 s) to confirm the switch.

| Left-hand fingers | Mode |
|:-----------------:|------|
| 1 | Virtual Mouse |
| 2 | Virtual Keyboard |
| 3 | Volume Control |
| 4 | Brightness Control |
| 5 (open palm) | Scroll |

A progress ring appears at the left edge of the screen during the hold.
A flash banner confirms the switch.

---

## ⌨ Keyboard Shortcuts (within the app window)

| Key | Action |
|-----|--------|
| `Q` | Quit |
| `H` | Toggle help overlay |
| `D` | Toggle debug landmarks |

---

## 🧠 How It Works

```
Webcam frame
     │
     ▼
  cv2.flip()   ← mirror for natural feel
     │
     ▼
MediaPipe Hands  ←── GestureEngine.process()
  • 21 landmarks per hand (pixel coords)
  • Finger extension classification (tip Y vs PIP Y)
  • Named gesture matching (pattern table)
  • Pinch distance threshold check
     │
     ▼
ModeManager.update()
  • Secondary hand finger count → mode-switch candidate
  • Hold-frame counter + cooldown
     │
     ▼
ModeManager.execute()   ──►  Active Controller
  MouseController          pyautogui move / click
  KeyboardController       on-screen keys + pyautogui.typewrite
  VolumeController         pulsectl / pactl / osascript / pycaw
  BrightnessController     brightnessctl / osascript / wmi
  ScrollController         pyautogui.scroll / hscroll
  ScreenshotController     pyautogui.screenshot → PNG
     │
     ▼
UIOverlay.draw()
  • Skeleton landmarks
  • HUD panels (mode, status, FPS)
  • Gesture badge
  • Mode-switch flash + progress ring
  • Help screen
     │
     ▼
cv2.imshow()
```

---

## 📦 Dependencies

| Library | Purpose |
|---------|---------|
| `opencv-python` | Frame capture, drawing, display |
| `mediapipe` | 21-point hand landmark detection |
| `pyautogui` | Mouse, keyboard, screenshot automation |
| `numpy` | Coordinate maths, interpolation |
| `pulsectl` *(Linux)* | PulseAudio volume control |
| `pycaw` *(Windows)* | Windows Core Audio volume |

---

## 🔧 Extending the Project

- **Add a gesture**: extend `GestureEngine.GESTURE_PATTERNS` dict.
- **Add a mode**: subclass a new controller, add it to `ModeManager._controllers`.
- **Improve smoothing**: replace EMA in `MouseController` with a Kalman filter.
- **Multi-screen support**: map active zone to a specific monitor via `pyautogui`.

---

## 📄 License

MIT — free to use, modify, and distribute.

---

*Built with ❤ using OpenCV 4 · MediaPipe 0.10 · Python 3.10+*
