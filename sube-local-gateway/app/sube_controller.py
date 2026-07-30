import os
import re
import time
import subprocess
import psutil
import win32gui
import win32con
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_result, retry_if_exception_type, RetryError, stop_after_delay
from pywinauto import Application
from pywinauto.win32functions import GetSystemMetrics
from pathlib import Path
from .logger_config import setup_logger
logger = setup_logger(__name__)


class AppConnectionError(Exception):
    def __init__(self, title, message):
        self.title = title
        self.message = f"{message} '{title}'"
        super().__init__(self.message)


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
    
    def minimize_window(self, title_pattern: str):
        """Minimizes the specified window natively."""
        hwnd = self.get_window_handle(title_pattern)
        if hwnd:
            win32gui.ShowWindow(hwnd, win32con.SW_MINIMIZE)
            return True
        return False
    
    def maximize_window(self, title_pattern: str):
        """Restores and maximizes (brings to front) the specified window."""
        hwnd = self.get_window_handle(title_pattern)
        if hwnd:
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            win32gui.SetForegroundWindow(hwnd)
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
        """
        Moves the application window to the far-right side of the screen using Win32 API.
        """
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

        
class WindowSube(WindowController):
    def __init__(self, title_pattern):
        self.title_pattern = title_pattern

    def connect(self, timeout: int = 5):
        """
        Attempts to connect to an existing instance of the application.

        :param window_title: The title of the window to search for.
        :param timeout: Maximum wait time in seconds.
        :return: True if the connection was successful.
        :raises AppConnectionError: If the connection fails or the window cannot be found.
        """
        try:
            hwnd = self.get_window_handle(self.title_pattern)
            if not hwnd:
                raise Exception(f"Window not found: {self.title_pattern}")
    
            app = Application(backend="uia").connect(handle=hwnd, timeout=timeout)
            return app.window(handle=hwnd)
        except Exception as e:
            raise AppConnectionError(self.title_pattern, message="Unable to connect to the application") from e

    def is_open(self, process_name: str) -> bool:
        """
        Verifies if the process is active in Windows.
        """
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
        """Scans the UI once using the window handle and returns True if any of the

        provided regex patterns match the UI text, otherwise returns False.
        """
        hwnd = self.get_window_handle(self.title_pattern)

        if not hwnd:
            return False

        app = Application(backend="uia").connect(handle=hwnd)
        actual_window = app.window(handle=hwnd)

        text_elements = actual_window.descendants(control_type="Text")
        captured_texts = [
            el.window_text().strip() for el in text_elements if el.window_text()
        ]

        full_ui_text = " ".join(captured_texts)

        for pattern in regex_patterns:
            if re.search(pattern, full_ui_text, re.IGNORECASE):
                return True

        return False


