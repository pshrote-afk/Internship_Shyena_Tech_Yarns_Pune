import pyautogui
import time

def open_protonvpn():
    pyautogui.hotkey('win', 'd')  # Show desktop
    time.sleep(1)
    pyautogui.hotkey('win')       # Open Start Menu
    time.sleep(0.5)
    pyautogui.write('Proton VPN') # Search
    time.sleep(1)
    pyautogui.press('enter')      # Launch
    time.sleep(5)                 # Wait for app
    print("ProtonVPN opened\n")

def quick_connect_and_close():
    pyautogui.press('tab', presses=3, interval=0.3)  # Focus Quick Connect
    pyautogui.press('enter')      # Click it
    time.sleep(5)                 # Wait 4 sec
    print("VPN server changed\n")
    pyautogui.hotkey('alt', 'f4') # Close app
    print("ProtonVPN closed\n")
# Run
open_protonvpn()
quick_connect_and_close()