import win32serviceutil
import win32service
import win32event
import servicemanager
import subprocess
import sys
import os

SCRIPT_PATH = r"C:\chemin\vers\ton\script.py"  # ton script FastAPI
PYTHON_EXE = sys.executable  # Python utilisé

class ZebraPrintService(win32serviceutil.ServiceFramework):
    _svc_name_ = "ZebraPrintAPI"
    _svc_display_name_ = "Zebra Print API Service"
    _svc_description_ = "Service Windows pour lancer l'API FastAPI et imprimer automatiquement."

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        self.process = None

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        if self.process:
            self.process.terminate()
        win32event.SetEvent(self.hWaitStop)

    def SvcDoRun(self):
        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STARTED,
            (self._svc_name_, "")
        )
        # Lance le script FastAPI
        self.process = subprocess.Popen([PYTHON_EXE, SCRIPT_PATH])
        win32event.WaitForSingleObject(self.hWaitStop, win32event.INFINITE)

if __name__ == '__main__':
    win32serviceutil.HandleCommandLine(ZebraPrintService)
