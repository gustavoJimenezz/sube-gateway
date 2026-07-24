# -*- coding: utf-8 -*-
# 1. automation.py (La Capa de Control del Sistema)
# Este archivo es el "músculo" del backend. No sabe nada de HTTP, rutas web, ni navegadores. Su único trabajo es hablar directamente con el sistema operativo Windows y la aplicación física de SUBE.
# Dentro de este archivo definiremos una clase o un conjunto de funciones especializadas que resolverán tres tareas críticas:

# A. Inspección de Procesos (psutil)
# Qué hace: Escanea la tabla de procesos activos de Windows buscando ConexionMovilSUBE.exe.
# Por qué importa: Es una operación de lectura ligera a nivel de kernel. Evita tener que inicializar la pesada librería de pywinauto solo para saber si la aplicación está abierta. Devuelve un simple valor booleano (True/False).

# B. Ciclo de Vida y Ocultación (subprocess + pywinauto)
# Qué hace: Si la aplicación está cerrada, la invoca. Inmediatamente después, abre un canal de comunicación con la API de Windows mediante el backend win32 (o uia, dependiendo de cómo esté construida la app de SUBE) para capturar el identificador de la ventana (Window Handle). Una vez obtenido, ejecuta el comando nativo para desplazar la ventana a las coordenadas lejanas.
# Lógica de Negocio Crítica: Debe incluir un mecanismo de retintento y espera activa. Las interfaces gráficas tardan milisegundos clave en dibujarse en memoria; si intentamos moverla antes de que Windows la registre visualmente, el script fallará.

# C. Simulación e Inspección de la UI (pywinauto)
# Qué hace: Es la función encargada del raspado de la interfaz (UI Scraping). Mapea el árbol de elementos internos de la ventana fantasma (botones, etiquetas de texto, campos de entrada).
# Flujo de ejecución interno:
# Busca el elemento tipo botón con el texto "Consultar saldo" (o su ID interno) y dispara un clic virtual.
# Pausa la ejecución del hilo durante un tiempo prudencial (ej. 1.5 segundos) para dar espacio a la lectura física del hardware USB.
# Analiza la pantalla resultante. Aquí la lógica se bifurca:
# Escenario A (Éxito): Encuentra el contenedor de texto con el patrón numérico (16 dígitos) y lo extrae.
# Escenario B (Error de lectura): Si detecta un diálogo o etiqueta que dice "Coloque su tarjeta" o "Error de conexión", captura ese estado de error en lugar de colgarse.


import os
import re
import time
import subprocess
import psutil
import win32gui
import win32con
from pywinauto import Application
from pathlib import Path

# def obtener_ruta_sube() -> str:
#     """Busca dinámicamente el ejecutable de la SUBE evitando problemas de tildes."""
#     try:
#         return str(next(Path("C:/Program Files (x86)").glob("*SUBE/*SUBE.exe")))
#     except StopIteration:
#         return r"C:\Program Files (x86)\Conexión Móvil SUBE\Conexión Móvil SUBE.exe"

# EXE_PATH = obtener_ruta_sube()
# PROCESS_NAME = r"Conexi[oó]n M[oó]vil SUBE\.exe"
# WINDOW_TITLE = r"Conexi[oó]n M[oó]vil"

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
        self.window_tittle = window_title
        self.procces_name = process_name
        self.window = WindowSube(self.window_tittle)

    def _status(self) -> bool:
        """
        Checks if the SUBE application is currently running.
        
        :return: True if the application is running, False otherwise.
        """
        return self.window.is_open(self.procces_name)

    def _launch_app(self) -> bool:
        """
        Verifies the existence of the executable and launches the process.
        
        :return: True if successfully launched, False if the file does not exist.
        """
        if not os.path.exists(self.exe_path):
            print(f"[!] Error: Executable not found at {self.exe_path}")
            return False

        print("[+] Launching executable process ...")
        subprocess.Popen(self.exe_path)
        return True

    def start_app(self) -> bool:
        """
        Verifies if the application is running and starts it if not.
        """
        if self.window.is_open(self.procces_name):
            print("[*] The application is currently running.")
            return True
        
        attempts = 5
        for i in range(attempts):
            try:
                if self._launch_app():
                    time.sleep(2)
                    self.window.minimize()
                    print("[*] Application opened and minimized.")
                    return True
            except Exception as e:
                print(f"[!] Connecting to the application {self.window_tittle} | attempt:{i+1}/{attempts} {str(e)}")
                return False
 
    def scan_card(self) -> dict:
        """
        Interact with the interface, press “Consultar saldo”
        and wait for the hardware to perform the physical read.
        """
        if self.window.is_minimized():
            self.window.maximize()

        app_window = self.window.connect()
        boton_consulta = app_window.Button4
        boton_consulta.click_input()
        
        print("[*] Waiting for a response from the reader hardware...")
        time.sleep(5)

        text_element = app_window.descendants(control_type="Text")
        textos_capturados = [el.window_text().strip() for el in text_element if el.window_text()]
        print(f"[debug] Data: {textos_capturados}")
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

    def credit_balance(self) -> dict:
        """
        Interact with the interface, press “Acreditar”
        """
        if self.window.is_minimized():
            self.window.maximize()

        app_window = self.window.connect()
        botn_credit_balance = app_window.Button5
        botn_credit_balance.click_input()
        
        print("[*] Waiting for a response from the reader hardware...")
        time.sleep(8)
        
        text_element = app_window.descendants(control_type="Text")
        textos_capturados = [el.window_text().strip() for el in text_element if el.window_text()]
        print(f"[debug] Data: {textos_capturados}")
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
