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

    def is_pattern_present_on_screen(self, app_window, regex_patterns):
        """Scans the already connected UI window and returns True if any match."""
        text_elements = app_window.descendants(control_type="Text")
        captured_texts = [el.window_text().strip() for el in text_elements if el.window_text()]

        full_ui_text = " ".join(captured_texts)
        for pattern in regex_patterns:
            if re.search(pattern, full_ui_text, re.IGNORECASE):
                return True
        return False

    def is_main_menu_visible(self, app_window):
        menu_buttons = [
            btn for btn in app_window.descendants(control_type="Button") if btn.element_info.name not in ("Minimizar", "Maximizar", "Cerrar")
        ]
        
        return len(menu_buttons) == 6

    def is_card_reader_connected(self, app_window):
        patterns = [r"conect[aá] tu dispositivo"]
        return not self.is_pattern_present_on_screen(app_window, patterns)
    
    def is_card_not_detected_error(self):
        """It detects the error screen when no card is inserted."""
        error_patterns = [
            r"no se detect(o|ó) ninguna tarjeta",
            r"err:\s?0x9301"
        ]
        return self.is_pattern_present_on_screen(regex_patterns=error_patterns)

    def is_card_scan_successful(self):
        """Check the interface to confirm whether the SUBE card was read successfully."""
        success_patterns = [
            r"consulta de saldo",
            r"sube nro",
            r"\d{4}\s\d{4}\s\d{4}\s\d{4}" 
        ]
        return self.is_pattern_present_on_screen(regex_patterns=success_patterns)

    def is_processing_transaction(self):
        """It detects the transient loading screen."""
        processing_patterns = [
            r"aguard(a|á) un instante",
            r"procesando\.\.\."
        ]
        return self.is_pattern_present_on_screen(regex_patterns=processing_patterns)
