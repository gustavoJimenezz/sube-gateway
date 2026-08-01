import re
import win32gui
import win32con
from pywinauto.win32functions import GetSystemMetrics
from app.logger_config import setup_logger

logger = setup_logger(__name__)
class WindowController:
    def get_window_handle(self, title_pattern: str):
        """Searches for the window HWND using regular expressions."""
        found = []
        
        def enum_cb(h, _):
            if win32gui.IsWindowVisible(h):
                window_text = win32gui.GetWindowText(h)
                if window_text and re.search(title_pattern, window_text, re.IGNORECASE):
                    found.append(h)
                
        win32gui.EnumWindows(enum_cb, None)
        return found[0] if found else None
    
    def enable_always_on_top(self, title_pattern: str) -> bool:
        """Clamps the window permanently to the front (Topmost)."""
        hwnd = self.get_window_handle(title_pattern)
        if hwnd:
            win32gui.SetWindowPos(
                hwnd, 
                win32con.HWND_TOPMOST, 
                0, 0, 0, 0, 
                win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_SHOWWINDOW
            )
            logger.info(f"[+] Always-on-top enabled for: {title_pattern}")
            return True
        return False

    def disable_always_on_top(self, title_pattern: str) -> bool:
        """Removes the permanent floating state (Notopmost) safely."""
        hwnd = self.get_window_handle(title_pattern)
        if hwnd:
            win32gui.SetWindowPos(
                hwnd, 
                win32con.HWND_NOTOPMOST, 
                0, 0, 0, 0, 
                win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_NOACTIVATE
            )
            logger.info(f"[-] Always-on-top disabled for: {title_pattern}")
            return True
        return False


    def minimize_window(self, title_pattern: str) -> bool:
        """Safely removes floating state and minimizes the window."""
        hwnd = self.get_window_handle(title_pattern)
        if hwnd:
            self.disable_always_on_top(title_pattern)
            win32gui.ShowWindow(hwnd, win32con.SW_MINIMIZE)
            return True
        return False
    
    def maximize_window(self, title_pattern: str) -> bool:
        """Restores/Maximizes the window and forces it to be always-on-top."""
        hwnd = self.get_window_handle(title_pattern)
        if hwnd:
            if self.is_window_minimized(title_pattern):
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
    
            win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
            self.enable_always_on_top(title_pattern)
            try:
                win32gui.SetForegroundWindow(hwnd)
            except Exception:
                pass
            return True
        return False
    
    def is_window_minimized(self, title_pattern: str):
        """Returns True if the window is currently minimized."""
        hwnd = self.get_window_handle(title_pattern)
        if hwnd:
            placement = win32gui.GetWindowPlacement(hwnd)
            return placement[1] == win32con.SW_SHOWMINIMIZED
        return False
    
    def is_window_maximized(self, title_pattern: str):
        """Returns True if the window is currently maximized or visible/restored."""
        hwnd = self.get_window_handle(title_pattern)
        if hwnd:
            placement = win32gui.GetWindowPlacement(hwnd)
            return placement[1] in (win32con.SW_SHOWMAXIMIZED, win32con.SW_NORMAL)
        return False

    def reposition_to_right(self, title_pattern: str) -> None:
        """Moves the application window to the far-right side of the screen using Win32 API."""
        hwnd = self.get_window_handle(title_pattern)

        if not hwnd:
            logger.warning(f"[!] No window found matching pattern: {title_pattern}")
            return

        screen_width = GetSystemMetrics(0)
        screen_height = GetSystemMetrics(1)
        left, top, right, bottom = win32gui.GetWindowRect(hwnd)
        w_width = right - left
        w_height = bottom - top

        new_x = screen_width - w_width
        new_y = (screen_height - w_height) // 2

        win32gui.MoveWindow(hwnd, new_x, new_y, w_width, w_height, True)
        logger.info(f"[+] Window repositioned via Win32 API to X: {new_x}, Y: {new_y}")
