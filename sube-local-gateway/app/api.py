import re
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from pathlib import Path
from .sube_controller import SubeApp

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
# Modelos de Respuesta (Pydantic)
# -----------------------------------------------------------------------------
from typing import Literal
from pydantic import BaseModel, Field

class StatusResponse(BaseModel):
    status: Literal["open", "closed"] = Field(
        ...,
        description="Indicates whether the SUBE application is open or closed"
    )


class AccionResponse(BaseModel):
    status: Literal["success", "error"] = Field(
        ..., 
        description="Result of the action, either success or error"
    )
    message: Optional[str] = Field(None, description="Additional message or error details")


class ReadCardResponse(BaseModel):
    """Response when attempting to read a SUBE card.

    status: Result of the operation: 'success' if read correctly,
    'error' otherwise.
    """
    status: Literal["success", "error"] = Field(
        ..., description="Result of the read operation"
    )
    card_number: Optional[str] = Field(
        None, description="Card number read (if applicable)"
    )
    balance: Optional[float] = Field(
        None, description="Available balance on the card (if applicable)"
    )
    message: Optional[str] = Field(
        None, description="Additional message or error details"
    )
    

class CreditBalanceResponse(BaseModel):
    """Response when attempting to credit balance on a SUBE card.

    status: Result of the operation: 'success' if credited correctly,
    'error' otherwise.
    """
    # [debug] Data: ['Saldo anterior:', 'Importe cargado:', 'Saldo:', 'Importe pendiente:', '$1675,71', '$2000,00', '$3675,71', '$0,00']
        
    status: Literal["success", "error"] = Field(
        ..., description="Result of the credit operation"
    )
    previous_balance: Optional[float] = Field(
        None, description="Previous balance before the credit operation"
    )
    amount_loaded: Optional[float] = Field(
        None, description="Amount loaded onto the card"
    )
    new_balance: Optional[float] = Field(
        None, description="New balance after the credit operation"
    )
    pending_amount: Optional[float] = Field(
        None, description="Pending amount after the operation"
    )
    message: Optional[str] = Field(
        None, description="Additional message or error details"
    )


# Instancia Sube 
sube_controller = SubeApp(exe_path=EXE_PATH, window_title=WINDOW_TITLE, process_name=PROCESS_NAME)
# B. EndPoint GET /status
# -----------------------------------------------------------------------------
@app.get("/status", response_model=StatusResponse, tags=["Monitoring"])
async def get_status():
    """
    Checks whether the SUBE application is running.
    """
    if sube_controller._status():
        return StatusResponse(status="open")
    return StatusResponse(status="closed")
 
# -----------------------------------------------------------------------------
# C. EndPoint POST /open
# -----------------------------------------------------------------------------

@app.post("/open", response_model=AccionResponse, tags=["Ciclo de Vida"])
async def open_application():
    """
    Checks the application status and starts.
    """
    try:
        success = sube_controller.start_app()
        if success:
            return AccionResponse(status="success", message="Application started successfully")
        else:
            return AccionResponse(status="error", message="Error starting the application")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# -----------------------------------------------------------------------------
# D. EndPoint POST /read
# -----------------------------------------------------------------------------

@app.post("/read", response_model=ReadCardResponse, tags=["Operaciones"])
async def read_card():
    """
    Activates the balance reading/query routine on the card reader.
    """
    try:
        result = sube_controller.scan_card()
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
                message=result.get("message", "Failed to read card")
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
# D. EndPoint POST /credit-balance
# -----------------------------------------------------------------------------

@app.post("/credit-balance", response_model=CreditBalanceResponse, tags=["Operaciones"])
async def credit_balance():
    """
    Activates the balance reading/query routine on the card reader.
    """
    try:
        result = sube_controller.credit_balance()
        
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