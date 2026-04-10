import mediapipe as mp
import cv2
print("Testing MediaPipe...")
mp_hands = mp.solutions.hands
hands = mp_hands.Hands()
print("MediaPipe Initialized Successfully!")