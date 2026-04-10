"""
gesture_engine.py
─────────────────
MediaPipe-based hand tracking pipeline.
Detects landmarks, classifies finger states, recognises high-level
gestures, and exposes a clean GestureResults dataclass to the rest
of the application.
"""

import cv2
import math
import numpy as np
import mediapipe as mp
from dataclasses import dataclass, field
from typing import Optional, List, Tuple, Dict


# ── Landmark indices (MediaPipe 21-point hand model) ──────────────
class LM:
    WRIST           = 0
    THUMB_CMC       = 1;  THUMB_MCP  = 2;  THUMB_IP   = 3;  THUMB_TIP  = 4
    INDEX_MCP       = 5;  INDEX_PIP  = 6;  INDEX_DIP  = 7;  INDEX_TIP  = 8
    MIDDLE_MCP      = 9;  MIDDLE_PIP = 10; MIDDLE_DIP = 11; MIDDLE_TIP = 12
    RING_MCP        = 13; RING_PIP   = 14; RING_DIP   = 15; RING_TIP   = 16
    PINKY_MCP       = 17; PINKY_PIP  = 18; PINKY_DIP  = 19; PINKY_TIP  = 20

    TIPS   = [THUMB_TIP, INDEX_TIP, MIDDLE_TIP, RING_TIP, PINKY_TIP]
    PIPS   = [THUMB_IP,  INDEX_PIP, MIDDLE_PIP, RING_PIP, PINKY_PIP]


