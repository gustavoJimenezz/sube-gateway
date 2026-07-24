```
SUBE Local Gateway

Local server that exposes a REST API to control the SUBE application. It allows
interaction with the SUBE desktop application from a web interface without
having to manually perform the steps required to execute its functionalities.
```

```
Project Structure

sube-local-gateway/
├── app/
│   ├── api.py              # FastAPI endpoints
│   ├── sube_controller.py  # SUBE application control logic
│   └── logger_config.py    # Logging configuration
├── dist/
│   └── sube-local-gateway.exe
├── installer/
│   └── SUBE-Local-Gateway-Setup.exe
├── main.py
└── requirements.txt
└── README.md
```

#### dev mode
```
Installation and Execution

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

Main Dependencies

FastAPI - API framework
pywinauto - GUI automation for the SUBE application
psutil - System process management
win32gui / win32con - Windows GUI interaction
```

### `Logs` 

```
The log file is stored at: %TEMP%\sube-local-gateway.log
Quick access: Press Win + R → type %TEMP% → locate sube-local-gateway.log
```

### Build

```
bash
pyinstaller --noconsole --onefile --name sube-local-gateway main.py
```

### Installer
```
The installer is generated with Inno Setup using the installer.iss file. It
configures the service to start automatically when Windows boots and creates
shortcuts on the Desktop and in the Start Menu.

/installer/SUBE-Local-Gateway-Setup.exe
```

###### Known Issue
```
ImportError: win32ui on stripped-down Windows versions (Tiny11)

This error may occur when the required Visual C++ runtime libraries
(vcruntime140.dll) are missing.

Install the Visual C++ Redistributable x64 from the official Microsoft website.

Restart the computer.

Run the following commands in PowerShell:

bash
pip uninstall pywin32 -y
pip install pywin32 --no-cache-dir
python venv\Scripts\pywin32_postinstall.py -install
```
