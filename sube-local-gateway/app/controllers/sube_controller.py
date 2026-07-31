import os
import re
import time
import subprocess
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_result, retry_if_exception_type, RetryError, stop_after_delay
from app.automation.sube_window import WindowSube
from app.logger_config import setup_logger

logger = setup_logger(__name__)

def _menu_not_visible(result: bool) -> bool:
    """Retorna True si debe reintentar (es decir, si el resultado fue False)."""
    return not result

def _return_false_on_failure(retry_state):
    """Callback que fuerza a tenacity a retornar False cuando se agotan los intentos."""
    logger.error("[!] Failed to return to the main menu after maximum attempts.")
    return False

class SubeApp:
    def __init__(self, exe_path, window_title, process_name):
        self.exe_path = exe_path
        self.window_title = window_title
        self.procces_name = process_name
        self.window = WindowSube(self.window_title)
        self._current_window = None

    def status(self) -> bool:
        """Checks if the SUBE application is currently running."""
        logger.info(f"[*] status ...")
        return self.window.is_open(self.procces_name)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_fixed(1),
        retry=retry_if_exception_type((PermissionError, OSError)),
        reraise=True
    )
    def _start_process(self) -> bool:
        """Verifies the existence of the executable and launches the process."""
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
        """Verifies if the application is running and starts it if not."""
        logger.info("[*] Opening application...")
        try:
            if not self.status():
                if self._start_process():
                    self._current_window = self.window.connect()
                    self.window.move_to_right()
                    self.window.minimize()
    
            logger.info("[+] Application process verified and window minimized.")
        except Exception as e:
            logger.warning(f"[!] Issue during application startup or minimization: {e}")

        return self.status() is True
    
    def close(self) -> bool:
        """Terminates the application process using window connection."""
        logger.info("[-] Stopping application...")
        try:
            if self.status():
                logger.info("[*] Attempting to close...")
                app_window = self._current_window
                if app_window:
                    app_window.close()
                    logger.info("[+] Process stopped successfully.")
        except Exception as e:
            logger.warning(f"[!] UI interaction finished or skipped: {e}")   
        return self.status() is False

    @retry(
        stop=stop_after_delay(180),
        wait=wait_fixed(0.5),
        retry=retry_if_result(lambda result: result is None),
        reraise=True,
    )
    def _wait_for_ui_data(self, app_window):
        """Polls the UI once and returns the captured text once processing finishes."""
        text_elements = app_window.descendants(control_type="Text")
        captured_texts = [el.window_text().strip() for el in text_elements if el.window_text()]
        if not captured_texts:
            return None
        
        full_ui_text = " ".join(captured_texts)
        
        processing_patterns = [
            r"aguard(a|á) un instante",
            r"procesando\.\.\."
        ]
        
        is_processing = any(
            re.search(pattern, full_ui_text, re.IGNORECASE) 
            for pattern in processing_patterns
        )

        if is_processing:
            logger.info("[*] UI is still processing transaction... retrying.")
            return None
        return captured_texts
    import time # Asegúrate de importarlo

    def scan_card(self) -> dict:
        """Interact with the interface and press “Consultar saldo”."""
        if not self.status():
            return {"status": "error", "message": "Application interface is not active or ready."}
        
        try:
            if not getattr(self, '_current_window', None):
                logger.info("[*] Window reference lost or None. Reconnecting...")
                self._current_window = self.window.connect()

            self.window.maximize()
            time.sleep(1)

            app_window = self._current_window
            if app_window is None:
                return {"status": "error", "message": "Could not attach to the application window."}

            if not self.window.is_card_reader_connected(app_window):
                return {"status": "error", "message": "Card reader hardware is not connected."}
                
            if not self.window.is_main_menu_visible(app_window):
                return {"status": "error", "message": "Application is not in the main menu."}

            boton_consulta = app_window.Button4
            boton_consulta.click_input()
            logger.info("[*] Waiting for a response from the reader hardware...")

            captured_texts = []
            try:
                captured_texts = self._wait_for_ui_data(app_window)

                if captured_texts:
                    self.back(app_window)
                else:
                    logger.warning("[!] Data captured but internal scan success validation failed.")
                    self.back(app_window) 
                    
            except Exception as ui_error: 
                logger.error(f"[!] UI Interaction Error: {ui_error}")
                captured_texts = []

            logger.info(f"[debug] Captured Data after completion: {captured_texts}")

            if captured_texts:
                self.window.minimize()
                return {"status": "success", "data": captured_texts}
                
            return {"status": "error", "message": "No data could be read from the card window."}

        except Exception as general_error:
            logger.critical(f"[CRITICAL] Unexpected crash in scan_card: {general_error}")
            return {"status": "error", "message": f"Unexpected fatal error: {str(general_error)}"}

    def credit_balance(self) -> dict:
        """Interact with the interface and press “Acreditar”."""
        if self.status():
            self.window.maximize()
            app_window = self._current_window
            if self.is_card_reader_connected(self._current_window):
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
                return {"status": "success", "data": textos_capturados}
        return {"status": "error", "message": "No data captured from the interface."}

    def restart(self) -> bool:
        """Closes the SUBE application if it is running and opens it again."""
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

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_fixed(1.5),
        retry=retry_if_result(_menu_not_visible),
        retry_error_callback=_return_false_on_failure  # <-- Esto intercepta el error y devuelve False
    )
    def back(self, window) -> bool:
        """Returns to the previous screen by clicking the lowest button.
        Guaranteed to return ONLY True (success) or False (failed after all retries).
        """
        if self.window.is_main_menu_visible(window):
            logger.info("[*] Successfully in main menu.")
            return True
            
        try:
            window_rect = window.rectangle()
            y_threshold = window_rect.top + (window_rect.height() * 0.7)

            for button in window.Custom.children(control_type="Button"):
                coords = button.rectangle()
                if coords.top > y_threshold:
                    button.click_input()
                    logger.info("[*] 'Back' button clicked. Verifying state...")
                    
                    time.sleep(0.5) 
                    return self.window.is_main_menu_visible(window)
                    
            logger.warning("[!] 'Back' button not found in the lower section.")
            return False
        except Exception as e:
            logger.warning(f"[!] Error trying to navigate back: {e}")
            return False
