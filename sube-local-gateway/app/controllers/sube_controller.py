import os
import re
import time
import subprocess
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_result, retry_if_exception_type, RetryError, stop_after_delay
from app.automation.sube_window import WindowSube
from app.logger_config import setup_logger

logger = setup_logger(__name__)

class SubeApp:
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
        """It detects the transient loading screen."""
        processing_patterns = [
            r"aguard(a|á) un instante",
            r"procesando\.\.\."
        ]
        return self.window.is_pattern_present_on_screen(regex_patterns=processing_patterns)

    def _is_card_not_detected_error(self):
        """It detects the error screen when no card is inserted."""
        error_patterns = [
            r"no se detect(o|ó) ninguna tarjeta",
            r"err:\s?0x9301"
        ]
        return self.window.is_pattern_present_on_screen(regex_patterns=error_patterns)

    def status(self, max_atemps=5, pause=2) -> bool:
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
        text_elements = app_window.descendants(control_type="Text")
        captured_texts = [el.window_text().strip() for el in text_elements if el.window_text()]

        if captured_texts and self._is_processing_transaction():
            return None

        if captured_texts:
            return captured_texts
        return None

    def scan_card(self) -> dict:
        """Interact with the interface and press “Consultar saldo”."""
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
                return {"status": "success", "data": captured_texts}
        return {"status": "error", "message": "No data captured from the interface."}

    def credit_balance(self) -> dict:
        """Interact with the interface and press “Acreditar”."""
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

    def back(self) -> bool:
        """Returns to the previous screen by clicking the lowest button."""
        try:
            app_window = self.window.connect(timeout=5)
            window_rect = app_window.rectangle()
            y_threshold = window_rect.top + (window_rect.height() * 0.7)

            for button in app_window.Custom.children(control_type="Button"):
                coords = button.rectangle()
                if coords.top > y_threshold:
                    button.click_input()
                    return True
                    
            logger.warning("[!] 'Back' button not found in the lower section.")
            return False
        except Exception as e:
            logger.warning(f"[!] Error trying to navigate back: {e}")
            return False