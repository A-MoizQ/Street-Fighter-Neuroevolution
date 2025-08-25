# Example: auto_gui.py
import pygetwindow as gw
import pyautogui
import time
import os

READY_FILE = "controller_ready.txt"

def wait_for_bizhawk():
    # Wait for BizHawk window to appear (adjust as needed)
    time.sleep(10)

def focus_bizhawk_window():
    # Replace with the actual window title if needed
    for w in gw.getAllTitles():
        if "SNES (interim)" in w:
            window = gw.getWindowsWithTitle(w)[0]
            window.activate()
            window.restore()
            # window.maximize()
            print(f"Focused window: {w}")
            return
    print("BizHawk window not found.")

def click_gyroscope_bot():
    # Move mouse to Gyroscope Bot icon (update coordinates for your screen)
    pyautogui.moveTo(829, 188)  # Example coordinates
    pyautogui.click()
    time.sleep(0.5)

def click_run_button():
    pyautogui.moveTo(514, 158)  # Example coordinates for Run button
    pyautogui.click()
    time.sleep(1)

def wait_for_controller_ready():
    while not os.path.exists(READY_FILE):
        time.sleep(0.5)

def cleanup_and_exit():
    if os.path.exists(READY_FILE):
        os.remove(READY_FILE)
    print("Cleaned up ready file. Exiting.")

if __name__ == "__main__":
    wait_for_bizhawk()
    # focus_bizhawk_window()
    click_gyroscope_bot()
    #click_run_button()
    wait_for_controller_ready()
    cleanup_and_exit()