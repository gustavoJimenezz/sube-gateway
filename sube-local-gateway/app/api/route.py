import re
import json
from dataclasses import dataclass, asdict
from typing import Literal, Optional
from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
from pathlib import Path
from app.controllers.sube_controller import SubeApp

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
def get_sube_controller() -> SubeApp:
    """Provide the SubeApp instance."""
    return SubeApp(
        exe_path=EXE_PATH, 
        window_title=WINDOW_TITLE, 
        process_name=PROCESS_NAME
    )
# app= get_sube_controller()
# app.scan_card()
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
    message: Optional[str] = None

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
    card_number: Optional[str] = None
    balance: Optional[float] = None
    message: Optional[str] = None

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
    previous_balance: Optional[float] = None
    amount_loaded: Optional[float] = None
    new_balance: Optional[float] = None
    pending_amount: Optional[float] = None
    message: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)


# -----------------------------------------------------------------------------
# EndPoint GET /status
# -----------------------------------------------------------------------------
@app.get("/status", tags=["Monitoring"])
async def get_status(sube: SubeApp = Depends(get_sube_controller)):
    """
    Returns a JSON object indicating whether the SUBE application is running.
    """
    try:
        is_running = bool(sube.status())
        return {"is_open": is_running}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Error al verificar el estado de la app: {str(e)}"
        )

# -----------------------------------------------------------------------------
# EndPoint POST /open
# -----------------------------------------------------------------------------
@app.post("/open", response_model=AccionResponse, tags=["Ciclo de Vida"])
async def open_application(sube: SubeApp=Depends(get_sube_controller)):
    """
    Ensures the SUBE application is open and ready for interaction.
    """
    try:
        # if sube_controller.status():
        #     return AccionResponse(status="success", message="Application is already open")

        success = sube.open()
        if success and sube.status():
            return AccionResponse(status="success", message="Application started successfully and minimized")

        return AccionResponse(status="error", message="Unable to start the application")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# -----------------------------------------------------------------------------
# EndPoint POST /close
# -----------------------------------------------------------------------------

@app.post("/close", response_model=AccionResponse, tags=["Ciclo de Vida"])
async def close_application(sube: SubeApp=Depends(get_sube_controller)):
    """
    Checks the application status and closes it.
    """
    try:
        success = sube.close()
        if success  and not sube.status():
            return AccionResponse(status="success", message="Application closed successfully")
        
        return AccionResponse(status="error", message="Application was not running or could not be closed")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# -----------------------------------------------------------------------------
# EndPoint POST /read
# -----------------------------------------------------------------------------

@app.post("/read", response_model=ReadCardResponse, tags=["Operaciones"])
async def read_card(sube: SubeApp=Depends(get_sube_controller)):
    """
    Activates the balance reading/query routine on the card reader.
    """
    try:
        result = sube.scan_card()
        print("result : : ")
        print(result)
        # Parse data
        card_number, balance = parse_card_data(result.get("data", []))
        
        # Prepare response
        if result["status"] == "success" and card_number and balance is not None:
            response = ReadCardResponse(
                status="success",
                card_number=card_number,
                balance=balance,
                message="Card read successfully"
            )
        else:
            response = ReadCardResponse(
                status="error",
                card_number=None,
                balance=None,
                message=result.get("message", "Not card read")
            )
        
        return response
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

def parse_card_data(data):
    """
    Extracts card number and balance from scanned data.
    """
    card_number = None
    balance = None
    
    for item in data:
        # Extract card number
        if re.match(r'^\d{4}\s\d{4}\s\d{4}\s\d{4}$', item):
            card_number = item.replace(" ", "")
            
        # Extract balance
        elif re.match(r'^\$[\d,.]+$', item):
            balance_str = item.replace("$", "").replace(",", ".")
            try:
                balance = float(balance_str)
            except ValueError:
                pass
    
    return card_number, balance

# -----------------------------------------------------------------------------
# EndPoint POST /credit-balance
# -----------------------------------------------------------------------------

@app.post("/credit-balance", response_model=CreditBalanceResponse, tags=["Operaciones"])
async def credit_balance(sube: SubeApp=Depends(get_sube_controller)):
    """
    Activates the balance reading/query routine on the card reader.
    """
    try:
        result = sube.credit_balance()
        
        if not isinstance(result, dict) or result.get("status") != "success":
            error_msg = result.get("message", "Failed to credit balance") if isinstance(result, dict) else "Failed to credit balance"
            return CreditBalanceResponse(
                status="error",
                message=error_msg
            )

        data = result.get("data", [])

        # Filtramos y parseamos todos los valores monetarios de una sola vez
        money_values = [
            parse_credit_balance(m) for m in data if isinstance(m, str) and m.startswith("$")
        ]

        # Extraemos los valores de forma segura asegurando los 4 elementos
        balances = (money_values + [None] * 4)[:4]

        return CreditBalanceResponse(
            status="success",
            previous_balance=balances[0],
            amount_loaded=balances[1],
            new_balance=balances[2],
            pending_amount=balances[3],
            message=result.get("message", "Credit operation completed")
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

def parse_credit_balance(s: str) -> Optional[float]:
    try:
        return float(s.replace("$", "").replace(".", "").replace(",", "."))
    except (ValueError, AttributeError):
        return None

# -----------------------------------------------------------------------------
# EndPoint POST /restart
# -----------------------------------------------------------------------------
@app.post("/restart", response_model=AccionResponse, tags=["Operaciones"])
async def restart(sube: SubeApp=Depends(get_sube_controller)):
    """
    Navigates back in the SUBE application interface.
    """
    try:
        success = sube.restart()
        if success:
            return AccionResponse(status="success", message="Navigation back executed")

        return AccionResponse(status="error", message="Could not navigate back")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

