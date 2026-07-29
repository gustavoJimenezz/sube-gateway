import os
import re
import time
import subprocess
import psutil
import win32gui
import win32con
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_result, retry_if_exception_type
from pywinauto import Application
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
    

class SubeApp():
    def __init__(self, exe_path, window_title, process_name):
        self.exe_path = exe_path
        self.window_title = window_title
        self.procces_name = process_name
        self.window = WindowSube(self.window_title)

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_fixed(2),
        retry=retry_if_result(lambda res: res is False),
        reraise=True
    )
    def status(self, max_atemps=5, pause=2) -> bool:
        """
        Checks if the SUBE application is currently running.
        
        :return: True if the application is running, False otherwise.
        """

        logger.info(f"[*] status ...")
        return self.window.is_open(self.procces_name)


    @retry(
        stop=stop_after_attempt(5),
        wait=wait_fixed(1),
        retry=retry_if_result(lambda res: res is False),
        reraise=True
    )
    def _stop_process(self) -> bool:
        if self._process.poll() is not None:
            logger.info("[+] Process stopped successfully.")
            return True
        return False

    def close(self) -> bool:
        """Terminates the process."""
        if not self._process or self._process.poll() is not None:
            logger.info("[*] The application is already stopped.")
            return True

        logger.info("[-] Stopping application...")
        try:
            self._process.terminate()
            return self._stop_process()
        except Exception as e:
            logger.error(f"[!] Error standard stopping: {e}. Forcing kill...")
            self._process.kill()
            return True
    
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
            self._process = subprocess.Popen(self.exe_path)
            return True
        except (PermissionError, OSError) as e:
            logger.warning(f"[-] Temporary error launching app: {e}. Retrying...")
            raise e

    def open(self) -> bool:
        """
        Verifies if the application is running and starts it if not.
        """
        if self.window.is_open(self.procces_name):
            logger.info("[*] The application is currently running.")
            return True
        
        try:
            self._start_process()
            time.sleep(0.5) 

            self.window.minimize()
            logger.info("[+] Application opened, verified, and successfully minimized.")
            return True
        except Exception as e:
            logger.error(f"[!] Error verifying or minimizing the window: {e}")
            return False
 
    def scan_card(self) -> dict:
        """
        Interact with the interface, press “Consultar saldo”
        and wait dynamically for the hardware to finish reading.
        """
        if self.window.is_minimized():
            self.window.maximize()

        app_window = self.window.connect()
        boton_consulta = app_window.Button4
        boton_consulta.click_input()
        
        logger.info("[*] Waiting for a response from the reader hardware...")
        
        timeout = 20  # Maximum waiting time in seconds
        start_time = time.time()
        captured_texts = []
        
        while time.time() - start_time < timeout:
            # Capture all text elements currently visible in the window
            text_elements = app_window.descendants(control_type="Text")
            captured_texts = [el.window_text().strip() for el in text_elements if el.window_text()]
            
            # Check if the app is still processing the request
            is_processing = any("procesando" in t.lower() or "aguardá" in t.lower() for t in captured_texts)
            
            # Exit loop once processing text disappears and we have captured data
            if not is_processing and len(captured_texts) > 0:
                break
                
            time.sleep(0.5)  # Check status every half a second
            
        logger.info(f"[debug] Captured Data after completion: {captured_texts}")
        self.window.minimize()
        
        if captured_texts:
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
        if self.window.is_minimized():
            self.window.maximize()

        app_window = self.window.connect()
        botn_credit_balance = app_window.Button5
        botn_credit_balance.click_input()
        
        logger.info("[*] Waiting for a response from the reader hardware...")
        
        timeout = 20  # Tiempo máximo de espera en segundos
        start_time = time.time()
        textos_capturados = []
        
        while time.time() - start_time < timeout:
            # Capturamos todos los textos actuales de la ventana
            text_element = app_window.descendants(control_type="Text")
            textos_capturados = [el.window_text().strip() for el in text_element if el.window_text()]
            
            # Verificamos si la aplicación YA TERMINó de procesar.
            # Condición de salida: que el texto "Procesando..." o "Aguardá" HAYA DESAPARECIDO,
            # y que al menos tengamos datos o algún mensaje de resultado en pantalla.
            sigue_procesando = any("procesando" in t.lower() or "aguardá" in t.lower() for t in textos_capturados)
            
            if not sigue_procesando and len(textos_capturados) > 0:
                # ¡Terminó el proceso! Salimos del bucle de inmediato
                break
                
            time.sleep(0.5)  # Revisa el estado cada medio segund
        logger.info(f"[debug] Data: {textos_capturados}")
        # [debug] Data: ['Saldo anterior:', 'Importe cargado:', 'Saldo:', 'Importe pendiente:', '$1675,71', '$2000,00', '$3675,71', '$0,00']
        
        self.window.minimize()
        
        if textos_capturados:
            return {
                "status": "success",
                "data": textos_capturados
            }
        return {
                "status": "error",
                "message": "No data captured from the interface."
            }
