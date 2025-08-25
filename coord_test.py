import pyautogui
import time

print("Move your mouse to the desired position. Press Ctrl+C to exit.")
try:
    while True:
        x, y = pyautogui.position()
        print(f"Mouse position: ({x}, {y})", end='\n')
        time.sleep(0.1)
except KeyboardInterrupt:
    print("\nDone.")