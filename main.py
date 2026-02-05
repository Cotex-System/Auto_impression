import win32print
import subprocess
import time
from fastapi import FastAPI, UploadFile, File, Form
import tempfile
import os

ACROBAT_PATH = r"C:\Program Files\Adobe\Acrobat Reader DC\Reader\AcroRd32.exe"
PRINTER_NAME = "ZDesigner TLP 2844"
API_TOKEN = os.environ.get("PRINT_API_TOKEN")

if not API_TOKEN:
    raise RuntimeError("PRINT_API_TOKEN non défini")
    
def check_token(authorization: str | None):
    if authorization is None:
        raise HTTPException(status_code=401, detail="Token manquant")

    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Format du token invalide")

    token = authorization.replace("Bearer ", "")
    if token != API_TOKEN:
        raise HTTPException(status_code=403, detail="Token invalide")
        
def print_epl(epl: bytes):
    hPrinter = win32print.OpenPrinter(PRINTER_NAME)
    try:
        hJob = win32print.StartDocPrinter(
            hPrinter, 1, ("EPL", None, "RAW")
        )
        win32print.StartPagePrinter(hPrinter)
        win32print.WritePrinter(hPrinter, epl)
        win32print.EndPagePrinter(hPrinter)
        win32print.EndDocPrinter(hPrinter)
    finally:
        win32print.ClosePrinter(hPrinter)


def print_pdf(pdf_path):
    subprocess.Popen([
        ACROBAT_PATH,
        "/t",
        pdf_path,
        "ZDesigner TLP 2844"
    ])
    time.sleep(5)

app = FastAPI()

@app.post("/print")
async def print_label(
    carrier: str = Form(...),
    file: UploadFile = File(...)
):
    data = await file.read()

    if carrier == "tnt":
        print_epl(data)

    elif carrier == "chronopost":
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as f:
            f.write(data)
            pdf_path = f.name
        print_pdf(pdf_path)
        os.remove(pdf_path)

    else:
        return {"error": "Transporteur inconnu"}

    return {"status": "printed"}
