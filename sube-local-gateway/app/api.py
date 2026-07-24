```
SUBE Local Gateway
Servidor local que expone una API REST para controlar el programa SUBE. Permite
interactuar con la aplicación de escritorio de SUBE desde una interfaz web sin
necesidad de gestionar manualmente los pasos requeridos para ejecutar sus
funcionalidades.
```

```
Estructura del proyecto
text
sube-local-gateway/
├── app/
│   ├── api.py              # Endpoints FastAPI
│   ├── sube_controller.py  # Lógica de control del programa SUBE
│   └── logger_config.py    # Configuración de logs
├── dist/
│   └── sube-local-gateway.exe
├── installer/
│   └── SUBE-Local-Gateway-Setup.exe
├── main.py
└── requirements.txt

```

#### Modo desarrollo
```
Instalación y ejecución
bash
python -m venv venv
pip install -r requirements.txt
python main.py
```

```
Endpoints
/status
json
{ "status": "open" | "closed" }
/open
json
{ "status": "success" | "error", "message": "..." }
/read
json
{
  "status": "success" | "error",
  "card_number": "1234567890123456",
  "balance": 1675.71,
  "message": "..."
}
/credit-balance
json
{
  "status": "success" | "error",
  "previous_balance": 1675.71,
  "amount_loaded": 2000.00,
  "new_balance": 3675.71,
  "pending_amount": 0.00,
    "message": "..."
}
```

```

Dependencias principales
FastAPI - Framework para la capa de API
pywinauto - Automatización de la interfaz gráfica del programa SUBE
psutil - Gestión de procesos del sistema
win32gui / win32con - Interacción con ventanas de Windows
```

### `Logs` 

```
El archivo de logs se almacena en: %TEMP%\sube-local-gateway.log
```

```
Para acceder rápidamente: Win + R → escribir %TEMP% → buscar sube-local-
gateway.log
```

### Compilación

```
bash
pyinstaller --noconsole --onefile --name sube-local-gateway main.py
Instalador
```

```
El instalador se genera con InnoSetup usando el archivo installer.iss. Configura
el servicio para que se ejecute automáticamente al iniciar la PC y agrega
accesos directos en el escritorio y menú de inicio.
```

###### Incidencias conocida
```
Error ImportError: win32ui en versiones recortadas de Windows (Tiny11)

Este error ocurre cuando faltan librerías del sistema Visual C++
(vcruntime140.dll).

Instalar Visual C++ Redistributable X64 desde el sitio oficial de Microsoft

Reiniciar la PC

Ejecutar en PowerShell:

bash
pip uninstall pywin32 -y
pip install pywin32 --no-cache-dir
python venv\Scripts\pywin32_postinstall.py -install
```
