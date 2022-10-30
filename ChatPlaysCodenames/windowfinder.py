from PIL import ImageGrab
import win32gui, win32com.client
import numpy as np
import cv2

class Screenshot:
    
    def __init__(self, search='codenames '):
        
        toplist, self.winlist = [], []
        self.search = search
        self.active_window = None
        def enum_cb(hwnd, results):
            self.winlist.append((hwnd, win32gui.GetWindowText(hwnd)))
        win32gui.EnumWindows(enum_cb, toplist)        
    
    
    def check_windows(self) -> int:
        
        codename_windows = [(hwnd, title) for hwnd, title in self.winlist if self.search.lower() in title.lower()]
        window_count = len(codename_windows)
        if window_count == 0:
            self.active_window = None
            return 0
        elif window_count == 1:
            self.active_window = codename_windows[0][0]
            return 1
        else:
            self.active_window = None
            return 2
    
    def take_screenshot(self) -> np.array:
        
        """
        shell = win32com.client.Dispatch("WScript.Shell")
        shell.SendKeys('%')
        win32gui.SetForegroundWindow(self.active_window)
        shell.SendKeys('%')
        """
        bbox = win32gui.GetWindowRect(self.active_window)
        screen = cv2.cvtColor(np.array(ImageGrab.grab(bbox)), cv2.COLOR_RGB2BGR)
        return screen
        
        
if __name__ == '__main__':
    sh = Screenshot()
    print(sh.check_windows())
    sh.take_screenshot()
    cv2.imshow('test',sh.take_screenshot())