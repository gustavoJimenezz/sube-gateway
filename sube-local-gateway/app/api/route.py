import json
from dataclasses import dataclass, asdict
from typing import Literal
from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from app.controllers.sube_controller import SubeApp
from app.logger_config import setup_logger

logger = setup_logger(__name__)

# -----------------------------------------------------------------------------
# Init app
# -----------------------------------------------------------------------------
def get_sube_path() -> str:
    """Dynamically searches for the SUBE executable, bypassing accent character issues."""
    try:
        return str(next(Path("C:/Program Files (x86)").glob("*SUBE/*SUBE.exe")))
    except StopIteration:
        return r"C:\Program Files (x86)\Conexión Móvil SUBE\Conexión Móvil SUBE.exe"

EXE_PATH = get_sube_path()
PROCESS_NAME = r"Conexi[oó]n M[oó]vil SUBE\.exe"
WINDOW_TITLE = r"Conexi[oó]n M[oó]vil"

app = FastAPI(
    title="SUBE Automation API",
    description="API local To orchestrate interaction with the SUBE reader",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow request from localhost
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------------------------------------------------------
# Init SubeApp instance
# -----------------------------------------------------------------------------
_sube_instance = None

def get_sube_controller() -> SubeApp:
    """Provide a single, persistent SubeApp instance (Singleton)."""
    global _sube_instance
    
    if _sube_instance is None:
        logger.info("[*] Creating unique SubeApp controller instance...")
        _sube_instance = SubeApp(
            exe_path=EXE_PATH, 
            window_title=WINDOW_TITLE, 
            process_name=PROCESS_NAME
        )
    return _sube_instance
# controller = get_sube_controller()
# import pdb;pdb.set_trace()
# controller.open()
# controller.scan_card()
# -----------------------------------------------------------------------------
# Response Classes
# -----------------------------------------------------------------------------
@dataclass
class StatusResponse:
    """Indicates whether the SUBE application is open or closed."""
    status: Literal["open", "closed"]

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)


@dataclass
class AccionResponse:
    """Result of the action, either success or error."""
    status: Literal["success", "error"]
    message: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)


@dataclass
class ReadCardResponse:
    """Response when attempting to read a SUBE card.

    status: Result of the operation: 'success' if read correctly, 'error' otherwise.
    """
    status: Literal["success", "error"]
    data: list[str] | None = None
    message: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)


@dataclass
class CreditBalanceResponse:
    """Response when attempting to credit balance on a SUBE card.
    status: Result of the operation: 'success' if credited correctly, 'error' otherwise.
    """
    status: Literal["success", "error"]
    data: list[str] | None = None
    message: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)

# -----------------------------------------------------------------------------
# EndPoint GET /status
# -----------------------------------------------------------------------------
@app.get("/status", response_model=StatusResponse, tags=["Monitoring"])
async def get_status(sube: SubeApp = Depends(get_sube_controller)):
    """
    Returns the current state of the SUBE application.
    """
    try:
        is_running = sube.status()
        return {"status": "open" if is_running else "closed"}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al verificar el estado de la app: {str(e)}"
        )

# -----------------------------------------------------------------------------
# EndPoint POST /open
# -----------------------------------------------------------------------------
@app.post("/open", response_model=AccionResponse, tags=["Ciclo de Vida"])
async def open_application(sube: SubeApp = Depends(get_sube_controller)):
    """
    Ensures the SUBE application process is running and initialized.
    """
    try:
        process_active = sube.open()
        
        if process_active:
            return {"status":"success", 
                    "message":"Application process verified active."}
            

        return {"status":"error", 
                "message":"Unable to verify or start the application process."}
        
    except Exception as e:
        logger.error(f"[CRITICAL] API crash in /open endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Fatal error during application opening: {str(e)}"
        )

# -----------------------------------------------------------------------------
# EndPoint POST /close
# -----------------------------------------------------------------------------
@app.post("/close", response_model=AccionResponse, tags=["Ciclo de Vida"])
async def close_application(sube: SubeApp = Depends(get_sube_controller)):
    """
    Terminates the application process and cleans up resources.
    """
    try:
        is_closed = sube.close()
        if is_closed:
            return {"status":"success", 
                    "message":"Application closed successfully and process terminated."}
        
        return {"status":"error", 
                "message":"Application was not running or could not be terminated."}

    except Exception as e:
        logger.error(f"[CRITICAL] API crash in /close endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Fatal error during application closure: {str(e)}"
        )

# -----------------------------------------------------------------------------
# EndPoint POST /read
# -----------------------------------------------------------------------------
@app.post("/read", response_model=ReadCardResponse, tags=["Operaciones"])
async def read_card(sube: SubeApp = Depends(get_sube_controller)):
    """
    Activates the balance reading routine and returns the raw UI text arrays.
    """
    try:
        result = sube.scan_card()
        
        if result.get("status") == "success":
            return {"status":"success",
                    "data":result.get("data", []),
                    "message":"Card read successfully"}
            
        return {"status":"error",
                "data":[],
                "message":result.get("message", "No card read or reader unavailable")}
        
    except Exception as e:
        logger.error(f"[CRITICAL] API crash in /read endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Fatal error during card reading routine: {str(e)}"
        )

# -----------------------------------------------------------------------------
# EndPoint POST /credit-balance
# -----------------------------------------------------------------------------
@app.post("/credit-balance", response_model=CreditBalanceResponse, tags=["Operaciones"])
async def credit_balance(sube: SubeApp = Depends(get_sube_controller)):
    """
    Activates the balance crediting routine and returns the raw UI text arrays.
    """
    try:
        result = sube.credit_balance()
        
        if isinstance(result, dict) and result.get("status") == "success":
            return {"status":"success",
                    "data":result.get("data", []),
                    "message":result.get("message", "Credit operation completed successfully.")}

        error_msg = result.get("message", "Failed to credit balance") if isinstance(result, dict) else "Failed to credit balance"
        return {"status":"error",
                "data":[],
                "message":error_msg}
    
        
    except Exception as e:
        logger.error(f"[CRITICAL] API crash in /credit-balance endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Fatal error during credit balance routine: {str(e)}"
        )

# -----------------------------------------------------------------------------
# EndPoint POST /restart
# -----------------------------------------------------------------------------
@app.post("/restart", response_model=AccionResponse, tags=["Ciclo de Vida"])
async def restart_application(sube: SubeApp = Depends(get_sube_controller)):
    """
    Closes the current application instance and starts a fresh one.
    """
    try:
        success = sube.restart()
        
        if success:
            return {
                "status": "success", 
                "message": "Application restarted successfully"
            }

        return {
            "status": "error", 
            "message": "Could not restart the application"
        }
        
    except Exception as e:
        logger.error(f"[CRITICAL] API crash in /restart endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Fatal error during application restart: {str(e)}"
        )

# -----------------------------------------------------------------------------
# EndPoint POST /float
# -----------------------------------------------------------------------------
@app.post("/float", response_model=AccionResponse, tags=["Ciclo de Vida"])
async def float_application(sube: SubeApp = Depends(get_sube_controller)):
    """
    Brings the SUBE application window to the front and sets it to always-on-top.
    """
    try:
        window_floated = sube.float_window()
        
        if window_floated:
            return {
                "status": "success", 
                "message": "Application window maximized and locked always-on-top."
            }
            
        return {
            "status": "error", 
            "message": "Unable to locate or maximize the application window. Ensure it is open."
        }
        
    except Exception as e:
        logger.error(f"[CRITICAL] API crash in /float endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Fatal error while trying to float application window: {str(e)}"
        )