@dataclass
class Hand:
    """Processed data for a single detected hand."""
    label: str                              # "Left" | "Right"
    landmarks: List[Tuple[int, int]]        # pixel (x, y) per landmark
    raw_lm: object                          # original mediapipe landmark obj
    fingers_up: List[bool] = field(default_factory=lambda: [False]*5)
    # index 0=Thumb, 1=Index, 2=Middle, 3=Ring, 4=Pinky

    # Convenience properties
    @property
    def index_tip(self)  -> Tuple[int,int]: return self.landmarks[LM.INDEX_TIP]
    @property
    def middle_tip(self) -> Tuple[int,int]: return self.landmarks[LM.MIDDLE_TIP]
    @property
    def thumb_tip(self)  -> Tuple[int,int]: return self.landmarks[LM.THUMB_TIP]
    @property
    def wrist(self)      -> Tuple[int,int]: return self.landmarks[LM.WRIST]

    def distance(self, a: int, b: int) -> float:
        """Euclidean pixel distance between two landmarks."""
        ax, ay = self.landmarks[a]
        bx, by = self.landmarks[b]
        return math.hypot(ax - bx, ay - by)

    def midpoint(self, a: int, b: int) -> Tuple[int,int]:
        ax, ay = self.landmarks[a]
        bx, by = self.landmarks[b]
        return ((ax+bx)//2, (ay+by)//2)

    def count_fingers(self) -> int:
        return sum(self.fingers_up)


@dataclass
class GestureResults:
    """Output bundle from GestureEngine.process()."""
    hands: List[Hand]           = field(default_factory=list)
    fps:   float                = 0.0
    # Named gesture flags (set by engine)
    gesture_label: str          = "none"   # dominant gesture name
    # Per-hand convenience (None if hand absent)
    primary:   Optional[Hand]   = None     # largest / most stable hand
    secondary: Optional[Hand]   = None

    @property
    def hand_count(self) -> int:
        return len(self.hands)


class GestureEngine:
    """
    Wraps MediaPipe Hands, converts landmarks to pixel coords,
    classifies finger extension states, and identifies named gestures.
    """

    # Pinch distance threshold (pixels at 1280px width; scales with frame)
    PINCH_THRESHOLD_RATIO = 0.045

    # Named gestures → finger pattern [T, I, M, R, P]
    GESTURE_PATTERNS: Dict[str, List[Optional[bool]]] = {
        "point":       [None, True,  False, False, False],
        "peace":       [None, True,  True,  False, False],
        "ok":          [None, False, False, False, False],   # thumb-index pinch
        "open_palm":   [True, True,  True,  True,  True ],
        "fist":        [False,False, False, False, False],
        "thumbs_up":   [True, False, False, False, False],
        "call_me":     [True, False, False, False, True ],
        "rock":        [False,True,  False, False, True ],
        "three":       [None, True,  True,  True,  False],
        "four":        [None, True,  True,  True,  True ],
    }

    # def __init__(self, smooth_factor: float = 0.5, debug: bool = False,
    #              max_hands: int = 2):
    #     self.smooth_factor = smooth_factor
    #     self.debug         = debug

    #     self._mp_hands  = mp.solutions.hands
    #     self._mp_draw   = mp.solutions.drawing_utils
    #     self._mp_styles = mp.solutions.drawing_styles
    #     self._hands     = self._mp_hands.Hands(
    #         static_image_mode       = False,
    #         max_num_hands           = max_hands,
    #         min_detection_confidence= 0.75,
    #         min_tracking_confidence = 0.65,
    #     )

    #     # FPS tracking
    #     self._prev_tick = cv2.getTickCount()

    #     # Smoothed cursor (for virtual mouse)
    #     self._smooth_x: float = 0.0
    #     self._smooth_y: float = 0.0

    # def __init__(self, smooth_factor: float = 0.5, debug: bool = False,
    #              max_hands: int = 2):
    #     self.smooth_factor = smooth_factor
    #     self.debug         = debug

    #     self._mp_hands  = mp.solutions.hands
    #     self._mp_draw   = mp.solutions.drawing_utils
    #     self._mp_styles = mp.solutions.drawing_styles
        
    #     # LOWER THESE VALUES: High confidence + High complexity = Crash
    #     self._hands     = self._mp_hands.Hands(
    #         static_image_mode       = False,
    #         max_num_hands           = max_hands,
    #         model_complexity        = 0,     # 0 is Lite (fastest), 1 is Full. Set to 0.
    #         min_detection_confidence= 0.5,   # Lowered from 0.75
    #         min_tracking_confidence = 0.5,   # Lowered from 0.65
    #     )


    def __init__(self, smooth_factor: float = 0.5, debug: bool = False, max_hands: int = 2):
        self.smooth_factor = smooth_factor
        self.debug         = debug
        self.max_hands     = max_hands

        # Leave these as None for now to avoid the Step A crash
        self._hands = None 
        self._mp_hands = None
        self._mp_draw = None
        self._mp_styles = None

        self._prev_tick = cv2.getTickCount()
        self._smooth_x = 0.0
        self._smooth_y = 0.0

    # def _initialize_mediapipe(self):
    #     """Only runs once when the first frame is processed."""
    #     if self._hands is None:
    #         print("[INFO] Starting MediaPipe Engine...")
    #         import mediapipe as mp


    #         self._mp_hands = mp.solutions.hands
    #         self._mp_draw  = mp.solutions.drawing_utils
    #         self._mp_styles = mp.solutions.drawing_styles
    #         # self._hands = self._mp_hands.Hands(
    #         #     static_image_mode=False,
    #         #     max_num_hands=self.max_hands,
    #         #     model_complexity=0,
    #         #     min_detection_confidence=0.5,
    #         #     min_tracking_confidence=0.5
    #         # )
    #         # Use the most basic settings to ensure it boots
    #         # self._hands = self._mp_hands.Hands(
    #         #     static_image_mode=True,
    #         #     max_num_hands=1,         # Start with 1 to save memory
    #         #     model_complexity=0,      # Lite model
    #         #     min_detection_confidence=0.5,
    #         #     min_tracking_confidence=0.5
    #         # )
    #         # print("[INFO] MediaPipe Engine Started Successfully.")

    #         # The most basic, "safe mode" initialization possible
    #         try:
    #             self._hands = self._mp_hands.Hands(
    #                 static_image_mode=False, 
    #                 max_num_hands=1,
    #                 min_detection_confidence=0.5,
    #                 min_tracking_confidence=0.5
    #             )
    #             print("[INFO] MediaPipe Engine Started Successfully.")
    #         except Exception as e:
    #             print(f"CRITICAL ERROR: MediaPipe could not start: {e}")
    #             # sys.exit(1)
    #             exit(1)




    # def _initialize_mediapipe(self):
    #     """Only runs once when the first frame is processed."""
    #     if self._hands is None:
    #         print("[INFO] Starting MediaPipe Engine...")
    #         try:
    #             import mediapipe as mp
    #             import os
                
    #             # Force CPU and hide logs that might be causing terminal buffer issues
    #             os.environ['CUDA_VISIBLE_DEVICES'] = '-1' 
    #             os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

    #             self._mp_hands = mp.solutions.hands
    #             self._mp_draw  = mp.solutions.drawing_utils
    #             self._mp_styles = mp.solutions.drawing_styles
                
    #             # STRICTEST SETTINGS FOR STABILITY
    #             self._hands = self._mp_hands.Hands(
    #                 static_image_mode=True,        # Use static mode to avoid tracking thread crashes
    #                 max_num_hands=1,
    #                 model_complexity=0,            # Lite model
    #                 min_detection_confidence=0.5,
    #                 min_tracking_confidence=0.5
    #             )
    #             print("[INFO] MediaPipe Engine Started Successfully.")
    #         except Exception as e:
    #             print(f"[CRITICAL] MediaPipe failed to load: {e}")
    #             self._hands = False # Flag it as failed

    def _initialize_mediapipe(self):
        if self._hands is None or self._hands is False:
            print("[INFO] Starting MediaPipe Engine...")
            try:
                # Use absolute import to bypass local file shadowing
                import mediapipe as mp
                # from mediapipe.python.solutions import hands as mp_hands
                # from mediapipe.python.solutions import drawing_utils as mp_draw
                # from mediapipe.python.solutions import drawing_styles as mp_styles

                # self._mp_hands = mp_hands
                # self._mp_draw = mp_draw
                # self._mp_styles = mp_styles
                
                # self._hands = self._mp_hands.Hands(
                #     static_image_mode=False,
                #     max_num_hands=1,
                #     model_complexity=0,
                #     min_detection_confidence=0.5,
                #     min_tracking_confidence=0.5
                # )

                # Use the standard access method
                self._mp_hands = mp.solutions.hands
                self._mp_draw  = mp.solutions.drawing_utils
                self._mp_styles = mp.solutions.drawing_styles
                
                self._hands = self._mp_hands.Hands(
                    static_image_mode=False,  #True is much slower because it re-detects the hand from scratch every frame.
                    max_num_hands=2, #both the hands 
                    model_complexity=0,
                    min_detection_confidence=0.5,
                    min_tracking_confidence=0.5
                )

                print("[INFO] MediaPipe Engine Started Successfully.")
            except Exception as e:
                print(f"[CRITICAL] MediaPipe failed to load: {e}")
                # self._hands = False
                # Print the actual path mediapipe is loading from to find conflicts
                import mediapipe
                print(f"MediaPipe location: {mediapipe.__file__}")
                self._hands = False

    # ── Public API ────────────────────────────────────────────────

    def process(self, frame: np.ndarray) -> GestureResults:
        """
        Run the full pipeline on a BGR frame.
        Returns a GestureResults object.
        """
        # Start MediaPipe here instead of __init__
        self._initialize_mediapipe()

        # 1. Safety Check: Ensure frame is not empty
        if frame is None or frame.size == 0:
            return GestureResults(fps=self._calc_fps())
        
        # 2. Force Convert to 8-bit (Just in case)
        if frame.dtype != np.uint8:
            frame = frame.astype(np.uint8)

        h, w = frame.shape[:2]

        # 3. Convert to RGB
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        rgb.flags.writeable = False

        # print("[DEBUG] Attempting MediaPipe Process...") # Checkpoint
        try:
            mp_results = self._hands.process(rgb)
        except Exception as e:
            print(f"[CRITICAL] MediaPipe failed during processing: {e}")
            return GestureResults(fps=self._calc_fps())
        
        # print("[DEBUG] MediaPipe Process Success!")
        rgb.flags.writeable = True
        
        # rgb  = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        # rgb.flags.writeable = False
        # mp_results = self._hands.process(rgb)
        # rgb.flags.writeable = True

        results = GestureResults(fps=self._calc_fps())
        if not mp_results.multi_hand_landmarks:
            return results

        for hand_lm, hand_class in zip(
            mp_results.multi_hand_landmarks,
            mp_results.multi_handedness
        ):
            label = hand_class.classification[0].label  # "Left"/"Right"
            landmarks = [
                (int(lm.x * w), int(lm.y * h))
                for lm in hand_lm.landmark
            ]
            hand = Hand(label=label, landmarks=landmarks, raw_lm=hand_lm)
            hand.fingers_up = self._classify_fingers(hand, w)
            results.hands.append(hand)

            if self.debug:
                self._draw_landmarks(frame, hand_lm)

        # Assign primary (right-dominant → first right, else first)
        rights = [h for h in results.hands if h.label == "Right"]
        lefts  = [h for h in results.hands if h.label == "Left"]
        results.primary   = (rights or lefts or [None])[0]
        results.secondary = (lefts  if rights else rights or [None])[0]

        # Gesture classification
        if results.primary:
            results.gesture_label = self._classify_gesture(
                results.primary, w
            )

        return results

    def smooth_cursor(self, x: int, y: int) -> Tuple[int, int]:
        """Exponential moving average on cursor position."""
        a = 1.0 - self.smooth_factor
        self._smooth_x = a * x + self.smooth_factor * self._smooth_x
        self._smooth_y = a * y + self.smooth_factor * self._smooth_y
        return int(self._smooth_x), int(self._smooth_y)

    # ── Private helpers ───────────────────────────────────────────

    def _classify_fingers(self, hand: Hand, frame_w: int) -> List[bool]:
        """
        Return [thumb, index, middle, ring, pinky] extension booleans.
        Uses tip-vs-PIP comparison; thumb uses horizontal axis for
        robustness against hand orientation.
        """
        lm   = hand.landmarks
        up   = [False] * 5

        # Thumb: compare tip X to IP joint X (left/right flipped per label)
        if hand.label == "Right":
            up[0] = lm[LM.THUMB_TIP][0] < lm[LM.THUMB_IP][0]
        else:
            up[0] = lm[LM.THUMB_TIP][0] > lm[LM.THUMB_IP][0]

        # Fingers: tip Y < PIP Y  (higher on frame = smaller Y = extended)
        for i, (tip, pip) in enumerate(zip(
            [LM.INDEX_TIP, LM.MIDDLE_TIP, LM.RING_TIP, LM.PINKY_TIP],
            [LM.INDEX_PIP, LM.MIDDLE_PIP, LM.RING_PIP, LM.PINKY_PIP]
        ), start=1):
            up[i] = lm[tip][1] < lm[pip][1]

        return up

    def _classify_gesture(self, hand: Hand, frame_w: int) -> str:
        """
        Match finger pattern; check pinch separately.
        """
        # Pinch check
        pinch_thresh = frame_w * self.PINCH_THRESHOLD_RATIO
        if hand.distance(LM.THUMB_TIP, LM.INDEX_TIP) < pinch_thresh:
            return "pinch"

        # Pattern match
        for name, pattern in self.GESTURE_PATTERNS.items():
            match = True
            for expected, actual in zip(pattern, hand.fingers_up):
                if expected is not None and expected != actual:
                    match = False
                    break
            if match:
                return name

        return "unknown"

    def _draw_landmarks(self, frame: np.ndarray, hand_lm) -> None:
        self._mp_draw.draw_landmarks(
            frame, hand_lm,
            self._mp_hands.HAND_CONNECTIONS,
            self._mp_styles.get_default_hand_landmarks_style(),
            self._mp_styles.get_default_hand_connections_style(),
        )

    def _calc_fps(self) -> float:
        tick       = cv2.getTickCount()
        freq       = cv2.getTickFrequency()
        fps        = freq / (tick - self._prev_tick)
        self._prev_tick = tick
        return fps
