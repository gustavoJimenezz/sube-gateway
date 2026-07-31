import re
import psutil
from pywinauto import Application
from .base_controller import WindowController

class AppConnectionError(Exception):
    def __init__(self, title, message):
        self.title = title
        self.message = f"{message} '{title}'"
        super().__init__(self.message)

class WindowSube(WindowController):
    def __init__(self, title_pattern):
        self.title_pattern = title_pattern

    def connect(self, timeout: int = 5):
        """Attempts to connect to an existing instance of the application."""
        try:
            hwnd = self.get_window_handle(self.title_pattern)
            if not hwnd:
                raise Exception(f"Window not found: {self.title_pattern}")
    
            app = Application(backend="uia").connect(handle=hwnd, timeout=timeout)
            return app.window(handle=hwnd)
        except Exception as e:
            raise AppConnectionError(self.title_pattern, message="Unable to connect to the application") from e

    def is_open(self, process_name: str) -> bool:
        """Verifies if the process is active in Windows."""
        for proc in psutil.process_iter(['name']): 
            try:
                name = proc.info['name']
                if name and re.search(process_name, name, re.IGNORECASE):
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
                
        return False
    
    def minimize(self):
        return self.minimize_window(self.title_pattern)
    
    def maximize(self):
        return self.maximize_window(self.title_pattern)

    def is_minimized(self):
        return self.is_window_minimized(self.title_pattern)
    
    def is_maximized(self):
        return self.is_window_maximized(self.title_pattern)

    def move_to_right(self):
        return self.reposition_to_right(self.title_pattern)

    def is_pattern_present_on_screen(self, regex_patterns):
        """Scans the UI once using the window handle and returns True if any match."""
        hwnd = self.get_window_handle(self.title_pattern)
        if not hwnd:
            return False

        app = Application(backend="uia").connect(handle=hwnd)
        actual_window = app.window(handle=hwnd)

        text_elements = actual_window.descendants(control_type="Text")
        captured_texts = [el.window_text().strip() for el in text_elements if el.window_text()]

        full_ui_text = " ".join(captured_texts)
        for pattern in regex_patterns:
            if re.search(pattern, full_ui_text, re.IGNORECASE):
                return True
        return False

    def is_main_menu_visible(self):
        hwnd = self.get_window_handle(self.title_pattern)

        if not hwnd:
            return False

        app = Application(backend="uia").connect(handle=hwnd)
        window = app.window(handle=hwnd)

        menu_buttons = [
            btn for btn in window.descendants(control_type="Button") if btn.element_info.name not in ("Minimizar", "Maximizar", "Cerrar")
        ]
        
        return len(menu_buttons) == 6