import cv2
import math
import json
import win32api
import win32con
import mediapipe as mp

### READING FROM CONFIG
with open("config.json", "r") as file:
    options = json.load(file)

### INIT
mouse_down = False
right_mouse_down = False

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    max_num_hands=1,
    model_complexity=options["model"]["complexity"],
    min_detection_confidence=options["model"]["minimum detection confidence"],
    min_tracking_confidence=options["model"]["minimum tracking confidence"]
)

mp_drawing = mp.solutions.drawing_utils

capture = cv2.VideoCapture(0)
capture.set(cv2.CAP_PROP_FRAME_WIDTH, options["camera"]["width"])
capture.set(cv2.CAP_PROP_FRAME_HEIGHT, options["camera"]["height"])
capture.set(cv2.CAP_PROP_FPS, options["camera"]["frameRate"])

### FUNCTIONS
def get_hand_size(landmarks):
    wrist = landmarks.landmark[0]
    middle_mcp = landmarks.landmark[9]

    # Convert normalized coordinates to camera pixel coordinates
    h, w = frame.shape[:2]
    wrist_x, wrist_y = int(wrist.x * w), int(wrist.y * h)
    middle_x, middle_y = int(middle_mcp.x * w), int(middle_mcp.y * h)

    return math.hypot(middle_x - wrist_x, middle_y - wrist_y)

def update_cursor(landmarks):
    global mouse_down, right_mouse_down

    thumb = landmarks.landmark[4]
    index = landmarks.landmark[8]
    middle = landmarks.landmark[12]

    # Convert normalized coordinates to camera pixel coordinates
    h, w = frame.shape[:2]
    thumb_x, thumb_y = int(thumb.x * w), int(thumb.y * h)
    index_x, index_y = int(index.x * w), int(index.y * h)
    middle_x, middle_y = int(middle.x * w), int(middle.y * h)

    # Convert camera pixel coordinates to screen pixel coordinates
    screen_w = win32api.GetSystemMetrics(0)
    screen_h = win32api.GetSystemMetrics(1)
    cursor_x, cursor_y = (w - thumb_x)*screen_w//w, thumb_y*screen_h//h

    win32api.SetCursorPos((cursor_x, cursor_y))
    # Distances
    index_thumb_dist = math.hypot(index_x - thumb_x, index_y - thumb_y)
    middle_thumb_dist = math.hypot(middle_x - thumb_x, middle_y - thumb_y)

    pinch_threshold = get_hand_size(landmarks) * 0.3

    # ---------------- LEFT CLICK (thumb + index) ----------------
    if index_thumb_dist < pinch_threshold:
        if not mouse_down:
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0)
            mouse_down = True
    elif middle_thumb_dist < pinch_threshold:
        if not right_mouse_down:
            win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTDOWN, 0, 0)
            right_mouse_down = True
    else:
        if mouse_down:
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0)
            mouse_down = False
        if right_mouse_down:
            win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTUP, 0, 0)
            right_mouse_down = False

def is_stop_requested():
    tab = win32api.GetAsyncKeyState(win32con.VK_TAB)
    esc = win32api.GetAsyncKeyState(win32con.VK_ESCAPE)
    return (tab & 0x8000) and (esc & 1)

### VIDEO STREAM PROCESSING
while capture.isOpened():
    ret, frame = capture.read()
    if not ret:
        break

    image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    image.flags.writeable = False
    results = hands.process(image)

    if results.multi_hand_landmarks:
        hand_landmarks = results.multi_hand_landmarks[0]
        update_cursor(hand_landmarks)

        if is_stop_requested():
            print("jarvis got killed")
            break

capture.release()
cv2.destroyAllWindows()