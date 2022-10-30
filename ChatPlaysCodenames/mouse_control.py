import pyautogui
pyautogui.FAILSAFE = False

def click_at(loc: tuple([int, int])):
    pyautogui.moveTo(loc[0], loc[1])
    pyautogui.mouseDown(button="left")
    pyautogui.mouseUp(button="left")