class SubeApp():
    def __init__(self, exe_path, window_title, process_name):
        self.exe_path = exe_path
        self.window_title = window_title
        self.procces_name = process_name
        self.window = WindowSube(self.window_title)

    def _is_card_reader_connected(self):
        patterns = [r"conect[aá] tu dispositivo"]
        return not self.window.is_pattern_present_on_screen(patterns)

    def _is_card_scan_successful(self):
        """Check the interface to confirm whether the SUBE card was read successfully."""
        success_patterns = [
            r"consulta de saldo",
            r"sube nro",
            r"\d{4}\s\d{4}\s\d{4}\s\d{4}" 
        ]
        return self.window.is_pattern_present_on_screen(regex_patterns=success_patterns)

    def _is_processing_transaction(self):
        """It detects the transient loading screen when the application is communicating with the SUBE servers."""
        processing_patterns = [
            r"aguard(a|á) un instante",
            r"procesando\.\.\."
        ]
        
        return self.window.is_pattern_present_on_screen(regex_patterns=processing_patterns)

    def _is_card_not_detected_error(self):
        """It detects the error screen when no card is inserted or when a card is removed prematurely."""
        error_patterns = [
            r"no se detect(o|ó) ninguna tarjeta",
            r"err:\s?0x9301"
        ]
        
        return self.window.is_pattern_present_on_screen(regex_patterns=error_patterns)

    def status(self, max_atemps=5, pause=2) -> bool:
        """
        Checks if the SUBE application is currently running.
        
        :return: True if the application is running, False otherwise.
        """

        logger.info(f"[*] status ...")
        return self.window.is_open(self.procces_name)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_fixed(1),
        retry=retry_if_exception_type((PermissionError, OSError)),
        reraise=True
    )
    def _start_process(self) -> bool:
        """
        Verifies the existence of the executable and launches the process.
        
        :return: True if successfully launched, False if the file does not exist.
        """
        if not os.path.exists(self.exe_path):
            logger.error(f"Executable not found at {self.exe_path}")
            return False

        logger.info("[+] Launching executable process ...")
        try:
            subprocess.Popen(self.exe_path)
            time.sleep(2)
            return True
        except (PermissionError, OSError) as e:
            logger.warning(f"[-] Temporary error launching app: {e}. Retrying...")
            raise e

    def open(self) -> bool:
        """
        Verifies if the application is running and starts it if not.
        """
        logger.info("[*] Opening application...")
        
        try:
            if not self.status(self.procces_name):
                if self._start_process():
                    self.window.move_to_right()
                    self.window.minimize()
    
            logger.info("[+] Application process verified and window minimized.")
            
        except Exception as e:
            logger.warning(f"[!] Issue during application startup or minimization: {e}")

        return self.status(self.procces_name) is True
    
    def close(self) -> bool:
        """Terminates the application process using window connection."""
        logger.info("[-] Stopping application...")

        try:
            if self.status(self.procces_name):
                logger.info("[*] Attempting to close via UI...")
                app_window = self.window.connect(timeout=5)
                if app_window:
                    app_window.close()
                    logger.info("[+] Process stopped successfully.")
                time.sleep(1.5)
                
        except Exception as e:
            logger.warning(f"[!] UI interaction finished or skipped: {e}")
        
        return self.status(self.procces_name) is False
    
    @retry(
        stop=stop_after_delay(180),
        wait=wait_fixed(0.5),
        retry=retry_if_result(lambda result: result is None),
        reraise=True,
    )
    def _wait_for_ui_data(self, app_window):
        """Polls the UI once and returns the captured text once processing finishes."""
        # 1. Volcamos los elementos de texto primero
        text_elements = app_window.descendants(control_type="Text")
        captured_texts = [el.window_text().strip() for el in text_elements if el.window_text()]

        if captured_texts and self._is_processing_transaction():
            return None

        if captured_texts:
            return captured_texts
            
        return None

    def scan_card(self) -> dict:
        """
        Interact with the interface, press “Consultar saldo”
        and wait dynamically for the hardware to finish reading.
        """
        if self.status():
            self.window.maximize()

            app_window = self.window.connect()
            if self._is_card_reader_connected():
                boton_consulta = app_window.Button4
                boton_consulta.click_input()
                logger.info("[*] Waiting for a response from the reader hardware...")

            try:
                captured_texts = self._wait_for_ui_data(app_window)
                if captured_texts and self._is_card_scan_successful():
                    self.back()

            except RetryError as e:
                logger.error(f"[!] Error : {e}")
                captured_texts = []
                
            logger.info(f"[debug] Captured Data after completion: {captured_texts}")

            if captured_texts:
                self.window.minimize()
                return {
                    "status": "success",
                    "data": captured_texts
                }
        return {
            "status": "error",
            "message": "No data captured from the interface."
        }

    def credit_balance(self) -> dict:
        """
        Interact with the interface, press “Acreditar”
        """
        if self.status():
            self.window.maximize()

            app_window = self.window.connect()
            if self._is_card_reader_connected():
                botn_credit_balance = app_window.Button5
                botn_credit_balance.click_input()
                logger.info("[*] Waiting for a response from the reader hardware...")

            try:
                textos_capturados = self._wait_for_ui_data(app_window)
                logger.info(f"[debug] textos_capturados: {textos_capturados}")
                if textos_capturados and self._is_card_not_detected_error():
                    self.back()

            except RetryError as e:
                logger.error(f"[!] Error : {e}")
                textos_capturados = []

            logger.info(f"[debug] Data: {textos_capturados}")
            if textos_capturados:
                self.window.minimize()
                return {
                    "status": "success",
                    "data": textos_capturados
                }
        return {
                "status": "error",
                "message": "No data captured from the interface."
            }

    def restart(self) -> bool:
        """
        Closes the SUBE application if it is running and opens it again.
        If it was already closed before calling this method, it simply starts it.
        """
        logger.info("[+] Initiating application restart...")

        if self.status():
            logger.info("[*] Closing the current application instance...")
            self.close()
            time.sleep(0.2)

        logger.info("[*] Opening the application again...")
        success = self.open()

        if success:
            logger.info("[+] Application successfully restarted.")
        else:
            logger.error("[!] Failed to restart the application properly.")

        return success

    def back(self) -> bool:
        """
        Returns to the previous screen by clicking the lowest button 
        available on the current interface layout.
        """

        try:
            app_window = self.window.connect(timeout=5)
            
            window_rect = app_window.rectangle()
            y_threshold = window_rect.top + (window_rect.height() * 0.7)

            for button in app_window.Custom.children(control_type="Button"):
                coords = button.rectangle()
                
                if coords.top > y_threshold:
                    button.click_input()
                    return True
                    
            logger.warning("[!] 'Back' button not found in the lower section of the screen.")
            return False
            
        except Exception as e:
            logger.warning(f"[!] Error trying to navigate back: {e}")
            return False
 