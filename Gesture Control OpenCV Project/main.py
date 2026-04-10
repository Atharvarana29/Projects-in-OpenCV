"""
╔══════════════════════════════════════════════════════════════════╗
║   VIRTUAL MOUSE & KEYBOARD VIA HAND GESTURES                    ║
║   OpenCV + MediaPipe Real-Time Hand Tracking System             ║
║   Author: Resume Project | GitHub: your-username                ║
╚══════════════════════════════════════════════════════════════════╝

Features:
  • Virtual Mouse  — index finger moves cursor, pinch to click
  • Virtual Keyboard — on-screen keyboard typed via finger tap
  • Volume Control  — thumb-index distance maps to system volume
  • Brightness Control — two-hand gesture controls screen brightness
  • Scroll Control — two-finger swipe scrolls pages
  • Screenshot      — open-palm gesture captures screenshot
  • Mode Switcher   — raise specific fingers to switch modes
"""
print("1: Importing cv2/sys")
import cv2
import sys
import argparse
print("2: Importing GestureEngine")
from modules.gesture_engine import GestureEngine
print("3: Importing UIOverlay")
from modules.ui_overlay   import UIOverlay
print("4: Importing ModeManager")
from modules.mode_manager import ModeManager
print("5: All imports successful")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Virtual Mouse & Keyboard via Hand Gestures"
    )
    parser.add_argument("--camera",    type=int,   default=0,
                        help="Camera index (default: 0)")
    parser.add_argument("--width",     type=int,   default=1280,
                        help="Camera capture width")
    parser.add_argument("--height",    type=int,   default=720,
                        help="Camera capture height")
    parser.add_argument("--smooth",    type=float, default=0.8,
                        help="Cursor smoothing factor 0–1 (default: 0.5)")
    parser.add_argument("--debug",     action="store_true",
                        help="Show landmark debug overlay")
    return parser.parse_args()


def main():
    print("🔥 MAIN STARTED")
    args = parse_args()
    print(f"[INFO] Opening camera {args.camera}")

    print(__doc__)
    print(f"[INFO] Opening camera {args.camera} at {args.width}×{args.height}")

    # cap = cv2.VideoCapture(0) #args.camera
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    # cap.set(cv2.CAP_PROP_FPS, 30)

    if not cap.isOpened():
        print("[RETRY] DSHOW failed, trying default backend...")
        cap = cv2.VideoCapture(0)

    # WARM UP THE SENSOR
    print("[INFO] Warming up camera...")
    for _ in range(10):
        cap.read()
        # time.sleep(0.01)

    if not cap.isOpened():
        print("[ERROR] Camera failed to open with CAP_DSHOW. Trying default...")
        cap = cv2.VideoCapture(0)
    # cap.set(cv2.CAP_PROP_FRAME_WIDTH,  args.width)
    # cap.set(cv2.CAP_PROP_FRAME_HEIGHT, args.height)

    if not cap.isOpened():
        print("[ERROR] Cannot open camera. Exiting.")
        sys.exit(1)

    print("A: Initializing GestureEngine...")
    gesture_engine = GestureEngine(
        smooth_factor=args.smooth,
        debug=args.debug
    )
    print("B: Initializing ModeManager...")
    mode_manager  = ModeManager()
    print("C: Initializing UIOverlay...")
    ui_overlay    = UIOverlay(cam_w=args.width, cam_h=args.height)

    print("[INFO] System ready.")
    print("[INFO] System ready. Press 'q' to quit, 'h' for help.\n")

    # Clear the buffer
    for _ in range(5):
        cap.read()
    
    print("🔥 ENTERING DATA LOOP")
    window_name = "Gesture Control System"
    cv2.namedWindow(window_name, cv2.WINDOW_AUTOSIZE)

    # while True:
    #     ret, frame = cap.read()
    #     # if not ret:
    #     #     print("[DEBUG] Failed to grab frame - is the camera being used by another app?")
    #     #     break
        
    #     # print("Frame grabbed!") # Add this temporary line
    
    #     if not ret or frame is None:
    #         # print("[DEBUG] Received empty frame from camera. Skipping...")
    #         # continue # Instead of break, try to wait for the next frame

    #     # frame = cv2.flip(frame, 1)          # mirror for natural feel

    #         continue 

    #     # Only flip if the frame actually exists
    #     try:
    #         frame = cv2.flip(frame, 1)
    #         results = gesture_engine.process(frame)
            
    #         # Delegate execution
    #         mode_manager.update(results)
    #         mode_manager.execute(results, frame)
            
    #         # UI
    #         frame = ui_overlay.draw(frame, results, mode_manager)

    #         # Only show window if everything processed correctly
    #         if not window_created:
    #             cv2.namedWindow("Gesture Control System", cv2.WINDOW_AUTOSIZE)
    #             window_created = True

    #         cv2.imshow("Gesture Control System", frame)
    #     except Exception as e:
    #         print(f"Flip Error: {e}")
    #         continue

    #     if cv2.waitKey(1) & 0xFF == ord('q'):
    #         break

    # while True:
    #     ret, frame = cap.read()
    #     if not ret or frame is None:
    #         continue

    #     frame = cv2.flip(frame, 1)

    #     # Core pipeline
    #     results = gesture_engine.process(frame)
    #     mode_manager.update(results)
    #     mode_manager.execute(results, frame)

    #     # Draw UI
    #     frame = ui_overlay.draw(frame, results, mode_manager)

    #     # Use the variable name to ensure it stays in the same window
    #     cv2.imshow(window_name, frame)

    #     if cv2.waitKey(1) & 0xFF == ord('q'):
    #         break

    #     # ── Core pipeline ─────────────────────────────────────────
    #     results   = gesture_engine.process(frame)
    #     mode_manager.update(results)
    #     mode_manager.execute(results, frame)

    #     # ── Draw UI ───────────────────────────────────────────────
    #     frame = ui_overlay.draw(frame, results, mode_manager)

    #     cv2.imshow("Gesture Control System  |  Press Q to quit", frame)

    #     key = cv2.waitKey(1) & 0xFF
    #     if key == ord('q'):
    #         break
    #     elif key == ord('h'):
    #         ui_overlay.toggle_help()
    #     elif key == ord('d'):
    #         gesture_engine.debug = not gesture_engine.debug

    # cap.release()
    # cv2.destroyAllWindows()

    while True:
        ret, frame = cap.read()
        if not ret or frame is None:
            continue

        try:
            # 1. Flip
            frame = cv2.flip(frame, 1)

            # 2. Gesture Pipeline
            results = gesture_engine.process(frame)
            
            # 3. Manager/Logic
            mode_manager.update(results)
            mode_manager.execute(results, frame)

            # 4. Draw Overlay
            frame = ui_overlay.draw(frame, results, mode_manager)

            # 5. Display
            cv2.imshow(window_name, frame)

        except Exception as e:
            print(f"[RUNTIME ERROR] {e}")

        # Check for keys
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('h'):
            ui_overlay.toggle_help()
        elif key == ord('d'):
            gesture_engine.debug = not gesture_engine.debug

    cap.release()
    cv2.destroyAllWindows()
    print("[INFO] Session ended.")


if __name__ == "__main__":
    print("🔥 CALLING MAIN")
    main()
