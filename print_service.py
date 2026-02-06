import win32serviceutil
import win32service
import win32event
import servicemanager
import subprocess
import sys
import os
import logging
from pathlib import Path

logging.info("Service démarré")
# Résoudre les chemins dynamiquement (même dossier que le service)
SERVICE_DIR = Path(__file__).parent
SCRIPT_PATH = SERVICE_DIR / "main.py"
LOG_PATH = SERVICE_DIR / "logs"
LOG_FILE = LOG_PATH / "zebra_print_service.log"
PYTHON_EXE = "C:\\Users\\Tubconcept\\anaconda3\\envs\\branch-print\\python.exe"  # Python utilisé

# Créer le dossier logs s'il n'existe pas
LOG_PATH.mkdir(exist_ok=True)

# Configurer logging
logging.basicConfig(
    filename=str(LOG_FILE),
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ZebraPrintService(win32serviceutil.ServiceFramework):
    _svc_name_ = "ZebraPrintAPI"
    _svc_display_name_ = "Zebra Print API Service"
    _svc_description_ = "Service Windows pour lancer l'API FastAPI et imprimer automatiquement sur imprimante Zebra TLP 2844."

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        self.process = None
        self.is_running = True

    def SvcStop(self):
        logger.info("Service arrêt demandé...")
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        self.is_running = False
        if self.process:
            logger.info("Arrêt du processus uvicorn...")
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                logger.warning("Timeout lors de l'arrêt - forçage...")
                self.process.kill()
        win32event.SetEvent(self.hWaitStop)

    def SvcDoRun(self):
        try:
            logger.info(f"Service {self._svc_name_} démarré")
            logger.info(f"Python: {PYTHON_EXE}")
            logger.info(f"Script: {SCRIPT_PATH}")
            logger.info(f"Logs: {LOG_FILE}")
            
            # Lance uvicorn sur le script FastAPI
            cmd = [
                PYTHON_EXE,
                "-m", "uvicorn",
                "main:app",
                "--host", "0.0.0.0",
                "--port", "5000",
                "--log-level", "info"
            ]
            logger.info(f"Commande: {' '.join(cmd)}")
            
            self.process = subprocess.Popen(
                cmd,
                cwd=str(SERVICE_DIR),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )
            
            # Lire les logs du processus
            while self.is_running and self.process.poll() is None:
                line = self.process.stdout.readline()
                if line:
                    logger.info(f"uvicorn: {line.strip()}")
            
            if self.process.returncode != 0:
                logger.error(f"Processus terminé avec code {self.process.returncode}")
        
        except Exception as e:
            logger.error(f"Erreur dans SvcDoRun: {e}", exc_info=True)
        finally:
            logger.info("Service arrêté")
            win32event.SetEvent(self.hWaitStop)

if __name__ == '__main__':
    win32serviceutil.HandleCommandLine(ZebraPrintService)
