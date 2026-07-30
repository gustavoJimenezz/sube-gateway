import uvicorn
import logging
from app.api.route import app
from app.logger_config import setup_logger
logger = setup_logger(__name__)

if __name__ == "__main__":
    logger.info("Iniciando servidor...")
    
    uvicorn_logger = logging.getLogger("uvicorn")
    uvicorn_logger.handlers = logger.handlers
    uvicorn_logger.setLevel(logging.ERROR)
    
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
        reload=False,
        use_colors=False,
        access_log=True,
        log_config=None,
        log_level="info"
    )
    logger.info("Servidor detenido")